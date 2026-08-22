import re
from collections.abc import Callable
from datetime import date
from typing import TypeVar, cast

from pyairbnb.calendar_contract import CalendarContractError, CalendarContractIssue

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_T = TypeVar("_T")


def _issue(
    path: str,
    kind: str,
    expected: str | None,
    value: object,
    message: str,
    *,
    actual: str | None = None,
) -> CalendarContractIssue:
    if actual is None:
        actual = type(value).__name__
    return CalendarContractIssue(path, kind, expected, actual, message)


def require_list(data: object, *, path: str) -> list[object]:
    if type(data) is not list:
        raise CalendarContractError(
            (_issue(path, "invalid_container", "list", data, "expected a list"),)
        )
    return cast(list[object], data)


class _ObjectReader:
    def __init__(
        self,
        data: object,
        *,
        path: str,
        expected_fields: set[str],
    ) -> None:
        self.path = path
        self.issues: list[CalendarContractIssue] = []
        self._data: dict[object, object] | None = None

        if type(data) is not dict:
            self.issues.append(
                _issue(path, "invalid_container", "dict", data, "expected an object")
            )
            return

        self._data = cast(dict[object, object], data)
        received_fields = set(self._data)
        for missing_field in sorted(expected_fields - received_fields):
            self.issues.append(
                CalendarContractIssue(
                    f"{path}.{missing_field}",
                    "missing_field",
                    "present",
                    None,
                    "missing required field",
                )
            )
        for extra_field in sorted(received_fields - expected_fields, key=str):
            self.issues.append(
                _issue(
                    f"{path}.{extra_field}",
                    "extra_field",
                    None,
                    self._data[extra_field],
                    "unexpected field",
                )
            )

    def _value(self, field: str) -> tuple[bool, object]:
        if self._data is None or field not in self._data:
            return False, None
        return True, self._data[field]

    def string(self, field: str) -> str | None:
        present, value = self._value(field)
        if not present:
            return None
        if type(value) is not str:
            self.issues.append(
                _issue(
                    f"{self.path}.{field}",
                    "invalid_type",
                    "str",
                    value,
                    "expected a string",
                )
            )
            return None
        return cast(str, value)

    def nullable_string(self, field: str) -> str | None:
        present, value = self._value(field)
        if not present or value is None:
            return None
        return self.string(field)

    def boolean(self, field: str) -> bool | None:
        present, value = self._value(field)
        if not present:
            return None
        if type(value) is not bool:
            self.issues.append(
                _issue(
                    f"{self.path}.{field}",
                    "invalid_type",
                    "bool",
                    value,
                    "expected a boolean",
                )
            )
            return None
        return cast(bool, value)

    def nullable_boolean(self, field: str) -> bool | None:
        present, value = self._value(field)
        if not present or value is None:
            return None
        return self.boolean(field)

    def integer(
        self,
        field: str,
        *,
        minimum: int = 0,
        maximum: int | None = None,
    ) -> int | None:
        present, value = self._value(field)
        if not present:
            return None
        if type(value) is not int:
            self.issues.append(
                _issue(
                    f"{self.path}.{field}",
                    "invalid_type",
                    "int",
                    value,
                    "expected an integer",
                )
            )
            return None

        converted = cast(int, value)
        if converted < minimum or (maximum is not None and converted > maximum):
            expected = f"int from {minimum}"
            if maximum is not None:
                expected += f" to {maximum}"
            self.issues.append(
                _issue(
                    f"{self.path}.{field}",
                    "invalid_value",
                    expected,
                    value,
                    f"expected {expected}",
                    actual=repr(value),
                )
            )
            return None
        return converted

    def date(self, field: str) -> str | None:
        value = self.string(field)
        if value is None:
            return None
        if not _DATE_PATTERN.fullmatch(value):
            self.issues.append(
                _issue(
                    f"{self.path}.{field}",
                    "invalid_value",
                    "date in YYYY-MM-DD format",
                    value,
                    "expected a date in YYYY-MM-DD format",
                    actual=repr(value),
                )
            )
            return None
        try:
            date.fromisoformat(value)
        except ValueError:
            self.issues.append(
                _issue(
                    f"{self.path}.{field}",
                    "invalid_value",
                    "valid calendar date",
                    value,
                    "expected a valid calendar date",
                    actual=repr(value),
                )
            )
            return None
        return value

    def literal(self, field: str, expected: str) -> str | None:
        value = self.string(field)
        if value is not None and value != expected:
            self.issues.append(
                _issue(
                    f"{self.path}.{field}",
                    "invalid_value",
                    expected,
                    value,
                    f"expected {expected}",
                    actual=repr(value),
                )
            )
            return None
        return value

    def null(self, field: str) -> None:
        present, value = self._value(field)
        if present and value is not None:
            self.issues.append(
                _issue(
                    f"{self.path}.{field}",
                    "invalid_value",
                    "null",
                    value,
                    "expected null",
                    actual=repr(value),
                )
            )

    def model(
        self,
        field: str,
        factory: Callable[..., _T],
    ) -> _T | None:
        present, value = self._value(field)
        if not present:
            return None
        try:
            return factory(value, path=f"{self.path}.{field}")
        except CalendarContractError as error:
            self.issues.extend(error.issues)
            return None

    def models(
        self,
        field: str,
        factory: Callable[..., _T],
    ) -> tuple[_T, ...] | None:
        present, value = self._value(field)
        if not present:
            return None
        if type(value) is not list:
            self.issues.append(
                _issue(
                    f"{self.path}.{field}",
                    "invalid_container",
                    "list",
                    value,
                    "expected a list",
                )
            )
            return None

        converted: list[_T] = []
        valid = True
        for index, item in enumerate(cast(list[object], value)):
            try:
                converted.append(factory(item, path=f"{self.path}.{field}[{index}]"))
            except CalendarContractError as error:
                self.issues.extend(error.issues)
                valid = False
        if not valid:
            return None
        return tuple(converted)

    def invalid_value(
        self,
        field: str,
        *,
        expected: str,
        actual: object,
        message: str,
    ) -> None:
        self.issues.append(
            _issue(
                f"{self.path}.{field}",
                "invalid_value",
                expected,
                actual,
                message,
                actual=repr(actual),
            )
        )

    def raise_if_invalid(self) -> None:
        if self.issues:
            raise CalendarContractError(tuple(self.issues))
