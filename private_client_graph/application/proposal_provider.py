"""Pre-dispatch task accounting for authenticated synthetic provider invocations."""

from collections.abc import Callable
from typing import TypeVar
from uuid import uuid4

from private_client_graph.research.artifacts import BudgetExceeded
from private_client_graph.research.live_accounting import reserve_external_attempt

from .proposal_config import ProposalAnalysisConfig
from .proposal_errors import ProposalFailure

_Result = TypeVar('_Result')


def invoke_authorized(config: ProposalAnalysisConfig | None, invoke: Callable[[], _Result]) -> _Result:
    """A task reservation is irreversible, including failed and uncertain dispatches."""
    if config is None or config.task_root is None or config.authorization is None:
        raise _unavailable()
    attempt_id = uuid4().hex
    try:
        reserved = reserve_external_attempt(config.task_root,
            authorization=config.authorization, attempt_id=attempt_id)
    except BudgetExceeded as exc:
        raise ProposalFailure('provider_allowance_exhausted',
            'The approved shared provider allowance is exhausted. No analysis was started.',
            status_code=429) from exc
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise _unavailable() from exc
    if not reserved:
        raise _unavailable()
    return invoke()


def _unavailable() -> ProposalFailure:
    return ProposalFailure('provider_authorization_unavailable',
        'Shared provider authorization is unavailable. No analysis was started.', status_code=503)
