"""Test adapter for the shared synthetic Google HTTP boundary."""

from urllib.parse import parse_qs, urlencode, urlsplit

from local_development.google import GoogleBoundary


def make_google_boundary(
    authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
):
    return GoogleBoundary(
        authorization_endpoint,
        subject="test-subject",
        client_id="test-client.apps.googleusercontent.com",
    )


def sign_in(client, *, next_path="/app"):
    response = client.get("/auth/login", params={"next": next_path}, follow_redirects=False)
    params = parse_qs(urlsplit(response.headers["location"]).query)
    return client.get("/auth/callback?" + urlencode({
        "state": params["state"][0], "code": params["nonce"][0],
    }), follow_redirects=False)
