# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.17R.1 Complete — Independent Verification of the Gate-10 Slice-A Reconciliation

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.17R.1
**Type:** independent verification (RE-DERIVE, DO NOT TRUST) of `.1R.17R` (Gate-10 Slice-A Scope-Fence and Verification-Evidence Reconciliation)
**Status:** INDEPENDENTLY VERIFIED WITH NON-BLOCKING FINDINGS — GATE-10 SLICE-A RECONCILIATION COMPLETE
**Verification-entry SHA:** `ab36dc97` (`.1R.17R` finalize head; `origin/main..HEAD = 0` at entry)
**Immutable pre-`.1R.17` baseline:** `1f8b9c76` (independently verified: `git rev-parse 302f5aba^` = `1f8b9c76`)
**Original `.1R.17` head:** `c618134a` · **`.1R.18` finalize / `.1R.17R` reconciliation-entry:** `3aef3b79` · **`.1R.17R` reconciliation range:** `d04a2830..ab36dc97` (7 commits; guard changes all in `d04a2830`) · **`.1R.15.3` byte-scope baseline:** `4d480553`
**Production source changed:** none (`git diff c618134a HEAD -- src/pcae` empty; `git diff --name-only 1f8b9c76 HEAD -- src/pcae` = the single pre-existing `.1R.17` file)
**Normative contracts changed:** none (`git diff 1f8b9c76 HEAD -- docs/contracts docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` empty)
**Scope-fence guards changed:** none by this phase — it re-derives and adversarially challenges the `.1R.17R` guards only
**Runtime:** `not_implemented / Observed / observe / unavailable`; POL-005 hard DENY; 0 plugins / 0 capabilities; `pcae runtime inspect` byte-identical at entry and finalization

## Adjudications

| Target | Result |
|---|---|
| `.1R.18` LIFECYCLE / REGRESSION BLOCKER | **CLOSED** |
| GATE-10 SLICE-A SCOPE-FENCE RECONCILIATION | **CLOSED** |
| `.1R.17` VERIFICATION-EVIDENCE ERRATUM | **CLOSED** |
| SLICE-A LIFECYCLE ACCEPTANCE | **CLOSED** |

`.1R.18` remains historically the BLOCKED IV that discovered the defect — not retroactively rewritten.

## Fixed-SHA A/B (re-run; dedicated `git worktree`s, deterministic `-p no:randomly`, NO xdist, identical `-k` selection)

* **Historical reproduction:** A = `1f8b9c76` = **29** failing / B = `c618134a` = **47** failing → **18 added, 0 removed**. The **17** `.1R.17`-attributable added nodes reproduce PASS@baseline / FAIL@`c618134a` and map **one-to-one** onto the `.1R.17R` §5 table (14 consumer-inventory allowlists + 1 `.1R.15.5` byte-scope + 2 docstring-grep false positives). The 18th added node — `test_concurrent_conflicting_successors_have_one_canonical_winner` (`…_1r321.py`) — is **exactly** the pre-existing HPAC-lifecycle concurrency flake `.1R.17R` §4 / §12 disclose as non-attributable; it passes on the repaired-HEAD run (**non-blocking finding N-17R1-1**).
* **Repaired-tree acceptance:** A = `1f8b9c76` = **29** / HEAD = `ab36dc97` = **29**, with the **failing-node sets byte-identical** (`comm` diff empty both ways) → **0 added, 0 removed, 0 candidate-only unexplained**. The closure gate holds under independent reproduction.

## What was independently re-derived

