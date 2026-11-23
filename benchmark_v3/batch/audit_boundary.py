"""Project verified stage commitments into a delivery-attested scientific audit."""

from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, repair_authority, science
from benchmark_v3.batch.contracts import MaskAssignment, MilestoneAudit, SourceId
from benchmark_v3.research_contracts import Text
from private_client_graph.evaluation import _edge
from private_client_graph.models.source import Source

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner

INSTRUCTIONS = (
    " The custodian supplies verified commitments for the earlier isolation, documentary and blind gates. "
    "Review the science and precommit controls here. Acceptance at this stage recommends the control plan; "
    "it does not claim the controls were observed, replay ran, or the owner admitted a family. The controller "
    "requires those independent controls and final zero-provider replay separately before a technical dossier. "
    "Preserve substantive limitations even when the available science supports progression."
)


def prior_gates(runner: "SessionRunner") -> dict[str, Any]:
    """Report only the actual completed transitions before contrast disclosure."""
    expected = ("author", "realism", "freeze", "blind", "adjudicate")
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    transitions = {
        row["name"]: row for row in events if row["revision"] == runner.revision
        and row["kind"] == "transition" and row["name"] in expected
    }
    ordered = [transitions[name] for name in expected]
    if [row["sequence"] for row in ordered] != sorted(row["sequence"] for row in ordered):
        raise ValueError("Scientific audit requires properly ordered, exact completed prior gates.")
    return {
        row["name"]: {
            "gate": row["details"]["gate"], "outputs": row["details"]["outputs"],
            "receipts": [receipt["receipt_sha256"] for receipt in row["details"]["sessions"]],
        }
        for row in ordered
    }


RECHECK = "audit-recheck"
RECHECK_INSTRUCTIONS = (
    " Reassess the retained independent audit objections from the same frozen inputs. The previous review did not "
    "qualify the family. Address each substantive objection. Retain the exact valid planned controls and compatible "
    "expectations. For any listed whole-file assignment that could not be rendered as a mask, retain its neutral "
    "question and expectations using an independently justified targeted view. Independently assess the exact additional "
    "excerpt requests and include each warranted request in excerpt_controls. Return if they fail scientific review."
)


class ExactExcerpt(MaskAssignment):
    retained_quotes: dict[SourceId, Text]


class RecheckedAudit(MilestoneAudit):
    excerpt_controls: list[ExactExcerpt]


def render_excerpt(view: ExactExcerpt, sources: list[Source]) -> list[Source]:
    by_id = {source.id: source for source in sources}
    if (len(view.included) != len(set(view.included)) or set(view.included) != view.retained_quotes.keys()
            or not view.retained_quotes.keys() <= by_id.keys() or view.remove_quotes
            or not (view.present or view.absent) or set(view.present) & set(view.absent)
            or any(edge != _edge(*edge) for edge in [*view.present, *view.absent])):
        raise ValueError("An excerpt control requires a nonempty exact Source selection and distinct expectations.")
    result = []
    for source in sources:
        quote = view.retained_quotes.get(source.id)
        if quote is None:
            continue
        if source.text.count(quote) != 1:
            raise ValueError("A retained excerpt must occur exactly once in the specified frozen Source.")
        result.append(Source(id=source.id, title="Evidence excerpt", text=quote))
    return result


def release(runner: "SessionRunner") -> dict[str, Any] | None:
    return next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if row["revision"] == runner.revision and row["kind"] == "reconcile" and row["name"] == RECHECK), None)


def returned_audit(runner: "SessionRunner", record: dict[str, Any]) -> MilestoneAudit:
    joint_plan = record.get("incomplete_joint_control_plan") is True
    original_job = "audit" + repair_authority.FORMAT_RETRY if joint_plan else "audit"
    output_type = RecheckedAudit if joint_plan else MilestoneAudit
    original, receipt, _ = runner.committed_result("audit", original_job, "audit", output_type)
    accepted_format = (original.verdict == "accept" and (
        (not original.objections and (record.get("unrenderable_control_plan") is True or joint_plan))
        or (original.objections and record.get("ambiguous_acceptance") is True)
    ))
    returned = original.verdict in {"repair", "return"} and bool(original.objections)
    fictional_dispatch = (original.verdict == "quarantine" and bool(original.objections)
                          and record.get("fictional_dispatch_only") is True)
    if (not runner.ledger.requires_delivery_attestation or not (returned or accepted_format or fictional_dispatch)
            or receipt["receipt_sha256"] != record["receipt_sha256"]
            or commissioning.digest(artifacts.read_bytes(runner.directory / "family" / "freeze.json"))
            != record["freeze_sha256"]):
        raise ValueError("The fresh audit must bind an actual repair request and the same frozen conditions.")
    return original


