# MSTeams VertexAI Connector

Sample FastAPI service that connects Microsoft Teams (via Power Automate) to Vertex AI through LangChain and returns stable JSON for downstream flows.

## What it does

- Receives HTTP calls from Power Automate (Teams events).
- Builds a compact prompt and calls Vertex AI through LangChain.
- Returns a deterministic JSON shape for success and error cases.

## Architecture

- API layer handles request validation and HTTP only.
- Core layer handles orchestration and prompt logic.
- Provider layer wraps Vertex AI calls only.
- Config layer reads environment variables only.
- Formatter owns the final JSON shape.

## Requirements

- Python 3.11+
- GCP project with Vertex AI enabled
- Application Default Credentials (ADC) or a service account JSON

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install uvicorn
```

## Configuration

Set the required environment variables:

```bash
export VERTEX_MODEL="gemini-3-pro"
export GCP_PROJECT="your-gcp-project"
export GCP_REGION="us-central1"
```

Optional endpoint override:

```bash
export SURVEY_PATH="/survey"
```

Authentication options:

- `gcloud auth application-default login`
- or set `GOOGLE_APPLICATION_CREDENTIALS` to a service account JSON path

## Run locally

```bash
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

## Power Automate notes

- Use an HTTP action to call `/survey` (or `SURVEY_PATH` if overridden).
- Keep response parsing strictly by JSON keys (`ok`, `result`, `error`).
- Always pass a `correlation_id` from your flow for traceability.

## Schemas

- Request example: [schema/request.json](schema/request.json)
- Response example: [schema/response.json](schema/response.json)
