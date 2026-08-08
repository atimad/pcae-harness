# Phase 149O.12C — HATP Signing CLI Integration + Full HSCE Attack-Matrix Implementation

## Identity

- **Phase ID:** 149O.12C
- **Status:** COMPLETE
- **Report completeness:** complete
- **Type:** BOUNDED PRODUCTION IMPLEMENTATION (Wave E + Wave F of the
  149O.11 implementation plan)
- **Commit:** `478e49c9` — "Phase 149O.12C: HATP Signing CLI Integration
  + Full HSCE Attack-Matrix Implementation"
- **Files changed (production):** `src/pcae/commands/hatp.py` (NEW),
  `src/pcae/cli.py` (MODIFY, registration only)
- **Files changed (tests, 7):** `tests/test_hatp_cli.py` (NEW),
  `tests/test_phase_149o_12c_hsce_attack_matrix.py` (NEW),
  `tests/conftest.py` (Fast Green registration),
  `tests/test_phase_149o_12b_hatp_signing_ceremony_implementation.py`,
  `tests/test_phase_149o_12a_signed_evidence_model_store_implementation.py`,
  `tests/test_phase_149o_8_hatp_ag3_ag5_production_consumption_signing_ceremony_architecture.py`,
  `tests/test_phase_149o_9_hatp_signing_ceremony_evidence_store_contract_freeze.py`
  (149O.5-F-3 boundary-test widening/inversion, see §9)
- **Tests:** 78 new (`test_hatp_cli.py`) + 25 new
  (`test_phase_149o_12c_hsce_attack_matrix.py`) = 103 new deterministic
  tests, all real-filesystem/fake-hardware, no real device required.
- **Pushed:** pending this report's own finalization sequence (see
  canonical phase-completion metadata for final commit hashes).

## HSCE-001 status

