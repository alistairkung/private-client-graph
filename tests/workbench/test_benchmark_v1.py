"""Deterministic package admission and retained Workbench replay for benchmark v1."""
import hashlib
import json
import shutil

import pytest

from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import build_graph
from private_client_graph.models import ExtractionResult, SourcedExtractionResult
from private_client_graph.pipeline import Pipeline, PipelineConfig
from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.fixtures import ROOT
from private_client_graph.research.source_attribution import diagnose_source_attribution
from private_client_graph.research.runner import execute
from private_client_graph.workbench.case_catalog import default_input_ids, load_case_catalog, repository_inputs
from private_client_graph.workbench.run_inspection import read_run
from private_client_graph.workbench.run_planning import freeze_run, preview_run
from private_client_graph.workbench.workspace_contracts import CreateExperiment, DraftUpdate, FreezeRun, RunConfiguration
from private_client_graph.workbench.workspaces import create_experiment, update_draft


AXES = ('aliases', 'authority', 'cross_source', 'distractors', 'hallucination', 'temporal')
SPLITS = ('dev', 'held_out')
DEFAULTS = [f'case_{index:02d}_fixture' for index in range(1, 6)]
LEGACY_SCORES = {
    'case_01_fixture': (6, 0, 0, 6, 0),
    'case_02_fixture': (10, 0, 0, 10, 0),
    'case_03_fixture': (6, 1, 1, 6, 0),
    'case_03_historical': (7, 0, 0, 7, 0),
    'alias_merge': (1, 1, 1, 1, 0),
    'alias_distinct': (2, 0, 0, 2, 0),
    'case_04_fixture': (7, 0, 0, 7, 0),
    'case_05_fixture': (6, 0, 0, 6, 0),
    **{f'heldout_{index:02d}_fixture': (count, 0, 0, count, 0)
       for index, count in enumerate((5, 4, 3, 3, 4, 3, 6, 5, 3, 3), start=1)},
}


def case_id(axis, split):
    return f'benchmark_v1_{axis}_{split}_1'


def normalized_source_text(text):
    return text.replace('\r\n', '\n').strip()


@pytest.fixture(scope='module')
def samples():
    return {sample.sample_id: sample for sample in repository_inputs()}


def test_catalog_preserves_legacy_identities_defaults_and_requires_new_case_opt_in(samples):
    catalog = {row.id: row for row in load_case_catalog()}
    expected_new = {f'{case_id(axis, split)}_fixture' for axis in AXES for split in SPLITS}
    assert set(samples) == set(LEGACY_SCORES) | expected_new
    assert set(catalog) == set(samples)
    assert default_input_ids() == DEFAULTS
    assert RunConfiguration().input_ids == DEFAULTS
    assert catalog['case_03_historical'].kind == 'historical'
    for split in SPLITS:
        rows = [catalog[f'{case_id(axis, split)}_fixture'] for axis in AXES]
        assert {row.kind for row in rows} == {'diagnostic' if split == 'dev' else 'heldout'}
        assert all(row.metadata_available and row.axis in AXES and row.split == split for row in rows)


@pytest.mark.parametrize('axis', AXES)
@pytest.mark.parametrize('split', SPLITS)
def test_complete_package_has_explicit_identity_files_and_two_perfect_ideals(samples, axis, split):
    identity = case_id(axis, split)
    directory = ROOT / 'benchmark_v1' / axis / split / 'case_1'
    sample = samples[f'{identity}_fixture']
    metadata = json.loads((directory / 'metadata.json').read_text())
    assert (sample.case_id, metadata['id'], metadata['axis'], metadata['split']) == (identity, identity, axis, split)
    assert metadata['matter_family'] == f'benchmark_v1_{axis}_1'
    assert all(isinstance(metadata[field], str) and metadata[field].strip()
               for field in ('name', 'description'))
    manifest = json.loads((directory / 'sources.json').read_text())
    assert manifest and len({item['id'] for item in manifest}) == len(manifest)
    assert len(sample.sources) == len(manifest) == (2 if axis in ('authority', 'cross_source', 'temporal') else 1)
    reconstructed = '\n\n'.join(normalized_source_text(source.text) for source in sample.sources)
    matches_compatibility_source = normalized_source_text(sample.source) == reconstructed
    assert matches_compatibility_source
    assert len({item['path'] for item in manifest}) == len(manifest)
    for record, source in zip(manifest, sample.sources):
        path = (directory / record['path']).resolve()
        assert path.is_relative_to(directory.resolve())
        raw = path.read_bytes()
        # Keep held-out material opaque in failure reports.
        assert all((source.id == record['id'], source.title == record['title'], source.text == raw.decode()))
        assert sample.origin_hashes[record['path']] == hashlib.sha256(raw).hexdigest()
    for filename in ('sources.json', 'expected_source_extraction.json', 'source_evidence.json'):
        assert sample.origin_hashes[filename] == hashlib.sha256((directory / filename).read_bytes()).hexdigest()
    legacy = ExtractionResult.model_validate_json((directory / 'expected_extraction.json').read_text())
    attributed = SourcedExtractionResult.model_validate_json((directory / 'expected_source_extraction.json').read_text())
    projection = [item.model_dump(exclude={'source_id'}) for item in attributed.relationships]
    assert all((projection == legacy.model_dump()['relationships'], legacy == sample.extraction,
                attributed == sample.sourced_extraction))
    legacy_graph = build_graph(legacy.relationships, document='source.txt', source_text=sample.source)
    output = Pipeline(PipelineConfig()).run_from_sourced_extraction(sample.sources, attributed)
    for graph in (legacy_graph, output.graph):
        score = evaluate_graph(graph, sample.truth)
        assert (score.tp, score.fp, score.fn, score.f1, score.provenance_accuracy) == (
            len(sample.truth.relationships), 0, 0, 1, 1)
    snapshot = json.loads((directory / 'expected_extraction.evaluation.json').read_text())
    matches_snapshot = evaluate_graph(legacy_graph, sample.truth).model_dump(mode='json') == snapshot
    assert matches_snapshot
    attribution = diagnose_source_attribution(output.state, sample.truth, sample.source_evidence)
    assert attribution.assessed > 0
    assert (attribution.failed, attribution.accuracy) == (0, 1)


