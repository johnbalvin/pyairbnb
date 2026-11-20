import unittest
from unittest.mock import MagicMock, patch

from curl_cffi import requests

import pyairbnb.reviews as reviews


def reviews_response(review_count: int, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "data": {
            "presentation": {
                "stayProductDetailPage": {
                    "reviews": {"reviews": [{"id": i} for i in range(review_count)]}
                }
            }
        }
    }
    return response


def error_response(status_code: int) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(f"HTTP {status_code}")
    return response


class ReviewsPaginationTests(unittest.TestCase):
    @patch(f"{reviews.__name__}.get_from_offset")
    def test_get_stops_on_short_page(self, get_from_offset):
        get_from_offset.side_effect = [[{"id": i} for i in range(50)], [{"id": 0}, {"id": 1}]]

        all_reviews = reviews.get(api_key="key", product_id="123", timeout=10)

        self.assertEqual(len(all_reviews), 52)
        self.assertEqual(get_from_offset.call_count, 2)
        self.assertEqual(get_from_offset.call_args_list[0].args[1], 0)
        self.assertEqual(get_from_offset.call_args_list[1].args[1], 50)

    @patch(f"{reviews.__name__}.get_from_offset")
    def test_get_stops_immediately_on_empty_page(self, get_from_offset):
        get_from_offset.side_effect = [[]]

        all_reviews = reviews.get(api_key="key", product_id="123", timeout=10)

        self.assertEqual(all_reviews, [])
        self.assertEqual(get_from_offset.call_count, 1)


class ReviewsRequestTests(unittest.TestCase):
    def setUp(self):
        self.get_patcher = patch(f"{reviews.__name__}.requests.get")
        self.mock_get = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

    def test_get_from_offset_builds_query_from_current_hash(self):
        self.mock_get.return_value = reviews_response(0)

        result = reviews.get_from_offset("key", 50, "123", timeout=10)

        self.assertEqual(result, [])
        url = self.mock_get.call_args.args[0]
        self.assertIn(reviews.PERSISTED_QUERY_HASH, url)
        self.assertIn("StaysPdpReviewsQuery", url)
        self.assertIn("offset%22%3A+%2250%22", url)

    def test_http_400_refreshes_hash_and_retries_once(self):
        self.mock_get.side_effect = [
            error_response(400),
            reviews_response(3),
        ]

        with (
            patch.object(reviews, "PERSISTED_QUERY_HASH", "0" * 64),
            patch(
                f"{reviews.__name__}.fetch_reviews_hash", return_value="b" * 64
            ) as fetch_hash,
        ):
            result = reviews.get_from_offset("key", 0, "123", timeout=10)
            self.assertEqual(reviews.PERSISTED_QUERY_HASH, "b" * 64)

        self.assertEqual(len(result), 3)
        self.assertEqual(self.mock_get.call_count, 2)
        fetch_hash.assert_called_once()

    def test_missing_reviews_payload_retries_then_raises(self):
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status.return_value = None
        response.json.return_value = {"data": {}}
        self.mock_get.side_effect = [response, response]

        with (
            patch.object(reviews, "PERSISTED_QUERY_HASH", "0" * 64),
            patch(
                f"{reviews.__name__}.fetch_reviews_hash", return_value="b" * 64
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "no reviews payload"):
                reviews.get_from_offset("key", 0, "123", timeout=10)

        self.assertEqual(self.mock_get.call_count, 2)

    def test_network_error_is_not_mistaken_for_a_stale_hash(self):
        self.mock_get.side_effect = requests.exceptions.Timeout("timed out")

        with (
            patch(
                f"{reviews.__name__}.fetch_reviews_hash"
            ) as fetch_hash,
            self.assertRaises(requests.exceptions.Timeout),
        ):
            reviews.get_from_offset("key", 0, "123", timeout=10)

        self.assertEqual(self.mock_get.call_count, 1)
        fetch_hash.assert_not_called()


if __name__ == "__main__":
    unittest.main()
