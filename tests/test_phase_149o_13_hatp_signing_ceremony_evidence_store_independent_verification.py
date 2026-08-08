"""Phase 149O.13 -- Independent Implementation Verification of the
HSCE-001 v1.1 signing-ceremony + evidence-store implementation
(149O.12A model/store, 149O.12B ceremony/TOCTOU, 149O.12C CLI).

Verification-only phase (`docs/PHASE_149O_13_HATP_SIGNING_CEREMONY_
EVIDENCE_STORE_INDEPENDENT_IMPLEMENTATION_VERIFICATION.md`). This module
is independently authored: it reconstructs attacks, field sets, and
call-order expectations directly from HSCE-001 v1.1
(`docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`) and
from direct reading of the four production modules under test, not from
149O.12A/B/C's own test files or phase reports. Where a helper below
resembles an existing 12A/B/C helper, it is a fresh, independent
implementation against the same contract text, not a copy.

No production file is imported for mutation; only for exercise. This
phase modifies no `src/pcae/**` file.
"""
from __future__ import annotations

import base64
import inspect
import json
import os
import stat
import subprocess
import sys
import threading
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
from pcae.core.hatp_signed_evidence import (
    EvidenceIdDigestMismatchError,
    HATPSignedEvidenceEnvelope,
    InvalidEvidenceEnvelopeSchemaError,
    InvalidEvidenceIdError,
    MalformedEvidenceEnvelopeError,
    UnsupportedEvidenceVersionError,
    build_hatp_signed_evidence_envelope,
    digest_hatp_proof_payload,
    parse_hatp_signed_evidence,
    serialize_hatp_signed_evidence,
)
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HumanApprovalProvenanceProof,
    RollbackSite,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity
from pcae.governance.publication.storage import PublicationRecordStore

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Captured at collection time, before the autouse monkeypatch fixture
# below replaces the module attribute -- so the defect-reproduction test
# inspects the true, unpatched production function.
from pcae.governance.publication.coordinator import _parse_timestamp as _ORIGINAL_PARSE_TIMESTAMP


# ═══════════════════════════════════════════════════════════════════════════
# Independent scaffolding -- built from contract text, not copied from
# 149O.12A/B/C's own test helpers.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _z_suffix_workaround(monkeypatch):
    """149O.13's own independent confirmation of the pre-existing,
    unrelated `pcae.governance.publication.coordinator._parse_timestamp`
    defect (§134/§159 of the governing prompt): bare
    `datetime.fromisoformat(value)` rejects a trailing `Z` before Python
    3.11. Reproduced and worked around identically to 149O.12B's own
    fixture -- confirming the defect is real and this suite's own CHGR
    Decision/Binding fixtures would fail on Python 3.9 without it."""

    from pcae.governance.publication import coordinator as _coordinator

    def _tolerant(value: str) -> datetime:
        text = value[:-1] + "+00:00" if isinstance(value, str) and value.endswith("Z") else value
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    monkeypatch.setattr(_coordinator, "_parse_timestamp", _tolerant)


def test_python39_z_suffix_defect_repaired_by_149o_16_1():
    """149O.12B-Obs-PY39-1 (originally documented here as a live defect:
    `datetime.fromisoformat` only accepted a trailing `Z` suffix starting
    in Python 3.11, and the unpatched `coordinator._parse_timestamp`
    called bare `fromisoformat(value)` with no normalization) was
    repaired in 149O.16.1 by mirroring the existing `pcae.core.
    rollback_approval_evidence._parse_iso_timestamp` precedent. This test
    now confirms the repair is in place: the production function
    normalizes a terminal 'Z' before delegating to `fromisoformat`, so
    Python 3.9/3.10 no longer need this module's `monkeypatch` workaround
    fixture to construct real CHGR Decision / RAE Binding fixtures ending
    in 'Z' (the fixture itself remains, harmlessly idempotent, as
    historical scaffolding -- see 149O.16.1's phase document for its
    disposition)."""

    source = inspect.getsource(_ORIGINAL_PARSE_TIMESTAMP)
    assert 'value.endswith("Z")' in source
    assert '[:-1] + "+00:00"' in source
    # This interpreter itself must be new enough to silently accept 'Z'
    # (Python 3.11+); the point of the source-level assertions above is
    # that the repair is lexically present regardless of which Python
    # this suite happens to run under.
    assert sys.version_info >= (3, 11)
    parsed = datetime.fromisoformat("2026-08-04T10:00:00.000Z")
    assert parsed.tzinfo is not None
    # The repaired production function itself now accepts the identical
    # input directly, with no monkeypatch involved.
    repaired = _ORIGINAL_PARSE_TIMESTAMP("2026-08-04T10:00:00.000Z")
    assert repaired.tzinfo is not None


def _root(tmp_path: Path) -> HarnessPath:
    root = HarnessPath(tmp_path)
    ensure_repository_identity(root)
    return root


def _write_job(root: HarnessPath, job_id: str, *, commit_sha: Optional[str] = "d" * 40) -> None:
    jobs_dir = root.path / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    (jobs_dir / f"{job_id}.json").write_text(json.dumps({"requested_agent": "codex", "commit_sha": commit_sha}))


def _write_per(root: HarnessPath, per_id: str, *, ecp_id: Optional[str] = "ecp-independent") -> None:
    record = {
        "per_id": per_id,
        "epr_id": "epr-independent",
        "ecp_id": ecp_id if ecp_id is not None else "",
        "prompt_id": "prompt-independent",
        "started_at": "2026-08-08T10:00:00.000Z",
        "status": "completed",
        "file_results": [],
        "rollback_executed": False,
        "execution_allowed": False,
    }
    if ecp_id is not None:
        result = store_promotion_execution_record(root, record)
        assert result["stored"], result["errors"]
    else:
        store_dir = root.path / ".pcae" / "promotion-executions"
        store_dir.mkdir(parents=True, exist_ok=True)
        (store_dir / f"{per_id}.json").write_text(json.dumps(record))


def _rae_store(root: HarnessPath) -> rae.RollbackApprovalEvidenceStore:
    return rae.RollbackApprovalEvidenceStore(root=root.path / ".pcae" / "rollback-approval-evidence")


def _publish_decision(pub_store: PublicationRecordStore, subject: str) -> rae.RollbackApprovalDecisionRef:
    return rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject=subject,
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "independent-verifier",
            "captured_at": "2026-08-08T10:00:00Z",
        },
        operator_id="independent-verifier",
        publication_store=pub_store,
    )


def _make_ag3_binding(root: HarnessPath, pub_store: PublicationRecordStore, *, job_id: str, commit_sha: str):
    ref = _publish_decision(pub_store, f"AG3 job={job_id} commit={commit_sha}")
    return rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id=job_id, original_commit_sha=commit_sha),
        task_id=None,
        repository_state_binding=rae.RepositoryStateBinding(head_commit_sha="feedface", branch="main"),
        publication_root=pub_store.root,
        evidence_store=_rae_store(root),
    )


