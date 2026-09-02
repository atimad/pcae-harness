#!/usr/bin/env python3
"""HPAC-PAWA-001 v1.1 out-of-band protected-root administration —
Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 (Slice 1).
`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
§23 / §32B / §38 / §50 / §51.

**Standalone script, deliberately outside `src/pcae/`.** Never imported by
`cli.py`, `commands/**`, `core/agent.py`, or any other agent-reachable
code path (HPAC-PAWA-REQ-084/085, mirroring
`scripts/hatp_deployment_binding_admin.py` exactly). Not packaged, not a
console-script entry point, not a `pcae` CLI subcommand. Invoked manually,

    python scripts/hpac_protected_root_admin.py provision \\
        --protected-root /etc/pcae/hpac/protected-root \\
        --agent-account pcae-agent-svc
    python scripts/hpac_protected_root_admin.py set-agent-exclusion \\
        --protected-root ... --agent-account new-svc-account
    python scripts/hpac_protected_root_admin.py rotate  --protected-root ...
    python scripts/hpac_protected_root_admin.py revoke  --protected-root ...
    python scripts/hpac_protected_root_admin.py enroll-principal \\
        --protected-root ... --principal-id hp-<hex> \\
        --enrollment-provenance-ref <ref>
    python scripts/hpac_protected_root_admin.py revoke-principal \\
        --protected-root ... --principal-id hp-<hex>

by an operator logged in as the deployment owner — the only OS principal
with real write access to the protected root (HPAC-PAWA-REQ-010, the real
security boundary; never an in-process check). `--protected-root` locates
an *already-protected* out-of-band location; it is never a caller
*authority* input on the recognition path (§29 — the `production_writer`
path itself resolves the fixed compiled-in root and takes no override).

`--agent-account` is the explicit protected-administration input for
`symbolic_account` (HPAC-PAWA-REQ-195): the account is resolved by this
tool against the OS account database — never inferred from `USER` /
`LOGNAME` / `SUDO_USER` / the current euid / a logical agent-id label.

FIDO2-free (Slice 1): no credential enrollment, no RHAMP ceremony, no
sidecar, no hardware.
"""
from __future__ import annotations

import argparse
import pwd
import sys
from pathlib import Path

from pcae.core.hpac_protected_admin_writer import (
    PawaError,
    ProvisioningError,
    enroll_principal_via_pawa,
    provision_protected_root,
    revoke_anchor,
    revoke_principal_via_pawa,
    rotate_descriptor,
    set_agent_exclusion,
)


def _resolve_account_uid(account: str) -> int:
    """Resolve the administrator-selected account name against the trusted
    OS account database (HPAC-PAWA-REQ-181 / §32B.2). Fails closed."""

    try:
        return pwd.getpwnam(account).pw_uid
    except KeyError:
        raise SystemExit(f"ERROR: OS account {account!r} is unknown to the account database")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hpac_protected_root_admin.py",
        description=(
            "Out-of-band HPAC-PAWA-001 v1.1 protected-root administration. Not reachable from the "
            "ordinary pcae CLI or any agent-executed code path (HPAC-PAWA-REQ-084/085). Requires real "
            "OS write access to the HPAC protected root."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _root_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument("--protected-root", type=Path, required=True, help="Already-protected out-of-band location.")

    prov = sub.add_parser("provision", help="One-time bootstrap: root + manifest + descriptor@1 + current-generation@1 + agent-exclusion.")
    _root_arg(prov)
    prov.add_argument("--agent-account", required=True, help="OS account name of the configured PCAE agent principal (§32B.2).")

    sae = sub.add_parser("set-agent-exclusion", help="Rotate the configured-agent OS account binding (§32B.4).")
    _root_arg(sae)
    sae.add_argument("--agent-account", required=True)

    rot = sub.add_parser("rotate", help="Explicit descriptor rotation, generation += 1 (§50).")
    _root_arg(rot)

    rev = sub.add_parser("revoke", help="Revoke the anchor; recognition fails closed until re-provision (§51).")
    _root_arg(rev)

    ep = sub.add_parser("enroll-principal", help="Bounded protected principal administration: enroll one PrincipalRecord (§38 cat. 1).")
    ep.add_argument("--principal-id", required=True)
    ep.add_argument("--enrollment-provenance-ref", required=True)

    rp = sub.add_parser("revoke-principal", help="Bounded protected principal administration: revoke one PrincipalRecord.")
    rp.add_argument("--principal-id", required=True)

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "provision":
            uid = _resolve_account_uid(args.agent_account)
            out = provision_protected_root(
                protected_root=args.protected_root, agent_account=args.agent_account, agent_uid=uid
            )
            print(f"provisioned anchor_id={out['anchor_id']} installation_id={out['installation_id']} generation=1")
            print(f"  symbolic_account={out['symbolic_account']} provisioned_uid={out['provisioned_uid']}")
        elif args.command == "set-agent-exclusion":
            uid = _resolve_account_uid(args.agent_account)
            out = set_agent_exclusion(
                protected_root=args.protected_root, agent_account=args.agent_account, agent_uid=uid
            )
            print(f"agent-exclusion rotated: generation={out['generation']} symbolic_account={out['symbolic_account']}")
        elif args.command == "rotate":
            out = rotate_descriptor(protected_root=args.protected_root)
            print(f"descriptor rotated: generation={out['generation']}")
        elif args.command == "revoke":
            out = revoke_anchor(protected_root=args.protected_root)
            print(f"anchor revoked: state={out['state']} generation={out['generation']}")
        elif args.command == "enroll-principal":
            # §29 — the recognition path resolves the FIXED compiled-in
            # protected root; no caller root override.
            rec = enroll_principal_via_pawa(
                principal_id=args.principal_id,
                enrollment_provenance_ref=args.enrollment_provenance_ref,
            )
            print(f"enrolled principal_id={rec.principal_id} status={rec.status}")
        else:  # revoke-principal
            rec = revoke_principal_via_pawa(principal_id=args.principal_id)
            print(f"revoked principal_id={rec.principal_id} status={rec.status}")
    except (PawaError, ProvisioningError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: OSError: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
