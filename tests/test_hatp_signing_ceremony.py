"""Phase 149O.12B, Waves C + D -- proof-context resolver + signing-
ceremony orchestrator tests for `pcae.core.hatp_signing_ceremony`.

Real filesystem throughout: job/PER records, RAE Bindings, repository
identity, and the resulting `.pcae/hatp-evidence/` envelopes are all
real files under `tmp_path`, exercised through the identical public
`agent.py`/`rollback_approval_evidence.py`/`repository_identity.py`
APIs production code uses. Only the hardware provider and trust store
are deterministic in-memory fakes -- this module's own production
defaults (`create_production_hardware_provider`, `HATPTrustStore.
production()`) are never invoked by this suite (mirrors 149O.12A's own
real-filesystem-only, no-hardware test discipline).
"""
from __future__ import annotations

import dataclasses
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pytest

from pcae.core import hatp_signing_ceremony as ceremony
from pcae.core import rollback_approval_evidence as rae
from pcae.core.agent import store_promotion_execution_record
from pcae.core.hatp_bootstrap import SignerRecord
from pcae.core.hatp_evidence_store import (
    EvidenceConflictError,
    EvidencePersistenceFailureError,
    HATPEvidenceStore,
)
from pcae.core.hatp_providers import (
    HATPProviderCancelledError,
    HATPProviderDeviceError,
    HATPProviderUnavailableError,
    ProviderAssertion,
)
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    RollbackSite,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity
from pcae.governance.publication.storage import PublicationRecordStore

_PLACEHOLDER_DIGEST = "a" * 64
_REMOTE_JOBS_OUTPUT_DIR = Path(".pcae") / "remote" / "jobs"


@pytest.fixture(autouse=True)
def _chgr_publication_z_suffix_workaround(monkeypatch):
    """Test-layer-only workaround for a pre-existing, unrelated defect in
    `pcae.governance.publication.coordinator._parse_timestamp` (Phase
    144C): unlike this module's own `rollback_approval_evidence.py::
    _parse_iso_timestamp`, it calls bare `datetime.fromisoformat(value)`
    without normalizing a trailing `Z`, which `datetime.fromisoformat`
    only accepts starting in Python 3.11. On this repository's
    minimum-supported Python 3.9 (`.venv`), every real `create_
    rollback_approval_decision` call -- including many pre-existing,
    already-merged test files unrelated to this phase (confirmed via
    `git stash -u` A/B: identical failures present on `main` before this
    phase's changes) -- raises `RollbackApprovalDecisionCreationError`
    from inside `PublicationCoordinator._validate_authorization_
    freshness`. Fixing `coordinator.py` is out of this phase's scope
    (149O.12B may add exactly one new file, `hatp_signing_ceremony.py`);
    this fixture patches only the imported reference this test module's
    own fixtures exercise, for the duration of this test module only, so
    this phase's own new tests are deterministically green on Python 3.9
    without touching any production file."""

    from pcae.governance.publication import coordinator as _coordinator

    def _z_tolerant_parse_timestamp(value: str) -> datetime:
        text = value[:-1] + "+00:00" if isinstance(value, str) and value.endswith("Z") else value
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    monkeypatch.setattr(_coordinator, "_parse_timestamp", _z_tolerant_parse_timestamp)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures / builders
# ═══════════════════════════════════════════════════════════════════════════


def _root(tmp_path: Path) -> HarnessPath:
    root = HarnessPath(tmp_path)
    ensure_repository_identity(root)
    return root


def _write_job(root: HarnessPath, job_id: str, *, commit_sha: Optional[str] = "c" * 40) -> None:
    jobs_dir = root.path / _REMOTE_JOBS_OUTPUT_DIR
    jobs_dir.mkdir(parents=True, exist_ok=True)
    payload = {"requested_agent": "codex", "commit_sha": commit_sha}
    (jobs_dir / f"{job_id}.json").write_text(json.dumps(payload))


_PXR_STORE_DIR = Path(".pcae") / "promotion-executions"


