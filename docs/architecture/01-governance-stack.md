# PCAE Governance Stack

The governance stack shows how each domain governs a distinct layer of the AI execution lifecycle. Human Approval is the authoritative gate at every level — no domain can produce an execution-eligible artifact without it.

```mermaid
flowchart TD
    HA["👤 Human Approval\n─────────────────────\nAuthoritative at every gate.\nNo execution proceeds without\nexplicit human sign-off."]

    subgraph TOP["Upstream Governance — constrains what may be attempted"]
        CG["Change Governance\n──────────────────\nTask contracts define allowed\nfiles, forbidden operations,\nand architecture zone rules.\npcae check enforces on every\nsource change."]
        RG["Rollback Governance\n────────────────────\nRollback strategy declared and\nvalidated before write execution.\nPre-modification snapshot\nrequired. Triggered by failed\nverification."]
        PG["Prompt Governance\n──────────────────\nPrompts generated, rendered,\nand preflight-validated before\nsubmission. Forbidden operations\nderived from task contract."]
    end

    subgraph MID["Execution Governance — controls whether invocation may proceed"]
        EG["Execution Governance\n─────────────────────\n8-step lifecycle gate chain.\nAuthorization → contract →\npreflight → audit → capture\n→ human approval.\nexecution_allowed=False\nuntil all gates pass."]
        RTG["Runtime Governance\n────────────────────\nRuntime trust assessed.\n7 contract enforcement checks.\nSandbox, timeout, and output\ncapture verified per runtime.\nAll runtimes currently blocked."]
    end

    subgraph BOTTOM["Audit and Evidence — makes every attempt reviewable"]
        AEG["Audit / Evidence Governance\n───────────────────────────\nEvery attempt produces a\nstructured audit record.\nEvidence model links request,\nauthorization, audit, capture,\nand review into one chain.\nevidence_ready=False until\nall upstream gates pass."]
    end

    HA --> CG & RG & PG
    CG & RG & PG --> EG
    EG --> RTG
    RTG --> AEG
    AEG -->|"human_review_required=True"| HA
```

## Current Status

All execution gates are currently **blocked**. `execution_allowed=False` for all runtimes. The governance stack is scaffolded and validated; execution will be unblocked progressively as each gate is cleared by subsequent phases.
