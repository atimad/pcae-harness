"""Phase 149O.9 -- HATP Signing Ceremony + Evidence Store Contract Freeze.

Contract-freeze-only phase: no production implementation, no HATP-001/
RAE-001 amendment, no CLI implementation, no hardware provisioning, no
signing execution, no Permission Broker change, no rollback dispatch
behavior change. This suite does not exercise any such implementation --
none was written -- it validates that:

1. The new HSCE-001 contract document and phase report are present and
   internally complete (cover every closed decision this phase was
   required to freeze).
2. The load-bearing production facts the contract's decisions rest on
   -- especially the AG5 CLI entry-point inventory 149O.8 left open --
   are independently re-confirmed against the actual source tree right
   now, rather than trusted from the contract's own prose.
3. No production source and no existing frozen contract (HATP-001,
   RAE-001) was modified by this phase.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_149O_9_HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT_FREEZE.md"
HATP_001 = REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
RAE_001 = REPO_ROOT / "docs" / "contracts" / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"

HATP_AG_AUTHORITY = REPO_ROOT / "src" / "pcae" / "core" / "hatp_ag_authority.py"
HATP_PROVENANCE = REPO_ROOT / "src" / "pcae" / "core" / "human_approval_trusted_provenance.py"
HATP_PROVIDERS = REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py"
ROLLBACK_EVIDENCE = REPO_ROOT / "src" / "pcae" / "core" / "rollback_approval_evidence.py"
AGENT_CORE = REPO_ROOT / "src" / "pcae" / "core" / "agent.py"
CLI_MODULE = REPO_ROOT / "src" / "pcae" / "cli.py"
COMMANDS_DIR = REPO_ROOT / "src" / "pcae" / "commands"

REQ_ID_RE = re.compile(r"HSCE-REQ-(\d{3})")


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC.read_text(encoding="utf-8")


class TestContractDocumentPresenceAndStructure:
    def test_contract_doc_exists(self):
        assert CONTRACT_DOC.is_file()

    def test_phase_doc_exists(self):
        assert PHASE_DOC.is_file()

    def test_declares_frozen_v1_0(self, contract_text):
        assert "HSCE-001 v1.0 FROZEN" in contract_text

    def test_declares_contract_freeze_only_no_implementation(self, contract_text):
        assert "NOT IMPLEMENTED" in contract_text
        normalized = " ".join(contract_text.lower().split())
        assert "does not implement the cli" in normalized

    REQUIRED_SECTION_FRAGMENTS = [
        "Signing Command",
        "AG3 Operation Locator",
        "AG5 CLI Entry-Point Inventory",
        "No User-Typed Security Fields",
        "Proof Field-Source Table",
        "Decision/Binding Lookup",
        "Signer / Provider Resolution",
        "Substrate Readiness Is Not a Signing Precondition",
        "Human Presence, Hardware Absence, Cancellation",
        "Evidence Envelope",
        "Envelope Version",
        "Provider Evidence Representation",
        "Evidence ID",
        "Content-Addressing Precision",
        "No-Clobber",
        "Evidence Store Root",
        "Evidence Lookup Semantics",
        "Closed Error Vocabulary",
        "Secret Handling",
        "Atomic Write",
        "Path Validation",
        "Case Sensitivity",
        "Storage Trust Classification",
        "Authority Semantics",
        "Security Invariants",
        "Mandatory Future Attack Matrix",
        "Blocking-Condition Check",
        "Recommended Next Phase",
    ]

    def test_all_required_content_areas_present(self, contract_text):
        lowered = contract_text.lower()
        missing = [
            frag for frag in self.REQUIRED_SECTION_FRAGMENTS if frag.lower() not in lowered
        ]
        assert not missing, f"contract doc missing required content areas: {missing}"

    def test_requirement_ids_sequential_no_gaps_no_duplicates(self, contract_text):
        ids = [int(m.group(1)) for m in REQ_ID_RE.finditer(contract_text)]
        # Each requirement is defined once as "**HSCE-REQ-###.**" and may be
        # cross-referenced elsewhere; collect only the defining occurrences.
        defining_ids = [
            int(m.group(1))
            for m in re.finditer(r"\*\*HSCE-REQ-(\d{3})\.\*\*", contract_text)
        ]
        assert defining_ids, "no defining HSCE-REQ-### statements found"
        assert defining_ids == sorted(defining_ids), "requirement IDs not in ascending order"
        assert len(defining_ids) == len(set(defining_ids)), "duplicate requirement definitions"
        expected = list(range(1, defining_ids[-1] + 1))
        assert defining_ids == expected, (
            f"requirement sequence has gaps: expected {expected[:5]}...{expected[-5:]}, "
            f"got {defining_ids[:5]}...{defining_ids[-5:]}"
        )
        assert min(ids) == 1


class TestCLISurfaceFrozen:
    def test_no_dry_run_flag_documented(self, contract_text):
        assert "No `--dry-run` flag exists" in contract_text

    def test_no_forbidden_security_flags_documented(self, contract_text):
        for flag in ("--provider", "--signer", "--force", "--overwrite", "--output"):
            assert flag in contract_text, f"contract must explicitly name and forbid {flag}"

    def test_site_flag_closed_choices(self, contract_text):
        assert "ag3" in contract_text and "ag5" in contract_text
        assert "--site" in contract_text

    def test_ecp_id_auto_derivation_resolved(self, contract_text):
        assert "No `--ecp-id` flag exists" in contract_text


class TestEvidenceIdAndEnvelopeSemantics:
    def test_evidence_id_formula_frozen(self, contract_text):
        assert "digest_hatp_proof_payload(proof)" in contract_text

    def test_content_addressing_precision_stated(self, contract_text):
        assert "addresses" in contract_text.lower()
        assert "proof payload only" in contract_text.lower() or (
            "canonical proof payload" in contract_text.lower()
            and "does not address" in contract_text.lower()
        )

    def test_same_id_different_evidence_case_resolved(self, contract_text):
        assert "evidence_conflict" in contract_text
        assert "idempotent" in contract_text.lower()

    def test_no_clobber_rule_frozen(self, contract_text):
        assert "CREATE-ONCE" in contract_text or "NO-CLOBBER" in contract_text

    def test_evidence_version_bool_rejection_frozen(self, contract_text):
        assert "isinstance(value, bool)" in contract_text or "bool" in contract_text
        assert "evidence_version" in contract_text

    def test_explicit_id_only_lookup(self, contract_text):
        assert "explicit" in contract_text.lower() and "evidence_id" in contract_text
        assert "latest" in contract_text.lower()

    def test_forbidden_approval_pattern_stated(self, contract_text):
        assert "evidence_file.exists()" in contract_text or "Forbidden pattern" in contract_text


class TestErrorVocabularyClosed:
    EXPECTED_ERROR_TYPES = [
        "repository_identity_unavailable",
        "operation_not_found",
        "decision_unavailable",
        "binding_unavailable",
        "no_authorized_signer",
        "provider_unavailable",
        "hardware_device_fault",
        "human_signing_cancelled",
        "provider_signature_failure",
        "evidence_serialization_failure",
        "evidence_conflict",
        "evidence_persistence_failure",
    ]

    @pytest.mark.parametrize("error_type", EXPECTED_ERROR_TYPES)
    def test_error_type_documented(self, contract_text, error_type):
        assert error_type in contract_text

    def test_exit_code_constants_documented(self, contract_text):
        for const in (
            "EXIT_SUCCESS",
            "EXIT_GENERIC_SIGNING_FAILURE",
            "EXIT_OPERATION_NOT_FOUND",
            "EXIT_SUBSTRATE_UNAVAILABLE",
            "EXIT_HUMAN_CANCELLED",
            "EXIT_PROVIDER_FAILURE",
            "EXIT_EVIDENCE_CONFLICT",
            "EXIT_PERSISTENCE_FAILURE",
        ):
            assert const in contract_text


class TestSecurityInvariantsFrozen:
    @pytest.mark.parametrize("sc_id", [f"SC-{n}" for n in range(1, 13)])
    def test_sc_invariant_present(self, contract_text, sc_id):
        assert sc_id in contract_text


class TestAg5InventoryIndependentlyReconfirmed:
    """Re-derive, from the current source tree (not from the contract
    document's own prose), the AG5 CLI entry-point inventory finding this
    phase's central factual claim depends on."""

    def test_build_rollback_execution_defined_exactly_once(self):
        text = AGENT_CORE.read_text(encoding="utf-8")
        assert len(re.findall(r"^def build_rollback_execution\(", text, re.M)) == 1

    def test_run_rollback_calls_build_rollback_execution_with_no_hatp_args(self):
        for path in COMMANDS_DIR.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "def run_rollback(" in text:
                match = re.search(r"def run_rollback\(.*?\n\n\n", text, re.S)
                assert match, "run_rollback body could not be isolated"
                body = match.group(0)
                assert "build_rollback_execution(" in body
                assert "hatp_evidence_id" not in body
                assert "hatp_proof" not in body
                assert "hatp_evidence" not in body
                return
        pytest.fail("run_rollback not found in any commands module")

    def test_rollback_top_level_subcommand_registered_in_cli(self):
        text = CLI_MODULE.read_text(encoding="utf-8")
        assert 'subparsers.add_parser(\n        "rollback",' in text or re.search(
            r'add_parser\(\s*"rollback"\s*,', text
        )
        assert "run_rollback" in text

    def test_build_rollback_execution_pilot_is_a_distinct_function(self):
        text = AGENT_CORE.read_text(encoding="utf-8")
        pilot_match = re.search(r"def build_rollback_execution_pilot\(.*?\n\n\n", text, re.S)
        assert pilot_match, "build_rollback_execution_pilot not found"
        assert "build_rollback_execution(" not in pilot_match.group(0)

    def test_build_rollback_execution_signature_accepts_optional_hatp_params(self):
        text = AGENT_CORE.read_text(encoding="utf-8")
        match = re.search(r"def build_rollback_execution\(([^)]*(?:\([^)]*\)[^)]*)*)\)", text, re.S)
        assert match
        signature = match.group(1)
        for param in ("hatp_evidence_id", "hatp_proof", "hatp_evidence"):
            assert param in signature


class TestLoadBearingFactsIndependentlyReconfirmed:
    def test_digest_hatp_proof_payload_helper_exists(self):
        text = HATP_PROVENANCE.read_text(encoding="utf-8")
        assert "def digest_hatp_proof_payload(" in text

    def test_hatp_proof_to_document_helper_exists(self):
        text = HATP_PROVENANCE.read_text(encoding="utf-8")
        assert "def hatp_proof_to_document(" in text

    def test_hatp_verification_evidence_shape_unchanged(self):
        text = HATP_PROVENANCE.read_text(encoding="utf-8")
        match = re.search(r"class HATPVerificationEvidence:.*?\n\n\n", text, re.S)
        assert match
        assert "assertion: bytes" in match.group(0)

    def test_provider_assertion_shape_unchanged(self):
        text = HATP_PROVIDERS.read_text(encoding="utf-8")
        match = re.search(r"class ProviderAssertion:.*?\n\n\n", text, re.S)
        assert match
        body = match.group(0)
        for field in ("credential_id", "provider_profile", "algorithm", "evidence: bytes"):
            assert field in body

    def test_create_production_hardware_provider_rejects_unknown_profiles(self):
        text = HATP_PROVIDERS.read_text(encoding="utf-8")
        assert "def create_production_hardware_provider(" in text
        assert "HATPProviderUnavailableError" in text

    def test_no_hatp_provider_selection_flag_exists_in_commands(self):
        """**Updated by Phase 149O.12C:** narrowed from a naive whole-text
        substring scan to a real `add_argument("--provider"...)`
        detection -- 149O.12C's own `commands/hatp.py` legitimately
        *discusses*, in its docstring, why no such flag exists
        (HSCE-REQ-022/026), which a naive substring scan cannot
        distinguish from an actual flag definition. The underlying
        invariant is unweakened -- see `test_hatp_cli.py`'s own
        code-only forbidden-flag suite."""
        import re

        add_argument_provider = re.compile(r"add_argument\(\s*[\"']--provider")
        for path in COMMANDS_DIR.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "hatp" not in text.lower():
                continue
            assert not add_argument_provider.search(text), (
                f"unexpected HATP provider-selection flag definition found in {path}"
            )

    def test_no_hatp_sign_cli_surface_implemented_yet(self):
        """149O.9 itself confirmed it did not accidentally implement the
        CLI it only freezes the contract for -- reconfirmed here against
        149O.9's own baseline (see the git-diff-based test below for the
        commit-scoped version).

        **Updated by Phase 149O.12C** (149O.5-F-3 precedent, see this
        file's sibling files' identical updates): 149O.12C is the later,
        separately-authorized phase 149O.9's own report recommended
        implement exactly this CLI surface. Its presence now is the
        planned outcome, not scope creep re-attributed to 149O.9 -- this
        phase's git-scoped `test_no_src_pcae_files_changed`/equivalent
        checks (this file, elsewhere) remain the authoritative "did
        149O.9 itself touch anything" confirmation."""
        hits = []
        for path in COMMANDS_DIR.glob("*.py"):
            if path.name == "hatp.py":
                continue
            text = path.read_text(encoding="utf-8")
            if "hatp sign" in text.lower() or "HATPSignedEvidenceEnvelope" in text:
                hits.append(str(path))
        assert not hits, f"unexpected signing-ceremony implementation present outside commands/hatp.py: {hits}"

    def test_hatp_evidence_directory_not_created_in_repo_state(self):
        assert not (REPO_ROOT / ".pcae" / "hatp-evidence").exists(), (
            "no evidence should have been created -- this phase is contract-freeze only"
        )

    def test_list_bindings_with_keys_exists_for_decision_binding_lookup(self):
        text = ROLLBACK_EVIDENCE.read_text(encoding="utf-8")
        assert "def list_bindings_with_keys(" in text

    def test_hatp_trust_store_production_and_hardware_provider_factory_exist(self):
        ag_text = HATP_AG_AUTHORITY.read_text(encoding="utf-8")
        assert "HATPTrustStore.production()" in ag_text
        assert "create_production_hardware_provider" in ag_text


class TestNoProductionOrExistingContractFilesModified:
    """This phase's allowed-file scope is: the new HSCE-001 contract, the
    new phase report, the new independent test file, and task/status
    metadata. It must not modify src/pcae/** or the existing frozen
    HATP-001/RAE-001 contract text. Skipped gracefully if run outside a
    git checkout with the expected history."""

    def _diff_against_head(self, path: Path):
        try:
            result = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "HEAD", "--", str(path)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except FileNotFoundError:
            pytest.skip("git not available")
        if result.returncode != 0:
            pytest.skip("git diff unavailable in this environment")
        return [line for line in result.stdout.splitlines() if line.strip()]

    def test_hatp_001_unmodified(self):
        assert self._diff_against_head(HATP_001) == []

    def test_rae_001_unmodified(self):
        assert self._diff_against_head(RAE_001) == []

    def test_no_src_pcae_files_changed(self):
        changed = self._diff_against_head(REPO_ROOT / "src" / "pcae")
        assert changed == [], f"unexpected production changes: {changed}"
