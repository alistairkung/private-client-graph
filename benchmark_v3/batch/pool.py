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
    predecessor_sha256: Digest | None = None
    excluded_families: tuple[FamilyId, ...] = ()


class MilestonePool:
    def __init__(self, root: Path, authority: PoolAuthority, *, predecessor: "MilestonePool | None" = None):
        self.root = root
        self.path = root / "milestone-pool.sqlite"
        self.authority = authority
        self.predecessor = predecessor
        if not authority.starting_charges < authority.cumulative_ceiling or not authority.members:
            raise ValueError("Milestone pool needs a bounded positive continuation and qualification target.")
        paths = [Path(member.root) for member in authority.members]
        task_ids = {member.task_id for member in authority.members}
        if (len(task_ids) != len(paths) or len(set(paths)) != len(paths)
                or any(path != path.resolve() or not path.is_dir() for path in paths)):
            raise ValueError("Milestone pool custody must bind distinct canonical directories.")
        self._members = dict(zip(paths, authority.members, strict=True))
        self._verify_predecessor()
        commitment = authority.model_dump(mode="json", exclude_defaults=True)
        payload = commissioning.json_text(commitment)
        self.digest = commissioning.digest(payload.encode())
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        artifacts.write_json(root / "authority.json", commitment)
        with closing(sqlite3.connect(self.path, timeout=30)) as connection, connection:
            connection.executescript(SCHEMA)
            if predecessor is not None:
                connection.execute("""CREATE TABLE IF NOT EXISTS enrolments (
                    custody TEXT PRIMARY KEY, task_id TEXT NOT NULL UNIQUE, batch TEXT NOT NULL,
                    manifest_sha256 TEXT NOT NULL, record_sha256 TEXT NOT NULL
                )""")
            connection.execute("INSERT OR IGNORE INTO authority VALUES (1, ?, ?)", (self.digest, payload))
            row = connection.execute("SELECT digest, detail FROM authority WHERE singleton = 1").fetchone()
            if row != (self.digest, payload):
                raise ValueError("The shared milestone budget is immutable.")

    def _verify_predecessor(self) -> None:
        previous = self.predecessor
        if previous is None:
            if self.authority.predecessor_sha256 is not None:
                raise ValueError("The exact predecessor pool is required to resume the shared ceiling.")
            return
        authority = self.authority
        if (authority.predecessor_sha256 != previous.digest or authority.owner != previous.authority.owner
                or authority.cumulative_ceiling != previous.authority.cumulative_ceiling
                or authority.prior_archive_sha256 == previous.authority.prior_archive_sha256):
            raise ValueError("A successor pool must preserve its predecessor owner and cumulative ceiling.")
        with closing(sqlite3.connect(f"{previous.path.as_uri()}?mode=ro", uri=True)) as connection:
            remaining = previous.remaining(connection, attached=False)
            count = connection.execute("SELECT COUNT(*) FROM qualified").fetchone()[0]
            if (authority.starting_charges != authority.cumulative_ceiling - remaining
                    or count != previous.authority.additional_target or not previous.members.keys() <= self._members.keys()):
                raise ValueError("The predecessor must be at its verified target with its exact charges retained.")
            for root, member in self._members.items():
                prior = previous.members.get(root)
                additional = connection.execute(
                    "SELECT COUNT(*) FROM reservations WHERE custody = ?", (str(root),),
                ).fetchone()[0]
                if prior is not None and (member.task_id != prior.task_id
                                          or member.starting_charges != prior.starting_charges + additional):
                    raise ValueError("A successor custody member must retain every earlier charge.")
                if prior is None and member.starting_charges:
                    raise ValueError("New custody must join the successor before any scientific session.")

    @property
    def members(self) -> dict[Path, CustodyMember]:
        if self.predecessor is None:
            return self._members.copy()
        with closing(sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True)) as connection:
            rows = connection.execute("SELECT custody, task_id FROM enrolments").fetchall()
        return self._members | {Path(root): CustodyMember(root=root, task_id=task, starting_charges=0)
                                for root, task in rows}

    def enrol(self, ledger: Ledger, manifest: BatchManifest, *, reference: str) -> str:
        """Register a new exact development commission under the existing successor ceiling."""
        if (self.predecessor is None or not reference.strip() or ledger.root in self._members
                or ledger.root != ledger.root.resolve() or manifest.namespace != "development"):
            raise ValueError("New custody requires an exact development commission in a successor pool.")
        committed = ledger.batch(manifest.batch_id)
        if committed is None or committed["manifest"] != manifest.model_dump(mode="json"):
            raise ValueError("Bind the immutable development commission before enrolment.")
        families = {allocation.family_id for allocation in manifest.families}
        slots = [slot for slot in committed["portfolio"]["slots"] if slot["family_id"] in families]
        if (families & set(self.authority.excluded_families) or any(self._previously_qualified(f) for f in families)
                or any(slot["tier"] == "giant" or slot["expected_sources"] >= 100 for slot in slots)):
            raise ValueError("Excluded families and the giant tier cannot enter the successor pool.")
        if any(slot["expected_sources"] >= 51 for slot in slots) and not self._verified_intermediate():
            raise ValueError("A large workload requires a verified intermediate development dossier.")
        self.check_running()
        manifest_digest = authorisation.commitment(manifest)
        details = {"pool_sha256": self.digest, "root": str(ledger.root), "task_id": manifest.task_id,
                   "batch": manifest.batch_id, "manifest_sha256": manifest_digest, "reference": reference}
        with closing(sqlite3.connect(self.path, timeout=30)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute("SELECT * FROM enrolments WHERE custody = ?", (str(ledger.root),)).fetchone()
            if prior is None:
                if any(ledger.attempts(family) for family in families):
                    raise ValueError("Enrol new custody before dispatch.")
                for root, member in self.members.items():
                    if member.task_id == manifest.task_id:
                        raise ValueError("New custody requires a distinct task identity.")
                    with closing(sqlite3.connect(f"{(root / 'ledger-v1.sqlite').as_uri()}?mode=ro", uri=True)) as existing:
                        if families & {row[0] for row in existing.execute("SELECT id FROM families")}:
                            raise ValueError("An existing development family must retain its original custody.")
            expected = commissioning.digest((commissioning.json_text(details) + "\n").encode())
            values = (str(ledger.root), manifest.task_id, manifest.batch_id, manifest_digest, expected)
            if prior is not None and prior != values:
                raise ValueError("The development custody enrolment is immutable.")
            record = artifacts.write_json(self.root / "enrolments" / f"{expected}.json", details)
            connection.execute("INSERT OR IGNORE INTO enrolments VALUES (?, ?, ?, ?, ?)", values)
        return record

    def _verified_intermediate(self) -> bool:
        from benchmark_v3.batch.workflow import verify_dossier

        for row in self.qualifications():
            ledger = Ledger(Path(row["custody"]))
            with closing(ledger.connect()) as connection:
                batch = connection.execute("SELECT batch FROM families WHERE id = ?", (row["family"],)).fetchone()[0]
            dossier = verify_dossier(ledger, batch, row["family"], row["revision"], row["dossier_sha256"])
            if any(21 <= case["source_count"] <= 50 for case in dossier["replay"]["preview"]["inputs"]):
                return True
        return False

    def _verify_enrolment(self, root: Path) -> None:
        if root in self._members:
            return
        with closing(sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True)) as connection:
            row = connection.execute("SELECT manifest_sha256, record_sha256 FROM enrolments WHERE custody = ?",
                                     (str(root),)).fetchone()
        if row is None:
            raise ValueError("Custody is outside this shared milestone release.")
        committed = artifacts.read_bytes(self.root / "enrolments" / f"{row[1]}.json")
        detail = commissioning._read_json(committed)
        if (commissioning.digest(committed) != row[1] or detail["root"] != str(root)
                or detail["pool_sha256"] != self.digest or detail["manifest_sha256"] != row[0]):
            raise TaskHalted("The custody enrolment failed its immutable authority commitment.")

    def _boundary_record(self, root: Path) -> tuple[Path, tuple[Any, ...]] | None:
        with closing(sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True)) as database:
            record = database.execute(
                "SELECT halt_sequence, halt_sha256, packet_sha256, evidence_sha256, record_sha256"
                " FROM boundary_successors WHERE custody = ?", (str(root),),
            ).fetchone()
        if record is not None:
            return self.root / "boundary", record
        return self.predecessor._boundary_record(root) if self.predecessor is not None else None

    def join(self, root: Path) -> "PooledLedger":
        if root not in self.members:
            raise ValueError("Custody is outside this shared milestone release.")
        self._verify_enrolment(root)
        return PooledLedger(namespace_directory(root, "development"), self)

    def check_running(self) -> None:
        for path in self.members:
            self._verify_enrolment(path)
            with closing(sqlite3.connect(f"{(path / 'ledger-v1.sqlite').as_uri()}?mode=ro", uri=True)) as db:
                self.check_member(path, db)

    def check_member(self, root: Path, connection: sqlite3.Connection) -> None:
        if connection.execute("SELECT 1 FROM events WHERE kind = 'task_freeze'").fetchone():
            raise TaskHalted("A development custody member has been frozen.")
        halts = connection.execute("SELECT sequence, details FROM events WHERE kind = 'task_halt'").fetchall()
        if not halts:
            return
        boundary = self._boundary_record(root)
        if boundary is None:
            raise TaskHalted("A custody member has an unresolved shared integrity stop.")
        directory, recovered = boundary
        if (len(halts) != 1 or recovered[0] != halts[0][0]
                or recovered[1] != commissioning.digest(halts[0][1].encode())
                or recovered[2] != commissioning.digest(Path(packet.__file__).read_bytes())):
            raise TaskHalted("A custody member has an unresolved shared integrity stop.")
        evidence = artifacts.read_bytes(directory / f"{recovered[3]}.json")
        record = artifacts.read_bytes(directory / f"{recovered[4]}.json")
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

        if (ledger.pool is not self or family in self.authority.excluded_families
                or self._previously_qualified(family)
                or family_status(ledger, batch, family) != (revision, "admission_ready", None)):
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

    def _previously_qualified(self, family: str) -> bool:
        previous = self.predecessor
        return previous is not None and (any(row["family"] == family for row in previous.qualifications())
                                         or previous._previously_qualified(family))


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
            binding = self._active_binding(connection)
            details = {"pool_sha256": self.pool.digest, "starting_charges": self.member.starting_charges}
            predecessor = self.pool.predecessor
            if predecessor is not None and self.root in predecessor.members:
                prior = predecessor.members[self.root]
                expected = {"pool_sha256": predecessor.digest, "starting_charges": prior.starting_charges}
                if binding not in (expected, details):
                    raise ValueError("The existing custody must bind the exact predecessor pool.")
            elif binding is not None and binding != details:
                raise ValueError("A custody ledger already belongs to a different pool.")
            name = f"milestone-{self.pool.digest[:16]}" if predecessor is not None else "milestone"
            self._append(connection, batch, None, 0, "pool_binding", name, None, None, details)

    @staticmethod
    def _active_binding(connection: sqlite3.Connection) -> dict[str, Any] | None:
        row = connection.execute(
            "SELECT details FROM events WHERE kind = 'pool_binding' ORDER BY sequence DESC LIMIT 1",
        ).fetchone()
        return commissioning._read_json(row[0]) if row is not None else None

    def _require_active_pool(self, connection: sqlite3.Connection) -> None:
        if self._active_binding(connection) != {"pool_sha256": self.pool.digest,
                                                 "starting_charges": self.member.starting_charges}:
            raise TaskHalted("New scientific work must use the active custody pool.")

    @property
    def _release_name(self) -> str:
        return "pooled-release" if self.pool.predecessor is None else f"pooled-release-{self.pool.digest[:16]}"

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
        with closing(self.connect()) as connection:
            self._require_active_pool(connection)
        TypeAdapter(Digest).validate_python(parent_sha256)
        if (stage not in STAGE_ROLES or not reference.strip() or family in self.pool.authority.excluded_families
                or self.pool._previously_qualified(family)):
            raise ValueError("Release requires an exact scientific stage and lineage reference.")
        events = self.events(batch, family)
        previous = next((row for row in events if row["name"] == self._release_name and row["revision"] == revision), None)
        details = {"pool_sha256": self.pool.digest, "parent_sha256": parent_sha256, "reference": reference}
        if previous is not None:
            if previous["details"] != details or previous["next"] != stage:
                raise ValueError("Pooled family release is immutable.")
            return
        prior_revision, current, _ = family_status(self, batch, family)
        if current in {"admission_ready", "admitted"} or revision not in {prior_revision, prior_revision + 1}:
            raise ValueError("A pooled release must extend a pending family without changing an existing dossier.")
        self.event(batch, family, revision, "reconcile", self._release_name, current, stage, details)

    @property
    def parallel_scientific_jobs(self) -> int:
        return 4 if self.pool.predecessor is not None else 1

    def pooled_revision(self, batch: str, family: str, revision: int) -> bool:
        return any(row["name"] == self._release_name and row["kind"] == "reconcile"
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
            if self.pool._boundary_record(self.root) is None:
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
        self._require_active_pool(connection)
        self._check_accounting(connection)
        if family in self.pool.authority.excluded_families or self.pool._previously_qualified(family):
            raise ValueError("Scientific reservations cannot include a reserved or already qualified family.")
        batch = connection.execute("SELECT batch FROM families WHERE id = ?", (family,)).fetchone()[0]
        role = request.get("role")
        planning = (self.pool.predecessor is not None and stage == "design" and role == "research_architect"
                    and job in {"portfolio-supplement", "portfolio-supplement-format-retry"})
        if not self.pooled_revision(batch, family, revision) or (not planning and role not in STAGE_ROLES.get(stage, set())):
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
            self._require_active_pool(connection)
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
