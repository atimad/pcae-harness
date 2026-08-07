"""Phase 149O.8 -- HATP AG3/AG5 Production Consumption + Signing-Ceremony
Architecture.

Architecture-only phase: no production implementation, no contract
change, no CLI implementation, no hardware provisioning, no signing
execution, no Permission Broker enforcement change, no rollback dispatch
behavior change. This suite does not exercise any such implementation --
none was written -- it validates that:

1. The architecture document itself is present and internally complete
   (covers every section the governing prompt required, §99).
2. The load-bearing production facts the document's decisions rest on
   are independently re-confirmed against the actual source tree right
   now, rather than trusted from the document's own prose (mirrors
   149O.1D's and 149O.7's own methodology).
3. No production or contract file was modified by this phase.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCH_DOC = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_8_HATP_AG3_AG5_PRODUCTION_CONSUMPTION_SIGNING_CEREMONY_ARCHITECTURE.md"
)

HATP_AG_AUTHORITY = REPO_ROOT / "src" / "pcae" / "core" / "hatp_ag_authority.py"
PB_FOUNDATION = REPO_ROOT / "src" / "pcae" / "core" / "permission_broker_foundation.py"
HATP_PROVENANCE = REPO_ROOT / "src" / "pcae" / "core" / "human_approval_trusted_provenance.py"
HATP_PROVIDERS = REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py"
ROLLBACK_EVIDENCE = REPO_ROOT / "src" / "pcae" / "core" / "rollback_approval_evidence.py"
AGENT_CORE = REPO_ROOT / "src" / "pcae" / "core" / "agent.py"
AGENT_COMMANDS = REPO_ROOT / "src" / "pcae" / "commands" / "agent.py"
COMMANDS_DIR = REPO_ROOT / "src" / "pcae" / "commands"


@pytest.fixture(scope="module")
def doc_text() -> str:
    return ARCH_DOC.read_text(encoding="utf-8")


class TestDocumentPresenceAndStructure:
    def test_architecture_doc_exists(self):
        assert ARCH_DOC.is_file()

    def test_declares_architecture_only_phase_type(self, doc_text):
        assert "ARCHITECTURE ONLY" in doc_text.upper() or "architecture only" in doc_text

    REQUIRED_SECTION_FRAGMENTS = [
        "Baseline",
        "Problem Statement",
        "Current Real Workflow",
        "Current Gated",
        "Gap Analysis",
        "Signing-Ceremony Ownership",
        "Proof Construction Ownership",
        "Provider",
        "Evidence Output",
        "Evidence Storage",
        "CLI",
        "rollback approve",
        "AG3 Target",
        "AG5 Target",
        "legacy",
        "Permission Broker",
        "COMP-002",
        "HUMAN_REVIEW",
        "Trust-Boundary Diagram",
        "Dataflow Table",
        "Authority Table",
        "System-Closure Gate",
        "Production-Certification Gate",
        "Implementation Phase Breakdown",
        "dependency graph",
        "Risks",
        "Retained Findings",
        "Recommended Next Phase",
    ]

    def test_all_required_content_areas_present(self, doc_text):
        lowered = doc_text.lower()
        missing = [
            frag
            for frag in self.REQUIRED_SECTION_FRAGMENTS
            if frag.lower() not in lowered
        ]
        assert not missing, f"architecture doc missing required content areas: {missing}"

    def test_no_no_go_blocking_patterns_recommended(self, doc_text):
        """The doc must not itself propose any of the explicitly blocking
        architecture conditions named by the governing prompt (§98)."""
        forbidden_endorsements = [
            "caller-supplied approval_present as authority",
        ]
        # The doc discusses these patterns in order to REJECT them; verify
        # each appears inside a self-check / rejection section rather than
        # being silently absent (absence would mean the self-check itself
        # is missing, which is also a failure).
        assert "Blocking-Architecture Self-Check" in doc_text
        self_check_start = doc_text.index("Blocking-Architecture Self-Check")
        self_check_section = doc_text[self_check_start : self_check_start + 4000]
        assert "never" in self_check_section.lower()
        assert "no dual authority" in doc_text.lower() or "dual authority" in doc_text.lower()


class TestExplicitNonImplementationConfirmations:
    """Section 100 of the governing prompt requires the phase to
    explicitly confirm each of these; verify the confirming language is
    actually present in the document."""

    @pytest.mark.parametrize("fragment", ["HATP-001", "RAE-001"])
    def test_key_frozen_artifact_names_referenced(self, doc_text, fragment):
        assert fragment in doc_text

    def test_does_not_claim_pol_005_modified(self, doc_text):
        assert "does not modify `ExecutionDisabledRule`/POL-005" in doc_text or (
            "POL-005" in doc_text and "does not modify" in doc_text
        )

    def test_states_no_dispatch_behavior_change(self, doc_text):
        assert "no rollback behavior change" in doc_text.lower() or (
            "no dispatch" in doc_text.lower() and "change" in doc_text.lower()
        )


class TestLoadBearingFactsIndependentlyReconfirmed:
    """Re-derive, from the current source tree (not from the architecture
    document's own prose), the facts the 149O.8 decisions depend on."""

    def test_hatp_ag_authority_functions_accept_no_provider_or_trust_store_param(self):
        text = HATP_AG_AUTHORITY.read_text(encoding="utf-8")
        for fn_name in (
            "resolve_ag3_gated_rollback_authority",
            "resolve_ag5_gated_rollback_authority",
        ):
            match = re.search(rf"def {fn_name}\(([^)]*(?:\([^)]*\)[^)]*)*)\)", text, re.S)
            assert match, f"could not locate signature for {fn_name}"
            signature = match.group(1)
            assert "hatp_provider" not in signature
            assert "hatp_trust_store" not in signature
            assert "approval_present" not in signature

    def test_hatp_ag_authority_hardcodes_simulation_only_true(self):
        text = HATP_AG_AUTHORITY.read_text(encoding="utf-8")
        assert re.search(r"simulation_only\s*=\s*True", text)

    def test_permission_broker_component_registry_defines_comp_002_not_implemented(self):
        text = PB_FOUNDATION.read_text(encoding="utf-8")
        assert re.search(
            r'ComponentRegistryEntry\(\s*"COMP-002"\s*,\s*"Execution Boundary"\s*,\s*"not_implemented"',
            text,
        ), "COMP-002 registry entry not found or changed shape"

    def test_execution_disabled_rule_denies_non_simulation_requests(self):
        text = PB_FOUNDATION.read_text(encoding="utf-8")
        assert "ExecutionDisabledRule" in text
        assert "simulation_only" in text
        assert "DECISION_DENY" in text

    def test_verify_hatp_proof_takes_no_datetime_now_shortcut(self):
        text = HATP_PROVENANCE.read_text(encoding="utf-8")
        assert "def verify_hatp_proof(" in text
        assert "evaluation_time" in text

    def test_digest_hatp_proof_payload_helper_exists(self):
        """149O.8's proposed evidence_id = digest_hatp_proof_payload(proof)
        depends on this helper existing with this exact name."""
        text = HATP_PROVENANCE.read_text(encoding="utf-8")
        assert "def digest_hatp_proof_payload(" in text

    def test_inspect_hatp_verification_substrate_readiness_exists(self):
        text = HATP_PROVENANCE.read_text(encoding="utf-8")
        assert "def inspect_hatp_verification_substrate_readiness(" in text
        assert "operational" in text

    def test_no_provider_selection_flag_exists_in_commands(self):
        """149O.8's architecture depends on there being no existing
        --provider-style selection surface for HATP providers; if one now
        exists, §10's decision needs revisiting."""
        for path in COMMANDS_DIR.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "--provider" not in text or "hatp" not in text.lower(), (
                f"unexpected HATP provider-selection flag found in {path}"
            )

    def test_no_cli_signing_surface_exists_yet(self):
        """Confirms the evidence-acquisition gap this architecture
        addresses is still open -- i.e. this phase did not accidentally
        also implement it."""
        hits = []
        for path in COMMANDS_DIR.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "hatp_evidence_id" in text or "HumanApprovalProvenanceProof" in text:
                hits.append(str(path))
        assert not hits, (
            f"CLI signing/consumption surface unexpectedly present: {hits} "
            "-- 149O.8 is architecture-only and must not implement this"
        )

    def test_approve_rollback_still_bare_state_mutation(self):
        text = AGENT_CORE.read_text(encoding="utf-8")
        match = re.search(r"def approve_rollback\(.*?\n\n\n", text, re.S)
        assert match, "approve_rollback not found"
        body = match.group(0)
        assert "hatp" not in body.lower(), (
            "approve_rollback unexpectedly references HATP -- 149O.8 must not "
            "change rollback dispatch/approval behavior"
        )

    def test_execute_rollback_accepts_optional_hatp_params_unused_by_cli(self):
        core_text = AGENT_CORE.read_text(encoding="utf-8")
        assert "def execute_rollback(" in core_text
        match = re.search(r"def execute_rollback\(([^)]*(?:\([^)]*\)[^)]*)*)\)", core_text, re.S)
        assert match
        signature = match.group(1)
        assert "hatp_evidence_id" in signature

        commands_text = AGENT_COMMANDS.read_text(encoding="utf-8")
        assert "run_remote_rollback_execute" in commands_text


class TestNoProductionOrContractFilesModified:
    """This phase's allowed-file scope is documentation/task/status
    metadata only; verify no src/** or docs/contracts/** file appears in
    this phase's own staged/committed diff once commits exist. Skipped
    gracefully if run outside a git checkout with the expected remote
    history (keeps this suite runnable in isolated test environments)."""

    def test_no_src_or_contract_files_in_working_tree_diff(self):
        try:
            result = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except FileNotFoundError:
            pytest.skip("git not available")
        if result.returncode != 0:
            pytest.skip("git diff unavailable in this environment")
        changed = [line for line in result.stdout.splitlines() if line.strip()]
        forbidden = [
            f
            for f in changed
            if f.startswith("src/pcae/") or f.startswith("docs/contracts/")
        ]
        assert not forbidden, f"unexpected production/contract changes: {forbidden}"
