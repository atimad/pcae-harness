# Phase 146H.1 — Governance Verification Schema-Version Support Repair

**Status:** Complete (targeted implementation repair; no contract or
schema file modified)
**Mode:** Targeted Implementation Repair
**Predecessor:** Phase 146H (Independent Implementation Verification;
verdict NOT VERIFIED, one independently demonstrated Blocking defect)
**Runtime:** Observed / observe / unavailable (unchanged; reconfirmed
below).
**Pushed:** pushed (this phase's own commits pushed to `origin/main`).

---

## 1. Bootstrap

- `git status --short`: one untracked file at start (146H's own report,
  `docs/PHASE_146H_...md`), otherwise clean.
- `git branch --show-current`: `main`.
- `git rev-list --count origin/main..HEAD` / `HEAD..origin/main`: `0` / `0`.
- `pcae session bootstrap --agent-id claude-local`: lock held; readiness
  initially `blocked` because the untracked 146H report file fell outside
  the (post-146G idle) active task's scope — resolved by
  `pcae task transition` before any implementation file was touched.
- `pcae check` / `pcae health` / `pcae doctor task-memory`: healthy, clean,
  no inconsistencies once the task was transitioned.
- `pcae runtime inspect`: `Runtime state: Observed`, `Execution
  capability: unavailable`, `Maximum plugin capability: observe` —
  identical at phase start and close (§8 below).
- `pcae push check`: working tree changed but nothing to push (no
  unpushed commits).

`PROJECT_STATUS.md` treated as authoritative over `tasks/TODO.md`, per
this chapter's established precedent.

---

## 2. Independent Root-Cause Confirmation

Per this phase's own instruction, 146H's diagnosis was not assumed
complete — it was independently re-derived from first principles before
any code was touched.

**Mechanically isolated the cause with five separate probes** (a live,
production-constructed `human_governance_record`, its family's manifest
entry, and `governance/verification.py`'s internal functions, exercised
directly):

1. **Manifest lookup**: `_shape_check`'s manifest-entry search for the
   `human_governance_record` family found exactly one entry, and its
   `schema_id` matched the artifact's own — confirmed correct.
2. **Schema registry / raw JSON-Schema validation**: calling
   `schema_runtime.validate_record_shape` directly (bypassing
   `_shape_check` entirely) on the same artifact returned
   `OutcomeStatus.VALID` — confirmed the registry and schema files
   already accept `schema_version: "1.1"` without issue.
3. **The actual failing check**: `_shape_check` itself returned
   `(False, "unsupported_schema_version")` on the unmodified artifact.
4. **Isolation of the exact line**: a copy of the same artifact with only
   `schema_version` force-set to `"1.0"` (nothing else changed) passed
   `_shape_check` cleanly — proving the rejection depends on nothing but
   that one field's value against the stale constant.
5. **Sibling-family control**: the three sibling artifacts (whose
   manifest-declared `schema_version` remains `"1.0"`, untouched by Phase
   146D) passed `_shape_check` without modification — confirming the
   defect is specific to the stale comparison, not a registry-wide or
   dispatch-wide problem.

**Ruled out, independently, as causes**: incorrect manifest lookup (probe
1), schema registry behavior (probe 2), version negotiation (there is
none — a blunt equality check, probe 4), CLI dispatch (the failure occurs
in the business-logic layer `_shape_check`, before any CLI formatting is
reached). **Confirmed sole cause**: `governance/verification.py`'s
module-level `SUPPORTED_SCHEMA_VERSION = "1.0"` constant, compared by
equality against every record's `schema_version` field regardless of
record family, left stale when Phase 146D's additive schema amendment
(CHGR-REQ-207) bumped `human_governance_record.schema.json`'s own
`schema_version` to `"1.1"` in `manifest.json` without any corresponding
update to this separate, independent consumer module (`git log` confirms
`verification.py` was last touched in Phase 143E, before 146D existed).

This reconfirms 146H's diagnosis exactly, now with mechanical, per-cause
isolation rather than a single before/after observation.

---

## 3. Repair Strategy

Per this phase's own guidance, evaluated deriving supported schema
versions from an authoritative source rather than any hardcoded
duplicate:

- **CHGR manifest** (`src/pcae/schema_resources/chgr/manifest.json`) —
  already the single authoritative source `_shape_check` uses for
  `schema_id` on the line immediately above the defective check, and the
  exact source `chgr_envelope.envelope_for` (the construction side) reads
  `schema_version` from per CHGR-REQ-194. **Selected.**
- **Schema metadata / schema runtime registry** — the registry validates
  shape, not the artifact's self-declared `schema_version` value; no
  registry API exposes "the current supported version per family"
  independent of the manifest, which is itself the registry's own input.
  Not a distinct source from the manifest option above.
- **Another mechanism** — none exists; introducing one (e.g. a second,
  new constant or lookup table) would itself duplicate a version literal,
  which this phase's guidance explicitly warns against.

**Chosen repair**: replace the equality check's stale constant with a
lookup already computed one line above it — `entries[0].get("schema_version")`,
the same manifest entry already matched against `schema_id`. No new
lookup, no new duplicated constant, no caching change, no new dependency.

---

## 4. Implementation

`src/pcae/governance/verification.py`, four lines changed:

```diff
 CONSUMER_ID = "pcae-governance-record-verify-v1"
 CHGR_CONTRACT_VERSION = "CHGR-001/1.0"
-SUPPORTED_SCHEMA_VERSION = "1.0"
 _MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/chgr/manifest.schema.json"
 _UNAVAILABLE = "unavailable"
@@
     schema_id = record.get("schema_id")
     if schema_id != entries[0].get("schema_id"):
         return False, "family_identity_mismatch"
-    if record.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
+    if record.get("schema_version") != entries[0].get("schema_version"):
         return False, "unsupported_schema_version"
@@
 __all__ = [
     "CONSUMER_ID",
     "CHGR_CONTRACT_VERSION",
-    "SUPPORTED_SCHEMA_VERSION",
     "CheckResult",
```

The now-provably-stale `SUPPORTED_SCHEMA_VERSION` constant is removed
entirely, not merely left unused: independently confirmed (`grep`) that
no other module or test imports or references it, and leaving a
demonstrably-incorrect, disconnected constant in place would only invite
the same class of defect to recur on a future schema-version bump. This
is the minimum change that eliminates the demonstrated defect: one
constant removed, one comparison retargeted at an already-fetched,
already-authoritative value, two `__all__`/declaration lines removed to
match.

### 4.1 Fixture-data consequence (test-only, not production code)

Fixing the comparison to be *correct* (not merely permissive) meant it
now, correctly, also rejects the *reverse* case: a `human_governance_record`
still declaring the stale `"1.0"` value the manifest no longer carries for
that family. Nineteen pre-existing, hand-authored test fixtures under
`tests/fixtures/chgr/` (`valid_record_*.json` ×8,
`adversarial_*`/`invalid_*` variants) were originally authored at Phase
143E, before Phase 146D's schema amendment existed, and still declared
the now-superseded `"1.0"` value with `authority_basis_claimed` present
(schema-valid under either version, since 146D only *loosened* that
field's requiredness). Each was updated:

- **schema_version bumped `"1.0"` → `"1.1"`** on every
  `human_governance_record`-family fixture (the intentionally-wrong
  `adversarial_unsupported_schema_version.json`, pinned at `"9.9"`, was
  left untouched — it exists specifically to test genuine version
  rejection, which must and does continue to work identically).
- **`record_digest` recomputed** only for fixtures whose stored digest
  was already self-consistent before this change (confirmed individually
  per file: `_record_digest_of(doc) == doc["record_digest"]` beforehand) —
  for these, the bump is metadata-only and digest self-consistency must
  be preserved to keep reaching whatever later check (assurance
  overclaim, template mismatch, lifecycle round-trip, the full positive
  chain) is each fixture's actual point.
- **`record_digest` deliberately left untouched** for fixtures whose
  stored digest was already, intentionally, *inconsistent* with their own
  content before this change (confirmed individually: `_record_digest_of(doc)
  != doc["record_digest"]` beforehand) — that mismatch *is* the
  fixture's adversarial content (e.g. `adversarial_record_substitution.json`).
  Recomputing it would have silently "healed" the tamper and defeated the
  test.
- The one fixture (`valid_record_published.json`) exercised together with
  real sibling artifacts in the "full positive chain" test required
  propagating its new post-bump "confirmable content digest"
  (`_confirmable_content_digest_of`, a digest over the record's
  substantive fields only) into the three sibling fixtures that cite it
  by digest (`valid_confirmation_evidence.json`'s `confirmed_content_digest`,
  `valid_provenance.json`'s `preview_content_digest`,
  `valid_integrity.json`'s `payload_digest`), and likewise into
  `adversarial_assurance_overclaim_selfconsistent_confirmation.json`
  (the one other fixture that cites a bumped primary record's confirmable
  digest) — each such sibling's own `record_digest` was then recomputed
  to remain self-consistent.

No fixture's *substantive* content (decision subject, template,
selection, evidence, assurance level, lifecycle state, tamper markers)
was altered — only the `schema_version` metadata field and the digests
mechanically dependent on it.

---

## 5. Architectural Justification

The repair makes the `schema_version` check structurally identical in
form to the `schema_id` check immediately preceding it in the same
function — both now read from `entries[0]`, the single manifest entry
already fetched for the record's family. This is not a new pattern
introduced by this repair; it is the *existing* pattern in the same
function, applied consistently to a field that had drifted from it. It
also achieves parity with the construction side: `chgr_envelope.envelope_for`
(the code that assigns `schema_version` when a record is built) already
reads it verbatim from this exact manifest entry per CHGR-REQ-194 — the
verification side now checks against the same source the construction
side writes from, closing the gap that let the two silently diverge
after Phase 146D's amendment. Because the manifest is re-read on every
`verify_artifact_at_path` call (no caching in this module, unchanged by
this repair), any future, similarly-additive schema-version bump for any
CHGR record family will be picked up automatically, without requiring a
parallel edit to this file — eliminating this defect's entire recurrence
class, not just today's instance of it.

---

## 6. Test Results

### 6.1 New tests (`tests/test_phase_146h1_governance_verification_schema_version_repair.py`, 11 tests, all passing)

- **Unit**: the stale constant is gone (`hasattr`/`__all__` checks); the
  current manifest `schema_version` for `human_governance_record`
  verifies standalone (the exact 146H-demonstrated scenario); sibling
  families' unaffected `"1.0"` value still verifies; three distinct
  genuinely-unsupported versions (`"2.0"`, `"0.9"`, `"1.2"`) are still
  refused; a malformed version string is still refused; the *stale*
  `"1.0"` value on the current `human_governance_record` family is now
  correctly refused too (proving the fix is a correct equality check,
  not a blanket widening); the preceding `schema_id`/manifest-lookup
  checks are unaffected by a genuinely wrong `schema_id`.
- **Integration**: a full, real `build_publication_record`-constructed
  bundle — every one of the four artifacts verifies standalone; tampered
  content is still refused as `DIGEST_MISMATCH` (fail-closed preserved).

### 6.2 Regression suites

- `tests/test_chgr_verification.py`, `test_chgr_authority_boundary.py`,
  `test_chgr_phase_separation.py`, `test_chgr_143f_independent_verification.py`
  — **60/60 passed** (19 pre-existing failures caused by this repair's
  fixture-staleness fallout, §4.1, all resolved; zero remaining
  failures).
- `tests/test_chgr_inspection.py`, `test_chgr_schema_family.py` (glob
  over the same fixture directory) — **66/66 passed**, unaffected.
- `tests/test_phase_146h1_governance_verification_schema_version_repair.py`,
  `test_phase_146g_chgr_schema_envelope_implementation.py`,
  `test_phase_144c_publication_coordinator.py` — **194/194 passed**
  (combined run).
- `fast_green` gate — **4391/4391 passed**, identical count to 146G's and
  146H's own independently-confirmed baseline.
- Broad sweep (`-k "chgr or publication or interactive_workflow or
  governance"`) — **1527 passed, 1 skipped, 2 failed**. The 2 failures
  are the same pre-existing packaging tests
  (`test_cltr_authority_136ah_publication.py::test_136ah_wheel_contains_publication_module_no_later_family`,
  `test_cltr_authority_136ai_publication_independent.py::TestPackaging::test_wheel_contains_publication_module_and_both_schemas_no_later_family`)
  Phase 146H already independently traced to `src/pcae/cltr/authority/**`
  (last touched by Phases 136AT/136AR, structurally unrelated to CHGR) and
  confirmed reproduce identically on a pre-Chapter-146 baseline commit —
  reconfirmed here as still the only, still pre-existing, still unrelated
  failures.

---

## 7. Regression Assessment

No regression found in Publication Coordinator, the publication pipeline,
CHGR construction, schema validation, manifest validation, or governance
verification beyond the expected, now-resolved fixture-staleness fallout
of correctly fixing the check (§4.1/§6.2). Interactive Workflow,
lifecycle sequencing, and authority boundaries are untouched by this
repair (no file under `interactive_workflow/**`, `lifecycle.py`, or any
authority-ownership module was modified) and their regression coverage
(fast_green, the broad sweep) is unaffected.

---

## 8. Governance Validation

- `pcae check`: passed (after widening the task contract's allowed-file
  patterns to cover the files this authorized repair actually touches —
  `src/pcae/governance/verification.py`, `tests/fixtures/chgr/**`, the
  new test file, and this document — no file outside that declared,
  narrow scope was changed).
- `pcae health`: healthy.
- `pcae doctor task-memory`: clean, no inconsistencies.
- `pcae runtime inspect`: `Runtime state: Observed`, `Execution
  capability: unavailable`, `Maximum plugin capability: observe`,
  `Registry status: empty`, `Plugin count: 0` — identical to phase start.
  Runtime unchanged.
- `pcae push check`: working tree changed, 0 unpushed commits, nothing to
  push.

No policy change. No `.pcae/policy.toml` edit. No strategic-lineage
modification. No contract or schema file touched (`git diff --stat` under
`docs/contracts/**` and `src/pcae/schema_resources/**` is empty).

---

## 9. Findings

1. **Repaired (this phase's authorized scope)** — the stale
   `SUPPORTED_SCHEMA_VERSION` hardcoded constant in
   `governance/verification.py`, independently confirmed as the sole
   cause of 146H's demonstrated Blocking defect. Fixed by comparing
   against the manifest's own per-family `schema_version` value already
   fetched one line above, with the stale constant removed rather than
   left dormant.
2. **Resolved as a direct, in-scope consequence** — 19 pre-existing test
   fixtures carrying the now-superseded `schema_version: "1.0"` literal
   for the `human_governance_record` family were updated (metadata and
   dependent digests only, no substantive content change), restoring 19
   previously-passing tests this repair's own correctness required to
   keep passing.
3. **Blocking, independently discovered, out of this phase's authorized
   scope — new finding, not repaired.** While independently confirming
   146H's diagnosis in full generality (testing the repaired check with
   real sibling artifacts supplied, not only standalone — the
   configuration 146H itself never reached), a **second, structurally
   separate** defect was found: `governance/verification.py`'s
   `confirmation_binding` check compares
   `human_confirmation_evidence.confirmed_content_digest` against
   `_confirmable_content_digest_of(record)` — a digest computed over the
   `human_governance_record`'s own stripped JSON fields. This matches the
   *original*, Phase-143E-era design intent (independently confirmed:
   every hand-authored fixture's `confirmed_content_digest` was
   originally computed exactly this way). However, CHGR-REQ-201 (Phase
   146B) instead specifies — and the current production implementation
   (`record.py`, Phase 146G) correctly follows — populating
   `confirmed_content_digest` **verbatim from
   `PublicationReadinessPackage.preview_digest`**, a digest computed
   upstream, in `interactive_workflow`, over the *rendered preview text*
   shown to the human before Confirmation — a structurally different
   digest, over structurally different bytes, that cannot coincidentally
   equal `_confirmable_content_digest_of`'s output. Live-reproduced: a
   real, fully schema-valid, correctly-146G-constructed four-artifact
   bundle, verified together with its own real siblings (not standalone),
   is rejected with `CONFIRMATION_UNBOUND` — "the confirmation evidence's
   confirmed_content_digest does not match this record's recomputed
   confirmable content" — even though nothing was tampered and the bundle
   fully conforms to CHGR-REQ-194–209. This is unrelated to, and not
   caused by, the schema_version repair (reproduces identically whether
   or not this phase's fix is applied, once cross-artifact verification
   is actually exercised) and was never disclosed by 146B, 146D, 146E,
   146F, 146G, or 146H (146H's own reproduction never supplied related
   artifacts, so it never reached this check). **Not repaired here**:
   this phase's Human Authorization and No-Go Boundary scope it tightly
   to "the independently demonstrated Blocking defect" named in 146H
   (the schema_version one) and explicitly forbid redesigning the
   verification subsystem or modifying any contract; a correct fix here
   plausibly requires reconciling CHGR-REQ-201's own construction rule
   with the schema's documented field semantics — a contract-adjacent
   question squarely outside this phase's authorization. Documented
   explicitly per this phase's own No-Go Boundary instruction, exactly as
   146H documented its own finding rather than silently repairing it.

---

## 10. Overall Verdict

**REPAIR COMPLETE** (for this phase's authorized, tightly-scoped
objective).

The independently demonstrated Blocking defect named in this phase's
Human Authorization — `governance/verification.py`'s stale
`SUPPORTED_SCHEMA_VERSION` hardcoded constant rejecting every
`human_governance_record` the current production implementation
constructs — is eliminated, root-caused independently (not merely
re-confirmed from 146H's report), repaired with the minimum change
identified as sufficient (four lines, no new duplicated constant, derived
from the same authoritative manifest source the construction side already
uses), and verified correct in both directions (accepts the current
version, still refuses genuinely unsupported, malformed, and now-stale
versions alike) without weakening any fail-closed guarantee. All
regression suites this phase was instructed to run are green, including
`fast_green` at an identical 4391/4391 count and a broad cross-file sweep
whose only 2 failures are the same pre-existing, structurally unrelated
packaging tests 146H already traced to a pre-Chapter-146 baseline.

This verdict covers the schema_version defect only. §9 Finding 3 disclosed
a second, independently discovered, out-of-scope Blocking defect
(`CONFIRMATION_UNBOUND` on full cross-artifact verification) that this
phase was not authorized to repair. A production `human_governance_record`
now verifies successfully **standalone** (the exact scenario 146H
demonstrated and this phase was authorized to fix); it does **not** yet
verify successfully when cross-checked against its own real sibling
artifacts, for the separate reason documented in §9.3. Full,
unconditional "a valid CHGR verifies successfully" (this phase's
objective §4, read at maximum generality) is therefore not yet achieved —
only the specific, named, authorized defect is.

---

## 11. No-Go Boundary

This phase did not: modify any CHGR contract or schema file; redesign the
verification subsystem (the fix keeps the exact same check structure,
retargeting one comparison's right-hand side); redesign the Publication
Coordinator; alter lifecycle sequencing; introduce execution capability;
change authority ownership; or broaden acceptance beyond the single,
manifest-declared, per-family version already used one line above the
fix. The newly-discovered §9.3 finding was documented, not repaired,
consistent with this instruction.

---

## 12. Recommended Next Phase

**146H.1V — Governance Verification Schema-Version Support Repair
Independent Verification**, mirroring this chapter's established
implement-then-independently-verify discipline, to independently confirm
this repair without trusting this document's own claims. Separately, and
independently of 146H.1V's own scope, §9 Finding 3 (`CONFIRMATION_UNBOUND`
on real cross-artifact verification) requires its own, distinctly
authorized phase — it is a different defect, in a different part of the
same module, requiring a decision this phase's own authorization
explicitly does not extend to. This recommendation is not an
authorization.
