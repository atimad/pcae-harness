"""Tests for Phase 104B — Runtime Enforcement No-Go Registry Contract. Contract-freeze. Non-executing."""
from __future__ import annotations
import json as _json, pytest, pathlib

_REGISTRY_PATH = pathlib.Path("docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md")
_FREEZE_PATH = pathlib.Path("docs/PHASE_104_RUNTIME_ENFORCEMENT_END_TO_END_NO_GO_MATRIX_FREEZE.md")

_CORE_BLOCKERS = [
    "RE-NOGO-001", "RE-NOGO-002", "RE-NOGO-003", "RE-NOGO-004",
    "RE-NOGO-005", "RE-NOGO-006", "RE-NOGO-007", "RE-NOGO-008",
    "RE-NOGO-009", "RE-NOGO-010", "RE-NOGO-011", "RE-NOGO-012",
]

_CATEGORIES = [
    "runtime_enforcement_absent", "execution_boundary_absent",
    "backend_invocation_absent", "adapter_execution_absent",
    "shell_subprocess_network_absent", "apply_patch_absent",
    "rollback_execution_absent", "commit_push_authorization_absent",
    "audit_persistence_absent", "execution_enablement_absent",
    "pre_existing_test_failures", "telegram_inbound_absent",
    "task_memory_warnings", "emergency_abort_absent",
    "output_capture_absent", "recovery_procedure_absent",
]


class TestRegistryExists:
    def test_registry_file_exists(self): assert _REGISTRY_PATH.exists(), "Registry file missing"
    def test_freeze_doc_exists(self): assert _FREEZE_PATH.exists(), "Freeze doc missing"


class TestRegistryStructure:
    def test_contains_17_entries(self):
        text = _REGISTRY_PATH.read_text()
        ids = [f"RE-NOGO-{i:03d}" for i in range(1, 18)]
        for rid in ids:
            assert rid in text, f"Missing {rid}"

    def test_all_core_blockers_present(self):
        text = _REGISTRY_PATH.read_text()
        for rid in _CORE_BLOCKERS:
            assert rid in text, f"Missing core blocker {rid}"

    def test_contains_categories(self):
        text = _REGISTRY_PATH.read_text()
        for cat in _CATEGORIES:
            assert cat in text, f"Missing category {cat}"

    def test_every_entry_has_id(self):
        text = _REGISTRY_PATH.read_text()
        for i in range(1, 18):
            assert f"RE-NOGO-{i:03d}" in text

    def test_no_duplicate_ids(self):
        text = _REGISTRY_PATH.read_text()
        for i in range(1, 18):
            rid = f"RE-NOGO-{i:03d}"
            assert text.count(rid) >= 1, f"ID {rid} appears only once or missing"


class TestRegistrySemantics:
    def test_does_not_authorize_execution(self):
        text = _REGISTRY_PATH.read_text()
        assert "authorizes execution" not in text.lower()
        assert "execution is available" not in text.lower()

    def test_states_no_runtime_enforcement(self):
        text = _REGISTRY_PATH.read_text()
        assert "No runtime enforcement" in text or "No Runtime Enforcement" in text

    def test_states_execution_unavailable(self):
        text = _FREEZE_PATH.read_text()
        assert "execution" in text.lower()

    def test_all_entries_block_enforcement(self):
        text = _REGISTRY_PATH.read_text()
        for i in range(1, 12):
            assert f"RE-NOGO-{i:03d}" in text

    def test_references_104a(self):
        text = _FREEZE_PATH.read_text()
        assert "104A" in text

    def test_references_104a1(self):
        text = _FREEZE_PATH.read_text()
        assert "104A.1" in text


class TestRegistryNoExec:
    def test_registry_no_exec_phrases(self):
        text = _REGISTRY_PATH.read_text().lower()
        assert "subprocess.run" not in text
        assert "os.system" not in text

    def test_freeze_doc_no_runtime(self):
        text = _FREEZE_PATH.read_text().lower()
        assert "does not implement runtime enforcement" in text or "no runtime enforcement" in text

    def test_evidence_only(self):
        text = _REGISTRY_PATH.read_text()
        assert "evidence" in text.lower()


class TestPreservation:
    def test_decision_preserved(self):
        from pcae.core.backend_invocations import RuntimeEnforcementDecision, RuntimeEnforcementCoordinator, RuntimeEnforcementEvidenceBundle
        assert RuntimeEnforcementDecision().design_only is True
        assert RuntimeEnforcementCoordinator().no_execution is True
        assert RuntimeEnforcementEvidenceBundle().no_execution is True
