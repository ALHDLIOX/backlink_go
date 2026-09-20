"""cli for Backlink Operations V1."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import argparse
import json
import sys
from backlink_records.credentials import (
    SCOPES,
    authenticate,
    backup_runtime_state,
    build_gmail_service,
    build_service,
    default_config_dir,
    read_json_file,
    validate_desktop_client,
    write_private_json,
    writer_lock,
)
from backlink_records.gmail_store import read_message, search_messages
from backlink_records.formatting import DEFAULT_TITLE, format_workbook
from backlink_records.migrations.runner import migrate_schema_v9
from backlink_records.model import (
    RecordValidationError,
    SCHEMA_VERSION,
    TABLE_HEADERS,
    export_campaign_markdown,
    prepare_record,
)
from backlink_records.operations import (
    append_event,
    doctor,
    placement_history,
    upsert,
    workbook_audit,
)
from backlink_records.reconciliation import safe_error_message
from backlink_records.sheets_store import GoogleSheetsStore, load_store

def dry_run(command: str, payload: dict[str, Any] | None = None, title: str | None = None) -> dict[str, object]:
    if command == "init":
        return {
            "dry_run": True,
            "network_access": False,
            "title": title or DEFAULT_TITLE,
            "schema_version": SCHEMA_VERSION,
            "worksheets": {name: headers for name, headers in TABLE_HEADERS.items()},
        }
    if payload is None:
        raise RecordValidationError("dry-run payload is required")
    kind = {
        "upsert-platform": "platform",
        "upsert-campaign": "campaign",
        "upsert-placement": "placement",
        "append-event": "event",
    }[command]
    prepared = prepare_record(kind, payload)
    key_field = {
        "platform": "platform_id", "campaign": "campaign_id",
        "placement": "idempotency_key", "event": "event_id",
    }[kind]
    return {
        "dry_run": True,
        "network_access": False,
        "deduplication_checked": False,
        "command": command,
        "key": prepared[key_field],
        "valid": True,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--config-dir", type=Path, default=default_config_dir())
    commands = result.add_subparsers(dest="command", required=True)

    auth_parser = commands.add_parser("auth")
    auth_parser.add_argument("--client-secret", type=Path, required=True)
    auth_parser.add_argument("--replace", action="store_true")
    auth_parser.add_argument("--dry-run", action="store_true")

    init_parser = commands.add_parser("init")
    init_parser.add_argument("--title", default=DEFAULT_TITLE)
    init_parser.add_argument("--replace-existing-config", action="store_true")
    init_parser.add_argument("--dry-run", action="store_true")

    commands.add_parser("doctor")
    commands.add_parser("format-workbook")
    commands.add_parser("migrate-schema-v5")
    commands.add_parser("migrate-schema-v6")
    commands.add_parser("migrate-schema-v7")
    commands.add_parser("migrate-schema-v8")
    commands.add_parser("migrate-schema-v9")

    for name in (
        "upsert-platform", "upsert-campaign", "upsert-placement", "append-event",
    ):
        item = commands.add_parser(name)
        item.add_argument("--input", type=Path, required=True)
        item.add_argument("--dry-run", action="store_true")
        if name == "upsert-placement":
            item.add_argument("--correction-event-id", help="Linked event for a verified unsubmitted awaiting-approval to waiting-badge correction")

    audit_parser = commands.add_parser("audit")
    audit_parser.add_argument("--campaign-id")
    audit_parser.add_argument("--json", action="store_true")

    export_parser = commands.add_parser("export-md")
    export_parser.add_argument("--campaign-id", required=True)
    export_parser.add_argument("--output", type=Path, required=True)

    history_parser = commands.add_parser("placement-history")
    history_parser.add_argument("--product-id", required=True)
    history_parser.add_argument("--platform-domain")
    history_parser.add_argument("--json", action="store_true")

    gmail_search = commands.add_parser("gmail-search")
    gmail_search.add_argument("--query", required=True)
    gmail_search.add_argument("--max-results", type=int, default=10)
    gmail_search.add_argument("--json", action="store_true")

    gmail_read = commands.add_parser("gmail-read")
    gmail_read.add_argument("--message-id", required=True)
    gmail_read.add_argument("--json", action="store_true")

    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    config_dir: Path = args.config_dir
    try:
        if args.command == "auth":
            if args.dry_run:
                client_config = read_json_file(args.client_secret)
                validate_desktop_client(client_config)
                output = {
                    "dry_run": True,
                    "network_access": False,
                    "command": "auth",
                    "client_secret": "valid desktop OAuth JSON",
                    "scopes": list(SCOPES),
                }
            else:
                with writer_lock(config_dir):
                    output = authenticate(config_dir, args.client_secret, replace=args.replace)
        elif args.command == "init":
            if args.dry_run:
                output = dry_run("init", title=args.title)
            else:
                with writer_lock(config_dir):
                    config_path = config_dir / "v1-sheets.json"
                    if config_path.exists() and not args.replace_existing_config:
                        raise RecordValidationError(
                            "workbook is already configured; use --replace-existing-config to create a new one"
                        )
                    store, config = GoogleSheetsStore.create(build_service(config_dir), args.title)
                    store.verify_schema()
                    backup = backup_runtime_state(config_dir, ("v1-sheets.json",))
                    write_private_json(config_path, config)
                    config["backup"] = str(backup) if backup else None
                output = config
        elif args.command in {"migrate-schema-v5", "migrate-schema-v6", "migrate-schema-v7", "migrate-schema-v8", "migrate-schema-v9"}:
            with writer_lock(config_dir):
                output = migrate_schema_v9(config_dir)
        elif args.command == "doctor":
            output = doctor(config_dir)
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0 if output["sheets"] == "ok" and output["gmail"] == "ok" else 1
        elif args.command == "format-workbook":
            with writer_lock(config_dir):
                output = format_workbook(load_store(config_dir))
        elif args.command.startswith("upsert-") or args.command == "append-event":
            payload = read_json_file(args.input)
            if args.dry_run:
                output = dry_run(args.command, payload=payload)
            else:
                with writer_lock(config_dir):
                    store = load_store(config_dir)
                    if args.command == "append-event":
                        output = append_event(store, payload)
                    else:
                        kind = {
                            "upsert-platform": "platform",
                            "upsert-campaign": "campaign",
                            "upsert-placement": "placement",
                        }[args.command]
                        output = upsert(store, kind, payload, correction_event_id=getattr(args, "correction_event_id", None))
        elif args.command == "audit":
            result = workbook_audit(load_store(config_dir), args.campaign_id)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Valid: {result['valid']}")
                print(f"Total placements: {result['total_placements']}")
                for key, count in result["status_counts"].items():
                    print(f"{key}: {count}")
                for error in result["errors"]:
                    print(f"ERROR: {error}")
            return 0 if result["valid"] else 1
        elif args.command == "export-md":
            store = load_store(config_dir)
            result = workbook_audit(store, args.campaign_id)
            if not result["valid"]:
                raise RecordValidationError("cannot export an invalid campaign")
            campaigns = [
                item for item in store.records("Campaigns") if item["campaign_id"] == args.campaign_id
            ]
            placements = [
                item for item in store.records("Placements") if item["campaign_id"] == args.campaign_id
            ]
            keys = {item["idempotency_key"] for item in placements}
            events = [item for item in store.records("Events") if item["idempotency_key"] in keys]
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                export_campaign_markdown(campaigns[0], placements, events),
                encoding="utf-8",
            )
            output = {"exported": True, "campaign_id": args.campaign_id, "output": str(args.output)}
        elif args.command == "placement-history":
            items = placement_history(load_store(config_dir), args.product_id, args.platform_domain)
            if args.json:
                print(json.dumps({"placements": items, "count": len(items)}, ensure_ascii=False, indent=2))
            else:
                for item in items:
                    print(f"{item['placement_id']} | {item['platform_domain']} | {item['status']} | {item['anchor_text']}")
                if not items:
                    print("No placement history found")
            return 0
        elif args.command == "gmail-search":
            output = search_messages(build_gmail_service(config_dir), args.query, args.max_results)
            if args.json:
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                for item in output["messages"]:
                    print(f"{item['message_id']} | {item['date']} | {item['from']} | {item['subject']}")
                    if item["snippet"]:
                        print(f"  {item['snippet']}")
                if not output["messages"]:
                    print("No messages found")
            return 0
        elif args.command == "gmail-read":
            output = read_message(build_gmail_service(config_dir), args.message_id)
            if args.json:
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                print(f"From: {output['from']}")
                print(f"To: {output['to']}")
                print(f"Date: {output['date']}")
                print(f"Subject: {output['subject']}")
                print()
                print(output["body"])
                if output["truncated"]:
                    print("\n[body truncated at 100 KiB]")
                if output["attachments"]:
                    print("\nAttachments:")
                    for item in output["attachments"]:
                        print(f"- {item['filename']} ({item['mime_type']}, {item['size']} bytes)")
            return 0
        else:  # pragma: no cover
            raise RecordValidationError("unknown command")
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except RecordValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Avoid stack traces and credential-bearing API diagnostics.
        print(f"ERROR: {type(exc).__name__}: {safe_error_message(exc)}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("ERROR: operation cancelled", file=sys.stderr)
        return 130
