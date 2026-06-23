# Second Real Captured Task Selection

## Purpose

Select a small, safe, documentation-only task for the second governed backend-created output adoption lifecycle. This validates that the lifecycle (77J-77V.1 pattern) is repeatable after the governance hardening (79A-79F) and lifecycle orchestration (80A-80F) work.

## Selected Task

Draft a concise markdown documentation snippet describing PCAE's backend-output-adoption lifecycle command family:

- `pcae lifecycle backend-output-adoption status [--json]`
- `pcae lifecycle backend-output-adoption next [--json]`
- `pcae lifecycle backend-output-adoption run-gate --gate <gate> --dry-run [--json]`
- `pcae lifecycle backend-output-adoption approve-gate --gate <gate> --approved-by <name> --reason <reason> [--dry-run] [--json]`
- `pcae lifecycle backend-output-adoption summary [--json]`

The snippet should explain that these commands provide lifecycle visibility, advisory next steps, dry-run gate evaluation, approval recording without execution, and final summary reporting. It must explicitly state that non-dry-run gate execution is not implemented and that approval is separate from execution.

## Why This Task Was Selected

1. **Documentation-only.** The backend produces only markdown text. No source code, no tests, no binary artifacts, no dependency changes.
2. **Bounded scope.** The snippet describes exactly five commands. The expected output is a concise markdown section (50-150 lines).
3. **Directly validates new work.** The 80A-80F lifecycle commands are the latest addition. Having the backend describe them tests whether it can accurately document governed PCAE behavior.
4. **Low risk.** If the backend produces incorrect or unsafe output, PCAE will quarantine it. The content is documentation, not executable code.
5. **Easy to review.** The output can be verified against the actual command JSON output and existing design docs.
6. **Deterministic review criteria.** The snippet either correctly describes the five commands or it does not.
7. **Repeatable lifecycle path.** The adoption pipeline (capture, quarantine, review, approve, stage, commit, push, verify) can be exercised again with the friction fixes from 79A-79F available.

## Scope

- Output: one markdown file (documentation snippet).
- Target: lifecycle command family documentation.
- Content: command names, purpose, key flags, safety properties.
- Length: 50-150 lines of markdown.

## Non-Goals

- Do not ask the backend to write source code.
- Do not ask the backend to write tests.
- Do not ask the backend to modify existing files.
- Do not ask the backend to produce multiple files.
- Do not ask the backend to make architectural decisions.
- Do not ask the backend to execute lifecycle gates.

## Allowed Future Output Type

- Markdown documentation file (.md).
- Single file.
- Text-only (no images, diagrams, or binary content).

## Candidate Target Files for Future Adoption

If the backend output is approved through the governed lifecycle, it could be adopted into:

- `docs/LIFECYCLE_COMMANDS.md` (new file, preferred)
- `README.md` (as a section addition, less preferred)
- `docs/LIFECYCLE_STATE_MACHINE.md` (as a section addition)

The final adoption target will be decided during the adoption review phase, not during task selection.

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Backend produces incorrect command descriptions | Low | Review against actual `--json` output |
| Backend includes unsafe instructions | Very low | Content safety scan in adoption review |
| Backend modifies repository files | Low | Mutation guard detects and quarantines |
| Backend produces excessive output | Low | Quarantine review checks size/scope |
| Backend produces source code instead of docs | Very low | Content safety scan blocks source references |
| Lifecycle friction repeats 77S issues | Low | 79A-79F staged-file-aware hardening available |

## Review Criteria

The backend output should be accepted if:

1. It is markdown-only text.
2. It correctly names all five lifecycle commands.
3. It correctly describes what each command does.
4. It states that `run-gate` requires `--dry-run`.
5. It states that `approve-gate` records approval without executing.
6. It states that `non_dry_run_runner_command=false`.
7. It states that `execution_authorized=false` always.
8. It does not contain secrets, credentials, or API keys.
9. It does not contain governance bypass instructions.
10. It does not contain force push or raw push instructions.
11. It does not reference or modify source code files.
12. It is between 50 and 200 lines.

## Required Future Gates

The full governed lifecycle must be followed:

1. 81B — Task contract preparation
2. 81C — Backend capture preflight
3. 81D — Backend capture
4. 81E — Output intake
5. 81F — Adoption lifecycle using consolidated gates
6. 81G — Final verification

Each gate requires its own approval where applicable. No gate may be skipped.

## Backend Invocation in This Phase

**No backend invocation occurred in Phase 81A.** This phase is selection and planning only. Backend capture is deferred to Phase 81D after contract preparation (81B) and preflight (81C).

## Recommended Next Phase

**81B — Second Real Captured Task Contract**

81B should create the formal task contract binding the selected task to a governed backend capture lifecycle.
