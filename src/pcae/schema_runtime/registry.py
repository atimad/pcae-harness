"""Offline-only schema registry foundation (Layer-2).

Phase 136F prerequisite infrastructure. Wraps ``referencing.Registry``
so that ``$id`` resolution is populated *only* from schema resources
already verified by :mod:`pcae.schema_runtime.loader`. A URI-shaped
``$id`` (e.g. ``https://example.test/...``) never authorizes a network
fetch: the registry's ``retrieve`` hook always fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from referencing import Registry, Resource

from .errors import SchemaRegistryError
from .limits import DEFAULT_MAX_REGISTRY_RESOURCES
from .loader import load_schema_package
from .models import SchemaResourceInfo


def _refuse_retrieve(uri: str):
    raise SchemaRegistryError(
        f"Offline schema registry refuses to retrieve unregistered reference: {uri}"
    )


@dataclass(frozen=True)
class SchemaRegistry:
    """Read-only, offline-only Draft 2020-12 schema registry."""

    referencing_registry: Registry
    _documents: dict
    _resource_infos: dict

    @property
    def schema_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._resource_infos))

    def resource_info(self, schema_id: str) -> SchemaResourceInfo:
        try:
            return self._resource_infos[schema_id]
        except KeyError:
            raise SchemaRegistryError(f"Unknown schema id: {schema_id}") from None

    def document(self, schema_id: str) -> dict:
        try:
            return self._documents[schema_id]
        except KeyError:
            raise SchemaRegistryError(f"Unknown schema id: {schema_id}") from None


def build_offline_registry(
    *roots: Path,
    max_resources: int = DEFAULT_MAX_REGISTRY_RESOURCES,
) -> SchemaRegistry:
    """Build a registry populated only from verified local schema resources.

    Performs no network access. Duplicate ``$id`` values, whether within
    a single root or across multiple roots, are rejected.
    """
    documents: dict[str, dict] = {}
    infos: dict[str, SchemaResourceInfo] = {}
    resource_entries = []
    for root in roots:
        for loaded in load_schema_package(root):
            if loaded.info.schema_id in infos:
                raise SchemaRegistryError(f"Duplicate $id across schema roots: {loaded.info.schema_id}")
            documents[loaded.info.schema_id] = loaded.document
            infos[loaded.info.schema_id] = loaded.info
            resource_entries.append((loaded.info.schema_id, Resource.from_contents(loaded.document)))

    if len(resource_entries) > max_resources:
        raise SchemaRegistryError(
            f"Schema registry would contain {len(resource_entries)} resources, "
            f"exceeding the configured maximum of {max_resources}"
        )

    registry = Registry(retrieve=_refuse_retrieve).with_resources(resource_entries)
    return SchemaRegistry(referencing_registry=registry, _documents=documents, _resource_infos=infos)
