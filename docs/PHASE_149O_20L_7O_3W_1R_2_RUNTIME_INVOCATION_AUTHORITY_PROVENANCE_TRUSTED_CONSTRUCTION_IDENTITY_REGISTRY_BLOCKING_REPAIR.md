# Phase 149O.20L.7O.3W.1R.2 — Runtime Invocation Authority Provenance, Trusted Construction, and Identity Registry Blocking Repair

## 1. Objective

Close the four active blockers left open by Phase 149O.20L.7O.3W.1R.1
(original B1, original B7, new N1, new N2) under unchanged RIHAC-001 v1.0,
RIASC-001 v1.0, PBRD-001 v1.1, RDGO-001 v2.0, and RPAC-001 v1.0, without
enabling execution.

## 2. Baseline

| Fact | Value |
|---|---|
| Repository | `~/repos/pcae-harness` |
| Repair baseline | `78de464b225f834b44cb0d5ad807faf7de3cdc2a` |
| Ahead of `origin/main` | 0 |
| Public release | v0.4.3 at `63580893b1de4782a694ab802ff7bdebdf29b0e6`, unchanged |
| Entry runtime | `Observed` / `observe` / `unavailable` |
| Entry Git state | clean, pushed |

`pcae health`, `pcae check`, `pcae status coherence`, `pcae push check`, and
`pcae runtime inspect` all passed/confirmed at entry. `pcae doctor
task-memory` reported only pre-existing `tasks/DONE.md` sync warnings
(historical debt, carried separately per §13, not repaired here).

## 3. Verification verdict entering this phase

Phase 3W.1R.1 (`docs/PHASE_149O_20L_7O_3W_1R_1_...md`) found:

```text
RUNTIME INVOCATION AUTHORITY + PB FOUNDATION REPAIR:
NOT VERIFIED
3W.1 ORIGINAL BLOCKERS:
5 / 7 INDEPENDENTLY CLOSED; B1 AND B7 OPEN
NEW BLOCKING:
2
```

## 4. Active blocker recovery (verbatim)

### B1 — Forgeable trust seals

> "copied projection seal and copied PB-request seal both obtain simulated
> ALLOW" (3W.1R.1 Matrix A). Exact attack (§25): "1. copy a legitimate
> projection, replace approval ID/digest/binding, retain `_validator_seal`,
> then obtain `approval_present=true` and simulated ALLOW; 2. copy a sealed
> no-authority PB request, replace its authority binding and boolean, retain
> `_runtime_dispatch_seal`, then obtain simulated ALLOW."

- File/symbol: `runtime_authority.ValidatedAuthorityProjection` /
  `is_trusted_validated_authority_projection`;
  `runtime_dispatch_permission.RuntimeDispatchIdentity` /
  `build_runtime_dispatch_permission_broker_request`.
- Root cause (confirmed by source read): `_VALIDATED_AUTHORITY_SEAL` and
  `_RUNTIME_DISPATCH_IDENTITY_SEAL` are bare module-level `object()`
  singletons. `is_trusted_validated_authority_projection` only checks
  `value._validator_seal is _VALIDATED_AUTHORITY_SEAL` — an identity check
  against a constant, not a content-bound proof. `dataclasses.replace()`
  preserves the `compare=False` seal field verbatim while letting every
  other field (including `approval_id`, `record_digest`,
  `subject_scope_binding_digest`) be overwritten arbitrarily.
- Contract: RIHAC-001 §16 step 12; PBRD-001 §§5, 7, 15, 22.

### B7 — Copied identity seal bypasses registry

> "copied identity seal creates an unregistered attempt accepted by
> builder" (3W.1R.1 Matrix A / §19: "a sealed identity can be copied with
> `dataclasses.replace`, its public digest recomputed, and an unregistered
> replacement attempt accepted").

- File/symbol: `runtime_dispatch_permission.RuntimeDispatchIdentity`,
  `_identity_registration_digest`,
  `build_runtime_dispatch_permission_broker_request`.