def _write_per(root: HarnessPath, per_id: str, *, ecp_id: Optional[str] = "ecp-1") -> None:
    record = {
        "per_id": per_id,
        "epr_id": "epr-1",
        "ecp_id": ecp_id if ecp_id is not None else "",
        "prompt_id": "prompt-1",
        "started_at": "2026-08-04T10:00:00.000Z",
        "status": "completed",
        "file_results": [],
        "rollback_executed": False,
        "execution_allowed": False,
    }
    if ecp_id is not None:
        # The canonical, validated write path (`store_promotion_execution_
        # record`) for the ordinary, well-formed case.
        result = store_promotion_execution_record(root, record)
        assert result["stored"], result["errors"]
    else:
        # `store_promotion_execution_record` itself rejects a missing
        # `ecp_id` at write time (`_pxr_validate`) -- to exercise the
        # "PER exists but ecp_id is unresolvable" resolver attack (20),
        # the malformed record is written directly, exactly as a real
        # live record with a missing field would be read by `lookup_
        # promotion_execution_record` (which performs no such
        # validation on read).
        store_dir = root.path / _PXR_STORE_DIR
        store_dir.mkdir(parents=True, exist_ok=True)
        (store_dir / f"{per_id}.json").write_text(json.dumps(record))


def _rae_store(root: HarnessPath) -> rae.RollbackApprovalEvidenceStore:
    return rae.RollbackApprovalEvidenceStore(root=root.path / ".pcae" / "rollback-approval-evidence")


def _identity_evidence() -> dict:
    return {
        "evidence_kind": "typed_confirmation_only",
        "identifier": "human-1",
        "captured_at": "2026-08-04T10:00:00Z",
    }


def _publish_decision(pub_store: PublicationRecordStore, subject: str) -> rae.RollbackApprovalDecisionRef:
    return rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject=subject,
        decision_maker_identity_evidence=_identity_evidence(),
        operator_id="alice",
        publication_store=pub_store,
    )


def _repo_state() -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha="deadbeef", branch="main")


def _make_ag3_binding(
    root: HarnessPath, pub_store: PublicationRecordStore, *, job_id: str, commit_sha: str, subject: Optional[str] = None
) -> rae.RollbackApprovalBinding:
    ref = _publish_decision(pub_store, subject or f"AG3 rollback job_id={job_id} commit={commit_sha}")
    return rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id=job_id, original_commit_sha=commit_sha),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_store.root,
        evidence_store=_rae_store(root),
    )


def _make_ag5_binding(
    root: HarnessPath, pub_store: PublicationRecordStore, *, per_id: str, ecp_id: str, subject: Optional[str] = None
) -> rae.RollbackApprovalBinding:
    ref = _publish_decision(pub_store, subject or f"AG5 rollback per_id={per_id} ecp_id={ecp_id}")
    return rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG5,
        rollback_operation_reference=rae.Ag5OperationReference(per_id=per_id, ecp_id=ecp_id),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_store.root,
        evidence_store=_rae_store(root),
    )


