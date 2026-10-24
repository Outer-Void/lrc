"""Failures and exit codes (docs/USAGE.md#exit-codes).

An error means LRC did not do what was asked. A validation verdict of "fail" or a migration blocked by conflicts
is a result, not an error, and has its own exit code so callers can tell the cases apart.
"""

from __future__ import annotations

import enum
from typing import Any

EXIT_OK = 0  # done (or nothing to do)
EXIT_CHECK_FAILED = 1  # validation failed, migration blocked by conflicts, or the DAT gate failed; nothing was changed
EXIT_USAGE = 2  # bad command line
EXIT_FAILURE = 3  # LRC could not do the operation; any partial change was rolled back
EXIT_INCONSISTENT = 4  # the operation failed AND its rollback failed: the target needs attention


class ErrorCode(enum.StrEnum):
    INVALID_INPUT = "INVALID_INPUT"
    SPEC_NOT_FOUND = "SPEC_NOT_FOUND"
    SPEC_UNREADABLE = "SPEC_UNREADABLE"
    SPEC_INVALID = "SPEC_INVALID"
    PLAN_INVALID = "PLAN_INVALID"
    UNDEFINED_VARIABLE = "UNDEFINED_VARIABLE"
    VARIABLE_INVALID = "VARIABLE_INVALID"
    TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
    TEMPLATE_INVALID = "TEMPLATE_INVALID"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    TARGET_EXISTS = "TARGET_EXISTS"
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
    TARGET_INVALID = "TARGET_INVALID"
    NOT_MANAGED = "NOT_MANAGED"
    ALREADY_MANAGED = "ALREADY_MANAGED"
    MANIFEST_INVALID = "MANIFEST_INVALID"
    MIGRATION_CONFLICT = "MIGRATION_CONFLICT"
    NOTHING_TO_ROLL_BACK = "NOTHING_TO_ROLL_BACK"
    ROLLBACK_CONFLICT = "ROLLBACK_CONFLICT"
    JOURNAL_INVALID = "JOURNAL_INVALID"
    GIT_UNAVAILABLE = "GIT_UNAVAILABLE"
    GIT_FAILED = "GIT_FAILED"
    DAT_UNAVAILABLE = "DAT_UNAVAILABLE"
    DAT_FAILED = "DAT_FAILED"
    VERIFY_FAILED = "VERIFY_FAILED"
    IO_ERROR = "IO_ERROR"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Codes that are the caller's "no": nothing was changed and the answer is a result, not a malfunction.
CHECK_CODES = frozenset({ErrorCode.MIGRATION_CONFLICT, ErrorCode.ROLLBACK_CONFLICT})


class LrcError(Exception):
    def __init__(self, code: ErrorCode, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details: dict[str, Any] = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code.value, "message": self.message, "details": self.details}

    @property
    def exit_code(self) -> int:
        if self.code is ErrorCode.ROLLBACK_FAILED:
            return EXIT_INCONSISTENT
        if self.code in CHECK_CODES:
            return EXIT_CHECK_FAILED
        return EXIT_FAILURE
