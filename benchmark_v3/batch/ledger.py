"""Single-host SQLite ledger. Reservations are charged before dispatch."""

import fcntl
import json
import sqlite3
from collections.abc import Iterator
from contextlib import AbstractContextManager, closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark_v3.batch.contracts import (
    BatchManifest, BudgetAllocation, BudgetAmendment, ConstructionFollowup, ConstructionJob,
    ConstructionRepairDecision, ConstructionRepairSlots,
    ExceptionRecord, Stage,
)
from benchmark_v3.commissioning import digest, json_text

SCHEMA = """
CREATE TABLE IF NOT EXISTS task (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1), identity TEXT NOT NULL,
    ceiling INTEGER NOT NULL, owner TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS batches (
    id TEXT PRIMARY KEY, phase TEXT NOT NULL, commitment TEXT NOT NULL, metadata TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_pilot ON batches(phase) WHERE phase = 'pilot';
CREATE TABLE IF NOT EXISTS families (
    id TEXT PRIMARY KEY, batch TEXT NOT NULL REFERENCES batches(id), allowance INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    family TEXT NOT NULL REFERENCES families(id), revision INTEGER NOT NULL, job TEXT NOT NULL,
    stage TEXT NOT NULL, request TEXT NOT NULL, request_sha256 TEXT NOT NULL, reserved_at TEXT NOT NULL,
    PRIMARY KEY(family, revision, job)
);
CREATE TABLE IF NOT EXISTS events (
    sequence INTEGER PRIMARY KEY, batch TEXT NOT NULL REFERENCES batches(id),
    family TEXT REFERENCES families(id), revision INTEGER NOT NULL, kind TEXT NOT NULL,
    name TEXT NOT NULL, previous TEXT, next TEXT, details TEXT NOT NULL, recorded_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS family_events ON events(family, revision, kind, name)
    WHERE family IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS distinct_threads ON events(json_extract(details, '$.thread_id'))
    WHERE kind = 'session' AND json_extract(details, '$.thread_id') IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS distinct_sessions ON events(json_extract(details, '$.session'))
    WHERE kind = 'session' AND json_extract(details, '$.session') IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS batch_events ON events(batch, kind, name)
    WHERE family IS NULL;
"""


class BudgetExhausted(ValueError):
    pass


class TaskHalted(ValueError):
    pass


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


