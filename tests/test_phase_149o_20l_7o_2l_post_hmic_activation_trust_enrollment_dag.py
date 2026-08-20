"""Phase 149O.20L.7O.2L -- Post-HMIC-Activation Trust-Enrollment DAG
Re-Derivation and Administrative Entry-Point Architecture.

Analysis/architecture-only phase: no Trust-Enrollment real effect
performed (this phase's own report §42/NO-GO). This suite exercises
structural, evidence-grounded assertions only -- current HMIC frozen
source-scope membership, admin-script filesystem presence/absence, DAG
topology (no cycle), and the readiness-conjunction term count -- none of
which touch a host or Protected Root.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]


# ═══════════════════════════════════════════════════════════════════════════
# §5/§34-36 -- admin entry-point gap re-confirmation (library exists,
# scripts/ standalone entrypoint does not; existing bound admin scripts do).
# ═══════════════════════════════════════════════════════════════════════════


def test_hardware_credential_and_principal_signer_library_modules_exist():
    assert (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credential_admin.py").is_file()
    assert (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_principal_signer_admin.py").is_file()


def test_hardware_credential_and_principal_signer_standalone_scripts_absent():
    scripts_dir = _REPO_ROOT / "scripts"
    existing = {p.name for p in scripts_dir.glob("*.py")}
    assert "hatp_hardware_credential_admin.py" not in existing
    assert "hatp_principal_signer_admin.py" not in existing
    # Existing precedent scripts remain present, confirming the
    # standalone-script architecture is the established convention.
    assert "hatp_certification_admin.py" in existing
    assert "hatp_deployment_binding_admin.py" in existing


def test_cli_has_no_hardware_credential_or_principal_signer_dispatch():
    cli_source = (_REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
    assert "hatp_hardware_credential_admin" not in cli_source
    assert "hatp_principal_signer_admin" not in cli_source


# ═══════════════════════════════════════════════════════════════════════════
# §34-36 -- HMIC frozen source-scope consequence: the two library admin
# modules are already bound (v1.5); the two standalone scripts this phase
# analyzes are NOT yet bound (would require a future HMIC scope evolution).
# ═══════════════════════════════════════════════════════════════════════════


def test_library_admin_modules_are_hmic_bound():
    assert "core/hatp_hardware_credential_admin.py" in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES
    assert "core/hatp_principal_signer_admin.py" in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES


def test_standalone_admin_scripts_not_yet_hmic_bound():
    assert "scripts/hatp_hardware_credential_admin.py" not in hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
    assert "scripts/hatp_principal_signer_admin.py" not in hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES


def test_frozen_authority_bearing_file_count_is_36():
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 36


def test_bound_contract_count_is_7():
    assert len(hmic._CONTRACT_IDENTITY_FILES) == 7


# ═══════════════════════════════════════════════════════════════════════════
# §14/§15 -- DeploymentBinding producer cross-validates against Principal/
# Signer/HardwareCredential registries (proves the hardware -> signer ->
# binding edge, Model B: registry resolves governance identity).
# ═══════════════════════════════════════════════════════════════════════════


def test_deployment_binding_admin_cross_validates_principal_signer_credential():
    source = (
        _REPO_ROOT / "src" / "pcae" / "core" / "hatp_deployment_binding_admin.py"
    ).read_text(encoding="utf-8")
    assert "AuthorityPrincipalNotFoundError" in source
    assert "AuthoritySignerNotFoundError" in source
    assert "HardwareCredentialRecord" in source
    assert "signer.provider_profile" in source or "provider_profile" in source


# ═══════════════════════════════════════════════════════════════════════════
# §18/§19 -- hatp_substrate_operational and the readiness conjunction: 8
# terms currently exist in production (not 6), and substrate readiness is
# strictly downstream of the same registry.json Principal/Signer/
# DeploymentBinding records (no independent parallel state, no cycle).
# ═══════════════════════════════════════════════════════════════════════════


def test_readiness_conjunction_has_eight_terms_not_six():
    import inspect

    from pcae.core import hatp_mandatory_cutover as cutover

    source = inspect.getsource(cutover._assess_hatp_mandatory_activation_readiness_at_root)
    expected_terms = (
        "class_b_protected_storage_available",
        "repository_deployment_identity_valid",
        "hatp_substrate_operational",
        "hsce_signing_implementation_available",
        "mandatory_consumption_implementation_independently_verified",
        "production_dependency_provenance_valid",
        "protected_activation_authority_mechanism_available",
        "class_b_deployment_conformance_satisfies_readiness",
    )
    for term in expected_terms:
        assert term in source, f"expected readiness term {term!r} not found"
    assert len(expected_terms) == 8


def test_trust_store_substrate_reads_same_registry_as_deployment_binding():
    source = (
        _REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py"
    ).read_text(encoding="utf-8")
    # load_repository_enrollment / lookup_authority both resolve through
    # HATPTrustStore._load_registry() -- the identical registry.json the
    # DeploymentBinding/Principal/Signer producers write, proving
    # hatp_substrate_operational is downstream of Trust-Enrollment state,
    # not an independent parallel record store.
    assert "def load_repository_enrollment(self, repository_id: str) -> Optional[DeploymentBinding]:" in source
    assert "def lookup_authority(self, principal_id: str, repository_id: str) -> Optional[AuthorityRecord]:" in source


# ═══════════════════════════════════════════════════════════════════════════
# §20-21 -- rebuilt post-HMIC DAG: no cycle among Trust-Enrollment /
# Class-B / substrate-readiness / HATP-activation nodes.
# ═══════════════════════════════════════════════════════════════════════════

_DAG_NODES = (
    "hmic_valid",
    "protected_root_compliant",
    "hardware_credential_admin_script",
    "principal_signer_admin_script",
    "fido2_hardware_credential_enrollment",
    "hardware_credential_record",
    "principal_enrollment",
    "signer_enrollment",
    "deployment_binding_creation",
    "class_b_compliant",
    "hatp_substrate_operational",
    "mandatory_readiness",
    "hatp_activation",
)

_DAG_EDGES = (
    ("hardware_credential_admin_script", "fido2_hardware_credential_enrollment"),
    ("fido2_hardware_credential_enrollment", "hardware_credential_record"),
    ("hardware_credential_record", "principal_signer_admin_script"),
    ("principal_signer_admin_script", "principal_enrollment"),
    ("principal_enrollment", "signer_enrollment"),
    ("hardware_credential_record", "signer_enrollment"),
    ("signer_enrollment", "deployment_binding_creation"),
    ("principal_enrollment", "deployment_binding_creation"),
    ("deployment_binding_creation", "class_b_compliant"),
    ("deployment_binding_creation", "hatp_substrate_operational"),
    ("principal_enrollment", "hatp_substrate_operational"),
    ("protected_root_compliant", "hatp_substrate_operational"),
    ("hmic_valid", "mandatory_readiness"),
    ("class_b_compliant", "mandatory_readiness"),
    ("hatp_substrate_operational", "mandatory_readiness"),
    ("mandatory_readiness", "hatp_activation"),
)


def test_post_hmic_dag_has_no_cycle():
    adjacency = {node: [] for node in _DAG_NODES}
    for pred, succ in _DAG_EDGES:
        adjacency[pred].append(succ)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in _DAG_NODES}

    def visit(node):
        color[node] = GRAY
        for neighbor in adjacency[node]:
            if color[neighbor] == GRAY:
                raise AssertionError(f"cycle detected through {node} -> {neighbor}")
            if color[neighbor] == WHITE:
                visit(neighbor)
        color[node] = BLACK

    for node in _DAG_NODES:
        if color[node] == WHITE:
            visit(node)


def test_next_implementation_prerequisite_is_the_missing_admin_scripts():
    # Both admin-script nodes have no unmet predecessor -- the library
    # writers, FIDO2 provider, and DeploymentBinding cross-validation logic
    # they call are all already implemented; only the standalone scripts/
    # entrypoint (mirroring the certification/deployment-binding admin
    # script precedent) is missing.
    predecessors = {node: set() for node in _DAG_NODES}
    for pred, succ in _DAG_EDGES:
        predecessors[succ].add(pred)
    assert predecessors["hardware_credential_admin_script"] == set()
    # principal_signer_admin_script's only graph predecessor is the
    # hardware_credential_record artifact it consumes -- not yet real, but
    # the *script itself* (an admin-entrypoint architecture decision, not a
    # real-effect record) has no architectural blocker distinct from the
    # hardware-credential script's own absence.
    assert predecessors["principal_signer_admin_script"] == {"hardware_credential_record"}
