# Phase 149O.1H.6 -- HATP Timestamp Canonicalization Final Independent Verification

**Type:** verification-only (no production change)
**Contract:** HATP-001 v1.0, FROZEN, byte-unchanged this phase
**Production module under test:** `src/pcae/core/human_approval_trusted_provenance.py`
**New suite:** `tests/test_phase_149o_1h_6_hatp_timestamp_canonicalization_final_independent_verification.py` (173 tests, all passing)

## 1. Baseline

Initial inspection (all confirmed before any test authoring began):

- `git status --short`: clean
- `git rev-list --count origin/main..HEAD`: 0
- `pcae health` / `pcae check` / `pcae status coherence`: healthy / passed / coherent
- `pcae push check`: nothing_to_push
- `pcae phase-report show --latest`: 149O.1H.5 complete, report complete, recommended next = 149O.1H.6
- `pcae phase-report reconcile --phase-id 149O.1H.5`: reconciled, already_dispatched
- Runtime: Observed / observe / unavailable (unchanged)

## 2. 149O.1H.5 Production Diff Reconstruction (independent)

`git diff --name-only 3d6b5a9a..66fde5c3 -- src/pcae/` yields exactly one file:
`src/pcae/core/human_approval_trusted_provenance.py`.

The functional diff is a single hunk. Classification:

- **LEXICAL_GUARD**: 1 (the `_FRACTIONAL_SECONDS_RE` assignment,
  `\.(\d+)(?=Z$|[+-]\d{2}:\d{2}$)` -> `(?<=:\d{2})[.,](\d+)`, plus its comment)
- **FRACTION_EXTRACTION**: 0 (extraction call site, `_reject_excess_fractional_precision`, unchanged)
- **UNRELATED**: 0

No canonicalizer or model-shape hunk exists. Confirmed programmatically by
`test_exact_149o_1h_5_production_boundary_reconstructed` and
`test_149o_1h_5_diff_hunk_is_single_lexical_guard_change_only`.

## 3. Historical Bypass Reproduction (isolated import of commit `3d6b5a9a`, independent of the 149O.1H.5 report's own claims)

**Non-colon-offset bypass (B-149O.1H.4-1):** the pre-repair regex's suffix lookahead
(`Z$|[+-]\d{2}:\d{2}$`) never matches `+00` / `+0000`. Independently re-derived:
`old_re.search(...)` returns `None` for all four of
`.0000001+00`, `.0000009+00`, `.0000001+0000`, `.0000009+0000`. Both
`.0000001+00` and `.0000009+00` parse to the *identical* `datetime`
(`microsecond == 0`) under the pre-repair `_parse_iso_timestamp` -- the exact
historical collision, reproduced fresh, not trusted from the prior report.

**Decimal-comma bypass:** the pre-repair regex is anchored on a literal `\.`,
so it never matches a `,`-separated fraction through any suffix, including `Z`.
Independently confirmed: `old_re.search(...)` is `None` for all of
`,0000001Z`, `,0000009Z`, `,0000001+00:00`, `,0000009+00:00`; the comma pair
also collides to `microsecond == 0`.

`+0000` was included in the non-colon-offset reproduction (the prompt's
`+00` case is a subset of the tested set).

Both classes are now correctly rejected by the live module, via both
`parse_hatp_proof` and the direct `HumanApprovalProvenanceProof` constructor.

## 4. Current Guard Reconstruction

`_FRACTIONAL_SECONDS_RE = re.compile(r"(?<=:\d{2})[.,](\d+)")`.

- Anchor: a lookbehind for `:` + exactly two digits (`SS`) -- i.e. it looks
  for the character *immediately after* a two-digit seconds field.
- Recognized separators: `.` or `,`, immediately following that anchor.
- Captured substring: one or more digits (`\d+`) contiguous from the
  separator.
- Suffix syntax does **not** participate in the match at all -- there is no
  lookahead constraint on what follows the digit run.
