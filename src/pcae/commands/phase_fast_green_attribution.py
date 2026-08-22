"""`pcae phase fast-green-attribution` -- Phase 149O.20L.7O.2R.

Real CLI implementation of the controlled baseline-vs-candidate Fast Green
comparison designed in 149O.20L.7O.2Q and frozen in 149O.20L.7O.2Q.1.
Produces machine-produced structured attribution evidence -- see
`pcae.core.fast_green_attribution` for the evidence model and the
validator consumed by `validate_derived_correctness()`.
"""

from __future__ import annotations

import argparse
import json

from pcae.core.fast_green_attribution import (
    AttributionError,
    build_attribution_evidence,
    current_head,
    persist_evidence,
    resolve_repo_root,
    validate_structured_fast_green,
)
from pcae.core.paths import HarnessPath


def run_phase_fast_green_attribution(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    repo_root = resolve_repo_root(str(root.path))

    phase_id = args.phase_id
    pushed_status = args.pushed_status or "local_only"
    rerun_nodes = list(args.rerun_node or [])

    try:
        candidate = current_head(repo_root)
        evidence = build_attribution_evidence(
            repo_root=repo_root,
            phase_id=phase_id,
            pushed_status=pushed_status,
            rerun_node_ids=rerun_nodes,
            candidate_commit=candidate,
            timeout=args.timeout,
        )
        structured_value = persist_evidence(repo_root, evidence)
    except AttributionError as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        else:
            print(f"FAST GREEN ATTRIBUTION -- ERROR\n{exc}")
        return 2

    issues = validate_structured_fast_green(
        structured_value, repo_root=repo_root, phase_id=phase_id, pushed_status=pushed_status,
    )
    verdict = "PASS" if not issues else "FAIL"

    raw_total = len(evidence["raw_failed"]) + len(evidence["raw_errors"])
    attributable = len(evidence["attributable_failures"])
    preexisting = len(evidence["excluded_preexisting_failures"])
    environment = len(evidence["excluded_environment_failures"])
    expected = len(evidence["expected_phase_artifacts"])

    if args.json:
        print(json.dumps({
            "status": verdict,
            "issues": issues,
            "baseline_commit": evidence["baseline_commit"],
            "candidate_commit": evidence["candidate_commit"],
            "raw_failed_count": len(evidence["raw_failed"]),
            "raw_errors_count": len(evidence["raw_errors"]),
            "attributable_failures": evidence["attributable_failures"],
            "excluded_preexisting_failures": evidence["excluded_preexisting_failures"],
            "excluded_environment_failures": evidence["excluded_environment_failures"],
            "expected_phase_artifacts": evidence["expected_phase_artifacts"],
            "fast_green": structured_value,
        }, indent=2))
    else:
        print("FAST GREEN ATTRIBUTION")
        print(f"  Baseline:      {evidence['baseline_commit']} ({evidence['baseline_method']})")
        print(f"  Candidate:     {evidence['candidate_commit']}")
        print(f"  Raw failures:  {raw_total} ({len(evidence['raw_failed'])} failed / {len(evidence['raw_errors'])} errors)")
        print(f"  Attributable:  {attributable}")
        print(f"  Pre-existing:  {preexisting}")
        print(f"  Environment:   {environment}")
        print(f"  Expected art.: {expected}")
        print(f"  Verdict:       {verdict}")
        if issues:
            print("  Issues:")
            for issue in issues:
                print(f"    - {issue}")
        print()
        print(
            "  Structured evidence value (embed as "
            "test_results['fast_green']):"
        )
        print("  " + json.dumps(structured_value, sort_keys=True)[:200] + " ...")
        print(f"  Full evidence artifact: {structured_value['provenance']['artifact_path']}")

    return 0 if verdict == "PASS" else 1
