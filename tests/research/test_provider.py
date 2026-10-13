import json

import httpx
import pytest

from private_client_graph.research.fixtures import load_inputs
from private_client_graph.research.provider import ModelRequest, ModelSettings, invoke_deepseek


def test_real_sdk_sends_only_source_candidates_and_preserves_usage_and_raw_response():
    sample = load_inputs()[-2]
    requests = []

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        assert body['model'] == 'deepseek-flash'
        assert body['thinking'] == {'type': 'disabled'}
        data = json.loads(body['messages'][1]['content'])
        assert data == {'source': sample.source, 'extraction': sample.extraction.model_dump()}
        assert 'annotations' not in data and 'truth' not in data
        tool = body['tools'][0]['function']['name']
        return httpx.Response(200, json={
            'id': 'recorded_response', 'model': 'deepseek-flash', 'object': 'chat.completion', 'created': 0,
            'choices': [{'index': 0, 'finish_reason': 'tool_calls', 'message': {'role': 'assistant', 'content': '',
                'tool_calls': [{'id': 'edit', 'type': 'function', 'function': {'name': tool, 'arguments': '{"edits": []}'}}]}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 10, 'total_tokens': 110,
                      'prompt_cache_hit_tokens': 20, 'prompt_cache_miss_tokens': 80},
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = invoke_deepseek(ModelRequest(stage='resolution', source=sample.source,
            extraction=sample.extraction, settings=ModelSettings()), api_key='test-only', http_client=client)
    assert len(requests) == 1
    assert result.payload == {'edits': []}
    assert result.usage.input_tokens == 100
    assert result.usage.cached_tokens == 20
    assert result.usage.output_tokens == 10
    assert result.raw_response['response_metadata']['model_name'] == 'deepseek-flash'


def test_bad_structured_output_keeps_raw_message_and_does_not_retry():
    sample = load_inputs()[-2]
    calls = []

    def respond(request):
        calls.append(request)
        tool = json.loads(request.content)['tools'][0]['function']['name']
        return httpx.Response(200, json={
            'id': 'broken', 'model': 'deepseek-flash', 'object': 'chat.completion', 'created': 0,
            'choices': [{'index': 0, 'finish_reason': 'tool_calls', 'message': {'role': 'assistant', 'content': '',
                'tool_calls': [{'id': 'edit', 'type': 'function', 'function': {'name': tool, 'arguments': '{"edits": "wrong"}'}}]}}],
            'usage': {'prompt_tokens': 20, 'completion_tokens': 5, 'total_tokens': 25}})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = invoke_deepseek(ModelRequest(stage='resolution', source=sample.source,
            extraction=sample.extraction, settings=ModelSettings()), api_key='secret', http_client=client)
    assert len(calls) == 1
    assert result.payload is None and result.error_type == 'ValidationError'
    assert result.raw_response['tool_calls'][0]['args'] == {'edits': 'wrong'}
    assert result.usage.input_tokens == 20


def test_persistable_response_uses_safe_fields_and_redacts_credentials():
    sample = load_inputs()[-2]
    api_key = 'credential-that-must-not-persist'

    def respond(request):
        body = json.loads(request.content)
        tool = body['tools'][0]['function']['name']
        return httpx.Response(200, json={
            'id': f'response-{api_key}',
            'model': f'model-{api_key}',
            'object': 'chat.completion',
            'created': 0,
            'system_fingerprint': f'fingerprint-{api_key}',
            'authorization': f'Bearer {api_key}',
            'choices': [{'index': 0, 'finish_reason': 'tool_calls', 'message': {
                'role': 'assistant', 'content': '',
                'tool_calls': [{'id': 'edit', 'type': 'function', 'function': {
                    'name': tool,
                    'arguments': json.dumps({'edits': [{
                        'candidate_index': 1,
                        'endpoint': 'source_name',
                        'name': api_key,
                    }]})}}],
            }}],
            'usage': {'prompt_tokens': 20, 'completion_tokens': 5, 'total_tokens': 25},
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = invoke_deepseek(
            ModelRequest(stage='resolution', source=sample.source,
                         extraction=sample.extraction, settings=ModelSettings()),
            api_key=api_key,
            http_client=client,
        )

    persisted = result.model_dump_json()
    assert api_key not in persisted
    assert '[redacted]' in persisted
    assert 'authorization' not in persisted.lower()
    assert set(result.raw_response) == {
        'content', 'id', 'tool_calls', 'invalid_tool_calls', 'response_metadata'
    }
    assert set(result.raw_response['response_metadata']) <= {
        'finish_reason', 'id', 'model_name', 'system_fingerprint'
    }


def test_extraction_uses_original_prompt_and_exact_source_and_transport_never_retries():
    from private_client_graph.extract import EXTRACTION_PROMPT
    calls = []
    def respond(request):
        calls.append(request)
        body = json.loads(request.content)
        assert body['messages'] == [{'role': 'system', 'content': EXTRACTION_PROMPT},
                                    {'role': 'user', 'content': 'Exact {Source}\n'}]
        return httpx.Response(429, json={'error': {'message': 'rate limited'}})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(Exception):
            invoke_deepseek(ModelRequest(stage='extraction', source='Exact {Source}\n', settings=ModelSettings()),
                            api_key='secret', http_client=client)
    assert len(calls) == 1
