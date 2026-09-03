# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1 — N-16-5 Protected Human-Approval Presentation and Real-Assurance Consumption Implementation After Authority Reconciliation

## Verdict

**IMPLEMENTED — INDEPENDENT VERIFICATION AND MANDATORY REAL-CTAP2-HARDWARE VERIFICATION PENDING. N-16-5 NOT CLOSED.**

The frozen protected-presentation and real-assurance-consumption architecture
established by `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R` (HPAC-PAWA-001 v1.2 +
HPAC-PPA-001 v1.0) is implemented exactly. Phase-entry SHA `A` is
`a727dbf4f160f904836905d3cb4adeba91953676`, the finalized `.30R.4R` head.
The repository was clean and synchronized at entry.

- **PAWA v1.2 presentation configuration authority:** IMPLEMENTED — IV PENDING.
- **Protected-presentation installation / currentness:** IMPLEMENTED — IV PENDING.
- **`pcae-protected-local-presentation/1.0`:** IMPLEMENTED — IV PENDING.
- **HPAC-PPA process-local non-bearer evidence-writer authority:** IMPLEMENTED — IV PENDING.
- **Explicit informed approval / REJECT / CANCEL / EOF / crash / timeout / replay / substitution fail-closed:** IMPLEMENTED — IV PENDING.
- **REAL authentication + REAL protected-presentation coupling:** IMPLEMENTED — IV PENDING.
- **`require_real_assurance` production integration:** IMPLEMENTED — IV PENDING.
- **Merged RHAMP authentication:** VERIFIED / PRESERVED (byte-unchanged).
- **N-16-5:** NOT CLOSED. **N-16-6 / N-16-7:** OPEN / UNTOUCHED. **Slice C:** not begun.
- **Runtime:** `not_implemented` / Observed / observe / unavailable; 0 plugins / 0 capabilities.
- **First external effect:** ABSENT / UNREACHABLE.
- **N-23-1:** INFO. **N-23-2:** INFO / DEFERRED — carried unchanged.
- `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

## Frozen architecture implemented

`.30R.4R` established, and this phase implements:

| Frozen decision | Implementation |
|---|---|
| INSTALLATION AUTHORITY = existing PAWA deployment owner | `production_writer(CONFIGURE_PRESENTATION_MECHANISM, …)` runs the full HPAC-PAWA-001 §33 recognition; no second admin authority |
| EXECUTABLE INSTALL MODEL = out-of-band admin install + PAWA metadata registration/pinning | `hpac_protected_presentation_admin` / `protected_presentation_installation` register and pin metadata only; the helper bytes are installed out of band at the content-addressed path; no copy / chmod / chown / package / download / exec of bytes |
| PAWA CONTRACT = HPAC-PAWA-001 v1.2 | one new `PawaOperation.CONFIGURE_PRESENTATION_MECHANISM`; taxonomy stays 21 codes; no HPAC-001 / RHAMP-001 change |
| PAWA MUTATION = `configure_presentation_mechanism` | exact closed lifecycle action `{install, rotate, revoke}`, role `presentation_mechanism_installer`, subject the exact `mechanism_id`, one bounded multi-write transaction spent once via `complete_multi_write` |
| PRESENTATION AUTHORITY CONTRACT = HPAC-PPA-001 v1.0 | `HPAC-PRESENTATION-INSTALLATION/1.0` + `HPAC-PRESENTATION-CURRENT-GENERATION/1.0` closed schemas, self-excluding digests, generation / rotation / revocation / currentness, content-addressed helper path, pinned digest, launch-time revalidation |
| RUNTIME EVIDENCE WRITER = process-local, non-bearer `protected_presentation_mechanism` | seal-guarded `mint_protected_presentation_evidence_writer`, held only by the launcher, single-use, restart-dead, non-serializable, one create-only `HPAC-PRESENTATION-EVIDENCE/2.0` write per valid `APPROVE` |
| INSTALLER != LAUNCHER != RUNTIME EVIDENCE-WRITER AUTHORITY | three distinct roles / factories; the launcher cannot configure the installation; the installer cannot emit evidence; the evidence writer cannot install |
| N-16-6 = DISTINCT / NO AUTHORITY TRANSFER | the fixed protected-helper launch grants no adapter / dispatch / executable-effect authority; static guard |

## Production surface

New:

- `src/pcae/core/protected_presentation_installation.py` — the
  `HPAC-PRESENTATION-INSTALLATION/1.0` and
  `HPAC-PRESENTATION-CURRENT-GENERATION/1.0` schemas, the content-addressed
  helper path derivation, the pre-launch helper-byte integrity check
  (non-symlink chain, regular single-link file, deployment-owner ownership,
  no group/other/configured-agent write, opened-byte SHA-256 == pinned
  `helper_sha256`, returned open fd so validation and execution address the
  same object), and `ProtectedPresentationInstallationStore` (resolution
  under §19/§20 anchor + immutable record + descriptor agreement; one bounded
  `install` / `rotate` / `revoke` configuration multi-write under §23).
- `src/pcae/core/hpac_protected_presentation_admin.py` — the **sole**
  production consumer of the `configure_presentation_mechanism` PAWA writer
  factory (HPAC-PPA-REQ-022). Inside the non-agent-importable fence.
- `src/pcae/core/protected_presentation.py` — the **sole** trusted launcher /
  mediator and evidence-writer issuer: launch-time revalidation, the fixed
  identity-preserving launch (`os.posix_spawn` of the trusted interpreter
  reading the held helper fd via `/dev/fd/N` on macOS / `/proc/self/fd/N` on
  Linux — no helper-path re-open, no substitution window), a fresh ≥256-bit
  CSPRNG nonce and a private parent/child pipe pair, the closed request /
  response protocol and every binding, and the runtime evidence-writer
  issuance + the one create-only `HPAC-PRESENTATION-EVIDENCE/2.0` write on a
  valid explicit `APPROVE`. Also the resolver-side real-attestation verifier
  `verify_protected_presentation_evidence` (imported lazily so `hpac_verifier`
  never transitively imports the admin-writer fence).
- `src/pcae/protected_presentation_helper.py` — the PCAE-owned fixed helper
  implementation (`pcae.protected_presentation_helper`): reads the canonical
  request over the private channel, deterministically renders all 13 closed
  `human_visible_facts` with C0/C1 / ANSI / OSC / bidi-override neutralization,
  requires `approval_preview_digest == human_visible_representation_digest`,
  observes the explicit election, and emits the closed one-shot response.
  There is no implicit / timeout / touch-alone approval; with no interactive
  surface and no disclosed test-only decision seam it fails closed with
  `CANCEL`.
- `scripts/hpac_protected_presentation_admin.py` — the only standalone
  administration entry point (`install` / `rotate` / `revoke` / `status`).
  Never a `pcae` CLI subcommand; calls only `hpac_protected_presentation_admin`.
- `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_1_protected_presentation_real_assurance.py`
  — the fresh dedicated implementation suite (59 test functions).

Changed:

- `src/pcae/core/hpac_protected_admin_writer.py` — `PawaOperation.CONFIGURE_PRESENTATION_MECHANISM`;
  `_PRESENTATION_CONFIG_OPERATIONS` / `_MULTI_WRITE_OPERATIONS`; the
  `presentation_mechanism_installer` mint role for that op; `mechanism_id` /
  `presentation_action` handle slots and consume checks; `context_annotation`
  carrying the transaction id + lifecycle action into issuance audit;
  `AUTHORIZED_FACTORY_CONSUMERS += "pcae.core.hpac_protected_presentation_admin"`;
  the seal-guarded `mint_protected_presentation_evidence_writer` runtime
  evidence-writer factory with `PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS`.
- `src/pcae/core/approval_presentation.py` — `_verify_installed_attestation`
  gains a real `pcae-protected-local-presentation/1.0` branch that delegates to
  `protected_presentation.verify_protected_presentation_evidence`; the
  `deterministic-test-fixture` fail-closed discipline is preserved byte-for-byte.
- `src/pcae/core/hpac_verifier.py` — `require_real_assurance` now additionally
  requires a real authentication mechanism (`hpac.fido2.uv_presence.v2`) **and**
  a real presentation mechanism id (`pcae-protected-local-presentation`);
  neither alone, and no fixture, satisfies it (HPAC-PPA-REQ-057 / RHAMP-REQ-038).
  The stale "not accepted until `.1R.32`" comment is corrected.

Not touched: `runtime_dispatch_gate5.py`, `runtime_dispatch_gate9.py`,
`runtime_authority.py`, `hpac_foundation.py`, every RHAMP / FIDO2 module,
`pyproject.toml`, and every normative contract. Gate 5 and Gate 9 consume real
assurance through their **existing frozen** `principal.assurance_class is
HPACAuthorityClass.PRODUCTION` check (`validate_approval`,
`.1R.6 §8`), which this phase makes reachable **only** through the coupled real
path; no Gate source change is required or made.

## Trusted launch and the HPAC-PPA-REQ-030 boundary

`fexecve(2)` is not usable via `ctypes` on macOS (the symbol is not exported),
and `execve("/dev/fd/N", …)` of a `#!`-script fails on macOS. The
implementation therefore uses the frozen interpreter (`sys.executable`, a fixed
compiled-in trusted path) with `-I` (isolated mode) reading the **held** helper
descriptor via the platform-equivalent identity-preserving handle
(`/dev/fd/N` on macOS, `/proc/self/fd/N` on Linux). The descriptor is opened
once with `O_RDONLY | O_NOFOLLOW`, fstat-validated, and hashed, and is held
open for the entire ceremony — the referent inode of an open descriptor cannot
change under it, so there is no path re-open and no substitution window
(HPAC-PPA-REQ-030). This is not a BLOCKED condition: RHAMP-REQ-087 items (1)
pinned executable digest verified immediately before launch and (2) the
administrator-installed descriptor digest + `verifier_configuration_digest` are
both established on the same opened object.

