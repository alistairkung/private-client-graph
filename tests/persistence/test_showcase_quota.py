from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from private_client_graph.persistence.showcase_quota import claim_slot, quota_reset


def test_fixed_utc_windows_persist_claims_and_roll_over(database):
    now = datetime(2026, 10, 4, 12, 0, 15, tzinfo=timezone.utc)
    reset = datetime(2026, 10, 4, 12, 1, tzinfo=timezone.utc)
    assert quota_reset(limit=2, window_seconds=60, at=now) is None
    assert claim_slot(limit=2, window_seconds=60, at=now) is None
    assert claim_slot(limit=2, window_seconds=60, at=now) is None
    assert claim_slot(limit=2, window_seconds=60, at=now) == reset
    assert quota_reset(limit=2, window_seconds=60, at=now) == reset
    assert quota_reset(limit=2, window_seconds=60, at=reset) is None
    assert claim_slot(limit=2, window_seconds=60, at=reset) is None


def test_competing_postgresql_claims_cannot_exceed_allowance(database):
    now = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(
            lambda _: claim_slot(limit=3, window_seconds=3600, at=now), range(24)
        ))
    assert results.count(None) == 3


def test_claim_survives_a_new_process(database):
    import subprocess
    import sys

    now = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)
    assert claim_slot(limit=1, window_seconds=3600, at=now) is None
    result = subprocess.run([sys.executable, "-c", '''
from datetime import datetime, timezone
from private_client_graph.persistence.showcase_quota import claim_slot
assert claim_slot(limit=1, window_seconds=3600,
                  at=datetime(2026, 10, 4, 12, tzinfo=timezone.utc)) == datetime(2026, 10, 4, 13, tzinfo=timezone.utc)
'''], check=False)
    assert result.returncode == 0
