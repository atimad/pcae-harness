"""``pcae cltr migration ...`` — read-only Stage 1 dual-derivation CLI
(Phase 135O). Every subcommand here is strictly read-only, matching the
``pcae cltr shadow ...`` convention (135K)."""

from __future__ import annotations

import argparse
import json

from pcae.cltr.migration import reconciliation, status
from pcae.cltr.migration.rehearsal import reconciliation as rehearsal_reconciliation
from pcae.cltr.migration.rehearsal import rollback as rehearsal_rollback
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


def run_cltr_migration_rehearsal_rollback_status(args: argparse.Namespace) -> int:
    payload = rehearsal_rollback.rollback_status(args.phase_id)
    _print_rehearsal(payload, getattr(args, "json", False))
    return 0 if not payload.get("blockers") else 1


def run_cltr_migration_rehearsal_rollback(args: argparse.Namespace) -> int:
    """Phase 135U -- the sole mutating rollback-rehearsal entry point.
    Operator-initiated only: no finalization caller, recovery path, or
    read-only status/reconcile command ever invokes this. Resolves
    ``transition_id``/``migration_epoch``/``authority_epoch`` from the
    same explicit, verified evidence ``rollback-status``/``reconcile``
    already use -- never from newest/oldest file, timestamps, titles, or
    Git history."""

    from pcae.cltr.migration.rehearsal.persistence import DEFAULT_MIGRATION_ROOT
    from pcae.cltr.migration.rehearsal.reconciliation import _find_rehearsal_transitions_for_phase

    matches = _find_rehearsal_transitions_for_phase(DEFAULT_MIGRATION_ROOT, args.phase_id)
    if not matches:
        _print_rehearsal({"error": f"no rehearsal evidence exists for phase_id {args.phase_id!r}"}, getattr(args, "json", False))
        return 1
    if len(matches) != 1:
        _print_rehearsal(
            {"error": f"phase_id {args.phase_id!r} resolves to {len(matches)} rehearsal transitions; rollback requires an unambiguous single transition"},
            getattr(args, "json", False),
        )
        return 1

    match = matches[0]
    request = rehearsal_rollback.build_rollback_request(
        phase_id=args.phase_id,
        transition_id=match["transition_id"],
        migration_epoch=match["migration_epoch"],
        authority_epoch=match["manifest"].get("authority_epoch"),
        target_rehearsal_generation_id=args.target_generation,
        reason=args.reason or "operator-requested rollback rehearsal",
    )
    result = rehearsal_rollback.execute_rollback(request=request)
    payload = {
        "outcome": result.outcome.value,
        "rollback_request_id": result.rollback_request_id,
        "source_rehearsal_generation_id": result.source_rehearsal_generation_id,
        "target_rehearsal_generation_id": result.target_rehearsal_generation_id,
        "limitations": list(result.limitations),
    }
    _print_rehearsal(payload, getattr(args, "json", False))
    return 0 if result.outcome.value in ("rollback_published", "rollback_verified", "rollback_idempotent_replay") else 1
