# Phase 149O.20L.7O.3N.2 — Deep Repository-Wide Capability Discovery and Consumption-Gap Audit

**Status:** COMPLETE — read-only. No `src/pcae` modified.
**Phase-entry commit:** `e93af3ce1757238c837b491e9a053fde14af3a5c` (= `origin/main`, clean, 0 ahead)

## 1. Objective

Determine, via a **bottom-up** (not architecture-chapter-organized) repository-wide sweep,
whether the prior conclusion `MATURE CAPABILITY CONSUMPTION PROGRAM: CURRENTLY EXHAUSTED AT
S/M SCOPE` still holds, given the specific concern that **prompt writing / prompt generation**
may be a mature capability missed by prior audits (which were organized around known
architecture chapters). This phase is read-only: no implementation, no v0.4.3 publication.

## 2. Why previous audits were insufficient (as a method, not necessarily as a conclusion)

Phases 3I/3J/3K/3N/3N.1 investigated candidates nominated from architecture-chapter history
(RI→Advisory, Repository Decision/Explainability, Advisory Governance Framework, rollback
evidence visibility). That is recall-limited: a capability implemented under an old chapter
number whose functions no longer appear in current architecture-status prose (e.g. the
`agent.py` "Phase 45F–45O" prompt-generation chain, which predates and is orphaned relative to
the current 149-series numbering) would never surface from a chapter-name search. This phase
instead enumerates capabilities from source structure (module/function/CLI naming, caller
graphs, tests, docs) independent of chapter labels.

## 3. v0.4.3 hold state

Confirmed via Section 4 baseline: `v0.4.3` RC exists only as unpublished local commits/tag
absence. `v0.4.2` remains the latest public release. No tag `v0.4.3` exists locally or on
`origin`. `149O.20L.7O.3O.1` (publication) was **not begun**. Classification:

```
v0.4.3 RC:
TECHNICALLY VERIFIED
PUBLICATION:
STRATEGICALLY HELD PENDING DEEP CAPABILITY AUDIT
```

RC evidence carried forward unchanged from the `3O` canonical report: candidate commit
`63580893b1de4782a694ab802ff7bdebdf29b0e6`; scope = 3M's rollback evidence-visibility
two-file patch only; byte-identical wheel/sdist across two clean-clone builds; BLOCKING=0,
MUST-FIX=0. Not modified this phase.

## 4. Discovery methodology

Bottom-up, not chapter-recycled:
1. Full `src/pcae` module inventory (114 `core/*.py` modules, 60 `commands/*.py` CLI modules,
   plus `advisory/`, `repository_intelligence/`, `interactive_workflow/`, `governance/`,
   `authority_evaluation/`, `cltr*`, `aesic/` — 416 `.py` files total).
2. For every `core/*.py` module, a caller-graph census: is it imported by (a) another
   production package (`core`, `advisory`, `interactive_workflow`, `governance`, `repository_intelligence`,
   `cltr*`, `aesic`), (b) only `commands/*.py` (CLI-only), or (c) neither (candidate orphan)?
   False positives from the caller census (module referenced only via string, or the grep
   pattern missing a real caller) were individually re-verified with a broader grep before
   being trusted.
3. A dedicated, exhaustive keyword sweep for prompt-related naming across `src/pcae`, `docs/`,
   `tests/` (Section 11).
4. Direct reading of the actual implementation (not just names) of every prompt-related
   function found, to determine real vs. advisory/prototype behavior.
5. RI/Historical-Memory consumer sweep reusing and re-verifying the caller-graph technique.
6. README/doc choreography scan for human-copy workflows.
`rg` remains absent in this sandbox (carried-forward known gap, Section 55 of the directive);
`grep -rn`, `find`, and direct source reads were used throughout with no reduction in recall
for the greps actually run.

## 5. Production-module inventory

`src/pcae` groups by behavior (not by phase number) into: CLI command layer (`commands/`, 60
files), core services (`core/`, 114 files spanning task/phase/session lifecycle, HATP/HMIC
hardware trust, permission broker, notifications, phase reporting, git/status probing,
repository identity, memory snapshots, decision evaluation), Advisory (`advisory/`, context
assembly + skills), Repository Intelligence (`repository_intelligence/`, including
`historical_memory/` as a sub-package), Interactive Workflow (`interactive_workflow/`, session/
state-machine/confirmation/preview/evidence/audit/publication-handoff), Governance/publication
(`governance/`), CLTR (`cltr/`, `cltr_prototype/`), AESIC (`aesic/`, decision templates), and
schema packages (`schema_resources/`, `schema_runtime/`). No new top-level grouping was found
that isn't already reflected in this list; the granular finding of interest (Section 9-19)
is a **sub-chapter inside `core/agent.py`**, not a new top-level module.

## 6. CLI-to-service map (representative, not exhaustive per-command)

All 60 `commands/*.py` modules map 1:1 to a CLI subcommand group and call into `core/*.py` (or
their own package) for behavior; none of the 60 command modules implement business logic
inline beyond argument parsing/printing. The caller census (Section 5 methodology) found the
following `core/*.py` modules with **zero non-CLI, non-self production callers** (CLI-only or
orphaned) after re-verification:

