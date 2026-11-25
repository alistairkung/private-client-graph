"""Coordinate a family from approved design through an offline technical package."""

import os
from collections.abc import Callable, Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from copy import copy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal, TypeVar

from pydantic import BaseModel

from benchmark_v3 import commissioning, packet, replay
from benchmark_v3.batch import (
    adjudication_contract, adjudication_recovery, annotation_recovery, artifacts, audit_boundary, audit_contract, audit_recovery,
    author_context, author_delivery, author_repair, authorisation, autonomous_realism, clean_redesign, construction, continuation,
    design_recovery,
    design_review, evidence_recovery, frozen_rekey, joint_control_plan, milestone_repair, read_format_recovery, repair_authority, science,
)
from benchmark_v3.batch.contracts import (
    Adjudication, AuditReview, AuthorBrief, AuthoredSource, Code, DesignOutput, MaskAssignment, Reading, RealismReview,
    MilestoneEvidenceRepair, MilestoneAudit, RecoveredAuditReview, Role, Stage,
)
from benchmark_v3.batch import large_merits_repair
from benchmark_v3.batch.ledger import Ledger
from benchmark_v3.batch.sessions import Blocked, SessionRunner
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.replay_manifest import BatchFamilyManifest, BatchSourceFreeze, SavedIdeal, load_family
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.source import Source
from private_client_graph.workbench.artifacts import artifact_digest

_T = TypeVar("_T", bound=BaseModel)
_POSSESSION_CONTEXT = (
    " The possession ledger's received field lists selected earlier author-context records. "
    "Use documentary covers, receipts and provenance to assess the actual enclosure inventory. "
    "Assess inconsistencies between what participants knew, held and actually delivered."
)
_KEY_ROSTER_CONTEXT = (
    " Record the complete condition-local roster of clearly identified named people and trusts, including names "
    "without a supported relationship. Do not infer relationships from roster membership. Use canonical endpoint "
    "names in sufficient_evidence edge triples and use local IDs only where the truth graph fields request them."
)


