"""Google-only identity and stateless, short-lived prototype authorization."""

import os
import re
import time
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit

from authlib.integrations.starlette_client import OAuth  # type: ignore[import-untyped]
from authlib.common.errors import AuthlibBaseError  # type: ignore[import-untyped]
from joserfc.errors import JoseError
from httpx2 import HTTPError
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import Receive, Scope, Send
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette_csrf import CSRFMiddleware

SESSION_COOKIE = "__Host-pcg-session"
CSRF_COOKIE = "__Host-pcg-csrf"
PRIVATE_PATH_PATTERN = r"(?:/app(?:/|$)|/api/matters|/api/matter-proposals)"


def allowed_subjects() -> set[str]:
    subjects = os.environ.get("PCG_GOOGLE_SUB_ALLOWLIST", "").split(",")
    if any(not subject.strip() or re.search(r"\s", subject.strip()) for subject in subjects):
        raise ValueError("PCG_GOOGLE_SUB_ALLOWLIST must contain Google subjects")
    return {subject.strip() for subject in subjects}


@dataclass(frozen=True)
class AuthConfig:
    client_id: str
    client_secret: str
    session_secret: str
    origin: str
    session_seconds: int

    @classmethod
    def from_environment(cls) -> "AuthConfig":
        client_id = os.environ.get("PCG_GOOGLE_CLIENT_ID", "").strip()
        client_secret = os.environ.get("PCG_GOOGLE_CLIENT_SECRET", "").strip()
        secret = os.environ.get("PCG_SESSION_SECRET", "")
        origin = os.environ.get("PCG_TRUSTED_ORIGIN", "")
        url = urlsplit(origin)
        seconds = int(os.environ.get("PCG_SESSION_SECONDS", "1800"))
        if not client_id.endswith(".apps.googleusercontent.com") or not client_secret:
            raise ValueError("Google client configuration is required")
        if len(secret.strip()) < 32 or not 60 <= seconds <= 3600:
            raise ValueError("A strong session secret and lifetime of 60–3600 seconds are required")
        if (url.scheme != "https" or not url.hostname
                or not re.fullmatch(r"[a-z0-9.-]+", url.hostname)
                or url.username or url.password
                or url.path or url.query or url.fragment or url.netloc != url.hostname + (f":{url.port}" if url.port else "")):
            raise ValueError("PCG_TRUSTED_ORIGIN must be one HTTPS origin")
        allowed_subjects()
        return cls(client_id, client_secret, secret, origin, seconds)


def protected_path(path: str) -> bool:
    return re.match(PRIVATE_PATH_PATTERN, path) is not None


class PractitionerTrustedHost(TrustedHostMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Public routes, including platform readiness probes, keep their existing
        # host behavior. Trust the configured host only at the private boundary.
        path = scope.get("path", "")
        if protected_path(path) or path.startswith("/auth/"):
            await super().__call__(scope, receive, send)
        else:
            await self.app(scope, receive, send)


class PractitionerBoundary(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await self._dispatch(request, call_next)
        if protected_path(request.url.path) or request.url.path.startswith("/auth/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    async def _dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        private = protected_path(path)
        auth_route = path.startswith("/auth/")
        if not private and not auth_route:
            return await call_next(request)
        config = request.app.state.auth_config
        if config is None:
            return JSONResponse({"error": {"message": "Authentication is unavailable."}}, status_code=503)
        try:
            subjects = allowed_subjects()
        except ValueError:
            return JSONResponse({"error": {"message": "Authentication is unavailable."}}, status_code=503)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            if request.headers.get("origin") != config.origin:
                return JSONResponse({"error": {"message": "Untrusted request origin."}}, status_code=403)
        if private:
            subject = request.session.get("sub")
            expires = request.session.get("expires", 0)
            if not subject or not isinstance(expires, (float, int)) or time.time() >= expires:
                request.session.clear()
                if path == "/app" or path.startswith("/app/"):
                    return RedirectResponse("/auth/login?" + urlencode({"next": path}), status_code=303)
                return JSONResponse({"error": {"message": "Sign in required."}}, status_code=401)
            if subject not in subjects:
                request.session.clear()
                return JSONResponse({"error": {"message": "Access is not allowed."}}, status_code=403)
        return await call_next(request)


async def login(request: Request) -> Response:
    target = request.query_params.get("next", "/app")
    if not (target == "/app" or target.startswith("/app/")) or "\\" in target:
        target = "/app"
    request.session.clear()
    request.session["next"] = target
    config = request.app.state.auth_config
    return await request.app.state.google.authorize_redirect(
        request, config.origin + "/auth/callback", prompt="select_account"
    )


async def callback(request: Request) -> Response:
    target = request.session.get("next", "/app")
    try:
        token = await request.app.state.google.authorize_access_token(request, leeway=0)
        claims = token.get("userinfo", {})
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ValueError("Missing Google subject")
        authorized = subject in allowed_subjects()
    except (AuthlibBaseError, JoseError, HTTPError, ValueError):
        request.session.clear()
        return JSONResponse({"error": {"message": "Google sign-in failed."}}, status_code=401)
    request.session.clear()
    if not authorized:
        return JSONResponse({"error": {"message": "Access is not allowed."}}, status_code=403)
    request.session.update(sub=subject, expires=time.time() + request.app.state.auth_config.session_seconds)
    return RedirectResponse(target, status_code=303)


async def logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


def configure_auth(application: FastAPI) -> None:
    # Invalid configuration leaves readiness and all private paths closed, even
    # when an ASGI server or test client does not execute lifespan hooks.
    try:
        config = AuthConfig.from_environment()
    except ValueError:
        config = None
    application.state.auth_config = config
    application.add_middleware(PractitionerBoundary)
    if config is not None:
        oauth = OAuth()
        application.state.google = oauth.register(
            "google", client_id=config.client_id, client_secret=config.client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email", "code_challenge_method": "S256"},
        )
        application.add_middleware(
            CSRFMiddleware, secret=config.session_secret, cookie_name=CSRF_COOKIE,
            cookie_secure=True, exempt_urls=[re.compile(rf"^(?!{PRIVATE_PATH_PATTERN}|/auth/)")],
        )
        application.add_middleware(
            SessionMiddleware, secret_key=config.session_secret, session_cookie=SESSION_COOKIE,
            max_age=config.session_seconds, https_only=True, same_site="lax",
        )
        host = urlsplit(config.origin).hostname
        assert host is not None
        application.add_middleware(PractitionerTrustedHost, allowed_hosts=[host])
    application.add_api_route("/auth/login", login, methods=["GET"])
    application.add_api_route("/auth/callback", callback, methods=["GET"])
    application.add_api_route("/auth/logout", logout, methods=["POST"])
