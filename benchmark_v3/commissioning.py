"""Custodian-side validation and projection for Benchmark v3 research packets."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter

from benchmark_v3.portfolio import PortfolioProposal
from benchmark_v3.research_contracts import (
    AdmittedFamily,
    CoverageRegister,
    FamilyId,
    Hypothesis,
    HypothesisRef,
    OwnerDecision,
    PlanningRecord,
    PlanningResult,
    PublicReference,
    ReconciliationContext,
    ReconciliationRecord,
    ReconciliationResult,
    SessionProvenance,
)

_ROOT = Path(__file__).resolve().parent
ARCHITECT_PROMPT = "instructions/research-architect-v1.md"
DESIGNER_PROMPT = "instructions/commissioned-designer-v1.md"
PLANNING_LABELS = {"research_specification", "development_findings", "practice_references"}
PORTFOLIO_LABELS = {"portfolio_specification", "development_findings", "practice_references"}
RECONCILIATION_LABELS = {"hypothesis_revision", "admission_dossier", "technical_findings"}
HISTORICAL_FAMILIES = frozenset({"A", "B", "C"})
_FAMILY_ID = TypeAdapter(FamilyId)
_REFERENCES = TypeAdapter(list[PublicReference])
_T = TypeVar("_T", bound=BaseModel)


def json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def trusted_bytes(relative_path: str) -> bytes:
    """Read a custodian-owned artifact within the factory's fixed data root."""
    path = _trusted_path(relative_path)
    if not path.is_file():
        raise ValueError(f"Missing custodian artifact: {relative_path}")
    return path.read_bytes()


def _trusted_path(relative_path: str) -> Path:
    path = _ROOT / relative_path
    if not path.is_relative_to(_ROOT) or path.resolve() != path:
        raise ValueError(f"Unsafe custodian artifact path: {relative_path}")
    return path


def _validate_json(contract: type[_T], content: str | bytes) -> _T:
    return contract.model_validate(_read_json(content))


def _read_json(content: str | bytes) -> Any:
    def unique_members(members: list[tuple[str, Any]]) -> dict[str, Any]:
        result = dict(members)
        if len(result) != len(members):
            raise ValueError("Research artifacts must use unique JSON keys.")
        return result

    return json.loads(content, object_pairs_hook=unique_members)


def coverage_register() -> CoverageRegister:
    register = _validate_json(CoverageRegister, trusted_bytes("coverage.json"))
    axes = [axis.id for axis in register.taxonomy]
    families = [family.family_id for family in register.families]
    if len(set(axes)) != len(axes) or len(set(families)) != len(families):
        raise ValueError("The coverage register has duplicate axes or families.")
    _validate_axes([axis for gap in register.gaps for axis in gap.axes], axes)
    for family in register.families:
        _validate_axes(
            [family.primary_axis, *family.secondary_axes]
            + [finding.axis for finding in family.verified_findings],
            axes,
        )
    return register


def _historical_or_admitted(family: str) -> bool:
    if family in HISTORICAL_FAMILIES:
        return True
    relative_path = f"family_{family.lower()}/admission.json"
    path = _ROOT / relative_path
    return (path.exists() or path.is_symlink()) and (
        _read_json(trusted_bytes(relative_path)).get("status") == "admitted"
    )


def admitted_family_ids() -> set[str]:
    """Read development admission statuses without opening evaluation custody."""
    admitted = set()
    for path in sorted(_ROOT.glob("family_*/admission.json")):
        name = path.parent.name.removeprefix("family_").upper()
        record = _read_json(trusted_bytes(path.relative_to(_ROOT).as_posix()))
        if record.get("status") == "admitted":
            _admission(name)
            admitted.add(name)
    return admitted


def development_artifact_path(relative_path: str) -> Path:
    """Resolve a projected development file under the architect custody root."""
    return _trusted_path(relative_path)


def _admission(family: str) -> tuple[dict[str, Any], str]:
    family = _FAMILY_ID.validate_python(family)
    directory = f"family_{family.lower()}"
    content = trusted_bytes(f"{directory}/admission.json")
    admission = _read_json(content)
    signature = admission.get("signature") if isinstance(admission, dict) else None
    if not (
        isinstance(signature, dict)
        and signature.get("source")
        and signature.get("recorded_at")
        and re.fullmatch(r"[0-9a-f]{40}", str(signature.get("reviewed_commit")))
        and admission.get("family") == family
        and (family in HISTORICAL_FAMILIES or admission.get("split") == "development")
        and admission.get("status") == "admitted"
        and admission.get("owner_decision") == "accept"
        and admission.get("manifest_sha256") == digest(trusted_bytes(f"{directory}/manifest.json"))
    ):
        raise ValueError(f"Family {family} requires a recorded human admission of its manifest.")
    manifest = _read_json(trusted_bytes(f"{directory}/manifest.json"))
    if manifest.get("schema_version") == 4:
        _verify_batch_admission(admission, manifest, directory)
    return admission, digest(content)


