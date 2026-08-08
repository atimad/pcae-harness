# Phase 149O.17 — HATP Mandatory Production Consumption Implementation Plan

**Phase type:** IMPLEMENTATION PLAN ONLY. No `src/pcae/**` file, and no
contract file (HMRC-001, HSCE-001, HATP-001, RAE-001, RWMPC-001,
PBPA-001, PBPC-001), was modified to produce this document. No Cutover
Record, consumption adapter, AG3/AG5 gate, PB enforcement capability, or
Class-B provisioning was implemented or activated.

**Subject:** `HMRC-001 v1.0` —
`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`, status
`VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS` (149O.16).

---

## 1. Baseline (Initial Inspection)

Confirmed by direct command execution at phase start:

- `git status --short` / `git status --branch --short`: clean, `main...origin/main`.
- `git rev-list --count origin/main..HEAD`: `0`.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — 7 pre-existing `tasks/done/` vs
  `tasks/DONE.md` entries predating this phase (task-lifecycle hygiene
  debt, unrelated to HMRC-001; not remediated here, outside this phase's
  allowed-file scope; identical pre-existing warning set already noted
  by 149O.16 and 149O.16.2).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`; Permission
  Broker status `execution_unavailable`.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.16.2`: 149O.16.2 confirmed `status: completed`, report
  `complete`, pushed, `origin/main..HEAD: 0`; reconciliation
  `status: delivery_recorded_bookkeeping_incomplete` (pre-existing
  receipt-bookkeeping condition, not a completeness defect —
  `Promoted generations: 2`, `Marker: already_dispatched`, `Mutation: none
  (inspection only)`); recommended next phase confirmed as 149O.17.

Confirmed: repository clean; 149O.16.2 complete; `149O.12B-Obs-PY39-1`
independently confirmed resolved; HMRC-001 v1.0 independently verified
`CONFORMS`; HATP production `NOT READY`; runtime `Observed / observe /
unavailable`. No mutation performed by this inspection.

---

## 2. HMRC Contract State (Restated)

- **HMRC-001 v1.0** — `VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS`
  (149O.16). 85 requirements (`HMRC-REQ-001..085`, mechanically confirmed
  no gaps/duplicates by 149O.16), 14 security invariants (`MC-1..MC-14`,
  no gaps/duplicates), 45 attack-matrix scenarios (`§29`, no gaps/
  duplicates), all independently reconfirmed against real source in this
  phase (§5 below).
- **Finding N-1** (149O.16, non-blocking, editorial): §26's category-index
  table omits `HMRC-REQ-083..085` from the index (they are still
  substantively defined and counted in the 85-total). Retained,
  unchanged, non-blocking — not remediated here (out of this phase's
  scope: HMRC-001 is byte-frozen).
- **New editorial observation (149O.17, non-blocking, not a new finding
  ID — informational only):** §28's Threat Model header line reads
  `**HMRC-REQ-080 (Threat-A attacker capabilities, frozen).**`, textually
  re-using the `HMRC-REQ-080` label already normatively defined at §30
  (`This contract is frozen as HMRC-001 v1.0.`). This does **not**
  contradict 149O.16's mechanical 85-unique-ID finding: 149O.16's
  extraction pattern matched `**HMRC-REQ-###.` (digit immediately
  followed by a literal period), which line 837's
  `HMRC-REQ-080 (Threat-A...` does not match (it is followed by a space
  and parenthesis, not a period) — so it was correctly not counted as a
  86th requirement definition. It is purely an informal, non-normative
  section-header citation of the requirement-080 label as a mnemonic for
  "the threat model this contract assumes," not a second definition of
  REQ-080's normative content. This plan treats §28's threat-model content
  as informative context under HMRC-REQ-005/007's terminology/semantic-wall
  framework, not as an independently numbered requirement, consistent with
  149O.16's own mechanical accounting. No contract change is proposed;
  this observation is recorded for the next independent-verification phase
  (149O.19) so it is not independently rediscovered as a false N-2 finding.

---

## 3. Current Real Effect Paths (Independently Re-Confirmed Against Live Source)

### 3.1 AG3

```
pcae remote rollback execute <job_id> [--json]      (cli.py:4174-4188, remote_rollback_execute_parser)
  → run_remote_rollback_execute                      (commands/agent.py:2236)
      calls execute_rollback(HarnessPath.cwd(), args.job_id)  — no HATP keywords
  → core.agent.execute_rollback                       (agent.py:5234)
      hatp_evidence_id/hatp_proof/hatp_evidence params (agent.py:5238-5240, all default None)
      if hatp_evidence_id is not None: additive-only hatp_ag_authority call (agent.py:5277-5302) — never gates
      rollback_approval_state precondition (agent.py:5323): "approved" required, else ValueError
      structural preconditions (agent.py:5339-5361): eligibility, revert-mode, clean tree, ancestor commit
  → _run_git_revert(original_commit_sha, ...)          (agent.py:5223, called agent.py:5367) — REAL GIT EFFECT
```

Confirmed live: `hatp_evidence_id`/`hatp_proof`/`hatp_evidence` remain
present at `agent.py:5238-5240` with identical semantics to 149O.14's
reconstruction; `run_remote_rollback_execute` still calls
`execute_rollback` positionally with no HATP keywords
(`commands/agent.py:2236-2244`). Current real caller passes no HATP
evidence; current PB result (when the inert block runs) does not gate
the real effect.

### 3.2 AG5

```
pcae rollback --per-id <per_id> [--dry-run] [--json]  (cli.py:3035-3055, rollback_parser)
  → run_rollback                                       (commands/agent.py:16258)
      calls build_rollback_execution(HarnessPath.cwd(), args.per_id, dry_run=args.dry_run) — no HATP keywords
  → core.agent.build_rollback_execution                (agent.py:93952)
      hatp_evidence_id/hatp_proof/hatp_evidence params (agent.py:93957-93959, all default None)
      if hatp_evidence_id is not None: additive-only hatp_ag_authority call (agent.py:93980-93996) — never gates
      structural preconditions (agent.py:~94006-94097): PER exists/status/payload/ECP/no-in-progress-RER/divergence
      dry_run short-circuit (agent.py:~94052-94065): preview only, no write
  → real file write_bytes/write_text/unlink loop over file_plan (agent.py:~94108-94147) — REAL FILE WRITE/UNLINK EFFECT
```

Confirmed live: identical parameter/line structure to 149O.14's
reconstruction (`agent.py:93952` def, `93957-93959` params). No human-
approval gate exists on AG5 today — only structural PER checks.

For both paths: current HATP kwargs are optional/inert; current real
caller passes no HATP evidence; current PB result (advisory-only, when
reached) does not gate the real effect. This is the exact gap HMRC-001
freezes the closure of.

---

## 4. Critical MC-14 Rule (Restated, Preserved As-Is)

`hatp_ag_authority._evaluate_rollback_permission` constructs its PB
request with `simulation_only=True` unconditionally
(`hatp_ag_authority.py:172`). Under the current runtime posture
(`Observed/observe/unavailable`), POL-005 (`ExecutionDisabledRule`,
`permission_broker_foundation.py:489-497`) denies any request truthfully
marked `simulation_only=False`, but never triggers under
`simulation_only=True` (`ExecutionDisabledRule.evaluate` short-circuits
to not-triggered when `simulation_only`). Therefore:

- `HATP_MANDATORY` does **not** currently imply rollback availability.
- If truthful PB permission is unavailable, the real rollback effect
  **must fail closed**.
- This plan preserves that rule exactly. It designs a truthful
  `simulation_only=False` PB request for the real effect path (§10, Wave
  F) and explicitly plans for that request to resolve `DENY` under the
  current runtime posture — it does **not** plan any advisory-PB bypass,
  any change to POL-005, or any COMP-002 implementation.

---

## 5. Current HATP Production State (Restated)

HATP production: **NOT READY**. Runtime: `Observed / observe /
unavailable`. `B-149O-1..4`: **INDEPENDENTLY VERIFIED AT HATP-GATED
AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED** — this plan does
not strengthen or weaken that status; it remains exactly as-is until a
future 149O.19-class independent implementation verification.

---

## 6. HMRC-REQ-001..085 Traceability Table

Ownership legend — modules: `CUT` = new `hatp_mandatory_cutover.py`
(Wave A); `CONS` = new `hatp_rollback_consumption.py` (Wave B); `AG3`/
`AG5` = `src/pcae/core/agent.py`'s `execute_rollback` /
`build_rollback_execution` (Waves C/D); `CLI` =
`src/pcae/commands/agent.py` + `src/pcae/cli.py` (Wave E); `DOC` = this
plan / contract-identity text, no production code owner; `EXIST` =
existing unmodified module (no change, preserved by construction).
Every requirement appears exactly once as **primary** owner; several also
carry a secondary verification obligation in 149O.19 (not restated per
row where it is simply "independently re-verify this row").

