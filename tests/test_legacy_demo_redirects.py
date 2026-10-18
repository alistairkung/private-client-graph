from fastapi.testclient import TestClient
from private_client_graph.api.app import create_app
from private_client_graph.api.auth import SESSION_COOKIE


def test_legacy_demo_links_redirect_to_the_real_public_application(tmp_path):
    (tmp_path / "index.html").write_text("public shell")
    client = TestClient(create_app(tmp_path), base_url="https://testserver", follow_redirects=False)
    for path in ("/demo", "/demo/", "/demo/matters/hillcrest", "/demo/matter-proposals/new",
                 "/demo/matter-proposals/hillcrest", "/demo/confirmation/hillcrest", "/demo/unknown"):
        response = client.get(path)
        assert response.status_code == 308
        assert response.headers["location"] == "/app"
        assert SESSION_COOKIE not in response.headers.get("set-cookie", "")
        assert client.post(path, json={"confirm": True}).status_code == 405
    assert client.get("/app").text == "public shell"
