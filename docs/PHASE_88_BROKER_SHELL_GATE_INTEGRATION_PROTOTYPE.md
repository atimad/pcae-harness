# Phase 88T — Broker + Shell Gate Integration Prototype

```
broker_shell_gate_integration_prototype_name    = phase_88_broker_shell_gate_integration_prototype
broker_shell_gate_integration_prototype_version = 0.1
broker_shell_gate_integration_prototype_status  = implemented_prototype
implementation_status                           = prototype_complete
recommended_next_phase                          = 88U_broker_shell_gate_integration_test_expansion
```

## 1. Purpose

Implement the first prototype integration between the permission broker
(`src/pcae/core/permission_broker.py`) and the shell gate classifier
(`src/pcae/core/shell_gate.py`). The broker now fully consumes shell gate
classification evidence, applies the decision mapping and priority rules from the
88S design, propagates hard blocks, preserves non-hard-block review states, detects
contradictions, redacts secret-access command evidence, and returns an integrated
broker decision envelope with 13 new audit fields.

## 2. Scope

Changed in 88T:
- `src/pcae/core/permission_broker.py` — integration logic, contradiction detection, audit fields
- `tests/test_broker_shell_gate_integration.py` — 162 new fast-green integration tests
- `docs/PHASE_88_BROKER_SHELL_GATE_INTEGRATION_PROTOTYPE.md` — this document
- `PROJECT_STATUS.md`, `CHANGELOG.md`

No changes to:
- `src/pcae/core/shell_gate.py` — no integration changes needed in classifier
- `src/pcae/commands/permission_broker.py` — CLI unchanged
- `tests/test_permission_broker.py` — all 150 existing tests pass unchanged
- Any shell wrapper, shell config, backend invocation, or persistent state

## 3. Non-Goals

88T must not and did not:
- Execute shell commands
- Intercept shell commands at OS/shell level
- Install shell wrappers or modify shell configuration
- Invoke backends, send prompts, capture outputs, perform intake/adoption
- Grant real execution authorization
- Override hard blocks with human approval or accepted risk
- Write persistent broker/shell-gate state or cache
- Raw git commit, raw git push, or force push

## 4. Relationship to 88S

This phase implements the design specified in
`docs/PHASE_88_BROKER_SHELL_GATE_INTEGRATION_DESIGN.md` (Phase 88S). Key design
decisions followed:
- Decision mapping from 88S §6 (26→24 with two mapping changes from 88R)
- Priority chain from 88S §8 (expanded to 9 levels)
- Contradiction conditions from 88S §15 (13 conditions implemented)
- Audit fields from 88S §17 (13 new fields)
- Performed-flag invariant from 88S §16 (14 flags unconditionally False)
- Secret redaction from 88S command text redaction policy

## 5. Implementation Summary

### 5.1 New Constants

```python
_SG_ALLOW_DECISIONS          # frozenset: allow_read_only, allow_governed, allow_test_execution
_SG_HARD_BLOCK_DECISIONS_SET # frozenset: all SG decisions implying hard block
_SG_PERFORMED_FORBIDDEN_KEYS # frozenset: 14 performed/auth keys that must never be True
_SG_SCHEMA_VERSION           # str: "0.1"
```

### 5.2 Updated Hard Block Map

Two mapping changes from 88R (per 88S §6):

| Shell Gate Decision           | 88R Mapping            | 88T Mapping            | Rationale |
|-------------------------------|------------------------|------------------------|-----------|
| `blocked_by_policy_forbidden_file` | `blocked_by_shell_gate` | `blocked_by_scope` | Consistent with scope preflight audit trail |
| `blocked_by_missing_task`     | *(not mapped — fell through)* | `blocked_by_task_contract` | Promoted to hard block |

### 5.3 New Function: `_check_sg_contradiction`

Accepts `(sg_evidence, requested_action, human_approval_present, accepted_risk_present)`,
returns `list[str]` of contradiction descriptions. Empty list = no contradiction.

