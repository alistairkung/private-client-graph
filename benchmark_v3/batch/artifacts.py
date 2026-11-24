"""Private immutable artifact I/O and isolated packet receipt verification."""

import math
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, TypeVar

from pydantic import BaseModel

from benchmark_v3 import commissioning, packet

_T = TypeVar("_T", bound=BaseModel)


def read_bytes(path: Path) -> bytes:
    if path.resolve() != path or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"Expected a regular, non-symlink artifact: {path.name}")
    return path.read_bytes()


def read_contract(path: Path, contract: type[_T]) -> _T:
    return contract.model_validate(commissioning._read_json(read_bytes(path)))


def write_bytes(path: Path, content: bytes) -> str:
    # Publish a complete regular file by exclusive linking. A killed process
    # can leave an unreferenced temporary file, but never a partial commitment.
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.parent.resolve() != path.parent:
        raise ValueError("Artifact parents must be canonical custody paths.")
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=".staging-", delete=False) as temporary:
            try:
                temporary.write(content)
                temporary.flush()
                os.fchmod(temporary.fileno(), 0o400)
                os.fsync(temporary.fileno())
                os.link(temporary.name, path)
            finally:
                os.unlink(temporary.name)
    except FileExistsError:
        if read_bytes(path) != content:
            raise ValueError(f"Immutable artifact changed: {path.name}") from None
    with _directory_fd(path.parent) as fd:
        os.fsync(fd)
    return commissioning.digest(content)


@contextmanager
def _directory_fd(path: Path) -> Iterator[int]:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        yield fd
    finally:
        os.close(fd)


def write_json(path: Path, value: Any) -> str:
    return write_bytes(path, (commissioning.json_text(value) + "\n").encode())


def completed_packet(directory: Path, request: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    # Recompute the exact projected message, including the approved designer brief.
    approved = request.copy()
    packet._prepare_research_handoff(approved)
    message = commissioning.json_text({"inputs": approved["inputs"], "prompt": approved["prompt"]})
    handoff_bytes = read_bytes(directory / "handoff.json")
    receipt_bytes = read_bytes(directory / "receipt.json")
    handoff = commissioning._read_json(handoff_bytes)
    receipt = commissioning._read_json(receipt_bytes)
    output = read_bytes(directory / "output.txt")
    isolation = receipt.get("isolation") or {}
    if (
        handoff.get("role") != request["role"]
        or handoff.get("parent") != request["parent"]
        or handoff.get("packet_sha256") != commissioning.digest(message.encode())
        or handoff.get("inputs") != {
            label: packet._fingerprint(text) for label, text in approved["inputs"].items()
        }
        or handoff.get("prompt") != packet._fingerprint(approved["prompt"])
        or receipt.get("handoff_sha256") != commissioning.digest(handoff_bytes)
        or not handoff.get("session") or receipt.get("session") != handoff["session"]
        or receipt.get("packet_sha256") != handoff["packet_sha256"]
        or receipt.get("status") != "completed"
        or receipt.get("observed_tool_actions") != []
        or receipt.get("output") != {"bytes": len(output), "sha256": commissioning.digest(output)}
        or not receipt.get("turn_id") or not receipt.get("completed_at")
    ):
        raise ValueError("The completed packet does not match its reserved input and receipt.")
    if any(isolation.get(key) != value for key, value in {
        "model": request["model"], "effort": request["effort"], "ephemeral": True,
        "provider": "openai", "empty_workspace": True, "approval_policy": "never",
        "permission_profile": {"id": "benchmark_packet", "extends": None},
        "sandbox": {"type": "readOnly", "networkAccess": False},
        "instruction_sources": [], "thread_environments": [], "runtime_workspace_roots": [],
    }.items()) or not isolation.get("thread_id") or not isolation.get("codex_session_id"):
        raise packet.PacketIsolationError("The completed packet lacks the approved isolation evidence.")
    price = receipt.get("cost_usd")
    if price is not None and (
        type(price) not in {int, float} or not math.isfinite(price) or price < 0
    ):
        raise ValueError("The receipt contains invalid USD pricing.")
    return output, {
        "session": handoff["session"], "thread_id": isolation["thread_id"],
        "codex_session_id": isolation["codex_session_id"], "turn_id": receipt["turn_id"],
        "role": request["role"], "model": isolation["model"], "effort": isolation["effort"],
        "packet_sha256": handoff["packet_sha256"], "receipt_sha256": commissioning.digest(receipt_bytes),
        "output_sha256": commissioning.digest(output), "usage": receipt.get("usage"),
        "cost_usd": price, "pricing": "unpriced" if price is None else "priced",
    }