class Ledger:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / "ledger-v1.sqlite"
        with closing(self.connect()) as connection:
            connection.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            yield connection

    @contextmanager
    def coordinator_lock(self) -> Iterator[None]:
        with (self.root / "coordinator.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("Another coordinator holds this task's custody lock.") from None
            yield

    def register(self, manifest: BatchManifest, identity: str, metadata: dict[str, Any]) -> None:
        with self.transaction() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO task VALUES (1, ?, ?, ?)",
                (manifest.task_id, manifest.task_session_ceiling, metadata["decision"]["owner"]),
            )
            task = connection.execute("SELECT identity, ceiling, owner FROM task").fetchone()
            if tuple(task) != (manifest.task_id, manifest.task_session_ceiling, metadata["decision"]["owner"]):
                raise ValueError("This custody ledger is bound to its original task, owner and session ceiling.")
            self.check_halt(connection)
            prior = connection.execute("SELECT commitment FROM batches WHERE id = ?", (manifest.batch_id,)).fetchone()
            if prior:
                if prior["commitment"] != identity:
                    raise ValueError("Batch configuration changed after commissioning.")
                return
            if connection.execute("SELECT 1 FROM batches WHERE phase IN ('construction', 'milestone')").fetchone():
                raise ValueError("This custody ledger is bound to its original batch.")
            if manifest.phase == "expansion" and not connection.execute(
                "SELECT 1 FROM events WHERE kind = 'pilot_decision' AND next = 'continue'",
            ).fetchone():
                raise ValueError("Expansion requires the owner's exact pilot review and continuation.")
            if manifest.phase in {"construction", "milestone"} and connection.execute(
                "SELECT 1 FROM batches"
            ).fetchone():
                raise ValueError("Construction and milestone work require a separately authorised task ledger.")
            if manifest.phase == "pilot" and connection.execute(
                "SELECT 1 FROM batches WHERE phase = 'pilot'",
            ).fetchone():
                raise ValueError("This task already has an efficiency pilot.")
            connection.execute(
                "INSERT INTO batches VALUES (?, ?, ?, ?)",
                (manifest.batch_id, manifest.phase, identity, json_text(metadata)),
            )
            for family in manifest.families:
                if connection.execute("SELECT 1 FROM families WHERE id = ?", (family.family_id,)).fetchone():
                    raise ValueError(f"Family {family.family_id} already belongs to a batch in this task.")
                connection.execute(
                    "INSERT INTO families VALUES (?, ?, ?)", (family.family_id, manifest.batch_id, family.sessions),
                )
                self._append(connection, manifest.batch_id, family.family_id, 1, "transition",
                             "commissioned", "hypothesis_approved", "design", family.model_dump(mode="json"))

    def batch(self, batch_id: str) -> dict[str, Any] | None:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT commitment, metadata FROM batches WHERE id = ?", (batch_id,)).fetchone()
        if row is None:
            return None
        if digest(row["metadata"].encode()) != row["commitment"]:
            raise ValueError("The persisted batch approval and configuration failed their integrity check.")
        return json.loads(row["metadata"])

    def batch_ids(self) -> list[str]:
        with closing(self.connect()) as connection:
            return [row["id"] for row in connection.execute("SELECT id FROM batches ORDER BY rowid")]

    @staticmethod
    def check_halt(connection: sqlite3.Connection) -> None:
        if connection.execute("SELECT 1 FROM events WHERE kind = 'task_freeze'").fetchone():
            raise TaskHalted("This development benchmark task has been frozen.")
        if connection.execute("SELECT 1 FROM events WHERE kind = 'task_halt'").fetchone():
            raise TaskHalted("A shared isolation or integrity failure halted this task.")

    def require_running(self) -> None:
        with closing(self.connect()) as connection:
            self.check_halt(connection)

    @contextmanager
    def scientific_dispatch(self) -> Iterator[bool]:
        yield False

    def record_construction_repair(self, manifest: BatchManifest, decision: ConstructionRepairDecision) -> None:
        """Append the owner's single repair decision and start the second revision atomically."""
        payload = decision.model_dump(mode="json")
        identity = digest(json_text(payload).encode())
        batch, family = decision.batch_id, decision.family_id
        with self.transaction() as connection:
            self.check_halt(connection)
            commission = self.batch(batch)
            allocation = next((row for row in manifest.families if row.family_id == family), None)
            if (
                commission is None or manifest.phase != "construction" or batch != manifest.batch_id
                or commission["manifest"] != manifest.model_dump(mode="json")
                or decision.manifest_sha256 != digest(json_text(commission["manifest"]).encode())
                or decision.owner != commission["decision"]["owner"]
                or allocation is None or allocation.approved_design is None
                or allocation.approved_design.design_sha256 != decision.design_sha256
                or decision.prior_family_ceiling != allocation.sessions
                or decision.prior_task_ceiling != manifest.task_session_ceiling
                or decision.family_ceiling < allocation.sessions
                or decision.task_ceiling < manifest.task_session_ceiling
                or sum(row.sessions for row in manifest.families if row.family_id != family)
                + decision.family_ceiling > decision.task_ceiling
            ):
                raise ValueError("Repair authority must bind the original construction, owner and budget.")
            existing = self._construction_repair(connection)
            if existing is not None:
                if existing != decision:
                    raise ValueError("The construction batch already has a different immutable repair decision.")
                return
            rows = self.events(batch, family)
            if (
                not rows or rows[-1]["revision"] != 1
                or not any(row["kind"] in {"disposition", "operator_close"} and row["next"] == "quarantined"
                           for row in rows)
                or not any(row["kind"] == "exception" and row["details"]["code"] == "documentary_realism"
                           and row["details"]["stage"] == "realism" for row in rows)
                or any(row["kind"] == "human_decision" or row["next"] in {"freeze", "admission_ready"}
                       for row in rows)
            ):
                raise ValueError("Repair requires an original documentary-realism quarantine before freeze.")
            self._append(connection, batch, None, 1, "construction_repair", "owner_authorisation",
                         None, None, {"sha256": identity, "decision": payload})
            self._append(connection, batch, family, 2, "transition", "owner_repair", "quarantined", "design",
                         {"role": "custodian", "authorisation_sha256": identity,
                          "plan_sha256": decision.plan_sha256})

    def construction_repair(self) -> ConstructionRepairDecision | None:
        with closing(self.connect()) as connection:
            return self._construction_repair(connection)

    @staticmethod
    def _construction_repair(connection: sqlite3.Connection) -> ConstructionRepairDecision | None:
        row = connection.execute(
            "SELECT details FROM events WHERE kind = 'construction_repair' AND name = 'owner_authorisation'",
        ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["details"])
        if digest(json_text(payload["decision"]).encode()) != payload["sha256"]:
            raise ValueError("Construction repair decision failed its ledger commitment.")
        return ConstructionRepairDecision.model_validate(payload["decision"])

    def record_construction_followup(self, manifest: BatchManifest, grant: ConstructionFollowup) -> None:
        """Append exact follow-up authority while preserving original charges and quarantine."""
        batch, family = grant.batch_id, grant.family_id
        with self.transaction() as connection:
            self.check_halt(connection)
            commission = self.batch(batch)
            allocation = next((row for row in manifest.families if row.family_id == family), None)
            if (
                commission is None or manifest.phase != "construction" or batch != manifest.batch_id
                or commission["manifest"] != manifest.model_dump(mode="json")
                or grant.manifest_sha256 != digest(json_text(commission["manifest"]).encode())
                or grant.owner != commission["decision"]["owner"]
                or allocation is None or allocation.approved_design is None
                or allocation.approved_design.design_sha256 != grant.design_sha256
            ):
                raise ValueError("Follow-up authority must bind the original construction, design and owner.")
            prior = self._construction_followups(connection).get(family)
            if prior:
                if prior != grant:
                    raise ValueError("A construction follow-up grant is immutable.")
                return
            events = self.events(batch, family)
            attempts = self.attempts(family)
            expected_stage = "adjudicate" if grant.resume_stage == "adjudicate" else "realism"
            prior_jobs = {row["job"] for row in attempts
                          if (row["revision"], row["stage"]) == (grant.prior_revision, expected_stage)}
            latest = events[-1]
            if (
                (latest["revision"], latest["kind"], latest["next"])
                != (grant.prior_revision, "operator_close", "quarantined")
                or len(attempts) != grant.historical_charges
                or not any(row["revision"] == grant.prior_revision and row["kind"] == "session"
                           and row["name"] in prior_jobs and row["details"]["status"] == "completed"
                           and row["details"]["receipt_sha256"] == grant.parent_receipt_sha256 for row in events)
                or any(row["kind"] == "human_decision" for row in events)
                or any(row["revision"] == grant.revision and row["job"] in grant.jobs for row in attempts)
            ):
                raise ValueError("Follow-up authority requires exact historical charges, quarantine and receipt.")
            payload = grant.model_dump(mode="json")
            self._append(connection, batch, family, grant.revision, "reconcile", "construction-followup",
                         "quarantined", grant.resume_stage, {
                             "grant": payload, "sha256": digest(json_text(payload).encode()),
                         })

    def reserve_construction_repair_slots(self, amendment: ConstructionRepairSlots) -> None:
        """Trade two unused contingent checks for scoped repair work within the original ceiling."""
        family = amendment.family_id
        with self.transaction() as connection:
            self.check_halt(connection)
            grant = self._construction_followups(connection).get(family)
            if (grant is None or grant.resume_stage != "design"
                    or digest(json_text(grant.model_dump(mode="json")).encode()) != amendment.grant_sha256):
                raise ValueError("The documentary repair must bind the original construction follow-up.")
            recorded = self._construction_repair_slots(connection, family)
            if recorded is not None:
                if recorded != amendment:
                    raise ValueError("Construction repair slots are immutable.")
                return
            events = self.events(grant.batch_id, family)
            attempts = {row["job"] for row in self.attempts(family) if row["revision"] == grant.revision}
            latest = next(row for row in reversed(events) if row["kind"] in {
                "disposition", "operator_close", "transition", "reconcile",
            })
            audit = grant.jobs.get(amendment.review_job)
            if (audit != ConstructionJob(stage="author", role="audit")
                    or latest["revision"] != grant.revision or latest["next"] != "quarantined"
                    or not any(row["revision"] == grant.revision and row["kind"] == "session"
                               and row["name"] == amendment.review_job and row["details"]["status"] == "completed"
                               and row["details"]["receipt_sha256"] == amendment.review_receipt_sha256 for row in events)
                    or not any(row["revision"] == grant.revision and row["kind"] == "disposition"
                               and row["name"] == "author" and row["next"] in {"returned", "quarantined"} for row in events)):
                raise ValueError("Documentary repair slots require the exact independent scope return.")
            masks = set(amendment.unused_masks)
            if (masks & attempts or amendment.repair_jobs.keys() & (grant.jobs.keys() | attempts)
                    or any(grant.jobs.get(job) != ConstructionJob(stage="masks", role="masked") for job in masks)):
                raise ValueError("Only unreserved contingent check slots can be reassigned within the family.")
            payload = amendment.model_dump(mode="json")
            self._append(connection, grant.batch_id, family, grant.revision, "reconcile",
                         "construction-followup-documentary", "quarantined", "author",
                         {"slots": payload, "sha256": digest(json_text(payload).encode())})

    def construction_jobs(self, grant: ConstructionFollowup) -> dict[str, ConstructionJob]:
        with closing(self.connect()) as connection:
            return self._effective_construction_jobs(connection, grant)

    @staticmethod
    def _construction_repair_slots(
        connection: sqlite3.Connection, family: str,
    ) -> ConstructionRepairSlots | None:
        row = connection.execute(
            "SELECT details FROM events WHERE family = ? AND kind = 'reconcile'"
            " AND name = 'construction-followup-documentary'", (family,),
        ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["details"])
        if digest(json_text(payload["slots"]).encode()) != payload["sha256"]:
            raise ValueError("Construction repair slots failed their immutable commitment.")
        return ConstructionRepairSlots.model_validate(payload["slots"])

    def _effective_construction_jobs(
        self, connection: sqlite3.Connection, grant: ConstructionFollowup,
    ) -> dict[str, ConstructionJob]:
        amendment = self._construction_repair_slots(connection, grant.family_id)
        if amendment is None:
            return grant.jobs
        if (amendment.family_id != grant.family_id
                or amendment.grant_sha256 != digest(json_text(grant.model_dump(mode="json")).encode())):
            raise ValueError("Construction repair slots differ from their original grant.")
        return {job: spec for job, spec in grant.jobs.items()
                if job not in amendment.unused_masks} | amendment.repair_jobs

    def construction_followup(self, family: str) -> ConstructionFollowup | None:
        with closing(self.connect()) as connection:
            return self._construction_followups(connection).get(family)

    @staticmethod
    def _construction_followups(connection: sqlite3.Connection) -> dict[str, ConstructionFollowup]:
        grants = {}
        for row in connection.execute(
            "SELECT family, details FROM events WHERE kind = 'reconcile' AND name = 'construction-followup'",
        ):
            payload = json.loads(row["details"])
            if digest(json_text(payload["grant"]).encode()) != payload["sha256"]:
                raise ValueError("Construction follow-up failed its immutable commitment.")
            grant = ConstructionFollowup.model_validate(payload["grant"])
            if row["family"] != grant.family_id:
                raise ValueError("Construction follow-up family differs from its ledger event.")
            grants[grant.family_id] = grant
        return grants

    def ceilings(self, family: str) -> tuple[int, int]:
        budget = self.effective_budget()
        return budget.families[family], budget.shared

    def effective_budget(self) -> BudgetAllocation:
        with closing(self.connect()) as connection:
            return self._effective_budget(connection)

    def _effective_budget(self, connection: sqlite3.Connection) -> BudgetAllocation:
        shared = connection.execute("SELECT ceiling FROM task").fetchone()[0]
        families = dict(connection.execute("SELECT id, allowance FROM families").fetchall())
        record = connection.execute(
            "SELECT details FROM events WHERE kind = 'budget_amendment' ORDER BY sequence DESC LIMIT 1",
        ).fetchone()
        if record:
            amendment = BudgetAmendment.model_validate_json(record["details"])
            shared = amendment.allocation.shared
            families.update(amendment.allocation.families)

        repair = self._construction_repair(connection)
        if repair is not None:
            shared = repair.task_ceiling
            families[repair.family_id] = repair.family_ceiling
        for grant in self._construction_followups(connection).values():
            ceiling = grant.historical_charges + grant.additional_sessions
            shared += max(0, ceiling - families[grant.family_id])
            families[grant.family_id] = ceiling
        return BudgetAllocation(shared=shared, families=families)

    def amend_budget(self, amendment: BudgetAmendment) -> None:
        with self.transaction() as connection:
            self.check_halt(connection)
            pilot = connection.execute("SELECT id, phase FROM batches").fetchall()
            if [tuple(row) for row in pilot] != [(amendment.batch_id, "pilot")]:
                raise ValueError("A pilot amendment requires its original standalone pilot ledger.")
            history = connection.execute(
                "SELECT details FROM events WHERE kind = 'budget_amendment' ORDER BY sequence",
            ).fetchall()
            details = amendment.model_dump(mode="json")
            if any(json.loads(row["details"]) == details for row in history):
                return
            parent = amendment.previous_amendment_sha256
            if history and parent is None:
                raise ValueError("The recorded budget amendment is immutable.")
            latest = digest(history[-1]["details"].encode()) if history else None
            if parent != latest:
                raise ValueError("The amendment must bind the exact latest budget amendment.")
            previous = self._effective_budget(connection)
            allocation = amendment.allocation
            charged = dict.fromkeys(previous.families, 0)
            charged.update(dict(connection.execute("SELECT family, COUNT(*) FROM attempts GROUP BY family")))
            if previous != amendment.previous or charged != amendment.completed_charges:
                raise ValueError("The amendment must bind the exact current ceilings and charged state.")
            if (allocation.families.keys() != previous.families.keys()
                    or sum(allocation.families.values()) != allocation.shared
                    or allocation.shared <= previous.shared
                    or any(allocation.families[key] < value for key, value in previous.families.items())):
                raise ValueError("An amendment must increase the shared ceiling without moving any family allocation.")
            name = "owner" if parent is None else f"owner-{digest(json_text(details).encode())}"
            self._append(connection, amendment.batch_id, None, 0, "budget_amendment", name, None, None, details)

    def reserve(
        self, family: str, revision: int, job: str, stage: Stage, request: dict[str, Any], request_sha256: str,
        *, reuse_only: bool = False, active_only: bool = False,
    ) -> bool:
        with self.reservation_transaction() as connection:
            self._check_reservation_halt(connection)
            key = (family, revision, job)
            prior = connection.execute(
                "SELECT request_sha256, request FROM attempts WHERE family = ? AND revision = ? AND job = ?", key,
            ).fetchone()
            if prior:
                if prior["request_sha256"] != request_sha256 or prior["request"] != json_text(request):
                    raise ValueError("A reserved scientific input changed.")
                return False
            if reuse_only:
                raise ValueError("Annotation recovery cannot reserve an earlier scientific job.")
            self._authorize_reservation(connection, family, revision, job, stage, request, request_sha256,
                                        active_only=active_only)
            connection.execute(
                "INSERT INTO attempts VALUES (?, ?, ?, ?, ?, ?, ?)",
                (*key, stage, json_text(request), request_sha256, timestamp()),
            )
            return True

    def _check_reservation_halt(self, connection: sqlite3.Connection) -> None:
        self.check_halt(connection)

    def has_reservation(self, family: str, revision: int, job: str) -> bool:
        with closing(self.connect()) as connection:
            return connection.execute(
                "SELECT 1 FROM attempts WHERE family = ? AND revision = ? AND job = ?", (family, revision, job),
            ).fetchone() is not None

    def reservation_transaction(self) -> AbstractContextManager[sqlite3.Connection]:
        return self.transaction()

    def pooled_revision(self, batch: str, family: str, revision: int) -> bool:
        return False

    @property
    def requires_author_context(self) -> bool:
        return False

    @property
    def requires_delivery_attestation(self) -> bool:
        return False

    @property
    def requires_workload_merits(self) -> bool:
        return False

    @property
    def parallel_scientific_jobs(self) -> int:
        return 1

    def _authorize_reservation(
        self, connection: sqlite3.Connection, family: str, revision: int, job: str, stage: Stage,
        request: dict[str, Any], request_sha256: str, *, active_only: bool,
    ) -> None:
        if connection.execute("SELECT 1 FROM events WHERE kind = 'pool_binding'").fetchone():
            raise ValueError("New work in this custody requires the registered shared milestone pool.")
        phase = connection.execute(
            "SELECT batches.phase FROM batches JOIN families ON families.batch = batches.id WHERE families.id = ?",
            (family,),
        ).fetchone()[0]
        if phase == "construction":
            self._verify_construction_reservation(
                connection, family, revision, job, stage, request.get("role"), active_only=active_only,
            )
        elif phase == "milestone":
            if not connection.execute(
                "SELECT 1 FROM events WHERE family = ? AND kind = 'roadmap_activation'", (family,),
            ).fetchone():
                raise ValueError("This roadmap family is still in reserve.")
            self._verify_active_stage(connection, family, revision, stage)
        elif active_only:
            self._verify_active_stage(connection, family, revision, stage)
        budget = self._effective_budget(connection)
        if connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] >= budget.shared:
            raise BudgetExhausted("Task-wide scientific-session ceiling reached.")
        used = connection.execute("SELECT COUNT(*) FROM attempts WHERE family = ?", (family,)).fetchone()[0]
        if used >= budget.families[family]:
            raise BudgetExhausted("Family scientific-session allowance reached.")
    def _verify_construction_reservation(
        self, connection: sqlite3.Connection, family: str, revision: int, job: str, stage: Stage,
        role: str | None, *, active_only: bool,
    ) -> None:
        followups = self._construction_followups(connection)
        if not followups:
            if active_only:
                self._verify_active_stage(connection, family, revision, stage)
            self._verify_construction_repair(family, revision, role, self._construction_repair(connection))
            return
        grant = followups.get(family)
        spec = self._effective_construction_jobs(connection, grant).get(job) if grant else None
        if (grant is None or grant.revision != revision or spec is None
                or (spec.stage, spec.role) != (stage, role)):
            raise ValueError("Construction follow-up reservations require an exact released job.")
        self._verify_active_stage(connection, family, revision, stage)

    @staticmethod
    def _verify_construction_repair(
        family: str, revision: int, role: str | None, repair: ConstructionRepairDecision | None,
    ) -> None:
        if revision != 1 and (revision != 2 or repair is None or repair.family_id != family or role == "designer"):
            raise ValueError("Construction reservations require the exact owner-authorised repair revision.")
        if repair is not None and (revision != 2 or family != repair.family_id):
            raise ValueError("Only the named family repair can reserve new construction work.")

    def verify_active_stage(self, family: str, revision: int, stage: Stage) -> None:
        with closing(self.connect()) as connection:
            self._check_reservation_halt(connection)
            self._verify_active_stage(connection, family, revision, stage)

    @staticmethod
    def _verify_active_stage(connection: sqlite3.Connection, family: str, revision: int, stage: Stage) -> None:
        rows = connection.execute(
            """SELECT revision, kind, next FROM events WHERE family = ?
               AND kind IN ('family_release', 'transition', 'disposition', 'human_decision',
                            'operator_close', 'exception', 'task_halt', 'reconcile')
               ORDER BY sequence DESC""", (family,),
        )
        latest = rows.fetchone()
        if latest is None or (latest["revision"], latest["next"]) != (revision, stage):
            raise ValueError("A new continuation packet requires the active revision and stage.")

    def require_capacity(self, family: str, revision: int, jobs: set[str]) -> None:
        with self.transaction() as connection:
            self.check_halt(connection)
            attempts = connection.execute(
                "SELECT revision, job FROM attempts WHERE family = ?", (family,),
            ).fetchall()
            remaining_jobs = jobs - {row["job"] for row in attempts if row["revision"] == revision}
            budget = self._effective_budget(connection)
            used = connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            remaining = min(budget.families[family] - len(attempts), budget.shared - used)
            if len(remaining_jobs) > remaining:
                raise BudgetExhausted(
                    f"The required packet plan needs {len(remaining_jobs)} new sessions with {remaining} available.",
                )

    def attempts(self, family: str) -> list[dict[str, Any]]:
        with closing(self.connect()) as connection:
            return [dict(row) for row in connection.execute(
                "SELECT * FROM attempts WHERE family = ? ORDER BY rowid", (family,),
            )]

    def events(self, batch: str, family: str | None = None) -> list[dict[str, Any]]:
        with closing(self.connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE batch = ? AND family IS ? ORDER BY sequence", (batch, family),
            )
            return [dict(row) | {"details": json.loads(row["details"])} for row in rows]

    def event(
        self, batch: str, family: str | None, revision: int, kind: str, name: str,
        previous: str | None, next_stage: str | None, details: dict[str, Any],
    ) -> None:
        with self.transaction() as connection:
            self._append(connection, batch, family, revision, kind, name, previous, next_stage, details)

    def _append(
        self, connection: sqlite3.Connection, batch: str, family: str | None, revision: int, kind: str,
        name: str, previous: str | None, next_stage: str | None, details: dict[str, Any],
    ) -> None:
        prior = connection.execute(
            """SELECT previous, next, details FROM events
               WHERE batch = ? AND family IS ? AND revision = ? AND kind = ? AND name = ?""",
            (batch, family, revision, kind, name),
        ).fetchone()
        payload = (previous, next_stage, json_text(details))
        if prior:
            if tuple(prior) != payload:
                raise ValueError(f"Immutable ledger event changed: {kind}/{name}.")
            return
        connection.execute(
            """INSERT INTO events(batch, family, revision, kind, name, previous, next, details, recorded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (batch, family, revision, kind, name, *payload, timestamp()),
        )

    def block(self, batch: str, revision: int, exception: ExceptionRecord, *, continuation: bool = False,
              qualifier: str | None = None) -> None:
        kind = "task_halt" if exception.remaining_work == "task_halted" else "exception"
        name = f"{exception.stage}-{exception.code}" + ("-continuation" if continuation else "")
        if qualifier is not None:
            name = f"{name}-{qualifier}"
        self.event(batch, exception.family_id, revision, kind, name,
                   exception.stage, None, exception.model_dump(mode="json"))
