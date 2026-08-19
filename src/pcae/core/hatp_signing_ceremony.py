"""HATP Signing Ceremony -- Proof-Context Resolver + Orchestrator
(Phase 149O.12B, Waves C + D of the 149O.11 implementation plan; signer
resolution repaired in place by Phase 149O.20L.7O.2F.2, BF-1/BF-2;
cross-record consistency and revalidation repaired by Phase
149O.20L.7O.2F.4).

Implements HSCE-REQ-013, HSCE-REQ-016, HSCE-REQ-018..030, HSCE-REQ-049..051,
HSCE-REQ-067..071, HSCE-REQ-080..084
(`docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`,
HSCE-001 v1.3). This module owns AG3/AG5 proof-context resolution
(Wave C) and signing-ceremony orchestration (Wave D): deriving every
`HumanApprovalProvenanceProof` field from canonical current state,
resolving the production hardware provider/signer, rendering a
blind-touch-defense preview, invoking the hardware provider exactly
once per ceremony attempt, re-checking context for TOCTOU safety before
persistence, and publishing the resulting envelope through
`hatp_evidence_store.HATPEvidenceStore.publish` -- consuming
`hatp_signed_evidence.build_hatp_signed_evidence_envelope` directly,
never reimplementing envelope construction or the atomic-publication
algorithm.

**No CLI is implemented by this module** (`commands/hatp.py`/`cli.py`
registration remains 149O.12C's exclusive scope, per HSCE-REQ-002/§30 of
the contract). This module alone is inert: nothing in `src/pcae/` calls
`sign_rollback_evidence` yet.

Scope boundary, restated verbatim from the governing phase prompt: this
module

- accepts only `site` (`RollbackSite`) plus a site-specific typed
  operation locator (`job_id` for AG3, `per_id` for AG5) -- no other
  caller-supplied authority field exists on `sign_rollback_evidence`'s
  production entry point (`production_sign_rollback_evidence`, below), which takes
  zero overridable parameters (F-2 non-regression, mirroring
  `hatp_ag_authority.py`'s own zero-override production-adapter
  discipline);
- derives repository identity, Binding, Decision, digests, principal,
  signer, and provider exclusively from canonical current state --
  never from caller input (SC-1/SC-2);
- never calls `verify_hatp_proof`, never derives `approval_present`,
  never mutates AG3's legacy rollback approval state or PER status,
  never calls `execute_rollback`/`build_rollback_execution`, and imports
  no Permission Broker module (HSCE-REQ-067, SC-8/SC-9/SC-10);
- never accepts a caller-supplied physical-presence boolean, and always
  resolves the production hardware provider/trust store through the
  Wave-5/Wave-2 factories (`create_production_hardware_provider`,
  `HATPTrustStore.production()`) at the production entry point -- no
  test/software provider or arbitrary trust store is reachable from it
  (SC-3/SC-4, mirrors `hatp_ag_authority.py`'s F-2 closure).

Dependency direction: this module imports `human_approval_trusted_
provenance.py` (proof model + canonical payload function only -- never
`verify_hatp_proof`), `hatp_providers.py` (Wave-5 production factory +
error vocabulary), `hatp_bootstrap.py` (`HATPTrustStore`,
`resolve_canonical_deployment_root` -- Phase 149O.20L.7O.2F.2's
HSCE-REQ-080 signer resolution), `hatp_hardware_credentials.py`
(`HATPHardwareCredentialStore`, read-only -- the same registry
HSCE-REQ-080 step 5 cross-checks), `hatp_signed_
evidence.py`/`hatp_evidence_store.py` (149O.12A's envelope builder and
store, consumed not reimplemented), `rollback_approval_evidence.py`
(read-only Binding lookup via the public `list_bindings_with_keys`/
`is_revoked` surface -- no RAE mutation function is called),
`repository_identity.py` (read-only), and `agent.py` (read-only:
`build_rollback_review`, `lookup_promotion_execution_record` -- the
identical live-record reads `execute_rollback`/`build_rollback_execution`
already perform for their own preconditions, per HSCE-REQ-013/016). It
does not import `commands/agent.py`, `hatp_ag_authority.py`, `cli.py`,
or any `permission_broker*.py` module.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Tuple, Union

from pcae.core.agent import build_rollback_review, lookup_promotion_execution_record
from pcae.core.hatp_bootstrap import (
    DeploymentBinding,
    HATPTrustStore,
    HATPTrustStoreError,
    PrincipalRecord,
    SignerRecord,
    resolve_canonical_deployment_root,
)
from pcae.core.hatp_evidence_store import HATPEvidenceStore, HATPEvidencePublicationResult
from pcae.core.hatp_hardware_credentials import HardwareCredentialRecord, HATPHardwareCredentialStore
from pcae.core.hatp_providers import (
    HATP_HARDWARE_PROVIDER_V1,
    HATPHardwareSigner,
    HATPProviderCancelledError,
    HATPProviderDeviceError,
    HATPProviderUnavailableError,
    create_production_hardware_provider,
)
from pcae.core.hatp_signed_evidence import build_hatp_signed_evidence_envelope
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HATPProofError,
    HumanApprovalProvenanceProof,
    RollbackSite,
    canonicalize_hatp_proof_payload,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import RepositoryIdentityError, read_repository_identity
from pcae.core.rollback_approval_evidence import (
    Ag3OperationReference as _RaeAg3OperationReference,
    Ag5OperationReference as _RaeAg5OperationReference,
    RollbackApprovalBinding,
    RollbackApprovalEvidenceStore,
    RollbackSite as _RaeRollbackSite,
)

# ═══════════════════════════════════════════════════════════════════════════
# Closed error vocabulary (HSCE-REQ-046..048, the subset this module owns
# per the 149O.11 plan §8). Never expressed using HATP-001's own
# verification-status vocabulary (HSCE-REQ-049) -- this module does not
# import that enum at all. `hatp_evidence_store.py`'s own
# `EvidenceConflictError`/
# `EvidencePersistenceFailureError` are propagated unmodified from
# `store.publish()` (never re-wrapped/reinterpreted), per the 149O.11
# plan's explicit "map its outcomes directly" instruction.
# ═══════════════════════════════════════════════════════════════════════════


class HATPSigningCeremonyError(Exception):
    """Base error for this module. Every subclass below carries a class-
    level `error_type` string drawn exclusively from HSCE-REQ-047's
    closed 12-member vocabulary -- a future CLI (149O.12C) maps this
    attribute to the frozen exit-code table; this module itself performs
    no exit-code mapping."""

    error_type: str = "generic_signing_failure"


class RepositoryIdentityUnavailableError(HATPSigningCeremonyError):
    error_type = "repository_identity_unavailable"


class OperationNotFoundError(HATPSigningCeremonyError):
    """Job/PER record for the given locator does not exist, or its
    required derived field (`original_commit_sha`/`ecp_id`) cannot be
    resolved from the live record (HSCE-REQ-013/016, attacks 20/21).
    Raised before any RAE Binding lookup and before any hardware
    provider is touched."""

    error_type = "operation_not_found"


class DecisionUnavailableError(HATPSigningCeremonyError):
    error_type = "decision_unavailable"


class BindingUnavailableError(HATPSigningCeremonyError):
    """No matching, non-superseded, non-revoked RAE Binding exists for
    the given operation locator, or more than one candidate remains
    ambiguous after supersession-aware selection (HSCE-REQ-020/021).
    Raised before any hardware provider is touched."""

    error_type = "binding_unavailable"


class NoAuthorizedSignerError(HATPSigningCeremonyError):
    error_type = "no_authorized_signer"


class ProviderUnavailableError(HATPSigningCeremonyError):
    error_type = "provider_unavailable"


class HardwareDeviceFaultError(HATPSigningCeremonyError):
    error_type = "hardware_device_fault"


class HumanSigningCancelledError(HATPSigningCeremonyError):
    """The human cancelled the touch/PIN operation, it timed out, or
    declined the mandatory blind-touch-defense preview confirmation
    (HSCE-REQ-029, HSCE-REQ-071). No evidence is ever persisted for this
    outcome."""

    error_type = "human_signing_cancelled"


class ProviderSignatureFailureError(HATPSigningCeremonyError):
    error_type = "provider_signature_failure"


class EvidenceSerializationFailureError(HATPSigningCeremonyError):
    """Either envelope construction failed structurally, or the mandatory
    post-sign TOCTOU recheck (HSCE-REQ-070) found the Decision/Binding/
    operation context changed since the pre-touch preview -- in both
    cases the freshly-produced provider assertion is discarded, no
    evidence is persisted, and no automatic re-sign is attempted; a
    fresh ceremony invocation is required."""

    error_type = "evidence_serialization_failure"


# ═══════════════════════════════════════════════════════════════════════════
# Signing context -- Wave C (HSCE-REQ-013, HSCE-REQ-016, HSCE-REQ-018,
# HSCE-REQ-020/021)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class HATPRollbackSigningContext:
    """Canonical *source* identifiers resolved once from live state
    (HSCE-REQ-018/020), never duplicating the proof's own shape. This is
    the exact set of fields the mandatory post-sign TOCTOU recheck
    (HSCE-REQ-070) compares between the pre-touch snapshot (context A)
    and the post-touch snapshot (context B): equal-by-value on every
    field here means the context has not changed; `frozen=True`
    dataclass equality is therefore the entire TOCTOU comparison, no
    separate field-by-field comparator is needed or maintained."""

    rollback_site: RollbackSite
    operation_reference: Union[Ag3OperationReference, Ag5OperationReference]
    binding_id: str
    binding_digest: str
    decision_record_id: str
    decision_record_digest: str
    repository_id: str


def _parse_binding_created_at(value: str) -> Optional[datetime]:
    """Module-local timestamp parser (matching this repository's own
    per-module timestamp-handling duplication convention, e.g.
    `human_approval_trusted_provenance.py::_parse_iso_timestamp`,
    `rollback_approval_evidence.py::_parse_iso_timestamp`) used only to
    order RAE Binding candidates for supersession-aware selection
    (HSCE-REQ-020). Never used to construct or validate a HATP proof
    field -- `issued_at` generation is entirely separate (§ below)."""

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


def _rae_site(site: RollbackSite) -> _RaeRollbackSite:
    return _RaeRollbackSite.AG3 if site is RollbackSite.AG3 else _RaeRollbackSite.AG5


def _resolve_ag3_operation(root: HarnessPath, job_id: str) -> Tuple[Ag3OperationReference, _RaeAg3OperationReference]:
    """HSCE-REQ-013: `original_commit_sha` is read from the live job
    record via `agent.py::build_rollback_review` -- the exact same live
    record `execute_rollback` already reads for its own preconditions
    (never a second, independent job-file reader). Missing job, malformed
    job, or an unresolvable/malformed `original_commit_sha` all fail
    `operation_not_found` (attack 21), before any RAE Binding lookup and
    before any hardware provider is touched."""

    try:
        review_data = build_rollback_review(root, job_id)
    except ValueError as exc:
        raise OperationNotFoundError(f"AG3 job {job_id!r} could not be resolved: {exc}") from exc

    review = review_data.get("rollback_review") or {}
    original_commit_sha = review.get("original_commit_sha") or ""
    if not original_commit_sha:
        raise OperationNotFoundError(
            f"AG3 job {job_id!r} has no resolvable original_commit_sha on its live job record"
        )

    try:
        hatp_reference = Ag3OperationReference(job_id=job_id, original_commit_sha=original_commit_sha)
    except HATPProofError as exc:
        raise OperationNotFoundError(
            f"AG3 job {job_id!r} original_commit_sha is not a resolvable commit identity: {exc}"
        ) from exc

    rae_reference = _RaeAg3OperationReference(job_id=job_id, original_commit_sha=original_commit_sha)
    return hatp_reference, rae_reference


def _resolve_ag5_operation(root: HarnessPath, per_id: str) -> Tuple[Ag5OperationReference, _RaeAg5OperationReference]:
    """HSCE-REQ-016: `ecp_id` is read directly from the live
    `PromotionExecutionRecord` via `agent.py::lookup_promotion_execution_
    record` -- the exact same live record `build_rollback_execution`
    already reads for its own preconditions. Missing PER, or a missing/
    unresolvable `ecp_id`, both fail `operation_not_found` (attack 20),
    before any RAE Binding lookup and before any hardware provider is
    touched."""

    per = lookup_promotion_execution_record(root, per_id)
    if per is None:
        raise OperationNotFoundError(f"AG5 PER {per_id!r} not found")

    ecp_id = per.get("ecp_id") or ""
    if not ecp_id:
        raise OperationNotFoundError(f"AG5 PER {per_id!r} has no resolvable ecp_id on its live record")

    try:
        hatp_reference = Ag5OperationReference(per_id=per_id, ecp_id=ecp_id)
    except HATPProofError as exc:
        raise OperationNotFoundError(
            f"AG5 PER {per_id!r} ecp_id is not a resolvable operation identity: {exc}"
        ) from exc

    rae_reference = _RaeAg5OperationReference(per_id=per_id, ecp_id=ecp_id)
    return hatp_reference, rae_reference


def _rollback_approval_evidence_store(root: HarnessPath) -> RollbackApprovalEvidenceStore:
    """RAE-001's own evidence store, rooted explicitly under this
    ceremony's `root` (never an ambiguous CWD-relative default) -- reused
    read-only via its public `list_bindings_with_keys()`/`is_revoked()`
    surface, never RAE's own mutation functions."""

    return RollbackApprovalEvidenceStore(root=root.path / ".pcae" / "rollback-approval-evidence")


