# PCAE Runtime Governance

Runtime governance evaluates each AI runtime independently against explicit trust, contract, and readiness criteria before any invocation is attempted. Different runtimes have different sandboxing guarantees, output behaviors, and trust levels — these differences are verified systematically, not assumed.

```mermaid
flowchart TD
    RUNTIME(["Target Runtime\n─────────────────\ncodex-local\nclaude-local\nkimi-local"])

    RC["Runtime Contract\n──────────────────\nFormal contract artifact\ndeclares the runtime's:\n- Sandbox mode\n- Timeout parameters\n- Output capture format\n- Invocation mode\n- Trust level assertion\nMust exist before evaluation."]

    CV["Contract Verification\n──────────────────────\n7 blocking enforcement checks:\n✗ runtime_contract_exists\n✗ runtime_trust_acceptable\n✗ sandbox_contract_verified\n✗ timeout_contract_verified\n✗ output_capture_contract_verified\n✗ invocation_mode_matches_request\n✗ writable_execution_blocked\npcae runtime-contract-enforcement"]

    RT["Runtime Trust\n──────────────\nTrust level assessed:\n- untrusted\n- low\n- medium\n- high\nMinimum trust threshold\nmust be met. kimi-local\ncurrently: untrusted.\npcae runtime-trust"]

    RR["Runtime Readiness\n───────────────────\nAll contract checks passed.\nTrust level acceptable.\nSandbox, timeout, and\ncapture path confirmed.\nRuntime eligible for preflight.\npcae readonly-runtime-pilot"]

    RP["Runtime Pilot\n──────────────\nControlled read-only\ninvocation pilot evaluated.\n8 lifecycle gates checked.\nPilot result produced.\nAll results currently blocked.\npcae readonly-runtime-pilot"]

    REB{{"Execution\nBlocked?"}}

    BLOCKED_STATE["Runtime Execution Blocked\n──────────────────────────\nexecution_allowed=False\nhuman_review_required=True\nBlocker report produced.\nNo invocation occurs.\nCurrent state for all runtimes."]

    ELIGIBLE(["Runtime Eligible\n─────────────────\nAll gates cleared.\nexecution_allowed\nmay be set True\nby future 49A gate."])

    RUNTIME --> RC --> CV --> RT
    RT --> RR --> RP --> REB
    REB -->|"Yes (current state)"| BLOCKED_STATE
    REB -->|"No (future state)"| ELIGIBLE

    style RUNTIME fill:#2980b9,stroke:#1a5276,color:#fff
    style REB fill:#ffd700,stroke:#b8860b,color:#000
    style BLOCKED_STATE fill:#ff6b6b,stroke:#c0392b,color:#fff
    style ELIGIBLE fill:#27ae60,stroke:#1e8449,color:#fff
```

## Per-Runtime Current State

| Runtime | Trust Level | Contract | Sandbox | Execution |
|---------|-------------|----------|---------|-----------|
| codex-local | low | blocked | unverified | **blocked** |
| claude-local | low | blocked | unverified | **blocked** |
| kimi-local | untrusted | blocked | unverified | **blocked** |

All three runtimes are blocked in the current phase. This is expected and intentional. The contract and trust scaffolding must be validated before any runtime is cleared for invocation.
