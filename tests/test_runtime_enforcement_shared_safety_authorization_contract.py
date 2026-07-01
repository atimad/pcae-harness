"""Tests for Phase 104C — Shared Runtime Enforcement Safety/Authorization Contract. Design-only. Non-executing."""
from __future__ import annotations
import json as _json, pytest, pathlib
from pcae.core.runtime_enforcement_safety_authorization import (
    AUTHORIZATION_FLAG_NAMES, SAFETY_FLAG_NAMES,
    DEFAULT_AUTHORIZATION_FLAGS, DEFAULT_SAFETY_FLAGS,
    AUTH_FLAG_TO_NO_GO, SAFETY_FLAG_TO_NO_GO,
    validate_all_authorization_false, validate_all_safety_true,
    build_authorization_summary,
)

_DOC_PATH = pathlib.Path("docs/PHASE_104_RUNTIME_ENFORCEMENT_SHARED_SAFETY_AUTHORIZATION_CONTRACT_DESIGN.md")


class TestCanonicalFlags:
    def test_12_auth_flags(self): assert len(AUTHORIZATION_FLAG_NAMES) == 12
    def test_5_safety_flags(self): assert len(SAFETY_FLAG_NAMES) == 5
    def test_all_auth_defaults_false(self):
        for v in DEFAULT_AUTHORIZATION_FLAGS.values(): assert v is False
    def test_all_safety_defaults_true(self):
        for v in DEFAULT_SAFETY_FLAGS.values(): assert v is True

    def test_auth_flags_match_existing_artifacts(self):
        from pcae.core.backend_invocations import RuntimeEnforcementDecision
        a = RuntimeEnforcementDecision()
        for f in AUTHORIZATION_FLAG_NAMES:
            assert hasattr(a, f), f"Decision missing {f}"
            assert getattr(a, f) is False, f"Decision.{f} must be False"

    def test_safety_flags_match_existing_artifacts(self):
        from pcae.core.backend_invocations import RuntimeEnforcementDecision
        a = RuntimeEnforcementDecision()
        for f in SAFETY_FLAG_NAMES:
            assert hasattr(a, f), f"Decision missing {f}"
            assert getattr(a, f) is True, f"Decision.{f} must be True"

    def test_coordinator_flags_match(self):
        from pcae.core.backend_invocations import RuntimeEnforcementCoordinator
        a = RuntimeEnforcementCoordinator()
        for f in AUTHORIZATION_FLAG_NAMES:
            assert hasattr(a, f) and getattr(a, f) is False
        for f in SAFETY_FLAG_NAMES:
            assert hasattr(a, f) and getattr(a, f) is True


class TestNoGoMapping:
    def test_all_auth_flags_mapped(self):
        for f in AUTHORIZATION_FLAG_NAMES: assert f in AUTH_FLAG_TO_NO_GO, f"Missing mapping for {f}"
    def test_all_safety_flags_mapped(self):
        for f in SAFETY_FLAG_NAMES: assert f in SAFETY_FLAG_TO_NO_GO, f"Missing mapping for {f}"
    def test_all_mappings_are_re_nogo(self):
        for v in list(AUTH_FLAG_TO_NO_GO.values()) + list(SAFETY_FLAG_TO_NO_GO.values()):
            assert v.startswith("RE-NOGO-"), f"Not a RE-NOGO ID: {v}"


class TestValidationHelpers:
    def test_all_false_passes(self):
        assert validate_all_authorization_false(DEFAULT_AUTHORIZATION_FLAGS) == []
    def test_any_true_detected(self):
        bad = dict(DEFAULT_AUTHORIZATION_FLAGS); bad["execution_authorized"] = True
        assert "execution_authorized" in validate_all_authorization_false(bad)
    def test_all_safety_true_passes(self):
        assert validate_all_safety_true(DEFAULT_SAFETY_FLAGS) == []
    def test_any_safety_false_detected(self):
        bad = dict(DEFAULT_SAFETY_FLAGS); bad["no_execution"] = False
        assert "no_execution" in validate_all_safety_true(bad)
    def test_helpers_no_exec_calls(self):
        import inspect, subprocess
        src = inspect.getsource(validate_all_authorization_false)
        assert "subprocess" not in src and "os.system" not in src


class TestBuildSummary:
    def test_all_false_summary(self):
        s = build_authorization_summary(DEFAULT_AUTHORIZATION_FLAGS)
        assert len(s) == 12
        for v in s.values(): assert v is False


class TestNoExec:
    def test_module_no_exec_phrases(self):
        text = pathlib.Path("src/pcae/core/runtime_enforcement_safety_authorization.py").read_text()
        assert "subprocess.run" not in text
        assert "os.system" not in text

    def test_no_runtime_in_module(self):
        text = pathlib.Path("src/pcae/core/runtime_enforcement_safety_authorization.py").read_text().lower()
        assert "implements runtime enforcement" not in text


class TestDocReferences:
    def test_doc_exists(self): assert _DOC_PATH.exists()
    def test_doc_refs_104a1(self): assert "104A.1" in _DOC_PATH.read_text()
    def test_doc_refs_104b(self): assert "104B" in _DOC_PATH.read_text()
    def test_doc_refs_no_go(self): assert "RE-NOGO" in _DOC_PATH.read_text()


class TestPreservation:
    def test_decision_preserved(self):
        from pcae.core.backend_invocations import RuntimeEnforcementDecision, RuntimeEnforcementCoordinator, RuntimeEnforcementEvidenceBundle
        assert RuntimeEnforcementDecision().design_only is True
        assert RuntimeEnforcementCoordinator().no_execution is True
        assert RuntimeEnforcementEvidenceBundle().no_execution is True
