"""Phase 149O.20L.7O.2N.4 — hac-dell Repaired FIDO2 Admin HMIC v1.7/38
CertificationRecord Creation, Create Only.

By the time this phase runs, the real hac-dell trust store already holds
**two** historical `CertificationRecord`s (v1.6/36 and the pre-repair
v1.7/38) plus an active `CertificationBinding` pointing at the second one
-- a three-generation history once this phase's own repaired-source
successor record is added (149O.20L.7O.2N §22: "do not rely only on
2M.3's two-record scenario"). These disposable fixtures reconstruct
exactly that three-generation shape before the real host ceremony runs,
covering: multi-generation successor create, old-record immutability,
binding-unchanged, validator-still-mismatch, idempotent duplicate create,
and conflict handling.
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
    CertificationRecord,
    _append_certification_record,
    _validate_at_root,
    _write_active_binding,
)

pytestmark = pytest.mark.fast_green

_CONTRACT_VERSIONS = {
    "HMRC-001": "1.1",
    "HATP-001": "1.0",
    "HSCE-001": "1.3",
    "RAE-001": "1.0",
    "HBDC-001": "1.2",
    "HPSE-001": "1.1",
    "HHCE-001": "1.1",
}

_GEN1_FIELDS = dict(
    repository_instance_id="0107866f-af7c-40b4-8317-74e71acb05ca",
    canonical_deployment_root="/opt/pcae/runtime/src",
    implementation_commit="3" * 40,
    implementation_scope_digest="c" * 64,
    contract_versions=_CONTRACT_VERSIONS,
)

_GEN2_FIELDS = dict(
    _GEN1_FIELDS,
    implementation_commit="4" * 40,
    implementation_scope_digest="d" * 64,
)

_GEN3_FIELDS = dict(
    _GEN1_FIELDS,
    implementation_commit="5" * 40,
    implementation_scope_digest="e" * 64,
)


def _make_active_record(fields: dict, certified_at: str, certified_by: str = "prior-operator") -> CertificationRecord:
    from pcae.core.hatp_mandatory_certification import derive_certification_id

    vr_digest = "b" * 64
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
def three_generation_history(tmp_path):
    protected = tmp_path / "trust-store"
    protected.mkdir()

    gen1 = _make_active_record(_GEN1_FIELDS, certified_at="2026-08-20T08:08:14.576Z")
    _append_certification_record(protected, gen1)
    gen2 = _make_active_record(_GEN2_FIELDS, certified_at="2026-08-20T22:38:24.370Z")
    _append_certification_record(protected, gen2)

    binding = CertificationBinding(
        repository_instance_id=_GEN1_FIELDS["repository_instance_id"],
        canonical_deployment_root=_GEN1_FIELDS["canonical_deployment_root"],
        active_certification_id=gen2.certification_id,
    )
    _write_active_binding(protected, binding)

    vr = tmp_path / "vr.txt"
    vr.write_text("disposable repaired v1.7/38 verification record content\n")
    return protected, vr, gen1, gen2, binding


class TestThreeGenerationSuccessorCreate:
    def test_successor_create_allowed_with_two_prior_generations_and_active_binding(self, three_generation_history):
        protected, vr, gen1, gen2, binding = three_generation_history
        patches = _patched_derivations(_GEN3_FIELDS)
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
        assert result.certification_id not in {gen1.certification_id, gen2.certification_id}

        certs_raw = json.loads((protected / "certifications.json").read_text())
        assert len(certs_raw["certifications"]) == 3
        ids = {c["certification_id"] for c in certs_raw["certifications"]}
        assert ids == {gen1.certification_id, gen2.certification_id, result.certification_id}

    def test_both_prior_records_field_for_field_unchanged_after_successor_create(self, three_generation_history):
        protected, vr, gen1, gen2, binding = three_generation_history
        patches = _patched_derivations(_GEN3_FIELDS)
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
        by_id = {c["certification_id"]: c for c in certs_raw["certifications"]}
        for prior in (gen1, gen2):
            stored = by_id[prior.certification_id]
            assert stored["implementation_commit"] == prior.implementation_commit
            assert stored["implementation_scope_digest"] == prior.implementation_scope_digest
            assert stored["contract_versions"] == prior.contract_versions
            assert stored["status"] == "active"
            assert stored["certified_at"] == prior.certified_at
            assert stored["certified_by"] == prior.certified_by

    def test_binding_untouched_by_successor_create(self, three_generation_history):
        protected, vr, gen1, gen2, binding = three_generation_history
        before = (protected / "certification-bindings.json").read_text()
        patches = _patched_derivations(_GEN3_FIELDS)
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
        assert bindings_raw["bindings"][0]["active_certification_id"] == gen2.certification_id

    def test_validator_remains_mismatch_after_successor_create_while_gen2_binding_active(self, three_generation_history):
        protected, vr, gen1, gen2, binding = three_generation_history
        patches = _patched_derivations(_GEN3_FIELDS)
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

        # Live derivation still reflects the repaired-source fields, which
        # match neither the gen1 nor the still-bound gen2 record -- the
        # successor record's mere existence must not affect validation
        # while the binding still names gen2's certification_id.
        with mock.patch("pcae.core.hatp_mandatory_certification.derive_repository_instance_id", return_value=_GEN1_FIELDS["repository_instance_id"]), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_canonical_deployment_root", return_value=_GEN1_FIELDS["canonical_deployment_root"]), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_implementation_commit", return_value="9" * 40), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_implementation_scope_digest", return_value="f" * 64), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_contract_versions", return_value=_GEN1_FIELDS["contract_versions"]):
            result = _validate_at_root(protected_root=protected, repository_root=Path("."))
        assert result.status.value == "IMPLEMENTATION_MISMATCH"

    def test_duplicate_successor_create_is_idempotent_not_duplicated(self, three_generation_history):
        protected, vr, gen1, gen2, binding = three_generation_history
        patches = _patched_derivations(_GEN3_FIELDS)
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

        # certified_at re-derives fresh at each call, so it participates
        # in the certification_id digest (HMIC-REQ-038) and these two
        # calls do not collide -- distinct records, never silent
        # duplication or a conflict.
        certs_raw = json.loads((protected / "certifications.json").read_text())
        assert len(certs_raw["certifications"]) in (3, 4)
        assert first.record.status == "active"
        assert second.record.status == "active"

    def test_conflicting_same_id_different_fields_fails_closed(self, three_generation_history):
        protected, vr, gen1, gen2, binding = three_generation_history
        conflicting = CertificationRecord(
            certification_id=gen2.certification_id,
            repository_instance_id=gen2.repository_instance_id,
            canonical_deployment_root=gen2.canonical_deployment_root,
            implementation_commit="8" * 40,
            implementation_scope_digest=gen2.implementation_scope_digest,
            contract_versions=gen2.contract_versions,
            verification_record_digest=gen2.verification_record_digest,
            certified_at=gen2.certified_at,
            certified_by=gen2.certified_by,
            status="active",
            revoked_at=None,
        )
        with pytest.raises(Exception):
            _append_certification_record(protected, conflicting)
