# Phase 88V — Broker + Shell Gate Enforcement Boundary Design

```
enforcement_boundary_design_name    = phase_88_broker_shell_gate_enforcement_boundary_design
enforcement_boundary_design_version = 0.1
enforcement_boundary_design_status  = draft_documented
implementation_status               = not_started
recommended_next_phase              = 88V.1_secret_redaction_and_deny_mapping_repair
```

## 1. Purpose

Define the enforcement boundary for the PCAE broker + shell gate system without
implementing any enforcement. Specify exactly what must be true before PCAE can
move from read-only command classification and policy aggregation into any form of
enforcement, command gating, command blocking, shell wrapping, or
execution-control prototype.

This document makes four obligations explicit:

1. **PCAE is currently read-only.** The broker classifies and aggregates evidence.
   It does not intercept, block, or gate any command.

2. **Enforcement is not the next step.** Four unresolved issues from Phase 88U
   (§13) must be repaired before any enforcement prototype begins.

3. **Each enforcement stage requires its own design and approval.** No stage may
   be skipped or collapsed into a faster path.

4. **Hard blocks are permanent.** No human approval, accepted risk, or operator
   override may cause a hard-blocked command to execute.

This is a design document. Nothing is implemented here. No source files, test
files, shell configuration files, or shell wrappers are modified.

## 2. Scope

In scope (design only):

- Enforcement terminology definitions
- Read-only, advisory, blocking, and execution gate stage definitions
- Enforcement preconditions and blockers
- Secret redaction requirements (all fields)
- env/printenv/VAR=value detection and redaction requirements
- `broker.requested_command` redaction requirements
- `deny` mapping consistency requirements
- Human approval limits
- Accepted risk limits
- Hard-block non-override rules
- Audit requirements before enforcement
- Performed-flag invariants
- Contradiction detection requirements
- CLI output safety requirements
- Persistent state/cache restrictions
- Shell wrapper restrictions
- Disable/rollback strategy
- Test requirements before enforcement
- Enforcement staging roadmap (Stages 0–6)
- Recommended next phase (88V.1)

Out of scope:

- Implementing any enforcement mechanism
- Modifying `src/pcae/core/permission_broker.py`
- Modifying `src/pcae/core/shell_gate.py`
- Installing shell wrappers or hooks
- Modifying shell configuration (`.bashrc`, `.zshrc`, etc.)
- Executing, intercepting, or blocking any command
- Invoking backends
- Sending prompts, capturing outputs, performing intake/adoption
- Granting execution authorization
- Writing persistent broker/shell-gate state or cache
- Phase 88V.1 task contract
- Phase 88W task contract
- Any phase beyond 88V

## 3. Non-Goals

88V must not and does not:

- Implement enforcement
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
- Change broker or shell gate source behavior
- Write persistent broker/shell-gate state or cache
- Change tests (except minor docs-validation correction if absolutely necessary)
- Raw git commit, raw git push, or force push

## 4. Current State from 88T and 88U

### 4.1 What Exists

After Phases 88P–88U, PCAE has:

- **Shell gate classifier** (`src/pcae/core/shell_gate.py`) — read-only command
  classifier; 24 categories, 26 decisions; no execution; all performed flags
  unconditionally False.

- **Permission broker** (`src/pcae/core/permission_broker.py`) — read-only
  policy aggregator; 24 broker decisions; consumes shell gate evidence; detects
  contradictions; redacts secret-access command text in `shell_gate_evidence`;
  all 14 performed/authorization flags unconditionally False.

- **CLI surface** — `pcae shell-gate check` and `pcae permission-broker evaluate`
  return JSON envelopes with classification/aggregation results; no execution.

- **Test coverage** — 8,652 tests (fast-green: 2,666; quick: 7,915; full: 8,652);
  120 edge-case integration tests from 88U covering compound commands, pipe/tee,
  environment mutation, secret access, CLI envelope stability, task boundaries.

### 4.2 What Does Not Exist

- No shell interception mechanism
- No command blocking mechanism
- No shell wrapper
- No pre-commit hook invoking the broker
- No execution-time gate
- No enforcement mode
- No persistent broker/shell-gate state or cache

### 4.3 Known Gaps from 88U

Four findings from 88U are unresolved and act as enforcement blockers (§13):

| ID | Finding | Severity |
|---|---|---|
| GAP-1 | VAR=val secret command not redacted | Critical |
| GAP-2 | env\|grep and printenv secret exposure not detected | Medium |
| GAP-3 | broker.requested_command retains raw secret-access command | Critical |
| GAP-4 | "deny" dormant in _SG_HARD_BLOCK_TO_BROKER (not in BPE_HARD_BLOCK_DECISIONS) | Medium |

## 5. Enforcement Terminology

The following terms are used consistently throughout this document and all
subsequent enforcement design phases.

### 5.1 Classification

**Classification**: The act of reading a proposed command text and assigning it
a category and decision without executing it. Currently performed by
`_classify_command` + `_decide` in `shell_gate.py`. Always read-only.
Never causes side effects.

### 5.2 Aggregation

**Aggregation**: The act of combining classification evidence, preflight
evidence, task contract state, and explicit evidence flags into a single broker
decision. Currently performed by `build_permission_broker`. Always read-only.
Never causes side effects.

### 5.3 Gate

**Gate**: A decision point that an operation must pass through. A gate has an
input (proposed command or action), a policy (rules), and an output (allow,
deny, or require-more-evidence). A gate may be read-only (advisory) or
enforcement-capable (blocking/execution). PCAE currently has only advisory
gates.

### 5.4 Enforcement

**Enforcement**: The act of causing a gate decision to have real-world effect —
preventing a command from executing, blocking a commit, or requiring human
action before proceeding. **Enforcement does not exist in PCAE today.**

### 5.5 Advisory Gate

**Advisory gate**: A gate whose output is informational. The agent can read the
decision but is not technically prevented from proceeding. An advisory gate is
what PCAE currently has. `pcae permission-broker evaluate` returns a decision;
it does not prevent the agent from running any command.

### 5.6 Blocking Gate

