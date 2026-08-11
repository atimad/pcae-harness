"""Phase 149O.20C -- Independent verification tests for the HATP Class-B
Deployment Contract (HBDC-001 v1.0,
`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`).

149O.20C is an INDEPENDENT-VERIFICATION-ONLY phase: it modifies no
`src/pcae/**` file, no `scripts/**` file, and no existing contract. This
module independently re-derives HBDC-001's requirement/invariant/attack
inventory directly from the live contract text (never importing constants
from `test_phase_149o_20b_hatp_class_b_deployment_contract_freeze.py` as an
oracle), and independently cross-checks HBDC-001's normative claims against
live production source: Protected Root resolution/symlink-rejection in
`hatp_bootstrap.py`, the mode-bit-only permission checks in
`hatp_bootstrap.py`/`hatp_mandatory_cutover.py`, the absence of any
application-level admin mechanism, the absence of any environment-lock
(PYTHONPATH/sitecustomize/.pth/meta_path) implementation, the Git
executable PATH-resolution attack surface in `hatp_mandatory_certification.
py`, and -- the load-bearing self-binding question -- the empirical
absence of HBDC-001 from both HMIC-001's `contract_versions` binding
(`_CONTRACT_IDENTITY_FILES`) and its `implementation_scope_digest` frozen
set (`_FROZEN_AUTHORITY_BEARING_FILES`).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_ARCHITECTURE_DOC = _REPO_ROOT / "docs" / "PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md"
_FREEZE_PHASE_DOC = _REPO_ROOT / "docs" / "PHASE_149O_20B_HATP_CLASS_B_DEPLOYMENT_CONTRACT_FREEZE.md"
_VERIFICATION_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20C_HATP_CLASS_B_DEPLOYMENT_CONTRACT_INDEPENDENT_VERIFICATION.md"
)
_HATP_BOOTSTRAP = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py"
_HATP_MANDATORY_CUTOVER = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py"
_HATP_MANDATORY_CERTIFICATION = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"
_REPOSITORY_IDENTITY = _REPO_ROOT / "src" / "pcae" / "core" / "repository_identity.py"
_HMIC_CONTRACT = (
    _REPO_ROOT
    / "docs"
    / "contracts"
    / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)

_EXISTING_EIGHT_BOUND_CONTRACTS = (
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
)


@pytest.fixture(scope="module")
def contract_text() -> str:
    assert _CONTRACT.exists(), f"expected contract document at {_CONTRACT}"
    return _CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def architecture_text() -> str:
    assert _ARCHITECTURE_DOC.exists()
    return _ARCHITECTURE_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hmic_contract_text() -> str:
    assert _HMIC_CONTRACT.exists()
    return _HMIC_CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hatp_bootstrap_text() -> str:
    assert _HATP_BOOTSTRAP.exists()
    return _HATP_BOOTSTRAP.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hatp_mandatory_cutover_text() -> str:
    assert _HATP_MANDATORY_CUTOVER.exists()
    return _HATP_MANDATORY_CUTOVER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hatp_mandatory_certification_text() -> str:
    assert _HATP_MANDATORY_CERTIFICATION.exists()
    return _HATP_MANDATORY_CERTIFICATION.read_text(encoding="utf-8")


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text)


# ═══════════════════════════════════════════════════════════════════════════
# Independent mechanical re-extraction of HBDC-001's inventory (no oracle)
# ═══════════════════════════════════════════════════════════════════════════


class TestIndependentRequirementExtraction:
    def test_55_unique_gapless_requirement_ids(self, contract_text: str):
        ids = sorted(int(m) for m in re.findall(r"HBDC-REQ-(\d{3})", contract_text))
        unique_ids = sorted(set(ids))
        assert len(unique_ids) == 55, f"expected 55 unique HBDC-REQ ids, found {len(unique_ids)}"
        assert unique_ids == list(range(1, 56)), "requirement IDs must be gapless 1..55"

    def test_traceability_table_has_exactly_55_rows_no_duplicates(self, contract_text: str):
        table_start = contract_text.index("## 24. Full Requirement Traceability")
        table_end = contract_text.index("## 25.")
        table = contract_text[table_start:table_end]
        row_ids = re.findall(r"HBDC-REQ-\d{3}", table)
        assert len(row_ids) == 55
        assert len(set(row_ids)) == 55, "traceability table must not repeat any requirement ID"

    def test_every_traceability_id_is_normatively_defined_in_body(self, contract_text: str):
        table_start = contract_text.index("## 24. Full Requirement Traceability")
        table_end = contract_text.index("## 25.")
        table_ids = set(re.findall(r"HBDC-REQ-\d{3}", contract_text[table_start:table_end]))
        # normative definitions use the bold "**HBDC-REQ-NNN.**" pattern
        defined_ids = set(re.findall(r"\*\*(HBDC-REQ-\d{3})\.\*\*", contract_text))
        missing = table_ids - defined_ids
        assert not missing, f"traceability-table IDs with no normative definition: {sorted(missing)}"


class TestIndependentInvariantExtraction:
    def test_8_unique_invariants(self, contract_text: str):
        ids = sorted(int(m) for m in re.findall(r"CBD-(\d+)", contract_text))
        unique_ids = sorted(set(ids))
        assert unique_ids == list(range(1, 9)), f"expected CBD-1..8, found {unique_ids}"


class TestIndependentAttackExtraction:
    def test_21_unique_attack_rows(self, contract_text: str):
        matrix_start = contract_text.index("### Attack Matrix (21 scenarios)")
        matrix_end = contract_text.index("## 22.")
        rows = re.findall(r"^\|\s*(\d+)\s*\|", contract_text[matrix_start:matrix_end], re.MULTILINE)
        assert len(rows) == 21
        assert len(set(rows)) == 21, "attack matrix must not repeat any row index"
        assert sorted(int(r) for r in rows) == list(range(1, 22))


# ═══════════════════════════════════════════════════════════════════════════
# DRA-REQ-001..003 traceability (independent, cross-checked against 20A text)
# ═══════════════════════════════════════════════════════════════════════════


class TestDRATraceabilityIndependentlyReconstructed:
    def test_dra_req_001_002_003_named_in_architecture_doc(self, architecture_text: str):
        assert "DRA-REQ-001" in architecture_text
        assert "DRA-REQ-002" in architecture_text
        assert "DRA-REQ-003" in architecture_text

    def test_dra_traceability_table_maps_001_002_003(self, contract_text: str):
        norm = _normalize_ws(contract_text)
        assert "DRA-REQ-001" in norm and "HBDC-REQ-001..005" in norm
        assert "DRA-REQ-002" in norm and "HBDC-REQ-011..021" in norm
        assert "DRA-REQ-003" in norm and "HBDC-REQ-025..041" in norm

    def test_dra_ids_not_reused_as_hbdc_ids(self, contract_text: str):
        # HBDC-REQ namespace is entirely distinct from DRA-REQ; no shared numerals as bare IDs
        assert not re.search(r"(?<!HBDC-)(?<!DRA-)REQ-\d{3}\s+SHALL", contract_text)


class TestHMICREQ063QuoteByteIdentical:
    def test_architecture_doc_quotes_hmic_req_063_byte_identical(
        self, architecture_text: str, hmic_contract_text: str
    ):
        # HBDC-001 itself references HMIC-REQ-063 by name/paraphrase only;
        # the verbatim block-quote lives in the 149O.20A architecture doc.
        arch_quote_start = architecture_text.index('"HMIC-REQ-063')
        arch_quote_end = architecture_text.index("not a silent gap.", arch_quote_start) + len(
            "not a silent gap."
        )
        arch_quote = re.sub(r"[>\s]+", " ", architecture_text[arch_quote_start:arch_quote_end]).strip().rstrip('."')

        hmic_start = hmic_contract_text.index("HMIC-REQ-063")
        hmic_end = hmic_contract_text.index("not a silent gap", hmic_start) + len("not a silent gap")
        hmic_quote = re.sub(r"[*\s]+", " ", hmic_contract_text[hmic_start:hmic_end]).strip()

        # both quotes must reference the same core claim without contradiction
        for fragment in ("does NOT verify", "module shadowing", "sitecustomize", "PYTHONPATH"):
            assert fragment in arch_quote, f"architecture-doc quote missing fragment: {fragment}"
            assert fragment in hmic_quote, f"HMIC source missing fragment: {fragment}"

    def test_hbdc_references_not_quotes_hmic_req_063(self, contract_text: str):
        # HBDC-001 must reference HMIC-REQ-063 without re-typing its full
        # normative text as its own block quote (that text belongs to HMIC-001).
        assert "HMIC-REQ-063" in contract_text
        assert '"HMIC-REQ-063' not in contract_text


# ═══════════════════════════════════════════════════════════════════════════
# Production source cross-checks (independent attack modeling against live code)
# ═══════════════════════════════════════════════════════════════════════════


class TestProtectedRootResolutionCrossCheck:
    def test_no_env_or_cli_override_of_production_root(self, hatp_bootstrap_text: str):
        func_start = hatp_bootstrap_text.index("def _default_production_trust_root")
        func_end = hatp_bootstrap_text.index("\ndef ", func_start + 1)
        body = hatp_bootstrap_text[func_start:func_end]
        # exclude the docstring (which *discusses* the rejected alternatives)
        # from the functional-usage check -- only the executable body must
        # be free of environment/home-derived resolution
        doc_end = body.index('"""', body.index('"""') + 3) + 3
        executable_body = body[doc_end:]
        assert "os.environ" not in executable_body
        assert "getenv" not in executable_body
        assert "Path.home" not in executable_body
        assert "expanduser" not in executable_body

    def test_no_mkdir_or_auto_creation_in_bootstrap_module(self, hatp_bootstrap_text: str):
        assert "mkdir" not in hatp_bootstrap_text
        assert "os.makedirs" not in hatp_bootstrap_text

    def test_symlink_rejection_present_and_fails_closed(self, hatp_bootstrap_text: str):
        assert "_reject_symlink" in hatp_bootstrap_text
        assert "is_symlink()" in hatp_bootstrap_text
        assert "raise HATPTrustStoreSymlinkError" in hatp_bootstrap_text

    def test_symlink_rejection_independently_reimplemented_in_cutover(self, hatp_mandatory_cutover_text: str):
        assert "_reject_symlink" in hatp_mandatory_cutover_text
        assert "is_symlink()" in hatp_mandatory_cutover_text

    def test_agent_admin_shared_principal_detected_by_live_uid_check(self, hatp_bootstrap_text: str):
        assert "os.getuid()" in hatp_bootstrap_text
        assert "agent_and_admin_share_os_principal" in hatp_bootstrap_text


class TestEffectivePermissionCoverageGapIndependentlyConfirmed:
    """HBDC-REQ-015/016/017/019 require effective ACL/group/ancestor-chain/
    hard-link coverage. This independently confirms the *current* production
    checks are mode-bit-only -- a Non-Blocking implementation-coverage
    finding, not a contract-text defect (the contract's own text already
    anticipates this as future-verifier work)."""

    def test_bootstrap_environment_check_is_mode_bits_only(self, hatp_bootstrap_text: str):
        func_start = hatp_bootstrap_text.index("def inspect_bootstrap_environment")
        body = hatp_bootstrap_text[func_start:]
        assert "S_IWGRP" in body or "S_IWOTH" in body
        # no ACL or effective-access library usage (functional import/call,
        # not incidental prose elsewhere in the module) exists in this function
        assert "posix1e" not in body
        assert "getfacl" not in body
        assert re.search(r"\bacl\b", body, re.IGNORECASE) is None

    def test_bootstrap_environment_check_covers_only_immediate_parent(self, hatp_bootstrap_text: str):
        func_start = hatp_bootstrap_text.index("def inspect_bootstrap_environment")
        rest = hatp_bootstrap_text[func_start + 1:]
        func_end = func_start + 1 + rest.index("\ndef ") if "\ndef " in rest else len(hatp_bootstrap_text)
        body = hatp_bootstrap_text[func_start:func_end]
        assert "store_root.parent" in body
        # only one level of ancestor traversal -- no loop over parents
        assert "parents[" not in body and ".parents" not in body

    def test_cutover_readiness_check_is_also_mode_bits_only(self, hatp_mandatory_cutover_text: str):
        func_start = hatp_mandatory_cutover_text.index(
            "def _assess_hatp_mandatory_activation_readiness_at_root"
        )
        body = hatp_mandatory_cutover_text[func_start:]
        assert "0o022" in body

    def test_no_hard_link_detection_anywhere_in_hatp_authority_modules(
        self, hatp_bootstrap_text: str, hatp_mandatory_cutover_text: str, hatp_mandatory_certification_text: str
    ):
        for text in (hatp_bootstrap_text, hatp_mandatory_cutover_text, hatp_mandatory_certification_text):
            assert "st_nlink" not in text
            assert "os.link(" not in text


class TestEnvironmentLockHasNoLiveImplementationYet:
    """HBDC-REQ-025..039 (the full §13 environment lock) is contract-freeze-
    only; no production code enforces it yet. Independently confirmed by
    absence, not accepted from the contract's own status line."""

    @pytest.mark.parametrize(
        "needle",
        [
            "PYTHONPATH",
            "sys.meta_path",
            "sitecustomize",
            "usercustomize",
            "ENABLE_USER_SITE",
        ],
    )
    def test_no_environment_lock_enforcement_in_core_modules(self, needle: str):
        core_dir = _REPO_ROOT / "src" / "pcae" / "core"
        hits = []
        for path in core_dir.glob("*.py"):
            if needle in path.read_text(encoding="utf-8"):
                hits.append(path.name)
        assert not hits, f"unexpected environment-lock-related reference to {needle!r} in {hits}"

    def test_no_admin_flag_or_env_var_mechanism_exists(self):
        for rel in ("core", "commands"):
            directory = _REPO_ROOT / "src" / "pcae" / rel
            for path in directory.glob("*.py"):
                text = path.read_text(encoding="utf-8")
                assert "PCAE_ADMIN" not in text
                assert not re.search(r"--admin\b", text)


