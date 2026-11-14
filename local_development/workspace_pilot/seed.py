"""Operator-only installation of the versioned Alder Trust corpus."""

import argparse
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import format_datetime
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from tempfile import NamedTemporaryFile

from httpx2 import Client, HTTPError

from private_client_graph.application.discovery.google import item_id

CORPUS = Path(__file__).resolve().parents[2] / "tests/fixtures/alder-trust-v1"
MAIL = "https://gmail.googleapis.com/gmail/v1/users/me"
DRIVE = "https://www.googleapis.com/drive/v3/files"
LABEL = "PCG Alder Trust v1"
FOLDER = "application/vnd.google-apps.folder"


class PilotError(ValueError):
    """Safe, operator-facing diagnostic."""


def require(condition, message: str) -> None:
    if not condition:
        raise PilotError(message)


def save(path: Path, data: dict) -> None:
    with NamedTemporaryFile(dir=path.parent, mode="w", delete=False) as out:
        json.dump(data, out)
        out.flush()
        os.fsync(out.fileno())
    os.replace(out.name, path)


def get(http, url, **params):
    return http.get(url, params=params).raise_for_status().json()


def marker(key: str) -> str:
    return f"<pcg-alder-v1-{key}@example.invalid>"


def message_bytes(row, subject, account):
    message = EmailMessage()
    message["Message-ID"] = marker(row["id"])
    message["From"] = "corpus@example.invalid"
    message["To"] = account
    message["Subject"] = subject
    message["Date"] = format_datetime(datetime.fromtimestamp(int(row["internalDate"]) / 1000, timezone.utc))
    if row["threadId"] != row["id"]:
        message["References"] = message["In-Reply-To"] = marker(row["threadId"])
    message.set_payload(row["body"])
    message["Content-Type"] = 'text/plain; charset="utf-8"'
    return message.as_bytes(policy=policy.SMTP)


class Installation:
    def __init__(self, http, directory, identity):
        self.http = http
        self.path = directory / "manifest.json"
        self.state = (
            json.loads(self.path.read_text())
            if self.path.exists()
            else {
                "corpus": "alder-trust-v1",
                "sub": identity["sub"],
                "email": identity["email"],
                "ids": {},
            }
        )
        require(
            self.state["corpus"] == "alder-trust-v1"
            and self.state["sub"] == identity["sub"]
            and self.state["email"] == identity["email"],
            "Manifest account or corpus mismatch",
        )
        self.ids = self.state["ids"]
        self.created = 0

    def ensure(self, key, create, verify):
        if key not in self.ids:
            # A timed-out POST can succeed remotely. Journal intent before dispatch
            # and require operator reconciliation before another create attempt.
            require("pending" not in self.state, "Unresolved create in manifest; reconcile before retry")
            self.state["pending"] = key
            save(self.path, self.state)
            self.ids[key] = item_id(create())
            self.created += 1
            del self.state["pending"]
            save(self.path, self.state)
        verify(item_id(self.ids[key]))

    def label(self):
        def create():
            labels = get(self.http, MAIL + "/labels")["labels"]
            require(not any(row["name"] == LABEL for row in labels), "Existing label without manifest")
            return self.http.post(MAIL + "/labels", json={"name": LABEL}).raise_for_status().json()["id"]

        def verify(key):
            require(get(self.http, MAIL + "/labels/" + key)["name"] == LABEL, "Label drift")

        self.ensure("alder-label", create, verify)

    def message(self, row, messages):
        key, parent = row["id"], row["threadId"]
        subject = messages[parent]["subject"]
        labels = [self.ids.get(label, label) for label in row["labelIds"]]
        raw = message_bytes(row, subject, self.state["email"])
        parent_thread = None
        if parent != key:
            parent_thread = get(self.http, MAIL + "/messages/" + self.ids[parent], fields="threadId")[
                "threadId"
            ]

        def create():
            prior = get(
                self.http, MAIL + "/messages", q="rfc822msgid:" + marker(key)[1:-1], includeSpamTrash="true"
            )
            require(not prior.get("messages"), "Existing message without manifest")
            data = {"raw": urlsafe_b64encode(raw).decode(), "labelIds": labels}
            if parent_thread:
                data["threadId"] = parent_thread
            return (
                self.http.post(MAIL + "/messages", params={"internalDateSource": "dateHeader"}, json=data)
                .raise_for_status()
                .json()["id"]
            )

        def verify(google_id):
            msg = get(self.http, MAIL + "/messages/" + google_id, format="raw")
            parsed = BytesParser(policy=policy.default).parsebytes(urlsafe_b64decode(msg["raw"]))
            require(
                parsed["Message-ID"] == marker(key)
                and parsed["Subject"] == subject
                and parsed.get_payload(decode=True) == row["body"].encode()
                and str(msg["internalDate"]) == row["internalDate"]
                and not {"TRASH", "SPAM"}.intersection(msg.get("labelIds", []))
                and set(labels) <= set(msg.get("labelIds", []))
                and (self.ids["alder-label"] in msg.get("labelIds", [])) == ("alder-label" in row["labelIds"])
                and (not parent_thread or msg["threadId"] == parent_thread),
                "Message content, date, scope or thread drift",
            )

        self.ensure(key, create, verify)

    def file(self, key, name, mime, *, parent=None, pdf=None, target=None):
        tag = "alder-v1-" + key
        metadata = {"name": name, "mimeType": mime, "appProperties": {"pcgSeed": tag}}
        if parent:
            metadata["parents"] = [parent]
        if target:
            metadata["shortcutDetails"] = {"targetId": target}

        def create():
            prior = get(
                self.http,
                DRIVE,
                q=f"appProperties has {{ key='pcgSeed' and value='{tag}' }}",
                fields="nextPageToken,files(id)",
            )
            require(
                not prior.get("files") and not prior.get("nextPageToken"),
                "Existing Drive key without manifest",
            )
            if pdf is None:
                response = self.http.post(DRIVE, json=metadata)
            else:
                boundary = b"pcg-alder-v1-upload"
                body = b"\r\n".join(
                    [
                        b"--" + boundary,
                        b"Content-Type: application/json; charset=UTF-8",
                        b"",
                        json.dumps(metadata).encode(),
                        b"--" + boundary,
                        b"Content-Type: application/pdf",
                        b"",
                        pdf,
                        b"--" + boundary + b"--",
                        b"",
                    ]
                )
                response = self.http.post(
                    "https://www.googleapis.com/upload/drive/v3/files",
                    params={"uploadType": "multipart"},
                    content=body,
                    headers={"Content-Type": "multipart/related; boundary=" + boundary.decode()},
                )
            return response.raise_for_status().json()["id"]

        def verify(google_id):
            obj = get(
                self.http,
                DRIVE + "/" + google_id,
                fields="name,mimeType,parents,trashed,appProperties,shortcutDetails,sha256Checksum,shared",
            )
            require(
                not obj["trashed"]
                and obj.get("shared") is False
                and obj["name"] == name
                and obj["mimeType"] == mime
                and obj["appProperties"]["pcgSeed"] == tag
                and (not parent or obj["parents"] == [parent])
                and (not target or obj["shortcutDetails"]["targetId"] == target)
                and (pdf is None or obj.get("sha256Checksum") == sha256(pdf).hexdigest()),
                "Drive object drift",
            )

        self.ensure(key, create, verify)


