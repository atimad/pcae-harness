# Phase 88P — Shell Gate Prototype

## 1. Purpose

Phase 88P introduces the first concrete shell gate implementation: a read-only command
classifier that accepts proposed shell command text, classifies it against the 23-category
taxonomy defined in Phase 88O, and returns a structured JSON gate decision envelope.

The prototype establishes the classification foundation required before the shell gate can
evolve into an active mediator (Phase 88Q: test matrix and false-positive review; Phase 88R:
permission broker prototype).

## 2. Scope

- New core module: `src/pcae/core/shell_gate.py`
- New command module: `src/pcae/commands/shell_gate.py`
- CLI registration in `src/pcae/cli.py`: `pcae shell-gate check --command "..." [--json]`
- Regression tests: `tests/test_shell_gate.py` (155 tests, fast tier)
- Fast-green inclusion: `tests/conftest.py` updated to include `test_shell_gate`

## 3. Non-Goals

88P does **not**:

- Execute shell commands
- Intercept shell execution at the OS or shell level
- Install shell wrappers or modify shell configuration
- Implement the permission broker
- Invoke backends or send prompts
- Capture outputs
- Perform intake or adoption
- Grant execution authorization
- Write persistent gate state or cache
- Raw git commit, raw git push, or force push

## 4. Relationship to 88O Design

Phase 88O (Shell Gate Design Reconciliation) documented the full shell gate architecture:
23 command categories, 26 decision values, policies for each category, and the relationship
between the shell gate, permission broker, and five explicit preflights.

Phase 88P implements the classifier layer only — the decision engine that maps command text
to `(category, decision)` pairs. It does not yet implement:
- Active shell interception (future: 88R+)
- Integration with the permission broker (future: 88R)
- Scope preflight invocation for mutation commands (future: 88Q+)

The divergence corrected in 88O.1 (gate_dry_run scope matching) was a prerequisite: the
shell gate reuses `_detect_task_contract` from `gate_dry_run.py` to detect active task
context.

## 5. Prototype Command

```
pcae shell-gate check --command "<shell command text>" [--json]
```

Examples:

```
pcae shell-gate check --command "ls -la" --json
pcae shell-gate check --command "git push --force" --json
pcae shell-gate check --command "python -m pytest -n auto" --json
pcae shell-gate check --command "pip install requests" --json
```

## 6. JSON Envelope

```json
{
  "schema_version": "0.1",
  "generated_at": "<ISO 8601>",
  "source_command": "pcae shell-gate check",
  "repository_root": "<path>",
  "shell_gate": { ... },
  "warnings": [],
  "errors": [],
  "safety_notes": { ... }
}
```

### shell_gate object

