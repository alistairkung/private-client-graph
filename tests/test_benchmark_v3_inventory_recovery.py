import json

import pytest

from benchmark_v3 import commissioning, inventory_recovery
from benchmark_v3.batch import artifacts
from benchmark_v3.portfolio import Portfolio

CHILD = ("Casey Hart", "parent_of", "Robin Hart")
ORDINARY = ("Jo Rivers", "sibling_of", "Lee Rivers")


@pytest.fixture
def parent_packet(tmp_path, monkeypatch):
    portfolio = Portfolio.model_validate_json(commissioning.trusted_bytes(
        "planning/development-20/portfolio.json",
    ))
    slot = next(slot for slot in portfolio.slots if slot.family_id == "M")
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (tmp_path / "validation.json").write_text(json.dumps({
        "status": "design rejected",
        "reason": "Source provenance must form a unique chronological inventory.",
    }))
    receipt_sha256 = commissioning.digest(b"fixture receipt")

    def stage(*, same_day=False, historical_edge=False, extra_predecessor=False, future_dependency=False):
        scoped_slot = slot.model_copy(update={"expected_sources": 3 if extra_predecessor else 2})
        request = {
            "role": "designer", "prompt": "candidate-designer-v1",
            "inputs": {"portfolio_slot": scoped_slot.model_dump_json()},
        }
        (packet_dir / "request.json").write_text(json.dumps(request))
        late = {
            "source_id": "late", "author": "Later author", "created_on": "2025-06-02",
            "provenance": "Received a verified record",
            "participant_brief": "Record the finding: verified",
            "received": ["early"],
        }
        early = {
            "source_id": "early", "author": "Earlier author",
            "created_on": "2025-06-02" if same_day else "2025-06-01",
            "provenance": "Original record", "participant_brief": "Résumé [draft]",
            "received": ["late"] if future_dependency else [],
        }
        design = {
            "neutral_brief": 'Review a file quoting "inventory".',
            "cutoff": "2025-06-02", "documentary_references": [],
            "private_history": "Fixture case.",
            "matched": [{
                "kind": "literal_edit", "edit": {"source_id": "late", "before": "verified", "after": "open"},
            }],
            "candidates": [CHILD], "required": {"M000": [CHILD], "M001": []},
            "expected_graphs": {
                "M000": [CHILD, ORDINARY],
                "M001": [ORDINARY, ("Casey Prior", "parent_of", "Robin Hart")] if historical_edge else [ORDINARY],
            },
            "evidence_routes": {"M000": ["Both records"], "M001": ["One record"]},
            "knowledge_boundaries": ["Only the later author held the first record."],
            "documentary_assumptions": ["Both records reach the file."],
            "shortcut_predictions": ["An always-affirmative rule fails."],
            "independent_review_plan": ["Read each condition twice."],
            "open_questions": ["Check the response format."],
            "approximate_source_words": {"early": 50, "late": 60},
        }
        raw_entries = [json.dumps(late, indent=3), json.dumps(early, indent=2, ensure_ascii=False)]
        if extra_predecessor:
            raw_entries.append(json.dumps({**early, "source_id": "same-date"}))
            design["approximate_source_words"]["same-date"] = 40
        outer = json.dumps(design, indent=2)[:-2]
        prefix = (outer + ',\n  "inventory": [\n    ').encode()
        suffix = b"\n  ]\n}\n"
        raw = prefix + ",\n    ".join(raw_entries).encode() + suffix
        (tmp_path / "original-response.txt").write_bytes(raw)
        output_sha256 = commissioning.digest(raw)

        def verified_packet(directory, supplied_request):
            assert directory == packet_dir and supplied_request == request
            return raw, {"output_sha256": output_sha256, "receipt_sha256": receipt_sha256}

        monkeypatch.setattr(artifacts, "completed_packet", verified_packet)
        scope = inventory_recovery.InventoryRecoveryScope(
            family_id=slot.family_id, hypothesis=slot.hypothesis,
            output_sha256=output_sha256, receipt_sha256=receipt_sha256,
        )
        expected = prefix + ",\n    ".join(reversed(raw_entries)).encode() + suffix
        return scope, raw, expected, raw_entries

    return stage


def test_preview_moves_only_raw_inventory_entries(tmp_path, parent_packet):
    scope, raw, expected, entries = parent_packet(same_day=True)
    preview = inventory_recovery.preview_inventory_recovery(tmp_path, scope)
    assert preview.before == ("late", "early")
    assert preview.after == ("early", "late")
    assert preview.permutation == (1, 0)
    assert preview.reordered_output == expected
    assert preview.entry_sha256 == dict(zip(preview.before, (
        commissioning.digest(entry.encode()) for entry in entries
    ), strict=True))
    assert preview.validation_error is None
    assert (tmp_path / "original-response.txt").read_bytes() == raw
    assert {path.name for path in tmp_path.iterdir()} == {"packet", "original-response.txt", "validation.json"}


@pytest.mark.parametrize("field", ["output_sha256", "receipt_sha256"])
def test_preview_rejects_unpinned_parent(tmp_path, parent_packet, field):
    scope, *_ = parent_packet()
    with pytest.raises(ValueError, match="response and receipt must match"):
        inventory_recovery.preview_inventory_recovery(tmp_path, scope.model_copy(update={field: "0" * 64}))


def test_preview_exposes_remaining_scientific_validation_error(tmp_path, parent_packet):
    scope, raw, expected, _ = parent_packet(historical_edge=True)
    preview = inventory_recovery.preview_inventory_recovery(tmp_path, scope)
    assert preview.reordered_output == expected
    assert preview.validation_error == "Retain at least one independent ordinary edge across conditions."
    assert (tmp_path / "original-response.txt").read_bytes() == raw


def test_preview_refuses_more_than_one_valid_order(tmp_path, parent_packet):
    scope, *_ = parent_packet(extra_predecessor=True)
    with pytest.raises(ValueError, match="More than one chronological"):
        inventory_recovery.preview_inventory_recovery(tmp_path, scope)


def test_preview_refuses_a_future_dependency(tmp_path, parent_packet):
    scope, *_ = parent_packet(future_dependency=True)
    with pytest.raises(ValueError, match="dated after its recipient"):
        inventory_recovery.preview_inventory_recovery(tmp_path, scope)
