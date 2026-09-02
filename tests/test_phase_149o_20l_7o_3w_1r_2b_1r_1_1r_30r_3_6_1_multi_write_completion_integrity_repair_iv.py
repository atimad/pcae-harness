"""Independent verification of the .1R.30R.3.6 multi-write repair.

Verification only: this suite independently contrasts immutable .3.4 with
the finalized repair, challenges canonical issuance state and concurrency,
and proves that the repair did not widen the surrounding RHAMP/FIDO2/runtime
surface.
"""

from __future__ import annotations

import ast
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
    HPACAuthorityError,
    HPACStoreAuthority,
    HPACWriterCapability,
    _CapabilityIssuanceState,
    _PRODUCTION_TEST_FIXTURE_SEAL,
    canonical_digest,
    write_atomic_create_only,
)
from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
from pcae.core.hpac_rhamp_enrollment import RhampEnrollmentError, enroll_first_credential
from pcae.core.hpac_rhamp_terminal_reasons import TERMINAL_REASON_CODES
from pcae.core.human_principal_registry import new_principal_id

pytestmark = pytest.mark.fast_green

REPO = Path(__file__).resolve().parents[1]
A = "c9cf99d5150200c426ba708d87fbdb62e73d8e18"
B = "3968814ce1746299f4785462aa1e2e7c8e74af3b"
R = "e0f79220539c80eebfc52cc169a82a37f14b8f91"
V = R
ROLE = "human_principal_registry_admin"
SUBJECT = "txn-r361"
FAKE_AGENT_UID = 4_242_461
FAKE_AGENT_GID = 999_961
AGENT_ACCOUNT = "pcae-agent-svc-r361"


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True, check=check
    )


def _issued(tmp_path: Path, *, multi_write: bool = True):
    authority = HPACStoreAuthority.fixture(tmp_path / "authority")
    capability = authority._new_capability(
        ROLE, SUBJECT, single_use=True, multi_write=multi_write
    )
    record = hf._lookup_issued_capability(capability)
    assert record is not None
    return authority, capability, record


def _historical(script: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="pcae-r361-a-") as raw:
        tree = Path(raw) / "tree"
        _git("worktree", "add", "--detach", str(tree), A)
        try:
            return subprocess.run(
                [sys.executable, "-c", script],
                cwd=tree,
                env={**os.environ, "PYTHONPATH": str(tree / "src")},
                capture_output=True,
                text=True,
                check=True,
            )
        finally:
            _git("worktree", "remove", "--force", str(tree))


def _agent_source(symbolic_account, provisioned_uid):
    return provisioned_uid, frozenset({FAKE_AGENT_GID})


def _locked_probe():
    return w.TopologyProbe(
        effective_write_access=lambda path, uid, gids: (False, "fixture_locked", ()),
        ancestor_chain_safe=lambda start, uid, gids: (True, ("fixture_root_reached",)),
    )


def _provisioned_root(tmp_path: Path) -> Path:
    root = (tmp_path / "protected-root").resolve()
    w.provision_protected_root(
        protected_root=root, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID
    )
    return root


def test_01_immutable_a_b_r_v_are_independently_derived():
    log = _git("log", "--format=%H %s", "--all").stdout
    assert f"{A} Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4: reconcile" in log
    assert f"{B} Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.5: reconcile" in log
    assert f"{R} Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.6: stage" in log
    assert _git("rev-parse", V).stdout.strip() == V


def test_02_historical_sequential_defect_reproduces_at_a():
    result = _historical("""
from pathlib import Path
from tempfile import TemporaryDirectory
from pcae.core.hpac_foundation import HPACStoreAuthority
with TemporaryDirectory() as raw:
 a=HPACStoreAuthority.fixture(Path(raw)); c=a._new_capability('r','t',single_use=True,multi_write=True)
 a.complete_multi_write(c); a.complete_multi_write(c)
print('two-successes')
""")
    assert result.stdout.strip() == "two-successes"


def test_03_historical_eight_way_concurrent_defect_reproduces_at_a():
    result = _historical("""
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
from pcae.core.hpac_foundation import HPACStoreAuthority
with TemporaryDirectory() as raw:
 a=HPACStoreAuthority.fixture(Path(raw)); c=a._new_capability('r','t',single_use=True,multi_write=True); b=threading.Barrier(8); out=[]
 def f():
  b.wait()
  try: a.complete_multi_write(c); out.append('ok')
  except Exception: out.append('blocked')
 ts=[threading.Thread(target=f) for _ in range(8)]
 [t.start() for t in ts]; [t.join() for t in ts]
 print(out.count('ok'))
""")
    assert result.stdout.strip() == "8"


