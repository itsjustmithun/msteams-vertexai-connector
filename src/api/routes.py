from fastapi import APIRouter

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
from src.config.settings import get_settings, get_survey_path
from src.core.agent import run_agent
from src.core.errors import CoreError
from src.core.models import CoreRequest
from src.providers.vertex_ai import VertexAIProvider

router = APIRouter()
SURVEY_PATH = get_survey_path()


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
        )
        result = run_agent(core_request, provider)
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
                    )
                    for answer in result.answers
                ],
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