def _resolve_binding(
    root: HarnessPath,
    *,
    site: RollbackSite,
    rae_operation_reference: Union[_RaeAg3OperationReference, _RaeAg5OperationReference],
) -> RollbackApprovalBinding:
    """HSCE-REQ-020/021: locate the exact current `RollbackApprovalBinding`
    for this operation by scanning RAE's own `list_bindings_with_keys()`
    and structurally matching `rollback_site` + operation reference --
    never "pick the newest" across genuinely distinct operations. Revoked
    Bindings are excluded outright. Among remaining candidates matching
    this *one already-identified* operation, supersession-aware selection
    picks the strictly-latest `created_at`; a tie, or a candidate with an
    unparseable `created_at`, is ambiguous and fails closed
    (`binding_unavailable`) rather than guessing -- never an implicit
    human-disambiguation prompt."""

    store = _rollback_approval_evidence_store(root)
    rae_site = _rae_site(site)

    candidates = []
    for _key, binding in store.list_bindings_with_keys():
        if binding.rollback_site != rae_site:
            continue
        if binding.rollback_operation_reference != rae_operation_reference:
            continue
        if store.is_revoked(binding.evidence_id):
            continue
        candidates.append(binding)

    if not candidates:
        raise BindingUnavailableError(
            f"no matching, non-revoked RollbackApprovalBinding found for site={rae_site.value!r} "
            f"operation_reference={rae_operation_reference!r}"
        )
    if len(candidates) == 1:
        return candidates[0]

    parsed = [(_parse_binding_created_at(binding.created_at), binding) for binding in candidates]
    if any(created_at is None for created_at, _binding in parsed):
        raise BindingUnavailableError(
            "ambiguous RollbackApprovalBinding selection: one or more candidates has an "
            "unparseable created_at timestamp"
        )
    latest_created_at = max(created_at for created_at, _binding in parsed)
    winners = [binding for created_at, binding in parsed if created_at == latest_created_at]
    if len(winners) != 1:
        raise BindingUnavailableError(
            "ambiguous RollbackApprovalBinding selection: multiple candidates tie for the "
            "latest created_at"
        )
    return winners[0]


