# Phase 93A — Narrow Shell Gate Design

```
phase_name    = phase_93a_narrow_shell_gate_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 93B — Narrow Shell Gate Prototype
```

## 1. Purpose and Scope

### 1.1 Purpose

Define the narrowest safe Production v1 shell-gate surface for PCAE. The shell gate is the classification and decision point between an agent's intention to run a shell command and the shell executing that command. This phase defines what the first Production v1 shell gate must surface, how it relates to the existing 91-series permission broker and hard-block registry, and what the go/no-go criteria are for a future prototype.

### 1.2 Scope

In scope (design only):

- Define the narrow Production v1 shell-gate surface: the minimum set of commands to classify, gate, or block
- Define how the shell gate consumes and extends the 91A/91B/91C permission broker and hard-block registry
- Define command classification categories, decision semantics, and audit model
- Define trust boundaries between actors (human, agent, PCAE broker, shell gate, git, backends)
- Define fail-closed behavior, degraded-mode behavior, and no-go conditions
- Define test strategy for future 93B prototype
- Define go/no-go criteria that must be satisfied before 93B prototype begins
- Define relationship to 92-series phase reports and notifications

Out of scope (not in this phase):

- Implementing shell interception, shell wrappers, command mediation, or any command execution path
- Modifying shell configuration (.bashrc, .zshrc, shell hooks, PROMPT_COMMAND)
- Executing requested command text, invoking backends, sending prompts
- Capturing outputs, performing intake/adoption
- Granting real authorization or real enforcement
- Telegram inbound command reception, remote shell, /run
- Modifying existing shell gate classifier (88P, 88Q, 89A) behavior
- Persisting shell-gate state or audit records to disk
- Implementing any code in src/ or tests/

### 1.3 Non-Goals

93A must not and does not:

- Implement shell interception
- Implement shell wrappers
- Implement command mediation
- Implement backend invocation
- Implement real enforcement
- Implement Telegram inbound control
- Implement remote shell
- Implement /run
- Implement any command execution path
- Modify shell configuration files
- Install shell hooks or wrappers
- Change existing shell gate classifier behavior
- Change existing permission broker behavior
- Add new CLI commands
- Write any source code, test code, or configuration files other than this design document

---

## 2. Why Shell Gate Is Needed

### 2.1 The Gap: Runtime Permission vs PCAE Governance

Claude Code and other AI coding agents have their own permission systems (allow/deny/ask). These runtime permissions control whether an agent may propose a tool call or shell command. However, runtime permission is **not the same** as PCAE governance approval:

| Dimension | Runtime Permission | PCAE Governance |
|-----------|-------------------|-----------------|
| **Scope** | Per-tool-call | Per-task-contract, per-phase |
| **Evidence** | User click (allow/deny) | Health, check, task contract, broker decision, audit |
| **Hard blocks** | Not present | 12 non-overridable hard blocks (88V §16) |
| **Audit** | Not present | Full audit payload per decision |
| **State awareness** | Session only | Task lifecycle, repo state, enforcement readiness |
| **Policy** | Agent-defined | PCAE-defined, repository-scoped, non-overridable |

An agent with `allowed` permission can run `git push --force` or `rm -rf` directly in the shell. The agent's runtime permission system does not know about PCAE hard blocks, task contracts, or governance state. **PCAE needs a gate between agent intention and shell execution** — a gate that checks the permission broker, hard-block registry, task scope, and lifecycle state before a command reaches the shell.

### 2.2 What the Shell Gate Must Preserve

The shell gate is the last classification and gating point before a command executes. It must preserve:

1. **Task scope** — Is the command consistent with the active task contract?
2. **Lifecycle state** — Is the repository in a state where this command is appropriate?
3. **Broker decision** — What does the permission broker say about this action?
4. **Hard blocks** — Is this command in the non-overridable hard-block registry?
5. **Audit evidence** — Is every gating decision traceable and auditable?
6. **Fail-closed behavior** — Does uncertainty produce a block, not an allow?

### 2.3 Design Principle

The shell gate **classifies and gates**. It does not execute, intercept, wrap, or modify the shell. In Production v1, the shell gate is an **explicit PCAE-mediated check** — the operator or agent asks PCAE "would this command be allowed?" and PCAE answers. The command itself is still typed and executed by the operator in their own shell. The gate is a governance checkpoint, not a shell replacement.

---

## 3. Narrow Production v1 Shell-Gate Surface

### 3.1 Surface Definition

The narrow Production v1 shell-gate surface is the set of command classes the shell gate must classify, decide on, and produce audit evidence for. This surface is deliberately **minimal** — it covers only the commands that pose the highest governance risk. Commands not in this surface pass through without PCAE mediation (the operator runs them directly).

### 3.2 Command Classes in the Narrow Surface

