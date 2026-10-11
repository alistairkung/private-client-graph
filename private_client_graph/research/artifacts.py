"""Append-only observations with durable pre-dispatch budget reservations."""
import fcntl
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from .fixtures import ROOT
from .plan import ExperimentPlan, FiniteExperimentPlan
from private_client_graph.resolution import RESOLUTION_PROMPT
from private_client_graph.extraction import EXTRACTION_PROMPT


class BudgetExceeded(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_json_once(path: Path, value: Any) -> None:
    """Publish a complete JSON record without replacing an existing observation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".pending-")
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        os.unlink(temporary)


def code_snapshot() -> dict[str, str]:
    paths = sorted((ROOT / 'private_client_graph').glob('*.py'))
    for package in ('models', 'pipeline', 'extraction', 'research'):
        paths += sorted((ROOT / 'private_client_graph' / package).rglob('*.py'))
    return {str(p.relative_to(ROOT)): p.read_text() for p in paths}


def dependency_versions() -> dict[str, str]:
    packages = ('pydantic', 'pydantic-core', 'langchain-core', 'langchain-deepseek',
                'langchain-openai', 'openai', 'langsmith', 'httpx', 'httpcore')
    return {package: importlib.metadata.version(package) for package in packages}


def _provenance() -> dict[str, Any]:
    def git(*args: str) -> str | None:
        try:
            result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
        except FileNotFoundError:
            return None
        return result.stdout.strip() if result.returncode == 0 else None
    return {'git_sha': git('rev-parse', 'HEAD'),
            'dirty': bool(git('status', '--porcelain')),
            'dependencies': dependency_versions(),
            'code': code_snapshot(),
            'prompts': {'extraction': EXTRACTION_PROMPT, 'resolution': RESOLUTION_PROMPT},
            'prompt_hashes': {'extraction': checksum(EXTRACTION_PROMPT.encode()),
                              'resolution': checksum(RESOLUTION_PROMPT.encode())}}


def _safe_id(value: str) -> str:
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', value):
        raise ValueError('Invalid artifact ID')
    return value


class Bundle:
    """One experiment's immutable manifest and persistent attempt ledger."""
    def __init__(self, path: Path, manifest: dict[str, Any]):
        self.path = path
        self.manifest = manifest
        self.plan = (FiniteExperimentPlan if manifest['schema_version'] in (2, 3) else ExperimentPlan).model_validate(manifest['plan'])
        self.task_ledger = Path(manifest['task_ledger'])
        self.authorization_id: str | None = None

    @classmethod
    def create(cls, path: Path, plan: ExperimentPlan, *, task_ledger: Path | None = None) -> "Bundle":
        path.mkdir(parents=True, exist_ok=False)
        manifest = {'schema_version': plan.plan_version if isinstance(plan, FiniteExperimentPlan) else 1, 'experiment_id': uuid4().hex,
                    'created_at': utc_now(), 'plan': plan.model_dump(mode='json'),
                    'task_ledger': str((task_ledger or ROOT / 'runs/research/task-ledgers' / plan.task_id).resolve()),
                    'provenance': _provenance()}
        write_json_once(path / 'manifest.json', manifest)
        write_json_once(path / 'manifest-checksum.json', checksum((path / 'manifest.json').read_bytes()))
        return cls(path, manifest)

    @classmethod
    def open(cls, path: Path) -> "Bundle":
        data = (path / 'manifest.json').read_bytes()
        if checksum(data) != json.loads((path / 'manifest-checksum.json').read_text()):
            raise ValueError('Manifest checksum mismatch')
        manifest = json.loads(data)
        if manifest['schema_version'] not in (1, 2, 3):
            raise ValueError('Unsupported artifact schema version')
        return cls(path, manifest)

    @contextmanager
    def execution_lock(self) -> Iterator[None]:
        with (self.path / '.execution.lock').open('a') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError('Another process is executing this experiment') from error
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    @property
    def attempt_count(self) -> int:
        return len(list((self.path / 'attempts').glob('*.started.json')))

    @property
    def task_attempt_count(self) -> int:
        if self.plan.kind == 'demonstration':
            return self.attempt_count
        if self.plan.kind == 'live_experiment':
            from .live_accounting import task_state
            return task_state(self.task_ledger)['used']
        return len(list(self.task_ledger.glob('*.json')))

    def reserve(self, attempt_id: str, request: dict[str, Any]) -> bool:
        """Reserve a provider call, returning false when a shared reservation is recovered."""
        path = self.path / 'attempts' / f'{_safe_id(attempt_id)}.started.json'
        record = {'attempt_id': attempt_id, 'started_at': utc_now(),
                  'request': request, 'status': 'uncertain'}
        if self.plan.kind == 'demonstration':
            self._reserve_demonstration(path, record)
            return True

        if self.plan.kind == 'live_experiment':
            from .live_accounting import reserve
            return reserve(self, path, record)
        return self._reserve_paid_attempt(path, record)

    def _reserve_demonstration(self, path: Path, record: dict[str, Any]) -> None:
        self._check_budget(path)
        write_json_once(path, record)

    def _reserve_paid_attempt(self, path: Path, record: dict[str, Any]) -> bool:
        self.task_ledger.mkdir(parents=True, exist_ok=True)
        with (self.task_ledger / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self._validate_task_ledger()
            shared = self._task_reservation_path(record['attempt_id'])
            if self._recover_bundle_reservation(path, shared):
                return False
            self._check_budget(path)
            if self.task_attempt_count >= self._task_call_limit():
                raise BudgetExceeded('Shared task allowance exhausted; approval required')
            write_json_once(shared, record)
            write_json_once(path, record)
            return True

    def _validate_task_ledger(self) -> None:
        for previous in self.attempts():
            if not self._task_reservation_path(previous['attempt_id']).exists():
                raise ValueError('Task ledger is incomplete; restore it before paid execution')

    def _task_reservation_path(self, attempt_id: str) -> Path:
        return self.task_ledger / f"{self.manifest['experiment_id']}-{attempt_id}.json"

    @staticmethod
    def _recover_bundle_reservation(path: Path, shared: Path) -> bool:
        if shared.exists() and not path.exists():
            # Recover a crash between the task-wide and bundle reservations.
            write_json_once(path, json.loads(shared.read_text()))
            return True
        return False

    def _task_call_limit(self) -> int:
        return 5 if self.plan.kind == 'task_a_diagnostic' else 38

    def _check_budget(self, path: Path) -> None:
        if path.exists():
            raise FileExistsError(path)
        if self.attempt_count >= self.plan.max_calls:
            raise BudgetExceeded('Task call allowance exhausted; obtain approval before more calls')

    def complete(self, attempt_id: str, observation: dict[str, Any]) -> None:
        if not (self.path / 'attempts' / f'{_safe_id(attempt_id)}.started.json').exists():
            raise ValueError('Cannot finish an unreserved attempt')
        write_json_once(self.path / 'attempts' / f'{attempt_id}.finished.json',
                        {**observation, 'attempt_id': attempt_id, 'finished_at': utc_now()})

    def attempts(self) -> list[dict[str, Any]]:
        attempts = []
        for path in sorted((self.path / 'attempts').glob('*.started.json')):
            start = json.loads(path.read_text())
            finish = path.with_name(path.name.replace('.started.', '.finished.'))
            attempts.append({**start, **(json.loads(finish.read_text()) if finish.exists() else {})})
        return attempts

    def attempt(self, attempt_id: str) -> dict[str, Any] | None:
        return next(
            (attempt for attempt in self.attempts() if attempt['attempt_id'] == attempt_id),
            None,
        )

    def save_result(self, result_id: str, result: dict[str, Any]) -> None:
        write_json_once(self._result_path(result_id), result)

    def has_result(self, result_id: str) -> bool:
        return self._result_path(result_id).exists()

    def _result_path(self, result_id: str) -> Path:
        return self.path / 'results' / f'{_safe_id(result_id)}.json'

    def results(self) -> list[dict[str, Any]]:
        from .results import ResearchResult

        return [
            ResearchResult.model_validate_json(path.read_text()).model_dump(mode='json')
            for path in sorted((self.path / 'results').glob('*.json'))
        ]