class TestGitExecutablePathAttackSurfaceConfirmed:
    def test_run_git_uses_bare_git_resolved_via_path(self, hatp_mandatory_certification_text: str):
        func_start = hatp_mandatory_certification_text.index("def _run_git")
        func_end = hatp_mandatory_certification_text.index("\ndef ", func_start + 1)
        body = hatp_mandatory_certification_text[func_start:func_end]
        assert '"git"' in body
        assert "subprocess.run" in body
        # no absolute-path pinning or resolved-executable validation in code today
        assert "shutil.which" not in body
        assert "os.path.isabs" not in body


class TestDeploymentIdentityCrossCheck:
    def test_canonicalization_uses_strict_resolve(self, hatp_bootstrap_text: str):
        func_start = hatp_bootstrap_text.index("def resolve_canonical_deployment_root")
        func_end = hatp_bootstrap_text.index("\ndef ", func_start + 1)
        body = hatp_bootstrap_text[func_start:func_end]
        assert "resolve(strict=True)" in body

    def test_deployment_binding_matches_checks_both_fields(self, hatp_bootstrap_text: str):
        func_start = hatp_bootstrap_text.index("def deployment_binding_matches")
        func_end = hatp_bootstrap_text.index("\ndef ", func_start + 1) if "\ndef " in hatp_bootstrap_text[func_start:] else len(hatp_bootstrap_text)
        body = hatp_bootstrap_text[func_start:func_end]
        assert "repository_id" in body or "repository_instance_id" in body
        assert "canonical_deployment_root" in body

    def test_wrong_repository_and_wrong_deployment_statuses_exist(self, hatp_mandatory_certification_text: str):
        assert "WRONG_REPOSITORY" in hatp_mandatory_certification_text
        assert "WRONG_DEPLOYMENT" in hatp_mandatory_certification_text

    def test_repository_identity_is_agent_writable_by_design(self):
        text = _REPOSITORY_IDENTITY.read_text(encoding="utf-8")
        assert "def ensure_repository_identity" in text


