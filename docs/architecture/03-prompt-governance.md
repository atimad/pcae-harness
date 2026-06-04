# PCAE Prompt Governance

Prompt governance ensures that every prompt submitted to an AI runtime is derived from a governed roadmap, parameterized against the current task context, validated against the task contract, and explicitly approved before submission.

```mermaid
flowchart TD
    RP["Roadmap Proposal\n───────────────────\nNext phase recommended by\npcae roadmap next based on\ngovernance readiness, health,\nand provenance history.\nAdvisory — not binding."]

    RA["Roadmap Approval\n──────────────────\n👤 Human reviews and\napproves the proposed phase.\nApproved phase becomes the\nbasis for prompt generation.\nHuman decision is authoritative."]

    CP["Canonical Prompt\n──────────────────\nStructured prompt template\nfor the approved phase.\nDeclares: task scope,\nforbidden operations,\nexpected output format,\nand governance constraints."]

    AP["Agent-Specific Prompt\n──────────────────────\nCanonical prompt rendered\nfor the target runtime.\nRuntime-specific parameters\napplied: timeout, sandbox mode,\noutput capture format,\ninvocation constraints."]

    PV["Prompt Validation\n──────────────────\nRendered prompt checked\nagainst task contract:\n- No forbidden operations\n- Scope within allowed files\n- Output format declared\n- Authorization artifact present\npcae prompt-render"]

    PG["Prompt Governance\n──────────────────\nPreflight result produced.\nPrompt artifact linked to\nauthorization record.\nBlocked if any validation\ncheck fails. Blocker report\nproduced with findings."]

    PA["Prompt Approval\n─────────────────\n👤 Human reviews the\nrendered, validated prompt\nbefore submission.\nNo prompt is submitted\nwithout explicit approval.\nhuman_review_required=True"]

    SUBMIT(["Prompt Eligible\nfor Submission\n─────────────────\nexecution_allowed\nevaluated by\nexecution lifecycle"])

    BLOCKED{{"Validation\nFailed?"}}
    REPORT["Blocker Report\n───────────────\nValidation findings\nreported. Prompt\nnot submitted."]

    RP --> RA --> CP --> AP --> PV --> BLOCKED
    BLOCKED -->|"Yes"| REPORT
    BLOCKED -->|"No"| PG --> PA --> SUBMIT

    style RA fill:#2980b9,stroke:#1a5276,color:#fff
    style PA fill:#2980b9,stroke:#1a5276,color:#fff
    style BLOCKED fill:#ffd700,stroke:#b8860b,color:#000
    style REPORT fill:#ff6b6b,stroke:#c0392b,color:#fff
    style SUBMIT fill:#27ae60,stroke:#1e8449,color:#fff
```

## Governance Invariants

- No prompt is generated without an approved roadmap phase as its source.
- No prompt is rendered without the task contract being applied.
- No prompt is submitted without a passing preflight and explicit human approval.
- Prompt artifacts are linked to authorization records for full traceability.