class FamilyWorkflow:
    def __init__(self, runner: SessionRunner, slot: FamilySlot, admission_criteria: list[str]):
        self.runner = runner
        self.slot = slot
        self.admission_criteria = admission_criteria
        self.directory = runner.directory
        self.stage: Stage = "design"
        self.sessions: list[dict[str, Any]] = []
        self.repair_tickets: dict[str, str] = {}
        self.retained_authored_sources: dict[str, Source] = {}
        self.realism_release = autonomous_realism.release_event(runner)
        self.documentary_revision: autonomous_realism.Revision | None = None
        self.large_merits_required = False
        self.audit_recovery = audit_recovery.recorded(runner)
        self.frozen_release = frozen_rekey.recorded(runner)
        self.frozen_case: frozen_rekey.ReopenedCase | None = None
        self.release = continuation.recorded(runner)
        self.evidence_release = next((
            row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
            if row["revision"] == runner.revision and row["kind"] == "transition"
            and row["name"] == evidence_recovery.RELEASE
        ), None)
        self.recovered_evidence: evidence_recovery.RecoveredEvidence | None = None
        self.author_packets: dict[str, Any] = {}
        self.release_action = self.release["decision"]["release"]["action"] if self.release else None
        self.transition_inputs: dict[str, str] = {
            "hypothesis": slot.hypothesis.hypothesis_sha256,
            "portfolio": runner.manifest.portfolio_sha256,
        }

    def run(self, *, stop_after: Literal["audit", "masks"] | None = None) -> None:
        if self.evidence_release is not None:
            recovered = self.recover_invariant_evidence(self.evidence_release)
            design, bundles, freeze = recovered.design, recovered.bundles, recovered.freeze
            realism, agreements, reviews = recovered.realism, recovered.agreements, recovered.adjudications
        elif self.frozen_release is not None:
            case = self.restore_frozen_case(self.frozen_release)
            design, bundles, freeze = case.design, case.bundles, case.freeze
            realism, agreements = case.realism, case.agreements
            reviews = self.adjudicate(design, bundles, case.readings, agreements)
        else:
            design = self.design()
            natural = self.author(design)
            bundles, freeze = science.freeze_bundles(self.slot, design, natural)
            if self.documentary_revision is not None:
                receipt = autonomous_realism.verify_revision(self.runner, self.slot, self.documentary_revision, bundles)
                self.sessions.append(receipt)
            self.advance("realism", {"natural": _source_array(natural)}, gate="complete authored inventory and matched diff")
            realism = self.realism(design, bundles)
            self.freeze(bundles, freeze)
            readings, agreements = self.blind(design, bundles)
            reviews = self.adjudicate(design, bundles, readings, agreements)
        audit = self.audit(design, bundles, freeze, reviews, agreements)
        if stop_after == "audit":
            return
        masks = self.masks(design, bundles, audit)
        if stop_after == "masks":
            return
        report, manifest = self.technical(freeze, reviews)
        self.dossier(realism, agreements, reviews, audit, masks, report, manifest)

    def restore_frozen_case(self, release: frozen_rekey.FrozenEvidenceReview) -> frozen_rekey.ReopenedCase:
        case = frozen_rekey.reopen(self.runner, self.slot, release)
        self.frozen_case = case
        self.transition_inputs["frozen_evidence_lineage"] = authorisation.commitment(release)
        artifacts.write_json(self.directory / "design.json", case.design.model_dump(mode="json"))
        self.sessions = case.stages["design"]["sessions"]
        self.advance("author", {"design": case.design.model_dump(mode="json")}, gate="exact retained documentary design")
        self.sessions = case.stages["author"]["sessions"]
        self.advance("realism", {"natural": _source_array(case.bundles[case.freeze.natural])},
                     gate="previously reviewed sender-attested Sources")
        self.sessions = case.stages["realism"]["sessions"]
        self.advance("freeze", {"realism": _models(case.realism)}, gate="verified original independent realism")
        self.freeze(case.bundles, case.freeze)
        self.sessions = case.stages["blind"]["sessions"]
        readings = {condition: [reply.model_dump(mode="json") for reply in pair]
                    for condition, pair in case.readings.items()}
        self.advance("adjudicate", {"readings": readings, "agreements": case.agreements},
                     gate="verified original independent condition-local blind readings")
        return case

    def recover_invariant_evidence(self, release: dict[str, Any]) -> evidence_recovery.RecoveredEvidence:
        self.stage = "adjudicate"
        previous = continuation.previous_runner(self.runner)
        plan = MilestoneEvidenceRepair.model_validate(release["plan"])
        recovered = evidence_recovery.derive(previous, self.slot, plan)
        if recovered.plan_sha256 != release["plan_sha256"]:
            raise ValueError("The accepted invariant evidence plan failed its commitment.")
        self.recovered_evidence = recovered
        root = self.directory / "family"
        for condition, sources in recovered.bundles.items():
            artifacts.write_json(root / "sources" / f"{condition}.json", _source_array(sources))
            _locked_key_digest(root, condition, recovered.adjudications[condition].key)
        artifacts.write_json(root / "freeze.json", recovered.freeze.model_dump(mode="json"))
        self.transition_inputs["evidence_repair"] = recovered.plan_sha256
        self.transition_inputs["original_freeze"] = plan.freeze_sha256
        self.advance("audit", {"provisional": _models(recovered.adjudications)},
                     gate="same frozen Sources and graph with reconciled independently approved invariant evidence")
        return recovered

    def job(
        self, key: str, role: Role, inputs: dict[str, str], instructions: str, result_type: type[_T],
        *, output_schema: dict[str, Any] | None = None, validate: Callable[[_T], None] | None = None,
        allow_format_retry: bool = True,
    ) -> _T:
        result, receipt = self.runner.run(
            self.stage, key, role, inputs, instructions, result_type, output_schema=output_schema, validate=validate,
            allow_format_retry=allow_format_retry,
        )
        self.sessions.append(receipt)
        return result

    def advance(self, next_stage: Stage, outputs: Mapping[str, Any], *, gate: str) -> None:
        digests = (
            dict(outputs) if self.stage == "freeze" else
            {label: commissioning.digest(commissioning.json_text(value).encode())
             for label, value in outputs.items()}
        )
        self.record(
            "transition", self.stage, self.stage, next_stage,
            {"inputs": self.transition_inputs, "outputs": digests, "sessions": self.sessions,
             "gate": gate, "role": "batch_coordinator"},
        )
        self.stage = next_stage
        self.transition_inputs = digests
        self.sessions = []

    def record(
        self, kind: str, name: str, previous: str, next_stage: str | None, details: dict[str, Any],
    ) -> None:
        self.runner.ledger.event(
            self.runner.manifest.batch_id, self.runner.family, self.runner.revision,
            kind, name, previous, next_stage, details,
        )

    def design(self, *, recovery_only: bool = False) -> DesignOutput:
        recovery = design_recovery.recorded_cutoff_recovery(self.runner)
        ref = self.slot.hypothesis
        allocation = next(row for row in self.runner.manifest.families if row.family_id == self.slot.family_id)
        brief_repair = author_repair.recorded(self.runner)
        unused_delivery = author_repair.reopen_unused_delivery(self.runner)
        restored_cover = author_repair.reopen_cover_clarification(self.runner)
        cutoff_repair = design_recovery.isolated_cutoff_recovery(self.runner, self.slot)
        replacement = clean_redesign.recorded(self.runner)
        merits_repair = large_merits_repair.recorded(self.runner)
        self.large_merits_required = (self.runner.ledger.requires_workload_merits or merits_repair is not None or
                                      (replacement is not None and replacement.audited_replacement is not None))
        initial_retry = design_recovery.initial_runtime_retry(self.runner)
        sender_repair = author_repair.reopen_empty_sender_repair(self.runner)
        if merits_repair is not None:
            design = large_merits_repair.repair(self, merits_repair)
        elif sender_repair is not None:
            design, self.retained_authored_sources, record = sender_repair
            self.transition_inputs["retained_sender_repair"] = artifacts.write_json(
                self.directory / "sender-repair-lineage.json", record,
            )
        elif cutoff_repair is not None:
            design, receipt, digest = cutoff_repair
            self.sessions.append(receipt)
            self.transition_inputs["assembled_inventory_cutoff"] = digest
        elif unused_delivery is not None:
            design = unused_delivery
        elif restored_cover is not None:
            design = restored_cover
        elif brief_repair is not None:
            design = author_repair.repair(self, brief_repair)
        elif self.realism_release is not None:
            revision, receipt = autonomous_realism.plan_revision(self.runner, self.slot, self.realism_release)
            self.documentary_revision = revision
            self.sessions.append(receipt)
            design = revision.design
            self.repair_tickets = revision.participant_tickets()
            lineage_name = ("repair-budget-lineage.json" if revision.planner_job == repair_authority.BUDGET_PLAN_JOB
                            else "repair-lineage.json")
            self.transition_inputs["repair_lineage"] = artifacts.write_json(
                self.directory / lineage_name, revision.lineage,
            )
        elif allocation.approved_design:
            candidate = construction.load_design(self.runner.ledger.root, self.runner.manifest.batch_id, allocation)
            self.transition_inputs["approved_design"] = allocation.approved_design.design_sha256
            self.transition_inputs["design_lineage"] = allocation.approved_design.lineage_sha256
            design = DesignOutput.model_validate(candidate.model_dump(include=set(DesignOutput.model_fields)))
        elif recovery:
            design, receipt = design_recovery.reopen_cutoff_recovery(self.runner, self.slot, recovery)
            self.sessions.append(receipt)
        elif recovery_only:
            raise ValueError("No owner-authorized Source cut-off recovery was recorded.")
        elif self.release and self.runner.revision > 1:
            design = continuation.released_design(self.runner, self.release)
            self.repair_tickets = self.release.get("repair_tickets", {})
        elif self.runner.revision == 1 or replacement is not None or initial_retry is not None:
            slot = clean_redesign.fresh_slot(self.slot, replacement) if replacement else self.slot

            def verify_design(value: DesignOutput) -> None:
                self._verify_fresh_design(value)
                if replacement is not None:
                    clean_redesign.verify_distinct(self.runner, value, replacement)

            design = self.job(
                "design", "designer", {
                    "hypothesis_revision": f"{ref.hypothesis_id}@{ref.revision}",
                    "portfolio_slot": slot.model_dump_json(),
                },
                "commissioned-designer-batch-v1", DesignOutput,
                validate=verify_design if self.runner.ledger.requires_author_context else None,
            )
            if replacement is not None:
                self.transition_inputs["documentary_redesign"] = authorisation.commitment(replacement)
            if initial_retry is not None:
                self.transition_inputs["initial_design_runtime_retry"] = commissioning.digest(_json(initial_retry).encode())
        else:
            previous = self.directory.parent / str(self.runner.revision - 1)
            design = artifacts.read_contract(previous / "design.json", DesignOutput)
            dispositions = [
                row for row in self.runner.ledger.events(self.runner.manifest.batch_id, self.slot.family_id)
                if row["kind"] == "disposition" and row["revision"] == self.runner.revision - 1
            ]
            self.repair_tickets = (
                milestone_repair.recorded_tickets(self.runner, self.slot) or dispositions[-1]["details"]["repair_tickets"]
            )
            expected = next(row["details"]["outputs"]["design"] for row in self.runner.ledger.events(
                self.runner.manifest.batch_id, self.slot.family_id,
            ) if row["kind"] == "transition" and row["name"] == "design"
                and row["revision"] == self.runner.revision - 1)
            if commissioning.digest(_json(design.model_dump(mode="json")).encode()) != expected:
                raise ValueError("Repair changed the locked design or hypothesis.")
        if self.runner.manifest.phase == "milestone":
            if replacement is not None or initial_retry is not None:
                design = design_recovery.verify_milestone_design(self.runner, self.slot, design, fresh_replacement=True)
            else:
                design = design_recovery.verify_milestone_design(self.runner, self.slot, design)
            self._check_design_capacity(design)
        else:
            science.verify_design(self.slot, design)
        artifacts.write_json(self.directory / "design.json", design.model_dump(mode="json"))
        self.advance("author", {"design": design.model_dump(mode="json")}, gate="approved scope and dated inventory")
        if self.runner.manifest.phase == "milestone" and self.runner.revision == 1:
            return self._reviewed_design(design)
        return design

    def _verify_fresh_design(self, design: DesignOutput) -> None:
        science.verify_design(self.slot, design_recovery.fresh_design_representation(
            design, workload=self.runner.ledger.requires_workload_merits,
        ))
        self._project_authors(design, {})

    def _reviewed_design(self, design: DesignOutput) -> DesignOutput:
        review = design_review.recorded_review(self.runner.ledger, self.runner.manifest, self.runner.owner)
        correction = next((row.name_correction for row in review.designs
                           if row.family_id == self.slot.family_id), None) if review else None
        if correction is None:
            return design
        revised = design_review.apply_name_correction(design, correction)
        self.transition_inputs["design_review_derivative"] = artifacts.write_json(
            self.directory / "reviewed-design.json", revised.model_dump(mode="json"),
        )
        return revised

    def _check_design_capacity(self, design: DesignOutput) -> None:
        revision = self.documentary_revision
        changed: set[str] = set()
        if revision is not None:
            changed = revision.affected
        elif self.retained_authored_sources:
            changed = {brief.source_id for brief in design.inventory} - self.retained_authored_sources.keys()
        else:
            for brief in design.inventory:
                if not self.repair_tickets or brief.source_id in self.repair_tickets or changed.intersection(brief.received):
                    changed.add(brief.source_id)
        jobs = autonomous_realism.mandatory_jobs(design, changed, verification=revision is not None)
        if self.large_merits_required:
            jobs.update({clean_redesign.MERITS_JOB, author_context.JOB})
        self.runner.ledger.require_capacity(self.runner.family, self.runner.revision, jobs)

    def author(self, design: DesignOutput) -> list[Source]:
        if self.large_merits_required:
            self._review_large_workload_merits(design)
        assignments = self._author_assignments(design)
        if self.runner.ledger.requires_author_context:
            self.author_packets = self._review_author_context(
                design, {brief.source_id: ticket for brief, ticket, _, _ in assignments if ticket},
            )
        workers = self.runner.ledger.parallel_scientific_jobs
        if workers > 1:
            return self._author_in_parallel(design, assignments, workers)
        sources: dict[str, Source] = {}
        for brief, ticket, reuse, prior in assignments:
            source = prior or self._author_record(design, brief, ticket, reuse, [sources[key] for key in brief.received])
            sources[brief.source_id] = source
        return list(sources.values())

    def _review_large_workload_merits(self, design: DesignOutput) -> None:
        inventory = {row.source_id for row in design.inventory}
        sequence = (" At this pre-author gate, assess whether the design can support these checks. Actual full-file "
                    "readings, measured packet sizes and the bidirectional audit must be obtained after authorship "
                    "and verified before qualification.")
        if not self._use_scoped_prompt(clean_redesign.MERITS_JOB, sequence):
            sequence = ""
        roster = (" In findings, use exactly the supplied Source IDs as keys. Put a blocking file-level issue "
                  "in objections instead of introducing a case-summary key in findings.")
        if not self._use_scoped_prompt(clean_redesign.MERITS_JOB, roster):
            roster = ""

        def verify_acceptance(review: author_context.AuthorContextReview) -> None:
            if review.verdict == "accept" and not review.objections and review.findings.keys() != inventory:
                raise ValueError("An accepted workload review needs precisely one finding per Source ID.")

        review = self.job(clean_redesign.MERITS_JOB, "audit", {
            "intended_intervention": design.model_dump_json(),
            "audit_rules": _json({"hypothesis": self.slot.hypothesis.model_dump(mode="json"),
                                  "workload": self.slot.expected_sources, "scope": self.slot.natural_condition}),
        }, "Independently assess the new exact large-file design before any participant dispatch. "
           "For every required relationship, trace an organised set of contemporaneous documentary facts "
           "and exact custody paths that could establish every operative premise. A delivery event must "
           "establish the recipient's specific capacity on that date when the instrument requires it. "
           "A later engagement, broad job title or index cannot establish an earlier capacity. Inspect every "
           "planned Source for genuine use, provenance, chronology, required transmission and participant knowledge. "
           "Check ordinary alternative proofs, varied documentary workstreams, exact evidence scope, "
           "unscored sections and prefixes, and two complete independently reviewed lanes. Reject unsupported "
           "historical premises, padding or hidden answers. Return a distinct finding for every Source ID, "
           "with no objections on acceptance. This review is separate from the author-scope gate." + sequence + roster,
           author_context.AuthorContextReview, validate=verify_acceptance)
        if review.verdict != "accept" or review.objections or review.findings.keys() != inventory:
            self.reject("scientific_review", review.model_dump_json(), quarantine=True, disposition=clean_redesign.MERITS_JOB)

    def _project_authors(self, design: DesignOutput, tickets: dict[str, str]) -> dict[str, Any]:
        guard = author_delivery if self.runner.ledger.requires_delivery_attestation else author_context
        return guard.projection(design, tickets)

    def _review_author_context(self, design: DesignOutput, tickets: dict[str, str]) -> dict[str, Any]:
        projected = self._project_authors(design, tickets)
        attested = self.runner.ledger.requires_delivery_attestation
        rules = {"participant_packets": projected, **({"delivery_attestation": 1} if attested else {})}
        policy = " Any flagged local ticket names or periods require actual participant authority before dispatch."
        needs_basis = (attested and self.runner.ledger.requires_workload_merits and self.documentary_revision is not None
                       and self._use_scoped_prompt(author_context.JOB, policy))
        if needs_basis:
            revision = self.documentary_revision
            assert revision is not None
            rules.update(ticket_basis_version=1, unavailable_ticket_literals=autonomous_realism.unavailable_ticket_literals(revision, projected))
        exact_context = ""
        if self.documentary_revision is not None and self.documentary_revision.parent.exact_recipient_edit is not None:
            exact = self.documentary_revision.parent.exact_recipient_edit
            rules["locally_owned_repair"] = exact.model_dump(mode="json", exclude_none=True)
            if exact.brief_omission is None:
                exact_context = (
                    " The independently retained complete draft belongs to this author. The revised copy changes"
                    " one entry to reflect the contemporaneous counterpart they actually received. Check the exact"
                    " author, attachment and direct delivery. Return on any new fact, possession, transmission or cue."
                )
            else:
                exact_context = (
                    " One exact repair revises a dated inventory the same participant previously authored. Review the"
                    " candidate text as their own earlier record with the documented omissions and label correction."
                    " Reject new facts, new possession, new transmissions or cues to a scientific answer."
                )
            if self.documentary_revision.lineage.get("exact_omission_assessment"):
                exact_context += (
                    " The two authorised documentary edits revise the retained intake scope. The"
                    " original tally instruction and corresponding paragraph are deliberately omitted from this"
                    " newly authored version. Decide independently whether the omission loses any required"
                    " intake fact, receipt or enclosure status. Check the original sender evidence and dates"
                    " independently for every actual attachment. Return on any remaining material objection."
                )
        delivery_scope = (author_repair.SELECTED_DELIVERY_SCOPE if attested and
                          self._use_scoped_prompt(author_context.JOB, author_repair.SELECTED_DELIVERY_SCOPE) else "")
        origin_scope = (
            " A claimed personal worksheet that reproduces the case-wide file needs separately documented local"
            " origin. Reject a brief that imports the full inventory or other participants' records merely by"
            " calling them personal notes. Identify exact observed facts or authenticated deliveries."
        )
        if not attested or not self._use_scoped_prompt(author_context.JOB, origin_scope):
            origin_scope = ""
        review = self.job(author_context.JOB, "audit", {
            "intended_intervention": design.model_dump_json(),
            "audit_rules": _json(rules),
        }, "Independently audit every exact proposed participant packet before any author is called. "
           "Check participant and date, what they personally know, and each declared earlier delivery against "
           "the chronology and origin. Inspect nested text and tickets for references to future or unavailable "
           "documents, case-wide summaries, alternate conditions, hidden answers or intended proof routes. "
           "The participant's own act or observation may be documented in ordinary wording. Check that other "
           "people's knowledge and experimental reasoning stay out. Return on any material objection. "
           "Give one finding keyed to every Source ID."
           + (" " + author_delivery.REVIEW_INSTRUCTION if attested else "") + delivery_scope + origin_scope + exact_context
           + (policy if needs_basis else ""),
           author_context.AuthorContextReview)
        if (review.verdict != "accept" or review.objections or rules.get("unavailable_ticket_literals")
                or review.findings.keys() != projected.keys()):
            self.reject("scientific_review", review.model_dump_json(), quarantine=True)
        return projected

    def _author_assignments(self, design: DesignOutput) -> list[tuple[AuthorBrief, str | None, bool, Source | None]]:
        assignments: list[tuple[AuthorBrief, str | None, bool, Source | None]] = []
        changed: set[str] = set()
        tickets = self.repair_tickets
        if not tickets.keys() <= {brief.source_id for brief in design.inventory}:
            raise ValueError("Repair tickets must identify known Sources.")
        revision = self.documentary_revision
        scoped = revision is not None and self.runner.ledger.requires_delivery_attestation
        if revision is not None and scoped:
            tickets = autonomous_realism.retained_draft_tickets(self.runner, revision, tickets)
        retained_tickets = self._retained_generated_tickets() if scoped else {}
        prior_sources = ({source.id: source for source in revision.parent.bundles[revision.parent.freeze.natural]}
                         if revision is not None else {})
        for brief in design.inventory:
            if prior := self.retained_authored_sources.get(brief.source_id):
                assignments.append((brief, None, False, prior))
                continue
            if revision is not None and brief.source_id not in revision.affected:
                assignments.append((brief, None, False, prior_sources[brief.source_id]))
                continue
            ticket = tickets.get(brief.source_id)
            if scoped:
                assignments.append((brief, ticket or retained_tickets.get(brief.source_id), False, None))
                continue
            if ticket is None and changed.intersection(brief.received):
                ticket = repair_authority.LEGACY_REVISED_ATTACHMENTS
            if ticket:
                changed.add(brief.source_id)
            if revision is not None and ticket is None:
                ticket = repair_authority.LEGACY_REVISED_CONTEXT
            assignments.append((brief, ticket, revision is None and bool(tickets) and ticket is None, None))
        return assignments

    def _retained_generated_tickets(self) -> dict[str, str]:
        """Preserve exact historic packets while fresh authors use their documented attachments."""
        attempt = next((row for row in self.runner.ledger.attempts(self.runner.family)
                        if row["revision"] == self.runner.revision and row["job"] == author_context.JOB), None)
        if attempt is None:
            return {}
        request = commissioning._read_json(attempt["request"])
        projections = commissioning._read_json(request["inputs"]["audit_rules"])["participant_packets"]
        generated = {repair_authority.LEGACY_REVISED_ATTACHMENTS, repair_authority.LEGACY_REVISED_INSTRUCTIONS,
                     repair_authority.LEGACY_REVISED_CONTEXT}
        return {identity: row["revision_ticket"] for identity, row in projections.items()
                if row.get("revision_ticket") in generated}

    def _author_record(self, design: DesignOutput, brief: AuthorBrief, ticket: str | None, reuse: bool,
                       received: list[Source]) -> Source:
        inputs = {
            "author_brief": _json({
                "participant": brief.author, "date": brief.created_on.isoformat(), "brief": brief.participant_brief,
            }),
            "received_correspondence": _json(_source_array(received)),
        }
        if self.runner.ledger.requires_delivery_attestation:
            inputs["author_brief"] = self.author_packets[brief.source_id]["author_brief"]
        if ticket:
            inputs["revision_ticket"] = ticket
        result = self.authored(brief.source_id, inputs, reuse=reuse, design=design)
        return Source(id=brief.source_id, title=result.title, text=result.text)

    def _author_in_parallel(
        self, design: DesignOutput, assignments: list[tuple[AuthorBrief, str | None, bool, Source | None]], workers: int,
    ) -> list[Source]:
        def produce(brief: AuthorBrief, ticket: str | None, reuse: bool,
                    deliveries: list[Future[tuple[Source, list[dict[str, Any]]]]],
                    ) -> tuple[Source, list[dict[str, Any]]]:
            # Each author sees only the declared deliveries and keeps a local receipt list.
            received = [task.result()[0] for task in deliveries]
            worker = copy(self)
            worker.sessions = []
            return worker._author_record(design, brief, ticket, reuse, received), worker.sessions

        jobs: dict[str, Future[tuple[Source, list[dict[str, Any]]]]] = {}
        sources = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for brief, ticket, reuse, prior in assignments:
                if prior is None:
                    job = executor.submit(produce, brief, ticket, reuse, [jobs[key] for key in brief.received])
                else:
                    job = Future()
                    job.set_result((prior, []))
                jobs[brief.source_id] = job
            for job in jobs.values():
                source, receipts = job.result()
                sources.append(source)
                self.sessions.extend(receipts)
        return sources

    def authored(self, identity: str, inputs: dict[str, str], *, reuse: bool, design: DesignOutput) -> AuthoredSource:
        name = f"author-{identity}"
        if reuse:
            original = continuation.previous_runner(self.runner)
            content, _, request = original.committed_packet("author", name, "author")
            if request["inputs"] != inputs:
                raise ValueError("An unaffected author packet changed before repair.")
            return AuthoredSource.model_validate(commissioning._read_json(content))
        literals = [control.edit.before for control in design.matched if control.edit and control.edit.source_id == identity]

        def verify_literals(source: AuthoredSource) -> None:
            if any(source.text.count(literal) != 1 for literal in literals):
                raise ValueError("An assigned exact body literal must occur exactly once.")

        if self.runner.ledger.requires_delivery_attestation:
            expected = self.documentary_revision.parent.expected_local_source() if self.documentary_revision else None
            if self.documentary_revision is not None:
                parent = self.documentary_revision.parent
                intake = parent.incoming_particulars
                if parent.owned_records is not None and intake is not None and identity != intake.source_id:
                    expected = parent.owned_records.get(identity)

            def verify_source(source: author_delivery.AttestedSource) -> None:
                verify_literals(source)
                if (expected is not None and expected.id == identity
                        and (source.title, source.text) != (expected.title, expected.text)):
                    raise ValueError("The scoped recipient repair must preserve the exact revised title and complete text.")
                if not author_repair.unused_attestation(self.runner, identity, design):
                    author_delivery.verify_attestation(source, inputs["author_brief"])

            return self.job(name, "author", inputs, author_delivery.INSTRUCTIONS, author_delivery.AttestedSource,
                            validate=verify_source)
        return self.job(
            name, "author", inputs, author_context.INSTRUCTIONS, AuthoredSource,
            validate=verify_literals if self._validates_documentary_outputs() else None,
        )

    def realism(self, design: DesignOutput, bundles: dict[str, list[Source]]) -> dict[str, RealismReview]:
        result = {}
        for index, (condition, sources) in enumerate(bundles.items()):
            inventory = {source.id for source in sources}

            def verify_inventory(review: RealismReview) -> None:
                if review.source_findings.keys() != inventory or not review.repair_tickets.keys() <= inventory:
                    raise ValueError("Documentary realism must assess every Source and target only supplied records.")

            job = f"realism-{index:03}"
            instructions = ("Review documentary realism independently. Assess purpose, possession, chronology, form, "
                            "density and cues. Supply a source_findings entry for each Source ID. If repair is needed, "
                            "return participant-safe documentary repair tickets keyed by Source ID and describe objections.")
            if self._use_scoped_prompt(job, _POSSESSION_CONTEXT):
                instructions += _POSSESSION_CONTEXT
            review = self.job(
                job, "realism",
                {
                    "sources": _json(_source_array(sources)), "neutral_brief": design.neutral_brief,
                    "cutoff": design.cutoff.isoformat(),
                    "possession_ledger": _json([
                        {"id": row.source_id, "date": row.created_on.isoformat(), "provenance": row.provenance,
                         "received": row.received} for row in design.inventory
                    ]),
                    "genre_references": _json(design.documentary_references),
                },
                instructions, RealismReview,
                validate=verify_inventory if self._validates_documentary_outputs() else None,
            )
            if review.source_findings.keys() != {source.id for source in sources}:
                raise ValueError("Documentary realism must assess every Source.")
            result[condition] = review
        failed = [review for review in result.values() if review.verdict != "pass" or review.objections]
        if failed:
            tickets: dict[str, str] = {}
            natural = next(iter(result.values()))
            if failed == [natural] and natural.verdict == "repair":
                tickets = natural.repair_tickets
            self.reject("documentary_realism", _json(_models(result)), repair_tickets=tickets)
        self.advance("freeze", {"realism": _models(result)}, gate="independent realism for every condition")
        return result

    def _use_scoped_prompt(self, job: str, addition: str) -> bool:
        if self.runner.ledger.parallel_scientific_jobs <= 1 and not self.runner.ledger.requires_delivery_attestation:
            return False
        for attempt in self.runner.ledger.attempts(self.runner.family):
            if attempt["revision"] == self.runner.revision and attempt["job"] == job:
                return addition in commissioning._read_json(attempt["request"])["prompt"]
        return True

    def _validates_documentary_outputs(self) -> bool:
        return self.realism_release is not None or repair_authority.enabled(self.runner.ledger, self.runner.manifest)

    def freeze(self, bundles: dict[str, list[Source]], freeze: BatchSourceFreeze) -> None:
        root = self.directory / "family"
        files = {
            f"sources/{condition}.json": artifacts.write_json(
                root / "sources" / f"{condition}.json", _source_array(sources),
            ) for condition, sources in bundles.items()
        }
        files["freeze.json"] = artifacts.write_json(root / "freeze.json", freeze.model_dump(mode="json"))
        self.advance("blind", files, gate="ordered Source bytes and precommitted matched controls locked")

    def blind(
        self, design: DesignOutput, bundles: dict[str, list[Source]],
    ) -> tuple[dict[str, tuple[Reading, Reading]], dict[str, dict[str, Any]]]:
        readings = {}
        agreements = {}
        for index, (condition, sources) in enumerate(bundles.items()):
            first, second = self._condition_readers(index, design, sources)
            readings[condition] = first, second
            agreements[condition] = science.compare_readings(first, second, sources)
        persisted = {condition: [reply.model_dump(mode="json") for reply in pair]
                     for condition, pair in readings.items()}
        self.advance("adjudicate", {"readings": persisted, "agreements": agreements},
                     gate="two separately isolated full-file readings per frozen condition")
        return readings, agreements

    def _condition_readers(self, index: int, design: DesignOutput, sources: list[Source]) -> tuple[Reading, Reading]:
        keys = (f"{index:03}-a", f"{index:03}-b")
        if self.runner.ledger.parallel_scientific_jobs <= 1:
            first, second = keys
            return self.reader(first, design, sources), self.reader(second, design, sources)

        def read_independently(key: str) -> tuple[Reading, list[dict[str, Any]]]:
            worker = copy(self)
            worker.sessions = []
            return worker.reader(key, design, sources), worker.sessions

        with ThreadPoolExecutor(max_workers=2) as executor:
            (first_reading, first_receipts), (second_reading, second_receipts) = executor.map(read_independently, keys)
        self.sessions.extend(first_receipts + second_receipts)
        return first_reading, second_reading

    def reader(self, key: str, design: DesignOutput, sources: list[Source]) -> Reading:
        parts = []
        for index, ids in enumerate(design.sections.values()):
            section = [source for source in sources if source.id in ids]
            parts.append(self.read(f"reading-{key}-part-{index:03}", "annotation", design, section).model_dump(mode="json"))
        extra = {"section_readings": _json(parts)} if parts else {}
        return self.read(f"reading-{key}-full", "annotation", design, sources, extra)

    def read(
        self, key: str, role: Role, design: DesignOutput, sources: list[Source],
        extra: dict[str, str] | None = None,
    ) -> Reading:
        recovery = annotation_recovery.recorded(self.runner) if role == "annotation" else None
        if recovery and recovery["decision"]["reader_job"] == key:
            try:
                reading, receipt = annotation_recovery.reopen(self.runner, recovery)
            except packet.PacketIsolationError as error:
                raise Blocked(self.stage, "isolation", str(error), job=key) from error
            except (ValueError, OSError, KeyError, TypeError) as error:
                raise Blocked(self.stage, "input_integrity", str(error), job=key) from error
            self.sessions.append(receipt)
            return reading
        extra_instructions = audit_recovery.MASK_INSTRUCTIONS if role == "masked" and self.audit_recovery else ""
        inputs = _reading_inputs(design, sources) | (extra or {})
        job = key
        if self.runner.ledger.requires_delivery_attestation:
            if role == "annotation" or role == "masked":
                derived = read_format_recovery.reopen_whitespace(self.runner, key, inputs, role=role)
                if derived is not None:
                    reading, receipt = derived
                    self.sessions.append(receipt)
                    return reading
                job = read_format_recovery.selected_job(self.runner, key, inputs, role=role)
            if self._use_scoped_prompt(job, read_format_recovery.INSTRUCTIONS):
                extra_instructions += read_format_recovery.INSTRUCTIONS

        def verify_mechanical_evidence(reading: Reading) -> None:
            by_id = {source.id: source.text for source in sources}
            if len(reading.reviewed_sources) != len(by_id) or set(reading.reviewed_sources) != by_id.keys():
                raise ValueError(read_format_recovery.INVENTORY_ERROR)
            for candidate in reading.candidates.relationships:
                if candidate.source_id not in by_id or candidate.supporting_text not in by_id[candidate.source_id]:
                    raise ValueError(read_format_recovery.QUOTE_ERROR)

        result = self.job(
            job, role, inputs,
            "Read only the supplied file. Record exact sourced candidates, unresolved questions, and "
            "each reviewed Source ID. Where your own sectional readings are supplied, independently "
            "reconcile identities, supersession and cross-section claims against every full Source." + extra_instructions,
            Reading, validate=verify_mechanical_evidence if self._validates_documentary_outputs() else None,
            allow_format_retry=job == key,
        )
        science.check_reading(result, sources)
        return result

    def adjudicate(
        self, design: DesignOutput, bundles: dict[str, list[Source]],
        readings: dict[str, tuple[Reading, Reading]], agreements: dict[str, dict[str, Any]],
    ) -> dict[str, Adjudication]:
        result = {}
        for index, (condition, sources) in enumerate(bundles.items()):
            first, second = readings[condition]
            review = self._adjudicate_condition(index, design, sources, first, second, agreements[condition])
            if review.key.condition != "local":
                raise ValueError("Adjudication must return a condition-local provisional key.")
            review = review.model_copy(update={"key": review.key.model_copy(update={"condition": condition})})
            science.verify_adjudication(condition, review, sources, agreements[condition])
            if self.frozen_case is not None:
                frozen_rekey.verify_same_semantics(review, self.frozen_case.locked[condition])
            result[condition] = review
            artifacts.write_json(self.directory / "family" / f"{condition}.json", review.key.model_dump(mode="json"))
        self.advance("audit", {"provisional": _models(result)}, gate="all condition-local keys locked before disclosure")
        return result

    def _adjudicate_condition(
        self, index: int, design: DesignOutput, sources: list[Source], first: Reading, second: Reading,
        agreement: dict[str, Any],
    ) -> Adjudication:
        recovery = adjudication_recovery.recorded(self.runner)
        if recovery is not None:
            if index != 0:
                raise ValueError("The mechanical adjudication recovery is limited to condition zero.")
            try:
                review, receipt = adjudication_recovery.reopen(self.runner, recovery)
            except packet.PacketIsolationError as error:
                raise Blocked(self.stage, "isolation", str(error)) from error
            except (ValueError, OSError, KeyError, TypeError) as error:
                raise Blocked(self.stage, "input_integrity", str(error)) from error
            self.sessions.append(receipt)
            return review
        inputs = _reading_inputs(design, sources) | {
            "annotation_a": first.model_dump_json(), "annotation_b": second.model_dump_json(),
        }
        prompt = (
            "Commit one provisional complete key for this file alone. Set key.condition to 'local'. "
            "Account for every Source. Explain all edge and evidence disagreements with canonical "
            "JSON arrays of [source name, relationship type, target name] as resolution-map keys. "
            "Use compact JSON without spaces and sort names for symmetric edges."
        )
        job = f"adjudicate-{index:03}"
        if not self.release and self.runner.manifest.phase != "milestone" and self.realism_release is None:
            return self.job(job, "adjudication", inputs, prompt, Adjudication)
        ids = adjudication_contract.resolution_ids(agreement["disagreements"])
        released_job = adjudication_contract.RELEASE_JOBS.get(self.release_action or "")
        if released_job:
            if self.release is None or index != 0 or ids != self.release["resolution_ids"]:
                raise ValueError("The actual disputes differ from the owner-bound adjudication preflight.")
            job = released_job
        prompt += (
            " The required properties of disagreement_resolutions are exactly the disputed IDs. "
            "Use unresolved for remaining scientific objections to the provisional key. "
            "Include ordinary practitioner follow-up in the relevant source_audit entry."
        )
        complete = (self.runner.manifest.phase == "milestone" or self.realism_release is not None
                    or self.release_action == "complete_evidence_adjudication")
        if complete:
            prompt += adjudication_contract.COMPLETE_EVIDENCE_INSTRUCTIONS
        if self.frozen_case is not None:
            prompt += frozen_rekey.POLICY
        proof_retry = adjudication_contract.proof_retry(self.runner, job)
        if proof_retry is not None:
            _, receipt, previous = self.runner.committed_packet("adjudicate", job, "adjudication")
            if previous["inputs"] != inputs or receipt["receipt_sha256"] != proof_retry["receipt_sha256"]:
                raise ValueError("An independent proof retry requires the exact prior blind inputs and receipt.")
            self.transition_inputs[f"{job}_proof_retry"] = commissioning.digest(_json(proof_retry).encode())
            job += "-complete-proof"
            prompt += (
                " Verify each sufficient alternative against the literal Source text. Attach every exact Source ID "
                "and verbatim text pair from at least one complete approved alternative, including all pairs from "
                "a multi-quote single Source. Reconstruct and assess the proof independently."
            )
        if self._use_scoped_prompt(job, _KEY_ROSTER_CONTEXT):
            prompt += _KEY_ROSTER_CONTEXT
        if (self.runner.ledger.requires_delivery_attestation
                and self._use_scoped_prompt(job, adjudication_contract.LOCAL_APPROVAL_IDS)):
            prompt += adjudication_contract.LOCAL_APPROVAL_IDS
        if (self.runner.ledger.requires_delivery_attestation
                and self._use_scoped_prompt(job, adjudication_contract.TRUTH_QUOTATIONS)):
            prompt += adjudication_contract.TRUTH_QUOTATIONS
        review = self.job(
            job, "adjudication", inputs, prompt, Adjudication,
            output_schema=adjudication_contract.output_schema(ids, complete_evidence=complete),
            allow_format_retry=proof_retry is None,
        )
        quotation = adjudication_contract.quote_recovery(self.runner, job)
        if quotation is not None:
            original, receipt, request = self.runner.committed_result("adjudicate", job, "adjudication", Adjudication)
            derivative, changes = adjudication_contract.exact_whitespace_key(original, sources)
            if (original != review or inputs != request["inputs"] or receipt["receipt_sha256"] != quotation["receipt_sha256"]
                    or authorisation.commitment(derivative) != quotation["derivative_sha256"] or changes != quotation["edits"]):
                raise packet.PacketIsolationError("The exact adjudication quotation derivative differs from its receipt.")
            self.transition_inputs[f"{job}_exact_quotes"] = commissioning.digest(_json(quotation).encode())
            review = derivative
        if self.runner.ledger.requires_delivery_attestation and not review.unresolved:
            review = self._localize_approval_ids(job, review)
        return review

    def _localize_approval_ids(self, job: str, original: Adjudication) -> Adjudication:
        review, edits = adjudication_contract.localize_key_presentation(original)
        if edits:
            retained, receipt, _ = self.runner.committed_result("adjudicate", job, "adjudication", Adjudication)
            if original != retained:
                raise ValueError("The local-ID derivative requires the exact adjudicated output.")
            commitment = artifacts.write_json(self.directory / "recoveries" / job / "local-approval-ids.json", {
                "receipt_sha256": receipt["receipt_sha256"],
                "output_sha256": receipt["output_sha256"],
                "derivative_sha256": authorisation.commitment(review),
                "changes": edits,
            })
            self.transition_inputs[f"{job}_local_approval_ids"] = commitment
        return review

    def audit(
        self, design: DesignOutput, bundles: dict[str, list[Source]], freeze: BatchSourceFreeze,
        reviews: dict[str, Adjudication], agreements: dict[str, dict[str, Any]],
    ) -> AuditReview:
        required = science.audit_risks(self.slot, reviews, agreements)
        completion = joint_control_plan.released(self.runner)
        if completion is not None:
            return self.confirm_joint_plan(design, bundles, freeze, reviews, required, completion)
        prompt = (
            "Audit each Source for ground-truth completeness and each critical edge for evidence "
            "necessity and sufficiency. Key sufficiency by compact JSON edge array. Check negative "
            "controls, material differences and shortcuts for every condition, including the natural file. "
            "Classify all applicable risks. For each triggered risk, precommit masked independent "
            "questions with a rationale, Source subset or exact deletions, and expected present/absent edges. "
            "Cover joint proofs with sufficient-subset and proper-deletion readings. State limitations. "
            "Apply the supplied admission and stopping criteria. Recommend accept only if all scientific "
            "objections are resolved."
        )
        rules: dict[str, Any] = {
            "mandatory_risks": sorted(required), "blind_agreement": agreements,
            "portfolio_admission_criteria": self.admission_criteria,
            "batch_stop_conditions": self.runner.manifest.stop_conditions,
        }
        job = "audit"
        schema = None
        result_type: type[AuditReview] = AuditReview
        if self.audit_recovery is not None:
            job = audit_recovery.JOB
            audit_recovery.verify_authority(self.runner, self.audit_recovery)
            rules.update(audit_recovery.rules(self.audit_recovery))
            rules["verified_prior_gates"] = [
                "Condition-local documentary realism passed.",
                "The frozen bundle preceded two separate full-file blind readings.",
                "The provisional key was fully validated before this audit.",
            ]
            prompt += audit_recovery.INSTRUCTIONS
            result_type = RecoveredAuditReview
        recheck = audit_boundary.release(self.runner) if self.runner.ledger.requires_delivery_attestation else None
        if recheck is not None:
            job = audit_boundary.RECHECK
        reserved_prompt = self._reserved_audit_prompt(job) if recheck is not None else self._reserved_audit_prompt()
        if (self.runner.ledger.requires_delivery_attestation
                and (reserved_prompt is None or audit_boundary.INSTRUCTIONS in reserved_prompt)):
            rules["verified_prior_gates"] = audit_boundary.prior_gates(self.runner)
            prompt += audit_boundary.INSTRUCTIONS
        if self.runner.manifest.phase == "milestone" and (
            reserved_prompt is None or evidence_recovery.MASK_EQUIVALENCE_INSTRUCTIONS in reserved_prompt
        ):
            prompt += evidence_recovery.MASK_EQUIVALENCE_INSTRUCTIONS
            result_type = MilestoneAudit
        valid = None
        requested: list[audit_boundary.ExactExcerpt] = []
        whole: list[MaskAssignment] = []
        if recheck is not None or self.frozen_case is not None:
            if recheck is not None:
                original = audit_boundary.returned_audit(self.runner, recheck)
                requested = [audit_boundary.ExactExcerpt.model_validate(row) for row in recheck["excerpt_controls"]]
                if recheck.get("mask_quote_repairs"):
                    rules["mechanical_mask_quote_repairs"] = recheck["mask_quote_repairs"]
            else:
                assert self.frozen_case is not None
                original = self.frozen_case.audit
                if isinstance(original, audit_boundary.RecheckedAudit):
                    requested = original.excerpt_controls
                prompt += " Independently audit the fresh condition-local evidence keys on the exact retained freeze."
            if recheck is not None and recheck.get("incomplete_joint_control_plan") is True:
                assert self.frozen_case is not None
                previous = self.frozen_case.audit
                combined = {authorisation.commitment(view): view for view in [*previous.masks, *original.masks]}
                original = original.model_copy(update={"masks": list(combined.values()),
                                                       "objections": [*previous.objections, *original.objections]})
                rules["joint_proof_obligations"] = {
                    condition: [proof.model_dump(mode="json") for proof in review.key.sufficient_evidence
                                if any(len({quote.source_id for quote in alternative}) > 1
                                       for alternative in proof.alternatives)]
                    for condition, review in reviews.items()
                }
                prompt += (
                    " Independently verify each exact retained joint proof. Precommit an isolated sufficient subset "
                    "for each alternative, including all its exact quotations, and an independently assessed "
                    "proper-deletion view for each necessary Source. The explicit obligation table identifies "
                    "every committed sufficient alternative. Retain all previously valid controls and return on "
                    "any scientific disagreement."
                )
            valid, whole = audit_boundary.original_views(original, bundles)
            if recheck is not None and recheck.get("fictional_dispatch_only") is True:
                prompt += (
                    " Separate unresolved real scientific workflow submissions from questions inside the fictional file. "
                    "The former remain subject to integrity quarantine. The retained terminal receipts confirm there is no "
                    "uncertain scientific dispatch. Independently assess the fictional question for realism, confidentiality "
                    "evidence, scientific identifiability and potential effects at the cutoff. Keep all substantiated "
                    "objections and retain ordinary uncertain practitioner follow-up in the findings."
                )
            rules.update({
                "retained_audit_objections": original.objections,
                "retained_valid_controls": evidence_recovery.proposed_views(valid),
                "whole_file_objectives_for_targeted_controls": [view.model_dump(mode="json") for view in whole],
                "independent_excerpt_requests": [view.model_dump(mode="json", exclude={"present", "absent"})
                                                 for view in requested],
            })
            prompt += audit_boundary.RECHECK_INSTRUCTIONS
            if self._use_scoped_prompt(job, audit_boundary.EXACT_CONTROL_CONTEXT):
                prompt += audit_boundary.EXACT_CONTROL_CONTEXT
                rules["retained_valid_controls"] = [view.model_dump(mode="json") for view in valid.masks]
            result_type = audit_boundary.RecheckedAudit
        if self.recovered_evidence is not None:
            previous_audit = self.recovered_evidence.prior_audit
            prompt += evidence_recovery.AUDIT_INSTRUCTIONS
            rules["prior_objections"] = previous_audit.objections
            rules["proposed_exact_views"] = evidence_recovery.proposed_views(previous_audit)
        if (self.audit_recovery is not None or reserved_prompt is None
                or audit_contract.SCOPED_INSTRUCTIONS in reserved_prompt):
            prompt += audit_contract.SCOPED_INSTRUCTIONS
            schema = audit_contract.output_schema(bundles, freeze, result_type)
        if (job == "audit" and self.runner.ledger.requires_delivery_attestation
                and self._use_scoped_prompt(job, audit_boundary.ACCEPTANCE_LAYOUT)):
            prompt += audit_boundary.ACCEPTANCE_LAYOUT

        def science_audit(value: AuditReview) -> AuditReview:
            if self.runner.ledger.requires_delivery_attestation and isinstance(value, MilestoneAudit):
                return audit_boundary.targeted_audit(value, bundles)
            return value

        def verify_audit_output(value: AuditReview) -> None:
            if value.verdict == "accept":
                if value.objections:
                    raise ValueError(audit_boundary.ACCEPTANCE_FORMAT_ERROR)
                if valid is not None:
                    science.verify_audit(science_audit(value), bundles, freeze, required, reviews)
                    audit_boundary.verify_recheck(audit_boundary.RecheckedAudit.model_validate(value), valid, whole,
                                                  requested, bundles)

        result = self.job(
            job, "audit", {
                "paired_bundles": _json({condition: _source_array(sources) for condition, sources in bundles.items()}),
                "intended_intervention": _json(freeze.model_dump(mode="json", include={
                    "natural", "variants", "required", "candidates",
                })),
                "provisional_keys": _json(_models(reviews)), "neutral_brief": design.neutral_brief,
                "ontology": _instruction("ontology.md"), "audit_rules": _json(rules),
            },
            prompt, result_type, output_schema=schema,
            validate=verify_audit_output if self.runner.ledger.requires_delivery_attestation else None,
        )
        science.verify_audit(science_audit(result), bundles, freeze, required, reviews)
        if result.verdict != "accept":
            self.reject("scientific_review", result.model_dump_json(), quarantine=result.verdict == "quarantine",
                        disposition=job if recheck is not None else None)
        if self.audit_recovery is not None:
            audit_recovery.verify_plan(RecoveredAuditReview.model_validate(result), self.audit_recovery)
        if self.recovered_evidence is not None:
            evidence_recovery.verify_controls(self.recovered_evidence.prior_audit, result)
        if valid is not None:
            audit_boundary.verify_recheck(audit_boundary.RecheckedAudit.model_validate(result), valid, whole, requested, bundles)
        self.advance("masks", {"audit": result.model_dump(mode="json")}, gate="independent scientific audit and risk plan")
        return result

    def confirm_joint_plan(
        self, design: DesignOutput, bundles: dict[str, list[Source]], freeze: BatchSourceFreeze,
        reviews: dict[str, Adjudication], required: set[science.Risk], release: dict[str, Any],
    ) -> AuditReview:
        original = joint_control_plan.retained_audit(self.runner, release)
        earlier: list[MilestoneAudit] = [self.frozen_case.audit] if self.frozen_case is not None else []
        recheck = audit_boundary.release(self.runner)
        if recheck is not None:
            earlier.append(audit_boundary.returned_audit(self.runner, recheck))
        plan = joint_control_plan.build_plan(original, earlier, bundles, freeze, required, reviews)
        job = joint_control_plan.JOB
        return_context = {}
        followup = joint_control_plan.followup(self.runner)
        if followup is not None:
            returned, receipt, request = self.runner.committed_result("audit", job, "audit", joint_control_plan.Confirmation)
            prior_rules = commissioning._read_json(request["inputs"]["audit_rules"])
            if (receipt["receipt_sha256"] != followup.receipt_sha256 or returned.verdict != "return"
                    or prior_rules["additional_proposed_views_by_commitment"] != plan.commitments):
                raise ValueError("A joint-plan follow-up must preserve the exact returned precommitments.")
            plan = joint_control_plan.amend(plan, followup)
            science.verify_audit(audit_boundary.targeted_audit(plan.audit, bundles), bundles, freeze, required, reviews)
            return_context = {"prior_review_and_objections": returned.model_dump(mode="json")}
            job = joint_control_plan.FOLLOWUP_JOB
        proposed = plan.commitments

        def verify_acceptance(review: joint_control_plan.Confirmation) -> None:
            if review.verdict == "accept" and (review.objections or len(review.confirmed_views) != len(proposed)
                                              or set(review.confirmed_views) != proposed.keys()):
                raise ValueError("An accepted plan must independently confirm every proposed exact view.")

        confirmation = self.job(
            job, "audit", {
                "paired_bundles": _json({name: _source_array(sources) for name, sources in bundles.items()}),
                "intended_intervention": _json(freeze.model_dump(mode="json", include={"required", "variants", "candidates"})),
                "ontology": _instruction("ontology.md"), "neutral_brief": design.neutral_brief,
                "provisional_keys": _json(_models(reviews)),
                "audit_rules": _json({
                    "retained_exact_audit": original.model_dump(mode="json"),
                    "earlier_independent_objections": [note for review in earlier for note in review.objections],
                    "full_control_plan": plan.audit.model_dump(mode="json"),
                    "additional_proposed_views_by_commitment": proposed,
                    "verified_prior_gates": audit_boundary.prior_gates(self.runner),
                    **return_context,
                    **({"exact_whitespace_excerpt_derivatives": plan.excerpt_derivatives}
                       if plan.excerpt_derivatives else {}),
                }),
            },
            "Independently test the documentary and scientific validity of this exact control plan for the frozen "
            "adjudicated file. Check each newly proposed sufficient subset, its verbatim quotations and each proper "
            "deletion. Decide independently whether the expected edge follows from those Sources at the requested "
            "cutoff, whether another route remains and whether the inherited plan is still coherent. Return if a "
            "proof route or any control expectation is unsupported. If all controls are appropriate, accept and give "
            "every exact proposed view commitment in confirmed_views. This assessment precommits predictions for "
            "separate masked reviewers. Report any scientific limitation.",
            joint_control_plan.Confirmation, validate=verify_acceptance,
        )
        if confirmation.verdict != "accept":
            self.reject("scientific_review", confirmation.model_dump_json(), quarantine=True)
        result = plan.audit.model_copy(update={
            "limitations": [*plan.audit.limitations, *confirmation.limitations],
        })
        outputs: dict[str, Any] = {
            "audit": result.model_dump(mode="json"), "joint_plan_confirmation": confirmation.model_dump(mode="json"),
        }
        if plan.excerpt_derivatives:
            outputs["exact_whitespace_excerpt_derivatives"] = plan.excerpt_derivatives
        self.advance("masks", outputs,
                     gate="independently confirmed exact joint control assignments")
        return result

    def _reserved_audit_prompt(self, job: str = "audit") -> str | None:
        for row in self.runner.ledger.attempts(self.runner.family):
            if row["revision"] == self.runner.revision and row["job"] == job:
                return str(commissioning._read_json(row["request"])["prompt"])
        return None

    def masks(
        self, design: DesignOutput, bundles: dict[str, list[Source]], audit: AuditReview,
    ) -> list[dict[str, Any]]:
        if isinstance(audit, MilestoneAudit):
            return self.milestone_masks(design, bundles, audit)
        jobs = {f"mask-{index:03}": mask for index, mask in enumerate(audit.masks)}
        if (self.runner.manifest.phase in {"construction", "milestone"} or self.release
                or annotation_recovery.recorded(self.runner) is not None):
            self.runner.ledger.require_capacity(self.runner.family, self.runner.revision, set(jobs))
        results = []
        for index, (job, mask) in enumerate(jobs.items()):
            sources = science.mask_sources(mask, bundles[mask.condition])
            reading = self.read(job, "masked", design, sources)
            edges = science.check_reading(reading, sources).keys()
            if not set(mask.present) <= edges or set(mask.absent) & edges:
                self.reject("scientific_review", f"Independent mask {index} failed its exact precommitment.",
                            quarantine=True)
            results.append({"assignment": mask.model_dump(mode="json"), "observed_edges": sorted(edges)})
        self.advance("technical", {"mask_results": results}, gate="all targeted masked readings satisfy commitments")
        return results

    def milestone_masks(
        self, design: DesignOutput, bundles: dict[str, list[Source]], audit: MilestoneAudit,
    ) -> list[dict[str, Any]]:
        assignments = []
        first_jobs: dict[str, str] = {}
        excerpts = audit.excerpt_controls if isinstance(audit, audit_boundary.RecheckedAudit) else []
        for index, mask in enumerate([*audit.masks, *excerpts]):
            if any(condition.casefold() in mask.question.casefold() for condition in bundles):
                self.reject("scientific_review", "A masked reviewer question exposes a condition identifier.")
            condition_sources = bundles[mask.condition]
            if isinstance(mask, audit_boundary.ExactExcerpt):
                sources = audit_boundary.render_excerpt(mask, condition_sources)
            elif self.runner.ledger.requires_delivery_attestation and audit_boundary.large_confirmation(mask, condition_sources):
                sources = condition_sources
            else:
                sources = science.mask_sources(mask, condition_sources)
            signature = evidence_recovery.observation_key(mask, sources)
            job = f"mask-{index:03}"
            if audit.equivalent_views_reusable:
                job = first_jobs.setdefault(signature, job)
            assignments.append((job, mask, sources))
        self.runner.ledger.require_capacity(
            self.runner.family, self.runner.revision, {job for job, _, _ in assignments},
        )
        observations = self._observe_masked_jobs(design, assignments)
        results = [
            {"assignment": mask.model_dump(mode="json"), "observation_job": job,
             "observed_edges": sorted(observations[job]),
             **({"observation_kind": "isolated_whole_file_confirmation"}
                if (self.runner.ledger.requires_delivery_attestation
                    and not isinstance(mask, audit_boundary.ExactExcerpt)
                    and audit_boundary.large_confirmation(mask, sources)) else {})}
            for job, mask, sources in assignments
        ]
        self.advance("technical", {"mask_results": results},
                     gate="independent masked readings satisfy every retained precommitment")
        return results

    def _observe_masked_jobs(
        self, design: DesignOutput, assignments: list[tuple[str, MaskAssignment, list[Source]]],
    ) -> dict[str, set[SemanticEdge]]:
        def observe(job: str, mask: MaskAssignment, sources: list[Source]) -> tuple[set[SemanticEdge], list[dict[str, Any]]]:
            worker = copy(self)
            worker.sessions = []
            brief = design.neutral_brief + "\n\nReviewer question: " + mask.question
            reading = worker.read(job, "masked", design.model_copy(update={"neutral_brief": brief}), sources)
            return set(science.check_reading(reading, sources)), worker.sessions

        unique = {job: (job, mask, sources) for job, mask, sources in assignments}
        jobs = list(unique.values())
        workers = min(self.runner.ledger.parallel_scientific_jobs, 2)
        observations = {}
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Stop at the first failed pair, before reserving more isolated controls.
            for start in range(0, len(jobs), workers):
                batch = jobs[start:start + workers]
                futures = [executor.submit(observe, *arguments) for arguments in batch]
                completed = [future.result() for future in futures]
                for _, receipts in completed:
                    self.sessions.extend(receipts)
                for (job, mask, _), (edges, _) in zip(batch, completed, strict=True):
                    if not set(mask.present) <= edges or set(mask.absent) & edges:
                        self.reject("scientific_review", f"Independent observation {job} failed a required control.",
                                    quarantine=True)
                    observations[job] = edges
        return observations

    def technical(
        self, freeze: BatchSourceFreeze, reviews: dict[str, Adjudication],
    ) -> tuple[dict[str, Any], BatchFamilyManifest]:
        root = self.directory / "family"
        manifest = BatchFamilyManifest(
            schema_version=4, family=self.slot.family_id,
            freeze_sha256=commissioning.digest(artifacts.read_bytes(root / "freeze.json")),
            conditions={condition: _locked_key_digest(root, condition, review.key)
                        for condition, review in reviews.items()},
        )
        artifacts.write_json(root / "manifest.json", manifest.model_dump(mode="json"))
        report = offline_report(root)
        if report["freeze_sha256"] != manifest.freeze_sha256 or set(manifest.conditions) != set(freeze.order):
            raise ValueError("Technical replay differs from the scientific freeze.")
        self.advance("admission_ready", {"replay": report, "manifest": manifest.model_dump(mode="json")},
                     gate="manifest, graph, quote, Source attribution, sufficient proof and offline scoring")
        return report, manifest

    def dossier(
        self, realism: dict[str, RealismReview], agreements: dict[str, dict[str, Any]],
        reviews: dict[str, Adjudication], audit: AuditReview, masks: list[dict[str, Any]],
        report: dict[str, Any], manifest: BatchFamilyManifest,
    ) -> None:
        root = self.directory / "family"
        events = self.runner.ledger.events(self.runner.manifest.batch_id, self.slot.family_id)
        sessions = [event["details"] for event in events if event["kind"] == "session"]
        attempts = self.runner.ledger.attempts(self.slot.family_id)
        dossier = {
            "schema_version": 1, "batch_id": self.runner.manifest.batch_id, "family_id": self.slot.family_id,
            "revision": self.runner.revision, "portfolio_sha256": self.runner.manifest.portfolio_sha256,
            "hypothesis": self.slot.hypothesis.model_dump(mode="json"), "recommendation": "accept",
            "manifest": manifest.model_dump(mode="json"), "realism": _models(realism),
            "agreement": agreements, "complete_keys": _models(reviews), "audit": audit.model_dump(mode="json"),
            "mask_results": masks, "replay": report, "sessions": sessions, "charged_attempts": len(attempts),
            "unpriced_attempts": len(attempts) - sum(row["pricing"] == "priced" for row in sessions),
            "known_cost_usd": sum(row["cost_usd"] for row in sessions if row["pricing"] == "priced"),
        }
        markdown = (
            f"# Family {self.slot.family_id}\n\nTechnical recommendation **accept**. Owner decision pending.\n\n"
            f"Scientific sessions charged **{len(attempts)}** with **{dossier['unpriced_attempts']}** unpriced.\n\n"
            f"{audit.summary}\n\n"
            + "\n".join(f"- {limitation}" for limitation in audit.limitations)
            + "\n\n[Full dossier](dossier.json) · [Manifest](manifest.json) · [Offline replay](replay/preflight.json)\n"
        )
        artifacts.write_bytes(root / "DOSSIER.md", markdown.encode())
        if self.documentary_revision is not None:
            dossier["documentary_repair_lineage"] = self.documentary_revision.lineage
        if self.frozen_release is not None:
            dossier["frozen_evidence_lineage"] = self.frozen_release.model_dump(mode="json")
        if self.recovered_evidence is not None:
            dossier["invariant_evidence_recovery"] = self.evidence_release
            dossier["invariant_route_replay"] = self.recovered_evidence.exact_route_checks
        dossier["review_files"] = review_commitments(root, manifest)
        digest = artifacts.write_json(root / "dossier.json", dossier)
        self.record("transition", "dossier", "admission_ready", "admission_ready",
                    {"family_sha256": digest, "revision": self.runner.revision, "role": "batch_coordinator",
                     "inputs": self.transition_inputs, "outputs": {"dossier": digest}})

    def reject(
        self, code: Code, evidence: str, *, repair_tickets: dict[str, str] | None = None,
        quarantine: bool = False, disposition: str | None = None,
    ) -> None:
        autonomous = code == "documentary_realism" and repair_authority.enabled(
            self.runner.ledger, self.runner.manifest,
        )
        permitted = autonomous or (self.release is None and bool(repair_tickets)
                                   and self.runner.revision <= self.runner.manifest.repair_cycles)
        target = "quarantined" if quarantine or (repair_tickets and not permitted) else "returned"
        self.record("disposition", disposition or self.stage, self.stage, target, {
            "repair_permitted": permitted, "repair_tickets": repair_tickets or {},
            "evidence": evidence, "role": "batch_coordinator",
            "inputs": self.transition_inputs, "sessions": self.sessions,
        })
        raise Blocked(self.stage, code, evidence)


