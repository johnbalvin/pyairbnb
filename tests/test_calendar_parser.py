import unittest

from test_calendar_fixtures import calendar_fixture, month_fixture

import pyairbnb
from pyairbnb.parsers.calendar import parse_calendar


class CalendarParserTests(unittest.TestCase):
    def test_converts_a_valid_root_list(self):
        result = parse_calendar(calendar_fixture())

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], pyairbnb.CalendarMonth)

    def test_accepts_an_explicitly_empty_root_list(self):
        self.assertEqual(parse_calendar([]), [])

    def test_rejects_an_invalid_root_container(self):
        with self.assertRaises(pyairbnb.CalendarContractError) as caught:
            parse_calendar({})

        issue = caught.exception.issues[0]
        self.assertEqual(issue.kind, "invalid_container")
        self.assertEqual(issue.path, "$")

    def test_aggregates_issues_from_multiple_months(self):
        first = month_fixture()
        second = month_fixture()
        first["month"] = 13
        second["listingId"] = 123

        with self.assertRaises(pyairbnb.CalendarContractError) as caught:
            parse_calendar([first, second])

        self.assertEqual(
            [issue.path for issue in caught.exception.issues],
            ["$[0].month", "$[1].listingId"],
        )

    def test_never_returns_partial_results(self):
        valid = month_fixture()
        invalid = month_fixture()
        del invalid["days"]

        with self.assertRaises(pyairbnb.CalendarContractError):
            parse_calendar([valid, invalid])


if __name__ == "__main__":
    unittest.main()
