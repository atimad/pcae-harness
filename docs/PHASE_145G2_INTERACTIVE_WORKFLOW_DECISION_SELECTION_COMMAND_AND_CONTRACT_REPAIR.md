# Phase 145G.2 — Interactive Workflow Decision-Selection Command and Contract Repair

**Status:** Completed (bounded repair phase).
**Repairs:** Phase 145G.1's disclosed Blocking finding F-145G.1-1.
**Runtime:** Observed / observe / unavailable, unchanged before and after
this phase (confirmed via `pcae runtime inspect --json`).
**Governing contracts:** IWPC-001 v1.1 → v1.2 (revised by this phase, §33
of the contract itself), IWC-001 v1.2 (read, not modified), PEC-001 v1.1
(read, not modified), CHGR-001 (read, not modified).

This report follows the same leaner format Phase 145G.1 adopted (a
scoping decision reused here for the same reason: the governing prompt's
surface area is large; this states what was built, why, what was
verified, and what remains open).

## 1. What Phase 145G.1 disclosed, and what this phase closes

Phase 145G.1 implemented `evidence`/`clarify`/`preview`/`confirm`/
`cancel` and repaired `readiness` construction, but disclosed Blocking
finding **F-145G.1-1**: no command in IWPC-001 v1.1's frozen §5 command
surface transitioned a session out of `AwaitingDecision`.
`Session.human_selection_id`/`human_rationale_text`/
`human_conditions_text`/`options_presented` had no production setter
anywhere in the codebase; `clarify`/`preview`/`confirm` were each
implemented correctly but reachable only via direct test-fixture
session-state construction, never a real CLI-only sequence from `create`.

This phase closes F-145G.1-1 by: repairing IWPC-001 (v1.1 → v1.2, §33) to
add a `decision-session select` command; implementing the corresponding
domain/application/CLI code; and — a second finding this phase's own
required re-derivation step surfaced, not present in F-145G.1-1's
original text — repairing a pre-existing implementation defect in
`preview` that also blocked the same downstream reachability chain (§3
below).

## 2. Independent re-derivation (required first step)

Re-derived directly from source (`interactive_workflow/models/session.py`,
`state_machine/transitions.py`, `orchestration/models.py`,
`application/session_service.py`, `commands/decision_session.py`), not
from Phase 145G.1's own report text:

1. **State enum and transition table confirmed unchanged and sufficient:**
   `AwaitingDecision → DecisionSelected` and `EvidenceReady →
   AwaitingDecision` are both already legal in `TRANSITION_TABLE`; no
   state-machine code change was needed or made.
2. **No production setter confirmed:** grep across
   `interactive_workflow/**` for writers of `human_selection_id`/
   `human_rationale_text`/`human_conditions_text`/`options_presented`
   found none outside `serialization/schema.py` (round-trip only),
   `publication_handoff/handoff.py` (read-only), and test fixtures.
3. **No orchestration stage governs selection:** the eight fixed
   `OrchestrationStage` values (`orchestration/models.py`) have no
   "option presentation" or "decision selection" member — confirmed this
   is a pure `SessionState`-level transition with no orchestration
   bookkeeping counterpart, unlike `evidence`/`clarify`/`preview`/
   `confirm`, each of which advances a real stage.
4. **No production Decision Template resolver exists anywhere in this
   codebase:** `template_ref` is treated as an opaque string throughout;
   there is no way to derive a real closed option set, template version,
   or eligible-selector identity from it. This directly shaped every
   input-source decision below (§4).
5. **Closest existing precedent for a combined-hop, single-invocation
   command:** `submit_evidence` (Phase 145G.1), which already combines
   `Created → EvidenceReady`'s precondition-then-transition pattern in
   one call for the identical reason (no separate "evidence complete"
   signal exists). Reused directly for `select`'s own
   `EvidenceReady → AwaitingDecision → DecisionSelected` combination.
6. **Closest existing precedent for replay/mutation semantics:**
   `record_confirmation` (single-use, fail-closed, no idempotent-replay
   path) rather than `submit_evidence`/`cancel_session` (idempotent by
   key) — a human decision selection is not safely re-derivable from
   identical resupplied inputs the way a declared-evidence-id set is.
7. **Closest existing precedent for identity input:** `confirm`, which
   takes no separate identity flag and implicitly uses the session's own
   bound `owner_identity` — reused for `select` over `create`'s
   fresh-binding pattern.