13 contradiction conditions checked:
1. Schema version missing or not "0.1"
2. Any of 14 performed/authorization keys set to True in sg_evidence or detected_flags
3. `hard_block_present=True` + allow decision
4. `force_push_detected=True` + decision ≠ `blocked_by_force_push`
5. `raw_git_push_detected=True` + allow decision
6. `command_category == "unknown"` + allow decision
7. Mutating broker action + `allow_read_only` decision from shell gate
8. Secret-access command text not redacted when `secret_access_detected=True`
9. Human approval presented alongside SG hard block
10. Accepted risk presented alongside SG hard block
(Conditions 2 covers 14 specific flag keys, making 22 distinct checks total.)

### 5.4 Updated `_broker_decide` Priority Chain

```
Priority 1  — SG hard blocks (checked before all evidence)
  1a. SG decision in _SG_HARD_BLOCK_TO_BROKER → mapped hard block decision
  1b. [special] requires_active_task + no task → blocked_by_task_contract (hard)
Priority 2  — Contradiction detection
  If _check_sg_contradiction returned non-empty → blocked_by_conflicting_evidence
Priority 3  — Explicit evidence failures (health, check, doctor, tests, push_check)
Priority 4  — Test run lock (expensive test + not clear)
Priority 5  — No active task for mutating actions
Priority 6  — Scope preflight denial
Priority 7  — Missing evidence collection → requires_more_evidence
Priority 8  — Human review gate (SG requires_human_review + action-level gate)
Priority 9  — All checks pass → allow_preflight_only
```

Priority 2 (contradiction) only fires when priority 1 does not. If there's a real SG
hard block at priority 1, the hard block decision is returned; the contradiction is
still recorded in audit fields (`conflicting_evidence_detected`, `conflicting_evidence_details`).

### 5.5 Updated `build_permission_broker`: Shell Gate Evidence Fields

New fields added to the internal `sg_evidence` dict:

```python
{
    "schema_version": "0.1",           # NEW: validates internal evidence integrity
    "command_text": ...,               # REDACTED if secret_access_detected
    "command_text_redacted": bool,     # NEW: True when command text was redacted
    "command_category": ...,
    "decision": ...,
    "reason_codes": [...],
    "detected_flags": {...},
    "hard_block_present": bool,        # NEW: computed from SG decision vs hard block set
    "secret_access_detected": bool,    # NEW: mirrored from detected_flags
}
```

## 6. Shell Gate Evidence Consumed

The broker now explicitly validates and consumes the following shell gate fields
(as implemented in `build_permission_broker`):

| Field | How Used |
|---|---|
| `command_category` | Decision mapping, audit label, evidence source |
| `decision` | Priority 1 hard block check, priority 1b active task check, steps 2/8 |
| `reason_codes` | Passed to broker reason_codes and `shell_gate_reason_codes` audit field |
| `detected_flags["force_push_detected"]` | Contradiction check condition 4 |
| `detected_flags["raw_git_push_detected"]` | Contradiction check condition 5 |
| `detected_flags["secret_access_detected"]` | Command text redaction |
| `detected_flags["expensive_test_execution_detected"]` | Test run preflight decision |
| `detected_flags` (all) | Contradiction check for performed flags |
| `hard_block_present` | Computed; used in contradiction checks 3, 9, 10 |

## 7. Decision Mapping Implemented

Full 26→24 mapping as defined in 88S §6. Changes from 88R:
- `blocked_by_policy_forbidden_file` → `blocked_by_scope` (was `blocked_by_shell_gate`)
- `blocked_by_missing_task` → `blocked_by_task_contract` (was not mapped, now hard block)
- `requires_active_task` with no task → `blocked_by_task_contract` at priority 1b

All allow decisions (`allow_read_only`, `allow_governed`, `allow_test_execution`) remain
mapped to `allow_preflight_only` at the broker level. None grant execution authorization.

## 8. Hard-Block Propagation

Hard blocks from shell gate propagate unconditionally. The following commands produce
the listed broker decisions regardless of human approval, accepted risk, health status,
or any other evidence:

| Command Pattern | SG Decision | Broker Decision |
|---|---|---|
| `git push --force` | `blocked_by_force_push` | `blocked_by_force_push` |
| `git push origin main` | `blocked_by_raw_git_push` | `blocked_by_raw_git_push` |
| `git commit -m "msg"` | `blocked_by_raw_git_commit` | `blocked_by_shell_gate` |
| `git rebase -i` | `blocked_by_history_rewrite` | `blocked_by_shell_gate` |
| `rm -rf .` | `blocked_by_destructive_filesystem` | `blocked_by_shell_gate` |
| `cat file > README.md` | `blocked_by_policy_forbidden_file` | `blocked_by_scope` |
| `somecustomtool --arg` | `blocked_by_unknown_command` | `blocked_by_shell_gate` |
| `cp src/a src/b` (no task) | `blocked_by_missing_task` | `blocked_by_task_contract` |
| `pytest -n auto` (no task) | `requires_active_task` | `blocked_by_task_contract` |

## 9. Non-Hard-Block Handling

| SG Decision | With Evidence | Broker Decision |
|---|---|---|
| `requires_human_review` | `human_review_present=False` | `requires_human_review` |
| `requires_human_review` | `human_review_present=True` | `allow_preflight_only` |
| `requires_preflight` | no scope evidence | `requires_more_evidence` |
| `requires_preflight` | scope evidence present | scope result takes effect |
| `requires_active_task` | task present | constraint satisfied; continues |
| `requires_more_evidence` | — | `requires_more_evidence` |
| `allow_read_only` | — | `allow_preflight_only` (never stronger) |
| `allow_governed` | — | `allow_preflight_only` |
| `allow_test_execution` | all evidence | `allow_preflight_only` |

## 10. Contradiction Detection

`_check_sg_contradiction` is called in `build_permission_broker` before `_broker_decide`.
When contradictions are detected:
- `contradiction_details` (list of descriptions) is passed to `_broker_decide`
- At priority 2, if `contradiction_details` is non-empty, decision becomes
  `blocked_by_conflicting_evidence`
- If a priority 1 hard block fires first, `blocked_by_conflicting_evidence` is NOT the
  decision — the hard block wins — but `conflicting_evidence_detected=True` and
  `conflicting_evidence_details` are still populated in audit fields
- All performed flags remain False regardless

Contradiction conditions tested:
1. Schema version missing/wrong → `blocked_by_conflicting_evidence` (via priority 2)
2. Performed flag True in sg_evidence → `blocked_by_conflicting_evidence`
3. SG hard block + allow decision → `blocked_by_conflicting_evidence`
4. `force_push_detected=True` + non-force-push decision → `blocked_by_conflicting_evidence`
5. `raw_git_push_detected=True` + allow decision → `blocked_by_conflicting_evidence`
6. `unknown` category + allow decision → `blocked_by_conflicting_evidence`
7. Mutating action + `allow_read_only` → `blocked_by_conflicting_evidence`
8. Secret not redacted when `secret_access_detected=True` → `blocked_by_conflicting_evidence`
9. Human approval + SG hard block → contradiction noted in audit; hard block wins at priority 1
10. Accepted risk + SG hard block → contradiction noted in audit; hard block wins at priority 1

## 11. Secret-Access Redaction

When `detected_flags["secret_access_detected"]=True`, the broker:
1. Stores `"<redacted_secret_access_command>"` in `sg_evidence["command_text"]`
2. Sets `sg_evidence["command_text_redacted"]=True`
3. Sets `sg_evidence["secret_access_detected"]=True`
4. Sets `broker["shell_gate_command_text_redacted"]=True`
5. Sets `broker["shell_gate_command_text_hash"]=None` (no hash for redacted commands)

For non-secret commands: `broker["shell_gate_command_text_hash"]` = SHA-256 of command text.

Programs triggering redaction: `security`, `keychain`, `pass`, `op`, `gpg`, `gopass`,
`bitwarden`, `bw`, `vault` (from `_SECRET_ACCESS_PROGRAMS` in shell_gate.py).

