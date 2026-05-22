# Decisions

## Accepted

- Use Python and `pathlib` for cross-platform filesystem behavior.
- Use Markdown files as the only persistence mechanism for the MVP.
- Defer databases, LLM calls, and vector search.
- Keep commands modular under `src/pcae/commands`.
- Keep `pcae inspect` read-only; reserve enforcement and repair behavior for future commands.