`ci`, `commit_push_preflight`, `daemon`, `dry_run`, `enforcement_readiness` (internally wires
`enforcement_approval`/`enforcement_audit`/`enforcement_rollback`, itself CLI-only),
`handoff_verification`, `hooks`, `import_`, `intake`, `mutation_preflight`, `phase`, `pipeline`,
`post_push_canonicalization`, `reporting`, `review`, `runtime_enforcement_safety_authorization`
(true zero-caller — see Section 8).

These are diagnostic/administrative/CLI-leaf commands (health checks, dry-runs, hooks
management, import, review, reporting summaries) — a human invoking `pcae ci`, `pcae review`,
`pcae hooks ...` etc. directly is the intended usage; there is no other PCAE workflow stage
that plausibly needs to auto-invoke a CI summary or a hooks admin command. No confirmed S/M
candidate in this list (all NC — Section "gap taxonomy").

## 7. Zero/one-caller audit

Caller census performed across all 114 `core/*.py` modules (raw counts and methodology in
Section 4/6). Two modules initially appeared to have zero references anywhere and were
individually re-verified by direct source read:

- `core/runtime_enforcement_safety_authorization.py` — confirmed **true zero-caller**.
  Docstring: *"Phase 104C — Shared Runtime Enforcement Safety/Authorization Contract.
  Design-only. Non-executing. Non-authorizing."* Contains only `Final` tuple constant
  definitions (canonical flag-name vocabulary). It is a shared-vocabulary contract reference,
  not a workflow. **Verdict: NC** (not a consumable capability — nothing to "consume", it is a
  frozen naming contract deliberately not wired anywhere).
- All other apparent-zero hits (`enforcement_approval`, `enforcement_audit`,
  `enforcement_rollback`, `human_approval_gate`, `notification_config`,
  `repository_skills_integration`, `advisory_runtime`) were **false positives** of the crude
  grep pattern — each has a real caller once relative-import forms were checked (Section 5).

No genuine unused-but-mature service beyond the one NC case above was found.

## 8. Orphaned mature-module audit

`core/runtime_enforcement_safety_authorization.py` (Section 7) is the only module meeting the
"mature-looking, zero callers" bar (it has a dedicated test file
`tests/test_runtime_enforcement_shared_safety_authorization_contract.py` and originates from a
named phase, 104C). It is **deliberately disconnected by design** — a frozen constants module
documenting flag-name vocabulary shared across other artifacts' *prose*, not a service with
inputs/outputs to wire. Adjudication: not a missing consumer, correctly orphaned.

No other module combining (dedicated contract doc + multi-phase history + large test corpus +
typed result models + persistence + CLI exposure) was found disconnected from all production
callers; the `core/agent.py` prompt-generation chain (Section 9 onward) is the one borderline
case, and it fails the "mature" precondition on inspection (Section 13), not the "orphaned"
one — it is orphaned **and** self-declared non-production-ready.

## 9. Manual choreography audit

`README.md` documents the operator flow: acquire the agent lock
(`pcae session bootstrap --agent-id <agent>`), work under a task, then hand off. The actual
handoff artifact a human moves between stages is the **compact bootstrap prompt** text
produced by `pcae session bootstrap --compact` (backed by `build_bootstrap_prompt`, Section 12)
— a human copies that text into a new agent/terminal session to continue. This is the
concrete, load-bearing "human glue" instance in this repository (see Human-Glue Matrix,
Section "matrices"), and it is precisely the boundary the mandatory prompt deep-dive
(Sections 9–19) had to evaluate.

## 10. Generated-artifact capability audit (selected, high-signal instances)

| Artifact | Generator | Persisted? | Consumer |
|---|---|---|---|
| Compact bootstrap prompt | `build_bootstrap_prompt` (`core/context.py`) | No (ephemeral stdout) | Human, copied into next agent/session |
| Canonical phase report | `core/phase_reports.py` | Yes (`.pcae/phase-reports/`) | `pcae push`/`phase complete` gates (production-consumed) |
| Fast Green attribution artifact | `core/fast_green_attribution.py` | Yes (`.pcae/fast-green-attribution/`) | Canonical report / human review |
| "Autonomous prompt proposal" (45M-series) | `build_autonomous_prompt_proposal` (`core/agent.py`) | Not observed to persist beyond `store_approved_prompt_artifact` on explicit CLI call | CLI display only; no non-CLI consumer found |
| Handoff record (`.pcae/handoffs/`) | `core/session.py` | Yes | `pcae session bootstrap` reads latest handoff (production-consumed) |
| Phase-prompt-capture archive | `run_phase_prompt_capture` (`commands/phase.py`) | Yes (`.pcae/phase-prompts/`) | Human-fed *archival* store (captures a human-authored prompt for audit trail); not a generator, no gap |

## 11. Prompt-writing / Prompt-generation deep dive (mandatory)

