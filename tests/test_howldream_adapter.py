"""
test_howldream_adapter.py

Unit and integration tests for HowlRelay's HowlDream exploration adapter:
1. Collector identification.
2. Discovery and extraction of valid exploration envelopes.
3. Strict enforcement of advisory authority and failure-closed escalation handling.
4. Full integration with HandoffEngine.
"""

import json
from pathlib import Path
import pytest

from howlrelay.adapters.howldream import HowlDreamCollector
from howlrelay.engine import HandoffEngine
from howlrelay.model import EvidenceType


def test_collector_name():
    collector = HowlDreamCollector()
    assert collector.collector_name() == "howldream"


def test_runtime_evidence_when_no_runs(tmp_path: Path):
    collector = HowlDreamCollector()
    evidence = collector.collect(tmp_path)
    assert len(evidence) == 1
    ev = evidence[0]
    assert ev.type == EvidenceType.HOWLDREAM_EXPLORATION
    assert ev.ref == "runtime_status"
    assert ev.metadata.get("envelope_count") == 0
    assert ev.metadata.get("authority", {}).get("executable") is False
    assert ev.metadata.get("authority", {}).get("type") == "ADVISORY"


def test_collects_valid_exploration_envelope(tmp_path: Path):
    # Set up mock .howldream/runs/hd-run-001/exploration_envelope.json
    run_dir = tmp_path / ".howldream" / "runs" / "hd-run-001"
    run_dir.mkdir(parents=True, exist_ok=True)
    envelope_data = {
        "schema_version": "howl.exploration_result/v1",
        "exploration_id": "hd-run-001",
        "parent_request_id": "req-001",
        "objective": "Investigate pipeline queue ingestion timeout",
        "originating_component": "howlplane",
        "authority": {"type": "ADVISORY", "executable": False},
        "candidates": [
            {"candidate_id": "cand-01", "status": "LOCALLY_VERIFIED", "text": "Proposal A"},
            {"candidate_id": "cand-02", "status": "UNRESOLVED", "text": "Proposal B"},
        ],
        "unresolved_assumptions": ["Assumption 1", "Assumption 2"],
        "contradictions": ["Contradiction 1"],
        "recommended_disposition": "INVESTIGATE",
    }
    env_file = run_dir / "exploration_envelope.json"
    env_file.write_text(json.dumps(envelope_data), encoding="utf-8")

    collector = HowlDreamCollector()
    evidence = collector.collect(tmp_path)

    # 1 runtime status + 1 envelope run evidence
    assert len(evidence) == 2
    run_ev = next(e for e in evidence if e.ref == "run:hd-run-001")
    assert run_ev.type == EvidenceType.HOWLDREAM_EXPLORATION
    assert run_ev.metadata["candidate_count"] == 2
    assert run_ev.metadata["unresolved_assumptions_count"] == 2
    assert run_ev.metadata["contradictions_count"] == 1
    assert run_ev.metadata["recommended_disposition"] == "INVESTIGATE"
    assert run_ev.metadata["authority"]["executable"] is False
    assert run_ev.metadata["authority"]["type"] == "ADVISORY"


def test_fails_closed_on_authority_escalation(tmp_path: Path):
    run_dir = tmp_path / ".howldream" / "runs" / "hd-exploit-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    malicious_data = {
        "schema_version": "howl.exploration_result/v1",
        "exploration_id": "hd-exploit-run",
        "parent_request_id": "req-999",
        "objective": "Inject execution authority",
        "authority": {"type": "EXECUTIVE", "executable": True},
        "candidates": [],
    }
    env_file = run_dir / "exploration_envelope.json"
    env_file.write_text(json.dumps(malicious_data), encoding="utf-8")

    collector = HowlDreamCollector()
    evidence = collector.collect(tmp_path)

    violation_ev = next(e for e in evidence if "authority_violation" in e.ref)
    assert violation_ev.metadata["authority_violation"] is True
    assert violation_ev.metadata["authority"]["executable"] is False
    assert "SECURITY WARNING" in violation_ev.description


def test_handoff_engine_integrates_howldream_collector(tmp_path: Path):
    run_dir = tmp_path / ".howldream" / "runs" / "hd-run-002"
    run_dir.mkdir(parents=True, exist_ok=True)
    envelope_data = {
        "schema_version": "howl.exploration_result/v1",
        "exploration_id": "hd-run-002",
        "parent_request_id": "req-002",
        "objective": "Explore latency reduction",
        "authority": {"type": "ADVISORY", "executable": False},
        "candidates": [{"candidate_id": "cand-01", "status": "LOCALLY_VERIFIED", "text": "Opt"}],
        "unresolved_assumptions": ["Assumption A"],
        "contradictions": [],
        "recommended_disposition": "ACCEPT_FOR_DEVELOPMENT",
    }
    (run_dir / "exploration_envelope.json").write_text(json.dumps(envelope_data))

    engine = HandoffEngine()
    envelope = engine.inspect_repo(tmp_path)

    howldream_evs = [
        e for e in envelope.work_state.evidence if e.type == EvidenceType.HOWLDREAM_EXPLORATION
    ]
    assert len(howldream_evs) >= 2
    run_ev = next(e for e in howldream_evs if e.ref == "run:hd-run-002")
    assert run_ev.metadata["candidate_count"] == 1
    assert run_ev.metadata["authority"]["executable"] is False
