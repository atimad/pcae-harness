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
ACTIVATION_TIMESTAMP_69B = "2026-06-13T07:57:40+00:00"
ACTIVATION_TIMESTAMP_69C = "2026-06-13T06:49:36+00:00"
ACTIVATION_TIMESTAMP_69D = "2026-06-14T08:49:00+00:00"
ACTIVATION_TIMESTAMP_69E = "2026-06-14T09:00:00+00:00"
ACTIVATION_TIMESTAMP_69F = "2026-06-14T13:00:00+00:00"
ACTIVATION_TIMESTAMP_69G = "2026-06-14T17:00:00+00:00"
ACTIVATION_TIMESTAMP_69H = "2026-06-15T00:00:00+00:00"
ACTIVATION_TIMESTAMP_69I = "2026-06-15T00:00:01+00:00"
ACTIVATION_TIMESTAMP_69J = "2026-06-15T11:19:00+00:00"
ACTIVATION_TIMESTAMP_69K = "2026-06-15T13:06:00+00:00"
ACTIVATION_TIMESTAMP_69L = "2026-06-15T19:13:00+00:00"
ACTIVATION_TIMESTAMP_69M = "2026-06-16T13:35:00+00:00"
ACTIVATION_TIMESTAMP_69N = "2026-06-16T15:01:00+00:00"
ACTIVATION_TIMESTAMP_69O = "2026-06-16T16:30:00+00:00"


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
        "lineage_status": "superseded",
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


def _valid_69b_record() -> dict:
    return {
        "lineage_id": "SLR-69B-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69B,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69A",
        "predecessor_phase_id": "69A",
        "activated_phase_id": "69B",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": "Implements ApprovedPromptArtifact persistent storage and wires gep-gate-001 and gep-gate-005.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-69A-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69B,
        "activation_validation_status": "validated",
    }


def _valid_69c_record() -> dict:
    return {
        "lineage_id": "SLR-69C-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69C,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69B",
        "predecessor_phase_id": "69B",
        "activated_phase_id": "69C",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": "Validates approved-agent and invocation-contract prerequisites without enabling execution.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-69B-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69C,
        "activation_validation_status": "validated",
    }


def _valid_69d_record() -> dict:
    return {
        "lineage_id": "SLR-69D-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69D,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69C",
        "predecessor_phase_id": "69C",
        "activated_phase_id": "69D",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": "Integrates all four required gates into a single governed pathway without enabling execution.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-69C-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69D,
        "activation_validation_status": "validated",
    }


def _valid_69e_record() -> dict:
    return {
        "lineage_id": "SLR-69E-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69E,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69D",
        "predecessor_phase_id": "69D",
        "activated_phase_id": "69E",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": "Records authorization artifacts before execution for EAR-based authorization verification.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-69D-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69E,
        "activation_validation_status": "validated",
    }


def _valid_69f_record() -> dict:
    return {
        "lineage_id": "SLR-69F-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69F,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69E",
        "predecessor_phase_id": "69E",
        "activated_phase_id": "69F",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": "Records execution audit trail for each governed execution attempt via EAR artifact.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-69E-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69F,
        "activation_validation_status": "validated",
    }


def _valid_69g_record() -> dict:
    return {
        "lineage_id": "SLR-69G-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69G,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69F",
        "predecessor_phase_id": "69F",
        "activated_phase_id": "69G",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": "First controlled execution path: claude-local, read-only, single-agent, 11-condition gate. execution_allowed=True inside invocation boundary only; ERR store at .pcae/results/.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-69F-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69G,
        "activation_validation_status": "validated",
    }


def _valid_69h_record() -> dict:
    return {
        "lineage_id": "SLR-69H-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69H,
        "lineage_status": "superseded",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69G",
        "predecessor_phase_id": "69G",
        "activated_phase_id": "69H",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": "Classifies ERR outcomes on technical_status and governance_attention axes. Ephemeral; no persistence. SLR-69H-001: ExecutionResultReviewArtifact persistence deferred to 69I.",
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve_with_changes",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [],
        "supersedes_lineage_id": "SLR-69G-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69H,
        "activation_validation_status": "validated",
    }


