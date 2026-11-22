"""Reserve, dispatch and recover one isolated scientific job."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import artifacts, authorisation
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

    def _require_authority(self) -> None:
        self.ledger.require_running()
        allocation = next(row for row in self.manifest.families if row.family_id == self.family)
        authorisation.verify_hypothesis(self.family, allocation.hypothesis, self.owner)

    def run(
        self, stage: Stage, job: str, role: Role, inputs: dict[str, str], instructions: str,
        result_type: type[_T],
    ) -> tuple[_T, dict[str, Any]]:
        try:
            self._require_authority()
        except TaskHalted:
            raise
        except ValueError as error:
            raise Blocked(stage, "input_integrity", str(error), job=job) from error
        allocation = self.manifest.models[role]
        prompt = instructions if role == "designer" else (
            f"{instructions}\nReturn one JSON object. Output schema: "
            f"{commissioning.json_text(result_type.model_json_schema())}"
        )
        request = dict(
            role=role, **allocation.model_dump(mode="json"),
            parent=f"{self.family}@{self.revision}", inputs=inputs, prompt=prompt,
        )
        path = self.directory / "packets" / job
        fresh = self.ledger.reserve(
            self.family, self.revision, job, stage, request,
            commissioning.digest(commissioning.json_text(request).encode()),
        )
        if fresh:
            try:
                artifacts.write_json(path / "request.json", request)
                packet.run_packet(path, before_turn=self._require_authority)
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
