"""Append-only budget shared by development custody ledgers on one host."""

import fcntl
import sqlite3
import time
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import Field, TypeAdapter

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch import artifacts, author_context, author_delivery, authorisation, construction
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
QUARANTINE_SCHEMA = """CREATE TABLE IF NOT EXISTS quarantined_runtime_custody (
    custody TEXT PRIMARY KEY, halt_sequence INTEGER NOT NULL, halt_sha256 TEXT NOT NULL,
    verification_sha256 TEXT NOT NULL, record_sha256 TEXT NOT NULL
)"""
LOCK_TIMEOUT_SECONDS = 30
STAGE_ROLES = {
    "design": {"designer", "audit"}, "author": {"author", "audit"}, "realism": {"realism"},
    "blind": {"annotation"}, "adjudicate": {"adjudication"}, "audit": {"audit"}, "masks": {"masked"},
}


def _read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=LOCK_TIMEOUT_SECONDS)


class CustodyMember(Contract):
    root: Text
    task_id: Text
    starting_charges: Annotated[int, Field(strict=True, ge=0)]


class IsolationRestart(Contract):
    previous_database_sha256: Digest
    halted_member: Text
    halt_event_sha256: Digest
    verification_sha256: Digest
    replace_qualified: tuple[FamilyId, ...] = ()
    require_delivery_attestation: bool = False


class GiantPhaseRelease(Contract):
    authorisation_sha256: Digest
    hypothesis_sha256: Digest
    expected_sources: Annotated[int, Field(strict=True, ge=100)]


class BudgetExtension(Contract):
    previous_database_sha256: Digest
    previous_accounting_sha256: Digest
    additional_sessions: Annotated[int, Field(strict=True, gt=0)]
    giant_phase: GiantPhaseRelease | None = None


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
    isolation_restart: IsolationRestart | None = None
    budget_extension: BudgetExtension | None = None


