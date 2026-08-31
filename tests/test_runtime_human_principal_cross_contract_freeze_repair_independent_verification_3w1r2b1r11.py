"""Fresh static verification for phase 149O.20L.7O.3W.1R.2B.1R.1.1.

This suite reads contract text only.  It deliberately does not import PCAE
production modules or reuse the repair phase's test module.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs" / "contracts"
PRIMARY = (ROOT / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1_INDEPENDENT_VERIFICATION_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT_FREEZE.md").read_text()
STOP = (ROOT / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT_FREEZE_BLOCKING_REPAIR.md").read_text()
RIHAC = (CONTRACTS / "RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md").read_text()
RIASC = (CONTRACTS / "RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md").read_text()
HPAC = (CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md").read_text()
PBRD = (CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md").read_text()
RDGO = (CONTRACTS / "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md").read_text()
RPAC_PATH = CONTRACTS / "RUNTIME_PROVIDER_ADAPTER_CONTRACT.md"
RPAC = RPAC_PATH.read_text()


FINDINGS = {
    "B-1": "Principal registry/bootstrap/configuration trust root is not same-user-agent resistant. Location and “non-agent-invocable” convention do not replace protected ownership/ACL/separate-principal enforcement.",
    "B-2": "UP-only overclaims a named authenticated human. UV is optional and no exclusive credential custody is frozen.",
    "B-3": "Blind touch can substitute for informed approval. No non-forgeable confirmation evidence or trusted subject display is bound.",
    "B-4": "Proof schema/store/reference contract is incomplete and internally inconsistent. Canonical resolution cannot be implemented uniquely.",
    "B-5": "Revocation does not invalidate an outstanding gate-5-validated, unconsumed approval. Current-principal assurance can go stale before dispatch.",
    "B-6": "PBRD/RDGO still normatively pin RIHAC/RIASC v1.0. The active contract graph is ambiguous and permits the insecure predecessor.",
    "B-7": "Proof nonce consumption at gate 5 contradicts mandatory pre-gate-9 approval revalidation. The frozen lifecycle is not implementable consistently.",
    "M-1": "RIHAC v1.1 should be a new MAJOR. The change is mandatory and semantically incompatible, not optional evidence or mere clarification.",
    "M-2": "Internal cross-references are stale/mistargeted. Examples: HPAC references nonexistent §39–§41 and mispoints fallback sections; RIHAC calls software fallback HPAC §15 although §15 is domain separation.",
}


def _norm(text: str) -> str:
    return " ".join(text.split())


def _schema() -> dict:
    match = re.search(r"```json\n(.*?)\n```", RIASC, re.S)
    assert match
    return json.loads(match.group(1))


def test_exact_primary_nine_finding_inventory() -> None:
    assert list(FINDINGS) == ["B-1", "B-2", "B-3", "B-4", "B-5", "B-6", "B-7", "M-1", "M-2"]
    for finding_id, wording in FINDINGS.items():
        assert f"{finding_id} — {wording}" in _norm(PRIMARY.replace("**", ""))
        assert wording in _norm(STOP.replace("**", ""))


def test_active_versions_and_supersession_are_exact() -> None:
    # `.1R.15.4` normalization bumped RDGO-001 -> v3.1, PBRD-001 -> v2.1,
    # HPAC-001 -> v2.1 (all MINOR). RIHAC-001 v2.0, RIASC-001 v3.0,
    # RPAC-001 v1.0 unchanged.
    # Phase ...1R.22 (N-16-3): PBRD-001 v2.1 -> v3.0 (MAJOR; §16 "weakening
    # POL-005 eligibility"). Every other version pin is unchanged.
    # Reconciled by .1R.22R (N-23-3).
    expected = [(RIHAC, "RIHAC-001", "2.0"), (RIASC, "RIASC-001", "3.0"), (HPAC, "HPAC-001", "2.1"), (PBRD, "PBRD-001", "3.0"), (RDGO, "RDGO-001", "3.1"), (RPAC, "RPAC-001", "1.0")]
    for text, contract, version in expected:
        assert f"**Contract:** {contract}" in text
        assert f"**Version:** {version}" in text
        assert "**Status:** FROZEN" in text
    assert "V1.x approvals remain historical evidence only" in _norm(RIHAC)
    assert "V1/v2 artifacts are historical only" in _norm(RIASC)
    assert "V1 proof, registry, enrollment, assurance, and presentation semantics are not authority-compatible" in _norm(HPAC)


def test_major_version_rationales_are_semantically_justified() -> None:
    assert "cannot remain authority-valid under v2" in _norm(RIHAC)
    assert "mandatory incompatible authority semantics" in _norm(RIHAC)
    assert "V3 is a MAJOR because" in RIASC
    assert "presence-gating relaxation" in HPAC and "requires a new MAJOR" in HPAC
    assert "an old valid request is no longer valid" in _norm(PBRD)
    assert "state-machine change, so a MAJOR is required" in RDGO


def test_riasc_v3_normative_json_is_closed_and_exact() -> None:
    schema = _schema()
    assert schema["$id"].endswith("/3.0/schema.json")
    assert schema["properties"]["schema_version"] == {"const": "3.0"}
    assert schema["properties"]["contract_version"] == {"const": "RIHAC-001/2.0"}
    assert schema["additionalProperties"] is False
    assert len(schema["required"]) == 16
    assert schema["properties"]["subject"]["required"] == ["invocation_id", "runtime_target_id", "prompt_hash", "repository_identity", "task_id"]
    assert schema["properties"]["provenance"]["required"] == ["principal_id", "authentication_mechanism_id", "credential_id", "authentication_proof_ref", "approval_mechanism", "approval_preview_digest", "producer_component"]
    assert schema["$defs"]["authentication_proof_ref"]["required"] == ["proof_id", "proof_digest"]


def test_trust_properties_are_normatively_separate() -> None:
    for wall in ["credential authentication       != user presence", "user presence                   != user verification", "user verification               != informed approval intent", "approval                      != PB permission", "PB permission                 != runtime capability", "runtime capability            != execution"]:
        assert wall in HPAC
    assert "Each property is verified\n  independently; none silently implies another" in HPAC


def test_up_uv_and_no_downgrade_are_unambiguous() -> None:
    assert "both UP\n  and UV are mandatory and form an immutable contract minimum" in HPAC
    assert "UP-only proofs may be recorded as\n  credential-presence evidence but SHALL NOT authorize real runtime" in HPAC
    assert "neither repository nor protected\n  administrator may lower this floor" in HPAC
    assert "Required mechanism unavailable means approval unavailable; there\n  is no downgrade" in HPAC
    assert "No software-key or UP-only alternative qualifies" in HPAC


def test_authenticated_principal_is_credential_bound_not_natural_identity() -> None:
    assert "distinct from OS, Git, agent/session,\n  producer, biological, civil, or legal identity" in HPAC
    assert "means only that an active credential enrolled to that ID met\n  the required proof profile" in HPAC


def test_same_user_agent_and_ordinary_identity_shortcuts_are_rejected() -> None:
    normalized = _norm(RIHAC)
    assert "coding agent executes under the same OS account as the human operator" in normalized
    for shortcut in ["OS username", "filesystem ownership", "environment variable", "local process UID", "ordinary CLI stdin", "Git identity"]:
        assert shortcut in normalized
    assert "ordinary agent-controlled process cannot forge" in normalized


def test_registry_bootstrap_and_repository_isolation_close_b1() -> None:
    assert "protected root outside every repository" in HPAC
    assert "protected administration\n  principal unavailable to ordinary same-user agent execution" in HPAC
    assert "reject symlinks, traversal, owner/ACL mismatch, replace/delete access" in HPAC
    assert "externally\n  established deployment-owner administration principal" in HPAC
    assert "same-UID agent invocation SHALL be denied" in HPAC
    assert "Repository/task/agent-controlled state SHALL NOT select" in HPAC


def test_trusted_presentation_intent_and_blind_touch_language_exists() -> None:
    normalized = _norm(RIHAC)
    assert "ordinary agent-controlled terminal output/stdin" in normalized.lower()
    assert "PCAE does not claim to prove human comprehension" in normalized
    assert "raw hashes alone are insufficient" in normalized
    assert "A blind touch or blind authenticator touch" in normalized
    for fact in ["repository", "task", "target", "operation/effect", "prompt/instruction", "invocation", "expiry", "one-shot"]:
        assert fact in HPAC[HPAC.index("**TrustedApprovalPresentation.**"):HPAC.index("**Assurance level.**")]


def test_presentation_challenge_semantic_binding_is_required() -> None:
    assert "The subject digest covers repository identity, task ID, runtime target,\n  operation/effect and scope, prompt/instruction identity, invocation ID,\n  expiry, and one-shot status" in HPAC
    assert "Any display, subject, domain,\n  principal, credential, or version mismatch invalidates the proof" in HPAC
    assert "WHAT HUMAN WAS SHOWN == WHAT HUMAN AUTHENTICATED == WHAT PCAE AUTHORIZES" in HPAC


def test_b3_remains_open_because_presentation_evidence_is_not_canonically_defined() -> None:
    # The contract names a reference and a protected store, but freezes no
    # presentation schema identity, closed fields, canonical bytes, or path.
    assert "trusted_presentation_ref" in HPAC
    assert "protected presentation store" in HPAC
    assert "HPAC-PRESENTATION/" not in HPAC
    assert "presentation_schema_version" not in HPAC
    assert "<HPAC_PROTECTED_ROOT>/presentations/" not in HPAC
    assert "presentation.json" not in HPAC


def test_challenge_domain_subject_and_nonce_are_exact() -> None:
    assert "pcae.hpac.runtime-invocation-approval.v2" in HPAC
    challenge = HPAC[HPAC.index("HPAC-REQ-049"):HPAC.index("HPAC-REQ-051")]
    for field in ["domain_separator", "challenge_version", "proof_schema_version", "principal_id", "credential_id", "approval_subject_digest", "trusted_presentation_digest", "nonce", "issued_at", "expires_at"]:
        assert f"`{field}`" in challenge
    assert "generated by the trusted challenge-construction component (never the\n  authenticator, adapter, or caller)" in HPAC


def test_hatp_registry_principal_credential_and_domain_separation() -> None:
    assert "physically and logically separate from HATP's `registry.json`" in HPAC
    assert "principal_id` space is\n  independent of HATP's `principal_id` space" in HPAC
    assert "own distinct `credential_id`/`signer_key_id`" in HPAC
    assert "HATP\n  signing-ceremony assertion, or vice versa" in HPAC


def test_hpac_proof_schema_store_and_reference_are_exact() -> None:
    proof = HPAC[HPAC.index("HPAC-REQ-052"):HPAC.index("## 18.")]
    for field in ["proof_schema_version", "proof_id", "proof_digest", "mechanism_id", "principal_id", "credential_id", "challenge_digest", "approval_subject_digest", "trusted_presentation_ref", "assertion", "up", "uv", "authenticated_at", "verifier_version"]:
        assert f"`{field}`" in proof
    assert "<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/proof.json" in proof
    assert "(proof_id, proof_digest)" in proof


def test_b4_remains_open_because_bound_lifecycle_record_is_not_implementably_closed() -> None:
    # Gate 5 must distinguish same-approval idempotent revalidation from
    # cross-binding, but the adjacent lifecycle record has no schema/path or
    # approval-binding fields with which to make that decision.
    assert "PROOF_VERIFIED_AND_BOUND` to this exact same approval and bytes" in HPAC
    assert "lifecycle_schema_version" not in HPAC
    assert "bound_approval_id" not in HPAC
    assert "bound_approval_digest" not in HPAC
    assert "lifecycle.json" not in HPAC


def test_revocation_replay_and_fresh_per_approval_semantics_close_b5() -> None:
    assert "immediately marks all\n  its unused challenges, verified/bound proofs, unmaterialized approvals,\n  unconsumed approvals, and derived PB authority projections invalid" in HPAC
    assert "including one previously validated at gate 5" in RIHAC
    assert "Each real invocation\n  requires its own fresh challenge and its own fresh proof" in HPAC
    assert "No session-caching layer for authentication exists" in HPAC


def test_gate5_gate9_lifecycle_wording_closes_original_b7_contradiction() -> None:
    assert "Gate-5 verification binds but does not\n  consume" in HPAC
    assert "Gate 9 atomically writes the durable `dispatch_attempted` marker,\n  consumes the canonical approval, and transitions the bound HPAC proof" in HPAC
    assert "It binds fresh proof state to this approval but does not consume the approval,\nnonce, or proof" in RDGO


def test_authenticated_principal_object_shape_has_no_authority() -> None:
    assert "never by direct construction from caller-\n  supplied strings or dicts" in HPAC
    assert "ephemeral and non-serializable" in HPAC
    assert "Deserializing stored proof material SHALL NOT by itself yield\n  trusted" in HPAC


def test_rihac_validation_conjunction_and_canonical_approval_provenance() -> None:
    for requirement in ["strict RIASC-001 schema validation", "canonical-storage lookup", "current freshness and consumption-state validation", "successful HPAC-001 v2.1 proof verification", "trusted-construction-only validated-authority projection"]:
        assert requirement in RIHAC
    assert "validator resolves it by `approval_id`; callers SHALL NOT supply an arbitrary\npath" in RIHAC
    assert "never a caller-copyable\n    seal, boolean, or public digest" in RIHAC


def test_pbrd_v2_uses_typed_evidence_and_pb_does_not_authenticate() -> None:
    start = PBRD.index("| 14 | `human_authority_binding`")
    binding = PBRD[start:PBRD.index("\n\n", start)]
    for field in ["approval_id", "approval_digest", "authority_projection_id", "authority_projection_digest", "authority_contract_version", "proof_validation_digest", "request_binding_digest"]:
        assert f"`{field}`" in binding
    assert "PB SHALL NOT authenticate humans, parse FIDO2 assertions, read HPAC registries" in PBRD
    assert "caller assertion,\n`approval_present`, a public digest, or a copyable object seal" in PBRD
    assert "Only successful RIHAC-001 v2.0 validation may cause the trusted request builder" in PBRD


def test_human_review_and_pol005_are_unchanged_fail_closed() -> None:
    assert "Other applicable policies remain free to produce `DENY` or\n  `HUMAN_REVIEW`" in PBRD
    assert "POL-005 (`ExecutionDisabledRule`) is unchanged" in PBRD
    assert "denies every truthful non-simulation request" in PBRD
    assert "DENY > HUMAN_REVIEW > ALLOW" in PBRD


def test_rdgo_has_exact_eleven_gates_and_gate10_first_effect() -> None:
    rows = re.findall(r"^\| (\d+) \| ([^|]+?) \|", RDGO, re.M)
    gates = [(int(number), name.strip()) for number, name in rows[:11]]
    assert [number for number, _ in gates] == list(range(1, 12))
    assert gates[2][1] == "Human authority creation"
    assert gates[4][1] == "Approval validation"
    assert gates[5][1] == "Permission Broker"
    assert gates[8][1] == "Durable pre-dispatch record"
    assert gates[9][1] == "Adapter dispatch"
    assert "Gate 10 is the real-effect boundary" in RDGO


def test_dispatch_identity_is_independent_of_human_authority() -> None:
    assert "attempt_id` and `idempotency_key` are minted at RDGO-001 gate 2" in PBRD
    assert "Neither may be selected,\noverwritten, echoed back, or influenced by the adapter, runtime, provider,\ncaller payload, or approval producer" in PBRD
    assert "Duplicate/replayed `attempt_id`" in RDGO


def test_rpac_is_byte_identical_and_semantically_compatible() -> None:
    assert hashlib.sha256(RPAC_PATH.read_bytes()).hexdigest() == "395f6b9d3f1779fb312f66e06819176417db6380193d1f5fee52668d43260c89"
    assert "PCAE SHALL remain the authority-owning control plane" in RPAC
    assert "obtain human InvocationApproval" in RPAC
    assert "Runtime Enforcement SHALL be the final whether-to-invoke gate" in RPAC
    assert "HATP artifacts SHALL NOT be reinterpreted as generic invocation\npermission" in RPAC


def test_cross_contract_version_pins_are_current_except_historical_text() -> None:
    # `.1R.15.4` normalization: RDGO-001 v3.1, PBRD-001 v2.1, HPAC-001 v2.1.
    assert "RIHAC-001 v2.0, RIASC-001 v3.0,\nHPAC-001 v2.1, RDGO-001 v3.1" in PBRD
    assert "RIHAC-001 v2.0, RIASC-001 v3.0,\nHPAC-001 v2.1, PBRD-001 v2.1" in RDGO
    assert "Schema companion:** RIASC-001 v3.0" in RIHAC
    assert "Semantic authority:** RIHAC-001 v2.0" in RIASC


def test_n2_caller_fields_without_canonical_proof_have_no_authority() -> None:
    assert "caller IDs,\n  references, booleans, or plausible proof-shaped bytes cannot satisfy" in HPAC
    assert "A bare caller-supplied identifier string, of any\nshape" in RIHAC
    assert "Schema conformance, digest agreement, storage presence, and identifier shape\ndo not independently create human authority" in RIASC