def _manual_binding(
    *,
    site: rae.RollbackSite,
    operation_reference,
    created_at: datetime,
    decision_record_id: str = "decision-1",
    expires_hours: int = 24,
) -> rae.RollbackApprovalBinding:
    """A hand-constructed Binding (bypassing the full CHGR-Decision
    pipeline) for supersession/ambiguity tests that need precise control
    over `created_at`, which `create_rollback_approval_binding`'s own
    internal clock does not expose to callers outside `rollback_approval_
    evidence.py`'s own test files."""

    evidence_id = f"rae-{uuid.uuid4().hex}"
    created_str = created_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    expires_str = (created_at + timedelta(hours=expires_hours)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return rae.RollbackApprovalBinding(
        evidence_id=evidence_id,
        governance_record_reference=rae.RollbackApprovalDecisionRef(
            record_id=decision_record_id, record_digest=_PLACEHOLDER_DIGEST
        ),
        rollback_site=site,
        rollback_operation_reference=operation_reference,
        task_id=None,
        repository_state_binding=_repo_state(),
        created_at=created_str,
        expires_at=expires_str,
        state=rae.BindingState.ISSUED,
        decision=rae.BindingDecision.APPROVE,
        replay_binding=f"raerep-{uuid.uuid4().hex}",
        content_digest=_PLACEHOLDER_DIGEST,
    )


def _active_signer(signer_key_id: str = "signer-1", principal_id: str = "principal-1") -> SignerRecord:
    return SignerRecord(
        signer_key_id=signer_key_id,
        principal_id=principal_id,
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        status="active",
    )


class FakeTrustStore:
    """Duck-typed fake exposing only `lookup_signer`, the sole
    `HATPTrustStore` method `hatp_signing_ceremony.py` calls."""

    def __init__(self, signers=None, *, raise_on_lookup: Optional[BaseException] = None):
        self._signers = signers or {}
        self._raise_on_lookup = raise_on_lookup

    def lookup_signer(self, signer_key_id: str):
        if self._raise_on_lookup is not None:
            raise self._raise_on_lookup
        return self._signers.get(signer_key_id)


class FakeHardwareProvider:
    """Duck-typed fake exposing only `credential_identity`/`request_
    signature`, the sole `HATPHardwareSigner` methods `hatp_signing_
    ceremony.py` calls."""

    def __init__(
        self,
        *,
        signer_key_id: str = "signer-1",
        cancel: bool = False,
        device_error: bool = False,
        unavailable_at_touch: bool = False,
        raise_other: Optional[BaseException] = None,
        raise_on_identity: Optional[BaseException] = None,
        vary_evidence: bool = False,
    ) -> None:
        self.signer_key_id = signer_key_id
        self.cancel = cancel
        self.device_error = device_error
        self.unavailable_at_touch = unavailable_at_touch
        self.raise_other = raise_other
        self.raise_on_identity = raise_on_identity
        self.vary_evidence = vary_evidence
        self.credential_identity_calls = 0
        self.request_signature_calls = 0
        self.received_payloads: list = []

    def capabilities(self):  # pragma: no cover - not used by the ceremony
        raise NotImplementedError

    def credential_identity(self) -> str:
        self.credential_identity_calls += 1
        if self.raise_on_identity is not None:
            raise self.raise_on_identity
        return self.signer_key_id

    def request_signature(self, payload: bytes, *, signer_key_id: str, provider_profile: str, presence_timeout_s: float = 30.0) -> ProviderAssertion:
        self.request_signature_calls += 1
        self.received_payloads.append(payload)
        if self.cancel:
            raise HATPProviderCancelledError("human cancelled")
        if self.device_error:
            raise HATPProviderDeviceError("device transport fault")
        if self.unavailable_at_touch:
            raise HATPProviderUnavailableError("device disappeared mid-ceremony")
        if self.raise_other is not None:
            raise self.raise_other
        evidence = b"assertion-" + (str(self.request_signature_calls).encode() if self.vary_evidence else b"fixed")
        return ProviderAssertion(
            credential_id=signer_key_id, provider_profile=provider_profile, algorithm="fake", evidence=evidence
        )


def _fixed_clock(instant: datetime):
    def _clock() -> datetime:
        return instant

    return _clock


_FIXED_INSTANT = datetime(2026, 8, 4, 10, 0, 0, 123000, tzinfo=timezone.utc)


def _sign(
    root: HarnessPath,
    *,
    site: RollbackSite,
    job_id: Optional[str] = None,
    per_id: Optional[str] = None,
    provider: Optional[FakeHardwareProvider] = None,
    trust_store: Optional[FakeTrustStore] = None,
    clock=None,
    confirm=None,
):
    provider = provider if provider is not None else FakeHardwareProvider()
    trust_store = trust_store if trust_store is not None else FakeTrustStore({"signer-1": _active_signer()})
    clock = clock if clock is not None else _fixed_clock(_FIXED_INSTANT)
    confirm = confirm if confirm is not None else (lambda preview: True)
    return ceremony.sign_rollback_evidence(
        root,
        site=site,
        job_id=job_id,
        per_id=per_id,
        clock=clock,
        provider_factory=lambda: provider,
        trust_store_factory=lambda: trust_store,
        confirm=confirm,
    )


# ═══════════════════════════════════════════════════════════════════════════
# AG3 resolver
# ═══════════════════════════════════════════════════════════════════════════


def test_ag3_resolver_success(tmp_path):
    root = _root(tmp_path)
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_job(root, "job-1", commit_sha="c" * 40)
    binding = _make_ag3_binding(root, pub_store, job_id="job-1", commit_sha="c" * 40)

    context = ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")

    assert context.rollback_site is RollbackSite.AG3
    assert context.operation_reference == Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40)
    assert context.binding_id == binding.evidence_id
    assert context.binding_digest == binding.content_digest
    assert context.decision_record_id == binding.governance_record_reference.record_id
    assert context.decision_record_digest == binding.governance_record_reference.record_digest


