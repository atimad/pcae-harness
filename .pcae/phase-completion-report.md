# Phase 149O.20L.7O.3V.2 Complete — Local-CLI Real-Runtime Dispatch Implementation Planning

**Verdict: PLANNING COMPLETE. FIRST IMPLEMENTATION SCOPED: AUTHORITY + PB
FOUNDATION ONLY. POL-005 REMAINS HARD DENY. HUMAN DECISION REQUIRED.**

Phase ID: `149O.20L.7O.3V.2`. Status: completed. Completeness: complete.

Verification baseline SHA: `9a645154fc35d41e6a1d7a95bc73245e89082ffe`.
3V.1R entry SHA: `6933f6e033ba89647889ad1a6343faf37609c26c`. 3V.1R final
SHA: `9a645154fc35d41e6a1d7a95bc73245e89082ffe`. Phase commits: `940a0210`,
`665ea5d4`.

v0.4.3 unchanged at `63580893b1de4782a694ab802ff7bdebdf29b0e6`. Runtime:
`Observed` / `observe` / `unavailable`, unchanged throughout.

Original 3V.1 BLOCKING 1 (RDGO gate order vs RPAC-REQ-042): **CLOSED**,
independently confirmed — RDGO-001 v2.0's gate table shows gate 3 (human
authority creation) strictly precedes gate 4 (static preflight), an exact
literal match to RPAC-REQ-042's own steps 3/4, re-read from RPAC-001
primary text. Original 3V.1 BLOCKING 2 (PBRD attempt/idempotency binding):
**CLOSED**, independently confirmed — PBRD-001 v1.1's fact table
independently recounted at exactly fourteen rows, `attempt_id` and
`idempotency_key` both required and PCAE-coordinator-owned.

PBRD-001 current ID/version: PBRD-001 v1.1, FROZEN. RDGO-001 current
ID/version: RDGO-001 v2.0, FROZEN. RIHAC-001 current version: v1.0,
UNCHANGED, VERIFIED. RIASC-001 current version: v1.0, UNCHANGED, NORMATIVE
SCHEMA VERIFIED.

`attempt_id` semantics: identifies exactly one concrete dispatch try under
one logical invocation; minted at RDGO gate 2 by the trusted invocation
coordinator from cryptographically strong random identity (`att-<32-hex>`);
immutable gate 2 through gate 11; never reusable once consumed.
`idempotency_key` semantics: identifies the logical dispatch operation's
canonical content (not one attempt); a SHA-256 digest over canonical
request content excluding timestamps/attempt-specific facts, minted at
gate 2. Distinction verdict: **SEMANTICALLY DISTINCT: YES**. Ownership:
both PCAE-coordinator-owned exclusively; caller/adapter/runtime influence
is a reject-at-construction security invariant.

Retry/replay result: no automatic retry in any class; every retry mints a
new `attempt_id` through a fresh gate-2 pass; `idempotency_key` stays
identical only when canonical content is unchanged; all eight tested
replay-threat scenarios (modified payload, different target, different
prompt, different repo/task, stale PB ALLOW, stale approval, new attempt
with stale approval, replay after uncertain dispatch) are independently
confirmed rejected by explicit contract text.

PB pre/post field count: 12 -> 14. Exact current 14-fact set:
`invocation_id`, `attempt_id`, `idempotency_key`, `repository_identity`,
`task_id`, `lifecycle_context`, `runtime_target_id`,
`adapter_descriptor_binding`, `prompt_hash`, `requested_capability`,
`transport_type`, `network_requirement`, `filesystem_scope_ref`,
`human_authority_binding`.

Gate pre/post count: 11 -> 11 (unchanged; gates 3/4 transposed only).
Exact current gate order: 1 Prompt preparation; 2 Explicit target
selection and request construction; 3 Human authority creation; 4 Static
preflight; 5 Approval validation; 6 Permission Broker; 7 Runtime
Enforcement; 8 Process containment and live preflight; 9 Durable
pre-dispatch record; 10 Adapter dispatch (first external effect); 11
Result capture and intake.

RPAC-REQ-042 verdict: **CONSISTENT**.

Durable pre/post count: 8 -> 8 (unchanged; item 1 enriched to
unconditionally bind all three identifiers). Exact current durable set:
(1) invocation identity — `invocation_id`/`attempt_id`/`idempotency_key`;
(2) repository/task binding; (3) target binding; (4) prompt binding; (5)
approval binding; (6) PB binding; (7) Runtime Enforcement binding; (8)
dispatch intent/state.

