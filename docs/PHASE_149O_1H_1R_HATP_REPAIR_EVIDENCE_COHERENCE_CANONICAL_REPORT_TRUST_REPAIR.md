# Phase 149O.1H.1R — HATP Repair Phase Evidence-Coherence / Canonical Report Trust Repair

**Phase ID:** 149O.1H.1R
**Mode:** canonical phase-report trust / evidence-coherence repair (documentation only; no production code touched)
**Predecessor:** 149O.1H.1 (HATP Timestamp Canonicalization + Constructor-Domain Hardening — completed, `commit d75b96b1`, pushed, but canonical report `Report completeness: incomplete ❌`, missing trust field `internal_evidence_coherence`)
**Date:** 2026-08-06
**Status:** completed
**Runtime boundary:** unchanged (Observed / observe / unavailable)

---

## 1. Original Incomplete-Report Condition

`pcae phase-report show --latest` (re-run at the start of this phase) confirmed, byte-for-byte, the condition described in the governing prompt:

```
Report completeness: incomplete ❌ Manual review required.
Missing trust fields: internal_evidence_coherence
```

with the trust-warning text:

```
internal report evidence is contradictory
  Coherence: test evidence is linked only to other phase identities: 149O, 149O.1C, 149O.1F, 149O.1G, 149O.1H
```

`pcae phase-report reconcile --phase-id 149O.1H.1` independently confirmed:

```
Status: conflict
Promoted generations: 2
Blocker: promoted report is not trust-complete
```

## 2. Missing Field and Validator

The field is produced by `_apply_internal_report_coherence()` in `src/pcae/core/phase_reports.py:1414`, which calls `validate_internal_report_coherence()` (`phase_reports.py:1318`). If that function returns any issues, the report is forced to `report_completeness = incomplete` and `"internal_evidence_coherence"` is appended to `missing_trust_fields`.

Two on-disk generations of the promoted report exist in `.pcae/phase-reports/`:

- `20260806-144825-149O.1H.1.json` (first promotion) — `missing_trust_fields: ['pushed_status', 'origin_main_head', 'internal_evidence_coherence']`
- `20260806-144949-149O.1H.1.json` (second promotion, = `latest.json`) — `missing_trust_fields: ['internal_evidence_coherence']`

Both generations were produced by `pcae phase-report create` at implementation time; neither generation's internal `metadata` dict contains a `test_evidence_classification` key (confirmed by direct inspection: `metadata keys: ['commit_attribution', 'phase_id', 'source_revision']` for the committed reports in this series). This is a separate, deeper finding — see §6.

## 3. Trust-Gate Mechanics (read-only inspection; no modification)

`validate_internal_report_coherence()` builds a bag of "evidence phase identity" tokens by scanning the concatenated `test_results` text with:

```python
r"(?<![A-Za-z0-9])\d+[A-Za-z]+(?:\.?\d+[A-Za-z]*)?(?![A-Za-z0-9])"
```

It then checks whether the current phase's own normalized ID (dots stripped) appears among the extracted tokens; if not, and if any extracted token shares a "series" (`pcae.core.phase_id.same_series`) with the current phase, it raises `"test evidence is linked only to other phase identities: ..."` — **unless** `report.metadata.get("test_evidence_classification") == "inherited_regression"` (an explicit, governed escape hatch documented in the Phase 134E.9 code comment as "the only way to suppress this check").

## 4. Evidence Inventory and Ownership Classification

