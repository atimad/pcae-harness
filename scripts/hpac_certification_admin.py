#!/usr/bin/env python3
"""HPAC-PAWA-001 v1.3 §38A — out-of-band N-16-5 real-human-authentication
**certification** administration.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R
(alias N16-5-H3-IMPL).
`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
§33A / §38A / §42B / §68A.

**Standalone script, deliberately outside `src/pcae/`.** Never imported by
`cli.py`, `commands/**`, `core/agent.py`, or any other agent-reachable code
path (HPAC-PAWA-REQ-241, mirroring `scripts/hpac_protected_presentation_admin.py`
and `scripts/hatp_certification_admin.py` exactly). Not packaged as a
console-script entry point, not a `pcae` CLI subcommand, not in any dispatch
table. It calls **only** the exact admin module
`pcae.core.hpac_certification_coordinator` (§38A / §39A). The recognition
path resolves the FIXED compiled-in protected root and takes no caller
override; this script has **no** `--protected-root` flag.

**This is a deliberately bounded admin/certification boundary, not a generic
admin shell (prompt §13).** It exposes no arbitrary subcommand execution, no
generic Python execution, no generic role selection, no generic writer
minting, no generic filesystem writes, no shell escape, no arbitrary module
import, and no arbitrary consumer selection. It provides **no**
`--approve` / `--yes` / stdin-injected approval and **no** `--pin` / stored
PIN (prompt §89/§90): the future real ceremony's human APPROVE is obtained
separately at the trusted protected presentation, and the FIDO2 assertion
comes from the genuine authenticator. There is no `--fake-real` flag.

Subcommands:

    describe   print the frozen §38A consumer identity + §42B closed
               five-role allowlist + the §68A walls (read-only, no root
               access).
    status     resolve and print the current HPAC-PAWA anchor generation
               (read-only protected-store resolution; mints nothing).

The end-to-end real certification ceremony (protected APPROVE → presentation
evidence → genuine YubiKey getAssertion → UP + UV → real assurance →
PRODUCTION principal → Gate 5 → N-16-5 closure adjudication) is performed by
the dedicated fresh-CPIPC-id phase **N16-5-FINAL-CERT**, not by this script
and not by this phase.
"""
from __future__ import annotations

import argparse
import json
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hpac_certification_admin.py",
        description=(
            "HPAC-PAWA-001 v1.3 §38A out-of-band N-16-5 certification administration "
            "(bounded; no approval injection, no PIN, no arbitrary role/subcommand)."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("describe", help="print the frozen §38A / §42B / §68A boundary (read-only)")
    sub.add_parser("status", help="resolve and print the current HPAC-PAWA anchor generation (read-only)")
    return parser


def _cmd_describe() -> int:
    from pcae.core.hpac_protected_admin_writer import (
        CERTIFICATION_FACTORY_CONSUMERS,
        CERTIFICATION_ROLE_ALLOWLIST,
        CERTIFICATION_COUNTER_ROLE,
    )

    payload = {
        "contract": "HPAC-PAWA-001 v1.3",
        "authorized_certification_consumer": sorted(CERTIFICATION_FACTORY_CONSUMERS),
        "certification_role_allowlist": sorted(CERTIFICATION_ROLE_ALLOWLIST),
        "counter_role_subject": "credential_id",
        "lifecycle_role_subject": "proof_id",
        "explicitly_denied_roles": [
            "hpac_lifecycle_terminator",
            "<wildcard>",
            "<prefix>",
            "<arbitrary string>",
        ],
        "walls": [
            "certification authority != execution authority (no Gate 6-10, no DispatchEnvelope, no no-go override)",
            "no runtime approval / PB permission / policy exception / RE result / runtime capability / adapter admission",
            "coordinator does not manufacture APPROVE/REJECT/UP/UV/real presentation/real assertion",
            "coordinator does not construct a PRODUCTION AuthenticatedHumanPrincipal (verify_human_authentication does)",
            "Gate 5 is not manufactured and not bypassed; deterministic input never becomes REAL assurance",
            "path terminates no later than the bounded Gate-5 certification result",
        ],
        "real_ceremony_performed_by": "N16-5-FINAL-CERT (fresh CPIPC id; not this script, not this phase)",
    }
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _cmd_status() -> int:
    try:
        from pcae.core.hpac_foundation import HPACStoreAuthority
        from pcae.core.hpac_pawa_schemas import validate_current_generation
        from pcae.core.hpac_foundation import read_canonical_json_document

        authority = HPACStoreAuthority.production()
        cg_path = authority.root / ".authority" / "current-generation.json"
        record = validate_current_generation(read_canonical_json_document(cg_path))
        payload = {
            "installation_id": record.installation_id,
            "current_generation": record.current_generation,
        }
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except Exception as exc:  # noqa: BLE001 — a bounded read tool; report and exit non-zero
        sys.stderr.write(f"status unavailable: {type(exc).__name__}: {exc}\n")
        return 2


def main(argv: "list[str] | None" = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "describe":
        return _cmd_describe()
    if args.command == "status":
        return _cmd_status()
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
