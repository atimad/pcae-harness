# Phase 134B.3 — Finalization Configuration, Identity, and Cross-Agent Hardening

## 1. Motivation

Phase 134B.1 repaired a test/subprocess environment-isolation defect that
let ordinary tests reach the operator's Telegram channel. Phase 134B.2
independently challenged that repair and closed one genuine BLOCKING
authorization gap in a second dispatch path. Executing 134B.2 itself
exposed three further weaknesses in the governed finalization lifecycle
that were not caused by, and would recur regardless of, any specific model
or agent:

1. Delivery configuration had no automatic resolution path — every
   governed finalization required the operator to `source
   ~/.config/pcae/telegram.env` in the same shell as `pcae phase complete`.
2. `.pcae/phase-completion-metadata.json` going stale (its `phase_id`
   lagging one phase behind) repeatedly blocked finalization, and the only
   recovery was unconstrained hand-editing of the whole JSON file.
3. The notification flood that motivated 134B.1 was first observed during
   DeepSeek-backed work, then reproduced under Claude, then under Codex —
   evidence that must be recorded correctly rather than left attributed to
   any one agent.

This phase hardens all three without beginning 134C or any larger Track 134
architecture.

## 2. Investigation Methodology

Traced from source, not from prior reports: every `os.environ.get("PCAE_
...")` call site across the codebase; the CLI entrypoint (`pcae.cli.main`);
`RepositoryState`/`validate_transition`/`TransitionKind` in the repository
transition validator; `resolve_canonical_phase_identity()` and
`validate_finalization_gate()` in `phase_reports.py`; the existing
`push_state_reconciliation` module; and every module in the notification/
finalization call graph, grepped for any DeepSeek/Claude/Codex/model-
identity reference.

## 3. Part I — Delivery Configuration Sources (Before Hardening)

Eleven independent call sites across six files
(`notification_certification.py`, `phase_reports.py`, `notifications.py`,
`commands/task.py`, `commands/phase.py`, `commands/session.py`,
`commands/phase_reports.py`, `commands/notifications.py`) each called
`os.environ.get("PCAE_...")` directly. There was no automatic resolution
path other than the operator manually sourcing
`~/.config/pcae/telegram.env` in the same shell as the finalization
command — a real, felt dependency (the operator had to re-source it for
this session multiple times across tool calls, since each shell invocation
starts a fresh, unconfigured environment).

**Answers to Part I's ten questions:**

1. Configuration sources: process environment only (no file, no keychain).
2. Authoritative source: `os.environ`, read independently at each call
   site.
3. Loaded per invocation, but only from shell inheritance — no explicit
   load step existed.
4. Subprocesses received configuration only by environment inheritance
   from whatever process spawned them.
5. Resolution never depended on the calling agent (see Part III).
6. No — finalization could not resolve configuration without a preceding
   shell `source`.
7. `notify status` (`commands/notifications.py::run_notify_status`) and
   dispatch (`finalize_phase_report()`) each read `os.environ` themselves
   — same variable names, but no shared resolver.
8. Yes — 134B.1/134B.2 isolation strips these names in tests; production
   was unaffected by that stripping.
9. No — a future adapter would need its own literal env-var names read at
   its own call site, same as Telegram.
10. Credentials only ever lived in `os.environ` and the shell file the
    operator sourced — no logging, report, or repository-state leak was
    found.

## 4. Canonical Resolver (After Hardening)

**New module:** `src/pcae/core/notification_config.py`.

`ensure_notification_environment_loaded()` is called exactly once, at the
very start of `pcae.cli.main()` — the one choke point every governed
invocation, including a fresh subprocess, already passes through. It:

- Is a no-op if `PCAE_NOTIFY_CONFIG_DISABLE` is set (test isolation's own
  escape hatch — see §6).
- Is a no-op for any `PCAE_*` variable already present in `os.environ`
  (explicit shell-sourced/exported configuration always wins).
- Otherwise reads a flat JSON object from a governed config file
  (default `~/.config/pcae/notify.json`, overridable via
  `PCAE_NOTIFY_CONFIG_FILE`) and copies only its `PCAE_`-prefixed,
  string-valued keys into `os.environ`.

**Precedence (highest to lowest):** governed test-isolation disable flag →
explicit process environment → governed config file → nothing (fail
closed).

