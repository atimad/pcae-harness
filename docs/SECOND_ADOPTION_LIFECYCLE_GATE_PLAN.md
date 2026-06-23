# Second Adoption Lifecycle Gate Plan

## Purpose

Plan the governed adoption of REAL-CAPTURED-TASK-002 backend output into README.md using the lifecycle advisory commands and dry-run gate evaluations. This plan does not execute adoption, modify README.md, or invoke any backend.

## Input Artifacts

| Artifact | Path |
|----------|------|
| Task contract | `docs/SECOND_REAL_CAPTURED_TASK_CONTRACT.md` |
| Capture preflight | `docs/SECOND_BACKEND_CAPTURE_PREFLIGHT.md` |
| Capture result | `docs/SECOND_BACKEND_CAPTURE_RESULT.md` |
| Output intake | `docs/SECOND_OUTPUT_INTAKE.md` |

## Captured Output Metadata

| Field | Value |
|-------|-------|
| Task ID | REAL-CAPTURED-TASK-002 |
| Lines | 22 |
| Bytes | 1599 |
| SHA256 | 73d1f43487f2a490a4971dcb79e5b98378e1c68d975fabfea958aa10c3e6a0f4 |
| Mutation | no_mutation_detected |
| Backend | claude-local / claude |
| Return code | 0 |

## Intake Outcome

- **Status:** reviewed
- **Outcome:** reviewable_adoption_candidate
- **Contract compliance:** 17/17 passed
- **Safety review:** 9/9 passed

## Future Adoption Target

**`README.md`**

The captured snippet documents the lifecycle command family and is most appropriate as a README section addition.

## Consolidated Gate Sequence

### Lifecycle State Finding

The lifecycle advisory commands report `current_state=closed` because the first backend-output-adoption lifecycle (77J-77V.1) completed successfully. All dry-run gate evaluations return `illegal_transition` from the `closed` state.

This is correct behavior: the lifecycle state model tracks the first lifecycle instance. The second adoption is a new, independent lifecycle instance.

### Dry-Run Gate Results

| Gate | Dry-Run Status | Reason |
|------|---------------|--------|
| adoption_preflight | illegal_transition | First lifecycle is closed |
| adoption_review | illegal_transition | First lifecycle is closed |
| adoption_approval | illegal_transition | First lifecycle is closed |
| adoption_execution_preflight | illegal_transition | First lifecycle is closed |
| adoption_execution | illegal_transition | First lifecycle is closed |
| approve-gate (dry-run) | illegal_state_for_approval | First lifecycle is closed |
| run-gate without --dry-run | dry_run_required (blocked) | Safety enforcement working correctly |

### Interpretation

The lifecycle advisory commands correctly enforce that the first lifecycle is closed. To proceed with the second adoption, the operator must work through direct phase commands (the same approach used for the first 77J-77V.1 lifecycle), since the advisory lifecycle model does not yet support multiple lifecycle instances.

A future enhancement (multi-lifecycle tracking) could allow `pcae lifecycle backend-output-adoption start-new` to reset state for a new lifecycle. This is not implemented and is not required for 81F-81G.

## Adoption Path for REAL-CAPTURED-TASK-002

Since the captured output is stdout-only (no repo mutation, no file to quarantine), the adoption path is simpler than the first lifecycle:

| Step | Phase | Action | Approval Required |
|------|-------|--------|-------------------|
| 1 | 81G | Adoption approval | Yes — operator must approve adopting the snippet into README.md |
| 2 | 81G or 81H | Adoption execution | Yes — write the snippet into README.md, stage, and commit |
| 3 | 81G or 81H | Push approval + execution | Yes — governed push of the adoption commit |
| 4 | 81G or 81H | Final verification | No — verify README.md on origin/main matches |

### Why Fewer Gates Than the First Lifecycle

The first lifecycle (77J-77V.1) required 15 phases because:
- Backend created a file directly in the repo (mutation detected).
- The file had to be quarantined, reviewed, and force-staged from gitignore.
- Hook bypass was needed and had to be reconciled.
- Push approval had to be refreshed after implementation commits.

The second lifecycle is simpler because:
- Backend produced stdout only (no mutation).
- Output was captured externally, not as a repo file.
- Adoption is a controlled README edit, not a force-staged quarantined file.
- No hook bypass should be needed (README.md is a normal tracked file).
- Staged-file-aware commands (79A-79C) are available if needed.

## Exact Future README Adoption Proposal

The captured backend output (after stripping the code fence wrapper) should be added to README.md as a new section. The content to adopt:

```
## Backend Output Adoption Lifecycle Commands

The `pcae lifecycle backend-output-adoption` command family provides governance and advisory
tooling for managing the backend output adoption lifecycle. These commands offer visibility
and control over the adoption process **without performing autonomous execution**.

### Commands

| Command | Purpose |
|---------|---------|
| `status` | Display the current lifecycle state, including phase, gate results, and authorization flags. |
| `next` | Show advisory next steps based on current state. Does not perform any action. |
| `run-gate --dry-run` | Evaluate gate criteria and report pass/fail without recording results or changing state. |
| `approve-gate` | Record gate approval. Approval is recorded as a governance decision only — it does not trigger execution. |
| `summary` | Generate a final summary report of the lifecycle process, including all recorded decisions and gate evaluations. |

### Design Constraints

- **No non-dry-run gate execution.** The `run-gate` command only supports `--dry-run`. Live gate execution is not implemented.
- **Approval is separate from execution.** `approve-gate` records that a gate has been approved but does not cause any downstream action to occur.
- **`execution_authorized=false` is the safety default.** Authorization for execution is never implicitly granted by lifecycle commands.
- **Governance/advisory tooling only.** These commands exist to provide lifecycle visibility, advisory guidance, dry-run evaluation, and approval recording. They are not autonomous execution tooling.
```

This content must NOT be written to README.md in Phase 81F. It is recorded here for the future adoption phase only.

## Blockers / Warnings

**Blockers:** none for the planned adoption path.

**Warnings:**
- Lifecycle advisory commands report `closed` for all gates because they track the first lifecycle instance only. This is expected and does not block the direct adoption path.
- The captured output is 22 lines (below the contract's 50-line guideline). The intake classified this as non-blocking.
- The output has a code fence wrapper that must be stripped during adoption.

## Safety Flags

| Flag | Value |
|------|-------|
| backend_invocation_performed | false (in this phase) |
| backend_reinvocation_performed | false |
| output_reviewed | true |
| adoption_planned | true |
| adoption_authorized | false |
| adoption_execution_authorized | false |
| adoption_performed | false |
| readme_modified | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |

## Recommended Next Phase

**81G — Second Adoption Approval**

81G should:
1. Grant explicit operator approval to adopt the captured snippet into README.md.
2. Perform the README.md modification (add the lifecycle commands section).
3. Commit the adoption.
4. Push via governed `pcae push`.
5. Verify final state.

This can be a single consolidated phase because:
- The output is already reviewed and classified (81E).
- The adoption target is clear (README.md).
- No quarantine, force-staging, or hook bypass is needed.
- Staged-file-aware commands are available if needed.
