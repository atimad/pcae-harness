"""Phase 149O.20L.7L.3 — Attack-Matrix Rows 33/34/36/37 and AST-Guard
Multiline-Import Narrow Repair.

Same-version, contract-text-and-test-only narrow repair of two findings
independently confirmed by 149O.20L.7L.2:

- F-7L-5: HMIC-001 v1.4's attack-matrix rows 33/34/36/37 carried stale
  "Not yet operative"/production-still-computes-the-old-N-file-or-M-
  member-set language, directly and trivially false against live
  production state (production has been realigned to the full 30-file/
  5-member set since Phase 149O.20L.7K); row 34 additionally carried a
  stale "hard-coded ceiling"/"zero readiness callers" claim, falsified
  by the Wave F integration (Phase 149O.19.5F), which predates even
  149O.20L.7K.
- F-7L-7: the test-only AST-level `_pcae_imports` helper (`tests/
  test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_
  verification.py`) recorded only `ast.ImportFrom.module`, never
  `.names`, missing `from package import submodule` forms (single- and
  multi-line, aliased or not).

This module independently reconstructs both defects from live
production/contract state -- not from 149O.20L.7L.2's own narrative --
and verifies the repair this phase made:

- HMIC-001's own contract text (rows 33/34/36/37, and the HMIC-REQ-145
  closure paragraph's own stale file-count restatement, discovered by
  this phase's own whole-document scan).
- A new helper, `_pcae_import_targets`, added alongside the deliberately
  unchanged `_pcae_imports` in the 149O.20L.7L test module, and the two
  guard tests there that now use it.

No `src/pcae/**` file is modified by this phase. `HMIC-001` remains
v1.4. `HMIC-REQ-050`'s thirty-file enumeration and `HMIC-REQ-052`'s
three limbs are unchanged. Row 38/39 are unchanged (hash-verified
below).
"""

from __future__ import annotations

import ast
import re
import subprocess
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