**Blocking gate**: A gate that can prevent an action from proceeding without
operator override. Requires: a hook or interception point, a hard-block
non-override rule, an operator-visible disable path, and a rollback mechanism.
**Not implemented.**

### 5.7 Execution Gate

**Execution gate**: A gate that controls whether a command reaches the shell
execution layer. The strongest form of enforcement. Requires: all blocking gate
requirements plus: command redaction completeness, audit completeness, and a
full disable/rollback certification. **Not implemented.**

### 5.8 Hard Block

**Hard block**: A broker or shell gate decision from which no human approval,
accepted risk, or operator flag may grant execution. Hard blocks represent
unconditional policy: force push, raw git push, destructive filesystem
operations, policy-forbidden file mutations, test-run lock, unknown commands,
conflicting evidence.

### 5.9 Redaction

**Redaction**: Replacing a command string with a non-reversible sentinel value
(`<redacted_secret_access_command>`) before storing it in any audit record,
evidence field, CLI output, log, or persistent store. Redaction must apply to
every field that receives command text, not only to one field.

### 5.10 Enforcement Blocker

**Enforcement blocker**: A known gap in classification, redaction, or mapping
that must be resolved before any enforcement prototype begins. If enforcement
begins while a blocker is open, the blocker becomes a security defect under
active enforcement.

## 6. Read-Only Classifier Boundary

**Stage 0 — Current state after 88T/88U.**

The shell gate classifier and permission broker operate strictly within this
boundary:

- They receive command text as input.
- They return a structured decision envelope as output.
- They do not execute any command.
- They do not intercept any command.
- They do not communicate with any shell process.
- They do not install any hook, wrapper, or interception point.
- They do not write any file to disk (beyond the return value in memory).
- They do not invoke any backend.
- All 14 performed/authorization flags are unconditionally False.
- `execution_authorized` is unconditionally False regardless of decision.
- `authorization_granted` is unconditionally False regardless of decision.

The read-only classifier boundary must be preserved exactly as described at
Stage 0. Nothing at Stage 0 grants any execution authority.

**What `allow_preflight_only` means at Stage 0:**
`allow_preflight_only` means the presented evidence satisfies the broker's
preflight checks. It does not mean the command is safe to run. It does not mean
the command is authorized to run. It does not mean PCAE has approved execution.
It means: "no preflight evidence was missing or failed." The human and/or
AI agent must still decide whether to proceed.

## 7. Advisory Gate Boundary

**Stage 2 — Future. Requires Stage 1 repair first.**

An advisory gate can emit warnings, recommended decisions, and structured output
that an AI coding agent can read before deciding to proceed. Key properties:

- The advisory gate **does not block** any command.
- The advisory gate output is consumed by the agent voluntarily.
- The agent may disregard advisory gate output (this is a feature, not a bug —
  it proves the gate is advisory).
- Advisory gate output must satisfy all redaction requirements (§14, §15).
- Advisory gate output must include all audit fields (§21).
- Advisory gate output must have contradiction detection active (§23).
- Advisory gate output must have all performed flags False (§22).

**What distinguishes an advisory gate from Stage 0:**
At Stage 0, the broker is called explicitly. An advisory gate is integrated into
an agent's workflow contract so that the broker is consulted automatically before
certain actions, with the result surfaced to the agent before (not after) the
decision.

**Advisory gate does not require:**
- Shell interception
- Pre-commit hooks
- Shell wrappers
- Process monitoring

## 8. Blocking Gate Boundary

**Stage 5 — Future. Requires Stages 1–4 first.**

A blocking gate can prevent an action from proceeding without explicit operator
override. Minimum requirements before any blocking gate prototype:

1. All Stage 0–4 requirements satisfied.
2. GAP-1, GAP-2, GAP-3, GAP-4 from §13 fully resolved.
3. Complete secret redaction across all fields (§14, §15).
4. env/printenv/VAR=value detection and redaction (§16).
5. `deny` mapping consistency resolved (§17).
6. Full audit record for every blocked command (§21).
7. An operator-visible disable path that does not require code changes.
8. A tested rollback procedure (§27).
9. Explicit test coverage for: block fires, block overridden by operator disable,
   secret command redacted in block record, hard-block cannot be overridden.
10. A separate design document and approval for the blocking gate prototype.

**Blocking gate must not:**
- Block read-only commands
- Block `pcae` governed commands
- Override hard blocks with human approval
- Operate without an active disable path
- Be introduced as default behavior in the same phase it is prototyped

## 9. Execution Gate Boundary

**Stage 6+ — Future. Requires Stages 1–5 first.**

An execution gate controls whether a command reaches the shell execution layer.
This is the strongest form of enforcement. In addition to all blocking gate
requirements:

1. Shell interception mechanism fully specified in a separate design document.
2. Interception mechanism approved by operator before installation.
3. Interception mechanism reversible without code changes.
4. Zero leakage of raw secret commands through any interception path.
5. Full audit chain: command received → classified → brokered → decision made →
   interception record created → command allowed/blocked → audit written.
6. Separation between classification (read-only) and interception (execution-path).
7. No interception of `pcae` governed commands.
8. No interception of read-only commands.
9. Interception covers hard-block categories only in Stage 6 prototype.

**Execution gate is not designed here.** It requires a separate design phase
that cannot begin until Stages 1–5 are fully operational and validated.

## 10. What PCAE May Do Now

At Stage 0 (current state), PCAE is authorized to:

1. **Classify** any proposed command text with `_classify_command` / `_decide`.
2. **Aggregate** governance evidence with `build_permission_broker`.
3. **Return** a structured JSON decision envelope via CLI.
4. **Redact** secret-access command text in `shell_gate_evidence.command_text`.
5. **Hash** non-secret command text with SHA-256 for audit purposes.
6. **Detect** contradictions and record them in `conflicting_evidence_details`.
7. **Report** hard blocks, missing evidence, and human review requirements.
8. **Surface** advisory decisions to the agent or operator.
9. **Consult** `pcae doctor test-run` to detect active expensive test runs.
10. **Run** fast-green / quick / full test tiers to validate classifier behavior.

## 11. What PCAE Must Not Do Yet

At Stage 0, PCAE must not:

