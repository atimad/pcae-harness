# Phase 149O.1H.3 — HATP Sub-Microsecond Timestamp Truncation Narrow Repair

## Scope

Narrow Wave-3 production repair of exactly one Blocking finding
independently discovered by Phase 149O.1H.2's re-verification: the
narrow basis on which `B-149O.1H-1` was reopened (sub-microsecond
lexical fractional-second truncation, distinct from the original
millisecond-level collision Phase 149O.1H.1 already closed). Owns
`src/pcae/core/human_approval_trusted_provenance.py`, focused Wave-3
tests, and this document. No Wave 4 verification engine, no signature/
attestation/human-presence verification, no trusted-signer resolution,
no FIDO2/PIV provider, no Class-B OS provisioning, no RAE/Permission
Broker/AG3/AG5 wiring. `HATP-001 v1.0` is byte-unchanged; the
independently verified requirement span remains `HATP-REQ-001..117`
(117 requirements).

## Baseline (confirmed before any edit)

- `git status --short`: clean. `origin/main..HEAD`: 0 commits.
- `pcae health`/`pcae check`/`pcae status coherence`: healthy / passed /
  coherent.
- `pcae push check`: nothing_to_push.
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`.
- `pcae phase-report show --latest` + `pcae phase-report reconcile
  --phase-id 149O.1H.2`: 149O.1H.2 confirmed `completed`, report
  `complete`, reconciled `already_dispatched`; recommended next phase
  `149O.1H.3` exactly.
- `pcae doctor task-memory`: 8 pre-existing `tasks/DONE.md` sync
  warnings, unrelated to this phase, unchanged by this phase.
- Wave-3 entering baseline: 100 (`test_hatp_proof_models.py` +
  `test_hatp_canonical_serialization.py` +
  `test_phase_149o_1g_...py`) + 166 (149O.1H suite) + 93 (149O.1H.1
  suite) + 99 (149O.1H.2 suite) = 358 passed.

## New Blocking finding, restated

`B-149O.1H-1`, reopened on a narrow sub-microsecond basis by
Phase 149O.1H.2:

```
raw A = "2026-01-01T12:00:00.0000001Z"
raw B = "2026-01-01T12:00:00.0000009Z"
raw A != raw B
parsed_datetime(A) == parsed_datetime(B)   # both truncate to microsecond=0
canonical(A) == canonical(B)               # both "2026-01-01T12:00:00.000Z"
digest(A) == digest(B)
```

## Direct CPython truncation reproduction (before any edit)

```python
>>> from datetime import datetime
>>> datetime.fromisoformat("2026-01-01T12:00:00.0000001+00:00").microsecond
0
>>> datetime.fromisoformat("2026-01-01T12:00:00.0000009+00:00").microsecond
0
```

Both raw strings collapse to `microsecond == 0` before
`_require_issued_at` ever inspects the value — confirming the defect
is CPython's `datetime.fromisoformat` silently discarding fractional
digits past the sixth, not a rounding or width-mismatch bug in
`_require_issued_at` itself.

Against the pre-repair production module:

```python
>>> _require_issued_at("2026-01-01T12:00:00.0000001Z")
'2026-01-01T12:00:00.000Z'
>>> _require_issued_at("2026-01-01T12:00:00.0000009Z")
'2026-01-01T12:00:00.000Z'
```

Both accepted, identical canonical string. Defect independently
reproduced.

## Repair strategy

Lexical fractional-second precision is now validated **before**
`datetime.fromisoformat` ever runs, per the governing prompt's required
processing order. A new regular expression,
`_FRACTIONAL_SECONDS_RE = re.compile(r"\.(\d+)(?=Z$|[+-]\d{2}:\d{2}$)")`,
matches the raw fractional-second digit group immediately preceding the
timestamp's `Z` or colon-separated `±HH:MM` timezone suffix at the end
of the string — the only place a fractional-second group can lexically
appear in the timestamp forms this module's grammar accepts. A new
helper, `_reject_excess_fractional_precision(value, context=...)`,
raises `InvalidProofSchemaError` if that captured digit group is longer
than 6 characters (the most Python's `datetime` can represent without
silent truncation). It is called from `_parse_iso_timestamp` — the sole
call site through which both the parser path
(`_build_proof_from_document` → `_require_issued_at`) and every
model's `__post_init__` (`_require_issued_at`, call site unchanged)
already flow, so no second, drifting timestamp-validation path is
introduced (`B-149O.1H-2`'s shared-validator architecture is preserved,
not disturbed).

The existing millisecond-domain rule
(`parsed.microsecond % 1000 != 0` → reject, Phase 149O.1H.1) is
unchanged and runs strictly after the new lexical guard, on whatever
`datetime` the (now-guaranteed-lossless, ≤6-digit) parse produces. The
canonical renderer (`_canonical_timestamp_string`) is unchanged.

Effective accepted domain after this repair:

```
input lexical fractional-digit count: 0..6         (lexical guard)
semantic precision must resolve to a whole millisecond
  (parsed.microsecond % 1000 == 0)                  (pre-existing rule)