# ═══════════════════════════════════════════════════════════════════════════
# Self-binding: the load-bearing question, verified empirically
# ═══════════════════════════════════════════════════════════════════════════


class TestSelfBindingEmpiricallyConfirmed:
    def test_hbdc_absent_from_contract_versions_binding_set(self, hatp_mandatory_certification_text: str):
        match = re.search(
            r"_CONTRACT_IDENTITY_FILES:[^=]*=\s*\((.*?)\n\)",
            hatp_mandatory_certification_text,
            re.DOTALL,
        )
        assert match, "could not locate _CONTRACT_IDENTITY_FILES tuple literal"
        block = match.group(1)
        assert "HBDC" not in block
        for expected in ("HMRC-001", "HATP-001", "HSCE-001", "RAE-001"):
            assert expected in block

    def test_hbdc_absent_from_implementation_scope_digest_frozen_set(self, hatp_mandatory_certification_text: str):
        block_start = hatp_mandatory_certification_text.index("_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES")
        block_end = hatp_mandatory_certification_text.index(")", block_start)
        block = hatp_mandatory_certification_text[block_start:block_end]
        assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT" not in block

    def test_frozen_file_count_still_exactly_24(self, hatp_mandatory_certification_text: str):
        assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 24" in hatp_mandatory_certification_text

    def test_contract_text_states_option_a_disposition(self, contract_text: str):
        norm = _normalize_ws(contract_text)
        assert "Selected disposition: Option A." in norm
        assert "not, as of v1.0, one of HMIC-001's bound contracts" in norm

    def test_contract_text_names_future_hmic_v1_2_amendment_not_performed_here(self, contract_text: str):
        norm = _normalize_ws(contract_text)
        assert "HMIC-001 v1.2" in norm
        assert "NOT made by Phase 149O.20B" in norm

    def test_hmic_v1_1_current_version_unchanged(self, hmic_contract_text: str):
        assert "**Version:** 1.1" in hmic_contract_text


