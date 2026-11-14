"""Session-bound online access for one explicitly configured synthetic Google corpus."""

from dataclasses import dataclass, field
import os
from secrets import compare_digest, token_urlsafe
from threading import RLock, Timer
from time import time

from authlib.integrations.starlette_client import OAuth  # type: ignore[import-untyped]
from fastapi import APIRouter, Request
from httpx2 import Client, Request as GoogleRequest, Response as GoogleResponse
from starlette.responses import RedirectResponse

from private_client_graph.application.discovery.collection import CollectionReview
from private_client_graph.application.discovery.google import WorkspaceScope, item_id
from private_client_graph.application.proposal_errors import ProposalFailure
from .auth import AuthConfig, allowed_subjects

CALLBACK = "/auth/workspace/callback"
RETURN = "/app/matter-proposals/new?workspace="
SCOPES = {
    "openid",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
}


@dataclass(frozen=True, repr=False)
class PilotConfig:
    client_id: str
    secret: str
    subject: str
    scope: WorkspaceScope
    folder_name: str
    label_name: str
    message_ids: frozenset[str]
    file_ids: frozenset[str]

    @classmethod
    def load(cls, auth: AuthConfig | None) -> "PilotConfig | None":
        if os.getenv("PCG_WORKSPACE_ENABLED") != "true":
            return None

        def required(name: str) -> str:
            value = os.getenv("PCG_WORKSPACE_" + name, "").strip()
            if not value:
                raise ValueError("Missing Workspace configuration: " + name)
            return value

        client = required("CLIENT_ID")
        if auth is None or client == auth.client_id or not client.endswith(".apps.googleusercontent.com"):
            raise ValueError("Configure a separate Workspace OAuth client and PCG sign-in")
        scope = WorkspaceScope(required("MAILBOX"), required("LABEL"), required("FOLDER"))
        return cls(
            client,
            required("CLIENT_SECRET"),
            required("SUBJECT"),
            scope,
            required("FOLDER_NAME"),
            required("LABEL_NAME"),
            frozenset(item_id(i.strip()) for i in required("MESSAGE_IDS").split(",")),
            frozenset(item_id(i.strip()) for i in required("FILE_IDS").split(",")),
        )


def reconnect() -> ProposalFailure:
    return ProposalFailure(
        "workspace_reconnect", "Reconnect Google Workspace and start a fresh search.", status_code=409
    )


@dataclass(eq=False, repr=False)
class Connection:
    deadline: float
    timer: Timer | None = None
    pending: dict = field(default_factory=dict)
    http: Client | None = None
    token: str = ""
    journey: tuple[str, CollectionReview] | None = None
    generation: str = field(default_factory=token_urlsafe)