- **Version:** v1.1 (unchanged by this phase)
- **Byte status:** byte-unchanged (confirmed by `git diff --stat`
  against this phase's entering commit — empty)
- **HATP-001 byte status:** unchanged
- **RAE-001 byte status:** unchanged

## 1. Scope subset owned by this phase

HSCE-REQ-009..012 (exact CLI grammar), HSCE-REQ-013/016/017 (locator
validation, no user-typed security fields), HSCE-REQ-022..026 (no
provider/signer/substrate-readiness override flags), HSCE-REQ-046..048
(closed error vocabulary / exit-code mapping), HSCE-REQ-065/066/051
(success/error output discipline, no authority claims, no secret
leakage), HSCE-REQ-071 (blind-touch-defense integration — preserved
exactly as 149O.12B's production wrapper already owns it, not
duplicated at the CLI layer).

**Requirement coverage:** every requirement in this phase's owned
subset has both code (`src/pcae/commands/hatp.py`) and test coverage
(`tests/test_hatp_cli.py` field/grammar-level,
`tests/test_phase_149o_12c_hsce_attack_matrix.py` attack-level).

## 2. Production diff — exact allowlist confirmation

```
src/pcae/commands/hatp.py   NEW
src/pcae/cli.py             MODIFY (registration only, pure addition —
                             confirmed by `git diff --numstat`: 0 lines
                             removed)
```

No other `src/pcae/**` file appears in this commit's diff (`git
diff --stat 478e49c9^ 478e49c9 -- src/pcae/` — independently
re-confirmed at report-writing time). **Core-file byte identity:**
`src/pcae/core/hatp_signed_evidence.py`,
`src/pcae/core/hatp_evidence_store.py`, and
`src/pcae/core/hatp_signing_ceremony.py` all remain byte-unchanged
(`git diff --stat` against this phase's entering commit — empty for
all three). `src/pcae/core/hatp_ag_authority.py`,
`src/pcae/core/agent.py`, `src/pcae/commands/agent.py`,
`src/pcae/core/permission_broker.py`,
`src/pcae/core/permission_broker_foundation.py` all remain untouched.

**Unrelated hunks:** 0.

## 3. CLI hierarchy and exact syntax

```
pcae hatp sign rollback --site {ag3|ag5} (--job-id <id> | --per-id <id>) [--json]
```

- `pcae hatp` — new top-level command group.
- `pcae hatp sign` — sub-group (room reserved by HSCE-001's own naming,
  no other `hatp sign` subcommand added — HSCE-REQ-009).
- `pcae hatp sign rollback` — the one frozen leaf command.

**AG3 valid invocation:** `pcae hatp sign rollback --site ag3 --job-id
job-123 [--json]`.
**AG5 valid invocation:** `pcae hatp sign rollback --site ag5 --per-id
per-456 [--json]`.

**Wrong-site behavior:** `--site` uses `argparse choices=["ag3","ag5"]`
— any other value (including uppercase `AG3`) is rejected by argparse
itself before any handler code runs (`test_unknown_site_is_argparse_error`,
`test_uppercase_site_is_argparse_error`).

**Both-locators behavior:** rejected by `_validate_locator_arguments`
before any call into `production_sign_rollback_evidence` — the
wrong-locator-for-site message wins over the missing-locator message,
so a caller who supplies the wrong flag always gets the more specific
diagnosis (`test_locator_validation_rejects_before_production_call`).

**Missing-locator behavior:** rejected the same way (`--job-id is
required for --site ag3` / `--per-id is required for --site ag5`).

**Wrong-locator-for-site behavior:** rejected the same way (`--per-id
is not a valid locator for --site ag3; use --job-id`, and the AG5
mirror).

All four of the above return exit code `2` (ordinary argparse-style CLI
misuse, per governing-prompt §25 — never an HSCE `error_type`; confirmed
`error_type` is absent from the JSON payload in this failure mode,
`test_locator_validation_error_json_has_no_error_type`), and never call
`production_sign_rollback_evidence` (`called` spy assertion in every
parametrized case).

## 4. Forbidden-flag inventory

Every flag named in the governing prompt (§11) plus every flag named in
the 149O.11 implementation plan's own §13.2 inventory — the union, 31
flags total — is confirmed rejected by the argparse parser
(`test_forbidden_flag_rejected_by_parser`, parametrized) and confirmed
absent from the CLI handler's actual code, independent of docstring
prose, via a tokenize-based static scan that excludes `STRING`/`COMMENT`
tokens (`test_forbidden_flags_absent_from_source`):

`--provider`, `--signer`, `--principal`, `--trust-store`,
`--credential-store`, `--force`, `--overwrite`, `--output`,
`--repository-id`, `--decision-id`, `--decision-digest`, `--binding-id`,
`--binding-digest`, `--signer-key-id`, `--ecp-id`,
`--original-commit-sha`, `--issued-at`, `--timestamp`,
`--approval-present`, `--hatp-valid`, `--operational`, `--dry-run`,
`--hatp-trust-store`, `--trusted-key`, `--dev`, `--test-provider`,
`--software-provider`, `--skip-touch`, `--assume-present`,
`--ignore-not-ready`, `--root`.

## 5. CLI handler API / production wrapper call / zero-override proof

`run_hatp_sign_rollback(args: argparse.Namespace) -> int`
(`src/pcae/commands/hatp.py`) is the sole handler, registered via
`set_defaults(handler=run_hatp_sign_rollback)`, matching this
repository's existing `handler`/`args.handler(args)` dispatch
convention (`src/pcae/cli.py:main`).

**Production wrapper call:** exactly one call site,
`production_sign_rollback_evidence(root, site=site, job_id=args.job_id,
per_id=args.per_id)` — `root = HarnessPath.cwd()` (no `--root` flag, per
HSCE-001 contract §16).

**Zero-override proof (F-2 non-regression, mandatory attack 11):**
- `inspect.signature(production_sign_rollback_evidence)` carries exactly
  `{root, site, job_id, per_id}` — no `provider`/`trust_store`/`clock`/
  `confirm` parameter exists structurally
  (`test_production_wrapper_signature_carries_no_override_parameter`).
- An AST walk of `commands/hatp.py`'s one call site confirms it passes
  exactly `root` positionally and `site`/`job_id`/`per_id` as keywords —
  no other keyword (`test_handler_calls_production_wrapper_with_only_frozen_kwargs`).

**Internal `sign_rollback_evidence` non-reachability:** confirmed by a
tokenize-based static scan (excluding docstring prose) that the bare
identifier `sign_rollback_evidence` never appears in `commands/hatp.py`'s
code, and that `production_sign_rollback_evidence` is the only name of
that family referenced by any `ast.Name`/`ast.alias`
(`test_injectable_sign_function_never_imported_by_cli_handler`,
`test_run_hatp_sign_rollback_is_the_only_reference_to_sign_rollback_evidence_name_prefix`).

## 6. Help / import behavior without hardware

`pcae hatp --help`, `pcae hatp sign --help`, and `pcae hatp sign rollback
--help` are each confirmed to exit 0 in a **fresh subprocess**
(`test_help_succeeds_without_hardware_in_subprocess`) and to create no
`.pcae/hatp-evidence/` directory
(`test_help_creates_no_evidence_directory`). `commands/hatp.py`'s only
production import is `production_sign_rollback_evidence`, whose own
module (149O.12B) already imports cleanly without `fido2`/`cryptography`
installed — no hardware discovery occurs at import or `--help` time.

## 7. Human output / JSON output

**Human success:** "Signed HATP evidence created." plus `evidence_id`/
`evidence_path`/`idempotent`, followed by an explicit disclaimer that
this is not approval/permission/execution. Confirmed to contain none of
`approved`/`allowed`/`authorized for execution`/`permission granted`/
`rollback ready`/`rollback executed` (`test_success_human_output_has_no_authority_claims`).

**JSON success (exact frozen schema):**
```json
{"status": "success", "evidence_id": "<64-hex>", "evidence_path": "<path>", "idempotent": <bool>}
```
Confirmed to contain none of `approval_present`/`hatp_valid`/
`pb_decision`/`execution_available`/`approved`/`permission`/`executed`
(`test_success_json_output_schema_is_exact`). Constructed explicitly
(no `dataclasses.asdict()` of the core result type), so no accidental
internal field ever leaks.

**Human/JSON error:** `error: <message>` / `error_type: <type>` (human),
`{"status": "error", "error_type": "<type>", "message": "<message>"}`
(JSON) — every one of the 12 closed `error_type` values confirmed for
both human and JSON rendering and the correct exit code
(`test_every_error_type_human_and_json_output_and_exit_code`,
parametrized ×12×2).

## 8. Error vocabulary / exit-code mapping

The closed 12-member `error_type` vocabulary
(`repository_identity_unavailable`, `operation_not_found`,
`decision_unavailable`, `binding_unavailable`, `no_authorized_signer`,
`provider_unavailable`, `hardware_device_fault`,
`human_signing_cancelled`, `provider_signature_failure`,
`evidence_serialization_failure`, `evidence_conflict`,
`evidence_persistence_failure`) is centralized in one dict,
`_EXIT_CODE_BY_ERROR_TYPE`, mapping to the frozen 9 exit categories
(`EXIT_SUCCESS=0` through `EXIT_PERSISTENCE_FAILURE=8`). Set-equality
between the mapping's keys and the closed vocabulary, and full
9-category coverage, are both independently tested
(`test_error_vocabulary_is_exactly_the_closed_12_member_set`,
`test_all_nine_exit_categories_are_represented`).

`hatp_signing_ceremony.py`'s own 10 exception subclasses each carry a
class-level `error_type` used directly; `hatp_evidence_store.py`'s
`EvidenceConflictError`/`EvidencePersistenceFailureError` and
`hatp_signed_evidence.py`'s `HATPSignedEvidenceError` (structural
envelope-construction failure) carry no such attribute of their own and
are mapped explicitly by `_error_type_for` — never re-wrapped or
reinterpreted, propagated unmodified.

**Exit-zero semantics:** `EXIT_SUCCESS` occurs only when
`production_sign_rollback_evidence` returns normally (including
idempotent-success). Every one of the 12 error types maps to a non-zero
exit; an unclassified exception (a genuine bug) is never caught by the
handler and propagates unmislabeled
(`test_unexpected_internal_exception_is_never_mislabeled_as_success`).

## 9. Cancellation / device absence / provider failure / TOCTOU / Binding / AG3 / AG5

All six exercised through the fully assembled CLI handler (real parser
→ real handler → real resolver/Binding lookup/store, fake hardware
provider/trust store/clock only):

- **`human_signing_cancelled`** (attack 16): `confirm` declines →
  `EXIT_HUMAN_CANCELLED`(5), no evidence file
  (`test_attack_16_human_cancellation_via_cli_no_evidence`).
- **`provider_unavailable`** (attack 17): provider disappears at touch
  → `EXIT_SUBSTRATE_UNAVAILABLE`(4), no evidence
  (`test_attack_17_device_absence_via_cli_no_fallback`).
- **`evidence_serialization_failure`** (attack 18, TOCTOU discard): a
  second, superseding Binding is created from inside `confirm()` →
  exactly one provider call, no publish, no auto-retry
  (`test_attack_18_toctou_discard_via_cli_exactly_one_provider_call_no_publish`).
- **`binding_unavailable`** (attack 19): no RAE Binding exists → fails
  before any hardware touch (`provider.request_signature_calls == 0`
  and `credential_identity_calls == 0`)
  (`test_attack_19_missing_binding_fails_before_touch_no_hardware_call`).
- **`operation_not_found`** (attack 20, AG5): PER exists, `ecp_id`
  unresolvable → fails before touch
  (`test_attack_20_ag5_ecp_id_unresolvable_fails_before_touch`).
- **`operation_not_found`** (attack 21, AG3): job exists,
  `original_commit_sha` unresolvable → fails before touch
  (`test_attack_21_ag3_original_commit_sha_unresolvable_fails_before_touch`).

## 10. No legacy mutation / no PER mutation / no PB / no approval_present / no rollback dispatch / no auto-consumption

- **No legacy approval mutation / no PER status mutation:** confirmed by
  static source scan of `commands/hatp.py` for
  `rollback_approval_state`/`approve_rollback` (absent —
  `test_no_scope_creep_in_cli_handler_source`) and by 149O.12B's own
  unmodified core module never calling either.
- **No PB:** `commands/hatp.py` never imports `permission_broker*`
  (same static scan).
- **No `approval_present`:** never derived or referenced anywhere in
  this module (same scan; also confirmed absent from every success/
  error JSON payload assertion above).
- **No rollback dispatch:** `execute_rollback`/`build_rollback_execution`/
  `run_rollback` never appear in `commands/hatp.py`'s code (same scan).
  `pcae rollback`, `pcae remote rollback approve/deny/execute` remain
  byte-unchanged this phase (confirmed via the production-diff
  allowlist, §2 — `commands/agent.py` untouched).
- **No automatic evidence consumption:** the CLI never performs a
  "latest"/glob lookup of `.pcae/hatp-evidence/`; each invocation only
  ever writes/reads the one `evidence_id` its own signing attempt
  produces (structural — no lookup-by-anything-other-than-fresh-signing
  code path exists in this module at all).

## 11. Mandatory attack-matrix results (1-21)

| # | Attack | Result |
|---|---|---|
| 1 | Path traversal `evidence_id` | rejected before filesystem access — PASS |
| 2 | Case aliasing (uppercase) | rejected, no case-insensitive alias — PASS |
| 3 | Idempotent rewrite (identical bytes) | success, no duplicate, same `evidence_id` — PASS |
| 4 | Conflicting rewrite (differing assertion) | `evidence_conflict`, winner unchanged — PASS |
| 5 | Duplicate JSON key | rejected at parse — PASS |
| 6 | Unknown top-level field | rejected, closed schema — PASS |
| 7 | `evidence_version` bool | rejected — PASS |
| 8 | Missing required field | rejected at parse — PASS |
| 9 | `evidence_id`/digest mismatch | rejected — PASS |
| 10 | Corrupt `provider_assertion` | parses structurally, no `verified`/`approved` field ever exposed — PASS |
| 11 | Provider-profile override | unreachable — no `--provider` flag, argparse rejects — PASS |
| 12 | Wrong-operation replay | two distinct operations never collide on `evidence_id`; each envelope's embedded `operation_reference` bound to its own locator — PASS |
| 13 | Evidence-file symlink | rejected — PASS |
| 14 | Store-root symlink | rejected — PASS |
| 15 | Partial/interrupted write | no canonical final artifact visible — PASS |
| 16 | Human cancellation | no evidence, exit 5 — PASS |
| 17 | Hardware device absent | `provider_unavailable`, exit 4, no fallback — PASS |
| 18 | Post-preview mutation (TOCTOU) | discarded, no publish, exactly one provider call — PASS |
| 19 | No matching Binding | `binding_unavailable`, exit 3, before touch — PASS |
| 20 | AG5 `ecp_id` unresolvable | `operation_not_found`, exit 2, before touch — PASS |
| 21 | AG3 `original_commit_sha` unresolvable | `operation_not_found`, exit 2, before touch — PASS |

**Extra attacks:**

| # | Attack | Result |
|---|---|---|
| E1 | Obs-3 loser-read (non-regular object at final path) | fails closed, never `evidence_conflict` — PASS |
| E2 | Temp-FD mutation | canonical bytes unchanged post-publish — PASS |
| E3 | Many-writer race (8 concurrent identical writers) | exactly one canonical file, 1 winner + 7 idempotent — PASS |
| E4 | Non-EEXIST link error (`EXDEV`) | fails closed, no fallback, no file created — PASS |

Every attack enters through the highest practical assembled boundary:
CLI-argument-shaped attacks (11) through the real parser; ceremony-flow
attacks (16-21) through the real, assembled CLI handler with only the
hardware provider/trust store/clock faked; envelope/store-shaped attacks
(1-2, 5-10, 13-15, E1-E4) — which have no CLI-argument surface at all —
against a genuine envelope produced by a real, CLI-driven signing call.

## 12. Regressions

- **149O.12A regression:** `tests/test_hatp_signed_evidence.py` +
  `tests/test_hatp_evidence_store.py` — all green, modules byte-unchanged.
- **149O.12B regression:** `tests/test_hatp_signing_ceremony.py` +
  `tests/test_phase_149o_12b_hatp_signing_ceremony_implementation.py` —
  all green (12B's own phase-boundary file updated per §13 below;
  substance unchanged).
- **149O.9/10/10.1/10.2 regression:** re-run as part of the full
  `-k "hatp or rollback_approval"` sweep (§14) — zero new failures.
- **Wave 3-7 / RAE / rollback / PB regression:** `-k "rollback or
  permission_broker"` (1403 passed, 5 pre-existing unrelated failures,
  identical set before/after this phase) and `tests/test_agent.py -k
  rollback` (78 passed, 0 failed) — no rollback dispatch behavior
  changed.
