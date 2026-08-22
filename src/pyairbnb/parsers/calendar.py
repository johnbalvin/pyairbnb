from pyairbnb.calendar_contract import CalendarContractError, CalendarContractIssue
from pyairbnb.models import CalendarMonth
from pyairbnb.models._validation import require_list


def parse_calendar(data: object) -> list[CalendarMonth]:
    """Validate and convert an extracted Airbnb calendar payload."""
    items = require_list(data, path="$")
    months: list[CalendarMonth] = []
    issues: list[CalendarContractIssue] = []

    for index, item in enumerate(items):
        try:
            months.append(CalendarMonth.from_dict(item, path=f"$[{index}]"))
        except CalendarContractError as error:
            issues.extend(error.issues)

    if issues:
        raise CalendarContractError(tuple(issues))
    return months
