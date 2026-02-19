import json

from fastapi.testclient import TestClient

from src.api import routes
from src.config.settings import get_survey_path
from src.app import app

client = TestClient(app)
SURVEY_PATH = get_survey_path()


class StubProvider:
    model_name = "test-model"

    def generate(self, prompt: str) -> str:
        return json.dumps(
            {
                "summary": "User is requesting to start the survey.",
                "answers": [
                    {"question_id": "q1", "answer": "Kick off the survey."},
                    {"question_id": "q2", "answer": "Product team."},
                    {"question_id": "q3", "answer": "Next week."},
                ],
            }
        )


class FailingProvider:
    model_name = "test-model"

    def generate(self, prompt: str) -> str:
        raise RuntimeError("boom")


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_valid_request() -> None:
    original_provider = routes.get_vertex_provider
    routes.get_vertex_provider = lambda: StubProvider()

    payload = {
        "source": "msteams",
        "event_type": "message_mentioned",
        "team": {"id": "TEAM_ID", "channel_id": "CHANNEL_ID"},
        "message": {
            "id": "MESSAGE_ID",
            "content_type": "html",
            "content": "<p>Hello @Agent please run survey</p>",
            "created_at": "2026-02-19T10:15:30Z",
            "reply_to_id": None,
        },
        "sender": {"id": "USER_ID", "display_name": "Jane Doe"},
        "mentions": [
            {
                "type": "user",
                "id": "AGENT_USER_ID",
                "display_name": "MSTeams Vertex Connector",
            }
        ],
        "correlation_id": "FLOW_RUN_ID_OR_CUSTOM_GUID",
    }

    response = client.post(SURVEY_PATH, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["correlation_id"] == "FLOW_RUN_ID_OR_CUSTOM_GUID"
    assert "result" in body
    assert "meta" in body
    assert body["result"]["answers"][0]["question_id"] == "q1"

    routes.get_vertex_provider = original_provider


def test_invalid_request() -> None:
    response = client.post(SURVEY_PATH, json={"source": "msteams"})
    assert response.status_code == 422


def test_provider_failure() -> None:
    original_provider = routes.get_vertex_provider
    routes.get_vertex_provider = lambda: FailingProvider()

    payload = {
        "source": "msteams",
        "event_type": "message_mentioned",
        "team": {"id": "TEAM_ID", "channel_id": "CHANNEL_ID"},
        "message": {
            "id": "MESSAGE_ID",
            "content_type": "html",
            "content": "<p>Hello @Agent please run survey</p>",
            "created_at": "2026-02-19T10:15:30Z",
            "reply_to_id": None,
        },
        "sender": {"id": "USER_ID", "display_name": "Jane Doe"},
        "mentions": [
            {
                "type": "user",
                "id": "AGENT_USER_ID",
                "display_name": "MSTeams Vertex Connector",
            }
        ],
        "correlation_id": "FLOW_RUN_ID_OR_CUSTOM_GUID",
    }

    response = client.post(SURVEY_PATH, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "VERTEX_UNAVAILABLE"

    routes.get_vertex_provider = original_provider