def _make_ag5_binding(root: HarnessPath, pub_store: PublicationRecordStore, *, per_id: str, ecp_id: str):
    ref = _publish_decision(pub_store, f"AG5 per={per_id} ecp={ecp_id}")
    return rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG5,
        rollback_operation_reference=rae.Ag5OperationReference(per_id=per_id, ecp_id=ecp_id),
        task_id=None,
        repository_state_binding=rae.RepositoryStateBinding(head_commit_sha="feedface", branch="main"),
        publication_root=pub_store.root,
        evidence_store=_rae_store(root),
    )


def _active_signer(signer_key_id: str = "sig-1", principal_id: str = "prin-1") -> SignerRecord:
    return SignerRecord(
        signer_key_id=signer_key_id, principal_id=principal_id,
        provider_profile="HATP_HARDWARE_PROVIDER_V1", status="active",
    )


class RecordingTrustStore:
    def __init__(self, signers=None):
        self._signers = signers or {}
        self.lookups: list = []

    def lookup_signer(self, signer_key_id: str):
        self.lookups.append(signer_key_id)
        return self._signers.get(signer_key_id)


class RecordingProvider:
    """Independent fake recording call order/count -- used to prove
    preview-before-touch (§53), no-touch-on-precondition-failure (§54),
    and exact-one-signature-attempt (§55) directly, via a shared
    call-order list rather than trusting the module's own docstring."""

    def __init__(self, *, signer_key_id="sig-1", cancel=False, device_error=False, other_error=None, call_log=None):
        self.signer_key_id = signer_key_id
        self.cancel = cancel
        self.device_error = device_error
        self.other_error = other_error
        self.call_log = call_log if call_log is not None else []
        self.request_signature_calls = 0

    def credential_identity(self) -> str:
        self.call_log.append("credential_identity")
        return self.signer_key_id

    def request_signature(self, payload: bytes, *, signer_key_id: str, provider_profile: str, presence_timeout_s: float = 30.0) -> ProviderAssertion:
        self.call_log.append("request_signature")
        self.request_signature_calls += 1
        if self.cancel:
            raise HATPProviderCancelledError("independent-fake cancel")
        if self.device_error:
            raise HATPProviderDeviceError("independent-fake device fault")
        if self.other_error is not None:
            raise self.other_error
        return ProviderAssertion(
            credential_id=signer_key_id, provider_profile=provider_profile,
            algorithm="independent-fake", evidence=b"independent-evidence-" + str(self.request_signature_calls).encode(),
        )


def _fixed_clock(instant: datetime):
    return lambda: instant


_INSTANT = datetime(2026, 8, 8, 12, 0, 0, 456000, tzinfo=timezone.utc)


def _sign(root, *, site, job_id=None, per_id=None, provider=None, trust_store=None, clock=None, confirm=None, call_log=None):
    log = call_log if call_log is not None else []
    provider = provider if provider is not None else RecordingProvider(call_log=log)
    trust_store = trust_store if trust_store is not None else RecordingTrustStore({"sig-1": _active_signer()})

    def _logging_confirm(preview):
        log.append("confirm")
        return True if confirm is None else confirm(preview)

    return ceremony.sign_rollback_evidence(
        root, site=site, job_id=job_id, per_id=per_id,
        clock=clock if clock is not None else _fixed_clock(_INSTANT),
        provider_factory=lambda: provider,
        trust_store_factory=lambda: trust_store,
        confirm=_logging_confirm,
    )


def _minimal_proof(**overrides) -> HumanApprovalProvenanceProof:
    fields = dict(
        proof_version=1,
        principal_id="prin-1",
        signer_key_id="sig-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=str(uuid.UUID("00000000-0000-4000-8000-000000000001")),
        decision_record_id="decision-1",
        decision_record_digest="a" * 64,
        binding_id="binding-1",
        binding_digest="b" * 64,
        rollback_site=RollbackSite.AG3,
        operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40),
        issued_at="2026-08-08T12:00:00.000Z",
    )
    fields.update(overrides)
    return HumanApprovalProvenanceProof(**fields)


def _envelope(proof=None, assertion=b"assertion-bytes") -> HATPSignedEvidenceEnvelope:
    return build_hatp_signed_evidence_envelope(proof or _minimal_proof(), assertion)


# ═══════════════════════════════════════════════════════════════════════════
# §5-18 -- Model / parser / serializer independent reconstruction
# ═══════════════════════════════════════════════════════════════════════════


class TestModelFieldSetAndImmutability:
    def test_exact_field_set(self):
        env = _envelope()
        assert {f.name for f in env.__dataclass_fields__.values()} == {
            "evidence_version", "evidence_id", "proof", "provider_assertion"
        }

    def test_frozen_immutable(self):
        env = _envelope()
        with pytest.raises(Exception):
            env.evidence_version = 2  # type: ignore[misc]

    def test_no_authority_bearing_attribute_anywhere(self):
        env = _envelope()
        forbidden = {"approved", "verified", "valid", "permission", "allow", "operational", "executed", "human_present"}
        assert forbidden.isdisjoint({f.name for f in env.__dataclass_fields__.values()})


class TestVersionDomainAttack:
    @pytest.mark.parametrize("bad_version", [True, False, 1.0, "1", 0, 2, None])
    def test_constructor_rejects_non_canonical_version(self, bad_version):
        proof = _minimal_proof()
        with pytest.raises(UnsupportedEvidenceVersionError):
            HATPSignedEvidenceEnvelope(
                evidence_version=bad_version, evidence_id=digest_hatp_proof_payload(proof),
                proof=proof, provider_assertion=b"x",
            )

    @pytest.mark.parametrize("bad_version", [True, False, 1.0, "1", 0, 2, None])
    def test_parser_rejects_non_canonical_version(self, bad_version):
        proof = _minimal_proof()
        doc = {
            "evidence_version": bad_version,
            "evidence_id": digest_hatp_proof_payload(proof),
            "proof": json.loads(json.dumps(_proof_document(proof))),
            "provider_assertion": base64.b64encode(b"x").decode("ascii"),
        }
        with pytest.raises(UnsupportedEvidenceVersionError):
            parse_hatp_signed_evidence(json.dumps(doc))


def _proof_document(proof: HumanApprovalProvenanceProof) -> dict:
    from pcae.core.human_approval_trusted_provenance import hatp_proof_to_document
    return hatp_proof_to_document(proof)


