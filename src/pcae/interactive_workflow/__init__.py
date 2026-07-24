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
retrieval only, each scoped passively to one session identifier.

No workflow orchestration lives here. No CHGR is created here. Nothing in
this package can orchestrate a full session lifecycle, generate a Preview
or Preview Digest, perform confirmation,
cancellation/expiry/abandonment *execution*, or publication -- those
remain deferred to later phases (143N onward) per Phase 143J's
implementation plan.
"""

from __future__ import annotations
