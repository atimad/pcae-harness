"""
Runtime Invocation Authority — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.7.

Implements the RIHAC-001 v1.0
(docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md) and
RIASC-001 v1.0
(docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md) frozen
contracts: the immutable `RuntimeInvocationApproval` model, the
`pcae.prompt-semantic.v1` canonicalizer, RIASC-001 schema-shape
validation, and the RIHAC-001 twelve-step ordered validator.

This module is a data/validation boundary. It imports no
`subprocess`, `socket`, provider SDK, or execution-adjacent module, and it
never reads a live git/OS clock or repository state itself -- every fact
(repository fingerprint, task state, HEAD, current time, ...) is supplied
by the trusted caller. Approval and authenticated-principal authority are
different: this phase resolves the former through its exact canonical
store and freshly re-verifies the latter through verifier-owned HPAC store
context. It still performs no dispatch, Permission Broker evaluation, or
Gate-9 write.

No field named `approved`, `authorized`, `permission`, `pb_allow`, or an
equivalent authority shortcut exists anywhere in this module (RIASC-001
§0). Approval creation (Option A, per Phase 149O.20L.7O.3V.2 §13) is
internal-API-only: there is no CLI surface here and none is added by this
phase.

Consumption (RIHAC-001 §17, the durable gate-9 `dispatch_attempted`
marker) is explicitly NOT implemented here -- gates 8/9 do not exist yet
(3V.2 §16 "Approval consumption staging"). Validating an approval in this
module never marks it consumed.

The persisted approval envelope remains the frozen RIASC-001 v1.0 shape:
the later contract files and canonical approval-store structure are outside
this phase's allowlist.  The production boundary therefore hard-rejects the
only currently implemented deterministic NON-REAL HPAC mechanism; no real
authority success path is introduced by these structural repairs.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Callable, Mapping, Protocol, Sequence

Clock = Callable[[], str]

RIHAC_CONTRACT_VERSION = "RIHAC-001/1.0"
RIASC_SCHEMA_ID = "RIASC-001"
RIASC_SCHEMA_VERSION = "1.0"
RIASC_RECORD_TYPE = "runtime_invocation_approval"
PROMPT_HASH_PROFILE = "pcae.prompt-semantic.v1"

_APPROVAL_ID_RE = re.compile(r"^ria-[0-9a-f]{32}$")
_INVOCATION_ID_RE = re.compile(r"^inv-[0-9a-f]{32}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")
_NONEMPTY_ID_RE = re.compile(r"^[^\s].*[^\s]$|^[^\s]$")

#: RIASC-001 §0 -- forbidden anywhere in a stored/candidate approval
#: document, recursively, regardless of nesting depth.
FORBIDDEN_AUTHORITY_SHORTCUT_KEYS: frozenset[str] = frozenset(
    {"approved", "authorized", "permission", "pb_allow", "execution_allowed", "authorization"}
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _normalize_recursive(value: object) -> object:
    """NFC-normalize every string in a nested structure (RIASC-001 §8
    step 2 / RIHAC-001 §10 step 2), preserving array order and dict key
    order (canonical JSON serialization sorts keys separately)."""
    if isinstance(value, str):
        return _nfc(value)
    if isinstance(value, Mapping):
        return {k: _normalize_recursive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_recursive(v) for v in value]
    return value


def _digest(value: object) -> str:
    normalized = _normalize_recursive(value)
    return hashlib.sha256(_canonical_json(normalized).encode("utf-8")).hexdigest()


def _parse_utc_timestamp(value: str) -> datetime:
    """Parse the RIASC RFC3339 UTC profile into an aware instant."""
    if not _TIMESTAMP_RE.fullmatch(value):
        raise ValueError("invalid_riasc_timestamp")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    return parsed.astimezone(timezone.utc)


def compute_canonical_digest(value: object) -> str:
    """Public alias of this module's canonical NFC-normalized,
    sorted-key-JSON SHA-256 digest helper, for trusted callers outside
    this module (e.g. `runtime_dispatch_permission.py`) that need the same
    canonicalization rule without duplicating it."""
    return _digest(value)


def new_approval_id() -> str:
    """An opaque, cryptographically strong approval identity
    (RIASC-001 §3), allocated only by the trusted approval coordinator."""
    return f"ria-{uuid.uuid4().hex}"


def is_valid_approval_id(value: object) -> bool:
    return isinstance(value, str) and bool(_APPROVAL_ID_RE.match(value))


# ═══════════════════════════════════════════════════════════════════════
# pcae.prompt-semantic.v1 canonicalizer (RIHAC-001 §10)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PromptSemanticComponent:
    """One ordered instruction/context component that will be delivered
    to the runtime, or can otherwise change its behavior (RIHAC-001 §10
    step 1). `kind` is a stable label (e.g. "system", "task", "context");
    `content` is the exact semantic text."""

    kind: str
    content: str


def _normalize_prompt_text(text: str) -> str:
    """RIHAC-001 §10 step 2: NFC normalize; normalize CRLF/bare CR to LF;
    preserve all other whitespace, blank lines, punctuation, ordering,
    case. No trimming, no collapsing."""
    normalized = _nfc(text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    return normalized


def compute_prompt_semantic_hash(components: Sequence[PromptSemanticComponent]) -> str:
    """Compute the `pcae.prompt-semantic.v1` digest (RIHAC-001 §10 steps
    1-6): ordered semantic components, NFC+CRLF normalized, serialized as
    compact UTF-8 JSON with recursively sorted object keys and preserved
    array order, hashed with SHA-256.

    Exclusion of transport/display-only material (ANSI decoration,
    terminal wrapping, ephemeral timestamps/request IDs/host paths used
    solely for presentation) is the trusted caller's responsibility when
    building the `components` sequence -- this function only canonicalizes
    and hashes whatever ordered semantic document it is given (step 3/4 are
    caller-side inclusion decisions, not something this pure function can
    infer)."""
    document = [
        {"kind": _nfc(c.kind), "content": _normalize_prompt_text(c.content)} for c in components
    ]
    return hashlib.sha256(_canonical_json(document).encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# RIASC-001 v1.0 model -- exact 1:1 representation of the frozen schema
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ArtifactRef:
    artifact_id: str
    artifact_digest: str

    def to_dict(self) -> dict:
        return {"artifact_id": self.artifact_id, "artifact_digest": self.artifact_digest}


@dataclass(frozen=True)
class ApprovalSubject:
    """RIASC-001 §3 -- the exact, closed, five-member subject. All five
    members are one indivisible subject; no member is optional."""

    invocation_id: str
    runtime_target_id: str
    prompt_hash: str
    repository_identity: str
    task_id: str

    def to_dict(self) -> dict:
        return {
            "invocation_id": self.invocation_id,
            "runtime_target_id": self.runtime_target_id,
            "prompt_hash": self.prompt_hash,
            "repository_identity": self.repository_identity,
            "task_id": self.task_id,
        }


@dataclass(frozen=True)
class GovernanceContext:
    """RIASC-001 §4. `session_id` is present iff the invocation is
    actually inside an explicitly session-scoped interactive workflow;
    absence means "not session-scoped," never unknown/defaulted."""

    phase_id: str
    session_id: str | None = None

    def to_dict(self) -> dict:
        out: dict = {"phase_id": self.phase_id}
        if self.session_id is not None:
            out["session_id"] = self.session_id
        return out


@dataclass(frozen=True)
class ApprovalScope:
    """RIASC-001 §5. Every field is fixed/const per the frozen schema
    except `requested_capability` and the two closed reference pairs."""

    requested_capability: str
    filesystem_scope_ref: ArtifactRef
    process_profile_ref: ArtifactRef
    transport_type: str = "local_cli"
    effect_class: str = "bounded_local_process_dispatch"
    dispatch_limit: int = 1
    network_required: bool = False

    def to_dict(self) -> dict:
        return {
            "requested_capability": self.requested_capability,
            "transport_type": self.transport_type,
            "effect_class": self.effect_class,
            "dispatch_limit": self.dispatch_limit,
            "network_required": self.network_required,
            "filesystem_scope_ref": self.filesystem_scope_ref.to_dict(),
            "process_profile_ref": self.process_profile_ref.to_dict(),
        }


@dataclass(frozen=True)
class AdapterBinding:
    """RIASC-001 §5. Executable identity is deliberately absent -- it is
    descriptor-pinned and live-preflight verified (gate 8, a later
    phase's scope)."""

    adapter_id: str
    descriptor_version: str
    descriptor_digest: str
    target_config_digest: str

    def to_dict(self) -> dict:
        return {
            "adapter_id": self.adapter_id,
            "descriptor_version": self.descriptor_version,
            "descriptor_digest": self.descriptor_digest,
            "target_config_digest": self.target_config_digest,
        }


@dataclass(frozen=True)
class FreshnessSnapshot:
    """RIASC-001 §6. Together with `subject`/`adapter_binding`/`expires_at`
    this encodes all seven RIHAC-001 §13 freshness conditions."""

    head_commit: str
    task_contract_digest: str
    policy_version: str
    task_state: str = "active"

    def to_dict(self) -> dict:
        return {
            "head_commit": self.head_commit,
            "task_contract_digest": self.task_contract_digest,
            "task_state": self.task_state,
            "policy_version": self.policy_version,
        }


IDENTITY_EVIDENCE_TYPED_CONFIRMATION_ONLY = "typed_confirmation_only"
IDENTITY_EVIDENCE_OS_AUTHENTICATED_USER = "os_authenticated_user"
_IDENTITY_EVIDENCE_KINDS = frozenset(
    {IDENTITY_EVIDENCE_TYPED_CONFIRMATION_ONLY, IDENTITY_EVIDENCE_OS_AUTHENTICATED_USER}
)
APPROVAL_MECHANISM_V1 = "interactive_local_cli_confirmation"
PRODUCER_COMPONENT_V1 = "pcae.trusted_runtime_approval_coordinator"


@dataclass(frozen=True)
class ApprovalProvenance:
    """RIASC-001 §7. `approver_id` is the identified human, never the
    artifact producer; `producer_component` is fixed to the one trusted
    coordinator identity this v1 contract recognizes."""

    approver_id: str
    identity_evidence_kind: str
    approval_preview_digest: str
    approval_mechanism: str = APPROVAL_MECHANISM_V1
    producer_component: str = PRODUCER_COMPONENT_V1

    def to_dict(self) -> dict:
        return {
            "approver_id": self.approver_id,
            "identity_evidence_kind": self.identity_evidence_kind,
            "approval_mechanism": self.approval_mechanism,
            "approval_preview_digest": self.approval_preview_digest,
            "producer_component": self.producer_component,
        }


@dataclass(frozen=True)
class RuntimeInvocationApproval:
    """RIASC-001 v1.0 -- exact sixteen required top-level fields. No
    additional fields; no boolean authority shortcuts anywhere (§0)."""

    approval_id: str
    record_digest: str
    created_at: str
    expires_at: str
    subject: ApprovalSubject
    governance_context: GovernanceContext
    approval_scope: ApprovalScope
    adapter_binding: AdapterBinding
    freshness_snapshot: FreshnessSnapshot
    provenance: ApprovalProvenance
    schema_id: str = RIASC_SCHEMA_ID
    schema_version: str = RIASC_SCHEMA_VERSION
    contract_version: str = RIHAC_CONTRACT_VERSION
    record_type: str = RIASC_RECORD_TYPE
    prompt_hash_profile: str = PROMPT_HASH_PROFILE
    attempt_limit: int = 1

    def to_dict(self) -> dict:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
            "record_type": self.record_type,
            "approval_id": self.approval_id,
            "record_digest": self.record_digest,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "subject": self.subject.to_dict(),
            "governance_context": self.governance_context.to_dict(),
            "prompt_hash_profile": self.prompt_hash_profile,
            "approval_scope": self.approval_scope.to_dict(),
            "adapter_binding": self.adapter_binding.to_dict(),
            "freshness_snapshot": self.freshness_snapshot.to_dict(),
            "provenance": self.provenance.to_dict(),
            "attempt_limit": self.attempt_limit,
        }

    def digest_payload(self) -> dict:
        """RIASC-001 §8 step 1: everything except `record_digest`."""
        payload = self.to_dict()
        del payload["record_digest"]
        return payload


