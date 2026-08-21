"""Phase 149O.20L.7O.2N.5 — hac-dell Repaired FIDO2 Admin HMIC v1.7/38
Certification Activation, Successor Binding Only.

This phase's real-host mutation repeats the successor-binding-only
pattern independently proven by 149O.20L.7O.2M.4 (rather than
149O.20L.7O.2K.5's first-activation pattern): a pre-repair
CertificationRecord + an old active CertificationBinding pointing at it
+ a repaired (successor) CertificationRecord already exist (the repaired
record created by 149O.20L.7O.2N.4), and this phase must *replace* the
existing binding to point at the repaired record, leaving both records
themselves untouched (HMIC-REQ-086/088/090/099). These disposable
fixtures re-exercise that scenario, plus the required negative/idempotent
cases, fresh before the real host ceremony runs -- deliberately not
reused from 2M.4's own test module (each real-effect phase re-derives
its own disposable proof, per governing-prompt item 21).
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
    CertificationRecordNotFoundError,
    _append_certification_record,
    _validate_at_root,
    _write_active_binding,
    _write_revocation,
    derive_certification_id,
)

pytestmark = pytest.mark.fast_green

_REPO_ID = "0107866f-af7c-40b4-8317-74e71acb05ca"
_DEPLOY_ROOT = "/opt/pcae/runtime/src"

_PRE_REPAIR_FIELDS = dict(
    repository_instance_id=_REPO_ID,
    canonical_deployment_root=_DEPLOY_ROOT,
    implementation_commit="4efcb255ca5340224f0278f724b939d794a553c" + "a",
    implementation_scope_digest="3" * 64,
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

_REPAIRED_FIELDS = dict(
    _PRE_REPAIR_FIELDS,
    implementation_commit="cdb77b75fc8bbca04340c7f25c405db3b07d32f" + "7",
    implementation_scope_digest="a" * 64,
)


def _make_active_record(fields: dict, certified_at: str, certified_by: str = "prior-operator"):
    from pcae.core.hatp_mandatory_certification import CertificationRecord

    vr_digest = "e" * 64
    all_fields = dict(fields, verification_record_digest=vr_digest, certified_at=certified_at, certified_by=certified_by)
    cid = derive_certification_id(all_fields)
    return CertificationRecord(certification_id=cid, status="active", revoked_at=None, **all_fields)


@pytest.fixture()
def pre_repair_and_repaired_cert_with_old_binding(tmp_path):
    protected = tmp_path / "trust-store"
    protected.mkdir()
    pre_repair_record = _make_active_record(_PRE_REPAIR_FIELDS, certified_at="2026-08-20T22:38:24.370Z")
    repaired_record = _make_active_record(_REPAIRED_FIELDS, certified_at="2026-08-21T08:29:48.434Z")
    assert pre_repair_record.certification_id != repaired_record.certification_id
    _append_certification_record(protected, pre_repair_record)
    _append_certification_record(protected, repaired_record)
    old_binding = CertificationBinding(
        repository_instance_id=_REPO_ID,
        canonical_deployment_root=_DEPLOY_ROOT,
        active_certification_id=pre_repair_record.certification_id,
    )
    _write_active_binding(protected, old_binding)
    return protected, pre_repair_record, repaired_record


def _activate(protected, certification_id, repository_root=Path(".")):
    with mock.patch("hatp_certification_admin.derive_repository_instance_id", return_value=_REPO_ID), \
         mock.patch("hatp_certification_admin.derive_canonical_deployment_root", return_value=_DEPLOY_ROOT):
        return admin.activate(
            repository_root=repository_root,
            certification_id=certification_id,
            confirm=True,
            _protected_root=protected,
        )


class TestSuccessorBindingActivation:
    def test_binding_switches_exactly_once_to_repaired(self, pre_repair_and_repaired_cert_with_old_binding):
        protected, pre_repair_record, repaired_record = pre_repair_and_repaired_cert_with_old_binding
        result = _activate(protected, repaired_record.certification_id)
        assert result.certification_id == repaired_record.certification_id

        bindings_raw = json.loads((protected / "certification-bindings.json").read_text())
        assert len(bindings_raw["bindings"]) == 1
        assert bindings_raw["bindings"][0]["active_certification_id"] == repaired_record.certification_id

    def test_both_records_unchanged_after_activation(self, pre_repair_and_repaired_cert_with_old_binding):
        protected, pre_repair_record, repaired_record = pre_repair_and_repaired_cert_with_old_binding
        before = (protected / "certifications.json").read_text()
        _activate(protected, repaired_record.certification_id)
        after = (protected / "certifications.json").read_text()
        assert after == before

    def test_validator_transitions_mismatch_to_valid(self, pre_repair_and_repaired_cert_with_old_binding):
        protected, pre_repair_record, repaired_record = pre_repair_and_repaired_cert_with_old_binding
        with mock.patch("pcae.core.hatp_mandatory_certification.derive_repository_instance_id", return_value=_REPO_ID), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_canonical_deployment_root", return_value=_DEPLOY_ROOT), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_implementation_commit", return_value=_REPAIRED_FIELDS["implementation_commit"]), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_implementation_scope_digest", return_value=_REPAIRED_FIELDS["implementation_scope_digest"]), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_contract_versions", return_value=_REPAIRED_FIELDS["contract_versions"]):
            before = _validate_at_root(protected_root=protected, repository_root=Path("."))
            assert before.status.value == "IMPLEMENTATION_MISMATCH"

            _activate(protected, repaired_record.certification_id)

            after = _validate_at_root(protected_root=protected, repository_root=Path("."))
            assert after.status.value == "VALID"

    def test_idempotent_activation_of_already_repaired_binding(self, pre_repair_and_repaired_cert_with_old_binding):
        protected, pre_repair_record, repaired_record = pre_repair_and_repaired_cert_with_old_binding
        _activate(protected, repaired_record.certification_id)
        before = (protected / "certification-bindings.json").read_text()
        result = _activate(protected, repaired_record.certification_id)
        after = (protected / "certification-bindings.json").read_text()
        assert result.certification_id == repaired_record.certification_id
        assert after == before

    def test_unknown_certification_id_rejected(self, pre_repair_and_repaired_cert_with_old_binding):
        protected, pre_repair_record, repaired_record = pre_repair_and_repaired_cert_with_old_binding
        with pytest.raises(CertificationRecordNotFoundError):
            _activate(protected, "f" * 64)
        bindings_raw = json.loads((protected / "certification-bindings.json").read_text())
        assert bindings_raw["bindings"][0]["active_certification_id"] == pre_repair_record.certification_id

    def test_revoked_repaired_certification_can_be_bound_but_validator_reports_revoked(self, pre_repair_and_repaired_cert_with_old_binding):
        protected, pre_repair_record, repaired_record = pre_repair_and_repaired_cert_with_old_binding
        _write_revocation(protected, certification_id=repaired_record.certification_id, revoked_at="2026-08-21T09:00:00.000Z")
        # activate() only structurally checks existence/parse, never status -- HMIC-REQ item-21.
        result = _activate(protected, repaired_record.certification_id)
        assert result.certification_id == repaired_record.certification_id
        with mock.patch("pcae.core.hatp_mandatory_certification.derive_repository_instance_id", return_value=_REPO_ID), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_canonical_deployment_root", return_value=_DEPLOY_ROOT), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_implementation_commit", return_value=_REPAIRED_FIELDS["implementation_commit"]), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_implementation_scope_digest", return_value=_REPAIRED_FIELDS["implementation_scope_digest"]), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_contract_versions", return_value=_REPAIRED_FIELDS["contract_versions"]):
            after = _validate_at_root(protected_root=protected, repository_root=Path("."))
        assert after.status.value == "REVOKED"

    def test_malformed_certifications_file_fails_closed_on_activate(self, pre_repair_and_repaired_cert_with_old_binding):
        protected, pre_repair_record, repaired_record = pre_repair_and_repaired_cert_with_old_binding
        (protected / "certifications.json").write_text("{not valid json")
        with pytest.raises(Exception):
            _activate(protected, repaired_record.certification_id)
        # Binding must remain untouched by the failed attempt.
        bindings_raw = json.loads((protected / "certification-bindings.json").read_text())
        assert bindings_raw["bindings"][0]["active_certification_id"] == pre_repair_record.certification_id

    def test_conflicting_repository_deployment_state_yields_wrong_repository(self, pre_repair_and_repaired_cert_with_old_binding):
        # A binding correctly keyed on the real (repository_instance_id,
        # canonical_deployment_root) tuple, but pointing at a record whose
        # OWN stored repository_instance_id field differs (e.g. a record
        # improperly copied from a different repository) must fail closed
        # as WRONG_REPOSITORY, never silently validate.
        protected, pre_repair_record, repaired_record = pre_repair_and_repaired_cert_with_old_binding
        foreign_fields = dict(_REPAIRED_FIELDS, repository_instance_id="99999999-9999-4999-8999-999999999999")
        foreign_record = _make_active_record(foreign_fields, certified_at="2026-08-21T09:30:00.000Z")
        _append_certification_record(protected, foreign_record)
        _activate(protected, foreign_record.certification_id)

        with mock.patch("pcae.core.hatp_mandatory_certification.derive_repository_instance_id", return_value=_REPO_ID), \
             mock.patch("pcae.core.hatp_mandatory_certification.derive_canonical_deployment_root", return_value=_DEPLOY_ROOT):
            result = _validate_at_root(protected_root=protected, repository_root=Path("."))
        assert result.status.value == "WRONG_REPOSITORY"

    def test_no_other_protected_state_mutation(self, pre_repair_and_repaired_cert_with_old_binding):
        protected, pre_repair_record, repaired_record = pre_repair_and_repaired_cert_with_old_binding
        pre_existing_files = {p.name for p in protected.iterdir()}
        _activate(protected, repaired_record.certification_id)
        post_files = {p.name for p in protected.iterdir()}
        # Only certification-bindings.json may have been rewritten; no new
        # file (e.g. an extra certifications.json entry, a stray artifact)
        # is created by activation.
        assert post_files == pre_existing_files
