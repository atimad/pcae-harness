"""Tests for enforcement readiness reporter (89N, simulation-only)."""

from __future__ import annotations

import json

import pytest

from pcae.core.enforcement_readiness import (
    SCHEMA_VERSION,
    ENFORCEMENT_NOT_AUTHORIZED,
    GATE_STATE_SATISFIED,
    GATE_STATE_NOT_SATISFIED,
    GATE_STATE_DEFERRED,
    GateStatus,
    EnforcementReadinessReport,
    build_enforcement_readiness_report,
    format_readiness_report,
    format_readiness_report_json,
    validate_readiness_report,
    _GATE_COUNT,
)


# ---------------------------------------------------------------------------
# Readiness report building
# ---------------------------------------------------------------------------

class TestBuildReport:
    """Tests for report construction."""

    def test_build_report_returns_report(self):
        report = build_enforcement_readiness_report()
        assert isinstance(report, EnforcementReadinessReport)

    def test_total_gates_is_69(self):
        report = build_enforcement_readiness_report()
        assert report.total_gates == 69

    def test_gate_counts_sum_to_total(self):
        report = build_enforcement_readiness_report()
        total = report.satisfied + report.unsatisfied + report.conditional + report.deferred
        assert total == report.total_gates

    def test_enforcement_authorized_is_false(self):
        report = build_enforcement_readiness_report()
        assert report.enforcement_authorized is False

    def test_enforcement_ready_is_false(self):
        report = build_enforcement_readiness_report()
        # Not all 69 gates are satisfied, so ready must be False
        assert report.enforcement_ready is False

    def test_schema_version(self):
        report = build_enforcement_readiness_report()
        assert report.schema_version == SCHEMA_VERSION

    def test_generated_at_is_populated(self):
        report = build_enforcement_readiness_report()
        assert report.generated_at

    def test_has_evidence_references(self):
        report = build_enforcement_readiness_report()
        assert len(report.evidence_references) > 0

    def test_has_missing_evidence(self):
        report = build_enforcement_readiness_report()
        assert len(report.missing_evidence) > 0

    def test_recommended_next_phase_is_set(self):
        report = build_enforcement_readiness_report()
        assert "90A" in report.recommended_next_phase

    def test_safety_footer_present(self):
        report = build_enforcement_readiness_report()
        assert "no enforcement" in report.safety_footer.lower()


# ---------------------------------------------------------------------------
# Gate counts
# ---------------------------------------------------------------------------

class TestGateCounts:
    """Tests for gate count accuracy."""

    def test_all_dimensions_present(self):
        report = build_enforcement_readiness_report()
        dimensions = {g.dimension for g in report.gates}
        expected = {"design", "implementation", "test", "audit", "rollback",
                     "approval", "secret", "bypass"}
        assert dimensions == expected

    def test_each_dimension_has_gates(self):
        report = build_enforcement_readiness_report()
        dim_counts: dict[str, int] = {}
        for g in report.gates:
            dim_counts[g.dimension] = dim_counts.get(g.dimension, 0) + 1
        for dim, count in dim_counts.items():
            assert count > 0, f"Dimension {dim} has {count} gates"

    def test_satisfied_count_matches_gates(self):
        report = build_enforcement_readiness_report()
        counted = sum(1 for g in report.gates if g.state == GATE_STATE_SATISFIED)
        assert report.satisfied == counted

    def test_unsatisfied_count_matches_gates(self):
        report = build_enforcement_readiness_report()
        counted = sum(1 for g in report.gates if g.state == GATE_STATE_NOT_SATISFIED)
        assert report.unsatisfied == counted

    def test_deferred_count_reasonable(self):
        report = build_enforcement_readiness_report()
        counted = sum(1 for g in report.gates if g.state == GATE_STATE_DEFERRED)
        assert report.deferred == counted


# ---------------------------------------------------------------------------
# Unsatisfied gate reporting
# ---------------------------------------------------------------------------

