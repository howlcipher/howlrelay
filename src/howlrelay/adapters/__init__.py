"""Evidence collectors and external system adapters for HowlRelay."""

from howlrelay.adapters.base import BaseEvidenceCollector
from howlrelay.adapters.git import GitCollector
from howlrelay.adapters.continuity import ContinuityCollector
from howlrelay.adapters.test_runner import TestCollector
from howlrelay.adapters.howlframe import HowlFrameCollector

__all__ = [
    "BaseEvidenceCollector",
    "GitCollector",
    "ContinuityCollector",
    "TestCollector",
    "HowlFrameCollector",
]
