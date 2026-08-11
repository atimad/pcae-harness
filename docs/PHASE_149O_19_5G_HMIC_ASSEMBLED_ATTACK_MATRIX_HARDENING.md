# Phase 149O.19.5G — HMIC Assembled Attack Matrix / Hardening

**Status:** VERIFIED WITH NON-BLOCKING FINDINGS — ASSEMBLED CERTIFICATION
→ READINESS → ACTIVATION BOUNDARY HOLDS — NO PRODUCTION OR CONTRACT
CHANGES — NO REAL ACTIVATION PERFORMED

**Phase type:** ASSEMBLED ADVERSARIAL VERIFICATION / HARDENING (Wave G).
Verify-first; no new capability by default; narrow repairs only on a
demonstrated Blocking defect (none found).

---

## 1. Baseline

- Latest completed phase entering this one: **149O.19.5F** (HMIC
  Activation-Readiness Integration), commits `478f8b2c`, `45068337`,
  `c290bcc6`, `64ed230d`, pushed, `origin/main..HEAD` = 0 at entry, repo
  clean.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent. `pcae push check`: clean, `nothing_to_push`.
- `pcae doctor task-memory`: warnings — the same pre-existing
  `tasks/done/` entries (149O.1H.3–149O.3) missing from `tasks/DONE.md`
  noted at every prior 149O.19.5x baseline; unrelated to HMIC, not
  remediated here (outside this phase's allowed-file scope).
- `pcae runtime inspect`: Observed / observe / unavailable, Permission
  Broker `execution_unavailable`.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest` / `reconcile --phase-id
  149O.19.5F`: 149O.19.5F confirmed `completed`/`complete`, recommending
  exactly 149O.19.5G.
- HMIC-001 v1.1, HMRC-001, HATP-001, HSCE-001, RAE-001, RWMPC-001,
  PBPA-001, PBPC-001: confirmed byte-unchanged entering this phase and
  reconfirmed byte-unchanged at exit (§13).

## 2. Primary Sources Read Directly

`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
(HMIC-001 v1.1, in full); `src/pcae/core/hatp_mandatory_certification.py`
(2096 lines, in full); `src/pcae/core/hatp_mandatory_cutover.py` (1025
lines, in full); `scripts/hatp_certification_admin.py` (537 lines, in
full); prior phase docs 149O.19.5A–F (background context only — every
claim re-derived independently against live source, not copied).

## 3. Reconstructed Inventories (Mechanical, Not Copied From Reports)

- **`CertificationStatus`**: 9 members exactly — `MISSING`, `MALFORMED`,
  `WRONG_REPOSITORY`, `WRONG_DEPLOYMENT`, `IMPLEMENTATION_MISMATCH`,
  `CONTRACT_MISMATCH`, `REVOKED`, `ACCESS_ERROR`, `VALID`
  (`hatp_mandatory_certification.py:459-478`). Matches HMIC-REQ-106's
  closed vocabulary.
- **24-file frozen scope**: independently re-extracted from the live
  contract text (HMIC-REQ-050); confirmed to include all three
  self-referential members — `hatp_mandatory_certification.py`,
  `scripts/hatp_certification_admin.py`, and `hatp_mandatory_cutover.py`
  — matching the prior phases' claims.
- **HMRC-REQ-054 readiness terms**: 6, plus 1 module-owned
  (`repository_deployment_identity_valid`) = 7 total
  `HATPMandatoryActivationReadinessCheck` entries in
  `_assess_hatp_mandatory_activation_readiness_at_root`, unchanged in
  count/order/names since 149O.19.5F.
- **144 HMIC requirements / 12 CIVC invariants / 34 attack scenarios**:
  present in the contract as HMIC-REQ-001 through HMIC-REQ-144, CIVC-1
  through CIVC-12, and the numbered attack-scenario table. Adjudication
  is via the assembled test module (§6) plus the traceability summary in
  §7-§8, not 144 bespoke bespoke tests — mechanically redundant items
  (e.g. per-field parser rejections) are covered by parametrized cases.

## 4. Assembled Path Under Attack

`certification artifact (JSON)` → parser/model → `implementation +
contract identity derivation` → protected certification store (active
binding, revocation) → `validate_active_hatp_mandatory_independent_
verification_certification` → `CertificationStatus` → `certification_
status_satisfies_readiness` → one of 7 HMRC readiness checks → overall
`HATPMandatoryActivationReadiness` → `activate_hatp_mandatory`'s
lock-held fresh recheck → `Cutover Record` write / activation marker.
Every layer in this chain was independently attacked (§6).

## 5. Method

A general-purpose research/implementation pass read all primary sources
in full, reconstructed the inventories in §3 independently, and wrote
one new assembled test module composing multiple layers per test (not
re-running per-layer unit tests already covering these paths in
isolation) against real (never mocked) production code, using isolated
`tmp_path` protected-root fixtures consistent with the existing
149O.19.5A-F fixture style. I independently reviewed the diff, reran the
new module myself, and independently confirmed the real host's protected
root (`HATPTrustStore.production().root`) is absent both before and
after, and that `git status` shows only the expected task-lifecycle
files plus the one new test file.

## 6. Assembled Attack Matrix — Adjudication

`tests/test_phase_149o_19_5g_hmic_assembled_attack_matrix_hardening.py`
— 68 tests, 68 passed.

| # | Category | Result |
|---|----------|--------|
| 1 | Parser/model attacks (unknown field, bool-as-version, wrong-type ID, path-traversal-shaped ID, duplicate JSON key, NaN/Infinity) | Held — rejected at parse; malformed store files map to `MALFORMED`, never silently downgraded |
| 2 | Parsed-but-not-valid (revoked / wrong-repo / wrong-deployment / wrong-implementation / wrong-contracts) | Held — none reach `VALID`; each maps to its exact contract status via the real admin ceremony |
| 3 | 24-file identity attacks (omit / add / modify one frozen file, incl. self-binding on the certification module, admin script, and cutover module) | Held — digest changes on any frozen-file omission/modification; unaffected by extra non-frozen files |
| 4 | No implicit-latest | Held — unbound certifications never consulted; no `sorted`/`glob`/`max`/timestamp-based selection in the validator |
| 5 | Active-invalid vs. newer-valid | Held — a revoked active-bound cert stays `REVOKED`; no fallback to a newer unbound record |
| 6 | Validator status precedence (multi-defect: revoked+mismatch, wrong-repo+revoked, mismatch+contract-mismatch, missing+everything) | Held — matches HMIC-REQ-103's 12-step order exactly |
| 7 | Freshness / no-cache / read-only | Held — no memoization decorator in the module; byte-identical protected root before/after repeated calls; live-state-reflecting |
| 8 | Authority-input injection | Held — production entrypoint signature is exactly `(repository_root)`; no `implementation_digest=`/`valid=`/`force=`-shaped parameter anywhere, including internal test seams; env-var injection has no effect |
| 9 | Admin/agent-reachability | Held — no `src/pcae/**` file besides the module itself references the writer primitives; no CLI/agent import of the admin script |
| 10 | Readiness integration re-attack (HMIC VALID alone insufficient; HMIC non-VALID always blocks; exact 9-member enum mapping incl. exception→False) | Held |
| 11 | TOCTOU / lock-held recheck (revocation, binding change, implementation drift between advisory pre-lock read and lock-held recheck) | Held — activation refused in all three; Cutover Record byte-identical before/after; no activation marker written |
| 12 | One-way cutover | Held — post-activation revocation degrades readiness honestly but never reverses `HATP_MANDATORY`; no reverse transition-graph edge |
| 13 | Historical replay (v1.0/22-file-shaped digest; pre-Wave-F `hatp_mandatory_cutover.py` bytes) | Held — neither validates against current post-Wave-F source, since `hatp_mandatory_cutover.py` is itself a frozen, changed file |
| 14 | No-fallback-chains | Held — no bare `except:` in the three modules; no `os.environ`/`os.getenv` reads in the certification or admin modules; no legacy-scope/bypass tokens found |
| 15 | Real-host non-mutation | Held — `HATPTrustStore.production().root` absent before and after; no real certification/binding/revocation/Cutover-Record/activation-marker state anywhere |

Cross-check regression: `pytest -k "hmic or hatp_mandatory or 149o_19"`
→ 1216 passed, 10 failed, 2 skipped; `git stash -u` A/B (new test file
included in the stash) reproduced the identical 10 failures with the
phase's change removed — all pre-existing, mostly other phases' pinned
"no production files changed since commit X" checks that necessarily
trip once any later phase (149O.19.5F) touches a shared file, none
implicating this phase's own (nonexistent) production diff.

## 7. CIVC-1..12 Adjudication

All 12 invariants re-evaluated against the assembled implementation via
the matrix in §6 (no implicit-latest = CIVC covering unbound-authority
rejection; active-invalid-not-superseded = CIVC covering binding
integrity; one-way cutover = CIVC covering irreversibility; freshness/no
caller-injection = CIVC covering fresh-evaluation and authority-input
integrity; 24-file self-binding = CIVC covering identity-scope
completeness). Zero invariant violated under attack.

## 8. Findings

**Blocking:** none.

**Non-blocking / observation (all pre-existing or purely textual, none
touched):**

- **F-149O.19.5G-1 (new this phase, textual only).**
  `certification_status_satisfies_readiness`'s docstring in
  `hatp_mandatory_certification.py` (line ~488) still reads "This
  function is never wired into `hatp_mandatory_cutover.py` by this phase
  (Wave F only, gated by Stop Condition W-1)" — stale since 149O.19.5F
  actually performed that wiring. Purely descriptive text with no
  authority effect (the function's behavior, not its docstring, governs
  runtime outcomes); not repaired here per the non-opportunistic-repair
  policy (§74 of this phase's governing instructions) since it does not
  touch a frozen-file byte relevant to any certification's validity in a
  way that would itself need re-certification — flagged for a future
  documentation-only phase.
- Stale "HMIC-001 v1.0" textual references remain in contract
  §HMIC-REQ-139/Sec42/Sec46 — reconfirmed pre-existing, not repaired.
- HMIC-REQ-063 (runtime/executed-source-binding) remains an explicitly
  deferred, named limitation — not a defect.
- The pre-existing `pcae doctor task-memory` warning (tasks/done/ entries
  missing from tasks/DONE.md, predating 149O.1H.3) — reconfirmed
  unrelated.
- 10 regression-suite failures and 24 Fast Green failures (below) are all
  pre-existing per A/B stash comparison; none implicate the HMIC
  validator, admin script, or cutover readiness wiring.
- `fido2` is not installed in this environment, causing one unrelated
  test file to fail collection and two others to skip.

## 9. Assembled Verdict

**HMIC ASSEMBLED WAVE A–F ATTACK MATRIX / HARDENING: VERIFIED WITH
NON-BLOCKING FINDINGS — ASSEMBLED CERTIFICATION → READINESS →
ACTIVATION BOUNDARY HOLDS.**

No untrusted/caller/repository/environment-controlled input was found
able to cause HMIC VALID, `mandatory_consumption_implementation_
independently_verified=True`, overall activation readiness=True, or a
`HATP_MANDATORY` transition without satisfying every frozen prerequisite.

**HATP production remains NOT READY.** Runtime remains **Observed /
observe / unavailable**.

## 10. Historical Finding Statuses (Unchanged)

- **W-1:** remains INDEPENDENTLY CONFIRMED CLOSED AT CONTRACT +
  IMPLEMENTATION-IDENTITY BOUNDARY — deployment/runtime-source provenance
  still deferred. Not reopened; this phase found no scope gap.
- **B-149O.19.3-1:** remains INDEPENDENTLY CLOSED.
- **B-149O-1..4:** remain INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM
  IMPLEMENTATION/ENFORCEMENT BOUNDARY — deployment/operational activation
  deferred. Not upgraded to deployment closure.

## 11. No-Go Confirmations

Zero production files changed. Zero contract files changed. No real
certification artifact, active binding, revocation record, Cutover
Record, or activation marker created anywhere on this host, before or
after. No real `HATP_MANDATORY` activation. No Class-B provisioning. No
Permission Broker behavior changed. POL-005 unchanged. COMP-002 not
implemented. Runtime/executed-source binding remains deferred under
HMIC-REQ-063. No governance bypass, `--no-verify`, or force push was
used.

## 12. Test Evidence

- New module: `tests/test_phase_149o_19_5g_hmic_assembled_attack_matrix_hardening.py`
  — 68 tests, 68 passed (independently rerun).
- Wave A-F/HMRC/HATP-adjacent regression (`pytest -k "hmic or
  hatp_mandatory or 149o_19"`): 1216 passed, 10 failed (pre-existing,
  A/B-confirmed), 2 skipped.
- Fast Green (`pytest -m fast_green -n auto`): clean deselected run
  (26 confirmed pre-existing/unrelated node IDs deselected, one file
  ignored): **0 failed, 6251 passed, 2 skipped**. Raw run: 25 failed,
  6252 passed, 2 skipped, 1 collection error — all 25 confirmed
  pre-existing by direct A/B comparison (new test file moved out of
  `tests/`, rerun: identical 25 failures, 6184 passed instead of 6252,
  a difference of exactly 68 matching the new test count). One node
  (`test_backend_cli.py::TestBackendReviewCreate`) is flaky under
  `-n auto` parallelism, failing a different subtest in each run — not
  attributable to this phase. The collection error is `fido2` not
  being installed in this environment (pre-existing/unrelated).

## 13. Contract/Production Diff Expectation

Zero contract bytes changed (HMIC-001 v1.1, HMRC-001, HATP-001,
HSCE-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001 all confirmed
byte-unchanged at exit). Zero `src/pcae/**` files changed. Zero
`scripts/**` files changed. Exactly one file added:
`tests/test_phase_149o_19_5g_hmic_assembled_attack_matrix_hardening.py`.

## 14. Strategic Next-Step Reassessment

The assembled Wave A-F implementation chapter (parser/model → identity →
store → validator → admin → readiness → lock-held activation) is now
independently attacked and verified end-to-end with no Blocking finding.
Deployment prerequisites remain unaddressed: no real Class-B principal is
provisioned on this host, and runtime/executed-source binding
(HMIC-REQ-063) remains an explicit residual limitation. Recommended next
phase: a deployment-readiness architecture phase examining what a real
Class-B provisioning plan requires (not provisioning it), and/or
disposition of the HMIC-REQ-063 residual limitation as its own scoped
design phase — not real Class-B provisioning or real activation, which
remain out of scope until those architecture phases exist and are
independently reviewed. This is not pre-authorization of either; the next
phase's own governing instructions will make the final selection against
canonical state at that time.
