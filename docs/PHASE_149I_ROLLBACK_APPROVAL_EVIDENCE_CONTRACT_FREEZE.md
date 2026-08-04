# Phase 149I — Rollback Approval Evidence Contract Freeze

## 0. Baseline

- Latest completed phase: 149H (`58fc73bf`, `45ca7a1d`, `f104107a`,
  `80eca83f`, `64e99976`; pushed; `origin/main..HEAD` = 0).
- 149H result: `ROLLBACK APPROVAL EVIDENCE ARCHITECTURE DEFINED` —
  CHGR trust substrate + new Rollback Approval Decision Template + new
  dedicated Rollback Approval Binding record, structurally modeled on
  (never composed with) the Typed Authority Model's `human_authorization`
  shape.
- Chapter 149 state: Wave 1 (`PU1/PU2`, `AG1/AG2/AG4/PH1`, `PH2/PH3`)
  VERIFIED WITH NON-BLOCKING FINDINGS; `AG3/AG5` (rollback-class) blocked
  on trusted approval evidence; `TK1/TK2/TK3` deferred. 13 real
  production mutation sites, 0 UNKNOWN.
- Runtime before this phase: `Observed` / `observe` / `unavailable`.
- Pre-phase checks (all ran clean): `git status --short` (clean),
  `git status --branch --short` (`## main...origin/main`),
  `git rev-list --count origin/main..HEAD` (0), `pcae health` (healthy),
  `pcae check` (passed), `pcae status coherence` (coherent),
  `pcae doctor task-memory` (clean), `pcae push check` (nothing to
  push), `pcae runtime inspect` (Observed / observe / unavailable),
  `pcae notify status` (telegram configured/enabled),
  `pcae phase-report show --latest` (149H, completed, pushed,
  `origin/main..HEAD`=0), `pcae phase-report reconcile --phase-id 149H`
  (`delivery_recorded_bookkeeping_incomplete`, mutation: none —
  inspection only, no state changed by the reconcile call itself).

## 1. Phase Type

Normative rollback approval-evidence contract freeze only. No
`src/pcae/**` change. No RWMPC-001, PBPC-001, PBPA-001, CHGR-001,
IWC-001, TAMC-001/TAMPC-001, AESIC-001/AEM-001, or PEC-001 amendment.
No rollback implementation. No AG3/AG5 broker wiring. No
`approval_present=True` production value. No POL-013+. No Prompt
Generation/Dispatch/agent invocation. No runtime capability elevation.

## 2. Independent 149H Architecture Reconstruction

Before drafting contract text, 149H's own selected architecture was
independently re-derived from primary sources, not trusted from its
prose alone:

- **Why CHGR is the trust substrate:** direct reading of
  `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` §1-§13
  confirms CHGR-001 actually guarantees human authorship, a bounded
  Confirmation act distinct from Publication, atomic Publication with
  stable canonical identity, provenance sufficient to reconstruct what
  was confirmed, and immutability after Publication — properties this
  contract needs and does not need to reinvent.
- **Why TAM cannot be directly composed:** direct reading of CHGR-001
  §19.1 (lines 612-644) and `TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md`
  TAMC-REQ-024 (line 209), TAMC-REQ-025 (line 212), TAMC-REQ-036 (line
  277) independently confirms the wall: `human_authorization` records
  SHALL NEVER imply authorization/approval, and CHGR/TAM composition is
  explicitly forbidden. The Typed Authority Model's `human_authorization.schema.json`
  was read directly (`src/pcae/schema_resources/cltr_cutover/records/human_authorization.schema.json`)
  and independently confirmed to have exactly the family-locked
  reference triad, `expires_at`, `state`, `revocation_metadata`,
  `use_binding`, and `replay_binding` shape 149H described — a genuinely
  reusable *shape*, scoped to a different subsystem (CLTR cutover), with
  its own `authority_disclosure.is_authoritative` hard-const-`false`.
- **Why IWC is insufficient:** direct reading of
  `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` §1 and RWMPC-001
  RWMPC-REQ-023 confirms confirmation is explicitly not approval by
  frozen contract text on both sides.
- **Why AESIC is insufficient:** direct reading of
  `docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md` AEM-REQ-003
  confirms disclosure-only, evaluate-and-never-gate semantics.