- Root cause (confirmed by source read): `_identity_registration_digest`
  is a plain, unkeyed, public-algorithm hash over
  `(invocation_id, attempt_id, idempotency_key)`. It is not a secret-keyed
  MAC and it is never compared against the durable
  `RuntimeDispatchIdentityTracker` registry files on disk at builder time.
  An attacker who can call `dataclasses.replace()` and re-invoke this same
  pure function can produce a self-consistent `_registration_digest` for
  any forged triple; `build_runtime_dispatch_permission_broker_request`
  never re-reads `.pcae/runtime-dispatch-identities/v1/**` to confirm the
  triple was actually registered.
- Contract: PBRD-001 §§6, 10, 15; RDGO-001 §10a; RPAC-REQ-064–068.

### N1 — Canonical-store provenance not bound to validation

> "`validate_approval` accepts a caller-created approval object directly;
> steps 1–2 are documented as another caller's responsibility, with no
> store-issued evidence. A recomputed, schema-valid object can validate
> without ever existing canonically." (3W.1R.1 §41)

- File/symbol: `runtime_authority.validate_approval`;
  `runtime_invocation_approval_store.RuntimeInvocationApprovalStore.load`.
- Root cause (confirmed by source read): `RuntimeInvocationApprovalStore.load`
  returns a bare `RuntimeInvocationApproval` dataclass — no field, wrapper,
  or side channel distinguishes "this object was just read through the
  confined, no-follow, create-only store" from "this object was constructed
  in-process by any caller of `create_runtime_invocation_approval` or by
  hand." `validate_approval`'s docstring explicitly says step 1/2 canonical
  resolution is "the store's job" and is not itself checked.
- Contract: RIHAC-001 §§15, 18; RIASC-001 §12 (store confinement is proven;
  the *link* from store-confinement to validator-trust is not).

### N2 — Human-confirmation provenance is caller-manufacturable

> "`create_runtime_invocation_approval` is a public callable that accepts
> `approver_id` and `identity_evidence_kind` as strings and emits a record
> that validates as `identified_human_distinct_from_producer`, without
> trusted confirmation evidence." (3W.1R.1 §14)

- File/symbol: `runtime_authority.create_runtime_invocation_approval`,
  `runtime_authority.ApprovalProvenance`.
- Root cause (confirmed by source read): `approver_id` and
  `identity_evidence_kind` are ordinary caller-supplied strings, validated
  only against an enum (`os_authenticated_user` /
  `typed_confirmation_only`) and against "not equal to
  `producer_component`" — no independent verification that a real human
  confirmation event, or a real OS-authenticated session, ever occurred.
- Contract: RIHAC-001 §3; RIASC-001 §7.

## 5. Previously closed findings (B2–B6) — regression check

Re-read against current source (no code changed this phase, so these
remain at their 3W.1R.1-verified state; re-run not required since nothing
in their shared surface was touched):

| Finding | 3W.1R.1 verdict | This phase |
|---|---|---|
| B2 (store link/hardlink escape) | CLOSED | untouched, remains CLOSED |
| B3 (RIASC schema/duplicate-key) | CLOSED | untouched, remains CLOSED |
| B4 (preview provenance recompute) | CLOSED | untouched, remains CLOSED |
| B5 (descriptor/scope cross-binding) | CLOSED | untouched, remains CLOSED |
| B6 (lexical vs instant timestamp) | CLOSED | untouched, remains CLOSED |

## 6. Contract sufficiency (pre-implementation gate)

Per this phase's own instructions: *"Before implementation, for each
open/new blocker answer: CAN THIS BE REPAIRED UNDER CURRENT FROZEN
CONTRACTS? YES / NO. If any answer is NO: STOP and recommend contract
evolution."*

### Matrix A — Contract-sufficiency verdicts

| Finding | Repairable under frozen contracts? | Reasoning |
|---|---|---|
| B1 | **YES** | RIHAC/PBRD require "validator-issued evidence" and a "trusted PB request builder," not a specific mechanism. A content-bound (HMAC-keyed) seal replacing an identity-only seal is an implementation strengthening, not a new normative semantic. |
| B7 | **YES** | RDGO-001 §10a and RPAC-REQ-064–068 already require a "durable cross-process conflict guarantee" from a registry that already exists on disk (`RuntimeDispatchIdentityTracker`). Re-checking the identity triple against that existing durable registry at construction time uses an already-specified mechanism, just applies it at the point it was skipped. |
| N1 | **YES** | RIHAC-001 §15/§18 already requires canonical, confined, create-only store behavior; binding `validate_approval` to store-issued evidence (rather than a bare object) formalizes an already-intended two-step "resolve-then-validate" split the current docstring already describes as required but unenforced. |
| N2 | **NO** | See §7. |

