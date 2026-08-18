"""Phase 149O.20L.7O.2B.1 -- RepositoryIdentity Creation Independent
Real-Host Verification.

This phase's live findings (fresh SSH to `hac-dell`, independent
stat/getfacl/find, live `read_repository_identity`/
`validate_repository_identity_document`/
`derive_implementation_scope_digest`/
`verify_class_b_deployment_conformance` invocation) are not
reproducible in CI -- no route to `hac-dell` exists here. These tests
instead assert the local, source-level invariants this phase's
independent verification actually relied on: the closed
RepositoryIdentity field/schema contract, the idempotent-read-first
`ensure_repository_identity` structure that let this phase avoid
invoking it, the exact reason-transition branch in
`hatp_class_b_conformance.py`, the absence of any local
RepositoryIdentity artifact, and this phase's own doc recording the
exact live values reported above (self-consistency, not
re-execution).
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2B_1_REPOSITORYIDENTITY_CREATION_INDEPENDENT_REAL_HOST_VERIFICATION.md"
)
_MODULE_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "repository_identity.py"
_CONFORMANCE_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_class_b_conformance.py"

_EXPECTED_UUID = "0107866f-af7c-40b4-8317-74e71acb05ca"
_EXPECTED_SOURCE_SHA = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"
_EXPECTED_HMIC_DIGEST = (
    "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"
)
_SOLE_RESIDUAL_REQ = "HBDC-REQ-042"
_SOLE_RESIDUAL_REASON = "no_active_deployment_binding_matches_repository_and_root"
_ABSENT_REASON = "no_repository_identity_present"


def _doc_text() -> str:
    return " ".join(_DOC_PATH.read_text().split())


def _module_source() -> str:
    return _MODULE_PATH.read_text()


def _conformance_source() -> str:
    return _CONFORMANCE_PATH.read_text()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Doc self-consistency: this phase's own report records the exact
#    live values it claims, and states verification-only scope.
# ═══════════════════════════════════════════════════════════════════════════


class TestDocSelfConsistency:
    def test_doc_records_expected_uuid(self) -> None:
        assert _EXPECTED_UUID in _doc_text()

    def test_doc_records_expected_source_sha(self) -> None:
        assert _EXPECTED_SOURCE_SHA in _doc_text()

    def test_doc_records_expected_hmic_digest(self) -> None:
        assert _EXPECTED_HMIC_DIGEST in _doc_text()

    def test_doc_records_sole_residual_reason(self) -> None:
        text = _doc_text()
        assert _SOLE_RESIDUAL_REQ in text
        assert _SOLE_RESIDUAL_REASON in text

    def test_doc_states_final_verdict(self) -> None:
        assert (
            "INDEPENDENTLY VERIFIED -- REPOSITORYIDENTITY MATERIALIZATION COMPLETE"
            in _doc_text()
        )

    def test_doc_disclaims_mutation(self) -> None:
        text = _doc_text().lower()
        assert "no repositoryidentity created or replaced" in text
        assert "no deploymentbinding created" in text

    def test_doc_recommends_exact_next_phase(self) -> None:
        assert "149O.20L.7O.2C" in _doc_text()


# ═══════════════════════════════════════════════════════════════════════════
# 2. RepositoryIdentity contract, independently reconstructed from
#    source this phase (closed field set, UUID4 grammar, idempotent
#    read-first ensure structure).
# ═══════════════════════════════════════════════════════════════════════════


class TestRepositoryIdentityContract:
    def test_schema_version_is_1(self) -> None:
        from pcae.core.repository_identity import SCHEMA_VERSION

        assert SCHEMA_VERSION == 1

    def test_relative_path_is_expected(self) -> None:
        from pcae.core.repository_identity import REPOSITORY_IDENTITY_RELATIVE_PATH

        assert str(REPOSITORY_IDENTITY_RELATIVE_PATH) == str(
            Path(".pcae") / "repository-identity.json"
        )

    def test_required_fields_closed_set(self) -> None:
        from pcae.core.repository_identity import _REQUIRED_FIELDS

        assert _REQUIRED_FIELDS == frozenset(
            {"schema_version", "repository_instance_id", "created_at"}
        )

    def test_uuid4_validator_accepts_expected_id(self) -> None:
        from pcae.core.repository_identity import is_valid_repository_instance_id

        assert is_valid_repository_instance_id(_EXPECTED_UUID) is True

    def test_uuid4_validator_rejects_non_v4(self) -> None:
        from pcae.core.repository_identity import is_valid_repository_instance_id

        # A well-formed UUID1 string must be rejected (version check, not
        # merely a format check).
        assert is_valid_repository_instance_id(
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        ) is False

    def test_validate_document_rejects_unknown_field(self) -> None:
        from pcae.core.repository_identity import (
            RepositoryIdentityMalformedError,
            validate_repository_identity_document,
        )

        doc = {
            "schema_version": 1,
            "repository_instance_id": _EXPECTED_UUID,
            "created_at": "2026-08-18T12:53:43.508Z",
            "extra_field": "unexpected",
        }
        with pytest.raises(RepositoryIdentityMalformedError):
            validate_repository_identity_document(doc)

    def test_validate_document_accepts_expected_shape(self) -> None:
        from pcae.core.repository_identity import validate_repository_identity_document

        doc = {
            "schema_version": 1,
            "repository_instance_id": _EXPECTED_UUID,
            "created_at": "2026-08-18T12:53:43.508Z",
        }
        identity = validate_repository_identity_document(doc)
        assert identity.repository_instance_id == _EXPECTED_UUID

    def test_ensure_source_reads_before_any_write_reference(self) -> None:
        """Structural proof (independent of empirical re-invocation) that
        `ensure_repository_identity` reads first and returns immediately
        on an existing identity -- the write path is only reachable when
        `existing is None`."""

        source = _module_source()
        tree = ast.parse(source)
        func = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "ensure_repository_identity"
        )
        body_dump = ast.dump(func)
        assert "read_repository_identity" in body_dump
        # The first statement must be the `existing = read_repository_identity(root)`
        # assignment, preceding any write-path call.
        non_docstring_body = [
            stmt
            for stmt in func.body
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
        ]
        first_stmt = non_docstring_body[0]
        assert isinstance(first_stmt, ast.Assign)
        assert isinstance(first_stmt.value, ast.Call)
        assert getattr(first_stmt.value.func, "id", None) == "read_repository_identity"

    def test_module_never_calls_chmod_or_chown(self) -> None:
        source = _module_source()
        assert "chmod(" not in source
        assert "chown(" not in source

    def test_module_imports_no_authority_concept(self) -> None:
        # Structural check: no import statement names an authority module.
        tree = ast.parse(_module_source())
        import_modules = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ] + [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ]
        for module_name in import_modules:
            assert "hatp" not in module_name.lower()
            assert "permission_broker" not in module_name.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 3. HBDC-REQ-042 reason-transition branch, independently re-read this
#    phase from the actual consumer logic.
# ═══════════════════════════════════════════════════════════════════════════


class TestHbdcReasonTransitionBranch:
    def test_absent_reason_string_present(self) -> None:
        assert _ABSENT_REASON in _conformance_source()

    def test_matched_reason_string_present(self) -> None:
        assert _SOLE_RESIDUAL_REASON in _conformance_source()

    def test_absent_branch_precedes_binding_branch(self) -> None:
        source = _conformance_source()
        assert source.index(_ABSENT_REASON) < source.index(_SOLE_RESIDUAL_REASON)

    def test_check_id_is_hbdc_req_042_for_both_branches(self) -> None:
        from pcae.core.hatp_class_b_conformance import _check_deployment_identity

        source = inspect.getsource(_check_deployment_identity)
        assert source.count('"HBDC-REQ-042"') >= 3


# ═══════════════════════════════════════════════════════════════════════════
# 4. No local RepositoryIdentity/DeploymentBinding artifact exists in
#    this repository checkout (the deployed Dell artifact is remote,
#    real-host, and gitignored).
# ═══════════════════════════════════════════════════════════════════════════


class TestNoLocalArtifact:
    def test_no_local_repository_identity_file(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()

    def test_gitignore_excludes_repository_identity(self) -> None:
        gitignore = (_REPO_ROOT / ".pcae" / ".gitignore").read_text()
        assert "repository-identity.json" in gitignore
