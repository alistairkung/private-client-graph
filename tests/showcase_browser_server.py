"""E2E-only server: real API/quota/graph, fixture at the model boundary."""

import os
from pathlib import Path

import uvicorn

# Never read real provider credentials in this deterministic test server.
os.environ.update({
    "PCG_SHOWCASE_LIVE_ENABLED": "true",
    "PCG_SHOWCASE_LIVE_LIMIT": "1",
    "PCG_SHOWCASE_LIVE_WINDOW_SECONDS": "86400",
    "DEEPSEEK_API_KEY": "e2e-test-only",
})

from private_client_graph.api.app import create_app
from private_client_graph.application import case_analysis
from private_client_graph.models import ExtractionResult


def extract_fixture(source, *, llm):
    return ExtractionResult.model_validate_json(
        (Path(__file__).resolve().parents[1] / "cases/case_01/expected_extraction.json").read_text()
    )


case_analysis.extract_relationships_from_text = extract_fixture

if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=4174)
