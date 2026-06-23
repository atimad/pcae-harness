# Agent Identity / Backend Capability Probe

## Purpose

Perform bounded identity and availability probes for known backend commands. Record metadata without sending prompts, executing tasks, or modifying the repository through agents.

## Scope

Shell-level availability checks (`command -v`) and non-interactive metadata probes (`--version`) only. No prompts sent, no interactive sessions opened, no repository modifications by agents.

## Non-Goals

- Sending prompts to any backend.
- Running agents in task/interactive mode.
- Implementing registry code.
- Authorizing routing.
- Discovering new unknown agents.

## Probe Safety Rules

- Only `command -v` and `--version` probes were used.
- All probes had a 5-second timeout.
- No natural-language prompts were sent to any backend.
- No agent was invoked in interactive or task mode.
- No backend modified any repository file.

## Commands Probed

| Command | Availability | Path |
|---------|-------------|------|
| `claude` | available | `/Users/atilamadai/.local/bin/claude` |
| `claude-deepseek` | available | `/Users/atilamadai/.local/bin/claude-deepseek` |
| `claude-kimi` | missing | not found on PATH |
| `codex` | available | `/Users/atilamadai/.local/bin/codex` |

## Availability Results

### claude

- **Available:** yes
- **Version probe:** `2.1.186 (Claude Code)`
- **Version probe return code:** 0
- **Type:** native binary/CLI
- **Interactive risk:** high if invoked without `--print` or `--version`
- **Safe probe flags:** `--version`, `--help`, `--print`

### claude-deepseek

- **Available:** yes
- **Version probe:** `2.1.186 (Claude Code)` (same as claude — wrapper delegates to claude binary)
- **Version probe return code:** 0
- **Type:** zsh wrapper script
- **Interactive risk:** high if invoked without safe flags
- **Note:** This is a shell wrapper that configures claude to use a different model/provider. It shares the claude binary.

### claude-kimi

- **Available:** no
- **Version probe:** not attempted (command missing)
- **Status:** missing — not installed or not on PATH
- **Note:** Cannot be probed, verified, or routed until installed.

### codex

- **Available:** yes
- **Version probe:** `codex-cli 0.140.0`
- **Version probe return code:** 0
- **Type:** native CLI
- **Interactive risk:** high if invoked without safe flags
- **Note:** OpenAI Codex CLI. Separate provider from Anthropic. Capability profile not yet verified.

## Capability Inference Method

Capabilities are inferred conservatively from:

1. Command availability (exists on PATH).
2. Version probe response (responds to `--version` without entering interactive mode).
3. Known provider family (anthropic, openai, etc.).
4. Known invocation patterns from prior PCAE lifecycle phases.

Inference does NOT imply permission. All routing requires task contracts, approvals, and governance gates.

## Capability Observations

| Agent | Text Gen | Code Edit | Markdown | Task Contracts | Repo Mutation Risk |
|-------|----------|-----------|----------|----------------|--------------------|
| claude | yes (proven in 81D) | likely | yes (proven) | yes (proven) | low via `--print` |
| claude-deepseek | yes (proven in 77F) | likely | yes (proven) | yes (proven) | medium (wrapper may behave differently) |
| claude-kimi | unknown | unknown | unknown | unknown | unknown |
| codex | likely | likely | likely | unverified | high (can execute shell) |

## Safety Profile Observations

| Agent | Risk Level | Mutation Guard | Approval Required | Auto-Apply | Auto-Commit | Auto-Push |
|-------|-----------|----------------|-------------------|------------|-------------|-----------|
| claude | low | required | yes | forbidden | forbidden | forbidden |
| claude-deepseek | medium | required | yes | forbidden | forbidden | forbidden |
| claude-kimi | unknown | required | yes | forbidden | forbidden | forbidden |
| codex | high | required | yes | forbidden | forbidden | forbidden |

## Disabled / Unknown Backend Handling

- **claude-kimi:** missing from PATH. Remains disabled. Cannot be routed until installed, probed, and verified.
- **codex:** available but unverified for PCAE task contracts. Remains disabled for routing until a future capability verification phase (82D or later) establishes a safety profile.
- **Any unlisted agent:** disabled by default per registry design.

## Routing Eligibility Result

| Agent | Routing Eligible | Reason |
|-------|-----------------|--------|
| claude | not yet | Proven capable, but routing requires future dry-run/approval phase |
| claude-deepseek | not yet | Proven capable, but routing requires future dry-run/approval phase |
| claude-kimi | no | Missing from PATH |
| codex | no | Available but unverified for PCAE governance |

No agent is authorized for routing based solely on this probe. Routing authorization requires Phase 82E (Agent Routing Dry-Run) or later.

## Registry Implications

Based on this probe, a future registry implementation should initialize:

- `claude`: enabled=true, last_verified_at=2026-06-23, verification_source=82B_probe
- `claude-deepseek`: enabled=true, last_verified_at=2026-06-23, verification_source=82B_probe
- `claude-kimi`: enabled=false, last_verified_at=null, verification_source=none
- `codex`: enabled=false (pending safety profile), last_verified_at=2026-06-23, verification_source=82B_probe_availability_only

## Blockers / Warnings

**Blockers:** none for this probe phase.

**Warnings:**
- `claude-kimi` is not available and cannot be probed.
- `codex` is available but its PCAE compatibility is unverified.
- `claude-deepseek` shares the claude binary — its behavior depends on wrapper configuration.

## Safety Conclusion

- No backend prompts were sent.
- No backend task execution occurred.
- No backend output was adopted.
- No backend modified the repository.
- No backend is authorized for routing solely because of this probe.
- Missing/unknown agents remain disabled.
- Routing requires a future explicit dry-run/approval phase.

## Recommended Next Phase

**82C — Subagent Discovery Contract**

82C should formalize what information is needed to register an agent for governed routing, based on the probe findings from 82B.
