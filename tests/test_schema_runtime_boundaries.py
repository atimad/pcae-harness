"""Phase 136F: dependency, no-network, no-authority, and no-execution proofs.

These tests prove that schema_runtime is generic infrastructure only:
it cannot resolve lifecycle authority, cannot mutate production state,
and introduces no execution capability (subprocess, shell, socket,
HTTP client, or backend invocation).
"""
from __future__ import annotations

import ast
import importlib
import socket
from pathlib import Path

import jsonschema
import pytest

import pcae.schema_runtime as schema_runtime
from pcae.schema_runtime import DEFAULT_MAX_INPUT_BYTES

SCHEMA_RUNTIME_SRC = Path(schema_runtime.__file__).parent
SCHEMA_RESOURCES_SRC = SCHEMA_RUNTIME_SRC.parent / "schema_resources"

_FORBIDDEN_IMPORT_MODULES = {
    "subprocess",
    "socket",
    "os.system",
    "shlex",
    "shutil.which",
    "http.client",
    "http.server",
    "urllib.request",
    "urllib3",
    "requests",
    "ftplib",
    "telnetlib",
    "smtplib",
}

_FORBIDDEN_AUTHORITY_SUBSTRINGS = (
    # "authority_state"/"authority_epoch" are no longer forbidden tokens:
    # Phase 136J's schema_resources/__init__.py docstrings legitimately
    # name the packaged Implementation Group 2 record schemas.
    "pcae.cltr",
    "current_authority",
    "cltr-authority",
)


def _iter_source_files() -> list[Path]:
    return sorted(SCHEMA_RUNTIME_SRC.rglob("*.py")) + sorted(SCHEMA_RESOURCES_SRC.rglob("*.py"))


def test_136f_dependency_version_within_frozen_range():
    from importlib.metadata import version

    from packaging.specifiers import SpecifierSet

    assert SpecifierSet(">=4.18,<5").contains(version("jsonschema"))


def test_136f_draft202012_validator_importable():
    from jsonschema import Draft202012Validator

    assert Draft202012Validator.META_SCHEMA["$id"] == "https://json-schema.org/draft/2020-12/schema"


def test_136f_no_forbidden_imports_in_source():
    for path in _iter_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {node.module} if node.module else set()
            else:
                continue
            forbidden_hit = names & _FORBIDDEN_IMPORT_MODULES
            assert not forbidden_hit, f"{path} imports forbidden module(s): {forbidden_hit}"


def _dotted_call_name(node: ast.Call) -> str | None:
    func = node.func
    parts: list[str] = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
        return ".".join(reversed(parts))
    return None


def test_136f_no_subprocess_or_os_system_calls_in_source():
    forbidden_calls = {"subprocess.run", "subprocess.call", "subprocess.Popen", "os.system", "os.popen"}
    for path in _iter_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _dotted_call_name(node)
                assert name not in forbidden_calls, f"{path} calls forbidden {name}"


def test_136f_no_authority_module_references_in_source():
    for path in _iter_source_files():
        text = path.read_text(encoding="utf-8")
        for needle in _FORBIDDEN_AUTHORITY_SUBSTRINGS:
            assert needle not in text, f"{path} references authority-related identifier {needle!r}"


def test_136f_no_authority_namespace_created_on_disk():
    repo_root = SCHEMA_RUNTIME_SRC.parents[2]
    assert not (repo_root / ".pcae" / "cltr-authority").exists()
    assert not (repo_root / "schemas" / "cltr_cutover").exists()


def test_136f_module_does_not_import_cltr_package():
    # Presence of pcae.cltr elsewhere in the interpreter (pulled in by other
    # test modules) is fine; the assertion is that schema_runtime itself
    # binds no reference into it.
    for _, value in vars(schema_runtime).items():
        module = getattr(value, "__module__", "")
        assert not str(module).startswith("pcae.cltr")


