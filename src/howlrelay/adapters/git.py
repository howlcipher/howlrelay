"""Git evidence collector for HowlRelay.

Inspects local Git repository state: branches, commit history, working tree status,
staged/unstaged diffs, remotes, and modified files.
"""

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from howlrelay.adapters.base import BaseEvidenceCollector
from howlrelay.model import Evidence, EvidenceType


class GitCollector(BaseEvidenceCollector):
    """Gathers factual evidence directly from the local Git repository."""

    def collector_name(self) -> str:
        return "git"

    def _run_git(self, repo_path: Path, args: List[str]) -> Optional[str]:
        """Execute a git command safely within repo_path."""
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path)] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.rstrip("\r\n")
            return None
        except Exception:
            return None

    def is_git_repo(self, repo_path: Path) -> bool:
        """Check whether repo_path is inside a git work tree."""
        out = self._run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
        return (out or "").strip() == "true"

    def collect(self, repo_path: Path) -> List[Evidence]:
        """Collect git evidence items from repo_path."""
        evidence_list: List[Evidence] = []

        if not self.is_git_repo(repo_path):
            evidence_list.append(
                Evidence(
                    type=EvidenceType.CUSTOM,
                    ref="not_a_git_repo",
                    source="git",
                    description=f"Directory '{repo_path}' is not a valid Git repository.",
                    metadata={"is_git_repo": False},
                )
            )
            return evidence_list

        # 1. Current branch
        branch = self._run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
        if branch:
            evidence_list.append(
                Evidence(
                    type=EvidenceType.GIT_BRANCH,
                    ref=branch,
                    source="git",
                    description=f"Active branch: {branch}",
                    metadata={"branch": branch},
                )
            )

        # 2. HEAD commit
        head_sha = self._run_git(repo_path, ["rev-parse", "HEAD"])
        if head_sha:
            commit_subject = self._run_git(repo_path, ["log", "-1", "--format=%s"]) or ""
            author = self._run_git(repo_path, ["log", "-1", "--format=%an"]) or ""
            author_date = self._run_git(repo_path, ["log", "-1", "--format=%aI"]) or ""
            head_files_raw = self._run_git(
                repo_path, ["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]
            )
            head_modified_files = (
                [f.strip() for f in head_files_raw.splitlines() if f.strip()]
                if head_files_raw
                else []
            )
            evidence_list.append(
                Evidence(
                    type=EvidenceType.GIT_COMMIT,
                    ref=head_sha,
                    source="git",
                    description=f"HEAD commit {head_sha[:8]}: {commit_subject}",
                    fingerprint=head_sha,
                    metadata={
                        "sha": head_sha,
                        "subject": commit_subject,
                        "author": author,
                        "date": author_date,
                        "head_modified_files": head_modified_files,
                    },
                )
            )
        else:
            evidence_list.append(
                Evidence(
                    type=EvidenceType.GIT_COMMIT,
                    ref="NONE",
                    source="git",
                    description="Repository has no commits yet (initial state).",
                    metadata={"has_commits": False},
                )
            )

        # 3. Working tree status (porcelain)
        status_raw = self._run_git(repo_path, ["status", "--porcelain"])
        if status_raw is not None:
            lines = [line for line in status_raw.splitlines() if line]
            modified_files: List[str] = []
            untracked_files: List[str] = []
            staged_files: List[str] = []

            for line in lines:
                if len(line) < 3:
                    continue
                status_code = line[:2]
                filename = line[3:].strip()
                if " -> " in filename:
                    filename = filename.split(" -> ")[-1].strip()
                if status_code.startswith("?") or status_code.endswith("?"):
                    untracked_files.append(filename)
                else:
                    if status_code[0] in ("M", "A", "D", "R", "C"):
                        staged_files.append(filename)
                    if status_code[1] in ("M", "D"):
                        modified_files.append(filename)

            all_dirty = list(dict.fromkeys(staged_files + modified_files + untracked_files))
            status_digest = hashlib.sha256(status_raw.encode("utf-8")).hexdigest()

            evidence_list.append(
                Evidence(
                    type=EvidenceType.GIT_STATUS,
                    ref="working_tree",
                    source="git",
                    description=(
                        f"Working tree: {len(all_dirty)} uncommitted files "
                        f"({len(staged_files)} staged, {len(modified_files)} unstaged, "
                        f"{len(untracked_files)} untracked)."
                    ),
                    fingerprint=status_digest,
                    metadata={
                        "is_clean": len(all_dirty) == 0,
                        "staged_count": len(staged_files),
                        "modified_count": len(modified_files),
                        "untracked_count": len(untracked_files),
                        "staged_files": staged_files,
                        "modified_files": modified_files,
                        "untracked_files": untracked_files,
                        "all_uncommitted_files": all_dirty,
                    },
                )
            )

        # 4. Working tree diff stat & deep architectural analysis
        diff_stat = self._run_git(repo_path, ["diff", "--stat"])
        cached_stat = self._run_git(repo_path, ["diff", "--cached", "--stat"])
        diff_parts = [part for part in (diff_stat, cached_stat) if part]
        total_diff = "\n".join(diff_parts)
        if total_diff.strip():
            deep_diff = self.analyze_diff(repo_path)
            diff_digest = hashlib.sha256(total_diff.encode("utf-8")).hexdigest()
            evidence_list.append(
                Evidence(
                    type=EvidenceType.GIT_DIFF,
                    ref="diff_stat",
                    source="git",
                    description=f"Active diff summary:\n{total_diff.strip()}",
                    fingerprint=diff_digest,
                    metadata={
                        "has_uncommitted_diffs": True,
                        "layers": deep_diff["layers"],
                        "modified_symbols": deep_diff["modified_symbols"],
                        "test_parity_risk": deep_diff["test_parity_risk"],
                        "core_files_count": deep_diff["core_files_count"],
                        "test_files_count": deep_diff["test_files_count"],
                    },
                )
            )

        # 5. Recent commit log (up to 10 commits)
        log_raw = self._run_git(
            repo_path,
            ["log", "-n", "10", "--format=%H%x09%an%x09%aI%x09%s"],
        )
        if log_raw:
            recent_commits = []
            for line in log_raw.splitlines():
                parts = line.split("\t")
                if len(parts) >= 4:
                    recent_commits.append({
                        "sha": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "subject": parts[3],
                    })
            evidence_list.append(
                Evidence(
                    type=EvidenceType.CUSTOM,
                    ref="recent_commit_log",
                    source="git",
                    description=f"Recent commit log ({len(recent_commits)} commits)",
                    metadata={"commits": recent_commits},
                )
            )

        # 6. Remote origin info
        origin_url = self._run_git(repo_path, ["remote", "get-url", "origin"])
        if origin_url:
            evidence_list.append(
                Evidence(
                    type=EvidenceType.CUSTOM,
                    ref="remote_origin",
                    source="git",
                    description=f"Git remote origin: {origin_url}",
                    metadata={"origin_url": origin_url},
                )
            )

        return evidence_list

    def analyze_diff(self, repo_path: Path) -> Dict[str, Any]:
        """Perform deep architectural diff analysis and test parity evaluation."""
        raw_diff = self._run_git(repo_path, ["diff", "-U0"]) or ""
        raw_cached = self._run_git(repo_path, ["diff", "--cached", "-U0"]) or ""
        combined_diff = f"{raw_diff}\n{raw_cached}".strip()

        layers: Dict[str, List[str]] = {
            "core": [],
            "tests": [],
            "docs": [],
            "config": [],
            "other": [],
        }

        modified_symbols: List[str] = []

        for line in combined_diff.splitlines():
            if line.startswith("diff --git "):
                parts = line.split()
                if len(parts) >= 4:
                    b_path = parts[3]
                    current_file = b_path[2:] if b_path.startswith("b/") else b_path

                    if current_file.startswith("src/") or "/src/" in current_file:
                        layers["core"].append(current_file)
                    elif (
                        current_file.startswith("tests/")
                        or "/tests/" in current_file
                        or "test_" in current_file
                    ):
                        layers["tests"].append(current_file)
                    elif current_file.startswith("docs/") or current_file.endswith(".md"):
                        layers["docs"].append(current_file)
                    elif (
                        current_file in ("pyproject.toml", "setup.py", "Cargo.toml", "package.json")
                        or current_file.startswith(".github/")
                    ):
                        layers["config"].append(current_file)
                    else:
                        layers["other"].append(current_file)

            elif line.startswith("@@ ") and "@@" in line[3:]:
                after_second_at = line.split("@@", 2)[-1].strip()
                if after_second_at:
                    symbol = after_second_at
                    if (
                        symbol.startswith("def ")
                        or symbol.startswith("class ")
                        or symbol.startswith("async def ")
                    ):
                        sym_name = symbol.split("(")[0].split(":")[0].strip()
                        modified_symbols.append(sym_name)
                    else:
                        modified_symbols.append(symbol[:40])

        for k in layers:
            layers[k] = list(dict.fromkeys(layers[k]))
        modified_symbols = list(dict.fromkeys(modified_symbols))

        has_core_changes = len(layers["core"]) > 0
        has_test_changes = len(layers["tests"]) > 0
        test_parity_risk = has_core_changes and not has_test_changes

        return {
            "has_uncommitted_diffs": bool(combined_diff),
            "layers": layers,
            "modified_symbols": modified_symbols,
            "test_parity_risk": test_parity_risk,
            "core_files_count": len(layers["core"]),
            "test_files_count": len(layers["tests"]),
        }

    def compute_blocker_staleness(
        self, repo_path: Path, blocker_text: str
    ) -> Tuple[Optional[int], bool]:
        """Compute commit age for an active blocker in the work system."""
        if not blocker_text or not self.is_git_repo(repo_path):
            return None, False

        words = [w for w in blocker_text.split() if len(w) > 3 and w.isalnum()]
        if not words:
            return None, False
        query = " ".join(words[:2])

        log_sha = self._run_git(repo_path, ["log", "-1", "--format=%H", "-S", query])
        if not log_sha or not log_sha.strip():
            return None, False

        commit_sha = log_sha.strip()
        count_raw = self._run_git(repo_path, ["rev-list", "--count", f"{commit_sha}..HEAD"])
        if count_raw and count_raw.strip().isdigit():
            age = int(count_raw.strip())
            return age, age >= 3

        return None, False
