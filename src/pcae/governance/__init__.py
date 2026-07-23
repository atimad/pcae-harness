"""Canonical Human Governance Record (CHGR) library code (Phase 143E).

Implements only the machine-verifiable schema/artifact foundation for CHGR
per ``docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md``
(CHGR-001 v1.0): read-only inspection (:mod:`pcae.governance.inspection`)
and deterministic, fail-closed verification
(:mod:`pcae.governance.verification`) of explicit, caller-supplied CHGR
artifact files.

No interactive decision workflow, no ``create``/``confirm``/``publish``/
``suspend``/``supersede``/``revoke``/``import`` command, no
``.pcae/governance-records/`` storage or registry, no legacy-election
import, no signing, no external identity integration, no runtime
consumption, and no authority resolution exists in this package. Successful
schema validation or verification means only that an artifact conforms to
the CHGR representation contract -- it never establishes that the
represented governance act was valid, applicable, current, or performed by
an authorized human.
"""
from __future__ import annotations