def test_ag3_resolver_missing_job_is_operation_not_found(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(ceremony.OperationNotFoundError):
        ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="does-not-exist")


def test_ag3_resolver_unresolvable_original_commit_sha_is_operation_not_found(tmp_path):
    """Attack 21 (149O.10.1 Obs-2): a job that exists but whose
    `original_commit_sha` cannot be resolved fails `operation_not_found`
    before any Binding lookup or hardware touch."""

    root = _root(tmp_path)
    _write_job(root, "job-1", commit_sha=None)
    with pytest.raises(ceremony.OperationNotFoundError):
        ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")


def test_ag3_resolver_malformed_commit_sha_is_operation_not_found(tmp_path):
    root = _root(tmp_path)
    _write_job(root, "job-1", commit_sha="not-a-valid-sha")
    with pytest.raises(ceremony.OperationNotFoundError):
        ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")


# ═══════════════════════════════════════════════════════════════════════════
# AG5 resolver
# ═══════════════════════════════════════════════════════════════════════════


def test_ag5_resolver_success(tmp_path):
    root = _root(tmp_path)
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_per(root, "per-1", ecp_id="ecp-1")
    binding = _make_ag5_binding(root, pub_store, per_id="per-1", ecp_id="ecp-1")

    context = ceremony.resolve_signing_context(root, site=RollbackSite.AG5, per_id="per-1")

    assert context.rollback_site is RollbackSite.AG5
    assert context.operation_reference == Ag5OperationReference(per_id="per-1", ecp_id="ecp-1")
    assert context.binding_id == binding.evidence_id


def test_ag5_resolver_missing_per_is_operation_not_found(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(ceremony.OperationNotFoundError):
        ceremony.resolve_signing_context(root, site=RollbackSite.AG5, per_id="does-not-exist")


def test_ag5_resolver_unresolvable_ecp_id_is_operation_not_found(tmp_path):
    """Attack 20: a PER that exists but whose `ecp_id` cannot be resolved
    fails `operation_not_found` before any Binding lookup or hardware
    touch."""

    root = _root(tmp_path)
    _write_per(root, "per-1", ecp_id=None)
    with pytest.raises(ceremony.OperationNotFoundError):
        ceremony.resolve_signing_context(root, site=RollbackSite.AG5, per_id="per-1")


# ═══════════════════════════════════════════════════════════════════════════
# Binding resolution: missing / ambiguous / repository identity
# ═══════════════════════════════════════════════════════════════════════════


def test_no_matching_binding_is_binding_unavailable(tmp_path):
    """Attack 19."""

    root = _root(tmp_path)
    _write_job(root, "job-1", commit_sha="c" * 40)
    with pytest.raises(ceremony.BindingUnavailableError):
        ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")


def test_binding_unavailable_before_any_hardware_touch(tmp_path):
    root = _root(tmp_path)
    _write_job(root, "job-1", commit_sha="c" * 40)
    provider = FakeHardwareProvider()
    with pytest.raises(ceremony.BindingUnavailableError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)
    assert provider.credential_identity_calls == 0
    assert provider.request_signature_calls == 0


def test_revoked_binding_is_excluded_yielding_binding_unavailable(tmp_path):
    root = _root(tmp_path)
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_job(root, "job-1", commit_sha="c" * 40)
    binding = _make_ag3_binding(root, pub_store, job_id="job-1", commit_sha="c" * 40)
    store = _rae_store(root)
    store.write_revocation(
        binding.evidence_id,
        rae.RevocationMetadata(revoked_at="2026-08-04T11:00:00.000Z", revoked_by="alice", reason_code="mistake"),
    )
    with pytest.raises(ceremony.BindingUnavailableError):
        ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")


def test_ambiguous_tied_created_at_is_binding_unavailable(tmp_path):
    root = _root(tmp_path)
    _write_job(root, "job-1", commit_sha="c" * 40)
    store = _rae_store(root)
    same_instant = datetime(2026, 8, 4, 9, 0, 0, tzinfo=timezone.utc)
    op_ref = rae.Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40)
    b1 = _manual_binding(site=rae.RollbackSite.AG3, operation_reference=op_ref, created_at=same_instant)
    b2 = _manual_binding(site=rae.RollbackSite.AG3, operation_reference=op_ref, created_at=same_instant)
    store.write_binding(b1)
    store.write_binding(b2)
    with pytest.raises(ceremony.BindingUnavailableError):
        ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")


