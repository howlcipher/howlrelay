"""HowlForge worker checkpoints (`howlforge.checkpoint/v1`) as continuity evidence.

A HowlForge handoff bundle is a directory holding `checkpoint.json` plus
summary files; `howlforge handoff validate <dir>` checks it. HowlRelay reads
the checkpoint off disk (no package dependency on HowlForge) and reports what
the last worker completed, what remains, and whether it is safe to resume.
Only `howlforge.checkpoint/v1` documents are read; anything else named
`checkpoint.json` is ignored.
"""

from datetime import datetime
import hashlib
import json
import os
import re
import stat
import time
from importlib.resources import files

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from pathlib import Path
from typing import Any, Dict, List

from howlrelay.adapters.base import BaseEvidenceCollector
from howlrelay.model import Evidence, EvidenceType

CHECKPOINT_SCHEMA = "howlforge.checkpoint/v1"
_IGNORED_DIRS = {".git", "node_modules", "build", "dist", ".venv", "venv", "__pycache__", ".tox"}
_MAX_DEPTH = 5
_MAX_ENTRIES = 4096
_MAX_BYTES = 1024 * 1024
_MAX_SECONDS = 2.0


def _validator():
    schemas = [json.loads(files("howlrelay").joinpath(
        f"schemas/{name}.schema.json").read_text())
        for name in ("checkpoint", "verification", "decisions")]
    # Forge's published IDs are relative references; use local URNs so the
    # resolver never resolves them against another schema's path or the network.

    def local_refs(value):
        if isinstance(value, dict):
            return {k: ("urn:" + v if k in ("$id", "$ref")
                        and isinstance(v, str) and v.startswith("howlforge.")
                        else local_refs(v)) for k, v in value.items()}
        if isinstance(value, list):
            return [local_refs(v) for v in value]
        return value
    schemas = [local_refs(schema) for schema in schemas]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas)
    checker = FormatChecker()

    @checker.checks("date-time", raises=(ValueError, TypeError))
    def timestamp(value):
        if not isinstance(value, str):
            return True  # The schema type validator rejects nonstrings.
        if not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?"
                r"(?:[Zz]|[+-]\d{2}:\d{2})", value):
            return False
        parsed = datetime.fromisoformat(value.upper().replace("Z", "+00:00"))
        return parsed.tzinfo is not None

    return Draft202012Validator(schemas[0], registry=registry, format_checker=checker)


_VALIDATOR = _validator()


def _open_confined(root: Path, relative: Path) -> int:
    # Each component is opened relative to its already-open parent. Neither
    # symlink replacement nor parent-directory rename can redirect the read.
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise OSError("Secure checkpoint reading is unsupported on this platform")
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in relative.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    finally:
        os.close(fd)


class CheckpointCollector(BaseEvidenceCollector):
    """Collects HowlForge worker checkpoints found in the repository."""

    def collector_name(self) -> str:
        return "howlforge_checkpoint"

    def discover(self, repo_path: Path) -> List[Path]:
        found: List[Path] = []
        if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
            return found
        deadline = time.monotonic() + _MAX_SECONDS
        pending = [(Path(), 0)]
        count = 0
        while pending and count < _MAX_ENTRIES and time.monotonic() < deadline:
            relative, depth = pending.pop()
            try:
                if relative.parts:
                    fd = _open_confined(repo_path, relative / ".")
                else:
                    fd = os.open(repo_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try:
                    with os.scandir(fd) as entries:
                        for entry in entries:
                            count += 1
                            if count > _MAX_ENTRIES or time.monotonic() >= deadline:
                                break
                            child = relative / entry.name
                            if entry.name == "checkpoint.json":
                                if entry.is_file(follow_symlinks=False):
                                    found.append(repo_path / child)
                            elif (depth < _MAX_DEPTH and entry.name not in _IGNORED_DIRS
                                  and entry.is_dir(follow_symlinks=False)):
                                pending.append((child, depth + 1))
                finally:
                    os.close(fd)
            except OSError:
                continue
        return sorted(found)

    def load(self, path: Path, repo_path: Path = None) -> Dict[str, Any]:
        root = repo_path if repo_path is not None else path.parent
        relative = path.relative_to(root)
        if not relative.parts or any(p in ("..", ".") for p in relative.parts):
            raise ValueError("Invalid checkpoint path")
        fd = _open_confined(root, relative)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_BYTES:
                raise ValueError("Checkpoint must be a bounded regular file")
            deadline = time.monotonic() + _MAX_SECONDS
            payload = bytearray()
            while len(payload) <= _MAX_BYTES:
                if time.monotonic() >= deadline:
                    raise ValueError("Checkpoint read budget exceeded")
                chunk = os.read(fd, min(65536, _MAX_BYTES + 1 - len(payload)))
                if not chunk:
                    break
                payload.extend(chunk)
            if len(payload) > _MAX_BYTES:
                raise ValueError("Checkpoint byte budget exceeded")
        finally:
            os.close(fd)
        data = json.loads(payload)
        if not _VALIDATOR.is_valid(data):
            return {}
        for value in data.get("changed_files", []):
            normalized = value.replace("\\", "/")
            if (normalized.startswith("/") or ".." in normalized.split("/")
                    or (len(normalized) > 1 and normalized[1] == ":")):
                return {}
        data["_source_sha256"] = hashlib.sha256(payload).hexdigest()
        return data

    def collect(self, repo_path: Path) -> List[Evidence]:
        evidence: List[Evidence] = []
        deadline = time.monotonic() + _MAX_SECONDS
        for path in self.discover(repo_path)[:64]:
            if time.monotonic() >= deadline:
                break
            try:
                data = self.load(path, repo_path)
            except (OSError, ValueError, RecursionError):
                continue
            if not data:
                continue
            task = data["task_id"]
            completed = data["completed"]
            remaining = data["remaining"]
            commit = data["last_verified_commit"]
            safe = data["safe_to_resume"]
            evidence.append(
                Evidence(
                    type=EvidenceType.WORKER_CHECKPOINT,
                    ref=f"checkpoint:{task}",
                    source="howlforge",
                    description=(
                        f"Worker checkpoint for {task} ({data.get('role', '?')} on "
                        f"{data.get('runtime', '?')}): status {data.get('status', '?')}, "
                        f"{len(completed)} completed, {len(remaining)} remaining, "
                        f"{'safe' if safe else 'NOT safe'} to resume"
                        + (f" from {commit[:12]}" if commit else "")
                        + "."
                    ),
                    metadata={
                        "task_id": task,
                        "status": data.get("status"),
                        "safe_to_resume": safe,
                        "handoff_reason": data.get("handoff_reason"),
                        "last_verified_commit": commit,
                        "completed": completed,
                        "remaining": remaining,
                        "changed_files": data.get("changed_files", []),
                        "relative_path": str(path.relative_to(repo_path)),
                        "source_sha256": data["_source_sha256"],
                        "authorization": "none; worker assertion only",
                        "checkpoint": {k: v for k, v in data.items()
                                       if k != "_source_sha256"},
                    },
                )
            )
        return evidence
