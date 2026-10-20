"""HowlFrame capability and policy integration adapter.

Provides a clean adapter boundary with the HowlFrame capability-bounded runtime.
Gracefully degrades when HowlFrame is not available.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from howlrelay.adapters.base import BaseEvidenceCollector
from howlrelay.model import Evidence, EvidenceType


class HowlFrameCollector(BaseEvidenceCollector):
    """Inspects HowlFrame toolchain availability and policy artifacts."""

    def collector_name(self) -> str:
        return "howlframe"

    def _find_binary(self) -> Optional[str]:
        """Find howlframe binary on PATH or standard Howl local locations."""
        bin_path = shutil.which("howlframe")
        if bin_path:
            return bin_path

        home_local = Path.home() / ".local" / "bin" / "howlframe"
        if home_local.is_file():
            return str(home_local)

        return None

    def _discover_policies(self, repo_path: Path) -> List[Path]:
        """Discover .howl or .hfbc policy files in repo."""
        policies: List[Path] = []
        for ext in ("*.howl", "*.hfbc"):
            policies.extend(repo_path.glob(ext))
            policies.extend(repo_path.glob(f"**/{ext}"))
        ignore_dirs = {"node_modules", "build", "dist", ".venv"}
        return [
            p for p in policies
            if not any(part.startswith(".") or part in ignore_dirs for part in p.parts)
        ]

    def collect(self, repo_path: Path) -> List[Evidence]:
        """Collect HowlFrame availability and policy evidence."""
        evidence_list: List[Evidence] = []
        binary_path = self._find_binary()
        policies = self._discover_policies(repo_path)

        if not binary_path:
            evidence_list.append(
                Evidence(
                    type=EvidenceType.HOWLFRAME_POLICY,
                    ref="runtime_status",
                    source="howlframe",
                    description=(
                        "HowlFrame runtime not detected on PATH or local locations "
                        "(graceful fallback active)."
                    ),
                    metadata={"available": False, "fallback_mode": True},
                )
            )
            return evidence_list

        # Binary is available
        version_info = "available"
        try:
            # `--version` is HowlFrame's documented probe (in its interop descriptor).
            res = subprocess.run(
                [binary_path, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            reports_version = res.stdout.startswith("HowlFrame ")
            version_info = "operational" if res.returncode == 0 and reports_version else "error"
        except Exception:
            version_info = "unreachable"

        evidence_list.append(
            Evidence(
                type=EvidenceType.HOWLFRAME_POLICY,
                ref="runtime_status",
                source="howlframe",
                description=(
                    f"HowlFrame runtime operational at '{binary_path}'. "
                    f"Policies found: {len(policies)}."
                ),
                metadata={
                    "available": True,
                    "binary_path": binary_path,
                    "status": version_info,
                    "policy_files": [str(p.relative_to(repo_path)) for p in policies],
                },
            )
        )

        return evidence_list
