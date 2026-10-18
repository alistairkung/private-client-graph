"""Local-only launcher; reuse unchanged PCG auth/model substitutes and API."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.update({
    "PCG_GOOGLE_CLIENT_ID": "local-development.apps.googleusercontent.com",
    "PCG_GOOGLE_CLIENT_SECRET": "local-development-google-secret",
    "PCG_GOOGLE_SUB_ALLOWLIST": "local-development-subject",
    "PCG_SESSION_SECRET": "practitioner-next-local-synthetic-session-secret-only",
    "PCG_SESSION_SECONDS": "3600",
    "PCG_TRUSTED_ORIGIN": "https://127.0.0.1:5443",
    "PCG_PROPOSAL_ANALYSIS_LIMIT": "1000",
    "PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS": "86400",
    "PCG_SHOWCASE_LIVE_ENABLED": "false",
    "DEEPSEEK_API_KEY": "local-development-model-substitute",
})
if not os.environ.get("DATABASE_URL"):
    raise SystemExit("Set DATABASE_URL to a migrated, seeded disposable PostgreSQL database. See README.md.")

from local_development.server import create_local_app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(create_local_app(origin=os.environ["PCG_TRUSTED_ORIGIN"]), host="127.0.0.1", port=8001)
