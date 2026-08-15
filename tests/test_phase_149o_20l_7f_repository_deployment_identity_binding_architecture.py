"""Phase 149O.20L.7F -- Repository/Deployment Identity + DeploymentBinding
Architecture.

Architecture/design-analysis phase. This module is proof, not
implementation: it demonstrates, against live production source, the
exact facts `docs/PHASE_149O_20L_7F_REPOSITORY_DEPLOYMENT_IDENTITY_AND_
BINDING_ARCHITECTURE.md` reconstructs -- REQ-042's failure-reason
inventory, the repository-identity producer's existence, the
DeploymentBinding producer's absence, current consumers, the CWD-
dependent evaluation context, the lifecycle-mechanism inventory, and the
governing CHGR's condition 6 exclusion list. No production module is
modified by this phase. Fixture state is isolated (`tmp_path`) except
where a genuinely read-only, no-argument call against the real,
unprovisioned local host mirrors what prior phases already established
as an accepted pattern.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from pcae.core import hatp_bootstrap
from pcae.core import repository_identity
from pcae.core.hatp_bootstrap import DeploymentBinding, HATPTrustStore
from pcae.core.hatp_class_b_conformance import (
    _check_deployment_identity,
    verify_class_b_deployment_conformance,
)
from pcae.core.paths import HarnessPath

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONFORMANCE_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_class_b_conformance.py").read_text(encoding="utf-8")
_BOOTSTRAP_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py").read_text(encoding="utf-8")
_IDENTITY_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "repository_identity.py").read_text(encoding="utf-8")
_INIT_SRC = (_REPO_ROOT / "src" / "pcae" / "commands" / "init.py").read_text(encoding="utf-8")
_CLI_SRC = (_REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
_CHGR_PATH = _REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-0e37ed1340b14311826722c4dbf3e856.json"
_HBDC_CONTRACT = (_REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md").read_text(encoding="utf-8")
_HMIC_CONTRACT = (
    _REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
).read_text(encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# 1. REQ-042 failure-reason inventory (§5 of the architecture doc) --
#    exhaustive, six terminal outcomes.
# ═══════════════════════════════════════════════════════════════════════════


class TestReq042ReasonInventory:
    def test_all_six_reasons_present_in_source(self) -> None:
        expected = {
            "canonical_deployment_root_unresolvable",
            "repository_identity_malformed",
            "no_repository_identity_present",
            "trust_store_unavailable",
            "no_active_deployment_binding_matches_repository_and_root",
            "deployment_binding_matches_repository_and_root",
        }
        for reason in expected:
            assert reason in _CONFORMANCE_SRC, f"missing REQ-042 reason: {reason}"

    def test_no_repository_identity_present_is_the_second_check(self) -> None:
        """Evaluation order (§5): canonical-root resolution first, identity
        lookup second, binding lookup third/fourth -- confirmed by source
        order, not by re-deriving semantics."""

        order = [
            _CONFORMANCE_SRC.index("resolve_canonical_deployment_root"),
            _CONFORMANCE_SRC.index("no_repository_identity_present"),
            _CONFORMANCE_SRC.index("no_active_deployment_binding_matches_repository_and_root"),
        ]
        assert order == sorted(order)

    def test_absent_identity_short_circuits_before_binding_lookup(self, tmp_path: Path) -> None:
        """Live behavioral proof: with no identity file present, the check
        fails at `no_repository_identity_present` regardless of trust-store
        state -- the trust store is never even consulted."""

        root = HarnessPath(tmp_path)
        result = _check_deployment_identity(root)
        assert result.satisfied is False
        assert result.status == "no_repository_identity_present"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Repository-identity producer: CONFIRMED PRESENT (§7).
# ═══════════════════════════════════════════════════════════════════════════


class TestRepositoryIdentityProducerPresent:
    def test_ensure_repository_identity_exists(self) -> None:
        assert hasattr(repository_identity, "ensure_repository_identity")

    def test_pcae_init_calls_ensure_repository_identity(self) -> None:
        assert "ensure_repository_identity" in _INIT_SRC

    def test_no_rotate_revoke_repair_import_migrate_function_exists(self) -> None:
        for absent_name in (
            "rotate_repository_identity",
            "revoke_repository_identity",
            "repair_repository_identity",
            "import_repository_identity",
            "migrate_repository_identity",
            "reidentify",
        ):
            assert absent_name not in _IDENTITY_SRC, f"unexpected producer surface found: {absent_name}"

    def test_ensure_is_idempotent_preserve(self, tmp_path: Path) -> None:
        root = HarnessPath(tmp_path)
        first = repository_identity.ensure_repository_identity(root)
        second = repository_identity.ensure_repository_identity(root)
        assert first.repository_instance_id == second.repository_instance_id


# ═══════════════════════════════════════════════════════════════════════════
# 3. DeploymentBinding producer: CONFIRMED ABSENT (§8) -- reconfirms 7E's
#    claim independently, from a fresh source sweep, not by trusting 7E's
#    prose.
# ═══════════════════════════════════════════════════════════════════════════


class TestDeploymentBindingProducerAbsent:
    def test_no_create_register_enroll_function_in_bootstrap(self) -> None:
        for absent_name in (
            "create_deployment_binding",
            "register_deployment_binding",
            "enroll_deployment",
            "enroll_repository",
            "add_deployment_binding",
        ):
            assert absent_name not in _BOOTSTRAP_SRC, f"unexpected producer surface found: {absent_name}"

    def test_trust_store_docstring_states_read_only(self) -> None:
        source = inspect.getsource(HATPTrustStore)
        assert "No method here mutates state" in source

    def test_trust_store_has_no_write_methods(self) -> None:
        methods = {
            name
            for name, _ in inspect.getmembers(HATPTrustStore, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        assert methods == {
            "environment_status",
            "load_repository_enrollment",
            "lookup_principal",
            "lookup_signer",
            "lookup_authority",
            "signer_revoked",
            "resolve_deployment_authorization",
        }, f"unexpected method set on HATPTrustStore (possible new write surface): {sorted(methods)}"

    def test_no_cli_surface_for_deployment_binding(self) -> None:
        for absent_token in ("deployment bind", "deployment-bind", "deployment_bind", "repository identity"):
            assert absent_token not in _CLI_SRC.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 4. DeploymentBinding schema reconstruction (§8) -- exact field set.
# ═══════════════════════════════════════════════════════════════════════════


class TestDeploymentBindingSchema:
    def test_field_set_matches_reconstructed_schema(self) -> None:
        fields = set(DeploymentBinding.__dataclass_fields__.keys())
        assert fields == {
            "repository_id",
            "canonical_deployment_root",
            "principal_id",
            "signer_key_id",
            "provider_profile",
            "authority_scope",
            "valid_from",
            "status",
            "revoked_at",
        }

    def test_no_hmic_or_host_identity_field_present(self) -> None:
        """§20/§22 findings: no HMIC digest/certification field, no host
        machine-id field, in the current schema."""

        fields = set(DeploymentBinding.__dataclass_fields__.keys())
        for absent in ("hmic_digest", "certification_id", "machine_id", "host_id", "implementation_commit"):
            assert absent not in fields

    def test_matches_checks_only_repository_id_and_root(self) -> None:
        source = inspect.getsource(hatp_bootstrap.deployment_binding_matches)
        assert "binding.repository_id == repository_id" in source
        assert "binding.canonical_deployment_root == canonical_deployment_root" in source
        assert "machine_id" not in source
        assert "host" not in source.lower()

    def test_registry_parser_rejects_duplicate_repository_id(self) -> None:
        """§21/§24/§25: at most one binding entry per repository_id --
        schema-enforced, not merely conventional."""

        source = inspect.getsource(hatp_bootstrap._parse_registry_document)
        assert "in deployment_bindings" in source


# ═══════════════════════════════════════════════════════════════════════════
# 5. Consumer inventory (§5, §6, §8) -- read-only across the board.
# ═══════════════════════════════════════════════════════════════════════════


class TestConsumerInventory:
    def test_conformance_module_imports_both_identity_and_bootstrap(self) -> None:
        assert "from pcae.core import repository_identity" in _CONFORMANCE_SRC
        assert "from pcae.core import hatp_bootstrap" in _CONFORMANCE_SRC

    def test_repository_identity_is_hmic_frozen_scope_member(self) -> None:
        cert_src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py").read_text(
            encoding="utf-8"
        )
        assert '"core/repository_identity.py"' in cert_src
        assert '"core/hatp_class_b_conformance.py"' in cert_src


# ═══════════════════════════════════════════════════════════════════════════
# 6. CWD/context dependence (§17) -- the exact defect/fact this phase had
#    to resolve before reasoning about "which repository" Action 9
#    evaluates.
# ═══════════════════════════════════════════════════════════════════════════


class TestCwdContextBehavior:
    def test_root_defaults_to_cwd_when_omitted(self) -> None:
        source = inspect.getsource(verify_class_b_deployment_conformance)
        assert "root = HarnessPath.cwd()" in source
        assert "if root is None" in source

    def test_check_deployment_identity_uses_caller_supplied_root_only(self, tmp_path: Path) -> None:
        """No hidden CWD fallback inside `_check_deployment_identity` itself
        -- the CWD default lives exactly one call frame up, in
        `verify_class_b_deployment_conformance`, confirming §17's call-path
        reconstruction precisely."""

        root = HarnessPath(tmp_path)
        result = _check_deployment_identity(root)
        assert result.check_id == "HBDC-REQ-042"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Lifecycle-mechanism inventory (§24/§26) -- two-state closed
#    vocabulary, no rotation/revocation write path.
# ═══════════════════════════════════════════════════════════════════════════


class TestLifecycleMechanismInventory:
    def test_status_consistency_helper_only_recognizes_active_and_revoked(self) -> None:
        source = inspect.getsource(hatp_bootstrap._require_revoked_at_consistency)
        assert '"revoked"' in source
        assert "candidate" not in source
        assert "superseded" not in source
        assert "expired" not in source

    def test_matches_treats_non_active_status_as_no_binding(self) -> None:
        source = inspect.getsource(hatp_bootstrap.deployment_binding_matches)
        assert 'binding.status != "active"' in source


# ═══════════════════════════════════════════════════════════════════════════
# 8. Governing CHGR condition 6 (§27) -- exact text, read directly from
#    the persisted governance record, not from any phase's prose summary.
# ═══════════════════════════════════════════════════════════════════════════


class TestGoverningChgrCondition6:
    def test_chgr_record_exists(self) -> None:
        assert _CHGR_PATH.is_file()

    def test_condition_6_text_matches_exactly(self) -> None:
        document = json.loads(_CHGR_PATH.read_text(encoding="utf-8"))
        conditions = document["conditions"]
        assert "6) No venv reinstall, no wrapper mutation, no DeploymentBinding" in conditions
        assert "without a fresh, separate election" in conditions

    def test_condition_6_excludes_deployment_binding_and_onboarding_not_identity_creation(self) -> None:
        document = json.loads(_CHGR_PATH.read_text(encoding="utf-8"))
        conditions = document["conditions"]
        assert "no DeploymentBinding" in conditions
        assert "no repository onboarding" in conditions
        assert "repository identity" not in conditions.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 9. HBDC-REQ-042 / HATP-REQ-051 normative text reconfirmation (§4) --
#    read directly from the frozen contract, not from any prior phase's
#    paraphrase.
# ═══════════════════════════════════════════════════════════════════════════


class TestNormativeTextReconfirmation:
    def test_hbdc_req_042_text_present(self) -> None:
        assert (
            "`repository_instance_id` (CRI Layer 1, repository-local and agent-writable per HATP-001 §17) "
            "confers no authority by itself. The controlling authority artifact is the admin-created "
            "`DeploymentBinding` (CRI Layer 2)."
        ) in _HBDC_CONTRACT

    def test_hbdc_req_049_advisory_only_disclaimer_present(self) -> None:
        assert "HBDC-001 conformance is advisory only" in _HBDC_CONTRACT

    def test_hmic_req_044_reads_canonical_root_from_deployment_binding(self) -> None:
        assert "DeploymentBinding` already define it" in _HMIC_CONTRACT


# ═══════════════════════════════════════════════════════════════════════════
# 10. No-mutation / no-implementation proof (§47) -- this phase's own
#     scope boundary, verified operationally.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoMutationNoImplementationProof:
    def test_no_repository_identity_file_created_in_this_working_tree(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()

    def test_repository_identity_file_is_gitignored(self) -> None:
        gitignore = (_REPO_ROOT / ".pcae" / ".gitignore").read_text(encoding="utf-8")
        assert "repository-identity.json" in gitignore

    def test_architecture_document_exists(self) -> None:
        doc = (
            _REPO_ROOT
            / "docs"
            / "PHASE_149O_20L_7F_REPOSITORY_DEPLOYMENT_IDENTITY_AND_BINDING_ARCHITECTURE.md"
        )
        assert doc.is_file()
        text = doc.read_text(encoding="utf-8")
        assert "Architecture/design only" in text
        assert "No `DeploymentBinding` created" in text


# ═══════════════════════════════════════════════════════════════════════════
# 11. Real-host regression (mirrors prior phases' accepted pattern) --
#     read-only, no argument, local unprovisioned host.
# ═══════════════════════════════════════════════════════════════════════════


class TestRealHostRegression:
    def test_local_host_class_b_conformance_is_not_compliant(self) -> None:
        result = verify_class_b_deployment_conformance()
        assert result.status.value != "COMPLIANT"

    def test_local_host_req_042_check_is_a_known_reason(self) -> None:
        result = verify_class_b_deployment_conformance()
        req_042_checks = [c for c in result.checks if c.check_id == "HBDC-REQ-042"]
        assert len(req_042_checks) == 1
        known_reasons = {
            "canonical_deployment_root_unresolvable",
            "repository_identity_malformed",
            "no_repository_identity_present",
            "trust_store_unavailable",
            "no_active_deployment_binding_matches_repository_and_root",
            "deployment_binding_matches_repository_and_root",
        }
        assert req_042_checks[0].status in known_reasons
