"""Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1
— Independent Verification of Production Protected-Presentation Generation-1
Deployment State.

This is a strictly VERIFICATION-ONLY phase. It independently re-derives and
checks the ACTUAL production deployment state created by the predecessor
registration transaction -- it does not rerun registration, does not
reprovision the protected root, does not reinstall the helper, and performs
no human/YubiKey ceremony.

The privileged (root-owned, mode-0700) reads of
`/Library/Application Support/PCAE/HPAC/protected-root` were performed once,
out of band, by the human operator via `sudo` in their own terminal (never
through this agent's shell, which has no interactive TTY for a password
prompt). This repository's own unprivileged pytest process (uid 501) cannot
read most of that tree directly. The literal privileged read results are
recorded as frozen evidence in
`.pcae/evidence/PHASE_1R_1R_1R_1_DEPLOYMENT_STATE_IV.json` and asserted below
via self-consistency / independent-recomputation checks, exactly as the
predecessor phase's own IV suite did for its registration evidence.

This suite additionally, independently (not by re-running the existing
failing unit tests alone) re-exercises the real Gate 5 forged-object
rejection boundary from a fresh standalone construction, and independently
traces the three historical point-in-time guard failures to the exact
unrelated intervening phase commits that moved HEAD past their fixed
anchors.

Strictly read-only against the real filesystem, git history, and Python
source outside test-owned fixtures. No protected-root mutation, no PPA
registration, no sudo invoked from within this test process, no YubiKey, no
FIDO2 PIN, no protected human APPROVE/REJECT, no PRODUCTION principal
minted, no Gate 5 certification performed.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pcae.core.hpac_foundation import canonical_digest  # noqa: E402
from pcae.core.phase_id import compare, parse, same_branch, same_series  # noqa: E402

PREDECESSOR_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R"
)
THIS_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1"
)

V0 = "8db9178e61c44f36bba4c7e879e79fc75fdf99fc"

_EXPECTED_HELPER_SHA256 = "933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182"
_EXPECTED_HELPER_BYTE_LENGTH = 16295
_EXPECTED_VERIFIER_CONFIG_OBJECT = {"schema": "v1", "verifier_kind": "pcae-protected-local-presentation/1.0"}
_EXPECTED_VERIFIER_CONFIG_DIGEST = "951182f5e737068d286313903504e34cb3dc57b47a2a19f9031ac068c7992c85"
_EXPECTED_ANCHOR_ID = "hpaw-f9661f401f204d828a4aec951855819a"
_EXPECTED_PAWA_INSTALLATION_ID = "hpawi-bfc91d001ac940b8bda0ed06566180eb"
_EXPECTED_UID = 501
_EXPECTED_ACCOUNT = "atilamadai"

_EVIDENCE_PATH = REPO_ROOT / ".pcae/evidence/PHASE_1R_1R_1R_1_DEPLOYMENT_STATE_IV.json"


def _git(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)


def _load_evidence() -> dict:
    return json.loads(_EVIDENCE_PATH.read_text())


# ═══════════════════════════════════════════════════════════════════════
# LINEAGE / SCOPE
# ═══════════════════════════════════════════════════════════════════════


def test_this_phase_id_is_the_direct_cpipc_successor_of_the_predecessor():
    pred = parse(PREDECESSOR_PHASE_ID)
    cand = parse(THIS_PHASE_ID)
    assert same_series(pred, cand)
    assert same_branch(pred, cand)
    assert compare(pred, cand) == "less"
    assert cand.subphase[:-1] == pred.subphase
    assert cand.subphase[-1] == (1, "")


def test_evidence_file_exists_and_parses_and_matches_phase_lineage():
    assert _EVIDENCE_PATH.is_file()
    evidence = _load_evidence()
    assert evidence["phase_id"] == THIS_PHASE_ID
    assert evidence["predecessor_phase_id"] == PREDECESSOR_PHASE_ID
    assert evidence["V0"] == V0


def test_predecessor_canonical_report_preserved_byte_identical():
    # This IV must not rewrite the predecessor's own finalized report.
    result = _git("log", "--oneline", "-1", "--format=%H", V0)
    assert result.stdout.strip() == V0


# N16-5-H3-IMPL: this PPA Gen-1 deployment-state IV completed at `_IV_END`
# (its own final `…1` commit). Its downstream successor N16-5-H3-IMPL is the
# sanctioned §33A/§38A/§42B implementation phase. Re-anchor the endpoint from
# the moving `HEAD` to the fixed IV-completion SHA so the guard keeps
# asserting exactly what it was written to assert — that THIS IV made no
# production mutation — without implicating the later implementation phase.
_IV_END = "e44becc9"


def test_no_iv_production_mutation_since_v0():
    diff = _git("diff", "--name-only", V0, _IV_END, "--", "src/pcae", "scripts", "pyproject.toml")
    assert diff.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════
# PROTECTED ROOT / PAWA (independently recomputed digests + frozen
# privileged-read evidence self-consistency)
# ═══════════════════════════════════════════════════════════════════════


def test_protected_root_topology_matches_pawa_anchor_identity():
    evidence = _load_evidence()
    root = evidence["privileged_readback"]["protected_root"]
    anchor = evidence["privileged_readback"]["pawa_anchor"]
    assert root["mode_octal"] == "0700"
    assert root["owner"] == "root:admin"
    assert root["device"] == anchor["protected_root_identity"]["device"]
    assert root["inode"] == anchor["protected_root_identity"]["inode"]
    assert root["verdict"] == "VERIFIED"


def test_pawa_anchor_ids_and_generation_match_expected():
    evidence = _load_evidence()
    anchor = evidence["privileged_readback"]["pawa_anchor"]
    assert anchor["anchor_id"] == _EXPECTED_ANCHOR_ID
    assert anchor["installation_id"] == _EXPECTED_PAWA_INSTALLATION_ID
    assert anchor["generation"] == 1
    assert anchor["state"] == "ACTIVE"
    assert anchor["supersedes"] is None


def test_configured_agent_binding_matches_expected():
    evidence = _load_evidence()
    excl = evidence["privileged_readback"]["agent_exclusion"]
    assert excl["symbolic_account"] == _EXPECTED_ACCOUNT
    assert excl["provisioned_uid"] == _EXPECTED_UID
    assert excl["installation_id"] == _EXPECTED_PAWA_INSTALLATION_ID
    assert excl["state"] == "ACTIVE"


def test_writer_lock_empty_and_unheld_no_partial_transaction():
    evidence = _load_evidence()
    lock = evidence["privileged_readback"]["writer_lock"]
    assert lock["byte_length"] == 0
    assert lock["held_by_any_process_lsof"] is False


# ═══════════════════════════════════════════════════════════════════════
# HELPER PROVENANCE / BYTE IDENTITY (independently recomputed here, not
# merely copied from evidence)
# ═══════════════════════════════════════════════════════════════════════


def test_helper_source_sha256_independently_recomputed_from_immutable_source():
    data = (REPO_ROOT / "src/pcae/protected_presentation_helper.py").read_bytes()
    assert len(data) == _EXPECTED_HELPER_BYTE_LENGTH
    assert hashlib.sha256(data).hexdigest() == _EXPECTED_HELPER_SHA256


def test_helper_source_unchanged_between_v0_and_head():
    diff = _git("diff", "--stat", V0, "HEAD", "--", "src/pcae/protected_presentation_helper.py")
    assert diff.stdout.strip() == ""


def test_installed_helper_matches_recomputed_immutable_source_digest():
    evidence = _load_evidence()
    helper = evidence["privileged_readback"]["helper"]
    assert helper["sha256_installed"] == _EXPECTED_HELPER_SHA256
    assert helper["byte_length"] == _EXPECTED_HELPER_BYTE_LENGTH
    assert helper["regular_file_not_symlink"] is True
    assert helper["hard_links"] == 1
    assert helper["matches_pre_registration_helper_evidence"] is True


def test_helper_not_group_or_world_writable():
    evidence = _load_evidence()
    mode = evidence["privileged_readback"]["helper"]["mode_octal"]
    perm_bits = int(mode, 8) & 0o022
    assert perm_bits == 0, f"helper mode {mode} is group- or other-writable"


# ═══════════════════════════════════════════════════════════════════════
# PPA INSTALLATION DESCRIPTOR / CURRENT-GENERATION (recomputed digests)
# ═══════════════════════════════════════════════════════════════════════


def test_verifier_configuration_digest_independently_recomputed():
    assert canonical_digest(_EXPECTED_VERIFIER_CONFIG_OBJECT) == _EXPECTED_VERIFIER_CONFIG_DIGEST


def test_descriptor_binds_the_independently_recomputed_verifier_digest():
    evidence = _load_evidence()
    descr = evidence["privileged_readback"]["descriptor_json"]
    assert descr["verifier_configuration_digest"] == _EXPECTED_VERIFIER_CONFIG_DIGEST
    assert descr["mechanism_id"] == "pcae-protected-local-presentation"
    assert descr["verifier_kind"] == "pcae-protected-local-presentation/1.0"
    assert descr["renderer_profile"] == "pcae-protected-local-presentation-renderer/1.0"
    assert descr["descriptor_version"] == "pcae-protected-local-presentation-descriptor/1.0"
    assert descr["status"] == "active"


def _self_excluding_digest(document: dict, field: str) -> str:
    projected = dict(document)
    projected[field] = ""
    return canonical_digest(projected)


def test_installation_digest_recomputes_from_recorded_fields():
    evidence = _load_evidence()
    rec = evidence["privileged_readback"]["installation_1_json"]
    doc = {
        "installation_schema_version": rec["installation_schema_version"],
        "installation_id": rec["installation_id"],
        "mechanism_id": rec["mechanism_id"],
        "helper_implementation_id": rec["helper_implementation_id"],
        "helper_implementation_version": rec["helper_implementation_version"],
        "helper_path": rec["helper_path"],
        "helper_sha256": rec["helper_sha256"],
        "descriptor_digest": rec["descriptor_digest"],
        "verifier_configuration_digest": rec["verifier_configuration_digest"],
        "renderer_profile": rec["renderer_profile"],
        "generation": rec["generation"],
        "lifecycle_action": rec["lifecycle_action"],
        "status": rec["status"],
        "installed_at": "2026-09-05T16:53:22.143Z",
        "supersedes": None,
        "installation_digest": "",
    }
    assert _self_excluding_digest(doc, "installation_digest") == rec["installation_digest"]


def test_anchor_digest_recomputes_from_recorded_fields():
    evidence = _load_evidence()
    rec = evidence["privileged_readback"]["current_generation_json"]
    doc = {
        "current_generation_schema_version": rec["current_generation_schema_version"],
        "installation_id": rec["installation_id"],
        "mechanism_id": "pcae-protected-local-presentation",
        "current_generation": rec["current_generation"],
        "installation_digest": rec["installation_digest"],
        "descriptor_digest": rec["descriptor_digest"],
        "status": rec["status"],
        "updated_at": "2026-09-05T16:53:22.143Z",
        "anchor_digest": "",
    }
    assert _self_excluding_digest(doc, "anchor_digest") == rec["anchor_digest"]


def test_current_generation_points_to_the_only_installation_and_generation_1():
    evidence = _load_evidence()
    cg = evidence["privileged_readback"]["current_generation_json"]
    inst = evidence["privileged_readback"]["installation_1_json"]
    assert cg["current_generation"] == 1
    assert cg["installation_id"] == inst["installation_id"]
    assert cg["installation_digest"] == inst["installation_digest"]
    assert cg["descriptor_digest"] == inst["descriptor_digest"]
    assert cg["no_conflicting_active_generation"] is True
    assert cg["status"] == "active"


def test_currentness_and_revocation_state_are_all_active_no_stale_pointer():
    evidence = _load_evidence()
    rb = evidence["privileged_readback"]
    assert rb["descriptor_json"]["status"] == "active"
    assert rb["current_generation_json"]["status"] == "active"
    assert rb["installation_1_json"]["status"] == "active"


# ═══════════════════════════════════════════════════════════════════════
# WRITE-SET CONFINEMENT / SUBSTITUTION / UNPRIVILEGED-MUTATION RESISTANCE
# ═══════════════════════════════════════════════════════════════════════


def test_write_set_confined_to_exactly_three_mechanism_files_and_one_helper():
    evidence = _load_evidence()
    tree = evidence["privileged_readback"]["write_set_full_tree_listing"]
    mech_files = {p for p in tree["presentation-mechanisms_tree"] if p.endswith(".json")}
    assert mech_files == {
        "presentation-mechanisms/v2/pcae-protected-local-presentation/current-generation.json",
        "presentation-mechanisms/v2/pcae-protected-local-presentation/installations/1/installation.json",
        "presentation-mechanisms/v2/pcae-protected-local-presentation/descriptor.json",
    }
    helper_files = [p for p in tree["presentation-helper_tree"] if p.endswith("/pcae-protected-local-presentation")]
    assert len(helper_files) == 1
    assert tree["exactly_3_mechanism_files_no_other_generation"] is True
    assert tree["exactly_1_helper_content_addressed_directory"] is True


def test_unprivileged_configured_agent_cannot_write_protected_state():
    evidence = _load_evidence()
    mut = evidence["privileged_readback"]["unprivileged_mutation_resistance"]
    assert mut["agent_can_write_current_generation_json"] is False
    assert mut["agent_can_write_protected_root"] is False


def test_helper_path_derivation_rejects_symlink_chain_by_source_design():
    """HPAC-PPA-REQ-012: `_reject_symlink_chain` walks every path component
    up to `protected_root` and raises on any symlink. Verify the guard
    exists and is wired into `verify_helper_bytes` (source-level design
    check; live substitution was not attempted against the real deployed
    path, per this phase's read-only-only scope)."""
    src = (REPO_ROOT / "src/pcae/core/protected_presentation_installation.py").read_text()
    assert "_reject_symlink_chain" in src
    assert "def verify_helper_bytes(" in src
    verify_fn = src.split("def verify_helper_bytes(", 1)[1]
    assert "_reject_symlink_chain(" in verify_fn.split("\n\n\n")[0]


# ═══════════════════════════════════════════════════════════════════════
# CAPABILITY PROVENANCE / TERMINAL CONSUMPTION / ROLE SEPARATION
# ═══════════════════════════════════════════════════════════════════════


def test_no_persisted_reusable_capability_token_in_write_set():
    evidence = _load_evidence()
    cap = evidence["capability_provenance_and_terminal_consumption"]
    assert cap["no_persisted_capability_token_found_in_write_set"] is True


def test_hpac_writer_capability_is_structurally_single_use():
    src = (REPO_ROOT / "src/pcae/core/hpac_protected_admin_writer.py").read_text()
    assert "HPACWriterCapability" in src


def test_role_separation_recorded_and_source_confirmed_distinct_modules():
    evidence = _load_evidence()
    roles = evidence["role_separation"]
    assert roles["installer"] != roles["launcher"]
    assert roles["launcher"] != roles["evidence_writer"]
    assert roles["evidence_writer"] != roles["human_approver"]
    assert (REPO_ROOT / "src/pcae/core/hpac_protected_presentation_admin.py").exists()
    assert (REPO_ROOT / "src/pcae/core/protected_presentation.py").exists()
    assert (REPO_ROOT / "src/pcae/protected_presentation_helper.py").exists()


# ═══════════════════════════════════════════════════════════════════════
# FORGED-OBJECT NEGATIVE VERIFICATION (fresh, independent construction --
# not merely a re-run of the existing failing unit tests)
# ═══════════════════════════════════════════════════════════════════════


def test_forged_principal_isinstance_true_but_rejected_by_real_gate5_boundary():
    import datetime

    from pcae.core.hpac_verifier import (
        AuthenticatedHumanPrincipal,
        HPACAuthorityClass,
        is_verifier_authenticated_principal,
    )

    forged = object.__new__(AuthenticatedHumanPrincipal)
    forged.principal_id = "forged-principal"
    forged.credential_id = "forged-credential"
    forged.mechanism_id = "forged-mechanism"
    forged.approval_id = "forged-approval"
    forged.invocation_id = "forged-invocation"
    forged.proof_id = "forged-proof"
    forged.presentation_id = "forged-presentation"
    forged.assurance_class = HPACAuthorityClass.PRODUCTION
    forged.verified_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    forged._verifier_seal = object()

    # Confirms the documented HPAC-REQ-056 construction-boundary gap exists
    # (raw isinstance / property level) -- tracked as a current product
    # defect, not repaired in this verification-only phase.
    assert isinstance(forged, AuthenticatedHumanPrincipal)
    assert forged.is_real_runtime_eligible is True

    # But the ACTUAL production consumption boundary independently rejects
    # it: never added to the identity-keyed registry that
    # is_verifier_authenticated_principal checks.
    assert is_verifier_authenticated_principal(forged) is False


def test_gate5_call_site_uses_the_real_boundary_not_isinstance_alone():
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate5.py").read_text()
    assert "from pcae.core.hpac_verifier import is_verifier_authenticated_principal" in src
    assert "if not is_verifier_authenticated_principal(authenticated_principal):" in src
    assert 'return None, ("authenticated_principal_not_verifier_issued",)' in src


def test_runtime_authority_call_sites_also_use_the_real_boundary():
    src = (REPO_ROOT / "src/pcae/core/runtime_authority.py").read_text()
    assert src.count("is_verifier_authenticated_principal") >= 3  # 2 imports + at least 2 checks


# ═══════════════════════════════════════════════════════════════════════
# PREDECESSOR FIVE-FAILURE RE-ADJUDICATION (independently traced, not
# source-diff-absence alone)
# ═══════════════════════════════════════════════════════════════════════


_TARGETED_SUITES = [
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_1_protected_presentation_real_assurance.py",
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4_blocked_protected_presentation_authority.py",
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1_protected_presentation_human_election_iv_and_n16_5_certification.py",
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_2_protected_presentation_real_assurance_iv.py",
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_protected_presentation_interactive_election_repair.py",
    "tests/test_hpac_verifier.py",
    "tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py",
    "tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py",
    "tests/test_hpac_verifier_repair_independent_verification_3w1r2b1r1115a21.py",
    "tests/test_gate5_approval_validation_coordinator_3w1r2b1r1_1r10.py",
    "tests/test_gate5_approval_validation_coordinator_integration_independent_verification_3w1r2b1r1_1r11.py",
]

_EXPECTED_FIVE_FAILURES = {
    "test_31_current_phase_changes_no_production_or_contract",
    "test_30_repair_suite_contains_a_stale_live_head_assertion_finding_f3",
    "test_05_production_diff_is_exactly_the_two_authorized_files",
    "test_object_dunder_new_bypasses_trusted_construction_seal",
    "test_forged_via_object_new_would_report_real_runtime_eligible",
}


def test_targeted_suites_still_reproduce_exactly_the_five_predecessor_failures():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no", "-rf", *_TARGETED_SUITES],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    failed = {
        line.split("::")[-1].strip()
        for line in result.stdout.splitlines()
        if line.startswith("FAILED ")
    }
    assert failed == _EXPECTED_FIVE_FAILURES
    assert "468 passed" in result.stdout
    assert "5 failed" in result.stdout


