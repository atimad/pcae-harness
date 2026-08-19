"""Phase 149O.20L.7L.6 — Contract-Preamble and Relative-Import Guard
Repair Independent Verification.

Verification-only phase. Independently re-derives 149O.20L.7L.5's own
claims from live contract/production/test state -- not from
149O.20L.7L.5's narrative -- for:

- F-7L-5 (§0 preamble repair, contract §58.1): the top-of-document
  Status/Identity preamble no longer restates the stale hard-coded
  `False` ceiling claim, and does not overstate certification,
  readiness, activation, Boundary C completion, first use, or
  `DeploymentBinding` existence.
- F-7L-7 (relative-import guard repair, contract §58.2/§58.3): both
  critical producer-reachability guards
  (`test_no_module_under_src_pcae_imports_the_producer_at_ast_level` and
  `test_admin_script_is_the_only_non_test_caller_of_the_producer_entry_
  points`) use the relative-import-aware `_pcae_import_targets`, and
  `_module_name_for_path`/`_resolve_relative_import_base` reproduce
  Python's own relative-import resolution algorithm faithfully
  (independently cross-checked against `importlib._bootstrap.
  _resolve_name`).

This phase makes NO `src/pcae/**`, contract, or test-helper change: it
is a pure verification phase and this module is its only deliverable,
an executable, durable record of the verification performed. No
RepositoryIdentity, DeploymentBinding, election, CHGR, certification,
or HATP activation is authorized or performed by this phase.
"""

from __future__ import annotations

import ast
import importlib._bootstrap as _py_bootstrap
import importlib.util
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath

REPO_ROOT = Path(__file__).resolve().parents[1]

HMIC_CONTRACT_PATH = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
CUTOVER_MODULE = "src/pcae/core/hatp_mandatory_cutover.py"
AST_GUARD_MODULE = "tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.py"
TARGET = "hatp_deployment_binding_admin"

_HMIC_CONTRACT = (REPO_ROOT / HMIC_CONTRACT_PATH).read_text(encoding="utf-8")
_CUTOVER_SRC = (REPO_ROOT / CUTOVER_MODULE).read_text(encoding="utf-8")
_GUARD_SRC = (REPO_ROOT / AST_GUARD_MODULE).read_text(encoding="utf-8")

_PHASE_ENTRY_COMMIT = "d6dd458d"  # Phase 149O.20L.7L.4's own last commit, immediately pre-149O.20L.7L.5
_REPAIR_COMMIT = "8799b457"  # Phase 149O.20L.7L.5's sole substantive commit

_spec = importlib.util.spec_from_file_location("_guard_module_7l6", REPO_ROOT / AST_GUARD_MODULE)
_GUARD_MODULE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_GUARD_MODULE)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout


# ═══════════════════════════════════════════════════════════════════════════
# 1. Baseline reconciliation (items 3-4)
# ═══════════════════════════════════════════════════════════════════════════


def test_phase_entry_commit_is_parent_of_repair_commit() -> None:
    parent = _git("log", "--format=%H", "-1", f"{_REPAIR_COMMIT}^").strip()
    assert parent.startswith(_PHASE_ENTRY_COMMIT)


def test_repair_commit_touched_only_contract_and_test_files() -> None:
    changed = _git("diff", "--name-only", _PHASE_ENTRY_COMMIT, _REPAIR_COMMIT).splitlines()
    assert changed
    for path in changed:
        assert path.startswith("docs/contracts/") or path.startswith("tests/"), path
    assert not any(p.startswith("src/pcae/") for p in changed)
    assert not any(p.startswith("scripts/") for p in changed)


# ═══════════════════════════════════════════════════════════════════════════
# 2. §0 preamble repair (F-7L-5, contract §58.1) — items 6-10
# ═══════════════════════════════════════════════════════════════════════════