1. **Intercept** any shell command at the OS or shell level.
2. **Block** any command from executing.
3. **Install** shell wrappers, aliases, or functions that intercept commands.
4. **Modify** `.bashrc`, `.zshrc`, `.profile`, or any shell configuration file.
5. **Install** pre-commit hooks that invoke the broker for enforcement.
6. **Invoke** any backend (claude, codex, openai, anthropic, gemini, vertex).
7. **Send** prompts to any AI system.
8. **Capture** command outputs for analysis.
9. **Perform** intake or adoption operations.
10. **Grant** real execution authorization for any command.
11. **Override** hard blocks with human approval or accepted risk.
12. **Write** persistent broker or shell gate state or cache to disk.
13. **Monitor** shell processes for interception.
14. **Enforce** any decision at the execution layer.

## 12. Enforcement Preconditions

All of the following must be true before any enforcement prototype (Stage 2+)
begins:

### 12.1 Redaction completeness (BLOCKER)

- `shell_gate_evidence.command_text` is `<redacted_secret_access_command>` for
  all secret-access commands.
- `broker.requested_command` does NOT retain raw command text for secret-access
  commands. (Currently violated — GAP-3.)
- All other broker fields that may contain command text are also redacted.
- CLI JSON output contains no raw secret command text anywhere.
- Tests prove zero raw secret command leakage across all serialized fields.

### 12.2 Secret detection completeness (BLOCKER)

- `OPENAI_API_KEY=x cmd` classified as `secret_access` (or `environment_mutation`
  with forced redaction), not left unredacted. (Currently violated — GAP-1.)
- `env | grep KEY` classified conservatively (not `read_only_inspection`).
  (Currently a false negative — GAP-2.)
- `printenv KEY` classified conservatively. (Currently a false negative — GAP-2.)
- All fields visible in CLI output for secret-adjacent commands are sanitized.

### 12.3 Mapping completeness (BLOCKER)

- `deny` either: (a) removed from `_SG_HARD_BLOCK_TO_BROKER` if unreachable,
  or (b) added to `BPE_HARD_BLOCK_DECISIONS` if it is a hard block. (Currently
  inconsistent — GAP-4.)
- Every shell gate terminal decision has an explicit broker mapping.
- Unmapped decisions fail closed (`blocked_by_shell_gate` or `unknown`).

### 12.4 Audit completeness (precondition)

All minimum audit fields from §21 present and non-null for every broker call
before enforcement begins.

### 12.5 Contradiction detection (precondition)

`_check_sg_contradiction` fires on every broker call, including calls from any
future enforcement hook or wrapper.

### 12.6 Performed-flag invariant (precondition)

All 14 performed/authorization flags unconditionally False across all code paths
including any future enforcement-adjacent code.

### 12.7 Operator disable path (precondition)

A documented, tested, operator-accessible disable path exists before any
blocking gate or execution gate prototype. The disable path must not require a
code change or redeployment.

### 12.8 Rollback procedure (precondition)

A tested rollback procedure exists that removes any enforcement mechanism (hook,
wrapper, interception point) without leaving residual state.

### 12.9 Separate design approval (precondition)

Each enforcement stage (Stage 2–6) has its own design document reviewed and
approved before implementation begins.

## 13. 88U Findings as Enforcement Blockers

**Real enforcement must not begin while any of these remain unresolved.**

### GAP-1 — VAR=val secret command not redacted (CRITICAL BLOCKER)

**Finding (88U FN-1):** `OPENAI_API_KEY=sk-secret123 python script.py` is
classified as `environment_mutation`, not `secret_access`. The key value is NOT
redacted in `shell_gate_evidence.command_text` or `broker.requested_command`.
The API key leaks into the audit trail in plaintext.

**Why this blocks enforcement:** Under enforcement, this command might be logged,
stored in audit records, sent to a monitoring system, or displayed in a UI — all
with the raw API key visible. This is a confidentiality defect.

**Required repair (Phase 88V.1):** Detect known secret env-var name patterns
(e.g., `.*_API_KEY`, `.*_SECRET`, `.*_TOKEN`, `.*_PASSWORD`, `.*_CREDENTIAL`)
in `VAR=val` prefix commands and either: (a) reclassify as `secret_access` with
full redaction, or (b) keep `environment_mutation` but force redaction of command
text when a known-secret var name is present.

### GAP-2 — env|grep / printenv secret exposure (MEDIUM BLOCKER)

**Finding (88U FN-2, FN-3):** `env | grep AWS_SECRET_ACCESS_KEY` is classified
as `read_only_inspection` (both `env` and `grep` are in `_READ_ONLY_PROGRAMS`).
`printenv AWS_SECRET_ACCESS_KEY` is similarly classified as `read_only_inspection`.
Either command could expose a secret value in its output.

**Why this blocks enforcement:** If enforcement logs or audits read-only commands
before allowing them, these commands would be logged without any redaction — but
their output can expose secret values. Under advisory enforcement (Stage 2), this
is acceptable. Under any form of output capture or logging enforcement (Stage 5+),
it becomes a leakage path.

**Required repair (Phase 88V.1):** Detect `env | grep <VARNAME>` and
`printenv <VARNAME>` patterns where VARNAME matches known-secret patterns.
Classify conservatively as `secret_access` or `environment_mutation` with a
`potential_secret_output_detected` flag. Do NOT classify as `read_only_inspection`
when the output may contain secret values.

### GAP-3 — broker.requested_command raw secret retention (CRITICAL BLOCKER)

**Finding (88U RSL-1):** `build_permission_broker` stores the raw
`requested_command` value in the broker output dict without checking whether it
is a secret-access command. `shell_gate_evidence.command_text` is redacted
correctly, but `broker.requested_command` retains the raw string (e.g.,
`"cat ~/.ssh/id_rsa"`). The CLI JSON output therefore contains the raw command
at `broker.requested_command`.

**Why this blocks enforcement:** Under enforcement, the broker output may be:
- Logged in audit records
- Returned to AI agents
- Sent to monitoring systems
- Displayed in UI

Any of these paths exposes the raw secret command. The redaction at
`shell_gate_evidence.command_text` is insufficient if `broker.requested_command`
is also visible.