class Pilot:
    """A fresh grant retires the previous client and discovery handles."""

    def __init__(self, config: PilotConfig, origin: str):
        self.config = config
        self.redirect = origin + CALLBACK
        self.oauth = OAuth().register(
            "workspace",
            client_id=config.client_id,
            client_secret=config.secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": " ".join(sorted(SCOPES)), "code_challenge_method": "S256"},
        )
        self.entries: dict[str, Connection] = {}
        self.logins: dict[str, float] = {}
        self.lock = RLock()
        self.transport = None  # Private Google HTTP seam for credential-free integration tests.

    def login(self, expires: float) -> str:
        with self.lock:
            self.logins = {k: v for k, v in self.logins.items() if v > time()}
            key = token_urlsafe()
            self.logins[key] = expires
            return key

    def logout(self, key: str) -> None:
        with self.lock:
            self.logins.pop(key, None)
            self.retire(key)

    def require_login(self, request: Request) -> str:
        key = request.session.get("workspace_login", "")
        with self.lock:
            if self.logins.get(key, 0) <= time():
                raise ProposalFailure("sign_in_required", "Sign in again.", status_code=401)
        return key

    def retire(self, key: str, expected: Connection | None = None) -> None:
        with self.lock:
            entry = self.entries.get(key)
            if entry is None or (expected is not None and entry is not expected):
                return
            del self.entries[key]
            entry.journey = None
            entry.token = ""
            entry.pending.clear()
            if entry.timer:
                entry.timer.cancel()
            if entry.http:
                entry.http.close()

    def _expire(self, key: str, entry: Connection, deadline: float) -> None:
        if entry.timer:
            entry.timer.cancel()
        entry.deadline = deadline

        def expire_current() -> None:
            with self.lock:
                if entry.deadline == deadline:
                    self.retire(key, entry)

        entry.timer = Timer(max(0, deadline - time()), expire_current)
        entry.timer.daemon = True
        entry.timer.start()

    def connected(self, request: Request) -> Connection:
        key = self.require_login(request)
        with self.lock:
            entry = self.entries.get(key)
            if entry and entry.deadline <= time():
                self.retire(key, entry)
                raise reconnect()
            if not entry or not entry.http:
                raise reconnect()
            return entry

    async def begin(self, request: Request) -> dict:
        with self.lock:
            key = self.require_login(request)
            self.retire(key)
            entry = Connection(time())
            self.entries[key] = entry
            self._expire(key, entry, min(time() + 300, request.session["expires"]))
        try:
            data = await self.oauth.create_authorization_url(
                self.redirect, access_type="online", prompt="select_account consent"
            )
        except Exception:
            self.retire(key, entry)
            raise ProposalFailure(
                "workspace_unavailable", "Workspace connection unavailable.", status_code=503
            ) from None
        with self.lock:
            if self.entries.get(key) is not entry:
                raise reconnect()
            entry.pending = data
            return {"url": data["url"]}

    async def callback(self, request: Request) -> RedirectResponse:
        key = self.require_login(request)
        params = request.query_params
        with self.lock:
            entry = self.entries.get(key)
            if (
                not entry
                or not entry.pending
                or not compare_digest(entry.pending["state"].encode(), params.get("state", "").encode())
            ):
                return RedirectResponse(RETURN + "invalid", 303)
            transaction, entry.pending = entry.pending, {}
        reason = "cancelled" if params.get("error") == "access_denied" else "invalid"
        if "code" in params and "error" not in params:
            try:
                token = await self.oauth.fetch_access_token(
                    redirect_uri=self.redirect,
                    code=params["code"],
                    code_verifier=transaction["code_verifier"],
                    grant_type="authorization_code",
                )
                claims = await self.oauth.parse_id_token(token, nonce=transaction["nonce"], leeway=0)
                if claims.get("aud") != self.config.client_id or claims.get("nonce") != transaction["nonce"]:
                    raise ValueError("Invalid nonce")
                if claims["sub"] != self.config.subject:
                    reason = "account"
                elif set(token.get("scope", "").split()) != SCOPES:
                    reason = "permissions"
                elif request.session["sub"] in allowed_subjects():
                    self._activate(key, entry, token, request.session["expires"])
                    return RedirectResponse(RETURN + "ready", 303)
            except Exception:
                reason = "invalid"
        self.retire(key, entry)
        return RedirectResponse(RETURN + reason, 303)

    def _activate(self, key: str, entry: Connection, token: dict, login_expiry: float) -> None:
        with self.lock:
            if self.entries.get(key) is not entry or entry.deadline <= time():
                raise reconnect()
            deadline = min(login_expiry, time() + min(int(token["expires_in"]), 3600))
            if (
                deadline <= time()
                or token.get("token_type", "").lower() != "bearer"
                or not token.get("access_token")
            ):
                raise ValueError("Invalid grant")

            def authorize(request: GoogleRequest) -> None:
                with self.lock:
                    if self.entries.get(key) is not entry or entry.deadline <= time():
                        raise reconnect()
                    request.headers["Authorization"] = "Bearer " + entry.token

            def check(response: GoogleResponse) -> None:
                if response.status_code == 401 or (
                    response.status_code == 403
                    and "insufficient_scope" in response.headers.get("www-authenticate", "")
                ):
                    self.retire(key, entry)
                    raise reconnect()

            entry.token = token["access_token"]
            entry.http = Client(
                transport=self.transport,
                trust_env=False,
                event_hooks={"request": [authorize], "response": [check]},
            )
            self._expire(key, entry, deadline)

    def router(self) -> APIRouter:
        router = APIRouter(include_in_schema=False)
        root = "/api/matter-proposals/discovery/"
        router.add_api_route(root + "connect", self.begin, methods=["POST"])
        router.add_api_route(CALLBACK, self.callback, methods=["GET"])

        @router.post(root + "connection")
        def status(request: Request) -> dict:
            try:
                entry = self.connected(request)
            except ProposalFailure as exc:
                if exc.error.code != "workspace_reconnect":
                    raise
                entry = None
            scope = self.config.scope
            return {
                "connected": bool(entry),
                "expires": entry.deadline if entry else None,
                "generation": entry.generation if entry else None,
                "account": scope.mailbox,
                "label": scope.label,
                "folder": scope.folder,
                "label_name": self.config.label_name,
                "folder_name": self.config.folder_name,
            }

        @router.post(root + "disconnect")
        def disconnect(request: Request) -> dict:
            self.retire(self.require_login(request))
            return {"connected": False}

        return router
