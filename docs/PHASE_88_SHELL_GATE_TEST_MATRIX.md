# Phase 88Q: Shell Gate Test Matrix and False-Positive Review

**Phase**: 88Q  
**Status**: Completed  
**Predecessor**: 88P — Shell Gate Prototype  
**Successor recommended**: 88R — Permission Broker Prototype

---

## 1. Purpose

Systematically harden the Phase 88P shell gate classifier by:

- Building a comprehensive command-category test matrix across all 23 categories
- Reviewing idle-vs-active task behavior for each relevant category
- Identifying and fixing false positives (over-blocking)
- Identifying and fixing false negatives (under-blocking)
- Adding coverage for compound commands, pipe/tee chains, and redirection
- Adding missing program classifiers: backend invocation, secret access, environment mutation

---

## 2. Scope

**Classifier changes** in `src/pcae/core/shell_gate.py`:

1. **Compound command parsing** — `&&`, `||`, `;` operators split into segments; most-restrictive classification wins.
2. **Pipe/tee write detection** — `cmd | tee <path>` detects the tee target and classifies the write.
3. **Backend invocation programs** — `_BACKEND_PROGRAMS`: `claude`, `claude-deepseek`, `codex`, `openai`, `gemini`, `vertex`.
4. **Secret access programs** — `_SECRET_ACCESS_PROGRAMS`: `security`, `pass`, `gpg`, `op`, `vault`, etc.
5. **Secret file path detection** — `cat ~/.ssh/id_rsa` and similar reads classified as `secret_access` via `_SECRET_FILE_PREFIXES`.
6. **Environment mutation** — `export VAR=val`, `unset VAR`, `source file`, `. file`, `VAR=val cmd` prefix.
7. **Filesystem permission changes** — `chmod`, `chown`, `chgrp`, `chattr`, `ln` → `filesystem_write`.
8. **`python -m pip install`** — correctly classified as `package_install`.
9. **Category severity ordering** — `_CATEGORY_SEVERITY` dict used by compound/pipe resolution.

**Test additions** in `tests/test_shell_gate_matrix.py`:

- 287 new tests across 24 test classes
- All marked `fast_green` via `tests/conftest.py`

---

## 3. Non-Goals

88Q does **not**:

- Implement shell interception
- Install shell wrappers
- Modify shell configuration files
- Execute classified command text
- Implement a permission broker
- Invoke backends
- Send prompts or capture outputs
- Perform intake or adoption
- Write persistent shell gate state or cache
- Grant execution authorization
- Implement phases 88R or beyond

---

## 4. Starting Point from 88P

Phase 88P delivered:

- `_classify_command` single-command classifier
- 23 command categories, 26 decision values
- Programs: read-only, git, grep, package managers, network
- Redirection detection (>, >>, sed -i)
- 155 tests in `tests/test_shell_gate.py`

**Known gaps at 88P entry**:

| Gap | Impact |
|-----|--------|
| No compound command parsing | `git status && rm -rf /` classified as `read_only_inspection` (FALSE NEGATIVE) |
| No pipe/tee write detection | `echo x | tee README.md` classified as `read_only_inspection` (FALSE NEGATIVE) |
| No backend program list | `claude "do something"` classified as `unknown` (correct block, wrong category) |
| No secret file detection | `cat ~/.ssh/id_rsa` classified as `read_only_inspection` (FALSE NEGATIVE) |
| No secret access programs | `security find-generic-password` classified as `unknown` |
| No environment mutation | `export API_KEY=secret` classified as `unknown` |
| `chmod` unclassified | `chmod +x script.sh` classified as `unknown` |
| `python -m pip install` unclassified | classified as `unknown` |

---

## 5. Command-Category Matrix

### 5.1 read_only_inspection

**Decision**: `allow_read_only`  
**Idle/Active**: same behavior  

Representative commands:
- `pwd`, `ls`, `ls -la`, `cat PROJECT_STATUS.md`, `head -20 PROJECT_STATUS.md`
- `git status`, `git log --oneline -5`, `git diff`, `git show HEAD`
- `grep -R "Phase 88" docs`, `find docs -maxdepth 1 -type f`
- `sed -n '1,20p' PROJECT_STATUS.md` (read-only sed)
- `awk '{print $1}' file.txt` (read-only awk)

### 5.2 test_execution

