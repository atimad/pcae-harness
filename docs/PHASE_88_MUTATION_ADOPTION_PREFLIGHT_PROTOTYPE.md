# Phase 88H Mutation/Adoption Preflight Prototype

## 1. Purpose

Implement the mutation/adoption preflight prototype: an explicit command that
evaluates whether a proposed mutation or adoption-related action has sufficient
evidence. Returns structured JSON with a preflight decision, reason codes,
scope/backend relationship, captured-output/diff/adoption evidence status,
human review requirements, and safety notes.

## 2. Scope

88H implements `pcae preflight mutation` with `--json`, `--requested-action`,
`--requested-file`, `--captured-output-present`, `--captured-output-hash`,
`--diff-present`, `--diff-hash`, `--adoption-review-present`,
`--adoption-approval-present`, and `--source-backend` arguments. 34 tests.

## 3. Non-Goals

Performing mutation, adoption, commit, push, or backend invocation.

## 4. Relationship to 88G

88G designed the mutation/adoption preflight boundary. 88H implements it.

## 5. Command Behavior

Evaluates evidence for proposed mutation/adoption without performing it.

## 6. JSON Output Model

Envelope: schema_version, generated_at, source_command, repository_root,
preflight, warnings, errors, safety_notes. Preflight: 37 fields.

## 7. Mutation/Adoption Action Values

docs_mutation, source_mutation, test_mutation, generated_artifact_mutation,
captured_output_review, captured_output_adoption, adoption_review,
adoption_approval, adoption_execution, unknown_mutation_action, unknown.

## 8. Decision Values

14 values including allow_preflight through unknown.

## 9. Reason Codes

Comprehensive codes for scope, backend, capture, diff, review, approval.

## 10–15. Evidence/Relationship Handling

Captured output, diff, adoption review/approval/execution, scope, backend,
and human review all evaluated as evidence, not authorization.

## 16. Non-Authorizing Boundary

All authorization/execution/mutation/adoption flags always false.

## 17–19. Safety

No mutation, adoption, commit, push, backend, prompt, capture, or storage.
19 safety notes.

## 20. Test Coverage

34 tests covering command existence, fields, all decision paths, safety flags,
no artifacts, existing commands work.

## 21. Known Limitations

The mutation/adoption preflight prototype evaluates proposed mutation and
adoption-related actions only. It does not mutate files, apply captured output,
perform adoption review, grant adoption approval, execute adoption, invoke
backends, send prompts, capture output, perform intake, stage, commit, push,
write storage, implement the permission broker, or implement the shell gate.

## 22. Recommended Next Phase

**88I — Mutation/Adoption Preflight Tests and False-Positive Review.**

---

phase_88h_name=mutation_adoption_preflight_prototype
phase_88h_version=0.1
phase_88h_status=implemented
command_name=pcae preflight mutation
test_count=34
action_values=11
decision_values=14
flags_implemented=requested_file,captured_output_present,captured_output_hash,diff_present,diff_hash,adoption_review_present,adoption_approval_present,source_backend
authorization_granted=false
execution_authorized=false
mutation_performed=false
recommended_next=88I
