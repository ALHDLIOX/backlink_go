from __future__ import annotations

import base64
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from backlink_records import credentials, gmail_store  # noqa: E402
from backlink_records import cli  # noqa: E402
from backlink_records.model import RecordValidationError  # noqa: E402


def encoded(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


class Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeGmail:
    def __init__(self, pages=None, messages=None, attachments=None):
        self.pages = list(pages or [])
        self.message_data = messages or {}
        self.attachment_data = attachments or {}
        self.resource = ""
        self.list_calls = []

    def users(self):
        return self

    def messages(self):
        self.resource = "messages"
        return self

    def attachments(self):
        self.resource = "attachments"
        return self

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        return Request(self.pages.pop(0))

    def get(self, **kwargs):
        if self.resource == "attachments":
            return Request(self.attachment_data[kwargs["id"]])
        return Request(self.message_data[kwargs["id"]])


class GmailStoreTests(unittest.TestCase):
    def test_search_paginates_and_reads_metadata(self):
        service = FakeGmail(
            pages=[
                {"messages": [{"id": "m1"}], "nextPageToken": "p2"},
                {"messages": [{"id": "m2"}]},
            ],
            messages={
                "m1": {"id": "m1", "threadId": "t1", "snippet": "one\x1b[31m", "payload": {"headers": [
                    {"name": "From", "value": "Sender One <one@example.test>"},
                    {"name": "Subject", "value": "First"},
                    {"name": "Date", "value": "Mon"},
                ]}},
                "m2": {"id": "m2", "threadId": "t2", "snippet": "two", "payload": {"headers": [
                    {"name": "From", "value": "Sender Two <two@example.test>"},
                    {"name": "Subject", "value": "Second"},
                    {"name": "Date", "value": "Tue"},
                ]}},
            },
        )

        result = gmail_store.search_messages(service, "newer_than:7d", 2)

        self.assertEqual(result["count"], 2)
        self.assertEqual([item["message_id"] for item in result["messages"]], ["m1", "m2"])
        self.assertNotIn("\x1b", result["messages"][0]["snippet"])
        self.assertEqual([call["pageToken"] for call in service.list_calls], [None, "p2"])

    def test_search_rejects_empty_query_and_large_limit(self):
        with self.assertRaisesRegex(RecordValidationError, "must not be empty"):
            gmail_store.search_messages(FakeGmail(), "  ")
        with self.assertRaisesRegex(RecordValidationError, "between 1 and 50"):
            gmail_store.search_messages(FakeGmail(), "in:inbox", 51)

    def test_read_prefers_plain_text_and_lists_attachment_metadata(self):
        service = FakeGmail(messages={
            "m1": {
                "id": "m1", "threadId": "t1", "snippet": "preview",
                "payload": {
                    "mimeType": "multipart/mixed",
                    "headers": [
                        {"name": "From", "value": "Sender <sender@example.test>"},
                        {"name": "To", "value": "Reader <reader@example.test>"},
                        {"name": "Subject", "value": "=?utf-8?b?5rWL6K+V?="},
                        {"name": "Date", "value": "Today"},
                    ],
                    "parts": [
                        {"mimeType": "text/plain", "body": {"data": encoded("plain body")}, "headers": []},
                        {"mimeType": "text/html", "body": {"data": encoded("<p>html body</p>")}, "headers": []},
                        {"mimeType": "application/pdf", "filename": "guide.pdf", "body": {"attachmentId": "a1", "size": 321}},
                    ],
                },
            },
        })

        result = gmail_store.read_message(service, "m1")

        self.assertEqual(result["subject"], "测试")
        self.assertEqual(result["body"], "plain body")
        self.assertFalse(result["truncated"])
        self.assertEqual(result["attachments"], [{"filename": "guide.pdf", "mime_type": "application/pdf", "size": 321}])

    def test_html_fallback_and_utf8_safe_truncation(self):
        service = FakeGmail(messages={
            "m1": {"id": "m1", "threadId": "t1", "payload": {
                "mimeType": "text/html",
                "headers": [],
                "body": {"data": encoded("<p>Hello</p><div>世界世界世界</div>")},
            }},
        })
        with patch.object(gmail_store, "MAX_BODY_BYTES", 12):
            result = gmail_store.read_message(service, "m1")
        self.assertTrue(result["truncated"])
        result["body"].encode("utf-8")
        self.assertIn("Hello", result["body"])

    def test_externalized_text_body_is_fetched_but_file_attachment_is_not(self):
        service = FakeGmail(
            messages={"m1": {"id": "m1", "threadId": "t1", "payload": {
                "mimeType": "text/plain", "headers": [], "body": {"attachmentId": "body-1"},
            }}},
            attachments={"body-1": {"data": encoded("external body")}},
        )
        self.assertEqual(gmail_store.read_message(service, "m1")["body"], "external body")


class FakeCredentials:
    def __init__(self, scopes, *, refresh_token="refresh"):
        self.granted_scopes = scopes
        self.scopes = scopes
        self.refresh_token = refresh_token

    def to_json(self):
        return json.dumps({
            "token": "new-token",
            "refresh_token": self.refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "new-client",
            "client_secret": "new-secret",
            "scopes": self.scopes,
        })


class FakeFlow:
    def __init__(self, result):
        self.result = result
        self.kwargs = None

    def run_local_server(self, **kwargs):
        self.kwargs = kwargs
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class CredentialTests(unittest.TestCase):
    def client(self, marker="new"):
        return {"installed": {
            "client_id": f"{marker}-client",
            "client_secret": f"{marker}-secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }}

    def prepare(self, root: str):
        config = Path(root) / "runtime"
        credentials.write_private_json(config / "google-oauth-client.json", self.client("old"))
        credentials.write_private_json(config / "google-token.json", {"scopes": [credentials.SHEETS_SCOPE], "token": "old"})
        credentials.write_private_json(config / "v1-sheets.json", {"schema_version": "8", "spreadsheet_id": "old-sheet"})
        source = Path(root) / "new.json"
        source.write_text(json.dumps(self.client("new")), encoding="utf-8")
        return config, source

    def test_replace_backs_up_then_activates_both_scopes(self):
        with tempfile.TemporaryDirectory() as root:
            config, source = self.prepare(root)
            flow = FakeFlow(FakeCredentials(credentials.SCOPES))
            with patch("google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file", return_value=flow):
                result = credentials.authenticate(config, source, replace=True)

            self.assertEqual(result["scopes"], credentials.SCOPES)
            backup = Path(result["backup"])
            self.assertEqual(json.loads((backup / "v1-sheets.json").read_text())["spreadsheet_id"], "old-sheet")
            self.assertEqual(json.loads((config / "google-oauth-client.json").read_text())["installed"]["client_id"], "new-client")
            self.assertEqual(set(json.loads((config / "google-token.json").read_text())["scopes"]), set(credentials.SCOPES))
            self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o700)
            self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in backup.iterdir()))
            self.assertEqual(flow.kwargs["access_type"], "offline")
            self.assertIn("select_account", flow.kwargs["prompt"])

    def test_missing_scope_leaves_active_credentials_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            config, source = self.prepare(root)
            original = (config / "google-token.json").read_text()
            flow = FakeFlow(FakeCredentials([credentials.SHEETS_SCOPE]))
            with patch("google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file", return_value=flow):
                with self.assertRaisesRegex(RecordValidationError, "every required scope"):
                    credentials.authenticate(config, source, replace=True)
            self.assertEqual((config / "google-token.json").read_text(), original)

    def test_cancelled_flow_leaves_active_credentials_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            config, source = self.prepare(root)
            original = (config / "google-oauth-client.json").read_text()
            flow = FakeFlow(RuntimeError("cancelled"))
            with patch("google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file", return_value=flow):
                with self.assertRaisesRegex(RuntimeError, "cancelled"):
                    credentials.authenticate(config, source, replace=True)
            self.assertEqual((config / "google-oauth-client.json").read_text(), original)

    def test_refresh_failure_has_safe_reauthorization_error(self):
        class Expired:
            expired = True
            refresh_token = "refresh"
            valid = False

            def refresh(self, _request):
                raise RuntimeError("secret provider response")

        with tempfile.TemporaryDirectory() as root:
            config = Path(root) / "runtime"
            credentials.write_private_json(config / "google-token.json", {"scopes": credentials.SCOPES})
            with patch("google.oauth2.credentials.Credentials.from_authorized_user_file", return_value=Expired()):
                with self.assertRaisesRegex(RecordValidationError, "run auth --replace"):
                    credentials.load_credentials(config)

    def test_init_failure_preserves_existing_workbook_config(self):
        with tempfile.TemporaryDirectory() as root:
            config = Path(root) / "runtime"
            credentials.write_private_json(config / "v1-sheets.json", {"schema_version": "8", "spreadsheet_id": "old-sheet"})
            with patch.object(cli, "build_service", return_value=object()), patch.object(
                cli.GoogleSheetsStore, "create", side_effect=RuntimeError("provider failed")
            ):
                with redirect_stderr(io.StringIO()):
                    code = cli.main(["--config-dir", str(config), "init", "--replace-existing-config"])
            self.assertEqual(code, 3)
            self.assertEqual(json.loads((config / "v1-sheets.json").read_text())["spreadsheet_id"], "old-sheet")


if __name__ == "__main__":
    unittest.main()
