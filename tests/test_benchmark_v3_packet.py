import hashlib
import json
import stat
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from benchmark_v3 import commissioning, packet
from benchmark_v3.architect import read_architect_packet


_FAKE_CODEX = r"""
import json
import sys
from pathlib import Path

mode, capture_path = sys.argv[1:]
commands = []

def emit(**message):
    print(json.dumps(message), flush=True)

def notify(method, **params):
    emit(method=method, params=params)

for line in sys.stdin:
    request = json.loads(line)
    commands.append(request)
    name, params = request["method"], request["params"]
    if name == "initialize":
        result = {}
    elif name == "thread/start":
        result = {
            "cwd": str(Path.cwd()),
            "thread": {
                "id": "thread-1", "sessionId": "session-1", "cliVersion": "0.166.0",
                "ephemeral": True, "environments": [], "turns": [], "path": None,
            },
            "model": params["model"],
            "modelProvider": "openai",
            "reasoningEffort": "medium",
            "runtimeWorkspaceRoots": [],
            "instructionSources": [],
            "approvalPolicy": "never",
            "sandbox": {"type": "readOnly", "networkAccess": False},
            "activePermissionProfile": {"id": "benchmark_packet", "extends": None},
        }
        if mode == "instructions":
            result["instructionSources"] = ["/restricted/AGENTS.md"]
        if mode == "environment":
            result["thread"]["environments"] = [{"id": "inherited"}]
        if mode == "model":
            result["model"] = "other-model"
    elif name == "mcpServerStatus/list":
        connector = {
            "name": "test", "runtimeStatus": "disabled",
            "tools": {}, "resources": [], "resourceTemplates": [],
        }
        if mode == "tool":
            connector["tools"] = {"opaque-tool": {}}
        if mode in {"resources", "resourceTemplates"}:
            connector[mode] = [{"uri": "restricted://example"}]
        if mode == "active":
            connector["runtimeStatus"] = "connected"
        if mode == "missing":
            del connector["resourceTemplates"]
        result = {"data": [connector], "nextCursor": "other-page" if mode == "page" else None}
        if mode == "unverified_page":
            del result["nextCursor"]
    elif name == "turn/start":
        handoff = Path(capture_path).parent / "packet" / "handoff.json"
        json.loads(handoff.read_text(encoding="utf-8"))
        result = {"turn": {"id": "turn-1", "status": "inProgress"}}
    else:
        raise AssertionError(name)
    Path(capture_path).write_text(json.dumps(commands), encoding="utf-8")
    emit(id=request["id"], result=result)
    if name != "turn/start":
        continue

    scope = {"threadId": "thread-1", "turnId": "turn-1"}
    if mode == "tool_action":
        notify("item/started", item={"type": "commandExecution"}, **scope)
    if mode == "server_request":
        emit(id=17, method="item/tool/request", params=scope)
    if mode == "hook":
        notify("hook/started", **scope)
    if mode == "rerouted":
        notify("model/rerouted", **scope)
    if mode == "foreign_turn":
        scope["turnId"] = "foreign"
    text = str(Path.cwd()) if mode == "exposure" else "答え\nline 2"
    if mode == "architect":
        text = (Path(capture_path).parent / "response.json").read_text(encoding="utf-8")
    answer = {"type": "agentMessage", "phase": "final_answer", "text": text}
    if mode != "no_final":
        notify("item/completed", item=answer, **scope)
    notify("thread/tokenUsage/updated", tokenUsage={"total": {"totalTokens": 12}}, **scope)
    notify("turn/completed", threadId="thread-1", turn={
        "id": "turn-1", "status": "completed", "items": [],
    })
"""


@pytest.fixture
def packet_directory(tmp_path):
    directory = tmp_path / "packet"
    directory.mkdir()
    request = {
        "role": "annotation",
        "model": "model-selected-by-custodian",
        "effort": "medium",
        "rationale": "private allocation rationale",
        "parent": "private-parent-revision",
        "inputs": {"sources": "原文\r\n"},
        "prompt": "Extract every claim.",
    }
    _write_request(directory, request)
    return directory


def _write_request(directory, request):
    (directory / "request.json").write_text(json.dumps(request), encoding="utf-8")


def _read_json(directory, name):
    return json.loads((directory / name).read_text(encoding="utf-8"))