def test_supersession_selects_the_latest_created_at_binding(tmp_path):
    root = _root(tmp_path)
    _write_job(root, "job-1", commit_sha="c" * 40)
    store = _rae_store(root)
    op_ref = rae.Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40)
    older = _manual_binding(
        site=rae.RollbackSite.AG3,
        operation_reference=op_ref,
        created_at=datetime(2026, 8, 4, 8, 0, 0, tzinfo=timezone.utc),
        decision_record_id="decision-older",
    )
    newer = _manual_binding(
        site=rae.RollbackSite.AG3,
        operation_reference=op_ref,
        created_at=datetime(2026, 8, 4, 9, 0, 0, tzinfo=timezone.utc),
        decision_record_id="decision-newer",
    )
    store.write_binding(older)
    store.write_binding(newer)

    context = ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")

    assert context.binding_id == newer.evidence_id
    assert context.decision_record_id == "decision-newer"


def test_repository_identity_unavailable(tmp_path):
    root = HarnessPath(tmp_path)  # deliberately skip ensure_repository_identity
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_job(root, "job-1", commit_sha="c" * 40)
    _make_ag3_binding(root, pub_store, job_id="job-1", commit_sha="c" * 40)
    with pytest.raises(ceremony.RepositoryIdentityUnavailableError):
        ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")


# ═══════════════════════════════════════════════════════════════════════════
# Signer / provider resolution
# ═══════════════════════════════════════════════════════════════════════════


def _setup_ag3(tmp_path) -> HarnessPath:
    root = _root(tmp_path)
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_job(root, "job-1", commit_sha="c" * 40)
    _make_ag3_binding(root, pub_store, job_id="job-1", commit_sha="c" * 40)
    return root


def test_no_authorized_signer_when_credential_not_enrolled(tmp_path):
    root = _setup_ag3(tmp_path)
    trust_store = FakeTrustStore({})  # empty registry
    provider = FakeHardwareProvider()
    with pytest.raises(ceremony.NoAuthorizedSignerError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider, trust_store=trust_store)
    assert provider.request_signature_calls == 0


def test_no_authorized_signer_when_signer_revoked(tmp_path):
    root = _setup_ag3(tmp_path)
    revoked = SignerRecord(
        signer_key_id="signer-1", principal_id="principal-1", provider_profile="HATP_HARDWARE_PROVIDER_V1",
        status="revoked", revoked_at="2026-08-01T00:00:00.000Z",
    )
    trust_store = FakeTrustStore({"signer-1": revoked})
    provider = FakeHardwareProvider()
    with pytest.raises(ceremony.NoAuthorizedSignerError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider, trust_store=trust_store)
    assert provider.request_signature_calls == 0


def test_provider_unavailable_when_credential_identity_raises(tmp_path):
    root = _setup_ag3(tmp_path)
    provider = FakeHardwareProvider(raise_on_identity=RuntimeError("no device"))
    with pytest.raises(ceremony.ProviderUnavailableError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)


def test_provider_unavailable_at_factory_time(tmp_path):
    """Attack 17: hardware device absent -> `provider_unavailable`, no
    software fallback, fails before any signature request."""

    root = _setup_ag3(tmp_path)

    def _raising_factory():
        raise HATPProviderUnavailableError("no compatible hardware provider discovered")

    with pytest.raises(ceremony.ProviderUnavailableError):
        ceremony.sign_rollback_evidence(
            root,
            site=RollbackSite.AG3,
            job_id="job-1",
            clock=_fixed_clock(_FIXED_INSTANT),
            provider_factory=_raising_factory,
            trust_store_factory=lambda: FakeTrustStore({"signer-1": _active_signer()}),
            confirm=lambda preview: True,
        )


# ═══════════════════════════════════════════════════════════════════════════
# Preview-before-touch ordering + exactly-one-provider-call
# ═══════════════════════════════════════════════════════════════════════════


