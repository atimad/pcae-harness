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


def load_policy(root: HarnessPath) -> Policy:
    policy_path = root.join(POLICY_RELATIVE_PATH)
    if not policy_path.is_file():
        return Policy(
            protected_patterns=DEFAULT_PROTECTED_PATTERNS,
            source=POLICY_SOURCE_DEFAULTS,
            path=policy_path,
            file_exists=False,
        )

    patterns = parse_protected_patterns(policy_path.read_text(encoding="utf-8"))
    if not patterns:
        return Policy(
            protected_patterns=DEFAULT_PROTECTED_PATTERNS,
            source=POLICY_SOURCE_DEFAULTS,
            path=policy_path,
            file_exists=True,
        )
    return Policy(
        protected_patterns=patterns,
        source=POLICY_SOURCE_REPO,
        path=policy_path,
        file_exists=True,
    )


def parse_protected_patterns(content: str) -> tuple[str, ...]:
    lines = content.splitlines()
    in_protected_section = False
    in_patterns = False
    patterns: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("[") and stripped.endswith("]"):
            in_protected_section = stripped == "[protected]"
            in_patterns = False
            continue

        if not in_protected_section:
            continue

        if stripped.startswith("patterns"):
            in_patterns = True
            if "[" in stripped and "]" in stripped:
                patterns.extend(parse_inline_strings(stripped))
                in_patterns = False
            continue

        if not in_patterns:
            continue

        if stripped.startswith("]"):
            in_patterns = False
            continue

        patterns.extend(parse_inline_strings(stripped))

    return tuple(patterns)


def parse_inline_strings(line: str) -> tuple[str, ...]:
    values: list[str] = []
    in_string = False
    current: list[str] = []

    for character in line:
        if character == '"':
            if in_string:
                values.append("".join(current))
                current = []
            in_string = not in_string
            continue
        if in_string:
            current.append(character)

    return tuple(values)


def render_default_policy() -> str:
    patterns = "\n".join(f'  "{pattern}",' for pattern in DEFAULT_PROTECTED_PATTERNS)
    return f"""[protected]
patterns = [
{patterns}
]
"""
