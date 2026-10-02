from pathlib import Path
import shutil

import pytest

from private_client_graph.evaluate import main
from private_client_graph.models import EvaluationResult


def test_saved_run_evaluation_is_persisted_without_overwriting(tmp_path, monkeypatch, capsys):
    case = Path(__file__).resolve().parents[1] / "cases" / "case_01"
    shutil.copytree(case, tmp_path / "cases" / "case_01")
    run = tmp_path / "runs" / "case_01" / "2026-10-02T075056.json"
    run.parent.mkdir(parents=True)
    original = (case / "expected_extraction.json").read_bytes()
    run.write_bytes(original)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["evaluate", str(run)])

    main()

    output = run.with_suffix(".evaluation.json")
    saved = output.read_text(encoding="utf-8")
    assert saved == capsys.readouterr().out
    result = EvaluationResult.model_validate_json(saved)
    assert (result.tp, result.fp, result.fn) == (6, 0, 0)
    assert result.provenance_accuracy == 1.0
    assert run.read_bytes() == original
    with pytest.raises(FileExistsError):
        main()
    assert output.read_text(encoding="utf-8") == saved
