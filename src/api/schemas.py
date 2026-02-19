from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict


class Team(BaseModel):
    id: str
    channel_id: str
    model_config = ConfigDict(extra="forbid")


class Message(BaseModel):
    id: str
    content_type: str
    content: str
    created_at: str
    reply_to_id: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class Sender(BaseModel):
    id: str
    display_name: str
    model_config = ConfigDict(extra="forbid")


class Mention(BaseModel):
    type: str
    id: str
    display_name: str
    model_config = ConfigDict(extra="forbid")


class SurveyRequest(BaseModel):
    source: str
    event_type: str
    team: Optional[Team] = None
    message: Message
    sender: Sender
    mentions: List[Mention]
    correlation_id: str
    model_config = ConfigDict(extra="forbid")


class AnswerItem(BaseModel):
    question_id: str
    question: str
    answer: str
    model_config = ConfigDict(extra="forbid")


class Result(BaseModel):
    summary: str
    answers: List[AnswerItem]
    model_config = ConfigDict(extra="forbid")


class Meta(BaseModel):
    model: str
    latency_ms: int
    model_config = ConfigDict(extra="forbid")


class ErrorDetail(BaseModel):
    code: str
    message: str
    model_config = ConfigDict(extra="forbid")


class SuccessResponse(BaseModel):
    ok: bool
    correlation_id: str
    result: Result
    meta: Meta
    model_config = ConfigDict(extra="forbid")


class ErrorResponse(BaseModel):
    ok: bool
    correlation_id: str
    error: ErrorDetail
    model_config = ConfigDict(extra="forbid")


SurveyResponse = Union[SuccessResponse, ErrorResponse]