def resolve_signing_context(
    root: HarnessPath,
    *,
    site: RollbackSite,
    job_id: Optional[str] = None,
    per_id: Optional[str] = None,
) -> HATPRollbackSigningContext:
    """Resolve every canonical signing-context field from live state
    (HSCE-REQ-018), for exactly one of AG3 (`job_id`) or AG5 (`per_id`).
    No hardware provider call occurs anywhere in this function
    (HSCE-REQ-021/025's "no hardware touch before all canonical context
    resolves"). Called twice by `sign_rollback_evidence` -- once to
    produce the pre-touch preview snapshot, once to produce the post-
    touch TOCTOU recheck snapshot (HSCE-REQ-069/070)."""

    _validate_locator_arguments(site, job_id=job_id, per_id=per_id)

    if site is RollbackSite.AG3:
        hatp_reference, rae_reference = _resolve_ag3_operation(root, job_id)  # type: ignore[arg-type]
    else:
        hatp_reference, rae_reference = _resolve_ag5_operation(root, per_id)  # type: ignore[arg-type]

    binding = _resolve_binding(root, site=site, rae_operation_reference=rae_reference)

    decision_record_id = binding.governance_record_reference.record_id
    decision_record_digest = binding.governance_record_reference.record_digest
    if not decision_record_id or not decision_record_digest:
        raise DecisionUnavailableError(
            f"RollbackApprovalBinding {binding.evidence_id!r} has no resolvable Decision reference"
        )

    try:
        identity = read_repository_identity(root)
    except RepositoryIdentityError as exc:
        raise RepositoryIdentityUnavailableError(f"repository identity could not be read: {exc}") from exc
    if identity is None:
        raise RepositoryIdentityUnavailableError("no repository identity provisioned for this deployment")

    return HATPRollbackSigningContext(
        rollback_site=site,
        operation_reference=hatp_reference,
        binding_id=binding.evidence_id,
        binding_digest=binding.content_digest,
        decision_record_id=decision_record_id,
        decision_record_digest=decision_record_digest,
        repository_id=identity.repository_instance_id,
    )


