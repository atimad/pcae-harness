"""Contract-level verification for phase .30R.4R.

This suite is intentionally static/read-only: the phase freezes authority and
schema semantics but implements no protected-presentation production path.
"""

from __future__ import annotations

import hashlib
import ast
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
A = "db5f1dd761174d6ac1ca16e49e8871c02f747fdf"
#: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1 reconciliation anchor — the
#: finalized `.30R.4R` head. The implementation successor `.30R.4R.1` adds
#: production source under an EXACT enumerated file set and changes NO
#: normative contract; the point-in-time "no implementation exists yet"
#: guards below are widened, not weakened, to that fixed head.
R4R_FINALIZED = "a727dbf4f160f904836905d3cb4adeba91953676"
_R4R1_IMPLEMENTATION_FILES = frozenset(
    {
        "src/pcae/core/protected_presentation_installation.py",
        "src/pcae/core/hpac_protected_presentation_admin.py",
        "src/pcae/core/protected_presentation.py",
        "src/pcae/protected_presentation_helper.py",
        "src/pcae/core/hpac_protected_admin_writer.py",
        "src/pcae/core/approval_presentation.py",
        "src/pcae/core/hpac_verifier.py",
        "scripts/hpac_protected_presentation_admin.py",
    }
)
PAWA = ROOT / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
PPA = ROOT / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
RHAMP = ROOT / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
BLOCKED = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_4_N_16_5_PROTECTED_PRESENTATION_REAL_ASSURANCE_BLOCKED.md"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def at_a(path: Path) -> bytes:
    rel = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "show", f"{A}:{rel}"], cwd=ROOT)


def test_01_phase_entry_is_finalized_blocked_head() -> None:
    assert subprocess.check_output(["git", "show", "-s", "--format=%H", A], cwd=ROOT).decode().strip() == A


def test_02_historical_30r4_blocked_artifact_preserved() -> None:
    assert hashlib.sha256(BLOCKED.read_bytes()).hexdigest() == "757268a2481f8077f1c7ed7334c763383f03e7b0813222f025bee54a9ab28715"
    assert "BLOCKED — frozen production helper-installation authority is absent" in text(BLOCKED)


def test_03_rhamp_installation_requirements_reconstructed() -> None:
    c = text(RHAMP)
    for req in ("RHAMP-REQ-015", "RHAMP-REQ-016", "RHAMP-REQ-082", "RHAMP-REQ-087", "RHAMP-REQ-088"):
        assert req in c
    assert "administrator-installed" in c and "pinned executable digest" in c


def test_04_pawa_v11_closed_world_reconstructed_and_evolved_explicitly() -> None:
    c = text(PAWA)
    assert "HPAC-PAWA-REQ-090" in c and "HPAC-PAWA-REQ-095" in c
    assert "HPAC-PAWA-001 v1.2" in c
    assert "configure_presentation_mechanism" in c


def test_05_blocker_is_independently_stated() -> None:
    c = text(PPA)
    assert "previously absent installation/currentness and\nwriter-issuance specialization" in c
    assert "Historical HPAC-PAWA-001 v1.1" in c


def test_06_installation_authority_is_existing_pawa_deployment_owner() -> None:
    c = text(PPA)
    assert "HPAC-PAWA-001 v1.2 authorizes only one bounded metadata" in c
    assert "presentation_mechanism_installer" in c


def test_07_installer_and_evidence_writer_are_distinct() -> None:
    c = text(PPA)
    assert "Installation administrator authority and runtime\n  presentation-evidence authority are distinct" in c
    assert "Installer, launcher, helper response, and evidence writer are\n  distinct trust actions" in c


def test_08_executable_install_model_is_out_of_band_plus_pin() -> None:
    c = text(PPA)
    assert "out-of-band immutable helper bytes plus PAWA metadata registration" in c
    assert "PAWA does not copy, replace, chmod, chown, package,\n  download, or execute bytes" in c


