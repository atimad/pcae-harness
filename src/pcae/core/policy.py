from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.paths import HarnessPath

POLICY_RELATIVE_PATH = Path(".pcae") / "policy.toml"
POLICY_SOURCE_REPO = "repo config"
POLICY_SOURCE_DEFAULTS = "built-in defaults"

DEFAULT_PROTECTED_PATTERNS = (
    ".git/**",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "**/__pycache__/**",
    ".venv/**",
    "venv/**",
    "node_modules/**",
    "pyproject.toml",
    "poetry.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Cargo.toml",
    "Cargo.lock",
)

DEFAULT_ARCHITECTURE_ZONES = {
    "core": ("src/pcae/core/**",),
    "commands": ("src/pcae/commands/**",),
    "tests": ("tests/**",),
    "docs": ("docs/**", "*.md"),
    "tasks": ("tasks/**",),
    "config": (".pcae/**", "pyproject.toml"),
}

DEFAULT_ARCHITECTURE_RULES = {
    "core": ("core",),
    "commands": ("core", "commands"),
    "tests": ("*",),
    "docs": ("*",),
    "tasks": ("*",),
    "config": ("config",),
}

ARCHITECTURE_ENFORCEMENT_ADVISORY = "advisory"
ARCHITECTURE_ENFORCEMENT_STRICT = "strict"
SUPPORTED_ARCHITECTURE_ENFORCEMENT_MODES = (
    ARCHITECTURE_ENFORCEMENT_ADVISORY,
    ARCHITECTURE_ENFORCEMENT_STRICT,
)


@dataclass(frozen=True)
class Policy:
    protected_patterns: tuple[str, ...]
    architecture_zones: dict[str, tuple[str, ...]]
    architecture_rules: dict[str, tuple[str, ...]]
    architecture_enforcement_mode: str
    source: str
    path: Path
    file_exists: bool
    valid: bool
    error: str | None = None


def load_policy(root: HarnessPath) -> Policy:
    policy_path = root.join(POLICY_RELATIVE_PATH)
    if not policy_path.is_file():
        return Policy(
            protected_patterns=DEFAULT_PROTECTED_PATTERNS,
            architecture_zones={},
            architecture_rules={},
            architecture_enforcement_mode=ARCHITECTURE_ENFORCEMENT_ADVISORY,
            source=POLICY_SOURCE_DEFAULTS,
            path=policy_path,
            file_exists=False,
            valid=True,
        )

    try:
        parsed = parse_policy(policy_path.read_text(encoding="utf-8"))
    except ValueError as error:
        return Policy(
            protected_patterns=(),
            architecture_zones={},
            architecture_rules={},
            architecture_enforcement_mode=ARCHITECTURE_ENFORCEMENT_ADVISORY,
            source=POLICY_SOURCE_REPO,
            path=policy_path,
            file_exists=True,
            valid=False,
            error=str(error),
        )

    return Policy(
        protected_patterns=parsed.protected_patterns,
        architecture_zones=parsed.architecture_zones,
        architecture_rules=parsed.architecture_rules,
        architecture_enforcement_mode=parsed.architecture_enforcement_mode,
        source=POLICY_SOURCE_REPO,
        path=policy_path,
        file_exists=True,
        valid=True,
    )


@dataclass(frozen=True)
class ParsedPolicy:
    protected_patterns: tuple[str, ...]
    architecture_zones: dict[str, tuple[str, ...]]
    architecture_rules: dict[str, tuple[str, ...]]
    architecture_enforcement_mode: str


def parse_policy(content: str) -> ParsedPolicy:
    architecture_zones = parse_architecture_zones(content)
    return ParsedPolicy(
        protected_patterns=parse_protected_patterns(content),
        architecture_zones=architecture_zones,
        architecture_rules=parse_architecture_rules(content, architecture_zones),
        architecture_enforcement_mode=parse_architecture_enforcement_mode(content),
    )


