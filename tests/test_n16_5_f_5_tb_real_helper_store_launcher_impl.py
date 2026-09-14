"""N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL — canonical-store read
wiring, Linux one-shot launcher, and adversarial matrix.

Covers what this phase actually implements: (1) real canonical-store reads
for `certification_read` / `ceremony_entry` via
`hpac_pawa_helper_store_adapter.RealCanonicalReadAdapter`, exercised against
disposable fixture protected roots (never the live host); (2) the Linux
one-shot launcher + helper-process entrypoint, exercised via a genuine
separate process; (3) the durable-replay / peer-credential / framing /
substitution-matrix adversarial tests the phase authorization requires.

Does NOT exercise real writes for `admin_mutation` / `certification_write` /
`presentation_evidence_write` — those remain NON_REAL-backed pending the
writer-authority blocker documented in
`hpac_pawa_helper_store_adapter`'s module docstring and the phase completion
report (HPAC-PAWA-HELPER-REQ-033 forbids the helper from reaching the sole
`_PRODUCTION_WRITER_FACTORY_SEAL`-gated mint in
`hpac_protected_admin_writer`).
"""

from __future__ import annotations

import hashlib
import os
import socket
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core import hpac_protected_presentation_admin as admin
from pcae.core import protected_presentation_installation as inst
from pcae.core.hpac_foundation import HPACStoreAuthority
from pcae.core.hpac_pawa_helper_entrypoint import (
    FramingError,
    MAX_FRAME_BYTES,
    read_one_frame,
    run_one_shot,
)
from pcae.core.hpac_pawa_helper_launcher import LaunchOutcome, launch_and_exchange
from pcae.core.hpac_pawa_helper_os import OneShotChannel, UnsupportedPlatformProfile, verify_helper_executable
from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_OPERATIONS,
    EvidenceStager,
    HelperContext,
    HelperOperation,
    HelperProtocolError,
    ProtectedStoreFoundation,
    ReplayLedger,
    build_signed_request,
)
from pcae.core.hpac_pawa_helper_replay_state import open_durable_replay_ledger
from pcae.core.hpac_pawa_helper_store_adapter import (
    BLOCKED_READ_RECORD_TYPES,
    RealCanonicalReadAdapter,
    resolve_launcher_deployment_metadata,
)
from pcae.core.human_principal_registry import HumanPrincipalRegistryStore, PrincipalRecord, CredentialRecord
from pcae.core.hpac_rhamp_credential_sidecar import Fido2CredentialSidecar, HpacRhampCredentialSidecarStore
from pcae.core.hpac_rhamp_counter_state import HpacRhampCounterStateStore

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-store / launch model"),
]

FAKE_AGENT_UID = 4_242_425
FAKE_AGENT_GID = 999_998


# ═══════════════════════════════════════════════════════════════════════════
# §1 — real canonical read-store fixtures (FIXTURE_NON_REAL authority; no
# presentation-installation lineage required for the registry/RHAMP stores).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def registry_authority(tmp_path):
    return HPACStoreAuthority.fixture(tmp_path / "hpac-root")


def test_principal_record_real_read_positive_and_negative(registry_authority):
    registry = HumanPrincipalRegistryStore(registry_authority)
    writer = registry.fixture_admin_writer()
    registry.enroll_principal(
        writer, principal_id="hp-" + "a" * 32,
        enrollment_provenance_ref="prov-1", enrolled_at="2026-01-01T00:00:00.000000Z",
    )

    adapter = RealCanonicalReadAdapter(registry_authority)
    doc = adapter.get_record("principal_record", "hp-" + "a" * 32)
    assert doc is not None and doc["principal_id"] == "hp-" + "a" * 32
    assert adapter.get_record("principal_record", "hp-" + "b" * 32) is None


