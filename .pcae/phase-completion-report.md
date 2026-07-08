# Phase 118E Complete - Advisory Reasoning Expansion Architecture

- **Phase ID:** `118E`
- **Status:** completed
- **Report completeness:** complete
- **Missing trust fields:** none
- **Files changed:** 9
- **Tests run:** governance validation only
- **Commits:** pending governed commit
- **Pushed:** pending
- **origin/main..HEAD:** pending

## Summary

Phase 118E defines Advisory Reasoning Expansion as the architecture by
which PCAE Advisory may eventually consume deterministic,
source-attributed Repository Intelligence context to produce better
explanations, recommendations, uncertainty statements, evidence-gap
summaries, reasoning traces, and structured handoff context.

The phase strengthens Advisory reasoning quality without increasing
Advisory authority. Advisory may become more informed. Advisory must
not become a decision maker, execution planner, permission broker,
enforcement layer, lifecycle authority, model orchestration system, or
repository mutation mechanism.

## Architecture Produced

- Created `docs/PHASE_118_ADVISORY_REASONING_EXPANSION_ARCHITECTURE.md`.
- Defined Advisory Reasoning Expansion and its Track B role.
- Distinguished expanded Advisory from current Advisory, Decision
  Evaluation, model inference, autonomous planning, Repository State,
  Evidence, Repository Skills, and execution.
- Defined core primitives: Advisory Claim, Advisory Explanation,
  Advisory Recommendation, Advisory Context Item, Advisory Context
  Package, Advisory Evidence Link, Advisory Source, Advisory
  Uncertainty, Advisory Limitation, Advisory Reasoning Trace, Advisory
  Knowledge Reference, Advisory Historical Reference, Advisory Impact
  Reference, Advisory Graph Reference, Advisory Handoff, and Advisory
  Report.
- Defined advisory input, output, reasoning trace, source attribution,
  uncertainty, recommendation, and handoff models.
- Defined integrations with Repository Knowledge, Historical Memory,
  Change Impact Analysis, Dependency Knowledge Graph, Evidence,
  Repository Skills, Advisory Context Packages, and Decision Evaluation.
- Preserved the read-only, non-authoritative, no-execution boundary.

## Advisory Reasoning Expansion Definition

Advisory Reasoning Expansion is the architecture by which PCAE Advisory
may consume deterministic, source-attributed Repository Intelligence
context to produce better explanations, recommendations, uncertainty
statements, evidence-gap summaries, and structured handoff context while
remaining read-only and non-authoritative.

## Conceptual Boundaries

Advisory vs Decision Evaluation:
Advisory explains, recommends, preserves uncertainty, identifies
evidence gaps, and packages context. Decision Evaluation remains the
only component responsible for allow/block/escalate/more-evidence
decisions.

Advisory vs model inference:
Advisory may use model-produced content only as advisory/probabilistic
evidence or explanation. Hidden model state, prompt wording,
conversation memory, and model confidence are not canonical sources of
truth.

Advisory vs autonomous planning:
Advisory may recommend review, evidence collection, or inspection. It
must not produce authoritative executable plans, patch plans,
refactoring plans, shell-command plans, commit/push plans, or lifecycle
transition plans.

## Core Primitives Summary

Expanded Advisory uses source-attributed advisory claims,
human-readable explanations, non-authoritative recommendations,
bounded context items/packages, evidence links, sources, uncertainty,
limitations, reasoning traces, Repository Knowledge references,
Historical Memory references, Change Impact Analysis references,
Dependency Knowledge Graph references, structured handoffs, and
advisory reports.

## Advisory Input Model Summary

Advisory may later receive structured context from Repository Knowledge,
Historical Memory, Change Impact Analysis, Dependency Knowledge Graph,
Evidence, Repository Skills, Advisory Repository Skills, Advisory
Context Packages, and canonical lifecycle artifacts.

Inputs must preserve source attribution, trust class, determinism,
freshness, confidence, and limitations where available.

## Advisory Output Model Summary

Expected outputs include explanations, recommendations, risk summaries,
uncertainty statements, evidence gaps, impact summaries, dependency
summaries, historical lineage summaries, contract implication summaries,
test implication summaries, documentation implication summaries,
governance context summaries, and handoff to Decision Evaluation.

All outputs are advisory-only context, not authorization.

## Advisory Reasoning Trace Model Summary

A reasoning trace records the advisory question and scope, context used
and excluded, sources referenced, relationships followed, dependency
paths considered, historical facts considered, impact claims
considered, evidence gaps, uncertainty, conflicts, stale or superseded
knowledge, limitations, recommendations, and what Advisory did not
decide.

## Source Attribution Summary

Every advisory claim, explanation, recommendation, reasoning trace, and
handoff item must link to sources when support exists: source files,
tests, docs, architecture documents, contract documents, verification
documents, phase reports, phase-completion metadata, changelog entries,
task records, release notes, tags, commits, evidence artifacts,
Repository Skills, Advisory Repository Skills, Advisory Context
Packages, canonical lifecycle artifacts, and no-go boundary documents.

## Uncertainty Model Summary

