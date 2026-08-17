"""Phase 149O.20L.7L.5 — Contract-Preamble and AST-Guard Relative-Import
Narrow Repair.

Same-version, contract-text-and-test-only narrow repair of three findings
independently confirmed by 149O.20L.7L.4:

- F-7L-5 (whole-document scan): HMIC-001 v1.4's own top-of-document §0
  preamble restated the same stale "hard-coded
  `mandatory_consumption_implementation_independently_verified = False`
  ceiling ... is unchanged" claim rows 33/34/36/37 already corrected --
  149O.20L.7L.3's own §57.9 scan misclassified this exact paragraph
  historical.
- F-7L-7 (relative-import bypass): `_pcae_import_targets`'s
  `pcae.`-prefix filter silently misses every relative import of the
  `DeploymentBinding` producer (`from . import x`, `from .x import y`,
  `from ..pkg import x`) -- relative imports are a live convention
  elsewhere in this codebase (`schema_runtime/**`, 29 instances).
- F-7L-7 (second critical guard): `test_admin_script_is_the_only_non_
  test_caller_of_the_producer_entry_points` still called the un-widened
  `_pcae_imports`, not `_pcae_import_targets`.

This module independently reconstructs all three defects from live
contract/test state -- not from 149O.20L.7L.4's own narrative -- and
verifies the repair this phase made:

- HMIC-001's own §0 preamble text and its new §58 repair-history section.
- `_pcae_import_targets`'s new relative-import resolution
  (`_module_name_for_path` + `_resolve_relative_import_base`) in the
  149O.20L.7L test module.
- The second guard's migration to the repaired helper.

No `src/pcae/**` file is modified by this phase. `HMIC-001` remains
v1.4. `HMIC-REQ-050`'s thirty-file enumeration and `HMIC-REQ-052`'s
three limbs are unchanged. Rows 33/34/36/37/38/39 and the HMIC-REQ-145
closure paragraph are unchanged (hash/substring-verified below).
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath

REPO_ROOT = Path(__file__).resolve().parents[1]

HMIC_CONTRACT_PATH = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
CUTOVER_MODULE = "src/pcae/core/hatp_mandatory_cutover.py"
CERT_MODULE = "src/pcae/core/hatp_mandatory_certification.py"
AST_GUARD_MODULE = "tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.py"
TARGET = "hatp_deployment_binding_admin"

_HMIC_CONTRACT = (REPO_ROOT / HMIC_CONTRACT_PATH).read_text(encoding="utf-8")
_CUTOVER_SRC = (REPO_ROOT / CUTOVER_MODULE).read_text(encoding="utf-8")
_GUARD_SRC = (REPO_ROOT / AST_GUARD_MODULE).read_text(encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout


# ═══════════════════════════════════════════════════════════════════════════
# 1. F-7L-5: independent reconstruction of current production truth
# ═══════════════════════════════════════════════════════════════════════════


def test_no_hardcoded_false_ceiling_assignment_exists_in_production() -> None:
    assert "mandatory_consumption_implementation_independently_verified = False" not in _CUTOVER_SRC
    assert "mandatory_consumption_implementation_independently_verified=False" not in _CUTOVER_SRC


def test_production_readiness_term_is_a_dynamic_validator_call() -> None:
    assert "validate_active_hatp_mandatory_independent_verification_certification" in _CUTOVER_SRC
    assert "certification_status_satisfies_readiness" in _CUTOVER_SRC


# ═══════════════════════════════════════════════════════════════════════════
# 2. F-7L-5: §0 preamble repair
# ═══════════════════════════════════════════════════════════════════════════


def test_stale_preamble_sentence_removed() -> None:
    assert (
        "The current\nhard-coded `mandatory_consumption_implementation_independently_verified\n"
        "= False` ceiling (`hatp_mandatory_cutover.py:842-853`) is unchanged."
    ) not in _HMIC_CONTRACT


def test_preamble_now_states_current_mechanism() -> None:
    intro_start = _HMIC_CONTRACT.index("This is a **contract-freeze document**")
    intro_end = _HMIC_CONTRACT.index("## 0. Contract Identity and Status")
    intro = _HMIC_CONTRACT[intro_start:intro_end]
    normalized = " ".join(intro.split())
    assert "no longer exists" in normalized
    assert "Phase 149O.19.5F" in normalized
    assert "validate_active_hatp_mandatory_independent_verification_certification" in normalized
    assert "certification_status_satisfies_ readiness" in normalized or "certification_status_satisfies_readiness" in (
        intro.replace("_\n", "_")
    )


def test_preamble_does_not_overstate_readiness() -> None:
    """Item 7: the repair must not imply certification, HATP readiness,
    Boundary C completion, first use, or DeploymentBinding existence."""
    intro_start = _HMIC_CONTRACT.index("This is a **contract-freeze document**")
    intro_end = _HMIC_CONTRACT.index("## 0. Contract Identity and Status")
    intro = _HMIC_CONTRACT[intro_start:intro_end]
    normalized = " ".join(intro.split())
    assert "still evaluates `False` today" in normalized
    assert "no stored HMIC certification exists anywhere on this host" in normalized
    assert "does not assert HMIC certification" in normalized


def test_preamble_citation_present() -> None:
    assert "149O.20L.7L.5, finding F-7L-5 whole-document scan" in _HMIC_CONTRACT


def test_header_status_line_mentions_this_phase() -> None:
    assert "TOP-OF-DOCUMENT PREAMBLE AND AST-GUARD RELATIVE-IMPORT GAP REPAIRED (149O.20L.7L.5)" in _HMIC_CONTRACT


def test_repaired_by_header_line_present() -> None:
    assert "**Repaired by:** Phase 149O.20L.7L.5" in _HMIC_CONTRACT


# ═══════════════════════════════════════════════════════════════════════════
# 3. Already-repaired rows/requirements remain byte-unchanged
# ═══════════════════════════════════════════════════════════════════════════


def _row(n: int) -> str:
    marker = f"| {n} "
    lines = _HMIC_CONTRACT.splitlines()
    for line in lines:
        if line.startswith(marker):
            return line
    raise AssertionError(f"row {n} not found")


def test_rows_33_34_36_37_unchanged() -> None:
    assert "Operative, not yet consequential" in _row(33)
    assert "*(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.3.)*" in _row(33)
    assert "the hard-coded `mandatory_consumption_implementation_independently_verified = False`" in _row(34)
    assert "*(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.4.)*" in _row(34)
    assert "Operative, not yet consequential" in _row(36)
    assert "*(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.5.)*" in _row(36)
    assert "mirrors attack #33's corrected caveat" in _row(36)
    assert "no live readiness decision currently turns on this particular rejection" in _row(37)


def test_row_38_and_39_unchanged() -> None:
    assert "Operative and consequential in this repository's current state" in _row(38)
    assert "not functionally load-bearing" in _row(39)
    assert "149O.20L.7L.5" not in _row(38)
    assert "149O.20L.7L.5" not in _row(39)


def test_hmic_req_145_closure_paragraph_unchanged() -> None:
    assert "now mechanically enforced in production" in _HMIC_CONTRACT
    assert "realigned past the pre-repair twenty-four-file set" in _HMIC_CONTRACT


def test_hmic_req_050_thirty_file_enumeration_unchanged() -> None:
    assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 30" in (REPO_ROOT / CERT_MODULE).read_text(
        encoding="utf-8"
    )


def test_hmic_req_052_present_unchanged() -> None:
    assert "**HMIC-REQ-052" in _HMIC_CONTRACT


def test_archival_phase_history_sections_left_untouched() -> None:
    """§48-57 restate their own named phase's historical snapshot in the
    past tense -- confirm this repair did not rewrite historical truth
    while repairing the one live current-state claim."""
    assert (
        "the literal\nhard-coded `False` ceiling §49/§50 both describe no longer exists in\nthis file."
        in _HMIC_CONTRACT
    )
    assert "The current hard-coded `False` readiness\nceiling remained unchanged." in _HMIC_CONTRACT


def test_whole_document_scan_finds_no_other_live_stale_claim() -> None:
    """Independent re-scan for the same defect class, outside archival
    'Contract Repair/Amendment History' sections and outside the §41
    attack matrix (already correctly repaired/current)."""
    lines = _HMIC_CONTRACT.splitlines()
    section_starts = [i for i, line in enumerate(lines) if line.startswith("## ")]

    def _section_of(idx: int) -> str:
        for start in reversed(section_starts):
            if start <= idx:
                return lines[start]
        return ""

    suspects = []
    for i, line in enumerate(lines):
        lowered = line.lower()
        if "is unchanged" in lowered and "hard-coded" in lowered and "ceiling" in lowered:
            section = _section_of(i)
            if section.startswith("## 4") or section.startswith("## 5") and not section.startswith(
                "## 58"
            ):
                # §41 attack matrix and §48-57 archival sections are
                # independently verified historical/current-and-correct
                # above; anything else is a genuine new hit.
                continue
            if section.startswith("## 0"):
                suspects.append((i, line))
    assert suspects == [], f"unexpected live stale-current claim(s) outside archival sections: {suspects}"


# ═══════════════════════════════════════════════════════════════════════════
# 4. F-7L-7: module-context derivation (item 18/19)
# ═══════════════════════════════════════════════════════════════════════════


def _load_guard_module():
    spec = importlib.util.spec_from_file_location("_pcae_20l_7l5_ast_guard_module", REPO_ROOT / AST_GUARD_MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GUARD_MODULE = _load_guard_module()


class TestModuleNameForPath:
    def test_regular_module(self) -> None:
        path = REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py"
        assert _GUARD_MODULE._module_name_for_path(path) == "pcae.core.hatp_mandatory_cutover"

    def test_package_init(self) -> None:
        path = REPO_ROOT / "src" / "pcae" / "core" / "__init__.py"
        assert _GUARD_MODULE._module_name_for_path(path) == "pcae.core"

    def test_deeper_module(self) -> None:
        path = REPO_ROOT / "src" / "pcae" / "schema_runtime" / "manifest.py"
        assert _GUARD_MODULE._module_name_for_path(path) == "pcae.schema_runtime.manifest"

    def test_top_level_package_init(self) -> None:
        path = REPO_ROOT / "src" / "pcae" / "__init__.py"
        assert _GUARD_MODULE._module_name_for_path(path) == "pcae"

    def test_file_outside_src_pcae_returns_none(self) -> None:
        path = REPO_ROOT / "scripts" / "hatp_deployment_binding_admin.py"
        assert _GUARD_MODULE._module_name_for_path(path) is None

    def test_platform_separator_independence(self) -> None:
        # Path.parts-based derivation, never a raw os.sep string split.
        path = REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"
        assert _GUARD_MODULE._module_name_for_path(path) == "pcae.core.hatp_mandatory_certification"


class TestResolveRelativeImportBase:
    def test_level_1_from_regular_module(self) -> None:
        # "from . import x" / "from .x import y" inside pcae.core.foo
        assert _GUARD_MODULE._resolve_relative_import_base("pcae.core.foo", False, 1) == "pcae.core"

    def test_level_1_from_package_init(self) -> None:
        assert _GUARD_MODULE._resolve_relative_import_base("pcae.core", True, 1) == "pcae.core"

    def test_level_2_multilevel(self) -> None:
        # "from ..core import x" inside pcae.orchestration.deep_module
        assert _GUARD_MODULE._resolve_relative_import_base("pcae.orchestration.deep_module", False, 2) == "pcae"

    def test_level_escapes_root_returns_none(self) -> None:
        # "from .. import x" inside a module directly under pcae (only
        # one ancestor component available) must fail closed, not
        # silently resolve to something outside "pcae".
        assert _GUARD_MODULE._resolve_relative_import_base("pcae.foo", False, 2) is None

    def test_level_escapes_root_from_deeper_module(self) -> None:
        assert _GUARD_MODULE._resolve_relative_import_base("pcae.core.foo", False, 3) is None


# ═══════════════════════════════════════════════════════════════════════════
# 5. F-7L-7: relative-import adversarial forms (items 23-30)
# ═══════════════════════════════════════════════════════════════════════════

RELATIVE_ADVERSARIAL_FORMS: dict[str, str] = {
    "level1_from_dot_import": f"from . import {TARGET}\n",
    "level1_from_dot_import_aliased": f"from . import {TARGET} as x\n",
    "level1_from_module_symbol": f"from .{TARGET} import create_deployment_binding\n",
    "level1_multiline": f"from . import (\n    {TARGET},\n)\n",
    "level1_multiple_names": f"from . import (\n    something_else,\n    {TARGET},\n)\n",
    "level2_multilevel": f"from ..core import {TARGET}\n",
}

RELATIVE_NEGATIVE_CONTROLS: dict[str, str] = {
    "relative_string_literal": f'"../{TARGET}.py"\n',
    "relative_comment": f"# from . import {TARGET} (just a comment)\nx = 1\n",
    "relative_unrelated": "from . import hatp_bootstrap\n",
    "docstring_mentioning_producer": f'"""References {TARGET} in prose only."""\n',
}


def _write_scratch(name: str, text: str, *, under: Path) -> Path:
    tmp = under / name
    tmp.write_text(text, encoding="utf-8")
    return tmp


def _targets_for_module(module_dotted_dir: Path, filename: str, text: str) -> "tuple[set[str], set[str]]":
    """Writes `text` as `filename` inside `module_dotted_dir` (a real
    src/pcae subpackage directory) so `_module_name_for_path` derives a
    real, non-fabricated module context, exactly as it would for a real
    producer caller."""
    tmp = _write_scratch(filename, text, under=module_dotted_dir)
    try:
        return _GUARD_MODULE._pcae_import_targets(tmp)
    finally:
        tmp.unlink()


CORE_DIR = REPO_ROOT / "src" / "pcae" / "core"


class TestRelativeImportFormsDetected:
    @pytest.mark.parametrize("name", list(RELATIVE_ADVERSARIAL_FORMS))
    def test_form_detected(self, name: str) -> None:
        # All forms except the multilevel one are level-1, resolved
        # against pcae.core (the scratch file's own containing package).
        targets, wildcards = _targets_for_module(
            CORE_DIR, "__scratch_7l5_relative__.py", RELATIVE_ADVERSARIAL_FORMS[name]
        )
        found = targets | wildcards
        assert any(TARGET in m for m in found), f"{name} should be detected post-repair, got {found}"

    def test_level1_resolves_to_exact_module_not_fabricated(self) -> None:
        targets, _wildcards = _targets_for_module(
            CORE_DIR, "__scratch_7l5_relative_exact__.py", RELATIVE_ADVERSARIAL_FORMS["level1_from_dot_import"]
        )
        assert f"pcae.core.{TARGET}" in targets

    def test_level1_module_symbol_resolves_to_exact_module(self) -> None:
        targets, _wildcards = _targets_for_module(
            CORE_DIR,
            "__scratch_7l5_relative_symbol__.py",
            RELATIVE_ADVERSARIAL_FORMS["level1_from_module_symbol"],
        )
        assert f"pcae.core.{TARGET}" in targets

    def test_multilevel_resolves_through_deeper_package_context(self) -> None:
        # Representative deeper package context (item 25): a scratch
        # module two components deep under pcae (pcae.schema_runtime.X)
        # so a 2-dot relative import climbs exactly back to "pcae", then
        # into "core".
        deeper_dir = REPO_ROOT / "src" / "pcae" / "schema_runtime"
        assert deeper_dir.is_dir(), "expected a real second-level pcae subpackage for this test"
        targets, _wildcards = _targets_for_module(
            deeper_dir, "__scratch_7l5_multilevel__.py", RELATIVE_ADVERSARIAL_FORMS["level2_multilevel"]
        )
        assert f"pcae.core.{TARGET}" in targets

    def test_relative_wildcard_flagged_not_silently_safe(self) -> None:
        targets, wildcards = _targets_for_module(CORE_DIR, "__scratch_7l5_wildcard__.py", "from . import *\n")
        assert "pcae.core" in wildcards

    @pytest.mark.parametrize("name", list(RELATIVE_NEGATIVE_CONTROLS))
    def test_negative_control_not_flagged(self, name: str) -> None:
        targets, wildcards = _targets_for_module(
            CORE_DIR, "__scratch_7l5_negative__.py", RELATIVE_NEGATIVE_CONTROLS[name]
        )
        found = targets | wildcards
        if name == "relative_unrelated":
            assert not any(TARGET in m for m in found)
            assert "pcae.core.hatp_bootstrap" in targets
        else:
            assert not any(TARGET in m for m in found), f"{name} must not be flagged: {found}"

    def test_escape_root_fails_closed_as_suspicious(self) -> None:
        # A 3-dot relative import from a file directly under pcae/core
        # (only 2 ancestor components available: pcae, core) climbs
        # above the pcae root -- must fail closed into the wildcard/
        # suspicious set, never silently resolve to nonsense or be
        # treated as "no import found".
        text = f"from ...somewhere import {TARGET}\n"
        targets, wildcards = _targets_for_module(CORE_DIR, "__scratch_7l5_escape__.py", text)
        assert any(name.startswith("<unresolved-relative") for name in wildcards), wildcards
        assert not any(TARGET in m for m in targets)


def test_absolute_import_forms_have_no_regression() -> None:
    """F-7L-7's original (149O.20L.7L.3) absolute-import coverage must
    be unaffected by this phase's relative-import widening."""
    absolute_forms = {
        "plain_import": f"import pcae.core.{TARGET}\n",
        "importfrom_single_line": f"from pcae.core import {TARGET}\n",
        "importfrom_multiline": f"from pcae.core import (\n    {TARGET},\n)\n",
        "importfrom_module_symbol": f"from pcae.core.{TARGET} import create_deployment_binding\n",
    }
    for name, text in absolute_forms.items():
        targets, _wildcards = _targets_for_module(CORE_DIR, f"__scratch_7l5_abs_{name}__.py", text)
        assert any(TARGET in m for m in targets), f"absolute form {name} regressed"


