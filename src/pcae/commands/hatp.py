"""``pcae hatp sign rollback`` -- HSCE-001 v1.1 CLI surface (Phase 149O.12C,
Wave E of the 149O.11 implementation plan).

Implements HSCE-REQ-009..012, HSCE-REQ-017, HSCE-REQ-046..047, HSCE-REQ-065..066,
HSCE-REQ-071 (`docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`,
HSCE-001 v1.1). This module owns only: CLI argument definition, cross-field
locator validation, the single production-path call into
``pcae.core.hatp_signing_ceremony.production_sign_rollback_evidence``,
``error_type`` -> exit-code mapping, and human/``--json`` output rendering.

It owns **none** of: proof construction, provider selection, trust-store
selection, blind-touch-defense preview/confirmation, evidence
serialization, store publication, or RAE/Decision resolution -- all of
that is 149O.12A/149O.12B's core-layer responsibility, consumed here
unmodified through the single zero-override production entry point.

**Critical F-2 non-regression boundary (HSCE-REQ-002/§30 of the
contract):** this module imports and calls only
``production_sign_rollback_evidence`` -- never the injectable
``sign_rollback_evidence`` -- and passes it exactly ``root``/``site``/
``job_id``/``per_id``, the identical four parameters its own signature
already carries. There is no ``--provider``/``--signer``/``--trust-
store``/``--force``/``--overwrite``/``--dry-run`` flag, and none may be
added without a governed contract amendment.

Optional-dependency boundary (HSCE-REQ-028, 149O.11 plan §13.5): this
module's only production import is
``pcae.core.hatp_signing_ceremony.production_sign_rollback_evidence``,
whose own module already imports cleanly without ``fido2``/
``cryptography`` installed (149O.12B's own non-scope-creep confirmation).
No hardware discovery occurs at import time or at ``--help`` time --
only when the production entry point actually reaches provider
resolution.
"""
from __future__ import annotations

import argparse
import json
from typing import Optional

from pcae.core.hatp_evidence_store import EvidenceConflictError, EvidencePersistenceFailureError
from pcae.core.hatp_signed_evidence import HATPSignedEvidenceError
from pcae.core.hatp_signing_ceremony import HATPSigningCeremonyError, production_sign_rollback_evidence
from pcae.core.human_approval_trusted_provenance import RollbackSite
from pcae.core.paths import HarnessPath

# ═══════════════════════════════════════════════════════════════════════════
# Exit-code contract (HSCE-REQ-046) -- a small, closed set of integer
# categories, centralized here exactly once. No numeric literal is
# scattered through the handler branches below.
# ═══════════════════════════════════════════════════════════════════════════

EXIT_SUCCESS = 0
EXIT_GENERIC_SIGNING_FAILURE = 1
EXIT_OPERATION_NOT_FOUND = 2
EXIT_GOVERNANCE_STATE_UNAVAILABLE = 3
EXIT_SUBSTRATE_UNAVAILABLE = 4
EXIT_HUMAN_CANCELLED = 5
EXIT_PROVIDER_FAILURE = 6
EXIT_EVIDENCE_CONFLICT = 7
EXIT_PERSISTENCE_FAILURE = 8

#: HSCE-REQ-047: the closed error-vocabulary-to-exit-code mapping, frozen
#: as exactly these 12 members -- a future implementation SHALL NOT add a
#: 13th `error_type` here without a governed contract amendment
#: (HSCE-REQ-048).
_EXIT_CODE_BY_ERROR_TYPE = {
    "repository_identity_unavailable": EXIT_GOVERNANCE_STATE_UNAVAILABLE,
    "operation_not_found": EXIT_OPERATION_NOT_FOUND,
    "decision_unavailable": EXIT_GOVERNANCE_STATE_UNAVAILABLE,
    "binding_unavailable": EXIT_GOVERNANCE_STATE_UNAVAILABLE,
    "no_authorized_signer": EXIT_SUBSTRATE_UNAVAILABLE,
    "provider_unavailable": EXIT_SUBSTRATE_UNAVAILABLE,
    "hardware_device_fault": EXIT_PROVIDER_FAILURE,
    "human_signing_cancelled": EXIT_HUMAN_CANCELLED,
    "provider_signature_failure": EXIT_PROVIDER_FAILURE,
    "evidence_serialization_failure": EXIT_GENERIC_SIGNING_FAILURE,
    "evidence_conflict": EXIT_EVIDENCE_CONFLICT,
    "evidence_persistence_failure": EXIT_PERSISTENCE_FAILURE,
}


def _error_type_for(exc: Exception) -> str:
    """Map a caught signing exception to its closed HSCE-REQ-047
    ``error_type``. ``hatp_signing_ceremony.py``'s own exception classes
    already carry a class-level ``error_type`` attribute drawn from the
    identical closed vocabulary. ``hatp_evidence_store.py``'s
    ``EvidenceConflictError``/``EvidencePersistenceFailureError`` and
    ``hatp_signed_evidence.py``'s ``HATPSignedEvidenceError`` (structural
    envelope-construction failure, HSCE-REQ-047's ``evidence_
    serialization_failure`` row) carry no such attribute of their own --
    both are propagated unmodified from ``production_sign_rollback_
    evidence`` (never re-wrapped/reinterpreted), so this function maps
    them explicitly rather than mutating those modules."""

    if isinstance(exc, HATPSigningCeremonyError):
        return exc.error_type
    if isinstance(exc, EvidenceConflictError):
        return "evidence_conflict"
    if isinstance(exc, EvidencePersistenceFailureError):
        return "evidence_persistence_failure"
    if isinstance(exc, HATPSignedEvidenceError):
        return "evidence_serialization_failure"
    raise TypeError(f"unclassified signing exception type: {type(exc)!r}")  # pragma: no cover


