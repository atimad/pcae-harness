"""Repository Knowledge Snapshot assembly (120D pipeline stages 4-9).

Extraction, normalization, assembly, schema alignment, limitation/
unknown capture, and boundary attachment all live here, matching the
component plan frozen in 120D Section 6. No stage performs inference:
every field is either directly, deterministically observed or is
explicitly represented as an unknown/limitation.
"""

from __future__ import annotations

from pathlib import Path

from pcae.repository_intelligence.attribution import (
    commit_attribution,
    file_path_attribution,
    limitation_record,
    source_locator,
    verification_state,
)
from pcae.repository_intelligence.source_inventory import (
    SourceInventoryError,
    git_branch,
    git_commit_sha,
    list_top_level_entries,
    read_project_status_current_phase,
    read_pyproject_project_fields,
)

ARTIFACT_CONTRACT_VERSION = "119E.1.0"
SCHEMA_CONCEPT_VERSION = "119C.1.0-concept"
ENVELOPE_EXECUTABLE_SCHEMA_VERSION = "119K.1.0-json-schema"
SNAPSHOT_EXECUTABLE_SCHEMA_VERSION = "119O.1.0-json-schema"

REPOSITORY_KNOWLEDGE_SNAPSHOT_DISCLAIMER = (
    "This Repository Knowledge Snapshot describes repository "
    "architecture and entity relationships. It is not Repository "
    "State and does not decide whether the repository is valid, "
    "correct, or complete."
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

# Deterministic, non-inferential entity_type classification for the
# fixed set of top-level source locations this narrow prototype
# observes. "module" for directories, "source_file" for .py files,
# per schema entity_type enum.
_SRC_PCAE_TOP_LEVEL_DIRS = ("commands", "core")


class SnapshotGenerationError(RuntimeError):
    """Raised when the generator must fail closed rather than emit output."""


def _entity_type_for(entry_relative_path: str, is_dir: bool) -> str:
    if is_dir:
        return "module"
    if entry_relative_path.endswith(".py"):
        return "source_file"
    return "unknown"


def _build_architectural_entities(repo_root: Path, commit_sha: str) -> list[dict]:
    entities: list[dict] = []

    src_pcae_entries = list_top_level_entries(repo_root, "src/pcae")
    for entry in src_pcae_entries:
        entity_type = _entity_type_for(entry.relative_path, entry.is_dir)
        entity_id = f"entity:{entry.relative_path}"
        entities.append(
            {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "entity_name": entry.name,
                "entity_path": entry.relative_path,
                "entity_locator": source_locator("file_path", entry.relative_path),
                "entity_role": "top_level_package_member",
                "source_attribution": [
                    file_path_attribution(
                        source_id=f"source:{entry.relative_path}",
                        path=entry.relative_path,
                        commit_sha=commit_sha,
                    )
                ],
                "verification_state": verification_state(
                    state_value="verified",
                    state_reason=(
                        "Path existence observed via deterministic "
                        "filesystem listing at generation commit."
                    ),
                    commit_sha=commit_sha,
                    state_limitations=[
                        "Verification is limited to path existence; "
                        "semantic purpose or correctness was not verified."
                    ],
                ),
                "limitations": [
                    limitation_record(
                        limitation_type="scope_limitation",
                        limitation_description=(
                            "This prototype records top-level path "
                            "existence only; it does not parse file "
                            "contents, imports, or symbols."
                        ),
                    )
                ],
            }
        )

    for fixed_dir, entity_type in (
        ("tests", "test"),
        ("schemas/repository_intelligence", "schema"),
    ):
        if not (repo_root / fixed_dir).is_dir():
            continue
        entity_id = f"entity:{fixed_dir}"
        entities.append(
            {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "entity_name": fixed_dir.rsplit("/", maxsplit=1)[-1],
                "entity_path": fixed_dir,
                "entity_locator": source_locator("file_path", fixed_dir),
                "entity_role": "top_level_repository_directory",
                "source_attribution": [
                    file_path_attribution(
                        source_id=f"source:{fixed_dir}",
                        path=fixed_dir,
                        commit_sha=commit_sha,
                    )
                ],
                "verification_state": verification_state(
                    state_value="verified",
                    state_reason=(
                        "Directory existence observed via deterministic "
                        "filesystem listing at generation commit."
                    ),
                    commit_sha=commit_sha,
                    state_limitations=[
                        "Verification is limited to directory existence; "
                        "contents were not recursively enumerated."
                    ],
                ),
                "limitations": [
                    limitation_record(
                        limitation_type="scope_limitation",
                        limitation_description=(
                            "This prototype records directory existence "
                            "only; it does not recursively enumerate or "
                            "parse directory contents."
                        ),
                    )
                ],
            }
        )

    return entities


def _build_subsystems(repo_root: Path, commit_sha: str) -> list[dict]:
    subsystem_defs = (
        ("schemas/repository_intelligence", "schema"),
        ("docs", "documentation"),
    )
    subsystems: list[dict] = []
    for path, subsystem_type in subsystem_defs:
        if not (repo_root / path).is_dir():
            continue
        subsystems.append(
            {
                "subsystem_id": f"subsystem:{path}",
                "subsystem_name": path,
                "subsystem_type": subsystem_type,
                "subsystem_boundary": f"Files under `{path}/`.",
                "source_attribution": [
                    file_path_attribution(
                        source_id=f"source:subsystem:{path}",
                        path=path,
                        commit_sha=commit_sha,
                    )
                ],
                "verification_state": verification_state(
                    state_value="verified",
                    state_reason=(
                        "Directory existence observed via deterministic "
                        "filesystem listing at generation commit."
                    ),
                    commit_sha=commit_sha,
                    state_limitations=[
                        "Subsystem boundary is declared as a top-level "
                        "directory path only; internal structure was not "
                        "analyzed."
                    ],
                ),
                "limitations": [
                    limitation_record(
                        limitation_type="scope_limitation",
                        limitation_description=(
                            "Subsystem classification reflects only the "
                            "directory's declared top-level purpose; it "
                            "is not a semantic analysis of subsystem "
                            "behavior."
                        ),
                    )
                ],
            }
        )
    return subsystems


def _build_knowledge_claims(repo_root: Path, commit_sha: str) -> list[dict]:
    claims: list[dict] = []

    claims.append(
        {
            "claim_id": "claim:generation-commit",
            "claim_type": "documentation",
            "claim_subject": "repository.commit",
            "claim_text": (
                f"This Repository Knowledge Snapshot was generated for "
                f"the repository at commit {commit_sha}."
            ),
            "claim_status": "verified",
            "source_attribution": [
                commit_attribution(source_id="source:generation-commit", commit_sha=commit_sha)
            ],
            "verification_state": verification_state(
                state_value="verified",
                state_reason="Commit SHA observed via `git rev-parse HEAD`.",
                commit_sha=commit_sha,
                state_limitations=["Limited to the commit identifier itself."],
            ),
            "uncertainty_state": verification_state(
                state_value="known",
                state_reason="Commit SHA is directly observable, not inferred.",
                commit_sha=commit_sha,
                state_limitations=["Limited to the commit identifier itself."],
            ),
            "limitations": [
                limitation_record(
                    limitation_type="scope_limitation",
                    limitation_description="Identifies the snapshotted commit only.",
                )
            ],
        }
    )

    project_fields = read_pyproject_project_fields(repo_root)
    for field_name in ("name", "version", "description"):
        value = project_fields.get(field_name)
        if not value:
            continue
        claims.append(
            {
                "claim_id": f"claim:pyproject.project.{field_name}",
                "claim_type": "documentation",
                "claim_subject": f"pyproject.toml [project].{field_name}",
                "claim_text": (
                    f"pyproject.toml declares [project].{field_name} = "
                    f'"{value}".'
                ),
                "claim_status": "verified",
                "source_attribution": [
                    file_path_attribution(
                        source_id=f"source:pyproject.{field_name}",
                        path="pyproject.toml",
                        commit_sha=commit_sha,
                        relationship="documents",
                    )
                ],
                "verification_state": verification_state(
                    state_value="verified",
                    state_reason=(
                        "Field value read directly from pyproject.toml "
                        "[project] table via deterministic text parsing."
                    ),
                    commit_sha=commit_sha,
                    state_limitations=[
                        "Parsing is limited to a narrow regex over the "
                        "[project] table; complex TOML value types are "
                        "not supported."
                    ],
                ),
                "uncertainty_state": verification_state(
                    state_value="known",
                    state_reason="Value is directly observable, not inferred.",
                    commit_sha=commit_sha,
                    state_limitations=["Limited to the declared field value."],
                ),
                "limitations": [
                    limitation_record(
                        limitation_type="scope_limitation",
                        limitation_description=(
                            "Reflects the declared pyproject.toml field "
                            "value only; does not verify runtime behavior."
                        ),
                    )
                ],
            }
        )

    current_phase_line = read_project_status_current_phase(repo_root)
    if current_phase_line:
        claims.append(
            {
                "claim_id": "claim:project-status.current-phase",
                "claim_type": "documentation",
                "claim_subject": "PROJECT_STATUS.md ## Current Phase",
                "claim_text": (
                    "PROJECT_STATUS.md's '## Current Phase' section "
                    f"begins: {current_phase_line}"
                ),
                "claim_status": "verified",
                "source_attribution": [
                    file_path_attribution(
                        source_id="source:project-status.current-phase",
                        path="PROJECT_STATUS.md",
                        commit_sha=commit_sha,
                        relationship="documents",
                    )
                ],
                "verification_state": verification_state(
                    state_value="verified",
                    state_reason=(
                        "Line read directly from PROJECT_STATUS.md's "
                        "'## Current Phase' section via deterministic "
                        "text parsing."
                    ),
                    commit_sha=commit_sha,
                    state_limitations=[
                        "Reflects only the first non-empty line of the "
                        "section; the section may continue with "
                        "additional detail not captured here."
                    ],
                ),
                "uncertainty_state": verification_state(
                    state_value="partially_verified",
                    state_reason=(
                        "The line was observed directly, but its "
                        "continued accuracy depends on PROJECT_STATUS.md "
                        "staying in sync with governed phase state, "
                        "which this prototype does not independently "
                        "verify."
                    ),
                    commit_sha=commit_sha,
                    state_limitations=[
                        "Does not cross-check against .pcae/ canonical "
                        "phase-completion metadata."
                    ],
                ),
                "limitations": [
                    limitation_record(
                        limitation_type="scope_limitation",
                        limitation_description=(
                            "Reflects PROJECT_STATUS.md's declared "
                            "current phase text only; does not "
                            "independently verify phase completion state."
                        ),
                    )
                ],
            }
        )

    return claims


def _collect_knowledge_sources(entities: list[dict], subsystems: list[dict], claims: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for collection in (entities, subsystems, claims):
        for record in collection:
            for source in record.get("source_attribution", []):
                seen.setdefault(source["source_id"], source)
    return [seen[key] for key in sorted(seen)]


def build_snapshot_content(repo_root: Path, *, generated_at_utc: str) -> dict:
    """Assemble a schema-conformant Repository Knowledge Snapshot.

    Deterministic given a fixed commit, except ``generated_at_utc`` and
    ``snapshot_created_at_utc``, which are the only approved
    non-substantive metadata fields per 120B Section 6.

    Raises ``SnapshotGenerationError`` (fail-closed, 120B Section 15 /
    120D Section 12) if a required deterministic source cannot be
    observed.
    """
    try:
        commit_sha = git_commit_sha(repo_root)
    except SourceInventoryError as exc:
        raise SnapshotGenerationError(str(exc)) from exc

    branch = git_branch(repo_root)

    entities = _build_architectural_entities(repo_root, commit_sha)
    if not entities:
        raise SnapshotGenerationError(
            "No architectural entities could be observed at the "
            "expected top-level locations (src/pcae, tests, "
            "schemas/repository_intelligence); refusing to produce a "
            "non-conformant snapshot with an empty required "
            "architectural_entities array."
        )
    subsystems = _build_subsystems(repo_root, commit_sha)
    claims = _build_knowledge_claims(repo_root, commit_sha)
    knowledge_sources = _collect_knowledge_sources(entities, subsystems, claims)

    snapshot_id = f"rks-{commit_sha}"
    snapshot_subject = "pcae-harness repository architecture"
    snapshot_scope = (
        "Top-level members of src/pcae, the tests/ and "
        "schemas/repository_intelligence directories, and pyproject.toml "
        "[project] metadata, as observed at a fixed commit. Recursive "
        "file-content parsing, import analysis, and symbol extraction "
        "are not performed by this narrow first prototype."
    )

    unknowns = [
        "Capabilities were not extracted in this narrow prototype pass; "
        "the capabilities array is empty pending a future, separately "
        "scoped extraction phase.",
        "Relationships between architectural entities were not "
        "extracted in this narrow prototype pass; the "
        "knowledge_relationships array is empty.",
        "File contents, imports, and internal symbols were not parsed; "
        "entity records reflect top-level path existence only.",
        "The full repository directory tree was not recursively "
        "enumerated; only a fixed set of top-level locations was "
        "observed (src/pcae direct children, tests/, "
        "schemas/repository_intelligence, pyproject.toml, "
        "PROJECT_STATUS.md).",
    ]

    snapshot_limitations = [
        limitation_record(
            limitation_type="scope_limitation",
            limitation_description=(
                "This is the first, intentionally narrow Repository "
                "Knowledge Snapshot prototype (Phase 120E). It observes "
                "a fixed set of top-level repository locations without "
                "recursive parsing."
            ),
            affected_claims_or_fields=[
                "architectural_entities",
                "capabilities",
                "subsystems",
                "knowledge_relationships",
            ],
            severity_or_scope="snapshot-wide",
            mitigation_or_follow_up=(
                "Future phases may extend extraction depth and breadth "
                "under a new, separately scoped contract phase."
            ),
        )
    ]

    envelope_source_attribution = list(knowledge_sources) or [
        commit_attribution(source_id="source:envelope-commit", commit_sha=commit_sha)
    ]

    envelope = {
        "artifact_id": f"repository_knowledge_snapshot:{commit_sha}",
        "artifact_type": "repository_knowledge_snapshot",
        "artifact_family": "repository_knowledge_snapshot",
        "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
        "schema_concept_version": SCHEMA_CONCEPT_VERSION,
        "executable_schema_version": ENVELOPE_EXECUTABLE_SCHEMA_VERSION,
        "repository_context": {
            "repository_identity": {
                "identity_type": "repository_name",
                "identity_value": (
                    read_pyproject_project_fields(repo_root).get("name") or "pcae-harness"
                ),
            },
            "repository_path": None,
            "repository_commit": commit_sha,
            "repository_branch": branch,
            "repository_status_context": None,
            "release_context_ref": None,
        },
        "generated_at_utc": generated_at_utc,
        "producer": {
            "producer_type": "tool",
            "producer_identity": (
                "pcae repository-intelligence snapshot generate "
                "(Phase 120E read-only prototype)"
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
        "boundary_disclosures": dict(BOUNDARY_DISCLOSURES),
        "limitations": [
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=(
                    "This is a narrow, first-prototype Repository "
                    "Knowledge Snapshot; see snapshot_limitations for "
                    "the full disclosure."
                ),
            )
        ],
        "disclaimers": dict(DISCLAIMERS),
    }

    snapshot: dict = {
        "envelope": envelope,
        "snapshot_identity": {
            "snapshot_id": snapshot_id,
            "snapshot_subject": snapshot_subject,
            "snapshot_scope": snapshot_scope,
            "snapshot_created_at_utc": generated_at_utc,
            "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
            "schema_concept_version": SCHEMA_CONCEPT_VERSION,
            "executable_schema_version": SNAPSHOT_EXECUTABLE_SCHEMA_VERSION,
        },
        "snapshot_subject": snapshot_subject,
        "snapshot_scope": snapshot_scope,
        "architectural_entities": entities,
        "capabilities": [],
        "subsystems": subsystems,
        "knowledge_relationships": [],
        "knowledge_claims": claims,
        "knowledge_sources": knowledge_sources,
        "evidence_links": [],
        "unknowns": unknowns,
        "snapshot_limitations": snapshot_limitations,
        "boundary_disclosures": dict(BOUNDARY_DISCLOSURES),
        "disclaimers": dict(DISCLAIMERS),
        "repository_knowledge_snapshot_disclaimer": REPOSITORY_KNOWLEDGE_SNAPSHOT_DISCLAIMER,
    }

    return snapshot
