"""Deterministic, fail-closed CHGR artifact verification (Phase 143E).

Implements the business logic behind ``pcae governance-record verify
<path> [--related PATH ...]``. Re-parses independently of
:mod:`pcae.governance.inspection` (no shared mutable state) and performs
the checks that apply without a live storage/registry: schema validity,
digest self-consistency, confirmation-content binding, provenance/
integrity cross-checks against caller-supplied related artifacts,
lifecycle-state structural legality, and assurance-level truthfulness.

Verification never determines substantive policy (it does not decide "was
this the right decision") and never invents authority: a structurally
perfect record with an ineligible confirmer still verifies as
*structurally valid*; whether it was *authoritative* is outside this
module's job. A check that cannot be performed because a related artifact
was not supplied is explicitly reported as skipped, never silently treated
as passed.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any, Union

from pcae.schema_resources import chgr_root
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
    SchemaRegistryError,
    build_offline_registry,
    load_and_verify_manifest,
    parse_strict_json,
    validate_record_shape,
)

CONSUMER_ID = "pcae-governance-record-verify-v1"
CHGR_CONTRACT_VERSION = "CHGR-001/1.0"
_MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/chgr/manifest.schema.json"
_UNAVAILABLE = "unavailable"

_ASSURANCE_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
# Only L0/L1 have an implemented confirmer_identity_evidence shape this
# increment; L2+ is structurally acceptable (open extension point) but
# never actually achievable by any evidence shape this package implements.
_MAX_IMPLEMENTED_ASSURANCE = "L1"

_ERROR_CODES = frozenset(
    {
        "SCHEMA_INVALID",
        "DIGEST_MISMATCH",
        "PROVENANCE_INCOMPLETE",
        "CONFIRMATION_UNBOUND",
        "LIFECYCLE_INCONSISTENT",
        "ASSURANCE_OVERCLAIM",
        "TEMPLATE_UNRESOLVABLE",
        "PHASE_REPORT_SUBSTITUTION",
        "UNREGISTERED_SCHEMA",
    }
)

_KNOWN_RECORD_TYPES = frozenset(
    {
        "decision_template",
        "human_governance_record",
        "human_confirmation_evidence",
        "governance_record_provenance",
        "governance_record_integrity",
        "governance_record_lifecycle_event",
    }
)

_DISCLOSURE = (
    "Successful verification means only that this artifact, and any "
    "related artifacts supplied alongside it, are structurally consistent "
    "and internally coherent. It never means the represented governance "
    "act was valid, applicable, current, or performed by an authorized "
    "human -- that determination requires the applicable governing "
    "authority model, which this module does not resolve."
)


class VerificationError(Exception):
    """Raised only for genuine misuse of this module's own API."""


@dataclasses.dataclass(frozen=True)
class CheckResult:
    name: str
    status: str  # "passed" | "failed" | "skipped"
    detail: str = ""


@dataclasses.dataclass(frozen=True)
class VerificationObservation:
    source_artifact_identity: str
    input_digest: str
    record_family: str
    record_identity: str
    checks: tuple[CheckResult, ...]
    disclosure: str = _DISCLOSURE
    consumer_identity: str = CONSUMER_ID
    chgr_contract_version: str = CHGR_CONTRACT_VERSION
    outcome: str = "verified"

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "consumer_identity": self.consumer_identity,
            "chgr_contract_version": self.chgr_contract_version,
            "source_artifact_identity": self.source_artifact_identity,
            "input_digest": self.input_digest,
            "record_family": self.record_family,
            "record_identity": self.record_identity,
            "checks": [dataclasses.asdict(c) for c in self.checks],
            "disclosure": self.disclosure,
        }


@dataclasses.dataclass(frozen=True)
class VerificationFailure:
    error_code: str
    message: str
    source_artifact_identity: str
    input_digest: str
    record_family: str = _UNAVAILABLE
    record_identity: str = _UNAVAILABLE
    checks: tuple[CheckResult, ...] = ()
    disclosure: str = _DISCLOSURE
    consumer_identity: str = CONSUMER_ID
    chgr_contract_version: str = CHGR_CONTRACT_VERSION
    outcome: str = "rejected"

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "error_code": self.error_code,
            "message": self.message,
            "consumer_identity": self.consumer_identity,
            "chgr_contract_version": self.chgr_contract_version,
            "source_artifact_identity": self.source_artifact_identity,
            "input_digest": self.input_digest,
            "record_family": self.record_family,
            "record_identity": self.record_identity,
            "checks": [dataclasses.asdict(c) for c in self.checks],
            "disclosure": self.disclosure,
        }


