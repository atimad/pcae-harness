"""Historical Memory deterministic construction (127D pipeline stages 1-9).

Consumes an existing Repository Knowledge Snapshot (reached exclusively
through the Track 121 Query Layer, for structural entity cross-reference
only -- never as a temporal source, per 127D Section 2.1) plus the
repository's own already-governed provenance record: git commit history
and ``tasks/done/*.md`` task contracts (127D Section 2.3-2.6). Never
reads ``.pcae/phase-reports/`` as a required input (gitignored, not
durable -- 127D Section 2.2). Never parses CHANGELOG.md/PROJECT_STATUS.md
as an extraction source (127D Section 2.5).

No relationship, event, or claim is created without direct,
deterministic support in a git commit or a task contract's own already-
labeled Markdown sections. This module never imports ``subprocess`` --
all git/filesystem discovery is delegated to ``git_source.py``, mirroring
exactly how ``snapshot_builder.py`` delegates to ``source_inventory.py``
for Track 120.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pcae.repository_intelligence.attribution import (
    limitation_record,
    source_attribution_record,
    source_locator,
    verification_state,
)
from pcae.repository_intelligence.consumer_validation import (
    ensure_boundary_material_present,
    ensure_limitations_present,
    validate_query_result_shape,
)
from pcae.repository_intelligence.historical_memory.git_source import (
    GitTag,
    HistoricalSourceError,
    TaskContract,
    TaskIntroduction,
    git_head_commit_sha,
    list_git_tags,
    list_task_contract_files,
    parse_task_contract,
    phase_code_from_title,
    resolve_task_introduction,
)
from pcae.repository_intelligence.query.query_engine import (
    QueryExecutionError,
    execute_query,
)
from pcae.repository_intelligence.query.query_request import QueryRequest
from pcae.repository_intelligence.query.query_result import QueryResult
from pcae.repository_intelligence.query.snapshot_loader import (
    SnapshotCompatibilityError,
    SnapshotLoadError,
    load_snapshot,
)

ARTIFACT_CONTRACT_VERSION = "119E.1.0"
SCHEMA_CONCEPT_VERSION = "119C.1.0-concept"
ENVELOPE_EXECUTABLE_SCHEMA_VERSION = "119K.1.0-json-schema"
HISTORICAL_EXECUTABLE_SCHEMA_VERSION = "119Q.1.0-json-schema"

HISTORICAL_MEMORY_SNAPSHOT_DISCLAIMER = (
    "This Historical Memory Snapshot describes declared repository "
    "history and lineage. It is not Repository State, does not decide "
    "lifecycle standing, does not prove historical truth or "
    "completeness, and does not authorize action or execution."
)

READ_ONLY_BOUNDARY = (
    "This artifact is descriptive and read-only. It does not mutate "
    "repository state, lifecycle state, or any other PCAE subsystem "
    "state."
)
DECISION_BOUNDARY = (
    "This artifact is not a decision. Decision Evaluation is the sole "
    "decision maker in PCAE. This artifact provides context only."
)
EXECUTION_BOUNDARY = (
    "This artifact does not execute commands, invoke runtimes, "
    "mediate shells, route execution, or authorize execution. "
    "Execution remains unavailable."
)

DISCLAIMERS = {
    "non_decision_disclaimer": (
        "This artifact is not a decision. Decision Evaluation remains "
        "required for PCAE decisions."
    ),
    "no_execution_disclaimer": (
        "This artifact does not execute commands, invoke runtimes, "
        "mediate shells, route execution, or authorize execution. "
        "Execution remains unavailable."
    ),
    "advisory_non_authority_disclaimer": (
        "This artifact may inform Advisory context but does not "
        "convert Advisory output into approval, permission, "
        "enforcement, or execution."
    ),
    "evidence_boundary_disclaimer": (
        "This artifact may link to Evidence but does not replace, "
        "bypass, or preempt the Evidence subsystem."
    ),
    "repository_state_boundary_disclaimer": (
        "This artifact may describe repository context but does not "
        "replace Repository State."
    ),
}

BOUNDARY_DISCLOSURES = {
    "read_only": True,
    "no_execution": True,
    "non_decision": True,
    "advisory_non_authority": True,
    "decision_evaluation_required": True,
    "no_repository_mutation": True,
    "no_lifecycle_mutation": True,
    "no_evidence_replacement": True,
    "no_repository_state_replacement": True,
}

# 127D Section 5.2: task-contract title/mode signal -> frozen event_type.
# Frozen; do not add, rename, or reinterpret values here without a
# governed contract-amendment phase.
_HARDENING_TITLE_RE = re.compile(r"hardening", re.IGNORECASE)
_REPAIR_TITLE_RE = re.compile(r"repair|\bfix\b", re.IGNORECASE)
_CONTRACT_FREEZE_TITLE_RE = re.compile(r"contract freeze", re.IGNORECASE)
_CONTRACT_VERIFICATION_TITLE_RE = re.compile(r"contract verification", re.IGNORECASE)
_ARCHITECTURE_REVIEW_TITLE_RE = re.compile(r"architecture.*review|review.*architecture", re.IGNORECASE)
_SCHEMA_TITLE_RE = re.compile(r"schema", re.IGNORECASE)
_PROTOTYPE_TITLE_RE = re.compile(r"prototype", re.IGNORECASE)

_NO_TASK_HISTORY_LIMITATION = (
    "This Historical Memory Snapshot v1 builder classifies task-contract "
    "signal deterministically from '## Title'/'## Mode' section content "
    "only. Only a minority of this repository's tasks/done/*.md files "
    "follow the 'Phase <ID> <Name>' title convention with a populated "
    "Mode field (confirmed by direct inspection during 127D planning: "
    "20 of several hundred). Task contracts that do not match a known "
    "pattern are represented with event_type/relationship classification "
    "'unknown' rather than guessed -- this is an honest data-consistency "
    "limitation of the source corpus, not a builder defect."
)
_NO_SUBPHASE_GOVERNANCE_EVENTS_LIMITATION = (
    "This graph declares zero 'governance_check_completed', "
    "'report_generated', 'metadata_promoted', or 'notification_sent' "
    "events because this repository does not durably (git-tracked) "
    "record sub-phase-granularity governance actions outside "
    "'.pcae/phase-reports/', which is gitignored and therefore excluded "
    "as a required source (127D Section 2.2). This is an inherited "
    "repository data-availability limitation, not a Historical Memory "
    "Builder deficiency; it will resolve automatically if a future, "
    "separately governed change makes this data durably git-tracked."
)
_NO_DECISION_RECORDS_LIMITATION = (
    "This graph declares zero decision_history_record entries. This "
    "repository's governed decision points are recorded in prose within "
    "phase documents (docs/PHASE_*.md), not in any structured, "
    "task-contract-adjacent field a deterministic rule can extract "
    "without interpretation. This is an inherited repository "
    "data-availability limitation, not a Historical Memory Builder "
    "deficiency."
)
_NO_PHASE_LINEAGE_TRAVERSAL_LIMITATION = (
    "phase_lineage_record predecessor_phase_ids/successor_phase_ids are "
    "left empty in v1. These are declared fields, not computed by "
    "traversal (127B Section 6); no source content this builder consumes "
    "explicitly declares phase predecessor/successor relationships, so "
    "populating them would require inference, which is forbidden."
)


class HistoricalGenerationError(RuntimeError):
    """Raised when the Historical Memory Builder must fail closed."""


def _node_id_safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "-", value)


def _event_id(event_type: str, commit_sha: str | None, task_id: str) -> str:
    anchor = commit_sha if commit_sha else "unknown"
    return f"event:{event_type}:{anchor}:{_node_id_safe(task_id)}"


def _claim_id(task_id: str) -> str:
    return f"claim:{_node_id_safe(task_id)}"


def _record_id(prefix: str, task_id: str) -> str:
    return f"{prefix}:{_node_id_safe(task_id)}"


def _relationship_id(relationship_type: str, source_ref_id: str, target_ref_id: str) -> str:
    return f"relationship:{relationship_type}:{source_ref_id}->{target_ref_id}"


def _historical_reference(reference_id: str, reference_type: str) -> dict[str, Any]:
    return {"reference_id": reference_id, "reference_type": reference_type}


def _graph_wide_period() -> dict[str, Any]:
    """A `historical_period`-shaped object for an `unknown_gap` that is
    not scoped to any single period.

    128F repair: `unknown_gap.affected_period` is a `historical_period`
    object per the frozen 119Q schema, not a plain string -- a
    pre-existing, 127E-introduced schema-conformance defect independently
    discovered by 128F's own recursive schema validation. `period_start`/
    `period_end` are `["string", "null"]` per schema; `null` here is
    honest (this gap is not bounded to a specific start/end), not a
    fabricated value.
    """
    return {
        "period_id": "period:graph-wide",
        "period_description": "graph-wide",
        "period_start": None,
        "period_end": None,
    }


def _query_snapshot_material(snapshot_path: Path) -> tuple[QueryResult, QueryResult]:
    try:
        limitations_result = execute_query(
            snapshot_path, QueryRequest(category="limitation_lookup")
        )
        boundary_result = execute_query(
            snapshot_path, QueryRequest(category="boundary_lookup")
        )
    except QueryExecutionError as exc:
        raise HistoricalGenerationError(str(exc)) from exc

    for result in (limitations_result, boundary_result):
        validate_query_result_shape(
            result,
            required_fields=(
                "query_metadata",
                "source_artifact",
                "records",
                "attribution",
                "limitations",
                "boundary_disclosures",
                "disclaimers",
                "result_status",
            ),
            error_type=HistoricalGenerationError,
        )

    ensure_limitations_present(
        limitations_result.limitations, error_type=HistoricalGenerationError
    )
    ensure_boundary_material_present(
        boundary_result.boundary_disclosures,
        boundary_result.disclaimers,
        error_type=HistoricalGenerationError,
    )
    return limitations_result, boundary_result


def _load_and_validate_snapshot(snapshot_path: Path) -> dict[str, Any]:
    try:
        raw_snapshot = load_snapshot(snapshot_path)
    except (SnapshotLoadError, SnapshotCompatibilityError) as exc:
        raise HistoricalGenerationError(str(exc)) from exc

    entities = raw_snapshot.get("architectural_entities", [])
    if not isinstance(entities, list):
        raise HistoricalGenerationError(
            "source Repository Knowledge Snapshot has a malformed "
            "architectural_entities field; refusing to derive Historical "
            "Memory from a corrupted artifact."
        )
    return raw_snapshot


def _classify_task(contract: TaskContract) -> tuple[str, str | None]:
    """Deterministically classify a task contract's event_type and phase_code.

    Returns ``(event_type, phase_code)``. ``phase_code`` is ``None``
    when the title does not follow the 'Phase <ID> ...' convention
    (127D Section 5.2's critical v1 scope finding). ``event_type``
    falls back to 'unknown' -- the frozen enum's own honest fallback --
    rather than guessing.
    """
    phase_code = phase_code_from_title(contract.title)
    title = contract.title or ""
    mode = (contract.mode or "").strip().lower()

    if phase_code is None:
        return "unknown", None

    if _CONTRACT_FREEZE_TITLE_RE.search(title):
        return "contract_frozen", phase_code
    if _CONTRACT_VERIFICATION_TITLE_RE.search(title):
        return "contract_verified", phase_code
    if _ARCHITECTURE_REVIEW_TITLE_RE.search(title):
        return "architecture_reviewed", phase_code
    if mode == "architecture":
        return "architecture_defined", phase_code
    if _HARDENING_TITLE_RE.search(title):
        return "hardening_completed", phase_code
    if _REPAIR_TITLE_RE.search(title):
        return "repair_completed", phase_code
    if mode == "verification" and _SCHEMA_TITLE_RE.search(title):
        return "schema_verified", phase_code
    if _PROTOTYPE_TITLE_RE.search(title):
        return "prototype_added", phase_code
    if mode == "implementation" and _SCHEMA_TITLE_RE.search(title):
        return "schema_implemented", phase_code
    if mode == "implementation":
        return "integration_recorded", phase_code
    return "unknown", phase_code


def _build_phase_records(
    repo_root: Path, task_files: tuple[str, ...], commit_sha: str
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Build historical_events, phase_lineage, historical_claims,
    repair_hardening_history, and dependency_sources-equivalent attribution,
    one pass over every task contract file (127D pipeline stages 3-7).
    """
    events: list[dict[str, Any]] = []
    phase_lineage: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    repair_hardening: list[dict[str, Any]] = []
    all_attribution: list[dict[str, Any]] = []

    phase_code_index: dict[str, str] = {}  # phase_code -> task_id, for relationship resolution

    parsed: list[tuple[TaskContract, TaskIntroduction, str, str | None]] = []
    for relative_path in task_files:
        contract = parse_task_contract(repo_root / relative_path)
        if not contract.task_id:
            # Fails closed for this one record only -- a task contract
            # without its own Task ID cannot be attributed or identified
            # deterministically; it is omitted, never fabricated.
            continue
        introduction = resolve_task_introduction(repo_root, relative_path)
        event_type, phase_code = _classify_task(contract)
        parsed.append((contract, introduction, event_type, phase_code))
        if phase_code:
            phase_code_index[phase_code] = contract.task_id

    # Chronological ordering (127D Section 5.3 / 127C Finding 2 resolution):
    # non-null commit dates first (stable sort), null-boundary records
    # (unresolved introduction) sort after, tie-broken by task_id.
    def _sort_key(item: tuple[TaskContract, TaskIntroduction, str, str | None]):
        contract, introduction, _event_type, _phase_code = item
        has_date = introduction.commit_author_date_utc is not None
        return (0 if has_date else 1, introduction.commit_author_date_utc or "", contract.task_id or "")

    parsed.sort(key=_sort_key)

    for contract, introduction, event_type, phase_code in parsed:
        task_id = contract.task_id or ""
        source_attr = source_attribution_record(
            source_id=f"source:task-contract:{_node_id_safe(task_id)}",
            source_type="file",
            locator_type="task_id",
            locator_value=task_id,
            source_claim_relationship="documents",
            source_support_level="direct",
            source_verification_state="verified" if introduction.commit_sha else "unverified",
            source_staleness_state="current",
            source_limitations=[
                "Existence and section content observed via deterministic "
                f"Markdown-section extraction from {contract.relative_path!r}; "
                "prose content beyond labeled sections was not interpreted."
            ],
        )
        source_attribution = [source_attr]
        if introduction.commit_sha:
            source_attribution.append(
                source_attribution_record(
                    source_id=f"source:commit:{introduction.commit_sha}",
                    source_type="commit",
                    locator_type="commit_sha",
                    locator_value=introduction.commit_sha,
                    source_claim_relationship="documents",
                    source_support_level="direct",
                    source_verification_state="verified",
                    source_staleness_state="current",
                    source_limitations=[
                        "Commit SHA observed via `git log --diff-filter=A` "
                        "for this task contract's own exact file path "
                        "(deliberately without --follow, which would "
                        "falsely merge unrelated files via content-"
                        "similarity rename detection -- see git_source.py); "
                        "commit contents beyond this path were not "
                        "enumerated."
                    ],
                )
            )
        all_attribution.extend(source_attribution)

        vstate_value = "known" if introduction.commit_sha else "unverified"
        vstate = verification_state(
            state_value=vstate_value,
            state_reason=(
                "Introducing commit resolved via git log --diff-filter=A "
                "against this task contract's exact file path."
                if introduction.commit_sha
                else "No introducing commit could be resolved for this task "
                "contract file; existence is declared by the file itself."
            ),
            commit_sha=introduction.commit_sha or commit_sha,
            state_limitations=[_NO_TASK_HISTORY_LIMITATION],
        )
        record_limitations = [
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=_NO_TASK_HISTORY_LIMITATION,
            )
        ]

        event_time = {
            "time_reference_type": "commit" if introduction.commit_sha else "unknown",
            "time_reference_value": introduction.commit_sha,
        }
        if introduction.commit_author_date_utc:
            event_time["time_reference_source"] = source_attr

        event_id = _event_id(event_type, introduction.commit_sha, task_id)
        events.append(
            {
                "event_id": event_id,
                "event_type": event_type,
                "event_subject": contract.title or task_id,
                "event_time": event_time,
                "event_phase_id": task_id,
                "event_summary": (
                    f"Task contract {task_id!r} declared status "
                    f"{contract.status!r} for {contract.title or 'an untitled task'}."
                ),
                "event_status": "known" if introduction.commit_sha else "unverified",
                "source_attribution": source_attribution,
                "verification_state": vstate,
                "limitations": record_limitations,
            }
        )

        phase_lineage.append(
            {
                "phase_id": task_id,
                "phase_name": contract.title or task_id,
                "phase_status_context": contract.status or "unknown",
                "predecessor_phase_ids": [],
                "successor_phase_ids": [],
                "commit_references": (
                    [{"locator_type": "commit_sha", "locator_value": introduction.commit_sha}]
                    if introduction.commit_sha
                    else []
                ),
                "source_attribution": source_attribution,
                "verification_state": vstate,
                "limitations": record_limitations + [
                    limitation_record(
                        limitation_type="scope_limitation",
                        limitation_description=_NO_PHASE_LINEAGE_TRAVERSAL_LIMITATION,
                    )
                ],
            }
        )

        claims.append(
            {
                "claim_id": _claim_id(task_id),
                # 128F repair: the frozen 119Q `claim_type` enum has never
                # included "phase_summary" (a pre-existing, 127E-introduced
                # schema-conformance defect, independently discovered by
                # 128F's own recursive schema validation -- no prior phase's
                # test coverage checked this specific field/enum
                # combination). "evolution" is the closest frozen enum value
                # for a claim describing a phase reaching a completion
                # status, matching 127A/127B's own "Historical Memory
                # records repository evolution" framing.
                "claim_type": "evolution",
                "claim_subject": task_id,
                "claim_statement": (
                    f"Phase {task_id!r} was completed with status "
                    f"{contract.status!r}, per task contract "
                    f"{contract.relative_path!r}."
                ),
                "historical_period": {
                    "period_id": f"period:{_node_id_safe(task_id)}",
                    "period_description": f"Task contract lifetime for {task_id}",
                    "period_start": contract.created_timestamp,
                    "period_end": introduction.commit_author_date_utc,
                },
                "source_attribution": source_attribution,
                "verification_state": vstate,
                "limitations": record_limitations,
            }
        )

        if event_type in ("repair_completed", "hardening_completed"):
            record_type = "hardening" if event_type == "hardening_completed" else "repair"
            repair_hardening.append(
                {
                    "record_id": _record_id(record_type, task_id),
                    "record_type": record_type,
                    "record_subject": contract.title or task_id,
                    "issue_or_boundary_addressed": (contract.goal or "Not declared.")[:2000],
                    "correction_or_hardening_summary": (contract.goal or "Not declared.")[:2000],
                    # 128F repair: the frozen 119Q schema's `phase_reference`
                    # field is a `source_locator` object (locator_type/
                    # locator_value), not a plain string -- a pre-existing,
                    # 127E-introduced schema-conformance defect independently
                    # discovered by 128F's own recursive schema validation.
                    "phase_reference": source_locator("task_id", task_id),
                    "source_attribution": source_attribution,
                    "verification_state": vstate,
                    "limitations": record_limitations,
                }
            )

    return events, phase_lineage, claims, repair_hardening, all_attribution


