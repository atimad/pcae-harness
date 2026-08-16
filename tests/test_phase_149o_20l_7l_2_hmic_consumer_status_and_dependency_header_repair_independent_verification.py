"""Phase 149O.20L.7L.2 — HMIC-001 v1.4 Consumer-Status and
Dependency-Header Repair Independent Verification.

Independently verifies 149O.20L.7L.1's repair (F-7L-1/F-7L-2 CLOSED,
confirmed by direct production-source reconstruction and byte-identity
checks below) and independently re-adjudicates F-7L-5/F-7L-7 without
inheriting 149O.20L.7L.1's own labels. Two of this phase's own findings
are recorded here as guards that currently FAIL/pass in the "gap exists"
direction and are expected to flip once a future narrow repair (see the
phase document's recommended next phase) lands -- update this module,
not delete these guards, when that happens:

- F-7L-5 (rows 33/34/36/37): each independently re-derived to be
  currently, demonstrably false against live production state (not
  merely "requires wide archaeology" as 149O.20L.7L.1 claimed) --
  `test_row_*_claim_is_currently_false` documents each with a direct,
  reproducible check against production constants.
- F-7L-7: the AST-level import guard
  (`test_no_module_under_src_pcae_imports_the_producer_at_ast_level` in
  the 149O.20L.7L test module) has a real, reproducible blind spot for
  `from package import submodule` forms -- `test_ast_guard_blind_spot_*`
  demonstrates it directly against literal adversarial source snippets,
  not against the real guard's file (no production/test file is edited
  by this phase).

Scope discipline: verification-only. No `src/pcae/**` edit, no contract
edit, no other test file edit.
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
    """Each of these documents that a row 149O.20L.7L.1 deferred as
    'requires wide architecture interpretation' is in fact directly,
    trivially falsifiable against today's live production state. These
    tests assert the row's *stale claim* is present in the live document
    (i.e. still unrepaired) -- they are expected to start failing, and
    should be updated/removed, once a future phase repairs rows
    33/34/36/37 the way 149O.20L.7L.1 repaired row 38."""

    def test_row_33_claim_of_22_file_digest_is_currently_false(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 30, (
            "if this ever reads 22, row 33's caveat may be accurate again"
        )
        assert "production still computes the twenty-two-file digest" in _HMIC_CONTRACT

    def test_row_36_claim_of_four_member_contract_versions_is_currently_false(self) -> None:
        live = hmic.derive_contract_versions(HarnessPath(REPO_ROOT))
        assert len(live) == 5, "if this ever reads 4, row 36's caveat may be accurate again"
        assert "production still computes the four-member set" in _HMIC_CONTRACT

    def test_row_37_claim_of_24_file_digest_is_currently_false(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 30
        assert "production still computes the twenty-four-file digest" in _HMIC_CONTRACT

    def test_row_34_hardcoded_ceiling_claim_is_currently_false(self) -> None:
        # The claim: "the hard-coded `mandatory_consumption_implementation_
        # independently_verified = False` ceiling remains unchanged and zero
        # readiness/cutover callers of the validator exist". Independently
        # falsified: cutover.py computes this term live via the validator,
        # not a hard-coded False.
        assert (
            "hmic_verified = certification_status_satisfies_readiness(hmic_validation.status)"
            in _CUTOVER_SRC
        )
        assert (
            "validate_active_hatp_mandatory_independent_verification_certification("
            in _CUTOVER_SRC
        )
        assert (
            "zero readiness/cutover callers of the validator exist" in _HMIC_CONTRACT
        )

    def test_row_34_functional_dependency_on_file_count_is_currently_false(self) -> None:
        # The claim: "no functional readiness decision depends on which file
        # count production currently computes over". Independently
        # falsified: the validator's Step 9 freshly recomputes
        # derive_implementation_scope_digest and rejects on divergence, and
        # that validator IS a live readiness term (previous test).
        assert "current_scope_digest = derive_implementation_scope_digest(harness_root)" in _CERT_SRC
        assert "current_scope_digest != record.implementation_scope_digest" in _CERT_SRC
        assert (
            "no functional readiness decision depends on which file count production currently computes over"
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
    module."""

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

    def test_ast_guard_blind_spot_single_line_from_package_import_submodule(self) -> None:
        found = _pcae_imports_as_implemented(
            "from pcae.core import hatp_deployment_binding_admin\n"
        )
        # This SHOULD be caught -- it is a real, valid submodule import --
        # but the guard as implemented only records `node.module` ("pcae.core"),
        # never inspecting `node.names`. Documents the gap; will start
        # failing once a future repair fixes `_pcae_imports`.
        assert not any("hatp_deployment_binding_admin" in m for m in found)

    def test_ast_guard_blind_spot_multiline_parenthesized_from_import(self) -> None:
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
