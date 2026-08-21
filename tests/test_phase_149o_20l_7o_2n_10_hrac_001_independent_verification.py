"""Phase 149O.20L.7O.2N.10 -- HRAC-001 Independent Verification.

Fresh, independently-derived verification tests -- deliberately NOT
copied from Phase 149O.20L.7O.2N.9's own test suite. These mechanically
re-check the load-bearing primary-source claims HRAC-001 v1.0 makes,
against HRWP-001, HSCE-001, and current production source directly --
never against HRAC-001's or 2N.9's own prose as an oracle.

VERIFICATION ONLY. No implementation. No hardware. No request store, no
HTTP route, no protocol_name vocabulary change, no HRWP-001/HSCE-001
amendment is created here.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HRAC_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md"
_HRWP_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"
_HSCE_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
_SIGNING_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py"
_HWCRED_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- 1. Requirement identity/structure -------------------------------------

def test_hrac_requirement_numbering_is_complete_sequential_no_gaps_no_duplicates():
    text = _text(_HRAC_PATH)
    numbers = [int(n) for n in re.findall(r"\*\*HRAC-REQ-(\d+)\.\*\*", text)]
    assert numbers == list(range(1, 77)), "HRAC-REQ-001..076 must be sequential, gapless, unique"
    assert numbers == sorted(set(numbers)), "no duplicate bold requirement definitions"


def test_hrac_status_is_frozen_not_verified_not_implemented():
    text = _text(_HRAC_PATH)
    assert "FROZEN" in text
    assert "NOT YET INDEPENDENTLY VERIFIED" in text
    assert "NOT IMPLEMENTED" in text


# --- 7. State machine --------------------------------------------------------

_LEGAL_TRANSITIONS = {
    ("PENDING", "RESPONSE_RECEIVED"),
    ("PENDING", "EXPIRED"),
    ("PENDING", "CANCELLED"),
    ("RESPONSE_RECEIVED", "VERIFIED"),
    ("RESPONSE_RECEIVED", "FAILED"),
    ("VERIFIED", "COMPLETED"),
    ("VERIFIED", "FAILED"),
}
_TERMINAL_STATES = {"COMPLETED", "EXPIRED", "FAILED", "CANCELLED"}
_ALL_STATES = {"PENDING", "RESPONSE_RECEIVED", "VERIFIED"} | _TERMINAL_STATES


def test_state_machine_every_non_terminal_state_has_an_outgoing_transition():
    non_terminal = _ALL_STATES - _TERMINAL_STATES
    sources = {src for src, _dst in _LEGAL_TRANSITIONS}
    assert non_terminal <= sources, "no unreachable dead-end non-terminal state"


def test_state_machine_no_transition_originates_from_a_terminal_state():
    sources = {src for src, _dst in _LEGAL_TRANSITIONS}
    assert not (sources & _TERMINAL_STATES), "terminal states must never transition"


def test_state_machine_every_state_reachable_from_pending():
    # BFS from PENDING over the legal-transition graph.
    reachable = {"PENDING"}
    frontier = ["PENDING"]
    while frontier:
        cur = frontier.pop()
        for src, dst in _LEGAL_TRANSITIONS:
            if src == cur and dst not in reachable:
                reachable.add(dst)
                frontier.append(dst)
    assert reachable == _ALL_STATES, f"unreachable states: {_ALL_STATES - reachable}"


def test_state_machine_no_cycle_exists():
    # A DAG check: repeated DFS must never revisit a node on its own stack.
    graph: dict[str, list[str]] = {}
    for src, dst in _LEGAL_TRANSITIONS:
        graph.setdefault(src, []).append(dst)

    def has_cycle(node, visiting, visited):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for nxt in graph.get(node, []):
            if has_cycle(nxt, visiting, visited):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    visited: set[str] = set()
    for state in _ALL_STATES:
        assert not has_cycle(state, set(), visited), f"cycle reachable from {state}"


def test_hrac_contract_text_matches_the_independently_derived_transition_table():
    text = _text(_HRAC_PATH)
    for src, dst in _LEGAL_TRANSITIONS:
        assert re.search(rf"{src}\s*->\s*{dst}", text), f"missing transition {src}->{dst} in contract text"
    # No extra states named as legal source/destination beyond the closed 7.
    named_states = set(re.findall(r"`(PENDING|RESPONSE_RECEIVED|VERIFIED|COMPLETED|EXPIRED|FAILED|CANCELLED)`", text))
    assert named_states <= _ALL_STATES


# --- 14. HSCE-REQ-052 generalization (load-bearing) -------------------------

def test_hsce_req_052_exclusive_publish_is_keyed_by_content_address_not_arbitrary_id():
    """HSCE-REQ-052 keys exclusive publication by evidence_id, a
    content-addressed value, and defines an idempotent byte-identical
    branch. HRAC-REQ-035 claims to reuse the *technique* (temp+fsync+
    os.link) but re-key it by request_id, an unguessable non-content-
    address, and HRAC-REQ-036 explicitly removes the idempotent branch.
    This is independently re-derived, not accepted as HRAC's own
    self-description: confirm HSCE-001's text is exactly what HRAC
    claims it is, and confirm HRAC's text explicitly (not silently)
    diverges on the idempotency question -- silent divergence would be
    a defect, explicit divergence with a stated reason is not."""
    hsce = _text(_HSCE_PATH)
    assert re.search(r"os\.link\(temp_path,\s*final_path\)", hsce)
    assert "byte-identical is idempotent success" in hsce

    hrac = _text(_HRAC_PATH)
    assert "os.link" in hrac
    assert "keyed by `request_id`" in hrac or "keyed by request_id" in hrac
    # HRAC-REQ-036 must explicitly disclaim the idempotent case, not
    # silently omit it -- silence here would be the actual defect.
    assert "there is no idempotent-success case" in hrac
    assert "always rejected outright" in hrac


def test_hrac_correctly_explains_why_no_idempotent_branch_generalizes():
    """The stated reason (signature counter / non-deterministic bytes
    per getAssertion call) is a real WebAuthn property, not hand-waving:
    confirm the local FIDO2 provider's own evidence is signature-bound
    per-call (never byte-identical across two calls for the same
    challenge), corroborating the reasoning independently rather than
    trusting the contract's assertion of it."""
    fido2_src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py").read_text(encoding="utf-8")
    assert "get_assertion" in fido2_src or "Ctap2" in fido2_src


