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

    def _read_file_safe(self, path: Optional[Path]) -> Optional[str]:
        if path and path.is_file():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def _find_file_or_dir(self, repo_path: Path, filename: str) -> Optional[Path]:
        """Find a canonical file or directory checking root, docs/, and .github/."""
        direct = repo_path / filename
        if direct.is_file() or direct.is_dir():
            return direct

        stem = filename.replace(".md", "")
        candidates = [
            repo_path / "docs" / filename,
            repo_path / ".github" / filename,
            repo_path / "docs" / stem.lower(),
            repo_path / "docs" / filename.lower(),
        ]
        if stem.upper() == "DECISIONS":
            candidates.extend([repo_path / "docs" / "adr", repo_path / ".adr"])

        for c in candidates:
            if c.is_file():
                return c
            if c.is_dir() and any(c.glob("*.md")):
                return c

        return None

    def _extract_markdown_section(self, text: str, header: str) -> Optional[str]:
        """Extract content under a heading, handling numbered prefixes and code fences."""
        header_re = re.compile(
            rf"^#+\s+(?:\d+[\.\)]\s+|[A-Za-z][\.\)]\s+)?{re.escape(header)}[^\n]*$",
            re.IGNORECASE,
        )
        lines = text.splitlines()
        capturing = False
        captured_lines: List[str] = []
        in_code_fence = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_fence = not in_code_fence

            if not in_code_fence and re.match(r"^#+\s+", line):
                if capturing:
                    break
                if header_re.match(line):
                    capturing = True
                    continue

            if capturing:
                captured_lines.append(line)

        if capturing:
            return "\n".join(captured_lines).strip()
        return None

    def _extract_section_by_synonyms(self, text: str, headers: List[str]) -> Optional[str]:
        """Try extracting markdown section across synonym headers in priority order."""
        for h in headers:
            sec = self._extract_markdown_section(text, h)
            if sec:
                return sec
        return None

    def _parse_list_items(self, text: Optional[str]) -> List[str]:
        """Parse bullet, numbered, or checkbox list items from text."""
        if not text:
            return []
        items: List[str] = []
        for line in text.splitlines():
            line = line.strip()
            m = re.match(r"^(?:[-*]|\d+[\.\)])\s+(?:\[[ xX]\]\s+)?(.+)$", line)
            if m:
                item_val = m.group(1).strip()
                if item_val:
                    items.append(item_val)
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
            rat_text = (
                rationale_match.group(1).strip() if rationale_match else "Recorded in ADR"
            )
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
        found_files: List[str] = []
        missing_files: List[str] = []

        for filename in self.CANONICAL_FILES:
            target_path = self._find_file_or_dir(repo_path, filename)
            if target_path is not None:
                found_files.append(filename)
                rel_path = str(target_path.relative_to(repo_path))
                if target_path.is_file():
                    content = self._read_file_safe(target_path) or ""
                    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                    evidence_list.append(
                        Evidence(
                            type=EvidenceType.CONTINUITY_DOC,
                            ref=rel_path,
                            source="continuity_docs",
                            description=(
                                f"Continuity document '{filename}' present at '{rel_path}' "
                                f"({len(content.splitlines())} lines)."
                            ),
                            fingerprint=digest,
                            metadata={
                                "filename": filename,
                                "path": rel_path,
                                "line_count": len(content.splitlines()),
                                "sha256": digest,
                            },
                        )
                    )
                else:
                    # Directory of entries (e.g. docs/journal/ or docs/adr/)
                    sub_files = sorted(target_path.glob("*.md"))
                    joined = "\n".join(
                        self._read_file_safe(sf) or "" for sf in sub_files
                    )
                    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
                    evidence_list.append(
                        Evidence(
                            type=EvidenceType.CONTINUITY_DOC,
                            ref=rel_path,
                            source="continuity_docs",
                            description=(
                                f"Continuity directory '{filename}' present at '{rel_path}' "
                                f"({len(sub_files)} markdown records)."
                            ),
                            fingerprint=digest,
                            metadata={
                                "filename": filename,
                                "path": rel_path,
                                "file_count": len(sub_files),
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

        # Dogfood artifacts inspection
        dogfood_dir = repo_path / "dogfood"
        if dogfood_dir.is_dir():
            artifacts = sorted([p.name for p in dogfood_dir.glob("*.*")])
            if artifacts:
                evidence_list.append(
                    Evidence(
                        type=EvidenceType.CUSTOM,
                        ref="creative_dogfood_artifacts",
                        source="dogfood_artifacts",
                        description=(
                            f"Discovered {len(artifacts)} dogfood artifacts under dogfood/ "
                            f"({', '.join(artifacts[:4])})."
                        ),
                        metadata={"artifacts": artifacts, "count": len(artifacts)},
                    )
                )

        return evidence_list

    def extract_structured_context(self, repo_path: Path) -> Dict[str, Any]:
        """Extract parsed workstream elements (objective, blockers, decisions, next actions)."""
        handoff_path = self._find_file_or_dir(repo_path, "HANDOFF.md")
        handoff_content = (
            self._read_file_safe(handoff_path)
            if handoff_path and handoff_path.is_file()
            else None
        )

        state_path = self._find_file_or_dir(repo_path, "PROJECT_STATE.md")
        project_state_content = (
            self._read_file_safe(state_path)
            if state_path and state_path.is_file()
            else None
        )

        dec_path = self._find_file_or_dir(repo_path, "DECISIONS.md")
        if dec_path and dec_path.is_file():
            decisions_content = self._read_file_safe(dec_path)
        elif dec_path and dec_path.is_dir():
            decisions_content = "\n\n".join(
                self._read_file_safe(f) or "" for f in sorted(dec_path.glob("*.md"))
            )
        else:
            decisions_content = None

        objective = "Unknown objective (not explicitly defined in continuity docs)"
        current_state_text = "Unknown state"
        completed_items: List[str] = []
        active_work: List[str] = []
        blockers: List[Blocker] = []
        next_actions: List[NextAction] = []
        known_failures: List[str] = []
        starting_commands: List[str] = []
        key_files: List[str] = []
        continuation_instructions: List[str] = []

        obj_synonyms = [
            "Objective",
            "System Summary",
            "Overview",
            "Summary",
            "Mission",
            "Goal",
            "Purpose",
        ]
        status_synonyms = ["Current State", "Current Status", "Status", "State"]
        completed_synonyms = [
            "Last Completed Work",
            "What Is Complete",
            "What Works Right Now",
            "Completed Work",
            "Completed",
            "Implemented Features",
            "Implemented",
        ]
        active_synonyms = [
            "What Remains Incomplete / Active",
            "What Remains Incomplete",
            "What Is in Progress / Known Limitations",
            "What Is in Progress",
            "Incomplete / In-Progress Features",
            "Incomplete / Next Priorities",
            "Active Work",
            "In Progress",
            "Known Limitations",
            "Current Priorities",
            "Immediate Priorities",
        ]
        blocker_synonyms = [
            "Blockers",
            "Active Blockers",
            "Blockers & Dependencies",
            "Blockers & Risks",
        ]
        failure_synonyms = ["Known Failures", "Failures", "Known Defects"]
        next_synonyms = [
            "Next Recommended Action",
            "Next Recommended Actions",
            "Next Actions",
            "Next Priorities",
            "Immediate Priorities",
            "Immediate Next Actions",
        ]
        cmd_synonyms = [
            "Exact Starting Commands",
            "Commands to Resume Work",
            "Commands to Resume",
            "Starting Commands",
            "Quickstart",
            "Important Commands",
        ]
        files_synonyms = [
            "Files & Components Involved",
            "Files / Components Involved",
            "Key Files & Architecture",
            "Key Files",
        ]
        ctx_synonyms = [
            "Context the Next Agent Must Not Lose",
            "Continuation Context & Instructions",
            "Continuation Instructions",
        ]

        if handoff_content:
            obj_sec = self._extract_section_by_synonyms(handoff_content, obj_synonyms)
            if obj_sec:
                objective = obj_sec.split("\n\n")[0].strip()

            state_sec = self._extract_section_by_synonyms(handoff_content, status_synonyms)
            if state_sec:
                current_state_text = state_sec.strip()
            else:
                m = re.search(
                    r"\*\*(?:Current Status|Status)\*\*:\s*([^\n]+)",
                    handoff_content,
                    re.IGNORECASE,
                )
                if m:
                    current_state_text = m.group(1).strip()

            last_work_sec = self._extract_section_by_synonyms(handoff_content, completed_synonyms)
            if last_work_sec:
                completed_items.extend(self._parse_list_items(last_work_sec))

            active_sec = self._extract_section_by_synonyms(handoff_content, active_synonyms)
            if active_sec:
                active_work.extend(self._parse_list_items(active_sec))

            blocker_sec = self._extract_section_by_synonyms(handoff_content, blocker_synonyms)
            if blocker_sec and blocker_sec.strip().lower() not in ("none", "none.", "n/a"):
                for item in self._parse_list_items(blocker_sec):
                    blockers.append(Blocker(description=item, reason="Documented in continuity"))

            failures_sec = self._extract_section_by_synonyms(handoff_content, failure_synonyms)
            if failures_sec and failures_sec.strip().lower() not in ("none", "none.", "n/a"):
                known_failures.extend(self._parse_list_items(failures_sec))

            next_sec = self._extract_section_by_synonyms(handoff_content, next_synonyms)
            if next_sec:
                items = self._parse_list_items(next_sec)
                if items:
                    for item in items:
                        next_actions.append(NextAction(action=item, priority="NEXT"))
                else:
                    next_actions.append(NextAction(action=next_sec.strip(), priority="NEXT"))

            cmds_sec = self._extract_section_by_synonyms(handoff_content, cmd_synonyms)
            if cmds_sec:
                code_match = re.search(r"```(?:bash|sh)?\n(.*?)\n```", cmds_sec, re.DOTALL)
                raw_lines = (
                    code_match.group(1).splitlines() if code_match else cmds_sec.splitlines()
                )
                for line in raw_lines:
                    clean_line = line.strip()
                    if clean_line and not clean_line.startswith("#"):
                        starting_commands.append(clean_line)

            files_sec = self._extract_section_by_synonyms(handoff_content, files_synonyms)
            if files_sec:
                for item in self._parse_list_items(files_sec):
                    m = re.search(r"`?([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9_\-]+)`?", item)
                    if m:
                        key_files.append(m.group(1))
                    elif "/" in item or "." in item:
                        candidate = item.split()[0].strip("`:")
                        if "/" in candidate or "." in candidate:
                            key_files.append(candidate)

            ctx_sec = self._extract_section_by_synonyms(handoff_content, ctx_synonyms)
            if ctx_sec:
                continuation_instructions.extend(self._parse_list_items(ctx_sec))

        if project_state_content:
            if objective.startswith("Unknown objective"):
                obj_sec = self._extract_section_by_synonyms(project_state_content, obj_synonyms)
                if obj_sec:
                    objective = obj_sec.split("\n\n")[0].strip()

            implemented_sec = self._extract_section_by_synonyms(
                project_state_content, completed_synonyms
            )
            if implemented_sec:
                for item in self._parse_list_items(implemented_sec):
                    if item not in completed_items:
                        completed_items.append(item)

            incomplete_sec = self._extract_section_by_synonyms(
                project_state_content, active_synonyms
            )
            if incomplete_sec:
                for item in self._parse_list_items(incomplete_sec):
                    if item not in active_work:
                        active_work.append(item)

        # Objective fallback: README.md
        if objective.startswith("Unknown objective"):
            readme_text = self._read_file_safe(repo_path / "README.md")
            if readme_text:
                match = re.search(r"^#\s+[^\n]+\n+(.*?)(?=\n#|\Z)", readme_text, re.DOTALL)
                if match:
                    first_p = match.group(1).strip().split("\n\n")[0].strip()
                    if first_p and not first_p.startswith("<!--"):
                        objective = first_p

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
            "key_files": list(dict.fromkeys(key_files)),
            "continuation_instructions": continuation_instructions,
        }
