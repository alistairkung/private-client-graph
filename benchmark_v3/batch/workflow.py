"""Coordinate a family from approved design through an offline technical package."""

import os
from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, TypeVar

from pydantic import BaseModel

from benchmark_v3 import commissioning, packet, replay
from benchmark_v3.batch import (
    adjudication_contract, adjudication_recovery, annotation_recovery, artifacts, audit_contract, continuation,
    design_recovery, science,
)
from benchmark_v3.batch.contracts import (
    Adjudication, AuditReview, AuthoredSource, Code, DesignOutput, Reading, RealismReview,
    Role, Stage,
)
from benchmark_v3.batch.sessions import Blocked, SessionRunner
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.replay_manifest import BatchFamilyManifest, BatchSourceFreeze, SavedIdeal
from private_client_graph.models.source import Source
from private_client_graph.workbench.artifacts import artifact_digest

_T = TypeVar("_T", bound=BaseModel)


class FamilyWorkflow:
    def __init__(self, runner: SessionRunner, slot: FamilySlot, admission_criteria: list[str]):
        self.runner = runner
        self.slot = slot
        self.admission_criteria = admission_criteria
        self.directory = runner.directory
        self.stage: Stage = "design"
        self.sessions: list[dict[str, Any]] = []
        self.repair_tickets: dict[str, str] = {}
        self.release = continuation.recorded(runner)
        self.release_action = self.release["decision"]["release"]["action"] if self.release else None
        self.transition_inputs: dict[str, str] = {
            "hypothesis": slot.hypothesis.hypothesis_sha256,
            "portfolio": runner.manifest.portfolio_sha256,
        }

    def run(self) -> None:
        design = self.design()
        natural = self.author(design)
        bundles, freeze = science.freeze_bundles(self.slot, design, natural)
        self.advance("realism", {"natural": _source_array(natural)}, gate="complete authored inventory and matched diff")
        realism = self.realism(design, bundles)
        self.freeze(bundles, freeze)
        readings, agreements = self.blind(design, bundles)
        reviews = self.adjudicate(design, bundles, readings, agreements)
        audit = self.audit(design, bundles, freeze, reviews, agreements)
        masks = self.masks(design, bundles, audit)
        report, manifest = self.technical(freeze, reviews)
        self.dossier(realism, agreements, reviews, audit, masks, report, manifest)

    def job(
        self, key: str, role: Role, inputs: dict[str, str], instructions: str, result_type: type[_T],
        *, output_schema: dict[str, Any] | None = None,
    ) -> _T:
        result, receipt = self.runner.run(
            self.stage, key, role, inputs, instructions, result_type, output_schema=output_schema,
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
        if recovery:
            design, receipt = design_recovery.reopen_cutoff_recovery(self.runner, self.slot, recovery)
            self.sessions.append(receipt)
        elif recovery_only:
            raise ValueError("No owner-authorized Source cut-off recovery was recorded.")
        elif self.release and self.runner.revision > 1:
            design = continuation.released_design(self.runner, self.release)
            self.repair_tickets = self.release.get("repair_tickets", {})
        elif self.runner.revision == 1:
            design = self.job(
                "design", "designer", {
                    "hypothesis_revision": f"{ref.hypothesis_id}@{ref.revision}",
                    "portfolio_slot": self.slot.model_dump_json(),
                },
                "commissioned-designer-batch-v1", DesignOutput,
            )
        else:
            previous = self.directory.parent / str(self.runner.revision - 1)
            design = artifacts.read_contract(previous / "design.json", DesignOutput)
            dispositions = [
                row for row in self.runner.ledger.events(self.runner.manifest.batch_id, self.slot.family_id)
                if row["kind"] == "disposition" and row["revision"] == self.runner.revision - 1
            ]
            self.repair_tickets = dispositions[-1]["details"]["repair_tickets"]
            expected = next(row["details"]["outputs"]["design"] for row in self.runner.ledger.events(
                self.runner.manifest.batch_id, self.slot.family_id,
            ) if row["kind"] == "transition" and row["name"] == "design"
                and row["revision"] == self.runner.revision - 1)
            if commissioning.digest(_json(design.model_dump(mode="json")).encode()) != expected:
                raise ValueError("Repair changed the locked design or hypothesis.")
        science.verify_design(self.slot, design)
        artifacts.write_json(self.directory / "design.json", design.model_dump(mode="json"))
        self.advance("author", {"design": design.model_dump(mode="json")}, gate="approved scope and dated inventory")
        return design

    def author(self, design: DesignOutput) -> list[Source]:
        sources: dict[str, Source] = {}
        changed: set[str] = set()
        tickets = self.repair_tickets
        if not tickets.keys() <= {brief.source_id for brief in design.inventory}:
            raise ValueError("Repair tickets must identify known Sources.")
        for brief in design.inventory:
            received = [sources[identity].model_dump(mode="json") for identity in brief.received]
            inputs = {
                "author_brief": _json({
                    "participant": brief.author, "date": brief.created_on.isoformat(), "brief": brief.participant_brief,
                }),
                "genre_references": _json(design.documentary_references),
                "received_correspondence": _json(received),
            }
            ticket = tickets.get(brief.source_id)
            if ticket is None and changed.intersection(brief.received):
                ticket = "Rewrite this record using the revised received correspondence."
            if ticket:
                inputs["revision_ticket"] = ticket
                changed.add(brief.source_id)
            result = self.authored(brief.source_id, inputs, reuse=bool(tickets) and ticket is None)
            sources[brief.source_id] = Source(id=brief.source_id, title=result.title, text=result.text)
        natural = list(sources.values())
        return natural

    def authored(self, identity: str, inputs: dict[str, str], *, reuse: bool) -> AuthoredSource:
        name = f"author-{identity}"
        if reuse:
            original = continuation.previous_runner(self.runner)
            content, _, request = original.committed_packet("author", name, "author")
            if request["inputs"] != inputs:
                raise ValueError("An unaffected author packet changed before repair.")
            return AuthoredSource.model_validate(commissioning._read_json(content))
        return self.job(
            name, "author", inputs, "Write this one fictional record from the participant's dated perspective. "
            "Return its title and complete text without editorial notes.", AuthoredSource,
        )

    def realism(self, design: DesignOutput, bundles: dict[str, list[Source]]) -> dict[str, RealismReview]:
        result = {}
        for index, (condition, sources) in enumerate(bundles.items()):
            review = self.job(
                f"realism-{index:03}", "realism",
                {
                    "sources": _json(_source_array(sources)), "neutral_brief": design.neutral_brief,
                    "cutoff": design.cutoff.isoformat(),
                    "possession_ledger": _json([
                        {"id": row.source_id, "date": row.created_on.isoformat(), "provenance": row.provenance,
                         "received": row.received} for row in design.inventory
                    ]),
                    "genre_references": _json(design.documentary_references),
                },
                "Review documentary realism independently. Assess purpose, possession, chronology, form, "
                "density and cues. Supply a source_findings entry for each Source ID. If repair is needed, "
                "return participant-safe documentary repair tickets keyed by Source ID and describe objections.", RealismReview,
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
            first = self.reader(f"{index:03}-a", design, sources)
            second = self.reader(f"{index:03}-b", design, sources)
            readings[condition] = first, second
            agreements[condition] = science.compare_readings(first, second, sources)
        persisted = {condition: [reply.model_dump(mode="json") for reply in pair]
                     for condition, pair in readings.items()}
        self.advance("adjudicate", {"readings": persisted, "agreements": agreements},
                     gate="two separately isolated full-file readings per frozen condition")
        return readings, agreements

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
        result = self.job(
            key, role, _reading_inputs(design, sources) | (extra or {}),
            "Read only the supplied file. Record exact sourced candidates, unresolved questions, and "
            "each reviewed Source ID. Where your own sectional readings are supplied, independently "
            "reconcile identities, supersession and cross-section claims against every full Source.",
            Reading,
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
        if not self.release:
            return self.job(job, "adjudication", inputs, prompt, Adjudication)
        ids = adjudication_contract.resolution_ids(agreement["disagreements"])
        released_job = adjudication_contract.RELEASE_JOBS.get(self.release_action or "")
        if released_job:
            if index != 0 or ids != self.release["resolution_ids"]:
                raise ValueError("The actual disputes differ from the owner-bound adjudication preflight.")
            job = released_job
        prompt += (
            " The required properties of disagreement_resolutions are exactly the disputed IDs. "
            "Use unresolved for remaining scientific objections to the provisional key. "
            "Include ordinary practitioner follow-up in the relevant source_audit entry."
        )
        complete = self.release_action == "complete_evidence_adjudication"
        if complete:
            prompt += adjudication_contract.COMPLETE_EVIDENCE_INSTRUCTIONS
        return self.job(
            job, "adjudication", inputs, prompt, Adjudication,
            output_schema=adjudication_contract.output_schema(ids, complete_evidence=complete),
        )

    def audit(
        self, design: DesignOutput, bundles: dict[str, list[Source]], freeze: BatchSourceFreeze,
        reviews: dict[str, Adjudication], agreements: dict[str, dict[str, Any]],
    ) -> AuditReview:
        required = science.audit_risks(self.slot, reviews, agreements)
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
        schema = None
        if self._uses_scoped_audit():
            prompt += audit_contract.SCOPED_INSTRUCTIONS
            schema = audit_contract.output_schema(bundles, freeze)
        result = self.job(
            "audit", "audit", {
                "paired_bundles": _json({condition: _source_array(sources) for condition, sources in bundles.items()}),
                "intended_intervention": _json(freeze.model_dump(mode="json", include={
                    "natural", "variants", "required", "candidates",
                })),
                "provisional_keys": _json(_models(reviews)), "neutral_brief": design.neutral_brief,
                "ontology": _instruction("ontology.md"),
                "audit_rules": _json({
                    "mandatory_risks": sorted(required), "blind_agreement": agreements,
                    "portfolio_admission_criteria": self.admission_criteria,
                    "batch_stop_conditions": self.runner.manifest.stop_conditions,
                }),
            },
            prompt, AuditReview, output_schema=schema,
        )
        science.verify_audit(result, bundles, freeze, required, reviews)
        if result.verdict != "accept":
            self.reject("scientific_review", result.model_dump_json(), quarantine=result.verdict == "quarantine")
        self.advance("masks", {"audit": result.model_dump(mode="json")}, gate="independent scientific audit and risk plan")
        return result

    def _uses_scoped_audit(self) -> bool:
        for row in self.runner.ledger.attempts(self.runner.family):
            if row["revision"] == self.runner.revision and row["job"] == "audit":
                # Reopening a reserved packet must reconstruct its original input commitment.
                return audit_contract.SCOPED_INSTRUCTIONS in commissioning._read_json(row["request"])["prompt"]
        return True

    def masks(
        self, design: DesignOutput, bundles: dict[str, list[Source]], audit: AuditReview,
    ) -> list[dict[str, Any]]:
        jobs = {f"mask-{index:03}": mask for index, mask in enumerate(audit.masks)}
        if self.release or annotation_recovery.recorded(self.runner) is not None:
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
        dossier["review_files"] = review_commitments(root, manifest)
        digest = artifacts.write_json(root / "dossier.json", dossier)
        self.record("transition", "dossier", "admission_ready", "admission_ready",
                    {"family_sha256": digest, "revision": self.runner.revision, "role": "batch_coordinator",
                     "inputs": self.transition_inputs, "outputs": {"dossier": digest}})

    def reject(
        self, code: Code, evidence: str, *, repair_tickets: dict[str, str] | None = None, quarantine: bool = False,
    ) -> None:
        permitted = (self.release is None and bool(repair_tickets)
                     and self.runner.revision <= self.runner.manifest.repair_cycles)
        target = "quarantined" if quarantine or (repair_tickets and not permitted) else "returned"
        self.record("disposition", self.stage, self.stage, target, {
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
