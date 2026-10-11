"""Supported public imports and command entry points survive package moves."""
import subprocess
import sys

import pytest


def test_pipeline_public_exports_are_the_implementation_contracts():
    from private_client_graph import pipeline
    from private_client_graph.pipeline import config, errors, executor, models

    for name, module in [
        ('Pipeline', executor), ('GraphBuilder', executor), ('PipelineConfig', config),
        ('PipelineInput', models), ('PipelineResult', models), ('PipelineExecutionError', errors),
    ]:
        assert getattr(pipeline, name) is getattr(module, name)


def test_legacy_extraction_imports_reexport_the_same_implementations():
    from private_client_graph import extract, extraction
    from private_client_graph.extraction import cli, semantic

    for name in ('EXTRACTION_PROMPT', 'extraction_messages',
                 'build_relationship_extraction_chain', 'extract_relationships_from_text'):
        assert getattr(extract, name) is getattr(semantic, name)
        assert getattr(extraction, name) is getattr(semantic, name)
    assert extract.extract_relationships is cli.extract_relationships
    assert extract.main is cli.main


@pytest.mark.parametrize('module', ['extract', 'evaluate', 'research'])
def test_existing_module_cli_help_needs_no_credentials(module, monkeypatch):
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    result = subprocess.run([sys.executable, '-m', f'private_client_graph.{module}', '--help'],
                            capture_output=True, text=True, check=True)
    assert 'usage:' in result.stdout
    assert not result.stderr
    if module == 'extract':
        assert '--model' in result.stdout