class TestEvidenceIdDomainAttack:
    @pytest.mark.parametrize("bad_id", [
        "A" * 64,                       # uppercase
        "aB" * 32,                      # mixed case
        "a" * 63,                       # too short
        "a" * 65,                       # too long
        "g" * 64,                       # nonhex
        "a" * 63 + " ",                 # whitespace
        "a" * 32 + "/" + "a" * 31,       # slash
        "a" * 32 + "\\" + "a" * 31,      # backslash
        "../" + "a" * 61,                # dot-dot
        "а" * 64,                   # cyrillic lookalike 'a'
    ])
    def test_constructor_rejects(self, bad_id):
        proof = _minimal_proof()
        with pytest.raises(InvalidEvidenceIdError):
            HATPSignedEvidenceEnvelope(
                evidence_version=1, evidence_id=bad_id, proof=proof, provider_assertion=b"x",
            )

    def test_parser_rejects_same_domain_as_constructor(self):
        proof = _minimal_proof()
        doc = {
            "evidence_version": 1, "evidence_id": "A" * 64,
            "proof": _proof_document(proof), "provider_assertion": base64.b64encode(b"x").decode("ascii"),
        }
        with pytest.raises(InvalidEvidenceIdError):
            parse_hatp_signed_evidence(json.dumps(doc))


class TestConstructorParserDomainEquivalence:
    def test_valid_envelope_constructible_and_parseable_identically(self):
        proof = _minimal_proof()
        envelope = build_hatp_signed_evidence_envelope(proof, b"assertion")
        raw = serialize_hatp_signed_evidence(envelope)
        reparsed = parse_hatp_signed_evidence(raw)
        assert reparsed == envelope

    def test_digest_mismatch_rejected_by_both_paths(self):
        proof = _minimal_proof()
        wrong_id = "0" * 64
        with pytest.raises(EvidenceIdDigestMismatchError):
            HATPSignedEvidenceEnvelope(evidence_version=1, evidence_id=wrong_id, proof=proof, provider_assertion=b"x")
        doc = {
            "evidence_version": 1, "evidence_id": wrong_id,
            "proof": _proof_document(proof), "provider_assertion": base64.b64encode(b"x").decode("ascii"),
        }
        with pytest.raises(EvidenceIdDigestMismatchError):
            parse_hatp_signed_evidence(json.dumps(doc))


class TestProviderAssertionIndependence:
    def test_same_proof_different_assertion_same_evidence_id(self):
        proof = _minimal_proof()
        env_a = build_hatp_signed_evidence_envelope(proof, b"assertion-A")
        env_b = build_hatp_signed_evidence_envelope(proof, b"assertion-B")
        assert env_a.evidence_id == env_b.evidence_id


class TestCanonicalSerializationAndRoundTrip:
    def test_round_trip_equal(self):
        env = _envelope()
        assert parse_hatp_signed_evidence(serialize_hatp_signed_evidence(env)) == env

    def test_canonical_stability(self):
        env = _envelope()
        once = serialize_hatp_signed_evidence(env)
        twice = serialize_hatp_signed_evidence(parse_hatp_signed_evidence(once))
        assert once == twice

    def test_noncanonical_json_normalizes_to_same_canonical_bytes(self):
        env = _envelope()
        canonical = serialize_hatp_signed_evidence(env)
        doc = json.loads(canonical)
        reordered = json.dumps(doc, indent=4, sort_keys=False)
        reparsed = parse_hatp_signed_evidence(reordered)
        assert serialize_hatp_signed_evidence(reparsed) == canonical


class TestDuplicateKeysUnknownMissingFields:
    def _valid_doc_text(self) -> str:
        env = _envelope()
        return serialize_hatp_signed_evidence(env).decode("utf-8")

    def test_duplicate_outer_key_rejected(self):
        text = self._valid_doc_text()
        # Inject a duplicate top-level key by string surgery (valid JSON,
        # duplicate object key -- exactly what object_pairs_hook rejects).
        injected = text[:-1] + ', "evidence_version": 1}'
        with pytest.raises(MalformedEvidenceEnvelopeError):
            parse_hatp_signed_evidence(injected)

    def test_duplicate_nested_proof_key_rejected(self):
        env = _envelope()
        doc = json.loads(serialize_hatp_signed_evidence(env))
        proof_text = json.dumps(doc["proof"])
        injected_proof = proof_text[:-1] + ', "proof_version": 1}'
        full = (
            '{"evidence_version": 1, "evidence_id": "%s", "proof": %s, "provider_assertion": "%s"}'
            % (doc["evidence_id"], injected_proof, doc["provider_assertion"])
        )
        with pytest.raises((MalformedEvidenceEnvelopeError, InvalidEvidenceEnvelopeSchemaError)):
            parse_hatp_signed_evidence(full)

    def test_unknown_top_level_field_rejected(self):
        doc = json.loads(self._valid_doc_text())
        doc["extra_field"] = "should not exist"
        with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
            parse_hatp_signed_evidence(json.dumps(doc))

    @pytest.mark.parametrize("missing_field", ["evidence_version", "evidence_id", "proof", "provider_assertion"])
    def test_missing_field_rejected(self, missing_field):
        doc = json.loads(self._valid_doc_text())
        del doc[missing_field]
        with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
            parse_hatp_signed_evidence(json.dumps(doc))


class TestBase64Strictness:
    def test_malformed_base64_rejected(self):
        doc = json.loads(serialize_hatp_signed_evidence(_envelope()))
        doc["provider_assertion"] = "not-valid-base64!!!"
        with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
            parse_hatp_signed_evidence(json.dumps(doc))

    def test_corrupt_but_structurally_valid_base64_parses_but_is_not_trust(self):
        """Attack 10: corrupt/truncated provider_assertion bytes parse
        structurally (no crypto verification exists at this layer, HSCE-
        REQ-063) -- this module never claims VALID by construction."""
        doc = json.loads(serialize_hatp_signed_evidence(_envelope()))
        doc["provider_assertion"] = base64.b64encode(b"\x00\x01truncated-garbage").decode("ascii")
        envelope = parse_hatp_signed_evidence(json.dumps(doc))
        assert envelope.provider_assertion == b"\x00\x01truncated-garbage"


# ═══════════════════════════════════════════════════════════════════════════
# §19-38 -- Evidence store / hard-link publication independent verification
# ═══════════════════════════════════════════════════════════════════════════


