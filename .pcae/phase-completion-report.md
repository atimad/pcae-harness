# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.2 Complete — Independent Verification of the N-16-5 Protected Human-Approval Presentation and Real-Assurance Consumption Implementation After Authority Reconciliation

- **Status:** COMPLETE — INDEPENDENTLY VERIFIED (software) WITH ONE NON-BLOCKING FINDING
- **Type:** Independent verification. VERIFICATION ONLY — no production source or normative contract byte changed; no defect repaired inside the IV.
- **Independently re-derived anchors:** `A` (finalized `.30R.4R` head) = `a727dbf4f160f904836905d3cb4adeba91953676` (== `git rev-parse 99bc5705^`); `I` = `V` = `5b6b4013a69ffcb366209b12c495571917bb5ccc` (finalized `.30R.4R.1` head / phase entry).
- **N-16-5:** NOT CLOSED — mandatory real-CTAP2-hardware verification still outstanding (a distinct successor phase).
- **Contracts changed:** none. **Gate 5 / Gate 9 / runtime_authority / hpac_foundation / permission_broker / RHAMP-FIDO2 source changed:** none. **pyproject changed:** none.

## What was verified

Independently re-derived from primary sources (HPAC-PPA-001 v1.0, HPAC-PAWA-001 v1.2, RHAMP-001 v1.0) and running code. All sixteen product properties **VERIFIED**:

