# Offline validation

The isolated Architect's final turn returned JSON. The original packet was rejected because one URL fell outside the staged allowlist. The original [receipt](packets/planning/receipt.json) and [response](packets/planning/output-captured.txt) are preserved. A [custodian recovery record](packets/planning/custodian-validation.json) binds the correction and result. Run this verification from the repository root at the reviewed revision.

```bash
uv run python - <<'PY'
import json
from pathlib import Path

from benchmark_v3 import commissioning
from benchmark_v3.batch.authorisation import verify_portfolio
from benchmark_v3.portfolio import Portfolio
from benchmark_v3.research_contracts import PlanningRecord

plan = Path("benchmark_v3/planning/development-20")
packet = plan / "packets" / "planning"
recovery = json.loads((packet / "custodian-validation.json").read_bytes())
handoff = (packet / "handoff.json").read_bytes()
receipt = (packet / "receipt.json").read_bytes()
raw = (packet / "output-captured.txt").read_bytes()
assert commissioning.digest(handoff) == recovery["handoff_sha256"]
assert commissioning.digest(receipt) == recovery["runner_receipt_sha256"]
assert commissioning.digest(raw) == recovery["original_model_output_sha256"]
assert json.loads(receipt)["status"] == "rejected"
before = recovery["correction"]["before"].encode()
after = recovery["correction"]["after"].encode()
assert raw.count(before) == 1
corrected = raw.replace(before, after, 1)
assert commissioning.digest(corrected) == recovery["corrected_model_output_sha256"]
result = commissioning.validate_architect_result(corrected.decode(), json.loads(handoff)["research"])
round_bytes = Path("benchmark_v3/planning/rounds/2026-11-23-development-20.json").read_bytes()
assert commissioning.digest(round_bytes) == recovery["normalized_planning_record_sha256"]
record = PlanningRecord.model_validate_json(round_bytes)
assert result == record.result
assert record.provenance.output_sha256 == commissioning.digest(raw)
verify_portfolio(Portfolio.model_validate_json((plan / "portfolio.json").read_bytes()))
for hypothesis in record.result.proposals:
    reference = commissioning.hypothesis_ref(hypothesis, record.provenance)
    key = f"{reference.hypothesis_id}@{reference.revision}"
    assert commissioning.proposal_history()[key][:2] == (hypothesis, reference)
PY
```

The completed-packet command fails on the preserved rejected packet as expected. The recovery validates the corrected response with the stock result validator and unchanged handoff reference allowlist. The proposal register and portfolio schema validate all ten commitments and the exact admitted-coverage snapshot. The generated Markdown matches the register. The evaluation projection ran against empty scratch directories, using the stock custody helper.

Local repository checks included the full PostgreSQL 16-backed test suite, the CI mypy target list, an exact planning-file allowlist, review of the complete staged diff, and `git diff --check`.
