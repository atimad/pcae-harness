"""Rollback Approval Evidence (Phase 149L; RAE-001 v1.0,
`docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`, FROZEN Phase
149I, independently verified Phase 149J with zero BLOCKING findings,
implementation-planned Phase 149K,
`docs/PHASE_149K_ROLLBACK_APPROVAL_EVIDENCE_IMPLEMENTATION_PLAN.md`).

This module owns: the Rollback Approval Binding data model (RAE-001 §8),
the AG3/AG5 family-locked operation-reference profiles (§9-§10), the
`rollback-approval` Decision Template constant (§7), canonical
serialization and canonical, non-arbitrary persistence for Binding and
revocation records (§12-§14, §17), a thin creation API that produces a
Rollback Approval Decision through the existing, unmodified CHGR
Confirmation->Publication pipeline and a Rollback Approval Binding
referencing it (§16), the Evidence Validator
(`resolve_rollback_approval_evidence`, §12/§13/§19 of the 149K plan) that
is the sole authority permitted to derive `approval_present`, and the
narrow `derive_rollback_approval_present` derivation API (§28).

It is NOT: a Permission Broker, a Permission Broker request constructor,
an AG3/AG5 consumer, a Runtime Enforcement adapter, or a Typed Authority
Model (TAM) composition. It imports none of the Permission Broker
Foundation module, the Wave-1 mutation-permission adapter,
`pcae.core.agent`, or the CLTR Typed Authority Model's authority package
(the TAM/CLTR wall, RAE-REQ-001/003/004,
RAE-REQ-037/039/066, 149K plan §6/§49-51) -- verified mechanically by
this repository's import-graph tests
(`tests/test_rollback_approval_evidence_contract.py`), not merely by
convention.

`rollback_approval_binding` is a new, dedicated record type -- it is not
a CHGR-001 record family and not a Typed Authority Model
`human_authorization` artifact (RAE-REQ-003, RAE-REQ-016). Structural
precedent from `HumanAuthorization` (the CLTR authority package's
`authorization_candidate` module) informed this module's field shapes
and conditional-requirement pattern; nothing here imports that module.

Dependency direction (149K plan §80-81, one-way, no cycle):

    CHGR / canonical governance substrate (unmodified)
            |  (read-only: Decision Template extension point, record resolution)
            v
    rollback_approval_evidence.py  (this module)
            |  (future: derive_rollback_approval_present() call)
            v
    a future mutation_permission.py-style rollback adapter (not this phase)

This module derives `approval_present: bool` only. It never constructs a
`PermissionBrokerRequest` and never returns `ALLOW`/`DENY`/`HUMAN_REVIEW`.
AG3/AG5 remain unimplemented and unwired; this module supplies an
evidence *substrate* only, independently testable and usable without any
real rollback ever executing.
"""
from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import os
import tempfile
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Literal, Mapping, Optional, Union

from pcae.governance.publication.chgr_envelope import chgr_timestamp
from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.identity import generate_session_id

# ═══════════════════════════════════════════════════════════════════════════
# Errors
# ═══════════════════════════════════════════════════════════════════════════


class RollbackApprovalError(Exception):
    """Base class for every error this module raises."""


class RollbackApprovalBindingConstructionError(RollbackApprovalError):
    """A `RollbackApprovalBinding` (or one of its component dataclasses)
    was constructed with an internally inconsistent shape (RAE-REQ-022's
    family-lock, or a conditional-field violation of RAE-REQ-017)."""


class RollbackApprovalStorageError(RollbackApprovalError):
    """A canonical-storage operation (write, revoke) could not complete,
    including refusal to overwrite an existing, immutable artifact
    (RAE-REQ-057)."""


class RollbackApprovalDecisionCreationError(RollbackApprovalError):
    """A Rollback Approval Decision could not be created, or a referenced
    Decision could not be resolved as a real, published,
    correctly-templated, digest-matching `human_governance_record`
    (RAE-REQ-018)."""


# ═══════════════════════════════════════════════════════════════════════════
# Closed vocabularies
# ═══════════════════════════════════════════════════════════════════════════


class RollbackDecisionType(str, Enum):
    """The `rollback-approval` Decision Template's exactly-two frozen
    options (RAE-REQ-013). Never conflated with Permission Broker
    ALLOW/DENY/HUMAN_REVIEW vocabulary (RAE-REQ-015)."""

    APPROVE_ROLLBACK = "approve_rollback"
    DENY_ROLLBACK = "deny_rollback"


class BindingDecision(str, Enum):
    """The Binding record's own denormalized `decision` field vocabulary
    (RAE-001 §8), textually distinct from `RollbackDecisionType`'s
    CHGR-level `selected_option_id` vocabulary by RAE-001's own design
    (149K plan §10)."""

    APPROVE = "APPROVE"
    DENY = "DENY"


_DECISION_TO_BINDING_DECISION: Mapping[RollbackDecisionType, BindingDecision] = {
    RollbackDecisionType.APPROVE_ROLLBACK: BindingDecision.APPROVE,
    RollbackDecisionType.DENY_ROLLBACK: BindingDecision.DENY,
}


class RollbackSite(str, Enum):
    """Which of the repository's two `EXECUTION_CLASS_ROLLBACK` mutation
    sites (RAE-001 §1) a Binding targets."""

    AG3 = "AG3"
    AG5 = "AG5"


class BindingState(str, Enum):
    """Mirrors `human_authorization.state`'s shape only (structural
    precedent, RAE-REQ-003); independently, rollback-specific semantics.
    The *persisted* Binding file's `state` is written once at creation as
    `ISSUED` and never rewritten in place (149K plan §34-36); the
    *effective* state used by the Evidence Validator is always computed
    at resolution time from (persisted Binding + revocation-record
    existence + `use_binding` presence + TTL comparison)."""

    ISSUED = "issued"
    USED = "used"
    REVOKED = "revoked"
    EXPIRED = "expired"


class RollbackApprovalValidationResult(str, Enum):
    """RAE-REQ-036's exact eight-value vocabulary. Kept structurally
    distinct from the Permission Broker Foundation module's own
    `DECISION_ALLOW`/`DECISION_DENY`/`DECISION_HUMAN_REVIEW` vocabulary."""

    VALID = "VALID"
    MISSING = "MISSING"
    INVALID = "INVALID"
    STALE = "STALE"
    REVOKED = "REVOKED"
    UNAUTHORIZED_APPROVER = "UNAUTHORIZED_APPROVER"
    WRONG_SCOPE = "WRONG_SCOPE"
    SUPERSEDED = "SUPERSEDED"


# ═══════════════════════════════════════════════════════════════════════════
# Decision Template (RAE-REQ-011/012/013) -- a frozen constant, not code that
# reaches into CHGR internals: build_publication_record already treats
# template_id/template_version as opaque caller-supplied strings (149K
# plan §46-47), so no CHGR schema/registry change is required to introduce
# this template.
# ═══════════════════════════════════════════════════════════════════════════

ROLLBACK_APPROVAL_TEMPLATE_ID = "rollback-approval"

