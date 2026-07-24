"""Interactive Workflow subsystem (IWC-001 v1.1).

Phase 143K: structural session infrastructure (domain model, identity,
state-machine skeleton, persistence abstraction, serialization framework,
invariant validation, error model, Session Coordinator skeleton). Phase
143L: the Transition Engine (transition legality determination and
in-memory state evolution only -- ``pcae.interactive_workflow.
state_machine.engine``). Phase 143M: Evidence Coordination
(``pcae.interactive_workflow.evidence``), Clarification infrastructure
(``pcae.interactive_workflow.clarification``), and Audit infrastructure
(``pcae.interactive_workflow.audit``) -- registration, ordering, and
retrieval only, each scoped passively to one session identifier. Phase
143N: Preview infrastructure (``pcae.interactive_workflow.preview`` --
deterministic, immutable Preview construction, Preview Digest generation,
preview validation, stale-preview detection) and Confirmation
infrastructure (``pcae.interactive_workflow.confirmation`` --
confirmation-request/response lifecycle, replay detection, digest
recheck), each scoped passively to one session identifier.

No workflow orchestration lives here. No CHGR is created here. Nothing in
this package can orchestrate a full session lifecycle, execute a
governance workflow, publish a record, or create a CHGR -- those remain
deferred to later phases (143O onward) per Phase 143J's implementation
plan.
"""

from __future__ import annotations
