"""
Runtime Invocation Approval Store — Phase 149O.20L.7O.3W.

Canonical, create-only, path-confined persistence for
`RuntimeInvocationApproval` documents (RIHAC-001 §15 / RIASC-001 §12):

    .pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json

This is a separate store from `RuntimeInvocationStore`
(`runtime_invocation.py`, the pre-existing mock-v1 dry-path store) --
RIHAC-001 §15 forbids embedding the approval in CHGR or the invocation
record, and 3S.2.1's MUST-FIX #2 (path traversal via an unsanitized
`invocation_id`) is repaired-by-design here, not inherited: `approval_id`
is validated against the exact `^ria-[0-9a-f]{32}$` pattern *before* any
path is constructed from it, and no other caller-supplied string is ever
used to build a path.

Reuses the existing atomic create-only write pattern
(`RuntimeInvocationStore._write_create_only`,
`runtime_invocation.py:850`): write to a `.tmp` sibling, then
`Path.replace()`. No `subprocess`, no network, no credential access.
"""

from __future__ import annotations

import json
from pathlib import Path

from .runtime_authority import (
    AdapterBinding,
    ApprovalProvenance,
    ApprovalScope,
    ApprovalSubject,
    ArtifactRef,
    FreshnessSnapshot,
    GovernanceContext,
    RuntimeInvocationApproval,
    is_valid_approval_id,
    validate_riasc_schema_shape,
)

STORE_ROOT = Path(".pcae") / "runtime-invocation-approvals" / "v1"


class ApprovalStoreIntegrityError(Exception):
    """Raised for any conflicting, corrupt, or malformed persisted
    approval, or for any caller-supplied identifier that fails path
    confinement. Callers must treat this as fail-closed: never auto-repair,
    never treat a partially-valid load as authority."""


class RuntimeInvocationApprovalStore:
    """Canonical approval store. Lookup is by `approval_id` only, resolved
    to the fixed canonical path -- never a caller-supplied arbitrary path
    (RIHAC-001 §15)."""

    def __init__(self, root: Path):
        self._root = Path(root) / STORE_ROOT

    def _approval_dir(self, approval_id: str) -> Path:
        if not is_valid_approval_id(approval_id):
            raise ApprovalStoreIntegrityError(f"invalid_approval_id_pattern:{approval_id!r}")
        # `approval_id` is now proven to match `^ria-[0-9a-f]{32}$`: no
        # path separator, no "..", no leading "/" is representable by that
        # pattern, so confinement holds by construction, not by string
        # post-processing.
        return self._root / approval_id

    def _approval_path(self, approval_id: str) -> Path:
        return self._approval_dir(approval_id) / "approval.json"

    def create(self, approval: RuntimeInvocationApproval) -> None:
        """Create-only write. A second write to the same `approval_id` is
        always a hard integrity failure -- never a silent overwrite and
        never an idempotent no-op, even with byte-identical content
        (RIHAC-001 §1: approvals are immutable one-shot human acts, not
        replayable requests; RIASC-001 §9 has no mutable `consumed` field
        to make "same content" a meaningful resume signal)."""
        path = self._approval_path(approval.approval_id)
        if path.exists():
            raise ApprovalStoreIntegrityError(f"approval_already_exists:{approval.approval_id}")
        document = approval.to_dict()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(path)

    def load(self, approval_id: str) -> RuntimeInvocationApproval | None:
        """Load and structurally validate exactly one canonical artifact.
        Returns `None` if no artifact exists. Raises
        `ApprovalStoreIntegrityError` for any malformed, truncated,
        schema-invalid, or mismatched-identity artifact -- never a silent
        fallback and never partial trust (RIHAC-001 §15/§18)."""
        path = self._approval_path(approval_id)
        if not path.exists():
            return None
        try:
            raw_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ApprovalStoreIntegrityError(f"approval_unreadable:{approval_id}") from exc
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ApprovalStoreIntegrityError(f"approval_malformed_json:{approval_id}") from exc

        issues = validate_riasc_schema_shape(data)
        if issues:
            raise ApprovalStoreIntegrityError(
                f"approval_schema_invalid:{approval_id}:{','.join(issues)}"
            )
        if data.get("approval_id") != approval_id:
            raise ApprovalStoreIntegrityError(
                f"approval_identity_mismatch:{approval_id}!={data.get('approval_id')}"
            )

        return _approval_from_dict(data)

    def exists(self, approval_id: str) -> bool:
        return self._approval_path(approval_id).exists()


def _approval_from_dict(data: dict) -> RuntimeInvocationApproval:
    subject = data["subject"]
    gov = data["governance_context"]
    scope = data["approval_scope"]
    adapter = data["adapter_binding"]
    freshness = data["freshness_snapshot"]
    provenance = data["provenance"]
    return RuntimeInvocationApproval(
        approval_id=data["approval_id"],
        record_digest=data["record_digest"],
        created_at=data["created_at"],
        expires_at=data["expires_at"],
        subject=ApprovalSubject(**subject),
        governance_context=GovernanceContext(
            phase_id=gov["phase_id"], session_id=gov.get("session_id")
        ),
        approval_scope=ApprovalScope(
            requested_capability=scope["requested_capability"],
            filesystem_scope_ref=ArtifactRef(**scope["filesystem_scope_ref"]),
            process_profile_ref=ArtifactRef(**scope["process_profile_ref"]),
            transport_type=scope["transport_type"],
            effect_class=scope["effect_class"],
            dispatch_limit=scope["dispatch_limit"],
            network_required=scope["network_required"],
        ),
        adapter_binding=AdapterBinding(**adapter),
        freshness_snapshot=FreshnessSnapshot(
            head_commit=freshness["head_commit"],
            task_contract_digest=freshness["task_contract_digest"],
            policy_version=freshness["policy_version"],
            task_state=freshness["task_state"],
        ),
        provenance=ApprovalProvenance(**provenance),
        schema_id=data["schema_id"],
        schema_version=data["schema_version"],
        contract_version=data["contract_version"],
        record_type=data["record_type"],
        prompt_hash_profile=data["prompt_hash_profile"],
        attempt_limit=data["attempt_limit"],
    )
