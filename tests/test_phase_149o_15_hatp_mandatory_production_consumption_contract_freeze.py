"""Phase 149O.15 -- Contract-verification test for the HATP Mandatory
Rollback Consumption Contract (HMRC-001 v1.0,
`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`) and
its phase document
(`docs/PHASE_149O_15_HATP_MANDATORY_PRODUCTION_CONSUMPTION_CONTRACT_FREEZE.md`).

149O.15 is a CONTRACT-FREEZE-ONLY phase: it modifies no `src/pcae/**`
file and no existing contract file. This module does not test an
implementation (there is none yet). It independently re-verifies, by
direct document and source inspection rather than by trusting the
contract's own prose:

  * the frozen contract identity, requirement sequence, and invariant/
    attack-matrix counts declared by the new contract document itself;
  * that the contract text is internally self-consistent (no dual/OR
    legacy-fallback authority language, no implicit-lookup language);
  * that the *current-state* production facts the contract's design
    decisions rest on (AG3/AG5 call graphs, inert Wave-7 hooks,
    explicit-ID-only evidence store, unconditional
    `simulation_only=True` PB request, POL-005's exact trigger
    condition) are still true today, independent of the contract's own
    claims about them;
  * that no existing contract file (HSCE-001, HATP-001, RAE-001,
    RWMPC-001, PBPA-001, PBPC-001) was modified by this phase.
"""
from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"

_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
_PHASE_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_15_HATP_MANDATORY_PRODUCTION_CONSUMPTION_CONTRACT_FREEZE.md"
)


def _contract_text() -> str:
    return _CONTRACT_PATH.read_text(encoding="utf-8")


def _read_src(relpath: str) -> str:
    return (_SRC / relpath).read_text(encoding="utf-8")


def _parse_src(relpath: str) -> ast.Module:
    return ast.parse(_read_src(relpath), filename=relpath)


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function {name!r} not found")


def _kwonly_names(fn: ast.FunctionDef) -> list:
    return [a.arg for a in fn.args.kwonlyargs]


# ═══════════════════════════════════════════════════════════════════════════
# Contract document exists and declares the frozen identity
# ═══════════════════════════════════════════════════════════════════════════


class TestContractIdentity:
    def test_contract_file_exists(self):
        assert _CONTRACT_PATH.is_file()

    def test_phase_doc_exists(self):
        assert _PHASE_DOC_PATH.is_file()

    def test_contract_id_and_version_frozen(self):
        text = _contract_text()
        assert "**Contract ID:** HMRC-001" in text
        assert "**Version:** 1.0" in text

    def test_status_is_frozen_not_verified(self):
        text = _contract_text()
        assert "READY FOR INDEPENDENT CONTRACT VERIFICATION" in text
        # Must not claim VERIFIED anywhere as this contract's own status.
        assert "Status:** FROZEN — READY FOR INDEPENDENT CONTRACT VERIFICATION (not VERIFIED)" in text

    def test_declares_dependency_on_unmodified_upstream_contracts(self):
        text = _contract_text()
        for dep in (
            "HATP-001 v1.0",
            "HSCE-001 v1.1",
            "RAE-001 v1.0",
            "RWMPC-001 v1.0",
            "PBPA-001 v1.0",
            "PBPC-001 v1.2",
        ):
            assert dep in text, f"missing dependency declaration: {dep}"


# ═══════════════════════════════════════════════════════════════════════════
# Requirement inventory, security invariants, attack matrix counts
# ═══════════════════════════════════════════════════════════════════════════


