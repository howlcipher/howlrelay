"""Tests for anti-surveillance policy and prohibited signals."""

import pytest

from howlrelay.model import Evidence, EvidenceType
from howlrelay.policy import (
    SurveillanceSignalError,
    is_prohibited_signal,
    sanitize_dict_payload,
    validate_signal_safety,
)


def test_prohibited_signal_detection():
    assert is_prohibited_signal("keystroke")
    assert is_prohibited_signal("keystrokes")
    assert is_prohibited_signal("mouse_movement")
    assert is_prohibited_signal("webcam")
    assert is_prohibited_signal("screenshot")
    assert is_prohibited_signal("slack_presence")
    assert is_prohibited_signal("idle_time")
    assert is_prohibited_signal("hours_online")
    assert is_prohibited_signal("badge_swipes")

    # Safe engineering signals
    assert not is_prohibited_signal("commit_sha")
    assert not is_prohibited_signal("test_status")
    assert not is_prohibited_signal("diff_stat")
    assert not is_prohibited_signal("code_review")


def test_validate_signal_safety_raises():
    with pytest.raises(SurveillanceSignalError) as exc_info:
        validate_signal_safety("keystrokes")
    assert "Prohibited surveillance signal" in str(exc_info.value)

    # Does not raise for valid signals
    validate_signal_safety("git_commit")


def test_sanitize_dict_payload():
    payload = {
        "repo": "howlrelay",
        "keystroke_rate": 120,
        "slack_presence": "active",
        "commit_count": 5,
        "nested": {
            "mouse_clicks": 42,
            "branch": "main",
        },
    }
    sanitized = sanitize_dict_payload(payload)
    assert "repo" in sanitized
    assert "commit_count" in sanitized
    assert "keystroke_rate" not in sanitized
    assert "slack_presence" not in sanitized
    assert sanitized["nested"] == {"branch": "main"}


def test_evidence_model_rejects_surveillance_metadata():
    with pytest.raises(Exception) as exc_info:
        Evidence(
            type=EvidenceType.CUSTOM,
            ref="test_run",
            source="agent",
            description="Agent run",
            metadata={"idle_time": 300},
        )
    assert "Prohibited surveillance signals found" in str(exc_info.value)

    # Valid metadata passes
    ev = Evidence(
        type=EvidenceType.GIT_COMMIT,
        ref="abc1234",
        source="git",
        description="Commit abc1234",
        metadata={"branch": "main", "changed_files": 3},
    )
    assert ev.metadata["branch"] == "main"
