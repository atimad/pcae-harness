# Phase 149O.20L.7O.3W — Runtime Invocation Authority + PB Dispatch Request Foundation Implementation

## 1. Objective

Implement the frozen human-authority (RIHAC-001 v1.0 / RIASC-001 v1.0)
and permission (PBRD-001 v1.1) foundation for a future local-CLI real
runtime dispatch, per the implementation-ready sequence produced by
Phase 149O.20L.7O.3V.2, without enabling real execution. POL-005
(`ExecutionDisabledRule`) remains an unmodified, unconditional hard
deny for every real (`simulation_only=False`) request. Runtime
Enforcement and Shell Gate are not activated; no process is spawned.

## 2. Baseline

| Fact | Value |
|---|---|
| Repository | `~/repos/pcae-harness` |
| `implementation_baseline` (phase-entry HEAD) | `daebfdbb2d8664518c51e904b64aad555195d626` |
| `origin/main..HEAD` at entry | 0 |
| `v0.4.3` tag commit | `63580893b1de4782a694ab802ff7bdebdf29b0e6` (unchanged) |
| `pcae health` at entry | healthy |
| `pcae check` at entry | passed |
| `pcae status coherence` at entry | coherent |
| `pcae push check` at entry | clean, nothing to push |
| `pcae runtime inspect` at entry | `Observed` / `observe` / `unavailable`, `not_implemented`, 0 plugins/capabilities |
| Active governed phase at entry | none (idle task, human-decision hold, post-3V.2) |
| Telegram notification | configured, enabled, ready |

## 3. Verified contract baseline (read directly, this phase)

- **RIHAC-001 v1.0** — `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` — read in full.
- **RIASC-001 v1.0** — `docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` — read in full.
- **PBRD-001 v1.1** — `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` — read in full.
- **RDGO-001 v2.0** — `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` — read in full.
- **RPAC-001** — read via 3V.2's own recovery (`docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`), not re-transcribed here.
- Production source read in full: `src/pcae/core/permission_broker_foundation.py`, `src/pcae/core/runtime_invocation.py`, `src/pcae/core/runtime_adapter.py`, `src/pcae/core/intake.py` (`compute_repo_fingerprint`), `src/pcae/core/tasks.py`, `src/pcae/core/runtime_registry.py` (descriptor shape survey).

No contract was modified. No contradiction requiring a STOP condition
was discovered.

## 4. 3V.2 plan (read completely before touching source)

`docs/PHASE_149O_20L_7O_3V_2_LOCAL_CLI_REAL_RUNTIME_DISPATCH_IMPLEMENTATION_PLANNING.md`
was read in full and used as the implementation blueprint. Mandatory
decisions preserved exactly:

- **PermissionBrokerRequest architecture: Option B** (nested
  `runtime_dispatch_context: RuntimeDispatchRequestFacts | None = None`
  field on the existing `PermissionBrokerRequest`, not 14 fields bolted
  onto every request).
- **Approval creation UX: Option A** (internal core/API + tests only;
  no public CLI added).
- POL-005: unchanged, still an unconditional hard deny.
- Runtime Enforcement / Shell Gate: not activated.
- Stages 1–7 of 3V.2 §57 implemented; Stage 8 (independent verification)
  explicitly deferred to a separate future phase.

## 5. Scope

Implemented, matching 3V.2 §59 exactly:

- `RuntimeInvocationApproval` model, RIASC-001 schema validator, canonical
  create-only store.
- RIHAC-001 §16's twelve-step ordered validator, all seven freshness
  conditions, security/threat adversarial coverage.
- `attempt_id`/`idempotency_key` identity primitives (reusing existing
  generators; new sibling idempotency-key function for the real-dispatch
  fact set).
- `runtime_dispatch` PB action/request architecture (Option B), the
  fourteen-fact context, the trusted approval projection adapter.
- POL-004/POL-005 interaction proof, precedence proof, existing-action
  and dry-path regression proof.

