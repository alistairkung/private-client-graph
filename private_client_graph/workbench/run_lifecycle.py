"""Read retained lifecycle events without loading execution machinery."""
import json

from private_client_graph.research.artifacts import Bundle


def latest_event(bundle: Bundle) -> dict:
    events = [json.loads(path.read_text()) for path in (bundle.path / 'lifecycle').glob('*.json')]
    return max(events, key=lambda event: event['at']) if events else {
        'state': 'frozen', 'message': 'Frozen plan; execution has not started.', 'invocation': ''}


def can_archive(bundle: Bundle, state: str) -> bool:
    if state == 'failed':
        return True
    return state in ('frozen', 'stopped', 'interrupted') and not bundle.results()