8. **Newly discovered, previously undisclosed blocker (not named by
   F-145G.1-1's own text):** even after closing the `AwaitingDecision →
   DecisionSelected` hop, manual end-to-end verification (`pcae
   decision-session confirm` against a freshly `DecisionSelected` +
   previewed session) failed with `invalid_state_transition` — `confirm`
   requires `AwaitingConfirmation`, and nothing drove
   `DecisionSelected → AwaitingConfirmation` either.
   `generate_preview`'s existing implementation never transitioned
   session state at all. Direct re-reading of IWC-001's own frozen state
   table (`AwaitingConfirmation` = "Preview generated, awaiting
   Confirmation") and this contract's own IWPC-REQ-018 ("no transition …
   unless IWC-001 defines otherwise") confirmed this was a pre-existing
   implementation defect relative to already-frozen contract text, not a
   new contract gap requiring authorization to fix — see §3.
9. **A second, structurally identical but distinct sibling gap
   confirmed and deliberately left open:** no command transitions
   `AwaitingDecision → AwaitingClarification` (`clarify` only answers a
   clarification already open, `AwaitingClarification → AwaitingDecision`).
   This blocks `clarify`'s own real-world reachability, exactly as
   F-145G.1-1 blocked `select`'s — but it is a different operation
   ("open a clarification request") from decision selection, and this
   phase's own governing prompt authorizes only "decision selection."
   Disclosed as new finding **F-145G.2-1** (Non-Blocking for this
   phase's own exit criteria, since the happy path never requires
   `clarify`), not closed.

## 3. The two repairs

### 3.1 `decision-session select` (closes F-145G.1-1)

- **Domain:** `Session.with_decision_capture(...)` — a new structural
  mutator (`interactive_workflow/models/session.py`), mirroring
  `with_state`'s own precedent exactly (frozen dataclass reconstruction,
  no legality check performed here).
- **Application:** `SessionApplicationService.select_decision(...)`
  (`interactive_workflow/application/session_service.py`) — loads the
  session, validates the precondition state
  (`EvidenceReady`/`AwaitingDecision`), validates `option_id` is a member
  of the caller-declared `options_presented` set (`InvalidSelectionError`
  otherwise, a new domain error registered in the existing
  `_ORCHESTRATION_DOMAIN_ERRORS` auto-mapping, reusing the existing
  `invalid_state_transition`/exit-2 mapping — no new `error_type` or exit
  code was added), performs one or two `TransitionEngine.apply` calls
  depending on starting state, and persists via the existing
  `SessionRepository`/`FilesystemOrchestrationStore` only (no new store).
- **CLI:** `run_decision_session_select` (`commands/decision_session.py`)
  and its `argparse` wiring (`cli.py`) — `<session-id>`, `--option-id`,
  one-or-more `--options-presented`, `--template-version`, optional
  `--rationale`/`--conditions`, `--json`. CLI-layer structural checks
  (non-empty, no duplicates, `--option-id` ∈ `--options-presented`) run
  before the application call, matching every other command's own
  discipline; no `--force`/`--yes`/`--assume-authorized` flag exists.
- **`--template-version` (a second, adjacent field this command also
  captures):** `PublicationHandoff.validate_completeness` already
  requires `Session.template_version` non-empty, and — like the Decision
  Capture fields — it had no production setter anywhere. Manual
  end-to-end verification surfaced this the same way it surfaced §3.2:
  without it, a freshly-selected session could never reach `readiness`.
  Captured here (not at `create`, whose frozen `IWPC-REQ-015` argument
  list has no field for it, and not invented as a new `create` argument,
  since no template resolver exists to make it meaningful there either)
  because `select` is the first, and only, point in the existing command
  sequence where the caller already supplies other template-derived
  metadata (`options_presented`). Required (not optional) on the CLI, to
  avoid silently stranding a session that can never reach publication.

### 3.2 `preview` first-construction transition (necessary repair, not new scope)

`SessionApplicationService.generate_preview`'s `PREVIEW_CONSTRUCTION`
branch now transitions the session `DecisionSelected → AwaitingConfirmation`
via `TransitionEngine.apply` before rendering the Preview, when (and only
when) the session is currently `DecisionSelected`. Idempotent re-renders
(session already `AwaitingConfirmation`/`Confirmed`) perform no further
transition. The new transition's sequence number is threaded into the
Preview's own bound `transition_sequence_number` so the constructed
Preview is never immediately stale against the record it is persisted
alongside. IWPC-001 §5.5 (`preview`, renumbered from §5.4) is corrected
in place to state this — IWPC-REQ-018 already said "no transition …
unless IWC-001 defines otherwise," and IWC-001 already defines otherwise;
this is a textual correction to already-frozen intent, not new contract
authority, mirroring §32's own precedent for a garbled/incorrect
"State transition" clause.

## 4. Contract disposition

- **IWPC-001:** v1.1 → v1.2. §33 (new) documents the full repair.
  IWPC-REQ-014 amended in place (new `select` line); IWPC-REQ-192–196
  added (new); IWPC-REQ-018's `preview` transition clause and
  IWPC-REQ-064's cross-reference corrected in place; §29 register gains
  C-9 (F-145G.1-1, Repaired) and C-10 (F-145G.2-1, disclosed,
  out-of-scope). No existing `IWPC-REQ-###` identifier renumbered,
  retired, or reassigned.
- **IWC-001:** unmodified. Direct re-reading of §4.4/§5/§6
  (IWC-REQ-018/052/063 and the state table) confirmed IWC-001 already
  fully anticipates human decision selection as an exclusively human act
  over a closed option set — the gap was entirely a missing CLI/transport
  binding in IWPC-001, not a semantic gap in IWC-001.
- **PEC-001, CHGR-001:** unmodified; this repair does not touch
  publication authority, execution, or CHGR ownership.

## 5. Verification

- Manual, real-CLI, restart-separated smoke test (temp-directory
  processes, not in-process fixtures): `create` → `evidence` → `select`
  → `preview` → `status` (confirms `AwaitingConfirmation`) → `confirm` →
  `readiness` (twice, idempotent) → `governance-record publish` →
  replay (rejected, `publication_already_completed`) — all succeeded
  with no direct session/orchestration-state construction anywhere in
  the chain.
- `tests/test_phase_145g2_decision_selection_cli_repair.py` (new, 28
  tests): parser registration; `select` success from `EvidenceReady` and
  from `AwaitingDecision` (reached via the clarify bridge); restart
  survival; wrong-state/empty/duplicate/non-member/conflicting-replay/
  post-cancellation/post-confirmation/post-readiness/post-publication
  rejection; the `preview`-drives-`AwaitingConfirmation` repair (first
  call transitions, second does not, digest stable across the
  transition); a fully CLI-only `create`-through-`publish`-through-replay
  scenario with **no** state bridging anywhere; a second CLI-only
  scenario additionally exercising `clarify` (one disclosed bridge, for
  F-145G.2-1 only); cross-session option-set isolation; path-traversal-
  style option-id acceptance (structurally opaque, like evidence ids);
  and an extension of the forbidden-import boundary test.
- `tests/test_phase_145g1_decision_session_cli_repair.py`: all 44
  pre-existing tests pass unmodified (confirms the `preview` repair does
  not regress bridged-session flows).
- Broader regression:
  `python -m pytest tests/ -k "interactive_workflow or decision_session
  or 145g or 145d or 145e or 145f or 144c or publication"` — 1000 passed,
  1 skipped, 2 failed. Both failures
  (`test_cltr_authority_136ah_publication.py::test_136ah_wheel_contains_publication_module_no_later_family`,
  `test_cltr_authority_136ai_publication_independent.py::TestPackaging::test_wheel_contains_publication_module_and_both_schemas_no_later_family`)
  independently reproduced identically against unmodified `main` (`git
  stash` + re-run), confirming they are pre-existing wheel-packaging
  artifacts, untouched by this phase's diff.
- `python -m pytest -m fast_green`: 4391 passed, 0 failed.
- `pcae check`: passed. `pcae runtime inspect --json`: Observed / observe
  / unavailable, unchanged before and after.
- Dependency-boundary/forbidden-import tests: pass unchanged; no import
  added to `decision_session.py` beyond its existing allowed set; no
  `.pcae/policy.toml` change was needed or made.

## 6. No-Go confirmation

No HTTP/RPC/socket/web/message-bus/remote transport added. No TUI or
interactive prompt added. No automatic confirmation, authorization, or
publication added. No `--force`/`--yes`/`--assume-authorized` flag on any
command. No CLI handler bypasses `SessionApplicationService`. No CLI
handler accesses `SessionRepository`, `FilesystemOrchestrationStore`, or
the Pending-Readiness Store directly. No CLI handler invokes
`WorkflowOrchestrator`/`TransitionEngine`/`PublicationHandoff`/
`PublicationCoordinator` directly. No CHGR artifact is created by CLI or
application-service code beyond the existing, unmodified publish path. No
readiness-package immutability or digest verification weakened. No
identity or decision inferred from OS user, Git config, agent ID,
lifecycle lock owner, undeclared environment variable, Telegram
configuration, or shell user. No engineering execution capability added.
Runtime unchanged (Observed / observe / unavailable), confirmed before
and after via `pcae runtime inspect --json`.

## 7. Findings summary

| Finding | Status | Disposition |
|---|---|---|
| F-145G.1-1 | Closed | `decision-session select` (IWPC-REQ-192-196) + `preview`'s `DecisionSelected → AwaitingConfirmation` repair; full CLI-only path `create` → `evidence` → `select` → `preview` → `confirm` → `readiness` → `governance-record publish` → replay verified. |
| F-145G.2-1 (new) | Disclosed, not closed | No command opens `AwaitingClarification` from `AwaitingDecision`; `clarify` itself only answers one already open. Out of this phase's own authorized "decision selection" scope — a "request clarification" command is a genuinely different operation. Non-Blocking: the happy path this phase's exit criteria require never needs `clarify`. |
| Adjacent gap (disclosed, not a finding): `Session.disclosure_acknowledgements` | Not closed | IWC-REQ-089 ties it to pre-Preview timing, but nothing in this codebase (including `generate_preview`) currently reads or enforces it, so it does not block any of this phase's exit criteria. Left for a future phase to scope explicitly rather than silently folded into `select`. |

No Blocking finding remains open.

## 8. Recommended next phase

**145G.2V — Interactive Workflow Decision-Selection Contract and
Implementation Independent Verification.** This recommendation does not
authorize 145G.2V, 145G.3, or 145H.
