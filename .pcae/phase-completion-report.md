# Phase 149O.20L.7O.2U.1 Complete — Reference Adapter Contract Freeze

Executed the first of the 5 governed phases frozen by
`docs/PHASE_149O_20L_7O_2U_V0_3_RELEASE_EXECUTION_PLAN_AND_CRITICAL_PATH_FREEZE.md`:
froze the generic diff/JSON reference-adapter intake contract and the
thin Claude Code reference-adapter relationship, per the two human
decisions already resolved in Phase 2U.

**Gap analysis (grounded in current code)**: inspected the real
`execution-activation`/`execution-change-package`/`promotion-review`/
`promote` CLI surface in `src/pcae/cli.py` directly. Confirmed
`execution-activation invoke` is scoped specifically to sandboxing
PCAE's own claude-local runtime, and `ExecutionChangePackage` (ECP) is
"created automatically during sandboxed execution" with no existing
path to construct one from an externally-produced diff. Everything
downstream of an ECP (`promotion-review`, `promote`, `rollback`) is
already runtime-agnostic, referencing only ECP/EPR identifiers and
approved-path lists — never claude-local specifically. The gap is
narrow: only PCAE's own sandboxed invocation can currently produce an
ECP.

**Contract frozen (v1)**: a generic diff/JSON `Intake Candidate` schema
(`intake_contract_version`, `producer`, `task_context`,
`proposed_changes[]` with per-path diff/hash, `producer_claims`) as a
new, additive, non-authorizing ECP-compatible artifact-creation path —
task-scope checked via the existing allow-list mechanism, content-hash
verified against the proposed content rather than trusted on the
producer's word, producer identity never a basis for trust or review
skip.

**Thin Claude Code relationship frozen**: Claude Code is the first
concrete producer against the generic contract via a thin adapter, with
an explicit constraint that no Claude-Code-specific field or semantic
may appear in the generic schema itself.

**CLI surface shape frozen (not implemented)**: `pcae intake
create/show/list`, mirroring existing `promotion-review`/
`execution-change-package` conventions — for 2U.2 to implement.

A 7-test suite mechanically verifies the contract document's substance,
the frozen schema fields, that the schema block contains no Claude-Code
identifier, that the referenced existing commands are unmodified, that
no production code or HATP/WebAuthn/FIDO2 path was touched, and that no
`pcae intake` command exists yet: 7 passed, 0 failed.

No production code (`src/pcae/**`) was modified this phase. No adapter
code was written. No new authority surface was enabled. No Git history
rewritten; no force push; no raw `git push`.

Full text:
`docs/PHASE_149O_20L_7O_2U_1_REFERENCE_ADAPTER_CONTRACT_FREEZE.md`.

Recommended next: 149O.20L.7O.2U.2 — Reference Adapter Implementation
(requires independent verification, 2U.3, per the 2U plan's critical
path).