Advisory records known, unknown, unverified, partially verified,
conflicting, stale, superseded, inferred, advisory-only, and
decision-required states. False certainty is avoided through explicit
labels, limitations, source attribution, and evidence-gap reporting.

## Recommendation Model Summary

Advisory may recommend review, evidence collection, test inspection,
documentation review, contract review, historical review, graph/impact
verification, or Decision Evaluation input. It must not say an action is
authorized, allowed, approved, accepted, ready for execution, ready for
commit/push, valid for lifecycle transition, or safe for artifact
promotion.

## Handoff to Decision Evaluation Summary

Advisory Handoff packages claims, recommendations, source references,
evidence links, evidence candidates, Repository Knowledge references,
Historical Memory references, Change Impact Analysis references,
Dependency Knowledge Graph references, uncertainty, conflicts, stale or
superseded context, limitations, and required evidence. It carries an
explicit non-decision disclaimer.

Decision Evaluation may consume conforming Evidence derived from a
handoff. The handoff itself is not a verdict.

## Integration Summaries

Repository Knowledge integration:
Advisory consumes structured architectural entities, relationships,
claims, sources, snapshots, and views without becoming a knowledge
extractor or authority.

Historical Memory integration:
Advisory uses lineage, phases, decisions, repairs, hardening, releases,
corrections, and supersession to explain why a boundary exists and how
it evolved.

Change Impact Analysis integration:
Advisory uses impact subjects, surfaces, paths, claims, blast radius,
unknowns, and evidence gaps to recommend review without deciding.

Dependency Knowledge Graph integration:
Advisory uses graph paths, reverse dependencies, dependency types, edge
direction, graph views, snapshots, and uncertainty states to make
explanations traceable without building or mutating the graph.

Evidence integration:
Advisory references Evidence, identifies evidence gaps, and may later
produce advisory/model-produced Evidence through existing advisory
skill boundaries. Advisory evidence remains probabilistic/advisory by
default and never sole authority for Accept.

Repository Skills integration:
Future Repository Skills may expose advisory-ready Repository
Intelligence context, but remain evidence producers only.

Advisory Context Package integration:
Repository Intelligence context must enter packages as bounded,
labelled, provenance-preserving context with redaction, trust-class
separation, limitations, and prompt-injection protection.

Decision Evaluation integration:
Advisory supports decisions only indirectly through structured context
or conforming Evidence. Decision Evaluation remains the only
decision-making component.

## Boundary Confirmations

- Decision Evaluation remains the only component responsible for
  allow/block/escalate/more-evidence decisions.
- Repository Transition Validator remains the canonical transition gate.
- Advisory remains explanatory, recommendation-oriented,
  evidence-linked, read-only, and non-authoritative.
- Execution remains unavailable.
- Runtime state remains `Observed`.
- Maximum runtime capability remains `observe`.

## Non-Goals Confirmed

This phase did not implement:

- advisory behavior changes
- advisory runtime changes
- advisory context package changes
- advisory CLI
- advisory reasoning engine
- model integration
- model selection
- provider orchestration
- repository knowledge extraction
- historical memory extraction
- change impact analysis engine
- dependency graph construction
- graph query engine
- evidence subsystem changes
- repository skills changes
- decision evaluation changes
- execution
- shell mediation
- Permission Broker changes
- lifecycle redesign
- REST
- Dashboard
- Web UI
- Telegram inbound
- autonomous coding
- model capability expansion
- repository mutation
- runtime plugin changes
- repository state changes
- test execution through advisory
- automatic patch generation
- automatic refactoring

## Governance Results

- `pcae health`: healthy during pre-commit validation
- `pcae check`: passed during pre-commit validation
- `pcae doctor task-memory`: clean during pre-commit validation
- `pcae push check`: nothing_to_push before commit; final push pending
- `pcae runtime inspect`: execution unavailable, Observed, observe, zero
  runtime plugins
- `pcae notify status`: Telegram configured, enabled, ready for outbound
  delivery after sourcing environment
- `pcae skill invoke phase-finalization 118E`: target resolved;
  invocation is preview-only in current lifecycle

## Validation Results

- Architecture scope check: passed; no `src/` or `tests/` changes.
- Documentation section check: passed.
- Full implementation test suite: not run; architecture-only phase with
  no source or test changes.
- Fast green: not run; not applicable for architecture-only docs unless
  lifecycle requires it.

## Notification Detail

The latest 118D report retained a `pending_final_telegram_delivery`
metadata field, but 118D manual Telegram `send-report --latest`
succeeded after completion. This is recorded as inherited report
metadata, not a 118E blocker.

## Recommended Next Phase

118R - Repository Intelligence Architecture Review

118A through 118E define the major Track B architecture surfaces. Before
freezing contracts or prototyping, PCAE should review coherence across
Repository Knowledge, Historical Memory, Change Impact Analysis,
Dependency Knowledge Graph, and Advisory Reasoning Expansion.

## Report Consistency

- **Canonical report:** pending `pcae phase complete` promotion
- **Metadata:** present
- **Status:** consistent

---
*Report generated for PCAE Phase 118E. Schema version 1.0.*