## Guard reconciliation

Every point-in-time scope-fence guard broken by this phase's legitimate
production surface was reconciled **phase-aware, widened not weakened** — no
`def test_` removed or renamed, no wildcard / `fnmatch` / skip / xfail
introduced, subset/`==` orientation preserved, every widening carries an
explicit `.1R.30R.4R.1` comment and an exact filename:

- `.30R.4R` contract-reconciliation suite — `test_32` / `test_35` / `test_36`
  re-anchored to the finalized `.30R.4R` head with the exact `.1R.30R.4R.1`
  file set; the launcher now exists and carries no first external effect.
- `.30R.4` BLOCKED suite — the `configure_presentation_mechanism` mutation and
  the `hpac_protected_presentation_admin` consumer are added; the historically
  proposed generic `install_presentation_mechanism` verb is still absent and
  `approval_presentation` is still not a factory consumer; the real attestation
  branch now delegates to the launcher verifier.
- `.30R.3.1` PAWA Slice-1 suite — `test_40` / `test_42` (exact consumer /
  importer inventory widened) and `test_87` (contract byte fence re-anchored).
- `.30R.3.4` merged-RHAMP suite — `test_01` / `test_70` / `test_72` / `test_73`
  re-anchored; a `PRODUCTION` `AuthenticatedHumanPrincipal` is now reachable,
  but only through the coupled real path; Gate 5 / Gate 9 source byte-unchanged.
