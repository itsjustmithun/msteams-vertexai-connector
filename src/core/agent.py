import time

from src.core.errors import CoreError
from src.core.formatter import format_model_output
from src.core.models import AgentResult, CoreRequest
from src.core.prompts import SURVEY_QUESTIONS, build_prompt
from src.providers.vertex_ai import VertexAIProvider


def run_agent(request: CoreRequest, provider: VertexAIProvider) -> AgentResult:
    prompt = build_prompt(request.message_content, request.sender_name)
    start = time.time()
    try:
        model_output = provider.generate(prompt)
    except Exception as exc:
        raise CoreError("VERTEX_UNAVAILABLE", "Upstream model call failed.") from exc

    latency_ms = int((time.time() - start) * 1000)
    summary, answers = format_model_output(model_output, SURVEY_QUESTIONS)

    return AgentResult(
        summary=summary,
        answers=answers,
        model=provider.model_name,
        latency_ms=latency_ms,
    )
