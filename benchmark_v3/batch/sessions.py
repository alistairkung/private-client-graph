"""Reserve, dispatch and recover one isolated scientific job."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import (
    adjudication_contract, adjudication_recovery, annotation_recovery, artifacts, audit_boundary, audit_recovery, author_context,
    author_delivery, author_repair, authorisation, construction, continuation, design_review, repair_authority,
)
from benchmark_v3.batch.contracts import BatchManifest, Code, Role, Stage
from benchmark_v3.batch.ledger import Ledger, TaskHalted

_T = TypeVar("_T", bound=BaseModel)
_JSON_WRAPPER = re.compile(rb"\s*```(?:json)?[ \t]*\r?\n(.*?)\r?\n```[ \t]*\s*", re.DOTALL)


class InvalidRoleOutput(ValueError):
    """A completed packet could not satisfy its deterministic output contract."""


def _decode(content: bytes, result_type: type[_T], *, unwrap: bool) -> tuple[_T, bool]:
    fenced = _JSON_WRAPPER.fullmatch(content) if unwrap else None
    payload = fenced.group(1) if fenced else content
    return result_type.model_validate(commissioning._read_json(payload)), fenced is not None


class Blocked(ValueError):
    def __init__(self, stage: Stage, code: Code, evidence: str, *, job: str | None = None):
        super().__init__(evidence)
        self.stage = stage
        self.code = code
        self.job = job


@dataclass(frozen=True)
class SessionRunner:
    ledger: Ledger
    manifest: BatchManifest
    family: str
    revision: int
    directory: Path
    owner: str

    def _require_authority(self, role: Role) -> None:
        self.ledger.require_running()
        events = self.ledger.events(self.manifest.batch_id, self.family)
        release = continuation.family_release(events, self.revision)
        if release is not None:
            continuation.verify_authority(self, release)
        elif (not self.ledger.pooled_revision(self.manifest.batch_id, self.family, self.revision)
              and any(row["kind"] in {"deferred_review", "family_release"} for row in events)):
            raise ValueError("The owner decision defers this family pending separate execution approval.")
        allocation = next(row for row in self.manifest.families if row.family_id == self.family)
        approved = allocation.approved_design
        authorisation.verify_hypothesis(
            self.family, allocation.hypothesis, self.owner, approved.hypothesis_decision if approved else None,
        )
        if approved:
            try:
                construction.load_design(self.ledger.root, self.manifest.batch_id, allocation)
            except (ValueError, OSError) as error:
                raise packet.PacketIsolationError("An approved design or lineage commitment changed.") from error
        if role != "designer" and self.manifest.requires_design_review:
            review = design_review.recorded_review(self.ledger, self.manifest, self.owner)
            activated = release is not None and release["decision"]["release"]["action"] == "child_activation"
            if not activated and self._pooled_documentary_repair(events):
                activated = any(row["kind"] == "family_release" and row["revision"] < self.revision
                                and row["details"]["decision"]["release"]["action"] == "child_activation"
                                for row in events)
            if review is None or not (review.accepts(self.family) or activated):
                raise ValueError("The commissioning owner must accept this exact design before authoring.")

    def _pooled_documentary_repair(self, events: list[dict[str, Any]]) -> bool:
        return self.ledger.pooled_revision(self.manifest.batch_id, self.family, self.revision) and any(
            row["revision"] == self.revision and row["kind"] == "transition" and row["name"] == repair_authority.REVISION
            for row in events
        )

    def run(
        self, stage: Stage, job: str, role: Role, inputs: dict[str, str], instructions: str,
        result_type: type[_T], *, output_schema: dict[str, Any] | None = None,
        validate: Callable[[_T], None] | None = None, allow_format_retry: bool = True,
    ) -> tuple[_T, dict[str, Any]]:
        recovery = repair_authority.enabled(self.ledger, self.manifest)
        followup = (
            self.ledger.construction_followup(self.family) if self.manifest.phase == "construction" else None
        )
        pooled = self.ledger.pooled_revision(self.manifest.batch_id, self.family, self.revision)
        unwrap = recovery or followup is not None or pooled
        fresh_retry_allowed = (allow_format_retry and (recovery or pooled)
                               and not (role == "designer" and self.manifest.requires_design_review))
        retry = job + repair_authority.FORMAT_RETRY
        retry_instructions = instructions if role == "designer" else (
            instructions + " Return only the exact requested JSON object."
        )
        if role == "audit" and stage == "audit" and job == audit_boundary.RECHECK:
            retry_instructions += audit_boundary.retry_instructions(self)
        elif role == "audit" and stage == "audit" and job == "audit" and self.ledger.requires_delivery_attestation:
            retry_instructions += audit_boundary.ACCEPTANCE_LAYOUT
        choice = self._selection(job) if unwrap else None
        if choice and choice["selected_job"] == retry:
            result, receipt, unwrapped = self._run_one(
                stage, retry, role, inputs, retry_instructions, result_type, output_schema=output_schema,
                validate=validate, recovery=True,
            )
            self._record_selection(stage, job, retry, receipt, result, choice["reason"], unwrapped)
            return result, receipt
        try:
            result, receipt, unwrapped = self._run_one(
                stage, job, role, inputs, instructions, result_type, output_schema=output_schema,
                validate=validate, recovery=unwrap,
            )
        except InvalidRoleOutput as error:
            if not fresh_retry_allowed:
                raise
            result, receipt, unwrapped = self._run_one(
                stage, retry, role, inputs, retry_instructions,
                result_type, output_schema=output_schema, validate=validate, recovery=True,
            )
            self._record_selection(stage, job, retry, receipt, result, str(error), unwrapped)
        else:
            if unwrapped:
                self._record_selection(stage, job, job, receipt, result, "Removed one exact JSON wrapper.", True)
        return result, receipt

    def _record_selection(
        self, stage: Stage, job: str, selected: str, receipt: dict[str, Any], result: BaseModel, reason: str,
        unwrapped: bool,
    ) -> None:
        self.ledger.event(self.manifest.batch_id, self.family, self.revision, "output_selection", job, stage, stage, {
            "selected_job": selected, "receipt_sha256": receipt["receipt_sha256"],
            "representation_unwrapped": unwrapped, "reason": reason,
            "result_sha256": commissioning.digest(commissioning.json_text(result.model_dump(mode="json")).encode()),
        })

    def committed_result(
        self, stage: Stage, job: str, role: Role, result_type: type[_T],
    ) -> tuple[_T, dict[str, Any], dict[str, Any]]:
        choice = self._selection(job)
        selected = choice["selected_job"] if choice else job
        if selected not in {job, job + repair_authority.FORMAT_RETRY}:
            raise ValueError("A derivative must reference its original job or the single format retry.")
        output, receipt, request = self.committed_packet(stage, selected, role)
        value, unwrapped = _decode(output, result_type, unwrap=bool(choice))
        if choice and (
            choice["receipt_sha256"] != receipt["receipt_sha256"] or choice["representation_unwrapped"] != unwrapped
            or choice["result_sha256"] != commissioning.digest(
                commissioning.json_text(value.model_dump(mode="json")).encode(),
            )
        ):
            raise ValueError("The recovered role output differs from its committed derivative.")
        return value, receipt, request

    def _selection(self, job: str) -> dict[str, Any] | None:
        return next((row["details"] for row in self.ledger.events(self.manifest.batch_id, self.family)
                     if (row["revision"], row["kind"], row["name"]) == (self.revision, "output_selection", job)), None)

    def _run_one(
        self, stage: Stage, job: str, role: Role, inputs: dict[str, str], instructions: str,
        result_type: type[_T], *, output_schema: dict[str, Any] | None, validate: Callable[[_T], None] | None,
        recovery: bool,
    ) -> tuple[_T, dict[str, Any], bool]:
        if self.manifest.phase == "construction" and role == "designer":
            raise Blocked(stage, "input_integrity", "Construction cannot reserve a designer turn.", job=job)
        if role == "author" and "genre_references" in inputs:
            raise Blocked(stage, "isolation", "Author packets cannot include full-file genre references.", job=job)
        try:
            self._require_authority(role)
        except TaskHalted:
            raise
        except packet.PacketIsolationError as error:
            raise Blocked(stage, "isolation", str(error), job=job) from error
        except (ValueError, OSError) as error:
            raise Blocked(stage, "input_integrity", str(error), job=job) from error
        if role == "author" and self.ledger.requires_author_context:
            try:
                self._author_guard().require_projection(self, job, inputs)
            except (ValueError, OSError, KeyError, TypeError, packet.PacketError) as error:
                raise Blocked(stage, "isolation", str(error), job=job) from error
        allocation = self.manifest.models[role]
        prompt = instructions if role == "designer" else (
            f"{instructions}\nReturn one JSON object. Output schema: "
            f"{commissioning.json_text(output_schema or result_type.model_json_schema())}"
        )
        request = dict(
            role=role, **allocation.model_dump(mode="json"),
            parent=f"{self.family}@{self.revision}", inputs=inputs, prompt=prompt,
        )
        path = self.directory / "packets" / job
        release = continuation.recorded(self)
        if role == "adjudication" and adjudication_recovery.recorded(self) is not None:
            raise ValueError("Reuse the owner-authorised adjudication derivative without a new session.")
        released_job = adjudication_contract.RELEASE_JOBS.get(release["decision"]["release"]["action"]) if release else None
        if released_job and role == "adjudication" and job != released_job:
            raise ValueError("Only one fresh adjudication job is authorised.")
        audit_release = audit_recovery.recorded(self)
        followup = (self.ledger.construction_followup(self.family)
                    if self.manifest.phase == "construction" else None)
        if role == "audit":
            base_job = job.removesuffix(repair_authority.FORMAT_RETRY) if recovery else job
            permitted = base_job == (audit_recovery.JOB if audit_release else "audit")
            if self.ledger.requires_delivery_attestation and stage == "audit" and base_job == audit_boundary.RECHECK:
                permitted = audit_boundary.release(self) is not None
            if recovery and (stage, base_job) in {
                ("design", repair_authority.PLAN_JOB), ("design", repair_authority.BUDGET_PLAN_JOB),
                ("author", repair_authority.VERIFY_JOB),
            }:
                events = self.ledger.events(self.manifest.batch_id, self.family)
                permitted = self._pooled_documentary_repair(events) or (
                    repair_authority.enabled(self.ledger, self.manifest) and any(
                        row["revision"] == self.revision and row["kind"] == "transition"
                        and row["name"] == repair_authority.REVISION for row in events
                    )
                )
            if (recovery and (stage, base_job) == ("author", "design-scope") and self.revision == 1
                    and self.manifest.requires_design_review
                    and self.ledger.pooled_revision(self.manifest.batch_id, self.family, self.revision)):
                permitted = True
            if self.ledger.requires_author_context:
                if (stage, base_job) == ("author", author_context.JOB):
                    permitted = True
                if (stage, base_job) == ("design", author_repair.JOB) and author_repair.recorded(self) is not None:
                    permitted = True
            followup_job = self.ledger.construction_jobs(followup).get(job) if followup else None
            if followup_job is not None and followup_job.stage == stage and followup_job.role == role:
                permitted = True
            if not permitted:
                raise ValueError("Only the authorised audit or repair job may be reserved.")
        if role == "masked" and audit_release:
            authorised_jobs = {f"mask-{index:03}" for index in range(len(audit_release.views))}
            if job not in authorised_jobs:
                raise ValueError("The mask job is outside the authorised audit recovery plan.")
        active_only = (release is not None or self.manifest.phase == "milestone" or followup is not None
                       or self.ledger.pooled_revision(self.manifest.batch_id, self.family, self.revision))
        fresh = self.ledger.reserve(
            self.family, self.revision, job, stage, request,
            commissioning.digest(commissioning.json_text(request).encode()),
            reuse_only=(role in {"designer", "author", "realism", "annotation"}
                        and annotation_recovery.recorded(self) is not None)
            or (role == "designer" and release is not None),
            active_only=active_only,
        )
        if fresh:
            try:
                artifacts.write_json(path / "request.json", request)
                packet.run_packet(
                    path, before_turn=lambda: self._before_turn(role, stage, active_only, path, request),
                )
            except (packet.PacketError, OSError, ValueError) as error:
                if not (path / "receipt.json").is_file():
                    code: Code = "isolation" if isinstance(error, packet.PacketIsolationError) else "uncertain_dispatch"
                    raise Blocked(stage, code, str(error), job=job) from error
        result, evidence = self.read_reserved(stage, job, request)
        # Commit the receipt even when the output subsequently fails its scientific schema.
        self.ledger.event(
            self.manifest.batch_id, self.family, self.revision, "session", job, stage, stage, evidence,
        )
        try:
            value, unwrapped = _decode(result, result_type, unwrap=recovery)
            if validate is not None:
                validate(value)
        except (UnicodeError, ValueError) as error:
            if recovery:
                self.ledger.event(
                    self.manifest.batch_id, self.family, self.revision, "rejected_output", job, stage, stage,
                    {"receipt_sha256": evidence["receipt_sha256"], "reason": str(error)},
                )
            raise InvalidRoleOutput(f"{job} failed its output contract: {error}") from error
        return value, evidence, unwrapped

    def _author_guard(self) -> Any:
        return author_delivery if self.ledger.requires_delivery_attestation else author_context

    def _before_turn(
        self, role: Role, stage: Stage, active_only: bool, directory: Path, request: dict[str, Any],
    ) -> None:
        self._require_authority(role)
        if role == "author" and self.ledger.requires_author_context:
            guard = self._author_guard()
            guard.require_prompt(directory.name, request["prompt"])
            guard.require_projection(self, directory.name, request["inputs"])
            message = commissioning.json_text({"inputs": request["inputs"], "prompt": request["prompt"]})
            handoff = commissioning._read_json(artifacts.read_bytes(directory / "handoff.json"))
            if handoff["packet_sha256"] != commissioning.digest(message.encode()):
                raise packet.PacketIsolationError("The staged author message differs from the reviewed reservation.")
        if active_only:
            self.ledger.verify_active_stage(self.family, self.revision, stage)

    def read_reserved(
        self, stage: Stage, job: str, request: dict[str, Any],
    ) -> tuple[bytes, dict[str, Any]]:
        path = self.directory / "packets" / job
        if not (path / "receipt.json").exists():
            raise Blocked(stage, "uncertain_dispatch", "A charged reservation lacks a terminal receipt.", job=job)
        try:
            receipt_bytes = artifacts.read_bytes(path / "receipt.json")
            receipt = commissioning._read_json(receipt_bytes)
        except (ValueError, OSError) as error:
            raise Blocked(stage, "uncertain_dispatch", "A charged reservation has an unreadable receipt.",
                          job=job) from error
        if not isinstance(receipt, dict) or receipt.get("status") not in {"completed", "rejected"}:
            raise Blocked(stage, "uncertain_dispatch", "A charged reservation has an invalid receipt.", job=job)
        if receipt["status"] == "rejected":
            code: Code = "isolation" if receipt.get("failure_kind") == "isolation" else "failed_dispatch"
            self.ledger.event(
                self.manifest.batch_id, self.family, self.revision, "session", job, stage, stage,
                {
                    "role": request["role"], "model": request["model"], "effort": request["effort"],
                    "session": receipt.get("session"), "receipt_sha256": commissioning.digest(receipt_bytes),
                    "packet_sha256": receipt.get("packet_sha256"), "status": "rejected",
                    "usage": receipt.get("usage"), "cost_usd": receipt.get("cost_usd"),
                    "pricing": "unpriced" if receipt.get("cost_usd") is None else "priced",
                },
            )
            raise Blocked(stage, code, receipt.get("reason", "Packet rejected."), job=job)
        try:
            if commissioning._read_json(artifacts.read_bytes(path / "request.json")) != request:
                raise ValueError("Reserved packet request changed.")
            result, evidence = artifacts.completed_packet(path, request)
        except packet.PacketIsolationError as error:
            raise Blocked(stage, "isolation", str(error), job=job) from error
        except (ValueError, KeyError, OSError, TypeError) as error:
            code = "isolation" if self.manifest.phase in {"construction", "milestone"} else "input_integrity"
            raise Blocked(stage, code, str(error), job=job) from error
        return result, evidence | {"status": "completed"}

    def committed_packet(
        self, stage: Stage, job: str, role: Role,
    ) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
        attempt = next((row for row in self.ledger.attempts(self.family)
                        if (row["revision"], row["job"], row["stage"]) == (self.revision, job, stage)), None)
        session = next((row["details"] for row in self.ledger.events(self.manifest.batch_id, self.family)
                        if (row["revision"], row["kind"], row["name"]) == (self.revision, "session", job)), None)
        if attempt is None or session is None or session.get("status") != "completed":
            raise ValueError("Owner review requires an original charged and completed scientific packet.")
        request = commissioning._read_json(attempt["request"])
        if request["role"] != role or commissioning.digest(attempt["request"].encode()) != attempt["request_sha256"]:
            raise ValueError("The completed scientific reservation differs from its recorded commitment.")
        directory = self.directory / "packets" / job
        if commissioning._read_json(artifacts.read_bytes(directory / "request.json")) != request:
            raise ValueError("The completed scientific request differs from its reservation.")
        output, evidence = artifacts.completed_packet(directory, request)
        if evidence | {"status": "completed"} != session:
            raise ValueError("The completed receipt differs from its ledger commitment.")
        return output, session, request
