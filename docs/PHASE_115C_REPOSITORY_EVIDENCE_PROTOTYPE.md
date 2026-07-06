# Phase 115C — Repository Evidence Framework Prototype

## Status

Completed. Runtime object prototype only: no Repository Skills, no
Decision Evaluation, no Repository Transition Validator integration, no
lifecycle command changes, no Notification Policy changes, no Canonical
Artifact Promotion changes, no Push-State Reconciliation changes, no
Post-Push Canonicalization changes, no execution capability, no
authorization, no Permission Broker enforcement, no plugins, no Telegram
inbound, no REST, no Web UI, and no Dashboard.

## Purpose

Implement the runtime representation of the Evidence contract frozen by
115B (`docs/PCAE_REPOSITORY_EVIDENCE_FRAMEWORK.md` and
`docs/PCAE_EVIDENCE_PROVIDER_CONTRACT.md`): immutable `Evidence`,
`EvidenceCollection`, the four frozen enumerations, `EvidenceReference`,
and `EvidenceProvenance`. This phase implements only the Evidence model
and supporting container types — nothing consumes it yet.

Implementation: `src/pcae/core/evidence.py`.

## Implemented Runtime Objects

### Evidence

An immutable (`@dataclass(frozen=True)`) item carrying exactly the 14
fields frozen by 115B — `evidence_id`, `source`, `category`, `producer`,
`timestamp_utc`, `freshness`, `confidence`, `determinism`, `scope`,
`references`, `observed_value`, `expected_value`, `explanation`, and
`limitations` — plus one additional field, `provenance`
(`EvidenceProvenance`), added by this phase per Objective 5. `category`,
`freshness`, `confidence`, and `determinism` accept either an enum member
or its raw frozen string value at construction; both are normalized to
the enum member in `__post_init__`, and an invalid value raises
`ValueError` via the enum's own constructor. Six fields
(`evidence_id`, `source`, `producer`, `timestamp_utc`, `scope`,
`explanation`) must be non-empty strings.

### EvidenceCollection

An ordered, immutable container of `Evidence` items. Provides:

- ordered iteration (`__iter__`, insertion order preserved)
- `__len__`, `__contains__` (by `evidence_id`)
- `by_id(evidence_id)` lookup
- `by_category(...)`, `by_source(...)`, `by_determinism(...)`,
  `by_confidence(...)` filtering, each returning a new
  `EvidenceCollection`
- `add(evidence)`, returning a new `EvidenceCollection` — the original is
  never mutated

Duplicate `evidence_id` values are rejected both at construction and at
`add()` time. `EvidenceCollection` contains no decision logic and no
evaluation: conflicting evidence (115B "Conflict Semantics") is preserved
exactly as given, never silently resolved, voted on, or chosen between —
see `TestConflictingEvidencePreserved` in
`tests/test_evidence_collection.py`.

### The Four Frozen Enumerations

`EvidenceCategory` (15 values), `EvidenceDeterminism` (5 values),
`EvidenceConfidence` (4 values), and `EvidenceFreshness` (4 values), each
a `class X(str, Enum)` using exactly the values frozen in 115B. No value
was added, removed, or renamed.

### EvidenceReference

A minimal citation shape — `evidence_id: str` plus an optional `note:
str | None` — for decision explanations to cite Evidence IDs (115B
"Explanation Reference Model", e.g. citing `E-git-001`).

**Intentionally distinct from `core/advisory_runtime.py`'s
`EvidenceReference`** (113B §3: `domain`/`object_id`/`field_path`/
`evidence_summary`, a pointer into a Runtime Snapshot field). The two
serve different citation models and are not unified by this phase — the
Advisory Runtime's reference cites a snapshot field path; the Evidence
Framework's reference cites a stable Evidence ID within one decision
evaluation. Both classes coexist under the same name in different
modules; callers must import the one relevant to their context.

### EvidenceProvenance

Metadata-only, containing `producer`, `produced_from`, `timestamp`, and
`deterministic_origin`. Carries no runtime behavior — nothing in this
module or any other reads `EvidenceProvenance` to make a decision.

## Immutability

- `Evidence`, `EvidenceCollection`, `EvidenceReference`, and
  `EvidenceProvenance` are all `@dataclass(frozen=True)`; reassigning any
  field raises `dataclasses.FrozenInstanceError`.
- `@dataclass(frozen=True)` alone only prevents field *reassignment* — it
  does not stop a caller mutating a dict/list they handed to the
  constructor, nor mutating a dict/list read back out (the same gap
  documented and fixed for `PluginDescriptor.manifest` in
  `core/runtime_registry.py`, 110E/110F). `Evidence.references` is
  coerced to a `tuple`; `Evidence.observed_value`/`expected_value` are
  deep-frozen via `_freeze_json_value` (dicts become read-only
  `MappingProxyType` views, lists become tuples, recursively) so that
  neither a caller's original object nor the value read back from
  `Evidence` can mutate stored state. See
  `TestEvidenceImmutability` in `tests/test_evidence.py`.
