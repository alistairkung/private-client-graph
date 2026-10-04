"""HTTPS and Google substitution for browser tests; never imported by production."""
import datetime
import ipaddress
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from urllib.parse import urlencode
from fastapi import Request
from starlette.responses import RedirectResponse
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from google_boundary import GoogleBoundary


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
    GoogleBoundary(origin + "/_test/google").install(app)

    async def google_authorization(request: Request):
        params = request.query_params
        return RedirectResponse(origin + "/auth/callback?" + urlencode({
            "state": params["state"], "code": params["nonce"],
        }), status_code=302)

    app.add_api_route("/_test/google", google_authorization, methods=["GET"])
    app.router.routes.insert(0, app.router.routes.pop())
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=1))
            .not_valid_after(now + datetime.timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            ]), critical=False).sign(key, hashes.SHA256()))
    with TemporaryDirectory(prefix="pcg-browser-tls-") as directory:
        key_path, cert_path = Path(directory) / "key.pem", Path(directory) / "cert.pem"
        key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        uvicorn.run(app, host="127.0.0.1", port=port,
                    ssl_keyfile=str(key_path), ssl_certfile=str(cert_path))
