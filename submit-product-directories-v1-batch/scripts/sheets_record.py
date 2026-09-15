#!/usr/bin/env python3
"""Compatibility entry point; implementation lives in backlink_records."""
from backlink_records.cli import (
    dry_run,
    parser,
    main,
)
from backlink_records.credentials import (
    SCOPES,
    CONFIG_ENV,
    default_config_dir,
    ensure_private_dir,
    write_private_json,
    require_private_file,
    read_json_file,
    writer_lock,
    authenticate,
    load_credentials,
    build_service,
)
from backlink_records.formatting import (
    DEFAULT_TITLE,
    METADATA_KEY,
    COLOR_GREEN,
    COLOR_BLUE,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_GRAY,
    fixed_option_colors,
    column_letter,
    workbook_create_body,
    initialization_batch_requests,
    readable_format_requests,
    format_workbook,
)
from backlink_records.migrations.runner import (
    schema_v8_migration_requests,
    migrate_schema_v8,
    migrate_schema_v5,
    migrate_schema_v6,
    migrate_schema_v7,
)
from backlink_records.operations import (
    doctor,
    upsert,
    append_event,
    workbook_audit,
    placement_history,
)
from backlink_records.reconciliation import (
    records_equal,
    is_retryable_write_error,
    safe_error_message,
    write_with_reconciliation,
)
from backlink_records.sheets_store import (
    GoogleSheetsStore,
    load_store,
    records_with_rows,
)

if __name__ == "__main__":
    raise SystemExit(main())