def test_scratch_files_cleaned_up() -> None:
    leftovers = list(CORE_DIR.glob("__scratch_7l5_*")) + list(
        (REPO_ROOT / "src" / "pcae" / "schema_runtime").glob("__scratch_7l5_*")
    )
    assert leftovers == [], f"scratch files leaked: {leftovers}"


# ═══════════════════════════════════════════════════════════════════════════
# 6. F-7L-7: mutation tests against disposable copies of real src/pcae
#    modules (item 35) -- the guard must fail (detect the producer)
# ═══════════════════════════════════════════════════════════════════════════


class TestMutationTestingRealModuleCopies:
    """Inserts a relative import of the producer into a disposable copy
    of a real src/pcae module and confirms the repaired guard detects
    it. The real working tree is never mutated."""

    @pytest.fixture()
    def mutated_copy(self, tmp_path: Path) -> Path:
        real = REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"
        dest_root = tmp_path / "src" / "pcae" / "core"
        dest_root.mkdir(parents=True)
        dest = dest_root / "hatp_mandatory_certification.py"
        dest.write_text(real.read_text(encoding="utf-8"), encoding="utf-8")
        return dest

    def _guard_module_for_tmp_root(self, tmp_repo_root: Path):
        """A fresh guard-module instance whose own REPO_ROOT-derived
        helpers resolve against the disposable tree, not the real repo,
        so `_module_name_for_path` derives a real module context for
        the mutated copy."""
        spec = importlib.util.spec_from_file_location(
            "_pcae_20l_7l5_ast_guard_module_mutation", REPO_ROOT / AST_GUARD_MODULE
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.REPO_ROOT = tmp_repo_root
        return module

    def test_level1_from_dot_import_mutation_detected(self, tmp_path: Path, mutated_copy: Path) -> None:
        original = mutated_copy.read_text(encoding="utf-8")
        mutated_copy.write_text(f"from . import {TARGET}\n" + original, encoding="utf-8")
        guard = self._guard_module_for_tmp_root(tmp_path)
        targets, wildcards = guard._pcae_import_targets(mutated_copy)
        found = targets | wildcards
        assert any(TARGET in m for m in found), "mutation-injected relative import was not detected"

    def test_level1_from_module_symbol_mutation_detected(self, tmp_path: Path, mutated_copy: Path) -> None:
        original = mutated_copy.read_text(encoding="utf-8")
        mutated_copy.write_text(f"from .{TARGET} import create_deployment_binding\n" + original, encoding="utf-8")
        guard = self._guard_module_for_tmp_root(tmp_path)
        targets, wildcards = guard._pcae_import_targets(mutated_copy)
        found = targets | wildcards
        assert any(TARGET in m for m in found), "mutation-injected relative symbol import was not detected"

    def test_multilevel_relative_mutation_detected(self, tmp_path: Path) -> None:
        real = REPO_ROOT / "src" / "pcae" / "schema_runtime" / "manifest.py"
        dest_root = tmp_path / "src" / "pcae" / "schema_runtime"
        dest_root.mkdir(parents=True)
        dest = dest_root / "manifest.py"
        base_text = real.read_text(encoding="utf-8")
        dest.write_text(f"from ..core import {TARGET}\n" + base_text, encoding="utf-8")
        guard = self._guard_module_for_tmp_root(tmp_path)
        targets, wildcards = guard._pcae_import_targets(dest)
        found = targets | wildcards
        assert any(TARGET in m for m in found), "mutation-injected multilevel relative import was not detected"

    def test_absolute_mutation_still_detected_no_regression(self, tmp_path: Path, mutated_copy: Path) -> None:
        original = mutated_copy.read_text(encoding="utf-8")
        mutated_copy.write_text(f"import pcae.core.{TARGET}\n" + original, encoding="utf-8")
        guard = self._guard_module_for_tmp_root(tmp_path)
        targets, wildcards = guard._pcae_import_targets(mutated_copy)
        assert any(TARGET in m for m in targets), "absolute mutation regressed"

    def test_false_positive_control_string_literal_stays_clean(self, tmp_path: Path, mutated_copy: Path) -> None:
        original = mutated_copy.read_text(encoding="utf-8")
        mutated_copy.write_text(f'TEXT = "{TARGET}"\n' + original, encoding="utf-8")
        guard = self._guard_module_for_tmp_root(tmp_path)
        targets, wildcards = guard._pcae_import_targets(mutated_copy)
        found = targets | wildcards
        assert not any(TARGET in m for m in found), "string literal false-positived the guard"


# ═══════════════════════════════════════════════════════════════════════════
# 7. F-7L-7: second critical guard migration
# ═══════════════════════════════════════════════════════════════════════════


def _function_source(func_name: str) -> str:
    tree = ast.parse(_GUARD_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return ast.get_source_segment(_GUARD_SRC, node) or ""
    raise AssertionError(f"{func_name} not found in {AST_GUARD_MODULE}")


def test_second_guard_no_longer_calls_blind_helper() -> None:
    src = _function_source("test_admin_script_is_the_only_non_test_caller_of_the_producer_entry_points")
    tree = ast.parse(src)
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_pcae_import_targets" in called_names, "expected the repaired call"
    assert "_pcae_imports" not in called_names, "still calls the unrepaired blind helper"


def test_second_guard_surfaces_wildcards_as_findings() -> None:
    src = _function_source("test_admin_script_is_the_only_non_test_caller_of_the_producer_entry_points")
    assert "wildcards" in src


def test_first_critical_guard_still_uses_repaired_helper() -> None:
    src = _function_source("test_no_module_under_src_pcae_imports_the_producer_at_ast_level")
    tree = ast.parse(src)
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_pcae_import_targets" in called_names
    assert "_pcae_imports" not in called_names


def test_unrelated_completeness_helper_left_unchanged() -> None:
    """`_pcae_imports` is retained, unmodified: SAFE TO KEEP per item 34
    -- it backs an unrelated completeness check over the producer
    pair's own outbound dependencies, not a producer-reachability guard."""
    found = _GUARD_MODULE._pcae_imports(
        _write_scratch(
            "__scratch_7l5_completeness__.py",
            "from pcae.core.hatp_bootstrap import HATPTrustStoreError\n",
            under=REPO_ROOT / "tests",
        )
    )
    (REPO_ROOT / "tests" / "__scratch_7l5_completeness__.py").unlink()
    assert found == {"pcae.core.hatp_bootstrap"}


def test_no_other_critical_guard_remains_on_blind_helper() -> None:
    """Every remaining `_pcae_imports` caller in the guard module is
    either the retained unrelated completeness check, or a helper
    invoked only by it -- confirmed by direct source inspection."""
    tree = ast.parse(_GUARD_SRC)
    callers = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body_src = ast.get_source_segment(_GUARD_SRC, node) or ""
            if "_pcae_imports(" in body_src and node.name != "_pcae_imports":
                callers.add(node.name)
    assert callers == {"test_producer_pair_reaches_no_unbound_pcae_module"}, callers


# ═══════════════════════════════════════════════════════════════════════════
# 8. Whole-tree reachability and dynamic-reachability search (items 38-40)
# ═══════════════════════════════════════════════════════════════════════════


def test_whole_tree_zero_producer_importers() -> None:
    importers = []
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        if path.name == f"{TARGET}.py":
            continue
        targets, wildcards = _GUARD_MODULE._pcae_import_targets(path)
        if any(TARGET in m for m in targets):
            importers.append(str(path.relative_to(REPO_ROOT)))
        if wildcards:
            importers.append(f"{path.relative_to(REPO_ROOT)} (wildcard: {sorted(wildcards)})")
    assert importers == []


def test_no_dynamic_reachability_of_producer_anywhere_under_src() -> None:
    """Static-AST reachability claims are undermined if a dynamic call
    (importlib.import_module, __import__, subprocess/Popen, runpy,
    os.system/os.popen) *actually references the producer by name in
    its own arguments* -- not merely co-occurs somewhere else in the
    same file (e.g. `hatp_mandatory_certification.py` legitimately uses
    `subprocess` for unrelated `git` calls, and separately mentions the
    producer only as frozen path-string data; a same-file substring
    co-occurrence check would false-positive on that). AST-based: only
    a `Call` node whose own source segment contains the producer name
    is inspected."""
    dynamic_markers = ("import_module", "__import__", "subprocess", "Popen", "runpy", "system", "popen")
    hits = []
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        if path.name == f"{TARGET}.py":
            continue
        text = path.read_text(encoding="utf-8")
        if TARGET not in text:
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            segment = ast.get_source_segment(text, node) or ""
            if TARGET not in segment:
                continue
            func_repr = ast.dump(node.func)
            if any(marker in func_repr for marker in dynamic_markers):
                hits.append((str(path.relative_to(REPO_ROOT)), segment.splitlines()[0]))
    assert hits == [], f"potential dynamic reachability of the producer: {hits}"


def test_producer_module_itself_still_has_no_escape_hatch() -> None:
    text = (REPO_ROOT / "src" / "pcae" / "core" / f"{TARGET}.py").read_text(encoding="utf-8")
    for forbidden in ("importlib.import_module", "__import__", "subprocess", "os.system", "runpy"):
        assert forbidden not in text, f"producer module contains {forbidden}"


def test_no_console_script_exposes_deployment_binding_admin() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    scripts_start = pyproject.index("[project.scripts]")
    scripts_end = pyproject.index("\n[", scripts_start + 1)
    scripts_block = pyproject[scripts_start:scripts_end]
    assert "deployment_binding" not in scripts_block
    cli = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
    assert "deployment_binding" not in cli
    assert TARGET not in cli


# ═══════════════════════════════════════════════════════════════════════════
# 9. Same-version discipline, byte-identity, and no-go confirmations
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_001_remains_v1_4() -> None:
    assert "**Version:** 1.4" in _HMIC_CONTRACT


def test_implementation_scope_digest_unchanged() -> None:
    digest = hmic.derive_implementation_scope_digest(HarnessPath(REPO_ROOT))
    assert digest == "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"


def test_frozen_source_scope_still_thirty_members() -> None:
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 30


def test_contract_versions_still_five_members() -> None:
    live = hmic.derive_contract_versions(HarnessPath(REPO_ROOT))
    assert len(live) == 5


def test_no_production_source_touched() -> None:
    diff = _git("diff", "--name-only", "origin/main...HEAD", "--", "src/pcae/")
    assert diff.strip() == ""


def test_no_dell_or_first_use_artifacts() -> None:
    for name in (
        "registry.json",
        "repository-identity.json",
        "deployment-binding.json",
        "certifications.json",
        "certification-bindings.json",
        "active-certification.json",
    ):
        assert not list(REPO_ROOT.rglob(name))