def test_09_no_generic_executable_authority() -> None:
    c = text(PAWA) + text(PPA)
    assert "SHALL NOT create, copy, replace, chmod, chown, or execute helper bytes" in c
    assert "not executable-install\n  authority" in c


def test_10_exact_admin_consumer_and_entrypoint() -> None:
    c = text(PPA)
    assert "`pcae.core.hpac_protected_presentation_admin`" in c
    assert "`scripts/hpac_protected_presentation_admin.py`" in c
    assert "only production PAWA consumer" in c


def test_11_helper_path_is_fixed_content_addressed_and_not_path_lookup() -> None:
    c = text(PPA)
    assert "presentation-helper/installations/<helper_sha256>/pcae-protected-local-presentation" in c
    assert "No repository, cwd, environment, caller, PATH lookup" in c


def test_12_helper_digest_is_sha256_of_complete_bytes() -> None:
    c = text(PPA)
    assert "equals SHA-256 of the complete executable byte stream" in c
    assert "hashes the opened bytes" in c


def test_13_helper_owner_mode_symlink_and_link_predicates_are_frozen() -> None:
    c = text(PPA)
    assert "non-symlink" in c and "regular file\n  with one hard link" in c
    assert "not writable by group,\n  other, the configured agent principal" in c


def test_14_installation_schema_is_closed_and_versioned() -> None:
    c = text(PPA)
    assert "HPAC-PRESENTATION-INSTALLATION/1.0" in c
    fields = re.findall(r"^\| `([^`]+)` \|", c, flags=re.MULTILINE)
    assert fields[:16] == [
        "installation_schema_version", "installation_id", "mechanism_id",
        "helper_implementation_id", "helper_implementation_version", "helper_path",
        "helper_sha256", "descriptor_digest", "verifier_configuration_digest",
        "renderer_profile", "generation", "lifecycle_action", "status",
        "installed_at", "supersedes", "installation_digest",
    ]


def test_15_current_generation_schema_is_closed() -> None:
    c = text(PPA)
    assert "HPAC-PRESENTATION-CURRENT-GENERATION/1.0" in c
    assert "`current_generation_schema_version` (const), `installation_id`," in c
    assert "`anchor_digest` (self-excluding SHA-256)" in c


def test_16_rotation_is_monotonic_and_old_generation_stale() -> None:
    c = text(PPA)
    assert "Rotation requires a current active generation G" in c
    assert "creates G+1" in c and "G becomes stale by derivation" in c


def test_17_revocation_has_no_fallback() -> None:
    c = text(PPA)
    assert "creates\n  G+1 with `lifecycle_action == revoke`" in c
    assert "Revocation has no automatic fallback" in c


def test_18_rollback_claim_is_bounded_to_existing_tcb() -> None:
    c = text(PPA)
    assert "Restoring an older generation record, descriptor, or\n  helper alone fails" in c
    assert "does not claim\n  resistance to a deployment owner restoring the entire trusted machine state" in c


def test_19_bootstrap_is_non_circular() -> None:
    c = text(PPA)
    assert "Bootstrap is non-circular" in c
    assert "No protected presentation is required" in c


def test_20_installation_reuses_verified_multi_write_lifecycle() -> None:
    c = text(PAWA)
    assert "independently verified\n  `complete_multi_write` ACTIVE→CONSUMED lifecycle" in c
    assert "creates no new lifecycle primitive" in c


def test_21_evidence_writer_role_is_exact_and_outside_pawa() -> None:
    c = text(PPA)
    assert "runtime evidence writer role is exactly the\n  existing `protected_presentation_mechanism`" in c
    assert "It is not a PAWA writer role" in c


def test_22_evidence_writer_is_process_local_non_bearer_and_single_use() -> None:
    c = text(PPA)
    for phrase in ("process-local", "non-serializable", "non-copyable", "restart-dead", "single-use"):
        assert phrase in c