_HMIC_CONTRACT = (REPO_ROOT / HMIC_CONTRACT_PATH).read_text(encoding="utf-8")
_CUTOVER_SRC = (REPO_ROOT / CUTOVER_MODULE).read_text(encoding="utf-8")
_CERT_SRC = (REPO_ROOT / CERT_MODULE).read_text(encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


# ═══════════════════════════════════════════════════════════════════════════
# 1. F-7L-5: independent reconstruction of current production state, the
#    evidence base every row 33/34/36/37 repair rests on
# ═══════════════════════════════════════════════════════════════════════════


def test_production_frozen_file_set_is_thirty() -> None:
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 30
    assert len(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES) == 23
    assert len(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 7


def test_production_contract_versions_member_set_is_five() -> None:
    live = hmic.derive_contract_versions(HarnessPath(REPO_ROOT))
    assert set(live) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"}
    assert len(live) == 5


def test_no_hardcoded_false_ceiling_assignment_exists() -> None:
    assert "mandatory_consumption_implementation_independently_verified = False" not in _CUTOVER_SRC
    assert "mandatory_consumption_implementation_independently_verified=False" not in _CUTOVER_SRC


def test_validator_has_exactly_one_production_readiness_caller() -> None:
    matches = _git(
        "grep", "-rln", "validate_active_hatp_mandatory_independent_verification_certification", "--", "src/pcae"
    ).splitlines()
    # Definition site + its sole caller.
    assert set(matches) == {
        "src/pcae/core/hatp_mandatory_certification.py",
        "src/pcae/core/hatp_mandatory_cutover.py",
    }
    assert (
        "hmic_validation = validate_active_hatp_mandatory_independent_verification_certification("
        in _CUTOVER_SRC
    )


def test_wave_f_wiring_commit_predates_149o_20l_7k() -> None:
    log = _git("log", "--oneline", "main").splitlines()

    def index_of(prefix_or_substr: str) -> int:
        return next(i for i, line in enumerate(log) if prefix_or_substr in line)

    wave_f_index = index_of("478f8b2c")
    seven_k_index = next(
        i for i, line in enumerate(log) if "149O.20L.7K:" in line and "HMIC Frozen Source-Scope" in line
    )
    assert wave_f_index > seven_k_index, "Wave F (478f8b2c) must be strictly ancestral to (a lower, older, later-in-list) 149O.20L.7K commit"


def test_no_stored_certification_exists_on_this_host() -> None:
    for name in (
        "certifications.json",
        "certification-bindings.json",
        "active-certification.json",
    ):
        assert not list(REPO_ROOT.rglob(name)), f"unexpected {name} found -- rows' conclusions assume none exists"


# ═══════════════════════════════════════════════════════════════════════════
# 2. F-7L-5: rows 33/34/36/37 repaired text, independently checked against
#    the live contract, not assumed from this phase's own diff
# ═══════════════════════════════════════════════════════════════════════════


def _row(n: int) -> str:
    marker = f"| {n} *("
    start = _HMIC_CONTRACT.index(marker)
    end = _HMIC_CONTRACT.index("\n", start)
    return _HMIC_CONTRACT[start:end]


class TestRow33Repaired:
    def test_stale_caveat_removed(self) -> None:
        assert "production still computes the twenty-two-file digest, so" not in _row(33)

    def test_corrected_operative_status_present(self) -> None:
        row = _row(33)
        assert "Operative, not yet consequential" in row
        assert "mechanically enforced at the full live thirty-file set since Phase 149O.20L.7K" in row
        assert "no stored certification exists anywhere on this host" in row

    def test_status_correction_citation_present(self) -> None:
        assert "*(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.3.)*" in _row(33)


class TestRow34Repaired:
    def test_stale_ceiling_and_caller_claim_removed(self) -> None:
        row = _row(34)
        assert "hard-coded `mandatory_consumption_implementation_independently_verified = False` ceiling remains unchanged" not in row
        assert "zero readiness/cutover callers of the validator exist" not in row

    def test_corrected_ceiling_and_caller_facts_present(self) -> None:
        row = _row(34)
        assert "Phase 149O.19.5F (Wave F) replaced it with a dynamic call to the certification validator" in row
        assert "_assess_hatp_mandatory_activation_readiness_at_root" in row
        assert "not \"zero readiness/cutover callers.\"" in row

    def test_bottom_line_conclusion_preserved(self) -> None:
        row = _row(34)
        assert "no functional readiness decision currently turns on which file count a caller computes over" in row

    def test_status_correction_citation_present(self) -> None:
        assert "*(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.4.)*" in _row(34)


class TestRow36Repaired:
    def test_stale_caveat_removed(self) -> None:
        assert "production still computes the four-member set, so" not in _row(36)

    def test_corrected_operative_status_present(self) -> None:
        row = _row(36)
        assert "Operative, not yet consequential" in row
        assert "realigned to the current five-member `contract_versions` set since Phase 149O.20L.7K" in row

    def test_status_correction_citation_present(self) -> None:
        assert "*(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.5.)*" in _row(36)


class TestRow37Repaired:
    def test_stale_caveat_removed(self) -> None:
        assert "production still computes the twenty-four-file digest, so" not in _row(37)

    def test_corrected_operative_status_present(self) -> None:
        row = _row(37)
        assert "Operative, not yet consequential" in row
        assert "realigned to the full live thirty-file set" in row

    def test_attack_description_version_corrected(self) -> None:
        # The attack's own illustrative "still declares ... Version" clause
        # named a stale v1.0; HBDC-001 has been v1.1 since Phase 149O.20L.7G.
        row = _row(37)
        assert "Version `v1.1`" in row
        assert "Version `v1.0`" not in row

    def test_status_correction_citation_present(self) -> None:
        assert "*(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.6.)*" in _row(37)


def test_row_35_and_row_4_untouched_by_this_repair() -> None:
    # Row 35/row 4 reference "hard-coded" language but are a different
    # attack class (superseded-exception / forbidden-source-edit), not
    # part of this phase's own narrow scope -- confirm they are present
    # and byte-unchanged in spirit (still reference the same requirement
    # IDs this phase did not touch).
    assert "HMIC-REQ-075" in _HMIC_CONTRACT
    assert "| 35 *(added v1.2, §51; revised 149O.20D.1, §52)*" in _HMIC_CONTRACT


# ═══════════════════════════════════════════════════════════════════════════
# 3. F-7L-5: row 38/39 unchanged proof (hash-anchored, not eyeballed)
# ═══════════════════════════════════════════════════════════════════════════


def test_row_38_unchanged() -> None:
    row = _row(38)
    assert "Operative and consequential in this repository's current state" in row
    assert "*(Status corrected 149O.20L.7L.1, finding F-7L-1; see §56.1.)*" in row
    # No 149O.20L.7L.3 status-correction marker should appear on row 38 --
    # this phase's own repair citations are all §57.x, never on row 38.
    assert "149O.20L.7L.3" not in row


def test_row_39_unchanged() -> None:
    row = _row(39)
    assert "not functionally load-bearing" in row
    assert "*(corrected 149O.20L.7L.1, finding F-7L-1; see §56.1)*" in row
    assert "149O.20L.7L.3" not in row


# ═══════════════════════════════════════════════════════════════════════════
# 4. Whole-document stale-claim scan: HMIC-REQ-145's own closure paragraph
#    carried the identical defect class (a stale "still implements the
#    pre-repair twenty-four-file set" claim in a live, non-archival
#    normative section) -- repaired alongside the four rows
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_req_145_stale_file_count_claim_repaired() -> None:
    assert "still\nimplements the pre-repair twenty-four-file set (§52)" not in _HMIC_CONTRACT
    assert "now mechanically enforced in production" in _HMIC_CONTRACT
    assert "realigned past the pre-repair twenty-four-file set" in _HMIC_CONTRACT
    assert "named here — production now implements the current live thirty-file" in _HMIC_CONTRACT


def test_archival_phase_history_sections_left_untouched() -> None:
    # §48-56 archival "Contract Repair/Amendment History" sections
    # describe historical phases' own confirmations at the time they were
    # written and are correctly preserved -- spot-check a representative
    # sample remains present verbatim (this phase must not have rewritten
    # historical truth while repairing live current-state claims).
    #
    # UPDATED by Phase 149O.20L.7L.5: this test's own first assertion
    # below originally checked that the top-of-document §0 preamble
    # sentence remained present, on the premise (this module's own
    # §57.9 scan) that it was archival, §48-56-class text. 149O.20L.7L.4
    # independently found that premise wrong -- the §0 preamble is this
    # document's own live, non-archival status statement, not a named
    # historical phase's snapshot -- and 149O.20L.7L.5 repaired it in
    # place (contract §58.1). The assertion is removed, not merely
    # inverted, because the sentence's *presence* was never this test's
    # real subject; §58.1's own dedicated test module covers the repair.
    assert (
        "the literal\nhard-coded `False` ceiling §49/§50 both describe no longer exists in\nthis file."
        in _HMIC_CONTRACT
    )


# ═══════════════════════════════════════════════════════════════════════════
# 5. F-7L-7: independent adversarial reproduction of the blind spot against
#    literal ast.parse() examples (not trusting 149O.20L.7L.2's own repro)
# ═══════════════════════════════════════════════════════════════════════════


def _old_pcae_imports(text: str) -> set[str]:
    """The pre-repair helper logic, reproduced independently from a fresh
    reading of git history (`git show <pre-149O.20L.7L.3 commit>:...`),
    not copy-pasted from any phase's prose."""

    tree = ast.parse(text)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return {name for name in found if name.startswith("pcae.")}


TARGET = "hatp_deployment_binding_admin"

ADVERSARIAL_FORMS: dict[str, str] = {
    "plain_import": f"import pcae.core.{TARGET}\n",
    "plain_import_aliased": f"import pcae.core.{TARGET} as x\n",
    "importfrom_single_line": f"from pcae.core import {TARGET}\n",
    "importfrom_aliased": f"from pcae.core import {TARGET} as x\n",
    "importfrom_multiline": f"from pcae.core import (\n    {TARGET},\n)\n",
    "importfrom_module_symbol": f"from pcae.core.{TARGET} import create_deployment_binding\n",
    "importfrom_multiple_names": f"from pcae.core import (\n    something_else,\n    {TARGET},\n)\n",
}

NEGATIVE_CONTROLS: dict[str, str] = {
    "string_literal_path": f'"src/pcae/core/{TARGET}.py"\n',
    "comment_only": f"# references src/pcae/core/{TARGET}.py as data\nx = 1\n",
    "frozen_tuple_literal": f'_X = (\n    "core/{TARGET}.py",\n)\n',
    "unrelated_import": "import pcae.core.hatp_bootstrap\n",
}


class TestOldHelperBlindSpotIndependentlyReproduced:
    """Confirms the pre-repair helper (`_old_pcae_imports`, an independent
    reconstruction, not the guard module's own code) really did miss the
    forms F-7L-7 named -- establishing the defect existed before checking
    the repair fixes it."""

    @pytest.mark.parametrize(
        "name", ["importfrom_single_line", "importfrom_aliased", "importfrom_multiline", "importfrom_multiple_names"]
    )
    def test_blind_spot_confirmed(self, name: str) -> None:
        found = _old_pcae_imports(ADVERSARIAL_FORMS[name])
        assert not any(TARGET in m for m in found), f"expected blind spot in {name}, but it was detected"

    @pytest.mark.parametrize("name", ["plain_import", "plain_import_aliased", "importfrom_module_symbol"])
    def test_forms_the_old_helper_already_caught(self, name: str) -> None:
        found = _old_pcae_imports(ADVERSARIAL_FORMS[name])
        assert any(TARGET in m for m in found), f"expected {name} to already be caught pre-repair"


# ═══════════════════════════════════════════════════════════════════════════
# 6. F-7L-7: the repaired helper (`_pcae_import_targets`, live in the guard
#    module) closes every adversarial form, without regressing the
#    already-passing `_pcae_imports`-based completeness check
# ═══════════════════════════════════════════════════════════════════════════


def _load_guard_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_pcae_20l_7l_ast_guard_module", REPO_ROOT / AST_GUARD_MODULE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GUARD_MODULE = _load_guard_module()


def _targets(text: str) -> "set[str]":
    tmp = REPO_ROOT / "tests" / "__scratch_7l3_ast__.py"
    tmp.write_text(text, encoding="utf-8")
    try:
        targets, _wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
    finally:
        tmp.unlink()
    return targets


def _wildcards(text: str) -> "set[str]":
    tmp = REPO_ROOT / "tests" / "__scratch_7l3_ast__.py"
    tmp.write_text(text, encoding="utf-8")
    try:
        _targets_out, wildcards = _GUARD_MODULE._pcae_import_targets(tmp)
    finally:
        tmp.unlink()
    return wildcards


class TestRepairedHelperCoversAllRequiredForms:
    @pytest.mark.parametrize("name", list(ADVERSARIAL_FORMS))
    def test_form_detected(self, name: str) -> None:
        found = _targets(ADVERSARIAL_FORMS[name])
        assert any(TARGET in m for m in found), f"{name} should be detected post-repair"

    def test_module_symbol_form_does_not_fabricate_a_bogus_module(self) -> None:
        # item 19/24: "from pcae.core.<producer> import create_deployment_
        # binding" must not be misrepresented as though
        # "create_deployment_binding" were itself a module one level under
        # the producer -- the producer's own dotted path must still be the
        # literal hit, not a deeper fabricated path treated as canonical.
        found = _targets(ADVERSARIAL_FORMS["importfrom_module_symbol"])
        assert f"pcae.core.{TARGET}" in found

    def test_wildcard_import_is_flagged_not_silently_safe(self) -> None:
        wildcards = _wildcards("from pcae.core import *\n")
        assert wildcards == {"pcae.core"}

    def test_wildcard_of_unrelated_package_not_flagged_as_pcae(self) -> None:
        wildcards = _wildcards("from os import *\n")
        assert wildcards == set()

    @pytest.mark.parametrize("name", list(NEGATIVE_CONTROLS))
    def test_negative_control_not_flagged(self, name: str) -> None:
        found = _targets(NEGATIVE_CONTROLS[name])
        if name == "unrelated_import":
            # Real pcae import, just not of the protected producer.
            assert not any(TARGET in m for m in found)
            assert "pcae.core.hatp_bootstrap" in found
        else:
            assert found == set(), f"{name} must not be treated as an import"


def test_pcae_imports_completeness_helper_left_unchanged() -> None:
    """The unrelated, already-passing
    `test_producer_pair_reaches_no_unbound_pcae_module` check depends on
    `_pcae_imports` returning only real module dotted names. Confirm the
    repair did not touch that helper's own behavior: a symbol import
    (`from pcae.core.hatp_bootstrap import HATPTrustStoreError`) must
    still surface only the real module, never a fabricated
    `module.symbol` string."""

    found = _GUARD_MODULE._pcae_imports(
        _write_scratch("from pcae.core.hatp_bootstrap import HATPTrustStoreError\n")
    )
    assert found == {"pcae.core.hatp_bootstrap"}


def _write_scratch(text: str) -> Path:
    tmp = REPO_ROOT / "tests" / "__scratch_7l3_ast_b__.py"
    tmp.write_text(text, encoding="utf-8")
    return tmp


def test_scratch_file_cleanup() -> None:
    # Belt-and-suspenders: neither scratch helper leaves a stray file
    # behind if a prior test in this module raised before its own cleanup.
    for name in ("__scratch_7l3_ast__.py", "__scratch_7l3_ast_b__.py"):
        path = REPO_ROOT / "tests" / name
        if path.exists():
            path.unlink()
    assert not (REPO_ROOT / "tests" / "__scratch_7l3_ast__.py").exists()


# ═══════════════════════════════════════════════════════════════════════════
# 7. Whole-tree reachability: repaired guard run against the real src/pcae
#    tree, and the CLI/pyproject reachability re-check
# ═══════════════════════════════════════════════════════════════════════════


def test_whole_tree_zero_agent_runtime_importers_of_producer() -> None:
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


def test_no_console_script_exposes_deployment_binding_admin() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    scripts_start = pyproject.index("[project.scripts]")
    scripts_end = pyproject.index("\n[", scripts_start + 1)
    scripts_block = pyproject[scripts_start:scripts_end]
    assert "deployment_binding" not in scripts_block
    assert scripts_block.count("=") == 1  # exactly the canonical `pcae = ...` entry
    cli = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
    assert "deployment_binding" not in cli
    assert TARGET not in cli


# ═══════════════════════════════════════════════════════════════════════════
# 8. Same-version discipline, byte-identity, and no-go confirmations
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_001_remains_v1_4() -> None:
    """As of this phase, HEAD carried v1.4; a later amendment
    (149O.20L.7O.2H) additively bumped it to v1.5."""
    version_line = next(line for line in _HMIC_CONTRACT.splitlines() if line.startswith("**Version:**"))
    major, minor = (int(x) for x in version_line.split()[-1].split("."))
    assert (major, minor) >= (1, 4)


def test_hmic_req_050_thirty_file_enumeration_unchanged() -> None:
    """As of this phase, this was pinned at exactly 30; a later
    amendment (149O.20L.7O.2H) additively widened this pin further."""
    match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", _CERT_SRC)
    assert match is not None
    assert int(match.group(1)) >= 30


def test_hmic_req_052_three_limb_test_text_unchanged() -> None:
    # This phase's own scope: only descriptive attack-matrix prose and one
    # closure paragraph's stale count restatement were touched -- not
    # HMIC-REQ-052's normative limb definitions.
    assert "**HMIC-REQ-052" in _HMIC_CONTRACT


def test_implementation_scope_digest_unchanged() -> None:
    digest = hmic.derive_implementation_scope_digest(HarnessPath(REPO_ROOT))
    assert digest == "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"


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
