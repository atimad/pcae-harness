# Phase 149O.20L.7O.2M.1 — HMIC v1.7 Trust-Enrollment Admin Entry-Point Source-Scope Evolution Independent Verification

**Status:** COMPLETE — INDEPENDENTLY VERIFIED
**Verification-only phase.** No HMIC repair, no hac-dell connection, no CertificationRecord/Principal/Signer/DeploymentBinding creation, no FIDO2/PIV hardware touch, no Protected Root mutation, no readiness/HATP-activation/Permission Broker/runtime-capability change.

## 1. Entering state / true phase-entry commit

True pre-2M phase-entry commit: `fd782695c90a8d6ac4e6dd6f985aaf3a9540101a` (149O.20L.7O.2L.4 task-lifecycle-sync commit, immediately preceding `ef2af012`, 2M's first commit). Verified via `git log --oneline fd782695..ef2af012` (exactly one commit range boundary, no other commits between).

Isolated git worktree created at this commit for the fixed pre-2M checkpoint; current HEAD used separately for the current checkpoint. No modification to either was left in place — every disposable-mutation experiment below was restored via `git checkout --` immediately after measurement (verified clean via `git status --short`).

## 2. Pre-2M checkpoint (independently re-derived)

- `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` header: `**Version:** 1.6`.
- `src/pcae/core/hatp_mandatory_certification.py`: `_FROZEN_SRC_PCAE_RELATIVE_FILES` = 27 entries, `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` = 9 entries, total 36; `assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36` present.
- `scripts/hatp_hardware_credential_admin.py` and `scripts/hatp_principal_signer_admin.py` exist on disk at this commit but are **not** members of either frozen tuple (confirmed by direct string search of the tuple literals — absent).
- **Gap mechanically proven** (§8 below): mutating both scripts at this checkpoint leaves `derive_implementation_scope_digest` byte-for-byte unchanged — exactly the security gap 2M closes.

## 3. Current checkpoint (independently re-derived)

- Contract header: `**Version:** 1.7`.
- Production: `_FROZEN_SRC_PCAE_RELATIVE_FILES` = 27, `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` = 11, total 38 (`assert ... == 38`).
- Both new scripts present in `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, absent from `_FROZEN_SRC_PCAE_RELATIVE_FILES` (correct path classification, §15).

## 4. Exact membership — contract text (independently transcribed)

Enumerated the literal fenced block in HMIC-REQ-050 directly from `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (not the production constants). 38 lines, in order, ending in the four `scripts/` entries: `hatp_certification_admin.py`, `hatp_deployment_binding_admin.py`, `hatp_hardware_credential_admin.py`, `hatp_principal_signer_admin.py`.

## 5. Exact membership — production and derived runtime

`python3 -c "... from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES, _frozen_canonical_paths ..."` at current HEAD:

- `_FROZEN_SRC_PCAE_RELATIVE_FILES`: 27
- `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`: 11
- `_FROZEN_AUTHORITY_BEARING_FILES` total: 38
- `_frozen_canonical_paths()` (derived-runtime enumeration, `HMIC-REQ-055` canonicalization applied): 38 canonical paths, exact-string comparison against the contract-transcribed set (after `src/pcae/`-prefixing) — **equal, set-for-set**.

**Contract == production == derived runtime, exact-member equality, not count-only.** No missing/extra member. §12/§13 satisfied.

## 6. Exact delta

Independent AST-based extraction of `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` from the pre-2M worktree's own `hatp_mandatory_certification.py` (36 members) diffed against current HEAD's 38 members:

- **Added:** `scripts/hatp_hardware_credential_admin.py`, `scripts/hatp_principal_signer_admin.py`
- **Removed:** none
- **Reordered/changed:** none

Exact +2 delta confirmed, no third path. (Encoded as `test_exact_delta_is_addition_of_the_two_scripts_only_nothing_else` in the new focused suite.)

## 7. Path classification (§15)

Both new members are repository-root-relative (`scripts/...`), not `src/pcae/`-relative — confirmed both structurally (tuple membership) and via `_frozen_canonical_paths()`'s canonicalization (no `src/pcae/` prefix applied to either). Matches the `scripts/hatp_certification_admin.py`/`scripts/hatp_deployment_binding_admin.py` precedent exactly.

## 8. HMIC version verification (§5)

Contract header changed 1.6 → 1.7 in lockstep with the 36→38 membership widening; matches repository precedent (v1.1/v1.3/v1.4/v1.5/v1.6 were all minor scope-evolution bumps, not schema/algorithm changes). No membership change occurred without a version bump, and no version bump occurred without a membership change. **Consistent — not Blocking.**

One **pre-existing, non-2M** descriptive-header staleness independently found during this sweep: the contract's own `**Depends on (current, HMIC-unamended):**` line states `HSCE-001 v1.1` / `HBDC-001 v1.1`, but live `derive_contract_versions()` and the live `**Version:**` headers of those two contracts return `HSCE-001 = 1.3` and `HBDC-001 = 1.2`. This exact category of defect (a stale *descriptive* header line, distinct from the real drift mechanism) was already investigated and classified Non-Blocking twice before, by Phase 149O.20L.1A (§54, finding B-149O.20L.1-1) and Phase 149O.20L.7L.1 (§56) — both explicitly held that this line is non-normative prose and that `derive_contract_versions`/HMIC-REQ-069's own live-header comparison mechanism (verified live and correct in §12 above, returning the true 1.3/1.2 values) is the actual, unaffected drift-detection mechanism. Predates 2M by multiple phases (HSCE-001 reached 1.3, HBDC-001 reached 1.2, before 2M ran); **2M did not introduce, and was not responsible to repair, this line.** Classified **Non-Blocking**, out of 2M.1's charter to repair.

## 9. HMIC-REQ-052 authority-sensitivity re-test (§6/§7)

**`scripts/hatp_hardware_credential_admin.py`** (freshly read, not trusted from 2M): owns subcommand dispatch (`enroll`/`revoke`), the in-process automatic-retry decision against the *same* `CredentialEnrollmentEvidence` (never re-touching hardware, never accepting caller-supplied identity for "recovery" — the exact defect 149O.20L.7O.2L.3 repaired), and direct invocation of `register_credential()`/`revoke_credential()`. Mutating only this file (e.g., allowing caller-supplied `signer_key_id` on `enroll`, or weakening the retry-safety no-second-`makeCredential` guarantee) can change authoritative Trust-Enrollment output while every pre-2M-frozen byte remains unchanged. **YES.**

**`scripts/hatp_principal_signer_admin.py`** (freshly read): owns four-subcommand dispatch (`enroll-principal`/`revoke-principal`/`enroll-signer`/`revoke-signer`), the `_prompt_confirm`/`--assume-yes` confirmation boundary (`ConfirmationDeclinedError` on decline — no write occurs), and exact core-writer dispatch. Mutating only the confirmation gate or dispatch logic can permit an unconfirmed authoritative write. **YES.**

Both answers independently confirmed YES, matching the expected finding in §6/§7 of the governing task.

## 10. Digest non-participation (pre-2M) — mechanical proof (§8)

At the pre-2M worktree checkpoint: baseline `derive_implementation_scope_digest` = `cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f`. Appended a byte to **both** `scripts/hatp_hardware_credential_admin.py` and `scripts/hatp_principal_signer_admin.py` (disposable, `git checkout --` restored immediately after). Digest recomputed: **identical**, `cd021db4...`. This is the exact security gap Phase 149O.20L.7O.2M closes.

## 11. Digest participation (current) — mechanical proof (§9)

At current HEAD: baseline digest = `3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e`.

- Mutating only `scripts/hatp_hardware_credential_admin.py` → digest changes to `f87cc67fb43dfea7879bd9e699619d6d19bd850e3f17d938fb156b639f8ef533`.
- Restored, then mutating only `scripts/hatp_principal_signer_admin.py` → digest changes to `6cf3e39f77c141ddebf05f49ae96edc5d7d6af3ce0769fe533c04c036edfad0a`.
- Both restored via `git checkout --`; repository verified clean (`git status --short`, no output) after every experiment.

**Both scripts independently, individually confirmed digest-binding.**

## 12. Negative control (§10)

Mutated a known non-HMIC-bound current file (`PROJECT_STATUS.md`, disposable, restored) at current HEAD: digest unchanged (`3b076a639...`, identical to baseline). **Methodology is discriminating, not simply detecting arbitrary repository change.**

## 13. Complete transitive closure (§16/§17)

Direct import extraction (AST-based) of both new scripts' own `pcae.*` imports:

- `scripts/hatp_hardware_credential_admin.py` → `pcae.core.hatp_fido2_provider`, `pcae.core.hatp_hardware_credential_admin`, `pcae.core.hatp_hardware_credentials`, `pcae.core.hatp_providers` — **all four already inside the 38/36-shared frozen set** (bound since v1.5/v1.0).
- `scripts/hatp_principal_signer_admin.py` → `pcae.core.hatp_bootstrap`, `pcae.core.hatp_hardware_credentials`, `pcae.core.hatp_principal_signer_admin` — **all three already inside the frozen set.**

No new, not-yet-bound direct dependency from either script.

A recursive whole-repository import walk starting from these entry points (not gated to only authority-relevant call graphs) does reach a large tail of unrelated PCAE CLI/session/task-bookkeeping modules (`core/architecture.py`, `core/tasks.py`, `core/session.py`, `governance/publication/*`, `interactive_workflow/*`, etc.) that are **not** members of the frozen set. Traced the entry edge precisely: this tail is reached exclusively via `src/pcae/core/hatp_signing_ceremony.py`'s existing `from pcae.core.agent import build_rollback_review, lookup_promotion_execution_record` import — `hatp_signing_ceremony.py` and `core/agent.py` were **both already frozen members at v1.5** (Phase 149O.20L.7O.2H, §59), predating 2M by two phases. Neither of the two NEW files 2M added introduces this edge; it exists identically at the pre-2M v1.6 checkpoint. Confirmed `hatp_bootstrap.py` (the other new script's sole non-already-bound-adjacent import target) does **not** import `core.agent` or reach this tail.

