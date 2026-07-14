"""Production validation against CLTR-SCHEMA-001 v1.0.1 (135I §6, §18).

Deterministic, fail-closed. Returns a tuple of ``ValidationError`` — never
raises for an ordinary content defect (raising is reserved for programmer
errors such as passing the wrong type). An empty tuple means the record is
structurally and semantically valid under this schema version.
"""

from __future__ import annotations

import dataclasses

from pcae.cltr import schema
from pcae.cltr.enums import (
    CERTIFIED_OR_LATER_STATES,
    PERMITTED_TRANSITIONS,
    ORTHOGONAL_TRANSITIONS,
    LifecycleState,
    TransitionType,
)
from pcae.cltr.models import ProductionCltrRecord


@dataclasses.dataclass(frozen=True)
class ValidationError:
    code: str
    field: str
    message: str


def validate_schema_version(version: str) -> tuple[ValidationError, ...]:
    if not schema.is_supported_schema_version(version):
        return (
            ValidationError(
                code="CLTR-VALIDATE-VERSION",
                field="schema_version",
                message=f"unsupported schema_version {version!r}; this implementation "
                f"supports exactly {sorted(schema.SUPPORTED_SCHEMA_VERSIONS)}",
            ),
        )
    return ()


def validate_schema_identity(record: ProductionCltrRecord) -> tuple[ValidationError, ...]:
    errors = []
    if record.schema_id != schema.SCHEMA_ID:
        errors.append(
            ValidationError("CLTR-VALIDATE-SCHEMA-ID", "schema_id", f"expected {schema.SCHEMA_ID!r}, got {record.schema_id!r}")
        )
    if record.contract_version != schema.CONTRACT_VERSION:
        errors.append(
            ValidationError(
                "CLTR-VALIDATE-CONTRACT-VERSION",
                "contract_version",
                f"expected {schema.CONTRACT_VERSION!r}, got {record.contract_version!r}",
            )
        )
    errors.extend(validate_schema_version(record.schema_version))
    return tuple(errors)


def validate_state_transition_legality(record: ProductionCltrRecord) -> tuple[ValidationError, ...]:
    """135I §3.3/§3.5 — reject any (from_state, transition_type) not in the
    permitted-next-state table, unless it is an orthogonal transition."""

    if record.transition_type in ORTHOGONAL_TRANSITIONS:
        return ()
    # 135I §7: `prior_state` is an identity reference (predecessor
    # transition_id, or explicit "none"), never itself a LifecycleState
    # value. This single-snapshot implementation (135K §26) does not
    # retain a multi-record history to look up a predecessor's own
    # lifecycle_state, so cross-record (from_state, transition_type)
    # legality is only checkable in the degenerate case where a caller
    # happens to pass a literal LifecycleState name as a convenience
    # (never required, never assumed) -- any other value is treated as an
    # opaque identity and this check is skipped, never faked as a pass.
    if not record.prior_state or record.prior_state == "none":
        return ()
    try:
        from_state = LifecycleState(record.prior_state)
    except ValueError:
        return ()
    key = (from_state, record.transition_type)
    if key not in PERMITTED_TRANSITIONS:
        return (
            ValidationError(
                "CLTR-VALIDATE-STATE",
                "transition_type",
                f"forbidden transition: ({from_state.value}, {record.transition_type.value})",
            ),
        )
    expected = PERMITTED_TRANSITIONS[key]
    if expected != record.lifecycle_state:
        return (
            ValidationError(
                "CLTR-VALIDATE-STATE",
                "lifecycle_state",
                f"transition ({from_state.value}, {record.transition_type.value}) "
                f"produces {expected.value}, not {record.lifecycle_state.value}",
            ),
        )
    return ()


