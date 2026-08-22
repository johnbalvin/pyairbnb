def price_fixture() -> dict[str, object]:
    return {
        "__typename": "MerlinCalendarDayPrice",
        "localPriceFormatted": None,
    }


def day_fixture() -> dict[str, object]:
    return {
        "__typename": "MerlinCalendarDay",
        "calendarDate": "2026-08-01",
        "available": True,
        "availableForCheckin": True,
        "availableForCheckout": False,
        "bookable": None,
        "minNights": 1,
        "maxNights": 365,
        "price": price_fixture(),
    }


def conditions_fixture() -> dict[str, object]:
    return {
        "__typename": "MerlinCalendarConditions",
        "closedToArrival": False,
        "closedToDeparture": False,
        "endDayOfWeek": None,
        "minNights": 1,
        "maxNights": 365,
    }


def condition_range_fixture() -> dict[str, object]:
    return {
        "__typename": "MerlinCalendarConditionRange",
        "startDate": "2026-08-01",
        "endDate": "2026-08-01",
        "conditions": conditions_fixture(),
    }


def month_fixture() -> dict[str, object]:
    return {
        "__typename": "MerlinCalendarMonth",
        "listingId": "123",
        "month": 8,
        "year": 2026,
        "days": [day_fixture()],
        "conditionRanges": [condition_range_fixture()],
    }


def calendar_fixture() -> list[dict[str, object]]:
    return [month_fixture()]
