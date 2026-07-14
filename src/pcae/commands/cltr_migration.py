"""``pcae cltr migration ...`` — read-only Stage 1 dual-derivation CLI
(Phase 135O). Every subcommand here is strictly read-only, matching the
``pcae cltr shadow ...`` convention (135K)."""

from __future__ import annotations

import argparse
import json

from pcae.cltr.migration import reconciliation, status
from pcae.cltr.migration.rehearsal import reconciliation as rehearsal_reconciliation
from pcae.cltr.migration.rehearsal import status as rehearsal_status

_DISCLOSURE_LINE = "[migration evidence only, non-authoritative — production lifecycle authority (legacy) unchanged]"
_REHEARSAL_DISCLOSURE_LINE = (
    "[Stage 2 rehearsal evidence only, non-authoritative — rehearsal generation and pointer are never "
    "production authority; production lifecycle authority (legacy) unchanged]"
)


def _print(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    print(_DISCLOSURE_LINE)
    for key in sorted(payload):
        print(f"  {key}: {payload[key]}")


def run_cltr_migration_status(args: argparse.Namespace) -> int:
    payload = status.migration_status()
    _print(payload, getattr(args, "json", False))
    return 0 if not payload.get("blockers") else 1


def run_cltr_migration_reconcile(args: argparse.Namespace) -> int:
    payload = reconciliation.reconcile(args.phase_id)
    _print(payload, getattr(args, "json", False))
    return 0 if not payload.get("blockers") else 1


def _print_rehearsal(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    print(_REHEARSAL_DISCLOSURE_LINE)
    for key in sorted(payload):
        print(f"  {key}: {payload[key]}")


def run_cltr_migration_rehearsal_status(args: argparse.Namespace) -> int:
    payload = rehearsal_status.rehearsal_status()
    _print_rehearsal(payload, getattr(args, "json", False))
    return 0 if not payload.get("blockers") else 1


def run_cltr_migration_rehearsal_reconcile(args: argparse.Namespace) -> int:
    payload = rehearsal_reconciliation.reconcile(args.phase_id)
    _print_rehearsal(payload, getattr(args, "json", False))
    return 0 if not payload.get("blockers") else 1
