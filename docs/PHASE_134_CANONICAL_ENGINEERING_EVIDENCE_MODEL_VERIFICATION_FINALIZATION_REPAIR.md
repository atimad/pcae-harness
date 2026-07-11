# Phase 134E.1V Finalization Repair — 134E vs 134E.1V Identity Mismatch

## 1. Incident

Phase 134E.1V's technical work (independent verification of the
Canonical Engineering Evidence executable model, two BLOCKING defects
found and repaired) completed successfully. Its terminal report,
however, was not trusted: `report_completeness: partial`, missing trust
field `metadata_consistency`, with a reported mismatch of "canonical
report title phase_id=134E, current phase_id=134E.1V." Phase 134E.1V had
therefore not reached a fully governed terminal state.

## 2. Observed Mismatch

- Governed (correct) phase identity: `134E.1V`.
- Value the trust engine extracted from the canonical report title:
  `134E`.

## 3. Investigation Methodology

Per this phase's explicit instruction, no cause was assumed in advance.
Traced the complete identity flow: active task identity, `--phase-id`
CLI argument, `.pcae/phase-completion-report.md` title, `.pcae/phase-
completion-metadata.json`, `PhaseReport` construction, phase-ID parsing/
normalization, report trust validation, metadata-consistency validation,
report promotion, notification dispatch, `latest.*` pointers, task
completion, repository transition validation, and `pcae phase metadata-
repair`. Read every source function that parses or compares a phase
identifier, and independently re-executed each regex against the actual
observed strings rather than reasoning about them abstractly.

## 4. Exact Root Cause

`src/pcae/core/phase_reports.py` contained the **same literal regex**,
independently duplicated, in two functions both invoked during trust
assessment (`_apply_canonical_and_trust()` calls both, in order):

```python
r'^#\s+Phase\s+(\d+[A-Z](?:\.\d+)*)\b'
```

used by:
- `validate_canonical_report()` (canonical-report validation)
- `_check_canonical_metadata_consistency()` (the check that actually
  fired and produced the observed mismatch)

**Mechanism**: for input `"# Phase 134E.1V Complete — ..."`, the regex
engine matches `134E` against `\d+[A-Z]`, then attempts `(?:\.\d+)*`
against `.1V`. It successfully consumes `.1` (dot + one-or-more digits),
but then must satisfy the trailing `\b` (word boundary) immediately
afterward. The next character is `V` — a word character immediately
following another word character (`1`) — so **no word boundary exists
at that position**, and `\b` fails. The regex engine backtracks: it
reduces `(?:\.\d+)*` from one repetition to zero, landing on `134E` with
`.` immediately following — `E` (word) to `.` (non-word) **is** a valid
boundary, so the match succeeds there instead, discarding `.1V` entirely.

Independently reproduced and confirmed with the exact pattern before
writing any code change:

| Title | Captured (pre-fix) |
|---|---|
| `# Phase 134E.1V Complete — X` | `134E` |
| `# Phase 134E.2 Complete — X` | `134E.2` (no trailing letter — unaffected) |
| `# Phase 134E.10 Complete — X` | `134E.10` (no trailing letter — unaffected) |
| `# Phase 134E.10V Complete — X` | `134E` (same defect) |
| `# Phase 134B.3 Complete — X` | `134B.3` (no trailing letter — unaffected) |

## 5. Authority Sources Involved and Answers to the Ten Investigation Questions

1. **Which source supplied `134E`?** The trust engine's own regex-based
   extraction from `.pcae/phase-completion-report.md`'s title — not any
   externally-declared value.
2. **Which source supplied `134E.1V`?** `report.phase_id`, correctly
   resolved via `resolve_canonical_phase_identity()` (the CLI
   `--phase-id 134E.1V` argument, matching the correctly hand-repaired
   `.pcae/phase-completion-metadata.json`).
3. **Was either source stale?** No. `.pcae/phase-completion-report.md`'s
   title was, and always had been, correctly `# Phase 134E.1V Complete —
   ...` (independently re-inspected and confirmed — the artifact was
   never wrong). `.pcae/phase-completion-metadata.json`'s `phase_id` was
   also already correctly `134E.1V` (repaired via `pcae phase metadata-
   repair` before the failing `phase complete` call). Neither artifact
   was stale.
