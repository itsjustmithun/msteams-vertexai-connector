from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class StateAnswer:
    question_id: str
    answer: str


@dataclass(frozen=True)
class SurveyState:
    status: str
    initial_message: str
    current_question_id: Optional[str]
    awaiting_question_id: Optional[str]
    answers: List[StateAnswer]


@dataclass(frozen=True)
class RoutingDecision:
    next_question_id: str
    accepted_answer: bool
    assistant_message: str
    normalized_answer: Optional[str] = None


def survey_state_from_dict(data: Optional[Dict[str, Any]]) -> Optional[SurveyState]:
    if not isinstance(data, dict):
        return None
    answers_in = data.get("answers")
    answers: List[StateAnswer] = []
    if isinstance(answers_in, list):
        for item in answers_in:
            if not isinstance(item, dict):
                continue
            question_id = item.get("question_id")
            answer = item.get("answer")
            if isinstance(question_id, str) and isinstance(answer, str):
                answers.append(StateAnswer(question_id=question_id, answer=answer))
    status = data.get("status")
    initial_message = data.get("initial_message")
    current_question_id = data.get("current_question_id")
    awaiting_question_id = data.get("awaiting_question_id")
    if not isinstance(status, str) or not isinstance(initial_message, str):
        return None
    if current_question_id is not None and not isinstance(current_question_id, str):
        current_question_id = None
    if awaiting_question_id is not None and not isinstance(awaiting_question_id, str):
        awaiting_question_id = None
    return SurveyState(
        status=status,
        initial_message=initial_message,
        current_question_id=current_question_id,
        awaiting_question_id=awaiting_question_id,
        answers=answers,
    )


def survey_state_to_dict(state: Optional[SurveyState]) -> Optional[Dict[str, Any]]:
    if state is None:
        return None
    return {
        "status": state.status,
        "initial_message": state.initial_message,
        "current_question_id": state.current_question_id,
        "awaiting_question_id": state.awaiting_question_id,
        "answers": [
            {
                "question_id": answer.question_id,
                "answer": answer.answer,
            }
            for answer in state.answers
        ],
    }

