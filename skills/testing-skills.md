# Testing Skills

priority: high
use_when:
  - Adding or modifying endpoints
  - Changing schemas
  - Modifying formatter
  - Changing provider interface
  - Fixing bugs

---

## Core Testing Rules

- Tests must be fast.
- Tests must be deterministic.
- Never call real Vertex AI.
- Always mock providers.
- Focus on critical paths only.

---

## Minimum Required Tests

For API:

- Health endpoint returns 200.
- Valid request returns 200 with correct JSON shape.
- Invalid input returns 422.
- Provider failure returns controlled error JSON.

---

## Mocking Rules

- Mock `providers.vertex_ai` layer only.
- Do not mock core logic unless necessary.
- Never mock FastAPI itself.

---

## Validation Rules

- Assert response structure, not just status code.
- Assert JSON keys explicitly.
- Avoid brittle string matching.

---

## Anti-Patterns

Do not:
- Add integration tests with real GCP.
- Add slow end-to-end workflows.
- Test internal implementation details.
- Over-test trivial pure functions.

Test behavior, not internals.