Exhaustive keyword sweep (`prompt`, `prompt writer`, `prompt generation`, `prompt builder`,
`instruction builder`, `task prompt`, `system prompt`, `agent prompt`, `execution prompt`,
`phase prompt`, `handoff prompt`, `provider prompt`, `templating`) across `src/pcae`, `docs/`,
`tests/` found prompt-related code in **two functionally distinct, unrelated subsystems**, plus
a documentation-only chapter and an archival capture command:

**(A) `build_bootstrap_prompt`** — `src/pcae/core/context.py:171`, also
`commands/phase.py:2437` (`_build_bootstrap_prompt`, a narrower phase-handoff variant).
Assembles a real, live "compact governed bootstrap prompt" string from `ContextPack` (active
task, governance state, agent-lock state), the latest handoff record, the phase-completion
audit, and `PROJECT_STATUS.md`'s roadmap summary — including explicit phase-identity-ambiguity
detection (Section reading at `context.py:236`). This is exactly what `pcae session
bootstrap --compact` prints and is what every agent in this multi-agent-governance repository
(including this very phase) has been bootstrapped with historically.

**(B) The `core/agent.py` "Phase 45F–45O" prompt-generation/adaptation/validation/governance/
rendering/proposal chain** — `build_prompt_generation_design`, `build_adaptive_prompt_design`,
`build_prompt_validation_design`, `build_prompt_governance_design`, `build_prompt_artifact_design`,
`build_prompt_approval_workflow`, `build_autonomous_prompt_proposal`, `build_prompt_render`,
`build_prompt_execution_readiness`, `build_prompt_execution_dry_run`,
`store_approved_prompt_artifact` (all `core/agent.py`, ~lines 11526–15100+), each backing a
`pcae agent prompt-*` CLI subcommand in `commands/agent.py`.

**(C) `docs/MULTI_AGENT_PROMPT_*` (5 files)** — documentation-only chapter (explicit
"Non-Goals: ... CLI command implementation ... Backend invocation or prompt sending"); no
corresponding `prompt_package` code exists anywhere in `src/pcae` (confirmed zero hits).

**(D) `run_phase_prompt_capture`/`run_phase_activated_task_prompt_capture`/
`run_phase_claude_deepseek_prompt_capture`** (`commands/phase.py`) — archival capture tools:
a human supplies prompt text (`--text`/`--file`/`--stdin`) and PCAE stores it in
`.pcae/phase-prompts/` for audit trail. This is not a generator; it never produces prompt
content itself.

## 12. Prompt-writing caller graph

- **(A) `build_bootstrap_prompt`**: called from `core/context.py` (twice, internally, lines
  367 and 772), `commands/session.py:671`, and `commands/phase.py:1161` (via the narrower
  `_build_bootstrap_prompt` wrapper). **Production-consumed**, not CLI-only — the two internal
  `core/context.py` call sites are themselves invoked as part of the `session bootstrap`
  production code path, not merely printed by a CLI leaf.
- **(B) The 45-series chain**: grep for each `build_prompt_*`/`build_autonomous_prompt_proposal`/
  `store_approved_prompt_artifact` symbol outside `core/agent.py` and `commands/agent.py`
  returned **zero matches**. Confirmed CLI-only, self-referential (each design function calls
  the next design function in the chain, e.g. `build_prompt_render` calls
  `build_autonomous_prompt_proposal`), with no consumer anywhere else in the codebase.

## 13. Prompt-writing maturity

- **(A) `build_bootstrap_prompt`: PRODUCTION.** Deterministic, local, template-based
  (Python f-strings over live `ContextPack`/handoff/roadmap data structures) — no LLM/provider
  call. Has real callers inside the production `session bootstrap` path. No dedicated unit-test
  file found by that exact name, but it is exercised transitively by
  `tests/test_session.py`/`tests/test_context.py`-class suites (session bootstrap is a
  continuously-exercised path across the whole test suite).
- **(B) The 45-series chain: PROTOTYPE**, by its own explicit self-declaration. Direct
  evidence from source (Section 13 reading, `core/agent.py:13276` `build_prompt_render` and
  the `PROMPT_EXECUTION_READINESS_ADVISORY`/`_PER_READINESS_AREAS` block ~line 13400): "Prompt
  Generation" area is rated `readiness_status: "partially_ready"` with explicit listed
  blockers — *"No runtime prompt generation pipeline is deployed"*, *"Agent-specific prompt
  adaptation not yet validated end-to-end"*. The underlying data is **hardcoded synthetic
  content** (`candidate-45M`, `candidate-45N`, `candidate-45O` phase IDs, fixed
  `_APP_PRIORITIES`/`_APP_DEPENDENCY_GRAPH` tuples) unrelated to and never updated for the
  repository's real current phase numbering (now `149O.20L.7O.3N.2`). Every function in this
  chain returns an `advisory` field explicitly stating no execution/approval/adoption occurs.
  This is not merely "unconsumed" — it is a design-only prototype that has never claimed
  production readiness.

## 14. Prompt-writing consumer gap