def _build_sequential_relationships(
    phase_lineage: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """One deterministic 'related_to' relationship per chronologically
    adjacent phase pair (127D Section 5.5) -- a pure function of the
    already-established ordering, never a guess about content.
    """
    relationships: list[dict[str, Any]] = []
    all_attribution: list[dict[str, Any]] = []
    for earlier, later in zip(phase_lineage, phase_lineage[1:]):
        source_ref = _historical_reference(f"ref:phase:{_node_id_safe(later['phase_id'])}", "phase")
        target_ref = _historical_reference(f"ref:phase:{_node_id_safe(earlier['phase_id'])}", "phase")
        rel_id = _relationship_id("related_to", source_ref["reference_id"], target_ref["reference_id"])
        source_attribution = list(later["source_attribution"])
        relationships.append(
            {
                "relationship_id": rel_id,
                "relationship_type": "related_to",
                "source_reference": source_ref,
                "target_reference": target_ref,
                "direction": "source_to_target",
                "source_attribution": source_attribution,
                "verification_state": later["verification_state"],
                "limitations": [
                    limitation_record(
                        limitation_type="scope_limitation",
                        limitation_description=(
                            "This 'related_to' relationship represents declared "
                            "chronological adjacency in the constructed timeline "
                            "only, not a verified causal or structural "
                            "dependency between the two phases."
                        ),
                    )
                ],
            }
        )
        all_attribution.extend(source_attribution)
    return relationships, all_attribution


_PHASE_REF_IN_TEXT_RE = re.compile(r"\b(\d{2,3}[A-Za-z](?:\.\d+)?)\b")


def _build_repair_relationships(
    repair_hardening: list[dict[str, Any]], phase_code_index: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Link each repair/hardening record to the single, unambiguous phase
    code it names in its own goal text (127D Section 5.5) -- omitted,
    never guessed, where zero or multiple candidates are found.
    """
    relationships: list[dict[str, Any]] = []
    all_attribution: list[dict[str, Any]] = []
    for record in repair_hardening:
        goal_text = record["issue_or_boundary_addressed"]
        candidates = {
            m for m in _PHASE_REF_IN_TEXT_RE.findall(goal_text) if m in phase_code_index
        }
        # Exclude self-reference (a repair record referencing its own phase).
        # 128F repair: phase_reference is now a source_locator object
        # (see the append site above); read locator_value, not the record
        # itself, to preserve the pre-existing string-comparison behavior.
        own_task_id = record["phase_reference"]["locator_value"]
        candidates = {c for c in candidates if phase_code_index[c] != own_task_id}
        if len(candidates) != 1:
            continue
        target_phase_code = next(iter(candidates))
        target_task_id = phase_code_index[target_phase_code]
        relationship_type = "hardened_by" if record["record_type"] == "hardening" else "repaired_by"
        source_ref = _historical_reference(
            f"ref:phase:{_node_id_safe(target_task_id)}", "phase"
        )
        target_ref = _historical_reference(record["record_id"], "repair_or_hardening")
        rel_id = _relationship_id(relationship_type, source_ref["reference_id"], target_ref["reference_id"])
        source_attribution = list(record["source_attribution"])
        relationships.append(
            {
                "relationship_id": rel_id,
                "relationship_type": relationship_type,
                "source_reference": source_ref,
                "target_reference": target_ref,
                "direction": "source_to_target",
                "source_attribution": source_attribution,
                "verification_state": record["verification_state"],
                "limitations": [
                    limitation_record(
                        limitation_type="scope_limitation",
                        limitation_description=(
                            "This relationship was derived from an exact, "
                            "unambiguous phase-code token match in the repair/"
                            "hardening record's own declared goal text -- not "
                            "independently verified against the target "
                            "phase's own content."
                        ),
                    )
                ],
            }
        )
        all_attribution.extend(source_attribution)
    return relationships, all_attribution


def _build_release_records(
    tags: tuple[GitTag, ...], commit_sha: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    releases: list[dict[str, Any]] = []
    all_attribution: list[dict[str, Any]] = []
    for tag in tags:
        source_attr = source_attribution_record(
            source_id=f"source:tag:{tag.tag_name}",
            source_type="commit",
            locator_type="tag",
            locator_value=tag.tag_name,
            source_claim_relationship="documents",
            source_support_level="direct",
            source_verification_state="verified",
            source_staleness_state="current",
            source_limitations=[
                "Tag name and target commit observed via `git tag`/`git log`; "
                "release notes or artifact contents were not parsed."
            ],
        )
        vstate = verification_state(
            state_value="known",
            state_reason="Tag and target commit observed via git plumbing.",
            commit_sha=tag.commit_sha,
            state_limitations=[
                "Release version is the raw git tag name; no separate "
                "version-metadata source was consulted."
            ],
        )
        releases.append(
            {
                "release_id": tag.tag_name,
                "version": tag.tag_name,
                "tag": tag.tag_name,
                "release_date": tag.commit_author_date_utc,
                "release_status_context": "tagged",
                "source_attribution": [source_attr],
                "verification_state": vstate,
                "limitations": [
                    limitation_record(
                        limitation_type="scope_limitation",
                        limitation_description=(
                            "Release record derived from git tag existence "
                            "only; no release-artifact or changelog content "
                            "was parsed."
                        ),
                    )
                ],
            }
        )
        all_attribution.append(source_attr)
    return releases, all_attribution


def _merge_unique_attribution(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        source_id = item.get("source_id")
        if source_id is None:
            continue
        unique[source_id] = item
    return [unique[key] for key in sorted(unique)]


def build_historical_content(
    repo_root: Path, snapshot_path: Path, *, generated_at_utc: str
) -> dict[str, Any]:
    """Build a schema-conformant Historical Memory Snapshot.

    Deterministic given a fixed repository state (git history +
    tasks/done/ content + source snapshot), except
    ``generated_at_utc``/``snapshot_created_at_utc`` (approved
    non-substantive metadata, mirroring 120B Section 6's rule).

    Consumes the source snapshot exclusively through the Track 121
    Query Layer; consumes git history and task contracts exclusively
    through ``git_source.py``. Never reads
    ``.pcae/phase-reports/``. Never reruns Track 120's generator.

    Raises ``HistoricalGenerationError`` (fail-closed, 127B Section 9 /
    127D Section 9) if required sources are invalid, unsupported, or
    missing required provenance/limitation/boundary material.
    """
    raw_snapshot = _load_and_validate_snapshot(snapshot_path)
    limitations_result, boundary_result = _query_snapshot_material(snapshot_path)

    envelope = raw_snapshot.get("envelope") or {}
    repository_context = envelope.get("repository_context") or {}
    snapshot_source_commit = repository_context.get("repository_commit")
    if not snapshot_source_commit:
        raise HistoricalGenerationError(
            "source Repository Knowledge Snapshot envelope is missing "
            "repository_context.repository_commit; refusing to produce "
            "Historical Memory without a stable commit anchor."
        )
    repository_identity = repository_context.get("repository_identity") or {}
    repository_name = repository_identity.get("identity_value") or "unknown-repository"
    source_executable_schema_version = (raw_snapshot.get("snapshot_identity") or {}).get(
        "executable_schema_version"
    )
    if source_executable_schema_version is None:
        raise HistoricalGenerationError(
            "source Repository Knowledge Snapshot is missing its own "
            "executable_schema_version; refusing to derive Historical "
            "Memory from an unversioned source artifact."
        )

    try:
        head_commit_sha = git_head_commit_sha(repo_root)
    except HistoricalSourceError as exc:
        raise HistoricalGenerationError(str(exc)) from exc

    task_files = list_task_contract_files(repo_root)
    if not task_files:
        raise HistoricalGenerationError(
            "no tasks/done/*.md task contract files were found; refusing "
            "to produce Historical Memory with no historical source "
            "material."
        )

    events, phase_lineage, claims, repair_hardening, phase_attribution = (
        _build_phase_records(repo_root, task_files, head_commit_sha)
    )
    if not events or not phase_lineage:
        raise HistoricalGenerationError(
            "no historical events or phase lineage records could be "
            "constructed from tasks/done/*.md; refusing to produce a "
            "non-conformant artifact with empty required arrays."
        )

    phase_code_index = {
        phase_code_from_title(rec["phase_name"]): rec["phase_id"]
        for rec in phase_lineage
        if phase_code_from_title(rec["phase_name"])
    }
    sequential_rel, sequential_attr = _build_sequential_relationships(phase_lineage)
    repair_rel, repair_rel_attr = _build_repair_relationships(repair_hardening, phase_code_index)
    relationships = sequential_rel + repair_rel

    tags = list_git_tags(repo_root)
    releases, release_attribution = _build_release_records(tags, head_commit_sha)

    dependency_sources = _merge_unique_attribution(
        phase_attribution
        + sequential_attr
        + repair_rel_attr
        + release_attribution
        + list(limitations_result.attribution)
    )
    if not dependency_sources:
        raise HistoricalGenerationError(
            "no source attribution could be assembled for this Historical "
            "Memory Snapshot; refusing to produce a non-conformant "
            "artifact."
        )

    snapshot_limitations = _merge_unique_limitations(
        list(limitations_result.limitations)
        + [
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=_NO_TASK_HISTORY_LIMITATION,
            ),
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=_NO_SUBPHASE_GOVERNANCE_EVENTS_LIMITATION,
            ),
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=_NO_DECISION_RECORDS_LIMITATION,
            ),
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=_NO_PHASE_LINEAGE_TRAVERSAL_LIMITATION,
            ),
        ]
    )

    unknowns_gaps = [
        {
            "unknown_id": "unknown:governance-subphase-events",
            "unknown_subject": "sub-phase governance actions",
            "missing_evidence": "governance_check_completed/report_generated/metadata_promoted/notification_sent events",
            "affected_period": _graph_wide_period(),
            "uncertainty_state": verification_state(
                state_value="unknown",
                state_reason=_NO_SUBPHASE_GOVERNANCE_EVENTS_LIMITATION,
                commit_sha=head_commit_sha,
                state_limitations=[_NO_SUBPHASE_GOVERNANCE_EVENTS_LIMITATION],
            ),
            "limitation": limitation_record(
                limitation_type="scope_limitation",
                limitation_description=_NO_SUBPHASE_GOVERNANCE_EVENTS_LIMITATION,
            ),
        },
        {
            "unknown_id": "unknown:decision-history",
            "unknown_subject": "recorded engineering decisions",
            "missing_evidence": "decision_history_record entries",
            "affected_period": _graph_wide_period(),
            "uncertainty_state": verification_state(
                state_value="unknown",
                state_reason=_NO_DECISION_RECORDS_LIMITATION,
                commit_sha=head_commit_sha,
                state_limitations=[_NO_DECISION_RECORDS_LIMITATION],
            ),
            "limitation": limitation_record(
                limitation_type="scope_limitation",
                limitation_description=_NO_DECISION_RECORDS_LIMITATION,
            ),
        },
    ]

    boundary_disclosures = dict(boundary_result.boundary_disclosures) or dict(BOUNDARY_DISCLOSURES)
    disclaimers = dict(boundary_result.disclaimers) or dict(DISCLAIMERS)

    snapshot_id = f"hms-{head_commit_sha}"
    snapshot_subject = f"Historical Memory Snapshot for {repository_name}"
    snapshot_scope = (
        f"Declared repository evolution derived from git commit history "
        f"and {len(task_files)} tasks/done/*.md task contract files, "
        f"cross-referenced against Repository Knowledge Snapshot "
        f"{(raw_snapshot.get('snapshot_identity') or {}).get('snapshot_id', 'unknown-snapshot')!r}. "
        "v1 covers phase-lineage events and declared chronological "
        "adjacency relationships only; sub-phase governance events and "
        "decision history are not yet available (see unknowns_gaps)."
    )

    period_starts = [
        rec.get("period_start") for rec in [c["historical_period"] for c in claims] if rec.get("period_start")
    ]
    period_ends = [
        rec.get("period_end") for rec in [c["historical_period"] for c in claims] if rec.get("period_end")
    ]

    historical_window = {
        "period_id": f"window:{snapshot_id}",
        "period_description": f"Full declared historical window covered by {snapshot_id}",
        "period_start": min(period_starts) if period_starts else None,
        "period_end": max(period_ends) if period_ends else None,
    }

    envelope_source_attribution = list(dependency_sources)
    historical_envelope = {
        "artifact_id": f"historical_memory_snapshot:{head_commit_sha}",
        "artifact_type": "historical_memory_snapshot",
        "artifact_family": "historical_memory_snapshot",
        "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
        "schema_concept_version": SCHEMA_CONCEPT_VERSION,
        "executable_schema_version": ENVELOPE_EXECUTABLE_SCHEMA_VERSION,
        "repository_context": dict(repository_context),
        "generated_at_utc": generated_at_utc,
        "producer": {
            "producer_type": "tool",
            "producer_identity": (
                "pcae repository-intelligence historical-memory generate "
                "(Phase 127E read-only prototype)"
            ),
        },
        "source_attribution": envelope_source_attribution,
        "evidence_links": [
            {
                "evidence_id": "evidence-gap:envelope",
                "evidence_type": "evidence_gap_marker",
                "evidence_source": {
                    "source_type": "none",
                    "source_identity": "not_applicable",
                },
                "supported_claim": {
                    "claim_id": "envelope",
                    "claim_summary": (
                        "No Evidence subsystem link is established by "
                        "this prototype."
                    ),
                },
                "support_strength": "inconclusive",
                "candidate_or_accepted_state": "unsubmitted",
                "decision_evaluation_eligibility": "not_eligible_evidence_gap",
                "limitations": [
                    "This prototype does not integrate with the "
                    "Evidence subsystem."
                ],
            }
        ],
        "verification_state": "partially_verified",
        "uncertainty_state": "partially_verified",
        "conflict_state": "none",
        "supersession_state": "current",
        "read_only_boundary": READ_ONLY_BOUNDARY,
        "decision_boundary": DECISION_BOUNDARY,
        "execution_boundary": EXECUTION_BOUNDARY,
        "boundary_disclosures": dict(boundary_disclosures),
        "limitations": [
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=(
                    "This is a narrow, first-prototype Historical Memory "
                    "Snapshot; see snapshot_limitations for the full "
                    "disclosure."
                ),
            )
        ],
        "disclaimers": dict(disclaimers),
    }

    historical: dict[str, Any] = {
        "envelope": historical_envelope,
        "snapshot_identity": {
            "snapshot_id": snapshot_id,
            "snapshot_subject": snapshot_subject,
            "snapshot_scope": snapshot_scope,
            "historical_window": historical_window,
            "snapshot_created_at_utc": generated_at_utc,
            "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
            "schema_concept_version": SCHEMA_CONCEPT_VERSION,
            "executable_schema_version": HISTORICAL_EXECUTABLE_SCHEMA_VERSION,
        },
        "snapshot_subject": snapshot_subject,
        "snapshot_scope": snapshot_scope,
        "historical_window": historical_window,
        # 128E (128C Finding 1 / 128D Section 2.1): the collections below
        # are sorted by each record's own identifier field, not by any
        # declared time reference. Chronological ordering is already
        # performed earlier, during construction (see `_sort_key` above,
        # which governs the order task-derived records are *built* in).
        # This final, separate sort is intentionally identifier-based --
        # it exists to guarantee deterministic, stable, diffable
        # serialization (matching what `historical_validation.py`'s
        # `_validate_deterministic_ordering` actually checks), not to
        # express historical/chronological ordering. Do not read this as
        # chronological ordering.
        "historical_events": sorted(events, key=lambda e: e["event_id"]),
        "historical_claims": sorted(claims, key=lambda c: c["claim_id"]),
        "historical_sources": dependency_sources,
        "evidence_links": [],
        "phase_lineage": sorted(phase_lineage, key=lambda p: p["phase_id"]),
        "release_lineage": sorted(releases, key=lambda r: r["release_id"]),
        "decision_history": [],
        "repair_hardening_history": sorted(repair_hardening, key=lambda r: r["record_id"]),
        "supersession_correction_history": [],
        "historical_relationships": sorted(relationships, key=lambda r: r["relationship_id"]),
        "unknowns_gaps": unknowns_gaps,
        "snapshot_limitations": snapshot_limitations,
        "conflict_or_supersession_records": [],
        "derivation_records": [],
        "boundary_disclosures": dict(boundary_disclosures),
        "disclaimers": dict(disclaimers),
        "historical_memory_snapshot_disclaimer": HISTORICAL_MEMORY_SNAPSHOT_DISCLAIMER,
    }

    return historical


def _merge_unique_limitations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in items:
        key = (item.get("limitation_type"), item.get("limitation_description"))
        unique[key] = item
    return [unique[key] for key in sorted(unique, key=lambda k: (k[0] or "", k[1] or ""))]
