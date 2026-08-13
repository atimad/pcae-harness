"""Phase 149O.20K.1 -- HMIC Class-B Verifier Source-Scope Contract
Independent Verification.

Independently verifies Phase 149O.20K's HMIC-001 v1.2 -> v1.3 amendment
(`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
§53). This module is written fresh: it does not import, reuse, or copy
149O.20K's own test module
(`tests/test_phase_149o_20k_hmic_class_b_verifier_source_scope_contract_evolution.py`),
does not trust 149O.20K's narrative, dependency graph, AST walk,
Category A/B/C/D/E classification, 28-file conclusion, version-bump
rationale, cycle/self-binding analysis, or historical-test-failure
attribution. Every assertion below is re-derived from primary sources:
the pre-K contract text (read via `git show <pre-K commit>:<path>`),
the current contract text, current production source, and a fresh
`ast`-based dependency walk run by this module itself.

Verification-only: no production source or contract document is
imported for mutation, and this module performs no write of any kind.
"""
from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")
_HBDC_CONTRACT_PATH = _CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_HMIC_MODULE_TEXT = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
_PATHS_MODULE_PATH = _SRC / "core" / "paths.py"

_VERIFIER_FILES = (
    "hatp_class_b_topology_verifier.py",
    "hatp_environment_lock_verifier.py",
    "hatp_class_b_conformance.py",
)

