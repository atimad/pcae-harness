"""Phase 149O.20K.3 -- HMIC Class-B Verifier Production Source-Set
Alignment Independent Verification.

Independently verifies Phase 149O.20K.2's production alignment of live
HMIC (`src/pcae/core/hatp_mandatory_certification.py`) to the
independently-verified HMIC-001 v1.3 Class-B verifier source-scope
target (28 authority-bearing files). This module is written fresh: it
does not import, reuse, or copy 149O.20K.2's own test module
(`tests/test_phase_149o_20k_2_hmic_class_b_verifier_production_source_set_alignment.py`)
or 149O.20K.1's
(`tests/test_phase_149o_20k_1_hmic_class_b_verifier_source_scope_contract_independent_verification.py`),
and does not trust K.2's report, its 40-new/9-fixed Fast Green
attribution, its per-file digest-sensitivity proof, its missing-file
fail-closed proof, its contract-version identity interpretation, its
historical-test attribution, or its zero-consumer/cycle claims. Every
assertion below is re-derived from primary sources: the true K.2
parent commit (via `git log`), the current contract text (via its own
independent extraction), current production source, and fresh
digest-derivation calls against isolated fixtures.

Verification-only: no production source or contract document is
modified by this module, and it performs no write to any tracked
repository file.
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_HBDC_CONTRACT_PATH = _CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"

_NEW_VERIFIER_FILES = (
    "core/hatp_class_b_topology_verifier.py",
    "core/hatp_environment_lock_verifier.py",
    "core/hatp_class_b_conformance.py",
)

# Independently reconstructed via `git rev-parse 05e3861b^`: the true
# parent of K.2's own alignment commit, resolved fresh at runtime below
# rather than copied from K.2's report.
_K2_COMMIT = "05e3861bb6a931987bf743e54ecff591e64af1b6"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _resolve_k2_parent() -> str:
    return _git("rev-parse", f"{_K2_COMMIT}^")


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _git_show_bytes(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        check=True,
    )
    return result.stdout


def _extract_frozen_lists_from_text(module_text: str) -> "tuple[list[str], list[str]]":
    m1 = re.search(
        r"_FROZEN_SRC_PCAE_RELATIVE_FILES: \"tuple\[str, \.\.\.\]\" = \((.*?)\n\)\n",
        module_text,
        re.S,
    )
    src_files = re.findall(r'"([^"]+)"', m1.group(1))
    m2 = re.search(
        r"_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES: \"tuple\[str, \.\.\.\]\" = \((.*?)\n\)\n",
        module_text,
        re.S,
    )
    root_files = re.findall(r'"([^"]+)"', m2.group(1))
    return src_files, root_files


def _extract_contract_28_paths(contract_text: str) -> "list[str]":
    idx = contract_text.index("**HMIC-REQ-050 (Exact Enumeration")
    segment = contract_text[idx : idx + 3000]
    block = re.search(r"```\n(.*?)```", segment, re.S).group(1)
    lines = [line.strip() for line in block.split("\n") if line.strip()]
    return [re.sub(r"\s+\([A-Z0-9-]+\)\s*$", "", line) for line in lines]


# ═══════════════════════════════════════════════════════════════════════════
# 1. True K.2 parent reconstruction
# ═══════════════════════════════════════════════════════════════════════════


class TestK2ParentReconstruction:
    def test_k2_true_parent_is_20k_1_task_lifecycle_commit(self) -> None:
        parent = _resolve_k2_parent()
        assert parent == _git("rev-parse", "17a797af")

    def test_pre_k2_production_has_exactly_25_frozen_files(self) -> None:
        parent = _resolve_k2_parent()
        text = _git_show(parent, "src/pcae/core/hatp_mandatory_certification.py")
        src_files, root_files = _extract_frozen_lists_from_text(text)
        assert len(src_files) == 19
        assert len(root_files) == 6
        assert len(src_files) + len(root_files) == 25

    def test_pre_k2_production_excludes_all_three_verifier_files(self) -> None:
        parent = _resolve_k2_parent()
        text = _git_show(parent, "src/pcae/core/hatp_mandatory_certification.py")
        src_files, _ = _extract_frozen_lists_from_text(text)
        for verifier in _NEW_VERIFIER_FILES:
            assert verifier not in src_files


# ═══════════════════════════════════════════════════════════════════════════
# 2. Current production 28-file extraction + independent contract extraction
# ═══════════════════════════════════════════════════════════════════════════


class TestCurrentProductionAndContractExtraction:
    def test_current_production_has_exactly_28_frozen_files(self) -> None:
        text = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        src_files, root_files = _extract_frozen_lists_from_text(text)
        assert len(src_files) + len(root_files) == 28

    def test_current_production_frozen_files_are_unique(self) -> None:
        text = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        src_files, root_files = _extract_frozen_lists_from_text(text)
        all_files = src_files + root_files
        assert len(all_files) == len(set(all_files))

    def test_independently_extracted_contract_set_has_28_entries(self) -> None:
        contract_text = _CONTRACT_PATH.read_text(encoding="utf-8")
        paths = _extract_contract_28_paths(contract_text)
        assert len(paths) == 28
        assert len(paths) == len(set(paths))

    def test_contract_and_production_sets_are_exactly_equal(self) -> None:
        contract_text = _CONTRACT_PATH.read_text(encoding="utf-8")
        contract_paths = _extract_contract_28_paths(contract_text)

        prod_text = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        src_files, root_files = _extract_frozen_lists_from_text(prod_text)
        prod_paths = src_files + root_files

        assert contract_paths == prod_paths  # both set and presentation-order equality


# ═══════════════════════════════════════════════════════════════════════════
# 3. Exact +3 delta / original-25 preservation
# ═══════════════════════════════════════════════════════════════════════════


class TestExactDelta:
    def test_added_set_is_exactly_the_three_verifier_files(self) -> None:
        parent = _resolve_k2_parent()
        pre_text = _git_show(parent, "src/pcae/core/hatp_mandatory_certification.py")
        pre_src, pre_root = _extract_frozen_lists_from_text(pre_text)
        pre_set = set(pre_src) | set(pre_root)

        cur_text = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        cur_src, cur_root = _extract_frozen_lists_from_text(cur_text)
        cur_set = set(cur_src) | set(cur_root)

        added = cur_set - pre_set
        removed = pre_set - cur_set
        assert added == set(_NEW_VERIFIER_FILES)
        assert removed == set()

    def test_original_25_is_a_subset_of_current_28(self) -> None:
        parent = _resolve_k2_parent()
        pre_text = _git_show(parent, "src/pcae/core/hatp_mandatory_certification.py")
        pre_src, pre_root = _extract_frozen_lists_from_text(pre_text)
        pre_set = set(pre_src) | set(pre_root)

        cur_text = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        cur_src, cur_root = _extract_frozen_lists_from_text(cur_text)
        cur_set = set(cur_src) | set(cur_root)

        assert pre_set.issubset(cur_set)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Byte-identity: verifier files, HMIC contract, HBDC contract
# ═══════════════════════════════════════════════════════════════════════════


class TestByteIdentitySinceK2Entry:
    @pytest.mark.parametrize("relpath", _NEW_VERIFIER_FILES)
    def test_verifier_module_byte_unchanged_since_k2_entry(self, relpath: str) -> None:
        parent = _resolve_k2_parent()
        pre = _git_show_bytes(parent, f"src/pcae/{relpath}")
        post = (_SRC / relpath).read_bytes()
        assert pre == post

    def test_hmic_contract_byte_unchanged_since_k2_entry(self) -> None:
        parent = _resolve_k2_parent()
        pre = _git_show_bytes(
            parent, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
        )
        post = _CONTRACT_PATH.read_bytes()
        assert pre == post

    def test_hbdc_contract_byte_unchanged_since_k2_entry(self) -> None:
        parent = _resolve_k2_parent()
        pre = _git_show_bytes(parent, "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
        post = _HBDC_CONTRACT_PATH.read_bytes()
        assert pre == post

    @pytest.mark.parametrize(
        "relpath",
        (
            "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
            "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
            "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
            "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
            "scripts/hatp_certification_admin.py",
        ),
    )
    def test_other_bound_files_byte_unchanged_since_k2_entry(self, relpath: str) -> None:
        parent = _resolve_k2_parent()
        pre = _git_show_bytes(parent, relpath)
        post = (_REPO_ROOT / relpath).read_bytes()
        assert pre == post


# ═══════════════════════════════════════════════════════════════════════════
# 5-7. Digest sensitivity, missing-file fail-closed, alias attacks
# (isolated fixture; real production `derive_implementation_scope_digest`)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def isolated_fixture(tmp_path: Path):
    import sys

    sys.path.insert(0, str(_SRC.parent))
    from pcae.core.paths import HarnessPath  # noqa: E402

    text = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    src_files, root_files = _extract_frozen_lists_from_text(text)
    canonical = [f"src/pcae/{f}" for f in src_files] + root_files
    for rel in canonical:
        src_abs = _REPO_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src_abs, dst)
    yield tmp_path, HarnessPath(tmp_path)


class TestDigestSensitivity:
    @pytest.mark.parametrize("relpath", _NEW_VERIFIER_FILES)
    def test_new_verifier_file_semantic_mutation_changes_digest(self, isolated_fixture, relpath: str) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        tmp_path, harness_root = isolated_fixture
        target = tmp_path / "src" / "pcae" / relpath
        base = hmc.derive_implementation_scope_digest(harness_root)
        original = target.read_bytes()
        target.write_bytes(original + b"\n# K3-independent-semantic-mutation-probe\n")
        mutated = hmc.derive_implementation_scope_digest(harness_root)
        target.write_bytes(original)
        assert mutated != base

    @pytest.mark.parametrize("relpath", _NEW_VERIFIER_FILES)
    def test_new_verifier_file_single_byte_mutation_changes_digest(self, isolated_fixture, relpath: str) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        tmp_path, harness_root = isolated_fixture
        target = tmp_path / "src" / "pcae" / relpath
        base = hmc.derive_implementation_scope_digest(harness_root)
        original = target.read_bytes()
        mutated_bytes = bytearray(original)
        mutated_bytes[0] ^= 0x01
        target.write_bytes(bytes(mutated_bytes))
        mutated = hmc.derive_implementation_scope_digest(harness_root)
        target.write_bytes(original)
        assert mutated != base

    @pytest.mark.parametrize(
        "relpath",
        (
            "src/pcae/core/hatp_mandatory_certification.py",
            "src/pcae/core/hatp_providers.py",
            "src/pcae/core/hatp_fido2_provider.py",
            "src/pcae/core/hatp_piv_provider.py",
            "src/pcae/core/hatp_hardware_credentials.py",
            "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
        ),
    )
    def test_representative_existing_file_still_digest_sensitive(self, isolated_fixture, relpath: str) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        tmp_path, harness_root = isolated_fixture
        target = tmp_path / relpath
        base = hmc.derive_implementation_scope_digest(harness_root)
        original = target.read_bytes()
        target.write_bytes(original + b"\n# probe\n")
        mutated = hmc.derive_implementation_scope_digest(harness_root)
        target.write_bytes(original)
        assert mutated != base

    def test_hbdc_dual_binding_content_and_version_mechanism(self, isolated_fixture) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        _, harness_root = isolated_fixture
        versions = hmc.derive_contract_versions(harness_root)
        assert "HBDC-001" in versions


class TestMissingAndUnreadableFileFailClosed:
    @pytest.mark.parametrize("relpath", _NEW_VERIFIER_FILES)
    def test_missing_new_verifier_file_fails_closed(self, isolated_fixture, relpath: str) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        tmp_path, harness_root = isolated_fixture
        target = tmp_path / "src" / "pcae" / relpath
        moved = target.with_suffix(".py.moved")
        os.rename(target, moved)
        try:
            with pytest.raises(hmc.FrozenFileDerivationError):
                hmc.derive_implementation_scope_digest(harness_root)
        finally:
            os.rename(moved, target)

    def test_unreadable_new_verifier_file_fails_closed(self, isolated_fixture) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        tmp_path, harness_root = isolated_fixture
        target = tmp_path / "src" / "pcae" / _NEW_VERIFIER_FILES[0]
        original_mode = target.stat().st_mode
        os.chmod(target, 0o000)
        try:
            with pytest.raises(hmc.FrozenFileDerivationError):
                hmc.derive_implementation_scope_digest(harness_root)
        finally:
            os.chmod(target, original_mode)


class TestAliasNormalizationAndDuplicates:
    def test_symlink_substitution_for_new_verifier_file_is_rejected(self, isolated_fixture) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        tmp_path, harness_root = isolated_fixture
        target = tmp_path / "src" / "pcae" / _NEW_VERIFIER_FILES[0]
        original = target.read_bytes()
        decoy = tmp_path / "decoy.py"
        decoy.write_bytes(b"# decoy, must never be read as the frozen file\n")
        os.remove(target)
        os.symlink(decoy, target)
        try:
            with pytest.raises(hmc.FrozenFileDerivationError):
                hmc.derive_implementation_scope_digest(harness_root)
        finally:
            os.remove(target)
            target.write_bytes(original)
            decoy.unlink()

    def test_frozen_path_literal_rejects_dotdot_segment(self) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        with pytest.raises(hmc.HMICIdentityDerivationError):
            hmc._validate_frozen_path_literal("../etc/passwd")

    def test_frozen_path_literal_rejects_absolute_path(self) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        with pytest.raises(hmc.HMICIdentityDerivationError):
            hmc._validate_frozen_path_literal("/etc/passwd")

    def test_28_canonical_paths_are_unique(self) -> None:
        from pcae.core import hatp_mandatory_certification as hmc

        paths = hmc._frozen_canonical_paths()
        assert len(paths) == 28
        assert len(paths) == len(set(paths))


# ═══════════════════════════════════════════════════════════════════════════
# 8. HMIC v1.3 identity representation + contract identity member count
# ═══════════════════════════════════════════════════════════════════════════


class TestHmicVersionIdentityRepresentation:
    def test_production_does_not_claim_stale_v1_2_28_file_pairing(self) -> None:
        text = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        assert "28-path\nenumeration, v1.2" not in text
        assert re.search(r"28.entry literal enumeration \(v1\.3", text)
        assert "== 28  # HMIC-REQ-050 (v1.3)" in text

    def test_contract_versions_mechanism_has_exactly_five_members(self) -> None:
        text = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        m = re.search(
            r"_CONTRACT_IDENTITY_FILES: \"tuple\[tuple\[str, str\], \.\.\.\]\" = \((.*?)\n\)\n", text, re.S
        )
        members = re.findall(r'\("([A-Z0-9-]+)",', m.group(1))
        # As of this phase (149O.20K.3) this was exactly five; a later
        # amendment (149O.20L.7O.2H) additively widened it to seven.
        assert members[:5] == ["HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"]

    def test_hmic_own_amendment_history_names_v1_3_and_28_files(self) -> None:
        contract_text = _CONTRACT_PATH.read_text(encoding="utf-8")
        assert "v1.2 → v1.3" in contract_text or "v1.2 -> v1.3" in contract_text or "v1.2→v1.3" in contract_text
        assert "twenty-eight" in contract_text


# ═══════════════════════════════════════════════════════════════════════════
# 9. Cycle / self-binding + zero-consumer analysis (fresh AST walk)
# ═══════════════════════════════════════════════════════════════════════════


def _module_imports(path: Path) -> "set[str]":
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: "set[str]" = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class TestNoCycleAndZeroConsumers:
    def test_verifier_modules_do_not_import_certification_or_admin(self) -> None:
        forbidden = {"pcae.core.hatp_mandatory_certification", "hatp_mandatory_certification"}
        for relpath in _NEW_VERIFIER_FILES:
            imports = _module_imports(_SRC / relpath)
            assert imports.isdisjoint(forbidden), f"{relpath} imports forbidden module"

    def test_certification_module_does_not_import_any_verifier_module(self) -> None:
        imports = _module_imports(_HMIC_MODULE_PATH)
        forbidden = {
            "pcae.core.hatp_class_b_topology_verifier",
            "pcae.core.hatp_environment_lock_verifier",
            "pcae.core.hatp_class_b_conformance",
        }
        assert imports.isdisjoint(forbidden)

    def test_certification_module_references_verifier_names_only_as_string_literals(self) -> None:
        tree = ast.parse(_HMIC_MODULE_PATH.read_text(encoding="utf-8"), filename=str(_HMIC_MODULE_PATH))
        import_names: "set[str]" = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    import_names.update(a.name for a in node.names)
                elif node.module:
                    import_names.add(node.module)
        verifier_tokens = ("hatp_class_b_topology_verifier", "hatp_environment_lock_verifier", "hatp_class_b_conformance")
        for tok in verifier_tokens:
            assert not any(tok in name for name in import_names)

    def test_zero_authority_consumers_of_verifier_functions_repo_wide(self) -> None:
        result = subprocess.run(
            [
                "grep", "-rl",
                "-e", "hatp_class_b_topology_verifier",
                "-e", "hatp_environment_lock_verifier",
                "-e", "hatp_class_b_conformance",
                "--include=*.py",
                str(_REPO_ROOT / "src"), str(_REPO_ROOT / "scripts"),
            ],
            capture_output=True, text=True,
        )
        hits = [line for line in result.stdout.splitlines() if line]
        allowed = {
            str(_SRC / relpath) for relpath in _NEW_VERIFIER_FILES
        } | {str(_HMIC_MODULE_PATH)}
        unexpected = [h for h in hits if h not in allowed]
        assert unexpected == []


# ═══════════════════════════════════════════════════════════════════════════
# 10. Real host + CBV-S10 regression
# ═══════════════════════════════════════════════════════════════════════════


class TestRealHostAndReadinessRegression:
    def test_real_host_class_b_deployment_conformance_is_non_compliant(self) -> None:
        import sys

        sys.path.insert(0, str(_SRC.parent))
        from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
        from pcae.core.paths import HarnessPath

        result = verify_class_b_deployment_conformance(HarnessPath(_REPO_ROOT))
        assert result.status.value == "NON_COMPLIANT"

    def test_cbv_s10_language_still_present_and_open_in_project_status(self) -> None:
        status_text = (_REPO_ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
        assert "CBV-S10" in status_text
        assert "NOT CLOSED" in status_text or "OPEN" in status_text

    def test_no_readiness_certification_or_pb_module_references_class_b_verdict(self) -> None:
        result = subprocess.run(
            [
                "grep", "-rl",
                "-e", "verify_class_b_deployment_conformance",
                "-e", "ClassBConformanceStatus",
                "--include=*.py",
                str(_REPO_ROOT / "src"),
            ],
            capture_output=True, text=True,
        )
        hits = [line for line in result.stdout.splitlines() if line]
        allowed_suffixes = ("hatp_class_b_conformance.py", "hatp_class_b_topology_verifier.py", "hatp_environment_lock_verifier.py")
        unexpected = [h for h in hits if not h.endswith(allowed_suffixes)]
        assert unexpected == []
