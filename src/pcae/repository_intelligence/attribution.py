"""Source attribution and uncertainty/verification state builders (120D pipeline stage 3).

Every builder here produces a dict shaped to match one of the shared
Repository Intelligence schema components
(``schemas/repository_intelligence/shared/``). Attribution is attached
before extraction proceeds and is never dropped or weakened by later
pipeline stages, per 120B Section 8 / 120D Section 7.
"""

from __future__ import annotations


def source_locator(locator_type: str, locator_value: str) -> dict:
    return {"locator_type": locator_type, "locator_value": locator_value}


def source_attribution_record(
    *,
    source_id: str,
    source_type: str,
    locator_type: str,
    locator_value: str,
    source_claim_relationship: str,
    source_support_level: str,
    source_verification_state: str,
    source_staleness_state: str,
    source_limitations: list[str],
) -> dict:
    """Build a ``source_attribution_record.schema.json``-shaped dict."""
    return {
        "source_id": source_id,
        "source_type": source_type,
        "source_locator": source_locator(locator_type, locator_value),
        "source_claim_relationship": source_claim_relationship,
        "source_support_level": source_support_level,
        "source_verification_state": source_verification_state,
        "source_staleness_state": source_staleness_state,
        "source_limitations": list(source_limitations),
    }


def file_path_attribution(
    *, source_id: str, path: str, commit_sha: str, relationship: str = "documents"
) -> dict:
    """A deterministic attribution record for a repository-local file path.

    ``source_verification_state`` is ``verified`` only in the narrow
    sense that the path's existence was observed at ``commit_sha``;
    contents were not parsed, which is disclosed in
    ``source_limitations``.
    """
    return source_attribution_record(
        source_id=source_id,
        source_type="file",
        locator_type="file_path",
        locator_value=path,
        source_claim_relationship=relationship,
        source_support_level="direct",
        source_verification_state="verified",
        source_staleness_state="current",
        source_limitations=[
            "Existence and path observed via deterministic filesystem "
            f"listing at commit {commit_sha}; file contents were not parsed."
        ],
    )


def commit_attribution(*, source_id: str, commit_sha: str) -> dict:
    return source_attribution_record(
        source_id=source_id,
        source_type="commit",
        locator_type="commit_sha",
        locator_value=commit_sha,
        source_claim_relationship="documents",
        source_support_level="direct",
        source_verification_state="verified",
        source_staleness_state="current",
        source_limitations=[
            "Commit SHA observed via `git rev-parse HEAD`; commit contents "
            "beyond the paths explicitly listed elsewhere in this snapshot "
            "were not enumerated."
        ],
    )


def verification_state(
    *,
    state_value: str,
    state_reason: str,
    commit_sha: str,
    state_limitations: list[str],
) -> dict:
    """Build an ``uncertainty_verification_state.schema.json``-shaped dict.

    Used wherever a schema field references the full object (not just
    ``#/$defs/state_value``).
    """
    return {
        "state_value": state_value,
        "state_reason": state_reason,
        "supporting_sources": [],
        "state_limitations": list(state_limitations),
        "timestamp_or_snapshot_context": {
            "context_type": "commit",
            "context_value": commit_sha,
        },
    }


def limitation_record(
    *,
    limitation_type: str,
    limitation_description: str,
    affected_claims_or_fields: list[str] | None = None,
    severity_or_scope: str | None = None,
    mitigation_or_follow_up: str | None = None,
) -> dict:
    record: dict = {
        "limitation_type": limitation_type,
        "limitation_description": limitation_description,
    }
    if affected_claims_or_fields is not None:
        record["affected_claims_or_fields"] = list(affected_claims_or_fields)
    if severity_or_scope is not None:
        record["severity_or_scope"] = severity_or_scope
    if mitigation_or_follow_up is not None:
        record["mitigation_or_follow_up"] = mitigation_or_follow_up
    return record
