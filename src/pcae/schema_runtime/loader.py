"""Offline, containment-checked schema resource loader (Layer-2).

Phase 136F prerequisite infrastructure. Loads only local, verified
schema resources beneath an explicit, caller-supplied trusted root. It
never fetches remote resources, never trusts an externally supplied
absolute path, and rejects symlink escapes and duplicate ``$id``
values.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from .errors import SchemaResourceError, SchemaResourceNotFoundError
from .limits import DEFAULT_MAX_SCHEMA_RESOURCE_BYTES
from .models import OutcomeStatus, SchemaResourceInfo

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError as _JsonSchemaError
except ImportError as _exc:  # pragma: no cover - dependency declared in pyproject.toml
    raise SchemaResourceError("jsonschema is not installed; schema_runtime requires jsonschema>=4.18,<5") from _exc

from .json_parser import parse_strict_json

SUPPORTED_DIALECT = "https://json-schema.org/draft/2020-12/schema"


@dataclass(frozen=True)
class LoadedSchemaResource:
    """A verified, strictly-parsed schema resource and its metadata."""

    info: SchemaResourceInfo
    document: dict


def _resolve_root(root: Path) -> Path:
    resolved = Path(root).resolve(strict=True)
    if not resolved.is_dir():
        raise SchemaResourceError(f"Schema root is not a directory: {root}")
    return resolved


def _normalize_lexical(path: Path) -> Path:
    """Normalize '.'/'..' components without touching the filesystem or
    following symlinks -- used to reject traversal before any I/O."""
    return Path(os.path.normpath(str(path)))


def discover_schema_files(root: Path) -> tuple[Path, ...]:
    """Deterministically enumerate ``*.schema.json`` files under a trusted root.

    Returned paths may still resolve outside the root via a symlink; callers
    (``load_schema_resource``) verify containment before trusting content.
    """
    resolved_root = _resolve_root(root)
    try:
        candidates = sorted(resolved_root.rglob("*.schema.json"), key=lambda p: p.as_posix())
    except OSError as exc:
        raise SchemaResourceError(f"Failed to enumerate schema resources under {root}: {exc}") from exc
    return tuple(candidates)


def load_schema_resource(
    path: Path,
    *,
    root: Path,
    max_bytes: int = DEFAULT_MAX_SCHEMA_RESOURCE_BYTES,
) -> LoadedSchemaResource:
    """Load and verify a single schema resource beneath ``root``.

    Rejects absolute paths outside ``root``, path traversal, and any
    symlink (leaf or intermediate directory) that would place the
    resolved file outside ``root``.
    """
    resolved_root = _resolve_root(root)
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = resolved_root / candidate
    normalized = _normalize_lexical(candidate)

    try:
        normalized.relative_to(resolved_root)
    except ValueError:
        raise SchemaResourceError(f"Schema resource path escapes trusted root: {path}") from None

    if not normalized.exists() and not normalized.is_symlink():
        raise SchemaResourceNotFoundError(f"Schema resource does not exist: {path}")

    if normalized.is_symlink():
        raise SchemaResourceError(f"Symlinked schema resource is not permitted: {path}")

    resolved = normalized.resolve(strict=True)
    if resolved != normalized:
        # An intermediate directory component was a symlink; the fully
        # resolved path no longer matches the lexically normalized one.
        raise SchemaResourceError(f"Schema resource path contains a symlink: {path}")

    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        raise SchemaResourceError(f"Schema resource escapes trusted root after resolution: {path}") from None

    raw = resolved.read_bytes()
    if len(raw) > max_bytes:
        raise SchemaResourceError(f"Schema resource exceeds maximum size of {max_bytes} bytes: {path}")

    parse_result = parse_strict_json(raw, require_top_level_object=True)
    if parse_result.status is not OutcomeStatus.VALID:
        raise SchemaResourceError(f"Schema resource is not strictly valid JSON: {path} ({parse_result.errors})")
    document = parse_result.value

    schema_id = document.get("$id")
    if not isinstance(schema_id, str) or not schema_id:
        raise SchemaResourceError(f"Schema resource missing string $id: {path}")

    dialect = document.get("$schema")
    if dialect != SUPPORTED_DIALECT:
        raise SchemaResourceError(
            f"Schema resource does not declare Draft 2020-12 dialect (got {dialect!r}): {path}"
        )

    try:
        Draft202012Validator.check_schema(document)
    except _JsonSchemaError as exc:
        raise SchemaResourceError(f"Schema resource fails Draft 2020-12 schema checking: {path} ({exc})") from exc

    digest = hashlib.sha256(raw).hexdigest()
    relative = resolved.relative_to(resolved_root).as_posix()
    info = SchemaResourceInfo(
        schema_id=schema_id,
        relative_path=relative,
        dialect=dialect,
        sha256=digest,
        size_bytes=len(raw),
    )
    return LoadedSchemaResource(info=info, document=document)


def load_schema_package(
    root: Path,
    *,
    max_resource_bytes: int = DEFAULT_MAX_SCHEMA_RESOURCE_BYTES,
) -> tuple[LoadedSchemaResource, ...]:
    """Load every schema resource beneath ``root``, deterministically ordered.

    Rejects duplicate ``$id`` values across the package.
    """
    resolved_root = _resolve_root(root)
    resources: list[LoadedSchemaResource] = []
    seen_ids: dict[str, str] = {}
    for file_path in discover_schema_files(resolved_root):
        loaded = load_schema_resource(file_path, root=resolved_root, max_bytes=max_resource_bytes)
        if loaded.info.schema_id in seen_ids:
            raise SchemaResourceError(
                f"Duplicate $id {loaded.info.schema_id!r} in {loaded.info.relative_path} "
                f"(already used by {seen_ids[loaded.info.schema_id]})"
            )
        seen_ids[loaded.info.schema_id] = loaded.info.relative_path
        resources.append(loaded)
    return tuple(resources)