def test_preview_shown_before_provider_touch_and_provider_called_exactly_once(tmp_path, monkeypatch):
    root = _setup_ag3(tmp_path)
    call_log: list = []

    original_resolve = ceremony.resolve_signing_context

    def logging_resolve(*args, **kwargs):
        call_log.append("resolve")
        return original_resolve(*args, **kwargs)

    monkeypatch.setattr(ceremony, "resolve_signing_context", logging_resolve)

    provider = FakeHardwareProvider()
    original_request_signature = provider.request_signature

    def logging_request_signature(*args, **kwargs):
        call_log.append("provider_touch")
        return original_request_signature(*args, **kwargs)

    provider.request_signature = logging_request_signature

    def logging_confirm(preview: ceremony.HATPSigningPreview) -> bool:
        call_log.append("preview_confirm")
        assert preview.rollback_site is RollbackSite.AG3
        assert preview.provider_profile == "HATP_HARDWARE_PROVIDER_V1"
        return True

    result = _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider, confirm=logging_confirm)

    assert call_log == ["resolve", "preview_confirm", "provider_touch", "resolve"]
    assert provider.request_signature_calls == 1
    assert provider.credential_identity_calls == 1
    assert isinstance(result, ceremony.HATPSigningResult)
    assert result.idempotent is False


def test_preview_has_no_authority_bearing_fields():
    field_names = {f.name for f in dataclasses.fields(ceremony.HATPSigningPreview)}
    forbidden = {"approved", "verified", "valid", "permission", "allow", "operational", "executed", "human_present"}
    assert field_names.isdisjoint(forbidden)


def test_declined_confirmation_is_human_signing_cancelled_no_touch(tmp_path):
    root = _setup_ag3(tmp_path)
    provider = FakeHardwareProvider()
    with pytest.raises(ceremony.HumanSigningCancelledError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider, confirm=lambda preview: False)
    assert provider.request_signature_calls == 0


# ═══════════════════════════════════════════════════════════════════════════
# Cancellation / device absence / provider failure during the touch
# ═══════════════════════════════════════════════════════════════════════════


def test_human_cancels_touch_no_evidence_persisted(tmp_path):
    """Attack 16."""

    root = _setup_ag3(tmp_path)
    provider = FakeHardwareProvider(cancel=True)
    with pytest.raises(ceremony.HumanSigningCancelledError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)
    store = HATPEvidenceStore(root)
    assert not store.envelopes_dir.exists() or list(store.envelopes_dir.glob("*.json")) == []


def test_hardware_device_fault_distinct_from_cancellation(tmp_path):
    root = _setup_ag3(tmp_path)
    provider = FakeHardwareProvider(device_error=True)
    with pytest.raises(ceremony.HardwareDeviceFaultError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)


def test_provider_unavailable_raised_during_touch(tmp_path):
    root = _setup_ag3(tmp_path)
    provider = FakeHardwareProvider(unavailable_at_touch=True)
    with pytest.raises(ceremony.ProviderUnavailableError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)


def test_generic_provider_exception_is_provider_signature_failure(tmp_path):
    root = _setup_ag3(tmp_path)
    provider = FakeHardwareProvider(raise_other=ValueError("provider blew up"))
    with pytest.raises(ceremony.ProviderSignatureFailureError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)


# ═══════════════════════════════════════════════════════════════════════════
# TOCTOU: mismatch on each of Decision / Binding / operation / repository
# ═══════════════════════════════════════════════════════════════════════════


def _resolved_context(root: HarnessPath, *, site: RollbackSite, job_id=None, per_id=None):
    return ceremony.resolve_signing_context(root, site=site, job_id=job_id, per_id=per_id)


def _run_toctou_mismatch(tmp_path, monkeypatch, mutate_context):
    root = _setup_ag3(tmp_path)
    context_a = _resolved_context(root, site=RollbackSite.AG3, job_id="job-1")
    context_b = mutate_context(context_a)
    responses = iter([context_a, context_b])
    monkeypatch.setattr(ceremony, "resolve_signing_context", lambda *a, **kw: next(responses))

    provider = FakeHardwareProvider()
    with pytest.raises(ceremony.EvidenceSerializationFailureError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)
    assert provider.request_signature_calls == 1
    store = HATPEvidenceStore(root)
    assert not store.envelopes_dir.exists() or list(store.envelopes_dir.glob("*.json")) == []


