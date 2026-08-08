# Phase 149O.12A — Signed Evidence Model + Evidence Store Implementation

Phase type: **BOUNDED PRODUCTION IMPLEMENTATION**. Implements Wave A +
Wave B of the Phase 149O.11 implementation plan: the
`HATPSignedEvidenceEnvelope` model/parser/canonical serializer
(`src/pcae/core/hatp_signed_evidence.py`) and the exclusive-publication
evidence store (`src/pcae/core/hatp_evidence_store.py`). Not
authorized, and not implemented, this phase: signing ceremony
(149O.12B), proof-context resolution, hardware invocation, CLI
(149O.12C), AG3/AG5 consumption wiring, rollback dispatch changes,
Permission Broker changes, Class-B provisioning, or HATP production
activation.

## 1. Baseline

- Latest completed phase entering this phase: **149O.11 — HATP Signing
  Ceremony + Evidence Store Implementation Plan.** Status: completed,
  report complete, pushed, `origin/main..HEAD = 0`. Last commit:
  `0812d49c`.
- Contract entering this phase: **HSCE-001 v1.1 — VERIFIED WITH
  NON-BLOCKING FINDINGS — CONFORMS.** `149O.10-F-1/F-2/F-3`,
  `149O.10-Obs-2`: all INDEPENDENTLY CONFIRMED CLOSED.
  `149O.10.2-Obs-3` (loser-comparison read-failure `error_type` gap):
  open non-blocking observation, resolved by the 149O.11 plan's design
  selection (`evidence_persistence_failure`) and implemented this phase.
  `149O.10.2-Obs-4` (historical 89-vs-29 report-count discrepancy):
  documentation-only, not propagated.
- `B-149O-1..4`: INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
  BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED. Unaffected by this
  phase.
- Initial inspection this phase reconfirmed: repo clean,
  `origin/main..HEAD = 0`; `pcae health` healthy; `pcae check` passed;
  `pcae status coherence` coherent; `pcae doctor task-memory` warnings
  pre-existing/unrelated (stale `tasks/done/` DONE.md sync gaps
  predating this phase); `pcae push check` clean (`nothing_to_push`);
  `pcae runtime inspect` Observed/observe/unavailable, PB
  `execution_unavailable`; `pcae notify status` Telegram
  configured/enabled/ready; `pcae phase-report show --latest` confirmed
  149O.11 completed/complete/pushed/consistent; `pcae phase-report
  reconcile --phase-id 149O.11` returned `reconciled`
  (inspection-only, no mutation).
- HATP production entering and leaving this phase: **NOT READY**.
  Runtime entering and leaving this phase: **Observed / observe /
  unavailable**.

## 2. Contract State

| Contract | Version | Status | Byte-changed by this phase? |
|---|---|---|---|
| HSCE-001 | 1.1 | VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS | No |
| HATP-001 | 1.0 | FROZEN, unamended | No |
| RAE-001 | 1.0 | FROZEN, unamended | No |

Independently reconfirmed via `git diff --stat <149O.11-baseline-commit>
-- <contract-path>` for all three contract files: empty diff in every
case.

## 3. 149O.12A Requirement Subset (from the 149O.11 79-requirement table)

Per the 149O.11 plan's Production File Allowlist (§16):

| Module | Requirements owned |
|---|---|
| `hatp_signed_evidence.py` | HSCE-REQ-031–040, 053, 056, 059, 062–064, 072–073 |
| `hatp_evidence_store.py` | HSCE-REQ-007, 041–045, 052, 054–055, 057–058, 060–061, 064 |

**Coverage result:** every requirement in this subset has both code and
test coverage in `tests/test_hatp_signed_evidence.py` /
`tests/test_hatp_evidence_store.py` (field-level/attack-level) and
`tests/test_phase_149o_12a_signed_evidence_model_store_implementation.py`
(cross-cutting scope/boundary checks). No requirement in this subset
was left unimplemented or untested.