def test_04_current_first_completion_succeeds_and_consumes(tmp_path):
    authority, capability, record = _issued(tmp_path)
    authority.complete_multi_write(capability)
    assert capability._spent is True
    assert record.state is _CapabilityIssuanceState.CONSUMED


def test_05_current_second_completion_is_canonical_stale(tmp_path):
    authority, capability, _ = _issued(tmp_path)
    authority.complete_multi_write(capability)
    with pytest.raises(HPACAuthorityError, match="one-operation lifetime exhausted"):
        authority.complete_multi_write(capability)


def test_06_current_eight_way_completion_has_exactly_one_success(tmp_path):
    authority, capability, _ = _issued(tmp_path)
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
    assert results.count("writer capability is spent (one-operation lifetime exhausted)") == 7


def test_07_active_check_and_consumed_transition_share_one_lock():
    source = inspect.getsource(hf._mark_capability_consumed)
    critical = source[source.index("with _ISSUANCE_REGISTRY_LOCK:") :]
    assert critical.index("record.state is _CapabilityIssuanceState.CONSUMED") < critical.index(
        "record.state = _CapabilityIssuanceState.CONSUMED"
    )
    assert "capability._mark_spent" in critical


def test_08_completion_uses_canonical_registry_identity_and_scope():
    source = inspect.getsource(hf._mark_capability_consumed)
    for token in ("record.capability is not capability", "record.role", "record.subject", "record.authority_class"):
        assert token in source


def test_09_spent_reset_cannot_restore_consumed_authority(tmp_path):
    authority, capability, record = _issued(tmp_path)
    authority.complete_multi_write(capability)
    capability._spent = False
    assert record.state is _CapabilityIssuanceState.CONSUMED
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)


def test_10_object_spent_registry_active_inconsistency_fails_closed(tmp_path):
    authority, capability, record = _issued(tmp_path)
    capability._spent = True
    with pytest.raises(HPACAuthorityError, match="one-operation lifetime exhausted"):
        authority.complete_multi_write(capability)
    assert record.state is _CapabilityIssuanceState.ACTIVE


def test_11_non_issued_reconstruction_is_rejected(tmp_path):
    authority, capability, _ = _issued(tmp_path)
    shell = HPACWriterCapability.__new__(HPACWriterCapability)
    for slot in HPACWriterCapability.__slots__:
        setattr(shell, slot, getattr(capability, slot))
    with pytest.raises(HPACAuthorityError, match="absent, forged"):
        authority.complete_multi_write(shell)


def test_12_fixture_capability_cannot_complete_on_production_authority(tmp_path):
    root = _provisioned_root(tmp_path)
    production = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    fixture, capability, _ = _issued(tmp_path / "fixture")
    assert fixture.authority_class is not production.authority_class
    with pytest.raises(HPACAuthorityError):
        production.complete_multi_write(capability)


def test_13_ordinary_non_multi_write_capability_is_rejected_without_consumption(tmp_path):
    authority, capability, record = _issued(tmp_path, multi_write=False)
    with pytest.raises(HPACAuthorityError, match="only valid for a multi-write"):
        authority.complete_multi_write(capability)
    assert record.state is _CapabilityIssuanceState.ACTIVE


def test_14_wrong_principal_scope_is_rejected(tmp_path):
    authority, capability, record = _issued(tmp_path)
    capability.subject = "hp-wrong-principal"
    with pytest.raises(HPACAuthorityError, match="canonical issuance"):
        authority.complete_multi_write(capability)
    assert record.state is _CapabilityIssuanceState.ACTIVE


def test_15_wrong_transaction_scope_is_rejected(tmp_path):
    authority, capability, record = _issued(tmp_path)
    capability.subject = "txn-wrong"
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)
    assert record.state is _CapabilityIssuanceState.ACTIVE


def test_16_wrong_mutation_class_is_rejected(tmp_path):
    authority, capability, record = _issued(tmp_path, multi_write=False)
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)
    assert record.state is _CapabilityIssuanceState.ACTIVE


def test_17_wrong_role_is_rejected(tmp_path):
    authority, capability, record = _issued(tmp_path)
    capability.role = "wrong-role"
    with pytest.raises(HPACAuthorityError, match="canonical issuance"):
        authority.complete_multi_write(capability)
    assert record.state is _CapabilityIssuanceState.ACTIVE


def test_18_invalid_call_does_not_corrupt_valid_lifecycle(tmp_path):
    authority, capability, record = _issued(tmp_path)
    capability.role = "wrong"
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(capability)
    capability.role = ROLE
    authority.complete_multi_write(capability)
    assert record.state is _CapabilityIssuanceState.CONSUMED


