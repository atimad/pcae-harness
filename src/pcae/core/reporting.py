from __future__ import annotations

import json

from pcae.core.inspect import InspectionResult


def format_inspection(result: InspectionResult) -> str:
    lines = [f"PCAE inspection for {result.root.path}", ""]

    categories = tuple(dict.fromkeys(path.entry.category for path in result.paths))
    for category in categories:
        lines.append(f"{category}:")
        for inspected in result.paths:
            if inspected.entry.category != category:
                continue
            status = "present" if inspected.present else "missing"
            lines.append(f"  [{status}] {inspected.relative_path.as_posix()}")
        lines.append("")

    policy_status = "present" if result.policy.present else "missing"
    lines.append("Policy:")
    lines.append(f"  [{policy_status}] {result.policy.relative_path.as_posix()}")
    lines.append(f"  source: {result.policy.source}")
    validation = "valid" if result.policy.valid else "invalid"
    lines.append(f"  validation: {validation}")
    if result.policy.error is not None:
        lines.append(f"  error: {result.policy.error}")
    lines.append(
        f"  protected patterns: {result.policy.protected_pattern_count}"
    )
    lines.append("  architecture zones:")
    if result.policy.architecture_zones:
        for name, pattern_count in result.policy.architecture_zones.items():
            lines.append(f"    {name}: {pattern_count} patterns")
    else:
        lines.append("    none")
    lines.append(f"  architecture rules: {result.policy.architecture_rule_count}")
    lines.append("")

    if result.missing_paths:
        lines.append("Missing required PCAE paths:")
        for inspected in result.missing_paths:
            lines.append(f"  {inspected.relative_path.as_posix()}")
    else:
        lines.append("All required PCAE paths are present.")

    return "\n".join(lines)


def format_inspection_json(result: InspectionResult) -> str:
    return json.dumps(inspection_json_data(result), indent=2, sort_keys=True)


def inspection_json_data(result: InspectionResult) -> dict:
    missing_paths = [path.relative_path.as_posix() for path in result.missing_paths]
    status = "ok"
    if missing_paths or not result.policy.valid:
        status = "attention_required"

    return {
        "architecture": {
            "rules_count": result.policy.architecture_rule_count,
            "zones": result.policy.architecture_zones,
        },
        "check_scripts": category_paths(result, "Check scripts"),
        "hooks": category_paths(result, "Git hooks"),
        "overall_status": status,
        "policy": {
            "error": result.policy.error,
            "present": result.policy.present,
            "protected_pattern_count": result.policy.protected_pattern_count,
            "relative_path": result.policy.relative_path.as_posix(),
            "source": result.policy.source,
            "valid": result.policy.valid,
        },
        "required_files": category_paths(result, "Required files"),
        "root": str(result.root.path),
        "task_files": category_paths(result, "Task files"),
    }


def category_paths(result: InspectionResult, category: str) -> dict[str, list[str]]:
    inspected = tuple(path for path in result.paths if path.entry.category == category)
    return {
        "missing": [
            path.relative_path.as_posix()
            for path in inspected
            if not path.present
        ],
        "present": [
            path.relative_path.as_posix()
            for path in inspected
            if path.present
        ],
    }
