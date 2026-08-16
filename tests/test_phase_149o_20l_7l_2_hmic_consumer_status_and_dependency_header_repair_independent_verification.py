"""Phase 149O.20L.7L.2 — HMIC-001 v1.4 Consumer-Status and
Dependency-Header Repair Independent Verification.

Independently verifies 149O.20L.7L.1's repair (F-7L-1/F-7L-2 CLOSED,
confirmed by direct production-source reconstruction and byte-identity
checks below) and independently re-adjudicates F-7L-5/F-7L-7 without
inheriting 149O.20L.7L.1's own labels.

**Updated by Phase 149O.20L.7L.3** (finding F-7L-5/F-7L-7 repair; see
`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_
CONTRACT.md` §57 and `tests/test_phase_149o_20l_7l_3_attack_matrix_and_
ast_guard_narrow_repair.py`), per this module's own original instruction
to update, not delete, these guards once the gap they document closes:

- F-7L-5 (rows 33/34/36/37): `TestF7L5DeferredRowsCurrentlyFalse` is
  flipped in place below -- it now asserts the stale claims this class
  originally documented are *absent* from the live contract text, and
  that each row's corrected replacement text is present, while
  re-confirming the same underlying production facts (30 files, 5
  `contract_versions` members, dynamic not hard-coded ceiling, one real
  validator caller) unchanged.
- F-7L-7: `_pcae_imports_as_implemented` below still accurately
  reproduces `_pcae_imports` in the 149O.20L.7L test module -- that
  helper is deliberately left byte-unchanged by 149O.20L.7L.3 (it also
  backs the unrelated, already-passing transitive-closure completeness
  check, `test_producer_pair_reaches_no_unbound_pcae_module`, which a
  naive in-place fix would have broken). The real producer-reachability
  guard (`test_no_module_under_src_pcae_imports_the_producer_at_ast_
  level`) was repaired by switching to a new, separate helper,
  `_pcae_import_targets`, in the same 149O.20L.7L test module --
  `TestASTGuardBlindSpot` below is annotated in place to make this
  distinction explicit; it no longer characterizes "the guard's" blind
  spot, only the narrower helper's, which remains correct for its own,
  different purpose.

Scope discipline: verification-only for its own original phase; updated
in place by 149O.20L.7L.3 exactly as this module's own header
anticipated. No other file's test logic is touched by this update.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath

REPO_ROOT = Path(__file__).resolve().parents[1]

HMIC_CONTRACT_PATH = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
CUTOVER_MODULE = "src/pcae/core/hatp_mandatory_cutover.py"
CERT_MODULE = "src/pcae/core/hatp_mandatory_certification.py"

_HMIC_CONTRACT = (REPO_ROOT / HMIC_CONTRACT_PATH).read_text(encoding="utf-8")
_CUTOVER_SRC = (REPO_ROOT / CUTOVER_MODULE).read_text(encoding="utf-8")
_CERT_SRC = (REPO_ROOT / CERT_MODULE).read_text(encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


# ═══════════════════════════════════════════════════════════════════════════
# 1. F-7L-1 / F-7L-2: independent re-confirmation (this phase's own
#    reconstruction, not a re-import of 149O.20L.7L.1's test module)
# ═══════════════════════════════════════════════════════════════════════════


def test_cutover_module_is_the_sole_production_consumer_of_the_verifier() -> None:
    matches = _git(
        "grep", "-rln", "verify_class_b_deployment_conformance", "--", "src/pcae"
    ).splitlines()
    assert set(matches) == {
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hatp_mandatory_cutover.py",
    }


def test_class_b_readiness_term_is_the_eighth_of_eight() -> None:
    assert _CUTOVER_SRC.count("checks.append(") == 8
    assert "class_b_deployment_conformance_satisfies_readiness" in _CUTOVER_SRC


def test_readiness_recheck_is_lock_held_before_activation_write() -> None:
    assert "fcntl.flock(lock_fd, fcntl.LOCK_EX)" in _CUTOVER_SRC
    lock_index = _CUTOVER_SRC.index("fcntl.flock(lock_fd, fcntl.LOCK_EX)")
    readiness_check_call_index = _CUTOVER_SRC.index("readiness = readiness_check()")
    assert lock_index < readiness_check_call_index


def test_hbdc_header_matches_live_derivation() -> None:
    live = hmic.derive_contract_versions(HarnessPath(REPO_ROOT))
    assert live["HBDC-001"] == "1.1"
    assert "HBDC-001 v1.1" in _HMIC_CONTRACT
    header = next(
        line
        for line in _HMIC_CONTRACT.splitlines()
        if line.startswith("**Depends on (current, HMIC-unamended):**")
    )
    assert "HBDC-001 v1.1" in header
    assert "HBDC-001 v1.0" not in header


def test_implementation_scope_digest_matches_expected() -> None:
    digest = hmic.derive_implementation_scope_digest(HarnessPath(REPO_ROOT))
    assert digest == "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"


def test_thirty_member_frozen_set_matches_production_exactly() -> None:
    prod = list(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES) + list(
        hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
    )
    assert len(prod) == 30
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 30


# ═══════════════════════════════════════════════════════════════════════════
# 2. F-7L-5 (independent, non-inherited): rows 33/34/36/37 currently false
# ═══════════════════════════════════════════════════════════════════════════


class TestF7L5DeferredRowsCurrentlyFalse:
    """Originally documented that a row 149O.20L.7L.1 deferred as
    'requires wide architecture interpretation' was in fact directly,
    trivially falsifiable against live production state. Flipped in
    place by Phase 149O.20L.7L.3, per this module's own original
    instruction: now asserts the stale claim is *absent* from the live
    contract text (repaired), while re-confirming the same underlying
    production facts this class always rested on."""

    def test_row_33_stale_22_file_digest_claim_is_repaired(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 30, (
            "if this ever reads other than 30, row 33's repair text needs re-adjudication"
        )
        assert "production still computes the twenty-two-file digest, so" not in _HMIC_CONTRACT
        assert "production still computes the twenty-two-file digest\" caveat is superseded" in _HMIC_CONTRACT

    def test_row_36_stale_four_member_contract_versions_claim_is_repaired(self) -> None:
        live = hmic.derive_contract_versions(HarnessPath(REPO_ROOT))
        assert len(live) == 5, "if this ever reads other than 5, row 36's repair text needs re-adjudication"
        assert "production still computes the four-member set\", so" not in _HMIC_CONTRACT
        assert "production still computes the four-member set\" caveat is superseded" in _HMIC_CONTRACT

    def test_row_37_stale_24_file_digest_claim_is_repaired(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 30
        assert "production still computes the twenty-four-file digest\", so" not in _HMIC_CONTRACT
        assert "production still computes the twenty-four-file digest\" caveat is superseded" in _HMIC_CONTRACT

    def test_row_34_hardcoded_ceiling_claim_is_repaired(self) -> None:
        # The original claim: "the hard-coded `mandatory_consumption_
        # implementation_independently_verified = False` ceiling remains
        # unchanged and zero readiness/cutover callers of the validator
        # exist". Independently falsified, and now corrected in place:
        # cutover.py computes this term live via the validator, not a
        # hard-coded False, and that validator has exactly one caller.
        assert (
            "hmic_verified = certification_status_satisfies_readiness(hmic_validation.status)"
            in _CUTOVER_SRC
        )
        assert (
            "validate_active_hatp_mandatory_independent_verification_certification("
            in _CUTOVER_SRC
        )
        assert "zero readiness/cutover callers of the validator exist" not in _HMIC_CONTRACT
        assert "not \"zero readiness/cutover callers.\"" in _HMIC_CONTRACT

    def test_row_34_functional_dependency_on_file_count_conclusion_preserved(self) -> None:
        # The row's bottom-line conclusion ("no functional readiness
        # decision currently turns on file count") is independently true
        # for an unchanged, different reason (no stored certification
        # exists on this host) and is deliberately preserved, not removed,
        # by the repair -- only the two false supporting premises were
        # corrected (previous test).
        assert "current_scope_digest = derive_implementation_scope_digest(harness_root)" in _CERT_SRC
        assert "current_scope_digest != record.implementation_scope_digest" in _CERT_SRC
        assert (
            "no functional readiness decision currently turns on which file count a caller computes over"
            in _HMIC_CONTRACT
        )

    def test_wave_f_wiring_predates_149o_19_5e_1_row_34_text(self) -> None:
        # Independently reconstructed chronology: Phase 149O.19.5F wired the
        # real validator call into cutover.py readiness; 149O.19.5E.1 wrote
        # row 34's now-stale text. 149O.19.5F is *more recent* than
        # 149O.19.5E.1 in git log --oneline (lower line index == closer to
        # HEAD == later commit).
        log = _git("log", "--oneline").splitlines()
        wave_f_index = next(i for i, line in enumerate(log) if line.startswith("478f8b2c"))
        wave_e1_index = next(
            i
            for i, line in enumerate(log)
            if "149O.19.5E.1: HMIC v1.1 Validator/Admin Implementation Identity Contract Evolution" in line
        )
        assert wave_f_index < wave_e1_index, "Wave F wiring must be the more recent commit"


# ═══════════════════════════════════════════════════════════════════════════
# 3. F-7L-7 (independent): AST-guard blind spot for `from package import
#    submodule` forms, demonstrated against literal adversarial snippets
# ═══════════════════════════════════════════════════════════════════════════


def _pcae_imports_as_implemented(text: str) -> set[str]:
    """Reproduces the exact logic of `_pcae_imports` in
    tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_
    independent_verification.py, against a literal string rather than a
    file, to demonstrate the gap without importing or mutating that
    module.

    Annotated by Phase 149O.20L.7L.3 (finding F-7L-7 repair): `_pcae_
    imports` itself is intentionally left byte-unchanged by that repair
    (it also backs an unrelated, already-passing transitive-closure
    completeness check that a naive fix would have broken -- see that
    module's own `_pcae_import_targets` docstring for why). The real
    producer-reachability guard was repaired by switching to a new,
    separate helper there, not by editing this one. The tests below
    therefore still correctly describe `_pcae_imports`'s own remaining
    narrower blind spot; they no longer describe "the guard's" blind
    spot, since the guard no longer uses this helper. See
    `tests/test_phase_149o_20l_7l_3_attack_matrix_and_ast_guard_narrow_
    repair.py` for adversarial coverage of the repaired guard itself."""

    tree = ast.parse(text)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return {name for name in found if name.startswith("pcae.")}


class TestASTGuardBlindSpot:
    def test_ast_guard_catches_a_plain_import(self) -> None:
        found = _pcae_imports_as_implemented(
            "import pcae.core.hatp_deployment_binding_admin\n"
        )
        assert any("hatp_deployment_binding_admin" in m for m in found)

    def test_helper_blind_spot_single_line_from_package_import_submodule(self) -> None:
        found = _pcae_imports_as_implemented(
            "from pcae.core import hatp_deployment_binding_admin\n"
        )
        # `_pcae_imports` only records `node.module` ("pcae.core"), never
        # inspecting `node.names` -- unchanged by 149O.20L.7L.3 (see the
        # helper docstring above for why); the real guard no longer uses
        # this helper for producer reachability.
        assert not any("hatp_deployment_binding_admin" in m for m in found)

    def test_helper_blind_spot_multiline_parenthesized_from_import(self) -> None:
        text = (
            "from pcae.core import (\n"
            "    hatp_bootstrap,\n"
            "    hatp_deployment_binding_admin,\n"
            ")\n"
        )
        found = _pcae_imports_as_implemented(text)
        assert not any("hatp_deployment_binding_admin" in m for m in found)

    def test_textual_occurrence_guard_also_misses_the_multiline_form(self) -> None:
        # Reproduces the tightened 7I/7J occurrence check exactly (first
        # token of the matching line must be import/from) against the same
        # multiline snippet, in the one file that carries an exemption
        # (hatp_mandatory_certification.py) -- demonstrating that this
        # specific adversarial construction evades *every* current guard,
        # not only the AST one.
        text = (
            "from pcae.core import (\n"
            "    hatp_bootstrap,\n"
            "    hatp_deployment_binding_admin,\n"
            ")\n"
        )
        offending = [
            line
            for line in text.splitlines()
            if "hatp_deployment_binding_admin" in line
            and line.strip().split(" ", 1)[0] in ("import", "from")
        ]
        assert offending == []