def test_19_bounded_component_writes_remain_possible_before_completion(tmp_path):
    authority, capability, record = _issued(tmp_path)
    authority._ensure_root(create=True)
    for name in ("a.json", "b.json"):
        path = authority.root / name
        write_atomic_create_only(path, b"{}")
        authority.record_write(path, canonical_digest({}), capability, role=ROLE, subject=SUBJECT)
    assert record.state is _CapabilityIssuanceState.ACTIVE


def test_20_completion_is_terminal_after_component_writes(tmp_path):
    authority, capability, record = _issued(tmp_path)
    authority._ensure_root(create=True)
    path = authority.root / "component.json"
    write_atomic_create_only(path, b"{}")
    authority.record_write(path, canonical_digest({}), capability, role=ROLE, subject=SUBJECT)
    authority.complete_multi_write(capability)
    assert record.state is _CapabilityIssuanceState.CONSUMED


def test_21_post_completion_component_write_is_rejected(tmp_path):
    authority, capability, _ = _issued(tmp_path)
    authority._ensure_root(create=True)
    authority.complete_multi_write(capability)
    path = authority.root / "late.json"
    write_atomic_create_only(path, b"{}")
    with pytest.raises(HPACAuthorityError):
        authority.record_write(path, canonical_digest({}), capability, role=ROLE, subject=SUBJECT)


def test_22_failed_enrollment_before_writes_never_calls_completion(tmp_path, monkeypatch):
    root = _provisioned_root(tmp_path)
    principal_id = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=principal_id,
        enrollment_provenance_ref="r361-partial",
        _protected_root=root,
        _configured_agent_identity_source=_agent_source,
        _topology_probe=_locked_probe(),
    )
    calls = 0
    original = HPACStoreAuthority.complete_multi_write

    def counted(self, writer):
        nonlocal calls
        calls += 1
        return original(self, writer)

    monkeypatch.setattr(HPACStoreAuthority, "complete_multi_write", counted)
    provider = DeterministicCtap2Provider()
    original_make = provider.make_credential

    def invalid_make(**kwargs):
        result = original_make(**kwargs)
        return result.__class__(**{**result.__dict__, "uv": False})

    monkeypatch.setattr(provider, "make_credential", invalid_make)
    with pytest.raises(RhampEnrollmentError):
        enroll_first_credential(
            principal_id=principal_id,
            subject_digest="a" * 64,
            presentation_digest="b" * 64,
            invocation_id="iv-r361-partial",
            attempt_id="at-r361-partial",
            provider=provider,
            protected_root=root,
            _configured_agent_identity_source=_agent_source,
            _topology_probe=_locked_probe(),
        )
    assert calls == 0


def test_23_docstring_matches_reentry_rejection():
    doc = inspect.getdoc(HPACStoreAuthority.complete_multi_write) or ""
    assert "exactly once" in doc and "second call" in doc and "fails closed" in doc


def test_24_existing_failure_vocabularies_are_reused():
    assert "capability_stale" in w.PAWA_FAILURE_CODES and len(w.PAWA_FAILURE_CODES) == 21
    assert len(TERMINAL_REASON_CODES) == 41


def test_25_capability_shape_has_no_r36_expansion():
    assert HPACWriterCapability.__slots__ == (
        "_authority_seal", "role", "subject", "authority_class", "_single_use", "_spent", "_multi_write"
    )


def test_26_issuance_registry_shape_is_single_and_unchanged():
    assert hf._CapabilityIssuanceRecord.__slots__ == (
        "capability", "issuance_id", "role", "subject", "authority_class", "state"
    )
    source = (REPO / "src/pcae/core/hpac_foundation.py").read_text()
    assert source.count("_ISSUED_CAPABILITY_REGISTRY:") == 1


def test_27_b_to_r_production_diff_is_exactly_hpac_foundation():
    out = _git("diff", "--name-status", B, R, "--", "src/pcae", "scripts", "pyproject.toml").stdout.strip()
    assert out == "M\tsrc/pcae/core/hpac_foundation.py"


def test_28_normative_contracts_are_byte_identical_b_to_r():
    assert _git("diff", "--quiet", B, R, "--", "docs/contracts", check=False).returncode == 0


def test_29_credential_record_is_byte_identical_b_to_r():
    path = "src/pcae/core/human_principal_registry.py"
    assert _git("diff", "--quiet", B, R, "--", path, check=False).returncode == 0


def test_30_historical_r35_blocked_report_is_byte_identical_b_to_r():
    path = "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_5_N_16_5_MERGED_RHAMP_INDEPENDENT_VERIFICATION.md"
    assert _git("diff", "--quiet", B, R, "--", path, check=False).returncode == 0


def test_31_exact_two_r35_blocking_nodes_retain_security_expectations():
    path = REPO / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_5_merged_rhamp_iv.py"
    source = path.read_text()
    assert "def test_11_multi_write_replay_after_complete_rejected" in source
    assert "def test_14_multi_write_concurrent_complete_only_one_wins" in source
    assert "results.count(\"ok\") == 1" in source


