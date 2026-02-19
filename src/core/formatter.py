from typing import Any, Dict, Optional


def serialize_agent_state(state: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if state is None:
        return None
    return dict(state)