## 7. N2 contract-sufficiency analysis (STOP finding)

RIHAC-001 §3 ("Authority source and approving subject") states:

> "The approving human SHALL be identified by provenance evidence... The v1
> approval mechanism is `interactive_local_cli_confirmation`. This is a
> dedicated runtime-invocation confirmation mechanism. It is not CHGR
> Confirmation, an Interactive Decision Session, a task/phase lifecycle
> decision, or a Typed Authority Model `human_authorization` record."

This phase investigated whether any *existing* PCAE mechanism could supply
genuine authenticated-human evidence to `create_runtime_invocation_approval`
without inventing new authentication architecture:

1. **PCAE's own Interactive Workflow system** (`pcae.interactive_workflow`,
   `SessionCoordinator`/`ConfirmationController`, built in Phases
   143J–143N per project memory) is a genuine confirmation architecture
   with digest-bound, replay-resistant confirmation — but RIHAC-001 §3
   explicitly forbids treating "an Interactive Decision Session" as this
   contract's approval mechanism.
2. **TAM `human_authorization` records** and **CHGR Confirmation** are
   likewise explicitly excluded by the same sentence.
3. **`os_authenticated_user`** (one of exactly two schema-permitted
   `identity_evidence_kind` values, RIASC-001 §7) has no existing trusted
   resolver in this codebase. A search for `getuser`/`getlogin`/`getuid`
   usage found that `hatp_class_b_topology_verifier.py:715-723` explicitly
   flags `getuser()`/`getlogin()` calls as untrustworthy
   "admin/user/identity-shaped literal[s]" elsewhere in this same
   repository's own security posture, and `hatp_bootstrap.py:214-220`
   explicitly disclaims deriving trust-relevant state from
   `getpass.getuser()`. There is no counter-example anywhere in
   `src/pcae/core/` where an OS username is treated as authenticated
   identity evidence.
4. **`typed_confirmation_only`** requires an actual interactive
   confirmation surface. `runtime_authority.py`'s own module docstring
   states approval creation is "Option A, internal-API-only... there is no
   CLI surface here and none is added by this phase" (3V.2 §13) — i.e. the
   real confirmation UI this evidence kind describes has been deliberately
   deferred by an earlier, still-governing phase decision.
5. `agent_id` (the CLI `--agent-id` roster used by `pcae session
   bootstrap`) is a self-declared identifier from a fixed roster, not an
   OS- or cryptographically-authenticated human principal, and identifies
   an *agent* (frequently an AI assistant), not necessarily a human.

**Conclusion: no existing PCAE mechanism can supply genuine
authenticated-human evidence to this contract's dedicated approval
mechanism without building new authentication/confirmation architecture.**
This matches this phase's own explicit stop condition (§56 of the governing
instructions): *"STOP if repair requires... authentication architecture
absent from current contracts."*

**Verdict: NO. Contract change (or a new confirmation-capability contract)
required. Do not improvise new authority semantics.**

## 8. Decision

Per instruction: *"If any answer is NO: STOP and recommend contract
evolution."* This phase stops here. **No production source was modified.**
B1, B7, and N1 remain OPEN (not repaired in this phase, despite being
independently assessed as repairable under frozen contracts) because the
governing instruction requires a full stop — not a partial repair — the
moment any one of the four active blockers is found contract-insufficient.

This was confirmed with the human operator directly during this phase
(explicit choice: "Full stop, no implementation" over "narrow to B1+B7+N1"
or "reconsider N2 analysis").

## 9. Trusted-construction-boundary design notes (not implemented)

Recorded for the future repair phase, without being built now (avoiding
"improvised new authority semantics" ahead of a STOP):

- B1: replace both bare-`object()` seals with an HMAC-keyed digest computed
  over each capability's own content at emission time, using a
  process-local secret never exported from the module. Verification
  recomputes the expected digest from the object's *current* field values
  and compares — `dataclasses.replace()` on any bound field then breaks
  the seal instead of surviving it.