* **Immutable SHAs** from git (`302f5aba^` = `1f8b9c76`; range and ancestry confirmed).
* **One-to-one 17-node mapping** onto `.1R.17R` §5 — no node lost in an aggregate count; classification split 14 CI + 1 BS + 2 DG.
* **Reclassified node** `.1R.14::test_gate9_is_sole_production_owner_of_consumption_boundary` (stale → 2nd docstring-grep FP): **source-supported** — both DG guards grep the identical regex; in `runtime_dispatch_gate10_eligibility.py` `run_gate9_atomic_authority_consumption` appears **only** at module-docstring line 39 (`ast.get_docstring` confirms), `_GATE9_RESULTS` never. `.1R.18` was imprecise (one of two guards sharing a root cause), not `.1R.17R` misclassifying.
* **Every widened allowlist** (`git show d04a2830`): explicit / finite, grew by **exactly** `runtime_dispatch_gate10_eligibility.py` (checked against a live `git grep -l` per pattern), `==` stays `==` / `<=` stays `<=` — **no equality→subset downgrade**. Two guards **strengthened**.
* **Adversarial battery:** every reconciled guard rejects an invented first-effect `runtime_dispatch_gate10.py`, an invented effect-bearing adapter, and an arbitrary module — none exists as a real file; no effect-bearing consumer is admitted.
* **`.1R.15.5` byte-scope fence:** its `forbidden = {gate5, permission, gate7, gate8}` assertion is **separate from** and **untouched by** the widened `allowed` set; `git diff 4d480553 HEAD -- src/pcae/core` is disjoint from `forbidden`; a synthetic Gate-5 change still trips it.
* **Both docstring-grep repairs** track code semantics — a real `import` + call is detected, docstring/comment prose is ignored, f-string `{names}` are kept; **non-blocking finding N-17R1-2**: a string-literal-only `getattr`-by-name reference would be stripped, but `ast` inspection confirms no such reference exists for any guarded Gate-9-internal symbol; the "semantic consumer" intent is preserved.
* **Original `.1R.17` doc** is a strict-prefix append (`## ERRATUM` absent from `c618134a`); sections 1–14 byte-unchanged; the original incorrect "ADDED failures = 0" / "A = B = 29" claims still visible as history; immutable `.pcae/phase-reports/*1R.17*` and `.pcae/finalization-transactions/*1R.17*` `git diff` empty.
* **Erratum** provenance, quantitative truth (vs. reproduced evidence), and chronology (commit `b4f36d2f` 20:53 later than `c618134a` 17:05; "disproved", not rewritten).
* **N-18-2:** `GATE10_ELIGIBILITY_REASON_IDS` a `frozenset` of **39**; `git diff c618134a HEAD -- src/pcae` empty → taxonomy unchanged.
* **N-18-3 preserved:** envelope still minted on the positive path; no production suppression under an `unavailable` runtime.
* **No production / contract / Gate 5–9 drift**; runtime non-executing; first external effect **ABSENT** (code-only token scan + AST: imports only `__future__` / `hashlib` / `pathlib` / `typing` / `pcae.core.*`; no `.dispatch(` call site); Slice-B **ABSENT**.

## Suites (deterministic, no xdist)

| Suite | Result |
|---|---|
| new `.1R.17R.1` RE-DERIVE IV suite (`…_1r17r_1.py`) | **48 passed, 0 failed** |
| `.1R.17R` reconciliation suite | 42 passed, 0 failed |
| `.1R.18` IV suite (byte-unchanged since `3aef3b79`) | 111 passed, 0 failed |
| `.1R.17` implementation suite (byte-unchanged since `c618134a`) | 65 passed, 0 failed |
| 7 reconciled guard suites in full | 468 passed, 0 failed |

**Test-weakening audit** (`d04a2830^..ab36dc97`): 0 skip/`xfail` added, 0 tests removed, 0 wildcarding.

## Carried-forward status

Coordinator / DispatchEnvelope / N-16-1 **VERIFIED**; first external effect **ABSENT**; item 9 **NOT SATISFIED / DEFERRED TO Slice B**; N-16-2 → Slice B; N-16-3..7 → Slice C. `.3` delegated finalization / commit / push incident remains **UNAUTHORIZED**.

## Non-blocking findings

* **N-17R1-1** — historical A/B reproduced 18 added, not 17; the 18th is the disclosed HPAC concurrency flake (`.1R.17R` §4/§12), non-attributable, passes on repaired HEAD. Recommend `.1R.17R` cross-reference the flake node by name.
* **N-17R1-2** — the code-only stripper removes string literals; a string-literal-only symbol reference would be filtered from the two repaired docstring-grep guards. Confirmed no such reference exists for any guarded symbol; original intent preserved.

Neither meets an early-STOP condition.

## Recommended next phase (NOT begun)

`149O.20L.7O.3W.1R.2B.1R.1.1R.19` — Dispatch-Attempt Durable Lifecycle, Idempotency, and 3S.2.1 Prerequisite Repairs (Slice B). Slice C / D keep no phase ID. Do not implement the Gate-10 effect. Do not enable execution.

---
*Canonical staging header — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.17R.1. Full detail in `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_17R_1_INDEPENDENT_VERIFICATION_OF_THE_GATE_10_SLICE_A_RECONCILIATION.md`.*
