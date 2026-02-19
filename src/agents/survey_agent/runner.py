import time

from src.agents.survey_agent.catalog import SURVEY_QUESTION_CATALOG
from src.agents.survey_agent.formatter import (
    build_answers,
    parse_final_model_output,
    parse_routing_output,
)
from src.agents.survey_agent.models import (
    RoutingDecision,
    StateAnswer,
    SurveyState,
    survey_state_from_dict,
    survey_state_to_dict,
)
from src.agents.survey_agent.prompts import build_final_prompt, build_routing_prompt
from src.core.errors import CoreError
from src.core.models import AgentResult, CoreRequest
from src.providers.vertex_ai import VertexAIProvider


def _first_unanswered_question_id(answers_by_id: dict[str, str]) -> str | None:
    for question in SURVEY_QUESTION_CATALOG:
        question_id = question["question_id"]
        if not answers_by_id.get(question_id, "").strip():
            return question_id
    return None


def _build_state(
    initial_message: str,
    current_question_id: str | None,
    answers_by_id: dict[str, str],
) -> SurveyState:
    state_answers = [
        StateAnswer(
            question_id=question["question_id"],
            answer=answers_by_id[question["question_id"]],
        )
        for question in SURVEY_QUESTION_CATALOG
        if answers_by_id.get(question["question_id"], "").strip()
    ]
    return SurveyState(
        status="in_progress",
        initial_message=initial_message,
        current_question_id=current_question_id,
        awaiting_question_id=current_question_id,
        answers=state_answers,
    )


def _safe_fallback_next_question_id(
    current_question_id: str | None,
    answers_by_id: dict[str, str],
) -> str | None:
    if current_question_id and not answers_by_id.get(current_question_id, "").strip():
        return current_question_id
    return _first_unanswered_question_id(answers_by_id)


def _call_routing_model(
    provider: VertexAIProvider,
    initial_message: str,
    sender_name: str,
    current_question: dict[str, str],
    current_user_message: str,
    answers_by_id: dict[str, str],
    allowed_next_ids: list[str],
) -> RoutingDecision:
    prompt = build_routing_prompt(
        initial_message=initial_message,
        sender_name=sender_name,
        current_question=current_question["question"],
        current_question_id=current_question["question_id"],
        current_user_message=current_user_message,
        answers=[
            {"question_id": qid, "answer": answer}
            for qid, answer in answers_by_id.items()
            if answer.strip()
        ],
        allowed_next_ids=allowed_next_ids,
    )
    try:
        model_output = provider.generate(prompt)
    except Exception as exc:
        raise CoreError("VERTEX_UNAVAILABLE", "Upstream model call failed.") from exc

    return parse_routing_output(model_output)