| # | Command Class | Detection Trigger | Shell Gate Decision | Hard Block? |
|---|--------------|-------------------|---------------------|-------------|
| 1 | `raw_git_commit` | `git commit` (not via `pcae commit`) | `blocked_by_raw_git_commit` | Yes |
| 2 | `raw_git_push` | `git push` (not via `pcae push`) | `blocked_by_raw_git_push` | Yes |
| 3 | `force_push` | `git push --force`, `-f`, `--force-with-lease`, `+refspec`, `--delete` | `blocked_by_force_push` | Yes |
| 4 | `no_verify` | `--no-verify`, `-n`, `--no-gpg-sign` on git commit/push | `blocked_by_no_verify` | Yes |
| 5 | `destructive_filesystem` | `rm -rf`, `git clean -fdx`, `:(){:\|:&};:` (fork bomb), `dd if=... of=...` destructive writes, `mkfs.*`, `chmod -R 777 /` | `blocked_by_destructive_filesystem` | Yes |
| 6 | `backend_invocation` | `claude`, `claude-code`, `deepseek`, `kimi`, `codex`, `copilot`, `cursor` CLI invocations, `anthropic.*` API calls, any AI backend SDK call pattern | `requires_human_review` | No (gated) |
| 7 | `unknown` | Command cannot be parsed, is ambiguous, or has no matching classification | `blocked_by_unknown_command_class` | Yes |
| 8 | `out_of_scope_mutation` | Write/mutation to files outside active task contract scope | `blocked_by_out_of_scope` | Yes |
| 9 | `forbidden_path` | Write/mutation to policy-forbidden files (README.md, docs/REAL_CAPTURED_TASKS.md, docs/LINKEDIN_ARTICLE_DRAFT.md) or task-forbidden paths | `blocked_by_forbidden_path` | Yes |
| 10 | `missing_active_task` | Mutating command with no active task contract present | `blocked_by_missing_task` | Yes |

### 3.3 Commands Explicitly NOT in the Narrow Surface

The following command classes are explicitly excluded from the narrow Production v1 shell-gate surface. They pass through to the operator's shell without PCAE mediation:

- `read_only_inspection` — `git status`, `git log`, `git diff`, `ls`, `cat`, `grep`, `find` (read-only)
- `governed_pcae_command` — `pcae health`, `pcae check`, `pcae commit`, `pcae push`, `pcae phase ...` (already governed)
- `test_execution` — `python -m pytest ...`, `pytest ...` (operator-controlled)
- `file_mutation_in_scope` — Write to files within the active task's allowed scope
- `environment_setup` — `export`, `source venv/bin/activate`, `pip install`
- `network_read` — `curl`, `wget` (read-only network access)
- `build_tool` — `make`, `cargo build`, `npm run build`, `poetry install`

Rationale: The narrow surface targets **the highest-risk commands** (force push, destructive fs, raw git operations, unauthorized backend calls). Broadening the surface before these are proven stable would risk operator friction and false positives. The surface can be expanded in future phases after the narrow prototype is validated.

### 3.4 Classification Flow

```
Raw command text
       │
       ▼
┌─────────────────────┐
│  Parse & Normalize  │  Split compound commands (&&, ||, ;, |)
│  (pure string ops)  │  Extract sub-commands, flags, paths
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Classify           │  Map to known command class
│  (rule-based)       │  Detect patterns: git push --force, rm -rf, etc.
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Hard-Block Check   │  Is the command class in HARD_BLOCK_COMMAND_CLASSES?
│  (registry lookup)  │  → Yes: deny immediately, non-overridable
└──────────┬──────────┘
           │ (not hard-blocked)
           ▼
┌─────────────────────┐
│  Scope Preflight    │  Are affected paths in task scope?
│  (task contract)    │  → No: blocked_by_scope
└──────────┬──────────┘
           │ (in scope or read-only)
           ▼
┌─────────────────────┐
│  Broker Evaluation  │  Consume health/check/task/human factors
│  (decision agg)     │  → allow_preflight_only / requires_human_review / ...
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Audit Payload      │  Build audit evidence (command, class, decision, ...)
│  (no disk write)    │  Return structured result
└─────────────────────┘
```

---

## 4. Explicit Non-Goals

The following capabilities are explicitly **not** part of the Production v1 shell gate, not designed in this phase, and not to be implemented in 93B:

1. **No global shell replacement** — PCAE does not replace bash/zsh/sh. The operator always has direct shell access.
2. **No unrestricted wrapper** — PCAE does not wrap every shell command. Only commands in the narrow surface are classified.
3. **No remote shell** — PCAE does not provide remote shell access, SSH tunneling, or web terminal.
4. **No Telegram command gateway** — Telegram remains outbound-only. No `/run`, `/commit`, `/push`, or shell commands from Telegram.
5. **No /run** — No PCAE-mediated execution shortcut. Commands are typed by the operator in their shell.
6. **No backend runner** — PCAE does not invoke AI backends. Backend invocation is detected and gated, not performed.
7. **No autonomous execution** — PCAE never executes commands autonomously. Every command is operator-initiated.
8. **No full enforcement in this phase** — 93A is design-only. 93B will be simulation-only. Real enforcement requires all 89J readiness gates.
9. **No bypass of human terminal permissions** — The operator's terminal permissions (sudo, file access) are respected. PCAE adds governance, not OS-level restrictions.
10. **No weakening of PCAE governed commit/push lifecycle** — `pcae commit` and `pcae push` remain the only governed paths for commits and pushes.

---

## 5. Shell-Gate Actors and Trust Boundaries

### 5.1 Actor Model

| Actor | Role | Trust Level | Shell Gate Interaction |
|-------|------|-------------|----------------------|
| **Human operator** | Authoritative decision-maker. Types commands, approves/rejects gated actions. | Full trust (human authority is absolute) | Receives shell gate advisory decisions. May override non-hard-block decisions. May run commands directly in shell regardless. |
| **Claude / DeepSeek / Kimi / Codex / other AI agents** | Proposes commands, generates code, suggests actions. | Untrusted for execution | Commands proposed by agents are classified by the shell gate. Agents do not bypass the gate. Agent runtime permission is not PCAE governance. |
| **PCAE broker** | Aggregates governance evidence, produces permission decisions. Simulation-only. | Trusted (PCAE internal) | Provides hard-block registry, broker decisions, reason codes, audit payloads to the shell gate. |
| **Shell gate** | Classifies command text, checks hard blocks, evaluates scope, produces gating decisions. Design-only in 93A. | Trusted (PCAE internal) | The classification and gating point. Consumes broker evidence. Produces structured decisions and audit evidence. |
| **Governed PCAE CLI** | `pcae commit`, `pcae push`, `pcae phase ...` — already governed commands. | Trusted (PCAE internal) | Pass through shell gate as `governed_pcae_command` class. Already has its own governance path. |
| **Git** | Version control system. Target of git commands (commit, push, force push). | External — commands gated | Raw git commands are classified and potentially blocked. Governed git operations use `pcae commit`/`pcae push`. |
| **Backend agents** | Claude API, DeepSeek API, etc. AI model providers. | External — invocation gated | Backend invocation commands are classified as `backend_invocation` → `requires_human_review`. |
| **Notification/reporting layer** | Phase reports (92A), notification dispatcher (92B/92C/92D). | Trusted (PCAE internal) | Shell-gate decisions are reportable. Notification failures must never weaken hard blocks. |

