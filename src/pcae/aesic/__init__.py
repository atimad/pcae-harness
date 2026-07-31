"""Authority Evaluation Service integration package (AESIC-001 v1.3).

This package is deliberately **separate** from ``pcae.authority_evaluation``
(AEMIC-001, frozen): AESIC-001 §2.1 (AESIC-REQ-001) governs only the
integration surface, never the internal implementation of the already-
frozen, pure ``pcae.authority_evaluation`` package, whose own closed
module shape and forbidden-import boundary (AEMIC-REQ-010-014,
``tests/test_phase_147g_authority_evaluation.py``) this package's own
existence leaves entirely undisturbed.

Public entry points:

- ``service.AuthorityEvaluationService`` -- the sole orchestrator (§5).
- ``records.Stage1EvaluationResult`` / ``records.AuthorityEvaluationRecord``
  -- the two AESIC-001-owned value types (§5.2.1, §8).
- ``storage.AuthorityEvaluationRecordStore`` -- the two-tier persistence
  layer (§12.1).
- ``registry_filesystem.FilesystemAuthorityRegistry`` -- the minimum
  concrete ``AuthorityRegistry`` adapter (§7).
- ``errors`` -- the integration-owned error taxonomy (§13).
- ``diagnostics`` -- the read-only inspection surface (§16).
"""

from __future__ import annotations

from pcae.aesic.records import (
    AuthorityEvaluationRecord,
    Stage1EvaluationResult,
)
from pcae.aesic.service import AuthorityEvaluationService

__all__ = [
    "AuthorityEvaluationService",
    "AuthorityEvaluationRecord",
    "Stage1EvaluationResult",
]
