"""Anti-surveillance policy and signal validation.

Foundational Principle: Measure the work system, not the worker.
Never infer productivity or work quality from presence, typing, screen activity,
or other employee surveillance signals.
"""

from typing import Any, Dict, List, Set


class SurveillanceSignalError(ValueError):
    """Raised when an attempt is made to ingest or process prohibited surveillance signals."""
    pass


# Normalized identifiers for signals that must never be ingested or evaluated.
PROHIBITED_SIGNALS: Set[str] = {
    # Keystroke and input dynamics
    "keystroke",
    "keystrokes",
    "keystroke_dynamics",
    "typing_speed",
    "typing_frequency",
    "wpm",
    "keylogger",

    # Mouse and cursor movement
    "mouse",
    "mouse_movement",
    "mouse_clicks",
    "cursor_tracking",
    "scroll_depth",

    # Screen and physical sensors
    "webcam",
    "camera",
    "microphone",
    "screenshot",
    "screenshots",
    "screen_recording",
    "screen_capture",
    "active_window",
    "window_focus",
    "application_usage_time",

    # Presence and idle time
    "presence",
    "online_status",
    "idle_time",
    "idle_duration",
    "away_status",
    "slack_presence",
    "teams_presence",
    "discord_presence",

    # Physical tracking
    "badge_swipe",
    "badge_swipes",
    "office_attendance",
    "seat_sensor",
    "rfid_location",

    # Raw duration theater
    "hours_online",
    "hours_logged",
    "active_hours",
}


def is_prohibited_signal(signal_name: str) -> bool:
    """Check whether a signal name matches prohibited surveillance metrics."""
    cleaned = signal_name.strip().lower().replace("-", "_").replace(" ", "_")
    if cleaned in PROHIBITED_SIGNALS:
        return True
    # Substring checks for compound terms
    keywords = ("metric", "score", "rate", "track")
    for prohibited in PROHIBITED_SIGNALS:
        if prohibited in cleaned and any(kw in cleaned for kw in keywords):
            return True
    return False


def validate_signal_safety(signal_name: str) -> None:
    """Validate that a signal is safe and does not violate anti-surveillance policy.

    Raises:
        SurveillanceSignalError: If the signal name is prohibited.
    """
    if is_prohibited_signal(signal_name):
        raise SurveillanceSignalError(
            f"Prohibited surveillance signal rejected: '{signal_name}'. "
            "HowlRelay measures the work system, not the worker."
        )


def sanitize_dict_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize a dictionary by removing prohibited surveillance fields.

    Nested dictionaries and lists are sanitized recursively.
    """
    sanitized: Dict[str, Any] = {}
    for key, val in data.items():
        if is_prohibited_signal(key):
            continue
        if isinstance(val, dict):
            sanitized[key] = sanitize_dict_payload(val)
        elif isinstance(val, list):
            sanitized[key] = [
                sanitize_dict_payload(item) if isinstance(item, dict) else item
                for item in val
            ]
        else:
            sanitized[key] = val
    return sanitized


def check_prohibited_keys(data: Dict[str, Any], path: str = "") -> List[str]:
    """Find all prohibited keys in a dictionary structure."""
    violations: List[str] = []
    for key, val in data.items():
        current_path = f"{path}.{key}" if path else key
        if is_prohibited_signal(key):
            violations.append(current_path)
        if isinstance(val, dict):
            violations.extend(check_prohibited_keys(val, current_path))
        elif isinstance(val, list):
            for idx, item in enumerate(val):
                if isinstance(item, dict):
                    violations.extend(check_prohibited_keys(item, f"{current_path}[{idx}]"))
    return violations