def _verify_batch_admission(
    admission: dict[str, Any], manifest: dict[str, Any], directory: str,
) -> None:
    files = admission.get("review_files")
    if not isinstance(files, dict) or not all(isinstance(name, str) for name in files):
        raise ValueError("Batch admission requires exact review file digests.")
    required = {
        "DOSSIER.md", "manifest.json", "freeze.json", "dossier.json", "replay/preflight.json",
        *(name for condition in manifest["conditions"] for name in (f"{condition}.json", f"sources/{condition}.json")),
    }
    if (
        files.keys() != required or admission.get("approved_conditions") != sorted(manifest["conditions"])
        or files["freeze.json"] != manifest["freeze_sha256"]
        or files["dossier.json"] != admission["signature"].get("reviewed_family_sha256")
        or any(digest(trusted_bytes(f"{directory}/{name}")) != expected for name, expected in files.items())
    ):
        raise ValueError("The admitted family differs from the exact reviewed dossier and files.")


def _rounds() -> list[PlanningRecord]:
    return [
        _validate_json(PlanningRecord, trusted_bytes(path.relative_to(_ROOT).as_posix()))
        for path in sorted(_trusted_path("planning/rounds").glob("*.json"))
    ]


def hypothesis_ref(hypothesis: Hypothesis, provenance: SessionProvenance) -> HypothesisRef:
    content = json_text({
        "hypothesis": hypothesis.model_dump(mode="json"),
        "provenance": provenance.model_dump(mode="json"),
    })
    return HypothesisRef(
        hypothesis_id=hypothesis.hypothesis_id,
        revision=hypothesis.revision,
        hypothesis_sha256=digest(content.encode("utf-8")),
    )


def proposal_history() -> dict[str, tuple[Hypothesis, HypothesisRef, OwnerDecision | None]]:
    history = {}
    for record in _rounds():
        for hypothesis in record.result.proposals:
            ref = hypothesis_ref(hypothesis, record.provenance)
            key = f"{ref.hypothesis_id}@{ref.revision}"
            if key in history:
                raise ValueError(f"Duplicate hypothesis revision: {key}")
            history[key] = (hypothesis, ref, _owner_decision(ref))
    for hypothesis, _, _ in history.values():
        if hypothesis.revision > 1:
            previous = history.get(f"{hypothesis.hypothesis_id}@{hypothesis.revision - 1}")
            if (
                previous is None or previous[0].family_id != hypothesis.family_id
                or previous[1].hypothesis_sha256 != hypothesis.previous_revision_sha256
            ):
                raise ValueError(f"Invalid revision lineage for {hypothesis.hypothesis_id}.")
    return history


def _owner_decision(ref: HypothesisRef) -> OwnerDecision | None:
    relative_path = f"planning/decisions/{ref.hypothesis_id}@{ref.revision}.json"
    path = _ROOT / relative_path
    if not path.exists() and not path.is_symlink():
        return None
    decision = _validate_json(OwnerDecision, trusted_bytes(relative_path))
    if (decision.hypothesis_id, decision.revision, decision.hypothesis_sha256) != (
        ref.hypothesis_id, ref.revision, ref.hypothesis_sha256,
    ):
        raise ValueError("The owner decision does not match the exact hypothesis revision digest.")
    return decision


def approved_hypothesis(key: str) -> tuple[Hypothesis, HypothesisRef]:
    if re.fullmatch(r"[a-z][a-z0-9-]{1,63}@[1-9][0-9]*", key) is None:
        raise ValueError("Use a hypothesis revision identifier such as example@1.")
    record = proposal_history().get(key)
    if record is None or record[2] is None or record[2].status != "approved":
        raise ValueError("A registered, human-approved hypothesis revision is required.")
    return record[0], record[1]


