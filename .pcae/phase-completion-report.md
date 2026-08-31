# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22R Complete — N-16-3 Scope-Fence / Verification-Evidence Reconciliation and Repair

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.22R
**Type:** governed reconciliation / repair phase — clears exactly the `.1R.23` BLOCKER **N-23-3** (undisclosed `.1R.22`-attributable point-in-time guard-freeze failures + inaccurate `.1R.22` fixed-SHA A/B and guard-inventory evidence)
**Status:** RECONCILIATION COMPLETE — INDEPENDENT VERIFICATION PENDING (`149O.20L.7O.3W.1R.2B.1R.1.1R.22R.1`)
**Phase-entry SHA:** `2338e7c7` (`.1R.23` finalize head; `origin/main..HEAD = 0` at entry)
**Immutable pre-`.1R.22` baseline:** `8603fe6a` · **`.1R.22` finalize head:** `15aeb269` (`8603fe6a..15aeb269` = 9 commits) · **`.1R.23` finalize head:** `2338e7c7`
**Production source changed by this phase:** **none** (`git diff 2338e7c7 HEAD -- src/pcae` empty; `git diff --name-only 8603fe6a HEAD -- src/pcae` is exactly the two `.1R.22`-authorized files)
**Normative contracts changed by this phase:** **none** (`git diff 2338e7c7 HEAD -- docs/contracts` empty)
**First external effect:** ABSENT · **Execution:** not enabled — runtime `not_implemented / Observed / observe / unavailable`; POL-005 hard DENY unchanged; POL-013 never emits `ALLOW` / `HUMAN_REVIEW`; 0 plugins / 0 capabilities

## Dispositions

| Finding | Disposition |
|---|---|
| **N-23-3** — undisclosed `.1R.22`-attributable point-in-time guard-freeze failures + inaccurate `.1R.22` A/B / guard-inventory evidence | **REPAIRED** — INDEPENDENT VERIFICATION PENDING `.1R.22R.1` (not self-closed) |
| **`.1R.23` verification-evidence / regression BLOCKER** | **REPAIRED** — INDEPENDENT VERIFICATION PENDING `.1R.22R.1` (`.1R.23` remains historically **BLOCKED**; not rewritten into a successful IV) |
| **N-16-3 policy model** | **SUBSTANTIVELY VERIFIED** — carried from `.1R.23`, not reopened |
| **N-16-3 lifecycle acceptance** | **REPAIR IMPLEMENTED** — INDEPENDENT VERIFICATION PENDING `.1R.22R.1` (**NOT CLOSED**) |
| **N-22R-1** (non-blocking) — the `.1R.23` §12 inventory under-counted the attributable set by 6 | Enumeration completed to **22** by `.1R.22R`; same guard-freeze class; no production impact |
| **N-23-1** (informational) | Preserved — synthetic complete profile → bounded non-executable INV-008 `ALLOW`; the **production** narrow profile remains unsatisfiable; no production behaviour change |
| **N-23-2** (non-blocking contract-wording debt) | **DEFERRED** to a later normalization pass — no contract edit in `.1R.22R`; not independently Blocking |
| N-16-4 / N-16-5 / N-16-6 / N-16-7 | **OPEN** — untouched; Slice C / Slice D keep no phase ID |
| DELEGATED `.3` FINALIZATION / COMMIT / PUSH | **UNAUTHORIZED** (preserved) |

## Historical fixed-SHA A/B — the 22-node discrepancy

Two deterministic no-xdist `-p no:randomly` sweeps in dedicated `git worktree`s at `8603fe6a` and `15aeb269`: (i) the 11 files `.1R.23` §12 implicates; (ii) a broad ~65-file candidate sweep matching every PBRD / PBPA / POL-005 / policy-count freeze pattern.

> **22 functional guard-test nodes PASS at `8603fe6a` and FAIL at `15aeb269`**, attributable to the two authorized `.1R.22` changes (add POL-013 → canonical policy registry 12→13; PBPA-001 v1.0→v1.1 byte change; PBRD-001 v2.1→v3.0 header/body + POL-005 §12a wording). **0 attributable removals.**

`.1R.23` §12 enumerated **16**; it under-counted by **6** (2 found re-deriving the 11-file set, 4 more in the full-suite sweep — all the same PBRD v2.1→v3.0 / PBPA byte-freeze class). All 22 are **non-behavioural** stale point-in-time text / count / byte freezes. The ~41 pre-existing common failures reproduce **identically** at `8603fe6a` and at HEAD (0 A/B delta) — unrelated to `.1R.22` / `.1R.22R`, outside N-23-3 scope.