def parse_protected_patterns(content: str) -> tuple[str, ...]:
    lines = content.splitlines()
    in_protected_section = False
    saw_protected_section = False
    saw_patterns = False
    in_patterns = False
    patterns: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("["):
            if not stripped.endswith("]"):
                raise ValueError("Invalid TOML: malformed table header.")
            in_protected_section = stripped == "[protected]"
            saw_protected_section = saw_protected_section or in_protected_section
            in_patterns = False
            continue

        if not in_protected_section:
            continue

        if stripped.startswith("patterns"):
            saw_patterns = True
            if "=" not in stripped:
                raise ValueError("Invalid policy: protected.patterns must be assigned.")
            value = stripped.split("=", 1)[1].strip()
            if not value.startswith("["):
                raise ValueError("Invalid policy: protected.patterns must be a list.")
            if "]" in value:
                patterns.extend(parse_pattern_values(value))
                in_patterns = False
            else:
                in_patterns = True
            continue

        if not in_patterns:
            continue

        if stripped.startswith("]"):
            in_patterns = False
            continue

        patterns.extend(parse_pattern_values(stripped))

    if in_patterns:
        raise ValueError("Invalid TOML: unterminated protected.patterns list.")
    if not saw_protected_section:
        raise ValueError("Invalid policy: [protected] section is missing.")
    if not saw_patterns:
        raise ValueError("Invalid policy: protected.patterns is missing.")
    if not patterns:
        raise ValueError("Invalid policy: protected.patterns must contain patterns.")

    return tuple(patterns)


def parse_architecture_zones(content: str) -> dict[str, tuple[str, ...]]:
    lines = content.splitlines()
    in_zones_section = False
    in_zone_patterns = False
    current_zone: str | None = None
    zones: dict[str, tuple[str, ...]] = {}
    pending_patterns: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("["):
            if in_zone_patterns:
                raise ValueError(
                    f"Invalid TOML: unterminated architecture zone '{current_zone}'."
                )
            if not stripped.endswith("]"):
                raise ValueError("Invalid TOML: malformed table header.")
            in_zones_section = stripped == "[architecture.zones]"
            current_zone = None
            continue

        if not in_zones_section:
            continue

        if in_zone_patterns:
            if stripped.startswith("]"):
                zones[current_zone or ""] = tuple(pending_patterns)
                in_zone_patterns = False
                current_zone = None
                pending_patterns = []
                continue
            pending_patterns.extend(parse_architecture_pattern_values(stripped))
            continue

        if "=" not in stripped:
            raise ValueError("Invalid policy: architecture zone must be assigned.")
        raw_name, raw_value = stripped.split("=", 1)
        zone_name = parse_architecture_zone_name(raw_name)
        value = raw_value.strip()
        if not value.startswith("["):
            raise ValueError(
                f"Invalid policy: architecture zone '{zone_name}' patterns must be a list."
            )
        if "]" in value:
            zones[zone_name] = parse_architecture_pattern_values(value)
        else:
            in_zone_patterns = True
            current_zone = zone_name
            pending_patterns = []

    if in_zone_patterns:
        raise ValueError(f"Invalid TOML: unterminated architecture zone '{current_zone}'.")

    for zone_name, patterns in zones.items():
        if not patterns:
            raise ValueError(
                f"Invalid policy: architecture zone '{zone_name}' patterns must contain patterns."
            )

    return zones