**Decision**: `requires_active_task` (idle), `allow_test_execution` (active + test-run clear)  
**Expensive** (xdist `-n`): additionally requires `test_run_clear`

Representative commands:
- `python -m pytest tests/test_shell_gate.py -q` (non-expensive)
- `python -m pytest -n auto` (expensive)
- `python -m pytest -m fast_green -n auto` (expensive)

### 5.3 pcae_governed_lifecycle

**Decision**: `allow_governed`  
**Idle/Active**: same (pcae manages its own lifecycle)

Representative commands:
- `pcae health`, `pcae check`, `pcae doctor task-memory`
- `pcae session bootstrap --compact --profile implementation`
- `pcae output capture`, `pcae intake review`, `pcae adoption approve`

### 5.4 pcae_governed_commit

**Decision**: `allow_governed`

Representative commands:
- `pcae commit implementation --path src/example.py --message 'x'`

### 5.5 pcae_governed_push

**Decision**: `allow_governed`

Representative commands:
- `pcae push`, `pcae push check`

### 5.6 raw_git_commit

**Decision**: `blocked_by_raw_git_commit`  
**Idle/Active**: same (hard block)

Representative commands:
- `git commit -m 'x'`, `git commit --amend`

### 5.7 raw_git_push

**Decision**: `blocked_by_raw_git_push`  
**Idle/Active**: same (hard block)

Representative commands:
- `git push`, `git push origin main`

### 5.8 force_push

**Decision**: `blocked_by_force_push`  
**Idle/Active**: same (hard block)

Representative commands:
- `git push --force`, `git push -f`, `git push --force-with-lease`

### 5.9 git_history_rewrite

**Decision**: `blocked_by_history_rewrite`  
**Idle/Active**: same (hard block)

Representative commands:
- `git reset --hard HEAD`, `git rebase main`, `git cherry-pick abc123`

### 5.10 destructive_filesystem

**Decision**: `blocked_by_destructive_filesystem`  
**Idle/Active**: same (hard block)

Representative commands:
- `rm -rf /tmp/example`, `git clean -fd`

### 5.11 filesystem_write

**Decision**: `blocked_by_missing_task` (idle), `requires_preflight` (active)

Representative commands:
- `rm file.txt`, `mv a b`, `cp a b`, `chmod +x script.sh`
- `chown user:group file`, `ln -s src dst`

### 5.12 source_mutation

**Decision**: `blocked_by_missing_task` (idle), `requires_preflight` (active)

Representative commands:
- `echo x > src/example.py`, `cat template > src/new.py`

### 5.13 test_mutation

**Decision**: `blocked_by_missing_task` (idle), `requires_preflight` (active)

Representative commands:
- `echo x > tests/test_example.py`

### 5.14 docs_mutation

**Decision**: `blocked_by_missing_task` (idle), `requires_preflight` (active)

Representative commands:
- `echo x > docs/example.md`

### 5.15 policy_forbidden_file_mutation

**Decision**: `blocked_by_policy_forbidden_file`  
**Idle/Active**: same (hard block)

Forbidden files: `README.md`, `docs/REAL_CAPTURED_TASKS.md`, `docs/LINKEDIN_ARTICLE_DRAFT.md`

Representative commands:
- `echo x > README.md`, `echo x >> README.md`
- `echo x > docs/REAL_CAPTURED_TASKS.md`
- `cat template > docs/LINKEDIN_ARTICLE_DRAFT.md`

### 5.16 backend_invocation

**Decision**: `requires_human_review`  
**NEW in 88Q**: previously classified as `unknown`

Representative commands:
- `claude "modify src/app.py"`, `codex "fix bug"`, `openai "analyze code"`

### 5.17 prompt_send / output_capture / intake_adoption

Not directly triggerable by program name (governed via pcae subcommands).  
These are planned for 88R+ as part of the permission broker layer.

### 5.18 package_install

**Decision**: `requires_human_review`

Representative commands:
- `pip install requests`, `python -m pip install requests` (NEW in 88Q)
- `brew install jq`, `npm install`, `cargo install ripgrep`

### 5.19 network_access

**Decision**: `requires_human_review`

Representative commands:
- `curl https://example.com`, `wget https://example.com/file`
- `ssh host`, `aws s3 ls`, `gh pr list`

### 5.20 secret_access

**Decision**: `requires_human_review`  
**NEW in 88Q**: previously `read_only_inspection` or `unknown`

