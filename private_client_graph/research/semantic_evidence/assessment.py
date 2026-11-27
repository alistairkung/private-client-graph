"""Freeze the exact DeepSeek assessment and execute only its approved slots."""
import fcntl
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from collections import Counter
from decimal import Decimal
from math import isclose
from collections.abc import Iterator, Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from typing import Any, Literal

import httpx

from private_client_graph.research.artifacts import checksum, dependency_versions, write_json_once
from private_client_graph.research.benchmark_v4 import configured_custody, load_workload
from private_client_graph.research.live_accounting import (
    authorize_external_invocation, finish_external_attempt, read_task,
    reserve_external_attempt, task_lock, task_state,
)
from private_client_graph.research.plan import Pricing
from private_client_graph.research.provider import ModelResponse, ModelSettings, invoke_deepseek_json

from .inputs import EXPECTED_MULTI_SOURCE, EXPECTED_TARGETS, VERSION, AssessmentInputs, Item, extract_inputs
from .judging import Contract, Judgment, SYSTEM_PROMPT, parse_judgment

MODEL = 'deepseek-v4-pro'
BASE_URL: Literal['https://api.deepseek.com'] = 'https://api.deepseek.com'
MAX_CALLS = EXPECTED_TARGETS
MAX_USD = Decimal('2.50')
MAX_INPUT_TOKENS = 12_000
MAX_OUTPUT_TOKENS = 4_000
MESSAGE_FRAMING_ALLOWANCE = 1024

SETTINGS = ModelSettings(model=MODEL, temperature=0)
PRICING = Pricing(model=MODEL, input_per_million=1.32, output_per_million=3.96,
    source_url='https://api-docs.deepseek.com/quick_start/pricing/', retrieved_at='2026-11-27')


class Receipt(Contract):
    request_sha256: str
    latency_seconds: float
    response: ModelResponse | None = None
    provider_error: str | None = None
    provider_status_code: int | None = None


class ReusedJudgment(Contract):
    origin_run: str
    origin_plan_sha256: str
    origin_receipt_sha256: str
    receipt: Receipt


class Plan(Contract):
    version: Literal['pcg-semantic-evidence-equivalence'] = VERSION
    directory: str
    task_id: str
    task_root: str
    task_call_ceiling: int
    inputs: AssessmentInputs
    system_prompt: str
    request_sha256: dict[str, str]
    dependencies: dict[str, str]
    settings: ModelSettings
    base_url: Literal['https://api.deepseek.com'] = BASE_URL
    pricing: Pricing
    reused: dict[str, ReusedJudgment] = {}
    max_calls: int = MAX_CALLS
    max_usd: Decimal = MAX_USD
    max_input_tokens: int = MAX_INPUT_TOKENS
    max_output_tokens: int = MAX_OUTPUT_TOKENS


    @property
    def ledger_root(self) -> Path:
        return Path(self.task_root)

    @property
    def task_limit(self) -> int:
        return self.task_call_ceiling

    @property
    def payable(self) -> tuple[Item, ...]:
        return tuple(item for item in self.inputs.dispatchable if item.id not in self.reused)


def prepare(run_directory: Path, directory: Path, *, task_root: Path, task_call_ceiling: int,
            donors: Sequence[Path] = (), pricing: Pricing = PRICING, max_usd: Decimal = MAX_USD) -> str:
    custody = configured_custody()
    if custody is None:
        raise ValueError('Set PCG_BENCHMARK_V4_CUSTODY to the verified private custody root')
    inputs = extract_inputs(run_directory.resolve(), load_workload(custody))
    return freeze(directory, inputs, task_root=task_root, task_call_ceiling=task_call_ceiling,
                  donors=donors, pricing=pricing, max_usd=max_usd)