# RAE-REQ-011's prose names this template's version as "1.0.0". CHGR's own,
# unamended `template_version` schema field
# (`schema_resources/chgr/shared/identity.schema.json#/$defs/template_version`)
# is pattern-locked to MAJOR.MINOR (`^[0-9]+\.[0-9]+$`) everywhere it appears
# (`decision_template.schema.json` and `human_governance_record.template_ref`
# alike) -- "1.0.0" is not schema-conformant against CHGR-001's own,
# unamended shape, independently reconfirmed here by direct construction
# (`build_publication_record` fail-closed-refuses it, CHGR-REQ-204/205).
# Recorded as a NON-BLOCKING implementation-phase finding in the Phase 149L
# report: this is a mechanical version-string format correction only (no
# RAE-001 semantic content -- template_id, options, eligible_authority, or
# any other frozen field value -- is altered), required because RAE-REQ-011
# itself names conformance to this exact, unamended schema as its own
# authoring basis.
ROLLBACK_APPROVAL_TEMPLATE_VERSION = "1.0"

ROLLBACK_APPROVAL_TEMPLATE: Mapping[str, object] = {
    "template_id": ROLLBACK_APPROVAL_TEMPLATE_ID,
    "template_version": ROLLBACK_APPROVAL_TEMPLATE_VERSION,
    "authoritative_basis": ["RAE-001 Sec.7", "RWMPC-001 RWMPC-REQ-027"],
    "eligible_authority": (
        "The human operator of this governed repository checkout, per "
        "RAE-001 Sec.6/Sec.8's trust model. No stronger authority-registry "
        "check exists today."
    ),
    "subject_binding_rule": (
        "One instance per rollback attempt. decision_subject SHALL name "
        "the concrete Rollback Operation reference (AG3: job_id + "
        "original_commit_sha; AG5: per_id + ecp_id), never a generic "
        "phrase such as 'rollback approval'."
    ),
    "options": (
        {
            "option_id": RollbackDecisionType.APPROVE_ROLLBACK.value,
            "consequence_text": (
                "Records a human approval of the named Rollback Operation. "
                "This selection, combined with a valid Rollback Approval "
                "Binding record referencing it, may allow a future "
                "rollback request's approval_present to resolve True."
            ),
            "non_effect_text": (
                "Approval alone does not execute, schedule, or guarantee "
                "any rollback. Execution remains gated by the Permission "
                "Broker (POL-001 through POL-007), by RWMPC-001's live "
                "freshness re-check, and by AG3/AG5 remaining unimplemented "
                "today. This selection performs no repository mutation."
            ),
        },
        {
            "option_id": RollbackDecisionType.DENY_ROLLBACK.value,
            "consequence_text": (
                "Records a human refusal of the named Rollback Operation. "
                "A Rollback Approval Binding record MAY reference this "
                "decision to document the refusal for audit purposes."
            ),
            "non_effect_text": (
                "This selection performs no repository mutation and does "
                "not, by itself, block any future distinct rollback "
                "attempt against a different Rollback Operation reference."
            ),
        },
    ),
    "required_fields": ["decision_subject"],
    "optional_fields": ["rationale", "conditions"],
    "confirmation_method": ["L0"],
    "expiry_rule": (
        "The Rollback Approval Decision itself does not expire; the "
        "Rollback Approval Binding record's own expires_at is the "
        "operative freshness mechanism (RAE-001 Sec.11)."
    ),
    "supersession_rules": (
        "A later, published Rollback Approval Decision for the same "
        "decision_subject supersedes an earlier one for evidence-"
        "resolution purposes; supersession is enforced at the "
        "Binding-record layer (RAE-001 Sec.11), not by mutating the "
        "Decision record."
    ),
    "revocation_rules": (
        "Revocation of a Rollback Approval Decision is expressed at the "
        "Binding-record layer via state=revoked; CHGR-001's own revoked "
        "lifecycle state is not relied upon by this contract."
    ),
    "status": "active",
}


def _authority_valid(eligible_authority_text: object) -> bool:
    """RAE-REQ-008(1)'s honest ceiling: no authority registry exists, so
    the `UNAUTHORIZED_APPROVER` trigger is, for now, only a template-shape
    check -- the referenced Decision Template's own `eligible_authority`
    descriptive text must be present and non-empty (149K plan §19). This
    is deliberately *not* an identity check; it is a structural
    placeholder that a future authority-registry integration can replace
    without redesigning this function's call site."""

    return isinstance(eligible_authority_text, str) and bool(eligible_authority_text.strip())


# ═══════════════════════════════════════════════════════════════════════════
# Data model
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RollbackApprovalDecisionRef:
    """Family-locked, read-only pointer to a published rollback-approval
    Decision (a `human_governance_record` whose `template_ref` resolves
    to `rollback-approval`/`1.0.0`), never a copy of its content
    (RAE-REQ-018). Mirrors RAE-001 §8's `governance_record_reference`
    field exactly."""

    record_id: str
    record_digest: str


@dataclass(frozen=True)
class Ag3OperationReference:
    """AG3 (`execute_rollback`) Rollback Operation identity (RAE-REQ-020)."""

    job_id: str
    original_commit_sha: str


@dataclass(frozen=True)
class Ag5OperationReference:
    """AG5 (`build_rollback_execution`) Rollback Operation identity
    (RAE-REQ-021)."""

    per_id: str
    ecp_id: str


@dataclass(frozen=True)
class RepositoryStateBinding:
    """Repository state captured at approval time (RAE-001 §8, §11.2) --
    distinct from RWMPC's own live, execution-time freshness re-check
    (RAE-REQ-033)."""

    head_commit_sha: str
    branch: str


@dataclass(frozen=True)
class RevocationMetadata:
    """Mirrors `human_authorization.revocation_metadata`'s shape only
    (structural precedent, RAE-REQ-003); RAE-REQ-046's exact field set."""

    revoked_at: str
    revoked_by: str
    reason_code: str


@dataclass(frozen=True)
class Ag3RollbackApprovalContext:
    """The live AG3 rollback attempt's own operation context, supplied by
    a future Evidence Consumer (RAE-REQ-035, RAE-REQ-037 -- the Consumer
    performs no trust evaluation itself)."""

    job_id: str
    original_commit_sha: str
    task_id: Optional[str]
    repository_state: RepositoryStateBinding


@dataclass(frozen=True)
class Ag5RollbackApprovalContext:
    """The live AG5 rollback attempt's own operation context."""

    per_id: str
    ecp_id: str
    task_id: Optional[str]
    repository_state: RepositoryStateBinding


RollbackOperationReference = Union[Ag3OperationReference, Ag5OperationReference]
RollbackApprovalContext = Union[Ag3RollbackApprovalContext, Ag5RollbackApprovalContext]


