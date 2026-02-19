# Coding Skills

priority: high
use_when:
  - Writing new features
  - Refactoring code
  - Creating new modules
  - Adjusting architecture

---

## Core Principles

- Keep functions small.
- Prefer explicit inputs and outputs.
- Avoid hidden state.
- Avoid deep inheritance.
- Avoid unnecessary abstractions.

---

## Layer Enforcement

API:
- No business logic.
- No provider calls directly.

Core:
- No FastAPI imports.
- Orchestrates only.

Providers:
- No prompt construction.
- No formatting logic.
- Single responsibility: external call.

Config:
- Env parsing only.
- No side effects.

---

## Type Safety

- Use type hints for public functions.
- Use Pydantic for request/response schemas.
- Avoid returning raw dicts from core.

---

## Error Handling

- Raise controlled exceptions in core.
- Convert exceptions to stable JSON in API layer.
- Never leak raw errors.

---

## Simplicity Heuristic

If implementation feels complex:
- Remove abstraction.
- Inline logic.
- Reduce indirection.

Minimal > clever.