File paths triggering redaction: `~/.ssh/`, `~/.gnupg/`, `~/.netrc`, `~/.aws/credentials`,
`~/.kube/config`, and others in `_SECRET_FILE_PREFIXES`.

## 12. Audit Fields

13 new fields added to the `broker` dict:

| Field | Type | Description |
|---|---|---|
| `shell_gate_schema_version` | str \| null | "0.1" when sg evidence present |
| `shell_gate_command_category` | str \| null | Classified category from shell gate |
| `shell_gate_command_text_hash` | str \| null | SHA-256 of command; null if redacted or no command |
| `shell_gate_command_text_redacted` | bool | True when secret access detected |
| `shell_gate_decision` | str \| null | Shell gate decision, for audit traceability |
| `shell_gate_reason_codes` | list[str] | Shell gate reason codes |
| `shell_gate_hard_block_present` | bool \| null | True if SG decision in hard block set |
| `conflicting_evidence_detected` | bool | True if any contradiction detected |
| `conflicting_evidence_details` | list[str] | Contradiction description strings |
| `hard_block_sources` | list[str] | "shell_gate" and/or "broker" |
| `human_review_sources` | list[str] | Reason codes that triggered human review gate |
| `accepted_risk_noted` | bool | Mirrors `accepted_risk_present` input |
| `broker_mapping_reason` | str | "sg:{sg_decision}->broker:{broker_decision}" |

All fields are null/empty/False when `requested_command` is not provided.

## 13. Performed-Flag Invariants

All 14 performed/authorization flags remain unconditionally `False`:

```
authorization_granted=False     execution_authorized=False
command_executed=False          repo_mutation_performed=False
backend_invocation_performed=False  prompt_sent=False
capture_performed=False         intake_performed=False
adoption_performed=False        commit_performed=False
push_performed=False            raw_git_push_performed=False
force_push_performed=False      storage_written=False
```

These are invariant across all decisions (allow, block, contradiction, human review).
Verified by 56 parametrized tests (14 flags × 4 decision paths).

## 14. CLI Behavior

`pcae permission-broker evaluate` CLI is unchanged. The broker output JSON now includes the
13 new audit fields automatically when `--requested-command` is provided.

```bash
pcae permission-broker evaluate \
  --requested-action read \
  --requested-command "git push --force" \
  --json
```

Output includes:
- `broker.decision`: `"blocked_by_force_push"`
- `broker.hard_block_present`: `true`
- `broker.shell_gate_evidence`: non-null with schema_version, hard_block_present, etc.
- `broker.shell_gate_decision`: `"blocked_by_force_push"`
- `broker.shell_gate_command_text_hash`: SHA-256 of command text
- `broker.conflicting_evidence_detected`: `false` (no contradiction for clean hard block)
- `broker.command_executed`: `false`
- `broker.execution_authorized`: `false`

## 15. Tests Added

**New test file**: `tests/test_broker_shell_gate_integration.py`

| Test Class | Tests | Coverage |
|---|---|---|
| `TestShellGateHardBlockPropagation` | 14 | Force push, raw push, commit, rebase, rm -rf, policy file, missing task, human approval, accepted risk, no health, scope interaction |
| `TestShellGateNonHardBlock` | 8 | Package install, network, backend, environment, preflight, human review gate |
| `TestShellGateReadOnly` | 7 | cat, git log, ls, git status, grep, pcae lifecycle, no-task read |
| `TestShellGateContradictionDetection` | 18 | Schema version, performed flags, hard block + allow, force push flag, raw push flag, unknown + allow, mutating + allow_read_only, secret not redacted, human approval alongside hard block, accepted risk alongside hard block, clean evidence, priority 2 fire, contradiction notes in audit |
| `TestShellGatePerformedFlagInvariant` | 56 | 14 flags × 4 decision paths (allow, hard block, human review, contradiction) |
| `TestSecretAccessRedaction` | 7 | SSH key, keychain, GPG, non-secret, no hash for redacted, SHA-256 for non-secret, not-redacted contradiction |
| `TestActiveTaskBoundary` | 7 | Read no task, mutating no task, mutating with task, requires_active_task with/without task, read-only SG decision no task |
| `TestAuditFields` | 15 | All 13 audit fields, evidence source label, warnings |
| `TestDecisionMapping` | 9 | Key 88T mapping changes, allow decisions, hard block map contents |
| `TestShellGateEvidenceFields` | 10 | All new sg_evidence fields |
| `TestEnvelopeInvariants` | 8 | Schema, decision in BPE_DECISIONS, hard_block consistent, sources, warnings |
| `TestCLISmoke` | 3 | Read, force push, secret access (slow/integration tier) |
| **Total** | **162** | Exceeds 88S minimum of 102 |

