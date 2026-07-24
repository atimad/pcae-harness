"""Interactive Workflow subsystem (IWC-001 v1.1).

Phase 143K scope only: structural session infrastructure (domain model,
identity, state-machine skeleton, persistence abstraction, serialization
framework, invariant validation, error model, Session Coordinator skeleton).

No workflow behavior lives here. No CHGR is created here. Nothing in this
package can orchestrate evidence, clarification, preview, confirmation,
cancellation/expiry/abandonment execution, or publication -- those remain
deferred to later phases (143L onward) per Phase 143J's implementation plan.
"""

from __future__ import annotations
