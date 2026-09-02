#!/usr/bin/env python3
"""RHAMP-001 v1.0 §13 / §14 / §16 / §61 — out-of-band protected-admin
credential enrollment + first-credential bootstrap + revocation ceremony.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156 ``.1R.30``
bundle).

**Standalone script, deliberately outside ``src/pcae/``** (RHAMP-REQ-150,
HPAC-PAWA-REQ-084/085). Never imported by ``cli.py``, ``commands/**``,
``core/agent.py``, or any agent-reachable code path. Not packaged, not a
console-script entry point, not a ``pcae`` CLI subcommand. Not an agent
tool. Not plugin / runtime callable. No arbitrary shell. Invoked manually,

    python scripts/hpac_principal_admin.py enroll-first-credential \\
        --principal-id hp-<hex> \\
        --subject-digest <hex64> --presentation-digest <hex64> \\
        --invocation-id iv-<...> --attempt-id at-<...>
    python scripts/hpac_principal_admin.py revoke-credential \\
        --credential-id hpc-<hex>

by an operator logged in as the deployment owner — the only OS principal
with real write access to ``<HPAC_PROTECTED_ROOT>`` (HPAC-PAWA-REQ-010,
the real security boundary). Credential enrollment / revocation authority
originates **only** from the independently-verified Slice-1 PAWA
``production_writer`` boundary (RHAMP-REQ-047/049).

The CTAP2 ``authenticatorMakeCredential`` ceremony uses the **production
native provider** — a supported roaming USB-HID / NFC FIDO2 authenticator
with UP + UV must be attached. There is no ``--deterministic`` /
``--fixture`` flag: the deterministic NON_REAL provider is reachable only
from test code (RHAMP-REQ-048 / §63).
"""
from __future__ import annotations

import argparse
import sys

from pcae.core.hpac_rhamp_enrollment import (
    RhampEnrollmentError,
    enroll_first_credential,
    revoke_credential,
)
from pcae.core.hpac_rhamp_ctap2 import Ctap2CancelledError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hpac_principal_admin.py",
        description=(
            "Out-of-band RHAMP-001 v1.0 protected-admin credential enrollment / bootstrap / "
            "revocation. Not reachable from the ordinary pcae CLI or any agent-executed code "
            "path (HPAC-PAWA-REQ-084/085). Requires real OS write access to the HPAC protected "
            "root and an attached roaming CTAP2 authenticator (USB-HID / NFC, UP + UV)."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    enr = sub.add_parser(
        "enroll-first-credential",
        help="RHAMP-REQ-043/047/048 — enroll the first (or an additional) canonical FIDO2 credential "
        "for an existing active PrincipalRecord.",
    )
    enr.add_argument("--principal-id", required=True)
    enr.add_argument("--subject-digest", required=True, help="Canonical approval-subject digest (hex64).")
    enr.add_argument("--presentation-digest", required=True, help="Trusted presentation digest (hex64).")
    enr.add_argument("--invocation-id", required=True)
    enr.add_argument("--attempt-id", required=True)

    rev = sub.add_parser(
        "revoke-credential",
        help="RHAMP-REQ-116 — PAWA-authorized revocation of one CredentialRecord.",
    )
    rev.add_argument("--credential-id", required=True)

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "enroll-first-credential":
            result = enroll_first_credential(
                principal_id=args.principal_id,
                subject_digest=args.subject_digest,
                presentation_digest=args.presentation_digest,
                invocation_id=args.invocation_id,
                attempt_id=args.attempt_id,
            )
            print(
                f"enrolled credential_id={result.credential_id} principal_id={result.principal_id} "
                f"mechanism_id={result.mechanism_id} transports={','.join(result.transports)}"
            )
            print(
                f"  raw_credential_id_digest={result.raw_credential_id_digest} "
                f"evidence={result.enrollment_evidence_ref}"
            )
        else:  # revoke-credential
            record = revoke_credential(credential_id=args.credential_id)
            print(f"revoked credential_id={record.credential_id} status={record.status}")
    except Ctap2CancelledError as exc:
        print(f"ERROR: ceremony cancelled/timed out: {exc}", file=sys.stderr)
        return 1
    except RhampEnrollmentError as exc:
        print(
            f"ERROR: {exc.terminal_reason_code} ({exc.human_visible_category}): {exc.detail}",
            file=sys.stderr,
        )
        return 1
    except OSError as exc:
        print(f"ERROR: OSError: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
