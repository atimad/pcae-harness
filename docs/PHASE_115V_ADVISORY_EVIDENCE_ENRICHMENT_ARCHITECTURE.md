# Phase 115V — Advisory Evidence Enrichment Architecture

## Status

Completed. Architecture and design only: no new Evidence Provider
implemented, no new Repository Skill implemented, no Advisory
Provider runtime modified, no second advisory provider added, no
model configuration added, no DeepSeek/GLM/Qwen/Codex/OpenAI/Claude-
specific/local-SLM integration introduced, no Decision Evaluation
modified, no Repository Transition Validator modified, no lifecycle
command modified. No execution, authorization, Permission Broker
enforcement, plugin, Telegram inbound, REST, Web UI, or Dashboard
capability introduced.

## Purpose

Design how PCAE improves advisory quality by enriching the
deterministic evidence supplied to Advisory Repository Skills — the
axis of improvement 115U's roadmap outcome named instead of a second
advisory provider.

Canonical architecture document:

- `docs/PCAE_ADVISORY_EVIDENCE_ENRICHMENT.md`

## Core Principle

Models improve by receiving better evidence, not by receiving more
authority.

## Advisory Evidence Enrichment Summary

Enrichment supplies an Advisory Repository Skill's Prompt Builder with
richer deterministic evidence — drawn from existing 115D Evidence
Providers, 115J Repository Skills, and future deterministic sources —
so a bounded advisory answer has more relevant context to reason from,
without changing what the model is permitted to do with it.
Containment (115Q/115T), the Normalizer boundary, and Decision
Evaluation authority are all completely unaffected — enrichment only
ever adds to `bounded_context`, never changes anything downstream of
the Prompt Builder.

## Evidence Category Summary

Eleven categories named: repository state, git/history, changed-files,
test evidence, architecture evidence, dependency/module evidence,
documentation evidence, governance evidence, runtime capability
evidence, report/metadata consistency evidence, and future semantic/
code graph evidence — each mapped to its deterministic source
(existing 115D/115J providers/skills where applicable, or named as
future work).

## Priority Matrix Summary

Each category classified by value, implementation difficulty,
determinism, risk, and expected advisory benefit. Recommended tiering:
Tier 1 (repository state, changed-files, governance evidence,
report/metadata consistency — highest value, lowest difficulty), Tier
2 (git/history, test evidence, runtime capability), Tier 3
(architecture, dependency/module, documentation, future semantic/code
graph evidence).

## Advisory Context Package Summary

A future input bundle — bounded repository summary, deterministic
evidence, current transition/question, constraints/no-go rules,
relevant artifacts, known limitations — designed as a target for
115W's contract freeze, not implemented here and not a modification of
`AdvisoryRequest`'s already-frozen four fields.

## Safety Boundary Summary

Enriched evidence must never grant execution capability, expose
secrets, include unbounded repository dumps, allow prompt injection
from repository files, allow model output to bypass normalization, or
change Decision Evaluation authority.

## Prompt-Injection Handling

Repository-derived content is always untrusted input, never
instructions. A future assembled prompt must separate trusted PCAE
instructions, deterministic evidence, and untrusted repository content
(always delimited and framed as observed content, not instructions) —
a new, complementary concern to 115Q's Normalizer boundary (which
protects PCAE from untrusted model output, not untrusted repository
input).

## Summarization Strategy

Deterministic summaries preferred over a second model call; bounded
length; provenance preserved; references retained; raw evidence never
blindly pasted.

## Future Roadmap

115W — Advisory Context Package Contract (freeze fields/bounded-length
numbers/injection-separation rule). 115X — Advisory Context Package
Prototype (implement using Tier 1 evidence only). 115Y — Advisory
Evidence Enrichment Verification (verify containment/boundaries/
injection handling empirically). 115Z — Advisory Skill Pilot Hardening
(harden the one bounded pilot's usefulness using the verified
enriched package).

## Tests

`tests/test_phase_115v_advisory_evidence_enrichment_architecture.py`
(new): architecture/documentation verification only. Verifies both
new docs exist and contain: the enrichment definition, all eleven
evidence categories, the priority matrix and tiering, the Advisory
Context Package components, safety boundaries, prompt-injection
handling, evidence summarization rules, the four-phase future roadmap,
and explicit "no implementation"/"execution capability remains
unavailable" confirmations. No implementation-claim strings are
asserted to exist — the tests confirm none were added.

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
- `pcae skill invoke phase-finalization 115V`: see final report

## Governance

No new Evidence Provider implemented, no new Repository Skill
implemented, no Advisory Provider runtime modified, no second advisory
provider added, no model configuration added, no DeepSeek/GLM/Qwen/
Codex/OpenAI/Claude-specific/local-SLM integration introduced, no
Decision Evaluation modified, no Repository Transition Validator
modified, no lifecycle command modified.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115W — Advisory Context Package Contract
