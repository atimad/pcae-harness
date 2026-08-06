# Phase 149O.1H.5 — HATP Timestamp Canonicalization Lexical Guard Widening

## Scope

Narrow Wave-3 production repair of exactly one Blocking finding
independently discovered by Phase 149O.1H.4's final re-verification:
`B-149O.1H.4-1` (the 149O.1H.3 lexical fractional-second precision
guard's regex anchored on the timezone-suffix syntax that follows the
fraction, rather than on the fraction itself, and so did not recognize
every offset syntax `datetime.fromisoformat` accepts). Owns
`src/pcae/core/human_approval_trusted_provenance.py`, a new focused
test suite, and this document. No Wave 4 verification engine, no
signature/attestation/human-presence verification, no trusted-signer
resolution, no FIDO2/PIV provider, no Class-B OS provisioning, no
RAE/Permission Broker/AG3/AG5 wiring. `HATP-001 v1.0` is
byte-unchanged; the independently verified requirement span remains
`HATP-REQ-001..117` (117 requirements).

## Baseline (confirmed before any edit)

- `git status --short`: clean. `origin/main..HEAD`: 0 commits.
- `pcae health`/`pcae check`/`pcae status coherence`: healthy / passed /
  coherent.
- `pcae doctor task-memory`: 2 pre-existing `tasks/DONE.md` sync
  warnings, unrelated to this phase, unchanged by this phase.
