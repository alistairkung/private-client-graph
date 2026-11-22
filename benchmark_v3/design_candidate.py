"""Isolated preparation of unapproved development design candidates."""

from typing import Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import science
from benchmark_v3.batch.contracts import DesignOutput, SourceId
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.research_contracts import NonemptyNotes
from private_client_graph.evaluation import _edge
from private_client_graph.models.evaluation_result import SemanticEdge


class CandidateDesign(DesignOutput):
    expected_graphs: dict[SourceId, list[SemanticEdge]]
    evidence_routes: dict[SourceId, NonemptyNotes]
    knowledge_boundaries: NonemptyNotes
    documentary_assumptions: NonemptyNotes
    shortcut_predictions: NonemptyNotes
    independent_review_plan: NonemptyNotes
    open_questions: NonemptyNotes
    approximate_source_words: dict[SourceId, int]


def prepare(request: dict[str, Any]) -> None:
    """Project a registered proposal into a non-commissioning designer packet."""
    inputs = request["inputs"]
    if inputs.keys() != {"hypothesis_revision", "portfolio_slot"}:
        raise ValueError("Supply only the registered proposal revision and workload slot.")
    record = commissioning.proposal_history().get(inputs["hypothesis_revision"])
    if record is None or record[2] is not None:
        raise ValueError("Candidate design requires a registered proposal pending owner disposition.")
    hypothesis, ref, _ = record
    slot = FamilySlot.model_validate(commissioning._read_json(inputs["portfolio_slot"]))
    if (slot.hypothesis != ref or slot.family_id != hypothesis.family_id
            or slot.primary_axis != hypothesis.objective.primary_axis
            or slot.secondary_axes != hypothesis.objective.secondary_axes
            or len(slot.matched_conditions) + 1 != hypothesis.feasibility.conditions
            or slot.retainer != hypothesis.grounding.retainer
            or slot.workflow != hypothesis.grounding.legal_workflow
            or slot.natural_condition != hypothesis.design.scenario
            or slot.matched_conditions != (
                [hypothesis.design.intervention] if hypothesis.feasibility.conditions == 2 else []
            )):
        raise ValueError("Candidate slot differs from the registered proposal.")
    brief = commissioning._designer_brief(hypothesis, ref)
    brief["proposal"] = brief.pop("commission")
    brief["authority"] = "design candidate only; no approval or construction"
    brief["workload"] = {
        "tier": slot.tier, "expected_sources": slot.expected_sources,
        "condition_count": hypothesis.feasibility.conditions,
    }
    brief["evidence_dependencies"] = hypothesis.design.evidence_dependencies
    brief["shortcut_heuristics"] = hypothesis.design.shortcut_heuristics
    brief["practice_references"] = [
        item.model_dump(mode="json") for item in hypothesis.grounding.references
    ]
    prompt = commissioning.trusted_bytes("instructions/candidate-designer-v1.md").decode()
    schema = commissioning.json_text(CandidateDesign.model_json_schema())
    request.update(
        candidate_design=True,
        prompt=f"{prompt}\nOutput schema: {schema}",
        inputs={"capability_brief": commissioning.json_text(brief)},
    )


def verify_candidate(slot: FamilySlot, design: CandidateDesign) -> None:
    """Check structural commitments and the proposed complete graphs."""
    science.verify_design(slot, design)
    inventory = {item.source_id: item for item in design.inventory}
    if design.approximate_source_words.keys() != inventory.keys() or any(
        words < 1 for words in design.approximate_source_words.values()
    ):
        raise ValueError("Estimate text volume for every natural Source.")
    if design.scaling_snapshots:
        raise ValueError("This checkpoint permits the planned conditions only.")
    conditions = science.condition_ids(slot)
    if design.expected_graphs.keys() != set(conditions) or design.evidence_routes.keys() != set(conditions):
        raise ValueError("Commit a complete provisional graph and evidence plan for each condition.")
    for condition, edges in design.expected_graphs.items():
        if (len(set(edges)) != len(edges) or any(edge != _edge(*edge) for edge in edges)
                or set(edges) & set(design.candidates) != set(design.required[condition])):
            raise ValueError("Provisional graph disagrees with its canonical critical declarations.")
    ordinary = [set(edges) - set(design.candidates) for edges in design.expected_graphs.values()]
    if not ordinary[0] or any(edges != ordinary[0] for edges in ordinary):
        raise ValueError("Retain at least one independent ordinary edge across conditions.")
    order = list(inventory)
    for condition, control in zip(conditions[1:], design.matched, strict=True):
        if control.edit:
            edit = control.edit
            author = inventory.get(edit.source_id)
            if (author is None or edit.before == edit.after
                    or author.participant_brief.count(edit.before) != 1):
                raise ValueError("A literal control must identify one baseline instruction in its Source brief.")
        elif (control.order == order or len(control.order or []) != len(order)
              or set(control.order or []) != set(order)
              or set(design.expected_graphs[condition]) != set(design.expected_graphs[conditions[0]])):
            raise ValueError("An order control must permute every Source and preserve the graph.")
