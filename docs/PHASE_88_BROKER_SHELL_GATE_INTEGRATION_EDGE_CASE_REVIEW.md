# Phase 88U — Broker + Shell Gate Integration Test Expansion and Edge-Case Review

```
broker_shell_gate_edge_case_review_name    = phase_88u_broker_shell_gate_edge_case_review
broker_shell_gate_edge_case_review_version = 0.1
broker_shell_gate_edge_case_review_status  = implemented
implementation_status                      = complete
recommended_next_phase                     = 88V_broker_shell_gate_enforcement_boundary_design
```

## 1. Purpose

Pressure-test the 88T broker + shell gate integration prototype with expanded
edge-case test coverage. Verify that compound commands, pipe/tee chains,
environment mutation, network access, package install, unknown commands, secret
access variants, CLI JSON envelope structure, and idle-vs-active task boundary
all behave correctly and consistently. Document known false positives and false
negatives. No source changes are made unless a narrow classifier/broker defect
is found by a new test.

## 2. Scope

Changed in 88U:

- `tests/test_broker_shell_gate_edge_cases.py` — 120 new fast-green tests (12
  CLI integration tests also fast_green by module marker, slow+integration by
  method marker)
- `docs/PHASE_88_BROKER_SHELL_GATE_INTEGRATION_EDGE_CASE_REVIEW.md` — this document
- `PROJECT_STATUS.md`, `CHANGELOG.md`

No changes to:

- `src/pcae/core/permission_broker.py` — no defects found requiring source changes
- `src/pcae/core/shell_gate.py` — no defects found requiring source changes
- `src/pcae/commands/permission_broker.py` — CLI unchanged
- Any shell wrapper, shell config, backend invocation, or persistent state

## 3. Non-Goals

88U must not and did not:

- Implement shell interception
- Install shell wrappers
- Modify shell configuration
- Execute classified command text
- Invoke backends
- Send prompts
- Capture outputs
- Perform intake/adoption
- Grant real execution authorization
- Override hard blocks
- Replace human review
- Weaken broker/shell-gate decisions
- Write persistent broker/shell-gate state or cache
- Raw git commit, raw git push, or force push

## 4. Test Suite Structure

New file: `tests/test_broker_shell_gate_edge_cases.py`

All tests marked `pytestmark = pytest.mark.fast_green`. CLI integration tests
additionally marked `@pytest.mark.slow` and `@pytest.mark.integration`.

### 4.1 Test Classes

| Class | Tests | Focus |
|---|---|---|
| `TestCompoundCommandsThruBroker` | 11 | &&, \|\|, ; operators through broker |
| `TestPipeTeeWritesThruBroker` | 8 | Pipe+tee chains to various write targets |
| `TestEnvironmentMutationThruBroker` | 9 | export, unset, source, ., VAR=val |
| `TestNetworkAccessThruBroker` | 8 | curl, wget, ssh, scp, ping |
| `TestPackageInstallThruBroker` | 6 | pip, python -m pip, npm |
| `TestUnknownCommandThruBroker` | 6 | unknown-tool, bash, ./script.sh |
| `TestSecretAccessEdgeCases` | 11 | ~/.ssh/config, ~/.aws/credentials, etc. |
| `TestExpensivePytestClassification` | 7 | -n auto detection (no subprocess) |
| `TestCLIJSONEnvelopeStability` | 12 | Full CLI output structure (slow) |
| `TestIdleVsActiveTaskEdgeCases` | 12 | Task boundary across all command types |
| `TestNonHardBlockNeverAuthorizes` | 16 | auth flags always False for non-hard-blocks |
| `TestHardBlockMappingConsistency` | 9 | _SG_HARD_BLOCK_TO_BROKER integrity |
| `TestFalseNegativeDocumented` | 5 | Known false positives and negatives |

**Total: 120 tests**

## 5. Compound Command Behavior

Verified through broker for all three compound operators:

| Command | Classification | Broker Decision |
|---|---|---|
| `git status && git push origin main` | raw_git_push (most restrictive) | `blocked_by_raw_git_push` |
| `git status \|\| git push origin main` | raw_git_push (most restrictive) | `blocked_by_raw_git_push` |
| `git status ; git push origin main` | raw_git_push (spaces required) | `blocked_by_raw_git_push` |
| `pcae health && git push --force` | force_push | `blocked_by_force_push` |
| `cat file.py && echo done` | read_only_inspection | `allow_preflight_only` |
| `git log --oneline && git status` | read_only_inspection | `allow_preflight_only` |
| `pip install requests && python script.py` | unknown (severity 5 < 6) | `blocked_by_shell_gate` |

**Category severity** determines the winner in compound commands (lower = more
dangerous). `unknown` (5) beats `package_install` (6), so a compound of an
install with any unrecognized program blocks at the shell gate level.

**Semicolon without spaces** is a documented limitation: `shlex.split` treats
`status;` as a single token, so `git status; git push` is classified as
`unknown` (git unknown subcommand `status;`), not detected as a compound.
Commands with `;` as a space-separated token are handled correctly.

Compound `reason_codes` include `compound_command_detected` from the shell gate
evidence layer.

## 6. Pipe/Tee Write Behavior

`echo x | tee README.md` and `echo x | tee -a README.md` both block at
`blocked_by_scope` — the `-a` append flag is skipped by `_find_tee_write_target`
(tokens beginning with `-` are ignored), so `README.md` is detected as the tee
write target in both cases.

| Tee Target | Classification | Broker Decision (no task) |
|---|---|---|
| `README.md` | policy_forbidden_file_mutation | `blocked_by_scope` (hard) |
| `src/output.py` | source_mutation | `blocked_by_task_contract` (hard) |
| `docs/notes.md` | docs_mutation | `blocked_by_task_contract` (hard) |
| `output.txt` | filesystem_write | `blocked_by_task_contract` (hard) |

With an active task, `src/output.py` via tee yields `requires_more_evidence`
(missing health_check, governance_check, scope_preflight_for_command).

## 7. Environment Mutation Behavior

All five environment mutation patterns require human review (not a hard block):

| Command | SG Category | Broker Decision |
|---|---|---|
| `export OPENAI_API_KEY=x` | environment_mutation | `requires_human_review` |
| `unset OPENAI_API_KEY` | environment_mutation | `requires_human_review` |
| `source .env` | environment_mutation | `requires_human_review` |
| `. .env` | environment_mutation | `requires_human_review` |
| `OPENAI_API_KEY=x python script.py` | environment_mutation | `requires_human_review` |

With `human_review_present=True`: `allow_preflight_only`. `execution_authorized`
remains unconditionally `False`.

## 8. Network and Package Install Behavior

Network programs and package managers are classified conservatively as
`requires_human_review` (not hard blocks). Human review satisfies the gate.

| Command | Broker Decision |
|---|---|
| `curl https://example.com` | `requires_human_review` |
| `wget https://example.com/file` | `requires_human_review` |
| `ssh user@host` | `requires_human_review` |
| `scp file host:/tmp` | `requires_human_review` |
| `ping 8.8.8.8` | `requires_human_review` |
| `pip install requests` | `requires_human_review` |
| `pip install -r requirements.txt` | `requires_human_review` |
| `python -m pip install requests` | `requires_human_review` |
| `npm install` | `requires_human_review` |

## 9. Unknown Command Conservative Blocking

Any unrecognized program is classified as `unknown` → `blocked_by_unknown_command`
→ `blocked_by_shell_gate` (hard block). This applies to:

- `unknown-tool --dangerous` — hyphenated unknown tools
- `customtool run` — single-word unknown programs
- `./myscript.sh` — relative-path scripts (program = `myscript.sh`)
- `bash script.sh` — known false positive (see §12)

