"""Suppress transport diagnostics inside private Workspace requests, including OAuth callback URLs."""

from contextvars import ContextVar
import logging

from starlette.types import ASGIApp, Receive, Scope, Send

private_request = ContextVar("private_workspace_request", default=False)


class _PrivateDiagnostics(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "uvicorn.access":
            return not (
                isinstance(record.args, tuple)
                and len(record.args) >= 3
                and str(record.args[2]).split("?")[0] == "/auth/workspace/callback"
            )
        return not private_request.get()


_filter = _PrivateDiagnostics()


class WorkspaceLogBoundary:
    def __init__(self, app: ASGIApp):
        self.app = app
        for name in (
            "uvicorn.access",
            "httpx2",
            "authlib.integrations.base_client.sync_app",
            "httpcore2.connection",
            "httpcore2.http11",
            "httpcore2.http2",
            "httpcore2.proxy",
            "authlib.oauth2.client",
            "authlib.integrations.base_client.async_app",
        ):
            logging.getLogger(name).addFilter(_filter)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        flag = private_request.set(
            path.startswith("/api/matter-proposals/discovery/") or path == "/auth/workspace/callback"
        )
        try:
            await self.app(scope, receive, send)
        finally:
            private_request.reset(flag)
