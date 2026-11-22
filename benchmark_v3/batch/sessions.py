"""Reserve, dispatch and recover one isolated scientific job."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import annotation_recovery, artifacts, authorisation, continuation, design_review
from benchmark_v3.batch.contracts import BatchManifest, Code, Role, Stage
from benchmark_v3.batch.ledger import Ledger, TaskHalted

_T = TypeVar("_T", bound=BaseModel)


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
        elif any(row["kind"] in {"deferred_review", "family_release"} for row in events):
            raise ValueError("The owner decision defers this family pending separate execution approval.")
        allocation = next(row for row in self.manifest.families if row.family_id == self.family)
        authorisation.verify_hypothesis(self.family, allocation.hypothesis, self.owner)
        if role != "designer" and self.manifest.requires_design_review:
            review = design_review.recorded_review(self.ledger, self.manifest, self.owner)
            activated = release is not None and release["decision"]["release"]["action"] == "child_activation"
            if review is None or not (review.accepts(self.family) or activated):
                raise ValueError("The commissioning owner must accept this exact design before authoring.")

    def run(
        self, stage: Stage, job: str, role: Role, inputs: dict[str, str], instructions: str,
        result_type: type[_T], *, output_schema: dict[str, Any] | None = None,
    ) -> tuple[_T, dict[str, Any]]:
        try:
            self._require_authority(role)
        except TaskHalted:
            raise
        except packet.PacketIsolationError as error:
            raise Blocked(stage, "isolation", str(error), job=job) from error
        except (ValueError, OSError) as error:
            raise Blocked(stage, "input_integrity", str(error), job=job) from error
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
        if (release and release["decision"]["release"]["action"] == "fresh_adjudication"
                and role == "adjudication" and job != "adjudicate-000-fresh"):
            raise ValueError("Only one fresh adjudication job is authorised.")
        fresh = self.ledger.reserve(
            self.family, self.revision, job, stage, request,
            commissioning.digest(commissioning.json_text(request).encode()),
            reuse_only=(role in {"designer", "author", "realism", "annotation"}
                        and annotation_recovery.recorded(self) is not None)
            or (role == "designer" and release is not None),
            active_only=release is not None,
        )
        if fresh:
            try:
                artifacts.write_json(path / "request.json", request)
                packet.run_packet(path, before_turn=lambda: self._before_turn(role, stage, release is not None))
            except (packet.PacketError, OSError, ValueError) as error:
                if not (path / "receipt.json").is_file():
                    code: Code = "isolation" if isinstance(error, packet.PacketIsolationError) else "uncertain_dispatch"
                    raise Blocked(stage, code, str(error), job=job) from error
        result, evidence = self.read_reserved(stage, job, request)
        # Commit the receipt even when the output subsequently fails its scientific schema.
        self.ledger.event(
            self.manifest.batch_id, self.family, self.revision, "session", job, stage, stage, evidence,
        )
        return result_type.model_validate(commissioning._read_json(result)), evidence

    def _before_turn(self, role: Role, stage: Stage, continuation_active: bool) -> None:
        self._require_authority(role)
        if continuation_active:
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
            raise Blocked(stage, "input_integrity", str(error), job=job) from error
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
