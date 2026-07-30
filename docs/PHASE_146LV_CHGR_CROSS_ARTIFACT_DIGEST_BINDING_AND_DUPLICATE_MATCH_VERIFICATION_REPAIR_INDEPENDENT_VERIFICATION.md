# Phase 146LV: CHGR Cross-Artifact Digest-Binding and Duplicate-Match Verification Repair Independent Verification

**Predecessor:** Phase 146L (`5485dcf0`)
**Mode:** Independent Implementation Verification
**Verified against:** repository state at `3d9dc92c` (HEAD, `origin/main`, clean, 0 ahead/0 behind)

## 1. Executive Summary

Phase 146L's verifier-only repair to `src/pcae/governance/verification.py`
was independently re-derived from CHGR-001 v1.3 §30 (CHGR-REQ-210–216)
without trusting Phase 146L's own report, tests, or code comments as
proof. A 36-scenario adversarial matrix was independently constructed
against two genuine `build_publication_record` bundles and executed
directly through the internal API; every outcome matched the frozen
contract exactly. A full live production workflow (decision session →
evidence → selection → preview → confirmation → readiness → CHGR
publish → verify → inspect) was run end to end through the real CLI,
producing a fifth genuine bundle; exact siblings verified, a
cryptographically re-signed cross-bundle confirmation forgery was
rejected, and a duplicate sibling was rejected — all through the actual
`pcae` executable, not a stub. CLI argument-order determinism was
confirmed across repeated fresh-process invocations. 223 focused
regression tests passed; the `fast_green` sentinel reproduced the
4391/4391 baseline every prior 146-series phase has cited.

**Verdict: VERIFIED WITH NON-BLOCKING FINDINGS.** No Blocking finding was
identified. Two Non-Blocking findings and one Informational finding are
recorded in §18.

## 2. Authorization and Scope

Authorized to independently verify Phase 146L's repair against CHGR-001
v1.3 §30 (CHGR-REQ-210–216). Explicitly forbidden from repairing any
discovered defect, modifying production code, verification code,
contracts, schemas, the manifest, publication construction, the
Publication Coordinator, or migrating fixtures. This report, optional
independent adversarial test scripts (not committed to `tests/`, kept in
the session scratchpad only — see §21 No-Go Confirmation), and governance
bookkeeping are the only outputs.

## 3. Independent Contract Reconstruction

