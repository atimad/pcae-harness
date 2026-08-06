# Phase 149O.1H — HATP Proof Models + Canonical Serialization Independent Verification

## 0. Baseline

- **Repository:** `~/repos/pcae-harness`, branch `main`, working tree clean
  at phase start, `origin/main..HEAD` = 0.
- **Latest completed phase:** 149O.1G — HATP Proof Models + Canonical
  Serialization Implementation (Wave 3), commit `01c7fb74`, pushed,
  `origin/main..HEAD` 0. Verdict: `HATP WAVE 3 IMPLEMENTED — PROOF
  MODELS + CANONICAL SERIALIZATION READY FOR INDEPENDENT VERIFICATION`.
- **Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`,
  `HATP-001 v1.0`, `FROZEN`. Normative span `HATP-REQ-001..HATP-REQ-117`
  (117 requirements). Confirmed byte-unchanged by this phase (§11 below).
- **Wave-3 production surface under review:**
  `src/pcae/core/human_approval_trusted_provenance.py` (439 lines, one
  file, per `git show 01c7fb74 --stat`).
- **Wave 1/2 foundation:** `repository_identity.py` (Wave 1, VERIFIED),
  `hatp_bootstrap.py` (Wave 2, VERIFIED WITH NON-BLOCKING FINDINGS),
  `B-149O.1F-1` CONFIRMED CLOSED. Not reopened by this phase.
- **Phase type:** independent adversarial verification. This phase does
  NOT modify `human_approval_trusted_provenance.py`,
  `repository_identity.py`, `hatp_bootstrap.py`, HATP-001, RAE, or the
  Permission Broker, and does not implement Wave 4/5/6/7.

## 1. Methodology

Every claim made by the 149O.1G implementation report was independently
re-derived rather than accepted:

1. The exact production diff was reconstructed via `git show 01c7fb74
   --stat` / `git diff <parent>..01c7fb74` rather than trusted from the
   report text.
2. HATP-001 §19-21 (`HATP-REQ-067..077`) and §29 (`HATP-REQ-117`) were
   read directly to re-derive the Wave-3 requirement set and the
   required canonical-payload field list, independent of the 149O.1D
   plan's own table.
3. The module's public surface (`parse_hatp_proof`,
   `HumanApprovalProvenanceProof`, `Ag3OperationReference`,
   `Ag5OperationReference`, `canonicalize_hatp_proof_payload`,
   `digest_hatp_proof_payload`, `hatp_proof_to_document`) was exercised
   directly via ad-hoc adversarial scripts (not reusing 149O.1G's own
   test fixtures) before any assertion was written into the permanent
   test file, to separate exploration from claims.
4. Golden vectors were independently recomputed from HATP-REQ-075's
   determinism requirement (sorted-key, compact-separator,
   `ensure_ascii=False` UTF-8 JSON + SHA-256) using a hand-rolled
   canonicalizer (`_independent_canonical_bytes` in the new test file),
   not by copying constants out of `tests/test_hatp_canonical_serialization.py`.
5. Direct dataclass construction was attempted through the public
   constructors (bypassing `parse_hatp_proof` entirely) to test whether
   parser-level invariants are also constructor-level invariants.

## 2. Exact Wave-3 Production Diff Reconstruction

```
git show 01c7fb74 --stat
```

```
 CHANGELOG.md                                                    |  20 +
 PROJECT_STATUS.md                                                |  42 ++
 docs/PHASE_149O_1G_..._IMPLEMENTATION.md                         | 415 ++
 src/pcae/core/human_approval_trusted_provenance.py               | 439 ++
 tasks/active/...-149o-1g-....md                                  |  82 ++
 tasks/active/...-idle-...-149o-1f-2.md                           |   2 +-
 tests/conftest.py                                                |   6 +
 tests/test_hatp_canonical_serialization.py                       | 273 ++
 tests/test_hatp_proof_models.py                                  | 376 ++
 tests/test_phase_149o_1e_....py                                  |   7 +
 tests/test_phase_149o_1g_....py                                  | 280 ++
