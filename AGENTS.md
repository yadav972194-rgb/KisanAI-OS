# AGENTS.md

## Repository
KisanAI-OS — Farmer AI assistant backend (Phase 1.x milestones).

## Commands
- Run the full test suite: `python -m pytest tests/` (currently **772/772 passing**)
- Run a single test file: `python -m pytest tests/test_<module>.py -v`
- Syntax check changed Python files: `python -m py_compile <file...>`
- Live API verification requires `PYTHONPATH` set to project root before running scripts.

## Conventions
- Backend responses and code identifiers are in English; user-facing assistant messages are in Hindi.
- No DB schema changes without a new Alembic migration. Never touch Advisory API, auth architecture, or existing provider contracts — additive changes only.
- New detection features follow the growth-stage pattern: provider (with `Unavailable*` fallback) → service → controller → `main.py` endpoint (with `*Error` handler) → intent routing → tests in 3 files (`_provider`, `_intent`, base).

## Environment
- Windows / PowerShell. Use `cmd1; if ($?) { cmd2 }` to chain. Use `workdir` instead of `cd`.