def test_23_evidence_writer_is_exact_request_and_generation_bound() -> None:
    c = text(PPA)
    flat = " ".join(c.split())
    assert "role, mechanism id, approval id, challenge id, request digest" in flat
    assert "installation id/generation/digest, descriptor digest" in flat
    assert "authority class `PRODUCTION`, and ACTIVE lifecycle" in c


def test_24_response_authenticity_uses_verified_child_channel_not_new_crypto() -> None:
    c = text(PPA)
    assert "private one-shot parent/child channel" in c
    assert "No new signing key is required or\n  implied" in c


def test_25_evidence_storage_is_durable_but_not_bearer_authority() -> None:
    c = text(PPA)
    assert "Evidence is durable canonical input and audit material,\n  not bearer authority" in c


def test_26_launcher_installer_writer_separation_is_explicit() -> None:
    c = text(PPA)
    assert "The protected presentation launcher is distinct from\n  both authorities" in c
    assert "Launch permission is not PAWA installation authority\n  and not runtime dispatch authority" in c


def test_27_n16_6_is_distinct_with_no_authority_transfer() -> None:
    c = text(PPA)
    assert "Fixed protected-helper launch is distinct from N-16-6" in c
    assert "may be interpreted as adapter supply-chain admission" in c


def test_28_pawa_is_minor_and_no_major_trigger_fires() -> None:
    c = text(PAWA)
    assert "v1.2 is a **MINOR**" in c
    assert "No §152 MAJOR trigger fires" in c


def test_29_pawa_failure_vocabulary_remains_21_codes() -> None:
    c = text(PAWA)
    assert "existing 21-code `pawa_failure_code` vocabulary is\n  sufficient and unchanged" in c


def test_30_hpac_rhamp_and_writer_provenance_do_not_evolve() -> None:
    c = text(PPA)
    assert "HPAC-001 remains v2.1 byte-identical" in c
    assert "RHAMP-001 remains v1.0 byte-identical" in c
    assert "Existing `HPAC-WRITER-PROVENANCE/1.0` is sufficient" in c


def test_31_all_preexisting_contracts_except_pawa_are_byte_identical_to_a() -> None:
    for path in sorted((ROOT / "docs/contracts").glob("*.md")):
        if path in {PAWA, PPA}:
            continue
        assert path.read_bytes() == at_a(path), path


def test_32_pawa_and_new_companion_are_only_contract_delta() -> None:
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", A, "--", "docs/contracts"], cwd=ROOT, text=True
        ).splitlines()
    )
    # `.30R.4R` delta: the PAWA MINOR + the new companion PPA (PPA was
    # untracked at `A` and is listed once it is committed). No other contract.
    assert changed <= {
        "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
        "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md",
    }
    assert PPA.exists()
    # Phase .1R.30R.4R.1 reconciliation — the implementation successor changes
    # NO normative contract byte.
    assert (
        subprocess.check_output(
            ["git", "diff", "--name-only", R4R_FINALIZED, "--", "docs/contracts"], cwd=ROOT, text=True
        ).strip()
        == ""
    )


def test_33_requirement_numbering_is_closed_and_sequential() -> None:
    pawa_nums = [int(v) for v in re.findall(r"\*\*HPAC-PAWA-REQ-(\d{3})(?:\.|\*\*)", text(PAWA))]
    ppa_nums = [int(v) for v in re.findall(r"\*\*HPAC-PPA-REQ-(\d{3})(?:\.|\*\*)", text(PPA))]
    assert sorted(pawa_nums) == list(range(1, 234))
    assert sorted(ppa_nums) == list(range(1, 77))


def test_34_exact_future_module_inventory_has_no_wildcard() -> None:
    c = text(PPA)
    for module in (
        "pcae.core.protected_presentation_installation",
        "pcae.core.hpac_protected_presentation_admin",
        "pcae.core.protected_presentation",
        "pcae.protected_presentation_helper",
    ):
        assert module in c
    assert "No\n  wildcard, prefix, glob, `fnmatch`" in c