VerificationOutcome = Union[VerificationObservation, VerificationFailure]


def _safe_text(value: object) -> str:
    return value if type(value) is str and value else _UNAVAILABLE


def _canonical_bytes(doc: dict[str, Any]) -> bytes:
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _record_digest_of(doc: dict[str, Any]) -> str:
    stripped = {k: v for k, v in doc.items() if k != "record_digest"}
    return hashlib.sha256(_canonical_bytes(stripped)).hexdigest()


def _fail(
    error_code: str,
    message: str,
    *,
    source_artifact_identity: str,
    input_digest: str,
    record: dict[str, Any] | None = None,
    checks: tuple[CheckResult, ...] = (),
) -> VerificationFailure:
    if error_code not in _ERROR_CODES:
        raise VerificationError(f"Unknown verification error_code: {error_code}")
    record = record or {}
    return VerificationFailure(
        error_code=error_code,
        message=message,
        source_artifact_identity=source_artifact_identity,
        input_digest=input_digest,
        record_family=_safe_text(record.get("record_type")),
        record_identity=_safe_text(record.get("record_id")),
        checks=checks,
    )


def _parse(raw: bytes) -> dict[str, Any] | None:
    parsed = parse_strict_json(raw, require_top_level_object=True)
    if parsed.status is not OutcomeStatus.VALID or type(parsed.value) is not dict:
        return None
    return parsed.value


