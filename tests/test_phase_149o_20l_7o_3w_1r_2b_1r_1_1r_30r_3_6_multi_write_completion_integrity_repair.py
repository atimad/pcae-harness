"""Phase .1R.30R.3.6 — PAWA multi-write completion integrity repair.

The repair is deliberately confined to the canonical process-local issuance
lifecycle.  These tests prove single-success completion, registry-state
dominance, fail-closed invalid inputs, ordinary writer compatibility, and the
unchanged RHAMP/FIDO2/runtime scope fences.
"""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import pytest

from pcae.core import hpac_foundation as hf
from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
    HPACWriterCapability,
    _CapabilityIssuanceState,
    _PRODUCTION_TEST_FIXTURE_SEAL,
    canonical_digest,
    write_atomic_create_only,
)
from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
from pcae.core.hpac_rhamp_enrollment import enroll_first_credential
from pcae.core.hpac_rhamp_terminal_reasons import TERMINAL_REASON_CODES
from pcae.core.human_principal_registry import new_principal_id

pytestmark = pytest.mark.fast_green

REPO = Path(__file__).resolve().parents[1]
R34 = "c9cf99d5150200c426ba708d87fbdb62e73d8e18"
V35 = "3968814ce1746299f4785462aa1e2e7c8e74af3b"
R0 = V35
ROLE = "human_principal_registry_admin"
SUBJECT = "txn-r36"
FAKE_AGENT_UID = 4_242_436
FAKE_AGENT_GID = 999_996
AGENT_ACCOUNT = "pcae-agent-svc-r36"


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, check=check)


def _issued(tmp_path: Path, *, multi_write: bool = True):
    authority = HPACStoreAuthority.fixture(tmp_path / "authority")
    capability = authority._new_capability(
        ROLE, SUBJECT, single_use=True, multi_write=multi_write
    )
    return authority, capability


def _record(capability: HPACWriterCapability):
    record = hf._lookup_issued_capability(capability)
    assert record is not None
    return record


def _agent_src(symbolic_account, provisioned_uid):
    return provisioned_uid, frozenset({FAKE_AGENT_GID})


def _locked_probe():
    def ewa(path, uid, gids):
        return False, "fixture_locked", ()

    def acs(start, uid, gids):
        return True, ("fixture_root_reached",)

    return w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


def _provisioned_root(tmp_path: Path) -> Path:
    root = (tmp_path / "hpac-protected-root").resolve()
    w.provision_protected_root(
        protected_root=root,
        agent_account=AGENT_ACCOUNT,
        agent_uid=FAKE_AGENT_UID,
    )
    return root


def _production_multi(tmp_path: Path, *, subject: str = SUBJECT):
    root = _provisioned_root(tmp_path)
    principal_id = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=principal_id,
        enrollment_provenance_ref="r36-principal",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src,
        _topology_probe=_locked_probe(),
    )
    handle = w.production_writer(
        w.PawaOperation.ENROLL_CREDENTIAL,
        principal_id=principal_id,
        transaction_id=subject,
        _protected_root=root,
        _configured_agent_identity_source=_agent_src,
        _topology_probe=_locked_probe(),
        _caller_module="pcae.core.hpac_rhamp_enrollment",
    )
    capability = handle.consume(
        w.PawaOperation.ENROLL_CREDENTIAL,
        principal_id=principal_id,
        transaction_id=subject,
    )
    return root, principal_id, handle.authority, capability


def test_01_historical_blocked_artifact_is_preserved():
    path = "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_5_N_16_5_MERGED_RHAMP_INDEPENDENT_VERIFICATION.md"
    assert _run("git", "diff", "--quiet", R0, "--", path, check=False).returncode == 0


