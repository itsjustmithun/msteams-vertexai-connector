from typing import Callable, Dict

from src.core.errors import CoreError
from src.core.models import AgentResult, CoreRequest
from src.providers.vertex_ai import VertexAIProvider

AgentRunner = Callable[[CoreRequest, VertexAIProvider], AgentResult]

AGENT_RUNNERS: Dict[str, AgentRunner] = {}


def register_agent_runner(agent_key: str, runner: AgentRunner) -> None:
    AGENT_RUNNERS[agent_key] = runner


def get_agent_runner(agent_key: str) -> AgentRunner:
    runner = AGENT_RUNNERS.get(agent_key)
    if runner is None:
        raise CoreError("AGENT_NOT_FOUND", f"Unknown agent: {agent_key}")
    return runner


def run_agent(
    request: CoreRequest, provider: VertexAIProvider, agent_key: str
) -> AgentResult:
    runner = get_agent_runner(agent_key)
    return runner(request, provider)
