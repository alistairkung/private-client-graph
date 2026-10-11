"""Artifact-authoritative workspace identity, draft revisions and Run membership."""
import fcntl
import json
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from uuid import NAMESPACE_URL, uuid5

from private_client_graph.research.artifacts import checksum, utc_now, write_json_once
from .workspace_contracts import CreateExperiment, DraftUpdate, RunDraft, WorkspaceDetail


@contextmanager
def workspace_lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.workspaces.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def experiment_path(root: Path, identity: str) -> Path:
    if not re.fullmatch('[a-f0-9]{32}', identity):
        raise ValueError('Invalid Experiment identity')
    path = root / 'experiments' / identity
    if path.is_symlink() or (root / 'experiments').is_symlink():
        raise ValueError('Symlink workspaces are unsupported')
    return path


def create_experiment(root: Path, command: CreateExperiment) -> WorkspaceDetail:
    identity = uuid5(NAMESPACE_URL, 'pcg-experiment:' + command.request_id).hex
    path = experiment_path(root, identity)
    with workspace_lock(root):
        artifact = path / 'workspace.json'
        if artifact.exists():
            previous = read_record(artifact)
            if previous['command'] != command.model_dump():
                raise ValueError('Idempotency key was already used for another Experiment')
        else:
            write_record(artifact, {'schema_version': 1, 'id': identity,
                'created_at': utc_now(), 'command': command.model_dump(),
                'initial_draft': RunDraft().model_dump(mode='json')})
        return read_experiment(root, identity)


def read_experiment(root: Path, identity: str) -> WorkspaceDetail:
    path = experiment_path(root, identity)
    value = read_record(path / 'workspace.json')
    if value['schema_version'] != 1 or value['id'] != identity:
        raise ValueError('Unsupported or mismatched Experiment artifact')
    command = CreateExperiment.model_validate(value['command'])
    draft = RunDraft.model_validate(value['initial_draft'])
    revisions = sorted((path / 'drafts').glob('*.json'))
    for revision, record in enumerate(revisions, start=1):
        updated = RunDraft.model_validate(read_record(record)['draft'])
        if updated.revision != revision:
            raise ValueError('Draft revision history is incomplete')
        draft = updated
    memberships = []
    for record in (path / 'runs').glob('*.json'):
        membership = read_record(record)
        if membership.get('experiment_id') != identity or membership.get('run_id') != record.stem or not re.fullmatch('[a-f0-9]{32}', record.stem):
            raise ValueError('Run membership identity mismatch')
        memberships.append(membership)
    runs = [record['run_id'] for record in sorted(memberships, key=lambda record: record['created_at'])]
    if len(runs) != len(set(runs)):
        raise ValueError('Duplicate Run membership')
    return WorkspaceDetail(id=identity, name=command.name, hypothesis=command.hypothesis,
        description=command.description, created_at=value['created_at'], draft=draft, run_ids=runs)


def update_draft(root: Path, identity: str, command: DraftUpdate, *, copied_from: str | None = None) -> RunDraft:
    with workspace_lock(root):
        return save_draft(root, identity, command, copied_from=copied_from)


def save_draft(root: Path, identity: str, command: DraftUpdate, *, copied_from: str | None = None) -> RunDraft:
    """Publish one revision while the caller holds the workspace command lock."""
    path = experiment_path(root, identity)
    payload = {'command': command.model_dump(mode='json'), 'copied_from': copied_from}
    for record in (path / 'drafts').glob('*.json'):
        previous = read_record(record)
        if previous['command']['request_id'] == command.request_id:
            if any(previous[key] != value for key, value in payload.items()):
                raise ValueError('Idempotency key was already used for another draft command')
            return RunDraft.model_validate(previous['draft'])
    current = read_experiment(root, identity).draft
    if command.expected_revision != current.revision:
        raise ValueError('Draft revision changed; review the current draft')
    updated = RunDraft(revision=current.revision + 1, configuration=command.configuration,
                       copied_from_run=copied_from)
    write_record(path / 'drafts' / f'{updated.revision:08d}.json',
                    {**payload, 'draft': updated.model_dump(mode='json')})
    return updated


def write_record(path: Path, value: dict) -> None:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    write_json_once(path, {'record': value, 'checksum': checksum(encoded)})


def read_record(path: Path) -> dict:
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError('Symlink workspace records are unsupported')
    value = json.loads(path.read_text())
    if not isinstance(value, dict) or not isinstance(value.get('record'), dict):
        raise ValueError('Invalid workspace record')
    record = value['record']
    encoded = json.dumps(record, sort_keys=True, ensure_ascii=False).encode()
    if value.get('checksum') != checksum(encoded):
        raise ValueError('Workspace record checksum mismatch')
    return record
