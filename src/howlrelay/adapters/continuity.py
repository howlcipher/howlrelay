"""Continuity documentation collector for HowlRelay.

Inspects canonical repository continuity files:
- AGENTS.md
- PROJECT_STATE.md
- ROADMAP.md
- HANDOFF.md
- DECISIONS.md
- JOURNAL.md
"""

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from howlrelay.adapters.base import BaseEvidenceCollector
from howlrelay.model import Blocker, Decision, Evidence, EvidenceType, NextAction


class ContinuityCollector(BaseEvidenceCollector):
    """Parses repository continuity documentation to ground handoff state."""

    CANONICAL_FILES = [
        "AGENTS.md",
        "PROJECT_STATE.md",
        "ROADMAP.md",
        "HANDOFF.md",
        "DECISIONS.md",
        "JOURNAL.md",
    ]

    def collector_name(self) -> str:
        return "continuity_docs"

    def _read_file_safe(self, path: Path) -> Optional[str]:
        if path.is_file():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def _extract_markdown_section(self, text: str, header: str) -> Optional[str]:
        """Extract the content under a specific markdown heading (## Header or # Header)."""
        pattern = rf"(?:^|\n)#+\s+{re.escape(header)}[^\n]*\n(.*?)(?=\n#+ |\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _parse_list_items(self, text: Optional[str]) -> List[str]:
        """Parse bullet or checkbox list items from text."""
        if not text:
            return []
        items: List[str] = []
        for line in text.splitlines():
            line = line.strip()
            m = re.match(r"^[-*]\s+(?:\[[ xX]\]\s+)?(.+)$", line)
            if m:
                items.append(m.group(1).strip())
        return items

    def _parse_adrs(self, text: Optional[str]) -> List[Decision]:
        """Parse lightweight ADR entries from DECISIONS.md."""
        if not text:
            return []
        decisions: List[Decision] = []
        adr_blocks = re.split(r"(?=\n##\s+ADR-\d+)", text)
        for block in adr_blocks:
            header_match = re.search(r"##\s+(ADR-\d+[:\s]+[^\n]+)", block)
            if not header_match:
                continue
            title = header_match.group(1).strip()

            date_match = re.search(r"-\s+\*\*Date:\*\*\s*([^\n]+)", block, re.IGNORECASE)
            status_match = re.search(r"-\s+\*\*Status:\*\*\s*([^\n]+)", block, re.IGNORECASE)
            dec_pattern = r"-\s+\*\*Decision:\*\*\s*([^\n]+(?:\n(?!\s*-\s+\*\*)[^\n]+)*)"
            decision_match = re.search(dec_pattern, block, re.IGNORECASE)
            rat_pattern = r"-\s+\*\*Rationale:\*\*\s*([^\n]+(?:\n(?!\s*-\s+\*\*)[^\n]+)*)"
            rationale_match = re.search(rat_pattern, block, re.IGNORECASE)

            dec_text = decision_match.group(1).strip() if decision_match else ""
            rat_text = rationale_match.group(1).strip() if rationale_match else "Recorded in ADR"
            decisions.append(
                Decision(
                    decision=f"{title}: {dec_text}" if dec_text else title,
                    rationale=rat_text,
                    status=status_match.group(1).strip() if status_match else "DECIDED",
                    decided_at=date_match.group(1).strip() if date_match else None,
                    evidence_refs=["DECISIONS.md"],
                )
            )
        return decisions

    def collect(self, repo_path: Path) -> List[Evidence]:
        """Collect continuity document evidence from repo_path."""
        evidence_list: List[Evidence] = []
        found_files = []
        missing_files = []

        for filename in self.CANONICAL_FILES:
            file_path = repo_path / filename
            content = self._read_file_safe(file_path)
            if content is not None:
                found_files.append(filename)
                digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                evidence_list.append(
                    Evidence(
                        type=EvidenceType.CONTINUITY_DOC,
                        ref=filename,
                        source="continuity_docs",
                        description=(
                            f"Continuity document '{filename}' present "
                            f"({len(content.splitlines())} lines)."
                        ),
                        fingerprint=digest,
                        metadata={
                            "filename": filename,
                            "line_count": len(content.splitlines()),
                            "sha256": digest,
                        },
                    )
                )
            else:
                missing_files.append(filename)

        evidence_list.append(
            Evidence(
                type=EvidenceType.CUSTOM,
                ref="continuity_files_audit",
                source="continuity_docs",
                description=(
                    f"Continuity files audit: {len(found_files)}/6 present. "
                    f"Found: {', '.join(found_files) if found_files else 'none'}; "
                    f"Missing: {', '.join(missing_files) if missing_files else 'none'}."
                ),
                metadata={
                    "found": found_files,
                    "missing": missing_files,
                    "is_complete": len(missing_files) == 0,
                },
            )
        )

        return evidence_list

    def extract_structured_context(self, repo_path: Path) -> Dict[str, Any]:
        """Extract parsed workstream elements (objective, blockers, decisions, next actions)."""
        handoff_content = self._read_file_safe(repo_path / "HANDOFF.md")
        project_state_content = self._read_file_safe(repo_path / "PROJECT_STATE.md")
        decisions_content = self._read_file_safe(repo_path / "DECISIONS.md")

        objective = "Unknown objective (not explicitly defined in continuity docs)"
        current_state_text = "Unknown state"
        completed_items: List[str] = []
        active_work: List[str] = []
        blockers: List[Blocker] = []
        next_actions: List[NextAction] = []
        known_failures: List[str] = []
        starting_commands: List[str] = []
        continuation_instructions: List[str] = []

        if handoff_content:
            obj_sec = self._extract_markdown_section(handoff_content, "Objective")
            if obj_sec:
                objective = obj_sec.strip()

            state_sec = self._extract_markdown_section(handoff_content, "Current State")
            if state_sec:
                current_state_text = state_sec.strip()

            last_work_sec = self._extract_markdown_section(handoff_content, "Last Completed Work")
            if last_work_sec:
                completed_items.extend(self._parse_list_items(last_work_sec))

            blocker_sec = self._extract_markdown_section(handoff_content, "Blockers")
            if blocker_sec and blocker_sec.strip().lower() not in ("none", "none."):
                for item in self._parse_list_items(blocker_sec):
                    blockers.append(Blocker(description=item, reason="Documented in HANDOFF.md"))

            failures_sec = self._extract_markdown_section(handoff_content, "Known Failures")
            if failures_sec and failures_sec.strip().lower() not in ("none", "none."):
                known_failures.extend(self._parse_list_items(failures_sec))

            next_sec = self._extract_markdown_section(handoff_content, "Next Recommended Action")
            if next_sec:
                items = self._parse_list_items(next_sec)
                if items:
                    for item in items:
                        next_actions.append(NextAction(action=item, priority="NEXT"))
                else:
                    next_actions.append(NextAction(action=next_sec.strip(), priority="NEXT"))

            cmds_sec = self._extract_markdown_section(handoff_content, "Exact Starting Commands")
            if cmds_sec:
                code_match = re.search(r"```(?:bash|sh)?\n(.*?)\n```", cmds_sec, re.DOTALL)
                if code_match:
                    raw_lines = code_match.group(1).splitlines()
                else:
                    raw_lines = cmds_sec.splitlines()
                for line in raw_lines:
                    if line.strip() and not line.strip().startswith("#"):
                        starting_commands.append(line.strip())

            ctx_sec = self._extract_markdown_section(
                handoff_content, "Context the Next Agent Must Not Lose"
            )
            if ctx_sec:
                continuation_instructions.extend(self._parse_list_items(ctx_sec))

        if project_state_content:
            implemented_sec = self._extract_markdown_section(
                project_state_content, "Implemented Features"
            )
            if implemented_sec:
                for item in self._parse_list_items(implemented_sec):
                    if item not in completed_items:
                        completed_items.append(item)

            incomplete_sec = self._extract_markdown_section(
                project_state_content, "Incomplete / In-Progress Features"
            )
            if incomplete_sec:
                active_work.extend(self._parse_list_items(incomplete_sec))

        decisions = self._parse_adrs(decisions_content)

        return {
            "objective": objective,
            "current_state_text": current_state_text,
            "completed": completed_items,
            "active_work": active_work,
            "blockers": blockers,
            "decisions": decisions,
            "next_actions": next_actions,
            "known_failures": known_failures,
            "starting_commands": starting_commands,
            "continuation_instructions": continuation_instructions,
        }