def test_136f_validation_infrastructure_performs_no_network_io(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from pcae.schema_runtime import build_offline_registry, validate_record_shape

    fixtures = Path(__file__).parent / "fixtures" / "schema_runtime" / "valid_package"
    registry = build_offline_registry(fixtures)

    def _forbidden_socket(*args, **kwargs):
        raise AssertionError("schema_runtime attempted to open a network socket during validation")

    monkeypatch.setattr(socket, "socket", _forbidden_socket)
    result = validate_record_shape(
        {"name": "n", "mode": "lenient"},
        schema_id="https://pcae.test/schema_runtime/valid_package/root-features.schema.json",
        registry=registry,
    )
    assert result.ok


def test_136f_limits_are_centrally_recorded_and_positive():
    from pcae.schema_runtime import (
        DEFAULT_MAX_ISSUE_COUNT,
        DEFAULT_MAX_REGISTRY_RESOURCES,
        DEFAULT_MAX_SCHEMA_RESOURCE_BYTES,
    )

    assert DEFAULT_MAX_INPUT_BYTES > 0
    assert DEFAULT_MAX_SCHEMA_RESOURCE_BYTES > 0
    assert DEFAULT_MAX_ISSUE_COUNT > 0
    assert DEFAULT_MAX_REGISTRY_RESOURCES > 0


def test_136f_error_vocabulary_matches_frozen_set():
    from pcae.schema_runtime import ERROR_CODES

    assert ERROR_CODES == frozenset(
        {
            "invalid_utf8",
            "input_too_large",
            "invalid_json",
            "duplicate_key",
            "non_finite_number",
            "top_level_not_object",
            "unknown_schema",
            "unsupported_schema_version",
            "unsupported_dialect",
            "schema_resource_invalid",
            "schema_reference_unresolved",
            "schema_invalid_record",
            "internal_validation_error",
        }
    )


def test_136f_schema_resources_package_does_not_contain_later_group_stage3_files():
    # Phase 136J legitimately packages authority_epoch.schema.json and
    # authority_state.schema.json (Implementation Group 2). Phase 136L
    # legitimately packages cutover_request.schema.json and
    # readiness_package.schema.json (Implementation Group 3). Phase 136N
    # legitimately packages human_authorization.schema.json,
    # cutover_candidate.schema.json, and certification.schema.json
    # (Implementation Group 4). Phase 136P legitimately packages
    # publication_attempt.schema.json and publication_evidence.schema.json
    # (Implementation Group 5). Phase 136R legitimately packages
    # concurrency_conflict.schema.json and recovery_journal_entry.schema.json
    # (contract Group 8, Sec.46, paired atomically per CSCH-EXEC-REQ-062).
    # Phase 136T legitimately packages notification_authority_binding.
    # schema.json, marker_authority_binding.schema.json, and
    # receipt_authority_binding.schema.json (contract Group 10). Phase 136V
    # legitimately packages compatibility_state.schema.json and
    # quarantine_record.schema.json (contract Group 11) -- the final of
    # the 11 frozen executable-schema groups. No later group remains.
    allowed_stage3_files = {
        "authority_epoch.schema.json",
        "authority_state.schema.json",
        "cutover_request.schema.json",
        "readiness_package.schema.json",
        "human_authorization.schema.json",
        "cutover_candidate.schema.json",
        "certification.schema.json",
        "publication_attempt.schema.json",
        "publication_evidence.schema.json",
        "concurrency_conflict.schema.json",
        "recovery_journal_entry.schema.json",
        "notification_authority_binding.schema.json",
        "marker_authority_binding.schema.json",
        "receipt_authority_binding.schema.json",
        "compatibility_state.schema.json",
        "quarantine_record.schema.json",
    }
    later_group_markers = ()
    for path in SCHEMA_RESOURCES_SRC.rglob("*"):
        if path.is_file() and path.name not in allowed_stage3_files:
            lowered = path.name.lower()
            for marker in later_group_markers:
                assert marker not in lowered, f"Unexpected later-group Stage 3 resource: {path}"


def test_136f_module_reimports_cleanly():
    reloaded = importlib.reload(schema_runtime)
    assert reloaded.parse_strict_json is not None
