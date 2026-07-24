"""Publication Handoff package (IWC-001 v1.1 §2, §11.4, §18.4,
IWC-REQ-171; Phase 143O).

Implements the Publication Handoff *interface* -- an immutable
``PublicationReadinessPackage`` (``models``) and its sole constructor/
validator (``handoff.PublicationHandoff``) -- never Publication
*execution*. IWC-REQ-171 leaves Publication Handoff execution ownership
an explicitly open question for a future, separately governed phase; this
package does not close that question, assign that ownership, publish, or
create a CHGR.
"""

from __future__ import annotations

from pcae.interactive_workflow.publication_handoff.handoff import PublicationHandoff
from pcae.interactive_workflow.publication_handoff.models import (
    PUBLICATION_HANDOFF_SCHEMA_VERSION,
    PublicationReadinessPackage,
)

__all__ = [
    "PUBLICATION_HANDOFF_SCHEMA_VERSION",
    "PublicationReadinessPackage",
    "PublicationHandoff",
]