def original_views(
    audit: MilestoneAudit, bundles: dict[str, list[Source]],
) -> tuple[MilestoneAudit, list[MaskAssignment]]:
    valid, whole = [], []
    for mask in audit.masks:
        sources = bundles[mask.condition]
        if (len(mask.included) == len(sources) and set(mask.included) == {row.id for row in sources}
                and not mask.remove_quotes and mask.risk != "joint_proof"):
            whole.append(mask)
        else:
            science.mask_sources(mask, sources)
            valid.append(mask)
    return audit.model_copy(update={"masks": valid}), whole


def verify_recheck(
    result: RecheckedAudit, valid: MilestoneAudit, whole: list[MaskAssignment],
    requested: list[ExactExcerpt], bundles: dict[str, list[Source]],
) -> None:
    from benchmark_v3.batch import evidence_recovery

    evidence_recovery.verify_controls(valid, result)
    for old in whole:
        sources = bundles[old.condition]
        is_full_file_confirmation = large_confirmation(old, sources)
        if not any((mask.risk, mask.condition, mask.question) == (old.risk, old.condition, old.question)
                   and set(old.present) <= set(mask.present) and set(old.absent) <= set(mask.absent)
                   and (is_full_file_confirmation or not large_confirmation(mask, sources))
                   for mask in result.masks):
            raise ValueError("A retained whole-file objective needs a conforming control with compatible expectations.")
    approved = {(view.condition, evidence_recovery.observation_key(view, render_excerpt(view, bundles[view.condition])))
                for view in result.excerpt_controls}
    for view in requested:
        if (view.condition, evidence_recovery.observation_key(view, render_excerpt(view, bundles[view.condition]))) not in approved:
            raise ValueError("The fresh scientific audit did not retain an exact requested quotation control.")


FORMAT_RETRY = "audit-recheck-representation"
ACCEPTANCE_FORMAT_ERROR = "Acceptance requires resolved objections and targeted independent masks for every risk."


def retry_instructions(runner: "SessionRunner") -> str:
    record = release(runner)
    if record is None:
        raise ValueError("An audit representation retry needs the exact original audit recheck release.")
    original = returned_audit(runner, record)
    return (
        " For verdict accept, objections must be an empty array. Put answers to earlier objections in summary and "
        "findings. Put residual limitations and later technical gates in limitations. Return a non-accept verdict "
        "if any current scientific objection remains. Preserve each valid exact control and all its present and absent "
        "edges, including absent non-keyed relationships. The original independent precommitments to retain are "
        + commissioning.json_text([mask.model_dump(mode="json") for mask in original.masks])
    )


EXACT_CONTROL_CONTEXT = (
    " The retained valid masks include all independently proposed present and absent relationships. "
    "Assess the proof independently and retain each commitment. Return if an original control is scientifically invalid. "
    "Use the commissioned workload to determine whether a matched contrast exists."
)


ACCEPTANCE_LAYOUT = (
    " If verdict is accept, return an empty objections array. Put resolved issues in findings and remaining "
    "nonblocking limitations in limitations. If any substantive scientific objection remains, return the file."
)


LARGE_CONFIRMATION = "audit-isolated-whole-file-confirmation"
MASK_RENDER_FAILURE = "A targeted mask must remove evidence and precommit distinct edge expectations."
JOINT_PLAN_FAILURE = "Each joint alternative needs an independent sufficient subset and one deletion per Source."


def large_confirmation(mask: MaskAssignment, sources: list[Source]) -> bool:
    """Identify an additional unmodified full-file reading outside targeted-mask coverage."""
    return (mask.risk == "large_or_complex" and len(sources) >= 21
            and len(mask.included) == len(sources) and set(mask.included) == {row.id for row in sources}
            and not mask.remove_quotes and bool(mask.present or mask.absent)
            and not set(mask.present) & set(mask.absent)
            and all(edge == _edge(*edge) for edge in [*mask.present, *mask.absent]))


def targeted_audit(
    audit: MilestoneAudit, bundles: dict[str, list[Source]],
) -> MilestoneAudit:
    return audit.model_copy(update={
        "masks": [mask for mask in audit.masks if not large_confirmation(mask, bundles.get(mask.condition, []))],
    })