```

Exactly **one** new `src/pcae/**` production file:
`src/pcae/core/human_approval_trusted_provenance.py`. No other
production source file under `src/pcae/` was touched.

**Hunk classification** (all in the single new module):

| Region | Classification |
|---|---|
| `SUPPORTED_PROOF_VERSIONS`, `HATPProofError` family | VERSIONING / structural error vocabulary |
| `RollbackSite`, `Ag3OperationReference`, `Ag5OperationReference` | OPERATION_MODEL |
| `HumanApprovalProvenanceProof` + `__post_init__` | PROOF_MODEL |
| `_parse_iso_timestamp`, `_canonical_timestamp_string` | TIMESTAMP_NORMALIZATION |
| `_reject_duplicate_keys`, `_load_json_no_duplicate_keys` | DUPLICATE_KEY_REJECTION |
| `_require_nonempty_str`, `_require_sha256_hex`, `_require_commit_sha`, `_COMMON_FIELDS`/`_AG3_ONLY_FIELDS`/`_AG5_ONLY_FIELDS`, `_build_proof_from_document`, `parse_hatp_proof` | STRICT_PARSER |
| `hatp_proof_to_document`, `canonicalize_hatp_proof_payload` | CANONICAL_SERIALIZATION |
| `digest_hatp_proof_payload` | DIGEST |

No `UNRELATED` production hunk found. This confirms the "one new file,
nothing else in `src/pcae/`" claim.

## 3. Wave-3 Requirement Reconstruction (independent)

Read directly from HATP-001 §19 ("Human Approval Provenance Proof"), §20
("Canonical Payload"), §21 ("Proof Creation"), and §29 ("Versioning"):

| Requirement | Normative meaning | Owner | Verified? |
|---|---|---|---|
| HATP-REQ-067 | Proof artifact named `HumanApprovalProvenanceProof`, structurally distinct from CHGR Decision / RAE Binding / PB decision | Wave 3 | Yes — class exists, distinct name/type |
| HATP-REQ-068 | `proof_version` field mandatory; contract freezes `1` as the only defined value | Wave 3 | Yes — `SUPPORTED_PROOF_VERSIONS = {1}`, enforced |
| HATP-REQ-069 | Payload SHALL bind (at minimum) 11 common fields + family-locked AG3/AG5 operation fields | Wave 3 | Yes, field-set-complete (§9 below) |
| HATP-REQ-070 | No raw canonical local deployment path in the payload | Wave 3 | Yes — no such field exists in `_COMMON_FIELDS`/`_AG3_ONLY_FIELDS`/`_AG5_ONLY_FIELDS` |
| HATP-REQ-071 | Generic action label without concrete operation fields is insufficient (`WRONG_OPERATION`/`MALFORMED`) | Wave 3 | Yes — schema has no generic-action field; AG3/AG5 operation fields are mandatory per family |
| HATP-REQ-072 | Mutation of Decision content SHALL invalidate the proof via `decision_record_digest` | Wave 3 | Yes — `decision_record_digest` is signed-payload-bound and mutation-sensitive (§14 below) |
| HATP-REQ-073 | Mutation of Binding content SHALL invalidate the proof via `binding_digest` | Wave 3 | Yes — same mechanism |
| HATP-REQ-074 | Changing `repository_id` after proof creation SHALL invalidate the proof | Wave 3 | Yes — `repository_id` mutation-sensitive; **but see F-149O.1H-1 (non-blocking)**, case-variant `repository_id` is not normalized to one canonical form |
| HATP-REQ-075 | Canonical serialization SHALL be deterministic, independent of key order/locale/newline/timestamp ambiguity | Wave 3 | **NOT VERIFIED — see B-149O.1H-1 (BLOCKING)**: sub-millisecond-distinct timestamps canonicalize identically |
| HATP-REQ-076 | Future implementation SHALL define provider/signature semantics; none frozen by this contract | Not Wave 3 (future) | Correctly absent — no signature code in this module |
| HATP-REQ-077 | Proof SHALL NOT establish signer trust merely by carrying its own public key | Wave 3 boundary | Yes — no public-key/trust field exists anywhere in the schema |
| HATP-REQ-117 | Versioning: unsupported version never silently reinterpreted, rejected outright | Wave 3 | Yes — `UnsupportedProofVersionError`, fails before any construction |

No Wave-3-owned requirement is missing an implementation and test
mapping. **One Wave-3-owned requirement (HATP-REQ-075) is found NOT
satisfied** — see the BLOCKING timestamp finding in §10.

## 4. Model Field Inventory (independently reconstructed by reading source)

`HumanApprovalProvenanceProof` (frozen dataclass): `proof_version: int`,
`principal_id: str`, `signer_key_id: str`, `provider_profile: str`,
`repository_id: str`, `decision_record_id: str`,
`decision_record_digest: str`, `binding_id: str`, `binding_digest: str`,
`rollback_site: RollbackSite`, `operation_reference: Union[Ag3OperationReference,
Ag5OperationReference]`, `issued_at: str`. All 12 fields required (no
`Optional[...]` field on the class itself). All participate in the
canonical signed payload except `operation_reference` (which is
decomposed into its own sub-fields at serialization time — see §9).

`Ag3OperationReference` (frozen): `job_id: str`, `original_commit_sha: str` —
matches the expected shape exactly.

`Ag5OperationReference` (frozen): `per_id: str`, `ecp_id: str` — matches
the expected shape exactly.

## 5. AG3/AG5 Discrimination

The discriminator is `rollback_site: RollbackSite` (a `str` `Enum` with
members `AG3`/`AG5`), independent of which operation fields happen to be
present. `_build_proof_from_document` computes `family_fields` /
`other_family_fields` from the discriminator value, not from key
presence, and explicitly rejects any document that carries the *other*
family's fields (`wrong_family` check) even before the closed-schema
`unknown` check runs. `HumanApprovalProvenanceProof.__post_init__`
re-enforces the same rule at the *typed-object* level: an AG3
`rollback_site` with a non-`Ag3OperationReference` `operation_reference`
(or vice versa) raises `InvalidProofSchemaError`, independent of the
parser. Both checks were independently attacked and confirmed effective
(§8 below) — this is genuinely discriminator-driven, not
key-presence-inferred.

## 6-7. Construction / Immutability Attacks

- **AG3 family + AG5 object / AG5 family + AG3 object**, via direct
  `HumanApprovalProvenanceProof(...)` construction (not the parser):
  both rejected with `InvalidProofSchemaError` by `__post_init__`. Confirmed.
- **Field mutation after construction**: `proof.principal_id = "x"`
  raises `dataclasses.FrozenInstanceError` (the class is
  `@dataclass(frozen=True)`); same for `Ag3OperationReference` and
  `Ag5OperationReference`. Confirmed immutable.
- **Nested mutable-container / alias-mutation surface**: none exists.
  Every field on every one of the three dataclasses is a plain `str`,
  `int`, `RollbackSite`, or a nested frozen dataclass — no `list`,
  `dict`, or `set` field anywhere in the model graph, so there is no
  possible "mutate the original after construction" attack (there is
  nothing externally-owned and mutable to alias).

## 8. Proof Version Attacks

| Input | Result |
|---|---|
| `0`, `2`, `-1` | `UnsupportedProofVersionError` (not a member of `{1}`) |
| `"1"` (string) | `UnsupportedProofVersionError` ("must be an integer") |
| `1.0` (float) | `UnsupportedProofVersionError` |
| `True` | `UnsupportedProofVersionError` — the implementation explicitly guards `isinstance(x, bool)` before the `int` check, so the classic "`bool` is an `int` subclass" trap is correctly closed **for the parser path** (see B-149O.1H-2 for the constructor path, where this guard is absent) |
| `False` | `UnsupportedProofVersionError` |
| `null` / missing | `UnsupportedProofVersionError` |

All fail structurally, before canonicalization; no best-effort parse
observed.

## 9. Closed-Schema / Self-Selected-Trust Attacks (F-149O.1C-1 re-verification)

Every one of the following unknown top-level fields was independently
injected into an otherwise-valid AG3 document and rejected with
`InvalidProofSchemaError`: `harmless_unknown`, `trusted_root`,
`trusted_public_key`, `attestation_root`, `authority_registry`,
`canonical_root`, `trust_store_root`, `deployment_root`, `approved`,
`trusted`, `authorized`, `human_present`, `valid`. All 13 rejected — none
accepted.

AG3-fields-injected-into-AG5-document and AG5-fields-injected-into-AG3-document
are both rejected (`wrong_family` check, independent of the generic
unknown-field check).

There is no separate nested/evidence/envelope object in the schema to
attack — HATP-REQ-069 defines a flat payload and the implementation
mirrors that (confirmed by direct source reading, §4 above); "closed
nested schema" therefore has nothing further to enforce beyond the
top-level closed field set already tested.

**F-149O.1C-1 verdict: INDEPENDENTLY CONFIRMED IMPLEMENTED — STRICT
CLOSED PROOF SEMANTICS ENFORCED** (at the parser boundary — see
B-149O.1H-2 for a caveat about the constructor boundary).

## 10. Duplicate JSON Keys

Attacked at every layer: (a) a minimal two-key duplicate
(`{"principal_id":"a","principal_id":"b"}`) — rejected
(`MalformedProofError`); (b) duplicate `repository_id`,
`decision_record_digest`, `binding_digest`, `rollback_site` each
injected into an otherwise-valid full document — all rejected, no
last-wins behavior; (c) duplicate `job_id` (AG3) and duplicate `per_id`
(AG5) injected into the nested operation-field region of an otherwise
flat document — both rejected. The custom `object_pairs_hook`
(`_reject_duplicate_keys`) is applied by `json.loads` to every object
in the document, so it is inherently recursive — confirmed by testing a
duplicate key that is not at the outermost object level (there is only
one JSON object level in this flat schema, so "recursive" here reduces
to "applies uniformly to the single object," which was directly
verified).

## 11. Non-Object Top-Level / NaN-Infinity

`[]`, `"string"`, `1`, `true`, `null` as the full document all raise
`InvalidProofSchemaError` (`_build_proof_from_document`'s
`isinstance(document, dict)` guard). `NaN`/`Infinity`/`-Infinity`
injected into the `proof_version` position are parsed by
`json.loads(..., allow_nan=True by default)` into Python `float('nan')`/
`float('inf')`/`float('-inf')`, which then fail the `isinstance(x, int)`
check in `_build_proof_from_document` and are rejected with
`UnsupportedProofVersionError`. No canonicalization ambiguity arises
because these values never reach a constructed `HumanApprovalProvenanceProof`
via the parser path.

## 12. Unicode Analysis

- ASCII, non-ASCII BMP (`"élodie"`), and non-BMP (emoji) principal IDs
  all parse and canonicalize to distinct byte sequences.
- The canonical serializer uses `ensure_ascii=False`; canonical bytes
  contain literal UTF-8 (confirmed: no `\uXXXX` escape sequence appears
  for the BMP test case; the literal UTF-8 encoding of `"é"` is present
  in the canonical bytes instead).
- Precomposed `"é"` (U+00E9) vs. `"e"` + combining acute accent
  (U+0065 U+0301) are **not** silently collapsed — they canonicalize to
  distinct byte sequences (no NFC/NFD normalization is performed
  anywhere in the module). This matches HATP-001, which does not require
  Unicode normalization.
- A lone UTF-16 surrogate (`"\ud800"`) is accepted by
  `json.loads`/Python's `str` type at parse time, but
  `canonicalize_hatp_proof_payload` raises `UnicodeEncodeError`
  deterministically when it attempts to UTF-8-encode the canonical JSON
  string — this fails closed rather than producing inconsistent bytes.
  Classified: unsupported input, rejected deterministically at
  canonicalization time (not at parse time) — an acceptable but slightly
  late failure point; **non-blocking observation**, since no bytes are
  ever produced or signed for this input.

## 13. Determinism

- **Key order**: a document with reversed key order canonicalizes to
  identical bytes as the original.
- **Whitespace**: compact vs. pretty-printed (indented) JSON input
  canonicalizes to identical bytes.
- **JSON escape equivalence**: `"a/b"` vs. `"a\/b"` (both legal JSON
  encodings of the same string) canonicalize to identical bytes, since
  `json.loads` yields the same Python string either way and the
  canonical serializer is a pure function of the parsed model.
- **Cross-call stability**: calling `canonicalize_hatp_proof_payload`
  twice on the same proof object yields byte-identical output.
- **Round trip**: raw JSON → proof → canonical bytes → JSON parse (via
  `hatp_proof_to_document`) → proof → canonical bytes is byte-identical
  at both ends.
- **TZ environment independence**: setting `TZ=America/New_York` in the
  process environment before parsing does not change canonical output
  (the module performs no local-timezone-dependent formatting — all
  timestamp handling converts explicitly to UTC).

**Canonicalization verdict for these axes: DETERMINISTIC.** (The
timestamp-precision axis is a separate, failing axis — see §14.)

## 14. Timestamp Semantics — HIGH PRIORITY, BLOCKING FINDING

**Accepted input forms** (`_parse_iso_timestamp`, built on
`datetime.fromisoformat` with a manual `Z` → `+00:00` substitution):

| Input | Accepted? | Canonical result |
|---|---|---|
| `2026-01-01T12:00:00Z` | Yes | `2026-01-01T12:00:00.000Z` |
| `2026-01-01T13:00:00+01:00` (same instant) | Yes | `2026-01-01T12:00:00.000Z` — **timezone-equivalent instants canonicalize identically, confirmed** |
| `2026-01-01T12:00:00.000Z` | Yes | `2026-01-01T12:00:00.000Z` |
| `2026-01-01T12:00:00` (no timezone) | **No** — rejected (`_parse_iso_timestamp` requires `parsed.tzinfo is not None`) |
| `2026-01-01 12:00:00Z` (space instead of `T`) | Yes — `datetime.fromisoformat` accepts any single separator character |
| `2026-01-01T12:00:00z` (lowercase `z`) | **No** — the module's `Z`-substitution only matches uppercase `"Z"` (`value.endswith("Z")`); a lowercase `z` is passed through unmodified to `fromisoformat`, which does not accept it |
| `2026-01-01T12:00:00+0100` (offset without colon) | Yes, **on Python ≥3.11** — see version-portability finding below |
| `2026-01-01` (date only) | **No** — rejected, `fromisoformat` on a date-only string yields a naive `datetime` (`tzinfo is None`) |
| `2026-01-01T24:00:00Z` | Yes — Python's `datetime` normalizes `24:00:00` by rolling to `2026-01-02T00:00:00.000Z` |
| `2026-01-01T23:59:60Z` (leap second) | **No** — `fromisoformat` rejects second=60 |
| `not-a-date` | **No** |

**Fractional precision / rounding**: the canonical renderer
(`_canonical_timestamp_string`) formats via
`parsed.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"`. `%f` always
produces 6 microsecond digits; slicing off the last 3 characters
**truncates** (does not round) to millisecond precision.

**BLOCKING (B-149O.1H-1): timestamp canonicalization is NOT injective
over the accepted semantic domain.** `datetime.fromisoformat` accepts
fractional-second precision finer than milliseconds (e.g.
`.0001`/100µs, `.0009`/900µs), and these are individually valid,
individually-accepted, semantically-distinct instants. Both
`2026-01-01T12:00:00.0001Z` and `2026-01-01T12:00:00.0009Z` truncate to
the identical canonical string `2026-01-01T12:00:00.000Z`, and therefore
produce **byte-identical canonical payloads and identical SHA-256
digests** despite representing two different instants 800 microseconds
apart. Reproduced directly (see
`test_BLOCKING_submillisecond_timestamps_collapse_to_identical_canonical_bytes`
in the new test file) — not repaired, per this phase's mandate.

Because HATP-REQ-075 requires that "signature/assertion verification
MUST NOT depend on ... ambiguous timestamp rendering," and Wave 4/5 will
eventually sign exactly these canonical bytes, this many-to-one
collision means the canonical bytes are not a faithful, unambiguous
representation of `issued_at` as currently specified: the contract does
not state that sub-millisecond precision is invalid input, so the
parser's acceptance of such input, combined with the renderer's lossy
truncation, is a genuine defect in the canonicalization boundary itself
— not a defect in either half considered alone.

**Timestamp collision verdict: TIMESTAMP CANONICALIZATION: NOT
INJECTIVE — BLOCKING CANONICALIZATION DEFECT.**

**Python-version portability (non-blocking observation):** this
repository's `pyproject.toml` declares `requires-python = ">=3.9"`, but
CI (`.github/workflows/pcae-governance.yml`) pins only `python-version:
"3.x"` (the runner's latest 3.x), and this verification ran under Python
3.14.5. `datetime.fromisoformat`'s acceptance of a colonless UTC offset
(`+0100`) and of fractional-second precision other than 0/3/6 digits
(e.g. `.0001`) is a CPython ≥3.11 behavior; on Python 3.9/3.10 those same
input strings would raise `ValueError` and be rejected as malformed
instead of accepted. The module's docstring states it duplicated the
timestamp parser specifically "to avoid reintroducing the Python 3.9
`fromisoformat` Z-suffix portability defect" — that specific defect (the
`Z` suffix) is indeed fixed by the manual substitution, but the broader
class of `fromisoformat` version-dependent leniency (colonless offsets,
non-standard fractional-digit counts) is not, and is not exercised by
any pinned-3.9 CI job. Recorded as an OBSERVATION, not Blocking, since it
is not currently exercised and does not by itself create a same-input
different-output ambiguity within a single interpreter version.

## 15. Signed-Payload Reconstruction (independent)

Independently derived (not from the module's own field-name constants)
from HATP-REQ-069's field list:

| Semantic field | Contract requires binding? | In canonical signed payload? |
|---|---|---|
| `proof_version` | Yes (HATP-REQ-068/117) | Yes |
| `principal_id` | Yes | Yes |
| `signer_key_id` (credential identity) | Yes | Yes |
| `provider_profile` | Yes | Yes |
| `repository_id` | Yes | Yes |
| `decision_record_id` | Yes | Yes |
| `decision_record_digest` | Yes | Yes |
| `binding_id` | Yes | Yes |
| `binding_digest` | Yes | Yes |
| `rollback_site` (operation family) | Yes | Yes |
| AG3 exact operation (`job_id`, `original_commit_sha`) | Yes, when AG3 | Yes |
| AG5 exact operation (`per_id`, `ecp_id`) | Yes, when AG5 | Yes |
| `issued_at` | Yes | Yes (subject to the B-149O.1H-1 truncation defect above) |

No additional HATP-001-required semantic field exists beyond this set
(HATP-REQ-070 explicitly excludes the raw canonical deployment path).
Every field in the table is present in `hatp_proof_to_document`'s output,
which is exactly what `canonicalize_hatp_proof_payload` serializes — the
entire proof model **is** the signed payload; there is no separate
envelope/signature/assertion layer in Wave 3 (correct, since no signing
exists yet — HATP-REQ-076 defers signature semantics to a future wave).
There is therefore no signature field that could accidentally be
included in the to-be-signed bytes (there is no signature field at all
yet).

**Self-selected-trust audit**: no field named or semantically equivalent
to a trusted root, verification key, attestation authority, registry
path, deployment root, trusted principal, or authorization status exists
anywhere in the schema (§9 above, the 13-field closed-schema attack
matrix). No `approved`/`trusted`/`authorized`/`human_present`/`valid`
field exists. The proof cannot represent a generic rollback approval
without a concrete AG3 or AG5 operation (HATP-REQ-071 — `rollback_site`
and its family-locked operation fields are unconditionally required).
The proof binds `decision_record_id`/`decision_record_digest` and
`binding_id`/`binding_digest` (external references + integrity digests)
but contains no field asserting its own approval verdict — it cannot
conflict with a CHGR/RAE decision because it makes no decision of its
own.

**Signed-payload completeness verdict: SIGNED PAYLOAD: COMPLETE FOR ALL
HATP-001 SECURITY SEMANTICS** (field-set-complete; the *canonicalization*
of one of those fields, `issued_at`, has the separate B-149O.1H-1
timestamp-injectivity defect documented above, which is a
canonicalization defect, not a field-coverage gap).

## 16. AG3/AG5 Exact Binding & Collision

Both `job_id` and `original_commit_sha` are present in the AG3 canonical
payload; both `per_id` and `ecp_id` are present in the AG5 canonical
payload (confirmed directly against `hatp_proof_to_document`'s output).
An AG3 proof and an AG5 proof constructed with deliberately identical
opaque values across every shared field (`principal_id`, `signer_key_id`,
`provider_profile`, `repository_id`, `decision_record_id`,
`decision_record_digest`, `binding_id`, `binding_digest`, `issued_at`)
and identical opaque strings in the family-specific slots (`job_id` =
`per_id` = `"same"`) were confirmed to canonicalize to **different**
bytes, because `rollback_site` differs (`"AG3"` vs. `"AG5"`) and the key
names themselves differ (`job_id`/`original_commit_sha` vs.
`per_id`/`ecp_id`) — the family discriminator is baked directly into the
canonical JSON key set, not inferred, so no AG3/AG5 collision is
possible by construction.

## 17. Field Lexical Validation

- **`repository_id`** (delegates to
  `repository_identity.is_valid_repository_instance_id`): accepts
  lowercase UUID4 strings. Also accepts **uppercase** UUID4 strings —
  because the underlying check is `str(parsed) == value.lower()`
  (compares the canonical lowercase form against the *lowered* input,
  not the raw input), an uppercase UUID passes validation. Rejects
  braced (`{...}`) and hyphenless forms (`str(parsed)` never equals
  those lowered). Rejects the all-zero UUID (not version 4). Rejects a
  version-1 UUID (`uuid.uuid1()`).
  **Non-blocking finding, F-149O.1H-1**: the accepted uppercase form is
  **not normalized** to the canonical lowercase form before being stored
  on the proof or serialized — an uppercase-vs-lowercase spelling of the
  *same* UUID canonicalizes to *different* signed bytes. This is exactly
  the ambiguous middle ground the verification brief warned against
  ("accepted-and-normalized... must be deterministic" — this
  implementation is accepted-and-**not**-normalized). It does not create
  a many-to-one collision (the opposite failure mode: one semantic
  identity, two possible byte forms), so it is classified non-blocking,
  but it is a real asymmetry against the digest/commit-SHA fields below,
  which correctly reject any non-lowercase form outright.
- **`decision_record_digest` / `binding_digest`** (SHA-256 hex, via
  `_require_sha256_hex`): only exactly-64-lowercase-hex-character
  strings accepted. Uppercase, 63-char, 65-char, non-hex, and
  algorithm-prefixed (`sha256:...`) forms are all rejected. One
  canonical form — no normalization ambiguity.
- **`original_commit_sha`** (via `_require_commit_sha`): accepts
  40-lowercase-hex (Git SHA-1) **or** 64-lowercase-hex (Git SHA-256,
  future-proofed) forms. Uppercase, 7-char (short SHA), 39-char, 41-char,
  and non-hex forms are all rejected. This matches the module's own
  regex (`^(?:[0-9a-f]{40}|[0-9a-f]{64})$`) and is a defensible, explicit
  choice not to assume SHA-1 forever.
- **`job_id`/`per_id`/`ecp_id`/`decision_record_id`/`binding_id`/`principal_id`/`signer_key_id`/`provider_profile`**:
  all validated only via `_require_nonempty_str` — any non-empty string
  is accepted, including whitespace-only (`" "`, `"\t"`, `"\n"`) and
  padded (`" alice "`) values. No silent trimming/normalization is
  performed — the exact input string is retained verbatim on the
  constructed proof and in the canonical payload (independently
  confirmed). This is a defensible reading of HATP-001, which imposes no
  charset restriction on these opaque identifiers beyond "field
  present"; documented here as an OBSERVATION (a future contract
  revision could tighten this) rather than a finding, since no silent
  semantic-altering normalization occurs.

## 18. Serializer / Domain Equivalence — HIGH PRIORITY, BLOCKING FINDING

The canonical serializer is exactly:

```python
json.dumps(document, sort_keys=True, separators=(",", ":"),
           ensure_ascii=False, allow_nan=False).encode("utf-8")
```

It accepts only a `HumanApprovalProvenanceProof` instance (via
`hatp_proof_to_document(proof)`, which dereferences typed attributes
such as `proof.rollback_site.value`) — it cannot be called with an
arbitrary `dict`, so there is no ambiguity risk from that direction.

**BLOCKING (B-149O.1H-2): the public dataclass constructors enforce
strictly less than the parser (`parse_hatp_proof`).**
`HumanApprovalProvenanceProof.__post_init__` performs exactly one check:
that `rollback_site` and the *type* of `operation_reference` agree
(AG3↔`Ag3OperationReference`, AG5↔`Ag5OperationReference`). It performs
**no** field-format validation whatsoever. Directly constructing a
`HumanApprovalProvenanceProof` (or `Ag3OperationReference`/
`Ag5OperationReference`) via the public constructor — an ordinary,
legitimate library-API call, not a private/internal API — succeeds, and
the resulting object canonicalizes and digests without error, for every
one of the following inputs the parser rejects:

| Attack | Parser (`parse_hatp_proof`) | Direct constructor |
|---|---|---|
| `repository_id="not-a-uuid"` | `InvalidProofSchemaError` | **Constructs successfully**; canonicalizes with the invalid string embedded verbatim |
| `decision_record_digest="not-a-digest"` | `InvalidProofSchemaError` | **Constructs successfully**; canonicalizes with the invalid string embedded verbatim |
| `proof_version=99` (unsupported) | `UnsupportedProofVersionError` | **Constructs successfully**; canonicalizes with `99` embedded |
| `proof_version=True` (boolean) | `UnsupportedProofVersionError` (explicit `isinstance(x, bool)` guard) | **Constructs successfully** — the `__post_init__` bool-guard does not exist at the constructor level; the resulting canonical JSON literally contains `"proof_version":true` (a boolean), not an integer `1`, a structurally different signed-payload shape than any parser-accepted document could ever produce |
| `issued_at="not-a-timestamp"` (non-canonical / unparseable) | `InvalidProofSchemaError` | **Constructs successfully**; the raw garbage string is embedded verbatim in the canonical payload, entirely bypassing `_parse_iso_timestamp`/`_canonical_timestamp_string` |
| `principal_id=""` (empty) | `InvalidProofSchemaError` | **Constructs successfully**; canonicalizes with an empty string |

Every one of these is reproduced directly in the new test file (`tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py::test_BLOCKING_constructor_*`
and `test_public_constructor_domain_verdict_is_bypass_not_equivalent`).
This matters because Wave 4/5 (a future verifier and provider adapter)
will necessarily need to *construct* `HumanApprovalProvenanceProof`
instances themselves (e.g. a provider adapter assembling a proof to sign
does not receive pre-validated JSON text — it builds the object
directly), and nothing in the current module prevents that future
caller from constructing and then canonicalizing/signing a
structurally-invalid proof (invalid repository ID, non-canonical
timestamp, or a `proof_version=True` payload that free-floats outside
the versioning scheme entirely) without ever going through
`parse_hatp_proof`.

**Constructor/parser domain verdict: PUBLIC CONSTRUCTOR DOMAIN: BYPASSES
STRUCTURAL SECURITY INVARIANTS.**

## 19. Golden Vectors — Independent Derivation

Two golden vectors (one AG3, one AG5) were built from scratch: the exact
input document was authored directly against HATP-REQ-069's field list,
and the *expected* canonical bytes/digest were computed with a
hand-written canonicalizer (`_independent_canonical_bytes` — sorted
keys, `json.dumps(key)`/`json.dumps(value, ensure_ascii=False)` per
pair, `,`-joined, UTF-8-encoded) that does not call, import, or reuse
`canonicalize_hatp_proof_payload`. The module's actual output was then
compared against this independently-computed expectation, avoiding the
circularity of "verify implementation output equals a constant copied
from the implementation's own test file."

- **AG3 golden vector**: input document with `repository_id =
  "11111111-1111-4111-8111-111111111111"`, `decision_record_digest =
  "a"*64`, `binding_digest = "b"*64`, `original_commit_sha = "c"*40`,
  `issued_at = "2026-01-01T12:00:00.000Z"`. Independently-computed
  digest: `d69567a62527f37825bc59fcb0564f21281511c21ffb0a07195c21dc8ff84212`
  (SHA-256, 64 lowercase hex characters) — **matches** the module's
  `digest_hatp_proof_payload` output exactly, and the independently
  computed canonical bytes match `canonicalize_hatp_proof_payload`'s
  output byte-for-byte.
- **AG5 golden vector**: analogous construction with `repository_id =
  "22222222-2222-4222-8222-222222222222"`, `decision_record_digest =
  "d"*64`, `binding_digest = "e"*64`. Independently-computed digest:
  `9efedce2594fcd123f4646c88278f8820eb274ea45d06afd9a9cbd3e5c845312`
  (verified programmatically at test time, not hand-transcribed) —
  **matches** exactly.

Both vectors are asserted in the new test file
(`test_ag3_golden_vector_independently_reproduced`,
`test_ag5_golden_vector_independently_reproduced`).

## 20. Digest Verification

`digest_hatp_proof_payload` returns `hashlib.sha256(canonical_bytes).hexdigest()`
— confirmed by direct source reading and by independently recomputing
`hashlib.sha256(canonicalize_hatp_proof_payload(proof)).hexdigest()` and
comparing. The digest is always exactly 64 lowercase hex characters
(confirmed on every test proof constructed in this phase). No SHA-1/MD5
substitution or truncation was found anywhere in the digest path.

## 21. Mutation Sensitivity Matrix

Every AG3 signed-payload field
(`principal_id`, `signer_key_id`, `provider_profile`, `repository_id`,
`decision_record_id`, `decision_record_digest`, `binding_id`,
`binding_digest`, `job_id`, `original_commit_sha`, `issued_at`) was
independently mutated one at a time against an otherwise-fixed baseline
document; every mutation changed the resulting SHA-256 digest. The same
was independently confirmed for the two AG5-specific fields (`per_id`,
`ecp_id`). A family-flip mutation (AG3 → AG5 with maximally-overlapping
opaque values) also changes the digest (§16 above). The sub-millisecond
timestamp probe is the sole case where mutation does **not** change the
digest — see B-149O.1H-1 (§14).

## 22. Domain Separation / Round Trip (assessment only)

HATP-001 does not itself specify a domain-separation prefix/tag
requirement for the canonical payload distinguishing it from other
project artifacts' canonical bytes (e.g. CHGR record digests, RAE
Binding digests) that happen to also be plain SHA-256 hex over
sorted-key JSON. This is recorded as an OBSERVATION only (not invented
as a requirement): if a future signing scheme reuses the same raw
SHA-256-over-canonical-JSON convention across multiple artifact types
without a type tag inside the payload, a signature over one artifact
type's canonical bytes could theoretically be indistinguishable, at the
raw-bytes level, from a signature over a different but coincidentally
byte-identical canonical payload of a *different* artifact type sharing
the same field-naming happenstance — this project's several
`_canonical_bytes`-style helpers (CHGR, RAE, now HATP) do not currently
carry an explicit type discriminator baked into the byte stream beyond
their own field names. No exploit was constructed (HATP's own field
names make an accidental collision with CHGR/RAE payloads extremely
unlikely in practice), and this contract does not require
domain-separation, so this is not raised as a finding — purely an
observation for a future contract-amendment phase to consider before
Wave 4/5 finalizes any provider-signing scheme.

Round-trip (`raw JSON → proof → canonical bytes → JSON parse → proof →
canonical bytes`) was independently confirmed byte-identical (§13).
`hatp_proof_to_document`/`canonicalize_hatp_proof_payload` are two
distinct, explicitly separate functions — the "full artifact" (plain
dict) vs. "signed payload" (canonical bytes) distinction is explicit in
the API surface, ready for a future provider to sign
`canonicalize_hatp_proof_payload`'s output specifically.

## 23. API / Vocabulary / Purity Audits

**Public callable/class inventory**, classified:

| Name | Classification |
|---|---|
| `HumanApprovalProvenanceProof`, `Ag3OperationReference`, `Ag5OperationReference`, `RollbackSite` | model |
| `HATPProofError`, `MalformedProofError`, `UnsupportedProofVersionError`, `InvalidProofSchemaError` | structural error vocabulary |
| `parse_hatp_proof` | structural parser |
| `hatp_proof_to_document` | canonical serializer (plain-dict form) |
| `canonicalize_hatp_proof_payload` | canonical serializer (bytes form) |
| `digest_hatp_proof_payload` | digest |
| `SUPPORTED_PROOF_VERSIONS` | constant |

No `trust/verification` category exists. No public name contains
`verify`/`trusted`/`authoriz`/`approval_present`/`hatp_valid` (confirmed
programmatically, substring-scanned against `dir(module)`, case-folded).
HATP-REQ-078's 13-member verification-status vocabulary
(`VALID`/`MISSING`/`MALFORMED`/`INVALID_SIGNATURE`/`UNKNOWN_SIGNER`/
`UNAUTHORIZED_SIGNER`/`REVOKED_SIGNER`/`INVALID_ATTESTATION`/
`USER_PRESENCE_NOT_PROVEN`/`WRONG_OPERATION`/`WRONG_REPOSITORY`/
`WRONG_DEPLOYMENT`/`EXPIRED`) does not appear as a value or symbol
anywhere in the canonicalized document or the module namespace (note:
`MalformedProofError`'s name shares the word "Malformed" with the
vocabulary's `MALFORMED` member by coincidence of English, but it is a
structural exception class, not a verification-status value, and is
never assigned to a HATP-REQ-078-typed field).

**Dependency/import audit** (AST-walked, not grep-only): the module
imports exactly `__future__`, `hashlib`, `json`, `re`, `dataclasses`,
`datetime`, `enum`, `typing`, and `pcae.core.repository_identity`
(specifically only `is_valid_repository_instance_id`). Zero imports of
`hatp_bootstrap`, `HATPTrustStore`, `resolve_deployment_authorization`,
`inspect_bootstrap_environment`, `rollback_approval_evidence`,
`permission_broker*`, `mutation_permission`, `agent.py`, or
`commands/agent.py`. Confirmed both by AST walk and by the fact that
every other mention of those names in the source file is inside a
docstring/comment (grep-confirmed, §dependency audit above).

**Purity audits**: no `open(`, `Path(`, `os.chdir`, `os.getcwd`,
filesystem read, network call, `datetime.now(`/`.utcnow(`, or `random.`
call exists anywhere in the module source (confirmed by source-string
scan, not just docstring claims). `TZ`-environment independence and
survival of a deleted-CWD scenario were independently re-exercised and
confirmed (both are asserted in the new test file). Locale independence
follows directly from the purity finding — no locale-sensitive
formatting call (`str.format` with locale, `locale.` module, or
`strftime` format codes that vary by locale) is used; `strftime("%Y-%m-%dT%H:%M:%S.%f")`
uses only numeric format codes, which are locale-invariant in Python's
`datetime` implementation.

## 24. Environment Independence & Boundaries

- No hardware-dependency import (`fido2`, `webauthn`, `piv`, `pyscard`,
  `ykman`, `cryptography`) exists anywhere in the module — confirmed.
- `git diff 84cb9b15..HEAD -- pyproject.toml` is empty: no new
  production dependency was added.
- `git diff --stat 01c7fb74..HEAD -- src/pcae/core/repository_identity.py
  src/pcae/core/hatp_bootstrap.py src/pcae/core/rollback_approval_evidence.py`
  is empty: all three files remain byte-unchanged since 149O.1G (this is
  additionally asserted as a permanent regression test in the new test
  file, `test_hatp_contract_and_wave_1_2_files_byte_unchanged_since_149o_1g`).
- `git diff --name-only 84cb9b15..HEAD -- docs/contracts/` is empty:
  HATP-001 remains byte-unchanged.
- `git diff --name-only 84cb9b15..HEAD -- src/pcae/` returns exactly one
  file: this phase's own new test file lives under `tests/`, not
  `src/pcae/`, so this confirms **zero production-code changes** by
  149O.1H itself (the 149O.1G diff pre-dates this phase and was already
  accounted for in §2).

## 25. Findings Summary

| ID | Severity | Description |
|---|---|---|
| B-149O.1H-1 | **BLOCKING** | Timestamp canonicalization is not injective: sub-millisecond-distinct, individually-accepted `issued_at` values truncate to identical canonical bytes/digest (§14). |
| B-149O.1H-2 | **BLOCKING** | Public dataclass constructors enforce strictly less than the parser; direct construction bypasses every field-format invariant except AG3/AG5 family agreement, including the `proof_version` boolean-guard (§18). |
| F-149O.1H-1 | NON-BLOCKING | `repository_id` accepts uppercase UUID4 strings without normalizing them to the canonical lowercase form used by `decision_record_digest`/`binding_digest`/`original_commit_sha`, so a case-variant of the same UUID canonicalizes to different bytes (§17). |
| F-149O.1H-2 | OBSERVATION | Opaque identifier fields (`principal_id`, `signer_key_id`, etc.) accept whitespace-only/padded values; retained verbatim, no silent trimming (defensible per contract, but worth tightening in a future revision) (§17). |
| F-149O.1H-3 | OBSERVATION | `datetime.fromisoformat`'s acceptance of colonless UTC offsets and non-standard fractional-digit counts is a Python ≥3.11 behavior; the declared `>=3.9` floor is not exercised by CI, so this specific class of the "Z-suffix portability defect" the module's docstring says it avoided is only partially avoided (§14). |
| F-149O.1H-4 | OBSERVATION | No domain-separation tag distinguishes HATP canonical payload bytes from other project artifacts' canonical bytes at the raw-byte level; not required by HATP-001, flagged for a future signing-scheme design discussion only (§22). |
| F-149O.1H-5 | OBSERVATION | A lone UTF-16 surrogate is accepted at parse time but rejected only at canonicalization time (`UnicodeEncodeError`), not at parse time; fails closed, but slightly later in the pipeline than ideal (§12). |

B-149O-1 through B-149O-4 remain OPEN, unaffected by this phase (no
attempt was made to close them; they are outside Wave 3's scope).
F-149O.1C-2 remains editorial debt only.

## 26. Verdicts

- **F-149O.1C-1 verdict: F-149O.1C-1 INDEPENDENTLY CONFIRMED IMPLEMENTED
  — STRICT CLOSED PROOF SEMANTICS ENFORCED** (at the parser boundary).
- **Structural/trust separation verdict**: successful parse,
  canonicalization, and digest generation NEVER imply HATP VALID,
  authorized signer, human presence, or `approval_present=True` — no
  such symbol, field, or vocabulary member exists anywhere in the module
  or its output (§23).
- **Timestamp collision verdict: TIMESTAMP CANONICALIZATION: NOT
  INJECTIVE — BLOCKING CANONICALIZATION DEFECT.**
- **Constructor/parser domain verdict: PUBLIC CONSTRUCTOR DOMAIN:
  BYPASSES STRUCTURAL SECURITY INVARIANTS.**
- **Signed-payload completeness verdict: SIGNED PAYLOAD: COMPLETE FOR
  ALL HATP-001 SECURITY SEMANTICS** (field coverage is complete; the
  timestamp field's *canonicalization* has the separate B-149O.1H-1
  defect, tracked independently).
- **Canonicalization verdict: CANONICALIZATION: BLOCKING AMBIGUITY /
  COLLISION FOUND** (B-149O.1H-1).
- **Overall Wave-3 verification verdict: NOT VERIFIED — BLOCKING HATP
  WAVE 3 FINDINGS.**
- **HATP PRODUCTION: NOT READY.** (Independent of the Wave-3 verdict —
  Wave 4/5/6/7 remain entirely unimplemented.)

## 27. Regressions

| Suite | Result |
|---|---|
| `tests/test_hatp_proof_models.py` + `tests/test_hatp_canonical_serialization.py` + `tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py` | 100 passed |
| Wave-1/2 foundation (`test_repository_identity.py`, `test_hatp_bootstrap_foundation.py`, `test_phase_149o_1e_...py`, `test_phase_149o_1f_...py`, `test_phase_149o_1f_1_...py`) | 103 passed |
| 149O.1F.2 independent re-verification suite | 90 passed |
| HATP contract + implementation-plan regression (`test_phase_149o_1c_...py`, `test_phase_149o_1d_...py`) | 127 passed |
| Broad RAE/Permission-Broker/agent regression (`-k "rae or permission_broker or rollback_approval or agent or mutation_permission"`, `-n auto`) | 5 failed / 5631 passed — the 5 failures reproduce the same pre-existing, unrelated tests already documented as pre-existing by 149O.1G (`test_149o_fake_chgr_record_plus_fake_publication_receipt`, `test_149o_fake_binding_plus_fake_creation_registration`, `test_149o_full_end_to_end_forgery_zero_legitimate_api_calls`, `test_149o_copied_registration_under_new_key_with_matching_fields_rejected`, `test_permission_broker_consumer_scope_inventory`); not attributable to this phase (no `src/pcae/` file changed by 149O.1H) |
| `python -m pytest -m fast_green -n auto -q` | 4531 passed — identical to the entering baseline (149O.1G left it at 4531); no regression, no new Fast Green tests added by this verification-only phase (new tests intentionally not marked `fast_green`) |
| New independent verification suite (`tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py`) | 166 passed (includes the two BLOCKING-finding tests, which pass because they assert the *current, defective* behavior as documented, per "record it, reproduce it, do NOT repair it") |

This phase is verification-only; the full whole-repository suite was not
re-run in full (the targeted suites above, plus the broad
RAE/PB/agent/mutation_permission regression, are sufficient to establish
that this phase touched zero production code and introduced zero
regressions — full-suite drift unrelated to `src/pcae/` is out of scope
for a phase that changed no production file).

## 28. Next Phase Recommendation

Per the governing brief's decision logic: because accepted timestamp
precision collapses semantically distinct instants into identical
canonical bytes (B-149O.1H-1), **and** direct model construction
bypasses invariants enforced by the parser (B-149O.1H-2), the overall
verdict is **NOT VERIFIED**. Recommended next phase: **149O.1H.1 — HATP
Timestamp Canonicalization + Constructor-Domain Hardening**, a narrow
repair phase scoped to exactly these two defects:

1. Make `_canonical_timestamp_string` reject (not silently truncate)
   `issued_at` input carrying sub-millisecond precision, OR round
   instead of truncate AND additionally reject any input whose rounding
   would itself be ambiguous — whichever HATP-001 amendment (if any is
   needed) or plain implementation clarification the repair phase
   determines is correct; the essential fixed property is that the
   accepted-input-to-canonical-bytes mapping must become injective.
2. Move field-format validation (repository ID, digest, commit SHA,
   version, timestamp canonicality, non-empty checks) out of
   parser-only code and into `HumanApprovalProvenanceProof.__post_init__`
   (and the two operation-reference dataclasses' own `__post_init__`s),
   so that direct construction and `parse_hatp_proof` share one
   invariant-enforcing code path and cannot diverge.

This phase (149O.1H) does not implement either repair — per its mandate,
it records and reproduces both defects only. Wave 4 (HATP Verification
Engine Implementation) should not begin until 149O.1H.1 resolves both
BLOCKING findings, since Wave 4 will build on exactly this canonical-byte
boundary.

## 29. Explicit Confirmations

HATP-001 v1.0 remained byte-unchanged. No production source was
modified by Phase 149O.1H. Wave 1 repository identity remained
unchanged. Wave 2 bootstrap/trust-store foundation remained unchanged.
B-149O.1F-1 remains independently confirmed closed; this phase found no
contrary evidence. Wave 3 was independently reconstructed rather than
accepted from the 149O.1G implementation report. F-149O.1C-1 was
independently re-evaluated. F-149O.1C-2 remains editorial debt only.
HATP signature verification was not implemented. Provider attestation
verification was not implemented. Trusted-signer lookup was not
implemented. Human-presence verification was not implemented. A real
FIDO2 provider was not implemented. A real PIV provider was not
implemented. A human approval CLI was not implemented. A bootstrap/admin
CLI was not implemented. A Class-B OS security boundary was not
provisioned. Current HATP deployment remains NOT READY. A structurally
valid HATP proof does not imply HATP VALID. No production rollback
request derives `approval_present=True` from HATP. B-149O-1 through
B-149O-4 remain OPEN. RAE production integration was not implemented.
AG3 Permission Broker integration was not implemented. AG5 Permission
Broker integration was not implemented. Rollback execution behavior did
not change. RAE-001 v1.0 remains unchanged. RWMPC-001 v1.0 remains
unchanged. PBPC-001 v1.2 remains unchanged. PBPA-001 v1.0 remains
unchanged. CHGR-001 remains unchanged. IWC confirmation remains distinct
from approval. AESIC/AEM remain disclosure-only. No illegal CHGR/TAM
composition was introduced. POL-001..012 meaning was not changed.
POL-013+ was not added. TK1/TK2/TK3 remain deferred. Runtime Enforcement
behavior did not change. Prompt Generation, Prompt Dispatch, and
agent-invocation capability were not implemented. Runtime remains
Observed, maximum capability remains observe, and execution availability
remains unavailable.