- No later timestamp text affects the digit count for a given match: the
  captured group is exactly the contiguous digit run starting right after
  the separator; it stops at the first non-digit character (independently
  confirmed against the multi-dot attack, `12:00:00.123.456Z` captures only
  `"123"`, never `"123456"`).

Fraction detection therefore depends only on: the seconds field + the
decimal separator immediately after it + the contiguous digit run -- not on
timezone-offset syntax.

## 5. Ordering (guard runs before lossy parse)

Source-inspection proof (`test_losslessness_guard_runs_before_lossy_parse_for_every_rejected_case`):
in `_parse_iso_timestamp`'s source text, the call to
`_reject_excess_fractional_precision(...)` appears strictly before the call
to `datetime.fromisoformat(...)`. This is not merely behaviorally inferred;
it is read directly from `inspect.getsource`.

## 6. Independent Runtime Grammar Probe (Python 3.14.5, this interpreter)

Probed directly (not copied from 149O.1H.5's matrix). Accepted by
`datetime.fromisoformat`:

- `Z`, `+HH:MM`/`-HH:MM`, `+HH`/`-HH`, `+HHMM`/`-HHMM` (compact)
- `+HH:MM:SS`/`+HHMMSS` (offset-seconds field)
- `+HH:MM:SS.f`/`+HH:MM:SS,f` (offset with fractional seconds -- **the
  sub-second component of the offset itself is silently discarded**;
  `utcoffset()` is identical with or without it)
- `,` as the main-timestamp decimal separator (independent bypass class,
  not previously tested prior to 149O.1H.5)
- a bare space in place of `T` as the date/time separator
- lowercase `z` is **rejected** (`Invalid isoformat string`)
- a timezone-naive timestamp (no offset at all) is accepted by
  `fromisoformat` itself, but `_parse_iso_timestamp` independently rejects
  it (`parsed.tzinfo is None` check)

## 7. Offset Fractional-Seconds Probe / Main-vs-Offset Fraction Analysis

Confirmed: `datetime.fromisoformat("...+00:00:00.5")` parses with
`utcoffset() == 0` -- the offset's own sub-second component is accepted
lexically but has **zero semantic effect**; it is not part of the resulting
instant. It is therefore *not* HATP timestamp fractional precision, and the
guard must not (and does not) treat it as such in the sense of *losing*
precision -- there is nothing there to lose.

## 8. Multiple-Match / `re.search` First-Match Analysis (decisive)

A single parser-accepted string CAN contain two `:\d{2}[.,]\d+` structures
(main-timestamp seconds fraction, offset-seconds fraction) -- confirmed via
`_FRACTIONAL_SECONDS_RE.findall("...12:00:00.123+00:00:00.456")` ==
`["123", "456"]`.

`_reject_excess_fractional_precision` uses `.search()`, which returns the
**leftmost** match. In every syntactically valid ISO-8601 timestamp the
main-timestamp seconds field lexically *precedes* any offset-seconds field
(time comes before offset in the string). This is a structural, not
incidental, property: the leftmost match is therefore always the MAIN
fraction whenever one is present, regardless of what the offset contains.

Adversarial sweep (main-fraction-length x offset-fraction-length),
independently constructed, not copied:

| main fraction | offset fraction | verdict | reason |
|---|---|---|---|
| 7 digits | 1, 6, or 7 digits | REJECT | leftmost match = main, >6 digits |
| 6 digits (aligned, `.100000`) | 7 digits | ACCEPT, canonical `.100Z` | leftmost match = main, <=6 digits; offset fraction is a red herring the guard never reaches |
| 3 digits (`.100`) | 7 digits | ACCEPT, canonical `.100Z` | same |
| none | 7 digits | REJECT (safe over-rejection) | no main match exists; the only `:\d{2}[.,]\d+` present is the offset's, so `.search()` matches it instead -- this is the *safe* direction (a real instant is unnecessarily rejected, never the reverse) |

**No main timestamp fraction >6 digits can evade detection because of
offset content, in either direction.** This was attacked explicitly per
prompt items 11-13 and confirmed clean.

The `none`/offset-only-fraction case is recorded as a **NON-BLOCKING
OBSERVATION**: it is theoretically possible to construct a parser-accepted
string with zero main-timestamp fractional precision that the guard
nonetheless rejects, purely because of a >6-digit fractional component in
the offset's own (semantically discarded) seconds. This never causes an
unsafe *acceptance*, only an occasional unnecessary *rejection* of a
pathological, not practically-occurring, input shape.

## 9. Decimal-Point / Decimal-Comma / Fraction-Length Matrix (0..50 digits)

For both `.` and `,`, main-timestamp fraction lengths 0-6 are accepted
(subject to the pre-existing millisecond-alignment rule, unchanged); lengths
7, 8, 9, 10, 12, 20, and 50 are rejected, for both all-zero (`.0000000`,
etc.) and significant-digit (`.9999999`, etc.) subclasses. All confirmed
directly against the live module (Sections G of the new suite).

## 10. Millisecond-Domain Semantics (unchanged, Stage 2)

Re-confirmed unchanged: `.000`, `.001`, `.0010`, `.00100`, `.001000`,
`.123`, `.123000`, `.999`, `.999000` accepted; `.000001`, `.000999`,
`.001001`, `.123456`, `.999999` rejected (sub-millisecond remainder).
Original 149O.1H pair (`.0001`, `.0009`) still rejected.

## 11. Cartesian Suffix Matrix (item 24)

For every discovered suffix (`Z`, `+00:00`, `+0000`, `+00`, `+01:00`,
`+0100`, `+01`, `-05:00`, `-0500`, `-05`): no-fraction and 3-digit/6-digit
aligned fractions accept; 6-digit non-aligned, 7-digit all-zero, and
7-digit significant fractions all reject. 60 parametrized cases, all as
expected.

## 12. Suffix-Independence Property (items 25/26)

For the fixed fraction `.1234567`, the captured digit count is identical
(`7`) across every discovered suffix and the naive (no-suffix) form.
For every discovered suffix with no main fraction, the guard reports no
match at all -- bare offset digits (e.g. `+0000`) are never counted, since
no `.`/`,` character precedes them.

## 13. Malformed / Near-Valid Forms (items 34-37)

All rejected by the downstream `datetime.fromisoformat` (not by guard
miscounting): `12:00:00.123.456Z`, `12:00:00,123,456Z`, `12:00:00.,123Z`,
`12:00:00..123Z`, mixed `.123,456Z`/`,123.456Z`, exponent-like `.1e3Z`,
signed-fraction `.+123Z`/`.-123Z`. The multi-dot case was specifically
attacked to confirm the guard itself only captures the first contiguous
digit run (`"123"`, never `"123456"`) -- the eventual rejection is the
parser's, not an artifact of guard miscounting that happens to reject for
the wrong reason.

Naive timestamps, lowercase `z`, and leading/trailing whitespace/newline
all remain rejected -- no trimming occurs.

## 14. Losslessness / Injectivity / Same-Instant Equivalence

- **Losslessness:** guard executes before any lossy conversion (Section 5).
- **Same-instant equivalence:** `.001Z`, `.001+00:00`, `.001+0000`,
  `.001+00`, `,001Z` all canonicalize to the identical
  `2026-01-01T12:00:00.001Z`; the analogous non-zero-offset set
  (`13:00:00.001+01:00`/`+0100`/`+01`) canonicalizes to the identical
  `2026-01-01T12:00:00.001Z`.
- **Injectivity:** a sweep of 5 distinct millisecond-fraction values
  (`.000`, `.001`, `.002`, `.500`, `.999`) produces 5 distinct canonical
  strings, no collisions.
- **Distinct-instant payload sensitivity:** `.001Z` vs `.002Z` (all other
  fields fixed) produces distinct canonical bytes and distinct SHA-256
  digests.

## 15. Parser/Constructor Equivalence

Re-verified over both the newly-probed accepted forms (non-colon offsets,
comma separator) and the newly-probed rejected forms (>6-digit fractions
via both separators, naive timestamps, 6-digit non-aligned) -- `parse_hatp_proof`
and the direct `HumanApprovalProvenanceProof` constructor produce identical
accept/reject outcomes and identical canonical values in every case tested.

## 16. B-149O.1H-2 Regression

Re-tested: boolean `proof_version`, invalid repository ID, invalid decision
digest, invalid binding digest, invalid commit SHA, empty identifier,
AG3/AG5 family mismatch -- all still rejected via direct construction.
Closed-schema unknown-field probe (13 fields incl. `trusted_root`,
`approved`, `human_present`, `valid`, `arbitrary_unknown`, ...), duplicate
top-level JSON key, AG3/AG5 wrong-family field, unknown `rollback_site`
value, and missing required field -- all correctly rejected.

**B-149O.1H-2 REMAINS INDEPENDENTLY CONFIRMED CLOSED** -- unaffected by this
phase or by 149O.1H.5.

## 17. F-149O.1C-1 / F-149O.1C-2

Closed-schema strict parsing (F-149O.1C-1) independently re-exercised
above (unknown/wrong-family fields rejected) -- **INDEPENDENTLY CONFIRMED
IMPLEMENTED**. F-149O.1C-2 is out of this phase's scope (editorial debt
only, unaffected).