def _fake_codex(monkeypatch, directory, mode):
    tmp_path = directory.parent
    server = tmp_path / "fake_codex.py"
    server.write_text(_FAKE_CODEX, encoding="utf-8")
    capture = tmp_path / "commands.json"
    monkeypatch.setattr(
        packet, "_server_command", lambda *_: [sys.executable, str(server), mode, str(capture)],
    )
    monkeypatch.setattr(
        packet, "_create_runtime", lambda: tempfile.TemporaryDirectory(dir=tmp_path),
    )
    return capture


def test_commits_exact_text_and_custodian_metadata(monkeypatch, packet_directory):
    capture = _fake_codex(monkeypatch, packet_directory, "normal")

    packet.run_packet(packet_directory)

    handoff = _read_json(packet_directory, "handoff.json")
    receipt = _read_json(packet_directory, "receipt.json")
    _, thread, _, turn = json.loads(capture.read_bytes())
    assert thread["params"]["environments"] == thread["params"]["runtimeWorkspaceRoots"] == []
    assert thread["params"]["selectedCapabilityRoots"] == thread["params"]["dynamicTools"] == []
    assert turn["params"]["environments"] == turn["params"]["runtimeWorkspaceRoots"] == []
    item, = turn["params"]["input"]
    assert item["type"] == "text"
    assert item["text_elements"] == []
    assert json.loads(item["text"]) == {
        "inputs": {"sources": "原文\r\n"},
        "prompt": "Extract every claim.",
    }
    assert handoff["role"] == "annotation"
    assert handoff["parent"] == "private-parent-revision"
    assert handoff["rationale"] == "private allocation rationale"
    assert handoff["inputs"]["sources"] == {
        "bytes": len("原文\r\n".encode()),
        "sha256": hashlib.sha256("原文\r\n".encode()).hexdigest(),
    }
    assert handoff["packet_sha256"] == hashlib.sha256(item["text"].encode()).hexdigest()
    assert receipt["packet_sha256"] == handoff["packet_sha256"]
    assert receipt["session"] == handoff["session"]
    assert handoff["created_at"] <= receipt["submitted_at"] <= receipt["completed_at"]
    assert receipt["status"] == "completed"
    assert receipt["isolation"]["instruction_sources"] == []
    assert receipt["isolation"]["disabled_connectors"] == ["test"]
    assert receipt["observed_tool_actions"] == []
    assert receipt["usage"]["total"]["totalTokens"] == 12
    output = (packet_directory / "output.txt").read_bytes()
    assert output == "答え\nline 2".encode()
    assert receipt["output"] == {"bytes": len(output), "sha256": hashlib.sha256(output).hexdigest()}
    for name in ("handoff.json", "output.txt", "receipt.json"):
        assert not stat.S_IMODE((packet_directory / name).stat().st_mode) & stat.S_IWUSR

    with pytest.raises(packet.PacketError, match="fresh packet"):
        packet.run_packet(packet_directory)
    assert _read_json(packet_directory, "receipt.json") == receipt


def test_only_one_concurrent_runner_reserves_a_handoff(monkeypatch, packet_directory):
    capture = _fake_codex(monkeypatch, packet_directory, "normal")
    original_read_request = packet._read_request
    read_barrier = threading.Barrier(2)

    def read_before_either_reservation(directory):
        request = original_read_request(directory)
        read_barrier.wait(timeout=5)
        return request

    monkeypatch.setattr(packet, "_read_request", read_before_either_reservation)
    with ThreadPoolExecutor(max_workers=2) as executor:
        attempts = [executor.submit(packet.run_packet, packet_directory) for _ in range(2)]
        errors = [attempt.exception(timeout=10) for attempt in attempts]

    assert errors.count(None) == 1
    assert sum(isinstance(error, FileExistsError) for error in errors) == 1
    assert [request["method"] for request in json.loads(capture.read_bytes())].count("turn/start") == 1
    assert _read_json(packet_directory, "receipt.json")["status"] == "completed"


@pytest.mark.parametrize(
    "mode", [
        "instructions", "environment", "model", "tool", "resources", "resourceTemplates",
        "active", "missing", "page", "unverified_page",
    ],
)
def test_rejects_unverified_isolation_before_turn(monkeypatch, packet_directory, mode):
    capture = _fake_codex(monkeypatch, packet_directory, mode)

    with pytest.raises(packet.PacketError):
        packet.run_packet(packet_directory)

    assert "turn/start" not in [request["method"] for request in json.loads(capture.read_bytes())]
    receipt = _read_json(packet_directory, "receipt.json")
    assert receipt["status"] == "rejected"
    assert "submitted_at" not in receipt
    assert not (packet_directory / "output.txt").exists()


