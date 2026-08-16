# Phase 149O.20L.7L.1 — HMIC-001 v1.4 Consumer-Status and Dependency-Header Repair

## Purpose

149O.20L.7L independently verified that the HMIC 28 → 30 frozen
source-scope expansion (149O.20L.7K) is technically correct, but withheld
a VERIFIED verdict because HMIC-001 v1.4 itself contains false/stale
contract text: it asserts in multiple locations that no readiness,
certification, or activation code path consumes
`verify_class_b_deployment_conformance()`, when Phase 149O.20L.3 had
already wired it into `hatp_mandatory_cutover.py` as the eighth
activation-readiness term — ancestral to 149O.20L.7K's own phase entry.
This phase performs the minimum narrow, same-version, contract-text-only
repair the withheld verdict requires (findings F-7L-1, blocking, and
F-7L-2, non-blocking), and adjudicates two optional adjacent findings
(F-7L-5, F-7L-7).

This is **not** an independent-verification phase; it is a repair phase.
149O.20L.7L.2 must independently verify this repair before the 7J §31
source-scope finding can close.

## True phase-entry commit

`95cfd008690b65a31ff8f61f3cfb893622d308ec` — "Phase 149O.20L.7L: repair
pcae_push_check literal value for finalization gate", clean working tree,
`main` in sync with `origin/main` (0 commits ahead/behind).

## Independent F-7L-1 reconstruction

Read directly from `src/pcae/core/hatp_mandatory_cutover.py`, not from
7L's own report narrative:

- Line 74: `from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance`.
- Line 952, inside `_assess_hatp_mandatory_activation_readiness_at_root`
  (called by `assess_hatp_mandatory_activation_readiness`, the sole
  production activation-readiness entrypoint, at line 993):
  `class_b_result = verify_class_b_deployment_conformance(...)`.
- The result is appended as `class_b_deployment_conformance_satisfies_readiness`
  — the **eighth and final** entry among the eight
  `HATPMandatoryActivationReadinessCheck` instances the function
  assembles, exactly matching the module's own comment at lines 938-949
  ("the eighth, additive readiness term").
- The same function is also re-invoked, lock-held, immediately before
  any real `HATP_MANDATORY` activation write, via
  `_activate_hatp_mandatory_at_root`'s `readiness_check` callback (lines
  1049-1051) — consumed by both the advisory readiness assessment and
  the pre-activation re-check.
- Repository-wide grep confirms no other `src/pcae/**` module calls
  `assess_hatp_mandatory_activation_readiness` or
  `_assess_hatp_mandatory_activation_readiness_at_root`.

**Chronology** (`git log --oneline main`, position numbers = distance
from HEAD, lower = more recent): 149O.20L.3's wiring commit `e2ccb7a3`
sits at position 224; 149O.20K (v1.3, contract §53) sits at position
272 (older); 149O.20L.7K (v1.4, contract §55) sits at position 18
(much more recent). So: **149O.20L.3's wiring landed after 149O.20K
but before 149O.20L.7K.** §53.4's "zero production consumers" finding
was accurate when 149O.20K wrote it and is a legitimate historical
snapshot, left unmodified. §55.4/§55.15/HMIC-REQ-052 limb (c)'s closing
paragraph and attack rows 38/39 (149O.20L.7K) were written *after* the
wiring landed — their "zero production consumers" language was never
accurate at the moment it was written, not merely stale afterward.

## Exact production consumer evidence

`verify_class_b_deployment_conformance` has exactly one production
consumer: `hatp_mandatory_cutover.py`'s mandatory activation-readiness
assessment (readiness **and**, via the same function's lock-held
re-invocation, activation). It has **zero** certification consumers —
`hatp_mandatory_certification.py`'s validator neither calls nor is
called by it; the two are evaluated by independent readiness terms in
different functions (`hmic_verified` vs. `class_b_satisfied`).

## Complete stale-claim inventory

