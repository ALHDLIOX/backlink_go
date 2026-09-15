"""reconciliation for Backlink Operations V1."""
from __future__ import annotations
from typing import Callable
import re
from backlink_records.model import RecordValidationError, TABLE_HEADERS
from backlink_records.sheets_store import GoogleSheetsStore, records_with_rows

def records_equal(headers: list[str], expected: dict[str, object], actual: dict[str, object]) -> bool:
    return all(str(expected.get(header, "")) == str(actual.get(header, "")) for header in headers)


def is_retryable_write_error(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    status = getattr(getattr(exc, "resp", None), "status", None)
    return status == 429 or isinstance(status, int) and 500 <= status <= 599


def safe_error_message(exc: Exception) -> str:
    message = str(exc).replace("\n", " ")
    message = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "[redacted-email]", message, flags=re.I)
    message = re.sub(
        r"([?&](?:token|key|api_key|apikey|code|state|session|auth|password|otp|signature|sig)=)[^&#\s]+",
        r"\1[redacted]",
        message,
        flags=re.I,
    )
    message = re.sub(r"(?<![\w-])\+\d[\d\s().-]{7,}\d(?![\w-])", "[redacted-phone]", message)
    message = re.sub(
        r"((?:password|passcode|otp|cookie|session[_ ]?id|oauth[_ ]?code)\s*[:=]\s*)\S+",
        r"\1[redacted]",
        message,
        flags=re.I,
    )
    message = re.sub(r"Bearer\s+\S+", "Bearer [redacted]", message, flags=re.I)
    return message[:500]


def write_with_reconciliation(
    store: GoogleSheetsStore,
    tab_name: str,
    key_field: str,
    key_value: str,
    expected: dict[str, object],
    operation: Callable[[], None],
    *,
    original: tuple[int, dict[str, object]] | None = None,
) -> None:
    """Retry only when readback proves the original state is still present.

    A moved or deleted update target is a conflict because the operation uses
    a physical row number. A failed readback never authorizes another write.
    """
    headers = TABLE_HEADERS[tab_name]
    for attempt in range(2):
        error = None
        try:
            operation()
        except Exception as exc:
            if not is_retryable_write_error(exc):
                raise RecordValidationError(f"non-retryable write failure in {tab_name}") from exc
            error = exc
        matches = [(row, record) for row, record in records_with_rows(store, tab_name)
                   if record.get(key_field) == key_value]
        if len(matches) > 1:
            raise RecordValidationError(f"duplicate {key_field} rows after write in {tab_name}")
        found = matches[0] if matches else None
        if found and records_equal(headers, expected, found[1]):
            return
        unchanged = (
            found is None if original is None else
            found is not None and found[0] == original[0]
            and records_equal(headers, original[1], found[1])
        )
        if not unchanged:
            raise RecordValidationError(f"conflicting row found after write in {tab_name}") from error
        if error is None:
            raise RecordValidationError(f"written row could not be read back from {tab_name}")
        if attempt == 1:
            raise RecordValidationError(f"write failed after reconciliation in {tab_name}") from error
