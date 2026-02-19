from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CoreRequest:
    source: str
    event_type: str
    message_content: str
    sender_name: str
    mentions: List[Dict[str, str]]
    correlation_id: str
    agent_state: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class Answer:
    question_id: str
    question: str
    answer: str
    solution_id: Optional[str] = None


@dataclass(frozen=True)
class AgentResult:
    summary: str
    answers: List[Answer]
    model: str
    latency_ms: int
    status: str
    agent_message: str
    agent_state: Optional[Dict[str, Any]] = None