| Location | Claim | Status |
|---|---|---|
| HMIC-REQ-052 limb (c) closing paragraph (§17, live text) | "as of v1.4, no readiness, certification, or activation code path calls `verify_class_b_deployment_conformance`" | **False when written (149O.20L.7K); repaired** |
| §55.4 (149O.20L.7K historical record) | Producer-only zero-consumer finding, cited by §55.15 as if it covered the verifier too | Producer finding itself accurate; **misleading citation repaired via scope note** |
| §55.15 Verdict (149O.20L.7K historical record) | "Zero production consumers of `verify_class_b_deployment_conformance` remain (§53.4/§55.4)" | **False when written; repaired** |
| Attack row 38 (§41, added v1.3) | "zero production consumers of the Class-B verifier island exist today" | **False in current repo state; repaired (F-7L-5, row 38)** |
| Attack row 39 clause (a) (§41, added v1.4) | "`verify_class_b_deployment_conformance`'s result still has zero readiness/certification consumers" | **False when written; repaired** |
| §53.4 (149O.20K historical record) | Same-shape claim, but predates the 20L.3 wiring | **Accurate when written — legitimate historical snapshot, left unmodified** |
| §54's "Recommended next phase" pointer (149O.20L.1A, predates 20L.3) | "zero readiness-path consumer of the Class-B verifier island" | **Accurate when written — legitimate historical snapshot, left unmodified** |
| Attack rows 33/34/36/37 | "Not yet operative" caveats tied to a *different* subsystem's (validator/contract-count) realignment history | **Deferred, non-blocking — see F-7L-5 adjudication** |

Full-document grep for `verify_class_b_deployment_conformance`,
`zero production consumer`, and `no readiness ... code path calls`
confirms no further occurrence needed repair; the two remaining
post-repair matches (line 723-ish, in the limb (c) correction prose
itself, and inside §56's own repair-history narrative) are this phase's
own corrective text, not stale claims.

## Readiness/certification/activation distinction

Independently verified from source, not asserted by analogy:
**readiness** — yes, direct call inside the sole production
readiness-assessment function. **Activation** — yes, indirect via
readiness (the same function is re-invoked, lock-held, immediately
before any real `HATP_MANDATORY` write; there is no separate
activation-time call). **Certification** — no; the HMIC validator does
not call, and is not called by, the verifier. **Other production
paths** — none found.

## HMIC-REQ-052 limb (c) repaired semantics

Repaired to state limb (c)'s first anchor is **not** anticipatory (the
verifier already has a real consumer), while explicitly preserving the
third anchor's own rationale **unweakened**: the `DeploymentBinding`
producer/admin-ceremony write path remains genuinely unreachable from
the verifier's own call graph (an independently true fact, unaffected
by the verifier's consumer status) and remains anticipatory in its own
right because no real `DeploymentBinding` has ever been created. The
repair distinguishes "the producer is not reachable through the
verifier's own transitive dependency graph" (still true, unweakened)
from "the verifier itself is unconsumed" (was false, now corrected) —
these are different facts, and the repair does not conflate them.

## §55.4 repair

§55.4's own text, read narrowly, was always scoped to the producer's
zero-consumer/zero-invocation status — it never itself asserted a claim
about the verifier. A scope-clarifying note was appended stating this
explicitly and cross-referencing the correction at §55.15/§56.1, without
altering §55.4's own (accurate, unaffected) producer-level finding.

## §55.15 repair

"Zero production consumers of `verify_class_b_deployment_conformance`
remain (§53.4/§55.4)" is repaired with an inline correction explaining
why it was never accurate and why §53.4/§55.4 do not, and never did,
jointly support it. The adjacent, independent claim "zero real
`DeploymentBinding` invocations exist on any host" is preserved
unmodified.

## Row 39 repair

Clause (a) is repaired to ground the row's "not functionally
load-bearing" conclusion in the true, load-bearing fact: the
`DeploymentBinding` producer/admin-ceremony pair is bound under limb
(c)'s third, non-reachability anchor precisely because it is a separate
write path not transitively captured by the verifier's own call graph —
independent of the verifier's consumer status. Legs (b) (no real
`DeploymentBinding` ever created) and (c) (no HMIC certification exists)
are unchanged; the row's overall conclusion is preserved.

## F-7L-2 dependency-header repair

This document's own `Depends on (current, HMIC-unamended)` header read
`HBDC-001 v1.0`. `HBDC-001`'s own live Version header field reads `1.1`
(`HBDC-001` has been v1.1 since Phase 149O.20L.7G); `derive_contract_versions`
(`core/hatp_mandatory_certification.py`) independently returns
`{"HBDC-001": "1.1", ...}` against the live repository — the
live-header-derivation mechanism was never stale, the identical
Outcome-B shape §54.3 (149O.20L.1A) established for the same defect
class against `HMRC-001`. Repaired: the header now reads `HBDC-001
v1.1`; all other four members unchanged.

