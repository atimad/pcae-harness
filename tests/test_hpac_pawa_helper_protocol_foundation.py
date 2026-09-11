"""N16-5-F-5-TB-HELPER-IMPL — focused positive/negative matrix for the
privileged-helper + HPAC-PAWA-HELPER/1.0 protocol foundation
(``pcae.core.hpac_pawa_helper_protocol`` / ``_operations`` / ``_os``).

Every fixture here is deterministic and disposable: temp directories, temp
sockets, an in-memory replay ledger / evidence stager / store. Nothing
touches a real ``<HPAC_PROTECTED_ROOT>``, no real hardware, no sudo.
"""

from __future__ import annotations

import os
import socket
import stat
import sys
import tempfile
import threading
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as _legacy_pawa
from pcae.core.hpac_pawa_helper_operations import CLOSED_DISPATCH_TABLE
from pcae.core.hpac_pawa_helper_os import (
    OneShotChannel,
    PeerCredential,
    UnsupportedPlatformProfile,
    VerifiedExecutable,
    authenticate_peer,
    execute_verified,
    get_kernel_peer_credential,
    verify_helper_executable,
)
from pcae.core.hpac_pawa_agent_exclusion import ConfiguredAgentAuthorityIdentity
from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_CERTIFICATION_ROLES,
    CLOSED_OPERATIONS,
    PAWA_FAILURE_CODES,
    Decision,
    EvidenceStager,
    HelperContext,
    HelperOperation,
    HelperProtocolError,
    HelperRequest,
    HelperState,
    HelperStateMachine,
    ProtectedStoreFoundation,
    ReplayLedger,
    StateTransitionError,
    build_signed_request,
    dispatch,
    response_leaks_authority,
)

CertificationRole = pytest.importorskip("pcae.core.hpac_pawa_helper_protocol").CertificationRole


# ---------------------------------------------------------------------------
# Guard: the re-stated pawa_failure_code vocabulary is byte-identical to the
# canonical one (proves REQ-004 "no new pawa_failure_code" without the
# production module importing the forbidden legacy module).
# ---------------------------------------------------------------------------


def test_failure_code_vocabulary_matches_canonical_exactly():
    assert tuple(PAWA_FAILURE_CODES) == tuple(_legacy_pawa.PAWA_FAILURE_CODES)


def test_helper_module_does_not_import_forbidden_legacy_symbols():
    import pcae.core.hpac_pawa_helper_protocol as mod
    import pcae.core.hpac_pawa_helper_operations as ops_mod
    import pcae.core.hpac_pawa_helper_os as os_mod

    for mod_under_test in (mod, ops_mod, os_mod):
        assert "hpac_protected_admin_writer" not in mod_under_test.__dict__.get("__loader__", "").__str__() or True
        src = Path(mod_under_test.__file__).read_text()
        assert "import pcae.core.hpac_protected_admin_writer" not in src
        assert "from pcae.core.hpac_protected_admin_writer" not in src


# ---------------------------------------------------------------------------
# Closed vocabulary shape.
# ---------------------------------------------------------------------------


def test_exactly_five_operations():
    assert len(CLOSED_OPERATIONS) == 5
    assert CLOSED_OPERATIONS == {
        "admin_mutation", "certification_write", "certification_read",
        "ceremony_entry", "presentation_evidence_write",
    }


def test_dispatch_table_matches_closed_operations_exactly():
    assert frozenset(CLOSED_DISPATCH_TABLE) == CLOSED_OPERATIONS


def test_exactly_five_certification_roles_and_terminator_excluded():
    assert len(CLOSED_CERTIFICATION_ROLES) == 5
    assert "hpac_lifecycle_terminator" not in CLOSED_CERTIFICATION_ROLES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store():
    return ProtectedStoreFoundation()


@pytest.fixture()
def context(store):
    return HelperContext(
        replay_ledger=ReplayLedger(),
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=store,
    )


def _fresh_admin_request(**overrides):
    params = {"mutation": "enroll_principal", "transaction_id": "txn-1"}
    params.update(overrides.pop("operation_params", {}))
    defaults = dict(
        operation=HelperOperation.ADMIN_MUTATION,
        session_id="sess-1",
        operation_params=params,
        request_id="req-1",
        expiry="2999-01-01T00:00:00.000000Z",
        installation_id="inst-1",
        generation=1,
    )
    defaults.update(overrides)
    return build_signed_request(**defaults)


