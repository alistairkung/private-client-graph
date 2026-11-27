import json

import pytest
from fastapi.testclient import TestClient

from private_client_graph.research.artifacts import checksum
from private_client_graph.research.retained_inputs import value_digest
from private_client_graph.workbench.api import create_app


_ROUTE = '/api/research/v1/exploratory-workload'
_TOKEN = 'fixture-token-for-local-owner-only'
_AUTH = ('owner', _TOKEN)
_LOCAL = ('127.0.0.1', 50000)


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    directory = tmp_path / 'workload'
    directory.mkdir(mode=0o700)
    sources = [
        {'id': f'doc-{index}', 'title': f'Document {index}', 'text': f'Example body {index}.'}
        for index in range(65)
    ]

    def write(sources, **fields):
        content = json.dumps(sources).encode()
        digest = value_digest(sources)
        manifest = {
            'schema_version': 1,
            'workload_id': f'exploratory-scale-65-{digest[:12]}',
            'workload_kind': 'exploratory_scale',
            'qualification': 'unqualified',
            'read_only': True,
            'scored': False,
            'source_count': 65,
            'source_file_sha256': checksum(content),
            'source_array_sha256': digest,
        } | fields
        encoded = json.dumps(manifest).encode()
        for name, data in [('sources.json', content), ('manifest.json', encoded)]:
            path = directory / name
            path.write_bytes(data)
            path.chmod(0o600)
        monkeypatch.setenv('PCG_EXPLORATORY_WORKLOAD_DIR', str(directory))
        monkeypatch.setenv('PCG_EXPLORATORY_MANIFEST_SHA256', checksum(encoded))
        monkeypatch.setenv('PCG_EXPLORATORY_ACCESS_TOKEN', _TOKEN)
        return manifest

    return directory, sources, write


def test_owner_inspects_exact_ordered_sources_without_run_capability(bundle):
    _, sources, write = bundle
    manifest = write(sources)
    client = TestClient(create_app(), client=_LOCAL)
    assert client.get(_ROUTE).status_code == 401
    assert client.get(f'{_ROUTE}/sources', auth=('owner', 'incorrect')).status_code == 401

    metadata = client.get(_ROUTE, auth=_AUTH)
    assert metadata.json() == manifest
    assert metadata.headers['cache-control'] == 'no-store'
    detail = client.get(f'{_ROUTE}/sources', auth=_AUTH)
    assert detail.json() == {'manifest': manifest, 'sources': sources}
    assert detail.headers['cache-control'] == 'no-store'
    assert client.post(_ROUTE, auth=_AUTH).status_code == 405
    assert client.get('/api/research/v1/capabilities', auth=_AUTH).status_code == 404
    existing_cases = TestClient(create_app(show_exploratory=False)).get('/api/research/v2/cases').json()
    assert client.get('/api/research/v2/cases', auth=_AUTH).json() == existing_cases

    external = TestClient(create_app(), client=('192.0.2.4', 50000))
    assert external.get(f'{_ROUTE}/sources', auth=_AUTH).status_code == 403
    assert client.get(_ROUTE, auth=_AUTH, headers={'Host': 'untrusted.example'}).status_code == 400


def test_execution_composition_does_not_expose_workload(bundle, tmp_path, monkeypatch):
    _, sources, write = bundle
    write(sources)
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(tmp_path / 'execution-artifacts'))
    from private_client_graph.workbench.execution_api import create_execution_app

    client = TestClient(create_execution_app(), client=_LOCAL)
    assert client.get(_ROUTE).status_code == 404
    assert client.get(f'{_ROUTE}/sources', auth=_AUTH).status_code == 404


def test_manifest_and_source_mutation_are_rejected_without_leaking_paths(bundle):
    directory, sources, write = bundle
    write(sources)
    client = TestClient(create_app(), client=_LOCAL)
    for name in ('manifest.json', 'sources.json'):
        path = directory / name
        original = path.read_bytes()
        path.write_bytes(original + b' ')
        response = client.get(f'{_ROUTE}/sources', auth=_AUTH)
        assert response.status_code == 409
        assert response.json() == {'detail': 'The released exploratory workload could not be verified.'}
        path.write_bytes(original)
    (directory / 'answer-key.json').write_text('private')
    assert client.get(_ROUTE, auth=_AUTH).status_code == 409


@pytest.mark.parametrize('problem', ['scored', 'extra_source_field', 'duplicate_id', 'missing_source', 'symlink'])
def test_export_shape_is_enforced_separately_from_digests(bundle, problem):
    directory, sources, write = bundle
    fields = {}
    if problem == 'scored':
        fields['scored'] = True
    elif problem == 'extra_source_field':
        sources[0]['answer'] = 'disallowed'
    elif problem == 'duplicate_id':
        sources[1]['id'] = sources[0]['id']
    elif problem == 'missing_source':
        sources.pop()
    write(sources, **fields)
    if problem == 'symlink':
        original = directory / 'sources.json'
        target = directory.parent / 'elsewhere.json'
        original.rename(target)
        original.symlink_to(target)
    client = TestClient(create_app(), client=_LOCAL)
    assert client.get(f'{_ROUTE}/sources', auth=_AUTH).status_code == 409
