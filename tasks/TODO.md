# TODO

**Source of truth:** `PROJECT_STATUS.md`'s `## Current Phase` section is
authoritative for "what phase are we on" and "what phase is recommended
next" — never this file. `docs/ROADMAP.md` is the canonical long-term
roadmap and product-direction document. This file is planning scratch
space only: useful for browsing upcoming/candidate work, but never a
source a session should trust over `PROJECT_STATUS.md` if the two
disagree. See the full source-of-truth precedence order and the stale
90-series finding this file previously had in
[docs/PHASE_112_PLANNING_BOOTSTRAP_CONSISTENCY_HARDENING.md](../docs/PHASE_112_PLANNING_BOOTSTRAP_CONSISTENCY_HARDENING.md)
(Phase 112B.1).

## Known Issues / Queued Fixes

- **Bootstrap stale-active-task self-comparison bug** (found 2026-07-20,
  during 137J→137K task transition): `pcae session bootstrap`'s
  `_classify_bootstrap_readiness()` compares the latest completed phase
  report's phase to itself instead of to the active task's phase, so it
  reports `Readiness: blocked` / "Active task appears stale" on every
  bootstrap after any completed phase report, even when the active task
  correctly matches the recommended next phase. Cosmetic/diagnostic only —
  does not block real commands. See
  [docs/FINDING_BOOTSTRAP_READINESS_STALE_TASK_SELF_COMPARISON.md](../docs/FINDING_BOOTSTRAP_READINESS_STALE_TASK_SELF_COMPARISON.md)
  for full report and proposed fix. Not yet scheduled as a governed phase.

- **Phase-report finalization regex truncates multi-letter, non-dotted
  phase-ID suffixes** (found 2026-07-20, during Phase 137M's own
  finalization): `src/pcae/core/phase_reports.py`'s Architecture-Status
  conflict-projection helper (the `if completing_phase_id and
  report_status == "completed":` block, `rec_match = re.match(...)` at
  line 3043-3048) uses the pattern
  `r"^(?:Phase\s+)?(\d+[A-Za-z](?:\.\d+[A-Za-z]?)*)"` — a single
  `[A-Za-z]` (no `+`/`*` quantifier) for the phase-ID's letter suffix.
  Three other phase-ID-parsing regexes in the same file (lines 1245, 1260,
  2112, 2977) correctly use `[A-Za-z]+` or `[A-Za-z]*`. The unquantified
  version truncates a `recommended_next_phase` value like `"137MV — ..."`
  to `"137M"`, and if the phase currently being completed is itself
  `"137M"`, the truncated ID collides with `completed_id_set`, producing a
  spurious `"projected recommended next phase '137M' is already
  completed -- dropped from planned"` conflict and an `'invalid'`
  Architecture Status snapshot — blocking `pcae phase complete` from
  writing a non-quarantined canonical report even though there is no real
  conflict (the actual next phase is `137MV`, not `137M`). Phase 137M
  worked around this with `--allow-partial-report` rather than fixing
  `src/pcae/core/phase_reports.py`, which was outside Phase 137M's own
  allowed-file scope (a TAMPC-001 contract-repair phase). Recommend a
  small, dedicated future phase change the line-3044 regex to match the
  other three occurrences (`[A-Za-z]` → `[A-Za-z]+`) and add a regression
  test asserting a two-letter, non-dotted phase-ID suffix (e.g. `137MV`
  immediately following completed phase `137M`) does not trigger a false
  conflict. Not yet scheduled as a governed phase.

