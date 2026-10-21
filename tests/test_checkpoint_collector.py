"""HowlForge worker checkpoints (howlforge.checkpoint/v1) feed HowlRelay's handoff."""

import json
import shutil
from pathlib import Path

from howlrelay.adapters.checkpoint import CheckpointCollector
from howlrelay.engine import HandoffEngine
from howlrelay.model import EvidenceType

# Copied from howlcipher/howlforge examples/handoffs/HOWL-0042/checkpoint.json.
FIXTURE = Path(__file__).parent / "fixtures" / "howlforge-bundle" / "checkpoint.json"


def bundle(repo: Path, name: str = "HOWL-0042") -> Path:
    target = repo / ".howlforge" / "handoffs" / name
    target.mkdir(parents=True)
    shutil.copy(FIXTURE, target / "checkpoint.json")
    return target


def test_reads_a_real_howlforge_checkpoint(tmp_path):
    bundle(tmp_path)
    (evidence,) = CheckpointCollector().collect(tmp_path)
    assert evidence.type == EvidenceType.WORKER_CHECKPOINT
    assert evidence.ref == "checkpoint:HOWL-0042"
    assert evidence.metadata["safe_to_resume"] is True
    assert evidence.metadata["remaining"] == ["integration tests", "documentation"]
    assert "safe to resume from 5549653fda43" in evidence.description


def test_ignores_other_checkpoint_files_and_ignored_dirs(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "checkpoint.json").write_text(json.dumps({"epoch": 3}))
    (tmp_path / "node_modules" / "x").mkdir(parents=True)
    shutil.copy(FIXTURE, tmp_path / "node_modules" / "x" / "checkpoint.json")
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "checkpoint.json").write_text("{not json")
    assert CheckpointCollector().collect(tmp_path) == []


def test_engine_uses_the_checkpoint_when_continuity_docs_are_silent(tmp_path):
    bundle(tmp_path)
    envelope = HandoffEngine().inspect_repo(tmp_path)
    actions = [a.action for a in envelope.work_state.next_actions]
    assert "Resume HOWL-0042: integration tests" in actions
    assert "internal/runtimes/runtime.go" in envelope.files_involved
