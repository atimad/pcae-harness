#!/usr/bin/env python3
"""HHCE-001 v1.1 Hardware Credential Registration/Revocation Admin
Surface — Phase 149O.20L.7O.2L.1, `docs/contracts/
HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` §11-§20
(HHCE-REQ-015..049).

This is a **standalone script, deliberately outside `src/pcae/`** — never
imported by `cli.py`, `commands/agent.py`, `core/agent.py`, or any other
`src/pcae/**` module (HHCE-REQ-019/020), mirroring `scripts/
hatp_deployment_binding_admin.py`'s own module docstring exactly. It is
not packaged, not installed as a console-script entry point, and not
reachable from any agent-executable code path. It is invoked manually,

    python scripts/hatp_hardware_credential_admin.py enroll \\
        --repository-root . --enrollment-reference <CHGR-id>
    python scripts/hatp_hardware_credential_admin.py revoke \\
        --repository-root . --signer-key-id <hex> --enrollment-reference <CHGR-id>

by an operator running under the Class-B Protected Administrator OS
principal (HHCE-REQ-020) — the only principal with real write access to
`HATPHardwareCredentialStore.production().root`. It imports `pcae.core.
hatp_hardware_credential_admin`'s public writer functions directly and
never reimplements record parsing, validation, locking, persistence,
duplicate detection, or revocation semantics (those already belong to
that module).

Real security boundary (HHCE-REQ-020, mirroring HBDC-REQ-066): **OS
filesystem write permission on the hardware-credential-store root**,
never an in-process authority check. Nothing in this script establishes
or substitutes for that permission.

Two mutating ceremonies, two subcommands:

- **`enroll`** — the normal path. Runs a real CTAP2 `makeCredential`
  ceremony against an attached FIDO2 device
  (`Fido2HardwareProvider.enroll_credential()`, Surface A) to mint a
  fresh credential and derive its identity, then registers it
  (`register_credential()`, Surface B). `signer_key_id`/`public_key`/
  `algorithm` are never caller-supplied here (HHCE-REQ-012/§10 of the
  governing prompt) — they are always the live ceremony's own output.
  If the registry write does not cleanly succeed on the first attempt,
  `enroll` retries the write **in-process, automatically**, against the
  identical `CredentialEnrollmentEvidence` object the same ceremony
  already produced — it never re-touches hardware (no second
  `makeCredential`) and never accepts caller-supplied identity to do so.
  This is safe by construction: `register_credential()`'s own
  `_candidate_equal` idempotency (HHCE-REQ-016) makes a retry against an
  already-landed write a no-op, and a genuine write if the first attempt
  never landed (Phase 149O.20L.7O.2L architecture-freeze doc §6: "no
  additional recovery state machine is required ... not by a new
  mechanism this phase needs to invent"). If every retry fails, `enroll`
  fails closed with a diagnostic (no credential material dumped for
  manual re-entry) directing the operator to governed reconciliation —
  there is no CLI path that accepts caller-supplied credential identity
  to "recover" a record from scratch (Phase 149O.20L.7O.2L.3, repairing
  the Blocking finding independently verified by Phase 149O.20L.7O.2L.2:
  the former `recover` subcommand accepted fully human-typed identity
  material with no binding to any actual hardware ceremony and persisted
  it as an authoritative record).
- **`revoke`** — `revoke_credential()`, no hardware interaction.

No `--credential-id`/`--public-key` flag exists on either subcommand
(HHCE-REQ-012/§10 of the governing prompt): this script has no CLI path,
under any subcommand, that accepts caller-supplied credential identity
material for creating or reconstructing a `HardwareCredentialRecord`. No
PIN, private key, or other secret device material is ever accepted as a
CLI argument or printed by this script (HHCE-REQ-004).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from pcae.core.hatp_hardware_credential_admin import (
    CredentialConflictError,
    CredentialEnrollmentEvidence,
    CredentialEvidenceMalformedError,
    CredentialEvidenceMissingError,
    CredentialNotFoundError,
    CredentialReadbackMismatchError,
    HardwareCredentialOperationResult,
    HardwareCredentialPreview,
    HardwareCredentialStoreUnavailableError,
    HATPHardwareCredentialAdminError,
    preview_register_credential,
    preview_revoke_credential,
    register_credential,
    revoke_credential,
)
from pcae.core.hatp_hardware_credentials import HATPHardwareCredentialStoreError
from pcae.core.hatp_providers import HATPHardwareProviderError

_HANDLED_ERRORS = (
    HATPHardwareCredentialAdminError,
    HATPHardwareCredentialStoreError,
    HATPHardwareProviderError,
    OSError,
)


class ConfirmationDeclinedError(Exception):
    """The human operator did not confirm the tool-derived target. No
    registry write of any kind occurs. (A prior `enroll` ceremony's real
    hardware interaction, if any already happened, cannot itself be
    undone by declining here — there is no CLI path to retry only the
    registry write outside of a fresh `enroll` invocation.)"""


def _prompt_confirm(target_description: str) -> bool:
    print(target_description, file=sys.stderr)
    print("Type 'yes' to confirm this exact tool-derived target, anything else to abort:", file=sys.stderr)
    try:
        response = input()
    except EOFError:
        return False
    return response.strip() == "yes"


def _describe_preview(preview: HardwareCredentialPreview, *, ceremony: str) -> str:
    lines = [
        f"{ceremony.upper()} HardwareCredentialRecord for signer_key_id={preview.signer_key_id}",
        f"  registry_path={preview.registry_path}",
        f"  computed outcome kind={preview.kind.value}",
    ]
    if preview.existing_record is not None:
        lines.append(f"  existing entry: {preview.existing_record}")
    if preview.candidate_record is not None:
        lines.append(f"  candidate entry: {preview.candidate_record}")
    return "\n".join(lines)


def _report_result(result: HardwareCredentialOperationResult) -> None:
    record = result.record
    print(f"outcome={result.outcome.value} signer_key_id={record.signer_key_id}")
    print(f"  provider_profile={record.provider_profile} protocol_name={record.protocol_name} algorithm={record.algorithm}")
    print(f"  status={record.status} revoked_at={record.revoked_at}")


_MAX_REGISTER_ATTEMPTS = 3


def _register_with_in_process_retry(
    *, repository_root: Path, evidence: CredentialEnrollmentEvidence
) -> HardwareCredentialOperationResult:
    """Retries ONLY the registry write (`register_credential`), against the
    identical provider-generated `evidence` object the ceremony already
    produced — never re-touches hardware, never accepts a second, caller
    -reconstructed identity. Safe by construction: `register_credential`'s
    own idempotency (HHCE-REQ-016) makes a retry against an already-landed
    write a no-op, and a genuine write if the first attempt never landed;
    a deterministic failure (e.g. a real `CREDENTIAL_CONFLICT`) simply
    fails identically on every attempt, costing nothing beyond the wasted
    calls. This is the entire in-process recovery mechanism -- no separate
    CLI surface, no caller-supplied identity path (Phase 149O.20L.7O.2L.3,
    repairing the Blocking finding independently verified by Phase
    149O.20L.7O.2L.2)."""

    last_error: Optional[BaseException] = None
    for attempt in range(1, _MAX_REGISTER_ATTEMPTS + 1):
        try:
            return register_credential(repository_root=repository_root, evidence=evidence)
        except _HANDLED_ERRORS as exc:
            last_error = exc
    assert last_error is not None
    print(
        "REGISTRY PERSISTENCE DIAGNOSTIC: the physical hardware credential was created "
        f"(signer_key_id={evidence.signer_key_id}), but registry persistence did not complete "
        f"after {_MAX_REGISTER_ATTEMPTS} in-process attempts using the identical provider-generated "
        f"evidence (last error: {type(last_error).__name__}: {last_error}). This operation requires "
        "governed reconciliation/retry; no manual credential import path exists.",
        file=sys.stderr,
    )
    raise last_error


def _run_enrollment_ceremony(*, presence_timeout_s: float) -> "object":
    """Lazily imports `Fido2HardwareProvider` (mirrors that module's own
    documented lazy-import discipline: ordinary PCAE core imports never
    require the optional `fido2`/`cryptography` extras). The only
    production hardware provider currently implemented (HHCE-REQ-014)."""

    from pcae.core.hatp_fido2_provider import Fido2HardwareProvider

    provider = Fido2HardwareProvider()
    return provider.enroll_credential(presence_timeout_s=presence_timeout_s)


def _evidence_from_enrolled_credential(enrolled: "object", *, enrollment_reference: str) -> CredentialEnrollmentEvidence:
    return CredentialEnrollmentEvidence(
        signer_key_id=enrolled.credential_id_hex,
        provider_profile=enrolled.provider_profile,
        protocol_name="FIDO2",
        algorithm=enrolled.algorithm,
        public_key_hex=enrolled.public_key_hex,
        enrollment_reference=enrollment_reference,
    )


def _cmd_enroll(args: argparse.Namespace) -> int:
    enrolled = _run_enrollment_ceremony(presence_timeout_s=args.presence_timeout_s)
    evidence = _evidence_from_enrolled_credential(enrolled, enrollment_reference=args.enrollment_reference)

    preview = preview_register_credential(evidence=evidence)
    description = _describe_preview(preview, ceremony="enroll")

    if args.preview:
        print(description)
        return 0

    confirmed = args.assume_yes or _prompt_confirm(description)
    if not confirmed:
        raise ConfirmationDeclinedError(
            "enroll was not confirmed by the operator; no registry write occurred "
            "(the physical makeCredential ceremony already happened and cannot be undone by this script)"
        )

    result = _register_with_in_process_retry(repository_root=args.repository_root, evidence=evidence)
    _report_result(result)
    return 0


def _cmd_revoke(args: argparse.Namespace) -> int:
    if args.preview:
        preview = preview_revoke_credential(signer_key_id=args.signer_key_id)
        print(_describe_preview(preview, ceremony="revoke"))
        return 0

    preview = preview_revoke_credential(signer_key_id=args.signer_key_id)
    confirmed = args.assume_yes or _prompt_confirm(_describe_preview(preview, ceremony="revoke"))
    if not confirmed:
        raise ConfirmationDeclinedError("revoke was not confirmed by the operator; no registry write occurred")

    result = revoke_credential(
        repository_root=args.repository_root,
        signer_key_id=args.signer_key_id,
        enrollment_reference=args.enrollment_reference,
    )
    _report_result(result)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hatp_hardware_credential_admin.py",
        description=(
            "Protected-admin HHCE-001 v1.1 hardware credential enroll/revoke ceremony. "
            "Not reachable from the ordinary pcae CLI or any agent-executed code path (HHCE-REQ-019/020). "
            "Requires real OS write access to HATPHardwareCredentialStore.production().root."
        ),
    )
    sub = parser.add_subparsers(dest="ceremony", required=True)

    enroll_parser = sub.add_parser(
        "enroll",
        help="Run a live FIDO2 makeCredential ceremony, then register the resulting credential.",
    )
    enroll_parser.add_argument("--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd).")
    enroll_parser.add_argument(
        "--enrollment-reference",
        required=True,
        help="Evidence reference (e.g. a CHGR id) for a fresh, separate human election authorizing this "
        "registration (HHCE-REQ-049). Recorded as audit metadata only -- never cryptographically verified.",
    )
    enroll_parser.add_argument("--presence-timeout-s", type=float, default=30.0, help="Device presence timeout in seconds.")
    enroll_parser.add_argument("--assume-yes", action="store_true", help="Skip the interactive confirmation prompt.")
    enroll_parser.add_argument(
        "--preview", action="store_true", help="Run the ceremony and compute the target only; never writes the registry."
    )

    revoke_parser = sub.add_parser("revoke", help="Field-mutate an existing entry to status=revoked (never deletes, never touches hardware).")
    revoke_parser.add_argument("--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd).")
    revoke_parser.add_argument("--signer-key-id", required=True, help="The credential's signer_key_id.")
    revoke_parser.add_argument(
        "--enrollment-reference",
        required=True,
        help="Evidence reference (e.g. a CHGR id) for this revocation. Recorded as audit metadata only.",
    )
    revoke_parser.add_argument("--assume-yes", action="store_true")
    revoke_parser.add_argument("--preview", action="store_true", help="Compute the target only; never writes.")

    return parser


def main(argv: "Optional[list]" = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        if args.ceremony == "enroll":
            return _cmd_enroll(args)
        return _cmd_revoke(args)
    except ConfirmationDeclinedError as exc:
        print(f"ABORTED: {exc}", file=sys.stderr)
        return 1
    except (
        CredentialEvidenceMalformedError,
        CredentialEvidenceMissingError,
        HardwareCredentialStoreUnavailableError,
        CredentialConflictError,
        CredentialNotFoundError,
        CredentialReadbackMismatchError,
    ) + _HANDLED_ERRORS as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
