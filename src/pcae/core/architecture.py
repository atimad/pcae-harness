from __future__ import annotations

import ast
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from pcae.core.git_status import GitChange
from pcae.core.paths import HarnessPath


@dataclass(frozen=True)
class ArchitectureDependencyWarning:
    path: Path
    source_zone: str
    target_zone: str

    @property
    def text(self) -> str:
        return (
            f"{self.path.as_posix()}: {self.source_zone} -> {self.target_zone} "
            "is not allowed by policy"
        )


@dataclass(frozen=True)
class ArchitectureParseWarning:
    path: Path
    reason: str

    @property
    def text(self) -> str:
        return f"{self.path.as_posix()}: {self.reason}"


@dataclass(frozen=True)
class ArchitectureAnalysisResult:
    dependency_warnings: tuple[ArchitectureDependencyWarning, ...]
    parse_warnings: tuple[ArchitectureParseWarning, ...]


def analyze_changed_python_dependencies(
    root: HarnessPath,
    changes: tuple[GitChange, ...],
    architecture_zones: dict[str, tuple[str, ...]],
    architecture_rules: dict[str, tuple[str, ...]],
    forbidden_dependencies: tuple[tuple[str, str], ...] = (),
) -> ArchitectureAnalysisResult:
    if not architecture_rules and not forbidden_dependencies:
        return ArchitectureAnalysisResult(dependency_warnings=(), parse_warnings=())

    dependency_warnings: list[ArchitectureDependencyWarning] = []
    parse_warnings: list[ArchitectureParseWarning] = []

    for change in changes:
        if change.path.suffix != ".py":
            continue

        source_zones = zones_for_path(change.path, architecture_zones)
        if not source_zones:
            continue

        source_path = root.join(change.path)
        try:
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            parse_warnings.append(
                ArchitectureParseWarning(
                    path=change.path,
                    reason=f"Could not parse Python imports: {error}",
                )
            )
            continue

        for module_name in imported_modules(tree):
            target_path = local_module_path(root, module_name)
            if target_path is None:
                continue
            target_zones = zones_for_path(target_path, architecture_zones)
            if not target_zones:
                continue
            dependency_warnings.extend(
                disallowed_dependencies(
                    change.path,
                    source_zones,
                    target_zones,
                    architecture_rules,
                    forbidden_dependencies,
                )
            )

    return ArchitectureAnalysisResult(
        dependency_warnings=tuple(deduplicate_dependency_warnings(dependency_warnings)),
        parse_warnings=tuple(parse_warnings),
    )


def imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module is None:
                continue
            modules.append(node.module)
            modules.extend(
                f"{node.module}.{alias.name}"
                for alias in node.names
                if alias.name != "*"
            )
    return tuple(modules)


def local_module_path(root: HarnessPath, module_name: str) -> Path | None:
    if not module_name.startswith("pcae."):
        return None

    module_parts = module_name.split(".")
    module_path = Path("src").joinpath(*module_parts).with_suffix(".py")
    if root.join(module_path).is_file():
        return module_path

    package_path = Path("src").joinpath(*module_parts) / "__init__.py"
    if root.join(package_path).is_file():
        return package_path

    return None


def zones_for_path(path: Path, zones: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    return tuple(
        zone_name
        for zone_name, patterns in zones.items()
        if path_matches_any(path, patterns)
    )


def disallowed_dependencies(
    path: Path,
    source_zones: tuple[str, ...],
    target_zones: tuple[str, ...],
    architecture_rules: dict[str, tuple[str, ...]],
    forbidden_dependencies: tuple[tuple[str, str], ...] = (),
) -> tuple[ArchitectureDependencyWarning, ...]:
    warnings: list[ArchitectureDependencyWarning] = []
    for source_zone in source_zones:
        allowed_targets = architecture_rules.get(source_zone, ())
        for target_zone in target_zones:
            if dependency_is_forbidden(
                source_zone,
                target_zone,
                forbidden_dependencies,
            ):
                warnings.append(
                    ArchitectureDependencyWarning(
                        path=path,
                        source_zone=source_zone,
                        target_zone=target_zone,
                    )
                )
                continue
            if "*" in allowed_targets:
                continue
            if target_zone in allowed_targets:
                continue
            warnings.append(
                ArchitectureDependencyWarning(
                    path=path,
                    source_zone=source_zone,
                    target_zone=target_zone,
                )
            )
    return tuple(warnings)


def dependency_is_forbidden(
    source_zone: str,
    target_zone: str,
    forbidden_dependencies: tuple[tuple[str, str], ...],
) -> bool:
    return any(
        source_zone == forbidden_source
        and (forbidden_target == "*" or target_zone == forbidden_target)
        for forbidden_source, forbidden_target in forbidden_dependencies
    )


def deduplicate_dependency_warnings(
    warnings: list[ArchitectureDependencyWarning],
) -> tuple[ArchitectureDependencyWarning, ...]:
    deduplicated: list[ArchitectureDependencyWarning] = []
    seen: set[tuple[Path, str, str]] = set()
    for warning in warnings:
        key = (warning.path, warning.source_zone, warning.target_zone)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(warning)
    return tuple(deduplicated)


def path_matches_any(path: Path, patterns: tuple[str, ...]) -> bool:
    path_text = path.as_posix()
    return any(path_matches_pattern(path_text, pattern.strip()) for pattern in patterns)


def path_matches_pattern(path_text: str, pattern: str) -> bool:
    if not pattern:
        return False
    if pattern.endswith("/"):
        return path_text.startswith(pattern)
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path_text == prefix or path_text.startswith(f"{prefix}/")
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        if not path_text.startswith(f"{prefix}/"):
            return False
        remainder = path_text[len(prefix) + 1 :]
        return "/" not in remainder
    if "/" not in pattern and fnmatch(Path(path_text).name, pattern):
        return True
    return fnmatch(path_text, pattern)