- **Fast Green:** 4868 passed, 2 skipped, 1 pre-existing collection
  error (`fido2` absent, unrelated), 0 genuine failures (one
  `-n auto`-only flaky unrelated test, `test_backend_cli.py::
  TestBackendReviewCreate::test_create_persists_to_latest`, passes
  standalone) — entering baseline was 4828 passed/1 skipped/0 failed;
  delta matches this phase's own newly Fast-Green-registered
  `test_hatp_cli`/`test_phase_149o_12c_hsce_attack_matrix` modules.
- **Report trust:** `test_phase_report_trust_gate*.py`,
  `test_phase_reports*.py`, `test_push_phase_report_identity_137f1.py` —
  272 passed, 0 failed.

## 13. Pre-existing/unrelated failures (not caused by this phase)

Independently confirmed via `git stash -u` A/B comparison on the
`-k "hatp or rollback_approval"` sweep: **13 failures present
identically before and after this phase's changes** —
`test_phase_149o_10_1`/`10_2`/`10` (`test_no_hatp_sign_cli_
implementation_exists*` — these three are older "CLI not implemented
yet" boundary tests for phases that predate 149O.12A entirely; updating
them is out of this phase's own allowed-file scope and they are not
"regressed" — they were already broken by 149O.12A's own signing
surface groundwork before this phase touched anything), 4×
`test_phase_149o_rollback_approval_evidence_canonical_provenance_
hardening_independent_verification.py` (unrelated pre-existing forgery-
harness failures), and several `test_phase_149o_1f*`/`1h*`/`4`
byte-identity/import checks unrelated to the CLI surface. None of these
13 are newly introduced by this phase.

