# Review Skills

priority: high
use_when:
  - Reviewing PRs
  - Evaluating architecture changes
  - Checking new dependencies
  - Approving schema updates

---

## Goal

Protect simplicity, boundaries, and API stability.

---

## Architecture

- API: no business logic.
- Core: no FastAPI imports.
- Providers: no formatting or prompts.
- Formatter owns final JSON shape.
- Config: env parsing only.

Reject boundary violations.

---

## Simplicity

- Remove unnecessary abstractions.
- No speculative flexibility.
- Minimal > clever.

---

## Dependencies

- Must be strictly necessary.
- Prefer standard library.
- No DBs, queues, telemetry, logging frameworks.

---

## API Contract

- JSON schema must remain stable.
- No breaking changes without explicit reason.
- No stack traces in responses.

---

## Testing

- Critical paths covered.
- Vertex mocked.
- Tests fast and deterministic.

---

## Diff Discipline

- Small, focused changes only.
- No unrelated refactors.

If unsure → request clarification.
Stability over speed.
