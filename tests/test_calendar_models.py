import unittest
from dataclasses import FrozenInstanceError

from test_calendar_fixtures import (
    condition_range_fixture,
    conditions_fixture,
    day_fixture,
    month_fixture,
    price_fixture,
)

import pyairbnb
from pyairbnb.models import (
    CalendarConditionRange,
    CalendarConditions,
    CalendarDay,
    CalendarDayPrice,
    CalendarMonth,
)


class CalendarModelTests(unittest.TestCase):
    cases = (
        (CalendarDayPrice, price_fixture, "localPriceFormatted"),
        (CalendarDay, day_fixture, "bookable"),
        (CalendarConditions, conditions_fixture, "endDayOfWeek"),
        (CalendarConditionRange, condition_range_fixture, "endDate"),
        (CalendarMonth, month_fixture, "listingId"),
    )

    def test_each_model_converts_its_fragment_and_python_names(self):
        price = CalendarDayPrice.from_dict(price_fixture())
        self.assertEqual(price.local_price_formatted, None)

        day = CalendarDay.from_dict(day_fixture())
        self.assertEqual(day.calendar_date, "2026-08-01")
        self.assertTrue(day.available_for_checkin)
        self.assertFalse(day.available_for_checkout)
        self.assertEqual(day.min_nights, 1)
        self.assertEqual(day.max_nights, 365)
        self.assertIsInstance(day.price, CalendarDayPrice)

        conditions = CalendarConditions.from_dict(conditions_fixture())
        self.assertFalse(conditions.closed_to_arrival)
        self.assertFalse(conditions.closed_to_departure)
        self.assertIsNone(conditions.end_day_of_week)

        condition_range = CalendarConditionRange.from_dict(condition_range_fixture())
        self.assertEqual(condition_range.start_date, "2026-08-01")
        self.assertEqual(condition_range.end_date, "2026-08-01")
        self.assertIsInstance(condition_range.conditions, CalendarConditions)

        month = CalendarMonth.from_dict(month_fixture())
        self.assertEqual(month.listing_id, "123")
        self.assertIsInstance(month.days, tuple)
        self.assertIsInstance(month.days[0], CalendarDay)
        self.assertIsInstance(month.condition_ranges, tuple)
        self.assertIsInstance(month.condition_ranges[0], CalendarConditionRange)

    def test_each_model_requires_exact_fields(self):
        for model, fixture, required_field in self.cases:
            with self.subTest(model=model.__name__, mismatch="missing"):
                payload = fixture()
                del payload[required_field]
                with self.assertRaises(pyairbnb.CalendarContractError) as caught:
                    model.from_dict(payload)
                issue = caught.exception.issues[0]
                self.assertEqual(issue.kind, "missing_field")
                self.assertEqual(issue.path, f"$.{required_field}")

            with self.subTest(model=model.__name__, mismatch="extra"):
                payload = fixture()
                payload["newField"] = "new"
                with self.assertRaises(pyairbnb.CalendarContractError) as caught:
                    model.from_dict(payload)
                issue = caught.exception.issues[0]
                self.assertEqual(issue.kind, "extra_field")
                self.assertEqual(issue.path, "$.newField")

    def test_leaf_model_accumulates_all_local_issues(self):
        payload = price_fixture()
        del payload["localPriceFormatted"]
        payload["newField"] = "new"
        payload["__typename"] = "UnknownPrice"

        with self.assertRaises(pyairbnb.CalendarContractError) as caught:
            CalendarDayPrice.from_dict(payload)

        self.assertEqual(
            [(issue.path, issue.kind) for issue in caught.exception.issues],
            [
                ("$.localPriceFormatted", "missing_field"),
                ("$.newField", "extra_field"),
                ("$.__typename", "invalid_value"),
            ],
        )

    def test_each_model_rejects_an_invalid_container_at_the_supplied_path(self):
        for model, _, _ in self.cases:
            with self.subTest(model=model.__name__):
                with self.assertRaises(pyairbnb.CalendarContractError) as caught:
                    model.from_dict([], path="$.fragment")
                issue = caught.exception.issues[0]
                self.assertEqual(issue.kind, "invalid_container")
                self.assertEqual(issue.path, "$.fragment")

    def test_each_model_rejects_invalid_scalar_types(self):
        cases = (
            (CalendarDayPrice, price_fixture, "localPriceFormatted", 1),
            (CalendarDay, day_fixture, "available", 1),
            (CalendarConditions, conditions_fixture, "minNights", True),
            (CalendarConditionRange, condition_range_fixture, "startDate", 1),
            (CalendarMonth, month_fixture, "month", True),
        )
        for model, fixture, field, invalid in cases:
            with self.subTest(model=model.__name__):
                payload = fixture()
                payload[field] = invalid
                with self.assertRaises(pyairbnb.CalendarContractError) as caught:
                    model.from_dict(payload)
                issue = caught.exception.issues[0]
                self.assertEqual(issue.kind, "invalid_type")
                self.assertEqual(issue.path, f"$.{field}")

    def test_each_model_rejects_invalid_values(self):
        cases = (
            (CalendarDayPrice, price_fixture, "__typename", "UnknownPrice"),
            (CalendarDay, day_fixture, "calendarDate", "2026-02-30"),
            (CalendarConditions, conditions_fixture, "endDayOfWeek", "MONDAY"),
            (CalendarConditionRange, condition_range_fixture, "endDate", "2026-02-30"),
            (CalendarMonth, month_fixture, "month", 13),
        )
        for model, fixture, field, invalid in cases:
            with self.subTest(model=model.__name__):
                payload = fixture()
                payload[field] = invalid
                with self.assertRaises(pyairbnb.CalendarContractError) as caught:
                    model.from_dict(payload)
                issue = caught.exception.issues[0]
                self.assertEqual(issue.kind, "invalid_value")
                self.assertEqual(issue.path, f"$.{field}")

    def test_parent_models_delegate_and_aggregate_child_issues(self):
        day = day_fixture()
        del day["price"]["localPriceFormatted"]
        with self.assertRaises(pyairbnb.CalendarContractError) as caught:
            CalendarDay.from_dict(day, path="$[3]")
        self.assertEqual(
            caught.exception.issues[0].path,
            "$[3].price.localPriceFormatted",
        )

        condition_range = condition_range_fixture()
        condition_range["conditions"]["minNights"] = -1
        with self.assertRaises(pyairbnb.CalendarContractError) as caught:
            CalendarConditionRange.from_dict(condition_range, path="$[4]")
        self.assertEqual(caught.exception.issues[0].path, "$[4].conditions.minNights")

        month = month_fixture()
        month["days"][0]["available"] = 1
        month["conditionRanges"][0]["conditions"]["maxNights"] = -1
        with self.assertRaises(pyairbnb.CalendarContractError) as caught:
            CalendarMonth.from_dict(month, path="$[5]")
        self.assertEqual(
            [issue.path for issue in caught.exception.issues],
            [
                "$[5].days[0].available",
                "$[5].conditionRanges[0].conditions.maxNights",
            ],
        )

    def test_month_aggregates_every_item_in_both_child_collections(self):
        month = month_fixture()
        month["days"].append(day_fixture())
        month["conditionRanges"].append(condition_range_fixture())
        month["days"][0]["available"] = 1
        month["days"][1]["calendarDate"] = "invalid"
        month["conditionRanges"][0]["conditions"]["minNights"] = -1
        month["conditionRanges"][1]["conditions"]["maxNights"] = -1

        with self.assertRaises(pyairbnb.CalendarContractError) as caught:
            CalendarMonth.from_dict(month)

        self.assertEqual(
            [issue.path for issue in caught.exception.issues],
            [
                "$.days[0].available",
                "$.days[1].calendarDate",
                "$.conditionRanges[0].conditions.minNights",
                "$.conditionRanges[1].conditions.maxNights",
            ],
        )

    def test_range_end_cannot_precede_start(self):
        payload = condition_range_fixture()
        payload["startDate"] = "2026-08-02"

        with self.assertRaises(pyairbnb.CalendarContractError) as caught:
            CalendarConditionRange.from_dict(payload)

        issue = caught.exception.issues[0]
        self.assertEqual(issue.kind, "invalid_value")
        self.assertEqual(issue.path, "$.endDate")
        self.assertEqual(issue.message, "endDate cannot be before startDate")

    def test_every_result_is_frozen(self):
        for model, fixture, _ in self.cases:
            with self.subTest(model=model.__name__):
                result = model.from_dict(fixture())
                with self.assertRaises(FrozenInstanceError):
                    result.typename = "changed"


if __name__ == "__main__":
    unittest.main()
