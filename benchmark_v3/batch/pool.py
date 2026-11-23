"""Append-only budget shared by development custody ledgers on one host."""

import fcntl
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import Field, TypeAdapter

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import artifacts, authorisation, construction
from benchmark_v3.batch.contracts import BatchManifest, BudgetAllocation, Stage
from benchmark_v3.batch.custody import namespace_directory
from benchmark_v3.batch.ledger import BudgetExhausted, Ledger, TaskHalted
from benchmark_v3.research_contracts import Contract, Digest, FamilyId, Text

if TYPE_CHECKING:
    from benchmark_v3.batch.coordinator import Commission

SCHEMA = """
CREATE TABLE IF NOT EXISTS authority (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1), digest TEXT NOT NULL, detail TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reservations (
    custody TEXT NOT NULL, family TEXT NOT NULL, revision INTEGER NOT NULL, job TEXT NOT NULL,
    stage TEXT NOT NULL, request_sha256 TEXT NOT NULL,
    PRIMARY KEY (custody, family, revision, job)
);
CREATE TABLE IF NOT EXISTS qualified (
    family TEXT PRIMARY KEY, dossier_sha256 TEXT NOT NULL, custody TEXT NOT NULL, revision INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS boundary_successors (
    custody TEXT PRIMARY KEY, halt_sequence INTEGER NOT NULL, halt_sha256 TEXT NOT NULL,
    packet_sha256 TEXT NOT NULL, evidence_sha256 TEXT NOT NULL, record_sha256 TEXT NOT NULL
);
"""
STAGE_ROLES = {
    "design": {"designer", "audit"}, "author": {"author", "audit"}, "realism": {"realism"},
    "blind": {"annotation"}, "adjudicate": {"adjudication"}, "audit": {"audit"}, "masks": {"masked"},
}


class CustodyMember(Contract):
    root: Text
    task_id: Text
    starting_charges: Annotated[int, Field(strict=True, ge=0)]


class PoolAuthority(Contract):
    owner: Text
    reference: Text
    prior_archive_sha256: Digest
    starting_charges: Annotated[int, Field(strict=True, ge=0)]
    cumulative_ceiling: Annotated[int, Field(strict=True, gt=0)]
    additional_target: Annotated[int, Field(strict=True, ge=1, le=20)]
    members: list[CustodyMember]


