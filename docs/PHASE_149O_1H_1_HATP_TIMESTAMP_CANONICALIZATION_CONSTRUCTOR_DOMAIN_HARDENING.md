# Phase 149O.1H.1 — HATP Timestamp Canonicalization + Constructor-Domain Hardening

## Scope

Narrow Wave-3 production repair of exactly two Blocking findings from
Phase 149O.1H's independent verification of
`src/pcae/core/human_approval_trusted_provenance.py`: `B-149O.1H-1`
(timestamp canonicalization non-injective) and `B-149O.1H-2` (public
constructor domain bypasses parser invariants). Owns
`src/pcae/core/human_approval_trusted_provenance.py`, focused Wave-3
tests, and this document. No Wave 4 verification engine, no signature/
attestation/human-presence verification, no trusted-signer resolution,
no FIDO2/PIV provider, no Class-B OS provisioning, no RAE/Permission
Broker/AG3/AG5 wiring. HATP-001 v1.0 is byte-unchanged; the
independently verified requirement span remains HATP-REQ-001..117 (117
requirements).

## Baseline (confirmed before any edit)

- `git status --short`: clean. `origin/main..HEAD`: 0 commits.
- `pcae health`/`pcae check`/`pcae status coherence`: healthy / passed /
  coherent.
- `pcae push check`: nothing_to_push.
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`.
- `pcae phase-report show --latest` + `pcae phase-report reconcile
  --phase-id 149O.1H`: 149O.1H confirmed `completed`, reconciled,
  `already_dispatched`; verdict `NOT VERIFIED — BLOCKING HATP WAVE 3
  FINDINGS` (`B-149O.1H-1`, `B-149O.1H-2` both open).
- `pcae doctor task-memory`: 4 pre-existing `tasks/DONE.md` sync
  warnings, unrelated to this phase, unchanged by this phase.
- Wave 3 pre-existing suites: `tests/test_hatp_proof_models.py` +
  `tests/test_hatp_canonical_serialization.py` +
  `tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py`:
  100 passed (entering baseline, matches 149O.1G/149O.1H's own record).
- `tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py`:
  166 passed (entering baseline; includes the two Blocking findings
  encoded as tests asserting *current defective behavior*, per that
  phase's verification-only mandate).

## Pre-repair reproduction (both Blocking findings, before any edit)

### B-149O.1H-1 — timestamp canonicalization non-injective

```python
doc_a = {..., "issued_at": "2026-01-01T12:00:00.0001Z"}
doc_b = {..., "issued_at": "2026-01-01T12:00:00.0009Z"}
pa = parse_hatp_proof(json.dumps(doc_a))
pb = parse_hatp_proof(json.dumps(doc_b))
pa.issued_at == pb.issued_at == "2026-01-01T12:00:00.000Z"          # True
canonicalize_hatp_proof_payload(pa) == canonicalize_hatp_proof_payload(pb)  # True
digest_hatp_proof_payload(pa) == digest_hatp_proof_payload(pb)              # True
```

Root cause: `_canonical_timestamp_string` rendered via
`strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"`. `%f` always produces six
microsecond digits; slicing the last three characters off **truncates**
(never rounds) to millisecond precision. `_parse_iso_timestamp` placed
no lower bound on accepted fractional precision, so two individually
valid, individually accepted, semantically distinct instants 800
microseconds apart collapsed into byte-identical canonical payloads and
identical SHA-256 digests — a many-to-one collision in the eventual
Wave 4/5 cryptographic signing boundary.

### B-149O.1H-2 — public constructor domain bypasses parser invariants

```python
bad = HumanApprovalProvenanceProof(
    proof_version=True, principal_id="", signer_key_id="k", provider_profile="P",
    repository_id="not-a-uuid", decision_record_id="d", decision_record_digest="not-hex",
    binding_id="b", binding_digest="not-hex", rollback_site=RollbackSite.AG3,
    operation_reference=Ag3OperationReference(job_id="j", original_commit_sha="c" * 40),
    issued_at="not-a-timestamp",
)
canonicalize_hatp_proof_payload(bad)   # succeeds -- no exception
```

Root cause: `HumanApprovalProvenanceProof.__post_init__` checked only
AG3/AG5 family-vs-operation-reference-type agreement. No field-format
validation (`proof_version` type/support/boolean, `repository_id`
format, digest format, `issued_at` parseability, non-empty required
identifiers) existed on the constructor path, so it accepted a strict
superset of what `parse_hatp_proof` accepted for every one of those
invariants, and the resulting object survived canonicalization/
digesting unchanged.