Read directly from `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
§30 (lines 2201–2760), independent of Phase 146L's own report text:

- **CHGR-REQ-210**: `integrity_ref.record_digest` is schema-required,
  reference-authoring-time-only, and is explicitly **not** the
  authoritative proof of binding — no verifier may reject solely because
  it disagrees with the resolved integrity artifact's own `record_digest`.
- **CHGR-REQ-211**: the reciprocal binding
  `governance_record_integrity.payload_digest ==
  human_governance_record.record_digest` is the authoritative
  anti-substitution proof for the integrity sibling.
- **CHGR-REQ-212**: `confirmation_evidence_ref` and `provenance_ref`
  verification SHALL reject when the reference's own `record_digest`
  does not exactly equal the resolved sibling's actual `record_digest`
  (no exception — no construction-time cycle constrains either).
- **CHGR-REQ-213**: resolving any of the three references SHALL reject
  if more than one supplied candidate matches the reference's
  `record_id` (and, per the literal text, `record_family` — see §18
  Finding NB-1 below for a nuance the implementation resolves more
  conservatively than the literal text requires). First-match selection
  is explicitly forbidden as the sole resolution rule.
- **CHGR-REQ-214**: freezes `record.py`'s existing seven-step
  construction sequence (confirmation → provenance → provisional
  integrity digest → final `human_governance_record` → final
  `governance_record_integrity`) as contractually binding, with no
  post-step-5 mutation of `human_governance_record.record_digest`.
- **CHGR-REQ-215**: pre-146K bundles carrying a well-formed but
  non-matching `integrity_ref.record_digest` remain valid without
  migration or regeneration, provided CHGR-REQ-211's reciprocal check
  holds.
- **CHGR-REQ-216**: no requirement CHGR-REQ-001–209 is narrowed,
  superseded, or reworded; §30 is purely additive.

§30.8's verification-contract table and §30.11's verification matrix
were independently re-derived (not copied) as the basis for §16 below.
CHGR-REQ-081/082 (a reference SHALL cite an identifier and, where
deterministic referencing is required, a digest) were re-read directly
(lines 1010–1015): neither requirement's own text mandates byte-for-byte
digest equality enforcement — that enforcement rule is supplied by
§30's verification-layer design, confirming §30.3's own claim that no
existing requirement's wording is narrowed. §18 (Security Contract) was
independently re-read: "one record being substituted for another under
the same identifier" is a named threat this section's Model C directly
targets, and the contract's fail-closed default ("this contract's
default response to any detected ambiguity or verification gap is to
treat the affected record as not currently authoritative... never a
best-effort or benefit-of-the-doubt default") was used as the standard
against which §18 (Findings) below classifies the one implementation/
contract-text divergence identified.

## 4. Code-Path Reconstruction

Read directly (not from 146L's own description):

- `src/pcae/governance/verification.py` (642 lines, full read) — the
  nested `_resolve_related` closure (lines 358–390) is the single,
  centralized resolution path for all three reference roles. It builds
  `identity_candidates` by `record_id` equality over the full
  caller-supplied `related_records` list (order-independent — a Python
  list comprehension, not a first-match scan), rejects on `len == 0`
  (`"not_supplied"` → skipped) or `len > 1` (`"ambiguous"` →
  `RELATED_ARTIFACT_AMBIGUOUS`), then checks family, self-consistency
  (schema shape + self-digest), and — only when
  `enforce_reference_digest=True` (confirmation and provenance call
  sites, never integrity) — exact reference-digest equality. No
  generic first-match path remains active anywhere in the module; the
  old `_find_related` name and closure no longer exist in this file.
- `src/pcae/governance/publication/record.py` (300 lines, full read) —
  confirmed byte-for-byte unmodified by 146L (not in its commit's
  changed-file list, §12); construction sequence matches CHGR-REQ-214's
  seven steps exactly, including the provisional-integrity-digest
  pattern (`provisional_digest4`, `_PLACEHOLDER_DIGEST`) that creates
  the CHGR-REQ-210 exception in the first place.
- `src/pcae/commands/governance_record.py` (261 lines, full read) — the
  `verify` subcommand reads `--related` paths in the exact order
  supplied and passes them straight through as a tuple to
  `verify_artifact_at_path`; no reordering, deduplication, or filtering
  occurs at the CLI layer, so any order-independence guarantee must (and
  does, per §9 below) originate entirely inside `_resolve_related`.
- `src/pcae/schema_resources/chgr/**` and the schema manifest — not
  read line-by-line in full (no change is authorized or claimed to
  these files), but their entry points (`references.schema.json`,
  `digest.schema.json`, `manifest.json`) were spot-checked via
  `_shape_check`'s manifest-lookup logic in `verification.py` and
  confirmed unreferenced by any 146L diff (§12).

Trace of the four dispatch call sites: `confirmation_evidence_ref`
(`enforce_reference_digest=True`, line 392), `provenance_ref`
(`enforce_reference_digest=True`, line 468), `integrity_ref`
(`enforce_reference_digest=False`, line 549), and `template_ref`
(a structurally separate, pre-existing, unrelated resolution loop at
line 597 that CHGR-REQ-210–216 does not govern and 146L did not touch).

## 5. Confirmation Reference Verification

Independently constructed two genuine bundles (A, B) via the real,
unmodified `build_publication_record` and ran nine scenarios directly
against `verify_artifact_at_path` (script retained in session scratchpad,
not committed per the No-Go Boundary):

| # | Scenario | Result | Error code |
|---|---|---|---|
| 1 | Genuine exact sibling | PASS | — |
| 2 | Correct ID, wrong digest (self-consistent, resigned) | REJECT | `REFERENCE_DIGEST_MISMATCH` |
| 3 | Correct digest, wrong ID (bundle B's confirmation, unmodified) | PASS (check `skipped`, not silently passed as bound) | — |
| 4 | Correct ID+digest, wrong `record_type` | REJECT | `RELATED_ARTIFACT_FAMILY_MISMATCH` |
| 5 | Unrelated cross-bundle confirmation alone | PASS (`confirmation_binding` explicitly `skipped`) | — |
| 6 | Rewritten cross-bundle ID + recomputed self-digest | REJECT | `REFERENCE_DIGEST_MISMATCH` |
| 7 | Malformed candidate (missing required field) | REJECT | (schema-shape failure classified `DIGEST_MISMATCH` — see §13) |
| 8 | Invalid self-digest (tampered, not resigned) | REJECT | `DIGEST_MISMATCH` |
| 9 | Matches reference digest but breaks semantic binding | Not independently constructible — see below | — |

Scenario 9 is a genuine finding, not a test gap: `record_digest` covers
the artifact's **entire** canonical payload including
`preview_rendering_digest`, so any semantic mutation necessarily changes
the candidate's own digest, which then fails CHGR-REQ-212's exact-match
gate before the semantic `confirmed_content_digest ==
preview_rendering_digest` check (line 439) is ever reached. This
confirms §30.6's claim that reference-digest matching is *additive to*,
not a *replacement for*, semantic verification is vacuously true for
confirmation/provenance (the exact-digest gate makes the semantic check
unreachable by any artifact that also fails it) — recorded as
Informational finding I-1 (§18).

## 6. Provenance Reference Verification

The identical nine-scenario matrix was re-run against `provenance_ref`
independently (own script section, not a parametrized reuse of §5's
code): all nine outcomes matched CHGR-REQ-212/213 exactly, including the
`selected_option_id` semantic-check variant of scenario 9 (also
unreachable independently of the digest gate, same finding as I-1).

## 7. Directed Integrity Verification

Independently confirmed via direct inspection (not 146L's own claim)
that `integrity_ref.record_digest` (`e7bdaee8…`) never equals the
resolved `governance_record_integrity` artifact's actual `record_digest`
(`f490ec51…`) for genuine bundle A — this is a structural property of
`record.py`'s provisional-digest construction (§30.2), reproduced
independently by direct field comparison, not asserted. Nine scenarios
run:

| Scenario | Result | Error code |
|---|---|---|
| Genuine current bundle | PASS | — |
| Genuine legacy-shaped (provisional-digest) bundle | PASS — is in fact **every** bundle this construction path produces, confirmed structurally in §7 above, not merely for a synthetic "legacy" fixture | — |
| Wrong integrity ID (cross-bundle, unmodified) | PASS, check `skipped` (id mismatch, no candidate) | — |
| Wrong `record_type` | REJECT | `RELATED_ARTIFACT_FAMILY_MISMATCH` |
| Wrong `payload_digest` (same id, forged) | REJECT | `DIGEST_MISMATCH` |
| Cross-bundle forged integrity (B's payload_digest, A's id, resigned) | REJECT | `DIGEST_MISMATCH` |
| Malformed integrity artifact | REJECT | `DIGEST_MISMATCH` |
| Invalid integrity self-digest | REJECT | `DIGEST_MISMATCH` |
| Exception-scope isolation | Confirmed: only the integrity call site passes `enforce_reference_digest=False`; both other call sites pass `True` (line 393, 469, 550 read directly) | — |

CHGR-REQ-210's non-enforcement is real and exclusive to `integrity_ref`
— independently confirmed both by static reading of the three call
sites' `enforce_reference_digest` arguments and dynamically by
scenario 2 (§5)/10 (§6) rejecting on digest mismatch while the
integrity equivalent does not.

## 8. Duplicate-Match Verification

All three roles tested for: byte-identical duplicates, same-ID/
different-digest duplicates, one-valid-plus-one-invalid-candidate, and
different-families-sharing-an-ID:

| Case | Confirmation | Provenance | Integrity |
|---|---|---|---|
| Exact byte-identical duplicate | REJECT `RELATED_ARTIFACT_AMBIGUOUS` | REJECT `RELATED_ARTIFACT_AMBIGUOUS` | REJECT `RELATED_ARTIFACT_AMBIGUOUS` |
| Same ID, different digest | REJECT `RELATED_ARTIFACT_AMBIGUOUS` | (same code path, not re-tested per role — mechanism is family-agnostic) | (same code path) |
| One valid + one same-ID wrong-family | REJECT `RELATED_ARTIFACT_AMBIGUOUS` | — | — |
| Different families sharing an ID (both orderings) | REJECT `RELATED_ARTIFACT_AMBIGUOUS`, identical both orders | — | — |

**Contract-precision finding (Non-Blocking, NB-1):** CHGR-REQ-213's
literal text conditions ambiguity on candidates matching *both*
`record_id` **and** `record_family`. `_resolve_related`'s
`identity_candidates` filters by `record_id` alone (line 377); family is
checked only *after* the ambiguity gate, and only against the sole
surviving candidate when exactly one exists. Consequently, two
candidates sharing an ID but differing in family are classified
`RELATED_ARTIFACT_AMBIGUOUS` by the implementation, where a literal
reading of CHGR-REQ-213 would classify them as: one candidate correctly
matching id+family (proceed to family/digest checks) and one candidate
that does not match at all (silently ignored, not itself a rejection
ground). Both readings **reject** the case (the implementation via
`RELATED_ARTIFACT_AMBIGUOUS`, the literal reading via whatever
`family_mismatch`/`digest_mismatch` outcome the single surviving
candidate would separately produce), so this is not exploitable as an
acceptance bypass and is consistent with §18's Security Contract
fail-closed default and with §30.9's own stated security analysis
("Duplicate sibling injection: rejected outright... independent of
which candidate is genuine"). It is a stricter-than-literal-text
implementation choice, not a weaker one. Classified Non-Blocking because
`record_id`s are UUID4 (`uuid.uuid4().hex`, `record.py` line 88) — a
genuine different-family collision on a caller-supplied related artifact
in real operation is not a realistic scenario this finding could ever
surface outside of adversarial construction, and the adversarial
construction case it does affect still rejects.

## 9. Argument-Order Determinism

Re-ran the genuine three-sibling set through six random shuffles inside
one process (all six produced `PASS` with identical check sets) and
through the real `pcae governance-record verify` CLI in three fresh,
independent subprocess invocations (forward order, fully reversed order,
interleaved order) against a fourth, separately-constructed genuine
bundle — all three produced byte-identical `checks` arrays and
`outcome: verified`. The duplicate-confirmation ambiguity case (§8) was
also independently re-run in both argument orders (`30a`/`30b` in the
adversarial script) with identical `RELATED_ARTIFACT_AMBIGUOUS` outcomes.
No case examined depends on input order, filesystem order, or process
identity — consistent with `_resolve_related`'s pure list-comprehension
candidate scan (no dict, no set, no first-match break).

## 10. Cross-Bundle Attack Results

Two independent cross-bundle impersonation attempts, per the
authorization's exact procedure (retarget `record_id` to the victim
bundle's referenced ID, recompute the forged artifact's own
`record_digest`, retain the donor bundle's substantive content):

1. **Confirmation forgery** (in-memory bundles A/B): rejected,
   `REFERENCE_DIGEST_MISMATCH` — the forged artifact's freshly
   recomputed digest does not equal `confirmation_evidence_ref`'s
   exact expected digest, exactly as CHGR-REQ-212 requires.
2. **Confirmation forgery against a live, CLI-published production
   bundle**: constructed a fifth genuine bundle end-to-end through the
   real CLI (§15), took the confirmation artifact from an unrelated,
   separately-constructed CLI-published bundle, retargeted its
   `record_id` to the live bundle's `confirmation_evidence_ref.record_id`,
   recomputed its digest via the same production `compute_record_digest`
   function, and supplied it to `pcae governance-record verify` against
   the live bundle's real `human_governance_record.json` on disk:
   rejected, `REFERENCE_DIGEST_MISMATCH`, through the actual installed
   CLI binary, not the internal API.
3. **Integrity forgery** (in-memory bundles A/B): rejected,
   `DIGEST_MISMATCH` — via the directed payload-binding check
   (`integrity.payload_digest != declared_digest`, line 585), not via
   any reference-digest equality (none is computed for integrity),
   exactly as CHGR-REQ-211 mandates as the authoritative anti-
   substitution proof and CHGR-REQ-210 mandates as *not itself* a
   rejection ground.

## 11. Missing and Extra Artifact Behavior

- No related artifacts supplied: `verified`, with
  `confirmation_binding`/`provenance_consistency`/`integrity_consistency`
  all explicitly `skipped` — never silently passed, never rejected.
  Independently confirmed the disclosed check-name/status pairs, not
  merely the top-level outcome.
- Extra valid, unrelated (non-matching-ID) artifact present alongside a
  complete genuine set: `verified`, unchanged — the extra artifact
  never contributes an `identity_candidates` match for any of the three
  references and cannot cause accidental role substitution because
  `_resolve_related` never selects by role/position, only by exact
  `record_id` equality.
- Extra malformed/unknown-schema artifact (arbitrary JSON with no valid
  CHGR envelope beyond the two required top-level keys) present:
  `verified`, unchanged — irrelevant because it too fails to match any
  reference's `record_id`.
- No retained "optional verification mode" beyond the disclosed
  skip-on-missing behavior was found; there is exactly one verification
  entry point (`verify_artifact_at_path`) and no configuration flag
  altering its fail-closed behavior.

## 12. Fixture Migration Assessment

Three fixtures were changed by 146L (`5485dcf0`), independently diffed
against their pre-146L blobs:

- `tests/fixtures/chgr/valid_record_published.json`: only
  `confirmation_evidence_ref.record_digest`,
  `provenance_ref.record_digest`, and the record's own top-level
  `record_digest` changed. Independently recomputed: the new
  `confirmation_evidence_ref.record_digest` (`ca95401d…`) and
  `provenance_ref.record_digest` (`8e2a2f3b…`) now equal the actual,
  unmodified `record_digest` fields of the sibling fixtures
  `valid_confirmation_evidence.json` and `valid_provenance.json`
  respectively (verified by direct field read, not assumed) — these two
  sibling fixtures were **not** in 146L's changed-file list and were
  independently confirmed unmodified.
- `tests/fixtures/chgr/valid_integrity.json`: `payload_digest` and
  `record_digest` changed. The new `payload_digest`
  (`fdd0c12d…`) equals the *new* `record_digest` of
  `valid_record_published.json` exactly (the reciprocal CHGR-REQ-211
  binding, independently re-verified by direct comparison) — the old
  `payload_digest` equaled the *old* `record_digest` identically, so
  this is a pure cascade: correcting the two exact-match references
  changed `valid_record_published`'s own digest (any field change
  changes the whole-payload digest), which forced `valid_integrity`'s
  reciprocal `payload_digest` to be recomputed to keep pointing at the
  now-different final value, which in turn forced `valid_integrity`'s
  own `record_digest` to be recomputed.
- `tests/fixtures/chgr/adversarial_assurance_overclaim_selfconsistent.json`:
  same pattern — only `confirmation_evidence_ref.record_digest` and the
  record's own `record_digest` changed, cascading from correcting the
  reference to point at its sibling
  `adversarial_assurance_overclaim_selfconsistent_confirmation.json`'s
  real, unmodified digest.

No substantive (non-digest) field was altered in any of the three
fixtures — confirmed by independent `git diff` inspection line-by-line
(§12 above shows the complete diffs). This is exactly the migration
CHGR-REQ-212's new exact-match gate necessitates: these three fixtures
previously carried schema-valid but factually mismatched reference
digests (permitted pre-146L because the verifier never checked them),
and would otherwise now spuriously fail `REFERENCE_DIGEST_MISMATCH`
against their own genuine, unmodified siblings.

**Adjacent, unmigrated fixtures**: `adversarial_confirmation_content_mismatch.json`
is consumed by exactly one test
(`test_chgr_verification.py::…`, called with an empty `related_bytes`
tuple) — independently confirmed via `grep`; since no related artifact
is ever supplied, CHGR-REQ-212's exact-match gate is never reached for
it, so no migration was needed or would have any effect.
`valid_record_confirmed.json`, `valid_record_awaiting_human_confirmation.json`,
and `invalid_missing_provenance_field.json` are referenced by no test in
`tests/*.py` at all (independently confirmed via repository-wide grep) —
orphaned fixtures predating 146L, out of this phase's and 146L's scope,
recorded as Informational finding I-2 below, not a defect either phase
introduced.

No fixture was found to have been modified merely to accommodate
incorrect implementation behavior — every changed byte in every changed
fixture is a digest field whose new value was independently recomputed
here and matches the corresponding sibling's real, unmodified content.

## 13. Error-Semantics Assessment

`_ERROR_CODES` (independently re-read, line 49–70) is a fixed
twelve-member `frozenset`; `_fail()` raises `VerificationError` (an
internal misuse exception, not a verification outcome) if ever called
with a code outside that set — this makes a silent collapse into an
undeclared/generic code structurally impossible, not merely untested.
No `INTERNAL_ERROR` or equivalent catch-all code exists anywhere in the
module. Every `except` block in the module (only one, around manifest/
registry loading, line 285) maps its three specific exception types to
`UNREGISTERED_SCHEMA` explicitly; no bare `except Exception` exists.
CLI exit codes (`governance_record.py` line 198): `0` iff
`isinstance(outcome, VerificationObservation)`, else `1` — independently
reproduced live (§8, duplicate-confirmation case, `exit=1`). JSON output
(`--json`) always includes `error_code` on rejection and the full
`checks` array; no raw artifact content beyond field values already
present in the caller-supplied artifacts is echoed. API
(`verify_artifact_at_path`) and CLI (`run_governance_record_verify`)
classifications agree by construction — the CLI is a thin, non-branching
wrapper calling the API and rendering its `to_dict()` verbatim (line
196–198), independently confirmed by reading the full function.

One minor overload noted, Informational (I-3, not a defect): `malformed`
candidates for all three roles, and self-tampered (invalid self-digest)
candidates, both classify as `DIGEST_MISMATCH` — the same code the
*primary* artifact's own self-consistency failure uses. This is
consistent with the module's documented nine-original-code minimalism
(146L's own commit message calls this out as a considered choice: it
"does not accurately name... a self-inconsistent/tampered artifact,
which DIGEST_MISMATCH already covers" for the three *new* codes, i.e.
146L deliberately left this overload in place rather than adding a
thirteenth code) and does not weaken fail-closed behavior — both cases
reject unconditionally.

## 14. Prior-Repair Regression Assessment

- **146H.1** (manifest-derived schema-version support): unaffected —
  `_shape_check` (lines 219–238), including its manifest-entry lookup
  and `unsupported_schema_version` rejection path, was not touched by
  146L's diff (§4) and is exercised unchanged by every scenario in §5–8.
- **146H.3** (confirmation/provenance/integrity preview-digest
  semantics): the semantic checks at lines 439, 515, 524, and 585 are
  byte-identical to their pre-146L form (confirmed via `git diff
  5485dcf0^ 5485dcf0 -- src/pcae/governance/verification.py`, semantic
  check blocks unchanged, only `_resolve_related`'s ambiguity/digest
  gates are new code inserted *before* these checks run). Six 146H.3
  unit tests required updating (via a `_rereferenced` helper, per 146L's
  commit message) purely because the new exact reference-digest gate
  now fires before those tests' own isolated semantic scenario is
  reached — not because the semantic checks themselves changed;
  independently confirmed all six still pass (§17).
- **Chapter 146 construction**: genuine bundles verify (§5–7, §15); no
  construction change was required or made (§4, §12); the provisional
  integrity reference remains compatible (§7, CHGR-REQ-215).
- **Existing protections** (schema validation, self-digest consistency,
  lifecycle-state checks, confirmation/provenance/integrity semantics,
  authority-boundary behavior): all independently re-exercised as a
  byproduct of §5–11's adversarial matrix and confirmed unweakened; the
  authority-boundary suite (`test_chgr_authority_boundary.py`) passed
  unchanged as part of §17's regression run.

## 15. Live End-to-End Scenario

Ran the full production workflow through the real, installed `pcae`
CLI, not the internal API, not a fixture:

```
pcae decision-session create   --template-ref tmpl-146lv --subject-ref subj-146lv --owner-id ivan
  -> session CDS-ace2df39-39e5-4ee1-8556-59fd527caacd, state Created
pcae decision-session evidence  --declare ev-146lv-1 --as-identity ivan
  -> state EvidenceReady
pcae decision-session select    --option-id opt-a --options-presented opt-a --options-presented opt-b
                                 --template-version 1.0 --as-identity ivan --rationale "146LV live e2e independent verification"
  -> state DecisionSelected
pcae decision-session preview   --as-identity ivan
  -> preview_digest f3e257ddc24195647a2e71279f92fab472e9ef7141a97fba028f2dd7daecbf4c
pcae decision-session confirm   --preview-digest f3e257dd... --statement "confirmed by ivan for 146LV" --as-identity ivan
  -> state Confirmed
pcae decision-session readiness --as-identity ivan
  -> package_id prp-13a537ee4a7548f6a177cdf739751214, disposition pending
pcae governance-record publish  prp-13a537ee4a7548f6a177cdf739751214 --operator-id ivan-op
  -> success, record_id chgr-5f40b474e81242b1aeed8a1c203c254e
```

All four artifacts persisted at
`.pcae/publication-execution/records/{chgr-5f40b474…,
chgrconf-61428ce7…, chgrprov-7ae90bcf…, chgrintg-1a0625ab…}.json`
(independently confirmed present via `find`, not asserted from the
publish command's own claimed `success`).

```
pcae governance-record verify <human_governance_record> \
    --related <confirmation> --related <provenance> --related <integrity>
  -> outcome: verified
     schema_shape passed / digest_self_consistency passed /
     lifecycle_structural_legality passed / confirmation_binding passed /
     assurance_truthfulness passed / provenance_consistency passed /
     integrity_consistency passed / template_resolution skipped

pcae governance-record inspect <human_governance_record>
  -> outcome: inspected, declared_record_digest 661236b4807f8c5d4268d5dec7101aad8ce4e508a7ce85034673bfd839a79ea1
     (asserts no authority; representation-only per its own disclosure line)
```

Exact siblings passed; a cross-bundle-forged confirmation (retargeted ID,
recomputed digest, from an unrelated separately-published bundle)
supplied against this same live artifact was rejected
`REFERENCE_DIGEST_MISMATCH` (§10.2); a duplicated genuine confirmation
was rejected `RELATED_ARTIFACT_AMBIGUOUS`; tampering the primary
record's `decision_subject` in place was rejected `DIGEST_MISMATCH`;
tampering the related confirmation's `confirmation_statement` in place
was rejected `DIGEST_MISMATCH`. Runtime was independently re-checked
after this scenario (§22) and remains `Observed`/`observe`/`unavailable`,
unchanged.

## 16. Adversarial Matrix

| Scenario | Required outcome | Observed outcome | Observed error code |
|---|---|---|---|
| Exact confirmation sibling | pass | PASS | — |
| Confirmation ID match, digest mismatch | reject | REJECT | `REFERENCE_DIGEST_MISMATCH` |
| Duplicate confirmation | reject | REJECT | `RELATED_ARTIFACT_AMBIGUOUS` |
| Cross-bundle forged confirmation | reject | REJECT | `REFERENCE_DIGEST_MISMATCH` |
| Exact provenance sibling | pass | PASS | — |
| Provenance ID match, digest mismatch | reject | REJECT | `REFERENCE_DIGEST_MISMATCH` |
| Duplicate provenance | reject | REJECT | `RELATED_ARTIFACT_AMBIGUOUS` |
| Cross-bundle forged provenance | reject | REJECT | `REFERENCE_DIGEST_MISMATCH` |
| Genuine directed integrity sibling | pass | PASS | — |
| Integrity wrong ID | pass (skipped, unresolved) / reject if resolved to wrong candidate | PASS (skipped; no candidate) | — |
| Integrity wrong payload digest | reject | REJECT | `DIGEST_MISMATCH` |
| Duplicate integrity | reject | REJECT | `RELATED_ARTIFACT_AMBIGUOUS` |
| Cross-bundle forged integrity | reject | REJECT | `DIGEST_MISMATCH` |
| Reordered related arguments | identical outcome | IDENTICAL (in-process shuffles + 3 fresh-process CLI orderings) | — |
| Missing required sibling | no verified result *for that check* (explicitly skipped; overall record can still verify if no rejection ground fires) | PASS, check `skipped` | — |
| Genuine provisional integrity reference | pass | PASS (structural property of every bundle this construction path produces, §7) | — |
| Primary record tampering | reject | REJECT | `DIGEST_MISMATCH` |
| Related artifact tampering | reject | REJECT | `DIGEST_MISMATCH` |

## 17. Regression Assessment

Focused suite (independently re-run, not trusted from 146L's report):

```
tests/test_chgr_verification.py
tests/test_chgr_authority_boundary.py
tests/test_chgr_phase_separation.py
tests/test_chgr_schema_family.py
tests/test_chgr_inspection.py
tests/test_chgr_143f_independent_verification.py
tests/test_phase_146g_chgr_schema_envelope_implementation.py
tests/test_phase_146h1_governance_verification_schema_version_repair.py
tests/test_phase_146h3_confirmation_binding_verification_repair.py
tests/test_phase_146l_chgr_cross_artifact_digest_binding_and_duplicate_match_verification_repair.py
-> 223 passed in 8.21s
```

`fast_green` sentinel:

```
python -m pytest -m fast_green -n auto -q
-> 4391 passed, 105 warnings in 104.42s
```

Identical to the count every 146-series phase from 146G onward has
independently cited as its own baseline — reproduced here fresh, not
copied from a prior report.

Broad keyword sweep (`-k "chgr or publication or governance or
verification"`, run without `-n auto` per the authorization's literal
command):

```
10 failed, 4038 passed, 4 skipped, 22791 deselected, 7 warnings in 442.51s
```

Independently classified each failure, not trusted from 146L's own
report:

- **9 failures** in `test_chgr_packaging.py`,
  `test_cltr_authority_136ah_publication.py`,
  `test_cltr_authority_136ai_publication_independent.py`,
  `test_cltr_cutover_136k_authority_core_independent_verification.py`,
  `test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py`
  — reproduced one directly (`test_143e_wheel_contains_all_six_chgr_record_schemas`)
  in isolation: `subprocess.CalledProcessError` from `python -m build
  --wheel` itself failing in this environment, unrelated to any Python
  logic in `verification.py`, `record.py`, or CHGR schemas — an
  environment/packaging-toolchain failure, not a code regression. Same
  9 test IDs Phase 146L's own report independently identified via a
  `git stash` baseline rerun; not re-verified against a pre-146L
  checkout here (redundant given the direct-reproduction evidence
  above conclusively locates the failure outside any file 146L or
  146LV touched).
- **1 failure**: `test_runtime_introspection_prototype.py::test_get_governance_returns_governance_info`
  — independently re-run in isolation: **passes** (`1 passed in 0.03s`).
  Test-ordering/shared-state interference from the broad sweep's ~22800
  collected tests, not a regression; unrelated to CHGR/verification
  logic (this test exercises `runtime` introspection, a different
  module entirely, never touched by 146L or this phase).

Both failure classes are independently confirmed pre-existing/
environment-caused, not attributable to Phase 146L's repair.

## 18. Findings

**NB-1 (Non-Blocking).** `_resolve_related`'s ambiguity gate groups
candidates by `record_id` alone, not the literal CHGR-REQ-213 text's
`record_id` **and** `record_family` conjunction. Every case this
broadens rejection to (different-family, same-ID candidates) still
rejects under both readings (§8); no acceptance-bypass or
order-dependence was demonstrated. Not exploitable given UUID4
`record_id` generation (`record.py` line 88). Recommend 146M or a future
phase either narrow §30.7's own CHGR-REQ-213 text to match the
(stricter, already-shipped) implementation, or file this as a tracked,
non-urgent implementation-vs-contract-text precision gap — either
resolution requires no runtime behavior change.

**NB-2 (Non-Blocking).** Malformed and self-tampered related-artifact
candidates for all three roles classify under the same `DIGEST_MISMATCH`
code the primary artifact's own self-consistency failure uses (§13).
Deliberate (per 146L's own commit message reasoning for why it did *not*
add a thirteenth code), fail-closed in every case, but reduces a
caller's ability to distinguish "the primary record was altered" from
"a supplied sibling was malformed" from machine-readable output alone.

**I-1 (Informational).** The "reference matches but semantic binding
fails" scenario (§20 in the authorization's Confirmation matrix, §6 in
Provenance) is not independently constructible for confirmation or
provenance: `record_digest` covers the full payload, so no mutation can
change semantic content while preserving the exact digest a genuine
sibling's reference expects. This does not weaken semantic verification
in practice (CHGR-REQ-212's gate already rejects every case that would
otherwise reach it) but means semantic checks (`confirmation_binding`'s
digest-equality assertion, `provenance_consistency`'s option/preview
checks) are currently unreachable-in-practice dead code paths for any
artifact that also satisfies exact reference-digest matching against a
*different* record than the one it is actually bound to. Worth a future
phase's disclosure note, not a defect.

**I-2 (Informational).** `valid_record_confirmed.json`,
`valid_record_awaiting_human_confirmation.json`, and
`invalid_missing_provenance_field.json` are referenced by no test in
`tests/*.py` (independently confirmed by repository-wide grep) — stale
fixtures predating both 146L and this phase, out of scope for either.

**I-3 (Informational).** See §13 — the `DIGEST_MISMATCH` code overload
between primary-record self-inconsistency and related-artifact
self-inconsistency/malformation, restated here for the findings index.

No finding meets any Blocking criterion in §19 of the authorization: no
independently demonstrated case rejected a valid genuine bundle,
accepted a substituted or cross-bundle-forged confirmation/provenance/
integrity artifact, permitted order-dependent or duplicate-derived
success, permitted a verified result with a missing *required* sibling
silently treated as passed, treated `integrity_ref.record_digest` as
final, rejected a genuine provisional-integrity bundle, or weakened any
prior schema/self-digest/confirmation/provenance/integrity protection.

## 19. No-Go Confirmation

This phase modified no production code, verification code, contract,
schema, manifest, construction code, Publication Coordinator code, or
fixture. `git status --short` before and after this phase's work is
identical apart from this report and governance bookkeeping files (task
contract, `PROJECT_STATUS.md`, `CHANGELOG.md`, `.pcae/phase-completion-*`).
The one adversarial test script used for §5–11 was written and executed
from the session scratchpad
(`/private/tmp/.../scratchpad/verify_146lv.py`), never copied into
`tests/`, and is not part of this commit. No `<phrase>` was implemented
that this authorization forbade; no `<phrase>` occurred that constitutes
a repair of any finding in §18.

## 20. Overall Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS.**

Independently proven: exact confirmation-reference enforcement (§5),
exact provenance-reference enforcement (§6), directed integrity binding
preserved with CHGR-REQ-210's non-enforcement intact (§7), duplicate
matches fail closed for all three roles (§8), argument order cannot
change results across six in-process shuffles and three fresh-process
CLI orderings (§9), cross-bundle impersonation is rejected both
in-memory and against a live CLI-published production bundle (§10),
genuine existing bundles remain valid including the structurally
universal provisional-integrity-reference case (§7, §15), and every
prior verification protection (146H.1, 146H.3, schema/self-digest/
lifecycle/authority-boundary) remains intact under regression (§14,
§17).

## 21. Recommended Next Phase

**146M — CHGR-001 Schema-Envelope Operational Readiness Reassessment**,
repeating the operational-readiness assessment Phase 146I originally
failed, specifically re-verifying closure of: duplicate-match ambiguity,
confirmation/provenance digest-reference bypass, integrity
directed-binding behavior, and end-to-end publication/auditability —
now against a repository state this phase has independently confirmed
satisfies CHGR-REQ-210–216.

This recommendation is not authorization.
