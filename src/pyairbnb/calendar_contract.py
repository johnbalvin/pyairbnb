from dataclasses import dataclass


@dataclass(frozen=True)
class CalendarContractIssue:
    path: str
    kind: str
    expected: str | None
    actual: str | None
    message: str


def _format_contract_mismatch(issues: tuple[CalendarContractIssue, ...]) -> str:
    lines = [f"Calendar contract mismatch: {len(issues)} issues"]
    lines.extend(f"- {issue.path}: {issue.message}" for issue in issues)
    return "\n".join(lines)


class CalendarContractError(ValueError):
    def __init__(self, issues: tuple[CalendarContractIssue, ...]):
        self.issues = tuple(issues)
        super().__init__(_format_contract_mismatch(self.issues))


class CalendarExtractionError(ValueError):
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Calendar could not be extracted at {path}")


class CalendarContractWarning(UserWarning):
    def __init__(self, issues: tuple[CalendarContractIssue, ...]):
        self.issues = tuple(issues)
        super().__init__(_format_contract_mismatch(self.issues))