- **(A)** already answers "is prompt generation currently a mature capability PCAE knows how
  to perform but does not automatically invoke at the point where an agent/task handoff needs
  a prompt?" — **No.** It already IS automatically invoked at exactly that point
  (`session bootstrap`). The remaining gap is not generation but **dispatch**: PCAE produces
  the text; a human still copies it into a new agent process, because PCAE has no execution
  capability (`pcae runtime inspect`: `Runtime status: not_implemented`, `Execution capability:
  unavailable`, `Permission Broker status: execution_unavailable`). Automating that dispatch
  would require granting runtime execution authority — explicitly out of scope for this
  read-only phase and gated by the whole existing HATP/Permission-Broker/Runtime-Enforcement
  fail-closed architecture. **Gap type: TB** (trust/authority block, deliberate,
  pre-existing — not new).
- **(B)** is CLI-only and self-declared non-production; there is no "gap" to close because the
  precondition (a mature capability) is not met. **Gap type: does not qualify as a candidate**
  (fails the maturity leg of the Section 40 acceptance test).

## 15. Prompt generation vs. agent execution

Preserved throughout: (A)'s output is text only; nothing in `build_bootstrap_prompt` or its
callers submits that text to any provider, invokes a subprocess, or activates execution
authority. (B)'s chain likewise only ever returns `dict`s with `advisory`/`human_review_required`
fields; `_derive_command_preview` in `core/agent.py` (line 2869, part of the unrelated Remote
Agent dispatch subsystem, Section 20) constructs a **preview string only**, never executes it.

## 16. Prompt-writing human boundary

For (A): the human must currently read/copy the bootstrap-prompt text and paste it into a new
agent session — this is the entire remaining manual step, and it exists because PCAE
deliberately has no execution authority, not because prompt composition itself is manual.
No legitimate human decision is being removed by this framing; dispatch-authorization is
exactly the kind of decision the project's every prior HATP/Permission-Broker phase has held
must remain human-gated.

## 17. Prompt-writing integration candidates (evaluated, not wired)

`pcae task new`/`task start`/`task finish`: do not call `build_bootstrap_prompt` (task
lifecycle and session bootstrap are separate commands today; the bootstrap prompt is only
produced on demand via `session bootstrap`). `pcae phase` lifecycle: `commands/phase.py`
already has its own narrower `_build_bootstrap_prompt` wrapper used at phase-boundary points
(`phase.py:1161`). Producer intake / agent handoff / advisory / RI context / codex-ox session
path: none of these currently call `build_bootstrap_prompt` or consume its output. This
matches Section 26 (RI consumer sweep) — RI is not an input to the bootstrap prompt at all
today.

## 18. Prompt-writing runtime-neutrality

**(A)** is fully deterministic/local/template-based — confirmed by direct source read, no
network or provider call present. **(B)** is also deterministic/local (no LLM call), but its
inputs are hardcoded constants, not live state, so "runtime-neutral" is true but not
meaningful for a prototype that isn't reading real state to begin with.

## 19. Prompt artifact identity/provenance