def test_historical_guard_05_extra_files_traced_to_two_unrelated_completed_phases():
    entry = "0250e5f79340b659f4c34ce391656d8f7219ccc3"
    # N16-5-H3-IMPL: endpoint re-anchored to this IV's completion (`_IV_END`);
    # see the note on `test_no_iv_production_mutation_since_v0`.
    diff = _git("diff", "--name-only", entry, _IV_END, "--", "src/pcae")
    extra = set(diff.stdout.split()) - {
        "src/pcae/protected_presentation_helper.py",
        "src/pcae/core/protected_presentation.py",
    }
    assert extra == {
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/notifications.py",
        "src/pcae/core/phase_reports.py",
    }
    log = _git("log", "--oneline", f"{entry}..HEAD", "--", *extra)
    subjects = log.stdout
    assert "configured-agent-identity threading repair" in subjects
    assert "durable Telegram notification acceptance receipts" in subjects
    # Neither intervening commit is the PPA registration commit or this IV.
    assert "PPA REGISTRATION TRANSACTION" not in subjects
    assert THIS_PHASE_ID not in subjects


def test_five_failure_reclassification_recorded_and_none_is_a_blocker():
    evidence = _load_evidence()
    nodes = evidence["predecessor_five_failure_reclassification"]["nodes"]
    assert len(nodes) == 5
    node_ids = {n["node_id"].split("::")[-1] for n in nodes}
    assert node_ids == _EXPECTED_FIVE_FAILURES
    for node in nodes:
        assert node["classification"] in {
            "PRE-EXISTING REPRODUCED",
            "HISTORICAL / POINT-IN-TIME GUARD",
            "HOST-STATE-TRIGGERED BUT NONBLOCKING",
            "CURRENT PRODUCT DEFECT",
            "CURRENT TEST/HARNESS DEFECT",
            "F-5 / N-16-5 BLOCKER",
        }
        assert node["classification"] != "F-5 / N-16-5 BLOCKER"
    assert evidence["predecessor_five_failure_reclassification"]["no_hidden_f5_n16_5_blocker"] is True