## 18. Signed-Payload Reconstruction / Completeness

Independently reconstructed the expected AG3 signed field set
(`proof_version`, `principal_id`, `signer_key_id`, `provider_profile`,
`repository_id`, `decision_record_id`, `decision_record_digest`,
`binding_id`, `binding_digest`, `rollback_site`, `issued_at`, `job_id`,
`original_commit_sha`) and confirmed `hatp_proof_to_document(proof).keys()`
matches exactly -- no field added or removed by any timestamp repair. No
`issued_at_raw` or other unsigned/duplicate timestamp channel was
introduced.

**SIGNED PAYLOAD: COMPLETE FOR HATP-001 WAVE-3 SECURITY SEMANTICS.**

## 19. Golden Vectors / SHA-256

Independently constructed AG3 and AG5 canonical JSON documents (fixed field
order irrelevant -- `sort_keys=True`), computed `json.dumps(..., sort_keys=True,
separators=(",", ":"), ensure_ascii=False, allow_nan=False)` bytes without
calling `canonicalize_hatp_proof_payload`, and compared: **bytes match**,
and independently computed `hashlib.sha256(expected_bytes).hexdigest()`
**matches** `digest_hatp_proof_payload(proof)` exactly, for both AG3 and
AG5. Mutation sensitivity re-confirmed across every signed field
(`principal_id`, `signer_key_id`, `provider_profile`, `decision_record_id`,
`decision_record_digest`, `binding_id`, `binding_digest`, `issued_at`,
`job_id`, `original_commit_sha`) -- every one changes the digest.