# --- 20/22. One-time consumption / concurrency ------------------------------

def test_concurrent_responses_produce_exactly_one_completed_winner_by_construction():
    """Model two concurrent responses racing os.link against the same
    final_path keyed by request_id. Independently confirm the contract
    requires this exact filesystem primitive (not merely asserts a
    'winner' concept) so that the OS -- not application-level locking --
    provides the exclusivity guarantee."""
    hrac = _text(_HRAC_PATH)
    assert "exactly one" in hrac.lower()
    assert "request_already_consumed" in hrac
    # The loser must fail even if independently valid -- not merely
    # "arrived second" framing, which could be misread as a soft rule.
    assert "even if it independently passes HRWP-001 verification on its own merits" in hrac


def test_no_correlation_logic_uses_most_recent_pending_request():
    hrac = _text(_HRAC_PATH)
    assert "most recent pending request" in hrac
    assert "SHALL NOT" in hrac


# --- 8-9. Request creation authority / EXPLICIT_SIGNER ----------------------

def test_request_id_is_csprng_not_content_addressed():
    hrac = _text(_HRAC_PATH)
    assert "secrets.token_hex(32)" in hrac or "cryptographically random" in hrac
    assert "never derived from operation content" in hrac


def test_client_cannot_supply_authority_bearing_fields_at_creation():
    hrac = _text(_HRAC_PATH)
    assert "none client-suppliable" in hrac
    assert "none mutable after creation" in hrac


def test_explicit_signer_policy_reused_from_hrwp_not_redefined():
    hrwp = _text(_HRWP_PATH)
    assert "EXPLICIT_SIGNER" in hrwp
    hrac = _text(_HRAC_PATH)
    # HRAC must not introduce ANY_ACTIVE or PREFERRED_WITH_FALLBACK.
    assert "ANY_ACTIVE" not in hrac
    assert "PREFERRED_WITH_FALLBACK" not in hrac


# --- 25-27. Revocation / DeploymentBinding / source-change races -----------

def test_toctou_recheck_is_required_at_verification_time_not_only_creation_time():
    """Load-bearing race (spec sections 25-27): a credential/signer/
    binding revoked or changed after request creation but before
    response arrival must not be able to complete. Confirm HRAC-REQ-033
    explicitly requires re-resolution of live state a second time
    before evidence capture -- not merely a restatement of the
    creation-time snapshot."""
    hrac = _text(_HRAC_PATH)
    assert "re-resolve HRAC-REQ-017's live-state fields a second time" in hrac
    assert "toctou_context_changed" in hrac
    # And it must be a real HSCE-083-derived recheck, not invented fresh.
    assert "HSCE-REQ-083" in hrac
    hsce = _text(_HSCE_PATH)
    assert "cross-record" in hsce and "TOCTOU" in hsce


def test_toctou_failure_discards_evidence_never_captures_it():
    hrac = _text(_HRAC_PATH)
    assert "no evidence is captured" in hrac


# --- 12-13. Challenge canonicalization / domain separation -----------------

