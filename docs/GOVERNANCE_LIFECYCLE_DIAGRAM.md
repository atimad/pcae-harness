# Governance Lifecycle Diagrams

Mermaid diagrams illustrating PCAE's governance architecture and transition path.

## 1. High-Level Governance Lifecycle

```mermaid
flowchart TD
    A[Human Intent] --> B{Task Contract}
    B --> C[Governed Phase Work]
    C --> D[PCAE Health / Check]
    D --> E{Scope Verified?}
    E -->|Yes| F[Governed Commit]
    E -->|No| G[Blocked — Fix Scope]
    G --> C
    F --> H[Governed Push]
    H --> I[Phase Complete]
    I --> J{Next Phase?}
    J -->|Yes| B
    J -->|No| K[Lifecycle Closed]
```

## 2. Read-Only Project Intelligence Stack

```mermaid
flowchart BT
    AI[Artifact Index] --> PS[Project State]
    MS[Memory Snapshot] --> PS
    GT[Governance Timeline] --> PS
    DL[Decision Log] --> PS
    RR[Risk Register] --> PS

    style PS fill:#2d5,color:#fff
    style AI fill:#36a,color:#fff
    style MS fill:#36a,color:#fff
    style GT fill:#36a,color:#fff
    style DL fill:#36a,color:#fff
    style RR fill:#36a,color:#fff
```

All six layers are **read-only** and **non-authorizing**.

## 3. Gate Dry-Run Evaluation Layer

```mermaid
flowchart LR
    subgraph "Gate Dry-Run (15 gates)"
        SG[Scope Gate]
        BG[Backend Gate]
        AG[Adoption Gate]
        MG[Mutation Gate]
        CG[Commit Gate]
        PG[Push Gate]
        OG[9 Other Gates]
    end

    PI[Project Intelligence] --> SG
    PI --> BG
    PI --> AG
    PI --> MG
    PI --> CG
    PI --> PG
    TC[Task Contract] --> SG
    TC --> MG

    SG --> D{Decision}
    BG --> D
    AG --> D
    MG --> D
    CG --> D
    PG --> D
    OG --> D

    D --> R[requires_human_review]
    D --> M[requires_more_evidence]
    D --> B[blocked_by_*]
    D --> DN[deny]

    style D fill:#c52,color:#fff
```

No gate produces `allow`. All decisions are non-authorizing.

## 4. Future Broker and Shell Gate Architecture

```mermaid
flowchart TD
    subgraph "Current (Implemented)"
        PI2[Project Intelligence Stack]
        GDR[Gate Dry-Run Evaluator]
    end

    subgraph "Future (Designed, Not Implemented)"
        PB[Permission Broker]
        SGT[Shell Gate]
    end

    subgraph "Future (Not Started)"
        EG[Enforced Preflight Gates]
        GE[Governed Execution]
    end

    PI2 -->|evidence| GDR
    GDR -->|dry-run decisions| PB
    PI2 -->|evidence| PB
    PB -->|broker decisions| SGT
    SGT -->|allow/deny| EG
    EG --> GE

    style PI2 fill:#2d5,color:#fff
    style GDR fill:#2d5,color:#fff
    style PB fill:#da3,color:#fff
    style SGT fill:#da3,color:#fff
    style EG fill:#888,color:#fff
    style GE fill:#888,color:#fff
```

## 5. Transition Path

```mermaid
flowchart LR
    O[Observe] --> DE[Dry-Run Evaluate]
    DE --> PF[Preflight Block]
    PF --> BD[Broker Decisions]
    BD --> SM[Shell Mediation]
    SM --> GX[Governed Execution]

    style O fill:#2d5,color:#fff
    style DE fill:#2d5,color:#fff
    style PF fill:#da3,color:#fff
    style BD fill:#da3,color:#fff
    style SM fill:#da3,color:#fff
    style GX fill:#888,color:#fff
```

**Green** = implemented. **Orange** = designed, not implemented. **Gray** = future.
