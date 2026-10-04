"""Fixed Case 01 orchestration over the existing extraction and graph boundaries."""

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr
from openai import APIConnectionError, APIStatusError

from private_client_graph.extract import extract_relationships_from_text

from private_client_graph.graph import build_graph
from private_client_graph.models import CanonicalGraph, ExtractionResult

from .contracts import AnalysisError, AnalysisMode, CaseAnalysis, CaseDetail, Execution
from .errors import AnalysisFailure
from .showcase_live import LiveConfig, require_live, consume_live_slot

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "cases" / "case_01"


def get_case() -> CaseDetail:
    try:
        source = (CASE / "source.txt").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AnalysisFailure(
            AnalysisError(
                stage="source",
                message="The synthetic source could not be loaded.",
            )
        ) from exc
    return CaseDetail(
        title="Case 01 · Evergreen Family Trust",
        notice="Synthetic case · Fictional material for demonstration only",
        source_text=source,
    )


def analyse_case(mode: AnalysisMode, live_config: LiveConfig) -> CaseAnalysis:
    source = get_case().source_text
    if mode == "live":
        extraction, run_id = _run_live_analysis(source, live_config)
    else:
        extraction = _load_sample_extraction()
        run_id = None

    graph = _build_canonical_graph(extraction, source, run_id)
    return CaseAnalysis(
        execution=Execution(mode=mode, run_artifact_id=run_id), graph=graph
    )


def _run_live_analysis(
    source: str, live_config: LiveConfig
) -> tuple[ExtractionResult, str]:
    require_live(live_config)
    try:
        extraction = extract_live(source, live_config)
    except AnalysisFailure:
        raise
    except Exception as exc:
        raise AnalysisFailure(
            AnalysisError(
                stage="provider",
                message="Live analysis could not be completed.",
                retryable=_is_retryable_provider_failure(exc),
            ),
            502,
        ) from exc

    try:
        run_id = _persist_extraction(extraction)
    except OSError as exc:
        raise AnalysisFailure(
            AnalysisError(
                stage="persistence",
                message="Live analysis could not be saved. No analysis was produced.",
            )
        ) from exc
    return extraction, run_id


def _load_sample_extraction() -> ExtractionResult:
    try:
        return ExtractionResult.model_validate_json(
            (CASE / "expected_extraction.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        raise AnalysisFailure(
            AnalysisError(
                stage="sample",
                message="The sample analysis could not be loaded.",
            )
        ) from exc


def _build_canonical_graph(
    extraction: ExtractionResult, source: str, run_id: str | None
) -> CanonicalGraph:
    try:
        return build_graph(
            extraction.relationships, document="source.txt", source_text=source
        )
    except ValueError as exc:
        raise AnalysisFailure(
            AnalysisError(
                stage="graph",
                message="The extracted relationships could not be validated. No analysis was produced.",
                run_artifact_id=run_id,
            ),
            422,
        ) from exc


def _is_retryable_provider_failure(exc: Exception) -> bool:
    return isinstance(exc, APIConnectionError) or (
        isinstance(exc, APIStatusError)
        and (exc.status_code in (408, 429) or exc.status_code >= 500)
    )


def extract_live(source: str, config: LiveConfig) -> ExtractionResult:
    """Invoke the model once; configuration never crosses the browser boundary."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("Live analysis is not configured.")
    llm = ChatDeepSeek(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        api_key=SecretStr(api_key),
        max_retries=0,
        timeout=90,
        extra_body={"thinking": {"type": "disabled"}},
    )
    consume_live_slot(config)
    return extract_relationships_from_text(source, llm=llm)


def _persist_extraction(extraction: ExtractionResult) -> str:
    run_dir = Path(os.getenv("PCG_RUN_DIR", str(ROOT / "runs" / "case_01")))
    run_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    run_id = f"{timestamp}-{uuid4().hex}.json"
    with (run_dir / run_id).open("x", encoding="utf-8") as run_file:
        run_file.write(extraction.model_dump_json(indent=2) + "\n")
    return run_id
