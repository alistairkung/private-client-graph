"""Read-only provider contract checks. Output contains only the check name and result."""

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from httpx2 import Client, HTTPError

from private_client_graph.application.discovery.google import WorkspaceReader, WorkspaceScope, item_id
from private_client_graph.application.discovery.limits import Action, Limits, Usage
from .seed import CORPUS, DRIVE, MAIL, PilotError, get, operator_token, require


def page_ids(http, url, collection, **params):
    ids = set()
    for _ in range(24):
        page = get(http, url, **params)
        rows = page.get(collection, [])
        for row in rows:
            key = item_id(row["id"])
            require(key not in ids, "Duplicate result during pagination")
            ids.add(key)
        if not page.get("nextPageToken"):
            return ids
        params["pageToken"] = page["nextPageToken"]
    raise PilotError("Pagination exceeded the pilot budget")


def check(http, directory, account):
    manifest = json.loads((directory / "manifest.json").read_text())
    user = get(http, "https://openidconnect.googleapis.com/v1/userinfo")
    require(
        user.get("email_verified") is True
        and user["sub"] == manifest["sub"]
        and user["email"] == account == manifest["email"],
        "Unexpected synthetic account",
    )
    ids = manifest["ids"]
    scope = WorkspaceScope(account, ids["alder-label"], ids["folder-1"])
    expected = {ids[f"{i:02d}"] for i in range(1, 7)}
    params = dict(q='"Alder Trust"', maxResults="2", fields="messages(id),nextPageToken")
    outside = page_ids(http, MAIL + "/messages", "messages", **params)
    require(ids["07"] in outside, "Unlabelled sibling positive control missing")
    inside = page_ids(http, MAIL + "/messages", "messages", labelIds=scope.label, **params)
    require(inside == expected, "Scoped Gmail pagination or sibling exclusion failed")
    print("PASS Gmail pagination and message-label isolation")
    for day, expected_hits in ((5, expected), (6, set())):
        bounded = WorkspaceScope(account, scope.label, scope.folder, date(2026, 1, day), date(2026, 1, day))
        params["q"] = bounded.gmail_query('"Alder Trust"')
        require(
            page_ids(http, MAIL + "/messages", "messages", labelIds=scope.label, **params) == expected_hits,
            "Gmail date bounds differ",
        )
    print("PASS Gmail UTC date bounds")
    query = """trashed = false and mimeType = 'application/pdf' and fullText contains '"Mara Voss"'"""
    drive = dict(q=query, pageSize="1", fields="files(id),nextPageToken")
    both = page_ids(http, DRIVE, "files", **drive)
    require({ids["other"], ids["appointment"]} <= both, "Drive positive controls missing")
    drive["q"] = f"'{scope.folder}' in parents and " + query
    require(page_ids(http, DRIVE, "files", **drive) == {ids["appointment"]}, "Drive parent exclusion failed")
    print("PASS Drive direct-parent isolation")
    action = Action(Limits(), Usage())
    reader = WorkspaceReader(http, scope, file_ids=frozenset({ids["appointment"]}))
    page = reader.drive_page("Mara Voss", "", action)
    require(len(page.get("files", [])) == 1, "Unexpected acquisition candidate count")
    candidate = reader.admitted_file(page["files"][0])
    pdf = reader.preview_pdf(candidate, action)
    fixture = json.loads((CORPUS / "corpus.json").read_text())["appointment_media"]
    require(
        pdf.sha256 == fixture["sha256"] == sha256((CORPUS / fixture["path"]).read_bytes()).hexdigest(),
        "Acquisition digest mismatch",
    )
    print("PASS original PDF bytes through PCG acquisition")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("account")
    args = parser.parse_args()
    try:
        with Client(
            headers={"Authorization": "Bearer " + operator_token(args.directory)}, trust_env=False
        ) as client:
            check(client, args.directory, args.account)
    except PilotError as exc:
        raise SystemExit(str(exc)) from None
    except (HTTPError, OSError, ValueError, KeyError, RuntimeError):
        raise SystemExit(
            "Provider checks incomplete. Verify pilot configuration, access and indexing."
        ) from None
