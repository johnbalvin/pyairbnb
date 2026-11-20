import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from curl_cffi import requests

import pyairbnb.price as price


def price_response(
    *,
    discounted_price: str = "$100",
    original_price: str = "$120",
) -> dict:
    return {
        "data": {
            "presentation": {
                "stayProductDetailPage": {
                    "sections": {
                        "sections": [
                            {
                                "sectionId": "BOOK_IT_SIDEBAR",
                                "section": {
                                    "structuredDisplayPrice": {
                                        "primaryLine": {
                                            "discountedPrice": discounted_price,
                                            "originalPrice": original_price,
                                            "qualifier": {"kind": "nightly"},
                                        },
                                        "explanationData": {
                                            "priceDetails": [
                                                {
                                                    "items": [
                                                        {
                                                            "description": "2 nights",
                                                            "priceString": original_price,
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                    }
                                },
                            }
                        ],
                        "metadata": {},
                    }
                }
            }
        }
    }


def mock_response(payload: dict, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def mock_session(*responses: MagicMock) -> MagicMock:
    session = MagicMock()
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    session.post.side_effect = list(responses)
    return session


class PriceRequestTests(unittest.TestCase):
    def setUp(self):
        self.check_in = date(2027, 1, 10)
        self.check_out = date(2027, 1, 12)

    @patch("pyairbnb.price._new_p3_impression_id", return_value="p3-test")
    def test_build_query_variables_uses_the_new_request_schema(self, _):
        variables = price._build_query_variables(
            room_id="123",
            check_in=self.check_in,
            check_out=self.check_out,
            adults=2,
        )

        self.assertEqual(
            variables["dateRange"],
            {"startDate": "2027-01-10", "endDate": "2027-01-12"},
        )
        self.assertEqual(variables["guestCounts"], {"numberOfAdults": 2})
        self.assertEqual(variables["p3ImpressionId"], "p3-test")
        self.assertTrue(variables["includeGpBookItFragment"])
        self.assertNotIn("displayExtensions", variables["pdpSectionsRequest"])
        self.assertNotIn("dateRange", variables["pdpSectionsRequest"])

    def test_get_posts_json_and_preserves_the_public_shape(self):
        session = mock_session(mock_response(price_response()))

        with patch("pyairbnb.price.requests.Session", return_value=session):
            result = price.get(
                room_id="123",
                check_in=self.check_in,
                check_out=self.check_out,
                currency="CAD",
                api_key="key",
                cookies=None,
                timeout=10,
            )

        self.assertEqual(result["main"]["price"], "$100")
        self.assertEqual(result["main"]["originalPrice"], "$120")
        self.assertEqual(result["main"]["details"], {"2 nights": "$120"})
        session.cookies.update.assert_not_called()

        request = session.post.call_args
        self.assertIn("currency=CAD", request.kwargs["url"])
        self.assertEqual(
            request.kwargs["json"]["operationName"], "StaysPdpSections"
        )
        self.assertEqual(
            request.kwargs["json"]["variables"]["dateRange"]["startDate"],
            "2027-01-10",
        )

    def test_invalid_hash_response_refreshes_hash_and_retries_once(self):
        new_hash = "a" * 64
        session = mock_session(
            mock_response({"errors": [{"message": "bad hash"}]}),
            mock_response(price_response()),
        )

        with (
            patch.object(price, "PERSISTED_QUERY_HASH", "0" * 64),
            patch(
                "pyairbnb.price.fetch_pdp_sections_hash", return_value=new_hash
            ) as fetch_hash,
            patch("pyairbnb.price.requests.Session", return_value=session),
        ):
            result = price.get(
                room_id="123",
                check_in=self.check_in,
                check_out=self.check_out,
                api_key="key",
                timeout=10,
            )
            self.assertEqual(price.PERSISTED_QUERY_HASH, new_hash)

        self.assertEqual(result["main"]["price"], "$100")
        self.assertEqual(session.post.call_count, 2)
        self.assertIn(new_hash, session.post.call_args.kwargs["url"])
        fetch_hash.assert_called_once()

    def test_missing_main_price_is_an_error_after_refresh(self):
        payload = price_response()
        payload["data"]["presentation"]["stayProductDetailPage"]["sections"][
            "sections"
        ] = []
        session = mock_session(
            mock_response(payload),
            mock_response(payload),
        )

        with (
            patch.object(price, "PERSISTED_QUERY_HASH", "0" * 64),
            patch(
                "pyairbnb.price.fetch_pdp_sections_hash", return_value="b" * 64
            ),
            patch("pyairbnb.price.requests.Session", return_value=session),
            self.assertRaisesRegex(RuntimeError, "no BOOK_IT_SIDEBAR price"),
        ):
            price.get(
                room_id="123",
                check_in=self.check_in,
                check_out=self.check_out,
                api_key="key",
                timeout=10,
            )

        self.assertEqual(session.post.call_count, 2)

    def test_network_error_is_not_mistaken_for_a_stale_hash(self):
        session = mock_session()
        session.post.side_effect = requests.exceptions.Timeout("timed out")

        with (
            patch(
                "pyairbnb.price.fetch_pdp_sections_hash"
            ) as fetch_hash,
            patch("pyairbnb.price.requests.Session", return_value=session),
            self.assertRaises(requests.exceptions.Timeout),
        ):
            price.get(
                room_id="123",
                check_in=self.check_in,
                check_out=self.check_out,
                api_key="key",
                timeout=10,
            )

        self.assertEqual(session.post.call_count, 1)
        fetch_hash.assert_not_called()

    def test_unavailable_listing_does_not_retry(self):
        payload = price_response()
        sidebar = payload["data"]["presentation"]["stayProductDetailPage"][
            "sections"
        ]["sections"][0]
        sidebar["section"]["localizedUnavailabilityMessage"] = "Not available"
        session = mock_session(mock_response(payload))

        with (
            patch(
                "pyairbnb.price.fetch_pdp_sections_hash"
            ) as fetch_hash,
            patch("pyairbnb.price.requests.Session", return_value=session),
            self.assertRaisesRegex(price.UnavailableError, "Not available"),
        ):
            price.get(
                room_id="123",
                check_in=self.check_in,
                check_out=self.check_out,
                api_key="key",
                timeout=10,
            )

        self.assertEqual(session.post.call_count, 1)
        fetch_hash.assert_not_called()


if __name__ == "__main__":
    unittest.main()