@dataclass(frozen=True)
class RollbackApprovalBinding:
    """RAE-001 §8's field table, independently re-derived (never copied
    from `HumanAuthorization`'s Python shape; no import of it exists in
    this module). Immutable once constructed: `frozen=True` enforces this
    for in-memory instances; the storage layer enforces it for persisted
    artifacts by refusing overwrite (RAE-REQ-057)."""

    evidence_id: str
    governance_record_reference: RollbackApprovalDecisionRef
    rollback_site: RollbackSite
    rollback_operation_reference: RollbackOperationReference
    task_id: Optional[str]
    repository_state_binding: RepositoryStateBinding
    created_at: str
    expires_at: str
    state: BindingState
    decision: BindingDecision
    replay_binding: str
    revocation_metadata: Optional[RevocationMetadata] = None
    use_binding: Optional[str] = None
    content_digest: str = ""

    def __post_init__(self) -> None:
        if self.rollback_site is RollbackSite.AG3 and not isinstance(
            self.rollback_operation_reference, Ag3OperationReference
        ):
            raise RollbackApprovalBindingConstructionError(
                "RollbackApprovalBinding.rollback_operation_reference must be an "
                f"Ag3OperationReference when rollback_site is AG3, got "
                f"{type(self.rollback_operation_reference).__name__} (RAE-REQ-022)."
            )
        if self.rollback_site is RollbackSite.AG5 and not isinstance(
            self.rollback_operation_reference, Ag5OperationReference
        ):
            raise RollbackApprovalBindingConstructionError(
                "RollbackApprovalBinding.rollback_operation_reference must be an "
                f"Ag5OperationReference when rollback_site is AG5, got "
                f"{type(self.rollback_operation_reference).__name__} (RAE-REQ-022)."
            )
        if self.state is BindingState.REVOKED and self.revocation_metadata is None:
            raise RollbackApprovalBindingConstructionError(
                "RollbackApprovalBinding.revocation_metadata is required when state is 'revoked'."
            )
        if self.state is not BindingState.REVOKED and self.revocation_metadata is not None:
            raise RollbackApprovalBindingConstructionError(
                "RollbackApprovalBinding.revocation_metadata is forbidden unless state is 'revoked'."
            )
        if self.state is BindingState.USED and self.use_binding is None:
            raise RollbackApprovalBindingConstructionError(
                "RollbackApprovalBinding.use_binding is required when state is 'used'."
            )
        if self.state is not BindingState.USED and self.use_binding is not None:
            raise RollbackApprovalBindingConstructionError(
                "RollbackApprovalBinding.use_binding is forbidden unless state is 'used'."
            )


@dataclass(frozen=True)
class ValidatedEvidence:
    """The Evidence Validator's structured resolution outcome (149K plan
    §27)."""

    result: RollbackApprovalValidationResult
    approval_present: bool
    binding: Optional[RollbackApprovalBinding]
    diagnostic: Optional[str]


# ═══════════════════════════════════════════════════════════════════════════
# Canonical serialization (RAE-REQ-055) -- independently authored, reusing
# only CHGR's timestamp-normalization convention (chgr_timestamp), never its
# four-family-scoped envelope/validation helpers (149K plan §11).
# ═══════════════════════════════════════════════════════════════════════════


def _operation_reference_to_dict(reference: RollbackOperationReference) -> dict:
    if isinstance(reference, Ag3OperationReference):
        return {"job_id": reference.job_id, "original_commit_sha": reference.original_commit_sha}
    if isinstance(reference, Ag5OperationReference):
        return {"per_id": reference.per_id, "ecp_id": reference.ecp_id}
    raise RollbackApprovalBindingConstructionError(
        f"Unknown rollback_operation_reference type: {type(reference).__name__!r}"
    )


def _operation_reference_from_dict(site: RollbackSite, data: Mapping[str, object]) -> RollbackOperationReference:
    if site is RollbackSite.AG3:
        return Ag3OperationReference(
            job_id=str(data["job_id"]), original_commit_sha=str(data["original_commit_sha"])
        )
    if site is RollbackSite.AG5:
        return Ag5OperationReference(per_id=str(data["per_id"]), ecp_id=str(data["ecp_id"]))
    raise RollbackApprovalBindingConstructionError(f"Unknown rollback_site: {site!r}")


def _binding_to_dict(binding: RollbackApprovalBinding, *, include_digest: bool) -> dict:
    payload: dict = {
        "record_type": "rollback_approval_binding",
        "evidence_id": binding.evidence_id,
        "governance_record_reference": {
            "record_id": binding.governance_record_reference.record_id,
            "record_digest": binding.governance_record_reference.record_digest,
        },
        "rollback_site": binding.rollback_site.value,
        "rollback_operation_reference": _operation_reference_to_dict(binding.rollback_operation_reference),
        "task_id": binding.task_id,
        "repository_state_binding": {
            "head_commit_sha": binding.repository_state_binding.head_commit_sha,
            "branch": binding.repository_state_binding.branch,
        },
        "created_at": binding.created_at,
        "expires_at": binding.expires_at,
        "state": binding.state.value,
        "decision": binding.decision.value,
        "replay_binding": binding.replay_binding,
        "revocation_metadata": (
            {
                "revoked_at": binding.revocation_metadata.revoked_at,
                "revoked_by": binding.revocation_metadata.revoked_by,
                "reason_code": binding.revocation_metadata.reason_code,
            }
            if binding.revocation_metadata is not None
            else None
        ),
        "use_binding": binding.use_binding,
    }
    if include_digest:
        payload["content_digest"] = binding.content_digest
    return payload


def _binding_from_dict(data: Mapping[str, object]) -> RollbackApprovalBinding:
    site = RollbackSite(data["rollback_site"])
    raw_revocation = data.get("revocation_metadata")
    raw_governance_ref = data["governance_record_reference"]
    raw_repo_state = data["repository_state_binding"]
    return RollbackApprovalBinding(
        evidence_id=str(data["evidence_id"]),
        governance_record_reference=RollbackApprovalDecisionRef(
            record_id=str(raw_governance_ref["record_id"]),
            record_digest=str(raw_governance_ref["record_digest"]),
        ),
        rollback_site=site,
        rollback_operation_reference=_operation_reference_from_dict(
            site, data["rollback_operation_reference"]
        ),
        task_id=data.get("task_id"),
        repository_state_binding=RepositoryStateBinding(
            head_commit_sha=str(raw_repo_state["head_commit_sha"]),
            branch=str(raw_repo_state["branch"]),
        ),
        created_at=str(data["created_at"]),
        expires_at=str(data["expires_at"]),
        state=BindingState(data["state"]),
        decision=BindingDecision(data["decision"]),
        replay_binding=str(data["replay_binding"]),
        revocation_metadata=(
            RevocationMetadata(
                revoked_at=str(raw_revocation["revoked_at"]),
                revoked_by=str(raw_revocation["revoked_by"]),
                reason_code=str(raw_revocation["reason_code"]),
            )
            if raw_revocation is not None
            else None
        ),
        use_binding=data.get("use_binding"),
        content_digest=str(data.get("content_digest", "")),
    )