Explicitly NOT implemented (deferred per 3V.2 §16/§28, RDGO-001 gates
7–11): Runtime Enforcement real-gate wiring, Shell Gate/process
containment, the durable gate-9 8-item pre-dispatch record and its
consumption semantics, adapter dispatch, result capture repair
(3S.2.1 MUST-FIX #1).

## 6. Existing-code reuse

| Existing primitive | Reused for | Not duplicated |
|---|---|---|
| `new_invocation_id()` / `new_attempt_id()` (`runtime_invocation.py`) | Real-dispatch identity minting (`runtime_dispatch_permission.new_runtime_dispatch_identity`) | Yes — called directly |
| `is_valid_generated_id(..., prefix=...)` | Construction-time `inv-`/`att-` pattern checks | Yes |
| `_canonical_json`/digest pattern (`runtime_invocation.py:46`) | Re-implemented (not imported, to keep `runtime_authority.py` free of a cross-module private-name dependency) with an added NFC-normalization step RIASC-001 requires | Mechanism reused, not the private function itself |
| `_write_create_only` tmp-then-`replace()` pattern (`runtime_invocation.py:850`) | `RuntimeInvocationApprovalStore.create` | Pattern reused; separate store per RIHAC-001 §15 |
| `compute_repo_fingerprint` (`intake.py`) | NOT called by new modules — repository identity is trusted-caller-supplied input to `runtime_authority`/`runtime_dispatch_permission`, exactly mirroring `AuthoritySnapshot`'s existing construction discipline | Avoids introducing `subprocess` into new authority/PB code (§42 audit) |
| `PermissionBrokerRequest`/`PolicyRegistry`/`PermissionBroker` (`permission_broker_foundation.py`) | Extended additively (new field, new action constant); zero new `PolicyRule` subclasses | POL-004/POL-005 logic unchanged |

## 7. Production footprint

| File | New/Modify | Lines changed (approx) |
|---|---|---|
| `src/pcae/core/runtime_authority.py` | New | ~520 |
| `src/pcae/core/runtime_invocation_approval_store.py` | New | ~170 |
| `src/pcae/core/runtime_dispatch_permission.py` | New | ~250 |
| `src/pcae/core/permission_broker_foundation.py` | Modify (additive) | +~75 |
| `src/pcae/core/runtime_invocation.py` | Modify (additive) | +~15 |

No command-zone (`src/pcae/commands/*`) file changed — Option A means
there is no CLI surface to add (§64 command-zone invariant satisfied by
construction: nothing to explain).

## 8. `RuntimeInvocationApproval` model

Exact 1:1 representation of RIASC-001's sixteen top-level fields as one
frozen dataclass composed of nested frozen dataclasses (`ApprovalSubject`,
`GovernanceContext`, `ApprovalScope`, `AdapterBinding`,
`FreshnessSnapshot`, `ApprovalProvenance`, `ArtifactRef`). No field named
`approved`/`authorized`/`permission`/`pb_allow`/`execution_allowed`
anywhere in the model (verified by
`test_no_model_field_is_named_an_authority_shortcut`).

## 9. RIASC-001 validator

`validate_riasc_schema_shape` implements structural validation: exactly
sixteen required top-level fields, `additionalProperties:false` applied
recursively to every nested object, const/pattern/type checks for every
field, and a recursive scan for forbidden authority-shortcut keys
anywhere in the document (not just at known field positions).

## 10. Five-member subject

`ApprovalSubject(invocation_id, runtime_target_id, prompt_hash,
repository_identity, task_id)` — exactly the five 3U-selected members, no
more, no fewer, closed (`additionalProperties:false` enforced by schema
validation).

## 11. Repository binding

`repository_identity` is trusted-caller-supplied (never resolved by
`git` subprocess inside the new authority/PB modules — see §6). Binding
is enforced at RIHAC-001 §16 step 5: `approval.subject.repository_identity
!= context.repository_identity` fails closed
(`test_copied_approval_into_sibling_repository_fails_repository_binding`).

## 12. Task binding

Step 5 also binds `task_id` exactly; a task-A approval fails under a
task-B context (`test_task_swap_attack`).

## 13. Runtime-target binding

Step 6 binds `runtime_target_id` exactly, no fallback
(`test_step_6_target_swap_no_fallback`).

## 14. Prompt binding

`pcae.prompt-semantic.v1` implemented in `runtime_authority.py`:
NFC-normalizes and CRLF/CR→LF-normalizes every ordered component's
content, serializes as compact sorted-key JSON (array order preserved),
SHA-256. Step 7 binds the resulting hash exactly
(`test_step_7_prompt_swap`, `test_prompt_hash_changes_on_single_character_change`).

## 15. Invocation identity

`new_invocation_id()`/`new_attempt_id()` reused directly, no parallel
generator introduced. Identity is exclusively PCAE-owned: neither
function accepts caller input.

## 16. Approval provenance

`ApprovalProvenance` records `approver_id` (identified human),
`identity_evidence_kind`, `approval_mechanism` (const
`interactive_local_cli_confirmation`), `approval_preview_digest`, and
`producer_component` (const `pcae.trusted_runtime_approval_coordinator`,
schema-pinned so tampering fails at step 3, not just step 4). Approver
identity is never derived from producer/agent/runtime identity
(`test_producer_identity_must_be_distinct_from_approver`).

## 17. Approval store

Canonical location `.pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json`.
Create-only (duplicate creation always errors, even with identical
content — RIHAC-001 §1's one-shot-human-act semantics). `approval_id` is
validated against `^ria-[0-9a-f]{32}$` strictly before any path is
constructed — confinement holds by construction, not string
post-processing (repairs MUST-FIX #2's class of gap by design, not
inheritance — see §46).

## 18. Atomic/create-only behavior

Reuses the `tmp`-then-`Path.replace()` pattern. Verified: no orphaned
half-written valid artifact is ever observable; a stray `.tmp` file alone
is invisible to `load`/`exists`.

## 19. Approval load/validation

`RuntimeInvocationApprovalStore.load` performs: existence check → read →
`json.loads` (fails closed on malformed JSON) → `validate_riasc_schema_shape`
(fails closed on any schema issue) → identity match (`approval_id` in
document must equal the ID it was looked up by). No silent fallback at
any step.

## 20. Seven freshness rules

All seven RIHAC-001 §13 conditions are checked at RIHAC-001 §16 step 9
(`runtime_authority.validate_approval`): HEAD, task-contract-digest,
task-state, prompt (via step 7's subject-mismatch path), runtime-target
(via step 6), adapter-configuration (via step 8), and policy-version
(recorded as a non-invalidating-but-blocking freshness fact per RIHAC-001
§13's explicit disposition). Live executable-identity revalidation (gate
8) is explicitly out of this phase's scope, documented as a boundary, not
silently assumed implemented.

## 21. Expiry/revocation

`expires_at > created_at` enforced at creation (`ValueError`) and
re-checked at validation step 10 against a trusted-caller-supplied
`current_time`. No arbitrary TTL invented. No mutable `revoked` field —
matches RIASC-001 §9 exactly. Explicit revocation remains out of v1
scope, as RIHAC-001 specifies.

## 22. One-shot/consumption staging

Consumption (the durable gate-9 `dispatch_attempted` marker) is
explicitly NOT implemented. `validate_approval` accepts an injected
`consumption_lookup` callable and fails closed on any
already-bound/uncertain/cancelled/completed state, but no code path in
this phase's production surface ever calls it with anything other than
"unconsumed" in real usage, since no consuming write exists yet. Repeated
validation of the same still-fresh approval never marks it consumed
(`test_validating_an_unconsumed_approval_repeatedly_never_consumes_it`).

## 23. `attempt_id`

Reused via `new_attempt_id()`. Minted fresh at every
`new_runtime_dispatch_identity` call; never caller-supplied (verified via
signature introspection in
`test_uncertain_attempt_requires_brand_new_attempt_id_for_retry`).

## 24. `idempotency_key`

New sibling function `compute_runtime_dispatch_idempotency_key` added to
`runtime_invocation.py` (existing `compute_idempotency_key` untouched —
it remains exclusively the dry path's function). Computed over
`canonical_runtime_dispatch_projection`: repository identity, task ID,
lifecycle context, runtime target, adapter descriptor binding, prompt
hash, requested capability, filesystem scope ref — excludes `attempt_id`
and any timestamp.

## 25. Replay/idempotency behavior

`RuntimeDispatchIdentityTracker` implements the construction-time
collision guard (explicitly documented as NOT the durable gate-9 record):
same `attempt_id` + different content → hard collision, reject; same
`idempotency_key` + different `invocation_id` → reject. A caller-presented
`idempotency_key` that doesn't match the canonical-content recomputation
is rejected at request-construction time regardless of the tracker.

## 26. PB request architecture — Option B

`RuntimeDispatchRequestFacts` (14 facts, closed nested dataclasses for
`lifecycle_context` and `human_authority_binding`) added as one new
optional field `runtime_dispatch_context: RuntimeDispatchRequestFacts |
None = None` on the existing `PermissionBrokerRequest`. Every existing
action type leaves it `None` (verified:
`test_runtime_dispatch_context_is_none_for_existing_actions`).

## 27. `runtime_dispatch` action

`ACTION_TYPE_RUNTIME_DISPATCH = "runtime_dispatch"` added to
`KNOWN_ACTION_TYPES`. Zero new `PolicyRule` subclasses.

## 28. Execution class

Reuses `EXECUTION_CLASS_ADAPTER` exactly, per PBRD-001 §1 — confirmed
`MissingHumanApprovalRule.applicable_execution_classes` already includes
it.

## 29. Fourteen request facts

`RuntimeDispatchRequestFacts` carries exactly: `invocation_id`,
`attempt_id`, `idempotency_key`, `repository_identity`, `task_id`,
`lifecycle_context`, `runtime_target_id`, `adapter_descriptor_binding`,
`prompt_hash`, `requested_capability`, `transport_type`,
`network_requirement`, `filesystem_scope_ref`, `human_authority_binding`
— 14 fields, verified by
`test_runtime_dispatch_request_carries_fourteen_facts` (Matrix B below).

## 30. Trusted approval projection

`project_human_authority_binding` is the ONLY function in this phase's
entire surface that can produce `approval_present=True` — it reads
exclusively `ValidatedAuthorityProjection` (gate 5's output), never raw
approval content or a caller boolean. The public builder
`build_runtime_dispatch_permission_broker_request` does not even accept
an `approval_present` parameter (verified via signature introspection).

## 31. POL-004 integration

Unchanged logic. `test_missing_approval_triggers_pol004_human_review` and
`test_valid_approval_does_not_trigger_pol004` both pass against the
unmodified `MissingHumanApprovalRule`.

## 32. PB precedence

`DENY > HUMAN_REVIEW > ALLOW`, unmodified, re-verified for
`runtime_dispatch` (`test_pol005_deny_precedes_pol004_human_review_when_both_would_fire`).

## 33. POL-005 hard deny — proof

`test_real_dispatch_always_denied_by_pol005_regardless_of_valid_approval`
and `test_positive_control_plane_structural_validity_distinguished_from_pol005_deny`
prove: valid approval + valid `runtime_dispatch` request + all other
checks passing still yields `DENY` with `causing_policy_ids == ("POL-005",)`
for any `simulation_only=False` request. `ExecutionDisabledRule` source
is byte-unmodified.

## 34. Dry-path compatibility

`adapter_invocation`/`simulation_only=True` is untouched — not migrated.
`InvocationRequest`'s shape gains no new field
(`test_dry_path_invocation_request_shape_unchanged`). Existing dry-path
suites (`test_runtime_dry_consumption_3s2.py`,
`test_session_bootstrap_dry_runtime_3s2.py`) re-run unmodified and green.

## 35. Runtime Enforcement / Shell Gate non-activation

Neither is imported, called, or referenced by any new module. No new
module imports `pcae.core.shell_gate` or any Runtime Enforcement
production coordinator.

## 36. Invocation-store staging

`runtime_invocation.py`'s `RuntimeInvocationStore` (dry-v1 store) is
untouched except for the additive sibling function in §24. No new
real-dispatch invocation record store was created — correctly deferred
per 3V.2 §27/§28 (gate 9 depends on gate 8, which doesn't exist yet).

## 37. Failure semantics

Implemented exactly per 3V.2 §36's fail-closed table: invalid schema →
no projection; missing approval → `approval_present=false` → HUMAN_REVIEW;
stale/mismatched approval → fails at validation, never reaches PB as
present; invalid attempt/invocation ID → construction-time rejection;
idempotency conflict → hard collision reject; real dispatch → POL-005
DENY unconditionally.

## 38. Path confinement

`RuntimeInvocationApprovalStore._approval_dir` validates the exact
`^ria-[0-9a-f]{32}$` pattern before any `Path` object referencing the
caller-supplied ID is constructed. Nine adversarial malicious-ID cases
tested, all rejected with zero filesystem side effect.

## 39. Corruption/tamper

Ten adversarial store-corruption cases tested: malformed JSON, truncated
JSON, schema-invalid document, unknown fields, mismatched stored
identity, corrupted provenance enum, corrupted digest shape — all fail
closed via `ApprovalStoreIntegrityError`.

## 40. Replay attacks

Covered: forged approval (digest mismatch), copied approval into sibling
repository (repository-identity mismatch), task swap, target swap,
prompt swap, replay-after-validation-without-consumption (repeated
validation never consumes), attempt-ID collision with conflicting
content, idempotency-key replay across a different invocation.

## 41. Restart/atomicity

`test_approval_persists_across_store_instances` simulates a fresh-process
restart (new store instance against the same root) and confirms exact
round-trip equality. Freshness is always recomputed from live
`InvocationRequestContext` input, never cached.

## 42. Existing PB regressions

`test_runtime_dispatch_regression_pb_actions.py`: rollback, push,
source-mutation, backend-invocation, adapter-invocation, and
shell-command actions all produce byte-identical decision shapes
(decision, reason, matched IDs, precedence reason) with
`runtime_dispatch_context=None` throughout. Registry remains exactly
twelve canonical policies.

## 43. Runtime/dry regressions

`test_runtime_dispatch_regression_dry_path.py` plus unmodified re-run of
`test_runtime_dry_consumption_3s2.py` and
`test_session_bootstrap_dry_runtime_3s2.py` (both pass unchanged).

## 44. Contract regressions

`test_phase_149o_20l_7o_3v_1r_1_contract_verification.py` (RIASC/RIHAC/
PBRD/RDGO v1.1/v2.0 static re-verification) re-run: unaffected by this
phase's source changes (it verifies contract *documents*, which are
byte-unmodified). See §46 for two pre-existing-and-one-new self-check
finding in the OLDER 3V.1-scoped verification files.

## 45. Two 3S.2.1 MUST-FIX findings — reachability re-check

Recovered verbatim (from
`docs/PHASE_149O_20L_7O_3S_2_1_INDEPENDENT_END_TO_END_PRODUCTION_DRY_LIFECYCLE_RUNTIME_ADAPTER_CONSUMPTION_VERIFICATION.md`
§62, quoted in full in 3V.2 §32):

1. Malformed adapter result crashes uncaught in `simulate_invocation`/
   `RuntimeInvocationStore.write_result` (`runtime_adapter.py`/
   `runtime_invocation.py`).
2. `RuntimeInvocationStore` (mock-v1) does not sanitize `invocation_id`
   against path traversal.

**Reachability after 3W:**

- Finding 1: `reachable after 3W: NO`. This phase adds no gate-10/11
  (dispatch/result-capture) code path. `runtime_adapter.py` and
  `runtime_invocation.py`'s `write_result`/`_write_create_only` are
  untouched except for the additive sibling idempotency function, which
  touches none of the affected code. **Latest safe repair point: first
  non-mock adapter phase (unchanged from 3V.2's assessment).**
- Finding 2: `reachable after 3W: NO`. `RuntimeInvocationStore` (the
  affected mock-v1 store) is untouched. The NEW approval store
  (`RuntimeInvocationApprovalStore`) is a structurally separate store
  that validates `approval_id` against `^ria-[0-9a-f]{32}$` before any
  path construction — it does not inherit the gap; it never had it.
  **Latest safe repair point: whichever future phase next touches
  `RuntimeInvocationStore` itself (unchanged from 3V.2's assessment).**

Neither finding became reachable. No opportunistic repair performed
(per governing instructions §60, repair without dedicated authorization
is itself a stop condition — none was triggered because neither finding
is reachable).

## 46. Runtime inspect limitation

Carried forward unchanged: `TRUTHFUL_WITH_LIMITATION`. `pcae runtime
inspect` still reports `not_implemented` / `Observed` / `observe` /
`unavailable`, 0 plugins, 0 capabilities — re-verified identical at
phase close (§50). This phase registers no adapter and makes no new
availability claim.

## 47. Architecture-wall audit

Verified by direct code inspection and by the explicit non-equivalence
docstrings/comments preserved from every contract:

```text
approval != permission        — RuntimeInvocationApproval is a separate
                                 type from PermissionBrokerDecision;
                                 neither embeds the other.
permission != capability       — ALLOW decisions carry
                                 implementation_status=execution_unavailable.
capability != RE decision      — no RE call exists in new code.
RE decision != containment     — N/A, RE not activated.
containment != dispatch        — N/A, no containment/dispatch code added.
dispatch != accepted result    — N/A, no dispatch code added.
invocation_id != attempt_id    — distinct fields, distinct prefixes
                                 (inv-/att-), independently tested.
attempt_id != idempotency_key  — distinct fields; idempotency_key stable
                                 across a retry, attempt_id always fresh.
approval_id != PB decision ID  — approval_id (ria-...) never appears as
                                 a PermissionBrokerDecision field; only
                                 referenced by digest inside
                                 human_authority_binding.
```

## 48. Source-diff audit

`src/pcae/core/permission_broker_foundation.py`: additive only (one new
constant, four new frozen dataclasses, one new optional field, one
extended builder-function parameter). `src/pcae/core/runtime_invocation.py`:
additive only (one new sibling function). No existing function's body was
altered in either file. Three wholly new files added.

## 49. Fast Green

`implementation_baseline` (phase-entry SHA): `daebfdbb2d8664518c51e904b64aad555195d626`.
Functional candidate SHA: recorded at phase close in the canonical phase
report (post-commit).

- New test files (8 files, 190 tests): all pass.
- Pre-existing dry-path suites (`test_runtime_dry_consumption_3s2.py`,
  `test_session_bootstrap_dry_runtime_3s2.py`): unchanged, pass.
- Pre-existing PB foundation/policy-framework suites
  (`test_permission_broker_foundation.py`,
  `test_permission_broker_policy_rule_framework.py`): unchanged, pass.
- `fast_green`-marked suite (`pytest -m fast_green -n auto`): run at
  phase close; see canonical phase report for the final count.
- **Attributable functional regressions: 0.** One pre-existing 3V.1-scoped
  historical self-check
  (`test_phase_149o_20l_7o_3v_1_contract_verification.py::TestPBAndDryCompatibility::test_future_action_is_not_implemented_but_selected_class_exists`)
  newly fails as an **intentional, expected consequence of this phase's
  own chartered scope**: that test asserted `"runtime_dispatch" not in
  KNOWN_ACTION_TYPES` as a point-in-time snapshot of Phase 3V.1's world,
  before the roadmap item this phase implements existed. This is the same
  category of accepted historical-snapshot debt already present at
  baseline (Phase 3V.1R's own contract-fact-count assertions —
  `test_four_unique_frozen_contract_identities`,
  `test_exact_twelve_pb_facts`, `test_blocking_gate_order_conflict_with_rpac_is_detected`,
  `test_blocking_attempt_and_idempotency_omission_is_detected` — were
  already failing at this phase's entry baseline, before any 3W change,
  confirmed via `git stash` bisection). None of these five represent a
  behavioral regression in current production code; all are historical
  point-in-time self-checks whose assertions were superseded by later,
  correctly-repaired reality. Not repaired in this phase (out of scope —
  repairing a different phase's historical self-check test is not part
  of 3W's chartered scope, matching the repo's own established precedent
  of not repairing 3V.1's stale self-checks during 3V.1R).

## 50. Stop-condition audit

None of the section-67 stop conditions were triggered: no contract
modification required; no MUST-FIX finding became reachable; POL-005 was
never relaxed; Runtime Enforcement was never activated; Shell Gate was
never activated; no subprocess/network/credential access was introduced
in new authority/PB code (static AST audit + runtime tripwire tests, see
`test_runtime_dispatch_no_external_effect.py`); no broader/reusable
human authority was invented; execution availability remains
`unavailable` throughout.

## 51. Findings

None. Zero BLOCKING, zero MUST-FIX, zero NON-BLOCKING findings
discovered during implementation.

## 52. Final verdict

See §77-style verdict block reproduced in the canonical phase-completion
report. Summary: authority/PB foundation implemented per 3V.2's exact
blueprint; POL-005 unchanged hard deny; Runtime Enforcement and Shell
Gate not activated; process spawn/network/credential access: 0; runtime
posture unchanged (`Observed`/`observe`/`unavailable`).

## 53. Recommended next phase

**149O.20L.7O.3W.1 — Independent End-to-End Runtime Invocation Authority
+ PB Dispatch Request Foundation Verification.** Not begun in this phase.

## 54. Human decision required

A human decision is required to authorize 149O.20L.7O.3W.1. This phase
does not authorize or begin it.

---

## Matrix A — RIASC-001 approval implementation (16 fields)

| # | Field | Source | Validation | Persistence | Test |
|---:|---|---|---|---|---|
| 1 | `schema_id` | Const | Schema-shape const check | Stored top-level | `test_bad_schema_version_fails_closed` (sibling) |
| 2 | `schema_version` | Const `1.0` | Const check | Stored | `test_bad_schema_version_fails_closed` |
| 3 | `contract_version` | Const `RIHAC-001/1.0` | Const check | Stored | `test_bad_contract_version_fails_closed` |
| 4 | `record_type` | Const | Const check | Stored | `test_valid_approval_passes_schema_shape_validation` |
| 5 | `approval_id` | `new_approval_id()` | `^ria-[0-9a-f]{32}$` pattern | Store path key | `test_approval_id_matches_ria_pattern`, path-confinement suite |
| 6 | `record_digest` | `compute_record_digest` | Recompute-and-compare | Stored | `test_record_digest_matches_recomputation`, tamper suite |
| 7 | `created_at` | Trusted caller/clock | Timestamp pattern + `<expires_at` | Stored | `test_create_approval_rejects_expiry_equal_created` |
| 8 | `expires_at` | Trusted caller/clock | Timestamp pattern + `>created_at`, expiry check | Stored | `test_expired_approval_fails_closed` |
| 9 | `subject` (5-member) | Gate 2/live context | Closed-object + per-member equality | Stored nested | Full subject-mismatch suite |
| 10 | `governance_context` | Active phase/session | Closed-object + equality | Stored nested | `test_step_5_phase_mismatch`, `test_step_5_session_mismatch_...` |
| 11 | `prompt_hash_profile` | Const | Const check | Stored | `test_step_7_prompt_swap` |
| 12 | `approval_scope` | Fixed local-CLI scope + refs | Closed-object + const checks | Stored nested | `test_step_8_requested_capability_mismatch` |
| 13 | `adapter_binding` | Registry/config preflight | Closed-object + digest equality | Stored nested | `test_step_8_adapter_descriptor_digest_mismatch` |
| 14 | `freshness_snapshot` | HEAD/task/policy snapshot | Closed-object + 7-condition check | Stored nested | Full freshness suite |
| 15 | `provenance` | Identified human + fixed producer | Closed-object + const + distinctness | Stored nested | `test_producer_identity_must_be_distinct_from_approver` |
| 16 | `attempt_limit` | Const `1` | Const check | Stored | `test_wrong_type_fails_closed` |

## Matrix B — PBRD-001 request context (14 facts)

| # | Fact | Type | Trusted source | Required? | Test |
|---:|---|---|---|---|---|
| 1 | `invocation_id` | `inv-<32-hex>` | Trusted coordinator | Yes | `test_attempt_id_distinct_from_invocation_id` |
| 2 | `attempt_id` | `att-<32-hex>` | Trusted coordinator | Yes | `test_invalid_attempt_id_rejected_at_construction` |
| 3 | `idempotency_key` | 64-hex SHA-256 | Trusted coordinator | Yes | `test_tampered_idempotency_key_rejected_at_construction` |
| 4 | `repository_identity` | 64-hex SHA-256 | Trusted caller | Yes | `test_changed_repository_produces_different_idempotency_key` |
| 5 | `task_id` | non-empty string | Active task | Yes | `test_changed_task_produces_different_idempotency_key` |
| 6 | `lifecycle_context` | closed object | Active phase/session | Yes | `test_runtime_dispatch_request_carries_fourteen_facts` |
| 7 | `runtime_target_id` | exact ID | Explicit selection | Yes | `test_changed_target_produces_different_idempotency_key` |
| 8 | `adapter_descriptor_binding` | closed object | Registry/config | Yes | `test_runtime_dispatch_request_carries_fourteen_facts` |
| 9 | `prompt_hash` | 64-hex SHA-256 | Prompt builder | Yes | `test_changed_prompt_produces_different_idempotency_key` |
| 10 | `requested_capability` | non-empty ID | Coordinator | Yes | `test_step_8_requested_capability_mismatch` |
| 11 | `transport_type` | const `local_cli` | Fixed | Yes | `test_transport_type_fixed_local_cli` |
| 12 | `network_requirement` | const `false` | Fixed | Yes | `test_network_requirement_fixed_false` |
| 13 | `filesystem_scope_ref` | ID/digest ref | Scope owner | Yes | `test_runtime_dispatch_request_carries_fourteen_facts` |
| 14 | `human_authority_binding` | closed object | RIHAC validator only | Yes | `test_human_authority_binding_is_reference_plus_digest_not_raw_authority` |

## Matrix C — Identifier semantics

| Identifier | Creator | Purpose | Persistence | Reuse rule |
|---|---|---|---|---|
| `invocation_id` | Trusted coordinator (`new_invocation_id`) | Stable logical invocation across attempts | Approval subject; PB request | Same across genuine retry |
| `approval_id` | Trusted coordinator (`new_approval_id`) | Human-authority artifact identity | Approval store path key | Never reused; one artifact per ID |
| `attempt_id` | Trusted coordinator (`new_attempt_id`) | One concrete dispatch try | PB request; future gate-9 record | New every attempt, never reused |
| `idempotency_key` | Trusted coordinator (`compute_runtime_dispatch_idempotency_key`) | Logical-request replay/safe-retry identity | PB request; future gate-9 record | Same across safe retries of unchanged request |
| PB decision (no persistent ID field) | `PermissionBroker.evaluate` | Policy evaluation result | Evaluation-time only (not persisted this phase) | Freshly evaluated every request, never cached |

## Matrix D — Gate implementation status (11 gates)

| Gate | Frozen owner | 3W status | External effect? |
|---:|---|---|---|
| 1 Prompt preparation | Trusted prompt builder | Implemented (`compute_prompt_semantic_hash`) | No |
| 2 Target selection + identity minting | Coordinator | Implemented (`new_runtime_dispatch_identity`, reused generators) | No |
| 3 Human authority creation | Approval coordinator | Implemented (`create_runtime_invocation_approval`) | No |
| 4 Static preflight | Registry/preflight | Partially implemented — descriptor/config equality checked at validation step 8; full registry-live wiring deferred | No |
| 5 Approval validation | RIHAC validator | Implemented (`validate_approval`, 12 steps) | No |
| 6 Permission Broker | PB + PBRD extension | Implemented (`build_runtime_dispatch_permission_broker_request` + unmodified `PermissionBroker`) | No |
| 7 Runtime Enforcement | RE coordinator | Not implemented (mock-only, pre-existing, untouched) | No |
| 8 Process containment + live preflight | Shell Gate | Not implemented | No dispatch yet |
| 9 Durable pre-dispatch record | Coordinator/store | Staged only — `RuntimeDispatchIdentityTracker` is a construction-time, non-durable collision guard, explicitly NOT the durable 8-item record | No process effect |
| 10 Adapter dispatch | Runtime Adapter | Not implemented | N/A — no code added |
| 11 Result capture/intake | Adapter collector | Not implemented | N/A — no code added |

## Matrix E — Security invariants

| Threat | Mechanism | Test | Verdict |
|---|---|---|---|
| Forged/tampered approval | Record-digest recomputation | `test_forged_approval_digest_never_validates` | PASS |
| Copied approval, sibling repo | Repository-identity subject binding | `test_copied_approval_into_sibling_repository_fails_repository_binding` | PASS |
| Task swap | `task_id` subject binding | `test_task_swap_attack` | PASS |
| Target swap | `runtime_target_id` subject binding, no fallback | `test_step_6_target_swap_no_fallback` | PASS |
| Prompt swap | `prompt_hash` subject binding | `test_step_7_prompt_swap` | PASS |
| Replay after validation (no consumption) | Non-consuming validation | `test_validating_an_unconsumed_approval_repeatedly_never_consumes_it` | PASS |
| Attempt-ID collision, conflicting content | `RuntimeDispatchIdentityTracker` | `test_same_attempt_id_different_content_hard_collision` | PASS |
| Idempotency-key replay, different invocation | `RuntimeDispatchIdentityTracker` | `test_same_idempotency_key_different_invocation_id_rejected` | PASS |
| Caller-supplied `approval_present` shortcut | Builder signature excludes the parameter entirely | `test_only_gate_5_projection_can_produce_approval_present_true` | PASS |
| Path traversal via `approval_id` | Regex confinement before path construction | 9-case parametrized store suite | PASS |
| Malformed/corrupted store artifact | Fail-closed load | 10-case corruption suite | PASS |
| Real (non-simulation) dispatch with valid authority | POL-005 unmodified | `test_real_dispatch_always_denied_by_pol005_regardless_of_valid_approval` | PASS |
| subprocess/network/credential use in new modules | Static AST audit + runtime tripwires | `test_runtime_dispatch_no_external_effect.py` (12 tests) | PASS |

## Matrix F — Normative vs. implemented

| Capability | Contract | 3W implementation status |
|---|---|---|
| RIHAC-001 human-authority semantics | RIHAC-001 v1.0 | Production-implemented (creation, validation, freshness, provenance) |
| RIASC-001 schema | RIASC-001 v1.0 | Production-implemented (structural validator; still no JSON-Schema-file registration, per RIASC-001 §13's own non-goal) |
| PBRD-001 request/action | PBRD-001 v1.1 | Production-implemented (Option B, 14 facts, projection) |
| RDGO-001 gates 1–6 | RDGO-001 v2.0 | Implemented (gate 4 partially — see Matrix D) |
| RDGO-001 gates 7–11 | RDGO-001 v2.0 | Not implemented — future phases |
| Durable gate-9 record | RDGO-001 §10 | Not implemented — staged construction-time guard only |
| POL-005 eligibility evolution | PBRD-001 §12 | Not implemented — 10 of 11 prerequisites remain outstanding |
| Real execution | All | Not implemented — `unavailable` |
