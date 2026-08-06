# Phase 149O.1H.4 -- HATP Timestamp Canonicalization Final Independent Re-Verification

**Status:** NOT VERIFIED -- BLOCKING finding.
**Phase type:** Verification-only. No production, contract, RAE, Permission
Broker, Agent, or Wave-4 code was modified by this phase.

## 1. Baseline

- Repository clean at phase start; `origin/main..HEAD` = 0.
- Latest completed phase: 149O.1H.3 (`acb511bb`), status completed, report
  completeness complete, pushed.
- `pcae health` / `pcae check` / `pcae status coherence`: healthy / passed /
  coherent.
- `pcae push check`: nothing_to_push.
- `pcae runtime inspect`: Runtime state Observed, execution capability
  unavailable, maximum plugin capability observe -- unchanged before and
  after this phase.
- `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.1H.3`: 149O.1H.3 confirmed completed, report complete,
  reconciled (`already_dispatched`), B-149O.1H-1 recorded as
  `repaired_pending_reverification`, B-149O.1H-2 recorded as unaffected/
  closed, recommended next phase 149O.1H.4 exactly.

## 2. Repair Diff Reconstruction (`01bacf8a..acb511bb`)

`git diff --name-only 01bacf8a..acb511bb -- src/pcae/` independently
reconstructed: exactly one file changed --
`src/pcae/core/human_approval_trusted_provenance.py`. **UNRELATED = 0.**

The single hunk adds `_FRACTIONAL_SECONDS_RE`,
`_reject_excess_fractional_precision`, and one call site inserted at the
top of `_parse_iso_timestamp`, before the `datetime.fromisoformat` call.
Classification: **RAW_TIMESTAMP_PRECISION_VALIDATION**, correctly placed
per **TIMESTAMP_PARSE_ORDER** (call precedes the lossy conversion
textually and at runtime -- independently confirmed by
`test_mandatory_ordering_lexical_guard_precedes_lossy_conversion`, which
inspects `inspect.getsource(_parse_iso_timestamp)` and asserts the guard
call's source offset is smaller than the `fromisoformat` call's offset).

## 3. Historical >6-Digit Collision Reproduction (Isolated Pre-Repair Source)

