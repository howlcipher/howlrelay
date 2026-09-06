"""Evidence-based meeting recommendation reasoning engine.

Evaluates whether a synchronous meeting is genuinely required based on:
- Unresolved architectural or policy decisions.
- Critical blockers and stale dependencies.
- Verification and test status.
- Sufficiency and consistency of recorded evidence.

Never claims certainty based on an LLM opinion. Every recommendation includes
inspectable triggers and grounded rationale.
"""

from typing import List

from howlrelay.model import (
    Blocker,
    Decision,
    Dependency,
    Evidence,
    EvidenceType,
    MeetingRecommendation,
    MeetingRecommendationState,
    Risk,
)


class MeetingReasoningEngine:
    """Computes evidence-based recommendations for synchronous meetings."""

    def evaluate(
        self,
        evidence: List[Evidence],
        decisions: List[Decision],
        blockers: List[Blocker],
        dependencies: List[Dependency],
        risks: List[Risk],
        test_status: str,
        known_failures: List[str],
        has_git_repo: bool = True,
        has_continuity_docs: bool = True,
    ) -> MeetingRecommendation:
        """Evaluate workstream facts and return an inspectable MeetingRecommendation."""
        triggers: List[str] = []

        # 1. Check for insufficient evidence
        if not has_git_repo:
            return MeetingRecommendation(
                recommendation=MeetingRecommendationState.INSUFFICIENT_EVIDENCE,
                reason=(
                    "Target directory is not a Git repository; "
                    "unable to inspect commits or working tree."
                ),
                triggers=["not_a_git_repo"],
            )

        # Check if git has no commits and no continuity docs
        has_commits = any(
            e.type == EvidenceType.GIT_COMMIT and e.ref != "NONE"
            for e in evidence
        )
        if not has_commits and not has_continuity_docs:
            return MeetingRecommendation(
                recommendation=MeetingRecommendationState.INSUFFICIENT_EVIDENCE,
                reason=(
                    "Repository has no commit history and lacks continuity documents; "
                    "insufficient evidence to evaluate."
                ),
                triggers=["no_commits", "no_continuity_docs"],
            )

        # 2. Check for human authority gates and unresolved decisions
        unresolved_decisions = [
            d for d in decisions
            if d.status.upper() in ("UNRESOLVED", "PROPOSED")
        ]
        if unresolved_decisions:
            triggers.append(f"unresolved_decisions({len(unresolved_decisions)})")
            titles = ", ".join(d.decision.split(":")[0] for d in unresolved_decisions[:3])
            return MeetingRecommendation(
                recommendation=MeetingRecommendationState.REQUIRES_HUMAN_DECISION,
                reason=(
                    f"Workstream contains {len(unresolved_decisions)} unresolved architectural "
                    f"or policy decision(s) ({titles}) requiring explicit human authority."
                ),
                triggers=triggers,
            )

        # 3. Check for critical or high-severity blockers
        critical_blockers = [
            b for b in blockers
            if b.severity.upper() in ("CRITICAL", "HIGH")
        ]
        if critical_blockers:
            triggers.append(f"critical_blockers({len(critical_blockers)})")
            blocker_summaries = "; ".join(b.description for b in critical_blockers[:2])
            return MeetingRecommendation(
                recommendation=MeetingRecommendationState.RECOMMENDED,
                reason=(
                    f"Workstream has {len(critical_blockers)} high-priority blocker(s): "
                    f"'{blocker_summaries}'. Synchronous collaboration may expedite unblocking."
                ),
                triggers=triggers,
            )

        # 4. Check for blocked dependencies
        blocked_deps = [
            dep for dep in dependencies
            if dep.status.upper() == "BLOCKED"
        ]
        if blocked_deps:
            triggers.append(f"blocked_dependencies({len(blocked_deps)})")
            dep_items = ", ".join(dep.item for dep in blocked_deps[:2])
            return MeetingRecommendation(
                recommendation=MeetingRecommendationState.RECOMMENDED,
                reason=(
                    f"External dependencies are blocked ({dep_items}). "
                    "Cross-team synchronization recommended."
                ),
                triggers=triggers,
            )

        # 5. Check for critical risks without mitigation
        unmitigated_risks = [
            r for r in risks
            if r.level.upper() in ("CRITICAL", "HIGH") and not r.mitigation
        ]
        if unmitigated_risks:
            triggers.append(f"unmitigated_risks({len(unmitigated_risks)})")
            return MeetingRecommendation(
                recommendation=MeetingRecommendationState.RECOMMENDED,
                reason=(
                    f"Detected {len(unmitigated_risks)} unmitigated high-level risk(s). "
                    "A targeted alignment meeting is recommended to define mitigations."
                ),
                triggers=triggers,
            )

        # 6. Check for active test failures without assigned next actions
        if test_status == "FAILED" and known_failures:
            triggers.append(f"known_failures({len(known_failures)})")
            return MeetingRecommendation(
                recommendation=MeetingRecommendationState.RECOMMENDED,
                reason=(
                    f"Test verification is failing with {len(known_failures)} known failure(s). "
                    "Review or pair debugging recommended if async reproduction is unclear."
                ),
                triggers=triggers,
            )

        # 7. Default: Asynchronous progress is healthy
        triggers.append("all_decisions_resolved")
        triggers.append("no_active_blockers")
        return MeetingRecommendation(
            recommendation=MeetingRecommendationState.NOT_REQUIRED,
            reason=(
                "Current work has no unresolved decisions, critical blockers, or failing gates "
                "requiring synchronous discussion. Next actions can continue asynchronously."
            ),
            triggers=triggers,
        )
