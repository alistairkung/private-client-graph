"""Synthetic local Google HTTP boundary; never included in the production image."""

import time
from urllib.parse import parse_qs

import httpx2 as httpx
from fastapi import FastAPI
from joserfc import jwt
from joserfc.jwk import RSAKey


class GoogleBoundary:
    def __init__(
        self,
        authorization_endpoint: str = "https://accounts.google.com/o/oauth2/v2/auth",
        *,
        subject: str = "local-development-subject",
        client_id: str = "local-development.apps.googleusercontent.com",
    ) -> None:
        self.authorization_endpoint = authorization_endpoint
        self.subject = subject
        self.client_id = client_id
        self.key = RSAKey.generate_key(2048)
        self.claims: dict[str, object] = {}
        self.bad_signature = False

    def respond(self, request: httpx.Request) -> httpx.Response:
        payload: dict[str, object]
        if request.url.path.endswith("openid-configuration"):
            payload = {
                "issuer": "https://accounts.google.com",
                "authorization_endpoint": self.authorization_endpoint,
                "token_endpoint": "https://oauth2.googleapis.com/token",
                "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
                "id_token_signing_alg_values_supported": ["RS256"],
            }
        elif request.url.path.endswith("certs"):
            payload = {"keys": [self.key.as_dict(private=False)]}
        elif request.url.path == "/token":
            params = parse_qs(request.content.decode())
            claims = {
                "iss": "https://accounts.google.com",
                "sub": self.subject,
                "aud": self.client_id,
                "iat": int(time.time()),
                "exp": int(time.time()) + 300,
                "nonce": params["code"][0],
            } | self.claims
            key = RSAKey.generate_key(2048) if self.bad_signature else self.key
            payload = {
                "access_token": "local-google-access-token-never-store",
                "token_type": "Bearer",
                "id_token": jwt.encode({"alg": "RS256"}, claims, key),
            }
        else:
            raise AssertionError(f"Unexpected Google request: {request.url}")
        return httpx.Response(200, json=payload)

    def install(self, app: FastAPI) -> None:
        app.state.google.client_kwargs["transport"] = httpx.MockTransport(self.respond)
