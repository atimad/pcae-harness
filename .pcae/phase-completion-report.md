# Phase 149O.20L.7O.3V.2 Complete — Local-CLI Real-Runtime Dispatch Implementation Planning

**Verdict: PLANNING COMPLETE. FIRST IMPLEMENTATION SCOPED: AUTHORITY + PB
FOUNDATION ONLY. POL-005 REMAINS HARD DENY. HUMAN DECISION REQUIRED.**

Phase ID: `149O.20L.7O.3V.2`. Status: completed. Completeness: complete.

Baseline SHA: `3482d8cf92eeb352f94f68ca0f478924d69b442b`. Phase commits:
`71e5f24b`, `f3b5a9de`, `5ea523f4`.

v0.4.3 unchanged at `63580893b1de4782a694ab802ff7bdebdf29b0e6`. Runtime:
`Observed` / `observe` / `unavailable`, unchanged throughout.

All four verified contracts read directly this phase: RIHAC-001 v1.0
(unchanged, FROZEN), RIASC-001 v1.0 (unchanged, normative schema FROZEN),
PBRD-001 v1.1 (unchanged, FROZEN), RDGO-001 v2.0 (unchanged, FROZEN).

Cardinality recovered directly from primary contract text: 14 PBRD
request facts, 16 RIASC required fields (5-member subject), 11 RDGO
gates, 8 durable-before-effect items, 7 TOCTOU facts — all unchanged from
the 3V.1R.1 baseline, reconfirmed not recomputed.

Existing-code reuse audit: `new_invocation_id`/`new_attempt_id`/
`compute_idempotency_key`/`_write_create_only`
(`src/pcae/core/runtime_invocation.py`) already match the frozen
`inv-`/`att-` ID grammar and atomic create-only store pattern and are
directly reusable for the future authority/permission implementation.
`PermissionBrokerRequest` (`src/pcae/core/permission_broker_foundation.py`)
is a flat 12-field frozen dataclass with no extension point.

Key planning decisions: PB request architecture — **Option B** (new
optional nested `runtime_dispatch_context` field) selected over widening
the shared envelope (Option A) or a generic typed-payload refactor
(Option C). Approval-creation UX — **Option A** (internal API/test-only
first) selected over an explicit CLI (Option B) or Interactive Workflow
integration (Option C), to verify the frozen contracts without
prematurely expanding UX.

Both pre-existing 3S.2.1 MUST-FIX findings (malformed adapter result
crash in `simulate_invocation`/`runtime_adapter.py`; `RuntimeInvocationStore`
path-traversal gap in `_invocation_dir`/`_write_create_only`) were
recovered verbatim from source and confirmed **not reachable** by the
recommended first implementation phase; neither requires repair
before/within it.

Gate/durable-item/TOCTOU-fact classification (first-implementation-phase
vs later) was produced for all 11 gates, all 8 durable items, and all 7
TOCTOU facts (see the planning document's §6-8 tables). POL-005 staging:
the recommended first implementation phase adds the `runtime_dispatch`
action/request architecture and approval integration while POL-005
remains a hard, unconditional deny for every non-simulation request —
verified structurally against `ExecutionDisabledRule`/
`MissingHumanApprovalRule` source, which already apply generically to
`execution_class=adapter` with no `action_type` awareness in POL-005.

**LOCAL-CLI AUTHORITY/PERMISSION IMPLEMENTATION PLANNING: COMPLETE.**
**REAL-RUNTIME READY: NO.**

BLOCKING: 0. MUST-FIX: 0 new (2 pre-existing 3S.2.1 findings carried
forward unchanged, confirmed not reachable by the recommended next
phase). NON-BLOCKING: 0.

Production source modified: NO. Execution activated: NO. External runtime
invocation: NONE. Release unchanged. Article stopped. Private research
untouched.

Checks: `pcae health` healthy; `pcae check` passed; `pcae status
coherence` coherent; `pcae doctor task-memory` warnings limited to
pre-existing `tasks/DONE.md` sync debt; `pcae push check` clean at entry;
`pcae runtime inspect` not_implemented/Observed/observe/unavailable,
unchanged. Tests: 0 added; planning-only phase, no production or test
source changed.

Commits: `71e5f24b`, `f3b5a9de`, `5ea523f4`. Pushed: not_pushed.
`origin/main..HEAD`: 3 (pending push).

See
`docs/PHASE_149O_20L_7O_3V_2_LOCAL_CLI_REAL_RUNTIME_DISPATCH_IMPLEMENTATION_PLANNING.md`
for the complete implementation plan (70 sections, per the governing
task instructions), including all required matrices.

Recommended next phase: **Runtime Invocation Authority + PB Dispatch
Request Foundation Implementation** — Stages 1-7 of the plan's
implementation sequence (approval model/store/validator, attempt/
idempotency primitives, `runtime_dispatch` request/action vocabulary, PB
evaluation plumbing, while POL-005 remains hard deny), mandatorily
followed by a separate independent-verification phase before any Runtime
Enforcement work begins. Human decision required; not begun.
