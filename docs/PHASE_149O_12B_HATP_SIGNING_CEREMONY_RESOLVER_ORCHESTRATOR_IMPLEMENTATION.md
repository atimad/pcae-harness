# Phase 149O.12B — HATP Signing Ceremony Resolver + Orchestrator Implementation

Phase type: **BOUNDED PRODUCTION IMPLEMENTATION**. Implements Wave C +
Wave D of the Phase 149O.11 implementation plan: the AG3/AG5
proof-context resolver and the signing-ceremony orchestrator
(`src/pcae/core/hatp_signing_ceremony.py`). Not authorized, and not
implemented, this phase: CLI (`commands/hatp.py`, `cli.py` registration
— 149O.12C's exclusive scope), AG3/AG5 consumption wiring, rollback
dispatch changes, Permission Broker changes, Class-B provisioning, or
HATP production activation.

## 1. Baseline

- Latest completed phase entering this phase: **149O.12A — Signed
  Evidence Model + Evidence Store Implementation.** Status: completed,
  report complete, pushed. Baseline commit: `53bf12ca`.
- Contract entering this phase: **HSCE-001 v1.1 — VERIFIED WITH
  NON-BLOCKING FINDINGS — CONFORMS.** `149O.10-F-1/F-2/F-3`,
  `149O.10-Obs-2`, `149O.10.2-Obs-3`: all resolved/closed per 149O.11's
  design selections and 149O.12A's implementation, unaffected by this
  phase.
- `B-149O-1..4`: INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
  BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED. Unaffected by this
  phase.
- HATP production entering and leaving this phase: **NOT READY**.
  Runtime entering and leaving this phase: **Observed / observe /
  unavailable**. This phase adds no CLI, no AG3/AG5 wiring, and no
  hardware touch to any reachable production path; `sign_rollback_
  evidence`/`production_sign_rollback_evidence` are inert — nothing in
  `src/pcae/` calls them yet.

## 2. Contract State

| Contract | Version | Status | Byte-changed by this phase? |
|---|---|---|---|
| HSCE-001 | 1.1 | VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS | No |
| HATP-001 | 1.0 | FROZEN, unamended | No |
| RAE-001 | 1.0 | FROZEN, unamended | No |

Independently reconfirmed via `git diff --stat 53bf12ca -- <contract-path>`
for all three contract files: empty diff in every case (see
`tests/test_phase_149o_12b_hatp_signing_ceremony_implementation.py::
TestContractByteIdentity`).

## 3. 149O.12B Requirement Subset (from the 149O.11 plan's 79-requirement table)

Per the 149O.11 plan's Production File Allowlist (§16):

| Module | Requirements owned |
|---|---|
| `hatp_signing_ceremony.py` | HSCE-REQ-013, 016, 018–030, 049–051, 067–071 |

**Coverage result:** every requirement in this subset has both code and
test coverage in `tests/test_hatp_signing_ceremony.py` (field-level/
attack-level) and `tests/test_phase_149o_12b_hatp_signing_ceremony_
implementation.py` (cross-cutting scope/boundary checks). No requirement
in this subset was left unimplemented or untested.

## 4. Production Diff

**Production file added (exactly one, matching the 149O.11 plan's
allowlist for this phase):**

- `src/pcae/core/hatp_signing_ceremony.py`

**Production files modified:** none. 149O.12A's two modules
(`hatp_signed_evidence.py`, `hatp_evidence_store.py`) remain
byte-unchanged — consumed (imported), never edited. No existing HATP
module (`human_approval_trusted_provenance.py`, `hatp_providers.py`,
`hatp_fido2_provider.py`, `hatp_bootstrap.py`, `hatp_hardware_
credentials.py`, `hatp_ag_authority.py`, `repository_identity.py`,
`rollback_approval_evidence.py`), `agent.py`, `commands/agent.py`,
Permission Broker module, or `cli.py` was touched.

**Unrelated hunks:** 0 — independently confirmed by
`TestProductionFileAllowlist` in the phase-specific suite (diffs the
current tree against the 149O.12A baseline commit `53bf12ca` via `git
diff --name-only` plus `git ls-files --others --exclude-standard`,
unioned, and asserted to be exactly the one file above).

**Test/config files touched (outside the production allowlist, as
expected for an implementation phase):**

- `tests/test_hatp_signing_ceremony.py` (new)
- `tests/test_phase_149o_12b_hatp_signing_ceremony_implementation.py` (new)
- `tests/conftest.py` (modified — Fast Green module registration only:
  `test_hatp_signing_ceremony` added)
- `tests/test_phase_149o_1e_hatp_repository_identity_trust_store_
  foundation.py` (modified — allowed-file-widening precedent, adds this
  phase's new module to the cumulative `src/pcae/` diff-scope allowlist,
  alongside the already-widened 149O.6/149O.12A entries)
- `tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py`
  (modified — same allowed-file-widening precedent, extends the
  existing 149O.12A widening to also name this phase's new module)
- `tests/test_phase_149o_12a_signed_evidence_model_store_
  implementation.py` (modified — its own production-diff-scope test
  updated from a strict two-file equality to an explicit,
  separately-documented `_LATER_PHASE_APPROVED_FILES` allowlist entry
  for this phase's module, and its now-permanently-obsolete
  `test_no_signing_ceremony_module_created` assertion removed, since
  that module's non-existence was correctly asserted only up to 149O.12A's
  own completion and is not this phase's finding to reopen)

**Hunk classification** (per the 149O.11 plan's §16 taxonomy):
`PROOF_CONTEXT_RESOLUTION`, `SIGNING_ORCHESTRATION`, `TOCTOU_RECHECK`,
`ERROR_MAPPING` (all in `hatp_signing_ceremony.py`). **`UNRELATED` = 0.**

## 5. Proof-Context Resolver Design (Wave C)

`resolve_signing_context(root, *, site, job_id=None, per_id=None) ->
HATPRollbackSigningContext` derives every canonical signing-context field
from live state, for exactly one of AG3 (`job_id`) or AG5 (`per_id`):

- **AG3** (HSCE-REQ-013): `original_commit_sha` is read from the live
  job record via `agent.py::build_rollback_review` — the identical live
  record `execute_rollback` already reads for its own preconditions
  (never a second, independent job-file reader). Missing job, malformed
  job, or an unresolvable/malformed `original_commit_sha` all fail
  `operation_not_found` (attack 21), before any RAE Binding lookup and
  before any hardware provider is touched.
- **AG5** (HSCE-REQ-016): `ecp_id` is read directly from the live
  `PromotionExecutionRecord` via `agent.py::lookup_promotion_execution_
  record` — the identical live record `build_rollback_execution` already
  reads for its own preconditions. Missing PER, or a missing/
  unresolvable `ecp_id`, both fail `operation_not_found` (attack 20).
- **Binding lookup** (HSCE-REQ-020/021): scans `RollbackApprovalEvidence
  Store.list_bindings_with_keys()`, filters structurally on
  `rollback_site` + operation reference, excludes revoked Bindings
  (`store.is_revoked`), then applies supersession-aware selection among
  remaining candidates matching this one already-identified operation:
  the strictly-latest `created_at` wins; a tie, or a candidate with an
  unparseable `created_at`, is ambiguous and fails closed
  (`binding_unavailable`) — never an implicit "pick the newest across
  distinct operations" rule, and never a human-disambiguation prompt.
  Zero matching candidates also fails `binding_unavailable`, before any
  hardware provider is touched.
- **Decision resolution**: `decision_record_id`/`decision_record_digest`
  are read directly from the matched Binding's own `governance_record_
  reference` (no second CHGR record read/re-serialization — reuses the
  Binding's own already-resolved reference); an empty/missing reference
  fails `decision_unavailable`.
- **Repository identity**: `repository_identity.read_repository_
  identity(root)`; missing or malformed fails `repository_identity_
  unavailable`.

`HATPRollbackSigningContext` is a frozen dataclass holding exactly the
HSCE-required stable fields (`rollback_site`, `operation_reference`,
`binding_id`, `binding_digest`, `decision_record_id`, `decision_record_
digest`, `repository_id`) — no proof-shape duplication, no authority
field. Its `frozen=True` dataclass equality *is* the entire TOCTOU
comparison (§7 below): no separate field-by-field comparator exists or
is maintained.

## 6. Signing-Ceremony Orchestration Design (Wave D)

### 6.1 API shape

```python
def resolve_signing_context(
    root: HarnessPath, *, site: RollbackSite,
    job_id: Optional[str] = None, per_id: Optional[str] = None,
) -> HATPRollbackSigningContext: ...

def sign_rollback_evidence(
    root: HarnessPath,
    *,
    site: RollbackSite,
    job_id: Optional[str] = None,
    per_id: Optional[str] = None,
    clock: Callable[[], datetime] = _default_clock,
    provider_factory: Callable[[], HATPHardwareSigner] = _default_provider_factory,
    trust_store_factory: Callable[[], HATPTrustStore] = _default_trust_store_factory,
    confirm: Callable[[HATPSigningPreview], bool] = _default_confirm,
) -> HATPSigningResult: ...

def production_sign_rollback_evidence(
    root: HarnessPath, *, site: RollbackSite,
    job_id: Optional[str] = None, per_id: Optional[str] = None,
) -> HATPSigningResult:
    return sign_rollback_evidence(root, site=site, job_id=job_id, per_id=per_id)
```

**F-2 non-regression** (mirrors `hatp_ag_authority.py`'s own
zero-override production-adapter discipline): `production_sign_rollback_
evidence` carries no `provider`/`trust_store`/`clock`/`confirm`
parameter at all — its signature is exactly `{root, site, job_id,
per_id}` — and its body passes no override keyword to `sign_rollback_
evidence`, always relying on that function's own production defaults.
There is structurally nothing here for a production caller to substitute
a test provider or an arbitrary trust store with. Confirmed by
`TestProductionWrapperZeroOverride` (signature inspection + static
source-text check that no `*_factory=`/`clock=`/`confirm=` override
appears in the wrapper's body).

`sign_rollback_evidence` itself is the internal, test-injectable core:
only `tests/test_hatp_signing_ceremony.py` supplies deterministic fakes
directly to it. Its own *default* values (`_default_provider_factory`,
`_default_trust_store_factory`) resolve exclusively through the
production factories (`create_production_hardware_provider(HATP_
HARDWARE_PROVIDER_V1)`, `HATPTrustStore.production()`) — no
`TestHATPProofVerifierProvider`/test-fixture class is imported by, or
reachable from, either default.

### 6.2 Typed results and errors

- `HATPSigningResult(evidence_id, path, idempotent)` — the sole success
  type; no `approved`/`permission`/`executed` field (mirrors
  HSCE-REQ-065/066's success-output discipline at the core-orchestrator
  layer, even though no CLI exists yet).
- `HATPSigningPreview(rollback_site, operation_reference, repository_id,
  decision_record_id, decision_record_digest, binding_id, binding_digest,
  principal_id, signer_key_id, provider_profile)` — the blind-touch-
  defense preview (HSCE-REQ-071); no authority-bearing field.
- The closed `HATPSigningCeremonyError` hierarchy (10 subclasses, each
  with a class-level `error_type` string drawn exclusively from
  HSCE-REQ-047's vocabulary): `RepositoryIdentityUnavailableError`,
  `OperationNotFoundError`, `DecisionUnavailableError`, `Binding
  UnavailableError`, `NoAuthorizedSignerError`, `ProviderUnavailable
  Error`, `HardwareDeviceFaultError`, `HumanSigningCancelledError`,
  `ProviderSignatureFailureError`, `EvidenceSerializationFailureError`.
  `hatp_evidence_store.py`'s own `EvidenceConflictError`/`Evidence
  PersistenceFailureError` propagate unmodified from `store.publish()` —
  never re-wrapped or reinterpreted, per the 149O.11 plan's explicit "map
  its outcomes directly" instruction. No `error_type` outside HSCE-001's
  closed 12-member vocabulary is introduced anywhere in this module
  (confirmed by `TestClosedErrorVocabulary`).

### 6.3 Ordering (preview-before-touch, TOCTOU-before-publish)

1. Resolve context A (`resolve_signing_context`) — no hardware touch.
2. Resolve provider/signer identity (`provider.credential_identity()`
   cross-checked against `trust_store.lookup_signer(...)`, HSCE-REQ-024)
   — a credential-exchange identification call, not yet the physical
   presence touch — and render the preview.
3. Require explicit human confirmation of the preview
   (`human_signing_cancelled` if declined) — still no hardware touch.
4. Generate `issued_at` (internal clock, called exactly once,
   immediately pre-proof-construction), construct the proof, and invoke
   `provider.request_signature(...)` exactly once — the sole physical
   hardware touch this function ever performs, and the only call site of
   `request_signature` in this module (confirmed by static source-text
   count in `TestPreviewBeforeTouchAndToctouOrdering`).
5. Re-resolve context B (`resolve_signing_context`, called a second
   time) and compare against context A via dataclass equality on every
   HSCE-required stable field. Any mismatch discards the signed
   assertion and fails `evidence_serialization_failure` — no publish, no
   second provider call, no automatic re-sign; a fresh ceremony
   invocation is required.
6. Build the envelope (`hatp_signed_evidence.build_hatp_signed_evidence_
   envelope`, 149O.12A) from the untouched original proof and publish it
   (`hatp_evidence_store.HATPEvidenceStore.publish`, 149O.12A).

Dynamic evidence: `test_preview_shown_before_provider_touch_and_
provider_called_exactly_once` (call-order spy: `["resolve",
"preview_confirm", "provider_touch", "resolve"]`, exactly one
`request_signature` call on both the success path and every TOCTOU-
failure path: `test_toctou_mismatch_on_decision/_decision_digest/
_binding/_binding_digest/_operation/_repository`, plus a real
(non-monkeypatched) integration test
`test_toctou_real_supersession_between_preview_and_touch` that mutates
RAE state from inside the `confirm()` callback — the exact moment
between preview and touch attack 18 targets). Static evidence:
`TestPreviewBeforeTouchAndToctouOrdering` in the phase-specific suite
(source-text ordering of `confirm(preview)` before `provider.request_
signature(`, and of `provider.request_signature(` before `context_b =
resolve_signing_context(`, before `build_hatp_signed_evidence_
envelope(`, before `store.publish(`).

### 6.4 Timestamp generation

`issued_at` is produced by `_issued_at_string(clock())`: the internal
clock (`_default_clock`, production default `datetime.now(timezone.
utc)`; test seam `clock:` parameter) is truncated to whole-millisecond
precision (`microsecond // 1000 * 1000`) and rendered via `datetime.
isoformat()` — a valid input to `HumanApprovalProvenanceProof`'s own
`issued_at` field. The actual canonical rendering (the exact
`%Y-%m-%dT%H:%M:%S.%f`-sliced-to-milliseconds-plus-`Z` form) happens
inside `HumanApprovalProvenanceProof.__post_init__`'s existing `_require_
issued_at`/`_canonical_timestamp_string` machinery
(`human_approval_trusted_provenance.py`) — reused, not reimplemented.
Python 3.9-compatible: uses only `datetime.replace`/`isoformat`, no
`fromisoformat` lexical-extension dependence. Whole-millisecond edge
cases (`0`, `1`, `1000`, `999000`, `999999`, `500499`, `500999`
microseconds; naive-datetime UTC treatment) are covered by
`test_issued_at_string_truncates_to_whole_milliseconds` (parametrized)
and `test_issued_at_string_naive_datetime_is_treated_as_utc`.

### 6.5 Provider/signer resolution and failure mapping

`provider.credential_identity()` resolves `signer_key_id`; `trust_store.
lookup_signer(signer_key_id)` cross-checks it against the protected
trust store's authorized-approver mapping. A credential absent from the
registry, or present but not `status == "active"`, fails `no_authorized_
signer` before any signature request (HSCE-REQ-024). `provider_factory()`
raising `HATPProviderUnavailableError` (device absent at resolution
time) and `provider.request_signature(...)` raising the same exception
at call time both map to `ProviderUnavailableError`;
`HATPProviderCancelledError` maps to `HumanSigningCancelledError`;
`HATPProviderDeviceError` maps to `HardwareDeviceFaultError`; any other
provider exception maps to `ProviderSignatureFailureError` (fail-closed
umbrella, HSCE-REQ-030's cancellation/device-fault distinction
preserved).

## 7. Tests

- **`tests/test_hatp_signing_ceremony.py`** — 44 tests. Real filesystem
  throughout (job/PER records, RAE Bindings via the real `create_
  rollback_approval_decision`/`create_rollback_approval_binding`
  pipeline, real repository identity, real `.pcae/hatp-evidence/`
  envelopes) — only the hardware provider and trust store are
  deterministic in-memory fakes; this module's own production defaults
  are never invoked by this suite. Covers: AG3/AG5 resolver success/
  failure (including attacks 20/21), missing/ambiguous/superseded/
  revoked Binding resolution (attack 19), repository-identity failure,
  no-authorized-signer (missing + revoked signer), provider-unavailable
  (identity-time + factory-time + touch-time), preview-before-touch
  ordering with exactly-one-provider-call on both the success and
  TOCTOU-failure paths, cancellation (attack 16) including declined
  preview confirmation, hardware device fault distinct from cancellation,
  generic provider-exception mapping, TOCTOU mismatch on each of
  Decision/Decision-digest/Binding/Binding-digest/operation/repository
  (attack 18, both monkeypatched-deterministic and a real RAE-mutation
  integration test), envelope built through the 149O.12A factory only
  (spy-confirmed), store publish outcome mapping (idempotent/conflict/
  persistence-failure, propagated unmodified), whole-millisecond
  timestamp edge cases, and module import with no hardware/`fido2`
  present (subprocess-isolated).
- **`tests/test_phase_149o_12b_hatp_signing_ceremony_implementation.py`**
  — 42 tests. Production-diff-scope allowlist (git-derived, robust
  across untracked/staged/committed states, pinned to the 149O.12A
  baseline commit `53bf12ca`), no CLI module/registration anywhere, no
  Permission Broker import, no `verify_hatp_proof`/`HATPVerification
  Status` usage, no legacy approval-state mutation or rollback-dispatch
  call, no `approval_present` derivation, contract byte-identity
  (HSCE-001/HATP-001/RAE-001), 149O.12A's two modules byte-unchanged,
  no-authority-bearing-field confirmation on all three new dataclasses,
  production-wrapper zero-override structural checks (signature
  inspection + static source-text check + confirmation that the core
  function's own defaults resolve production dependencies only, never a
  test-fixture provider class), static preview-before-touch/TOCTOU-
  before-publish ordering checks, closed-error-vocabulary membership
  check, lazy-import/optional-hardware-dependency discipline, and a
  coarse presence check for the required attack-subset (16, 17, 18, 19,
  20, 21) in the core test file.

**Total new tests this phase: 86. All pass.**

Three earlier-phase "allowed-file-widening" tests were updated to
account for this phase's new module — an established, explicitly
documented repository convention (retained 149O.5-F-3 lesson,
independently applied by 149O.12A's own report to the 149O.1G-era test):
`tests/test_phase_149o_1e_hatp_repository_identity_trust_store_
foundation.py::test_only_expected_production_files_changed`,
`tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py::
test_only_expected_production_files_changed`, and
`tests/test_phase_149o_12a_signed_evidence_model_store_implementation.py::
TestProductionFileAllowlist` (converted from strict two-file equality to
an explicit, separately-named `_LATER_PHASE_APPROVED_FILES` widening,
plus removal of the now-permanently-obsolete `test_no_signing_ceremony_
module_created` negative assertion, whose invariant 149O.12A itself
scoped only through its own completion, not through all future phases).
No other pre-existing test file was modified.

## 8. Regression Suites

| Suite | Result |
|---|---|
| `tests/test_hatp_signed_evidence.py` | 84 passed (unchanged) |
| `tests/test_hatp_evidence_store.py` | 48 passed (unchanged) |
| `tests/test_phase_149o_12a_signed_evidence_model_store_implementation.py` | 44 passed (3 assertions updated per §4/§7 above; same pass count) |
| `tests/test_hatp_signing_ceremony.py` (new) | 44 passed |
| `tests/test_phase_149o_12b_hatp_signing_ceremony_implementation.py` (new) | 42 passed |
| `-k "hatp or rollback_approval"` bounded sweep (excluding the pre-existing `fido2`-import collection error in `test_phase_149o_7_...py`, unrelated to this phase, unchanged from baseline) | 1925 passed / 10 failed / 3 skipped — **identical 10 pre-existing failures** to the `git stash -u` baseline (1839 passed / 10 failed / 3 skipped): `test_phase_149o_1f_2_...::test_no_production_caller_imports_hatp_bootstrap_outside_itself`, `test_phase_149o_1f_2_...::test_phase_149o_1f_2_did_not_modify_hatp_contract`, `test_phase_149o_1f_...::test_rae_permission_broker_agent_still_byte_unchanged_since_freeze`, `test_phase_149o_1h_4_...::test_no_forbidden_imports_in_production_module`, `test_phase_149o_1h_...::test_hatp_contract_and_wave_1_2_files_byte_unchanged_since_149o_1g`, `test_phase_149o_4_hatp_rae_integration.py::test_rae_stale_plus_valid_hatp_still_false`, and the four `test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py` forgery findings — all pre-existing, none touched by, or related to, this phase's new module; 86 additional passes are this phase's own new tests |
| Fast Green (`pytest -m fast_green -n auto`) | see §9 below |

## 9. Fast Green

`tests/conftest.py::FAST_GREEN_MODULES` gains one entry this phase:
`test_hatp_signing_ceremony` (deterministic, real-filesystem-only I/O,
no hardware, no network, injectable clock — mirrors 149O.12A's own
Fast Green registration rationale for its two new modules).

Independently reconfirmed via `git stash -u` A/B comparison in this
environment (`pytest -m fast_green -n auto`):

| Run | Result |
|---|---|
| `git stash -u` baseline (this phase's changes removed) | 4722 passed, 2 skipped, 0 failed, 1 pre-existing collection error |
| This phase's working tree | 4766 passed, 2 skipped, 0 failed, 1 pre-existing collection error |

Delta: **+44 passed**, exactly this phase's own newly-registered
`test_hatp_signing_ceremony` Fast Green tests; skip/fail counts
unchanged. The one collection error in both runs
(`tests/test_phase_149o_7_hatp_class_b_activation_independent_
verification.py`, `ModuleNotFoundError: No module named 'fido2'`) is a
pre-existing environment condition (this test environment has no
`fido2` extra installed) — independently confirmed present, byte-
identical, in the `git stash -u` baseline before this phase's changes
existed; not introduced or affected by this phase's module (which
imports no `fido2` symbol, directly or transitively, at module load
time — confirmed by `TestLazyImportDiscipline` and `test_module_
importable_without_hardware_or_fido2`). The 149O.12A-report-cited
figure of "4784 passed, 1 skipped, 0 failed" reflects a different prior
environment session in which the `fido2` extra was installed; this
report cites the reproducible, environment-verified A/B comparison
above rather than re-asserting that historical absolute figure, per
this project's own "cite what was independently reproduced" discipline
(149O.10.2-Obs-4's own precedent).

## 10. Findings

- No blocking finding raised by this phase. No genuinely missing
  low-level API was discovered in 149O.12A's two modules, RAE-001's
  production surface, or HATP-001's production surface — every field
  this phase's resolver needed was obtainable through an existing public
  read API (`agent.py::build_rollback_review`/`lookup_promotion_
  execution_record`, `RollbackApprovalEvidenceStore.list_bindings_with_
  keys`/`is_revoked`, `repository_identity.read_repository_identity`,
  `hatp_bootstrap.HATPTrustStore.lookup_signer`, `hatp_providers.
  create_production_hardware_provider`/`HATPHardwareSigner.credential_
  identity`/`request_signature`).
- Non-blocking observation: this phase's Binding supersession-selection
  algorithm (§5 above) is independently re-derived in `hatp_signing_
  ceremony.py` rather than importing `rollback_approval_evidence.py`'s
  own private `_is_superseded`/`_binding_effective_state` helpers (which
  that module's own docstrings mark test-file-only/internal). This
  mirrors an existing, confirmed-legitimate precedent already in
  production: `rollback_approval_evidence.py::_hatp_expected_operation_
  for` independently re-derives the identical RAE-Binding-to-HATP-
  operation-reference field mapping this module also needed, rather than
  this module importing that private helper. No RAE digest/serialization
  algorithm is reimplemented anywhere — only a field-mapping/selection
  pattern already demonstrated as production-legitimate.

## 11. Scope Confirmations

Only the one planned production module
(`src/pcae/core/hatp_signing_ceremony.py`) was added; no other
`src/pcae/**` file was changed. HSCE-001 v1.1, HATP-001 v1.0, and
RAE-001 v1.0 all remained byte-unchanged. 149O.12A's two modules
(`hatp_signed_evidence.py`, `hatp_evidence_store.py`) remained
byte-unchanged. No CLI command was implemented (`cli.py` and
`commands/` untouched; no `commands/hatp.py` created). No hardware
signing occurred outside this phase's own deterministic tests (neither
`sign_rollback_evidence` nor `production_sign_rollback_evidence` is
called from anywhere in `src/pcae/` — both remain inert). No AG3/AG5
consumption was added (`hatp_ag_authority.py` untouched and does not
reference this phase's new module). No rollback dispatch behavior
changed (`agent.py`, `commands/agent.py` untouched — read-only imports
of two existing public functions only). No Permission Broker behavior
changed (the new module imports no `permission_broker*` module). No
Class-B provisioning occurred. No HATP production activation occurred.
No legacy `rollback_approval_state`/PER-status mutation occurs anywhere
in this module — it is read-only against job/PER/Binding state. Signing
remains distinct from verification, approval, permission, capability,
and execution (`verify_hatp_proof` and `HATPVerificationStatus` are
never imported or referenced). `B-149O-1..4` remain independently
verified at the HATP-gated authority boundary with system execution
closure deferred. HATP production remains **NOT READY**. Runtime
remains **Observed / observe / unavailable**.

## 12. Implementation Verdict

```
HATP SIGNING CEREMONY RESOLVER + ORCHESTRATOR: IMPLEMENTED
— READY FOR 149O.12C
```

This is not a claim of full HSCE-001 implementation — only Wave C
(proof-context resolution) and Wave D (signing-ceremony orchestration)
of the 149O.11 plan's six-wave decomposition. Wave E (CLI command +
output/error mapping) and Wave F (integrated deterministic attack-matrix
suite) remain unimplemented, scheduled for 149O.12C.

## 13. Recommended Next Phase

**149O.12C — HATP Signing CLI Integration** (Wave E + Wave F of the
149O.11 plan): `commands/hatp.py` CLI handler, `cli.py` `pcae hatp sign
rollback --site {ag3|ag5} [locators] [--json]` registration, exit-code/
error-vocabulary mapping (`commands/hatp.py`'s own centralized
`error_type -> exit_code` table per HSCE-REQ-046/047), forbidden-flag
inventory tests, optional-dependency (`fido2`-absent) `--help` behavior,
zero-override production-path assertion for the CLI handler itself (it
must call only `production_sign_rollback_evidence`, never `sign_rollback_
evidence` with overrides), and the integrated, end-to-end 21-item
mandatory attack-matrix suite (`test_hatp_cli.py`, `test_phase_149o_12_
hsce_attack_matrix.py` or equivalent) exercising the fully assembled
implementation. A separate, dedicated **149O.13 — Independent
Verification** phase remains required after 149O.12C completes, before
HATP production readiness is reconsidered (149O.11 plan §18).