def freeze(directory: Path, inputs: AssessmentInputs, *, task_root: Path, task_call_ceiling: int,
           donors: Sequence[Path] = (), pricing: Pricing = PRICING, max_usd: Decimal = MAX_USD) -> str:
    directory = directory.resolve()
    if any(_input_envelope(SYSTEM_PROMPT, item) > MAX_INPUT_TOKENS for item in inputs.dispatchable):
        raise ValueError('A frozen request exceeds the input-token envelope')
    task = read_task(task_root.resolve())
    plan = Plan(directory=str(directory), task_id=task['task_id'], task_root=task['root'],
        task_call_ceiling=task_call_ceiling, inputs=inputs, system_prompt=SYSTEM_PROMPT,
        request_sha256={}, dependencies=dependency_versions(),
        settings=SETTINGS, pricing=pricing, max_usd=max_usd)
    plan = plan.model_copy(update={'request_sha256': {
        item.id: _request_digest(plan, item) for item in inputs.dispatchable}})
    reused = _reuse_judgments(plan, donors)
    plan = plan.model_copy(update={'reused': reused, 'max_calls': len(inputs.dispatchable) - len(reused)})
    _validate_plan(plan)
    # Prepare the lock before publishing a plan so read-only reporting can share it.
    with task_lock(Path(task['ledger'])):
        pass
    with publish_directory(directory) as staging:
        path = staging / 'plan.json'
        write_json_once(path, plan.model_dump(mode='json'))
        digest = checksum(path.read_bytes())
        write_json_once(staging / 'plan-sha256.json', digest)
    return digest


