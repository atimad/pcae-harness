# PCAE Advisory Repository Skills Prototype

## Status

Phase 115R. Implements the framework 115P designed and 115Q froze as
contract, using **only** a deterministic `MockAdvisoryProvider`. No
real model backend is implemented or invoked. No DeepSeek, Claude API,
OpenAI, GLM, Qwen, Codex backend, local SLM, network call, subprocess
model execution, MCP model invocation, or execution capability exists
anywhere in this implementation.

## Purpose

Validate that 115P's architecture and 115Q's contract are actually
implementable, end-to-end, before any real model backend is
considered. Build the framework. Do not build AI integration.

Implementation module: `src/pcae/core/advisory_repository_skills.py`.
Tests: `tests/test_advisory_repository_skills_prototype_115r.py` (77
tests).

## Core Principle (Restated, Unchanged)

Advisory Repository Skills produce evidence. They never decide.

## Implemented Pipeline

```
Repository State
    -> RepositoryConsistencyAdvisorySkill.invoke()
    -> build_advisory_request()          (Prompt Builder)
    -> AdvisoryProvider.invoke()          (MockAdvisoryProvider only)
    -> RawAdvisoryResponse
    -> normalize_advisory_response()      (Normalizer)
    -> NormalizedAdvisoryResponse
    -> build_evidence_from_normalized()   (Evidence Builder)
    -> EvidenceCollection
```

This is the exact pipeline 115Q froze, implemented with concrete
Python types and functions. Nothing beyond `EvidenceCollection` is
implemented in this phase — no Decision Evaluation integration change,
no Validator integration change, no lifecycle change.

## Canonical Types

| Type | Frozen fields (115Q) | Implementation notes |
| --- | --- | --- |
| `AdvisoryRequest` | `bounded_context`, `question`, `response_schema_hint`, `timeout_seconds` | Frozen dataclass; rejects empty `bounded_context`/`question` and non-positive `timeout_seconds` at construction. |
| `RawAdvisoryResponse` | `raw_content`, `provider_id`, `succeeded` | Frozen dataclass; rejects empty `provider_id`. |
| `NormalizedAdvisoryResponse` | `findings`, `confidence_signal`, `references`, `limitations`, `normalization_status` | Frozen dataclass; structurally enforces the 115Q Evidence Builder contract at construction: `normalization_status` must be one of `("succeeded", "partial", "failed")`; a non-`failed` status requires at least one finding; `limitations` must be non-empty always. |

## `AdvisoryProvider` Interface

`AdvisoryProvider` is an `ABC` declaring `provider_id`, `backend_kind`,
`determinism`, and one abstract method: `invoke(request:
AdvisoryRequest) -> RawAdvisoryResponse`. No provider-specific logic
exists in the interface itself — only the shape.

## `MockAdvisoryProvider`

The only concrete `AdvisoryProvider` implemented in this phase:

- `backend_kind = "deterministic_mock"`, `determinism =
  EvidenceDeterminism.DETERMINISTIC` (115Q Section 2 explicitly permits
  this for a deterministic mock provider).
- Constructed with a `responses: Mapping[str, RawAdvisoryResponse]`
  keyed by `AdvisoryRequest.question`, plus an optional
  `default_response` for unmatched questions.
- `invoke()` is a pure, in-memory dictionary lookup: no randomness, no
  network I/O, no filesystem writes, no subprocess, no execution of
  any kind. The same request always returns the same response object.
- Supports deterministic failure scenarios by construction: a caller
  configures a canned `RawAdvisoryResponse(succeeded=False)` or a
  canned response with malformed/unparseable `raw_content` for a given
  question, and `invoke()` returns it exactly as configured every time.

## Prompt Builder

`build_advisory_request(root, *, evidence_categories, objective,
constraints=DEFAULT_ADVISORY_CONSTRAINTS) -> AdvisoryRequest`:

- Builds a small, deterministic `bounded_context` string (repository
  root presence, requested evidence categories, declared constraints)
  — never a raw filesystem dump, never secret material.
- `question` is always the caller's explicit `objective` — never an
  open-ended prompt.
- Declares `DEFAULT_ADVISORY_CONSTRAINTS = ("no_secrets",
  "no_unrestricted_command_capability", "no_execution_request",
  "advisory_request_only")` in every request's bounded context.
- Takes no `AdvisoryProvider` parameter and imports no provider type —
  verified by
  `TestPromptBuilder::test_prompt_builder_signature_has_no_provider_parameter`.

## Response Normalizer

`normalize_advisory_response(response: RawAdvisoryResponse) ->
NormalizedAdvisoryResponse`:

- A provider-level failure (`succeeded=False`) normalizes immediately
  to `normalization_status="failed"`.
- Unparseable JSON, a non-object JSON value, a response claiming any
  unauthorized top-level field (`verdict`, `commit`, `push`,
  `authorized`, `execute`, `finalize` — 115Q's Model Boundary example
  list), or a missing/empty `findings` list each normalize to
  `"failed"` outright — never partially accepted.
- A response with some invalid finding entries (non-string, wrong
  shape) alongside valid ones normalizes to `"partial"`, keeping only
  the valid findings and recording that some were dropped via the
  status itself.
- Missing or non-numeric `confidence_signal` degrades to `None`
  (never fabricated); missing/blank `limitations` degrades to an
  honest placeholder string, never left empty (the Evidence Builder
  contract requires non-empty limitations on every item).

## Evidence Builder

`build_evidence_from_normalized(normalized, *, provider_id, producer,
category, scope, evidence_id_prefix) -> EvidenceCollection`:

- One `Evidence` item per finding for a `"succeeded"`/`"partial"`
  normalization, each: `determinism=PROBABILISTIC`, `confidence`
  derived from `confidence_signal` (≥0.75 → `HIGH`, ≥0.4 → `MEDIUM`,
  otherwise/`None` → `LOW`), `freshness=CURRENT`, `references` and
  `limitations` carried through from the normalized response, and
  `provenance` recording `produced_from="AdvisoryProvider:<provider_id>"`
  with `deterministic_origin=False`.
- A `"failed"` normalization produces exactly one `Evidence` item with
  `freshness=UNKNOWN`, `confidence=UNKNOWN`,
  `observed_value="unavailable"` — 115D's established provider-failure
  pattern, reused unmodified. Never a fabricated passing observation.
- Every item's `category` is `EvidenceCategory.AI_REVIEW` for the first
  pilot skill (Section below) — the category 115I's contract already
  reserved for "model-produced review evidence."

## First Advisory Repository Skill

`RepositoryConsistencyAdvisorySkill` (subclass of the new
`AdvisoryRepositorySkill` base class, itself a `RepositorySkill`):

- Implements 115Q's first-pilot scope choice: **repository consistency
  review** (one of the three named options, chosen alone — not
  documentation or report consistency review).
- Manifest: `capabilities=(RepositorySkillCapability.AI_REVIEW,)`,
  `determinism=PROBABILISTIC`, `model_produced=True`,
  `evidence_categories=(EvidenceCategory.AI_REVIEW,)`,
  `side_effect_policy="none"` (the `RepositorySkillManifest`
  constructor already rejects any other value).
- Defaults to a `MockAdvisoryProvider()` instance if no provider is
  supplied — any `AdvisoryProvider` implementation may be substituted
  without changing this class (the backend-agnostic principle,
  concretely demonstrated).
- `invoke(context)` wires the full pipeline (Prompt Builder ->
  provider -> Normalizer -> Evidence Builder) and returns a
  `RepositorySkillResult`: `SUCCESS` with evidence (including the
  `UNKNOWN`-evidence failure case) for any handled outcome, or
  `FAILED` with a non-empty `failure_reason` only when the
  `AdvisoryProvider.invoke()` call itself raises.