```

## Timestamp pipeline, before and after

Before:

```
raw issued_at -> datetime.fromisoformat (lossy, silently truncates >6 digits)
             -> millisecond-domain check (operates on already-lossy value)
             -> canonical millisecond rendering
```

After:

```
raw issued_at -> lexical fractional-digit-count guard (reject if > 6)
             -> datetime.fromisoformat (now lossless for all accepted input)
             -> millisecond-domain check (unchanged)
             -> canonical millisecond rendering (unchanged)
```

## Post-repair verification

### Original collision pair (149O.1H.1's domain) — still rejected

```python
>>> _require_issued_at("2026-01-01T12:00:00.0001Z")
InvalidProofSchemaError: ... sub-millisecond fractional-second precision is not accepted ...
>>> _require_issued_at("2026-01-01T12:00:00.0009Z")
InvalidProofSchemaError: ... sub-millisecond fractional-second precision is not accepted ...
```

### New collision pair — now rejected before lossy parsing

```python
>>> _require_issued_at("2026-01-01T12:00:00.0000001Z")
InvalidProofSchemaError: issued_at: fractional-second precision exceeds 6 digits ...
>>> _require_issued_at("2026-01-01T12:00:00.0000009Z")
InvalidProofSchemaError: issued_at: fractional-second precision exceeds 6 digits ...
```

Both fail at the new lexical guard, before `datetime.fromisoformat`
ever runs on them.

### Seven-plus-digit collision matrix — all rejected lexically

`.0000001`/`.0000009`, `.0010001`/`.0010009`, `.1234561`/`.1234569`,
`.9999991`/`.9999999` — all 8 values independently confirmed rejected
(`tests/test_phase_149o_1h_3_...py::test_seven_plus_digit_collision_matrix_all_rejected`).

### ≤6-digit matrix — lexical guard passes through, millisecond rule decides

| fraction   | accepted? | reason                                   |
|------------|-----------|-------------------------------------------|
| `.000000`  | yes       | 0µs, millisecond-aligned                  |
| `.000001`  | no        | 1µs, not millisecond-aligned              |
| `.001000`  | yes       | 1000µs = 1ms exactly                      |
| `.123000`  | yes       | 123000µs = 123ms exactly                  |
| `.123456`  | no        | 123456µs, not millisecond-aligned         |
| `.999999`  | no        | 999999µs, not millisecond-aligned         |

Demonstrates the required separation: lexical representability (≤ 6
digits) vs. HATP's millisecond semantic domain — two independent
layers, not one conflated rule.

### Timezone-suffix coverage

`+01:00`/`-05:00` offset forms with 7+ fractional digits are rejected
identically to the `Z` form
(`test_offset_forms_with_excess_precision_rejected`). Timezone
equivalence for accepted values is preserved:
`12:00:00.001Z == 13:00:00.001+01:00 == 07:00:00.001-05:00`, and
distinct milliseconds remain distinct
(`test_timezone_equivalence_preserved_for_accepted_values`).

### Parser/constructor equivalence

Every representative precision-matrix value (`Z`, `.001Z`,
`.000001Z`, `.0000001Z`, `.1234567Z`, `.123456789Z`) produces the
identical accept/reject outcome through `parse_hatp_proof` and direct
`HumanApprovalProvenanceProof(...)` construction
(`test_parser_constructor_equivalence_across_precision_matrix`) —
`B-149O.1H-2`'s shared-validator architecture confirmed undisturbed.

### Canonical bytes / golden vectors / digest — unchanged for valid input

Independently recomputed for `issued_at="2026-03-04T05:06:07.008Z"`
(same fixture used by 149O.1G/149O.1H/149O.1H.2):

```
canonical bytes contain: "issued_at":"2026-03-04T05:06:07.008Z"
digest: 968f67163a0367d5f21e2800a3b51e2bd9a4751743ee1a83be5ddd261ee3474c
```

Identical rendering rule (`_canonical_timestamp_string`,
untouched) and identical digest algorithm (plain lowercase hex
SHA-256 of the canonical JSON payload, untouched). No golden constant
required updating.

### Injectivity

A bounded sweep of distinct accepted millisecond instants
(`0, 7, 14, ..., 994` ms) produces zero canonical-string collisions
(`test_injectivity_over_accepted_millisecond_instants`).

## Regressions

- New repair suite:
  `tests/test_phase_149o_1h_3_hatp_sub_microsecond_timestamp_truncation_repair.py`
  — 57 passed.
- Wave-3 combined (100 + 166 + 93 + 99 + 57): 515 passed. The
  149O.1H.2 suite's two findings-in-progress tests
  (`test_sub_microsecond_fractional_digits_are_silently_truncated_not_rejected`,
  `test_new_finding_sub_microsecond_collision_reproduced`) were updated
  in place (not deleted) to assert the now-repaired behavior, following
  the same historical-test-flip convention 149O.1H.1 established for
  149O.1H's own tests — the pre-repair narrative is preserved in this
  document, in git history, and in the updated tests' docstrings.
- Wave-1/2 foundation (`test_repository_identity.py`,
  `test_hatp_bootstrap_foundation.py`,
  `test_phase_149o_1e_...py`, `test_phase_149o_1f_...py`,
  `test_phase_149o_1f_1_...py`): 103 passed, unchanged.
- 149O.1F.2 suite: 90 passed, unchanged.
- Report-trust (`test_phase_reports.py`, `test_phase_reports_cli.py`,
  `test_phase_report_trust_hard_fail.py`,
  `test_push_phase_report_identity_137f1.py`): 201 passed, unchanged.
- HATP contract/plan (`test_phase_149o_1c_...py`,
  `test_phase_149o_1d_...py`): 126/126 substantive assertions passed
  (`test_phase_149o_1d_...py::TestProductionBoundaryUnchanged::test_no_src_pcae_files_modified_this_phase`
  fails only against the dirty working tree during this phase's own
  edit — the well-known "dirty-tree-only `git diff HEAD`-style check"
  pattern documented in prior phases (149O.1H.1's own gotcha #2);
  confirmed passing (32/32) against a clean stash-popped tree before
  this repair, and resolves once this phase's commit lands).
- Fast Green (`python -m pytest -m fast_green -n auto -q`): 4531
  passed, identical to the entering baseline — the new repair suite is
  not registered as `fast_green` (deliberately, matching this module's
  existing pattern of keeping its authoritative regression suites
  outside that marker).
- RAE/PB/agent broad regression: unaffected — zero production changes
  outside `human_approval_trusted_provenance.py`.

## Purity / import boundary audit

`src/pcae/core/human_approval_trusted_provenance.py` still imports
only `hashlib`, `json`, `re`, `dataclasses`, `datetime`, `enum`,
`typing`, and `pcae.core.repository_identity.is_valid_repository_instance_id`
— no new import, no filesystem/network/wall-clock/randomness
dependency introduced by this repair. `_reject_excess_fractional_precision`
and `_FRACTIONAL_SECONDS_RE` are pure string operations.

## Production diff

```
git diff --name-only 01bacf8a..HEAD -- src/pcae/
src/pcae/core/human_approval_trusted_provenance.py
```

Exactly one production file. Diff classification:

- `RAW_TIMESTAMP_PRECISION_VALIDATION` / `TIMESTAMP_PARSER_GUARD`: the
  new `_FRACTIONAL_SECONDS_RE` constant, `_reject_excess_fractional_precision`
  helper, and its call from `_parse_iso_timestamp`.

`UNRELATED = 0`. No proof field added or removed. No canonical
timestamp precision change. No canonical signed-payload field-set
change. No digest algorithm change. No proof-version semantics change.
No AG3/AG5 operation semantics change. No `issued_at_raw` shadow field.
No new verification vocabulary. No Wave-4 behavior implemented.

## Findings status

- **B-149O.1H-1 REPAIRED** — raw timestamp domain is now lossless
  before canonicalization: any raw `issued_at` carrying more than 6
  fractional digits is rejected before `datetime.fromisoformat` runs;
  any value that survives the lexical guard is then subject to the
  pre-existing, unchanged millisecond-domain rule. Both the original
  millisecond-level collision (149O.1H.1's scope) and the newly
  discovered sub-microsecond collision (149O.1H.2's reopened scope)
  are now rejected. This is an **implementation** verdict, not an
  independent verification verdict — a follow-up independent
  re-verification phase (149O.1H.4) is required before this may be
  considered closed for governance purposes.
- **B-149O.1H-2**: unaffected, remains INDEPENDENTLY CONFIRMED CLOSED
  — the shared `_require_*` validator layer (including
  `_require_issued_at`, now with the additional lexical guard) is
  still called identically by the parser and every constructor
  `__post_init__`; no drift introduced.
- **F-149O.1C-1**: unaffected, remains INDEPENDENTLY CONFIRMED
  IMPLEMENTED. No parser loosening.
- **F-149O.1C-2**: unaffected, remains editorial debt only.
- **B-149O.1F-1**: unaffected, remains CONFIRMED CLOSED.
- **B-149O.1R-1 / B-149O.1R-2**: unaffected, remain CLOSED.
- **B-149O-1 through B-149O-4**: unaffected, remain OPEN.

## Technical canonicalization statement

Accepted raw timestamp → no precision loss during parse (lexical
guard enforces ≤ 6 fractional digits before `datetime.fromisoformat`
runs) → millisecond-domain validation (unchanged,
`microsecond % 1000 == 0`) → deterministic canonical timestamp
(unchanged renderer). For every two accepted timestamp semantics,
`instant A != instant B` implies distinct canonical representations,
over the now-lossless accepted lexical domain.

## Wave-3 status

**WAVE 3: REPAIRED, PENDING INDEPENDENT RE-VERIFICATION.** Not fully
verified by this implementation phase alone.

## HATP production readiness

Remains **NOT READY**. Still unimplemented: Wave 4 verification
engine, signature verification, provider attestation verification,
trusted signer resolution, human-presence verification, real FIDO2
provider, real PIV provider, Class-B deployment, RAE/HATP integration.
A structurally valid HATP proof still does NOT imply HATP VALID.
Verification vocabulary (`VALID`, `UNKNOWN_SIGNER`, `approval_present`,
`HATP_VALID`) remains absent from this module.

## Runtime / OS boundary

Runtime state before and after: `Observed` / `observe` / `unavailable`
(unchanged). No user creation, ACL change, sudoers edit, trust-store
provisioning, or hardware setup performed.

## Recommended next phase

**149O.1H.4 — HATP Timestamp Canonicalization Final Independent
Re-Verification.** Must independently re-test: 7+ fractional-digit
rejection across the full matrix, the lossless accepted lexical
domain, the millisecond-domain rule, timezone equivalence, timestamp
injectivity, constructor/parser equivalence, golden vectors, closed
schema, and signed-payload completeness — before Wave 4
(`149O.1I`) may begin.