## 4. Production Diff

**Production files added (exactly two, matching the 149O.11 plan's
allowlist for this phase):**

- `src/pcae/core/hatp_signed_evidence.py` (363 lines)
- `src/pcae/core/hatp_evidence_store.py` (304 lines)

**Production files modified:** none.

**Unrelated hunks:** 0 — independently confirmed by
`TestProductionFileAllowlist` in the phase-specific suite (diffs the
current tree against the 149O.11 baseline commit `0812d49c` via `git
diff --name-only` plus `git ls-files --others --exclude-standard`,
unioned, and asserted equal to exactly the two files above). No existing
HATP module (`human_approval_trusted_provenance.py`, `hatp_providers.py`,
`hatp_fido2_provider.py`, `hatp_bootstrap.py`, `hatp_ag_authority.py`,
`repository_identity.py`), RAE module, `agent.py`,
`commands/agent.py`, Permission Broker module, or `cli.py` was touched.

**Test/config files touched (outside the production allowlist, as
expected for an implementation phase):**

- `tests/test_hatp_signed_evidence.py` (new)
- `tests/test_hatp_evidence_store.py` (new)
- `tests/test_phase_149o_12a_signed_evidence_model_store_implementation.py` (new)
- `tests/conftest.py` (modified — Fast Green module registration only)
- `tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py`
  (modified — the retained 149O.5-F-3-lesson semantic production-file
  allowlist widened to include this phase's two new modules, per the
  149O.11 plan's own explicit instruction on how that lesson applies
  to an intentional new-HATP-module addition; not a violation)