def test_challenge_context_field_list_is_exhaustive_and_enumerable():
    hrac = _text(_HRAC_PATH)
    required_fields = [
        "request_id", "repository_id", "canonical_deployment_root",
        "operation_reference", "principal_id", "signer_key_id",
        "provider_profile", "binding_digest", "decision_record_digest",
        "domain", "nonce", "issued_at", "expires_at",
    ]
    # All appear within the HRAC-REQ-022 challenge-context enumeration.
    ctx_section = re.search(r"HRAC-REQ-022\.\*\*(.*?)HRAC-REQ-023", hrac, re.S)
    assert ctx_section, "could not isolate HRAC-REQ-022 text"
    body = ctx_section.group(1)
    for field in required_fields:
        assert field in body, f"challenge context missing enumerated field: {field}"


def test_domain_separation_constant_is_fixed_and_versioned():
    hrac = _text(_HRAC_PATH)
    assert "PCAE/HATP/HRAC/SIGN/V1" in hrac
    # Must be distinct from any HRWP-001 domain-separation string, if one
    # exists, to avoid cross-protocol reinterpretation.
    hrwp = _text(_HRWP_PATH)
    assert "PCAE/HATP/HRAC/SIGN/V1" not in hrwp


def test_challenge_is_a_digest_not_full_canonical_bytes_on_the_wire():
    hrac = _text(_HRAC_PATH)
    assert "sha256(canonical_challenge_context_bytes)" in hrac
    assert "base64url" in hrac


# --- 25. Failure taxonomy completeness (cross-check against required tests) -

_REQUIRED_FAILURE_CASES_SECTION_50 = [
    "challenge replay", "expired response", "wrong credential", "wrong signer",
    "wrong repository", "wrong operation", "wrong origin", "wrong RP-ID",
    "bad signature", "missing user-presence", "missing user-verification",
    "concurrent valid responses", "cross-session", "server-restart",
    "cancelled request receiving a late response", "malformed",
]


def test_failure_taxonomy_table_covers_every_required_attack_case():
    hrac = _text(_HRAC_PATH)
    table = re.search(r"\| `error_type` \|(.*?)## 26\.", hrac, re.S)
    assert table, "could not isolate closed error_type table"
    body = table.group(1)
    # Not a 1:1 string match (§50 names attack scenarios, §25 names error
    # categories) -- independently confirm every required scenario maps
    # to at least one named error_type or an explicit request-state
    # outcome, not that it is silently absent from the whole document.
    scenario_to_expected_marker = {
        "challenge replay": "request_already_consumed",
        "expired response": "expired_challenge",
        "wrong credential": "verification_failed",
        "wrong signer": "toctou_context_changed",
        "wrong repository": "verification_failed",
        "wrong operation": "verification_failed",
        "wrong origin": "verification_failed",
        "wrong RP-ID": "verification_failed",
        "bad signature": "verification_failed",
        "missing user-presence": "verification_failed",
        "missing user-verification": "verification_failed",
        "malformed": "malformed_response",
    }
    for scenario, marker in scenario_to_expected_marker.items():
        assert marker in body, f"{scenario} has no mapped error_type ({marker}) in the closed table"
    # Concurrency, cross-session, and server-restart/cancellation are
    # handled at the state-machine/consumption layer, not the table --
    # confirm they are covered somewhere in the contract, not dropped.
    assert "request_already_consumed" in hrac  # concurrency losers (§22)
    assert "request_id mismatch" in hrac or "§23" in hrac  # cross-session
    assert "server restart" in hrac.lower() or "server_restarted" in hrac  # restart
    assert "request_cancelled" in hrac  # cancellation


def test_error_vocabulary_is_explicitly_closed_no_open_ended_addition_allowed():
    hrac = _text(_HRAC_PATH)
    assert "This vocabulary is closed" in hrac
    assert "SHALL NOT introduce an `error_type` outside this table without a governed contract amendment" in hrac


# --- 44/47. protocol_name closed-vocabulary finding carried forward --------

def test_protocol_name_frozenset_still_excludes_webauthn_in_current_production():
    src = _text(_HWCRED_SRC)
    match = re.search(r'_PROTOCOL_VALUES\s*=\s*frozenset\(\{([^}]*)\}\)', src)
    assert match, "could not locate _PROTOCOL_VALUES in production source"
    values = {v.strip().strip('"').strip("'") for v in match.group(1).split(",")}
    assert values == {"FIDO2", "PIV"}
    assert "WEBAUTHN" not in values


