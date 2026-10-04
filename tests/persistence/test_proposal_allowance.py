from datetime import datetime, timezone


def test_proposal_attempts_use_separate_persistent_fixed_windows(database):
    from private_client_graph.persistence.proposal_allowance import claim_slot, quota_reset
    from private_client_graph.persistence.showcase_quota import claim_slot as showcase_claim

    now = datetime(2026, 10, 5, 12, 0, 15, tzinfo=timezone.utc)
    reset = datetime(2026, 10, 5, 12, 1, tzinfo=timezone.utc)
    assert quota_reset(limit=2, window_seconds=60, at=now) is None
    assert claim_slot(limit=2, window_seconds=60, at=now) is None
    assert claim_slot(limit=2, window_seconds=60, at=now) is None
    assert claim_slot(limit=2, window_seconds=60, at=now) == reset
    assert quota_reset(limit=2, window_seconds=60, at=now) == reset
    assert showcase_claim(limit=1, window_seconds=60, at=now) is None
    assert claim_slot(limit=2, window_seconds=60, at=reset) is None


def test_competing_authenticated_attempts_cannot_exceed_allowance(database):
    from concurrent.futures import ThreadPoolExecutor
    from private_client_graph.persistence.proposal_allowance import claim_slot

    now = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: claim_slot(limit=3, window_seconds=3600, at=now), range(24)))
    assert results.count(None) == 3


def test_authenticated_allowance_survives_new_process(database):
    import subprocess
    import sys
    from private_client_graph.persistence.proposal_allowance import claim_slot

    now = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)
    assert claim_slot(limit=1, window_seconds=3600, at=now) is None
    subprocess.run([sys.executable, "-c", '''
from datetime import datetime, timezone
from private_client_graph.persistence.proposal_allowance import claim_slot
assert claim_slot(limit=1, window_seconds=3600,
                  at=datetime(2026, 10, 5, 12, tzinfo=timezone.utc)) == datetime(2026, 10, 5, 13, tzinfo=timezone.utc)
'''], check=True)
