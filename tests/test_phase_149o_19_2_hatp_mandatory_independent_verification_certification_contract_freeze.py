"""Phase 149O.19.2 -- Contract-verification test for the HATP Mandatory
Independent-Verification Certification Contract (HMIC-001 v1.0,
`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`)
and its phase document
(`docs/PHASE_149O_19_2_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT_FREEZE.md`).

149O.19.2 is a CONTRACT-FREEZE-ONLY phase: it modifies no `src/pcae/**`
file and no existing contract file. This module does not test an
implementation (there is none yet -- no certification artifact, active-
certification pointer, or revocation record exists anywhere in this
repository). It independently re-verifies, by direct document and
source inspection rather than by trusting the contract's own prose:

  * the frozen contract identity, requirement sequence, invariant, and
    attack-matrix counts declared by the new contract document itself;
  * that the contract text is internally self-consistent (no implicit-
    latest language, no partial-credit validation status, no self-
    certification path);
  * that the frozen authority-bearing file set (HMIC-REQ-050) names
    files that actually exist on disk today (existence only -- this
    does not, and cannot, certify their bytes);
  * that the four bound contracts' own current version headers still
    match the `contract_versions` values this contract freezes;
  * that no existing contract file (HMRC-001, HATP-001, HSCE-001,
    RAE-001, RWMPC-001, PBPA-001, PBPC-001) was modified by this phase,
    and that no `src/pcae/**` file was modified by this phase.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"

_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_PHASE_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_19_2_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT_FREEZE.md"
)
_ARCHITECTURE_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_19_1_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_ARCHITECTURE.md"
)

# HMIC-REQ-050's frozen authority-bearing file set, exactly as enumerated
# in the contract. Paths under `core/`, `commands/`, or bare `cli.py`
# are relative to `src/pcae/`; the four contract paths are relative to
# the repository root.
#: NOTE: Phase 149O.19.3R added the last four entries below (finding
#: B-149O.19.3-1, see contract §49) to repair an under-bound frozen file
#: set 149O.19.3's independent verification found. The 149O.19.2
#: freeze phase itself only ever named the first fourteen; this
#: regression test's expected list/count is updated per that later
#: phase's own explicit repair-regression instruction, not reopened
#: casually.
_FROZEN_SRC_RELATIVE_PATHS = (
    "core/hatp_mandatory_cutover.py",
    "core/hatp_ag_authority.py",
    "core/hatp_rollback_consumption.py",
    "core/hatp_bootstrap.py",
    "core/human_approval_trusted_provenance.py",
    "core/repository_identity.py",
    "core/rollback_approval_evidence.py",
    "core/hatp_evidence_store.py",
    "core/hatp_signed_evidence.py",
    "core/agent.py",
    "commands/agent.py",
    "cli.py",
    "core/permission_broker.py",
    "core/permission_broker_foundation.py",
    "core/hatp_providers.py",
    "core/hatp_fido2_provider.py",
    "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py",
)

_FROZEN_CONTRACT_REPO_RELATIVE_PATHS = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
)

# This phase's own entry commit -- the last commit before 149O.19.2's
# own first commit. Used to scope the "no production/contract change"
# diff to exactly this phase's own commits, not an eternally-moving
# ref (149O.18F's methodology).
_PHASE_149O_19_2_ENTRY_COMMIT = "560924f2"


def _contract_text() -> str:
    return _CONTRACT_PATH.read_text(encoding="utf-8")


def _phase_doc_text() -> str:
    return _PHASE_DOC_PATH.read_text(encoding="utf-8")


def _diff_since_entry(pathspec: str) -> str:
    result = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_149O_19_2_ENTRY_COMMIT, "HEAD", "--", pathspec],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout


# ═══════════════════════════════════════════════════════════════════════════
# Contract document exists and declares the frozen identity
# ═══════════════════════════════════════════════════════════════════════════


class TestContractIdentity:
    def test_contract_file_exists(self):
        assert _CONTRACT_PATH.is_file()

    def test_phase_doc_exists(self):
        assert _PHASE_DOC_PATH.is_file()

    def test_architecture_source_exists(self):
        assert _ARCHITECTURE_DOC_PATH.is_file()

    def test_contract_id_and_version_frozen(self):
        # Phase 149O.19.5E.1 bumped HMIC-001 from v1.0 to v1.1 (contract
        # §50): v1.0 was independently verified and a real implementation
        # of it now exists, so continuing to call the widened 24-file
        # scope "v1.0" would let the term silently mean two different
        # things. This assertion tracks the contract's own live current
        # version, exactly as it already did across the 149O.19.2 ->
        # 149O.19.3R status-text update below; it is not a claim that
        # v1.0 never existed (see tests/test_phase_149o_19_3r_1_..., which
        # independently pins the historical v1.0/22-file state).
        text = _contract_text()
        assert "**Contract ID:** HMIC-001" in text
        assert "**Version:** 1.1" in text

    def test_status_is_frozen_not_verified(self):
        # Phase 149O.19.3R repaired HMIC-REQ-050/052 (finding B-149O.19.3-1,
        # see contract §49) after 149O.19.3's independent verification found
        # the original "READY FOR INDEPENDENT CONTRACT VERIFICATION" status
        # blocked on an under-bound frozen file set. The status text
        # necessarily changed; it must still explicitly disclaim VERIFIED.
        # Phase 149O.19.5E.1 (contract §50) then amended the contract again
        # (v1.0 -> v1.1, validator/admin implementation identity binding);
        # the status text changed again, still explicitly not VERIFIED.
        text = _contract_text()
        assert "not VERIFIED at v1.1" in text
        assert (
            "**Status:** FROZEN — VALIDATOR/ADMIN IMPLEMENTATION IDENTITY "
            "CONTRACT EVOLUTION COMPLETE — PENDING INDEPENDENT VERIFICATION "
            "(not VERIFIED at v1.1)"
            in text
        )

    def test_declares_dependency_on_unmodified_upstream_contracts(self):
        text = _contract_text()
        for dep in ("HMRC-001 v1.0", "HATP-001 v1.0", "HSCE-001 v1.1", "RAE-001 v1.0"):
            assert dep in text, f"missing dependency declaration: {dep}"

    def test_does_not_reuse_hmrc_001_numbering(self):
        text = _contract_text()
        assert "HMIC-001 is a new, standalone contract" in text
        assert "does not amend HMRC-001" in text


# ═══════════════════════════════════════════════════════════════════════════
# Requirement inventory, security invariants, attack matrix counts
# ═══════════════════════════════════════════════════════════════════════════


class TestRequirementAndInvariantCounts:
    def test_requirement_ids_sequential_no_gaps_no_duplicates(self):
        text = _contract_text()
        ids = sorted({int(m) for m in re.findall(r"HMIC-REQ-(\d{3})", text)})
        assert ids, "no HMIC-REQ-### requirement IDs found"
        assert ids[0] == 1, "requirement numbering must start at HMIC-REQ-001"
        expected = list(range(ids[0], ids[-1] + 1))
        assert ids == expected, "requirement IDs must be sequential with no gaps"

    def test_at_least_one_hundred_requirements(self):
        text = _contract_text()
        ids = {int(m) for m in re.findall(r"HMIC-REQ-(\d{3})", text)}
        assert len(ids) >= 100

    def test_civc_invariants_1_through_12_present_and_exact(self):
        text = _contract_text()
        for i in range(1, 13):
            assert re.search(rf"\bCIVC-{i}\b", text), f"missing CIVC-{i}"
        section = text.split("## 40. Security Invariants")[1]
        section = section.split("## 41.")[0]
        numbers = sorted(int(m) for m in re.findall(r"\*\*CIVC-(\d+)\.", section))
        assert numbers == list(range(1, 13))

    def test_attack_matrix_has_exactly_thirty_two_rows(self):
        text = _contract_text()
        section = text.split("## 41. Full Mandatory Attack Matrix")[1]
        section = section.split("## 42.")[0]
        rows = re.findall(r"^\|\s*(\d+)\s*\|", section, flags=re.MULTILINE)
        numbers = [int(r) for r in rows]
        assert numbers == list(range(1, 33)), (
            f"expected exactly 32 sequential attack rows, got {len(numbers)}: {numbers}"
        )

    def test_attack_matrix_covers_named_minimum_scenario_topics(self):
        text = _contract_text()
        section = text.split("## 41. Full Mandatory Attack Matrix")[1]
        section = section.split("## 42.")[0]
        for topic in (
            "PROJECT_STATUS",
            "phase-report",
            "test-suite output",
            "Environment variable",
            "CLI boolean flag",
            "Wrong-repository",
            "Wrong-deployment",
            "Old-implementation replay",
            "Dirty frozen file",
            "Contract-version replay",
            "Missing certification",
            "Corrupt certification",
            "Duplicate JSON keys",
            "Unknown/future schema version",
            "Symlinked",
            "Missing Active-Certification Pointer",
            "Corrupt Active-Certification Pointer",
            "Implicit-latest attempt",
            "Revoked active certification",
            "Concurrent revoke and activate",
            "certification writer",
            "alternate root injection",
            "import-shadowing",
            "Stale readiness token",
            "automatically activates",
        ):
            assert topic in section, f"attack matrix missing coverage for: {topic!r}"


# ═══════════════════════════════════════════════════════════════════════════
# Frozen file set: named paths exist on disk (existence, not byte-identity)
# ═══════════════════════════════════════════════════════════════════════════


class TestFrozenFileSetNamesExistingPaths:
    def test_contract_enumerates_exactly_these_src_relative_paths(self):
        text = _contract_text()
        section = text.split("## 17. Implementation Identity")[1]
        section = section.split("## 18.")[0]
        for relpath in _FROZEN_SRC_RELATIVE_PATHS:
            assert relpath in section, f"contract does not name frozen path: {relpath}"

    def test_frozen_src_relative_paths_exist(self):
        for relpath in _FROZEN_SRC_RELATIVE_PATHS:
            assert (_SRC / relpath).is_file(), f"frozen file does not exist: src/pcae/{relpath}"

    def test_frozen_contract_paths_exist(self):
        for relpath in _FROZEN_CONTRACT_REPO_RELATIVE_PATHS:
            assert (_REPO_ROOT / relpath).is_file(), f"frozen contract file does not exist: {relpath}"

    def test_frozen_file_set_has_exactly_twenty_two_entries(self):
        assert len(_FROZEN_SRC_RELATIVE_PATHS) + len(_FROZEN_CONTRACT_REPO_RELATIVE_PATHS) == 22


# ═══════════════════════════════════════════════════════════════════════════
# Contract binding set version headers still match what HMIC-001 froze
# ═══════════════════════════════════════════════════════════════════════════


class TestContractBindingSetVersionsStillCurrent:
    def _version_header(self, contract_repo_relative_path: str) -> str:
        text = (_REPO_ROOT / contract_repo_relative_path).read_text(encoding="utf-8")
        match = re.search(r"\*\*Version:\*\*\s*([0-9]+\.[0-9]+)", text)
        assert match, f"no version header found in {contract_repo_relative_path}"
        return match.group(1)

    def test_hmrc_001_version_matches_frozen_binding(self):
        assert self._version_header(
            "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
        ) == "1.0"

    def test_hatp_001_version_matches_frozen_binding(self):
        assert self._version_header(
            "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
        ) == "1.0"

    def test_hsce_001_version_matches_frozen_binding(self):
        assert self._version_header(
            "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
        ) == "1.1"

    def test_rae_001_version_matches_frozen_binding(self):
        assert self._version_header(
            "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"
        ) == "1.0"


# ═══════════════════════════════════════════════════════════════════════════
# Self-consistency: no implicit-latest, no partial credit, no self-cert path
# ═══════════════════════════════════════════════════════════════════════════


class TestContractSelfConsistency:
    def test_no_implicit_latest_language_asserted_as_the_rule(self):
        text = _contract_text()
        assert "SHALL NEVER list `certifications.json`, sort by `certified_at`" in text
        assert "no implicit-latest" in text.lower() or "no-implicit-latest" in text.lower()

    def test_no_valid_with_warning_partial_credit_status(self):
        text = _contract_text()
        assert "VALID_WITH_WARNING" in text  # named explicitly as a forbidden precedent
        assert "No `VALID_WITH_WARNING`" in text or "no `VALID_WITH_WARNING`" in text.lower() or (
            "No future implementation SHALL introduce a\n`VALID_WITH_WARNING`" in text
        )

    def test_readiness_mapping_is_binary_exactly_valid(self):
        text = _contract_text()
        assert (
            "mandatory_consumption_implementation_independently_verified = True` if\nand only if Validation Status is exactly `VALID`"
            in text
        )

    def test_certification_never_equals_activation(self):
        text = _contract_text()
        section = text.split("## 5. Semantic Walls")[1]
        section = section.split("## 6.")[0]
        assert "certification valid                          ≠  activation" in section

    def test_no_self_certification_path_statement_present(self):
        text = _contract_text()
        assert "No Self-Certification Path" in text
        assert "CIVC-12" in text

    def test_agent_write_api_explicitly_absent(self):
        text = _contract_text()
        assert "No production, agent-reachable API exposes" in text or (
            "No production,\nagent-reachable API exposes" in text
        )

    def test_certify_and_activate_kept_separate(self):
        text = _contract_text()
        section = text.split("## 35. Certification/Activation Independence")[1]
        section = section.split("## 36.")[0]
        assert "separate ceremonies" in section
        assert "never combined into one action" in section

    def test_pol005_and_comp002_unaffected(self):
        text = _contract_text()
        assert "POL-005" in text
        assert "COMP-002" in text
        normalized = " ".join(text.split())
        assert "does not amend, trigger, or interact with" in normalized

    def test_import_shadowing_limitation_named_not_hidden(self):
        text = _contract_text()
        assert "HMIC-REQ-063" in text
        assert "named, explicit limitation" in text.lower() or "named residual limitation" in text.lower()


# ═══════════════════════════════════════════════════════════════════════════
# No production or existing-contract change was made this phase
# ═══════════════════════════════════════════════════════════════════════════


class TestNoProductionOrExistingContractChange:
    def test_existing_contracts_untouched(self):
        for existing in (
            "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
            "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
            "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
            "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
            "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
            "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
            "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
        ):
            diff = _diff_since_entry(f"docs/contracts/{existing}")
            assert existing not in diff, f"{existing} was modified by this phase"

    def test_no_src_pcae_files_changed(self):
        diff = _diff_since_entry("src/pcae/")
        assert diff.strip() == "", f"production source changed this phase: {diff}"

    def test_no_certification_artifact_created_anywhere_in_repo(self):
        # This phase creates no certification state; a repo-local
        # certifications.json/certification-bindings.json anywhere under
        # the repository (which would itself violate HMIC-REQ-022's
        # protected-root-only rule) must not exist.
        matches = list(_REPO_ROOT.rglob("certifications.json")) + list(
            _REPO_ROOT.rglob("certification-bindings.json")
        )
        matches = [m for m in matches if ".git" not in m.parts]
        assert matches == [], f"unexpected certification-shaped file(s) found: {matches}"


# ═══════════════════════════════════════════════════════════════════════════
# Phase document sanity
# ═══════════════════════════════════════════════════════════════════════════


class TestPhaseDocument:
    def test_phase_doc_declares_contract_freeze_only(self):
        text = _phase_doc_text()
        assert "Contract-freeze only" in text

    def test_phase_doc_states_verdict(self):
        text = _phase_doc_text()
        assert "HMIC-001 v1.0: FROZEN — READY FOR INDEPENDENT CONTRACT VERIFICATION" in text

    def test_phase_doc_names_next_phase(self):
        text = _phase_doc_text()
        assert "149O.19.3" in text
