# Phase 149O.11 — HATP Signing Ceremony + Evidence Store Implementation Plan

Phase type: **IMPLEMENTATION PLAN ONLY**. No production source modified. No CLI implemented. No evidence store implemented. No hardware touched. No `.pcae/hatp-evidence/` created.

## 1. Baseline / Confirmed Position

- Latest completed phase: **149O.10.2 — HSCE-001 Atomic No-Clobber Repair Independent Re-Verification.** Status: completed, report complete, pushed, `origin/main..HEAD = 0`.
- Contract verdict entering this phase: **HSCE-001 v1.1 — VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS. READY FOR IMPLEMENTATION PLANNING.**
- `149O.10-F-1`, `149O.10-F-2`, `149O.10-F-3`, `149O.10-Obs-2`: all INDEPENDENTLY CONFIRMED CLOSED.
- `149O.10.2-Obs-3` (loser-comparison read-failure `error_type` gap) and `149O.10.2-Obs-4` (report-count discrepancy, 89 vs. reproducible 29) remain open **non-blocking observations**, explicitly deferred to this phase's design work (Obs-3) or retained as a documentation note only (Obs-4).
- HSCE inventory: **HSCE-REQ-001..079**, 79 requirements, sequential, gapless (independently reconfirmed by regex extraction this phase, see §5).
- Mandatory attack matrix: **21 items** (widened from 20 by 149O.10.1's Obs-2 closure).
- `B-149O-1..4`: INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED. Unaffected by this phase.
- HATP production: **NOT READY**. Runtime: **Observed / observe / unavailable**.
- Initial inspection this phase reconfirmed: repo clean, `origin/main..HEAD = 0`; `pcae health` healthy; `pcae check` passed; `pcae status coherence` coherent; `pcae doctor task-memory` warnings are pre-existing/unrelated (stale `tasks/done/` DONE.md sync gaps predating this phase, plus one now-remediated stale active-task file from a post-149O.6 idle placeholder); `pcae push check` clean (`nothing_to_push`); `pcae runtime inspect` Observed/observe/unavailable, PB `execution_unavailable`; `pcae notify status` Telegram configured/enabled/ready; `pcae phase-report show --latest` confirms 149O.10.2 completed/complete/pushed/consistent; `pcae phase-report reconcile --phase-id 149O.10.2` returned `reconciled` (inspection-only, no mutation).

This plan governs the **implementation** of HSCE-001 v1.1's already-frozen surface. It reinterprets nothing. Where the contract text is silent (Obs-3), this plan selects and documents one contract-consistent resolution, per the governing prompt's instruction, without amending HSCE-001 itself.

## 2. Contract State Entering This Phase

| Contract | Version | Status | Byte-changed by this phase? |
|---|---|---|---|
| HSCE-001 | 1.1 | VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS | No |
| HATP-001 | 1.0 | FROZEN, unamended | No |
| RAE-001 | 1.0 | FROZEN, unamended | No |

## 3. Current Production Source Architecture (as independently inspected this phase)

- `src/pcae/core/human_approval_trusted_provenance.py` — owns `HumanApprovalProvenanceProof`, `parse_hatp_proof`, `hatp_proof_to_document`, `canonicalize_hatp_proof_payload` (the *signed* canonical payload — `sort_keys=True, separators=(",",":"), ensure_ascii=False, allow_nan=False`, UTF-8), `digest_hatp_proof_payload` (SHA-256 hex of that payload), `_require_proof_version` (explicit `isinstance(value, bool)` pre-check pattern), `_reject_duplicate_keys`/`_load_json_no_duplicate_keys` (module-local, duplicated-by-convention), the 13-state `HATPVerificationStatus` vocabulary, `verify_hatp_proof`, `inspect_hatp_verification_substrate_readiness`, `HATPVerificationEvidence(assertion: bytes)`.
- `src/pcae/core/hatp_providers.py` — `ProviderAssertion(credential_id, provider_profile, algorithm, evidence: bytes)`, `HATPHardwareSigner` protocol (`.request_signature(payload, *, signer_key_id, provider_profile, presence_timeout_s=30.0)`), `HATP_HARDWARE_PROVIDER_V1` constant, `create_production_hardware_provider(provider_profile, *, allow_piv_fallback=False)`, `discover_hardware_providers()`, `HATPProviderUnavailableError`, `HATPProviderCancelledError`, `HATPProviderDeviceError`, `TestHATPProofVerifierProvider` (test-only, `__test__ = False`, never production-reachable).
- `src/pcae/core/hatp_fido2_provider.py` — `Fido2HardwareProvider`; imports `fido2`/`cryptography` at module top level; reached only via `hatp_providers.py`'s `try/except ImportError` boundary, never imported eagerly elsewhere.
- `src/pcae/core/hatp_hardware_credentials.py` — `HATPHardwareCredentialStore.production()`, `.lookup_credential(signer_key_id)`. Consumed by a concrete provider's own `.verify()`, not directly by Wave 4 or by this plan's orchestrator.
- `src/pcae/core/hatp_bootstrap.py` — `HATPTrustStore.production()`, `.lookup_signer`, `.resolve_deployment_authorization`, `resolve_canonical_deployment_root(path)`, `deployment_binding_matches`.
- `src/pcae/core/hatp_ag_authority.py` — `resolve_ag3_gated_rollback_authority(...)`, `resolve_ag5_gated_rollback_authority(...)` — Wave 7 consumers of HATP evidence; **out of scope for this implementation** (149O.12-13 wiring), referenced only to confirm this plan introduces no conflicting AG3/AG5 helper names.
- `src/pcae/core/rollback_approval_evidence.py` — `RollbackApprovalEvidenceStore.list_bindings_with_keys()` (the lookup surface HSCE-REQ-020 requires), `RollbackApprovalBinding` (fields incl. `evidence_id`, `governance_record_reference`, `rollback_site`, `rollback_operation_reference`, `state`), `_write_atomic_json` (temp-file-in-same-directory + fsync + `os.replace` — **the technique to mirror, not call directly**, since it has no symlink checks and uses `os.replace` not `os.link`).
- `src/pcae/core/repository_identity.py` — `read_repository_identity(root)`, `is_valid_repository_instance_id`.
- `src/pcae/commands/agent.py` / `src/pcae/core/agent.py` — `run_rollback(args)` → `build_rollback_execution(HarnessPath.cwd(), args.per_id, dry_run=...)` (`src/pcae/commands/agent.py:16258`, registered `src/pcae/cli.py:3035`) is the existing production CLI-handler pattern this plan's new `commands/hatp.py` handler mirrors. `execute_rollback` / `build_rollback_execution` are **never called** by this plan's code (HSCE-REQ-067 boundary).
- `src/pcae/cli.py` — subcommand registration convention: `from pcae.commands.<module> import run_xxx` → `subparsers.add_parser("<name>", ...)` → `.add_argument(...)` → `.set_defaults(handler=run_xxx)`. `src/pcae/commands/` currently has no `hatp.py`.
- **No production code anywhere uses `os.link`** (confirmed by grep). The existing atomic-exclusive idiom is `os.open(path, os.O_CREAT|os.O_EXCL|os.O_WRONLY)` (`governance/publication/storage.py:126`, `rollback_approval_evidence.py:650`), and the existing atomic-but-*not*-exclusive idiom is temp-file+fsync+`os.replace` (duplicated independently at ~8 call sites — established repo convention is deliberate per-module duplication of small helpers, not a shared import). This plan's `hatp_evidence_store.py` continues that convention: a **new**, independently-defined `os.link`-based helper, not a call into any existing `_write_atomic_json`.
- Two existing strict-JSON techniques: (a) `pcae.schema_runtime.json_parser` — general-purpose recursive-descent strict parser with path-reporting duplicate-key rejection; (b) HATP's own module-local `_reject_duplicate_keys` + `json.loads(object_pairs_hook=...)` pattern (`human_approval_trusted_provenance.py:341-356`), duplicated per-module by convention elsewhere in HATP. This plan's envelope parser follows convention (b) — a **new, module-local** duplicate-key rejector in `hatp_signed_evidence.py`, matching the codebase's own HATP-family precedent, per HSCE-REQ-053's explicit instruction to reuse "the `object_pairs_hook` technique."

## 4. Proposed Module Architecture

| Module | Status | Owns |
|---|---|---|
| `src/pcae/core/hatp_signed_evidence.py` | NEW | `HATPSignedEvidenceEnvelope` model, parser, canonical serializer, evidence-ID validator |
| `src/pcae/core/hatp_evidence_store.py` | NEW | Store root/path, `load`/`publish`/`path_for`, exclusive hard-link publication algorithm |
| `src/pcae/core/hatp_signing_ceremony.py` | NEW | Proof-context resolution (AG3/AG5), provider/signer resolution, preview, hardware invocation, TOCTOU recheck, persistence orchestration |
| `src/pcae/commands/hatp.py` | NEW | CLI handler(s), human/JSON output, error→exit-code mapping |
| `src/pcae/cli.py` | MODIFY | Parser registration only (`hatp sign rollback` subcommand wiring) |

No other production file is touched. Explicitly **not** modified: `permission_broker_foundation.py`, `permission_broker.py`, `agent.py`, `hatp_ag_authority.py`, any rollback-dispatch code, `human_approval_trusted_provenance.py`, `hatp_providers.py`, `hatp_bootstrap.py`, `rollback_approval_evidence.py`, `repository_identity.py` (all consumed read-only, imported not edited).

Naming rationale: three focused core modules (not one monolith, not folded into `human_approval_trusted_provenance.py` which already owns proof/verification semantics and must not destabilize its verified Wave-3/4 surface) plus one CLI module, matching the existing one-module-per-command-area / one-module-per-concern convention already used across `src/pcae/core/` and `src/pcae/commands/`.

## 5. 79-Requirement Traceability Table

Every requirement appears exactly once as primary owner. "Narrative" rows are contract-history/scope statements with no code obligation of their own; they are satisfied by architectural conformance to the requirements they introduce, verified by inspection rather than by a dedicated test.

| Req | Primary owner | Test owner | Attack rel. |
|---|---|---|---|
| REQ-001 | Narrative (purpose) | — | — |
| REQ-002 | Narrative (scope boundary: no AG3/AG5 wiring) | boundary test in `test_hatp_cli.py` (no `--hatp-evidence` consumption added) | — |
| REQ-003 | Cross-cutting (all 4 modules) | full suite | — |
| REQ-004 | Cross-cutting scope exclusion (no HATP/RAE/PB edits, no `--hatp-evidence` wiring, no Class-B) | production-diff allowlist test (§16) | — |
| REQ-005 | Narrative (definitions) | — | — |
| REQ-006 | `hatp_signing_ceremony.py`, `hatp_signed_evidence.py` — reuse not reimplement `HumanApprovalProvenanceProof`/`canonicalize_hatp_proof_payload`/`digest_hatp_proof_payload`/`verify_hatp_proof` | non-regression: HATP-001 byte-unchanged | — |
| REQ-007 | `hatp_evidence_store.py` — distinct root from `.pcae/rollback-approval-evidence/` | `test_hatp_evidence_store.py` root isolation test | — |
| REQ-008 | Narrative (exclusive governance scope) | — | — |
| REQ-009 | `commands/hatp.py`, `cli.py` — exact grammar `pcae hatp sign rollback --site {ag3\|ag5} [locators] [--json]` | `test_hatp_cli.py` grammar tests | 11 |
| REQ-010 | `cli.py` — `--site` `choices=["ag3","ag5"]` | `test_hatp_cli.py` invalid-site test | — |
| REQ-011 | `commands/hatp.py` — `--json` output mode | `test_hatp_cli.py` JSON-mode test | — |
| REQ-012 | `cli.py` — no `--dry-run` registered | `test_hatp_cli.py` forbidden-flags test | — |
| REQ-013 | `cli.py` + `hatp_signing_ceremony.py` — AG3 `--job-id` only, `original_commit_sha` from live job record | `test_hatp_signing_ceremony.py` AG3 resolution | 21 |
| REQ-014 | Narrative (architecture finding, informs REQ-067 boundary) | boundary test asserting no new caller of `build_rollback_execution` | — |
| REQ-015 | Narrative (production entry-point finding) | boundary test | — |
| REQ-016 | `cli.py` + `hatp_signing_ceremony.py` — AG5 `--per-id` only, `ecp_id` auto-derived from PER | `test_hatp_signing_ceremony.py` AG5 resolution | 20 |
| REQ-017 | `cli.py` — forbidden-flag inventory test | `test_hatp_cli.py` | — |
| REQ-018 | `hatp_signing_ceremony.py` — proof-field-source resolver (the central function) | `test_hatp_signing_ceremony.py` field-by-field source assertions | — |
| REQ-019 | `hatp_signing_ceremony.py` — no boolean human-presence input path exists | `test_hatp_cli.py` forbidden-flags | — |
| REQ-020 | `hatp_signing_ceremony.py` — Binding resolver via `list_bindings_with_keys()` + supersession discipline | `test_hatp_signing_ceremony.py` | 19 |
| REQ-021 | `hatp_signing_ceremony.py` — `binding_unavailable`, before provider touch | `test_hatp_signing_ceremony.py` no-touch-on-precondition-failure | 19 |
| REQ-022 | `hatp_signing_ceremony.py` — sole call `create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)` | `test_hatp_signing_ceremony.py` + `test_hatp_cli.py` (no `--provider`) | 11 |
| REQ-023 | `hatp_signing_ceremony.py` — sole call `HATPTrustStore.production()` | `test_hatp_cli.py` (no `--hatp-trust-store`) | — |
| REQ-024 | `hatp_signing_ceremony.py` — `no_authorized_signer` mapping | `test_hatp_signing_ceremony.py` | — |
| REQ-025 | `hatp_signing_ceremony.py` — substrate readiness NOT called as a gate | `test_hatp_signing_ceremony.py` (readiness-NOT_READY-still-signs test) | — |
| REQ-026 | `cli.py` — no force/dev/ignore-not-ready flags | `test_hatp_cli.py` forbidden-flags | — |
| REQ-027 | `hatp_signing_ceremony.py` — `request_signature(canonicalize_hatp_proof_payload(proof), ...)` | `test_hatp_signing_ceremony.py` | 10 |
| REQ-028 | `hatp_signing_ceremony.py` — `provider_unavailable` | `test_hatp_signing_ceremony.py` device-absence | 17 |
| REQ-029 | `hatp_signing_ceremony.py` — `human_signing_cancelled`, no evidence persisted | `test_hatp_signing_ceremony.py` cancellation | 16 |
| REQ-030 | `hatp_signing_ceremony.py` — `hardware_device_fault`, distinct from cancellation | `test_hatp_signing_ceremony.py` device-fault | — |
| REQ-031 | `hatp_signed_evidence.py` — `HATPSignedEvidenceEnvelope` type definition | `test_hatp_signed_evidence.py` | — |
| REQ-032 | `hatp_signed_evidence.py` — closed 4-field set | `test_hatp_signed_evidence.py` unknown-field rejection | 6 |
| REQ-033 | `hatp_signed_evidence.py` — `evidence_version==1`, bool-rejecting | `test_hatp_signed_evidence.py` version tests | 7 |
| REQ-034 | `hatp_signed_evidence.py` — Base64 of `ProviderAssertion.evidence` | `test_hatp_signed_evidence.py` | — |
| REQ-035 | `hatp_signed_evidence.py`/`hatp_evidence_store.py` — load-time Base64 decode → `HATPVerificationEvidence` | `test_hatp_evidence_store.py` load test | 10 |
| REQ-036 | `hatp_signed_evidence.py` — `evidence_id = digest_hatp_proof_payload(proof)` | `test_hatp_signed_evidence.py` digest binding | 9 |
| REQ-037 | `hatp_signed_evidence.py` — content-addressing precision (proof only) | `test_hatp_signed_evidence.py` | — |
| REQ-038 | `hatp_evidence_store.py` — same-ID different-assertion → conflict, first-persisted canonical | `test_hatp_evidence_store.py` conflict test | 4 |
| REQ-039 | `hatp_evidence_store.py` — create-once/no-clobber (A/B outcomes) | `test_hatp_evidence_store.py` idempotency+conflict | 3, 4 |
| REQ-040 | `hatp_signed_evidence.py` — immutability-by-construction (pure function of `proof`) | `test_hatp_signed_evidence.py` | — |
| REQ-041 | `hatp_evidence_store.py` — root `.pcae/hatp-evidence/`, repo-root-relative | `test_hatp_evidence_store.py` root resolution | — |
| REQ-042 | `hatp_evidence_store.py` — `envelopes/{evidence_id}.json` layout | `test_hatp_evidence_store.py` path_for | — |
| REQ-043 | `hatp_evidence_store.py` — no sibling files/index/latest-symlink API surface | `test_hatp_evidence_store.py` API-surface negative test | — |
| REQ-044 | `hatp_evidence_store.py` — `load(evidence_id)` explicit-only | `test_hatp_evidence_store.py` | — |
| REQ-045 | `hatp_evidence_store.py` — `load()` return contract note (ID is locator only, future consumer must reverify) | `test_hatp_evidence_store.py` docstring/contract test | — |
| REQ-046 | `commands/hatp.py` — closed exit-code set (0-8) | `test_hatp_cli.py` exit-code table | — |
| REQ-047 | `commands/hatp.py` — `error_type`→exit-code mapping table | `test_hatp_cli.py` | — |
| REQ-048 | `hatp_signing_ceremony.py`/`hatp_evidence_store.py` — closed `error_type` enum, no ad hoc strings | full suite | — |
| REQ-049 | `hatp_signing_ceremony.py` — signing errors never expressed as `HATPVerificationStatus` | code review / type-boundary test | — |
| REQ-050 | `hatp_signing_ceremony.py`, `hatp_signed_evidence.py`, `commands/hatp.py` — no secret persisted/logged/argv | `test_hatp_signing_ceremony.py` + `test_hatp_cli.py` secret-absence scan | — |
| REQ-051 | `commands/hatp.py` — diagnostic logging allowed-field scope | `test_hatp_cli.py` logging test | — |
| REQ-052 | `hatp_evidence_store.py` — exclusive hard-link publication algorithm (the central requirement, full algorithm in §10) | `test_hatp_evidence_store.py` real-filesystem race suite | 3, 4, 15, 122, 123 |
| REQ-053 | `hatp_signed_evidence.py` — `serialize_hatp_signed_evidence()` canonical bytes (UTF-8, sort_keys, allow_nan=False, dup-key-rejecting parse) | `test_hatp_signed_evidence.py` canonical-bytes test | 3, 4, 5 |
| REQ-054 | `hatp_evidence_store.py` — ordinary repo-private file mode | `test_hatp_evidence_store.py` | — |
| REQ-055 | `hatp_evidence_store.py` — `mkdir(parents=True, exist_ok=True)` on first publish only | `test_hatp_evidence_store.py` + `test_hatp_cli.py` no-dir-on-help test | — |
| REQ-056 | `hatp_signed_evidence.py` — shared `evidence_id` validator (lowercase 64-hex, pre-path-construction) | `test_hatp_signed_evidence.py` + `test_hatp_evidence_store.py` | 1, 2 |
| REQ-057 | `hatp_evidence_store.py` — destination-symlink rejection | `test_hatp_evidence_store.py` symlink test | 13 |
| REQ-058 | `hatp_evidence_store.py` — escaping path-component symlink rejection | `test_hatp_evidence_store.py` root-symlink test | 14 |
| REQ-059 | `hatp_signed_evidence.py` — always-lowercase, no case alias | `test_hatp_signed_evidence.py` uppercase-rejection | 2 |
| REQ-060 | `hatp_evidence_store.py` — untrusted-storage classification (docstring + no-authority design) | code review | — |
| REQ-061 | `hatp_evidence_store.py` — no `exists()`-as-approval API; `hatp_signing_ceremony.py` never checks bare existence as authority | `test_hatp_evidence_store.py` forbidden-pattern test | — |
| REQ-062 | `hatp_signed_evidence.py` — parse: closed schema + digest recheck | `test_hatp_signed_evidence.py` | 6, 8, 9 |
| REQ-063 | `hatp_signed_evidence.py` — parsing establishes structural validity only | docstring + `test_hatp_signed_evidence.py` | — |
| REQ-064 | `hatp_evidence_store.py` — missing/corrupt → `approval_present=False`/`evidence_not_found` | `test_hatp_evidence_store.py` missing/corrupt tests | — |
| REQ-065 | `commands/hatp.py` — exit-0 meaning (evidence persisted only) | `test_hatp_cli.py` success-semantics test | — |
| REQ-066 | `commands/hatp.py` — success output schema (no `approved`/`permission`/`executed`) | `test_hatp_cli.py` output-schema negative test | — |
| REQ-067 | `hatp_signing_ceremony.py`, `commands/hatp.py` — never call `execute_rollback`/`build_rollback_execution` | boundary test (grep-based + call-graph assertion) | — |
| REQ-068 | `hatp_signing_ceremony.py` — `issued_at` via reused `_canonical_timestamp_string` convention, no caller clock | `test_hatp_signing_ceremony.py` clock-seam test, Python 3.9 check | — |
| REQ-069 | `hatp_signing_ceremony.py` — context captured once at proof-construction (context A) | `test_hatp_signing_ceremony.py` TOCTOU setup | — |
| REQ-070 | `hatp_signing_ceremony.py` — post-sign recheck (context B), discard on mismatch, `evidence_serialization_failure` | `test_hatp_signing_ceremony.py` TOCTOU discard | 18 |
| REQ-071 | `hatp_signing_ceremony.py` + `commands/hatp.py` — blind-touch preview, confirm before hardware call | `test_hatp_cli.py` preview-before-touch ordering test | — |
| REQ-072 | `hatp_signed_evidence.py` — constructor/parser domain equivalence (`__post_init__` shared with parser) | `test_hatp_signed_evidence.py` equivalence test | — |
| REQ-073 | `hatp_signed_evidence.py` — `@dataclass(frozen=True)` | `test_hatp_signed_evidence.py` | — |
| REQ-074 | Narrative (no touch to `pcae remote rollback approve`) | boundary test: `commands/agent.py` byte-unchanged | — |
| REQ-075 | Cross-cutting SC-1..12, see §7 | `test_hatp_*` (distributed) | — |
| REQ-076 | Cross-cutting, see §6 21-attack table | `test_phase_149o_12_hsce_attack_matrix.py` (or exact next-phase-ID suite) | 1–21 |
| REQ-077 | Narrative (contract versioning history) | — | — |
| REQ-078 | Narrative (requirement-count correction) | — | — |
| REQ-079 | Narrative (blocking-condition check) | — | — |

**79/79 mapped.** Every requirement has exactly one primary owner (module or "Narrative"); several also have a listed test owner and/or attack relationship as a secondary mapping.

## 6. 21-Attack Traceability Table

| # | Attack | Boundary attacked | Defense | Test level | Expected outcome | Test file |
|---|---|---|---|---|---|---|
| 1 | `evidence_id` with `../` or absolute path | Path construction | Pre-path-construction regex validator (REQ-056) | Unit | Rejected before filesystem access | `test_hatp_signed_evidence.py`, `test_hatp_evidence_store.py` |
| 2 | `evidence_id` uppercase hex | Case aliasing | Same validator, lowercase-only regex (REQ-056/059) | Unit | Rejected, no alias | `test_hatp_signed_evidence.py` |
| 3 | Byte-identical re-write, existing ID | Idempotent rewrite | Hard-link EEXIST → canonical byte-compare (REQ-052 step 6) | Integration, real fs | Idempotent success, no error | `test_hatp_evidence_store.py` |
| 4 | Byte-differing re-write, existing ID | Conflicting rewrite | Same, differing branch | Integration, real fs | `evidence_conflict`, winner unchanged | `test_hatp_evidence_store.py` |
| 5 | Duplicate JSON keys in envelope | Parser | `_reject_duplicate_keys` object_pairs_hook | Unit | Rejected at parse | `test_hatp_signed_evidence.py` |
| 6 | Unknown top-level field | Parser (closed schema) | Exact 4-field allowlist parse | Unit | Rejected, closed schema | `test_hatp_signed_evidence.py` |
| 7 | `evidence_version` as bool (`True`/`False`) | Constructor + parser | `isinstance(value, bool)` pre-check before `isinstance(value, int)` | Unit | Rejected, `unsupported_envelope_version` | `test_hatp_signed_evidence.py` |
| 8 | Missing required field | Parser | Closed schema, all 4 fields required | Unit | Rejected at parse | `test_hatp_signed_evidence.py` |
| 9 | `evidence_id` != `digest_hatp_proof_payload(proof)` | Parser/load validation | Digest recheck on load (REQ-062) | Unit | Rejected, `evidence_id_digest_mismatch` | `test_hatp_signed_evidence.py` |
| 10 | Corrupt/truncated `provider_assertion` bytes | Structural vs. cryptographic validity | Structural parse succeeds; `verify_hatp_proof` (future consumer) rejects | Unit (structural) + note (crypto is HATP-001's) | Parses structurally; never treated `VALID` by construction | `test_hatp_signed_evidence.py` |
| 11 | Provider-profile override attempt | CLI grammar / provider resolution | No `--provider` flag exists; production factory hardcoded | CLI negative test | Unreachable — argparse rejects unknown flag | `test_hatp_cli.py` |
| 12 | Wrong-operation replay | Proof binding | Reused `verify_hatp_proof` `WRONG_OPERATION` (future consumer, HATP-001-owned) | Note / non-regression | Caught at consumption, unaffected by this store | `test_hatp_signing_ceremony.py` (binding-only, not full replay) |
| 13 | `evidence_id` symlinked outside repo | Store write path | `os.path.islink(final_path)` pre-check before compare | Integration, real fs | Rejected, `evidence_persistence_failure` | `test_hatp_evidence_store.py` |
| 14 | `.pcae/hatp-evidence/` replaced by escaping symlink | Store root | Path-component symlink-escape check | Integration, real fs | Rejected, `evidence_persistence_failure` | `test_hatp_evidence_store.py` |
| 15 | Partial/interrupted write (process killed mid-write) | Publication atomicity | Temp file + fsync + close, then single atomic `os.link` | Fault-injected, real fs | No partial file ever visible at final path | `test_hatp_evidence_store.py` |
| 16 | Human cancels touch | Signing orchestrator | `HATPProviderCancelledError` → `human_signing_cancelled`, exit 5 | Unit (fake provider) | No evidence written | `test_hatp_signing_ceremony.py` |
| 17 | Hardware device absent | Provider resolution | `provider_unavailable`, exit 4, no fallback | Unit | Fails before any signing attempt | `test_hatp_signing_ceremony.py` |
| 18 | Post-preview Decision/Binding mutation before touch completes | TOCTOU | Post-sign recheck discards candidate (REQ-070) | Integration (mutate state between resolve calls) | No persistence, `evidence_serialization_failure` | `test_hatp_signing_ceremony.py` |
| 19 | No matching RAE Binding | Resolver | `binding_unavailable`, before hardware touch | Unit | Fails before provider call | `test_hatp_signing_ceremony.py` |
| 20 | `--per-id` with unresolvable `ecp_id` | AG5 resolution | `operation_not_found`, exit 2, before hardware touch | Unit | Fails before provider call | `test_hatp_signing_ceremony.py` |
| 21 | `--job-id` with unresolvable `original_commit_sha` (Obs-2, AG3 analogue) | AG3 resolution | `operation_not_found`, exit 2, before hardware touch | Unit | Fails before provider call | `test_hatp_signing_ceremony.py` |

**21/21 mapped**, all with concrete future test files.

Plus four **extra implementation attacks** (not Section-38-numbered, but mandated by this plan per governing-prompt §120-123 and Obs-3):

| Extra # | Attack | Defense | Test file |
|---|---|---|---|
| E1 | Loser comparison hits an unreadable/directory/special-file destination (Obs-3) | Pre-comparison object-type check; fail closed, map to `evidence_persistence_failure` (see §10.4 for rationale) | `test_hatp_evidence_store.py` |
| E2 | Temp writable fd mutation after `os.link` | Instrumented test confirms fd closed before `os.link`, no post-link write path exists | `test_hatp_evidence_store.py` |
| E3 | Many-writer race (not just 2 threads) | Real temp-dir concurrency test, N writers (identical and differing candidates), exactly one canonical final | `test_hatp_evidence_store.py` |
| E4 | Non-EEXIST `os.link` error (`EXDEV`, `EPERM`) | Fault-injected via monkeypatch; fails closed, `evidence_persistence_failure`, no fallback to `os.replace` | `test_hatp_evidence_store.py` |

## 7. SC-1..SC-12 Test Mapping

| SC | Invariant | Test plan |
|---|---|---|
| SC-1 | Only operation locator is human-selected | `test_hatp_cli.py`: forbidden-flags inventory covers every other field name |
| SC-2 | Governed fields always derived, never caller input | `test_hatp_signing_ceremony.py`: field-source-table assertions (mirrors REQ-018) |
| SC-3 | Provider always production-resolved | `test_hatp_cli.py`/`test_hatp_signing_ceremony.py`: no test-provider reachable from CLI path |
| SC-4 | Human presence always provider-derived | Code-path test: no boolean parameter exists on any public signing function |
| SC-5 | `evidence_id` derives only from canonical proof payload | `test_hatp_signed_evidence.py`: vary `provider_assertion`, confirm `evidence_id` unchanged |
| SC-6 | Lookup always explicit-ID-only | `test_hatp_evidence_store.py`: API-surface test, no `list`/`latest` public function |
| SC-7 | No silent overwrite | `test_hatp_evidence_store.py`: real hard-link race suite (attacks 3, 4, 15, E3) |
| SC-8 | Corruption/missing never falls back to legacy `rollback_approval_state` | `test_hatp_evidence_store.py`: load failure paths never touch `rollback_approval_evidence.py` state |
| SC-9 | File existence alone never treated as approval | `test_hatp_evidence_store.py`: forbidden-pattern test (no `exists()`-only approval helper in public API) |
| SC-10 | Signing success never PB permission or execution | `test_hatp_cli.py`: output-schema negative test (§6, REQ-066) |
| SC-11 | Secrets never in evidence/log/argv | `test_hatp_signing_ceremony.py` + `test_hatp_cli.py`: secret-absence scan of all persisted/logged artifacts |
| SC-12 | Consumption always re-verifies, never cached | `test_hatp_evidence_store.py`: loader returns parsed envelope only, no `verified`/`approved` field anywhere in the model |

**12/12 mapped.**

## 8. Error Vocabulary and Exit-Code Mapping (reaffirmed, closed, plus Obs-3 resolution)

The 12-member `error_type` vocabulary and 9-value exit-code set are frozen by HSCE-REQ-046/047/048 (§22) and are reproduced verbatim below — this plan introduces no new contract vocabulary member.

| `error_type` | Exit | Owner module |
|---|---|---|
| `repository_identity_unavailable` | 3 | `hatp_signing_ceremony.py` |
| `operation_not_found` | 2 | `hatp_signing_ceremony.py` |
| `decision_unavailable` | 3 | `hatp_signing_ceremony.py` |
| `binding_unavailable` | 3 | `hatp_signing_ceremony.py` |
| `no_authorized_signer` | 4 | `hatp_signing_ceremony.py` |
| `provider_unavailable` | 4 | `hatp_signing_ceremony.py` |
| `hardware_device_fault` | 6 | `hatp_signing_ceremony.py` |
| `human_signing_cancelled` | 5 | `hatp_signing_ceremony.py` |
| `provider_signature_failure` | 6 | `hatp_signing_ceremony.py` |
| `evidence_serialization_failure` | 1 | `hatp_signing_ceremony.py` (TOCTOU discard), `hatp_signed_evidence.py` (construction failure) |
| `evidence_conflict` | 7 | `hatp_evidence_store.py` |
| `evidence_persistence_failure` | 8 | `hatp_evidence_store.py` |

`commands/hatp.py` owns the single centralized `error_type → exit_code` mapping function (mirroring `decision_session.py::_EXIT_CODE_BY_ERROR_TYPE`) — no handler-specific deviation.

**Obs-3 resolution (loser-comparison read failure — destination unreadable, or occupied by a directory/special file):** this plan selects **`evidence_persistence_failure`** (exit 8). Rationale: HSCE-REQ-052 step 7 already establishes `evidence_persistence_failure` as the fail-closed default for "any `OSError` other than `FileExistsError`" during the publication attempt itself; a loser-comparison read failure is the structurally closest analogue — a filesystem-layer operation that cannot be completed safely, not a determination that two *readable* candidate byte-sequences differ (which is what `evidence_conflict` specifically means, per REQ-039(B) and REQ-038). Treating an unreadable/directory/special-file destination as `evidence_conflict` would misrepresent "I could not safely compare" as "I compared and they differ," which is a weaker, less accurate signal. This is documented here as an **implementation-level diagnostic mapping**, not an HSCE-001 amendment (no `error_type` outside the closed 12-member table is introduced; the mapping *selects among* existing members). `evidence_not_found` (REQ-064, load-path only) is reserved exclusively for missing-file lookups and is never used on the publish path.

Additionally, `evidence_not_found` (referenced by REQ-064 for the load/consumption path, not present as a row in the REQ-047 write-path table) is owned by `hatp_evidence_store.py::load()` only — this plan does not attempt to reconcile the contract's own internal 12-vs-13 naming tension; it is reported and used exactly as the contract text describes it (a load-path-only category distinct from the write-path's 12-member table).

## 9. Envelope Model Plan — `hatp_signed_evidence.py`

```python
@dataclass(frozen=True)
class HATPSignedEvidenceEnvelope:
    evidence_version: int
    evidence_id: str
    proof: HumanApprovalProvenanceProof
    provider_assertion: bytes   # decoded; base64 only at the JSON boundary

    def __post_init__(self) -> None:
        _validate_envelope_fields(self.evidence_version, self.evidence_id, self.proof, self.provider_assertion)
```

- **Constructor/parser equivalence (REQ-072):** `_validate_envelope_fields(...)` is the single shared validation function called both from `__post_init__` and from the parser's document-to-model step. No separate, weaker validation path exists in either direction.
- **Version validation (REQ-033):** `isinstance(evidence_version, bool)` rejected explicitly before `isinstance(evidence_version, int)` is trusted; only `1` accepted — identical pattern to `_require_proof_version`.
- **`evidence_id` validation (REQ-056/059):** one shared `_validate_evidence_id(value: str) -> str` function (module-level, exported for `hatp_evidence_store.py` to reuse for its own path-construction guard) — regex `^[0-9a-f]{64}$`, no `.lower()` normalization, no `.strip()`, rejects before any path use.
- **`proof` field:** stored as the parsed `HumanApprovalProvenanceProof` object (not a raw dict) — reuses `parse_hatp_proof`/`hatp_proof_to_document` from `human_approval_trusted_provenance.py` for the nested boundary; the envelope parser never re-implements proof-field validation.
- **`provider_assertion` (REQ-034/035):** stored on the model as decoded `bytes`; Base64 encode/decode happens only at the JSON serialize/parse boundary (`base64.b64encode`/`base64.b64decode`, standard library, strict mode — invalid Base64 padding/characters raise `binascii.Error`, mapped to `evidence_serialization_failure` on construction or to a parse rejection on load).
- **Evidence-ID computation (REQ-036):** the builder function `build_hatp_signed_evidence_envelope(proof, provider_assertion_bytes) -> HATPSignedEvidenceEnvelope` **derives** `evidence_id = digest_hatp_proof_payload(proof)` internally — it does not accept an externally supplied `evidence_id` at all (no independent-value acceptance path in the production builder, per the governing prompt's §16 preference). The typed constructor still accepts an explicit `evidence_id` argument (needed for the parser's use, which must recompute-and-compare rather than blindly trust), but the *production builder* used exclusively by `hatp_signing_ceremony.py` is the only call site and always derives it.
- **Parser digest recheck (REQ-062):** `parse_hatp_signed_evidence(raw: bytes) -> HATPSignedEvidenceEnvelope` parses the closed 4-field schema via a module-local `_reject_duplicate_keys` + `json.loads(object_pairs_hook=...)` (matching HATP's own module-local convention, not `pcae.schema_runtime.json_parser`, to keep this module's dependency graph independent, mirroring `hatp_bootstrap.py`'s and `human_approval_trusted_provenance.py`'s own stated duplication discipline), then recomputes `digest_hatp_proof_payload(parsed_proof)` and compares against the document's own `evidence_id` field — mismatch raises a structured error mapped to `evidence_id_digest_mismatch` by the caller.
- **Canonical serialization (REQ-053):** `serialize_hatp_signed_evidence(envelope) -> bytes` — the **one** function all of winner-write, loser-byte-comparison, and idempotency checks use. `json.dumps(document, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")`, where `document` nests `hatp_proof_to_document(proof)` unchanged and `provider_assertion` as its Base64 string form. (The contract's REQ-053 text does not specify compact separators the way `canonicalize_hatp_proof_payload` does — this plan does not invent one; standard `json.dumps` default separators are used, since REQ-053 lists exactly four properties and no fifth.) No second JSON encoder exists anywhere in this module or `hatp_evidence_store.py`.
- **Immutability (REQ-040/073):** `frozen=True` dataclass; because `evidence_id` is a pure function of `proof`, any `proof` mutation is impossible post-construction (frozen) and would in any case yield a different `evidence_id`/different file, never an in-place edit.

## 10. Evidence Store Plan — `hatp_evidence_store.py`

### 10.1 Store type and root

```python
class HATPEvidenceStore:
    def __init__(self, repository_root: HarnessPath) -> None: ...
    def path_for(self, evidence_id: str) -> Path: ...
    def load(self, evidence_id: str) -> HATPSignedEvidenceEnvelope: ...
    def publish(self, envelope: HATPSignedEvidenceEnvelope) -> HATPEvidencePublicationResult: ...
```

Constructor accepts an explicit `repository_root` (mirroring `RollbackApprovalEvidenceStore`'s own explicit-root convention) rather than deriving it implicitly from CWD — `hatp_signing_ceremony.py`/`commands/hatp.py` are responsible for resolving that root once (`HarnessPath.cwd()`) and passing it in, so the store itself never reads CWD directly (REQ-041). Root: `<repository_root>/.pcae/hatp-evidence/envelopes/`. Unlike the protected HATP trust-store/hardware-credential roots (which are fixed, OS-level, ownership-checked paths), this store is **intentionally untrusted, repository-local, and agent-writable** (REQ-060) — no admin-root permission checks are applied to it; only the path-traversal/symlink protections in §10.3 apply.

### 10.2 Public API (REQ-043/044/061)

- `load(evidence_id: str) -> HATPSignedEvidenceEnvelope` — raises a structured not-found/corrupt error; never returns a bare boolean.
- `publish(envelope: HATPSignedEvidenceEnvelope) -> HATPEvidencePublicationResult` — `HATPEvidencePublicationResult(evidence_id: str, path: Path, idempotent: bool)`.
- `path_for(evidence_id: str) -> Path` — pure path computation, includes `_validate_evidence_id` call, no I/O.

No `exists()`, `latest()`, `list_latest()`, `overwrite()`, `update()`, `delete_authority()`, or `approve()` method exists on this class, by design (REQ-043, REQ-061, SC-6, SC-9).

### 10.3 Path validation / symlink protections (REQ-056/057/058)

Before any path is constructed: `evidence_id` passes `_validate_evidence_id` (shared with `hatp_signed_evidence.py`, §9). Before writing: `os.path.islink(final_path)` checked explicitly (REQ-057). Before any directory is used: each path component of `.pcae/hatp-evidence/envelopes/` relative to `repository_root` is checked for a symlink that would escape `repository_root` (REQ-058) — implemented via `Path.resolve()` comparison against the resolved repository root, rejecting if the resolved store path is not a descendant of the resolved repository root.

### 10.4 Exclusive hard-link publication algorithm (REQ-052 — the central algorithm)

`publish()` implements the contract's repaired HSCE-REQ-052 exactly, as a dedicated helper (not a call into `rollback_approval_evidence.py::_write_atomic_json`, which lacks the symlink checks and uses `os.replace`):

1. Validate `evidence_id` (§10.3); compute `final_path = envelopes_dir / f"{evidence_id}.json"`.
2. Compute canonical bytes: `candidate_bytes = serialize_hatp_signed_evidence(envelope)` (§9, REQ-053) — the *only* serializer used anywhere in this algorithm.
3. `mkdir(envelopes_dir, parents=True, exist_ok=True)` (REQ-055) — first-publish-only side effect; `load()`/`path_for()` never create directories.
4. Create a uniquely-named temp file **in the same `envelopes/` directory** via `tempfile.mkstemp(dir=envelopes_dir, prefix=f".{evidence_id}.", suffix=".tmp")` (collision-safe, `O_EXCL`-backed by the stdlib primitive — no guessed/predictable filename, no following an attacker-controlled temp symlink).
5. Write the complete `candidate_bytes` to the temp fd, `os.fsync(fd)`, then `os.close(fd)` — **no writable file descriptor referencing the temp inode survives past this line** (the post-link-FD-safety invariant, tested explicitly per governing-prompt §121/§24).
6. `os.path.islink(final_path)` check (REQ-057) — if true, unlink the temp file and fail `evidence_persistence_failure` immediately, without attempting `os.link`.
7. Attempt `os.link(temp_path, final_path)`.
8. **Success** → this writer is the exclusive-publication winner; unlink `temp_path` (best-effort, failure non-authoritative); return `idempotent=False`.
9. **`FileExistsError`** → this writer lost the race. Before reading: re-check `os.path.islink(final_path)` (a symlink could have appeared between steps 6 and 7 in a hostile-but-unlikely window) — if now a symlink, fail `evidence_persistence_failure`, do not read through it. Otherwise, validate the existing final object's type (§10.5) before reading; if it fails that validation, fail `evidence_persistence_failure` (Obs-3 mapping, §8). Otherwise read `existing_bytes` and compare to `candidate_bytes`: identical → unlink temp, return `idempotent=True`, no error; different → unlink temp, raise `evidence_conflict`.
10. **Any other `OSError`** (`EXDEV`, `EPERM`, unsupported-hard-link filesystem, etc.) → unlink temp (best-effort), fail closed as `evidence_persistence_failure`. **No fallback to `os.replace` or any other overwrite-capable primitive, ever, under any condition.**
11. `finally`: temp file unlink is attempted in every exit path; a failure to unlink is logged but never raised/authoritative.

No write occurs after step 5's `os.close(fd)`. This is a testable implementation invariant (extra attack E2, §6).

### 10.5 Existing-final-object type validation (Obs-3, extra attacks E1)

Before comparing bytes in step 9, the existing `final_path` object is validated as: a regular file (`stat.S_ISREG`), not a symlink (already checked), and its resolved path stays within the canonical store directory. If it is a directory, FIFO, socket, device file, or otherwise unreadable/non-regular object, `publish()` fails closed with `evidence_persistence_failure` (§8) — **no unlink, no replace, no fallback**, regardless of diagnostic category (SC-7 holds unconditionally).

### 10.6 EEXIST is not itself conflict

REQ-052 step 6/9 above never treats `FileExistsError` alone as `evidence_conflict` — only a completed, safe, byte-for-byte comparison against readable canonical bytes decides idempotent-success vs. conflict; every other EEXIST sub-case (symlink, non-regular object, unreadable) fails closed as `evidence_persistence_failure` instead.

## 11. Proof Context Resolver / AG3 / AG5 Resolution Plan — `hatp_signing_ceremony.py`

### 11.1 `HATPRollbackSigningContext` (internal, immutable)

```python
@dataclass(frozen=True)
class HATPRollbackSigningContext:
    rollback_site: RollbackSite
    operation_reference: Union[Ag3OperationReference, Ag5OperationReference]
    binding: RollbackApprovalBinding
    decision_record_id: str
    decision_record_digest: str
    repository_id: str
```

Minimal form: holds canonical *source* identifiers (Binding/Decision IDs and digests, operation reference, repository ID) rather than duplicating proof shape — `proof` itself is built from this context plus signer/provider resolution, not stored redundantly inside the context.

### 11.2 `resolve_signing_context(root, *, site, job_id=None, per_id=None) -> HATPRollbackSigningContext`

- **AG3** (REQ-013): given `job_id`, reads the live job record (same record `execute_rollback` already reads) for `original_commit_sha`. Missing job or unresolvable `original_commit_sha` → `operation_not_found` (attack 21), before any Binding lookup.
- **AG5** (REQ-016): given `per_id`, reads the live `PromotionExecutionRecord` for `ecp_id`. Missing/unresolvable `ecp_id` → `operation_not_found` (attack 20), before any Binding lookup.
- **Binding/Decision lookup (REQ-020/021):** `RollbackApprovalEvidenceStore.list_bindings_with_keys()`, filtered by structural match on `rollback_site` + operation locator, applying the store's own supersession discipline (never "pick the newest" across distinct operations). Zero matches, multiple ambiguous matches, or malformed/revoked state → `binding_unavailable`. Decision resolved from the matched Binding's `governance_record_reference`; missing/unresolvable → `decision_unavailable`.
- **Repository ID (REQ-041's cross-reference via §9's table):** `repository_identity.read_repository_identity(root)`; missing → `repository_identity_unavailable`.
- No hardware provider call occurs anywhere in this function (REQ-021/025 — "no hardware touch before all canonical context resolves").

### 11.3 TOCTOU strategy (REQ-069/070, §12.5)

`resolve_signing_context` is called **twice**: once to produce context A (shown in preview, §12.4) and once, after the hardware touch, to produce context B. The orchestrator compares the contract-required stable fields (Binding id/state, Decision id/digest, operation reference) between A and B; any difference discards the signed candidate.

## 12. Signing Ceremony Orchestration Plan — `hatp_signing_ceremony.py`

### 12.1 Public entry point

```python
def sign_rollback_evidence(
    root: HarnessPath,
    *,
    site: RollbackSite,
    job_id: Optional[str] = None,
    per_id: Optional[str] = None,
    clock: Callable[[], datetime] = _default_clock,     # test seam, production default
    provider_factory: Callable[[], HATPHardwareSigner] = _default_provider_factory,  # test seam
    trust_store_factory: Callable[[], HATPTrustStore] = _default_trust_store_factory,  # test seam
    confirm: Callable[[HATPSigningPreview], bool] = _default_cli_confirm,  # test seam
) -> HATPSigningResult:
```

**Test-seam layering (REQ-091 discipline):** the keyword-only factory/clock/confirm parameters default to production implementations (`HarnessPath.cwd()`-rooted trust store, `create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)`, real UTC clock, real interactive confirm). `commands/hatp.py`'s CLI handler calls this function with **no overrides** — it never exposes these parameters as CLI flags (REQ-017/022/023/026). Only `tests/test_hatp_signing_ceremony.py` supplies deterministic fakes directly to this core function. This function itself is not part of the public CLI surface; it is an internal core API, so accepting test-injectable parameters here does not create a production authority-bearing adapter.

### 12.2 Provider/signer resolution (REQ-022/023/024)

`provider = provider_factory()` (production default: `create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)`); `trust_store = trust_store_factory()` (production default: `HATPTrustStore.production()`). Signer identity resolved from the provider's own credential exchange, then cross-checked against `trust_store.lookup_signer(...)` — a credential absent from the trust store's authorized-approver mapping fails `no_authorized_signer` (REQ-024), before any signature request.

### 12.3 Substrate readiness (REQ-025)

`inspect_hatp_verification_substrate_readiness` is **not called** as a precondition anywhere in this function. It MAY be called purely for informational preview display (REQ-025 permits signing to proceed regardless) — this plan defers that display decision to the CLI layer (§13) since it does not change signing preconditions; if displayed, it is clearly informational and never gates the hardware call.

### 12.4 Preview-before-touch (REQ-071, "blind-touch defense")

After context A resolves and before any provider call, `commands/hatp.py` renders every field from the REQ-018 field-source table (repository_id, decision_record_id/digest, binding_id/digest, rollback_site, operation_reference, provider_profile) and requires explicit confirmation (`confirm(preview) -> bool`). `--json` changes the output *encoding* of the preview and result only — it does not skip confirmation or turn signing into unattended mode (REQ-071's own text, plus governing-prompt §128).

### 12.5 Hardware invocation and issued_at (REQ-018/027/068)

`issued_at` generated once, internally, via the reused `_canonical_timestamp_string`-equivalent convention from `human_approval_trusted_provenance.py` (millisecond-precision UTC) — never `datetime.now()` called ad hoc, never a caller-supplied value in production (the `clock` parameter's production default is the only call site). Python 3.9 compatibility: this plan reuses the existing, already-3.9-validated generation function rather than any `datetime.fromisoformat` lexical-extension-dependent code path (governing-prompt §50).

`proof = HumanApprovalProvenanceProof(proof_version=1, principal_id=..., signer_key_id=..., provider_profile=HATP_HARDWARE_PROVIDER_V1, repository_id=context.repository_id, decision_record_id=context.decision_record_id, decision_record_digest=context.decision_record_digest, binding_id=context.binding.evidence_id, binding_digest=context.binding.content_digest, rollback_site=site, operation_reference=context.operation_reference, issued_at=issued_at)`.

`assertion = provider.request_signature(canonicalize_hatp_proof_payload(proof), signer_key_id=..., provider_profile=HATP_HARDWARE_PROVIDER_V1)` — the exact existing Wave-3 canonicalizer, Wave-5 API; no new canonicalizer introduced (REQ-027, governing-prompt §48). `HATPProviderCancelledError` → `human_signing_cancelled`; `HATPProviderDeviceError` → `hardware_device_fault`; `HATPProviderUnavailableError` (if raised at call time rather than at factory time) → `provider_unavailable`.

### 12.6 TOCTOU recheck and persistence order (REQ-069/070, §11.3)

After a successful hardware touch, before building the envelope: `context_b = resolve_signing_context(root, site=site, job_id=job_id, per_id=per_id)`. Compare `context_a` vs `context_b` on Binding id/state, Decision id/digest, operation reference. Mismatch → discard the signed `assertion`, persist nothing, fail `evidence_serialization_failure` (REQ-070). Match → `envelope = build_hatp_signed_evidence_envelope(proof, assertion.evidence)` (§9) → `store.publish(envelope)` (§10). No automatic re-sign on mismatch (governing-prompt §56) — a changed context requires a fresh ceremony invocation by the human.

### 12.7 Signer revocation during ceremony (REQ-024, governing-prompt §55)

HSCE-001 requires only the initial signer-authorization check (§12.2); it does not require a second pre-publish trust recheck. This plan does not add one — HATP-001's own mandatory consumption-time re-verification (§21-22) remains the authoritative signer-trust boundary regardless of ceremony-time state, exactly as REQ-025/SC-12 already establish. Documented here as a deliberate no-hidden-cache decision, not an oversight.

## 13. CLI Plan — `commands/hatp.py` + `cli.py`

### 13.1 Grammar (REQ-009/010/011/013/016)

```
pcae hatp sign rollback --site {ag3|ag5} (--job-id <id> | --per-id <id>) [--json]
```

`cli.py` registers a new `hatp` subparser with a `sign` sub-subparser and a `rollback` sub-sub-subparser (mirroring existing multi-level command families such as `remote rollback approve/deny/execute`), `--site` via `choices=["ag3","ag5"]`, `--job-id`/`--per-id` mutually exclusive at the argparse level where possible, cross-validated in the handler (`--site ag3` requires `--job-id` and forbids `--per-id`, and vice versa) since argparse's own mutual-exclusion groups cannot express "exactly one of A or B is required, and which one is valid depends on a third flag's value" directly.

### 13.2 Forbidden-flag inventory (REQ-017/022/023/024/026, exhaustively tested)

`--provider`, `--signer`, `--force`, `--overwrite`, `--output`, `--repository-id`, `--decision-digest`, `--binding-digest`, `--signer-key-id`, `--ecp-id`, `--dry-run`, `--hatp-trust-store`, `--trusted-key`, `--ignore-not-ready`, `--dev`, `--software-provider`. `test_hatp_cli.py` asserts every one of these raises an argparse error.

### 13.3 Handler (`run_hatp_sign_rollback(args) -> int`)

Mirrors `run_rollback`'s existing pattern: `root = HarnessPath.cwd()`; `result = sign_rollback_evidence(root, site=RollbackSite(args.site), job_id=args.job_id, per_id=args.per_id)` (no test-seam parameters passed — production defaults only); catch the closed set of signing exceptions, map via the centralized `error_type → exit_code` table (§8); print human or `--json` output (§13.4); return the exit code.

### 13.4 Output (REQ-065/066)

Success: `{"evidence_id": ..., "path": ...}` (or human-readable equivalent) — no `approved`, `permission`, or `executed` field anywhere in the schema. Error: `{"error_type": ..., "message": ...}` with no traceback by default; internal diagnostics logged separately, never surfaced as authority fields (REQ-051).

### 13.5 Optional-dependency boundary (REQ-028, governing-prompt §72-76)

`commands/hatp.py` and `hatp_signing_ceremony.py` never import `hatp_fido2_provider` directly — they call `hatp_providers.create_production_hardware_provider(...)`, which already performs the lazy `try/except ImportError` boundary. `pcae hatp --help` and `pcae hatp sign rollback --help` MUST succeed with `fido2` uninstalled (tested explicitly, §15). No hardware discovery occurs at import time or at `--help` time — only when `sign_rollback_evidence` actually reaches provider resolution (§12.2).

### 13.6 Secret handling (REQ-050)

No `--pin` flag. No secret ever appears in `args`, in logged output, or in the persisted envelope. PIN entry, if the provider requires it, is collected exclusively through the provider's own out-of-band FIDO2/CTAP2 mechanism — `commands/hatp.py` never reads stdin for a secret.

## 14. Test Seam Architecture

Layering (§12.1): production CLI handler (`commands/hatp.py`) → core orchestrator (`hatp_signing_ceremony.py::sign_rollback_evidence`, keyword-only test-injectable parameters defaulting to production factories) → individual resolvers/store (deterministic, plain function/class parameters, freely testable in isolation). The CLI handler is the only caller that must use zero overrides — this is enforced by a dedicated test (`test_hatp_cli.py`) asserting `run_hatp_sign_rollback`'s source never passes non-default keyword arguments to `sign_rollback_evidence`. This mirrors the 149O-family's own F-2 lesson: a production public adapter must never expose a caller-selectable trusted-dependency override.

## 15. Test Suite Plan

| File | Covers |
|---|---|
| `tests/test_hatp_signed_evidence.py` | Constructor/parser equivalence, version bool-rejection, closed schema, Base64 round-trip, digest binding, canonical serialization bytes, evidence-ID validator (attacks 1,2,5,6,7,8,9,10) |
| `tests/test_hatp_evidence_store.py` | Path validation, `load`, `publish`, real hard-link race (2/8/32+ writers, identical/differing), idempotency, conflict, symlink (destination + root-escaping), missing/corrupt load, partial-write/fault-injection, unsupported-link-error, temp-file cleanup, post-link-FD-safety instrumentation, Obs-3 object-type checks (attacks 3,4,13,14,15,E1,E2,E3,E4) |
| `tests/test_hatp_signing_ceremony.py` | AG3/AG5 resolution, preview content, provider call (fake), cancellation, device absence, TOCTOU discard, proof-field-source table, no-touch-on-precondition-failure, no-persistence-on-failure (attacks 16,17,18,19,20,21) |
| `tests/test_hatp_cli.py` | Exact grammar, `--help` with fido2 absent, JSON/text output, exit codes, forbidden flags, optional-dependency boundary, no-hardware-probe-at-import, zero-override production-path assertion (attacks 11) |
| `tests/test_phase_149o_12_hsce_attack_matrix.py` (exact name pinned to whichever phase ID actually implements this plan) | End-to-end deterministic assertion of all 21 mandatory attacks plus E1-E4 against the fully assembled implementation |

**Real-hardware test strategy (governing-prompt §90):** all of the above use `TestHATPProofVerifierProvider`-equivalent deterministic fakes injected only at the core-function test seam (§14) — never a software fallback reachable from production. An optional, explicitly hardware-required test marker (e.g. `@pytest.mark.hardware_required`, skipped by default) MAY be added for genuine FIDO2 device integration; if real hardware is absent, it is skipped deterministically and reported as skipped, never fabricated as passing. The production factory never resolves a test provider under any condition.

**Filesystem/concurrency test seam (governing-prompt §93):** store tests use real temporary directories and real `os.link` calls — `os.link` itself is never mocked away, since the race-safety guarantee is a real-filesystem property, not a mockable abstraction. Fault-injection tests (E4, non-EEXIST errors) monkeypatch `os.link` itself at the call site only for that specific negative test, not for the positive-path suite.

**Python/OS compatibility (governing-prompt §50, §132-134):** all timestamp generation reuses the already-3.9-compatible convention (§12.5); `os.link` is available and behaves identically on both supported platforms (macOS/APFS, Linux/ext4-equivalent) per HSCE-REQ-052's own platform-scope statement — no Windows-specific semantics are defined, matching the contract's existing scope. If the evidence store's filesystem does not support hard links, `publish()` fails closed as `evidence_persistence_failure` (§10.4 step 10) — no race-weaker fallback is implemented (governing-prompt §134).

## 16. Production File Allowlist

| File | Change | Requirements owned |
|---|---|---|
| `src/pcae/core/hatp_signed_evidence.py` | NEW | REQ-031–040, 053, 056, 059, 062–064, 072–073 |
| `src/pcae/core/hatp_evidence_store.py` | NEW | REQ-007, 041–045, 052, 054–055, 057–058, 060–061, 064 |
| `src/pcae/core/hatp_signing_ceremony.py` | NEW | REQ-013, 016, 018–030, 049–051, 067–071 |
| `src/pcae/commands/hatp.py` | NEW | REQ-009–012, 017, 046–047, 065–066, 071 |
| `src/pcae/cli.py` | MODIFY (registration only) | REQ-009–010, 017, 026 |

Every future implementation hunk classifies as one of: `EVIDENCE_MODEL`, `EVIDENCE_PARSER`, `EVIDENCE_SERIALIZER`, `EVIDENCE_STORE`, `EXCLUSIVE_PUBLICATION`, `PROOF_CONTEXT_RESOLUTION`, `SIGNING_ORCHESTRATION`, `TOCTOU_RECHECK`, `ERROR_MAPPING`, `CLI_REGISTRATION`, `CLI_HANDLER`, `OPTIONAL_DEPENDENCY_BOUNDARY`, `UNRELATED`. Expected `UNRELATED = 0`. The implementation phase's own boundary test SHOULD assert the production diff's file set is exactly the five rows above (a semantic allowlist test keyed on this table, not a brittle whole-repo-text assumption — per the retained 149O.5-F-3 lesson, §17).

## 17. Implementation Wave Decomposition and Order

Section-5 decomposition adopted as proposed, with justification:

1. **Wave A — Evidence envelope model + parser/serializer** (`hatp_signed_evidence.py`). No dependency on store or ceremony; fully unit-testable in isolation.
2. **Wave B — Evidence store + atomic exclusive publication** (`hatp_evidence_store.py`). Depends only on Wave A's serializer.
3. **Wave C — Proof-context resolver** (`hatp_signing_ceremony.py`, resolver half only). Depends on existing RAE/CHGR/repository-identity APIs, not on Waves A/B.
4. **Wave D — Signing-ceremony orchestration** (`hatp_signing_ceremony.py`, orchestrator half). Depends on A, B, C.
5. **Wave E — CLI command + output/error mapping** (`commands/hatp.py`, `cli.py`). Depends on D.
6. **Wave F — Integrated deterministic tests / regressions.** Depends on all prior waves.

This order is dependency-correct (each wave depends only on strictly earlier waves) and avoids starting with the CLI (governing-prompt §135's explicit warning).

**Commit/phase boundary decision (§136):** given the scope (three new core modules, a race-safety-critical algorithm, a new CLI surface, ~80 requirements, 21+4 attacks), this plan recommends **splitting the implementation across three bounded phases**, each independently reportable, rather than one monolithic implementation phase:

- **149O.12A — Signed Evidence Model + Evidence Store Implementation** (Waves A + B, plus `test_hatp_signed_evidence.py` + `test_hatp_evidence_store.py`).
- **149O.12B — Signing Ceremony Resolver + Orchestrator Implementation** (Waves C + D, plus `test_hatp_signing_ceremony.py`).
- **149O.12C — Signing CLI Integration** (Wave E + Wave F, plus `test_hatp_cli.py` and the full attack-matrix suite).

Each sub-phase produces no partial/broken production surface (149O.12A alone is inert — no CLI reaches it; 149O.12B alone is inert — nothing calls it without 149O.12C's CLI). A single, separate **independent-verification phase** (149O.13, per §18) follows completion of 149O.12C, before any AG3/AG5 consumption wiring (149O.14+, explicitly out of scope here) is even proposed.

## 18. Independent Verification Plan (reserved, future phase — not this phase)

A separate phase, **149O.13 — HATP Signing Ceremony + Evidence Store Implementation Independent Verification**, MUST run after 149O.12C completes, before HATP production readiness is reconsidered. It must independently exercise, at minimum: all 21 mandatory HSCE attacks, the 4 extra implementation attacks (E1-E4), the Obs-3 error-mapping choice (§8) for contract-consistency, hard-link writable-FD-mutation absence, many-writer races, optional-dependency (`fido2`-absent) behavior, TOCTOU discard, no-legacy-mutation (RAE `rollback_approval_state` untouched by signing), and no-authority-conflation (signing success never expressed as approval/permission/execution anywhere in output or logs). No production implementation phase self-certifies.

## 19. Stop Conditions (governing-prompt §137, retained verbatim as this plan's own)

Future implementation MUST STOP and return to architecture/contract reconsideration, rather than improvise, if any of: HSCE requirement text requires reinterpretation; hard-link publication cannot be made race-safe on the target filesystem; canonical serialization ambiguity appears; existing CHGR/RAE APIs cannot uniquely derive a required field; production signer/provider resolution requires caller authority; AG3/AG5 operation context cannot be deterministically derived; TOCTOU comparison cannot be implemented without modifying the HATP proof schema; new error vocabulary becomes necessary; the optional hardware dependency breaks ordinary PCAE imports; production CLI requires a software/test-provider fallback.

## 20. Regression Plan / Fast Green

Entering baseline (149O.10.2): **4590 passed, 2 skipped, 0 failed.** Implementation phases (149O.12A/B/C) should run, at minimum: the new model/store/ceremony/CLI suites; the phase-specific attack-matrix suite; 149O.9/149O.10/149O.10.1/149O.10.2 contract-verification suites (non-regression); Wave-3 proof tests, Wave-4 verifier tests, Wave-5 provider tests (where the `fido2` extra is available); Wave-6 gated-RAE tests, Wave-7 authority/readiness tests; Fast Green baseline; report-trust suite; a bounded rollback/Permission-Broker regression sweep (no PB behavior change is expected, so this is a non-regression check, not a feature test). The new deterministic model/store/CLI suites (not the optional hardware-required marker) are strong candidates to join Fast Green, given their real-but-fast filesystem-only I/O profile; the hardware-required marker must remain excluded/skipped deterministically from Fast Green.

## 21. Retained Findings (carried forward, fully qualified, no bare IDs)

- `149O.10-F-1` (editorial requirement-count correction): INDEPENDENTLY CONFIRMED CLOSED. No action this phase.
- `149O.10-F-2` (HSCE-REQ-052 literal-reuse wording precision): INDEPENDENTLY CONFIRMED CLOSED. This plan's §10.4 explicitly avoids literal reuse of `_write_atomic_json`, consistent with the repair.
- `149O.10-F-3` (BLOCKING, no-clobber race): INDEPENDENTLY CONFIRMED CLOSED at contract level and independently re-verified (149O.10.2). This plan's §10.4 implements the repaired algorithm exactly as specified.
- `149O.10-Obs-2` (AG3 attack-matrix gap): INDEPENDENTLY CONFIRMED CLOSED (attack 21 mapped, §6).
- `149O.10.2-Obs-3` (loser-comparison read-failure `error_type` gap): resolved in this plan's design (§8, §10.5) as `evidence_persistence_failure`, with rationale — an implementation-level diagnostic mapping, not a contract amendment. Not yet "closed" in the sense of a verified implementation; that verification is reserved for 149O.13.
- `149O.10.2-Obs-4` (report-count discrepancy, 89 vs. reproducible 29): retained as a documentation observation only. This plan does not cite the stale 89 figure anywhere; §20's baseline figures are taken from 149O.10.2's own independently reproduced counts.
- `149O.5-F-3` (historical stale-boundary-test debt, distinct from `149O.10-F-3`): retained separately; §16's production-diff test is deliberately designed as a semantic file-set allowlist rather than a brittle frozen-source-text assumption, so that this implementation's intentional addition of a new HATP CLI consumer does not itself trip a stale "zero HATP CLI consumers" assumption elsewhere in the test suite. Any existing test asserting that should be updated to reference this table, not deleted.

## 22. Plan Completeness Check

- [x] 79/79 HSCE requirements mapped (§5).
- [x] 21/21 mandatory attacks mapped, plus 4 extra implementation attacks (§6).
- [x] All 12 SC-1..SC-12 invariants mapped to a future test (§7).
- [x] All 12 `error_type` values have an implementation owner (§8).
- [x] All 9 exit-code categories have a CLI owner (§8, §13.3).
- [x] Every proposed production file has requirements (§16).
- [x] No implementation TBD remains for an authority-sensitive question (§10.4's Obs-3 gap is resolved with documented rationale, not left open; §12.7's signer-revocation question is explicitly answered as "no additional check, HATP-001 consumption-time re-verification remains authoritative").
- [x] No production source modified this phase (confirmed, §23).

## 23. Confirmations

No production source was modified. HSCE-001 v1.1 remained byte-unchanged. HATP-001 v1.0 remained byte-unchanged. RAE-001 v1.0 remained byte-unchanged. No CLI implementation was added. No evidence-store implementation was added. No `.pcae/hatp-evidence/` production directory was created. No hardware signing occurred. No rollback dispatch behavior changed. No Permission Broker behavior changed. No Class-B host provisioning occurred. No production HATP activation occurred. `149O.10-F-3` remains independently confirmed closed. Signing remains distinct from verification, approval, permission, capability, and execution throughout this plan. `B-149O-1..4` remain independently verified at the HATP-gated authority boundary with system execution closure deferred. HATP production remains **NOT READY**. Runtime remains **Observed / observe / unavailable**.

## 24. Verdict

**HATP SIGNING CEREMONY + EVIDENCE STORE IMPLEMENTATION PLAN: COMPLETE — READY FOR IMPLEMENTATION.**

## 25. Recommended Next Phase

**149O.12A — Signed Evidence Model + Evidence Store Implementation** (Wave A + B of §17), followed by 149O.12B (resolver/orchestrator), 149O.12C (CLI + integration), and 149O.13 (independent verification) — see §17-18 for the full staged sequence and rationale.