def _validate_locator_arguments(site: RollbackSite, *, job_id: Optional[str], per_id: Optional[str]) -> None:
    if not isinstance(site, RollbackSite):
        raise ValueError(f"site must be a RollbackSite member, got {site!r}")
    if site is RollbackSite.AG3:
        if not job_id:
            raise ValueError("site=AG3 requires a non-empty job_id")
        if per_id:
            raise ValueError("site=AG3 must not receive per_id")
    else:
        if not per_id:
            raise ValueError("site=AG5 requires a non-empty per_id")
        if job_id:
            raise ValueError("site=AG5 must not receive job_id")


# ═══════════════════════════════════════════════════════════════════════════
# Signing-ceremony orchestration -- Wave D (HSCE-REQ-019, HSCE-REQ-022..030,
# HSCE-REQ-067..071)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class HATPSigningPreview:
    """Presentation-only blind-touch-defense preview (HSCE-REQ-071): the
    full reconstructed canonical operation payload, shown to the human
    before any hardware touch is requested. No authority-bearing field
    exists here -- no `approved`/`allowed`/`verified`/`operational`
    field, by design (mirrors `HATPSignedEvidenceEnvelope`'s own
    no-authority-field discipline, 149O.12A)."""

    rollback_site: RollbackSite
    operation_reference: Union[Ag3OperationReference, Ag5OperationReference]
    repository_id: str
    decision_record_id: str
    decision_record_digest: str
    binding_id: str
    binding_digest: str
    principal_id: str
    signer_key_id: str
    provider_profile: str