def review_commitments(root: Path, manifest: BatchFamilyManifest) -> dict[str, str]:
    names = ["DOSSIER.md", "manifest.json", "freeze.json", "replay/preflight.json", *(
        path for condition in manifest.conditions for path in (f"{condition}.json", f"sources/{condition}.json")
    )]
    return {name: commissioning.digest(artifacts.read_bytes(root / name)) for name in names}


def offline_report(root: Path) -> dict[str, Any]:
    retained = root / "replay"
    if not retained.exists():
        with TemporaryDirectory(dir=root, prefix=".offline-") as path:
            work = Path(path) / "replay"
            replay.preflight(root / "manifest.json", work)
            os.rename(work, retained)
    report = commissioning._read_json(artifacts.read_bytes(retained / "preflight.json"))
    if (
        report["manifest_sha256"] != commissioning.digest(artifacts.read_bytes(root / "manifest.json"))
        or report["run_artifact_digest"] != artifact_digest(retained / "run")
        or report["paid_attempts"] != 0
    ):
        raise ValueError("Retained offline replay failed integrity checks.")
    return report


def verify_dossier(ledger: Ledger, batch: str, family: str, revision: int, expected: str) -> dict[str, Any]:
    root = ledger.root / "batches" / batch / family / str(revision) / "family"
    content = artifacts.read_bytes(root / "dossier.json")
    if commissioning.digest(content) != expected:
        raise ValueError(f"Family {family} dossier digest changed after technical recommendation.")
    dossier = commissioning._read_json(content)
    manifest = BatchFamilyManifest.model_validate(dossier["manifest"])
    if review_commitments(root, manifest) != dossier["review_files"]:
        raise ValueError(f"Family {family} reviewed artifact bytes changed.")
    verified = load_family(root / "manifest.json")
    if verified.family != family or verified.manifest_sha256 != dossier["review_files"]["manifest.json"]:
        raise ValueError(f"Family {family} manifest commitment does not match the dossier.")
    if offline_report(root) != dossier["replay"]:
        raise ValueError(f"Family {family} retained replay differs from its reviewed report.")
    return dossier


def _locked_key_digest(root: Path, condition: str, key: SavedIdeal) -> str:
    return artifacts.write_json(root / f"{condition}.json", key.model_dump(mode="json"))


def _reading_inputs(design: DesignOutput, sources: list[Source]) -> dict[str, str]:
    return {
        "sources": _json(_source_array(sources)), "neutral_brief": design.neutral_brief,
        "ontology": _instruction("ontology.md"), "annotation_rules": _instruction("annotation.md"),
    }


def _instruction(name: str) -> str:
    return commissioning.trusted_bytes(f"instructions/{name}").decode()


def _json(value: Any) -> str:
    return commissioning.json_text(value)


def _source_array(sources: list[Source]) -> list[dict[str, str]]:
    return [source.model_dump(mode="json") for source in sources]


def _models(by_condition: Mapping[str, BaseModel]) -> dict[str, Any]:
    return {condition: value.model_dump(mode="json") for condition, value in by_condition.items()}
