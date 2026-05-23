from __future__ import annotations

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
