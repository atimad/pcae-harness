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
    "cli": ("src/pcae/cli.py", "src/pcae/__main__.py", "src/pcae/__init__.py"),
    "tests": ("tests/**",),
    "docs": ("docs/**", "*.md"),
    "tasks": ("tasks/**",),
    "scripts": ("scripts/**",),
    "hooks": (".githooks/**",),
    "package": ("pyproject.toml",),
    "session": (".pcae/session.json",),
    "policy": (".pcae/policy.toml",),
    "config": (".pcae/**", "pyproject.toml"),
}

DEFAULT_ARCHITECTURE_RULES = {
    "core": ("core",),
    "commands": ("core", "commands"),
    "cli": ("core", "commands", "cli"),
    "tests": ("*",),
    "docs": ("*",),
    "tasks": ("*",),
    "scripts": ("*",),
    "hooks": ("hooks",),
    "package": ("package",),
    "session": ("session",),
    "policy": ("policy",),
    "config": ("config",),
}
DEFAULT_AGENT_STALE_AFTER_SECONDS = 14400
DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS = 300
DEFAULT_ORCHESTRATION_DEFAULT_AGENT = "claude-local"
DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT = "claude-local"
DEFAULT_ORCHESTRATION_RUNTIME_AGENT = "codex-local"
DEFAULT_ORCHESTRATION_VALIDATION_AGENT = "pcae-native"


@dataclass(frozen=True)
class AgentRegistryEntry:
    agent_id: str
    kind: str
    roles: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "kind": self.kind,
            "roles": list(self.roles),
        }


DEFAULT_AGENT_REGISTRY: tuple[AgentRegistryEntry, ...] = (
    AgentRegistryEntry(
        agent_id="claude-local",
        kind="claude",
        roles=("documentation", "architecture", "analysis"),
    ),
    AgentRegistryEntry(
        agent_id="codex-local",
        kind="codex",
        roles=("runtime", "implementation", "tests"),
    ),
    AgentRegistryEntry(
        agent_id="pcae-native",
        kind="pcae",
        roles=("validation", "governance"),
    ),
)


@dataclass(frozen=True)
class OrchestrationPolicy:
    default_agent: str
    documentation_agent: str
    runtime_agent: str
    validation_agent: str

    def to_dict(self) -> dict:
        return {
            "default_agent": self.default_agent,
            "documentation_agent": self.documentation_agent,
            "runtime_agent": self.runtime_agent,
            "validation_agent": self.validation_agent,
        }


DEFAULT_ORCHESTRATION_POLICY = OrchestrationPolicy(
    default_agent=DEFAULT_ORCHESTRATION_DEFAULT_AGENT,
    documentation_agent=DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT,
    runtime_agent=DEFAULT_ORCHESTRATION_RUNTIME_AGENT,
    validation_agent=DEFAULT_ORCHESTRATION_VALIDATION_AGENT,
)

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
    agent_stale_after_seconds: int
    daemon_watch_interval_seconds: int
    orchestration: OrchestrationPolicy
    agent_registry: tuple[AgentRegistryEntry, ...]
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
            agent_stale_after_seconds=DEFAULT_AGENT_STALE_AFTER_SECONDS,
            daemon_watch_interval_seconds=DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS,
            orchestration=DEFAULT_ORCHESTRATION_POLICY,
            agent_registry=DEFAULT_AGENT_REGISTRY,
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
            agent_stale_after_seconds=DEFAULT_AGENT_STALE_AFTER_SECONDS,
            daemon_watch_interval_seconds=DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS,
            orchestration=DEFAULT_ORCHESTRATION_POLICY,
            agent_registry=DEFAULT_AGENT_REGISTRY,
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
        agent_stale_after_seconds=parsed.agent_stale_after_seconds,
        daemon_watch_interval_seconds=parsed.daemon_watch_interval_seconds,
        orchestration=parsed.orchestration,
        agent_registry=parsed.agent_registry,
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
    agent_stale_after_seconds: int
    daemon_watch_interval_seconds: int
    orchestration: OrchestrationPolicy
    agent_registry: tuple[AgentRegistryEntry, ...]