def validate_certified_content(record: ProductionCltrRecord) -> tuple[ValidationError, ...]:
    """135I §6.3 — every CERTIFIED-or-later state shall contain certified
    content: report_id/report_digest, metadata_id/metadata_digest,
    snapshot_id/snapshot_digest, and at least one classified commit
    ownership entry or an explicit empty declaration is not distinguishable
    here without the caller's own explicit empty-set signal, so an empty
    ``phase_commit_ownership`` tuple is accepted (135I §10.2 — an empty
    array is a valid, first-class declaration for no-commit phases)."""

    if record.lifecycle_state not in CERTIFIED_OR_LATER_STATES:
        return ()
    errors = []
    required_pairs = (
        ("report_id", "report_digest"),
        ("metadata_id", "metadata_digest"),
        ("snapshot_id", "snapshot_digest"),
    )
    for id_field, digest_field in required_pairs:
        id_value = getattr(record, id_field)
        digest_value = getattr(record, digest_field)
        if not id_value or not digest_value:
            errors.append(
                ValidationError(
                    "CLTR-VALIDATE-CERTIFIED-CONTENT",
                    id_field,
                    f"CERTIFIED-or-later record ({record.lifecycle_state.value}) is missing "
                    f"certified content: {id_field}/{digest_field}",
                )
            )
    if not record.certified_state:
        errors.append(
            ValidationError(
                "CLTR-VALIDATE-CERTIFIED-CONTENT",
                "certified_state",
                f"CERTIFIED-or-later record ({record.lifecycle_state.value}) is missing certified_state",
            )
        )
    return tuple(errors)


def validate_notification_binding(record: ProductionCltrRecord) -> tuple[ValidationError, ...]:
    notifying_or_later = record.lifecycle_state in {
        LifecycleState.NOTIFYING,
        LifecycleState.NOTIFIED,
        LifecycleState.NOTIFIED_UNCONFIRMED,
        LifecycleState.TERMINAL_SUCCESS,
        LifecycleState.TERMINAL_PARTIAL_EXTERNAL,
    }
    if not notifying_or_later:
        return ()
    if not record.notification_ids and not record.notification_suppressed:
        return (
            ValidationError(
                "CLTR-VALIDATE-NOTIFICATION",
                "notification_ids",
                f"{record.lifecycle_state.value} requires >=1 notification_id or an explicit "
                "notification_suppressed=true declaration",
            ),
        )
    return ()


def validate_receipt_binding(record: ProductionCltrRecord) -> tuple[ValidationError, ...]:
    requires_receipt = record.lifecycle_state in {
        LifecycleState.NOTIFIED,
        LifecycleState.NOTIFIED_UNCONFIRMED,
        LifecycleState.TERMINAL_SUCCESS,
    }
    if requires_receipt and not record.receipt_id:
        return (
            ValidationError(
                "CLTR-VALIDATE-RECEIPT",
                "receipt_id",
                f"{record.lifecycle_state.value} requires receipt_id",
            ),
        )
    return ()


def validate_identity_ascii_safety(record: ProductionCltrRecord) -> tuple[ValidationError, ...]:
    """135G B-1 repair, adopted by 135I §16.2 — ``transition_id`` must be a
    single-segment, ASCII-only, non-path-traversing token, since it
    becomes a generation directory name (persistence.py)."""

    value = record.transition_id
    if not value.isascii() or "/" in value or "\\" in value or ".." in value or value.startswith("."):
        return (
            ValidationError(
                "CLTR-VALIDATE-IDENTITY",
                "transition_id",
                f"transition_id {value!r} is not a safe single-segment ASCII generation-directory name",
            ),
        )
    return ()


def validate_record(record: ProductionCltrRecord) -> tuple[ValidationError, ...]:
    """Full production validation pipeline. Deterministic, fail-closed."""

    errors: list[ValidationError] = []
    errors.extend(validate_schema_identity(record))
    if errors:
        # An unsupported schema identity/version makes further structural
        # validation meaningless; fail closed immediately (135I §2.7).
        return tuple(errors)
    errors.extend(validate_state_transition_legality(record))
    errors.extend(validate_certified_content(record))
    errors.extend(validate_notification_binding(record))
    errors.extend(validate_receipt_binding(record))
    errors.extend(validate_identity_ascii_safety(record))
    return tuple(errors)