**149O.12B Python-3.9 publication-timestamp defect
(`pcae.governance.publication.coordinator._parse_timestamp` lacking
trailing-`Z` normalization):** confirmed still present, still
out-of-scope, still worked around only at the test layer (identical
autouse-fixture technique, duplicated — not imported — into
`tests/test_phase_149o_12c_hsce_attack_matrix.py`, since the fixture is
module-scoped and not otherwise importable as a fixture across files).
No production file was touched to work around it. Recommended for a
future, separately-scoped governed repair (unchanged recommendation from
149O.12B).

## 14. 149O.5-F-3 boundary-test widening (this phase's own instance)

Six pre-existing phase-boundary test files asserted, by design, "no
HATP CLI surface/`--provider` mention exists yet" as a snapshot valid
only *before* 149O.12C landed — exactly the situation the 149O.11 plan's
own §17 anticipated and the repository's established 149O.5-F-3
precedent covers ("this implementation's intentional addition of a new
HATP CLI consumer does not itself trip a stale 'zero HATP CLI consumers'
assumption elsewhere in the test suite. Any existing test asserting that
should be updated to reference this table, not deleted"). Updated,
narrowly, in this phase:

- `tests/test_phase_149o_12b_hatp_signing_ceremony_implementation.py` —
  `_EXPECTED_PRODUCTION_FILES` widened to include this phase's two
  files; the four "CLI must not exist yet" assertions inverted to "CLI
  now exists, exactly as 149O.12B's own report recommended"; every other
  invariant (149O.12A byte-identity, contract byte-identity, no PB
  import, no AG-authority wiring) left completely unchanged.
- `tests/test_phase_149o_12a_signed_evidence_model_store_implementation.py`
  — identical treatment via its own pre-existing
  `_LATER_PHASE_APPROVED_FILES` widening mechanism (already used once
  for 149O.12B itself).
- `tests/test_phase_149o_8_...py` /
  `tests/test_phase_149o_9_...py` — two "no `--provider` flag mention
  anywhere in `commands/`" checks were **naive whole-text substring
  scans** that this module's own thorough docstring (explaining *why* no
  such flag exists) tripped as a false positive; narrowed to a real
  `add_argument("--provider"...)` regex detection, which correctly finds
  nothing (the actual invariant — no such flag is ever defined — is
  unweakened and independently reconfirmed by `test_hatp_cli.py`'s own
  code-only, docstring-excluded forbidden-flag suite). 149O.9's own
  "no CLI implemented yet" check was also inverted, scoped explicitly to
  exclude `commands/hatp.py` by name so 149O.9's own historical
  don't-implement-early claim about *its own* files remains intact.