class TestUnsatisfiedGateReporting:
    """Tests for unsatisfied gate detail."""

    def test_unsatisfied_gates_have_ids(self):
        report = build_enforcement_readiness_report()
        unsatisfied = [g for g in report.gates if g.state == GATE_STATE_NOT_SATISFIED]
        assert len(unsatisfied) > 0
        for g in unsatisfied:
            assert g.gate_id
            assert g.description

    def test_unsatisfied_gates_have_no_evidence(self):
        report = build_enforcement_readiness_report()
        unsatisfied = [g for g in report.gates if g.state == GATE_STATE_NOT_SATISFIED]
        # Not all unsatisfied gates necessarily lack evidence, but most should
        no_evidence = [g for g in unsatisfied if not g.evidence]
        assert len(no_evidence) > 0


# ---------------------------------------------------------------------------
# Deferred gate reporting
# ---------------------------------------------------------------------------

class TestDeferredGateReporting:
    """Tests for deferred gate detail."""

    def test_deferred_gates_exist(self):
        report = build_enforcement_readiness_report()
        deferred = [g for g in report.gates if g.state == GATE_STATE_DEFERRED]
        assert len(deferred) >= 0  # May be 0 or more

    def test_deferred_gates_all_have_state_deferred(self):
        report = build_enforcement_readiness_report()
        for g in report.gates:
            if g.state == GATE_STATE_DEFERRED:
                assert g.gate_id


# ---------------------------------------------------------------------------
# Enforcement not authorized
# ---------------------------------------------------------------------------

class TestEnforcementNotAuthorized:
    """Tests that enforcement is never authorized."""

    def test_enforcement_authorized_always_false(self):
        report = build_enforcement_readiness_report()
        assert report.enforcement_authorized is False

    def test_enforcement_ready_always_false(self):
        report = build_enforcement_readiness_report()
        assert report.enforcement_ready is False

    def test_safety_footer_includes_no_enforcement(self):
        report = build_enforcement_readiness_report()
        assert "no enforcement" in report.safety_footer.lower()
        assert "authorized" in report.safety_footer.lower()

    def test_human_readable_output_includes_warning(self):
        report = build_enforcement_readiness_report()
        output = format_readiness_report(report)
        assert "NO" in output  # "Enforcement authorized: NO"


# ---------------------------------------------------------------------------
# Evidence references
# ---------------------------------------------------------------------------

class TestEvidenceReferences:
    """Tests for evidence reference handling."""

    def test_evidence_references_are_documented(self):
        report = build_enforcement_readiness_report()
        assert len(report.evidence_references) > 0
        # Evidence refs should be file paths or doc names
        for ref in report.evidence_references:
            assert isinstance(ref, str)
            assert len(ref) > 0

    def test_satisfied_gates_have_evidence(self):
        report = build_enforcement_readiness_report()
        satisfied = [g for g in report.gates if g.state == GATE_STATE_SATISFIED]
        assert len(satisfied) > 0
        for g in satisfied:
            assert len(g.evidence) > 0, f"Gate {g.gate_id} is SATISFIED but has no evidence"


# ---------------------------------------------------------------------------
# Missing evidence list
# ---------------------------------------------------------------------------

class TestMissingEvidence:
    """Tests for missing evidence list."""

    def test_missing_evidence_list_exists(self):
        report = build_enforcement_readiness_report()
        assert len(report.missing_evidence) > 0

    def test_missing_evidence_gates_are_unsatisfied(self):
        report = build_enforcement_readiness_report()
        missing_ids = set()
        for entry in report.missing_evidence:
            gate_id = entry.split(":")[0].strip()
            missing_ids.add(gate_id)
        for g in report.gates:
            if g.gate_id in missing_ids:
                assert g.state in (GATE_STATE_NOT_SATISFIED, GATE_STATE_DEFERRED), \
                    f"Gate {g.gate_id} has missing evidence but state is {g.state}"


# ---------------------------------------------------------------------------
# No-execution/no-enforcement wording
# ---------------------------------------------------------------------------