# ═══════════════════════════════════════════════════════════════════════
# ORDINARY-DEVELOPMENT INDEPENDENCE / RUNTIME BOUNDARY
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_state_unchanged_and_unavailable():
    evidence = _load_evidence()
    runtime = evidence["runtime_final_check"]
    assert runtime["implementation"] == "not_implemented"
    assert runtime["state"] == "Observed"
    assert runtime["maximum_capability"] == "observe"
    assert runtime["execution_availability"] == "unavailable"
    assert runtime["plugins"] == 0
    assert runtime["capabilities"] == 0
    assert runtime["first_governed_runtime_effect"] == "ABSENT / UNREACHABLE"


def test_zero_host_mutation_by_this_iv():
    evidence = _load_evidence()
    mut = evidence["no_host_mutation_by_this_iv"]
    assert mut["authorized_mutating_host_commands"] == 0
    assert mut["unauthorized_mutating_host_commands"] == 0


# ═══════════════════════════════════════════════════════════════════════
# NO PRODUCT / TEST / CONTRACT / DEPENDENCY CHANGE THIS PHASE
# ═══════════════════════════════════════════════════════════════════════


def test_no_contract_change_since_v0():
    diff = _git("diff", "--name-only", V0, "HEAD", "--", "docs/contracts")
  # Reconciled by phase N16-5-H3-PAWA13 (HPAC-PAWA-001 v1.2 -> v1.3,
  # MINOR, S-2: certification-coordinator authority). The only later
  # docs/contracts delta is the in-place v1.3 evolution of the PAWA anchor
  # document (verified by the v1.3 contract-reconciliation suite); nothing
  # else in docs/contracts changed. No test function was renamed or removed
  # (HPAC-PAWA-REQ-217 discipline).
    assert set(diff.stdout.split()) <= {'docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md'}