- `EvidenceCollection.add(evidence)` returns a **new**
  `EvidenceCollection`; the original is left untouched.

## Serialization

`to_dict()`/`from_dict()` on all four dataclasses, JSON-compatible:

- Enum fields serialize to their plain string `.value`.
- `references` serializes to a `list`; deep-frozen `observed_value`/
  `expected_value` are unfrozen back to plain `dict`/`list` via
  `_unfreeze_json_value` so `json.dumps(...)` accepts the result
  directly.
- `Evidence.from_dict(...)` accepts raw string enum values (it delegates
  to the same constructor that accepts either form).
- `EvidenceCollection.to_dict()`/`from_dict()` wrap a list of
  `Evidence.to_dict()`/`from_dict()` results under one `"items"` key,
  preserving order.
- No persistence layer: nothing writes these dicts to disk. Raw evidence
  persistence remains future work per 115B's Persistence Boundary.

## Validation

- Required fields must be non-empty strings (see above).
- Enum values are validated by construction through the enum's own
  constructor (`EvidenceCategory(value)` etc.), which raises `ValueError`
  for any value outside the frozen set.
- Duplicate `evidence_id` values inside one `EvidenceCollection` are
  rejected, both at construction and at `add()`.
- Repository semantics are explicitly **not** validated: a
  `references` entry does not need to be a real commit hash, `scope`
  does not need to be a real repository path, and `source` is not
  checked against a provider registry (there is none yet). See
  `TestNoRepositorySemanticsValidation` in
  `tests/test_evidence_validation.py`.

## Future Integration Points (Not Implemented Here)

- **Evidence Providers**: 115B's Provider Contract (Provider ID,
  determinism class, categories produced, required inputs, scope,
  limitations) has no runtime implementation or registry yet — a future
  phase (115D, per Recommended Next Phase) would introduce concrete
  providers producing `Evidence`/`EvidenceCollection` instances from real
  repository state.
- **Decision Framework / Decision Evaluation**: 115A's
  `Repository State -> Repository Transition -> Evidence Collection ->
  Decision Evaluation -> Transition Result -> Repository Artifact ->
  Repository Event` chain has no evaluation logic consuming
  `EvidenceCollection` yet.
- **Repository Transition Validator integration**: `Evidence`/
  `EvidenceCollection` are not passed to, read by, or referenced from
  `core/repository_transition_validator.py`.
- **Explanation citation**: `EvidenceReference` exists as a shape but is
  not yet attached to any `TransitionResult`-like explanation object.
- **Raw evidence persistence**: no artifact format, lifecycle,
  redaction, or retention rules exist for durably storing `Evidence`
  beyond one in-memory evaluation.
- **SLM/AI evidence**: no provider emits `ai_review`-category evidence;
  the `probabilistic`/advisory boundary from 115B remains a contract-only
  constraint pending an actual AI Review Provider.

## What Intentionally Remains Disconnected

Per the phase brief's non-goals, `src/pcae/core/evidence.py` is not
imported by, and does not import from:

- Repository Skills (not implemented)
- Decision Evaluation (not implemented)
- `core/repository_transition_validator.py`
- Any lifecycle command (`pcae task finish`, `pcae phase complete`, ...)
- Notification Policy / `core/notification_certification.py`
- `core/push_state_reconciliation.py`
- `core/post_push_canonicalization.py`
- `core/canonical_artifact_promotion.py`
- `pcae agent verify-handoff` / `core/handoff_verification.py`
- Permission Broker enforcement
- Plugins, Telegram inbound, REST, Web UI, Dashboard

`src/pcae/core/evidence.py` imports only from the Python standard library
(`dataclasses`, `enum`, `types`, `typing`) — zero internal PCAE imports,
zero I/O, zero side effects. This was verified directly by inspection of
the module's import block, not merely asserted.

## Validation

- Focused: `python -m pytest tests/test_evidence*.py -n auto -q -ra
  --durations=100` — see final report for counts.
- Regression: `python -m pytest tests/test_*runtime* tests/test_*contract*
  tests/test_*autonomy* tests/test_*plugin* -n auto -q -ra
  --durations=100` — see final report.
- Fast-green: `python -m pytest -m "fast_green" -n auto -ra
  --durations=100` — see final report. (`test_evidence*.py` is not itself
  in the fast-green allowlist, matching how other disconnected-prototype
  phases' test files are not added to that curated set.)
- `pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae push
  check` / `pcae agent verify-handoff` / `pcae session bootstrap
  --compact --profile implementation` / `pcae runtime inspect --json` /
  `pcae notify status` — see final report.
- `pcae skill invoke phase-finalization 115C` — see final report.

## Governance

No Repository Transition Validator, lifecycle, Notification Policy,
Canonical Artifact Promotion, Push-State Reconciliation, Post-Push
Canonicalization, Permission Broker, plugin, Telegram inbound, REST, Web
UI, or Dashboard code was changed. Execution capability remains
unavailable. Runtime state remains Observed. Maximum plugin capability
remains `observe`.

## Recommended Next Phase

115D — Repository Evidence Provider Prototype