No invariant these six files protect was weakened; only the "no HATP CLI
exists yet" snapshot — which was always going to become false the moment
this phase's own planned, previously-recommended work landed — was
updated to the current, intentional state.

## 15. Findings

- **149O.10-F-3:** INDEPENDENTLY CONFIRMED CLOSED (unchanged).
- **149O.10.2-Obs-3:** RESOLVED AT IMPLEMENTATION LEVEL — PENDING
  149O.13 INDEPENDENT VERIFICATION (unchanged; this phase's E1 attack
  re-exercises the same mapping through a CLI-driven envelope, still
  non-blocking).
- **149O.10.2-Obs-4:** historical report-accounting observation
  (unchanged).
- **149O.5-F-3:** historical stale-boundary-test debt — this phase is
  itself a fresh instance of applying that lesson (§14 above); the
  underlying pattern remains retained, non-blocking debt for future
  phases to keep applying.
- **149O.12B Python-3.9 publication-timestamp defect:** PRE-EXISTING /
  OUT OF SCOPE / OPEN (unchanged).
- **B-149O.3-1, B-149O.3-3, B-149O.3-8:** NON-BLOCKING (unchanged).

## 16. Verdict

```
HATP SIGNING CLI + HSCE ASSEMBLED IMPLEMENTATION:
IMPLEMENTED
— READY FOR INDEPENDENT VERIFICATION
```

