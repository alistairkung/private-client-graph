import json
import subprocess
import sys

from private_client_graph.research.cli import main


def test_offline_cli_plans_executes_renders_and_exports_without_credentials(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    bundle = tmp_path / 'demo'
    main(['plan', str(bundle), '--kind', 'demonstration', '--samples', 'alias_merge,alias_distinct'])
    main(['run', str(bundle)])
    main(['render', str(bundle)])
    archive = tmp_path / 'portable.zip'
    main(['export', str(bundle), str(archive)])
    assert (bundle / 'report.html').is_file()
    assert (bundle / 'summary.json').is_file()
    assert archive.is_file()
    summary = json.loads((bundle / 'summary.json').read_text())
    assert summary['operations']['paid_attempts'] == 0
    assert summary['operations']['attempted'] == 6
    assert 'Deterministic demonstration' in (bundle / 'report.html').read_text()
