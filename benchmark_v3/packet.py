"""Submit a single isolated text packet through the Codex app-server."""

import argparse
import hashlib
import json
import os
import queue
import re
import stat
import sys
import subprocess
import tempfile
import threading
import time
import tomllib
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from benchmark_v3 import commissioning
from benchmark_v3.research_contracts import PlanningResult, ReconciliationResult


_INPUTS = {
    "research_architect": commissioning.PLANNING_LABELS | commissioning.RECONCILIATION_LABELS,
    "designer": {"hypothesis_revision"},
    "author": {"author_brief", "genre_references", "received_correspondence", "revision_ticket"},
    "realism": {"sources", "neutral_brief", "cutoff", "possession_ledger", "genre_references"},
    "annotation": {"sources", "neutral_brief", "ontology", "annotation_rules"},
    "adjudication": {
        "sources", "annotation_a", "annotation_b", "neutral_brief", "ontology", "annotation_rules",
    },
    "audit": {
        "paired_bundles", "intended_intervention", "provisional_keys", "neutral_brief",
        "ontology", "audit_rules",
    },
    "masked": {"sources", "neutral_brief", "ontology", "annotation_rules"},
    "probe": {"probe"},
}
_FIELDS = {"role", "model", "effort", "rationale", "parent", "inputs", "prompt"}
_DISABLED_FEATURES = (
    "apps", "browser_use", "browser_use_external", "computer_use", "goals", "hooks",
    "image_generation", "in_app_browser", "memories", "multi_agent", "plugins", "remote_plugin",
    "shell_tool", "unified_exec", "skill_search", "tool_suggest", "view_image",
    "workspace_dependencies", "js_repl", "code_mode_host",
)
_PROFILE = "benchmark_packet"
_BASE_INSTRUCTIONS = (
    "Work solely from the supplied text packet. Follow its prompt and use only its inputs."
)
_DEVELOPER_INSTRUCTIONS = "Return the requested result as final text."
_ITEM_TYPES = {"userMessage", "agentMessage", "reasoning"}
_ITEM_EVENTS = {"item/started", "item/completed"}
_ITEM_NOTIFICATIONS = {
    *_ITEM_EVENTS, "item/agentMessage/delta",
    "item/reasoning/summaryTextDelta", "item/reasoning/summaryPartAdded",
    "item/reasoning/textDelta",
}
_UNEXPECTED_NOTIFICATIONS = {
    "error", "turn/diff/updated", "turn/plan/updated", "thread/compacted",
    "thread/environment/connected", "thread/environment/disconnected", "model/rerouted",
    "mcpServer/event/stream/notification", "fs/changed",
}
_DEADLINE_SECONDS = 900


class PacketError(Exception):
    """The packet cannot be submitted or its output cannot be admitted."""


def run_packet(directory: Path) -> None:
    """Record the handoff, verify isolation, and publish the completed text and receipt."""
    request = _read_request(directory)
    message = _json_text({"inputs": request["inputs"], "prompt": request["prompt"]})
    handoff = _handoff(request, message)
    handoff_text = _json_text(handoff) + "\n"
    _write_new(directory / "handoff.json", handoff_text)

    receipt: dict[str, Any] = {
        "session": handoff["session"],
        "packet_sha256": handoff["packet_sha256"],
        "model_requested": request["model"],
        "effort_requested": request["effort"],
    }
    if request.get("research", {}).get("profile") == "reconciliation":
        receipt["handoff_sha256"] = _fingerprint(handoff_text)["sha256"]
    try:
        with _create_runtime() as temporary:
            runtime = Path(temporary)
            workspace = runtime / "empty"
            workspace.mkdir()
            with _Codex(_server_command(runtime, workspace, request["effort"]), workspace) as codex:
                isolation = _start_checked_thread(codex, workspace, request)
                receipt["isolation"] = isolation
                receipt["submitted_at"] = _timestamp()
                result = _run_turn(codex, isolation["thread_id"], message, request["effort"])
            output = result.pop("text")
            private_paths = {directory.resolve(), runtime.resolve()}
            if any(str(path) in output for path in private_paths):
                raise PacketError("Output exposed an unstaged runtime path.")
            if request["role"] == "research_architect":
                commissioning.validate_architect_result(output, request["research"])
        receipt.update(result)
        receipt["output"] = _fingerprint(output)
        _write_new(directory / "output.txt", output)
    except (PacketError, OSError, ValueError, TypeError, KeyError) as error:
        reason = (
            _validation_reason(error) if isinstance(error, ValidationError)
            else str(error) if isinstance(error, (PacketError, ValueError))
            else type(error).__name__
        )
        receipt.update(status="rejected", reason=reason, completed_at=_timestamp())
        _write_new(directory / "receipt.json", _json_text(receipt) + "\n")
        raise PacketError(reason) from None

    receipt.update(status="completed", completed_at=_timestamp())
    _write_new(directory / "receipt.json", _json_text(receipt) + "\n")