**HSCE SIGNING CEREMONY + EVIDENCE STORE IMPLEMENTATION: COMPLETE** —
meaning the evidence model/store (149O.12A), the signing resolver/
orchestrator (149O.12B), and the CLI signing surface (149O.12C, this
phase) are all implemented. Explicitly qualified: **production rollback
consumption is NOT complete. Execution enforcement is NOT complete. HATP
production is NOT READY.**

`B-149O-1..4` remain **INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED**, unchanged by this phase.
Mandatory rollback consumption is still missing; a signing surface alone
does not establish it.

Runtime remains **Observed / observe / unavailable**.

## 17. No-Go confirmations

Only `src/pcae/commands/hatp.py` (NEW) and `src/pcae/cli.py`
(registration-only MODIFY) were changed in production this phase.
149O.12A's two modules and 149O.12B's one module all remain
byte-unchanged. HSCE-001 v1.1, HATP-001 v1.0, and RAE-001 v1.0 all
remain byte-unchanged. No rollback command (`pcae rollback`, `pcae
remote rollback approve/deny/execute`) was modified. No AG3/AG5
mandatory evidence consumption was implemented — signed evidence created
by this CLI is not automatically discovered or consumed by anything. No
legacy `rollback_approval_state`/PER-status mutation occurs anywhere in
the new module. No Permission Broker behavior changed (no
`permission_broker*` import). No `approval_present` value was derived.
No rollback execution was performed by signing. No Class-B host
provisioning occurred. No HATP production activation occurred. Signing
success remains distinct from verification, approval, permission,
capability, and execution throughout this phase's output schema.
`B-149O-1..4` remain independently verified at the HATP-gated authority
boundary with system execution closure deferred. HATP production remains
**NOT READY**. Runtime remains **Observed / observe / unavailable**.

## 18. Recommended next phase

```
149O.13 — HATP Signing Ceremony + Evidence Store Independent Implementation Verification
```

Must independently reconstruct and adversarially verify: 12A's
model/store, 12B's context/signing/TOCTOU, 12C's CLI (this phase), all
21 mandatory attacks plus the four extra implementation attacks,
production dependency closure (no `fido2` hard requirement at import/
help time), no authority conflation anywhere in output/logs, and no
rollback-consumption side effects. Do not proceed directly to mandatory
AG3/AG5 consumption wiring before 149O.13 completes.