### 5.2 Trust Boundaries

```
┌──────────────────────────────────────────────────────────────────────┐
│                        HUMAN OPERATOR (trusted, authoritative)        │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  SHELL (bash/zsh/sh) — operator types commands directly       │    │
│  │  PCAE never intercepts, never wraps, never replaces.         │    │
│  └──────────────────────────────────────────────────────────────┘    │
│         │                                                             │
│         │ Command text (operator-initiated, read-only inspection)     │
│         ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  SHELL GATE (classifier + gating point)  ← THIS PHASE (93A)  │    │
│  │  _classify_and_gate(command_text, task_contract, repo_state) │    │
│  │                                                               │    │
│  │  ┌─────────────────────────────────────────────────────────┐ │    │
│  │  │  1. Parse & normalize command (pure string ops)         │ │    │
│  │  │  2. Classify into narrow surface command class          │ │    │
│  │  │  3. Check hard-block registry → deny immediately        │ │    │
│  │  │  4. Check scope preflight (task contract)               │ │    │
│  │  │  5. Evaluate via permission broker                       │ │    │
│  │  │  6. Build audit payload                                  │ │    │
│  │  │  7. Return structured decision + audit evidence          │ │    │
│  │  └─────────────────────────────────────────────────────────┘ │    │
│  │                                                               │    │
│  │  BOUNDARY: classification + gating only                       │    │
│  │  Never executes. Never intercepts. Never wraps.               │    │
│  └───────────────────┬──────────────────────────────────────────┘    │
│                       │                                              │
│         ┌─────────────┼─────────────┐                                │
│         ▼             ▼             ▼                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐                       │
│  │ Broker   │  │ Hard-    │  │ Scope        │                       │
│  │ (91A)    │  │ Block    │  │ Preflight    │                       │
│  │          │  │ Registry │  │              │                       │
│  │ Decision │  │ (91C)    │  │ Task scope   │                       │
│  │ agg      │  │ 12 blocks│  │ validation   │                       │
│  └──────────┘  └──────────┘  └──────────────┘                       │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  AUDIT EVIDENCE (no disk write in 93A, defined for 93B+)     │    │
│  │  command, class, decision, hard_block, reason, timestamp     │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  REPORT/NOTIFICATION LAYER (92A–92D)                         │    │
│  │  Shell-gate decisions are reportable. Notification failures   │    │
│  │  never weaken hard blocks. Telegram outbound only.           │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 6. Relationship to Permission Broker

### 6.1 How the Shell Gate Uses the Broker

The shell gate is a **consumer** of the permission broker, not a replacement. The broker remains the central governance decision authority. The shell gate adds command classification and narrow-surface gating — it extends the broker's reach to raw shell commands.

```
Command text → Shell Gate (classify) → Broker (decide) → Shell Gate (gate)
                                                              │
                                              ┌───────────────┼───────────────┐
                                              ▼               ▼               ▼
                                            allow          deny         human_review
                                         (preflight    (hard block    (operator must
                                          only)         or policy)      approve)
