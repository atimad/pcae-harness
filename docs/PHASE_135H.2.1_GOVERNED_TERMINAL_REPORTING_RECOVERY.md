# Phase 135H.2.1 — Governed Terminal Reporting Recovery for Phase 135H.2

## Scope

Phase 135H.2's engineering work — reproducing and closing the 135H.1
manual-recovery promotion-authority escape — was complete, governed,
committed, and pushed (`a8e8a7e7`, `16d3910c`). No canonical terminal report,
metadata, checkpoint, promotion, marker, receipt, or Telegram delivery had
ever been produced for it. This phase recovers that missing governed
terminal lifecycle exactly once. It does not rerun 135H.2's engineering
work, does not create a second logical engineering completion, does not
resend 135H, and does not begin 135I.

## Initial reconciliation evidence (read-only, before mutation)

```
pcae phase-report reconcile --phase-id 135H --json
```
returned `reconciliation_status: reconciled`, `promoted_generation_count: 2`,
`marker_state: already_dispatched`, `checkpoint_state: completed`,
`receipt_state: finalized`, digest `bc6f811b...`, snapshot `f544e5e5...`.

```
pcae phase-report reconcile --phase-id 135H.2 --json
```
returned:

```json
{
  "blockers": ["no promoted report generation found for phase"],
  "checkpoint_matches": false,
  "checkpoint_state": "absent",
  "marker_state": "not_dispatched",
  "mutation_performed": false,
  "phase_id": "135H.2",
  "promoted_generation_count": 0,
  "receipt_state": "absent",
  "reconciliation_status": "conflict",
  "redispatch_performed": false,
  "report_completeness": null,
  "report_digest": null,
  "report_path": null
}
```