def test_toctou_mismatch_on_decision(tmp_path, monkeypatch):
    """Attack 18."""

    _run_toctou_mismatch(
        tmp_path, monkeypatch, lambda ctx: dataclasses.replace(ctx, decision_record_id="different-decision")
    )


def test_toctou_mismatch_on_decision_digest(tmp_path, monkeypatch):
    _run_toctou_mismatch(
        tmp_path, monkeypatch, lambda ctx: dataclasses.replace(ctx, decision_record_digest="b" * 64)
    )


def test_toctou_mismatch_on_binding(tmp_path, monkeypatch):
    _run_toctou_mismatch(tmp_path, monkeypatch, lambda ctx: dataclasses.replace(ctx, binding_id="different-binding"))


def test_toctou_mismatch_on_binding_digest(tmp_path, monkeypatch):
    _run_toctou_mismatch(tmp_path, monkeypatch, lambda ctx: dataclasses.replace(ctx, binding_digest="c" * 64))


def test_toctou_mismatch_on_operation(tmp_path, monkeypatch):
    _run_toctou_mismatch(
        tmp_path,
        monkeypatch,
        lambda ctx: dataclasses.replace(
            ctx, operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="d" * 40)
        ),
    )


def test_toctou_mismatch_on_repository(tmp_path, monkeypatch):
    _run_toctou_mismatch(tmp_path, monkeypatch, lambda ctx: dataclasses.replace(ctx, repository_id=str(uuid.uuid4())))


def test_toctou_real_supersession_between_preview_and_touch(tmp_path):
    """Real (non-monkeypatched) TOCTOU: a second, later Binding for the
    same operation is created from inside `confirm()` -- the exact
    moment between the pre-touch preview and the hardware touch attack
    18 targets. The post-touch recheck must observe the new Binding and
    discard the just-produced signature."""

    root = _root(tmp_path)
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_job(root, "job-1", commit_sha="c" * 40)
    _make_ag3_binding(root, pub_store, job_id="job-1", commit_sha="c" * 40, subject="original decision")

    def _mutate_then_confirm(preview: ceremony.HATPSigningPreview) -> bool:
        # A fresh, later Binding for the identical operation supersedes
        # the one the preview was built from.
        _make_ag3_binding(root, pub_store, job_id="job-1", commit_sha="c" * 40, subject="superseding decision")
        return True

    provider = FakeHardwareProvider()
    with pytest.raises(ceremony.EvidenceSerializationFailureError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider, confirm=_mutate_then_confirm)
    assert provider.request_signature_calls == 1
    store = HATPEvidenceStore(root)
    assert not store.envelopes_dir.exists() or list(store.envelopes_dir.glob("*.json")) == []


# ═══════════════════════════════════════════════════════════════════════════
# Envelope construction / store publish outcomes
# ═══════════════════════════════════════════════════════════════════════════


def test_envelope_built_through_the_12a_factory_only(tmp_path, monkeypatch):
    root = _setup_ag3(tmp_path)
    calls: list = []
    original_builder = ceremony.build_hatp_signed_evidence_envelope

    def spy_builder(proof, provider_assertion):
        calls.append((proof, provider_assertion))
        return original_builder(proof, provider_assertion)

    monkeypatch.setattr(ceremony, "build_hatp_signed_evidence_envelope", spy_builder)

    provider = FakeHardwareProvider()
    result = _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)

    assert len(calls) == 1
    proof, provider_assertion = calls[0]
    assert proof.rollback_site is RollbackSite.AG3
    assert provider_assertion == b"assertion-fixed"
    assert len(provider.received_payloads) == 1
    assert result.evidence_id


def test_publish_is_idempotent_on_identical_repeat(tmp_path):
    root = _setup_ag3(tmp_path)
    provider = FakeHardwareProvider()
    first = _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)
    assert first.idempotent is False

    provider2 = FakeHardwareProvider()  # produces identical fixed evidence bytes
    second = _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider2)
    assert second.idempotent is True
    assert second.evidence_id == first.evidence_id


def test_publish_conflict_on_differing_assertion_same_proof(tmp_path):
    root = _setup_ag3(tmp_path)
    provider1 = FakeHardwareProvider(vary_evidence=True)
    first = _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider1)
    assert first.idempotent is False

    provider2 = FakeHardwareProvider(vary_evidence=True)
    provider2.request_signature_calls = 5  # forces different "vary" bytes than provider1's first call
    with pytest.raises(EvidenceConflictError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider2)


