import json
from typing import Any, Dict, List, Optional, Tuple

from src.core.errors import CoreError
from src.core.models import Answer
from src.agents.survey_agent.models import RoutingDecision


def build_answers(
    answers_by_id: Dict[str, str], questions: List[Dict[str, Any]]
) -> List[Answer]:
    answers: List[Answer] = []
    for question in questions:
        question_id = question["question_id"]
        question_text = question["question"]
        answers.append(
            Answer(
                question_id=question_id,
                question=question_text,
                answer=answers_by_id.get(question_id, ""),
                solution_id=question.get("solution_id")
                if isinstance(question.get("solution_id"), str)
                else None,
            )
        )
    return answers


def parse_routing_output(model_output: str) -> RoutingDecision:
    try:
        data = json.loads(model_output)
    except json.JSONDecodeError as exc:
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.") from exc

    if not isinstance(data, dict):
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.")

    next_question_id = data.get("next_question_id")
    accepted_answer = data.get("accepted_answer")
    assistant_message = data.get("assistant_message")
    normalized_answer = data.get("normalized_answer")
    if (
        not isinstance(next_question_id, str)
        or not isinstance(accepted_answer, bool)
        or not isinstance(assistant_message, str)
    ):
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.")

    normalized_value: Optional[str] = None
    if isinstance(normalized_answer, str):
        normalized_value = normalized_answer.strip()
    elif normalized_answer is not None:
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.")

    return RoutingDecision(
        next_question_id=next_question_id.strip(),
        accepted_answer=accepted_answer,
        assistant_message=assistant_message.strip(),
        normalized_answer=normalized_value,
    )


def parse_final_model_output(model_output: str) -> Tuple[str, str]:
    try:
        data = json.loads(model_output)
    except json.JSONDecodeError as exc:
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.") from exc

    if not isinstance(data, dict):
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.")

    summary = data.get("summary")
    agent_message = data.get("agent_message")
    if not isinstance(summary, str) or not isinstance(agent_message, str):
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.")

    return summary.strip(), agent_message.strip()
