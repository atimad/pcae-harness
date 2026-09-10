# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1 Complete — N-16-5 Privileged Production Authority Trust-Boundary Architecture: Stronger-than-Same-Interpreter Consumer Authenticity

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1`
- Alias: **N16-5-F-5-TB-ARCH** (operator readability only; the full canonical CPIPC id is authoritative in task state, lifecycle, reports, completion metadata, evidence, and canonical project status)
- Status: **COMPLETE — stronger-than-same-interpreter architecture DEFINED**
- Predecessor: **N16-5-F-5-B2-R2-IMPL** (COMPLETE — BLOCKED), canonical HEAD `089817c8`
- CPIPC: valid direct `.1` successor of the predecessor — independently re-derived via `pcae.core.phase_id` (`compare` == `less`; same series `149`; same branch `O`; exactly one appended `.1` segment, 47 → 48; exact canonical text; unique against `git log --all` and `docs/` / `tasks/` / `.pcae/`; no conflicting active governed phase); alias display-only, no discrepancy

## Verdict

- **Contract-evolution decision: B — REQUIRES HPAC-PAWA-001 CONTRACT EVOLUTION**
- **F-5-B2: BLOCKED pending stronger-boundary contract + implementation**
- **F-5: CERTIFICATION BLOCKED**
- **N-16-5: NOT CLOSED**
- **N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly last)**

## Entry state and predecessor confirmation

Branch `main`; HEAD == `origin/main` == `089817c8`; `origin/main..HEAD` = 0;
working tree clean. Predecessor **N16-5-F-5-B2-R2-IMPL** confirmed COMPLETE —
BLOCKED from `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json`
(`status: completed`), the canonical report, and the governed done task.
Carried-forward axiom (not re-adjudicated): the frozen HPAC-PAWA-001 v1.4
consumer-authenticity property is unsatisfiable within a same-process Python
interpreter for all four privileged factories.

## Baseline reconciliation — HPAC-PAWA-001 v1.3 to v1.4

Reconstructed from primary artifacts (contract header, section 7C, section
80.4, section 90.4, section 94, section 95C, PAWA-INV-14) and the predecessor
completion metadata. v1.4 is **FROZEN**, **MINOR** (S-3): one recognized
read-only `HPACStoreAuthority` accessor (section 33B / section 38B / section
42D / section 42E / section 49B / section 68B). The v1.4 trust root is
**unchanged** — OS filesystem write authority on the out-of-band-provisioned
protected root, "never an in-process check" (HPAC-PAWA-REQ-010 / REQ-300). The
section 33B / section 32 step-9 consumer-authenticity conjunct **reuses** the
same-process module-identity check now known unsound. v1.4 does **not** already
define out-of-process authority, authenticated local IPC, or a protected
helper boundary for the four factories (only the HPAC-PPA-001 ceremony hand-off
is out-of-process). v1.4 lineage is consistent and unambiguous — no STOP.

## Same-interpreter failure (reconstructed)

The section 33 recognition sequence steps 1 to 8 are OS-level; step 9 ("verify
the calling module is an authorized factory consumer", section 32 / section 38)
is the sole in-process Python-identity conjunct, implemented by
`_detect_caller_module` / `_verified_production_caller_name` over the
module-level `_PINNED_*` dicts. Two failure modes make it (and the whole
sequence) unsound in-process: (F-A) recognition bypass — in-process code can
mutate the pin state, `exec()` into the module namespace, or reach any object
via `gc`; (F-B) authority exfiltration — even a perfectly recognized caller
receives a Python authority object on a heap shared with attacker code.

## Threat model

T1 / T2 / T6 (ordinary same-interpreter code, malicious plugin, writable
source) are **not mitigated today**; the selected architecture **mitigates**
them. T7 (compromised unprivileged account on a single-account host) is
**fail-closed** by the two-principal requirement. T15 and a hostile root TCB
within the protected boundary are **explicitly out of scope** (bound claim
only, HPAC-PAWA-001 section 8 / section 60 / PAWA-INV-6, inherited). Full
T1..T15 table in the canonical report.

## Candidate architectures and selection

Compared: 6A persistent helper; 6B daemon; 6C short-lived one-shot privileged
process; 6D reuse of the HPAC-PPA-001 verified-helper pattern; 6E C-extension
opaque handle / in-process hardening.

**Selected: 6C, realized as a generalization of the IV'd HPAC-PPA-001
verified-helper pattern (6D), anchored on the unchanged HPAC-PAWA-001 section 4
filesystem trust root.** The standalone deployment-owner launcher
integrity-verifies the out-of-band helper executable (byte hash / owner / mode
/ no-symlink / same-file-object exec), opens a private one-shot parent/child
channel not inherited by agent code, and `exec`s the helper. The helper runs
the section 33 steps 1 to 8 OS recognition **in its own interpreter** (binding
the configured-agent identity so the negative boundary keys off the agent
principal, not root under `sudo`), verifies its peer credential is the
deployment owner, validates a narrow typed request bound to a certification
session, performs **exactly one** bounded operation, writes audit evidence
under the protected root, returns **typed evidence only**, and exits. **No
`HPACWriterCapability` / `HPACStoreAuthority` / handle ever crosses back to the
main interpreter or the launcher.** Section 33 step 9 is replaced by "the
process was `exec`'d from the verified helper, its peer is the deployment
owner, and the OS recognition passed inside it."

Rejected: 6A / 6B (larger standing privileged surface, cross-request authority
state); 6E as the boundary (recognition still runs in the shared interpreter;
object still in-process reachable — retained only as optional in-helper
defense-in-depth); network / cloud authority service (out of scope, would
trigger a MAJOR).

## Preserved

The five-role certification family
(`hpac_challenge_coordinator`, `hpac_assertion_recorder`,
`human_authentication_proof_verifier`, `hpac_gate5_binder`,
`hpac_rhamp_counter_state_verifier`) exactly — mapped to five members of the
closed operation enum with exact internal role dispatch;
`hpac_lifecycle_terminator` stays outside. Human approval is not authentication
is not user presence is not PB permission is not runtime capability is not
execution — all walls preserved; the helper is not a human approver.
`mint_protected_presentation_evidence_writer` stays the sole author of the
presentation evidence record; `hpac_rhamp_counter_state_verifier` stays the
sole counter-state mutation authority. Mechanism-neutral / mobile-only future
path preserved. No second trust root. `FILE LOCATION` is not `TRUSTED ORIGIN`;
`HASH CONSISTENCY` is not `PROVENANCE`; `STRUCTURALLY VALID OBJECT` is not
`TRUSTED CANONICAL STATE`.

## Contract impact

Verdict **B**. The v1.4 section 32 predicate 6 / section 33 step 9 ("calling
module"), section 36 / section 37 (factory in a module returning a capability),
section 33A / section 33B (accessor returning a handle), and the section 42B /
section 42D / section 49B / PAWA-INV-13 / PAWA-INV-14 handle semantics are all
written around an in-process factory returning a Python authority object.
Delivering authority out-of-process and replacing "calling module identity"
with "verified peer process plus OS recognition" is not a permitted MINOR move
(HPAC-PAWA-REQ-153); it restructures the frozen recognition-sequence delivery
model and probably adds a companion helper-protocol contract analogous to
HPAC-PPA-001. Magnitude most likely **MAJOR**; the definitive call belongs to
the contract phase. Default recommendation: a fresh, separately authorized
governed contract-evolution phase.

## Evidence

- Phase-ID CPIPC derivation via `pcae.core.phase_id` (independently re-derived,
  no discrepancy).
- Contract baseline read directly from
  `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v1.4) and
  `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`
  (HPAC-PPA-001 v1.0).
