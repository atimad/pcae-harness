# Phase 105B — Phase Report Trust Gate CLI / Finalization Integration

## Purpose

Phase 105A implemented `validate_phase_report_trust` and
`select_active_phase_report` in `src/pcae/core/phase_report_trust.py`: pure,
non-executing validation logic that classifies a phase completion report as
`complete` / `partial` / `invalid`, based on 8 required report fields, 5
required governance fields, 3 required test fields, and 4 disallowed
placeholder values (`TBD`, `pending`, `not captured`, `unknown`). That
validator was implemented but not reachable from any CLI surface or the
phase-completion lifecycle.

Phase 105B makes the validator **reachable**: a CLI command to run it
on-demand, and a warning-only hook into `pcae phase complete` so completing
phases surface a trust signal automatically.

## Scope

- Add `pcae phase-report trust` — validates a phase report's trust
  completeness from CLI, in human or JSON form.
- Add `--trust` to `pcae phase-report show` to include the same assessment
  inline with the existing report view.
- Add a normalization layer (`adapt_report_for_trust_check`) that reconciles
  the field-name and shape differences between the report schemas below.
- Surface an advisory (non-blocking) trust line during `pcae phase complete`.

## Non-goals

105B does not implement runtime enforcement, execution, backend invocation,
adapter execution, shell mediation, Telegram inbound/polling, apply/commit/push
authorization, an execution enablement flag or toggle, cryptographic signing,
remote attestation, database-backed audit storage, or rollback execution. The
trust gate remains non-executing and non-authorizing. All authorization flags
remain False; `simulation_only`, `no_execution`, `evidence_only`,
`non_authorizing`, and `design_only` remain True where applicable.

## Relationship to the 105A validator, and a documented schema gap

This codebase already had, prior to 105A, an independent and *already wired*
report-trust model in `src/pcae/core/phase_reports.py`
(`PhaseReport.assess_completeness()` / `apply_trust_assessment()`, and the
Phase 95M.1 hard-fail `validate_finalization_gate()`, which today already
blocks `pcae phase complete` for reports it considers incomplete). 105A's
`phase_report_trust.py` module defines a second, overlapping trust model with
different field names and shapes:

| Concept | `phase_reports.py` (pre-105A, wired) | `phase_report_trust.py` (105A) |
|---|---|---|
| push field | `pushed_status` | `pushed` |
| files changed | `files_changed` (int) | `files_changed` (any non-placeholder) |
| commits | `commits` (list) / `metadata["phase_commits"]` | `commits` |
| governance results | dict | dict (list-of-record also seen in `.pcae/phase-completion-metadata.json`) |
| placeholder rejection | not checked (presence only) | `TBD`/`pending`/`not captured`/`unknown` rejected |

Because of this, 105B does **not** replace or hard-gate on top of the
95M.1 gate — doing so with a second, differently-shaped schema at the same
call site risked spurious hard blocks on legitimate completions (the
pre-completion metadata draft, for instance, never carries `status`/`summary`,
since those are supplied separately as `pcae phase complete --summary`
arguments). `adapt_report_for_trust_check()` reconciles the two schemas
(`pushed_status`→`pushed`, `files_changed_count`→`files_changed`,
`phase_commits`→`commits`, governance/test result lists→mappings) so the
105A validator can read either shape, but the two trust systems remain
functionally distinct. Reconciling them into one model is out of scope here
and is flagged as a residual risk below.

## CLI command

```
pcae phase-report trust [--metadata PATH] [--report PATH] [--phase-id ID]
                         [--reports-dir DIR] [--json]
```

### Options

- `--metadata PATH` — validate a specific structured metadata JSON file
  directly (e.g. a `.pcae/phase-completion-metadata.json`-shaped file).
- `--report PATH` — validate a specific report file. JSON is supported the
  same way as `--metadata`. Markdown is **not** parsed — passing a `.md`
  report returns a clear `unsupported_report_format` message (exit 2), not a
  silent pass, since no Markdown trust parser exists.
- `--phase-id ID` — scope selection to a specific phase. When given without
  `--metadata`/`--report`, scans `.pcae/phase-reports/*.json` for all records
  matching that phase and applies 105A's `select_active_phase_report`
  (complete beats partial for the same phase; a partial-only history reports
  `can_be_active_latest: false` and `repair_required: true`).
- `--reports-dir DIR` — override the default `.pcae/phase-reports` directory.
- `--json` — machine-readable output.

