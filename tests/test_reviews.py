import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

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


def json_response(payload: dict, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


def text_response(text: str, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.raise_for_status.return_value = None
    response.text = text
    return response


def error_response(status_code: int) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        f"HTTP {status_code}"
    )
    return response


def parse_request_url(url: str) -> tuple[str, dict, dict]:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    variables = json.loads(params["variables"][0])
    extensions = json.loads(params["extensions"][0])
    return parsed.path, variables, extensions


class ReviewsPaginationTests(unittest.TestCase):
    @patch(f"{reviews.__name__}.get_from_offset")
    def test_get_stops_on_short_page(self, get_from_offset):
        get_from_offset.side_effect = [
            [{"id": i} for i in range(50)],
            [{"id": 0}, {"id": 1}],
        ]

        all_reviews = reviews.get(api_key="key", product_id="123", timeout=10)

        self.assertEqual(len(all_reviews), 52)
        self.assertEqual(get_from_offset.call_count, 2)
        self.assertEqual(get_from_offset.call_args_list[0].args[1], 0)
        self.assertEqual(get_from_offset.call_args_list[1].args[1], 50)

    @patch(f"{reviews.__name__}.get_from_offset")
    def test_get_stops_on_exact_page_boundary(self, get_from_offset):
        get_from_offset.side_effect = [[{"id": i} for i in range(50)], []]

        all_reviews = reviews.get(api_key="key", product_id="123", timeout=10)

        self.assertEqual(len(all_reviews), 50)
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
        path, variables, extensions = parse_request_url(self.mock_get.call_args.args[0])
        self.assertIn(f"StaysPdpReviewsQuery/{reviews.PERSISTED_QUERY_HASH}/", path)
        self.assertEqual(
            extensions["persistedQuery"]["sha256Hash"], reviews.PERSISTED_QUERY_HASH
        )
        self.assertEqual(variables["pdpReviewsRequest"]["offset"], "50")

    def test_http_400_refreshes_hash_and_retries_once(self):
        new_hash = "b" * 64
        self.mock_get.side_effect = [
            error_response(400),
            reviews_response(3),
        ]

        with (
            patch.object(reviews, "PERSISTED_QUERY_HASH", "0" * 64),
            patch(
                f"{reviews.__name__}.fetch_reviews_hash", return_value=new_hash
            ) as fetch_hash,
        ):
            result = reviews.get_from_offset("key", 0, "123", timeout=10)
            self.assertEqual(reviews.PERSISTED_QUERY_HASH, new_hash)

        self.assertEqual(len(result), 3)
        self.assertEqual(self.mock_get.call_count, 2)
        retry_path, _, retry_extensions = parse_request_url(
            self.mock_get.call_args_list[1].args[0]
        )
        self.assertIn(new_hash, retry_path)
        self.assertEqual(retry_extensions["persistedQuery"]["sha256Hash"], new_hash)
        fetch_hash.assert_called_once()

    def test_graphql_error_surfaces_message_and_retries_once(self):
        new_hash = "b" * 64
        self.mock_get.side_effect = [
            json_response({"errors": [{"message": "PersistedQueryNotFound"}]}),
            json_response({"errors": [{"message": "Still invalid"}]}),
        ]

        with (
            patch.object(reviews, "PERSISTED_QUERY_HASH", "0" * 64),
            patch(f"{reviews.__name__}.fetch_reviews_hash", return_value=new_hash),
            self.assertRaisesRegex(RuntimeError, "Still invalid"),
        ):
            reviews.get_from_offset("key", 0, "123", timeout=10)

        self.assertEqual(self.mock_get.call_count, 2)

    def test_graphql_not_found_does_not_refresh_or_retry(self):
        self.mock_get.return_value = json_response(
            {
                "errors": [
                    {
                        "message": "Listing not found",
                        "extensions": {"errorType": "NOT_FOUND"},
                    }
                ]
            }
        )

        with (
            patch(f"{reviews.__name__}.fetch_reviews_hash") as fetch_hash,
            self.assertRaisesRegex(RuntimeError, r"NOT_FOUND.*Listing not found"),
        ):
            reviews.get_from_offset("key", 0, "123", timeout=10)

        self.assertEqual(self.mock_get.call_count, 1)
        fetch_hash.assert_not_called()

    def test_missing_reviews_payload_retries_then_raises(self):
        response = json_response({"data": {}})
        self.mock_get.side_effect = [response, response]

        with (
            patch.object(reviews, "PERSISTED_QUERY_HASH", "0" * 64),
            patch(f"{reviews.__name__}.fetch_reviews_hash", return_value="b" * 64),
            self.assertRaisesRegex(RuntimeError, "no reviews payload"),
        ):
            reviews.get_from_offset("key", 0, "123", timeout=10)

        self.assertEqual(self.mock_get.call_count, 2)

    def test_unchanged_hash_skips_duplicate_retry(self):
        self.mock_get.return_value = error_response(400)

        with (
            patch.object(reviews, "PERSISTED_QUERY_HASH", "0" * 64),
            patch(
                f"{reviews.__name__}.fetch_reviews_hash", return_value="0" * 64
            ) as fetch_hash,
            self.assertRaisesRegex(RuntimeError, "HTTP 400"),
        ):
            reviews.get_from_offset("key", 0, "123", timeout=10)

        self.assertEqual(self.mock_get.call_count, 1)
        fetch_hash.assert_called_once()

    def test_hash_refresh_failure_chains_original_error(self):
        self.mock_get.return_value = error_response(400)
        refresh_error = RuntimeError("bundle unavailable")

        with (
            patch.object(reviews, "PERSISTED_QUERY_HASH", "0" * 64),
            patch(
                f"{reviews.__name__}.fetch_reviews_hash", side_effect=refresh_error
            ),
            self.assertRaisesRegex(RuntimeError, "HTTP 400") as ctx,
        ):
            reviews.get_from_offset("key", 0, "123", timeout=10)

        self.assertIs(ctx.exception.__cause__, refresh_error)
        self.assertEqual(self.mock_get.call_count, 1)

    def test_non_400_http_error_propagates_without_refresh(self):
        self.mock_get.return_value = error_response(500)

        with (
            patch(f"{reviews.__name__}.fetch_reviews_hash") as fetch_hash,
            self.assertRaises(requests.exceptions.HTTPError),
        ):
            reviews.get_from_offset("key", 0, "123", timeout=10)

        self.assertEqual(self.mock_get.call_count, 1)
        fetch_hash.assert_not_called()

    def test_http_422_invalid_listing_fails_without_refresh(self):
        self.mock_get.return_value = error_response(422)

        with (
            patch(f"{reviews.__name__}.fetch_reviews_hash") as fetch_hash,
            self.assertRaisesRegex(RuntimeError, r"HTTP 422.*invalid listing"),
        ):
            reviews.get_from_offset("key", 0, "invalid", timeout=10)

        self.assertEqual(self.mock_get.call_count, 1)
        fetch_hash.assert_not_called()

    def test_network_error_is_not_mistaken_for_a_stale_hash(self):
        self.mock_get.side_effect = requests.exceptions.Timeout("timed out")

        with (
            patch(f"{reviews.__name__}.fetch_reviews_hash") as fetch_hash,
            self.assertRaises(requests.exceptions.Timeout),
        ):
            reviews.get_from_offset("key", 0, "123", timeout=10)

        self.assertEqual(self.mock_get.call_count, 1)
        fetch_hash.assert_not_called()


class FetchReviewsHashTests(unittest.TestCase):
    BUNDLE_URL = "https://a0.muscache.com/airbnb/static/packages/web/en/frontend/airmetro/browser/asyncRequire.abc123.js"
    MODULE_PATH = "common/frontend/gp-stays-pdp-sections/migrated-sections/ReviewsSection/ReviewsSection.prepare.deadbeef.js"
    EXPECTED_HASH = "a" * 64

    def test_discovers_hash_directly_from_homepage(self):
        homepage = text_response(f'<script src="{self.BUNDLE_URL}"></script>')
        bundle = text_response(f'"{self.MODULE_PATH}"')
        chunk = text_response(
            f"{{name:'StaysPdpReviewsQuery',type:'query',operationId:'{self.EXPECTED_HASH}'}}"
        )

        with patch(
            f"{reviews.__name__}.requests.get", side_effect=[homepage, bundle, chunk]
        ) as mock_get:
            discovered = reviews.fetch_reviews_hash(timeout=10)

        self.assertEqual(discovered, self.EXPECTED_HASH)
        self.assertEqual(mock_get.call_args_list[0].args[0], "https://www.airbnb.com/")
        self.assertEqual(mock_get.call_args_list[1].args[0], self.BUNDLE_URL)
        self.assertEqual(
            mock_get.call_args_list[2].args[0],
            f"https://a0.muscache.com/airbnb/static/packages/web/{self.MODULE_PATH}",
        )

    def test_follows_geo_handoff_form_when_initial_page_has_no_bundle(self):
        handoff_form = text_response(
            '<form action="https://www.airbnb.example/v2/domain_switch/handoff">'
            '<input name="payload" value="signed-payload" /></form>'
        )
        handoff_homepage = text_response(f'<script src="{self.BUNDLE_URL}"></script>')
        bundle = text_response(f'"{self.MODULE_PATH}"')
        chunk = text_response(
            f"{{name:'StaysPdpReviewsQuery',type:'query',operationId:'{self.EXPECTED_HASH}'}}"
        )

        with (
            patch(
                f"{reviews.__name__}.requests.get",
                side_effect=[handoff_form, bundle, chunk],
            ),
            patch(
                f"{reviews.__name__}.requests.post", return_value=handoff_homepage
            ) as mock_post,
        ):
            discovered = reviews.fetch_reviews_hash(timeout=10)

        self.assertEqual(discovered, self.EXPECTED_HASH)
        mock_post.assert_called_once()
        self.assertEqual(
            mock_post.call_args.args[0],
            "https://www.airbnb.example/v2/domain_switch/handoff",
        )
        self.assertEqual(
            mock_post.call_args.kwargs["data"],
            {"version": "1", "payload": "signed-payload"},
        )

    def test_raises_when_bundle_module_or_hash_is_missing(self):
        cases = [
            ("missing bundle", [text_response("<html></html>")], "asyncRequire bundle"),
            (
                "missing module",
                [text_response(f'<script src="{self.BUNDLE_URL}"></script>'), text_response("no module")],
                "module chunk",
            ),
            (
                "missing hash",
                [
                    text_response(f'<script src="{self.BUNDLE_URL}"></script>'),
                    text_response(f'"{self.MODULE_PATH}"'),
                    text_response("no operation id"),
                ],
                "operationId",
            ),
        ]

        for label, responses, expected_error in cases:
            with self.subTest(label=label):
                with (
                    patch(f"{reviews.__name__}.requests.get", side_effect=responses),
                    self.assertRaisesRegex(RuntimeError, expected_error),
                ):
                    reviews.fetch_reviews_hash(timeout=10)


if __name__ == "__main__":
    unittest.main()
