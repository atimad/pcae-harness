# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1 Complete — N-16-5 Privileged Production Authority Trust-Boundary Contract Evolution: Out-of-Process Consumer Authenticity and Typed Privileged Operations

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1`
- Alias: **N16-5-F-5-TB-CONTRACT** (operator readability only; the full canonical CPIPC id is authoritative in task state, lifecycle, reports, completion metadata, evidence, and canonical project status)
- Status: **COMPLETE — CONTRACT FROZEN**
- Predecessor: **N16-5-F-5-TB-ARCH** (COMPLETE — contract-evolution verdict B), canonical finalizing HEAD `05056eeb`
- CPIPC: valid direct `.1` successor of the predecessor — independently re-derived via `pcae.core.phase_id` (`is_valid` True; `validate` no error; `format(parse(candidate)) == candidate`; `compare` == `less`; same series `149`; same branch `O`; exactly one appended `.1` segment, 48 → 49; exact canonical text; unique against `git log --all` and `docs/` / `tasks/` / `.pcae/`; no conflicting active governed phase); alias display-only, no discrepancy

## Verdict

- **HPAC-PAWA-001 evolved v1.4 → v2.0 — MAJOR (finding S-4).** Governing rule HPAC-PAWA-REQ-152 read with HPAC-PAWA-REQ-153 (the closed MINOR-permit list) and section 80. Frozen as HPAC-PAWA-REQ-331.
- **New companion contract HPAC-PAWA-HELPER-001 v1.0 — FROZEN** (adjudication B, HPAC-PAWA-REQ-334).
- **Trust-boundary status: OUT-OF-PROCESS TYPED-OPERATION CONTRACT FROZEN / IV PENDING.**
- **F-5-B2: BLOCKED pending contract IV + implementation.**
- **F-5: CERTIFICATION BLOCKED.**
- **N-16-5: NOT CLOSED.**
- **N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly last).**
- **REPORTING-UX-1: open, non-blocking.**

## Entry state and predecessor confirmation

Branch `main`; HEAD == `origin/main` == `05056eeb`; `origin/main..HEAD` = 0;
working tree clean. Predecessor **N16-5-F-5-TB-ARCH** confirmed COMPLETE
(contract-evolution verdict B) from `PROJECT_STATUS.md`,
`.pcae/phase-completion-metadata.json` (`status: completed`), the canonical
report `docs/PHASE_N16_5_F_5_TB_ARCH.md`, and the governed done task. Carried-
forward axiom (not re-adjudicated): the frozen HPAC-PAWA-001 v1.4 consumer-
authenticity property is unsatisfiable within a same-process Python interpreter
for all four privileged factories.

## HPAC-PAWA-001 v1.4 baseline — reconstructed

Reconstructed from primary artifacts (contract header, sections 4, 5, 7C, 8,
32, 33, 33A, 33B, 36 to 39, 41, 42B, 42D, 42E, 49B, 60, 68 / 68A / 68B, 80.1
to 80.4, 90.4, 91, 92 PAWA-INV-1 to 14, 94, 95C, 96C) and the HPAC-PPA-001 v1.0
companion shape. Current version HPAC-PAWA-001 v1.4 FROZEN, MINOR (S-3);
lineage v1.0 to v1.1 to v1.2 to v1.3 to v1.4, every evolution MINOR. Trust
root: OS filesystem write authority on the out-of-band-provisioned protected
root, "never an in-process check". Section 32 predicate 6 / section 33 step 9
is the in-process calling-module authorized-factory-consumer check; sections
36 to 38 / 41 / 42B / 42D / 33B deliver an HPACWriterCapability /
HPACStoreAuthority / handle to a same-process caller. v1.4 lineage is
consistent and unambiguous — no STOP.

## Version classification — v1.4 to v2.0, MAJOR (S-4)

HPAC-PAWA-REQ-153's MINOR permits are a closed enumeration. This evolution is
outside every one of them: it **replaces a normative recognition predicate**
(section 32 predicate 6 / section 33 step 9) and **restructures the authority-
delivery model** of sections 36 to 38 / 41 / 42B / 42D / 33B from "an
in-process factory returns an HPACWriterCapability / HPACStoreAuthority /
handle to a same-process caller" to "a distinct out-of-process protected helper
performs the bounded operation and returns typed evidence only". Section 153's
closing clause ("provided no meaning above changes") is not satisfied. Section
80 requires a MAJOR to carry explicit human authorization and independent
verification — both present. Section 152 verbatim-trigger review: no trigger
fires literally (the one-shot channel is a local private pipe / AF_UNIX
socket, not remote / network / cloud; the trust root is unchanged; the
helper-hash pin is a digest, not a cryptographic authority key; consumer
enumeration is not widened by wildcard — it is replaced by the stronger
exec'd-from-the-verified-helper property). No contract-versioning-rule
ambiguity — no section 4-mandated STOP.

## Companion-contract adjudication — B (new companion)

`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`, contract id
HPAC-PAWA-HELPER-001, v1.0 FROZEN, independent `HPAC-PAWA-HELPER-REQ-###`
namespace (114 requirements), PAWAH-INV-1 to PAWAH-INV-10. Not an extension of
HPAC-PPA-001 (that contract's own sections 1 / 2 / 19 / PPA-INV-1 / PPA-INV-2
scope it to protected presentation; the helper protocol covers privileged
operations well beyond it). Not an in-line HPAC-PAWA-001 section (the helper
protocol is a self-contained specification — the REPRC-001 / PBNDE-001 /
RHAMP-001 / HPAC-PPA-001 companion-born-to-avoid-overloading-the-parent
precedent). Semantic separation preserved: protected presentation, protected
authority operations, human authentication, approval, Gate 5, counter-state
verification — all distinct.

