"""``pcae cltr shadow ...`` — read-only production shadow CLTR CLI (Phase 135K).

Every subcommand here is strictly read-only: it never creates a
generation, never repairs the current pointer, never replays shadow
integration, never mutates lifecycle state, never promotes a report, never
dispatches a notification, and never creates a marker or receipt. Every
JSON payload discloses ``shadow_mode``/``authoritative``/``mutation``.
"""

from __future__ import annotations

import argparse
import json

from pcae.cltr import inspection
from pcae.cltr.shadow import is_shadow_enabled

_DISCLOSURE_LINE = "[shadow, non-authoritative, derivative — production lifecycle authority unchanged]"


def _print(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    print(_DISCLOSURE_LINE)
    for key in sorted(payload):
        print(f"  {key}: {payload[key]}")


def run_cltr_shadow_show(args: argparse.Namespace) -> int:
    if getattr(args, "latest", False):
        payload = inspection.show_latest()
    elif getattr(args, "phase_id", None):
        payload = inspection.show_phase(args.phase_id)
    else:
        print("error: pcae cltr shadow show requires --latest or --phase-id")
        return 2
    _print(payload, getattr(args, "json", False))
    return 0 if payload.get("found") else 1


def run_cltr_shadow_verify(args: argparse.Namespace) -> int:
    payload = inspection.verify_latest()
    _print(payload, getattr(args, "json", False))
    return 0 if payload.get("verified") else 1


def run_cltr_shadow_list(args: argparse.Namespace) -> int:
    payload = inspection.list_shadow_generations(limit=getattr(args, "limit", None))
    _print(payload, getattr(args, "json", False))
    return 0


def run_cltr_shadow_reconcile(args: argparse.Namespace) -> int:
    payload = inspection.reconcile(args.phase_id)
    _print(payload, getattr(args, "json", False))
    return 0 if not payload.get("blockers") else 1


def run_cltr_shadow_status(args: argparse.Namespace) -> int:
    payload = {
        "feature_flag": "PCAE_CLTR_SHADOW_ENABLED",
        "enabled": is_shadow_enabled(),
        "shadow_mode": True,
        "authoritative": False,
        "mutation": "none",
    }
    _print(payload, getattr(args, "json", False))
    return 0
