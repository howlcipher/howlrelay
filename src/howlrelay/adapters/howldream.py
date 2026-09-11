"""HowlDream speculative exploration integration adapter for HowlRelay.

Collects bounded exploration artifacts, candidate evaluations, and unresolved
assumptions from HowlDream runs into the durable HandoffEnvelope as grounded
evidence. Strictly preserves the advisory-only, non-executable authority boundary.
"""

import json
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

from howlrelay.adapters.base import BaseEvidenceCollector
from howlrelay.model import Evidence, EvidenceType


class HowlDreamCollector(BaseEvidenceCollector):
    """Inspects HowlDream availability and surfaces exploration run evidence."""

    def collector_name(self) -> str:
        return "howldream"

    def _find_binary(self) -> Optional[str]:
        """Finds howldream executable on PATH, env, or standard dev locations."""
        env_bin = os.environ.get("HOWLDREAM_BIN")
        if env_bin:
            p = Path(env_bin).expanduser().resolve()
            if p.is_file() and os.access(p, os.X_OK):
                return str(p)

        bin_path = shutil.which("howldream")
        if bin_path:
            return bin_path

        home_local = Path.home() / ".local" / "bin" / "howldream"
        if home_local.is_file() and os.access(home_local, os.X_OK):
            return str(home_local)

        dev_venv_bin = Path("/run/media/system/tallgeese/dev/howldream/.venv/bin/howldream")
        if dev_venv_bin.is_file() and os.access(dev_venv_bin, os.X_OK):
            return str(dev_venv_bin)

        return None

    def _discover_exploration_envelopes(self, repo_path: Path) -> List[Path]:
        """Discovers exploration_envelope.json files in repo or .howldream directories."""
        envelopes: List[Path] = []
        ignore_dirs = {".git", "node_modules", "build", "dist", ".venv", "__pycache__"}

        # First check explicit .howldream location
        howldream_dir = repo_path / ".howldream"
        if howldream_dir.is_dir():
            for p in howldream_dir.glob("**/exploration_envelope.json"):
                if p.is_file() and not any(part in ignore_dirs for part in p.parts):
                    envelopes.append(p)

        # Also search top-level repo runs
        for p in repo_path.glob("hd-*/exploration_envelope.json"):
            if p.is_file() and not any(part in ignore_dirs for part in p.parts):
                envelopes.append(p)

        return sorted(set(envelopes))

    def collect(self, repo_path: Path) -> List[Evidence]:
        """Collects HowlDream exploration evidence and authority constraints."""
        evidence_list: List[Evidence] = []
        binary_path = self._find_binary()
        envelopes = self._discover_exploration_envelopes(repo_path)

        # Baseline runtime evidence
        runtime_available = binary_path is not None
        runtime_desc = (
            f"HowlDream runtime available at '{binary_path}'."
            if runtime_available
            else "HowlDream runtime not detected on PATH or local locations."
        )

        evidence_list.append(
            Evidence(
                type=EvidenceType.HOWLDREAM_EXPLORATION,
                ref="runtime_status",
                source="howldream",
                description=f"{runtime_desc} Envelopes discovered: {len(envelopes)}.",
                metadata={
                    "available": runtime_available,
                    "binary_path": binary_path,
                    "envelope_count": len(envelopes),
                    "authority": {"type": "ADVISORY", "executable": False},
                },
            )
        )

        # Envelope details
        for env_path in envelopes:
            try:
                data = json.loads(env_path.read_text(encoding="utf-8"))
                run_id = data.get("exploration_id") or env_path.parent.name
                objective = data.get("objective", "")
                candidates = data.get("candidates", [])
                unresolved = data.get("unresolved_assumptions", [])
                contradictions = data.get("contradictions", [])
                recommended = data.get("recommended_disposition", "DEFER")

                # Strictly audit authority: speculative artifacts are non-executable
                auth = data.get("authority", {})
                is_executable = auth.get("executable", False)
                auth_type = auth.get("type", "ADVISORY")
                if is_executable or auth_type != "ADVISORY":
                    # Mark authority escalation attempt in evidence
                    evidence_list.append(
                        Evidence(
                            type=EvidenceType.HOWLDREAM_EXPLORATION,
                            ref=f"run:{run_id}:authority_violation",
                            source="howldream",
                            description=(
                                f"SECURITY WARNING: Exploration run '{run_id}' claimed executable "
                                f"authority ({auth_type}). Demoted to ADVISORY."
                            ),
                            metadata={
                                "run_id": run_id,
                                "authority_violation": True,
                                "original_claimed_type": auth_type,
                                "authority": {"type": "ADVISORY", "executable": False},
                            },
                        )
                    )
                    continue

                evidence_list.append(
                    Evidence(
                        type=EvidenceType.HOWLDREAM_EXPLORATION,
                        ref=f"run:{run_id}",
                        source="howldream",
                        description=(
                            f"HowlDream exploration '{run_id}' for objective '{objective[:60]}': "
                            f"{len(candidates)} candidates generated, {len(unresolved)} unresolved "
                            f"assumptions, recommended disposition: {recommended}."
                        ),
                        metadata={
                            "run_id": run_id,
                            "objective": objective,
                            "candidate_count": len(candidates),
                            "unresolved_assumptions_count": len(unresolved),
                            "contradictions_count": len(contradictions),
                            "recommended_disposition": recommended,
                            "relative_path": str(env_path.relative_to(repo_path)),
                            "authority": {"type": "ADVISORY", "executable": False},
                        },
                    )
                )
            except Exception as exc:
                evidence_list.append(
                    Evidence(
                        type=EvidenceType.HOWLDREAM_EXPLORATION,
                        ref=f"run:{env_path.parent.name}:error",
                        source="howldream",
                        description=f"Error reading exploration envelope {env_path.name}: {exc}",
                        metadata={"error": str(exc)},
                    )
                )

        return evidence_list