Independently loaded `human_approval_trusted_provenance.py` at commit
`01bacf8a` via `importlib` (isolated module name, never touching
`sys.modules`'s live production import). Against that isolated pre-repair
source:

- `.0000001Z` and `.0000009Z` both **ACCEPTED**.
- Both canonicalize to `2026-01-01T12:00:00.000Z` (identical).
- Both produce canonical payloads containing the identical
  `"issued_at":"2026-01-01T12:00:00.000Z"` bytes.

The historical defect remains demonstrably real against the actual
pre-repair production source, not merely against the bare interpreter.

`datetime.fromisoformat('...0000001+00:00').microsecond ==
datetime.fromisoformat('...0000009+00:00').microsecond == 0` independently
reconfirmed on this session's interpreter (Python 3.14.5) -- the
truncation the repair defends against remains a live CPython behavior.

## 4. Current Lexical Guard Reconstruction

`_FRACTIONAL_SECONDS_RE = re.compile(r"\.(\d+)(?=Z$|[+-]\d{2}:\d{2}$)")`,
called from `_parse_iso_timestamp` before `datetime.fromisoformat`.

- **Where inspected:** inside `_parse_iso_timestamp`, first statement
  after the type/emptiness guard, strictly before the `try:
  datetime.fromisoformat(...)` block.
- **How digits are identified:** a regex capturing one-or-more digits
  after a literal `.`, using a lookahead requiring the match be
  immediately followed by end-of-string `Z`, or a **colon-separated**
  `[+-]\d{2}:\d{2}` offset, at the end of the string.
- **Maximum accepted precision:** 6 digits (`len(match.group(1)) > 6`
  rejects).
- **Timezone suffix handling:** only two suffix shapes are recognized by
  the lookahead -- literal `Z` and a colon-separated numeric offset. Any
  other syntactically valid ISO-8601 timezone suffix that
  `datetime.fromisoformat` itself accepts is **not** matched by this
  lookahead.

## 5. Mandatory Ordering Verdict

**RAW PRECISION VALIDATION: PRECEDES LOSSY ISO DATETIME CONVERSION**

(True for every input shape the guard's regex actually matches. See
Finding B-149O.1H.4-1 below for the case where the regex fails to match
at all, and the value falls through to lossy conversion unguarded.)

## 6. Maximum Fractional Precision / Fraction-Length Matrix (0..12+)

Tested 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12 digit forms with a `Z` suffix:
0-6 digits lexically eligible (proceed to the millisecond-domain rule,
all-zero forms accepted); 7, 8, 9, 12 digits rejected lexically before
any `datetime` conversion. Matches the expected 0..6 / 7+ boundary
exactly for the `Z`-suffix and colon-offset domain.

## 7. Seven-Plus-Digit Adversarial Matrix

`.0000001`/`.0000009`, `.0010001`/`.0010009`, `.1234561`/`.1234569`,
`.9999991`/`.9999999`, `.123456789`/`.123456780`,
`.000000000001`/`.000000000009` -- each tested with `Z`, `+00:00`,
`+01:00`, `-05:00` suffixes: **all rejected** in the colon/`Z` domain.

## 8. BLOCKING FINDING B-149O.1H.4-1 -- Non-Colon Offset Bypasses the Lexical Guard, Reproduces the Original Collision

**Root cause:** `_FRACTIONAL_SECONDS_RE`'s lookahead
`(?=Z$|[+-]\d{2}:\d{2}$)` requires a *colon-separated* numeric offset (or
literal `Z`). Python 3.11+'s `datetime.fromisoformat` is materially more
permissive than the guard assumes -- it also accepts **non-colon**
offsets such as `+00` (2-digit) and `+0000` (4-digit, no colon). For
those forms, the guard's regex does not match at all, so
`_reject_excess_fractional_precision` never raises, and the raw
`issued_at` string flows straight into the historically lossy
`datetime.fromisoformat` call unguarded.

**Independent confirmation (regex level):**

```
>>> _FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.0000001+00")
None
>>> _FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.0000001+0000")
None
>>> _FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.0000001Z")
<re.Match object; span=(19, 27), match='.0000001'>
```

**Independent confirmation (parser level) -- exact reproduction of the
original B-149O.1H-1 collision:**

```
issued_at="2026-01-01T12:00:00.0000001+00"  -> ACCEPTED, issued_at == "2026-01-01T12:00:00.000Z"
issued_at="2026-01-01T12:00:00.0000009+00"  -> ACCEPTED, issued_at == "2026-01-01T12:00:00.000Z"
```

Both proofs' canonical payloads contain the byte-identical
`"issued_at":"2026-01-01T12:00:00.000Z"` field. Two distinct raw
`issued_at` claims -- differing in their 7th fractional digit --
canonicalize identically and would digest identically over an otherwise
identical payload. This is not a new defect class; it is the *exact*
B-149O.1H-1 defect, reachable through an offset syntax the 149O.1H.3
repair did not cover.

**Confirmed via both public entry points** -- `parse_hatp_proof` and the
direct `HumanApprovalProvenanceProof(...)` constructor produce the
identical (wrong) outcome, so this is **not** a parser/constructor
divergence and does **not** reopen B-149O.1H-2 (the shared
`_require_issued_at` validator is equally exposed on both paths, exactly
as B-149O.1H-2's architecture guarantees -- consistently wrong, not
divergently wrong).

**Scope of the bypass -- narrow, not wholesale:** most 7+-digit,
non-colon-offset values still truncate to a *non*-millisecond-aligned
microsecond value and are still caught by the pre-existing
`microsecond % 1000 != 0` semantic rule (independently confirmed for
`.1234567+05`, `.1234567-0500`, `.9999999+00` -- all still rejected).
Only the specific values whose truncated (first-6-digit) microsecond
value happens to already be millisecond-aligned -- i.e. digits 7+ are
the only non-zero content beyond the first 6, such as `.0000001` /
`.0000009` -- fully evade both layers. The bypass is real, reproducible,
and reopens the exact historical collision, but is not a full-precision
free-for-all.

**Constructor/parser equivalence audit:** unaffected by this finding --
both paths agree (wrongly) on the bypassed values. B-149O.1H-2 REMAINS
INDEPENDENTLY CONFIRMED CLOSED on its own terms (constructor domain ==
parser domain); this finding is scoped entirely to B-149O.1H-1.

## 9. Raw Input Variants / Malformed-Form Bypass Attempts

Lowercase `z`, naive (no timezone), trailing/leading whitespace, and
double-`Z` malformed forms were all independently confirmed **rejected**
(no bypass via simple textual mangling). Supported colon-offset and `Z`
forms cannot bypass >6-digit detection. The one confirmed bypass class is
syntactically **valid**, `datetime.fromisoformat`-accepted ISO-8601 --
not a malformed string -- which is precisely why it evades a
regex-shaped guard tuned to only two of `fromisoformat`'s several
accepted timezone-suffix shapes.

## 10. No-Fraction / 1-6 Digit Forms

`2026-01-01T12:00:00Z` still accepted. `.1`/`.12`/`.123`/`.1230`/
`.12300`/`.123000` all canonicalize to the same instant per their
semantic value (`.1`->`.100Z`, `.12`->`.120Z`, the four `.123*` variants
all ->`.123Z`).

## 11. Millisecond-Aligned / Non-Aligned <=6-Digit Forms

`.000000`/`.001000`/`.123000`/`.999000` accepted. `.000001`/`.000999`/
`.001001`/`.123456`/`.999999` rejected by the pre-existing
millisecond-domain rule -- independently confirmed as a layer distinct
from the lexical guard (`_reject_excess_fractional_precision` does not
itself raise on `.123456`; the full `_require_issued_at` call still
rejects it via the semantic layer).

## 12. Original 149O.1H.1 / Current 149O.1H.2 Collision Regressions

`.0001Z`/`.0009Z` (149O.1H.1's own repair target) remain rejected -- no
regression. `.0000001Z`/`.0000009Z` (the `Z`/colon-offset domain) remain
rejected by the 149O.1H.3 repair -- confirmed. (The **non-colon** variant
of this exact pair is Finding B-149O.1H.4-1, §8 above.)

## 13. Losslessness / Injectivity / Timezone Equivalence (Guarded Domain)

Within the domain the 149O.1H.3 guard actually covers (`Z` suffix,
colon-separated offsets): every accepted raw sample loses no non-zero
significant fractional digit before the millisecond-domain check; a
broad bounded sweep (3 dates x 3 hours x ~77 millisecond values, 693
total) produced zero canonical collisions; `12:00:00.001Z ==
13:00:00.001+01:00 == 07:00:00.001-05:00 == 12:00:00.001+00:00`;
`12:00:00.001Z != 12:00:00.002Z` at both the canonical-string and digest
level.

## 14. Parser/Constructor Equivalence

No-fraction, millisecond, 6-digit millisecond-aligned, invalid
sub-millisecond, invalid 7-digit, invalid 9-digit, malformed, and naive
forms all produce identical accept/reject outcomes through
`parse_hatp_proof` and direct `HumanApprovalProvenanceProof(...)`
construction, including on the bypassed non-colon-offset values (§8).

## 15. B-149O.1H-2 Regression

Boolean `proof_version`, invalid repository ID, invalid digests, invalid
commit SHA, empty required identifier, AG3/AG5 family mismatch: all still
independently confirmed rejected via direct construction. **B-149O.1H-2
REMAINS INDEPENDENTLY CONFIRMED CLOSED.**

## 16. Closed Schema / Duplicate Keys / AG3-AG5 Discrimination

Unknown-field attacks (`trusted_root`, `trusted_public_key`,
`attestation_root`, `authority_registry`, `canonical_root`,
`trust_store_root`, `deployment_root`, `approved`, `trusted`,
`authorized`, `human_present`, `valid`, `arbitrary_unknown`): all
rejected. Duplicate top-level key: rejected (`MalformedProofError`).
Wrong-family payload and unknown family (`AG7`): rejected. AG3 vs AG5
proofs of the same instant produce distinct digests.

**F-149O.1C-1: INDEPENDENTLY CONFIRMED IMPLEMENTED** (closed-schema
enforcement unaffected).

## 17. Signed-Payload Reconstruction / Completeness

All HATP-REQ-069 fields independently reconstructed and confirmed present
in `hatp_proof_to_document`'s output: `proof_version`, `principal_id`,
`signer_key_id`, `provider_profile`, `repository_id`,
`decision_record_id`, `decision_record_digest`, `binding_id`,
`binding_digest`, `rollback_site`, `issued_at`, plus the family-specific
fields (`job_id`/`original_commit_sha` or `per_id`/`ecp_id`). No raw
lexical "shadow" timestamp field was introduced by the 149O.1H.3 repair.

**SIGNED PAYLOAD: COMPLETE FOR HATP-001 WAVE-3 SECURITY SEMANTICS.**

## 18. Independent Golden Vectors + SHA-256 Verification

Independently written canonicalizer (not calling or copying
`canonicalize_hatp_proof_payload`) constructs expected AG3 and AG5
documents and independently JSON-encodes them
(`sort_keys=True, separators=(",", ":"), ensure_ascii=False,
allow_nan=False`). Production `canonicalize_hatp_proof_payload` output
compared byte-for-byte: **identical** for both families. SHA-256
independently recomputed via `hashlib.sha256(...).hexdigest()`: matches
`digest_hatp_proof_payload` exactly, for both the golden vectors and an
additional millisecond fixture (`2026-03-04T05:06:07.008Z`).

## 19. Canonical Serializer / Mutation Sensitivity / Purity / Dependency / Public API Audits

Key-order independence, whitespace independence, and Unicode round-trip
all confirmed unchanged. Timestamp mutation (`.001Z` -> `.002Z`) alters
the digest. Model immutability (top-level and nested frozen dataclasses)
confirmed. No filesystem/network/environment/wall-clock/randomness call
found in the production module's actual code (import-statement and
call-site level scan, distinct from docstring prose that *discusses*
what is deliberately absent). No import of `hatp_bootstrap`,
`rollback_approval_evidence`, `permission_broker*`, `agent.py`, or
`commands/agent.py`. No `VALID`/`UNKNOWN_SIGNER`/`approval_present`/
`HATP_VALID` symbol in the module's runtime namespace or in
`hatp_proof_to_document`'s output keys.

## 20. Structural/Trust Separation

Explicitly reconfirmed: parse success, canonicalization success, and
digest success carry no `signature_valid`/`signer_trusted`/
`human_present`/`authorized`/`hatp_valid` attribute or document key. A
structurally valid HATP proof still does NOT imply HATP VALID.

## 21. Report-Trust Self-Hosting

This phase's own canonical report round-trips through the repaired
phase-report evidence-coherence path (`pcae phase-report reconcile
--phase-id 149O.1H.4` at completion time; see final governance report).

## 22. Regressions (Exact Counts Observed)

| Suite | Expected | Observed |
|---|---|---|
| Wave-3 baseline (`test_hatp_proof_models.py` + `test_hatp_canonical_serialization.py` + `test_phase_149o_1g_...py`) | 100 | **100** |
| 149O.1H | 166 | **166** |
| 149O.1H.1 | 93 | **93** |
| 149O.1H.2 | 99 | **99** |
| 149O.1H.3 | 57 | **57** |
| Combined Wave-3 baseline | 515 | **515** |
| Combined Wave-3 baseline + this phase's 105 new tests | -- | **620** |
| Wave-1/2 (`test_repository_identity.py` + `test_hatp_bootstrap_foundation.py` + `test_phase_149o_1e_...py` + `test_phase_149o_1f_...py` + `test_phase_149o_1f_1_...py`) | 103 | **103** |
| 149O.1F.2 | 90 | **90** |
| Report-trust (`test_phase_reports.py` + `test_phase_reports_cli.py` + `test_phase_report_trust_hard_fail.py` + `test_push_phase_report_identity_137f1.py`) | 201 | **201** |
| HATP contract/plan (`test_phase_149o_1c_...py` + `test_phase_149o_1d_...py`) | -- | **127 passed** |
| RAE/Permission Broker/Agent, broad `-k 'rae or permission_broker or agent'` | pre-existing 5 failures | **1 failed / 5399 passed** (`test_phase_148f_..._test_permission_broker_consumer_scope_inventory`, the same known pre-existing failure documented in 149O.1H.3) |
| RAE canonical-provenance suite run directly (`-k` did not select it -- filename lacks "rae"/"permission_broker"/"agent") | -- | **4 failed / 13 passed**, all 4 matching the known pre-existing B-149O-1..4 findings |
| Combined RAE/PB/agent pre-existing-failure total | 5 | **5** (1 + 4), matching the 149O.1H.2/149O.1H.3 baseline exactly -- zero new failures |
| Fast Green (`-m fast_green -n auto`) | 4531 | **4531** |

No new failures introduced anywhere. All mismatches from the phase
brief's predicted counts (none found) would have been reported here as
findings; none occurred -- every regression suite matched its expected
count exactly.

## 23. New Independent Verification Suite

`tests/test_phase_149o_1h_4_hatp_timestamp_canonicalization_final_independent_reverification.py`
-- 105 tests, all passing, covering: isolated pre-repair source
reproduction, current-source ordering/fraction-matrix/offset coverage,
the B-149O.1H.4-1 bypass finding (regex-level, parser-level,
constructor-level, scope-boundary), malformed-form rejection,
injectivity sweep, timezone equivalence, distinct-millisecond
sensitivity, parser/constructor equivalence, B-149O.1H-2 constructor
regressions, closed-schema/duplicate-key/AG3-AG5 regressions,
independent AG3/AG5 golden vectors, SHA-256 verification, canonical
serializer semantics (key-order/whitespace/Unicode), mutation
sensitivity, model immutability, purity/dependency/public-API audits,
and structural/trust separation.

## 24. Findings

- **B-149O.1H.4-1 (BLOCKING):** The 149O.1H.3 lexical guard's regex
  covers only `Z`-suffix and colon-separated-offset timestamp syntax.
  Python 3.11+'s more permissive `datetime.fromisoformat` also accepts
  non-colon numeric offsets (`+00`, `+0000`, etc.), which the guard's
  lookahead does not match. For 7+-digit fractional values whose
  truncated (first-6-digit) microsecond value is already
  millisecond-aligned (e.g. `.0000001`, `.0000009`), this fully bypasses
  both the lexical guard and the pre-existing millisecond-domain rule,
  reproducing the exact original B-149O.1H-1 collision end-to-end
  (identical canonical timestamp, identical canonical payload field).
  Confirmed via both `parse_hatp_proof` and direct
  `HumanApprovalProvenanceProof(...)` construction -- consistent across
  both paths (not a parser/constructor divergence; B-149O.1H-2 itself is
  not reopened). Reproduced in
  `test_finding_non_colon_offset_bypasses_lexical_guard_and_is_accepted`,
  `test_finding_non_colon_offset_reproduces_exact_original_collision_parser`,
  `test_finding_non_colon_offset_reproduces_exact_original_collision_constructor`,
  and `test_finding_lexical_guard_regex_does_not_match_non_colon_offset_directly`.
  **Recommend a narrow repair phase (149O.1H.5)** that widens the guard's
  timezone-suffix recognition to match every offset syntax
  `datetime.fromisoformat` itself accepts (or, more robustly, inspects
  fractional-digit count independent of any assumed suffix shape) --
  this phase does NOT implement that repair.
- **F-149O.1C-1:** INDEPENDENTLY CONFIRMED IMPLEMENTED (unaffected,
  re-evaluated this phase).
- **F-149O.1C-2:** remains editorial debt only.
- Pre-existing non-blocking observations (uppercase repository UUID
  lexical variant, whitespace opaque identifiers, no digest
  domain-separation prefix, lone surrogate rejection at canonicalization,
  broader Python ISO syntax differences outside the accepted security
  domain) remain unchanged and out of this phase's narrow scope; not
  broadened.

## 25. Verdicts

**Canonicalization verdict:** Within the domain the 149O.1H.3 guard
actually covers, canonicalization is deterministic, unambiguous, and
lossless. However, because Finding B-149O.1H.4-1 demonstrates a live,
reproducible non-injective collision over the *actually accepted* raw
input domain (the guard does not reject every syntactically valid
7+-digit timestamp `datetime.fromisoformat` accepts), the domain-wide
injectivity property does **not** hold:

> **B-149O.1H-1 REOPENED -- LOSSY / NON-INJECTIVE TIMESTAMP DOMAIN REMAINS**

**B-149O.1H-2 verdict:**

> **B-149O.1H-2 REMAINS INDEPENDENTLY CONFIRMED CLOSED -- PUBLIC CONSTRUCTOR DOMAIN MATCHES STRUCTURAL PARSER DOMAIN**

**Overall Wave-3 verification verdict:**

> **NOT VERIFIED -- BLOCKING HATP WAVE 3 FINDINGS**

**Wave-3 readiness:** Wave 3 is NOT ready for Wave 4 implementation until
B-149O.1H.4-1 is repaired and independently re-verified.

**HATP production readiness (unconditional regardless of the above):**

> **HATP PRODUCTION: NOT READY** -- no Wave-4 verifier, no real provider,
> no Class-B deployment, no RAE integration.

## 26. Explicit No-Go Confirmations

HATP-001 v1.0 remained byte-unchanged this phase; zero
`docs/contracts/**` files touched. No production source was modified by
Phase 149O.1H.4 -- `git diff --name-only <pre-phase>..HEAD -- src/pcae/`
is empty. Canonical proof shape remained unchanged. Canonical
signed-payload field set remained unchanged. Canonical millisecond
timestamp format remained unchanged. SHA-256 digest semantics remained
unchanged. Wave 1 remained unchanged. Wave 2 remained unchanged.
B-149O.1F-1 remains confirmed closed. B-149O.1R-1 remains closed.
B-149O.1R-2 remains closed. F-149O.1C-1 was independently re-evaluated
and remains confirmed implemented. F-149O.1C-2 remains editorial debt
only. A Wave-4 verifier was not implemented. Signature verification was
not implemented. Provider attestation verification was not implemented.
Trusted-signer lookup was not implemented. Human-presence verification
was not implemented. A FIDO2 provider was not implemented. A PIV
provider was not implemented. A Class-B deployment was not provisioned.
RAE/HATP integration was not implemented. AG3/AG5 production wiring was
not implemented. A structurally valid HATP proof still does not imply
HATP VALID. B-149O-1 through B-149O-4 remain OPEN. HATP production
remains NOT READY. Runtime remains Observed / observe / unavailable. No
governance bypass, `--no-verify`, or force push was used.

## 27. Recommended Next Phase

Because Finding B-149O.1H.4-1 is BLOCKING (an accepted raw timestamp
still canonicalizes non-injectively via a live, reproducible bypass), per
the governing phase logic this phase does **not** recommend 149O.1I
(Wave 4). It recommends:

> **149O.1H.5 -- HATP Timestamp Canonicalization Lexical Guard Widening
> (Narrow Repair)** -- widen or replace
> `_FRACTIONAL_SECONDS_RE`'s timezone-suffix recognition so that every
> ISO-8601 timezone-offset syntax `datetime.fromisoformat` itself accepts
> is covered by the pre-conversion fractional-precision guard (or adopt a
> suffix-independent fractional-digit-count check), followed by a
> 149O.1H.6 independent re-verification before Wave 4/149O.1I may begin.

This phase (149O.1H.4) does not implement that repair and does not begin
149O.1I, per its verification-only mandate.