def parse_architecture_rules(
    content: str,
    architecture_zones: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    lines = content.splitlines()
    in_rules_section = False
    in_rule_targets = False
    current_source: str | None = None
    rules: dict[str, tuple[str, ...]] = {}
    pending_targets: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("["):
            if in_rule_targets:
                raise ValueError(
                    f"Invalid TOML: unterminated architecture rule '{current_source}'."
                )
            if not stripped.endswith("]"):
                raise ValueError("Invalid TOML: malformed table header.")
            in_rules_section = stripped == "[architecture.rules]"
            current_source = None
            continue

        if not in_rules_section:
            continue

        if in_rule_targets:
            if stripped.startswith("]"):
                rules[current_source or ""] = tuple(pending_targets)
                in_rule_targets = False
                current_source = None
                pending_targets = []
                continue
            pending_targets.extend(parse_architecture_rule_values(stripped))
            continue

        if "=" not in stripped:
            raise ValueError("Invalid policy: architecture rule must be assigned.")
        raw_source, raw_value = stripped.split("=", 1)
        source_zone = parse_architecture_zone_name(raw_source)
        value = raw_value.strip()
        if not value.startswith("["):
            raise ValueError(
                f"Invalid policy: architecture rule '{source_zone}' targets must be a list."
            )
        if "]" in value:
            rules[source_zone] = parse_architecture_rule_values(value)
        else:
            in_rule_targets = True
            current_source = source_zone
            pending_targets = []

    if in_rule_targets:
        raise ValueError(f"Invalid TOML: unterminated architecture rule '{current_source}'.")

    validate_architecture_rules(rules, architecture_zones)
    return rules


def validate_architecture_rules(
    rules: dict[str, tuple[str, ...]],
    architecture_zones: dict[str, tuple[str, ...]],
) -> None:
    known_zones = set(architecture_zones)
    for source_zone, target_zones in rules.items():
        if source_zone not in known_zones:
            raise ValueError(
                f"Invalid policy: architecture rule source '{source_zone}' "
                "must exist in architecture.zones."
            )
        if not target_zones:
            raise ValueError(
                f"Invalid policy: architecture rule '{source_zone}' targets must contain zones."
            )
        for target_zone in target_zones:
            if target_zone == "*":
                continue
            if target_zone not in known_zones:
                raise ValueError(
                    f"Invalid policy: architecture rule '{source_zone}' references "
                    f"unknown target zone '{target_zone}'."
                )


def parse_architecture_enforcement_mode(content: str) -> str:
    lines = content.splitlines()
    in_enforcement_section = False
    mode: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("["):
            if not stripped.endswith("]"):
                raise ValueError("Invalid TOML: malformed table header.")
            in_enforcement_section = stripped == "[architecture.enforcement]"
            continue

        if not in_enforcement_section:
            continue

        if not stripped.startswith("mode"):
            continue
        if "=" not in stripped:
            raise ValueError("Invalid policy: architecture.enforcement.mode must be assigned.")
        value = stripped.split("=", 1)[1].strip()
        mode = parse_string_value(
            value,
            "Invalid policy: architecture.enforcement.mode must be a string.",
        )

    if mode is None:
        return ARCHITECTURE_ENFORCEMENT_ADVISORY
    if mode not in SUPPORTED_ARCHITECTURE_ENFORCEMENT_MODES:
        raise ValueError(
            "Invalid policy: architecture.enforcement.mode must be "
            "'advisory' or 'strict'."
        )
    return mode


def parse_architecture_zone_name(raw_name: str) -> str:
    zone_name = raw_name.strip()
    if zone_name.startswith('"') and zone_name.endswith('"'):
        zone_name = zone_name[1:-1]
    if not zone_name:
        raise ValueError(
            "Invalid policy: architecture zone names must be non-empty strings."
        )
    return zone_name


def parse_string_value(value: str, error: str) -> str:
    if not (value.startswith('"') and value.endswith('"')):
        raise ValueError(error)
    parsed = value[1:-1]
    if not parsed:
        raise ValueError(error)
    return parsed


def parse_pattern_values(line: str) -> tuple[str, ...]:
    stripped = line.strip()
    if stripped in {"[", "]"}:
        return ()
    if stripped.startswith("["):
        stripped = stripped[1:].strip()
    if stripped.endswith("]"):
        stripped = stripped[:-1].strip()
    if not stripped:
        return ()

    values: list[str] = []
    for raw_value in stripped.split(","):
        value = raw_value.strip()
        if not value:
            continue
        if not (value.startswith('"') and value.endswith('"')):
            raise ValueError(
                "Invalid policy: every protected pattern must be a non-empty string."
            )
        pattern = value[1:-1]
        if not pattern:
            raise ValueError(
                "Invalid policy: every protected pattern must be a non-empty string."
            )
        values.append(pattern)

    return tuple(values)


def parse_architecture_pattern_values(line: str) -> tuple[str, ...]:
    try:
        return parse_pattern_values(line)
    except ValueError as error:
        message = str(error)
        if "every protected pattern" in message:
            raise ValueError(
                "Invalid policy: architecture zone patterns must be non-empty strings."
            ) from error
        raise


def parse_architecture_rule_values(line: str) -> tuple[str, ...]:
    try:
        return parse_pattern_values(line)
    except ValueError as error:
        message = str(error)
        if "every protected pattern" in message:
            raise ValueError(
                "Invalid policy: architecture rule targets must be non-empty strings."
            ) from error
        raise


def render_default_policy() -> str:
    patterns = "\n".join(f'  "{pattern}",' for pattern in DEFAULT_PROTECTED_PATTERNS)
    zones = "\n".join(
        f"{name} = {render_inline_pattern_list(zone_patterns)}"
        for name, zone_patterns in DEFAULT_ARCHITECTURE_ZONES.items()
    )
    rules = "\n".join(
        f"{name} = {render_inline_pattern_list(target_zones)}"
        for name, target_zones in DEFAULT_ARCHITECTURE_RULES.items()
    )
    return f"""[protected]
patterns = [
{patterns}
]

[architecture.zones]
{zones}

[architecture.rules]
{rules}

[architecture.enforcement]
mode = "{ARCHITECTURE_ENFORCEMENT_ADVISORY}"
"""


def render_inline_pattern_list(patterns: tuple[str, ...]) -> str:
    rendered_patterns = ", ".join(f'"{pattern}"' for pattern in patterns)
    return f"[{rendered_patterns}]"
