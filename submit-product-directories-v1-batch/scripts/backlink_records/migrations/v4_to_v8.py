"""migrations / v4_to_v8 for Backlink Operations V1."""
from __future__ import annotations
from backlink_records.model import SCHEMA_V6_TABLE_HEADERS

def migrate_legacy_record(tab_name: str, record: dict[str, object]) -> dict[str, str]:
    result = {h: str(record.get(h, "")) for h in SCHEMA_V6_TABLE_HEADERS.get(tab_name, [])}
    if tab_name == "Platforms": result["platform_type"] = "directory"
    if tab_name == "Campaigns": result.update(campaign_mode="directory", workflow_version="SPD V1 Batch")
    if tab_name == "Events": result["record_type"] = "submission"
    return result



def migrate_records(source: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, str]]]:
    from .v6_to_v8 import migrate_v6_records

    return migrate_v6_records({
        tab: [migrate_legacy_record(tab, row) for row in rows]
        for tab, rows in source.items()
    })