**Missing-config behavior:** no file → no environment change, no error.
**Invalid-config behavior:** unreadable/unparseable/non-dict JSON → no
environment change, no exception ever raised or logged with content.
**Secret redaction:** `redact_config_value()` marks any key containing
`TOKEN`/`SECRET`/`KEY`/`PASSWORD`/`CHAT_ID` as `present`/`missing` only,
never the value; the resolver's own return summary never contains
resolved values, only which keys were applied.
**Adapter registration:** none needed — any `PCAE_`-prefixed key works
through the same mechanism, proven for a synthetic, nonexistent channel
(`tests/test_finalization_configuration_identity_cross_agent_134b3.py::
test_future_synthetic_adapter_env_resolves_through_the_same_mechanism`).
**Subprocess propagation:** automatic and equivalent — the file is read
fresh by every process's own `pcae` CLI entrypoint; no environment
inheritance is required at all.
**Test override behavior:** `PCAE_NOTIFY_CONFIG_FILE` lets a test point at
a fixture file without touching the operator's real one.
**Live-test authorization separation:** unchanged from 134B.1/134B.2 —
`PCAE_TEST_ALLOW_LIVE_NOTIFICATIONS=1` only stops the isolation fixture
from setting the disable flag; it does not itself enable notifications or
resolve any configuration.

The actual governed config file was populated at
`~/.config/pcae/notify.json` (mode `0600`, outside the repository, never
committed) from the same five variables already in
`~/.config/pcae/telegram.env`, so this phase's own terminal report could be
delivered without sourcing anything in the finalization command chain
(§11).

## 5. Test Isolation Compatibility

Wiring the resolver into every CLI invocation created a new theoretical
bypass: a subprocess a test spawns would, on its own, reload real
credentials from the governed file even though its parent process had
stripped the five known environment variables. `tests/conftest.py`'s
autouse isolation fixture was extended to also set
`PCAE_NOTIFY_CONFIG_DISABLE=1` (mirroring exactly how it already strips the
five variable names), so the resolver is disabled for the entire isolated
test session and every subprocess it spawns, regardless of what the real
config file contains. Verified end-to-end via a genuine subprocess CLI
call
(`test_ordinary_tests_isolated_even_though_resolver_is_globally_wired`),
not just an in-process unit check.

## 6. Part II — Phase Identity Source Map

Every phase-identity source found by source inspection:

| Source | Where | Precedence in `resolve_canonical_phase_identity()` |
|---|---|---|
| Active task contract title | `tasks/active/*.md` `## Title` | 1 (highest) |
| Phase-completion metadata | `.pcae/phase-completion-metadata.json` `phase_id` | 2 |
| Lifecycle context | `PROJECT_STATUS.md` "## Current Phase" (only if not `(completed)`) | 3 |
| Explicit CLI `--phase-id` | `pcae phase complete --phase-id` | 4 (last resort) |

`resolve_canonical_phase_identity()` (Phase 113X.4) already picks exactly
one of these deterministically and never mixes fields across sources —
this is why `--phase-id 134B.2` was silently outranked by a stale metadata
`phase_id` of `134B.1` during this phase's own execution: metadata is
priority 2, above the CLI override at priority 4, by design (metadata is
meant to be more authoritative than an ad hoc CLI flag). The correct fix
for staleness is therefore never "let the CLI silently win" — it is
repairing the metadata itself, which had no safe tool before this phase.

Separately, `repository_transition_validator.py`'s `RepositoryState`
(Phase 113U/113T) is **already** deliberately agent-agnostic (it carries
`phase_id`, `active_task_phase_id`, `metadata_phase_id`,
`lifecycle_current_phase_id` as independent evidence fields, and
`_check_phase_identity_consistency()` / `_check_metadata_consistency()`
are `mandatory`/`blocking` invariants) and — confirmed directly by this
phase's own experience finalizing 134B.2 — genuinely fails closed when
sources disagree, quarantining rather than silently promoting.