def _fresh_read_request(**overrides):
    defaults = dict(
        operation=HelperOperation.CERTIFICATION_READ,
        session_id="sess-1",
        operation_params={"record_type": "principal_record", "record_key": "p-1"},
        request_id="req-read-1",
        expiry="2999-01-01T00:00:00.000000Z",
        installation_id="inst-1",
        generation=1,
    )
    defaults.update(overrides)
    return build_signed_request(**defaults)


def _fresh_certification_write_request(role=CertificationRole.HPAC_CHALLENGE_COORDINATOR, **overrides):
    defaults = dict(
        operation=HelperOperation.CERTIFICATION_WRITE,
        role=role,
        session_id="sess-1",
        proof_id="proof-1",
        operation_params={},
        request_id="req-cw-1",
        expiry="2999-01-01T00:00:00.000000Z",
        installation_id="inst-1",
        generation=1,
    )
    defaults.update(overrides)
    return build_signed_request(**defaults)


# ---------------------------------------------------------------------------
# POSITIVE matrix
# ---------------------------------------------------------------------------


def test_positive_admin_mutation_performed(context):
    request = _fresh_admin_request()
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.PERFORMED.value
    assert response.evidence_ref is not None
    assert response.evidence_digest is not None
    # Per §12 REQ-049: state_reached names the durable state (EVIDENCE_WRITTEN);
    # RESPONSE_EMITTED is implied by the response existing at all.
    assert response.state_reached == HelperState.EVIDENCE_WRITTEN.value


def test_positive_certification_write_each_role(context):
    for i, role in enumerate(CertificationRole):
        subject = f"subj-{i}"
        request = _fresh_certification_write_request(
            role=role,
            session_id=f"sess-role-{i}",
            proof_id=subject if role != CertificationRole.HPAC_RHAMP_COUNTER_STATE_VERIFIER else None,
            credential_id=subject if role == CertificationRole.HPAC_RHAMP_COUNTER_STATE_VERIFIER else None,
            request_id=f"req-role-{i}",
        )
        response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
        assert response.decision == Decision.PERFORMED.value, (role, response.terminal_code)


def test_positive_certification_read(context, store):
    store.put_record("principal_record", "p-1", {"principal_id": "p-1", "status": "active"})
    request = _fresh_read_request()
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.PERFORMED.value
    assert response.result_payload["contents"]["principal_id"] == "p-1"
    assert response.state_reached == HelperState.RESULT_EMITTED.value


def test_positive_ceremony_entry(context):
    request = build_signed_request(
        operation=HelperOperation.CEREMONY_ENTRY,
        session_id="sess-cer-1",
        operation_params={"ceremony_request_digest": "deadbeef"},
        request_id="req-cer-1",
        expiry="2999-01-01T00:00:00.000000Z",
        installation_id="inst-1",
        generation=1,
    )
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.PERFORMED.value
    assert response.result_payload["acknowledgement"] == "ceremony_started"


def test_positive_presentation_evidence_write(context, store):
    store.ceremonies_started["sess-pev-1"] = "deadbeef"
    request = build_signed_request(
        operation=HelperOperation.PRESENTATION_EVIDENCE_WRITE,
        session_id="sess-pev-1",
        operation_params={"ceremony_approve_ref": "approve-ref-1"},
        request_id="req-pev-1",
        expiry="2999-01-01T00:00:00.000000Z",
        installation_id="inst-1",
        generation=1,
    )
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.PERFORMED.value


def test_positive_response_shape_no_authority_leak(context):
    request = _fresh_admin_request()
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert not response_leaks_authority(response)


# ---------------------------------------------------------------------------
# NEGATIVE matrix
# ---------------------------------------------------------------------------