**Required repair (Phase 88V.1):** In `build_permission_broker`, when
`secret_detected=True`, set `broker["requested_command"]` to
`"<redacted_secret_access_command>"` instead of the raw `requested_command` value.
All other fields that receive command text must also be checked.

### GAP-4 — Dormant deny mapping inconsistency (MEDIUM BLOCKER)

**Finding (88U SI-1):** `_SG_HARD_BLOCK_TO_BROKER` contains the entry
`"deny": "deny"`. The `"deny"` decision maps to the broker decision `"deny"`.
However, `"deny"` is NOT in `BPE_HARD_BLOCK_DECISIONS`. This means:

- If the SG ever returned `"deny"`, the broker would route it at priority 1 (as
  a hard-block-map entry) and return `"deny"`.
- But `hard_block_present = broker_decision in BPE_HARD_BLOCK_DECISIONS` would
  be `False` because `"deny"` is not in `BPE_HARD_BLOCK_DECISIONS`.
- The audit field `hard_block_present` would be `False` despite the decision
  being a routing-level hard block.

No current SG classifier path produces `"deny"`, so this is dormant. But
dormant inconsistencies become active defects when any of the following occur:
- A new SG classification path is added that produces `"deny"`
- An enforcement prototype queries `hard_block_present` to decide whether to
  block a command
- An audit system uses `hard_block_present` as a signal

**Required repair (Phase 88V.1):** Either:
- (a) Add `"deny"` to `BPE_HARD_BLOCK_DECISIONS` (treating it as a hard block),
  OR
- (b) Remove `"deny"` from `_SG_HARD_BLOCK_TO_BROKER` if it is intentionally
  unreachable (with a comment documenting why).
- Either way, document the decision.

## 14. Secret Redaction Requirements

The following requirements apply to all broker and shell gate code paths before
any enforcement prototype begins. They extend and harden the partial redaction
already present after 88T.

### 14.1 Scope of redaction

Redaction must cover **every broker-visible field** that receives command text,
not only `shell_gate_evidence.command_text`. Specifically:

| Field | Must be redacted when secret_access_detected |
|---|---|
| `shell_gate_evidence.command_text` | Yes (already done in 88T) |
| `broker.requested_command` | Yes (not done — GAP-3) |
| `broker.broker_mapping_reason` (contains `sg:decision->broker:decision`) | Only decision labels, not command text — check for leakage |
| Any new audit field added in 88V.1+ | Yes |
| CLI stdout JSON (every field) | Yes |

### 14.2 Redaction sentinel

The sentinel value `<redacted_secret_access_command>` must be used exactly and
consistently. No variation (`[REDACTED]`, `***`, `null`) is permitted except
where a field is structurally null (e.g., `shell_gate_command_text_hash=null`).

### 14.3 Hash behavior

- Non-secret commands: SHA-256 hash of raw command text stored in
  `shell_gate_command_text_hash`.
- Secret commands: `shell_gate_command_text_hash=null`. No hash is computed
  from the redacted sentinel (the sentinel is not the command text).

### 14.4 Redaction timing

Redaction must occur **before** any field is:
- Stored in any dict or object
- Passed to any function (including `_check_sg_contradiction`)
- Logged or written to any output
- Returned by any API call

The current 88T implementation redacts before `sg_evidence` is constructed and
before contradiction detection. This timing must be preserved and extended to
`broker.requested_command`.

### 14.5 Test requirements for redaction

Before enforcement, a test suite must prove:
- `broker.requested_command` is `<redacted_secret_access_command>` for all
  secret-access commands
- `shell_gate_evidence.command_text` is `<redacted_secret_access_command>` for
  all secret-access commands
- `shell_gate_command_text_hash` is `null` for all secret-access commands
- The raw secret command text does NOT appear anywhere in the serialized JSON
  output of `build_permission_broker` for secret-access commands
- The raw secret command text does NOT appear anywhere in the CLI stdout JSON
  for `pcae permission-broker evaluate` with a secret command

## 15. requested_command Redaction Requirements

`broker.requested_command` is the outer broker envelope field that mirrors the
`--requested-command` CLI argument back to the caller. It exists for reference
and audit. Under the current implementation it retains the raw command text even
for secret-access commands (GAP-3).

**Before enforcement:**

- `broker.requested_command` must be set to `<redacted_secret_access_command>`
  when `secret_access_detected=True`.
- This must be applied in `build_permission_broker` at the same point where
  `stored_command_text` is computed.
- The raw `requested_command` must not be stored in any intermediate variable
  that escapes into any output path.
- After repair, `broker.requested_command` and `shell_gate_evidence.command_text`
  must both be `<redacted_secret_access_command>` for secret-access commands.
- A test must verify: `json.dumps(build_permission_broker(...))` does not contain
  the raw secret command text anywhere in the serialized output.

## 16. env/printenv/VAR=value Handling Requirements

The following three patterns represent an incomplete secret-detection boundary
that must be closed before enforcement.

### 16.1 VAR=val prefix with known-secret variable names (GAP-1)

**Current behavior:** `OPENAI_API_KEY=sk-x python script.py` → `environment_mutation`,
command text NOT redacted.

**Required behavior before enforcement:**

- Maintain a set of known-secret env-var name patterns, e.g.:
  `.*_API_KEY`, `.*_SECRET`, `.*_SECRET_KEY`, `.*_SECRET_ACCESS_KEY`,
  `.*_TOKEN`, `.*_PASSWORD`, `.*_CREDENTIAL`, `.*_PRIVATE_KEY`,
  `OPENAI_.*`, `ANTHROPIC_.*`, `AWS_.*`, `GITHUB_.*_TOKEN`.
- When a `VAR=val` prefix command matches a known-secret pattern:
  - Either reclassify to `secret_access` with full redaction, OR
  - Keep `environment_mutation` but set `secret_access_detected=True` for
    redaction purposes.
- The command text must be redacted in all broker-visible fields.

### 16.2 env piped to grep/similar (GAP-2)

**Current behavior:** `env | grep KEY` → `read_only_inspection`.

**Required behavior before enforcement:**