**Answers to Part II's twelve questions:** identity sources (4, table
above); authoritative source per stage (`resolve_canonical_phase_identity`'s
fixed precedence); different stages do consult different subsets (task
finish vs. phase complete vs. notify send-report — 134B.2 §2 documented
this duplication for dispatch; identity uses the same shared resolver
everywhere, no duplication found); staleness detection (mandatory blocking
invariants in the validator, confirmed firsthand); conflicts are
quarantined/rejected, never silently ignored; the existing workaround
(hand-editing metadata) did not bypass canonical finalization — it fed the
same validator, which still correctly re-checked afterward; finalization
did not deadlock in practice but had no *safe* repair tool (§7 closes
this); resolution is deterministic (fixed precedence, no randomness);
Phase 113X.4 already repairs the historical "identity derived by regex
from `--summary`" defect class, and no reachable regression of it was
found; report/metadata/task/CLI identity can disagree (this is exactly
`phase_identity_consistency`'s job to catch); delivery cannot occur for an
identity finalization later rejects — `NOTIFY` is certified from the same
`RepositoryState` and fails closed identically.

## 7. Canonical Identity Hardening: `pcae phase metadata-repair`

**New command:** `pcae phase metadata-repair [--json]`
(`src/pcae/commands/phase.py::run_phase_metadata_repair`).

A single, narrow, one-direction repair: it reads the already
hand-authored, reviewed canonical narrative report
(`.pcae/phase-completion-report.md`)'s own title line
(`# Phase <id> Complete — <name>`) and syncs
`phase-completion-metadata.json`'s `phase_id`/`phase_name`/`phase_title`
fields to match it exactly. It never accepts a phase_id as a CLI argument,
free text, or any other unreviewed input — the canonical report is the
only source of truth it will ever copy from, and only in that direction.

- Refuses (no mutation) if no metadata file exists.
- Refuses (no mutation) if no canonical report exists.
- Refuses (no mutation) if the canonical report's title does not match the
  expected format.
- Reports success with no change (never a silent overwrite) when metadata
  already agrees.
- On a genuine repair, touches only the three identity fields — all other
  metadata (test results, governance results, push state) is untouched —
  and appends one line to `.pcae/phase-metadata-repairs.log` (old id, new
  id, timestamp, source) as a durable audit trail distinct from the
  metadata file itself.
- Inspects no git state at all (`git` and `pushed_status` do not appear in
  its source — confirmed by
  `test_metadata_repair_does_not_require_clean_or_pushed_state`), so it
  cannot be blocked by, or contribute to, the clean/pushed circular
  dependency this phase's own 134B.2 finalization hit.

This directly replaces what this phase's own predecessor session did by
hand (an unconstrained `Write` of the entire metadata JSON file) with a
narrow, auditable, safe operation.

## 8. Stale Metadata Hardening Summary

- **Freshness validation:** delegated to the existing, already-correct
  `phase_identity_consistency`/`metadata_consistency` mandatory invariants
  — not duplicated.
- **Identity validation:** unchanged — `resolve_canonical_phase_identity()`
  remains the single source per stage.
- **Lifecycle ownership:** `metadata-repair` owns only the metadata file's
  identity fields; it does not touch canonical reports, task contracts, or
  git state.
- **Safe quarantine or replacement:** replacement, one direction, from a
  human-reviewed source only.
- **Auditability:** `.pcae/phase-metadata-repairs.log`, append-only.
- **Recovery behavior:** re-running `metadata-repair` after a repair is a
  verified no-op.
- **No silent overwrite:** every repair prints/returns the exact old/new
  values.
- **No external delivery before identity is resolved:** unchanged —
  `metadata-repair` never dispatches anything.
- **No circular clean/push/finalization dependency:** confirmed by source
  inspection and test (§7).

## 9. Part III — Cross-Agent Incident Analysis (Corrected Attribution)

The notification flood was:

- **first observed** during DeepSeek-backed work;
- **reproduced** during Claude-backed work (134B.1's own investigation,
  conducted by a Claude-backed session, itself triggered synthetic
  notification events during its focused-test runs, per 134B.1's incident
  evidence table);
- **reproduced** during Codex-backed work.

This reproduction pattern is direct evidence *against* a DeepSeek-specific
cause: if the defect were unique to DeepSeek's invocation style, it would
not have reproduced identically under two architecturally unrelated
agents. The defect tracked the repository's lifecycle and configuration
boundaries (ordinary pytest execution inheriting a sourced shell
environment; a second dispatch call site bypassing the master switch) —
boundaries that are identical regardless of which agent invokes `pcae` or
`pytest`. **The historical DeepSeek attribution is explicitly incorrect
and is corrected here:** this was, from the beginning, a PCAE substrate
defect, not a DeepSeek-specific one.

**Agent-Agnostic Lifecycle Invariant — verified, not newly built.**
Source inspection (`repository_transition_validator.py`'s own module
docstring: *"No field on any type in this module carries the identity of
the proposing agent"*) confirms this was already an explicit design
principle as of Phase 113U, not something 134B.3 needed to introduce.
`ProposedTransition.payload` is an open bag that may carry an `"agent"`
key for a caller's own bookkeeping, but `validate_transition()` never
reads it. Grepping every lifecycle-critical module
(`repository_transition_validator`, `notification_certification`,
`notifications`, `phase_reports`, `notification_config`) for
`deepseek`/`claude`/`codex` found zero matches.

## 10. Cross-Agent Verification Evidence

`tests/test_finalization_configuration_identity_cross_agent_134b3.py`:

- `test_validator_produces_equivalent_verdicts_regardless_of_caller_identity`
  — parametrized over four synthetic caller identities (`deepseek-agent`,
  `claude-agent`, `codex-agent`, `unknown-future-agent`) passed through
  `ProposedTransition.payload`; identical `RepositoryState` produces
  `TransitionVerdict.ACCEPT` in all four cases.
- `test_no_model_specific_branch_exists_in_lifecycle_critical_modules` —
  static confirmation across five modules.
- `test_configuration_resolution_is_caller_independent` — the resolver's
  own signature takes no caller/agent argument at all.
- `test_synthetic_execution_remains_isolated_regardless_of_synthetic_caller_marker`
  — a synthetic `PCAE_SYNTHETIC_CALLER_AGENT=deepseek-agent` marker present
  in the environment does not affect external-delivery authorization;
  `dispatch()` still fail-closes.

No real model was invoked; all four "agents" are string markers exercising
the same code path a real invocation would.

## 11. Part IV — Delivery Receipt and Audit Classification (Transport-Neutral)

Re-evaluated, not re-litigated: `FilesystemSink` durably persists one JSON
file per dispatched event (a logical-delivery record). `TelegramSink.send()`
returns one `NotificationResult` per logical dispatch, with
`send_message_ok`/`send_document_ok` captured in that result's `metadata`
dict — sub-attempt granularity exists in memory for the single call that
produced it, but nothing durably persists per-physical-attempt records
across dispatches, and no component distinguishes retries (there are none
to distinguish — confirmed again, no retry loop exists in any sink).
Synthetic and production dispatches are distinguished only by the
5734isolation boundary being in effect during tests, not by any receipt
flag.

**This absence affects only after-the-fact historical reconstruction, not
correctness:** every current control (134B.1's environment isolation,
134B.2's `dispatch()` authorization gate, 134B.3's identity/config
hardening) operates independently of whether a durable receipt exists.
**No blocking defect.** Carried forward, in transport-neutral language, as
Track 134 implementation debt: a generic External Delivery Receipt Ledger
distinguishing logical delivery from per-adapter physical attempts,
retries, and failures — scoped to 134D–134F, not implemented here.

## 12. Focused Verification Results

- `tests/test_finalization_configuration_identity_cross_agent_134b3.py`:
  26 passed.
- Combined with 134B.1/134B.2/telegram/notifications/phase_reports/
  finalization-gate/trust-hard-fail/certification-idempotency/model-
  containment/permission-broker/RC-audit/session/phase suites: **1428
  passed**.
- `python -m compileall -q src`: passed.
- Full fast-green suite: see §13.

## 13. Full Regression Results

`python -m pytest -m "fast_green" -n auto -ra --durations=100`: see commit
message / final report for the exact count. The one pre-existing,
environment-state-dependent failure identified in 134B.2
(`test_pytest_dry_run_not_blocked`, unrelated to notifications) is expected
to reproduce identically here as well, since no active-task-dependent code
was touched by this phase.

## 14. Governance Results

- `pcae check`: passed throughout.
- Governed commit/push commands only (`pcae commit implementation`,
  `pcae push`, `pcae task new`/`finish`) — no raw `git commit`/`git push`,
  no `--no-verify`, no force push.
- Runtime remained Observed; execution unavailable throughout.

## 15. Remaining Track 134 Debt

- Generic External Delivery Receipt Ledger (§11) — 134D–134F.
- The governed live-integration opt-in still depends on whatever
  production configuration is already resolvable, rather than a fully
  independent test-only credential set (134B.2 §6, unchanged here).
- No pytest marker scopes live-integration tests for collection-time
  exclusion (134B.2 §6, unchanged here).
- The governed config file's location/format
  (`~/.config/pcae/notify.json`) is a minimal, single-tier convention;
  Track 134's future Delivery Adapter framework may want a richer,
  per-adapter schema — deliberately not built here (Part V scope limit).

## 16. Compatibility with 134A and 134B

No change to the twelve-stage lifecycle contract frozen in 134A/134B, to
PFN-001, to exactly-once logical completion, to Canonical Engineering
Evidence, Evidence Extraction, Derived Evidence Views, or Architecture
Status. This phase strengthens the substrate those stages already run on.

## 17. Recommended Next Phase

**134C — Canonical Phase Finalization & Reporting Lifecycle Contract
Verification.** Phase 134C has not begun.