- **PAWA presentation configuration** — one bounded metadata-only `configure_presentation_mechanism`; exact role `presentation_mechanism_installer`, subject `mechanism_id`, closed lifecycle action `{install, rotate, revoke}`; multi-write spent once via `complete_multi_write`; taxonomy stays 21 codes.
- **Out-of-band executable model** — the admin and installation modules never `chown`/`copy`/`copyfile`/`copytree`/`system`/`posix_spawn`/`execv`/`Popen`; `apply_configuration` only verifies (read-only) pre-installed helper bytes and writes JSON records at `0o600`.
- **Exact PAWA consumer inventory** — `{hpac_protected_admin_writer, hpac_rhamp_enrollment, hpac_protected_presentation_admin}`, no wildcard; the standalone script reaches only the admin module; no import from `cli.py` / `commands/**` / `core/agent.py`.
- **Installation / current-generation records** — closed self-excluding schemas that recompute; `supersedes` null@gen1 / closed `{generation, installation_digest}` for gen>1.
- **Content-addressed helper path** — derived only from the pinned digest; no env / cwd / PATH influence.
- **Helper integrity** — corrupt bytes / symlinked helper / symlinked ancestor / non-regular / multi-link / wrong owner / group-other-write all fail closed via the held `O_NOFOLLOW` fd; opened-byte SHA-256 == pinned digest.
- **Generation / rotation / revocation / currentness** — monotonic G→G+1 with exact `supersedes`; a rotated generation's evidence fails resolution; revoke has no fallback; repeat install over a live lineage is rejected.
- **Installer ≠ launcher ≠ evidence-writer** — three distinct role strings/factories; the evidence-writer role is not a `PawaOperation`; `create_canonical` requires role `protected_presentation_mechanism`, so an installer capability is role/subject-ineligible (HPAC-PPA-REQ-064).
- **Helper self-authorization impossible** — the helper source holds no configuration / writer / authority symbol.
- **Fixed helper launch** — the single launch is `os.posix_spawn(sys.executable, [sys.executable, "-I", plat_fd], env, …)` reading the held helper fd via `/dev/fd/N` (darwin) or `/proc/self/fd/N` (linux); no shell, PATH, argv, cwd, network, or path re-open; the held fd stays open for the whole ceremony (no substitution window).
- **Child environment** — closed `{PCAE_PPLP_REQUEST_FD, PCAE_PPLP_RESPONSE_FD, PATH, LC_ALL}`; no authority/auto-approve/verifier-kind/helper-path selector.
- **Launch-time revalidation** — currentness re-resolved after the response; a generation switch → `ceremony_superseded` before any persistence.
- **Request / display / response binding** — ≥256-bit `os.urandom(32)` nonce; closed field sets with self-excluding digests; every response field compared to the request; re-rendered `human_visible_representation_digest` equality; a caller display fact diverging from the canonical subject → `presentation_digest_mismatch`.
- **Response vocabulary / election** — closed `{APPROVE, REJECT}`; `REJECT` → `approval_rejected_by_human`; cancel/EOF → `ceremony_cancelled`; malformed/crash → `helper_response_untrusted`; timeout → `ceremony_timed_out`; no interactive surface → fail-closed `CANCEL`; the disclosed test-only decision seam forces `test-only` mode, must acknowledge the exact rendered-byte digest, is rejected in a `production` envelope, and no production caller passes it.
- **PPA evidence-writer non-bearer / single-use / create-only** — `_single_use` true, `_multi_write` false, `PRODUCTION`; `pickle.dumps` raises; every non-launcher caller → `unauthorized_factory_consumer`; `write_atomic_create_only`; a second ceremony mints a fresh writer and a distinct evidence id; a forged/copied/replayed evidence record does not resolve (every read re-validates schema, digest, subject binding, attestation object binding, and writer provenance).
- **Real presentation verifier** — `VERIFIER_KIND == "pcae-protected-local-presentation/1.0"` exact; re-resolves the current generation, rejects a superseded/revoked descriptor digest (`ceremony_superseded`), rebinds the closed attestation object and `mechanism_attestation_digest`.
- **Deterministic seam isolation** — the deterministic mechanism id ≠ the real id and its `verifier_kind` stays `deterministic-test-fixture`; the resolver real branch matches only the exact real kind; `_REAL_ELIGIBLE_MECHANISM_IDS == {"hpac.fido2.uv_presence.v2"}` unchanged; no env/caller can select or relabel a fixture.
- **REAL auth + REAL presentation coupling** — `_authority_class_of` requires all resolved records (principal, credential, presentation, proof) to agree on assurance class, else `cross-store substitution`; `PRODUCTION` requires every record `PRODUCTION`, and the presentation record reaches `PRODUCTION` only through the real attestation branch; `require_real_assurance` additionally requires `proof.mechanism_id in _REAL_ELIGIBLE_MECHANISM_IDS` **and** `presentation.mechanism_ref.mechanism_id == "pcae-protected-local-presentation"` — "authentication alone is insufficient".
- **Gate 5 / Gate 9 consumption** — Gate 5 → `runtime_authority.validate_approval` → `reverify_authenticated_principal` → `verify_human_authentication`; the frozen NON-REAL hard stop `principal.assurance_class is HPACAuthorityClass.PRODUCTION` is inherited; `runtime_dispatch_gate5.py` / `runtime_dispatch_gate9.py` / `runtime_authority.py` byte-unchanged since `A`.
- **PB / policy / runtime / dispatch independence** — no `PermissionBroker` / `permission_broker` / `RuntimeEnforcementResult` / `DispatchEnvelope` in the phase source; the only `src/pcae` process launch is the one trusted `posix_spawn`; no `subprocess` / `socket` / `multiprocessing` import in any `.30R.4R.1` production file; `pcae runtime inspect` unchanged.

## Guard reconciliation review

Independently reviewed across eleven historical suites: authorized consumer/inventory sets widened by exact filenames/tuples with `.1R.30R.4R.1` comments and preserved no-wildcard assertions; byte-frozen guards replaced with not-weakened checks (`def ` count non-decreasing, `_ELIGIBLE_MECHANISM_IDS` literal unchanged, `fnmatch` / `adapter.dispatch(` absent, deterministic-fixture fail-closed line preserved). **No `def test_` removed or renamed anywhere in `tests/`. No `pytest.skip` / `pytest.xfail` / `@pytest.mark.xfail` / `fnmatch` / wildcard-broadening added.** The single added `skipif` is the disclosed POSIX platform guard on the fresh `.30R.4R.1` suite.

