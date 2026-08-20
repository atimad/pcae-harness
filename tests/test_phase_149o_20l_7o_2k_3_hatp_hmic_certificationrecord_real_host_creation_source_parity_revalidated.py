"""Phase 149O.20L.7O.2K.3 — HATP HMIC CertificationRecord Real-Host Creation,
Source-Parity Revalidated.

This phase performed exactly one real protected-state mutation on
hac-dell: creating one `CertificationRecord` via
`scripts/hatp_certification_admin.py create` against the already-parity
-restored deployment source at commit `305f8e7913bac76941dade6ff4e018c74533f062`
(established by 149O.20L.7O.2K.2). No activation, no binding, no FIDO2,
no Principal/Signer/DeploymentBinding, no Protected Root topology
change, and no source redeployment occurred in this phase.

These tests exercise only the local, repository-side ceremony surface
(the `certify()`/`ConfirmationDeclinedError` behavior already used to
disposable-test the create-only writer before the real host mutation).
They do not reach the real Dell Protected Root -- that evidence is
captured in the phase report, not re-derived by a local test suite.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import hatp_certification_admin as admin  # noqa: E402
from pcae.core.hatp_mandatory_certification import (  # noqa: E402
    CertificationRecordNotFoundError,
    _append_certification_record,
)

pytestmark = pytest.mark.fast_green

_FIXED_FIELDS = dict(
    repository_instance_id="12345678-1234-4123-8123-123456789abc",
    canonical_deployment_root="/tmp/fake-root",
    implementation_commit="deadbeef" * 5,
    implementation_scope_digest="ab" * 32,
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


def _patched_derivations():
    return [
        mock.patch("hatp_certification_admin.derive_repository_instance_id", return_value=_FIXED_FIELDS["repository_instance_id"]),
        mock.patch("hatp_certification_admin.derive_canonical_deployment_root", return_value=_FIXED_FIELDS["canonical_deployment_root"]),
        mock.patch("hatp_certification_admin.derive_implementation_commit", return_value=_FIXED_FIELDS["implementation_commit"]),
        mock.patch("hatp_certification_admin.derive_implementation_scope_digest", return_value=_FIXED_FIELDS["implementation_scope_digest"]),
        mock.patch("hatp_certification_admin.derive_contract_versions", return_value=_FIXED_FIELDS["contract_versions"]),
    ]


@pytest.fixture()
def disposable_root(tmp_path):
    protected = tmp_path / "trust-store"
    protected.mkdir()
    vr = tmp_path / "vr.txt"
    vr.write_text("disposable verification record content\n")
    patches = _patched_derivations()
    for p in patches:
        p.start()
    try:
        yield protected, vr
    finally:
        for p in patches:
            p.stop()


class TestCreateOnlyWriterBehavior:
    def test_confirm_false_declines_no_write(self, disposable_root):
        protected, vr = disposable_root
        with pytest.raises(admin.ConfirmationDeclinedError):
            admin.certify(
                repository_root=Path("."),
                certified_by="test",
                verification_record_path=vr,
                confirm=False,
                _protected_root=protected,
            )
        assert not (protected / "certifications.json").exists()

    def test_confirm_true_creates_exactly_one_active_record(self, disposable_root):
        protected, vr = disposable_root
        result = admin.certify(
            repository_root=Path("."),
            certified_by="test-operator",
            verification_record_path=vr,
            confirm=True,
            _protected_root=protected,
        )
        assert result.already_existed is False
        assert result.record.status == "active"
        assert result.record.contract_versions == _FIXED_FIELDS["contract_versions"]
        assert not (protected / "certification-bindings.json").exists()

    def test_exact_byte_identical_replay_is_idempotent_not_duplicated(self, disposable_root):
        protected, vr = disposable_root
        result = admin.certify(
            repository_root=Path("."),
            certified_by="test-operator",
            verification_record_path=vr,
            confirm=True,
            _protected_root=protected,
        )
        replay = _append_certification_record(protected, result.record)
        assert replay.idempotent is True
        assert replay.record.certification_id == result.certification_id

        certs_raw = json.loads((protected / "certifications.json").read_text())
        assert len(certs_raw["certifications"]) == 1

    def test_activate_on_unknown_id_fails_closed(self, disposable_root):
        protected, vr = disposable_root
        with pytest.raises(CertificationRecordNotFoundError):
            admin.activate(
                repository_root=Path("."),
                certification_id="nonexistent-id",
                confirm=True,
                _protected_root=protected,
            )


class TestNoOtherProtectedStateSurfaceTouched:
    def test_admin_script_never_imports_activation_or_hardware_modules(self):
        import_lines = [
            line
            for line in (REPO_ROOT / "scripts" / "hatp_certification_admin.py").read_text(encoding="utf-8").splitlines()
            if line.startswith("import ") or line.startswith("from ")
        ]
        joined = "\n".join(import_lines)
        assert "hatp_mandatory_cutover" not in joined
        assert "permission_broker" not in joined
        assert "fido2" not in joined.lower()

    def test_no_deploymentbinding_or_principal_writer_reachable_from_this_script(self):
        source = (REPO_ROOT / "scripts" / "hatp_certification_admin.py").read_text(encoding="utf-8")
        assert "DeploymentBinding" not in source
        assert "Principal" not in source
        assert "Signer" not in source
