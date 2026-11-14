"""Literal Google HTTP exchanges. No query evaluation, access policy or ranking."""
import base64
import json
from pathlib import Path

from httpx2 import Client, MockTransport, Response

ROOT = Path(__file__).parents[1] / "fixtures" / "alder-trust-v1"
CORPUS = json.loads((ROOT / "corpus.json").read_text())
MAIL = "/gmail/v1/users/synthetic@example.test/messages"
FILES = "/drive/v3/files"


class Exchanges:
    def __init__(self):
        self.steps = []
        self.http = Client(transport=MockTransport(self.respond))

    def expect(self, path, params, payload, status=200):
        self.steps.append((path, params, payload, status))

    def respond(self, request):
        path, params, payload, status = self.steps.pop(0)
        assert request.method == "GET"
        assert request.url.path == path
        for key, value in params.items():
            assert request.url.params.get(key) == value
        if isinstance(payload, bytes):
            return Response(status, content=payload)
        return Response(status, json=payload)

    def list_mail(self, terms, ids, *, token=None, next_token=None, dates=""):
        self.expect(MAIL, {"labelIds": "alder-label", "q": f'"{terms}"{dates}', "pageToken": token},
                    {"messages": [{"id": i} for i in ids], "nextPageToken": next_token})

    def list_files(self, terms, ids, *, token=None, next_token=None):
        query = ("'folder-1' in parents and trashed = false and mimeType = 'application/pdf' "
                 f"and fullText contains '\"{terms}\"'")
        self.expect(FILES, {"q": query, "pageToken": token},
                    {"files": [file(i) for i in ids], "nextPageToken": next_token})

    def message(self, id, fmt, *, body=None, labels=None):
        record = next(m for m in CORPUS["messages"] if m["id"] == id)
        payload = {"mimeType": "text/plain", "headers": [{"name": "Subject", "value": record["subject"]}]}
        if fmt == "full":
            data = (body if body is not None else record["body"]).encode()
            payload["body"] = {"data": base64.urlsafe_b64encode(data).decode(), "size": len(data)}
        response = {k: record[k] for k in ("id", "threadId", "internalDate", "labelIds")}
        if labels is not None:
            response["labelIds"] = labels
        self.expect(f"{MAIL}/{id}", {"format": fmt}, {**response, "payload": payload})


def file(id):
    return next(f for f in CORPUS["files"] if f["id"] == id)
