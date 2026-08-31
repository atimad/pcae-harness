# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.21 Complete — N-16-3 Local-CLI Narrow-Eligibility Policy and Contract Planning

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.21
**Type:** planning / contract analysis only
**Status:** N-16-3 ARCHITECTURE / CONTRACT PLAN COMPLETE — IMPLEMENTATION NOT BEGUN — POL-005 PRODUCTION HARD-DENY BEHAVIOUR UNCHANGED — FIRST EXTERNAL EFFECT STILL BLOCKED — EXECUTION NOT ENABLED
**Production source changed:** none (`git diff --name-only ced1b934 HEAD -- src/pcae` empty)
**Normative contracts changed:** none (`git diff --name-only ced1b934 HEAD -- docs/contracts docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` empty)
**POL-005:** `ExecutionDisabledRule` byte-identical; still an unconditional hard DENY for every truthful non-simulation request
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; real execution UNAVAILABLE; deterministic authentication NON_REAL
**Phase-entry SHA:** `ced1b934` (`origin/main` synced; `origin/main..HEAD = 0`)

## Summary

Planning / contract analysis only. Re-derived N-16-3 from primary source
(PBRD-001 v2.1 §12 verbatim; RDGO-001 v3.1; PBPA-001; the RE No-Go Registry
schema 1.1; `permission_broker_foundation.py` `ExecutionDisabledRule` /
`_compose` / `_structural_request_failure` / `RuntimeDispatchRequestFacts` /
`_valid_runtime_dispatch_request` / the `_RUNTIME_DISPATCH_REQUEST_SEAL`;
`runtime_dispatch_permission.py` `build_runtime_dispatch_permission_broker_request`;
`.1R.16` §7 / §18 / §19 / §20 / §30 / §33 / §35 / §36.2; the `.1R.19R.1`
canonical report), not from phase summaries.