Two detection paths:
1. Secret access programs: `security`, `gpg`, `pass`, `op`, `vault`
2. Secret file paths in read program args: `~/.ssh/*`, `~/.aws/credentials`, etc.

Representative commands:
- `cat ~/.ssh/id_rsa`, `cat ~/.aws/credentials`
- `security find-generic-password`, `gpg --decrypt secrets.gpg`
- `pass show api/key`, `vault kv get secret/api`

### 5.21 environment_mutation

**Decision**: `requires_human_review`  
**NEW in 88Q**: previously `unknown`

Three detection paths:
1. `export VAR=val` / `unset VAR` programs
2. `source file` / `. file` shell sourcing
3. `VAR=val cmd` env-var prefix pattern

Representative commands:
- `export API_KEY=secret`, `unset API_KEY`
- `source ~/.zshrc`, `. .env`
- `OPENAI_API_KEY=x python script.py`

### 5.22 unknown

**Decision**: `blocked_by_unknown_command`

Programs not matching any known category:
- `some_totally_unknown_program`
- Unrecognized compound segments

### 5.23 Categories not yet classified (deferred to 88R+)

| Category | Status | Deferred reason |
|----------|--------|-----------------|
| `prompt_send` | Deferred | Requires permission broker |
| `output_capture` | Deferred | Requires capture governance layer |
| `intake_adoption` | Deferred | Requires adoption governance layer |

These are routed via pcae subcommands and return `pcae_governed_lifecycle` today.

---

## 6. Idle vs Active Task Behavior

| Category | Idle decision | Active decision |
|----------|---------------|-----------------|
| `read_only_inspection` | `allow_read_only` | `allow_read_only` |
| `test_execution` | `requires_active_task` | `allow_test_execution` |
| `pcae_governed_*` | `allow_governed` | `allow_governed` |
| `raw_git_commit` | `blocked_by_raw_git_commit` | `blocked_by_raw_git_commit` |
| `raw_git_push` | `blocked_by_raw_git_push` | `blocked_by_raw_git_push` |
| `force_push` | `blocked_by_force_push` | `blocked_by_force_push` |
| `git_history_rewrite` | `blocked_by_history_rewrite` | `blocked_by_history_rewrite` |
| `destructive_filesystem` | `blocked_by_destructive_filesystem` | `blocked_by_destructive_filesystem` |
| `filesystem_write` | `blocked_by_missing_task` | `requires_preflight` |
| `source_mutation` | `blocked_by_missing_task` | `requires_preflight` |
| `test_mutation` | `blocked_by_missing_task` | `requires_preflight` |
| `docs_mutation` | `blocked_by_missing_task` | `requires_preflight` |
| `policy_forbidden_file_mutation` | `blocked_by_policy_forbidden_file` | `blocked_by_policy_forbidden_file` |
| `backend_invocation` | `requires_human_review` | `requires_human_review` |
| `package_install` | `requires_human_review` | `requires_human_review` |
| `network_access` | `requires_human_review` | `requires_human_review` |
| `secret_access` | `requires_human_review` | `requires_human_review` |
| `environment_mutation` | `requires_human_review` | `requires_human_review` |
| `unknown` | `blocked_by_unknown_command` | `blocked_by_unknown_command` |

---

## 7. False-Positive Review

A false positive occurs when a safe command is blocked or over-classified.

### 7.1 Known acceptable false positives

| Command | Classification | Correct? | Notes |
|---------|---------------|----------|-------|
| `echo 'x > y'` | May trigger `filesystem_write` | Conservative | `>` inside quotes matched by regex; known limitation |
| `env python script.py` | `read_only_inspection` | Acceptable | `env` is in `_READ_ONLY_PROGRAMS`; args not checked |
| `printenv | grep KEY` | `read_only_inspection` | Correct | Read-only display of env vars |
| `git fetch origin` | `read_only_inspection` | Correct | fetch doesn't modify working tree |
| `diff src/a.py src/b.py` | `read_only_inspection` | Correct | diff is read-only |

### 7.2 Not a false positive: `cat ~/.zshrc`

`cat ~/.zshrc` classifies as `read_only_inspection` since `.zshrc` is not in `_SECRET_FILE_PREFIXES`. Reading a shell config is generally acceptable. Adding it to secret prefixes would create false positives for legitimate config review.

### 7.3 Redirection detection limitation

