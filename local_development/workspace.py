"""Literal offline Google responses for the versioned Alder Trust practitioner journey."""
import base64
import json
import logging
from email.utils import formatdate
from pathlib import Path

from httpx2 import Client, MockTransport, Request, Response, URL

ROOT = Path(__file__).resolve().parents[1] / "tests/fixtures/alder-trust-v1"
MAIL = "/gmail/v1/users/synthetic@example.test/messages"
FILES = "/drive/v3/files"


def message_response(record: dict, fmt: str) -> dict:
    payload = {"mimeType": "text/plain", "headers": [{"name": "Subject", "value": record["subject"]}]}
    if fmt == "full":
        payload["headers"].extend([
            {"name": "From", "value": "corpus@example.invalid"},
            {"name": "To", "value": "synthetic@example.test"},
            {"name": "Date", "value": formatdate(int(record["internalDate"]) / 1000, usegmt=True)},
        ])
        data = record["body"].encode()
        payload["body"] = {"data": base64.urlsafe_b64encode(data).decode(), "size": len(data)}
    return {key: record[key] for key in ("id", "threadId", "internalDate", "labelIds")} | {"payload": payload}


class _PrivateWorkspaceRequests(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # httpx2's INFO request record contains the complete URL including search terms.
        return not (isinstance(record.args, tuple) and any(
            isinstance(arg, URL) and arg.host in {"gmail.googleapis.com", "www.googleapis.com"}
            for arg in record.args))


def fixture_client() -> Client:
    logging.getLogger("httpx2").addFilter(_private_filter)
    corpus = json.loads((ROOT / "corpus.json").read_text())
    messages = {row["id"]: row for row in corpus["messages"]}
    files = {row["id"]: row for row in corpus["files"]}
    media = (ROOT / corpus["appointment_media"]["path"]).read_bytes()

    def respond(request: Request) -> Response:
        path, params = request.url.path, request.url.params
        if request.method != "GET":
            return Response(405)
        if path == MAIL and params.get("labelIds") == "alder-label":
            # The application checks inclusive UTC bounds on each message's metadata.
            phrase = params["q"].split('"')[1]
            ids, next_page = MAIL_PAGES.get((phrase, params.get("pageToken")), ([], None))
            return Response(200, json={"messages": [{"id": key} for key in ids], "nextPageToken": next_page})
        if path.startswith(MAIL + "/") and (row := messages.get(path.rsplit("/", 1)[1])):
            return Response(200, json=message_response(row, params["format"]))
        if path == FILES:
            ids, next_page = DRIVE_PAGES.get((params["q"], params.get("pageToken")), ([], None))
            return Response(200, json={"files": [files[key] for key in ids], "nextPageToken": next_page})
        if path.startswith(FILES + "/") and (row := files.get(path.rsplit("/", 1)[1])):
            if params.get("alt") == "media":
                return Response(200, content=media)
            return Response(200, json=row)
        return Response(404)

    return Client(transport=MockTransport(respond))


_private_filter = _PrivateWorkspaceRequests()
MAIL_PAGES = {
    ("Alder Trust", None): (["05", "03", "04", "02", "01"], "mail-p2"),
    ("Alder Trust", "mail-p2"): (["07", "06"], None),
    ("Alice Reed", None): (["08"], None),
    ("Ben Wong", None): (["09"], None),
}
_DRIVE_SCOPE = "'folder-1' in parents and trashed = false and mimeType = 'application/pdf' and fullText contains "
DRIVE_PAGES = {
    (_DRIVE_SCOPE + """'"Alder Trust"'""", None): (["deed", "shortcut", "other"], "drive-p2"),
    (_DRIVE_SCOPE + """'"Alder Trust"'""", "drive-p2"): (["minutes"], None),
    (_DRIVE_SCOPE + """'"Mara Voss"'""", None): (["appointment", "other"], None),
}
