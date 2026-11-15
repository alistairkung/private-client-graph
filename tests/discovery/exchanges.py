"""Literal Google HTTP exchanges. No query evaluation, access policy or ranking."""
import json
from local_development.workspace import FILES, MAIL, ROOT, message_response

from httpx2 import Client, MockTransport, Response

CORPUS = json.loads((ROOT / "corpus.json").read_text())


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

    def list_files(self, terms, ids, *, token=None, next_token=None, records=None):
        query = ("'folder-1' in parents and trashed = false and mimeType = 'application/pdf' "
                 f"and fullText contains '\"{terms}\"'")
        self.expect(FILES, {"q": query, "pageToken": token},
                    {"files": [file(i) for i in ids] if records is None else records, "nextPageToken": next_token})

    def message(self, id, fmt, *, body=None, labels=None):
        record = next(m for m in CORPUS["messages"] if m["id"] == id)
        row = {**record, "body": record["body"] if body is None else body,
               "labelIds": record["labelIds"] if labels is None else labels}
        self.expect(f"{MAIL}/{id}", {"format": fmt}, message_response(row, fmt))


def file(id):
    return next(f for f in CORPUS["files"] if f["id"] == id)
