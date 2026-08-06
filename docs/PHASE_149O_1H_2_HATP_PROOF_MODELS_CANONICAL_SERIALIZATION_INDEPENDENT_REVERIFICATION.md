# Phase 149O.1H.2 — HATP Proof Models + Canonical Serialization Independent Re-Verification

## Scope

Independent adversarial re-verification of the 149O.1H.1 repair of two
Blocking findings (`B-149O.1H-1`, `B-149O.1H-2`) against
`src/pcae/core/human_approval_trusted_provenance.py` (Wave 3). Does
**not** trust the 149O.1H.1 repair report, the 149O.1H.1R
evidence-coherence analysis, or the 149O.1R report-trust outcome as
substitutes for fresh semantic verification. Verification-only: no
production source, HATP-001, or Wave 4 engine was implemented or
modified.

## Baseline

- `git status --short`: clean. `origin/main..HEAD`: 0.
- `pcae health` / `pcae check` / `pcae status coherence`: healthy /
  passed / coherent.
- `pcae doctor task-memory`: warnings only — 3 stale idle-placeholder
  files in `tasks/active/` (pre-existing task-memory directory-collapse
  pattern) and 4 pre-existing `tasks/DONE.md` sync gaps, both unrelated
  to and unchanged by this phase.
- `pcae push check`: `nothing_to_push`.
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`.
- `pcae notify status`: telegram configured/enabled.
- `pcae phase-report show --latest` + `pcae phase-report reconcile
  --phase-id 149O.1R`: 149O.1R confirmed `completed`, report
  `complete`, `internal_evidence_coherence: clear`,
  `derived_correctness: clear`, reconciled `already_dispatched`.
  Recommended next phase: **149O.1H.2** (as expected).

## Report-trust infrastructure baseline (149O.1R)

`B-149O.1R-1` and `B-149O.1R-2` remain CLOSED per the canonical 149O.1R
report; not independently re-verified in full here (out of this
narrow phase's scope), only exercised as a live regression: this
phase's own nested phase ID (`149O.1H.2`) round-trips correctly through
the repaired evidence extractor —

```python
from pcae.core.phase_id import parse
from pcae.core.phase_reports import _extract_evidence_phase_ids
text = "Phase 149O.1H.2 independently re-verifies B-149O.1H-1 and B-149O.1H-2 from Phase 149O.1H.1."
_extract_evidence_phase_ids(text)
# -> includes PhaseId(source_text='149O.1H.2') distinct from '149O.1H' and '149O.1H.1'
```

confirming `149O.1H.2` is recognized as its own standalone token, not
collapsed into `149O.1H` or `149O.1H.1`. See
`tests/test_phase_149o_1h_2_..._reverification.py::test_own_phase_id_self_hosts_in_evidence_extraction`.

## Production repair diff reconstruction

Pre-repair commit: `01c7fb74` (Phase 149O.1G). Repair commit:
`d75b96b1` (Phase 149O.1H.1).

```
git diff --name-only 01c7fb74 HEAD -- src/pcae/
  src/pcae/core/human_approval_trusted_provenance.py   (only file)
