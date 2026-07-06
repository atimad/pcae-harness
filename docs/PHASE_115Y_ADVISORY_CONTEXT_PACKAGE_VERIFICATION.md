# Phase 115Y — Advisory Context Package Verification & Compatibility

## Status

Completed. Verification only: no `AdvisoryContextPackage` integration
into any Advisory Provider runtime added, no Repository Skill
modified, no Evidence Provider modified, no Decision Evaluation
modified, no Repository Transition Validator modified, no lifecycle
command modified, no model configuration added, no second provider
added, no DeepSeek/GLM/Qwen/Codex/OpenAI/Claude-specific/local-SLM
integration introduced. No execution, authorization, Permission Broker
enforcement, plugin, Telegram inbound, REST, Web UI, or Dashboard
capability introduced.

## Purpose

Verify that 115X's `AdvisoryContextPackage` prototype is
deterministic, bounded, prompt-safe, serialization-compatible, and
ready to be consumed by a future advisory pipeline — without
integrating it into anything yet.

## Determinism Verification

Identical inputs produce equal `AdvisoryContextPackage` objects,
identical `to_dict()` serialization, and identical JSON output across
20 repeated constructions. Validation outcomes (both acceptance and
rejection) are identical across 10 repeated attempts. Section
ordering from `ordered_sections_for_prompt_assembly()` is stable
across repeated builds.

## Required Sections Verification

Confirmed exactly 15 sections exist, each present in `to_dict()`
output, each a required (no-default) constructor argument, and each
individually rejected via `from_dict()` when missing — 15 dedicated
parametrized tests, one per section.

## Trust Boundary Verification

Confirmed the four trust classes remain distinct; trusted instruction
sections share the trusted class; evidence sections share the
deterministic class; untrusted content sections never share a trusted
or evidence class; the fourth class (model-produced output) exists in
the frozen vocabulary but is never assigned by the package itself. A
section's cosmetic `name` field cannot spoof its trust class — a
section named `"trusted_pcae_instructions"` but declared
`untrusted_repository_content` is still validated, labelled, and
ordered as untrusted, and the package's own `trusted_pcae_instructions`
field is completely unaffected by the spoof attempt.

## Prompt-Injection Boundary Verification

Four adversarial content strings (fake system overrides, fake
authorization/execution instructions, fake instruction-tag injection,
fake push instructions) were placed in `untrusted_repository_content`
sections and confirmed to: remain classified `untrusted_repository_content`,
never migrate into `trusted_pcae_instructions` or
`constraints_and_no_go_rules` content, and always sort after every
trusted section in `ordered_sections_for_prompt_assembly()`'s output
regardless of how many adversarial sections are present. Every
section's `prompt_label` is present and class-distinguishing.

## Size Budget Verification

Content exactly at a section's budget is accepted; one character over
is rejected. Per-section overrides are enforced independently of the
global default. The total budget is verified to be the true sum across
every section and every artifact reference's summary, not merely the
largest single section. The default budget's tighter ceiling for
untrusted repository content is reconfirmed.

## Redaction / Secrets Policy Verification

`redaction_summary` remains a required, non-defaultable field —
omitting it raises `TypeError`. Declared redactions are recorded, not
dropped. The "no redactions" case is an explicit present record, never
an absent one. **Documented scope boundary**: `AdvisoryContextPackage`
validates that a `redaction_summary` is present and internally
consistent (115W Section 5), but does not itself scan section content
for secret-shaped strings — redacting sensitive content before
constructing a section, and recording that a redaction happened,
remains the assembler's responsibility. This is not a regression:
115X's scope was the package object, validation, and serialization,
never a secret-detection heuristic.

## Provenance Verification

Package-level and artifact-reference-level provenance are both
present and survive a full `to_dict()`/`from_dict()` round trip
exactly, including `evidence_ids`. Evidence-summary sections can cite
Evidence IDs traceably via their `references` field.

## Artifact Reference Verification

References are structured (`kind`/`locator`/`summary`), never free
text; a full-file-sized summary (1000 lines) is rejected outright by
the existing `MAX_ARTIFACT_SUMMARY_CHARS` bound; references identify
artifacts by locator (path/Evidence ID/commit hash), never by
embedding; all three kinds (`file`, `evidence`, `commit`) remain
distinct and frozen.

## Allowed Advisory Question Verification

Exactly one question is accepted. Six near-miss variants (trailing/
leading whitespace, missing question mark, case variants) are all
individually confirmed rejected — confirming the check is an exact
match, not a fuzzy or case-insensitive one.

## JSON Compatibility Verification

`to_dict()` output is recursively confirmed to contain only JSON
primitive types (str, int, float, bool, list, dict, None — no
`MappingProxyType`, no tuple, no custom object). Output survives a
real `json.dumps()`/`json.loads()` round trip and reconstructs an
equal package. `from_dict()` ignores unknown extra keys gracefully
(forward-compatible with a future schema addition). Serialization is
stable across five repeated round trips.

## No Hidden Integration Verification

Reconfirmed: no lifecycle command, Notification Policy, handoff
verification, post-push canonicalization, Decision Evaluation, the
Repository Transition Validator, any Advisory Provider, or any
Repository Skill references `advisory_context_package` at all; the
module itself imports none of them; the default Repository Skills
registry still returns exactly 115J's four deterministic skills; no
provider-registry or backend-selection class exists anywhere in the
module.

## Tests

`tests/test_advisory_context_package_verification_115y.py` (new, 87
tests): deterministic serialization, required sections, trust
boundaries, prompt-injection safety, size budgets, redaction policy,
provenance, artifact references, allowed advisory question, JSON
compatibility, no hidden integration, execution unavailable.

## Validation

- focused context package / advisory / repository-skills / evidence / decision-evaluation tests: see final report
- fast_green: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115Y`: see final report

## Governance

No `AdvisoryContextPackage` integration added, no Repository Skill
modified, no Evidence Provider modified, no Decision Evaluation
modified, no Repository Transition Validator modified, no lifecycle
command modified, no model configuration added, no second provider
added, no DeepSeek/GLM/Qwen/Codex/OpenAI/Claude-specific/local-SLM
integration.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115Z — Advisory Skill Pilot Hardening
