# Phase 115Z — Advisory Subsystem Hardening & Release Readiness

## Purpose

Complete and harden the entire Advisory subsystem introduced across
Phases 115P–115Y, proving it is internally consistent, fully
contained, architecturally complete, and ready to become a stable v0.2
subsystem. This is a consolidation and hardening phase only: no new
feature, no new evidence provider, no new Repository Skill, no new
Advisory Provider, no second Advisory Provider, and no modification to
Decision Evaluation, the Repository Transition Validator, any
lifecycle command, Notification Policy, or the Repository State
Kernel. No execution, authorization, Permission Broker enforcement,
plugin, Telegram inbound, REST, Dashboard, or Web UI implementation is
added.

## Scope Boundary — Two Unrelated Pre-Existing "Advisory" Subsystems

Before reviewing anything, this phase confirms a scoping fact that
must not be lost in future consolidation work: the codebase contains
**three** distinct systems that use the word "advisory," only one of
which is in scope for 115P–115Y and this hardening phase.

| Module | Phase | Subject | In scope for 115Z? |
|---|---|---|---|
| `src/pcae/core/advisory.py` | 88X | Read-only, non-authorizing "Advisory mode" — a would-* decision layer over Permission Broker / shell-gate evidence | No |
| `src/pcae/core/advisory_runtime.py` | 113C | Observation-only "Advisory Runtime" — runtime capability advisory results | No |
| `src/pcae/core/advisory_repository_skills.py`, `src/pcae/core/current_acting_model_advisory_provider.py`, `src/pcae/core/advisory_context_package.py` | 115P–115Y | **Advisory Repository Skills** — bounded, evidence-only AI advisory input into the Decision Evaluation pipeline | **Yes** |

These three subsystems share no code, no shared base class, and no
runtime coupling. `tests/test_phase_115z_advisory_subsystem_hardening.py`
scopes every check to an explicit three-module allowlist
(`ADVISORY_SUBSYSTEM_MODULES`), never a `*advisory*` glob, specifically
to avoid conflating this subsystem's hardening with the unrelated
88X/113C systems.

## 1. Architectural Review Summary (Objective 1)

Reviewed every one of the ten phase reports (115P–115Y) and six
canonical architecture/contract documents
(`PCAE_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md`,
`PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md`,
`PCAE_ADVISORY_PROVIDER_STRATEGY.md`,
`PCAE_ADVISORY_EVIDENCE_ENRICHMENT.md`,
`PCAE_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md`, plus the 115R prototype
doc) against the three real runtime modules.

**Responsibilities are clearly separated, with no duplication:**

| Responsibility | Owner | Verified single-definition |
|---|---|---|
| Advisory question / skill invocation surface | `AdvisoryRepositorySkill` (extends `RepositorySkill`) | one concrete subclass: `RepositoryConsistencyAdvisorySkill` |
| Prompt assembly | `build_advisory_request()` | defined exactly once |
| Backend-agnostic provider contract | `AdvisoryProvider` (abstract, one method: `invoke`) | two conforming implementations: `MockAdvisoryProvider` (test/prototype fixture), `CurrentActingModelAdvisoryProvider` (the one real provider) |
| Response normalization | `normalize_advisory_response()` | defined exactly once |
| Evidence construction from a normalized response | `build_evidence_from_normalized()` | defined exactly once |
| Bounded context assembly (not yet wired into the pipeline) | `AdvisoryContextPackage` | standalone, zero internal imports |

**No hidden coupling.** None of the three modules is imported by
`decision_evaluation.py`, `repository_transition_validator.py`, any
`pcae.commands.*` lifecycle command, `notification_certification.py`,
`handoff_verification.py`, `post_push_canonicalization.py`,
`runtime_inspect.py`, `repository_skills_integration.py`, or
`repository_transition_integration.py`. Confirmed by direct source
grep across all nine of those modules — zero references either
direction.

**No circular dependencies.** The dependency graph is one-directional
and terminates in the standard library:

```
advisory_context_package.py   (zero pcae-internal imports — pure stdlib: dataclasses, types, typing)
advisory_repository_skills.py -> evidence.py, paths.py, repository_skills.py
current_acting_model_advisory_provider.py -> advisory_repository_skills.py, evidence.py
```

`advisory_repository_skills.py` never imports
`current_acting_model_advisory_provider.py` or
`advisory_context_package.py`; `repository_skills.py` never imports
any of the three advisory modules. No cycle exists at any point in the
graph.

**No authority leakage.** None of the three modules expose a
`decide`, `authorize`, `commit`, `push`, `finalize`, `notify`,
`mutate`, `execute`, `approve`, or `reject` method on any public class,
none import `TransitionVerdict`, and none contain an execution
primitive (`subprocess`, `os.system`, `Popen`, `exec`, `eval`, socket
or HTTP calls).

## 2. Extension Point Verification (Objective 2)

Every extension point named in the 115Z brief was re-verified against
its frozen shape:

