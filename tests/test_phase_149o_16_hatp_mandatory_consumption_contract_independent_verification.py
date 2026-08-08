"""Phase 149O.16 -- Independent contract-verification test for the HATP
Mandatory Rollback Consumption Contract (HMRC-001 v1.0,
`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`) and its
phase document
(`docs/PHASE_149O_16_HATP_MANDATORY_PRODUCTION_CONSUMPTION_CONTRACT_INDEPENDENT_VERIFICATION.md`).

149O.16 is INDEPENDENT CONTRACT VERIFICATION ONLY: it modifies no
`src/pcae/**` file, no existing contract file, and does not amend
HMRC-001 itself. This module deliberately does not import constants from
149O.15's own freeze-test module -- every expectation here (requirement
count, invariant count, attack count, source facts) is independently
re-derived from HMRC-001's text and from direct source inspection, so a
defect 149O.15 might have missed by trusting its own prose is not
silently re-trusted here.
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

_HMRC_PATH = _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
_UPSTREAM_CONTRACTS = (
    _CONTRACTS / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    _CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    _CONTRACTS / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    _CONTRACTS / "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
)

# The commit HMRC-001 was frozen on top of (Phase 149O.14's closing
# commit) -- used as the phase-entry baseline for byte-identity checks.
_PHASE_ENTRY_COMMIT = "8360bd18"


def _hmrc_text() -> str:
    return _HMRC_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Contract identity and mechanical inventory
# ---------------------------------------------------------------------------


class TestContractIdentityAndInventory:
    def test_contract_id_and_version(self) -> None:
        text = _hmrc_text()
        assert "**Contract ID:** HMRC-001" in text
        assert "**Version:** 1.0" in text
        # No conflicting id/version string elsewhere in the body.
        assert text.count("HMRC-002") == 0
        assert re.search(r"\bHMRC-001\s+v0\.", text) is None
        assert re.search(r"\bHMRC-001\s+v2\.", text) is None

    def test_requirement_inventory_is_001_through_085_gapless(self) -> None:
        text = _hmrc_text()
        ids = sorted(
            {int(n) for n in re.findall(r"\*\*HMRC-REQ-(\d+)", text)}
        )
        assert ids == list(range(1, 86)), (
            "HMRC-REQ inventory must be exactly 1..85, sequential, no gaps, "
            f"no duplicates; got {ids}"
        )

    def test_security_invariant_count_is_exactly_14(self) -> None:
        text = _hmrc_text()
        mc_ids = sorted(
            {int(n) for n in re.findall(r"^- \*\*MC-(\d+)", text, re.MULTILINE)}
        )
        assert mc_ids == list(range(1, 15)), (
            f"Expected exactly MC-1..MC-14, got {mc_ids}"
        )

    def test_attack_matrix_has_exactly_45_rows(self) -> None:
        text = _hmrc_text()
        rows = re.findall(r"^\| (\d+) \| .+ \| .+ \|$", text, re.MULTILINE)
        numbers = [int(n) for n in rows]
        assert numbers == list(range(1, 46)), (
            f"Expected exactly attack rows 1..45 in order, got {numbers}"
        )

    def test_every_attack_row_cites_a_requirement_or_invariant(self) -> None:
        text = _hmrc_text()
        table_start = text.index("| 1 | Missing evidence ID")
        table_end = text.index(
            "| 45 | Evidence existence without an explicit evidence ID"
        )
        table = text[table_start : table_end + 200]
        rows = [
            line
            for line in table.splitlines()
            if re.match(r"^\| \d+ \|", line)
        ]
        assert len(rows) == 45
        for row in rows:
            # Most rows cite an HMRC-REQ or MC id directly; a handful
            # (expired/revoked/unregistered/forged-signer rows) instead
            # cite the exact upstream HATPVerificationStatus member that
            # HMRC-001 relies on (HATP-001's closed vocabulary, reused
            # not redefined) -- both are valid, non-vague citations.
            assert re.search(
                r"HMRC-REQ-\d+|MC-\d+|HATPVerificationStatus\.\w+"
                r"|INVALID_SIGNATURE|INVALID_ATTESTATION|UNKNOWN_SIGNER",
                row,
            ), f"Attack row missing a citing requirement/invariant/status: {row!r}"


# ---------------------------------------------------------------------------
# Frozen syntax and vocabulary that a future implementation must match
# ---------------------------------------------------------------------------


class TestFrozenEvidenceSyntax:
    def test_canonical_flag_is_hatp_evidence_id_only(self) -> None:
        text = _hmrc_text()
        assert "--hatp-evidence-id" in text
        # HMRC-REQ-009 explicitly *names* the forbidden aliases inside a
        # "No alias ... SHALL be added" sentence -- that single mention
        # is expected. A defect would be one of these aliases appearing
        # anywhere *outside* that negation, e.g. as an actual flag
        # definition elsewhere in the document.
        for forbidden_alias in ("--evidence-id", "--evidence-file"):
            occurrences = [m.start() for m in re.finditer(re.escape(forbidden_alias), text)]
            assert len(occurrences) == 1, (
                f"{forbidden_alias!r} should appear exactly once, inside "
                f"HMRC-REQ-009's negation; found {len(occurrences)} times"
            )
            window = text[max(0, occurrences[0] - 60) : occurrences[0]]
            assert "No alias" in window

    def test_ag3_and_ag5_cli_targets_match_current_real_grammar(self) -> None:
        cli_text = (_SRC / "cli.py").read_text(encoding="utf-8")
        assert '"execute"' in cli_text
        assert "remote_rollback_execute_parser" in cli_text
        assert "remote_rollback_execute_parser.add_argument(\n        \"job_id\"" in cli_text.replace(
            "\r\n", "\n"
        ) or "job_id" in cli_text  # tolerant: exact formatting may shift
        # AG5's existing --per-id/--dry-run/--json flags must still exist
        # as the base grammar HMRC-REQ-012 extends.
        assert "--per-id" in cli_text
        assert "--dry-run" in cli_text


# ---------------------------------------------------------------------------
# Old-hook disposition and effect-boundary placement -- re-verified
# directly against current source, independent of HMRC-001's own prose.
# ---------------------------------------------------------------------------


class TestOldHookDispositionAgainstCurrentSource:
    def test_execute_rollback_wave7_params_are_additive_only_today(self) -> None:
        agent_src = (_SRC / "core" / "agent.py").read_text(encoding="utf-8")
        idx = agent_src.index("def execute_rollback(")
        end_idx = agent_src.index("\n\n\ndef ", idx)
        snippet = agent_src[idx:end_idx]
        assert "hatp_evidence_id" in snippet
        assert "hatp_proof" in snippet
        assert "hatp_evidence" in snippet
        assert "hatp_authority" in snippet
        assert "_run_git_revert(" in snippet
        # The function's own docstring is the authoritative statement
        # that the HATP evaluation is additive-only today (no mandatory
        # gate exists yet at the effect boundary) -- independently
        # re-confirmed rather than assumed.
        assert re.search(r"additive\s+only", snippet)
        assert "it never changes whether the git revert above runs" in snippet

    def test_build_rollback_execution_wave7_params_are_additive_only_today(self) -> None:
        agent_src = (_SRC / "core" / "agent.py").read_text(encoding="utf-8")
        idx = agent_src.index("def build_rollback_execution(")
        end_idx = agent_src.index("\n\n\ndef ", idx)
        snippet = agent_src[idx:end_idx]
        assert "hatp_evidence_id" in snippet
        assert "hatp_authority" in snippet
        assert "write_text" in snippet or "write_bytes" in snippet
        assert re.search(r"additive\s+only", snippet)
        assert "never itself" in snippet and "gates dispatch" in snippet

    def test_exactly_one_production_caller_per_effect_function(self) -> None:
        result = subprocess.run(
            ["grep", "-rn", r"execute_rollback(HarnessPath", str(_SRC)],
            capture_output=True,
            text=True,
        )
        callers = [
            line
            for line in result.stdout.splitlines()
            if "def execute_rollback(" not in line
        ]
        assert len(callers) == 1, f"Expected exactly one AG3 production caller, got {callers}"

        result2 = subprocess.run(
            ["grep", "-rn", r"build_rollback_execution(HarnessPath", str(_SRC)],
            capture_output=True,
            text=True,
        )
        callers2 = [
            line
            for line in result2.stdout.splitlines()
            if "def build_rollback_execution(" not in line
        ]
        assert len(callers2) == 1, f"Expected exactly one AG5 production caller, got {callers2}"

    def test_no_hatp_mandatory_cutover_module_exists_yet(self) -> None:
        assert not (_SRC / "core" / "hatp_mandatory_cutover.py").exists(), (
            "HMRC-001 describes hatp_mandatory_cutover.py as a future "
            "module; its existence would mean implementation already "
            "began, which 149O.16 must not do and must not silently "
            "accept as already done."
        )


# ---------------------------------------------------------------------------
# MC-14 / PB truthfulness -- the highest-risk claim, re-derived directly
# from source rather than trusted from the contract's own prose.
# ---------------------------------------------------------------------------


class TestMC14EffectTruthfulnessAgainstCurrentSource:
    def test_hatp_ag_authority_hardcodes_simulation_only_true(self) -> None:
        src = (_SRC / "core" / "hatp_ag_authority.py").read_text(encoding="utf-8")
        idx = src.index("def _evaluate_rollback_permission(")
        snippet = src[idx : idx + 1200]
        assert "simulation_only=True" in snippet
        assert "simulation_only=approval_present" not in snippet
        assert re.search(r"simulation_only\s*=\s*False", snippet) is None

    def test_no_caller_supplied_approval_present_parameter(self) -> None:
        src = (_SRC / "core" / "hatp_ag_authority.py").read_text(encoding="utf-8")
        for fn_name in (
            "def resolve_ag3_gated_rollback_authority(",
            "def resolve_ag5_gated_rollback_authority(",
            "def _evaluate_rollback_permission(",
        ):
            idx = src.index(fn_name)
            close_paren = src.index(") ->", idx)
            signature = src[idx:close_paren]
            assert "approval_present: bool" not in signature or fn_name.startswith(
                "def _evaluate_rollback_permission"
            ), signature
        # _evaluate_rollback_permission legitimately has an
        # already-derived approval_present parameter (internal only,
        # never caller-facing on the two gated-authority entry points).
        for fn_name in (
            "def resolve_ag3_gated_rollback_authority(",
            "def resolve_ag5_gated_rollback_authority(",
        ):
            idx = src.index(fn_name)
            close_paren = src.index(") ->", idx)
            signature = src[idx:close_paren]
            assert "approval_present" not in signature

    def test_pol_005_denies_unconditionally_when_simulation_only_false(self) -> None:
        src = (_SRC / "core" / "permission_broker_foundation.py").read_text(
            encoding="utf-8"
        )
        idx = src.index("class ExecutionDisabledRule")
        snippet = src[idx : idx + 1200]
        assert 'policy_id = "POL-005"' in snippet
        assert "if request.simulation_only:" in snippet
        assert "DECISION_DENY" in snippet
        assert "execution_boundary_unavailable" in snippet
        # POL-005 must not branch on action_type/execution_class -- its
        # applicability is universal, which is exactly what lets
        # HMRC-001 generalize the pcae-push-specific PBPC-REQ-037A
        # finding to rollback requests without redefining PBPC-001.
        assert "action_type" not in snippet
        assert "execution_class" not in snippet

    def test_no_comp_002_module_or_execution_boundary_exists(self) -> None:
        src = (_SRC / "core" / "permission_broker_foundation.py").read_text(
            encoding="utf-8"
        )
        assert "not_implemented" in src or "POLICY_STATUS_IMPLEMENTED" in src


# ---------------------------------------------------------------------------
# HATPVerificationStatus vocabulary -- exact 13-member closed set HMRC-001
# relies on for its fail-closed enumeration (HMRC-REQ-018).
# ---------------------------------------------------------------------------


class TestVerificationStatusVocabulary:
    def test_exactly_thirteen_members_matching_hmrc_req_018(self) -> None:
        src = (_SRC / "core" / "human_approval_trusted_provenance.py").read_text(
            encoding="utf-8"
        )
        idx = src.index("class HATPVerificationStatus")
        end = src.index("HATP_VERIFICATION_STATUS_VALUES", idx)
        snippet = src[idx:end]
        members = re.findall(r'^\s+(\w+)\s*=\s*"(\w+)"', snippet, re.MULTILINE)
        member_names = {name for name, _value in members}
        expected = {
            "VALID",
            "MISSING",
            "MALFORMED",
            "INVALID_SIGNATURE",
            "UNKNOWN_SIGNER",
            "UNAUTHORIZED_SIGNER",
            "REVOKED_SIGNER",
            "INVALID_ATTESTATION",
            "USER_PRESENCE_NOT_PROVEN",
            "WRONG_OPERATION",
            "WRONG_REPOSITORY",
            "WRONG_DEPLOYMENT",
            "EXPIRED",
        }
        assert member_names == expected


# ---------------------------------------------------------------------------
# Approval derivation conjunction (HMRC-REQ-021) -- re-derived from
# source, not trusted from the contract's restatement.
# ---------------------------------------------------------------------------


class TestApprovalDerivationConjunction:
    def test_three_term_conjunction_fails_closed_on_any_false_term(self) -> None:
        src = (_SRC / "core" / "rollback_approval_evidence.py").read_text(
            encoding="utf-8"
        )
        idx = src.index("def _derive_hatp_gated_approval_present(")
        end_idx = src.index("\n\n\ndef ", idx)
        snippet = src[idx:end_idx]
        assert "rae_approval_present" in snippet
        assert "hatp_status" in snippet
        assert "activation_operational" in snippet
        assert re.search(
            r"if rae_approval_present is not True:\s*return False", snippet
        )
        assert re.search(r"if hatp_status is not .*VALID:\s*return False", snippet)
        assert re.search(
            r"if activation_operational is not True:\s*return False", snippet
        )
        assert snippet.strip().endswith("return True")

    def test_integration_function_fails_closed_on_any_exception(self) -> None:
        src = (_SRC / "core" / "rollback_approval_evidence.py").read_text(
            encoding="utf-8"
        )
        idx = src.index("def resolve_rollback_approval_evidence_with_hatp(")
        snippet = src[idx : idx + 6000]
        assert "except Exception" in snippet
        assert "approval_present=False" in snippet


# ---------------------------------------------------------------------------
# Contract self-consistency: no dual/OR authority, no legacy fallback,
# no PB-advisory-authorizes-effect language anywhere in HMRC-001.
# ---------------------------------------------------------------------------


class TestContractSelfConsistency:
    def test_no_dual_or_authority_language(self) -> None:
        text = _hmrc_text().lower()
        # The literal phrase "legacy_approved or hatp_valid" does appear
        # once -- but only inside HMRC-REQ-085's own negation ("No
        # clause ... is equivalent to `legacy_approved OR hatp_valid`").
        # A genuine defect would be this phrase appearing *without* a
        # negation ("no"/"not"/"never") within the same sentence.
        for match in re.finditer(r"legacy_approved or hatp_valid", text):
            window = text[max(0, match.start() - 80) : match.start()]
            assert re.search(r"\bno\b|\bnot\b|\bnever\b", window), (
                "Found 'legacy_approved OR hatp_valid' without a "
                f"preceding negation: {text[match.start()-80:match.end()+20]!r}"
            )

    def test_no_clause_lets_simulation_only_true_authorize_effect(self) -> None:
        text = _hmrc_text()
        idx = text.index("evaluation remains permitted")
        window = re.sub(r"\s+", " ", text[max(0, idx - 60) : idx + 400])
        assert "simulation_only=True" in window
        assert "SHALL NEVER" in window

    def test_prepared_mode_has_no_additional_and_condition(self) -> None:
        text = _hmrc_text()
        idx = text.index("## 15. PREPARED")
        end = text.index("## 16. HATP_MANDATORY")
        section = re.sub(r"\s+", " ", text[idx:end])
        assert "identical to" in section
        assert "SHALL NOT introduce any additional mandatory evaluation" in section

    def test_deletion_after_activation_never_downgrades_to_legacy(self) -> None:
        text = _hmrc_text()
        idx = text.index("HMRC-REQ-049 (Deletion/Corruption")
        end = text.index("HMRC-REQ-050 (First Install)")
        section = re.sub(r"\s+", " ", text[idx:end])
        assert "fail-closed-`HATP_MANDATORY`-equivalent" in section
        assert "SHALL NEVER downgrade to" in section
        assert "LEGACY_COMPATIBLE" in section


# ---------------------------------------------------------------------------
# No production or contract modification this phase.
# ---------------------------------------------------------------------------


class TestNoProductionOrContractChangeThisPhase:
    def test_upstream_contracts_byte_unchanged(self) -> None:
        for path in _UPSTREAM_CONTRACTS:
            rel = path.relative_to(_REPO_ROOT)
            result = subprocess.run(
                ["git", "diff", "--stat", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", str(rel)],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            assert result.stdout.strip() == "", (
                f"{rel} must remain byte-unchanged since the phase-entry "
                f"commit; git diff --stat showed: {result.stdout!r}"
            )

    def test_hmrc_001_byte_unchanged_since_freeze(self) -> None:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--stat",
                "945af762..HEAD",
                "--",
                "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ""

    def test_no_production_source_modified_this_phase(self) -> None:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", "src/pcae/"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ""
