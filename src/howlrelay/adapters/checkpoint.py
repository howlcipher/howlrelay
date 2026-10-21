"""HowlForge worker checkpoints (`howlforge.checkpoint/v1`) as continuity evidence.

A HowlForge handoff bundle is a directory holding `checkpoint.json` plus
summary files; `howlforge handoff validate <dir>` checks it. HowlRelay reads
the checkpoint off disk (no package dependency on HowlForge) and reports what
the last worker completed, what remains, and whether it is safe to resume.
Only `howlforge.checkpoint/v1` documents are read; anything else named
`checkpoint.json` is ignored.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from howlrelay.adapters.base import BaseEvidenceCollector
from howlrelay.model import Evidence, EvidenceType

CHECKPOINT_SCHEMA = "howlforge.checkpoint/v1"
_IGNORED_DIRS = {".git", "node_modules", "build", "dist", ".venv", "venv", "__pycache__", ".tox"}
_MAX_DEPTH = 5


class CheckpointCollector(BaseEvidenceCollector):
    """Collects HowlForge worker checkpoints found in the repository."""

    def collector_name(self) -> str:
        return "howlforge_checkpoint"

    def discover(self, repo_path: Path) -> List[Path]:
        found: List[Path] = []
        root_depth = len(repo_path.parts)
        for current, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in _IGNORED_DIRS]
            if len(Path(current).parts) - root_depth >= _MAX_DEPTH:
                dirs[:] = []
            if "checkpoint.json" in files:
                found.append(Path(current) / "checkpoint.json")
        return sorted(found)

    def load(self, path: Path) -> Dict[str, Any]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != CHECKPOINT_SCHEMA:
            return {}
        return data

    def collect(self, repo_path: Path) -> List[Evidence]:
        evidence: List[Evidence] = []
        for path in self.discover(repo_path):
            try:
                data = self.load(path)
            except (OSError, ValueError):
                continue
            if not data:
                continue
            task = str(data.get("task_id", path.parent.name))
            completed = [str(x) for x in data.get("completed") or []]
            remaining = [str(x) for x in data.get("remaining") or []]
            commit = str(data.get("last_verified_commit") or "")
            safe = bool(data.get("safe_to_resume"))
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
                        "changed_files": [str(x) for x in data.get("changed_files") or []],
                        "relative_path": str(path.relative_to(repo_path)),
                    },
                )
            )
        return evidence
