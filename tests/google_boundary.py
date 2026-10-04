"""Test-only Google HTTP boundary; real OAuth state and JWT validation remain active."""
import time
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx2 as httpx
from joserfc import jwt
from joserfc.jwk import RSAKey


class GoogleBoundary:
    def __init__(self, authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth"):
        self.authorization_endpoint = authorization_endpoint
        self.key = RSAKey.generate_key(2048)
        self.claims = {}
        self.bad_signature = False

    def respond(self, request):
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
                "iss": "https://accounts.google.com", "sub": "test-subject",
                "aud": "test-client.apps.googleusercontent.com",
                "iat": int(time.time()), "exp": int(time.time()) + 300,
                "nonce": params["code"][0],
            } | self.claims
            key = RSAKey.generate_key(2048) if self.bad_signature else self.key
            payload = {"access_token": "google-access-token-never-store", "token_type": "Bearer",
                       "id_token": jwt.encode({"alg": "RS256"}, claims, key)}
        else:
            raise AssertionError(f"Unexpected Google request: {request.url}")
        return httpx.Response(200, json=payload)

    def install(self, app):
        app.state.google.client_kwargs["transport"] = httpx.MockTransport(self.respond)


def sign_in(client, *, next_path="/app"):
    response = client.get("/auth/login", params={"next": next_path}, follow_redirects=False)
    params = parse_qs(urlsplit(response.headers["location"]).query)
    return client.get("/auth/callback?" + urlencode({
        "state": params["state"][0], "code": params["nonce"][0],
    }), follow_redirects=False)