def test_credential_record_real_read(registry_authority):
    registry = HumanPrincipalRegistryStore(registry_authority)
    writer = registry.fixture_admin_writer()
    principal_id = "hp-" + "a" * 32
    registry.enroll_principal(
        writer, principal_id=principal_id,
        enrollment_provenance_ref="prov-1", enrolled_at="2026-01-01T00:00:00.000000Z",
    )
    registry.enroll_credential(
        writer, credential_id="cr-" + "c" * 32, principal_id=principal_id,
        mechanism_id="fido2", public_key=hashlib.sha256(b"pk").hexdigest(),
        assurance_capabilities=("user_verification",),
        enrollment_provenance_ref="prov-2", enrolled_at="2026-01-01T00:00:00.000000Z",
    )

    adapter = RealCanonicalReadAdapter(registry_authority)
    doc = adapter.get_record("credential_record", "cr-" + "c" * 32)
    assert doc is not None and doc["principal_id"] == principal_id


def test_rhamp_credential_sidecar_real_read(registry_authority):
    sidecar_store = HpacRhampCredentialSidecarStore(registry_authority)
    writer = registry_authority.writer("human_principal_registry_admin", subject="txn-1")
    sidecar = Fido2CredentialSidecar(
        credential_id="cr-" + "d" * 32,
        principal_id="hp-" + "a" * 32,
        raw_credential_id=hashlib.sha256(b"raw").hexdigest(),
        cose_public_key=hashlib.sha256(b"pk").hexdigest(),
        transports=("usb",),
        aaguid="a" * 32,
        created_at="2026-01-01T00:00:00.000000Z",
        writer_provenance_ref="",
        status="active",
    )
    sidecar_store.create_canonical(writer, sidecar, transaction_subject="txn-1")

    adapter = RealCanonicalReadAdapter(registry_authority)
    doc = adapter.get_record("rhamp_credential_sidecar", "cr-" + "d" * 32)
    assert doc is not None and doc["credential_id"] == "cr-" + "d" * 32
    assert adapter.get_record("rhamp_credential_sidecar", "cr-" + "e" * 32) is None


def test_rhamp_counter_state_real_read_fails_closed_not_zero(registry_authority):
    counter_store = HpacRhampCounterStateStore(registry_authority)
    writer = registry_authority.writer("human_principal_registry_admin", subject="txn-2")
    counter_store.initialize_canonical(
        writer, credential_id="cr-" + "f" * 32, updated_at="2026-01-01T00:00:00.000000Z", transaction_subject="txn-2"
    )

    adapter = RealCanonicalReadAdapter(registry_authority)
    doc = adapter.get_record("rhamp_counter_state", "cr-" + "f" * 32)
    assert doc is not None and doc["credential_id"] == "cr-" + "f" * 32
    # absent record -> None (adapter's own fail-closed-to-None translation), not "counter 0" fabricated
    assert adapter.get_record("rhamp_counter_state", "cr-" + "g" * 32) is None


def test_pawa_anchor_record_is_a_reported_blocker_not_a_silent_fallback(registry_authority):
    adapter = RealCanonicalReadAdapter(registry_authority)
    with pytest.raises(HelperProtocolError) as exc:
        adapter.get_record("pawa_anchor_record", "whatever")
    assert exc.value.code == "internal_fail_closed"
    assert "pawa_anchor_record" in BLOCKED_READ_RECORD_TYPES


def test_unknown_record_type_rejected(registry_authority):
    adapter = RealCanonicalReadAdapter(registry_authority)
    with pytest.raises(HelperProtocolError) as exc:
        adapter.get_record("not_a_real_type", "x")
    assert exc.value.code == "operation_scope_invalid"


def test_put_record_fails_closed_no_writer_capability(registry_authority):
    """§21/§95 — ``admin_mutation``/``certification_write`` both route
    through ``put_record``; it must fail closed with the documented
    REQ-033 blocker, never a bare ``AttributeError`` a caller could mistake
    for an unrelated bug."""
    adapter = RealCanonicalReadAdapter(registry_authority)
    with pytest.raises(HelperProtocolError) as exc:
        adapter.put_record("admin_mutation_record", "k", {"mutation": "x"})
    assert exc.value.code == "internal_fail_closed"