@pytest.mark.parametrize(
    "mode",
    ["tool_action", "server_request", "hook", "rerouted", "foreign_turn", "no_final", "exposure"],
)
def test_rejects_exposure_and_nonfinal_results(monkeypatch, packet_directory, mode):
    _fake_codex(monkeypatch, packet_directory, mode)

    with pytest.raises(packet.PacketError):
        packet.run_packet(packet_directory)

    receipt = _read_json(packet_directory, "receipt.json")
    assert receipt["status"] == "rejected"
    assert receipt["submitted_at"]
    assert not (packet_directory / "output.txt").exists()


@pytest.mark.parametrize(
    ("role", "labels"),
    [
        ("author", "author_brief genre_references received_correspondence revision_ticket"),
        ("realism", "sources neutral_brief cutoff possession_ledger genre_references"),
        ("annotation", "sources neutral_brief ontology annotation_rules"),
        ("adjudication", "sources annotation_a annotation_b neutral_brief ontology annotation_rules"),
        ("audit", "paired_bundles intended_intervention provisional_keys neutral_brief ontology audit_rules"),
        ("masked", "sources neutral_brief ontology annotation_rules"),
        ("probe", "probe"),
    ],
)
def test_accepts_each_roles_scope_and_rejects_extra_history(
    monkeypatch, packet_directory, role, labels,
):
    capture = _fake_codex(monkeypatch, packet_directory, "normal")
    request = _read_json(packet_directory, "request.json")
    inputs = {label: "synthetic text" for label in labels.split()}
    request.update(role=role, inputs=inputs | {"private_history": "restricted text"})
    _write_request(packet_directory, request)

    with pytest.raises(packet.PacketError, match="allowlist"):
        packet.run_packet(packet_directory)
    assert not capture.exists()

    request.update(inputs=inputs)
    _write_request(packet_directory, request)
    packet.run_packet(packet_directory)

    turn = json.loads(capture.read_bytes())[-1]
    assert json.loads(turn["params"]["input"][0]["text"])["inputs"] == inputs


@pytest.mark.parametrize(
    "fields", [
        {"role": "invalid"},
        {"inputs": {"annotation_a": "hidden peer labels"}},
        {"inputs": {"sources": ["detached attachments"]}},
        {"unexpected": "anything"},
    ],
)
def test_requires_a_valid_allowlisted_request(packet_directory, fields):
    request = _read_json(packet_directory, "request.json")
    _write_request(packet_directory, request | fields)

    with pytest.raises(packet.PacketError):
        packet.run_packet(packet_directory)

    assert {path.name for path in packet_directory.iterdir()} == {"request.json"}


def test_rejects_duplicate_keys(packet_directory):
    request = packet_directory / "request.json"
    request.write_text('{"role":"probe","role":"annotation"}', encoding="utf-8")

    with pytest.raises(packet.PacketError, match="duplicate keys"):
        packet.run_packet(packet_directory)


def test_requires_the_request_to_be_a_regular_file(packet_directory):
    request = packet_directory / "request.json"
    original = request.rename(packet_directory.parent / "original.json")
    request.symlink_to(original)

    with pytest.raises(packet.PacketError, match="regular file"):
        packet.run_packet(packet_directory)


def test_architect_turn_sends_only_staged_prebaseline_material(monkeypatch, packet_directory):
    capture = _fake_codex(monkeypatch, packet_directory, "architect")
    restricted = packet_directory.parent / "sealed-sentinel.json"
    restricted.write_text("private test sentinel that must not enter a turn", encoding="utf-8")
    inputs = {
        "research_specification": "Use the benchmark rules.",
        "development_findings": "Summaries of admitted family reviews.",
        "practice_references": "[]",
    }
    request = _read_json(packet_directory, "request.json") | {
        "role": "research_architect", "prompt": "research-architect-v1", "inputs": inputs,
    }
    _write_request(packet_directory, request)
    response = {
        "schema_version": 1,
        "portfolio_summary": "No new diagnostic need established.",
        "family_assessments": [
            {"family_id": family, "assessment": "Admitted development review.", "overlap": "Joint proof."}
            for family in (row.family_id for row in commissioning.coverage_register().families)
        ],
        "gaps": [],
        "proposals": [],
        "stopping_criteria": ["Stop when no distinctive feasible contrast remains."],
    }
    (packet_directory.parent / "response.json").write_text(json.dumps(response), encoding="utf-8")

    packet.run_packet(packet_directory)

    thread, turn = json.loads(capture.read_bytes())[1::2]
    message = turn["params"]["input"][0]["text"]
    payload = json.loads(message)
    assert payload["inputs"].keys() == inputs.keys() | {
        "coverage_register", "ontology", "previous_decisions",
    }
    assert restricted.read_text() not in message
    assert str(restricted) not in message
    assert "Output schema" in payload["prompt"]
    assert thread["params"]["environments"] == thread["params"]["runtimeWorkspaceRoots"] == []
    record = read_architect_packet(packet_directory, "planning")
    assert record.result.proposals == []
    assert record.provenance.session == _read_json(packet_directory, "receipt.json")["session"]

    (packet_directory / "output.txt").chmod(0o600)
    (packet_directory / "output.txt").write_text("changed response", encoding="utf-8")
    with pytest.raises(ValueError, match="matching completed receipt"):
        read_architect_packet(packet_directory, "planning")