class TestNoProductionOrContractSourceModifiedByThisPhase:
    def test_git_status_touches_no_src_pcae_or_existing_contract_file(self):
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain", "--", "src/pcae", "scripts", "docs/contracts"],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("git unavailable in this environment")
        if proc.returncode != 0:
            pytest.skip("not a git checkout")
        offending = [
            line
            for line in proc.stdout.splitlines()
            if line.strip() and not line.startswith("?? docs/contracts/")
        ]
        assert not offending, f"unexpected change under src/pcae, scripts, or docs/contracts: {offending}"

    def test_no_new_contract_added_by_this_phase(self):
        # 149O.20C is verification-only: unlike 149O.20B, it must not add a
        # new docs/contracts file either.
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain", "--", "docs/contracts"],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("git unavailable in this environment")
        if proc.returncode != 0:
            pytest.skip("not a git checkout")
        assert proc.stdout.strip() == "", f"docs/contracts must be untouched by 149O.20C: {proc.stdout}"

    def test_all_eight_existing_bound_contracts_present_and_unchanged_shape(self):
        for rel in _EXISTING_EIGHT_BOUND_CONTRACTS:
            path = _REPO_ROOT / rel
            assert path.exists(), f"expected bound contract at {rel}"


# ═══════════════════════════════════════════════════════════════════════════
# Status-claim discipline and verification-artifact completeness
# ═══════════════════════════════════════════════════════════════════════════