**(A)**'s output is ephemeral (printed, not persisted with its own identity/version) — it is
regenerated fresh on every `session bootstrap` call from current live state, so
freshness/staleness is structural (it's always current) rather than something requiring a
version field. **(B)**'s `store_approved_prompt_artifact` does persist an artifact with an
explicit `prompt_id`, but nothing downstream ever reads it back except
`lookup_approved_prompt_artifact` (same CLI-only chain) — no freshness gap beyond the fact
that the whole chain is prototype-only.

## 20. Agent handoff capability audit

Separately from prompts: `core/agent.py`'s "Remote Agent" dispatch subsystem
(`build_remote_dry_run`, `persist_remote_job`, `_build_invoke_command`,
`_derive_command_preview`, lines ~2178–3200) builds real invocation command previews
(`claude -p '<prompt>'`, `codex exec --sandbox ... '<prompt>'`, `kimi -p '<prompt>'`) for a
`requested_task` string a human supplies via CLI — this is invocation **preview/dry-run**
tooling, not prompt generation; the `requested_task` prompt content itself is always
human-supplied to this subsystem, never generated by it. It is intentionally preview-only
(explicit `_REMOTE_DRY_RUN_...` advisory strings: "no agent was executed and no prompt was
submitted"). No new gap: this is consistent, deliberate CLI-only tooling for human-operated
remote-agent dispatch under a non-executing runtime posture.

## 21. Planning capability audit

`build_autonomous_phase_proposal` (`core/agent.py:12794`, feeds the 45-series prompt chain)
generates candidate phases from `build_roadmap_evidence`, but its candidate list
(`_APP_PRIORITIES`, `_APP_DEPENDENCY_GRAPH`) is the same hardcoded `candidate-45M/45N/45O` set
found in Section 13 — a frozen prototype output, not a live planner. No separate,
currently-mature planning capability was found beyond this prototype and the human-authored
`PROJECT_STATUS.md`/phase-doc "Recommended next phase" prose that every governed phase already
writes (which is the actual mechanism `session bootstrap`'s roadmap summary reads).

## 22. Task transformation/scaffolding audit

`pcae task new` (human-invoked, `core/tasks.py`) is the only issue→task transform; there is no
task→phase, phase→agent-instruction, evidence→task-update, or report→next-action *automatic*
transform found — each of those transitions is currently human-authored prose (the phase
document's own "Recommended next phase" section, hand-written per phase, exactly as this
document does). This is consistent with every prior phase's practice and is the same
human-authorship pattern already relied upon throughout the project; no new mature-but-orphaned
transformer was found.

## 23. Context assembly audit

Context builders found: `core/context.py` (`ContextPack`/session context, feeds the bootstrap
prompt), `advisory/context/advisory_context_builder.py` (feeds Advisory/RI, per 3J/3J.1/3K),
`core/memory_snapshot.py` (session/history context), `core/repository_identity.py` (repo
identity context). All four have real, distinct production consumers already (session
bootstrap, Advisory, memory-snapshot CLI+internal callers, repository-identity's 8 internal
callers per the Section 5 caller census). No context builder was found that is only
manually invoked with no production caller.

## 24. Review/explanation generation audit

`commands/review.py` (CLI-only per Section 6) and `core/decision_evaluation.py`/
`core/repository_transition_validator.py` (already the subject of `3N.1`'s finding, carried
forward unchanged — `TransitionResult.explanation` produced but not fully surfaced; not
reopened here, no new evidence found this phase). No new review/explanation generator beyond
what `3N.1` already catalogued was discovered.

## 25. Memory/history consumption audit

Historical Memory (`repository_intelligence/historical_memory/`) is consumed only through RI's
own query layer, same finding as prior phases — no separate task/prompt/planning-workflow
caller was found bypassing RI's query layer to use Historical Memory directly, and none of
Sections 11-21's prompt/planning capabilities call into RI or Historical Memory at all
(confirmed: `core/context.py`, `core/agent.py`'s 45-series chain, and
`core/tasks.py` have zero `repository_intelligence` imports).

## 26. Repository Intelligence consumer sweep

Repeated (not assumed from memory) via direct grep this phase: `repository_intelligence` is
imported, outside its own package and tests, only by `cli.py`, `core/advisory.py`, and the
`advisory/context/*` package (5 files). Prompt writing, task planning, phase planning, review
preparation, and agent handoff (Sections 11-24) all have **zero** RI imports. This reconfirms,
via a fresh bottom-up import sweep rather than a recalled conclusion, the `3J.1`/`3K` finding
that RI feeds Advisory only. **Gap type: CG**, carried forward unchanged, not reopened (matches
`3K`'s explicit decision not to reopen this boundary without a new contract).

## 27. Cross-capability composition discovery

Evaluated pairs: RI → Prompt Writer (unconsumed, Section 26 — CG, not new); Task → Prompt
Writer (Section 17 — `build_bootstrap_prompt` does not read task-specific detail beyond
`active_task.id/title`, which is arguably sufficient for its purpose as a session/handoff
prompt rather than a task-instruction prompt — NG, no meaningful gap for its actual purpose);
Prompt Writer → Agent Handoff (Section 14 — TB, deliberate, execution-authority-gated);
Historical Memory → Planning (Section 21/25 — no live planner exists to receive it; N/A, no
planning capability mature enough to be a consumer).

## 28. Producer/intake reverse-path audit

Inbound generic producer intake (`core/intake.py`, `commands/intake.py`) is mature and CLI-
exposed (per prior phases' work, e.g. 2X Codex-Ox intake). The outbound side — "PCAE → prepare
task/prompt/context → external producer" — is exactly `build_bootstrap_prompt`
(Section 11-14): it exists, is production-consumed for session handoff, but does not itself
package a *task-specific* instruction bundle for a specific external producer (it is
identity-agnostic — same text regardless of which agent will receive it). This is a real,
narrow observation but does not by itself meet the Section 40 acceptance bar: there is no
identified production workflow B that currently needs a producer-specific outbound package and
is blocked only by human glue — the only current outbound need (generic session handoff) is
already served. **Gap type: NG.**

## 29. Agent identity vs. handoff analysis

`claude-local`, `codex`, `codex-ox`, and custom identities are registered in
`core/agent.py`'s `AgentEntry`/adapter registry and are used descriptively (lock ownership,
adapter capability lookup, Remote Agent dry-run command-string construction — Section 20). No
prompt-generation logic branches on agent identity to produce agent-specific content in the
production path; the 45-series prototype (Section 11B) does have an "adaptive prompt" concept
keyed by agent identity, but it is the same non-production prototype already classified in
Section 13. No execution was introduced or implied by this review.

## 30. Session/bootstrap capability sweep

`pcae session bootstrap` (both `--compact` and `--agent-id` forms) already produces: governance
state, active task, latest handoff, phase-completion audit summary, roadmap summary
(`PROJECT_STATUS.md`-authoritative, `tasks/TODO.md` staleness cross-check with explicit
"PROJECT_STATUS.md is authoritative" language per Section 224-ish of `context.py`), and
phase-identity-ambiguity detection. All of these outputs are consumed (printed to the invoking
agent and read directly, as happened at the start of this very phase). No output found that
is generated but silently discarded.

## 31. Reporting lifecycle reverse-consumption audit

No new instance found beyond the already-known `3N.1` finding
(`TransitionResult.explanation`, Section 24). Canonical phase reports feed `pcae push`/
`phase complete` gates already (production-consumed); no report→prompt or report→handoff
auto-transform exists, but the only place that would matter (session bootstrap's handoff
summary) already reads the *prior* handoff record directly rather than needing a new
transform.

## 32. Typed-result unread-field audit

No new unread-field instance beyond `3N.1`'s carried-forward finding was identified this phase
within the time available; a full field-by-field sweep of every typed result class in 416
files was not performed exhaustively (see honesty note, Section "exhaustion verdict").

## 33. Persisted-artifact reader/writer audit

`.pcae/phase-reports/` (writer: `phase_reports.py`; reader: `push`/`phase complete` gates —
production-consumed), `.pcae/fast-green-attribution/` (writer:
`fast_green_attribution.py`; reader: canonical report + human — VG, visibility not
consumption, consistent with prior phases), `.pcae/handoffs/` (writer: `core/session.py`;
reader: `session bootstrap`'s handoff-summary code path — production-consumed), `.pcae/
phase-prompts/` (writer: `run_phase_prompt_capture`; reader: `run_phase_prompt_show`/`list` —
CLI-only archival, NC, correctly so since it's an audit trail not a generator).

## 34. Tests-as-capability-discovery

`tests/test_agent.py`, `tests/test_phase.py`, `tests/test_session.py` contain the prompt-
related test coverage; none of them assert that the 45-series chain is called from any
non-CLI production path (consistent with Section 12's caller-graph finding). No production
capability was found via test-name discovery that hadn't already surfaced from the module/CLI
sweep.

## 35. Documentation-as-capability-discovery

`docs/CAPABILITY_INVENTORY.md` and the five `MULTI_AGENT_PROMPT_*` docs were the main hits;
all five `MULTI_AGENT_PROMPT_*` docs are confirmed documentation-only (Section 11C, explicit
"Non-Goals: CLI command implementation"). `docs/CAPABILITY_INVENTORY.md` was read for
cross-check; it does not list a distinct capability beyond what Sections 5-9 already found.

## 36. Git-history supplemental discovery

The 45-series prompt chain's own docstrings/comments (`Phase 45F`, `45G`, `45H`, `45M`, `45M.1`,
`45N`) were the git-history signal that led to Section 11's discovery in the first place —
these phase numbers do not appear anywhere in the current `PROJECT_STATUS.md` architecture
status prose (which starts its detailed numbering much later), exactly the "names no longer
appear prominently in current architecture status" scenario the directive anticipated. History
was used to improve recall, not as the primary oracle, per the directive's constraint.

## 37. Public package surface audit

`pcae agent prompt-*`, `pcae agent autonomous-prompt-proposal`, `pcae agent prompt-render`,
etc. are real, user-invocable commands. Per Section 13B, they are self-declared
non-production-ready; a user *can* invoke them manually today, and the answer to "should PCAE
itself ever invoke this" is **NO** for this specific case, on the direct evidence that the
underlying data has never been wired to real state.

## 38. "No production caller" candidate list (mandatory)

See Section 6 for the full list (14 CLI-only `core/*.py` modules) plus the 45-series prompt
chain (CLI-only within `core/agent.py`/`commands/agent.py`, Section 12). Adjudication for each
is NC (diagnostic/admin/human-leaf, no plausible internal consumer) except the 45-series chain,
which is adjudicated PROTOTYPE (fails the maturity precondition, not merely "orphaned").

## 39. "Human glue" candidate list (mandatory)

| Workflow | A | Human transfer | B | Automatable? |
|---|---|---|---|---|
| Agent handoff | `build_bootstrap_prompt` output | Human copies text into new agent/terminal session | New agent process | No — blocked by deliberate absence of execution authority (TB), not by missing generation |
| Remote-agent dry-run → real invocation | `build_remote_dry_run` preview | Human reviews preview, then separately runs the real command | Actual agent subprocess | No — same TB boundary, and this is explicitly preview-only tooling |
| Phase→next-phase recommendation | Phase document "Recommended next phase" prose (human-authored) | Human reads it, decides, and (for governed continuation) invokes the next `pcae task new`/`phase start` | Next governed phase | Partially — `session bootstrap`'s roadmap-summary already surfaces the recommendation automatically; only the decision-to-proceed and the `task new` invocation remain human, which is intentional (human governance authority, not a capability gap) |

## 40. Consumption-vs-visibility adjudication

Every candidate considered in Sections 6-39 was run through the Section 40/41 acceptance
tests. None passed all eight legs of the Section 40 test (existing capability A + existing
workflow B needing A's result + human glue + existing-contract support + no new authority +
no execution activation + S/M + E2E-testable) with a **new** finding — the one candidate that
comes closest (prompt dispatch, Section 14/39) fails specifically on "no new authority
semantics", since closing it would require exactly the runtime-execution authority this
project's entire governance architecture has deliberately withheld through every HATP/
Permission-Broker/Runtime-Enforcement phase to date.

## 41. Capability-universe matrix

| Capability | Module/service | Tests/contracts | CLI/API | Non-CLI consumers | Manual glue | Gap type | Candidate? |
|---|---|---|---|---|---|---|---|
| Session bootstrap prompt composition | `core/context.py: build_bootstrap_prompt` | transitive (session/context suites) | `session bootstrap --compact` | `core/context.py` internal, `commands/session.py`, `commands/phase.py` | Human copies output into new session | TB (dispatch only) | No — already AC for generation |
| 45-series prompt generation/adaptation/validation/governance/rendering/proposal | `core/agent.py` (Phase 45F-45O) | `tests/test_agent.py` | `pcae agent prompt-*` | none | N/A (prototype) | N/A | No — fails maturity bar |
| Phase-prompt capture/archive | `commands/phase.py` | `tests/test_phase.py` | `pcae phase prompt-capture/show/list` | none (archival) | Human supplies content | NC | No |
| Remote-agent dry-run preview | `core/agent.py` remote-dispatch subsystem | `tests/test_agent.py` | `pcae agent remote-*` | none | Human runs real command separately | TB | No |
| RI → Advisory | `core/advisory.py`, `advisory/context/*` | extensive (3J/3J.1) | `pcae advisory ...` | `core/advisory.py` internal | n/a | AC | No (already consumed) |
| RI → other reasoning (prompt/plan/review) | — | — | — | none | n/a | CG (carried forward) | No (already decided, not reopened) |
| `runtime_enforcement_safety_authorization` | `core/runtime_enforcement_safety_authorization.py` | `tests/test_runtime_enforcement_shared_safety_authorization_contract.py` | none | none | n/a | NC | No |
| Canonical phase report | `core/phase_reports.py` | extensive | `pcae phase-reports ...` | `push`/`phase complete` gates | n/a | AC | No |
| Handoff record | `core/session.py` | extensive | `pcae session ...` | `session bootstrap` | n/a | AC | No |

## 42. Zero/one-caller matrix

| Service | Production callers | Test callers | CLI caller | Why apparently orphaned | Verdict |
|---|---|---|---|---|---|
| `runtime_enforcement_safety_authorization` | 0 | yes | none | Deliberate constants-only contract module | NC — correctly orphaned |
| `ci`, `commit_push_preflight`, `daemon`, `dry_run`, `enforcement_readiness`, `handoff_verification`, `hooks`, `import_`, `intake`, `mutation_preflight`, `phase`(core), `pipeline`, `post_push_canonicalization`, `reporting`, `review` | 0 | yes (each has tests) | 1 (own CLI command) | Human-operated diagnostic/admin leaves | NC — no plausible internal consumer |
| 45-series prompt chain functions | 0 | yes | 1 (`pcae agent prompt-*`) | Self-declared prototype, hardcoded stale data | Fails maturity bar, not a candidate |

## 43. Generated-artifact matrix

See Section 10's table (reused here as the required matrix); no additional rows found beyond
that table during the broader sweep.

## 44. Human-glue matrix

See Section 39's table (reused here as the required matrix).

## 45. Confirmed candidates

**None.** No capability in this sweep passed the Section 40 acceptance test as a new genuine
S/M consumption-gap candidate. The one candidate that most resembled the user's premise
(prompt writing) resolved, on direct evidence, into: a capability already consumed in
production (`build_bootstrap_prompt`) plus a self-declared non-production prototype (the
45-series chain) — neither is a genuine gap.

## 46. Rejected candidates

- 45-series prompt-generation chain → rejected: fails maturity precondition (self-declared
  prototype, hardcoded stale data, zero non-CLI callers).
- Prompt dispatch automation (bootstrap prompt → auto-invoked agent) → rejected: requires new
  runtime-execution authority (TB), out of scope, not S/M in the authority-safety sense even if
  it might be S/M in raw code size.
- RI → Prompt Writer / RI → Planning composition → rejected: carried-forward CG, already
  adjudicated in `3K`, not reopened absent a new contract decision.
- Outbound producer-specific prompt packaging → rejected: no identified blocked production
  workflow B (Section 28), NG.
- Remote-agent dry-run → real invocation → rejected: same TB boundary as bootstrap-prompt
  dispatch, and the tooling is explicitly preview-only by design.

## 47. Candidate ranking

Not applicable — zero confirmed candidates to rank.

## 48. Exhaustion falsification attempt (mandatory)

1. *What useful production service has no caller?* — `runtime_enforcement_safety_authorization`
   only; adjudicated NC (Section 7/8).
2. *What CLI command's service is never internally called?* — The 14-module list in Section 6,
   plus the 45-series chain; all adjudicated NC or prototype (Section 38).
3. *What generated artifact is manually copied?* — The session-bootstrap prompt (Section 9/39);
   adjudicated TB, not a new gap (deliberate authority boundary).
4. *What result field is never consumed?* — `TransitionResult.explanation`, carried forward
   unchanged from `3N.1`, not reopened; no new instance found this phase within budget
   (Section 32 honesty note).
5. *What two mature workflows rely on human glue?* — Bootstrap-prompt → new agent session; and
   phase-recommendation prose → next `task new` invocation (Section 39); both adjudicated
   intentional human-governance boundaries, not automatable without new authority.
6. *What agent/handoff preparation remains manual?* — Dispatch of the bootstrap prompt into a
   live agent process (Section 14/16); intentional TB.
7. *What context builder is only manually invoked?* — None found; all four context builders
   identified (Section 23) have real production callers.
8. *What capability tests exist without production integration?* — The 45-series prompt chain
   (`tests/test_agent.py`); adjudicated prototype, not a gap.
9. *What mature module is disconnected by design but no longer needs to be?* — None found;
   `runtime_enforcement_safety_authorization` is a vocabulary contract, not a workflow, so
   "connecting" it has no meaning.
10. *What previously undocumented feature exists?* — The 45-series prompt-generation/adaptation/
    validation/governance/rendering/approval/proposal chain itself was the main previously-
    undocumented (in current architecture-status prose) feature surfaced this phase — fully
    documented here (Sections 11-19) and correctly resolved as non-actionable.

## 49. Exhaustion verdict

```
DEEP REPOSITORY-WIDE CAPABILITY AUDIT:
COMPLETE
MATURE S/M CONSUMPTION GAPS:
NONE
PRIOR EXHAUSTION CONCLUSION:
RECONFIRMED AFTER BOTTOM-UP AUDIT
```

Scope honesty note: this reconfirmation rests on (a) a full caller-graph census of all 114
`core/*.py` modules, (b) an exhaustive, source-level (not name-only) mandatory prompt-writing
deep dive that found and correctly resolved a previously-undocumented prototype chapter, (c) a
fresh RI-consumer import sweep, (d) an orphan/zero-caller module audit, and (e) a documented
falsification attempt across all ten Section 49-directive questions. It does **not** claim a
literal field-by-field read of every typed result class in all 416 files, nor a manual
end-to-end walk of every one of the 60 CLI commands' full internal call graphs — those would
require materially more time than this phase budget allows. The one area most likely to still
harbor an undiscovered instance is Section 32 (typed-result unread-field sweep), which was only
partially performed. This is disclosed rather than glossed over, consistent with the standard
set in prior 3J.1/3K/3N.1 phases of not overclaiming exhaustiveness.

## 50. v0.4.3 release decision

No meaningful S/M candidate was found (Section 45/49). Per the directive's Section 51 logic:
**recommend proceeding with v0.4.3 publication.** There is no candidate to compare against a
"hold and bundle" alternative, and no version-scope reassessment is needed — v0.4.3's already-
frozen scope (3M's rollback evidence-visibility patch) remains correct and complete. Prompt
writing itself is not high-value-S/M-unimplemented (Section 13B/49): the mature half of it is
already shipped and consumed; the immature half is correctly un-shipped. No comparison against
"releasing 3M visibility alone" is needed since 3M's visibility change is already the entire
v0.4.3 content — nothing new to add or hold back.

## 51. Plan A — Best immediate integration

**No implementation action recommended.** The best "immediate integration" available is
procedural, not code: authorize `149O.20L.7O.3O.1` to publish the already-frozen, already-
verified v0.4.3 release candidate (tag, GitHub Release, optionally PyPI per separate
authorization). This requires no new code, carries the lowest risk of any option evaluated,
and closes out the open release-hold created by this phase and by `3N`/`3N.1`/`3O`.

## 52. Plan B — Best agent/handoff workflow improvement

If the human elects to invest in agent/handoff orchestration despite no confirmed gap: the
only evidence-backed candidate improvement is closing the TB boundary identified in Sections
14/39 (auto-dispatch of the bootstrap prompt to a live agent process) — but this is explicitly
**not recommended** as an S/M item, since it requires new runtime-execution authority, which
is a Runtime/Trust/Authority-architecture decision (out of scope for an S/M consumption-gap
closure and out of scope for this read-only phase). If pursued at all, it belongs in a future
Runtime/Provider Architecture phase (consistent with the `3O`/prior-phase "Recommended next
phase" guidance already on record), not as a capability-consumption patch.

## 53. Plan C — Broader strategic bundle

No broader strategic bundle is justified by this phase's findings — there is nothing
confirmed to bundle. Should the human instead want to retire the 45-series prototype chain
(Section 13B) as dead/misleading surface area (it self-reports non-production-readiness but
remains reachable via `pcae agent prompt-*`), that would be a documentation/deprecation
decision, not a consumption-gap closure, and is offered here only as an optional, separately-
authorizable follow-up — not a recommendation of this phase.

## 54. Recommendation

Publish v0.4.3 via `149O.20L.7O.3O.1` (Plan A) under separate explicit human authorization.
Do not pursue Plan B without a dedicated Runtime/Provider/Trust-authority phase. Do not pursue
Plan C unless the human independently wants prototype-surface cleanup; it is optional and
unrelated to the release decision.

## 55. Human decision required

Authorize (or decline) `149O.20L.7O.3O.1` — v0.4.3 publication (tag push, GitHub Release
creation; PyPI upload remains separately unauthorized regardless). No other decision is
pending from this phase's findings.
