# Phase N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL

Canonical Phase ID:
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`

Display alias: N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL
Title: Linux-First Canonical-Store Wiring and One-Shot Privileged Helper
Launcher Implementation

## 0. Governance / CPIPC

Predecessor: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
(alias N16-5-F-5-TB-ADMIN-MUTATION-PACKAGING-DECISION), confirmed COMPLETE via
PROJECT_STATUS.md / `.pcae/phase-completion-metadata.json` (`status:
completed`) / `.pcae/phase-reports/latest.json`, all agreeing, at entry HEAD
`18453885` == `origin/main`, `origin/main..HEAD` = 0, tree clean.

CPIPC independently re-derived via `pcae.core.phase_id` (not trusted from the
authorization prompt): candidate = predecessor + appended `.1` segment.
`is_valid(pred)` True, `is_valid(cand)` True, `normalize(cand) == cand` True,
`same_series` True, `same_branch` True, `compare(pred, cand)` = `less`, unique
against `git log --all` at entry.

## 1. Contract baseline (unchanged, verified byte-identical to `origin/main`)

- `HPAC-PAWA-HELPER-001` v1.0 — sha256 `e7b30daeb1f6967fe985cf7394834e76a81acefb538a0038672aa026a5b58815`
  (`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`)
- `HPAC-PAWA-001` v2.0 — sha256 `b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e`
  (`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`)
- `HPAC-PPA-001` v2.0 — sha256 `27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2`
  (`docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`)

`git diff origin/main -- <the three files above>` is empty. No schema,
dependency, or failure-vocabulary change.

## 2. Foundation seams reconstructed (before editing)

`hpac_pawa_helper_operations.py`'s five handlers (`handle_admin_mutation`,
`handle_certification_write`, `handle_certification_read`,
`handle_ceremony_entry`, `handle_presentation_evidence_write`) all read/wrote
exclusively through the injected `ProtectedStoreFoundation` — a deterministic
in-memory dict, explicitly labeled `NON_REAL`, with no relationship to any
canonical protected store implementation.

## 3. Canonical store inventory and operation/role mapping

| Operation | Real store needed | Read or write | Wired this phase? |
|---|---|---|---|
| `certification_read` (`principal_record`) | `HumanPrincipalRegistryStore.resolve_principal` | read | **yes** |
| `certification_read` (`credential_record`) | `HumanPrincipalRegistryStore.resolve_credential` | read | **yes** |
| `certification_read` (`rhamp_credential_sidecar`) | `HpacRhampCredentialSidecarStore.resolve` | read | **yes** |
| `certification_read` (`rhamp_counter_state`) | `HpacRhampCounterStateStore.resolve` | read | **yes** |
| `certification_read` (`presentation_installation_record`, `helper_registration_record`) | `ProtectedPresentationInstallationStore.resolve_current_generation` | read | **yes** |
| `certification_read` (`presentation_mechanism_descriptor`) | `PresentationMechanismDescriptorStore.resolve` | read | **yes** |
| `certification_read` (`trusted_approval_presentation_record`) | `TrustedApprovalPresentationStore.resolve_structural` | read | **yes** |
| `certification_read` (`pawa_anchor_record`) | none exists | read | **no — explicit `BLOCKED_READ_RECORD_TYPES`, fails closed** |
| `ceremony_entry` (generation check half) | `ProtectedPresentationInstallationStore.resolve_current_generation` | read | **yes** (`verify_current_generation`) |
| `ceremony_entry` (in-process duplicate-use bookkeeping) | none (documented non-durable limitation) | n/a | unchanged, not a real-store gap |
| `admin_mutation` | any canonical store write | write | **no — BLOCKED (§4)** |
| `certification_write` (all 5 roles) | any canonical store write | write | **no — BLOCKED (§4)** |
| `presentation_evidence_write` | any canonical store write | write | **no — BLOCKED (§4)** |

8 of 9 enumerated `certification_read` record types are real-store-wireable;
`pawa_anchor_record` has no canonical store anywhere in the codebase and is
kept in an explicit `BLOCKED_READ_RECORD_TYPES` set (fails closed, never a
silent 404).

Certification-role → store mapping is moot: all five roles
(`hpac_challenge_coordinator`, `hpac_assertion_recorder`,
`human_authentication_proof_verifier`, `hpac_gate5_binder`,
`hpac_rhamp_counter_state_verifier`) write through `certification_write`,
which is blocked (§4) for every role identically — no role gains or is denied
differential access; the blocker is upstream of role dispatch.

## 4. BLOCKING finding (Section 95 STOP — not routed around)

Every real canonical-store *write* — required by `admin_mutation`,
`certification_write`, and `presentation_evidence_write` — needs an
`HPACWriterCapability` minted by
`HPACStoreAuthority._mint_production_writer_capability`, which is gated by
`_PRODUCTION_WRITER_FACTORY_SEAL` (`hpac_foundation.py:124`). Every call site
that presents this seal lives exclusively in `hpac_protected_admin_writer.py`
(verified: `grep -rn "_mint_production_writer_capability\|_PRODUCTION_WRITER_FACTORY_SEAL" src/pcae/`
returns matches only in `hpac_foundation.py` — the seal's definition — and
`hpac_protected_admin_writer.py` — every mint call site). There is no second
factory and no second seal anywhere in the repository.

`HPAC-PAWA-HELPER-REQ-033` (`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md:374`)
explicitly forbids the helper from importing
`pcae.core.hpac_protected_admin_writer`, its `production_writer` /
`certification_writer` / `recognized_certification_read_authority` symbols, or
any agent-reachable module.

Consequently, under the frozen contract trio as it exists today, **the
one-shot helper process has no code path to obtain PRODUCTION-class write
authority against any canonical store.** This is contract-confirmed, not an
implementation oversight — independently re-verified by the primary operator
(not merely reported by the delegated implementation worker), including
direct inspection of the seal, every mint call site, and the exact REQ-033
text.

Per phase-authorization §95/§101 this is a valid early-STOP condition
("real store APIs require exported bearer authority"). The phase is not
routed around this: `RealCanonicalReadAdapter.put_record` and item-assignment
on `presentation_evidence` both fail closed with the identical documented
`internal_fail_closed` reason (an existing failure-vocabulary member, no new
code invented per §69) rather than crashing with a bare `AttributeError` or
silently succeeding against fake in-memory state.

## 5. What was implemented

- `src/pcae/core/hpac_pawa_helper_store_adapter.py` (new, ~230 lines) —
  `RealCanonicalReadAdapter`, duck-type compatible with
  `ProtectedStoreFoundation` (`get_record`, `ceremonies_started`,
  `presentation_evidence`, `put_record`), backing `certification_read` and
  `ceremony_entry`'s real-read half against the canonical stores in §3;
  `resolve_launcher_deployment_metadata` for the launcher's own trusted
  metadata resolution (same resolver `ceremony_entry` uses — one canonical
  source of truth, never two divergent ones).
- `src/pcae/core/hpac_pawa_helper_launcher.py` (new, ~190 lines) — the
  Linux-first one-shot launcher: resolves/verifies the helper executable via
  the pre-existing `hpac_pawa_helper_os.verify_helper_executable` +
  `execute_verified` (same-file-object exec, no pathname reopen), creates a
  private `OneShotChannel`, authenticates the kernel peer credential
  (`SO_PEERCRED` via pre-existing `authenticate_peer`), exchanges exactly one
  bounded request/response frame, reaps the child exactly once, and returns a
  typed `LaunchOutcome` — never an authority object. Fails closed with
  `UnsupportedPlatformProfile` on any non-Linux `sys.platform` before any
  protected operation.
- `src/pcae/core/hpac_pawa_helper_entrypoint.py` (new, ~180 lines) — the
  narrow one-shot helper-process entrypoint: bounded single-frame framing
  (`read_one_frame`/`write_one_frame`, 1 MiB cap), dispatch through the
  existing closed §13 table only, exactly one request handled then exit.
  `main()` still constructs `ProtectedStoreFoundation()` (see §7 — a
  deliberate, acknowledged deferral, not an oversight).
- `src/pcae/core/hpac_pawa_helper_operations.py` (+9 lines) — a
  backward-compatible `ceremony_entry` hook: `getattr(context.store,
  "verify_current_generation", None)` is called when present (real adapter)
  and skipped when absent (foundation store) — no behavior change for
  existing foundation-only callers/tests.
- 4 existing AST "authorized production consumer" guard test files extended
  with exact-filename tuples for the new adapter's imports
  (`hpac_pawa_helper_store_adapter.py` → `hpac_foundation`,
  `human_principal_registry`, `approval_presentation`) — mechanical, no
  wildcard, matches the established per-phase pattern; independently reviewed
  diff-by-diff by the primary operator.
- `tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py` (new, ~680
  lines, 28 tests — 2 added by the primary operator for the §4 fail-closed
  write-blocker behavior after independent review found the original
  `RealCanonicalReadAdapter.presentation_evidence` was a plain dict that would
  have silently "succeeded" on write, masking the exact blocker documented
  for that operation).

## 6. Adversarial matrix coverage (phase-authorization §76)

Covered with real/adversarial fixtures: unknown record type rejection, blocked
read record type fail-closed, put_record/presentation_evidence-write fail
closed (added by primary operator), helper substitution after verification,
symlink helper, digest mismatch, wrong mode, multiple hardlinks, stale/wrong
generation for `ceremony_entry`, forged peer uid/gid/pid vs. kernel
`SO_PEERCRED` truth, malformed/truncated/zero-length/oversized request and
response framing, second request on same connection, no-authority-export on a
real-store `certification_read` response, durable-replay ledger reuse.

Skipped (3, honestly reported, not faked): genuine-separate-process positive
integration, cross-process replay after a new helper process, and the full
helper-executable substitution-attack subprocess matrix — all three require
actually `exec`-ing a subprocess launcher end-to-end on Linux; this session
ran on **macOS (darwin)**, and per phase-authorization §60 this is reported
honestly as not performed rather than fabricated. Concurrent-duplicate,
response-loss, and crash-indeterminate real-subprocess scenarios were
likewise not executed for the same reason (they build on the same
subprocess harness).

Transitive Python import/provenance analysis (§32/§33/§62/§77-§79): not
performed this phase — moot given the §4 blocker already halts all three
write operations upstream of any store-authority question, and the two
wired-read operations exercise only pre-existing, already-verified-elsewhere
import paths (`hpac_foundation`, `human_principal_registry`,
`hpac_rhamp_credential_sidecar`, `hpac_rhamp_counter_state`,
`protected_presentation_installation`, `approval_presentation` — all already
production-consumed by `hpac_certification_coordinator.py` per the guard
tests' own pre-existing authorized set). Recommended successor should still
perform this analysis explicitly once/if a real write pathway is designed.

## 7. Acknowledged limitation: `main()` does not select the real adapter

`hpac_pawa_helper_entrypoint.main()` — the actual process body a real Linux
launcher would `exec` — still constructs `ProtectedStoreFoundation()`
unconditionally. `RealCanonicalReadAdapter` is verified as a standalone
component (constructed directly against disposable `HPACStoreAuthority.fixture()`
roots in the new test file) but is **not yet main()'s default store**.

This is deliberate, not an oversight the primary operator missed: `.production()`
resolves a **fixed, non-overridable** live path (`hpac_foundation.py:174`,
"no override input is accepted"), by design, specifically to prevent a root
override. Naively wiring `main()` to `HPACStoreAuthority.production()` would
mean any real subprocess execution of `main()` — including in a test —
reads/writes against the actual live protected root, which phase-authorization
§45/§58 forbid. Resolving this safely (a disposable-root test seam for the
real one-shot entrypoint, distinct from the fixed production path) is real
remaining work, not scope this phase silently absorbed or hid. The 3 blocked
write operations would fail closed either way once wired (§4), so this
deferral affects only the 2 already-blocked-elsewhere honesty question, not
correctness of what is claimed as done: **the real store adapter is proven
correct as a component; it is not yet the live entrypoint's default.**

## 8. Regression and Fast Green attribution

Broad regression slice (`tests/ -k "helper or pawa or hpac or rhamp or
presentation"`, ~1850 tests deselected down from the full suite): baseline
(pre-change, via `git stash -u`) and candidate produce an **identical set of
58 failing node IDs** (`diff` exit 0) — 0 attributable regressions,
independently re-verified by the primary operator (not merely trusted from
the delegated worker's report).

Governed `pcae phase fast-green-attribution --phase-id <CPIPC>
--pushed-status not_pushed` (full suite, two sequential runs):

- Baseline: `18453885735657f549804c71c3257ec0a3760f11` (method:
  `parent_of_oldest_phase_attributed_commit`)
- Candidate: `f922c8b18e0fc75bccc79bec51692660aa58536b`
- Raw failures: 363 (354 failed / 9 errors)
- Attributable: **0**
- Pre-existing: 362
- Environment: 0
- Expected phase artifacts: 1 (`test_head_equals_origin_main`, correctly
  predicted by `pushed_status=not_pushed` pending this phase's own push)
- Verdict: **PASS**
- Evidence artifact:
  `.pcae/fast-green-attribution/00dd8566502c030691d62a2ac401b69738b416396ddcd52d1a2c0ccd2f090e33.json`

(An earlier `--pushed-status clean` run mis-derived `pushed_status` for a
repo state that actually had unpushed commits — corrected before use. A
second, accidentally-concurrent duplicate run produced one spurious
attributable failure from test interference between two simultaneous full
suite runs; both invalid artifacts were deleted, never embedded in any
report, and are not part of this phase's evidence.)

## 9. No authority export / no generic broker

`response_leaks_authority` (pre-existing, unchanged) is still checked on every
dispatch response, plus a defence-in-depth re-check in
`handle_one_request`. The launcher never holds/receives/forwards an
`HPACWriterCapability`/`HPACStoreAuthority` — it only ever sees the
`HelperResponse` bytes the child already produced (verified by direct
reading of `hpac_pawa_helper_launcher.py`). No sixth operation, no dynamic
dispatch, no generic store key/path injection surface was introduced.

## 10. Scope discipline (verified, not merely asserted)

- Production file diff vs. `origin/main`: exactly `hpac_pawa_helper_operations.py`
  (+9), 3 new modules (~600 lines total) — no other production file touched.
- `git diff origin/main --stat -- pyproject.toml` and `-- docs/schemas/`:
  both empty.
- Contract trio: byte-identical (§1).
- No caller migration, no typed client, no packaging change, no live
  install/register, no Dell/host mutation, no real FIDO2/ceremony/certification.
- macOS: launcher fails closed via `UnsupportedPlatformProfile` before any
  protected operation (untouched, unimplemented, as required).

## 11. Disposition

**N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL: COMPLETE — BLOCKED.**
(2 of 5 helper operations — `certification_read`, `ceremony_entry` —
genuinely wired to real canonical stores as a verified standalone component;
3 of 5 — `admin_mutation`, `certification_write`, `presentation_evidence_write`
— contract-confirmed BLOCKED by HPAC-PAWA-HELPER-REQ-033's writer-seal
exclusivity, not routed around. Linux one-shot launcher + entrypoint
implemented and unit/adversarial-tested; genuine-subprocess/cross-process
scenarios not executed this session — macOS host, honestly reported.)

Canonical-store helper wiring: **PARTIAL (2/5), REMAINDER CONTRACT-BLOCKED**.
Linux one-shot launcher: **IMPLEMENTED** (subprocess-level verification
pending Linux IV). Real protected helper process boundary: **IMPLEMENTED /
PENDING FRESH INDEPENDENT VERIFICATION**. Canonical production store
implementations: consumed through the new adapter using disposable test
state only. Live protected host: **UNCHANGED**. Caller migration: **NOT
BEGUN**. Typed routine admin client: **NOT IMPLEMENTED**. Packaging:
**UNCHANGED**. Helper installation/registration: **NOT PERFORMED LIVE**.
macOS same-file-object execution: **FAIL-CLOSED / NOT IMPLEMENTED**. Real
authentication/presentation: **NOT PERFORMED**.

F-5-B2: **BLOCKED PENDING (a) the REQ-033 writer-authority contract-evolution
question and (b) a fresh Linux IV of what this phase did implement**. F-5:
**CERTIFICATION BLOCKED**. N-16-5: **NOT CLOSED**. N-16-6 / N-16-7: **OPEN /
UNTOUCHED** (N-16-7 strictly last).

**Recommended next (derived, NOT begun):** two candidate successors, not yet
adjudicated between them:

1. **N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IV** — fresh independent
   verification of what this phase actually implemented (the 2 wired
   read-operations, the launcher/entrypoint, same-file-object execution,
   peer credentials, framing, replay) on a genuine Linux host, since this
   session could not perform genuine-subprocess Linux verification itself.
2. A narrow **helper writer-authority contract-evolution phase** — the only
   way `admin_mutation`/`certification_write`/`presentation_evidence_write`
   can ever be real-store-wired is a second, helper-scoped mint pathway or an
   explicit `HPAC-PAWA-HELPER-001` amendment; this is a normative-contract
   decision, not an implementation task, and needs fresh explicit human
   authorization before any such contract change.

Per the absolute stop boundary: do not begin either successor, implement the
typed client, migrate any caller, modify packaging, implement macOS
same-file-object support, install/register the helper, perform real
certification, N-16-6, or N-16-7 without fresh explicit human authorization
for each.