def designer_brief(key: str) -> dict[str, Any]:
    hypothesis, ref = approved_hypothesis(key)
    if _historical_or_admitted(hypothesis.family_id):
        raise ValueError("An existing admission record reserves this Matter family ID.")
    return {
        "commission": ref.model_dump(mode="json"),
        "family_id": hypothesis.family_id,
        "primary_axis": hypothesis.objective.primary_axis,
        "capability_question": hypothesis.objective.falsifiable_hypothesis,
        "retainer": hypothesis.grounding.retainer,
        "meeting_purpose": hypothesis.grounding.meeting_purpose,
        "scenario": hypothesis.design.scenario,
        "genres_and_provenance": hypothesis.design.genres_and_provenance,
        "intervention": hypothesis.design.intervention,
        "invariants": hypothesis.design.invariants,
        "negative_controls": hypothesis.design.negative_controls,
        "acceptance_criteria": hypothesis.design.success_criteria,
    }


def prepare_architect(inputs: dict[str, str]) -> tuple[dict[str, str], dict[str, Any]]:
    """Build an exact-profile packet and capture the context needed to admit its output."""
    if any(not value.strip() for value in inputs.values()):
        raise ValueError("Architect inputs must be nonempty.")
    register = coverage_register()
    axes = [axis.id for axis in register.taxonomy]
    if inputs.keys() == PORTFOLIO_LABELS:
        from benchmark_v3.batch.authorisation import admitted_coverage

        planning_inputs = inputs.copy()
        planning_inputs["research_specification"] = planning_inputs.pop("portfolio_specification")
        projected, metadata = _prepare_planning(planning_inputs, register, axes)
        coverage_digest, existing = admitted_coverage()
        snapshot = {"coverage_sha256": coverage_digest, "existing": [row.model_dump() for row in existing]}
        return projected | {"admitted_snapshot": json_text(snapshot)}, metadata | {"profile": "portfolio"}
    if inputs.keys() == PLANNING_LABELS:
        return _prepare_planning(inputs, register, axes)
    if inputs.keys() == RECONCILIATION_LABELS:
        hypothesis, context = _reconciliation_context(inputs["hypothesis_revision"])
        metadata = {"profile": "reconciliation", "axes": axes, "admission": context.model_dump(mode="json")}
        return {
            "approved_hypothesis": json_text({
                "proposal": hypothesis.model_dump(mode="json"),
                "approved_revision": context.hypothesis.model_dump(mode="json"),
            }),
            "admission_dossier": inputs["admission_dossier"],
            "technical_findings": inputs["technical_findings"],
            "coverage_register": _portfolio(register),
        }, metadata
    raise ValueError("The architect packet must match the planning or reconciliation input allowlist.")


def _prepare_planning(
    inputs: dict[str, str], register: CoverageRegister, axes: list[str],
) -> tuple[dict[str, str], dict[str, Any]]:
    references = _REFERENCES.validate_python(_read_json(inputs["practice_references"]))
    history = proposal_history()
    previous = {
        key: {
            "hypothesis": hypothesis.model_dump(mode="json"),
            "ref": ref.model_dump(mode="json"),
            "decision": decision.model_dump(mode="json") if decision else None,
        }
        for key, (hypothesis, ref, decision) in history.items()
    }
    metadata = {
        "profile": "planning",
        "axes": axes,
        "families": [family.family_id for family in register.families],
        "references": sorted({str(reference.url) for reference in references}),
        "previous_revisions": {
            key: {"family_id": hypothesis.family_id, **ref.model_dump(mode="json")}
            for key, (hypothesis, ref, _) in history.items()
        },
    }
    return inputs | {
        "coverage_register": _portfolio(register),
        "ontology": trusted_bytes("instructions/ontology.md").decode("utf-8"),
        "previous_decisions": json_text(previous),
    }, metadata


def _portfolio(register: CoverageRegister) -> str:
    assessments = []
    for family in register.families:
        verify_coverage_family(family)
        reconciliation = saved_reconciliation(family)
        if reconciliation:
            assessments.append(reconciliation.model_dump(mode="json"))
    return json_text({"coverage": register.model_dump(mode="json"), "reconciliations": assessments})


def _reconciliation_context(key: str) -> tuple[Hypothesis, ReconciliationContext]:
    hypothesis, ref = approved_hypothesis(key)
    if hypothesis.family_id in HISTORICAL_FAMILIES:
        raise ValueError("Historical admissions have no approved Research Architect hypothesis.")
    admission, admission_sha256 = _admission(hypothesis.family_id)
    if admission.get("hypothesis") != ref.model_dump(mode="json"):
        raise ValueError("The admission must identify this approved hypothesis revision and digest.")
    return hypothesis, ReconciliationContext(
        family_id=hypothesis.family_id, hypothesis=ref, admission_sha256=admission_sha256,
    )


