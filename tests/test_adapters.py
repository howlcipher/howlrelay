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


def test_continuity_collector_heterogeneous_formats(tmp_path: Path):
    collector = ContinuityCollector()

    # Create HowlCreate-style numbered headers and docs/journal layout
    (tmp_path / "HANDOFF.md").write_text(
        "# HowlCreate Engineering Handoff\n\n"
        "**Current Status**: Milestone 1 Complete / Actively Dogfooding\n\n"
        "## 1. System Summary\n\n"
        "Computational creativity and open-ended problem-solving layer.\n\n"
        "## 2. What Works Right Now\n\n"
        "- 12 composable operators implemented and tested.\n"
        "- Lineage DAG tracks ancestry.\n\n"
        "## 3. What Is in Progress / Known Limitations\n\n"
        "- Dogfood Target 3 cross-repo run analysis.\n\n"
        "## 4. Key Files & Architecture\n\n"
        "- `src/howlcreate/models/idea.py`\n"
        "- `src/howlcreate/engine/pipeline.py`\n\n"
        "## 5. Commands to Resume Work\n\n"
        "```bash\n"
        "pytest -v\n"
        "howlcreate --version\n"
        "```\n"
    )

    docs_journal = tmp_path / "docs" / "journal"
    docs_journal.mkdir(parents=True)
    (docs_journal / "2026-09-06-session-01.md").write_text(
        "# Session 01\n\nCompleted initial release."
    )

    dogfood_dir = tmp_path / "dogfood"
    dogfood_dir.mkdir()
    (dogfood_dir / "01_test.json").write_text("{}")
    (dogfood_dir / "01_test.md").write_text("# Dogfood 1")

    evidence = collector.collect(tmp_path)
    audit = next(e for e in evidence if e.ref == "continuity_files_audit")
    # JOURNAL.md should be discovered via docs/journal/
    assert "JOURNAL.md" in audit.metadata["found"]

    ctx = collector.extract_structured_context(tmp_path)
    assert "Computational creativity" in ctx["objective"]
    assert len(ctx["completed"]) >= 2
    assert any("12 composable operators" in item for item in ctx["completed"])
    assert len(ctx["active_work"]) >= 1
    assert any("Dogfood Target 3" in item for item in ctx["active_work"])
    assert len(ctx["starting_commands"]) == 2
    assert "pytest -v" in ctx["starting_commands"]
    assert len(ctx["key_files"]) >= 2


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


def test_git_collector_porcelain_parsing(monkeypatch, tmp_path: Path):
    collector = GitCollector()

    # Mock _run_git to simulate porcelain output with leading spaces, renames, and staging
    porcelain_output = (
        " M src/modified_unstaged.py\n"
        "M  src/staged_only.py\n"
        "MM src/staged_and_modified.py\n"
        "R  src/old_name.py -> src/renamed.py\n"
        "?? untracked.txt\n"
    )

    def mock_run_git(repo_path, args):
        if args == ["rev-parse", "--is-inside-work-tree"]:
            return "true"
        if args == ["status", "--porcelain"]:
            return porcelain_output
        return None

    monkeypatch.setattr(collector, "_run_git", mock_run_git)

    evidence = collector.collect(tmp_path)
    status_ev = next(e for e in evidence if e.type == EvidenceType.GIT_STATUS)

    assert status_ev.metadata["staged_count"] == 3
    assert status_ev.metadata["staged_files"] == [
        "src/staged_only.py",
        "src/staged_and_modified.py",
        "src/renamed.py",
    ]
    assert status_ev.metadata["modified_count"] == 2
    assert status_ev.metadata["modified_files"] == [
        "src/modified_unstaged.py",
        "src/staged_and_modified.py",
    ]
    assert status_ev.metadata["untracked_count"] == 1
    assert status_ev.metadata["untracked_files"] == ["untracked.txt"]
    assert "src/modified_unstaged.py" in status_ev.metadata["all_uncommitted_files"]
    assert "src/renamed.py" in status_ev.metadata["all_uncommitted_files"]


def test_git_collector_deep_diff_and_test_parity(monkeypatch, tmp_path: Path):
    collector = GitCollector()

    # Case 1: Core modified, no tests -> test_parity_risk = True
    diff_core_only = (
        "diff --git a/src/core.py b/src/core.py\n"
        "@@ -10,0 +11,5 @@ def process_transaction(amount):\n"
        "+    verify(amount)\n"
    )

    def mock_run_git_core(repo_path, args):
        if args == ["diff", "-U0"]:
            return diff_core_only
        if args == ["diff", "--cached", "-U0"]:
            return ""
        return None

    monkeypatch.setattr(collector, "_run_git", mock_run_git_core)
    res = collector.analyze_diff(tmp_path)
    assert res["has_uncommitted_diffs"] is True
    assert "src/core.py" in res["layers"]["core"]
    assert len(res["layers"]["tests"]) == 0
    assert res["test_parity_risk"] is True
    assert "def process_transaction" in res["modified_symbols"]

    # Case 2: Core modified AND tests modified -> test_parity_risk = False
    diff_with_tests = (
        "diff --git a/src/core.py b/src/core.py\n"
        "@@ -10,0 +11,5 @@ def process_transaction(amount):\n"
        "+    verify(amount)\n"
        "diff --git a/tests/test_core.py b/tests/test_core.py\n"
        "@@ -20,0 +21,4 @@ def test_process_transaction():\n"
        "+    assert True\n"
    )

    def mock_run_git_tests(repo_path, args):
        if args == ["diff", "-U0"]:
            return diff_with_tests
        if args == ["diff", "--cached", "-U0"]:
            return ""
        return None

    monkeypatch.setattr(collector, "_run_git", mock_run_git_tests)
    res_with_tests = collector.analyze_diff(tmp_path)
    assert res_with_tests["test_parity_risk"] is False
    assert len(res_with_tests["layers"]["tests"]) == 1


def test_git_collector_blocker_staleness(monkeypatch, tmp_path: Path):
    collector = GitCollector()

    def mock_run_git(repo_path, args):
        if args == ["rev-parse", "--is-inside-work-tree"]:
            return "true"
        if args[:4] == ["log", "-1", "--format=%H", "-S"]:
            return "abc12345"
        if args[:2] == ["rev-list", "--count"]:
            return "4\n"
        return None

    monkeypatch.setattr(collector, "_run_git", mock_run_git)

    age, is_stale = collector.compute_blocker_staleness(tmp_path, "Third party outage on API")
    assert age == 4
    assert is_stale is True