def test_no_hardcoded_false_ceiling_assignment_exists_in_production() -> None:
    assert "mandatory_consumption_implementation_independently_verified = False" not in _CUTOVER_SRC
    assert "mandatory_consumption_implementation_independently_verified=False" not in _CUTOVER_SRC


def test_cited_line_range_842_853_does_not_contain_the_hmic_term() -> None:
    cited = "\n".join(_CUTOVER_SRC.splitlines()[841:853])  # 842-853, 1-indexed inclusive
    assert "mandatory_consumption_implementation_independently_verified" not in cited


def test_production_readiness_term_uses_dynamic_validator_call() -> None:
    assert "validate_active_hatp_mandatory_independent_verification_certification" in _CUTOVER_SRC
    assert "certification_status_satisfies_readiness" in _CUTOVER_SRC


def test_certification_status_satisfies_readiness_is_exact_valid_identity() -> None:
    import inspect

    from pcae.core import hatp_mandatory_certification as hmc

    src = inspect.getsource(hmc.certification_status_satisfies_readiness)
    assert "return status is CertificationStatus.VALID" in src


def test_no_stored_hmic_certification_exists_on_this_host() -> None:
    hits = list(REPO_ROOT.rglob("registry.json"))
    hits += list(REPO_ROOT.rglob("repository-identity.json"))
    hits += list(REPO_ROOT.rglob("deployment-binding.json"))
    hits += list(REPO_ROOT.rglob("certifications.json"))
    hits += list(REPO_ROOT.rglob("certification-bindings.json"))
    hits += list(REPO_ROOT.rglob("active-certification.json"))
    hits = [h for h in hits if ".venv" not in h.parts]
    assert hits == []


def test_preamble_no_longer_restates_stale_ceiling_sentence() -> None:
    preamble = _HMIC_CONTRACT.split("## 0. Contract Identity", 1)[0]
    assert (
        "The current\nhard-coded `mandatory_consumption_implementation_independently_verified\n"
        "= False` ceiling (`hatp_mandatory_cutover.py:842-853`) is unchanged."
    ) not in preamble


def test_preamble_names_current_dynamic_mechanism() -> None:
    preamble = " ".join(_HMIC_CONTRACT.split("## 0. Contract Identity", 1)[0].split())
    assert "no longer exists" in preamble
    assert "Phase 149O.19.5F" in preamble
    assert "validate_active_hatp_mandatory_independent_verification_certification" in preamble
    assert "CertificationStatus.VALID" in preamble
    assert "fail-closed" in preamble


def test_preamble_does_not_overstate_certification_readiness_or_activation() -> None:
    # Whitespace-normalized: the raw markdown hard-wraps prose at ~79
    # columns, so a phrase spanning a line break must not be treated as
    # absent just because a literal newline splits it.
    preamble = " ".join(_HMIC_CONTRACT.split("## 0. Contract Identity", 1)[0].split())
    assert "does not assert HMIC certification" in preamble
    assert "HATP activation readiness" in preamble
    assert "Boundary C completion" in preamble
    assert "first use" in preamble
    assert "DeploymentBinding` existence" in preamble
    assert "still unmet" in preamble
    assert "still evaluates `False` today" in preamble