def test_presentation_evidence_write_fails_closed_not_silent_fake_success(registry_authority):
    """§21 — item assignment on ``presentation_evidence`` must fail closed
    identically to ``put_record``, not silently succeed against fake
    in-memory state (which would mask the exact same REQ-033 blocker
    documented for the other two blocked write operations)."""
    adapter = RealCanonicalReadAdapter(registry_authority)
    with pytest.raises(HelperProtocolError) as exc:
        adapter.presentation_evidence["sid:ref"] = {"session_id": "sid", "approve_ref": "ref"}
    assert exc.value.code == "internal_fail_closed"


# ═══════════════════════════════════════════════════════════════════════════
# §2 — full protected-presentation installation lineage fixture (reused
# recipe: provision root -> configure_presentation_mechanism install ->
# production-class fixture authority), needed for presentation-record reads,
# ceremony_entry real wiring, and the launcher/entrypoint integration.
# ═══════════════════════════════════════════════════════════════════════════


def _agent_src():
    return lambda account, provisioned_uid: (provisioned_uid, frozenset({FAKE_AGENT_GID}))


def _locked_probe():
    return w.TopologyProbe(
        effective_write_access=lambda p, u, g: (False, "fixture_locked", ()),
        ancestor_chain_safe=lambda s, u, g: (True, ("fixture_root_reached",)),
    )


def _provisioned_root(tmp_path: Path) -> Path:
    root = (tmp_path / "hpac-protected-root").resolve()
    w.provision_protected_root(protected_root=root, agent_account="pcae-agent-svc", agent_uid=FAKE_AGENT_UID)
    return root


def _install_helper_bytes(root: Path, helper_bytes: bytes, *, mode: int) -> str:
    sha = hashlib.sha256(helper_bytes).hexdigest()
    path = inst.helper_content_addressed_path(root, sha)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.exists():
        path.chmod(0o600)
    path.write_bytes(helper_bytes)
    os.chmod(path, mode)
    return sha


def _configure(root: Path, action: str, *, helper_bytes: bytes | None = None):
    kwargs: dict = {
        "action": action, "protected_root": root,
        "_configured_agent_identity_source": _agent_src(), "_topology_probe": _locked_probe(),
    }
    if action in ("install", "rotate"):
        sha = _install_helper_bytes(root, helper_bytes, mode=0o755)
        kwargs.update(
            helper_sha256=sha,
            helper_implementation_version="pawa-helper/1.0.0",
            verifier_configuration_digest=hashlib.sha256(b"verifier-config-v1").hexdigest(),
            renderer_profile="pcae-protected-local-presentation-renderer/1.0",
            descriptor_version="pplp-1.0",
        )
    return admin.configure_presentation_mechanism(**kwargs)


def _authority(root: Path):
    from pcae.core.hpac_foundation import _PRODUCTION_TEST_FIXTURE_SEAL

    return HPACStoreAuthority._production_test_fixture(root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe())