@dataclass(frozen=True)
class HATPSigningResult:
    """`sign_rollback_evidence`'s sole success return type. Never a bare
    boolean, never an `approved`/`permission`/`executed` field anywhere
    on this type (HSCE-REQ-065/066's success-output discipline, applied
    here at the core-orchestrator layer even though no CLI exists yet)."""

    evidence_id: str
    path: Path
    idempotent: bool


@dataclass(frozen=True)
class HATPSignerResolution:
    """Immutable semantic snapshot of signer-resolution authority state.

    Equality covers the complete records and their repository/root/provider
    context, not object identity and not only the principal/signer tuple.
    Re-resolving and comparing this value immediately before publication
    therefore detects both invalid cross-record relationships and material
    same-identity registry changes.
    """

    repository_id: str
    canonical_deployment_root: str
    provider_profile: str
    binding: DeploymentBinding
    signer: SignerRecord
    principal: PrincipalRecord
    credential: HardwareCredentialRecord

    @property
    def principal_id(self) -> str:
        return self.binding.principal_id

    @property
    def signer_key_id(self) -> str:
        return self.binding.signer_key_id


def _default_clock() -> datetime:
    """Production default clock (HSCE-REQ-068): internal, wall-clock,
    UTC, called exactly once per signing attempt, immediately before
    proof construction -- never `datetime.now()` called ad hoc elsewhere
    in this module."""

    return datetime.now(timezone.utc)


def _issued_at_string(instant: datetime) -> str:
    """Produce a timezone-aware, whole-millisecond ISO-8601 string from
    `instant` -- a valid *input* to `HumanApprovalProvenanceProof`'s own
    `issued_at` field, which performs the actual canonical rendering
    (`_require_issued_at`/`_canonical_timestamp_string`,
    `human_approval_trusted_provenance.py`) at construction time. This
    function does not reimplement that canonical renderer; it only
    truncates microsecond precision down to a whole millisecond so the
    value construction accepts is never rejected for sub-millisecond
    precision it did not intend to carry (Python 3.9-compatible: uses
    only `datetime.isoformat`/`replace`, no `fromisoformat` extension
    dependence)."""

    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    instant = instant.astimezone(timezone.utc)
    truncated_microsecond = (instant.microsecond // 1000) * 1000
    return instant.replace(microsecond=truncated_microsecond).isoformat()


def _default_provider_factory() -> HATPHardwareSigner:
    """The sole production provider-resolution path (HSCE-REQ-022):
    `create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)`. No
    Wave-4 deterministic test-fixture provider class is imported by, or
    reachable from, this function."""

    return create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)  # type: ignore[return-value]


def _default_trust_store_factory() -> HATPTrustStore:
    """The sole production trust-store-resolution path (HSCE-REQ-023)."""

    return HATPTrustStore.production()


def _default_confirm(preview: HATPSigningPreview) -> bool:
    """Production default confirmation gate (HSCE-REQ-071's "blind-touch
    defense"): renders every preview field and requires an explicit,
    affirmative human response before any hardware touch is requested.
    This is an internal orchestrator default only -- no CLI argument
    parsing, output-formatting convention, or subcommand registration is
    defined here; that remains 149O.12C's exclusive scope."""

    print("HATP signing ceremony -- review the operation below before the hardware touch:")
    print(f"  rollback_site:          {preview.rollback_site.value}")
    print(f"  operation_reference:    {preview.operation_reference!r}")
    print(f"  repository_id:          {preview.repository_id}")
    print(f"  decision_record_id:     {preview.decision_record_id}")
    print(f"  decision_record_digest: {preview.decision_record_digest}")
    print(f"  binding_id:             {preview.binding_id}")
    print(f"  binding_digest:         {preview.binding_digest}")
    print(f"  principal_id:           {preview.principal_id}")
    print(f"  signer_key_id:          {preview.signer_key_id}")
    print(f"  provider_profile:       {preview.provider_profile}")
    response = input("Proceed with hardware signing? [y/N]: ")
    return response.strip().lower() in ("y", "yes")


def _default_hardware_credential_store_factory() -> HATPHardwareCredentialStore:
    """The sole production hardware-credential-registry-resolution path
    (HSCE-REQ-080 step 5), mirroring `_default_trust_store_factory`'s own
    discipline: production code always resolves
    `HATPHardwareCredentialStore.production()`; only this module's own
    tests supply a deterministic fake directly to `sign_rollback_
    evidence`'s keyword-only `hardware_credential_store_factory`
    parameter (below) -- there is no CLI flag or environment variable
    that reaches this factory (mirrors HSCE-REQ-022/023's existing
    no-override discipline for the hardware-provider/trust-store
    factories)."""

    return HATPHardwareCredentialStore.production()


