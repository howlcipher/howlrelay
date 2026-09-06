"""Tests for evidence-grounded meeting recommendation reasoning."""

from howlrelay.model import (
    Blocker,
    Decision,
    Evidence,
    EvidenceType,
    MeetingRecommendationState,
)
from howlrelay.reasoning.meeting import MeetingReasoningEngine


def test_meeting_not_required_when_healthy():
    engine = MeetingReasoningEngine()
    rec = engine.evaluate(
        evidence=[
            Evidence(
                type=EvidenceType.GIT_COMMIT,
                ref="12345678",
                source="git",
                description="Initial commit",
            )
        ],
        decisions=[
            Decision(
                decision="Adopt ADR-0001",
                rationale="Agreed upon",
                status="DECIDED",
            )
        ],
        blockers=[],
        dependencies=[],
        risks=[],
        test_status="PASSED",
        known_failures=[],
        has_git_repo=True,
        has_continuity_docs=True,
    )
    assert rec.recommendation == MeetingRecommendationState.NOT_REQUIRED
    assert "NOT_REQUIRED" in rec.reason or "synchronous discussion" in rec.reason
    assert "all_decisions_resolved" in rec.triggers


def test_meeting_requires_human_decision():
    engine = MeetingReasoningEngine()
    rec = engine.evaluate(
        evidence=[
            Evidence(
                type=EvidenceType.GIT_COMMIT,
                ref="12345678",
                source="git",
                description="Commit",
            )
        ],
        decisions=[
            Decision(
                decision="Migrate database to PostgreSQL",
                rationale="Pending architectural review",
                status="UNRESOLVED",
            )
        ],
        blockers=[],
        dependencies=[],
        risks=[],
        test_status="PASSED",
        known_failures=[],
        has_git_repo=True,
        has_continuity_docs=True,
    )
    assert rec.recommendation == MeetingRecommendationState.REQUIRES_HUMAN_DECISION
    assert "unresolved architectural or policy decision" in rec.reason


def test_meeting_recommended_on_critical_blocker():
    engine = MeetingReasoningEngine()
    rec = engine.evaluate(
        evidence=[
            Evidence(
                type=EvidenceType.GIT_COMMIT,
                ref="12345678",
                source="git",
                description="Commit",
            )
        ],
        decisions=[],
        blockers=[
            Blocker(
                description="Production database credentials revoked",
                reason="Incident in progress",
                severity="CRITICAL",
            )
        ],
        dependencies=[],
        risks=[],
        test_status="PASSED",
        known_failures=[],
        has_git_repo=True,
        has_continuity_docs=True,
    )
    assert rec.recommendation == MeetingRecommendationState.RECOMMENDED
    assert "high-priority blocker" in rec.reason


def test_meeting_insufficient_evidence():
    engine = MeetingReasoningEngine()
    # Not a git repo
    rec = engine.evaluate(
        evidence=[],
        decisions=[],
        blockers=[],
        dependencies=[],
        risks=[],
        test_status="UNKNOWN",
        known_failures=[],
        has_git_repo=False,
        has_continuity_docs=False,
    )
    assert rec.recommendation == MeetingRecommendationState.INSUFFICIENT_EVIDENCE
    assert "not a Git repository" in rec.reason