#: The exact, closed set of exception types this handler catches and maps
#: through `_error_type_for`. Any other exception (a genuine bug) is
#: never caught here -- it propagates as an unexpected internal error,
#: never mislabeled as a successful or classified signing failure
#: (HSCE-REQ-065's exit-zero discipline).
_KNOWN_SIGNING_ERRORS = (
    HATPSigningCeremonyError,
    EvidenceConflictError,
    EvidencePersistenceFailureError,
    HATPSignedEvidenceError,
)


# ═══════════════════════════════════════════════════════════════════════════
# Argument validation (HSCE-REQ-013/016/017) -- argparse's own mutual-
# exclusion groups cannot express "exactly one of --job-id/--per-id is
# required, and which one is valid depends on --site's value" directly
# (149O.11 plan §13.1), so this cross-field validation lives here, in the
# handler, as ordinary CLI-level misuse -- distinct from, and never
# expressed using, the closed HSCE `error_type` vocabulary above
# (governing-prompt §25's "keep the distinction explicit").
# ═══════════════════════════════════════════════════════════════════════════


def _validate_locator_arguments(args: argparse.Namespace) -> Optional[str]:
    """Returns a human-readable usage-error message if the supplied
    locator flags are invalid for the given ``--site``, else ``None``.
    Rejects the wrong-locator-for-site and both-locators-supplied cases
    before the missing-locator case, so a caller who supplies the wrong
    flag always gets the more specific "not valid for this site" message
    rather than a generic "required" message."""

    if args.site == "ag3":
        if args.per_id is not None:
            return "--per-id is not a valid locator for --site ag3; use --job-id"
        if args.job_id is None:
            return "--job-id is required for --site ag3"
    else:
        if args.job_id is not None:
            return "--job-id is not a valid locator for --site ag5; use --per-id"
        if args.per_id is None:
            return "--per-id is required for --site ag5"
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Output rendering (HSCE-REQ-065/066, HSCE-REQ-051)
# ═══════════════════════════════════════════════════════════════════════════


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _emit_usage_error(args: argparse.Namespace, message: str) -> int:
    """Ordinary CLI-level argument misuse (never an HSCE `error_type` --
    governing-prompt §25). Exit code 2 mirrors argparse's own
    conventional usage-error exit status; this failure never reaches
    `production_sign_rollback_evidence`, so no hardware/governance state
    is ever touched."""

    if getattr(args, "json", False):
        _print_json({"status": "error", "message": message})
    else:
        print(f"error: {message}")
    return 2


def _emit_success(args: argparse.Namespace, result) -> int:
    """HSCE-REQ-066: success output displays, at minimum, `evidence_id`
    and the canonical evidence path. No `approved`/`permission`/
    `executed`-resembling field exists anywhere in this schema --
    signing success means only that evidence was durably persisted
    (HSCE-REQ-065), never approval, Permission Broker `ALLOW`, or
    rollback execution."""

    if getattr(args, "json", False):
        _print_json(
            {
                "status": "success",
                "evidence_id": result.evidence_id,
                "evidence_path": str(result.path),
                "idempotent": result.idempotent,
            }
        )
        return EXIT_SUCCESS

    print("Signed HATP evidence created.")
    print(f"  evidence_id:    {result.evidence_id}")
    print(f"  evidence_path:  {result.path}")
    print(f"  idempotent:     {result.idempotent}")
    print()
    print(
        "This confirms evidence was persisted only -- it is not itself "
        "rollback approval, Permission Broker permission, or rollback "
        "execution."
    )
    return EXIT_SUCCESS


def _emit_error(args: argparse.Namespace, error_type: str, message: str) -> int:
    """HSCE-REQ-047/051: closed `error_type` only, no raw exception
    internals or provider secret state serialized."""

    if getattr(args, "json", False):
        _print_json({"status": "error", "error_type": error_type, "message": message})
    else:
        print(f"error: {message}")
        print(f"  error_type: {error_type}")
    return _EXIT_CODE_BY_ERROR_TYPE[error_type]


# ═══════════════════════════════════════════════════════════════════════════
# Handler
# ═══════════════════════════════════════════════════════════════════════════


def run_hatp_sign_rollback(args: argparse.Namespace) -> int:
    """``pcae hatp sign rollback --site {ag3|ag5} [--job-id|--per-id] [--json]``.

    Mirrors ``run_rollback``'s existing pattern (``src/pcae/commands/
    agent.py``): ``root = HarnessPath.cwd()`` (no ``--root`` flag exists
    -- HSCE-REQ contract §16), a single call into the production entry
    point with zero overrides, then error-type/exit-code mapping and
    output rendering. This is the only call site of
    ``production_sign_rollback_evidence`` in this module, and this
    module never imports the injectable ``sign_rollback_evidence``.
    """

    usage_error = _validate_locator_arguments(args)
    if usage_error is not None:
        return _emit_usage_error(args, usage_error)

    site = RollbackSite.AG3 if args.site == "ag3" else RollbackSite.AG5
    root = HarnessPath.cwd()

    try:
        result = production_sign_rollback_evidence(root, site=site, job_id=args.job_id, per_id=args.per_id)
    except _KNOWN_SIGNING_ERRORS as exc:
        return _emit_error(args, _error_type_for(exc), str(exc))

    return _emit_success(args, result)


__all__ = ["run_hatp_sign_rollback"]
