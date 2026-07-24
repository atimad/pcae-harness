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
recheck), each scoped passively to one session identifier. Phase 143O:
Session Coordination & Publication Handoff Integration --
``pcae.interactive_workflow.orchestration`` (deterministic, eight-stage
workflow sequencing composing 143K-143N's infrastructure, invoking only
existing public methods; ``session.coordinator.SessionCoordinator``
composes this module rather than duplicating its logic) and
``pcae.interactive_workflow.publication_handoff`` (an immutable
Publication Readiness Package and its sole builder/validator -- a
readiness *interface* only, never publication execution, per
IWC-REQ-171's explicitly open Publication Handoff execution-ownership
question).

No CHGR is created here. Nothing in this package can execute a
governance workflow, publish a record, create a CHGR, or invoke PCAE
lifecycle authority -- those remain out of scope through Phase 143O per
Phase 143J's implementation plan and IWC-REQ-171.
"""

from __future__ import annotations
