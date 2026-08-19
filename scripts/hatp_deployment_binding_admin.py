#!/usr/bin/env python3
"""HBDC-001 v1.1 `DeploymentBinding` Producer/Rotation/Revocation Admin
Surface — Phase 149O.20L.7I, `docs/contracts/HATP_CLASS_B_DEPLOYMENT_
CONTRACT.md` §16.1 (HBDC-REQ-056..070).

This is a **standalone script, deliberately outside `src/pcae/`** — never
imported by `cli.py`, `commands/agent.py`, `core/agent.py`, or any other
`src/pcae/**` module (HBDC-REQ-056/066, mirroring `scripts/
hatp_certification_admin.py`'s own module docstring exactly). It is not
packaged, not installed as a console-script entry point, and not
reachable from any agent-executable code path. It is invoked manually,

    python scripts/hatp_deployment_binding_admin.py create \\
        --repository-root . --principal-id <id> --signer-key-id <id> \\
        --authority-scope <scope> \\
        --election-reference <CHGR-id>
    python scripts/hatp_deployment_binding_admin.py rotate \\
        --repository-root . --principal-id <id> --signer-key-id <id> \\
        --authority-scope <scope> \\
        --election-reference <CHGR-id>
    python scripts/hatp_deployment_binding_admin.py revoke \\
        --repository-root . --election-reference <CHGR-id>

by an operator running under the Class-B Protected Administrator OS
principal (HBDC-REQ-066) — the only principal with real write access to
`HATPTrustStore.production().root`. It imports `pcae.core.
hatp_deployment_binding_admin`'s public producer functions directly.

Real security boundary (HBDC-REQ-066, mirroring HMIC-REQ-079/HMIC-REQ-018/
HMIC-REQ-020): **OS filesystem write permission on the Protected Root**,
never an in-process authority check. Nothing in this script establishes
or substitutes for that permission.

Minimized human-entered authority-sensitive input (HBDC-REQ-057/058):
this script never accepts `--repository-id` or `--canonical-deployment-
root` — both are always derived read-only from `--repository-root`
(a neutral locator, exactly mirroring `scripts/hatp_certification_admin.
py`'s own `--repository-root` parameter shape). `--principal-id`/
`--signer-key-id`/`--authority-scope` are the only authority-sensitive
human input, drawn from the admin's own enrollment context (HBDC-REQ-058).
`provider_profile` is no longer a CLI flag as of Phase 149O.20L.7O.2F
(Surface E, HPSE-REQ-048): it is derived from the resolved SignerRecord,
and `--principal-id`/`--signer-key-id`/`--authority-scope` are now
cross-validated against the Principal/Signer/hardware-credential
registries and HBDC-001's closed vocabulary before any write (closing
149O.20L.7H's named, previously-deferred vocabulary-cross-validation
finding). `--election-reference`
(HBDC-REQ-064/065) is recorded as audit metadata only — this script
never accepts a bare `--approved` boolean and never itself
cryptographically verifies the referenced election.

No CLI first-use command (HBDC-REQ-069): this script performs create/
rotate/revoke exactly as directed; it never itself decides that a fresh
election has occurred, never mints a CHGR, and is not, and does not
become, a first-use election mechanism merely by existing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from pcae.core.hatp_bootstrap import HATPTrustStoreError
from pcae.core.hatp_deployment_binding_admin import (
    AuthorityEvidence,
    AuthorityEvidenceMalformedError,
    AuthorityEvidenceMissingError,
    DeploymentBindingNotFoundError,
    DeploymentBindingOperationResult,
    DeploymentBindingPreview,
    DeploymentBindingReadbackMismatchError,
    DeploymentBindingRevokedError,
    DeploymentBindingTrustStoreUnavailableError,
    DeploymentRootUnresolvableError,
    DuplicateConflictingBindingError,
    HATPDeploymentBindingAdminError,
    RepositoryIdentityMissingError,
    create_deployment_binding,
    preview_create_deployment_binding,
    preview_revoke_deployment_binding,
    preview_rotate_deployment_binding,
    revoke_deployment_binding,
    rotate_deployment_binding,
)
from pcae.core.repository_identity import RepositoryIdentityError

_HANDLED_ERRORS = (
    HATPDeploymentBindingAdminError,
    RepositoryIdentityError,
    HATPTrustStoreError,
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


def _describe_preview(preview: DeploymentBindingPreview, *, ceremony: str) -> str:
    lines = [
        f"{ceremony.upper()} DeploymentBinding for repository_id={preview.repository_id}",
        f"  canonical_deployment_root={preview.canonical_deployment_root}",
        f"  registry_path={preview.registry_path}",
        f"  computed outcome kind={preview.kind.value}",
    ]
    if preview.existing_binding is not None:
        lines.append(f"  existing entry: {preview.existing_binding}")
    if preview.candidate_binding is not None:
        lines.append(f"  candidate entry: {preview.candidate_binding}")
    return "\n".join(lines)


def _authority_from_args(args: argparse.Namespace) -> AuthorityEvidence:
    # Phase 149O.20L.7O.2F (Surface E, HPSE-REQ-048): `provider_profile`
    # is no longer accepted as independent caller input -- the producer
    # derives it from the resolved SignerRecord.provider_profile.
    return AuthorityEvidence(
        principal_id=args.principal_id,
        signer_key_id=args.signer_key_id,
        authority_scope=args.authority_scope,
        election_reference=args.election_reference,
    )


def _report_result(result: DeploymentBindingOperationResult) -> None:
    print(f"outcome={result.outcome.value} repository_id={result.binding.repository_id}")
    print(f"  canonical_deployment_root={result.binding.canonical_deployment_root}")
    print(f"  principal_id={result.binding.principal_id} status={result.binding.status}")
    print(f"  valid_from={result.binding.valid_from} revoked_at={result.binding.revoked_at}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hatp_deployment_binding_admin.py",
        description=(
            "Protected-admin HBDC-001 v1.1 DeploymentBinding create/rotate/revoke ceremony. "
            "Not reachable from the ordinary pcae CLI or any agent-executed code path (HBDC-REQ-056/066). "
            "Requires real OS write access to HATPTrustStore.production().root."
        ),
    )
    sub = parser.add_subparsers(dest="ceremony", required=True)

    def _add_authority_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd).")
        p.add_argument("--principal-id", required=True, help="Admin enrollment context (HBDC-REQ-058).")
        p.add_argument("--signer-key-id", required=True, help="Admin enrollment context (HBDC-REQ-058).")
        p.add_argument(
            "--authority-scope",
            required=True,
            help=(
                "Admin enrollment context (HBDC-REQ-058); validated against HBDC-001 v1.2's closed "
                "vocabulary (HBDC-REQ-072/074). provider_profile is no longer a CLI flag as of Phase "
                "149O.20L.7O.2F -- it is derived from the resolved SignerRecord."
            ),
        )
        p.add_argument(
            "--election-reference",
            required=True,
            help="Evidence reference (e.g. a CHGR id) for a fresh, separate human election (HBDC-REQ-064/065). "
            "Recorded as audit metadata only -- never cryptographically verified by this script.",
        )
        p.add_argument("--assume-yes", action="store_true", help="Skip the interactive confirmation prompt.")
        p.add_argument("--preview", action="store_true", help="Compute and print the target only; never writes.")

    create_parser = sub.add_parser("create", help="Create a new DeploymentBinding (idempotent-preserve on an identical active entry).")
    _add_authority_args(create_parser)

    rotate_parser = sub.add_parser("rotate", help="In-place overwrite the sole active entry's mutable fields.")
    _add_authority_args(rotate_parser)

    revoke_parser = sub.add_parser("revoke", help="Field-mutate the sole entry to status=revoked (never deletes).")
    revoke_parser.add_argument("--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd).")
    revoke_parser.add_argument(
        "--election-reference",
        required=True,
        help="Evidence reference (e.g. a CHGR id) for this revocation. Recorded as audit metadata only.",
    )
    revoke_parser.add_argument("--assume-yes", action="store_true")
    revoke_parser.add_argument("--preview", action="store_true", help="Compute and print the target only; never writes.")

    return parser


def main(argv: "Optional[list]" = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        if args.ceremony == "create":
            authority = _authority_from_args(args)
            if args.preview:
                preview = preview_create_deployment_binding(repository_root=args.repository_root, authority=authority)
                print(_describe_preview(preview, ceremony="create"))
                return 0
            preview = preview_create_deployment_binding(repository_root=args.repository_root, authority=authority)
            confirmed = args.assume_yes or _prompt_confirm(_describe_preview(preview, ceremony="create"))
            if not confirmed:
                raise ConfirmationDeclinedError("create was not confirmed by the operator; no write occurred")
            result = create_deployment_binding(repository_root=args.repository_root, authority=authority)
            _report_result(result)
        elif args.ceremony == "rotate":
            authority = _authority_from_args(args)
            if args.preview:
                preview = preview_rotate_deployment_binding(repository_root=args.repository_root, authority=authority)
                print(_describe_preview(preview, ceremony="rotate"))
                return 0
            preview = preview_rotate_deployment_binding(repository_root=args.repository_root, authority=authority)
            confirmed = args.assume_yes or _prompt_confirm(_describe_preview(preview, ceremony="rotate"))
            if not confirmed:
                raise ConfirmationDeclinedError("rotate was not confirmed by the operator; no write occurred")
            result = rotate_deployment_binding(repository_root=args.repository_root, authority=authority)
            _report_result(result)
        else:
            if args.preview:
                preview = preview_revoke_deployment_binding(repository_root=args.repository_root)
                print(_describe_preview(preview, ceremony="revoke"))
                return 0
            preview = preview_revoke_deployment_binding(repository_root=args.repository_root)
            confirmed = args.assume_yes or _prompt_confirm(_describe_preview(preview, ceremony="revoke"))
            if not confirmed:
                raise ConfirmationDeclinedError("revoke was not confirmed by the operator; no write occurred")
            result = revoke_deployment_binding(
                repository_root=args.repository_root, election_reference=args.election_reference
            )
            _report_result(result)
    except ConfirmationDeclinedError as exc:
        print(f"ABORTED: {exc}", file=sys.stderr)
        return 1
    except (
        RepositoryIdentityMissingError,
        DeploymentRootUnresolvableError,
        AuthorityEvidenceMalformedError,
        AuthorityEvidenceMissingError,
        DeploymentBindingTrustStoreUnavailableError,
        DuplicateConflictingBindingError,
        DeploymentBindingNotFoundError,
        DeploymentBindingRevokedError,
        DeploymentBindingReadbackMismatchError,
    ) + _HANDLED_ERRORS as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