```

Hunk classification:

| Hunk | Classification |
|---|---|
| `Ag3OperationReference.__post_init__` added | CONSTRUCTOR_HARDENING |
| `Ag5OperationReference.__post_init__` added | CONSTRUCTOR_HARDENING |
| `HumanApprovalProvenanceProof.__post_init__` rewritten to call shared `_require_*` validators, normalize via `object.__setattr__` | CONSTRUCTOR_HARDENING + PARSER_VALIDATOR_UNIFICATION |
| `_require_issued_at` added | TIMESTAMP_VALIDATION / TIMESTAMP_DOMAIN |
| `_require_proof_version`, `_require_repository_instance_id`, `_require_rollback_site` added | SHARED_STRUCTURAL_VALIDATOR |
| `_build_proof_from_document` simplified to call shared validators | PARSER_VALIDATOR_UNIFICATION |

`UNRELATED = 0`. Confirmed via `git diff --stat 01c7fb74 d75b96b1 --
src/pcae/`: 1 file changed, 134 insertions, 17 deletions.

## B-149O.1H-1 — timestamp canonicalization injectivity

### Historical reproduction (pre-repair commit `01c7fb74`, via `git worktree`)

```
doc_a issued_at = "2026-01-01T12:00:00.0001Z"
doc_b issued_at = "2026-01-01T12:00:00.0009Z"
pa.issued_at == pb.issued_at == "2026-01-01T12:00:00.000Z"                   True
canonicalize_hatp_proof_payload(pa) == canonicalize_hatp_proof_payload(pb)   True
digest_hatp_proof_payload(pa) == digest_hatp_proof_payload(pb)               True
```

Historical defect independently confirmed real.

### Current source: original collision pair

Both `.0001Z` and `.0009Z` now raise `InvalidProofSchemaError`
("sub-millisecond fractional-second precision is not accepted").

### Current accepted-domain reconstruction

Read directly from `_require_issued_at`/`_parse_iso_timestamp`/
`_canonical_timestamp_string` (not from repair-report prose):

- ISO-8601 timestamps with an explicit UTC offset or `Z` suffix are
  accepted; naive (no offset) timestamps are rejected.
- Accepted fractional-second precision: exactly 0 or a multiple of
  1000 microseconds (`parsed.microsecond % 1000 == 0`) — i.e.
  millisecond-grained.
- Canonical rendering: `YYYY-MM-DDTHH:MM:SS.mmmZ` (UTC, millisecond
  precision, `Z` suffix), regardless of input offset form.

### Timestamp boundary matrix

| microsecond | expected | actual |
|---:|---|---|
| 0 | accepted | accepted (`.000Z`) |
| 1 | rejected | rejected |
| 100 | rejected | rejected |
| 999 | rejected | rejected |
| 1000 | accepted | accepted (`.001Z`) |
| 1001 | rejected | rejected |
| 999000 | accepted | accepted (`.999Z`) |
| 999001 | rejected | rejected |
| 999999 | rejected | rejected |

Exact match, independently reproduced (see
`test_timestamp_boundary_matrix`).

### Broader injectivity sweep

300 independently-generated, distinct, accepted (year/month/day/hour/
minute/second/millisecond) instants across 2020–2035: zero
canonical-string collisions among distinct instants
(`test_broad_millisecond_domain_injectivity_sweep`).

### Same-instant timezone equivalence

`2026-01-01T12:00:00Z`, `...+00:00`, `2026-01-01T13:00:00+01:00`,
`2026-01-01T07:00:00-05:00` — all four canonicalize to the identical
`2026-01-01T12:00:00.000Z`. Correct equivalence, not a collision.

### Offset + millisecond combination

`12:00:00.001Z` == `13:00:00.001+01:00` (same instant, same
millisecond) → same canonical string. Both differ from `12:00:00.002Z`.

### Negative/malformed inputs

Naive timestamp, malformed string, date-only, impossible date (Feb 30),
invalid offset (`+99:00`), non-string, `None`, empty string: all
rejected with `InvalidProofSchemaError`.

### Python compatibility audit

The module deliberately duplicates (does not import) its own
`_parse_iso_timestamp`, explicitly to avoid the Python 3.9
`fromisoformat` `Z`-suffix defect (module docstring, confirmed by
direct source read: the `Z`→`+00:00` substitution at the call site is
exactly the documented workaround). This repository's runtime is
Python 3.14 (`sys.version` confirmed at test time); no Python 3.9
interpreter was available to execute targeted tests there, so this
item is source-audited only — recorded as a limitation, not a gap in
this phase's own verification (matches the original 149O.1H document's
own disclosed limitation).

### New independent finding (below the original collision's precision level)

`_require_issued_at`'s injectivity gate checks
`parsed.microsecond % 1000`, where `parsed` comes from
`datetime.fromisoformat`. CPython's `fromisoformat` **silently drops**
any fractional-second digits past the sixth rather than rejecting them
(confirmed by direct interpreter probe: `.0000001` and `.0000009`
(7-digit fractional) both parse to `microsecond == 0`, dropping the
7th digit rather than rounding or raising). Consequently:

```python
_require_issued_at("2026-01-01T12:00:00.0000001Z")  # -> "2026-01-01T12:00:00.000Z" (accepted)
_require_issued_at("2026-01-01T12:00:00.0000009Z")  # -> "2026-01-01T12:00:00.000Z" (accepted, same)
```

Two distinct, individually-accepted raw `issued_at` strings —
differing only beyond the sixth fractional digit — canonicalize
identically, and the resulting canonical payload bytes/digest are
identical. This is the same *class* of defect `B-149O.1H-1` closed
(accepted-domain non-injectivity), one precision level deeper than the
149O.1H.1 boundary matrix tested (that matrix only swept 0–999999
microseconds, i.e. at most six fractional digits). It was not
introduced by the 149O.1H.1 repair — the pre-repair source had the
identical `fromisoformat` truncation behavior and was already
vulnerable to it at a coarser (millisecond) level, which the repair
fixed; this finer-grained instance of the same root cause survived the
repair because the repair's own boundary matrix, faithfully following
the governing prompt's `0..999999` sweep, did not probe past six
fractional digits.

Reproduced independently in
`test_sub_microsecond_fractional_digits_are_silently_truncated_not_rejected`
and `test_new_finding_sub_microsecond_collision_reproduced`.

**Practical severity note:** no real timestamp source in this
project's stack (or any commonly-used clock/serialization convention)
naturally emits sub-microsecond ISO-8601 fractional precision;
exploiting this requires an adversarial proof author to hand-craft a
7+-digit fractional `issued_at` string. It is nonetheless a literal,
independently-reproduced instance of "accepted semantically distinct
timestamps canonicalize identically" (governing-prompt §95 Blocking
Condition), so it is recorded as **BLOCKING** per the letter of that
rule rather than downgraded on a severity judgment call this phase is
not chartered to make.

### B-149O.1H-1 verdict

**B-149O.1H-1 REOPENED — a narrower, independently-discovered
sub-microsecond timestamp canonicalization collision remains,** even
though the originally-reported millisecond-level collision (`.0001Z` /
`.0009Z` and the full declared millisecond-grained accepted domain) is
**independently confirmed closed**. Recommend a narrow follow-up repair
that rejects any `issued_at` value whose raw fractional-second segment
contains more than six digits (or, equivalently, revalidates the raw
string's fractional length before trusting `datetime.fromisoformat`'s
truncated `microsecond` field), rather than reopening or repeating the
149O.1H.1 repair's already-correct millisecond-domain logic.

## B-149O.1H-2 — public constructor / parser domain equivalence

### Historical reproduction (pre-repair commit `01c7fb74`)

Against the unmodified pre-repair source, all three of the following
constructed successfully with no exception (parser would have rejected
every one):

- `HumanApprovalProvenanceProof(proof_version=True, ...)` — accepted,
  `type(bad.proof_version) is bool`.
- `HumanApprovalProvenanceProof(repository_id="NOT-A-VALID-UUID", ...)`
  — accepted.
- `Ag3OperationReference(job_id="", original_commit_sha="not-a-sha")`
  — accepted.

Historical defect independently confirmed real.

### Current shared validator architecture

Directly identified from source (not repair-report prose):
`_require_proof_version`, `_require_nonempty_str`, `_require_sha256_hex`,
`_require_commit_sha`, `_require_repository_instance_id`,
`_require_rollback_site`, `_require_issued_at`. All seven are called by
both `_build_proof_from_document` (parser path) and
`HumanApprovalProvenanceProof.__post_init__` /
`Ag3OperationReference.__post_init__` /
`Ag5OperationReference.__post_init__` (constructor path) — a single
shared layer, not two independently-drifting ones.

### Parser/constructor semantic-domain equivalence matrix

| Invariant | Parser | Direct constructor |
|---|---|---|
| `proof_version` type/support/bool-exclusion | `_require_proof_version` | `_require_proof_version` |
| `principal_id`/`signer_key_id`/`provider_profile` non-empty | `_require_nonempty_str` | `_require_nonempty_str` |
| `repository_id` format | `_require_repository_instance_id` | `_require_repository_instance_id` |
| `decision_record_id`/`binding_id` non-empty | `_require_nonempty_str` | `_require_nonempty_str` |
| `decision_record_digest`/`binding_digest` hex-64 | `_require_sha256_hex` | `_require_sha256_hex` |
| `rollback_site` value + type normalization | `_require_rollback_site` | `_require_rollback_site` |
| `issued_at` validity + millisecond domain | `_require_issued_at` | `_require_issued_at` |
| `job_id` non-empty, `original_commit_sha` format | `Ag3OperationReference.__post_init__` (shared validators) | same (constructor is the only path — no separate parser-side struct) |
| `per_id`/`ecp_id` non-empty | `Ag5OperationReference.__post_init__` | same |
| family/operation-reference-type agreement | `_build_proof_from_document`'s discriminant dispatch | `HumanApprovalProvenanceProof.__post_init__` isinstance checks |

Parser-only responsibilities (do not indicate a domain mismatch —
typed constructors never accept raw untyped JSON structure in the
first place): JSON syntax validity, top-level-object requirement,
duplicate-key rejection, unknown-field rejection, wrong-field-set
detection.

### Adversarial probes (constructor path), independently run

All of the following raise `UnsupportedProofVersionError` or
`InvalidProofSchemaError` on direct construction:

`proof_version` ∈ {`True`, `False`, `0`, `2`, `-1`, `"1"`, `1.0`,
`None`, `[]`, `{}`} (10/10 rejected; only `1` accepted, and it survives
as `type is int`, not `bool`, confirming the `bool ⊂ int` trap is
handled). Invalid `repository_id`, invalid `decision_record_digest`,
invalid `binding_digest`, empty `principal_id`/`signer_key_id`/
`provider_profile`/`decision_record_id`/`binding_id`, malformed
`issued_at`, sub-millisecond `issued_at`, AG3/AG5 family mismatch (both
directions), `Ag3OperationReference`/`Ag5OperationReference` with empty
or malformed fields — 21 total adversarial constructions attempted, 21
rejected, 0 bypasses.

### Normalization equivalence

A direct construction given a raw `"AG3"` string (not the `RollbackSite`
enum) and a non-canonical `issued_at` (`+01:00` offset form) produces
an instance whose `rollback_site` is the typed `RollbackSite.AG3`
member and whose `issued_at` is the identical canonical string a
parser-built instance of the same semantic proof would carry; their
canonical payload bytes are byte-identical. Confirmed.

### B-149O.1H-2 verdict

**B-149O.1H-2 INDEPENDENTLY CONFIRMED CLOSED — PUBLIC CONSTRUCTOR
DOMAIN MATCHES STRUCTURAL PARSER DOMAIN.** No bypass found across 21
adversarial direct-construction probes plus the operation-reference and
normalization matrices above.

## Model immutability

`FrozenInstanceError` raised on `proof.principal_id = "other"` and on
`proof.operation_reference.job_id = "other"` (nested). No mutable
nested container exists in any model field (`str`/`int`/`RollbackSite`/
frozen-dataclass operation reference only). Confirmed.

## F-149O.1C-1 — closed-schema re-verification

All 13 self-selected-trust-field/unknown-field attacks
(`trusted_root`, `trusted_public_key`, `attestation_root`,
`authority_registry`, `canonical_root`, `trust_store_root`,
`deployment_root`, `approved`, `trusted`, `authorized`, `human_present`,
`valid`, `arbitrary_unknown`) rejected. Duplicate top-level JSON key
rejected (`MalformedProofError`). AG5-discriminator-with-AG3-payload,
mixed AG3+AG5 fields, missing `rollback_site`, unknown family `"AG7"`:
all rejected.

**F-149O.1C-1 INDEPENDENTLY CONFIRMED IMPLEMENTED.** No regression.

## F-149O.1C-2

Remains editorial debt only. Requirement count remains 117
(`HATP-REQ-001..117`, confirmed unchanged in
`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`).

## Signed-payload reconstruction

Independently cross-referenced against HATP-REQ-069's field list
(§20 of the contract): `principal_id`, `signer_key_id`,
`provider_profile`, `repository_id`, `decision_record_id`,
`decision_record_digest`, `binding_id`, `binding_digest`,
`rollback_site`, `issued_at`, `proof_version`, plus
`job_id`/`original_commit_sha` (AG3) or `per_id`/`ecp_id` (AG5).

| Security semantic | In canonical payload? |
|---|---|
| proof version | YES |
| principal | YES |
| signer/credential identity | YES |
| provider profile | YES |
| repository_instance_id | YES |
| Decision ID | YES |
| Decision digest | YES |
| Binding ID | YES |
| Binding digest | YES |
| rollback site/family | YES |
| AG3/AG5 operation reference | YES |
| issued_at | YES |

**SIGNED PAYLOAD: COMPLETE FOR HATP-001 WAVE-3 SECURITY SEMANTICS.** No
self-selected trust field (`trusted`, `trusted_key`, `trust_root`,
`attestation_root`, `authority_registry`, `deployment_root`,
`approved`, `human_present`, `valid`) is present in or constructible
into the payload.

## Canonical JSON rule + independent golden vectors

`canonicalize_hatp_proof_payload` reconstructed independently as
`sort_keys=True, separators=(",", ":"), ensure_ascii=False,
allow_nan=False`, UTF-8 — confirmed by direct source read.

An independent from-scratch canonicalizer (plain `json.dumps` with the
same parameters, no import of production canonicalization code) was
built and used to compute AG3/AG5 golden vectors from first
principles, using this phase's own fixture documents (not imported from
149O.1G/149O.1H/149O.1H.1's fixtures):

- AG3 fixture digest (independently computed, matches production
  exactly): `d69567a62527f37825bc59fcb0564f21281511c21ffb0a07195c21dc8ff84212`
- AG5 fixture digest (independently computed, matches production
  exactly): `9efedce2594fcd123f4646c88278f8820eb274ea45d06afd9a9cbd3e5c845312`

Both independently-recomputed values are **byte-for-byte identical** to
the values `canonicalize_hatp_proof_payload`/`digest_hatp_proof_payload`
themselves produce for the same input — the from-scratch reimplementation
and the production implementation agree exactly.

The governing-phase-prompt's own quoted "currently reported golden
digests" (`bafc5bc9...`/`480422914a...`) do **not** match either value
above. Per the prompt's own explicit caveat ("treat these as claims to
verify, not authorities... ignore older prompt-example digest
strings"), this is resolved as: the prompt-quoted strings are stale/
illustrative examples, not a discrepancy in production behavior — the
governing prompt itself anticipates and pre-authorizes disregarding
them once independently recomputed values disagree. **Not a defect.**

Golden vectors unchanged from the pre-repair (149O.1G) canonicalizer's
output for the same already-accepted millisecond-precision input,
confirmed directly (the repair narrowed the accepted *domain*; it never
touched the canonical *rendering* of any value that was already
accepted before and after).

Key-order independence, whitespace independence, and a representative
Unicode round-trip (ASCII + accented + emoji + combining-adjacent
codepoints) all confirmed: canonical bytes depend only on the decoded
semantic document, never on input formatting; no field is silently
normalized beyond what `_require_*` explicitly does (offset/precision
canonicalization for `issued_at` only).

## SHA-256 verification

Independently recomputed `hashlib.sha256(canonical_bytes).hexdigest()`
matches `digest_hatp_proof_payload`'s own output exactly for every
probed proof.

## Mutation sensitivity

Every accepted semantic field (`principal_id`, `signer_key_id`,
`provider_profile`, `repository_id`, `decision_record_id`,
`decision_record_digest`, `binding_id`, `binding_digest`, `rollback_site`
/family, `issued_at` at millisecond granularity, `job_id`,
`original_commit_sha`) independently mutated one at a time: digest
changes in every case (12/12). Two AG3/AG5 proofs sharing identical
opaque field values where structurally possible still canonicalize to
different bytes (family/field-name discrimination alone is sufficient).

## Structural validity ≠ trust; dependency/purity audit

- No symbol named `approval_present`, `HATP_VALID`, `UNKNOWN_SIGNER`,
  or `VALID` is defined anywhere in the module's public surface or as
  a dataclass field (confirmed via `dir()` + `dataclasses.fields()`,
  not a docstring-text search — the docstring *discusses* the boundary
  by name deliberately, as documentation, which is expected and
  correct).
- No import of `hatp_bootstrap`, `rollback_approval_evidence`,
  `permission_broker*`, `pcae.core.agent`, or `commands.agent` (AST
  import-walk over the module's own source).
- No `datetime.now(`/`.now()`/`time.time(`/`open(`/`requests.`/
  `socket.`/`os.environ`/`getenv(` call anywhere in the module source.
- Only dependency: `pcae.core.repository_identity.is_valid_repository_instance_id`,
  itself a pure `uuid.UUID(...)` format check with no I/O, confirmed by
  direct source read.

## Boundary confirmations

- HATP-001 v1.0: byte-unchanged (this phase touched no file under
  `docs/contracts/`).
- Wave 1 (`repository_identity.py`) and Wave 2
  (`hatp_bootstrap.py`/related): byte-unchanged; regression below.
- `src/pcae/core/phase_reports.py`, `src/pcae/commands/phase.py`,
  `src/pcae/commands/phase_reports.py`, `src/pcae/cli.py`
  (149O.1R report-trust surface): byte-unchanged.
- No production source under `src/pcae/` was modified by this phase —
  the only new file this phase adds is
  `tests/test_phase_149o_1h_2_..._reverification.py` and this document.

## Regressions

| Suite | Result |
|---|---|
| Wave-3 (`test_hatp_proof_models.py` + `test_hatp_canonical_serialization.py` + `test_phase_149o_1g_...py`) | 100 passed |
| 149O.1H historical (`test_phase_149o_1h_..._independent_verification.py`) | 166 passed |
| 149O.1H.1 repair (`test_phase_149o_1h_1_..._domain_hardening.py`) | 93 passed |
| Combined Wave-3 (above three files) | 359 passed |
| Wave-1/2 foundation (`test_repository_identity.py` + `test_hatp_bootstrap_foundation.py` + `test_phase_149o_1e_...py` + `test_phase_149o_1f_...py` + `test_phase_149o_1f_1_...py`) | 103 passed |
| 149O.1F.2 (`test_phase_149o_1f_2_..._reverification.py`) | 90 passed |
| Phase-report trust (`test_phase_reports.py` + `test_phase_reports_cli.py` + `test_phase_report_trust_hard_fail.py` + `test_push_phase_report_identity_137f1.py`) | 201 passed |
| This phase's new independent test file | 99 passed |
| Fast Green (`pytest -m fast_green -n auto`) | 4531 passed, matches entering baseline, no regression |
| RAE / Permission Broker / Agent | see final report (broad baseline, pre-existing known failures, no new failures introduced by this verification-only phase) |

No production regression detected in any suite.

## Findings

- **B-149O.1H-1 (original millisecond-level collision):**
  INDEPENDENTLY CONFIRMED CLOSED.
- **New finding (sub-microsecond fractional-digit truncation
  collision):** BLOCKING per governing-prompt §95's literal condition,
  independently discovered and reproduced; narrow scope (requires
  7+-digit fractional-second input, not producible by any realistic
  clock source in this stack); recommend a narrow follow-up repair
  phase, not a reopening of the original 149O.1H.1 repair's
  millisecond-domain logic.
- **B-149O.1H-2:** INDEPENDENTLY CONFIRMED CLOSED — no findings.
- **F-149O.1C-1:** INDEPENDENTLY CONFIRMED IMPLEMENTED — no findings.
- **F-149O.1C-2:** unchanged, editorial debt only.

## Verdicts

- `B-149O.1H-1`: **REOPENED** (narrow, sub-microsecond scope only — the
  originally-reported `.0001Z`/`.0009Z` millisecond-level collision and
  its full declared accepted domain are independently confirmed
  closed).
- `B-149O.1H-2`: **INDEPENDENTLY CONFIRMED CLOSED — PUBLIC CONSTRUCTOR
  DOMAIN MATCHES STRUCTURAL PARSER DOMAIN.**
- `F-149O.1C-1`: **INDEPENDENTLY CONFIRMED IMPLEMENTED.**
- Canonicalization: **BLOCKING AMBIGUITY / COLLISION REMAINS** (narrow,
  sub-microsecond scope — see above).
- Constructor domain: **EQUIVALENT TO OR STRICTER THAN PARSER SEMANTIC
  DOMAIN.**
- Signed payload: **COMPLETE FOR HATP-001 WAVE-3 SECURITY SEMANTICS.**
- Overall Wave-3 verdict: **NOT VERIFIED — BLOCKING HATP WAVE 3
  FINDING** (the new, narrow sub-microsecond timestamp finding; every
  other examined property — B-149O.1H-2, F-149O.1C-1, signed-payload
  completeness, immutability, closed schema, purity, dependency
  boundary, golden vectors — verifies cleanly).
- Wave-3 readiness: not ready for Wave 4 until this new finding is
  repaired and re-verified (same lineage discipline as the original
  B-149O.1H-1/-2 repair → re-verify cycle).
- HATP production readiness: **NOT READY** (unaffected either way —
  Wave 4/5/6 remain entirely unimplemented regardless of this finding).

## Recommended Next Phase

**149O.1H.3 — HATP Sub-Microsecond Timestamp Truncation Narrow Repair**:
reject any `issued_at` raw string carrying more than six fractional-
second digits (or otherwise re-derive the accepted/rejected boundary
from the raw string rather than trusting `datetime.fromisoformat`'s
silent truncation), scoped exactly as narrowly as 149O.1H.1 was scoped
to its two findings. **Do not begin Wave 4** until 149O.1H.3 repairs
this finding and a follow-up independent re-verification phase
confirms the repair (mirroring the 149O.1H → 149O.1H.1 → 149O.1H.2
lineage). `B-149O.1H-2`, `F-149O.1C-1`, and `F-149O.1C-2` require no
further action.
