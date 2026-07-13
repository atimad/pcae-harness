# Phase 135D.1 — Metadata-Repair Incident Investigation

**Phase class:** Narrow forensic investigation (not a Track 135 architecture/contract phase)
**Scope:** Investigate the `pcae phase metadata-repair` phase_id corruption disclosed during 135D's own finalization. Verify the causal chain from source, not from the prior turn's real-time (and, as this investigation proves, partly incorrect) assumption. Classify 135D's authoritative completion state. Implement the smallest justified repair, only after the evidence chain is fully documented.
**Trigger:** During 135D's finalization, `pcae phase metadata-repair` rewrote `.pcae/phase-completion-metadata.json`'s `phase_id` from `135D` to `135A`. The prior turn's response attributed this to "the known Architecture Status title cross-attribution defect" (135C's finding). **This investigation proves that attribution was wrong.**

---

## 1. Verification: final committed metadata identifies 135D

Directly inspected the committed blob, not the working tree alone:

```
git show a268657ee76fa4e8f9c50dbf8fd84e1c56b01475:.pcae/phase-completion-metadata.json
  phase_id: 135D
  phase_name: Cross-Representation Invariant Architecture and State-Machine Verification
  status: completed
  recommended_next_phase_id: 135E
```

`git diff HEAD -- .pcae/phase-completion-metadata.json` is empty; the working tree matches HEAD exactly. **Confirmed: the currently committed, currently pushed metadata file identifies phase 135D, not 135A.**

---

## 2. The exact string that caused 135A resolution — and correction of the prior turn's hypothesis

`.pcae/phase-metadata-repairs.log`'s own audit entry names its source precisely:

```
2026-07-12T20:28:15.982808+00:00 phase_id '135D' -> '135A' phase_name '...' -> 'Canonical Lifecycle State Authority Architecture' (source: .pcae/phase-completion-report.md title)
```

The source is **`.pcae/phase-completion-report.md`** — a *tracked, hand-authored* canonical narrative file, distinct from both:
- the gitignored, auto-generated `.pcae/phase-reports/latest.md` (the actual promoted phase report), and
- the generated "Architecture Status" section (embedded in phase reports, sourced from `PROJECT_STATUS.md`).

Its content today, and at the time of the incident:

```
$ head -1 .pcae/phase-completion-report.md
# Phase 135A Complete — Canonical Lifecycle State Authority Architecture

$ git log --oneline -1 -- .pcae/phase-completion-report.md
cdcbb926 Sync Phase 135A completion metadata
```

**This file has not been touched since 135A's own completion commit.** No commit for 135B, 135C, or 135D ever updated it — confirmed by `git log -- .pcae/phase-completion-report.md` showing zero entries between `cdcbb926` and the present. Grepping the codebase for `write_canonical_report` (the one function that writes this path) turns up **zero call sites outside its own definition** — no CLI command auto-generates or auto-refreshes this file. It is, and has only ever been, hand-authored, and that hand-authoring step was skipped for three consecutive phases (135B, 135C, 135D).

**Correction of the prior turn's claim:** the prior response asserted the corruption was caused by "the known Architecture Status title cross-attribution defect (135C's finding)" — 135C's finding concerns a *different* file (`PROJECT_STATUS.md`-derived Architecture Status generation, root-caused to a title-extraction regex in `phase_reports.py`) and was never actually re-verified against source before making that claim in the prior turn. It is **not** what happened. The true cause is unrelated: a separate, stale, hand-maintained tracked file that three phases in a row failed to update. This is now corrected with full source verification, per the RE-DERIVE / DO NOT TRUST discipline this track otherwise applies rigorously.

---

## 3. Exact code path of `pcae phase metadata-repair`

`run_phase_metadata_repair()`, `src/pcae/commands/phase.py:745-855` (docstring self-describes intent):