- **Pre-existing failure:
  `test_cltr_135o_integration.py::TestEnabledStage1::test_legacy_authority_still_completed_transaction`**
  (found 2026-07-20, during Phase 137MV's broader-than-137L authority test
  sweep, `-k authority` rather than 137L's narrower `-k cltr_authority_136`):
  asserts a Stage 3 transaction completes with status `'completed'` but
  observes `'completed_receipt_best_effort_incomplete'`. Independently
  confirmed unrelated to TAMPC-001/the production Typed Authority Model
  consumer (`authority_inspection.py`/`authority_inspect.py` do not appear
  in the failing test file) and pre-existing (Phase 137M's own commit
  touched zero files under `src/`/`tests/`, so it cannot be the cause). See
  Finding F-5,
  [docs/PHASE_137MV_TAMPC_SIGNATURE_AMBIGUITY_CONTRACT_REPAIR_INDEPENDENT_VERIFICATION.md](../docs/PHASE_137MV_TAMPC_SIGNATURE_AMBIGUITY_CONTRACT_REPAIR_INDEPENDENT_VERIFICATION.md).
  Not yet scheduled as a governed phase.

- **`src/pcae/commands/push.py`'s `_PHASE_TOKEN_RE` truncated a two-letter,
  non-dotted phase-ID suffix — fixed 2026-07-20 (Phase 137MV.1)**: a
  second, independent occurrence of the same unquantified-`[A-Za-z]`
  defect class documented above (found this time while finalizing Phase
  137MV itself — `pcae push check` falsely reported `phase_report
  identity: failed`, truncating the just-completed task's own phase id
  `"137MV"` to `"137M"`). Repaired by quantifying `[A-Za-z]` to
  `[A-Za-z]*`, matching `phase_reports.py`'s own already-corrected
  convention. Regression test added:
  `tests/test_push_phase_report_identity_137f1.py::test_137mv1_phase_token_regex_does_not_truncate_two_letter_undotted_suffix`.
  **Fixed 2026-07-20 (Phase 137R):**
  `pcae.core.repository_transition_integration.parse_phase_id_from_text()`
  used the identical unquantified pattern and was equally susceptible to
  the same two-letter, non-dotted truncation. Phase 137P (2026-07-20)
  confirmed this was one of fifteen independently-duplicated Phase ID
  parsers across `src/pcae/` (not just three) and architected a
  canonical parsing subsystem to eliminate the defect class
  architecturally (`docs/PHASE_137P_CANONICAL_PHASE_ID_PARSING_ARCHITECTURE.md`);
  Phase 137Q froze that architecture as CPIPC-001 v1.0; Phase 137R
  implemented the canonical parser (`src/pcae/core/phase_id.py`) and
  migrated this call site (and eight other consumer groups) to it,
  eliminating the duplicated regex outright rather than patching it
  again. See `docs/PHASE_137R_CANONICAL_PHASE_ID_PARSER_IMPLEMENTATION.md`
  and `docs/CANONICAL_PHASE_ID_PARSER_MIGRATION.md`.

- **Pre-existing full-suite failures unrelated to TAMPC-001** (found
  2026-07-20, during Phase 137N's own due-diligence full `python -m pytest
  -n auto` run — not part of 137N's own required evidence, run as
  additional verification): 38 failures beyond the 16 already logged above
  under the narrower `-k authority` sweep. All 38 independently reproduced
  identically against unmodified `main` (via `git stash`), confirming none
  are caused by Phase 137N's own `docs/**`-only edits. Two categories
  stand out as worth a future dedicated look: (1)
  `test_advisory_runtime_contract.py`/`test_advisory_runtime_architecture.py::test_no_new_directory_added_for_advisory`
  fail because `src/pcae/advisory/` already exists in the checkout,
  contradicting the test's own name/assertion — suggests either a stale
  test or an undocumented architecture change; (2)
  `test_bootstrap_todo_consistency.py` (3 tests) fail because
  `src/pcae/core/context.py`'s `_extract_recommended_next_phase()` regex
  requires a `"Recommended next repo phase: X — Y (not ..."` sentence
  form that `PROJECT_STATUS.md`'s actual, long-established "Recommended
  next phase: ..." convention never produces, so `roadmap_summary
  ["recommended_next_phase"]` is `None` for every real phase from at
  least 137D onward — the extractor and the document convention have
  drifted apart.
  **Fixed 2026-07-20 (Phase 137S):** independent verification of Phase
  137R's canonical Phase ID parser found this was actually worse than
  `None` — the regex's whole-file `.search()` matched a stale historical
  occurrence of the old phrasing rather than returning nothing,
  reproduced live returning a long-completed phase (`137I.1V`) as the
  "current" recommendation. Repaired by reusing `phase_reports.py`'s
  already-correct, section-bounded extraction instead of maintaining a
  second implementation. See
  `docs/PHASE_137S_CANONICAL_PHASE_ID_PARSER_INDEPENDENT_VERIFICATION.md`.

## Current Roadmap

`PROJECT_STATUS.md` remains authoritative. Phase 137G independently
reconciled the full 137A→137F.1V chain and produced an architecture-only
verdict — **SUITABLE WITH REQUIRED ARCHITECTURAL CHANGES** — for a single
first production Typed Authority Model consumer, `pcae authority inspect
<path>`, without implementing it. Phase 137H then converted that
architecture into TAMPC-001 v1.0
(`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`),
the binding normative contract for that consumer's implementation, without
implementing it. Phase 137I then independently verified TAMPC-001 v1.0
(verdict **VERIFIED AFTER REPAIR**; one non-blocking documentation-only
cross-reference repair, no Blocking finding), clearing the contract to
govern implementation. Phase 137I.1 then repaired a finalization-ordering
deadlock in the harness's own governance tooling (a completed-but-unpushed
phase could not be finalized through governed workflows), adding a
non-authoritative pending-report escape without weakening any trust gate.
Phase 137I.1V then independently verified that repair (verdict **VERIFIED
AFTER REPAIR**; one non-blocking residual regex-truncation defect found and
repaired, one non-blocking deferred bootstrap-consumer observation, no
Blocking finding), clearing 137J to proceed. Phase 137J then converted
TAMPC-001 v1.0 into a bounded implementation plan
(`docs/IMPLEMENTATION_PLAN_TYPED_AUTHORITY_MODEL_CONSUMER.md`), mapping all
178 TAMPC-REQ requirements to owners/tests, with no ambiguity requiring
contract repair. Phase 137K then implemented the production consumer,
`pcae authority inspect <path>`. Phase 137L then independently verified
137K (verdict **NOT VERIFIED**: two Blocking defects found and repaired
in-phase; one Blocking defect, Finding F-1 — the frozen
`inspect_artifact_at_path` signature did not match the shipped
implementation — found but left unrepaired, since resolving a contract
ambiguity is outside an independent-verification phase's authority).
Phase 137M then repaired Finding F-1 as a dedicated contract-freeze-class
phase, amending TAMPC-001 to v1.1 (Section 36) with no implementation
change required (Compatibility Review Outcome A). The recommended next
governed phase is **137MV — TAMPC-001 Signature Ambiguity Contract Repair
Independent Verification** (not yet activated).

| Phase | Name | Status |
|-------|------|--------|
| 137E | Typed Authority Model Consumption Read-Only Prototype Implementation | ✅ Complete |
| 137F | Typed Authority Model Consumption Prototype Independent Verification | ✅ Complete |
| 137F.1 | Canonical Report Finalization Recovery and Push-Semantics Repair | ✅ Complete |
| 137F.1V | Canonical Report Finalization Recovery and Push-Semantics Independent Verification | ✅ Complete |
| 137G | Typed Authority Model Prototype Review and Production Integration Architecture | ✅ Complete |
| 137H | Typed Authority Model Production Consumption Contract Freeze | ✅ Complete |
| 137I | Typed Authority Model Production Consumption Contract Independent Verification | ✅ Complete |
| 137I.1 | Finalization Ordering Deadlock Repair | ✅ Complete |
| 137I.1V | Finalization Ordering Deadlock Independent Verification | ✅ Complete |
| 137J | Typed Authority Model Production Consumption Implementation Planning | ✅ Complete |
| 137K | Typed Authority Model Production Consumer Implementation | ✅ Complete |
| 137L | Typed Authority Model Production Consumer Independent Verification | ✅ Complete (NOT VERIFIED — Finding F-1) |
| 137M | TAMPC-001 Signature Ambiguity Contract Repair | ✅ Complete |
| 137MV | TAMPC-001 Signature Ambiguity Contract Repair Independent Verification | ✅ Complete |
| 137MV.1 | push.py Phase-Token Regex Two-Letter Suffix Truncation Repair | ✅ Complete |
| 137N | Typed Authority Model Production Consumer Conformance Re-Verification | ✅ Complete |
| 137P | Canonical Phase ID Parsing Architecture | ✅ Complete |
| 137Q | Canonical Phase ID Parsing Contract Freeze | ✅ Complete |
| 137R | Canonical Phase ID Parser Implementation | ✅ Complete |
| 137S | Canonical Phase ID Parser Independent Verification | ✅ Complete (NOT VERIFIED — 1 Blocking finding repaired in-phase) |
| 137T | Canonical Phase ID Parser Operational Hardening & Repository-Wide Conformance | 🔜 Next |

## Historical: Track 133 — Engineering Evidence

Historical planning snapshot only; superseded by completed Tracks 133–135.

| Phase | Name | Status |
|-------|------|--------|
| 133A–133F | PFR-001 and Canonical Engineering Evidence architecture/contract/verification | ✅ Complete |
| 133G | Canonical Engineering Evidence & Derived Evidence Views Implementation Plan | ✅ Complete |
| 133H | Canonical Engineering Evidence Executable Model Implementation | 🔜 Recommended next |
| 133I–133N | Independent verification, views, rendering, delivery/PFN integration, final verification | Planned sequence; not activated |

## Historical Roadmap Snapshot (Track B — Repository Intelligence)

Per `PROJECT_STATUS.md`. Only the phase explicitly named "Recommended
next repo phase" there is confirmed; everything after it is a tentative
candidate, not a committed queue — no phase activation is inferred ahead
of an explicit human decision (`tasks/DECISIONS.md`). Track A is complete
through the v0.2.0 release and publication repair. Track B begins with
Repository Intelligence: deterministic, source-attributed architectural
understanding without execution, enforcement, or autonomy.

| Phase | Name | Status |
|-------|------|--------|
| 116A | v0.2 Architecture Review & Consolidation | ✅ Complete |
| 116B | v0.2 Architecture Consolidation | ✅ Complete |
| 116C | v0.2 Architecture Consolidation Verification | ✅ Complete |
| 116D | v0.2 Architecture Freeze Preparation | ✅ Complete |
| 116F | v0.2 Architecture Freeze | ✅ Complete |
| 117D | v0.2 Release Candidate Preparation | ✅ Complete |
| 117E | v0.2.0 Release | ✅ Complete |
| 117E.1 | v0.2.0 Release Publication Repair | ✅ Complete |
| 118A | Repository Knowledge Architecture | ✅ Complete |
| 118B | Historical Memory Architecture | ✅ Complete |
| 118C | Change Impact Analysis Architecture | ✅ Complete |
| 118D | Dependency Knowledge Graph Architecture | ✅ Complete |
| 118E | Advisory Reasoning Expansion Architecture | ✅ Complete |
| 118R | Repository Intelligence Architecture Review | ✅ Complete |
| 119A | Repository Intelligence Contract Freeze | ✅ Complete |
| 119B | Repository Intelligence Contract Verification | ✅ Complete |
| 119C | Repository Intelligence Conceptual Schema Architecture | ✅ Complete |
| 119D | Repository Intelligence Conceptual Schema Review | ✅ Complete |
| 119E | Repository Intelligence Artifact Contract Freeze | ✅ Complete |
| 119F | Repository Intelligence Artifact Contract Verification | ✅ Complete |
| 119G | Repository Intelligence Executable Schema Architecture | ✅ Complete |
| 119H | Repository Intelligence Executable Schema Contract Freeze | ✅ Complete |
| 119I | Repository Intelligence Executable Schema Contract Verification | ✅ Complete |
| 119J | Repository Intelligence Executable Schema Implementation Plan | ✅ Complete |
| 119K | Repository Intelligence Executable Schema Implementation: Shared Components | ✅ Complete |
| 119L | Repository Intelligence Executable Schema Verification: Shared Components | ✅ Complete |
| 119M | Repository Intelligence Executable Schema Implementation: First Artifact Family | ✅ Complete |
| 119N | Repository Intelligence Executable Schema Verification: First Artifact Family | ✅ Complete |
| 119O | Repository Intelligence Executable Schema Implementation: Repository Knowledge Snapshot | ✅ Complete |
| 119P | Repository Intelligence Executable Schema Verification: Repository Knowledge Snapshot | ✅ Complete |
| 119Q | Repository Intelligence Executable Schema Implementation: Historical Memory Snapshot | ✅ Complete |
| 119R | Repository Intelligence Executable Schema Verification: Historical Memory Snapshot | ✅ Complete |
| 119S | Repository Intelligence Executable Schema Implementation: Dependency Knowledge Graph Snapshot | ✅ Complete |
| 119T | Repository Intelligence Executable Schema Verification: Dependency Knowledge Graph Snapshot | ✅ Complete |
| 119U | Repository Intelligence Executable Schema Implementation: Change Impact Report | ✅ Complete |
| 119V | Repository Intelligence Executable Schema Verification: Change Impact Report | ✅ Complete |
| 119W | Repository Intelligence Executable Schema Implementation: Advisory Intelligence Context Package | ✅ Complete |
| 119X | Repository Intelligence Executable Schema Verification: Advisory Intelligence Context Package | ✅ Complete |
| 119Y | Repository Intelligence Executable Schema Implementation: Query Result | ✅ Complete |
| 119Z | Repository Intelligence Executable Schema Verification: Query Result | ✅ Complete |
| 119AA | Repository Intelligence Executable Schema Implementation: Repository Intelligence Package | ✅ Complete |
| 119AB | Repository Intelligence Executable Schema Verification: Repository Intelligence Package | ✅ Complete |
| 119AC | Repository Intelligence Executable Schema Final Review | ✅ Complete |
| 120A | Repository Intelligence Read-Only Prototype Architecture | ✅ Complete |
| 120B | Repository Intelligence Prototype Contract Freeze | ✅ Complete |
| 120C | Repository Intelligence Prototype Contract Verification | ✅ Complete |
| 120D | Repository Knowledge Snapshot Prototype Plan | ✅ Complete |
| 120E | Repository Knowledge Snapshot Prototype: Read-Only Generator | ✅ Complete |
| 120F | Repository Knowledge Snapshot Prototype Verification | Historical candidate; re-evaluate before activation |

## Historical: Repository State Kernel Track (113S-114B)

Completed historical track retained for reference. It is not the current
queue; `PROJECT_STATUS.md` remains authoritative for the active phase and
recommended next phase.

| Phase | Name | Status |
|-------|------|--------|
| 113S | Repository Transition Validator Architecture | ✅ Complete |
| 113T | Repository Transition Validator Contract Freeze | ✅ Complete |
| 113U | Repository Transition Validator Prototype | ✅ Complete |
| 113V | Repository Transition Validator Verification & Compatibility | ✅ Complete |
| 113V.N | Phase Finalization Notification Repair | ✅ Complete |
| 113W | Repository Transition Validator Integration Design | ✅ Complete |
| 113X | Repository Transition Validator Integration Contract | ✅ Complete |
| 113Y | Repository Transition Validator Integration: Phase Completion | ✅ Complete |
| 113Z | Repository Transition Validator Integration: Task Finish | ✅ Complete |
| 114A | Report Promotion / Quarantine Hardening | ✅ Complete |
| 114B | Notification Enforcement & Idempotency | ✅ Complete |

## Historical: Production v1 Path (90-series, superseded)

**Historical reference only — this table does not reflect current
work.** It predates the 107–112-series arc (autonomy/no-go →
Permission Broker → observation integrations → Runtime Registry →
Runtime Introspection → Runtime Context) and was left presented as
current in this file long after it was superseded, which is the stale
planning artifact 112B.1 repaired. Kept here, clearly marked, only
because some of its listed phases may still represent real, unstarted
future work once the current 112-series track concludes — not because
90C is upcoming.

| Phase | Name | Status |
|-------|------|--------|
| 90A | Permission Broker Enforcement Boundary Design | ✅ Complete |
| 90B | Full-Suite Baseline Inspection and Repair | ✅ Complete |
| 90B.1 | Roadmap Coherence and Production v1 Plan | ✅ Complete |
| 90C | Permission Broker Enforcement Boundary Test Plan | Historical — not current; re-evaluate scope before resuming |
| 91A | Permission Broker Simulation Prototype | Historical — not current |
| 91B | Broker CLI and Decision Explanation | Historical — not current |
| 91C | Hard-Block Policy Readiness | Historical — not current |
| 92A | Phase Report Artifact Model | ✅ Complete (superseded by later phase-report work; verify against `docs/ROADMAP.md`) |
| 92B | Pluggable Notification Foundation | ✅ Complete (superseded; verify against `docs/ROADMAP.md`) |
| 92C | Telegram Outbound Phase Report Delivery | ✅ Complete (superseded; verify against `docs/ROADMAP.md`) |
| 92D | Automatic Phase-Finalization Notification Hook | ✅ Complete (superseded; verify against `docs/ROADMAP.md`) |
| 93A | Narrow Shell Gate Design | Historical — not current |
| 93B | Narrow Shell Gate Prototype | Historical — not current |
| 94A | Governed Backend Invocation Design | Historical — not current |
| 95A | Production v1 Documentation / Install / Demo | Historical — not current |
| 96A | Production v1 Governance Review | Historical — not current |

## Future v2 / Pluggability

- Notification adapters (Slack, email, webhook, custom)
- Backend adapters (OpenAI, local models, custom)
- Policy modules (per-repo, per-org, per-workflow)
- Audit storage adapters (remote DB, cloud storage)
- Multi-agent orchestration plugins
- Mobile/operator command gateway (post-broker/shell-gate maturity)
- External packaging/release hardening (PyPI, Homebrew, Docker)

## Design

- Design explicit Phase Activation Governance that separates implementation approval, activation approval, commit approval, and push approval so implemented capabilities cannot be made active by inference.

## Future Explorations

- Automatic low-context detection triggering handoff.
- Compact-risk handoff triggering.
- Automatic governed bootstrap on agent initialization (`pcae session bootstrap`).
- Automatic session restoration from provenance timeline.
- Agent context monitoring and governance-aware context health reporting.
- Automatic AI session restart orchestration after bootstrap.
- True interactive next-agent selection from a configured agent roster.
- Auto-detect available agents from lock history or policy configuration.
- Orchestration-aware agent routing based on task type or governance context.
- Heterogeneous agent governance policies (per-agent policy overrides).
- Vendor-neutral agent flexibility.
- Roadmap/provenance coherence validation.
- ~~Stale roadmap detection.~~ Partially addressed by Phase 112B.1 (`tasks/TODO.md` staleness now surfaced in `pcae session bootstrap --compact`); full `docs/ROADMAP.md` "Current State" table refresh remains open — see 112B.1's Limitations.
- Governance artifact synchronization.
- Orchestration narrative validation.
- Governance drift detection.
