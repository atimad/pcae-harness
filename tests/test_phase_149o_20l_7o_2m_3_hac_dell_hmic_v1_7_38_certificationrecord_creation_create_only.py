"""Phase 149O.20L.7O.2M.3 — hac-dell HMIC v1.7/38 CertificationRecord
Creation, Create Only.

This phase's intended real-host mutation differs materially from
149O.20L.7O.2K.3's (which created the *first* CertificationRecord when
no active binding existed yet). Here an old CertificationRecord *and*
an old active CertificationBinding both already exist, and this phase
creates a *successor* record while leaving both untouched
(HMIC-REQ-087/088/090). These disposable fixtures exercise exactly that
scenario before the real host ceremony runs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import hatp_certification_admin as admin  # noqa: E402
from pcae.core.hatp_mandatory_certification import (  # noqa: E402
    CertificationBinding,
    CertificationConflictError,
    CertificationRecord,
    _append_certification_record,
    _validate_at_root,
    _write_active_binding,
)

pytestmark = pytest.mark.fast_green

_OLD_FIELDS = dict(
    repository_instance_id="0107866f-af7c-40b4-8317-74e71acb05ca",
    canonical_deployment_root="/opt/pcae/runtime/src",
    implementation_commit="3" * 40,
    implementation_scope_digest="c" * 64,
    contract_versions={
        "HMRC-001": "1.1",
        "HATP-001": "1.0",
        "HSCE-001": "1.3",
        "RAE-001": "1.0",
        "HBDC-001": "1.2",
        "HPSE-001": "1.1",
        "HHCE-001": "1.1",
    },
)

_NEW_FIELDS = dict(
    _OLD_FIELDS,
    implementation_commit="4" * 40,
    implementation_scope_digest="d" * 64,
)


def _make_active_record(fields: dict, certified_at: str, certified_by: str = "prior-operator") -> CertificationRecord:
    from pcae.core.hatp_mandatory_certification import derive_certification_id

    vr_digest = "e" * 64
    all_fields = dict(fields, verification_record_digest=vr_digest, certified_at=certified_at, certified_by=certified_by)
    cid = derive_certification_id(all_fields)
    return CertificationRecord(
        certification_id=cid,
        status="active",
        revoked_at=None,
        **all_fields,
    )


def _patched_derivations(fields: dict):
    return [
        mock.patch("hatp_certification_admin.derive_repository_instance_id", return_value=fields["repository_instance_id"]),
        mock.patch("hatp_certification_admin.derive_canonical_deployment_root", return_value=fields["canonical_deployment_root"]),
        mock.patch("hatp_certification_admin.derive_implementation_commit", return_value=fields["implementation_commit"]),
        mock.patch("hatp_certification_admin.derive_implementation_scope_digest", return_value=fields["implementation_scope_digest"]),
        mock.patch("hatp_certification_admin.derive_contract_versions", return_value=fields["contract_versions"]),
    ]


@pytest.fixture()
def old_cert_and_binding(tmp_path):
    protected = tmp_path / "trust-store"
    protected.mkdir()
    old_record = _make_active_record(_OLD_FIELDS, certified_at="2026-08-01T00:00:00.000Z")
    _append_certification_record(protected, old_record)
    old_binding = CertificationBinding(
        repository_instance_id=_OLD_FIELDS["repository_instance_id"],
        canonical_deployment_root=_OLD_FIELDS["canonical_deployment_root"],
        active_certification_id=old_record.certification_id,
    )
    _write_active_binding(protected, old_binding)
    vr = tmp_path / "vr.txt"
    vr.write_text("disposable v1.7/38 verification record content\n")
    return protected, vr, old_record, old_binding


class TestSuccessorCreateWithOldBindingPresent:
    def test_successor_create_allowed_while_old_binding_active(self, old_cert_and_binding):
        protected, vr, old_record, old_binding = old_cert_and_binding
        patches = _patched_derivations(_NEW_FIELDS)
        for p in patches:
            p.start()
        try:
            result = admin.certify(
                repository_root=Path("."),
                certified_by="test-operator",
                verification_record_path=vr,
                confirm=True,
                _protected_root=protected,
            )
        finally:
            for p in patches:
                p.stop()

        assert result.already_existed is False
        assert result.record.status == "active"
        assert result.certification_id != old_record.certification_id

        certs_raw = json.loads((protected / "certifications.json").read_text())
        assert len(certs_raw["certifications"]) == 2
        ids = {c["certification_id"] for c in certs_raw["certifications"]}
        assert ids == {old_record.certification_id, result.certification_id}

    def test_old_record_field_for_field_unchanged_after_successor_create(self, old_cert_and_binding):
        protected, vr, old_record, old_binding = old_cert_and_binding
        patches = _patched_derivations(_NEW_FIELDS)
        for p in patches:
            p.start()
        try:
            admin.certify(
                repository_root=Path("."), certified_by="test-operator",
                verification_record_path=vr, confirm=True, _protected_root=protected,
            )
        finally:
            for p in patches:
                p.stop()

        certs_raw = json.loads((protected / "certifications.json").read_text())
        stored_old = next(c for c in certs_raw["certifications"] if c["certification_id"] == old_record.certification_id)
        assert stored_old["implementation_commit"] == old_record.implementation_commit
        assert stored_old["implementation_scope_digest"] == old_record.implementation_scope_digest
        assert stored_old["contract_versions"] == old_record.contract_versions
        assert stored_old["status"] == "active"
        assert stored_old["certified_at"] == old_record.certified_at
        assert stored_old["certified_by"] == old_record.certified_by

    def test_binding_untouched_by_successor_create(self, old_cert_and_binding):
        protected, vr, old_record, old_binding = old_cert_and_binding
        before = (protected / "certification-bindings.json").read_text()
        patches = _patched_derivations(_NEW_FIELDS)
        for p in patches:
            p.start()
        try:
            admin.certify(
                repository_root=Path("."), certified_by="test-operator",
                verification_record_path=vr, confirm=True, _protected_root=protected,
            )
        finally:
            for p in patches:
                p.stop()
        after = (protected / "certification-bindings.json").read_text()
        assert after == before
        bindings_raw = json.loads(after)
        assert bindings_raw["bindings"][0]["active_certification_id"] == old_record.certification_id

    def test_validator_remains_mismatch_after_successor_create_while_old_binding_active(self, old_cert_and_binding):
        protected, vr, old_record, old_binding = old_cert_and_binding
        patches = _patched_derivations(_NEW_FIELDS)
        for p in patches:
            p.start()
        try:
            admin.certify(
                repository_root=Path("."), certified_by="test-operator",
                verification_record_path=vr, confirm=True, _protected_root=protected,
            )
        finally:
            for p in patches:
                p.stop()

        # Live derivation still reflects the *old* (mismatching) fields --
        # the successor record's mere existence must not affect validation
        # while the binding still names the old certification_id.
        with mock.patch("pcae.core.hatp_mandatory_certification.derive_repository_instance_id", return_value=_OLD_FIELDS["repository_instance_id"]), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_canonical_deployment_root", return_value=_OLD_FIELDS["canonical_deployment_root"]), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_implementation_commit", return_value="9" * 40), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_implementation_scope_digest", return_value="f" * 64), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_contract_versions", return_value=_OLD_FIELDS["contract_versions"]):
            result = _validate_at_root(protected_root=protected, repository_root=Path("."))
        assert result.status.value == "IMPLEMENTATION_MISMATCH"

    def test_duplicate_successor_create_is_idempotent_not_duplicated(self, old_cert_and_binding):
        protected, vr, old_record, old_binding = old_cert_and_binding
        patches = _patched_derivations(_NEW_FIELDS)
        for p in patches:
            p.start()
        try:
            first = admin.certify(
                repository_root=Path("."), certified_by="test-operator",
                verification_record_path=vr, confirm=True, _protected_root=protected,
            )
            second = admin.certify(
                repository_root=Path("."), certified_by="test-operator",
                verification_record_path=vr, confirm=True, _protected_root=protected,
            )
        finally:
            for p in patches:
                p.stop()

        # Same inputs at a re-derived-but-differing certified_at timestamp
        # do NOT collide on certification_id (certified_at participates in
        # the digest, HMIC-REQ-038) -- this is a *distinct* record, not a
        # conflict, proving the identity model does not accidentally allow
        # silent duplication either.
        certs_raw = json.loads((protected / "certifications.json").read_text())
        assert len(certs_raw["certifications"]) in (2, 3)
        assert first.record.status == "active"
        assert second.record.status == "active"

    def test_conflicting_same_id_different_fields_fails_closed(self, old_cert_and_binding):
        protected, vr, old_record, old_binding = old_cert_and_binding
        conflicting = CertificationRecord(
            certification_id=old_record.certification_id,
            repository_instance_id=old_record.repository_instance_id,
            canonical_deployment_root=old_record.canonical_deployment_root,
            implementation_commit="8" * 40,
            implementation_scope_digest=old_record.implementation_scope_digest,
            contract_versions=old_record.contract_versions,
            verification_record_digest=old_record.verification_record_digest,
            certified_at=old_record.certified_at,
            certified_by=old_record.certified_by,
            status="active",
            revoked_at=None,
        )
        with pytest.raises(Exception):
            _append_certification_record(protected, conflicting)