class MilestonePool:
    def __init__(self, root: Path, authority: PoolAuthority, *, predecessor: "MilestonePool | None" = None):
        self.root = root
        self.path = root / "milestone-pool.sqlite"
        self.authority = authority
        self.predecessor = predecessor
        if (not authority.starting_charges < authority.cumulative_ceiling
                or (not authority.members and authority.isolation_restart is None and self.giant_phase is None)
                or (authority.isolation_restart is not None and authority.budget_extension is not None)):
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
        with closing(sqlite3.connect(self.path, timeout=LOCK_TIMEOUT_SECONDS)) as connection, connection:
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
        if authority.budget_extension is not None:
            self._retire_predecessor()

    def _verify_predecessor(self) -> None:
        previous = self.predecessor
        authority = self.authority
        if previous is None:
            if any((authority.predecessor_sha256, authority.isolation_restart, authority.budget_extension)):
                raise ValueError("The exact predecessor pool is required to resume the shared ceiling.")
            return
        if (authority.predecessor_sha256 != previous.digest or authority.owner != previous.authority.owner
                or authority.prior_archive_sha256 == previous.authority.prior_archive_sha256):
            raise ValueError("A successor pool must preserve its predecessor owner and archive lineage.")
        if authority.budget_extension is None and authority.cumulative_ceiling != previous.authority.cumulative_ceiling:
            raise ValueError("A successor pool must preserve its predecessor owner and cumulative ceiling.")
        with closing(_read_only(previous.path)) as connection:
            remaining = previous.remaining(connection, attached=False)
            count = connection.execute("SELECT COUNT(*) FROM qualified").fetchone()[0]
            if authority.isolation_restart is not None:
                self._verify_isolation_restart(previous, remaining)
                return
            if authority.budget_extension is not None:
                self._verify_budget_extension(previous, remaining, count)
                if self.giant_phase is not None:
                    return
            elif (authority.starting_charges != authority.cumulative_ceiling - remaining
                  or count != previous.authority.additional_target):
                raise ValueError("The predecessor must be at its verified target with its exact charges retained.")
            self._verify_member_charges(previous, connection)

    def _verify_budget_extension(self, previous: "MilestonePool", remaining: int, count: int) -> None:
        authority = self.authority
        extension = authority.budget_extension
        assert extension is not None
        starting = previous.authority.cumulative_ceiling - remaining
        accounting = artifacts.read_bytes(previous.root / "final-accounting.json")
        if (remaining < 0 or authority.starting_charges != starting
                or commissioning.digest(accounting) != extension.previous_accounting_sha256
                or commissioning.digest(artifacts.read_bytes(previous.path)) != extension.previous_database_sha256):
            raise ValueError("An extension must preserve the exact closeout, exclusions, charges and outstanding target.")
        closed = commissioning._read_json(accounting)
        if (closed.get("cumulative_charges") != starting or closed.get("remaining") != remaining
                or closed.get("unresolved_reservations") != [] or closed.get("shared_halts") != []):
            raise ValueError("A budget extension requires a completed scientific accounting closeout.")
        if extension.giant_phase is not None:
            self._verify_giant_phase(previous, closed, count, extension)
        elif (authority.cumulative_ceiling != starting + extension.additional_sessions
              or authority.additional_target != previous.authority.additional_target - count
              or authority.excluded_families != previous.authority.excluded_families):
            raise ValueError("An extension must preserve the exact closeout, exclusions, charges and outstanding target.")

    @property
    def giant_phase(self) -> GiantPhaseRelease | None:
        extension = self.authority.budget_extension
        return extension.giant_phase if extension is not None else None

    def _verify_giant_phase(
        self, previous: "MilestonePool", closed: dict[str, Any], count: int, extension: BudgetExtension,
    ) -> None:
        release = extension.giant_phase
        assert release is not None
        authority = self.authority
        if (self._members or authority.additional_target != 1 or previous.giant_phase is not None
                or authority.cumulative_ceiling != previous.authority.cumulative_ceiling + extension.additional_sessions
                or "V" not in previous.authority.excluded_families
                or authority.excluded_families != tuple(f for f in previous.authority.excluded_families if f != "V")):
            raise ValueError("The giant phase requires fresh custody, one reserved slot and its exact cumulative ceiling.")
        signed = artifacts.read_bytes(previous.root / "giant-phase-authorisation.json")
        approved = commissioning._read_json(signed)
        if (commissioning.digest(signed) != release.authorisation_sha256
                or approved.get("predecessor_pool_sha256") != previous.digest
                or approved.get("additional_sessions") != extension.additional_sessions
                or approved.get("combined_cumulative_ceiling") != authority.cumulative_ceiling):
            raise ValueError("The giant phase requires its exact additional owner authorisation.")
        if previous.isolation_guard is None or not previous.isolation_guard.require_delivery_attestation:
            raise ValueError("The giant phase must inherit the verified sender-attested author boundary.")
        roadmap = commissioning._read_json(commissioning.trusted_bytes("planning/development-20/portfolio.json"))
        slot = next(entry for entry in roadmap["slots"] if entry["family_id"] == "V")
        if (slot["tier"] != "giant" or release.expected_sources != slot["expected_sources"]
                or release.hypothesis_sha256 != slot["hypothesis"]["hypothesis_sha256"]):
            raise ValueError("The giant release must bind the existing registered V workload and hypothesis.")
        coverage = closed.get("qualified_coverage", [])
        families = {row["family_id"] for row in coverage}
        verified = {(row["family"], row["revision"], row["dossier_sha256"]) for row in previous.qualifications()}
        archived = {(row["family"], row["revision"], row["dossier_sha256"])
                    for row in closed.get("added_technical_dossiers", [])}
        if (count != previous.authority.additional_target or closed.get("number_qualified") != 19
                or len(coverage) != 19 or len(families) != 19 or "V" in families or archived != verified
                or not {family for family, _, _ in verified} <= families):
            raise ValueError("The giant phase requires 19 distinct verified non-giant dossiers in the exact closeout.")
        if not previous._verified_workload(51, 99):
            raise ValueError("The giant phase requires a verified large development dossier before commissioning.")

    def _verify_member_charges(self, previous: "MilestonePool", connection: sqlite3.Connection) -> None:
        members = previous.members
        if not members.keys() <= self._members.keys():
            raise ValueError("A successor must preserve every predecessor custody member.")
        for root, member in self._members.items():
            prior = members.get(root)
            additional = connection.execute(
                "SELECT COUNT(*) FROM reservations WHERE custody = ?", (str(root),),
            ).fetchone()[0]
            if prior is not None and (member.task_id != prior.task_id
                                      or member.starting_charges != prior.starting_charges + additional):
                raise ValueError("A successor custody member must retain every earlier charge.")
            if prior is None and member.starting_charges:
                raise ValueError("New custody must join the successor before any scientific session.")

    def _retire_predecessor(self) -> None:
        previous = self.predecessor
        extension = self.authority.budget_extension
        assert previous is not None and extension is not None
        with closing(sqlite3.connect(previous.path, timeout=LOCK_TIMEOUT_SECONDS)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if commissioning.digest(artifacts.read_bytes(previous.path)) != extension.previous_database_sha256:
                raise ValueError("Predecessor reservations changed during budget extension.")
            artifacts.write_json(previous.root / "budget-successor.json", {
                "predecessor_sha256": previous.digest, "successor_sha256": self.digest,
                "accounting_sha256": extension.previous_accounting_sha256,
            })

    def _verify_isolation_restart(self, previous: "MilestonePool", remaining: int) -> None:
        restart = self.authority.isolation_restart
        assert restart is not None
        if (self._members or self.authority.starting_charges != self.authority.cumulative_ceiling - remaining
                or commissioning.digest(artifacts.read_bytes(previous.path)) != restart.previous_database_sha256):
            raise ValueError("The isolation restart requires fresh custody and the exact closed predecessor accounting.")
        member = Path(restart.halted_member)
        if member not in previous.members:
            raise ValueError("The reported isolation stop is outside the predecessor custody.")
        with closing(_read_only(member / "ledger-v1.sqlite")) as db:
            matched = next((name for name, raw in db.execute("SELECT name, details FROM events WHERE kind = 'task_halt'")
                            if commissioning.digest(raw.encode()) == restart.halt_event_sha256
                            and commissioning._read_json(raw).get("code") == "isolation"), None)
        if matched is None:
            raise ValueError("The original shared isolation stop must remain in custody.")
        prior_restart = previous.isolation_guard
        if (not restart.require_delivery_attestation
                and (matched == "author-attachment-provenance-exposure"
                     or (prior_restart is not None and prior_restart.require_delivery_attestation))):
            raise ValueError("A successor cannot release an attachment provenance stop without delivery attestation.")
        self._verify_restart_runtime()

    @property
    def isolation_guard(self) -> IsolationRestart | None:
        if self.authority.isolation_restart is not None:
            return self.authority.isolation_restart
        return self.predecessor.isolation_guard if self.predecessor is not None else None

    def _verify_restart_runtime(self) -> None:
        restart = self.authority.isolation_restart
        if restart is None:
            if self.predecessor is not None:
                self.predecessor._verify_restart_runtime()
            return
        raw = artifacts.read_bytes(self.root / "verified-author-boundary.json")
        details = commissioning._read_json(raw)
        if (commissioning.digest(raw) != restart.verification_sha256 or details.get("verdict") != "pass"
                or details.get("packet_sha256") != commissioning.digest(Path(packet.__file__).read_bytes())
                or details.get("projection_sha256") != commissioning.digest(Path(author_context.__file__).read_bytes())):
            raise TaskHalted("The verified replacement runtime differs from its isolation release.")
        if restart.require_delivery_attestation and (
            details.get("delivery_sha256") != commissioning.digest(Path(author_delivery.__file__).read_bytes())
            or details.get("scientific_turns") != 0
        ):
            raise TaskHalted("The replacement pool lacks the exact zero-turn delivery verification.")

    def _historical_members(self) -> set[Path]:
        previous = self.predecessor
        return set(previous.members) | previous._historical_members() if previous is not None else set()

    @property
    def members(self) -> dict[Path, CustodyMember]:
        if self.predecessor is None:
            return self._members.copy()
        with closing(_read_only(self.path)) as connection:
            rows = connection.execute("SELECT custody, task_id FROM enrolments").fetchall()
        return self._members | {Path(root): CustodyMember(root=root, task_id=task, starting_charges=0)
                                for root, task in rows}

    def enrol(self, ledger: Ledger, manifest: BatchManifest, *, reference: str) -> str:
        """Register a new exact development commission under the existing successor ceiling."""
        if (self.predecessor is None or not reference.strip() or ledger.root in self._members
                or ledger.root != ledger.root.resolve() or manifest.namespace != "development"):
            raise ValueError("New custody requires an exact development commission in a successor pool.")
        if self.isolation_guard is not None and ledger.root in self._historical_members():
            raise ValueError("An isolation restart cannot enrol historical author custody.")
        committed = ledger.batch(manifest.batch_id)
        if committed is None or committed["manifest"] != manifest.model_dump(mode="json"):
            raise ValueError("Bind the immutable development commission before enrolment.")
        families = {allocation.family_id for allocation in manifest.families}
        slots = [slot for slot in committed["portfolio"]["slots"] if slot["family_id"] in families]
        giant = self.giant_phase
        if giant is not None:
            if (manifest.phase != "milestone" or manifest.qualification_target != 1 or families != {"V"}
                    or len(slots) != 1 or slots[0]["tier"] != "giant" or slots[0]["expected_sources"] != giant.expected_sources
                    or manifest.families[0].hypothesis.hypothesis_sha256 != giant.hypothesis_sha256):
                raise ValueError("Only the exact registered giant commission may enter the dedicated phase.")
        if (families & set(self.authority.excluded_families) or any(self._previously_qualified(f) for f in families)
                or (giant is None and any(slot["tier"] == "giant" or slot["expected_sources"] >= 100 for slot in slots))):
            raise ValueError("Excluded families and the giant tier cannot enter the successor pool.")
        if any(slot["expected_sources"] >= 51 for slot in slots) and not self._verified_intermediate():
            raise ValueError("A large workload requires a verified intermediate development dossier.")
        self.check_running()
        manifest_digest = authorisation.commitment(manifest)
        details = {"pool_sha256": self.digest, "root": str(ledger.root), "task_id": manifest.task_id,
                   "batch": manifest.batch_id, "manifest_sha256": manifest_digest, "reference": reference}
        with closing(sqlite3.connect(self.path, timeout=LOCK_TIMEOUT_SECONDS)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute("SELECT * FROM enrolments WHERE custody = ?", (str(ledger.root),)).fetchone()
            if prior is None:
                if any(ledger.attempts(family) for family in families):
                    raise ValueError("Enrol new custody before dispatch.")
                for root, member in self.members.items():
                    if member.task_id == manifest.task_id:
                        raise ValueError("New custody requires a distinct task identity.")
                    with closing(_read_only(root / "ledger-v1.sqlite")) as existing:
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
        return self._verified_workload(21, 50)

    def _verified_workload(self, minimum: int, maximum: int) -> bool:
        from benchmark_v3.batch.workflow import verify_dossier

        for row in self.qualifications():
            ledger = Ledger(Path(row["custody"]))
            with closing(ledger.connect()) as connection:
                batch = connection.execute("SELECT batch FROM families WHERE id = ?", (row["family"],)).fetchone()[0]
            dossier = verify_dossier(ledger, batch, row["family"], row["revision"], row["dossier_sha256"])
            if any(minimum <= case["source_count"] <= maximum for case in dossier["replay"]["preview"]["inputs"]):
                return True
        return (self.authority.budget_extension is not None and self.predecessor is not None
                and self.predecessor._verified_workload(minimum, maximum))

    def _verify_enrolment(self, root: Path) -> None:
        if root in self._members:
            return
        with closing(_read_only(self.path)) as connection:
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
        with closing(_read_only(self.path)) as database:
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
        if (self.root / "budget-successor.json").exists():
            raise TaskHalted("This milestone budget has been superseded by a verified extension.")
        self._verify_restart_runtime()
        for path in self.members:
            self._verify_enrolment(path)
            with closing(_read_only(path / "ledger-v1.sqlite")) as db:
                self.check_member(path, db, allow_quarantined=True)

    def check_member(self, root: Path, connection: sqlite3.Connection, *, allow_quarantined: bool = False) -> None:
        if connection.execute("SELECT 1 FROM events WHERE kind = 'task_freeze'").fetchone():
            raise TaskHalted("A development custody member has been frozen.")
        halts = connection.execute("SELECT sequence, details FROM events WHERE kind = 'task_halt'").fetchall()
        quarantine = self.runtime_quarantine(root)
        if quarantine is not None:
            if not allow_quarantined or len(halts) != 1 or quarantine[:2] != (
                halts[0][0], commissioning.digest(halts[0][1].encode()),
            ):
                raise TaskHalted("The affected custody is quarantined after an isolated runtime failure.")
            self._verify_runtime_quarantine(quarantine[2], quarantine[3])
            return
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

    def runtime_quarantine(self, root: Path) -> tuple[int, str, str, str] | None:
        with closing(_read_only(self.path)) as connection:
            if not _has_runtime_quarantine(connection):
                return None
            row = connection.execute(
                "SELECT halt_sequence, halt_sha256, verification_sha256, record_sha256"
                " FROM quarantined_runtime_custody WHERE custody = ?", (str(root),),
            ).fetchone()
            return row

    def _verify_runtime_quarantine(self, evidence_sha: str, record_sha: str) -> None:
        directory = self.root / "boundary"
        try:
            evidence = artifacts.read_bytes(directory / f"{evidence_sha}.json")
            record = artifacts.read_bytes(directory / f"{record_sha}.json")
        except (ValueError, OSError) as error:
            raise TaskHalted("The runtime quarantine verification is missing.") from error
        if commissioning.digest(evidence) != evidence_sha or commissioning.digest(record) != record_sha:
            raise TaskHalted("The runtime quarantine verification changed.")

    def quarantine_runtime_custody(self, ledger: "PooledLedger", proof: dict[str, Any], rationale: str) -> str:
        """Retain an ambiguous runtime halt and permanently exclude its whole scientific lineage."""
        if ledger.pool is not self or not ledger.requires_delivery_attestation or not rationale.strip():
            raise ValueError("Runtime quarantine requires the active isolated development custody.")
        self._verify_restart_runtime()
        runtime = proof.get("runtime", {})
        boundary = proof.get("filesystem", {})
        if (proof.get("submitted_turns") != 0 or not boundary.get("inside", {}).get("allowed")
                or any(boundary.get(name, {}) != {"allowed": False, "denied": True} for name in ("outside", "repository"))
                or any(not _isolated_runtime(runtime.get(effort, {}), effort) for effort in ("medium", "high"))
                or proof.get("packet_sha256") != commissioning.digest(Path(packet.__file__).read_bytes())
                or proof.get("author_delivery_sha256") != commissioning.digest(Path(author_delivery.__file__).read_bytes())):
            raise ValueError("Runtime quarantine requires fresh exact zero-turn filesystem and role verification.")
        with closing(_read_only(ledger.path)) as member:
            halts = member.execute("SELECT sequence, family, details FROM events WHERE kind = 'task_halt'").fetchall()
        if len(halts) != 1:
            raise ValueError("Runtime quarantine requires the one exact retained unreconciled halt.")
        sequence, family, raw_halt = halts[0]
        halt = commissioning._read_json(raw_halt)
        if (halt.get("code") != "isolation" or not halt.get("job")
                or halt.get("evidence") != "Codex reported an unexpected runtime action or error."):
            raise ValueError("Only an ambiguous runtime notification is eligible for this quarantine.")
        batch, = ledger.batch_ids()
        events = ledger.events(batch, family)
        halted = next(row for row in events if row["sequence"] == sequence)
        directory = ledger.root / "batches" / batch / family / str(halted["revision"]) / "packets" / halt["job"]
        receipt_bytes = artifacts.read_bytes(directory / "receipt.json")
        receipt = commissioning._read_json(receipt_bytes)
        receipt_sha = commissioning.digest(receipt_bytes)
        if (receipt.get("status") != "rejected" or receipt.get("failure_kind") != "isolation"
                or receipt.get("reason") != halt["evidence"] or "submitted_at" not in receipt
                or (directory / "output.txt").exists() or not any(row["kind"] == "session"
                    and row["revision"] == halted["revision"] and row["name"] == halt["job"]
                    and row["details"]["receipt_sha256"] == receipt_sha for row in events)):
            raise ValueError("Runtime quarantine must bind the terminal rejected scientific receipt with no output.")
        evidence = (commissioning.json_text(proof) + "\n").encode()
        evidence_sha = commissioning.digest(evidence)
        halt_sha = commissioning.digest(raw_halt.encode())
        record = {
            "pool_sha256": self.digest, "family": family, "custody": str(ledger.root), "halt_sha256": halt_sha,
            "halt_sequence": sequence, "rejected_receipt_sha256": receipt_sha, "verification_sha256": evidence_sha,
            "disposition": "permanently_quarantined", "dispatch_parallelism": 1, "rationale": rationale,
        }
        record_bytes = (commissioning.json_text(record) + "\n").encode()
        record_sha = commissioning.digest(record_bytes)
        artifacts.write_bytes(self.root / "boundary" / f"{record_sha}.json", record_bytes)
        artifacts.write_bytes(self.root / "boundary" / f"{evidence_sha}.json", evidence)
        with closing(sqlite3.connect(self.path, timeout=LOCK_TIMEOUT_SECONDS)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM qualified WHERE custody = ?", (str(ledger.root),)).fetchone():
                raise ValueError("A qualified custody requires separate technical revalidation before runtime quarantine.")
            connection.execute(QUARANTINE_SCHEMA)
            saved = (str(ledger.root), sequence, halt_sha, evidence_sha, record_sha)
            connection.execute("INSERT OR IGNORE INTO quarantined_runtime_custody VALUES (?, ?, ?, ?, ?)", saved)
            if connection.execute("SELECT * FROM quarantined_runtime_custody WHERE custody = ?", saved[:1]).fetchone() != saved:
                raise ValueError("The runtime quarantine disposition is immutable.")
        return record_sha

    def serial_scientific_dispatch(self) -> bool:
        if self.giant_phase is not None:
            return True
        with closing(_read_only(self.path)) as connection:
            return (_has_runtime_quarantine(connection)
                    and connection.execute("SELECT 1 FROM quarantined_runtime_custody LIMIT 1").fetchone() is not None)

    def dispatch_quarantine_digests(self) -> list[str]:
        with closing(_read_only(self.path)) as connection:
            if not _has_runtime_quarantine(connection):
                return []
            return [record for record, in connection.execute(
                "SELECT record_sha256 FROM quarantined_runtime_custody ORDER BY record_sha256",
            )]

    def dispatch_capacity_path(self, quarantine_digests: list[str]) -> Path:
        epoch = commissioning.digest(commissioning.json_text(quarantine_digests).encode())
        return self.root / "dispatch-capacity" / f"{epoch}.json"

    def verified_dispatch_slots(self) -> int:
        """Allow a bounded second slot only on the exact verified recovery epoch."""
        if self.giant_phase is not None:
            return 1
        releases = self.dispatch_quarantine_digests()
        if not releases:
            return 1
        path = self.dispatch_capacity_path(releases)
        legacy = not path.exists()
        if legacy:
            path = self.root / "verified-dispatch-capacity.json"
        if not path.exists():
            return 1
        try:
            proof = commissioning._read_json(artifacts.read_bytes(path))
        except (ValueError, OSError) as error:
            raise TaskHalted("The independent dispatch-capacity proof cannot be verified.") from error
        if (not isinstance(proof, dict) or proof.get("pool_sha256") != self.digest
                or proof.get("submitted_turns") != 0 or proof.get("parallelism") != 2
                or proof.get("packet_sha256") != commissioning.digest(Path(packet.__file__).read_bytes())
                or proof.get("author_delivery_sha256") != commissioning.digest(Path(author_delivery.__file__).read_bytes())):
            raise TaskHalted("The independent dispatch-capacity proof differs from the current isolation release.")
        if releases != proof.get("quarantine_releases"):
            if legacy:
                return 1
            raise TaskHalted("The dispatch-capacity proof does not bind the current quarantine epoch.")
        contexts = proof.get("concurrent_runtime_contexts")
        if (not isinstance(contexts, list) or len(contexts) != 2
                or any(not isinstance(context, dict) for context in contexts)
                or {context.get("effort") for context in contexts} != {"medium", "high"}
                or len({context.get("thread_id") for context in contexts if context.get("thread_id")}) != 2
                or any(not _isolated_runtime(context, context["effort"]) for context in contexts)):
            raise TaskHalted("A second dispatch slot requires two independently verified empty runtime contexts.")
        return 2

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
        with closing(sqlite3.connect(self.path, timeout=LOCK_TIMEOUT_SECONDS)) as connection, connection:
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
        with closing(_read_only(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute("SELECT * FROM qualified ORDER BY rowid")]

    def record_qualification(self, ledger: "PooledLedger", batch: str, family: str, revision: int, digest: str) -> None:
        from benchmark_v3.batch.coordinator import family_status
        from benchmark_v3.batch.workflow import verify_dossier

        ledger.require_running()
        if (ledger.pool is not self or family in self.authority.excluded_families
                or self._previously_qualified(family)
                or family_status(ledger, batch, family) != (revision, "admission_ready", None)):
            raise ValueError("Only a verified technical dossier in the active custody can count.")
        verify_dossier(ledger, batch, family, revision, digest)
        with closing(sqlite3.connect(self.path, timeout=LOCK_TIMEOUT_SECONDS)) as connection, connection:
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
        restart = self.authority.isolation_restart
        if restart is not None and family in restart.replace_qualified:
            return False
        previous = self.predecessor
        return previous is not None and (any(row["family"] == family for row in previous.qualifications())
                                         or previous._previously_qualified(family))


def _has_runtime_quarantine(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'quarantined_runtime_custody'",
    ).fetchone() is not None


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
        documentary_redesign: dict[str, Any] | None = None, frozen_evidence_review: dict[str, Any] | None = None,
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
        details: dict[str, Any] = {
            "pool_sha256": self.pool.digest, "parent_sha256": parent_sha256, "reference": reference,
        }
        if documentary_redesign is not None:
            details["documentary_redesign"] = documentary_redesign
        if frozen_evidence_review is not None:
            details["frozen_evidence_review"] = frozen_evidence_review
        if previous is not None:
            if previous["details"] != details or previous["next"] != stage:
                raise ValueError("Pooled family release is immutable.")
            return
        prior_revision, current, _ = family_status(self, batch, family)
        if current in {"admission_ready", "admitted"} or revision not in {prior_revision, prior_revision + 1}:
            raise ValueError("A pooled release must extend a pending family without changing an existing dossier.")
        if documentary_redesign is not None and (
            not self.requires_delivery_attestation or stage != "design" or revision != prior_revision + 1
        ):
            raise ValueError("A clean redesign must advance to a new isolated design revision.")
        if frozen_evidence_review is not None and (
            documentary_redesign is not None or not self.requires_delivery_attestation
            or stage != "adjudicate" or revision != prior_revision + 1
        ):
            raise ValueError("A frozen evidence review must start a new isolated adjudication revision.")
        self.event(batch, family, revision, "reconcile", self._release_name, current, stage, details)

    @property
    def requires_author_context(self) -> bool:
        return self.pool.isolation_guard is not None

    @property
    def requires_delivery_attestation(self) -> bool:
        restart = self.pool.isolation_guard
        return restart is not None and restart.require_delivery_attestation

    @property
    def parallel_scientific_jobs(self) -> int:
        return 4 if self.pool.predecessor is not None and self.pool.giant_phase is None else 1

    def pooled_revision(self, batch: str, family: str, revision: int) -> bool:
        return any(row["name"] == self._release_name and row["kind"] == "reconcile"
                   and row["revision"] <= revision and row["details"]["pool_sha256"] == self.pool.digest
                   for row in self.events(batch, family))

    def require_running(self) -> None:
        self.pool.check_running()
        if self.pool.runtime_quarantine(self.root) is not None:
            raise TaskHalted("The affected custody is quarantined after an isolated runtime failure.")

    @contextmanager
    def scientific_dispatch(self) -> Iterator[bool]:
        if not self.pool.serial_scientific_dispatch():
            yield False
            return
        first = self.pool.root / "scientific-dispatch.lock"
        if self.pool.verified_dispatch_slots() == 1:
            with first.open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                self.require_running()
                yield True
            return
        paths = (first, self.pool.root / "scientific-dispatch-second.lock")
        # Keep incoming reservations from racing each other for each newly freed slot.
        with (self.pool.root / "scientific-dispatch-queue.lock").open("a") as queue:
            fcntl.flock(queue, fcntl.LOCK_EX)
            while True:
                self.require_running()
                for path in paths:
                    with path.open("a") as lock:
                        try:
                            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        except BlockingIOError:
                            continue
                        self.require_running()
                        if path == first or self.pool.verified_dispatch_slots() == 2:
                            fcntl.flock(queue, fcntl.LOCK_UN)
                            yield True
                            return
                time.sleep(0.25)

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
        if self.requires_author_context and role == "author":
            from benchmark_v3.batch.coordinator import load_commission

            runner = load_commission(self, batch).session_runner(self, family, revision)
            guard = author_delivery if self.requires_delivery_attestation else author_context
            guard.require_prompt(job, request["prompt"])
            guard.require_projection(runner, job, request["inputs"])
        planning = (self.pool.predecessor is not None and stage == "design" and role == "research_architect"
                    and job in {"portfolio-supplement", "portfolio-supplement-format-retry",
                                "portfolio-supplement-review"})
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
