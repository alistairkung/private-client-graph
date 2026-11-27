"""Read-only adapter for the exact first live Benchmark v3 archive."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from benchmark_v3 import commissioning
from benchmark_v3.batch.artifacts import read_bytes
from benchmark_v3.evaluation_protocol import (
    GRAPH_SCORER, PlannedCondition, ProtocolResult, evaluate_protocol,
)
from benchmark_v3.replay_manifest import VerifiedFamily, load_family
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.research.artifacts import Bundle, checksum
from private_client_graph.research.provider import ModelRequest, request_messages
from private_client_graph.research.retained_inputs import value_digest
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.pipeline import Pipeline, PipelineConfig, PipelineExecutionError


BASELINE_INVENTORY_SHA256 = 'b41242bd7bcfec25c09396b197f887441e11dccc0dff3aa920017fc6c18cdbab'


@dataclass(frozen=True)
class VerifiedBaseline:
    """Verified source records needed by read-only consumers of the baseline."""

    protocol: ProtocolResult
    planned: tuple[PlannedCondition, ...]
    predictions: dict[str, SourcedExtractionResult]
    original_results: dict[str, ResearchResult]
    family_details: dict[str, VerifiedFamily]


def evaluate_first_live_baseline(archive: Path, private_admissions: Path) -> ProtocolResult:
    """Verify the original archive and re-score its preserved live predictions offline."""
    return verify_first_live_baseline(archive, private_admissions).protocol


def verify_first_live_custody(archive: Path, private_admissions: Path) -> None:
    """Check retained commitments and receipt provenance without re-running scoring."""
    archive = archive.resolve()
    inventory = _verified_inventory(archive)
    configuration = _read(archive / 'CONFIGURATION.json')
    run = _read(archive / 'RUN.json')
    if run['configuration_sha256'] != inventory['CONFIGURATION.json']:
        raise ValueError('Run and configuration commitments differ')
    run_id = run['id']
    if f'{run_id}/manifest.json' not in inventory:
        raise ValueError('Run manifest is outside the retained inventory')
    bundle = Bundle.open(archive / run_id)
    public = commissioning._read_json(commissioning.trusted_bytes('admissions/2026-11-24.json'))
    admission_bytes = read_bytes(private_admissions.resolve())
    benchmark_digest = checksum(admission_bytes)
    if benchmark_digest != public['private_register_sha256'] or benchmark_digest != configuration['benchmark_digest']:
        raise ValueError('Private admission register differs from the frozen benchmark')
    planned = list(_admitted_conditions(public, commissioning._read_json(admission_bytes)))
    _verify_planned_inputs(bundle, planned, configuration)
    attempts = {attempt['attempt_id']: attempt for attempt in bundle.attempts()}
    retained = {row['sample_id']: ResearchResult.model_validate(row) for row in bundle.results()}
    for item in planned:
        sample = f'{item.frozen.sample_id}_fresh_01'
        attempt = attempts.pop(f'{sample}-extraction')
        original = retained.pop(sample)
        _verified_prediction(item, attempt, original, configuration,
                             bundle.manifest['provenance']['prompts']['sourced_extraction'])
    if attempts or retained:
        raise ValueError('Unplanned attempts or results in retained archive')


def verify_first_live_baseline(archive: Path, private_admissions: Path) -> VerifiedBaseline:
    """Verify the archive and return records for a typed, read-only inspection view."""
    archive = archive.resolve()
    inventory = _verified_inventory(archive)
    configuration = _read(archive / 'CONFIGURATION.json')
    run = _read(archive / 'RUN.json')
    if run['configuration_sha256'] != inventory['CONFIGURATION.json']:
        raise ValueError('Run and configuration commitments differ')
    run_id = run['id']
    if f'{run_id}/manifest.json' not in inventory:
        raise ValueError('Run manifest is outside the retained inventory')
    bundle = Bundle.open(archive / run_id)
    provenance = bundle.manifest['provenance']
    plan = bundle.plan
    if (
        not isinstance(plan, RunPlan) or plan.execution_mode != 'live' or plan.input_mode != 'fresh'
        or plan.resolver != 'none' or plan.evaluator_version != GRAPH_SCORER
        or provenance['git_sha'] != configuration['code_commit']
        or provenance['prompt_hashes']['sourced_extraction'] != configuration['prompt_sha256']
    ):
        raise ValueError('Retained run does not match the frozen configuration')

    _verify_scoring_code(configuration, provenance)
    public = commissioning._read_json(commissioning.trusted_bytes('admissions/2026-11-24.json'))
    admission_bytes = read_bytes(private_admissions.resolve())
    benchmark_digest = checksum(admission_bytes)
    if benchmark_digest != public['private_register_sha256'] or benchmark_digest != configuration['benchmark_digest']:
        raise ValueError('Private admission register differs from the frozen benchmark')
    family_details = _admitted_families(public, commissioning._read_json(admission_bytes))
    planned = [PlannedCondition(family, frozen)
               for family, detail in family_details.items() for frozen in detail.conditions.values()]
    _verify_planned_inputs(bundle, planned, configuration)

    attempts = {attempt['attempt_id']: attempt for attempt in bundle.attempts()}
    retained = {row['sample_id']: ResearchResult.model_validate(row) for row in bundle.results()}
    predictions = {}
    original_results = {}
    for item in planned:
        condition = item.frozen.saved.condition
        sample = f'{item.frozen.sample_id}_fresh_01'
        attempt = attempts.pop(f'{sample}-extraction')
        original = retained.pop(sample)
        predictions[condition] = _verified_prediction(
            item, attempt, original, configuration, provenance['prompts']['sourced_extraction'],
        )
        original_results[condition] = original
    if attempts or retained:
        raise ValueError('Unplanned attempts or results in retained archive')

    result = evaluate_protocol(planned, predictions, benchmark_sha256=benchmark_digest,
                               observation_origin='live', run_artifact_sha256=BASELINE_INVENTORY_SHA256)
    for condition, row in result.conditions.items():
        original = original_results[condition]
        expected = 'scored' if original.status == 'completed' else 'validation_failure'
        if row.outcome != expected or row.graph != original.evaluation:
            raise ValueError(f'{condition}: protected scorer or construction no longer reproduces the baseline')
        item = next(item for item in planned if item.frozen.saved.condition == condition)
        try:
            constructed = Pipeline(PipelineConfig()).run_from_sourced_extraction(
                item.frozen.sources, predictions[condition],
            )
        except PipelineExecutionError as error:
            if (row.outcome != 'validation_failure' or error.stage != 'graph'
                    or not isinstance(error.__cause__, ValueError)
                    or original.state is not None or original.graph is not None
                    or row.failure_detail != str(error.__cause__)):
                raise ValueError(f'{condition}: retained failure differs from deterministic construction') from error
        else:
            if (row.outcome != 'scored' or original.state != constructed.state
                    or original.graph != constructed.graph
                    or reconstruct_graph(original.state) != original.graph):
                raise ValueError(f'{condition}: retained canonical state differs from deterministic construction')
    return VerifiedBaseline(result, tuple(planned), predictions, original_results, family_details)


def _verify_scoring_code(configuration: dict, provenance: dict) -> None:
    repository = Path(__file__).resolve().parents[1]
    for name, expected in configuration['scorer_files'].items():
        if checksum(read_bytes(repository / name)) != expected:
            raise ValueError(f'Protected scorer differs from the baseline: {name}')
    for name in (
        'private_client_graph/graph.py',
        'private_client_graph/canonical_state.py',
        'private_client_graph/pipeline/config.py',
        'private_client_graph/pipeline/executor.py',
    ):
        if read_bytes(repository / name).decode() != provenance['code'][name]:
            raise ValueError(f'Graph construction differs from the baseline: {name}')


def _verified_inventory(archive: Path) -> dict[str, str]:
    content = read_bytes(archive / 'CHECKSUMS.json')
    if checksum(content) != BASELINE_INVENTORY_SHA256:
        raise ValueError('Baseline archive inventory commitment differs')
    inventory: dict[str, str] = commissioning._read_json(content)
    for name, expected in inventory.items():
        if checksum(read_bytes(archive / name)) != expected:
            raise ValueError(f'Baseline archive artifact differs: {name}')
    return inventory


def load_admitted_families(private_admissions: Path) -> dict[str, VerifiedFamily]:
    """Verify the frozen cohort independently of any model or retained Run."""
    public = commissioning._read_json(commissioning.trusted_bytes('admissions/2026-11-24.json'))
    admission_bytes = read_bytes(private_admissions)
    if checksum(admission_bytes) != public['private_register_sha256']:
        raise ValueError('Private admission register differs from the frozen benchmark')
    return _admitted_families(public, commissioning._read_json(admission_bytes))


def _admitted_conditions(public: dict, private: dict) -> Iterator[PlannedCondition]:
    for family, verified in _admitted_families(public, private).items():
        for frozen in verified.conditions.values():
            yield PlannedCondition(family, frozen)


def _admitted_families(public: dict, private: dict) -> dict[str, VerifiedFamily]:
    families: dict[str, VerifiedFamily] = {}
    for entry in public['families']:
        family = entry['family']
        admitted = private['families'][family]
        dossier = Path(admitted['custody_locator'])
        if admitted['status'] != 'admitted' or checksum(read_bytes(dossier)) != entry['technical_dossier_sha256']:
            raise ValueError(f'{family}: final admitted dossier differs')
        verified = load_family(dossier.parent / 'manifest.json')
        if (
            verified.family != family or verified.manifest_sha256 != entry['manifest_sha256']
            or verified.freeze_sha256 != entry['freeze_sha256']
            or set(verified.conditions) != set(entry['conditions'])
        ):
            raise ValueError(f'{family}: frozen manifest differs from admission')
        for condition in entry['conditions']:
            frozen = verified.conditions[condition]
            expected = admitted['condition_details'][condition]
            if (
                frozen.case_sha256 != expected['key_file_sha256']
                or frozen.sources_sha256 != expected['ordered_sources_sha256']
                or frozen.annotation_sha256 != expected['annotation_sha256']
                or len(frozen.sources) != expected['source_count']
            ):
                raise ValueError(f'{condition}: frozen Sources or key differ from admission')
        families[family] = verified
    return families


def _verify_planned_inputs(bundle: Bundle, planned: list[PlannedCondition], configuration: dict) -> None:
    if len(planned) != 34 or len({row.family for row in planned}) != 19:
        raise ValueError('Expected 34 conditions in the 19 admitted development families')
    if len(bundle.plan.inputs) != len(planned) or bundle.plan.fresh_extractions != 1:
        raise ValueError('Retained plan does not have one extraction per admitted condition')
    for item, template in zip(planned, bundle.plan.inputs, strict=True):
        frozen = item.frozen
        commitment = configuration['condition_commitments'][frozen.saved.condition]
        if (
            template.sample_id != frozen.sample_id or template.case_id != item.family
            or template.sources != frozen.sources or template.truth != frozen.saved.truth
            or commitment['family'] != item.family or commitment['condition'] != frozen.case_sha256
            or commitment['ordered_sources'] != frozen.sources_sha256
        ):
            raise ValueError(f'{frozen.saved.condition}: retained plan or configuration differs')


def _verified_prediction(
    item: PlannedCondition, attempt: dict, original: ResearchResult, configuration: dict, prompt: str,
) -> SourcedExtractionResult:
    condition = item.frozen.saved.condition
    request = ModelRequest.model_validate(attempt['request'])
    if (
        request.stage != 'extraction' or request.sources != item.frozen.sources or request.source
        or value_digest([('system', prompt), request_messages(request)[1]])
        != configuration['request_message_hashes'][condition]
        or request.settings.model_dump(mode='json') != configuration['settings']
    ):
        raise ValueError(f'{condition}: retained request does not match its frozen commitments')
    response = attempt['response']
    tool_calls = response['raw_response']['tool_calls']
    payload = response['payload']
    if (
        attempt['status'] != 'completed' or response['error_type'] is not None or len(tool_calls) != 1
        or tool_calls[0]['args'] != payload or original.case_id != item.family
        or original.status not in {'completed', 'graph_error'}
    ):
        raise ValueError(f'{condition}: retained prediction record does not match the baseline')
    prediction = SourcedExtractionResult.model_validate(payload)
    if prediction != original.sourced_extraction:
        raise ValueError(f'{condition}: retained parsed prediction differs from runner output')
    return prediction


def _read(path: Path) -> dict:
    value = commissioning._read_json(read_bytes(path))
    if not isinstance(value, dict):
        raise ValueError(f'Expected an object in {path.name}')
    return value
