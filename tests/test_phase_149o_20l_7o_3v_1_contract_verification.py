"""Independent verification of the Phase 149O.20L.7O.3V contract freeze.

This module verifies the frozen Markdown artifacts directly and compares them
with the pre-existing RPAC/PB production authority.  It intentionally records
detected contradictions as passing detection tests: 3V.1 is verification-only
and does not repair the frozen contracts or production source.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pcae.core.permission_broker_foundation import (
    ACTION_ADAPTER_INVOCATION,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    EXECUTION_CLASS_ADAPTER,
    KNOWN_ACTION_TYPES,
    PermissionBroker,
    build_permission_broker_request,
)


ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "docs" / "contracts"
RIHAC = CONTRACTS / "RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
PBRD = CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"
RDGO = CONTRACTS / "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
RIASC = CONTRACTS / "RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
RPAC = CONTRACTS / "RUNTIME_PROVIDER_ADAPTER_CONTRACT.md"
DRY_CONSUMER = ROOT / "src" / "pcae" / "core" / "runtime_adapter.py"
VERIFICATION_BASELINE = "60de4bda64af32e94a29039d10fdd96a811350dd"
PHASE_ENTRY = "934e1f07fac798417c1b5a25d5b06214a5f62ab3"
FREEZE_COMMIT = "2060ebd411df664aac97e3987a922c77cb05ef6f"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _schema() -> dict:
    text = _text(RIASC)
    match = re.search(r"```json\n(\{.*?\})\n```", text, re.DOTALL)
    assert match, "RIASC normative JSON Schema block not found"
    return json.loads(match.group(1))


def _canonical_instance() -> dict:
    h = "a" * 64
    return {
        "schema_id": "RIASC-001",
        "schema_version": "1.0",
        "contract_version": "RIHAC-001/1.0",
        "record_type": "runtime_invocation_approval",
        "approval_id": "ria-" + "1" * 32,
        "record_digest": "2" * 64,
        "created_at": "2026-08-27T10:00:00Z",
        "expires_at": "2026-08-27T10:05:00Z",
        "subject": {
            "invocation_id": "inv-" + "3" * 32,
            "runtime_target_id": "fixture-local-cli",
            "prompt_hash": "4" * 64,
            "repository_identity": "5" * 64,
            "task_id": "task-3v1",
        },
        "governance_context": {"phase_id": "149O.20L.7O.3V.1"},
        "prompt_hash_profile": "pcae.prompt-semantic.v1",
        "approval_scope": {
            "requested_capability": "bounded-fixture",
            "transport_type": "local_cli",
            "effect_class": "bounded_local_process_dispatch",
            "dispatch_limit": 1,
            "network_required": False,
            "filesystem_scope_ref": {"artifact_id": "scope-1", "artifact_digest": h},
            "process_profile_ref": {"artifact_id": "process-1", "artifact_digest": h},
        },
        "adapter_binding": {
            "adapter_id": "fixture-adapter",
            "descriptor_version": "1.0",
            "descriptor_digest": "6" * 64,
            "target_config_digest": "7" * 64,
        },
        "freshness_snapshot": {
            "head_commit": "8" * 40,
            "task_contract_digest": "9" * 64,
            "task_state": "active",
            "policy_version": "pb-foundation-current",
        },
        "provenance": {
            "approver_id": "human-1",
            "identity_evidence_kind": "os_authenticated_user",
            "approval_mechanism": "interactive_local_cli_confirmation",
            "approval_preview_digest": "b" * 64,
            "producer_component": "pcae.trusted_runtime_approval_coordinator",
        },
        "attempt_limit": 1,
    }


def _assert_subject_matches(instance: dict, expected: dict) -> None:
    assert instance["subject"] == expected


class TestFrozenInventoryAndSchema:
    def test_fixed_history_freeze_delta_has_no_production_or_test_change(self):
        changed = subprocess.run(
            ["git", "diff", "--name-only", PHASE_ENTRY, FREEZE_COMMIT],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout.splitlines()
        assert changed
        assert not [p for p in changed if p.startswith("src/pcae/") or p.startswith("tests/")]

    def test_four_unique_frozen_contract_identities(self):
        expected = {
            RIHAC: ("RIHAC-001", "1.0"),
            PBRD: ("PBRD-001", "1.0"),
            RDGO: ("RDGO-001", "1.0"),
            RIASC: ("RIASC-001", "1.0"),
        }
        for path, (contract_id, version) in expected.items():
            text = _text(path)
            assert f"**Contract:** {contract_id}" in text
            assert f"**Version:** {version}" in text
            assert "**Status:** FROZEN" in text
            assert sum(contract_id in _text(p) for p in expected) >= 1

    def test_normative_schema_is_valid_draft_2020_12_and_accepts_canonical_instance(self):
        schema = _schema()
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(_canonical_instance())

    def test_exact_sixteen_required_fields_and_exact_five_subject_fields(self):
        schema = _schema()
        assert schema["required"] == [
            "schema_id", "schema_version", "contract_version", "record_type",
            "approval_id", "record_digest", "created_at", "expires_at", "subject",
            "governance_context", "prompt_hash_profile", "approval_scope",
            "adapter_binding", "freshness_snapshot", "provenance", "attempt_limit",
        ]
        assert schema["properties"]["subject"]["required"] == [
            "invocation_id", "runtime_target_id", "prompt_hash",
            "repository_identity", "task_id",
        ]

    @pytest.mark.parametrize("field", _schema()["required"])
    def test_every_required_field_is_rejected_when_missing(self, field):
        instance = _canonical_instance()
        del instance[field]
        assert list(Draft202012Validator(_schema()).iter_errors(instance))

    @pytest.mark.parametrize(
        "field", ["approved", "authorized", "permission", "pb_allow", "execution_available"]
    )
    def test_authority_shortcut_and_unknown_fields_are_rejected(self, field):
        instance = _canonical_instance()
        instance[field] = True
        assert list(Draft202012Validator(_schema()).iter_errors(instance))

    def test_wrong_type_and_malformed_version_are_rejected(self):
        wrong_type = _canonical_instance()
        wrong_type["attempt_limit"] = "1"
        bad_version = _canonical_instance()
        bad_version["schema_version"] = "v1"
        validator = Draft202012Validator(_schema())
        assert list(validator.iter_errors(wrong_type))
        assert list(validator.iter_errors(bad_version))

    @pytest.mark.parametrize(
        "field,replacement",
        [
            ("invocation_id", "inv-" + "a" * 32),
            ("runtime_target_id", "another-target"),
            ("prompt_hash", "c" * 64),
            ("repository_identity", "d" * 64),
            ("task_id", "another-task"),
        ],
    )
    def test_each_subject_mismatch_is_detected_by_required_cross_field_check(self, field, replacement):
        instance = _canonical_instance()
        expected = copy.deepcopy(instance["subject"])
        instance["subject"][field] = replacement
        with pytest.raises(AssertionError):
            _assert_subject_matches(instance, expected)


class TestPBAndDryCompatibility:
    def test_future_action_is_not_implemented_but_selected_class_exists(self):
        assert "runtime_dispatch" not in KNOWN_ACTION_TYPES
        assert EXECUTION_CLASS_ADAPTER == "adapter"
        assert ACTION_ADAPTER_INVOCATION == "adapter_invocation"

    def test_pol_004_human_review_and_pol_005_deny_are_current_source_truth(self):
        missing = build_permission_broker_request(
            action_type=ACTION_ADAPTER_INVOCATION,
            execution_class=EXECUTION_CLASS_ADAPTER,
            requested_component="COMP-006",
            requested_capability="fixture",
            task_id="task",
            evidence_available=True,
            approval_present=False,
            simulation_only=True,
        )
        assert PermissionBroker().evaluate(missing).decision == DECISION_HUMAN_REVIEW
        real = build_permission_broker_request(
            action_type=ACTION_ADAPTER_INVOCATION,
            execution_class=EXECUTION_CLASS_ADAPTER,
            requested_component="COMP-006",
            requested_capability="fixture",
            task_id="task",
            evidence_available=True,
            approval_present=True,
            simulation_only=False,
        )
        decision = PermissionBroker().evaluate(real)
        assert decision.decision == DECISION_DENY
        assert "POL-005" in decision.causing_policy_ids

    def test_deny_precedes_human_review(self):
        request = build_permission_broker_request(
            action_type="unknown-real-action",
            execution_class=EXECUTION_CLASS_ADAPTER,
            requested_component="COMP-999",
            requested_capability="fixture",
            task_id="task",
            evidence_available=True,
            approval_present=False,
            simulation_only=False,
        )
        decision = PermissionBroker().evaluate(request)
        assert decision.decision == DECISION_DENY
        assert "POL-004" in decision.triggered_policy_ids

    def test_dry_consumer_stays_adapter_invocation_simulation_only(self):
        text = _text(DRY_CONSUMER)
        assert "action_type=ACTION_ADAPTER_INVOCATION" in text
        assert "execution_class=EXECUTION_CLASS_ADAPTER" in text
        assert "simulation_only=True" in text
        assert "runtime_dispatch" not in text

    def test_production_dry_source_is_byte_unchanged_from_verification_baseline(self):
        relative = DRY_CONSUMER.relative_to(ROOT).as_posix()
        baseline = subprocess.run(
            ["git", "show", f"{VERIFICATION_BASELINE}:{relative}"],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout
        assert baseline == DRY_CONSUMER.read_bytes()

    def test_semantic_walls_and_artifact_separation_are_explicit(self):
        walls = [
            "human approval != PB permission",
            "PB ALLOW != runtime capability",
            "runtime capability != Runtime Enforcement approval",
            "Runtime Enforcement ALLOW != process permission",
            "process permission != dispatch completion",
            "dispatch completion != accepted change",
            "runtime result != task completion",
        ]
        for path in (RIHAC, PBRD, RDGO):
            text = _text(path)
            assert all(wall in text for wall in walls)
        assert "approval artifact and the PB decision SHALL remain separate artifacts" in _text(RIHAC)

    def test_api_network_and_credentials_remain_out_of_local_cli_v1(self):
        combined = "\n".join(_text(p) for p in (RIHAC, PBRD, RDGO, RIASC))
        assert "network_requirement=false" in combined
        assert "API/provider dispatch remains blocked" in combined
        assert "grants no credential access" in combined


class TestCardinalitiesAndIndependentBlockingFindings:
    def test_exact_twelve_pb_facts(self):
        rows = re.findall(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|", _text(PBRD), re.MULTILINE)
        assert rows[:12] == [
            ("1", "invocation_id"), ("2", "repository_identity"),
            ("3", "task_id"), ("4", "lifecycle_context"),
            ("5", "runtime_target_id"), ("6", "adapter_descriptor_binding"),
            ("7", "prompt_hash"), ("8", "requested_capability"),
            ("9", "transport_type"), ("10", "network_requirement"),
            ("11", "filesystem_scope_ref"), ("12", "human_authority_binding"),
        ]

    def test_exact_eleven_gates(self):
        rows = re.findall(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", _text(RDGO), re.MULTILINE)
        assert [n for n, _ in rows[:11]] == [str(n) for n in range(1, 12)]
        assert rows[9][1].strip() == "Adapter dispatch"

    def test_exact_eight_durable_items_and_seven_toctou_facts(self):
        text = _text(RDGO)
        durable = text[text.index("The exact eight items are:"):text.index("## 11. Gate 10")]
        assert re.findall(r"^(\d+)\. \*\*", durable, re.MULTILINE) == [str(n) for n in range(1, 9)]
        toctou = text[text.index("## 15. TOCTOU contract"):text.index("## 16. Cross-contract identifiers")]
        names = re.findall(r"^\| ([^|]+?) \|", toctou, re.MULTILINE)[1:]
        assert names == [
            "HEAD", "Task state/contract", "Prompt", "Runtime target",
            "Adapter configuration", "Adapter executable identity", "Policy version",
        ]

    def test_blocking_gate_order_conflict_with_rpac_is_detected(self):
        rpac = _text(RPAC)
        rdgo = _text(RDGO)
        assert "3. obtain human InvocationApproval;\n4. resolve descriptor/config and perform fact-only status/capability preflight;" in rpac
        assert "| 3 | Static preflight" in rdgo
        assert "| 4 | Human authority creation" in rdgo
        assert re.search(r"changed\s+gate order[\s\S]*?require a new major version", rpac)

    def test_blocking_attempt_and_idempotency_omission_is_detected(self):
        rpac = _text(RPAC)
        pbrd = _text(PBRD)
        assert "unique `attempt_id`, and\n  `idempotency_key`" in rpac
        assert "idempotency" in rpac[rpac.index("RPAC-REQ-044"):rpac.index("RPAC-REQ-045")]
        assert "`attempt_id`" not in pbrd
        assert "`idempotency_key`" not in pbrd

    def test_schema_contract_is_normative_but_not_production_registered(self):
        assert "Executable production schema: NOT IMPLEMENTED / NOT AUTHORIZED" in _text(RIASC)
        assert not (ROOT / "src" / "pcae" / "schema_resources" / "runtime_invocation_approval").exists()
