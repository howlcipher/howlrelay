"""Tests for domain models, validation, and JSON/YAML serialization."""

import json
from howlrelay.model import (
    Blocker,
    ConfidenceLevel,
    Decision,
    Dependency,
    Evidence,
    EvidenceType,
    HandoffEnvelope,
    MeetingRecommendation,
    MeetingRecommendationState,
    NextAction,
    Risk,
    WorkItem,
    WorkState,
    WorkStatus,
)
from howlrelay.renderers.json_yaml import render_json, render_yaml


def test_work_state_serialization_roundtrip():
    ws = WorkState(
        repo_name="demo-repo",
        repo_root="/dev/demo-repo",
        work_item=WorkItem(objective="Build feature X"),
        status=WorkStatus.IN_PROGRESS,
        confidence=ConfidenceLevel.HIGH,
        completed=["Scaffold package", "Add tests"],
        active_work=["Implement adapter"],
        blockers=[
            Blocker(
                description="Blocked on credentials",
                reason="Waiting for vault access",
                severity="HIGH",
            )
        ],
        decisions=[
            Decision(
                decision="Use Python 3.10+",
                rationale="Required for typing and Pydantic v2 support",
                status="DECIDED",
            )
        ],
        dependencies=[
            Dependency(owner="infra", item="Vault role", status="PENDING")
        ],
        risks=[
            Risk(level="LOW", description="Local test execution speed")
        ],
        next_actions=[
            NextAction(action="Run full test suite", priority="IMMEDIATE")
        ],
        evidence=[
            Evidence(
                type=EvidenceType.GIT_BRANCH,
                ref="main",
                source="git",
                description="Active branch main",
            )
        ],
        meeting=MeetingRecommendation(
            recommendation=MeetingRecommendationState.NOT_REQUIRED,
            reason="Work progressing asynchronously",
            triggers=["all_decisions_resolved"],
        ),
    )

    json_str = render_json(ws)
    assert "Build feature X" in json_str
    data = json.loads(json_str)
    assert data["repo_name"] == "demo-repo"
    assert data["status"] == "in_progress"

    yaml_str = render_yaml(ws)
    assert "objective: Build feature X" in yaml_str
    assert "recommendation: NOT_REQUIRED" in yaml_str


def test_handoff_envelope_creation():
    ws = WorkState(
        repo_name="demo-repo",
        repo_root="/dev/demo-repo",
        work_item=WorkItem(objective="Handoff test"),
        status=WorkStatus.COMPLETED,
        confidence=ConfidenceLevel.HIGH,
        meeting=MeetingRecommendation(
            recommendation=MeetingRecommendationState.NOT_REQUIRED,
            reason="All work completed",
        ),
    )
    envelope = HandoffEnvelope(
        work_state=ws,
        files_involved=["src/main.py", "tests/test_main.py"],
        test_status="PASSED",
        continuation_instructions=["Deploy to staging"],
        exact_starting_commands=["git status"],
        generator_version="0.1.0",
    )

    assert envelope.test_status == "PASSED"
    assert len(envelope.files_involved) == 2
    assert envelope.continuation_instructions == ["Deploy to staging"]