| Req | Normative meaning (compressed) | Primary owner | Failure/behavior | Test owner | Attack(s) | Wave |
|---|---|---|---|---|---|---|
| 001 | Contract governs only mandatory AG3/AG5 rollback consumption | DOC | n/a — scope statement | Planning-completeness test | — | N/A |
| 002 | Does not redefine HSCE/HATP/RAE/PBPA/PBPC/RWMPC | DOC | n/a — scope statement | Contract byte-identity test | — | N/A |
| 003 | References frozen authorities by exact name, no duplicate impl | CONS, CUT | Structural (no parallel impl created) | Wave B/A test modules | — | A, B |
| 004 | Governs consumption only, not general execution capability (COMP-002 separate) | DOC | n/a — scope statement | Planning-completeness test | — | N/A |
| 005 | Frozen terminology table | DOC | n/a — naming discipline | Code review / docstrings in every new module | — | A, B |
| 006 | "Approval" not used informally for evidence/validity/approval_present/PB-ALLOW | CONS, CUT, AG3, AG5 | Structural (vocabulary discipline in code/docs/errors) | Wave B/C/D test modules (string/status vocabulary assertions) | — | A–F |
| 007 | 8 semantic walls not collapsed | CONS, AG3, AG5 | Structural | Assembled 45-attack suite (§9) | 16, 25, 26, 34 | B, C, D, F |
| 008 | Canonical flag `--hatp-evidence-id` on both AG3/AG5 | CLI | n/a — syntax | CLI/migration test module | 23 | E |
| 009 | No alias flag | CLI | Rejected if attempted | CLI/migration test module | — | E |
| 010 | `evidence_id` domain = HSCE-REQ-056 (64-lowercase-hex), rejected pre-path-construction | CONS | Fail closed (`ValueError`/domain error before store access) | Consumption adapter test module | 1 (partially) | B |
| 011 | AG3 CLI syntax `remote rollback execute <job_id> --hatp-evidence-id <id> [--json]` | CLI | n/a — syntax | CLI/migration test module | 23 | E |
| 012 | AG5 CLI syntax `rollback --per-id <id> --hatp-evidence-id <id> [--dry-run] [--json]` | CLI | n/a — syntax | CLI/migration test module | 23 | E |
| 013 | Evidence ID has no authority meaning alone (MC-1) | CONS | Structural | Consumption adapter test module | 16, 17 | B |
| 014 | No implicit evidence selection ("latest" etc. prohibited) | CONS, CLI | Rejected — no such lookup exists | Consumption + CLI test modules | 29, 45 | B, E |
| 015 | Sole loader `HATPEvidenceStore.load`; no arbitrary path/parse/caller envelope | CONS | Structural (no alternate loader) | Consumption adapter test module | — | B |
| 016 | Canonical loaded object exactly `HATPSignedEvidenceEnvelope` | CONS | Structural | Consumption adapter test module | 30, 31 | B |
| 017 | Full 7-step consumption chain, evaluated fresh every attempt | CONS | Fail closed at any step | Consumption adapter test module | 12, 13, 25, 26 | B |
| 018 | 13-member fail-closed load/verification-status enumeration | CONS | Fail closed, every member | Consumption adapter test module | 1, 2, 3, 9, 10 | B |
| 019 | Post-cutover, none of §10's failures fall back to legacy | AG3, AG5 | Fail closed, no fallback | AG3/AG5 integration test modules | 20, 21 | C, D |
| 020 | Unknown/future verification status always fails, never succeeds-by-default | CONS | Fail closed | Consumption adapter test module | — | B |
| 021 | `approval_present` derived exclusively by existing RAE+HATP+substrate 3-term AND | CONS | Fail closed on any internal error | Consumption adapter test module | 4, 7, 8, 11, 36, 37 | B |
| 022 | No duplication of RAE/digest/operation/freshness/revocation/readiness logic | CONS | Structural (calls existing engine only) | Consumption adapter test module | — | B |
| 023 | `approval_present` stays local to adapter/PB construction; no generic reusable `approved=True` | CONS | Structural | Consumption adapter test module | — | B |
| 024 | PB remains sole permission-decision owner | CONS | Structural | Consumption adapter test module | — | B |
| 025 | PB request reuses existing shape (`ACTION_ROLLBACK`, `EXECUTION_CLASS_ROLLBACK`, `COMP-008`, `evidence_available=True`, `approval_present=<derived>`) | CONS | n/a — shape reuse | Consumption adapter test module | — | B |
| 026 | PB `HUMAN_REVIEW` → effect does not proceed | AG3, AG5 | Effect blocked | AG3/AG5 integration test modules | 32 | C, D |
| 027 | PB `DENY` → effect does not proceed | AG3, AG5 | Effect blocked | AG3/AG5 integration test modules | 33 | C, D |
| 028 | PB `ALLOW` alone ≠ execution capability, ≠ sufficient to cross boundary | AG3, AG5 | Structural (see MC-14, req 029) | MC-14 assembled tests | 34 | F |
| 029 | MC-14 — effect-truthful PB requirement; real effect needs truthful `simulation_only=False` + ALLOW | CONS, AG3, AG5 | Fail closed (current POL-005 denies) | MC-14 assembled tests | 34 | F |
| 030 | Contract does not claim COMP-002 implemented; names narrow dependent capability only | DOC | n/a — scope statement | Planning-completeness test | — | N/A |
| 031 | Exactly 3 Consumption Modes | CUT | n/a — vocabulary | Cutover test module | 41, 42 | A |
| 032 | `LEGACY_COMPATIBLE` default; legacy dispatch fully operative | AG3, AG5 (unchanged code) | n/a — preserved | AG3/AG5 integration test modules (legacy-effect regression) | — | C, D |
| 033 | Pre-cutover `--hatp-evidence-id` supplied → advisory-only, never gates | AG3, AG5 | n/a — preserved (existing behavior formalized) | AG3/AG5 integration test modules | — | C, D |
| 034 | `PREPARED` = prerequisites satisfied, not yet activated | CUT | n/a — state definition | Cutover test module | — | A |
| 035 | `PREPARED` dispatch identical to `LEGACY_COMPATIBLE`; no AND-hybrid | AG3, AG5 | n/a — preserved | AG3/AG5 integration test modules | — | C, D |
| 036 | `HATP_MANDATORY`: human authority exclusively via fresh Consumption Attempt; no downgrade/fallback | AG3, AG5, CONS | Fail closed | AG3/AG5 integration + consumption test modules | 20, 21, 23 | C, D |
| 037 | `HATP_MANDATORY` does not guarantee availability | DOC | n/a — restated consequence (§4) | MC-14 assembled tests | 34 | F |
| 038 | Only `LEGACY_COMPATIBLE → PREPARED → HATP_MANDATORY`; no direct skip | CUT | Rejected (direct transition) | Cutover test module | — | A |
| 039 | No reverse transition via ordinary mechanism | CUT | Rejected | Cutover test module | 104 (invalid transition) | A |
| 040 | Monotonicity — no ordinary action causes MANDATORY→LEGACY by deleting/altering local state | CUT | Fail closed (see §17-19) | Cutover test module | 22 | A |
| 041 | `PREPARED → HATP_MANDATORY` only by Protected Activation Authority (Class-B) | CUT | Rejected for non-admin caller | Cutover test module | 41 (agent self-activation) | A |
| 042 | Activation never automatic on readiness alone | CUT | Structural (explicit call required) | Cutover test module | — | A |
| 043 | Cutover Record stored under existing Class-B protected HATP trust root, not `.pcae/` | CUT | Structural | Cutover test module (no-repo-local-authority tests) | 40 | A |
| 044 | Conceptual owning module: new `hatp_mandatory_cutover.py`, distinct from `hatp_ag_authority.py` | CUT | n/a — architecture decision | Cutover test module | — | A |
| 045 | Cutover Record schema v1: `version`, `repository_instance_id`, `mode`, `activated_at`, `activated_by` | CUT | Closed schema | Cutover test module | 42 | A |
| 046 | `version` strict integer; bool rejected | CUT | Rejected | Cutover test module | 42 | A |
| 047 | v1 closed schema: unknown/missing/duplicate-key rejected | CUT | Rejected | Cutover test module | — | A |
| 048 | Record for a different repository/deployment ⇒ not-present-for-this-repo | CUT | Treated as absent, no wrong-deployment activation | Cutover test module | 40 | A |
| 049 | Deletion/corruption ⇒ consult monotonic marker; never silently downgrade | CUT | Fail-closed-mandatory-equivalent if previously activated | Cutover test module | 22, 39 | A |
| 050 | First install (marker absent) ⇒ absence of record = `LEGACY_COMPATIBLE` | CUT | n/a — safe default | Cutover test module | — | A |
| 051 | Record file admin-owned, agent-unwritable, symlink/path-safety checked | CUT | Rejected on symlink/unsafe path | Cutover test module | — | A |
| 052 | Every effect attempt reads Cutover Record fresh; no cache | AG3, AG5, CUT | Structural (no cache) | Cutover + AG3/AG5 test modules | 25, 26, 38 | A, C, D |
| 053 | No OR-authority / no permanent AND-with-legacy prose or code | CUT, AG3, AG5 | Structural | Assembled 45-attack suite | 20, 21 | A, C, D |
| 054 | `PREPARED` prerequisite conjunction (Class-B valid, substrate operational, signing available, impl version present+verified, provenance valid, activation mechanism available) | CUT | n/a — readiness computation | Cutover test module (readiness-checker tests) | — | F |
| 055 | Activation to `HATP_MANDATORY` does not additionally require MC-14 capability to exist | CUT | n/a — explicit non-requirement | Cutover test module | 34 (consequence) | F |
| 056 | `PREPARED` establishes no additional stored authority beyond `mode` field | CUT | Structural (no extra object) | Cutover test module | — | A |
| 057 | `pcae remote rollback approve`, pre-cutover: unchanged | CLI, AG3 (unchanged code) | n/a — preserved | Legacy-approve regression test | — | E |
| 058 | Same command, `PREPARED`: identical to pre-cutover, may print deprecation warning only | CLI | n/a — preserved + optional diagnostic | CLI/migration test module | — | E |
| 059 | Same command, post-cutover: deterministic refusal, no mutation | CLI | Rejected, no mutation | CLI/migration test module | — | E |
| 060 | `rollback_approval_state`, pre-cutover: full legacy authority | AG3 (unchanged code) | n/a — preserved | AG3 integration test module | — | C |
| 061 | `rollback_approval_state`, post-cutover: historical/display only, not consulted by gate | AG3 | Structural (not read as authority) | AG3 integration test module | 20, 21 | C |
| 062 | Pending legacy approvals at cutover require fresh HATP at attempt time | AG3 | Fail closed absent fresh evidence | AG3 integration test module (regression scenario) | — | C |
| 063 | AG3 structural preconditions preserved in every mode | AG3 (unchanged code) | Fail closed if violated (unchanged) | AG3 integration test module (regression) | — | C |
| 064 | AG5 structural preconditions preserved in every mode; HATP is AG5's first approval gate | AG5 (unchanged code + new gate) | Fail closed if violated (unchanged) | AG5 integration test module (regression) | 44 | D |
| 065 | CLI-only enforcement forbidden; gate lives in effect functions | AG3, AG5 | Structural | Direct-call bypass tests | 24 | C, D |
| 066 | AG3 gate placed after structural checks, immediately before `_run_git_revert` | AG3 | Structural placement | AG3 integration test module | 24, 93 | C |
| 067 | AG5 gate placed after structural/divergence checks, immediately before first mutation | AG5 | Structural placement | AG5 integration test module | 24, 44, 94 | D |
| 068 | Direct-call bypass prevented; CLI is transport-only, no crypto/approval logic in CLI | AG3, AG5, CLI | Structural | Direct-call bypass tests | 24 | C, D, E |
| 069 | Inventory every production caller of the effect functions; no un-audited caller | AG3, AG5 | n/a — verification obligation | 149O.19 caller-inventory audit | — | C/D (impl), 149O.19 (verify) |
| 070 | Test seams bypass only via test-only/internal APIs, never production-callable | AG3, AG5, CONS | Structural | All new test modules | — | A, B, C, D |
| 071 | Per-parameter Wave-7 hook disposition (`hatp_evidence_id` retained/mandatory-when-cutover; `hatp_proof`/`hatp_evidence` deprecated, internal/private-only) | AG3, AG5 | Rejected as public caller input once mandatory | AG3/AG5 integration test modules | 30, 31 | C, D |
| 072 | Post-migration public API accepts only `hatp_evidence_id`; no parallel raw-object authority | AG3, AG5 | Structural | AG3/AG5 integration test modules | 30, 31 | C, D |
| 073 | No caller-supplied approval boolean / PB decision / cutover mode / provider override / raw object as authority (closed list) | AG3, AG5, CONS | Structurally absent from signatures | Assembled 45-attack suite | 16, 17, 18, 19 | B, C, D |
| 074 | Mode derived exclusively from protected Cutover Record, read fresh every attempt | AG3, AG5, CUT | Structural | AG3/AG5 + cutover test modules | 22, 39, 40 | A, C, D |
| 075 | Internal consumption-result shape (`evidence_id`, `hatp_status`, `pb_decision`, `reasons`); `approval_present` not generically exposed | CONS | n/a — type design | Consumption adapter test module | — | B |
| 076 | No Consumption Attempt result persisted/reused; repeat attempt reloads/re-verifies | CONS | Fail closed on repeat if state changed | Consumption adapter test module | 25, 26 | B |
| 077 | Evidence deleted/modified/revoked after prior success ⇒ later attempt fails/re-verifies | CONS | Fail closed on retry | Consumption adapter test module | 27, 28 | B |
| 078 | Two valid evidence IDs ⇒ caller must explicitly choose; no auto-selection | CONS, CLI | Rejected (no selection) | Consumption + CLI test modules | 29 | B, E |
| 079 | Pre-cutover evidence usable post-cutover if still fresh/valid (not the same as REQ-062 legacy-state rule) | CONS | n/a — allowed if fresh | Consumption adapter test module | 35 | B |
| 080 | Contract frozen as `HMRC-001 v1.0` | DOC | n/a — identity statement | Contract byte-identity test | — | N/A |
| 081 | Unknown future HMRC-001 version fails closed | DOC | n/a — forward-compatibility statement (no v2 exists yet) | 149O.19 (re-confirm no v2 drift) | — | N/A |
| 082 | Contract implementation-ready (all frozen sections enumerated) | DOC | n/a — readiness statement | Planning-completeness test | — | N/A |
| 083 | B-149O-1..4 close only once all 7 listed conditions are met (future phase) | DOC | n/a — closure-criteria statement | 149O.19 | all 45 | 149O.19 |
| 084 | Self-consistency search performed; no contradictory authority statement found | DOC | n/a — self-consistency statement | Contract byte-identity + planning-completeness tests | — | N/A |
| 085 | No dual authority (no OR/permanent-AND clause) | CUT, AG3, AG5 | Structural | Assembled 45-attack suite | 20, 21 | A, C, D |