def _resolve_deployment_binding_signer(
    root: HarnessPath,
    trust_store: HATPTrustStore,
    *,
    repository_id: str,
    provider_profile: str,
    hardware_credential_store_factory: Callable[[], HATPHardwareCredentialStore] = _default_hardware_credential_store_factory,
) -> HATPSignerResolution:
    """HSCE-REQ-080 (v1.3; Model-B BF-1 and cross-record repair):
    `principal_id`/`signer_key_id`
    are resolved exclusively from this repository's own durable
    `DeploymentBinding` (`HATPTrustStore.resolve_deployment_authorization`,
    the frozen Layer-1 `repository_id` + Layer-2 `canonical_deployment_
    root` match, HATP-REQ-057-063) -- **never** from the hardware
    provider's own credential exchange (which Phase 149O.20L.7O.2F.1
    found FIDO2 cannot ever satisfy, BF-1). Registry identity resolution
    is distinct from cryptographic possession proof (HSCE-REQ-082): the
    hardware authenticator still proves possession/signs, once, at
    `request_signature` time (below); this function never asks the
    provider who it is.

    Every check below fails closed as `no_authorized_signer`
    (HSCE-REQ-024/080), before any hardware touch:

    1. No `DeploymentBinding` for this repository/root.
    2. The binding's `provider_profile` does not match the resolved
       production provider's own profile.
    3. No matching `active` `SignerRecord`, or its signer/principal/
       provider relationships conflict with the binding.
    4. No matching `active` `PrincipalRecord`, or its identity conflicts
       with the binding.
    5. No matching `active` `HardwareCredentialRecord`, or its signer/
       provider relationships conflict with the binding.

    Multiple-signer behavior (HSCE-REQ-081) is fully determined by
    `DeploymentBinding`'s own existing structural uniqueness: the
    registry stores at most one `DeploymentBinding` per `repository_id`
    -- there is no "pick one of several" step here to get wrong."""

    try:
        canonical_deployment_root = resolve_canonical_deployment_root(Path(root.path))
    except (OSError, RuntimeError, ValueError) as exc:
        raise NoAuthorizedSignerError(
            f"canonical_deployment_root could not be resolved for signer resolution: {exc}"
        ) from exc

    try:
        binding: Optional[DeploymentBinding] = trust_store.resolve_deployment_authorization(
            repository_id=repository_id, canonical_deployment_root=canonical_deployment_root
        )
    except Exception as exc:  # noqa: BLE001 - any registry access failure fails closed
        raise NoAuthorizedSignerError(f"protected trust store unavailable: {exc}") from exc

    if binding is None:
        raise NoAuthorizedSignerError(
            f"no active DeploymentBinding exists for repository_id={repository_id!r} "
            f"canonical_deployment_root={canonical_deployment_root!r}; signing-time signer identity is "
            "resolved exclusively from this durable registry binding, never from the hardware provider"
        )
    if binding.provider_profile != provider_profile:
        raise NoAuthorizedSignerError(
            f"DeploymentBinding provider_profile={binding.provider_profile!r} does not match the resolved "
            f"production provider profile {provider_profile!r}"
        )

    try:
        signer = trust_store.lookup_signer(binding.signer_key_id)
    except Exception as exc:  # noqa: BLE001 - any registry access failure fails closed
        raise NoAuthorizedSignerError(f"protected trust store unavailable: {exc}") from exc
    if signer is None or signer.status != "active":
        raise NoAuthorizedSignerError(
            f"signer_key_id {binding.signer_key_id!r} bound by this repository's DeploymentBinding is not "
            "an active authorized signer"
        )
    if signer.signer_key_id != binding.signer_key_id:
        raise NoAuthorizedSignerError(
            f"SignerRecord signer_key_id={signer.signer_key_id!r} does not match DeploymentBinding "
            f"signer_key_id={binding.signer_key_id!r}"
        )
    if signer.principal_id != binding.principal_id:
        raise NoAuthorizedSignerError(
            f"SignerRecord principal_id={signer.principal_id!r} does not match DeploymentBinding "
            f"principal_id={binding.principal_id!r}"
        )
    if signer.provider_profile != provider_profile:
        raise NoAuthorizedSignerError(
            f"SignerRecord provider_profile={signer.provider_profile!r} does not match the resolved "
            f"production provider profile {provider_profile!r}"
        )

    try:
        principal = trust_store.lookup_principal(binding.principal_id)
    except Exception as exc:  # noqa: BLE001 - any registry access failure fails closed
        raise NoAuthorizedSignerError(f"protected trust store unavailable: {exc}") from exc
    if principal is None or principal.status != "active":
        raise NoAuthorizedSignerError(
            f"principal_id {binding.principal_id!r} bound by this repository's DeploymentBinding is not active"
        )
    if principal.principal_id != binding.principal_id:
        raise NoAuthorizedSignerError(
            f"PrincipalRecord principal_id={principal.principal_id!r} does not match DeploymentBinding "
            f"principal_id={binding.principal_id!r}"
        )

    try:
        hardware_store = hardware_credential_store_factory()
        credential = hardware_store.lookup_credential(binding.signer_key_id)
    except Exception as exc:  # noqa: BLE001 - any registry access failure fails closed
        raise NoAuthorizedSignerError(f"hardware credential registry unavailable: {exc}") from exc
    if credential is None or credential.status != "active":
        raise NoAuthorizedSignerError(
            f"hardware credential {binding.signer_key_id!r} has no active HardwareCredentialRecord"
        )
    if credential.signer_key_id != binding.signer_key_id:
        raise NoAuthorizedSignerError(
            f"HardwareCredentialRecord signer_key_id={credential.signer_key_id!r} does not match "
            f"DeploymentBinding signer_key_id={binding.signer_key_id!r}"
        )
    if credential.provider_profile != provider_profile:
        raise NoAuthorizedSignerError(
            f"hardware credential {binding.signer_key_id!r} provider_profile={credential.provider_profile!r} "
            f"does not match the resolved production provider profile {provider_profile!r}"
        )

    return HATPSignerResolution(
        repository_id=repository_id,
        canonical_deployment_root=canonical_deployment_root,
        provider_profile=provider_profile,
        binding=binding,
        signer=signer,
        principal=principal,
        credential=credential,
    )