**Central planning question answered (frozen).** A future local-CLI
`runtime_dispatch` request can be made Permission-Broker *eligible* — POL-005
does not categorically preclude ordinary PB evaluation — **only** via a
single **trusted-derived** execution profile `RUNTIME_DISPATCH_LOCAL_CLI_V1`
that is not within POL-005's historical hard-block domain, governed by a
**dedicated conjunctive policy `POL-013`** ("Narrow Local-CLI Dispatch
Eligibility") whose most permissive output is *not-triggered* — it never
emits `ALLOW`, never `HUMAN_REVIEW`, never suppresses any other policy.
Failure of any of the 21 profile predicates → POL-005 retains its hard-DENY
match **and** `POL-013` returns `DENY`
(`narrow_local_cli_dispatch_profile_incomplete`).

**Selected architecture: Option C + D.**
- **C** — a new trusted-derived execution profile that is genuinely
  materially narrower on every axis (local process, fixed argv, no network,
  no credentials, supply-chain-admitted executable, real human authority,
  single attempt, durable lifecycle, repo-scoped cwd) and is
  classification-proof because the marker is derived by the sealed trusted
  request builder, never caller-set.
- **D** — the `POL-013` conjunction that proves the request actually *is*
  the narrow profile and fails closed otherwise.
- **Option B REJECTED** — read directly, `_compose` iterates `(DENY,
  HUMAN_REVIEW)` and returns the first category with any triggered rule;
  there is **no specificity tier, weight, or override channel**, so a
  "higher-specificity ALLOW" cannot overcome a POL-005 DENY. PBRD §9 / §12
  also forbid weakening precedence.
- **Option A** inferior — makes POL-005's meaning taxonomy-dependent inside
  `ExecutionDisabledRule`; C is the cleaner framing of the same mechanical
  outcome ("this class was never in POL-005's domain" vs "POL-005 now has an
  exception").
- **Option E REJECTED** — the rule is contract-expressible now; it does not
  need N-16-4/5/6/7 to *exist* to be *defined*, only to be *satisfied*.
  Deferring the definition blocks N-16-4..7 planning coherence with no
  safety benefit.

**Current POL-005 semantics (re-derived, not paraphrased).** `POL-005`
(`ExecutionDisabledRule`) is triggered exactly when `request.simulation_only
is False`; when triggered it returns an unconditional `DENY` citing NG-025 /
INV-001 / COMP-002, for **every** `action_type` and `execution_class`. It is
universally applicable (no `applicable_execution_classes` declared → `None` →
universal per PBPA-REQ-019), is never `HUMAN_REVIEW` or `ALLOW`, carries no
exception channel, and under `_compose`'s `DENY > HUMAN_REVIEW > ALLOW`
precedence a single POL-005 trigger determines the decision regardless of any
other rule. The modeled future Slice-C PB request (14-fact sealed
`runtime_dispatch` / `execution_class=adapter` / `simulation_only=false` /
`approval_present=true`) evaluates to **`DENY`**,
`causing_policy_ids=("POL-005",)`, `matched_no_go_ids=("NG-025",)` — correct
today and required to remain so for every request outside the full narrow
profile.

**PBRD-001 §12 interpretation.** §12 enumerates eleven conditions "separately
implemented and independently verified" before `runtime_dispatch` "may
become eligible", then mandates the shape: "a narrowly scoped eligibility
rule for the exact local-CLI `runtime_dispatch` profile, not deletion of
POL-005, a universal non-simulation bypass, or an inference that
`simulation_only=false` is itself permission. Every non-eligible
non-simulation request remains denied." §12 mandates the shape but does not
define the rule — N-16-3 authors it. (`.1R.16` §35 row 13's "item 4 of the
eleven" is an imprecise cross-reference — item 4 is the "no precedence
weakening" *constraint*; the rule itself is the §12 closing mandate
paragraph. Non-blocking; N-16-3's scope is unchanged.)

**Target profile — `RUNTIME_DISPATCH_LOCAL_CLI_V1`, 21 trusted predicates.**
`action_type=runtime_dispatch`; `execution_class=adapter`;
`transport_type=local_cli` (const); `network_requirement=false`
(**mandatory** — PBRD §3/§11; a network-using executable belongs to a later
profile); no credential / secret / provider / model field (**mandatory** —
PBRD §6/§11); no shell or command string; `adapter_descriptor_binding`
carrying a resolvable canonical supply-chain admission binding of class
`local_fixed_argv` (N-16-6); fixed argv from the admitted descriptor;
trusted environment allowlist; repo-scoped cwd; bounded resource/time-limit
containment-profile references; `human_authority_binding` = a valid
RIHAC-001 v2.0 validated-authority projection for the exact `invocation_id`
with a **real** (non-deterministic, non-NON_REAL) assurance verdict (N-16-5);
coordinator-minted `attempt_id` + `idempotency_key`; one exact
`runtime_target_id` (no alias/fallback); digest-bound `filesystem_scope_ref`;
the Slice-B durable dispatch-attempt lifecycle wired; a derived, non-caller
`profile_classification` marker set **only** by the sealed trusted request
builder from the other predicates.

**Anti-bypass — the load-bearing property.** Every authority-bearing
predicate is `Caller-controllable? = No`. The classification is
**trusted-derived, not caller-declared**, at every predicate:
`RuntimeDispatchRequestFacts` is constructible only behind
`_RUNTIME_DISPATCH_REQUEST_SEAL`; the generic
`build_permission_broker_request` raises
`runtime_dispatch_requires_trusted_builder`; `_valid_runtime_dispatch_request`
fails closed on a missing seal, on `execution_class != adapter`, on
`network_requirement is not False`, and on authority inconsistency; caller
`approval_present` / `attempt_id` / `idempotency_key` are construction-time
rejections (PBRD §15); a fabricated `adapter_id` has no admission record
(N-16-6) → `POL-013` DENY; Gate 8 re-hashes the executable; the PB decision
expires on any request change (PBRD §10). The sealed builder + const
transport shipped in `.1R.13` already provide the trusted-derivation
substrate.

**Semantic walls — all verified against current source.** human approval ≠
PB permission ≠ Runtime Enforcement capability ≠ runtime execution
availability ≠ external effect; POL-005 eligibility ≠ blanket execution
permission. Human approval is **one predicate among twenty-one**, consumed
once at Gate 9, never a policy override. `if human_approved: ignore POL-005`
and `trusted principal → ALLOW` are explicitly rejected — `_compose` has no
channel by which any input flips a DENY, and P14 does not touch POL-005's
match logic (the trusted-derived P21 classification does, and P14 is only one
of its inputs).

**Eligibility to evaluation, not guaranteed ALLOW.** `narrow profile proven
→ POL-005 does not categorically preclude ordinary PB evaluation`; it does
**not** imply `ALLOW`. A `…_V1` request that clears POL-005 and `POL-013` is
then subject to POL-001 / POL-003 / POL-004 / POL-006 / POL-007 and the full
`DENY > HUMAN_REVIEW > ALLOW` composition, exactly as today — POL-004 still
emits `HUMAN_REVIEW` (which dominates `ALLOW`) if approval is absent, any
DENY policy still DENYs, and the `ALLOW` branch of `_compose` is reached only
when no rule triggered DENY or HUMAN_REVIEW. The narrow profile never
directly returns `ALLOW` by classification.

**Default-deny outside the exact profile.** Any missing predicate, any
unknown/indeterminate predicate state, any malformed binding, any
unsupported adapter/executable class, or any broader effect profile →
POL-005 DENY **and** `POL-013` DENY. No fuzzy matching, no partial credit.
Unknown/malformed new policy fields are never read as eligibility
(`profile_classification` must be the exact literal
`RUNTIME_DISPATCH_LOCAL_CLI_V1`).

**Conceptual deltas (no contract or production edit this phase).**
- **PBRD-001** — new **§12a** spelling out the narrow-eligibility rule
  (proposed normative text in the artifact §31). Versioning: **MINOR**
  (→ v2.2) — it defines the rule §12 already mandated; no request fact added
  or removed; no precedence change; no execution-class change; no old valid
  request invalidated.
- **POL-005** — canonical-statement **versioned amendment**; **POL-005
  retains its ID** for audit-trail continuity (every prior
  `causing_policy_ids=("POL-005",)` decision stays interpretable). Its match
  domain gains exactly one trusted-derived carve-out. The
  *policy-semantics* change is MAJOR-class and is carried with an explicit
  migration note + independent verification, but **without** a new policy
  ID and **without** deleting POL-005 (§12 forbids deletion).
- **`POL-013`** — new additive conjunctive policy; applicable only to
  `runtime_dispatch` / `adapter`; never emits `ALLOW`.
- **PB request schema** — two additive **internal, non-caller** fields:
  `RuntimeDispatchRequestFacts.profile_classification` (derived by the
  trusted builder) and `RuntimeDispatchAdapterDescriptorBinding.admission_record_digest`
  / `admission_class` (populated from N-16-6's admitted-descriptor
  preflight). Both are inside the PBRD §5 canonical request digest and
  transitively `consumption.json` `record_digest`. No caller-visible field
  is added; existing callers leave `runtime_dispatch_context = None` and are
  unaffected.
- **RE No-Go Registry** — NG-025 canonical-statement annotation only
  (schema unchanged; parallels the schema-1.1 V-13-3-2 precedent).
- **RDGO-001 / RIHAC / RIASC / HPAC / RPAC / PBPA** — no change.

**Trusted builder + digest binding.** The **only** builder allowed to
populate the two new fields is
`build_runtime_dispatch_permission_broker_request` (already the sole seal
holder). It computes `profile_classification` last, after every other fact
is validated and the N-16-6 admission binding resolves. A change to any
predicate changes the derivation → changes the request digest → expires any
prior PB decision.

**Policy precedence.** Re-derived from `_compose`: `DENY > HUMAN_REVIEW >
ALLOW`, fail-closed, **no** specificity tier / weight / override. POL-005
not triggering for `…_V1` removes one DENY contributor; it does not add an
ALLOW and does not change the algorithm. `POL-013` only ever contributes
nothing (pass) or a DENY (fail). §12 item 4 ("no precedence weakening") is
satisfied by construction.

**Hard no-go preservation.** POL-001 / POL-003 / POL-004 (HUMAN_REVIEW,
`adapter` in applicable set) / POL-006 / POL-007, the
`_valid_runtime_dispatch_request` structural failure path, RE-NOGO-001..017,
and POL-005-for-every-non-`…_V1`-non-simulation-request all still dominate.
Narrow eligibility does not become general allow.

**Backward compatibility.** No legacy caller becomes eligible accidentally —
`profile_classification == ""` → POL-005 DENYs exactly as today; provider /
network / credential requests stay blocked; the dry `adapter_invocation` /
`simulation_only=true` path is untouched; stored `/2.0` and `/2.1` records
are unaffected.

**Gate relationships.** Gate 5 validates human authority and MUST NOT decide
POL eligibility (`POL-013` reads its outputs as inputs). Gate 6 is the sole
PB policy owner — N-16-3 belongs here entirely. PB eligibility MUST NOT
imply a Gate-7 ALLOW — Gate 7 independently re-evaluates. Containment (Gate
8) and final effect-state read-back (Gate 10) remain downstream; `POL-013`
only requires the presence/well-formedness of the containment/admission
bindings, not the actual containment. Even a future PB ALLOW + RE ALLOW
produces **no external effect** while `EXECUTION_AVAILABILITY == "unavailable"`
(RDGO §11 item 5; re-read from current state at Gate 10).

**Positive-path structural reachability (§47).** After N-16-3 implementation
(`.1R.22`) alone, production **cannot** produce a `RUNTIME_DISPATCH_LOCAL_CLI_V1`
PB ALLOW: N-16-6 (no admission store / no admitted executable), N-16-5 (no
real human authority — Gate 5 hard-stops NON_REAL), and N-16-7 (capability
`unavailable`) each independently keep the profile incomplete. `.1R.22` may
ship a NON-admitting fail-closed stub so the profile stays unsatisfiable.
This is the safer, contract-consistent outcome.

**Implementation decomposition (frozen).**
- `149O.20L.7O.3W.1R.2B.1R.1.1R.22` — N-16-3 Narrow-Eligibility Policy and
  Contract Implementation: PBRD §12a (→ v2.2 MINOR); POL-005
  canonical-statement amendment; new `POL-013`; derived
  `profile_classification` + `admission_record_digest` internal request
  fields via the trusted builder; N-16-6 admission-binding **interface**
  with a fail-closed stub; the 25-case defensive test matrix; scope-fence
  guard reconciliation (subset checks over the exact authorized filename
  set, no wildcard). **No `adapter.dispatch()` call site, no runtime
  capability change, no N-16-6 store, no execution enablement; the narrow
  profile stays unsatisfiable in production.**
- `149O.20L.7O.3W.1R.2B.1R.1.1R.23` — Independent Verification of the N-16-3
  Narrow-Eligibility Policy: RE-DERIVE old callers still DENY; no
  human-approval override; the classification is trusted-derived at every
  predicate; default-deny outside the exact profile; `DENY > HUMAN_REVIEW >
  ALLOW` intact; all broader effect classes still blocked; POL-005 still
  hard DENY for everything else; no `ALLOW` reachable in production; no
  execution / runtime / contract-semantics drift beyond the approved
  change; fixed-SHA A/B.

`.1R.22` / `.1R.23` are **recommended, not reserved**; IDs above `.1R.20`
are not reserved (`.1R.16` §36.2), so `.1R.21` (this) / `.1R.22` / `.1R.23`
are the next free sequential IDs. Do not implement either in `.1R.21`.

**N-16-4..7 dependency ordering (frozen).** N-16-3 → N-16-4 (real positive
single-attempt Runtime Enforcement gate) → N-16-5 (real FIDO2 / WebAuthn /
CTAP + protected human-approval UI) → N-16-6 (RPAC-REQ-095 fixed-argv
external-executable adapter + supply-chain admission) → N-16-7 (runtime
capability enablement `Observed → Approved/Executable`, **strictly last**).
Adjudicated **N-16-4 before N-16-5**: a structural positive RE path can be
implemented and verified while real HPAC is unreachable, is lower-risk, and
has no hardware dependency — N-16-5 then slots into an already-verified
positive RE path. N-16-7 is proven last: all of policy + RE + human
authentication + adapter admission + the Gate-10 lifecycle must each
independently verify before runtime moves off `unavailable`; capability
promotion is never folded into an earlier prerequisite. Each of N-16-4..7 is
its own explicitly authorized implementation + IV pair. Slice C / D keep no
phase ID.

**Deliverables.** Canonical planning artifact
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_21_N_16_3_LOCAL_CLI_NARROW_ELIGIBILITY_POLICY_AND_CONTRACT_PLANNING.md`
(§2 central question + semantic walls; §3 N-16-3 re-derivation; §4 current
POL-005 semantics; §5 PBRD §12; §6 modeled future PB request + current
decision; §7 target profile — 21 predicates; §8 separate eligibility
dimensions; §9 no human-approved override; §10 Options A–E; §11 anti-bypass;
§12 trusted predicate ownership matrix; §13 execution-class trust; §14
local-CLI origin trust; §15 fixed-executable prerequisite; §16 real
human-authority prerequisite; §17 Runtime Enforcement prerequisite; §18
runtime capability prerequisite; §19 supply-chain relationship; §20
network + credential prohibition; §21 candidate normalized rule; §22
eligibility-not-ALLOW; §23 default-deny; §24 policy precedence; §25 hard
no-go preservation; §26 attempt-count semantics; §27 permission decision
lifetime; §28 gate relationships; §29 security-boundary matrix; §30 required
final report; §31 conceptual PBRD §12a delta; §32 conceptual POL-005 delta;
§33 PB request/schema/builder/digest impact; §34 versioning adjudication;
§35 POL-005 version/identity; §36 backward compatibility; §37 fail-closed +
25-case defensive test matrix; §38 anticipated contract files; §39
anticipated production files; §40 implementation decomposition; §41 N-16-4..7
ordering; §42 runtime zero-effect evidence; §43 contract identity; §44
STOP-condition check; §45 `.3` incident). `PROJECT_STATUS.md` and
`CHANGELOG.md` updated.

**Tests.** None — planning-only phase; no test file added or changed;
`test_evidence_classification = not_applicable_planning_only_phase_no_code_changed`.

**FINAL VERDICT:**
- **N-16-3 POLICY / CONTRACT ARCHITECTURE: PLANNED — IMPLEMENTATION NOT
  BEGUN.**
- **POL-005 NARROW-ELIGIBILITY MODEL: FROZEN FOR IMPLEMENTATION — CURRENT
  HARD-DENY PRODUCTION BEHAVIOUR UNCHANGED.**
- **FIRST EXTERNAL EFFECT: STILL BLOCKED.**
- **N-16-3 STATUS: ARCHITECTURE / CONTRACT PLAN COMPLETE — IMPLEMENTATION
  PENDING** (NOT CLOSED).

## No-Go Confirmations

- No `src/pcae` file was created, modified, or deleted; no `POL-013`
  policy, no `ExecutionDisabledRule` change, no `RuntimeDispatchRequestFacts`
  field, no trusted-builder change, no `adapter.dispatch()` call site.
- No normative contract file was edited; PBRD-001, RDGO-001, HPAC-001,
  RIHAC-001, RIASC-001, RPAC-001, PBPA-001, POL-005
  (`permission_broker_foundation.py`), and the RE No-Go Registry are all
  byte-unchanged.
- No POL-005 change: `ExecutionDisabledRule` is byte-identical; it still
  triggers on `simulation_only is False` and returns an unconditional hard
  `DENY` for every action type and execution class.
- No positive permission / runtime path was enabled; the modeled Slice-C PB
  request still evaluates to `DENY` (`POL-005`) and no
  `RUNTIME_DISPATCH_LOCAL_CLI_V1` classification exists in production.
- No execution was enabled; runtime remains `not_implemented / Observed /
  observe / unavailable`; 0 plugins / 0 capabilities.
- No runtime capability was elevated or promoted; no `Observed →
  Approved/Executable` transition; N-16-7 remains untouched and last.
- No Slice C was implemented; no `adapter.dispatch(` call site exists
  anywhere in `src/pcae`; Gate 10's effect keeps no phase ID.
- No N-16-4, N-16-5, N-16-6, or N-16-7 work was begun; each remains its own
  separately authorized implementation + IV pair.
- No adapter (mock or real) was registered, implemented, activated, or
  called; `RuntimeRegistry` remains empty; no supply-chain admission store
  was created.
- No credential, secret resolver, FIDO2 / WebAuthn / CTAP, or protected
  human-approval UI was accessed, created, or implemented; deterministic
  authentication remains NON_REAL.
- No approval / proof / presentation / challenge / nonce was consumed on any
  path; no `consumption.json` was written anywhere.
- No subprocess, process spawn, `os.system` / `popen` / `spawn` / `exec*`,
  `pty`, provider SDK, HTTP client, socket, or network path was created or
  invoked; the only subprocesses were `git` (history/read), `pcae` (governed
  lifecycle), and read-only shell inspection.
- No third-party system, unrelated account, provider API, external network,
  or deployment target was accessed or mutated.
- No test was added, removed, weakened, or skipped; no planning-traceability
  test was manufactured; no full functional-suite evidence was fabricated
  for a planning-only phase.
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no
  history rewrite, no hook bypass — governed `pcae` lifecycle only.
- No delegated worker committed, finalized, or pushed; only the primary
  human-authorized operator holds `.1R.21` lifecycle authority.
- No authorization of the historical delegated `.3` finalization, commit, or
  push; DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED is preserved.
- No MAJOR or MINOR contract version was bumped, forced, or overridden; the
  PBRD v2.2 MINOR / POL-005 amendment / `POL-013` are conceptual deltas for
  `.1R.22`, not applied.
- No reopening of a closed gate boundary (Gate 5 / 6 / 7 / 8 / 9) or the
  Slice-A / Slice-B verdicts.
- No human approval was treated as a policy override; the `if human_approved:
  ignore POL-005` and `trusted principal → ALLOW` models are explicitly
  rejected in the plan.
- No STOP / BLOCKED condition was reached; every valid early-STOP condition
  in the phase prompt was checked and none applies.

**Recommended next phase:** requires its own explicit human authorization —
`149O.20L.7O.3W.1R.2B.1R.1.1R.22` (N-16-3 Narrow-Eligibility Policy and
Contract Implementation), then `.1R.23` (its Independent Verification).
Recommended, not reserved. Do not implement N-16-3. Do not modify POL-005 or
normative contracts. Do not begin N-16-4..7. Do not implement or call the
first external effect. Do not enable execution.

**Canonical artifact:**
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_21_N_16_3_LOCAL_CLI_NARROW_ELIGIBILITY_POLICY_AND_CONTRACT_PLANNING.md`