@contextmanager
def publish_directory(directory: Path) -> Iterator[Path]:
    if directory.exists():
        raise FileExistsError(directory)
    with TemporaryDirectory(prefix='.pending-semantic-', dir=directory.parent) as staging:
        path = Path(staging)
        yield path
        os.rename(path, directory)
        fd = os.open(directory.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def open_plan(directory: Path) -> tuple[Plan, str, dict[str, Any]]:
    directory = directory.resolve()
    raw = (directory / 'plan.json').read_bytes()
    digest = checksum(raw)
    if digest != json.loads((directory / 'plan-sha256.json').read_text()):
        raise ValueError('Plan checksum mismatch')
    plan = Plan.model_validate_json(raw)
    task = read_task(plan.ledger_root)
    if plan.directory != str(directory) or plan.task_id != task['task_id'] or directory.stat().st_mode & 0o077:
        raise ValueError('Assessment plan requires its original private directory and task')
    _validate_plan(plan)
    return plan, digest, task


def _validate_plan(plan: Plan) -> None:
    items = plan.inputs.targets
    outcomes = Counter(item.baseline.exact_outcome for item in items)
    multi_source = [item for item in items if item.baseline.joint_only]
    quality = plan.inputs.evidence_quality
    if (len(items) != EXPECTED_TARGETS or len({item.id for item in items}) != len(items)
            or len({(item.condition, item.edge) for item in items}) != len(items)
            or outcomes['complete'] != quality.complete_proof.complete
            or quality.complete_proof.targets != EXPECTED_TARGETS or quality.state != 'complete'
            or len(multi_source) != EXPECTED_MULTI_SOURCE or quality.joint_only_coverage.targets != EXPECTED_MULTI_SOURCE
            or quality.joint_only_coverage.mean is None
            or not isclose(sum(item.baseline.best_exact_pair_coverage for item in multi_source) / EXPECTED_MULTI_SOURCE,
                           quality.joint_only_coverage.mean, abs_tol=1e-12)):
        raise ValueError('Assessment roster differs from the fixed formal-target scope or deterministic baseline')
    if (plan.settings != SETTINGS or plan.system_prompt != SYSTEM_PROMPT
            or plan.pricing.model != MODEL or plan.pricing.currency != 'USD'
            or not plan.max_calls <= plan.task_limit <= 10000
            or plan.max_calls != len(plan.payable) or not plan.reused.keys() <= plan.request_sha256.keys()
            or plan.max_input_tokens != MAX_INPUT_TOKENS or plan.max_output_tokens != MAX_OUTPUT_TOKENS):
        raise ValueError('Assessment differs from the versioned model settings or limits')
    rates = frozen_rates(plan)
    if (not all(rate.is_finite() and rate > 0 for rate in rates) or not plan.max_usd.is_finite()
            or plan.max_usd <= 0 or upper_cost(plan, rates) > plan.max_usd):
        raise ValueError('The estimated maximum cost exceeds the proposed USD ceiling or pricing is invalid')
    for item in plan.inputs.dispatchable:
        if _input_envelope(plan.system_prompt, item) > plan.max_input_tokens:
            raise ValueError('A frozen request exceeds the input-token envelope')
        reused = plan.reused.get(item.id)
        if reused:
            _validate_reuse(plan, item, reused)
    if plan.request_sha256 != {item.id: _request_digest(plan, item) for item in plan.inputs.dispatchable}:
        raise ValueError('Exact request commitment mismatch')


def _user_prompt(item: Item) -> str:
    packet = item.packet
    assert packet is not None
    return packet.model_dump_json()


def _input_envelope(system_prompt: str, item: Item) -> int:
    return len(system_prompt.encode()) + len(_user_prompt(item).encode()) + MESSAGE_FRAMING_ALLOWANCE


def _request_digest(plan: Plan, item: Item) -> str:
    request = {
        'base_url': plan.base_url,
        'settings': plan.settings.model_dump(mode='json'),
        'body': {'messages': [{'role': 'system', 'content': plan.system_prompt},
                              {'role': 'user', 'content': _user_prompt(item)}],
                 'max_tokens': plan.max_output_tokens, 'response_format': {'type': 'json_object'}},
    }
    return checksum(json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def upper_cost(plan: Plan, rates: tuple[Decimal, Decimal]) -> Decimal:
    return plan.max_calls * (
        plan.max_input_tokens * rates[0] + plan.max_output_tokens * rates[1]
    ) / 1_000_000


def frozen_rates(plan: Plan) -> tuple[Decimal, Decimal]:
    return Decimal(str(plan.pricing.input_per_million)), Decimal(str(plan.pricing.output_per_million))


def execute(directory: Path, *, approved_digest: str, approval_reference: str,
            verified_rates: tuple[Decimal, Decimal], api_key: str,
            http_client: httpx.Client | None = None) -> None:
    """Reserve once per frozen item, even across crashes or concurrent starts."""
    directory = directory.resolve()
    plan, digest, task = open_plan(directory)
    if approved_digest != digest or not approval_reference.strip():
        raise ValueError('The frozen plan needs its exact approved digest and approval reference')
    if not plan.payable:
        return
    if not api_key.strip():
        raise ValueError('The approved plan needs a DeepSeek key')
    if (verified_rates != frozen_rates(plan) or upper_cost(plan, verified_rates) > plan.max_usd
            or dependency_versions() != plan.dependencies):
        raise ValueError('Provider pricing, estimated upper cost, or transport environment differs from the approved plan')
    with task_lock(directory):
        reservations = reservation_snapshot(plan, digest, task)
        _require_within_envelope(directory, plan, reservations)
        authority = _execution_authority(task, plan, digest, approval_reference.strip())
        for item in plan.payable:
            if item.id not in reservations.ids:
                _dispatch(directory, plan, authority, item, api_key.strip(), http_client)


def _dispatch(directory: Path, plan: Plan, authority: str, item: Item,
              api_key: str, http_client: httpx.Client | None) -> None:
    lock = _attempt_lock(directory, item)
    lock.parent.mkdir(mode=0o700, exist_ok=True)
    with lock.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        if not reserve_external_attempt(plan.ledger_root, authorization=authority, attempt_id=item.id):
            return
        receipt = _invoke(plan, item, api_key, http_client)
        _save_receipt(directory, plan, authority, item, receipt)
        if receipt.provider_status_code in (401, 402, 403, 404):
            raise ValueError(f'DeepSeek access failed (HTTP {receipt.provider_status_code}). Further dispatch stopped')
        if receipt.response is not None and exceeded_envelope(plan, receipt.response):
            raise ValueError('Reported token usage exceeded the approved envelope. Further dispatch stopped')


def _execution_authority(task: dict[str, Any], plan: Plan,
                         digest: str, approval_reference: str) -> str:
    purpose = f'{VERSION} {digest}'
    authority = _recorded_authority(task, plan, digest)
    if authority is None:
        authority = authorize_external_invocation(plan.ledger_root, purpose=purpose, task_cap=plan.task_limit,
            invocation_cap=plan.max_calls, approval_reference=approval_reference)
    if authority['approval_reference'] != approval_reference:
        raise ValueError('Continuation must use the recorded approval reference')
    authorization = authority['authorization']
    path = plan.ledger_root / 'external-invocations' / authorization / 'authorization.json'
    if not path.exists():
        # Finish publication after a crash that retained shared authority only.
        write_json_once(path, authority)
    return authorization


def _recorded_authority(task: dict[str, Any], plan: Plan, digest: str) -> dict[str, Any] | None:
    paths = (Path(task['ledger']) / 'authorizations').glob('*.json')
    records = [(path.stem, json.loads(path.read_text())) for path in paths]
    matching = [(identity, record) for identity, record in records if record.get('purpose') == f'{VERSION} {digest}']
    if not matching:
        return None
    if len(matching) != 1:
        raise ValueError('The assessment must retain one fixed authorization')
    identity, record = matching[0]
    if (record['authorization'] != identity or record['kind'] != 'external'
            or record['task_id'] != plan.task_id
            or record['task_cap'] != plan.task_limit or record['invocation_cap'] != plan.max_calls):
        raise ValueError('Recorded authority does not match the exact plan and limits')
    return record


@dataclass(frozen=True)
class ReservationSnapshot:
    authorization: str | None
    ids: frozenset[str]


def reservation_snapshot(plan: Plan, digest: str, task: dict[str, Any]) -> ReservationSnapshot:
    ledger = Path(task['ledger'])
    # All writes to the task ledger hold the opposing exclusive lock.
    with (ledger / '.lock').open('rb') as stream:
        fcntl.flock(stream, fcntl.LOCK_SH)
        used = task_state(ledger)['used']
        authority = _recorded_authority(task, plan, digest)
        if authority is None:
            if _has_retained_attempt(plan, digest, ledger):
                raise ValueError('Semantic Evidence attempts are missing their retained authorization')
            return ReservationSnapshot(None, frozenset())
        prefix = authority['authorization']
        paths = (ledger / 'reservations').glob(f'{prefix}-*.json')
        ids = frozenset(path.stem.removeprefix(f'{prefix}-') for path in paths)
        if len(ids) > used or not ids <= {item.id for item in plan.payable}:
            raise ValueError('Assessment ledger differs from the retained reservations')
        return ReservationSnapshot(prefix, ids)


def _has_retained_attempt(plan: Plan, digest: str, ledger: Path) -> bool:
    if any((Path(plan.directory) / 'receipts').glob('*.json')):
        return True
    purpose = f'{VERSION} {digest}'
    return any(json.loads(path.read_text()).get('purpose') == purpose
               for path in (ledger / 'reservations').glob('*.json'))


def _attempt_lock(directory: Path, item: Item) -> Path:
    return directory / 'active-attempts' / f'{item.id}.lock'


def execution_active(directory: Path, item: Item) -> bool:
    try:
        with _attempt_lock(directory, item).open('rb') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            fcntl.flock(stream, fcntl.LOCK_UN)
    except FileNotFoundError:
        pass
    return False


def _invoke(plan: Plan, item: Item, api_key: str, http_client: httpx.Client | None) -> Receipt:
    started = monotonic()
    request_sha256 = plan.request_sha256[item.id]
    try:
        response = invoke_deepseek_json(plan.system_prompt, _user_prompt(item), settings=plan.settings,
            max_output_tokens=plan.max_output_tokens, api_key=api_key, base_url=plan.base_url,
            http_client=http_client)
    except Exception as error:
        status_code = getattr(error, 'status_code', None)
        return Receipt(request_sha256=request_sha256, latency_seconds=monotonic() - started,
                       provider_error=type(error).__name__,
                       provider_status_code=status_code if isinstance(status_code, int) else None)
    return Receipt(request_sha256=request_sha256, latency_seconds=monotonic() - started, response=response)


def exceeded_envelope(plan: Plan, response: ModelResponse) -> bool:
    return ((response.usage.input_tokens or 0) > plan.max_input_tokens
            or (response.usage.output_tokens or 0) > plan.max_output_tokens)


def _receipt_path(directory: Path, item: Item) -> Path:
    return directory / 'receipts' / f'{item.id}.json'


def _save_receipt(directory: Path, plan: Plan, authority: str, item: Item, receipt: Receipt) -> None:
    path = _receipt_path(directory, item)
    write_json_once(path, receipt.model_dump(mode='json'))
    response = receipt.response
    error_type = receipt.provider_error
    if response is not None:
        try:
            validate_judge_response(plan, item, response)
        except ValueError:
            error_type = 'InvalidJudgment'
    finish_external_attempt(plan.ledger_root, authorization=authority, attempt_id=item.id,
        outcome='failed' if error_type else 'completed', error_type=error_type,
        usage=response.usage if response else None, returned_model=response.returned_model if response else None,
        artifact_sha256=checksum(path.read_bytes()))


def read_receipt(directory: Path, plan: Plan, item: Item, snapshot: ReservationSnapshot) -> Receipt | None:
    if item.id not in snapshot.ids:
        return None
    path = _receipt_path(directory, item)
    sealed = (plan.ledger_root / 'external-invocations' / str(snapshot.authorization)
              / 'attempts' / f'{item.id}.finished.json')
    if not sealed.is_file():
        return None
    raw = path.read_bytes()
    if json.loads(sealed.read_text()).get('artifact_sha256') != checksum(raw):
        raise ValueError('Provider receipt differs from the sealed completion record')
    receipt = Receipt.model_validate_json(raw)
    if receipt.request_sha256 != plan.request_sha256[item.id]:
        raise ValueError('Provider receipt differs from the frozen request commitment')
    if (receipt.response is None) == (receipt.provider_error is None):
        raise ValueError('Provider receipt must contain a response or an error')
    return receipt


def validate_judge_response(plan: Plan, item: Item, response: ModelResponse) -> Judgment:
    if response.returned_model != plan.settings.model:
        raise ValueError('Provider did not return the frozen judge model')
    if exceeded_envelope(plan, response):
        raise ValueError('Reported token usage exceeded the approved envelope')
    packet = item.packet
    assert packet is not None
    return parse_judgment(packet, response)


def _require_within_envelope(directory: Path, plan: Plan, reservations: ReservationSnapshot) -> None:
    for item in plan.payable:
        receipt = read_receipt(directory, plan, item, reservations)
        if receipt is None and _receipt_path(directory, item).exists():
            raise ValueError('A retained receipt lacks its completion seal. Further dispatch stopped')
        if receipt and receipt.response and exceeded_envelope(plan, receipt.response):
            raise ValueError('Reported token usage exceeded the approved envelope. Further dispatch stopped')


def _reuse_judgments(plan: Plan, donors: Sequence[Path]) -> dict[str, ReusedJudgment]:
    reused: dict[str, ReusedJudgment] = {}
    for directory in sorted(set(donors)):
        origin, digest, task = open_plan(directory)
        if (origin.inputs.evidence_quality.scope_sha256 != plan.inputs.evidence_quality.scope_sha256
                or origin.inputs.evidence_quality.qualified_reference_sha256
                != plan.inputs.evidence_quality.qualified_reference_sha256
                or origin.inputs.evidence_quality.observation_origin != plan.inputs.evidence_quality.observation_origin):
            raise ValueError('Judgment reuse requires the same frozen Benchmark v4 scope and observation origin')
        reservations = reservation_snapshot(origin, digest, task)
        source_items = {item.id: item for item in origin.inputs.dispatchable}
        for item in plan.inputs.dispatchable:
            donor = source_items.get(item.id)
            if (item.id in reused or donor is None or donor.source_ids != item.source_ids
                    or origin.request_sha256[donor.id] != plan.request_sha256[item.id]):
                continue
            existing = origin.reused.get(item.id)
            if existing is None:
                receipt = read_receipt(directory, origin, donor, reservations)
                if receipt is None:
                    continue
                existing = ReusedJudgment(origin_run=origin.inputs.extractor_run, origin_plan_sha256=digest,
                    origin_receipt_sha256=checksum(_receipt_path(directory, donor).read_bytes()), receipt=receipt)
            try:
                _validate_reuse(plan, item, existing)
            except ValueError:
                continue
            reused[item.id] = existing
    return reused


def _validate_reuse(plan: Plan, item: Item, reused: ReusedJudgment) -> None:
    receipt = reused.receipt
    if (receipt.request_sha256 != plan.request_sha256[item.id] or receipt.response is None
            or receipt.provider_error is not None):
        raise ValueError('Reused judgment does not match the frozen request')
    validate_judge_response(plan, item, receipt.response)
