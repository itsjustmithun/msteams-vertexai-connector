from typing import Dict, List


def build_routing_prompt(
    initial_message: str,
    sender_name: str,
    current_question: str,
    current_question_id: str,
    current_user_message: str,
    answers: List[Dict[str, str]],
    allowed_next_ids: List[str],
) -> str:
    answers_block = "\n".join(
        [f"- {item['question_id']}: {item['answer']}" for item in answers]
    )
    allowed_block = ", ".join(allowed_next_ids)
    return (
        "You are MSTeams Vertex Connector routing controller.\n"
        "Decide whether the user answered the current question.\n"
        "If off-topic or unclear, set accepted_answer=false and keep next_question_id equal to current_question_id.\n"
        "Allowed next_question_id values are restricted to the provided list.\n"
        "Return JSON only with keys: next_question_id (string), accepted_answer (boolean), "
        "normalized_answer (string or null), assistant_message (string).\n\n"
        f"Sender: {sender_name}\n"
        f"Initial message: {initial_message}\n"
        f"Current question id: {current_question_id}\n"
        f"Current question: {current_question}\n"
        f"Current user message: {current_user_message}\n"
        "Existing answers:\n"
        f"{answers_block if answers_block else '- none'}\n"
        f"Allowed next ids: {allowed_block}\n\n"
        "JSON format example:\n"
        "{\"next_question_id\":\"q2\",\"accepted_answer\":true,"
        "\"normalized_answer\":\"Product managers\",\"assistant_message\":\"Thanks.\"}"
    )


def build_final_prompt(
    initial_message: str, sender_name: str, answers: List[Dict[str, str]]
) -> str:
    answers_block = "\n".join(
        [f"- {item['question_id']}: {item['answer']}" for item in answers]
    )
    return (
        "You are MSTeams Vertex Connector.\n"
        "Given the survey answers, return JSON only with keys: summary and agent_message.\n"
        "summary must be concise. agent_message should be a direct reply to the user.\n\n"
        f"Sender: {sender_name}\n"
        f"Initial message: {initial_message}\n\n"
        "Survey answers:\n"
        f"{answers_block}\n\n"
        "JSON format example:\n"
        "{\"summary\":\"...\",\"agent_message\":\"...\"}"
    )

