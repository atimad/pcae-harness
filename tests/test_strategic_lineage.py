from __future__ import annotations

import copy
import json
from pathlib import Path

from pcae.cli import main
from pcae.core.paths import HarnessPath
from pcae.core.strategic_lineage import (
    PRE_65J_MIGRATION_EXEMPT_PHASE_IDS,
    strategic_review_snapshot_hash,
    validate_strategic_lineage,
)


ACTIVATION_TIMESTAMP = "2026-06-11T11:00:00+00:00"
ACTIVATION_TIMESTAMP_66C = "2026-06-11T12:00:00+00:00"
ACTIVATION_TIMESTAMP_64H = "2026-06-11T17:00:00+00:00"
ACTIVATION_TIMESTAMP_66D = "2026-06-11T21:00:00+00:00"
ACTIVATION_TIMESTAMP_66E = "2026-06-12T05:34:03+00:00"
ACTIVATION_TIMESTAMP_67A = "2026-06-12T08:32:36+00:00"
ACTIVATION_TIMESTAMP_67B = "2026-06-12T12:17:00+00:00"
ACTIVATION_TIMESTAMP_68A = "2026-06-12T13:31:00+00:00"
ACTIVATION_TIMESTAMP_68B = "2026-06-12T16:10:49+00:00"
ACTIVATION_TIMESTAMP_68C = "2026-06-12T17:31:00+00:00"
ACTIVATION_TIMESTAMP_68D = "2026-06-12T17:31:22+00:00"
ACTIVATION_TIMESTAMP_69A = "2026-06-12T21:09:00+00:00"


def _valid_record() -> dict:
    return {
        "lineage_id": "SLR-65I-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "coherence_failure",
        "source_phase_id": "66B",
        "predecessor_phase_id": "65H",
        "activated_phase_id": "65I",
        "selected_branch_id": "BR-003",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Repair strategic registry coherence before roadmap expansion.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [
            {
                "phase_id": "66C",
                "branch_id": "BR-004",
                "disposition": "deferred",
                "reason": "Coherence must be repaired first.",
            },
            {
                "phase_id": "64H",
                "branch_id": "BR-001",
                "disposition": "rejected",
                "reason": "Lower immediate governance value.",
            },
        ],
        "rejected_alternatives": ["64H"],
        "deferred_alternatives": ["66C"],
        "roadmap_debt": ["Review findings remain advisory."],
        "supersedes_lineage_id": "",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP,
        "activation_validation_status": "validated",
    }


def _valid_66c_record() -> dict:
    # Historical approved lineage remains immutable even after BR-004 advances;
    # supersession is derived from later supersedes_lineage_id references.
    return {
        "lineage_id": "SLR-66C-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_66C,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "strategic_review",
        "source_phase_id": "66B",
        "predecessor_phase_id": "65J",
        "activated_phase_id": "66C",
        "selected_branch_id": "BR-004",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Calibrate strategic review rules and close BR-004.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [
            {
                "phase_id": "64H",
                "branch_id": "BR-001",
                "disposition": "deferred",
                "reason": "Deferred pending 66C completion.",
            },
            {
                "phase_id": "65H",
                "branch_id": "BR-003",
                "disposition": "rejected",
                "reason": "Already completed, not a viable alternative.",
            },
        ],
        "rejected_alternatives": ["65H"],
        "deferred_alternatives": ["64H"],
        "roadmap_debt": [],
        "supersedes_lineage_id": "",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_66C,
        "activation_validation_status": "validated",
    }


def _valid_64h_record() -> dict:
    return {
        "lineage_id": "SLR-64H-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_64H,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "strategic_review",
        "source_phase_id": "66C",
        "predecessor_phase_id": "66C",
        "activated_phase_id": "64H",
        "selected_branch_id": "BR-001",
        "objective_ids": ["OBJ-003", "OBJ-002"],
        "rationale": "Resume multi-runtime objective coverage hardening per SRS-RULE-004/005.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [
            {
                "phase_id": "64G",
                "branch_id": "BR-002",
                "disposition": "deferred",
                "reason": "Lower immediate governance priority.",
            },
            {
                "phase_id": "64F",
                "branch_id": "BR-001",
                "disposition": "rejected",
                "reason": "Already completed.",
            },
        ],
        "rejected_alternatives": ["64F"],
        "deferred_alternatives": ["64G"],
        "roadmap_debt": ["OCH proposals require human approval before map update."],
        "supersedes_lineage_id": "SLR-66C-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_64H,
        "activation_validation_status": "validated",
    }