## 16. Validation Results

| Check | Result |
|---|---|
| `tests/test_permission_broker.py` | 150 passed / 1.27s |
| `tests -k shell_gate` | 611 passed / 20.76s |
| `tests -k "broker and shell"` | 174 passed / 0.98s |
| Fast-green (`-m fast_green -n auto`) | 2,546 passed / 23.39s |
| Quick tier (`-m "not slow and not phase_closure" -n auto`) | 7,807 passed / 2:36 |
| Full suite (`-n auto`) | See full suite result |

## 17. Remaining Limitations

1. **Contradiction detection has coverage gaps**: Conditions 9 and 10 (human approval /
   accepted risk alongside SG hard block) are always pre-empted by priority 1 (the SG
   hard block fires first). The contradiction is noted in audit fields but the decision
   remains the hard block, not `blocked_by_conflicting_evidence`. This is correct per
   the 88S priority order.

2. **Schema version is broker-generated**: Because the broker generates `sg_evidence`
   internally by calling shell gate functions, the schema version is always "0.1".
   Schema version mismatch can only be triggered via direct `_broker_decide` calls with
   crafted evidence, or if the shell gate module is swapped at runtime. External sg_evidence
   ingestion (future) would require stronger schema version enforcement.

3. **`blocked_by_scope` vs `blocked_by_shell_gate` for policy_forbidden_file**: The 88T
   change from `blocked_by_shell_gate` to `blocked_by_scope` for `blocked_by_policy_forbidden_file`
   makes the mapping semantically consistent with scope preflight, but changes the observable
   broker decision for this path. Callers relying on the 88R behavior need to handle both.

4. **Redaction applied to command text only**: The sg_evidence `detected_flags` still contain
   `secret_access_detected=True` which confirms the access type even though the command text
   is redacted. This is intentional: the flag is needed for audit and contradiction detection.

5. **No external sg_evidence ingestion**: The broker always generates sg_evidence internally.
   External evidence formats (e.g., from a shell wrapper that pre-classified the command)
   are not yet consumed.

6. **Category-level human review not automatically gated at broker action level**: Shell gate
   categories like `backend_invocation`, `output_capture`, `intake_adoption`, `secret_access`,
   `environment_mutation` route to `requires_human_review` via the SG decision, but the broker
   human review gate (step 8) only checks for `sg_evidence["decision"] == "requires_human_review"`
   plus specific actions. 88U should review whether additional broker-level human review
   requirements are needed per category.

7. **`_broker_shell_gate_evidence` helper function unused**: This helper was defined in 88R
   but is not called from `build_permission_broker` (it builds sg_evidence inline). The helper
   remains for reference but should be reviewed in 88U.

## 18. Recommended Next Phase

**88U — Broker + Shell Gate Integration Test Expansion and Edge-Case Review**

Scope:
- Edge case test matrix for all 24 SGP_CATEGORIES × active/no-active-task combinations
- Compound command integration tests (&&, ||, ;, pipe/tee chains through broker)
- False-positive review (legitimate operations incorrectly blocked)
- False-negative review (dangerous operations incorrectly allowed)
- Review category-level human review requirements vs. broker action-level gate
- Remove or refactor unused `_broker_shell_gate_evidence` helper
- CLI integration tests for combined broker+shell-gate output (expand from 3 CLI smoke tests)
- Review `blocked_by_scope` vs `blocked_by_shell_gate` for policy_forbidden_file (§17.3)
