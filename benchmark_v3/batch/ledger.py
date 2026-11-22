"""Single-host SQLite ledger. Reservations are charged before dispatch."""

import fcntl
import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark_v3.batch.contracts import BatchManifest, BudgetAllocation, BudgetAmendment, ExceptionRecord, Stage
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
            if manifest.phase == "expansion" and not connection.execute(
                "SELECT 1 FROM events WHERE kind = 'pilot_decision' AND next = 'continue'",
            ).fetchone():
                raise ValueError("Expansion requires the owner's exact pilot review and continuation.")
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

    def check_halt(self, connection: sqlite3.Connection) -> None:
        if connection.execute("SELECT 1 FROM events WHERE kind = 'task_freeze'").fetchone():
            raise TaskHalted("This development benchmark task has been frozen.")
        if connection.execute("SELECT 1 FROM events WHERE kind = 'task_halt'").fetchone():
            raise TaskHalted("A shared isolation or integrity failure halted this task.")

    def require_running(self) -> None:
        with closing(self.connect()) as connection:
            self.check_halt(connection)

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
        return BudgetAllocation(shared=shared, families=families)

    def amend_budget(self, amendment: BudgetAmendment) -> None:
        with self.transaction() as connection:
            self.check_halt(connection)
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
        with self.transaction() as connection:
            self.check_halt(connection)
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
            if active_only:
                self._verify_active_stage(connection, family, revision, stage)
            budget = self._effective_budget(connection)
            if connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] >= budget.shared:
                raise BudgetExhausted("Task-wide scientific-session ceiling reached.")
            used = connection.execute("SELECT COUNT(*) FROM attempts WHERE family = ?", (family,)).fetchone()[0]
            if used >= budget.families[family]:
                raise BudgetExhausted("Family scientific-session allowance reached.")
            connection.execute(
                "INSERT INTO attempts VALUES (?, ?, ?, ?, ?, ?, ?)",
                (*key, stage, json_text(request), request_sha256, timestamp()),
            )
            return True

    def verify_active_stage(self, family: str, revision: int, stage: Stage) -> None:
        with closing(self.connect()) as connection:
            self.check_halt(connection)
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
                    f"Precommitted mask plan needs {len(remaining_jobs)} new sessions with {remaining} available.",
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
