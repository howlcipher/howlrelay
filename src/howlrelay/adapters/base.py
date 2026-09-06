"""Base adapter contract for evidence collection."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from howlrelay.model import Evidence


class BaseEvidenceCollector(ABC):
    """Abstract collector responsible for gathering grounded evidence from a repository."""

    @abstractmethod
    def collector_name(self) -> str:
        """Name of the collector."""
        pass

    @abstractmethod
    def collect(self, repo_path: Path) -> List[Evidence]:
        """Collect grounded evidence from the target repository path."""
        pass
