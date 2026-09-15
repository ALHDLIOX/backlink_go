"""Schema 5 shares the directory/article layout of schema 6, without social rows."""
from .v6_to_v8 import migrate_v6_records


def migrate_records(source: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, str]]]:
    return migrate_v6_records(source)