| Evidence item | Classification |
|---|---|
| Initial governance inspection (git/pcae health/check/coherence/push/runtime) | GENERATED_IN_149O.1H.1 |
| Pre-repair B-149O.1H-1 reproduction (`.0001Z`/`.0009Z` collision) | GENERATED_IN_149O.1H.1 (execution), reproducing a HISTORICAL_REFERENCE_ONLY finding first recorded in 149O.1H |
| Pre-repair B-149O.1H-2 reproduction (bool/invalid-field constructor bypass) | GENERATED_IN_149O.1H.1 (execution), reproducing a HISTORICAL_REFERENCE_ONLY finding first recorded in 149O.1H |
| New 93-test repair suite (`test_phase_149o_1h_1_...py`) | GENERATED_IN_149O.1H.1 (artifact and execution both current-phase) |
| 149O.1H independent-verification suite, 166 tests, 8 assertions flipped in place | REGRESSION_OF_PRIOR_PHASE (artifact origin: 149O.1H) with CURRENT_PHASE_DIRECT_EVIDENCE overlay for the 8 flipped assertions (execution + assertion content changed in 149O.1H.1) |
| Wave-3 100-test core regression (`test_hatp_proof_models.py` + `test_hatp_canonical_serialization.py` + `test_phase_149o_1g_...py`) | REUSED_BASELINE_FROM_PRIOR_PHASE (artifact: 149O.1G/Wave-3 baseline); execution is current-phase evidence |
| Wave-1/2 103-test foundation regression | REUSED_BASELINE_FROM_PRIOR_PHASE; execution current-phase |
| 149O.1F.2 90-test regression | REUSED_BASELINE_FROM_PRIOR_PHASE; execution current-phase |
| HATP contract independent-verification suite | REUSED_BASELINE_FROM_PRIOR_PHASE; execution current-phase |
| RAE/PB/agent regression (5 failed / 5631 passed, pre-existing) | REUSED_BASELINE_FROM_PRIOR_PHASE; execution current-phase; failures HISTORICAL_REFERENCE_ONLY (pre-existing, unrelated) |
| Fast Green 4531 | REUSED_BASELINE_FROM_PRIOR_PHASE test set; execution current-phase |
| Production diff (`human_approval_trusted_provenance.py`, 1 file) | GENERATED_IN_149O.1H.1 |
| Contract diff (empty) | CURRENT_PHASE_DIRECT_EVIDENCE (absence confirmed) |
| Commit `d75b96b1` | GENERATED_IN_149O.1H.1 (confirmed by task-lifecycle contract ownership, §5) |
| Golden AG3/AG5 digest bytes | HISTORICAL_REFERENCE_ONLY (fixture constants unchanged since prior to 149O.1H.1; independently recomputed in this phase, see §9) |

**Distinguishing test identity from execution identity (required by governing prompt §6):** a test file whose name embeds `149o_1h` (e.g. the independent-verification suite) was *authored* in Phase 149O.1H, but its *execution* during 149O.1H.1 — including the 8 assertions that were edited in place to record the repair — is evidence generated by 149O.1H.1. The two are not the same fact, and neither this phase nor 149O.1H.1 relabeled the artifact's authorship; only the 8 specific test bodies were edited, with explicit before/after docstrings (see §8).

## 5. Commit and Task Ownership

`tasks/done/20260806-1624-phase-149o-1h-1-hatp-timestamp-canonicalization-constructor-domain-hardening.md` is the governed task contract for 149O.1H.1. Its `Allowed Files` list is exactly `src/pcae/core/human_approval_trusted_provenance.py`, the two named test files, the phase doc, `PROJECT_STATUS.md`, `CHANGELOG.md`, and task/report bookkeeping files. `git diff --name-only d75b96b1~1..a601d511` (the full commit range of the phase) matches this list exactly (see §11). This independently confirms, via lifecycle metadata rather than chronology alone, that commit `d75b96b1` and its tests are owned by Phase 149O.1H.1.

## 6. Root Cause of the Coherence Contradiction

Two compounding, independently source-confirmed defects in the report-generation/validation pipeline — **not** any actual misattribution of evidence in 149O.1H.1's technical work:

**(a) Regex cannot recognize three-component phase IDs.** The tokenizer pattern `\d+[A-Za-z]+(?:\.?\d+[A-Za-z]*)?` contains only a single optional dot-extension. Empirically verified:

```
"Phase 149O.1H.1 repairs B-149O.1H-1" -> ['149O.1H', '149O.1H']
```

`"149O.1H.1"` can only ever tokenize as `"149O.1H"` — the current phase's own three-component ID (`149O.1H.1`, normalized `149O1H1`) can never appear in `evidence_phase_ids`, no matter how the report is worded. This affects every three-component phase ID in this repository's well-established convention (149O.1B.1/.2/.3, 149O.1F.1/.2, 149O.1H.1, …), not just this phase.