class TestRequirementAndInvariantCounts:
    def test_requirement_ids_sequential_no_gaps_no_duplicates(self):
        text = _contract_text()
        ids = sorted(
            {int(m) for m in re.findall(r"HMRC-REQ-(\d{3})", text)}
        )
        assert ids, "no HMRC-REQ-### requirement IDs found"
        assert ids[0] == 1, "requirement numbering must start at HMRC-REQ-001"
        expected = list(range(ids[0], ids[-1] + 1))
        assert ids == expected, "requirement IDs must be sequential with no gaps"

    def test_at_least_eighty_requirements(self):
        text = _contract_text()
        ids = {int(m) for m in re.findall(r"HMRC-REQ-(\d{3})", text)}
        assert len(ids) >= 80

    def test_mc_invariants_mc1_through_mc14_present(self):
        text = _contract_text()
        for i in range(1, 15):
            assert re.search(rf"\bMC-{i}\b", text), f"missing MC-{i}"
        # Exactly 14, not more, in the frozen invariant list section.
        section = text.split("## 27. Security Invariants")[1]
        section = section.split("## 28.")[0]
        numbers = sorted(int(m) for m in re.findall(r"\*\*MC-(\d+)", section))
        assert numbers == list(range(1, 15))

    def test_mc14_resolves_effect_truthful_pb_requirement(self):
        text = _contract_text()
        assert "MC-14" in text
        assert "Effect-Truthful PB Requirement" in text
        assert "simulation_only=False" in text
        assert "simulation_only=True" in text

    def test_attack_matrix_has_exactly_45_rows(self):
        text = _contract_text()
        section = text.split("## 29. Full Mandatory Attack Matrix")[1]
        section = section.split("## 30.")[0]
        # Table rows: lines starting with "| <number> |"
        rows = re.findall(r"^\|\s*(\d+)\s*\|", section, flags=re.MULTILINE)
        numbers = [int(r) for r in rows]
        assert numbers == list(range(1, 46)), (
            f"expected exactly 45 sequential attack rows, got {len(numbers)}: {numbers}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Evidence-reference syntax and mode vocabulary frozen exactly as specified
# ═══════════════════════════════════════════════════════════════════════════


class TestFrozenSyntaxAndVocabulary:
    def test_evidence_flag_is_exact_and_singular(self):
        text = _contract_text()
        assert "--hatp-evidence-id <evidence_id>" in text
        # Alias flags are only named inside the prohibition (HMRC-REQ-009);
        # they must never appear as an actual usable flag example elsewhere
        # (i.e. not inside a fenced/backtick command-line usage block).
        for forbidden in ("--evidence-id", "--evidence-file"):
            for line in text.splitlines():
                if forbidden in line:
                    assert "SHALL be added" in line or "alias" in line.lower(), (
                        f"{forbidden!r} appears outside the forbidden-alias prohibition: {line!r}"
                    )

    def test_ag3_cli_target_frozen(self):
        text = _contract_text()
        assert (
            "pcae remote rollback execute <job_id> --hatp-evidence-id <evidence_id> [--json]"
            in text
        )

    def test_ag5_cli_target_frozen(self):
        text = _contract_text()
        assert (
            "pcae rollback --per-id <per_id> --hatp-evidence-id <evidence_id> [--dry-run] [--json]"
            in text
        )

    def test_evidence_id_domain_referenced_not_redefined(self):
        text = _contract_text()
        assert "64-character, all-lowercase hexadecimal" in text
        assert "HSCE-REQ-056" in text

    def test_cutover_mode_vocabulary_exact(self):
        text = _contract_text()
        for mode in ("LEGACY_COMPATIBLE", "PREPARED", "HATP_MANDATORY"):
            assert mode in text

    def test_cutover_transition_rule_frozen(self):
        text = _contract_text()
        assert "LEGACY_COMPATIBLE → PREPARED → HATP_MANDATORY" in text
        assert "forbidden" in text.lower()

    def test_canonical_loader_and_object_named(self):
        text = _contract_text()
        assert "HATPEvidenceStore.load(evidence_id)" in text
        assert "HATPSignedEvidenceEnvelope" in text

    def test_old_hook_disposition_present_for_all_three(self):
        text = _contract_text()
        section = text.split("## 23. Old-Hook (Wave-7) Disposition")[1]
        section = section.split("## 24.")[0]
        assert "hatp_evidence_id" in section
        assert "hatp_proof" in section
        assert "hatp_evidence" in section
        assert "deprecated" in section.lower()

    def test_forbidden_caller_inputs_closed_list(self):
        text = _contract_text()
        section = text.split("## 24. Forbidden Caller Inputs")[1]
        section = section.split("## 25.")[0]
        for forbidden in (
            "approval_present",
            "pb_decision=ALLOW",
            'mode="HATP_MANDATORY"',
        ):
            assert forbidden in section


# ═══════════════════════════════════════════════════════════════════════════
# Self-consistency: no dual/OR authority, no implicit lookup language
# ═══════════════════════════════════════════════════════════════════════════


class TestContractSelfConsistency:
    def test_no_dual_or_authority_language(self):
        text = _contract_text()
        assert "legacy_approved OR hatp_valid" in text  # named explicitly as forbidden
        # It must be named only in a prohibition context, never asserted as the rule.
        forbidden_context = re.search(
            r"(No clause[^.]*legacy_approved OR hatp_valid|forbidden[^.]*legacy_approved OR hatp_valid|SHALL NOT[^.]*legacy_approved OR hatp_valid)",
            text,
        )
        assert forbidden_context, "dual-authority phrase must appear only inside a prohibition"

    def test_no_implicit_evidence_lookup_permitted(self):
        text = _contract_text()
        assert "Implicit evidence selection is prohibited absolutely" in text
        for term in ("latest", "newest", "glob"):
            assert term in text  # named as prohibited examples

    def test_pb_allow_alone_declared_insufficient(self):
        text = _contract_text()
        assert (
            "PB `ALLOW` alone satisfies the permission-decision" in text
            or "insufficient alone" in text
        )

    def test_effect_boundary_placed_inside_functions_not_cli(self):
        text = _contract_text()
        assert "CLI-only enforcement is forbidden" in text
        assert "execute_rollback" in text
        assert "build_rollback_execution" in text
        assert "_run_git_revert" in text

    def test_monotonicity_mechanism_specified(self):
        text = _contract_text()
        assert "Monotonicity" in text
        assert "never downgrade" in text.lower() or "shall never" in text.lower()

    def test_comp002_separation_maintained(self):
        text = _contract_text()
        assert "COMP-002" in text
        normalized = " ".join(text.split())
        assert "It does NOT establish general runtime execution capability" in normalized


# ═══════════════════════════════════════════════════════════════════════════
# Independent re-verification of underlying current-state production facts
# ═══════════════════════════════════════════════════════════════════════════


class TestUnderlyingProductionFactsStillTrue:
    def test_execute_rollback_signature_has_wave7_hooks(self):
        tree = _parse_src("core/agent.py")
        fn = _find_function(tree, "execute_rollback")
        names = _kwonly_names(fn)
        assert {"hatp_evidence_id", "hatp_proof", "hatp_evidence"} <= set(names)

    def test_build_rollback_execution_signature_has_wave7_hooks(self):
        tree = _parse_src("core/agent.py")
        fn = _find_function(tree, "build_rollback_execution")
        names = _kwonly_names(fn)
        assert {"hatp_evidence_id", "hatp_proof", "hatp_evidence"} <= set(names)

    def test_run_git_revert_is_the_ag3_real_effect_call(self):
        text = _read_src("core/agent.py")
        assert "def _run_git_revert(" in text
        # execute_rollback must call it.
        tree = _parse_src("core/agent.py")
        fn = _find_function(tree, "execute_rollback")
        call_names = {
            n.func.id
            for n in ast.walk(fn)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        }
        assert "_run_git_revert" in call_names

    def test_build_rollback_execution_performs_real_file_mutation(self):
        tree = _parse_src("core/agent.py")
        fn = _find_function(tree, "build_rollback_execution")
        attrs = {
            n.attr
            for n in ast.walk(fn)
            if isinstance(n, ast.Attribute)
        }
        assert {"write_bytes", "write_text", "unlink"} <= attrs

    def test_real_callers_pass_zero_hatp_kwargs_today(self):
        text = _read_src("commands/agent.py")
        # Locate the call sites and confirm no hatp_* kwarg is threaded through.
        tree = ast.parse(text, filename="commands/agent.py")
        calls = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id in ("execute_rollback", "build_rollback_execution")
        ]
        assert calls, "expected at least one real call site for each effect function"
        for call in calls:
            kwarg_names = {kw.arg for kw in call.keywords if kw.arg is not None}
            assert not (kwarg_names & {"hatp_evidence_id", "hatp_proof", "hatp_evidence"}), (
                "a real production call site now threads a HATP kwarg through -- "
                "the contract's 'inert Wave-7 hook' baseline fact is stale"
            )

    def test_evidence_store_load_is_explicit_id_only(self):
        tree = _parse_src("core/hatp_evidence_store.py")
        fn = _find_function(tree, "load")
        arg_names = [a.arg for a in fn.args.args]
        assert "evidence_id" in arg_names
        # No "latest"/glob-style alternate lookup method exists on the class.
        text = _read_src("core/hatp_evidence_store.py")
        for forbidden in ("def latest", "def load_latest", "def most_recent"):
            assert forbidden not in text

    def test_hatp_ag_authority_pb_request_is_simulation_only_true(self):
        text = _read_src("core/hatp_ag_authority.py")
        assert "simulation_only=True" in text
        assert "simulation_only=False" not in text

    def test_pol005_execution_disabled_rule_trigger_condition(self):
        text = _read_src("core/permission_broker_foundation.py")
        tree = ast.parse(text, filename="core/permission_broker_foundation.py")
        cls = next(
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.ClassDef) and n.name == "ExecutionDisabledRule"
        )
        assert any(
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "policy_id" for t in n.targets)
            for n in cls.body
        )
        src = ast.get_source_segment(text, cls)
        assert 'policy_id = "POL-005"' in src
        assert "if request.simulation_only:" in src
        assert "DECISION_DENY" in src
        assert '"COMP-002"' in src

    def test_no_hatp_evidence_id_flag_on_current_cli(self):
        cli_text = _read_src("cli.py")
        assert "--hatp-evidence-id" not in cli_text

    def test_comp002_and_comp008_not_implemented_today(self):
        text = _read_src("core/permission_broker_foundation.py")
        assert '"COMP-002"' in text
        assert '"COMP-008"' in text


