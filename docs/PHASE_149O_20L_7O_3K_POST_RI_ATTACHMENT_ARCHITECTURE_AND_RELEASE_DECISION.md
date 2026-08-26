# Phase 149O.20L.7O.3K — Post-RI Attachment Architecture and Release Decision

**Status: DECISION-ONLY — COMPLETE. NO `src/pcae` MODIFIED.**

## 1. Objective

Determine, from current source and contracts only (not from prior
phases' conclusions), whether PCAE can now safely move from
`149O.20L.7O.3J`'s verified **automatic Repository Intelligence context
attachment** to genuine **RI-backed Advisory reasoning consumption**
(Repository Intelligence → canonical `AdvisoryContextPackage` → real
`AdvisoryProvider` → Advisory result), without inventing new reasoning
architecture, activating a model/backend, changing authority semantics,
enabling execution, or violating the historically frozen Advisory
architecture — and, based on that evidence, select one of three
directions (A: complete true consumption; B: release attachment-only
as a patch; C: defer RI work and move to another capability). This
phase does not implement the selected direction.

## 2. v0.4.1 baseline

Verified at phase entry:

- `git status --short`: clean.
- `git rev-list --count origin/main..HEAD`: `0`.
- `HEAD` == `origin/main` == `62826d820ea62a05250cc6f32920ed50f508f21a`.
- `v0.4.1^{commit}` == `9869cb65d890b70d8649ddd4216ffda4e7d98df5`, unchanged.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent. `pcae push check`: clean, nothing to push.
- `pcae doctor task-memory`: warnings only — pre-existing historical
  `tasks/DONE.md` sync-debt entries from before this phase, repository-
  maintainer-only, unrelated to Advisory/RI, unchanged by this phase.
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`,
  registry empty, 0 plugins — unchanged throughout this phase.
- Telegram notify sink: configured, enabled, ready.

v0.4.1 remains the current, unmodified public release throughout this
phase. No tag, release, or build artifact was touched.

## 3. 3J result (restated, not re-litigated)

`149O.20L.7O.3J` wired `core/advisory.py::build_advisory()` (the engine
behind `pcae advisory check`) to automatically call the existing
`advisory/context/advisory_context_builder.py::build_advisory_context()`
bridge and attach its output, additively, under a new
`repository_intelligence_context` envelope key. Exactly one production
file changed. Read-only, fail-soft, structurally non-authoritative.

## 4. 3J.1 correction (restated, not re-litigated)

`149O.20L.7O.3J.1` independently confirmed 3J's mechanics but corrected
its framing: `core/advisory.py` (Phase 88W "Advisory Mode") is a
**deterministic decision-preview engine with no reasoning step**. RI
context is **attached** to its output envelope; it is not **consumed**
by any reasoning step, because that engine has none. The actually
Phase-122A-scoped reasoning consumer (`AdvisoryProvider` /
`AdvisoryContextPackage`) remains untouched, mock-only, and
disconnected. Two non-blocking findings were recorded: F1 (symlink
provenance gap) and F2 (authority non-flow enforced only by parameter
list, not by an interface-level type boundary).

This phase independently re-derived — not re-used — both findings and
the taxonomy below directly from current source, per the governing
instruction not to inherit 3I's or 3J's or 3J.1's conclusions
unverified.

## 5. Advisory subsystem taxonomy

Freshly enumerated from `src/pcae/` (excluding `.claude/worktrees/`,
which is a stale worktree copy, not the working tree):

| # | Module | Phase origin | Role |
|---|--------|--------------|------|
| 1 | `core/advisory.py` | 88W | Deterministic Advisory Mode preview/decision engine (`build_advisory`). Consumes Permission Broker + shell-gate evidence; produces `would_*` verdicts. Since 3J, also calls `_gather_repository_intelligence_context` to attach RI context additively. |
| 2 | `advisory/context/advisory_context_builder.py` | 122E | `build_advisory_context()` — assembles a `RepositoryIntelligenceContextPackage` from a Repository Knowledge Snapshot exclusively via the Track 121 `execute_query` entry point. Two callers: `commands/advisory_context.py` (manual CLI) and, since 3J, `core/advisory.py`. |
| 3 | `core/advisory_repository_skills.py` | 115R | `AdvisoryProvider`/`AdvisoryRequest`/`RawAdvisoryResponse`/`NormalizedAdvisoryResponse`/Prompt Builder/Normalizer/Evidence Builder/`AdvisoryRepositorySkill` framework. `MockAdvisoryProvider` only real implementation shipped here. |
| 4 | `core/advisory_context_package.py` | 115X | `AdvisoryContextPackage` runtime object: 15-section, four-trust-class, size-budgeted, single-hardcoded-question (`"Is the repository state internally consistent?"`) context object. |
| 5 | `core/current_acting_model_advisory_provider.py` | 115S | `CurrentActingModelAdvisoryProvider` — the one non-mock `AdvisoryProvider` implementation. Stateless, single-use; its "answer" is supplied once at construction time by whichever human/agent operator is running the session, not fetched via any live call. |
| 6 | `commands/advisory.py`, `commands/advisory_context.py` | 88X/122E | CLI surfaces: `pcae advisory check/explain/status` (→ #1) and `pcae advisory-context build` (→ #2). |
| 7 | `core/advisory_runtime.py` | 113A | Architecturally distinct "Advisory Runtime" (operational health/consistency/readiness). Explicitly disambiguated from #1-#5 by `docs/PCAE_ADVISORY_RUNTIME.md` and 122A §3.5. Reads only a Runtime Snapshot, never Repository Intelligence or Evidence. Out of scope for RI reasoning consumption. |

Call graph, current state:

```
pcae advisory check
  → core/advisory.py::build_advisory()
      → core/permission_broker.py::build_permission_broker()   [decision -- unaffected by RI]
      → advisory/context/advisory_context_builder.py::build_advisory_context()  [RI attachment -- additive, no decision effect]

pcae advisory-context build   (manual, unchanged since 122E)
  → advisory/context/advisory_context_builder.py::build_advisory_context()

(no production caller)
  → core/advisory_repository_skills.py (AdvisoryProvider framework)
  → core/advisory_context_package.py (AdvisoryContextPackage)
  → core/current_acting_model_advisory_provider.py
```

Verified via `grep -rn` over `src/pcae/*.py` (excluding `__pycache__`):
`advisory_repository_skills` is imported only by
`current_acting_model_advisory_provider.py`, which is itself imported
by nothing in `src/pcae`; `advisory_context_package` is imported only
inside `src/pcae/advisory/` by a different (context-package) module
also named similarly but structurally distinct — the frozen 115X
`AdvisoryContextPackage` object has zero non-test importers anywhere in
production code.

## 6. Phase 122 intended consumer

`docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONSUMPTION_ARCHITECTURE.md`
§3.4 defines "Advisory" for RI-consumption purposes as exactly the
115P-115Z/118E framework: a backend-agnostic `AdvisoryProvider`
(115Q) fed by a 115W `AdvisoryContextPackage`. §3.4 explicitly states
122A "does not authorize" placing RI content into a specific
`AdvisoryContextPackage` section — that requires "an explicit 115W-
contract amendment or extension phase." §12's roadmap (122B contract
freeze → 122C verification → 122D prototype plan → 122E prototype →
122F verification) ran to completion, but 122E's actual delivered
prototype (§5 above, `advisory_context_builder.py`) builds a
*different* object (`RepositoryIntelligenceContextPackage`, in
`advisory/context/context_package.py`) than the one §3.4 named as the
consumer input (`core/advisory_context_package.py`'s
`AdvisoryContextPackage`). §15 ("Strict Non-Goals") explicitly excludes
"Advisory integration" and "a context builder" from 122A's own scope —
122A is architecture-only.

Answers:

- **Who consumes `AdvisoryContextPackage`?** No production code. Only
  test suites (115R/115S/115T/115U/115V/115W/115X/115Y/115Z) construct
  or consume it.
- **What output is expected to change because of RI?** Per §3.4/§3.8,
  a *future* `AdvisoryContextPackage`-fed `AdvisoryProvider`'s
  `NormalizedAdvisoryResponse` — never `core/advisory.py`'s `would_*`
  decision fields, which §3.8 explicitly reserves for Decision
  Evaluation / the Repository Transition Validator, unchanged.
- **Was a real provider intentionally deferred?** Yes —
  `advisory_repository_skills.py`'s own module docstring states
  "Build the framework. Do not build AI integration," and lists
  DeepSeek/Claude API/OpenAI/GLM/Qwen/Codex/local-SLM/network calls as
  "absolutely forbidden, and absent from this module."
- **Was mock-only status a deliberate stop condition?** Yes — the same
  docstring states the module is "disconnected by design (115R scope)"
  from `decision_evaluation.py`, `repository_transition_validator.py`,
  `repository_skills_integration.py`, any lifecycle command, and
  `repository_skills.py`'s own `build_default_registry()`.
- **What prerequisite was required before production connection?**
  122A §3.4's own text: "Any future phase that wants Repository
  Intelligence context to occupy a specific `AdvisoryContextPackage`
  section... must do so as an explicit 115W-contract amendment or
  extension phase; 122A does not authorize that placement by itself."

## 7. AdvisoryProvider maturity

Interface: `AdvisoryProvider` (ABC, one abstract `invoke()` method) —
stable, frozen since 115Q/115R, unchanged.

Implementations:

- `MockAdvisoryProvider` — deterministic, in-memory canned-response
  lookup. No I/O.
- `CurrentActingModelAdvisoryProvider` — the only non-mock
  implementation. Requires its single answer be supplied at
  construction time by the calling code (in practice, a human or
  agent operator typing an answer, exactly as the module's own
  docstring states); stateless; raises on a second `invoke()` call.
  Not a live/automatic model call of any kind.

Production callers: **zero** (§5/§6). Package inclusion: shipped in
`src/pcae/core/`, importable, but never imported by any production
module. Tests: 9 dedicated test files exercise the framework end to
end against `MockAdvisoryProvider`/`CurrentActingModelAdvisoryProvider`
only. Persistence: none — no `AdvisoryContextPackage` or
`AdvisoryRequest`/response is ever written to disk. Failure semantics:
`normalize_advisory_response` fails closed on any malformed/
unauthorized-field/schema-violating raw response, producing
`UNKNOWN`-freshness Evidence rather than fabricating a result. Provider
selection: none exists — no registry, no default, no CLI flag.
Runtime dependencies: none beyond in-process Python; no network, no
model backend, no execution capability referenced anywhere in either
module.

**Classification: MOCK-ONLY / DISCONNECTED BY DESIGN.** Not
`CONTRACT ONLY` (an implementation exists and passes its own tests);
not `PROTOTYPE` in the sense of "partially wired" (it is *fully*
unwired from production, deliberately, per its own docstring); not
`PRODUCTION READY` (zero production callers, single hardcoded
question, no automatic/live invocation path).

## 8. Current reasoning consumers

Per subsystem (§5 table), stating packages-context / renders-output /
deterministic-rule-decision / invokes-provider / performs-reasoning /
invokes-model / mock-only / disconnected / production-reachable:

| Subsystem | Packages context | Renders output | Deterministic rule decision | Invokes provider | Performs reasoning | Invokes model | Mock-only | Disconnected | Production reachable |
|---|---|---|---|---|---|---|---|---|---|
| `core/advisory.py` | no | yes | **yes** | no | no | no | no | no | **yes** |
| `advisory_context_builder.py` | **yes** | no | no | no | no | no | no | no | **yes** |
| `advisory_repository_skills.py` (`AdvisoryProvider`/skill) | yes (via Prompt Builder) | no | no | **yes** (to whichever provider it's given) | no (the *provider* would reason, if real) | no (Mock returns canned data) | **yes** (only shipped concrete provider besides #5) | **yes** | no |
| `advisory_context_package.py` | yes | no | no | no | no | no | n/a (data object) | **yes** | no |
| `current_acting_model_advisory_provider.py` | no | no | no | n/a (is a provider) | **no** (relays a pre-supplied answer, does not compute it) | **no** (no live call) | no | **yes** | no |
| `advisory_runtime.py` | no | yes | yes (operational, not RI-related) | no | no | no | no | no | yes (unrelated to RI) |

No subsystem in this repository, today, both (a) is production
reachable and (b) performs reasoning whose output depends on Repository
Intelligence content. `core/advisory.py` is production-reachable and
makes a deterministic rule decision, but that decision is structurally
independent of RI (§3J.1, re-confirmed §16 below). The
`AdvisoryProvider` chain could perform reasoning (if a real, live
provider existed) but is not production reachable.

## 9. Production reachability

Only `core/advisory.py` and `advisory_context_builder.py` are reachable
from a real `pcae` CLI invocation today with respect to RI. The
`AdvisoryProvider`/`AdvisoryContextPackage`/`CurrentActingModel...`
chain has **no** current production entry point — no CLI command, no
lifecycle hook, no scheduled task constructs or invokes any of them
outside test code. This is not merely "the missing edge is a wiring
call" — there is no existing call site to wire *from* in production;
one would have to be created (a new CLI command, or a new lifecycle
integration point), which is itself new integration surface, not a
one-line connection.

## 10. Model/provider/runtime dependencies

Making the 122A-intended consumer real, with genuine *automatic*
reasoning (not a human typing an answer at construction time, which
would defeat the "automatic RI-backed reasoning" objective), requires:

- **A live model/backend invocation** — the only non-mock provider
  today is definitionally a stand-in for "ask whoever is running this
  session," not an automated call. No `backend_kind` other than
  `"deterministic_mock"` and `"current_acting_model"` exists.
- **Network access** — any real backend (local SLM, hosted API) would
  require network I/O, absent today and explicitly forbidden by
  `advisory_repository_skills.py`'s own docstring for this framework
  as currently scoped.
- **No runtime execution-capability elevation** is required *per se* —
  §3.9 of 122A is explicit that RI consumption is a read-only operation
  compatible with `Observed`/`observe`/`unavailable`. Network/model
  invocation is a distinct axis from execution capability; PCAE's 11
  frozen runtime principles do not currently gate outbound model calls
  through the runtime-capability system at all — there is simply no
  automatic-invocation path today, mock or real.

Classification: **model/network dependency required for genuine
automatic reasoning; no runtime-execution-capability dependency.**

## 11. True-consumption definition

Adopting the human's stated minimum: for a request with a fixed
non-RI-derived input, supplying a **different valid RI context** must
be capable of producing a **different Advisory recommendation output**,
while authority/permission fields remain structurally separate from
that output. Applied here:

- `core/advisory.py`'s `would_*`/`broker_decision`/`advisory_decision`
  fields are, by construction and by 3J.1's independent empirical
  A/B test, **invariant** to RI presence/absence/content — this
  satisfies "authority separate" trivially because RI touches nothing
  authority-shaped, but it also means **no reasoning output exists
  in this subsystem for RI to ever change.** This subsystem cannot
  become a true-consumption target without adding a reasoning stage —
  which the human's No-Go list forbids inventing.
  - The `AdvisoryProvider` chain's `NormalizedAdvisoryResponse.findings`
    *could* vary with `AdvisoryRequest.bounded_context` content (which
    could include RI-derived text) if a real, live provider answered
    it — but no such provider exists, and today's `bounded_context`
    (`build_advisory_request`) never includes RI content at all.

**Conclusion: RI currently affects no Advisory reasoning output
anywhere in this repository — the present state is attachment/
disclosure only, confirmed independently of 3J.1's wording, exactly
matching this phase's own true-consumption test.**

## 12. Contract readiness

Existing frozen contracts (115W/115Q, `docs/PCAE_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md`,
`docs/PCAE_ADVISORY_PROVIDER_STRATEGY.md`) already specify:

- context input shape (`AdvisoryContextPackage`'s 15 sections, 4 trust
  classes, size budgets) — **frozen, but does not include a Repository
  Intelligence section today** (122A §3.4 confirms this explicitly).
- provider behavior (`AdvisoryProvider.invoke()`, one request/one
  response, no streaming/multi-turn) — frozen, adequate.
- output type (`NormalizedAdvisoryResponse`) — frozen, adequate.
- limitations (mandatory `limitations` field, enforced by
  `NormalizedAdvisoryResponse.__post_init__`) — frozen, adequate.
- error semantics (fail-closed normalization, `UNKNOWN`-freshness
  Evidence on failure) — frozen, adequate.
- provenance (`EvidenceProvenance`, `deterministic_origin=False` for
  model-produced evidence) — frozen, adequate.
- authority non-flow (`_UNAUTHORIZED_RESPONSE_FIELDS` rejecting
  `verdict`/`commit`/`push`/`authorized`/`execute`/`finalize` outright
  at the Normalizer) — frozen, adequate, and independently the
  strongest existing safeguard found this phase.

**What is missing:** a contract amendment authorizing (a) where RI
content lives inside `AdvisoryContextPackage` (no section exists for
it today), and (b) a real, non-mock, non-human-relay `AdvisoryProvider`
backend specification (`backend_kind`, invocation trigger, network/
model boundary) — neither exists in any frozen document today.

**Conclusion: a new contract (115W amendment, per 122A §3.4's own
explicit instruction) is required. Option A is therefore not a simple
source-wiring phase.**

## 13. Authority separation

Assessed against the five required invariants:

- RI context != authority — **already true** (RI is read-only Query
  Layer output, never touches `permission_broker`, confirmed
  bidirectionally by static grep, §3J.1).
- Advisory recommendation != authorization — **already true**
  structurally in `core/advisory.py` (`authorization_granted`,
  `execution_authorized` are always `False`, computed independently of
  any Advisory field).
- Advisory reasoning != Permission Broker — **already true**; zero
  cross-references either direction (re-confirmed this phase, §5).
- Provider output != human approval — **already true** by construction:
  `_UNAUTHORIZED_RESPONSE_FIELDS` rejects any raw response claiming
  `authorized`/`execute`/`finalize`/etc. outright.
- Provider recommendation != execution capability — **already true**;
  no `AdvisoryProvider` code path touches `runtime_registry`/execution
  gating anywhere.

**Conclusion: the existing 122A/115Q/115R architecture already
guarantees authority separation structurally, at the type/normalizer
level, not merely by convention. This is a genuine asset for any
future Option-A phase — it does not need to be (re)designed, only
preserved.**

## 14. Effort reclassification

**True RI-backed Advisory reasoning consumption: L**, explicitly
**not** inherited from 3I's S classification.

3I's "S" effort estimate (`docs/PHASE_149O_20L_7O_3I_...md` §Effort
table, Candidate C) was scoped to "RI/Advisory context wiring" — i.e.
exactly the *attachment* work 3J then implemented (S was correct for
that). 3I did not evaluate wiring a real `AdvisoryProvider` consumer,
because at 3I's time of writing the distinction between "attachment"
and "reasoning consumption" had not yet been drawn (3J.1 drew it).
Re-scoped to *true reasoning consumption* as this phase defines it
(§11), the work requires, at minimum:

1. A 115W contract amendment (new document or versioned amendment)
   defining an RI section of `AdvisoryContextPackage` and/or relaxing
   the single-hardcoded-question restriction — **architecture +
   contract work**, not source wiring.
2. A real `AdvisoryProvider` backend specification and implementation
   — model/network boundary decision, explicitly out of this phase's
   and arguably the project's current runtime posture's scope.
3. A new production entry point (§9) — no existing call site to
   connect from; `core/advisory.py`'s decision engine has no reasoning
   hook to attach to without inventing one (forbidden), so the
   consumer would have to be a *new* command/lifecycle surface, not an
   edit to `build_advisory()`.
4. F1 (symlink provenance) repair as a precondition (§16 below) once
   RI can actually swing an output.
5. A new independent E2E verification phase (per the human's own
   Option-A "expected next" note).

Likely files/components: `docs/PCAE_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md`
(amendment), `core/advisory_context_package.py`, a new
`core/advisory_repository_skills.py` real provider, a new CLI command
or lifecycle hook, `advisory/context/advisory_context_builder.py` (to
feed the new section), plus F1 repair in `core/advisory.py`'s RI
acquisition path and/or `repository_intelligence` persistence.

## 15. Attachment-only value

- **Is `repository_intelligence_context` consumed by any downstream
  machine process?** No — grepped: no code anywhere in `src/pcae`
  reads that output key back in. It is terminal, human-facing JSON.
- **Is it primarily better diagnostics/explainability?** Yes — that is
  its entire current value: an operator running `pcae advisory check`
  now sees available RI (with attribution/limitations/staleness
  disclosure) alongside the would-* verdict, without a second manual
  `pcae advisory-context build` invocation.
- **Does it remove useful manual choreography?** Partially — it
  removes the need to separately run the manual CLI to see *some* RI
  context inline with an Advisory check, though the manual command
  still exists unchanged and offers finer query control (entity/
  capability/contract targeting) that the automatic path does not
  replicate.
- **Does it materially improve `pcae advisory check` output?** Yes,
  for repositories with a fresh RI snapshot — genuinely additive,
  zero regression risk (3J.1's Fast Green A/B).
- **Is it worth a release by itself?** Yes, if correctly labeled (§27).

**Standalone value score: 3/5** — real, verified, zero-risk
diagnostic improvement; capped below higher scores because it changes
no decision, is not consumed downstream, and duplicates (rather than
replaces) the existing manual command's capability.

## 16. F1 symlink provenance analysis

Re-examined against current contracts:

- Do current RI contracts permit symlink traversal? No contract
  addresses filesystem symlinks at all — the canonical-path resolution
  (`repo_root / ".pcae" / "repository-intelligence" / "latest.json"`)
  is a plain path join with no symlink-rejection or realpath-identity
  check anywhere in `core/advisory.py` or the Track 120/121 persistence
  layer.
- Is the canonical path supposed to establish repository binding? By
  convention yes (it is "the" per-repository snapshot location), but
  no code enforces that the path's resolved target is *this*
  repository rather than another one reachable via a symlink.
- Does an artifact-embedded repository identity exist separate from
  `repository_commit`? No (§18/§19 below) — `repository_commit` is the
  only proxy, and it is a commit hash, not a repository identity.
- Would true reasoning consumption make F1 materially more serious?
  Yes — today F1 can only mislabel a diagnostic disclosure (attachment
  has no decision effect). Under Option A, a poisoned or foreign
  snapshot silently consumed (the zero-commit case: **zero
  disclosure**) could feed fabricated content into an actual reasoning
  output, which is a materially different risk class.

**Classification: ACCEPTABLE NON-BLOCKING for the current
attachment-only state (matches 3J.1's own disposition, independently
re-confirmed). MUST REPAIR BEFORE TRUE REASONING CONSUMPTION** — F1 is
not merely cosmetic once RI can influence a reasoning output; it
becomes a live provenance-confusion / context-poisoning vector at that
point. **Not** classified BLOCKING FOR ANY RELEASE, because no release
under consideration in this phase (Option B) changes any reasoning
output.

## 17. Empty-repository provenance analysis

Root cause, re-derived from `core/advisory.py::_gather_repository_intelligence_context`:
staleness disclosure is a two-sided comparison
(`source_commit` from the snapshot vs. `current_commit` from
`git_head_commit_sha(repo_root)`). When the target repository has no
commits, `git_head_commit_sha` raises `HistoricalSourceError`, which is
caught and produces `current_commit = None`; the `if source_commit and
current_commit and source_commit != current_commit` guard then
short-circuits on the falsy `current_commit`, silently skipping the
comparison — not because provenance was checked and passed, but
because the comparison could not be attempted at all. No contract
addresses this specific case; it is a genuine gap in the existing
staleness-disclosure logic, not an intentional design decision. A
limitation such as "repository identity unverifiable (no HEAD in
current repository)" would be a faithful disclosure but is **not
implemented in this phase** (no-go, §33).

## 18. Repository identity binding

No, the RI snapshot artifact carries no repository identifier separate
from `repository_commit` (confirmed via `context_metadata.source_artifact`
field enumeration, §3J.1 and re-confirmed this phase against
`query_engine._source_artifact()`). `repository_commit` is a commit
hash, not a repository identity (a commit hash can exist, by
coincidence or by design, across unrelated repositories or forks).
**Repository-identity binding is a missing prerequisite for genuine
reasoning consumption** — without it, F1's cross-repository symlink
scenario cannot be distinguished from an ordinary stale-same-repository
snapshot by any means stronger than "the commit doesn't match," which
already fails silently in the zero-commit case (§17).

## 19. True reasoning threat model

Not implemented; assessed only, per the human's directive.

| Threat | Currently handled? |
|---|---|
| Malicious/tampered RI artifact | Partially — schema/compatibility validation exists at the Query Layer (`SnapshotCompatibilityError`/`SnapshotLoadError`), but no cryptographic integrity check exists on `latest.json` content. |
| Stale artifact | Yes, when the local repository has ≥1 commit (`possibly_stale_snapshot` disclosure). |
| Foreign artifact (F1) | Partially — disclosed only when the local repo has commits; **not handled** in the zero-commit case (§17). |
| Malformed context | Yes — `AdvisoryContextBuilderError` wraps every Query Layer/validation failure; fails closed for the manual CLI path, fails soft (by 3J's deliberate design) for the automatic attachment path. |
| Context poisoning (a real reasoning consumer trusting attacker-influenced RI content as fact) | **Not handled** — no content-level provenance/trust scoring beyond the existing four trust classes' structural separation (115W), which assumes correctly-sourced input; it does not defend against a correctly-formed but falsely-sourced artifact (F1). |
| Provider prompt/context injection (if a live model were involved) | **Not applicable today** — no live model exists to inject into. Would need dedicated design work under Option A. |
| Deterministic provider manipulation | Not applicable to `MockAdvisoryProvider` (test-only); `CurrentActingModelAdvisoryProvider` is not automatically invoked, so no unattended manipulation surface exists today. |

**Conclusion: several threats relevant to a future live reasoning
consumer (context poisoning, artifact integrity, prompt injection) are
presently unaddressed by any frozen contract — further evidence that
Option A is architecture/contract-scale work, not a wiring task.**

## 20. Rollback-readiness comparison (Candidate A)

Per `149O.20L.7O.3I` §5/§28/§31 (re-read, not re-verified in depth this
phase, per the human's "reassess only enough to compare priorities"
instruction): rollback readiness/evidence auto-generation remains
**S-M effort, LOW authority risk** (dry-run only, `execution_allowed:
False` preserved), with the underlying primitive
(`build_rollback_execution`) already safe and tested — only
persistence/schema/freshness-binding work remains. This is
**cheaper and lower-risk than Option A (L effort, new contract, model/
network dependency, F1-repair precondition, unaddressed threat-model
gaps)**. **Candidate A now outranks Option A as the next capability
priority**, given Option A's reclassified effort.

## 21. Runtime-preflight comparison (Candidate B)

Per 3I §11/§16: the runtime registry remains empty by architectural
invariant; existing static runtime facts are already internally
consumed by session bootstrap, phase reports, and finalization; no
real unmet routing need was found. No dependency on this phase's
Advisory findings changes that conclusion — Candidate B is not
reopened. It remains the lowest-priority of the three deferred
candidates.

## 22. Option A — Complete true RI reasoning consumption

| Item | Evidence |
|---|---|
| Real reasoning consumer exists? | No (§7/§8/§9) |
| Production reachable? | No (§9) |
| Context interface ready? | Partially — `AdvisoryRequest`/`NormalizedAdvisoryResponse` frozen and adequate; `AdvisoryContextPackage` frozen but has no RI section and one hardcoded allowed question (§12) |
| Provider implementation ready? | No — only `MockAdvisoryProvider` (test-only) and `CurrentActingModelAdvisoryProvider` (human-relay, not automatic) (§7) |
| New contract required? | **Yes** — 115W amendment, per 122A §3.4's own text (§6/§12) |
| Network/model required? | Yes, for genuine automatic reasoning (§10) |
| Runtime dependency? | No execution-capability dependency; a model/network dependency distinct from runtime execution capability (§10) |
| Authority risk | LOW — existing structural safeguards (`_UNAUTHORIZED_RESPONSE_FIELDS`, always-false performed flags) already sufficient if preserved (§13) |
| F1 provenance prerequisite | Must repair before this option is safe (§16) |
| Effort | **L** (§14) |
| E2E testability | Feasible once implemented, following the 122F/3J.1 independent-verification pattern already established in this repo |
| Likely release | Not this cycle — would need its own architecture/contract/prototype/verification sequence before any release; premature to assign a version |

## 23. Option B — Release attachment-only integration

- Standalone user value: 3/5 (§15).
- Semantic release size: patch — one production file changed by 3J
  (`core/advisory.py`, +112/-0), fully additive, zero authority change,
  zero new CLI surface, zero regression (Fast Green A/B, 3J.1).
- Documentation wording: must state "automatically attaches available
  Repository Intelligence context, provenance, and limitations" — must
  **not** say RI "drives" or is "consumed by" Advisory reasoning (§28).
- F1 impact: none additional — F1 is already present and already
  correctly classified non-blocking for this attachment-only scope
  (§16).
- Regression/release effort: minimal — already implemented, tested,
  and verified independently by 3J.1; a release phase would mainly be
  packaging/version/changelog/notes work.
- Likely version: `v0.4.2`-plausible (patch), matching 3I's own prior
  estimate for "Candidate C narrow cut."

## 24. Option C — Defer RI and move to another capability

Compared against Candidate A (rollback readiness/evidence, §20) and
Candidate B/runtime preflight (§21): Candidate A remains the strongest
alternative if RI work (in any form) is deferred entirely — S-M effort,
LOW risk, real differentiated value ("PCAE already built this
intelligence but does not use it by default" — 3I's own framing,
applicable equally to rollback readiness). Runtime preflight remains
the weakest of all options under consideration and is not recommended
next regardless of the RI decision.

## 25. Decision matrix

| Criterion | A: True RI reasoning | B: Release attachment | C: Defer RI |
|---|---|---|---|
| User value | Medium (once built) | Medium (now) | None (RI) / Medium (via Candidate A) |
| Strategic value | High (closes 118E's original promise) | Low-Medium (diagnostics only) | Medium (redirects to a cheaper win) |
| Existing maturity | Low (mock-only, disconnected, no contract) | High (built, tested, independently verified) | N/A |
| Implementation effort | L | Already done (packaging only) | S-M (Candidate A) |
| Authority risk | LOW (if built per existing safeguards) | LOW (already verified) | LOW (Candidate A already scoped LOW) |
| Provenance risk | HIGH until F1 repaired | LOW (no decision effect) | N/A |
| E2E testability | Feasible, not yet built | Already independently verified (3J.1) | Feasible (Candidate A pattern) |
| Release delay | Long (new contract + provider + entry point + verification) | None (ready now) | None (ready to start) |
| Differentiation | High (genuine reasoning) | Low (diagnostics) | Medium (rollback readiness) |

## 26. Recommendation

**Option B** — release the verified attachment-only integration as a
narrow patch, with corrected release language (§28), **and** re-prioritize
Candidate A (rollback readiness/evidence) as the next capability
ahead of any Option-A work, per §20's comparison.

Rationale, directly from evidence gathered this phase: the human's own
stated test ("if a real AdvisoryProvider consumer already exists and
only needs bounded connection, choose Option A; if the 122A framework
is genuinely mock-only/disconnected and requires provider/runtime
architecture, do not pretend the missing edge is small") resolves
unambiguously — §5-§14 establish that the framework is mock-only,
fully disconnected from production, has zero existing entry point, and
its own architecture document (122A §3.4) requires a contract
amendment before RI content may even occupy a section of it. This is
squarely the "genuinely mock-only/disconnected... requires provider/
runtime architecture" branch, not the "only needs bounded connection"
branch. Given attachment-only carries standalone value (3/5), zero
regression risk, and is already independently verified, Option B is
the correct release choice over Option C (defer everything). Candidate
A outranks a future Option A attempt on effort and risk given Option
A's reclassified L effort and unaddressed provenance/threat-model
gaps (§16/§19).

## 27. Release implications

If Option B is selected by the human: release notes/CHANGELOG must
describe the shipped behavior as "`pcae advisory check` now
automatically attaches available Repository Intelligence context,
provenance, and limitations to its Advisory Mode output" — never
"Repository Intelligence now drives Advisory reasoning" (§28). Likely
version `v0.4.2`. No version bump was made in this phase (no-go).

## 28. Project-status terminology correction

`PROJECT_STATUS.md`'s "Current Phase" section (previously describing
`149O.20L.7O.3J.1`) already correctly distinguished attachment from
consumption, per 3J.1's own careful wording. This phase's update
(§29 below, applied directly to `PROJECT_STATUS.md`) reinforces that
distinction for `149O.20L.7O.3K` itself and explicitly records that the
122A-scoped reasoning-consumption gap remains **open**, not closed, and
will remain open regardless of which option the human ultimately
selects for RI work, pending a dedicated future phase.

## 29. Human decision required

This phase selects a **recommendation** (Option B + Candidate A
reprioritization) but does not act on it. Per governing instructions,
no next phase begins automatically.

```
ADVISORY MODE ATTACHMENT:
VERIFIED
TRUE RI-BACKED ADVISORY REASONING:
NOT YET PRODUCTION-READY
ADVISORY PROVIDER:
MOCK-ONLY / DISCONNECTED
RECOMMENDED:
OPTION B (release attachment-only patch; reprioritize Candidate A next)
IMPLEMENTATION:
NOT STARTED

HUMAN PRIORITY / RELEASE SELECTION:
REQUIRED
```
