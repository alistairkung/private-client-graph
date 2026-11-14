"""Private localhost-only synthetic pilot with Google's real authorization endpoints."""

import argparse
import json
import logging
import os
from pathlib import Path
from secrets import token_urlsafe

from local_development.https import serve_https
from local_development.server import _local_extraction, _local_source_extraction
from private_client_graph.api.app import create_app
from private_client_graph.application import matter_proposals
from private_client_graph.application.discovery.google import item_id
from .seed import CORPUS, LABEL, require

ORIGIN = "https://localhost:8444"


def configure(directory: Path):
    manifest = json.loads((directory / "manifest.json").read_text())
    require(manifest["corpus"] == "alder-trust-v1" and "pending" not in manifest, "Incomplete seed")
    ids = manifest["ids"]
    corpus = json.loads((CORPUS / "corpus.json").read_text())
    messages = [item_id(ids[m["id"]]) for m in corpus["messages"] if "alder-label" in m["labelIds"]]
    files = [
        item_id(ids[f["id"]])
        for f in corpus["files"]
        if f["parents"] == ["folder-1"] and f["mimeType"] == "application/pdf"
    ]
    settings = {
        "PCG_GOOGLE_SUB_ALLOWLIST": manifest["sub"],
        "PCG_SESSION_SECRET": token_urlsafe(48),
        "PCG_TRUSTED_ORIGIN": ORIGIN,
        "PCG_SESSION_SECONDS": "1800",
        "PCG_WORKSPACE_ENABLED": "true",
        "PCG_WORKSPACE_SUBJECT": manifest["sub"],
        "PCG_WORKSPACE_MAILBOX": manifest["email"],
        "PCG_WORKSPACE_LABEL": item_id(ids["alder-label"]),
        "PCG_WORKSPACE_FOLDER": item_id(ids["folder-1"]),
        "PCG_WORKSPACE_LABEL_NAME": LABEL,
        "PCG_WORKSPACE_FOLDER_NAME": LABEL,
        "PCG_WORKSPACE_MESSAGE_IDS": ",".join(messages),
        "PCG_WORKSPACE_FILE_IDS": ",".join(files),
    }
    for name, prefix, callback in (
        ("signin", "PCG_GOOGLE", "/auth/callback"),
        ("discovery", "PCG_WORKSPACE", "/auth/workspace/callback"),
    ):
        web = json.loads((directory / (name + ".json")).read_text())["web"]
        require(ORIGIN + callback in web["redirect_uris"], "Missing pilot redirect URI")
        settings[prefix + "_CLIENT_ID"] = web["client_id"]
        settings[prefix + "_CLIENT_SECRET"] = web["client_secret"]
    return settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    require(
        os.environ.get("DATABASE_URL") == "postgresql:///pcg_workspace_pilot"
        and os.environ.get("PGHOST") == str(args.directory.resolve() / "socket")
        and os.environ.get("PGPORT") == "55481"
        and not os.getenv("PGHOSTADDR")
        and not os.getenv("PGSERVICE"),
        "Use the dedicated private pilot database socket",
    )
    os.environ.update(configure(args.directory))
    logging.disable(logging.INFO)
    matter_proposals._extract_proposal = _local_extraction
    matter_proposals._extract_proposal_sources = _local_source_extraction
    serve_https(create_app(), host="127.0.0.1", port=8444)


if __name__ == "__main__":
    main()
