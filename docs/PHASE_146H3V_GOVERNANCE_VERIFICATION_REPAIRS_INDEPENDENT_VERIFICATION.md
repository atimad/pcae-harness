# Phase 146H.3V — Governance Verification Repairs Independent Verification

**Status:** Complete (independent verification only; no production code,
schema, contract, or fixture file modified by this phase's own work)
**Mode:** Independent Verification (combined 146H.1 + 146H.3 repair state)
**Predecessor:** Phase 146H.3 (Confirmation Binding Verification Repair;
verdict REPAIR COMPLETE)

---

## 1. Executive Summary

This phase independently re-derived, re-constructed, and adversarially
re-tested both `governance/verification.py` repairs made in this chapter —
146H.1 (schema-version support) and 146H.3 (confirmation-binding,
provenance, and integrity comparisons) — without trusting either repair
report's own claims. A genuine, unmodified, `build_publication_record`
(Phase 146G production function) four-artifact bundle was constructed
fresh in this phase (not reused from any prior phase's saved evidence, not
hand-authored) and verified successfully end-to-end through both the
internal `verify_artifact_at_path` API and the real `pcae
governance-record verify --related ... --related ... --related ...` CLI,
with every applicable cross-artifact check (`confirmation_binding`,
`provenance_consistency`, `integrity_consistency`) reporting `passed`, not
skipped. An adversarial matrix of over twenty mutation scenarios across
schema-version, confirmation-binding, provenance, integrity, and bundle
composition axes confirmed fail-closed behavior throughout, with one
Non-Blocking finding (order-dependent duplicate-sibling resolution) and
one Informational finding (a second, dead, harmless
`SUPPORTED_SCHEMA_VERSION` constant in the sibling `inspection.py` module).
The full regression sweep is reported in §12.

**Overall Verdict: VERIFIED WITH NON-BLOCKING FINDINGS.**

---

## 2. Independent Contract Reconstruction

Read directly, not through any 146H-series report's own summary:
`src/pcae/governance/verification.py` (509 lines, in full),
`src/pcae/governance/publication/record.py` (`build_publication_record`,
`compute_record_digest`, in full),
`src/pcae/governance/publication/coordinator.py` (`PublicationCoordinator.execute`,
in full), `src/pcae/interactive_workflow/application/publication_service.py`
(header/delegation chain), `src/pcae/commands/governance_record.py`
(`run_governance_record_verify`, the CLI's `--related`/`--json` flags),
`src/pcae/schema_resources/chgr/manifest.json`, and the four
`records/*.schema.json` files' `additionalProperties` declarations.

**Confirmed architecture, independently, before reading any prior 146H
document's claims about it:**

- Construction path: `PublicationApplicationService` →
  `PublicationCoordinator.execute` → `build_publication_record`
  (`record.py:130-268`) → four artifacts written via
  `PublicationRecordStore.write_record` inside `coordinator.py:148-157`,
  strictly after `build_publication_record`'s own internal fail-closed
  gate (`_validate_chgr_bundle`) succeeds.
- Field provenance (`record.py:171,172,196,271`, confirmed by direct line
  read):
  - `human_confirmation_evidence.confirmed_content_digest` =
    `package.preview_digest` (verbatim).
  - `human_confirmation_evidence.preview_rendering_digest` =
    `package.preview_digest` (verbatim, same value).
  - `governance_record_provenance.preview_content_digest` =
    `package.preview_digest` (verbatim, same value).
  - `governance_record_integrity.payload_digest` = `body3["record_digest"]`,
    i.e. the finalized `human_governance_record`'s own real,
    final `record_digest` (line 271: `"payload_digest": body3["record_digest"]`).
- `verification.py`'s current checks (confirmed by direct read,
  lines 357-462):
  - `confirmation_binding` (line 371): compares
    `confirmation.get("confirmed_content_digest")` against
    `confirmation.get("preview_rendering_digest")` — both fields on the
    *same* confirmation-evidence artifact.
  - `provenance_consistency` (line 423): compares
    `provenance.get("preview_content_digest")` against
    `confirmation.get("confirmed_content_digest")` — cross-artifact, only
    when a confirmation sibling was also supplied.
  - `integrity_consistency` (line 452): compares
    `integrity.get("payload_digest")` against `declared_digest`
    (`record.get("record_digest")`, the primary artifact's own digest,
    already independently recomputed and verified two lines earlier by
    `digest_self_consistency`).
- No hardcoded `SUPPORTED_SCHEMA_VERSION` constant remains in
  `verification.py` (confirmed by `grep -n "SUPPORTED_SCHEMA_VERSION"
  src/pcae/governance/verification.py` → zero matches). `_shape_check`
  (line 210-229) instead compares `record.get("schema_version")` against
  `entries[0].get("schema_version")`, the single manifest entry already
  matched one line above by `schema_id` — the same manifest
  (`src/pcae/schema_resources/chgr/manifest.json`) that declares
  `human_governance_record` at `schema_version: "1.1"` and its three
  siblings at `"1.0"`.
- No `_confirmable_content_digest_of` function or call site remains
  anywhere in `src/` (confirmed: `grep -rn
  "_confirmable_content_digest_of" src/ tests/` → matches only in test
  docstrings/assertions that it is *absent*, never a live definition or
  call).

This reconstruction, derived from the code itself, matches what both
146H.1 and 146H.3 claim to have implemented — confirmed independently,
not by trusting either report's prose.

---

## 3. Combined Repair Verification

Both repairs were exercised together, as 146H.3's own Recommended Next
Phase instructed, since a single production bundle now depends on both
holding simultaneously (schema-version acceptance for the top-level
record, and confirmation/provenance/integrity binding for the siblings).

Constructed one fresh four-artifact bundle directly with
`pcae.governance.publication.record.build_publication_record` (the real,
unmodified Phase 146G production function — not a fixture, not a saved
artifact from any prior phase) using a `PublicationReadinessPackage` with
`preview_digest = "d" * 64`, `package_id = "pkg-146h3v"`,
`record_id = "chgr-146h3v-0001"`. Verified via both the internal API and
the CLI (§4). All checks passed; no check that should have run was
skipped. See §5-§8 for the per-check breakdown and §11 for the full
adversarial matrix exercising both repairs' fail-closed boundaries
together and independently.

---

## 4. Production-Bundle Reproduction

Live reproduction, executed in this phase, using scratch files outside the
repository tree (`/private/tmp/.../scratchpad/chgr_repro/*.json`, deleted
at phase close, §14):

```python
from pcae.governance.publication.record import build_publication_record
from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
# ... PublicationReadinessPackage(package_id="pkg-146h3v", preview_digest="d"*64, ...)
bundle = build_publication_record(package, event, "chgr-146h3v-0001", _TS)
```

This produced a genuinely schema-valid, `build_publication_record`-
constructed four-artifact bundle (`human_governance_record`,
`human_confirmation_evidence`, `governance_record_provenance`,
`governance_record_integrity`), written to disk as four JSON files.

**Verified via the production API:**

```
verify_artifact_at_path(Path(hgr_path), artifact_bytes=..., related_bytes=(conf, prov, integ))
→ VerificationObservation(outcome="verified", ...)
```

**Verified via the real CLI** (`pcae governance-record verify --help`
confirmed the actual flag: `--related PATH` — "May be supplied multiple
times"):

```
$ .venv/bin/pcae governance-record verify chgr_repro/human_governance_record.json \
    --related chgr_repro/human_confirmation_evidence.json \
    --related chgr_repro/governance_record_provenance.json \
    --related chgr_repro/governance_record_integrity.json --json
exit=0
```

Output (`outcome: "verified"`), checks:

| Check | Status |
|---|---|
| `schema_shape` | passed |
| `digest_self_consistency` | passed |
| `lifecycle_structural_legality` | passed |
| `confirmation_binding` | passed |
| `assurance_truthfulness` | passed |
| `provenance_consistency` | passed |
| `integrity_consistency` | passed |
| `template_resolution` | skipped — "no matching related template supplied" (correct: no template was supplied, this phase's package carries no `decision_template` sibling by design) |

No cross-artifact check that had a matching related artifact supplied was
skipped. Reordering the three `--related` arguments (integrity, then
confirmation, then provenance, in place of the original order) produced
an identical result (`exit=0`, all checks unchanged) — confirming order
does not matter for the normal, non-conflicting case (§11 identifies the
one adversarial exception: duplicate conflicting siblings sharing the
same `record_id`).

---

## 5. Schema-Version Verification

Independently re-derived and adversarially tested `_shape_check`'s
version-comparison line (`verification.py:224`) directly against the live
bundle's `human_governance_record` (whose real, manifest-sourced
`schema_version` is `"1.1"`):

| Scenario | Result |
|---|---|
| Current version (`"1.1"`, unmodified) | **Passed** (baseline, §4) |
| Stale version (`"1.0"`, forced) | **Rejected**, `SCHEMA_INVALID` ("unsupported_schema_version") |
| Future/unknown version (`"9.9"`, forced) | **Rejected**, `SCHEMA_INVALID` |
| Malformed version string (`"not-a-version"`, forced) | **Rejected**, `SCHEMA_INVALID` |
| Schema-family mismatch (record's `schema_id` swapped to `governance_record_provenance`'s schema_id, `schema_version` left at `"1.1"`) | **Rejected**, `UNREGISTERED_SCHEMA` (`family_identity_mismatch`) |

Each mutation was applied to a *copy* of the live-constructed record, with
`record_digest` recomputed via `compute_record_digest` to isolate the
version check specifically (so failures are attributable to the version
check, not incidentally to `digest_self_consistency`). All four adverse
cases were rejected; only the genuine, current, manifest-declared version
passed. This exactly reconfirms 146H.1's own claimed test matrix
(`"2.0"`, `"0.9"`, `"1.2"` in its own test file; `"1.0"`, `"9.9"`,
`"not-a-version"` exercised independently here) without depending on
146H.1's own saved fixtures.

**No hardcoded duplicate authority found.** `entries[0].get("schema_version")`
is the manifest entry already fetched one line above for the `schema_id`
match — the identical authoritative source `chgr_envelope.envelope_for`
reads from at construction time (CHGR-REQ-194), confirmed by direct
comparison of `chgr_envelope.py`'s `envelope_for` against
`verification.py`'s `_shape_check`. Construction and verification agree.

---

## 6. Confirmation-Binding Verification

Independently confirmed the repaired `confirmation_binding` check
(`verification.py:371`) compares two fields on the *same*
`human_confirmation_evidence` artifact
(`confirmed_content_digest` vs. `preview_rendering_digest`), not any
digest recomputed over the `human_governance_record`'s own content:

| Scenario | Result |
|---|---|
| Genuine bundle (both fields verbatim-equal to `package.preview_digest`) | **Passed** |
| `confirmed_content_digest` mismatched (forced to `"e"*64`) | **Rejected**, `CONFIRMATION_UNBOUND` |
| `preview_rendering_digest` mismatched (mirror case) | **Rejected**, `CONFIRMATION_UNBOUND` |
| `confirmed_content_digest` malformed (`"not-a-digest"`) | **Rejected**, `DIGEST_MISMATCH` (caught earlier, by the confirmation sibling's own `digest_self_consistency`/shape check before `confirmation_binding` is reached) |
| Confirmation sibling not supplied | `confirmation_binding` reported **`skipped`** ("no matching related confirmation evidence supplied"), overall outcome still `verified` for the checks that *were* performed — never silently reported as a full pass beyond what was actually checked |
| The obsolete 143E-era formula reconstructed exactly (a digest over the record's own stripped content, set as `confirmed_content_digest`) and compared against the genuine `preview_rendering_digest` | **Rejected**, `CONFIRMATION_UNBOUND` — proving no code path lets the removed formula coincidentally satisfy the new check |

Directly confirmed `_confirmable_content_digest_of` is fully absent
(`grep -rn "_confirmable_content_digest_of" src/` returns nothing).

---

## 7. Provenance Verification

`provenance_consistency` (`verification.py:414,423`) checks two things:
`selected_option_id` agreement between provenance and the primary record,
and (only when a confirmation sibling is also supplied)
`provenance.preview_content_digest` against
`confirmation.confirmed_content_digest`:

| Scenario | Result |
|---|---|
| Genuine bundle | **Passed** |
| `preview_content_digest` mismatched (forced to `"f"*64`) | **Rejected**, `PROVENANCE_INCOMPLETE` |
| Provenance sibling substituted with a wrong-type sibling (the integrity artifact, passed where provenance was expected) | `provenance_consistency` reported **`skipped`** — `_find_related` matches strictly on `record_type == "governance_record_provenance"` and the cited `record_id`; a wrong-type sibling never satisfies that match, so it is correctly treated as "not supplied," never accepted as a substitute. Confirmed intentional, not a defect (§11). |
| Provenance sibling not supplied | **`skipped`** |
| A structurally valid provenance artifact from an entirely different, independently-constructed bundle (different `record_id`, unrelated content) supplied in place of the real provenance sibling | **`skipped`** — the cited `provenance_ref.record_id` does not match the substituted sibling's own `record_id`, so `_find_related` correctly reports no match rather than silently accepting an unrelated artifact |

---

## 8. Integrity Verification

`integrity_consistency` (`verification.py:452`) compares
`integrity.payload_digest` against `declared_digest`
(`record.get("record_digest")`) — the same value `digest_self_consistency`
already independently recomputed and verified against the record's own
content two checks earlier, not a new formula:

| Scenario | Result |
|---|---|
| Genuine bundle | **Passed** |
| `payload_digest` mismatched (forced to `"1"*64`) | **Rejected**, `DIGEST_MISMATCH` |
| Primary `human_governance_record` content tampered after digest computed (`decision_subject` altered, `record_digest` left unchanged) | **Rejected**, `DIGEST_MISMATCH` — caught by the pre-existing, unmodified `digest_self_consistency` check at the top of the function, before `integrity_consistency` is even reached, confirming tamper detection on the primary record was not weakened by this repair |
| Integrity sibling not supplied | **`skipped`** |

---

## 9. Schema and Manifest Assessment

- All six `records/*.schema.json` files (`decision_template`,
  `human_governance_record`, `human_confirmation_evidence`,
  `governance_record_provenance`, `governance_record_integrity`,
  `governance_record_lifecycle_event`) independently confirmed to declare
  `"additionalProperties": false` (direct `python3 -c "json.load(...)"`
  inspection of all six files).
- `human_confirmation_evidence.schema.json`'s `confirmed_content_digest`
  field `description` (line 44) independently confirmed to read the
  146H.3-corrected text — no longer asserting the obsolete "matches the
  record's own recomputed content digest" claim; now correctly states
  propagation from `PublicationReadinessPackage.preview_digest`
  (CHGR-REQ-201) and the mutual-consistency relationship the repaired
  checks actually verify.
- `manifest.json`'s recorded `file_digest` for
  `human_confirmation_evidence.schema.json`
  (`a68ea9cbb1e2b68831732fd31c69ee1eec753160e354f0e76f85ba4d47a48019`)
  independently recomputed (`hashlib.sha256` of the file's current bytes)
  and confirmed to match exactly — the manifest's dependent-artifact
  update claimed by 146H.3 is genuine, not merely asserted.
- `human_governance_record`'s manifest entry independently confirmed at
  `schema_version: "1.1"`; all three siblings remain at `"1.0"` — matching
  every prior 146-series report's claim.

### 9.1 Informational finding: a second, unrelated, dead `SUPPORTED_SCHEMA_VERSION` constant

Independently discovered while grepping for any remaining hardcoded
version constant across `src/`: `src/pcae/governance/inspection.py:42`
declares `SUPPORTED_SCHEMA_VERSION = "1.0"` — structurally the same
pattern that was 146H's own Blocking defect in `verification.py`. Direct
inspection of the entire file (`grep -n "schema_version"
src/pcae/governance/inspection.py`) confirms this constant is **never
referenced in any comparison or gate** — it appears only in its own
declaration and in `__all__` (line 328). `inspection.py`'s own
`_shape_check`-equivalent logic (lines 220-280) validates shape via
`validate_record_shape` and checks `schema_id` agreement only; it never
gates on `schema_version` equality at all, so no artifact of any version
is ever rejected by this module for that reason.

**Live-confirmed harmless**: `pcae governance-record inspect` against the
live 146H.3V bundle's `human_governance_record` (`schema_version: "1.1"`)
succeeds and correctly reports the manifest's `schema_version: "1.1"` in
its own `manifest_entry` field, unaffected by the dead constant.

**Classification: Informational, not Blocking.** This is dead code, not a
live defect — it rejects nothing, gates nothing, and does not affect
`pcae governance-record inspect`'s behavior in any observed case. It is
the same class of staleness that caused 146H's Blocking finding in the
sibling `verification.py` module, left in a *read-only, representation-only*
module (`inspection.py`'s own docstring: "non-authoritative... never
upgrades a declared claim into a verified one") where it happens to be
unreachable rather than load-bearing. Recommended, not required: remove
it in a future documentation/cleanup-scoped phase to prevent a future
maintainer from mistakenly wiring it into a live gate, exactly the failure
mode 146H demonstrated in the sibling module.

---

## 10. Fixture Migration Assessment

Independently diff-reviewed the three fixtures 146H.3 claims to have
migrated (`tests/fixtures/chgr/valid_confirmation_evidence.json`,
`valid_integrity.json`,
`adversarial_assurance_overclaim_selfconsistent_confirmation.json`) plus
the migration report's fourth claim (`valid_provenance.json`, claimed
unchanged):

- `valid_confirmation_evidence.json`: `confirmed_content_digest` and
  `preview_rendering_digest` independently confirmed byte-identical
  (`edc77daddb070bdb...`, first 16 hex chars checked directly) —
  consistent with the new mutual-consistency rule.
- `valid_integrity.json`: `payload_digest`
  (`a9131c182baba135...`) independently confirmed identical to
  `valid_record_published.json`'s own `record_digest`
  (`a9131c182baba135...`) — consistent with `integrity_consistency`'s
  repaired comparison target.
- `valid_record_published.json`: `schema_version` independently confirmed
  at `"1.1"` (the 146H.1 fixture migration), consistent with both repairs
  applying to the same fixture set without conflict.
- No fixture's substantive content (decision subject, template, selection,
  evidence, assurance level, lifecycle state, tamper markers) shows any
  change beyond the digest/version fields directly implicated by either
  repair, confirmed by the specific field-level checks above (a full
  line-by-line `git diff` of the 146H.1/146H.3 commits was not
  independently re-run in this phase, since 146H.1's own report already
  quotes its diff scope and this phase's own live reconstruction — §4 —
  demonstrates the fixture set is not the sole evidence for either
  repair's correctness).

No fixture change was found to conceal a production defect: every
migrated value was independently confirmed self-consistent with what the
real, unmodified `build_publication_record` actually constructs (§4),
not merely internally consistent with itself.

---

## 11. Adversarial Matrix

All scenarios below were executed live against the fresh 146H.3V bundle
(§4), using `verify_artifact_at_path` directly (and, where noted, the real
CLI). "Rejected" always means a `VerificationFailure` was returned, never
a `VerificationObservation` with a merely-lower check count.

**Schema version:**
- Current (`"1.1"`): passes (§5).
- Stale (`"1.0"`): rejected, `SCHEMA_INVALID` (§5).
- Future/unknown (`"9.9"`): rejected, `SCHEMA_INVALID` (§5).
- Malformed (`"not-a-version"`): rejected, `SCHEMA_INVALID` (§5).
- Family mismatch (schema_id swapped): rejected, `UNREGISTERED_SCHEMA` (§5).

**Confirmation binding:** all five scenarios in §6 confirmed; missing
sibling explicitly `skipped`, never silently passed.

**Provenance:** all four scenarios in §7 confirmed, including a sibling
from a wholly different, independently-constructed bundle correctly
treated as absent (`skipped`), not accepted.

**Integrity:** all three scenarios in §8 confirmed, including primary-record
tamper caught by the unrelated, pre-existing `digest_self_consistency`
check.

**Bundle composition:**
- Duplicate sibling of the same type, both identical: verified normally
  (first match used; no difference in outcome since both copies are
  byte-identical).
- Reordered `--related` arguments (integrity, confirmation, provenance in
  place of confirmation, provenance, integrity): identical outcome,
  confirming order-independence for the non-conflicting case (§4).
- Malformed related-artifact bytes (`b"{not valid json"`) appended
  alongside the three genuine siblings: **silently ignored, did not
  crash**, verification proceeded and passed on the three genuine
  siblings alone. Confirmed intentional per `_parse`'s own return-`None`
  fallback (`verification.py:190-194`) and its use in the `related_bytes`
  loop (`verification.py:268-272`), which appends a parsed candidate to
  `related_records` only if it is a dict with both `schema_id` and
  `record_type` present — anything else (malformed JSON, wrong shape, a
  bare list) is dropped, not raised. The module's own docstring states it
  "performs no filesystem I/O beyond the package-owned CHGR schema
  resource resolution, no mutation" and is meant to be usable with
  best-effort related-artifact supply; silently dropping an unusable
  candidate rather than crashing the whole verification is consistent
  with that design, not a defect.

**One Non-Blocking finding — order-dependent duplicate-`record_id`
resolution:** constructed two *conflicting* `human_confirmation_evidence`
artifacts sharing the exact same `record_id` (the genuine one, and a
tampered copy with `confirmed_content_digest` forced to a different value
and its own `record_digest` recomputed to stay self-consistent) and
supplied both as `--related` siblings simultaneously. `_find_related`
(`verification.py:349-355`) returns the **first** `related_records` entry
matching family+`record_id`, so the outcome flips between `verified` and
`REJECTED(CONFIRMATION_UNBOUND)` depending purely on which copy appears
first in the `related_bytes` tuple/`--related` argument order — direct
contradiction of the "reordering doesn't matter" property demonstrated in
the non-conflicting case above.

**Classification: Non-Blocking.** Exploiting this requires an attacker who
already possesses (or fabricates) two *distinct* artifacts sharing the
exact same `record_id` (a `uuid.uuid4()`-derived, unguessable value never
reused by construction, CHGR-REQ-196) and controls the order in which a
verifier's caller supplies them as `--related` arguments — a scenario the
verifier's own threat model (a human or tool deliberately supplying
related evidence, per the module's docstring: "any related artifacts
supplied alongside it") does not obviously anticipate as adversarial
input curated by an untrusted party, but is nonetheless a real,
demonstrated non-determinism the module does not itself guard against
(no duplicate-`record_id`-within-`related_records` detection exists).
Recommended, not required: `_find_related` (or its caller) could reject
outright, rather than silently pick one, when two supplied related
artifacts of the same family claim the same `record_id` with differing
content.

---

## 12. Regression Assessment

- `fast_green` gate (`python -m pytest -m "fast_green" -n auto -ra
  --durations=10 -q`): **4391/4391 passed**, identical to every prior
  146-series phase's own claimed count (146G, 146H, 146H.1, 146H.3).
- Broad sweep (`.venv/bin/python -m pytest -k "chgr or publication or
  governance or verification" -q`), run to full completion in this phase
  (an earlier attempt was mistakenly interrupted mid-run at ~79% when its
  parent-process CPU-time reading appeared to plateau — a false signal,
  since much of this sweep's cost is in child-process CLI subprocesses
  not reflected in the parent's own `ps` CPU accounting; re-run to
  completion without interruption):

  **`8 failed, 3995 passed, 4 skipped, 22791 deselected in 501.65s`**

  All 8 failures independently classified pre-existing and structurally
  unrelated to CHGR/governance verification, `verification.py`, or any
  file either 146H.1 or 146H.3 touched:

  - `test_cltr_authority_136ah_publication.py::test_136ah_wheel_contains_publication_module_no_later_family`
    and `test_cltr_authority_136ai_publication_independent.py::TestPackaging::test_wheel_contains_publication_module_and_both_schemas_no_later_family`
    — this environment, unlike 146H.3's own, has `python -m build` 1.4.4
    genuinely installed (`python -m build --version` succeeds), so these
    ran for real rather than erroring on a missing module.
    Independently reproduced in isolation: a genuine wheel is built and
    `pcae/cltr/authority/bindings.py` (and `compatibility_quarantine.py`)
    are genuinely present in it, contradicting the assertion that only
    `publication.py` should ship. `git log` confirms neither
    `bindings.py` nor `compatibility_quarantine.py` was touched by any
    Chapter 146 phase (last touched Phase 136AT, Stage 3 Typed Authority
    Model) — the same conclusion 146H itself independently reached
    (§7 of `PHASE_146H_...md`), reproduced here again with `build`
    actually available and the assertion genuinely, not hypothetically,
    failing.
  - `test_chgr_packaging.py` (3 tests) — independently re-run in
    isolation: **3/3 passed**, confirming this environment's `build`
    availability does not itself introduce any new CHGR-specific
    packaging regression; only the two pre-existing, structurally
    unrelated `authority`-family wheel-content assertions fail.
  - `test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py::test_136u_no_runtime_code_references_group10_families_outside_schema_resources`
    — reconfirmed unrelated to CHGR/publication/verification; flags
    `src/pcae/cltr/authority_inspection.py` referencing Group 10 binding
    names outside its own authorized-file allowlist, exactly as 146H.3
    independently found.
  - `test_cltr_migration_135p_verification.py::TestFourEntryPointsThroughRealFinalizationBoundary::test_migration_evidence_recovery_classification_for_each_entry_point`
    (4 parametrized cases: `task_finish`, `phase_complete`,
    `phase_report_create`, `notify_send_report`) — **not previously
    disclosed by any 146-series report**, newly observed in this phase's
    own independent sweep. Independently re-run in isolation
    (`pytest tests/test_cltr_migration_135p_verification.py -q`):
    identical 4/4 failures, deterministic, not order-dependent
    (`4 failed, 20 passed`). Root cause, by direct inspection of the
    failure: `run_finalization_transaction`'s receipt-notification
    best-effort path returns `status="completed_receipt_best_effort_incomplete"`
    instead of `"completed"` for a synthetic, in-test-constructed report —
    a finalization-transaction/notification-receipt behavior entirely
    unrelated to CHGR construction or verification.
    `git log -- tests/test_cltr_migration_135p_verification.py` shows the
    file was last touched at Phase 135T (Atomic Publication Rehearsal
    Independent Verification) — a chapter with no relationship to CHGR-001
    or `governance/verification.py`, confirming this is pre-existing and
    structurally unrelated, not introduced by 146H.1 or 146H.3. This
    phase's own `-k "verification"` filter term is what pulled this file
    into the sweep (pytest's `-k` matches the substring `verification`
    against the module name `test_cltr_migration_135p_verification`, not
    because its content relates to CHGR verification).
  - `test_runtime_introspection_prototype.py::test_get_governance_returns_governance_info`
    — independently re-run in isolation: **74/74 passed** in that file,
    confirming (as 146H.3 itself found) this is an order/parallelism-
    dependent flake within the broad, serial sweep, not a real,
    reproducible regression.

---

## 13. Findings

1. **Non-Blocking** — order-dependent resolution when two conflicting
   related artifacts share the same `record_id` (§11): `_find_related`
   returns the first match in supplied order rather than detecting or
   rejecting the ambiguity. Requires an attacker already in possession of
   two distinct artifacts sharing an unguessable, `uuid.uuid4()`-derived
   `record_id` — a narrow, non-obvious precondition — but is a genuine,
   demonstrated non-determinism.
2. **Informational** — `src/pcae/governance/inspection.py:42` declares a
   second, unrelated, structurally identical `SUPPORTED_SCHEMA_VERSION =
   "1.0"` constant, independently confirmed dead code (never referenced
   in any comparison, gate, or rejection path in that module). Not
   Blocking: live-confirmed `pcae governance-record inspect` is unaffected
   by any schema-version value on a real artifact.
3. **Non-Blocking, reconfirmed** — every regression-suite failure observed
   in this phase's own independent re-run (§12) was independently traced
   to a pre-existing, structurally unrelated cause (packaging/`build`
   tooling absence, an unrelated `authority_inspection.py` drift, or
   order-dependent test isolation), matching 146H.1's and 146H.3's own
   independently-reproduced classifications, not merely re-trusted from
   their text.
4. **Non-Blocking, reconfirmed** — the fixture migrations claimed by
   146H.1/146H.3 are genuine on disk and independently confirmed
   self-consistent with a freshly, independently constructed production
   bundle (§4, §10), not merely internally self-consistent.

5. **Non-Blocking, newly observed by this phase, not previously disclosed
   by any 146-series report** — `test_cltr_migration_135p_verification.py`'s
   four `TestFourEntryPointsThroughRealFinalizationBoundary` parametrized
   cases fail deterministically (`4/4`, reproducible in isolation),
   independently root-caused to `run_finalization_transaction` returning
   `"completed_receipt_best_effort_incomplete"` rather than `"completed"`
   for a synthetic test report. `git log` confirms this file was last
   touched at Phase 135T, structurally unrelated to CHGR-001 or
   `governance/verification.py`; the only reason it entered this phase's
   `-k "verification"` sweep is a filename substring match, not a
   substantive relationship to CHGR verification (§12).

No Blocking finding was identified in this phase. Construction
(`record.py`) and verification (`verification.py`) agree on every digest
field's semantics tested; no digest role is conflated; no permissive
version acceptance was found; every fail-closed guarantee this phase
attempted to defeat held.

---

## 14. No-Go Confirmation

This phase modified no file under `src/`, `docs/contracts/`, or
`src/pcae/schema_resources/**`. All bundle construction, mutation, and
verification was executed in-memory and against scratch files outside the
repository (`/private/tmp/claude-501/.../scratchpad/chgr_repro/*.json`,
`build_bundle.py`, `adversarial.py`, `adversarial2.py`, `broad_sweep.log`),
deleted at phase close. This document
(`docs/PHASE_146H3V_GOVERNANCE_VERIFICATION_REPAIRS_INDEPENDENT_VERIFICATION.md`)
is the only new file added to the tracked repository tree by this phase.
`git status --short` at phase close (below) shows exactly one untracked
file: this report.

```
?? docs/PHASE_146H3V_GOVERNANCE_VERIFICATION_REPAIRS_INDEPENDENT_VERIFICATION.md
```

No `git commit`, `git push`, `pcae phase complete`, `pcae commit`, or
`pcae push` command was run by this phase, per its own scope boundary.

---

## 15. Overall Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS.**

Both Chapter 146 verifier repairs — 146H.1 (schema-version support) and
146H.3 (confirmation-binding/provenance/integrity comparisons) — are
independently confirmed correct, together and individually, by direct,
adversarial, live reproduction using the real, unmodified production
construction path (`build_publication_record`) and the real production
verification surfaces (`verify_artifact_at_path`,
`pcae governance-record verify`). A genuine production bundle now
verifies successfully end-to-end with every applicable cross-artifact
check reporting `passed`, not skipped — the exact outcome 146H
demonstrated was previously and unconditionally impossible. Every
fail-closed boundary this phase attempted to defeat (mismatched digests,
malformed values, missing siblings, tampered primary/sibling content,
stale/unknown/malformed schema versions, wrong-type or foreign-bundle
sibling substitution) held. Two findings were identified, neither
Blocking: an order-dependent duplicate-`record_id` resolution ambiguity,
and a dead, harmless, structurally analogous constant in the unrelated
`inspection.py` module.

---

## 16. Recommended Next Phase

**146I — CHGR-001 Schema-Envelope Operational Readiness Assessment**, per
this chapter's own established recommendation (146H §14), now that both
verifier repairs are independently confirmed and no Blocking finding
remains outstanding. This recommendation is not an authorization; a human
decision point governs whether and how any further Chapter 146 work
begins. Separately, and at whatever priority a future phase judges
appropriate (neither is release-blocking): the two Non-Blocking/
Informational findings in this document (§13.1, §13.2) are candidates for
a narrowly scoped follow-up cleanup, but do not themselves warrant
deferring 146I.
