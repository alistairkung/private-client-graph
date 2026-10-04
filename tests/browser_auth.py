"""HTTPS and Google substitution for browser tests; never imported by production."""
import os

from urllib.parse import urlencode
from fastapi import Request
from starlette.responses import RedirectResponse
from google_boundary import make_google_boundary
from local_development.https import serve_https


def configure_browser_auth(port):
    os.environ.update({
        "PCG_GOOGLE_CLIENT_ID": "test-client.apps.googleusercontent.com",
        "PCG_GOOGLE_CLIENT_SECRET": "test-google-secret",
        "PCG_SESSION_SECRET": "test-session-secret-with-at-least-32-characters",
        "PCG_TRUSTED_ORIGIN": f"https://127.0.0.1:{port}",
        "PCG_GOOGLE_SUB_ALLOWLIST": "test-subject",
        "PCG_SESSION_SECONDS": "900",
        "PCG_PROPOSAL_ANALYSIS_LIMIT": "100",
        "PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS": "86400",
        "DEEPSEEK_API_KEY": "test-only",
    })


def serve(app, port):
    origin = f"https://127.0.0.1:{port}"
    make_google_boundary(origin + "/_test/google").install(app)

    async def google_authorization(request: Request):
        params = request.query_params
        return RedirectResponse(origin + "/auth/callback?" + urlencode({
            "state": params["state"], "code": params["nonce"],
        }), status_code=302)

    app.add_api_route("/_test/google", google_authorization, methods=["GET"])
    app.router.routes.insert(0, app.router.routes.pop())
    serve_https(app, host="127.0.0.1", port=port)
