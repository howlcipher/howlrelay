"""Core HandoffEngine for HowlRelay.

Orchestrates evidence collectors, builds normalized WorkState and HandoffEnvelope,
and evaluates meeting recommendations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from howlrelay import __version__
from howlrelay.adapters.continuity import ContinuityCollector
from howlrelay.adapters.git import GitCollector
from howlrelay.adapters.howlframe import HowlFrameCollector
from howlrelay.adapters.howldream import HowlDreamCollector
from howlrelay.adapters.test_runner import TestCollector
from howlrelay.model import (
    Blocker,
    ConfidenceLevel,
    Decision,
    Dependency,
    Evidence,
    EvidenceType,
    HandoffEnvelope,
    NextAction,
    Risk,
    WorkItem,
    WorkState,
    WorkStatus,
)
from howlrelay.reasoning.meeting import MeetingReasoningEngine


class HandoffEngine:
    """Core coordinator for evidence gathering and handoff generation."""

    def __init__(
        self,
        git_collector: Optional[GitCollector] = None,
        continuity_collector: Optional[ContinuityCollector] = None,
        test_collector: Optional[TestCollector] = None,
        howlframe_collector: Optional[HowlFrameCollector] = None,
        howldream_collector: Optional[HowlDreamCollector] = None,
        meeting_engine: Optional[MeetingReasoningEngine] = None,
    ):
        self.git_collector = git_collector or GitCollector()
        self.continuity_collector = continuity_collector or ContinuityCollector()
        self.test_collector = test_collector or TestCollector()
        self.howlframe_collector = howlframe_collector or HowlFrameCollector()
        self.howldream_collector = howldream_collector or HowlDreamCollector()
        self.meeting_engine = meeting_engine or MeetingReasoningEngine()

    def inspect_repo(self, repo_path: Path, run_tests: bool = False) -> HandoffEnvelope:
        """Inspect a repository and generate an authoritative HandoffEnvelope."""
        repo_path = repo_path.resolve()
        repo_name = repo_path.name

        # 1. Gather evidence from collectors
        evidence: List[Evidence] = []
        evidence.extend(self.git_collector.collect(repo_path))
        evidence.extend(self.continuity_collector.collect(repo_path))
        evidence.extend(self.test_collector.collect(repo_path))
        evidence.extend(self.howlframe_collector.collect(repo_path))
        evidence.extend(self.howldream_collector.collect(repo_path))

        # 2. Extract structured context from continuity documents
        context = self.continuity_collector.extract_structured_context(repo_path)
        objective = context["objective"]
        completed = context["completed"]
        active_work = context["active_work"]
        blockers: List[Blocker] = context["blockers"]
        decisions: List[Decision] = context["decisions"]
        next_actions: List[NextAction] = context["next_actions"]
        known_failures: List[str] = context["known_failures"]
        starting_commands: List[str] = context["starting_commands"]
        continuation_instructions: List[str] = context["continuation_instructions"]

        # 3. Process Git evidence for files involved & working tree facts
        files_involved: List[str] = []
        is_git_repo = self.git_collector.is_git_repo(repo_path)
        has_uncommitted = False

        for ev in evidence:
            if ev.type == EvidenceType.GIT_STATUS:
                all_uncommitted = ev.metadata.get("all_uncommitted_files", [])
                files_involved.extend(all_uncommitted)
                if all_uncommitted:
                    has_uncommitted = True

        # When working tree is clean, surface key files from continuity or HEAD modified files
        if not files_involved:
            if context.get("key_files"):
                files_involved.extend(context["key_files"])
            for ev in evidence:
                if (
                    ev.type == EvidenceType.GIT_COMMIT
                    and ev.metadata.get("head_modified_files")
                ):
                    files_involved.extend(ev.metadata["head_modified_files"])

        files_involved = list(dict.fromkeys(files_involved))

        # If no next actions were explicitly given, but active work exists, populate next action
        if not next_actions and active_work:
            next_actions.append(
                NextAction(action=f"Continue active priority: {active_work[0]}", priority="NEXT")
            )

        # 4. Process test verification evidence
        tests_run: List[Dict[str, Any]] = []
        test_status = "NOT_RUN"
        if run_tests:
            test_res = self.test_collector.run_pytest_verification(repo_path)
            tests_run.append(test_res)
            test_status = test_res.get("status", "UNKNOWN")
            if not test_res.get("passed", False) and test_res.get("executed", False):
                known_failures.append(f"Pytest run failed: {test_res.get('summary')}")
        else:
            # Check cache evidence
            for ev in evidence:
                if ev.type == EvidenceType.TEST_RUN and ev.metadata.get("cache"):
                    failed_count = ev.metadata["cache"].get("failed_count", 0)
                    if failed_count > 0:
                        test_status = "PARTIAL"
                        known_failures.extend(ev.metadata["cache"].get("failed_tests", []))
                    else:
                        test_status = "UNKNOWN"

        # 5. Determine WorkStatus and ConfidenceLevel
        status = WorkStatus.IN_PROGRESS
        if blockers:
            status = WorkStatus.BLOCKED
        elif not has_uncommitted and not active_work and completed:
            status = WorkStatus.COMPLETED
        elif not is_git_repo or (not completed and not active_work):
            status = WorkStatus.UNKNOWN

        confidence = (
            ConfidenceLevel.HIGH
            if (is_git_repo and (decisions or completed) and (completed or not has_uncommitted))
            else (ConfidenceLevel.MEDIUM if is_git_repo else ConfidenceLevel.LOW)
        )

        # 6. Evaluate meeting recommendation & risks
        has_continuity_docs = any(
            ev.type == EvidenceType.CONTINUITY_DOC for ev in evidence
        )
        dependencies: List[Dependency] = []
        risks: List[Risk] = []

        # Check staleness of active blockers against git commit history
        if is_git_repo:
            for b in blockers:
                age, is_stale = self.git_collector.compute_blocker_staleness(
                    repo_path, b.description
                )
                if age is not None:
                    b.age_commits = age
                    b.stale = is_stale

        # Inspect diff evidence for test parity risks
        for ev in evidence:
            if ev.type == EvidenceType.GIT_DIFF and ev.metadata.get("test_parity_risk"):
                risks.append(
                    Risk(
                        level="MEDIUM",
                        description=(
                            "Test Parity Gap: Core source files modified without "
                            "corresponding test modifications."
                        ),
                        mitigation=(
                            "Add matching unit or integration tests before completing handoff."
                        ),
                    )
                )

        meeting_rec = self.meeting_engine.evaluate(
            evidence=evidence,
            decisions=decisions,
            blockers=blockers,
            dependencies=dependencies,
            risks=risks,
            test_status=test_status,
            known_failures=known_failures,
            has_git_repo=is_git_repo,
            has_continuity_docs=has_continuity_docs,
        )

        # 7. Partition observed facts vs inferred state vs missing information
        observed_facts: List[str] = []
        inferred_state: List[str] = []
        missing_information: List[str] = []

        # Observed facts
        for ev in evidence:
            observed_facts.append(f"[{ev.source}] {ev.description}")

        # Inferred state
        inferred_state.append(
            f"Work status evaluated as '{status.value}' with {confidence.value} confidence."
        )
        inferred_state.append(
            f"Synchronous meeting recommendation: {meeting_rec.recommendation.value} "
            f"({meeting_rec.reason})"
        )

        # Missing information
        if not is_git_repo:
            missing_information.append(
                "Repository is not a Git work tree; commit history and file diffs unavailable."
            )
        if "Unknown objective" in objective:
            missing_information.append(
                "No explicit work objective documented in continuity files."
            )
        if not decisions:
            missing_information.append("No architectural decisions recorded in DECISIONS.md.")
        if test_status in ("UNKNOWN", "NOT_RUN"):
            missing_information.append(
                "No live test verification run performed in this inspection session."
            )
        if not next_actions:
            missing_information.append("No explicit next actions recorded in continuity docs.")

        # 8. Build WorkState
        work_state = WorkState(
            repo_name=repo_name,
            repo_root=str(repo_path),
            work_item=WorkItem(objective=objective),
            status=status,
            confidence=confidence,
            completed=completed,
            active_work=active_work,
            blockers=blockers,
            decisions=decisions,
            dependencies=dependencies,
            risks=risks,
            next_actions=next_actions,
            evidence=evidence,
            meeting=meeting_rec,
            missing_information=missing_information,
        )

        # 9. Build and return HandoffEnvelope
        return HandoffEnvelope(
            work_state=work_state,
            files_involved=files_involved,
            tests_run=tests_run,
            test_status=test_status,
            known_failures=known_failures,
            continuation_instructions=continuation_instructions,
            exact_starting_commands=starting_commands,
            generator_version=__version__,
            observed_facts=observed_facts,
            inferred_state=inferred_state,
        )
