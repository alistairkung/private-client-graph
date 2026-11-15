# /// script
# dependencies = ["google-auth-oauthlib==1.5.0"]
# ///
"""Obtain an operator grant for the private seed and verification commands."""

import argparse
import json
import logging
import os
from pathlib import Path

SCOPES = (
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.insert",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/drive.file",
)


def authorize(directory, account, load_flow):
    credentials = directory / "gcloud/application_default_credentials.json"
    if credentials.exists():
        raise SystemExit("An isolated operator grant already exists.")
    if not credentials.parent.is_dir() or credentials.parent.stat().st_mode & 0o077:
        raise SystemExit("Create the private 0700 gcloud directory first.")
    flow = load_flow(directory / "operator.json", SCOPES, autogenerate_code_verifier=True)
    grant = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        timeout_seconds=600,
        authorization_prompt_message="",
        prompt="consent",
        login_hint=account,
    )
    if not grant.refresh_token:
        raise SystemExit("Google did not return an operator refresh grant.")
    with open(credentials, "x", opener=lambda path, flags: os.open(path, flags, 0o600)) as out:
        json.dump(
            {
                "type": "authorized_user",
                "client_id": grant.client_id,
                "client_secret": grant.client_secret,
                "refresh_token": grant.refresh_token,
            },
            out,
        )


def main():
    from google_auth_oauthlib.flow import InstalledAppFlow

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("account", help="Dedicated synthetic Gmail address")
    args = parser.parse_args()
    os.umask(0o077)
    # The loopback callback URL and token exchange must stay out of logs.
    logging.disable(logging.CRITICAL)
    authorize(args.directory, args.account, InstalledAppFlow.from_client_secrets_file)
    print("Isolated operator grant saved.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"Operator authorization stopped ({type(exc).__name__}).") from None