- **`AdvisoryProvider`** — abstract, exactly one abstract method
  (`invoke`); stable since 115Q.
- **`RepositorySkill`** — abstract, exactly one abstract method
  (`invoke`); unchanged since 115I; `AdvisoryRepositorySkill` correctly
  extends it rather than duplicating it.
- **`EvidenceProvider`** — abstract, exactly one abstract method
  (`collect`); unchanged since 115C/115D; the Advisory subsystem does
  not subclass it directly (it produces evidence via
  `build_evidence_from_normalized()`, consistent with 115S/115T).
- **`AdvisoryContextPackage`** — frozen 15-field dataclass shape
  unchanged since 115W/115X; `ALLOWED_ADVISORY_QUESTIONS` still exactly
  one entry; `TRUST_CLASSES` still exactly four.
- **`DecisionEvaluation`** — `evaluate(context)` signature and its six
  invariant evaluators unchanged; the Advisory subsystem does not
  touch this module at all (see containment, below).

All five extension points are stable and unmodified by this phase.

## 3. Containment Verification (Objective 3)

Re-confirmed, with executable tests, that the Advisory subsystem
remains strictly evidence-only:

- **Cannot authorize** — no class in the subsystem imports or
  constructs a `TransitionVerdict`.
- **Cannot execute** — no execution primitive appears anywhere in the
  three modules' source (docstrings stripped before the check, to
  avoid false positives from negation phrases such as "No
  subprocess...").
- **Cannot mutate the repository** — reconfirmed end-to-end: invoking
  `RepositoryConsistencyAdvisorySkill` via
  `build_repository_consistency_skill_with_current_model()` against a
  disposable git repository leaves `git log` byte-for-byte identical
  before and after.
- **Cannot bypass the Repository Transition Validator** —
  `repository_transition_validator.py` contains no reference to any of
  the three module names, and none of the three modules import the
  validator. The boundary holds in both directions.
- **Cannot bypass normalization** — the Evidence Builder's only public
  entry point (`build_evidence_from_normalized`) accepts a
  `NormalizedAdvisoryResponse`; a `RawAdvisoryResponse` cannot reach it
  directly. There is no code path from a raw provider response to
  evidence that skips the Normalizer.
- **`live` runtime execution remains unavailable** —
  `pcae runtime inspect --json` still reports
  `execution_availability: unavailable`, `current_runtime_state:
  Observed`, `current_maximum_plugin_capability: observe`, and
  `collect_evidence_via_repository_skills()` still reports
  `E-runtime-002` as `unavailable`.

## 4. Architecture Consistency Review (Objective 4)

Read every one of the 10 phase docs and 6 canonical docs together.
Findings:

- **Terminology is consistent.** "The advisory provider may produce
  evidence. PCAE remains the authority." and "Models improve by
  receiving better evidence, not by receiving more authority." appear
  verbatim and unchanged in every phase doc from 115P onward.
- **The pilot advisory question is quoted identically everywhere it
  appears** — `"Is the repository state internally consistent?"` — in
  115Q, 115S, and 115W-115Y, with no paraphrasing drift.
- **The "current acting model" / same-model-default term is used
  consistently** across 115Q, 115S–115U, and their respective
  contracts.
- **Cross-phase references are accurate.** Each canonical document's
  "Relationship to Prior Phases" section names its true immediate
  predecessor (verified 115Q→115P, 115U→115T, 115V→115U, 115W→115V).
- **The "Recommended Next Phase" chain is unbroken** end to end: 115P
  recommends 115Q; 115Q recommends 115R; ... 115Y recommends 115Z. No
  phase doc recommends a phase that did not, in fact, come next.
- **Diagrams are internally consistent.** `PCAE_ADVISORY_REPOSITORY_
  SKILLS_ARCHITECTURE.md` and `PCAE_ADVISORY_REPOSITORY_SKILLS_
  CONTRACT.md` each carry two Mermaid flowcharts that reference the
  same pipeline stage names (Advisory Repository Skill → Prompt
  Builder → Advisory Provider → ... ). `PCAE_ADVISORY_CONTEXT_PACKAGE_
  CONTRACT.md`, `PCAE_ADVISORY_EVIDENCE_ENRICHMENT.md`, and
  `PCAE_ADVISORY_PROVIDER_STRATEGY.md` are prose-only contracts by
  design and carry no diagrams — this is expected, not an
  inconsistency, since their subject matter (field-level contracts and
  a strategy review) is not itself a pipeline.
- **Every document confirms "Execution capability remains
  unavailable."** Verified present, verbatim, in all 16 documents
  (10 phase reports + 6 canonical docs).

No terminology drift, no contradictory diagrams, and no broken
cross-references were found.

## 5. Implementation Consistency Review (Objective 5)

Confirmed the three runtime prototypes still match their frozen
contracts exactly:

- `RepositorySkillManifest` still carries `skill_id`, `name`,
  `version`, `capabilities`, `determinism`, and `model_produced`,
  unchanged since 115I.
