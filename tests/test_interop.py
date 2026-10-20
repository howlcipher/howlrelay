"""HowlRelay's side of the Howl interop contract (docs/INTEROP.md in howlcipher/howl)."""

import json
from pathlib import Path

from howlrelay import __version__
from howlrelay.adapters.continuity import ContinuityCollector
from howlrelay.adapters.howldream import HowlDreamCollector
from howlrelay.cli.main import main
from howlrelay.model import HandoffEnvelope


def _envelope(tmp_path: Path, run: str, **fields) -> None:
    run_dir = tmp_path / ".howldream" / "runs" / run
    run_dir.mkdir(parents=True)
    data = {"exploration_id": run, "objective": "o", "candidates": [],
            "authority": {"type": "ADVISORY", "executable": False}, **fields}
    (run_dir / "exploration_envelope.json").write_text(json.dumps(data))


def test_only_the_envelope_howldream_writes_is_read(tmp_path):
    _envelope(tmp_path, "hd-good", schema_version="howl.exploration_result/v1")
    _envelope(tmp_path, "hd-request", schema_version="howl.exploration/v1")
    _envelope(tmp_path, "hd-none")
    refs = {e.ref for e in HowlDreamCollector().collect(tmp_path)}
    assert "run:hd-good" in refs
    assert "run:hd-request:unsupported_schema" in refs and "run:hd-request" not in refs
    assert "run:hd-none:unsupported_schema" in refs and "run:hd-none" not in refs


def test_howlproof_relay_handoff_is_used_when_there_is_no_handoff_md(tmp_path):
    (tmp_path / "howlproof-handoff.md").write_text("# Objective\n\nShip the parser.\n")
    context = ContinuityCollector().extract_structured_context(tmp_path)
    assert "Ship the parser" in context["objective"]
    (tmp_path / "HANDOFF.md").write_text("# Objective\n\nThe team's own handoff.\n")
    assert "team's own" in ContinuityCollector().extract_structured_context(tmp_path)["objective"]


def test_generator_version_is_the_package_version():
    assert HandoffEnvelope.model_fields["generator_version"].default_factory() == __version__


def test_interop_descriptor(capsys):
    assert main(["interop", "--json"]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["schema"] == "howl.interop/v1"
    assert (d["component"], d["version"]) == ("howlrelay", __version__)
    paths = {tuple(c["path"]) for c in d["commands"]}
    assert {("status",), ("handoff",), ("brief",), ("interop",)} <= paths
    assert d["consumes"] == [{"component": "howlframe", "command": [], "flags": ["--version"]}]