## 10. Secret Access Edge Cases

`_is_secret_file_access` detects path prefixes from `_SECRET_FILE_PREFIXES`.
Additional file paths confirmed:

| Command | Detected |
|---|---|
| `cat ~/.ssh/config` | ✓ (starts with `~/.ssh/`) |
| `cat ~/.aws/credentials` | ✓ (exact match `~/.aws/credentials`) |
| `cat ~/.kube/config` | ✓ (exact match `~/.kube/config`) |
| `cat ~/.netrc` | ✓ (exact match `~/.netrc`) |
| `cat ~/.ssh/id_ed25519` | ✓ (starts with `~/.ssh/`) |
| `cat ~/.gnupg/private-keys-v1.d` | ✓ (starts with `~/.gnupg/`) |
| `security find-generic-password` | ✓ (program in `_SECRET_ACCESS_PROGRAMS`) |
| `cat src/pcae/cli.py` | ✗ (not a secret path) |

For all secret-access commands:
- `shell_gate_evidence.command_text` → `<redacted_secret_access_command>`
- `shell_gate_command_text_redacted` → `True`
- `shell_gate_command_text_hash` → `None` (null — no hash for redacted)
- `broker.requested_command` → retains raw value (see §12 limitation 1)

With `human_review_present=True`, broker allows → `allow_preflight_only`.
`execution_authorized` remains `False`.

## 11. Expensive Pytest Classification

`_is_expensive_pytest` detects `-n` and `--numprocesses` flags. Verified at
classification level (no subprocess calls; safe for fast_green tier):

| Command | expensive_test_execution_detected |
|---|---|
| `python -m pytest -n auto` | `True` |
| `python -m pytest -n 4` | `True` |
| `pytest -n auto` | `True` |
| `pytest --numprocesses 4` | `True` |
| `python -m pytest tests -q` | `False` |
| `pytest tests/` | `False` |

When `expensive_test_execution_detected=True`, `build_permission_broker` calls
`_call_doctor_test_run` (subprocess). These cases are validated in the slow tier.

## 12. Known Limitations and Documented Behaviors

### 12.1 False Negatives

**FN-1: VAR=val prefix with secret value not redacted**

`OPENAI_API_KEY=sk-secret123 python script.py` is classified as
`environment_mutation` (not `secret_access`) and the command text is NOT
redacted. The classifier uses `_is_secret_file_access` which checks file path
prefixes, not env-var name patterns. The API key value leaks into the audit
trail via `broker.requested_command` and potentially `sg_evidence.command_text`.

_Impact_: Medium — API keys set via inline env-var prefix are visible in audit.
_Mitigation_: Environment mutation still requires human review.
_Future_: Could be addressed by checking arg values against known secret var
name patterns (OPENAI_API_KEY, AWS_SECRET_ACCESS_KEY, etc.).

**FN-2: `env | grep SECRET_KEY` classified as read_only**

`env | grep AWS_SECRET_ACCESS_KEY` is classified as `read_only_inspection`
because `env` is in `_READ_ONLY_PROGRAMS` and `grep` is a read-only filter.
The pipe chain takes the most restrictive segment, which is `read_only_inspection`
(severity 9 for both). Environment variables containing secrets could be exposed.

_Impact_: Low — observation only; no writes occur.
_Future_: Could detect `env` piped to `grep` as `output_capture`.

**FN-3: `printenv KEY` classified as read_only**

`printenv AWS_SECRET_ACCESS_KEY` is in `_READ_ONLY_PROGRAMS` and the argument
is a variable name (not a file path), so `_is_secret_file_access` returns False.

_Impact_: Low — the value is printed to stdout but not written anywhere.

### 12.2 False Positives (Conservative Blocking)

**FP-1: `bash script.sh` blocked as unknown**

