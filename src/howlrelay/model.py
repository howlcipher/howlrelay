"""Core domain models for HowlRelay.

Normalized representation of work state, evidence, decisions, blockers,
dependencies, risks, next actions, and meeting recommendations.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from howlrelay.policy import check_prohibited_keys, SurveillanceSignalError


class EvidenceType(str, Enum):
    GIT_COMMIT = "git_commit"
    GIT_DIFF = "git_diff"
    GIT_BRANCH = "git_branch"
    GIT_STATUS = "git_status"
    TEST_RUN = "test_run"
    CONTINUITY_DOC = "continuity_doc"
    HOWLFRAME_POLICY = "howlframe_policy"
    DECISION_RECORD = "decision_record"
    CUSTOM = "custom"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class WorkStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    PAUSED = "paused"
    UNKNOWN = "unknown"


class MeetingRecommendationState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    RECOMMENDED = "RECOMMENDED"
    REQUIRES_HUMAN_DECISION = "REQUIRES_HUMAN_DECISION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Evidence(BaseModel):
    """An observable, verifiable piece of factual data with provenance."""
    type: EvidenceType
    ref: str
    source: str
    description: str
    fingerprint: Optional[str] = None
    collected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata_safety(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        violations = check_prohibited_keys(v)
        if violations:
            raise SurveillanceSignalError(
                f"Prohibited surveillance signals found in evidence metadata: {violations}"
            )
        return v


class Decision(BaseModel):
    """An explicit architectural, design, or implementation choice."""
    decision: str
    rationale: str
    status: str = "DECIDED"  # DECIDED, PROPOSED, UNRESOLVED
    evidence_refs: List[str] = Field(default_factory=list)
    decided_at: Optional[str] = None
    decided_by: Optional[str] = None


class Blocker(BaseModel):
    """An active obstacle preventing work progression."""
    description: str
    reason: str
    dependency_ref: Optional[str] = None
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL


class Dependency(BaseModel):
    """An external or team dependency."""
    owner: str
    item: str
    status: str = "PENDING"  # PENDING, MET, BLOCKED


class Risk(BaseModel):
    """An identified technical or operational risk."""
    level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    mitigation: Optional[str] = None


class NextAction(BaseModel):
    """A concrete, actionable next step for an engineer or AI agent."""
    action: str
    owner: Optional[str] = None
    priority: str = "NEXT"  # IMMEDIATE, NEXT, LATER
    command: Optional[str] = None


class MeetingRecommendation(BaseModel):
    """Evidence-based recommendation regarding whether synchronous alignment is required."""
    recommendation: MeetingRecommendationState
    reason: str
    triggers: List[str] = Field(default_factory=list)


class WorkItem(BaseModel):
    """The high-level workstream or objective being tracked."""
    id: Optional[str] = None
    objective: str
    description: Optional[str] = None


class WorkState(BaseModel):
    """Normalized snapshot of workstream state."""
    repo_name: str
    repo_root: str
    work_item: WorkItem
    status: WorkStatus = WorkStatus.UNKNOWN
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    completed: List[str] = Field(default_factory=list)
    active_work: List[str] = Field(default_factory=list)
    blockers: List[Blocker] = Field(default_factory=list)
    decisions: List[Decision] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    next_actions: List[NextAction] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    meeting: MeetingRecommendation
    missing_information: List[str] = Field(default_factory=list)
    gathered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    schema_version: str = "1.0.0"


class HandoffEnvelope(BaseModel):
    """Complete asynchronous handoff package for an incoming engineer or AI agent."""
    work_state: WorkState
    files_involved: List[str] = Field(default_factory=list)
    tests_run: List[Dict[str, Any]] = Field(default_factory=list)
    test_status: str = "UNKNOWN"  # PASSED, FAILED, NOT_RUN, PARTIAL, UNKNOWN
    known_failures: List[str] = Field(default_factory=list)
    continuation_instructions: List[str] = Field(default_factory=list)
    exact_starting_commands: List[str] = Field(default_factory=list)
    generator_version: str = "0.1.0"
    observed_facts: List[str] = Field(default_factory=list)
    inferred_state: List[str] = Field(default_factory=list)
