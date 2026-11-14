"""Google request construction and admission checks for private discovery."""
import base64
import binascii
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from email.message import Message
from hashlib import sha256
from urllib.parse import quote

from httpx2 import Client, HTTPError

from ..pdf_acquisition import extract_pdf_source
from .limits import Action


class ReadFailure(ValueError):
    """Safe error for a failed provider read."""


class OutsideScope(ValueError):
    """Provider metadata no longer admits this item."""


def literal(value: str) -> str:
    # Restricted V1 phrase grammar prevents Google query syntax from entering either request.
    value = value.strip()
    if not 1 <= len(value) <= 160 or not all(c.isalnum() or c in " '-’" for c in value):
        raise ValueError("Enter a name or literal search phrase")
    return value


def _day_start(day: date) -> int:
    return int(datetime.combine(day, time.min, timezone.utc).timestamp())


@dataclass(frozen=True)
class WorkspaceScope:
    """Caller supplies the permitted synthetic account and locations. Dates are inclusive UTC days."""
    mailbox: str
    label: str
    folder: str
    first_day: date | None = None
    last_day: date | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[^/@\s]+@[^/@\s]+", self.mailbox):
            raise ValueError("Expected an explicit mailbox")
        if not self.label or not re.fullmatch(r"[\w-]+", self.folder):
            raise ValueError("Expected fixed label and folder IDs")
        if self.first_day and self.last_day and self.first_day > self.last_day:
            raise ValueError("Invalid Gmail date range")

    def gmail_query(self, phrase: str) -> str:
        # Widen the provider's lower bound by a second; enforce the exact half-open range on metadata.
        if self.first_day:
            phrase += f" after:{_day_start(self.first_day) - 1}"
        if self.last_day:
            phrase += f" before:{_day_start(self.last_day) + 86400}"
        return phrase

    def admits_message(self, item: dict, key: str) -> bool:
        stamp = int(item["internalDate"])
        return (item.get("id") == key and self.label in item["labelIds"]
                and (not self.first_day or stamp >= _day_start(self.first_day) * 1000)
                and (not self.last_day or stamp < (_day_start(self.last_day) + 86400) * 1000))


@dataclass(frozen=True)
class DriveFile:
    id: str
    title: str
    version: str


@dataclass(frozen=True)
class PdfPreview:
    file: DriveFile
    sha256: str
    text: str


FILE_FIELDS = "id,name,mimeType,parents,trashed,version"


def _key(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", value):
        raise ReadFailure("Invalid item identity")
    return value


class WorkspaceReader:
    def __init__(self, http: Client, scope: WorkspaceScope):
        self.http = http
        self.scope = scope
        self.messages = f"https://gmail.googleapis.com/gmail/v1/users/{quote(scope.mailbox, safe='@')}/messages"
        self.files = "https://www.googleapis.com/drive/v3/files"

    def read(self, url: str, params: dict[str, str], action: Action) -> bytes:
        action.request()
        try:
            with self.http.stream("GET", url, params=params, headers={"Accept-Encoding": "identity"},
                                  follow_redirects=False) as response:
                response.raise_for_status()
                data = bytearray()
                for chunk in response.iter_bytes(8192):
                    action.consume(len(chunk))
                    data.extend(chunk)
                return bytes(data)
        except HTTPError:
            raise ReadFailure("Workspace read failed") from None

    def _json(self, url: str, params: dict[str, str], action: Action) -> dict:
        raw = self.read(url, params, action)
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeError):
            raise ReadFailure("Invalid Workspace response") from None
        if not isinstance(value, dict):
            raise ReadFailure("Invalid Workspace response")
        return value

    def mail_page(self, terms: str, token: str, action: Action) -> dict:
        params = {"q": self.scope.gmail_query(f'"{literal(terms)}"'), "labelIds": self.scope.label,
                  "fields": "nextPageToken,messages(id)", "maxResults": "100"}
        if token:
            params["pageToken"] = token
        return self._json(self.messages, params, action)

    def drive_page(self, terms: str, token: str, action: Action) -> dict:
        phrase = literal(terms).replace("'", "\\'")
        query = (f"'{self.scope.folder}' in parents and trashed = false and mimeType = 'application/pdf' "
                 f"and fullText contains '\"{phrase}\"'")
        params = {"q": query, "fields": f"nextPageToken,files({FILE_FIELDS})", "pageSize": "100"}
        if token:
            params["pageToken"] = token
        return self._json(self.files, params, action)

    def admitted_file(self, row: dict) -> DriveFile:
        if (row.get("parents") != [self.scope.folder] or row.get("trashed") is not False
                or row.get("mimeType") != "application/pdf"):
            raise OutsideScope()
        return DriveFile(_key(row["id"]), row["name"], row["version"])

    def preview_pdf(self, candidate: DriveFile, action: Action) -> PdfPreview:
        url = f"{self.files}/{_key(candidate.id)}"
        def current() -> DriveFile:
            return self.admitted_file(self._json(url, {"fields": FILE_FIELDS}, action))

        if current() != candidate:
            raise OutsideScope("File changed since discovery")
        media = self.read(url, {"alt": "media"}, action)
        if current() != candidate:
            raise OutsideScope("File changed during download")
        return PdfPreview(candidate, sha256(media).hexdigest(), extract_pdf_source(media))

    def message_text(self, key: str, action: Action) -> str:
        url = f"{self.messages}/{_key(key)}"
        fields = "id,labelIds,internalDate"
        metadata = self._json(url, {"format": "metadata", "fields": fields}, action)
        if not self.scope.admits_message(metadata, key):
            raise OutsideScope()
        full = self._json(url, {"format": "full", "fields": fields + ",payload"}, action)
        if not self.scope.admits_message(full, key):
            raise OutsideScope()
        return _plain_body(full["payload"])


def _plain_body(part: dict) -> str:
    """Read the first inline text/plain MIME body; attachments are outside V1."""
    mime = str(part.get("mimeType", "")).lower()
    if part.get("filename"):
        raise ReadFailure("Attachment excluded")
    if mime.startswith("multipart/"):
        for child in part.get("parts", []):
            try:
                return _plain_body(child)
            except ReadFailure:
                continue
        raise ReadFailure("No supported message body")
    if mime != "text/plain":
        raise ReadFailure("No supported message body")
    headers = Message()
    for header in part.get("headers", []):
        if header["name"].lower() in {"content-type", "content-disposition"}:
            headers[header["name"]] = header["value"]
    if headers.get_content_disposition() == "attachment":
        raise ReadFailure("Attachment excluded")
    try:
        data = part["body"]["data"]
        raw = base64.b64decode(data + "=" * (-len(data) % 4), altchars=b"-_", validate=True)
        return raw.decode(headers.get_content_charset() or "utf-8")
    except (KeyError, UnicodeError, LookupError, binascii.Error):
        raise ReadFailure("Unreadable message body") from None