@pytest.mark.parametrize('identity,expected', LEGACY_SCORES.items())
def test_legacy_scores_remain_unchanged(samples, identity, expected):
    sample = samples[identity]
    graph = build_graph(sample.extraction.relationships, document='source.txt', source_text=sample.source)
    legacy = evaluate_graph(graph, sample.truth)
    assert (legacy.tp, legacy.fp, legacy.fn, legacy.provenance_passed, legacy.provenance_failed) == expected
    if sample.sources is not None:
        output = Pipeline(PipelineConfig()).run_from_sourced_extraction(sample.sources, sample.sourced_extraction)
        sourced = evaluate_graph(output.graph, sample.truth)
        same_evaluation = sourced.model_dump() == legacy.model_dump()
        assert same_evaluation


def forbidden_provider(request):
    pytest.fail('Saved no-resolution replay must make zero provider calls')


def test_all_six_dev_cases_survive_normal_freeze_execute_reopen_and_source_inspection(tmp_path, samples):
    identities = [f'{case_id(axis, "dev")}_fixture' for axis in AXES]
    workspace = create_experiment(tmp_path, CreateExperiment(request_id='benchmark-v1', name='Synthetic dev replay'))
    configuration = RunConfiguration(input_ids=identities, input_mode='saved', resolver='none', execution_mode='replay')
    preview = preview_run(configuration, tmp_path)
    assert (preview.matrix_call_maximum, preview.planned_observations) == (0, 6)
    update_draft(tmp_path, workspace.id, DraftUpdate(request_id='select', expected_revision=0, configuration=configuration))
    frozen = freeze_run(tmp_path, workspace.id, FreezeRun(request_id='freeze', expected_revision=1))
    bundle = Bundle.open(tmp_path / frozen.id)
    assert [sample.sample_id for sample in bundle.plan.inputs] == identities
    execute(bundle, provider=forbidden_provider)
    reopened = Bundle.open(tmp_path / frozen.id)
    execute(reopened, provider=forbidden_provider)
    assert reopened.attempt_count == 0
    assert len(reopened.results()) == 6
    detail = read_run(tmp_path, workspace.id, frozen.id)
    aggregate = detail.evaluation.aggregate
    assert aggregate.state == 'complete'
    assert aggregate.coverage.model_dump() == dict(planned=6, scored=6, pending=0, failed=0, uncertain=0, unavailable=0)
    assert (aggregate.tp, aggregate.fp, aggregate.fn, aggregate.f1) == (
        sum(len(samples[identity].truth.relationships) for identity in identities), 0, 0, 1)
    assert detail.evaluation.cost.total == 0
    assert len(detail.observations) == 6
    for observation in detail.observations:
        sample = samples[observation.sample_id]
        assert observation.metadata.id == sample.sample_id
        assert observation.sources == sample.sources
        assert observation.result.source_attribution.accuracy == 1
        assert observation.relationships and all(row.outcome == 'matched' for row in observation.relationships)
        sources = {source.id: source.text for source in observation.sources}
        for relationship in observation.relationships:
            assert relationship.expected and relationship.predicted
            for quote in relationship.expected + relationship.predicted:
                assert quote.source_id in sources and quote.occurrences
                assert all(sources[quote.source_id][start:end] == quote.text for start, end in quote.occurrences)
    assert read_run(tmp_path, workspace.id, frozen.id).artifact_digest == detail.artifact_digest


