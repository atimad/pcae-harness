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
    python scripts/hatp_hardware_credential_admin.py recover \\
        --repository-root . --signer-key-id <hex> \\
        --provider-profile HATP_HARDWARE_PROVIDER_V1 --protocol-name FIDO2 \\
        --algorithm ES256 --public-key-hex <hex> \\
        --enrollment-reference <CHGR-id>
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

Two mutating ceremonies, three subcommands:

- **`enroll`** — the normal path. Runs a real CTAP2 `makeCredential`
  ceremony against an attached FIDO2 device
  (`Fido2HardwareProvider.enroll_credential()`, Surface A) to mint a
  fresh credential and derive its identity, then registers it
  (`register_credential()`, Surface B). `signer_key_id`/`public_key`/
  `algorithm` are never caller-supplied here (HHCE-REQ-012/§10 of the
  governing prompt) — they are always the live ceremony's own output.
- **`recover`** — the load-bearing exception to that rule (governing
  prompt §9/§10/§27). If the ceremony (`enroll_credential()`) succeeds
  but the subsequent registry write (`register_credential()`) fails or
  its outcome is uncertain, `enroll` prints the ceremony's own
  non-secret identity fields as RECOVERY EVIDENCE before propagating the
  error. An operator re-runs `recover` with those exact field values to
  retry *only* the registry write, never re-touching the physical
  device (which would mint a second, distinct credential). Retrying with
  the identical evidence is safe: `register_credential()`'s own
  `_candidate_equal` idempotency (HHCE-REQ-016) makes it a no-op if the
  first attempt actually durably succeeded, and a genuine write if it
  did not. Retrying with *different* evidence for the same
  `signer_key_id` fails closed as `CREDENTIAL_CONFLICT`
  (HHCE-REQ-017) — this script performs no evidence reconciliation of
  its own.
- **`revoke`** — `revoke_credential()`, no hardware interaction.

No `--credential-id`/`--public-key` flag exists on `enroll` (governing
prompt §10) — only `recover` accepts explicit identity fields, and only
because it is the named recovery/import mode the contract's own
partial-failure disposition (HHCE-REQ-016, governing prompt §9)
requires. No PIN, private key, or other secret device material is ever
accepted as a CLI argument or printed by this script (HHCE-REQ-004).
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
    undone by declining here — see the module docstring's `recover`
    disposition.)"""


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


def _print_recovery_evidence(evidence: CredentialEnrollmentEvidence) -> None:
    print("RECOVERY EVIDENCE (non-secret; capture these exact values for `recover` if the write below fails):", file=sys.stderr)
    print(f"  --signer-key-id {evidence.signer_key_id}", file=sys.stderr)
    print(f"  --provider-profile {evidence.provider_profile}", file=sys.stderr)
    print(f"  --protocol-name {evidence.protocol_name}", file=sys.stderr)
    print(f"  --algorithm {evidence.algorithm}", file=sys.stderr)
    print(f"  --public-key-hex {evidence.public_key_hex}", file=sys.stderr)


def _run_enrollment_ceremony(*, presence_timeout_s: float) -> "object":
    """Lazily imports `Fido2HardwareProvider` (mirrors that module's own
    documented lazy-import discipline: ordinary PCAE core imports never
    require the optional `fido2`/`cryptography` extras). The only
    production hardware provider currently implemented (HHCE-REQ-014);
    `recover` is the path for any other protocol's evidence."""

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
        _print_recovery_evidence(evidence)
        raise ConfirmationDeclinedError(
            "enroll was not confirmed by the operator; no registry write occurred "
            "(the physical makeCredential ceremony already happened and cannot be undone by this script)"
        )

    try:
        result = register_credential(repository_root=args.repository_root, evidence=evidence)
    except _HANDLED_ERRORS:
        _print_recovery_evidence(evidence)
        raise
    _report_result(result)
    return 0


def _cmd_recover(args: argparse.Namespace) -> int:
    evidence = CredentialEnrollmentEvidence(
        signer_key_id=args.signer_key_id,
        provider_profile=args.provider_profile,
        protocol_name=args.protocol_name,
        algorithm=args.algorithm,
        public_key_hex=args.public_key_hex,
        enrollment_reference=args.enrollment_reference,
    )
    preview = preview_register_credential(evidence=evidence)
    description = _describe_preview(preview, ceremony="recover")

    if args.preview:
        print(description)
        return 0

    confirmed = args.assume_yes or _prompt_confirm(description)
    if not confirmed:
        raise ConfirmationDeclinedError("recover was not confirmed by the operator; no registry write occurred")

    result = register_credential(repository_root=args.repository_root, evidence=evidence)
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
            "Protected-admin HHCE-001 v1.1 hardware credential enroll/recover/revoke ceremony. "
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

    recover_parser = sub.add_parser(
        "recover",
        help="Retry ONLY the registry write for a credential already minted by a prior `enroll` ceremony "
        "(never touches hardware). Use the RECOVERY EVIDENCE printed by a failed `enroll` attempt.",
    )
    recover_parser.add_argument("--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd).")
    recover_parser.add_argument("--signer-key-id", required=True, help="Exactly the value from `enroll`'s printed RECOVERY EVIDENCE.")
    recover_parser.add_argument("--provider-profile", required=True, help="Exactly the value from `enroll`'s printed RECOVERY EVIDENCE.")
    recover_parser.add_argument("--protocol-name", required=True, choices=("FIDO2", "PIV"), help="Exactly the value from `enroll`'s printed RECOVERY EVIDENCE.")
    recover_parser.add_argument("--algorithm", required=True, help="Exactly the value from `enroll`'s printed RECOVERY EVIDENCE.")
    recover_parser.add_argument("--public-key-hex", required=True, help="Exactly the value from `enroll`'s printed RECOVERY EVIDENCE.")
    recover_parser.add_argument(
        "--enrollment-reference",
        required=True,
        help="Evidence reference for this specific retry (HHCE-REQ-049). MAY be the same reference used by the "
        "original failed `enroll` attempt, or a fresh one -- this script performs no reconciliation of its own.",
    )
    recover_parser.add_argument("--assume-yes", action="store_true", help="Skip the interactive confirmation prompt.")
    recover_parser.add_argument("--preview", action="store_true", help="Compute the target only; never writes.")

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
        if args.ceremony == "recover":
            return _cmd_recover(args)
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