def compute_record_digest(approval: RuntimeInvocationApproval) -> str:
    """RIASC-001 §8: canonicalize (minus `record_digest`), NFC-normalize,
    compact-JSON with recursively sorted keys, SHA-256."""
    return _digest(approval.digest_payload())


# ═══════════════════════════════════════════════════════════════════════
# Approval creation (Option A -- internal API / test-only, 3V.2 §13)
# ═══════════════════════════════════════════════════════════════════════


def build_approval_preview_digest(
    *,
    subject: ApprovalSubject,
    approval_scope: ApprovalScope,
    expires_at: str,
) -> str:
    """The digest of the exact preview a human reviewed before approving
    (RIHAC-001 §3/§12). No CLI renders this preview in this phase (Option
    A); tests construct the preview digest directly from the same bound
    facts the approval will carry, matching what a future renderer would
    show."""
    return _digest(
        {
            "subject": subject.to_dict(),
            "approval_scope": approval_scope.to_dict(),
            "expires_at": expires_at,
        }
    )


def create_runtime_invocation_approval(
    *,
    subject: ApprovalSubject,
    governance_context: GovernanceContext,
    approval_scope: ApprovalScope,
    adapter_binding: AdapterBinding,
    freshness_snapshot: FreshnessSnapshot,
    created_at: str,
    expires_at: str,
    authenticated_principal: object | None = None,
    approver_id: str | None = None,
    identity_evidence_kind: str | None = None,
    approval_preview_digest: str | None = None,
) -> RuntimeInvocationApproval:
    """Construct one immutable `RuntimeInvocationApproval` (RIHAC-001 gate
    3). This is the sole trusted coordinator entry point (Option A,
    internal-API-only per 3V.2 §13); there is no public CLI. The caller
    (a test harness or a future trusted coordinator) supplies every
    already-resolved trusted fact -- this function performs no repository,
    task, or clock resolution of its own, matching `AuthoritySnapshot`'s
    existing construction discipline in `runtime_invocation.py`.

    Human provenance is never accepted as caller-authored text.  The
    approver and approval/invocation bindings are derived from a freshly
    reverified ``AuthenticatedHumanPrincipal``.  The legacy string
    keywords remain only as explicit fail-closed tripwires so an old
    caller receives a security-specific error instead of silently
    continuing under the superseded N2 behavior.

    No production assurance mechanism exists today.  Consequently every
    currently obtainable verifier result is ``FIXTURE_NON_REAL`` and this
    function always rejects it before constructing authority.  Tests that
    need a non-real approval-shaped object must use a test-module fixture
    constructor, never this production path.
    """
    # Lazy imports are mandatory here: hpac_foundation's canonical digest
    # primitive imports this module, so a module-level HPAC import would
    # create a cycle before either trust boundary finished initializing.
    from .hpac_foundation import HPACAuthorityClass
    from .hpac_verifier import (
        HPACVerificationError,
        is_verifier_authenticated_principal,
        reverify_authenticated_principal,
    )

    if _parse_utc_timestamp(expires_at) <= _parse_utc_timestamp(created_at):
        raise ValueError("expires_at_must_be_after_created_at")
    if approver_id is not None or identity_evidence_kind is not None:
        raise TypeError(
            "caller-supplied approver_id/identity_evidence_kind cannot establish human authority"
        )
    if not is_verifier_authenticated_principal(authenticated_principal):
        raise ValueError("authenticated_principal_not_verifier_issued")
    try:
        principal = reverify_authenticated_principal(
            authenticated_principal,
            now=created_at,
            occurred_at=created_at,
        )
    except HPACVerificationError as exc:
        raise ValueError("authenticated_principal_reverification_failed") from exc
    if principal.invocation_id != subject.invocation_id:
        raise ValueError("authenticated_principal_invocation_mismatch")
    if principal.assurance_class is not HPACAuthorityClass.PRODUCTION:
        raise ValueError("non_real_authenticated_principal_cannot_create_production_approval")
    if not is_valid_approval_id(principal.approval_id):
        raise ValueError("authenticated_principal_approval_id_invalid")

    preview_digest = approval_preview_digest or build_approval_preview_digest(
        subject=subject, approval_scope=approval_scope, expires_at=expires_at
    )
    provenance = ApprovalProvenance(
        approver_id=principal.principal_id,
        # The persisted v1 envelope remains frozen in this bounded repair;
        # the authority basis is the verifier result above, not this legacy
        # enum label.  A later schema migration can replace the envelope.
        identity_evidence_kind=IDENTITY_EVIDENCE_OS_AUTHENTICATED_USER,
        approval_preview_digest=preview_digest,
    )
    partial = RuntimeInvocationApproval(
        approval_id=principal.approval_id,
        record_digest="",
        created_at=created_at,
        expires_at=expires_at,
        subject=subject,
        governance_context=governance_context,
        approval_scope=approval_scope,
        adapter_binding=adapter_binding,
        freshness_snapshot=freshness_snapshot,
        provenance=provenance,
    )
    digest = compute_record_digest(partial)
    return RuntimeInvocationApproval(**{**partial.__dict__, "record_digest": digest})