def test_publish_persistence_failure_propagates_unmodified(tmp_path):
    root = _setup_ag3(tmp_path)
    store = HATPEvidenceStore(root)
    store.envelopes_dir.mkdir(parents=True, exist_ok=True)

    # Pre-compute the exact evidence_id this ceremony run will produce so
    # we can occupy its destination with a directory (Obs-3 mapping: a
    # non-regular final object always fails closed as persistence
    # failure, never conflict).
    context = ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")
    signer = _active_signer()
    from pcae.core.human_approval_trusted_provenance import HumanApprovalProvenanceProof, canonicalize_hatp_proof_payload
    from pcae.core.hatp_signed_evidence import build_hatp_signed_evidence_envelope

    proof = HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id=signer.principal_id,
        signer_key_id=signer.signer_key_id,
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=context.repository_id,
        decision_record_id=context.decision_record_id,
        decision_record_digest=context.decision_record_digest,
        binding_id=context.binding_id,
        binding_digest=context.binding_digest,
        rollback_site=context.rollback_site,
        operation_reference=context.operation_reference,
        issued_at=ceremony._issued_at_string(_FIXED_INSTANT),
    )
    envelope = build_hatp_signed_evidence_envelope(proof, b"assertion-fixed")
    (store.envelopes_dir / f"{envelope.evidence_id}.json").mkdir()

    provider = FakeHardwareProvider()
    with pytest.raises(EvidencePersistenceFailureError):
        _sign(root, site=RollbackSite.AG3, job_id="job-1", provider=provider)


# ═══════════════════════════════════════════════════════════════════════════
# Timestamp: whole-millisecond truncation
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "microsecond,expected_ms_digits",
    [
        (0, "000"),
        (1000, "001"),
        (999000, "999"),
        (999999, "999"),  # not divisible by 1000 -> truncated down
        (1, "000"),  # not divisible by 1000 -> truncated down
        (500499, "500"),
        (500999, "500"),
    ],
)
def test_issued_at_string_truncates_to_whole_milliseconds(microsecond, expected_ms_digits):
    instant = datetime(2026, 8, 4, 10, 0, 0, microsecond, tzinfo=timezone.utc)
    rendered = ceremony._issued_at_string(instant)
    # rendered is a valid ISO string accepted by HumanApprovalProvenanceProof;
    # confirm its fractional-second field is exactly the expected 3 digits
    # once round-tripped through the real proof constructor's own
    # canonical renderer.
    proof = _proof_with_issued_at(rendered)
    assert proof.issued_at.endswith(f".{expected_ms_digits}Z")


def _proof_with_issued_at(issued_at: str):
    from pcae.core.human_approval_trusted_provenance import HumanApprovalProvenanceProof

    return HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id="alice",
        signer_key_id="signer-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=str(uuid.uuid4()),
        decision_record_id="decision-1",
        decision_record_digest=_PLACEHOLDER_DIGEST,
        binding_id="rae-binding-1",
        binding_digest=_PLACEHOLDER_DIGEST,
        rollback_site=RollbackSite.AG3,
        operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40),
        issued_at=issued_at,
    )


def test_issued_at_string_naive_datetime_is_treated_as_utc():
    naive = datetime(2026, 8, 4, 10, 0, 0, 0)
    rendered = ceremony._issued_at_string(naive)
    proof = _proof_with_issued_at(rendered)
    assert proof.issued_at == "2026-08-04T10:00:00.000Z"


# ═══════════════════════════════════════════════════════════════════════════
# Import discipline
# ═══════════════════════════════════════════════════════════════════════════


def test_module_importable_without_hardware_or_fido2(tmp_path):
    """Importing `hatp_signing_ceremony` (or invoking `resolve_signing_
    context`, which performs no hardware I/O) must never require `fido2`
    or any hardware library -- only actually invoking the production
    provider factory touches that optional dependency boundary."""

    import subprocess
    import sys

    script = (
        "import sys\n"
        "import pcae.core.hatp_signing_ceremony as m\n"
        "assert 'pcae.core.hatp_fido2_provider' not in sys.modules\n"
        "assert 'fido2' not in sys.modules\n"
        "print('ok')\n"
    )
    completed = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stderr
    assert "ok" in completed.stdout
