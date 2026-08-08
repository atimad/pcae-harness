# Phase 149O.16 — HATP Mandatory Production Consumption Contract Independent Verification

**Phase type:** Independent contract verification only. No `src/pcae/**`
file, and no contract file (HMRC-001 or any upstream contract), was
modified to produce this document.

**Subject:** `HMRC-001 v1.0` — `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
(frozen by Phase 149O.15, 945af762).

---

## 1. Baseline

Confirmed by direct command execution at phase start:

- `git status --short`: clean. `origin/main..HEAD`: 0 commits.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — 7 pre-existing `tasks/done/` vs
  `tasks/DONE.md` entries predating this phase (task-lifecycle hygiene
  debt, unrelated to HMRC-001; not remediated here, outside this phase's
  allowed-file scope).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`; Permission
  Broker status `execution_unavailable`.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.15`: 149O.15 confirmed `completed`/`complete`/pushed,
  reconciliation `status: reconciled`, `Mutation: none (inspection only)`.
- `git diff --stat 8360bd18..HEAD -- docs/contracts/*.md`: exactly one file
  added (`HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`, 1023 lines,
  1023 insertions). All six upstream contracts (HSCE-001 v1.1, HATP-001
  v1.0, RAE-001 v1.0, RWMPC-001 v1.0, PBPA-001 v1.0, PBPC-001 v1.2) show
  zero diff — byte-unchanged.

Confirmed: HMRC-001 v1.0 present, status `FROZEN — READY FOR INDEPENDENT
CONTRACT VERIFICATION (not VERIFIED)`. HATP production `NOT READY`.
Runtime `Observed / observe / unavailable`.

---

## 2. Contract Identity and Inventory (Independently Reconstructed)

- **ID/Version:** `HMRC-001`, `v1.0` — confirmed at document header (§0)
  and versioning section (§30, HMRC-REQ-080). No conflicting name/version
  found anywhere else in the body.
- **Requirement inventory:** mechanically extracted every `**HMRC-REQ-###.`
  occurrence: **85 unique IDs, HMRC-REQ-001..085, strictly sequential, no
  gaps, no duplicates** (verified by sort+diff against the expected
  1..85 sequence, not by trusting the document's own prose).
- **Security invariants:** mechanically extracted every `**MC-#` bullet in
  §27: **exactly MC-1..MC-14, no gaps, no duplicates.**
- **Attack matrix:** mechanically counted table rows in §29 matching
  `^| # |`: **exactly 45 rows**, numbered 1..45 with no duplicate numbers,
  every row carrying an explicit "Expected Result" and a citing
  `HMRC-REQ`/`MC` ID.

**Finding N-1 (non-blocking, editorial).** §26's "Requirement Inventory —
Category Index" table only categorizes HMRC-REQ-001 through HMRC-REQ-082
contiguously; it omits HMRC-REQ-083 (§32, B-149O-1..4 closure criteria),
HMRC-REQ-084 and HMRC-REQ-085 (§33, self-consistency statement) from the
index table, even though those three requirements are substantively
defined in the body and correctly counted in the 85-total inventory. This
is an index-completeness gap only — no requirement is missing, contradicted,
or ambiguous; it does not affect any authority, gate, or bypass question.
Non-blocking.

---

## 3. Contract Ownership Boundary and Cross-Contract Compatibility

Independently compared HMRC-001 against HSCE-001 v1.1, HATP-001 v1.0,
RAE-001 v1.0, RWMPC-001 v1.0, PBPA-001 v1.0, PBPC-001 v1.2:

- HMRC-001 does not redefine HSCE evidence-ID content-addressing
  (`HATPEvidenceStore.load(evidence_id)` is referenced by exact name,
  §9/§14 — confirmed against real source, §5 below).
- Does not redefine HATP-001's `HATPVerificationStatus` vocabulary — HMRC-
  REQ-018's 13-member fail-closed list was independently checked against
  `human_approval_trusted_provenance.py:663-684` (`VALID`, `MISSING`,
  `MALFORMED`, `INVALID_SIGNATURE`, `UNKNOWN_SIGNER`,
  `UNAUTHORIZED_SIGNER`, `REVOKED_SIGNER`, `INVALID_ATTESTATION`,
  `USER_PRESENCE_NOT_PROVEN`, `WRONG_OPERATION`, `WRONG_REPOSITORY`,
  `WRONG_DEPLOYMENT`, `EXPIRED`) — **exact match**, no member added,
  removed, or renamed.
- Does not redefine RAE-001 Decision/Binding semantics — HMRC-REQ-021's
  three-term conjunction was checked against the real
  `_derive_hatp_gated_approval_present` (`rollback_approval_evidence.py:
  1489-1514`) — exact match: `rae_approval_present is True AND hatp_status
  is VALID AND activation_operational is True`, fail-closed (`False`) on
  any other combination, including internal error (the enclosing
  `resolve_rollback_approval_evidence_with_hatp`'s bare `except Exception`
  at line 1625).
- Does not redefine PBPA-001/PBPC-001 decision vocabulary or POL-004/
  POL-005. HMRC-REQ-029/MC-14's central claim — that a request truthfully
  marked `simulation_only=False` resolves `DENY` via POL-005 given the
  current runtime posture — was independently re-derived from
  `ExecutionDisabledRule.evaluate` (`permission_broker_foundation.py:
  501-518`): `if request.simulation_only: return _not_triggered(...)`;
  otherwise unconditional `DECISION_DENY`, `decision_reason=
  "execution_boundary_unavailable"`, docstring "Unconditionally active by
  construction (NG-025)". This check is **field-driven only** — it does
  not branch on `action_type`/`execution_class`/`requested_component` —
  so PBPC-REQ-037A's finding (independently confirmed for `pcae push`
  requests specifically, PERMISSION_BROKER_PRODUCTION_CONSUMPTION_
  CONTRACT.md:566-580, itself citing PBPA-REQ-068's "`simulation_only` is
  never an applicability input... universal") generalizes to rollback
  requests exactly as HMRC-001 claims, without contradicting or
  reinterpreting PBPC-001. This is a valid application of an existing,
  frozen, universal rule to a new request shape — not a redefinition.
- Does not overclaim `COMP-002`/`COMP-008`: confirmed no
  `hatp_mandatory_cutover.py` module exists in `src/pcae/` (only an
  unrelated `cltr_cutover` schema directory for a different subsystem);
  confirmed no Cutover Record artifact exists in this deployment; POL-005
  remains `implementation_status = POLICY_STATUS_IMPLEMENTED` and
  unconditionally active — `COMP-002` genuinely `not_implemented` as
  claimed.
- RWMPC-001's `EXECUTION_CLASS_ROLLBACK` classification (§8.3,
  `REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md:246-271`,
  binding AG3+AG5 to `ACTION_ROLLBACK`/`EXECUTION_CLASS_ROLLBACK`) is
  referenced, not altered, by HMRC-REQ-025.

No Blocking cross-contract conflict found.

---

## 4. Semantic Walls, Evidence Syntax, Canonical Chain (§5-9)

The eight semantic-wall distinctions in HMRC-REQ-007 were searched for
contradiction across the full document (per §33's own self-consistency
statement, independently re-run rather than trusted): no clause anywhere
collapses `evidence exists` into `evidence valid`, `approval_present` into
`PB ALLOW`, or `PB ALLOW` into `capability`/`executed`. Confirmed clean.

`--hatp-evidence-id` (HMRC-REQ-008/009) is the sole named flag; no
`--hatp-evidence`, `--evidence-id`, or `--evidence-file` alias appears
anywhere in the document. Cross-checked against the *current* CLI grammar
(`cli.py`): `pcae remote rollback execute <job_id> [--json]` (no
`--hatp-evidence-id` flag exists yet — correctly described by HMRC-REQ-011
as the *frozen future* syntax, not a claim about today's CLI) and `pcae
rollback --per-id <per_id> [--dry-run] [--json]` similarly. Both match
HMRC-REQ-011/012 exactly, including which existing flags (`--json`,
`--dry-run`) are retained.

Canonical loader: `HATPEvidenceStore.load(evidence_id) ->
HATPSignedEvidenceEnvelope` (`hatp_evidence_store.py:149-174`) —
independently confirmed explicit-ID-only (no `latest`/`newest`/glob
method exists anywhere on the class; the module docstring itself states
"there is deliberately no `exists()`, `latest()`, `list_latest()`...
method"), symlink-refusing, and evidence-ID-domain-validated
(`validate_evidence_id`, `hatp_signed_evidence.py:100-112`: 64-lowercase-
hex regex, `InvalidEvidenceIdError` otherwise) before any path is
constructed — exact match to HMRC-REQ-010/014/015/016.

---

## 5. Old-Hook Disposition and Effect-Boundary Placement (§22-23)

Independently inspected the real, current (pre-149O.16, pre-implementation)
`execute_rollback` (`agent.py:5234-5391`) and `build_rollback_execution`
(`agent.py:93952-94180ish`):

- Both currently accept `hatp_evidence_id`/`hatp_proof`/`hatp_evidence` as
  optional keyword-only Wave-7 parameters. When `hatp_evidence_id` is
  supplied, the HATP/RAE/PB evaluation is computed and attached under
  `result["hatp_authority"]` — **purely additive**; it does not gate the
  git-revert / file-write-unlink dispatch, which remains governed solely
  by the existing pre-Wave-7 structural preconditions. When omitted (every
  real caller today), no HATP/PB evaluation runs at all.
- The single production caller of each: `commands/agent.py:2238`
  (`execute_rollback(HarnessPath.cwd(), args.job_id)`) and
  `commands/agent.py:16259` (`build_rollback_execution(HarnessPath.cwd(),
  args.per_id, dry_run=args.dry_run)`) — **neither passes
  `hatp_evidence_id`**, confirming "real callers pass none" and that the
  CLI does not yet expose `--hatp-evidence-id` at all.
- Repo-wide grep for all callers of `execute_rollback(`/
  `build_rollback_execution(` outside `tests/` found exactly these two
  production call sites, plus one unrelated, differently-signatured
  function of the same short name in `cltr_migration.py`
  (`rehearsal_rollback.execute_rollback(request=..., migration_root=...)`)
  — a distinct CLTR migration-rehearsal mechanism, not an AG3/AG5 rollback
  effect-boundary caller, and therefore out of HMRC-REQ-069's scope. **No
  un-audited additional production caller exists.**
- The real effect calls are exactly where HMRC-001 says: `_run_git_revert`
  (`agent.py:5223-5231`, called at line 5367, after all structural
  preconditions at 5323-5365) for AG3; the `write_text`/`write_bytes`/
  `unlink` loop over `file_plan` (`agent.py:94103-94149`, after the
  divergence check at 94050 and PER-status/payload/in-progress checks at
  94014-94047) for AG5. Today both run **unconditionally** once structural
  checks pass — confirming HMRC-REQ-065/066/067's premise (no mandatory
  gate exists yet at this location) and that a future implementation has
  exactly one, unambiguous insertion point per function.

This is a correct, source-verified description of the *current* state a
*future* implementation must change — HMRC-001 makes no claim that the
gate exists today, and none was found to exist.

---

## 6. MC-1 .. MC-14 — Independent Verdicts

| Invariant | Verdict | Basis |
|---|---|---|
| MC-1 (evidence ID is locator only) | CONFORMS | HMRC-REQ-013/014; no clause treats a syntactically valid ID as approval. |
| MC-2 (fresh verification every attempt) | CONFORMS | HMRC-REQ-017/052/076; `resolve_rollback_approval_evidence_with_hatp` performs no caching, takes `evaluation_time` as a required caller-supplied parameter, never reads a stored prior result. |
| MC-3 (no cached verification/approval/PB) | CONFORMS | HMRC-REQ-075/076; `HATPIntegratedApprovalEvidence`/`GatedRollbackAuthorityResult` are per-call return values only, never persisted for reuse in current source. |
| MC-4 (no post-cutover legacy fallback) | CONFORMS | HMRC-REQ-019/036/061; no clause found (§33 search) permitting fallback after `HATP_MANDATORY`. |
| MC-5 (caller approval bool non-authoritative) | CONFORMS | HMRC-REQ-073; independently confirmed structurally absent today — `resolve_ag3/ag5_gated_rollback_authority` and `_evaluate_rollback_permission` have no `approval_present` parameter of their own; the fact is derived internally only. |
| MC-6 (protected state alone determines mode) | CONFORMS | HMRC-REQ-041/043/074; no Cutover Record or `hatp_mandatory_cutover.py` exists yet — the requirement is prospective and unambiguous about *where* mode must live (Class-B protected root, not `.pcae/`). |
| MC-7 (one-way cutover) | CONFORMS | HMRC-REQ-038-040; reverse transitions explicitly forbidden to any ordinary-runtime mechanism. |
| MC-8 (exact AG3/AG5 operation binding) | CONFORMS | Reused, unmodified RAE/HATP operation-binding logic (HMRC-REQ-022); not re-implemented by HMRC-001. |
| MC-9 (cross-family rejection) | CONFORMS | Same reuse; attacks 5/6 in §29 map directly to it. |
| MC-10 (approval always through PB) | CONFORMS | HMRC-REQ-024; confirmed in source — `resolve_ag3/ag5_gated_rollback_authority` always calls `_evaluate_rollback_permission` → `PermissionBroker().evaluate(...)`; the derived fact is never wired directly to dispatch (dispatch today isn't even gated by it at all, consistent with "not yet implemented"). |
| MC-11 (every effectful caller covered) | CONFORMS | HMRC-REQ-065/068/069; independently confirmed exactly one production caller per function (§5 above), and the gate is specified at the function itself, not the CLI. |
| MC-12 (PB ALLOW ≠ execution capability) | CONFORMS | HMRC-REQ-028/030; explicit, and consistent with the module docstring's own restatement ("HATP operational is not PCAE Runtime Execution capability"). |
| MC-13 (evidence creation never changes authority) | CONFORMS | HSCE-001's store `publish()` grants no approval (module docstring, confirmed at `hatp_evidence_store.py:14-23`); HMRC-001 does not contradict this. |
| MC-14 (Effect-Truthful PB Requirement) | CONFORMS | HMRC-REQ-029; independently re-derived from source (§3 above) — today's `hatp_ag_authority.py:172` hardcodes `simulation_only=True` unconditionally, and POL-005 fires unconditional `DENY` whenever `simulation_only=False` given the current runtime posture. The frozen rule (no real effect on a `simulation_only=True` result) is consistent with, not contradicted by, every other PB-related clause in the document (§106/150 search below). |

**MC cross-consistency (item 132).** MC-10 + MC-11 + MC-14 read together
require: HATP/RAE derive the input fact → PB decides permission → a real
effect additionally requires a *truthful* PB permission → none of this
implies general runtime execution capability (MC-12). No contradiction
found; HMRC-REQ-030 explicitly disclaims the `COMP-002` overclaim MC-12
would otherwise risk.

---

## 7. Cutover State Model, Storage, and Monotonicity (§13-19, items 39-68)

- **States:** exactly `LEGACY_COMPATIBLE`, `PREPARED`, `HATP_MANDATORY`
  (HMRC-REQ-031) — no fourth implicit mode found anywhere in the text.
- **`LEGACY_COMPATIBLE`:** legacy dispatch fully operative; HATP evidence
  if supplied is advisory-only (HMRC-REQ-032/033) — resolves the "pre-
  cutover evidence supplied" question unambiguously as advisory, never
  authoritative.
- **`PREPARED`:** independently the most safety-critical clause to check
  for accidental dual authority. HMRC-REQ-034/035 state dispatch behavior
  is *identical* to `LEGACY_COMPATIBLE` — no additional AND-condition, no
  rehearsal requirement, no advisory-turned-authoritative branch. HMRC-
  REQ-053 explicitly forbids both an OR-authority and a permanent-AND
  model. This is unambiguous: `PREPARED` is a pure readiness marker with
  zero behavioral effect of its own. No ambiguity found.
- **`HATP_MANDATORY`:** legacy has zero authority (HMRC-REQ-036); missing/
  invalid evidence fails closed; no downgrade/fallback (HMRC-REQ-039/040).
- **Forward transitions:** `LEGACY_COMPATIBLE → PREPARED → HATP_MANDATORY`
  only; a direct `LEGACY_COMPATIBLE → HATP_MANDATORY` jump is explicitly
  forbidden (HMRC-REQ-038) — unambiguous.
- **Reverse transitions:** explicitly unavailable to any ordinary
  mechanism (HMRC-REQ-039); reversion is out of this contract's scope by
  design, not left ambiguous.
- **Storage:** Class-B protected root, distinct module
  (`hatp_mandatory_cutover.py`, not yet implemented — confirmed absent),
  agent-unwritable, symlink-checked (HMRC-REQ-041/043/044/051) —
  sufficiently concrete for an implementer (exact schema below).
- **Schema (v1, closed):** `version` (strict int, bool rejected),
  `repository_instance_id`, `mode`, `activated_at`, `activated_by`
  (HMRC-REQ-045-047) — closed-schema (unknown/missing/duplicate-key
  rejection), matching the repository's existing strict-schema pattern
  already independently observed elsewhere in this codebase (e.g.
  `validate_evidence_id`'s own `isinstance(value, bool)` pre-check
  pattern at `hatp_signed_evidence.py:122`, reused by analogy).
- **Wrong repository/deployment (items 53-54):** HMRC-REQ-048 explicitly
  states a record naming a different repository is treated as *not
  present for this repository* — and explicitly cross-references
  HMRC-REQ-049 to forbid this being misread as "never activated" (the
  precise trap item 53 asks about). No ambiguity: a foreign-named record
  cannot cause either wrong-deployment activation or accidental legacy
  downgrade.
- **Deletion/corruption (items 55-60, the highest-value monotonicity
  check):** HMRC-REQ-049 is the load-bearing clause. It requires a
  *second*, independently-monotonic, write-once marker (distinct from the
  mutable Cutover Record) in the existing Class-B protected deployment
  baseline, used specifically to distinguish "never activated" (record
  absence → `LEGACY_COMPATIBLE`, HMRC-REQ-050, first-install case) from
  "previously activated, record now missing/corrupt" (→ fail-closed-
  `HATP_MANDATORY`-equivalent, never a downgrade). This is not merely
  asserted prose ("cutover is one-way") — it names a concrete second
  storage primitive and freezes its required semantic role, satisfying
  item 58's "mechanically supports" bar. If a future implementation
  cannot build such a marker from a single file, HMRC-REQ-049's closing
  sentence requires it to freeze a design that can before implementation
  proceeds — this is a implementation-readiness gate, not an ambiguity in
  the contract itself.
- **Mode caching (§61) / multi-process (§62):** HMRC-REQ-052 requires
  fresh reads on every attempt, no process-lifetime cache — compatible
  with concurrent processes by construction (no shared in-memory state is
  specified or implied).
- **Activation authority (§63-65):** Class-B Protected Activation
  Authority only — explicitly not an agent, CLI caller, env var, or
  repo-writable file (HMRC-REQ-041). Activation is always explicit
  (HMRC-REQ-042) — readiness never silently flips to activation.
  Prerequisites are itemized as a concrete six-item list (HMRC-REQ-054),
  not a vague "ready."
- **MC-14 prerequisite question (item 66):** HMRC-REQ-055 directly
  answers this: activation to `HATP_MANDATORY` does **not** additionally
  require the MC-14 execution-enforcement capability to exist —
  Protected Activation Authority may activate while it's absent, with the
  explicit, named consequence (rollback fails closed until it exists).
  This is internally consistent with MC-14/HMRC-REQ-037, not
  contradictory.

No Blocking finding in this section.

---

## 8. Legacy Command/Field Disposition, Structural Preconditions (§20-21)

`pcae remote rollback approve` pre-cutover/PREPARED/post-cutover
dispositions (HMRC-REQ-057-059) and `rollback_approval_state`'s pre/post-
cutover dispositions (HMRC-REQ-060-061) are each given one exact,
unambiguous behavior per mode — no "may be used either way" language
found. Pending-legacy-approval-at-cutover (HMRC-REQ-062, item 73) is
explicit: fresh HATP evidence is required regardless of a pre-cutover
legacy approval; authority is evaluated at effect-attempt time, never
grandfathered.

AG3/AG5 structural preconditions (HMRC-REQ-063/064) are explicitly and
repeatedly distinguished from human-approval authority, and explicitly
stated to remain required in every Consumption Mode — independently
confirmed against source: AG3's ancestor/clean-tree/eligibility checks
(`agent.py:5339-5365`) and AG5's PER-status/payload/in-progress/divergence
checks (`agent.py:94014-94057`) are structurally separate from, and
precede, any HATP evaluation in the current code, and HMRC-001 does not
propose collapsing them (item 44's divergence-vs-valid-HATP-evidence
attack — HMRC-REQ-064 is explicit that a structural check is never
overridden by HATP validity).

---

## 9. Forbidden Caller Inputs and Threat Model (§24, §28)

HMRC-REQ-073's closed list (caller-supplied approval boolean, PB decision,
cutover mode, provider/trust-store override, raw proof/evidence object)
was checked against the real current signatures of
`resolve_ag3_gated_rollback_authority`/`resolve_ag5_gated_rollback_
authority`/`_evaluate_rollback_permission` (`hatp_ag_authority.py`): none
of these five forbidden inputs exists as a parameter on any of them today
— the F-2 closure (no `hatp_provider`/`hatp_trust_store` parameter) is
structural, not a runtime check, exactly as the module's own docstring
claims and as independently confirmed by reading the signatures.

Threat-A capabilities (HMRC-REQ-080) were independently reconstructed and
found consistent with the existing 149O.6/149O.7 Class-B architecture
this contract was told to compare against: the agent can edit the
repository/evidence files, choose evidence IDs, invoke commands, call
public functions directly — and cannot write protected Class-B state,
forge hardware signatures, or substitute the production provider/trust
store. No new impossible trust root introduced.

---

## 10. Consumption Result, No Persistence, No Reuse (§25, items 75-79)

HMRC-REQ-075's output shape and HMRC-REQ-076/077 (no persisted result, no
cached success carried forward across evidence mutation) are consistent
with current source: `GatedRollbackAuthorityResult`/
`HATPIntegratedApprovalEvidence` are plain frozen dataclasses returned per
call, never written to disk or held across invocations anywhere in
`hatp_ag_authority.py` or `rollback_approval_evidence.py`. HMRC-REQ-079
(pre-cutover evidence usable post-cutover if still fresh/valid) is
explicitly and correctly distinguished from HMRC-REQ-062 (legacy approval
state never grandfathered) — these are two different objects (HATP
evidence vs. legacy approval state) and the contract does not conflate
them.

---

## 11. Full 45-Attack Matrix — Independent Reconstruction

Reproduced independently from HMRC-001 §29 itself (not from the prompt's
list, not from 149O.15's test names), cross-checked against the
requirement(s) each cites and, where the underlying mechanism is already
implemented, against real source:

| # | Attack | Independently-verified expected result | Conforms |
|---|---|---|---|
| 1 | Missing evidence ID | `EvidenceNotFoundError` — confirmed real (`hatp_evidence_store.py:165`) | Yes |
| 2 | Malformed evidence envelope | `MalformedEvidenceEnvelopeError` via `parse_hatp_signed_evidence` | Yes |
| 3 | Digest mismatch | `EvidenceIdDigestMismatchError` | Yes |
| 4 | Wrong operation | Fail closed via operation binding (reused RAE logic) | Yes |
| 5 | AG3 evidence used for AG5 | Fail closed, MC-9 | Yes |
| 6 | AG5 evidence used for AG3 | Fail closed, MC-9 | Yes |
| 7 | Wrong repository | Fail closed via repository-identity binding | Yes |
| 8 | Wrong deployment | Fail closed via deployment binding | Yes |
| 9 | Expired proof | `HATPVerificationStatus.EXPIRED` — confirmed real member | Yes |
| 10 | Revoked signer | `REVOKED_SIGNER` — confirmed real member | Yes |
| 11 | Revoked authority / readiness lost | Fail closed via readiness re-check | Yes |
| 12 | Decision changed after signing | Fail closed via digest cross-check — confirmed real (`rollback_approval_evidence.py:1601-1607`) | Yes |
| 13 | Binding changed after signing | Same digest cross-check | Yes |
| 14 | Fresh unregistered key | `UNKNOWN_SIGNER`-class status — confirmed real member | Yes |
| 15 | Forged signer | `INVALID_SIGNATURE`/`INVALID_ATTESTATION` — confirmed real members | Yes |
| 16 | Caller-supplied `approval_present=True` | Structurally impossible — confirmed no such parameter exists | Yes |
| 17 | Caller-supplied HATP VALID spoof | Structurally impossible — verification always re-runs internally | Yes |
| 18 | Test-provider injection | Structurally impossible — F-2 closure, confirmed no such parameter | Yes |
| 19 | Arbitrary trust-store injection | Same F-2 closure | Yes |
| 20 | Legacy-approved + missing HATP, post-cutover | Fail closed — HMRC-REQ-061 | Yes |
| 21 | Legacy-approved + invalid HATP, post-cutover | Fail closed — HMRC-REQ-061 | Yes |
| 22 | Delete Cutover Record | Fail closed / no silent downgrade — HMRC-REQ-049 | Yes |
| 23 | Omit `--hatp-evidence-id` post-cutover | Rejected — flag effectively required once mandatory | Yes |
| 24 | Direct function call skipping CLI | Fail closed — gate lives inside the effect functions themselves (confirmed: current callers already invoke the effect functions directly, not through a separate authority layer only the CLI can reach) | Yes |
| 25 | Cached previous VALID reused | Structurally impossible — no cache exists in current source | Yes |
| 26 | Cached previous PB ALLOW reused | Structurally impossible — PB always re-evaluated | Yes |
| 27 | Evidence deleted after prior success, retry | Fail closed on retry — HMRC-REQ-077 | Yes |
| 28 | Evidence modified after prior success, retry | Fail closed on retry — HMRC-REQ-077 | Yes |
| 29 | Two valid evidence IDs, none supplied | Rejected — explicit selection required, no auto-selection exists in `load()` | Yes |
| 30 | Old raw `hatp_proof` bypass | Rejected — deprecated, non-authoritative — HMRC-REQ-071 | Yes |
| 31 | Old `hatp_evidence` bypass | Same disposition | Yes |
| 32 | PB `HUMAN_REVIEW` despite valid HATP | Effect does not proceed — HMRC-REQ-026 | Yes |
| 33 | PB `DENY` despite valid HATP | Effect does not proceed — HMRC-REQ-027 | Yes |
| 34 | PB `ALLOW` under `simulation_only=True` | Does not authorize effect — MC-14, confirmed via current `hatp_ag_authority.py:172` + `ExecutionDisabledRule` source | Yes |
| 35 | Pre-cutover evidence, consumed post-cutover | Allowed if still fresh/valid — HMRC-REQ-079, distinguished from REQ-062 | Yes |
| 36 | Wrong AG3 job | Fail closed — operation binding | Yes |
| 37 | Wrong AG5 PER | Fail closed — operation binding | Yes |
| 38 | Wrong AG5 `ecp_id` | Fail closed — operation binding | Yes |
| 39 | Cutover-record corruption | Fail-closed-mandatory-equivalent, never legacy — HMRC-REQ-049 | Yes |
| 40 | Cutover-record wrong repository | Not-present-for-this-repo, no wrong-deployment activation — HMRC-REQ-048 | Yes |
| 41 | Cutover-record unknown version | Fail closed, never assume legacy — HMRC-REQ-046/047 | Yes |
| 42 | Cutover-record boolean version | Rejected — HMRC-REQ-046, pattern consistent with existing `isinstance(x, bool)` pre-checks already used elsewhere in this codebase | Yes |
| 43 | Repository moved/cloned/re-worktreed, evidence reused | Fail closed unless identity genuinely matches | Yes |
| 44 | AG5 divergence-blocking state + valid HATP evidence | Structural divergence check still blocks — confirmed structural checks are independent of and precede HATP evaluation in current source | Yes |
| 45 | Evidence exists, no explicit ID supplied | No effect — no implicit lookup exists anywhere in `HATPEvidenceStore` | Yes |

**45/45 coverage confirmed:** every row has an explicit expected result and
at least one supporting requirement ID; no duplicate attack numbering; no
unspecified outcome.

---

## 12. Contradiction Searches (§33, items 106, 148-151)

Independently searched the full HMRC-001 text for: `legacy`, `fallback`,
`approval`, `mandatory`, `PB`, `ALLOW`, `execution`, `evidence_id`,
`proof`, `cutover`, `prepared`, `simulation_only`, `dispatch`,
`permission`, `raw`, `downgrade`, `cache`. Every normative occurrence was
reviewed. No clause was found that: implies post-cutover legacy fallback;
lets a `simulation_only=True` PB `ALLOW` authorize a real effect; treats
evidence existence alone as authority; or expresses `legacy_approved OR
hatp_valid` (or a permanent authority-bearing AND). HMRC-001's own §33
self-consistency statement (HMRC-REQ-084/085) is corroborated, not merely
trusted.

---

## 13. Implementation Readiness (§31, items 143-147)

For each area, an implementer could proceed without architecture
guesswork: cutover storage (exact schema, exact protected-root family,
§18); effect-boundary locations (exact function + exact call site
immediately preceding, §22, independently confirmed against real line
numbers in this verification); old-hook disposition (three parameters,
three individually frozen dispositions, §23); PB handoff (exact request
shape reused, MC-14's exact truthfulness requirement, §12); activation
(exact authority class, exact six-item prerequisite list, §19). No
authority-sensitive TBD was found remaining anywhere in the document.

---

## 14. Findings Summary

**Blocking:** none.

**Non-blocking:**

- **N-1** (this phase, new): §26's category index table omits
  HMRC-REQ-083–085 from its range listing (editorial completeness gap
  only; see §2 above).
- **149O.12B-Obs-PY39-1** (carried forward, unrepaired): Python 3.9/3.10
  timestamp defect. Does not block 149O.16. Must be scheduled before the
  first mandatory-consumption *implementation* phase that depends on
  fresh CHGR/RAE fixture creation under Python 3.9/3.10.
- **149O.5-F-3 and 149O.13's three remaining stale historical boundary
  snapshots** (carried forward, unrepaired): pre-existing test debt, not
  touched by a contract-verification phase. These are boundary/snapshot
  tests fixed to a historical requirement count from an earlier phase;
  they will necessarily need updating once a future implementation phase
  changes production behavior at the AG3/AG5 effect boundary (since that
  is precisely the boundary they snapshot) — this is expected, ordinary
  test-maintenance debt for the *next* phase, not a defect in this
  contract or this verification.
- Pre-existing `pcae doctor task-memory` warnings (7 `tasks/done/` entries
  missing from `tasks/DONE.md`, predating this phase) — unrelated to
  HMRC-001, not remediated here (outside this phase's allowed-file scope).

---

## 15. Contract Verdict

```
HMRC-001 v1.0: VERIFIED WITH NON-BLOCKING FINDINGS
— HMRC-001 v1.0 CONFORMS
```

HMRC-001 v1.0 independently verified to provide a complete, internally
consistent, non-bypassable normative contract for mandatory HATP
consumption in real AG3/AG5 rollback effect paths, per all thirteen
questions in the Primary Objective (explicit evidence selection; canonical
envelope loading; fresh verification every attempt; no cached approval; no
legacy fallback post-cutover; no raw proof/evidence bypass; no direct-
function bypass; no caller-supplied approval/verification/mode authority;
protected one-way cutover; exact AG3/AG5 operation binding; PB remains
permission-decision owner; real effects require truthful enforceable PB
permission; evidence creation never changes authority).

**Implementation readiness:** `HMRC-001 v1.0: READY FOR IMPLEMENTATION
PLANNING`. This does not itself begin implementation.

---

## 16. PY39 Sequencing Decision

149O.12B-Obs-PY39-1 remains a narrow, non-blocking prerequisite. It does
not block 149O.16 (confirmed — nothing in this verification depends on
Python 3.9/3.10 timestamp behavior). It does not block a future HMRC-001
implementation *plan* phase either, since planning does not execute fresh
CHGR/RAE fixture creation. It must be resolved before the first phase that
*implements* mandatory consumption and therefore exercises fresh evidence-
creation fixtures under the supported Python range. Recommended
sequencing: 149O.16 (this phase) → narrow PY39 repair (149O.16.1-class) →
HMRC-001 implementation plan → implementation → independent implementation
verification.

---

## 17. Recommended Next Phase

**149O.16.1 — HATP Mandatory Rollback Consumption: Publication Coordinator
Python 3.9/3.10 Timestamp Compatibility Repair** (narrow scope: repair
149O.12B-Obs-PY39-1 only; no HMRC-001 implementation work). This clears
the one outstanding non-implementation prerequisite before a future
**149O.17 — HATP Mandatory Production Consumption Implementation Plan**
phase, per HMRC-001 §35's own sequencing guidance.

---

## 18. Explicit Confirmations

No production source (`src/pcae/**`) was modified this phase. `HMRC-001
v1.0` was not modified. `HSCE-001 v1.1`, `HATP-001 v1.0`, `RAE-001 v1.0`,
`RWMPC-001 v1.0`, `PBPA-001 v1.0`, `PBPC-001 v1.2` all remain byte-
unchanged (confirmed by `git diff --stat` against the phase-entering
commit). No AG3/AG5 mandatory consumption was implemented. No Cutover
Record was created. No legacy approval behavior changed. No Permission
Broker behavior changed. `POL-005` remains unchanged. No `COMP-002`
capability was implemented. No rollback dispatch behavior changed. No
Class-B provisioning occurred. No HATP production activation occurred.

`B-149O-1..4` remain **INDEPENDENTLY VERIFIED AT THE HATP-GATED AUTHORITY
BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED**, unchanged by this phase —
contract verification alone cannot close them (HMRC-001 §32).

HATP production remains **NOT READY**. Runtime remains **Observed /
observe / unavailable**.