| Field | Type | Description |
|---|---|---|
| `gate_type` | string | Always `"shell_gate_prototype"` |
| `command_text` | string | Verbatim command text (not executed) |
| `command_category` | string | One of 23 SGP_CATEGORIES |
| `decision` | string | One of 26 SGP_DECISIONS |
| `reason_codes` | list[str] | Classification + decision rationale |
| `active_task_detected` | bool | Whether a task contract exists |
| `task_contract_path` | str\|null | Active task contract path if detected |
| `requires_active_task` | bool | Decision requires active task |
| `requires_preflight` | bool | Decision requires scope preflight |
| `requires_human_review` | bool | Decision requires human review |
| `requires_more_evidence` | bool | More evidence needed |
| `hard_block_present` | bool | Decision is a hard block (blocked_by_*) |
| `read_only_detected` | bool | Command classified as read-only |
| `filesystem_write_detected` | bool | Write to arbitrary filesystem location |
| `source_mutation_detected` | bool | Write to src/** |
| `test_mutation_detected` | bool | Write to tests/** |
| `docs_mutation_detected` | bool | Write to docs/** |
| `policy_forbidden_file_detected` | bool | Write to always-forbidden file |
| `raw_git_commit_detected` | bool | `git commit` without pcae governance |
| `raw_git_push_detected` | bool | `git push` without pcae governance |
| `force_push_detected` | bool | `git push --force` or `-f` |
| `history_rewrite_detected` | bool | rebase, cherry-pick, reset --hard |
| `destructive_filesystem_detected` | bool | `rm -rf`, `git clean -fd` |
| `backend_invocation_detected` | bool | Backend CLI invocation |
| `prompt_send_detected` | bool | Prompt send detected |
| `capture_detected` | bool | Output capture detected |
| `intake_adoption_detected` | bool | Intake/adoption detected |
| `package_install_detected` | bool | pip/brew/npm/cargo install |
| `network_access_detected` | bool | curl/wget/ssh/API clients |
| `secret_access_detected` | bool | Secret store access |
| `environment_mutation_detected` | bool | Environment mutation |
| `test_execution_detected` | bool | pytest command |
| `expensive_test_execution_detected` | bool | pytest -n (xdist parallel) |
| `test_run_preflight_required` | bool | Doctor test-run evidence required |
| `test_run_clear_to_run` | bool\|null | Doctor test-run result (null if not checked) |
| `authorization_granted` | bool | Always false |
| `execution_authorized` | bool | Always false |
| `command_executed` | bool | Always false |
| `repo_mutation_performed` | bool | Always false |
| `backend_invocation_performed` | bool | Always false |
| `prompt_sent` | bool | Always false |
| `capture_performed` | bool | Always false |
| `intake_performed` | bool | Always false |
| `adoption_performed` | bool | Always false |
| `raw_git_push_performed` | bool | Always false |
| `force_push_performed` | bool | Always false |
| `storage_written` | bool | Always false |
| `evidence_sources` | list[str] | Active task contract, doctor output |
| `missing_evidence` | list[str] | Evidence items required but absent |
| `safety_notes` | dict | Safety invariant flags |

## 7. Command Taxonomy Implemented

All 23 categories from 88O §6 are represented in the classifier:

| Category | Example |
|---|---|
| `read_only_inspection` | `ls`, `git status`, `grep`, `cat` |
| `test_execution` | `python -m pytest tests/` |
| `pcae_governed_lifecycle` | `pcae health`, `pcae task new` |
| `pcae_governed_commit` | `pcae commit --message "..."` |
| `pcae_governed_push` | `pcae push` |
| `raw_git_commit` | `git commit -m "..."` |
| `raw_git_push` | `git push origin main` |
| `force_push` | `git push --force`, `git push -f` |
| `git_history_rewrite` | `git rebase`, `git reset --hard`, `git cherry-pick` |
| `destructive_filesystem` | `rm -rf`, `git clean -fd` |
| `filesystem_write` | `echo x > /tmp/out.txt`, `rm file`, `cp`, `mv` |
| `source_mutation` | `echo x > src/pcae/core/foo.py` |
| `test_mutation` | `echo x > tests/test_new.py` |
| `docs_mutation` | `echo x > docs/PHASE_99_FOO.md` |
| `policy_forbidden_file_mutation` | `echo x > README.md` |
| `backend_invocation` | (future explicit programs) |
| `prompt_send` | (future explicit programs) |
| `output_capture` | (future explicit programs) |
| `intake_adoption` | (future explicit programs) |
| `package_install` | `pip install X`, `brew install X`, `npm install X` |
| `network_access` | `curl`, `wget`, `ssh`, `aws`, `gh` |
| `secret_access` | (future explicit programs) |
| `environment_mutation` | (future explicit programs) |
| `unknown` | Unrecognized program |

## 8. Decision Model Implemented

All 26 decision values from 88O §7 are present in SGP_DECISIONS. Active paths:

| Decision | When |
|---|---|
| `allow_read_only` | Read-only inspection with no redirection |
| `allow_governed` | pcae commit / pcae push / pcae lifecycle |
| `allow_test_execution` | pytest with active task + test-run clear |
| `requires_active_task` | Mutation or test without active task |
| `requires_preflight` | Mutation with active task (scope preflight needed) |
| `requires_human_review` | Package install, network, backend, secret |
| `blocked_by_raw_git_commit` | `git commit` |
| `blocked_by_raw_git_push` | `git push` (non-force) |
| `blocked_by_force_push` | `git push --force / -f / --force-with-lease` |
| `blocked_by_history_rewrite` | rebase / reset --hard / cherry-pick |
| `blocked_by_destructive_filesystem` | rm -rf / git clean |
| `blocked_by_policy_forbidden_file` | Write to README.md / REAL_CAPTURED_TASKS.md / LINKEDIN_ARTICLE_DRAFT.md |
| `blocked_by_test_run_lock` | Expensive pytest when doctor test-run reports busy |
| `blocked_by_unknown_command` | Unrecognized program (deny by default) |

## 9. Read-Only Classification

Programs classified as read-only without active task requirement:
- UNIX inspection: `ls`, `pwd`, `cat`, `head`, `tail`, `wc`, `stat`, `du`, `df`, `date`, `whoami`, etc.
- Search: `grep`, `rg`, `ag`, `find`
- Git read-only subcommands: `status`, `log`, `diff`, `show`, `branch`, `tag`, `remote`, `stash`, `blame`, `ls-files`, `fetch`, etc.
- `sed` without `-i` (in-place), without redirection
- `awk` without redirection

Read-only classification requires no shell operators that produce output.

## 10. Mutation Classification

Output redirection (`>`, `>>`) is detected via regex. The write target is examined:

- Target in `_SGP_POLICY_FORBIDDEN_FILES` → `policy_forbidden_file_mutation` (hard block)
- Target starts with `src/` → `source_mutation`
- Target starts with `tests/` → `test_mutation`
- Target starts with `docs/` → `docs_mutation`
- Otherwise → `filesystem_write`

`sed -i` (in-place edit) uses the last non-flag argument as the write target.

## 11. Git Operation Classification

| Command | Category | Decision |
|---|---|---|
| `git status/log/diff/...` | `read_only_inspection` | `allow_read_only` |
| `git commit` | `raw_git_commit` | `blocked_by_raw_git_commit` |
| `git push` (plain) | `raw_git_push` | `blocked_by_raw_git_push` |
| `git push --force/-f/--force-with-lease` | `force_push` | `blocked_by_force_push` |
| `git rebase` / `git cherry-pick` | `git_history_rewrite` | `blocked_by_history_rewrite` |
| `git reset --hard` | `git_history_rewrite` | `blocked_by_history_rewrite` |
| `git clean -fd` | `destructive_filesystem` | `blocked_by_destructive_filesystem` |
| `git fetch` | `read_only_inspection` | `allow_read_only` |

## 12. Test Execution Classification

`python -m pytest ...` (and `pytest`, `py.test`) → `test_execution`.

Subcategory — expensive (`-n`/`--numprocesses` xdist flag present):
- `expensive_test_execution_detected = true`
- `test_run_preflight_required = true`
- `pcae doctor test-run --json` is called (read-only) to check `clear_to_run`

## 13. Test-Run Preflight Integration

When `expensive_test_execution_detected` is true:

1. `_call_doctor_test_run(repo_root)` is called via subprocess (read-only, 15s timeout)
2. If `clear_to_run = false`: decision → `blocked_by_test_run_lock`
3. If `clear_to_run = true` + active task: decision → `allow_test_execution`
4. If `clear_to_run = true` + no active task: decision → `requires_active_task`
5. On any subprocess failure: assumes `clear_to_run = true` (conservative, avoids false locks)

`pcae doctor test-run` is a read-only command; calling it does not violate the
shell-gate-does-not-execute-commands invariant (it observes process state, never runs tests).

## 14. Policy-Forbidden File Handling

Three files are always forbidden regardless of task contract:

```
README.md
docs/REAL_CAPTURED_TASKS.md
docs/LINKEDIN_ARTICLE_DRAFT.md
```

Any command that writes to these files (via redirection or `sed -i`) classifies as
`policy_forbidden_file_mutation` and receives decision `blocked_by_policy_forbidden_file`.
This is a hard block with no override path.

Defined in `_SGP_POLICY_FORBIDDEN_FILES`, consistent with `_SPF_POLICY_FORBIDDEN_FILES`
in `scope_preflight.py`.

## 15. No-Active-Task Behavior

| Category | No-active-task decision |
|---|---|
| `read_only_inspection` | `allow_read_only` (no task required) |
| `test_execution` (non-expensive) | `requires_active_task` |
| `test_execution` (expensive, clear) | `requires_active_task` |
| `source_mutation` / `test_mutation` / `docs_mutation` / `filesystem_write` | `blocked_by_missing_task` |
| Hard blocks | Always blocked regardless of task |

## 16. Safety Flags

All performed flags are unconditionally false:

```python
authorization_granted = False
execution_authorized = False
command_executed = False
repo_mutation_performed = False
backend_invocation_performed = False
prompt_sent = False
capture_performed = False
intake_performed = False
adoption_performed = False
raw_git_push_performed = False
force_push_performed = False
storage_written = False
```

The `safety_notes` dict includes 15 invariant flags, all `true`, confirming:
- No command execution
- No shell interception
- No wrapper installation
- No backend invocation
- No prompt sending
- No output capture
- No intake/adoption
- No repo mutation
- No commit or push
- No persistent storage
- Permission broker not implemented
- Execution authorization not granted

## 17. Limitations

1. **Compound commands with `;` or `&&`**: Only the first token (program) is examined. A
   compound command like `ls && git push` classifies as `read_only_inspection` because `ls`
   is the first token. Full compound-command parsing is deferred to 88Q.

2. **Shell variable expansion**: Commands like `$(cmd)` or `${VAR}` are not evaluated.
   Such commands will likely classify as `unknown` (conservative).

3. **Alias resolution**: Shell aliases are not resolved.

4. **Path-based program variants**: `/usr/bin/git push --force` is handled (path stripped),
   but `env git push` or `command git push` is not.

5. **Categories `backend_invocation`, `prompt_send`, `output_capture`, `intake_adoption`,
   `environment_mutation`, `secret_access`**: Not yet populated by specific program
   patterns. Commands that would fall into these categories currently reach the `unknown`
   fallback and receive `blocked_by_unknown_command`. This is conservative.

6. **Pipe chains**: `grep foo src/ | head -20` classifies as `read_only_inspection`
   (correct). `cat foo | tee README.md` is not detected as a policy-forbidden write because
   `tee` target detection is not implemented (will classify as `unknown`).

7. **No persistent gate log**: Gate decisions are not written to any store.

## 18. Validation Results

- Targeted: `python -m pytest tests/test_shell_gate.py -q` → **155 passed**
- Fast-green: `python -m pytest -m "fast_green" -n auto` → **1,947 passed / 22.60s**
  (was 1,792; 155 new shell gate tests added)
- Quick tier: see PROJECT_STATUS.md
- Full suite: see PROJECT_STATUS.md

## 19. Recommended Next Phase

**88Q — Shell Gate Test Matrix and False-Positive Review**

88Q should:
1. Design a systematic test matrix covering all 23 categories × active/idle states
2. Review compound-command false positives (limitation 1 above)
3. Add `backend_invocation`, `environment_mutation`, `secret_access` program lists
4. Evaluate tee/pipe chain write detection
5. Add CLI integration tests (subprocess-based, marked slow)
6. Document the false-positive and false-negative risk register

artifact identity:
```
shell_gate_prototype_name=phase_88_shell_gate_prototype
shell_gate_prototype_version=0.1
shell_gate_prototype_status=complete
implementation_status=classifier_only
```