def _valid_69i_record() -> dict:
    return {
        "lineage_id": "SLR-69I-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69I,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69H",
        "predecessor_phase_id": "69H",
        "activated_phase_id": "69I",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": (
            "Introduces append-only ERRA store. Persists human reviewer disposition and ERG snapshot. "
            "Completes APA→ARA→EAR→ERR→ERG→ERRA chain. "
            "SLR-69I-001: multi-reviewer conflict resolution intentionally deferred."
        ),
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": ["SLR-69I-001: multi-reviewer conflict resolution deferred to future phase"],
        "supersedes_lineage_id": "SLR-69H-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69I,
        "activation_validation_status": "validated",
    }


def _valid_69j_record() -> dict:
    return {
        "lineage_id": "SLR-69J-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69J,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69I",
        "predecessor_phase_id": "69I",
        "activated_phase_id": "69J",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": (
            "Introduces ESA store (.pcae/execution-snapshots/) and ECR store "
            "(.pcae/execution-changes/). change_severity classification (none/low/medium/high/critical). "
            "rollback_candidate=True when severity in {medium,high,critical}. "
            "SLR-69J-001: automatic snapshot integration deferred."
        ),
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [
            "SLR-69J-001: automatic snapshot integration into invoke_readonly_execution deferred"
        ],
        "supersedes_lineage_id": "SLR-69I-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69J,
        "activation_validation_status": "validated",
    }


def _valid_69k_record() -> dict:
    return {
        "lineage_id": "SLR-69K-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69K,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "technical_debt",
        "source_phase_id": "69J",
        "predecessor_phase_id": "69J",
        "activated_phase_id": "69K",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": (
            "Closes SLR-69J-001 by integrating ESA creation into invoke_readonly_execution "
            "before subprocess and ECR creation immediately after subprocess. "
            "ERR carries snapshot_id, snapshot_created, ecr_id, ecr_created linkage fields. "
            "snapshot_storage_failure blocks as condition_12_snapshot_storage_failed. "
            "ECR failure is advisory. execution_allowed semantics unchanged."
        ),
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [
            "SLR-69K-001: snapshot storage failure blocks execution; no degraded-mode fallback exists",
            "SLR-69K-002: post-execution capture may include changes from concurrent processes when sandbox_mode=none",
        ],
        "supersedes_lineage_id": "SLR-69J-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69K,
        "activation_validation_status": "validated",
    }


def _valid_69l_record() -> dict:
    return {
        "lineage_id": "SLR-69L-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69L,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "technical_debt",
        "source_phase_id": "69K",
        "predecessor_phase_id": "69K",
        "activated_phase_id": "69L",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": (
            "Introduces workspace isolation for invoke_readonly_execution via git worktree + rsync overlay. "
            "Subprocess runs with cwd=sandbox_dir not root. Condition 13 blocks on sandbox creation or "
            "rsync overlay failure. ERR schema expanded with sandbox_mode=workspace_isolation, sandbox_id, "
            "sandbox_provider. ECR post_state sourced from sandbox before destruction. Six SLR entries "
            "document forward-compatibility constraints for 69M write governance. "
            "SLR-69L-001: sandbox_provider fixed to git_worktree; container providers deferred. "
            "SLR-69L-002: os_isolation deferred; workspace_isolation is development containment only. "
            "SLR-69L-003: sandbox_dir ephemeral; forensic artifact copy deferred. "
            "SLR-69L-004: ECR captures paths not content; ECP class required in 69M for promotion. "
            "SLR-69L-005: workspace isolation is behavioral not OS containment; absolute path writes uncontained. "
            "SLR-69L-006: git worktree shares object store with root; git commits in sandbox persist in shared store."
        ),
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [
            "SLR-69L-001: sandbox_provider fixed to git_worktree; container providers deferred",
            "SLR-69L-002: os_isolation deferred; workspace_isolation is development containment only",
            "SLR-69L-003: sandbox_dir ephemeral; forensic artifact copy deferred",
            "SLR-69L-004: ECR captures paths not content; ECP artifact class required in 69M for promotion payload",
            "SLR-69L-005: workspace isolation is behavioral not OS containment; absolute path writes and symlink write-through uncontained",
            "SLR-69L-006: git worktree shares object store with root; git commits inside sandbox persist in shared store",
        ],
        "supersedes_lineage_id": "SLR-69K-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69L,
        "activation_validation_status": "validated",
    }