def parse_policy(content: str) -> ParsedPolicy:
    architecture_zones = parse_architecture_zones(content)
    return ParsedPolicy(
        protected_patterns=parse_protected_patterns(content),
        architecture_zones=architecture_zones,
        architecture_rules=parse_architecture_rules(content, architecture_zones),
        architecture_enforcement_mode=parse_architecture_enforcement_mode(content),
        agent_stale_after_seconds=parse_agent_stale_after_seconds(content),
        daemon_watch_interval_seconds=parse_daemon_watch_interval_seconds(content),
        orchestration=parse_orchestration_policy(content),
        agent_registry=parse_agent_registry(content),
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


def parse_agent_stale_after_seconds(content: str) -> int:
    lines = content.splitlines()
    in_agent_section = False
    stale_after_seconds: int | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("["):
            if not stripped.endswith("]"):
                raise ValueError("Invalid TOML: malformed table header.")
            in_agent_section = stripped == "[agent]"
            continue

        if not in_agent_section:
            continue

        if not stripped.startswith("stale_after_seconds"):
            continue
        if "=" not in stripped:
            raise ValueError("Invalid policy: agent.stale_after_seconds must be assigned.")
        value = stripped.split("=", 1)[1].strip()
        if not value.isdigit():
            raise ValueError(
                "Invalid policy: agent.stale_after_seconds must be a positive integer."
            )
        stale_after_seconds = int(value)

    if stale_after_seconds is None:
        return DEFAULT_AGENT_STALE_AFTER_SECONDS
    if stale_after_seconds <= 0:
        raise ValueError(
            "Invalid policy: agent.stale_after_seconds must be a positive integer."
        )
    return stale_after_seconds


def parse_daemon_watch_interval_seconds(content: str) -> int:
    lines = content.splitlines()
    in_daemon_section = False
    watch_interval_seconds: int | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("["):
            if not stripped.endswith("]"):
                raise ValueError("Invalid TOML: malformed table header.")
            in_daemon_section = stripped == "[daemon]"
            continue

        if not in_daemon_section:
            continue

        if not stripped.startswith("watch_interval_seconds"):
            continue
        if "=" not in stripped:
            raise ValueError(
                "Invalid policy: daemon.watch_interval_seconds must be assigned."
            )
        value = stripped.split("=", 1)[1].strip()
        if not value.isdigit():
            raise ValueError(
                "Invalid policy: daemon.watch_interval_seconds must be a positive integer."
            )
        watch_interval_seconds = int(value)

    if watch_interval_seconds is None:
        return DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS
    if watch_interval_seconds <= 0:
        raise ValueError(
            "Invalid policy: daemon.watch_interval_seconds must be a positive integer."
        )
    return watch_interval_seconds


_ORCHESTRATION_KEYS = frozenset(
    {"default_agent", "documentation_agent", "runtime_agent", "validation_agent"}
)


def parse_orchestration_policy(content: str) -> OrchestrationPolicy:
    lines = content.splitlines()
    in_orchestration_section = False
    values: dict[str, str] = {}

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("["):
            if not stripped.endswith("]"):
                raise ValueError("Invalid TOML: malformed table header.")
            in_orchestration_section = stripped == "[orchestration]"
            continue

        if not in_orchestration_section:
            continue

        if "=" not in stripped:
            continue

        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if key not in _ORCHESTRATION_KEYS:
            continue

        values[key] = parse_string_value(
            raw_value.strip(),
            f"Invalid policy: orchestration.{key} must be a non-empty string.",
        )

    return OrchestrationPolicy(
        default_agent=values.get("default_agent", DEFAULT_ORCHESTRATION_DEFAULT_AGENT),
        documentation_agent=values.get(
            "documentation_agent", DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT
        ),
        runtime_agent=values.get("runtime_agent", DEFAULT_ORCHESTRATION_RUNTIME_AGENT),
        validation_agent=values.get(
            "validation_agent", DEFAULT_ORCHESTRATION_VALIDATION_AGENT
        ),
    )


def parse_agent_registry(content: str) -> tuple[AgentRegistryEntry, ...]:
    lines = content.splitlines()
    entries: list[AgentRegistryEntry] = []
    current_agent_id: str | None = None
    current_kind: str | None = None
    current_roles: list[str] | None = None
    in_roles_list = False
    pending_roles: list[str] = []

    def _finalize_agent() -> None:
        if current_agent_id is None:
            return
        if in_roles_list:
            raise ValueError(
                f"Invalid TOML: unterminated roles list for agent '{current_agent_id}'."
            )
        if current_kind is None:
            raise ValueError(
                f"Invalid policy: agent '{current_agent_id}' is missing 'kind'."
            )
        if current_roles is None:
            raise ValueError(
                f"Invalid policy: agent '{current_agent_id}' is missing 'roles'."
            )
        entries.append(
            AgentRegistryEntry(
                agent_id=current_agent_id,
                kind=current_kind,
                roles=tuple(current_roles),
            )
        )

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("["):
            if not stripped.endswith("]"):
                raise ValueError("Invalid TOML: malformed table header.")
            _finalize_agent()
            current_agent_id = None
            current_kind = None
            current_roles = None
            in_roles_list = False
            pending_roles = []
            if stripped.startswith("[agents."):
                agent_id = stripped[len("[agents."):-1].strip()
                if not agent_id:
                    raise ValueError(
                        "Invalid policy: agent registry entry ID must be non-empty."
                    )
                current_agent_id = agent_id
            continue

        if current_agent_id is None:
            continue

        if in_roles_list:
            if stripped.startswith("]"):
                if not pending_roles:
                    raise ValueError(
                        f"Invalid policy: agent '{current_agent_id}' roles must be non-empty."
                    )
                current_roles = list(pending_roles)
                in_roles_list = False
                pending_roles = []
            else:
                pending_roles.extend(parse_agent_role_values(stripped))
            continue

        if "=" not in stripped:
            continue

        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        if key == "kind":
            current_kind = parse_string_value(
                raw_value,
                f"Invalid policy: agent '{current_agent_id}' kind must be a non-empty string.",
            )
        elif key == "roles":
            if not raw_value.startswith("["):
                raise ValueError(
                    f"Invalid policy: agent '{current_agent_id}' roles must be a list."
                )
            if "]" in raw_value:
                roles = parse_agent_role_values(raw_value)
                if not roles:
                    raise ValueError(
                        f"Invalid policy: agent '{current_agent_id}' roles must be non-empty."
                    )
                current_roles = list(roles)
            else:
                in_roles_list = True
                pending_roles = []

    _finalize_agent()

    return tuple(entries) if entries else DEFAULT_AGENT_REGISTRY


def parse_agent_role_values(line: str) -> tuple[str, ...]:
    try:
        return parse_pattern_values(line)
    except ValueError as error:
        message = str(error)
        if "every protected pattern" in message:
            raise ValueError(
                "Invalid policy: agent role values must be non-empty strings."
            ) from error
        raise


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

[agent]
stale_after_seconds = {DEFAULT_AGENT_STALE_AFTER_SECONDS}

[daemon]
watch_interval_seconds = {DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS}

[orchestration]
default_agent = "{DEFAULT_ORCHESTRATION_DEFAULT_AGENT}"
documentation_agent = "{DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT}"
runtime_agent = "{DEFAULT_ORCHESTRATION_RUNTIME_AGENT}"
validation_agent = "{DEFAULT_ORCHESTRATION_VALIDATION_AGENT}"

[agents.claude-local]
kind = "claude"
roles = ["documentation", "architecture", "analysis"]

[agents.codex-local]
kind = "codex"
roles = ["runtime", "implementation", "tests"]

[agents.pcae-native]
kind = "pcae"
roles = ["validation", "governance"]
"""


def render_inline_pattern_list(patterns: tuple[str, ...]) -> str:
    rendered_patterns = ", ".join(f'"{pattern}"' for pattern in patterns)
    return f"[{rendered_patterns}]"