**(b) The evidence prose for 149O.1H.1 legitimately cites related finding/phase identifiers** (`B-149O.1H-1`, `B-149O.1H-2`, `149O.1G`, `149O.1F`, `149O.1F.2`, `149O.1C`) inline in its `test_results` values, because the phase is *about* closing findings named with those prefixes. `pcae.core.phase_id.same_series` correctly classifies all of them as the same "149O" series as the current phase, so `same_series` in the validator comes out non-empty and the check fires.

**Directly simulating the validator** against the two promoted report generations confirms this precisely:

```
=== 149O.1F.1 (passed cleanly) ===
evidence_phase_ids: ['8B583817']              # an incidental hex-token match, not a phase ID
same_series: []                                # -> check does not fire

=== 149O.1H.1 (failed) ===
evidence_phase_ids: [... '149O', '149O.1C', '149O.1F', '149O.1G', '149O.1H' ...]
same_series: ['149O', '149O.1C', '149O.1F', '149O.1G', '149O.1H']   # -> check fires
```

149O.1F.1 (the closest precedent — also a narrow three-component-ID repair phase) passed only because its terser `test_results` prose happened not to cite any same-series token, not because of any structural difference in how it was evidenced. This confirms the failure is a validator fragility, not a real evidence-coherence defect in 149O.1H.1.

**(c) The one governed escape hatch is unwired.** The code comment at `phase_reports.py:1375-1378` states an explicit `test_evidence_classification` metadata value of `"inherited_regression"` is "the only way to suppress this check." `.pcae/phase-completion-metadata.json` (the separate, human/CLI-facing completion-metadata convenience file) does carry `"test_evidence_classification": "inherited_regression"` as of commit `a3215148`. However, `pcae phase-report create` — the actual command that builds the `PhaseReport` object the validator inspects — has no CLI argument that can set `test_evidence_classification` (confirmed: `pr_create_parser` in `src/pcae/cli.py` exposes no such flag, and `src/pcae/commands/phase_reports.py` only ever writes `commit_attribution`, `phase_id`, and `source_revision` into `report.metadata`). The value in `phase-completion-metadata.json` is therefore inert with respect to the actual trust gate — a second, independent defect from (a)/(b), and the reason a straightforward "regenerate the canonical report" step (§10) cannot repair this without a code change.

Because of (c), the earlier working theory — that this was merely a stale-metadata / needs-reconciliation issue fixable by re-running `pcae phase-report create` — does not hold up: even a fresh `phase-report create` invocation today, fed the same true, unredacted evidence, would hit the same regex defect (a)+(b) and would have no way to invoke the one documented suppression mechanism (c).

## 7. Fresh Re-Verification of the Two Repair-Critical Findings

Independently re-run this phase, from current source, without relying on 149O.1H.1's summary:

- `python -m pytest tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py -q` → **93 passed** (matches claim)
- `python -m pytest tests/test_hatp_proof_models.py tests/test_hatp_canonical_serialization.py tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py -q` → **100 passed** (matches claim)
- `python -m pytest tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py -q` → **166 passed** (matches claim)

Source-level reconstruction (not test-name-trusting):

- `_require_issued_at` (`human_approval_trusted_provenance.py:243`) rejects any `issued_at` with `parsed.microsecond % 1000 != 0`, before model acceptance.
- Reconstructing the pre-repair module from `git show d75b96b1~1:src/pcae/core/human_approval_trusted_provenance.py` and calling `parse_hatp_proof` directly: `.0001Z` and `.0009Z` both parse and both canonicalize to `2026-01-01T12:00:00.000Z` (**collision independently reproduced**).
- Calling the same two timestamps against current source: both raise `InvalidProofSchemaError` ("sub-millisecond fractional-second precision is not accepted"); `.001Z` (millisecond precision) is still accepted and round-trips unchanged.
- `_require_proof_version` (`human_approval_trusted_provenance.py:330`) has an explicit `isinstance(value, bool)` exclusion before the `int` check; a fresh probe of `HumanApprovalProvenanceProof(proof_version=True, ...)` raises `UnsupportedProofVersionError` on current source.
- `Ag3OperationReference.__post_init__` / `Ag5OperationReference.__post_init__` (lines 117-131) and `HumanApprovalProvenanceProof.__post_init__` (line 158) all call the shared `_require_*` layer; `parse_hatp_proof` → `_build_proof_from_document` calls the identical functions (lines 415-459). Confirmed by direct source read, not by trusting test names.

