import unittest
from unittest.mock import MagicMock, patch

from pyairbnb import details


def response(text: str) -> MagicMock:
    result = MagicMock()
    result.text = text
    result.cookies = {"cookie": text}
    result.raise_for_status.return_value = None
    return result


class DetailsDomainFallbackTests(unittest.TestCase):
    @patch("pyairbnb.details.parse.parse_body_details_wrapper")
    @patch("pyairbnb.details.requests.get")
    def test_com_room_url_falls_back_to_ca_after_parse_failure(
        self, get, parse_details
    ):
        get.side_effect = [response("handoff"), response("application")]
        parse_details.side_effect = [
            IndexError("missing deferred state"),
            ({"title": "listing"}, {"product_id": "123"}),
        ]

        data, price_input, cookies = details.get(
            "https://www.airbnb.com/rooms/123", "en", ""
        )

        self.assertEqual(data, {"title": "listing"})
        self.assertEqual(price_input, {"product_id": "123"})
        self.assertEqual(cookies, {"cookie": "application"})
        self.assertEqual(
            [call.args[0] for call in get.call_args_list],
            [
                "https://www.airbnb.com/rooms/123",
                "https://www.airbnb.ca/rooms/123",
            ],
        )

    @patch("pyairbnb.details.parse.parse_body_details_wrapper")
    @patch("pyairbnb.details.requests.get")
    def test_non_com_domain_does_not_retry_elsewhere(self, get, parse_details):
        get.return_value = response("response")
        parse_details.side_effect = IndexError("missing deferred state")

        with self.assertRaises(IndexError):
            details.get("https://www.airbnb.ca/rooms/123", "en", "")

        get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