def _canonical_bytes(binding: RollbackApprovalBinding) -> bytes:
    payload = _binding_to_dict(binding, include_digest=False)
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _compute_content_digest(binding: RollbackApprovalBinding) -> str:
    return hashlib.sha256(_canonical_bytes(binding)).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# Atomic persistence (RAE-REQ-056, RAE-REQ-057) -- duplicated, not imported,
# from governance/publication/storage.py's proven technique (149K plan §14):
# tempfile.mkstemp in the target directory, write, fsync, os.replace.
# ═══════════════════════════════════════════════════════════════════════════

_DEFAULT_EVIDENCE_ROOT = Path(".pcae") / "rollback-approval-evidence"


def _write_atomic_json(path: Path, payload: dict) -> None:
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RollbackApprovalStorageError(
            f"{path} already exists; refusing to overwrite an immutable rollback-approval-evidence record."
        )
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, str(path))
    except OSError as exc:
        raise RollbackApprovalStorageError(f"Failed to durably persist {path}: {exc}") from exc
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _registration_to_dict(binding: RollbackApprovalBinding) -> dict:
    """Phase 149N canonical creation registration payload (closes Findings
    F1, F4a, F4b / B-149M-1/3/4). Written exactly once, exclusively, by
    `create_rollback_approval_binding` -- never by
    `resolve_rollback_approval_evidence`, and never re-writable in place.
    Binds the Binding's canonical `evidence_id` (the store's own lookup
    key) to its exact content digest and declared identity fields, so a
    Binding resolved from a different registration key, or whose content
    no longer matches what was registered at creation time, is rejected."""

    return {
        "record_type": "rollback_approval_binding_creation_registration",
        "evidence_id": binding.evidence_id,
        "binding_content_digest": binding.content_digest,
        "governance_record_reference": {
            "record_id": binding.governance_record_reference.record_id,
            "record_digest": binding.governance_record_reference.record_digest,
        },
        "rollback_site": binding.rollback_site.value,
        "rollback_operation_reference": _operation_reference_to_dict(binding.rollback_operation_reference),
    }