## What v2.0 freezes

- **Section 33C** — the out-of-process `TrustedProtectedAuthorityConsumer(request)`
  conjunction: 13 conjuncts (RegisteredGenerationMatch,
  ProtectedHelperFilesystemPropertiesValid, HelperIntegrityBindingValid,
  VerifiedExecutionObjectValid, ProtectedProcessPrincipalValid,
  PrivateChannelValid, PeerCredentialValid, PAWAOSRecognitionValid,
  ConfiguredAgentIdentityBindingValid, RequestSchemaValid,
  ClosedOperationMembershipValid, OperationSpecificAuthorityPredicatesValid,
  FreshnessAndReplayPredicatesValid). Any conjunct fails → hard DENY (section
  42H); no single conjunct sufficient; no caller self-assertion; no in-process
  fallback.
- **Section 42F** — the helper performs the bounded operation in its own
  process and returns typed evidence only; no HPACWriterCapability /
  HPACStoreAuthority / handle / seal / reconstructable field set ever crosses
  back (PAWA-INV-15 / PAWA-INV-16).
- **Section 38C** — the authorized launchers are exactly the standalone
  deployment-owner entry points already enumerated (sections 38 / 38A / 38B).
- **Section 42G** — one new metadata-only mutation `configure_privileged_helper`,
  role `privileged_helper_installer`; the `PawaOperation` count becomes 7. No
  other new operation; no new certification role; no new pawa_failure_code (21
  unchanged, section 42H); no RHAMP-001 edit; no descriptor / current-
  generation schema change.
- **Section 49C** — non-bearer / restart-dead become process-boundary
  properties. **Section 68C** — every section 5 / 68 / 68A / 68B wall preserved
  verbatim. **PAWA-INV-17** — no second trust root; the helper registration is
  an integrity-pinned artifact of the existing kind.
- Requirement count 309 → 340 (contiguous 1 to 340, no gaps, no duplicates);
  invariant count 14 → 17. Every v1.0 to v1.4 requirement body survives
  verbatim; all prior freeze records immutable; v2.0 append-only.

## HPAC-PAWA-HELPER-001 v1.0 — the new companion

