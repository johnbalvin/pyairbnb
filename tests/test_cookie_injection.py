import unittest
from unittest.mock import MagicMock, patch

from pyairbnb import details, reviews, start

COOKIES = {"session": "abc123"}


def html_response(text: str) -> MagicMock:
    result = MagicMock()
    result.text = text
    result.cookies = {"server": "set"}
    result.raise_for_status.return_value = None
    return result


def json_response(payload: dict, status: int = 200) -> MagicMock:
    result = MagicMock()
    result.status_code = status
    result.raise_for_status.return_value = None
    result.json.return_value = payload
    return result


class DetailsCookieTests(unittest.TestCase):
    @patch("pyairbnb.details.parse.parse_body_details_wrapper")
    @patch("pyairbnb.details.requests.get")
    def test_user_cookies_are_sent(self, get, parse_details):
        get.return_value = html_response("page")
        parse_details.return_value = ({"title": "listing"}, {"product_id": "1"})

        details.get("https://www.airbnb.com/rooms/1", "en", "", cookies=COOKIES)

        self.assertEqual(get.call_args.kwargs["cookies"], COOKIES)

    @patch("pyairbnb.details.parse.parse_body_details_wrapper")
    @patch("pyairbnb.details.requests.get")
    def test_without_cookies_behavior_is_unchanged(self, get, parse_details):
        get.return_value = html_response("page")
        parse_details.return_value = ({"title": "listing"}, {"product_id": "1"})

        details.get("https://www.airbnb.com/rooms/1", "en", "")

        self.assertIsNone(get.call_args.kwargs["cookies"])


class ReviewsCookieTests(unittest.TestCase):
    @patch("pyairbnb.reviews.get_from_offset")
    def test_get_threads_cookies(self, get_from_offset):
        get_from_offset.return_value = []

        reviews.get(api_key="key", product_id="1", cookies=COOKIES)

        self.assertEqual(get_from_offset.call_args.kwargs["cookies"], COOKIES)

    @patch("pyairbnb.reviews.requests.get")
    def test_get_from_offset_sends_cookies(self, get):
        get.return_value = json_response(
            {
                "data": {
                    "presentation": {
                        "stayProductDetailPage": {"reviews": {"reviews": []}}
                    }
                }
            }
        )

        result = reviews.get_from_offset(
            "key", 0, "1", cookies=COOKIES
        )

        self.assertEqual(result, [])
        self.assertEqual(get.call_args.kwargs["cookies"], COOKIES)


class StartCookieTests(unittest.TestCase):
    def setUp(self):
        self.details_return = (
            {"title": "listing", "host": {"id": "1"}},
            {"product_id": "1", "api_key": "key", "impression_id": "imp"},
            {"server": "set"},
        )

    @patch("pyairbnb.start.host_details.get")
    @patch("pyairbnb.start.get_calendar")
    @patch("pyairbnb.start.price.get")
    @patch("pyairbnb.start.reviews.get")
    @patch("pyairbnb.start.details.get")
    def test_get_details_threads_user_cookies(
        self, details_get, reviews_get, price_get, calendar_get, host_details_get
    ):
        details_get.return_value = self.details_return
        reviews_get.return_value = []
        price_get.return_value = {}
        calendar_get.return_value = {}
        host_details_get.return_value = {}

        start.get_details(
            room_url="https://www.airbnb.com/rooms/1",
            check_in="2026-12-09",
            check_out="2026-12-23",
            cookies=COOKIES,
        )

        self.assertEqual(details_get.call_args.kwargs["cookies"], COOKIES)
        self.assertEqual(reviews_get.call_args.kwargs["cookies"], COOKIES)
        self.assertEqual(price_get.call_args.kwargs["cookies"], COOKIES)
        self.assertEqual(host_details_get.call_args.args[1], COOKIES)

    @patch("pyairbnb.start.host_details.get")
    @patch("pyairbnb.start.get_calendar")
    @patch("pyairbnb.start.price.get")
    @patch("pyairbnb.start.reviews.get")
    @patch("pyairbnb.start.details.get")
    def test_get_details_without_cookies_uses_harvested(
        self, details_get, reviews_get, price_get, calendar_get, host_details_get
    ):
        details_get.return_value = self.details_return
        reviews_get.return_value = []
        price_get.return_value = {}
        calendar_get.return_value = {}
        host_details_get.return_value = {}

        start.get_details(
            room_url="https://www.airbnb.com/rooms/1",
            check_in="2026-12-09",
            check_out="2026-12-23",
        )

        self.assertIsNone(details_get.call_args.kwargs["cookies"])
        self.assertEqual(price_get.call_args.kwargs["cookies"], {"server": "set"})
        self.assertEqual(host_details_get.call_args.args[1], {"server": "set"})

    @patch("pyairbnb.start.reviews.get")
    @patch("pyairbnb.start.details.get")
    def test_get_reviews_threads_cookies(self, details_get, reviews_get):
        details_get.return_value = (
            {},
            {"product_id": "1", "api_key": "key"},
            {"server": "set"},
        )
        reviews_get.return_value = []

        start.get_reviews(
            "https://www.airbnb.com/rooms/1", cookies=COOKIES
        )

        self.assertEqual(details_get.call_args.kwargs["cookies"], COOKIES)
        self.assertEqual(reviews_get.call_args.kwargs["cookies"], COOKIES)


if __name__ == "__main__":
    unittest.main()
