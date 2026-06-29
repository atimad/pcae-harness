# Phase 94O — Backend Manual Apply Package

## Overview

Phase 94O introduces the **Backend Manual Apply Package**: a model that bundles evidence
from an `ApplyPlan` (94K) and a `BackendApplyReadinessAssessment` (94L) into a single
human-readable artifact for manual operator review. No apply execution is performed.

## Boundary Guarantee

The package layer carries a hard `no_execution_performed = True` default. Creating or
persisting a package:

- does **not** execute any apply operation
- does **not** modify source files outside `.pcae/backend-manual-apply-packages/`
- does **not** parse patches for mutation
- does **not** invoke any backend (Claude, OpenAI, mock, or otherwise)
- does **not** run subprocess, network, or shell commands
- does **not** run `pcae check` or any test suite automatically
- does **not** authorize a commit or push

## Model: `BackendManualApplyPackage`

Defined in `src/pcae/core/backend_invocations.py`.

Key fields:

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `package_id` | str | `pkg-<uuid8>` | Unique package identifier |
| `apply_plan_id` | str | `""` | Bound to apply plan |
| `output_hash` | str | `""` | Hash of output being reviewed |
| `request_id` | str | `""` | Original backend request ID |
| `phase_id` | str | `""` | Phase ID, multi-part preserved |
| `readiness_assessment_id` | str | `""` | Bound assessment ID |
| `readiness_status` | str | `"unknown"` | Status from assessment |
| `apply_ready` | bool | `False` | Must be True for apply to proceed |
| `rollback_required` | bool | `True` | Fail-closed: rollback always required |
| `hard_blocks` | list | `[]` | Hard blocks from plan + assessment |
| `missing_evidence` | list | `[]` | Evidence gaps |
| `warnings` | list | `[]` | Non-blocking warnings |
| `operations` | list | `[]` | Operation summaries (strings) |
| `tests_to_run` | list | `[]` | Advisory tests before apply |
| `checks_to_run` | list | `[]` | Advisory pcae checks |
| `operator_notes` | str | `""` | Free-form operator notes |
| `rollback_instructions` | str | `""` | Advisory rollback steps |
| `manual_apply_instructions` | str | `""` | Advisory apply steps (ADVISORY ONLY) |
| `no_execution_performed` | bool | `True` | Always True — package never executes |
| `schema_version` | str | `"1.0"` | Schema version |
| `created_at` | str | ISO-8601 UTC | Creation timestamp |

### Serialization

```python
pkg = BackendManualApplyPackage(package_id="pkg-abc", output_hash="h-001")
d = pkg.to_dict()
pkg2 = BackendManualApplyPackage.from_dict(d)
```

### Markdown rendering

```python
md = pkg.render_markdown()
```

The Markdown output always includes:
- No-execution confirmation header
- Hard blocks section (if any)
- Missing evidence section (if any)
- Advisory rollback/apply/test instructions
- `no_execution_performed: True` in the YAML-like summary

## Factory: `create_backend_manual_apply_package`

```python
from pcae.core.backend_invocations import (
    create_backend_manual_apply_package,
    persist_manual_apply_package,
)

pkg = create_backend_manual_apply_package(
    plan=apply_plan,
    assessment=readiness_assessment,  # optional
    operator_notes="Reviewed at 2026-06-29. Context checked.",
    rollback_instructions="git revert HEAD~1 && pcae check",
    manual_apply_instructions="Apply src/pcae/foo.py manually via editor.",
)
```

Evidence is merged from `plan` and `assessment`:
- `hard_blocks` = union of plan.hard_blocks + assessment.hard_blocks
- `missing_evidence` = from plan
- `operations` = formatted strings from plan.operations
- `readiness_status` = from assessment (if provided), else `"unknown"`
- `apply_ready` = from assessment (if provided), else `False`
- `tests_to_run`, `checks_to_run` = from plan

## Persistence

```python
result = persist_manual_apply_package(pkg)
# result: {"status": "written", "json_path": ..., "md_path": ...,
#           "latest_json": ..., "latest_md": ...}
```

Artifacts are written to `.pcae/backend-manual-apply-packages/`:

```
.pcae/backend-manual-apply-packages/
  20260629-155754-pkg-faeba753.json    ← timestamped JSON
  20260629-155754-pkg-faeba753.md      ← timestamped Markdown
  latest.json                          ← atomic pointer (latest package)
  latest.md                            ← atomic pointer (latest Markdown)
```

This directory is listed in `.pcae/.gitignore` and is never tracked by git.

## Reading the latest package

```python
from pcae.core.backend_invocations import read_latest_manual_apply_package

pkg = read_latest_manual_apply_package()  # returns None if no packages exist
```

## CLI Commands

### Show

```bash
pcae backend manual-apply-package show --latest
pcae backend manual-apply-package show --latest --json
```

Returns non-zero exit if no package exists. JSON mode prints `{"error": "..."}` on failure.
No raw prompt/output content is displayed — metadata only.

### Create

```bash
pcae backend manual-apply-package create [--apply-plan PATH] [--readiness PATH] \
  [--review PATH] [--approval PATH] \
  [--operator-notes "..."] [--rollback-instructions "..."] [--json]
```

With `--json`, output includes:

```json
{
  "package": { ... },
  "persistence": { "status": "written", "json_path": "...", "md_path": "...", ... },
  "no_execution": true,
  "no_apply": true,
  "no_patch_parsing": true,
  "no_source_files_modified": true,
  "no_automatic_tests": true,
  "no_automatic_pcae_check": true
}
```

All flags are always `true` — they are informational guarantees, not conditional outputs.

## Test Coverage

**Model tests** (`tests/test_backend_invocations.py`, ~49 new tests, classes `Test94O*`):
- `BackendManualApplyPackage` safe defaults
- `to_dict`/`from_dict` round-trip
- No commit/push authorization implied
- No secrets in serialized output
- Multi-part phase IDs preserved
- `create_backend_manual_apply_package` from plan: binds IDs, operations, hard blocks,
  missing evidence, rollback, tests, checks
- `create_backend_manual_apply_package` from assessment: readiness status, apply_ready,
  merges hard blocks from both plan and assessment
- `render_markdown`: no-execution confirmation, advisory labels, hard blocks, rollback,
  tests, checks; no secrets
- `persist_manual_apply_package`: writes JSON + Markdown, updates `latest.json` + `latest.md`,
  no secrets in either file
- `read_latest_manual_apply_package`: returns None when missing, round-trips after persist,
  preserves phase ID
- Module-level: no subprocess, no network, gitignore, no Telegram inbound

**CLI tests** (`tests/test_backend_cli.py`, ~25 new tests, classes `TestManualApplyPackage*`):
- show: missing clean error (text + JSON), no raw content
- create: no_execution/no_apply/no_patch_parsing/no_source_files_modified flags all True
- create: persists JSON + Markdown, updates latest
- create: Markdown includes no-execution confirmation and advisory label
- create: JSON and Markdown no secrets
- create: with `--operator-notes`, `--rollback-instructions`
- create: with `--apply-plan FILE` and `--readiness FILE` for file-based loading
- create: multi-part phase ID from plan file preserved
- Module-level: no subprocess, no shell, no network, gitignore, no Telegram inbound

## Relationship to Adjacent Phases

| Phase | Component | Role |
|-------|-----------|------|
| 94K | `ApplyPlan` | Input to package |
| 94L | `BackendApplyReadinessAssessment` | Input to package (optional) |
| 94M | `ReviewArtifact`, `ApprovalArtifact` | Context IDs bound to package |
| 94N | CLI `be_apply_plan show/create/validate` | Source of latest plan + assessment |
| **94O** | **`BackendManualApplyPackage`** | **This phase** |
| 94P | Backend Apply Governance Hardening | Recommended next: enforcement boundary |

## Security Notes

- All serialized outputs are audited for secrets (`sk-ant`, `api_key`) in tests
- No raw AI output is stored in the package — only structured metadata
- The `manual_apply_instructions` field is advisory only: labeled as such in Markdown
- Atomic file replacement (via temp file + `os.replace`) prevents torn writes to `latest.*`
