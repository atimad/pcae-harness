#!/usr/bin/env python3
"""HPSE-001 v1.1 Principal/Signer Enrollment Admin Surface — Phase
149O.20L.7O.2L.1, `docs/contracts/
HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` §11-§18, §29-§31
(HPSE-REQ-026..046, HPSE-REQ-056..058).

This is a **standalone script, deliberately outside `src/pcae/`** — never
imported by `cli.py`, `commands/agent.py`, `core/agent.py`, or any other
`src/pcae/**` module (HPSE-REQ-028/029), mirroring `scripts/
hatp_deployment_binding_admin.py`'s own module docstring exactly. It is
not packaged, not installed as a console-script entry point, and not
reachable from any agent-executable code path. It is invoked manually,

    python scripts/hatp_principal_signer_admin.py enroll-principal \\
        --repository-root . --principal-id <id> --election-reference <CHGR-id>
    python scripts/hatp_principal_signer_admin.py enroll-signer \\
        --repository-root . --principal-id <id> --signer-key-id <hex> \\
        --provider-profile HATP_HARDWARE_PROVIDER_V1 --election-reference <CHGR-id>
    python scripts/hatp_principal_signer_admin.py revoke-principal \\
        --repository-root . --principal-id <id> --election-reference <CHGR-id>
    python scripts/hatp_principal_signer_admin.py revoke-signer \\
        --repository-root . --signer-key-id <hex> --election-reference <CHGR-id>

by an operator running under the Class-B Protected Administrator OS
principal (HPSE-REQ-029) — the only principal with real write access to
`HATPTrustStore.production().root`. It imports `pcae.core.
hatp_principal_signer_admin`'s public writer functions directly and
never reimplements record parsing, validation, identity derivation,
locking, persistence, duplicate detection, or the cross-registry
precondition (those already belong to that module).

Real security boundary (HPSE-REQ-029, mirroring HBDC-REQ-066): **OS
filesystem write permission on the Protected Root**, never an in-process
authority check. Nothing in this script establishes or substitutes for
that permission.

Four subcommands, one core operation each — `enroll-principal`,
`revoke-principal`, `enroll-signer`, `revoke-signer`. This mirrors the
core module's own four-operation writer API (HPSE-REQ-026) exactly: it
does **not** invent a single combined "enroll principal+signer" ceremony,
because HPSE-001's own architecture already keeps them as two
independent operations with independent preconditions (`enroll_signer`
merely *requires* an existing active `PrincipalRecord`, HPSE-REQ-027 —
it does not need to be invoked in the same process as the principal's
own enrollment). The load-bearing continuous two-lock critical section
this contract requires (HPSE-REQ-057, HHCE-REQ-037: the
hardware-credential-store lock held OUTER and `.deployment-binding-
transition.lock` held INNER, continuously, across `enroll_signer`'s own
precondition-check-through-write sequence) is entirely internal to one
single call to `hatp_principal_signer_admin.enroll_signer()` — this
script never decomposes that call across multiple shell invocations or
releases/reacquires anything itself; it simply invokes the one Python
function that already holds both locks for its own entire duration.

`enroll-signer` never accepts a `--public-key`/other cryptographic
material flag: `--signer-key-id`/`--provider-profile` here name an
*already-registered* `HardwareCredentialRecord` (via `scripts/
hatp_hardware_credential_admin.py enroll`, run first) — this script
re-validates that registration live, under the lock, rather than
trusting the caller's claim (HPSE-REQ-056). This script creates no
`DeploymentBinding` and performs no HMIC certification action.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from pcae.core.hatp_bootstrap import HATPTrustStoreError
from pcae.core.hatp_hardware_credentials import HATPHardwareCredentialStoreError
from pcae.core.hatp_principal_signer_admin import (
    DuplicatePrincipalError,
    DuplicateSignerError,
    HardwareCredentialConflictError,
    HardwareCredentialNotRegisteredError,
    HATPPrincipalSignerAdminError,
    PrincipalEnrollmentEvidence,
    PrincipalEvidenceMalformedError,
    PrincipalNotFoundError,
    PrincipalOperationResult,
    PrincipalPreview,
    PrincipalRevokedError,
    ReadbackMismatchError,
    SignerEnrollmentEvidence,
    SignerNotFoundError,
    SignerOperationResult,
    SignerPreview,
    UnsupportedProviderProfileError,
    enroll_principal,
    enroll_signer,
    preview_enroll_principal,
    preview_enroll_signer,
    preview_revoke_principal,
    preview_revoke_signer,
    revoke_principal,
    revoke_signer,
)

_HANDLED_ERRORS = (
    HATPPrincipalSignerAdminError,
    HATPTrustStoreError,
    HATPHardwareCredentialStoreError,
    OSError,
)


class ConfirmationDeclinedError(Exception):
    """The human operator did not confirm the tool-derived target. No
    write of any kind occurs."""


def _prompt_confirm(target_description: str) -> bool:
    print(target_description, file=sys.stderr)
    print("Type 'yes' to confirm this exact tool-derived target, anything else to abort:", file=sys.stderr)
    try:
        response = input()
    except EOFError:
        return False
    return response.strip() == "yes"


def _describe_principal_preview(preview: PrincipalPreview, *, ceremony: str) -> str:
    lines = [
        f"{ceremony.upper()} PrincipalRecord for principal_id={preview.principal_id}",
        f"  computed outcome kind={preview.kind.value}",
    ]
    if preview.existing_record is not None:
        lines.append(f"  existing entry: {preview.existing_record}")
    return "\n".join(lines)


def _describe_signer_preview(preview: SignerPreview, *, ceremony: str) -> str:
    lines = [
        f"{ceremony.upper()} SignerRecord for signer_key_id={preview.signer_key_id}",
        f"  computed outcome kind={preview.kind.value}",
    ]
    if preview.existing_record is not None:
        lines.append(f"  existing entry: {preview.existing_record}")
    return "\n".join(lines)


def _report_principal_result(result: PrincipalOperationResult) -> None:
    record = result.record
    print(f"outcome={result.outcome.value} principal_id={record.principal_id}")
    print(f"  status={record.status} revoked_at={record.revoked_at}")


def _report_signer_result(result: SignerOperationResult) -> None:
    record = result.record
    print(f"outcome={result.outcome.value} signer_key_id={record.signer_key_id}")
    print(f"  principal_id={record.principal_id} provider_profile={record.provider_profile}")
    print(f"  status={record.status} revoked_at={record.revoked_at}")


def _cmd_enroll_principal(args: argparse.Namespace) -> int:
    evidence = PrincipalEnrollmentEvidence(principal_id=args.principal_id, election_reference=args.election_reference)
    preview = preview_enroll_principal(evidence=evidence, _protected_root=args._protected_root)
    description = _describe_principal_preview(preview, ceremony="enroll-principal")

    if args.preview:
        print(description)
        return 0

    confirmed = args.assume_yes or _prompt_confirm(description)
    if not confirmed:
        raise ConfirmationDeclinedError("enroll-principal was not confirmed by the operator; no write occurred")

    result = enroll_principal(repository_root=args.repository_root, evidence=evidence, _protected_root=args._protected_root)
    _report_principal_result(result)
    return 0


def _cmd_revoke_principal(args: argparse.Namespace) -> int:
    preview = preview_revoke_principal(principal_id=args.principal_id, _protected_root=args._protected_root)
    description = _describe_principal_preview(preview, ceremony="revoke-principal")

    if args.preview:
        print(description)
        return 0

    confirmed = args.assume_yes or _prompt_confirm(description)
    if not confirmed:
        raise ConfirmationDeclinedError("revoke-principal was not confirmed by the operator; no write occurred")

    result = revoke_principal(
        repository_root=args.repository_root,
        principal_id=args.principal_id,
        election_reference=args.election_reference,
        _protected_root=args._protected_root,
    )
    _report_principal_result(result)
    return 0


def _cmd_enroll_signer(args: argparse.Namespace) -> int:
    evidence = SignerEnrollmentEvidence(
        principal_id=args.principal_id,
        signer_key_id=args.signer_key_id,
        provider_profile=args.provider_profile,
        election_reference=args.election_reference,
    )
    preview = preview_enroll_signer(
        evidence=evidence, _protected_root=args._protected_root, _hardware_store_root=args._hardware_store_root
    )
    description = _describe_signer_preview(preview, ceremony="enroll-signer")

    if args.preview:
        print(description)
        return 0

    confirmed = args.assume_yes or _prompt_confirm(description)
    if not confirmed:
        raise ConfirmationDeclinedError("enroll-signer was not confirmed by the operator; no write occurred")

    result = enroll_signer(
        repository_root=args.repository_root,
        evidence=evidence,
        _protected_root=args._protected_root,
        _hardware_store_root=args._hardware_store_root,
    )
    _report_signer_result(result)
    return 0


def _cmd_revoke_signer(args: argparse.Namespace) -> int:
    preview = preview_revoke_signer(signer_key_id=args.signer_key_id, _protected_root=args._protected_root)
    description = _describe_signer_preview(preview, ceremony="revoke-signer")

    if args.preview:
        print(description)
        return 0

    confirmed = args.assume_yes or _prompt_confirm(description)
    if not confirmed:
        raise ConfirmationDeclinedError("revoke-signer was not confirmed by the operator; no write occurred")

    result = revoke_signer(
        repository_root=args.repository_root,
        signer_key_id=args.signer_key_id,
        election_reference=args.election_reference,
        _protected_root=args._protected_root,
    )
    _report_signer_result(result)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hatp_principal_signer_admin.py",
        description=(
            "Protected-admin HPSE-001 v1.1 Principal/Signer enroll/revoke ceremony. "
            "Not reachable from the ordinary pcae CLI or any agent-executed code path (HPSE-REQ-028/029). "
            "Requires real OS write access to HATPTrustStore.production().root."
        ),
    )
    # `--_protected-root`/`--_hardware-store-root` are deliberately absent
    # from the public CLI surface: this script never exposes an
    # `--output-file`/alternate-root override (governing prompt §21).
    # `args._protected_root`/`args._hardware_store_root` are always None
    # in production; test seams call the underlying functions directly
    # instead of routing an override through this parser.
    sub = parser.add_subparsers(dest="ceremony", required=True)

    enroll_principal_parser = sub.add_parser("enroll-principal", help="Enroll a new PrincipalRecord (idempotent on an identical active entry).")
    enroll_principal_parser.add_argument("--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd).")
    enroll_principal_parser.add_argument("--principal-id", required=True, help="Admin enrollment context (HPSE-REQ-002).")
    enroll_principal_parser.add_argument(
        "--election-reference",
        required=True,
        help="Evidence reference (e.g. a CHGR id) for a fresh, separate human election (HPSE-REQ-042/043). "
        "Recorded as audit metadata only -- never cryptographically verified.",
    )
    enroll_principal_parser.add_argument("--assume-yes", action="store_true", help="Skip the interactive confirmation prompt.")
    enroll_principal_parser.add_argument("--preview", action="store_true", help="Compute the target only; never writes.")

    revoke_principal_parser = sub.add_parser("revoke-principal", help="Field-mutate a PrincipalRecord to status=revoked (never deletes).")
    revoke_principal_parser.add_argument("--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd).")
    revoke_principal_parser.add_argument("--principal-id", required=True)
    revoke_principal_parser.add_argument(
        "--election-reference", required=True, help="Evidence reference for this revocation. Recorded as audit metadata only."
    )
    revoke_principal_parser.add_argument("--assume-yes", action="store_true")
    revoke_principal_parser.add_argument("--preview", action="store_true", help="Compute the target only; never writes.")

    enroll_signer_parser = sub.add_parser(
        "enroll-signer",
        help="Bind an already-registered HardwareCredentialRecord to a principal as an active SignerRecord "
        "(HPSE-REQ-056's cross-registry precondition, checked live under the continuous two-lock critical section).",
    )
    enroll_signer_parser.add_argument("--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd).")
    enroll_signer_parser.add_argument("--principal-id", required=True, help="An existing, active PrincipalRecord (HPSE-REQ-027).")
    enroll_signer_parser.add_argument(
        "--signer-key-id",
        required=True,
        help="Identity of an already-registered HardwareCredentialRecord (from `hatp_hardware_credential_admin.py "
        "enroll`), never independently invented here (HPSE-REQ-010).",
    )
    enroll_signer_parser.add_argument(
        "--provider-profile", required=True, help="Must match the registered credential's own provider_profile (HPSE-REQ-020/056)."
    )
    enroll_signer_parser.add_argument(
        "--election-reference",
        required=True,
        help="This specific signer-enrollment act's own fresh election evidence (HPSE-REQ-042), distinct from the "
        "hardware credential's own enrollment_reference. Recorded as audit metadata only.",
    )
    enroll_signer_parser.add_argument("--assume-yes", action="store_true", help="Skip the interactive confirmation prompt.")
    enroll_signer_parser.add_argument("--preview", action="store_true", help="Compute the target only; never writes.")

    revoke_signer_parser = sub.add_parser("revoke-signer", help="Field-mutate a SignerRecord to status=revoked (never deletes, never cascades to the hardware credential).")
    revoke_signer_parser.add_argument("--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd).")
    revoke_signer_parser.add_argument("--signer-key-id", required=True)
    revoke_signer_parser.add_argument(
        "--election-reference", required=True, help="Evidence reference for this revocation. Recorded as audit metadata only."
    )
    revoke_signer_parser.add_argument("--assume-yes", action="store_true")
    revoke_signer_parser.add_argument("--preview", action="store_true", help="Compute the target only; never writes.")

    return parser


def main(argv: "Optional[list]" = None) -> int:
    args = _build_parser().parse_args(argv)
    # Production CLI surface never exposes a root override (governing
    # prompt §21) -- always resolved to the fixed production roots by the
    # underlying core functions themselves.
    args._protected_root = None
    args._hardware_store_root = None

    try:
        if args.ceremony == "enroll-principal":
            return _cmd_enroll_principal(args)
        if args.ceremony == "revoke-principal":
            return _cmd_revoke_principal(args)
        if args.ceremony == "enroll-signer":
            return _cmd_enroll_signer(args)
        return _cmd_revoke_signer(args)
    except ConfirmationDeclinedError as exc:
        print(f"ABORTED: {exc}", file=sys.stderr)
        return 1
    except (
        PrincipalEvidenceMalformedError,
        PrincipalNotFoundError,
        PrincipalRevokedError,
        DuplicatePrincipalError,
        SignerNotFoundError,
        DuplicateSignerError,
        UnsupportedProviderProfileError,
        HardwareCredentialNotRegisteredError,
        HardwareCredentialConflictError,
        ReadbackMismatchError,
    ) + _HANDLED_ERRORS as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