4. **Does a parser truncate dotted phase identifiers?** Only when a
   dotted segment is immediately followed by a bare letter with no
   further boundary-safe character — confirmed above. Plain dotted
   identifiers without a trailing letter (`134E.2`, `134E.10`, `134B.3`)
   were never affected.
5. **Are verification suffixes such as `V` supported consistently?** No
   — confirmed three independently-written regexes in this codebase
   (title-consistency check, canonical-report validation, and a third,
   differently-shaped pattern in `_parse_leading_phase_reference()` used
   for active-task-title identity resolution) all share the same blind
   spot for a bare trailing letter after a dotted segment, though they
   fail differently: the two now-repaired regexes truncated to the
   parent; `_parse_leading_phase_reference()`'s pattern fails to match
   at all (returns `None`) for such a title, meaning a task titled
   exactly `"Phase 134E.1V — ..."` would silently fall through to the
   next identity-resolution source rather than resolving from the task
   title. **Not repaired in this phase** (§9 below) — out of scope for
   this incident, since it was not the cause of the observed mismatch
   (this session's finalization task titles began with `"Finalize
   Phase ..."`, which never matched that stricter leading-anchor pattern
   in the first place, active or not).
6. **Do report titles and metadata use different normalization
   functions?** Yes — confirmed exactly two independent copies of the
   identical (buggy) pattern existed before this repair. Both are now
   replaced by one shared function, `_extract_canonical_title_phase_id()`,
   closing the divergence risk by construction.
7. **Would metadata-repair safely resolve this case?** Yes, and it
   already had: `pcae phase metadata-repair` (134B.3) parses the
   canonical report title with its own, independently-written, more
   permissive regex (`^#\s+Phase\s+(\S+)\s+Complete\s+—\s+(.+?)\s*$`,
   which captures any non-whitespace token, including `134E.1V` in
   full) and had already correctly written `134E.1V` into metadata
   before the failing `phase complete` call — confirmed by inspecting
   `.pcae/phase-metadata-repairs.log`'s entry for this phase, which
   already reads `phase_id 'X' -> '134E.1V'` (full, untruncated). The
   metadata-repair path was never the defect.
8. **Did external delivery occur before consistency was established?**
   Yes — the first terminal delivery (commit `e1c9cb31`) was dispatched
   as a `PARTIAL WARNING`, per 113X.3's rule that a finalized-but-partial
   report must never be silently dropped. It was not a normal "Phase
   COMPLETED" notification, and it was not silently suppressed either —
   it correctly disclosed the partial state to the operator. See §7 for
   how this repair phase treats that delivery.
9. **Could this mismatch class affect future identifiers?** Confirmed:
   `134E.2` and `134E.10` are unaffected (no trailing letter); `134E.2V`
   and `134E.10V` **would** have hit the identical defect had they
   arisen before this repair. This repair closes the defect for the
   general case (`\d+[A-Z](?:\.\d+[A-Za-z]?)*` — see §6), not just the
   one observed instance, so `134E.2V`, `134E.10V`, and any future
   dotted sub-phase with a bare verification-suffix letter now parse
   correctly.
10. **Was the identity invariant bypassed, or correctly caught?**
    **Correctly caught.** The fail-closed design worked exactly as
    intended: a real (if artifact-external) mismatch was detected,
    canonical promotion was refused, and the operator was not silently
    told the phase was fully trusted when it was not. The defect was in
    the *comparison mechanism*, not in the *decision to enforce* the
    comparison — the invariant itself held.

## 6. Repair

**Classification: implementation-level, not artifact-only.** The
artifact (`.pcae/phase-completion-report.md`) was already correct; no
artifact repair could have fixed a mismatch caused by the *comparison
logic* misreading a correct artifact.

**Location:** `src/pcae/core/phase_reports.py`. Added one module-level
constant and one shared helper function,
`_extract_canonical_title_phase_id()`, using the corrected pattern:

```python
r'^#\s+Phase\s+(\d+[A-Z](?:\.\d+[A-Za-z]?)*)\b'
```