```

### 6.2 Specific Integration Points

| Integration Point | Broker Function | Shell Gate Usage |
|-------------------|----------------|-----------------|
| **Hard-block check** | `HARD_BLOCK_REGISTRY` (91C) | Shell gate checks command class against registry first — before any other evaluation. Hard-block → deny immediately. |
| **Decision evaluation** | `evaluate_permission_broker()` (91A) | Shell gate calls broker with action_type, command_class, paths, task state. Receives allow/deny/human_review/more_evidence. |
| **Reason codes** | Broker's 24 reason codes + 91B explanation registry | Shell gate surfaces the broker's reason codes to the operator. "Why was this blocked?" → broker reason code → explanation. |
| **Audit payload** | Broker's audit_payload dict | Shell gate extends the broker audit payload with command text, working directory, actor/source, and matched paths. |
| **Hard-block invariant** | 88V §16 permanent invariant | Shell gate enforces: hard_block=true → deny, overridable=false, permanent=true. Human approval and accepted risk are refused at the shell gate level. |
| **More evidence** | Broker returns `more_evidence` with `required_evidence` list | Shell gate surfaces "I need X, Y, Z before I can evaluate this command" to the operator. |
| **Human review** | Broker returns `human_review` | Shell gate surfaces "This command requires human review. Provide approval to proceed." |

### 6.3 What the Shell Gate Adds Beyond the Broker

| Capability | Broker (91A) | Shell Gate (93A design) |
|-----------|-------------|------------------------|
| Command text parsing | No (takes action_type/command_class as input) | Yes (parses raw command text) |
| Compound command splitting | No | Yes (splits `cmd1 && cmd2`, evaluates each) |
| Path extraction from command | No | Yes (extracts file paths from command text) |
| Working directory awareness | No | Yes (command paths are relative to cwd) |
| Actor/source tracking | No | Yes (human vs agent, session id) |
| Narrow-surface gating | No (evaluates all action types) | Yes (only classifies narrow-surface commands; others pass through) |

---

## 7. Proposed Future Command Classification Model

### 7.1 Command Classes

The shell gate classifies every command in the narrow surface into one of the following classes:

| # | Command Class | Category | Description | Shell Gate Decision |
|---|--------------|----------|-------------|---------------------|
| 1 | `governed_pcae_command` | Safe | `pcae health`, `pcae check`, `pcae commit`, `pcae push`, `pcae phase ...` | `allow_governed` — already governed, passes through |
| 2 | `read_only_inspection` | Safe | `git status`, `git log`, `git diff`, `ls`, `cat`, `grep`, `find` (read-only) | `allow_read_only` — read-only, no governance risk |
| 3 | `raw_git_commit` | Hard block | `git commit` not via `pcae commit` | `blocked_by_raw_git_commit` — hard block, non-overridable |
| 4 | `raw_git_push` | Hard block | `git push` not via `pcae push` | `blocked_by_raw_git_push` — hard block, non-overridable |
| 5 | `force_push` | Hard block | `git push --force`, `-f`, `--force-with-lease`, `+refspec`, `--delete` | `blocked_by_force_push` — hard block, permanent |
| 6 | `no_verify` | Hard block | `--no-verify`, `-n` on git commit/push | `blocked_by_no_verify` — hard block, non-overridable |
| 7 | `destructive_filesystem` | Hard block | `rm -rf`, `git clean -fdx`, fork bombs, destructive writes | `blocked_by_destructive_filesystem` — hard block, permanent |
| 8 | `backend_invocation` | Gated | `claude`, `deepseek`, `kimi`, `codex`, AI API calls | `requires_human_review` — not hard block, gated |
| 9 | `file_mutation` | Conditional | Write/edit to files | Requires scope preflight. In-scope → allow. Out-of-scope → blocked_by_scope. |
| 10 | `unknown` | Hard block | Unparseable, ambiguous, no matching class | `blocked_by_unknown_command_class` — hard block, fail-closed |

### 7.2 Classification Rules (Conceptual)

The classification is rule-based (pure string analysis, no subprocess execution):

1. **First character check**: If the command starts with `pcae `, classify as `governed_pcae_command`.
2. **Git command detection**: Parse `git <subcommand>` patterns. Map `commit` → `raw_git_commit`, `push` → check for force flags → `force_push` or `raw_git_push`.
3. **Force flag detection**: Scan for `--force`, `-f`, `--force-with-lease`, `+<refspec>`, `--delete` in git push context.
4. **No-verify detection**: Scan for `--no-verify`, `-n`, `--no-gpg-sign` in git commit/push context.
5. **Destructive pattern detection**: Match `rm -rf`, `git clean -fdx`, `:(){ :|:& };:`, `dd if=... of=/dev/...`, `mkfs.*`, `chmod -R 777 /`.
6. **Backend invocation detection**: Match known AI CLI tool names (`claude`, `claude-code`, `deepseek`, `kimi`, `codex`, `copilot`, `cursor`) and API call patterns.
7. **Path extraction**: Extract file paths from command arguments. Match against task scope.
8. **Fallback**: If no rule matches and the command is mutating (contains write/create/delete patterns), classify as `file_mutation`. If command cannot be parsed at all, classify as `unknown`.

### 7.3 Compound Command Handling

Compound commands (`&&`, `||`, `;`, `|`) are split into sub-commands. Each sub-command is classified independently. If any sub-command is a hard block, the entire compound command is blocked.

```
Input:  git status && git push --force origin main
Split:  ["git status", "git push --force origin main"]
Class:  read_only_inspection, force_push
Result: blocked_by_force_push (hard block from sub-command 2)
```

This matches the existing 89A compound command splitting behavior.

---

## 8. Decision Semantics

### 8.1 Decision Outcomes

The shell gate produces one of four gating decisions:

| Decision | Meaning | Operator Action | Overridable? |
|----------|---------|----------------|-------------|
| **allow** | Command passes governance checks. Operator may proceed. | Run command in shell. | N/A (allowed) |
| **deny** | Command is blocked by hard block or policy. Permanent. | Use governed alternative (e.g., `pcae commit` instead of `git commit`). | **No** — hard blocks are non-overridable (88V §16) |
| **human_review** | Command requires human review before proceeding. Not a hard block. | Provide approval evidence. Shell gate re-evaluates. | Yes — with valid, fresh approval |
| **more_evidence** | Insufficient evidence to decide. Shell gate cannot evaluate. | Provide missing evidence (task contract, health check, etc.) and re-submit. | N/A (insufficient to decide) |

### 8.2 Hard Block = True Behavior

When `hard_block=true`:

| Property | Value | Enforced By |
|----------|-------|------------|
| Overridable | `false` | Shell gate refuses all override attempts |
| Human approval can override | `false` | Shell gate rejects approval when hard_block=true |
| Accepted risk can override | `false` | Shell gate rejects accepted risk when hard_block=true |
| Operator override | `false` | No operator flag can bypass a hard block |
| Permanent | `true` | Hard blocks do not expire |
| Audit required | `true` | Every hard block decision is auditable |

### 8.3 Allow Semantics

`allow` means: "This command passes all PCAE governance checks. You may proceed to run it in your shell. PCAE does not execute the command and does not authorize execution. You retain full authority and responsibility."

`allow` never means: "PCAE authorizes execution" or "PCAE guarantees safety." The operator always has the final say.

### 8.4 Fail-Closed Behavior

When the shell gate cannot reach a confident decision:

| Condition | Decision | Reason |
|-----------|----------|--------|
| Command cannot be parsed | `deny` (hard_block=true) | `blocked_by_unknown_command_class` — fail-closed |
| Command class ambiguous | `deny` (hard_block=true) | `blocked_by_unknown_command_class` — fail-closed |
| Task contract missing for mutating command | `deny` (hard_block=true) | `blocked_by_missing_task` |
| Task scope unknown for mutating command | `more_evidence` | `task_scope_unknown` — request scope definition |
| Broker unavailable (future) | `deny` (hard_block=true) | `blocked_by_conflicting_evidence` — cannot evaluate without broker |
| Health/check unavailable (future) | `more_evidence` | `missing_governance_evidence` — request evidence |
| Repo cannot be inspected | `more_evidence` | `repo_not_inspectable` — request repo access |

**The fail-closed principle is absolute**: uncertainty, missing evidence, or internal error → block, never allow.

---

## 9. Hard-Block Invariant

### 9.1 Permanent Invariant (88V §16)

The hard-block invariant from 88V §16 is the **foundation** of the shell gate design:

```
Accepted risk MUST NOT override hard blocks.
Human approval MUST NOT override hard blocks.
No operator, administrator, or automated system MAY override hard blocks.
This is a permanent, non-negotiable safety invariant.
```

### 9.2 Explicit Preservation in the Shell Gate

The shell gate design preserves this invariant through multiple redundant checks:

1. **Classification-time check**: Hard-block command classes (`raw_git_commit`, `raw_git_push`, `force_push`, `no_verify`, `destructive_filesystem`, `unknown`) are checked **first**, before any evidence is evaluated. A hard-block classification → `deny` immediately, with no further evaluation.

2. **Broker integration check**: The shell gate calls `evaluate_permission_broker()` which independently checks hard blocks at step 1 of its decision priority chain. Even if the shell gate classification fails, the broker catches hard blocks.

3. **Override refusal**: Any code path that applies human approval or accepted risk must first check `hard_block_present`. If true, the approval/risk is refused without further processing. This check exists in three places: shell gate gating logic, broker decision logic (91A), and hard-block registry validation (91C).

4. **Registry validation**: `validate_hard_block_registry()` (91C) verifies that every hard block has `override_allowed=False`, `approval_can_override=False`, `accepted_risk_can_override=False`. The shell gate must call this validation on initialization and refuse to operate if the registry is invalid.

### 9.3 What Cannot Override Hard Blocks (Exhaustive List)

| Override Attempt | Blocked By | Mechanism |
|-----------------|-----------|-----------|
| Human approval present + hard block | Shell gate + Broker | Both refuse to apply approval when hard_block_present=true |
| Accepted risk present + hard block | Shell gate + Broker | Both refuse to apply risk when hard_block_present=true |
| Human approval + accepted risk together + hard block | Shell gate + Broker | Neither can override; combination irrelevant |
| Telegram/mobile approval request + hard block | Shell gate (future) | Source of approval does not change hard-block status |
| Stale approval + hard block | Shell gate + Broker | Stale approval is invalid regardless; hard block stands independently |
| "I know what I'm doing" / operator insistence + hard block | Shell gate | No operator flag can bypass a hard block |
| Convenience argument ("just this once") + hard block | Shell gate | Hard blocks are permanent, not situational |
| "Emergency" without documented emergency procedure + hard block | Shell gate | Emergency override requires a separate, audited emergency procedure (not designed in 93A) |

---

## 10. Audit Model

### 10.1 Required Audit Evidence Fields

Every shell-gate decision must produce an audit payload with the following fields:

| # | Field | Type | Description |
|---|-------|------|-------------|
| 1 | `event_id` | str | Unique event identifier (`sg-<uuid12>`) |
| 2 | `event_type` | str | `shell_gate.classified`, `shell_gate.allowed`, `shell_gate.blocked`, `shell_gate.gated_review`, `shell_gate.insufficient_evidence` |
| 3 | `attempted_command` | str | The raw command text as provided (redacted if secrets detected) |
| 4 | `attempted_command_hash` | str | SHA-256 hash of the raw command text |
| 5 | `command_text_redacted` | bool | True if secrets were detected and command text was redacted |
| 6 | `normalized_command_class` | str | The classified command class (from §7.1) |
| 7 | `working_directory` | str | The working directory where the command was proposed |
| 8 | `actor_source` | str | `human_operator`, `claude_agent`, `deepseek_agent`, `kimi_agent`, `codex_agent`, `unknown_agent` |
| 9 | `active_task_id` | str\|null | The active task contract ID, or null if none |
| 10 | `matched_paths` | list[str] | File paths extracted from the command text |
| 11 | `broker_decision` | str | The broker's decision (allow/deny/human_review/more_evidence) |
| 12 | `shell_gate_decision` | str | The shell gate's gating decision (allow/deny/human_review/more_evidence) |
| 13 | `reason_code` | str | Primary machine-readable reason code |
| 14 | `reason_codes` | list[str] | All reason codes |
| 15 | `hard_block_status` | bool | Whether a hard block was triggered |
| 16 | `hard_block_reason` | str\|null | If hard_block_status=true, the specific hard block reason code |
| 17 | `overridable` | bool | Whether the decision can be overridden (always false for hard blocks) |
| 18 | `timestamp` | str | ISO 8601 timestamp with timezone |
| 19 | `policy_version` | str | Shell gate policy version (schema version) |
| 20 | `report_artifact_reference` | str\|null | Reference to the phase report artifact if reporting is active |
| 21 | `notification_result_reference` | str\|null | Reference to the notification result if notification is active |

### 10.2 Audit Evidence — No Disk Write in 93A/93B

In the 93B prototype (simulation-only), the audit payload is produced in memory and returned as structured output. It is not written to disk, not persisted, and not part of an audit chain. Disk-based audit logging belongs to a future enforcement phase after the 89J readiness gates are satisfied.

### 10.3 Audit Evidence Shape (Example)

```json
{
  "event_id": "sg-a1b2c3d4e5f6",
  "event_type": "shell_gate.blocked",
  "attempted_command": "git push --force origin main",
  "attempted_command_hash": "sha256:abc123...",
  "command_text_redacted": false,
  "normalized_command_class": "force_push",
  "working_directory": "/Users/operator/repos/pcae-harness",
  "actor_source": "claude_agent",
  "active_task_id": null,
  "matched_paths": [],
  "broker_decision": "deny",
  "shell_gate_decision": "deny",
  "reason_code": "blocked_by_force_push",
  "reason_codes": ["blocked_by_force_push"],
  "hard_block_status": true,
  "hard_block_reason": "blocked_by_force_push",
  "overridable": false,
  "timestamp": "2026-06-29T12:00:00.000000+00:00",
  "policy_version": "1.0",
  "report_artifact_reference": null,
  "notification_result_reference": null
}
```

### 10.4 Secret Redaction in Audit Evidence

When the shell gate detects secrets in command text (e.g., `OPENAI_API_KEY=sk-...`), the `attempted_command` field is set to `<redacted_secret_access_command>` and `command_text_redacted` is set to `true`. The `attempted_command_hash` stores the SHA-256 hash of the original (unredacted) command text for integrity verification without exposing the secret. This matches the existing 88V.1 secret redaction behavior.

---

## 11. Failure and Degraded-Mode Behavior

### 11.1 Fail-Closed Principle

**Any failure, uncertainty, missing evidence, contradiction, or internal error must result in blocking the command — never allowing it.**

### 11.2 Failure Mode Catalog

| # | Failure | Detection | Shell Gate Behavior |
|---|---------|-----------|-------------------|
| F1 | Command cannot be parsed | Parser returns no tokens or raises | `deny`, `blocked_by_unknown_command_class`, hard_block=true |
| F2 | Command class ambiguous | Multiple conflicting classifications | `deny`, `blocked_by_unknown_command_class`, hard_block=true |
| F3 | Repo cannot be inspected | Not a git repo, no .pcae directory, permission denied | `more_evidence`, "cannot inspect repository state" |
| F4 | Active task cannot be read | Task contract file missing, corrupted, or unreadable | `more_evidence` for read-only; `deny` (`blocked_by_missing_task`) for mutating |
| F5 | Broker unavailable | `evaluate_permission_broker()` raises or returns error | `deny`, `blocked_by_conflicting_evidence`, hard_block=true |
| F6 | Hard-block registry invalid | `validate_hard_block_registry()` returns issues | Shell gate refuses to operate. Return error. |
| F7 | Audit evidence cannot be built | Internal error during audit payload construction | `deny`, `blocked_by_conflicting_evidence`, hard_block=true |
| F8 | Notification unavailable (future) | Notification dispatch fails | Shell-gate decision stands. Notification failure is non-fatal. |
| F9 | Config missing | Shell gate policy config file missing | Use built-in defaults (narrow surface defined in code). Operate in safe-default mode. |
| F10 | Policy version mismatch | Shell gate expects v1 but config says v2 | `deny`, `blocked_by_conflicting_evidence`, hard_block=true |

### 11.3 Degraded Mode (Future)

When the shell gate cannot operate with full integrity (audit chain broken, broker unavailable, registry invalid), it degrades to the safest possible behavior:

1. **All commands in the narrow surface are blocked** — `deny` with `hard_block=true`.
2. **Commands outside the narrow surface are unaffected** — operator runs them directly.
3. **Audit events are still produced** (best-effort) for the degradation itself.
4. **Operator is notified**: "Shell gate degraded: all narrow-surface commands are blocked until integrity is restored."
5. **Recovery**: Operator runs `pcae shell-gate recover` (future CLI) after repairing the underlying issue.

This matches the enforcement degraded-mode pattern from 90A §25.

---

## 12. Future Implementation Options

### 12.1 Comparison of Possible Designs

| Design | Description | Safety | Complexity | Production v1 Fit |
|--------|------------|--------|-----------|------------------|
| **A. Explicit PCAE-mediated check** | `pcae shell-gate check --command "..."` — operator/agent explicitly asks PCAE to classify and gate a command before running it. PCAE returns a decision. Operator then runs the command (or not) in their own shell. | Highest. No interception. No wrapping. Explicit opt-in. | Low. A single CLI command. | **Recommended for 93B.** |
| **B. Opt-in shell wrapper** | Operator sources a PCAE wrapper script that hooks into the shell's pre-execution hook. Commands are classified before execution. | Medium. Wrapper introduces shell configuration dependency. Risk of wrapper bypass. | Medium. Requires shell-specific hooks (bash, zsh). | Deferred. Requires shell integration maturity. |
| **C. Git hook augmentation** | PCAE installs git pre-commit and pre-push hooks that call the shell gate. Only git commands are gated. | Medium-high. Limited to git. No general shell mediation. | Low. Standard git hooks. | Possible complement to A, but not a replacement. |
| **D. Terminal integration** | PCAE integrates with terminal emulators (iTerm2, VS Code terminal) to intercept commands before execution. | Low. Terminal-specific. Many bypass vectors. High complexity. | High. Terminal-specific APIs. | Not for Production v1. |
| **E. Agent-specific mediation** | PCAE provides an MCP tool or agent SDK that agents must call before proposing shell commands. | Medium. Only works for agents that integrate. Human bypass trivial. | Medium. SDK maintenance burden. | Future complement. Depends on agent ecosystem maturity. |

### 12.2 Recommended Production v1 Prototype Path

**Design A — Explicit PCAE-mediated shell-gate check** — is the recommended path for 93B.

Rationale:

1. **Safest**: No shell interception, no wrappers, no automatic gating. The operator explicitly asks PCAE for a governance decision.
2. **Simplest**: A single CLI command. No shell configuration changes. No persistent state.
3. **Proven pattern**: Matches the existing `pcae permission-broker check` CLI (91B). The shell gate extends this with command text parsing and narrow-surface classification.
4. **Operator retains full control**: PCAE never blocks the operator from running commands directly. The gate is advisory in 93B (simulation-only).
5. **Testable**: CLI input/output is deterministic and testable without shell integration.
6. **Incremental**: Design A can be extended with Design C (git hooks) and Design B (opt-in wrapper) in future phases.

### 12.3 Explicit Non-Goals for Production v1

- No global shell wrapper (Design B)
- No automatic interception (Design D)
- No agent-specific mediation requirement (Design E)
- Git hook augmentation (Design C) may be considered as a complement after 93B is stable, but is not required for Production v1

### 12.4 Recommended CLI Surface for 93B

```
pcae shell-gate check --command "<command>" [--json]
pcae shell-gate status [--json]
pcae shell-gate explain --reason-code <code> [--json]
```

These mirror the existing `pcae permission-broker check/status/explain` pattern (91B) for consistency.

---

## 13. Test Strategy for Future 93B

### 13.1 Test Categories

| # | Category | Tests | Description |
|---|----------|-------|-------------|
| 1 | **Command classification** | ~30 | Verify correct classification of each command class in §7.1, including edge cases (compound commands, flags, paths) |
| 2 | **Hard-block mapping** | ~12 | Verify each hard-block command class maps to the correct hard-block reason code from the registry |
| 3 | **Broker integration** | ~15 | Verify shell gate correctly calls `evaluate_permission_broker()` with extracted action_type, command_class, paths, and task state |
| 4 | **Audit payload generation** | ~10 | Verify every decision produces a complete audit payload with all 21 fields |
| 5 | **Fail-closed behavior** | ~12 | Verify each failure mode in §11.2 produces the correct decision (deny or more_evidence, never allow) |
| 6 | **No execution guarantee** | ~5 | Verify the shell gate never executes commands, never shells out, never invokes subprocess for classification |
| 7 | **CLI check output** | ~10 | Verify `pcae shell-gate check --command "..."` produces correct human-readable and JSON output |
| 8 | **JSON output** | ~8 | Verify `--json` flag produces valid JSON with all required fields and stable schema |
| 9 | **No global interception** | ~3 | Verify no shell hooks, wrappers, or configuration files are installed |
| 10 | **Hard-block non-overridability** | ~18 | Verify all 12 hard blocks cannot be overridden by approval, accepted risk, or operator flags |
| 11 | **Compound command handling** | ~8 | Verify compound commands (&&, ||, ;, \|) are split and each sub-command evaluated; hard block in any sub-command blocks all |
| 12 | **Secret redaction** | ~5 | Verify commands with secrets (API keys, tokens) are redacted in audit output and human output |
| 13 | **Scope preflight integration** | ~10 | Verify path extraction from command text and scope validation against task contract |
| 14 | **Regression — broker** | All existing | Verify no regression in existing broker tests (265 tests after 92D.1) |
| 15 | **Regression — fast-green** | All existing | Verify no regression in fast-green (3305 tests after 92D.1) |

**Estimated new tests: ~146**

### 13.2 Test Principles for 93B

1. **No command execution in tests** — Tests provide command text as strings. The shell gate classifies but never executes.
2. **No shell integration in tests** — Tests call `classify_and_gate()` directly or via CLI subprocess. No shell hooks, wrappers, or configuration.
3. **Deterministic classification** — Same command text always produces the same classification. No randomness, no ML, no external API calls.
4. **Isolated repo fixtures** — Tests use temp directories with synthetic task contracts, not the live PCAE repo.
5. **All invariants verified** — Every test that produces a hard block must verify `overridable=false`, `hard_block=true`, `permanent=true`.
6. **Simulation-only assertion** — Every test output must include `simulation_only=true` or equivalent assertion.

---

## 14. Relationship to Reports and Notifications

### 14.1 Shell-Gate Decisions as Reportable Events

Shell-gate decisions should later be reportable through the 92A phase report artifact model and 92B/92C/92D notification foundation:

- **Phase reports (92A)**: A phase that includes shell-gate development work may reference shell-gate decisions in its phase report.
- **Notification events (92B)**: Shell-gate decisions (especially `deny` with `hard_block=true`) can be converted to `NotificationEvent` objects for dispatch.
- **Telegram outbound (92C)**: In future phases, critical shell-gate blocks (e.g., attempted force push) could be reported to the operator via Telegram. This is **outbound only** — the operator receives a notification; the operator does not send commands back.

### 14.2 Invariant: Notification Failures Must Never Weaken Hard Blocks

This is a permanent invariant carried forward from 92D:

- Shell-gate decisions are made **before** notification is attempted.
- If notification fails (Telegram API error, network error, sink failure), the shell-gate decision stands unchanged.
- A notification failure does not downgrade a `deny` to an `allow`, does not make a hard block overridable, and does not change any decision property.
- The operator is informed: "Shell gate decision: deny. Notification of this decision failed. The block stands."

### 14.3 Telegram Remains Outbound Only

Per the canonical roadmap, Telegram in Production v1 is **outbound only**. The shell gate does not accept commands from Telegram, does not process Telegram messages, and does not provide a command gateway. Telegram is one notification channel — it receives reports about shell-gate decisions; it does not influence them.

---

## 15. Go/No-Go Criteria for 93B

### 15.1 Criteria That Must Be Satisfied Before 93B Prototype

| # | Criterion | Verification |
|---|-----------|-------------|
| G1 | **93A design reviewed** | Operator has read and approved this design document |
| G2 | **Hard-block mapping complete** | All 12 hard blocks from 91C are mapped to command classes in the narrow surface |
| G3 | **Test matrix defined** | Test plan (§13) is complete with ~146 test scenarios enumerated |
| G4 | **No global interception** | Design confirms explicit PCAE-mediated check only; no shell wrappers or hooks |
| G5 | **Prototype command is explicit and non-executing** | `pcae shell-gate check --command "..."` is classified and decided; command text is never executed |
| G6 | **Fail-closed behavior defined** | All failure modes (§11) produce deny or more_evidence, never allow |
| G7 | **Hard-block invariant preserved** | Design confirms hard blocks cannot be overridden by any actor (§9) |
| G8 | **Broker integration path defined** | Design specifies how shell gate calls `evaluate_permission_broker()` (§6) |
| G9 | **Audit model defined** | All 21 audit fields enumerated (§10) |
| G10 | **Relationship to existing phases clear** | Design references 90A, 91A, 91B, 91C, 92A, 92B, 92C, 92D where relevant |
| G11 | **Full suite green** | All existing tests pass (fast-green, broker regression, report/notification regression) |
| G12 | **Active task contract exists for 93B** | Operator must create a governed task contract before implementation |
| G13 | **Operator explicitly authorizes 93B** | Human authority is absolute; implementation requires explicit approval |

### 15.2 Conditional Criteria

| # | Criterion | Required For |
|---|-----------|-------------|
| G14 | 93B task contract defines exact command surface to implement | Scope control |
| G15 | Test fixtures for command classification are prepared | Test isolation |

---

## 16. No-Go Conditions

### 16.1 Absolute Blocks on Shell-Gate Implementation

Shell-gate implementation (93B and beyond) must not start or continue if ANY of these is true:

| # | Condition | Rationale |
|---|-----------|-----------|
| **STOP-1** | Uncertainty about command classification | Fail-closed requires confident classification. If a command class cannot be reliably detected, the shell gate must not operate on that class. |
| **STOP-2** | Inability to audit decisions | Every shell-gate decision must be auditable. If audit evidence cannot be produced, the shell gate must not operate. |
| **STOP-3** | Possibility that approval overrides hard blocks | 88V §16 permanent invariant. Any code path that allows approval or accepted risk to override a hard block must be blocked. |
| **STOP-4** | Hidden command execution | The shell gate must never execute command text. If any code path executes or shells out, it must be removed. |
| **STOP-5** | Broad wrapper requirement | The shell gate must not require shell wrappers, hooks, or configuration changes to operate. Design A (explicit check) only. |
| **STOP-6** | Backend invocation ambiguity | Backend invocation detection must be clear and reliable. If "is this a backend call?" cannot be answered confidently, that command class must be deferred. |
| **STOP-7** | Incomplete task-state handling | Mutating commands require an active task contract. If task state cannot be reliably detected, mutating commands must be blocked. |
| **STOP-8** | Full suite not green | Implementation must not regress existing tests. Any regression blocks 93B. |
| **STOP-9** | Hard-block registry invalid | `validate_hard_block_registry()` must return zero issues. Any registry corruption blocks 93B. |
| **STOP-10** | Broker safety invariants not preserved | `no_execution=True`, `no_enforcement=True`, `simulation_only=True` must remain true for all broker interactions. |
| **STOP-11** | No active task contract for 93B | Ungoverned implementation is not permitted. |
| **STOP-12** | Operator has not explicitly authorized 93B | Human authority is absolute. |

### 16.2 93A-Specific No-Go Conditions

| # | Condition | Rationale |
|---|-----------|-----------|
| **93A-STOP-1** | Design document not completed with all 16 sections | Design is the authority; implementation without complete design is ungoverned |
| **93A-STOP-2** | Design does not reference 91A/91B/91C/92A/92B/92C/92D where relevant | Shell gate must integrate with existing systems |
| **93A-STOP-3** | Design does not preserve 88V §16 hard-block invariant | Permanent safety invariant |
| **93A-STOP-4** | Design does not define fail-closed behavior | Fail-open is unacceptable |

---

## 17. Summary

Phase 93A defines the narrow Production v1 shell-gate surface: the minimum set of command classes the shell gate must classify, the decisions it must produce, the hard blocks it must enforce, and the audit evidence it must generate. The design is deliberately minimal — 10 command classes, explicit PCAE-mediated check only, no shell interception or wrappers.

The shell gate extends the 91-series permission broker and hard-block registry to raw shell commands. It preserves all existing invariants (88V §16 hard-block non-overridability, fail-closed behavior, simulation-only operation). It defines the integration points with the 92-series phase reports and notifications.

**Recommended next phase: 93B — Narrow Shell Gate Prototype** (requires explicit operator approval and a governed task contract).

---

*Phase 93A is a design-only phase. No shell interception, wrappers, command mediation, backend invocation, Telegram inbound control, remote shell, /run, enforcement, or command execution path was implemented. The design is complete and ready for operator review. All 16 required sections are covered. The recommended path for 93B is an explicit PCAE-mediated shell-gate check (`pcae shell-gate check --command "..."`), simulation-only, no shell wrappers, no global interception.*
