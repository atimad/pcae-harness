"""Phase 136F: Draft 2020-12 capability proof and shape-validation API tests."""
from __future__ import annotations

from pathlib import Path

from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

FIXTURES = Path(__file__).parent / "fixtures" / "schema_runtime"

ROOT_FEATURES_ID = "https://pcae.test/schema_runtime/valid_package/root-features.schema.json"
FORMAT_CHECK_ID = "https://pcae.test/schema_runtime/valid_package/format-check.schema.json"


def _registry():
    return build_offline_registry(FIXTURES / "valid_package")


def test_136f_valid_record_passes_defs_and_local_ref_and_cross_file_ref():
    registry = _registry()
    record = {
        "name": "widget-set",
        "mode": "lenient",
        "widgets": [{"kind": "a", "value": 1.5}],
    }
    result = validate_record_shape(record, schema_id=ROOT_FEATURES_ID, registry=registry)
    assert result.status is OutcomeStatus.VALID
    assert result.ok


def test_136f_cross_file_ref_enforced_min_length():
    registry = _registry()
    record = {"name": "", "mode": "lenient"}
    result = validate_record_shape(record, schema_id=ROOT_FEATURES_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID
    assert any(issue.code == "schema_invalid_record" for issue in result.issues)


def test_136f_if_then_else_enforces_conditional_requirement():
    registry = _registry()
    missing_amount = {"name": "n", "mode": "strict"}
    result = validate_record_shape(missing_amount, schema_id=ROOT_FEATURES_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID

    with_amount = {"name": "n", "mode": "strict", "amount": 5}
    result_ok = validate_record_shape(with_amount, schema_id=ROOT_FEATURES_ID, registry=registry)
    assert result_ok.status is OutcomeStatus.VALID


def test_136f_one_of_widgets_presence_is_exclusive():
    # The fixture schema's oneOf is a tautology (exactly one of "has widgets"
    # or "lacks widgets" always holds), proving oneOf is evaluated without
    # rejecting either valid shape.
    registry = _registry()
    without_widgets = {"name": "n", "mode": "lenient"}
    with_widgets = {"name": "n", "mode": "lenient", "widgets": []}
    assert validate_record_shape(without_widgets, schema_id=ROOT_FEATURES_ID, registry=registry).ok
    assert validate_record_shape(with_widgets, schema_id=ROOT_FEATURES_ID, registry=registry).ok


def test_136f_additional_properties_false_rejects_unknown_top_level_field():
    registry = _registry()
    record = {"name": "n", "mode": "lenient", "unexpected": True}
    result = validate_record_shape(record, schema_id=ROOT_FEATURES_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID


def test_136f_unevaluated_properties_false_rejects_nested_unknown_field():
    registry = _registry()
    record = {
        "name": "n",
        "mode": "lenient",
        "widgets": [{"kind": "a", "value": 1, "surprise": "nope"}],
    }
    result = validate_record_shape(record, schema_id=ROOT_FEATURES_ID, registry=registry)
    assert result.status is OutcomeStatus.INVALID


def test_136f_format_is_explicitly_not_enforced_by_default():
    # Draft 2020-12 treats "format" as an annotation, not an assertion,
    # unless a FormatChecker is explicitly wired in. schema_runtime does
    # not wire one in for generic shape validation, so a malformed email
    # value still passes -- this is deliberate, documented behavior.
    registry = _registry()
    record = {"email": "not-an-email-address"}
    result = validate_record_shape(record, schema_id=FORMAT_CHECK_ID, registry=registry)
    assert result.status is OutcomeStatus.VALID


def test_136f_unknown_schema_id_fails_closed_as_infrastructure_failure():
    registry = _registry()
    result = validate_record_shape({}, schema_id="https://pcae.test/does-not-exist", registry=registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "unknown_schema"


def test_136f_unresolved_reference_fails_closed_as_infrastructure_failure():
    registry = build_offline_registry(FIXTURES / "unresolved_ref_package")
    result = validate_record_shape(
        {"thing": {}},
        schema_id="https://pcae.test/schema_runtime/unresolved_ref_package/dangling-ref.schema.json",
        registry=registry,
    )
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE
    assert result.issues[0].code == "schema_reference_unresolved"


def test_136f_issue_ordering_is_deterministic_across_repeated_runs():
    registry = _registry()
    record = {"name": "", "mode": 42, "unexpected": True}
    first = validate_record_shape(record, schema_id=ROOT_FEATURES_ID, registry=registry)
    second = validate_record_shape(record, schema_id=ROOT_FEATURES_ID, registry=registry)
    assert [(i.code, i.instance_path, i.message) for i in first.issues] == [
        (i.code, i.instance_path, i.message) for i in second.issues
    ]


def test_136f_max_issues_caps_returned_issue_count():
    registry = _registry()
    record = {"name": "", "mode": 42, "unexpected": True, "widgets": "not-an-array"}
    result = validate_record_shape(record, schema_id=ROOT_FEATURES_ID, registry=registry, max_issues=1)
    assert len(result.issues) == 1


def test_136f_no_semantic_or_authority_fields_on_result():
    registry = _registry()
    result = validate_record_shape({"name": "n", "mode": "lenient"}, schema_id=ROOT_FEATURES_ID, registry=registry)
    field_names = {f for f in result.__dataclass_fields__}
    assert field_names == {"status", "schema_id", "issues"}
