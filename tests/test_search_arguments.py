import unittest
from unittest.mock import Mock, patch

from pyairbnb import search, start


class SearchArgumentCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.location_args = ("2026-01-01", "2026-01-04", 1.0, 2.0, 3.0, 4.0, 10)

    @patch("pyairbnb.start.search.get", return_value={})
    @patch("pyairbnb.start.api.get", return_value="api-key")
    def test_legacy_positional_price_arguments_still_work(self, api_get, search_get):
        result = start.search_all(
            *self.location_args,
            "MXN",
            "Private room",
            "1",
            "10000000",
        )

        self.assertEqual(result, [])
        kwargs = search_get.call_args.kwargs
        self.assertEqual(kwargs["currency"], "MXN")
        self.assertEqual(kwargs["place_type"], "Private room")
        self.assertEqual(kwargs["price_min"], 1)
        self.assertEqual(kwargs["price_max"], 10000000)
        api_get.assert_called_once_with("", timeout=60)

    @patch("pyairbnb.start.search.get", return_value={})
    @patch("pyairbnb.start.api.get", return_value="api-key")
    def test_legacy_positional_arguments_can_be_mixed_with_keywords(
        self, api_get, search_get
    ):
        start.search_all(
            *self.location_args,
            "MXN",
            "Private room",
            price_min=1,
            price_max=10000000,
        )

        kwargs = search_get.call_args.kwargs
        self.assertEqual(kwargs["currency"], "MXN")
        self.assertEqual(kwargs["place_type"], "Private room")
        self.assertEqual(kwargs["price_min"], 1)
        self.assertEqual(kwargs["price_max"], 10000000)

    @patch("pyairbnb.start.search.get", return_value={})
    @patch("pyairbnb.start.api.get", return_value="api-key")
    def test_current_positional_and_string_keyword_forms_work(
        self, api_get, search_get
    ):
        start.search_all(
            *self.location_args,
            "2",
            "500",
            "Entire home/apt",
        )
        positional_kwargs = search_get.call_args.kwargs
        self.assertEqual(positional_kwargs["price_min"], 2)
        self.assertEqual(positional_kwargs["price_max"], 500)
        self.assertEqual(positional_kwargs["place_type"], "Entire home/apt")

        start.search_all(
            *self.location_args,
            price_min="3",
            price_max="600",
            currency="USD",
        )
        keyword_kwargs = search_get.call_args.kwargs
        self.assertEqual(keyword_kwargs["price_min"], 3)
        self.assertEqual(keyword_kwargs["price_max"], 600)
        self.assertEqual(keyword_kwargs["currency"], "USD")


class SearchFilterTests(unittest.TestCase):
    def _call_get(self, **overrides):
        arguments = {
            "api_key": "api-key",
            "cursor": "",
            "check_in": None,
            "check_out": None,
            "ne_lat": 1.0,
            "ne_long": 2.0,
            "sw_lat": 3.0,
            "sw_long": 4.0,
            "zoom_value": 10,
            "currency": "USD",
            "place_type": "",
            "price_min": 0,
            "price_max": 0,
            "amenities": [],
            "free_cancellation": False,
            "adults": 0,
            "children": 0,
            "infants": 0,
            "min_bedrooms": 0,
            "min_beds": 0,
            "min_bathrooms": 0,
            "language": "en",
            "proxy_url": "",
            "hash": "hash",
        }
        arguments.update(overrides)

        response = Mock(status_code=200)
        response.json.return_value = {}
        with patch("pyairbnb.search.requests.post", return_value=response) as post:
            search.get(**arguments)

        raw_params = post.call_args.kwargs["json"]["variables"][
            "staysSearchRequest"
        ]["rawParams"]
        return {
            item["filterName"]: item["filterValues"] for item in raw_params
        }

    def test_numeric_string_filters_are_normalized(self):
        filters = self._call_get(
            price_min="1",
            price_max="10000000",
            adults="2",
            min_bedrooms="1",
        )

        self.assertEqual(filters["price_min"], ["1"])
        self.assertEqual(filters["price_max"], ["10000000"])
        self.assertEqual(filters["adults"], ["2"])
        self.assertEqual(filters["min_bedrooms"], ["1"])

    def test_invalid_numeric_filter_has_a_clear_error(self):
        with self.assertRaisesRegex(ValueError, "price_min must be a number"):
            self._call_get(price_min="not-a-price")


if __name__ == "__main__":
    unittest.main()