@pytest.fixture
def package_copy(tmp_path):
    # The public loader requires the legacy controls; copy no held-out packages.
    shutil.copytree(ROOT / 'cases', tmp_path / 'cases')
    shutil.copytree(ROOT / 'research' / 'fixtures', tmp_path / 'research' / 'fixtures')
    directory = tmp_path / 'benchmark_v1' / 'cross_source' / 'dev' / 'case_1'
    shutil.copytree(ROOT / 'benchmark_v1' / 'cross_source' / 'dev' / 'case_1', directory)
    return tmp_path, directory


@pytest.mark.parametrize('filename', ['sources.json', 'expected_source_extraction.json', 'source_evidence.json'])
def test_incomplete_package_is_rejected_during_catalog_admission(package_copy, filename):
    root, directory = package_copy
    (directory / filename).unlink()
    with pytest.raises((OSError, ValueError)):
        load_case_catalog(root)


@pytest.mark.parametrize('defect', ['missing_source', 'duplicate_source', 'escaping_source', 'unknown_source', 'projection'])
def test_malformed_source_bundle_is_rejected_during_catalog_admission(package_copy, defect):
    root, directory = package_copy
    manifest_path = directory / 'sources.json'
    manifest = json.loads(manifest_path.read_text())
    if defect == 'missing_source':
        (directory / manifest[0]['path']).unlink()
    elif defect == 'duplicate_source':
        manifest.append(manifest[0])
        manifest_path.write_text(json.dumps(manifest))
    elif defect == 'escaping_source':
        manifest[0]['path'] = '../outside.txt'
        manifest_path.write_text(json.dumps(manifest))
    else:
        path = directory / 'expected_source_extraction.json'
        extraction = json.loads(path.read_text())
        if defect == 'unknown_source':
            extraction['relationships'][0]['source_id'] = 'absent'
        else:
            extraction['relationships'].pop()
        path.write_text(json.dumps(extraction))
    with pytest.raises((OSError, ValueError)):
        load_case_catalog(root)


@pytest.mark.parametrize('field,value,message', [
    ('id', 'benchmark_v1_other_dev_1', 'Invalid benchmark_v1 case identity'),
    ('split', '', 'Axis or split mismatch'),
    ('axis', '', 'Axis or split mismatch'),
    ('matter_family', '', 'Missing matter family'),
])
def test_inconsistent_metadata_is_rejected_during_catalog_admission(package_copy, field, value, message):
    root, directory = package_copy
    path = directory / 'metadata.json'
    metadata = json.loads(path.read_text())
    metadata[field] = value
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match=message):
        load_case_catalog(root)


def test_duplicate_case_identity_is_rejected_during_catalog_admission(package_copy):
    root, directory = package_copy
    shutil.copytree(directory, root / 'cases' / case_id('cross_source', 'dev'))
    with pytest.raises(ValueError, match='Duplicate case identity'):
        load_case_catalog(root)


@pytest.mark.parametrize('axis,edge', [
    ('authority', ('Alice Chen', 'parent_of', 'Bob Chen')),
    ('cross_source', ('Alice Chen', 'parent_of', 'Bob Chen')),
    ('hallucination', ('Gregory Ashby', 'sibling_of', 'Margaret Ashby')),
])
def test_dev_answer_key_retains_factual_relationships_inside_proposed_actions(samples, axis, edge):
    sample = samples[f'{case_id(axis, "dev")}_fixture']
    names = {entity.id: entity.name for entity in sample.truth.entities}
    edges = {(names[item.source], item.type, names[item.target]) for item in sample.truth.relationships}
    assert edge in edges
    if axis == 'authority':
        assert ('Bob Chen', 'beneficiary_of', 'Evergreen Family Trust') not in edges
    if axis == 'hallucination':
        assert ('James Ashby', 'beneficiary_of', 'Ashby Family Trust') not in edges
        assert ('Margaret Ashby', 'trustee_of', 'Ashby Family Trust') not in edges


def test_alias_dev_source_supplies_full_name_used_by_the_ideal(samples):
    sample = samples[f'{case_id("aliases", "dev")}_fixture']
    quote = 'They have one child, Daniel Wu, known to the family as Daniel.'
    assert quote in sample.source
    assert any(quote in source.text for source in sample.sources)
    parents = [item for item in sample.sourced_extraction.relationships if item.relationship_type == 'parent_of']
    assert len(parents) == 2
    assert all(item.target_name == 'Daniel Wu' and item.supporting_text == quote for item in parents)