`bash` is not in `_READ_ONLY_PROGRAMS`, `_PKG_PROGRAMS`, `_NETWORK_PROGRAMS`,
`_BACKEND_PROGRAMS`, `_SECRET_ACCESS_PROGRAMS`, or the git/rm/cp/mkdir/etc.
handlers. It falls to the `unknown` category → `blocked_by_shell_gate`.

_Rationale_: The classifier cannot evaluate what a bash script does without
executing it. Conservative blocking is correct.
_Future_: Could be addressed with an explicit `bash`/`sh`/`zsh` category that
requires human review rather than hard-blocking.

**FP-2: `git reset HEAD~1` blocked as unknown**

`git reset` without `--hard` or `--mixed` falls through the reset handler to
`git_unknown_subcommand`. Soft reset (no destructive flags) should arguably be
`requires_human_review`, not `blocked_by_shell_gate`.

_Impact_: Low — soft reset is rare in automated workflows.
_Future_: 88V could add explicit `git reset` without `--hard`/`--mixed` handling.

**FP-3: `;` without spaces not detected as compound operator**

`shlex.split("git status; git push")` yields `["git", "status;", ...]`. The
token `"status;"` ≠ `";"`, so compound detection fails. The command is parsed
as `git` with unknown subcommand `status;` → `blocked_by_shell_gate`.

This is technically a false positive for the compound detection (the push is
not identified), but the final decision (`blocked_by_shell_gate`) is still a
block. The push does not execute.
_Future_: Pre-split on `;` before shlex parsing.

### 12.3 Structural Inconsistency (Non-Defect)

**SI-1: `"deny"` in `_SG_HARD_BLOCK_TO_BROKER` but not in `BPE_HARD_BLOCK_DECISIONS`**

`_SG_HARD_BLOCK_TO_BROKER["deny"] = "deny"`. The `"deny"` decision is in
`BPE_DECISIONS` but not in `BPE_HARD_BLOCK_DECISIONS`. If the SG ever returned
`"deny"`, the broker would return `"deny"` at priority 1 (treated as hard block
in routing) but `hard_block_present` would be `False` (set from
`BPE_HARD_BLOCK_DECISIONS`).

In practice no current SG classifier path produces `"deny"`. The inconsistency
is dormant. `"deny"` should either be added to `BPE_HARD_BLOCK_DECISIONS` or
removed from `_SG_HARD_BLOCK_TO_BROKER` in a future cleanup phase.

### 12.4 Redaction Scope Limitation

**RSL-1: `broker.requested_command` retains raw command for secret-access cases**

`build_permission_broker` stores the literal `requested_command` in the broker
output dict. For secret-access commands, `shell_gate_evidence.command_text` IS
redacted to `<redacted_secret_access_command>`, but `broker.requested_command`
retains the original string (e.g., `"cat ~/.ssh/id_rsa"`).

The CLI JSON output therefore contains the raw command path in
`broker.requested_command` even for redacted secret commands.

_Impact_: Medium — the redaction at the SG evidence layer is correct but the
outer envelope retains the value.
_Future_: Could be addressed by also redacting `broker.requested_command` when
secret access is detected.

## 13. Idle vs Active Task Behavior

Comprehensive verification across command types:

| Command | Action | Task | Decision |
|---|---|---|---|
| `cat file.py` | read | none | `allow_preflight_only` |
| `cat file.py` | read | present | `allow_preflight_only` |
| `cp file.py file2.py` | read | none | `blocked_by_task_contract` (hard) |
| `cp file.py file2.py` | filesystem_write | present | `requires_more_evidence` |
| `python -m pytest tests -q` | read | none | `blocked_by_task_contract` (1d) |
| `python -m pytest tests -q` | read | present | `allow_preflight_only` |
| `export API_KEY=x` | read | none | `requires_human_review` |
| `export API_KEY=x` | environment_mutation | none | `blocked_by_task_contract` (p5) |
| `curl https://example.com` | read | none | `requires_human_review` |
| `cat ~/.ssh/id_rsa` | read | none | `requires_human_review` |
| `git push origin main` | read | present | `blocked_by_raw_git_push` (always) |
| `git push --force` | read | present | `blocked_by_force_push` (always) |