— allowing **one** optional bare letter inside each dotted segment
(`\.\d+[A-Za-z]?`), so a verification suffix is consumed as part of the
identifier rather than trailing it and breaking the word-boundary check.
Replaced both `validate_canonical_report()`'s and
`_check_canonical_metadata_consistency()`'s local, independently
duplicated `re.search(...)` calls with calls to this one shared function.

**Compliance with the repair rules:**
- Smallest shared identity boundary: one function, two call sites
  updated, no new module, no new identity authority.
- Fail-closed conflict behavior preserved: a genuinely stale/wrong title
  (e.g. still literally reading `# Phase 134E Complete`) is still
  detected and still blocks promotion — confirmed by test
  (`test_stale_truncated_parent_still_detected_as_mismatch_pre_fix_
  scenario`).
- No new phase-identity authority: the function only extracts and
  compares; identity resolution precedence (`resolve_canonical_phase_
  identity()`) is untouched.
- Report-trust validation not weakened: the same two call sites still
  run, still append the same class of mismatch warning when a genuine
  mismatch exists.
- No silent parent/sub-phase equivalence: `134E` and `134E.1V` remain
  distinct values (confirmed by test) — the fix corrects *extraction*,
  not the *comparison*, which was already correctly strict.
- Distinct identifiers remain distinct, no prefix matching, no parent
  fallback: confirmed for `134E`, `134E.1`, `134E.1V`, `134E.2`,
  `134E.10`, `134E.10V` (all extract to their own exact, distinct
  values).

## 7. Notification Handling

The first terminal delivery (commit `e1c9cb31`, `PARTIAL WARNING`,
recorded in `.pcae/phase-reports/.last-notified.json` and preserved in
`.pcae/phase-reports/20260711-003356-134E.1V.md`/`.json`) is **not**
hidden or pretended-away. It is explicitly referenced in §0 of the
corrected canonical report (`.pcae/phase-completion-report.md`) as the
record this corrected artifact supersedes. Per PFN-001's exactly-once
policy and this phase's own instruction not to introduce a new
notification architecture, exactly one additional corrective terminal
delivery is dispatched after this repair restores consistency — using
the same existing `pcae phase complete` / idempotency-marker path
already governing every other phase in this track, not a new mechanism.
No duplicate uncontrolled notification occurs: the existing marker/
idempotency check (already independently verified in 134B.2/134B.3/
134C/134D/134E.1/134E.1V's own finalizations) continues to guarantee
exactly one dispatch per phase_id+commit pair.

## 8. Tests

14 new regression tests added
(`tests/test_phase_reports_134e1v_identity_repair.py`): exact parsing of
`134E.1V`/`134E.2`/`134E.10`/`134E.10V`; parent/sub-phase distinctness;
verification-suffix-is-part-of-identity; title/metadata cross-consumer
agreement; stale-truncated-parent still detected (fail-closed preserved);
identity conflict fails closed at the repository transition validator
(independent of `phase_reports.py`); metadata-repair produces the full
exact identifier; report promotion rejects truncated identity via
completeness downgrade; the positive control (correctly-titled report
reaches `COMPLETENESS_COMPLETE`); existing simple identifiers remain
compatible; and a 134B.3-style regression confirming the shared
consistency check's existing, correct behavior is unweakened. All 14
pass.

## 9. Remaining Technical Debt

`_parse_leading_phase_reference()` (used for active-task-title identity
resolution) shares the same underlying blind spot (a bare trailing
letter after a dotted segment) but fails by non-match rather than
truncation, and was not the cause of this incident (no active task in
this session's flow had a bare `"Phase <id> — ..."`-format title at the
relevant moment). Recorded as the same debt class (134B §34 item #4,
"historical phase-ID comparison defect") for a future pass, not repaired
here, consistent with this phase's own scope limits.

## 10. Readiness for 134E.2

The identity mismatch is resolved at its root cause, not worked around.
The corrected canonical report and metadata for Phase 134E.1V reach
`report_completeness: complete` with `metadata_consistency` satisfied.
Track 134 is ready to proceed to **134E.2 — Evidence Extraction**, not
begun in this phase.
