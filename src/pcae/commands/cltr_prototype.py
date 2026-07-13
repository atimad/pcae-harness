"""CLI wiring for the Phase 135F CLTR read-only prototype (135E §16).

Namespaced `pcae cltr-prototype ...`, deliberately distinct from any future
production `pcae cltr ...` command family, so no user or script could
mistake it for a production interface. Every subcommand here is read-only
except `generate`, whose only write path is `persistence.py`'s hardcoded
`.pcae/cltr-prototypes/` prefix. No subcommand completes a phase, promotes
an artifact, sends a notification, updates metadata, repairs production
state, changes task state, or authorizes execution.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

from pcae.cltr_prototype import comparison as comparison_mod
from pcae.cltr_prototype import generator as generator_mod
from pcae.cltr_prototype import persistence as persistence_mod
from pcae.cltr_prototype import verifier as verifier_mod
from pcae.cltr_prototype.canonicalization import record_from_dict, record_to_dict

_BOUNDARY_LINES = (
    "-- PROTOTYPE ONLY --",
    "This is a Phase 135F read-only prototype output. It is NOT a canonical",
    "phase report, NOT an authorization to proceed, and does not mutate any",
    "production lifecycle artifact.",
)


def _print_boundary_disclosure() -> None:
    for line in _BOUNDARY_LINES:
        print(line)
    print()


def _asdict_result(obj) -> dict:
    if dataclasses.is_dataclass(obj):
        return {f.name: _asdict_value(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    return obj


def _asdict_value(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _asdict_result(value)
    if isinstance(value, (list, tuple)):
        return [_asdict_value(v) for v in value]
    if hasattr(value, "value") and not isinstance(value, (str, int, float, bool)):
        return value.value
    return value


def run_cltr_prototype_generate(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: fixture input not found: {input_path}")
        return 1
    bundle = json.loads(input_path.read_text(encoding="utf-8"))

    try:
        result = generator_mod.generate(bundle)
    except generator_mod.GeneratorError as exc:
        if args.json:
            print(json.dumps({"error": type(exc).__name__, "detail": str(exc)}))
        else:
            print(f"Error: {type(exc).__name__}: {exc}")
        return 1

    gen_dir = persistence_mod.persist(result.record, result.invariant_results)

    fail_count = sum(1 for r in result.invariant_results if r.outcome.value == "fail")

    if args.json:
        print(
            json.dumps(
                {
                    "prototype_only": True,
                    "canonical": False,
                    "authorization": False,
                    "transition_id": result.record.identity.transition_id,
                    "phase_id": result.record.identity.phase_id,
                    "lifecycle_state": result.record.spine_state.value,
                    "record_digest": result.record.record_digest,
                    "invariant_summary": {"total": len(result.invariant_results), "fail": fail_count},
                    "generation_path": str(gen_dir),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if fail_count == 0 else 2

    _print_boundary_disclosure()
    print(f"transition_id:   {result.record.identity.transition_id}")
    print(f"phase_id:        {result.record.identity.phase_id}")
    print(f"lifecycle_state: {result.record.spine_state.value}")
    print(f"record_digest:   {result.record.record_digest}")
    print(f"invariants:      {len(result.invariant_results)} evaluated, {fail_count} failed")
    print(f"generation path: {gen_dir}")
    return 0 if fail_count == 0 else 2


def run_cltr_prototype_show(args: argparse.Namespace) -> int:
    record_dict = persistence_mod.read_generation(args.record)
    if record_dict is None:
        print(f"Error: no complete generation found for transition_id={args.record!r}")
        return 1

    if args.json:
        print(json.dumps(record_dict, indent=2, sort_keys=True))
        return 0

    _print_boundary_disclosure()
    for key in ("transition_id", "phase_id", "repository_identity", "branch_identity", "task_id"):
        print(f"{key}: {record_dict.get('identity', {}).get(key)}")
    print(f"spine_state: {record_dict.get('spine_state')}")
    print(f"record_digest: {record_dict.get('record_digest')}")
    print(f"limitations: {record_dict.get('limitations', [])}")
    return 0


def run_cltr_prototype_verify(args: argparse.Namespace) -> int:
    report = verifier_mod.verify_record(args.record)
    fail_count = sum(1 for r in report.invariant_results if r.outcome.value == "fail")

    if args.json:
        print(
            json.dumps(
                {
                    "prototype_only": True,
                    "canonical": False,
                    "authorization": False,
                    "transition_id": report.transition_id,
                    "phase_id": report.phase_id,
                    "lifecycle_state": report.lifecycle_state,
                    "digest_valid": report.digest_valid,
                    "manifest_consistent": report.manifest_consistent,
                    "state_valid": report.state_valid,
                    "conformance": report.conformance,
                    "terminal": report.terminal,
                    "invariant_summary": {"total": len(report.invariant_results), "fail": fail_count},
                    "invariant_results": [_asdict_result(r) for r in report.invariant_results],
                    "limitations": list(report.limitations),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if (report.digest_valid and fail_count == 0) else 2

    _print_boundary_disclosure()
    print(f"transition_id:       {report.transition_id}")
    print(f"lifecycle_state:     {report.lifecycle_state}")
    print(f"digest_valid:        {report.digest_valid}")
    print(f"manifest_consistent: {report.manifest_consistent}")
    print(f"conformance:         {report.conformance}")
    print(f"invariants:          {len(report.invariant_results)} evaluated, {fail_count} failed")
    if report.limitations:
        print(f"limitations:         {list(report.limitations)}")
    return 0 if (report.digest_valid and fail_count == 0) else 2


def run_cltr_prototype_compare(args: argparse.Namespace) -> int:
    record_dict = persistence_mod.read_generation(args.record)
    if record_dict is None:
        print(f"Error: no complete generation found for transition_id={args.record!r}")
        return 1
    record = record_from_dict(record_dict)

    manifest_path = Path(args.against)
    if not manifest_path.exists():
        print(f"Error: comparison target manifest not found: {manifest_path}")
        return 1
    targets = json.loads(manifest_path.read_text(encoding="utf-8"))

    report = comparison_mod.compare(record, targets)

    if args.json:
        print(
            json.dumps(
                {
                    "prototype_only": True,
                    "canonical": False,
                    "authorization": False,
                    "transition_id": report.transition_id,
                    "phase_id": report.phase_id,
                    "mixed_generation_detected": report.mixed_generation_detected,
                    "mixed_generation_detail": report.mixed_generation_detail,
                    "target_results": [_asdict_result(r) for r in report.target_results],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if not report.mixed_generation_detected else 2

    _print_boundary_disclosure()
    print(f"transition_id: {report.transition_id}")
    print(f"mixed_generation_detected: {report.mixed_generation_detected}")
    for target in report.target_results:
        print(f"  [{target.kind}] {target.classification} (source={target.source})")
        if target.limitation:
            print(f"    limitation: {target.limitation}")
    return 0 if not report.mixed_generation_detected else 2


def run_cltr_prototype_list(args: argparse.Namespace) -> int:
    generations = persistence_mod.list_generations()
    if args.json:
        print(json.dumps({"generations": generations}, indent=2, sort_keys=True))
        return 0
    _print_boundary_disclosure()
    if not generations:
        print("(no prototype generations found)")
    for transition_id in generations:
        print(f"  {transition_id}")
    return 0