def _valid_69m_record() -> dict:
    return {
        "lineage_id": "SLR-69M-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69M,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69L",
        "predecessor_phase_id": "69L",
        "activated_phase_id": "69M",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": (
            "Closes SLR-69L-004 by introducing ExecutionChangePackage (ECP), the canonical "
            "evidence artifact for sandbox-produced content, and ExecutionPromotionReview "
            "(EPR), a human content-level review of a specific ECP with partial-path approval. "
            "Accepted scope is ECP + EPR only -- no promotion execution, no rollback execution, "
            "no git commit, no git push, no automatic promotion. Condition 14 is the first "
            "post-execution governance condition: ECP capture attempt is mandatory and "
            "ordering-enforced before sandbox destruction, but capture success is not "
            "mandated -- failure is always recorded and surfaced as execution_reviewable=False "
            "rather than retroactively setting execution_occurred=False. Ten SLR entries "
            "document the accepted scope and forward-compatibility constraints for a future "
            "promotion-execution phase."
        ),
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [
            "SLR-69M-001: ECP is the canonical evidence artifact, captured from sandbox_dir before destruction, immutable after creation, does not modify root",
            "SLR-69M-002: EPR records human review of ECP content with partial-path approval; promotion_authorized is a separate explicit flag with no consumer until promotion execution exists",
            "SLR-69M-003: .git/ and .pcae/ are permanently excluded from ECP promotion eligibility; cannot be overridden by EPR",
            "SLR-69M-004: external symlink promotion is permanently forbidden",
            "SLR-69M-005: root divergence detection is required before any future promotion; divergence with conflicting files is a hard block",
            "SLR-69M-006: git commits made inside the sandbox are detected via git_head_diverged and must block promotion",
            "SLR-69M-007: promotion execution is deferred to a future phase (69N)",
            "SLR-69M-008: automatic_promotion_allowed=False is a permanent governance boundary, not specific to this phase",
            "SLR-69M-009: before_content is captured per file entry as a rollback payload; rollback execution itself is deferred",
            "SLR-69M-010: ECP capture attempt is mandatory and ordering-enforced (Condition 14) but capture success is not mandatory; sandbox destruction proceeds regardless of ECP outcome, preserving the ESB-C-003/004 cleanup guarantees from 69L",
        ],
        "supersedes_lineage_id": "SLR-69L-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69M,
        "activation_validation_status": "validated",
    }


def _valid_69n_record() -> dict:
    return {
        "lineage_id": "SLR-69N-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69N,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69M",
        "predecessor_phase_id": "69M",
        "activated_phase_id": "69N",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": (
            "Implements Write Promotion Execution: PromotionExecutionRecord (PER) is the "
            "first PCAE artifact and `pcae promote` is the first command that mutates root. "
            "Promotion is gated on an EPR with promotion_authorized=True, never on an ECP "
            "alone. Divergence is checked per file by content hash rather than git HEAD "
            "alone: a path whose current root hash equals the ECP after_hash is "
            "already_applied and is skipped without being re-written or treated as an "
            "error -- this is how re-running `pcae promote` resumes a partial promotion, "
            "with no --resume flag and no additional authority expansion. A path matching "
            "neither before_hash nor after_hash is a conflict that blocks the entire attempt "
            "before any file is touched. Partial promotion is a valid terminal state. PER is "
            "created before the first file write and persisted after every file, so an "
            "interrupted run is always a stored, inspectable record. Ten SLR entries document "
            "the accepted scope."
        ),
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [
            "SLR-69N-001: PER is the first artifact whose subject is root mutation; promotion gated on EPR promotion_authorized=True, not ECP alone",
            "SLR-69N-002: divergence checked per-file by content hash; git HEAD divergence alone is advisory, not blocking",
            "SLR-69N-003: already_applied (current hash matches after_hash) is skipped, not an error, not re-written -- resume-aware with no --resume command",
            "SLR-69N-004: any per-file conflict blocks the entire attempt before any file is touched",
            "SLR-69N-005: partial promotion is a valid terminal state, not automatically retried",
            "SLR-69N-006: PER created before first write, persisted after every file; interruption is always a stored record",
            "SLR-69N-007: mark-interrupted is bookkeeping only, never writes files",
            "SLR-69N-008: EPR override_divergence is not consumed in 69N; conflicts are unconditionally blocking",
            "SLR-69N-009: before_content/rollback_payload_available is evidence only; rollback execution is deferred",
            "SLR-69N-010: no automatic promotion, no git commit/push, no multi-EPR batch promotion, no atomic staged-rename writer -- sequential write plus incremental PER chosen as the smaller mechanism",
        ],
        "supersedes_lineage_id": "SLR-69M-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69N,
        "activation_validation_status": "validated",
    }