## Same-version precedent analysis

Inspected §52 (149O.20D.1) and §54 (149O.20L.1A): both are in-place,
same-version corrections of descriptive/dependency-header text that
never touched a requirement's normative meaning, membership, or
production behavior — precisely the shape of this repair. §55.14
(149O.20L.7K's own version-bump rationale) explicitly distinguishes
scope-*widening* amendments (v1.0→v1.1, v1.1→v1.2, v1.2→v1.3, v1.3→v1.4
— each changed which limb applied or how many files were bound) from
same-version repairs like §52/§54 (corrected only descriptive text, no
limb/membership change). This repair fixes false *consumer-status*
descriptive text and a dependency-header value — no `HMIC-REQ-###`
limb, membership, or algorithm changes — the identical shape, not the
widening shape. Version correctly remains v1.4.

## HMIC version unchanged proof

`grep -n "^\*\*Version:\*\*"` on the contract returns exactly one match,
`**Version:** 1.4`, both before and after this phase's edits.

## HMIC-REQ-050 unchanged proof

`grep` for "thirty files, no more, no fewer" and the fenced 30-path
enumeration block confirms byte-identical text before/after; `git diff`
of the contract file shows zero lines touched inside the §17
enumeration block.

## 30-member source set / frozen tuple byte-identity proof

`hmic._FROZEN_AUTHORITY_BEARING_FILES` still asserts `== 30` (unedited
assertion line, `src/pcae/core/hatp_mandatory_certification.py:1025`).
Git blob hash of `hatp_mandatory_certification.py` is unchanged from
`git status --short` (clean, no diff) — confirmed no production edit.

## Producer/admin byte-identity proof

`git hash-object` before and after this phase's edits:

| File | Hash |
|---|---|
| `src/pcae/core/hatp_deployment_binding_admin.py` | `c7950f302ba5714764de5fa0fd86699a07cfad1c` (unchanged) |
| `scripts/hatp_deployment_binding_admin.py` | `286db838d573ef9311a6d0df78a6842b5f4ef296` (unchanged) |
| `src/pcae/core/hatp_mandatory_cutover.py` | `1344ed86289369c225519f4ea13f2c296269c374` (unchanged) |

## HBDC-001 v1.1 unchanged proof

`git hash-object docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` =
`ccc4efba78b39633b63f25e1415b915598a49772`, identical before/after; the
document's own `**Version:** 1.1` line is untouched by this phase (only
HMIC-001's own header, referencing HBDC's version, was edited).

## Cutover implementation unchanged proof

Byte-identical (see table above); `git status --short` shows zero
modification to any `src/pcae/**` file for the whole duration of this
phase.

## F-7L-5 per-row adjudication

- **Row 38** — **REPAIRED NARROWLY.** Its stale "zero production
  consumers" clause directly restates the exact F-7L-1 claim this phase
  already independently reconstructed in full; leaving it unrepaired
  while repairing row 39's twin clause would leave a contradictory
  duplicate stale claim in the same table (violates the duplicate-search
  discipline). Both premises (28-file realignment not yet done; verifier
  unconsumed) are now false — production is at the full 30-file set, and
  the verifier has a real consumer — so the row is repaired to
  "Operative and consequential."
- **Rows 33, 34, 36, 37** — **DEFERRED, non-blocking.** Each ties its
  "not yet operative" caveat to a *different* production-identity
  subsystem's realignment history (the v1.1→v1.2→v1.3→v1.4 file/contract
  count thresholds, and, for row 34, a distinct Wave F readiness
  integration for the HMIC certification validator) outside this phase's
  own narrow F-7L-1 evidence chain. Confirming exactly when each was
  superseded requires independently re-deriving multiple earlier,
  separately-governed alignment phases — wider architecture
  interpretation this phase's own governing scope directs deferring.

## F-7L-7 adjudication

