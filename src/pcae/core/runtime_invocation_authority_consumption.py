"""
HPAC-001 v2.0 §41 — `RuntimeInvocationAuthorityConsumption` inert
model/store primitives (Gate-9).

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 (Layer 1-2 foundation). Implements
ONLY the record schema (HPAC-REQ-098) and a create-only, atomic,
duplicate-detecting store (HPAC-REQ-099/100). There is NO RDGO-001 gate
wiring here, no gate-9 caller, and no consumption of any real approval,
presentation, challenge, or proof -- this module is reachable only by
test code constructing its own inert records. A future phase (not this
one) wires an actual Gate 9 caller that populates and creates these
records as part of real dispatch; that wiring is explicitly out of this
phase's scope (phase instruction §31/§32).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACDuplicateError,
    HPACMalformedError,
    canonical_digest,
    read_canonical_json_document,
    reject_symlink,
    require_safe_relative_id_component,
    write_atomic_create_only,
)

CONSUMPTION_SCHEMA_VERSION = "HPAC-AUTHORITY-CONSUMPTION/2.0"

_TOP_ALLOWED_FIELDS = frozenset(
    {
        "consumption_schema_version",
        "record_digest",
        "request_identity",
        "repository_task_binding",
        "target_binding",
        "prompt_binding",
        "authority_binding",
        "pb_binding",
        "runtime_enforcement_binding",
        "dispatch_binding",
    }
)

_BINDING_FIELD_SETS: dict[str, frozenset[str]] = {
    "request_identity": frozenset({"invocation_id", "attempt_id", "idempotency_key"}),
    "repository_task_binding": frozenset(
        {"repository_identity", "head_commit", "task_id", "task_contract_digest", "phase_id", "session_id"}
    ),
    "target_binding": frozenset(
        {"runtime_target_id", "adapter_id", "descriptor_version", "descriptor_digest", "target_config_digest", "executable_identity_digest"}
    ),
    "prompt_binding": frozenset({"prompt_hash", "prompt_hash_profile"}),
    "authority_binding": frozenset(
        {
            "approval_id",
            "approval_digest",
            "authority_projection_id",
            "authority_projection_digest",
            "authority_contract_version",
            "proof_id",
            "proof_digest",
            "proof_validation_digest",
            "registry_state_digest",
            "approval_subject_digest",
            "trusted_presentation_ref",
            "challenge_digest",
        }
    ),
    "pb_binding": frozenset({"request_digest", "decision_digest", "decision", "policy_version", "causing_policy_ids", "matched_no_go_ids"}),
    "runtime_enforcement_binding": frozenset({"decision_id", "decision_digest", "verdict", "expires_at", "evaluated_input_digest"}),
    "dispatch_binding": frozenset({"containment_evidence_ref", "state", "consumed_at"}),
}


class RuntimeInvocationAuthorityConsumptionError(Exception):
    """Base error for consumption-record operations."""


class RuntimeInvocationAuthorityConsumptionDurabilityUncertainError(RuntimeInvocationAuthorityConsumptionError):
    """A partial/corrupt consumption record was found. Per
    HPAC-REQ-100/HPAC-REQ-023 (crash safety table), this is treated as
    durability-uncertain -- never as either consumed or unconsumed."""


@dataclass(frozen=True)
class RuntimeInvocationAuthorityConsumption:
    consumption_schema_version: str
    record_digest: str
    request_identity: dict
    repository_task_binding: dict
    target_binding: dict
    prompt_binding: dict
    authority_binding: dict
    pb_binding: dict
    runtime_enforcement_binding: dict
    dispatch_binding: dict

    def to_document(self, *, include_digest: bool) -> dict:
        doc = {
            "consumption_schema_version": self.consumption_schema_version,
            "request_identity": self.request_identity,
            "repository_task_binding": self.repository_task_binding,
            "target_binding": self.target_binding,
            "prompt_binding": self.prompt_binding,
            "authority_binding": self.authority_binding,
            "pb_binding": self.pb_binding,
            "runtime_enforcement_binding": self.runtime_enforcement_binding,
            "dispatch_binding": self.dispatch_binding,
        }
        if include_digest:
            doc["record_digest"] = self.record_digest
        return doc


def new_inert_consumption_record(
    *,
    request_identity: dict,
    repository_task_binding: dict,
    target_binding: dict,
    prompt_binding: dict,
    authority_binding: dict,
    pb_binding: dict,
    runtime_enforcement_binding: dict,
    dispatch_binding: dict,
) -> RuntimeInvocationAuthorityConsumption:
    """Constructs an inert (schema-only, non-authoritative) record for
    test/fixture use. This function performs no gate-9 revalidation,
    consumes no real approval, and is not reachable from any dispatch
    code path -- it exists only so Phase 1 can prove the store's
    create-only/duplicate/atomicity behavior against a structurally
    correct payload shape."""

    bindings = {
        "request_identity": request_identity,
        "repository_task_binding": repository_task_binding,
        "target_binding": target_binding,
        "prompt_binding": prompt_binding,
        "authority_binding": authority_binding,
        "pb_binding": pb_binding,
        "runtime_enforcement_binding": runtime_enforcement_binding,
        "dispatch_binding": dispatch_binding,
    }
    for name, value in bindings.items():
        expected_fields = _BINDING_FIELD_SETS[name]
        if not isinstance(value, dict) or set(value.keys()) != expected_fields:
            raise HPACMalformedError(f"{name} has an incorrect closed field set; expected {sorted(expected_fields)}")
    body_without_digest = {"consumption_schema_version": CONSUMPTION_SCHEMA_VERSION, **bindings}
    digest = canonical_digest(body_without_digest)
    return RuntimeInvocationAuthorityConsumption(record_digest=digest, **body_without_digest)


class RuntimeInvocationAuthorityConsumptionStore:
    """`<root>/proofs/v2/<proof_id>/consumption.json` (HPAC-REQ-098).
    Single, atomic, create-only commit; duplicate creation attempts
    raise `HPACDuplicateError` rather than overwriting (HPAC-REQ-100)."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def _path(self, proof_id: str) -> Path:
        safe_proof_id = require_safe_relative_id_component(proof_id, context="proof_id")
        return self._root / "proofs" / "v2" / safe_proof_id / "consumption.json"

    def create(self, proof_id: str, record: RuntimeInvocationAuthorityConsumption) -> RuntimeInvocationAuthorityConsumption:
        reject_symlink(self._root)
        body_without_digest = record.to_document(include_digest=False)
        recomputed = canonical_digest(body_without_digest)
        if recomputed != record.record_digest:
            raise RuntimeInvocationAuthorityConsumptionError("record_digest does not match canonical record bytes")
        payload_document = record.to_document(include_digest=True)
        import json

        payload = json.dumps(payload_document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        write_atomic_create_only(self._path(proof_id), payload)
        return record

    def resolve(self, proof_id: str) -> Optional[RuntimeInvocationAuthorityConsumption]:
        """Returns `None` only when the record is genuinely absent
        (not consumed). Raises
        `RuntimeInvocationAuthorityConsumptionDurabilityUncertainError` on
        any corruption/partial-write signal -- callers MUST NOT treat
        that exception as either consumed or unconsumed (HPAC-REQ-100's
        crash-safety table)."""

        path = self._path(proof_id)
        try:
            reject_symlink(path)
        except Exception as exc:  # HPACSymlinkError
            raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError(str(exc)) from exc
        if not path.exists():
            return None
        try:
            document = read_canonical_json_document(path)
        except Exception as exc:
            raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError(str(exc)) from exc
        if not isinstance(document, dict):
            raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError("consumption record is not an object")
        unknown = set(document.keys()) - _TOP_ALLOWED_FIELDS
        missing = _TOP_ALLOWED_FIELDS - set(document.keys())
        if unknown or missing:
            raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError(
                f"consumption record has incorrect fields (unknown={sorted(unknown)}, missing={sorted(missing)})"
            )
        stored_digest = document.get("record_digest")
        without_digest = {k: v for k, v in document.items() if k != "record_digest"}
        recomputed = canonical_digest(without_digest)
        if recomputed != stored_digest:
            raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError("stored record_digest does not match canonical bytes")
        return RuntimeInvocationAuthorityConsumption(record_digest=stored_digest, **without_digest)