- Detect `env | grep <VARNAME>` and similar patterns where `env` output is
  filtered for potentially-secret variable names.
- Classify as `environment_mutation` or `secret_access` with
  `potential_secret_output_detected=True`.
- Do NOT classify as `read_only_inspection` when the output may contain secret
  env var values.

### 16.3 printenv with variable name argument (GAP-2)

**Current behavior:** `printenv AWS_SECRET_ACCESS_KEY` → `read_only_inspection`.

**Required behavior before enforcement:**

- When `printenv` is called with a specific variable name argument, detect
  whether the variable name matches a known-secret pattern.
- If yes: classify as `secret_access` with `secret_access_detected=True`.
- If no: keep `read_only_inspection` (reading a non-sensitive env var is safe).

### 16.4 Scope note

The known-secret pattern set is not exhaustive by design. The goal is defense in
depth, not complete coverage. Unknown secret vars remain a residual risk that is
acceptable at Stage 2 (advisory), becomes lower-risk at Stage 3 (dry-run), and
must be re-evaluated at Stage 5 (blocking).

## 17. deny Mapping Consistency Requirements

The `_SG_HARD_BLOCK_TO_BROKER` mapping must be internally consistent before
enforcement. The consistency requirements are:

### 17.1 Every SG terminal decision must have an explicit broker mapping

Terminal decisions are those that `_decide` in `shell_gate.py` can return.
Each must appear in one of:
- `_SG_HARD_BLOCK_TO_BROKER` (routes to hard-block broker decision at priority 1), OR
- `_SG_ALLOW_DECISIONS` (routes to non-blocking broker path), OR
- Handled explicitly in `_broker_decide` priority chain.

No SG decision may be silently ignored or fall through to an unexpected broker
path.

### 17.2 Hard block mapping consistency

Every entry in `_SG_HARD_BLOCK_TO_BROKER` whose value is in
`BPE_HARD_BLOCK_DECISIONS` must result in `hard_block_present=True` in the
broker output. Currently `"deny"` violates this: it is routed at priority 1 but
maps to `"deny"` which is NOT in `BPE_HARD_BLOCK_DECISIONS`.

**Resolution:** Choose one of:
- **Option A:** Add `"deny"` to `BPE_HARD_BLOCK_DECISIONS`. This makes any
  `"deny"` broker decision a hard block. Semantically correct if `deny` is
  unconditional.
- **Option B:** Remove `"deny"` from `_SG_HARD_BLOCK_TO_BROKER` and handle it
  as a fallback at priority 7 (missing evidence) or priority 9 (allow). Only
  valid if `"deny"` is confirmed unreachable.

### 17.3 Fail-closed requirement

When a SG decision is not recognized by the broker:
- The broker must fail closed (`blocked_by_shell_gate` or `unknown`).
- The broker must never silently pass through an unrecognized decision as a
  non-blocking result.

### 17.4 Dormant mapping prohibition before enforcement

No dormant or partially-consistent mapping entry may exist before any enforcement
prototype. A mapping is dormant if: (a) it is in `_SG_HARD_BLOCK_TO_BROKER` but
the mapped broker decision is not in `BPE_HARD_BLOCK_DECISIONS`, or (b) it
references an SG decision that no classifier path can currently produce.

## 18. Human Approval Limits

Human approval (`human_approval_present=True`) satisfies a limited review gate
and nothing more. These limits apply at all enforcement stages and are permanent:

1. **Human approval may satisfy a review requirement.** If the broker requires
   human review for a non-hard-block decision and `human_approval_present=True`,
   the broker may advance to `allow_preflight_only`.

2. **Human approval must not override hard blocks.** A command that fires any
   entry in `_SG_HARD_BLOCK_TO_BROKER` at priority 1 receives a hard-block broker
   decision regardless of `human_approval_present`.

3. **Human approval must not authorize execution.** `human_approval_present=True`
   never causes `execution_authorized=True` or `authorization_granted=True`.

4. **Human approval must not suppress redaction.** Secret-access commands must
   be redacted even when `human_approval_present=True`.

5. **Human approval must not bypass a missing task contract.** Mutating actions
   require an active task. `human_approval_present=True` does not satisfy the
   task contract requirement.

6. **Human approval must not bypass failed evidence.** If `health_passed=False`,
   `check_passed=False`, `doctor_passed=False`, `tests_passed=False`, or
   `push_check_passed=False`, human approval does not override these failures.

7. **Human approval alongside a hard block is a contradiction** and must be
   detected by `_check_sg_contradiction` → `blocked_by_conflicting_evidence`.

## 19. Accepted Risk Limits

`accepted_risk_present=True` is a disclosure and audit signal only. It does not
grant any capability. These limits apply at all enforcement stages and are
permanent:

1. **Accepted risk is disclosure/audit evidence only.** It records that the
   operator is aware of a risk. It does not mitigate the risk.

2. **Accepted risk must not override hard blocks.** A hard-blocked command
   remains hard-blocked regardless of `accepted_risk_present`.

3. **Accepted risk must not authorize execution.** `accepted_risk_present=True`
   never causes `execution_authorized=True` or `authorization_granted=True`.

4. **Accepted risk must not suppress redaction.** Secret-access commands must
   be redacted even when `accepted_risk_present=True`.

5. **Accepted risk must not bypass failed governance checks.** Failed health,
   check, doctor, tests, and push-check are not overridden by accepted risk.

6. **Accepted risk alongside a hard block is a contradiction** and must be
   detected by `_check_sg_contradiction` → `blocked_by_conflicting_evidence`.

7. **Accepted risk alongside required human review does not satisfy the review.**
   `accepted_risk_present=True` and `human_review_present=False` yields
   `requires_human_review`, not `allow_preflight_only`.

## 20. Hard-Block Non-Override Rules

Hard blocks are unconditional. The following rules apply at all stages:

1. A hard-blocked command must not execute under any operator configuration.
2. A hard-blocked command must not be unblocked by any broker flag or evidence field.
3. A hard-blocked command must not be unblocked by human approval.
4. A hard-blocked command must not be unblocked by accepted risk.
5. A hard-blocked command must not be unblocked by an operator disable path.
   (The disable path disables the enforcement *mechanism*, not the policy.)