## 8. Audit of the 8 Modified Historical Tests

`git diff d75b96b1~1 d75b96b1 -- tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py` shows exactly 8 test bodies changed:

1. `test_BLOCKING_submillisecond_timestamps_collapse_to_identical_canonical_bytes`
2. `test_BLOCKING_constructor_accepts_invalid_repository_id_parser_rejects`
3. `test_BLOCKING_constructor_accepts_invalid_digest_parser_rejects`
4. `test_BLOCKING_constructor_accepts_unsupported_version_parser_rejects`
5. `test_BLOCKING_constructor_accepts_boolean_version_parser_rejects`
6. `test_BLOCKING_constructor_accepts_noncanonical_timestamp_parser_rejects`
7. `test_BLOCKING_constructor_accepts_empty_principal_id_parser_rejects`
8. `test_public_constructor_domain_verdict_is_bypass_not_equivalent`

Each retains its historical finding ID (`B-149O.1H-1`/`B-149O.1H-2`) in an expanded docstring that explicitly states the pre-repair behavior ("At the time this suite was written… collapsed/succeeded/bypassed…") before describing the post-repair assertion, and points to the phase doc and the new regression suite. None were deleted; the file's total test count is unchanged (166 before and after). This **preserves historical reproduction evidence while testing repaired behavior** — it does not destroy the original finding record, because (a) the original finding text is retained verbatim in the docstrings, and (b) the pre-repair behavior remains independently reconstructable from git history, as demonstrated in §7 by directly re-deriving the collision from `d75b96b1~1`. This matches the 149O.1F.1 precedent convention cited by 149O.1H.1, independently verified rather than taken on faith.

## 9. Golden-Vector Recomputation

Recomputed directly from `tests/test_hatp_canonical_serialization.py`'s own `_AG3_GOLDEN_BYTES`/`_AG5_GOLDEN_BYTES` constants (not from the governing prompt's example values, which the prompt itself flags as placeholders):

```
AG3: bafc5bc9bf7865652be0dcdb47ca2906666d43fe963e7da7f593bac201efdc83
AG5: 480422914a8a8e90acf8ee1c4ed4dc0adb6b0a3ef294266bb2fcf8a479b6aeaf
```

Both match the values reported by 149O.1H.1 exactly, and both differ from the placeholder digests in the governing prompt text (as 149O.1H.1 itself already noted). Because the canonical millisecond-precision renderer (`_canonical_timestamp_string`) is byte-unchanged by the repair, and both golden fixtures are already millisecond-precision, these digests are stable across the repair — confirmed, not merely asserted.

## 10. Canonical Report Regeneration Attempt

Per governing-prompt §45/§46, regeneration through governed lifecycle tooling (not hand-editing generated truth fields) was the first-line remedy considered. `pcae phase-report create` was inspected (not invoked with fabricated/reduced input) to determine whether a fresh, honest invocation could reach `internal_evidence_coherence: present`. It cannot: the CLI has no parameter to set `test_evidence_classification` on the produced report's `metadata`, and even if it did, the same true evidence text that legitimately cites `B-149O.1H-1`/`B-149O.1H-2`/`149O.1G`/`149O.1F`/`149O.1C` would still trip the three-component-ID regex defect (§6a-b) unless the classification escape hatch actually reached `report.metadata` (§6c). No workaround was attempted that would omit, reword, or truncate genuine evidence citations to dodge the regex — that would constitute fabricating matching data, which is explicitly out of scope for this phase.

## 11. Production/Contract Diff Confirmation