**Coverage check (mechanical, to be encoded in the planning-verification
test, §11):** 85/85 requirement IDs appear in the table above exactly
once in the "Req" column (001–085, contiguous, no gaps, no duplicates —
this table's own IDs are re-derived directly from the same mechanical
extraction 149O.16 used, not copied from this plan's prose).

---

## 7. MC-1..MC-14 Traceability Table

| Invariant | Production enforcement point | Test owner | Attack(s) | Wave | Independent-verification obligation |
|---|---|---|---|---|---|
| MC-1 (evidence ID is a locator only) | `CONS` — evidence-ID domain check happens before any load; ID alone never short-circuits to approval | Consumption adapter test module | 16, 17 | B | 149O.19 re-derives that no code path treats a well-formed ID as approval |
| MC-2 (fresh re-verification every attempt) | `CONS` — no `evaluation_time` caching; `CUT` — mode read fresh every attempt | Consumption + cutover test modules | 12, 13, 25, 26, 38 | A, B | 149O.19 re-confirms via direct-call repeat-attempt tests |
| MC-3 (no cached verification/approval/PB result) | `CONS` — `RollbackPermissionEvaluation`-shaped result never persisted (REQ-075/076) | Consumption adapter test module | 25, 26, 27, 28 | B | 149O.19 greps for any persistence of the result type |
| MC-4 (post-cutover no legacy fallback) | `AG3`/`AG5` — mandatory branch never reads `rollback_approval_state`/legacy structural-only path as authority | AG3/AG5 integration test modules | 20, 21 | C, D | 149O.19 exercises legacy-approved + missing/invalid HATP post-cutover |
| MC-5 (caller-supplied approval boolean structurally absent) | `AG3`/`AG5`/`CONS` — no such parameter in any public signature | Assembled 45-attack suite | 16 | B, C, D | 149O.19 inspects signatures directly (`inspect.signature`) |
| MC-6 (only protected Class-B state determines mode) | `CUT` — Cutover Record lives under `HATPTrustStore.production().root`-family storage, never `.pcae/` | Cutover test module | 22, 40 | A | 149O.19 confirms storage path is outside repo-writable tree |
| MC-7 (cutover one-way for ordinary principals) | `CUT` — no reverse-transition API; activation requires Protected Activation Authority | Cutover test module | 41 | A | 149O.19 attempts reversion as an ordinary agent principal |
| MC-8 (AG3/AG5 bind to exact signed operation) | `EXIST` — unmodified operation-binding machinery in `rollback_approval_evidence.py`/`human_approval_trusted_provenance.py`, reused by `CONS` | Consumption adapter test module | 4, 36, 37, 38 | B | 149O.19 re-confirms binding checks fire for the new adapter's calls |
| MC-9 (cross-family evidence cannot authorize) | `EXIST` (operation-family binding), reused by `CONS` | Consumption adapter test module | 5, 6 | B | 149O.19 exercises AG3-for-AG5 and AG5-for-AG3 |
| MC-10 (derived approval always passes through PB) | `CONS` — no direct wire from `approval_present` to effect | Consumption adapter test module | — | B | 149O.19 confirms no `if approval_present: dispatch()` shortcut exists |
| MC-11 (every effectful caller covered, CLI and direct alike) | `AG3`/`AG5` — gate inside the effect function itself | Direct-call bypass tests | 24 | C, D | 149O.19 inventories every caller of `execute_rollback`/`build_rollback_execution` (REQ-069) |
| MC-12 (PB ALLOW ≠ execution capability) | `DOC`/`CONS` — MC-14 gate is separate from and stricter than ALLOW alone | MC-14 assembled tests | 34 | F | 149O.19 re-confirms COMP-002 remains unimplemented and unclaimed |
| MC-13 (signing never changes authority) | `EXIST` — unchanged `pcae hatp sign rollback` (149O.13-verified) | No new test — regression only | — | n/a (pre-existing, re-confirmed not regressed) | 149O.19 re-confirms `pcae hatp sign rollback` still mutates nothing else |
| MC-14 (effect-truthful PB requirement) | `CONS` — real-effect PB request always `simulation_only=False`, structurally derived, never caller-supplied; dry-run/advisory paths always `simulation_only=True` | MC-14 assembled tests | 34 | F | 149O.19 independently attempts a real effect and confirms DENY under current runtime posture, with zero mutation |

**Coverage check:** 14/14 invariants present, each with at least one
concrete production enforcement point and at least one Wave.

---

## 8. 45-Attack Traceability Table

Independently re-enumerated from HMRC-001 §29 (not from the 149O.14
architecture doc's own §30 prose, per the governing instruction not to
trust an intermediate summary — cross-checked and found identical in
content, both counting exactly 45).

| # | Attack | Boundary attacked | Planned defense | Expected result | Test level | Test file | Wave |
|---|---|---|---|---|---|---|---|
| 1 | Missing evidence ID | CONS load | `HATPEvidenceStore.load` raises `EvidenceNotFoundError` | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 2 | Malformed evidence envelope | CONS load | Existing HSCE parser raises `MalformedEvidenceEnvelopeError` | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 3 | Digest mismatch | CONS load | Existing HSCE digest check raises `EvidenceIdDigestMismatchError` | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 4 | Wrong operation | CONS verify | Existing RAE operation-binding check | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 5 | AG3 evidence used for AG5 | CONS verify | Existing operation-family binding | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 6 | AG5 evidence used for AG3 | CONS verify | Existing operation-family binding | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 7 | Wrong repository | CONS verify | Existing repository-identity binding | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 8 | Wrong deployment | CONS verify | Existing deployment binding | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 9 | Expired proof | CONS verify | `HATPVerificationStatus.EXPIRED` | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 10 | Revoked signer | CONS verify | `HATPVerificationStatus.REVOKED_SIGNER` | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 11 | Revoked authority / substrate readiness lost | CONS verify | Existing readiness re-check | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 12 | Decision changed after signing | CONS verify | Existing Decision/Binding digest cross-check, re-run fresh | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 13 | Binding changed after signing | CONS verify | Same digest cross-check | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 14 | Fresh unregistered key | CONS verify | Not in trust store, `UNKNOWN_SIGNER`-class status | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 15 | Forged signer | CONS verify | `INVALID_SIGNATURE`/`INVALID_ATTESTATION` | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 16 | Caller-supplied `approval_present=True` | AG3/AG5/CONS signature | No such parameter exists | Structurally impossible | Unit + signature-inspection | assembled suite | B, C, D |
| 17 | Caller-supplied HATP `VALID` spoof | CONS verify | Verification always re-runs internally | Structurally impossible | Unit | `test_hatp_rollback_consumption.py` | B |
| 18 | Test-provider injection | CONS verify | F-2 closure preserved (no provider param) | Structurally impossible | Unit + signature-inspection | `test_hatp_rollback_consumption.py` | B |
| 19 | Arbitrary trust-store injection | CONS verify | F-2 closure preserved | Structurally impossible | Unit + signature-inspection | `test_hatp_rollback_consumption.py` | B |
| 20 | Legacy-approved + missing HATP evidence, post-cutover | AG3 gate | `rollback_approval_state` not consulted post-cutover | Fail closed | Integration | `test_hatp_ag3_mandatory_integration.py` | C |
| 21 | Legacy-approved + invalid HATP evidence, post-cutover | AG3 gate | Same | Fail closed | Integration | `test_hatp_ag3_mandatory_integration.py` | C |
| 22 | Delete Cutover Record | CUT resolution | Monotonic marker forces fail-closed-mandatory-equivalent | Fail closed, no silent downgrade | Unit | `test_hatp_mandatory_cutover.py` | A |
| 23 | Omit `--hatp-evidence-id` post-cutover | CLI + AG3/AG5 gate | Flag effectively required once mandatory | Rejected before effect | Integration | `test_hatp_cli_migration.py` | E |
| 24 | Direct function-call bypass (skip CLI) | AG3/AG5 gate placement | Gate lives inside effect function itself | Fail closed | Integration (direct call) | `test_hatp_ag3_mandatory_integration.py` / `test_hatp_ag5_mandatory_integration.py` | C, D |
| 25 | Cached previous `VALID` reused | CONS | No cache exists | Structurally impossible | Unit | `test_hatp_rollback_consumption.py` | B |
| 26 | Cached previous PB `ALLOW` reused | CONS | PB always re-evaluated | Structurally impossible | Unit | `test_hatp_rollback_consumption.py` | B |
| 27 | Evidence deleted after prior success, retry | CONS | Reload on every attempt | Fail closed on retry | Unit | `test_hatp_rollback_consumption.py` | B |
| 28 | Evidence modified after prior success, retry | CONS | Digest mismatch on reload | Fail closed on retry | Unit | `test_hatp_rollback_consumption.py` | B |
| 29 | Two valid evidence IDs, none supplied | CONS + CLI | No auto-selection | Rejected | Unit + Integration | `test_hatp_rollback_consumption.py`, `test_hatp_cli_migration.py` | B, E |
| 30 | Old `hatp_proof` bypass attempt | AG3/AG5 signature | Non-authoritative, internal/test-only at most | Rejected | Unit | `test_hatp_ag3_mandatory_integration.py` / `test_hatp_ag5_mandatory_integration.py` | C, D |
| 31 | Old `hatp_evidence` bypass attempt | AG3/AG5 signature | Same disposition | Rejected | Unit | same as #30 | C, D |
| 32 | PB `HUMAN_REVIEW` despite valid HATP | CONS + AG3/AG5 gate | Effect does not proceed | Blocked | Integration | assembled suite | C, D, F |
| 33 | PB `DENY` despite valid HATP | CONS + AG3/AG5 gate | Effect does not proceed | Blocked | Integration | assembled suite | C, D, F |
| 34 | PB `ALLOW` under `simulation_only=True` | CONS (MC-14) | Does not authorize effect | Blocked | Unit + Integration | `test_hatp_mc14_effect_truthful.py` | F |
| 35 | Pre-cutover evidence consumed post-cutover | CONS | Allowed if still fresh/valid | Allowed | Unit | `test_hatp_rollback_consumption.py` | B |
| 36 | Wrong AG3 job | CONS verify | Operation binding | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 37 | Wrong AG5 PER | CONS verify | Operation binding | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 38 | Wrong AG5 `ecp_id` | CONS verify | Operation binding | Fail closed | Unit | `test_hatp_rollback_consumption.py` | B |
| 39 | Cutover-record corruption | CUT resolution | Fail-closed-mandatory-equivalent, never legacy fallback | Fail closed | Unit | `test_hatp_mandatory_cutover.py` | A |
| 40 | Cutover-record wrong repository | CUT resolution | Treated as not-present-for-this-repo | No wrong-deployment activation | Unit | `test_hatp_mandatory_cutover.py` | A |
| 41 | Cutover-record unknown version | CUT resolution | Fail closed, never assume legacy | Fail closed | Unit | `test_hatp_mandatory_cutover.py` | A |
| 42 | Cutover-record boolean version | CUT parser | Rejected | Rejected | Unit | `test_hatp_mandatory_cutover.py` | A |
| 43 | Repository moved/cloned/re-worktreed, evidence reused | CONS verify | Repository/deployment identity binding | Fail closed unless genuinely matching | Unit | `test_hatp_rollback_consumption.py` | B |
| 44 | AG5 divergence-blocking state + valid HATP evidence | AG5 structural check | Structural check still blocks | Blocked | Integration | `test_hatp_ag5_mandatory_integration.py` | D |
| 45 | Evidence exists, no explicit ID supplied | CONS + CLI | No implicit lookup | No effect | Unit + Integration | `test_hatp_rollback_consumption.py`, `test_hatp_cli_migration.py` | B, E |

**Coverage check:** 45/45 attacks present, each with a future test file
and wave; none deferred to "TBD."

---

## 9. Selected Module Architecture

### 9.1 `src/pcae/core/hatp_mandatory_cutover.py` (NEW, Wave A)

Owns, and only owns: the Cutover Mode vocabulary, the Cutover Record
model/parser, protected persistence, mode resolution, activation
validation, and monotonicity. It owns **no** evidence verification, **no**
PB logic, and **no** rollback effects (HMRC-REQ-044).

- **Cutover Mode type (§9 of governing prompt):** a `str, Enum` — matching
  this repository's existing convention for closed, string-serializable
  status vocabularies (e.g. `BootstrapEnvironmentStatus(str, Enum)` in
  `hatp_bootstrap.py:140`, `HATPVerificationStatus` in
  `human_approval_trusted_provenance.py`) — with exactly three members:
  `LEGACY_COMPATIBLE`, `PREPARED`, `HATP_MANDATORY` (HMRC-REQ-031). A bare
  `Literal["LEGACY_COMPATIBLE", "PREPARED", "HATP_MANDATORY"]` is rejected
  as the primary type because the repository's existing precedent for
  closed runtime vocabularies with methods (`.value`, membership checks)
  is `str, Enum`, not a bare `Literal` — a frozen `Literal` remains usable
  as the on-disk JSON field's static type annotation only.
- **Cutover Record model:** a frozen dataclass, `CutoverRecord`, with
  exactly the 5 fields HMRC-REQ-045 freezes: `version: int`,
  `repository_instance_id: str`, `mode: CutoverMode` (`PREPARED` or
  `HATP_MANDATORY` only — `LEGACY_COMPATIBLE` is never itself persisted,
  since HMRC-REQ-050 defines it as the *absence* of a record, not a
  record value), `activated_at: str` (strict lexical ISO-8601 timestamp,
  §9.4 below), `activated_by: str` (protected-authority reference, never
  an agent/session/task ID).
- **Parser:** `parse_cutover_record(document: dict) -> CutoverRecord`,
  closed-schema (HMRC-REQ-047): rejects unknown fields, missing fields,
  and — where the JSON decoder can be configured to detect them —
  duplicate keys (mirroring the existing strict-schema pattern already
  used by `hatp_signed_evidence.py`'s envelope parser and
  `hatp_bootstrap.py`'s registry parser, e.g. `_parse_registry_document`,
  `_parse_deployment_binding`). `version` is validated with an explicit
  `isinstance(value, int) and not isinstance(value, bool)` guard (Python
  `bool` is an `int` subclass) — this is the same strict-integer pattern
  HMRC-REQ-046 requires and mirrors identical guards already present
  elsewhere in this repository's protected-record parsers.
- **Protected storage location:** the same Class-B protected root already
  used by `HATPTrustStore.production()` — i.e.
  `HATPTrustStore.production().root / "cutover-record.json"` — reusing
  the *existing* root-resolution API (`hatp_bootstrap.py:529`,
  `HATPTrustStore.production()`, and its public `.root` property at
  `hatp_bootstrap.py:536`) rather than defining a second, independent
  protected root (HMRC-REQ-043: "map to existing Class-B trust/deployment
  root APIs. Do not create a new environment-controlled protected root.").
  **No modification to `hatp_bootstrap.py` is required** — both the root
  path and a `.root` accessor already exist and are public.
- **Monotonic baseline (HMRC-REQ-049, the most important cutover-state
  design problem):** a second, independently-persisted, write-once file
  under the same protected root — `cutover-activation-marker.json` —
  written exactly once, at the moment of the *first* successful
  `PREPARED → HATP_MANDATORY` activation for a given
  `repository_instance_id`, and never rewritten or deleted by any
  ordinary code path thereafter. Its sole content is
  `{"version": 1, "repository_instance_id": "...", "first_activated_at":
  "..."}`. This is deliberately a **separate file** from the mutable
  Cutover Record (not a field inside it), so that deleting or corrupting
  the Cutover Record alone (attack #22/#39) cannot also erase the
  monotonic proof of prior activation — an attacker with agent-level
  write access to repository-local state cannot reach either file
  (both live under the Class-B protected root, HMRC-REQ-043/051), and an
  attacker who *could* reach the protected root (out of the Threat-A
  model, §28) would have to corrupt two independently-checked files
  identically to fake "never activated," which this plan does not
  attempt to further harden against since it is already outside the
  frozen threat model.
- **Resolution algorithm — `resolve_cutover_mode(root: HarnessPath) ->
  CutoverModeResolution`:**

  ```
  1. Load protected deployment baseline (existing HATPTrustStore /
     repository-identity APIs) — resolve repository_instance_id.
  2. Attempt to read cutover-record.json from the protected root.
     - Path-safety: reject symlink (mirrors hatp_bootstrap.py's
       _reject_symlink pattern, reimplemented locally since that
       function is private to hatp_bootstrap.py — see §9.5 below).
     - If unreadable/absent: go to step 4.
     - If present but unparsable/corrupt: go to step 5 (never step 4).
  3. If parsed successfully:
     - If record.repository_instance_id != current repository_instance_id:
       treat as not-present-for-this-repo -> go to step 4 (HMRC-REQ-048).
     - Else: validate version == 1 (else step 6); mode is
       record.mode (PREPARED or HATP_MANDATORY) -> return that mode.
  4. Record absent (or not-for-this-repo): read the monotonic marker.
     - Marker absent -> mode = LEGACY_COMPATIBLE (first install,
       HMRC-REQ-050).
     - Marker present -> mode = HATP_MANDATORY-fail-closed-equivalent
       (HMRC-REQ-049, "previously activated, record now missing").
  5. Record present but corrupt/unreadable -> read the monotonic marker.
     - Marker absent -> FAIL CLOSED anyway (a corrupt record is never
       treated the same as "absent", even pre-marker — HMRC-REQ-049
       does not distinguish "corrupt" from "missing" for this purpose;
       both consult the marker) -> if marker absent, mode =
       LEGACY_COMPATIBLE is still NOT assumed; instead this is flagged
       as an implementation stop condition (§13, item 8) since a
       corrupt record with no prior-activation proof is an ambiguous
       state HMRC-001 does not explicitly resolve (a genuinely
       first-install deployment cannot organically produce a corrupt
       record, since nothing ever wrote one — so this branch should be
       unreachable in practice; treat it as an internal-consistency
       assertion failure, fail closed, not a silent LEGACY_COMPATIBLE).
     - Marker present -> HATP_MANDATORY-fail-closed-equivalent, same
       as step 4.
  6. Unknown version -> fail closed, never assume legacy (HMRC-REQ-046/
     081-style unknown-version discipline).
  ```

  Returns a typed `CutoverModeResolution(mode: CutoverMode,
  reason: str)`. No caller override parameter exists (HMRC-REQ-074).
- **No cache (HMRC-REQ-052):** `resolve_cutover_mode` performs the full
  read/validate sequence on every call; it is called fresh at every
  effect attempt from inside `execute_rollback`/`build_rollback_execution`
  (§9.3), never once at CLI startup or cached in a module-level variable
  (§ governing-prompt item 112/113: TOCTOU between CLI start and effect
  attempt must resolve to the mode observed *at the effect boundary*).
- **Activation API:** an internal, non-CLI function,
  `activate_hatp_mandatory(*, protected_authority: ProtectedAdminPrincipal,
  ...) -> CutoverRecord`, reachable only through the same Class-B
  protected-admin authority mechanism 149O.6/149O.7 already established
  — this plan does **not** invent a new authority check; it reuses
  whatever principal type that lineage already defines for admin-only
  actions (to be confirmed by direct source reading of the 149O.6/149O.7
  implementation at the start of Wave A, since this plan does not modify
  that code and therefore does not re-derive its exact signature here).
  No public CLI command is planned for activation — HMRC-001 does not
  freeze one, and item 27 of the governing prompt instructs not to invent
  one; the API remains protected/internal until a future deployment-
  tooling phase, if any, explicitly adds one.
- **Prepared-mode creation:** `PREPARED` is a **stored** value in the
  Cutover Record (not purely computed), written by the same
  Protected-Activation-Authority-gated API once the §54 prerequisite
  conjunction holds — HMRC-REQ-056 confirms no *separate* authority
  object is introduced for `PREPARED`, but it is still a real record
  write, not a derived-on-read value, since HMRC-REQ-045's schema has no
  other way to represent "prepared" than storing `mode: "PREPARED"`.
- **Transition validation:** `LEGACY_COMPATIBLE → PREPARED` and
  `PREPARED → HATP_MANDATORY` are the only two writes the activation API
  permits; `HATP_MANDATORY → PREPARED`, `HATP_MANDATORY →
  LEGACY_COMPATIBLE`, and any direct `LEGACY_COMPATIBLE → HATP_MANDATORY`
  are rejected unconditionally (HMRC-REQ-038/039). `PREPARED →
  LEGACY_COMPATIBLE` is **not** frozen one way or the other by HMRC-001 —
  per item 105 of the governing prompt, this plan does not infer an
  answer; it is listed as a stop condition (§13, item 9) requiring a
  contract clarification before Wave A implements that specific
  transition either way. Wave A's activation API will simply not expose
  any `PREPARED → LEGACY_COMPATIBLE` path at all (the conservative
  default — omission, not a guess) until HMRC-001 is amended or a
  companion note resolves it.
- **Atomicity:** record writes use the existing protected-store atomic-
  replace precedent already established for other Class-B protected
  artifacts (write to a temp file under the same protected directory,
  `os.replace` into place) — reusing the pattern, not a new mechanism.
  Concurrent-activation races resolve via the same atomic replace: the
  last writer wins for the *value*, but since only forward transitions
  are permitted and the activation API re-checks current mode
  immediately before writing (no cached prior read, §9.3 TOCTOU
  discipline), a concurrent `PREPARED→HATP_MANDATORY` racing another
  identical transition simply converges on the same end state with no
  downgrade possible; a race between two *different* target transitions
  cannot occur because the only two writable transitions are strictly
  ordered.
- **Activation readiness checker:** `assess_hatp_mandatory_activation_
  readiness(root) -> ActivationReadinessResult` (HMRC-REQ-054-056),
  implemented in Wave F (not Wave A) because two of its six conjuncts —
  "mandatory-consumption implementation version present" and
  "independently verified" — cannot be meaningfully checked until Waves
  B-E exist. It performs no state mutation and must be called fresh
  immediately before any activation attempt (no cached readiness, item
  111 of the governing prompt — TOCTOU between check and write).

### 9.2 `src/pcae/core/hatp_rollback_consumption.py` (NEW, Wave B)

Owns, and only owns: explicit evidence-ID input, `HATPEvidenceStore.load`,
canonical envelope consumption, fresh HATP verification, gated RAE/HATP
approval derivation, PB request construction, and a typed consumption
result. It performs **no** rollback mutation and **no** cutover-mode
resolution (that remains `hatp_mandatory_cutover.py`'s and the effect
functions' concern, §9.3).

- **Does not overload `hatp_ag_authority.py` (item 33 of the governing
  prompt):** `hatp_ag_authority.py` remains completely unmodified. Its
  existing `resolve_ag3_gated_rollback_authority`/
  `resolve_ag5_gated_rollback_authority` continue to serve exactly their
  current role — the pre-cutover/`PREPARED` **advisory-only** evaluation
  path already wired at `agent.py:5277-5302`/`93980-93996`
  (HMRC-REQ-033/HMRC-REQ-035) — unchanged, still `simulation_only=True`
  unconditionally, still accepting raw `hatp_proof`/`hatp_evidence`
  because that advisory path is not the mandatory-consumption path this
  contract governs.
- **New, separate call path for the actual mandatory gate:** the new
  adapter calls the **lower-level** RAE/HATP engine directly —
  `resolve_rollback_approval_evidence_with_hatp`
  (`rollback_approval_evidence.py:1517`) and, transitively,
  `verify_hatp_proof` (`human_approval_trusted_provenance.py:762`) —
  rather than going through `hatp_ag_authority`'s PB-bundling wrapper.
  This is necessary because `hatp_ag_authority._evaluate_rollback_
  permission` hardcodes `simulation_only=True`
  (`hatp_ag_authority.py:172`), which is structurally incompatible with
  MC-14's requirement that a real effect attempt construct a truthful
  `simulation_only=False` request (item 124 of the governing prompt,
  option B: "move PB construction out to HMRC adapter" — selected over
  option A, "add a parameter to the existing hardcoded call," because
  adding a caller-controlled `simulation_only` parameter to
  `hatp_ag_authority.py`'s existing function would create exactly the
  kind of caller-controllable-truthfulness surface HMRC-REQ-073/086
  forbids; keeping the existing function's parameter list and behavior
  frozen, and building the new truthful-request path entirely in the new
  adapter, avoids that risk entirely).
- **Canonical input (HMRC-REQ-034 of governing prompt / item 34):** the
  adapter's public entrypoints accept `evidence_id: str` plus the
  existing per-site operation-context objects AG3/AG5 already construct
  today (`job_id`+`original_commit_sha`+repository state for AG3;
  `per_id`+`ecp_id`+repository state for AG5) — reusing the exact same
  operation-locator shapes `hatp_ag_authority.py`'s existing functions
  already accept, not a new raw dictionary (item 88). No `hatp_proof`/
  `hatp_evidence` parameter is ever accepted from the effect functions —
  those are derived **internally**, from the loaded envelope only.
- **Load / verify / order (item 90):**

  ```
  1. validate evidence_id against HSCE-REQ-056's domain (HMRC-REQ-010) —
     cheap, no I/O.
  2. HATPEvidenceStore.load(evidence_id) -> HATPSignedEvidenceEnvelope
     (existing, unmodified, HMRC-REQ-015).
  3. derive the operation context already available to the caller
     (job_id/per_id/ecp_id/repository state) — no re-derivation from
     the envelope.
  4. resolve_rollback_approval_evidence_with_hatp(..., evaluation_time=now)
     -> runs RAE resolution, verify_hatp_proof, Decision/Binding digest
     cross-check, substrate-readiness check (all existing, unmodified).
  5. derive approval_present via the existing 3-term AND
     (_derive_hatp_gated_approval_present's exact logic, reused, not
     duplicated — HMRC-REQ-021/022).
  6. construct a Permission Broker request via
     build_permission_broker_request (existing shape, HMRC-REQ-025),
     with simulation_only supplied by the *caller context* (the effect
     function tells the adapter whether this is a real attempt or an
     advisory/dry-run one — see §9.3/§9.4 — the adapter itself never
     invents this value, and it is never a raw caller-supplied boolean
     parameter on the *public* entrypoint; it is a fixed, named
     constant selected by which of two internal entrypoints is called:
     `evaluate_for_real_effect(...)` always uses False,
     `evaluate_for_advisory(...)` always uses True — closing item 125's
     "structural, not caller-supplied Boolean" requirement precisely).
  7. PermissionBroker().evaluate(request) -> ALLOW | DENY | HUMAN_REVIEW
     (existing, unmodified).
  8. return a typed HATPRollbackConsumptionResult (§9.2's result type,
     item 87/40) — no effect performed here.
  ```

  Structural precondition note (item 91): step 1's domain check may
  occur before any load, since it is a pure string-format check with no
  side effects; every subsequent step happens in the fixed order above
  on every attempt (no reordering, no step skipped on a "fast path").
- **Failure mapping (item 36/41):** every `HATPEvidenceStoreError`
  subclass, every non-`VALID` `HATPVerificationStatus`, and every
  non-`VALID` RAE result maps to a distinct, closed-vocabulary failure
  reason inside the result type's `reasons` field — never collapsed into
  one generic "denied" string, preserving the 5-layer diagnostic
  separation HMRC-001 §12/architecture §25 requires (evidence-load error
  / verification status / approval-derivation result / PB decision /
  command-level failure).
- **Production dependency closure (item 38, mirroring the existing
  signing F-2 closure pattern):** the adapter's production entrypoints
  resolve `HATPEvidenceStore`, the trust store, and the hardware provider
  **internally** (exactly as `hatp_ag_authority.py:124-125` already does
  for its own call), with a lower-level, test-only internal function
  accepting explicit overrides for deterministic unit tests. No
  production-callable parameter accepts a provider/trust-store/evidence-
  store override (HMRC-REQ-073, F-2 closure preserved).
- **Consumption result type (item 40/87):** `HATPRollbackConsumptionResult`
  — an immutable dataclass with `evidence_id: str`, `hatp_status:
  HATPVerificationStatus`, `pb_decision: str` (one of PB's existing
  decision constants), `reasons: tuple[str, ...]`. `approval_present` is
  **not** exposed on this public type (item 40's "prefer not unless
  contract requires it" — HMRC-001 does not require it); it remains an
  internal intermediate value used only to construct the PB request
  (HMRC-REQ-023). No `executed: bool` field exists on this type — whether
  the effect actually ran is determined by the caller (`AG3`/`AG5`) after
  receiving this result, not by the adapter (HMRC-REQ-075 exact field
  list).
- **No persistence (HMRC-REQ-076):** the adapter is a pure function of
  its inputs and current external state; it stores nothing between
  calls.

### 9.3 AG3 effect-boundary integration (`core/agent.py:execute_rollback`, Wave C)

Exact planned modification, located precisely (item 42):

```
def execute_rollback(root, job_id, hatp_evidence_id=None, hatp_proof=None, hatp_evidence=None):
    ... [UNCHANGED] existing structural preconditions (agent.py:5323-5361):
        rollback_approval_state read, eligibility, revert-mode, clean tree, ancestor commit
    mode_resolution = hatp_mandatory_cutover.resolve_cutover_mode(root)   # NEW, fresh every call
    if mode_resolution.mode == CutoverMode.HATP_MANDATORY:
        if hatp_evidence_id is None:
            raise <new, distinct error> ("HATP mandatory consumption requires --hatp-evidence-id")
        result = hatp_rollback_consumption.evaluate_for_real_effect(
            evidence_id=hatp_evidence_id, job_id=job_id,
            original_commit_sha=original_commit_sha, repository_state=...,
        )
        if result.pb_decision != DECISION_ALLOW:
            raise <new, distinct error> (surfacing result.reasons)
        # only then:
    else:
        # UNCHANGED: existing additive-only advisory block (agent.py:5277-5302),
        # still gated on `if hatp_evidence_id is not None`, still calling
        # hatp_ag_authority.resolve_ag3_gated_rollback_authority, still
        # attaching hatp_authority to the return dict for audit only.
        ...
    _run_git_revert(original_commit_sha, ...)   # UNCHANGED call site, now
                                                  # reached only after the
                                                  # HATP_MANDATORY branch above
                                                  # has allowed it
```

- **AG3 `LEGACY_COMPATIBLE` (HMRC-REQ-032/033):** unchanged. Existing
  advisory-only block preserved verbatim.
- **AG3 `PREPARED` (HMRC-REQ-035):** identical to `LEGACY_COMPATIBLE` —
  the `mode_resolution.mode == HATP_MANDATORY` branch above is the only
  new branch; `PREPARED` falls through to the unchanged `else`.
- **AG3 `HATP_MANDATORY` (HMRC-REQ-036):** exactly the branch shown above
  — evidence ID required, fresh consumption via the new adapter, PB
  `ALLOW` (from a truthful `simulation_only=False` request) required,
  before `_run_git_revert`. Legacy `rollback_approval_state` is not
  consulted in this branch at all (it may still have been read earlier
  in the function for its own unrelated structural-precondition role —
  see the note below — but its value plays no role in this branch's
  decision).

  **Structural-precondition interaction note (resolving HMRC-REQ-063 vs.
  HMRC-REQ-061 precisely):** `rollback_approval_state` is read at
  `agent.py:5323` today purely as the (pre-cutover) approval gate — it is
  not an independent "structural" fact like eligibility/revert-mode/
  clean-tree/ancestor-commit. Wave C's implementation must therefore make
  that specific read **conditional on mode** (only enforced as a gate in
  `LEGACY_COMPATIBLE`/`PREPARED`; read-but-ignored-as-authority in
  `HATP_MANDATORY`, HMRC-REQ-061), while the four genuinely structural
  checks at `agent.py:5339-5361` remain unconditionally enforced in every
  mode (HMRC-REQ-063). This distinction must be encoded explicitly in
  Wave C's code (e.g., moving the `rollback_approval_state` check inside
  the `else` branch above, not leaving it above the mode check) —
  flagged here so Wave C does not accidentally gate `HATP_MANDATORY`
  dispatch on a legacy field it must not consult (HMRC-REQ-036).
- **Raw-hook disposition (HMRC-REQ-071/072, item 47):** `hatp_proof`/
  `hatp_evidence` remain on `execute_rollback`'s signature but become
  **internal/test-only** — the production `HATP_MANDATORY` branch never
  reads them; if both `hatp_evidence_id` and a non-`None` `hatp_proof`/
  `hatp_evidence` are supplied simultaneously in `HATP_MANDATORY` mode,
  Wave C must decide (per HMRC-001's own note that 149O.15 deferred the
  "exact mechanical rejection" to implementation, HMRC architecture §11
  table) to **reject** the call outright (`TypeError`/explicit
  `ValueError`) rather than silently ignore the extra arguments — silent
  ignoring risks a caller believing a raw proof was honored. This
  decision is recorded here as a Wave C implementation commitment, not
  left ambiguous.
- **Direct-call coverage (HMRC-REQ-065/068, item 48):** because the gate
  is inside `execute_rollback` itself, any direct Python call (bypassing
  `commands/agent.py` and `cli.py` entirely) is gated identically. Wave
  C's test module must include at least one test that imports
  `execute_rollback` directly and calls it with no CLI involvement at
  all, in `HATP_MANDATORY` mode, to prove this (attack #24).

### 9.4 AG5 effect-boundary integration (`core/agent.py:build_rollback_execution`, Wave D)

Same shape as §9.3, mapped to AG5's exact structure:

```
def build_rollback_execution(root, per_id, hatp_evidence_id=None, hatp_proof=None, hatp_evidence=None, dry_run=False):
    ... [UNCHANGED] existing structural preconditions (agent.py:~94006-94097):
        PER exists/status/payload/ECP/no-in-progress-RER/divergence
    mode_resolution = hatp_mandatory_cutover.resolve_cutover_mode(root)   # NEW, fresh every call
    if dry_run:
        # UNCHANGED except: MC-14 dry-run semantics (item 95/96) — a dry-run
        # preview never performs a real effect regardless of mode, so no
        # mandatory-consumption gate is needed to *prevent* mutation here;
        # HATP_MANDATORY may still be evaluated for preview/advisory purposes
        # if HMRC-001 requires reporting readiness in the dry-run output, but
        # this plan does not invent a dry-run-specific evidence requirement
        # HMRC-001 does not freeze (see stop condition, item 95 below).
        return <existing preview path, unchanged>
    if mode_resolution.mode == CutoverMode.HATP_MANDATORY:
        if hatp_evidence_id is None:
            raise <new, distinct error>
        result = hatp_rollback_consumption.evaluate_for_real_effect(
            evidence_id=hatp_evidence_id, per_id=per_id, ecp_id=..., repository_state=...,
        )
        if result.pb_decision != DECISION_ALLOW:
            raise <new, distinct error>
    else:
        # UNCHANGED: existing additive-only advisory block (agent.py:93980-93996)
        ...
    for entry in file_plan:            # UNCHANGED loop, now reached only after
        full_path.write_bytes/...      # the HATP_MANDATORY branch above has allowed it
```

- **AG5 `LEGACY_COMPATIBLE`/`PREPARED` (HMRC-REQ-051/052 of architecture,
  HMRC-REQ-035):** unchanged — no human-approval gate, exactly as today
  (AG5 has never had one, §21 of HMRC-001).
- **AG5 `HATP_MANDATORY` (HMRC-REQ-036):** first human-approval gate AG5
  ever gains; existing structural checks (PER/divergence/etc.) are
  preserved unconditionally and are evaluated **before** this gate, per
  HMRC-REQ-064 ("HATP validity never substitutes for or overrides a
  structural check") — attack #44 depends on this exact ordering.
- **AG5 human authority (HMRC-REQ-055 of architecture, item 55):**
  post-cutover, human authority is exclusively HATP-derived; no new PER-
  approval boolean is introduced as an alternate authority.
- **Raw-hook disposition, direct-call coverage:** identical treatment to
  §9.3 for `hatp_proof`/`hatp_evidence` and direct-call bypass proof.

### 9.5 Path-safety helper duplication (explicit, minimized)

`hatp_bootstrap.py`'s `_reject_symlink` (line 253) and
`_default_production_trust_root` (line 226) are both private (leading
underscore) module internals. `hatp_mandatory_cutover.py` needs
equivalent symlink-rejection behavior for its own two files
(`cutover-record.json`, `cutover-activation-marker.json`) under the same
protected root, but the root path and store construction are already
public via `HATPTrustStore.production().root` — only the symlink-check
helper itself is unavailable publicly. Wave A will implement a small,
locally-owned `_reject_symlink`-equivalent function inside
`hatp_mandatory_cutover.py` (a two-line `Path.is_symlink()` check,
identical in behavior, not imported) rather than either (a) modifying
`hatp_bootstrap.py` to export its private helper, or (b) skipping the
check. This is recorded explicitly so a future reviewer does not mistake
the duplication for an oversight — a one-line, well-understood safety
check duplicated once is judged lower-risk than widening
`hatp_bootstrap.py`'s public surface for a single one-line reuse.

---

## 10. MC-14 / PB Truthful-Effect Handling and Wave Decomposition

### 10.1 `simulation_only` provenance (items 124-126)

- `hatp_rollback_consumption.py` exposes exactly two internal entrypoints
  that differ only in a fixed, hardcoded `simulation_only` value passed
  to `build_permission_broker_request`:
  - `evaluate_for_real_effect(...)` — always `simulation_only=False`.
    Called only from the `HATP_MANDATORY` branch inside
    `execute_rollback`/`build_rollback_execution`, immediately before the
    real effect.
  - `evaluate_for_advisory(...)` — always `simulation_only=True`. This is
    **not** newly introduced for real use in this plan; it exists only so
    Wave B's own test suite can exercise the full chain without a
    production real-effect call site depending on it. The actual pre-
    cutover advisory path continues to use the pre-existing
    `hatp_ag_authority.py` functions unchanged (§9.2) — it does not call
    this new adapter at all.
- No public entrypoint accepts `simulation_only` as a caller-supplied
  boolean parameter (closing item 86's "no fake ALLOW arg" and item 125's
  "structural, not caller-supplied" requirement in the same stroke: the
  *only* lever a caller has is which named function it calls, and only
  one of those two is reachable from the real effect boundary).
- **Dry-run semantics (items 95-96):** AG5's `--dry-run` short-circuits
  before the mandatory gate entirely (§9.4) — it never constructs a real-
  effect PB request, truthful or otherwise, because MC-14 governs *real*
  effect attempts and a dry-run is by definition not one. This avoids
  the trap item 95 warns against ("do not force `simulation_only=False`
  for a genuine dry-run"). AG3 has no dry-run mode today; none is added
  (item 96 — "if AG3 has no dry-run, do not invent one").

### 10.2 Current POL-005 consequence (items 70, 82, 138 — accepted, not worked around)

Under the current runtime posture, `evaluate_for_real_effect`'s truthful
`simulation_only=False` request deterministically resolves `DENY` via
POL-005, because `COMP-002` remains `not_implemented`. This plan's
success criterion (item 83) is explicitly **not** "a real rollback effect
succeeds" — it is "the mandatory boundary is real, no bypass exists, and
current policy denial is respected." Wave F's tests must assert `DENY` +
zero mutation for a real-effect attempt under current conditions, and
must **not** be written to expect `ALLOW` (a test that expected `ALLOW`
today would itself be a defect, since it could only pass by weakening
POL-005 or faking a decision). A second, lower-level deterministic test
seam (item 84B) is planned for the *separate* claim "if a future
enforcement capability returned ALLOW, exactly one effect would follow
and no more" — this uses an internal, non-production-reachable
permission-result substitution one layer below the real
`PermissionBroker().evaluate()` call (mirroring the existing signing F-2
dependency-closure test pattern), never a production `allow=True`
parameter (item 86, explicitly prohibited).

### 10.3 Wave decomposition (dependency-derived, not the prompt's suggested split accepted blindly)

The governing prompt's suggested split (149O.18A-F + 149O.19) is adopted
because independent dependency analysis confirms it is already the
minimal-risk ordering:

- **149O.18A — HATP Mandatory Cutover State Foundation.** Depends on
  nothing new (only existing `hatp_bootstrap.py`/`repository_identity.py`
  public APIs). Can be fully implemented and tested without touching
  `agent.py`, without any consumption logic, and without activating
  mandatory mode anywhere real (all activation tests use an isolated
  protected-state fixture, §12). Production files: new
  `src/pcae/core/hatp_mandatory_cutover.py` only.
- **149O.18B — HATP Mandatory Evidence Consumption Adapter.** Depends
  only on existing `hatp_evidence_store.py`/`rollback_approval_evidence.py`/
  `human_approval_trusted_provenance.py`/`permission_broker*.py` — **not**
  on 149O.18A's cutover-mode resolution (§9.2: the adapter takes no mode
  parameter; mode branching is the effect functions' job, Waves C/D).
  Can be fully implemented and tested without any AG3/AG5 wiring.
  Production files: new `src/pcae/core/hatp_rollback_consumption.py` only.
- **149O.18C — AG3 Mandatory Effect-Boundary Integration.** Depends on
  both 149O.18A (cutover-mode resolution) and 149O.18B (consumption
  adapter) existing. Implemented and tested via **direct function calls**
  to `execute_rollback` first (proving the gate with zero CLI
  involvement, attack #24) — no CLI flag is registered yet in this wave.
  Production files: `src/pcae/core/agent.py` (AG3 function only).
- **149O.18D — AG5 Mandatory Effect-Boundary Integration.** Same
  dependency shape as C, applied to `build_rollback_execution`. Can run
  in parallel with C (no shared production file beyond `agent.py`, and
  the two functions are independent regions of that file) but is listed
  after C for reporting clarity, not because of a hard ordering
  dependency. Production files: `src/pcae/core/agent.py` (AG5 function
  only).
- **149O.18E — CLI Evidence-ID Plumbing + Legacy Authority Migration
  Surfaces.** Depends on C and D existing (the flag must plumb into a
  gate that already enforces mode-dependent behavior; wiring the flag
  before the gate exists would create a dead/untested flag). Also covers
  `pcae remote rollback approve`'s mode-dependent disposition
  (HMRC-REQ-057-059), since that command's behavior is cross-cutting
  relative to AG3's gate rather than part of it. Production files:
  `src/pcae/commands/agent.py`, `src/pcae/cli.py`.
- **149O.18F — HMRC Assembled Attack-Matrix / Activation-Guard
  Implementation.** Depends on A-E all existing. Implements
  `assess_hatp_mandatory_activation_readiness` (§9.1, deferred here
  because it needs B-E to exist to check "implementation version
  present"), the truthful `simulation_only=False` real-effect path's
  final integration proof, and the full assembled 45-attack suite run
  against the complete, wired system (as opposed to each wave's own
  narrower unit/integration tests). No new production module; may touch
  `hatp_mandatory_cutover.py` only to add the readiness-checker function
  (still additive, no behavior change to A's existing surface).
- **149O.19 — Independent HMRC Implementation Verification.** Independent
  re-derivation of all 85 requirements/14 invariants/45 attacks against
  the assembled real production code (not against this plan's own
  prose), full caller-inventory audit (HMRC-REQ-069), and the formal
  B-149O-1..4 closure assessment (HMRC-REQ-083).

**Critical wave-ordering guarantees (§7 of governing prompt), confirmed
by the above dependency graph:**

- Cutover-state support (A) can be implemented and independently tested
  without activating mandatory mode anywhere real — confirmed: A's own
  tests use isolated fixtures; nothing in A touches `agent.py`.
- The consumption adapter (B) can be implemented/tested without effect
  wiring — confirmed: B has no dependency on A, C, or D.
- AG3/AG5 effect gates (C/D) can be implemented in a non-activated state
  — confirmed: on the current repository (and every repository until a
  real protected activation occurs), `resolve_cutover_mode` always
  returns `LEGACY_COMPATIBLE`, so C/D's new `HATP_MANDATORY` branch is
  exercised only by tests that inject an isolated fixture record, never
  by the real deployment.
- No wave may accidentally break existing `LEGACY_COMPATIBLE` deployments
  — confirmed: every wave's `LEGACY_COMPATIBLE`/`PREPARED` path is
  either fully unchanged existing code (§9.3/§9.4's `else` branches) or,
  in E's case, the exact pre-existing `approve` command behavior for
  those two modes.
- PB truthful-effect enforcement (F, specifically MC-14) is implemented
  before any wave could plausibly be mistaken for "activation-ready" —
  confirmed: F is last among the implementation waves, and A's activation
  API (built in Wave A) is never exposed to any real caller before F's
  readiness-checker exists to gate it (§9.1's `assess_hatp_mandatory_
  activation_readiness` is itself part of the §54 prerequisite
  conjunction that a real Class-B admin action would need to consult
  before ever calling A's activation API for real — this plan does not
  implement or trigger that real call in any wave).

---

## 11. Test Plan Summary

| Test module | Wave | Covers |
|---|---|---|
| `tests/test_hatp_mandatory_cutover.py` | A | Model, parser, protected path, first-install, prepared, mandatory, monotonicity, corruption, deletion, wrong-repo/deployment, concurrent transitions, no-cache, agent-writability simulation (attacks 22, 39-42) |
| `tests/test_hatp_rollback_consumption.py` | B | Explicit-ID-only, load, fresh verify, RAE/HATP conjunction, PB handoff, raw-object bypass rejection, provider/trust closure, wrong-operation/cross-family/revocation/cached-result attacks (attacks 1-19, 25-31, 35-38, 43, 45) |
| `tests/test_hatp_ag3_mandatory_integration.py` | C | Direct-call + real temp-git-repo effect test, legacy/prepared/mandatory behavior, raw-hook rejection, no-implicit-evidence (attacks 20, 21, 23, 24, 30, 31) |
| `tests/test_hatp_ag5_mandatory_integration.py` | D | Temp-filesystem, zero-write-before-gate proof, divergence-vs-HATP interaction (attacks 24, 30, 31, 44) |
| `tests/test_hatp_cli_migration.py` | E | `--hatp-evidence-id` flag, mode-dependent `approve` behavior, missing-evidence rejection, raw-hook rejection at CLI layer, no-implicit-lookup (attacks 8, 9 numbering per HMRC syntax reqs, 23, 29, 45) |
| `tests/test_hatp_mc14_effect_truthful.py` | F | Real-effect request always `simulation_only=False`; current PB `DENY` + zero effect; no code path ever sets `simulation_only=True` to obtain `ALLOW` for a real effect (attack 34); assembled 45-attack cross-check |
| `tests/test_phase_149o_17_hmrc_implementation_plan_completeness.py` | This phase | Planning-completeness mechanical checks (§12) |

All integration tests use temporary Git repositories / temporary
filesystem fixtures — never the developer's real repository — and an
isolated, test-constructed protected-cutover-record fixture via an
internal test API, never a `mandatory=True` production parameter (items
71, 74-76).

---

## 12. Planning Verification Test (This Phase's Own Deliverable)

`tests/test_phase_149o_17_hmrc_implementation_plan_completeness.py`
mechanically proves, against this plan document and the current
repository state (not by trusting this document's own prose):

1. This plan's §6 table contains exactly 85 rows with `Req` values
   `001`-`085`, contiguous, no gaps, no duplicates (mirrors HMRC-001's own
   85-count, cross-checked against a fresh mechanical extraction of
   `HATP-REQ-###.` from the contract file itself, not a cached count).
2. This plan's §7 table contains exactly 14 rows, `MC-1`-`MC-14`.
3. This plan's §8 table contains exactly 45 rows, `1`-`45`.
4. Every row in §6 has a non-empty "Primary owner" and "Wave" (or `N/A`
   with a documented reason) — no unmapped requirement.
5. Every production file named in §9 (`hatp_mandatory_cutover.py`,
   `hatp_rollback_consumption.py`, `core/agent.py`,
   `commands/agent.py`, `cli.py`) is cited by at least one row in §6, §7,
   or §8 — no file without normative ownership.
6. Every attack in §8 has a non-empty "Test file" and "Wave" — no attack
   deferred to "TBD."
7. `git diff --name-only <phase-entry-commit>..HEAD -- src/pcae/` is
   empty (no production file was touched by this phase).
8. `git diff --stat <phase-entry-commit>..HEAD -- docs/contracts/*.md` is
   empty for all seven contracts (HMRC-001, HSCE-001, HATP-001, RAE-001,
   RWMPC-001, PBPA-001, PBPC-001) — byte-identity.
9. Explicit markers for: cutover deletion/monotonicity coverage (§9.1/§8
   rows 22/39-42), MC-14 coverage (§7 row MC-14, §10.2), AG3/AG5 direct-
   call bypass coverage (§8 row 24, §9.3/§9.4).
10. No `src/pcae/**` file appears in this phase's git diff (redundant
    with #7, encoded as a second, independent check using a different
    extraction method — `git diff --name-status` line-prefix parsing
    rather than `--name-only`, so a defect in one check method is not
    silently mirrored in the other).

This test is structured/marker-based (parsing this Markdown file's
tables programmatically), not prose-only, per the governing prompt's
explicit instruction to avoid brittle prose-only checks.

---

## 13. Implementation Stop Conditions (Restated and Confirmed Applicable)

A future implementation phase covering any wave A-F MUST STOP and seek
contract/architecture clarification, rather than improvise, if:

1. The Cutover Record first-install/deletion distinction (§9.1's
   resolution algorithm, step 5's corrupt-record-with-no-marker branch)
   is reached in practice — this plan asserts it should be structurally
   unreachable, but if a future implementation finds a real code path
   that produces a corrupt record before any marker exists, that is a
   genuine contract gap requiring a companion HMRC-001 clarification
   note, not an improvised default.
2. The Class-B protected storage API (`HATPTrustStore`/`hatp_bootstrap.py`)
   is found, at implementation time, to lack the monotonic-write-once
   property this plan assumes (i.e., if two processes can write
   `cutover-activation-marker.json` non-atomically in a way that loses
   the first write) — implementation must stop and design (or request)
   a stronger primitive rather than accept a race.
3. HMRC timestamps (`activated_at`, `first_activated_at`) cannot be
   parsed strictly without a contract interpretation choice not already
   made in §9.1 (this plan mandates strict lexical validation
   independent of `datetime.fromisoformat`'s CPython-version-dependent
   permissiveness — see §14 below — but any further ambiguity found at
   implementation time is a stop condition).
4. Raw-hook removal (`hatp_proof`/`hatp_evidence` becoming internal-only)
   is found to break an unclassified production caller not identified in
   §3/§9.3/§9.4 of this plan.
5. The effect boundary (`_run_git_revert`/the file-write loop) is found
   to have an additional real production caller not mapped in §3 (HMRC-
   REQ-069's inventory obligation) — 149O.19 must re-confirm this
   exhaustively; if it finds one, that caller needs its own gate design,
   which this plan does not attempt to pre-solve.
6. The HATP verifier API (`verify_hatp_proof`) cannot be consumed by the
   new adapter without weakening any existing provenance guarantee.
7. The PB request cannot structurally derive a truthful `simulation_only`
   value without accepting a caller-supplied override (this plan asserts
   it can, via the two-named-entrypoints design in §10.1 — if a future
   implementer finds this insufficient, that is a stop condition, not
   license to add a boolean parameter).
8. Production code is found to need a caller-supplied approval/PB
   decision for any reason.
9. `PREPARED → LEGACY_COMPATIBLE` transition semantics are needed by a
   real deployment scenario before HMRC-001 clarifies whether that
   transition is permitted (§9.1 explicitly omits it rather than
   guessing).
10. Trust-state changes between HATP verification and the real effect
    (item 116) are found to require a second, adjacent recheck HMRC-001
    does not define — this plan does not invent a second-recheck
    requirement (item 116 instructs not to guess); if a future
    implementation phase's own threat analysis concludes one is
    necessary, that is a stop condition requiring a contract amendment,
    not a unilateral addition.
11. Activation prerequisites cannot be evaluated without implementing
    `COMP-002` semantics this contract does not own (HMRC-REQ-004/030).

---

## 14. Cutover-Record Timestamp Hardening (149O.16.2 Debt, Explicitly Not Inherited)

`149O.12B-Obs-PY39-1` (independently confirmed resolved, 149O.16.2) and
its newly-discovered sibling — CPython 3.9's `datetime.fromisoformat`
accepting a stray character before a valid `+00:00` offset (a malformed
"double-Z"-class input) — both live in narrow, already-scoped repair
targets (`publication/coordinator.py`, `rollback_approval_evidence.py`'s
`_parse_iso_timestamp`). This is repository-wide parser-hardening debt,
explicitly **not repaired here** (out of this phase's scope — this is a
planning phase). Because `hatp_mandatory_cutover.py`'s `CutoverRecord`
introduces a **new**, authority-bearing timestamp field (`activated_at`),
Wave A's implementation MUST NOT reuse either existing permissive
`fromisoformat`-based parser as a precedent. It must instead perform
strict lexical validation (e.g. a regex anchoring the exact expected
`YYYY-MM-DDTHH:MM:SS(.ffffff)?+00:00`/`Z` shape before ever calling
`fromisoformat`) independent of whichever CPython version executes it —
this is called out explicitly because this new field is authority-
bearing (governs `HATP_MANDATORY` activation timing/audit), unlike the
CHGR/RAE timestamps the existing quirk affects, which HMRC-001 doesn't
route through the cutover-record parser at all. `149O.16.2`'s finding is
assigned no new qualified ID here since it already carries the ID
`149O.12B-Obs-PY39-1` for the resolved defect and remains otherwise
unnamed/general for the sibling double-Z quirk in the prior report;
this plan does not invent a new ID, consistent with treating it as
retained, non-blocking, repository-wide debt rather than a new finding
of this phase.

---

## 15. Production File Forecast and Ownership Matrix

| File | New/Modify | Requirements owned | Invariants owned | Attacks covered | Wave | Reason |
|---|---|---|---|---|---|---|
| `src/pcae/core/hatp_mandatory_cutover.py` | NEW | 031-056, 074, 085 (cutover portion) | MC-6, MC-7 | 22, 39-42 | A | Sole owner of cutover mode/record/storage/activation |
| `src/pcae/core/hatp_rollback_consumption.py` | NEW | 006-007, 010, 013-030 (adapter portion), 073, 075-079 | MC-1, MC-2, MC-3, MC-8, MC-9, MC-10, MC-14 | 1-19, 25-31, 34-38, 43, 45 | B | Sole owner of load/verify/derive/PB-request chain |
| `src/pcae/core/agent.py` | MODIFY | 019, 036, 052 (AG3/AG5 read), 061-072, 073-074, 085 (AG3/AG5 portion) | MC-4, MC-5, MC-11 | 20, 21, 23, 24, 30, 31, 44 | C, D | Sole location of both real effect boundaries |
| `src/pcae/commands/agent.py` | MODIFY | 008-009, 011-012, 057-059, 068 | — | 23 | E | Evidence-ID transport + legacy `approve` disposition |
| `src/pcae/cli.py` | MODIFY | 008-009, 011-012 | — | 23 | E | `--hatp-evidence-id` flag registration |
| `src/pcae/core/hatp_ag_authority.py` | **NOT MODIFIED** | n/a (unchanged advisory role only) | — | — | n/a | §9.2 — explicitly kept as the unmodified pre-cutover advisory adapter |
| `src/pcae/core/human_approval_trusted_provenance.py` | **NOT MODIFIED** | n/a (reused by CONS) | MC-8, MC-9 (reused) | — | n/a | Verified engine, reused unchanged (item 123) |
| `src/pcae/core/rollback_approval_evidence.py` | **NOT MODIFIED** | n/a (reused by CONS) | MC-2, MC-8, MC-9 (reused) | — | n/a | Verified engine, reused unchanged |
| `src/pcae/core/hatp_evidence_store.py` | **NOT MODIFIED** | n/a (reused by CONS) | — | — | n/a | Verified engine, reused unchanged |
| `src/pcae/core/hatp_signed_evidence.py` | **NOT MODIFIED** | n/a (reused by CONS) | — | — | n/a | Verified engine, reused unchanged |
| `src/pcae/core/permission_broker.py` / `permission_broker_foundation.py` | **NOT MODIFIED** | n/a (reused by CONS) | MC-10, MC-12 (reused) | 32, 33 | n/a | POL-005/policy vocabulary frozen unchanged |
| `src/pcae/core/hatp_bootstrap.py` | **NOT MODIFIED** | n/a (reused by CUT via public API) | MC-6 (reused) | — | n/a | Existing public `HATPTrustStore.production().root` sufficient, §9.5 |

No file above lacks normative ownership; no requirement/invariant/attack
lacks a file. This matrix is the same information as §6-§9, restated in
file-first order for the required final-report field.

---

## 16. Independent Verification Strategy (149O.19, Reserved)

149O.19 must, independently (not by trusting this plan's own tables):

- Re-derive all 85 requirements, 14 invariants, and 45 attacks directly
  from HMRC-001's text (mirroring 149O.16's own mechanical-extraction
  method), then independently map each to the actual merged production
  code — not to this plan document.
- Reconstruct the actual AG3/AG5 effect call graphs from source, exactly
  as this plan did in §3, to confirm no drift occurred during
  implementation.
- Exhaustively inventory every caller of `execute_rollback`/
  `build_rollback_execution` (HMRC-REQ-069) — a fresh grep-based caller
  audit, not a citation of this plan's §9.3/§9.4 assumption that none
  exist beyond the known two.
- Independently attempt all 45 attack scenarios against the real merged
  code, including at least one genuine direct-function-call bypass
  attempt and one genuine real-effect `simulation_only=False` attempt
  (expected: `DENY`, zero mutation).
- Formally assess B-149O-1..4 closure against HMRC-REQ-083's 7 listed
  conditions and state explicitly which remain unmet (expected, at least
  initially: the "genuine `HATP_MANDATORY` cutover independently
  demonstrated on a protected deployment" condition, since no real
  activation is planned by 149O.18A-F).

---

## 17. Retained Findings (Restated, Unchanged by This Phase)

- **149O.12B-Obs-PY39-1** — INDEPENDENTLY CONFIRMED RESOLVED (149O.16.2).
- **HMRC-001 N-1** — editorial category-index omission of
  HMRC-REQ-083..085 — NON-BLOCKING (149O.16), unchanged.
- **149O.16.2 double-Z CPython 3.9 `fromisoformat` quirk** —
  NON-BLOCKING / repository-wide parser-hardening debt (149O.16.2),
  unchanged; explicitly not to be inherited by the new authority-bearing
  Cutover Record parser (§14 above).
- **Historical monkeypatch fixtures** (149O.13/149O.16.2 lineage) —
  NON-BLOCKING, unchanged, not touched by this phase.
- **149O.5-F-3 / stale boundary tests** — retained exact reconstructed
  status from prior phases, unchanged, not touched by this phase.
- **B-149O-1..4** — remain INDEPENDENTLY VERIFIED AT THE HATP-GATED
  AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED, unchanged.
- **New (149O.17, informational only, not a numbered finding):** §28's
  Threat Model header line's informal re-use of the `HMRC-REQ-080` label
  (§2 above) — recorded so 149O.19 does not independently rediscover it
  as a false new defect.

---

## 18. Plan Verdict

```
HATP MANDATORY PRODUCTION CONSUMPTION IMPLEMENTATION PLAN: COMPLETE
— READY FOR BOUNDED IMPLEMENTATION
```

All 85 requirements, 14 invariants, and 45 attacks are mapped to a
concrete module, function, test file, and implementation wave. No
authority-sensitive decision is left for implementation to improvise,
except the explicitly enumerated stop conditions (§13), each of which
requires a contract clarification rather than an improvised default, and
none of which blocks starting Wave A.

## 19. Recommended Next Phase

**149O.18A — HATP Mandatory Cutover State Foundation.** Dependency
analysis (§10.3) confirms cutover-state support is the correct base
layer: it depends on nothing new, blocks nothing else from being
independently testable, and is the layer every other wave (B, and
downstream C/D's mode resolution call) needs first. This plan does
**not** authorize 149O.18B-F in advance — each subsequent wave should be
proposed and scoped as its own governed phase once the prior wave is
independently verified complete.

## 20. Final Confirmations

No production source (`src/pcae/**`) was modified this phase. HMRC-001
v1.0, HSCE-001 v1.1, HATP-001 v1.0, RAE-001 v1.0, RWMPC-001 v1.0,
PBPA-001 v1.0, and PBPC-001 v1.2 all remain byte-unchanged. No Cutover
Record implementation was created. No AG3/AG5 mandatory consumption was
implemented. No legacy rollback behavior changed. No Permission Broker
behavior changed. `POL-005` remains unchanged. No `COMP-002` capability
was implemented. No rollback dispatch behavior changed. No Class-B
provisioning occurred. No HATP production activation occurred. Current
deployment remains `LEGACY_COMPATIBLE`-equivalent (no Cutover Record
exists anywhere real). B-149O-1..4 remain INDEPENDENTLY VERIFIED AT THE
HATP-GATED AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED. HATP
production remains NOT READY. Runtime remains Observed / observe /
unavailable.

**Recommended next phase: 149O.18A — HATP Mandatory Cutover State
Foundation.**
