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
from .plan import ExperimentPlan
from .provider import RESOLUTION_PROMPT
from private_client_graph.extract import EXTRACTION_PROMPT


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
    paths += sorted((ROOT / 'private_client_graph/models').glob('*.py'))
    paths += sorted((ROOT / 'private_client_graph/research').glob('*.py'))
    return {str(p.relative_to(ROOT)): p.read_text() for p in paths}


def dependency_versions() -> dict[str, str]:
    packages = ('pydantic', 'pydantic-core', 'langchain-core', 'langchain-deepseek',
                'langchain-openai', 'openai', 'langsmith', 'httpx', 'httpcore')
    return {package: importlib.metadata.version(package) for package in packages}


def _provenance() -> dict[str, Any]:
    def git(*args: str) -> str | None:
        result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
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
        self.plan = ExperimentPlan.model_validate(manifest['plan'])
        self.task_ledger = Path(manifest['task_ledger'])

    @classmethod
    def create(cls, path: Path, plan: ExperimentPlan, *, task_ledger: Path | None = None) -> "Bundle":
        path.mkdir(parents=True, exist_ok=False)
        manifest = {'schema_version': 1, 'experiment_id': uuid4().hex,
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
        if manifest['schema_version'] != 1:
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
        return len(list(self.task_ledger.glob('*.json')))

    def reserve(self, attempt_id: str, request: dict[str, Any]) -> None:
        path = self.path / 'attempts' / f'{_safe_id(attempt_id)}.started.json'
        record = {'attempt_id': attempt_id, 'started_at': utc_now(),
                  'request': request, 'status': 'uncertain'}
        if self.plan.kind == 'demonstration':
            self._check_budget(path)
            write_json_once(path, record)
            return
        self.task_ledger.mkdir(parents=True, exist_ok=True)
        with (self.task_ledger / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for previous in self.attempts():
                reservation = self.task_ledger / f"{self.manifest['experiment_id']}-{previous['attempt_id']}.json"
                if not reservation.exists():
                    raise ValueError('Task ledger is incomplete; restore it before paid execution')
            shared = self.task_ledger / f"{self.manifest['experiment_id']}-{attempt_id}.json"
            if shared.exists() and not path.exists():
                # Recover a crash between the task-wide and bundle reservations.
                write_json_once(path, json.loads(shared.read_text()))
            self._check_budget(path)
            limit = 5 if self.plan.kind == 'task_a_diagnostic' else 38
            if self.task_attempt_count >= limit:
                raise BudgetExceeded('Shared task allowance exhausted; approval required')
            write_json_once(shared, record)
            write_json_once(path, record)

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

    def save_result(self, result_id: str, result: dict[str, Any]) -> None:
        write_json_once(self.path / 'results' / f'{_safe_id(result_id)}.json', result)

    def results(self) -> list[dict[str, Any]]:
        return [json.loads(p.read_text()) for p in sorted((self.path / 'results').glob('*.json'))]