Freezes the `HPAC-PAWA-HELPER/1.0` protocol: helper provenance + integrity +
same-file-object validate-and-exec (anti-TOCTOU as a frozen property; a
platform without substitution-free exec STOPS BLOCKED); launcher obligations;
the private one-shot channel; OS peer-credential authentication (SO_PEERCRED /
LOCAL_PEERCRED / getpeereid platform profiles, not assumed equivalent); the
closed typed request / response schemas (self-excluding digests, unknown-field
fail-closed, CSPRNG >= 256-bit nonce); the closed operation vocabulary
(admin_mutation | certification_write over the closed five roles |
certification_read over the enumerated section 42D record set | ceremony_entry
| presentation_evidence_write; unknown / prefix / wildcard / bad-version →
DENY); freshness / replay semantics (fresh / consumed / duplicate / expired /
unknown / conflicting-replay; a lost response never frees a spent one-shot);
the state-transition model; crash / response-loss / uncertainty behaviour (an
explicit INDETERMINATE / RECONCILIATION-REQUIRED state; no auto-retry across
the mutation-attempt boundary); audit-write ordering (evidence durably staged
before the mutation, finalized after commit — the phrase "audit failure means
the mutation did not occur" is not frozen; the ordering is); the
deterministic-versus-real wall; mechanism neutrality and the mobile future;
bounded security claims. 114 requirements, PAWAH-INV-1 to PAWAH-INV-10, 35
sections.

## Cross-reference review

HPAC-001 v2.1, RHAMP-001 v1.0, HPAC-PPA-001 v1.0, HBDC-001 v1.2, RIHAC-001
v2.0, RIASC-001 v3.0, RDGO-001 v3.1, and `hpac_pawa_schemas.py` — byte-
unchanged (verified by the contract-verification suite). RHAMP counter is a
read in section 42D only — no mutation, no new terminal_reason_code, no section
49 change. One open question — HPAC-PPA-001 v1.0's evidence-writer authority
(HPAC-PPA-REQ-041) under the out-of-process model — is recorded in
HPAC-PAWA-HELPER-001 section 17 as an explicit question for
N16-5-F-5-TB-CONTRACT-IV and, if it needs a normative change, a fresh governed
HPAC-PPA-001 evolution phase; this phase does not silently edit HPAC-PPA-001.
Section 58 valid-BLOCKED discipline was considered and NOT triggered — the
evolution freezes coherently with the question deferred.

## Guard reconciliation (widen-not-weaken)

A/B: baseline `05056eeb` (phase entry, last v1.4 commit; isolated git
worktree) vs reconciled HEAD over the gsel + PPA + N-16-3/4 + v1.1-meta
guard-set. 40 pre-existing FAILED nodes at baseline; identical 40 at HEAD;
`comm -23` (HEAD-only vs baseline) empty; 0 attributable regressions. 27
attributable point-in-time guards across 17 completed-predecessor suites
reconciled: subset-widen by exactly the one new companion contract file;
re-anchor the moving `HEAD` to the fixed last-v1.4 SHA `05056eeb`; extend the
version-prefix tuple by `v2.x` and the requirement-ceiling set by
`range(1, 341)`; a new `R2` const + `at_r2` / `text_r2` helpers for the
v1.4-freeze-fact guards. 0 def-test functions renamed, removed, skipped, or
disabled; identical def-test counts per file; no bare `xfail` / `fnmatch` /
`rglob` / `mark.skip` / def-test token added in reconciliation code or
comments.

## Verification

- `pcae check` passed; `pcae health` healthy; `pcae status coherence` passed;
  `pcae doctor task-memory` warning-only pre-existing DONE.md omissions
  (unrelated completed F-5-B2 tasks), no errors, no "2 active task files".
- New contract-verification suite
  `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1_1_1_n16_5_f_5_tb_contract.py`
  — 45 tests, 45 passed, 0 failed (static / read-only).
- `git diff 05056eeb HEAD -- src/pcae scripts pyproject.toml` — EMPTY.
- `git diff --name-only 05056eeb HEAD -- docs/contracts` — exactly
  `HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` (v1.4 → v2.0 in
  place) and `HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` (new).
- Sibling contracts + schemas byte-unchanged; no protected-root or helper-
  installation artifact; no ceremony; no protected-host write.
- Runtime `not_implemented` / `Observed` / `observe` / `unavailable`; 0
  plugins / 0 capabilities; first governed runtime external effect ABSENT /
  UNREACHABLE. The in-process `_PINNED_` / `_verified_production_caller_name`
  mechanism is NOT removed by this freeze (a later governed slice; a
  compatibility shim MUST NOT preserve the insecure in-process path).

## Recommended next (derived, NOT begun)

Dedicated independent verification required first: **N16-5-F-5-TB-CONTRACT-IV**
— a dedicated independent verification of HPAC-PAWA-001 v2.0 AND
HPAC-PAWA-HELPER-001 v1.0 together (HPAC-PAWA-REQ-330 / section 80.5; required,
**not** foldable). It SHALL also adjudicate the deferred HPAC-PPA-001
evidence-writer-delivery question. THEN, each subject to its own fresh human
authorization: a privileged helper + `HPAC-PAWA-HELPER/1.0` protocol
implementation; caller integration; in-process authority-path removal (no
compatibility shim may preserve the insecure in-process path); packaging /
clean-install; a dedicated independent security IV; production deployment; and
only then a fresh **N16-5-FINAL-CERT** on a fresh CPIPC-valid successor id
(never reuse a completed or blocked certification identity). Do NOT begin
N16-5-F-5-TB-CONTRACT-IV, any implementation slice, N-16-6, or N-16-7.

## Historical governance integrity

Preserved exactly: N16-5-F-5-B2 NOT VERIFIED / BLOCKED; N16-5-F-5-B2R-IV NOT
VERIFIED / BLOCKED; N16-5-F-5-B2R2-IMPL COMPLETE — BLOCKED; N16-5-F-5-TB-ARCH
COMPLETE; DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED. Historical
HPAC-PAWA-001 v1.0 / v1.1 / v1.2 / v1.3 / v1.4 freeze records and their
independent verifications remain immutable; v2.0 is append-only.
