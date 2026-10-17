"""Fixed, curated synthetic examples. No extraction or provider execution."""
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from private_client_graph.canonical_state import single_source_state, validate_canonical_state
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.source import Source
from .case_analysis import analyse_case, get_case
from .showcase_live import LiveConfig

FIXTURES = Path(__file__).with_name("showcase_fixtures")


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
        detail = get_case()
        graph = analyse_case("sample", LiveConfig.from_environment()).graph
        state = single_source_state(Source(id="source_001", title="Attendance note", text=detail.source_text), graph)
    else:
        state = CanonicalState.model_validate_json((FIXTURES / f"{case_id}.json").read_text(encoding="utf-8"))
        validate_canonical_state(state)
    return ShowcaseCase(**summary.model_dump(), state=state)