def test_35_no_production_or_script_implementation_changed() -> None:
    # Phase .1R.30R.4R.1 reconciliation — `.30R.4R` (the contract-freeze
    # phase) changed no production source; its implementation successor
    # `.30R.4R.1` adds/changes production source under an EXACT enumerated
    # file set and nothing else (still no wildcard).
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", R4R_FINALIZED, "HEAD", "--", "src/pcae", "scripts"],
            cwd=ROOT, text=True,
        ).split()
        + subprocess.check_output(
            ["git", "diff", "--name-only", R4R_FINALIZED, "--", "src/pcae", "scripts"], cwd=ROOT, text=True
        ).split()
    )
    assert changed <= _R4R1_IMPLEMENTATION_FILES, sorted(changed - _R4R1_IMPLEMENTATION_FILES)


def test_36_no_gate_wiring_or_protected_implementation_exists_yet() -> None:
    c = text(PPA)
    assert "This contract implements no helper, launcher, writer,\n  descriptor, verifier, Gate wiring" in c
    # Phase .1R.30R.4R.1 reconciliation — the launcher/mediator now exists.
    # Not weakened: it exists, adds no first external effect, and carries the
    # frozen real verifier kind.
    launcher = ROOT / "src/pcae/core/protected_presentation.py"
    assert launcher.exists()
    src = launcher.read_text()
    tree = ast.parse(src)
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "dispatch" not in calls
    names = {n.id for node in ast.walk(tree) if isinstance(node, ast.Name) for n in [node]}
    assert "DispatchEnvelope" not in names
    assert "pcae-protected-local-presentation/1.0" in src
    # No Gate-5 / Gate-9 source was wired (real assurance is consumed via the
    # existing frozen assurance-class check — see the .30R.4R.1 phase doc).
    for gate in ("runtime_dispatch_gate5.py", "runtime_dispatch_gate9.py"):
        assert (
            subprocess.run(
                ["git", "diff", "--quiet", R4R_FINALIZED, "HEAD", "--", f"src/pcae/core/{gate}"], cwd=ROOT
            ).returncode
            == 0
        )


def test_37_deterministic_fixture_cannot_promote() -> None:
    c = text(PPA)
    assert "Deterministic NON_REAL descriptors, helpers, writers,\n  evidence, fixtures" in c
    assert "permanently\n  unable to produce `PRODUCTION` authority" in c


def test_38_runtime_and_first_effect_remain_absent() -> None:
    c = text(PPA)
    assert "Runtime remains Observed / observe /\n  unavailable with zero plugins/capabilities" in c
    assert "First external effect remains **ABSENT**" in c
    effect_calls: list[str] = []
    for path in (ROOT / "src/pcae").rglob("*.py"):
        tree = ast.parse(path.read_text(errors="ignore"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "dispatch"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "adapter"
            ):
                effect_calls.append(str(path.relative_to(ROOT)))
    assert effect_calls == []


def test_39_n16_5_not_closed_and_n16_6_7_untouched() -> None:
    c = text(PPA)
    assert "N-16-5 remains **NOT CLOSED**" in c
    assert "N-16-6, N-16-7, Slice C" in c


def test_40_successor_is_exact_fresh_cpipc_valid_shape() -> None:
    c = text(PPA)
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1" in c
    assert "Historical `.30R.4` remains BLOCKED and immutable" in c


def test_41_hpac_existing_descriptor_and_evidence_roles_are_reused() -> None:
    c = text(HPAC)
    assert "TrustedApprovalPresentationMechanism" in c
    assert "HPAC-PRESENTATION-EVIDENCE/2.0" in c
    prod = text(ROOT / "src/pcae/core/approval_presentation.py")
    assert '_WRITER_ROLE = "presentation_mechanism_installer"' in prod
    assert '_WRITER_ROLE = "protected_presentation_mechanism"' in prod


def test_42_contract_phase_does_not_claim_implementation() -> None:
    c = text(PPA)
    assert "IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING" in c
    assert "Protected presentation and Gate real-assurance consumption remain **NOT\nIMPLEMENTED**" in c