@pytest.mark.parametrize(
    "extra_label",
    ["held_out_sources", "answer_key", "annotation_a", "extractor_results", "private_history", "sources"],
)
def test_architect_rejects_restricted_labels_before_launch(monkeypatch, packet_directory, extra_label):
    capture = _fake_codex(monkeypatch, packet_directory, "normal")
    request = _read_json(packet_directory, "request.json")
    request.update(role="research_architect", prompt="research-architect-v1", inputs={
        "research_specification": "Specification.",
        "development_findings": "Admitted findings.",
        "practice_references": "[]",
        extra_label: "private content",
    })
    _write_request(packet_directory, request)

    with pytest.raises(packet.PacketError, match="allowlist"):
        packet.run_packet(packet_directory)

    assert not capture.exists()
    assert not (packet_directory / "handoff.json").exists()


def test_packet_profile_excludes_shared_storage_and_user_paths(tmp_path):
    config = packet._macos_filesystem(tmp_path)
    permissions = config.split("=", 1)[1]
    grants = json.loads(permissions.replace("=", ":"))
    assert grants == {
        ":minimal": "read",
        "/private/tmp": "deny",
        "/private/var/folders": "deny",
        "/Users": "deny",
        str(tmp_path.resolve()): "read",
    }


def test_architect_reconciliation_receipt_binds_admission_context(monkeypatch, packet_directory):
    _fake_codex(monkeypatch, packet_directory, "architect")
    context = {
        "family_id": "D",
        "hypothesis": {
            "hypothesis_id": "amendment-scope", "revision": 1, "hypothesis_sha256": "1" * 64,
        },
        "admission_sha256": "2" * 64,
    }
    metadata = {"profile": "reconciliation", "axes": [], "admission": context}
    monkeypatch.setattr(
        packet.commissioning, "prepare_architect",
        lambda _: ({"approved_hypothesis": "Owner-reviewed proposal."}, metadata),
    )
    request = _read_json(packet_directory, "request.json") | {
        "role": "research_architect", "prompt": "research-architect-v1",
        "inputs": {
            "hypothesis_revision": "amendment-scope@1",
            "admission_dossier": "Admitted dossier excerpt.",
            "technical_findings": "No independently verified new axis.",
        },
    }
    _write_request(packet_directory, request)
    response = {
        "schema_version": 1, "operationalisation": "unassessable",
        "achieved_vs_intended": "The technical findings do not report the required mask.",
        "verified_findings": [], "additional_coverage": "Unknown.", "redundancy": "Unknown.",
        "remaining_gaps": [], "recommendation": "refine_future_designs",
        "rationale": "Retain the hypothesis and record incomplete evidence.",
    }
    (packet_directory.parent / "response.json").write_text(json.dumps(response), encoding="utf-8")

    packet.run_packet(packet_directory)

    record = read_architect_packet(packet_directory, "reconciliation")
    assert record.context.model_dump() == context
    assert record.result.operationalisation == "unassessable"
    handoff = _read_json(packet_directory, "handoff.json")
    handoff["research"]["admission"]["admission_sha256"] = "3" * 64
    path = packet_directory / "handoff.json"
    path.chmod(0o600)
    path.write_text(json.dumps(handoff), encoding="utf-8")
    with pytest.raises(ValueError, match="handoff digest"):
        read_architect_packet(packet_directory, "reconciliation")
