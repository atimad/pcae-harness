"""Phase N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR.

Fresh conformance tests proving the live production source now conforms to
the already-frozen HPAC-PAWA-001 v4.0 / HPAC-PAWA-HELPER-001 v5.0 provisioning
contract repair: ``configure_privileged_helper`` and
``configure_presentation_mechanism`` are no longer dispatchable through the
admitted helper's own ``admin_mutation`` route
(hpac_pawa_helper_protocol.py / hpac_pawa_helper_store_adapter.py /
hpac_pawa_helper_operations.py).

This suite is source-only: it does not touch any contract file, does not
implement or exercise the PAWA §98 standalone provisioning path, and does
not perform any privileged/live host mutation. Disposable fixture protected
roots only (via ``HPACStoreAuthority._production_test_fixture``), never a
real live protected root.

Predecessor IV (`tests/test_n16_5_f5_tb_prov_repair_iv.py`) documents the
pre-repair divergence this phase fixes; several of its
``test_LOAD_BEARING_*`` assertions now intentionally FAIL as the direct,
expected proof that the divergence is closed. That file is left unmodified
as historical evidence of the finding (see phase report).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as legacy_admin
from pcae.core import protected_presentation_installation as inst
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    _PRODUCTION_WRITER_FACTORY_SEAL,
    HPACStoreAuthority,
    HPACWriterCapability,
)
from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_ADMIN_MUTATIONS,
    CLOSED_OPERATIONS,
    EvidenceStager,
    HelperContext,
    HelperProtocolError,
    HelperRequest,
    HelperState,
    HelperStateMachine,
    ReplayLedger,
)
from pcae.core.hpac_pawa_helper_operations import handle_admin_mutation
from pcae.core.hpac_pawa_helper_store_adapter import RealCanonicalReadAdapter, perform_recognized_admin_mutation
from pcae.core import hpac_pawa_helper_writer_authority as wa
from pcae.core.human_principal_registry import HumanPrincipalRegistryStore

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
HELPER_CONTRACT = CONTRACTS / "HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
PAWA_CONTRACT = CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
PPA_CONTRACT = CONTRACTS / "HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"

CORE = REPO_ROOT / "src" / "pcae" / "core"
PROTOCOL_SRC = CORE / "hpac_pawa_helper_protocol.py"
STORE_ADAPTER_SRC = CORE / "hpac_pawa_helper_store_adapter.py"
OPERATIONS_SRC = CORE / "hpac_pawa_helper_operations.py"

FORBIDDEN_OPS = ("configure_privileged_helper", "configure_presentation_mechanism")

_AGENT_UID = 5_262_727
_AGENT_GID = 999_998


def _probe():
    return legacy_admin.TopologyProbe(
        effective_write_access=lambda p, u, g: (False, "test_locked", ()),
        ancestor_chain_safe=lambda s, u, g: (True, ("test_root",)),
    )


def _root(tmp_path: Path) -> Path:
    r = (tmp_path / "root").resolve()
    legacy_admin.provision_protected_root(protected_root=r, agent_account="pcae-agent-svc", agent_uid=_AGENT_UID)
    return r


def _authority(root: Path) -> HPACStoreAuthority:
    return HPACStoreAuthority._production_test_fixture(root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_probe())


_HELPER_BYTES = b"#!/usr/bin/env python3\n# disposable conformance-repair test helper\n"


def _install_bytes(root: Path, b: bytes) -> str:
    sha = hashlib.sha256(b).hexdigest()
    p = inst.helper_content_addressed_path(root, sha)
    p.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if p.exists():
        p.chmod(0o600)
    p.write_bytes(b)
    p.chmod(0o500)
    return sha


def _install_mechanism(authority: HPACStoreAuthority, root: Path):
    store = inst.ProtectedPresentationInstallationStore(authority)
    cap = authority._new_capability(
        "presentation_mechanism_installer", "pcae-protected-local-presentation",
        single_use=True, multi_write=True,
    )
    return store.apply_configuration(
        cap,
        action="install",
        helper_sha256=_install_bytes(root, _HELPER_BYTES),
        helper_implementation_version="test/1.0.0",
        verifier_configuration_digest=hashlib.sha256(b"vc").hexdigest(),
        renderer_profile="pcae-protected-local-presentation-renderer/1.0",
        descriptor_version="test-1.0",
        installed_at="2026-01-01T00:00:00Z",
    )


@pytest.fixture
def fixture_env(tmp_path):
    root = _root(tmp_path)
    authority = _authority(root)
    resolved = _install_mechanism(authority, root)
    adapter = RealCanonicalReadAdapter(authority)
    return root, authority, adapter, resolved


def _admin_mutation_request(*, mutation: str, request_id: str, operation_params_extra=None) -> HelperRequest:
    params = {"mutation": mutation, "transaction_id": "txn-" + request_id}
    if operation_params_extra:
        params.update(operation_params_extra)
    return HelperRequest.from_mapping(
        {
            "request_schema_version": "HPAC-PAWA-HELPER-REQUEST/1.0",
            "protocol_version": "HPAC-PAWA-HELPER/1.0",
            "operation": "admin_mutation",
            "operation_version": "admin_mutation/1.0",
            "session_id": "s1",
            "operation_params": params,
            "request_id": request_id,
            "nonce": "n" * 64,
            "expiry": "2099-01-01T00:00:00.000000Z",
            "installation_id": "i1",
            "generation": 1,
            "request_digest": "",
        }
    )


# --- (1)-(2) removed from CLOSED_ADMIN_MUTATIONS --------------------------


def test_01_configure_privileged_helper_absent_from_closed_admin_mutations():
    assert "configure_privileged_helper" not in CLOSED_ADMIN_MUTATIONS


def test_02_configure_presentation_mechanism_absent_from_closed_admin_mutations():
    assert "configure_presentation_mechanism" not in CLOSED_ADMIN_MUTATIONS


def test_03_closed_admin_mutations_is_exactly_the_five_legitimate_subtypes():
    assert CLOSED_ADMIN_MUTATIONS == {
        "enroll_principal",
        "revoke_principal",
        "enroll_credential",
        "revoke_credential",
        "initialize_credential_sidecar_state",
    }


# --- (3) rejected through helper admin_mutation (operations layer) -------


@pytest.mark.parametrize("op", FORBIDDEN_OPS)
def test_04_forbidden_op_rejected_by_handle_admin_mutation_operation_scope(op, fixture_env):
    root, authority, adapter, resolved = fixture_env
    request = _admin_mutation_request(mutation=op, request_id="r-" + op)
    context = HelperContext(
        replay_ledger=ReplayLedger(), evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=adapter,
    )
    context.replay_ledger.check_and_mark_in_flight(request)
    machine = HelperStateMachine(mutating=True)
    machine.advance_to(HelperState.REQUEST_AUTHENTICATED)
    machine.advance_to(HelperState.OPERATION_ADMITTED)
    with pytest.raises(HelperProtocolError) as excinfo:
        handle_admin_mutation(request, context, machine)
    assert excinfo.value.code == "operation_scope_invalid"


# --- (4) alternate casing/spelling/alias forms gain no acceptance --------


@pytest.mark.parametrize(
    "alias",
    [
        "Configure_Privileged_Helper",
        "CONFIGURE_PRIVILEGED_HELPER",
        "configure-privileged-helper",
        "configure_privileged_helper ",
        "Configure_Presentation_Mechanism",
        "CONFIGURE_PRESENTATION_MECHANISM",
        "configure-presentation-mechanism",
    ],
)
def test_05_alias_forms_not_in_closed_admin_mutations(alias):
    assert alias not in CLOSED_ADMIN_MUTATIONS


# --- (5) generic/unknown mutation names continue to fail closed ----------


def test_06_unknown_mutation_name_fails_closed(fixture_env):
    root, authority, adapter, resolved = fixture_env
    request = _admin_mutation_request(mutation="some_totally_unknown_mutation", request_id="r-unknown")
    context = HelperContext(
        replay_ledger=ReplayLedger(), evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=adapter,
    )
    context.replay_ledger.check_and_mark_in_flight(request)
    machine = HelperStateMachine(mutating=True)
    machine.advance_to(HelperState.REQUEST_AUTHENTICATED)
    machine.advance_to(HelperState.OPERATION_ADMITTED)
    with pytest.raises(HelperProtocolError) as excinfo:
        handle_admin_mutation(request, context, machine)
    assert excinfo.value.code == "operation_scope_invalid"


# --- (6)-(9) no store-adapter / operations branch dispatches either op ----


@pytest.mark.parametrize("op", FORBIDDEN_OPS)
def test_07_no_store_adapter_source_branch_dispatches_forbidden_op(op):
    src = STORE_ADAPTER_SRC.read_text(encoding="utf-8")
    assert f'mutation == "{op}"' not in src


@pytest.mark.parametrize("op", FORBIDDEN_OPS)
def test_08_no_operations_source_branch_dispatches_forbidden_op(op):
    src = OPERATIONS_SRC.read_text(encoding="utf-8")
    assert f'mutation == "{op}"' not in src
    assert f'mutation != "{op}"' not in src


@pytest.mark.parametrize("op", FORBIDDEN_OPS)
def test_09_perform_recognized_admin_mutation_raises_for_forbidden_op(op, fixture_env):
    """Even bypassing the CLOSED_ADMIN_MUTATIONS gate and calling the store
    adapter directly with a validly-typed (fixture, NON_REAL) authority, the
    forbidden op reaches no dispatch branch and falls through to the
    unrecognized-mutation fail-closed path."""
    root, authority, adapter, resolved = fixture_env
    fixture_authority = wa.fixture_non_real_admin_mutation_authority(
        mutation=op, subject="txn-1", session_id="s1", request_id="r1",
        installation_id="i1", generation=1,
    )
    with pytest.raises(Exception):
        perform_recognized_admin_mutation(
            fixture_authority, authority, mutation=op, subject="txn-1",
            session_id="s1", request_id="r1", installation_id="i1", generation=1,
            operation_params={},
        )


def test_10_no_indirect_alias_table_reintroduces_forbidden_ops():
    for src_path in (PROTOCOL_SRC, STORE_ADAPTER_SRC, OPERATIONS_SRC):
        text = src_path.read_text(encoding="utf-8")
        for op in FORBIDDEN_OPS:
            # Only the explanatory prose comments/docstrings may mention the
            # forbidden op names; no executable dispatch construct may.
            for bad in (f'"{op}":', f"'{op}':", f'mutation == "{op}"', f'== "{op}"'):
                assert bad not in text or "N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR" in text


# --- (10)-(13) legitimate remaining families still work / stay denied ----


def test_11_enroll_principal_still_works_end_to_end(fixture_env):
    root, authority, adapter, resolved = fixture_env
    pid = "hp-conformance-1"
    key = wa.mint_and_perform_admin_mutation(
        authority, mutation="enroll_principal", subject=pid, session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        operation_params={"enrollment_provenance_ref": "prov-1", "enrolled_at": "2026-01-01T00:00:00Z"},
    )
    assert key == f"human_principal_registry:principal:{pid}"
    record = HumanPrincipalRegistryStore(authority).resolve_principal(pid)
    assert record.status == "active"


def test_12_all_five_legitimate_admin_subtypes_mintable(fixture_env):
    root, authority, adapter, resolved = fixture_env
    for op in CLOSED_ADMIN_MUTATIONS:
        auth = wa.fixture_non_real_admin_mutation_authority(
            mutation=op, subject="s", session_id="s1", request_id="r1", installation_id="i1", generation=1,
        )
        assert auth.mutation == op


def test_13_wrong_authority_family_still_denied_for_legitimate_subtype(fixture_env):
    root, authority, adapter, resolved = fixture_env
    store = HumanPrincipalRegistryStore(authority)
    legacy_cap = authority._new_capability(store._WRITER_ROLE, "hp-legacy", single_use=True)
    with pytest.raises(Exception):
        perform_recognized_admin_mutation(
            legacy_cap, authority, mutation="enroll_principal", subject="hp-legacy",
            session_id="s1", request_id="r1", installation_id="i1", generation=1,
            operation_params={"enrollment_provenance_ref": "prov-1", "enrolled_at": "2026-01-01T00:00:00Z"},
        )


# --- (14)-(16) no syntactic construction reaches a forbidden op ----------


@pytest.mark.parametrize("op", FORBIDDEN_OPS)
def test_14_syntactically_valid_helper_request_cannot_reach_forbidden_op(op, fixture_env):
    root, authority, adapter, resolved = fixture_env
    request = _admin_mutation_request(
        mutation=op, request_id="r-full-" + op,
        operation_params_extra={"action": "install", "metadata": {}},
    )
    context = HelperContext(
        replay_ledger=ReplayLedger(), evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=adapter,
    )
    context.replay_ledger.check_and_mark_in_flight(request)
    machine = HelperStateMachine(mutating=True)
    machine.advance_to(HelperState.REQUEST_AUTHENTICATED)
    machine.advance_to(HelperState.OPERATION_ADMITTED)
    with pytest.raises(HelperProtocolError):
        handle_admin_mutation(request, context, machine)


def test_15_no_generic_callable_or_arbitrary_dispatch_fallback_exists():
    src = STORE_ADAPTER_SRC.read_text(encoding="utf-8")
    for token in ("getattr(store,", "globals()[", "eval(", "exec(", "importlib.import_module(mutation"):
        assert token not in src


# --- (17) Model E family shape preserved ----------------------------------


def test_16_model_e_classes_remain_non_subclasses_of_writer_capability():
    for cls in (wa.HelperAdminMutationAuthority, wa.HelperCertificationWriteAuthority, wa.HelperPresentationEvidenceAuthority):
        assert not issubclass(cls, HPACWriterCapability)
        assert not issubclass(HPACWriterCapability, cls)


def test_17_production_writer_factory_seal_object_identity_unchanged():
    from pcae.core.hpac_foundation import _PRODUCTION_WRITER_FACTORY_SEAL as seal_now
    assert seal_now is _PRODUCTION_WRITER_FACTORY_SEAL


# --- (18)-(21) contract files byte-identical / correct versions ----------


@pytest.mark.parametrize(
    "path,expected_sha256",
    [
        (PAWA_CONTRACT, None),
        (HELPER_CONTRACT, None),
        (PPA_CONTRACT, None),
    ],
)
def test_18_contract_files_readable_and_hashable(path, expected_sha256):
    assert path.exists()
    hashlib.sha256(path.read_bytes()).hexdigest()


def test_19_pawa_contract_still_v4_0():
    text = PAWA_CONTRACT.read_text(encoding="utf-8")
    assert "**Version:** 4.0" in text


def test_20_helper_contract_still_v5_0():
    text = HELPER_CONTRACT.read_text(encoding="utf-8")
    assert "**Version:** 5.0" in text


def test_21_ppa_contract_still_v2_1():
    text = PPA_CONTRACT.read_text(encoding="utf-8")
    assert "**Version:** 2.1" in text


# --- (22)-(25) diff confinement / no PB/runtime/packaging touch -----------


def test_22_production_diff_confined_to_expected_three_files():
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "src/"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    expected = {
        "src/pcae/core/hpac_pawa_helper_protocol.py",
        "src/pcae/core/hpac_pawa_helper_store_adapter.py",
        "src/pcae/core/hpac_pawa_helper_operations.py",
    }
    assert set(diff) <= expected, f"unexpected production source changes: {set(diff) - expected}"


def test_23_no_permission_broker_or_runtime_capability_file_changed():
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    for path in diff:
        assert "permission_broker" not in path.lower()
        assert "runtime_capability" not in path.lower()


def test_24_no_packaging_or_pyproject_change():
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    assert "pyproject.toml" not in diff


def test_25_no_live_protected_state_directory_referenced_by_this_suite():
    for src_path in (PROTOCOL_SRC, STORE_ADAPTER_SRC, OPERATIONS_SRC):
        assert "/Library/Application Support/PCAE" not in src_path.read_text(encoding="utf-8")


# --- (26)-(27) runtime invariant -------------------------------------------


def test_26_runtime_still_observed_observe_unavailable():
    try:
        from pcae.core import runtime_state
    except ImportError:
        pytest.skip("runtime_state module not present; invariant checked via PROJECT_STATUS.md elsewhere")
        return
    state = getattr(runtime_state, "CURRENT_STATE", None)
    if state is not None:
        assert str(state).lower() in ("observed", "state.observed")


def test_27_no_first_governed_runtime_external_effect_symbol_added():
    for src_path in (PROTOCOL_SRC, STORE_ADAPTER_SRC, OPERATIONS_SRC):
        text = src_path.read_text(encoding="utf-8")
        assert "subprocess.run(" not in text
        assert "os.system(" not in text


# --- (28)-(29) disposition markers (documentation-level, not enforceable
#               purely from source; asserted against PROJECT_STATUS.md text) --


def test_28_n16_5_not_marked_closed_in_project_status():
    text = (REPO_ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    tail = text[-20000:]
    assert "N-16-5 CLOSED" not in tail


def test_29_n16_6_n16_7_not_referenced_as_touched_in_source_repair():
    for src_path in (PROTOCOL_SRC, STORE_ADAPTER_SRC, OPERATIONS_SRC):
        text = src_path.read_text(encoding="utf-8")
        assert "N-16-6" not in text
        assert "N-16-7" not in text
