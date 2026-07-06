# Phase 115D — Repository Evidence Provider Prototype

## Status

Completed. Read-only evidence provider prototype only: no decision
evaluation, no Repository Transition Validator integration, no lifecycle
command changes, no notification changes, no execution capability, no
SLM/LLM/AI evidence providers.

## Purpose

Implement the first deterministic Repository Evidence Providers on top
of 115C's runtime `Evidence`/`EvidenceCollection` objects: a common
provider contract plus four concrete providers producing real evidence
from git, runtime, phase report, and phase metadata state.

Implementation: `src/pcae/core/evidence_providers.py`.

## Provider Framework

### EvidenceProviderContext

A frozen dataclass carrying `root: HarnessPath` (read-only repository
handle) and `strict: bool = False`. `strict=True` tells a provider to
re-raise an unexpected collection failure instead of degrading to
unknown/unavailable evidence (Objective 5) — the default preserves the
fail-closed-to-evidence behavior every provider uses.

### EvidenceProviderResult

A frozen dataclass mirroring 115B's Evidence Provider Contract table:
`provider_id`, `producer`, `determinism`, `categories`,
`required_inputs`, `scope`, `limitations`, and the produced `evidence:
EvidenceCollection`.

### EvidenceProvider

An abstract base class (`abc.ABC`) declaring the contract every provider
implements: class-level `provider_id`/`producer`/`determinism`/
`categories`/`required_inputs`/`scope`/`limitations`, plus one abstract
method, `collect(context) -> EvidenceProviderResult`. Providers:

- collect evidence
- never decide, vote, or evaluate a transition
- never mutate `context.root` or any repository state
- never promote artifacts
- never send notifications
- never invoke execution
- carry no field identifying the calling agent/model anywhere in their
  declaration or output

## Implemented Providers

### GitEvidenceProvider

Categories: `git`, `push_state`. Produces:

- `E-git-001` — current branch (`git branch --show-current`)
- `E-git-002` — working tree clean/dirty (`git status --porcelain`)
- `E-git-003` — commits ahead of `origin/main` (`git rev-list --count
  origin/main..HEAD`)
- `E-git-004` — commits behind `origin/main` (`git rev-list --count
  HEAD..origin/main`)
- `E-git-005` — derived pushed status (`pushed`/`not_pushed`/
  `behind_only`), computed from the ahead/behind evidence above, not a
  separate git invocation

### RuntimeEvidenceProvider

Category: `runtime`. Reuses 111B/112E's own read-only introspection
(`build_runtime_snapshot`) unmodified — no new runtime computation.
Produces:

- `E-runtime-001` — current runtime state (`health.current_runtime_state`)
- `E-runtime-002` — execution availability
  (`health.execution_availability`)
- `E-runtime-003` — maximum plugin capability
  (`health.current_maximum_plugin_capability`)

### ReportEvidenceProvider

Category: `report`. Reads `.pcae/phase-reports/latest.json` only (never
quarantined or historical reports). Produces:

- `E-report-001` — whether a canonical latest report exists
- `E-report-002` — `phase_id`
- `E-report-003` — `report_completeness`
- `E-report-004` — `recommended_next_phase`
- `E-report-005` — report consistency, derived from
  `canonical_report_used` and the absence/presence of `trust_warnings`
  (not itself a 115B-frozen field; a convenience derivation, documented
  as such via the evidence item's own `limitations`)

### MetadataEvidenceProvider

Category: `metadata`. Reads `.pcae/phase-completion-metadata.json` only.
Produces:

- `E-metadata-001` — whether declared metadata exists
- `E-metadata-002` — `phase_id`
- `E-metadata-003` — `pushed_status` (declared, not reconciled against
  live git state — that reconciliation is Push-State Reconciliation's
  job, not this provider's; the evidence item's `limitations` field says
  so explicitly)
- `E-metadata-004` — `origin_main_head_count` (declared, same caveat)
- `E-metadata-005` — `recommended_next_phase`

## Determinism

All four providers declare `EvidenceDeterminism.DETERMINISTIC` at the
class level, and every `Evidence` item they produce carries the same
`determinism` value — verified directly in
`TestDeterministicClassification` (`tests/test_evidence_providers.py`).
Determinism describes the *observed value* (same repository state -> same
observed value), not the wall-clock `timestamp_utc` each item also
carries, which necessarily varies by collection time — consistent with
115B's own semantics ("same repository state and same inputs produce the
same observed value").

## Failure Behavior

Per Objective 5, a provider failure never crashes the caller unless
`context.strict=True`:

- Each provider wraps its per-datum collection in `try`/`except`.
- On failure (or when the input is simply absent — no git remote, no
  `.pcae/phase-reports/latest.json`, no
  `.pcae/phase-completion-metadata.json`), the provider emits an
  `Evidence` item with `observed_value="unavailable"`,
  `freshness=EvidenceFreshness.UNKNOWN`,
  `confidence=EvidenceConfidence.UNKNOWN` — an honestly unknown
  observation, never a fabricated value.
- When `context.strict=True`, the same failure is re-raised instead,
  for callers that want fail-loud behavior.

Verified in `TestGracefulUnknownEvidence`: a git repo with no
`origin/main` remote degrades ahead/behind/pushed evidence to unknown
without crashing; a missing/corrupt `latest.json` or
`phase-completion-metadata.json` degrades gracefully in non-strict mode
and raises in strict mode; a monkeypatched `build_runtime_snapshot`
failure degrades gracefully in non-strict mode and raises in strict
mode.

## No Integration (Confirmed)

`src/pcae/core/evidence_providers.py` is not imported by, and does not
import from:

- The Repository Transition Validator (`core/repository_transition_validator.py`)
- Any Decision Framework (none implemented yet)
- Any lifecycle command (`pcae phase complete`, `pcae task finish`,
  `pcae push`)
- Notification Policy / `core/notification_certification.py`
- `pcae agent verify-handoff` / `core/handoff_verification.py`
- `pcae runtime inspect` (`commands/runtime_inspect.py`) — the Runtime
  provider calls the same underlying `build_runtime_snapshot()` helper
  `pcae runtime inspect` calls, but neither module imports the other

Its only internal imports are `pcae.core.evidence` (115C's runtime
objects), `pcae.core.paths.HarnessPath`, and, lazily inside
`RuntimeEvidenceProvider.collect()`, `pcae.core.runtime_registry` /
`pcae.core.runtime_snapshot` (both pre-existing, unmodified, read-only
introspection). No SLM/LLM/AI evidence provider is implemented.

## Validation

- Focused: `python -m pytest tests/test_evidence*.py -n auto -q -ra
  --durations=100` — see final report for counts (115C + 115D
  combined).
- Regression: `python -m pytest tests/test_*runtime* tests/test_*contract*
  tests/test_*autonomy* tests/test_*plugin* -n auto -q -ra
  --durations=100` — see final report.
- Fast-green: `python -m pytest -m "fast_green" -n auto -ra
  --durations=100` — see final report.
- `pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae push
  check` / `pcae agent verify-handoff` / `pcae session bootstrap
  --compact --profile implementation` / `pcae runtime inspect --json` /
  `pcae notify status` — see final report.
- `pcae skill invoke phase-finalization 115D` — see final report.

## Governance

No Repository Transition Validator, lifecycle, Notification Policy,
Permission Broker, plugin, Telegram inbound, REST, Web UI, or Dashboard
code was changed. Execution capability remains unavailable. Runtime
state remains Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115E — Repository Decision Evaluation Prototype