## Timestamp repair decision

HATP-REQ-075 requires canonical serialization to be *deterministic* and
independent of "ambiguous timestamp rendering"; it does not itself
mandate millisecond precision (confirmed by direct reading of
HATP-REQ-067..077/117, contract §19-21/29). Two contract-compatible
repair strategies were available:

- **Strategy A** (preserve all accepted precision): widen the canonical
  renderer to full microsecond precision. Rejected: it would change the
  canonical byte format for *every* existing input (including the
  all-zero-microsecond fixtures every pre-existing golden vector and
  test uses), invalidating the 149O.1G golden digests without any
  contract requirement forcing that change, and widening this narrow
  repair's blast radius well beyond the two Blocking findings.
- **Strategy B** (restrict accepted precision to milliseconds) —
  **selected**: reject any `issued_at` input carrying non-zero
  fractional-second precision below one millisecond, before model
  acceptance, leaving the existing millisecond-precision canonical
  renderer and every existing millisecond-precision fixture/golden
  vector untouched.

Strategy B is the smaller, fully contract-compatible change: it
narrows the *accepted domain* rather than the *canonical format*, and
every existing valid fixture in this repository already carries
millisecond-or-coarser precision, so it requires no compatibility
break.

### Accepted timestamp domain (post-repair)

An `issued_at` value is accepted if and only if:

1. it is a non-empty string;
2. `_parse_iso_timestamp` (unchanged parsing logic — Z-suffix
   substitution + `datetime.fromisoformat`, matching
   `repository_identity.py`'s own duplicated parser) successfully
   parses it to a timezone-aware `datetime`;
3. the parsed instant's `microsecond` component is an exact multiple of
   1000 (i.e., its fractional-second precision, however many textual
   digits it was written with, resolves to a whole number of
   milliseconds).

Timestamps failing any of these three now raise
`InvalidProofSchemaError` — including the previously-accepted
sub-millisecond-precision forms.

### Canonical timestamp representation (unchanged)

`_canonical_timestamp_string` is unchanged: UTC, millisecond precision,
`YYYY-MM-DDTHH:MM:SS.mmmZ`. It is now only ever invoked on a `datetime`
already guaranteed (by `_require_issued_at`) to satisfy
`microsecond % 1000 == 0`, so its `%f`-slicing is exact truncation of
trailing zero digits, never a lossy operation over an accepted value.

### Injectivity argument

Let `D` be the accepted domain post-repair: timezone-aware instants
whose microsecond component is a multiple of 1000. The canonical
renderer maps each such instant to `strftime("%f")[:-3]`, i.e. its
millisecond count zero-padded to three digits. Two distinct instants in
`D` differing by at least one millisecond necessarily differ in at
least one of (year, month, day, hour, minute, second, millisecond) —
the exact fields captured by the canonical string — so their canonical
strings differ. Two instants that denote literally the same UTC instant
(e.g. `Z` vs. an equivalent explicit offset) legitimately canonicalize
identically — this is timezone equivalence, not a collision. No two
*distinct* accepted instants can produce the same canonical string:
canonicalization is injective over `D`.

### Timezone equivalence (preserved)

`2026-01-01T12:00:00Z` and `2026-01-01T13:00:00+01:00` denote the same
UTC instant and continue to canonicalize identically
(`test_equivalent_offsets_canonicalize_identically`,
`test_timezone_equivalent_instants_canonicalize_identically` in the
pre-existing 149O.1H suite, unchanged and still passing).

### Python-version compatibility

The repair adds one post-parse numeric check
(`parsed.microsecond % 1000 != 0`) operating on the already-parsed
`datetime` object; it does not change `_parse_iso_timestamp`'s parsing
logic or its `>=3.9` compatibility shim (`Z`-suffix substitution before
`fromisoformat`). Python 3.9/3.10's own stricter `fromisoformat`
(rejecting fractional-digit counts other than 0/3/6, per 149O.1H's own
non-blocking portability observation) and this repair's explicit
microsecond-modulus check are independently sufficient and mutually
reinforcing: on any supported Python version, no sub-millisecond-
precision instant can reach model acceptance.

## Constructor-domain repair architecture

A shared `_require_*` validator layer was introduced (not duplicated
per-`__post_init__` logic):

- `_require_proof_version(value) -> int` — exact-integer check
  (`isinstance(value, bool)` explicitly excluded, since `bool` is an
  `int` subclass in Python — the "boolean trap") plus
  `SUPPORTED_PROOF_VERSIONS` membership.
- `_require_repository_instance_id(value) -> str` — delegates to the
  pre-existing `is_valid_repository_instance_id` (Wave 1, unchanged).
- `_require_rollback_site(value) -> RollbackSite` — accepts an
  already-typed `RollbackSite` or its exact string value; rejects
  anything else.
- `_require_issued_at(value, *, context) -> str` — see timestamp
  section above.
- `_require_nonempty_str`, `_require_sha256_hex`, `_require_commit_sha`
  — pre-existing (149O.1G) field-format validators, unchanged, now also
  called from `__post_init__`.

`parse_hatp_proof` → `_build_proof_from_document` now calls these same
functions (replacing its own inlined `proof_version`/`repository_id`/
`issued_at` checks) before constructing the model; the model's own
`__post_init__` methods (`HumanApprovalProvenanceProof`,
`Ag3OperationReference`, `Ag5OperationReference`) call the identical
functions again. There is exactly one semantic-validation
implementation per invariant; the parser and every constructor call
site share it, per the governing prompt's "no drifting second
semantic-validation path" requirement. Document-shape-only checks
(closed field-set enforcement, wrong-family field detection, duplicate
JSON key rejection) remain parser-only, since they operate on raw
`dict`/JSON structure that a typed constructor call never receives —
this is expected, not a residual domain gap (governing prompt item
23/§Recommended-Next-Phase-Logic "if only JSON-specific properties
differ... expected and not a constructor-domain mismatch").

`HumanApprovalProvenanceProof.__post_init__` additionally normalizes,
via `object.__setattr__` (the dataclass remains `frozen=True`), a
directly-constructed instance's `rollback_site` (raw `"AG3"`/`"AG5"`
string → `RollbackSite` enum member) and `issued_at` (any valid,
non-canonical-but-accepted representation → the same canonical
millisecond string the parser would produce), so parser-built and
directly-built instances of equal semantic content are byte-identical
after canonicalization.

## Parser/constructor equivalence matrix

For each of the following semantic invalidities, both `parse_hatp_proof`
and direct `HumanApprovalProvenanceProof`/`Ag3OperationReference`/
`Ag5OperationReference` construction now raise (parametrized in
`tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py::test_parser_and_constructor_equivalence_matrix`
/ `test_ag5_parser_and_constructor_equivalence_matrix`, both families):

| Case | Result |
|---|---|
| invalid `repository_id` | both reject |
| invalid `decision_record_digest` | both reject |
| invalid `binding_digest` | both reject |
| empty `principal_id` | both reject |
| empty `signer_key_id` | both reject |
| empty `provider_profile` | both reject |
| empty `decision_record_id` | both reject |
| empty `binding_id` | both reject |
| malformed `issued_at` | both reject |
| naive (no-timezone) `issued_at` | both reject |
| sub-millisecond `issued_at` | both reject |
| unsupported `proof_version` (2) | both reject |
| `proof_version=True` | both reject |
| `proof_version=False` | both reject |

Plus, independently: empty AG3 `job_id`, invalid AG3
`original_commit_sha`, empty AG5 `per_id`/`ecp_id`, AG3/AG5
family-vs-reference-type mismatch — all reject on both the parser path
(via document-shape + field checks) and the direct-constructor path
(via `Ag3OperationReference`/`Ag5OperationReference.__post_init__` and
`HumanApprovalProvenanceProof.__post_init__`).

## Boolean proof-version result

`proof_version=True` and `proof_version=False` are both rejected by
`_require_proof_version` on both the parser and constructor paths
(`isinstance(value, bool)` excluded before the `SUPPORTED_PROOF_VERSIONS`
membership check, since `isinstance(True, int) is True` in Python).
Verified directly by
`test_constructor_rejects_invalid_proof_version[True]`/`[False]` and
`test_parser_rejects_invalid_proof_version_boolean_true`/`_false`.

## Golden-vector disposition

Unchanged. The canonical timestamp *rendering* (millisecond precision,
`YYYY-MM-DDTHH:MM:SS.mmmZ`) was not altered — only the *accepted input
domain* was narrowed to reject sub-millisecond precision before
rendering. Every pre-existing fixture in
`tests/test_hatp_canonical_serialization.py` and
`tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py`
already carries exact millisecond (or coarser) precision, so their
golden bytes/digests are unaffected. Independently re-confirmed in this
phase's new suite
(`test_ag3_golden_digest_unchanged_by_repair` /
`test_ag5_golden_digest_unchanged_by_repair`) by recomputing the SHA-256
digest directly from `test_hatp_canonical_serialization.py`'s own
`_AG3_GOLDEN_BYTES`/`_AG5_GOLDEN_BYTES` constants:

- AG3: `bafc5bc9bf7865652be0dcdb47ca2906666d43fe963e7da7f593bac201efdc83`
- AG5: `480422914a8a8e90acf8ee1c4ed4dc0adb6b0a3ef294266bb2fcf8a479b6aeaf`

(Note: the governing phase prompt's own text cited different
placeholder digest values for these two golden vectors. Those values do
not match this repository's actual `_AG3_GOLDEN_BYTES`/
`_AG5_GOLDEN_BYTES` fixtures under SHA-256 — independently recomputed
and cross-checked against `tests/test_hatp_canonical_serialization.py`'s
own passing `test_ag3_golden_digest`/`test_ag5_golden_digest` tests, both
of which continue to pass unchanged after this repair. Per this phase's
own governing instruction ("confirm rather than assume"), the values
recorded in this document and in the new repair suite are the
independently confirmed, actually-produced digests, not the prompt's
placeholder text.)

## 149O.1H suite disposition

Both Blocking-finding tests and the named verdict test in
`tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py`
are updated in place (not deleted), following the same convention
`hatp_bootstrap.py`'s 149O.1F.1 repair used for its own historical
verification suite: each test's docstring is rewritten to record the
historical finding and the repair that closed it, and the assertion is
flipped from "this bypass succeeds" to "this bypass now fails
identically to the parser." Updated tests:

- `test_BLOCKING_submillisecond_timestamps_collapse_to_identical_canonical_bytes`
- `test_BLOCKING_constructor_accepts_invalid_repository_id_parser_rejects`
- `test_BLOCKING_constructor_accepts_invalid_digest_parser_rejects`
- `test_BLOCKING_constructor_accepts_unsupported_version_parser_rejects`
- `test_BLOCKING_constructor_accepts_boolean_version_parser_rejects`
- `test_BLOCKING_constructor_accepts_noncanonical_timestamp_parser_rejects`
- `test_BLOCKING_constructor_accepts_empty_principal_id_parser_rejects`
- `test_public_constructor_domain_verdict_is_bypass_not_equivalent`

All 166 tests in that file pass after the update (same total as the
entering baseline — no tests were added to or removed from that file;
only assertions inside these 8 were flipped).

## New repair suite

`tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py`
(93 new tests): historical collision-pair closure, timestamp boundary
matrix (0/1/100/999/1000/1001/999000/999999 microseconds), distinct-
accepted-instants property sweep, equivalent-offset matrix, naive/
malformed-timestamp rejection, round-trip canonical timestamp,
constructor-domain hardening for `proof_version` (including the
boolean trap) and every other common field, `Ag3`/`Ag5`
operation-reference hardening, parser/constructor equivalence matrix
(both families), positive controls, round-trip after direct
construction, golden-vector cross-check, and frozen-model regression.

## Production diff classification

Every hunk in `src/pcae/core/human_approval_trusted_provenance.py`
classifies as exactly one of:

- **TIMESTAMP_DOMAIN** — `_require_issued_at`'s microsecond-modulus
  acceptance check; `_build_proof_from_document`'s replacement of its
  inlined timestamp-parse-and-render block with a call to
  `_require_issued_at`.
- **TIMESTAMP_CANONICALIZATION** — `_canonical_timestamp_string`'s
  updated docstring recording the injectivity precondition (the
  function's rendering logic itself is byte-for-byte unchanged).
- **SHARED_STRUCTURAL_VALIDATOR** — new `_require_proof_version`,
  `_require_repository_instance_id`, `_require_rollback_site`
  functions.
- **CONSTRUCTOR_HARDENING** — `HumanApprovalProvenanceProof.__post_init__`
  full rewrite; new `Ag3OperationReference.__post_init__`/
  `Ag5OperationReference.__post_init__`.
- **PARSER_VALIDATOR_UNIFICATION** — `_build_proof_from_document`'s
  replacement of its inlined `proof_version`/`repository_id` checks
  with calls to the new shared validators.

No unrelated hunk exists. `git diff --name-only HEAD -- src/pcae/`
shows exactly one file:
`src/pcae/core/human_approval_trusted_provenance.py`.

## Regressions

- `tests/test_hatp_proof_models.py` + `tests/test_hatp_canonical_serialization.py`
  + `tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py`:
  **100 passed** (identical to entering baseline).
- `tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py`:
  **166 passed** (identical total; 8 tests' assertions flipped in place
  per "149O.1H suite disposition" above).
- `tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py`
  (new): **93 passed**.
- Combined Wave-3 + 149O.1H + repair suites: **359 passed**.
- Foundation regression (`test_repository_identity.py` +
  `test_hatp_bootstrap_foundation.py` +
  `test_phase_149o_1e_hatp_repository_identity_trust_store_foundation.py`
  + `test_phase_149o_1f_hatp_repository_identity_trust_store_foundation_independent_verification.py`
  + `test_phase_149o_1f_1_hatp_production_trust_store_path_hardening.py`):
  **103 passed** (identical to entering baseline).
- 149O.1F.2 independent re-verification suite: **90 passed** (identical
  to entering baseline).
- HATP contract independent-verification suite
  (`test_phase_149o_1c_...`): passed (subset of the 127-test contract+
  plan combined baseline).
- HATP implementation-plan suite (`test_phase_149o_1d_...`): **1 test,
  `TestProductionBoundaryUnchanged::test_no_src_pcae_files_modified_this_phase`,
  fails while this phase's changes remain uncommitted.** This test
  asserts `git diff --name-only HEAD -- src/pcae/` is empty — i.e. it
  checks the *live, uncommitted* working-tree diff against `HEAD`, not
  a historical commit range scoped to Phase 149O.1D. It is expected to
  fail during the working session of *any* phase (including this one)
  that legitimately touches `src/pcae/**` and has not yet committed,
  and is expected to pass again once this phase's changes are
  committed (confirmed: the same command run against a clean tree, as
  recorded in this phase's own baseline section above, showed zero
  diff). Not a regression attributable to this repair; re-verify after
  commit as part of `pcae phase complete`.
- RAE/Permission-Broker/agent regression
  (`pytest tests/ -k 'rae or permission_broker or rollback_approval or
  agent or mutation_permission' -n auto`): **5 failed / 5631 passed** —
  identical count to 149O.1H's own recorded baseline; all 5 failures
  independently confirmed to be the same pre-existing, unrelated tests
  already documented by prior phases
  (`test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`
  ×4, `test_phase_148f_permission_broker_production_consumption_independent_verification.py`
  ×1).
- Fast Green (`pytest -m fast_green -n auto`): **4531 passed**,
  identical to the entering baseline. No regression. This phase's new
  repair tests are intentionally not added to Fast Green (consistent
  with 149O.1H's own convention).

## Boundary/import/purity audits

- `git diff --name-only HEAD -- docs/contracts/`: empty.
- `git diff --name-only HEAD -- src/pcae/core/repository_identity.py
  src/pcae/core/hatp_bootstrap.py`: empty (Wave 1/2 untouched).
- `git diff --name-only HEAD -- src/pcae/core/rollback_approval_evidence.py`:
  empty (RAE untouched).
- `git diff --name-only HEAD -- src/pcae/core/permission_broker.py
  src/pcae/core/permission_broker_foundation.py
  src/pcae/core/mutation_permission.py`: empty (Permission Broker
  untouched).
- `git diff --name-only HEAD -- src/pcae/core/agent.py
  src/pcae/commands/agent.py`: empty (agent untouched).
- AST-confirmed import set: exactly
  `{__future__, hashlib, json, re, dataclasses, datetime, enum, typing,
  pcae.core.repository_identity}` — byte-identical to 149O.1G/149O.1H's
  own confirmed set; no new import added.
- Source-scan confirmed: no `open(`, `Path(`, `socket`, `requests`,
  `urllib`, `datetime.now(`, `datetime.utcnow(`, `os.getcwd`,
  `os.chdir`, or `random.` reference anywhere in the module.
- Public symbol audit: no new public callable/name added beyond the
  pre-existing set; no verification/trust-suggestive name introduced.

## Findings status

- `B-149O.1H-1`: **CLOSED — TIMESTAMP CANONICALIZATION INJECTIVE OVER
  ACCEPTED DOMAIN.**
- `B-149O.1H-2`: **CLOSED — PUBLIC CONSTRUCTOR DOMAIN MATCHES
  STRUCTURAL PARSER DOMAIN.**
- `F-149O.1C-1`: remains **INDEPENDENTLY CONFIRMED IMPLEMENTED** —
  closed-schema/unknown-field/duplicate-key enforcement is untouched by
  this repair (all three pre-existing suites covering it pass
  unchanged).
- `F-149O.1C-2`: remains editorial debt only, unaffected.
- `B-149O.1F-1`: remains confirmed closed; no contrary evidence
  discovered (`hatp_bootstrap.py` byte-unchanged this phase).
- `B-149O-1` through `B-149O-4`: remain OPEN, unaffected
  (`rollback_approval_evidence.py` byte-unchanged this phase).

## Timestamp verdict

**TIMESTAMP CANONICALIZATION: INJECTIVE OVER ACCEPTED SEMANTIC DOMAIN.**

## Constructor-domain verdict

**PUBLIC CONSTRUCTOR DOMAIN: EQUIVALENT TO OR STRICTER THAN PARSER
SEMANTIC DOMAIN.**

## Wave-3 repair verdict

**HATP WAVE 3 BLOCKING FINDINGS REPAIRED — READY FOR INDEPENDENT
RE-VERIFICATION.**

Per the governing prompt's item 123, this is a repair-phase
self-assessment, not an independent verification: Wave 3's status is
`REPAIRED — PENDING INDEPENDENT RE-VERIFICATION`, not `VERIFIED`.

## HATP production readiness

Remains **NOT READY**. No Wave 4 verification engine, trusted-signer
resolution, attestation verification, human-presence verification, real
FIDO2 provider, real PIV provider, Class-B deployment provisioning, or
RAE/HATP integration exists. A structurally valid HATP proof still does
NOT imply HATP `VALID`. No production rollback request derives
`approval_present=True` from HATP as a result of this phase.

## Explicit confirmations

HATP-001 v1.0 remains byte-unchanged. The independently verified HATP
requirement count remains 117. Wave 1 repository identity remains
unchanged. Wave 2 bootstrap/trust-store foundation remains unchanged.
`B-149O.1F-1` remains confirmed closed; no contrary evidence was
discovered. `F-149O.1C-1` remains implemented as strict closed proof
semantics. `F-149O.1C-2` remains editorial debt only. No HATP signature
verification was implemented. No provider attestation verification was
implemented. No trusted-signer lookup was implemented. No human-
presence verification was implemented. No HATP verification-status
engine was implemented. No real FIDO2 provider was implemented. No real
PIV provider was implemented. No human approval CLI was implemented. No
bootstrap/admin CLI was implemented. No Class-B OS security boundary
was provisioned. Current HATP deployment remains NOT READY. A
structurally valid HATP proof still does NOT imply HATP VALID. No
production rollback request derives `approval_present=True` from HATP.
`B-149O-1` through `B-149O-4` remain OPEN. No RAE production
integration was implemented. No AG3 Permission Broker integration was
implemented. No AG5 Permission Broker integration was implemented. No
rollback execution behavior changed. RAE-001 v1.0 remains unchanged.
RWMPC-001 v1.0 remains unchanged. PBPC-001 v1.2 remains unchanged.
PBPA-001 v1.0 remains unchanged. CHGR-001 remains unchanged. IWC
confirmation remains distinct from approval. AESIC/AEM remain
disclosure-only. No illegal CHGR/TAM composition was introduced. No
POL-001..012 meaning was changed. No POL-013+ was added. TK1/TK2/TK3
remain deferred. No Runtime Enforcement behavior changed. No Prompt
Generation, Prompt Dispatch, or agent invocation capability was
implemented. Runtime remains Observed, maximum capability remains
observe, and execution availability remains unavailable (re-confirmed
via `pcae runtime inspect` after this phase's edits).

## Recommended next phase

**149O.1H.2 — HATP Proof Models + Canonical Serialization Independent
Re-Verification.** Both Blocking findings are repaired per this
phase's own self-assessment; per the governing prompt's mandate,
Wave 3 must not be marked `VERIFIED` by the same phase that repaired
it. Wave 4 must not begin until 149O.1H.2 independently confirms both
repairs from scratch. 149O.1H.2 should especially attack: sub-
millisecond timestamp collisions (including precisions this phase's own
test matrix did not exercise), timezone-equivalent timestamps,
parser/constructor semantic-domain equivalence for fields not
enumerated in this phase's matrix, bool-as-int `proof_version`, direct
construction of malformed proofs via paths not exercised here, unknown
fields, duplicate keys, signed-payload completeness, golden vectors,
and mutation sensitivity.