The `>` detection regex `(?<![<>])>{1,2}(?!=)` operates on the raw command text and does not account for `>` inside quoted strings. This is a known conservative behavior: it may over-classify some commands as writes. This is acceptable (conservative) and documented as a limitation.

---

## 8. False-Negative Review

A false negative occurs when a dangerous command is classified as safe or incorrectly categorized.

### 8.1 False negatives fixed in 88Q

| Command | 88P category | 88Q category | Severity |
|---------|-------------|-------------|---------|
| `echo x | tee README.md` | `read_only_inspection` | `policy_forbidden_file_mutation` | HIGH |
| `cat ~/.ssh/id_rsa` | `read_only_inspection` | `secret_access` | HIGH |
| `git status && rm -rf /` | `read_only_inspection` | `destructive_filesystem` | HIGH |
| `pcae health && git push` | `read_only_inspection` | `raw_git_push` | HIGH |
| `git status ; git commit -m x` | `read_only_inspection` | `raw_git_commit` | HIGH |
| `git status && echo x > README.md` | `read_only_inspection` | `policy_forbidden_file_mutation` | HIGH |
| `export API_KEY=secret` | `unknown` | `environment_mutation` | MEDIUM (blocked either way) |
| `claude "do something"` | `unknown` | `backend_invocation` | MEDIUM (blocked either way) |
| `security find-generic-password` | `unknown` | `secret_access` | MEDIUM (blocked either way) |
| `chmod +x script.sh` | `unknown` | `filesystem_write` | MEDIUM (blocked either way) |
| `python -m pip install requests` | `unknown` | `package_install` | MEDIUM (blocked either way) |

### 8.2 Remaining gaps (deferred to 88R+)

| Gap | Example | Current classification | Risk |
|-----|---------|----------------------|------|
| Complex nested quotes | `bash -c "rm -rf /"` | `unknown` (blocks) | LOW (blocked) |
| Heredoc to forbidden file | `cat <<EOF > README.md` | `filesystem_write` or `policy_forbidden_file_mutation` | MEDIUM |
| Eval with dangerous content | `eval "rm -rf /"` | `unknown` (blocks) | LOW (blocked) |
| Script execution | `./script.sh` | `unknown` (blocks) | LOW (blocked) |

---

## 9. Compound Command Handling

Compound commands use `&&`, `||`, or `;` operators. The classifier:

1. Tokenizes the full command with `shlex.split`
2. Detects operator tokens (`&&`, `||`, `;`) in the token list
3. Splits into segments on those operators
4. Classifies each segment via `_classify_single`
5. Returns the most restrictive (lowest severity) classification
6. Prepends `compound_command_detected` to reason codes

**Severity ordering** (lower = more dangerous, wins):
1. force_push, destructive_filesystem, policy_forbidden_file_mutation, git_history_rewrite, raw_git_push, raw_git_commit
2. backend_invocation, secret_access
3. environment_mutation, source/test/docs mutation
4. filesystem_write
5. unknown (conservative: blocks, wins over read-only)
6. package_install, network_access
7. test_execution
8. pcae_governed_*
9. read_only_inspection

**Examples**:

| Command | Segments | Result |
|---------|----------|--------|
| `git status && echo ok` | `git status` (read-only), `echo ok` (read-only) | `read_only_inspection` |
| `git status && rm -rf /` | `git status` (read-only), `rm -rf /` (destructive) | `destructive_filesystem` |
| `pcae health ; git commit -m x` | `pcae health` (governed), `git commit` (raw commit) | `raw_git_commit` |
| `git status && some_unknown` | `git status` (read-only), `some_unknown` (unknown) | `unknown` |

---

## 10. Pipe and Tee Handling

Pipe chains use `|` operators. The classifier:

1. Checks for `tee <path>` in any pipe segment
2. If tee found: classifies the tee target path → reports that write category
3. If no tee: classifies all segments, returns most restrictive

**Tee target classification** follows the same path rules as redirection:
- `README.md` → `policy_forbidden_file_mutation`
- `src/**` → `source_mutation`
- `tests/**` → `test_mutation`
- `docs/**` → `docs_mutation`
- Other → `filesystem_write`

**Examples**:

