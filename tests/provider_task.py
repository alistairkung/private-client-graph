"""Explicit disposable authorization for substituted-provider tests only."""

from pathlib import Path

from private_client_graph.research.live_accounting import authorize_external_invocation, initialize_task


def substituted_provider_settings(root: Path) -> dict[str, str]:
    initialize_task(root, 'Deterministic substituted provider task')
    authority = authorize_external_invocation(root, purpose='Substituted provider acceptance',
        task_cap=30, invocation_cap=30, approval_reference='deterministic-tests-only')
    return {'PCG_PROVIDER_TASK_ROOT': str(root), 'PCG_PROVIDER_AUTHORIZATION': authority['authorization']}