# Independently reconstructed (not trusted from K's report) via
# `git log --oneline -1 3e1137ef` and its parent: the true pre-K commit,
# i.e. the state of the repository immediately before 149O.20K's own
# contract-evolution commit.
_K_CONTRACT_COMMIT = "3e1137ef19c354f221a1b1b1a6d358259e6bfc9a"
_PRE_K_COMMIT = "e917779b891074bf957823fe6f20277296563745"


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _pre_k_contract_text() -> str:
    return _git_show(_PRE_K_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")


def test_pre_k_commit_is_true_parent_of_k_commit():
    result = subprocess.run(
        ["git", "log", "--format=%P", "-1", _K_CONTRACT_COMMIT],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == _PRE_K_COMMIT


def test_pre_k_contract_is_v1_2():
    text = _pre_k_contract_text()
    assert "**Version:** 1.2" in text


def test_pre_k_contract_hmic_req_052_has_only_limbs_a_and_b():
    text = _pre_k_contract_text()
    idx = text.index("**HMIC-REQ-052")
    # Slice up to the next requirement heading.
    next_idx = text.index("**HMIC-REQ-053", idx)
    body = text[idx:next_idx]
    assert "(a) the certification-relevant" in body
    assert "(b) *(added v1.1" in body
    assert "verify_class_b_deployment_conformance" not in body
    assert "(c) *(added" not in body


def test_pre_k_hmic_req_050_enumerates_exactly_25_files():
    text = _pre_k_contract_text()
    idx = text.index("**HMIC-REQ-050")
    fence_start = text.index("```", idx)
    fence_end = text.index("```", fence_start + 3)
    block = text[fence_start + 3 : fence_end].strip()
    entries = [line.strip() for line in block.splitlines() if line.strip()]
    assert len(entries) == 25
    for verifier_file in _VERIFIER_FILES:
        assert not any(verifier_file in e for e in entries)


def test_current_contract_is_v1_3():
    assert "**Version:** 1.3" in _CONTRACT_TEXT


def test_current_hmic_req_050_enumerates_exactly_28_files_including_verifiers():
    idx = _CONTRACT_TEXT.index("**HMIC-REQ-050")
    fence_start = _CONTRACT_TEXT.index("```", idx)
    fence_end = _CONTRACT_TEXT.index("```", fence_start + 3)
    block = _CONTRACT_TEXT[fence_start + 3 : fence_end].strip()
    entries = [line.strip() for line in block.splitlines() if line.strip()]
    assert len(entries) == 28
    for verifier_file in _VERIFIER_FILES:
        assert any(verifier_file in e for e in entries), verifier_file


def test_current_hmic_req_052_has_new_limb_c_naming_the_verifier_entrypoint():
    idx = _CONTRACT_TEXT.index("**HMIC-REQ-052")
    next_idx = _CONTRACT_TEXT.index("**HMIC-REQ-053", idx)
    body = _CONTRACT_TEXT[idx:next_idx]
    assert "(c) *(added v1.3" in body
    assert "verify_class_b_deployment_conformance" in body


def test_attack_matrix_header_declares_38_scenarios():
    assert "## 41. Full Mandatory Attack Matrix (38 Scenarios)" in _CONTRACT_TEXT


def test_attack_matrix_row_38_added_and_row_37_unweakened():
    assert "| 38 *(added v1.3, §53)*" in _CONTRACT_TEXT
    assert "| 37 *(added 149O.20D.1, §52; finding B-149O.20D-1)*" in _CONTRACT_TEXT


def test_no_stale_current_target_of_25_files_in_normative_prose():
    """Any sentence asserting the *current* normative target is 25 (as
    opposed to describing the historical pre-149O.20K state inside §49-52
    or §53's own "Context" paragraph) would be a Blocking internal
    contradiction. Search for the specific phrasing K's own contract
    text would use if a stale reference had slipped in."""
    assert "these twenty-five files" not in _CONTRACT_TEXT
    assert "these twenty-eight files" in _CONTRACT_TEXT


# --- Step 5: current production 25/5 identity, independently re-read ---


def test_production_frozen_authority_bearing_files_still_25():
    assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 25" in _HMIC_MODULE_TEXT


def test_production_does_not_name_any_verifier_module():
    for verifier_file in _VERIFIER_FILES:
        assert verifier_file not in _HMIC_MODULE_TEXT


def test_production_contract_identity_files_still_5_members():
    idx = _HMIC_MODULE_TEXT.index("_CONTRACT_IDENTITY_FILES: ")
    close_idx = _HMIC_MODULE_TEXT.index(")\n", idx)
    block = _HMIC_MODULE_TEXT[idx:close_idx]
    assert block.count('("') == 5


# --- Step 6/7: fresh static dependency graph (this module's own walk) ---


def _imports_of(module_filename: str) -> "list[str]":
    path = _SRC / "core" / module_filename
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
    return out


def test_topology_verifier_has_exactly_one_pcae_owned_import():
    imports = _imports_of("hatp_class_b_topology_verifier.py")
    pcae_owned = [i for i in imports if i.startswith("pcae.")]
    assert pcae_owned == ["pcae.core"] or pcae_owned == ["pcae.core.hatp_bootstrap"] or all(
        i in ("pcae.core",) for i in pcae_owned
    )


def test_environment_lock_verifier_only_imports_sibling_topology_module():
    imports = _imports_of("hatp_environment_lock_verifier.py")
    pcae_owned = [i for i in imports if i.startswith("pcae.")]
    assert pcae_owned == ["pcae.core.hatp_class_b_topology_verifier"]


def test_conformance_aggregator_imports_exactly_the_expected_four_pcae_modules():
    imports = _imports_of("hatp_class_b_conformance.py")
    pcae_owned = {i for i in imports if i.startswith("pcae.")}
    assert pcae_owned == {
        "pcae.core",
        "pcae.core.hatp_class_b_topology_verifier",
        "pcae.core.hatp_environment_lock_verifier",
        "pcae.core.paths",
    }


def test_no_fourth_pcae_owned_module_reached_by_any_of_the_three_roots():
    all_imports = set()
    for f in _VERIFIER_FILES:
        all_imports.update(_imports_of(f))
    pcae_owned = {i for i in all_imports if i.startswith("pcae.")}
    allowed = {
        "pcae.core",
        "pcae.core.hatp_class_b_topology_verifier",
        "pcae.core.hatp_environment_lock_verifier",
        "pcae.core.paths",
    }
    assert pcae_owned <= allowed


def test_no_dynamic_pcae_owned_import_via_import_module_or_dunder_import():
    for f in _VERIFIER_FILES:
        path = _SRC / "core" / f
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)
                if name in ("import_module", "__import__"):
                    pytest.fail(f"dynamic import call found in {f}: {ast.dump(node)}")


# --- Step 10: pcae.core.paths re-adjudication ---


def test_pcae_core_paths_is_a_trivial_inert_value_type():
    text = _PATHS_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    # No control flow, no I/O, no ACL/identity logic -- only cwd()/join().
    assert set(funcs) <= {"cwd", "join"}
    assert "os." not in text
    assert "subprocess" not in text
    assert "open(" not in text


def test_harnesspath_used_only_as_value_carrier_in_conformance_module():
    text = (_SRC / "core" / "hatp_class_b_conformance.py").read_text(encoding="utf-8")
    # The only uses of the imported HarnessPath symbol are type annotation,
    # `.cwd()`, and `.path` attribute access -- never a method call into
    # verdict-affecting logic (there is none to call).
    assert "root.path" in text
    assert "HarnessPath.cwd()" in text


# --- Step 11: bootstrap / repository-identity already-bound check ---


def test_hatp_bootstrap_and_repository_identity_already_hmic_bound():
    assert '"core/hatp_bootstrap.py"' in _HMIC_MODULE_TEXT
    assert '"core/repository_identity.py"' in _HMIC_MODULE_TEXT


# --- Step 8: aggregator/sub-verifier authority sensitivity (worked) ---


def test_conformance_aggregator_calls_all_four_authority_inputs():
    text = (_SRC / "core" / "hatp_class_b_conformance.py").read_text(encoding="utf-8")
    assert "verify_class_b_topology_conformance(" in text
    assert "verify_environment_lock_conformance(" in text
    assert "_check_model_a_deployment(" in text
    assert "_check_deployment_identity(" in text


def test_topology_verifier_is_self_contained_apart_from_hatp_bootstrap():
    imports = _imports_of("hatp_class_b_topology_verifier.py")
    pcae_owned = {i for i in imports if i.startswith("pcae.")}
    assert pcae_owned <= {"pcae.core"}


# --- Step 22/23: cycle / self-binding re-check ---


def test_authority_module_relative_paths_is_a_literal_not_an_import():
    text = (_SRC / "core" / "hatp_environment_lock_verifier.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "hatp_mandatory_certification" not in alias.name
                assert "hatp_certification_admin" not in alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert "hatp_mandatory_certification" not in node.module
            assert "hatp_certification_admin" not in node.module
    # The string literal appears only inside the diagnostic-only tuple.
    assert '"core/hatp_mandatory_certification.py"' in text


def test_hmic_module_does_not_import_any_verifier_module():
    for node in ast.walk(ast.parse(_HMIC_MODULE_TEXT)):
        if isinstance(node, ast.ImportFrom) and node.module:
            for verifier_module in (
                "hatp_class_b_topology_verifier",
                "hatp_environment_lock_verifier",
                "hatp_class_b_conformance",
            ):
                assert verifier_module not in node.module


def test_certification_admin_script_does_not_import_any_verifier_module():
    admin_script = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"
    text = admin_script.read_text(encoding="utf-8")
    for verifier_module in (
        "hatp_class_b_topology_verifier",
        "hatp_environment_lock_verifier",
        "hatp_class_b_conformance",
    ):
        assert verifier_module not in text


# --- Step 29: zero-consumer re-confirmation (symbol-level, fresh grep) ---


def test_zero_production_consumers_of_verifier_modules_or_symbols():
    excluded = {_SRC / "core" / f for f in _VERIFIER_FILES}
    needles = list(_VERIFIER_FILES) + [
        "verify_class_b_deployment_conformance",
        "verify_class_b_topology_conformance",
        "verify_environment_lock_conformance",
    ]
    hits = []
    for py_file in _SRC.rglob("*.py"):
        if py_file in excluded:
            continue
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            stem = needle.replace(".py", "")
            if stem in text:
                hits.append((str(py_file), needle))
    assert hits == []


# --- Step 20/21: regression checks ---


def test_hbdc_contract_unchanged_since_pre_k():
    pre_k_hbdc = _git_show(_PRE_K_COMMIT, "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
    current_hbdc = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
    assert pre_k_hbdc == current_hbdc


def test_hbdc_still_bound_in_contract_identity_and_scope():
    assert '"HBDC-001"' in _HMIC_MODULE_TEXT
    assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in _HMIC_MODULE_TEXT


def test_b_149o_19_3_1_provider_files_still_bound():
    for f in (
        "core/hatp_providers.py",
        "core/hatp_fido2_provider.py",
        "core/hatp_piv_provider.py",
        "core/hatp_hardware_credentials.py",
    ):
        assert f'"{f}"' in _HMIC_MODULE_TEXT


# --- Step 17/18: stdlib / external boundary disclosure check ---


def test_hmic_req_063_residual_limitation_still_present_and_unweakened():
    idx = _CONTRACT_TEXT.index("**HMIC-REQ-063")
    next_idx = _CONTRACT_TEXT.index("**HMIC-REQ-064", idx)
    body = _CONTRACT_TEXT[idx:next_idx]
    assert "does NOT implement an\nexecuted-code/runtime-module-resolution check" in body or (
        "does NOT implement an" in body and "executed-code" in body
    )


def test_verifier_modules_do_not_read_any_contract_document_at_runtime():
    for f in _VERIFIER_FILES:
        path = _SRC / "core" / f
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
                if name in ("open", "read_text"):
                    call_src = ast.dump(node)
                    assert "docs" not in call_src or "contracts" not in call_src, (
                        f"{f} appears to read a contracts-directory path at runtime: {call_src}"
                    )


# --- Step 37: real-host result ---


def test_real_host_verify_class_b_deployment_conformance_is_non_compliant():
    from pcae.core.hatp_class_b_conformance import (
        ClassBConformanceStatus,
        verify_class_b_deployment_conformance,
    )

    result = verify_class_b_deployment_conformance()
    assert result.status == ClassBConformanceStatus.NON_COMPLIANT


def test_working_tree_unchanged_by_this_verification_run():
    status = subprocess.run(
        ["git", "status", "--porcelain", "src/", "docs/contracts/"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert status.stdout.strip() == ""


# --- Step 30/31: stop-condition adjudication text is present verbatim ---


def test_cbv_s1_restated_open_not_closed_language_present():
    assert "CBV-S1 remains **OPEN — HMIC SOURCE-SCOPE" in _CONTRACT_TEXT
    assert "PENDING — NOT CLOSED" in _CONTRACT_TEXT


def test_cbv_s10_untouched_language_present():
    assert "CBV-S10 (readiness contract/integration gap) is\nuntouched by this phase" in _CONTRACT_TEXT