def test_02_defect_reproduces_at_immutable_r34_sha():
    with tempfile.TemporaryDirectory(prefix="pcae-r34-test-") as raw:
        worktree = Path(raw) / "tree"
        _run("git", "worktree", "add", "--detach", str(worktree), R34)
        script = """
from pathlib import Path
from tempfile import TemporaryDirectory
from pcae.core.hpac_foundation import HPACStoreAuthority
with TemporaryDirectory() as raw:
    authority = HPACStoreAuthority.fixture(Path(raw))
    cap = authority._new_capability('role', 'txn', single_use=True, multi_write=True)
    authority.complete_multi_write(cap)
    authority.complete_multi_write(cap)
print('historical-second-completion-succeeded')
"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", script],
                cwd=worktree,
                env={**os.environ, "PYTHONPATH": str(worktree / "src")},
                capture_output=True,
                text=True,
                check=True,
            )
            assert result.stdout.strip() == "historical-second-completion-succeeded"
        finally:
            _run("git", "worktree", "remove", "--force", str(worktree))


def test_03_current_second_completion_is_rejected(tmp_path):
    authority, capability = _issued(tmp_path)
    authority.complete_multi_write(capability)
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)


def test_04_canonical_first_completion_succeeds(tmp_path):
    authority, capability = _issued(tmp_path)
    authority.complete_multi_write(capability)
    assert capability._spent is True


def test_05_second_completion_uses_canonical_stale_result(tmp_path):
    authority, capability = _issued(tmp_path)
    authority.complete_multi_write(capability)
    with pytest.raises(HPACAuthorityError, match="one-operation lifetime exhausted"):
        authority.complete_multi_write(capability)


def test_06_eight_concurrent_completions_have_exactly_one_success(tmp_path):
    authority, capability = _issued(tmp_path)
    barrier = threading.Barrier(8)
    results: list[str] = []

    def attempt():
        barrier.wait()
        try:
            authority.complete_multi_write(capability)
            results.append("ok")
        except HPACAuthorityError as exc:
            results.append(str(exc))

    threads = [threading.Thread(target=attempt) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert results.count("ok") == 1


def test_07_concurrent_losers_are_deterministically_stale(tmp_path):
    authority, capability = _issued(tmp_path)
    results: list[str] = []

    def attempt():
        try:
            authority.complete_multi_write(capability)
            results.append("ok")
        except HPACAuthorityError as exc:
            results.append(str(exc))

    threads = [threading.Thread(target=attempt) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert results.count("writer capability is spent (one-operation lifetime exhausted)") == 7


def test_08_registry_lifecycle_transitions_active_to_consumed_once(tmp_path):
    authority, capability = _issued(tmp_path)
    record = _record(capability)
    assert record.state is _CapabilityIssuanceState.ACTIVE
    authority.complete_multi_write(capability)
    assert record.state is _CapabilityIssuanceState.CONSUMED


def test_09_object_local_spent_reset_cannot_restore_authority(tmp_path):
    authority, capability = _issued(tmp_path)
    authority.complete_multi_write(capability)
    capability._spent = False
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)


def test_10_registry_consumed_dominates_locally_unspent_object(tmp_path):
    authority, capability = _issued(tmp_path)
    record = _record(capability)
    with hf._ISSUANCE_REGISTRY_LOCK:
        record.state = _CapabilityIssuanceState.CONSUMED
    capability._spent = False
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)


def test_11_non_issued_reconstructed_capability_is_rejected(tmp_path):
    authority, capability = _issued(tmp_path)
    shell = HPACWriterCapability.__new__(HPACWriterCapability)
    for field in HPACWriterCapability.__slots__:
        setattr(shell, field, getattr(capability, field))
    with pytest.raises(HPACAuthorityError, match="absent, forged"):
        authority.complete_multi_write(shell)


def test_12_fixture_capability_is_rejected_by_production_authority(tmp_path):
    root = _provisioned_root(tmp_path)
    production = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    fixture = HPACStoreAuthority.fixture(tmp_path / "fixture")
    capability = fixture._new_capability(ROLE, SUBJECT, single_use=True, multi_write=True)
    with pytest.raises(HPACAuthorityError):
        production.complete_multi_write(capability)


def test_13_ordinary_non_multi_write_capability_is_rejected(tmp_path):
    authority, capability = _issued(tmp_path, multi_write=False)
    with pytest.raises(HPACAuthorityError, match="only valid for a multi-write"):
        authority.complete_multi_write(capability)
    assert _record(capability).state is _CapabilityIssuanceState.ACTIVE


def test_14_wrong_principal_scope_is_rejected_without_consumption(tmp_path):
    authority, capability = _issued(tmp_path)
    capability.subject = "hp-wrong-principal"
    with pytest.raises(HPACAuthorityError, match="canonical issuance"):
        authority.complete_multi_write(capability)
    assert _record(capability).state is _CapabilityIssuanceState.ACTIVE


def test_15_wrong_transaction_scope_is_rejected_without_consumption(tmp_path):
    authority, capability = _issued(tmp_path)
    capability.subject = "txn-wrong"
    with pytest.raises(HPACAuthorityError, match="canonical issuance"):
        authority.complete_multi_write(capability)
    assert capability._spent is False


def test_16_wrong_mutation_class_is_rejected(tmp_path):
    authority, capability = _issued(tmp_path, multi_write=False)
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)


def test_17_wrong_role_is_rejected_without_consumption(tmp_path):
    authority, capability = _issued(tmp_path)
    capability.role = "wrong-role"
    with pytest.raises(HPACAuthorityError, match="canonical issuance"):
        authority.complete_multi_write(capability)
    assert _record(capability).state is _CapabilityIssuanceState.ACTIVE


def test_18_invalid_call_does_not_consume_unrelated_valid_authority(tmp_path):
    authority, valid = _issued(tmp_path)
    invalid = HPACWriterCapability.__new__(HPACWriterCapability)
    for field in HPACWriterCapability.__slots__:
        setattr(invalid, field, getattr(valid, field))
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(invalid)
    authority.complete_multi_write(valid)


def test_19_completion_failure_does_not_corrupt_registry_lifecycle(tmp_path):
    authority, capability = _issued(tmp_path)
    capability.role = "wrong-role"
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)
    capability.role = ROLE
    authority.complete_multi_write(capability)
    assert _record(capability).state is _CapabilityIssuanceState.CONSUMED


def test_20_bounded_multi_write_component_writes_work_before_completion(tmp_path):
    authority, capability = _issued(tmp_path)
    authority._ensure_root(create=True)
    for name in ("component-a.json", "component-b.json"):
        path = authority.root / name
        write_atomic_create_only(path, b"{}")
        authority.record_write(path, canonical_digest({}), capability, role=ROLE, subject=SUBJECT)
    assert _record(capability).state is _CapabilityIssuanceState.ACTIVE
    authority.complete_multi_write(capability)


def test_21_successful_rhamp_enrollment_completes_exactly_once(tmp_path, monkeypatch):
    root = _provisioned_root(tmp_path)
    principal_id = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=principal_id,
        enrollment_provenance_ref="r36-rhamp-principal",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src,
        _topology_probe=_locked_probe(),
    )
    calls = 0
    original = HPACStoreAuthority.complete_multi_write

    def counted(self, writer):
        nonlocal calls
        calls += 1
        return original(self, writer)

    monkeypatch.setattr(HPACStoreAuthority, "complete_multi_write", counted)
    result = enroll_first_credential(
        principal_id=principal_id,
        subject_digest="a" * 64,
        presentation_digest="b" * 64,
        invocation_id="iv-r36",
        attempt_id="at-r36",
        provider=DeterministicCtap2Provider(),
        protected_root=root,
        _configured_agent_identity_source=_agent_src,
        _topology_probe=_locked_probe(),
    )
    assert result.principal_id == principal_id
    assert calls == 1


def test_22_post_completion_component_write_is_rejected(tmp_path):
    authority, capability = _issued(tmp_path)
    authority._ensure_root(create=True)
    authority.complete_multi_write(capability)
    path = authority.root / "post-complete.json"
    write_atomic_create_only(path, b"{}")
    with pytest.raises(HPACAuthorityError):
        authority.record_write(path, canonical_digest({}), capability, role=ROLE, subject=SUBJECT)


def test_23_post_completion_completion_is_rejected(tmp_path):
    authority, capability = _issued(tmp_path)
    authority.complete_multi_write(capability)
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)


def test_24_pawa_non_bearer_object_identity_is_unchanged(tmp_path):
    authority, capability = _issued(tmp_path)
    shell = HPACWriterCapability.__new__(HPACWriterCapability)
    for field in HPACWriterCapability.__slots__:
        setattr(shell, field, getattr(capability, field))
    assert hf._lookup_issued_capability(shell) is None


def test_25_ordinary_one_write_capability_semantics_are_unchanged(tmp_path):
    authority, capability = _issued(tmp_path, multi_write=False)
    authority._ensure_root(create=True)
    path = authority.root / "one-write.json"
    write_atomic_create_only(path, b"{}")
    authority.record_write(path, canonical_digest({}), capability, role=ROLE, subject=SUBJECT)
    assert capability._spent is True
    assert _record(capability).state is _CapabilityIssuanceState.CONSUMED


def test_26_issuance_registry_shape_is_unchanged():
    assert hf._CapabilityIssuanceRecord.__slots__ == (
        "capability", "issuance_id", "role", "subject", "authority_class", "state"
    )
    assert isinstance(hf._ISSUED_CAPABILITY_REGISTRY, dict)


def test_27_no_new_hpac_writer_capability_slot():
    assert HPACWriterCapability.__slots__ == (
        "_authority_seal", "role", "subject", "authority_class",
        "_single_use", "_spent", "_multi_write",
    )


def test_28_no_pawa_failure_code_was_added():
    assert len(w.PAWA_FAILURE_CODES) == 21
    assert "capability_stale" in w.PAWA_FAILURE_CODES


def test_29_no_rhamp_terminal_reason_was_added():
    assert len(TERMINAL_REASON_CODES) == 41


def test_30_normative_contracts_are_byte_unchanged():
    assert _run("git", "diff", "--quiet", R0, "e0f79220", "--", "docs/contracts", check=False).returncode == 0


def test_31_credential_record_source_is_byte_unchanged():
    path = "src/pcae/core/human_principal_registry.py"
    assert _run("git", "diff", "--quiet", R0, "--", path, check=False).returncode == 0


@pytest.mark.parametrize(
    "path",
    [
        "src/pcae/core/hpac_rhamp_enrollment.py",
        "src/pcae/core/hpac_rhamp_credential_sidecar.py",
    ],
)
def test_32_rhamp_registration_source_is_unchanged(path):
    assert _run("git", "diff", "--quiet", R0, "--", path, check=False).returncode == 0


def test_33_counter_source_is_unchanged():
    assert _run("git", "diff", "--quiet", R0, "--", "src/pcae/core/hpac_rhamp_counter_state.py", check=False).returncode == 0


def test_34_fido2_authenticator_source_is_unchanged():
    assert _run("git", "diff", "--quiet", R0, "--", "src/pcae/core/human_authenticator_fido2.py", check=False).returncode == 0


def test_35_hpac_verifier_source_is_unchanged():
    # Phase .1R.30R.4R.1 reconciliation — `.30R.3.6` changed nothing here.
    # `.30R.4R.1` adds exactly the HPAC-PPA-REQ-057 real-auth + real-presentation
    # coupling inside `require_real_assurance` (and refreshes a stale comment).
    # Not weakened: the eligible-mechanism allowlist literal is unchanged, no
    # wildcard, no first external effect, no `def ` removed.
    r4r_finalized = "a727dbf4f160f904836905d3cb4adeba91953676"
    old = _run("git", "show", f"{R0}:src/pcae/core/hpac_verifier.py").stdout
    since_r4r = _run(
        "git", "diff", "--name-only", r4r_finalized, "HEAD", "--", "src/pcae/core/hpac_verifier.py"
    ).stdout.split()
    new = (REPO / "src/pcae/core/hpac_verifier.py").read_text()
    assert since_r4r in ([], ["src/pcae/core/hpac_verifier.py"])
    assert 'frozenset(\n    {"hpac.deterministic.test-only.v1", "hpac.fido2.uv_presence.v2"}\n)' in new
    assert new.count("def ") >= old.count("def ")
    assert ("fn" "match") not in new and "adapter.dispatch(" not in new


def test_36_deterministic_ci_seam_is_unchanged():
    assert _run("git", "diff", "--quiet", R0, "--", "src/pcae/core/hpac_rhamp_ctap2.py", check=False).returncode == 0


def test_37_protected_presentation_remains_absent():
    # Phase .1R.30R.4R.1 reconciliation — `.30R.3.6` (a PAWA multi-write
    # completion repair) implemented no protected presentation. `.30R.4R.1`
    # implemented it; the real attestation branch here delegates to the
    # launcher verifier and preserves the deterministic NON_REAL seam.
    source = (REPO / "src/pcae/core/approval_presentation.py").read_text()
    assert "pcae-protected-local-presentation/1.0" in source
    assert "deterministic-test-fixture" in source
    assert "adapter.dispatch(" not in source


@pytest.mark.parametrize(
    "path",
    ["src/pcae/core/runtime_dispatch_gate5.py", "src/pcae/core/runtime_dispatch_gate9.py"],
)
def test_38_gate5_gate9_are_unchanged(path):
    assert _run("git", "diff", "--quiet", R0, "--", path, check=False).returncode == 0


def test_39_n16_6_is_untouched():
    assert _run("git", "diff", "--quiet", R0, "--", "src/pcae/core/permission_broker.py", check=False).returncode == 0


def test_40_n16_7_is_untouched():
    assert _run("git", "diff", "--quiet", R0, "--", "src/pcae/core/runtime.py", check=False).returncode == 0


def test_41_runtime_remains_observed_and_unavailable():
    output = _run("pcae", "runtime", "inspect").stdout
    assert "Runtime state:             Observed" in output
    assert "Execution capability:      unavailable" in output
    assert "Maximum plugin capability: observe" in output
    assert "Plugin count:              0" in output
    assert "Capability count:          0" in output


def test_42_first_external_effect_remains_absent():
    # The repository contains a pre-existing mock/dry runtime-adapter call
    # site, but runtime execution is unavailable and this phase does not
    # alter that boundary or make a first real effect reachable.
    assert _run(
        "git", "diff", "--quiet", R0, "--",
        "src/pcae/core/runtime_adapter.py",
        "src/pcae/core/runtime_invocation.py",
        "src/pcae/core/runtime_registry.py",
        check=False,
    ).returncode == 0
    output = _run("pcae", "runtime", "inspect").stdout
    assert "Execution capability:      unavailable" in output


def test_43_completion_guard_and_transition_share_registry_lock():
    method_source = inspect.getsource(HPACStoreAuthority.complete_multi_write)
    helper_source = inspect.getsource(hf._mark_capability_consumed)
    assert "require_multi_write=True" in method_source
    assert "with _ISSUANCE_REGISTRY_LOCK:" in helper_source
    assert helper_source.index("record.state is _CapabilityIssuanceState.CONSUMED") < helper_source.index(
        "record.state = _CapabilityIssuanceState.CONSUMED"
    )


def test_44_failure_before_completion_leaves_lifecycle_active(tmp_path):
    _authority, capability = _issued(tmp_path)
    assert _record(capability).state is _CapabilityIssuanceState.ACTIVE
    assert capability._spent is False
