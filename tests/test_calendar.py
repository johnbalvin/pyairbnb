import copy
import unittest
import warnings
from unittest.mock import Mock, patch

from test_calendar_fixtures import calendar_fixture

import pyairbnb
from pyairbnb import calendarinfo


class GetCalendarTests(unittest.TestCase):
    def setUp(self):
        self.payload = calendar_fixture()

    @patch("pyairbnb.start.calendar.get")
    def test_raw_mode_returns_the_original_payload_without_validation(self, get):
        self.payload[0]["unknown"] = {"preserved": True}
        get.return_value = self.payload

        result = pyairbnb.get_calendar(
            api_key="key", room_id="123", return_dataclass=False
        )

        self.assertIs(result, self.payload)
        get.assert_called_once()
        self.assertFalse(get.call_args.kwargs["require_calendar_path"])

    @patch("pyairbnb.start.calendar.get")
    def test_default_returns_dataclasses_for_a_valid_contract(self, get):
        get.return_value = self.payload

        result = pyairbnb.get_calendar(api_key="key", room_id="123")

        self.assertIsInstance(result[0], pyairbnb.CalendarMonth)
        self.assertTrue(get.call_args.kwargs["require_calendar_path"])

    @patch("pyairbnb.start.calendar.get")
    def test_default_warns_once_and_returns_the_whole_raw_list(self, get):
        payload = copy.deepcopy(self.payload)
        del payload[0]["days"][0]["bookable"]
        payload[0]["days"][0]["newField"] = 1
        get.return_value = payload

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = pyairbnb.get_calendar(api_key="key", room_id="123")

        self.assertIs(result, payload)
        self.assertEqual(len(caught), 1)
        self.assertIsInstance(caught[0].message, pyairbnb.CalendarContractWarning)
        self.assertEqual(len(caught[0].message.issues), 2)

    @patch("pyairbnb.start.calendar.get")
    def test_strict_mode_raises_structured_contract_error(self, get):
        payload = copy.deepcopy(self.payload)
        payload[0]["month"] = 13
        get.return_value = payload

        with self.assertRaises(pyairbnb.CalendarContractError) as caught:
            pyairbnb.get_calendar(
                api_key="key", room_id="123", on_dataclass_error="raise"
            )

        self.assertEqual(caught.exception.issues[0].path, "$[0].month")

    @patch("pyairbnb.start.api.get")
    @patch("pyairbnb.start.calendar.get")
    def test_invalid_options_fail_before_io(self, calendar_get, api_get):
        for invalid in (1, 0, "yes", None):
            with self.subTest(return_dataclass=invalid), self.assertRaises(TypeError):
                pyairbnb.get_calendar(return_dataclass=invalid)

        with self.assertRaises(ValueError):
            pyairbnb.get_calendar(on_dataclass_error="ignore")

        calendar_get.assert_not_called()
        api_get.assert_not_called()

    @patch("pyairbnb.start.calendar.get", return_value=[])
    def test_explicit_empty_list_is_valid_in_both_modes(self, get):
        self.assertEqual(pyairbnb.get_calendar(api_key="key"), [])
        self.assertEqual(
            pyairbnb.get_calendar(api_key="key", return_dataclass=False), []
        )


class CalendarExtractionTests(unittest.TestCase):
    def test_missing_path_is_an_error_only_for_dataclass_mode(self):
        with self.assertRaises(pyairbnb.CalendarExtractionError) as caught:
            calendarinfo._extract_calendar({}, require_path=True)
        self.assertEqual(
            caught.exception.path,
            "$.data.merlin.pdpAvailabilityCalendar.calendarMonths",
        )
        self.assertEqual(calendarinfo._extract_calendar({}, require_path=False), [])

    def test_explicit_empty_list_is_preserved(self):
        response = {
            "data": {"merlin": {"pdpAvailabilityCalendar": {"calendarMonths": []}}}
        }
        calendar = response["data"]["merlin"]["pdpAvailabilityCalendar"][
            "calendarMonths"
        ]
        self.assertIs(
            calendarinfo._extract_calendar(response, require_path=True), calendar
        )


class GetDetailsCompatibilityTests(unittest.TestCase):
    @patch("pyairbnb.start.host_details.get", return_value={})
    @patch("pyairbnb.start.get_calendar", return_value=[])
    @patch("pyairbnb.start.reviews.get", return_value=[])
    @patch("pyairbnb.start.details.get")
    def test_get_details_requests_raw_calendar(
        self, details_get, reviews_get, get_calendar, host_details_get
    ):
        details_get.return_value = (
            {"host": {"id": "host"}},
            {"product_id": "123", "api_key": "key", "impression_id": "id"},
            Mock(),
        )

        result = pyairbnb.get_details(room_id=123)

        self.assertEqual(result["calendar"], [])
        self.assertFalse(get_calendar.call_args.kwargs["return_dataclass"])


if __name__ == "__main__":
    unittest.main()