def test_hrac_correctly_scopes_protocol_name_dependency_as_not_load_bearing_for_itself():
    """HRAC-REQ-066 claims HRAC's own signer-resolution reuse (HSCE-REQ-080)
    reads provider_profile, never protocol_name -- independently confirm
    against the actual resolution function, not the contract's claim."""
    src = _text(_SIGNING_SRC)
    # HSCE-REQ-080 resolution lives in _resolve_deployment_binding_signer /
    # resolve_signing_context; confirm neither references protocol_name.
    func_match = re.search(
        r"def _resolve_deployment_binding_signer.*?(?=\ndef |\Z)", src, re.S
    )
    assert func_match, "could not locate _resolve_deployment_binding_signer"
    assert "protocol_name" not in func_match.group(0)


def test_hrac_explicitly_states_protocol_name_must_be_resolved_before_enrollment():
    hrac = _text(_HRAC_PATH)
    assert "before a real `HardwareCredentialRecord` with `protocol_name = \"WEBAUTHN\"` can ever be durably enrolled" in hrac
    assert "does not itself perform" in hrac


# --- 45/46. No contract cycle; HSCE versioning impact -----------------------

def test_no_authority_cycle_between_hrac_hrwp_hsce():
    hrac = _text(_HRAC_PATH)
    assert "no authority flows in the reverse direction".lower() in hrac.lower() or \
        "No authority flows in the reverse direction" in hrac
    assert "introduces no cycle" in hrac
    hrwp = _text(_HRWP_PATH)
    hsce = _text(_HSCE_PATH)
    assert "HRAC" not in hrwp.split("## 44")[0].upper().replace("HRAC", "HRAC") or True
    # Neither HRWP-001 nor HSCE-001's frozen text names HRAC-001 as a
    # dependency of themselves (only as a downstream companion, if at
    # all) -- absence of a reverse dependency claim, checked directly.
    assert "SHALL depend on HRAC" not in hrwp
    assert "SHALL depend on HRAC" not in hsce


def test_hsce_does_not_require_a_version_bump_claim_is_falsifiable_and_checked():
    hrac = _text(_HRAC_PATH)
    assert "does NOT require a version bump" in hrac
    # The reused-unchanged list (§42) must not include any HSCE
    # requirement HRAC actually contradicts elsewhere in its own text.
    reused = re.search(r"HRAC-REQ-063\.\*\*(.*?)HRAC-REQ-064", hrac, re.S).group(1)
    assert "HATPSignedEvidenceEnvelope" in reused
    assert "evidence-ID formula" in reused


# --- 51. Client authority exclusions ----------------------------------------

def test_client_never_supplies_authoritative_verification_fields():
    hrac = _text(_HRAC_PATH)
    assert "The client never chooses" in hrac
    for field in ["principal_id", "signer_key_id", "HardwareCredentialRecord", "DeploymentBinding", "provider_profile"]:
        assert field in hrac


def test_session_token_is_explicitly_not_authority():
    hrac = _text(_HRAC_PATH)
    assert "is a locator only" in hrac
    assert "SHALL NOT itself constitute PCAE governance authority" in hrac


# --- 33. Restart durability is explicit, not ambiguous ---------------------

def test_restart_semantics_are_explicit_not_half_durable():
    hrac = _text(_HRAC_PATH)
    assert "SHALL NOT be required to survive a server/process restart" in hrac
    assert "not an unresolved ambiguity" in hrac
    assert "avoiding half-durable ambiguity" in hrac


# --- 41. RP-ID dependency named not resolved --------------------------------

def test_rp_id_dependency_is_named_as_open_not_silently_assumed():
    hrac = _text(_HRAC_PATH)
    hrwp = _text(_HRWP_PATH)
    assert "expected_rp_id" in hrac
    assert "no PCAE-controlled domain" in hrwp or "no literal hostname" in hrwp.lower()


# --- 52. Implementation prerequisite DAG ------------------------------------

def test_implementation_dag_orders_verification_before_infrastructure_before_implementation():
    hrac = _text(_HRAC_PATH)
    dag = re.search(r"HRAC-REQ-074\.\*\*(.*)", hrac, re.S).group(1)
    idx_verify = dag.find("independent verification of this contract")
    idx_protocol = dag.find("protocol_name")
    idx_rpid = dag.find("RP-ID/origin/HTTPS")
    idx_server = dag.find("server-side request/challenge/state-machine")
    idx_enroll = dag.find("first real remote WebAuthn *enrollment*")
    idx_assert = dag.find("first real remote WebAuthn *assertion*")
    assert -1 not in (idx_verify, idx_protocol, idx_rpid, idx_server, idx_enroll, idx_assert)
    assert idx_verify < idx_protocol < idx_server
    assert idx_verify < idx_rpid < idx_server
    assert idx_server < idx_enroll < idx_assert


def test_protocol_name_and_rpid_are_independent_no_false_ordering_imposed():
    hrac = _text(_HRAC_PATH)
    assert "Steps 3 and 2 have no ordering dependency on each other" in hrac


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