def test_32_permanent_product_regression_is_present():
    source = (REPO / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py").read_text()
    assert "def test_99_multi_write_completion_is_single_success_per_canonical_issuance" in source
    assert "one-operation lifetime exhausted" in source


def test_33_r36_repair_suite_is_present_and_unchanged_since_r():
    path = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_6_multi_write_completion_integrity_repair.py"
    assert _git("diff", "--quiet", R, "--", path, check=False).returncode == 0


def test_34_r34_product_suite_is_unchanged_since_r():
    path = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py"
    assert _git("diff", "--quiet", R, "--", path, check=False).returncode == 0


def test_35_pawa_integrity_suites_are_unchanged_since_r():
    paths = [
        "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1.py",
        "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_2_1_pawa_writer_capability_integrity_repair.py",
        "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_2_1_1_writer_capability_integrity_iv.py",
    ]
    assert _git("diff", "--quiet", R, "--", *paths, check=False).returncode == 0


def test_36_normal_rhamp_enrollment_completes_exactly_once(tmp_path, monkeypatch):
    root = _provisioned_root(tmp_path)
    principal_id = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=principal_id,
        enrollment_provenance_ref="r361-normal",
        _protected_root=root,
        _configured_agent_identity_source=_agent_source,
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
        subject_digest="c" * 64,
        presentation_digest="d" * 64,
        invocation_id="iv-r361",
        attempt_id="at-r361",
        provider=DeterministicCtap2Provider(),
        protected_root=root,
        _configured_agent_identity_source=_agent_source,
        _topology_probe=_locked_probe(),
    )
    assert result.principal_id == principal_id and calls == 1


def test_37_counter_store_source_is_unchanged_b_to_r():
    assert _git("diff", "--quiet", B, R, "--", "src/pcae/core/hpac_rhamp_counter_state.py", check=False).returncode == 0


def test_38_fido2_authentication_sources_are_unchanged_b_to_r():
    paths = ["src/pcae/core/human_authenticator_fido2.py", "src/pcae/core/hpac_rhamp_assertion_verify.py"]
    assert _git("diff", "--quiet", B, R, "--", *paths, check=False).returncode == 0


def test_39_hpac_verifier_real_branch_is_unchanged_b_to_r():
    assert _git("diff", "--quiet", B, R, "--", "src/pcae/core/hpac_verifier.py", check=False).returncode == 0


def test_40_deterministic_ci_seam_is_unchanged_b_to_r():
    assert _git("diff", "--quiet", B, R, "--", "src/pcae/core/hpac_rhamp_ctap2.py", check=False).returncode == 0


def test_41_protected_presentation_fence_is_unchanged():
    source = (REPO / "src/pcae/core/approval_presentation.py").read_text()
    assert "pcae-protected-local-presentation/1.0" not in source
    assert _git("diff", "--quiet", B, R, "--", "src/pcae/core/approval_presentation.py", check=False).returncode == 0


def test_42_gate5_is_byte_identical_b_to_r():
    assert _git("diff", "--quiet", B, R, "--", "src/pcae/core/runtime_dispatch_gate5.py", check=False).returncode == 0


def test_43_gate9_is_byte_identical_b_to_r():
    assert _git("diff", "--quiet", B, R, "--", "src/pcae/core/runtime_dispatch_gate9.py", check=False).returncode == 0


def test_44_no_test_weakening_in_repair_window_or_this_iv():
    diff = _git("diff", B, R, "--", "tests").stdout
    assert not any(line.startswith("-def test_") for line in diff.splitlines())
    assert not any(line.startswith("+@pytest.mark.skip") or line.startswith("+@pytest.mark.xfail") for line in diff.splitlines())
    tree = ast.parse(Path(__file__).read_text())
    decorators = " ".join(ast.dump(dec) for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) for dec in node.decorator_list)
    assert "skip" not in decorators and "xfail" not in decorators


def test_45_runtime_remains_observed_observe_unavailable():
    output = subprocess.run(["pcae", "runtime", "inspect"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    for expected in (
        "Runtime state:             Observed",
        "Execution capability:      unavailable",
        "Maximum plugin capability: observe",
        "Plugin count:              0",
        "Capability count:          0",
    ):
        assert expected in output


def test_46_first_external_effect_remains_absent_and_unreachable():
    paths = ["src/pcae/core/runtime_adapter.py", "src/pcae/core/runtime_invocation.py", "src/pcae/core/runtime_registry.py"]
    assert _git("diff", "--quiet", B, R, "--", *paths, check=False).returncode == 0
    output = subprocess.run(["pcae", "runtime", "inspect"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    assert "Execution capability:      unavailable" in output