# ═══════════════════════════════════════════════════════════════════════
# RIASC-001 schema-shape validation (structural; §11 cross-field checks
# are separate, see `validate_approval` below)
# ═══════════════════════════════════════════════════════════════════════

_TOP_LEVEL_REQUIRED: frozenset[str] = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "approval_id",
        "record_digest",
        "created_at",
        "expires_at",
        "subject",
        "governance_context",
        "prompt_hash_profile",
        "approval_scope",
        "adapter_binding",
        "freshness_snapshot",
        "provenance",
        "attempt_limit",
    }
)
_SUBJECT_REQUIRED: frozenset[str] = frozenset(
    {"invocation_id", "runtime_target_id", "prompt_hash", "repository_identity", "task_id"}
)
_GOVERNANCE_ALLOWED: frozenset[str] = frozenset({"phase_id", "session_id"})
_SCOPE_REQUIRED: frozenset[str] = frozenset(
    {
        "requested_capability",
        "transport_type",
        "effect_class",
        "dispatch_limit",
        "network_required",
        "filesystem_scope_ref",
        "process_profile_ref",
    }
)
_ADAPTER_REQUIRED: frozenset[str] = frozenset(
    {"adapter_id", "descriptor_version", "descriptor_digest", "target_config_digest"}
)
_FRESHNESS_REQUIRED: frozenset[str] = frozenset(
    {"head_commit", "task_contract_digest", "task_state", "policy_version"}
)
_PROVENANCE_REQUIRED: frozenset[str] = frozenset(
    {
        "approver_id",
        "identity_evidence_kind",
        "approval_mechanism",
        "approval_preview_digest",
        "producer_component",
    }
)
_ARTIFACT_REF_REQUIRED: frozenset[str] = frozenset({"artifact_id", "artifact_digest"})