## 20. Purity / Dependency / Public API / Vocabulary Audit

No `VALID`/`UNKNOWN_SIGNER`/`approval_present`/`HATP_VALID` symbol in the
module namespace. No `import`/`from` statement lines reference
`hatp_bootstrap`, `rollback_approval_evidence`, `permission_broker`,
`pcae.core.agent`, or `commands.agent` (module docstring prose mentioning
`hatp_bootstrap.py` to document its deliberate non-import is not an import
statement -- checked separately). Both `HumanApprovalProvenanceProof` and
`Ag3OperationReference` remain frozen dataclasses (attribute assignment
raises). A structurally valid, directly-constructed proof exposes no
`approval_present`/`verified`/`trusted`/`valid`/`authorized`/
`human_present` attribute.

## 21. Report-Trust Self-Hosting

201/201 report-trust regression tests pass (`test_phase_reports.py`,
`test_phase_reports_cli.py`, `test_phase_report_trust_hard_fail.py`,
`test_push_phase_report_identity_137f1.py`); no file under
`src/pcae/core/phase_reports.py`, `src/pcae/commands/phase.py`,
`src/pcae/commands/phase_reports.py`, or `src/pcae/cli.py` was modified
this phase.

## 22. Findings

No BLOCKING findings.

One NON-BLOCKING observation (Section 8): a parser-accepted string with no
main-timestamp fraction but a >6-digit offset-seconds fractional component
is safely over-rejected rather than accepted -- never an unsafe acceptance,
and not a practically-occurring input shape for this contract's intended
producers. Retained as an observation per the standard non-blocking
observation class ("Python runtime accepts ISO forms broader than PCAE
needs, provided all accepted HATP forms are safely guarded").

No other findings from this phase's attack surface (multi-dot, mixed
separator, exponent, signed-fraction, naive, lowercase-z, whitespace,
duplicate-key, closed-schema, AG3/AG5 discrimination, golden vector, digest,
purity/dependency/API audit).

