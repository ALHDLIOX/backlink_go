"""Reorder schema 7 Placements and normalize persisted timestamps."""
from ..model import TABLE_HEADERS, compact_record_timestamps


def migrate_records(source: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, str]]]:
    return {
        tab: [compact_record_timestamps({key: row.get(key, "") for key in headers})
              for row in source.get(tab, [])]
        for tab, headers in TABLE_HEADERS.items()
    }