**Verdict on §17 ("no paths.py-style omission"):** this pre-existing tail (reached via `core/agent.py`, not via either new script) is a legacy, out-of-2M-scope structural question — not a defect 2M introduced, and not one 2M's own §61 closure claim ("a fresh transitive-closure re-walk of both scripts' own import graphs found no not-yet-bound dependency") is inaccurate about, since that claim is specifically and correctly scoped to the two new scripts' own reachable graph, all of which is bound. None of the CLI/session-bookkeeping modules in the wider tail participate in provider registry/selection, hardware/crypto assertion verification, trust-store resolution, HATP verification-status derivation, RAE/HATP approval derivation, Permission Broker request construction, AG3/AG5 gating, or certification parsing/writing (HMIC-REQ-052(a)/(b)/(d)'s actual test) — they are general task/session/CLI orchestration utilities. **No Blocking source-closure defect found for 2M's own claim.** (Observation, not a finding against 2M: whether `core/agent.py`'s own further transitive imports were fully audited when it was originally bound at v1.0/v1.1 is a legacy question for a future phase to consider if ever revisited — explicitly out of 2M.1's repair charter.)

## 14. Contract identity set (§19) and live contract_versions (§20)

`_CONTRACT_IDENTITY_FILES`: exactly 7 entries — `HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001`, `HPSE-001`, `HHCE-001`. Unchanged by 2M (verified: absent from the 2M production diff).