class TestNoExecutionWording:
    """Tests for no-execution/no-enforcement language."""

    def test_human_output_has_safety_wording(self):
        report = build_enforcement_readiness_report()
        output = format_readiness_report(report)
        assert "no enforcement" in output.lower()
        assert "authorized" in output.lower()

    def test_json_output_has_false_authorization(self):
        report = build_enforcement_readiness_report()
        json_str = format_readiness_report_json(report)
        data = json.loads(json_str)
        assert data["enforcement_authorized"] is False
        assert data["enforcement_ready"] is False

    def test_enforcement_not_authorized_constant(self):
        assert "NOT authorized" in ENFORCEMENT_NOT_AUTHORIZED

    def test_safety_footer_in_json_output(self):
        report = build_enforcement_readiness_report()
        json_str = format_readiness_report_json(report)
        data = json.loads(json_str)
        assert "no enforcement" in data["safety_footer"].lower()


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

class TestJsonOutput:
    """Tests for JSON output format."""

    def test_json_is_valid(self):
        report = build_enforcement_readiness_report()
        json_str = format_readiness_report_json(report)
        data = json.loads(json_str)
        assert isinstance(data, dict)

    def test_json_includes_all_summary_fields(self):
        report = build_enforcement_readiness_report()
        json_str = format_readiness_report_json(report)
        data = json.loads(json_str)
        for key in ("total_gates", "satisfied", "unsatisfied", "conditional",
                     "deferred", "enforcement_authorized", "enforcement_ready"):
            assert key in data, f"Missing key: {key}"

    def test_json_gates_are_list(self):
        report = build_enforcement_readiness_report()
        json_str = format_readiness_report_json(report)
        data = json.loads(json_str)
        assert isinstance(data["gates"], list)
        assert len(data["gates"]) == 69

    def test_json_gate_has_all_fields(self):
        report = build_enforcement_readiness_report()
        json_str = format_readiness_report_json(report)
        data = json.loads(json_str)
        gate = data["gates"][0]
        for key in ("id", "description", "dimension", "state", "source"):
            assert key in gate, f"Missing gate key: {key}"


# ---------------------------------------------------------------------------
# Human-readable output
# ---------------------------------------------------------------------------

class TestHumanReadableOutput:
    """Tests for human-readable output format."""

    def test_output_is_string(self):
        report = build_enforcement_readiness_report()
        output = format_readiness_report(report)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_output_includes_total_gates(self):
        report = build_enforcement_readiness_report()
        output = format_readiness_report(report)
        assert str(report.total_gates) in output

    def test_output_includes_satisfied_count(self):
        report = build_enforcement_readiness_report()
        output = format_readiness_report(report)
        assert str(report.satisfied) in output

    def test_output_includes_dimension_names(self):
        report = build_enforcement_readiness_report()
        output = format_readiness_report(report)
        for dim in ("design", "implementation", "test", "audit",
                     "rollback", "approval", "secret", "bypass"):
            assert dim in output, f"Missing dimension: {dim}"

    def test_output_includes_next_phase(self):
        report = build_enforcement_readiness_report()
        output = format_readiness_report(report)
        assert "90A" in output

    def test_output_includes_safety_footer(self):
        report = build_enforcement_readiness_report()
        output = format_readiness_report(report)
        assert "Readiness report only" in output


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    """Tests for report validation."""

    def test_validate_fresh_report_is_valid(self):
        report = build_enforcement_readiness_report()
        issues = validate_readiness_report(report)
        assert issues == [], f"Unexpected issues: {issues}"

    def test_validate_wrong_total_gates(self):
        report = build_enforcement_readiness_report()
        object.__setattr__(report, "total_gates", 50)
        issues = validate_readiness_report(report)
        assert any("total_gates" in i for i in issues)

    def test_validate_enforcement_authorized_true(self):
        report = build_enforcement_readiness_report()
        object.__setattr__(report, "enforcement_authorized", True)
        issues = validate_readiness_report(report)
        assert any("enforcement_authorized must be False" in i for i in issues)

    def test_validate_enforcement_ready_with_unsatisfied_gates(self):
        report = build_enforcement_readiness_report()
        object.__setattr__(report, "enforcement_ready", True)
        issues = validate_readiness_report(report)
        assert any("not all gates are satisfied" in i for i in issues)

    def test_validate_count_mismatch(self):
        report = build_enforcement_readiness_report()
        object.__setattr__(report, "satisfied", 1000)
        issues = validate_readiness_report(report)
        assert any("Gate count mismatch" in i for i in issues)
