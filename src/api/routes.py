from fastapi import APIRouter

from src.agents.survey_agent import run_survey_agent
from src.api.schemas import (
    AnswerItem,
    ErrorDetail,
    ErrorResponse,
    Meta,
    Result,
    SuccessResponse,
    SurveyRequest,
    SurveyResponse,
)
from src.config.settings import get_configured_path, get_settings
from src.core.formatter import serialize_agent_state
from src.core.agent import register_agent_runner, run_agent
from src.core.errors import CoreError
from src.core.models import CoreRequest
from src.providers.vertex_ai import VertexAIProvider

router = APIRouter()
SURVEY_PATH = get_configured_path(
    env_key="AGENT_SURVEY_PATH",
    default="/survey",
    legacy_env_key="SURVEY_PATH",
)
PATH_TO_AGENT_KEY = {
    SURVEY_PATH: "survey",
}
register_agent_runner(PATH_TO_AGENT_KEY[SURVEY_PATH], run_survey_agent)


def get_vertex_provider() -> VertexAIProvider:
    settings = get_settings()
    return VertexAIProvider(
        model_name=settings.vertex_model,
        project=settings.gcp_project,
        location=settings.gcp_region,
    )


@router.get("/health")
def health() -> dict:
    return {"ok": True}


@router.post(SURVEY_PATH, response_model=SurveyResponse)
def survey(request: SurveyRequest) -> SurveyResponse:
    try:
        provider = get_vertex_provider()
        core_request = CoreRequest(
            source=request.source,
            event_type=request.event_type,
            message_content=request.message.content,
            sender_name=request.sender.display_name,
            mentions=[mention.model_dump() for mention in request.mentions],
            correlation_id=request.correlation_id,
            agent_state=(
                request.survey_state.model_dump()
                if request.survey_state is not None
                else None
            ),
        )
        result = run_agent(core_request, provider, agent_key=PATH_TO_AGENT_KEY[SURVEY_PATH])
        return SuccessResponse(
            ok=True,
            correlation_id=request.correlation_id,
            result=Result(
                summary=result.summary,
                answers=[
                    AnswerItem(
                        question_id=answer.question_id,
                        question=answer.question,
                        answer=answer.answer,
                        solution_id=answer.solution_id,
                    )
                    for answer in result.answers
                ],
                status=result.status,
                agent_message=result.agent_message,
                survey_state=serialize_agent_state(result.agent_state),
            ),
            meta=Meta(model=result.model, latency_ms=result.latency_ms),
        )
    except CoreError as exc:
        return ErrorResponse(
            ok=False,
            correlation_id=request.correlation_id,
            error=ErrorDetail(code=exc.code, message=exc.message),
        )
    except ValueError:
        return ErrorResponse(
            ok=False,
            correlation_id=request.correlation_id,
            error=ErrorDetail(
                code="CONFIG_ERROR", message="Missing required configuration."
            ),
        )
    except Exception:
        return ErrorResponse(
            ok=False,
            correlation_id=request.correlation_id,
            error=ErrorDetail(
                code="INTERNAL_ERROR", message="Unexpected server error."
            ),
        )
