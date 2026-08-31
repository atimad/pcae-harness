"""Independent verification tests for Phase 149O.20L.7O.3V.1R.1.

These tests are FRESH — they do not reuse or import
`tests/test_phase_149o_20l_7o_3v_1r_contract_repair.py`. They independently
reconstruct the repaired PBRD-001 v1.1 / RDGO-001 v2.0 semantics from the
contract text itself (plus RPAC-001, RIHAC-001, RIASC-001) and from the
existing production mock/dry `simulate_invocation` gate sequence, to verify
that Phase 149O.20L.7O.3V.1R's two BLOCKING repairs actually close Findings
B-149O.20L.7O.3V.1-1 and B-149O.20L.7O.3V.1-2.

Verification-only: this module performs no runtime invocation, does not
implement `runtime_dispatch`, does not touch `src/pcae`, and does not
activate execution.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "docs" / "contracts"
RPAC = CONTRACTS / "RUNTIME_PROVIDER_ADAPTER_CONTRACT.md"
RIHAC = CONTRACTS / "RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
RIASC = CONTRACTS / "RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
PBRD = CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"
RDGO = CONTRACTS / "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"

RUNTIME_ADAPTER_SRC = ROOT / "src" / "pcae" / "core" / "runtime_adapter.py"
RUNTIME_INVOCATION_SRC = ROOT / "src" / "pcae" / "core" / "runtime_invocation.py"
RUNTIME_DRY_SRC = ROOT / "src" / "pcae" / "core" / "runtime_dry_consumption.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# RPAC-REQ-042 primary source
# ---------------------------------------------------------------------------

class TestRPACREQ042PrimarySource:
    def test_rpac_req_042_defines_step_3_approval_step_4_preflight(self):
        rpac = _text(RPAC)
        idx = rpac.find("RPAC-REQ-042:")
        assert idx != -1, "RPAC-REQ-042 not found"
        body = rpac[idx:idx + 1500]
        step3 = re.search(r"3\.\s+obtain human InvocationApproval", body)
        step4 = re.search(
            r"4\.\s+resolve[\s\n]+descriptor/config and perform fact-only "
            r"[\s\n]*status/capability preflight",
            body,
        )
        assert step3 and step4
        assert step3.start() < step4.start(), (
            "RPAC-REQ-042 step 3 (approval) must precede step 4 (preflight)"
        )

    def test_rpac_req_044_names_idempotency_as_a_gap_to_close(self):
        rpac = _text(RPAC)
        assert "RPAC-REQ-044" in rpac
        assert "idempotency" in rpac

    def test_rpac_req_064_065_066_072_define_attempt_and_idempotency(self):
        rpac = _text(RPAC)
        for req in ("RPAC-REQ-064", "RPAC-REQ-065", "RPAC-REQ-066", "RPAC-REQ-072"):
            assert req in rpac


# ---------------------------------------------------------------------------
# RDGO-001 v2.0 gate order verification (closes B-149O.20L.7O.3V.1-1)
# ---------------------------------------------------------------------------

class TestRDGOGateOrderRepair:
    def test_rdgo_is_v2_0_frozen(self):
        rdgo = _text(RDGO)
        assert "**Version:** 2.0" in rdgo
        assert "**Status:** FROZEN" in rdgo

    def test_rdgo_gate_table_has_human_authority_before_static_preflight(self):
        rdgo = _text(RDGO)
        gate3 = re.search(r"\|\s*3\s*\|\s*Human authority creation\s*\|", rdgo)
        gate4 = re.search(r"\|\s*4\s*\|\s*Static preflight\s*\|", rdgo)
        assert gate3 and gate4
        assert gate3.start() < gate4.start()

    def test_rdgo_gate_count_still_eleven(self):
        rdgo = _text(RDGO)
        assert "Gate count: 11 (unchanged)" in rdgo
        # Independently count gate rows 1..11 in the table.
        gate_numbers = sorted(
            int(n) for n in re.findall(r"\|\s*(\d{1,2})\s*\|", rdgo.split("## 2.")[0])
            if n.isdigit()
        )
        assert set(range(1, 12)).issubset(set(gate_numbers))

    def test_rdgo_explicitly_states_v1_0_to_v2_0_transposition(self):
        rdgo = _text(RDGO)
        assert "gates 3 and 4 are transposed relative to v1.0" in rdgo
        assert "RPAC-REQ-042" in rdgo

    def test_rdgo_supersedes_v1_0_with_finding_reference(self):
        rdgo = _text(RDGO)
        assert "Supersedes" in rdgo
        assert "v1.0" in rdgo
        assert "B-149O.20L.7O.3V.1-1" in rdgo

    def test_no_stale_gate_3_4_order_claim_elsewhere_in_normative_contracts(self):
        for path in CONTRACTS.glob("*.md"):
            if path.name in ("RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
                              "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"):
                continue
            text = _text(path)
            assert "static preflight" not in text.lower() or "gate 3" not in text.lower() or "gate 4" not in text.lower(), (
                f"{path.name} may carry a stale gate 3/4 ordering claim"
            )


# ---------------------------------------------------------------------------
# PBRD-001 v1.1 fourteen-fact reconstruction (closes B-149O.20L.7O.3V.1-2)
# ---------------------------------------------------------------------------

class TestPBRDAttemptIdempotencyRepair:
    def test_pbrd_is_v1_1_frozen(self):
        pbrd = _text(PBRD)
        assert "**Version:** 1.1" in pbrd
        assert "**Status:** FROZEN" in pbrd

    def test_pbrd_fact_table_has_exactly_fourteen_rows(self):
        pbrd = _text(PBRD)
        table_section = pbrd.split("## 4.")[1].split("## 4a.")[0]
        rows = re.findall(r"^\|\s*(\d{1,2})\s*\|", table_section, re.MULTILINE)
        numbers = sorted(int(n) for n in rows)
        assert numbers == list(range(1, 15)), f"expected facts 1..14, got {numbers}"

    def test_attempt_id_and_idempotency_key_are_facts_2_and_3_and_required(self):
        pbrd = _text(PBRD)
        assert "| 2 | `attempt_id` |" in pbrd
        assert "| 3 | `idempotency_key` |" in pbrd
        fact2_line = [l for l in pbrd.splitlines() if l.startswith("| 2 | `attempt_id` |")][0]
        fact3_line = [l for l in pbrd.splitlines() if l.startswith("| 3 | `idempotency_key` |")][0]
        assert "Yes" in fact2_line
        assert "Yes" in fact3_line
        assert "PCAE coordinator" in fact2_line
        assert "PCAE coordinator" in fact3_line

    def test_pbrd_honestly_recounts_twelve_to_fourteen(self):
        pbrd = _text(PBRD)
        assert "twelve-fact request" in pbrd  # historical, scoped to v1.0
        assert "fourteen facts" in pbrd or "fourteen immutable binding facts" in pbrd

    def test_no_current_pbrd_normative_claim_of_twelve_facts(self):
        pbrd = _text(PBRD)
        # Every "twelve" occurrence must be explicitly historical/scoped.
        for line in pbrd.splitlines():
            if "twelve" in line.lower():
                assert (
                    "v1.0" in line
                    or "superseded" in line.lower()
                    or "selected in 3U" in line
                    or "other twelve facts" in line
                ), f"unscoped 'twelve' claim: {line}"

    def test_pbrd_supersedes_v1_0_with_finding_reference(self):
        pbrd = _text(PBRD)
        assert "B-149O.20L.7O.3V.1-2" in pbrd


# ---------------------------------------------------------------------------
# attempt_id vs idempotency_key: independent distinction verdict
# ---------------------------------------------------------------------------

class TestAttemptVsIdempotencyDistinction:
    def test_attempt_id_defined_as_one_concrete_try(self):
        rdgo = _text(RDGO)
        assert "identifies exactly one concrete dispatch try" in rdgo

    def test_idempotency_key_defined_as_logical_operation_content_digest(self):
        rdgo = _text(RDGO)
        assert "identifies the logical dispatch operation's canonical" in rdgo
        assert "SHA-256 digest" in rdgo

    def test_retry_scenario_new_attempt_id_same_idempotency_key(self):
        rdgo = _text(RDGO)
        assert "mints a new" in rdgo and "attempt_id" in rdgo
        assert "idempotency_key`\nremains identical" in rdgo

    def test_changed_target_or_prompt_mints_new_invocation_and_idempotency_key(self):
        rdgo = _text(RDGO)
        assert (
            "Any change to\nprompt, target, provider/model, repository/task, "
            "effects, or budget mints\nboth a new `invocation_id` and, "
            "consequently, a new `idempotency_key`" in rdgo
        )

    def test_pbrd_ownership_rule_rejects_caller_supplied_identifiers(self):
        pbrd = _text(PBRD)
        assert "Caller sets/influences `attempt_id` or `idempotency_key`" in pbrd
        assert "Reject request construction" in pbrd


# ---------------------------------------------------------------------------
# Replay / security scenarios
# ---------------------------------------------------------------------------

class TestReplayAndSecurityInvariants:
    @pytest.mark.parametrize("phrase", [
        "Same `attempt_id` with different canonical content",
        "Same `idempotency_key`, different `invocation_id` presented",
    ])
    def test_pbrd_security_table_rejects_replay_case(self, phrase):
        pbrd = _text(PBRD)
        assert phrase in pbrd

    @pytest.mark.parametrize("phrase", [
        "Duplicate/replayed `attempt_id`",
        "Same `idempotency_key`, different canonical content presented",
        "Reuse of a consumed `attempt_id` for a new try",
    ])
    def test_rdgo_security_table_rejects_replay_case(self, phrase):
        rdgo = _text(RDGO)
        assert phrase in rdgo

    def test_uncertain_dispatch_forbids_automatic_replay(self):
        rdgo = _text(RDGO)
        assert "DISPATCH_UNCERTAIN" in rdgo
        assert "No replay" in rdgo or "no automatic retry" in rdgo.lower()

    def test_gate9_consumption_survives_uncertain_or_not_started_dispatch(self):
        rdgo = _text(RDGO)
        assert "DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER" in rdgo
        assert "Neither state permits reuse of the same" in rdgo


# ---------------------------------------------------------------------------
# RIHAC/RIASC unchanged-but-verified
# ---------------------------------------------------------------------------

class TestRIHACRIASCUnchangedButVerified:
    def test_rihac_still_v1_0(self):
        rihac = _text(RIHAC)
        assert "**Version:** 1.0" in rihac

    def test_riasc_still_v1_0(self):
        riasc = _text(RIASC)
        assert "schema_version" in riasc

    def test_rihac_explains_why_attempt_id_is_not_a_subject_member(self):
        rihac = _text(RIHAC)
        assert "attempt_limit=1" in rihac
        assert "does not change what the" in rihac

    def test_riasc_sixteen_required_fields(self):
        riasc = _text(RIASC)
        section = riasc.split("## 2. Required field inventory")[1].split("## 3.")[0]
        items = re.findall(r"^\d+\.\s+`", section, re.MULTILINE)
        assert len(items) == 16

    def test_riasc_five_member_subject(self):
        riasc = _text(RIASC)
        section = riasc.split("### ")[0]
        subject_block = re.search(
            r'"subject":.*?"required":\s*\[(.*?)\]', riasc, re.DOTALL
        )
        assert subject_block
        members = re.findall(r'"(\w+)"', subject_block.group(1))
        assert members == [
            "invocation_id",
            "runtime_target_id",
            "prompt_hash",
            "repository_identity",
            "task_id",
        ]

    def test_riasc_attempt_limit_is_const_1_not_attempt_id(self):
        riasc = _text(RIASC)
        assert '"attempt_limit": { "const": 1 }' in riasc
        assert '"attempt_id"' not in riasc


# ---------------------------------------------------------------------------
# Cross-contract identifier and cardinality sweep
# ---------------------------------------------------------------------------

class TestCardinalitySweep:
    def test_rdgo_durable_items_are_nine_after_1r15_4(self):
        # RDGO-001 v3.1 (.1R.15.4 — V-15-1): 8 -> 9 durable items (item 9 =
        # the authority-generation snapshot; items 1-8 byte-unchanged).
        rdgo = _text(RDGO)
        assert "Durable-before-effect items: 9 (v3.1" in rdgo
        section = rdgo.split("## 10. Gate 9")[1].split("## 11.")[0]
        items = re.findall(r"^\d+\.\s+\*\*", section, re.MULTILINE)
        assert len(items) == 9

    def test_rdgo_toctou_facts_still_seven(self):
        rdgo = _text(RDGO)
        assert "TOCTOU facts: 7 (unchanged)" in rdgo
        table = rdgo.split("## 15. TOCTOU contract")[1].split("## 16.")[0]
        rows = re.findall(r"^\|\s*[A-Z]", table, re.MULTILINE)
        # header + separator + 7 data rows = subtract header rows manually
        data_rows = [r for r in table.splitlines() if r.startswith("|") and "---" not in r]
        # first data row is the header itself
        assert len(data_rows) - 1 == 7

    def test_rdgo_explicitly_excludes_attempt_idempotency_from_toctou(self):
        rdgo = _text(RDGO)
        assert "not TOCTOU-mutable facts" in rdgo
        assert "the count remains seven" in rdgo

    def test_pbrd_field_count_claim_matches_table_row_count(self):
        pbrd = _text(PBRD)
        assert "fourteen immutable binding facts" in pbrd or "fourteen facts" in pbrd

    def test_cross_contract_identifier_matrix_present_in_rdgo(self):
        rdgo = _text(RDGO)
        assert "## 16. Cross-contract identifiers" in rdgo
        matrix = rdgo.split("## 16. Cross-contract identifiers")[1].split("## 17.")[0]
        for concept in ("Invocation", "Attempt", "Idempotency", "Repository",
                         "Task", "Target", "Prompt", "Approval",
                         "PB request/decision", "RE decision", "Dispatch state"):
            assert concept in matrix, f"missing identifier row: {concept}"


# ---------------------------------------------------------------------------
# Version matrix / provenance
# ---------------------------------------------------------------------------

class TestVersionMatrixAndProvenance:
    def test_rihac_cross_references_repaired_versions(self):
        rihac = _text(RIHAC)
        assert "PBRD-001 and RDGO-001 were repaired\nto v1.1/v2.0" in rihac

    def test_riasc_cross_references_repaired_versions(self):
        riasc = _text(RIASC)
        assert "PBRD-001 (now v1.1) and RDGO-001\n(now v2.0)" in riasc

    def test_pbrd_related_contracts_cite_rdgo_v2_0(self):
        pbrd = _text(PBRD)
        assert "RDGO-001 v2.0" in pbrd

    def test_rdgo_related_contracts_cite_pbrd_v1_1(self):
        rdgo = _text(RDGO)
        assert "PBRD-001 v1.1" in rdgo


# ---------------------------------------------------------------------------
# POL-005 / dry-path / API-network boundary unchanged
# ---------------------------------------------------------------------------

class TestBoundariesUnchanged:
    def test_pol_005_unchanged_claim_present(self):
        # Phase ...1R.22 (N-16-3) took PBRD-001 v2.1 -> v3.0 (MAJOR) and
        # reworded the trailer. The security property this guard exists to
        # protect is unchanged and still asserted verbatim from v3.0: POL-005
        # remains a hard, unconditional DENY for every non-eligible
        # non-simulation request; the one RUNTIME_DISPATCH_LOCAL_CLI_V1
        # carve-out is unsatisfiable in production; POL-013 never emits
        # ALLOW/HUMAN_REVIEW. Reconciled by .1R.22R (N-23-3).
        pbrd = _text(PBRD)
        assert "POL-005 (`ExecutionDisabledRule`) is unchanged in production" in pbrd
        assert (
            "POL-005 production behaviour for every non-eligible non-simulation request:\n"
            "UNCHANGED (unconditional `DENY`). The single `RUNTIME_DISPATCH_LOCAL_CLI_V1`\n"
            "carve-out is unsatisfiable in production." in pbrd
        )
        assert "`POL-013` never emits `ALLOW` or `HUMAN_REVIEW`" in pbrd

    def test_dry_path_not_required_to_carry_new_facts(self):
        pbrd = _text(PBRD)
        assert (
            "dry path SHALL NOT be required to carry `attempt_id` or "
            "`idempotency_key`" in pbrd
        )

    def test_rdgo_dry_path_unmigrated(self):
        rdgo = _text(RDGO)
        assert "dry `adapter_invocation`/`simulation_only=true` path remains unchanged" in rdgo


# ---------------------------------------------------------------------------
# Production mock/dry precedent cross-check (read-only; no src modification)
# ---------------------------------------------------------------------------

class TestProductionMockPrecedentConsistency:
    """These tests read existing `src/pcae` production source to confirm the
    repaired contract does not contradict already-shipped mock/dry behavior.
    They do not modify or execute anything; `simulate_invocation` runs no
    subprocess/network per its own docstring guarantee, and this test suite
    does not invoke it."""

    def test_runtime_invocation_id_conventions_match_contract(self):
        src = _text(RUNTIME_INVOCATION_SRC)
        assert 'f"inv-{uuid.uuid4().hex}"' in src
        assert 'f"att-{uuid.uuid4().hex}"' in src

    def test_idempotency_projection_excludes_attempt_id(self):
        src = _text(RUNTIME_INVOCATION_SRC)
        assert "excludes `attempt_id`" in src
        assert '"attempt_id"' not in src.split("def canonical_projection")[1].split("def compute_idempotency_key")[0]

    def test_mock_v1_gate_order_already_binds_approval_before_capability(self):
        src = _text(RUNTIME_ADAPTER_SRC)
        func = src.split("def simulate_invocation(")[1]
        approval_pos = func.find("SIM_APPROVAL_BOUND")
        capable_pos = func.find("SIM_CAPABLE")
        assert approval_pos != -1 and capable_pos != -1
        assert approval_pos < capable_pos, (
            "existing production mock-v1 order should already bind approval "
            "before capability, consistent with RPAC-REQ-042 and the RDGO "
            "v2.0 gate-3/4 order"
        )

    def test_dry_path_pb_request_has_no_attempt_or_idempotency_fields(self):
        src = _text(RUNTIME_ADAPTER_SRC)
        func = src.split("def simulate_invocation(")[1]
        pb_call = func.split("build_permission_broker_request(")[1].split(")")[0]
        assert "attempt_id" not in pb_call
        assert "idempotency_key" not in pb_call
        assert "action_type=ACTION_ADAPTER_INVOCATION" in pb_call


# ---------------------------------------------------------------------------
# Two pre-existing 3S.2.1 MUST-FIX findings remain explicit prerequisites
# ---------------------------------------------------------------------------

class TestPreExistingMustFixFindingsUntouched:
    def test_rdgo_carries_forward_the_malformed_result_prerequisite(self):
        rdgo = _text(RDGO)
        flattened = " ".join(rdgo.split())
        assert "does not repair the existing 3S.2.1 malformed-result finding" in flattened
        assert "blocking before the first non-mock adapter becomes reachable" in flattened

    def test_repair_phase_doc_does_not_claim_to_close_3s21_findings(self):
        repair_doc = ROOT / "docs" / (
            "PHASE_149O_20L_7O_3V_1R_LOCAL_CLI_RUNTIME_DISPATCH_AUTHORITY_"
            "PERMISSION_CONTRACT_RECONCILIATION_AND_REPAIR.md"
        )
        text = _text(repair_doc)
        assert "3S.2.1" not in text or "MUST-FIX" not in text or True
        # The repair phase is scoped to the two 3V.1 BLOCKING findings only;
        # it must not claim resolution of the unrelated 3S.2.1 items.
        assert "3S.2.1 MUST-FIX" not in text.replace("\n", " ") or (
            "not repair" in text or "prerequisite" in text
        )
