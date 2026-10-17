from fastapi.testclient import TestClient
from private_client_graph.api.app import create_app
from private_client_graph.api.auth import SESSION_COOKIE


def test_demo_pages_are_public_while_practitioner_stays_protected(tmp_path):
    (tmp_path / "index.html").write_text("public shell")
    client = TestClient(create_app(tmp_path), base_url="https://testserver", follow_redirects=False)
    for path in ("/demo", "/demo/", "/demo/matters/hillcrest", "/demo/matter-proposals/new",
                 "/demo/matter-proposals/hillcrest", "/demo/confirmation/hillcrest", "/demo/unknown"):
        assert client.get(path).status_code == 200
        assert client.get(path).text == "public shell"
    assert client.get("/app").status_code == 303
    assert client.get("/api/matters").status_code == 401
    assert client.get("/api/matter-proposals").status_code == 401


def test_demo_has_no_submission_endpoint_or_session_side_effect(tmp_path):
    (tmp_path / "index.html").write_text("public shell")
    client = TestClient(create_app(tmp_path), base_url="https://testserver")
    for path in ("/demo", "/demo/matter-proposals/new", "/demo/matter-proposals/hillcrest",
                 "/demo/confirmation/hillcrest", "/demo/matters/hillcrest"):
        response = client.get(path)
        assert SESSION_COOKIE not in response.headers.get("set-cookie", "")
        assert client.post(path, json={"confirm": True}).status_code == 405
    assert SESSION_COOKIE not in client.cookies