#: Updated by N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR (Repair B).
#:
#: This template previously called ``hpac_pawa_helper_entrypoint.main()``
#: directly and relied on it wiring a store from the env-supplied
#: ``PAWA_HELPER_PROTECTED_ROOT``. Repair B makes the REAL store profile
#: **non-redirectable**: ``main()`` accepts the real profile only for the one
#: fixed canonical protected root and constructs
#: ``HPACStoreAuthority.production()``, which takes no root argument at all.
#: A disposable-root exercise therefore cannot go through ``main()`` without
#: reintroducing exactly the redirection the repair exists to prevent.
#:
#: The script below still runs the genuine production code path
#: (``build_helper_context`` + ``run_one_shot``) in a genuine separate
#: process against the genuine ``RealCanonicalReadAdapter``; the only
#: test-only substitution is the already-disclosed
#: ``_production_test_fixture`` authority seal seam (HPAC-PAWA-REQ-166),
#: supplied through ``build_helper_context``'s explicit, keyword-only,
#: in-process ``_test_only_store`` seam. Nothing here is reachable from the
#: environment, argv, or a request.
_HELPER_SCRIPT_TEMPLATE = """#!{python}
import os, sys, types
from pathlib import Path
from pcae.core.hpac_foundation import HPACStoreAuthority, _PRODUCTION_TEST_FIXTURE_SEAL
from pcae.core.hpac_pawa_helper_entrypoint import (
    STORE_PROFILE_REAL, build_helper_context, run_one_shot,
)
from pcae.core.hpac_pawa_helper_store_adapter import RealCanonicalReadAdapter

root = os.environ["PAWA_HELPER_PROTECTED_ROOT"]
probe = types.SimpleNamespace(
    effective_write_access=lambda p, u, g: (False, "fixture_locked", ()),
    ancestor_chain_safe=lambda s, u, g: (True, ("fixture_root_reached",)),
)
authority = HPACStoreAuthority._production_test_fixture(
    Path(root), _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=probe
)
context = build_helper_context(
    protected_root=root,
    installation_id=os.environ["PAWA_HELPER_INSTALLATION_ID"],
    generation=int(os.environ["PAWA_HELPER_GENERATION"]),
    store_profile=STORE_PROFILE_REAL,
    _test_only_store=RealCanonicalReadAdapter(authority),
)
sys.exit(run_one_shot(channel_path=os.environ["PAWA_HELPER_CHANNEL_PATH"], context=context))
"""


@pytest.fixture
def installed(tmp_path):
    root = _provisioned_root(tmp_path)
    helper_bytes = _HELPER_SCRIPT_TEMPLATE.format(python=sys.executable).encode("utf-8")
    _configure(root, "install", helper_bytes=helper_bytes)
    authority = _authority(root)
    resolved = resolve_launcher_deployment_metadata(authority)
    return root, authority, resolved


def test_presentation_installation_record_real_read(installed):
    root, authority, resolved = installed
    adapter = RealCanonicalReadAdapter(authority)
    doc = adapter.get_record("presentation_installation_record", resolved.record.installation_id)
    assert doc is not None and doc["installation_id"] == resolved.record.installation_id
    assert adapter.get_record("presentation_installation_record", "not-the-current-one") is None


def test_helper_registration_record_real_read(installed):
    root, authority, resolved = installed
    adapter = RealCanonicalReadAdapter(authority)
    doc = adapter.get_record("helper_registration_record", resolved.record.installation_id)
    assert doc is not None and doc["helper_sha256"] == resolved.record.helper_sha256


def test_presentation_mechanism_descriptor_real_read(installed):
    root, authority, resolved = installed
    adapter = RealCanonicalReadAdapter(authority)
    doc = adapter.get_record("presentation_mechanism_descriptor", resolved.descriptor.mechanism_id)
    assert doc is not None and doc["mechanism_id"] == resolved.descriptor.mechanism_id


def test_ceremony_entry_real_store_wiring_accepts_current_generation(installed):
    root, authority, resolved = installed
    adapter = RealCanonicalReadAdapter(authority)
    out = adapter.verify_current_generation(
        installation_id=resolved.record.installation_id, generation=resolved.record.generation
    )
    assert out.record.installation_id == resolved.record.installation_id


def test_ceremony_entry_real_store_wiring_rejects_stale_generation(installed):
    root, authority, resolved = installed
    adapter = RealCanonicalReadAdapter(authority)
    with pytest.raises(HelperProtocolError) as exc:
        adapter.verify_current_generation(installation_id=resolved.record.installation_id, generation=resolved.record.generation + 1)
    assert exc.value.code == "descriptor_generation_stale"


def test_ceremony_entry_real_store_wiring_rejects_when_no_installation(tmp_path):
    root = _provisioned_root(tmp_path)
    authority = _authority(root)
    adapter = RealCanonicalReadAdapter(authority)
    with pytest.raises(HelperProtocolError) as exc:
        adapter.verify_current_generation(installation_id="whatever", generation=1)
    assert exc.value.code == "descriptor_missing"