- `.30R.3.6` / `.30R.3.6.1` multi-write repair + IV — `test_35` / `test_37` /
  `test_41` (the real branch is added trust) and `test_34` (the `.30R.3.4`
  suite is widened not weakened).
- `.1R.31` / `.1R.32` / `.1R.321` HPAC foundation-consumer IV suites — the
  three new core modules' exact foundation imports added to
  `AUTHORIZED_CONSUMERS` (no wildcard).
- `.30R.1` writer-anchor adjudication IV — `hpac_protected_presentation_admin.py`
  added to `_PAWA_FENCE`.
- `.1R.19R` dispatch-lifecycle reconciliation — the five changed/new src paths
  added to `_POST_1R19R_AUTHORIZED`.
- `hpac_protected_admin_writer._TEST_FACTORY_CONSUMERS` — the fresh suite name
  added (HPAC-PAWA-REQ-166, disclosed test-only allowlist, exact name).

All downstream meta-guards (`.1R.15.3::test_v15_2_guards_pass_at_head`,
`.1R.20::test_finding_n20_1/n20_3`, `.1R.19R` parametrised recovery guards,
`.1R.22R.1::test_29`) pass at HEAD after reconciliation.

## Verification evidence

- Fresh `.1R.30R.4R.1` suite: **59 passed**.
- Targeted combined affected suites (fresh suite + reconciled PAWA / PPA /
  RHAMP / `hpac_verifier` / presentation / IV suites): **559 passed, 0 failed**.
