"""Portable artifact export remains independent of retired HTML rendering."""
import json
import zipfile

import pytest

from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.fixtures import load_inputs
from private_client_graph.research.plan import ExperimentPlan
from private_client_graph.research.provider import ModelResponse
from private_client_graph.research.runner import execute
from private_client_graph.research.export import export_bundle, verify_export
from private_client_graph.research.summary import summarize


def test_summary_only_export_roundtrip_preserves_observations(tmp_path):
    sample = load_inputs()[-2].model_copy(deep=True)
    sample.source += '\n<script>alert("untrusted")</script>'
    bundle = Bundle.create(tmp_path / 'bundle', ExperimentPlan(inputs=[sample], repetitions=1))
    execute(bundle, provider=lambda request: ModelResponse(payload={'edits': []}, raw_response={'text': sample.source}))
    (bundle.path / 'summary.json').write_text(json.dumps(summarize(bundle), indent=2) + '\n')
    archive = export_bundle(bundle, tmp_path / 'export.zip')
    assert verify_export(archive)
    with zipfile.ZipFile(archive) as zip_file:
        zip_file.extractall(tmp_path / 'restored')
    restored = Bundle.open(tmp_path / 'restored')
    assert restored.results() == bundle.results()
    assert (tmp_path / 'restored/CHECKSUMS.json').is_file()


def test_export_requires_summary(tmp_path):
    bundle = Bundle.create(tmp_path / 'bundle', ExperimentPlan(inputs=[load_inputs()[-2]], repetitions=1))
    with pytest.raises(ValueError, match='summarized before export'):
        export_bundle(bundle, tmp_path / 'incomplete.zip')
    assert not (tmp_path / 'incomplete.zip').exists()