## 23. Verdicts

**B-149O.1H.4-1:**
INDEPENDENTLY CONFIRMED CLOSED
-- FRACTIONAL PRECISION GUARD IS SUFFIX-INDEPENDENT ACROSS
THE EFFECTIVE PARSER LANGUAGE

**B-149O.1H-1:**
INDEPENDENTLY CONFIRMED CLOSED
-- ACCEPTED RAW TIMESTAMP DOMAIN IS LOSSLESS AND
CANONICALIZATION IS INJECTIVE OVER ACCEPTED SEMANTICS

**B-149O.1H-2:**
REMAINS INDEPENDENTLY CONFIRMED CLOSED

**Canonicalization:**
DETERMINISTIC
UNAMBIGUOUS
LOSSLESS OVER ACCEPTED RAW INPUT
INJECTIVE OVER ACCEPTED SEMANTICS

**Overall Wave-3 verdict:**
VERIFIED WITH NON-BLOCKING FINDINGS
-- HATP WAVE 3 PROOF MODELS + CANONICAL SERIALIZATION CONFORM

**Wave-3 readiness:**
WAVE 3: READY FOR WAVE 4 IMPLEMENTATION

**HATP production readiness:**
NOT READY (unaffected; Wave 4 is the next implementation wave, not
production activation)

## 24. Explicit Confirmations

- HATP-001 v1.0 remained byte-unchanged this phase (no diff at HEAD;
  SHA-256 of the contract file recorded: `26d8e975a55d6247f8e8f3370908f594374e4cb755a9f61a151a09c088847872`).
- No production source (`src/pcae/**`) was modified by Phase 149O.1H.6.
- No proof field was added or removed; canonical signed-payload field set
  unchanged; canonical millisecond timestamp representation unchanged;
  SHA-256 digest semantics unchanged.
- Wave 1 and Wave 2 unchanged (103/103 regression).
- B-149O.1F-1 remains confirmed closed; B-149O.1R-1/B-149O.1R-2 remain
  closed. F-149O.1C-1 independently re-evaluated (confirmed implemented);
  F-149O.1C-2 remains editorial debt only.
- No Wave-4 verifier, signature verification, provider attestation
  verification, trusted-signer lookup, human-presence verification,
  FIDO2 provider, PIV provider, Class-B deployment, or RAE/HATP
  integration was implemented. No AG3/AG5 production wiring was
  implemented.
- A structurally valid HATP proof still does NOT imply HATP VALID.
- B-149O-1 through B-149O-4 remain OPEN.
- HATP production remains NOT READY.
- Runtime remains Observed / observe / unavailable.

## 25. Recommended Next Phase

All B-149O.1H-1, B-149O.1H.4-1 independently confirmed closed;
B-149O.1H-2 remains closed. No timestamp-syntax bypass, regex-match
ambiguity, decimal-comma gap, or information loss was found.

**149O.1I -- HATP Verification Engine Implementation (Wave 4)**

This phase is the trust boundary: Wave 4 may now safely treat the Wave-3
canonical payload as the exact bytes whose cryptographic authenticity it
will verify.
