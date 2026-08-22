from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from pyairbnb.models._validation import _ObjectReader


@dataclass(frozen=True)
class CalendarDayPrice:
    typename: str
    local_price_formatted: str | None

    @classmethod
    def from_dict(
        cls,
        data: object,
        *,
        path: str = "$",
    ) -> CalendarDayPrice:
        reader = _ObjectReader(
            data,
            path=path,
            expected_fields={"__typename", "localPriceFormatted"},
        )
        typename = reader.literal("__typename", "MerlinCalendarDayPrice")
        local_price = reader.nullable_string("localPriceFormatted")
        reader.raise_if_invalid()
        return cls(cast(str, typename), local_price)


@dataclass(frozen=True)
class CalendarDay:
    typename: str
    calendar_date: str
    available: bool
    available_for_checkin: bool
    available_for_checkout: bool
    bookable: bool | None
    min_nights: int
    max_nights: int
    price: CalendarDayPrice

    @classmethod
    def from_dict(
        cls,
        data: object,
        *,
        path: str = "$",
    ) -> CalendarDay:
        reader = _ObjectReader(
            data,
            path=path,
            expected_fields={
                "__typename",
                "calendarDate",
                "available",
                "availableForCheckin",
                "availableForCheckout",
                "bookable",
                "minNights",
                "maxNights",
                "price",
            },
        )
        typename = reader.literal("__typename", "MerlinCalendarDay")
        calendar_date = reader.date("calendarDate")
        available = reader.boolean("available")
        checkin = reader.boolean("availableForCheckin")
        checkout = reader.boolean("availableForCheckout")
        bookable = reader.nullable_boolean("bookable")
        min_nights = reader.integer("minNights")
        max_nights = reader.integer("maxNights")
        price = reader.model("price", CalendarDayPrice.from_dict)
        reader.raise_if_invalid()
        return cls(
            cast(str, typename),
            cast(str, calendar_date),
            cast(bool, available),
            cast(bool, checkin),
            cast(bool, checkout),
            bookable,
            cast(int, min_nights),
            cast(int, max_nights),
            cast(CalendarDayPrice, price),
        )


@dataclass(frozen=True)
class CalendarConditions:
    typename: str
    closed_to_arrival: bool
    closed_to_departure: bool
    end_day_of_week: None
    min_nights: int
    max_nights: int

    @classmethod
    def from_dict(
        cls,
        data: object,
        *,
        path: str = "$",
    ) -> CalendarConditions:
        reader = _ObjectReader(
            data,
            path=path,
            expected_fields={
                "__typename",
                "closedToArrival",
                "closedToDeparture",
                "endDayOfWeek",
                "minNights",
                "maxNights",
            },
        )
        typename = reader.literal("__typename", "MerlinCalendarConditions")
        arrival = reader.boolean("closedToArrival")
        departure = reader.boolean("closedToDeparture")
        reader.null("endDayOfWeek")
        min_nights = reader.integer("minNights")
        max_nights = reader.integer("maxNights")
        reader.raise_if_invalid()
        return cls(
            cast(str, typename),
            cast(bool, arrival),
            cast(bool, departure),
            None,
            cast(int, min_nights),
            cast(int, max_nights),
        )


@dataclass(frozen=True)
class CalendarConditionRange:
    typename: str
    start_date: str
    end_date: str
    conditions: CalendarConditions

    @classmethod
    def from_dict(
        cls,
        data: object,
        *,
        path: str = "$",
    ) -> CalendarConditionRange:
        reader = _ObjectReader(
            data,
            path=path,
            expected_fields={"__typename", "startDate", "endDate", "conditions"},
        )
        typename = reader.literal("__typename", "MerlinCalendarConditionRange")
        start_date = reader.date("startDate")
        end_date = reader.date("endDate")
        conditions = reader.model("conditions", CalendarConditions.from_dict)
        if start_date is not None and end_date is not None and start_date > end_date:
            reader.invalid_value(
                "endDate",
                expected="date on or after startDate",
                actual=end_date,
                message="endDate cannot be before startDate",
            )
        reader.raise_if_invalid()
        return cls(
            cast(str, typename),
            cast(str, start_date),
            cast(str, end_date),
            cast(CalendarConditions, conditions),
        )


@dataclass(frozen=True)
class CalendarMonth:
    typename: str
    listing_id: str
    month: int
    year: int
    days: tuple[CalendarDay, ...]
    condition_ranges: tuple[CalendarConditionRange, ...]

    @classmethod
    def from_dict(
        cls,
        data: object,
        *,
        path: str = "$",
    ) -> CalendarMonth:
        reader = _ObjectReader(
            data,
            path=path,
            expected_fields={
                "__typename",
                "listingId",
                "month",
                "year",
                "days",
                "conditionRanges",
            },
        )
        typename = reader.literal("__typename", "MerlinCalendarMonth")
        listing_id = reader.string("listingId")
        month = reader.integer("month", minimum=1, maximum=12)
        year = reader.integer("year")
        days = reader.models("days", CalendarDay.from_dict)
        condition_ranges = reader.models(
            "conditionRanges", CalendarConditionRange.from_dict
        )
        reader.raise_if_invalid()
        return cls(
            cast(str, typename),
            cast(str, listing_id),
            cast(int, month),
            cast(int, year),
            cast(tuple[CalendarDay, ...], days),
            cast(tuple[CalendarConditionRange, ...], condition_ranges),
        )