- Fixed-SHA A/B (worktree at `a727dbf4` vs HEAD, deterministic `-p no:randomly
  -n0`) over the 82-suite affected lineage: A had 131 failures, HEAD has 132.
  The four candidate-only failures are all working-tree-dirty `git status
  --porcelain` guards from unrelated HMIC Class-B phases
  (`test_phase_149o_20h_…`, `test_phase_149o_20k_1_…`, `test_phase_149o_20k_…`)
  that fire on any uncommitted `src/pcae` change and clear after the governed
  commit. **B-only unexplained functional regressions = 0.** Two tests
  (`.1R.22R::test_historical_22_node_set_reproduces_at_the_fixed_shas`,
  `::test_original_r22_completion_artifacts_preserved_unrewritten`) newly pass
  at HEAD — a reconciliation side-benefit, not a regression.
- No-test-weakening: 0 `def test_` removed or renamed across `tests/`; 0
  `pytest.skip` / `pytest.xfail` / `@pytest.mark.xfail` / `fnmatch` /
  wildcard-broadening lines added. (`.1R.22R::test_no_test_weakening_in_the_r22r_diff`
  and `.1R.22R.1::test_27` fail identically at `A` and at `HEAD` — a later
  phase added test files containing the literal string `"fnmatch"` and the
  scanner was never re-reconciled; not this phase's regression.)
- Static no-effect proof: the only process launch anywhere in the phase source
  is one `os.posix_spawn` of the trusted interpreter for the protected helper
  (HPAC-PPA-REQ-031). No `adapter.dispatch(` / `DispatchEnvelope` /
  `subprocess` / `socket` / `requests` / `urllib.request` / `http.client` /
  `asyncio` / `os.fork` / `Popen`.
- `git diff --stat a727dbf4 -- docs/contracts`: empty. HPAC-PAWA-001 v1.2,
  HPAC-PPA-001 v1.0, RHAMP-001 v1.0, HPAC-001 v2.1, RIHAC-001 v2.0,
  RIASC-001 v3.0, RDGO-001 v3.1 and every other normative contract:
  byte-identical to `A`.
- `pcae runtime inspect`: `not_implemented` / Observed / observe / unavailable;
  Registry empty; 0 plugins / 0 capabilities.
- Historical `.30R.4` BLOCKED report SHA-256 remains
  `757268a2481f8077f1c7ed7334c763383f03e7b0813222f025bee54a9ab28715`.

## No-go proof

No production Gate wiring change; no Permission Broker or policy evaluation; no
Runtime Enforcement result; no runtime capability; no `DispatchEnvelope`; no
dispatch authority; no adapter admission; no N-16-6 effect-adapter surface; no
N-16-7 runtime-capability enablement; no Slice C; no first external effect; no
new FIDO2 authentication mechanism; no new cryptography; no new dependency
(`pyproject.toml` byte-unchanged). A valid protected approval is never
interpreted as a PB `ALLOW`, a policy override, a runtime capability, a
`DispatchEnvelope`, permission to dispatch, or execution authority — even after
`require_real_assurance` succeeds.

## Exact successor

Recommended, not begun and requiring separate explicit authorization:

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.2` — **Independent Verification of the
N-16-5 Protected Human-Approval Presentation and Real-Assurance Consumption
Implementation After Authority Reconciliation** (derived under CPIPC-001).

That independent verification, and the **mandatory real-CTAP2-hardware
verification** required by RHAMP-001, must both complete before N-16-5 may
close. Historical `.30R.4` remains BLOCKED and immutable. N-16-6 and N-16-7
remain OPEN and untouched; N-16-7 is strictly last.
