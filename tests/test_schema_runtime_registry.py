"""Phase 136F: focused tests for the offline schema registry foundation."""
from __future__ import annotations

import socket
from pathlib import Path

import pytest

from pcae.schema_runtime import SchemaRegistryError, build_offline_registry

FIXTURES = Path(__file__).parent / "fixtures" / "schema_runtime"


def test_136f_registry_resolves_local_ids_deterministically():
    registry = build_offline_registry(FIXTURES / "valid_package")
    assert registry.schema_ids == tuple(sorted(registry.schema_ids))
    assert (
        "https://pcae.test/schema_runtime/valid_package/root-features.schema.json" in registry.schema_ids
    )


def test_136f_duplicate_id_across_roots_rejected(tmp_path: Path):
    root_a = tmp_path / "a"
    root_a.mkdir()
    (root_a / "x.schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://pcae.test/dup", '
        '"type": "object"}',
        encoding="utf-8",
    )
    root_b = tmp_path / "b"
    root_b.mkdir()
    (root_b / "y.schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://pcae.test/dup", '
        '"type": "string"}',
        encoding="utf-8",
    )
    with pytest.raises(SchemaRegistryError, match="Duplicate \\$id"):
        build_offline_registry(root_a, root_b)


def test_136f_registry_rejects_unregistered_lookup_without_network():
    registry = build_offline_registry(FIXTURES / "valid_package")

    original_socket = socket.socket

    def _forbidden_socket(*args, **kwargs):
        raise AssertionError("schema_runtime attempted to open a network socket")

    socket.socket = _forbidden_socket  # type: ignore[assignment]
    try:
        with pytest.raises(Exception):
            registry.referencing_registry.get_or_retrieve("https://json-schema.org/this-is-not-registered")
    finally:
        socket.socket = original_socket  # type: ignore[assignment]


def test_136f_uri_shaped_id_resolves_locally_never_fetched():
    # A URI-shaped $id (https://pcae.test/...) must resolve purely from the
    # locally verified registry contents, never a network fetch.
    registry = build_offline_registry(FIXTURES / "valid_package")
    original_socket = socket.socket

    def _forbidden_socket(*args, **kwargs):
        raise AssertionError("schema_runtime attempted to open a network socket")

    socket.socket = _forbidden_socket  # type: ignore[assignment]
    try:
        resolved = registry.referencing_registry.get_or_retrieve(
            "https://pcae.test/schema_runtime/valid_package/shared-defs.schema.json"
        )
        assert resolved is not None
    finally:
        socket.socket = original_socket  # type: ignore[assignment]


def test_136f_max_registry_resources_enforced():
    with pytest.raises(SchemaRegistryError, match="exceeding the configured maximum"):
        build_offline_registry(FIXTURES / "valid_package", max_resources=1)