Live `derive_contract_versions(root)` at current HEAD: `{HMRC-001: 1.1, HATP-001: 1.0, HSCE-001: 1.3, RAE-001: 1.0, HBDC-001: 1.2, HPSE-001: 1.1, HHCE-001: 1.1}` — 7 keys, matches `_CONTRACT_IDENTITY_FILES`'s ID set exactly. `HMIC-001` is correctly **not** a member (2M's own self-binding-avoidance claim, §16 below, independently confirmed).

## 15. Closed-schema parser re-test (§21) — fresh, not 2M's fixtures

New assertions (not copied from 2M's test module): valid 7-member `contract_versions` accepted; missing member (`HHCE-001` deleted) rejected; extra member (`EXTRA-001` added) rejected; malformed type (string instead of mapping) rejected; missing top-level required field (`status`) rejected; unknown top-level field rejected. All 6 pass against the real, unmocked `parse_certification_record`.

## 16. Old v1.6 certification against current v1.7 source — no grandfathering (§22/§23)

Fully isolated `tmp_path` fixture repository (never this repository's real files), synthetic frozen-set toggled between an "old" (admin-script-unbound) and "new" (admin-script-bound) configuration via `monkeypatch`, mirroring the repository's own established 149O.19.5D fixture pattern:

1. Certified under the OLD configuration (real `_append_certification_record`/`_write_active_binding`, real `_validate_at_root`) — validates `VALID`.
2. Frozen set evolved in place to the NEW (bound) configuration, **without** touching the original fixture file and **without** creating any new certification.
3. Re-validated the *same, unmodified* stored record against the *new* source: **`IMPLEMENTATION_MISMATCH`**, never `VALID`.

This is the exact "no grandfathering" property required: an old certification cannot remain valid merely because none of its originally-bound files changed — widening the frozen set itself changes `implementation_scope_digest`, and the validator's step 9 comparison (`hatp_mandatory_certification.py` `_validate_at_root`) fails closed. Independently proven with real, unmocked validator code — not asserted from 2M's own report.

## 17. Current v1.7 disposable compatibility (§24)

Same fixture harness: a fresh record built from live production derivation functions against the NEW (bound) configuration validates `VALID` end-to-end through the real `_validate_at_root` path. No real `CertificationRecord` was created against the actual Protected Root.

## 18. Self-binding consistency (§25)

`HMIC-001`'s own document bytes are confirmed absent from both `_FROZEN_AUTHORITY_BEARING_FILES` (38-member tuple) and `_CONTRACT_IDENTITY_FILES` (7-member tuple) — no recursive digest dependency (`derive_implementation_scope_digest` hashing its own governing contract, which would make the digest a function of a value the digest itself gates) was introduced. Matches 2M's own stated design choice, independently confirmed by direct tuple inspection, not by trusting the claim.

## 19. Normative stale-reference sweep (§26) and production stale-assumption sweep (§27)

Grepped `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` for `36`/`v1.6`/`thirty-six` occurrences outside the version-history amendment log (§8-§61 preamble lines, which are explicitly historical and correctly preserved) — the only current-normative enumeration section (§17, HMIC-REQ-050) correctly states 38/thirty-eight throughout, with historical widening steps narrated in past tense. No stale current-normative statement found, **except** the pre-existing §8 descriptive `Depends on` header staleness already addressed above (Non-Blocking, pre-2M, out of scope).

Grepped `src/pcae/core/hatp_mandatory_certification.py` for hardcoded `36`/`9`/`v1.6` production assumptions: only remaining literal is the `assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 38` (correct, current) and doc-comments narrating history correctly in past tense ("36-path enumeration, v1.6" appears zero times post-2M's own edit — confirmed via the `git diff fd782695..HEAD` inspection in §21 below, which shows exactly the docstring/count literals updated). **No live production logic still assumes the prior identity.**

## 20. Test-update audit (§28) — independently reclassified

`git diff --name-status fd782695..HEAD -- tests/` shows **12** modified test files (not "nine" as informally described in this task's own entering-state summary — that number traces to 2M's own report's narrower "8 test files" figure for the specific §26 stale-assumption-sweep commits `8404ed9d`+`7e19145c`, itself a different, correct count for that subset; neither figure is "nine" and neither is inconsistent once the two distinct commit groups are separated — see below). This is a documentation-precision discrepancy in the task's own entering-state paraphrase, not a defect in 2M's work.

Breakdown by commit:
- `ef2af012` (the binding commit itself): 6 modified test files, all category **A** (correctly updated live-current assertions — e.g. `test_..._2h_3...` re-asserting the widened count against live production) + 1 new file added (2M's own 28-test module).
- `8404ed9d` + `7e19145c` (the stale-assumption sweep): 8 modified test files (union), all inspected samples category **B** (correctly pinned historical truth to a fixed checkpoint via `subprocess.check_output(["git", "show", "<fixed-commit>:<path>"], ...)` rather than reading the live working tree — spot-checked `test_phase_149o_20l_7o_2i_...py`'s `test_hmic_contract_is_version_1_6_and_frozen` and `test_no_production_source_changed_since_phase_entry_commit`, both correctly re-pinned to commit `ddccb992` which independently verified to exist and correspond to Phase 149O.20L.7O.2I's own exit).

**No category C (improper rewrite of historical evidence) found in the sampled edits.** Historical phase evidence remains reconstructable via the pinned fixed-commit hashes.

## 21. Fixed historical truth preserved (§29)

`git show fd782695:src/pcae/core/hatp_mandatory_certification.py` still contains the literal `assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36`, and `git show fd782695:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` still states `**Version:** 1.6` — both immutable, git-history-preserved, unaffected by any later commit. Encoded as `test_pre_2m_checkpoint_had_exactly_36_and_lacked_both_new_scripts` in the new focused suite.

## 22. Admin script and core writer immutability (§30/§31)

Byte-for-byte `diff` between the pre-2M worktree and current HEAD, for all of: `scripts/hatp_hardware_credential_admin.py`, `scripts/hatp_principal_signer_admin.py`, `src/pcae/core/hatp_hardware_credential_admin.py`, `src/pcae/core/hatp_principal_signer_admin.py`, `src/pcae/core/hatp_fido2_provider.py`, `src/pcae/core/hatp_piv_provider.py`, `src/pcae/core/hatp_providers.py`, `src/pcae/core/hatp_hardware_credentials.py` — **all eight IDENTICAL**, zero bytes changed. 2M bound the scripts without altering their authority semantics. Encoded as a parametrized test in the new focused suite (8 cases, all pass).

## 23. NB-2L.4-1 non-interference (§32)

`git diff fd782695..HEAD --stat` confirms the only production file touched is `src/pcae/core/hatp_mandatory_certification.py` (30 lines, frozen-set constants and docstring counts only — full diff inspected, no logic change) plus one contract document. The retry-quality behavior 2L.4 left as a non-blocking observation lives in `scripts/hatp_hardware_credential_admin.py`, confirmed byte-identical (§22) — **not touched, not silently repaired.**

## 24. Current Dell interpretation (§33) — preserved, not re-verified against real host

No connection to hac-dell was made. Per the established deployment boundary (from prior phases, not re-derived here): the real Dell host runs an earlier deployed source generation; its own active certification, if any, may remain VALID for that deployed identity, but does not and cannot certify the Mac's new v1.7/38-member source — this is a structural consequence of `_validate_at_root` step 9's exact-digest comparison (§16 above), not a claim requiring a live host check.

## 25. Deployment progression / recertification / progression-gate consequence (§34/§35/§36)

If this independent verification stands (it does — see §26 Verdict), the exact next prerequisite is a **governed redeployment of the v1.7/38-member source to hac-dell**, distinct from and prior to a fresh `CertificationRecord`/activation phase (per §35's non-grandfathering property proven in §16: the old certification cannot and will not remain valid post-redeployment without a fresh certification). Real FIDO2 enrollment remains prohibited until, in order: this verification (done) → redeployment → fresh CertificationRecord → fresh activation/VALID. No step beyond independent verification was performed or authorized here.

## 26. Independent focused tests (§37)

New file: `tests/test_phase_149o_20l_7o_2m_1_hmic_v1_7_independent_verification.py` — 28 tests, not copied from 2M's own module (different fixture design, different assertions, different helper functions), covering: exact 38-member contract-text enumeration in order; production-constant equality; derived-runtime equality; pre-2M 36-member checkpoint re-derivation via `git show`; exact +2 delta via independent AST extraction; path classification; version header; digest non-participation (pre-2M-style)/participation (current-style)/negative-control (all three via disposable synthetic `tmp_path` fixtures, never this repository's real files); no-grandfathering old-vs-new-source validator proof; fresh v1.7 disposable compatibility; 6 closed-schema parser variants; 7-member contract identity; live 7-key `contract_versions`; 8-way admin/core-writer byte-immutability. **28/28 pass.**

```
$ python3 -m pytest tests/test_phase_149o_20l_7o_2m_1_hmic_v1_7_independent_verification.py -q
............................                                             [100%]
28 passed in 0.53s
```

## 27. A/B worktree regression (§38)

Fixed git-worktree comparison: pre-2M checkpoint `fd782695` vs. current HEAD, full `fast_green` marker set (`pytest -m fast_green -n auto -q --tb=no`) run identically at both:

- **Pre-2M baseline:** 333 failed, 8498 passed, 4 skipped, 9 errors (170.89s)
- **Current HEAD:** 333 failed, 8554 passed, 4 skipped, 9 errors (182.55s)

Exact failing/error node-ID set diff (`comm` on sorted `FAILED`/`ERROR` lines, 342 nodes each side):

- **Only at current HEAD (new):** `tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli` — investigated: a 15-second subprocess-timeout flake under `-n auto` parallel-worker contention (unrelated `pcae shell-gate audit verify` CLI, no HMIC/Trust-Enrollment relationship); re-ran standalone (no xdist contention) → **passes** (`1 passed in 12.05s`). Confirmed flake, not a regression.
- **Only at pre-2M baseline (resolved since):** `tests/test_phase_149o_20l_7n_1_dell_redeployment_proposition_independent_verification.py::TestCandidateCurrentness::test_head_equals_origin_main` — matches exactly 2M's own report's described "transient not-yet-pushed HEAD-vs-origin/main artifact," now resolved because `origin/main` has since caught up to `HEAD` via the actual push.

**0 attributable regressions** introduced by Phase 149O.20L.7O.2M's source/contract/test changes. The 333/9-error baseline is inherited, pre-existing, unrelated debt (mostly fixed-commit `git diff`/byte-identity self-checks from historical phases going stale as later phases legitimately touch `src`/`docs/contracts` — a documented, repository-wide, long-standing repin-debt pattern, not created or worsened by 2M or 2M.1).

## 28. Fast Green — honest raw outcome (§39)

Current HEAD, full `fast_green` marker set, single run for the record:

```
333 failed, 8554 passed, 4 skipped, 105 warnings, 9 errors in 182.55s (0:03:02)
```

Attributable regressions from 2M.1's own verification-phase changes (one new disposable test file, no production/contract file touched): **0 failed** (the new 28-test module itself is included in the 8554 passed; it introduces no failures).

## 29. No real effect (§40)

No hac-dell connection (no SSH, fetch, checkout, or file copy — confirmed by the phase's own tool-call log: only local git/pytest/python3 invocations against worktrees and the local repository were used). No FIDO2/PIV device enumeration. No `CertificationRecord`/`Principal`/`Signer`/`DeploymentBinding` created against the real Protected Root — every certification/validator exercise in §16/§17/§26 used `tmp_path` fixture repositories and fixture protected roots. No HATP activation, readiness, Permission Broker, or runtime-capability change. `pcae runtime inspect` confirms runtime state unchanged (see governance section below).

## 30. Findings

- **F-2M.1-1 (Non-Blocking, pre-existing, not introduced by 2M):** `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`'s descriptive `**Depends on (current, HMIC-unamended):**` header line states stale `HSCE-001 v1.1`/`HBDC-001 v1.1` values against live `1.3`/`1.2`. Same category of defect already twice classified Non-Blocking by precedent (§54, §56); the actual drift-detection mechanism (`derive_contract_versions`/HMIC-REQ-069 live-header comparison) is independently confirmed correct and unaffected. Not repaired here (out of 2M.1's verification-only charter).
- **F-2M.1-2 (Observation, not a defect):** the two new scripts' own transitive closure is fully bound (§13), but a *pre-existing* (v1.5-era, `core/agent.py`-rooted) tail of unrelated CLI/session modules is reachable through the already-frozen `hatp_signing_ceremony.py`. Not introduced by 2M, not part of either new script's own closure, and does not satisfy HMIC-REQ-052(a)/(b)/(d)'s actual authority-sensitivity test on inspection. No repair performed or required here.
- No other findings. **Zero Blocking findings.**

## 31. Final verdict

**A — INDEPENDENTLY VERIFIED — HMIC v1.7/38-MEMBER SOURCE IDENTITY VERIFIED — EXACT +2 DELTA VERIFIED — GOVERNED REDEPLOYMENT MAY PROCEED.**

Matches §42's expected successful finding status: "HMIC v1.7 / 38-MEMBER TRUST-ENROLLMENT ADMIN ENTRY-POINT SOURCE SCOPE → INDEPENDENTLY VERIFIED." Exact new authority-bearing members: `scripts/hatp_hardware_credential_admin.py`, `scripts/hatp_principal_signer_admin.py`. No omitted transitive authority dependency for either new script.

## 32. Next phase

Per §46: recommend the **governed hac-dell redeployment / source-parity restoration phase** for this exact independently-verified v1.7/38 identity — redeployment only, not combined with recertification. A separate subsequent phase must create a fresh `HMIC CertificationRecord`, followed by a separate activation phase, before real FIDO2 enrollment may proceed. Recommended phase ID: **149O.20L.7O.2M.2** (or the next governed hac-dell redeployment/source-parity-restoration phase in this track's own numbering convention).
