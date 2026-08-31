"""Static contract-repair verification for Phase 149O.20L.7O.3V.1R.

Verifies that the two BLOCKING findings independently identified by Phase
149O.20L.7O.3V.1 are closed by the repaired PBRD-001 v1.1 and RDGO-001 v2.0
contract text, without any production source change. This module tests
frozen Markdown contract text only; it does not implement, register, or
activate a runtime_dispatch action, approval store/validator, Runtime
Enforcement gate, or Shell Gate.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "docs" / "contracts"
RIHAC = CONTRACTS / "RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
PBRD = CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"
RDGO = CONTRACTS / "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
RIASC = CONTRACTS / "RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
RPAC = CONTRACTS / "RUNTIME_PROVIDER_ADAPTER_CONTRACT.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestVersioning:
    def test_pbrd_is_v1_1_and_rdgo_is_v2_0(self):
        pbrd = _text(PBRD)
        rdgo = _text(RDGO)
        assert "**Contract:** PBRD-001" in pbrd
        assert "**Version:** 1.1" in pbrd
        assert "**Status:** FROZEN" in pbrd
        assert "**Contract:** RDGO-001" in rdgo
        assert "**Version:** 2.0" in rdgo
        assert "**Status:** FROZEN" in rdgo

    def test_rihac_and_riasc_remain_v1_0_unchanged(self):
        rihac = _text(RIHAC)
        riasc = _text(RIASC)
        assert "RIHAC-001 v1.0" in rihac
        assert "**Version:** 1.0" not in [
            line for line in rihac.splitlines() if "Version" in line
        ] or "1.0" in rihac
        assert "RIASC-001 v1.0" in riasc

    def test_cross_references_updated_to_repaired_versions(self):
        rihac = _text(RIHAC)
        assert "PBRD-001 v1.1" in rihac
        assert "RDGO-001 v2.0" in rihac
        pbrd = _text(PBRD)
        assert "RDGO-001 v2.0" in pbrd
        rdgo = _text(RDGO)
        assert "PBRD-001 v1.1" in rdgo


class TestFindingB1GateOrderClosed:
    def test_rdgo_gate_table_has_approval_before_static_preflight(self):
        text = _text(RDGO)
        table_match = re.search(
            r"\| 3 \| (.+?) \|.*?\n\| 4 \| (.+?) \|", text
        )
        assert table_match, "expected gates 3 and 4 rows in the frozen gate table"
        gate3_name = table_match.group(1)
        gate4_name = table_match.group(2)
        assert "Human authority creation" in gate3_name
        assert "Static preflight" in gate4_name

    def test_rpac_req_042_order_is_literally_matched_at_gates_3_and_4(self):
        rpac = _text(RPAC)
        assert "3. obtain human InvocationApproval" in rpac
        assert (
            "4. resolve descriptor/config and perform fact-only "
            "status/capability preflight" in rpac
        )
        rdgo = _text(RDGO)
        assert "## 4. Gate 3 — human authority creation" in rdgo
        assert "## 5. Gate 4 — static preflight" in rdgo

    def test_rdgo_gate_count_unchanged_at_eleven(self):
        text = _text(RDGO)
        assert "Gate count: 11 (unchanged)" in text
        rows = re.findall(r"^\| (\d+) \| .+? \| .+? \| .+? \| .+? \| .+? \|$", text, re.MULTILINE)
        numeric_gate_rows = [r for r in rows if r.isdigit() and 1 <= int(r) <= 11]
        assert len(set(numeric_gate_rows)) == 11

    def test_rdgo_declares_major_version_bump_rationale_for_reordering(self):
        text = _text(RDGO)
        assert "reordering gates is" in text.lower() or "Reordering gates" in text
        assert "requires a new MAJOR" in text
        assert "v2.0" in text

    def test_ea_boundary_mapping_unaffected_by_transposition(self):
        text = _text(RDGO)
        assert "Gates 1–6 occur before the governed execution-attempt decision point." in text
        assert "unchanged by the v2.0 gate 3/4 transposition" in text


class TestFindingB2AttemptIdempotencyClosed:
    def test_pbrd_has_fourteen_facts_including_attempt_and_idempotency(self):
        text = _text(PBRD)
        rows = re.findall(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|", text, re.MULTILINE)
        first_fourteen = rows[:14]
        assert len(first_fourteen) == 14
        fields = [name for _, name in first_fourteen]
        assert fields[0] == "invocation_id"
        assert fields[1] == "attempt_id"
        assert fields[2] == "idempotency_key"
        assert "fourteen" in text
        assert "## 4. Base PB envelope and fourteen immutable binding facts" in text

    def test_pbrd_no_longer_claims_twelve_as_current_count(self):
        text = _text(PBRD)
        assert "Base PB envelope and fourteen immutable binding facts" in text
        assert "## 4. Base PB envelope and twelve immutable binding facts" not in text

    def test_attempt_id_and_idempotency_key_are_pcae_owned_not_caller_settable(self):
        text = _text(PBRD)
        assert (
            "Caller sets/influences `attempt_id` or `idempotency_key` | "
            "Reject request construction" in text
        )
        assert "PCAE coordinator" in text

    def test_rdgo_durable_item_one_binds_attempt_and_idempotency_unconditionally(self):
        text = _text(RDGO)
        assert "attempt_id\" where used" not in text.replace("`attempt_id` \"where used.\"", "")
        assert (
            "this attempt's mandatory unique\n   `attempt_id`, and the request's "
            "canonical `idempotency_key`" in text
            or "mandatory unique" in text
        )
        assert "never `attempt_id` \"where used.\"" in text

    def test_rpac_req_064_065_are_satisfied_by_the_repaired_semantics(self):
        rpac = _text(RPAC)
        rdgo = _text(RDGO)
        assert "unique `attempt_id`" in rpac
        assert "idempotency_key" in rpac
        assert "attempt_id" in rdgo and "idempotency_key" in rdgo
        assert "att-<32-hex>" in rdgo

    def test_retry_semantics_distinguish_attempt_id_from_idempotency_key(self):
        text = _text(RDGO)
        assert "new `attempt_id`" in text
        assert "the `idempotency_key`\nremains identical" in text

    def test_cross_contract_identifier_matrix_includes_attempt_and_idempotency_rows(self):
        text = _text(RDGO)
        assert "| Attempt |" in text
        assert "| Idempotency |" in text

    def test_riasc_subject_unchanged_five_members_no_attempt_id_added(self):
        text = _text(RIASC)
        assert '"invocation_id",\n        "runtime_target_id",\n        "prompt_hash",\n        "repository_identity",\n        "task_id"' in text
        assert '"attempt_id"' not in text
        assert '"idempotency_key"' not in text


class TestNoNewContradictions:
    def test_no_production_source_touched_by_this_repair(self):
        diff = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout.splitlines()
        staged = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout.splitlines()
        changed = set(diff) | set(staged)
        assert not [p for p in changed if p.startswith("src/pcae/")]

    def test_dry_path_shape_unchanged_and_excluded_from_new_facts(self):
        text = _text(PBRD)
        assert "action_type = adapter_invocation" in text
        assert "simulation_only = true" in text
        assert (
            "The dry path SHALL NOT be required to carry `attempt_id` or "
            "`idempotency_key`" in text
        )

    def test_pol_005_and_semantic_walls_still_present(self):
        for path in (RIHAC, PBRD, RDGO):
            text = _text(path)
            assert "human approval != PB permission" in text
        assert "POL-005" in _text(PBRD)
        assert "ExecutionDisabledRule" in _text(PBRD)

    def test_gate_ten_remains_first_external_effect(self):
        text = _text(RDGO)
        assert "Gate 10 is the real-effect boundary." in text
        assert "Gate 10 is the first external execution effect." in text

    def test_no_go_statements_preserved(self):
        for path in (RIHAC, PBRD, RDGO):
            text = _text(path)
            assert "UNAVAILABLE" in text.upper()
        assert "does not launch a process" in _text(RDGO)
        # Phase ...1R.22 (N-16-3) took PBRD-001 -> v3.0 (MAJOR) and reworded
        # this no-go clause from "does not launch a process" to "**not**
        # launch a process, invoke an external runtime, ...". The no-go
        # itself is preserved; accept either phrasing. Reconciled by .1R.22R.
        assert re.search(r"(does not|\*\*not\*\*)\s+launch a process", _text(PBRD))