def _load_registry_and_manifest():
    with chgr_root() as package_root:
        registry = build_offline_registry(package_root)
        manifest = load_and_verify_manifest(
            package_root / "manifest.json",
            package_root=package_root,
            registry=registry,
            manifest_schema_id=_MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
        return registry, manifest


def _shape_check(record: dict[str, Any], *, registry, manifest) -> tuple[bool, str]:
    family = record.get("record_type")
    if type(family) is not str or family not in _KNOWN_RECORD_TYPES:
        return False, "unknown_record_family"
    entries = [
        e
        for e in manifest.document["entries"]
        if e.get("family") == family and e.get("file_path", "").startswith("records/")
    ]
    if len(entries) != 1:
        return False, "manifest_entry_missing"
    schema_id = record.get("schema_id")
    if schema_id != entries[0].get("schema_id"):
        return False, "family_identity_mismatch"
    if record.get("schema_version") != entries[0].get("schema_version"):
        return False, "unsupported_schema_version"
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    if result.status is not OutcomeStatus.VALID:
        return False, "shape_invalid"
    return True, ""


def verify_artifact_at_path(
    path: Path,
    *,
    artifact_bytes: bytes,
    related_bytes: tuple[bytes, ...] = (),
) -> VerificationOutcome:
    """Verify one caller-supplied CHGR artifact, optionally cross-checked
    against explicitly supplied related artifacts (e.g. its confirmation
    evidence, provenance, integrity, or governing template).

    Performs no filesystem I/O beyond the package-owned CHGR schema
    resource resolution, no mutation, and no network access. Deterministic:
    identical inputs always produce an identical outcome.
    """
    source_artifact_identity = str(path)
    input_digest = hashlib.sha256(artifact_bytes).hexdigest()

    record = _parse(artifact_bytes)
    if record is None:
        return _fail(
            "SCHEMA_INVALID",
            "The supplied artifact is not a strict JSON object.",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
        )

    if "schema_id" not in record or "record_type" not in record:
        return _fail(
            "PHASE_REPORT_SUBSTITUTION",
            "The supplied artifact carries no CHGR envelope; it cannot be a CHGR of any kind "
            "(this also rejects a canonical phase-completion report presented as a CHGR).",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record=record,
        )

    related_records: list[dict[str, Any]] = []
    for blob in related_bytes:
        parsed = _parse(blob)
        if parsed is not None and "schema_id" in parsed and "record_type" in parsed:
            related_records.append(parsed)

    try:
        registry, manifest = _load_registry_and_manifest()
    except (OSError, SchemaRegistryError, ManifestIntegrityError, ValueError):
        return _fail(
            "UNREGISTERED_SCHEMA",
            "The installed CHGR schema registry or manifest could not be built/verified.",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record=record,
        )

    checks: list[CheckResult] = []

    ok, reason = _shape_check(record, registry=registry, manifest=manifest)
    if not ok:
        code = "UNREGISTERED_SCHEMA" if reason in ("unknown_record_family", "manifest_entry_missing", "family_identity_mismatch") else "SCHEMA_INVALID"
        return _fail(
            code,
            f"Primary artifact failed schema-level verification ({reason}).",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record=record,
        )
    checks.append(CheckResult("schema_shape", "passed"))

    declared_digest = record.get("record_digest")
    family = record["record_type"]
    # A human_governance_record's own record_digest is over the FULL final
    # payload (including its outbound sibling refs); confirmable_content_digest
    # (used below) is over the pre-ref-attachment content a confirmation
    # actually bound to. Both are independently verifiable.
    full_recomputed = _record_digest_of(record)
    if declared_digest != full_recomputed:
        return _fail(
            "DIGEST_MISMATCH",
            "The artifact's declared record_digest does not match its own recomputed content digest "
            "-- this artifact was altered after its digest was computed.",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record=record,
            checks=tuple(checks),
        )
    checks.append(CheckResult("digest_self_consistency", "passed"))

    if family != "human_governance_record":
        return VerificationObservation(
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record_family=family,
            record_identity=_safe_text(record.get("record_id")),
            checks=tuple(checks),
        )

    # From here on: human_governance_record-specific cross-artifact checks.
    lifecycle_state = record.get("lifecycle_state")
    if lifecycle_state == "suspended" and "suspension_ref" not in record:
        return _fail(
            "LIFECYCLE_INCONSISTENT",
            "lifecycle_state is 'suspended' but no suspension_ref evidence is present.",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record=record,
            checks=tuple(checks),
        )
    if lifecycle_state == "revoked" and "revocation_ref" not in record:
        return _fail(
            "LIFECYCLE_INCONSISTENT",
            "lifecycle_state is 'revoked' but no revocation_ref evidence is present.",
            source_artifact_identity=source_artifact_identity,
            input_digest=input_digest,
            record=record,
            checks=tuple(checks),
        )
    checks.append(CheckResult("lifecycle_structural_legality", "passed"))

    def _find_related(family_name: str, ref: dict[str, Any] | None) -> dict[str, Any] | None:
        if ref is None:
            return None
        for candidate in related_records:
            if candidate.get("record_type") == family_name and candidate.get("record_id") == ref.get("record_id"):
                return candidate
        return None

    confirmation = _find_related("human_confirmation_evidence", record.get("confirmation_evidence_ref"))
    if confirmation is None:
        checks.append(CheckResult("confirmation_binding", "skipped", "no matching related confirmation evidence supplied"))
    else:
        ok, _ = _shape_check(confirmation, registry=registry, manifest=manifest)
        if not ok or _record_digest_of(confirmation) != confirmation.get("record_digest"):
            return _fail(
                "DIGEST_MISMATCH",
                "The related confirmation evidence artifact is malformed or was altered after its digest was computed.",
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record=record,
                checks=tuple(checks),
            )
        if confirmation.get("confirmed_content_digest") != confirmation.get("preview_rendering_digest"):
            return _fail(
                "CONFIRMATION_UNBOUND",
                "The confirmation evidence's confirmed_content_digest does not match its own "
                "preview_rendering_digest -- both are required (CHGR-REQ-201) to be populated from "
                "the same upstream confirmed-preview content, so a mismatch means this evidence does "
                "not bind to a single, coherent preview.",
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record=record,
                checks=tuple(checks),
            )
        checks.append(CheckResult("confirmation_binding", "passed"))

        record_level = _ASSURANCE_ORDER.get(record.get("assurance_level"), 99)
        achieved_level = _ASSURANCE_ORDER.get(confirmation.get("achieved_assurance_level"), -1)
        max_implemented = _ASSURANCE_ORDER[_MAX_IMPLEMENTED_ASSURANCE]
        if record_level > achieved_level or record_level > max_implemented:
            return _fail(
                "ASSURANCE_OVERCLAIM",
                "The record's declared assurance_level exceeds what the confirmation evidence shape "
                "actually supports (or exceeds the highest level any evidence shape implements this increment).",
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record=record,
                checks=tuple(checks),
            )
        checks.append(CheckResult("assurance_truthfulness", "passed"))

    provenance = _find_related("governance_record_provenance", record.get("provenance_ref"))
    if provenance is None:
        checks.append(CheckResult("provenance_consistency", "skipped", "no matching related provenance supplied"))
    else:
        ok, _ = _shape_check(provenance, registry=registry, manifest=manifest)
        if not ok or _record_digest_of(provenance) != provenance.get("record_digest"):
            return _fail(
                "DIGEST_MISMATCH",
                "The related provenance artifact is malformed or was altered after its digest was computed.",
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record=record,
                checks=tuple(checks),
            )
        if provenance.get("selected_option_id") != record.get("selected_option_id"):
            return _fail(
                "PROVENANCE_INCOMPLETE",
                "The related provenance artifact's own claims do not agree with this record's actual content.",
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record=record,
                checks=tuple(checks),
            )
        if confirmation is not None and provenance.get("preview_content_digest") != confirmation.get(
            "confirmed_content_digest"
        ):
            return _fail(
                "PROVENANCE_INCOMPLETE",
                "The related provenance artifact's preview_content_digest does not match the related "
                "confirmation evidence's confirmed_content_digest -- both are required (CHGR-REQ-201) "
                "to be populated from the same upstream confirmed-preview content.",
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record=record,
                checks=tuple(checks),
            )
        checks.append(CheckResult("provenance_consistency", "passed"))

    integrity = _find_related("governance_record_integrity", record.get("integrity_ref"))
    if integrity is None:
        checks.append(CheckResult("integrity_consistency", "skipped", "no matching related integrity evidence supplied"))
    else:
        ok, _ = _shape_check(integrity, registry=registry, manifest=manifest)
        if not ok or _record_digest_of(integrity) != integrity.get("record_digest"):
            return _fail(
                "DIGEST_MISMATCH",
                "The related integrity artifact is malformed or was altered after its digest was computed.",
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record=record,
                checks=tuple(checks),
            )
        if integrity.get("payload_digest") != declared_digest:
            return _fail(
                "DIGEST_MISMATCH",
                "The related integrity artifact's payload_digest does not match this record's own "
                "record_digest -- the published content was altered after integrity evidence was computed.",
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record=record,
                checks=tuple(checks),
            )
        checks.append(CheckResult("integrity_consistency", "passed"))

    template = None
    template_ref = record.get("template_ref")
    if isinstance(template_ref, dict):
        for candidate in related_records:
            if (
                candidate.get("record_type") == "decision_template"
                and candidate.get("template_id") == template_ref.get("template_id")
                and candidate.get("version") == template_ref.get("version")
            ):
                template = candidate
                break
    if template is None:
        checks.append(CheckResult("template_resolution", "skipped", "no matching related template supplied"))
    else:
        ok, _ = _shape_check(template, registry=registry, manifest=manifest)
        option_ids = {opt.get("option_id") for opt in template.get("options", []) if isinstance(opt, dict)}
        if not ok or record.get("selected_option_id") not in option_ids:
            return _fail(
                "TEMPLATE_UNRESOLVABLE",
                "The referenced template does not resolve to a valid basis for this record's selected_option_id.",
                source_artifact_identity=source_artifact_identity,
                input_digest=input_digest,
                record=record,
                checks=tuple(checks),
            )
        checks.append(CheckResult("template_resolution", "passed"))

    return VerificationObservation(
        source_artifact_identity=source_artifact_identity,
        input_digest=input_digest,
        record_family=family,
        record_identity=_safe_text(record.get("record_id")),
        checks=tuple(checks),
    )


__all__ = [
    "CONSUMER_ID",
    "CHGR_CONTRACT_VERSION",
    "CheckResult",
    "VerificationError",
    "VerificationFailure",
    "VerificationObservation",
    "VerificationOutcome",
    "verify_artifact_at_path",
]
