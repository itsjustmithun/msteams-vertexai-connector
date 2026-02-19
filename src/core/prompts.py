from typing import List, Dict

SURVEY_QUESTIONS: List[Dict[str, str]] = [
    {"question_id": "q1", "question": "What is the goal of this survey request?"},
    {"question_id": "q2", "question": "Who is the intended audience?"},
    {"question_id": "q3", "question": "When should the survey be run?"},
]


def build_prompt(message_content: str, sender_name: str) -> str:
    questions_block = "\n".join(
        [f"- {q['question_id']}: {q['question']}" for q in SURVEY_QUESTIONS]
    )
    return (
        "You are MSTeams Vertex Connector. Read the message and answer the fixed questions.\n"
        "Return JSON only with keys: summary (string) and answers (array).\n"
        "Each answers item must include: question_id and answer.\n\n"
        f"Sender: {sender_name}\n"
        f"Message: {message_content}\n\n"
        "Questions:\n"
        f"{questions_block}\n\n"
        "JSON format example:\n"
        "{\"summary\": \"...\", \"answers\": [{\"question_id\": \"q1\", \"answer\": \"...\"}]}")