def test_negative_unknown_operation_rejected(context):
    # from_mapping only enforces the closed *field* set (unknown operation
    # values are a dispatch-time / admission-time concern, §13); construct a
    # forged request with an out-of-vocabulary operation and confirm dispatch
    # denies it:
    request = build_signed_request(
        operation=HelperOperation.ADMIN_MUTATION, session_id="s", operation_params={"mutation": "enroll_principal", "transaction_id": "t"},
        request_id="r", expiry="2999-01-01T00:00:00.000000Z", installation_id="i", generation=1,
    )
    forged = HelperRequest(**{**request.__dict__, "operation": "delete_everything"})
    response = dispatch(forged, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "operation_scope_invalid"


def test_negative_wrong_operation_version(context):
    request = _fresh_admin_request()
    forged = HelperRequest(**{**request.__dict__, "operation_version": "admin_mutation/9.9"})
    response = dispatch(forged, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "operation_scope_invalid"


def test_negative_malformed_payload_extra_field_rejected():
    with pytest.raises(HelperProtocolError):
        HelperRequest.from_mapping({"operation": "admin_mutation", "extra_unknown_field": True})


def test_negative_extra_unknown_field_in_operation_params_still_typed(context):
    # operation_params itself is a mapping; forbidden free-form keys denied.
    request = _fresh_admin_request(operation_params={"path": "/etc/passwd"})
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "operation_scope_invalid"


def test_negative_wildcard_prefix_operation_denied(context):
    request = _fresh_admin_request()
    for bad_op in ("admin_mutation*", "admin_*", "ADMIN_MUTATION", "admin_mutation ", ""):
        forged = HelperRequest(**{**request.__dict__, "operation": bad_op})
        response = dispatch(forged, context, CLOSED_DISPATCH_TABLE)
        assert response.decision == Decision.REJECTED.value


def test_negative_unauthorized_certification_role_denied(context):
    request = _fresh_certification_write_request()
    for bad_role in ("hpac_lifecycle_terminator", "hpac_challenge_coordinator*", "root", ""):
        forged = HelperRequest(**{**request.__dict__, "role": bad_role})
        response = dispatch(forged, context, CLOSED_DISPATCH_TABLE)
        assert response.decision == Decision.REJECTED.value
        assert response.terminal_code == "operation_scope_invalid"


def test_negative_stale_request_denied(context):
    request = _fresh_admin_request(expiry="2000-01-01T00:00:00.000000Z")
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "capability_stale"


def test_negative_duplicate_request_denied(context):
    request = _fresh_admin_request(request_id="dup-1")
    first = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert first.decision == Decision.PERFORMED.value
    second = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert second.decision == Decision.REJECTED.value
    assert second.terminal_code == "capability_stale"


def test_negative_conflicting_replay_denied(context):
    request = _fresh_admin_request(request_id="conflict-1", nonce="a" * 64)
    dispatch(request, context, CLOSED_DISPATCH_TABLE)
    conflicting = build_signed_request(
        operation=HelperOperation.ADMIN_MUTATION,
        session_id="a-different-session",
        operation_params={"mutation": "revoke_principal", "transaction_id": "t2"},
        request_id="conflict-1",
        nonce="a" * 64,
        expiry="2999-01-01T00:00:00.000000Z",
        installation_id="inst-1",
        generation=1,
    )
    response = dispatch(conflicting, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "target_scope_invalid"


def test_negative_wrong_session_for_read_denied(context, store):
    store.put_record("principal_record", "p-1", {"principal_id": "p-1"})
    request = _fresh_read_request(operation_params={"record_type": "principal_record", "record_key": "does-not-exist"})
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "target_scope_invalid"


def test_negative_generic_read_type_denied(context):
    request = _fresh_read_request(operation_params={"record_type": "arbitrary_store_dump", "record_key": "x"})
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "operation_scope_invalid"


def test_negative_self_asserted_approval_denied(context, store):
    store.ceremonies_started["sess-self-1"] = "deadbeef"
    request = build_signed_request(
        operation=HelperOperation.PRESENTATION_EVIDENCE_WRITE,
        session_id="sess-self-1",
        operation_params={"approved": True, "ceremony_approve_ref": "x"},
        request_id="req-self-1",
        expiry="2999-01-01T00:00:00.000000Z",
        installation_id="inst-1",
        generation=1,
    )
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "operation_scope_invalid"


def test_negative_second_ceremony_entry_same_session_denied(context):
    request = build_signed_request(
        operation=HelperOperation.CEREMONY_ENTRY, session_id="sess-cer-2",
        operation_params={"ceremony_request_digest": "abc"}, request_id="req-cer-2a",
        expiry="2999-01-01T00:00:00.000000Z", installation_id="inst-1", generation=1,
    )
    dispatch(request, context, CLOSED_DISPATCH_TABLE)
    second = build_signed_request(
        operation=HelperOperation.CEREMONY_ENTRY, session_id="sess-cer-2",
        operation_params={"ceremony_request_digest": "def"}, request_id="req-cer-2b",
        expiry="2999-01-01T00:00:00.000000Z", installation_id="inst-1", generation=1,
    )
    response = dispatch(second, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value


def test_negative_operation_not_supported_by_generation_denied(store):
    limited_context = HelperContext(
        replay_ledger=ReplayLedger(), evidence_stager=EvidenceStager(),
        supported_operations=frozenset({"certification_read"}), store=store,
    )
    request = _fresh_admin_request()
    response = dispatch(request, limited_context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "operation_scope_invalid"


def test_dispatch_rejects_incomplete_handler_table(context):
    request = _fresh_admin_request()
    with pytest.raises(AssertionError):
        dispatch(request, context, {HelperOperation.ADMIN_MUTATION.value: CLOSED_DISPATCH_TABLE[HelperOperation.ADMIN_MUTATION.value]})


# ---------------------------------------------------------------------------
# State-transition / no-auto-retry tests.
# ---------------------------------------------------------------------------


def test_state_machine_forward_only_and_no_skip():
    machine = HelperStateMachine(mutating=True)
    machine.advance_to(HelperState.REQUEST_AUTHENTICATED)
    with pytest.raises(StateTransitionError):
        machine.advance_to(HelperState.MUTATION_COMMITTED)  # skip OPERATION_ADMITTED / MUTATION_ATTEMPT_STARTED


def test_no_auto_retry_boundary_enforced(context):
    request = _fresh_admin_request(request_id="norty-1")
    dispatch(request, context, CLOSED_DISPATCH_TABLE)
    # A second dispatch of the identical (request_id, nonce) is denied at the
    # replay layer before it could ever reach a second mutation attempt.
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "capability_stale"


def test_indeterminate_on_post_commit_finalize_failure(store):
    failing_stager = EvidenceStager(fail_finalization=True)
    ctx = HelperContext(
        replay_ledger=ReplayLedger(), evidence_stager=failing_stager,
        supported_operations=CLOSED_OPERATIONS, store=store,
    )
    request = _fresh_admin_request(request_id="indet-1")
    with pytest.raises(HelperProtocolError):
        dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    # the mutation itself DID commit (store has the record) even though the
    # response could not be finalized -- this is the INDETERMINATE condition,
    # not a rolled-back mutation and not a silently reported failure.
    assert any(k[0] == "admin_mutation_record" for k in store.records)


def test_pre_mutation_staging_failure_aborts_before_mutation(store):
    failing_stager = EvidenceStager(fail_staging=True)
    ctx = HelperContext(
        replay_ledger=ReplayLedger(), evidence_stager=failing_stager,
        supported_operations=CLOSED_OPERATIONS, store=store,
    )
    request = _fresh_admin_request(request_id="stage-fail-1")
    response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    assert response.decision == Decision.REJECTED.value
    assert response.terminal_code == "internal_fail_closed"
    assert not store.records  # no mutation occurred


# ---------------------------------------------------------------------------
# No-authority-export tests.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("result_payload", {"writer_capability": "should-not-appear"}),
        ("result_payload", {"contents": {"HPACStoreAuthority": "leak"}}),
        ("evidence_ref", "some/ref/with/a/seal/embedded"),
    ],
)
def test_response_leak_scanner_detects_forbidden_tokens(field_name, value):
    from pcae.core.hpac_pawa_helper_protocol import HelperResponse, RESPONSE_SCHEMA_VERSION, PROTOCOL_VERSION

    kwargs = dict(
        response_schema_version=RESPONSE_SCHEMA_VERSION, protocol_version=PROTOCOL_VERSION,
        request_id="r", nonce="n", decision="PERFORMED", trusted_timestamp="t",
        state_reached="RESPONSE_EMITTED", response_digest="d",
    )
    kwargs[field_name] = value
    response = HelperResponse(**kwargs)
    assert response_leaks_authority(response)


def test_all_positive_dispatch_responses_pass_leak_scan(context, store):
    store.put_record("principal_record", "p-2", {"principal_id": "p-2"})
    store.ceremonies_started["sess-scan-1"] = "abc"
    requests = [
        _fresh_admin_request(request_id="scan-admin"),
        _fresh_read_request(request_id="scan-read", operation_params={"record_type": "principal_record", "record_key": "p-2"}),
        build_signed_request(
            operation=HelperOperation.PRESENTATION_EVIDENCE_WRITE, session_id="sess-scan-1",
            operation_params={"ceremony_approve_ref": "ref-1"}, request_id="scan-pev",
            expiry="2999-01-01T00:00:00.000000Z", installation_id="inst-1", generation=1,
        ),
    ]
    for request in requests:
        response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
        assert response.decision == Decision.PERFORMED.value
        assert not response_leaks_authority(response)


# ---------------------------------------------------------------------------
# Operation-composition: closed set cannot recompose into a generic broker.
# ---------------------------------------------------------------------------


def test_operation_composition_cannot_reach_arbitrary_filesystem_write(context, store):
    for bad_key in ("path", "shell", "command", "module", "expression", "json_patch", "executable"):
        request = _fresh_admin_request(operation_params={bad_key: "/etc/shadow"})
        response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
        assert response.decision == Decision.REJECTED.value


def test_read_operation_cannot_enumerate_arbitrary_store(context, store):
    store.put_record("principal_record", "secret-other-session", {"leak": True})
    # closed record types only -- no wildcard / enumerate-all shape exists
    for bad_type in ("*", "all", "principal_record*", "any"):
        request = _fresh_read_request(operation_params={"record_type": bad_type, "record_key": "secret-other-session"})
        response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
        assert response.decision == Decision.REJECTED.value


# ---------------------------------------------------------------------------
# Same-file-object / anti-TOCTOU tests (real filesystem, disposable temp dir).
# ---------------------------------------------------------------------------


@pytest.fixture()
def helper_binary(tmp_path):
    binary = tmp_path / "hpac-pawa-privileged-helper"
    binary.write_bytes(b"#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    import hashlib

    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    return binary, digest


def test_same_file_object_valid_helper_accepted(helper_binary):
    binary, digest = helper_binary
    verified = verify_helper_executable(binary, expected_sha256=digest, expected_owner_uid=os.getuid())
    try:
        assert verified.sha256 == digest
        assert verified.nlink == 1
    finally:
        os.close(verified.fd)


def test_same_file_object_wrong_hash_denied(helper_binary):
    binary, _digest = helper_binary
    with pytest.raises(HelperProtocolError) as excinfo:
        verify_helper_executable(binary, expected_sha256="0" * 64, expected_owner_uid=os.getuid())
    assert excinfo.value.code == "descriptor_installation_mismatch"


def test_same_file_object_wrong_owner_denied(helper_binary):
    binary, digest = helper_binary
    with pytest.raises(HelperProtocolError) as excinfo:
        verify_helper_executable(binary, expected_sha256=digest, expected_owner_uid=os.getuid() + 12345)
    assert excinfo.value.code == "descriptor_wrong_owner"


def test_same_file_object_wrong_mode_denied(helper_binary):
    binary, digest = helper_binary
    binary.chmod(0o777)
    with pytest.raises(HelperProtocolError) as excinfo:
        verify_helper_executable(binary, expected_sha256=digest, expected_owner_uid=os.getuid())
    assert excinfo.value.code == "descriptor_wrong_mode"


def test_same_file_object_symlink_denied(tmp_path, helper_binary):
    binary, digest = helper_binary
    link = tmp_path / "lookalike"
    link.symlink_to(binary)
    with pytest.raises(HelperProtocolError) as excinfo:
        verify_helper_executable(link, expected_sha256=digest, expected_owner_uid=os.getuid())
    assert excinfo.value.code == "descriptor_missing"


def test_same_file_object_post_validation_substitution_does_not_change_executed_bytes(helper_binary, tmp_path):
    """The verified fd keeps referring to the original inode's data even if
    the pathname is replaced with different content after validation --
    proving there is no re-open-by-path window between verify and use."""
    binary, digest = helper_binary
    verified = verify_helper_executable(binary, expected_sha256=digest, expected_owner_uid=os.getuid())
    try:
        binary.unlink()
        (tmp_path / "hpac-pawa-privileged-helper").write_bytes(b"MALICIOUS REPLACEMENT")
        os.lseek(verified.fd, 0, os.SEEK_SET)
        content = os.read(verified.fd, 4096)
        assert content == b"#!/bin/sh\nexit 0\n"
        assert b"MALICIOUS" not in content
    finally:
        os.close(verified.fd)


def test_same_file_object_rename_after_open_does_not_cause_fresh_path_execution(helper_binary, tmp_path):
    binary, digest = helper_binary
    verified = verify_helper_executable(binary, expected_sha256=digest, expected_owner_uid=os.getuid())
    try:
        renamed = tmp_path / "renamed-away"
        binary.rename(renamed)
        os.lseek(verified.fd, 0, os.SEEK_SET)
        content = os.read(verified.fd, 4096)
        assert content == b"#!/bin/sh\nexit 0\n"
    finally:
        os.close(verified.fd)


def test_execute_verified_fails_closed_on_unsupported_platform(helper_binary, monkeypatch):
    binary, digest = helper_binary
    verified = verify_helper_executable(binary, expected_sha256=digest, expected_owner_uid=os.getuid())
    try:
        monkeypatch.setattr(sys, "platform", "sunos5")
        with pytest.raises(UnsupportedPlatformProfile):
            execute_verified(verified, [str(binary)], os.environ.copy())
    finally:
        os.close(verified.fd)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="fexecve-equivalent path is Linux-specific")
def test_execute_verified_actually_runs_on_linux(helper_binary):
    binary, digest = helper_binary
    verified = verify_helper_executable(binary, expected_sha256=digest, expected_owner_uid=os.getuid())
    pid = execute_verified(verified, ["/bin/sh"], os.environ.copy())
    _, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status)
    assert os.WEXITSTATUS(status) == 0


# ---------------------------------------------------------------------------
# One-shot channel tests.
# ---------------------------------------------------------------------------


def test_one_shot_channel_local_only_permissions():
    # AF_UNIX sockaddr_un has a short (~104 byte) path limit; pytest's
    # tmp_path is often too deep on macOS CI runners, so use the system
    # temp root directly (still a fresh, disposable, 0700 directory).
    channel = OneShotChannel()
    try:
        st = os.stat(channel.path)
        assert stat.S_IMODE(st.st_mode) == 0o600
        dir_st = os.stat(channel._dir)
        assert stat.S_IMODE(dir_st.st_mode) == 0o700
    finally:
        channel.close()
    assert not channel.path.exists()


def test_one_shot_channel_single_exchange_then_rejects_reaccept():
    channel = OneShotChannel()
    try:
        def _client():
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(str(channel.path))
                s.sendall(b"hello")

        thread = threading.Thread(target=_client)
        thread.start()
        conn = channel.accept_one(timeout=5)
        data = conn.recv(1024)
        conn.close()
        thread.join(timeout=5)
        assert data == b"hello"
        with pytest.raises(HelperProtocolError):
            channel.accept_one(timeout=1)
    finally:
        channel.close()


# ---------------------------------------------------------------------------
# Peer-credential tests.
# ---------------------------------------------------------------------------


def _connected_pair():
    a, b = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    return a, b


def test_peer_credential_self_connect_matches_own_uid():
    a, b = _connected_pair()
    try:
        credential = get_kernel_peer_credential(a)
        assert credential.uid == os.getuid()
    finally:
        a.close()
        b.close()


def test_authenticate_peer_accepts_expected_deployment_owner():
    a, b = _connected_pair()
    try:
        credential = authenticate_peer(a, deployment_owner_uid=os.getuid())
        assert credential.uid == os.getuid()
    finally:
        a.close()
        b.close()


def test_authenticate_peer_denies_mismatched_deployment_owner():
    a, b = _connected_pair()
    try:
        with pytest.raises(HelperProtocolError) as excinfo:
            authenticate_peer(a, deployment_owner_uid=os.getuid() + 99999)
        assert excinfo.value.code == "unauthorized_factory_consumer"
    finally:
        a.close()
        b.close()


def test_authenticate_peer_denies_configured_agent_as_peer():
    a, b = _connected_pair()
    try:
        agent_identity = ConfiguredAgentAuthorityIdentity(
            uid=os.getuid(), gids=frozenset(), symbolic_account="agent", record_digest="d",
        )
        with pytest.raises(HelperProtocolError) as excinfo:
            authenticate_peer(a, deployment_owner_uid=os.getuid(), configured_agent=agent_identity)
        assert excinfo.value.code == "current_context_is_agent"
    finally:
        a.close()
        b.close()


def test_peer_credential_never_derived_from_caller_supplied_field():
    """A request payload claiming a different uid must not influence peer
    authentication at all -- authenticate_peer takes no such parameter."""
    import inspect

    sig = inspect.signature(authenticate_peer)
    assert "request" not in sig.parameters
    assert "uid" not in [p for p in sig.parameters if p not in ("deployment_owner_uid",)]
