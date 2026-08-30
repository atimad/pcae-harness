"""
HPAC-001 v2.1 §41 — `RuntimeInvocationAuthorityConsumption` inert
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

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 (Runtime-Dispatch Contract
Normalization). The consumption record schema evolves to
``HPAC-AUTHORITY-CONSUMPTION/2.1``: one new closed top-level binding
object, ``authority_generation_binding``, durably commits the
V-15-1 authority-generation snapshot ``S1`` that Gate 9 verified
unchanged at ``S2`` immediately before the create-only linearization
(HPAC-001 v2.1 HPAC-REQ-098/099; RDGO-001 v3.1 §10). It is verification
evidence, not a bearer token: it grants no capability and Gate 10 MUST
re-read current canonical state and compare against it (RDGO-001 v3.1
§10; ``.1R.15.1`` §22). The eight prior closed binding objects and the
closed 12-field ``authority_binding`` are byte-unchanged; ``/2.0`` records
remain readable historical/test data but are Gate-10-ineligible (§18 of
the phase prompt).
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

#: Current canonical consumption-record schema identity (HPAC-001 v2.1
#: HPAC-REQ-098). Every record Gate 9 creates after `.1R.15.4` carries
#: this constant; it is a required, future-Gate-10-eligible record.
CONSUMPTION_SCHEMA_VERSION = "HPAC-AUTHORITY-CONSUMPTION/2.1"

#: The pre-`.1R.15.4` schema identity. `resolve` still parses a well-formed
#: `/2.0` record as historical/test data (its closed field set had no
#: `authority_generation_binding`), but such a record is NOT future-Gate-10
#: eligible — the durable authority-generation snapshot RDGO-001 v3.1 §10
#: requires is absent. Gate 9 never writes `/2.0` after `.1R.15.4`.
CONSUMPTION_SCHEMA_VERSION_LEGACY_2_0 = "HPAC-AUTHORITY-CONSUMPTION/2.0"

#: Schema identity of the durable authority-generation snapshot embedded in
#: `authority_generation_binding` (HPAC-001 v2.1 §41). A closed field set;
#: additive-only future evolution requires a new MINOR.
AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION = "HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0"

_TOP_ALLOWED_FIELDS = frozenset(
    {
        "consumption_schema_version",
        "record_digest",
        "request_identity",
        "repository_task_binding",
        "target_binding",
        "prompt_binding",
        "authority_binding",
        "authority_generation_binding",
        "pb_binding",
        "runtime_enforcement_binding",
        "dispatch_binding",
    }
)

#: The closed top-level field set of a pre-`.1R.15.4` `/2.0` record —
#: identical to `_TOP_ALLOWED_FIELDS` minus `authority_generation_binding`.
_TOP_ALLOWED_FIELDS_LEGACY_2_0 = _TOP_ALLOWED_FIELDS - {"authority_generation_binding"}

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
    # HPAC-001 v2.1 §41 (`.1R.15.4`, V-15-1 durable representation). Closed
    # 6-field snapshot of every mutable authority-generation source at the
    # Gate-9 linearization point. Each `*_generation` value is a non-empty
    # bounded canonical digest/marker string over durable state, restart-
    # reconstructible, carrying no wall-clock/nonce/process identity. This
    # object is data (verification evidence), never execution authority.
    "authority_generation_binding": frozenset(
        {
            "snapshot_schema_version",
            "principal_generation",
            "credential_generation",
            "approval_generation",
            "lifecycle_generation",
            "consumption_generation",
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
    #: Present (a closed 6-field dict) on every `/2.1` record; ``None`` only
    #: on a historical `/2.0` record parsed by `resolve` (Gate-10-ineligible).
    authority_generation_binding: Optional[dict] = None

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
        if self.authority_generation_binding is not None:
            doc["authority_generation_binding"] = self.authority_generation_binding
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
    authority_generation_binding: dict,
    pb_binding: dict,
    runtime_enforcement_binding: dict,
    dispatch_binding: dict,
) -> RuntimeInvocationAuthorityConsumption:
    """Constructs an inert (schema-only, non-authoritative)
    ``HPAC-AUTHORITY-CONSUMPTION/2.1`` record for test/fixture use. This
    function performs no gate-9 revalidation, consumes no real approval,
    and is not reachable from any dispatch code path -- it exists only so
    the store's create-only/duplicate/atomicity behavior can be proven
    against a structurally correct payload shape.

    ``authority_generation_binding`` (`.1R.15.4`) is the closed 6-field
    durable authority-generation snapshot; its ``snapshot_schema_version``
    MUST be ``AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION`` and each
    ``*_generation`` value a non-empty bounded string."""

    bindings = {
        "request_identity": request_identity,
        "repository_task_binding": repository_task_binding,
        "target_binding": target_binding,
        "prompt_binding": prompt_binding,
        "authority_binding": authority_binding,
        "authority_generation_binding": authority_generation_binding,
        "pb_binding": pb_binding,
        "runtime_enforcement_binding": runtime_enforcement_binding,
        "dispatch_binding": dispatch_binding,
    }
    for name, value in bindings.items():
        expected_fields = _BINDING_FIELD_SETS[name]
        if not isinstance(value, dict) or set(value.keys()) != expected_fields:
            raise HPACMalformedError(f"{name} has an incorrect closed field set; expected {sorted(expected_fields)}")
    _validate_authority_generation_binding(authority_generation_binding)
    body_without_digest = {"consumption_schema_version": CONSUMPTION_SCHEMA_VERSION, **bindings}
    digest = canonical_digest(body_without_digest)
    return RuntimeInvocationAuthorityConsumption(record_digest=digest, **body_without_digest)


def _validate_authority_generation_binding(binding: object) -> None:
    """Value-level checks on the durable authority-generation snapshot
    beyond the closed field set (HPAC-001 v2.1 §41): the schema-version
    constant, and each ``*_generation`` value a non-empty, bounded,
    stripped string. Never a bearer token — no capability field, no
    identity claim, purely digest/marker evidence."""

    if not isinstance(binding, dict):
        raise HPACMalformedError("authority_generation_binding is not an object")
    if set(binding.keys()) != _BINDING_FIELD_SETS["authority_generation_binding"]:
        raise HPACMalformedError(
            "authority_generation_binding has an incorrect closed field set; expected "
            f"{sorted(_BINDING_FIELD_SETS['authority_generation_binding'])}"
        )
    if binding.get("snapshot_schema_version") != AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION:
        raise HPACMalformedError(
            "authority_generation_binding.snapshot_schema_version must be "
            f"{AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION!r}"
        )
    for key in (
        "principal_generation",
        "credential_generation",
        "approval_generation",
        "lifecycle_generation",
        "consumption_generation",
    ):
        value = binding.get(key)
        if not isinstance(value, str) or not (1 <= len(value) <= 256) or value != value.strip():
            raise HPACMalformedError(
                f"authority_generation_binding.{key} must be a non-empty bounded stripped string"
            )


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
        # Version-aware closed top-level field set. `/2.1` (current) requires
        # `authority_generation_binding`; a well-formed `/2.0` record is
        # accepted as historical/test data without it (Gate-10-ineligible —
        # RDGO-001 v3.1 §10 / phase-prompt §18). Any other version, or a
        # field-set that matches neither, is durability-uncertain.
        schema_version = document.get("consumption_schema_version")
        if schema_version == CONSUMPTION_SCHEMA_VERSION:
            allowed = _TOP_ALLOWED_FIELDS
        elif schema_version == CONSUMPTION_SCHEMA_VERSION_LEGACY_2_0:
            allowed = _TOP_ALLOWED_FIELDS_LEGACY_2_0
        else:
            raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError(
                f"consumption record has an unknown schema version {schema_version!r}"
            )
        unknown = set(document.keys()) - allowed
        missing = allowed - set(document.keys())
        if unknown or missing:
            raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError(
                f"consumption record has incorrect fields (unknown={sorted(unknown)}, missing={sorted(missing)})"
            )
        stored_digest = document.get("record_digest")
        without_digest = {k: v for k, v in document.items() if k != "record_digest"}
        recomputed = canonical_digest(without_digest)
        if recomputed != stored_digest:
            raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError("stored record_digest does not match canonical bytes")
        # A `/2.0` record round-trips with `authority_generation_binding is
        # None` (Gate-10-ineligible: RDGO-001 v3.1 §10's durable snapshot is
        # absent). A `/2.1` record carries the closed 6-field object.
        if schema_version == CONSUMPTION_SCHEMA_VERSION:
            try:
                _validate_authority_generation_binding(without_digest.get("authority_generation_binding"))
            except HPACMalformedError as exc:
                raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError(str(exc)) from exc
        return RuntimeInvocationAuthorityConsumption(record_digest=stored_digest, **without_digest)