class MilestonePool:
    def __init__(self, root: Path, authority: PoolAuthority):
        self.root = root
        self.path = root / "milestone-pool.sqlite"
        self.authority = authority
        if not authority.starting_charges < authority.cumulative_ceiling or not authority.members:
            raise ValueError("Milestone pool needs a bounded positive continuation and qualification target.")
        paths = [Path(member.root) for member in authority.members]
        task_ids = {member.task_id for member in authority.members}
        if (len(task_ids) != len(paths) or len(set(paths)) != len(paths)
                or any(path != path.resolve() or not path.is_dir() for path in paths)):
            raise ValueError("Milestone pool custody must bind distinct canonical directories.")
        self.members = dict(zip(paths, authority.members, strict=True))
        payload = commissioning.json_text(authority.model_dump(mode="json"))
        self.digest = commissioning.digest(payload.encode())
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        artifacts.write_json(root / "authority.json", authority.model_dump(mode="json"))
        with closing(sqlite3.connect(self.path, timeout=30)) as connection, connection:
            connection.executescript(SCHEMA)
            connection.execute("INSERT OR IGNORE INTO authority VALUES (1, ?, ?)", (self.digest, payload))
            row = connection.execute("SELECT digest, detail FROM authority WHERE singleton = 1").fetchone()
            if row != (self.digest, payload):
                raise ValueError("The shared milestone budget is immutable.")

    def join(self, root: Path) -> "PooledLedger":
        if root not in self.members:
            raise ValueError("Custody is outside this shared milestone release.")
        return PooledLedger(namespace_directory(root, "development"), self)

    def check_running(self) -> None:
        for path in self.members:
            with closing(sqlite3.connect(f"{(path / 'ledger-v1.sqlite').as_uri()}?mode=ro", uri=True)) as db:
                self.check_member(path, db)

    def check_member(self, root: Path, connection: sqlite3.Connection) -> None:
        if connection.execute("SELECT 1 FROM events WHERE kind = 'task_freeze'").fetchone():
            raise TaskHalted("A development custody member has been frozen.")
        halts = connection.execute("SELECT sequence, details FROM events WHERE kind = 'task_halt'").fetchall()
        if not halts:
            return
        with closing(sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True)) as database:
            recovered = database.execute(
                "SELECT halt_sequence, halt_sha256, packet_sha256, evidence_sha256, record_sha256"
                " FROM boundary_successors WHERE custody = ?", (str(root),),
            ).fetchone()
        if (recovered is None or len(halts) != 1 or recovered[0] != halts[0][0]
                or recovered[1] != commissioning.digest(halts[0][1].encode())
                or recovered[2] != commissioning.digest(Path(packet.__file__).read_bytes())):
            raise TaskHalted("A custody member has an unresolved shared integrity stop.")
        evidence = artifacts.read_bytes(self.root / "boundary" / f"{recovered[3]}.json")
        record = artifacts.read_bytes(self.root / "boundary" / f"{recovered[4]}.json")
        if commissioning.digest(evidence) != recovered[3] or commissioning.digest(record) != recovered[4]:
            raise TaskHalted("The successor packet boundary evidence changed.")

    def reconcile_packet_boundary(
        self, ledger: "PooledLedger", manifest: BatchManifest, previous_packet: bytes,
        boundary: bytes, runtime: dict[str, Any], rationale: str,
    ) -> str:
        """Resolve a recorded pre-dispatch version mismatch under the continuation authority."""
        if ledger.pool is not self or not rationale.strip():
            raise ValueError("A successor requires the current pool and reviewed version rationale.")
        configuration = ledger.batch(manifest.batch_id)
        if configuration is None or configuration["manifest"] != manifest.model_dump(mode="json"):
            raise ValueError("The successor must bind the original commissioned manifest.")
        with closing(ledger.connect()) as member:
            halts = member.execute("SELECT sequence, details FROM events WHERE kind = 'task_halt'").fetchall()
        if len(halts) != 1:
            raise ValueError("A boundary successor requires the one exact pre-dispatch mismatch.")
        sequence, raw_halt = halts[0]
        halt = commissioning._read_json(raw_halt)
        if (halt["stage"] != "design" or halt["code"] != "isolation"
                or halt["evidence"] != "The approved packet isolation implementation has changed."
                or commissioning.digest(previous_packet) != manifest.scope.packet_implementation_sha256):
            raise ValueError("The original stop is not a recoverable packet version mismatch.")
        current_sha = commissioning.digest(Path(packet.__file__).read_bytes())
        evidence_sha = commissioning.digest(boundary)
        scope = manifest.scope.model_copy(update={
            "packet_implementation_sha256": current_sha, "os_boundary_evidence_sha256": evidence_sha,
        })
        authorisation.verify_boundary(manifest.model_copy(update={"scope": scope}), boundary)
        proof = commissioning._read_json(boundary)
        if proof.get("turns") != 0 or any(
            effort not in runtime or not _isolated_runtime(runtime[effort], effort) for effort in ("medium", "high")
        ):
            raise ValueError("The successor boundary requires a zero-turn isolated runtime preflight.")
        record = {
            "pool_sha256": self.digest, "prior_manifest_sha256": authorisation.commitment(manifest),
            "previous_packet_sha256": manifest.scope.packet_implementation_sha256,
            "packet_sha256": current_sha, "evidence_sha256": evidence_sha,
            "halt_sequence": sequence, "halt_sha256": commissioning.digest(raw_halt.encode()),
            "runtime": runtime, "rationale": rationale,
        }
        artifacts.write_bytes(self.root / "boundary" / f"{evidence_sha}.json", boundary)
        encoded = (commissioning.json_text(record) + "\n").encode()
        record_sha = commissioning.digest(encoded)
        artifacts.write_bytes(self.root / "boundary" / f"{record_sha}.json", encoded)
        with closing(sqlite3.connect(self.path, timeout=30)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            stored = (str(ledger.root), sequence, record["halt_sha256"], current_sha, evidence_sha, record_sha)
            existing = connection.execute(
                "SELECT * FROM boundary_successors WHERE custody = ?", (str(ledger.root),),
            ).fetchone()
            if existing is not None:
                if existing != stored:
                    raise ValueError("The successor boundary reconciliation is immutable.")
                return record_sha
            if connection.execute("SELECT 1 FROM reservations WHERE custody = ?", (str(ledger.root),)).fetchone():
                raise ValueError("The version mismatch must precede any new dispatch in this custody member.")
            connection.execute("INSERT INTO boundary_successors VALUES (?, ?, ?, ?, ?, ?)", stored)
        return record_sha

    def remaining(self, connection: sqlite3.Connection, *, attached: bool = True) -> int:
        prefix = "pool." if attached else ""
        row = connection.execute(f"SELECT digest FROM {prefix}authority WHERE singleton = 1").fetchone()
        if row is None or row[0] != self.digest:
            raise TaskHalted("The attached pool differs from its approved commitment.")
        charged = connection.execute(f"SELECT COUNT(*) FROM {prefix}reservations").fetchone()[0]
        return self.authority.cumulative_ceiling - self.authority.starting_charges - charged

    def qualifications(self) -> list[dict[str, Any]]:
        with closing(sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute("SELECT * FROM qualified ORDER BY rowid")]

    def record_qualification(self, ledger: "PooledLedger", batch: str, family: str, revision: int, digest: str) -> None:
        from benchmark_v3.batch.coordinator import family_status
        from benchmark_v3.batch.workflow import verify_dossier

        if ledger.pool is not self or family_status(ledger, batch, family) != (revision, "admission_ready", None):
            raise ValueError("Only a verified technical dossier in the active custody can count.")
        verify_dossier(ledger, batch, family, revision, digest)
        with closing(sqlite3.connect(self.path, timeout=30)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute("SELECT * FROM qualified WHERE family = ?", (family,)).fetchone()
            row = (family, digest, str(ledger.root), revision)
            if current is None:
                count = connection.execute("SELECT COUNT(*) FROM qualified").fetchone()[0]
                if count >= self.authority.additional_target:
                    raise BudgetExhausted("The shared milestone qualification target has been reached.")
                connection.execute("INSERT INTO qualified VALUES (?, ?, ?, ?)", row)
            elif current != row:
                raise ValueError("A qualified family already has an immutable dossier commitment.")


def _isolated_runtime(data: dict[str, Any], effort: str) -> bool:
    return (
        data.get("effort") == effort and data.get("ephemeral") is True and data.get("empty_workspace") is True
        and data.get("approval_policy") == "never"
        and data.get("sandbox") == {"type": "readOnly", "networkAccess": False}
        and data.get("permission_profile") == {"id": "benchmark_packet", "extends": None}
        and data.get("instruction_sources") == [] and data.get("thread_environments") == []
        and data.get("runtime_workspace_roots") == []
    )


class PooledLedger(Ledger):
    def __init__(self, root: Path, pool: MilestonePool):
        self.pool = pool
        self.member = pool.members[root]
        super().__init__(root)
        self._bind()

    def _bind(self) -> None:
        with self.reservation_transaction() as connection:
            task = connection.execute("SELECT identity, owner FROM task").fetchone()
            if tuple(task) != (self.member.task_id, self.pool.authority.owner):
                raise ValueError("The pool member's original task or owner differs from its release.")
            batch = connection.execute("SELECT id FROM batches ORDER BY rowid LIMIT 1").fetchone()[0]
            self._check_accounting(connection)
            binding = connection.execute("SELECT details FROM events WHERE kind = 'pool_binding'").fetchone()
            details = {"pool_sha256": self.pool.digest, "starting_charges": self.member.starting_charges}
            if binding is not None and commissioning._read_json(binding[0]) != details:
                raise ValueError("A custody ledger already belongs to a different pool.")
            self._append(connection, batch, None, 0, "pool_binding", "milestone", None, None, details)

    @contextmanager
    def family_lock(self, family: str) -> Iterator[None]:
        family = TypeAdapter(FamilyId).validate_python(family)
        with (self.root / f"pooled-{family}.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("Another pooled worker holds this family's custody lock.") from None
            yield

    def release(
        self, batch: str, family: str, revision: int, stage: Stage, *, parent_sha256: str, reference: str,
    ) -> None:
        from benchmark_v3.batch.coordinator import family_status

        self.require_running()
        TypeAdapter(Digest).validate_python(parent_sha256)
        if stage not in STAGE_ROLES or not reference.strip():
            raise ValueError("Release requires an exact scientific stage and lineage reference.")
        events = self.events(batch, family)
        previous = next((row for row in events if row["name"] == "pooled-release" and row["revision"] == revision), None)
        details = {"pool_sha256": self.pool.digest, "parent_sha256": parent_sha256, "reference": reference}
        if previous is not None:
            if previous["details"] != details or previous["next"] != stage:
                raise ValueError("Pooled family release is immutable.")
            return
        prior_revision, current, _ = family_status(self, batch, family)
        if current in {"admission_ready", "admitted"} or revision not in {prior_revision, prior_revision + 1}:
            raise ValueError("A pooled release must extend a pending family without changing an existing dossier.")
        self.event(batch, family, revision, "reconcile", "pooled-release", current, stage, details)

    def pooled_revision(self, batch: str, family: str, revision: int) -> bool:
        return any(row["name"] == "pooled-release" and row["kind"] == "reconcile"
                   and row["revision"] <= revision and row["details"]["pool_sha256"] == self.pool.digest
                   for row in self.events(batch, family))

    def require_running(self) -> None:
        self.pool.check_running()

    def _check_reservation_halt(self, connection: sqlite3.Connection) -> None:
        self.pool.check_member(self.root, connection)

    def verify_commission_boundary(self, commission: "Commission") -> None:
        manifest = commission.manifest
        path = self.root / "boundary" / f"{manifest.scope.os_boundary_evidence_sha256}.json"
        original = artifacts.read_bytes(path)
        if commissioning.digest(original) != manifest.scope.os_boundary_evidence_sha256:
            raise TaskHalted("The original commissioned boundary evidence changed.")
        if manifest.scope.packet_implementation_sha256 == commissioning.digest(Path(packet.__file__).read_bytes()):
            authorisation.verify_boundary(manifest, original)
        else:
            self.require_running()
            with closing(sqlite3.connect(f"{self.pool.path.as_uri()}?mode=ro", uri=True)) as connection:
                accepted = connection.execute(
                    "SELECT 1 FROM boundary_successors WHERE custody = ?", (str(self.root),),
                ).fetchone()
            if accepted is None:
                raise TaskHalted("The separate successor packet boundary is not verified.")
        construction.verify_designs(self.root, manifest, commission.portfolio)

    @contextmanager
    def reservation_transaction(self) -> Iterator[sqlite3.Connection]:
        with closing(self.connect()) as connection, connection:
            connection.execute("ATTACH DATABASE ? AS pool", (str(self.pool.path),))
            for schema in ("main", "pool"):
                if connection.execute(f"PRAGMA {schema}.journal_mode").fetchone()[0] != "delete":
                    raise TaskHalted("Cross-ledger reservations require rollback journals for atomic commits.")
            connection.execute("BEGIN IMMEDIATE")
            yield connection

    def _check_accounting(self, connection: sqlite3.Connection) -> None:
        member_delta = connection.execute(
            "SELECT COUNT(*) FROM pool.reservations WHERE custody = ?", (str(self.root),),
        ).fetchone()[0]
        original_total = connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        if original_total != self.member.starting_charges + member_delta:
            raise TaskHalted("A custody reservation is missing from the approved shared accounting.")

    def _authorize_reservation(
        self, connection: sqlite3.Connection, family: str, revision: int, job: str, stage: Stage,
        request: dict[str, Any], request_sha256: str, *, active_only: bool,
    ) -> None:
        self.require_running()
        self._check_accounting(connection)
        batch = connection.execute("SELECT batch FROM families WHERE id = ?", (family,)).fetchone()[0]
        if not self.pooled_revision(batch, family, revision) or request.get("role") not in STAGE_ROLES.get(stage, set()):
            raise ValueError("A pooled reservation requires a released revision, stage and isolated role.")
        self._verify_active_stage(connection, family, revision, stage)
        if connection.execute("SELECT COUNT(*) FROM pool.qualified").fetchone()[0] >= self.pool.authority.additional_target:
            raise BudgetExhausted("The shared milestone qualification target has been reached.")
        if self.pool.remaining(connection) <= 0:
            raise BudgetExhausted("The shared milestone session ceiling has been reached.")
        connection.execute(
            "INSERT INTO pool.reservations VALUES (?, ?, ?, ?, ?, ?)",
            (str(self.root), family, revision, job, stage, request_sha256),
        )

    def require_capacity(self, family: str, revision: int, jobs: set[str]) -> None:
        self.require_running()
        with self.reservation_transaction() as connection:
            self._check_accounting(connection)
            used = {row[0] for row in connection.execute(
                "SELECT job FROM attempts WHERE family = ? AND revision = ?", (family, revision),
            )}
            remaining = self.pool.remaining(connection)
            if len(jobs - used) > remaining:
                raise BudgetExhausted(f"The required plan needs {len(jobs - used)} new sessions with {remaining} available.")

    def effective_budget(self) -> BudgetAllocation:
        with self.reservation_transaction() as connection:
            self._check_accounting(connection)
            remaining = self.pool.remaining(connection)
            used = connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            family_counts = connection.execute(
                "SELECT id, COUNT(job) FROM families LEFT JOIN attempts ON id = family GROUP BY id"
            ).fetchall()
            return BudgetAllocation(shared=used + remaining, families={row[0]: row[1] + remaining for row in family_counts})