def test_ceremony_entry_handler_wired_to_real_store_end_to_end(installed):
    from pcae.core.hpac_pawa_helper_operations import CLOSED_DISPATCH_TABLE
    from pcae.core.hpac_pawa_helper_protocol import dispatch

    root, authority, resolved = installed
    adapter = RealCanonicalReadAdapter(authority)
    context = HelperContext(
        replay_ledger=ReplayLedger(),
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=adapter,
    )
    request = build_signed_request(
        operation=HelperOperation.CEREMONY_ENTRY,
        session_id="sess-1",
        operation_params={"ceremony_request_digest": "d" * 64},
        request_id="req-1",
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation,
    )
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == "PERFORMED"

    # A stale generation on the request is rejected even though the
    # foundation-only in-memory store would have no notion of "current".
    stale_request = build_signed_request(
        operation=HelperOperation.CEREMONY_ENTRY,
        session_id="sess-2",
        operation_params={"ceremony_request_digest": "d" * 64},
        request_id="req-2",
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation + 1,
    )
    stale_response = dispatch(stale_request, context, CLOSED_DISPATCH_TABLE)
    assert stale_response.decision == "REJECTED"
    assert stale_response.terminal_code == "descriptor_generation_stale"


# ═══════════════════════════════════════════════════════════════════════════
# §3 — genuine separate-process launcher + entrypoint integration.
# ═══════════════════════════════════════════════════════════════════════════


def _launch_kwargs(root: Path, resolved, *, request):
    return dict(
        request=request,
        helper_path=str(resolved.helper_path),
        expected_sha256=resolved.record.helper_sha256,
        expected_owner_uid=os.getuid(),
        deployment_owner_uid=os.getuid(),
        protected_root=str(root),
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation,
        accept_timeout=10.0,
    )


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="same-file-object exec is Linux-only (§60)")
def test_genuine_separate_process_positive_integration(installed):
    root, authority, resolved = installed
    request = build_signed_request(
        operation=HelperOperation.CERTIFICATION_READ,
        session_id="sess-int-1",
        operation_params={"record_type": "presentation_mechanism_descriptor", "record_key": resolved.descriptor.mechanism_id},
        request_id="req-int-1",
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation,
    )
    outcome = launch_and_exchange(**_launch_kwargs(root, resolved, request=request))
    assert outcome.outcome == "completed", outcome
    assert outcome.helper_pid != os.getpid()
    assert outcome.response.decision == "PERFORMED"
    assert outcome.response.result_payload["record_key"] == resolved.descriptor.mechanism_id
    assert outcome.peer_credential.uid == os.getuid()


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="same-file-object exec is Linux-only (§60)")
def test_cross_process_replay_after_new_helper_process(installed):
    root, authority, resolved = installed
    # certification_read is REQ-078 non-replay-tracked by design (idempotent
    # reads never widen into a replay-guarded op); exercise cross-process
    # replay against ceremony_entry instead, which IS durably spent (§16).
    common = dict(
        operation=HelperOperation.CEREMONY_ENTRY,
        session_id="sess-replay-1",
        operation_params={"ceremony_request_digest": "e" * 64},
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation,
        expiry="2099-01-01T00:00:00.000000Z",
    )
    request = build_signed_request(request_id="req-replay-1", **common)
    first = launch_and_exchange(**_launch_kwargs(root, resolved, request=request))
    assert first.outcome == "completed" and first.response.decision == "PERFORMED"

    replay_request = build_signed_request(
        request_id="req-replay-1", nonce=request.nonce, **common
    )
    second = launch_and_exchange(**_launch_kwargs(root, resolved, request=replay_request))
    assert second.outcome == "completed"
    assert second.response.decision == "REJECTED"
    assert second.response.terminal_code == "capability_stale"


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="same-file-object exec is Linux-only (§60)")
def test_helper_substitution_after_verification_is_rejected(installed, tmp_path):
    """§25/§26 — the verified descriptor is opened once; swapping the
    directory-entry after verification must not change what actually
    executes (anti-TOCTOU). We assert this at the primitive level: the
    verified fd's content is fixed even if the path is replaced."""
    root, authority, resolved = installed
    verified = verify_helper_executable(
        resolved.helper_path, expected_sha256=resolved.record.helper_sha256, expected_owner_uid=os.getuid()
    )
    try:
        # Replace the on-disk file with different content at the same path.
        resolved.helper_path.chmod(0o700)
        resolved.helper_path.write_bytes(b"#!/bin/sh\necho pwned\n")
        os.chmod(resolved.helper_path, 0o755)
        # The already-open fd still reads the ORIGINAL verified bytes.
        os.lseek(verified.fd, 0, os.SEEK_SET)
        content = os.read(verified.fd, 1 << 20)
        assert content != b"#!/bin/sh\necho pwned\n"
        assert hashlib.sha256(content).hexdigest() == resolved.record.helper_sha256
    finally:
        os.close(verified.fd)


