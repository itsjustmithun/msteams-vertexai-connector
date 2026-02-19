import json
from typing import List, Dict, Tuple

from src.core.errors import CoreError
from src.core.models import Answer


def format_model_output(
    model_output: str, questions: List[Dict[str, str]]
) -> Tuple[str, List[Answer]]:
    try:
        data = json.loads(model_output)
    except json.JSONDecodeError as exc:
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.") from exc

    if not isinstance(data, dict):
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.")

    summary = data.get("summary")
    answers_in = data.get("answers")
    if not isinstance(summary, str) or not isinstance(answers_in, list):
        raise CoreError("MODEL_PARSE_ERROR", "Model response could not be parsed.")

    answers_by_id: Dict[str, str] = {}
    for item in answers_in:
        if not isinstance(item, dict):
            continue
        question_id = item.get("question_id")
        answer = item.get("answer")
        if isinstance(question_id, str) and isinstance(answer, str):
            answers_by_id[question_id] = answer

    answers: List[Answer] = []
    for question in questions:
        question_id = question["question_id"]
        question_text = question["question"]
        answers.append(
            Answer(
                question_id=question_id,
                question=question_text,
                answer=answers_by_id.get(question_id, ""),
            )
        )

    return summary.strip(), answers