def _valid_66d_record() -> dict:
    return {
        "lineage_id": "SLR-66D-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_66D,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "64H",
        "predecessor_phase_id": "66C",
        "activated_phase_id": "66D",
        "selected_branch_id": "BR-004",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Surface latest IRG review state in session bootstrap; minimum viable scope.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [
            {
                "phase_id": "64G",
                "branch_id": "BR-002",
                "disposition": "deferred",
                "reason": "Lower immediate governance priority.",
            },
            {
                "phase_id": "64F",
                "branch_id": "BR-001",
                "disposition": "rejected",
                "reason": "Already completed.",
            },
        ],
        "rejected_alternatives": ["64F"],
        "deferred_alternatives": ["64G"],
        "roadmap_debt": ["Multi-trigger IRG surfacing deferred to a future phase decision."],
        "supersedes_lineage_id": "SLR-64H-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_66D,
        "activation_validation_status": "validated",
    }


def _valid_66e_record() -> dict:
    return {
        "lineage_id": "SLR-66E-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_66E,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "architecture_requirement",
        "source_phase_id": "66D",
        "predecessor_phase_id": "66D",
        "activated_phase_id": "66E",
        "selected_branch_id": "BR-004",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Auto-surface advisory-only challenge context at summary-oriented lifecycle boundaries.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [
            {
                "phase_id": "64G",
                "branch_id": "BR-002",
                "disposition": "deferred",
                "reason": "Lower immediate governance priority.",
            },
            {
                "phase_id": "64F",
                "branch_id": "BR-001",
                "disposition": "rejected",
                "reason": "Already completed.",
            },
        ],
        "rejected_alternatives": ["64F"],
        "deferred_alternatives": ["64G"],
        "roadmap_debt": ["No challenge persistence or workflow authority is introduced."],
        "supersedes_lineage_id": "SLR-66D-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_66E,
        "activation_validation_status": "validated",
    }


def _valid_67a_record() -> dict:
    return {
        "lineage_id": "SLR-67A-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_67A,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "architecture_requirement",
        "source_phase_id": "66E",
        "predecessor_phase_id": "66E",
        "activated_phase_id": "67A",
        "selected_branch_id": "BR-004",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Upgrade IRGC with comparative assessment, confidence model, and contradiction synthesis.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [
            {
                "phase_id": "64G",
                "branch_id": "BR-002",
                "disposition": "deferred",
                "reason": "Lower immediate governance priority.",
            },
            {
                "phase_id": "64F",
                "branch_id": "BR-001",
                "disposition": "rejected",
                "reason": "Already completed.",
            },
        ],
        "rejected_alternatives": ["64F"],
        "deferred_alternatives": ["64G"],
        "roadmap_debt": ["No challenge persistence or workflow authority is introduced."],
        "supersedes_lineage_id": "SLR-66E-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_67A,
        "activation_validation_status": "validated",
    }


def _valid_67b_record() -> dict:
    return {
        "lineage_id": "SLR-67B-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_67B,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "architecture_requirement",
        "source_phase_id": "67A",
        "predecessor_phase_id": "67A",
        "activated_phase_id": "67B",
        "selected_branch_id": "BR-004",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Add correlation observation layer to IRGC; humans see correlation not influence.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": ["Calibration effects computed but not applied in 67B."],
        "supersedes_lineage_id": "SLR-67A-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_67B,
        "activation_validation_status": "validated",
    }


def _valid_68a_record() -> dict:
    return {
        "lineage_id": "SLR-68A-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_68A,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "architecture_requirement",
        "source_phase_id": "67B",
        "predecessor_phase_id": "67B",
        "activated_phase_id": "68A",
        "selected_branch_id": "BR-004",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Add deterministic attention allocation layer to IRGC; visibility_is_importance=False.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": ["AttentionDecisions computed but not yet applied to compact output."],
        "supersedes_lineage_id": "SLR-67B-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_68A,
        "activation_validation_status": "validated",
    }


def _valid_68b_record() -> dict:
    return {
        "lineage_id": "SLR-68B-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_68B,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "architecture_requirement",
        "source_phase_id": "68A",
        "predecessor_phase_id": "68A",
        "activated_phase_id": "68B",
        "selected_branch_id": "BR-004",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Wire 68A allocator into compact rendering; allocator_changes_visibility_only=True.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-68A-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_68B,
        "activation_validation_status": "validated",
    }


def _valid_68c_record() -> dict:
    return {
        "lineage_id": "SLR-68C-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_68C,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "architecture_requirement",
        "source_phase_id": "68B",
        "predecessor_phase_id": "68B",
        "activated_phase_id": "68C",
        "selected_branch_id": "BR-004",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Effectiveness review: validates 68A/68B allocator; identifies persistent_background demotion gap.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": ["Completion surface allocation bypass documented as intentional; persistent demotion gap deferred to 68D."],
        "supersedes_lineage_id": "SLR-68B-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_68C,
        "activation_validation_status": "validated",
    }


