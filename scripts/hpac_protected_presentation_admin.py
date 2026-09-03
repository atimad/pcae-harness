#!/usr/bin/env python3
"""HPAC-PPA-001 v1.0 out-of-band protected-presentation-mechanism
administration — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1.

`docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` §5
(HPAC-PPA-REQ-021..027 / §15).

**Standalone script, deliberately outside `src/pcae/`.** Never imported by
`cli.py`, `commands/**`, `core/agent.py`, or any other agent-reachable code
path (HPAC-PPA-REQ-053, mirroring `scripts/hpac_protected_root_admin.py`
exactly). Not packaged, not a console-script entry point, not a `pcae` CLI
subcommand. It calls **only** the exact admin module
`pcae.core.hpac_protected_presentation_admin` (HPAC-PPA-REQ-053). Invoked
manually,

    # the deployment owner first installs the fixed helper bytes OUT OF BAND
    # at the derived content-addressed path, then registers the metadata:
    python scripts/hpac_protected_presentation_admin.py install \\
        --helper-sha256 <64-hex> --helper-version <id> \\
        --verifier-config-digest <64-hex> \\
        --renderer-profile <id> --descriptor-version <id>
    python scripts/hpac_protected_presentation_admin.py rotate  ... (same flags)
    python scripts/hpac_protected_presentation_admin.py revoke
    python scripts/hpac_protected_presentation_admin.py status

by an operator logged in as the deployment owner — the only OS principal
with real write access to the protected root (HPAC-PAWA-REQ-010, the real
security boundary; never an in-process check). The recognition path itself
resolves the FIXED compiled-in protected root and takes no caller override
(HPAC-PPA-REQ-009); this script has no `--protected-root` flag.

It registers and pins **metadata only** (HPAC-PPA-REQ-004): it never copies,
replaces, chmods, chowns, packages, downloads, or executes helper bytes,
launches no helper, and writes no presentation evidence.
"""
from __future__ import annotations

import argparse
import sys

from pcae.core.hpac_protected_presentation_admin import (
    ProtectedPresentationAdminError,
    configure_presentation_mechanism,
    resolve_current_presentation_generation,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hpac_protected_presentation_admin.py",
        description=(
            "Out-of-band HPAC-PPA-001 v1.0 protected-presentation-mechanism configuration. Not "
            "reachable from the ordinary pcae CLI or any agent-executed code path (HPAC-PPA-REQ-053). "
            "Requires real OS write access to the HPAC protected root. Registers metadata only; the "
            "helper executable is installed out of band."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _config_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument("--helper-sha256", required=True, help="SHA-256 (64 lowercase hex) of the complete out-of-band-installed helper byte stream.")
        p.add_argument("--helper-version", required=True, help="Non-empty helper implementation version identifier.")
        p.add_argument("--verifier-config-digest", required=True, help="SHA-256 (64 lowercase hex) of the protected verifier configuration.")
        p.add_argument("--renderer-profile", required=True, help="Versioned deterministic renderer-profile identifier.")
        p.add_argument("--descriptor-version", required=True, help="Non-empty HPAC-REQ-090 descriptor version identifier.")

    ins = sub.add_parser("install", help="Register generation 1 metadata for the out-of-band-installed helper (HPAC-PPA-REQ-021/024).")
    _config_flags(ins)

    rot = sub.add_parser("rotate", help="Register the next generation for new out-of-band helper bytes (HPAC-PPA-REQ-025).")
    _config_flags(rot)

    sub.add_parser("revoke", help="Revoke the current generation; production presentation is unavailable until reinstall (HPAC-PPA-REQ-026).")
    sub.add_parser("status", help="Read-only: show the current resolved generation.")
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command in ("install", "rotate"):
            resolved = configure_presentation_mechanism(
                action=args.command,
                helper_sha256=args.helper_sha256,
                helper_implementation_version=args.helper_version,
                verifier_configuration_digest=args.verifier_config_digest,
                renderer_profile=args.renderer_profile,
                descriptor_version=args.descriptor_version,
            )
            print(
                f"{args.command} ok: mechanism={resolved.record.mechanism_id} "
                f"installation_id={resolved.anchor.installation_id} "
                f"generation={resolved.anchor.current_generation} "
                f"descriptor_digest={resolved.record.descriptor_digest}"
            )
        elif args.command == "revoke":
            resolved = configure_presentation_mechanism(action="revoke")
            print(
                f"revoke ok: installation_id={resolved.anchor.installation_id} "
                f"generation={resolved.anchor.current_generation} status={resolved.anchor.status}"
            )
        else:  # status
            from pcae.core.hpac_foundation import HPACStoreAuthority

            resolved = resolve_current_presentation_generation(HPACStoreAuthority.production())
            if resolved is None:
                print("status: no presentation-mechanism installation")
            else:
                print(
                    f"status: installation_id={resolved.anchor.installation_id} "
                    f"generation={resolved.anchor.current_generation} "
                    f"helper_path={resolved.helper_path} "
                    f"helper_sha256={resolved.record.helper_sha256}"
                )
    except ProtectedPresentationAdminError as exc:
        code = f" ({exc.pawa_code})" if exc.pawa_code else ""
        print(f"ERROR: {exc}{code}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: OSError: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