## Guard classes and repair discipline

Every widening is to an **exact finite set / exact sha256 / exact semantic property** — **no wildcard, no broad prefix glob, no "contains-expected" downgrade, no loosened invariant** — and each guard still rejects an unauthorized change.

- **Class A — policy-registry cardinality (6).** Assert `== 13` exactly (never `>=`) plus the exact canonical id set `POL-001..POL-013` (no gap, no duplicate) plus POL-013's identity. Adversarial: a 14th policy → count `14 ≠ 13`; missing POL-013 → `ValueError`; duplicate id → `ValueError`.
- **Class B — PBPA-001 v1.1 byte-freeze (6).** Repinned to the exact current sha256 `13fc441a…` plus a v1.1 / POL-013 semantic anchor. Any further PBPA byte change still fails; PBPC-001 / RWMPC-001 keep their `== ""` assertions; the v1.1 amendment is additive-only (POL-004 scope unchanged).
- **Class C — PBRD-001 v3.0 / POL-005 §12a text-freeze (10).** Rewritten to the v3.0 canonical security property: POL-005 remains a hard unconditional `DENY` for every non-eligible non-simulation domain except the exact trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` carve-out (unsatisfiable in production); POL-013 never `ALLOW` / `HUMAN_REVIEW`; MAJOR migration + "no silent auto-upgrade" + "old callers stay in the POL-005 hard-DENY domain" preserved. The brittle 1200-char text-window guard for `test_pol_005_denies_unconditionally_when_simulation_only_false` was rewritten to an AST-anchored method-body slice.

## Provenance-preserving `.1R.22` erratum

Append-only `## ERRATUM` on the `.1R.22` canonical doc **after** its original trailer; original §§1–20 are a byte-prefix of the new file; the immutable `.pcae/phase-reports/*1R.22*` md/json artifacts are byte-unchanged. It records the original claims verbatim, the corrected result (**22 attributable added, 0 removed**, non-behavioural, classes A/B/C), the full 22-node list, that **no N-16-3 policy-model defect** was found, and that the impact is a **material completeness defect** in the `.1R.22` guard inventory / A-B evidence. A matching `› ERRATUM` note is added to the `.1R.22` section of `PROJECT_STATUS.md` with the original claim preserved verbatim. **Historical truth vs repaired truth kept distinct:** `8603fe6a → 15aeb269` = 22 attributable added; `8603fe6a → .1R.22R HEAD` = 0 attributable added, 0 removed.

## `.1R.23` IV suite

Re-run and green (55/55). Four tests made **reconciliation-aware in place** (historical `.1R.23` finding kept in docstrings, repaired state asserted — the `.1R.19R` precedent for `.1R.20`'s finding tests). Two pre-existing `.1R.23`-suite bugs corrected (both failing at the `.1R.22R` phase-entry SHA before any `.1R.22R` change): a stale `BASELINE..HEAD == 9` count (only true at the `.1R.23` verification-entry SHA) rescoped to the immutable `BASELINE..R22_HEAD`; and a scanner that self-matched its own quoted `pytest.mark.xfail` string (the class `.1R.19R.1` fixed for its own suite in `dfbb79ca`) rescoped to the immutable `.1R.22` test diff. **The `.1R.23` canonical BLOCKED verdict is not rewritten.**

## Repaired-tree fixed-SHA A/B

**0 attributable added / 0 attributable removed / 0 unexplained attributable functional regressions / 0 candidate-only unexplained functional nonpassing nodes.** All 22 attributable nodes green at HEAD. The `.1R.22` 43-test policy suite: green. The new reconciliation suite `tests/test_n16_3_scope_fence_reconciliation_3w1r2b1r1_1r22r.py` (42 tests): green. Targeted PB-policy + N-16-3 suites: 626 passed, 0 failed.

## Test-weakening audit

`git diff 2338e7c7 HEAD -- tests/`: `def test_` removed = **0**; renamed = **0**; `pytest.mark.xfail` / `xfail()` added = **0**; `pytest.skip()` added = **0**; wildcard / `fnmatch` / package-prefix scope entry added = **0**; exact freeze weakened without justification = **0**.

## Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.22R.1` — Independent Verification of the N-16-3 Reconciliation.** Do not begin it in this phase. Do not skip to N-16-4. Do not implement Slice C, the first external effect, or execution enablement.

---

*Canonical completion report — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22R.*
