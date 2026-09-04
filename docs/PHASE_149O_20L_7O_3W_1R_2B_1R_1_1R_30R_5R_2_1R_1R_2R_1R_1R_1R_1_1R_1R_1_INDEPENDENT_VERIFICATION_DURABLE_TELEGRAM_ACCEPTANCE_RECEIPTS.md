# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1 — Independent Verification of Durable Telegram Acceptance Receipts and Phase-Completion Notification Auditability

## Scope

Verification-only. Independently adjudicates whether the predecessor
repair phase (`...1.1R`, commits `a0225cf8`/`08bfdc12`/`8bfce890`/
`cc4e8364`/`fbcaa519`) correctly repaired the historical defect in
which real Telegram API responses were consumed in-process but their
durable evidence (`message_id`, raw response, per-operation outcome)
was discarded, making it impossible to audit after process exit
whether a phase-completion Telegram send was actually accepted. No
production repair, no historical re-dispatch, no full-suite triage, no
F-5 continuation, no protected-root mutation, no human/YubiKey
ceremony performed in this phase.

## Lineage

- `N_ENTRY` (notification-repair phase-entry SHA, parent of `a0225cf8`) = `9c88f1a3`
- `N_CHANGE` (production repair commit) = `8bfce890`
- `N_FINAL` (notification-repair finalized endpoint) = `fbcaa519`
- `V` (this IV's phase-entry SHA) = `3d501880`
- Predecessor commit roles, independently re-derived from `git show
  --stat`: `a0225cf8` (task lifecycle open, no production content),
  `08bfdc12` (task-memory hygiene, unrelated deletion),
  `8bfce890` (the actual repair: `notifications.py` +341/-, `phase_reports.py`
  +39, `tests/conftest.py` +21, new predecessor test file +610,
  `CHANGELOG.md`, new doc), `cc4e8364` (`PROJECT_STATUS.md` only),
  `fbcaa519` (task lifecycle close, no production content).
- Whole-tree diff `N_ENTRY..N_FINAL` independently confirmed bounded to:
  `CHANGELOG.md`, `PROJECT_STATUS.md`, the predecessor's own doc,
  `src/pcae/core/notifications.py`, `src/pcae/core/phase_reports.py`,
  `tasks/DONE.md`, two task files, `tests/conftest.py`, the predecessor
  test file. No contract, schema, `pyproject.toml`, or dependency file
  changed. **No BLOCKING unrelated production change.**
- The separately recorded post-completion full-suite sweep
  (40587 passed / 979 failed / 117 errors) is preserved as frozen
  evidence attributed to its own baseline and is explicitly out of
  scope for this IV (see "Full-suite evidence preservation" below).

## Original defect, independently reproduced

Pre-repair `TelegramSink.send()` at `N_ENTRY`
(`src/pcae/core/notifications.py`, historical lines ~613-701) computed
`success = msg_result["ok"] and doc_result.get("ok", False)` and stored
only `{"send_message_ok": ..., "send_document_ok": ...}` in
`NotificationResult.metadata` — no `message_id`, no raw response, no
durable per-operation record. `.pcae/phase-reports/.last-notified.json`
(`phase_reports.py:937-1059`, unchanged by this repair) is confirmed
dedup-only — keyed on `phase_id`/`report_digest`/
`finalization_snapshot_id`, with no message_id/acceptance field, and is
written by CLI callers only after consulting `NotificationResult.success`.
This independently confirms the reported defect was real: PCAE could
consume a genuine Telegram API acceptance and then discard all durable
evidence of it.

## Current notification call graph, independently reconstructed

`finalize_phase_report` (`phase_reports.py:3722`, `dispatch(event, sinks)`)
→ `TelegramSink.send()` (`notifications.py:~803`) → for each of
summary/document: `_new_receipt_id()` → `_persist_receipt(_build_receipt(
status=PREPARED))` (durable atomic tmp-write + `os.replace`,
`notifications.py:100-148`) **before** → `_send_message()` /
`_send_document_bytes()` → HTTP call in `_api_call_form` /
`_api_call_multipart` (`notifications.py:~1254-1310`) → strict
`_classify_telegram_result()` (`notifications.py:330-357`: `ok:true`
requires an `int` `result.message_id`, else `OUTCOME_UNCERTAIN`) →
final `_persist_receipt()` overwriting the same `receipt_id` → the
per-operation status/message_id/receipt_id are exposed on
`NotificationResult.metadata` → `phase_reports._telegram_receipts_summary()`
(`phase_reports.py:768-792`) → `report.notification_result["telegram_receipts"]`
(`phase_reports.py:3757`) → persisted phase-report artifact.
`.last-notified.json` is untouched by any of this path.

## Dormant Delivery Receipt architecture — independently confirmed not bypassed

`src/pcae/core/delivery_pipeline.py` and `delivery_receipt.py` both
explicitly declare themselves "not yet active lifecycle authority."
Only registered adapters (`recording_v1`/`null_v1`) have
`represents_external_delivery=False` and are synthetic. Neither
`notifications.py` nor `phase_reports.py` imports either module
(grep-confirmed). Since no active, canonical, real-external-delivery
mechanism exists, the purpose-built Telegram receipt does not bypass
one — it is a legitimate bounded repair, not a duplication of
already-active machinery.

## Contract / digest independence

`compute_report_digest` (`phase_reports.py:1062-1073`) zeroes
`certified.notification_result = {}` before hashing, so
`telegram_receipts` (nested under `notification_result`) is excluded
from the certified digest. No circularity: each receipt's
`report_digest_prefix` is a sha256 of the raw canonical report markdown
captured at event-construction time — an input independent of
`compute_report_digest`'s own output. No frozen contract/schema file
was touched (confirmed by the bounded whole-tree diff above).

## Durability level — precisely characterized

`_atomic_write_json` (`notifications.py:100-106`) writes a sibling
`.{name}.tmp` file, then calls `os.replace()` (atomic rename on
POSIX). **No `fsync`** is called on the file or its containing
directory before or after the rename. This gives **process-exit /
restart-crash durability** (no partial/corrupt receipt file is ever
observable) but **not power-loss durability** (an OS-level crash
between the tmp write and the page-cache flush could still lose the
receipt). This is not a misrepresentation: the predecessor's own
report and code comments do not claim `fsync`-level/power-loss
durability, so the implementation matches its own claims. This is
recorded here for precision, non-blocking.

## Fresh independent IV suite

`tests/test_iv_telegram_receipt_fresh.py` (23 tests, independently
authored against a deterministic fake HTTP seam, not derived from the
predecessor's own test file) — **23/23 passed**. Covers: PREPARED
persisted before both summary and document network calls (verified by
reload from disk, not in-memory state); valid `ok:true`+`message_id` →
reloadable `API_ACCEPTED` with the exact message_id; `ok:true` with
missing/malformed `result`/`message_id` → `OUTCOME_UNCERTAIN`, never
accepted; explicit API rejection distinct from transport failure, with
receipt text never claiming "sent"/"accepted"/"delivered"; invalid
JSON never yields `API_ACCEPTED`; independent, non-colliding
summary/document receipts across accepted/rejected/transport-failed/
uncertain combinations, with the aggregate result never falsely
claiming complete two-operation success; PREPARED-then-hard-exception
leaves auditable non-accepted state; API-accepted-but-final-receipt-
write-failure does not crash the sink and is exposed as a persistence
failure rather than "safely resendable"; `PERSISTENCE-FAILURES.log`
and every receipt JSON file independently grepped byte-for-byte for
the bot token, `api.telegram.org/bot<token>`, and the raw chat_id —
absent in all cases, with a stable, non-reversible destination alias
used instead; `.last-notified.json` independently confirmed to carry
no message_id/acceptance field and to never be conflated with receipt
evidence; legacy (pre-repair-shape) phase reports load without
crashing and without fabricated message_id/status; no automatic retry
exists for uncertain or persistence-failure outcomes; a second
dispatch attempt is proven to allocate a new `receipt_id` rather than
overwrite the first attempt's evidence; terminology audit confirms
none of `human_delivered`/`delivered_to_human`/`human_received`/`read`/
`seen` are used to describe API acceptance.

Predecessor's own test file
(`tests/test_phase_149o_..._durable_telegram_notification_acceptance_receipts.py`),
run unchanged as regression evidence only (not as independent proof):
**41/41 passed**.

Targeted regression band (32 notification/telegram/phase-report/dedup/
finalization/completion-metadata test files, 1364 items): **1351
passed, 2 skipped, 11 failed**. All 11 failing node IDs independently
reproduced byte-for-byte at the fixed pre-repair baseline `N_ENTRY =
9c88f1a3` in a disposable detached worktree (`test_cltr_authority_136al`/
`136am`/`136ap`/`136aq`, `test_cltr_cutover_136t`/`136u`) — pre-existing
wheel/sdist packaging-authority guards unrelated to this repair.
**Zero attributable regression.**

## Non-blocking finding (F-1, this IV's own)

`NotificationResult.success` / `report.notification_result["success"]`
is still derived purely from raw Telegram `ok` booleans
(`notifications.py:948`; `phase_reports.py`'s `report_ok = all(r.success
...)`), not from the new strict `API_ACCEPTED`-requires-valid-
`message_id` classification. An `ok:true`-but-`OUTCOME_UNCERTAIN` send
(e.g. malformed `message_id`) therefore still reports `success: True`,
and a CLI caller (`phase.py:796-799`) would still write the
`.last-notified.json` dedup marker for it. This is disclosed and
explicitly scoped-out by the repair's own code comments ("never
replaces or redefines success ... preserved unchanged"), so it is a
real, reproducible gap between "durable audit evidence now exists" and
"the pre-existing success/dedup semantics were tightened to use it,"
but it does not contradict the repair's own stated claims. Recorded as
a candidate item for a future narrow follow-up; not repaired here.

## Historical facts preserved

- The affected configured-agent IV report
  (`...1.1R.1.1R.1` → i.e. the phase preceding this one's grandparent,
  `...1.1R.1`) remains byte-unchanged; no Telegram receipt was
  fabricated retroactively for it. Its original Telegram acceptance
  outcome remains: **NOT INDEPENDENTLY AUDITABLE FROM DURABLE PCAE
  EVIDENCE.**
- The human observing the predecessor repair's report in Telegram chat
  is preserved as contextual/observational evidence only, not as a
  machine-verifiable receipt for that phase.
- No historical re-dispatch was performed in this IV.

## Primary verdict

**DURABLE TELEGRAM ACCEPTANCE RECEIPT / PHASE-NOTIFICATION AUDITABILITY
REPAIR: INDEPENDENTLY VERIFIED.**

All 25 verdict conditions of the governing IV prompt are independently
satisfied: the original auditability defect is reproduced from
immutable pre-repair source; the production diff is bounded and fully
reconstructed; the purpose-built receipt architecture is justified
against the dormant Delivery Receipt mechanism; contract/digest
compatibility holds without circularity; PREPARED persistence is
proven (by disk reload, not static ordering) to precede both network
calls; the durability level is characterized precisely without
overclaiming; valid acceptance durably captures `message_id` and
survives reload; summary/document receipts are independent;
rejection/transport-failure/uncertain outcomes remain distinct;
malformed success is never treated as accepted; an accepted send
followed by a receipt-persistence failure is surfaced as a persistence
failure, not silently treated as safely resendable; no automatic retry
exists under uncertainty; dedup state remains separate from receipt
evidence; no secrets leak through any receipt or fallback log; legacy
reports remain loadable and uncorrupted; no historical fabrication
occurred; the affected historical IV remains non-auditable exactly as
before; API acceptance is never mislabeled as human delivery; the
receipt is evidence, not authority, over any phase/runtime/human
action; no contract, dependency, or unrelated production file changed;
F-5 execution remains on HOLD; and runtime authority is unchanged.

## Preserved state

- **F-5 CONTINUATION TECHNICAL PREREQUISITE: READY** (unchanged from
  predecessor phases; not re-verified here).
- **F-5 CONTINUATION EXECUTION: HOLD PENDING FULL-SUITE POST-COMPLETION
  TRIAGE.**
- **N-16-5: NOT CLOSED.** N-16-6/N-16-7 untouched.
- The historical full-suite sweep (40587 passed / 979 failed / 117
  errors) remains recorded as separate, frozen evidence at its own
  baseline; it was neither re-run, triaged, nor reattributed in this
  IV.
- Runtime: `Observed` / `observe` / execution `unavailable`, 0
  plugins, 0 capabilities. First governed runtime external effect
  remains absent/unreachable. This notification-auditability repair is
  disjoint from the governed runtime external-effect capability chain
  (no `adapter.dispatch`, `DispatchEnvelope`, plugin activation, or
  capability elevation involved).

## Recommended (not begun) successor

Post-Completion Full-Repository Test Sweep Failure/Error Attribution
and F-5 Hold Adjudication — must cluster and attribute the frozen
40587/979/117 evidence before any F-5 execution can resume. Its exact
CPIPC-valid ID is left for the operator to open explicitly; this phase
does not begin it, and does not re-dispatch the historical
`...1.1R.1` configured-agent IV report (a distinct, separately
human-authorized re-dispatch action may do so after this repair is
verified, per the governing prompt).