def run_survey_agent(request: CoreRequest, provider: VertexAIProvider) -> AgentResult:
    question_map = {
        question["question_id"]: question for question in SURVEY_QUESTION_CATALOG
    }
    question_ids = set(question_map.keys())
    answers_by_id: dict[str, str] = {}
    initial_message = request.message_content
    current_question_id = None
    state = survey_state_from_dict(request.agent_state)

    if state is not None:
        initial_message = state.initial_message
        current_question_id = state.current_question_id
        if not current_question_id:
            current_question_id = state.awaiting_question_id
        for item in state.answers:
            if item.question_id in question_ids:
                answers_by_id[item.question_id] = item.answer

    if current_question_id not in question_ids:
        current_question_id = _first_unanswered_question_id(answers_by_id)

    if current_question_id is not None and state is None:
        answers = build_answers(answers_by_id, SURVEY_QUESTION_CATALOG)
        survey_state = _build_state(initial_message, current_question_id, answers_by_id)
        return AgentResult(
            summary="Survey in progress.",
            answers=answers,
            model=provider.model_name,
            latency_ms=0,
            status="in_progress",
            agent_message=question_map[current_question_id]["question"],
            agent_state=survey_state_to_dict(survey_state),
        )

    latency_start = time.time()
    if current_question_id is not None:
        current_question = question_map[current_question_id]
        remaining_ids = [
            question["question_id"]
            for question in SURVEY_QUESTION_CATALOG
            if not answers_by_id.get(question["question_id"], "").strip()
        ]
        allowed_next_ids = [*remaining_ids, "END"]
        raw_user_answer = request.message_content.strip()

        try:
            routing = _call_routing_model(
                provider=provider,
                initial_message=initial_message,
                sender_name=request.sender_name,
                current_question=current_question,
                current_user_message=request.message_content,
                answers_by_id=answers_by_id,
                allowed_next_ids=allowed_next_ids,
            )
        except CoreError as exc:
            if exc.code == "MODEL_PARSE_ERROR":
                fallback_question_id = _safe_fallback_next_question_id(
                    current_question_id, answers_by_id
                )
                answers = build_answers(answers_by_id, SURVEY_QUESTION_CATALOG)
                survey_state = _build_state(
                    initial_message, fallback_question_id, answers_by_id
                )
                return AgentResult(
                    summary="Survey in progress.",
                    answers=answers,
                    model=provider.model_name,
                    latency_ms=int((time.time() - latency_start) * 1000),
                    status="in_progress",
                    agent_message=(
                        question_map[fallback_question_id]["question"]
                        if fallback_question_id
                        else "Please continue the survey."
                    ),
                    agent_state=survey_state_to_dict(survey_state),
                )
            raise

        if not routing.accepted_answer:
            answers = build_answers(answers_by_id, SURVEY_QUESTION_CATALOG)
            survey_state = _build_state(
                initial_message, current_question_id, answers_by_id
            )
            clarification = routing.assistant_message or (
                f"Please answer this question: {current_question['question']}"
            )
            return AgentResult(
                summary="Survey in progress.",
                answers=answers,
                model=provider.model_name,
                latency_ms=int((time.time() - latency_start) * 1000),
                status="in_progress",
                agent_message=clarification,
                agent_state=survey_state_to_dict(survey_state),
            )

        normalized = (
            routing.normalized_answer.strip()
            if routing.normalized_answer and routing.normalized_answer.strip()
            else ""
        )
        candidate_answer = normalized or raw_user_answer
        if not candidate_answer:
            answers = build_answers(answers_by_id, SURVEY_QUESTION_CATALOG)
            survey_state = _build_state(
                initial_message, current_question_id, answers_by_id
            )
            return AgentResult(
                summary="Survey in progress.",
                answers=answers,
                model=provider.model_name,
                latency_ms=int((time.time() - latency_start) * 1000),
                status="in_progress",
                agent_message=f"Please answer this question: {current_question['question']}",
                agent_state=survey_state_to_dict(survey_state),
            )

        answers_by_id[current_question_id] = candidate_answer

        remaining_after_save = [
            question["question_id"]
            for question in SURVEY_QUESTION_CATALOG
            if not answers_by_id.get(question["question_id"], "").strip()
        ]
        allowed_after_save = set([*remaining_after_save, "END"])
        next_question_id = routing.next_question_id
        if next_question_id not in allowed_after_save:
            next_question_id = _safe_fallback_next_question_id(
                current_question_id=None,
                answers_by_id=answers_by_id,
            ) or "END"

        if next_question_id != "END":
            answers = build_answers(answers_by_id, SURVEY_QUESTION_CATALOG)
            survey_state = _build_state(initial_message, next_question_id, answers_by_id)
            return AgentResult(
                summary="Survey in progress.",
                answers=answers,
                model=provider.model_name,
                latency_ms=int((time.time() - latency_start) * 1000),
                status="in_progress",
                agent_message=question_map[next_question_id]["question"],
                agent_state=survey_state_to_dict(survey_state),
            )

        if remaining_after_save:
            forced_next = remaining_after_save[0]
            answers = build_answers(answers_by_id, SURVEY_QUESTION_CATALOG)
            survey_state = _build_state(initial_message, forced_next, answers_by_id)
            return AgentResult(
                summary="Survey in progress.",
                answers=answers,
                model=provider.model_name,
                latency_ms=int((time.time() - latency_start) * 1000),
                status="in_progress",
                agent_message=question_map[forced_next]["question"],
                agent_state=survey_state_to_dict(survey_state),
            )

    answers = build_answers(answers_by_id, SURVEY_QUESTION_CATALOG)
    prompt = build_final_prompt(
        initial_message,
        request.sender_name,
        [
            {"question_id": answer.question_id, "answer": answer.answer}
            for answer in answers
        ],
    )
    try:
        model_output = provider.generate(prompt)
    except Exception as exc:
        raise CoreError("VERTEX_UNAVAILABLE", "Upstream model call failed.") from exc

    latency_ms = int((time.time() - latency_start) * 1000)
    summary, agent_message = parse_final_model_output(model_output)

    return AgentResult(
        summary=summary,
        answers=answers,
        model=provider.model_name,
        latency_ms=latency_ms,
        status="completed",
        agent_message=agent_message,
        agent_state=None,
    )