def _read_request(directory: Path) -> dict[str, Any]:
    if directory.is_symlink() or not directory.is_dir():
        raise PacketError("Use a real packet directory.")
    if {entry.name for entry in directory.iterdir()} != {"request.json"}:
        raise PacketError("A fresh packet directory must contain only request.json.")
    path = directory / "request.json"
    if not stat.S_ISREG(path.lstat().st_mode):
        raise PacketError("request.json must be a regular file.")
    try:
        request = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_unique_members,
        )
        _json_text(request).encode("utf-8")
    except (UnicodeError, json.JSONDecodeError):
        raise PacketError("request.json must be UTF-8 JSON.") from None
    if not isinstance(request, dict) or request.keys() != _FIELDS:
        raise PacketError("request.json has unexpected or missing fields.")
    for key in ("role", "model", "effort", "rationale", "prompt"):
        if not isinstance(request[key], str) or not request[key].strip():
            raise PacketError(f"{key} must be a nonempty string.")
    parent = request["parent"]
    if parent is not None and (not isinstance(parent, str) or not parent.strip()):
        raise PacketError("parent must be null or a nonempty revision identifier.")
    allowed = _INPUTS.get(request["role"])
    inputs = request["inputs"]
    if allowed is None or not isinstance(inputs, dict) or not inputs.keys() <= allowed:
        raise PacketError("The role or its input labels are outside the packet allowlist.")
    if any(not isinstance(value, str) for value in inputs.values()):
        raise PacketError("Every input must be supplied as text.")
    try:
        _prepare_research_handoff(request)
    except ValidationError as error:
        raise PacketError(_validation_reason(error)) from None
    except ValueError as error:
        raise PacketError(str(error)) from None
    return request


def _prepare_research_handoff(request: dict[str, Any]) -> None:
    if request["role"] == "research_architect":
        if request["prompt"] != "research-architect-v1":
            raise ValueError("Select the versioned research-architect-v1 prompt.")
        inputs, context = commissioning.prepare_architect(request["inputs"])
        schema = PlanningResult if context["profile"] == "planning" else ReconciliationResult
        instructions = commissioning.trusted_bytes(commissioning.ARCHITECT_PROMPT).decode("utf-8")
        request["prompt"] = (
            f"{instructions}\nActive profile: {context['profile']}\n"
            f"Output schema: {_json_text(schema.model_json_schema())}"
        )
        request["inputs"] = inputs
        request["research"] = context
    if request["role"] == "designer":
        if request["prompt"] != "commissioned-designer-v1" or request["inputs"].keys() != {
            "hypothesis_revision",
        }:
            raise ValueError("Design requires a human-approved hypothesis revision and the versioned prompt.")
        brief = commissioning.designer_brief(request["inputs"]["hypothesis_revision"])
        request["inputs"] = {"capability_brief": _json_text(brief)}
        request["prompt"] = commissioning.trusted_bytes(commissioning.DESIGNER_PROMPT).decode("utf-8")


