# Phase 87 Adoption and Mutation Gate Dry-Run

## 1. Purpose

Document the adoption and mutation gate dry-run added to `pcae gate-dry-run [--json]`.
Evaluates proposed adoption and mutation without performing intake, review, approval,
execution, file mutation, or storage writes.

## 2. Scope

Implementation summary. Extends the gate dry-run evaluator with concrete adoption and
mutation evaluation, optional CLI flags, and specific tests.

## 3. Non-Goals

- Performing intake, adoption review, approval, or execution.
- Mutating source, test, or docs files.
- Invoking backends, sending prompts, capturing output.
- Implementing permission broker, shell gate, or storage.

## 4. Command Behavior

```
pcae gate-dry-run --json --requested-action adoption --requested-file src/example.py
pcae gate-dry-run --json --requested-action adoption --adoption-artifact-present --human-approved
pcae gate-dry-run --json --requested-action source_mutation --requested-file src/example.py
pcae gate-dry-run --json --requested-action test_mutation --requested-file tests/example.py
pcae gate-dry-run --json --requested-action source_mutation --requested-file src/example.py --human-approved
```

## 5. Adoption Gate Model

adoption_approval_gate includes `adoption_evaluation` with: adoption_status,
requested_action, requested_files, adoption_artifact_present, adoption_review_detected,
adoption_approval_detected, human_approval_detected, task_contract_detected,
task_contract_path, scope_status, evidence_sources, adoption_notes.

## 6. Mutation Gate Model

source_mutation_gate and test_mutation_gate include `mutation_evaluation` with:
mutation_status, requested_action, requested_files, mutation_type, scope_status,
matched_allowed_files, matched_forbidden_files, unknown_files, human_approval_detected,
task_contract_detected, task_contract_path, evidence_sources, mutation_notes.

## 7. Adoption Evaluation Fields

adoption_status, requested_action, requested_files, adoption_artifact_present,
adoption_review_detected, adoption_approval_detected, human_approval_detected,
task_contract_detected, task_contract_path, scope_status, evidence_sources,
adoption_notes.

## 8. Mutation Evaluation Fields

mutation_status, requested_action, requested_files, mutation_type, scope_status,
matched_allowed_files, matched_forbidden_files, unknown_files, human_approval_detected,
task_contract_detected, task_contract_path, evidence_sources, mutation_notes.

## 9. Requested Action Handling

| Action | Gate | Behavior |
|--------|------|----------|
| adoption | adoption_approval_gate | Evaluates, never approves |
| source_mutation | source_mutation_gate | Evaluates scope, never authorizes |
| test_mutation | test_mutation_gate | Evaluates scope, never authorizes |
| docs_mutation | scope_check_gate | Evaluates scope only |

## 10. Human Approval Handling

`--human-approved` indicates human approval is present. This does not execute
mutation or approve adoption — it shifts the evaluation status but
authorization_granted remains false.

## 11. Adoption Artifact Handling

`--adoption-artifact-present` indicates an adoption artifact exists. This does
not approve adoption — adoption_approval_detected remains false.

## 12. Decision Mapping

No adoption or mutation gate produces `allow`. Decisions: requires_human_review,
requires_more_evidence, blocked_by_scope, deny.

## 13. Safety Guarantees

| Safety Note | Value |
|-------------|-------|
| `adoption_gate_dry_run_only` | `true` |
| `adoption_gate_does_not_review_output` | `true` |
| `adoption_gate_does_not_approve_output` | `true` |
| `adoption_gate_does_not_apply_output` | `true` |
| `adoption_gate_does_not_authorize_adoption` | `true` |
| `mutation_gate_dry_run_only` | `true` |
| `mutation_gate_does_not_mutate_source` | `true` |
| `mutation_gate_does_not_mutate_tests` | `true` |
| `mutation_gate_does_not_mutate_docs` | `true` |
| `mutation_gate_does_not_authorize_mutation` | `true` |
| `scope_match_is_not_mutation_approval` | `true` |
| `human_approval_flag_is_not_execution` | `true` |
| `adoption_artifact_presence_is_not_approval` | `true` |

## 14. No-Intake/No-Adoption/No-Mutation Behavior

- No intake performed
- No adoption review performed
- No adoption approval performed
- No adoption execution performed
- No source files mutated
- No test files mutated
- No docs files mutated

## 15. No-Write/No-Storage Behavior

- No files written
- No cache created
- No .pcae storage created

## 16. Test Coverage

27 tests in `tests/test_adoption_mutation_gate.py`.

## 17. Known Limitations

- Dry-run only; no actual adoption or mutation
- No gate produces `allow`
- Does not consume adoption candidate schemas
- Human-approved flag does not execute anything
- Mutation type detection is based on requested_action string

## 18. Recommended Next Phase

**87G — Commit and Push Gate Dry-Run.**

---

adoption_mutation_gate_name=phase_87_adoption_mutation_gate_dry_run
adoption_mutation_gate_version=0.1
adoption_mutation_gate_status=implemented
tests_added=27
total_test_count=7223
read_only=true
enforcement_performed=false
authorization_granted=false
adoption_performed=false
mutation_performed=false
storage_created=false
recommended_next=87G
