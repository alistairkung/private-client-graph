"""Fixed, curated synthetic examples. No extraction or provider execution."""
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from private_client_graph.canonical_state import single_source_state, validate_canonical_state
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.source import Source
from private_client_graph.models import ExtractionResult
from private_client_graph.pipeline import Pipeline, PipelineInput
from .analysis_config import APPROVED_APPLICATION_PIPELINE_CONFIG

FIXTURES = Path(__file__).with_name("showcase_fixtures")
EVERGREEN = Path(__file__).resolve().parents[2] / "cases" / "case_01"


class ShowcaseCaseSummary(BaseModel):
    id: str
    title: str
    description: str


class ShowcaseCase(ShowcaseCaseSummary):
    result_kind: Literal["curated_ideal_fixture"] = "curated_ideal_fixture"
    notice: str = "Curated ideal fixture · Synthetic demonstration, not a measured model result."
    state: CanonicalState


CASES = (
    ShowcaseCaseSummary(id="case-01", title="Case 01 · Evergreen Family Trust", description="Family and trust relationships in one attendance note."),
    ShowcaseCaseSummary(id="case-04", title="Case 04 · Hillcrest Family Trust", description="Two complementary notes, one combined graph and source-specific Evidence."),
    ShowcaseCaseSummary(id="case-05", title="Case 05 · Trustee replacement", description="An explicit replacement establishes the current trustee; earlier family and trust facts remain."),
)


def list_showcase_cases() -> list[ShowcaseCaseSummary]:
    return list(CASES)


def get_showcase_case(case_id: str) -> ShowcaseCase | None:
    summary = next((case for case in CASES if case.id == case_id), None)
    if summary is None:
        return None
    if case_id == "case-01":
        state = _evergreen_state()
    else:
        state = CanonicalState.model_validate_json((FIXTURES / f"{case_id}.json").read_text(encoding="utf-8"))
        validate_canonical_state(state)
    return ShowcaseCase(**summary.model_dump(), state=state)


def _evergreen_state() -> CanonicalState:
    source = Source(
        id="source_001", title="Attendance note",
        text=(EVERGREEN / "source.txt").read_text(encoding="utf-8"),
    )
    extraction = ExtractionResult.model_validate_json(
        (EVERGREEN / "expected_extraction.json").read_text(encoding="utf-8")
    )
    result = Pipeline(APPROVED_APPLICATION_PIPELINE_CONFIG).run_from_extraction(
        PipelineInput(source_text=source.text, document="source.txt"), extraction,
    )
    return single_source_state(source, result.graph)