def _valid_69o_record() -> dict:
    return {
        "lineage_id": "SLR-69O-TEST",
        "lineage_timestamp": ACTIVATION_TIMESTAMP_69O,
        "lineage_status": "approved",
        "decided_by": "human-user",
        "decision_basis": "roadmap_gap",
        "source_phase_id": "69N",
        "predecessor_phase_id": "69N",
        "activated_phase_id": "69O",
        "selected_branch_id": "BR-005",
        "objective_ids": ["OBJ-002", "OBJ-003"],
        "rationale": (
            "Implements Promotion Rollback Execution: RollbackExecutionRecord (RER) is the "
            "first PCAE artifact whose subject is reversing a root mutation, and `pcae "
            "rollback` is the first command that does so. Rollback is gated on a PER with "
            "status in {completed, partial} and rollback_payload_available=True. file_plan "
            "is derived strictly from PER.file_results where outcome=\"success\" -- never "
            "user-specified, never including already_applied entries. Divergence is the "
            "inverse of 69N's: current hash vs after_hash (pending) / before_hash "
            "(already_reverted) / neither (conflict). Any conflict blocks the entire attempt "
            "before any file is touched. RER created before first restore, persisted after "
            "every file. There is no mechanism to target an RER for reversal, so "
            "rollback-of-rollback is forbidden by construction. Ten SLR entries document the "
            "accepted scope."
        ),
        "review_ids": ["SRR-66B-001"],
        "finding_snapshot_hash": strategic_review_snapshot_hash(["SRR-66B-001"]),
        "recommendation": "approve",
        "considered_alternatives": [],
        "rejected_alternatives": [],
        "deferred_alternatives": [],
        "roadmap_debt": [
            "SLR-69O-001: RER is the first artifact reversing a root mutation; gated on PER.status in {completed, partial} and PER.rollback_payload_available=True",
            "SLR-69O-002: file_plan is derived strictly from PER.file_results where outcome=\"success\"; already_applied PER entries are excluded",
            "SLR-69O-003: divergence is inverted from 69N -- current hash vs after_hash (pending) / before_hash (already_reverted) / neither (conflict)",
            "SLR-69O-004: any conflict blocks the entire attempt before any file is touched",
            "SLR-69O-005: partial rollback is a valid terminal state, not automatically retried",
            "SLR-69O-006: RER created before first restore, persisted after every file; interruption is always a stored record",
            "SLR-69O-007: mark-interrupted is bookkeeping only, never writes files",
            "SLR-69O-008: rollback is idempotent via the already_reverted skip; no --resume command",
            "SLR-69O-009: rollback-of-rollback is forbidden by construction -- no rer_id-accepting entry point exists",
            "SLR-69O-010: no automatic rollback, no git commit/push, no override-divergence support, no multi-PER batch rollback, no user-specified paths",
        ],
        "supersedes_lineage_id": "SLR-69N-TEST",
        "human_approved": True,
        "execution_allowed": False,
        "activation_event_id": ACTIVATION_TIMESTAMP_69O,
        "activation_validation_status": "validated",
    }


def _post_65i_records() -> list[dict]:
    return [
        _valid_66c_record(),
        _valid_64h_record(),
        _valid_66d_record(),
        _valid_66e_record(),
        _valid_67a_record(),
        _valid_67b_record(),
        _valid_68a_record(),
        _valid_68b_record(),
        _valid_68c_record(),
        _valid_68d_record(),
        _valid_69a_record(),
        _valid_69b_record(),
        _valid_69c_record(),
        _valid_69d_record(),
        _valid_69e_record(),
        _valid_69f_record(),
        _valid_69g_record(),
        _valid_69h_record(),
        _valid_69i_record(),
        _valid_69j_record(),
        _valid_69k_record(),
        _valid_69l_record(),
        _valid_69m_record(),
        _valid_69n_record(),
        _valid_69o_record(),
    ]