**Key finding**: Hard blocks (raw push, force push) fire regardless of task
state. `requires_active_task` at the SG level fires at broker priority 1d
(no task = hard block). `environment_mutation` as a broker action hits the
priority-5 task contract check even when the SG says `requires_human_review`.

## 14. CLI JSON Envelope Stability

Verified for `pcae permission-broker evaluate --requested-action read --json`:

| Field | Expected |
|---|---|
| `schema_version` | `"0.1"` |
| `generated_at` | Non-empty ISO timestamp |
| `repository_root` | Non-empty string |
| `broker` | dict |
| `broker.decision` | In `BPE_DECISIONS` |
| `broker.reason_codes` | list |
| `broker.authorization_granted` | `False` |
| `broker.execution_authorized` | `False` |
| All 14 performed flags | `False` |
| `broker.shell_gate_evidence` | Present when `--requested-command` given |
| `broker.shell_gate_evidence` | `None` when no `--requested-command` |
| `shell_gate_evidence.command_text` | `<redacted_secret_access_command>` for secret |
| `shell_gate_evidence.command_text_redacted` | `True` for secret |

## 15. Hard-Block Mapping Consistency

All values of `_SG_HARD_BLOCK_TO_BROKER` are valid `BPE_DECISIONS` entries.
All keys are valid `SGP_DECISIONS` entries. `_SG_HARD_BLOCK_DECISIONS_SET`
equals `frozenset(_SG_HARD_BLOCK_TO_BROKER.keys())`. 88T mapping changes
(`blocked_by_scope`, `blocked_by_task_contract`) are in `BPE_HARD_BLOCK_DECISIONS`.

See §12.3 for the `"deny"` inconsistency.

## 16. Non-Hard-Block Authorization Invariant

Verified by parametrized tests across all non-hard-block commands that:
- `authorization_granted` is always `False`
- `execution_authorized` is always `False`
- Even with `human_review_present=True` and `allow_preflight_only` decision:
  all 14 performed/authorization flags remain `False`

## 17. Test Counts and Suite Health

| Tier | Before 88U | After 88U | Delta |
|---|---|---|---|
| Fast-green (`-m fast_green`) | 2,546 | 2,666 | +120 |
| Quick (`-m "not slow and not phase_closure"`) | 7,807 | 7,915 | +108 |
| Full suite | 8,532 | 8,652 | +120 |

Fast-green: 2,666 passed / 25.74s.
Quick tier: 7,915 passed / 2:33.
Full suite: 8,652 passed / 28:57.

## 18. Safety Invariants Preserved

All 88T safety invariants confirmed across all 120 new tests:

1. All 14 performed/authorization flags unconditionally `False`
2. `hard_block_present=True` only for decisions in `BPE_HARD_BLOCK_DECISIONS`
3. No execution authorization granted
4. No backend invoked; no command executed; no shell intercepted
5. `shell_gate_evidence.command_text` redacted for secret-access commands
6. Contradiction detection fires before broker decision for non-hard-block paths
7. Human review does not override SG hard blocks
8. Accepted risk does not override SG hard blocks

## 19. Recommended Next Phase

**88V — Broker + Shell Gate Enforcement Boundary Design**

Design the boundary between:
- "What decisions could be enforced?" (broker decision output)
- "What enforcement mechanisms exist?" (hook layer, pre-commit, IDE integration)

Define the formal enforcement contract: which broker decisions are pre-conditions
for which actions; how enforcement failures are surfaced to AI coding agents;
what the minimal hook integration looks like without modifying shell config.

Address FP-1 (bash/shell blocking), RSL-1 (redaction scope), and SI-1 (deny
inconsistency) as part of enforcement boundary hardening.
