"""Generic deterministic schema-manifest verification (Layer 2 infra).

Phase 136H prerequisite-adjacent infrastructure, added alongside the
first schema-core package (``cltr_cutover``) that actually needs a
manifest, but deliberately generic: nothing here is aware of any
particular package's ``$id`` namespace, family vocabulary, or record
schema. A manifest is a small, hand-authored JSON document listing, for
each schema resource file a package wants indexed, that file's own
``schema_id``, relative path, and SHA-256 digest. Verification proves two
things, and only two: (1) the manifest document itself is shape-valid
against a caller-supplied manifest schema, and (2) every listed entry's
recorded digest matches the real file on disk, right now. It does not
resolve authority, does not persist anything, and does not mutate the
package it verifies.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import SchemaResourceError
from .json_parser import parse_strict_json
from .limits import DEFAULT_MAX_SCHEMA_RESOURCE_BYTES
from .loader import discover_schema_files, load_schema_resource
from .models import OutcomeStatus
from .registry import SchemaRegistry
from .validation import validate_record_shape


class ManifestIntegrityError(SchemaResourceError):
    """Raised when a manifest fails shape validation, digest verification,
    or completeness verification against the package it indexes."""


@dataclass(frozen=True)
class VerifiedManifestEntry:
    """One digest-verified manifest entry, cross-checked against disk."""

    schema_id: str
    file_path: str
    file_digest: str


@dataclass(frozen=True)
class VerifiedManifest:
    """A manifest that has passed shape validation, per-entry digest
    verification, and two-way completeness verification against the
    schema resource files actually present under its package root."""

    document: dict
    entries: tuple[VerifiedManifestEntry, ...]


def load_and_verify_manifest(
    manifest_path: Path,
    *,
    package_root: Path,
    registry: SchemaRegistry,
    manifest_schema_id: str,
    entries_key: str = "entries",
    file_path_key: str = "file_path",
    schema_id_key: str = "schema_id",
    file_digest_key: str = "file_digest",
    excluded_relative_paths: frozenset[str] = frozenset(),
    max_bytes: int = DEFAULT_MAX_SCHEMA_RESOURCE_BYTES,
) -> VerifiedManifest:
    """Load, shape-validate, and digest-verify a manifest against its package.

    ``registry`` must already contain ``manifest_schema_id``. Every entry's
    recorded ``file_digest`` is compared against the *actual*, freshly
    computed SHA-256 of its own file (via :func:`load_schema_resource`,
    which independently re-derives the digest -- the manifest's own claim
    is never trusted without recomputation). Completeness is two-way: every
    ``*.schema.json`` resource discovered under ``package_root`` (other than
    ``excluded_relative_paths``, e.g. the manifest's own governing schema
    file) must appear in the manifest, and every manifest entry must
    correspond to a real, discovered file -- an orphaned entry or an
    unindexed file are both raised as :class:`ManifestIntegrityError`.

    Performs no network access, no mutation, and no authority resolution.
    """
    raw = Path(manifest_path).read_bytes()
    if len(raw) > max_bytes:
        raise ManifestIntegrityError(f"Manifest exceeds maximum size of {max_bytes} bytes: {manifest_path}")

    parse_result = parse_strict_json(raw, require_top_level_object=True)
    if parse_result.status is not OutcomeStatus.VALID:
        raise ManifestIntegrityError(f"Manifest is not strictly valid JSON: {manifest_path} ({parse_result.errors})")
    document = parse_result.value

    shape_result = validate_record_shape(document, schema_id=manifest_schema_id, registry=registry)
    if not shape_result.ok:
        raise ManifestIntegrityError(
            f"Manifest failed shape validation against {manifest_schema_id}: {shape_result.issues}"
        )

    raw_entries = document.get(entries_key)
    if not isinstance(raw_entries, list):
        raise ManifestIntegrityError(f"Manifest {entries_key!r} is not a list: {manifest_path}")

    resolved_root = Path(package_root).resolve(strict=True)
    entries: list[VerifiedManifestEntry] = []
    manifest_paths: set[str] = set()
    for raw_entry in raw_entries:
        file_path = raw_entry[file_path_key]
        schema_id = raw_entry[schema_id_key]
        claimed_digest = raw_entry[file_digest_key]

        if file_path in manifest_paths:
            raise ManifestIntegrityError(f"Duplicate manifest {file_path_key} entry: {file_path}")
        manifest_paths.add(file_path)

        loaded = load_schema_resource(Path(file_path), root=resolved_root, max_bytes=max_bytes)
        if loaded.info.schema_id != schema_id:
            raise ManifestIntegrityError(
                f"Manifest {schema_id_key} {schema_id!r} does not match on-disk $id "
                f"{loaded.info.schema_id!r} for {file_path}"
            )
        if loaded.info.sha256 != claimed_digest:
            raise ManifestIntegrityError(
                f"Manifest {file_digest_key} for {file_path} does not match the file's actual "
                f"SHA-256 (manifest claims {claimed_digest!r}, file is {loaded.info.sha256!r})"
            )
        entries.append(VerifiedManifestEntry(schema_id=schema_id, file_path=file_path, file_digest=claimed_digest))

    discovered = {
        path.relative_to(resolved_root).as_posix()
        for path in discover_schema_files(resolved_root)
    }
    required = discovered - excluded_relative_paths
    if manifest_paths != required:
        missing_from_manifest = required - manifest_paths
        orphaned_in_manifest = manifest_paths - required
        raise ManifestIntegrityError(
            "Manifest completeness check failed: "
            f"missing_from_manifest={sorted(missing_from_manifest)}, "
            f"orphaned_in_manifest={sorted(orphaned_in_manifest)}"
        )

    return VerifiedManifest(document=document, entries=tuple(entries))
