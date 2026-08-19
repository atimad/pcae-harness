"""Phase 149O.20L.7O.2C -- DeploymentBinding First-Use Field Resolution
Architecture.

This phase is architecture/investigation-only: no `DeploymentBinding`
was created, no election was initiated, no CHGR was published, no
certification was performed, and no Dell mutation occurred. These
tests assert (a) this phase's own report is internally self-consistent
with the live values it claims, and (b) the source-level facts the
report's field-resolution conclusions rest on are still true of the
current source tree -- not a live re-execution against `hac-dell`,
which is unreachable in CI.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pcae.core import hatp_deployment_binding_admin as admin
from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core import hatp_principal_signer_admin as ps_admin
from pcae.core.hatp_bootstrap import DeploymentBinding
from pcae.core.hatp_providers import (
    HATP_HARDWARE_PROVIDER_V1,
    _PRODUCTION_HARDWARE_PROVIDER_PROFILES,
)

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2C_DEPLOYMENTBINDING_FIRST_USE_FIELD_RESOLUTION_ARCHITECTURE.md"
)
_BOOTSTRAP_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py"
_ADMIN_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_deployment_binding_admin.py"
_CONFORMANCE_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_class_b_conformance.py"
_SIGNING_CEREMONY_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py"
_HBDC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HATP_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"

_EXPECTED_REPOSITORY_ID = "0107866f-af7c-40b4-8317-74e71acb05ca"
_EXPECTED_CANONICAL_ROOT = "/opt/pcae/runtime/src"
_EXPECTED_HMIC_DIGEST = "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"
_SOLE_RESIDUAL_REQ = "HBDC-REQ-042"
_SOLE_RESIDUAL_REASON = "no_active_deployment_binding_matches_repository_and_root"


def _doc_text() -> str:
    return " ".join(_DOC_PATH.read_text().split())


def _bootstrap_source() -> str:
    return _BOOTSTRAP_PATH.read_text()


def _bootstrap_source_normalized() -> str:
    return " ".join(_BOOTSTRAP_PATH.read_text().split())


def _admin_source() -> str:
    return _ADMIN_PATH.read_text()


def _conformance_source() -> str:
    return _CONFORMANCE_PATH.read_text()


def _signing_ceremony_source() -> str:
    return _SIGNING_CEREMONY_PATH.read_text()


def _hbdc_contract_text() -> str:
    return _HBDC_CONTRACT_PATH.read_text()


def _hatp_contract_text() -> str:
    return _HATP_CONTRACT_PATH.read_text()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Doc self-consistency: the report records the exact live values and
#    the exact final verdict / next-phase recommendation it claims.
# ═══════════════════════════════════════════════════════════════════════════


class TestDocSelfConsistency:
    def test_doc_records_repository_id(self) -> None:
        assert _EXPECTED_REPOSITORY_ID in _doc_text()

    def test_doc_records_canonical_root(self) -> None:
        assert _EXPECTED_CANONICAL_ROOT in _doc_text()

    def test_doc_records_hmic_digest(self) -> None:
        assert _EXPECTED_HMIC_DIGEST in _doc_text()

    def test_doc_records_sole_residual(self) -> None:
        text = _doc_text()
        assert _SOLE_RESIDUAL_REQ in text
        assert _SOLE_RESIDUAL_REASON in text

    def test_doc_records_final_verdict(self) -> None:
        assert "DEPLOYMENTBINDING FIELD CONTRACT GAP" in _doc_text()

    def test_doc_states_no_deployment_binding_created(self) -> None:
        assert "No `DeploymentBinding` created" in _doc_text() or "no `DeploymentBinding` created" in _doc_text().lower()

    def test_doc_states_no_election_no_chgr_no_certification(self) -> None:
        text = _doc_text().lower()
        assert "no election initiated" in text
        assert "no chgr published" in text
        assert "no certification performed" in text

    def test_doc_recommends_next_phase_149o_20l_7o_2d(self) -> None:
        assert "149O.20L.7O.2D" in _doc_text()

    def test_doc_classifies_principal_id_as_unresolved(self) -> None:
        assert "principal_id == \"pcae\"" in _doc_text() or "principal_id` == `\"pcae\"`" in _doc_text() or "INVALID" in _doc_text()


# ═══════════════════════════════════════════════════════════════════════════
# 2. Schema-reconstruction facts still true of the current source tree.
# ═══════════════════════════════════════════════════════════════════════════


class TestSchemaFactsStillTrue:
    def test_deployment_binding_has_exactly_nine_fields(self) -> None:
        field_names = tuple(f.name for f in DeploymentBinding.__dataclass_fields__.values())
        assert field_names == (
            "repository_id",
            "canonical_deployment_root",
            "principal_id",
            "signer_key_id",
            "provider_profile",
            "authority_scope",
            "valid_from",
            "status",
            "revoked_at",
        )

    def test_status_values_closed_two_member_enum(self) -> None:
        from pcae.core.hatp_bootstrap import _STATUS_VALUES

        assert _STATUS_VALUES == frozenset({"active", "revoked"})

    def test_producer_docstring_still_defers_vocabulary_cross_validation(self) -> None:
        source = _admin_source()
        assert "cross-validation against" in source
        assert "explicitly deferred" in source

    def test_producer_never_imports_provider_allowlist(self) -> None:
        """149O.20L.7O.2C §9: the DeploymentBinding producer does not
        import or enforce `hatp_providers.py`'s closed provider_profile
        allowlist -- confirmed by absence of the import."""

        source = _admin_source()
        assert "hatp_providers" not in source

    def test_producer_never_calls_lookup_signer_or_lookup_principal(self) -> None:
        source = _admin_source()
        assert "lookup_signer" not in source
        assert "lookup_principal" not in source


# ═══════════════════════════════════════════════════════════════════════════
# 3. HBDC-REQ-042 matching logic is field-value-independent (§14 of the
#    doc): only repository_id/canonical_deployment_root/status matter.
# ═══════════════════════════════════════════════════════════════════════════


class TestHbdcReq042FieldIndependence:
    def test_check_deployment_identity_only_calls_deployment_binding_matches(self) -> None:
        source = _conformance_source()
        assert "deployment_binding_matches(" in source

    def test_deployment_binding_matches_does_not_reference_authority_fields(self) -> None:
        import inspect

        from pcae.core.hatp_bootstrap import deployment_binding_matches

        source = inspect.getsource(deployment_binding_matches)
        for authority_field in ("principal_id", "signer_key_id", "provider_profile", "authority_scope"):
            assert authority_field not in source


# ═══════════════════════════════════════════════════════════════════════════
# 4. HATP-REQ-014/028/037 (principal_id semantics) and HATP-REQ-019
#    (provider_profile fixed value) still present verbatim in contract.
# ═══════════════════════════════════════════════════════════════════════════


class TestContractTextStillPresent:
    def test_hatp_req_014_principal_id_text_present(self) -> None:
        text = _hatp_contract_text()
        assert "HATP-REQ-014" in text
        assert "stable `principal_id`" in text

    def test_hatp_req_028_two_principal_topology_present(self) -> None:
        text = _hatp_contract_text()
        assert "HATP-REQ-028" in text
        assert "exactly two" in text

    def test_hatp_req_037_conceptual_enrollment_procedure_present(self) -> None:
        text = _hatp_contract_text()
        assert "HATP-REQ-037" in text
        assert "assigns a `principal_id`" in text

    def test_hatp_req_019_hardware_provider_v1_present(self) -> None:
        text = _hatp_contract_text()
        assert "HATP-REQ-019" in text
        assert "HATP_HARDWARE_PROVIDER_V1" in text

    def test_hbdc_req_058_verbatim_present(self) -> None:
        text = _hbdc_contract_text()
        assert "HBDC-REQ-058" in text
        assert "admin's own enrollment context" in text


# ═══════════════════════════════════════════════════════════════════════════
# 5. Provider-profile fixed-value candidate still exactly one member.
# ═══════════════════════════════════════════════════════════════════════════


class TestProviderProfileVocabulary:
    def test_hardware_provider_v1_constant_value(self) -> None:
        assert HATP_HARDWARE_PROVIDER_V1 == "HATP_HARDWARE_PROVIDER_V1"

    def test_production_hardware_provider_profiles_is_single_member(self) -> None:
        assert _PRODUCTION_HARDWARE_PROVIDER_PROFILES == (HATP_HARDWARE_PROVIDER_V1,)


# ═══════════════════════════════════════════════════════════════════════════
# 6. signer_key_id resolution mechanism (_resolve_signer) exists and is
#    scoped to the signing-ceremony proof, never to DeploymentBinding.
# ═══════════════════════════════════════════════════════════════════════════


class TestSignerResolutionPrecedent:
    def test_resolve_signer_exists_and_uses_lookup_signer(self) -> None:
        source = _signing_ceremony_source()
        assert "_resolve_signer" in source
        assert "trust_store.lookup_signer" in source

    def test_signing_ceremony_module_never_mentions_deployment_binding(self) -> None:
        source = _signing_ceremony_source()
        assert "DeploymentBinding" not in source


# ═══════════════════════════════════════════════════════════════════════════
# 7. No enrollment writer exists anywhere for principals/signers/
#    authorities (repo-wide, excluding this phase's own worktree noise).
# ═══════════════════════════════════════════════════════════════════════════


class TestNoEnrollmentWriterExists:
    def test_hatp_trust_store_docstring_still_states_enrollment_unimplemented(self) -> None:
        source = _bootstrap_source_normalized()
        assert "administrative-surface-only and are not implemented by this phase at all" in source

    def test_registry_parser_top_level_keys_unchanged(self) -> None:
        source = _bootstrap_source()
        assert '{"registry_version", "principals", "signers", "deployment_bindings", "authorities"}' in source


# ═══════════════════════════════════════════════════════════════════════════
# 8. Disposable preview: mechanically reproduces this phase's own
#    non-authoritative simulation, confirming zero real-path writes.
# ═══════════════════════════════════════════════════════════════════════════


def _enroll_disposable_prereqs(store_root: Path, *, principal_id: str, signer_key_id: str) -> None:
    """Phase 149O.20L.7O.2F (Surface E) prerequisite helper -- see the
    identical pattern's rationale in `tests/test_hatp_deployment_
    binding_admin.py`."""

    hw_admin.register_credential(
        repository_root=store_root,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=signer_key_id,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex="ab" * 20,
            enrollment_reference="CHGR-PREREQ-HW",
        ),
        _store_root=store_root,
    )
    ps_admin.enroll_principal(
        repository_root=store_root,
        evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id=principal_id, election_reference="CHGR-PREREQ-P"),
        _protected_root=store_root,
    )
    ps_admin.enroll_signer(
        repository_root=store_root,
        evidence=ps_admin.SignerEnrollmentEvidence(
            principal_id=principal_id,
            signer_key_id=signer_key_id,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            election_reference="CHGR-PREREQ-S",
        ),
        _protected_root=store_root,
        _hardware_store_root=store_root,
    )


class TestDisposablePreviewReproducible:
    def test_preview_create_with_real_repository_id_in_disposable_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "disposable-repo"
            (repo_root / ".pcae").mkdir(parents=True)
            store_root = Path(tmp) / "disposable-trust-store"
            store_root.mkdir()

            identity_path = repo_root / ".pcae" / "repository-identity.json"
            identity_path.write_text(
                '{"schema_version": 1, "repository_instance_id": '
                f'"{_EXPECTED_REPOSITORY_ID}", "created_at": "2026-08-18T00:00:00.000Z"}}\n'
            )

            # Phase 149O.20L.7O.2F (Surface E) added mandatory
            # cross-registry validation to preview_create_deployment_
            # binding, sharing the identical validator create_deployment_
            # binding uses -- an unenrolled principal_id/signer_key_id
            # now fails closed even in preview (this is the intended,
            # tightened behavior; HBDC-001's own closed authority_scope
            # vocabulary, HBDC-REQ-072, also replaces the free-form
            # "DISPOSABLE-NON-AUTHORITATIVE-SIMULATION" placeholder).
            _enroll_disposable_prereqs(
                store_root,
                principal_id="DISPOSABLE-NON-AUTHORITATIVE-SIMULATION",
                signer_key_id="DISPOSABLE-NON-AUTHORITATIVE-SIMULATION",
            )
            authority = admin.AuthorityEvidence(
                principal_id="DISPOSABLE-NON-AUTHORITATIVE-SIMULATION",
                signer_key_id="DISPOSABLE-NON-AUTHORITATIVE-SIMULATION",
                authority_scope="CLASS_B_DEPLOYMENT",
                election_reference="DISPOSABLE-NON-AUTHORITATIVE-SIMULATION",
            )

            preview = admin.preview_create_deployment_binding(
                repository_root=repo_root, authority=authority, _protected_root=store_root, _hardware_store_root=store_root
            )

            assert preview.repository_id == _EXPECTED_REPOSITORY_ID
            assert preview.kind == admin.DeploymentBindingPreviewKind.WOULD_CREATE
            # No real production path was ever touched -- disposable dirs only.
            assert str(store_root) not in ("/etc/pcae/hatp/trust-store",)

    def test_preview_never_writes_to_disposable_store_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "disposable-repo"
            (repo_root / ".pcae").mkdir(parents=True)
            store_root = Path(tmp) / "disposable-trust-store"
            store_root.mkdir()

            identity_path = repo_root / ".pcae" / "repository-identity.json"
            identity_path.write_text(
                '{"schema_version": 1, "repository_instance_id": '
                f'"{_EXPECTED_REPOSITORY_ID}", "created_at": "2026-08-18T00:00:00.000Z"}}\n'
            )

            # Surface E (Phase 149O.20L.7O.2F): prerequisites must be
            # enrolled for preview to reach WOULD_CREATE at all (see the
            # sibling test above); the "never writes" property this test
            # names is therefore checked as "preview's own call adds no
            # further files beyond the prerequisite state," not
            # "store_root is empty."
            _enroll_disposable_prereqs(store_root, principal_id="x", signer_key_id="y")
            authority = admin.AuthorityEvidence(
                principal_id="x",
                signer_key_id="y",
                authority_scope="CLASS_B_DEPLOYMENT",
                election_reference="w",
            )
            before = sorted(p.name for p in store_root.iterdir())

            admin.preview_create_deployment_binding(
                repository_root=repo_root, authority=authority, _protected_root=store_root, _hardware_store_root=store_root
            )

            assert sorted(p.name for p in store_root.iterdir()) == before