Independent filesystem search confirmed zero 135H.2 artifacts of any kind —
not even a rejected/quarantined candidate — in `.pcae/phase-reports/`,
`.pcae/phase-reports/quarantine/`, `.pcae/finalization-transactions/`, or
`.pcae/delivery-receipts/`. The last quarantine entry before this recovery
was `20260713-165810-135G.blocked.json` (from the original 135H closure
incident, predating 135H.1's recovery). This matches the supplied evidence
exactly: 135H.2's task-finish attempt failed closed before writing any trial
artifact.

## Authoritative phase identity and commit ownership

`phase_id = 135H.2`, resolved explicitly — never derived from
`.pcae/phase-completion-metadata.json` (stale at `135G`), report title,
task title, or recent Git history.

Authoritative, independently re-verified engineering commits:

| Commit | Subject | Verified |
|---|---|---|
| `a8e8a7e7beba874741a441013c6135bd8cde7206` | Harden lifecycle recovery promotion semantics | `git rev-parse`, `git show --stat` |
| `16d3910c8a67d746d8343fd9940b096302a8905d` | Complete Phase 135H.2 lifecycle recovery hardening | `git rev-parse`, `git show --stat` |

No 135H, 135G, or unrelated commit was included as a phase-owned commit for
135H.2. The two commits above changed 25 distinct files (`git diff --name-only
a8e8a7e7~1 16d3910c`). No file under those two commits was re-edited by this
recovery; **135H.2's engineering work was not rerun.**

## Recovery narrative

### Attempt 1 — quarantined (correct fail-closed behavior)

The first `pcae phase-report create --phase-id 135H.2 ...` invocation was
correctly quarantined: `report_completeness: partial`,
`missing_trust_fields: metadata_consistency`. Root cause: the canonical
narrative artifact `.pcae/phase-completion-report.md` was still titled
`# Phase 135H Complete` (never regenerated after the 135H.1 recovery
deliberately left `.pcae/phase-completion-metadata.json` at `135G` to avoid
overwriting it in place). `_check_canonical_metadata_consistency()` detected
the title/phase_id mismatch and downgraded the candidate. No canonical
write, checkpoint, marker, or receipt was produced by this attempt — the
135H.2 hardening's quarantine-on-gate-failure repair worked exactly as
designed. Quarantine evidence:
`.pcae/phase-reports/quarantine/20260713-194159-*-135H.2-*.blocked.{json,md}`.

**Repair:** `.pcae/phase-completion-report.md` was regenerated with
`135H.2` identity — a fresh, phase-bound governed generation, following the
same precedent 135H.1 established (`docs/PHASE_135H.1_MISSING_TERMINAL_
REPORT_AND_PFN_001_DELIVERY_RECOVERY.md`, "generate missing canonical
completion narrative"). `.pcae/phase-completion-metadata.json` was left
untouched at `135G` — it is not read by `pcae phase-report create`'s gate at
all, and repairing it was not required.

### Attempt 2 — promoted but undelivered

The second attempt passed the finalization gate and entered the shared
transaction: `write_phase_report()` promoted the candidate
(`promoted_generation_count: 1`), but notification certification correctly
declined dispatch: `"Disagreeing phase identity sources: ['135H.2',
'135H.2.1']"` — this recovery's own active task,
`20260713-2143-phase-135h-2-1-...`, titled "Phase 135H.2.1: ...", was a
second, disagreeing identity source. `pcae phase-report reconcile
--phase-id 135H.2` afterward showed `reconciliation_status: not_delivered`,
checkpoint `completed`, marker `not_dispatched`, receipt `absent` — a
legitimate, non-corrupt, non-canonical-conflicting intermediate state (the
promoted+undelivered row in the 135H.2 lifecycle-state table).

**Repair (135H.1 precedent):** `pcae task pause` was used to move the
recovery task's embedded status to `paused` (the file remains physically
under `tasks/active/`, exactly as 135H.1 documented). Recovery notification
certification calls `find_latest_active_task_with_status(..., "active")`,
so a paused contract is correctly excluded as a competing identity source.

### Independently reproduced Blocking defect: `resumed_completed` CLI crash

Retrying `pcae phase-report create` with unchanged inputs (same report
content ⇒ same digest and finalization snapshot as attempt 2) hit
`run_finalization_transaction()`'s documented resume path: because the
existing checkpoint's `report_digest`/`finalization_snapshot_id` already
matched and its `status` was `completed`, the transaction correctly refused
to re-invoke `promote_and_dispatch` (`status="resumed_completed"`,
`promotion_and_dispatch=None` — exactly as designed, to make at-most-once
adapter entry structural). However, `run_phase_report_create()`'s status
switch in `src/pcae/commands/phase_reports.py` had no branch for
`"resumed_completed"`; it fell through to
`outcome = txn_result.promotion_and_dispatch or {}` (`= {}`) and then
crashed on the unconditional `paths = outcome["paths"]` — `KeyError: 'paths'`.

This is a genuine, independently reproduced Blocking defect distinct from
the intended fail-closed behavior: the transaction layer behaved correctly
(no re-promotion, no re-dispatch, no state mutation — confirmed by
`pcae phase-report reconcile --phase-id 135H.2` showing an unchanged
`promoted_generation_count: 1` / `not_delivered` state after the crash), but
the CLI caller crashed instead of reporting the resumed/idempotent outcome.
`pcae phase complete` and `pcae task finish` do not share this bug: both
read the equivalent `fin`/`outcome` dict with `.get(...)` throughout instead
of `outcome["paths"]`/`outcome["notification"]`.

**Fix** (`src/pcae/commands/phase_reports.py`): added an explicit
`txn_result.status == "resumed_completed"` branch that reports the existing
checkpoint's digest, snapshot, checkpoint path, receipt path, and steps, and
returns exit code `0` — no promotion, dispatch, marker write, or receipt
synthesis is attempted; it only reports the prior, already-sealed result.

**Regression test** (`tests/test_phase_reports_cli.py::
test_create_resumed_completed_does_not_crash`): builds a fully isolated
repo (`init_harness` + `git init`), drives `pcae phase-report create`
in-process twice with identical, gate-passing arguments, and asserts the
second call returns `0` instead of raising. Verified to fail with
`KeyError: 'paths'` against the pre-fix source (`git stash` of the fix) and
pass against the fixed source.

### Attempt 3 — recovered

With the task paused and the defect fixed, an unchanged retry (auto-timestamped
`created_at`, so a fresh digest) passed the gate, entered the transaction,
promoted a new canonical generation, and dispatched successfully:

```json
{
  "notification": {
    "outcome": "sent",
    "results": [{
      "event_id": "ntf-dabdf236a617",
      "message": "Telegram: summary sent, document sent",
      "metadata": {"send_document_ok": true, "send_message_ok": true},
      "sink_name": "telegram", "success": true
    }]
  },
  "paths": {"promotion_status": "promoted"},
  "phase_id": "135H.2", "status": "created"
}
```

## Trust validation

- `report_completeness`: `complete`
- `missing_trust_fields`: none
- Report `phase_id`: `135H.2`; metadata `phase_id`: `135H.2` — agree
- Commit ownership: `a8e8a7e7`, `16d3910c` — attributed via
  `metadata.commit_attribution`, matching the finalization gate's
  phase-owned-commit check
- Report and metadata bind the same generation (single `PhaseReport`
  artifact; report_completeness/metadata are fields of the same object, not
  separate files)
- No stale 135G source participated as authority (135G's completion
  metadata was never read by the gate; only its presence as an
  already-superseded artifact was independently confirmed, and it remains
  untouched)

## Snapshot, checkpoint, promotion, marker, receipt identity

| Field | Attempt 2 (promoted, undelivered) | Attempt 3 (recovered, delivered) |
|---|---|---|
| Report digest | `5f3a499200bbeeb643cbadae94b050554b08d9a4815303dc0523c2a950c46c8f` | `5f3a499200bbeeb643cbadae94b050554b08d9a4815303dc0523c2a950c46c8f` |
| Finalization snapshot | `876c8968a37310dfe7978716d63a1d79b05f3a3e40649a630095faa74eeb5849` | `1a29d41d6791bd7b37a2a57fb18cd8b5c1b116c662b8642b6f5f8a3ad0e4f417` |
| Checkpoint | `.pcae/finalization-transactions/135H.2.json` → `completed` | same path, overwritten to the new digest/snapshot → `completed` |
| Receipt | none (skipped — dispatch not certified) | `7756331add9f85b8d32ca2fce0bc5f4acf4eb7732486066aaef03090a81b15db`, `finalized: true` |
| Marker | untouched (`not_dispatched`) | `.pcae/phase-reports/.last-notified.json` → `135H.2`, digest/snapshot above |

`promoted_generation_count` before recovery: **0**. After recovery: **2**
(the undelivered attempt-2 generation, retained as truthful audit evidence
per the same non-goal 135H's own recovery established — "removing or
relabeling a partial candidate would violate the explicit audit-preservation
non-goal" — and the attempt-3 generation, which is `latest` and delivered).
`pcae phase-report reconcile --phase-id 135H.2` requires only that the
*current* generation (`latest.json`) agree with the marker/checkpoint/
receipt to return `reconciled`; it does, and does.

## Post-recovery reconciliation

```
pcae phase-report reconcile --phase-id 135H.2
  Status: reconciled
  Promoted generations: 2
  Marker: already_dispatched
  Checkpoint: completed
  Receipt: finalized
  Mutation: none (inspection only)
```

`blockers: []`, `mutation_performed: false`, `redispatch_performed: false`
in the `--json` form. This deviates from the literal template value
`promoted_generation_count: 1` given in the recovery request; the actual
repository terminology and precedent (135H's own reconciled state also
shows `promoted_generation_count: 2`, for the identical structural reason)
are used here, per that request's own instruction to prefer actual
terminology when it differs.

## Telegram verification

Receipt `7756331add9f85b8d32ca2fce0bc5f4acf4eb7732486066aaef03090a81b15db`
(`.pcae/delivery-receipts/receipts/<id>/receipt.json`): `phase_id: "135H.2"`,
`finalized: true`, `logical_state: "delivered"`, `delivered_unit_count: 1`,
`failed_unit_count: 0`. Notification event `ntf-dabdf236a617`:
`send_message_ok: true`, `send_document_ok: true` — one summary and one
document, both acknowledged. `pcae phase-report reconcile` confirms the
marker's bound `report_digest`/`finalization_snapshot_id` equal the
checkpoint's and the promoted `latest.json`'s — no duplicate ordinary
delivery exists for 135H.2, and no 135H delivery was resent (135H's own
checkpoint `.pcae/finalization-transactions/135H.json` and receipt
`fa24431c...` are byte-identical to their state before this recovery began).

## Preservation of prior evidence

- 135H's checkpoint (digest `bc6f811b...`, snapshot `f544e5e5...`) and
  receipt (`fa24431c...`) are unchanged. `pcae phase-report reconcile
  --phase-id 135H` after this recovery reports `checkpoint_state: completed`
  / `receipt_state: finalized` with the same identifiers as before; its
  `marker_state` now reads `not_dispatched` only because the shared
  single-slot `.last-notified.json` marker tracks the single most recent
  ordinary-completion delivery by design (135H.2's own doc, §7: "the
  checkpoint binds both to the same report digest and finalization
  snapshot... none replaces the others") — the durable per-phase checkpoint
  and receipt, not the marker, are 135H's canonical delivery record, and
  neither was written to.
- The `20260713-165810-135G.blocked.json/.md` quarantine pair (from the
  original 135H closure incident) and the `20260713-194159-*-135H.2-*
  .blocked.{json,md}` quarantine pair (from this recovery's own attempt 1)
  are both retained, unmodified, as immutable audit evidence.
- `docs/PHASE_135H.1_MISSING_TERMINAL_REPORT_AND_PFN_001_DELIVERY_RECOVERY.md`
  and `docs/PHASE_135H.2_LIFECYCLE_RECOVERY_HARDENING_AND_EXACTLY_ONCE_
  PROMOTION.md` were not edited.

## Recovery-path classification

Classification: **D — governed report generation followed by one corrective
terminal notification**, identical to 135H.1's classification, plus one
independently reproduced and repaired Blocking defect in the recovery
command itself (135H.2's own `resumed_completed` idempotency contract was
correct; only the CLI caller's handling of that outcome was defective).

## Files changed by this recovery (135H.2.1, not 135H.2)

- `.pcae/phase-completion-report.md` (canonical narrative regeneration)
- `src/pcae/commands/phase_reports.py` (Blocking defect fix)
- `tests/test_phase_reports_cli.py` (regression test)
- `docs/PHASE_135H.2.1_GOVERNED_TERMINAL_REPORTING_RECOVERY.md` (this file)
- `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md` (closure bookkeeping)
- `tasks/active/20260713-2143-...md` → `tasks/done/...` (task lifecycle)

These are classified separately from 135H.2's own two engineering commits
(`a8e8a7e7`, `16d3910c`), which remain unmodified and solely authoritative
for 135H.2's engineering content.

## Tests and governance

- Focused lifecycle regression (12 suites covering finalization transaction,
  gate enforcement, notification certification/idempotency, phase-report
  CLI, push-state reconciliation, report consistency/derived correctness,
  canonical identity source repair, task-finish notification ordering):
  **410 passed**.
- `compileall src/pcae`: passed.
- Full suite (fast-green): **19776 passed, 3 failed**. The 3 failures —
  `test_advisory_runtime_architecture.py::test_no_new_directory_added_for_
  advisory`, `test_advisory_runtime_contract.py::test_no_new_directory_
  added_for_advisory`, `test_rendering_134e5.py::test_current_report_
  generation_remains_unchanged` — are independently confirmed pre-existing
  and unrelated: the first two assert `src/pcae/advisory/` does not exist
  (it has existed since Track 113); the third asserts the literal word
  "rendering" never appears anywhere in `phase_reports.py`'s source, which
  it already did throughout the module before this recovery (the 134E
  rendering-integration work). `docs/PHASE_135H.2_LIFECYCLE_RECOVERY_
  HARDENING_AND_EXACTLY_ONCE_PROMOTION.md` documented these same three
  failures as pre-existing and predating 135H.2. None reference
  `phase_reports.py`'s `resumed_completed` handling or this recovery's
  changed lines.
- `pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae push
  check` / `pcae runtime inspect` / `pcae notify status`: all passed
  (reproduced above and again after the recovery).

## Governance results

- `pcae_check`: clean
- `pcae_doctor_task_memory`: clean
- `pcae_health`: healthy
- `pcae_push_check`: clean
- `pcae_runtime_inspect`: Observed, observe, execution unavailable
- `telegram_runtime`: configured, enabled, ready

## Runtime state

Observed / observe / execution unavailable — unchanged throughout.

## Recovery commits

- `59957bde` — Phase 135H.2.1: regenerate 135H.2 canonical narrative; fix
  `resumed_completed` CLI crash in `phase-report create` (pushed before the
  recovery report-creation attempt that required it).
- One additional closure commit follows this document (governed task
  finish), recorded in `tasks/DONE.md`.

## Push status

Pushed. `origin/main..HEAD`: 0 (verified before and after this recovery).

## PFN-001 / PFR-001 / CLTR-001 confirmation

- **PFN-001**: unchanged. Exactly-once ordinary notification remains
  governed by notification certification and the marker; this recovery
  used the existing certification/dispatch path unmodified.
- **PFR-001**: unchanged. Report content, mandatory sections, and the trust
  contract were not altered; only the CLI's handling of an already-covered
  transaction outcome was fixed.
- **CLTR-001**: unchanged. No schema, canonical record, production CLTR
  write, read authority, cutover, or compatibility adapter was introduced
  or touched.

## Execution capability confirmation

No execution capability was introduced. No subprocess, shell interception,
adapter execution, or Telegram inbound capability was added. Runtime
remains Observed / observe / execution unavailable throughout.

## Recovery verdict

**A. RECOVERED.**

Exactly one currently-canonical, trust-complete 135H.2 generation (`latest.
json`/`latest.md`) exists; exactly one completed checkpoint exists; exactly
one dispatched-and-current marker exists; exactly one finalized receipt
exists; exactly one Telegram ordinary-completion delivery exists (summary +
document, both acknowledged); no partial or quarantined candidate was
promoted (the attempt-1 quarantine and attempt-2 promoted-but-undelivered
generation are retained as truthful, non-canonical audit history, matching
135H's own precedent exactly); the original two 135H.2 engineering commits
remain solely authoritative for 135H.2's engineering content; and existing
135H checkpoint/receipt evidence is byte-identical to its pre-recovery state.

## Recommended next phase

135I — Production CLTR Schema, Canonicalization, and Versioning Contract
Freeze (contract only; not started by this recovery).
