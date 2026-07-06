# PCAE Advisory Provider Strategy

## Status

Phase 115U. Architecture and review only. No second Advisory Provider
is implemented by this document. No provider selection, no model
configuration, no DeepSeek/GLM/Qwen/Codex-specific/OpenAI-specific/
Claude-specific/local-SLM integration is added. No Advisory Provider
runtime, Repository Skills runtime, Evidence, Decision Evaluation,
Repository Transition Validator, or lifecycle command is modified. No
execution, authorization, Permission Broker enforcement, plugin,
Telegram inbound, REST, Web UI, or Dashboard capability is introduced.

## Purpose

Decide whether PCAE needs a second Advisory Provider now, while
preserving the ability to add one later without architectural
redesign — the deliberate strategic pause this arc has been building
toward since 115P first named the Advisory skill class: implement one
real provider carefully (115R/115S), verify it thoroughly (115T), and
only then ask whether a second one earns its complexity, rather than
proliferating providers speculatively.

## Core Principle (Restated, Unchanged)

The advisory provider may produce evidence. PCAE remains the
authority.

## Core Question

**Do we need a second advisory provider now?**

**Answer: No.** Defer. Keep the extension point open.

## 1. Review of the Current Advisory Provider Model

`CurrentActingModelAdvisoryProvider` (115S), built on 115R's framework
and 115Q's frozen contract, exhibits five properties this review
confirms remain sound and sufficient for the present:

| Property | Current state | Assessment |
| --- | --- | --- |
| **Same-model default** | The current acting model serves as the advisory provider by default; no separate configuration exists (115Q Section 3, 115S). | Sound. Requires zero operational overhead — no API key, no backend selection, no cost decision — while still producing genuine advisory evidence subject to every safety rule any other provider would be. |
| **Bounded pilot scope** | Exactly one question: "Is the repository state internally consistent?" (115S/115T). | Sound. A narrow, well-understood scope is exactly the right size for a first real provider; expanding scope is a separate decision from adding a second provider, and this review does not conflate the two. |
| **One request / one response / one EvidenceCollection** | `CurrentActingModelAdvisoryProvider` is single-use and stateless; a second `invoke()` raises rather than retrying (115S, 115T-verified). | Sound. Removes an entire class of failure mode (partial retries, accumulating conversation state, drift across turns) that a second provider would otherwise have to re-solve independently. |
| **Normalized evidence boundary** | Raw provider output never reaches Decision Evaluation directly; the Normalizer and Evidence Builder (115R, reused unmodified by 115S) are the only path to `Evidence` (115Q Section 6). | Sound. This boundary is provider-agnostic by construction — 115T's portability tests already proved five different `backend_kind` stand-ins produce valid evidence through the identical unmodified pipeline. |
| **Provider containment** | No decide/authorize/mutate/commit/push/finalize/notify capability anywhere in the provider or the skill wrapping it (115T-verified exhaustively). | Sound. Containment is a property of the `AdvisoryProvider`/`AdvisoryRepositorySkill` contract itself (115Q), not of any one provider's implementation — a second provider inherits it automatically by conforming to the same interface. |

Nothing in this review finds a gap in the current model that a second
provider would need to close. The current provider does exactly what
115P/115Q designed it to do, at exactly the scope 115S/115T scoped and
verified it to.

## 2. Evaluating Whether a Second Provider Is Needed Now

| Consideration | Analysis |
| --- | --- |
| **Benefit** | No identified gap. The one bounded pilot question is already answered by the current provider; a second provider answering the identical question would add a second opinion, not new coverage. |
| **Complexity** | A second provider requires, at minimum: a new `AdvisoryProvider` implementation, a decision about how/whether its evidence is merged with the first provider's, and documentation of that merge behavior. This is nontrivial complexity to accept for zero identified coverage gain. |
| **Latency** | A second live-model provider (any real backend beyond "the current acting model") introduces a second model invocation's latency into any pipeline that uses it — pure cost with no offsetting benefit at present scope. |
| **Cost** | A second real backend (DeepSeek, GLM, Qwen, Codex, OpenAI, Claude, local SLM) means API cost, or local-compute cost, that the same-model default entirely avoids. |
| **Reproducibility** | The current same-model default is already probabilistic by design (115Q); a second provider does not improve reproducibility — determinism is not, and was never meant to be, an advisory-evidence property. |
| **Disagreement handling** | Not yet needed operationally: with one provider, there is nothing to disagree with. Section 7 below defines the handling rule in advance, precisely so that adding a second provider later does not require inventing this rule under time pressure. |
| **Reliability** | The current provider's failure contract (115R/115T) already degrades safely (`UNKNOWN` evidence or explicit failure) with a single provider; a second provider does not change this property, it only doubles the number of places a failure can originate. |
| **Configuration burden** | A second provider is the first thing that would require real configuration (which provider, in what order, with what credentials) — directly contradicting 115Q Section 3's "no separate configuration required for default mode" until there is a concrete reason to accept that burden. |
| **Vendor coupling** | Every named future backend (DeepSeek/GLM/Qwen/Codex/OpenAI/Claude/local SLM) is a vendor or infrastructure dependency PCAE does not currently have and has explicitly avoided introducing (115H Section 8's DeepSeek boundary, restated across 115P/115Q/115R/115S/115T's own "Absolutely forbidden" lists). |
| **Governance risk** | Every phase since 115P has carried an explicit "no backend integration" no-go list specifically to prevent scope creep into vendor coupling. Approving a second provider now, with no identified gap driving it, would be the first phase in this arc to abandon that discipline without a concrete justification. |