`git diff --name-only d75b96b1~1..a601d511`:

```
.pcae/phase-completion-metadata.json
.pcae/phase-completion-report.md
CHANGELOG.md
PROJECT_STATUS.md
docs/PHASE_149O_1H_1_HATP_TIMESTAMP_CANONICALIZATION_CONSTRUCTOR_DOMAIN_HARDENING.md
src/pcae/core/human_approval_trusted_provenance.py
tasks/DONE.md
tasks/active/20260806-1641-idle-awaiting-next-governed-phase-post-149o-1h-1.md
tasks/done/20260806-1235-idle-awaiting-next-governed-phase-post-149o-1h.md
tasks/done/20260806-1624-phase-149o-1h-1-hatp-timestamp-canonicalization-constructor-domain-hardening.md
tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py
tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py
```

`git diff --name-only d75b96b1~1..a601d511 -- src/pcae/` → exactly one file (`human_approval_trusted_provenance.py`). `-- docs/contracts/` → empty. Wave 1/2, RAE, Permission Broker, and agent boundary files are absent from the list. All confirmed, matching 149O.1H.1's own claims.

## 12. Fast Green

`python -m pytest -m fast_green -n auto -q` → **4531 passed**, identical to the entering baseline. No regression.

## 13. Internal Evidence Coherence — Result

The technical evidence for 149O.1H.1 (production diff, commit ownership, all regression/repair test counts, golden vectors, source-level repair mechanics, and the 8-test historical audit) is **internally coherent and independently reproducible from this repository's own history and source** — every specific, checkable claim in the 149O.1H.1 report was independently re-derived in this phase and matched.

What is **not** coherent is the canonical *report artifact's* own automated trust gate, which cannot currently represent "this three-component-ID repair phase legitimately cites related finding/phase identifiers while also being its own phase" without either (a) a regex fix to recognize three-component IDs, or (b) CLI wiring so the existing `test_evidence_classification` governed escape hatch actually reaches the object the validator reads. Neither is a 149O.1H.1 evidence defect; both are report-system defects.

## 14. Canonical Completeness Result

`Report completeness` **remains incomplete** as of this phase. No hand-edit was made to `missing_trust_fields` or `internal_evidence_coherence`, and no fabricated evidence was introduced to game the regex. Per governing-prompt §43/§50, this phase stops rather than falsifying trust-complete status.

## 15. Technical Status

- **B-149O.1H-1:** CLOSED BY IMPLEMENTATION, PENDING INDEPENDENT 149O.1H.2 RE-VERIFICATION. Fresh evidence in §7 supports this.
- **B-149O.1H-2:** CLOSED BY IMPLEMENTATION, PENDING INDEPENDENT 149O.1H.2 RE-VERIFICATION. Fresh evidence in §7 supports this.

## 16. Trust Verdict

**149O.1H.1 CANONICAL COMPLETION TRUST NOT REPAIRED — INTERNAL EVIDENCE COHERENCE REMAINS BLOCKING**

## 17. Recommended Next Phase

A bounded, narrow report-trust/validator repair phase (not yet numbered/authorized) targeting exactly two defects in `src/pcae/core/phase_reports.py`'s `validate_internal_report_coherence()`/tokenizer and `src/pcae/commands/phase_reports.py`'s `create` command:

1. Extend the phase-ID token regex to recognize three-component canonical IDs (or delegate token extraction to `pcae.core.phase_id`'s own parser instead of a hand-rolled pattern), so a phase's own three-component ID can be recognized in its own evidence text.
2. Wire a `test_evidence_classification` (or equivalent) CLI argument through `pcae phase-report create` into `report.metadata`, so the one documented governed suppression mechanism is actually reachable.

Until that repair lands and 149O.1H.1's canonical report is regenerated and shows `internal_evidence_coherence: present`, **149O.1H.2 (HATP Proof Models + Canonical Serialization Independent Re-Verification) should not begin** under the claim that 149O.1H.1 is trusted-complete — though nothing in this phase's findings suggests the underlying Wave-3 repair itself is technically defective; the block is purely at the report-trust layer.
