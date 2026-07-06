# Phase 115W — Advisory Context Package Contract

## Status

Completed. Contract/design only: no `AdvisoryContextPackage` runtime
implemented, no Advisory Provider runtime modified, no Repository
Skill modified, no Evidence Provider modified, no Decision Evaluation
modified, no Repository Transition Validator modified, no lifecycle
command modified, no model configuration added, no second provider
added, no DeepSeek/GLM/Qwen/Codex/OpenAI/Claude-specific/local-SLM
integration introduced. No execution, authorization, Permission Broker
enforcement, plugin, Telegram inbound, REST, Web UI, or Dashboard
capability introduced.

## Purpose

Freeze the `AdvisoryContextPackage` contract — the bounded, trusted,
provenance-preserving context that may be supplied to an Advisory
Repository Skill's Prompt Builder — before any implementation. 115V
designed the enrichment categories and named the future context
bundle's component list; 115W freezes that bundle as an exact,
field-named contract.

Canonical contract document:

- `docs/PCAE_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md`

## Core Principle

Advisory models receive bounded, trusted, provenance-preserving
context. They do not receive unrestricted repository access.

## Context Package Contract Summary

`AdvisoryContextPackage` is frozen with exactly 15 required sections;
no section is optional. Four trust-boundary classes are frozen
(trusted PCAE instructions, deterministic PCAE evidence, untrusted
repository content, model-produced advisory output) with an explicit
mapping of which sections belong to which class. The prompt-injection
boundary requires `untrusted_repository_content` to be its own
section, always delimited/labelled, never honored as instructions, with
trusted sections always assembled last. Size limits freeze the
existence (not fixed values) of a total package budget and per-section
budgets, a deterministic-summarization requirement, and an absolute
prohibition on unbounded repository dumps. The redaction/secrets
policy excludes secrets, tokens, credentials, private env values,
unrestricted logs, and raw config secrets — with every redaction
recorded, never silently dropped. Provenance is preserved at both the
package level and the item level. Artifacts are referenced by path/ID/
hash rather than embedded in full wherever a reference suffices. The
only currently allowed `advisory_question` is "Is the repository state
internally consistent?" Future extensibility (documentation/report/
architecture consistency review, code review, security review) is
documented but explicitly not implemented or authorized.

## Required Sections

`package_id`, `created_at_utc`, `objective`, `advisory_question`,
`trusted_pcae_instructions`, `repository_summary`,
`deterministic_evidence_summary`, `transition_context`,
`constraints_and_no_go_rules`, `artifact_references`,
`untrusted_repository_content`, `provenance`, `limitations`,
`size_budget`, `redaction_summary` — all 15 required, none optional.

## Trust Boundary Summary

Trusted PCAE instructions (`trusted_pcae_instructions`,
`constraints_and_no_go_rules`, `advisory_question`, `objective`) are
the only content ever treated as instructional. Deterministic PCAE
evidence (`repository_summary`, `deterministic_evidence_summary`,
`transition_context`, `artifact_references`) is structured data, never
instructional. Untrusted repository content
(`untrusted_repository_content`) is always delimited/labelled, never
instructional. Model-produced advisory output never re-enters a
package.

## Prompt-Injection Handling

`untrusted_repository_content` is structurally separate from
`trusted_pcae_instructions`; content is always delimited and labelled
as observed, not instructional; no instruction found in repository
content may ever be honored; trusted sections are always assembled
last so they are never supersedable by preceding repository-derived
text. Complementary to, not a substitute for, 115Q's Normalizer
boundary (which protects PCAE from untrusted model output, not
untrusted repository input).

## Size / Redaction / Provenance Rules

Size: total package budget and per-section budgets exist and are
enforced (concrete numbers deferred to 115X); deterministic
summarization required; no unbounded dumps ever, with gaps reported
via `limitations` instead. Redaction: no secrets/tokens/credentials/
private env values/unrestricted logs/raw config secrets; every
redaction recorded in `redaction_summary`. Provenance: package-level
(`provenance`) and item-level (every evidence summary/artifact
reference traceable to its source), never discarded during
summarization.

## Artifact Reference Model

Files referenced by path (with bounded diff summary where useful),
evidence referenced by Evidence ID (with summarized `observed_value`/
`explanation` only), commits referenced by hash (with bounded message
excerpt only) — full-content embedding reserved for cases where a
reference alone would be useless and the content already satisfies
every size/redaction rule.

## Allowed Advisory Question

Exactly one: `"Is the repository state internally consistent?"` —
identical to 115S/115T's verified pilot scope, unchanged and
unexpanded.

## Tests

`tests/test_phase_115w_advisory_context_package_contract.py` (new):
architecture/contract verification only. Verifies both new docs exist
and contain: the required-sections list, trust boundaries,
prompt-injection boundary, size limits, redaction policy, provenance
rules, artifact-reference rules, the allowed advisory question, future
extensibility, and explicit "no implementation"/"execution capability
remains unavailable" confirmations. No implementation-claim strings
are asserted to exist — the tests confirm none were added.

## Validation

- focused contract/architecture tests: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115W`: see final report

## Governance

No `AdvisoryContextPackage` runtime implemented, no Advisory Provider
runtime modified, no Repository Skill modified, no Evidence Provider
modified, no Decision Evaluation modified, no Repository Transition
Validator modified, no lifecycle command modified, no model
configuration added, no second provider added, no DeepSeek/GLM/Qwen/
Codex/OpenAI/Claude-specific/local-SLM integration introduced.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115X — Advisory Context Package Prototype
