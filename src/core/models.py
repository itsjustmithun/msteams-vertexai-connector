from dataclasses import dataclass
from typing import List, Dict


@dataclass(frozen=True)
class CoreRequest:
    source: str
    event_type: str
    message_content: str
    sender_name: str
    mentions: List[Dict[str, str]]
    correlation_id: str


@dataclass(frozen=True)
class Answer:
    question_id: str
    question: str
    answer: str


@dataclass(frozen=True)
class AgentResult:
    summary: str
    answers: List[Answer]
    model: str
    latency_ms: int
