from __future__ import annotations

import json

import pytest

from pcae.advisory.context.context_validation import AdvisoryContextValidationError
from pcae.repository_intelligence.change_impact.validation import (
    ChangeImpactValidationError,
)
from pcae.repository_intelligence.consumer_validation import (
    ensure_boundary_material_present,
    ensure_limitations_present,
    ensure_records_have_attribution,
    validate_query_result_shape,
)
from pcae.repository_intelligence.serialization import serialize_deterministic_json


class MinimalQueryResult:
    query_metadata = {"category": "entity_lookup", "target": "entity:x"}
    source_artifact = {"executable_schema_version": "119O.1.0-json-schema"}
    records = ()
    attribution = ()
    limitations = ()
    unknowns = ()
    boundary_disclosures = {}
    disclaimers = {}
    result_status = "ok"


def test_shared_deterministic_json_serializer_preserves_formatting_modes():
    payload = {"z": 1, "a": {"b": 2}}

    compact = serialize_deterministic_json(payload)
    pretty = serialize_deterministic_json(payload, pretty=True)

    assert compact == '{"a": {"b": 2}, "z": 1}'
    assert "\n" not in compact
    assert "\n" in pretty
    assert json.loads(pretty) == payload


def test_shared_query_result_shape_validation_preserves_consumer_error_type():
    validate_query_result_shape(
        MinimalQueryResult(),
        required_fields=("query_metadata", "source_artifact", "result_status"),
        error_type=AdvisoryContextValidationError,
    )

    class MissingSourceArtifact:
        query_metadata = {}
        result_status = "ok"

    with pytest.raises(
        ChangeImpactValidationError,
        match="invalid Query Layer result: missing field 'source_artifact'",
    ):
        validate_query_result_shape(
            MissingSourceArtifact(),
            required_fields=("query_metadata", "source_artifact", "result_status"),
            error_type=ChangeImpactValidationError,
        )


def test_shared_consumer_fail_closed_helpers_preserve_messages():
    with pytest.raises(
        AdvisoryContextValidationError,
        match="content-bearing selected records are missing required attribution",
    ):
        ensure_records_have_attribution(
            has_content=True,
            attribution=(),
            error_type=AdvisoryContextValidationError,
            message="content-bearing selected records are missing required attribution",
        )

    with pytest.raises(
        ChangeImpactValidationError,
        match="Query Layer result is missing required limitation records",
    ):
        ensure_limitations_present((), error_type=ChangeImpactValidationError)

    with pytest.raises(
        AdvisoryContextValidationError,
        match="Query Layer result is missing both boundary_disclosures and disclaimers",
    ):
        ensure_boundary_material_present(
            {}, {}, error_type=AdvisoryContextValidationError
        )