def _provenance_events(include_65i: bool = True) -> list[dict]:
    events = []
    if include_65i:
        events.append({
            "active_task": None,
            "agent_id": "codex-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 65I",
            "timestamp": ACTIVATION_TIMESTAMP,
        })
    events.extend([
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
        {
            "active_task": None,
            "agent_id": "codex-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69B",
            "timestamp": ACTIVATION_TIMESTAMP_69B,
        },
        {
            "active_task": None,
            "agent_id": "codex-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69C",
            "timestamp": ACTIVATION_TIMESTAMP_69C,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69D",
            "timestamp": ACTIVATION_TIMESTAMP_69D,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69E",
            "timestamp": ACTIVATION_TIMESTAMP_69E,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69F",
            "timestamp": ACTIVATION_TIMESTAMP_69F,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69G",
            "timestamp": ACTIVATION_TIMESTAMP_69G,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69H",
            "timestamp": ACTIVATION_TIMESTAMP_69H,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69I",
            "timestamp": ACTIVATION_TIMESTAMP_69I,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69J",
            "timestamp": ACTIVATION_TIMESTAMP_69J,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69K",
            "timestamp": ACTIVATION_TIMESTAMP_69K,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69L",
            "timestamp": ACTIVATION_TIMESTAMP_69L,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69M",
            "timestamp": ACTIVATION_TIMESTAMP_69M,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69N",
            "timestamp": ACTIVATION_TIMESTAMP_69N,
        },
        {
            "active_task": None,
            "agent_id": "claude-local",
            "event_type": "phase_activated",
            "git_branch": "main",
            "summary": "Human-approved activation of Phase 69O",
            "timestamp": ACTIVATION_TIMESTAMP_69O,
        },
    ])
    return events