def sign_rollback_evidence(
    root: HarnessPath,
    *,
    site: RollbackSite,
    job_id: Optional[str] = None,
    per_id: Optional[str] = None,
    clock: Callable[[], datetime] = _default_clock,
    provider_factory: Callable[[], HATPHardwareSigner] = _default_provider_factory,
    trust_store_factory: Callable[[], HATPTrustStore] = _default_trust_store_factory,
    hardware_credential_store_factory: Callable[
        [], HATPHardwareCredentialStore
    ] = _default_hardware_credential_store_factory,
    confirm: Callable[[HATPSigningPreview], bool] = _default_confirm,
) -> HATPSigningResult:
    """Core, test-injectable signing-ceremony orchestrator (149O.11 plan
    §12.1). The keyword-only `clock`/`provider_factory`/`trust_store_
    factory`/`confirm` parameters default to production implementations;
    only `tests/test_hatp_signing_ceremony.py` supplies deterministic
    fakes directly to this function. `production_sign_rollback_evidence` (below) is
    the zero-override production entry point that always calls this
    function with every default left in place -- it is the only
    production-reachable call site.

    Ordering (HSCE-REQ-021/025/069-071, "blind-touch defense" + TOCTOU):

    1. Resolve context A (`resolve_signing_context`) -- no hardware touch.
    2. Resolve signer identity from this repository's own durable
       `DeploymentBinding` (HSCE-REQ-080, v1.2 -- never from the hardware
       provider) and render the preview.
    3. Require explicit human confirmation of the preview
       (`human_signing_cancelled` if declined) -- still no hardware touch.
    4. Generate `issued_at`, construct the proof, and invoke the
       provider's `request_signature` exactly once -- the sole physical
       hardware touch this function ever performs, and the only call
       site of `request_signature` in this module.
    5. Re-resolve context B and compare against context A on every
       HSCE-required stable field. Any mismatch discards the signed
       assertion and fails `evidence_serialization_failure` -- no
       publish, no second provider call, no automatic re-sign.
    6. Build the envelope (`build_hatp_signed_evidence_envelope`, 149O.12A)
       from the untouched original proof and publish it
       (`HATPEvidenceStore.publish`, 149O.12A) -- `hatp_evidence_store.py`'s
       own `EvidenceConflictError`/`EvidencePersistenceFailureError`
       propagate unmodified.
    """

    context_a = resolve_signing_context(root, site=site, job_id=job_id, per_id=per_id)

    try:
        trust_store = trust_store_factory()
    except HATPTrustStoreError as exc:
        raise NoAuthorizedSignerError(f"protected trust store unavailable: {exc}") from exc

    try:
        provider = provider_factory()
    except HATPProviderUnavailableError as exc:
        raise ProviderUnavailableError(str(exc)) from exc

    signer_resolution_a = _resolve_deployment_binding_signer(
        root,
        trust_store,
        repository_id=context_a.repository_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        hardware_credential_store_factory=hardware_credential_store_factory,
    )
    principal_id = signer_resolution_a.principal_id
    signer_key_id = signer_resolution_a.signer_key_id

    preview = HATPSigningPreview(
        rollback_site=context_a.rollback_site,
        operation_reference=context_a.operation_reference,
        repository_id=context_a.repository_id,
        decision_record_id=context_a.decision_record_id,
        decision_record_digest=context_a.decision_record_digest,
        binding_id=context_a.binding_id,
        binding_digest=context_a.binding_digest,
        principal_id=principal_id,
        signer_key_id=signer_key_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
    )

    if not confirm(preview):
        raise HumanSigningCancelledError("signing preview was not confirmed")

    issued_at = _issued_at_string(clock())

    proof = HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id=principal_id,
        signer_key_id=signer_key_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        repository_id=context_a.repository_id,
        decision_record_id=context_a.decision_record_id,
        decision_record_digest=context_a.decision_record_digest,
        binding_id=context_a.binding_id,
        binding_digest=context_a.binding_digest,
        rollback_site=context_a.rollback_site,
        operation_reference=context_a.operation_reference,
        issued_at=issued_at,
    )

    canonical_payload = canonicalize_hatp_proof_payload(proof)

    try:
        assertion = provider.request_signature(
            canonical_payload,
            signer_key_id=signer_key_id,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
        )
    except HATPProviderCancelledError as exc:
        raise HumanSigningCancelledError(str(exc)) from exc
    except HATPProviderDeviceError as exc:
        raise HardwareDeviceFaultError(str(exc)) from exc
    except HATPProviderUnavailableError as exc:
        raise ProviderUnavailableError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - any other provider failure fails closed
        raise ProviderSignatureFailureError(str(exc)) from exc

    # HSCE-REQ-069/070: post-sign TOCTOU recheck. Re-resolve context from
    # live state and compare against the pre-touch snapshot on every
    # HSCE-required stable field before any envelope is built or
    # published. No automatic re-sign occurs on mismatch -- a fresh
    # ceremony invocation is required.
    context_b = resolve_signing_context(root, site=site, job_id=job_id, per_id=per_id)
    if context_a != context_b:
        raise EvidenceSerializationFailureError(
            "Decision/Binding/operation context changed since the pre-touch preview; "
            "the signed candidate has been discarded, no evidence was persisted"
        )

    # HSCE-REQ-083 (v1.3): the pre-touch signer authority state was resolved
    # from durable, mutable registry state (HSCE-REQ-080), not from an
    # immutable per-invocation hardware response -- unlike v1.1, that
    # state can itself change between the preview and the touch. Re-run
    # the identical resolution and compare the complete immutable
    # semantic snapshot; any difference is treated identically to any
    # other post-touch mismatch.
    try:
        signer_resolution_b = _resolve_deployment_binding_signer(
            root,
            trust_store,
            repository_id=context_a.repository_id,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            hardware_credential_store_factory=hardware_credential_store_factory,
        )
    except HATPSigningCeremonyError as exc:
        raise EvidenceSerializationFailureError(
            f"signer authority state became unresolvable since the pre-touch preview; the signed candidate has "
            f"been discarded, no evidence was persisted: {exc}"
        ) from exc
    if signer_resolution_b != signer_resolution_a:
        raise EvidenceSerializationFailureError(
            "DeploymentBinding-resolved signer authority state changed since the pre-touch preview; "
            "the signed candidate has been discarded, no evidence was persisted"
        )

    envelope = build_hatp_signed_evidence_envelope(proof, assertion.evidence)
    store = HATPEvidenceStore(root)
    publication: HATPEvidencePublicationResult = store.publish(envelope)

    return HATPSigningResult(
        evidence_id=publication.evidence_id,
        path=publication.path,
        idempotent=publication.idempotent,
    )