Two textual guard tests (7I:
`test_no_src_pcae_module_imports_the_producer_except_itself`; 7J:
`test_producer_module_not_imported_anywhere_in_src_pcae_except_itself`)
previously exempted `hatp_mandatory_certification.py` from their
substring scan at whole-file granularity. 149O.20L.7L's own strictly
stronger, unconditional AST-level guard
(`test_no_module_under_src_pcae_imports_the_producer_at_ast_level`) and
companion frozen-path-data proof
(`test_certification_module_references_the_producer_only_as_frozen_path_data`)
are preserved byte-unmodified. The two older guards are **tightened**:
`hatp_mandatory_certification.py` is no longer skipped outright — every
textual occurrence of the producer's name in it is inspected, and only
non-import (literal path-string) occurrences are tolerated (the file's
three known occurrences, at lines 952/983/1008, all pass; a future real
`import`/`from` line would now fail these two tests independently of the
AST guard). Both tightened tests pass.

## AST guard preservation

`test_no_module_under_src_pcae_imports_the_producer_at_ast_level` and
`test_certification_module_references_the_producer_only_as_frozen_path_data`
(both in the 149O.20L.7L test file) are untouched — confirmed by `git
diff` showing zero lines changed in either function.

## Pre/post implementation digest

`derive_implementation_scope_digest` (against the live repository, both
before this phase's first edit and after its last):
`65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` —
unchanged, matching the pre-existing post-7K/HEAD value (HMIC-001 is not
itself a member of its own frozen 30-file set, so a contract-document
edit does not enter this digest).

## Contract identity consequence

HMIC-001's own document bytes changed (git diff of
`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
is non-empty) — this is a **contract-identity** consequence, distinct
from the (unchanged) implementation/source digest. Any future
certification computed against this document's bytes would need to be
computed fresh against the repaired text; no certification currently
exists to be invalidated by this change (§56.13 restates this).

## `derive_contract_versions` result

Post-repair: `{'HMRC-001': '1.1', 'HATP-001': '1.0', 'HSCE-001': '1.1',
'RAE-001': '1.0', 'HBDC-001': '1.1'}` — `HBDC-001` now agrees exactly
with the repaired `Depends on` header.

## Focused regression guards added

New file `tests/test_phase_149o_20l_7l_1_hmic_consumer_status_and_dependency_header_repair.py`
(20 tests, all passing): dependency-header consistency (2), F-7L-1
consumer-status regression guards (4), direct production-consumer guard
(4, no line-number pinning), third-anchor regression guard (2),
attack-row coherence (1), and version/membership/production-immutability
guards (7, including literal pre-repair blob-hash pins for the producer,
admin script, HBDC-001, and cutover module, and a pinned
`implementation_scope_digest` value).

Two pre-existing self-pin tests (7L's own
`test_finding_7l_1_contract_still_asserts_the_disproven_zero_consumer_claim`
and `test_finding_7l_2_hmic_depends_header_is_stale_for_hbdc`, both
carrying explicit "update this test once repaired" docstrings) were
updated to assert the repaired state instead of the pre-repair bug.
One 149O.20K-era pin (`test_attack_row_38_present_and_named`) was
updated to match row 38's corrected operative-status wording. One
149O.20L.1A-era pin
(`test_other_four_members_versions_unchanged_by_this_repair`) was
re-scoped from comparing against today's live text to comparing against
that phase's own pre-repair/post-repair commit pair, since it was
falsely asserting an eternal invariant about a header value a *later,
different* phase (this one) legitimately changed.

## A/B regression classification

Two disposable states compared over the same 22-file narrow test
selection (HMIC/HBDC contract tests, 7K/7L/7I/7J suites,
certification/cutover focused tests): pre-repair (`git worktree` at this
phase's true entry commit `95cfd008`) vs. post-repair (working tree
after all edits). 114 pre-repair failures / 9 errors; 119 post-repair
failures / 9 errors before test updates. Node-ID diff: **6 new
failures**, all four of the non-working-tree-dirty ones matching
exactly the self-pin tests named above (fixed in this phase, now 0 new
after fixes, confirmed by a third run); the remaining two are
`git status --porcelain` working-tree-cleanliness pins that fail only
because the repair is not yet committed — resolve automatically once
committed. **1 resolved failure**
(`test_derived_versions_now_match_the_depends_on_line_exactly`, now
passing because the header/live-value mismatch it detected is fixed).
Zero unexplained, zero security/authority/behavioral regressions.

## Verdict

**CONTRACT REPAIR IMPLEMENTED — INDEPENDENT VERIFICATION PENDING.**
F-7L-1 and F-7L-2 repaired narrowly with no membership/production
semantic change.

- **F-7L-1:** REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.
- **F-7L-2:** REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.
- **F-7L-5 (rows 33/34/36/37):** DEFERRED, NON-BLOCKING — UNMODIFIED.
- **F-7L-5 (row 38):** REPAIRED — INDEPENDENT VERIFICATION PENDING.
- **F-7L-7:** REPAIRED — INDEPENDENT VERIFICATION PENDING (test-only; no
  production source touched).
- **7J §31 HMIC frozen-source-membership finding:** REPAIRED AT THE
  CONTRACT-AND-PRODUCTION LAYER — INDEPENDENT VERIFICATION PENDING —
  NOT CLOSED (unchanged by this phase; only 149O.20L.7L.2 may close it).
- **Carried-forward findings** (HMIC-REQ-103 revocation-validation gap,
  the producer's audit-failure-after-durable-mutation gap, the
  permissive `_parse_iso_timestamp()` consumer, HMIC-REQ-063's
  runtime/import-shadowing limitation, and all historical identity-pin
  tests): untouched, none claimed repaired.

HMIC-001 remains v1.4. Frozen source scope: 30 members, unchanged.
Implementation/source digest: unchanged from pre-phase. DeploymentBinding
producer: unchanged and independently verified (byte-identical). No
Dell access of any kind. No RepositoryIdentity. No DeploymentBinding.
No first-use election. Boundary C/A: not authorized. Runtime: Observed /
observe / unavailable.

## Governance results

- `pcae_health`: healthy
- `pcae_check`: passed
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, unrelated — historical
  `tasks/done/` entries missing from `tasks/DONE.md`, predating this
  phase, outside this phase's allowed-file scope)
- `pcae_push_check` (pre-phase): clean (nothing_to_push)
- `pcae_runtime_inspect`: Observed / observe / unavailable
- `pcae_notify_status`: Telegram configured/enabled

## Tests

New: `tests/test_phase_149o_20l_7l_1_hmic_consumer_status_and_dependency_header_repair.py`
(20 passed). Modified: `tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py`,
`tests/test_phase_149o_20l_7j_deploymentbinding_producer_implementation_independent_verification.py`
(F-7L-7 guard tightening, both still passing), `tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.py`
(two self-pins updated to repaired state), `tests/test_phase_149o_20k_hmic_class_b_verifier_source_scope_contract_evolution.py`
(one self-pin updated), `tests/test_phase_149o_20l_1a_hmrc_v1_1_hmic_contract_identity_alignment_repair.py`
(one self-pin re-scoped to its own phase's diff window).

## No-go confirmations

No `src/pcae/**` production source was modified. No producer or
admin-script behavior was modified. No RepositoryIdentity was created.
No real DeploymentBinding was created. No first-use human election was
initiated. No first-use CHGR was published. No HMIC certification was
computed, requested, or granted (none exists). No Dell access of any
kind (read or write) occurred. No Boundary C action was taken. No
Boundary A action was taken. No HATP activation occurred. No Permission
Broker, POL-005, or COMP-002 change was made. No pre-existing carried
finding was repaired. No historical test was migrated wholesale — only
the specific self-pins that documented *this phase's own* findings were
updated. No governance bypass, `--no-verify` flag, or force push was
used.

## Recommended next phase

**149O.20L.7L.2 — HMIC-001 v1.4 Consumer-Status and Dependency-Header
Repair Independent Verification.** Must independently verify: every
F-7L-1 correction; the HBDC dependency-header correction; same-version
repair legitimacy; no HMIC-REQ-050/052 semantic weakening; unchanged
30-member source scope; unchanged implementation digest; no production
behavior changes; the F-7L-5/F-7L-7 adjudications. Only after a clean
149O.20L.7L.2 may the 7J §31 source-scope finding be closed, and only
after that may a separate, separately-governed phase decide the
first-use sequencing architecture (redeploy-first vs. SHA-bound election
vs. two-CHGR). No binding, election, certification, redeployment, or
Dell mutation is authorized by this phase or by 149O.20L.7L.2.
