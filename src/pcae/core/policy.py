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


@dataclass(frozen=True)
class Policy:
    protected_patterns: tuple[str, ...]
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
            source=POLICY_SOURCE_DEFAULTS,
            path=policy_path,
            file_exists=False,
            valid=True,
        )

    try:
        patterns = parse_protected_patterns(policy_path.read_text(encoding="utf-8"))
    except ValueError as error:
        return Policy(
            protected_patterns=(),
            source=POLICY_SOURCE_REPO,
            path=policy_path,
            file_exists=True,
            valid=False,
            error=str(error),
        )

    return Policy(
        protected_patterns=patterns,
        source=POLICY_SOURCE_REPO,
        path=policy_path,
        file_exists=True,
        valid=True,
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


def render_default_policy() -> str:
    patterns = "\n".join(f'  "{pattern}",' for pattern in DEFAULT_PROTECTED_PATTERNS)
    return f"""[protected]
patterns = [
{patterns}
]
"""
