"""Enable tracing only for frozen Workbench inputs verified against synthetic fixtures."""
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from langfuse import Langfuse
from langfuse.span_filter import is_langfuse_span
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.research.tracing import ResearchTracing, best_effort

from .case_catalog import frozen_case_metadata, repository_inputs


@contextmanager
def workbench_tracing(bundle: Bundle) -> Iterator[ResearchTracing | None]:
    tracing = best_effort(lambda: _configured_tracing(bundle))
    try:
        yield tracing
    finally:
        if tracing is not None:
            # The worker exits after one invocation. Export after authoritative writes.
            best_effort(tracing.client.flush)


def _configured_tracing(bundle: Bundle) -> ResearchTracing | None:
    plan = bundle.plan
    if not isinstance(plan, RunPlan) or not plan.run_id or not plan.experiment_id:
        return None
    if os.getenv('PCG_RESEARCH_LANGFUSE_ENABLED') not in (None, '1'):
        return None

    local = dotenv_values(Path('.env'), interpolate=False)
    if os.environ.get('PCG_RESEARCH_LANGFUSE_ENABLED', local.get('PCG_RESEARCH_LANGFUSE_ENABLED')) != '1':
        return None
    settings = {key: os.environ.get(key, local.get(key)) for key in (
        'LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY', 'LANGFUSE_BASE_URL',
        'PCG_RESEARCH_LANGFUSE_DETAILS',
    )}
    public, secret, base_url = (settings[key] for key in (
        'LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY', 'LANGFUSE_BASE_URL',
    ))
    if not public or not secret or not base_url:
        return None
    endpoint = urlsplit(base_url)
    if (endpoint.scheme != 'https' or not endpoint.hostname or endpoint.username is not None
            or endpoint.password is not None or endpoint.query or endpoint.fragment):
        return None

    synthetic = _verified_inputs(plan)
    if not synthetic:
        return None
    # Avoid inheriting process-wide telemetry resource attributes.
    resource = Resource({'service.name': 'pcg-research-workbench'})
    client = Langfuse(public_key=public, secret_key=secret, base_url=base_url,
        tracer_provider=TracerProvider(resource=resource), should_export_span=is_langfuse_span, timeout=3)
    return ResearchTracing(client, synthetic, detailed=settings['PCG_RESEARCH_LANGFUSE_DETAILS'] == '1')


def _verified_inputs(plan: RunPlan) -> frozenset[str]:
    planned = [sample.sample_id for sample in plan.inputs]
    catalog = {sample.sample_id: sample for sample in repository_inputs(input_ids=planned) if sample.cohort == 'authored'}
    matched = [sample for sample in plan.inputs if catalog.get(sample.sample_id) == sample]
    metadata = frozen_case_metadata(matched)
    return frozenset(sample.sample_id for sample in matched
        if metadata[sample.sample_id] == plan.case_metadata.get(sample.sample_id))