def _find_authority_shortcut_keys(value: object, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, sub in value.items():
            if key in FORBIDDEN_AUTHORITY_SHORTCUT_KEYS:
                found.append(f"{path}.{key}")
            found.extend(_find_authority_shortcut_keys(sub, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for idx, sub in enumerate(value):
            found.extend(_find_authority_shortcut_keys(sub, f"{path}[{idx}]"))
    return found


def _closed_object_issues(
    obj: object, required: frozenset[str], allowed: frozenset[str] | None, name: str
) -> list[str]:
    issues: list[str] = []
    if not isinstance(obj, Mapping):
        return [f"{name}_not_object"]
    keys = set(obj.keys())
    allowed_keys = allowed if allowed is not None else required
    missing = required - keys
    extra = keys - allowed_keys
    for m in sorted(missing):
        issues.append(f"{name}_missing_field:{m}")
    for e in sorted(extra):
        issues.append(f"{name}_unknown_field:{e}")
    return issues


def validate_riasc_schema_shape(data: Mapping) -> tuple[str, ...]:
    """RIASC-001 structural validation: exactly sixteen required top-level
    fields, `additionalProperties:false` applied recursively to every
    object, no authority-shortcut field name anywhere, exact
    consts/patterns/types. This is shape validation only -- it does not
    establish authority (RIASC-001 §0) and does not perform the
    cross-field checks in §11 (digest recomputation, expiry ordering,
    subject equality with live state, etc; see `validate_approval`).

    Returns an empty tuple iff the document is a schema-shape-valid
    RIASC-001 v1.0 candidate.
    """
    issues: list[str] = []
    if not isinstance(data, Mapping):
        return ("not_an_object",)

    issues.extend(_closed_object_issues(data, _TOP_LEVEL_REQUIRED, _TOP_LEVEL_REQUIRED, "root"))

    def const(field_name: str, expected: object) -> None:
        if field_name in data and data[field_name] != expected:
            issues.append(f"root_const_mismatch:{field_name}")

    const("schema_id", RIASC_SCHEMA_ID)
    const("schema_version", RIASC_SCHEMA_VERSION)
    const("contract_version", RIHAC_CONTRACT_VERSION)
    const("record_type", RIASC_RECORD_TYPE)
    const("prompt_hash_profile", PROMPT_HASH_PROFILE)
    if "attempt_limit" in data and (type(data["attempt_limit"]) is not int or data["attempt_limit"] != 1):
        issues.append("root_const_mismatch:attempt_limit")

    if "approval_id" in data and not is_valid_approval_id(data["approval_id"]):
        issues.append("root_invalid_pattern:approval_id")
    for digest_field in ("record_digest",):
        if digest_field in data and not (
            isinstance(data[digest_field], str) and _SHA256_RE.match(data[digest_field])
        ):
            issues.append(f"root_invalid_pattern:{digest_field}")
    for ts_field in ("created_at", "expires_at"):
        if ts_field in data and not (
            isinstance(data[ts_field], str) and _TIMESTAMP_RE.match(data[ts_field])
        ):
            issues.append(f"root_invalid_pattern:{ts_field}")

    subject = data.get("subject")
    issues.extend(_closed_object_issues(subject, _SUBJECT_REQUIRED, _SUBJECT_REQUIRED, "subject"))
    if isinstance(subject, Mapping):
        if "invocation_id" in subject and not (
            isinstance(subject["invocation_id"], str)
            and _INVOCATION_ID_RE.match(subject["invocation_id"])
        ):
            issues.append("subject_invalid_pattern:invocation_id")
        for f in ("prompt_hash", "repository_identity"):
            if f in subject and not (isinstance(subject[f], str) and _SHA256_RE.match(subject[f])):
                issues.append(f"subject_invalid_pattern:{f}")
        for f in ("runtime_target_id", "task_id"):
            if f in subject and not (
                isinstance(subject[f], str)
                and 1 <= len(subject[f]) <= (128 if f == "runtime_target_id" else 256)
                and _NONEMPTY_ID_RE.match(subject[f])
            ):
                issues.append(f"subject_invalid_pattern:{f}")

    gov = data.get("governance_context")
    issues.extend(
        _closed_object_issues(gov, frozenset({"phase_id"}), _GOVERNANCE_ALLOWED, "governance_context")
    )
    if isinstance(gov, Mapping):
        for f in ("phase_id", "session_id"):
            if f in gov and not (
                isinstance(gov[f], str)
                and 1 <= len(gov[f]) <= 256
                and _NONEMPTY_ID_RE.fullmatch(gov[f])
            ):
                issues.append(f"governance_context_invalid_pattern:{f}")

    scope = data.get("approval_scope")
    issues.extend(_closed_object_issues(scope, _SCOPE_REQUIRED, _SCOPE_REQUIRED, "approval_scope"))
    if isinstance(scope, Mapping):
        if "requested_capability" in scope and not (
            isinstance(scope["requested_capability"], str)
            and 1 <= len(scope["requested_capability"]) <= 128
            and _NONEMPTY_ID_RE.fullmatch(scope["requested_capability"])
        ):
            issues.append("approval_scope_invalid_pattern:requested_capability")
        if "transport_type" in scope and scope["transport_type"] != "local_cli":
            issues.append("approval_scope_const_mismatch:transport_type")
        if "effect_class" in scope and scope["effect_class"] != "bounded_local_process_dispatch":
            issues.append("approval_scope_const_mismatch:effect_class")
        if "dispatch_limit" in scope and (
            type(scope["dispatch_limit"]) is not int or scope["dispatch_limit"] != 1
        ):
            issues.append("approval_scope_const_mismatch:dispatch_limit")
        if "network_required" in scope and scope["network_required"] is not False:
            issues.append("approval_scope_const_mismatch:network_required")
        for ref_field in ("filesystem_scope_ref", "process_profile_ref"):
            ref = scope.get(ref_field)
            issues.extend(
                _closed_object_issues(
                    ref, _ARTIFACT_REF_REQUIRED, _ARTIFACT_REF_REQUIRED, f"approval_scope.{ref_field}"
                )
            )
            if isinstance(ref, Mapping):
                if "artifact_id" in ref and not (
                    isinstance(ref["artifact_id"], str)
                    and 1 <= len(ref["artifact_id"]) <= 256
                    and _NONEMPTY_ID_RE.fullmatch(ref["artifact_id"])
                ):
                    issues.append(f"approval_scope.{ref_field}_invalid_pattern:artifact_id")
                if "artifact_digest" in ref and not (
                    isinstance(ref["artifact_digest"], str)
                    and _SHA256_RE.fullmatch(ref["artifact_digest"])
                ):
                    issues.append(f"approval_scope.{ref_field}_invalid_pattern:artifact_digest")

    adapter = data.get("adapter_binding")
    issues.extend(
        _closed_object_issues(adapter, _ADAPTER_REQUIRED, _ADAPTER_REQUIRED, "adapter_binding")
    )
    if isinstance(adapter, Mapping):
        for f in ("adapter_id", "descriptor_version"):
            if f in adapter and not (
                isinstance(adapter[f], str)
                and 1 <= len(adapter[f]) <= 128
                and _NONEMPTY_ID_RE.fullmatch(adapter[f])
            ):
                issues.append(f"adapter_binding_invalid_pattern:{f}")
        for f in ("descriptor_digest", "target_config_digest"):
            if f in adapter and not (isinstance(adapter[f], str) and _SHA256_RE.match(adapter[f])):
                issues.append(f"adapter_binding_invalid_pattern:{f}")

    freshness = data.get("freshness_snapshot")
    issues.extend(
        _closed_object_issues(
            freshness, _FRESHNESS_REQUIRED, _FRESHNESS_REQUIRED, "freshness_snapshot"
        )
    )
    if isinstance(freshness, Mapping):
        if "task_state" in freshness and freshness["task_state"] != "active":
            issues.append("freshness_snapshot_const_mismatch:task_state")
        if "task_contract_digest" in freshness and not (
            isinstance(freshness["task_contract_digest"], str)
            and _SHA256_RE.match(freshness["task_contract_digest"])
        ):
            issues.append("freshness_snapshot_invalid_pattern:task_contract_digest")
        if "head_commit" in freshness and not (
            isinstance(freshness["head_commit"], str)
            and re.match(r"^[0-9a-f]{40,64}$", freshness["head_commit"])
        ):
            issues.append("freshness_snapshot_invalid_pattern:head_commit")
        if "policy_version" in freshness and not (
            isinstance(freshness["policy_version"], str)
            and 1 <= len(freshness["policy_version"]) <= 128
            and _NONEMPTY_ID_RE.fullmatch(freshness["policy_version"])
        ):
            issues.append("freshness_snapshot_invalid_pattern:policy_version")

    provenance = data.get("provenance")
    issues.extend(
        _closed_object_issues(provenance, _PROVENANCE_REQUIRED, _PROVENANCE_REQUIRED, "provenance")
    )
    if isinstance(provenance, Mapping):
        if "approver_id" in provenance and not (
            isinstance(provenance["approver_id"], str)
            and 1 <= len(provenance["approver_id"]) <= 256
            and _NONEMPTY_ID_RE.fullmatch(provenance["approver_id"])
        ):
            issues.append("provenance_invalid_pattern:approver_id")
        if (
            "identity_evidence_kind" in provenance
            and provenance["identity_evidence_kind"] not in _IDENTITY_EVIDENCE_KINDS
        ):
            issues.append("provenance_invalid_enum:identity_evidence_kind")
        if (
            "approval_mechanism" in provenance
            and provenance["approval_mechanism"] != APPROVAL_MECHANISM_V1
        ):
            issues.append("provenance_const_mismatch:approval_mechanism")
        if (
            "producer_component" in provenance
            and provenance["producer_component"] != PRODUCER_COMPONENT_V1
        ):
            issues.append("provenance_const_mismatch:producer_component")
        if "approval_preview_digest" in provenance and not (
            isinstance(provenance["approval_preview_digest"], str)
            and _SHA256_RE.match(provenance["approval_preview_digest"])
        ):
            issues.append("provenance_invalid_pattern:approval_preview_digest")

    issues.extend(f"forbidden_authority_shortcut:{p}" for p in _find_authority_shortcut_keys(data))

    return tuple(dict.fromkeys(issues))


def approval_to_candidate_dict(approval: RuntimeInvocationApproval) -> dict:
    """Round-trip helper: the exact dict a store would persist/load."""
    return approval.to_dict()


# ═══════════════════════════════════════════════════════════════════════
# RIHAC-001 §16 ordered validation
# ═══════════════════════════════════════════════════════════════════════

CONSUMPTION_STATE_NONE = "none"
CONSUMPTION_STATE_CONSUMED = "dispatch_attempted"
CONSUMPTION_STATE_CANCELLED = "cancelled"
CONSUMPTION_STATE_UNCERTAIN = "dispatch_uncertain"
CONSUMPTION_STATE_COMPLETED = "completed"

_NON_CONSUMABLE_STATES: frozenset[str] = frozenset(
    {
        CONSUMPTION_STATE_CONSUMED,
        CONSUMPTION_STATE_CANCELLED,
        CONSUMPTION_STATE_UNCERTAIN,
        CONSUMPTION_STATE_COMPLETED,
    }
)

ConsumptionLookup = Callable[[str], str]
"""Given an `approval_id`, return one of `CONSUMPTION_STATE_*`. Injected
by the trusted caller; this module performs no store I/O itself."""


class CanonicalApprovalStore(Protocol):
    """The narrow read interface consumed by N1 validation.

    ``validate_approval`` additionally enforces the concrete canonical
    store type at runtime.  The protocol exists only to avoid a module
    import cycle in annotations; it is not an alternate trust source.
    """

    def load(self, approval_id: str) -> RuntimeInvocationApproval | None: ...


@dataclass(frozen=True)
class InvocationRequestContext:
    """The current, live facts a `runtime_dispatch` request presents to
    gate 5, to be bound/compared against the stored approval (RIHAC-001
    §16 steps 5-9). Every field here is caller-resolved trusted state,
    never adapter/runtime-supplied."""

    invocation_id: str
    runtime_target_id: str
    prompt_hash: str
    repository_identity: str
    task_id: str
    phase_id: str
    session_id: str | None
    approval_scope: ApprovalScope
    adapter_binding: AdapterBinding
    head_commit: str
    task_contract_digest: str
    task_state: str
    policy_version: str
    current_time: str


@dataclass(frozen=True, eq=False)
class ValidatedAuthorityProjection:
    """RIHAC-001 §16 step 12 -- the immutable evidence projection gate 5
    emits on success. This projection, never raw approval prose or a
    caller assertion, is the only thing the trusted PB request builder
    (`runtime_dispatch_permission.py`) may read to derive
    `approval_present`/`human_authority_binding` (PBRD-001 §7)."""

    approval_id: str
    record_digest: str
    subject_scope_binding_digest: str
    provenance_verdict: str
    freshness_verdict_digest: str
    expiry_verdict: str
    consumption_state_verdict: str
    validated_at: str
    principal_id: str = ""
    proof_id: str = ""
    mechanism_id: str = ""
    mechanism_assurance: str = ""
    invocation_id: str = ""
    schema_version: str = RIASC_SCHEMA_VERSION
    _content_binding_digest: str = ""

    def _binding_payload(self) -> dict:
        return {
            "approval_id": self.approval_id,
            "record_digest": self.record_digest,
            "subject_scope_binding_digest": self.subject_scope_binding_digest,
            "provenance_verdict": self.provenance_verdict,
            "freshness_verdict_digest": self.freshness_verdict_digest,
            "expiry_verdict": self.expiry_verdict,
            "consumption_state_verdict": self.consumption_state_verdict,
            "validated_at": self.validated_at,
            "principal_id": self.principal_id,
            "proof_id": self.proof_id,
            "mechanism_id": self.mechanism_id,
            "mechanism_assurance": self.mechanism_assurance,
            "invocation_id": self.invocation_id,
            "schema_version": self.schema_version,
        }

    def evidence_digest(self) -> str:
        return _digest(self._binding_payload())


@dataclass(frozen=True)
class _ProjectionRevalidationContext:
    approval_store: CanonicalApprovalStore
    authenticated_principal: object
    invocation_context: InvocationRequestContext
    consumption_lookup: ConsumptionLookup


_VALIDATED_AUTHORITY_CONTEXTS: dict[
    ValidatedAuthorityProjection, _ProjectionRevalidationContext
] = {}


def is_trusted_validated_authority_projection(value: object) -> bool:
    """Return true only for intact evidence emitted by ``validate_approval``.

    Exact-object registry provenance prevents a copied lookalike from
    transferring authority.  Recomputing the binding from every current
    field prevents mutation or ``dataclasses.replace`` from carrying a
    previously-valid token onto different content (B1).
    """
    return (
        type(value) is ValidatedAuthorityProjection
        and value in _VALIDATED_AUTHORITY_CONTEXTS
        and value._content_binding_digest == value.evidence_digest()
    )


def validate_approval(
    approval_id: object,
    *,
    approval_store: CanonicalApprovalStore | None = None,
    authenticated_principal: object | None = None,
    context: InvocationRequestContext,
    consumption_lookup: ConsumptionLookup,
) -> tuple[ValidatedAuthorityProjection | None, tuple[str, ...]]:
    """RIHAC-001 §16's exact twelve-step fail-closed ordered validation.
    No later step runs as a shortcut when an earlier step fails
    (short-circuit on first failing step, returning `(None, (reason,))`).
    On full success, returns `(projection, ())`.

    The first argument is an opaque approval ID, never an approval object.
    Steps 1-2 resolve it through the one concrete canonical approval store;
    caller-created objects and caller-provided lookalike stores fail closed.
    Human identity is freshly reverified from current HPAC stores and bound
    to the resolved approval before any authority projection can be emitted.
    """
    from .hpac_foundation import HPACAuthorityClass
    from .hpac_verifier import (
        is_verifier_authenticated_principal,
        reverify_authenticated_principal,
    )

    # Steps 1-2: canonical resolution/single-artifact load (N1).  Importing
    # locally avoids the store -> authority model import cycle while still
    # requiring the concrete canonical store, not a duck-typed substitute.
    if approval_id is None:
        return None, ("no_valid_approval:missing_or_unresolvable",)
    caller_supplied_approval = (
        approval_id if isinstance(approval_id, RuntimeInvocationApproval) else None
    )
    if caller_supplied_approval is None and not is_valid_approval_id(approval_id):
        return None, ("noncanonical_approval_id",)
    from .runtime_invocation_approval_store import RuntimeInvocationApprovalStore

    if caller_supplied_approval is not None:
        # A caller object is never authority.  We may still compute
        # fail-closed diagnostics from it so pre-N1 schema/binding tests
        # retain useful specificity, but the unconditional N1 rejection
        # below runs before HPAC provenance or projection construction.
        approval = caller_supplied_approval
    else:
        if type(approval_store) is not RuntimeInvocationApprovalStore:
            return None, ("canonical_approval_store_required",)
        try:
            approval = approval_store.load(approval_id)
        except Exception as exc:
            return None, (f"canonical_approval_resolution_failed:{type(exc).__name__}",)
    if approval is None:
        return None, ("no_valid_approval:missing_or_unresolvable",)
    if caller_supplied_approval is None and approval.approval_id != approval_id:
        return None, ("canonical_approval_identity_mismatch",)

    # Step 3: RIASC-001 schema/version/required-field/closed-field/type validation.
    schema_issues = validate_riasc_schema_shape(approval.to_dict())
    if schema_issues:
        return None, ("riasc_schema_invalid:" + ",".join(schema_issues),)
    if approval.schema_id != RIASC_SCHEMA_ID or approval.schema_version != RIASC_SCHEMA_VERSION:
        return None, ("unknown_schema_version",)
    if approval.contract_version != RIHAC_CONTRACT_VERSION:
        return None, ("unknown_contract_version",)

    # Step 4: record-digest recomputation + producer/human provenance.
    recomputed = compute_record_digest(approval)
    if recomputed != approval.record_digest:
        return None, ("record_digest_mismatch",)
    if approval.provenance.producer_component != PRODUCER_COMPONENT_V1:
        return None, ("untrusted_producer_component",)
    if approval.provenance.approval_mechanism != APPROVAL_MECHANISM_V1:
        return None, ("untrusted_approval_mechanism",)
    if not approval.provenance.approver_id:
        return None, ("missing_approver_identity",)
    if approval.provenance.approver_id == approval.provenance.producer_component:
        return None, ("producer_identity_not_distinct_from_approver",)
    expected_preview_digest = build_approval_preview_digest(
        subject=approval.subject,
        approval_scope=approval.approval_scope,
        expires_at=approval.expires_at,
    )
    if approval.provenance.approval_preview_digest != expected_preview_digest:
        return None, ("approval_preview_digest_mismatch",)

    # Step 5: repository, task, phase, conditional session binding.
    if approval.subject.repository_identity != context.repository_identity:
        return None, ("subject_mismatch:repository_identity",)
    if approval.subject.task_id != context.task_id:
        return None, ("subject_mismatch:task_id",)
    if approval.governance_context.phase_id != context.phase_id:
        return None, ("governance_context_mismatch:phase_id",)
    if approval.governance_context.session_id != context.session_id:
        return None, ("governance_context_mismatch:session_id",)

    # Step 6: invocation_id + exact runtime target.
    if approval.subject.invocation_id != context.invocation_id:
        return None, ("subject_mismatch:invocation_id",)
    if approval.subject.runtime_target_id != context.runtime_target_id:
        return None, ("subject_mismatch:runtime_target_id",)

    # Step 7: prompt hash + canonicalization profile.
    if approval.subject.prompt_hash != context.prompt_hash:
        return None, ("subject_mismatch:prompt_hash",)
    if approval.prompt_hash_profile != PROMPT_HASH_PROFILE:
        return None, ("unsupported_prompt_hash_profile",)

    # Step 8: capability, effect scope, adapter descriptor, target config.
    if approval.approval_scope != context.approval_scope:
        return None, ("scope_mismatch:approval_scope",)
    if approval.adapter_binding != context.adapter_binding:
        return None, ("adapter_binding_mismatch:adapter_binding",)

    subject_scope_binding_digest = _digest(
        {
            "subject": approval.subject.to_dict(),
            "approval_scope": approval.approval_scope.to_dict(),
            "adapter_binding": approval.adapter_binding.to_dict(),
        }
    )

    # Step 9: all seven freshness conditions.
    freshness_failures: list[str] = []
    if approval.freshness_snapshot.head_commit != context.head_commit:
        freshness_failures.append("stale:head_commit")
    if approval.freshness_snapshot.task_contract_digest != context.task_contract_digest:
        freshness_failures.append("stale:task_contract_digest")
    if context.task_state != "active" or approval.freshness_snapshot.task_state != "active":
        freshness_failures.append("stale:task_state")
    # Prompt/target/adapter-config drift already fails closed above (steps
    # 6-8) as subject/binding mismatches; policy-version drift is recorded
    # here as a freshness fact but does NOT by itself invalidate the
    # historical human act (RIHAC-001 §13's explicit disposition) -- it is
    # surfaced so the caller (PB evaluation) re-evaluates rather than
    # reusing a cached decision.
    policy_drifted = approval.freshness_snapshot.policy_version != context.policy_version
    freshness_verdict_digest = _digest(
        {
            "failures": freshness_failures,
            "policy_drifted": policy_drifted,
            "observed_policy_version": context.policy_version,
            "approval_policy_version": approval.freshness_snapshot.policy_version,
        }
    )
    if freshness_failures:
        return None, ("stale_approval:" + ",".join(freshness_failures),)

    # Step 10: created_at/expires_at against a trusted clock.
    if _parse_utc_timestamp(approval.expires_at) <= _parse_utc_timestamp(approval.created_at):
        return None, ("invalid_expiry_ordering",)
    if _parse_utc_timestamp(context.current_time) >= _parse_utc_timestamp(approval.expires_at):
        return None, ("expired",)
    expiry_verdict = "not_expired"

    # Step 11: prior consumption/cancellation/uncertainty/completion.
    consumption_state = consumption_lookup(approval.approval_id)
    if consumption_state in _NON_CONSUMABLE_STATES:
        return None, (f"already_bound:{consumption_state}",)
    if consumption_state != CONSUMPTION_STATE_NONE:
        return None, (f"unrecognized_consumption_state:{consumption_state}",)

    if caller_supplied_approval is not None:
        return None, ("noncanonical_approval_reference:caller_supplied_object",)

    # N2 + HPAC-REQ-058: provenance is derived from, and freshly checked
    # against, canonical HPAC state.  Registry membership alone is cached
    # provenance and is not sufficient at an authority-consumption point.
    if not is_verifier_authenticated_principal(authenticated_principal):
        return None, ("authenticated_principal_not_verifier_issued",)
    try:
        principal = reverify_authenticated_principal(
            authenticated_principal,
            now=context.current_time,
            occurred_at=context.current_time,
        )
    except Exception as exc:
        return None, (f"authenticated_principal_reverification_failed:{type(exc).__name__}",)
    if principal.approval_id != approval.approval_id:
        return None, ("authenticated_principal_approval_mismatch",)
    if principal.invocation_id != approval.subject.invocation_id:
        return None, ("authenticated_principal_invocation_mismatch",)
    if approval.provenance.approver_id != principal.principal_id:
        return None, ("approval_provenance_principal_mismatch",)

    # Interim production hard stop frozen by .1R.6 §8.  The deterministic
    # mechanism may exercise structural plumbing in tests, but it can never
    # be canonicalized into real production authority.
    if principal.assurance_class is not HPACAuthorityClass.PRODUCTION:
        return None, ("non_real_authenticated_principal_cannot_validate_production_approval",)

    # Step 12: emit the immutable validated-authority evidence projection.
    projection = ValidatedAuthorityProjection(
        approval_id=approval.approval_id,
        record_digest=approval.record_digest,
        subject_scope_binding_digest=subject_scope_binding_digest,
        provenance_verdict="identified_human_distinct_from_producer",
        freshness_verdict_digest=freshness_verdict_digest,
        expiry_verdict=expiry_verdict,
        consumption_state_verdict=consumption_state,
        validated_at=context.current_time,
        principal_id=principal.principal_id,
        proof_id=principal.proof_id,
        mechanism_id=principal.mechanism_id,
        mechanism_assurance=principal.assurance_class.value,
        invocation_id=principal.invocation_id,
    )
    projection = replace(projection, _content_binding_digest=projection.evidence_digest())
    _VALIDATED_AUTHORITY_CONTEXTS[projection] = _ProjectionRevalidationContext(
        approval_store=approval_store,
        authenticated_principal=principal,
        invocation_context=context,
        consumption_lookup=consumption_lookup,
    )
    if policy_drifted:
        return projection, ("policy_drift_requires_fresh_pb_re_evaluation",)
    return projection, ()


def revalidate_validated_authority_projection(
    value: object, *, current_time: str
) -> bool:
    """Re-resolve every authority-bearing dependency for PB projection.

    This is validation-only: it performs no Gate-9 consumption write.  A
    stale approval, revoked credential, expired proof/approval, changed
    consumption state, copied projection, or lost process-local provenance
    all return ``False``.
    """

    if not is_trusted_validated_authority_projection(value):
        return False
    assert isinstance(value, ValidatedAuthorityProjection)
    prior = _VALIDATED_AUTHORITY_CONTEXTS.get(value)
    if prior is None:
        return False
    refreshed_context = replace(prior.invocation_context, current_time=current_time)
    projection, reasons = validate_approval(
        value.approval_id,
        approval_store=prior.approval_store,
        authenticated_principal=prior.authenticated_principal,
        context=refreshed_context,
        consumption_lookup=prior.consumption_lookup,
    )
    if projection is None:
        return False
    try:
        if reasons not in ((), ("policy_drift_requires_fresh_pb_re_evaluation",)):
            return False
        return (
            projection.approval_id == value.approval_id
            and projection.record_digest == value.record_digest
            and projection.subject_scope_binding_digest == value.subject_scope_binding_digest
            and projection.principal_id == value.principal_id
            and projection.proof_id == value.proof_id
            and projection.mechanism_id == value.mechanism_id
            and projection.mechanism_assurance == value.mechanism_assurance
            and projection.invocation_id == value.invocation_id
        )
    finally:
        # The freshly emitted projection is comparison evidence only.  The
        # original projection remains the sole registered authority object.
        _VALIDATED_AUTHORITY_CONTEXTS.pop(projection, None)
