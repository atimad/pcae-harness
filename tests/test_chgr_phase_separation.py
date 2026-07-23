"""Phase 143E: CHGR / canonical phase report structural separation tests.

CHGR-001 Sec.15/CHGR-REQ-128 through CHGR-REQ-134: a CHGR and a canonical
phase report SHALL remain permanently, structurally separate artifact
classes, with no shared write path and no code path that could confuse
one for the other.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from pcae.governance.inspection import InspectionFailure, inspect_artifact_at_path
from pcae.governance.verification import VerificationFailure, verify_artifact_at_path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures" / "chgr"
GOVERNANCE_MODULE_FILES = (
    REPO_ROOT / "src" / "pcae" / "governance" / "inspection.py",
    REPO_ROOT / "src" / "pcae" / "governance" / "verification.py",
    REPO_ROOT / "src" / "pcae" / "commands" / "governance_record.py",
)

_FORBIDDEN_STRINGS = (
    ".pcae/phase-completion-report.md",
    ".pcae/phase-completion-metadata.json",
    ".pcae/phase-reports",
)


@pytest.mark.parametrize("module_path", GOVERNANCE_MODULE_FILES)
def test_143e_no_chgr_module_imports_phase_reports_machinery(module_path):
    tree = ast.parse(module_path.read_text())
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    forbidden = {
        "pcae.core.phase_reports",
        "pcae.core.phase_report_trust",
        "pcae.core.phase_report_view",
        "pcae.core.canonical_artifact_promotion",
    }
    assert not (imported_modules & forbidden), (module_path, imported_modules & forbidden)


@pytest.mark.parametrize("module_path", GOVERNANCE_MODULE_FILES)
def test_143e_no_chgr_module_source_mentions_phase_completion_paths(module_path):
    text = module_path.read_text()
    for forbidden in _FORBIDDEN_STRINGS:
        assert forbidden not in text, (module_path, forbidden)


def test_143e_phase_report_shaped_document_rejected_by_inspection():
    path = FIXTURES / "invalid_phase_report_substitution.json"
    outcome = inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, InspectionFailure)


def test_143e_phase_report_shaped_document_rejected_by_verification():
    path = FIXTURES / "invalid_phase_report_substitution.json"
    outcome = verify_artifact_at_path(path, artifact_bytes=path.read_bytes())
    assert isinstance(outcome, VerificationFailure)
    assert outcome.error_code == "PHASE_REPORT_SUBSTITUTION"


def test_143e_a_chgr_artifact_never_carries_a_phase_id_field():
    """A CHGR document carries a CHGR envelope (schema_id/record_type), not
    a phase_id -- the two shapes are structurally disjoint by construction,
    documenting the symmetric half of CHGR-REQ-128's separation guarantee."""
    doc = json.loads((FIXTURES / "valid_record_published.json").read_text())
    assert "phase_id" not in doc
    assert doc["schema_id"].startswith("https://pcae.local/schemas/chgr/")
    assert doc["record_type"] == "human_governance_record"


def test_143e_existing_phase_completion_artifacts_untouched_by_governance_module_import(tmp_path):
    """Importing pcae.governance and running inspect/verify against fixtures
    must not create, modify, or touch any .pcae/phase-completion-* file in
    the real repository."""
    report_path = REPO_ROOT / ".pcae" / "phase-completion-report.md"
    metadata_path = REPO_ROOT / ".pcae" / "phase-completion-metadata.json"

    def _digest(path: Path) -> str | None:
        if not path.exists():
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()

    before_report = _digest(report_path)
    before_metadata = _digest(metadata_path)

    fixture_path = FIXTURES / "valid_record_published.json"
    inspect_artifact_at_path(fixture_path, artifact_bytes=fixture_path.read_bytes())
    verify_artifact_at_path(fixture_path, artifact_bytes=fixture_path.read_bytes())

    assert _digest(report_path) == before_report
    assert _digest(metadata_path) == before_metadata


def test_143e_no_governance_module_defines_a_phase_complete_or_write_canonical_report_function():
    for module_path in GOVERNANCE_MODULE_FILES:
        tree = ast.parse(module_path.read_text())
        function_names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert "write_canonical_report" not in function_names
        assert not any("phase_complete" in name for name in function_names)