**Conclusion**: every consideration in this table either shows no
benefit or shows a cost with no offsetting benefit. Implementing a
second provider now would be complexity and vendor coupling accepted
in advance of any concrete need — the antipattern this arc has
consistently avoided.

## 3. Decision

- **Implement a second provider now? No.**
- **Defer the second provider? Yes.**
- **Keep the extension point open? Yes.**

This decision is a review outcome, not a permanent prohibition: Section
5 below defines the concrete criteria under which a future phase should
revisit it.

## 4. Extension Point Preservation

A future second `AdvisoryProvider` can be added by implementing
**only** the `AdvisoryProvider` contract (115Q Section 2): declare
`provider_id`, `backend_kind`, `determinism`, and implement
`invoke(request: AdvisoryRequest) -> RawAdvisoryResponse`. Nothing
else changes. Concretely, adding a second provider requires **no**
redesign of:

- **Evidence / `EvidenceCollection`** — 115C's frozen shape; a second
  provider's evidence is ordinary `Evidence`, indistinguishable in
  structure from the first provider's.
- **Repository Skills** — `RepositoryConsistencyAdvisorySkill` (or any
  future `AdvisoryRepositorySkill`) already accepts any
  `AdvisoryProvider` via constructor injection (115S); a second
  provider substitutes in identically, exactly as 115T's portability
  tests already demonstrated with five test-only stand-ins.
- **Decision Evaluation** — `core/decision_evaluation.py` has never
  imported, and must never import, any `AdvisoryProvider` or advisory
  module at all (115Q/115R/115S/115T, verified at every phase); it
  consumes `EvidenceCollection` only, unaware a second provider exists.
- **Repository Transition Validator** — likewise never references any
  advisory module; verdicts are computed from `RepositoryState`/
  `Evidence` alone.
- **lifecycle commands** — no advisory module is wired into `pcae
  phase complete`, `pcae task finish`, `pcae push`, `pcae notify`,
  `pcae agent verify-handoff`, or `pcae runtime inspect` today; a
  second provider does not change that boundary.
- **Notification Policy** — advisory evidence has never been a
  notification input; a second provider does not become one.

This is not a hopeful claim — it is a structural consequence of 115Q's
frozen Dependency Direction (Repository Skills depend on Evidence
Providers/Advisory Providers; Decision Evaluation depends only on
Evidence; the Validator depends only on `EvaluationResult`) and 115T's
empirical portability proof.

## 5. Future Provider Criteria

A second provider should only be added when it provides **one or more**
of the following clear benefits — not by default, not speculatively:

- **Independent review** — a genuinely different model reviewing the
  first model's own prior work, to reduce same-model blind-spot risk
  (115Q Section 4's original split-model rationale).
- **Better domain expertise** — a backend demonstrably stronger at a
  specific advisory task the current provider handles poorly.
- **Local/offline advisory** — a local SLM usable when no acting model
  session is available at all (a genuinely different operating mode,
  not a preference).
- **Lower cost** — a materially cheaper backend for a specific,
  high-volume advisory workload that does not yet exist in this
  codebase.
- **Privacy constraint** — a requirement that advisory review never
  leave a local/private boundary, which the current acting model may
  or may not already satisfy depending on deployment.
- **Stronger consistency checking** — measurably better performance on
  the one bounded pilot question (or a future, separately-authorized
  expansion of pilot scope) than the current provider achieves.
- **Comparative evidence** — a deliberate, explicitly-authorized
  decision to run two providers on the same question specifically to
  produce comparative evidence for human review (not a default mode).

## 6. Multi-Provider Risks (Documented in Advance)

If a second provider is ever added, these risks apply and must be
managed, not discovered:

- **Conflicting advisory evidence** — two providers may produce
  contradictory findings about the same repository state.
- **Provider disagreement** — beyond simple conflict, providers may
  disagree on confidence, scope, or interpretation of the same
  question.
- **Nondeterministic outputs** — every real provider is probabilistic
  by contract (115Q); two probabilistic sources compound
  unpredictability, not average it away.
- **Cost/latency** — every additional provider invoked adds its own
  cost and latency, potentially per-evaluation.
- **Prompt drift** — two providers may require subtly different
  `AdvisoryRequest` framing to produce comparable output, risking the
  Prompt Builder accumulating provider-specific special cases (which
  would itself violate 115R's "Prompt Builder must not know which
  provider is used").
- **Provider-specific quirks** — different backends may have
  different failure modes, rate limits, or response quirks the
  Normalizer must handle uniformly without becoming
  provider-aware.
- **Hidden vendor coupling** — informal accommodations for one
  vendor's response format could silently reintroduce the coupling
  115H Section 8 and every subsequent phase explicitly forbade.
- **Operator confusion** — a human operator seeing two advisory
  opinions must be able to tell, unambiguously, that neither is
  authoritative and that PCAE's own deterministic evaluation still
  governs the outcome.

## 7. Disagreement Handling (Defined in Advance, Not Implemented)

If multiple advisory providers exist in a future phase:

- **Preserve all evidence** — every provider's `Evidence` items are
  kept; none is discarded because another provider disagrees (115B's
  Conflict Semantics, already frozen and unchanged: "Providers never
  silently choose one conflicting item").
- **Mark conflicts** — disagreeing evidence is surfaced as conflicting
  evidence to Decision Evaluation, exactly as 115E's
  `push_state_consistency` invariant already demonstrates for two
  independently-sourced deterministic facts disagreeing.
- **Never average or vote blindly** — confidence scores or findings
  from different providers are never numerically averaged or
  majority-voted into a single synthetic answer; each item remains its
  own evidence, attributable to its own provider.
- **Deterministic Decision Evaluation handles conflicts** — the same
  unmodified `evaluate()` machinery that already resolves conflicting
  deterministic evidence (115E) is the only mechanism that ever
  reasons about conflicting advisory evidence; no new conflict-
  resolution code path is introduced for advisory evidence
  specifically.
- **No provider becomes authority** — regardless of provider count,
  confidence, or apparent consensus, no advisory evidence — from one
  provider or many — ever becomes sole authority for Accept (115H/
  115Q/115T's frozen, repeatedly-verified rule).

## 8. Configuration Posture

**For now:**

- No provider configuration is needed.
- The current acting model remains the default `AdvisoryProvider`.

**Future split-model mode, if ever implemented:**

- Optional — never a required upgrade path.
- Explicit — a human/operator decision, never an automatic escalation
  triggered by provider count or usage.
- Isolated to the provider-selection layer — any future configuration
  mechanism lives entirely alongside `AdvisoryProvider`
  implementations, never inside `AdvisoryRepositorySkill`,
  `core/decision_evaluation.py`, or
  `core/repository_transition_validator.py`.
- Never leaks into Decision Evaluation or the Validator — both remain,
  permanently, unaware that provider selection exists at all (Section
  4, restated as a configuration-specific guarantee).

## 9. Roadmap Outcome

Because a second provider is deferred, the recommended next phase
focuses on **higher-quality evidence and advisory skill hardening**,
not provider proliferation — concretely: strengthening the one
existing pilot's evidence quality (richer findings, better-calibrated
confidence, deeper repository-consistency coverage within the already-
authorized bounded question) rather than adding a second backend to
answer the same question a second time.

## Relationship to Prior Phases

- **115P/115Q** designed and froze the Advisory Provider contract this
  review confirms remains sufficient without modification.
- **115R/115S** implemented the framework and the first real provider
  this review assesses as sound.
- **115T** empirically verified containment, boundaries, failure
  isolation, nondeterminism containment, and — critically for this
  review — backend portability with zero change required to Decision
  Evaluation or the Validator, the exact property Section 4 relies on.
- **115U** (this phase) is the first phase in the arc to conclude
  "not yet" rather than "implement the next piece" — a deliberate,
  documented pause, not a stall.

## Frozen Boundaries

Phase 115U freezes review conclusions and strategy language only:

- the second-provider decision: defer, keep the extension point open
  (Section 3)
- the extension point's preserved scope: no redesign of Evidence,
  `EvidenceCollection`, Repository Skills, Decision Evaluation, the
  Repository Transition Validator, lifecycle commands, or Notification
  Policy (Section 4)
- future provider criteria: independent review, domain expertise,
  local/offline advisory, lower cost, privacy constraint, stronger
  consistency checking, comparative evidence (Section 5)
- multi-provider risks, documented in advance (Section 6)
- disagreement handling, defined in advance and never implemented
  (Section 7)
- configuration posture: none needed now; any future split-model
  configuration stays isolated to the provider-selection layer
  (Section 8)
- the roadmap outcome: evidence-quality/advisory-skill hardening next,
  not provider proliferation (Section 9)

This phase implements no second Advisory Provider, no provider
selection, no model configuration, and no DeepSeek/GLM/Qwen/Codex-
specific/OpenAI-specific/Claude-specific/local-SLM integration. It
modifies no Advisory Provider runtime, Repository Skills runtime,
Evidence, Decision Evaluation, Repository Transition Validator, or
lifecycle command. No execution, authorization, Permission Broker
enforcement, plugin, Telegram inbound, REST, Web UI, or Dashboard
capability is introduced.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115V — Advisory Evidence Quality Hardening