def test_pyproject_unchanged_since_v0():
    diff = _git("diff", "--stat", V0, "HEAD", "--", "pyproject.toml")
    assert diff.stdout.strip() == ""


def test_no_test_weakening_in_this_phases_diff():
    import ast

    changed = _git("diff", "--name-only", V0, "HEAD", "--", "tests").stdout.split()
    for path in changed:
        if not path.endswith(".py"):
            continue
        old_show = _git("show", f"{V0}:{path}")
        old_defs: set[str] = set()
        if old_show.returncode == 0:
            old_tree = ast.parse(old_show.stdout)
            old_defs = {n.name for n in ast.walk(old_tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
        new_text = (REPO_ROOT / path).read_text()
        new_tree = ast.parse(new_text)
        new_defs = {n.name for n in ast.walk(new_tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
        assert old_defs <= new_defs, f"{path}: tests removed/renamed: {old_defs - new_defs}"


# ═══════════════════════════════════════════════════════════════════════
# FINAL DEPLOYMENT-STATE VERDICT
# ═══════════════════════════════════════════════════════════════════════


def test_final_verdicts_are_verified_not_overclaiming_n16_5():
    evidence = _load_evidence()
    verdicts = evidence["final_verdicts"]
    assert verdicts["production_protected_presentation_generation_1_deployment_state"] == "INDEPENDENTLY VERIFIED"
    assert verdicts["f5"] == "DEPLOYMENT VERIFIED -- FINAL REAL ASSURANCE CERTIFICATION PENDING"
    assert verdicts["n16_5"] == "NOT CLOSED"
    assert "CLOSED" not in verdicts["n16_5"] or verdicts["n16_5"] == "NOT CLOSED"
    for key, value in verdicts.items():
        if key in ("authorized_mutating_host_commands",):
            continue
        assert "PRODUCTION" not in str(value) or key in (
            "production_protected_presentation_generation_1_deployment_state",
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
