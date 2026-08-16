# Phase 149O.20L.7L.2 — HMIC-001 v1.4 Consumer-Status and
Dependency-Header Repair Independent Verification

**Status:** COMPLETE — **NOT VERIFIED — CONTRACT REPAIR INCOMPLETE**
**Scope:** Independent verification only. No contract edit, no production
edit, no test edit, no `DeploymentBinding`, no `RepositoryIdentity`, no
election, no CHGR, no certification, no redeployment, no Dell access.

## 1. Purpose

Independently verify Phase 149O.20L.7L.1's same-version, contract-text-only
repair of HMIC-001 v1.4 (findings F-7L-1, F-7L-2), its adjudication of
attack-matrix rows 33/34/36/37/38 (F-7L-5), and its tightening of the two
7I/7J textual import guards (F-7L-7) — without trusting 149O.20L.7L.1's own
narrative for any of it.

## 2. Baselines (independently resolved from Git objects)

- True 149O.20L.7L phase-end / 149O.20L.7L.1 phase-entry commit:
  `95cfd008` ("Phase 149O.20L.7L: repair pcae_push_check literal value for
  finalization gate").
- 149O.20L.7L.1's substantive commit: `ae9da630` ("Phase 149O.20L.7L.1:
  HMIC-001 v1.4 Consumer-Status and Dependency-Header Repair") — 8 files
  changed, 1078 insertions, 42 deletions. Full diff independently read;
  every hunk classified below.
- HEAD at this phase's start: `4ba3e60a`. `git status --branch --short`:
  clean, `main...origin/main`, 0 commits ahead/behind
  (`git rev-list --count origin/main..HEAD` = 0).
- `pcae health`/`pcae check`/`pcae status coherence`: all clean/passed.
  `pcae doctor task-memory`: pre-existing warnings only (26 stale
  `tasks/done/**` entries missing from `tasks/DONE.md`, predating this
  phase, unrelated). `pcae push check`: nothing to push. `pcae runtime
  inspect`: Observed/observe/unavailable. `pcae notify status`: Telegram
  configured/enabled. `pcae phase-report reconcile --phase-id
  149O.20L.7L.1`: `delivery_recorded_bookkeeping_incomplete` (pre-existing
  bookkeeping note, inspection-only, no mutation).

**Diff classification (`ae9da630`):**
- Contract file (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_
  CERTIFICATION_CONTRACT.md`): header Status/Repaired-by/Depends-on lines;
  HMIC-REQ-052 limb (c) closing paragraph (§17); §55.4 scope note; §55.15
  verdict correction; attack rows 38/39; new §56 (Contract Repair
  History). No other section touched. `HMIC-REQ-050`'s enumeration,
  `HMIC-REQ-052`'s three-limb membership test, and every other requirement
  body are byte-identical (confirmed by direct diff read — the only
  hunks touch prose described above).
- Five test files: self-pin polarity flips (tests written to fail until
  the repair landed, now flipped to fail if it regresses) plus two new
  header/status assertions — all inspected individually, §5 below.
- One new test file (20 tests, all reviewed, §9 below).
- One new phase doc (149O.20L.7L.1's own report — not relied upon as an
  oracle anywhere in this verification).

## 3. F-7L-1 — independent production-source reconstruction

Read directly from `src/pcae/core/hatp_mandatory_cutover.py` at HEAD, not
from any prior phase's narrative:

- Line 74: `from pcae.core.hatp_class_b_conformance import
  verify_class_b_deployment_conformance` — confirmed.
- Line 952 (inside `_assess_hatp_mandatory_activation_readiness_at_root`):
  `class_b_result = verify_class_b_deployment_conformance(...)`. Counted
  8 `checks.append(...)` call sites (lines 803, 818, 848, 859, 898, 912,
  932, 965) — `class_b_deployment_conformance_satisfies_readiness` is
  literally the eighth and last. `assess_hatp_mandatory_activation_
  readiness` (line 979) is confirmed the sole caller (line 993).
- Lock-held re-invocation confirmed at the write path: `_write_cutover_
  transition` acquires `fcntl.flock(lock_fd, fcntl.LOCK_EX)` (line 668),
  then calls `readiness_check()` (line 682) before permitting a
  `HATP_MANDATORY` transition; `_activate_hatp_mandatory_at_root` passes
  `readiness_check=lambda: _assess_hatp_mandatory_activation_readiness_
  at_root(...)` (line 1049) — the same function, re-invoked under lock,
  immediately before any real write.
- Repository-wide grep (`grep -rn "assess_hatp_mandatory_activation_
  readiness\|verify_class_b_deployment_conformance" --include="*.py"
  src/pcae/`): the verifier's only production reference sites are its own
  definition (`hatp_class_b_conformance.py`) and
  `hatp_mandatory_cutover.py`. No other production module calls it.
- Certification independence confirmed: `hmic_verified` (readiness term
  at cutover.py:887, driven by `certification_status_satisfies_
  readiness`) and `class_b_satisfied` (cutover.py:955) are two distinct,
  independently computed readiness terms; `hatp_mandatory_certification.
  py`'s validator (`validate_active_hatp_mandatory_independent_
  verification_certification`) neither calls nor is called by
  `verify_class_b_deployment_conformance`.
- Chronology independently confirmed via `git log --oneline`: 149O.20L.3's
  wiring commit `e2ccb7a3` sits at line 231 (more recent than 149O.20K's
  substantive commit `3e1137ef` at line 279, older than 149O.20L.7K's
  commit `13a35e34` at line 16). Ordering: 149O.20K → 149O.20L.3 wiring →
  149O.20L.7K, exactly as 149O.20L.7L.1 claimed.

**Categorical consumption (independently derived, not asserted by
analogy):** Readiness — **yes**, direct call. Activation — **yes**,
indirect via the same lock-held readiness re-check; no separate
activation-time call exists. Certification — **no**, independent function
chain. Other production paths — **none found**.

**F-7L-1 verdict: CLOSED.** The repaired text at HMIC-REQ-052 limb (c)'s
closing paragraph, §55.4, §55.15, and attack row 39 clause (a) is
independently confirmed accurate. §53.4 (149O.20K's own historical
verdict) is correctly and legitimately left unmodified as an accurate
historical snapshot, since it predates the 149O.20L.3 wiring — verified
by the chronology above.

## 4. HMIC-REQ-052 limb (c), §55.4, §55.15, attack rows 38/39 — text audit

Read directly at HEAD:

- HMIC-REQ-052's normative membership test ("any file reachable from
  `verify_class_b_deployment_conformance`'s own call graph...", "or...
  the `DeploymentBinding` producer/rotation/revocation functions...") is
  **byte-identical** to pre-repair — only the closing paragraph's
  *descriptive* characterization of the first anchor's anticipatory
  status changed. No `HMIC-REQ-###` text was added, removed, or
  reworded; the closure rule itself is untouched. **No new normative
  duty was introduced** — this is a factual correction, not a scope
  change.
- §55.4's scope note and §55.15's verdict correction are internally
  consistent with each other, with §56.1-56.5, and with the production
  source reconstructed in §3 above.
- Attack rows 1-39 independently confirmed uniquely numbered, sequential,
  non-contradictory. Row 38's repair (28-file threshold long superseded
  by the 30-file set; verifier now has a real consumer) is accurate. Row
  39's repair correctly regrounds clause (a) in the producer's true
  non-reachability fact (independently confirmed: `hatp_class_b_
  conformance.py::_check_deployment_identity` reads `DeploymentBinding`
  state via `hatp_bootstrap.py` primitives, never calling the producer)
  rather than the now-corrected consumer-status claim; legs (b)/(c) and
  the row's overall conclusion are unaffected.

**Verdict: text repair is accurate, complete for F-7L-1's own scope, and
introduces no normative weakening.**

## 5. F-7L-2 — dependency header

- `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`'s own `**Version:**`
  header line reads `1.1` — confirmed directly.
- `derive_contract_versions` executed live against HEAD:
  `{'HMRC-001': '1.1', 'HATP-001': '1.0', 'HSCE-001': '1.1', 'RAE-001':
  '1.0', 'HBDC-001': '1.1'}` — matches the repaired `Depends on` header
  exactly.
- Precedent: §54 (149O.20L.1A) repaired the identical defect class for
  `HMRC-001`'s header in the same document; §52 (149O.20D.1) previously
  demonstrated this project's own precedent tolerates even a same-version
  *scope-widening* repair (adding `HBDC-001` to `implementation_scope_
  digest`), which is more invasive than 149O.20L.7L.1's pure header-text
  fix. F-7L-2's repair is legitimate under both precedents, a fortiori.

**F-7L-2 verdict: CLOSED.**

## 6. Same-version repair legitimacy / version-policy verdict

`HMIC-REQ-052`'s normative membership test is unchanged (§4); only
descriptive prose was corrected (§55.4/§55.15/limb-(c) closing paragraph/
attack rows 38-39/header). No file was added to or removed from
`HMIC-REQ-050`. **Verdict: SAME-VERSION REPAIR VALID.**

- HMIC version identity: `**Version:** 1.4` confirmed at the document
  header; no `v1.5` string appears anywhere in the document
  (`grep -n "v1\.5"` returns nothing) — no mixed-version state.
- `HMIC-REQ-050` immutability: independently re-extracted the fenced
  30-entry enumeration (lines 545-574) and diffed programmatically
  against production's `_FROZEN_SRC_PCAE_RELATIVE_FILES +
  _FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` — **entry-for-entry exact
  match, zero divergence**, same order, 30/30.

## 7. Digest, byte-identity

- `derive_implementation_scope_digest` recomputed live against HEAD:
  `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` —
  matches the expected value exactly.
- Same recomputation against a disposable worktree at the pre-repair
  commit `95cfd008`: **identical digest** — confirms the digest is
  causally unaffected by the contract-text-only edit (the contract
  document itself is not among the 30 frozen members; only file bytes of
  the 30 members feed the digest).
- `git hash-object` comparison (HEAD vs. `95cfd008`) for
  `hatp_mandatory_certification.py`, `hatp_mandatory_cutover.py`,
  `hatp_deployment_binding_admin.py`, `scripts/hatp_deployment_binding_
  admin.py`, `repository_identity.py`, `hatp_bootstrap.py`, and
  `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`: **all seven byte-identical**.
- **Contract identity consequence** (distinct from implementation
  identity): `HMIC-001`'s own document bytes *did* change — this is a
  contract-identity consequence, correctly not conflated with the
  unchanged implementation/source digest. No certification exists on any
  host for this distinction to invalidate.

## 8. F-7L-7 — guard-tightening adversarial verification

The two 7I/7J textual guards were tightened from whole-file exemption
(skip `hatp_mandatory_certification.py` outright) to occurrence-
granularity exemption (scan it, fail only on lines whose first token is
`import`/`from`). Independently confirmed both tightened assertions pass,
and the module's three known non-import literal occurrences (lines
952/983/1008) still pass.

**Adversarial construction (independently run, not inherited):**

| case | textual guards (7I/7J, in the exempted cert module) | AST guard (`test_no_module_under_src_pcae_imports_the_producer_at_ast_level`) |
|---|---|---|
| `import pcae.core.hatp_deployment_binding_admin` | catches | catches |
| `from pcae.core.hatp_deployment_binding_admin import create_deployment_binding as c` | catches | catches |
| indented/whitespace-varied import | catches | catches |
| **`from pcae.core import hatp_deployment_binding_admin`** (single line) | **catches** | **does NOT catch** |
| **`from pcae.core import (\n  hatp_deployment_binding_admin,\n)`** (multi-line, parenthesized) | **does NOT catch** | **does NOT catch** |

Root cause, independently traced: the AST guard's helper (`_pcae_imports`
in `tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_
independent_verification.py`) only records `ast.ImportFrom.module` for
`from X import Y` nodes — it never inspects `node.names` — so `from
pcae.core import hatp_deployment_binding_admin` is recorded only as
`pcae.core`, never as containing the producer's name. This is a real,
concrete, reproducible gap (verified with actual `ast.parse` calls
against literal adversarial snippets, not asserted), not a hypothetical
one: a standard, common Python import idiom for importing a submodule by
name evades what 149O.20L.7L.1's own §56.10 calls "the primary semantic
protection." For the **multi-line, parenthesized** form specifically,
this evades *both* the AST guard *and* the tightened textual guards in
`hatp_mandatory_certification.py` — the one file that actually carries an
exemption — directly contradicting §56.10's claim that "a future real
import statement referencing the producer would now be caught by these
two tests independently of the AST guard, not only by it."

This gap **predates 149O.20L.7L.1** (the `_pcae_imports` helper is
untouched by `ae9da630`'s diff) — it is not a regression this phase
introduced, and it does not affect F-7L-1/F-7L-2's own closure. But
149O.20L.7L.1's own F-7L-7 adjudication overstated the post-tightening
guard's completeness.

**F-7L-7 verdict: REPAIR INCOMPLETE** — the textual-guard tightening
itself is correctly implemented for its literal stated goal (first-token
occurrence detection), but the "AST guard is primary, strictly stronger,
and would independently catch a future import" claim in §56.10 does not
hold for `from package import submodule` forms, single- or multi-line.
No production source is affected; this is a test-coverage gap, not a
production defect. **Not edited** (verification-only phase) — recommend
a narrow follow-up: extend `_pcae_imports` to also record `alias.name`
for each name in `ImportFrom.names` (qualified as `f"{node.module}.
{alias.name}"`), which would close both the single-line and multi-line
gaps at once since it is AST-based.

## 9. F-7L-5 — independent, row-by-row adjudication (not inheriting labels)

**Row 38:** Independently re-derived — correctly repaired. Was a direct
restatement of the exact F-7L-1 claim (§3 above); production has been
realigned to the full 30-file set since 149O.20L.7K, and the verifier has
a real consumer (§3). "Operative and consequential" is accurate.

**Rows 33, 34, 36, 37 — 149O.20L.7L.1 deferred these as "requiring wider
architecture interpretation... outside this phase's own narrow evidence
chain" (§56.9). Independently re-checked against live production; this
deferral rationale does not hold up:**

- **Row 33** claims "production still computes the twenty-two-file
  digest." Independently verified: production's `_FROZEN_AUTHORITY_
  BEARING_FILES` is asserted `== 30` (§6 above). **This claim is false
  today** — trivially checkable by reading the live production constant,
  requiring no phase-history archaeology at all.
- **Row 36** claims "production still computes the four-member set" (for
  `contract_versions`). Independently verified: `derive_contract_
  versions()` executed live returns **five** members (§5 above). **False
  today** — same triviality.
- **Row 37** claims "production still computes the twenty-four-file
  digest." Same fact as row 33 — production computes over 30 files.
  **False today.**
- **Row 34** claims "the hard-coded `mandatory_consumption_
  implementation_independently_verified = False` ceiling remains
  unchanged and zero readiness/cutover callers of the validator exist...
  no functional readiness decision depends on which file count
  production currently computes over." Independently verified **false on
  every clause**: (a) `hatp_mandatory_cutover.py` (§3 above, lines
  876-899) computes `hmic_verified` live via `validate_active_hatp_
  mandatory_independent_verification_certification(repository_root)` —
  not a hard-coded `False` — and appends it as the readiness term
  literally named `mandatory_consumption_implementation_independently_
  verified`; this **is** a readiness/cutover caller of the validator.
  (b) That validator's own `_validate_at_root`, "Step 9" (lines
  2038-2053), freshly computes `derive_implementation_scope_digest` and
  rejects with `IMPLEMENTATION_MISMATCH` on any divergence — i.e. a real
  readiness decision *does* depend on the current file-count/digest.
  Independently traced via `git log --oneline` that this Wave F wiring
  (`478f8b2c`, "Phase 149O.19.5F: HMIC Activation-Readiness Integration")
  landed *after* 149O.19.5E.1 wrote row 34's text (149O.19.5E.1's own
  commits sit at line ~419-423 of `git log --oneline`, versus 149O.19.5F
  at line ~404 — more recent) — i.e. this row's claim was accurate when
  written and has been stale ever since, structurally the **same defect
  class F-7L-1 itself found and repaired**, just for the certification
  validator instead of the Class-B verifier, and dating back roughly a
  hundred phases further than F-7L-1's own defect.

None of the above required "independently re-deriving multiple earlier,
separately-governed alignment phases" as §56.9 claims — establishing that
each of these four claims is **currently false** required only reading
today's live production constants and (for row 34) two `git log` greps,
the same class of direct verification F-7L-1 itself modeled. These are
**current, present-tense assertions in the live, operative Attack-
Resistance Matrix** (§41) — not framed as historical narrative the way
§53.4 legitimately is (embedded in a dedicated "Contract Amendment
History — Phase 149O.20K" section, explicitly scoped to that phase's own
entry state). Per this phase's own governing distinction: "a historical
snapshot may stay historical; a current contract assertion may not" —
rows 33/34/36/37 are current assertions, not historical snapshots, and
they are false.

**F-7L-5 verdict: rows 33/34/36/37 — REPAIR INCOMPLETE (independently
found: current, false, live claims, wrongly deferred). Row 38 —
CLOSED.** This is not a regression 149O.20L.7L.1 introduced (these four
rows were equally false before 149O.20L.7L.1 ran); it is a genuine gap
in 149O.20L.7L.1's own whole-document stale-claim search (item 8/34 of
this phase's own governing scope), which evidently stopped at the rows
matching F-7L-1's specific evidence chain rather than checking every
"not yet operative" occurrence against current production state.

## 10. Carried findings — confirmed unchanged

`HMIC-REQ-103`'s revocation-validation gap, 7J §17's audit-failure-after-
mutation gap, `hatp_bootstrap.py::_parse_iso_timestamp`'s permissive
parser (confirmed present, byte-identical hash, §7), `HMIC-REQ-063`'s
import-shadowing limitation — all confirmed present, none claimed
repaired, none touched.

## 11. 7J §31 source-scope finding — status

**NOT CLOSED.** F-7L-1 and F-7L-2 are independently confirmed CLOSED, and
the 30-member scope/digest/production-alignment work underlying the 7J
finding is independently confirmed correct (§6-7). But this phase's own
governing scope is explicit: "Only after a **clean** 149O.20L.7L.2 may
the 7J §31 source-scope finding be closed." Given §9's finding, this
verification is not clean — the finding does not close.

## 12. Regression evidence (A/B, disposable worktree at true phase-entry commit `95cfd008`)

- **Targeted 22-item selection** (the 6 phase-adjacent test files):
  16 failures at HEAD, 17 at baseline; `comm` diff shows **zero new
  failures**, one resolved (`test_derived_versions_now_match_the_
  depends_on_line_exactly` — exactly the header fix in §5).
- **Full raw `-m fast_green` suite**, run twice (HEAD and baseline
  worktree, in parallel, `--ignore` on the one file needing an unmet
  optional `fido2` dependency — confirmed pre-existing/environmental at
  both commits): HEAD = 253 failed / 7552 passed / 5 skipped / 9 errors
  (7m57s); baseline = 254 failed / 7551 passed / 5 skipped / 9 errors
  (7m17s). Full `FAILED`/`ERROR` node-ID sets extracted and diffed with
  `comm`: **262 vs. 263 unique node IDs, zero new, exactly one
  resolved** (the same header-fix test). This raw count (262 pre-existing
  failures) is far larger than 149O.20L.7L.1's own report characterized
  ("0 failed" after an unlisted deselect set) — the underlying safety
  property (zero regression caused by this repair) is independently
  confirmed and, if anything, on stronger evidence (a full diff of every
  failing node ID, not a curated deselect list), but the raw scale of
  this repository's accumulated historical self-pin debris is
  substantially larger than 149O.20L.7L.1's phrasing implied. No
  backend_cli/shell_gate flakiness was observed in this run (both runs
  fully deterministic and identical modulo the one resolved test).
- New focused regression module (`tests/test_phase_149o_20l_7l_1_hmic_
  consumer_status_and_dependency_header_repair.py`): **20/20 pass**,
  independently reviewed — covers the dependency-header fact, the
  direct-consumer fact (no line-number pins), the third-anchor fact, row
  38/39 coherence, and no-normative-or-production-change guards. None of
  these 20 tests guard against the F-7L-5 finding in §9 (expected — that
  finding concerns rows this phase's own test suite never targeted).
- `tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_
  independent_verification.py`: 60/60 pass, including the AST guard test
  itself (which passes today only because no adversarial import
  currently exists in the tree — §8's finding is about the guard's
  future robustness, not a present failure).

## 13. No-Dell / no-first-use proof

No `ssh`/Dell command was run this phase. `find` for `repository-
identity.json`, `deployment-binding.json`, `certifications.json`,
`certification-bindings.json`, `active-certification.json` anywhere in
the repository: zero matches. `git status --short`: clean (no stray
artifacts from this phase's worktree/digest testing). No `RepositoryIdentity`,
no `DeploymentBinding`, no election, no CHGR, no certification, no
activation, no Boundary A/C action, no HATP mutation of any kind.

## 14. Governance

`pcae health`/`check`/`status coherence`: clean throughout. No `git
commit`/`git push` used directly — this phase's finalization uses `pcae
commit`/`pcae push` per the governed lifecycle. No `--no-verify`, no
force push, no hook bypass.

## 15. Final verdict

**NOT VERIFIED — CONTRACT REPAIR INCOMPLETE.**

F-7L-1: **CLOSED.** F-7L-2: **CLOSED.** F-7L-5 row 38: **CLOSED.** F-7L-5
rows 33/34/36/37: **REPAIR INCOMPLETE** (independently found: current,
false, live attack-matrix claims, wrongly deferred — §9). F-7L-7:
**REPAIR INCOMPLETE** (§8: the textual-guard tightening itself is
correct, but the companion AST guard's claimed completeness does not
hold against `from package import submodule` forms). 7J §31
source-scope finding: **remains NOT CLOSED.** `HMIC-001` remains v1.4.
`HMIC-REQ-050`'s 30-file enumeration and production alignment are
independently confirmed correct and unchanged. `implementation_scope_
digest` is independently confirmed unchanged. Zero production behavior
change (byte-identical hashes, §7). Zero regressions (§12). No
`DeploymentBinding`, no `RepositoryIdentity`, no election, no CHGR, no
certification, no Dell access, no Boundary C/A work (§13). HATP
production remains **NOT READY**. Runtime remains **Observed / observe /
unavailable**.

## 16. Recommended next phase

**149O.20L.7L.3 — Attack-Matrix Rows 33/34/36/37 and AST-Guard
Multiline-Import Narrow Repair.** Scope: (a) correct rows 33/34/36/37's
"not yet operative"/"production still computes the N-file/M-member set"
language to reflect that production has been realigned past every
threshold those rows name, mirroring exactly how 149O.20L.7L.1 repaired
row 38, including row 34's additional "hard-coded ceiling"/"zero
readiness callers" clauses (both now false — §9); (b) extend
`_pcae_imports` (`tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_
amendment_independent_verification.py`) to record `ImportFrom.names`
(not only `.module`), closing the single- and multi-line `from package
import submodule` gap identified at §8; (c) re-run the identical
whole-document stale-claim scan this phase performed (§9), not merely
the F-7L-1-shaped subset, to rule out further undiscovered instances of
the same defect class elsewhere in the document. Same-version,
contract-text-and-test-only repair expected — no production source
change anticipated. Only after a clean re-verification of *that* phase
may the 7J §31 source-scope finding close, and only after that may a
separately-governed phase address first-use sequencing architecture
(149O.20L.7M or equivalent). No binding, election, certification,
redeployment, or Dell mutation is authorized by 149O.20L.7L.2 or by its
recommended follow-up.