1. Reads `.pcae/phase-completion-report.md` (`canonical_path`), **not** Architecture Status, **not** `.pcae/phase-reports/latest.md`.
2. Parses **only its first line** via `_CANONICAL_REPORT_TITLE_RE = re.compile(r"^#\s+Phase\s+(\S+)\s+Complete\s+—\s+(.+?)\s*$")`.
3. Treats the parsed `(phase_id, phase_name)` as **authoritative ground truth by explicit design** — the docstring states: "reads the *already hand-authored, reviewed* canonical narrative report... and syncs metadata's `phase_id`/`phase_name`/`phase_title` fields to match that report's own title exactly. One direction only: canonical report -> metadata, never the reverse."
4. Writes `.pcae/phase-completion-metadata.json`'s `phase_id`/`phase_name`/`phase_title` to match, unconditionally, whenever they disagree — with **no recency check, no cross-check against the currently active phase, no check for which side is actually stale.**
5. Appends one audit line to `.pcae/phase-metadata-repairs.log`.

All three of the assignment's specific sub-questions, answered:

| Question | Answer |
|---|---|
| Did it parse phase identity from the generated Architecture Status title? | **No.** It parsed the first line of `.pcae/phase-completion-report.md`, a different, hand-maintained, tracked file. |
| Did it treat that derived identity as authoritative? | **Yes**, by explicit design — this is the tool's whole stated purpose (105/134B.3 hardening: treat the canonical report as reviewed ground truth). |
| Did it rewrite valid metadata from 135D to 135A? | **Yes**, because the "ground truth" file it trusted was stale (stuck at 135A content since 135B/135C/135D all skipped updating it) — not because the tool malfunctioned relative to its own design, but because its design has no defense against a stale "ground truth" input. |

---

## 4. Exact timing

| Event | Timestamp (local, UTC+2) | UTC | Artifact |
|---|---|---|---|
| Certification, promotion, notification dispatch (`pcae phase complete --allow-partial-report`) | 22:27:57 | 20:27:57 | `.pcae/phase-reports/20260712-202757-135D.md` / `.json`, promoted to `latest.md`/`latest.json`; marker `.pcae/phase-reports/.last-notified.json` bound |
| **Invalid rewrite** (`pcae phase metadata-repair`) | 22:28:15 | 20:28:15 | `.pcae/phase-completion-metadata.json` only (per audit log) |
| Revert committed | 22:29:26 | 20:29:26 | commit `d8e440754b95d3052a7b8d84110e0f23ab41bad7` |
| Correction task closure committed | 22:29:31 | 20:29:31 | commit `a268657ee76fa4e8f9c50dbf8fd84e1c56b01475` (pushed) |

- **The rewrite occurred 18 seconds *after* certification, promotion, and Telegram notification dispatch** — strictly post-terminal-closure, never before or during.
- **It never entered an immutable snapshot or checkpoint.** `--allow-partial-report` causes `run_phase_complete()` to take the `else: fin = _promote_and_dispatch()` branch (`src/pcae/commands/phase.py:488`, `if gate.get("finalizable") and not allow_partial_report:`) — the entire `run_finalization_transaction()` checkpoint/snapshot pipeline is **structurally skipped whenever `--allow-partial-report` is used**. No `.pcae/finalization-transactions/*135D*` file exists (confirmed by direct search); this documentation-only phase's completion never engaged that mechanism at all.
- **It never entered promotion.** `metadata-repair` writes exactly two things: `.pcae/phase-completion-metadata.json` and `.pcae/phase-metadata-repairs.log`. It does not touch `.pcae/phase-reports/*`, `latest.md`, or `latest.json` — confirmed by reading its full implementation (§3 above) and by direct inspection: `.pcae/phase-reports/20260712-202757-135D.json`'s `phase_id` field reads `135D` right now, unchanged.
- **Marker**: `.pcae/phase-reports/.last-notified.json`, bound at 22:27 (before the corruption), reads `"phase_id": "135D"` throughout, with `report_digest`/`finalization_snapshot_id` bound to the 135D report. Never touched by `metadata-repair`. Still correct.
- **Receipt**: no delivery receipt exists for this event at all (`.pcae/delivery-receipts/receipts/` — the ten most recent entries all predate 22:00; none corresponds to the 135D dispatch). This is a separate, pre-existing, unrelated gap in the harness's own receipt-creation coverage for `--allow-partial-report`-path dispatches — not something the corruption could have "bound," since nothing was created to bind.
- **It was purely transient local `.pcae/phase-completion-metadata.json` state** for approximately 71 seconds, corrected before the next push.
- **Correction commit:** `d8e440754b95d3052a7b8d84110e0f23ab41bad7` ("Revert erroneous Phase 135D metadata-repair phase-id corruption"), included in the push that landed at `a268657e`.

