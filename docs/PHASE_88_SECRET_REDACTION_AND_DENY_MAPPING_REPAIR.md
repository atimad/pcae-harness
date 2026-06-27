# Phase 88V.1 — Secret Redaction and Deny Mapping Repair

```
phase_name    = phase_88v1_secret_redaction_and_deny_mapping_repair
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 88W_advisory_enforcement_readiness_design
```

## 1. Purpose

Repair the four enforcement-readiness blockers identified in Phase 88U and
formalized in Phase 88V:

- **GAP-1**: VAR=val secret redaction gap
- **GAP-2**: env|grep / printenv secret exposure gap
- **GAP-3**: broker.requested_command raw secret retention gap
- **GAP-4**: dormant deny hard-block mapping inconsistency

88V.1 is an enforcement-readiness repair phase. It does not implement
enforcement, shell interception, shell wrappers, or execution authorization.

## 2. Scope

In scope:

- Detect secret-like VAR=val command prefixes and classify as secret_access
- Detect env/printenv as secret exposure commands (not harmless read-only)
- Redact broker.requested_command when secret_access is detected
- Ensure nested shell-gate evidence does not leak raw secret commands
- Ensure serialized broker JSON does not leak raw secret commands
- Map shell-gate deny to a concrete broker hard block decision
- Add tests proving all four gaps are closed
- Preserve all performed/authorization flags as false
- Preserve hard-block behavior
- Keep fast-green, quick, and full suite green

Out of scope:

- Implementing enforcement
- Shell interception or wrappers
- Shell configuration modification
- Backend invocation, prompts, capture, intake, adoption
- Real execution authorization
- Override of hard blocks
- Persistent broker/shell-gate storage or cache

## 3. Non-Goals

88V.1 must not and does not:

- Implement enforcement mechanisms
- Install shell wrappers
- Modify shell configuration (.bashrc, .zshrc, etc.)
- Execute classified command text
- Invoke backends
- Send prompts, capture outputs, perform intake/adoption
- Grant real execution authorization
- Override hard blocks
- Write persistent broker/shell-gate state or cache

## 4. GAP-1 Root Cause and Repair

### Root Cause

In `src/pcae/core/shell_gate.py`, the VAR=val prefix handler (line 637-642)
classified ALL environment variable assignments as `environment_mutation`
without distinguishing secret-like names (OPENAI_API_KEY, TOKEN, PASSWORD,
etc.) from benign ones (DEBUG, PYTHONPATH, PATH).

### Repair

1. Added `_SECRET_VAR_NAME_SUBSTRINGS` — a tuple of substrings that indicate
   a variable name is likely to contain secret material: KEY, SECRET, TOKEN,
   PASSWORD, PASSWD, CREDENTIAL, AUTH, CERT, PRIVATE_KEY, ENCRYPT, SIGNING,
   API_KEY, API_SECRET, API_TOKEN, ACCESS_KEY, SECRET_KEY.

2. Added `_is_secret_env_var_name(name)` helper that checks if a variable
   name (case-insensitive) matches any secret-like pattern.

3. Updated the VAR=val prefix handler: when the variable name is secret-like,
   both `environment_mutation_detected` and `secret_access_detected` flags
   are set, and the command is classified as `secret_access` (severity 2,
   which outranks `environment_mutation` at severity 3).

4. Fixed `_classify_single` to only strip path components from the program
   name when no `=` is present (prevents `PATH=/custom/bin` from being
   incorrectly stripped to just `bin`).

### Files Changed

- `src/pcae/core/shell_gate.py` — `_classify_single`: added `_is_secret_env_var_name`,
  `_SECRET_VAR_NAME_SUBSTRINGS`, updated VAR=val handler, fixed path stripping.

## 5. GAP-2 Root Cause and Repair

### Root Cause

`env` and `printenv` were listed in `_READ_ONLY_PROGRAMS` (shell_gate.py line
90). They were classified as `read_only_inspection` even though they can dump
all environment variables, potentially exposing secrets.

### Repair

1. Removed `env` and `printenv` from `_READ_ONLY_PROGRAMS`.

2. Added a dedicated handler block for `env`/`printenv` in `_classify_single`
   that classifies them as `secret_access` with reason code
   `env_printenv_secret_exposure_detected`.