- Failed mechanism reconstructed read-only from
  `src/pcae/core/hpac_protected_admin_writer.py` (byte-unchanged by this
  phase).
- `pcae runtime inspect`: `not_implemented` / `Observed` / `observe` /
  `unavailable` / 0 plugins / 0 capabilities — unchanged.
- `git diff 089817c8 HEAD -- src/pcae scripts pyproject.toml docs/contracts` —
  **empty**. No production, script, dependency, or contract change. No test
  file added or changed (architecture-only phase). No real ceremony, no live
  protected-root mutation, no FIDO2 / YubiKey interaction.
- Full detail, threat-model table, comparison matrix, factory-to-operation
  mapping, protocol model, migration plan, implementation slices, and IV
  strategy are in the canonical report: `docs/PHASE_N16_5_F_5_TB_ARCH.md`.

## Recommended successors (derived, NOT begun)

(1) a fresh governed **contract-evolution phase** freezing the HPAC-PAWA-001
section 32 / section 33 / section 36 to section 38 / section 42 restructure
plus a companion helper-protocol contract; (2) a dedicated **contract IV**;
(3) helper plus protocol implementation; (4) caller integration; (5)
in-process-path removal; (6) packaging / clean-install; (7) an independent
**security IV**; (8) production deployment; (9) a **fresh** final N-16-5
certification on a fresh CPIPC-valid id (never reuse a completed or blocked
certification identity). Each requires its own explicit human authorization.
Do not begin any of them, N-16-6, or N-16-7. REPORTING-UX-1 remains open
(non-blocking).

## Governance

- Tests run: 0 (architecture-only phase; no test changes)
- `pcae check`: passed — `pcae health`: healthy — `pcae status` coherence: passed
- Pushed: pushed (`origin/main` at `392de05d`)
- Phase commits: `71f9e337`, `59c1d82d`, `392de05d`