def seed(http, directory, account):
    identity = get(http, "https://openidconnect.googleapis.com/v1/userinfo")
    require(
        identity.get("email_verified") is True
        and identity["email"] == account
        and account.endswith("@gmail.com")
        and identity.get("sub"),
        "Unexpected synthetic account",
    )
    corpus = json.loads((CORPUS / "corpus.json").read_text())
    pdf = (CORPUS / corpus["appointment_media"]["path"]).read_bytes()
    require(sha256(pdf).hexdigest() == corpus["appointment_media"]["sha256"], "Local PDF drift")
    with (directory / ".seed.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        install = Installation(http, directory, identity)
        install.label()
        for key, title in (("folder-1", LABEL), ("folder-2", "PCG out-of-scope v1")):
            install.file(key, title, FOLDER)
        messages = {row["id"]: row for row in corpus["messages"]}
        for row in messages.values():
            install.message(row, messages)
        for row in corpus["files"]:
            target = row.get("shortcutDetails", {}).get("targetId")
            install.file(
                row["id"],
                row["name"],
                row["mimeType"],
                parent=install.ids[row["parents"][0]],
                pdf=pdf if row["mimeType"] == "application/pdf" else None,
                target=install.ids[target] if target else None,
            )
        print(f"Alder Trust v1 verified: {len(install.ids)} objects, {install.created} created this run.")
        return install.state


def operator_token(directory):
    env = dict(os.environ, CLOUDSDK_CONFIG=str(directory / "gcloud"))
    env.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    require(
        (directory / "gcloud/application_default_credentials.json").is_file(),
        "Missing isolated operator credentials",
    )
    return subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        capture_output=True,
        check=True,
        env=env,
        text=True,
    ).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("account", help="Dedicated synthetic Gmail address")
    args = parser.parse_args()
    os.umask(0o077)
    directory = args.directory.resolve()
    require(directory.is_dir() and directory.stat().st_mode & 0o077 == 0, "Use a private 0700 directory")
    require(not directory.is_relative_to(CORPUS.parents[2]), "Keep the manifest outside the repository")
    token = operator_token(directory)
    with Client(headers={"Authorization": "Bearer " + token}, trust_env=False) as http:
        seed(http, directory, args.account)


if __name__ == "__main__":
    try:
        main()
    except PilotError as exc:
        raise SystemExit(str(exc)) from None
    except (HTTPError, OSError, ValueError, KeyError, subprocess.SubprocessError):
        raise SystemExit(
            "Seed stopped. Check the isolated credentials and private manifest before retrying."
        ) from None