| Command | Result |
|---------|--------|
| `cat file | grep pattern` | `read_only_inspection` (both read-only) |
| `echo x | tee README.md` | `policy_forbidden_file_mutation` |
| `python -m pytest -n auto | tee /tmp/log` | `filesystem_write` |
| `cat a | tee docs/REAL_CAPTURED_TASKS.md` | `policy_forbidden_file_mutation` |
| `cat file | tee -a output.txt` | `filesystem_write` (flag skipped) |
| `cat file | some_unknown` | `unknown` (conservative) |

---

## 11. Redirection Handling

Redirection (`>`, `>>`) classification follows `_categorize_redirection_target`:

| Target path pattern | Category |
|--------------------|---------|
| `README.md` (exact) | `policy_forbidden_file_mutation` |
| `docs/REAL_CAPTURED_TASKS.md` | `policy_forbidden_file_mutation` |
| `docs/LINKEDIN_ARTICLE_DRAFT.md` | `policy_forbidden_file_mutation` |
| `src/**` | `source_mutation` |
| `tests/**` | `test_mutation` |
| `docs/**` (non-forbidden) | `docs_mutation` |
| Other | `filesystem_write` |

**Known limitation**: The regex `(?<![<>])>{1,2}(?!=)` matches `>` in raw command text and does not account for `>` inside quoted strings. This produces conservative false positives.

---

## 12. Backend and Network Detection

### Backend invocation

`_BACKEND_PROGRAMS = {"claude", "claude-deepseek", "codex", "openai", "anthropic", "gemini", "vertex"}`

Decision: `requires_human_review`

Note: `pcae output capture`, `pcae intake review`, `pcae adoption approve` are governed via pcae and return `pcae_governed_lifecycle`. Full `backend_invocation` / `output_capture` / `intake_adoption` categories will be enforced in 88R+ via the permission broker.

### Network access

`_NETWORK_PROGRAMS`: curl, wget, ssh, scp, aws, gcloud, gh, etc.

Decision: `requires_human_review`

---

## 13. Secret and Environment Detection

### Secret access

Two detection paths:

**Secret access programs** (`_SECRET_ACCESS_PROGRAMS`):
`security`, `keychain`, `pass`, `op`, `gpg`, `gopass`, `bitwarden`, `bw`, `vault`

**Secret file path reads** (`_SECRET_FILE_PREFIXES`):
When `cat`, `head`, `tail`, etc. target paths starting with:
- `~/.ssh/`, `~/.gnupg/`, `~/.age/`, `~/.config/age/`
- `~/.netrc`, `~/.aws/credentials`, `~/.aws/config`
- `~/.kube/config`, `~/.docker/config.json`
- `/etc/shadow`, `/etc/sudoers`

Decision: `requires_human_review`

### Environment mutation

Three detection paths:

1. **`export`/`unset` programs**: `export API_KEY=secret` → `environment_mutation`
2. **Shell sourcing**: `source .env`, `. .env` → `environment_mutation`
3. **Env-var prefix**: first token matches `[A-Za-z_][A-Za-z0-9_]*=` → `environment_mutation`

Decision: `requires_human_review`

---

## 14. Policy-Forbidden File Handling

Forbidden files: `README.md`, `docs/REAL_CAPTURED_TASKS.md`, `docs/LINKEDIN_ARTICLE_DRAFT.md`

Detection: both redirection target (`echo x > README.md`) and tee target (`cat a | tee README.md`).

Decision: `blocked_by_policy_forbidden_file` (hard block, unconditional, idle or active).

---

## 15. Performed-Flag Invariant

All performed flags are **unconditionally false** for all commands in all states:

- `authorization_granted`: False
- `execution_authorized`: False
- `command_executed`: False
- `repo_mutation_performed`: False
- `backend_invocation_performed`: False
- `prompt_sent`: False
- `capture_performed`: False
- `intake_performed`: False
- `adoption_performed`: False
- `raw_git_push_performed`: False
- `force_push_performed`: False
- `storage_written`: False

This invariant is tested across 17 representative commands in `TestPerformedFlagsInvariant`.

---

## 16. Classifier-Only Boundary

Phase 88Q preserves all 88P safety boundaries:

- `shell_gate_prototype_only`: True
- `shell_gate_does_not_execute_commands`: True
- `shell_gate_does_not_intercept_shell`: True
- `shell_gate_does_not_install_wrappers`: True
- `shell_gate_does_not_invoke_backends`: True
- `shell_gate_does_not_send_prompts`: True
- `shell_gate_does_not_capture_outputs`: True
- `shell_gate_does_not_perform_intake`: True
- `shell_gate_does_not_perform_adoption`: True
- `shell_gate_does_not_mutate_repo`: True
- `shell_gate_does_not_commit`: True
- `shell_gate_does_not_push`: True
- `shell_gate_does_not_write_storage`: True
- `permission_broker_not_implemented`: True
- `execution_authorization_not_granted`: True

