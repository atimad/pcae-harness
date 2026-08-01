"""``pcae aesic status`` -- Phase 147O.1 read-only Authority Evaluation
production-wiring diagnostics.

Narrow, read-only inspection surface (mirrors
``pcae.commands.architecture_status``'s discipline): reports whether
Authority Evaluation is configured/enabled in this repository
(AESIC-001 v1.3, ``pcae.aesic.composition``) and, optionally, the
current-effective Stage 2 reference for one named publication package.
Never mutates, never evaluates, never constructs a live
``AuthorityEvaluationService`` -- only
``describe_authority_evaluation_configuration`` (a directory listing)
and, when ``--package-id`` is supplied, ``pcae.aesic.diagnostics.
summarize_package`` (Phase 147M/147N's own pre-existing, never-wired
read-only diagnostics surface, AESIC-001 v1.3 §16/AESIC-REQ-097 --
reused here rather than duplicated). Both calls this module makes are
read-only, single-argument lookups already made elsewhere in production
(``AuthorityEvaluationService.evaluate_stage_2`` makes the same
``read_canonical(package_id)`` call ``summarize_package`` makes), so
this diagnostics surface adds no new caller shape and cannot expand
AESIC-N-01's reachability.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from pcae.aesic.composition import describe_authority_evaluation_configuration
from pcae.aesic.diagnostics import summarize_package
from pcae.aesic.storage import AuthorityEvaluationRecordStore

_STAGE_1_NOTE = (
    "not_persisted (advisory-only, no cross-process transport by design -- "
    "AESIC-001 v1.3 §5.2.1)"
)


def run_aesic_status(args: argparse.Namespace) -> int:
    status = describe_authority_evaluation_configuration()

    canonical: dict | None = None
    package_id = getattr(args, "package_id", None)
    if package_id:
        store = AuthorityEvaluationRecordStore(root=Path(status.aer_store_root))
        canonical = asdict(summarize_package(store, package_id))

    payload = {
        "enabled": status.enabled,
        "reason": status.reason,
        "template_root": status.template_root,
        "registry_root": status.registry_root,
        "aer_store_root": status.aer_store_root,
        "stage_1_last_status": _STAGE_1_NOTE,
        "package_id": package_id,
        "current_effective_stage_2": canonical,
    }

    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0

    print("Authority Evaluation status (AESIC-001 v1.3, Phase 147O.1 production wiring)")
    print(f"  Enabled: {status.enabled}")
    print(f"  Reason: {status.reason}")
    print(f"  Template root: {status.template_root}")
    print(f"  Registry root: {status.registry_root}")
    print(f"  AER store root: {status.aer_store_root}")
    print(f"  Stage 1 last status: {_STAGE_1_NOTE}")
    if package_id:
        print(f"  Current-effective Stage 2 ({package_id}): {canonical}")
    return 0


__all__ = ["run_aesic_status"]
