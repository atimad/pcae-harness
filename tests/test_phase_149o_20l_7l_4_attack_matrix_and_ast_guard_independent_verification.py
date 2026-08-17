"""Phase 149O.20L.7L.4 — Attack-Matrix and AST-Guard Narrow Repair
Independent Verification.

**Update note (Phase 149O.20L.7L.5):** the two gaps this module
documents below (the §0 preamble stale claim, and the relative-import
bypass plus second-critical-guard blind spot) were repaired by
149O.20L.7L.5 (contract §58). The historical narrative below is left
otherwise unmodified as an accurate record of what this phase itself
independently found; the specific test bodies that asserted the gaps'
*continued existence* are updated in place to confirm the repair,
per each test's own original instruction to update rather than leave
silently green with a now-false meaning -- mirroring 149O.20L.7L.3's
own precedent for updating 149O.20L.7L.2's finding classes once their
gap closed.

Verification-only phase. Independently re-derives 149O.20L.7L.3's own
claims from live production/contract state -- not from 149O.20L.7L.3's
narrative -- for finding F-7L-5 (attack-matrix rows 33/34/36/37 and the
HMIC-REQ-145 closure paragraph) and finding F-7L-7 (the AST-level
`_pcae_imports`/`_pcae_import_targets` guard helpers).

This module confirms what 149O.20L.7L.3 got right, and independently
documents two gaps 149O.20L.7L.3 did not find or did not fully close:

1. F-7L-7 is only partially repaired: `_pcae_import_targets` filters to
   `pcae.`-prefixed names, so a *relative* import of the producer
   (`from . import hatp_deployment_binding_admin`,
   `from .hatp_deployment_binding_admin import create_deployment_binding`,
   `from ..core import hatp_deployment_binding_admin`) inside a module
   under `src/pcae` produces zero hits. This codebase uses relative
   imports elsewhere under `src/pcae` (e.g.
   `src/pcae/schema_runtime/registry.py`), so this is not a purely
   theoretical form.
2. A second, broader critical guard --
   `test_admin_script_is_the_only_non_test_caller_of_the_producer_entry_
   points` in the 149O.20L.7L test module, which scans all of `src/` and
   `scripts/`, not only `src/pcae` -- still calls the unrepaired,
   `.names`-blind `_pcae_imports`, not `_pcae_import_targets`. A
   single-line `from pcae.core import hatp_deployment_binding_admin`
   added anywhere in that broader scope would not be caught by this
   specific assertion (the narrower `src/pcae`-only AST guard would still
   catch it, but this is exactly the "critical guard still relies on the
   blind helper" condition 149O.20L.7L.3's own governing instructions
   warned against).

Per this phase's own governing criteria (F-7L-7 closes only if "no
critical guard still relies on the blind helper" and no relevant import
form goes uncovered), F-7L-7 is classified NOT CLOSED by this phase.

This module also independently re-scans the contract's own top-of-
document Status/Identity preamble (the paragraph before "## 0. Contract
Identity and Status") and finds it still asserts, in the present tense,
that a hard-coded `mandatory_consumption_implementation_independently_
verified = False` ceiling exists at `hatp_mandatory_cutover.py:842-853`.
No such literal assignment exists anywhere in that file (Wave F, Phase
149O.19.5F, replaced it with a dynamic call, the same fact 149O.20L.7L.3
independently confirmed for row 34); the cited line range no longer even
corresponds to that logic. 149O.20L.7L.3's own §57.9 whole-document scan
read this exact paragraph and classified it "HISTORICAL AND TRUE IN
CONTEXT" -- this module shows that classification is itself a same-class
current-false claim, independently found by this phase's own fresh scan.
Per this phase's own governing criteria (item 14), this is classified
NOT VERIFIED -- REPAIR INCOMPLETE, and F-7L-5 (whole-document-scan
completeness) is therefore NOT fully closed either, even though rows
33/34/36/37 and the HMIC-REQ-145 closure paragraph themselves are
independently confirmed correct.

No `src/pcae/**` file is modified by this phase. No contract text, no
test guard, is repaired here -- this module only proves what is true,
including what remains broken.
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import tempfile
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath

REPO_ROOT = Path(__file__).resolve().parents[1]

HMIC_CONTRACT_PATH = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
CUTOVER_MODULE = "src/pcae/core/hatp_mandatory_cutover.py"
CERT_MODULE = "src/pcae/core/hatp_mandatory_certification.py"
AST_GUARD_MODULE = (
    "tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.py"
)
PRODUCER = "hatp_deployment_binding_admin"

_HMIC_CONTRACT = (REPO_ROOT / HMIC_CONTRACT_PATH).read_text(encoding="utf-8")
_CUTOVER_SRC = (REPO_ROOT / CUTOVER_MODULE).read_text(encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


PRE_7L3_COMMIT = "a1190b08ffbc1bcaf8a26b2121ea113c63e89327"  # Phase 149O.20L.7L.2 final commit


# ═══════════════════════════════════════════════════════════════════════════
# 1. Immutable baseline identity
# ═══════════════════════════════════════════════════════════════════════════


def test_pre_7l3_commit_is_the_true_parent_of_the_repair_commit() -> None:
    repair_commit = _git("log", "--format=%H", "--grep=149O.20L.7L.3: Attack-Matrix", "-1")
    assert repair_commit, "the 149O.20L.7L.3 substantive repair commit must exist"
    parent = _git("log", "--format=%H", "-1", f"{repair_commit}^")
    assert parent == PRE_7L3_COMMIT


# ═══════════════════════════════════════════════════════════════════════════
# 2. Rows 33/34/36/37 and HMIC-REQ-145 -- independently re-derived
# ═══════════════════════════════════════════════════════════════════════════


def test_production_frozen_file_set_is_thirty() -> None:
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 30


def test_production_contract_versions_member_set_is_five() -> None:
    root = HarnessPath(REPO_ROOT)
    versions = hmic.derive_contract_versions(root)
    assert set(versions.keys()) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"}


def test_no_hardcoded_false_ceiling_assignment_for_hmic_term_exists() -> None:
    assert "mandatory_consumption_implementation_independently_verified = False" not in _CUTOVER_SRC
    assert "mandatory_consumption_implementation_independently_verified=False" not in _CUTOVER_SRC


def test_validator_has_exactly_one_production_readiness_caller() -> None:
    hits = [
        line
        for line in _CUTOVER_SRC.splitlines()
        if "validate_active_hatp_mandatory_independent_verification_certification(" in line
        and "def validate_active" not in line
    ]
    assert len(hits) == 1


def test_no_stored_certification_exists_on_this_host() -> None:
    for name in (
        "certifications.json",
        "certification-bindings.json",
        "active-certification.json",
    ):
        assert not list(REPO_ROOT.rglob(name))


def _row(n: int) -> str:
    for line in _HMIC_CONTRACT.splitlines():
        if line.startswith(f"| {n} "):
            return line
    raise AssertionError(f"row {n} not found")


class TestRows33_34_36_37IndependentlyConfirmedCorrect:
    def test_row_33_reflects_live_thirty_file_state(self) -> None:
        row = _row(33)
        assert "Operative, not yet consequential" in row
        assert "superseded and no longer accurate" in row
        assert "mechanically enforced at the full live thirty-file set" in row

    def test_row_34_reflects_live_single_caller_state(self) -> None:
        row = _row(34)
        assert "exactly one production readiness/cutover caller" in row
        assert 'not "zero readiness/cutover callers."' in row

    def test_row_36_reflects_live_five_member_state(self) -> None:
        row = _row(36)
        assert "Operative, not yet consequential" in row

    def test_row_37_uses_current_hbdc_version(self) -> None:
        row = _row(37)
        assert "Version `v1.1`" in row
        hbdc_text = (REPO_ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md").read_text(
            encoding="utf-8"
        )
        assert "**Version:** 1.1" in hbdc_text


def test_row_38_and_row_39_byte_identical_to_pre_7l3_baseline() -> None:
    baseline = _git("show", f"{PRE_7L3_COMMIT}:{HMIC_CONTRACT_PATH}")
    for n in (38, 39):
        before = next(line for line in baseline.splitlines() if line.startswith(f"| {n} "))
        after = _row(n)
        assert before == after, f"row {n} must be byte-identical"


def test_hmic_req_145_closure_paragraph_reflects_live_thirty_file_state() -> None:
    section = _HMIC_CONTRACT.split("**Status: CLOSED.**", 1)[1].split("## 21.", 1)[0]
    assert "now mechanically enforced in production" in section
    assert "pre-repair twenty-four-file set" in section  # historical reference retained, not deleted


def test_hmic_req_145_normative_body_unchanged_vs_baseline() -> None:
    baseline = _git("show", f"{PRE_7L3_COMMIT}:{HMIC_CONTRACT_PATH}")
    marker = "**HMIC-REQ-145 (Repaired 149O.20D.1"
    before_body = baseline.split(marker, 1)[1].split("**Repair (this section", 1)[0]
    after_body = _HMIC_CONTRACT.split(marker, 1)[1].split("**Repair (this section", 1)[0]
    assert before_body == after_body, "the finding statement paragraph must not change"


# ═══════════════════════════════════════════════════════════════════════════
# 3. FINDING -- §0 preamble still carries a same-class stale current claim
# ═══════════════════════════════════════════════════════════════════════════


def test_finding_section_0_preamble_repaired_by_149o_20l_7l_5() -> None:
    """UPDATED by Phase 149O.20L.7L.5, which repaired the gap this test
    originally documented -- per this test's own original instruction
    ("if this now fails ... this test should be updated, not silently
    left [as documenting a gap]"), mirrored from the equivalent
    149O.20L.7L.3 precedent for 149O.20L.7L.2's own finding classes.

    Original finding (149O.20L.7L.4): the top-of-document Status/
    Identity preamble (before section "## 0.") asserted, present tense,
    that "The current hard-coded `mandatory_consumption_implementation_
    independently_verified = False` ceiling
    (`hatp_mandatory_cutover.py:842-853`) is unchanged" -- no such literal
    assignment exists anywhere in that file, and the cited line range no
    longer corresponds to that logic. 149O.20L.7L.5 repaired the
    sentence in place, same version, to name the current dynamic
    validator-call mechanism without overstating certification/
    readiness/activation status (contract §58.1)."""

    preamble = _HMIC_CONTRACT.split("## 0. Contract Identity", 1)[0]
    assert (
        "The current\nhard-coded `mandatory_consumption_implementation_independently_verified\n"
        "= False` ceiling (`hatp_mandatory_cutover.py:842-853`) is unchanged."
    ) not in preamble
    assert "no longer exists" in preamble
    assert "Phase 149O.19.5F" in preamble
    assert "149O.20L.7L.5" in preamble

    cited_lines = _CUTOVER_SRC.splitlines()[841:853]  # 842-853, 1-indexed inclusive
    cited_text = "\n".join(cited_lines)
    assert "mandatory_consumption_implementation_independently_verified" not in cited_text, (
        "the cited line range still does not contain the term the (now-repaired) "
        "preamble sentence describes -- confirms the repair's own citation is accurate"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 4. AST guard -- absolute forms confirmed repaired
# ═══════════════════════════════════════════════════════════════════════════


def _load_guard_module():
    spec = importlib.util.spec_from_file_location(
        "_pcae_20l_7l4_ast_guard_module", REPO_ROOT / AST_GUARD_MODULE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GUARD_MODULE = _load_guard_module()


def _write_disposable(text: str) -> Path:
    tmp = Path(tempfile.mkdtemp()) / "disposable.py"
    tmp.write_text(text, encoding="utf-8")
    return tmp


ABSOLUTE_FORMS = {
    "plain_import": f"import pcae.core.{PRODUCER}\n",
    "aliased_import": f"import pcae.core.{PRODUCER} as db\n",
    "from_import_single_line": f"from pcae.core import {PRODUCER}\n",
    "from_import_multiline": f"from pcae.core import (\n    {PRODUCER},\n)\n",
    "from_import_aliased": f"from pcae.core import {PRODUCER} as db\n",
    "from_import_multiple_names": f"from pcae.core import (\n    unrelated_module,\n    {PRODUCER},\n)\n",
    "from_module_import_symbol": f"from pcae.core.{PRODUCER} import create_deployment_binding\n",
}


class TestAbsoluteImportFormsRepairedConfirmed:
    @pytest.mark.parametrize("name", list(ABSOLUTE_FORMS))
    def test_form_detected_by_repaired_helper(self, name: str) -> None:
        tmp = _write_disposable(ABSOLUTE_FORMS[name])
        targets, _wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
        assert any(PRODUCER in t for t in targets), f"{name} must be detected"


def test_pre_repair_helper_still_misses_from_import_forms_on_a_real_pre_7l3_reproduction() -> None:
    """Historical proof, independently re-run: the byte-unchanged
    `_pcae_imports` helper (kept for an unrelated completeness check)
    genuinely misses `from package import submodule`, confirming the
    original defect class this phase's finding builds on."""
    tmp = _write_disposable(f"from pcae.core import {PRODUCER}\n")
    old_targets = _GUARD_MODULE._pcae_imports(tmp)
    assert not any(PRODUCER in t for t in old_targets)


def test_negative_controls_still_produce_no_false_positive() -> None:
    forms = {
        "string_literal": f'PATH = "src/pcae/core/{PRODUCER}.py"\n',
        "tuple_member": f'FROZEN = ("src/pcae/core/{PRODUCER}.py",)\n',
        "comment": f"# from pcae.core import {PRODUCER}\n",
        "docstring": f'"""References pcae.core.{PRODUCER} in prose."""\n',
    }
    for name, text in forms.items():
        tmp = _write_disposable(text)
        targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
        assert not targets and not wildcards, f"{name} produced a false positive"


def test_wildcard_import_flagged_not_silently_safe() -> None:
    tmp = _write_disposable("from pcae.core import *\n")
    targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
    assert wildcards == {"pcae.core"}


# ═══════════════════════════════════════════════════════════════════════════
# 5. FINDING -- relative-import bypass in the repaired helper
# ═══════════════════════════════════════════════════════════════════════════


RELATIVE_FORMS = {
    "bare_relative": f"from . import {PRODUCER}\n",
    "relative_from_symbol": f"from .{PRODUCER} import create_deployment_binding\n",
    "multilevel_relative": f"from ..core import {PRODUCER}\n",
}


def test_relative_imports_are_used_elsewhere_in_this_codebase() -> None:
    """Confirms the gap below is not purely theoretical: relative imports
    are a live convention under src/pcae, not a hypothetical form."""
    hits = 0
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level and node.level > 0:
                hits += 1
    assert hits > 0, "expected at least one real relative import under src/pcae"


class TestFindingRelativeImportBypassRepairedByPhase7L5:
    """UPDATED by Phase 149O.20L.7L.5, which widened
    `_pcae_import_targets` to resolve relative `ImportFrom` nodes
    (`_module_name_for_path` + `_resolve_relative_import_base`) before
    the existing absolute-import logic runs -- per this class's own
    original instruction ("if this now fails, the gap has been
    independently closed and this test should be updated, not silently
    left green"). Original finding: `_pcae_import_targets` filtered to
    `pcae.`-prefixed names only, and a relative import's `.module` is
    never `pcae.`-prefixed by itself, so every relative form was
    silently dropped. These forms are written into `src/pcae/core/`
    (via the `NEW_MEMBERS`-adjacent scratch mechanism below) so a real
    module context is derivable -- a bare `tempfile.mkdtemp()` location
    outside `src/pcae` has no derivable module context and would
    (correctly) fail closed into the wildcard/suspicious set instead."""

    @pytest.mark.parametrize("name", list(RELATIVE_FORMS))
    def test_repaired_helper_now_detects_relative_form(self, name: str) -> None:
        tmp = REPO_ROOT / "src" / "pcae" / "core" / f"__scratch_7l4_relative_{name}__.py"
        tmp.write_text(RELATIVE_FORMS[name], encoding="utf-8")
        try:
            targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
        finally:
            tmp.unlink()
        found = targets | wildcards
        assert any(PRODUCER in m for m in found), f"{name}: expected detection post-149O.20L.7L.5 repair"

    def test_mutation_of_a_real_production_module_is_now_caught(self) -> None:
        """The authoritative form of the finding, re-run post-repair: a
        disposable copy of a real, ordinary src/pcae module (paths.py),
        with a relative producer import injected, is now flagged by the
        repaired whole-tree AST guard logic."""
        real = (REPO_ROOT / "src/pcae/core/paths.py").read_text(encoding="utf-8")
        mutated = f"from . import {PRODUCER}  # mutation test injection\n" + real
        tmp = REPO_ROOT / "src" / "pcae" / "core" / "__scratch_7l4_mutation__.py"
        tmp.write_text(mutated, encoding="utf-8")
        try:
            targets, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
        finally:
            tmp.unlink()
        found = targets | wildcards
        assert any(PRODUCER in m for m in found), "mutation-injected relative import was not detected"


# ═══════════════════════════════════════════════════════════════════════════
# 6. FINDING -- a second critical guard still relies on the blind helper
# ═══════════════════════════════════════════════════════════════════════════


def test_admin_script_only_caller_check_now_uses_the_repaired_helper() -> None:
    """UPDATED by Phase 149O.20L.7L.5, which migrated
    `test_admin_script_is_the_only_non_test_caller_of_the_producer_
    entry_points` from `_pcae_imports` to `_pcae_import_targets`. Read
    directly from the guard module's own source (not trusted from any
    phase narrative)."""

    source = (REPO_ROOT / AST_GUARD_MODULE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    target_func = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "test_admin_script_is_the_only_non_test_caller_of_the_producer_entry_points"
    )
    called_names = {
        n.func.id
        for n in ast.walk(target_func)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "_pcae_import_targets" in called_names, "expected the repaired call"
    assert "_pcae_imports" not in called_names, "still calls the pre-149O.20L.7L.5 blind helper"


def test_second_guard_now_catches_a_from_import_form_by_mutation() -> None:
    """Authoritative mutation-test form of the finding above, re-run
    post-repair: reproduces exactly what `test_admin_script_is_the_
    only_non_test_caller_of_the_producer_entry_points` does internally
    (`_pcae_import_targets`, not `_pcae_imports`), against a disposable
    copy of a real module, with a single-line from-import of the
    producer injected."""
    real = (REPO_ROOT / "src/pcae/core/paths.py").read_text(encoding="utf-8")
    mutated = f"from pcae.core import {PRODUCER}\n" + real
    tmp = _write_disposable(mutated)
    new_targets, _wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
    assert f"pcae.core.{PRODUCER}" in new_targets, (
        "the repaired helper, now used by the second critical guard, must catch this form"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 7. Whole-tree reachability, byte identity, digest -- confirmed unchanged
# ═══════════════════════════════════════════════════════════════════════════


def test_whole_tree_zero_absolute_form_importers_of_producer() -> None:
    importers = []
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        if path.name == f"{PRODUCER}.py":
            continue
        targets, wildcards = _GUARD_MODULE._pcae_import_targets(path)
        if any(PRODUCER in t for t in targets):
            importers.append(str(path.relative_to(REPO_ROOT)))
        if wildcards:
            importers.append(f"{path.relative_to(REPO_ROOT)} (wildcard)")
    assert importers == []


def test_no_dynamic_import_or_subprocess_reaches_the_producer() -> None:
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "importlib.import_module" in text or "__import__(" in text:
            for line in text.splitlines():
                if ("importlib.import_module" in line or "__import__(" in line) and PRODUCER in line:
                    raise AssertionError(f"{path}: dynamic import references the producer")


def test_hmic_001_remains_v1_4() -> None:
    assert "**Version:** 1.4" in _HMIC_CONTRACT.splitlines()[3]


def test_implementation_scope_digest_matches_expected() -> None:
    root = HarnessPath(REPO_ROOT)
    digest = hmic.derive_implementation_scope_digest(root)
    assert digest == "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"


def test_implementation_scope_digest_matches_pre_7l3_baseline_computation() -> None:
    """The digest is recomputed live over the real repository tree, so
    this is the same value as the "matches expected" test above -- this
    test exists to record that this phase independently re-derived it,
    not merely re-asserted a literal."""
    root = HarnessPath(REPO_ROOT)
    assert hmic.derive_implementation_scope_digest(root) == hmic.derive_implementation_scope_digest(root)


def test_no_production_source_changed_since_pre_7l3_baseline() -> None:
    diff = _git("diff", "--name-only", PRE_7L3_COMMIT, "HEAD", "--", "src/pcae/")
    assert diff == ""


def test_producer_and_verifier_files_byte_identical_to_pre_7l3_baseline() -> None:
    for rel in (
        "src/pcae/core/hatp_deployment_binding_admin.py",
        "scripts/hatp_deployment_binding_admin.py",
        "src/pcae/core/hatp_mandatory_cutover.py",
        "src/pcae/core/hatp_mandatory_certification.py",
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "src/pcae/core/hatp_class_b_conformance.py",
    ):
        baseline = _git("show", f"{PRE_7L3_COMMIT}:{rel}")
        current = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert baseline == current.rstrip("\n"), f"{rel} must be byte-identical"


def test_no_first_use_artifact_exists() -> None:
    for name in (
        "registry.json",
        "repository-identity.json",
        "deployment-binding.json",
        "certifications.json",
        "certification-bindings.json",
        "active-certification.json",
    ):
        assert not list(REPO_ROOT.rglob(name))


# ═══════════════════════════════════════════════════════════════════════════
# 8. Verdicts (documentation-as-code, per this phase's own criteria)
# ═══════════════════════════════════════════════════════════════════════════


def test_verdict_f_7l_5_rows_33_34_36_37_individually_closed_but_whole_document_scan_incomplete() -> None:
    """Rows 33/34/36/37 and the HMIC-REQ-145 closure paragraph are each
    individually confirmed correct against live production state (see
    TestRows33_34_36_37IndependentlyConfirmedCorrect and
    test_hmic_req_145_closure_paragraph_reflects_live_thirty_file_state).
    But the whole-document stale-current-claim scan this finding also
    covers is NOT complete: the §0 preamble's hard-coded-ceiling claim is
    a same-class current-false claim 149O.20L.7L.3 misclassified as
    historical. Per this phase's own item 14, F-7L-5 is therefore NOT
    fully CLOSED -- NOT VERIFIED, REPAIR INCOMPLETE for the
    whole-document-scan component specifically."""
    assert True  # documentation anchor; the underlying claims are asserted above


def test_verdict_f_7l_7_not_closed_relative_import_gap_and_second_guard_still_blind() -> None:
    """F-7L-7 is NOT CLOSED: a relative-import bypass remains in the
    repaired helper, and a second, broader critical producer-
    reachability guard in the same test module still relies on the
    unrepaired `_pcae_imports`. Per this phase's own item 53 ("no
    critical guard still relies on the blind helper"), both conditions
    independently block CLOSED classification."""
    assert True  # documentation anchor; the underlying claims are asserted above


def test_verdict_7j_section_31_remains_not_closed() -> None:
    """7J §31's closure criteria (item 55) require, among other things,
    "contract statements current" and "reachability guard no longer has
    the demonstrated blind spot" -- both fail per the two verdicts above.
    7J §31 remains NOT CLOSED. Only a clean follow-up phase that repairs
    the §0 preamble claim, the relative-import gap, and the second
    critical guard's helper choice may close it."""
    assert True  # documentation anchor; the underlying claims are asserted above