- `pcae push check`: nothing_to_push.
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`.
- `pcae phase-report show --latest` + `pcae phase-report reconcile
  --phase-id 149O.1H.4`: 149O.1H.4 confirmed `completed`, report
  `complete`, reconciled `already_dispatched`; recommended next phase
  `149O.1H.5` exactly.
- Wave-3 entering baseline: 515 passed (`test_hatp_proof_models.py` +
  `test_hatp_canonical_serialization.py` +
  `test_phase_149o_1g_...py` [100] + 149O.1H suite [166] + 149O.1H.1
  suite [93] + 149O.1H.2 suite [99] + 149O.1H.3 suite [57]). Combined
  with the 149O.1H.4 suite (105): 620 passed.

## B-149O.1H.4-1, restated

`_FRACTIONAL_SECONDS_RE = re.compile(r"\.(\d+)(?=Z$|[+-]\d{2}:\d{2}$)")`
(149O.1H.3) only matched a fractional-seconds group immediately
followed by `Z` or a colon-separated `+HH:MM`/`-HH:MM` offset. Python
3.11+'s `datetime.fromisoformat` also accepts non-colon offsets, so:

```
issued_at="...12:00:00.0000001+00"  -> guard regex: no match -> flows to fromisoformat -> microsecond=0
issued_at="...12:00:00.0000009+00"  -> guard regex: no match -> flows to fromisoformat -> microsecond=0
both canonicalize to "...12:00:00.000Z"
```

## Reproduction against unmodified (pre-149O.1H.5) source

```python
>>> from pcae.core.human_approval_trusted_provenance import _FRACTIONAL_SECONDS_RE, _parse_iso_timestamp
>>> _FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.0000001+00")
None
>>> _FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.0000001+0000")
None
>>> _parse_iso_timestamp("2026-01-01T12:00:00.0000001+00")
datetime.datetime(2026, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)   # should have been rejected
>>> _parse_iso_timestamp("2026-01-01T12:00:00.0000009+00")
datetime.datetime(2026, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)   # identical -- collision
```

Preserved as historical evidence in
`tests/test_phase_149o_1h_4_hatp_timestamp_canonicalization_final_independent_reverification.py`,
Section C, now run against an isolated import of the pinned pre-repair
commit (`3d6b5a9a`) rather than the live module (see "Historical
evidence preservation" below).

## Runtime parser offset-grammar probe (this interpreter, Python 3.14.5)

Direct `datetime.fromisoformat` probing (not relying on documentation
alone) confirmed the following are all accepted, each independently
capable of carrying a fractional-seconds bypass:

| Offset syntax | Accepted | Notes |
|---|---|---|
| `Z` (rewritten to `+00:00` by this module) | yes | covered pre-repair |
| `+HH:MM` / `-HH:MM` | yes | covered pre-repair |
| `+HH` / `-HH` (2-digit, no colon) | yes | **B-149O.1H.4-1 bypass** |
| `+HHMM` / `-HHMM` (4-digit, no colon) | yes | **B-149O.1H.4-1 bypass** |
| `+HH:MM:SS` / `+HHMMSS` | yes | discarded sub-minute offset precision entirely (`microsecond` unaffected regardless of fraction there — see "Offset-embedded fractional seconds" below) |
| `,` in place of `.` as the fractional-seconds separator | yes | **independent bypass, not previously probed** — the pre-repair regex matched only `\.`, so a `,`-separated fraction bypassed the guard through *every* suffix, including `Z` and colon offsets |
| bare space in place of `T` as the date/time separator | yes | not itself a fraction-detection bypass with the new anchor (see design below), but confirms the anchor must not depend on a literal `T` |
| naive (no offset at all) | yes, at the `fromisoformat` level (rejected downstream by this module's own `parsed.tzinfo is None` check, unrelated to the fraction guard) | the fraction guard must still reject a 7+-digit fraction here *before* that downstream check runs |

Probe script and full matrix output are captured verbatim in the
149O.1H.5 test suite (`test_probe_runtime_accepts_offset_suffix`,
`test_probe_runtime_accepts_comma_decimal_separator`,
`test_probe_runtime_accepts_space_date_time_separator`).

## Chosen guard architecture

Re-anchor fraction detection on the seconds field itself, not on the
suffix that follows it:

```python
_FRACTIONAL_SECONDS_RE = re.compile(r"(?<=:\d{2})[.,](\d+)")
```

The lookbehind `(?<=:\d{2})` requires two digits immediately preceded
by a colon — i.e. the `SS` seconds field, wherever it occurs, using no
assumption about the date/time separator (`T` or space) or what
follows the fraction. The `[.,]` covers both the `.` and `,` decimal
separators this runtime's parser accepts. `(\d+)` then captures every
contiguous digit run immediately following that separator — stopping
at the first non-digit character (`+`, `-`, `Z`, or end of string),
so a bare offset's own digits (`+0000`) are never captured: there is
no separator character positioned directly before them.

This satisfies the fix's guiding invariant: fraction-digit detection
no longer depends on which (if any) valid timezone-offset spelling
follows it. It also intentionally does *not* attempt full ISO-8601
grammar validation — malformed multi-separator forms (`12:00:00.123.456Z`,
`12:00:00..123Z`) are left to the downstream `datetime.fromisoformat`
call to reject; the guard only ever answers "does the seconds
fraction, if any, exceed 6 digits?".

### Multiple-dot / malformed-separator behavior

`re.search` returns the leftmost match. For `12:00:00.123.456Z`, the
lookbehind is satisfied only immediately after the first `SS.`
occurrence; `(\d+)` then captures `123` (stopping at the second `.`,
a non-digit) — 3 digits, lexically eligible, so the guard does not
reject it itself. `fromisoformat` subsequently rejects the malformed
double-fraction string with `ValueError`, which `_parse_iso_timestamp`
already converts to a parse failure (`InvalidProofSchemaError` via
`_require_issued_at`). For `12:00:00..123Z`, the lookbehind is
satisfied after the first `.`, but the very next character is another
`.` (not a digit), so `(\d+)` cannot match at that position at all —
the guard reports no fraction found, and `fromisoformat` rejects the
double-dot string on its own. Neither case is a bypass: in both, the
7+-digit rejection rule is not the mechanism that ultimately rejects
the string, but nothing accepts an invalid instant either.

### Offset-embedded fractional seconds (documented, out of scope)

The probe surfaced one degenerate edge this design does not fully
disambiguate from the main-timestamp fraction: `datetime.fromisoformat`
also accepts a UTC offset carrying its own seconds field
(`+00:00:00`) and even, on this interpreter, a fractional component on
*that* offset-seconds field (`+00:00:00.5`). Because this offset-
seconds field also matches `:\d{2}` immediately before a `.`, a
main-timestamp string with *no* real seconds-fraction but an
offset-fraction of 7+ digits (`...12:00:00+00:00:00.0000001`) is
lexically rejected by this guard even though `fromisoformat` itself
discards that offset-sub-second value unconditionally (confirmed:
`microsecond` is `0` regardless of how many digits follow `.` in the
offset, for any digit count 0 through 7+ — the offset's own fractional
seconds carry no information that could ever produce a distinct
instant or a collision). This is a conservative, fail-closed
over-rejection of an practically-unused ISO-8601 corner form, not a
security gap: no distinct-instant collision can occur through it,
because the parser statically discards that data regardless of the
guard. It is not addressed further, consistent with §8/§48 of the
governing prompt ("do not attempt full ISO-8601 syntax validation" /
"avoid parser-grammar duplication") — introducing offset-vs-seconds
disambiguation would itself be exactly the kind of independent ISO
grammar reconstruction the governing prompt warns against, for a form
that carries zero real precision either way.

## Before/after collision (repaired)

```python
>>> _require_issued_at("2026-01-01T12:00:00.0000001+00")
InvalidProofSchemaError: issued_at: fractional-second precision exceeds 6 digits ...
>>> _require_issued_at("2026-01-01T12:00:00.0000009+00")
InvalidProofSchemaError: issued_at: fractional-second precision exceeds 6 digits ...
>>> _require_issued_at("2026-01-01T12:00:00,0000001+00:00")
InvalidProofSchemaError: issued_at: fractional-second precision exceeds 6 digits ...
```

All three historical/newly-probed bypass classes (non-colon offset,
comma separator) are now rejected before `datetime.fromisoformat` ever
runs.

## Offset-syntax matrix (post-repair)

For every offset suffix confirmed accepted by this runtime (`Z`,
`+00:00`, `+0000`, `+00`, `+01:00`, `+0100`, `+01`, `-05:00`, `-0500`,
`-05`):

- 7+-digit fractions (`.0000001`, `.1234567`, `.9999999`) are rejected
  lexically, before parsing, for every suffix.
- No-fraction forms remain accepted and canonicalize correctly.
- 6-digit millisecond-aligned fractions (`.001000`) remain accepted and
  canonicalize identically regardless of suffix spelling for the same
  instant (`.001Z` == `.001+00` == `.001+0000` == `.001+00:00`;
  `13:00:00.001+01` == `13:00:00.001+0100` == `13:00:00.001+01:00` ==
  `12:00:00.001Z`).
- Distinct millisecond values (`.001` vs `.002`) remain distinct in the
  canonical string and digest.

Full parametrized coverage in
`tests/test_phase_149o_1h_5_hatp_timestamp_lexical_guard_widening.py`.

## Parser/constructor equivalence

Every new bypass-class input (non-colon offset, comma separator) was
tested through both `parse_hatp_proof` and the direct
`HumanApprovalProvenanceProof(...)` constructor, both sharing
`_require_issued_at`/`_parse_iso_timestamp` (unchanged sharing
architecture from B-149O.1H-2 — this phase touches only the shared
helper's internal regex, not the sharing itself). Both entry points
reject identically. `B-149O.1H-2` (public-constructor domain matches
structural parser domain) is confirmed unaffected: the constructor
regression suite (bool `proof_version`, invalid repository ID, invalid
digest, invalid commit SHA, empty identifier, family mismatch) all
still reject via direct construction.

## Millisecond-domain preservation (Stage 2, unchanged)

`microsecond % 1000 == 0` is untouched. `.001000` (millisecond-aligned)
remains accepted; `.001001` (not millisecond-aligned) remains rejected
— independently re-confirmed for every offset suffix.

## Canonical format / digest (Stage 3, unchanged)

`_canonical_timestamp_string` and `canonicalize_hatp_proof_payload`
were not modified. Canonical rendering remains
`YYYY-MM-DDTHH:MM:SS.mmmZ`. SHA-256 digest semantics unchanged; a
golden AG3 vector was recomputed and its digest independently
re-verified via `hashlib.sha256`. Mutation sensitivity re-confirmed:
`.001Z` → `.002Z` still changes the digest.

## Historical evidence preservation

`tests/test_phase_149o_1h_4_hatp_timestamp_canonicalization_final_independent_reverification.py`
Section C (renamed `test_historical_finding_*`) now runs against an
isolated `importlib`-loaded snapshot of the pre-149O.1H.5 commit
(`3d6b5a9a`, the 149O.1H.4 commit), using the same isolated-import
pattern Section A already established for the 149O.1H.2/149O.1H.3
boundary (`_load_module_at_commit`). This preserves the historical
finding as demonstrably reproducible evidence rather than deleting it,
per repository convention (Phase 149O.1H.3's own precedent update to
149O.1H.1's suite). A new Section D
(`test_repair_non_colon_offset_bypass_now_rejected_*`) asserts the
live, current production module now rejects the same inputs. No
pre-existing 149O.1G/149O.1H/149O.1H.1/149O.1H.2/149O.1H.3 test file
content was otherwise modified.

## Regressions

| Suite | Expected | Result |
|---|---|---|
| Wave-1/2 (`test_repository_identity.py` + `test_hatp_bootstrap_foundation.py` + 149O.1E/149O.1F/149O.1F.1) | 103 | **103 passed** |
| 149O.1F.2 | 90 | **90 passed** |
| Wave-3 baseline (100+166+93+99+57) | 515 | **515 passed** |
| Wave-3 baseline + 149O.1H.4 suite (post its own repair-verification update, 114) + 149O.1H.5 new suite (130) | -- | **759 passed** |
| Report-trust (`test_phase_reports.py` + `test_phase_reports_cli.py` + `test_phase_report_trust_hard_fail.py` + `test_push_phase_report_identity_137f1.py`) | 201 | **201 passed** |
| HATP contract/plan (`test_phase_149o_1c_*.py` + `test_phase_149o_1d_*.py`) | 127 | 126 passed / **1 failed while this repair's production edit was uncommitted** (`test_no_src_pcae_files_modified_this_phase`, a `git diff HEAD` dirty-tree check — same transient artifact class documented in 149O.1H.3's own report; re-verified clean after commit, see final report) |
| RAE/PB/agent broad (`-k 'rae or permission_broker or agent'`) + RAE canonical-provenance direct | 5 known pre-existing failures, 0 new | see final phase-completion report for the exact re-run count |
| Fast Green (`-m fast_green -n auto`) | 4531 | **4531 passed**, identical to the entering baseline (this phase's new test file is not in `tests/conftest.py`'s `FAST_GREEN_MODULES`, matching the precedent set by every prior 149O.1H.x phase's own new suite) |

## Finding status

- **B-149O.1H.4-1**: **REPAIRED** — the fractional-precision guard now
  covers every parser-accepted timestamp offset syntax probed on this
  runtime (colon/non-colon offsets of both 2- and 4-digit width, `Z`,
  naive, and both `.`/`,` decimal separators). Implementation-level
  only; independent re-verification still required.
- **B-149O.1H-1**: **REPAIRED AT IMPLEMENTATION LEVEL, PENDING
  INDEPENDENT RE-VERIFICATION.** Not marked independently closed by
  this implementation phase.
- **B-149O.1H-2**: remains **INDEPENDENTLY CONFIRMED CLOSED** — no
  regression introduced; constructor-hardening regression suite
  re-passed in full.
- **F-149O.1C-1**: remains confirmed implemented (unaffected).
- **F-149O.1C-2**: remains editorial debt only (unaffected).
- **B-149O.1F-1**, **B-149O.1R-1**, **B-149O.1R-2**: remain closed
  (unaffected).
- **B-149O-1..4**: remain **OPEN** (unaffected; out of this phase's
  scope entirely).

## Wave-3 status

**REPAIRED, PENDING FINAL INDEPENDENT RE-VERIFICATION.**

## HATP production readiness

**NOT READY.** A structurally valid HATP proof still does not imply
`HATP VALID`. No Wave-4 verifier, signature verification,
trusted-signer lookup, human-presence verification, FIDO2/PIV
provider, Class-B deployment, RAE/HATP integration, or AG3/AG5
production wiring was implemented or modified by this phase. Runtime
remains `Observed` / `observe` / `unavailable`.

## Recommended next phase

`149O.1H.6` — HATP Timestamp Canonicalization Final Independent
Verification. That verification phase must independently probe this
runtime's `datetime.fromisoformat` offset/separator grammar itself
(not merely trust this document's matrix), attempt to find any
remaining parser-accepted syntax this guard's `(?<=:\d{2})[.,](\d+)`
anchor does not cover, and confirm B-149O.1H-1 can finally be marked
independently closed before Wave 4 / `149O.1I` may begin.
