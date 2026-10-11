import json
import zipfile
from html.parser import HTMLParser

import pytest

from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.fixtures import load_inputs
from private_client_graph.research.plan import ExperimentPlan
from private_client_graph.research.provider import ModelResponse
from private_client_graph.research.runner import execute
from private_client_graph.research.report import render_report
from private_client_graph.research.export import export_bundle, verify_export
from private_client_graph.research.summary import summarize


class Elements(HTMLParser):
    def __init__(self):
        super().__init__(); self.external = []; self.scripts = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script': self.scripts.append(attrs)
        if any(str(attrs.get(k, '')).startswith(('http:', 'https:')) for k in ('src', 'href')):
            self.external.append(attrs)


def test_report_escapes_evidence_is_self_contained_and_exports_roundtrip(tmp_path):
    sample = load_inputs()[-2].model_copy(deep=True)
    sample.source += '\n<script>alert("untrusted")</script>'
    bundle = Bundle.create(tmp_path / 'bundle', ExperimentPlan(inputs=[sample], repetitions=1))
    execute(bundle, provider=lambda request: ModelResponse(payload={'edits': []}, raw_response={'text': sample.source}))
    report = render_report(bundle)
    assert 'Deterministic demonstration' in report
    assert 'Paired extraction sample index' in report
    assert 'valid resolver repetitions' in report
    assert 'valid provider responses' in report
    assert '&lt;script&gt;' in report and '<script>alert' not in report
    parsed = Elements(); parsed.feed(report)
    assert not parsed.external and not parsed.scripts
    (bundle.path / 'report.html').write_text(report)
    (bundle.path / 'summary.json').write_text(json.dumps(summarize(bundle), indent=2) + '\n')
    archive = export_bundle(bundle, tmp_path / 'export.zip')
    assert verify_export(archive)
    with zipfile.ZipFile(archive) as zip_file:
        zip_file.extractall(tmp_path / 'restored')
    restored = Bundle.open(tmp_path / 'restored')
    assert restored.results() == bundle.results()
    assert render_report(restored) == report
    assert (tmp_path / 'restored/CHECKSUMS.json').is_file()


def test_export_requires_rendered_summary_and_html(tmp_path):
    bundle = Bundle.create(
        tmp_path / 'bundle',
        ExperimentPlan(inputs=[load_inputs()[-2]], repetitions=1),
    )

    with pytest.raises(ValueError, match='rendered before export'):
        export_bundle(bundle, tmp_path / 'incomplete.zip')

    assert not (tmp_path / 'incomplete.zip').exists()
