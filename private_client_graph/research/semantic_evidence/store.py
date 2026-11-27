"""Locate one assessment per Run alongside the private Workbench artifacts."""
import json
import re
from pathlib import Path

from private_client_graph.research.artifacts import Bundle, checksum, write_json_once
from private_client_graph.research.live_accounting import initialize_task, read_task, task_lock

from .assessment import BASELINE_PLAN_SHA256, open_plan, publish_directory
from .inputs import EXTRACTOR_MANIFEST_SHA256, EXTRACTOR_RUN

TASK_LABEL = 'Semantic Evidence provider accounting'


def task_root(root: Path) -> Path:
    return root / 'semantic-evidence'


def initialize(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir() or root.stat().st_mode & 0o077:
        raise ValueError('Semantic Evidence requires the private Research artifact directory')
    directory = task_root(root)
    directory.mkdir(mode=0o700, exist_ok=True)
    with task_lock(directory):
        if (directory / 'live-task.json').exists():
            return read_task(directory)
        existing = list((directory / 'task-ledgers').glob('live-*'))
        if not existing:
            return initialize_task(directory, TASK_LABEL)
        return _recover_task_registration(directory, existing)


def _recover_task_registration(directory: Path, candidates: list[Path]) -> dict:
    if len(candidates) != 1 or (directory / 'external-invocations').exists():
        raise ValueError('The Semantic Evidence task registry is incomplete; restore it from custody')
    ledger, = candidates
    if set(path.name for path in ledger.iterdir()) != {'task.json'}:
        raise ValueError('The Semantic Evidence task registry has retained state; restore it from custody')
    record = json.loads((ledger / 'task.json').read_text())
    if (record.get('version') != 1 or record.get('label') != TASK_LABEL or record.get('task_id') != ledger.name
            or record.get('root') != str(directory) or record.get('ledger') != str(ledger)):
        raise ValueError('The incomplete Semantic Evidence task record does not match its original location')
    write_json_once(directory / 'live-task.json', record)
    return read_task(directory)


def entry(root: Path, run_id: str) -> Path:
    if not re.fullmatch(r'[a-f0-9]{32}', run_id):
        raise ValueError('Invalid Benchmark v4 Run ID')
    return task_root(root) / run_id


def find(root: Path, run_id: str) -> Path | None:
    directory = entry(root, run_id)
    legacy = directory / 'retained-assessment.json'
    has_plan = (directory / 'plan.json').is_file() and (directory / 'plan-sha256.json').is_file()
    if not has_plan and not legacy.is_file():
        return None
    path = directory
    if legacy.is_file():
        link = json.loads(legacy.read_text())
        path = Path(link['directory'])
        if has_plan or run_id != EXTRACTOR_RUN or link['plan_sha256'] != BASELINE_PLAN_SHA256:
            raise ValueError('Invalid retained assessment registration')
        if checksum((path / 'plan.json').read_bytes()) != BASELINE_PLAN_SHA256:
            raise ValueError('Retained assessment differs from the registered baseline')
    plan, _, _ = open_plan(path)
    bundle = Bundle.open(root / run_id)
    if (plan.inputs.extractor_run != run_id
            or plan.inputs.extractor_manifest_sha256 != checksum((bundle.path / 'manifest.json').read_bytes())):
        raise ValueError('Semantic Evidence is bound to a different Benchmark v4 Run')
    return path


def require(root: Path, run_id: str) -> Path:
    path = find(root, run_id)
    if path is None:
        raise ValueError(f'No Semantic Evidence assessment for Run {run_id}')
    return path


def register_baseline(root: Path, original: Path) -> Path:
    root, original = root.resolve(), original.resolve()
    plan, digest, _ = open_plan(original)
    bundle = Bundle.open(root / EXTRACTOR_RUN)
    if (digest != BASELINE_PLAN_SHA256 or plan.inputs.extractor_run != EXTRACTOR_RUN
            or plan.inputs.extractor_manifest_sha256 != EXTRACTOR_MANIFEST_SHA256
            or checksum((bundle.path / 'manifest.json').read_bytes()) != EXTRACTOR_MANIFEST_SHA256):
        raise ValueError('The completed Extractor v1 Run and retained assessment do not match')
    directory = entry(root, EXTRACTOR_RUN)
    directory.parent.mkdir(mode=0o700, exist_ok=True)
    with publish_directory(directory) as staging:
        write_json_once(staging / 'retained-assessment.json', {'directory': str(original), 'plan_sha256': digest})
    return directory
