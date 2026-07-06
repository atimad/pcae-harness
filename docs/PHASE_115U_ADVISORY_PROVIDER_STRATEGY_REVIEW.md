# Phase 115U — Advisory Provider Strategy & Extension Point Review

## Status

Completed. Architecture and review only: no second Advisory Provider
implemented, no provider selection added, no model configuration
added, no DeepSeek/GLM/Qwen/Codex-specific/OpenAI-specific/Claude-
specific/local-SLM integration added, no Advisory Provider runtime
modified, no Repository Skills runtime modified, no Evidence modified,
no Decision Evaluation modified, no Repository Transition Validator
modified, no lifecycle command modified. No execution, authorization,
Permission Broker enforcement, plugin, Telegram inbound, REST, Web UI,
or Dashboard capability introduced.

## Purpose

Decide whether PCAE needs a second Advisory Provider now, while
preserving the ability to add one later without architectural
redesign.

Canonical strategy document:

- `docs/PCAE_ADVISORY_PROVIDER_STRATEGY.md`

## Core Principle

The advisory provider may produce evidence. PCAE remains the
authority.

## Core Question

Do we need a second advisory provider now?

## Advisory Provider Strategy Summary

Reviewed the current advisory provider model
(`CurrentActingModelAdvisoryProvider`, 115R/115S/115T) across five
properties — same-model default, bounded pilot scope, one request/one
response/one `EvidenceCollection`, stateless operation, normalized
evidence boundary, provider containment — and found all five sound
and sufficient. Evaluated a second provider against ten
considerations (benefit, complexity, latency, cost, reproducibility,
disagreement handling, reliability, configuration burden, vendor
coupling, governance risk): every consideration showed no benefit or a
cost with no offsetting benefit.

## Second-Provider Decision

**Defer.** Do not implement a second provider now. Keep the extension
point open. This is a review outcome, not a permanent prohibition —
Section 5 of the strategy document defines concrete criteria for
revisiting it.

## Extension Point Summary

A future second `AdvisoryProvider` can be added by implementing only
the frozen `AdvisoryProvider` contract (`provider_id`, `backend_kind`,
`determinism`, `invoke()`). No redesign is required of Evidence,
`EvidenceCollection`, Repository Skills, Decision Evaluation, the
Repository Transition Validator, lifecycle commands, or Notification
Policy — 115Q's frozen dependency direction and 115T's empirical
portability proof (five test-only `backend_kind` stand-ins, zero
change to Decision Evaluation or the Validator) both already
demonstrate this structurally, not merely by assertion.

## Future Provider Criteria

A second provider should only be added for one or more of: independent
review, better domain expertise, local/offline advisory, lower cost, a
privacy constraint, stronger consistency checking, or deliberate
comparative evidence — never by default.

## Multi-Provider Risk Summary

Documented in advance: conflicting advisory evidence, provider
disagreement, compounding nondeterminism, cost/latency, prompt drift,
provider-specific quirks, hidden vendor coupling, and operator
confusion.

## Disagreement Handling

If multiple providers exist later: preserve all evidence, mark
conflicts (never silently resolved), never average or vote blindly,
let the existing unmodified Decision Evaluation machinery handle
conflicts exactly as it already does for deterministic evidence, and
no provider ever becomes authority regardless of count or apparent
consensus.

## Configuration Posture

For now: no provider configuration needed; current acting model
remains default. Any future split-model mode would be optional,
explicit, isolated entirely to the provider-selection layer, and would
never leak into Decision Evaluation or the Validator.

## Roadmap Recommendation

Because the second provider is deferred, the next phase should focus
on higher-quality evidence and advisory skill hardening — not provider
proliferation.

## Tests

`tests/test_phase_115u_advisory_provider_strategy_review.py` (new):
architecture/documentation verification only. Verifies both new docs
exist and contain: the same-model default, the second-provider
decision, the extension point, future provider criteria, multi-
provider risks, disagreement handling, configuration posture, the
roadmap outcome, and explicit "no implementation"/"execution
capability remains unavailable" confirmations. No implementation-claim
strings are asserted to exist — the tests confirm none were added.

## Validation

- focused architecture/documentation tests: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115U`: see final report

## Governance

No second Advisory Provider implemented, no provider selection added,
no model configuration added, no DeepSeek/GLM/Qwen/Codex-specific/
OpenAI-specific/Claude-specific/local-SLM integration added, no
Advisory Provider runtime, Repository Skills runtime, Evidence,
Decision Evaluation, Repository Transition Validator, or lifecycle
command modified.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115V — Advisory Evidence Quality Hardening