**Hunk classification** (per the 149O.11 plan's §16 taxonomy):
`EVIDENCE_MODEL`, `EVIDENCE_VALIDATION`, `EVIDENCE_PARSER`,
`EVIDENCE_SERIALIZER`, `EVIDENCE_ID_BINDING` (all in
`hatp_signed_evidence.py`); `EVIDENCE_STORE`, `PATH_VALIDATION`,
`SYMLINK_SAFETY`, `EXCLUSIVE_PUBLICATION`, `LOSER_COMPARISON`,
`TEMP_LIFECYCLE`, `ERROR_MAPPING` (all in `hatp_evidence_store.py`).
**`UNRELATED` = 0.**

## 5. `HATPSignedEvidenceEnvelope` Model Design

Exact frozen four-field schema (HSCE-REQ-032): `evidence_version: int`,
`evidence_id: str`, `proof: HumanApprovalProvenanceProof`,
`provider_assertion: bytes`. No authority-bearing field exists on this
type or on `HATPEvidencePublicationResult` — independently confirmed by
`TestNoAuthorityBearingFields` (asserts the exact field-name set on both
types and the absence of `approved`/`verified`/`valid`/`permission`/
`allow`/`operational`/`executed`/`human_present`).

**Immutability:** `@dataclass(frozen=True)` (HSCE-REQ-073); confirmed by
`test_envelope_is_frozen` (`dataclasses.FrozenInstanceError` on mutation
attempt).

**Constructor-domain result:** `__post_init__` calls the single shared
`_validate_envelope_fields` helper.

**Parser-domain result:** `_envelope_from_document` builds each field
independently, then constructs `HATPSignedEvidenceEnvelope(...)` —
routing through the identical `__post_init__` validation.

**Constructor/parser equivalence (HSCE-REQ-072):** enforced structurally
(one shared validation function, not two independently-maintained
domains) — confirmed by `test_constructor_and_parser_reject_identical_domain`.

**Version validation:** `isinstance(value, bool)` checked independently
before `isinstance(value, int)` is trusted (mirrors
`_require_proof_version`'s own pattern). **Bool rejection:** confirmed —
`True`/`False` both rejected as `UnsupportedEvidenceVersionError`
(`test_bool_is_not_silently_accepted_as_int_one`,
`test_construction_rejects_bad_versions[True/False]`).

**Evidence-ID validation:** shared `validate_evidence_id` (regex
`^[0-9a-f]{64}$`, no `.lower()`/`.strip()` normalization), exported for
`hatp_evidence_store.py`'s own reuse (HSCE-REQ-056). 15-case parametrized
rejection test covers traversal, absolute path, wrong length, uppercase,
non-hex, whitespace, separator characters, `..`, a Cyrillic homoglyph,
empty string, `None`, and a non-string type.

**Proof-digest binding:** `evidence_id == digest_hatp_proof_payload(proof)`
enforced at construction (not just at parse); mismatch raises
`EvidenceIdDigestMismatchError` immediately, for both a directly-built
instance and a parsed document.

**Provider-assertion representation:** stored as decoded `bytes` on the
model; Base64 (`base64.b64encode`/`b64decode`, `validate=True` strict
mode) only at the JSON serialize/parse boundary. Empty bytes structurally
accepted (no cryptographic check performed by this module).

**Base64 strictness:** invalid Base64 (`binascii.Error`) mapped to
`InvalidEvidenceEnvelopeSchemaError` at parse — confirmed by
`test_invalid_base64_provider_assertion_rejected`.

**Closed-schema result:** exact 4-key allowlist; unknown key rejected
(`test_unknown_top_level_field_rejected`), each of the 4 required keys'
absence independently rejected
(`test_missing_required_field_rejected`, parametrized).

**Duplicate-key result:** module-local `_reject_duplicate_keys`
`object_pairs_hook` (matching the HATP-family per-module-duplication
convention, HSCE-REQ-053's explicit instruction) rejects a duplicate key
at any nesting level in one parse pass — confirmed for both the outer
envelope (`test_duplicate_top_level_key_rejected`) and the nested
`proof` object (`test_duplicate_nested_proof_key_rejected`).

**Unknown-field / wrong-type result:** every field independently
attacked with `None`/`bool`/`int`/`list`/`dict`/wrong-string as
applicable — all fail closed (parametrized wrong-type test classes).

**Canonical serialization result:** `serialize_hatp_signed_evidence` —
UTF-8, `sort_keys=True`, `allow_nan=False`, standard `json.dumps`
default separators (HSCE-REQ-053's text lists exactly these properties,
no compact-separator requirement — none invented). Embeds
`hatp_proof_to_document(proof)` unchanged (never reimplemented) and
`base64.b64encode(provider_assertion)`.

**Round-trip result:** `parse(serialize(E)) == E`
(`test_canonical_round_trip_parse_of_serialize_equals_original`) and
`serialize(parse(bytes)) == canonical_bytes`
(`test_canonical_round_trip_serialize_of_parse_equals_canonical_bytes`).

**Noncanonical-input canonicalization result:** differently key-ordered,
differently-indented input JSON parses to the identical envelope and
re-serializes to byte-identical canonical output
(`test_noncanonical_json_layout_canonicalizes_to_one_representation`).

## 6. Evidence Store Design

**Store root:** `<repository_root>/.pcae/hatp-evidence/envelopes/`
(HSCE-REQ-041/042), constructed from an explicit `HarnessPath`
constructor argument (mirroring `RollbackApprovalEvidenceStore`'s own
explicit-root convention) — never derived from an ambiguous CWD read
inside the store itself.

**Path builder:** `path_for(evidence_id)` — pure, no I/O, validates
`evidence_id` via the shared `hatp_signed_evidence.validate_evidence_id`
before constructing any path (HSCE-REQ-056). **Path traversal:**
9-case parametrized rejection test (`../`, absolute path, wrong length,
uppercase, `/`, `\`, `%2e%2e`-literal, leading whitespace) — all rejected
before filesystem access.

**Symlink root / parent symlink:** `_check_no_escaping_symlink_components`
walks `.pcae` → `hatp-evidence` → `envelopes` relative to the resolved
repository root; any existing symlink component resolving outside the
repository root fails closed as `evidence_persistence_failure`
(HSCE-REQ-058) — parametrized over all three component levels
(`test_publish_rejects_escaping_path_component_symlink`).

**Final symlink:** `os.path.islink(final_path)` checked explicitly before
the `os.link` attempt (HSCE-REQ-057), and re-checked in the loser branch
for the race window between the initial check and the `os.link` call —
confirmed for both `publish` and `load`
(`test_publish_rejects_symlinked_final_destination`,
`test_load_rejects_symlinked_final_destination`).

**Load API:** `load(evidence_id)` — explicit-ID-only, no `latest`/glob
fallback (confirmed by `test_load_has_no_latest_or_glob_fallback`,
asserting the absence of `latest`/`list_latest`/`list`/`exists`/
`overwrite`/`update`/`approve`/`delete_authority` on the class, and
independently by `TestNoAuthorityBearingFields.test_store_has_no_exists_or_approval_style_method`
asserting the public API surface is exactly
`{path_for, load, publish, repository_root, envelopes_dir}`).

**Missing evidence:** `EvidenceNotFoundError`, never a file created as a
side effect (`test_load_missing_evidence_raises_not_found`,
`test_load_never_creates_a_file`).

**Corrupt evidence:** the specific structural error
`hatp_signed_evidence.parse_hatp_signed_evidence` itself raises
propagates unmodified — no fallback (`test_load_corrupt_json_propagates_parse_error`).

**Digest mismatch on load:** `EvidenceIdDigestMismatchError` propagates
(`test_load_digest_mismatch_propagates`).

**Unsafe final object (load path):** symlinked/non-regular final path
rejected before read.

**Publish API:** `publish(envelope) -> HATPEvidencePublicationResult
(evidence_id, path, idempotent)` — never a bare boolean, never an
authority-bearing field.

**Canonical-bytes-before-temp:** `serialize_hatp_signed_evidence(envelope)`
computed once, in memory, before any temp file is created — the *same*
bytes are used for the temp-file write, the winner check, and every
loser byte-comparison (single serializer, no second encoder anywhere in
either module).

**Temp creation:** `tempfile.mkstemp(dir=envelopes_dir, prefix=".{evidence_id}.",
suffix=".tmp")` — collision-safe, same-directory, same-filesystem.

**Temp write / flush / fsync:** complete candidate bytes written inside
a `with os.fdopen(fd, "wb") as handle:` block; `handle.flush()` then
`os.fsync(handle.fileno())` before the block exits.

**Close-before-link:** the `with os.fdopen(...)` block's exit closes the
fd — no writable descriptor referencing the temp inode survives past
that point, before the `os.path.islink` check or the `os.link` attempt
ever run. **Verdict: CONFIRMED**, by two independent means: (a) static
source-ordering check
(`TestHardLinkPublicationPrimitive.test_close_before_link_ordering_in_source`,
docstring-stripped, confirms `os.fdopen(` precedes `os.link(` in
`publish`'s code body); (b) dynamic instrumentation
(`test_write_descriptor_closed_before_link_is_attempted`, which wraps
both `os.fdopen` and `os.link`, captures the temp fd, and — from inside
the wrapped `os.link` call itself — attempts `os.write(fd, ...)` and
asserts it raises `OSError` because the fd is already closed).

**`os.link` winner path:** on success, this writer is the exclusive-
publication winner; the temp pathname is unlinked (best-effort,
non-authoritative) in the `finally` block; result returned with
`idempotent=False`. **Verdict: no `os.replace` call anywhere in either
module** — independently confirmed by
`test_os_replace_never_used_as_winner_primitive` (`inspect.getsource`
substring absence) and by the two fault-injection tests that spy on
`os.replace` and assert it is never invoked even on `os.link` failure.

**EEXIST loser path:** re-checks `os.path.islink` (race-window
re-check), then validates the existing object is a safe regular file
(§6.1 below) before reading and comparing canonical bytes.

**Safe-final-object validation (149O.10.2-Obs-3 mapping):** `os.lstat`
(never follows a symlink) + `stat.S_ISREG` check. A directory, FIFO,
socket, device file, or unreadable file at the destination fails closed
as `EvidencePersistenceFailureError` — **never** `EvidenceConflictError`
— confirmed by `test_publish_existing_directory_at_final_path_fails_closed`,
`test_publish_existing_fifo_at_final_path_fails_closed`,
`test_publish_unreadable_existing_final_fails_closed` (skipped under
root), and independently by the phase-specific
`TestObs3Mapping.test_directory_at_final_path_maps_to_persistence_failure_not_conflict`,
which explicitly asserts the outcome is never misreported as a conflict.

**Equal compare (idempotent):** byte-identical existing vs. candidate →
`idempotent=True`, no error, no rewrite
(`test_byte_identical_rewrite_is_idempotent`).

**Different compare (conflict):** byte-differing → `EvidenceConflictError`,
winner file unchanged on disk
(`test_differing_rewrite_same_id_conflicts_and_winner_unchanged`,
`test_same_proof_different_assertion_only_first_persists`).

**Cleanup:** temp file unlink attempted in every exit path via a single
`finally` block (`contextlib.suppress(OSError)` — a cleanup failure is
never authoritative) — confirmed for the winner, idempotent, and
conflict paths (`test_temp_file_cleaned_up_after_successful_publish`,
`_after_idempotent_publish`, `_after_conflict`).

**Concurrency results (real filesystem, real `os.link`, never mocked in
the positive-path suite):**

- Single writer: `test_first_publish_is_winner`.
- Identical retry: `test_byte_identical_rewrite_is_idempotent`.
- Differing retry: `test_differing_rewrite_same_id_conflicts_and_winner_unchanged`.
- Two-identical race: `test_two_identical_concurrent_writers_race_safely`
  (`threading.Barrier`-synchronized) — exactly one winner, one
  idempotent loser.
- Two-differing race: `test_two_differing_concurrent_writers_race_safely`
  — exactly one success, one conflict.
- Many-writer race: `test_many_identical_writers_exactly_one_canonical_file`
  (parametrized 8 and 16 identical writers — exactly one canonical
  file, one winner, N-1 idempotent losers).
- Mixed identical/differing many-writer race:
  `test_many_mixed_writers_identical_and_differing` (8 writers, half
  identical/half distinct assertions — exactly one canonical file on
  disk, every non-canonical writer receives `EvidenceConflictError`).
- Race stability: `test_race_stability_repeated_iterations` — 5 isolated
  repeated 6-writer races, exactly one winner every time.

**Partial write / fsync failure:** `test_write_failure_leaves_no_partial_final_artifact`
(monkeypatched `os.fdopen` returns a writer that raises `OSError` on
`write`) and `test_fsync_failure_leaves_no_partial_final_artifact`
(monkeypatched `os.fsync` raises) — both confirm no final artifact is
ever visible and no orphan `.tmp` file remains.

**EXDEV / EPERM:** `test_non_eexist_link_errors_fail_closed_no_fallback`
(parametrized over `errno.EXDEV`, `errno.EPERM`) — `os.link` monkeypatched
to raise; `EvidencePersistenceFailureError` raised, no final file, no
leftover temp file.

**Unsupported hard-link filesystem:** `test_unsupported_hard_link_filesystem_fails_closed_no_replace_fallback`
(`errno.ENOTSUP`) — additionally spies on `os.replace` and asserts it is
never called, confirming no overwrite-capable fallback exists under any
condition.

**Orphan temp file / loader authority:** `test_loader_never_treats_temp_file_as_evidence` —
an orphan `.{evidence_id}.orphan.tmp` file present in `envelopes/` is
never discovered by `load()`; only the exact `{evidence_id}.json`
filename counts.

## 7. Tests

- **`tests/test_hatp_signed_evidence.py`** — 84 tests. Constructor/
  parser equivalence, immutability, builder never accepts a caller
  `evidence_id`, version bool-rejection (8-case parametrized), evidence-
  ID validation (15-case parametrized), digest binding, Base64
  round-trip/strictness, empty-assertion structural acceptance, closed
  schema (unknown/missing, parametrized), duplicate keys (outer +
  nested), wrong-type attacks per field (parametrized), canonical
  round-trip (both directions), noncanonical-input canonicalization,
  content-addressing precision, same-proof/different-assertion model-
  layer permission.
- **`tests/test_hatp_evidence_store.py`** — 48 tests. Store root
  isolation, no-mutation-on-construction, path traversal (9-case
  parametrized), winner/idempotent/conflict, load API (missing/corrupt/
  digest-mismatch/no-fallback), symlink safety (final + all three path
  components, parametrized), Obs-3 object-type checks (directory, FIFO,
  unreadable), temp-file lifecycle (cleanup on all three outcomes, no
  post-link-write instrumentation), fault injection (EXDEV, EPERM,
  ENOTSUP, fsync failure, write failure), real-filesystem concurrency
  (2-writer, many-writer parametrized 8/16, mixed, repeated-iteration
  stability).
- **`tests/test_phase_149o_12a_signed_evidence_model_store_implementation.py`** —
  44 tests. Production-diff-scope allowlist (git-derived, robust across
  untracked/staged/committed states), contract byte-identity (HSCE-001/
  HATP-001/RAE-001), no-scope-creep (no CLI, no signing-ceremony module,
  no existing-HATP-module edit, no PB/hardware/verification-call
  imports), no-authority-bearing-field confirmation, hard-link-primitive
  static checks (`os.link` present, `os.replace` absent, close-before-
  link ordering), Obs-3 mapping (error-class inventory, directory-vs-
  conflict distinction), no-`exists()`-as-approval pattern, required-
  attack-subset presence, Python 3.9 / no-hardware-import compatibility.

**Total new tests this phase: 176. All pass.**

## 8. Regression Suites

| Suite | Result |
|---|---|
| 149O.9 contract-freeze | 60 passed |
| 149O.10 verification | 29 passed |
| 149O.10.1 repair | 43 passed |
| 149O.10.2 re-verification | 66 passed |
| (combined, matches reproducible current baselines, not the historical stale 89 claim) | **198 passed** |
| HATP Wave 3 (proof models/canonical serialization) | included in Fast Green, passing |
| HATP Wave 4 (verification engine) | included in Fast Green, passing |
| HATP Wave 5 (hardware provider) | 1 test skipped (no real FIDO2 device attached), rest passing |
| RAE contract/models/persistence/validation | 34 pre-existing failures, byte-identical to the `0812d49c` baseline (`git stash -u` comparison run) — an `Invalid isoformat string: '...Z'` defect in `rollback_approval_evidence.py`'s Python-version-sensitive timestamp parsing, entirely unrelated to and unaffected by this phase's two new modules (neither module is imported by, nor imports, `rollback_approval_evidence.py`) |
| Bounded rollback/Permission-Broker sweep (`-k "rollback or permission_broker"`) | 93 failed / 1405 passed (with this phase's changes) vs. 93 failed / 1404 passed (`git stash -u` baseline) — **identical failure count**, one additional pass (this phase's own new `test_...rollback...`-matching test names), confirming non-regression |
| Report-trust suite (`test_phase_report_trust_gate*`, `test_phase_report_trust_hard_fail`, `test_report_consistency_derived_correctness_134e9`) | 162 passed |
| **Fast Green** (`pytest -m fast_green -n auto`) | **4784 passed, 1 skipped, 0 failed** — includes this phase's two new deterministic, real-filesystem-only test modules (`test_hatp_signed_evidence`, `test_hatp_evidence_store`) newly registered in `tests/conftest.py::FAST_GREEN_MODULES`; not byte-identical to the 149O.11-entering baseline (4590 passed, 2 skipped) by design, since this phase intentionally adds 132 new Fast-Green-eligible tests plus 44 non-Fast-Green phase-specific tests — **zero failures**, the only non-regression claim actually made here |

## 9. Findings

- `149O.10-F-1`, `149O.10-F-2`, `149O.10-F-3`, `149O.10-Obs-2`: retained,
  INDEPENDENTLY CONFIRMED CLOSED, unaffected by this phase.
- `149O.10.2-Obs-3` (loser-comparison read-failure `error_type` gap):
  **implemented this phase** per the 149O.11 plan's design selection —
  mapped to `EvidencePersistenceFailureError`
  (`evidence_persistence_failure`), never `EvidenceConflictError`.
  Independently exercised (directory, FIFO, unreadable-file cases).
  Remains formally **pending independent verification** (149O.13, not
  self-certified by this implementation phase).
- `149O.10.2-Obs-4` (historical 89-vs-29 report-count discrepancy):
  documentation observation only; this report cites the reproducible
  198-test combined 149O.9–149O.10.2 count, never the stale 89 figure.
- `149O.5-F-3` (stale-boundary-test debt): the retained lesson was
  **applied**, not re-triggered — `test_phase_149o_1g_..._only_expected_production_files_changed`'s
  semantic allowlist was deliberately widened to name this phase's two
  new files, per the 149O.11 plan's own explicit instruction for this
  exact scenario (an intentional new-HATP-module addition).
- No new finding raised by this phase.

## 10. Scope Confirmations

Only the two planned production modules
(`src/pcae/core/hatp_signed_evidence.py`,
`src/pcae/core/hatp_evidence_store.py`) were added; no other
`src/pcae/**` file was changed. HSCE-001 v1.1, HATP-001 v1.0, and
RAE-001 v1.0 all remained byte-unchanged (independently confirmed via
`git diff --stat` against the 149O.11 baseline commit). No signing
ceremony was implemented. No CLI command was implemented (`cli.py` and
`commands/` untouched; no `commands/hatp.py` created). No hardware
signing occurred (neither module imports `hatp_providers.py`,
`hatp_bootstrap.py`, or calls `request_signature`). No AG3/AG5
consumption was added (`hatp_ag_authority.py` untouched and does not
reference either new module). No rollback dispatch behavior changed
(`agent.py`, `commands/agent.py` untouched). No Permission Broker
behavior changed (neither new module imports any `permission_broker*`
module). No Class-B provisioning occurred. No HATP production
activation occurred. The evidence store remains untrusted storage and
does not itself establish approval — it computes no `approval_present`
value anywhere, and exposes no `exists()`/`latest()`/`approve()`-style
method. Signing/evidence remains distinct from verification, approval,
permission, capability, and execution (neither module calls
`verify_hatp_proof`). `B-149O-1..4` remain independently verified at
the HATP-gated authority boundary with system execution closure
deferred. HATP production remains **NOT READY**. Runtime remains
**Observed / observe / unavailable**.

## 11. Implementation Verdict

```
HATP SIGNED EVIDENCE MODEL + EVIDENCE STORE: IMPLEMENTED
— READY FOR 149O.12B
```

This is not a claim of full HSCE-001 implementation — only Wave A
(envelope model) and Wave B (evidence store) of the 149O.11 plan's
six-wave decomposition. Waves C–F (proof-context resolution, signing
orchestration, CLI, integrated attack-matrix suite) remain unimplemented,
scheduled for 149O.12B and 149O.12C.

## 12. Recommended Next Phase

**149O.12B — HATP Signing Ceremony Resolver + Orchestrator
Implementation** (Waves C + D of the 149O.11 plan): AG3/AG5 proof-
context resolution, provider/signer resolution, preview-before-touch,
`issued_at` generation, hardware provider invocation, TOCTOU recheck,
and evidence-store publication orchestration (consuming this phase's
`build_hatp_signed_evidence_envelope`/`HATPEvidenceStore.publish`
directly). Still no CLI — that remains 149O.12C's scope exclusively.