# ═══════════════════════════════════════════════════════════════════════════
# No production or existing-contract change was made this phase
# ═══════════════════════════════════════════════════════════════════════════


class TestNoProductionOrExistingContractChange:
    # Updated 149O.18F (149O.5-F-3 methodology): originally compared
    # against the symbolic `origin/main` ref, which equalled HEAD only at
    # 149O.15's own phase entry (`origin/main..HEAD == 0`). That
    # comparison is an "eternal moving target" -- it necessarily reports
    # a non-empty diff for *any* later phase's own legitimate, not-yet-
    # pushed production commits (18A-18F all add such commits before
    # their own push), independent of whether those commits touch
    # anything 149O.15 itself cares about. Pinned instead to the frozen
    # commit range spanning 149O.15's own execution only -- from the
    # commit immediately preceding its first commit (`e1c3653c`) to its
    # own phase-completion commit (`507b63d1`) -- which correctly and
    # permanently answers "did 149O.15 itself touch this path" regardless
    # of how many later phases commit locally before their own push.
    _PHASE_149O_15_ENTRY_COMMIT = "e1c3653c"
    _PHASE_149O_15_COMPLETION_COMMIT = "507b63d1"

    def _diff_against_head_before_this_phase(self, pathspec: str) -> str:
        result = subprocess.run(
            [
                "git", "diff", "--name-only",
                self._PHASE_149O_15_ENTRY_COMMIT, self._PHASE_149O_15_COMPLETION_COMMIT,
                "--", pathspec,
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout

    def test_existing_contracts_untouched(self):
        for existing in (
            "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
            "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
            "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
            "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
            "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
            "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
        ):
            diff = self._diff_against_head_before_this_phase(f"docs/contracts/{existing}")
            assert existing not in diff, f"{existing} was modified by this phase"

    def test_no_src_pcae_files_changed(self):
        diff = self._diff_against_head_before_this_phase("src/pcae/")
        assert diff.strip() == "", f"production source changed this phase: {diff}"