## Fixed-SHA A/B and lineage sweep

Deterministic (`-p no:randomly`) run at the `A` worktree (`/tmp/pcae-A` @ `a727dbf4`) and at `HEAD` over the affected lineage: `A` 20 failed / 656 passed; `HEAD` 18 failed / 717 passed. **B-only unexplained functional regressions = 0.** `.30R.4R.1` fixed three shared failures it targeted. The 17 shared failures are all pre-existing at `A` (the `_111r31` / `_111r321` "blocking reproduction" demo group, the `test_object_dunder_new_*` pair, the `.30R.1` contract-guard pair, `_1r19r::test_no_contract_change_since_r20_head`). **One candidate-only failure** — `.1R.19R::test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap` — classified **NON-BLOCKING** finding F-1 (below). Clean targeted affected-suite run: **684 passed, 0 failed.** The `.30R.4R.1` implementation suite rerun byte-unchanged: **59 passed**.

## Finding F-1 (NON-BLOCKING) — incomplete `.1R.19R` guard reconciliation

The pre-existing `.1R.19R` guard `test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap` ends with `assert not any("subprocess" in l or "socket" in l or ".dispatch(" in l for l in added)` over every added `src/pcae` line since `e05f0ea3`. `.30R.4R.1`'s authorized new launcher module `protected_presentation.py` contributes exactly two matching lines, both **disclaimer prose** (docstring `… generic subprocess API (HPAC-PPA-REQ-031);`; comment `# subprocess API. posix_spawn avoids fork() …`). The module has **zero** functional `subprocess`/`socket`/`adapter.dispatch` use (AST- and import-verified). `.30R.4R.1` correctly widened the sibling `_POST_1R19R_AUTHORIZED` filename allowlist in the same test but did not neutralize this separate content assertion. Classified as explained, non-functional, candidate-only guard evolution — a `.30R.4R.1` reconciliation completeness gap, not a defect in the architecture. **VERIFICATION ONLY — not repaired here.** The successor SHOULD fold this reconciliation (exclude comment/docstring lines, as `.30R.3.6.1::test_34` already does), with the sibling stale `.1R.19R` / `.30R.1` guards.

## Mandatory real-CTAP2-hardware verification — placement adjudication

Resolved from primary-source phase sequencing (RHAMP-REQ-152 "in `.1R.33`", RHAMP-REQ-153 "No hardware is accessed … before `.1R.33`'s controlled hardware session", RHAMP-REQ-156 table, RHAMP-INV-018, HPAC-PPA-REQ-074): the mandatory ≥ 1 real CTAP2 hardware verification is a **single dedicated controlled hardware session in a distinct successor phase**, not this software IV. No hardware was accessed here and **no real-hardware claim is made**. **N-16-5 remains NOT CLOSED.**

## Software implementation final verdict

**INDEPENDENTLY VERIFIED — N-16-5 PROTECTED HUMAN-APPROVAL PRESENTATION AND REAL-ASSURANCE CONSUMPTION IMPLEMENTATION COMPLETE (software).** Merged RHAMP authentication VERIFIED / PRESERVED. N-16-6 / N-16-7 OPEN / UNTOUCHED. Runtime Observed / observe / unavailable. First external effect ABSENT.

## Successor

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5` — Mandatory Real-CTAP2-Hardware Verification and N-16-5 Closure (== RHAMP `.1R.33`): the ≥ 1 real CTAP2 hardware ceremony with a genuine attached key and human gesture; the F-1 `.1R.19R` guard reconciliation (with the sibling stale `.1R.19R` / `.30R.1` guards); and — only if every frozen N-16-5 requirement is then complete — N-16-5 closure. Then N-16-6, then N-16-7 (strictly last). ID recommended NOT reserved; own explicit human authorization; do not begin.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved — this phase's governed lifecycle was performed only by the primary human-authorized operator session.