- `RepositoryConsistencyAdvisorySkill.manifest` still declares the
  `AI_REVIEW` capability and `model_produced=True`, per 115J/115R.
- `CurrentActingModelAdvisoryProvider` still exposes `provider_id`,
  `backend_kind`, `determinism`, and a callable `invoke`, per 115S's
  contract.
- `AdvisoryContextPackage` still enforces exactly one allowed advisory
  question and exactly four trust classes, per 115W/115X/115Y.
- The default Repository Skills registry (`build_default_registry()`)
  is still exactly the four deterministic skills frozen in 115J
  (`git_repository_skill`, `runtime_repository_skill`,
  `report_repository_skill`, `metadata_repository_skill`) — the
  Advisory skill is intentionally not part of the default registry,
  consistent with every prior phase's "no hidden integration" finding.

No drift between prototype and contract was found anywhere.

## 6. Roadmap Review (Objective 6)

This phase's own recommendation, and `PROJECT_STATUS.md`'s "Current
Phase" section, both now read:

**Recommended Next Phase: 116A — v0.2 Architecture Review &
Consolidation**

This supersedes the placeholder "115Z — Advisory Skill Pilot
Hardening" recommendation carried in 115Y's report (this phase *is*
that hardening work, now complete under its true name, 115Z —
Advisory Subsystem Hardening & Release Readiness). 116A is a
whole-project architecture review and consolidation phase, not
further Advisory-specific implementation — no second Advisory
Provider, no Advisory Repository Skill integration, and no
`AdvisoryContextPackage` wiring is recommended as the immediate next
step.

## 7. Remaining Architectural Debt

Classified into the four categories requested by the brief. None of
these are defects — each is a deliberate, previously-documented scope
boundary from its originating phase, restated here for visibility as
this subsystem is declared stable.

**Documentation debt**
- None major. All ten phase docs and six canonical docs are complete,
  cross-referenced, and terminology-consistent (Section 4).

**Implementation debt**
- `AdvisoryContextPackage` (115W–115Y) is not yet integrated into the
  live advisory pipeline — the Prompt Builder still assembles
  `AdvisoryRequest` directly rather than consuming a package. This was
  an explicit, intentional deferral in 115W/115X ("no
  `AdvisoryContextPackage` runtime, no Advisory Provider runtime
  change ... is implemented or modified"), not an oversight.
- No live/automated model-invocation mechanism exists —
  `CurrentActingModelAdvisoryProvider` relies on the current session
  supplying its own answer; there is no programmatic call-out. This
  was documented as an inherent characteristic of the same-model
  default in 115S, not a limitation to be fixed.
- No automatic secret/content redaction scanning exists inside
  `AdvisoryContextPackage` — `redaction_summary` is a required,
  self-validating record, but redacting content before construction
  remains the assembler's responsibility. Documented explicitly as a
  scope boundary in 115X/115Y.

**Optimization debt**
- None identified. All subsystem logic is lightweight, in-memory, and
  deterministic; no performance-sensitive path exists yet because no
  live pipeline integration exists yet (see implementation debt,
  above).

**Future capability debt**
- A second Advisory Provider (backend-specific, e.g. an external API)
  remains explicitly deferred, per 115U's strategy review.
- Advisory question types beyond repository-consistency review
  (documentation review, report review, architecture review, code
  review, security review) remain deferred, per 115Q Section 10 and
  115W Section 9.
- Split-model mode (a second model reviewing the first's advisory
  output) remains deferred, per 115Q Section 4.

## 8. Subsystem Freeze Declaration

The Advisory Repository Skills subsystem — comprising
`advisory_repository_skills.py`, `current_acting_model_advisory_
provider.py`, and `advisory_context_package.py`, together with their
six canonical contract documents and ten phase reports (115P–115Y) —
is hereby declared a **stable v0.2 subsystem of PCAE**. Its extension
points (`AdvisoryProvider`, `RepositorySkill`/`AdvisoryRepositorySkill`,
`EvidenceProvider`, `AdvisoryContextPackage`) are frozen. No further
contract changes to this subsystem are anticipated absent a
deliberate, separately-scoped future phase. Containment is
re-verified: the subsystem remains evidence-only. Execution capability
remains unavailable.

## Governance / No-Go Confirmations

- No new feature added.
- No new Evidence Provider added.
- No new Repository Skill added.
- No new Advisory Provider added.
- No second Advisory Provider added.
- No Decision Evaluation modified.
- No Repository Transition Validator modified.
- No lifecycle command modified.
- No Notification Policy modified.
- No Repository State Kernel modified.
- No execution.
- No authorization.
- No Permission Broker enforcement.
- No plugins.
- No Telegram inbound.
- No REST.
- No Dashboard.
- No Web UI implementation.
- No raw git commit.
- No raw git push.
- No force push.
- No tags.
- No releases.
- No package publication.
- Execution capability remains unavailable.

## Recommended Next Phase

116A — v0.2 Architecture Review & Consolidation