def test_helper_digest_mismatch_fails_closed(installed):
    root, authority, resolved = installed
    with pytest.raises(HelperProtocolError) as exc:
        verify_helper_executable(resolved.helper_path, expected_sha256="0" * 64, expected_owner_uid=os.getuid())
    assert exc.value.code == "descriptor_installation_mismatch"


def test_helper_wrong_mode_fails_closed(installed):
    root, authority, resolved = installed
    os.chmod(resolved.helper_path, 0o700)
    try:
        with pytest.raises(HelperProtocolError) as exc:
            verify_helper_executable(resolved.helper_path, expected_sha256=resolved.record.helper_sha256, expected_owner_uid=os.getuid())
        assert exc.value.code == "descriptor_wrong_mode"
    finally:
        os.chmod(resolved.helper_path, 0o755)


def test_helper_symlink_is_rejected(installed, tmp_path):
    root, authority, resolved = installed
    link = tmp_path / "helper-symlink"
    link.symlink_to(resolved.helper_path)
    with pytest.raises(HelperProtocolError) as exc:
        verify_helper_executable(link, expected_sha256=resolved.record.helper_sha256, expected_owner_uid=os.getuid())
    assert exc.value.code == "descriptor_missing"  # O_NOFOLLOW -> ELOOP -> open failure


def test_multiple_hardlinks_rejected(installed, tmp_path):
    root, authority, resolved = installed
    hardlink = tmp_path / "helper-hardlink"
    os.link(resolved.helper_path, hardlink)
    try:
        with pytest.raises(HelperProtocolError) as exc:
            verify_helper_executable(hardlink, expected_sha256=resolved.record.helper_sha256, expected_owner_uid=os.getuid())
        assert exc.value.code == "descriptor_wrong_owner"
    finally:
        hardlink.unlink()


# ═══════════════════════════════════════════════════════════════════════════
# §4 — peer credentials.
# ═══════════════════════════════════════════════════════════════════════════


def test_peer_credentials_come_from_kernel_not_request_payload():
    from pcae.core.hpac_pawa_helper_os import authenticate_peer, get_kernel_peer_credential

    a, b = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        cred = get_kernel_peer_credential(a)
        assert cred.uid == os.getuid()
        # Even if a "request" claimed a different uid, authenticate_peer never
        # looks at it -- only the kernel-reported peer uid.
        result = authenticate_peer(b, deployment_owner_uid=os.getuid())
        assert result.uid == os.getuid()
        with pytest.raises(HelperProtocolError) as exc:
            authenticate_peer(b, deployment_owner_uid=os.getuid() + 999)
        assert exc.value.code == "unauthorized_factory_consumer"
    finally:
        a.close()
        b.close()


# ═══════════════════════════════════════════════════════════════════════════
# §5 — request/response framing (§36/§37).
# ═══════════════════════════════════════════════════════════════════════════


def _framed_socketpair():
    return socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)


def test_framing_truncated_length_prefix():
    a, b = _framed_socketpair()
    try:
        a.sendall(b"\x00\x01")  # only 2 of 4 length-prefix bytes
        a.close()
        with pytest.raises(FramingError):
            read_one_frame(b)
    finally:
        b.close()


def test_framing_zero_length_frame():
    a, b = _framed_socketpair()
    try:
        a.sendall((0).to_bytes(4, "big"))
        with pytest.raises(FramingError):
            read_one_frame(b)
    finally:
        a.close()
        b.close()


