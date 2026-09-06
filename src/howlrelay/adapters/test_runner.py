"""Test evidence collector for HowlRelay.

Discovers test suites, examines test cache status, and captures test execution evidence.
"""

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional

from howlrelay.adapters.base import BaseEvidenceCollector
from howlrelay.model import Evidence, EvidenceType


class TestCollector(BaseEvidenceCollector):
    """Gathers test discovery and execution evidence."""

    def collector_name(self) -> str:
        return "test_runner"

    def _discover_test_framework(self, repo_path: Path) -> Optional[str]:
        has_py_conf = (
            (repo_path / "pytest.ini").is_file() or
            (repo_path / "pyproject.toml").is_file()
        )
        if has_py_conf or (repo_path / "tests").is_dir():
            return "pytest"
        if (repo_path / "go.mod").is_file():
            return "go_test"
        if (repo_path / "package.json").is_file():
            return "npm_test"
        return None

    def _inspect_pytest_cache(self, repo_path: Path) -> Dict[str, Any]:
        """Inspect pytest cache if present."""
        cache_dir = repo_path / ".pytest_cache"
        if not cache_dir.is_dir():
            return {"cache_present": False}

        lastfailed_path = cache_dir / "v" / "cache" / "lastfailed"
        failed_tests = []
        if lastfailed_path.is_file():
            try:
                data = json.loads(lastfailed_path.read_text(encoding="utf-8"))
                failed_tests = list(data.keys())
            except Exception:
                pass

        return {
            "cache_present": True,
            "failed_count": len(failed_tests),
            "failed_tests": failed_tests,
        }

    def run_pytest_verification(self, repo_path: Path, timeout: int = 30) -> Dict[str, Any]:
        """Execute pytest in bounded mode to obtain live test evidence."""
        python_bin = repo_path / ".venv" / "bin" / "pytest"
        cmd = [str(python_bin) if python_bin.is_file() else "pytest", "-q"]

        try:
            res = subprocess.run(
                cmd,
                cwd=str(repo_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=timeout,
            )
            output = (res.stdout + "\n" + res.stderr).strip()
            digest = hashlib.sha256(output.encode("utf-8")).hexdigest()
            passed = res.returncode == 0
            return {
                "executed": True,
                "exit_code": res.returncode,
                "passed": passed,
                "status": "PASSED" if passed else "FAILED",
                "summary": output.splitlines()[-1] if output else "No output",
                "output_digest": digest,
            }
        except subprocess.TimeoutExpired:
            return {
                "executed": True,
                "exit_code": -1,
                "passed": False,
                "status": "TIMED_OUT",
                "summary": f"Pytest timed out after {timeout}s",
                "output_digest": "timeout",
            }
        except Exception as ex:
            return {
                "executed": False,
                "exit_code": -1,
                "passed": False,
                "status": "ERROR",
                "summary": str(ex),
                "output_digest": "error",
            }

    def collect(self, repo_path: Path) -> List[Evidence]:
        """Collect test evidence without mandatory test execution."""
        evidence_list: List[Evidence] = []
        framework = self._discover_test_framework(repo_path)
        tests_dir = repo_path / "tests"

        if not framework and not tests_dir.is_dir():
            evidence_list.append(
                Evidence(
                    type=EvidenceType.TEST_RUN,
                    ref="no_tests_detected",
                    source="test_runner",
                    description="No recognized test directory or framework configuration found.",
                    metadata={"framework": None, "tests_dir_present": False},
                )
            )
            return evidence_list

        test_files = []
        if tests_dir.is_dir():
            patterns = ("test_*.py", "*_test.py", "*_test.go")
            for pat in patterns:
                test_files.extend([str(p.relative_to(repo_path)) for p in tests_dir.glob(pat)])

        cache_info = self._inspect_pytest_cache(repo_path) if framework == "pytest" else {}

        evidence_list.append(
            Evidence(
                type=EvidenceType.TEST_RUN,
                ref=f"{framework or 'custom'}:discovery",
                source="test_runner",
                description=(
                    f"Test framework '{framework}': {len(test_files)} test files found. "
                    f"Last failed count from cache: {cache_info.get('failed_count', 'n/a')}."
                ),
                metadata={
                    "framework": framework,
                    "test_file_count": len(test_files),
                    "test_files": test_files,
                    "cache": cache_info,
                },
            )
        )

        return evidence_list
