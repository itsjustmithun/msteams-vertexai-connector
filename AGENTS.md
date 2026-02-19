---
alwaysApply: true
always_on: true
trigger: always_on
applyTo: "**"
description: Enforce minimal, modular, production-safe implementation
---

# AGENTS.md

## Mission

Build and maintain a minimal FastAPI service that:

1. Receives REST calls from Power Automate.
2. Calls Vertex AI via LangChain.
3. Returns stable JSON.

Do not expand scope beyond this mission.

---

## Architecture Rules (Non-Negotiable)

- API layer (`src/api`) handles validation and HTTP only.
- Core layer (`src/core`) contains orchestration and prompt logic.
- Providers (`src/providers`) wrap external services only.
- Config (`src/config`) handles environment variables only.
- Formatter (`core/formatter.py`) owns final JSON shape.

No cross-layer shortcuts.

---

## Response Contract

- Always return JSON.
- Never return raw LLM output.
- Never expose stack traces.
- Maintain stable response schema.
- Additive changes only.

---

## Dependency Discipline

Allowed:
- FastAPI
- Pydantic
- LangChain
- langchain-google-genai

Do not introduce:
- Databases
- Queues
- Workflow engines
- Telemetry stacks
- Logging frameworks
- UI layers

---

## Change Rules

- Keep diffs small.
- No unrelated refactors.
- No premature abstraction.
- Prefer simple functions over complex classes.
- If unclear about behavior, stop and clarify.
- Plan steps and keep track of them as you implement features.
- Run `pytest` and relevant checks proactively after changes.

---

## Required Skills Usage

Before implementing:

- Use `.skills/coding-skills.md` for architectural and implementation guidance.
- Use `.skills/testing-skills.md` when modifying API, schemas, or providers.
- Use the `.skills/review-skills.md` when user asks to review the code.

Do not bypass skills guidance.

---

## Definition of Done

A change is complete only if:

- Architecture boundaries are respected.
- Tests pass.
- No unnecessary dependencies added.
- JSON response contract preserved.