def production_sign_rollback_evidence(
    root: HarnessPath,
    *,
    site: RollbackSite,
    job_id: Optional[str] = None,
    per_id: Optional[str] = None,
) -> HATPSigningResult:
    """The zero-override production entry point (F-2 non-regression,
    mirroring `hatp_ag_authority.py`'s own zero-override adapters). This
    function's signature carries no `provider`/`trust_store`/`clock`/
    `confirm` parameter at all -- there is structurally nothing here for
    a production caller to substitute a test provider or an arbitrary
    trust store with; every dependency is resolved internally, always
    through `sign_rollback_evidence`'s production defaults. A future CLI
    handler (149O.12C, `commands/hatp.py`) is expected to call only this
    function, never `sign_rollback_evidence` directly with overrides."""

    return sign_rollback_evidence(root, site=site, job_id=job_id, per_id=per_id)


__all__ = [
    "HATPSigningCeremonyError",
    "RepositoryIdentityUnavailableError",
    "OperationNotFoundError",
    "DecisionUnavailableError",
    "BindingUnavailableError",
    "NoAuthorizedSignerError",
    "ProviderUnavailableError",
    "HardwareDeviceFaultError",
    "HumanSigningCancelledError",
    "ProviderSignatureFailureError",
    "EvidenceSerializationFailureError",
    "HATPRollbackSigningContext",
    "HATPSigningPreview",
    "HATPSigningResult",
    "HATPSignerResolution",
    "resolve_signing_context",
    "sign_rollback_evidence",
    "production_sign_rollback_evidence",
]