6. At an enforcement stage, the enforced hard blocks are: `blocked_by_force_push`,
   `blocked_by_raw_git_push`, `blocked_by_shell_gate` (for unknown commands and
   raw git commit), `blocked_by_scope` (for policy-forbidden files), and
   `blocked_by_conflicting_evidence`.
7. `blocked_by_task_contract` and `blocked_by_test_run_lock` are hard blocks at
   the broker level but are clearable by the underlying condition being resolved
   (creating a task contract, or waiting for the test run to finish). They are
   not override-able by flags.

## 21. Audit Requirements Before Enforcement

Every broker call made during enforcement (Stage 2+) must produce an audit
record containing at minimum the following fields. Fields marked with (GAP) must
be repaired before enforcement:

| Field | Source | Notes |
|---|---|---|
| `timestamp` | `generated_at` | ISO 8601 UTC |
| `repository_root` | broker envelope | |
| `requested_action` | broker input | |
| `original_command_classification_status` | `shell_gate_command_category` | |
| `redacted_command_text` | `shell_gate_evidence.command_text` | Must be sentinel for secrets |
| `redaction_applied` | `shell_gate_command_text_redacted` | bool |
| `redaction_reason` | derived from `secret_access_detected` | |
| `requested_command_field` | `broker.requested_command` | Must be redacted (GAP-3) |
| `shell_gate_category` | `shell_gate_command_category` | |
| `shell_gate_decision` | `shell_gate_decision` | |
| `broker_decision` | `broker.decision` | |
| `hard_block_present` | `broker.hard_block_present` | Must be correct after GAP-4 repair |
| `hard_block_sources` | `broker.hard_block_sources` | |
| `hard_block_reason` | `broker.reason_codes` filtered | |
| `human_approval_present` | evidence field | |
| `accepted_risk_present` | `broker.accepted_risk_noted` | |
| `contradiction_detected` | `broker.conflicting_evidence_detected` | |
| `contradiction_details` | `broker.conflicting_evidence_details` | |
| `performed_flags` | all 14 broker flags | All must be False |
| `authorization_flags` | `authorization_granted`, `execution_authorized` | Both must be False |
| `evidence_sources` | `broker.evidence_sources` | |
| `missing_evidence` | `broker.missing_evidence` | |
| `active_task_detected` | `broker.active_task_detected` | |
| `schema_version` | envelope `schema_version` | |

## 22. Performed-Flag Invariants

The following 14 flags must be unconditionally `False` across all broker code
paths, including any future enforcement-adjacent code:

```
authorization_granted
execution_authorized
command_executed
repo_mutation_performed
backend_invocation_performed
prompt_sent
capture_performed
intake_performed
adoption_performed
commit_performed
push_performed
raw_git_push_performed
force_push_performed
storage_written
```

**These flags must remain False even when:**
- A hard block is triggered
- Human approval is present
- Accepted risk is present
- Any new enforcement code path is added

**Before enforcement**, a test must verify that every new code path in the
enforcement prototype satisfies this invariant. The existing 88T/88U parametrized
test (`TestPerformedFlagInvariant`, 56 tests, 14 flags × 4 decision paths) must
be extended to cover all new decision paths added by the enforcement prototype.

## 23. Contradiction Detection Requirements

`_check_sg_contradiction` must fire on every broker call. Its 13 conditions must
remain active and must not be weakened or bypassed. Before enforcement:

1. Contradiction detection must fire before the broker's priority-1 check, so
   contradictions are recorded in the audit even when a hard block wins.
2. Any new evidence field added by an enforcement prototype must be included in
   the contradiction check logic.
3. If an enforcement prototype adds new performed-flag-equivalent fields, those
   fields must be added to `_SG_PERFORMED_FORBIDDEN_KEYS` and checked by
   `_check_sg_contradiction`.
4. The contradiction → `blocked_by_conflicting_evidence` path must remain
   operative. No enforcement configuration may disable contradiction detection.
5. Tests must verify: (a) contradiction detected alongside hard block fires audit
   record but hard block wins, (b) contradiction alone (no hard block) yields
   `blocked_by_conflicting_evidence`, (c) contradiction detection cannot be
   suppressed by human approval or accepted risk.

## 24. CLI Output Safety Requirements

The CLI output of `pcae permission-broker evaluate --json` must satisfy:

1. **No raw secret command text anywhere in stdout.** For any command where
   `secret_access_detected=True`, the raw command string must not appear in
   `json.dumps(result)`. (Currently violated by GAP-3.)
2. **`schema_version` present** at envelope level.
3. **`generated_at` present** and non-empty.
4. **`broker.decision`** in `BPE_DECISIONS`.
5. **`broker.authorization_granted=False`** always.
6. **`broker.execution_authorized=False`** always.
7. **All 14 performed flags `False`** always.
8. **`broker.shell_gate_evidence`** present when `--requested-command` given,
   with `command_text` redacted for secret commands.
9. **`broker.shell_gate_command_text_hash=null`** for secret commands.
10. **`broker.warnings`** lists all active contradictions.

These requirements must be verified by automated tests before enforcement.
The existing `TestCLIJSONEnvelopeStability` test class (12 tests) covers most
of these but must be extended after GAP-3 repair to prove no raw secret leakage
in `broker.requested_command`.

## 25. Persistent State/Cache Restrictions

The broker and shell gate must not write persistent state or cache before
enforcement and must not do so as part of an enforcement prototype unless
explicitly designed and approved:

1. No file system writes from `build_permission_broker` or `_classify_command`.
2. No `.pcae/cache/` files created by broker or shell gate.
3. No audit log files written automatically by broker or shell gate.
4. No session state written by broker or shell gate.
5. An enforcement prototype that requires audit persistence must use an existing
   PCAE audit/storage mechanism — not a new ad-hoc file.
6. Any new persistent store introduced by an enforcement prototype must be
   documented in its own design phase.

## 26. Shell Wrapper Restrictions

Shell wrappers represent the highest risk of side effects. These restrictions
apply in perpetuity unless explicitly superseded by an approved design:

1. **No shell wrapper may be installed without operator opt-in.** An explicit
   operator command (e.g., `pcae enforcement enable --wrapper`) must be required.
2. **No shell wrapper may be installed by default** in any phase including its
   introduction phase.
3. **No shell configuration file may be modified** without explicit operator
   approval for each file. Batch modification is prohibited.
4. **Every shell wrapper must be reversible** by a single operator command
   without code changes.
5. **Shell wrappers must not intercept `pcae` governed commands.**
6. **Shell wrappers must not intercept read-only commands** (categories:
   `read_only_inspection`, `pcae_governed_lifecycle`, `pcae_governed_commit`,
   `pcae_governed_push`, `test_execution`).
7. **Shell wrappers must be audited.** Every interception must produce an audit
   record satisfying §21 before the command is allowed or blocked.
8. **Shell wrappers must not capture command output.** They may observe the
   command text and classification result; they must not read stdout/stderr.
9. **Shell wrappers must not modify command text.** They may block or allow;
   they must not transform.

## 27. Disable/Rollback Strategy

Any future enforcement prototype must implement the following disable/rollback
controls before it can be merged:

### 27.1 Operator-visible disable path

- A single CLI command must disable all enforcement mechanisms: e.g.,
  `pcae enforcement disable`.
- The disable command must produce visible confirmation (stdout) that enforcement
  is disabled.
- The disable command must not require a code change or redeployment.
- After disable, the system must return to Stage 0 behavior (read-only
  classification only).

### 27.2 Rollback procedure

- A documented rollback procedure must exist for each enforcement mechanism
  (hook, wrapper, config change).
- The rollback procedure must be tested in the same phase that introduces the
  mechanism.
- The rollback procedure must remove all residual state: wrapper files, hook
  files, config changes, generated audit records created by the mechanism.
- The rollback must be verifiable by a test that checks the pre-rollback state
  and post-rollback state.

### 27.3 No silent failure on disable

If the operator disables enforcement, any command that was previously blocked
must proceed without error or warning (the block is lifted, not just suppressed).
A suppressed block that re-activates on the next command is not a valid disable.

### 27.4 No enforcement as default

No enforcement mode may become the default configuration in the same phase it is
introduced. Every enforcement prototype phase starts with enforcement disabled.
The operator must explicitly enable enforcement after reviewing the design.

## 28. Test Requirements Before Enforcement

The following test requirements must be met before any enforcement prototype
(Stage 2+) begins. Requirements marked with (BLOCKER) cannot be waived.

### 28.1 Redaction coverage (BLOCKER)

- All broker-visible fields containing command text are redacted for secret-access
  commands.
- `json.dumps(build_permission_broker(..., command="cat ~/.ssh/id_rsa"))` contains
  no occurrence of `"~/.ssh/id_rsa"` or any substring of it.
- Same test for `"security find-generic-password"`.
- Same test for `"cat ~/.aws/credentials"`.

### 28.2 VAR=val secret detection (BLOCKER)

- `OPENAI_API_KEY=sk-secret123 python script.py` results in `command_text_redacted=True`.
- `AWS_SECRET_ACCESS_KEY=xxx aws s3 ls` results in `command_text_redacted=True`.
- `NOT_A_SECRET=value python script.py` results in `command_text_redacted=False`.

### 28.3 deny mapping consistency (BLOCKER)

- `"deny"` is either in `BPE_HARD_BLOCK_DECISIONS` (and a test verifies
  `hard_block_present=True` for a `deny` decision), or not in
  `_SG_HARD_BLOCK_TO_BROKER` (and a test verifies the map has no dormant entries).

### 28.4 requested_command redaction (BLOCKER)

- `broker.requested_command == "<redacted_secret_access_command>"` for all
  secret-access commands.
- `broker.requested_command == "cat ~/.ssh/id_rsa"` does not appear in the
  serialized JSON.

### 28.5 Performed-flag invariant under enforcement paths

- For every new code path in the enforcement prototype: all 14 performed flags
  are False.

### 28.6 Contradiction detection under enforcement paths

- Contradiction detection fires on every broker call in the enforcement prototype.
- `blocked_by_conflicting_evidence` cannot be suppressed by any enforcement
  configuration flag.

### 28.7 Hard-block non-override under enforcement

- `git push --force` is blocked by the enforcement prototype even when
  `human_approval_present=True`.
- `git push --force` is blocked by the enforcement prototype even when the
  operator disable path is NOT active.
- The disable path disables the enforcement mechanism; the operator can then run
  the command outside the enforcement path.

### 28.8 Disable path test

- After `pcae enforcement disable` (future command), the system returns to
  read-only classification behavior.
- No residual enforcement state remains after disable.

### 28.9 Fast-green preservation

- Adding an enforcement prototype must not reduce the fast-green test count or
  cause any fast-green test to fail.
- Enforcement-related tests may be `slow` or `integration` tier.

## 29. Enforcement Staging Roadmap

The following stages define the allowed enforcement evolution path. No stage may
be skipped. Each stage requires its own design document and approval before
implementation.

```
Stage 0 — Read-only classifier and broker aggregator (CURRENT)
Stage 1 — Enforcement readiness repair
Stage 2 — Advisory-only gate
Stage 3 — Explicit dry-run blocking simulation
Stage 4 — Opt-in command wrapper prototype
Stage 5 — Limited blocking enforcement
Stage 6 — Broader enforcement
```

### Stage 0 — Read-only classifier and broker aggregator (Current)

**Status:** Complete (88T/88U).

The shell gate classifier and permission broker operate as read-only tools.
`pcae shell-gate check` and `pcae permission-broker evaluate` return advisory
JSON. No command is blocked. No hook is installed. All performed flags are False.

**What exists at Stage 0:**
- 24 SGP categories, 26 SGP decisions, 24 BPE decisions
- Hard-block propagation (routing-only, not enforcement)
- Secret-access command redaction in `shell_gate_evidence.command_text`
- Contradiction detection
- 8,652-test suite (fast-green: 2,666; quick: 7,915)