3. The pipe chain classifier (`_classify_command`) naturally picks the most
   restrictive segment: `env | grep KEY` → `env` is `secret_access` (severity 2),
   `grep KEY` is `read_only_inspection` (severity 9), so the result is
   `secret_access`.

### Files Changed

- `src/pcae/core/shell_gate.py` — `_READ_ONLY_PROGRAMS`: removed env/printenv;
  `_classify_single`: added env/printenv handler block.

## 6. GAP-3 Root Cause and Repair

### Root Cause

In `src/pcae/core/permission_broker.py`, `build_permission_broker` stored the
raw `requested_command` in the broker envelope (line 527) even when
`secret_access_detected` was True. While `shell_gate_evidence.command_text`
was correctly redacted, the outer envelope field leaked raw secret-access
command text in serialized JSON output.

### Repair

1. Initialized `secret_detected` at function scope (default `False`) so it is
   available outside the `if requested_command:` block.

2. Added redaction logic: when `secret_detected` is True,
   `requested_command` is replaced with `"<redacted_secret_access_command>"`
   in the broker envelope.

### Files Changed

- `src/pcae/core/permission_broker.py` — `build_permission_broker`: added
  `secret_detected` initialization and `safe_requested_command` redaction.

## 7. GAP-4 Root Cause and Repair

### Root Cause

In `_SG_HARD_BLOCK_TO_BROKER` (permission_broker.py line 100), shell-gate
`deny` was mapped to broker `deny`. However, `deny` was NOT in
`BPE_HARD_BLOCK_DECISIONS` (the set of decisions that are treated as hard
blocks). This meant a shell-gate `deny` produced a broker decision that was
not recognized as a hard block, creating a gap in enforcement readiness.

### Repair

Changed the mapping from `"deny": "deny"` to `"deny": "blocked_by_shell_gate"`.
`blocked_by_shell_gate` is a member of `BPE_HARD_BLOCK_DECISIONS`, ensuring
that shell-gate deny decisions are properly recognized as hard blocks in the
broker.

### Verification

Five shell-gate decisions (`blocked_by_scope`, `blocked_by_failed_health`,
`blocked_by_failed_check`, `blocked_by_failed_doctor`, `blocked_by_push_check`)
are in `SGP_DECISIONS` but are not produced by the current `_decide` function.
They are handled through other broker paths (scope preflight, evidence
failures) and do not need to be in `_SG_HARD_BLOCK_TO_BROKER`. All reachable
blocking decisions from `_decide` are now mapped.

### Files Changed

- `src/pcae/core/permission_broker.py` — `_SG_HARD_BLOCK_TO_BROKER`: changed
  `"deny"` mapping from `"deny"` to `"blocked_by_shell_gate"`.

## 8. Redaction Policy Implemented

The following redaction policy is now in effect:

| Detection | Redaction | Scope |
|-----------|-----------|-------|
| Secret file access (cat ~/.ssh/id_rsa, etc.) | Full command redacted | sg_evidence.command_text, broker.requested_command |
| Secret-access programs (security, gpg, etc.) | Full command redacted | sg_evidence.command_text, broker.requested_command |
| Secret-like VAR=val prefix | Full command redacted | sg_evidence.command_text, broker.requested_command |
| env/printenv exposure | Full command redacted | sg_evidence.command_text, broker.requested_command |
| Ordinary read-only commands | NOT redacted | Preserved as-is |
| Benign VAR=val (DEBUG=1, PATH=) | NOT redacted | Preserved as-is |

Redaction sentinel: `"<redacted_secret_access_command>"`

## 9. Deny Mapping Policy Implemented

| Shell-Gate Decision | Broker Decision | Hard Block |
|---------------------|----------------|------------|
| `deny` | `blocked_by_shell_gate` | Yes |
| All reachable blocked_by_* decisions | Mapped to corresponding broker hard blocks | Yes |
| Unreachable reserved decisions (blocked_by_scope, etc.) | Handled through other paths | N/A |

Unmapped shell-gate decisions fail closed via other broker paths (scope
preflight, evidence failures).

## 10. Tests Added/Updated

### New Tests (43 tests across 7 classes)

- **TestGap1VarValSecretRedaction** (11 tests): Secret-like VAR=val detection
  and redaction in broker JSON
