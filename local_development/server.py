"""Run the real protected application with only external providers substituted."""

from urllib.parse import urlencode

from fastapi import FastAPI, Request
from langchain_deepseek import ChatDeepSeek
from starlette.responses import RedirectResponse

from local_development.google import GoogleBoundary
from local_development.https import serve_https
from local_development.model import extract_fixture
from private_client_graph.api.app import create_app
from private_client_graph.application import matter_proposals
from private_client_graph.application.proposal_config import ProposalAnalysisConfig

DEFAULT_ORIGIN = "https://localhost:8443"


def create_local_app(origin: str = DEFAULT_ORIGIN) -> FastAPI:
    matter_proposals.extract_relationships_from_text = extract_fixture
    matter_proposals._construct_model = _deterministic_model
    application = create_app()
    if application.state.auth_config is None:
        raise RuntimeError("Local authentication configuration is missing or invalid")
    if application.state.auth_config.origin != origin:
        raise RuntimeError("PCG_TRUSTED_ORIGIN must match the local HTTPS origin")
    GoogleBoundary(origin + "/_development/google").install(application)

    async def google_authorization(request: Request) -> RedirectResponse:
        params = request.query_params
        callback = origin + "/auth/callback?" + urlencode(
            {"state": params["state"], "code": params["nonce"]}
        )
        return RedirectResponse(callback, status_code=302)

    application.add_api_route(
        "/_development/google", google_authorization, methods=["GET"]
    )
    _place_development_provider_before_static_files(application)
    return application


def _place_development_provider_before_static_files(application: FastAPI) -> None:
    # create_app mounts the frontend at `/`, so the development-only provider
    # route must precede that catch-all route to remain reachable in a browser.
    development_provider = application.router.routes.pop()
    application.router.routes.insert(0, development_provider)


def _deterministic_model(config: ProposalAnalysisConfig) -> ChatDeepSeek:
    del config
    return ChatDeepSeek.model_construct()


def serve() -> None:
    serve_https(create_local_app(), host="0.0.0.0", port=8443)


if __name__ == "__main__":
    serve()