---

## 5. Why the final canonical report still shows `report_completeness: partial` / `missing_trust_fields: [metadata_consistency]`

**Precision correction of the assignment's own framing:** the already-promoted phase report (`.pcae/phase-reports/20260712-202757-135D.json`, and `latest.json`) does **not** record `phase_id: 135A` anywhere in its own identity field — it correctly and exclusively records `phase_id: 135D`. The string `"135A"` that appears is confined to a diagnostic `trust_warnings` line: `"Mismatch: canonical report title phase_id=135A, current phase_id=135D"` — a comparison *result* naming the stale external file's content, not a claim about the report's own identity.

The mechanism (`src/pcae/core/phase_reports.py`):
- `_apply_canonical_and_trust()` calls `load_canonical_report()`, which reads `.pcae/phase-completion-report.md` (`_CANONICAL_REPORT_PATH`, line 918) into `report.canonical_report_content`.
- `_check_canonical_metadata_consistency(report)` (line 1006) then regex-extracts a title-phase-id from that same stale content and compares it to `report.phase_id`. Since the file's title still reads "Phase 135A Complete," the comparison fails, `report.report_completeness` is downgraded to `"partial"`, and `"metadata_consistency"` is appended to `missing_trust_fields`.

This is why it was **still** partial even after I corrected `.pcae/phase-completion-metadata.json`: my correction fixed the *metadata* side of the comparison, but never touched `.pcae/phase-completion-report.md`, the actual input the comparison reads. **Confirmed still true right now** — `.pcae/phase-completion-report.md`'s first line still reads `# Phase 135A Complete — ...`, untouched since `cdcbb926`. Any report generated today would still be marked partial by this same check.

**135C hit the identical mismatch during its own finalization**, independently confirmed via its own quarantine artifacts (`.pcae/phase-reports/quarantine/20260712-185742-135C.blocked.md` and `...185833-135C.blocked.md`, both containing `canonical report title phase_id=135A`). This is not a 135D-specific defect — `.pcae/phase-completion-report.md` has been stale since 135A across the entirety of 135B, 135C, and 135D. 135C's own metadata JSON was apparently hand-set to `report_completeness: "complete"` after the fact without the underlying file ever being fixed, which is why the earlier session-bootstrap check showed 135C as "complete" — that field is not independently re-derived at read time by `pcae phase-report show --latest`, so a hand-corrected value simply displays through, whether or not it would still be recomputed as `complete` from source.

---

## 6. Identity sources across every artifact