- **Why self-declared CLI flags are insufficient:** direct reading of
  `src/pcae/core/agent.py:5146` (`approve_rollback`, no actor parameter
  at all) and `src/pcae/cli.py` flag definitions (`--approve-keep`,
  `--approved-by`, `--reason`, `--promotion-authorized`, `--reviewed-by`)
  independently confirms every one is an unauthenticated, unbound
  self-declaration.
- **Why a dedicated rollback binding record is needed:** direct reading
  of `human_governance_record.schema.json` confirms `decision_subject`
  is free text with no `record_family`-typed structural operation
  reference field — CHGR alone cannot enforce exact operation binding.

This independent reconstruction reached the same conclusion 149H did:
no conflict was found between 149H's architecture and primary contract
text. The contract below therefore proceeds to freeze it.

## 3. Contract Identity

`RAE-001` was selected over `RBAE-001`: shorter, and no existing
repository-conventional identifier collides with it; it follows the
same `<ABBREVIATION>-001` pattern as `RWMPC-001`/`PBPC-001`/`PBPA-001`.
Contract text:
`docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`.

## 4. What This Phase Froze

- Terminology (Rollback Operation, Approver, Approval Authority,
  Rollback Approval Decision, Rollback Approval Binding, Rollback
  Approval Evidence, Evidence Validator, Evidence Consumer) —
  contract §3.
- The four-layer semantic separation (human authority != human approval
  decision != approval evidence != Permission Broker permission !=
  execution capability != rollback execution) — contract §4.
- The CHGR/TAM wall, independently re-confirmed and restated as binding
  contract text (RAE-REQ-001-RAE-REQ-004) — contract §5.
- The repository's honest, non-overstated human-identity trust ceiling
  (RAE-REQ-005-RAE-REQ-010) — contract §6.
- The `rollback-approval` Decision Template, with exact frozen field
  values and two closed options (`approve_rollback`/`deny_rollback`)
  (RAE-REQ-011-RAE-REQ-015) — contract §7.
- The Rollback Approval Binding record's full field table, frozen at
  the field-name/semantics level (JSON Schema syntax deferred to
  implementation) (RAE-REQ-016-RAE-REQ-019) — contract §8.
- AG3 (`{job_id, original_commit_sha}`) and AG5 (`{per_id, ecp_id}`)
  operation-identity binding, family-locked, one shared contract with
  two explicit profiles (RAE-REQ-020-RAE-REQ-029) — contract §9-§10.
- Task/branch/repository-state binding, with the two-layer separation
  between approval-time state capture and RWMPC's own live freshness
  re-check (RAE-REQ-030-RAE-REQ-033) — contract §11.
- The Evidence Validator's conceptual interface, inputs, and result
  vocabulary, kept structurally distinct from Permission Broker
  vocabulary (RAE-REQ-034-RAE-REQ-037) — contract §12.
- The central `approval_present` derivation rule as a strict, fail-closed
  conjunction (RAE-REQ-038-RAE-REQ-042) — contract §13.
- Freshness (24-hour window, structurally reused from
  `human_authorization` precedent, not invented), revocation,
  supersession, replay/single-use, and retry semantics
  (RAE-REQ-043-RAE-REQ-053) — contract §14-§16.
- Provenance/integrity, canonical storage, immutability
  (RAE-REQ-054-RAE-REQ-057) — contract §17.
- IWC/AESIC exclusion and legacy-flag exclusion
  (RAE-REQ-058-RAE-REQ-060) — contract §18-§19.
- Human review presentation minimums (RAE-REQ-061) — contract §20.
- Failure semantics and the `HUMAN_REVIEW` flow, broker
  non-interactivity, no automatic evidence creation, rejection handling
  (RAE-REQ-062-RAE-REQ-068) — contract §21.
- A 20-item threat model with a contractual control cited for each
  — contract §22.
- A satisfiability matrix, independently traced against
  `permission_broker_foundation.py`'s current policy registry (no code
  executed), confirming a conceptual `approval_present=True`,
  `execution_class=ROLLBACK`, `simulation_only=True` request resolves
  `ALLOW` under otherwise-valid conditions (RAE-REQ-069-RAE-REQ-070) —
  contract §23.
- Compatibility confirmations for all six depended-on/related contracts,
  each requiring zero amendment (RAE-REQ-071-RAE-REQ-078) — contract
  §24.
- Governance responsibility mapping and the approval-creation boundary
  (RAE-REQ-079-RAE-REQ-080) — contract §25-§26.