class RollbackApprovalEvidenceStore:
    """Filesystem-backed, canonical, non-arbitrary store for Rollback
    Approval Binding and revocation records (RAE-REQ-056). Never a
    caller-suppliable free-form path: every write/read is addressed by
    `evidence_id` only. The root defaults to the real repository's
    `.pcae/rollback-approval-evidence/` only at this default-constructor
    boundary -- every function in this module accepts an explicit store
    (or root) so tests never touch the real project's own `.pcae/`
    (149K plan §57-58)."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self._root = Path(root) if root is not None else _DEFAULT_EVIDENCE_ROOT
        self._bindings_dir = self._root / "bindings"
        self._revocations_dir = self._root / "revocations"
        self._creation_registry_dir = self._root / "creation-registry"

    @property
    def root(self) -> Path:
        return self._root

    def _binding_path(self, evidence_id: str) -> Path:
        return self._bindings_dir / f"{evidence_id}.json"

    def _revocation_path(self, evidence_id: str) -> Path:
        return self._revocations_dir / f"{evidence_id}.json"

    def _registration_path(self, evidence_id: str) -> Path:
        return self._creation_registry_dir / f"{evidence_id}.json"

    def write_binding(self, binding: RollbackApprovalBinding) -> Path:
        path = self._binding_path(binding.evidence_id)
        _write_atomic_json(path, _binding_to_dict(binding, include_digest=True))
        return path

    def remove_binding(self, evidence_id: str) -> None:
        """Rollback helper (Phase 149N, RAE-REQ-056/057-adjacent atomicity
        discipline): removes a just-written Binding whose canonical
        creation registration could not be durably committed, so no
        Binding file is ever left on disk without its registration, and no
        Binding is ever readable in a partially-trusted state."""

        with contextlib.suppress(FileNotFoundError):
            self._binding_path(evidence_id).unlink()

    def write_creation_registration(self, binding: RollbackApprovalBinding) -> Path:
        """Phase 149N: the canonical creation registration, the sole
        source `resolve_rollback_approval_evidence` trusts to distinguish
        a Binding produced by `create_rollback_approval_binding` from one
        hand-authored or copied directly into `bindings/`. Written via an
        exclusive (`O_CREAT | O_EXCL`) create -- mirroring
        `PublicationRecordStore.commit_publication`'s own idempotency-
        marker technique -- so it can never silently overwrite a prior
        registration for the same `evidence_id`."""

        path = self._registration_path(binding.evidence_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = _registration_to_dict(binding)
        data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError:
            with contextlib.suppress(OSError):
                os.unlink(str(path))
            raise
        return path

    def read_creation_registration(self, evidence_id: str) -> Optional[dict]:
        path = self._registration_path(evidence_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def read_binding(self, evidence_id: str) -> Optional[RollbackApprovalBinding]:
        """Returns `None` only when no Binding file exists for
        `evidence_id` (RAE-REQ-036's `MISSING` case). Any other failure
        (malformed JSON, missing/invalid field) propagates as an
        exception -- the Evidence Validator's own fail-closed wrapper
        (RAE-REQ-042) is the intended catcher, not this method."""

        path = self._binding_path(evidence_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return _binding_from_dict(data)

    def list_bindings(self) -> list:
        """Every currently-persisted Binding, in no particular selection
        order. Used only to detect supersession/at-most-one-active-Binding
        for an *already-identified* operation reference or Decision
        reference -- never to select which `evidence_id` to resolve
        (RAE-REQ-041; 149K plan §36)."""

        return [binding for _key, binding in self.list_bindings_with_keys()]

    def list_bindings_with_keys(self) -> list:
        """Phase 149N: like `list_bindings`, but pairs each Binding with
        the filename-derived key it was actually found under
        (`(lookup_key, binding)`), so a caller can distinguish that key
        from the payload's own internal `evidence_id` field when checking
        canonical creation registration (closes Finding F4a's supersession
        variant: a copied Binding's internal `evidence_id` field, left
        unchanged, must never be treated as its filename-based identity).
        Phase 149N (directory-injection hardening): a malformed file
        dropped directly into the canonical `bindings/` directory (invalid
        JSON, or missing/malformed required fields) is silently skipped
        here rather than raised -- candidate discovery is not itself a
        trust decision (a skipped file is never treated as canonical
        evidence either way), and an unrelated piece of directory-
        injection garbage must not be able to fail-closed an otherwise
        legitimate, unrelated resolution via an uncaught exception."""

        if not self._bindings_dir.exists():
            return []
        results = []
        for path in sorted(self._bindings_dir.glob("*.json")):
            try:
                binding = self.read_binding(path.stem)
            except (KeyError, ValueError, TypeError):
                continue
            if binding is not None:
                results.append((path.stem, binding))
        return results

    def is_revoked(self, evidence_id: str) -> bool:
        return self._revocation_path(evidence_id).exists()

    def read_revocation(self, evidence_id: str) -> Optional[RevocationMetadata]:
        path = self._revocation_path(evidence_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return RevocationMetadata(
            revoked_at=str(data["revoked_at"]),
            revoked_by=str(data["revoked_by"]),
            reason_code=str(data["reason_code"]),
        )

    def write_revocation(self, evidence_id: str, metadata: RevocationMetadata) -> Path:
        path = self._revocation_path(evidence_id)
        payload = {
            "record_type": "rollback_approval_revocation",
            "revoked_at": metadata.revoked_at,
            "revoked_by": metadata.revoked_by,
            "reason_code": metadata.reason_code,
        }
        _write_atomic_json(path, payload)
        return path


# ═══════════════════════════════════════════════════════════════════════════
# Clock (149K plan §31) -- a narrow, module-local test override point, never
# exposed as a public API, never reachable from a CLI flag or production
# configuration value.
# ═══════════════════════════════════════════════════════════════════════════

_CLOCK_OVERRIDE: "contextvars.ContextVar[Optional[datetime]]" = contextvars.ContextVar(
    "_rollback_approval_evidence_clock_override", default=None
)


def _now_utc() -> datetime:
    override = _CLOCK_OVERRIDE.get()
    return override if override is not None else datetime.now(timezone.utc)


@contextlib.contextmanager
def _frozen_clock(instant: datetime):
    """Test-only. Freezes `_now_utc()` to `instant` for the duration of
    the context. Never imported outside this module's own test files."""

    token = _CLOCK_OVERRIDE.set(instant)
    try:
        yield
    finally:
        _CLOCK_OVERRIDE.reset(token)


def _parse_iso_timestamp(value: object) -> Optional[datetime]:
    """Fail-closed timestamp parsing (RAE-REQ-042, 149K plan §32-33): a
    malformed or ambiguous (naive) timestamp returns `None`, which every
    caller in this module treats as invalid -- never as "no constraint"."""

    if not isinstance(value, str) or not value:
        return None
    try:
        text = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════
# Decision resolution (RAE-REQ-018) -- the load-bearing canonicality check.
# Reads CHGR's own existing, unmodified storage directly
# (`<publication_root>/records/<record_id>.json`, matching
# `PublicationRecordStore`'s own documented `records/<record_id>.json`
# convention) -- never imports or mutates CHGR internals.
# ═══════════════════════════════════════════════════════════════════════════


def _chgr_record_has_publication_receipt(record_id: str, *, publication_root: Path) -> bool:
    """Phase 149N canonical-provenance hardening (closes Finding F2 /
    B-149M-2). A hand-authored file dropped directly at
    `records/<record_id>.json` is schema-shaped and digest-self-consistent,
    but it is not the product of the real `PublicationCoordinator.execute`
    pipeline unless that pipeline's own idempotency marker
    (`published/<package_id>.json`, `PublicationRecordStore.commit_publication`)
    names this exact `record_id`. That marker is the root trust anchor this
    hardening relies on: it is written, exclusively (`O_CREAT | O_EXCL`),
    only at the end of a successful `PublicationCoordinator.execute` call,
    after CHGR's own Authorization/Confirmation/Publication checks already
    passed -- a fact a hand-authored `records/` file cannot also fabricate
    without independently winning that same exclusive-create race for some
    `package_id`, which this function does not need to assume is
    impossible: it need only observe that *this specific, disclosed
    threat model's* adversarial writes (149M F2) never create one. This
    predicate is deliberately *not* `if path is under .pcae/...`: it reads
    a second, independently-written artifact and requires exact identity
    agreement between the two, never trusting the record file's own
    declared content alone."""

    published_dir = Path(publication_root) / "published"
    if not published_dir.exists():
        return False
    for marker_path in published_dir.glob("*.json"):
        try:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(marker, dict):
            continue
        if marker.get("record_id") == record_id:
            return True
        chgr_record_ids = marker.get("chgr_record_ids")
        if isinstance(chgr_record_ids, dict) and record_id in chgr_record_ids.values():
            return True
    return False


def _resolve_decision_ref(ref: RollbackApprovalDecisionRef, *, publication_root: Path) -> dict:
    """Resolve `ref` against real CHGR storage. Raises
    `RollbackApprovalDecisionCreationError` on any resolution failure
    (missing record, JSON error, digest mismatch, wrong template, not
    published, or a `selected_option_id` outside the closed rollback
    vocabulary) -- shared, unchanged, by both creation-time (§16) and
    consumption-time (§19) validation, so the two checks cannot drift
    apart (149K plan §23). Phase 149N's canonical-publication-receipt
    check (`_chgr_record_has_publication_receipt`) is deliberately layered
    on top of this function at the resolution call site only, not inside
    it: this function's four checks stay exactly as permissive at
    creation-time as before 149N (a Binding MAY still be created
    referencing a Decision that later fails the resolution-time receipt
    check -- creation-time permissiveness is not itself a security
    boundary; RAE-REQ-018's `approval_present` gate is), while
    `resolve_rollback_approval_evidence` -- the sole authority permitted
    to derive `approval_present` (RAE-REQ-034) -- always additionally
    requires it."""

    record_path = Path(publication_root) / "records" / f"{ref.record_id}.json"
    if not record_path.exists():
        raise RollbackApprovalDecisionCreationError(
            f"No published CHGR record found for record_id={ref.record_id!r}."
        )
    try:
        data = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RollbackApprovalDecisionCreationError(
            f"Failed to read/parse CHGR record {ref.record_id!r}: {exc}"
        ) from exc

    if data.get("record_digest") != ref.record_digest:
        raise RollbackApprovalDecisionCreationError(
            f"record_digest mismatch for {ref.record_id!r}: reference does not match the "
            "actually-published record's current content-integrity digest."
        )

    template_ref = data.get("template_ref") or {}
    if (
        template_ref.get("template_id") != ROLLBACK_APPROVAL_TEMPLATE_ID
        or template_ref.get("version") != ROLLBACK_APPROVAL_TEMPLATE_VERSION
    ):
        raise RollbackApprovalDecisionCreationError(
            f"CHGR record {ref.record_id!r} does not resolve to template_ref "
            f"{ROLLBACK_APPROVAL_TEMPLATE_ID}/{ROLLBACK_APPROVAL_TEMPLATE_VERSION}."
        )

    if data.get("lifecycle_state") != "published":
        raise RollbackApprovalDecisionCreationError(
            f"CHGR record {ref.record_id!r} is not published (lifecycle_state="
            f"{data.get('lifecycle_state')!r})."
        )

    selected_option_id = data.get("selected_option_id")
    if selected_option_id not in {member.value for member in RollbackDecisionType}:
        raise RollbackApprovalDecisionCreationError(
            f"CHGR record {ref.record_id!r} selected_option_id {selected_option_id!r} is outside "
            "the closed rollback-approval vocabulary."
        )

    return data


# ═══════════════════════════════════════════════════════════════════════════
# Canonical creation (RAE-REQ-079, 149K plan §16-24)
# ═══════════════════════════════════════════════════════════════════════════


def create_rollback_approval_decision(
    *,
    decision: RollbackDecisionType,
    decision_subject: str,
    decision_maker_identity_evidence: Mapping[str, object],
    operator_id: str,
    rationale_text: Optional[str] = None,
    conditions_text: Optional[str] = None,
    publication_store: Optional[PublicationRecordStore] = None,
) -> RollbackApprovalDecisionRef:
    """Thin orchestration wrapper around the existing, unmodified CHGR
    Confirmation->Publication pipeline (`PublicationCoordinator`),
    supplying the frozen `rollback-approval` template (RAE-REQ-011). Does
    not reimplement CHGR publication; produces exactly one published
    `human_governance_record` (+ its three CHGR companion artifacts) and
    returns a read-only reference to it. This is the *only* function pair
    in this module (together with `create_rollback_approval_binding`)
    that writes canonical evidence (149K plan §16, §83)."""

    if not isinstance(decision, RollbackDecisionType):
        raise RollbackApprovalDecisionCreationError(
            f"decision must be a RollbackDecisionType member, got {decision!r} (RAE-REQ-014)."
        )

    store = publication_store if publication_store is not None else PublicationRecordStore()
    coordinator = PublicationCoordinator(store=store)
    now = chgr_timestamp(_now_utc().isoformat())

    package = PublicationReadinessPackage(
        package_id=f"rae-pkg-{uuid.uuid4().hex}",
        session_id=generate_session_id(),
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=(),
        clarification_refs=(),
        audit_refs=(),
        preview_id=f"rae-preview-{uuid.uuid4().hex}",
        preview_digest=hashlib.sha256(decision_subject.encode("utf-8")).hexdigest(),
        confirmation_request_id=f"rae-req-{uuid.uuid4().hex}",
        confirmation_response_id=f"rae-resp-{uuid.uuid4().hex}",
        built_at=now,
        decision_subject=decision_subject,
        template_id=ROLLBACK_APPROVAL_TEMPLATE_ID,
        template_version=ROLLBACK_APPROVAL_TEMPLATE_VERSION,
        selected_option_id=decision.value,
        rationale_text=rationale_text,
        conditions_text=conditions_text,
        options_presented=tuple(member.value for member in RollbackDecisionType),
        decision_maker_identity_evidence=decision_maker_identity_evidence,
        preview_rendered_content=decision_subject,
        confirmation_statement=f"Confirmed: {decision.value} for {decision_subject}",
        confirmation_timestamp=now,
    )

    try:
        event = coordinator.authorize(operator_id=operator_id, package_id=package.package_id, invoked_at=now)
        result = coordinator.execute(package, event)
    except Exception as exc:  # noqa: BLE001 - re-raised as this module's own error type
        raise RollbackApprovalDecisionCreationError(
            f"CHGR Confirmation->Publication pipeline refused this Rollback Approval Decision: {exc}"
        ) from exc

    if not result.success or not result.record_id:
        raise RollbackApprovalDecisionCreationError(
            f"Publication did not succeed: {result.failure_reason or result.diagnostics}"
        )

    record_path = Path(store.root) / "records" / f"{result.record_id}.json"
    record_body = json.loads(record_path.read_text(encoding="utf-8"))
    return RollbackApprovalDecisionRef(record_id=result.record_id, record_digest=record_body["record_digest"])


def _binding_effective_state(
    binding: RollbackApprovalBinding, store: RollbackApprovalEvidenceStore, *, now: datetime
) -> BindingState:
    """The Binding's *effective* state, computed at resolution time
    (149K plan §34-36) -- never the persisted file's own `state` field
    read verbatim, since revocation/expiry are append-only, out-of-file
    facts by this plan's design."""

    if store.is_revoked(binding.evidence_id):
        return BindingState.REVOKED
    if binding.use_binding is not None:
        return BindingState.USED
    expires_at = _parse_iso_timestamp(binding.expires_at)
    if expires_at is None or now >= expires_at:
        return BindingState.EXPIRED
    return BindingState.ISSUED


def create_rollback_approval_binding(
    *,
    decision_ref: RollbackApprovalDecisionRef,
    rollback_site: RollbackSite,
    rollback_operation_reference: RollbackOperationReference,
    task_id: Optional[str],
    repository_state_binding: RepositoryStateBinding,
    ttl_hours: Literal[24] = 24,
    publication_root: Optional[Path] = None,
    evidence_store: Optional[RollbackApprovalEvidenceStore] = None,
) -> RollbackApprovalBinding:
    """Creates and durably persists a `RollbackApprovalBinding` referencing
    an already-resolvable canonical Decision (`decision_ref`). Enforces,
    in order: (1) the Decision resolves (exists, published, correctly
    templated, digest-matching) before any Binding is constructed --
    RAE-REQ-018, no orphan/forward-reference Binding (149K plan §22); (2)
    at most one `issued`/`used` Binding exists per Decision (RAE-REQ-019);
    then constructs, digests, and atomically persists the Binding
    (RAE-REQ-055/RAE-REQ-056)."""

    if ttl_hours != 24:
        raise RollbackApprovalBindingConstructionError(
            "ttl_hours is frozen at 24 by RAE-REQ-043 and is not caller-overridable."
        )
    if not isinstance(rollback_site, RollbackSite):
        raise RollbackApprovalBindingConstructionError(f"rollback_site must be a RollbackSite member, got {rollback_site!r}.")

    pub_root = Path(publication_root) if publication_root is not None else PublicationRecordStore().root
    store = evidence_store if evidence_store is not None else RollbackApprovalEvidenceStore()

    resolved = _resolve_decision_ref(decision_ref, publication_root=pub_root)

    now = _now_utc()
    for existing in store.list_bindings():
        if existing.governance_record_reference.record_id != decision_ref.record_id:
            continue
        if _binding_effective_state(existing, store, now=now) in (BindingState.ISSUED, BindingState.USED):
            raise RollbackApprovalBindingConstructionError(
                f"Decision {decision_ref.record_id!r} is already referenced by an active Binding "
                f"({existing.evidence_id!r}); RAE-REQ-019 permits at most one issued/used Binding "
                "per Decision at a time."
            )

    decision_type = RollbackDecisionType(resolved["selected_option_id"])
    binding_decision = _DECISION_TO_BINDING_DECISION[decision_type]

    created_at = chgr_timestamp(now.isoformat())
    expires_at = chgr_timestamp((now + timedelta(hours=24)).isoformat())

    binding = RollbackApprovalBinding(
        evidence_id=f"rae-{uuid.uuid4().hex}",
        governance_record_reference=decision_ref,
        rollback_site=rollback_site,
        rollback_operation_reference=rollback_operation_reference,
        task_id=task_id,
        repository_state_binding=repository_state_binding,
        created_at=created_at,
        expires_at=expires_at,
        state=BindingState.ISSUED,
        decision=binding_decision,
        replay_binding=f"raerep-{uuid.uuid4().hex}",
    )
    binding = replace(binding, content_digest=_compute_content_digest(binding))
    store.write_binding(binding)
    try:
        store.write_creation_registration(binding)
    except OSError as exc:
        # Phase 149N atomicity discipline: a Binding file MUST NOT exist
        # without its canonical creation registration, or it would be
        # readable and indistinguishable from a legitimately-created one
        # despite this call never having actually completed. Roll back the
        # just-written Binding rather than leave an orphan-trusted file.
        store.remove_binding(binding.evidence_id)
        raise RollbackApprovalStorageError(
            f"Failed to durably commit the canonical creation registration for "
            f"evidence_id={binding.evidence_id!r}: {exc}. The just-written Binding record has "
            "been rolled back; no Binding exists in canonical storage."
        ) from exc
    return binding


def revoke_rollback_approval_binding(
    evidence_id: str,
    *,
    revoked_by: str,
    reason_code: str,
    evidence_store: Optional[RollbackApprovalEvidenceStore] = None,
) -> RevocationMetadata:
    """Writes an immutable revocation record (RAE-REQ-046). Never edits
    the original Binding file in place (149K plan §34-36)."""

    store = evidence_store if evidence_store is not None else RollbackApprovalEvidenceStore()
    binding = store.read_binding(evidence_id)
    if binding is None:
        raise RollbackApprovalStorageError(f"No Binding found for evidence_id={evidence_id!r}; cannot revoke.")
    if store.is_revoked(evidence_id):
        raise RollbackApprovalStorageError(f"Binding {evidence_id!r} is already revoked.")
    metadata = RevocationMetadata(
        revoked_at=chgr_timestamp(_now_utc().isoformat()),
        revoked_by=revoked_by,
        reason_code=reason_code,
    )
    store.write_revocation(evidence_id, metadata)
    return metadata


# ═══════════════════════════════════════════════════════════════════════════
# Evidence Validator (RAE-001 §12; RAE-REQ-034-042; 149K plan §19, §25-29)
# ═══════════════════════════════════════════════════════════════════════════


def _operation_matches(reference: RollbackOperationReference, context: RollbackApprovalContext) -> bool:
    if isinstance(reference, Ag3OperationReference) and isinstance(context, Ag3RollbackApprovalContext):
        return (
            reference.job_id == context.job_id
            and reference.original_commit_sha == context.original_commit_sha
        )
    if isinstance(reference, Ag5OperationReference) and isinstance(context, Ag5RollbackApprovalContext):
        return reference.per_id == context.per_id and reference.ecp_id == context.ecp_id
    return False


def _expected_site_for(context: RollbackApprovalContext) -> RollbackSite:
    return RollbackSite.AG3 if isinstance(context, Ag3RollbackApprovalContext) else RollbackSite.AG5


def _binding_is_canonically_created(
    binding: RollbackApprovalBinding,
    store: RollbackApprovalEvidenceStore,
    *,
    lookup_key: Optional[str] = None,
) -> bool:
    """Phase 149N (closes Findings F1, F4a, F4b / B-149M-1/3/4): `True`
    only if a canonical creation registration exists for exactly the key
    this Binding was looked up under (`lookup_key` -- the store's own
    filename-based `evidence_id`, defaulting to the payload's own internal
    `evidence_id` field only when no distinct lookup key is known, e.g.
    when scanning `list_bindings()` for supersession candidates) and that
    registration's own declared fields exactly match this Binding's
    current, self-consistent content -- never merely that *some*
    registration file exists somewhere, and never merely that the
    Binding's own `content_digest` self-consistency check (already
    performed by the caller) passed. Deliberately keyed by `lookup_key`,
    not `binding.evidence_id`: a verbatim copy of a legitimate Binding's
    bytes placed under a new filename (F4a) still carries the *old*
    internal `evidence_id` field (digest-self-consistent, since the digest
    covers that unchanged internal field) -- checking the registration
    under the filename actually used to look it up, not the payload's own
    claim about its identity, is what makes the copy attack fail here."""

    key = lookup_key if lookup_key is not None else binding.evidence_id
    registration = store.read_creation_registration(key)
    if registration is None:
        return False
    if registration.get("evidence_id") != key or binding.evidence_id != key:
        return False
    if registration.get("binding_content_digest") != binding.content_digest:
        return False
    expected_governance_ref = {
        "record_id": binding.governance_record_reference.record_id,
        "record_digest": binding.governance_record_reference.record_digest,
    }
    if registration.get("governance_record_reference") != expected_governance_ref:
        return False
    if registration.get("rollback_site") != binding.rollback_site.value:
        return False
    if registration.get("rollback_operation_reference") != _operation_reference_to_dict(
        binding.rollback_operation_reference
    ):
        return False
    return True


def _is_superseded(binding: RollbackApprovalBinding, store: RollbackApprovalEvidenceStore) -> bool:
    """RAE-REQ-047: a later, published Binding referencing the same
    `rollback_operation_reference` supersedes an earlier one. This scans
    already-persisted Bindings only to detect supersession for `binding`'s
    own, already-identified operation reference -- never to select which
    `evidence_id` to resolve in the first place (RAE-REQ-041). Phase 149N
    (closes Finding F4b / B-149M-4): a competing record is eligible to
    supersede only if it is itself canonically created (§14 of the
    governing phase prompt, "filter candidates to canonical... before
    considering created_at") -- a hand-authored file with a forged, later
    `created_at` written directly into the canonical directory is not a
    supersession candidate at all, regardless of its timestamp."""

    own_created_at = _parse_iso_timestamp(binding.created_at)
    if own_created_at is None:
        return False
    for other_key, other in store.list_bindings_with_keys():
        if other_key == binding.evidence_id:
            continue
        if other.rollback_site != binding.rollback_site:
            continue
        if other.rollback_operation_reference != binding.rollback_operation_reference:
            continue
        if not _binding_is_canonically_created(other, store, lookup_key=other_key):
            continue
        other_created_at = _parse_iso_timestamp(other.created_at)
        if other_created_at is not None and other_created_at > own_created_at:
            return True
    return False


def resolve_rollback_approval_evidence(
    operation_context: RollbackApprovalContext,
    evidence_id: str,
    *,
    evidence_store: Optional[RollbackApprovalEvidenceStore] = None,
    publication_root: Optional[Path] = None,
) -> ValidatedEvidence:
    """The Evidence Validator (RAE-001 §12): the sole component permitted
    to resolve Rollback Approval Evidence and derive `approval_present`
    (RAE-REQ-034). Requires an explicit `evidence_id` -- never a "latest"
    lookup (RAE-REQ-041). Evaluates RAE-REQ-038's full conjunction and
    fails closed (`approval_present=False`) on every unmet condition,
    including any internal error (RAE-REQ-042) -- no exception from this
    function ever propagates to the caller."""

    try:
        store = evidence_store if evidence_store is not None else RollbackApprovalEvidenceStore()
        pub_root = Path(publication_root) if publication_root is not None else PublicationRecordStore().root

        binding = store.read_binding(evidence_id)
        if binding is None:
            return ValidatedEvidence(
                RollbackApprovalValidationResult.MISSING,
                False,
                None,
                f"No Rollback Approval Binding found for evidence_id={evidence_id!r}.",
            )

        expected_digest = _compute_content_digest(replace(binding, content_digest=""))
        if expected_digest != binding.content_digest:
            return ValidatedEvidence(
                RollbackApprovalValidationResult.INVALID,
                False,
                binding,
                "content_digest mismatch: this Binding record has been tampered with or corrupted "
                "since creation (RAE-REQ-055).",
            )

        if not _binding_is_canonically_created(binding, store, lookup_key=evidence_id):
            return ValidatedEvidence(
                RollbackApprovalValidationResult.INVALID,
                False,
                binding,
                f"No canonical creation registration matches evidence_id={evidence_id!r}; a "
                "well-formed, digest-self-consistent Binding is not sufficient canonical "
                "provenance on its own (Phase 149N, closes B-149M-1/B-149M-3).",
            )

        try:
            resolved_decision = _resolve_decision_ref(binding.governance_record_reference, publication_root=pub_root)
        except RollbackApprovalDecisionCreationError as exc:
            return ValidatedEvidence(
                RollbackApprovalValidationResult.INVALID,
                False,
                binding,
                f"governance_record_reference did not resolve to a real, published, "
                f"correctly-templated Rollback Approval Decision: {exc}",
            )

        if not _chgr_record_has_publication_receipt(
            binding.governance_record_reference.record_id, publication_root=pub_root
        ):
            return ValidatedEvidence(
                RollbackApprovalValidationResult.INVALID,
                False,
                binding,
                f"CHGR record {binding.governance_record_reference.record_id!r} has no matching "
                "PublicationCoordinator idempotency-marker receipt under published/*.json; a "
                "schema-valid, digest-consistent, correctly-templated record is not sufficient "
                "canonical provenance on its own (Phase 149N, closes B-149M-2).",
            )

        if resolved_decision["selected_option_id"] != RollbackDecisionType.APPROVE_ROLLBACK.value:
            return ValidatedEvidence(
                RollbackApprovalValidationResult.INVALID,
                False,
                binding,
                "Referenced Decision's selected_option_id is "
                f"{resolved_decision['selected_option_id']!r}, not approve_rollback (RAE-REQ-038(c)).",
            )

        if not _authority_valid(ROLLBACK_APPROVAL_TEMPLATE["eligible_authority"]):
            return ValidatedEvidence(
                RollbackApprovalValidationResult.UNAUTHORIZED_APPROVER,
                False,
                binding,
                "The rollback-approval template's eligible_authority text is absent or malformed.",
            )

        if binding.rollback_site != _expected_site_for(operation_context):
            return ValidatedEvidence(
                RollbackApprovalValidationResult.WRONG_SCOPE,
                False,
                binding,
                "Binding's rollback_site does not match the live operation context's site.",
            )

        if not _operation_matches(binding.rollback_operation_reference, operation_context):
            return ValidatedEvidence(
                RollbackApprovalValidationResult.WRONG_SCOPE,
                False,
                binding,
                "Binding's rollback_operation_reference does not exactly match the live "
                "operation context (RAE-REQ-024).",
            )

        if store.is_revoked(evidence_id):
            return ValidatedEvidence(
                RollbackApprovalValidationResult.REVOKED,
                False,
                binding,
                "This Binding has been revoked (RAE-REQ-046).",
            )

        if binding.use_binding is not None:
            return ValidatedEvidence(
                RollbackApprovalValidationResult.INVALID,
                False,
                binding,
                "This Binding has already transitioned to state=used and cannot be resolved again "
                "(RAE-REQ-050).",
            )

        now = _now_utc()
        created_at = _parse_iso_timestamp(binding.created_at)
        expires_at = _parse_iso_timestamp(binding.expires_at)
        if created_at is None or expires_at is None:
            return ValidatedEvidence(
                RollbackApprovalValidationResult.INVALID,
                False,
                binding,
                "created_at/expires_at failed to parse as a timezone-aware ISO-8601 timestamp.",
            )
        if created_at > now:
            return ValidatedEvidence(
                RollbackApprovalValidationResult.INVALID,
                False,
                binding,
                "Binding's created_at is in the future relative to validation time; rejected fail-closed.",
            )
        if now >= expires_at:
            return ValidatedEvidence(
                RollbackApprovalValidationResult.STALE,
                False,
                binding,
                "Binding's expires_at has passed (24-hour TTL, inclusive boundary, RAE-REQ-043).",
            )

        if binding.repository_state_binding != operation_context.repository_state:
            return ValidatedEvidence(
                RollbackApprovalValidationResult.STALE,
                False,
                binding,
                "Binding's repository_state_binding no longer matches the live operation context's "
                "repository state (RAE-REQ-033).",
            )

        if _is_superseded(binding, store):
            return ValidatedEvidence(
                RollbackApprovalValidationResult.SUPERSEDED,
                False,
                binding,
                "A later Binding referencing the same rollback_operation_reference supersedes this "
                "one (RAE-REQ-047).",
            )

        return ValidatedEvidence(RollbackApprovalValidationResult.VALID, True, binding, None)
    except Exception as exc:  # noqa: BLE001 - fail-closed umbrella, RAE-REQ-042
        return ValidatedEvidence(
            RollbackApprovalValidationResult.INVALID,
            False,
            None,
            f"Evidence Validator internal error (fail-closed, RAE-REQ-042): {exc}",
        )


def derive_rollback_approval_present(
    operation_context: RollbackApprovalContext,
    evidence_id: str,
    *,
    evidence_store: Optional[RollbackApprovalEvidenceStore] = None,
    publication_root: Optional[Path] = None,
) -> bool:
    """The narrow derivation API a future AG3/AG5 integration will call
    (RAE-001 §13; 149K plan §28). No caller-override parameter exists on
    this signature -- `True` only for `RollbackApprovalValidationResult.VALID`
    (which itself only occurs with `decision == APPROVE`); `False` for
    every other outcome, including any internal Evidence Validator error."""

    return resolve_rollback_approval_evidence(
        operation_context,
        evidence_id,
        evidence_store=evidence_store,
        publication_root=publication_root,
    ).approval_present


__all__ = [
    "RollbackApprovalError",
    "RollbackApprovalBindingConstructionError",
    "RollbackApprovalStorageError",
    "RollbackApprovalDecisionCreationError",
    "RollbackDecisionType",
    "BindingDecision",
    "RollbackSite",
    "BindingState",
    "RollbackApprovalValidationResult",
    "ROLLBACK_APPROVAL_TEMPLATE_ID",
    "ROLLBACK_APPROVAL_TEMPLATE_VERSION",
    "ROLLBACK_APPROVAL_TEMPLATE",
    "RollbackApprovalDecisionRef",
    "Ag3OperationReference",
    "Ag5OperationReference",
    "RepositoryStateBinding",
    "RevocationMetadata",
    "Ag3RollbackApprovalContext",
    "Ag5RollbackApprovalContext",
    "RollbackApprovalBinding",
    "ValidatedEvidence",
    "RollbackApprovalEvidenceStore",
    "create_rollback_approval_decision",
    "create_rollback_approval_binding",
    "revoke_rollback_approval_binding",
    "resolve_rollback_approval_evidence",
    "derive_rollback_approval_present",
]