| Artifact | Identity source | Value at completion time | Touched by the corruption? |
|---|---|---|---|
| Certified `PhaseReport` object (`report.phase_id`) | `cli_phase_id` (`--phase-id 135D`), resolved before the active-task/metadata fallback chain per `run_phase_metadata_repair`'s own docstring precedence note | `135D` | No |
| `.pcae/phase-reports/20260712-202757-135D.md/json` (promoted terminal report) | Serialized from the certified `PhaseReport` object above | `135D` | No |
| `.pcae/phase-reports/latest.md` / `latest.json` (mutable pointer) | Copied atomically from the same promotion call as the terminal report | `135D` / `135D` — mutually consistent, identical mtime (22:27:57) | No |
| `.pcae/phase-reports/.last-notified.json` (marker) | Bound from the promoted report's own identity + digests at dispatch time | `135D`, bound 22:27, before the corruption | No |
| Finalization receipt | N/A — none created for this `--allow-partial-report` dispatch (pre-existing gap, unrelated) | N/A | N/A |
| Checkpoint / immutable snapshot | N/A — `run_finalization_transaction()` is structurally skipped whenever `--allow-partial-report` is passed (`src/pcae/commands/phase.py:488`) | N/A | N/A |
| `.pcae/phase-completion-metadata.json` | Hand-authored by me | `135D` → corrupted to `135A` at 22:28:15 → reverted to `135D` at 22:29:26 | **Yes — the only artifact touched** |
| `.pcae/phase-completion-report.md` | Hand-authored (skipped for 135B/135C/135D) | `135A` (stale) — **still true right now** | No (was already wrong before the incident; the incident read it, didn't write it) |
| Telegram delivery payload | `phase_report_to_notification_event()`, `src/pcae/core/notifications.py:411`, builds `metadata["phase_id"]` directly from the in-memory certified `report.phase_id` | `135D` | No — dispatched at 22:27:57, before the corruption existed |

---

## 7. Telegram identity source

`phase_report_to_notification_event(report, ...)` constructs the notification event's `metadata["phase_id"]` directly from `report.phase_id` — the same in-memory, certified `PhaseReport` object used throughout the finalization gate, never re-read from `.pcae/phase-completion-report.md`, `.pcae/phase-completion-metadata.json`, or Architecture Status at send time. **Telegram correctly used certified phase identity 135D** — this was not a coincidence of some separate, independently-correct CLI/current-task source; it is the same identity value the entire finalization pipeline certified against, sourced from the explicit `--phase-id 135D` CLI argument I supplied, read once at report-construction time, well before the later, unrelated metadata-repair corruption occurred.

---

## 8. Override-policy challenge: does `--allow-partial-report` ever permit overriding a phase-identity mismatch?

Traced `validate_phase_report_transition()` (`src/pcae/core/repository_transition_integration.py:26`) and `_check_metadata_consistency()`/the `phase_identity_consistency` check (`src/pcae/core/repository_transition_validator.py`):

- `allow_partial_report` has **exactly one effect** on the `RepositoryState` fed into the transition validator: `report_completeness = "complete" if allow_partial_report else trial_report.report_completeness` (line 51). It spoofs the *completeness* field only.
- `metadata_phase_id`, `phase_id`, and `requested_phase_id` — every identity-bearing field — are read honestly and **never modified by the override flag**, anywhere in the call chain.
- `_check_metadata_consistency()` and the `phase_identity_consistency` check both operate purely on these untouched identity fields and are marked `"blocking"` unconditionally in `repository_transition_validator.py` — nothing in their implementation consults `allow_partial_report`.

**Empirical confirmation**: during this session's own earlier retries (before `PROJECT_STATUS.md`/metadata were corrected to 135D), the transition validator genuinely **rejected** with `Violation: phase_identity_consistency - Disagreeing phase identity sources: ['135C', '135D']` — and this occurred independent of whether `--allow-partial-report` was passed, because that flag structurally cannot reach this check.

**Conclusion, directly answering the assignment's item 8**: `--allow-partial-report` is **not** permitted to override a genuine phase-identity disagreement between the certified report and metadata, and — as designed today — **structurally cannot**, regardless of operator intent. It is scoped narrowly to the evidence-completeness/trust-quality dimension (the two legacy "95M.1 gate"/"105D trust gate" schemas, plus the single `report_completeness` field fed to the transition validator). Phase-identity disagreement is already, correctly, presumptively unoverrideable in the current implementation — consistent with CLTR-001's own Blocking-severity, no-override treatment of `CLTR-ID-1`/`CLTR-ID-2`/`CLTR-AUTH-1` (135D's own architecture document, §11), even though CLTR-001 itself has no production implementation yet. **No repair is required on this specific point** — it is already correctly enforced. This is a materially different, and better, finding than the assignment's framing anticipated ("presumptively unoverridable unless a contract says otherwise") — the code already meets that bar today, independent of CLTR-001.

One adjacent, narrower, genuine finding: spoofing `report_completeness` unconditionally to `"complete"` when `--allow-partial-report` is passed means the transition validator's own `_check_report_completeness()` invariant can **never** independently fire once the flag is used — the flag doesn't just permit an operator override at the CLI-output level (which is honestly disclosed via the printed "`--allow-partial-report`: phase completion proceeds despite blockers" lines), it also erases the underlying evidence-completeness fact from the separate transition-validator's own evaluation, rather than passing through an honest "overridden" state for that validator to reason about on its own terms. This is a real, if narrow, design conflation — worth flagging, not blocking.

---

## 9. Mixed-generation `latest.md`/`latest.json` hypothesis — tested, rejected

Per the assignment's explicit instruction not to assume this and to test it directly:

```
$ head -3 .pcae/phase-reports/latest.md → Phase ID: 135D
$ python3 -c "...json.load(open('latest.json'))['phase_id']" → 135D
$ stat .pcae/phase-reports/latest.md .pcae/phase-reports/latest.json
  .pcae/phase-reports/latest.md    Jul 12 22:27:57 2026
  .pcae/phase-reports/latest.json  Jul 12 22:27:57 2026
```

Both files agree exactly on phase identity and share an identical mtime to the second. **No mixed-generation defect is present in this incident.** The general structural gap this track has repeatedly disclosed (Gap B: `canonical_artifact_promotion.py`'s three non-atomic `write_text()` sites, unrelated to this reporting pipeline entirely — a *different* promotion mechanism for governed *artifacts*, not phase reports) remains a real, separately-tracked, unrepaired risk, but it did not manifest here and is not the cause of anything in this incident.

---

## 10. Classification

**A. Certified 135D evidence is internally correct; only terminal report derivation is corrupted.**

Refined precisely: "corrupted" here means the terminal report's own self-assessed **trust/completeness derivation** (a metadata-quality judgment, computed by comparing against a stale, unrelated, hand-maintained file) is degraded to `partial` — not that any certified identity, content, or substantive evidence is wrong. Specifically:

- The certified `PhaseReport`, the promoted `latest.md`/`latest.json`, the marker, and the Telegram delivery all correctly and exclusively identify phase 135D, both then and now (§6, §7).
- No checkpoint or immutable snapshot was ever engaged (§4) — nothing to corrupt at that layer.
- No receipt was created — a separate, pre-existing, unrelated gap, not corruption.
- The only artifact actually touched by the erroneous rewrite, `.pcae/phase-completion-metadata.json`, was corrected within ~71 seconds and the correction is durably committed and pushed (§1).
- The `partial`/`metadata_consistency` flag on the already-promoted report is a genuine, still-live, but narrow and separate defect: `.pcae/phase-completion-report.md` was never updated past 135A across three phases (135B, 135C, 135D) — a documentation-currency gap in the *derivation input*, not corruption of the *certified evidence* itself.

**B is not chosen**: the promoted report's substantive content, identity, and every certified fact are valid; nothing requires supersession by a new corrective transition. **C is conclusively ruled out**: 135A never entered certification or promotion at any point (§4's timing proof). **D is not chosen**: the evidence chain above is complete and internally consistent across every artifact and code path checked.

---

## 11. Smallest justified repair

Evaluated against the assignment's candidate list, keeping only what the evidence actually proves is needed:

| Candidate | Justified? | Disposition |
|---|---|---|
| Prohibit Architecture Status titles/grouping labels from serving as phase identity authority | **No** — Architecture Status was never the source (§2, §3). Not implemented; would address a defect that did not occur. |
| Require metadata repair to use explicit canonical phase identity only | **Partially** — the tool already reads an explicit, tracked file by design; the actual gap is that the file can silently go stale with no detection. Implemented in a targeted form below. |
| Prevent repair from replacing an explicit valid phase ID with a derived value | **Yes, narrowly** — implemented via a staleness guard (below), not a blanket prohibition on the tool's core function. |
| Make report/metadata phase mismatch an unoverridable blocker | **Already true** (§8) — no change needed. |
| Regenerate terminal reporting only from the certified phase-bound artifact set | **No** — disproportionate; the fix is one stale input file, not a regeneration-policy change. |
| Preserve the original partial 135D report and explicitly supersede it | **No** — nothing about the promoted report is wrong; supersession would misrepresent a documentation-currency gap as a content defect. |

**Repair implemented, smallest-first:**

1. **Immediate data fix**: hand-author `.pcae/phase-completion-report.md` to reflect 135D's actual completion (title, identity, summary), closing the specific staleness that caused this incident and that has been live since 135A.
2. **Structural guard**: add a staleness check to `run_phase_metadata_repair()` — refuse (fail closed, no mutation, clear message) rather than blindly overwrite when the canonical report's parsed `phase_id` does not match the phase_id declared in `PROJECT_STATUS.md`'s own "Current Phase" section (the one file every phase in this track's history has reliably kept current, unlike `.pcae/phase-completion-report.md`). This directly targets the proven defect class — "a stale ground-truth file with no recency check" — without touching the already-correctly-enforced identity invariants (§8) or any unrelated mechanism.