**Not added to `build_default_registry()`.** 115J's four deterministic
skills' default registry is unchanged — the advisory skill is an
opt-in, separately constructed skill, never automatically registered.

## End-to-End Demonstration

`tests/test_advisory_repository_skills_prototype_115r.py`'s
`TestEndToEndAdvisoryPipeline` exercises the full pipeline against a
`MockAdvisoryProvider` configured with a canned success response,
proving: the skill returns `SUCCESS`, produces the expected evidence
count, is deterministic across repeated invocations against the same
context, and never mutates the repository (verified against a real,
git-initialized `tmp_path` fixture — file listing and git log are
identical before and after `invoke()`).

## Deterministic Failure Handling

`TestDeterministicFailureHandling` proves three distinct failure
paths, each handled without exception escaping (unless
`context.strict=True`, matching every other Repository Skill's
established convention):

1. **Provider-level failure** (`RawAdvisoryResponse(succeeded=False)`)
   -> Normalizer `"failed"` -> Evidence Builder emits one `UNKNOWN`
   evidence item -> skill reports `SUCCESS` (the skill itself ran to
   completion; the *evidence* is honestly unknown).
2. **Malformed/unparseable raw content** (`succeeded=True` but garbage
   `raw_content`) -> identical `UNKNOWN`-evidence outcome.
3. **Provider invocation raising an exception** -> the skill itself
   reports `RepositorySkillResult(status=FAILED, failure_reason=...)`
   with zero evidence — the explicit second failure outcome 115I/115Q
   both froze, never disguised as evidence.

## No Real Model / No Network / No Execution

Verified structurally:

- No network primitive (`socket`, `urllib`, `requests`, `httpx`,
  `http.client`) or subprocess/execution primitive (`subprocess`,
  `os.system`, `Popen(`, `exec(`, `eval(`) appears anywhere in the
  module's executable code (docstrings, which *describe* these
  prohibitions in prose, are excluded from the check).
- No forbidden backend name (`deepseek`, `claude`, `openai`, `glm`,
  `qwen`, `codex`, `mcp`) appears in any import, identifier, class
  name, or function name in the module.
- `core/decision_evaluation.py`, `core/repository_transition_validator.py`,
  `core/repository_transition_integration.py`,
  `core/repository_skills.py`, `core/repository_skills_integration.py`,
  every lifecycle command module, and Notification/handoff/post-push
  modules never reference `advisory_repository_skills` at all.
- `build_default_registry()` (115J, unchanged) still returns exactly
  four deterministic skills — the advisory skill is not among them.
- Execution capability remains unavailable: the real repository's
  `E-runtime-002` evidence (via the unmodified 115M skills-integration
  path) is still `"unavailable"`.

## Remaining Work Before a First Real Provider

This phase implements no real `AdvisoryProvider`. Before 115S (First
Advisory Provider Integration, Current Acting Model) or any later
real-backend phase:

- a concrete `AdvisoryProvider` implementation must invoke the actual
  acting model (per 115P/115Q's default same-model mode) rather than a
  canned lookup — this is explicitly out of scope here
- the Normalizer's schema-validation rules (Section "Response
  Normalizer" above) will need to be exercised against real model
  output shapes, which may reveal additional malformed-response
  patterns to reject
- no split-model configuration exists yet (115Q Section 4) — still
  entirely deferred
- this prototype's `RepositoryConsistencyAdvisorySkill` is not wired
  into any registry a real evaluation consumes; a future integration
  phase decides if/how that happens, mirroring 115M/115N's own
  staged migration for deterministic skills

## Frozen Boundaries Preserved

This phase adds implementation but changes no frozen contract from
115P or 115Q: every type name, field name, and boundary rule
(backend-agnostic principle, prompt boundary, response boundary,
Evidence Builder contract, failure contract, safety rules, first pilot
scope) is implemented exactly as frozen, not renamed or reshaped.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115S — First Advisory Provider Integration (Current Acting Model)
