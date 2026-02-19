import json

from fastapi.testclient import TestClient

from src.api import routes
from src.app import app

client = TestClient(app)
SURVEY_PATH = routes.SURVEY_PATH


class ScenarioProvider:
    model_name = "test-model"

    def __init__(
        self,
        call_plan: list[tuple[str, dict]] | None = None,
        fail_on: str | None = None,
    ) -> None:
        self.call_plan = call_plan or []
        self.fail_on = fail_on
        self.routing_call_count = 0
        self.final_call_count = 0

    def generate(self, prompt: str) -> str:
        if not self.call_plan:
            raise RuntimeError("missing planned model call")

        mode, payload = self.call_plan.pop(0)
        if mode == "routing":
            if self.fail_on == "routing":
                raise RuntimeError("boom")
            if "next_question_id" not in prompt:
                raise RuntimeError("unexpected non-routing prompt")
            self.routing_call_count += 1
            return json.dumps(payload)

        if mode != "final":
            raise RuntimeError("unknown planned call mode")
        if self.fail_on == "final":
            raise RuntimeError("boom")
        if "summary and agent_message" not in prompt:
            raise RuntimeError("unexpected non-final prompt")
        self.final_call_count += 1
        return json.dumps(payload)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def build_payload(message_content: str, survey_state: dict | None = None) -> dict:
    payload = {
        "source": "msteams",
        "event_type": "message_mentioned",
        "team": {"id": "TEAM_ID", "channel_id": "CHANNEL_ID"},
        "message": {
            "id": "MESSAGE_ID",
            "content_type": "html",
            "content": message_content,
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
    if survey_state is not None:
        payload["survey_state"] = survey_state
    return payload


def test_valid_request_multi_turn() -> None:
    original_provider = routes.get_vertex_provider
    provider = ScenarioProvider(
        call_plan=[
            (
                "routing",
                {
                    "next_question_id": "q1",
                    "accepted_answer": False,
                    "normalized_answer": None,
                    "assistant_message": "I still need the goal. Please answer q1.",
                },
            ),
            (
                "routing",
                {
                    "next_question_id": "q2",
                    "accepted_answer": True,
                    "normalized_answer": "Gather onboarding feedback.",
                    "assistant_message": "Captured.",
                },
            ),
            (
                "routing",
                {
                    "next_question_id": "q3",
                    "accepted_answer": True,
                    "normalized_answer": "Engineering teams.",
                    "assistant_message": "Captured.",
                },
            ),
            (
                "routing",
                {
                    "next_question_id": "END",
                    "accepted_answer": True,
                    "normalized_answer": "Next week.",
                    "assistant_message": "Captured.",
                },
            ),
            (
                "final",
                {
                    "summary": "Survey completed successfully.",
                    "agent_message": "Thanks. I have captured your survey responses.",
                },
            ),
        ]
    )
    routes.get_vertex_provider = lambda: provider

    # Turn 1: start survey, return q1 without model calls.
    response_1 = client.post(
        SURVEY_PATH, json=build_payload("<p>Hello @Agent please run survey</p>")
    )
    assert response_1.status_code == 200
    body_1 = response_1.json()
    assert body_1["ok"] is True
    assert body_1["result"]["status"] == "in_progress"
    assert body_1["result"]["survey_state"]["current_question_id"] == "q1"
    assert body_1["result"]["survey_state"]["awaiting_question_id"] == "q1"
    assert provider.routing_call_count == 0
    assert provider.final_call_count == 0
    assert body_1["result"]["answers"][0]["solution_id"] == "s1"

    # Turn 2: off-topic answer should hold position on q1.
    response_2 = client.post(
        SURVEY_PATH,
        json=build_payload(
            "By the way what model are you using?",
            survey_state=body_1["result"]["survey_state"],
        ),
    )
    assert response_2.status_code == 200
    body_2 = response_2.json()
    assert body_2["result"]["survey_state"]["current_question_id"] == "q1"
    assert body_2["result"]["survey_state"]["awaiting_question_id"] == "q1"
    assert body_2["result"]["agent_message"] == "I still need the goal. Please answer q1."
    assert body_2["result"]["answers"][0]["answer"] == ""
    assert provider.routing_call_count == 1
    assert provider.final_call_count == 0

    # Turn 3: valid q1 answer advances to q2.
    response_3 = client.post(
        SURVEY_PATH,
        json=build_payload(
            "The goal is onboarding feedback.",
            survey_state=body_2["result"]["survey_state"],
        ),
    )
    assert response_3.status_code == 200
    body_3 = response_3.json()
    assert body_3["result"]["survey_state"]["current_question_id"] == "q2"
    assert body_3["result"]["survey_state"]["awaiting_question_id"] == "q2"
    assert body_3["result"]["answers"][0]["answer"] == "Gather onboarding feedback."
    assert provider.routing_call_count == 2
    assert provider.final_call_count == 0

    # Turn 4: valid q2 answer advances to q3.
    response_4 = client.post(
        SURVEY_PATH,
        json=build_payload(
            "Audience is internal product teams.",
            survey_state=body_3["result"]["survey_state"],
        ),
    )
    assert response_4.status_code == 200
    body_4 = response_4.json()
    assert body_4["result"]["status"] == "in_progress"
    assert body_4["result"]["survey_state"]["current_question_id"] == "q3"
    assert body_4["result"]["answers"][1]["answer"] == "Engineering teams."
    assert provider.routing_call_count == 3
    assert provider.final_call_count == 0

    # Turn 5: valid q3 answer completes survey and triggers final synthesis.
    response_5 = client.post(
        SURVEY_PATH,
        json=build_payload(
            "Run it next Monday.",
            survey_state=body_4["result"]["survey_state"],
        ),
    )
    assert response_5.status_code == 200
    body_5 = response_5.json()
    assert body_5["ok"] is True
    assert body_5["correlation_id"] == "FLOW_RUN_ID_OR_CUSTOM_GUID"
    assert body_5["result"]["status"] == "completed"
    assert body_5["result"]["survey_state"] is None
    assert body_5["result"]["agent_message"] == "Thanks. I have captured your survey responses."
    assert body_5["result"]["answers"][2]["answer"] == "Next week."
    assert body_5["result"]["answers"][2]["solution_id"] == "s3"
    assert provider.routing_call_count == 4
    assert provider.final_call_count == 1

    routes.get_vertex_provider = original_provider


def test_invalid_request() -> None:
    response = client.post(SURVEY_PATH, json={"source": "msteams"})
    assert response.status_code == 422


def test_invalid_routing_output_fallback() -> None:
    original_provider = routes.get_vertex_provider
    provider = ScenarioProvider(
        call_plan=[
            (
                "routing",
                {
                    "next_question_id": "q999",
                    "accepted_answer": True,
                    "normalized_answer": "Capture goal.",
                    "assistant_message": "Captured.",
                },
            )
        ]
    )
    routes.get_vertex_provider = lambda: provider

    response_1 = client.post(
        SURVEY_PATH,
        json=build_payload("<p>Hello @Agent please run survey</p>"),
    )
    state_1 = response_1.json()["result"]["survey_state"]

    response_2 = client.post(
        SURVEY_PATH, json=build_payload("Goal is feedback.", survey_state=state_1)
    )
    assert response_2.status_code == 200
    body_2 = response_2.json()
    assert body_2["result"]["status"] == "in_progress"
    assert body_2["result"]["survey_state"]["current_question_id"] == "q2"
    assert body_2["result"]["answers"][0]["answer"] == "Capture goal."
    assert provider.final_call_count == 0

    routes.get_vertex_provider = original_provider


def test_provider_failure() -> None:
    original_provider = routes.get_vertex_provider
    provider = ScenarioProvider(
        call_plan=[
            (
                "routing",
                {
                    "next_question_id": "END",
                    "accepted_answer": True,
                    "normalized_answer": "Run it tomorrow.",
                    "assistant_message": "Captured.",
                },
            ),
            (
                "final",
                {
                    "summary": "Survey completed successfully.",
                    "agent_message": "Thanks. I have captured your survey responses.",
                },
            ),
        ],
        fail_on="final",
    )
    routes.get_vertex_provider = lambda: provider

    response = client.post(
        SURVEY_PATH,
        json=build_payload(
            "Run it tomorrow.",
            survey_state={
                "status": "in_progress",
                "initial_message": "<p>Hello @Agent please run survey</p>",
                "current_question_id": "q3",
                "awaiting_question_id": "q3",
                "answers": [
                    {"question_id": "q1", "answer": "Gather feedback."},
                    {"question_id": "q2", "answer": "Leadership."},
                ],
            },
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "VERTEX_UNAVAILABLE"

    routes.get_vertex_provider = original_provider
