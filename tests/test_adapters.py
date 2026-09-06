"""Tests for evidence collectors (Git, Continuity, Test, HowlFrame)."""

from pathlib import Path

from howlrelay.adapters.continuity import ContinuityCollector
from howlrelay.adapters.git import GitCollector
from howlrelay.adapters.howlframe import HowlFrameCollector
from howlrelay.adapters.test_runner import TestCollector
from howlrelay.model import EvidenceType


def test_git_collector_on_real_repo():
    repo_path = Path(__file__).resolve().parent.parent
    collector = GitCollector()

    assert collector.is_git_repo(repo_path)
    evidence = collector.collect(repo_path)
    assert len(evidence) > 0

    types = [e.type for e in evidence]
    assert EvidenceType.GIT_BRANCH in types or EvidenceType.GIT_STATUS in types


def test_continuity_collector(tmp_path: Path):
    collector = ContinuityCollector()

    # Empty dir
    evidence = collector.collect(tmp_path)
    audit = next(e for e in evidence if e.ref == "continuity_files_audit")
    assert audit.metadata["is_complete"] is False

    # Create dummy continuity docs
    (tmp_path / "HANDOFF.md").write_text(
        "# Current Handoff\n\n"
        "## Objective\nShip Milestone 1\n\n"
        "## Current State\nIn progress\n\n"
        "## Last Completed Work\n- Configured project\n\n"
        "## Blockers\nNone.\n\n"
        "## Next Recommended Action\n- Write unit tests\n\n"
        "## Exact Starting Commands\n```bash\npytest\n```\n"
    )
    (tmp_path / "DECISIONS.md").write_text(
        "# Architectural Decisions\n\n"
        "## ADR-0001: Use SQLite\n"
        "- **Date:** 2026-09-06\n"
        "- **Status:** Accepted\n"
        "- **Decision:** Use local sqlite\n"
        "- **Rationale:** Simple and zero server setup\n"
    )

    ctx = collector.extract_structured_context(tmp_path)
    assert ctx["objective"] == "Ship Milestone 1"
    assert "Configured project" in ctx["completed"]
    assert any("Write unit tests" in na.action for na in ctx["next_actions"])
    assert len(ctx["decisions"]) == 1
    assert "ADR-0001" in ctx["decisions"][0].decision


def test_test_collector(tmp_path: Path):
    collector = TestCollector()
    assert collector.collector_name() == "test_runner"

    # In tmp_path without tests
    ev = collector.collect(tmp_path)
    assert len(ev) == 1
    assert ev[0].ref == "no_tests_detected"


def test_howlframe_collector():
    collector = HowlFrameCollector()
    assert collector.collector_name() == "howlframe"
    repo_path = Path(__file__).resolve().parent.parent
    ev = collector.collect(repo_path)
    assert len(ev) == 1
    assert ev[0].type == EvidenceType.HOWLFRAME_POLICY