- B7: `build_runtime_dispatch_permission_broker_request` must re-read the
  durable `RuntimeDispatchIdentityTracker` registry file for the presented
  `(invocation_id, attempt_id, idempotency_key)` triple at construction
  time and require it to exist and match, not merely recompute a
  self-consistent public digest.
- N1: the approval store's `load()` (and the internal creation path) should
  emit a store-sealed handle using the same HMAC pattern as B1, and
  `validate_approval` (or a newly named wrapping entry point, e.g.
  `validate_runtime_invocation_authority()` vs. a separate
  `load_approval_record()`) should require that handle rather than a bare
  `RuntimeInvocationApproval`.
- N2: cannot be designed without a human decision on which authentication
  architecture (if any) RIHAC-001 v2 should adopt; deliberately left
  undesigned here.

## 10. Older MUST-FIX findings (3S.2.1) — reachability

Recovered verbatim from 3W.1R.1 §42: (1) malformed adapter result crashes
uncaught instead of failing closed cleanly (`simulate_invocation` /
`RuntimeInvocationStore.write_result`); (2) `RuntimeInvocationStore` does
not sanitize `invocation_id` against path traversal. Since this phase made
no source change, reachability is unchanged: **neither is reachable**
through the (still four-file, unmodified) authority/PB foundation. They
remain **MUST-FIX / DEFERRED-REAL-RUNTIME**.

## 11. Runtime inspect

`pcae runtime inspect` at entry: `Observed` / `observe` / `unavailable`,
implementation `not_implemented`, 0 plugins / 0 capabilities. Classification
unchanged: **TRUTHFUL_WITH_LIMITATION**.

## 12. No effect proof

No production file was opened for write. `git status --short` was clean
before and remains clean except for this document and governance/task
bookkeeping files. Runtime subprocess / network / provider / credential
reads / external runtime / background work: **0** (no new code path was
exercised; this is a documentation-only phase).

## 13. Infrastructure debt (carried separately, not repaired)

- `tasks/DONE.md` sync warnings surfaced by `pcae doctor task-memory`
  (pre-existing across many prior phases).
- Shell-Gate order/hang debt (carried since 3W.1).
- Optional-`build`-module packaging test gap (carried since 3W.1).

None of these were touched or newly caused by this phase.

## 14. Contract integrity

`git diff` against `docs/contracts/` for this phase's commits is empty by
construction (no contract file was opened). Normative contract drift:
**NONE**.

## 15. Final verdict

```text
RUNTIME INVOCATION AUTHORITY PROVENANCE REPAIR:
STOPPED — CONTRACT-INSUFFICIENT FINDING (N2)
B1:
OPEN (assessed repairable, not implemented — full-stop rule)
B7:
OPEN (assessed repairable, not implemented — full-stop rule)
N1:
OPEN (assessed repairable, not implemented — full-stop rule)
N2:
OPEN (assessed NOT repairable under current frozen contracts)
B2-B6:
REMAIN CLOSED
PRODUCTION SOURCE MODIFIED:
NO
EXECUTION ACTIVATED:
NO
CONTRACT DRIFT:
NONE
RUNTIME:
Observed / observe / unavailable
RELEASE:
v0.4.3 unchanged
SELF-CERTIFICATION:
NO
```

## 16. Recommended next phase

Two options, not mutually exclusive, both requiring human authorization:

1. **Contract-evolution phase** — define what "authenticated" means for
   RIHAC-001's `interactive_local_cli_confirmation` mechanism (an RIHAC-001
   v2 amendment or a new dedicated confirmation-capability contract), since
   N2 cannot close honestly without it.
2. **149O.20L.7O.3W.1R.3 — Trusted Construction and Identity Registry
   Repair (B1/B7/N1 only)** — a re-scoped bounded repair phase, explicitly
   authorized to proceed on only the three contract-sufficient findings
   while N2 stays open pending option 1, followed by independent
   verification.

## 17. Human decision required

**YES.** Stop after this phase. Production source modified: **NO**.
Execution activated: **NO**. Release changed: **NO**. Article remains
stopped; private research remains untouched (out of scope, not accessed).