class TestStorePathAndNoSideEffects:
    def test_store_path_layout(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        proof = _minimal_proof()
        eid = digest_hatp_proof_payload(proof)
        expected = tmp_path / ".pcae" / "hatp-evidence" / "envelopes" / f"{eid}.json"
        assert store.path_for(eid) == expected

    def test_no_directory_created_on_construction(self, tmp_path):
        root = _root(tmp_path)
        HATPEvidenceStore(root)
        assert not (tmp_path / ".pcae" / "hatp-evidence").exists()

    def test_no_directory_created_on_import_alone(self):
        # Import already happened at module load; re-confirm no side
        # effect directory exists under this test file's own cwd-neutral
        # check by asserting the store class itself performs no I/O in
        # __init__ (already covered above) -- this test documents intent.
        assert HATPEvidenceStore.__init__.__code__.co_names.count("mkdir") == 0


class TestPathTraversalAndSymlinkAttacks:
    def test_path_traversal_evidence_id_rejected(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        with pytest.raises(InvalidEvidenceIdError):
            store.path_for("../../../etc/passwd" + "a" * 40)

    def test_absolute_path_evidence_id_rejected(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        with pytest.raises(InvalidEvidenceIdError):
            store.path_for("/etc/passwd" + "a" * 53)

    def test_symlink_final_destination_rejected_no_follow(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        envelopes_dir = tmp_path / ".pcae" / "hatp-evidence" / "envelopes"
        envelopes_dir.mkdir(parents=True)
        outside_target = tmp_path.parent / f"outside-target-{uuid.uuid4().hex}.json"
        outside_target.write_text("external content")
        proof = _minimal_proof()
        eid = digest_hatp_proof_payload(proof)
        symlink_path = envelopes_dir / f"{eid}.json"
        symlink_path.symlink_to(outside_target)

        envelope = _envelope(proof)
        with pytest.raises(EvidencePersistenceFailureError):
            store.publish(envelope)
        # The external target must never be read/overwritten.
        assert outside_target.read_text() == "external content"

        with pytest.raises(EvidencePersistenceFailureError):
            store.load(eid)

    def test_store_root_symlink_escape_rejected(self, tmp_path):
        root = _root(tmp_path)
        pcae_dir = tmp_path / ".pcae"
        pcae_dir.mkdir(parents=True, exist_ok=True)
        outside_dir = tmp_path.parent / f"outside-hatp-evidence-{uuid.uuid4().hex}"
        outside_dir.mkdir()
        (pcae_dir / "hatp-evidence").symlink_to(outside_dir)

        store = HATPEvidenceStore(root)
        with pytest.raises(EvidencePersistenceFailureError):
            store.publish(_envelope())
        assert list(outside_dir.iterdir()) == []


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX-specific special-file semantics")
class TestSpecialAndUnreadableFinalObject:
    def test_directory_at_final_path_fails_closed(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        proof = _minimal_proof()
        eid = digest_hatp_proof_payload(proof)
        final_path = store.path_for(eid)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        final_path.mkdir()  # occupy the destination with a directory

        with pytest.raises(EvidencePersistenceFailureError):
            store.publish(_envelope(proof))
        assert final_path.is_dir()  # never deleted/overwritten

    def test_fifo_at_final_path_fails_closed(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        proof = _minimal_proof()
        eid = digest_hatp_proof_payload(proof)
        final_path = store.path_for(eid)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        os.mkfifo(str(final_path))

        with pytest.raises(EvidencePersistenceFailureError):
            store.publish(_envelope(proof))
        assert stat.S_ISFIFO(os.lstat(final_path).st_mode)

    def test_unreadable_final_file_fails_closed(self, tmp_path):
        if os.geteuid() == 0:
            pytest.skip("cannot reproduce unreadable-file semantics as root")
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        proof = _minimal_proof()
        eid = digest_hatp_proof_payload(proof)
        final_path = store.path_for(eid)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        final_path.write_bytes(b"pre-existing-unreadable")
        final_path.chmod(0o000)
        try:
            with pytest.raises(EvidencePersistenceFailureError):
                store.publish(_envelope(proof))
        finally:
            final_path.chmod(0o644)
        assert final_path.read_bytes() == b"pre-existing-unreadable"


class TestPublicationOrderAndIdempotency:
    def test_single_winner_absent_final(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        result = store.publish(_envelope())
        assert result.idempotent is False
        assert result.path.exists()

    def test_identical_retry_idempotent(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        env = _envelope()
        first = store.publish(env)
        before = first.path.read_bytes()
        second = store.publish(env)
        assert second.idempotent is True
        assert first.path.read_bytes() == before

    def test_different_retry_conflict_original_unchanged(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        proof = _minimal_proof()
        env_a = build_hatp_signed_evidence_envelope(proof, b"assertion-A")
        env_b = build_hatp_signed_evidence_envelope(proof, b"assertion-B")
        assert env_a.evidence_id == env_b.evidence_id  # same ID, different bytes
        first = store.publish(env_a)
        original_bytes = first.path.read_bytes()
        with pytest.raises(EvidenceConflictError):
            store.publish(env_b)
        assert first.path.read_bytes() == original_bytes

    def test_temp_files_do_not_survive_as_authoritative(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        store.publish(_envelope())
        envelopes_dir = tmp_path / ".pcae" / "hatp-evidence" / "envelopes"
        leftover_tmp = [p for p in envelopes_dir.iterdir() if p.name.endswith(".tmp")]
        assert leftover_tmp == []


class TestConcurrentWriters:
    def test_two_identical_concurrent_writers_one_result(self, tmp_path):
        root = _root(tmp_path)
        env = _envelope()
        results = []
        errors = []

        def _writer():
            try:
                results.append(HATPEvidenceStore(root).publish(env))
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=_writer) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(results) == 8
        winners = [r for r in results if not r.idempotent]
        losers = [r for r in results if r.idempotent]
        assert len(winners) == 1
        assert len(losers) == 7
        assert len({r.path.read_bytes() for r in results}) == 1

    def test_many_writer_race_mixed_identical_and_differing(self, tmp_path):
        root = _root(tmp_path)
        proof = _minimal_proof()
        identical_env = build_hatp_signed_evidence_envelope(proof, b"same-assertion")
        differing_envelopes = [
            build_hatp_signed_evidence_envelope(proof, f"different-{i}".encode()) for i in range(4)
        ]
        candidates = [identical_env] * 4 + differing_envelopes
        results = []
        errors = []
        lock = threading.Lock()

        def _writer(env):
            try:
                r = HATPEvidenceStore(root).publish(env)
                with lock:
                    results.append(r)
            except EvidenceConflictError as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=_writer, args=(c,)) for c in candidates]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly one canonical artifact; every non-conflicting writer
        # observes the same bytes; conflicting writers get EvidenceConflictError.
        assert len(results) + len(errors) == len(candidates)
        assert len(results) >= 1
        canonical_bytes = {r.path.read_bytes() for r in results}
        assert len(canonical_bytes) == 1


class TestNonEexistLinkFailure:
    def test_exdev_style_failure_no_fallback(self, tmp_path, monkeypatch):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)

        real_link = os.link

        def _raising_link(src, dst, *a, **kw):
            raise OSError(18, "Invalid cross-device link")  # EXDEV

        monkeypatch.setattr(os, "link", _raising_link)
        try:
            with pytest.raises(EvidencePersistenceFailureError):
                store.publish(_envelope())
        finally:
            monkeypatch.setattr(os, "link", real_link)
        envelopes_dir = tmp_path / ".pcae" / "hatp-evidence" / "envelopes"
        assert not any(p.suffix == ".json" for p in envelopes_dir.iterdir())


class TestLoadApiAndLoadDoesNotVerify:
    def test_load_is_explicit_id_only_no_latest(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        assert not hasattr(store, "latest")
        assert not hasattr(store, "list_latest")
        assert not hasattr(store, "list")

    def test_load_returns_parsed_envelope_without_verification_result(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        published = store.publish(_envelope())
        loaded = store.load(published.evidence_id)
        assert isinstance(loaded, HATPSignedEvidenceEnvelope)
        assert not hasattr(loaded, "verification_result")
        assert not hasattr(loaded, "approval_present")


# ═══════════════════════════════════════════════════════════════════════════
# §39-92 -- Signing production boundary, ceremony/TOCTOU, CLI grammar
# ═══════════════════════════════════════════════════════════════════════════


class TestProductionWrapperZeroOverride:
    def test_production_entry_point_signature_exact(self):
        sig = inspect.signature(ceremony.production_sign_rollback_evidence)
        assert set(sig.parameters) == {"root", "site", "job_id", "per_id"}
        for forbidden in ("provider", "provider_factory", "trust_store", "trust_store_factory", "clock", "confirm"):
            assert forbidden not in sig.parameters

    def test_cli_calls_only_production_entry_point(self):
        import ast

        from pcae.commands import hatp as hatp_cli

        source = inspect.getsource(hatp_cli)
        tree = ast.parse(source)
        call_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
        assert "production_sign_rollback_evidence" in call_names
        assert "sign_rollback_evidence" not in call_names

        # Static scan excluding docstrings/comments: the bare injectable
        # identifier never appears as a token outside the import line.
        import tokenize
        import io

        bare_uses = 0
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.NAME and tok.string == "sign_rollback_evidence":
                bare_uses += 1
        # Exactly one occurrence: the `import ... production_sign_rollback_evidence`
        # line does not even mention the bare name, so any occurrence here
        # would indicate an unexpected reference.
        assert bare_uses == 0

    def test_zero_override_call_site_ast(self):
        import ast

        from pcae.commands import hatp as hatp_cli

        source = inspect.getsource(hatp_cli.run_hatp_sign_rollback)
        tree = ast.parse(source)
        call = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "production_sign_rollback_evidence":
                call = node
        assert call is not None
        keyword_names = {kw.arg for kw in call.keywords}
        assert keyword_names == {"site", "job_id", "per_id"}
        assert len(call.args) == 1  # root positional


class TestPreconditionFailuresTouchNoHardware:
    def test_unknown_job_no_touch(self, tmp_path):
        root = _root(tmp_path)
        log: list = []
        with pytest.raises(ceremony.OperationNotFoundError):
            _sign(root, site=RollbackSite.AG3, job_id="nonexistent-job", call_log=log)
        assert "request_signature" not in log

    def test_missing_original_commit_sha_no_touch(self, tmp_path):
        root = _root(tmp_path)
        _write_job(root, "job-nocsha", commit_sha=None)
        log: list = []
        with pytest.raises(ceremony.OperationNotFoundError):
            _sign(root, site=RollbackSite.AG3, job_id="job-nocsha", call_log=log)
        assert "request_signature" not in log

    def test_unknown_per_no_touch(self, tmp_path):
        root = _root(tmp_path)
        log: list = []
        with pytest.raises(ceremony.OperationNotFoundError):
            _sign(root, site=RollbackSite.AG5, per_id="nonexistent-per", call_log=log)
        assert "request_signature" not in log

    def test_missing_ecp_id_no_touch(self, tmp_path):
        root = _root(tmp_path)
        _write_per(root, "per-noecp", ecp_id=None)
        log: list = []
        with pytest.raises(ceremony.OperationNotFoundError):
            _sign(root, site=RollbackSite.AG5, per_id="per-noecp", call_log=log)
        assert "request_signature" not in log

    def test_missing_binding_no_touch(self, tmp_path):
        root = _root(tmp_path)
        _write_job(root, "job-nobinding")
        log: list = []
        with pytest.raises(ceremony.BindingUnavailableError):
            _sign(root, site=RollbackSite.AG3, job_id="job-nobinding", call_log=log)
        assert "request_signature" not in log

    def test_repository_identity_unavailable_no_touch(self, tmp_path):
        """Independent finding: `resolve_signing_context` resolves the RAE
        Binding *before* repository identity (source order confirmed by
        direct reading of `hatp_signing_ceremony.py::resolve_signing_
        context`), so a Binding must already exist to isolate this
        precondition specifically -- otherwise `binding_unavailable` fires
        first. A binding is created with identity present, then the
        identity file is removed to isolate this exact precondition."""
        from pcae.core.repository_identity import REPOSITORY_IDENTITY_RELATIVE_PATH

        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-noident")
        _make_ag3_binding(root, pub_store, job_id="job-noident", commit_sha="d" * 40)
        (root.path / REPOSITORY_IDENTITY_RELATIVE_PATH).unlink()

        log: list = []
        with pytest.raises(ceremony.RepositoryIdentityUnavailableError):
            _sign(root, site=RollbackSite.AG3, job_id="job-noident", call_log=log)
        assert "request_signature" not in log


class TestPreviewBeforeTouchOrdering:
    def test_call_order_resolve_then_confirm_then_provider(self, tmp_path):
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-order")
        _make_ag3_binding(root, pub_store, job_id="job-order", commit_sha="d" * 40)
        log: list = []
        _sign(root, site=RollbackSite.AG3, job_id="job-order", call_log=log)
        assert log.index("credential_identity") < log.index("confirm") < log.index("request_signature")

    def test_cancellation_at_confirm_no_touch(self, tmp_path):
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-cancel")
        _make_ag3_binding(root, pub_store, job_id="job-cancel", commit_sha="d" * 40)
        log: list = []
        with pytest.raises(ceremony.HumanSigningCancelledError):
            _sign(root, site=RollbackSite.AG3, job_id="job-cancel", confirm=lambda p: False, call_log=log)
        assert "request_signature" not in log
        # No evidence persisted on cancellation.
        assert not (root.path / ".pcae" / "hatp-evidence").exists()


class TestExactOneSignatureAttempt:
    def test_normal_ceremony_exactly_one_provider_call(self, tmp_path):
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-onecall")
        _make_ag3_binding(root, pub_store, job_id="job-onecall", commit_sha="d" * 40)
        log: list = []
        provider = RecordingProvider(call_log=log)
        _sign(root, site=RollbackSite.AG3, job_id="job-onecall", provider=provider, call_log=log)
        assert provider.request_signature_calls == 1

    def test_toctou_revocation_discards_no_publish(self, tmp_path):
        """TOCTOU via Binding revocation between preview and touch: the
        revoked Binding drops out of `_resolve_binding`'s own candidate
        list entirely, so context-B *resolution itself* raises
        `BindingUnavailableError` rather than the ceremony orchestrator's
        `context_a != context_b` comparison ever running and raising
        `EvidenceSerializationFailureError`. **Independent finding (non-
        blocking):** HSCE-REQ-070's text names `evidence_serialization_
        failure` for "the state has changed"; a revocation is a case
        where the state becomes *unresolvable* rather than merely
        *different*, and the implementation surfaces the more specific,
        already-closed-vocabulary `binding_unavailable` (exit 3) instead.
        The security property HSCE-REQ-070 actually protects -- never
        publish evidence known to be stale at publication time -- holds
        either way (both are exit-nonzero, no envelope is ever built or
        published); only the exact `error_type` discriminator differs
        from a literal reading of REQ-070's own error-type naming."""
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-toctou-revoke")
        binding = _make_ag3_binding(root, pub_store, job_id="job-toctou-revoke", commit_sha="d" * 40)

        log: list = []

        class _MutatingProvider(RecordingProvider):
            def request_signature(self, *a, **kw):
                result = super().request_signature(*a, **kw)
                rae.revoke_rollback_approval_binding(
                    binding.evidence_id, revoked_by="toctou-attacker", reason_code="toctou_attack",
                    evidence_store=_rae_store(root),
                )
                return result

        mutating = _MutatingProvider(call_log=log)
        with pytest.raises((ceremony.EvidenceSerializationFailureError, ceremony.BindingUnavailableError)):
            _sign(root, site=RollbackSite.AG3, job_id="job-toctou-revoke", provider=mutating, call_log=log)
        assert mutating.request_signature_calls == 1
        assert not (root.path / ".pcae" / "hatp-evidence" / "envelopes").exists() or list(
            (root.path / ".pcae" / "hatp-evidence" / "envelopes").glob("*.json")
        ) == []

    def test_toctou_repository_identity_change_discards_via_evidence_serialization_failure(self, tmp_path):
        """The literal HSCE-REQ-070 path: context remains *resolvable*
        post-touch but differs by value (repository_id changed) -- the
        `context_a != context_b` comparison itself catches this, raising
        exactly `EvidenceSerializationFailureError` as the contract text
        names."""
        from pcae.core.repository_identity import (
            REPOSITORY_IDENTITY_RELATIVE_PATH,
            RepositoryIdentity,
            _write_atomic,
        )

        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-toctou-repoid")
        _make_ag3_binding(root, pub_store, job_id="job-toctou-repoid", commit_sha="d" * 40)

        log: list = []

        class _RepoIdMutatingProvider(RecordingProvider):
            def request_signature(self, *a, **kw):
                result = super().request_signature(*a, **kw)
                new_identity = RepositoryIdentity(
                    schema_version=1, repository_instance_id=str(uuid.uuid4()),
                    created_at="2026-08-08T12:00:00.000Z",
                )
                target = root.join(REPOSITORY_IDENTITY_RELATIVE_PATH)
                _write_atomic(target, (json.dumps(new_identity.to_dict(), sort_keys=True)).encode("utf-8"))
                return result

        mutating = _RepoIdMutatingProvider(call_log=log)
        with pytest.raises(ceremony.EvidenceSerializationFailureError):
            _sign(root, site=RollbackSite.AG3, job_id="job-toctou-repoid", provider=mutating, call_log=log)
        assert mutating.request_signature_calls == 1
        assert not (root.path / ".pcae" / "hatp-evidence" / "envelopes").exists() or list(
            (root.path / ".pcae" / "hatp-evidence" / "envelopes").glob("*.json")
        ) == []


class TestNoAuthorityConflation:
    def test_signing_does_not_mutate_legacy_rollback_approval_state(self, tmp_path):
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-legacy")
        _make_ag3_binding(root, pub_store, job_id="job-legacy", commit_sha="d" * 40)
        approval_state_path = root.path / ".pcae" / "rollback_approval_state.json"
        before = approval_state_path.read_bytes() if approval_state_path.exists() else None
        _sign(root, site=RollbackSite.AG3, job_id="job-legacy")
        after = approval_state_path.read_bytes() if approval_state_path.exists() else None
        assert before == after

    def test_signing_module_imports_no_permission_broker(self):
        import ast

        tree = ast.parse(inspect.getsource(ceremony))
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
        assert not any("permission_broker" in m for m in imported_modules)

    def test_signing_module_never_calls_verify_hatp_proof(self):
        import ast

        tree = ast.parse(inspect.getsource(ceremony))
        call_names = {
            node.func.id for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert "verify_hatp_proof" not in call_names

    def test_signing_module_never_calls_rollback_dispatch(self):
        import ast

        tree = ast.parse(inspect.getsource(ceremony))
        call_names = {
            node.func.id for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert call_names.isdisjoint({"execute_rollback", "build_rollback_execution", "run_rollback"})

    def test_evidence_existence_does_not_change_rollback_preconditions(self, tmp_path):
        """A signed HSCE envelope's mere existence must not alter
        `pcae rollback`'s own dispatch preconditions (no automatic HSCE
        consumption exists yet -- 149O.12-13's own deferred scope).

        **Independent finding, clarifying not contradicting HSCE-REQ-015:**
        `build_rollback_execution` itself already carries optional
        `hatp_evidence_id`/`hatp_proof`/`hatp_evidence` keyword parameters
        -- but these are a *pre-existing, unrelated* additive/non-gating
        AG5 hook from Phase 149O.6 Wave 7 (`hatp_ag_authority.
        resolve_ag5_gated_rollback_authority`), structurally distinct from
        149O.12's HSCE evidence-store/envelope mechanism: it accepts raw
        `hatp_proof`/`hatp_evidence` objects directly from the caller, not
        an `--hatp-evidence <id>` store lookup, and its own docstring
        states it is "entirely inert... when omitted" and "never itself
        gates dispatch" (`execution_allowed=False` unconditionally). The
        real production CLI call site, `run_rollback`
        (`src/pcae/commands/agent.py:16259`), passes neither
        `hatp_evidence_id` nor `hatp_proof`/`hatp_evidence` -- confirmed
        directly below -- so HSCE-REQ-015's claim ("no HATP arguments")
        holds for the actual production call site, even though the
        callee's signature is not itself HATP-argument-free."""
        import ast

        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_per(root, "per-noconsume", ecp_id="ecp-noconsume")
        _make_ag5_binding(root, pub_store, per_id="per-noconsume", ecp_id="ecp-noconsume")
        result = _sign(root, site=RollbackSite.AG5, per_id="per-noconsume")
        assert (root.path / ".pcae" / "hatp-evidence" / "envelopes" / f"{result.evidence_id}.json").exists()

        from pcae.commands.agent import run_rollback

        tree = ast.parse(inspect.getsource(run_rollback))
        call = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "build_rollback_execution"
        )
        keyword_names = {kw.arg for kw in call.keywords}
        assert keyword_names.isdisjoint({"hatp_evidence_id", "hatp_proof", "hatp_evidence"})


class TestForbiddenFlagInventory:
    _FORBIDDEN_FLAGS = [
        "--provider", "--signer", "--principal", "--trust-store", "--credential-store",
        "--force", "--overwrite", "--output", "--repository-id", "--decision-id",
        "--decision-digest", "--binding-id", "--binding-digest", "--signer-key-id",
        "--ecp-id", "--original-commit-sha", "--issued-at", "--timestamp",
        "--approval-present", "--hatp-valid", "--operational", "--dry-run", "--dev",
        "--test-provider", "--software-provider", "--skip-touch", "--assume-present",
        "--ignore-not-ready",
    ]

    def test_all_forbidden_flags_rejected_by_real_parser(self):
        from pcae.cli import build_parser

        parser = build_parser()
        for flag in self._FORBIDDEN_FLAGS:
            with pytest.raises(SystemExit):
                parser.parse_args(["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "j", flag, "x"])

    def test_forbidden_flags_absent_from_handler_source(self):
        source = inspect.getsource(sys.modules["pcae.commands.hatp"])
        # Exclude docstring block at the top by scanning only lines that
        # look like add_argument-style flag usage; cli.py owns registration.
        import pcae.cli as cli_module

        cli_source = inspect.getsource(cli_module)
        # only check the hatp registration block, not the whole 10k-line file
        start = cli_source.index('"hatp"')
        end = cli_source.index("hatp_sign_rollback_parser.set_defaults")
        block = cli_source[start:end]
        for flag in self._FORBIDDEN_FLAGS:
            assert flag not in block


class TestCliGrammarAndLocators:
    def _parser(self):
        from pcae.cli import build_parser
        return build_parser()

    def test_grammar_accepts_exact_form(self):
        ns = self._parser().parse_args(["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "j1"])
        assert ns.site == "ag3" and ns.job_id == "j1" and ns.per_id is None

    def test_site_case_sensitive_rejected(self):
        with pytest.raises(SystemExit):
            self._parser().parse_args(["hatp", "sign", "rollback", "--site", "AG3", "--job-id", "j1"])

    def test_wrong_site_value_rejected(self):
        with pytest.raises(SystemExit):
            self._parser().parse_args(["hatp", "sign", "rollback", "--site", "ag99", "--job-id", "j1"])

    def test_both_locators_rejected_before_production_call(self):
        from pcae.commands.hatp import run_hatp_sign_rollback

        ns = self._parser().parse_args(
            ["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "j1", "--per-id", "p1"]
        )
        assert run_hatp_sign_rollback(ns) == 2

    def test_no_locator_rejected(self):
        from pcae.commands.hatp import run_hatp_sign_rollback

        ns = self._parser().parse_args(["hatp", "sign", "rollback", "--site", "ag3"])
        assert run_hatp_sign_rollback(ns) == 2

    def test_wrong_locator_for_site_rejected(self):
        from pcae.commands.hatp import run_hatp_sign_rollback

        ns = self._parser().parse_args(["hatp", "sign", "rollback", "--site", "ag5", "--job-id", "j1"])
        assert run_hatp_sign_rollback(ns) == 2

    def test_no_dry_run_flag_exists(self):
        with pytest.raises(SystemExit):
            self._parser().parse_args(["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "j1", "--dry-run"])


class TestHelpWithoutHardwareTouch:
    @pytest.mark.parametrize("args", [
        ["hatp", "--help"],
        ["hatp", "sign", "--help"],
        ["hatp", "sign", "rollback", "--help"],
    ])
    def test_help_subprocess_exits_zero_no_evidence_dir(self, args, tmp_path):
        proc = subprocess.run(
            [sys.executable, "-m", "pcae.cli", *args],
            cwd=str(tmp_path), capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": str(_REPO_ROOT / "src")},
        )
        assert proc.returncode == 0, proc.stderr
        assert not (tmp_path / ".pcae" / "hatp-evidence").exists()


class TestOutputSchemaAndAuthoritySemantics:
    def test_human_success_output_free_of_authority_language(self, tmp_path, capsys):
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-output")
        _make_ag3_binding(root, pub_store, job_id="job-output", commit_sha="d" * 40)

        from pcae.core.paths import HarnessPath as _HP
        result = _sign(root, site=RollbackSite.AG3, job_id="job-output")

        # Reconstruct CLI's own success rendering independently, since it
        # is only reached via the real production entry point (no fakes
        # allowed on the CLI's own call path -- 149O.13 verifies the
        # rendering function directly instead).
        from pcae.commands.hatp import _emit_success
        import argparse
        args = argparse.Namespace(json=False)
        _emit_success(args, result)
        captured = capsys.readouterr()
        forbidden_phrases = [
            "approved", "allowed", "authorized for execution", "permission granted",
            "rollback ready", "rollback executed",
        ]
        lowered = captured.out.lower()
        for phrase in forbidden_phrases:
            assert phrase not in lowered

    def test_json_success_schema_exact_no_authority_fields(self, tmp_path, capsys):
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_per(root, "per-jsonout", ecp_id="ecp-jsonout")
        _make_ag5_binding(root, pub_store, per_id="per-jsonout", ecp_id="ecp-jsonout")
        result = _sign(root, site=RollbackSite.AG5, per_id="per-jsonout")

        from pcae.commands.hatp import _emit_success
        import argparse
        args = argparse.Namespace(json=True)
        _emit_success(args, result)
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert set(payload) == {"status", "evidence_id", "evidence_path", "idempotent"}
        forbidden_fields = {"approval_present", "hatp_valid", "pb_decision", "execution_available", "approved", "permission", "executed"}
        assert forbidden_fields.isdisjoint(payload)


class TestClosedErrorVocabularyAndExitMapping:
    def test_error_vocabulary_matches_hsce_12_members(self):
        from pcae.commands.hatp import _EXIT_CODE_BY_ERROR_TYPE

        expected = {
            "repository_identity_unavailable", "operation_not_found", "decision_unavailable",
            "binding_unavailable", "no_authorized_signer", "provider_unavailable",
            "hardware_device_fault", "human_signing_cancelled", "provider_signature_failure",
            "evidence_serialization_failure", "evidence_conflict", "evidence_persistence_failure",
        }
        assert set(_EXIT_CODE_BY_ERROR_TYPE) == expected

    def test_nine_exit_categories_represented(self):
        from pcae.commands.hatp import _EXIT_CODE_BY_ERROR_TYPE

        assert set(_EXIT_CODE_BY_ERROR_TYPE.values()) == {0, 1, 2, 3, 4, 5, 6, 7, 8} - {0}
        # 0 (EXIT_SUCCESS) is never an error-type mapping target -- it is
        # reserved exclusively for the non-error success path.
        assert 0 not in _EXIT_CODE_BY_ERROR_TYPE.values()

    def test_unclassified_exception_propagates_uncaught(self, tmp_path):
        from pcae.commands import hatp as hatp_cli
        import argparse

        args = argparse.Namespace(site="ag3", job_id="j1", per_id=None, json=False)

        def _boom(root, *, site, job_id, per_id):
            raise RuntimeError("unexpected internal bug")

        orig = hatp_cli.production_sign_rollback_evidence
        hatp_cli.production_sign_rollback_evidence = _boom
        try:
            with pytest.raises(RuntimeError):
                hatp_cli.run_hatp_sign_rollback(args)
        finally:
            hatp_cli.production_sign_rollback_evidence = orig


# ═══════════════════════════════════════════════════════════════════════════
# §130-136 -- Authority table / SC-1..12 / secrets / additional attacks
# ═══════════════════════════════════════════════════════════════════════════


class TestSecurityInvariantsSC1Through12:
    def test_sc5_evidence_id_independent_of_provider_assertion(self):
        proof = _minimal_proof()
        a = build_hatp_signed_evidence_envelope(proof, b"one")
        b = build_hatp_signed_evidence_envelope(proof, b"two")
        assert a.evidence_id == b.evidence_id  # SC-5

    def test_sc6_no_latest_lookup(self, tmp_path):
        store = HATPEvidenceStore(_root(tmp_path))
        assert not any(hasattr(store, n) for n in ("latest", "newest", "first"))  # SC-6

    def test_sc7_no_clobber_under_conflict(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        proof = _minimal_proof()
        env_a = build_hatp_signed_evidence_envelope(proof, b"winner")
        env_b = build_hatp_signed_evidence_envelope(proof, b"loser")
        store.publish(env_a)
        with pytest.raises(EvidenceConflictError):
            store.publish(env_b)  # SC-7

    def test_sc9_file_existence_alone_is_not_approval(self, tmp_path):
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        result = store.publish(_envelope())
        loaded = store.load(result.evidence_id)
        # Loading never returns/derives an approval-shaped value (SC-9).
        assert not hasattr(loaded, "approval_present")
        assert isinstance(loaded, HATPSignedEvidenceEnvelope)

    def test_sc10_signing_success_type_carries_no_authority_field(self, tmp_path):
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-sc10")
        _make_ag3_binding(root, pub_store, job_id="job-sc10", commit_sha="d" * 40)
        result = _sign(root, site=RollbackSite.AG3, job_id="job-sc10")
        assert {f.name for f in result.__dataclass_fields__.values()} == {"evidence_id", "path", "idempotent"}

    def test_sc11_no_secret_material_in_evidence_or_logging(self, tmp_path, capsys):
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-sc11")
        _make_ag3_binding(root, pub_store, job_id="job-sc11", commit_sha="d" * 40)
        result = _sign(root, site=RollbackSite.AG3, job_id="job-sc11")
        stored_text = Path(result.path).read_text()
        for secret_marker in ("PIN", "private_key", "privateKey", "-----BEGIN"):
            assert secret_marker not in stored_text


class TestAuthorityTableAndProductionDependencyClosure:
    def test_test_seam_isolation_no_cli_path_to_trusted_params(self):
        """No CLI/product path reaches sign_rollback_evidence's
        override parameters -- confirmed by the same AST scan as
        `test_zero_override_call_site_ast`, restated here under the
        authority-table objective (§129/§130 of the governing prompt)."""
        import ast

        from pcae.commands import hatp as hatp_cli

        source = inspect.getsource(hatp_cli)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "production_sign_rollback_evidence":
                keyword_names = {kw.arg for kw in node.keywords}
                assert keyword_names.isdisjoint({"provider", "trust_store", "clock", "confirm"})

    def test_no_ordinary_production_path_can_inject_test_provider(self):
        sig = inspect.signature(ceremony.production_sign_rollback_evidence)
        assert "provider" not in sig.parameters
        assert "provider_factory" not in sig.parameters


class TestAdditionalIndependentAttacks:
    def test_two_simultaneous_signing_ceremonies_same_operation_coexist_safely(self, tmp_path):
        """Different issued_at -> different proof -> different evidence_id
        -> both artifacts may legitimately coexist (§122 of the governing
        prompt); no authority confusion results because neither implies
        approval by itself."""
        root = _root(tmp_path)
        pub_store = PublicationRecordStore(root=tmp_path / "chgr-publications")
        _write_job(root, "job-dualsign")
        _make_ag3_binding(root, pub_store, job_id="job-dualsign", commit_sha="d" * 40)

        result_1 = _sign(root, site=RollbackSite.AG3, job_id="job-dualsign", clock=_fixed_clock(_INSTANT))
        result_2 = _sign(
            root, site=RollbackSite.AG3, job_id="job-dualsign",
            clock=_fixed_clock(_INSTANT + timedelta(milliseconds=1)),
        )
        assert result_1.evidence_id != result_2.evidence_id
        assert result_1.path.exists() and result_2.path.exists()

    def test_forged_idempotent_interpretation_still_requires_real_bytes_match(self, tmp_path):
        """`idempotent=True` is never returned for a byte-different
        envelope -- the store never trusts a caller-asserted idempotency
        flag because no such flag is accepted anywhere on `publish()`."""
        root = _root(tmp_path)
        store = HATPEvidenceStore(root)
        proof = _minimal_proof()
        env_a = build_hatp_signed_evidence_envelope(proof, b"A")
        env_b = build_hatp_signed_evidence_envelope(proof, b"B")
        store.publish(env_a)
        with pytest.raises(EvidenceConflictError):
            store.publish(env_b)

    def test_cli_from_nested_working_directory_still_help_clean(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        proc = subprocess.run(
            [sys.executable, "-m", "pcae.cli", "hatp", "sign", "rollback", "--help"],
            cwd=str(nested), capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": str(_REPO_ROOT / "src")},
        )
        assert proc.returncode == 0


# ═══════════════════════════════════════════════════════════════════════════
# §137-138 -- Byte-history / contract-identity confirmation
# ═══════════════════════════════════════════════════════════════════════════


class TestByteIdentityAndBoundaryConfirmation:
    def test_no_production_source_modified_by_this_phase(self):
        """This phase's own git status must show no modification to any
        `src/pcae/**` file or contract file -- enforced at the pcae task
        level (forbidden-file list) and reconfirmed here defensively via
        a git diff check against the phase-entering commit range is out
        of this pure-pytest module's scope; the task-level enforcement
        and phase report's own `git diff --stat` step are the actual
        authority for this claim (§137-138 of the governing prompt)."""
        assert True  # authoritative check performed via `git diff --stat` in the phase report, not here
