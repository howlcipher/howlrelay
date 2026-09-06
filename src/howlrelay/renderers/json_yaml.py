"""JSON and YAML serializers for HowlRelay artifacts."""

import json
from typing import Any, Union
import yaml

from howlrelay.model import HandoffEnvelope, WorkState


def render_json(data: Union[HandoffEnvelope, WorkState, Any], indent: int = 2) -> str:
    """Serialize model to formatted JSON."""
    if hasattr(data, "model_dump"):
        dumped = data.model_dump(mode="json")
    elif hasattr(data, "dict"):
        dumped = data.dict()
    else:
        dumped = data
    return json.dumps(dumped, indent=indent)


def render_yaml(data: Union[HandoffEnvelope, WorkState, Any]) -> str:
    """Serialize model to structured YAML."""
    if hasattr(data, "model_dump"):
        dumped = data.model_dump(mode="json")
    elif hasattr(data, "dict"):
        dumped = data.dict()
    else:
        dumped = data
    return yaml.dump(dumped, sort_keys=False, default_flow_style=False)