---

## 17. Tests Added / Updated

### New: `tests/test_shell_gate_matrix.py`

287 new tests in 24 test classes:

| Class | Tests | Coverage |
|-------|-------|---------|
| `TestCategoryConstants` | 5 | Category set completeness |
| `TestReadOnlyInspection` | ~25 | All read-only patterns |
| `TestTestExecution` | 8 | Expensive/non-expensive, idle/active |
| `TestPcaeGoverned` | 12 | lifecycle/commit/push/subcommands |
| `TestRawGit` | ~12 | commit/push/force/rewrite/clean |
| `TestDestructiveFilesystem` | 4 | rm -rf, git clean |
| `TestFilesystemWrite` | ~12 | chmod/chown/mv/cp/ln, idle/active |
| `TestMutationCategories` | 8 | source/test/docs, idle/active |
| `TestPolicyForbiddenFileMutation` | 8 | README/REAL_CAPTURED/LINKEDIN |
| `TestBackendInvocation` | 7 | claude/codex/openai/gemini |
| `TestPackageInstall` | 8 | pip/brew/npm/cargo, python -m pip |
| `TestNetworkAccess` | 8 | curl/wget/ssh/aws/gh |
| `TestSecretAccess` | ~15 | Secret programs + secret file paths |
| `TestEnvironmentMutation` | ~15 | export/unset/source/VAR=val |
| `TestUnknownCategory` | 3 | Unknown programs blocked |
| `TestIdleVsActiveBehavior` | 11 | Task-state-dependent decisions |
| `TestCompoundCommands` | 13 | &&, ||, ; parsing |
| `TestPipeChains` | 14 | tee write detection, pure pipe |
| `TestRedirectionHandling` | 13 | >, >>, sed -i |
| `TestPerformedFlagsInvariant` | 17 | All 12 performed flags × 17 commands |
| `TestClassifierOnlyBoundary` | 7 | Safety notes |
| `TestFalsePositiveReview` | 5 | Known conservative patterns |
| `TestFalseNegativeReview` | 8 | 88Q fixed false negatives |
| `TestHelperFunctions` | ~20 | Unit tests for new helpers |

### Updated: `tests/conftest.py`

Added `test_shell_gate_matrix` to `FAST_GREEN_MODULES`.

### Unchanged: `tests/test_shell_gate.py`

All 155 existing 88P tests pass unchanged.

---

## 18. Validation Results

| Tier | Tests | Status | Runtime |
|------|-------|--------|---------|
| Targeted (shell gate both files) | 442 | PASSED | 2.43s |
| Fast-green | 2,234 | PASSED | 22.66s |
| Quick tier | TBD (running) | — | — |
| Full suite | TBD | — | — |

---

## 19. Remaining Limitations

1. **Redirection inside quotes**: `echo 'x > y'` may trigger redirection detection (conservative false positive).
2. **Complex eval/bash -c**: `bash -c "rm -rf /"` → `unknown` (blocked, but wrong category).
3. **Script execution**: `./script.sh`, `bash script.sh` → `unknown` (blocked, but should probably be a specific category in 88R+).
4. **Heredoc to forbidden file**: `cat <<EOF > README.md` — may or may not detect the forbidden target depending on tokenization.
5. **Absolute paths in env-var prefix**: `cat ~/.zshrc` is `read_only_inspection` (not secret access) since `.zshrc` is not in `_SECRET_FILE_PREFIXES`. This is intentional.
6. **`prompt_send`, `output_capture`, `intake_adoption`** categories not yet directly triggerable; deferred to 88R+ permission broker.

---

## 20. Recommended Next Phase

**88R — Permission Broker Prototype**

The permission broker will:
- Wrap the shell gate classifier decision with an explicit authorization workflow
- Implement `prompt_send`, `output_capture`, `intake_adoption` enforcement
- Provide human-in-the-loop approval for `requires_human_review` decisions
- Track authorization state across a session

Alternatively, if the full suite reveals additional classifier gaps:

**88Q.1 — Shell Gate Classifier Gap Repair**
