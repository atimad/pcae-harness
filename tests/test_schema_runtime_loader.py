"""Phase 136F: focused tests for the offline schema resource loader."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from pcae.schema_runtime import SchemaResourceError, SchemaResourceNotFoundError
from pcae.schema_runtime.loader import discover_schema_files, load_schema_package, load_schema_resource

FIXTURES = Path(__file__).parent / "fixtures" / "schema_runtime"


def test_136f_loads_valid_package_deterministically():
    resources = load_schema_package(FIXTURES / "valid_package")
    ids = [r.info.schema_id for r in resources]
    assert ids == sorted(ids)
    assert len(resources) == 3
    for resource in resources:
        assert resource.info.sha256
        assert resource.info.size_bytes > 0


def test_136f_discover_is_sorted_and_pure():
    files_a = discover_schema_files(FIXTURES / "valid_package")
    files_b = discover_schema_files(FIXTURES / "valid_package")
    assert files_a == files_b
    assert list(files_a) == sorted(files_a, key=lambda p: p.as_posix())


def test_136f_duplicate_id_within_package_rejected():
    with pytest.raises(SchemaResourceError, match="Duplicate \\$id"):
        load_schema_package(FIXTURES / "duplicate_id_package")


def test_136f_duplicate_key_inside_schema_file_rejected():
    with pytest.raises(SchemaResourceError, match="not strictly valid JSON"):
        load_schema_package(FIXTURES / "duplicate_key_schema_package")


def test_136f_missing_id_rejected():
    with pytest.raises(SchemaResourceError, match="missing string \\$id"):
        load_schema_package(FIXTURES / "missing_id_package")


def test_136f_wrong_dialect_rejected():
    with pytest.raises(SchemaResourceError, match="Draft 2020-12 dialect"):
        load_schema_package(FIXTURES / "invalid_dialect_package")


def test_136f_schema_failing_meta_schema_check_rejected():
    with pytest.raises(SchemaResourceError, match="Draft 2020-12 schema checking"):
        load_schema_package(FIXTURES / "invalid_schema_package")


def test_136f_missing_resource_is_distinct_from_invalid_resource(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(SchemaResourceNotFoundError):
        load_schema_resource(root / "does_not_exist.schema.json", root=root)


def test_136f_absolute_path_outside_root_rejected(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.schema.json"
    outside.write_text('{"$schema": "x", "$id": "y", "type": "object"}', encoding="utf-8")
    with pytest.raises(SchemaResourceError, match="escapes trusted root"):
        load_schema_resource(outside, root=root)


def test_136f_traversal_resource_path_rejected(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (tmp_path / "secret.schema.json").write_text(
        '{"$schema": "x", "$id": "y", "type": "object"}', encoding="utf-8"
    )
    with pytest.raises(SchemaResourceError, match="escapes trusted root"):
        load_schema_resource(Path("../secret.schema.json"), root=root)


def test_136f_leaf_symlink_escape_rejected(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.schema.json"
    outside.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "z", "type": "object"}',
        encoding="utf-8",
    )
    link = root / "linked.schema.json"
    os.symlink(outside, link)
    with pytest.raises(SchemaResourceError, match="[Ss]ymlink"):
        load_schema_resource(link, root=root)


def test_136f_symlinked_root_directory_escape_rejected(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    outside_dir = tmp_path / "outside_dir"
    outside_dir.mkdir()
    (outside_dir / "escaped.schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "z2", "type": "object"}',
        encoding="utf-8",
    )
    linked_subdir = root / "linked_subdir"
    os.symlink(outside_dir, linked_subdir)
    with pytest.raises(SchemaResourceError, match="[Ss]ymlink"):
        load_schema_resource(linked_subdir / "escaped.schema.json", root=root)


def test_136f_schema_resource_size_limit(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    big = root / "big.schema.json"
    padding = " " * 100
    big.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "big", "type": "object", "%s": 1}'
        % padding,
        encoding="utf-8",
    )
    with pytest.raises(SchemaResourceError, match="exceeds maximum size"):
        load_schema_resource(big, root=root, max_bytes=10)


def test_136f_nonexistent_root_raises():
    with pytest.raises(FileNotFoundError):
        load_schema_package(Path("/nonexistent/schema/root/for/136f"))
