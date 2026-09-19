"""Read-only Gmail search and message parsing."""
from __future__ import annotations

from email.header import decode_header, make_header
from html.parser import HTMLParser
import base64
import re
from typing import Any

from backlink_records.model import RecordValidationError

MAX_BODY_BYTES = 100 * 1024
MAX_SEARCH_RESULTS = 50
METADATA_HEADERS = ["From", "To", "Subject", "Date", "Content-Type"]


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self.parts)).strip()


def _decode_header(value: str) -> str:
    try:
        decoded = str(make_header(decode_header(value)))
    except (LookupError, UnicodeError):
        decoded = value
    return _sanitize_text(decoded)


def _sanitize_text(value: str) -> str:
    return "".join(character for character in value if character in "\n\t" or ord(character) >= 32)


def _headers(payload: dict[str, Any]) -> dict[str, str]:
    return {
        str(item.get("name", "")).lower(): _decode_header(str(item.get("value", "")))
        for item in payload.get("headers", [])
    }


def _decode_data(data: str, content_type: str = "") -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    match = re.search(r"charset\s*=\s*[\"']?([^;\"']+)", content_type, flags=re.I)
    charset = match.group(1).strip() if match else "utf-8"
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def _truncate(text: str) -> tuple[str, bool]:
    raw = text.encode("utf-8")
    if len(raw) <= MAX_BODY_BYTES:
        return text, False
    return raw[:MAX_BODY_BYTES].decode("utf-8", errors="ignore"), True


def _message_metadata(message: dict[str, Any]) -> dict[str, object]:
    headers = _headers(message.get("payload", {}))
    return {
        "message_id": str(message.get("id", "")),
        "thread_id": str(message.get("threadId", "")),
        "date": headers.get("date", ""),
        "from": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "snippet": _sanitize_text(str(message.get("snippet", ""))),
    }


def search_messages(service: Any, query: str, max_results: int = 10) -> dict[str, object]:
    if not query.strip():
        raise RecordValidationError("Gmail query must not be empty")
    if not 1 <= max_results <= MAX_SEARCH_RESULTS:
        raise RecordValidationError("Gmail max-results must be between 1 and 50")
    listed_items: list[dict[str, Any]] = []
    page_token = None
    while len(listed_items) < max_results:
        listed = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=max_results - len(listed_items),
                pageToken=page_token,
            )
            .execute()
        )
        remaining = max_results - len(listed_items)
        listed_items.extend((listed.get("messages") or [])[:remaining])
        page_token = listed.get("nextPageToken")
        if not page_token:
            break
    messages = []
    for item in listed_items[:max_results]:
        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=item["id"],
                format="metadata",
                metadataHeaders=METADATA_HEADERS[:4],
            )
            .execute()
        )
        messages.append(_message_metadata(message))
    return {"query": query, "count": len(messages), "messages": messages}


def _body_data(service: Any, message_id: str, part: dict[str, Any]) -> str:
    body = part.get("body", {})
    data = str(body.get("data", ""))
    attachment_id = body.get("attachmentId")
    if not data and attachment_id:
        fetched = (
            service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        data = str(fetched.get("data", ""))
    return _decode_data(data, _headers(part).get("content-type", ""))


def _walk_parts(
    service: Any,
    message_id: str,
    part: dict[str, Any],
    plain: list[str],
    html: list[str],
    attachments: list[dict[str, object]],
) -> None:
    mime_type = str(part.get("mimeType", ""))
    filename = str(part.get("filename", ""))
    body = part.get("body", {})
    if filename:
        attachments.append({
            "filename": _sanitize_text(filename),
            "mime_type": mime_type,
            "size": int(body.get("size", 0) or 0),
        })
        return
    if mime_type == "text/plain":
        text = _body_data(service, message_id, part)
        if text:
            plain.append(text)
    elif mime_type == "text/html":
        text = _body_data(service, message_id, part)
        if text:
            html.append(text)
    for child in part.get("parts", []):
        _walk_parts(service, message_id, child, plain, html, attachments)


def read_message(service: Any, message_id: str) -> dict[str, object]:
    if not message_id.strip():
        raise RecordValidationError("Gmail message-id must not be empty")
    message = (
        service.users().messages().get(userId="me", id=message_id, format="full").execute()
    )
    payload = message.get("payload", {})
    plain: list[str] = []
    html: list[str] = []
    attachments: list[dict[str, object]] = []
    _walk_parts(service, message_id, payload, plain, html, attachments)
    if plain:
        body = "\n\n".join(item.strip() for item in plain if item.strip())
    else:
        extractor = _HTMLTextExtractor()
        extractor.feed("\n".join(html))
        body = extractor.text()
    body = _sanitize_text(body)
    body, truncated = _truncate(body)
    headers = _headers(payload)
    return {
        **_message_metadata(message),
        "to": headers.get("to", ""),
        "body": body,
        "truncated": truncated,
        "attachments": attachments,
    }
