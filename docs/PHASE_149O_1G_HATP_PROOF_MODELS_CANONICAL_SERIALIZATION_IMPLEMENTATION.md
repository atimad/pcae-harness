# Phase 149O.1G — HATP Proof Models + Canonical Serialization Implementation (Wave 3)

## 0. Baseline

- **Repository:** `~/repos/pcae-harness`, branch `main`, working tree clean
  at phase start, `origin/main..HEAD` = 0.
- **Latest completed phase:** 149O.1F.2 — HATP Repository Identity +
  Trust-Store Foundation Independent Re-Verification. Verdict: `VERIFIED
  WITH NON-BLOCKING FINDINGS — HATP WAVE 1 + WAVE 2 FOUNDATION CONFORMS`.
  `B-149O.1F-1` `CONFIRMED CLOSED`.
- **Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`,
  `HATP-001 v1.0`, `FROZEN`. Normative span `HATP-REQ-001`..`HATP-REQ-117`,
  117 requirements. Byte-unchanged by this phase (confirmed, §9 below).
- **Canonical implementation plan:** `docs/PHASE_149O_1D_HUMAN_APPROVAL_TRUSTED_PROVENANCE_IMPLEMENTATION_PLAN.md`.
  This phase implements Wave 3 (G — HATP Proof Schema/Models, H — Canonical
  Serialization) only. It does not implement Wave 4 (verifier), Wave 5
  (real provider/human-presence signing), Wave 6 (RAE integration), or
  Wave 7 (deployment provisioning).
- **Runtime, unaffected:** `Observed` / `observe` / `unavailable`.
- **Open findings, unaffected:** `B-149O-1`, `B-149O-2`, `B-149O-3`,
  `B-149O-4` remain `OPEN`. `F-149O.1C-2` remains editorial debt only.

## 1. Wave-3 Requirement Set

Independently re-derived from HATP-001 (§4.2 of the 149O.1D plan), every
requirement whose primary owner is Wave 3 (subsystems G/H):

| Requirement(s) | Disposition | Test |
|---|---|---|
| HATP-REQ-067 | Proof artifact named `HumanApprovalProvenanceProof`, distinct type | `test_hatp_proof_models.py` (module import), naming used throughout |
| HATP-REQ-068 | `proof_version` field frozen; `1` is the only defined value | `test_unsupported_proof_version_rejected`, `test_missing_proof_version_rejected` |
| HATP-REQ-069 | Canonical payload field set (11 common + 2 AG3-only/2 AG5-only) | `test_ag3_valid_proof_parses`, `test_ag5_valid_proof_parses`, missing-field matrix |
| HATP-REQ-070 | No raw canonical deployment path field in the schema | `test_no_raw_deployment_path_field_in_schema` |
| HATP-REQ-071 | Generic action label without concrete operation fields is insufficient | `test_missing_operation_family_and_fields_rejected` |
| HATP-REQ-072 | `decision_record_digest` mutation invalidates equality/canonical bytes | `test_ag3_field_mutation_changes_canonical_bytes[decision_record_digest]` |
| HATP-REQ-073 | `binding_digest` mutation invalidates equality/canonical bytes | `test_ag3_field_mutation_changes_canonical_bytes[binding_digest]` |
| HATP-REQ-074 | `repository_id` mutation invalidates equality/canonical bytes | `test_ag3_repository_id_mutation_changes_canonical_bytes` |
| HATP-REQ-075 | Deterministic canonical serialization: sorted-key, fixed-encoding, no locale/whitespace dependence | `test_key_order_independence`, `test_whitespace_independence`, `test_canonical_round_trip_is_stable`, golden-vector tests |
| HATP-REQ-117 | Versioning discipline: no silent reinterpretation, unknown version rejected outright | `test_unsupported_proof_version_rejected` |

No Wave-3 requirement is left unmapped.

## 2. Scope Freeze (Reconfirmed)

**MUST_CHANGE (actual):** `src/pcae/core/human_approval_trusted_provenance.py`
(new); `tests/test_hatp_proof_models.py` (new); `tests/test_hatp_canonical_serialization.py`
(new); `tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py`
(new); `tests/conftest.py` (Fast Green marker registration, additive
only).

**MAY_CHANGE, used:** `tests/test_phase_149o_1e_hatp_repository_identity_trust_store_foundation.py`
— widened its own `expected` production-file set by one entry (the new
Wave-3 module), following this project's established phase-scoped
allowed-file-widening precedent; the same test file's independent
`test_wave_1_2_foundation_untouched`-equivalent checks (`test_hatp_contract_byte_unchanged`,
and this phase's own `test_wave_1_2_foundation_untouched`) separately
confirm `repository_identity.py`/`hatp_bootstrap.py` remain byte-unchanged.

**MUST_NOT_CHANGE, confirmed unchanged (§9 below):**
`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`,
`src/pcae/core/repository_identity.py`, `src/pcae/core/hatp_bootstrap.py`,
`src/pcae/core/rollback_approval_evidence.py`,
`src/pcae/core/permission_broker.py`,
`src/pcae/core/permission_broker_foundation.py`,
`src/pcae/core/mutation_permission.py`, `src/pcae/core/agent.py`,
`src/pcae/commands/agent.py`, `src/pcae/commands/init.py`,
`src/pcae/core/templates.py`.

## 3. Module Ownership

`src/pcae/core/human_approval_trusted_provenance.py` (new), matching the
149O.1D plan's own module-ownership proposal (§7) for subsystems G and H
(proof model, schema, canonical serialization). Dependency direction:
this module imports only `pcae.core.repository_identity.is_valid_repository_instance_id`
(a pure UUID4 format check, no authority claim) — reused, not
reimplemented, per the plan's explicit Wave-1-reuse instruction (§45 of
the governing prompt). No import of `hatp_bootstrap.py`,
`rollback_approval_evidence.py`, `permission_broker*.py`, `agent.py`, or
`commands/agent.py` — independently confirmed by
`test_no_forbidden_module_imports`/`test_only_expected_upstream_import`
(AST-based, not a `grep` best-effort).

## 4. Schema Strictness Mechanism (Deliberate Deviation From the Plan's Named Example)

F-149O.1C-1 requires `additionalProperties: false` **or an equivalent
strict typed parser**. This phase uses the latter: an explicit
`allowed`/`present`/`unknown` set-difference check
(`_build_proof_from_document`), mirroring the exact pattern already used
by the verified Wave-2 sibling module (`hatp_bootstrap.py`'s
`_parse_principal`/`_parse_signer`/`_parse_authority`/
`_parse_deployment_binding`), rather than the 149O.1D plan's illustrative
`schema_resources/human_approval_trusted_provenance/records/*.schema.json`
+ `jsonschema` Draft-2020-12 file. Rationale: a discriminated-union field
set (AG3-only vs. AG5-only fields, each family rejecting the other
family's fields) is more directly and legibly expressed as an explicit
set-difference check than as a `oneOf`/`if`/`then` JSON Schema
construction, and this choice keeps Wave 3 stylistically and structurally
consistent with the already-verified Wave 2 module rather than
introducing a second strictness mechanism into the same contract's
implementation. No `schema_resources/human_approval_trusted_provenance/`
directory was created this phase; none was needed. This is an
implementation-hardening choice within the space HATP-001 itself leaves
open (HATP-REQ-075 fixes canonical-serialization determinism, not the
parser's internal implementation strategy) — it changes no HATP-001
semantic meaning, and satisfies the phase's literal requirement text
("`additionalProperties: false` or an equivalent strict typed parser").

## 5. Field Layout (No Envelope/Payload Split)

HATP-REQ-069 defines no signature/assertion/envelope field in the
canonical payload — the entire 11-common + 2-family-specific field set
*is* the canonical signed payload, with no nested object anywhere in the
schema. This phase therefore models exactly that flat structure with no
artificial payload/envelope separation (149O.1D plan §47 applies only
where the contract itself distinguishes the two layers; it does not
here). A future Wave 5 provider adapter is responsible for whatever
provider-specific envelope wraps these exact canonical bytes; this phase
defines the bytes, not the wrapper.

## 6. Proof Type / Version / Discriminated Operation Models

- **Type:** `HumanApprovalProvenanceProof`, a frozen `dataclass`,
  distinct from `RollbackApprovalDecisionRef`/`RollbackApprovalBinding`
  (RAE), CHGR's Decision, and any Permission Broker type.
- **`proof_version`:** `SUPPORTED_PROOF_VERSIONS = frozenset({1})`.
  Missing, non-integer, boolean, or any value other than `1` is rejected
  via `UnsupportedProofVersionError` before any other structural check
  runs.
- **`rollback_site`:** `RollbackSite` `str` `Enum` (`AG3`, `AG5`),
  family-locking discriminant.
- **`Ag3OperationReference`** (`job_id`, `original_commit_sha`) and
  **`Ag5OperationReference`** (`per_id`, `ecp_id`): distinct frozen
  dataclasses, never a single loose dict with four optional fields (no
  "optional-field soup," §19 of the governing prompt). `HumanApprovalProvenanceProof.__post_init__`
  additionally enforces the family/type match even against direct
  dataclass construction bypassing `parse_hatp_proof` — defense in
  depth, mirroring RAE-001's own `RollbackApprovalBinding.__post_init__`
  pattern.

## 7. Strict Parsing / Closed Schema / Duplicate-Key Rejection

- **Entry point:** `parse_hatp_proof(raw: str | bytes) -> HumanApprovalProvenanceProof`.
- **Parsing order:** raw JSON (duplicate-key-rejecting `object_pairs_hook`)
  → top-level type check → `proof_version` check → `rollback_site`
  discriminant check → closed field-set check (wrong-family fields
  rejected, unknown fields rejected, missing fields rejected) →
  per-field structural validation → typed model construction.
- **Duplicate JSON keys:** rejected via a custom `object_pairs_hook`
  (`_reject_duplicate_keys`), applied at every nesting level by
  `json.loads`'s own recursive object-parsing (there happens to be no
  nested object in this flat schema, but the hook is general or would
  be).
- **F-149O.1C-1 result:** `IMPLEMENTED HARDENING`. An otherwise-valid
  proof carrying one unrecognized field
  (`test_f_149o_1c_1_unknown_field_hardening_is_enforced`, plus the
  general `test_unknown_top_level_field_rejected` and the
  self-selected-authority-field parametrized matrix) is rejected, never
  ignored. HATP-001's own text is unmodified (§9 below).

## 8. Canonical Serialization / Digest

- **`hatp_proof_to_document(proof) -> dict`:** plain JSON-serializable
  representation in HATP-REQ-069's exact field names.
- **`canonicalize_hatp_proof_payload(proof) -> bytes`:** `json.dumps(...,
  sort_keys=True, separators=(",", ":"), ensure_ascii=False,
  allow_nan=False).encode("utf-8")`, mirroring the existing project
  convention (`cltr/canonicalization.py::_canonical_bytes`,
  `rollback_approval_evidence.py::_canonical_bytes`) rather than
  inventing a new one.
- **`digest_hatp_proof_payload(proof) -> str`:** `hashlib.sha256(...).hexdigest()`
  — plain lowercase hex, no algorithm prefix, matching the existing
  project digest convention (`_compute_content_digest`, CHGR
  `record_digest`). No digest domain-separation prefix was added: HATP-001
  does not specify one, and none of RAE's own analogous digests use one
  either (§55 of the governing prompt — no new semantics introduced
  silently).
- **Timestamp canonicalization:** `issued_at` is parsed via a
  fail-closed, timezone-aware ISO-8601 parser duplicated (not imported)
  from `repository_identity.py`/`hatp_bootstrap.py`/
  `rollback_approval_evidence.py::_parse_iso_timestamp` (avoids
  reintroducing the Python 3.9 `fromisoformat` Z-suffix defect this
  project already hit once), then re-rendered to one canonical
  millisecond-precision UTC `Z`-suffixed form
  (`%Y-%m-%dT%H:%M:%S.%f`[:-3]+`Z`, matching `repository_identity.py`'s
  own format exactly) at parse time. Two structurally-equivalent but
  differently-formatted input timestamps (explicit `+00:00` offset vs.
  `Z` suffix) therefore canonicalize identically
  (`test_equivalent_timestamp_representations_canonicalize_identically`).
- **Round trip:** model → canonical JSON → parse → model → canonical
  JSON produces identical bytes (`test_canonical_round_trip_is_stable`).
- **Determinism:** no random ID, no wall-clock `now`, no filesystem/
  network access anywhere in the module (`test_no_filesystem_or_network_or_now_dependency`,
  `test_no_filesystem_call_site_at_runtime`).

## 9. Dependency Boundaries / Production Diff (Reconfirmed)

```
git diff --name-only HEAD -- docs/contracts/     => empty
git diff --name-only HEAD -- src/pcae/core/repository_identity.py src/pcae/core/hatp_bootstrap.py  => empty
git diff --name-only HEAD -- src/pcae/core/rollback_approval_evidence.py  => empty
git diff --name-only HEAD -- src/pcae/core/permission_broker.py src/pcae/core/permission_broker_foundation.py src/pcae/core/mutation_permission.py  => empty
git diff --name-only HEAD -- src/pcae/core/agent.py src/pcae/commands/agent.py  => empty
```

Production diff is exactly one new file:
`src/pcae/core/human_approval_trusted_provenance.py`. No unrelated
hunk. Hunk classification: `PROOF_MODEL` + `OPERATION_MODEL` +
`STRICT_PARSER` + `CANONICAL_SERIALIZATION` + `DIGEST` + `VERSIONING`
(single cohesive module, no separable unrelated change).

## 10. Golden Vectors

Fixed fixture (`repository_id = 11111111-1111-4111-8111-111111111111`,
`decision_record_digest = "a"*64`, `binding_digest = "b"*64`,
`issued_at = 2026-08-06T00:00:00.000Z`):

- AG3 canonical bytes and SHA-256 digest: asserted exactly in
  `test_ag3_golden_canonical_bytes` / `test_ag3_golden_digest`.
- AG5 canonical bytes and SHA-256 digest: asserted exactly in
  `test_ag5_golden_canonical_bytes` / `test_ag5_golden_digest`.
- AG3/AG5 digests differ (`test_ag3_ag5_golden_digests_differ`).

These are compatibility anchors for a future Wave 4/5 implementation, per
the governing prompt's own instruction (§105-108).

## 11. Mutation-Sensitivity Matrix

Every AG3 field (`principal_id`, `signer_key_id`, `provider_profile`,
`repository_id`, `decision_record_id`, `decision_record_digest`,
`binding_id`, `binding_digest`, `job_id`, `original_commit_sha`,
`issued_at`) and every AG5-specific field (`per_id`, `ecp_id`),
individually mutated, changes both canonical bytes and digest
(parametrized matrix, `test_hatp_canonical_serialization.py`). Swapping
the entire operation family (`rollback_site` + its fields) also changes
canonical bytes.

## 12. Adversarial Coverage Summary

Structural attacks exercised (all reject, per governing-prompt items
90-104): unknown top-level field; self-selected trust/authority fields
(`trusted_root`, `trusted_public_key`, `attestation_root`,
`authority_registry`, `canonical_root`, `trust_store_root`,
`deployment_root`); authority booleans (`approved`, `trusted`,
`authorized`, `human_present`, `valid`); AG3 discriminator + AG5 fields;
AG5 discriminator + AG3 fields; AG3 discriminator + AG5-only payload;
mixed-family fields; missing operation family entirely; every individual
missing required field (AG3 and AG5); malformed `repository_id`; bad
digest format; bad commit-SHA format; bad/naive timestamp; unsupported/
missing/non-integer/boolean `proof_version`; top-level JSON array instead
of object; invalid JSON; duplicate JSON key (top-level, and injected into
a full valid document).

## 13. No-Verification-Vocabulary / No-Trust-Derivation Audit

`test_no_verification_status_vocabulary_defined`,
`test_no_verify_or_trust_named_callable_exists`,
`test_no_approval_present_or_hatp_valid_symbol_defined`, and
`test_no_signature_or_attestation_verification_code_present`
independently confirm: no member of HATP-REQ-078's closed 13-state
vocabulary is defined; no public callable name contains `verify`,
`trusted`, or `authorized`, and none is named `is_valid`; no
`approval_present`/`HATP_TRUSTED_OPERATIONAL`/`HATP_VALID` symbol exists;
no cryptography/FIDO2/WebAuthn/PIV library reference exists anywhere in
the module's source.

## 14. Regression Results

- **Combined Wave-1/2 foundation regression** (`test_repository_identity.py`
  + `test_hatp_bootstrap_foundation.py` + `test_phase_149o_1e_...py` +
  `test_phase_149o_1f_...py` + `test_phase_149o_1f_1_...py`): `103
  passed` — matches the entering baseline exactly.
- **149O.1F.2 independent re-verification suite**
  (`test_phase_149o_1f_2_...py`): `90 passed` — matches baseline.
- **HATP contract + implementation-plan regression**
  (`test_phase_149o_1c_...py` + `test_phase_149o_1d_...py`): `127
  passed` — matches baseline.
- **New Wave-3 suite** (`test_hatp_proof_models.py` +
  `test_hatp_canonical_serialization.py` +
  `test_phase_149o_1g_hatp_proof_models_canonical_serialization.py`):
  `100 passed`.
- **Fast Green:** `python -m pytest -m fast_green -n auto -q`: `4531
  passed`, entering baseline `4431 passed` + 100 new deterministic,
  hardware- and environment-independent Wave-3 tests, all three new test
  modules added to `tests/conftest.py`'s `FAST_GREEN_MODULES`. No
  regression.
- **RAE / Permission Broker / agent broadened regression:** recorded at
  §15 below (this module makes no RAE/PB/agent code changes; expected
  zero-impact, confirmed).

## 15. RAE / Permission Broker / Agent Regression (Filled In)

`python -m pytest tests/ -k "rollback_approval or permission_broker or
mutation_permission or agent" -q -n auto`: **5 failed, 5626 passed.**
The 5 failures (4 in
`test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`,
1 in
`test_phase_148f_permission_broker_production_consumption_independent_verification.py::test_permission_broker_consumer_scope_inventory`)
were independently reproduced, identically, against the unmodified tree
via `git stash push -u` / re-run / `git stash pop` — confirmed
pre-existing and unrelated to this phase's diff, matching the exact
pre-existing-failure disposition already recorded by 149O.1F.2's own
report (`5381 passed / 5 failed, all 5 confirmed pre-existing`; the
`passed` count differs only because this run's `-k` filter and repo
state differ, not because the failure set changed).

## 16. Full Suite

`python -m pytest -q -n auto`: **97 failed, 28145 passed, 10 skipped**
(1:26:08). A serial re-run of exactly the failed set
(`python -m pytest --lf -q -n0`) reduced this to **75 failed, 22
passed** — the 22 delta are `-n auto` parallel-worker cross-test
interference (shared temp/env state across wheel-build/sdist-packaging
tests, Telegram-notification tests, and similar), not genuine failures;
this class of parallel-only flake was already noted as a known
non-deterministic artifact by 149O.1F.2's own Fast Green result. The
remaining **75 failed** were independently reproduced, identically
(same 75 test IDs), against the unmodified tree via `git stash push -u`
/ re-run `--lf -n0` / `git stash pop` — confirmed entirely pre-existing
and unrelated to this phase's diff. None of the 75 touch HATP,
`repository_identity.py`, `hatp_bootstrap.py`,
`human_approval_trusted_provenance.py`, RAE, or the Permission Broker;
the affected areas span CLTR authority packaging (Group 2-11 wheel/
sdist tests), Telegram notification dispatch tests, bootstrap/TODO
roadmap consistency, and other long-standing, unrelated areas. Baseline
entering this phase (per 149O.1F.2's own report) was `68
pre-existing-unrelated`; this phase's own stash-reconfirmed pre-existing
count is `75` on the current `main` tip — a pre-existing drift between
149O.1F.2 and this phase's start that predates and is independent of
this phase's own diff (reconfirmed by the identical stash-based
reproduction), not a regression this phase introduced.

## 17. No-Go Confirmations

- `HATP-001 v1.0` remained byte-unchanged; not modified by this phase.
- The independently verified HATP requirement count remains **117**.
- Wave 1 repository identity (`repository_identity.py`) remains
  unchanged.
- Wave 2 bootstrap/trust-store foundation (`hatp_bootstrap.py`) remains
  unchanged.
- `B-149O.1F-1` remains `CONFIRMED CLOSED`.
- `F-149O.1C-1` is implemented only as strict proof-schema hardening; no
  HATP-001 semantic contract amendment was made.
- `F-149O.1C-2` remains editorial debt only.
- No HATP signature verification was implemented.
- No provider attestation verification was implemented.
- No trusted-signer lookup was implemented.
- No human-presence verification was implemented.
- No real FIDO2 provider was implemented.
- No real PIV provider was implemented.
- No human approval CLI was implemented.
- No bootstrap/admin CLI was implemented.
- No Class-B OS security boundary was provisioned.
- Current HATP deployment remains `NOT READY`.
- A structurally valid HATP proof does NOT mean HATP `VALID`; no such
  status is derivable from anything in this module.
- No production HATP verification status `VALID` was introduced.
- No production rollback request derives `approval_present=True` from
  HATP; the symbol does not exist anywhere in this module.
- `B-149O-1` through `B-149O-4` remain `OPEN`.
- No RAE production integration was implemented.
- No AG3 Permission Broker integration was implemented.
- No AG5 Permission Broker integration was implemented.
- No rollback execution behavior changed.
- `RAE-001 v1.0`, `RWMPC-001 v1.0`, `PBPC-001 v1.2`, `PBPA-001 v1.0`,
  `CHGR-001` remain unchanged.
- IWC confirmation remains distinct from approval; not touched by this
  phase.
- AESIC/AEM remain disclosure-only; not touched by this phase.
- No illegal CHGR/TAM composition was introduced.
- No POL-001..012 meaning was changed; no POL-013+ was added.
- TK1/TK2/TK3 remain deferred.
- No Runtime Enforcement behavior changed.
- No Prompt Generation, Prompt Dispatch, or agent invocation capability
  was implemented.
- Runtime remains `Observed`, maximum capability remains `observe`,
  execution availability remains `unavailable`.

## 18. Wave-3 Verdict

```
HATP WAVE 3 IMPLEMENTED
— PROOF MODELS + CANONICAL SERIALIZATION READY FOR INDEPENDENT VERIFICATION
```

All 10 Wave-3-owned requirements (HATP-REQ-067..075, HATP-REQ-117) have a
concrete, tested implementation. Unknown fields, wrong-family fields,
self-selected trust/authority fields, duplicate JSON keys, and every
individually-omitted required field are rejected across the entire
schema (there is no separate nested layer in this contract's flat
payload). Canonical bytes are independent of JSON key order, whitespace,
and equivalent timestamp representations; every load-bearing field's
mutation changes both canonical bytes and digest; round-trip
serialization is stable; golden vectors are fixed for both AG3 and AG5.
`F-149O.1C-1: IMPLEMENTED HARDENING — STRICT CLOSED PROOF SCHEMA
ENFORCED.`

## 19. HATP Production Readiness

```
HATP PRODUCTION:
NOT READY
```

Unaffected by this phase, as required.

## 20. Recommended Next Phase

```
149O.1H — HATP Proof Models + Canonical Serialization Independent Verification
```

Per the governing prompt's own logic (§175): this Wave defines the exact
bytes a future signature will cover, and deserves independent adversarial
verification before Wave 4 (verifier) or Wave 5 (real provider) build on
top of it.