def _write_registry(root: Path, records: list[dict], *, provenance: bool = True) -> None:
    pcae_dir = root / ".pcae"
    pcae_dir.mkdir(parents=True, exist_ok=True)
    (pcae_dir / "strategic-lineage.json").write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if provenance:
        (pcae_dir / "provenance-history.json").write_text(
            json.dumps(_provenance_events(), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )


def _errors_for(tmp_path: Path, record: dict, *, provenance: bool = True) -> tuple[str, ...]:
    _write_registry(
        tmp_path,
        [record, *_post_65i_records()],
        provenance=provenance,
    )
    return validate_strategic_lineage(HarnessPath(tmp_path)).errors


def test_65j_valid_lineage_passes_with_provenance(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        [_valid_record(), *_post_65i_records()],
    )
    result = validate_strategic_lineage(HarnessPath(tmp_path))
    assert result.valid is True
    assert result.current_lineage_id == "SLR-69O-TEST"


def test_65j_historical_approved_lineage_can_be_superseded_by_reference(
    tmp_path: Path,
) -> None:
    _write_registry(
        tmp_path,
        [_valid_record(), *_post_65i_records()],
    )
    result = validate_strategic_lineage(HarnessPath(tmp_path))
    assert result.valid is True
    assert not any("SLR-66C-TEST" in error for error in result.errors)


def test_65j_current_approved_lineage_must_match_live_branch_phase(
    tmp_path: Path, monkeypatch
) -> None:
    from pcae.core import strategic_lineage as strategic_lineage_module

    records = [_valid_record(), *_post_65i_records()]
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
        "SLR-69O-TEST: activated phase does not match branch current_phase." == error
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
            [record, *_post_65i_records()],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (pcae_dir / "provenance-history.json").write_text(
        json.dumps(_provenance_events(include_65i=False), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    result = validate_strategic_lineage(HarnessPath(tmp_path))
    assert result.valid is True
    assert result.current_lineage_id == "SLR-69O-TEST"


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
        [_valid_record(), *_post_65i_records()],
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
        [_valid_record(), *_post_65i_records()],
    )
    before = {
        path.name: path.read_bytes()
        for path in (tmp_path / ".pcae").iterdir()
        if path.is_file()
    }
    monkeypatch.chdir(tmp_path)
    assert main(["strategic-continuity", "show", "current", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["current"]["lineage_id"] == "SLR-69O-TEST"
    assert main(["strategic-continuity", "history", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["record_count"] == 26
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


def test_69i_slr_present_in_strategic_lineage(tmp_path: Path) -> None:
    import json as _json

    data = _json.loads((Path(".pcae") / "strategic-lineage.json").read_text())
    slr = next((r for r in data if r.get("lineage_id") == "SLR-69I-001"), None)
    assert slr is not None, "SLR-69I-001 must be present in .pcae/strategic-lineage.json"
    assert slr["activated_phase_id"] == "69I"
    assert slr["selected_branch_id"] == "BR-005"
    assert slr["supersedes_lineage_id"] == "SLR-69H-001"
    assert slr["execution_allowed"] is False
    assert "OBJ-002" in slr["objective_ids"]
    assert "OBJ-003" in slr["objective_ids"]
    assert slr["human_approved"] is True
    assert any("conflict" in debt.lower() for debt in slr.get("roadmap_debt", [])), (
        "SLR-69I-001 roadmap_debt must document deferred multi-reviewer conflict resolution"
    )


def test_69k_slr_present_in_strategic_lineage(tmp_path: Path) -> None:
    import json as _json

    data = _json.loads((Path(".pcae") / "strategic-lineage.json").read_text())
    slr = next((r for r in data if r.get("lineage_id") == "SLR-69K-001"), None)
    assert slr is not None, "SLR-69K-001 must be present in .pcae/strategic-lineage.json"
    assert slr["activated_phase_id"] == "69K"
    assert slr["selected_branch_id"] == "BR-005"
    assert slr["supersedes_lineage_id"] == "SLR-69J-001"
    assert slr["execution_allowed"] is False
    assert "OBJ-002" in slr["objective_ids"]
    assert "OBJ-003" in slr["objective_ids"]
    assert slr["human_approved"] is True
    assert slr["decision_basis"] == "technical_debt"
    assert any("snapshot" in debt.lower() for debt in slr.get("roadmap_debt", [])), (
        "SLR-69K-001 roadmap_debt must document snapshot-related technical debt"
    )


def test_69l_slr_present_in_strategic_lineage(tmp_path: Path) -> None:
    import json as _json

    data = _json.loads((Path(".pcae") / "strategic-lineage.json").read_text())
    slr = next((r for r in data if r.get("lineage_id") == "SLR-69L-001"), None)
    assert slr is not None, "SLR-69L-001 must be present in .pcae/strategic-lineage.json"
    assert slr["activated_phase_id"] == "69L"
    assert slr["selected_branch_id"] == "BR-005"
    assert slr["supersedes_lineage_id"] == "SLR-69K-001"
    assert slr["execution_allowed"] is False
    assert "OBJ-002" in slr["objective_ids"]
    assert "OBJ-003" in slr["objective_ids"]
    assert slr["human_approved"] is True
    assert slr["decision_basis"] == "technical_debt"
    debts = slr.get("roadmap_debt", [])
    assert len(debts) == 6, f"SLR-69L-001 must have 6 roadmap_debt entries, got {len(debts)}"
    assert any("SLR-69L-001" in d for d in debts), "SLR-69L-001 must be in roadmap_debt"
    assert any("SLR-69L-002" in d for d in debts), "SLR-69L-002 must be in roadmap_debt"
    assert any("SLR-69L-003" in d for d in debts), "SLR-69L-003 must be in roadmap_debt"
    assert any("SLR-69L-004" in d for d in debts), "SLR-69L-004 must be in roadmap_debt"
    assert any("SLR-69L-005" in d for d in debts), "SLR-69L-005 must be in roadmap_debt"
    assert any("SLR-69L-006" in d for d in debts), "SLR-69L-006 must be in roadmap_debt"
    assert any("sandbox" in d.lower() or "worktree" in d.lower() for d in debts), (
        "SLR-69L-001 roadmap_debt must document sandbox/worktree technical debt"
    )