- Non-goals, findings (two carried-forward STRATEGIC_GAPs, one
  OBSERVATION, one NON-BLOCKING, two new OBSERVATIONs), and an explicit
  Blocking-condition check against every category the governing prompt
  named — contract §27-§29.

## 5. Blocking-Condition Independent Check

Each Blocking-condition category from the governing phase prompt was
independently re-evaluated against primary source, not assumed resolved
because 149H said so:

| Condition | Verdict | Basis |
|---|---|---|
| No trustworthy approver identity source | Not Blocking — honestly disclosed as repository-wide ceiling, not fabricated stronger | Direct reading confirms no OS/IdP auth exists anywhere in CHGR, IWC, TAM, or PEC |
| No authority source | Not Blocking — `eligible_authority` descriptive-text mechanism already exists on `decision_template.schema.json`, verified by direct schema read | `src/pcae/schema_resources/chgr/records/decision_template.schema.json:63-68` |
| No operation binding | Resolved — new, family-locked `rollback_operation_reference` structural field | Contract §9 |
| No provenance guarantee | Resolved — inherits CHGR-001 §10 plus a new Binding-record digest | Contract §17 |
| CHGR cannot legally host rollback approval semantics | False — Decision Template extension point verified to exist and require no CHGR-001 amendment | `decision_template.schema.json`; CHGR-001 §6 |
| Record can be self-created by agent and trusted | False — `governance_record_reference` must resolve to an actually-published, digest-matched CHGR record | Contract RAE-REQ-018 |
| RWMPC incompatible | False — satisfiability independently traced, no wording change required | Contract §23-§24 |

No Blocking finding resulted. The contract is frozen at v1.0.

## 6. Verification Commands Run

```
pcae health                                  -> healthy
pcae check                                   -> passed
pcae status coherence                        -> coherent
pcae doctor task-memory                      -> clean
pcae push check                              -> nothing to push
pcae runtime inspect                         -> Observed / observe / unavailable
pcae notify status                           -> telegram configured/enabled
```

`git diff --name-only 58fc73bf..HEAD -- src/pcae/` (58fc73bf = 149H's
architecture commit, predating this phase's own edits): confirmed empty
before this phase's contract/phase-document commit, and this phase adds
only `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` and this
document under `docs/` — no `src/pcae/**` path is touched.

## 7. Governance Boundary Confirmations

- RWMPC-001 v1.0 remains unchanged.
- PBPC-001 v1.2 remains unchanged.
- PBPA-001 v1.0 remains unchanged.
- CHGR-001 remains unchanged.
- IWC semantics remain unchanged.
- TAM/TAMPC authority semantics remain unchanged.
- AESIC/AEM remain disclosure-only.
- No production source (`src/pcae/**`) was modified by Phase 149I.
- No rollback Permission Broker consumer was implemented.
- AG3 and AG5 remain unimplemented.
- No `approval_present=True` production value was introduced.
- No self-declared CLI flag was treated as trusted approval.
- No IWC confirmation was treated as approval.
- No AESIC result was treated as approval or permission.
- No illegal CHGR/TAM authority-family composition was introduced.
- No POL-001..012 meaning was changed. No POL-013+ was added.
- No Runtime Enforcement behavior was changed.
- TK1/TK2/TK3 remain deferred.
- No Prompt Generation capability was implemented.
- No Prompt Dispatch capability was implemented.
- No agent invocation capability was implemented.
- Runtime remains Observed, maximum capability remains observe, and
  execution availability remains unavailable.

## 8. Contract Freeze Verdict

```
ROLLBACK APPROVAL EVIDENCE CONTRACT (RAE-001) v1.0 FROZEN
```

## 9. Rollback Readiness Status

```
ROLLBACK APPROVAL ARCHITECTURE:      DEFINED
ROLLBACK APPROVAL CONTRACT:          FROZEN
ROLLBACK APPROVAL IMPLEMENTATION:    NOT IMPLEMENTED
AG3 / AG5:                           STILL UNIMPLEMENTED
```

## 10. Recommended Next Phase

```
149J — Rollback Approval Evidence Contract Independent Verification
```

No RWMPC clarification phase or human-identity-trust repair phase is
recommended: §5 above independently found no Blocking gap in either
area. The independent verifier is directed at contract §33's explicit
attack list.