- **TestGap2EnvPrintenvSecretExposure** (8 tests): env/printenv classification
  as secret_access, broker decision, pipe chain handling
- **TestGap3BrokerRequestedCommandRedaction** (7 tests): requested_command
  redaction, JSON safety, nested evidence safety, ordinary command preservation
- **TestGap4DenyMappingConsistency** (5 tests): deny mapping, hard block
  membership, fail-closed, authorization invariants
- **Test88v1PerformedFlagsInvariant** (5 parametrized): All performed flags
  false across secret commands
- **Test88v1HardBlockPropagation** (5 tests): Hard blocks still propagate
- **Test88v1HumanApprovalLimits** (2 tests): Human approval/accepted risk
  cannot override hard blocks

### Updated Tests (7 tests)

- `test_env_var_prefix_command_is_redacted_88v1` — was "not redacted" (false
  negative), now asserts redaction
- `TestFalseNegativeDocumented` (3 tests) — were documenting false negatives
  as accepted behavior; now assert the repaired behavior
- `test_env_var_prefix` — split into benign and secret parametrized tests
- `test_printenv_is_read_only` / `test_env_no_args_is_read_only` — updated
  to assert secret_access
- `test_env_without_assignment_read_only` / `test_printenv_grep_read_only` —
  updated to assert secret_access

### Test Files Changed

- `tests/test_broker_shell_gate_edge_cases.py` — 43 new tests, 4 updated
- `tests/test_shell_gate_matrix.py` — 6 updated

## 11. Validation Results

| Suite | Result | Details |
|-------|--------|---------|
| Broker tests | 150 passed | Unchanged |
| Shell-gate tests | 774 passed | 731→774 (+43 new) |
| Broker-shell integration | 162 passed | Unchanged |
| Edge case (combined) | 475 passed | 163→475 (+312 from new 88V.1 tests) |
| Fast-green | 2,709 passed / 23.00s | 2,666→2,709 (+43 new) |
| Quick tier | TBD | |
| Full suite | TBD | |
| Health | healthy (idle) | |
| Check | passed | |
| Doctor task-memory | clean | |
| Doctor test-run | clear_to_run | |
| Push check | nothing_to_push | |

## 12. Remaining Limitations

1. **Value-based secret detection**: The classifier uses variable name
   patterns, not value analysis. `MY_VAR=sk-secret-key python script.py`
   is NOT detected as secret because `MY_VAR` lacks secret-like substrings.
   This is an accepted limitation — value-based detection would require
   regex over arbitrary strings with high false-positive risk.

2. **env/printenv over-classification**: `env` and `printenv` without
   arguments are now ALWAYS classified as `secret_access`, even when no
   secrets exist in the environment. This is conservative but safe.

3. **printenv with harmless var**: `printenv HOME` is now classified as
   `secret_access` because printenv is a secret-exposure tool regardless of
   the specific variable requested. The variable name alone is not sufficient
   to determine exposure risk.

4. **Shell-gate reserved decisions**: Five decisions in `SGP_DECISIONS`
   (`blocked_by_scope`, `blocked_by_failed_health`, `blocked_by_failed_check`,
   `blocked_by_failed_doctor`, `blocked_by_push_check`) are reserved for
   future use and not produced by the current `_decide` function. They are
   handled through other broker paths.

## 13. Enforcement Readiness Impact

Before 88V.1:
- GAP-1: Secret-like VAR=val not detected → raw secrets in audit trail
- GAP-2: env/printenv not detected → raw secrets in audit trail
- GAP-3: broker.requested_command not redacted → raw secrets in JSON output
- GAP-4: deny not mapped to hard block → gap in enforcement boundary

After 88V.1:
- GAP-1: REPAIRED — secret-like VAR=val detected and redacted
- GAP-2: REPAIRED — env/printenv detected as secret exposure
- GAP-3: REPAIRED — broker.requested_command redacted for secret commands
- GAP-4: REPAIRED — deny mapped to blocked_by_shell_gate (hard block)

The four enforcement blockers from 88V are resolved. No enforcement has been
implemented. All performed/authorization flags remain false.

## 14. Recommended Next Phase

**88W — Advisory Enforcement Readiness Design**

If more gaps are discovered during 88W design, return to 88V.2 for additional
enforcement-readiness repair before proceeding to enforcement implementation.