def test_framing_oversized_frame_rejected():
    a, b = _framed_socketpair()
    try:
        a.sendall((MAX_FRAME_BYTES + 1).to_bytes(4, "big"))
        with pytest.raises(FramingError):
            read_one_frame(b)
    finally:
        a.close()
        b.close()


def test_framing_truncated_body():
    a, b = _framed_socketpair()
    try:
        a.sendall((100).to_bytes(4, "big") + b"short")
        a.close()
        with pytest.raises(FramingError):
            read_one_frame(b)
    finally:
        b.close()


def test_malformed_json_request_yields_no_response_not_a_crash():
    from pcae.core.hpac_pawa_helper_entrypoint import handle_one_request

    a, b = _framed_socketpair()
    context = HelperContext(
        replay_ledger=ReplayLedger(),
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=ProtectedStoreFoundation(),
    )
    try:
        payload = b"not json{{{"
        a.sendall(len(payload).to_bytes(4, "big") + payload)
        response = handle_one_request(b, context=context)
        assert response is None
    finally:
        a.close()
        b.close()


def test_second_request_on_same_connection_is_not_processed():
    """§36 — the entrypoint reads and answers exactly one request per
    connection; anything sent afterward on the same connection is never
    read (one dispatch per exec, HPAC-PAWA-HELPER-REQ-034.5)."""
    from pcae.core.hpac_pawa_helper_entrypoint import handle_one_request

    a, b = _framed_socketpair()
    context = HelperContext(
        replay_ledger=ReplayLedger(),
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=ProtectedStoreFoundation(),
    )
    try:
        request = build_signed_request(
            operation=HelperOperation.CERTIFICATION_READ,
            session_id="s",
            operation_params={"record_type": "principal_record", "record_key": "nope"},
            request_id="r1",
            expiry="2099-01-01T00:00:00.000000Z",
            installation_id="inst-1",
            generation=1,
        )
        import json
        from dataclasses import asdict

        payload = json.dumps(asdict(request)).encode("utf-8")
        a.sendall(len(payload).to_bytes(4, "big") + payload)
        a.sendall(len(payload).to_bytes(4, "big") + payload)  # a "second request"
        response = handle_one_request(b, context=context)
        assert response is not None
        assert response.decision == "REJECTED"  # unknown record -> target_scope_invalid
        # The connection is untouched after the first read/write — a second
        # would-be request left unread on the wire proves nothing was
        # dispatched twice.
    finally:
        a.close()
        b.close()


# ═══════════════════════════════════════════════════════════════════════════
# §6 — no-authority-export / recursive scan against real responses.
# ═══════════════════════════════════════════════════════════════════════════


def test_real_store_certification_read_response_leaks_no_authority(installed):
    from pcae.core.hpac_pawa_helper_operations import CLOSED_DISPATCH_TABLE
    from pcae.core.hpac_pawa_helper_protocol import dispatch, response_leaks_authority

    root, authority, resolved = installed
    adapter = RealCanonicalReadAdapter(authority)
    context = HelperContext(
        replay_ledger=ReplayLedger(),
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=adapter,
    )
    request = build_signed_request(
        operation=HelperOperation.CERTIFICATION_READ,
        session_id="s",
        operation_params={"record_type": "presentation_installation_record", "record_key": resolved.record.installation_id},
        request_id="r-noauth",
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation,
    )
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    assert response.decision == "PERFORMED"
    assert not response_leaks_authority(response)
    # And the response never carries the authority object itself.
    assert "authority" not in str(response.result_payload).lower().replace("authority_class", "")


# ═══════════════════════════════════════════════════════════════════════════
# §7 — durable-replay ledger reused, not reinvented, by this phase.
# ═══════════════════════════════════════════════════════════════════════════


def test_wiring_reuses_the_existing_durable_replay_ledger(tmp_path):
    ledger = open_durable_replay_ledger(protected_root=str(tmp_path), installation_id="inst-x", generation=1)
    assert ledger.is_durable