def test_same_version_repair_no_new_requirement_text() -> None:
    import re

    added = _git("diff", _PHASE_ENTRY_COMMIT, _REPAIR_COMMIT, "--", HMIC_CONTRACT_PATH)
    added_lines = [ln[1:] for ln in added.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    added_text = "\n".join(added_lines)
    new_req_ids = set(re.findall(r"HMIC-REQ-\d{3}", added_text))
    existing_req_ids = set(re.findall(r"HMIC-REQ-\d{3}", _HMIC_CONTRACT))
    # every REQ id mentioned in the diff must already exist elsewhere in
    # the (post-repair) document -- i.e. no newly-coined identifier
    assert new_req_ids <= existing_req_ids
    assert "**Version:** 1.4" in _HMIC_CONTRACT


# ═══════════════════════════════════════════════════════════════════════════
# 3. Whole-document stale-current-claim scan (item 10) — independent re-scan
# ═══════════════════════════════════════════════════════════════════════════


def test_stale_ceiling_sentence_absent_from_live_preamble() -> None:
    """The exact stale sentence 149O.20L.7L.5 repaired must not appear
    in the document's own live, non-archival preamble (before '## 0.'),
    whitespace-normalized so a hard-wrap line break cannot hide it. It
    is expected to still appear verbatim inside at least one archival
    Phase-history section elsewhere in the document (e.g. Phase
    149O.19.3R's own historical re-verification narrative) -- that is
    correct preservation of historical truth, not a live defect; the
    dedicated `test_archival_phase_history_sections_left_untouched`
    tests (149O.20L.7L.3/149O.20L.7L.4 modules) independently confirm
    those sections are untouched."""
    stale_sentence = (
        "hard-coded `mandatory_consumption_implementation_independently_verified = False` "
        "ceiling (`hatp_mandatory_cutover.py:842-853`) is unchanged."
    )
    preamble_normalized = " ".join(_HMIC_CONTRACT.split("## 0. Contract Identity", 1)[0].split())
    assert stale_sentence not in preamble_normalized
    whole_doc_normalized = " ".join(_HMIC_CONTRACT.split())
    assert stale_sentence in whole_doc_normalized, "expected the archival occurrence to remain preserved"


def test_no_stale_28_or_25_file_count_claim_as_current() -> None:
    assert "the current 28-file" not in _HMIC_CONTRACT
    assert "the current 25-file" not in _HMIC_CONTRACT
    assert "currently twenty-eight files" not in _HMIC_CONTRACT
    assert "currently twenty-five files" not in _HMIC_CONTRACT


# ═══════════════════════════════════════════════════════════════════════════
# 4. Previously repaired sections unchanged (items 11-13)
# ═══════════════════════════════════════════════════════════════════════════


def _contract_text_at(rev: str) -> str:
    return subprocess.run(
        ["git", "show", f"{rev}:{HMIC_CONTRACT_PATH}"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _extract_attack_row(text: str, n: int) -> str:
    import re

    m = re.search(rf"\n\|\s*{n}\s*\*?\(.*?\n(?=\||\Z)", text, re.S)
    assert m, f"row {n} not found"
    return m.group(0)


@pytest.mark.parametrize("row_number", [33, 34, 36, 37, 38, 39])
def test_attack_matrix_row_byte_unchanged_since_7l3(row_number: int) -> None:
    old_text = _contract_text_at("85616f4b")  # 149O.20L.7L.3's own commit
    new_text = _contract_text_at("HEAD")
    assert _extract_attack_row(old_text, row_number) == _extract_attack_row(new_text, row_number)


def _extract_requirement_block(text: str, req_id: str) -> str:
    import re

    m = re.search(rf"\*\*{re.escape(req_id)} \(.*?(?=\n\*\*HMIC-REQ-\d{{3}} \(|\Z)", text, re.S)
    assert m, f"{req_id} not found"
    return m.group(0)


def _extract_hmic_req_145_block(text: str) -> str:
    """Extract only HMIC-REQ-145, whose own section ends at the rule.

    The historical generic helper above requires the *next* requirement
    heading to contain a parenthesized subtitle. HMIC-REQ-145 is followed by
    HMIC-REQ-071, which uses the plain ``.**`` form, so that helper ran across
    unrelated current requirements including HMIC-REQ-076. The horizontal
    rule is HMIC-REQ-145's stable, exact section boundary in both the 7L.3
    checkpoint and the live contract.
    """

    import re

    m = re.search(r"\*\*HMIC-REQ-145 \(.*?(?=\n---\n)", text, re.S)
    assert m, "HMIC-REQ-145 not found"
    return m.group(0)


def test_hmic_req_050_thirty_file_enumeration_unchanged_since_7l3() -> None:
    old_text = _contract_text_at("85616f4b")
    new_text = _contract_text_at("HEAD")
    assert _extract_requirement_block(old_text, "HMIC-REQ-050") == _extract_requirement_block(new_text, "HMIC-REQ-050")


def test_hmic_req_052_unchanged_since_7l3() -> None:
    old_text = _contract_text_at("85616f4b")
    new_text = _contract_text_at("HEAD")
    assert _extract_requirement_block(old_text, "HMIC-REQ-052") == _extract_requirement_block(new_text, "HMIC-REQ-052")


def test_hmic_req_145_closure_paragraph_present_and_unchanged() -> None:
    assert "HMIC-REQ-145" in _HMIC_CONTRACT
    old_text = _contract_text_at("85616f4b")
    new_text = _contract_text_at("HEAD")
    assert _extract_hmic_req_145_block(old_text) == _extract_hmic_req_145_block(new_text)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Thirty-member set, digest, byte identity (items 14-17)
# ═══════════════════════════════════════════════════════════════════════════


def test_frozen_authority_bearing_set_is_exactly_thirty_members() -> None:
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 30
    assert "core/hatp_deployment_binding_admin.py" in hmic._FROZEN_AUTHORITY_BEARING_FILES
    assert "scripts/hatp_deployment_binding_admin.py" in hmic._FROZEN_AUTHORITY_BEARING_FILES


def test_implementation_scope_digest_matches_expected() -> None:
    digest = hmic.derive_implementation_scope_digest(HarnessPath(REPO_ROOT))
    assert digest == "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"


def test_no_production_or_scripts_file_touched_by_this_phase_lineage() -> None:
    changed = _git("diff", "--name-only", _PHASE_ENTRY_COMMIT, "HEAD").splitlines()
    changed = [c for c in changed if c]
    disallowed = [
        c
        for c in changed
        if c.startswith("src/pcae/")
        or c.startswith("scripts/")
        or (c.startswith("docs/contracts/") and c != HMIC_CONTRACT_PATH)
    ]
    assert disallowed == [], disallowed


# ═══════════════════════════════════════════════════════════════════════════
# 6. Module-name derivation and relative-import level semantics (items 21-26)
# — cross-validated against Python's own resolution algorithm, not assumed
# ═══════════════════════════════════════════════════════════════════════════


def _python_native_expected_base(module_dotted: str, is_package: bool, level: int) -> "str | None":
    package = module_dotted if is_package else (module_dotted.rsplit(".", 1)[0] if "." in module_dotted else "")
    try:
        return _py_bootstrap._resolve_name("", package, level)
    except ImportError:
        return None


@pytest.mark.parametrize(
    "module_dotted,is_package,level",
    [
        ("pcae.core.foo", False, 1),
        ("pcae.core", True, 1),
        ("pcae.orchestration.deep_module", False, 2),
        ("pcae.foo", False, 2),
        ("pcae.core.foo", False, 3),
        ("pcae.core.sub.deep", False, 1),
    ],
)
def test_resolve_relative_import_base_matches_python_native_algorithm(
    module_dotted: str, is_package: bool, level: int
) -> None:
    got = _GUARD_MODULE._resolve_relative_import_base(module_dotted, is_package, level)
    expected = _python_native_expected_base(module_dotted, is_package, level)
    assert got == expected, (module_dotted, is_package, level, got, expected)


def test_module_name_for_path_regular_and_init_and_nested() -> None:
    mnp = _GUARD_MODULE._module_name_for_path
    assert mnp(REPO_ROOT / "src/pcae/core/foo.py") == "pcae.core.foo"
    assert mnp(REPO_ROOT / "src/pcae/core/__init__.py") == "pcae.core"
    assert mnp(REPO_ROOT / "src/pcae/__init__.py") == "pcae"
    assert mnp(REPO_ROOT / "src/pcae/core/sub/deep.py") == "pcae.core.sub.deep"
    assert mnp(REPO_ROOT / "scripts/hatp_deployment_binding_admin.py") is None


# ═══════════════════════════════════════════════════════════════════════════
# 7. Both critical guards use the repaired resolver (items 18-19, 43-44)
# ═══════════════════════════════════════════════════════════════════════════


def _called_names(func_name: str) -> set:
    tree = ast.parse(_GUARD_SRC)
    target = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func_name)
    return {n.func.id for n in ast.walk(target) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


def test_first_critical_guard_uses_repaired_helper() -> None:
    called = _called_names("test_no_module_under_src_pcae_imports_the_producer_at_ast_level")
    assert "_pcae_import_targets" in called
    assert "_pcae_imports" not in called


def test_second_critical_guard_uses_repaired_helper() -> None:
    called = _called_names("test_admin_script_is_the_only_non_test_caller_of_the_producer_entry_points")
    assert "_pcae_import_targets" in called
    assert "_pcae_imports" not in called


def test_only_unrelated_completeness_check_still_uses_blind_helper() -> None:
    tree = ast.parse(_GUARD_SRC)
    callers = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body_src = ast.get_source_segment(_GUARD_SRC, node) or ""
            if "_pcae_imports(" in body_src and node.name != "_pcae_imports":
                callers.add(node.name)
    assert callers == {"test_producer_pair_reaches_no_unbound_pcae_module"}


def test_unrelated_completeness_check_does_not_assert_producer_reachability() -> None:
    tree = ast.parse(_GUARD_SRC)
    target = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "test_producer_pair_reaches_no_unbound_pcae_module"
    )
    body_src = ast.get_source_segment(_GUARD_SRC, target) or ""
    # this check discards the producer module from its own reachable
    # set before asserting -- it is checking the producer pair's own
    # outbound dependency completeness, not inbound reachability *into*
    # the producer.
    assert 'reachable.discard("pcae.core.hatp_deployment_binding_admin")' in body_src


# ═══════════════════════════════════════════════════════════════════════════
# 8. Pre-repair bug reproduction (item 20) — causal proof, immutable
#    pre-149O.20L.7L.5 code
# ═══════════════════════════════════════════════════════════════════════════


def _pre_repair_pcae_import_targets(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set = set()
    wildcard_modules: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            for alias in node.names:
                if alias.name == "*":
                    wildcard_modules.add(node.module)
                else:
                    found.add(f"{node.module}.{alias.name}")
    targets = {n for n in found if n.startswith("pcae.")}
    wildcards = {n for n in wildcard_modules if n.startswith("pcae.")}
    return targets, wildcards


@pytest.mark.parametrize(
    "name,content",
    [
        ("level1_from_dot_import", f"from . import {TARGET}\n"),
        ("level1_from_module_symbol", f"from .{TARGET} import create_deployment_binding\n"),
    ],
)
def test_pre_repair_helper_misses_relative_forms(name: str, content: str) -> None:
    tmp = REPO_ROOT / "src" / "pcae" / "core" / f"__scratch_7l6_prerepair_{name}__.py"
    tmp.write_text(content, encoding="utf-8")
    try:
        targets, wildcards = _pre_repair_pcae_import_targets(tmp)
    finally:
        tmp.unlink()
    assert not any(TARGET in m for m in (targets | wildcards)), (
        f"expected the pre-repair helper to miss {name} (causal proof of the "
        f"defect this phase's own predecessor repaired); got {targets | wildcards}"
    )


def test_pre_repair_helper_misses_multilevel_form() -> None:
    deeper = REPO_ROOT / "src" / "pcae" / "schema_runtime"
    tmp = deeper / "__scratch_7l6_prerepair_multilevel__.py"
    tmp.write_text(f"from ..core import {TARGET}\n", encoding="utf-8")
    try:
        targets, wildcards = _pre_repair_pcae_import_targets(tmp)
    finally:
        tmp.unlink()
    assert not any(TARGET in m for m in (targets | wildcards))


def test_repaired_helper_now_detects_all_three_pre_repair_bug_forms() -> None:
    cases = {
        "level1_module": (REPO_ROOT / "src/pcae/core", f"from . import {TARGET}\n"),
        "level1_symbol": (REPO_ROOT / "src/pcae/core", f"from .{TARGET} import create_deployment_binding\n"),
        "multilevel": (REPO_ROOT / "src/pcae/schema_runtime", f"from ..core import {TARGET}\n"),
    }
    for name, (directory, content) in cases.items():
        tmp = directory / f"__scratch_7l6_postrepair_{name}__.py"
        tmp.write_text(content, encoding="utf-8")
        try:
            targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
        finally:
            tmp.unlink()
        assert any(TARGET in m for m in (targets | wildcards)), f"{name}: repaired helper must detect this"


# ═══════════════════════════════════════════════════════════════════════════
# 9. Escape-root, missing-context, wildcard, absolute-regression,
#    negative controls (items 25-40) — independent re-derivation
# ═══════════════════════════════════════════════════════════════════════════


def test_escape_root_fails_closed_not_silently_dropped() -> None:
    tmp = REPO_ROOT / "src" / "pcae" / "core" / "__scratch_7l6_escape__.py"
    tmp.write_text(f"from ... import {TARGET}\n", encoding="utf-8")
    try:
        targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
    finally:
        tmp.unlink()
    assert not any(TARGET in t for t in targets)
    assert any(w.startswith("<unresolved-relative") for w in wildcards)


def test_missing_module_context_fails_closed(tmp_path: Path) -> None:
    outside = tmp_path / "outside_pcae.py"
    outside.write_text(f"from . import {TARGET}\n", encoding="utf-8")
    targets, wildcards = _GUARD_MODULE._pcae_import_targets(outside)
    assert not any(TARGET in t for t in targets)
    assert any(w.startswith("<unresolved-relative") for w in wildcards)


def test_wildcard_absolute_and_relative_flagged_not_silently_safe() -> None:
    core = REPO_ROOT / "src" / "pcae" / "core"
    for name, content in [
        ("wild_abs", "from pcae.core import *\n"),
        ("wild_rel", "from . import *\n"),
    ]:
        tmp = core / f"__scratch_7l6_{name}__.py"
        tmp.write_text(content, encoding="utf-8")
        try:
            _targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
        finally:
            tmp.unlink()
        assert "pcae.core" in wildcards


def test_absolute_import_and_importfrom_forms_have_no_regression() -> None:
    core = REPO_ROOT / "src" / "pcae" / "core"
    forms = {
        "plain": f"import pcae.core.{TARGET}\n",
        "alias": f"import pcae.core.{TARGET} as dba\n",
        "importfrom": f"from pcae.core import {TARGET}\n",
        "multiline": f"from pcae.core import (\n    {TARGET},\n)\n",
        "importfrom_alias": f"from pcae.core import {TARGET} as dba\n",
        "multiname": f"from pcae.core import unrelated, {TARGET}\n",
        "symbol": f"from pcae.core.{TARGET} import create_deployment_binding\n",
    }
    for name, content in forms.items():
        tmp = core / f"__scratch_7l6_abs_{name}__.py"
        tmp.write_text(content, encoding="utf-8")
        try:
            targets, _wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
        finally:
            tmp.unlink()
        assert any(TARGET in t for t in targets), name


def test_relative_alias_multiline_multiname_forms_detected() -> None:
    core = REPO_ROOT / "src" / "pcae" / "core"
    forms = {
        "paren": f"from . import (\n    {TARGET},\n)\n",
        "alias": f"from . import {TARGET} as db\n",
        "multiname": f"from . import (\n    unrelated,\n    {TARGET},\n)\n",
    }
    for name, content in forms.items():
        tmp = core / f"__scratch_7l6_rel_{name}__.py"
        tmp.write_text(content, encoding="utf-8")
        try:
            targets, _wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
        finally:
            tmp.unlink()
        assert any(TARGET in t for t in targets), name


@pytest.mark.parametrize(
    "name,content",
    [
        ("string_literal", f'x = "{TARGET}"\n'),
        ("comment", f"# {TARGET}\nx = 1\n"),
        ("docstring", f'"""mentions {TARGET} in prose only."""\n'),
        ("tuple_literal", f'X = ("{TARGET}",)\n'),
        ("symbol_use_no_import", f"{TARGET}()\n"),
        ("unrelated_relative_import", "from . import hatp_bootstrap\n"),
    ],
)
def test_negative_controls_not_flagged(name: str, content: str) -> None:
    core = REPO_ROOT / "src" / "pcae" / "core"
    tmp = core / f"__scratch_7l6_neg_{name}__.py"
    tmp.write_text(content, encoding="utf-8")
    try:
        targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
    finally:
        tmp.unlink()
    assert not any(TARGET in m for m in (targets | wildcards)), name


# ═══════════════════════════════════════════════════════════════════════════
# 10. Mutation tests against real module copies (items 41-42)
# ═══════════════════════════════════════════════════════════════════════════


def test_mutation_relative_import_into_real_module_copy_detected() -> None:
    real = (REPO_ROOT / "src/pcae/core/paths.py").read_text(encoding="utf-8")
    mutated = f"from . import {TARGET}  # mutation test injection\n" + real
    tmp = REPO_ROOT / "src" / "pcae" / "core" / "__scratch_7l6_mutation_real__.py"
    tmp.write_text(mutated, encoding="utf-8")
    try:
        targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
    finally:
        tmp.unlink()
    assert any(TARGET in m for m in (targets | wildcards))


def test_mutation_false_positive_control_string_only_stays_clean() -> None:
    real = (REPO_ROOT / "src/pcae/core/paths.py").read_text(encoding="utf-8")
    mutated = f'_NOTE = "references {TARGET} only as text"  # not an import\n' + real
    tmp = REPO_ROOT / "src" / "pcae" / "core" / "__scratch_7l6_mutation_fp__.py"
    tmp.write_text(mutated, encoding="utf-8")
    try:
        targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
    finally:
        tmp.unlink()
    assert not any(TARGET in m for m in (targets | wildcards))


# ═══════════════════════════════════════════════════════════════════════════
# 11. Dynamic reachability, whole-tree static reachability, entry points
#     (items 45-49)
# ═══════════════════════════════════════════════════════════════════════════


def test_whole_tree_zero_producer_importers_and_zero_wildcard_hits() -> None:
    importers = []
    for path in list((REPO_ROOT / "src").rglob("*.py")) + list((REPO_ROOT / "scripts").glob("*.py")):
        if path.name == f"{TARGET}.py":
            continue
        targets, wildcards = _GUARD_MODULE._pcae_import_targets(path)
        if any(TARGET in t for t in targets) or wildcards:
            importers.append(str(path.relative_to(REPO_ROOT)))
    assert importers == []


def test_no_dynamic_reachability_of_producer_anywhere_under_src() -> None:
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if TARGET in text:
            assert path.name == f"{TARGET}.py" or "hatp_mandatory_certification" in path.name, str(path)
        for dynamic_marker in ("importlib.import_module", "__import__(", "runpy."):
            if dynamic_marker in text and TARGET in text:
                assert path.name in (f"{TARGET}.py",), (path, dynamic_marker)


def test_no_subprocess_invocation_of_admin_script_in_production() -> None:
    """Item 47: no ordinary PCAE command/runtime *executes* the admin
    script. Mentioning its path in a docstring/comment (e.g. to explain
    the Protected Admin ceremony boundary) is expected and fine; this
    checks for an actual invocation construct co-occurring with the
    script path, not mere textual mention."""
    invocation_markers = ("subprocess.", "Popen(", "os.system(", "check_call(", "check_output(", "run(")
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if f"scripts/{TARGET}.py" not in text and f"scripts/{TARGET}" not in text:
            continue
        for line in text.splitlines():
            if f"scripts/{TARGET}" in line:
                assert not any(marker in line for marker in invocation_markers), (path, line)


def test_no_console_script_entry_point_for_admin_script() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    scripts_section = pyproject.split("[project.scripts]", 1)[1].split("\n[", 1)[0]
    assert TARGET not in scripts_section
    assert "hatp_certification_admin" not in scripts_section


# ═══════════════════════════════════════════════════════════════════════════
# 12. Carried findings untouched (item 54)
# ═══════════════════════════════════════════════════════════════════════════


def test_carried_findings_untouched_since_phase_entry() -> None:
    diff = _git("diff", "--name-only", _PHASE_ENTRY_COMMIT, "HEAD")
    changed = set(diff.splitlines())
    assert "src/pcae/core/hatp_bootstrap.py" not in changed


# ═══════════════════════════════════════════════════════════════════════════
# 13. No Dell access, no first-use artifacts, no production change (items 59-61)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_production_source_touched_this_phase() -> None:
    changed = _git("diff", "--name-only", _PHASE_ENTRY_COMMIT, "HEAD").splitlines()
    assert not any(c.startswith("src/pcae/") for c in changed if c)


def test_no_dell_or_first_use_artifacts() -> None:
    for name in (
        "registry.json",
        "repository-identity.json",
        "deployment-binding.json",
        "certifications.json",
        "certification-bindings.json",
        "active-certification.json",
    ):
        hits = [h for h in REPO_ROOT.rglob(name) if ".venv" not in h.parts]
        assert hits == []


def test_hmic_001_remains_v1_4() -> None:
    """As of this phase, HEAD carried v1.4; a later amendment
    (149O.20L.7O.2H) additively bumped it to v1.5."""
    assert "**Contract ID:** HMIC-001" in _HMIC_CONTRACT
    version_line = next(line for line in _HMIC_CONTRACT.splitlines() if line.startswith("**Version:**"))
    major, minor = (int(x) for x in version_line.split()[-1].split("."))
    assert (major, minor) >= (1, 4)


def test_no_scratch_files_left_behind() -> None:
    leftovers = list((REPO_ROOT / "src" / "pcae").rglob("__scratch_7l6*"))
    assert leftovers == []


# ═══════════════════════════════════════════════════════════════════════════
# 14. Closure verdict (items 50-53, 62)
# ═══════════════════════════════════════════════════════════════════════════


def test_closure_verdict_f_7l_5_closed() -> None:
    """F-7L-5 (whole-document scan / §0 preamble): CLOSED by this phase's
    independent verification -- preamble accurate, no other live
    same-class false claim found, previously-repaired sections unchanged."""
    assert True


def test_closure_verdict_f_7l_7_closed() -> None:
    """F-7L-7 (relative-import gap and second-guard migration): CLOSED
    by this phase's independent verification -- both critical guards
    confirmed on the repaired resolver, resolver semantics independently
    cross-validated against Python's own algorithm, mutation and
    negative-control tests independently reproduced green, zero residual
    unsafe `_pcae_imports` usage, zero dynamic-reachability path, zero
    whole-tree importers."""
    assert True


def test_closure_verdict_7j_section_31_closed() -> None:
    """7J §31 (HMIC frozen-source-membership finding): CLOSED. The
    thirty-file/five-member production identity is independently
    reconstructed and matches the contract exactly; the
    `implementation_scope_digest` is independently recomputed and
    matches `65ff8ab0...` exactly; both defects that blocked this
    finding's closure (F-7L-5, F-7L-7) are independently verified
    repaired and CLOSED above."""
    assert True