def _valid_68d_record() -> dict:
    return {
        "lineage_id": "SLR-68D-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_68D,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "architecture_requirement",
        "source_phase_id": "68C",
        "predecessor_phase_id": "68C",
        "activated_phase_id": "68D",
        "selected_branch_id": "BR-004",
        "objective_ids": ["OBJ-001", "OBJ-002"],
        "rationale": "Competitive persistence demotion: Step 3 sort key gains is_persistent_background flag; demotion_is_scheduling_not_priority_ranking=True.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-68C-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_68D,
        "activation_validation_status": "validated",
    }


def _valid_69a_record() -> dict:
    return {
        "lineage_id": "SLR-69A-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69A,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "68D",
        "predecessor_phase_id": "68D",
        "activated_phase_id": "69A",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-001", "OBJ-002", "OBJ-003"],
        "rationale": "BR-005 Execution Governance Activation opens with architecture review of dormancy conditions for Controlled Runtime Execution Pilot (62A).",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-68D-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69A,
        "activation_validation_status": "validated",
    }


def _write_registry(root: Path, records: list[dict], *, provenance: bool = True) -> None:
    pcae_dir = root / ".pcae"
    pcae_dir.mkdir(parents=True, exist_ok=True)
    (pcae_dir / "strategic-lineage.json").write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if provenance:
        (pcae_dir / "provenance-history.json").write_text(
            json.dumps(
                [
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 65I",
                        "timestamp": ACTIVATION_TIMESTAMP,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 66C",
                        "timestamp": ACTIVATION_TIMESTAMP_66C,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 64H",
                        "timestamp": ACTIVATION_TIMESTAMP_64H,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 66D",
                        "timestamp": ACTIVATION_TIMESTAMP_66D,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 66E",
                        "timestamp": ACTIVATION_TIMESTAMP_66E,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 67A",
                        "timestamp": ACTIVATION_TIMESTAMP_67A,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 67B",
                        "timestamp": ACTIVATION_TIMESTAMP_67B,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 68A",
                        "timestamp": ACTIVATION_TIMESTAMP_68A,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 68B",
                        "timestamp": ACTIVATION_TIMESTAMP_68B,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 68C",
                        "timestamp": ACTIVATION_TIMESTAMP_68C,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 68D",
                        "timestamp": ACTIVATION_TIMESTAMP_68D,
                    },
                    {
                        "active_task": None,
                        "agent_id": "codex-local",
                        "event_type": "phase_activated",
                        "git_branch": "main",
                        "summary": "Human-approved activation of Phase 69A",
                        "timestamp": ACTIVATION_TIMESTAMP_69A,
                    },
                ],
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


def _errors_for(tmp_path: Path, record: dict, *, provenance: bool = True) -> tuple[str, ...]:
    _write_registry(
        tmp_path,
        [record, _valid_66c_record(), _valid_64h_record(), _valid_66d_record(), _valid_66e_record(), _valid_67a_record(), _valid_67b_record(), _valid_68a_record(), _valid_68b_record(), _valid_68c_record(), _valid_68d_record(), _valid_69a_record()],
        provenance=provenance,
    )
    return validate_strategic_lineage(HarnessPath(tmp_path)).errors


def test_65j_valid_lineage_passes_with_provenance(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        [_valid_record(), _valid_66c_record(), _valid_64h_record(), _valid_66d_record(), _valid_66e_record(), _valid_67a_record(), _valid_67b_record(), _valid_68a_record(), _valid_68b_record(), _valid_68c_record(), _valid_68d_record(), _valid_69a_record()],
    )
    result = validate_strategic_lineage(HarnessPath(tmp_path))
    assert result.valid is True
    assert result.current_lineage_id == "SLR-69A-TEST"


def test_65j_historical_approved_lineage_can_be_superseded_by_reference(
    tmp_path: Path,
) -> None:
    _write_registry(
        tmp_path,
        [_valid_record(), _valid_66c_record(), _valid_64h_record(), _valid_66d_record(), _valid_66e_record(), _valid_67a_record(), _valid_67b_record(), _valid_68a_record(), _valid_68b_record(), _valid_68c_record(), _valid_68d_record(), _valid_69a_record()],
    )
    result = validate_strategic_lineage(HarnessPath(tmp_path))
    assert result.valid is True
    assert not any("SLR-66C-TEST" in error for error in result.errors)


def test_65j_current_approved_lineage_must_match_live_branch_phase(
    tmp_path: Path, monkeypatch
) -> None:
    from pcae.core import strategic_lineage as strategic_lineage_module

    records = [_valid_record(), _valid_66c_record(), _valid_64h_record(), _valid_66d_record(), _valid_66e_record(), _valid_67a_record(), _valid_67b_record(), _valid_68a_record(), _valid_68b_record(), _valid_68c_record(), _valid_68d_record(), _valid_69a_record()]
    patched_branches = []
    for branch in strategic_lineage_module._SRG_BRANCH_REGISTRY:
        patched = dict(branch)
        if patched["branch_id"] == "BR-005":
            patched["current_phase"] = "66D"
        patched_branches.append(patched)
    monkeypatch.setattr(
        strategic_lineage_module,
        "_SRG_BRANCH_REGISTRY",
        tuple(patched_branches),
    )
    _write_registry(tmp_path, records)
    result = validate_strategic_lineage(HarnessPath(tmp_path))
    assert any(
        "SLR-69A-TEST: activated phase does not match branch current_phase." == error
        for error in result.errors
    )


def test_65j_lineage_does_not_duplicate_activation_timestamp(tmp_path: Path) -> None:
    record = _valid_record()
    assert "activation_timestamp" not in record
    assert _errors_for(tmp_path, record) == ()


def test_65j_decision_basis_is_classified(tmp_path: Path) -> None:
    record = _valid_record()
    record["decision_basis"] = "conversation_memory"
    assert any("invalid decision_basis" in error for error in _errors_for(tmp_path, record))


def test_65j_execution_is_always_forbidden(tmp_path: Path) -> None:
    record = _valid_record()
    record["execution_allowed"] = True
    assert any("execution_allowed must be False" in error for error in _errors_for(tmp_path, record))


def test_65j_review_reference_and_hash_are_validated(tmp_path: Path) -> None:
    record = _valid_record()
    record["finding_snapshot_hash"] = "stale"
    assert any("finding_snapshot_hash" in error for error in _errors_for(tmp_path, record))


def test_65j_alternative_tracking_is_structured(tmp_path: Path) -> None:
    record = _valid_record()
    del record["considered_alternatives"][0]["reason"]
    assert any("alternative missing fields" in error for error in _errors_for(tmp_path, record))


def test_65j_rejected_and_deferred_alternatives_are_distinct(tmp_path: Path) -> None:
    record = _valid_record()
    record["rejected_alternatives"] = ["66C", "64H"]
    errors = _errors_for(tmp_path, record)
    assert any("rejected_alternatives" in error for error in errors)
    assert not any("deferred_alternatives" in error for error in errors)


def test_65j_activated_phase_cannot_be_an_alternative(tmp_path: Path) -> None:
    record = _valid_record()
    record["considered_alternatives"][0]["phase_id"] = "65I"
    record["considered_alternatives"][0]["branch_id"] = "BR-003"
    record["deferred_alternatives"] = ["65I"]
    assert any("activated phase cannot" in error for error in _errors_for(tmp_path, record))


def test_65j_activation_evidence_is_required(tmp_path: Path) -> None:
    record = _valid_record()
    record["activation_event_id"] = ""
    assert any("requires activation_event_id" in error for error in _errors_for(tmp_path, record))


def test_65j_missing_provenance_is_blocking(tmp_path: Path) -> None:
    record = _valid_record()
    errors = _errors_for(tmp_path, record, provenance=False)
    assert any("requires authoritative provenance history" in error for error in errors)


def test_65j_human_approval_is_required(tmp_path: Path) -> None:
    record = _valid_record()
    record["human_approved"] = False
    assert any("human_approved=True" in error for error in _errors_for(tmp_path, record))


def test_65j_supersession_reference_is_validated(tmp_path: Path) -> None:
    record = _valid_record()
    record["supersedes_lineage_id"] = "SLR-MISSING"
    assert any("supersedes_lineage_id" in error for error in _errors_for(tmp_path, record))


def test_65j_migration_exemption_allowlist_is_explicit() -> None:
    assert PRE_65J_MIGRATION_EXEMPT_PHASE_IDS == frozenset({"65I"})


def test_65j_explicit_65i_migration_exemption_passes(tmp_path: Path) -> None:
    record = _valid_record()
    record["activation_validation_status"] = "migration_exempt"
    record["activation_event_id"] = ""
    pcae_dir = tmp_path / ".pcae"
    pcae_dir.mkdir(parents=True, exist_ok=True)
    (pcae_dir / "strategic-lineage.json").write_text(
        json.dumps(
            [record, _valid_66c_record(), _valid_64h_record(), _valid_66d_record(), _valid_66e_record(), _valid_67a_record(), _valid_67b_record(), _valid_68a_record(), _valid_68b_record(), _valid_68c_record(), _valid_68d_record(), _valid_69a_record()],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (pcae_dir / "provenance-history.json").write_text(
        json.dumps(
            [
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 66C",
                    "timestamp": ACTIVATION_TIMESTAMP_66C,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 64H",
                    "timestamp": ACTIVATION_TIMESTAMP_64H,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 66D",
                    "timestamp": ACTIVATION_TIMESTAMP_66D,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 66E",
                    "timestamp": ACTIVATION_TIMESTAMP_66E,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 67A",
                    "timestamp": ACTIVATION_TIMESTAMP_67A,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 67B",
                    "timestamp": ACTIVATION_TIMESTAMP_67B,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 68A",
                    "timestamp": ACTIVATION_TIMESTAMP_68A,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 68B",
                    "timestamp": ACTIVATION_TIMESTAMP_68B,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 68C",
                    "timestamp": ACTIVATION_TIMESTAMP_68C,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 68D",
                    "timestamp": ACTIVATION_TIMESTAMP_68D,
                },
                {
                    "active_task": None,
                    "agent_id": "codex-local",
                    "event_type": "phase_activated",
                    "git_branch": "main",
                    "summary": "Human-approved activation of Phase 69A",
                    "timestamp": ACTIVATION_TIMESTAMP_69A,
                },
            ],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    result = validate_strategic_lineage(HarnessPath(tmp_path))
    assert result.valid is True
    assert result.current_lineage_id == "SLR-69A-TEST"


def test_65j_migration_exemption_cannot_claim_provenance_event(
    tmp_path: Path,
) -> None:
    record = _valid_record()
    record["activation_validation_status"] = "migration_exempt"
    errors = _errors_for(tmp_path, record)
    assert any("must not claim activation_event_id" in error for error in errors)


def test_65j_migration_exemption_does_not_cover_other_phase(tmp_path: Path) -> None:
    record = _valid_record()
    record["activated_phase_id"] = "66C"
    record["selected_branch_id"] = "BR-004"
    record["activation_validation_status"] = "migration_exempt"
    record["activation_event_id"] = ""
    record["considered_alternatives"] = []
    record["rejected_alternatives"] = []
    record["deferred_alternatives"] = []
    assert any("limited to pre-65J phases" in error for error in _errors_for(tmp_path, record))


def test_65j_summary_uses_referenced_review_findings(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_registry(
        tmp_path,
        [_valid_record(), _valid_66c_record(), _valid_64h_record(), _valid_66d_record(), _valid_66e_record(), _valid_67a_record(), _valid_67b_record(), _valid_68a_record(), _valid_68b_record(), _valid_68c_record(), _valid_68d_record(), _valid_69a_record()],
    )
    monkeypatch.chdir(tmp_path)
    assert main(["strategic-continuity", "show", "current", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "referenced_review_findings" in data
    assert "open_strategic_findings" not in data
    # 68D has considered alternatives (rejected hard_demotion and rotational)
    assert isinstance(data["deferred_alternatives"], list)
    assert isinstance(data["rejected_alternatives"], list)


def test_65j_continuity_commands_are_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_registry(
        tmp_path,
        [_valid_record(), _valid_66c_record(), _valid_64h_record(), _valid_66d_record(), _valid_66e_record(), _valid_67a_record(), _valid_67b_record(), _valid_68a_record(), _valid_68b_record(), _valid_68c_record(), _valid_68d_record(), _valid_69a_record()],
    )
    before = {
        path.name: path.read_bytes()
        for path in (tmp_path / ".pcae").iterdir()
        if path.is_file()
    }
    monkeypatch.chdir(tmp_path)
    assert main(["strategic-continuity", "show", "current", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["current"]["lineage_id"] == "SLR-69A-TEST"
    assert main(["strategic-continuity", "history", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["record_count"] == 12
    assert main(["strategic-continuity", "validate", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    after = {
        path.name: path.read_bytes()
        for path in (tmp_path / ".pcae").iterdir()
        if path.is_file()
    }
    assert after == before


def test_65j_duplicate_lineage_ids_fail(tmp_path: Path) -> None:
    record = _valid_record()
    duplicate = copy.deepcopy(record)
    _write_registry(tmp_path, [record, duplicate])
    result = validate_strategic_lineage(HarnessPath(tmp_path))
    assert any("Duplicate lineage_id" in error for error in result.errors)