def _validation_reason(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(map(str, issue['loc'])) or 'packet'}: {issue['msg']}"
        for issue in error.errors(include_input=False, include_url=False)
    )


def _unique_members(members: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(members)
    if len(members) != len(result):
        raise PacketError("request.json contains duplicate keys.")
    return result


def _handoff(request: dict[str, Any], message: str) -> dict[str, Any]:
    return {
        "session": str(uuid4()),
        "created_at": _timestamp(),
        "role": request["role"],
        "model_requested": request["model"],
        "effort_requested": request["effort"],
        "rationale": request["rationale"],
        "parent": request["parent"],
        "packet_sha256": _fingerprint(message)["sha256"],
        "inputs": {name: _fingerprint(text) for name, text in request["inputs"].items()},
        "prompt": _fingerprint(request["prompt"]),
        "base_instructions": _fingerprint(_BASE_INSTRUCTIONS),
        "developer_instructions": _fingerprint(_DEVELOPER_INSTRUCTIONS),
        **({"research": request["research"]} if request["role"] == "research_architect" else {}),
    }


def _fingerprint(text: str) -> dict[str, Any]:
    content = text.encode("utf-8")
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_new(path: Path, value: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    with os.fdopen(os.open(path, flags, 0o400), "wb") as file:
        file.write(value.encode("utf-8"))
        file.flush()
        os.fsync(file.fileno())


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _create_runtime() -> tempfile.TemporaryDirectory:
    if sys.platform != "darwin":
        raise PacketError("The packet permission profile is verified only on macOS.")
    return tempfile.TemporaryDirectory(dir="/private/tmp", prefix="benchmark-packet-")


def _server_command(runtime: Path, workspace: Path, effort: str) -> list[str]:
    command = ["codex", "app-server", "--stdio"]
    for feature in _DISABLED_FEATURES:
        command.extend(("--disable", feature))

    config = [
        'web_search="disabled"',
        'skills.include_instructions=false',
        'skills.bundled.enabled=false',
        'include_environment_context=false',
        'project_doc_max_bytes=0',
        'include_apps_instructions=false',
        'include_collaboration_mode_instructions=false',
        'include_permissions_instructions=false',
        'approval_policy="never"',
        'history.persistence="none"',
        'analytics.enabled=false',
        'feedback.enabled=false',
        'notify=[]',
        f'model_reasoning_effort={json.dumps(effort)}',
        f'sqlite_home={json.dumps(str(runtime / "state"))}',
        f'log_dir={json.dumps(str(runtime / "logs"))}',
        _macos_filesystem(workspace),
        f'permissions.{_PROFILE}.network.enabled=false',
    ]
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    config_path = codex_home / "config.toml"
    if config_path.is_file():
        with config_path.open("rb") as file:
            configured_mcp = tomllib.load(file).get("mcp_servers", {})
        for name in configured_mcp:
            if re.fullmatch(r"[A-Za-z0-9_-]+", name) is None:
                raise PacketError("A configured connector name cannot be safely disabled.")
            config.append(f"mcp_servers.{name}.enabled=false")
    for setting in config:
        command.extend(("-c", setting))
    return command


def _macos_filesystem(workspace: Path) -> str:
    grants = {
        ":minimal": "read",
        "/private/tmp": "deny",
        "/private/var/folders": "deny",
        "/Users": "deny",
        str(workspace.resolve()): "read",
    }
    rules = ",".join(f"{json.dumps(path)}={json.dumps(access)}" for path, access in grants.items())
    return f"permissions.{_PROFILE}.filesystem={{{rules}}}"


def _start_checked_thread(
    codex: "_Codex", workspace: Path, request: dict[str, Any],
) -> dict[str, Any]:
    codex.request("initialize", {
        "clientInfo": {"name": "benchmark-packet", "version": "1"},
        "capabilities": {"experimentalApi": True},
    })
    started = codex.request("thread/start", {
        "cwd": str(workspace),
        "model": request["model"],
        "modelProvider": "openai",
        "allowProviderModelFallback": False,
        "environments": [],
        "runtimeWorkspaceRoots": [],
        "selectedCapabilityRoots": [],
        "dynamicTools": [],
        "approvalPolicy": "never",
        "permissions": _PROFILE,
        "ephemeral": True,
        "baseInstructions": _BASE_INSTRUCTIONS,
        "developerInstructions": _DEVELOPER_INSTRUCTIONS,
    })
    thread = started["thread"]
    if not isinstance(thread, dict):
        raise PacketError("Codex did not return valid thread metadata.")
    expected = {
        "cwd": str(workspace.resolve()),
        "runtimeWorkspaceRoots": [],
        "instructionSources": [],
        "approvalPolicy": "never",
        "sandbox": {"type": "readOnly", "networkAccess": False},
        "activePermissionProfile": {"id": _PROFILE, "extends": None},
        "model": request["model"],
        "modelProvider": "openai",
        "reasoningEffort": request["effort"],
    }
    if any(started.get(key) != value for key, value in expected.items()):
        raise PacketError("Codex did not confirm the requested isolation, model, and effort.")
    if (
        thread.get("ephemeral") is not True
        or thread.get("environments") != []
        or thread.get("turns") != []
        or any(thread.get(key) is not None for key in ("path", "forkedFromId", "parentThreadId"))
        or any(workspace.iterdir())
    ):
        raise PacketError("Codex did not start an empty, isolated ephemeral thread.")

    inventory = codex.request("mcpServerStatus/list", {"threadId": thread["id"]})
    if "nextCursor" not in inventory or inventory["nextCursor"] is not None:
        raise PacketError("Codex did not return a complete connector inventory.")
    if not isinstance(inventory.get("data"), list):
        raise PacketError("Codex did not return a complete connector inventory.")
    for server in inventory["data"]:
        if not (
            isinstance(server, dict)
            and server.get("runtimeStatus") == "disabled"
            and server.get("tools") == {}
            and server.get("resources") == []
            and server.get("resourceTemplates") == []
        ):
            raise PacketError("Codex reported an active or unverified connector.")
    return {
        "thread_id": thread["id"],
        "codex_session_id": thread["sessionId"],
        "codex_cli_version": thread["cliVersion"],
        "model": started["model"],
        "effort": started["reasoningEffort"],
        "provider": started["modelProvider"],
        "service_tier": started.get("serviceTier"),
        "ephemeral": True,
        "empty_workspace": True,
        "instruction_sources": started["instructionSources"],
        "thread_environments": thread["environments"],
        "runtime_workspace_roots": started["runtimeWorkspaceRoots"],
        "permission_profile": started["activePermissionProfile"],
        "sandbox": started["sandbox"],
        "approval_policy": started["approvalPolicy"],
        "disabled_features": list(_DISABLED_FEATURES),
        "disabled_connectors": sorted(server["name"] for server in inventory["data"]),
    }


def _run_turn(codex: "_Codex", thread_id: str, message: str, effort: str) -> dict[str, Any]:
    started = codex.request("turn/start", {
        "threadId": thread_id,
        "environments": [],
        "runtimeWorkspaceRoots": [],
        "effort": effort,
        "input": [{"type": "text", "text": message, "text_elements": []}],
    })
    turn_id = started["turn"]["id"]
    usage = None
    final: list[str] = []
    for event in codex.events():
        method = event.get("method")
        params = event.get("params", {})
        if method in _ITEM_EVENTS or method in {"turn/completed", "thread/tokenUsage/updated"}:
            if params.get("threadId") != thread_id:
                raise PacketError("Codex reported events from another thread.")
            if "turnId" in params and params["turnId"] != turn_id:
                raise PacketError("Codex reported events from another turn.")
        if method == "item/completed":
            item = params["item"]
            if item["type"] == "agentMessage" and item.get("phase") == "final_answer":
                final.append(item["text"])
        if method == "thread/tokenUsage/updated":
            usage = params["tokenUsage"]
        if method == "turn/completed":
            turn = params["turn"]
            if turn.get("id") != turn_id or turn.get("status") != "completed" or turn.get("error"):
                raise PacketError("The Codex turn did not complete successfully.")
            for item in turn["items"]:
                _check_item(item)
            if len(final) != 1 or not isinstance(final[0], str) or not final[0].strip():
                raise PacketError("The turn must produce one nonempty final text item.")
            return {
                "text": final[0],
                "turn_id": turn_id,
                "turn_environments_requested": [],
                "turn_runtime_workspace_roots_requested": [],
                "usage": usage,
                "observed_tool_actions": [],
            }
    raise PacketError("Codex exited before completing the turn.")


def _check_item(item: dict[str, Any]) -> None:
    if not isinstance(item, dict) or item.get("type") not in _ITEM_TYPES:
        raise PacketError("Codex reported an unexpected item or tool action.")


class _Codex:
    """One bounded stdio connection, with notifications retained while awaiting replies."""

    def __init__(self, command: list[str], cwd: Path):
        self.command = command
        self.cwd = cwd
        self.incoming: queue.Queue[str] = queue.Queue()
        self.pending: list[dict[str, Any]] = []
        self.request_id = 0

    def __enter__(self) -> "_Codex":
        self.process = subprocess.Popen(
            self.command, cwd=self.cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
        )
        self.deadline = time.monotonic() + _DEADLINE_SECONDS
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.reader.join(timeout=3)
        if self.process.stdin is not None:
            self.process.stdin.close()
        if self.process.stdout is not None:
            self.process.stdout.close()

    def _read(self) -> None:
        try:
            if self.process.stdout is not None:
                for line in self.process.stdout:
                    self.incoming.put(line)
        except UnicodeError:
            pass
        finally:
            self.incoming.put("")

    def _receive(self) -> dict[str, Any]:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise PacketError("The Codex app-server timed out.")
        try:
            line = self.incoming.get(timeout=remaining)
        except queue.Empty:
            raise PacketError("The Codex app-server timed out.") from None
        if not line:
            raise PacketError("The Codex app-server closed its connection.")
        reply = json.loads(line)
        if not isinstance(reply, dict):
            raise PacketError("Codex returned an invalid protocol message.")
        method = reply.get("method")
        if method is not None:
            if not isinstance(method, str):
                raise PacketError("Codex returned an invalid protocol method.")
            _check_notification(method, reply)
        return reply

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.request_id += 1
        assert self.process.stdin is not None
        self.process.stdin.write(_json_text({
            "id": self.request_id, "method": method, "params": params,
        }) + "\n")
        self.process.stdin.flush()
        while True:
            reply = self._receive()
            if reply.get("id") == self.request_id:
                if "error" in reply:
                    raise PacketError(f"Codex rejected the {method} request.")
                result = reply["result"]
                if not isinstance(result, dict):
                    raise PacketError("Codex returned an invalid request result.")
                return result
            if "id" in reply:
                raise PacketError("Codex returned a response to an unknown request.")
            self.pending.append(reply)

    def events(self) -> Iterator[dict[str, Any]]:
        yield from self.pending
        self.pending.clear()
        while True:
            yield self._receive()


def _check_notification(method: str, reply: dict[str, Any]) -> None:
    if "id" in reply:
        raise PacketError("Codex requested an action.")
    if method in _UNEXPECTED_NOTIFICATIONS or method.startswith(
        ("hook/", "command/", "process/", "fuzzyFileSearch/", "thread/realtime/"),
    ):
        raise PacketError("Codex reported an unexpected runtime action or error.")
    if method.startswith("item/") and method not in _ITEM_NOTIFICATIONS:
        raise PacketError("Codex reported an unexpected item or tool action.")
    if method in _ITEM_EVENTS:
        _check_item(reply["params"]["item"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet_dir", type=Path)
    args = parser.parse_args()
    try:
        run_packet(args.packet_dir)
    except (PacketError, OSError) as error:
        parser.exit(1, f"Packet rejected: {error}\n")


if __name__ == "__main__":
    main()
