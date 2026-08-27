"""Fresh independent verification of the 3W.1R.2B contract freeze.

Verification-only: these tests read frozen Markdown and fixed git objects.
They perform no hardware access, runtime invocation, network access, or
production mutation.  Contradictions are asserted as passing *detection*
tests so the suite records a reproducible NOT VERIFIED verdict rather than
silently repairing the frozen contracts.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "docs" / "contracts"
HPAC = CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
RIHAC = CONTRACTS / "RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
RIASC = CONTRACTS / "RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
PBRD = CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"
RDGO = CONTRACTS / "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
RPAC = CONTRACTS / "RUNTIME_PROVIDER_ADAPTER_CONTRACT.md"
HATP = CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
HPSE = CONTRACTS / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
RUNTIME_AUTHORITY = ROOT / "src" / "pcae" / "core" / "runtime_authority.py"

VERIFICATION_ENTRY = "1991726db1db1504c9ad7e98b321b1dc3859fab7"
PRE_FREEZE = "ca09ab39"
FREEZE_COMMIT = "f2894044"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _git_show(revision: str, path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _schema(text: str) -> dict:
    match = re.search(r"```json\n(\{.*?\})\n```", text, re.DOTALL)
    assert match, "normative Draft 2020-12 JSON block not found"
    return json.loads(match.group(1))


def _canonical_v2_instance() -> dict:
    digest = "a" * 64
    return {
        "schema_id": "RIASC-001",
        "schema_version": "2.0",
        "contract_version": "RIHAC-001/1.1",
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
            "task_id": "task-3w1r2b1",
        },
        "governance_context": {"phase_id": "149O.20L.7O.3W.1R.2B.1"},
        "prompt_hash_profile": "pcae.prompt-semantic.v1",
        "approval_scope": {
            "requested_capability": "bounded-fixture",
            "transport_type": "local_cli",
            "effect_class": "bounded_local_process_dispatch",
            "dispatch_limit": 1,
            "network_required": False,
            "filesystem_scope_ref": {
                "artifact_id": "scope-1",
                "artifact_digest": digest,
            },
            "process_profile_ref": {
                "artifact_id": "process-1",
                "artifact_digest": digest,
            },
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
            "principal_id": "principal-1",
            "authentication_mechanism_id": "hpac.fido2.presence_gated.v1",
            "credential_id": "credential-1",
            "authentication_proof_ref": {
                "artifact_id": "proof-1",
                "artifact_digest": "b" * 64,
            },
            "approval_mechanism": "interactive_local_cli_confirmation",
            "approval_preview_digest": "c" * 64,
            "producer_component": "pcae.trusted_runtime_approval_coordinator",
        },
        "attempt_limit": 1,
    }


def _section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


class TestFreezeInventoryAndVersionDelta:
    def test_verification_entry_is_the_recorded_clean_baseline(self):
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", VERIFICATION_ENTRY, "HEAD"],
            cwd=ROOT,
        ).returncode == 0

    def test_freeze_changed_exactly_three_normative_contracts(self):
        changed = subprocess.run(
            ["git", "diff", "--name-only", PRE_FREEZE, FREEZE_COMMIT, "--", "docs/contracts"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        assert changed == [
            "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
            "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
            "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        ]

    def test_current_and_historical_contract_identities_are_exact(self):
        assert "# RIHAC-001 v1.1" in _text(RIHAC)
        assert "# RIASC-001 v2.0" in _text(RIASC)
        assert "# HPAC-001 v1.0" in _text(HPAC)
        assert "# RIHAC-001 v1.0" in _git_show(PRE_FREEZE, RIHAC)
        assert "# RIASC-001 v1.0" in _git_show(PRE_FREEZE, RIASC)

    def test_rihac_delta_is_a_mandatory_semantic_change_not_optional_evidence(self):
        old = _git_show(PRE_FREEZE, RIHAC)
        new = _text(RIHAC)
        assert "No cryptographic signature is required for v1" in old
        assert 'sentence "No cryptographic signature is\nrequired for v1" is retired' in new
        assert "A cryptographic signature or assertion is now\nrequired for every approval" in new
        assert "semantic redefinition" in new and "requires a new\nMAJOR" in new

    def test_rihac_delta_locations_are_fully_recovered(self):
        delta = subprocess.run(
            ["git", "diff", "--unified=0", PRE_FREEZE, FREEZE_COMMIT, "--", str(RIHAC.relative_to(ROOT))],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        for phrase in (
            "what \"identified by provenance evidence\"",
            "successful HPAC-001 authentication-proof verification",
            "principal/credential revocation is a distinct",
            "load the referenced",
            "v1.0 → v1.1",
        ):
            assert phrase in delta

    def test_riasc_major_version_is_justified_and_cardinality_is_exact(self):
        old_schema = _schema(_git_show(PRE_FREEZE, RIASC))
        new_schema = _schema(_text(RIASC))
        assert len(old_schema["required"]) == len(new_schema["required"]) == 16
        assert len(old_schema["properties"]["subject"]["required"]) == 5
        assert len(new_schema["properties"]["subject"]["required"]) == 5
        assert old_schema["properties"]["provenance"]["required"] == [
            "approver_id",
            "identity_evidence_kind",
            "approval_mechanism",
            "approval_preview_digest",
            "producer_component",
        ]
        assert new_schema["properties"]["provenance"]["required"] == [
            "principal_id",
            "authentication_mechanism_id",
            "credential_id",
            "authentication_proof_ref",
            "approval_mechanism",
            "approval_preview_digest",
            "producer_component",
        ]


class TestRIASCV2Schema:
    def test_normative_schema_is_valid_and_accepts_a_canonical_instance(self):
        schema = _schema(_text(RIASC))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(_canonical_v2_instance())

    @pytest.mark.parametrize(
        "field",
        [
            "principal_id",
            "authentication_mechanism_id",
            "credential_id",
            "authentication_proof_ref",
            "approval_mechanism",
            "approval_preview_digest",
            "producer_component",
        ],
    )
    def test_every_v2_provenance_field_is_required(self, field):
        value = _canonical_v2_instance()
        del value["provenance"][field]
        assert list(Draft202012Validator(_schema(_text(RIASC))).iter_errors(value))

    def test_v1_fields_and_unknown_authority_shortcuts_are_rejected(self):
        validator = Draft202012Validator(_schema(_text(RIASC)))
        for field, value in (
            ("approver_id", "human"),
            ("identity_evidence_kind", "typed_confirmation_only"),
            ("approved", True),
        ):
            instance = _canonical_v2_instance()
            instance["provenance"][field] = value
            assert list(validator.iter_errors(instance))

    def test_schema_shape_alone_accepts_a_plausible_but_unverified_principal_claim(self):
        instance = _canonical_v2_instance()
        instance["provenance"].update(
            principal_id="legitimate-human",
            credential_id="legitimate-looking",
        )
        instance["provenance"]["authentication_proof_ref"]["artifact_id"] = "caller-created"
        Draft202012Validator(_schema(_text(RIASC))).validate(instance)
        assert "Schema-shape validation is necessary but insufficient" in _text(RIASC)
        assert "Failure of any check yields no validated-authority projection" in _text(RIASC)


class TestHPACPositiveInvariants:
    def test_requirement_ids_are_exactly_001_through_087(self):
        ids = [
            int(value)
            for value in re.findall(r"^- \*\*HPAC-REQ-(\d{3})(?: \([^)]*\))?\.\*\*", _text(HPAC), re.MULTILINE)
        ]
        assert ids == list(range(1, 88))

    def test_identity_exclusions_and_registry_mapping_are_explicit(self):
        hpac = _text(HPAC)
        for phrase in (
            "OS-level username",
            "Git `user.name`",
            "PCAE `--agent-id`",
            "artifact\n  `producer_component`",
            "credential_id`, `principal_id`, `mechanism_id`",
        ):
            assert phrase in hpac

    def test_primary_mechanism_up_uv_and_minimum_assurance_are_exact(self):
        hpac = _text(HPAC)
        assert "`hpac.fido2.presence_gated.v1`" in hpac
        assert "v1 minimum: UP required; UV\n  optional, deployment-configurable" in hpac
        assert "Minimum required assurance for real local-CLI v1\n  dispatch: `PRESENCE_GATED` or stronger" in hpac

    def test_domain_and_registry_separation_from_hatp_are_explicit(self):
        hpac = _text(HPAC)
        assert "`hpac.runtime_invocation_approval.v1`" in hpac
        assert "physically and logically separate from HATP's `registry.json`" in hpac
        assert "`principal_id` space is\n  independent of HATP's `principal_id` space" in hpac
        assert "SHALL NOT verify successfully as an HATP signing-ceremony" in hpac

    def test_nonce_subject_replay_and_session_caching_fail_closed(self):
        hpac = _text(HPAC)
        assert "cryptographically strong random bytes" in hpac
        assert "approval-preview\n  digest" in hpac
        assert "durable, checked-under-lock record of consumed\n  challenge/nonce values" in hpac
        assert "Each real invocation\n  requires its own fresh challenge and its own fresh proof" in hpac
        assert "No session-caching layer for authentication exists in\n  v1" in hpac

    def test_serialized_proof_is_untrusted_until_fresh_verification(self):
        hpac = _text(HPAC)
        assert "deserializing stored proof material SHALL NOT by\n  itself yield trusted `AuthenticatedHumanPrincipal` state" in hpac
        assert "every\n  consumption SHALL re-run §18's verification sequence" in hpac
        assert "never by direct construction from caller-\n  supplied strings or dicts" in hpac

    def test_privacy_offline_portability_and_delegation_are_explicit(self):
        hpac = _text(HPAC)
        assert "No secret, PIN, private key, or raw biometric" in hpac
        assert "SHALL function fully\n  offline" in hpac
        assert "macOS" in hpac and "Linux" in hpac
        assert "delegated/forked agent" in hpac
        assert "No automated or policy-based auto-authentication exists" in hpac


class TestBlockingTrustRootAndIntentFindings:
    def test_registry_protection_is_only_path_and_convention_not_same_user_enforcement(self):
        hpac = _text(HPAC)
        registry = _section(hpac, "## 7. Registry scope, path, and trust root", "## 8. Enrollment")
        config = _section(hpac, "## 28. Configuration authority", "## 29. Multiple principals")
        assert "outside any single\n  repository's own working tree" in registry
        assert "standalone,\n  non-agent-invocable admin tool" in registry
        for required_protection in (
            "Agent OS principal",
            "Human/Admin OS principal",
            "ACL",
            "not writable, replaceable, or deletable",
            "permission weakening",
        ):
            assert required_protection not in registry + config

    def test_hatp_precedent_requires_the_os_boundary_hpac_did_not_adopt(self):
        hatp = _text(HATP)
        hpac = _text(HPAC)
        for phrase in (
            "separate OS-enforced security context",
            "Agent OS principal and the Human/Admin",
            "NOT READY",
        ):
            assert phrase in hatp
        assert re.search(
            r"NOT writable, replaceable, or deletable by\s+the Agent OS principal",
            hatp,
        )
        assert "same OS account as the enrolled human" in hpac
        assert "separate OS-enforced security context" not in hpac

    def test_first_principal_bootstrap_has_no_verifiable_non_circular_authority_artifact(self):
        hpac = _text(HPAC)
        bootstrap = _section(hpac, "## 7. Registry scope, path, and trust root", "## 9. Credential ownership")
        assert "local admin/human\n  bootstrap ceremony" in bootstrap
        assert "fresh, separate human election" in bootstrap
        assert "never cryptographically verified by this writer" in bootstrap
        for missing in ("bootstrap_proof", "bootstrap_authority_record", "protected election store"):
            assert missing not in bootstrap

    def test_up_only_cannot_distinguish_the_named_human_and_no_exclusive_custody_is_frozen(self):
        hpac = _text(HPAC)
        assurance = _section(hpac, "## 14. Primary v1 mechanism", "## 16. Challenge subject")
        assert "someone touched it" in assurance
        assert "optional, deployment-configurable" in assurance
        assert "single-principal default" in assurance
        for exclusive_custody_rule in ("exclusive custody", "credential sharing is prohibited", "sole physical control"):
            assert exclusive_custody_rule not in hpac

    def test_blind_touch_has_no_nonforgeable_confirmation_evidence_or_trusted_display(self):
        hpac = _text(HPAC)
        riasc_schema = _schema(_text(RIASC))
        proof_fields = {
            "proof_id",
            "mechanism_id",
            "principal_id",
            "credential_id",
            "challenge_digest",
            "assertion",
            "authenticated_at",
            "verifier_version",
        }
        provenance_fields = set(riasc_schema["properties"]["provenance"]["required"])
        assert "approval_preview_digest" in provenance_fields
        assert not ({"confirmation_proof_ref", "human_intent_evidence", "trusted_display_digest"} & provenance_fields)
        assert "approval_mechanism" in provenance_fields  # const claim, not evidence
        assert "human-visible" not in hpac
        assert "trusted display" not in hpac
        assert proof_fields == set(re.findall(r"`([a-z_]+)`", _section(hpac, "## 17. Authentication proof", "## 18. Proof verification")))


class TestBlockingProofAndLifecycleContradictions:
    def test_hpac_has_no_normative_proof_schema_or_canonical_proof_store_contract(self):
        hpac = _text(HPAC)
        assert "```json" not in hpac
        assert "canonical proof store" not in hpac
        assert "canonical proof path" not in hpac
        assert "## 19. Authentication proof store" not in hpac
        assert not re.search(r"\.pcae/[^\n`]*proof", hpac)
        assert "from HPAC-001's canonical proof store" in _text(RIHAC)

    def test_proof_reference_field_names_conflict_between_prose_and_schema(self):
        riasc = _text(RIASC)
        assert "An `artifact_ref` (`proof_id`, `proof_digest`)" in riasc
        artifact_ref = _schema(riasc)["$defs"]["artifact_ref"]
        assert artifact_ref["required"] == ["artifact_id", "artifact_digest"]
        assert not {"proof_id", "proof_digest"} & set(artifact_ref["properties"])

    def test_rihac_requires_a_challenge_subject_field_hpac_proof_does_not_define(self):
        rihac = _text(RIHAC)
        hpac_proof = _section(_text(HPAC), "## 17. Authentication proof", "## 18. Proof verification")
        assert "`challenge_subject`" in rihac
        assert "`challenge_subject`" not in hpac_proof
        assert "`challenge_digest`" in hpac_proof

    def test_gate5_proof_consumption_conflicts_with_required_pre_gate9_revalidation(self):
        hpac = _text(HPAC)
        rihac = _text(RIHAC)
        rdgo = _text(RDGO)
        assert "Consumption is recorded\n  atomically with successful verification" in hpac
        assert "reject any proof\n  whose challenge/nonce is already so recorded" in hpac
        assert "Before gate 9" in rihac and "complete\n  validation" in rihac
        assert "They SHALL be\n  revalidated/re-evaluated" in rihac
        assert "Same approval only after full revalidation" in rdgo

    def test_revocation_does_not_invalidate_an_unconsumed_already_validated_approval(self):
        hpac = _text(HPAC)
        rihac = _text(RIHAC)
        assert "does not retroactively invalidate a `RuntimeInvocationApproval`\n  already validated" in hpac
        assert "An approval already validated\nat gate 5" in rihac
        assert "is not\nretroactively invalidated" in rihac

    def test_companion_contract_headers_still_pin_the_insecure_old_versions(self):
        assert "**Related contracts:** Permission Broker Foundation, PBPA-001 v1.0,\nPBPC-001 v1.2, RPAC-001 v1.0, RIHAC-001 v1.0" in _text(PBRD)
        assert "**Related contracts:** RPAC-001 v1.0, RIHAC-001 v1.0, RIASC-001 v1.0" in _text(RDGO)


class TestCompatibilityAndCurrentImplementationState:
    def test_rpac_approval_subject_and_gate_order_remain_compatible_in_shape(self):
        rpac = _text(RPAC)
        assert "Approval SHALL NOT be embedded as mutable state" in rpac
        assert "3. obtain human InvocationApproval" in rpac
        assert "4. resolve descriptor/config and perform fact-only status/capability preflight" in rpac
        assert "HATP artifacts SHALL NOT be reinterpreted as generic invocation\npermission" in rpac

    def test_pbrd_and_rdgo_were_byte_unchanged_by_the_freeze(self):
        for path in (PBRD, RDGO, RPAC):
            relative = path.relative_to(ROOT).as_posix()
            before = subprocess.run(
                ["git", "show", f"{PRE_FREEZE}:{relative}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
            after = subprocess.run(
                ["git", "show", f"{FREEZE_COMMIT}:{relative}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
            assert before == after

    def test_current_production_still_implements_v1_and_caller_supplied_identity(self):
        source = _text(RUNTIME_AUTHORITY)
        assert 'RIHAC_CONTRACT_VERSION = "RIHAC-001/1.0"' in source
        assert 'RIASC_SCHEMA_VERSION = "1.0"' in source
        assert "approver_id: str" in source
        assert "identity_evidence_kind: str" in source
        assert "HumanAuthenticationProof" not in source

    def test_full_trust_conjunction_requires_all_layers_and_n2_scenario_fails_normatively(self):
        rihac = _text(RIHAC)
        riasc = _text(RIASC)
        for phrase in (
            "strict RIASC-001 schema validation",
            "canonical-storage lookup",
            "record-digest recomputation",
            "current freshness and consumption-state validation",
            "successful HPAC-001 authentication-proof verification",
        ):
            assert phrase in rihac
        assert "Failure of any check yields no validated-authority projection and no real\ndispatch" in riasc

    def test_b1_b7_n1_closure_enablers_remain_independent_requirements(self):
        rihac = _text(RIHAC)
        pbrd = _text(PBRD)
        assert "canonical-storage lookup rather than a caller-supplied arbitrary path" in rihac
        assert "immutable validated-authority evidence projection" in rihac
        assert "validation-evidence projection digest" in pbrd
        assert "PB SHALL NOT receive or trust raw approval prose" in pbrd
