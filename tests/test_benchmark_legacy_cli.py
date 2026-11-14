"""The legacy reproduction command writes a new score and preserves attribution boundaries."""
import json
import subprocess
import sys

from private_client_graph.research.fixtures import ROOT


def test_reproduce_committed_score_in_new_destination(tmp_path):
    case = ROOT / 'benchmark_v1/authority/dev/case_1'
    output = tmp_path / 'score.json'
    command = [sys.executable, str(ROOT / 'benchmark_v1/evaluate_case.py'), str(case),
               str(case / 'expected_extraction.json'), '--output', str(output)]
    subprocess.run(command, check=True, capture_output=True)
    original = output.read_bytes()
    assert json.loads(original) == json.loads((case / 'expected_extraction.evaluation.json').read_bytes())
    repeated = subprocess.run(command, capture_output=True, text=True)
    assert repeated.returncode != 0
    assert 'FileExistsError' in repeated.stderr
    assert output.read_bytes() == original


def test_legacy_command_rejects_attributed_candidates(tmp_path):
    case = ROOT / 'benchmark_v1/authority/dev/case_1'
    output = tmp_path / 'score.json'
    result = subprocess.run([sys.executable, str(ROOT / 'benchmark_v1/evaluate_case.py'), str(case),
        str(case / 'expected_source_extraction.json'), '--output', str(output)], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Source-attributed replay' in result.stderr
    assert not output.exists()