def verify_coverage_family(family: AdmittedFamily) -> None:
    historical = family.family_id in HISTORICAL_FAMILIES
    if historical != (family.protocol == "historical"):
        raise ValueError(f"Unexpected historical lineage for Family {family.family_id}.")
    ref = family.hypothesis
    if ref is None:
        _, admission_sha256 = _admission(family.family_id)
    else:
        hypothesis, context = _reconciliation_context(f"{ref.hypothesis_id}@{ref.revision}")
        admission_sha256 = context.admission_sha256
        if (
            context.family_id != family.family_id or context.hypothesis != ref
            or hypothesis.objective.primary_axis != family.primary_axis
            or hypothesis.objective.secondary_axes != family.secondary_axes
            or hypothesis.objective.falsifiable_hypothesis != family.intended_difficulty
        ):
            raise ValueError("Coverage differs from the admitted, approved hypothesis or axes.")
    if admission_sha256 != family.admission_sha256:
        raise ValueError(f"Coverage admission digest mismatch for Family {family.family_id}.")


def saved_reconciliation(family: AdmittedFamily) -> ReconciliationRecord | None:
    relative_path = f"planning/reconciliations/{family.family_id}.json"
    path = _ROOT / relative_path
    if not path.exists() and not path.is_symlink():
        return None
    record = _validate_json(ReconciliationRecord, trusted_bytes(relative_path))
    if (
        record.context.family_id != family.family_id
        or record.context.hypothesis != family.hypothesis
        or record.context.admission_sha256 != family.admission_sha256
    ):
        raise ValueError("The saved reconciliation does not match the admitted coverage row.")
    return record


def validate_architect_result(
    output: str, metadata: dict[str, Any],
) -> PlanningResult | ReconciliationResult | PortfolioProposal:
    if metadata["profile"] == "planning":
        plan = _validate_json(PlanningResult, output)
        _validate_plan(plan, metadata)
        return plan
    if metadata["profile"] == "portfolio":
        from benchmark_v3.batch.authorisation import verify_portfolio

        portfolio = _validate_json(PortfolioProposal, output)
        verify_portfolio(portfolio)
        if any(f"{slot.hypothesis.hypothesis_id}@{slot.hypothesis.revision}"
               not in metadata["previous_revisions"] for slot in portfolio.slots):
            raise ValueError("Portfolio slots may reference only staged hypotheses.")
        return portfolio
    if metadata["profile"] == "reconciliation":
        assessment = _validate_json(ReconciliationResult, output)
        _validate_axes(
            [finding.axis for finding in assessment.verified_findings]
            + [axis for gap in assessment.remaining_gaps for axis in gap.axes],
            metadata["axes"],
        )
        return assessment
    raise ValueError("Unknown Research Architect packet profile.")


def _validate_plan(plan: PlanningResult, metadata: dict[str, Any]) -> None:
    if sorted(item.family_id for item in plan.family_assessments) != sorted(metadata["families"]):
        raise ValueError("Assess each admitted family exactly once.")
    identities = [proposal.hypothesis_id for proposal in plan.proposals]
    families = [proposal.family_id for proposal in plan.proposals]
    if len(set(identities)) != len(identities) or len(set(families)) != len(families):
        raise ValueError("Rank each proposed family and hypothesis only once per round.")
    _validate_axes([axis for gap in plan.gaps for axis in gap.axes], metadata["axes"])
    previous = metadata["previous_revisions"]
    for proposal in plan.proposals:
        if proposal.family_id in metadata["families"] or proposal.family_id in HISTORICAL_FAMILIES:
            raise ValueError("A proposal cannot reuse an admitted family ID.")
        if f"{proposal.hypothesis_id}@{proposal.revision}" in previous:
            raise ValueError("A proposal cannot overwrite an existing revision.")
        if proposal.revision > 1:
            parent = previous.get(f"{proposal.hypothesis_id}@{proposal.revision - 1}")
            if (
                parent is None or parent["family_id"] != proposal.family_id
                or parent["hypothesis_sha256"] != proposal.previous_revision_sha256
            ):
                raise ValueError("A revised proposal must preserve the exact prior lineage.")
        _validate_axes(
            [proposal.objective.primary_axis, *proposal.objective.secondary_axes], metadata["axes"],
        )
        if any(str(reference.url) not in metadata["references"] for reference in proposal.grounding.references):
            raise ValueError("Hypotheses may cite only supplied public references.")


def _validate_axes(used: list[str], taxonomy: list[str]) -> None:
    if set(used) - set(taxonomy):
        raise ValueError("A finding or proposal references an unregistered difficulty axis.")