**Stage 0 limitations (must be repaired before Stage 2):**
- GAP-1: VAR=val secret not redacted
- GAP-2: env|grep / printenv secret exposure not detected
- GAP-3: broker.requested_command raw secret retention
- GAP-4: deny mapping inconsistency

### Stage 1 — Enforcement Readiness Repair

**Status:** Not started. Next recommended phase: 88V.1.

**Goal:** Resolve all four enforcement blockers (GAP-1 through GAP-4) so that
the system is safe to use as a foundation for enforcement prototypes.

**Required deliverables:**

1. VAR=val prefix: known-secret pattern detection + redaction
2. env|grep / printenv: conservative reclassification for known-secret patterns
3. broker.requested_command: redact when `secret_access_detected=True`
4. deny: resolve mapping inconsistency (Option A or Option B from §17.2)
5. Tests proving zero raw secret leakage in all broker-visible fields
6. Tests proving all 14 performed flags still False after repair
7. Fast-green and quick tier still green after repair

**Stage 1 does not include:**
- Any enforcement mechanism
- Any shell wrapper or hook
- Any change to the CLI surface beyond what is needed for redaction repair

### Stage 2 — Advisory-Only Gate

**Status:** Future. Requires Stage 1 complete.

An advisory gate integrates the broker into an agent's workflow contract so that
the broker is consulted automatically before certain actions, with the advisory
result surfaced to the agent before (not after) the decision. No blocking occurs.
The agent may disregard the advisory result.

**Requires before Stage 2:**
- Stage 1 complete (all four blockers resolved)
- A separate design document for Stage 2

### Stage 3 — Explicit Dry-Run Blocking Simulation

**Status:** Future. Requires Stage 2 validated.

A dry-run blocking simulation allows an agent to request: "what would happen if
I enforced this decision?" and receive a structured response describing which
commands would be blocked, which would be allowed, and why — without any command
actually being blocked.

**Requires before Stage 3:**
- Stage 2 complete and validated
- A separate design document for Stage 3

### Stage 4 — Opt-In Command Wrapper Prototype

**Status:** Future. Requires Stage 3 validated.

An opt-in command wrapper is a shell function or alias (NOT a system-level
interception) that an operator explicitly installs and can explicitly remove. It
wraps specific high-risk commands (e.g., `git push`, `rm -rf`) with a broker
check before proceeding.

**Requires before Stage 4:**
- Stage 3 complete and validated
- All shell wrapper restrictions from §26 met
- Disable/rollback controls from §27 implemented and tested
- A separate design document for Stage 4

### Stage 5 — Limited Blocking Enforcement

**Status:** Future. Requires Stage 4 validated.

Limited blocking enforcement prevents hard-blocked commands from executing,
covering only the narrow set of unconditional hard blocks:
`force_push`, `raw_git_push`, `raw_git_commit`, `destructive_filesystem`,
`policy_forbidden_file`.

**Requires before Stage 5:**
- Stage 4 complete and validated
- All blocking gate requirements from §8 met
- Full audit for every blocked command (§21)
- A separate design document for Stage 5

### Stage 6 — Broader Enforcement

**Status:** Future. Requires Stage 5 validated, and a separate design phase.

Broader enforcement covers additional command categories and may include
execution-gate-level interception. This stage cannot be designed before Stage 5
is operational and validated. It requires a separate design document and is not
described further here.

### Forbidden Shortcuts

The following shortcuts are permanently forbidden regardless of urgency or
operator preference:

- **Skipping stages.** No transition from Stage 0 to Stage 3+ without Stages 1
  and 2 complete.
- **"Temporary" enforcement.** No enforcement mechanism introduced as temporary
  that lacks a disable path and rollback procedure.
- **Silent default.** No enforcement mode that activates by default without
  operator opt-in.
- **Combining repair and enforcement.** Stage 1 repair and Stage 2 enforcement
  must be in separate phases.
- **Hard-block override.** No configuration, flag, or operator action may cause
  a hard-blocked command to execute through an enforcement mechanism.

## 30. Recommended Next Phase

**88V.1 — Secret Redaction and Deny Mapping Repair**

Not 88W or any enforcement prototype.

88V.1 must repair the four enforcement blockers identified in §13:

1. **VAR=val secret redaction (GAP-1):** Add known-secret env-var name pattern
   detection to `_classify_single` in `shell_gate.py`. When the VAR=val prefix
   matches a known-secret pattern, set `secret_access_detected=True` and return
   `secret_access` (or `environment_mutation` with forced redaction).

2. **env|grep / printenv detection (GAP-2):** In `_classify_single` and
   `_classify_command`, detect `env | grep <VARNAME>` and
   `printenv <VARNAME>` where VARNAME matches a known-secret pattern. Reclassify
   to `environment_mutation` with `potential_secret_output_detected=True`, or to
   `secret_access`.

3. **broker.requested_command redaction (GAP-3):** In `build_permission_broker`,
   when `secret_detected=True`, set `requested_command_stored = "<redacted_secret_access_command>"` 
   instead of the raw value. Store the redacted value in `broker["requested_command"]`.

4. **deny mapping consistency (GAP-4):** Choose Option A (add `"deny"` to
   `BPE_HARD_BLOCK_DECISIONS`) or Option B (remove from `_SG_HARD_BLOCK_TO_BROKER`
   with documentation). Add a test that verifies the chosen resolution.

**88V.1 deliverables:**

- Source changes to `src/pcae/core/shell_gate.py` (GAP-1, GAP-2)
- Source changes to `src/pcae/core/permission_broker.py` (GAP-3, GAP-4)
- New tests proving zero raw secret leakage (all broker-visible fields)
- New tests proving env|grep/printenv correct classification
- New tests proving VAR=val redaction
- Fast-green and quick tier still green
- Phase document `docs/PHASE_88_SECRET_REDACTION_AND_DENY_MAPPING_REPAIR.md`
- PROJECT_STATUS.md and CHANGELOG.md updated

**88V.1 must not:**

- Implement any enforcement mechanism
- Install any shell wrapper
- Modify any shell configuration
- Start any Stage 2+ work

After 88V.1, the system will be at a fully consistent Stage 0 baseline with all
four enforcement blockers resolved, and Stage 2 design (advisory gate) may begin.