### Default (no flags) behavior — "the latest canonical report"

1. Read `.pcae/phase-reports/latest.json` if it exists (the canonical,
   already-finalized `PhaseReport` artifact) — this is a single record, not
   a cross-phase selection, so it always answers "what is the latest report",
   not "what is the most complete report across all history".
2. If absent, fall back to `.pcae/phase-completion-metadata.json` (the
   pre-completion draft) and add a `note` explaining that `status`/`summary`
   are expected to be missing from that source until `pcae phase complete`
   runs — this is documented, not hidden, behavior.
3. If neither exists, return a clear `trust_check_failed` error (exit 2).

## JSON output

```json
{
  "complete": true,
  "status": "complete",
  "missing_fields": [],
  "placeholder_fields": [],
  "empty_fields": [],
  "warnings": ["No missing or placeholder fields detected."],
  "repair_required": false,
  "can_be_active_latest": true,
  "summary": "Report is COMPLETE. All trust fields present.",
  "phase_id": "105A",
  "source": "canonical latest report: .pcae/phase-reports/latest.json"
}
```

`note` is added only when the source is a pre-completion metadata draft.

## Human output

Reports phase ID, source, status (complete/partial/invalid), complete flag,
repair_required, can_be_active_latest, missing/placeholder fields, any
warnings, and the summary line. When not complete, a "Repair guidance"
section lists each missing field and placeholder to fix, and states plainly
that the report cannot be trusted as active/latest until repaired.

## Exit code behavior

- `0` — report is complete.
- `1` — report is partial or invalid (validation ran, trust failed).
- `2` — usage/IO error (file not found, invalid JSON, unsupported Markdown
  report, no report found for a `--phase-id` filter). Distinguished from `1`
  so automation can tell "the check ran and failed" apart from "the check
  could not run".

## `pcae phase-report show --trust`

Existing `pcae phase-report show` output (Markdown or JSON) is unchanged by
default. Passing `--trust` appends a `## Trust Gate (Phase 105B)` section (or
a `trust` key in JSON) with the same status/complete/can_be_active_latest/
missing/placeholder fields, computed from the currently-displayed report.

## Finalization integration status: **warning-only, CLI-adjacent**

`pcae phase complete` already runs the pre-existing 95M.1
`validate_finalization_gate()` hard gate (unchanged by this phase). 105B adds
one line after that gate passes:

```
Trust gate (105B, advisory): complete
```

or, for a partial report:

```
Trust gate (105B, advisory): partial
  Report is PARTIAL: 1 placeholder(s). Repair required.
```

This is **advisory only** — it never blocks `pcae phase complete`, and it
does not mutate the report. **Hard-fail finalization enforcement using the
105A/105B trust model is deferred to Phase 105C**, pending the schema
reconciliation noted above (making this a second hard gate today would
introduce spurious blocks wherever the two schemas disagree, e.g. the
`pushed`/`pushed_status` and list/mapping differences documented in this
file).

## Repair guidance behavior

Both the CLI (`_print_trust_human` / JSON `missing_fields`+`placeholder_fields`)
and `phase complete`'s advisory line reuse the exact same
`PhaseReportTrustResult` produced by 105A's `validate_phase_report_trust` — no
separate repair-guidance logic was introduced, so guidance text cannot drift
from the underlying validator.

## Residual risks

1. Two independent, overlapping trust-completeness models exist in this
   codebase (95M.1's `assess_completeness`/`validate_finalization_gate`, and
   105A/105B's `validate_phase_report_trust`). They agree in spirit but not
   in field names, and only one is hard-gating. Reconciling them is
   substantial surgery and out of scope for 105B; flagged for a future
   design phase.
2. `adapt_report_for_trust_check()` is a best-effort field-name/shape bridge,
   not a schema migration — it does not fabricate `status`/`summary` when a
   pre-completion metadata draft lacks them, so validating a draft directly
   will correctly, and expectedly, show those as missing.
3. `pcae phase-report trust --phase-id ID` scans all JSON files under the
   reports directory; this is fine at current phase-report volumes but is
   an O(n) directory scan, not an index.

## Recommended next phase

105C — Phase Report Trust Gate Finalization Hard-Fail / Push-Check
Integration. Should decide whether/how to reconcile the two trust schemas
before making the 105A/105B trust gate a second hard-fail finalization gate.