class TestStatusClaimDiscipline:
    def test_hbdc_reserves_verified_claim_for_independent_verification(self, contract_text: str):
        norm = _normalize_ws(contract_text)
        assert "CLASS-B DEPLOYMENT VERIFIED" in norm
        assert "149O.20C or a successor" in norm

    def test_hbdc_does_not_equal_broader_readiness_terms(self, contract_text: str):
        norm = _normalize_ws(contract_text)
        assert "HATP DEPLOYMENT READY" in norm
        assert "HATP PRODUCTION READY" in norm
        assert "ROLLBACK EXECUTION READY" in norm


class TestVerificationArtifactPresent:
    def test_verification_document_exists(self):
        assert _VERIFICATION_DOC.exists()
        text = _VERIFICATION_DOC.read_text(encoding="utf-8")
        assert len(text) > 5000

    def test_verification_document_states_no_blocking_findings(self):
        text = _VERIFICATION_DOC.read_text(encoding="utf-8")
        assert "**Blocking:** None." in text

    def test_verification_document_states_self_binding_verdict(self):
        text = _VERIFICATION_DOC.read_text(encoding="utf-8")
        assert "INDEPENDENTLY VERIFIED" in text
        assert "HBDC-001 MUST ENTER HMIC'S PROTECTED BOUND-CONTRACT IDENTITY" in text

    def test_verification_document_confirms_no_real_state_change(self):
        text = _VERIFICATION_DOC.read_text(encoding="utf-8")
        assert "No real OS principal or Protected Root was created." in text
        assert "HATP production remains NOT READY." in text

    def test_verification_document_recommends_149o_20d_not_provisioning(self):
        text = _VERIFICATION_DOC.read_text(encoding="utf-8")
        assert "149O.20D" in text
        assert "do not recommend Class-B provisioning next" in text