TOCTOU pre/post count: 7 -> 7 (unchanged). Exact current TOCTOU set: HEAD;
task state/contract; prompt; runtime target; adapter configuration;
adapter executable identity; policy version. `attempt_id`/`idempotency_key`
correctly excluded as immutable identity, not drift-subject state.

RIASC required-field count: 16 (unchanged). Approval-subject count: 5
(unchanged): `invocation_id`, `runtime_target_id`, `prompt_hash`,
`repository_identity`, `task_id`.

Cross-contract identifier verdict: CONSISTENT across RPAC, RIHAC, RIASC,
PBRD v1.1, RDGO v2.0 (10-row matrix independently reconstructed).
Terminology verdict: CONSISTENT; no unqualified ambiguous overload found.
Security/replay verdict: all tested invariants hold (DENY beats ALLOW;
missing approval blocks dispatch; RE DENY blocks dispatch; runtime
unavailable blocks dispatch; identifier collisions rejected; no automatic
retry).

POL-004/HUMAN_REVIEW result: valid approval satisfies
`MissingHumanApprovalRule` specifically; other HUMAN_REVIEW-producing
policies remain independent; no global suppression claim exists — unchanged
by the repair. POL-005: UNCHANGED. Dry path: UNCHANGED (read-only
cross-check of `runtime_dry_consumption.py`/`runtime_adapter.py` confirms
the existing shipped mock/dry gate order already matches RPAC-REQ-042 and
carries no `attempt_id`/`idempotency_key` in its PB request, consistent
with PBRD-001 §13).

Existing PB action compatibility: no other action inherits
`runtime_dispatch` fields; confirmed unaffected. Two existing 3S.2.1
MUST-FIX findings (invocation-store path confinement; malformed-result
handling): unchanged, unresolved, explicit deferred-real-runtime
prerequisites — not repaired here, not newly discovered.

Runtime inspect limitation: `TRUTHFUL_WITH_LIMITATION`, unchanged.
API/network: `NOT FROZEN` / `UNRESOLVED`, unchanged.

Version/supersession result: PBRD-001 v1.0 -> v1.1 (MINOR, additive,
correctly justified); RDGO-001 v1.0 -> v2.0 (MAJOR, reordering, correctly
justified); RIHAC-001/RIASC-001 v1.0 unchanged, correctly so — all
independently verified against each contract's own versioning rule.

Normative-vs-implemented result: production implementation remains mostly
NO across approval schema/store/validator, `runtime_dispatch` PB action,
POL-005 evolution, RE projection, Shell Gate, and real adapter; the
`inv-`/`att-` identifier conventions and idempotency-digest exclusion rule
are already precedented in shipped mock/dry code (`runtime_invocation.py`),
which is corroborating evidence, not an implementation of the future
`runtime_dispatch` action.

**LOCAL-CLI AUTHORITY/PERMISSION IMPLEMENTATION READY: YES.**
**REAL-RUNTIME READY: NO.**

BLOCKING: 0. MUST-FIX: 0 new (2 pre-existing 3S.2.1 findings carried
forward unchanged). NON-BLOCKING: 1.

Production source modified: NO. Execution activated: NO. External runtime
invocation: NONE. Release unchanged. Article stopped. Private research
untouched.

Checks: `pcae health` healthy; `pcae check` passed; `pcae status coherence`
coherent; `pcae doctor task-memory` warnings limited to pre-existing
`tasks/DONE.md` sync debt; `pcae push check` clean; `pcae runtime inspect`
not_implemented/Observed/observe/unavailable, unchanged. Tests: 51 passed,
0 failed, in `tests/test_phase_149o_20l_7o_3v_1r_1_contract_verification.py`
(fresh module, not a rerun of 3V.1R's own tests).

Commits: `940a0210`, `665ea5d4`. Pushed: pushed. `origin/main..HEAD`: 0.

See
`docs/PHASE_149O_20L_7O_3V_1R_1_INDEPENDENT_VERIFICATION_REPAIRED_LOCAL_CLI_RUNTIME_DISPATCH_AUTHORITY_PERMISSION_CONTRACTS.md`
for the complete independent-verification analysis, matrices, and
cardinality reconciliation.

Recommended next phase: exactly **149O.20L.7O.3V.2 — Local-CLI
Real-Runtime Dispatch Implementation Planning**. Human decision required;
not begun.
