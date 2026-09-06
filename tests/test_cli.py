"""Tests for HowlRelay CLI commands (status, handoff, brief)."""

from pathlib import Path
import pytest

from howlrelay.cli.main import main


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "howlrelay" in captured.out
    assert "status" in captured.out
    assert "handoff" in captured.out
    assert "brief" in captured.out


def test_cli_no_args(capsys):
    # When called with no subcommand, main prints help and returns 0
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 0


def test_cli_status(capsys):
    repo_path = str(Path(__file__).resolve().parent.parent)
    ret = main(["status", "--repo", repo_path])
    assert ret == 0
    captured = capsys.readouterr()
    assert "# Status: howlrelay" in captured.out
    assert "Synchronous Alignment" in captured.out


def test_cli_handoff(capsys):
    repo_path = str(Path(__file__).resolve().parent.parent)
    ret = main(["handoff", "--repo", repo_path])
    assert ret == 0
    captured = capsys.readouterr()
    assert "# Asynchronous Handoff: howlrelay" in captured.out
    assert "## Objective" in captured.out
    assert "## Synchronous Meeting Recommendation" in captured.out
    assert "## Epistemic Provenance" in captured.out


def test_cli_handoff_json_format(capsys):
    repo_path = str(Path(__file__).resolve().parent.parent)
    ret = main(["handoff", "--repo", repo_path, "--format", "json"])
    assert ret == 0
    captured = capsys.readouterr()
    assert '"repo_name": "howlrelay"' in captured.out
    assert '"meeting": {' in captured.out


def test_cli_brief(capsys):
    repo_path = str(Path(__file__).resolve().parent.parent)
    ret = main(["brief", "--repo", repo_path])
    assert ret == 0
    captured = capsys.readouterr()
    assert "# Team Brief: howlrelay" in captured.out
    assert "## Executive Summary" in captured.out
    assert "## Meaningful Progress" in captured.out


def test_cli_update_handoff(tmp_path: Path):
    # Initialize a mock git repo with a HANDOFF.md
    (tmp_path / "HANDOFF.md").write_text("# Initial Handoff\n## Objective\nInitial objective\n")
    ret = main(["handoff", "--repo", str(tmp_path), "--update-handoff"])
    assert ret == 0
    content = (tmp_path / "HANDOFF.md").read_text()
    assert "# Asynchronous Handoff:" in content
