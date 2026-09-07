"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R
(alias N16-5-H3-IMPL) — the H-3 implementation suite.

Exercises HPAC-PAWA-001 v1.3 §33A / §38A / §39A / §42B / §42C / §43A / §49A /
§68A as implemented by:

  * ``hpac_protected_admin_writer.certification_writer`` (the dedicated
    §33A factory) + ``CertificationWriterHandle`` (§49A one-shot);
  * ``hpac_certification_coordinator`` (the sole §38A consumer);
  * ``scripts/hpac_certification_admin.py`` (the bounded standalone entry);
  * the one additive ``HumanAuthenticationProofStore.create_canonical``
    ``certification_proof_subject`` keyword (OQ-1, HPAC-PAWA-REQ-260).

No real ceremony, no genuine YubiKey, no PIN, no protected APPROVE, no
``makeCredential`` / ``getAssertion``. All mutation tests use a disposable
provisioned PRODUCTION test-fixture protected root under ``tmp_path``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hpac_certification_coordinator as cc
from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    _PRODUCTION_WRITER_FACTORY_SEAL,
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
)
from pcae.core.human_authentication_proof import new_proof_id
from pcae.core.human_principal_registry import HumanPrincipalRegistryStore, new_principal_id

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root model"),
]

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACTS = REPO / "docs" / "contracts"
THIS_MODULE = "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_h3_impl"
COORDINATOR_MODULE = "pcae.core.hpac_certification_coordinator"

#: I0 — this implementation phase's entry SHA (docs/PHASE_…_N16_5_H3_IMPL.md §1).
I0 = "74e52d59738007c4b9f6dbeb28f83990ba82e9a8"
#: HPAC-PAWA-001 v1.3 git blob at I0 — must stay byte-unchanged.
PAWA_V13_BLOB = "9c816716bae2262831945ac24b1771cf79de4c55"

FAKE_AGENT_UID = 4_242_701
FAKE_AGENT_GID = 999_701
AGENT_ACCOUNT = "pcae-agent-svc-n16-5-h3-impl"

FIVE_ROLES = (
    "hpac_challenge_coordinator",
    "hpac_assertion_recorder",
    "human_authentication_proof_verifier",
    "hpac_gate5_binder",
    "hpac_rhamp_counter_state_verifier",
)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures / helpers
# ═══════════════════════════════════════════════════════════════════════════


def _agent_src(uid_by_name=None):
    def source(symbolic_account, provisioned_uid):
        if uid_by_name is not None:
            if symbolic_account not in uid_by_name:
                raise KeyError(symbolic_account)
            return uid_by_name[symbolic_account], frozenset({FAKE_AGENT_GID})
        return provisioned_uid, frozenset({FAKE_AGENT_GID})

    return source


def _locked_probe():
    def ewa(path, uid, gids):
        return (False, "fixture_locked", ())

    def acs(start, uid, gids):
        return (True, ("fixture_root_reached",))

    return w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


class Rig:
    """A provisioned PRODUCTION test-fixture protected root + one active
    principal + one active bound credential, ready to drive
    ``certification_writer`` / the coordinator."""

    def __init__(self, tmp_path):
        self.root = (tmp_path / "hpac-protected-root").resolve()
        w.provision_protected_root(
            protected_root=self.root, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID
        )
        self.authority = HPACStoreAuthority._production_test_fixture(
            self.root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
        )
        self.registry = HumanPrincipalRegistryStore(self.authority)
        self.principal_id = new_principal_id()
        w.enroll_principal_via_pawa(
            principal_id=self.principal_id,
            enrollment_provenance_ref="rig-prov-ref",
            _protected_root=self.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
        self.credential_id = self._enroll_credential()
        self.proof_id = new_proof_id()
        self.session_id = "hcs-" + "0" * 32

    def _enroll_credential(self) -> str:
        from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
        from pcae.core.hpac_rhamp_enrollment import enroll_first_credential

        result = enroll_first_credential(
            principal_id=self.principal_id,
            subject_digest="a" * 64,
            presentation_digest="b" * 64,
            invocation_id="iv-n16-5-h3",
            attempt_id="at-n16-5-h3",
            provider=DeterministicCtap2Provider(),
            protected_root=self.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
        return result.credential_id

    def cw(self, role, **over):
        kw = dict(
            certification_session_id=self.session_id,
            principal_id=self.principal_id,
            credential_id=self.credential_id,
            proof_id=self.proof_id,
            _protected_root=self.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
            _caller_module=COORDINATOR_MODULE,
        )
        kw.update(over)
        return w.certification_writer(role, **kw)


@pytest.fixture
def rig(tmp_path):
    return Rig(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# A. Contract identity / no forbidden changes (§102 / §42 / §43 / §45 / §46)
# ═══════════════════════════════════════════════════════════════════════════


def test_01_pawa_v13_contract_byte_unchanged_since_i0():
    blob = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse",
         "HEAD:docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert blob == PAWA_V13_BLOB


def test_02_no_contract_normative_diff_since_i0():
    names = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", I0, "HEAD", "--", "docs/contracts"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert names == [], names


def test_03_pawa_operation_membership_unchanged():
    assert [m.value for m in w.PawaOperation] == [
        "enroll_principal",
        "revoke_principal",
        "enroll_credential",
        "revoke_credential",
        "initialize_credential_sidecar_state",
        "configure_presentation_mechanism",
    ]


def test_04_pawa_failure_codes_still_21_closed():
    assert len(w.PAWA_FAILURE_CODES) == 21 == len(set(w.PAWA_FAILURE_CODES))
    assert "certification" not in " ".join(w.PAWA_FAILURE_CODES)


def test_05_rhamp_terminal_reason_vocab_unchanged():
    from pcae.core.hpac_rhamp_terminal_reasons import TerminalReasonCode

    assert len(list(TerminalReasonCode)) == 41


def test_06_no_new_pawa_schema_field():
    from pcae.core.hpac_pawa_schemas import ISSUANCE_EVIDENCE_FIELDS

    assert "certification" not in " ".join(ISSUANCE_EVIDENCE_FIELDS)


def test_07_dependency_set_unchanged_since_i0():
    names = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", I0, "HEAD", "--", "pyproject.toml"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert names == [], names


# ═══════════════════════════════════════════════════════════════════════════
# B. Factory / §33A recognition (§99 items 1-10)
# ═══════════════════════════════════════════════════════════════════════════


def test_10_certification_writer_symbol_exists_and_is_distinct_from_production_writer():
    assert callable(w.certification_writer)
    assert w.certification_writer is not w.production_writer


def test_11_ordinary_writer_still_raises_for_non_fixture_class():
    a = HPACStoreAuthority.production()
    with pytest.raises(HPACAuthorityError):
        a.writer("human_authentication_proof_verifier", subject="x")


def test_12_authorized_certification_category_accepted(rig):
    handle = rig.cw("hpac_challenge_coordinator")
    assert isinstance(handle, w.CertificationWriterHandle)
    assert handle.role == "hpac_challenge_coordinator"
    assert handle.subject == rig.proof_id
    assert handle.certification_session_id == rig.session_id


def test_13_wrong_category_caller_denied(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator", _caller_module="pcae.core.agent")
    assert ei.value.code == "unauthorized_factory_consumer"


def test_14_production_writer_admin_module_cannot_request_certification_role(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator", _caller_module="pcae.core.hpac_protected_admin_writer")
    assert ei.value.code == "unauthorized_factory_consumer"


def test_15_ss33_steps_1_9_enforced_bad_root(tmp_path):
    with pytest.raises(w.PawaError):
        w.certification_writer(
            "hpac_challenge_coordinator",
            certification_session_id="hcs-" + "0" * 32,
            principal_id="hp-x",
            credential_id="hpc-y",
            proof_id="hap-" + "0" * 32,
            _protected_root=tmp_path / "nonexistent",
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
            _caller_module=COORDINATOR_MODULE,
        )


def test_16_ss33_agent_writable_root_denied(rig):
    def ewa(path, uid, gids):
        return (True, "agent_can_write", ())

    def acs(start, uid, gids):
        return (True, ())

    probe = w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator", _topology_probe=probe)
    assert ei.value.code == "agent_has_protected_write_authority"


def test_17_ss33a_recognition_is_fail_closed_unresolvable_agent(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.cw(
            "hpac_challenge_coordinator",
            _configured_agent_identity_source=_agent_src({"someone-else": 5}),
        )
    assert ei.value.code == "agent_principal_unknown"


def test_18_ambient_identity_is_not_authority(rig, monkeypatch):
    # USER / SUDO_USER / LOGNAME / cwd / PATH cannot stand in for the §33
    # recognition inputs; with the real seams present the mint still
    # succeeds, and clearing the env changes nothing.
    for var in ("USER", "SUDO_USER", "LOGNAME"):
        monkeypatch.delenv(var, raising=False)
    handle = rig.cw("hpac_challenge_coordinator")
    assert isinstance(handle, w.CertificationWriterHandle)


def test_19_caller_string_cannot_self_identify_via_argument(rig):
    # An arbitrary _caller_module string that is not the exact §38A consumer
    # is rejected; the argument is a disclosed test seam, not a trust input.
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator", _caller_module="pcae.core.hpac_certification_coordinator.evil")
    assert ei.value.code == "unauthorized_factory_consumer"


def test_20_issuance_audit_emitted_without_secrets(rig):
    rig.cw("hpac_challenge_coordinator")
    evdir = rig.root / ".authority" / "issuance-evidence"
    docs = list(evdir.glob("*.json"))
    assert docs
    blob = "\n".join(p.read_text() for p in docs)
    assert "certification_lifecycle_writer:hpac_challenge_coordinator" in blob
    assert "_seal" not in blob and "_authority_seal" not in blob


# ═══════════════════════════════════════════════════════════════════════════
# C. Role set (§99 items 11-20)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("role", FIVE_ROLES)
def test_30_each_allowlisted_role_mints(rig, role):
    handle = rig.cw(role)
    assert handle.role == role
    expected = rig.credential_id if role == "hpac_rhamp_counter_state_verifier" else rig.proof_id
    assert handle.subject == expected


def test_31_terminator_role_denied(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_lifecycle_terminator")
    assert ei.value.code == "operation_scope_invalid"


def test_32_unknown_role_denied(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.cw("totally_unknown_role")
    assert ei.value.code == "operation_scope_invalid"


@pytest.mark.parametrize("bad", ["*", "hpac_*", "hpac_challenge_*", "hpac_", "", "hpac_challenge_coordinatorX"])
def test_33_wildcard_prefix_nearmiss_denied(rig, bad):
    with pytest.raises(w.PawaError) as ei:
        rig.cw(bad)
    assert ei.value.code == "operation_scope_invalid"


def test_34_role_allowlist_is_exact_set_no_startswith():
    import ast

    assert isinstance(w.CERTIFICATION_ROLE_ALLOWLIST, frozenset)
    assert len(w.CERTIFICATION_ROLE_ALLOWLIST) == 5
    # AST of the validator: the role gate is exact `in` membership against the
    # allowlist, never a prefix / glob / regex-family match.
    src = (SRC / "core" / "hpac_protected_admin_writer.py").read_text()
    fn = next(
        n for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.FunctionDef) and n.name == "_validate_certification_inputs"
    )
    # structural: a `NotIn` comparison against CERTIFICATION_ROLE_ALLOWLIST,
    # and no attribute call that would be a prefix/glob/regex family match.
    has_notin = False
    bad_calls = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, ast.NotIn) and isinstance(comp, ast.Name) and comp.id == "CERTIFICATION_ROLE_ALLOWLIST":
                    has_notin = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("startswith", "endswith", "match", "search", "fnmatch", "fnmatchcase"):
                bad_calls.add(node.func.attr)
    assert has_notin
    assert not bad_calls, bad_calls


def test_35_generic_production_writer_authority_not_introduced():
    # certification_writer takes no caller-controlled generic role: its
    # `role` must be one of the closed five.
    import inspect

    sig = inspect.signature(w.certification_writer)
    assert list(sig.parameters)[0] == "role"
    a = HPACStoreAuthority.production()
    # no new public generic mint
    assert not hasattr(a, "certification_production_writer")


# ═══════════════════════════════════════════════════════════════════════════
# D. Binding (§99 items 21-28)
# ═══════════════════════════════════════════════════════════════════════════


def test_40_role_bound_to_expected_subject(rig):
    h = rig.cw("hpac_gate5_binder")
    assert h.subject == rig.proof_id
    h2 = rig.cw("hpac_rhamp_counter_state_verifier")
    assert h2.subject == rig.credential_id


def test_41_missing_session_id_rejected(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator", certification_session_id="")
    assert ei.value.code == "operation_scope_invalid"


def test_42_none_bypass_rejected(rig):
    for field in ("certification_session_id", "principal_id", "credential_id", "proof_id"):
        with pytest.raises(w.PawaError) as ei:
            rig.cw("hpac_challenge_coordinator", **{field: None})
        assert ei.value.code == "operation_scope_invalid"


def test_43_malformed_proof_id_rejected(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator", proof_id="not-a-proof-id")
    assert ei.value.code == "operation_scope_invalid"


def test_44_unresolvable_principal_rejected(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator", principal_id="hp-" + "0" * 32)
    assert ei.value.code == "operation_scope_invalid"


def test_45_credential_not_bound_to_principal_rejected(rig):
    other = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=other,
        enrollment_provenance_ref="other-ref",
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator", principal_id=other)
    assert ei.value.code == "operation_scope_invalid"


def test_46_revoked_principal_rejected(rig):
    w.revoke_principal_via_pawa(
        principal_id=rig.principal_id,
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator")
    assert ei.value.code == "operation_scope_invalid"


def test_47_revoked_credential_rejected(rig):
    w.revoke_credential_via_pawa(
        credential_id=rig.credential_id,
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_challenge_coordinator")
    assert ei.value.code == "operation_scope_invalid"


# ═══════════════════════════════════════════════════════════════════════════
# E. Capability lifecycle (§99 items 29-37)
# ═══════════════════════════════════════════════════════════════════════════


def test_50_trusted_construction_required_forgery_rejected(rig):
    h = rig.cw("hpac_challenge_coordinator")
    cap = h._capability
    forged = object.__new__(type(cap))
    with pytest.raises(HPACAuthorityError):
        h.authority.require_writer(forged, "hpac_challenge_coordinator", subject=rig.proof_id)


def test_51_handle_is_non_serializable(rig):
    import pickle

    h = rig.cw("hpac_challenge_coordinator")
    with pytest.raises(TypeError):
        pickle.dumps(h)
    with pytest.raises(TypeError):
        h.__reduce__()


def test_52_one_shot_first_consume_ok_second_denied(rig):
    h = rig.cw("hpac_challenge_coordinator")
    cap = h.consume("hpac_challenge_coordinator", certification_session_id=rig.session_id, subject=rig.proof_id)
    assert cap is h._capability
    with pytest.raises(w.PawaError) as ei:
        h.consume("hpac_challenge_coordinator", certification_session_id=rig.session_id, subject=rig.proof_id)
    assert ei.value.code == "capability_stale"


def test_53_consume_wrong_role_denied(rig):
    h = rig.cw("hpac_challenge_coordinator")
    with pytest.raises(w.PawaError) as ei:
        h.consume("hpac_assertion_recorder", certification_session_id=rig.session_id, subject=rig.proof_id)
    assert ei.value.code == "target_scope_invalid"


def test_54_consume_wrong_session_denied(rig):
    h = rig.cw("hpac_challenge_coordinator")
    with pytest.raises(w.PawaError) as ei:
        h.consume("hpac_challenge_coordinator", certification_session_id="hcs-" + "9" * 32, subject=rig.proof_id)
    assert ei.value.code == "target_scope_invalid"


def test_55_consume_wrong_subject_denied(rig):
    h = rig.cw("hpac_challenge_coordinator")
    with pytest.raises(w.PawaError) as ei:
        h.consume("hpac_challenge_coordinator", certification_session_id=rig.session_id, subject="hap-" + "1" * 32)
    assert ei.value.code == "target_scope_invalid"


def test_56_second_certification_writer_call_reruns_full_ss33a(rig):
    h1 = rig.cw("hpac_challenge_coordinator")
    h2 = rig.cw("hpac_challenge_coordinator")
    assert h1 is not h2
    assert h1._capability is not h2._capability
    assert h1.authority is not h2.authority


def test_57_no_remint_delegate_or_generic_conversion(rig):
    h = rig.cw("hpac_gate5_binder")
    assert not hasattr(h, "remint")
    assert not hasattr(h, "delegate")
    assert not hasattr(h, "to_generic")
    # possessing the handle does not expose the factory seal
    assert not hasattr(h, "_factory_seal")


def test_58_spent_flag_not_caller_resettable(rig):
    h = rig.cw("hpac_challenge_coordinator")
    h.consume("hpac_challenge_coordinator", certification_session_id=rig.session_id, subject=rig.proof_id)
    # even forcing the private flag back does not revive the handle
    h._consumed = False
    # the underlying capability object flag also cannot be reset via _mark_spent
    with pytest.raises(HPACAuthorityError):
        h._capability._mark_spent(object())


# ═══════════════════════════════════════════════════════════════════════════
# F. §39A consumer inventory + fixture-seam guards (§99 items 73-82)
# ═══════════════════════════════════════════════════════════════════════════

_AGENT_REACHABLE = [
    SRC / "cli.py",
    SRC / "core" / "agent.py",
]
_COMMANDS = sorted((SRC / "commands").rglob("*.py"))


def test_60_coordinator_and_factory_not_imported_by_agent_reachable_code():
    needles = ("hpac_certification_coordinator", "certification_writer")
    for path in _AGENT_REACHABLE + _COMMANDS:
        text = path.read_text()
        for n in needles:
            assert f"import {n}" not in text
            assert f"{n} import" not in text
            assert f", {n}" not in text


def test_61_admin_script_is_standalone_not_a_cli_subcommand():
    script = REPO / "scripts" / "hpac_certification_admin.py"
    assert script.exists()
    cli = (SRC / "cli.py").read_text()
    assert "hpac_certification_admin" not in cli
    # not a console_scripts entry point
    assert "hpac_certification_admin" not in (REPO / "pyproject.toml").read_text()


def test_62_only_caller_of_certification_writer_is_the_coordinator_ss33a_path():
    hits = subprocess.run(
        ["git", "-C", str(REPO), "grep", "-l", "certification_writer(", "--", "src", "scripts"],
        capture_output=True, text=True,
    ).stdout.split()
    assert set(hits) <= {
        "src/pcae/core/hpac_protected_admin_writer.py",  # the definition
        "src/pcae/core/hpac_certification_coordinator.py",  # the sole §38A consumer
    }, hits


def test_63_certification_test_consumer_allowlist_is_test_only():
    assert w._CERTIFICATION_TEST_CONSUMERS == frozenset({THIS_MODULE})
    for name in w._CERTIFICATION_TEST_CONSUMERS:
        assert name.startswith("test_")


def test_64_coordinator_does_not_import_test_or_pytest_or_fixture_modules():
    text = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    for forbidden in ("import pytest", "from tests", "_PRODUCTION_TEST_FIXTURE_SEAL", "_test_decision_source",
                      "DeterministicCtap2Provider", "monkeypatch", "object.__new__"):
        assert forbidden not in text


def test_65_coordinator_not_exported_from_public_package_namespace():
    import pcae
    import pcae.core

    assert not hasattr(pcae, "certification_writer")
    assert not hasattr(pcae, "HpacCertificationCoordinator")
    assert not hasattr(pcae.core, "certification_writer")


def test_66_no_new_pawa_operation_or_failure_code_added_by_certification():
    assert len(list(w.PawaOperation)) == 6
    assert len(w.PAWA_FAILURE_CODES) == 21
    # certification rejections all reuse existing codes
    for code in ("unauthorized_factory_consumer", "operation_scope_invalid",
                 "target_scope_invalid", "capability_stale", "reconstruction_attempt",
                 "internal_fail_closed"):
        assert code in w.PAWA_FAILURE_CODES


# ═══════════════════════════════════════════════════════════════════════════
# G. Coordinator orchestration (§99 items 61-66, admin entry 83-88)
# ═══════════════════════════════════════════════════════════════════════════


def _coord(rig):
    return cc.HpacCertificationCoordinator(
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
        _caller_module=COORDINATOR_MODULE,
    )


def test_70_coordinator_begin_session_reserves_ids(rig):
    co = _coord(rig)
    s = co.begin_session(principal_id=rig.principal_id, credential_id=rig.credential_id)
    assert s.certification_session_id.startswith("hcs-")
    assert s.proof_id.startswith("hap-")
    assert co.ceremony_mode == "test-only"


def test_71_coordinator_is_sole_ss38a_consumer_constant():
    assert w.CERTIFICATION_FACTORY_CONSUMERS == frozenset({"pcae.core.hpac_certification_coordinator"})


def test_72_coordinator_cannot_construct_authenticated_principal():
    text = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    assert "AuthenticatedHumanPrincipal(" not in text
    assert "_VERIFIER_CONSTRUCTOR_SEAL" not in text


def test_73_coordinator_does_not_reach_runtime_or_dispatch():
    text = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    # no *import* of any runtime / dispatch / gate-6+ / PB module
    import ast

    tree = ast.parse(text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    forbidden_mods = {
        "pcae.core.runtime_dispatch_permission",
        "pcae.core.runtime_dispatch_gate6",
        "pcae.core.runtime_dispatch_gate7",
        "pcae.core.runtime_dispatch_gate9",
        "pcae.core.permission_broker_foundation",
        "pcae.core.adapter",
        "pcae.core.daemon",
    }
    assert not (imported & forbidden_mods), imported & forbidden_mods
    # no call expression that dispatches an effect
    assert "adapter.dispatch(" not in text
    assert "DispatchEnvelope(" not in text


def test_74_coordinator_reach_gate5_terminates_at_verifier(rig):
    # `reach_gate5_assurance` calls verify_human_authentication and returns
    # its principal — it never continues to a Gate 6+ / effect call.
    text = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    body = text.split("def reach_gate5_assurance")[1].split("\n    def ")[0]
    assert "verify_human_authentication(" in body
    assert "return principal" in body
    for forbidden in ("run_gate6", "run_gate7", "run_gate9", "adapter.dispatch(", "DispatchEnvelope("):
        assert forbidden not in body


def test_80_admin_script_describe_is_read_only_and_lists_frozen_boundary():
    out = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "hpac_certification_admin.py"), "describe"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "hpac_certification_coordinator" in out
    for role in FIVE_ROLES:
        assert role in out
    assert "hpac_lifecycle_terminator" in out  # listed as denied


def test_81_admin_script_has_no_approval_pin_or_arbitrary_role_flags():
    import ast

    text = (REPO / "scripts" / "hpac_certification_admin.py").read_text()
    tree = ast.parse(text)
    # collect every argparse add_argument / add_parser literal
    added = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in (
            "add_argument", "add_parser"
        ):
            added += [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
    for opt in added:
        assert opt.lstrip("-") in {"describe", "status"} or not opt.startswith("-"), opt
    assert "--approve" not in added and "--pin" not in added and "--fake-real" not in added
    for forbidden in ("eval(", "exec(", "subprocess", "os.system", "__import__("):
        assert forbidden not in text


def test_82_admin_script_rejects_unknown_subcommand():
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "hpac_certification_admin.py"), "ceremony"],
        capture_output=True, text=True,
    )
    assert r.returncode != 0


def test_83_admin_script_not_imported_by_any_src_module():
    import ast

    for path in sorted((SRC).rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all("hpac_certification_admin" not in a.name for a in node.names), path
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "hpac_certification_admin" not in node.module, path


# ═══════════════════════════════════════════════════════════════════════════
# H. Host-state preservation (§99 items 93-100) — the rig root is disposable
# ═══════════════════════════════════════════════════════════════════════════


def test_90_no_write_outside_the_disposable_fixture_root(rig, tmp_path):
    before = {p: p.stat().st_mtime_ns for p in tmp_path.rglob("*") if p.is_file()}
    rig.cw("hpac_challenge_coordinator")
    # the only new/changed files are under the fixture root's .authority/
    after = {p: p.stat().st_mtime_ns for p in tmp_path.rglob("*") if p.is_file()}
    changed = {p for p in after if before.get(p) != after[p]}
    assert all(str(rig.root) in str(p) for p in changed), changed


def test_91_runtime_remains_unavailable_after_import():
    # importing the coordinator must not change runtime observability
    from pcae.core import hpac_certification_coordinator  # noqa: F401

    # no plugin / capability registration side effect
    import pcae.core.hpac_certification_coordinator as m

    assert not hasattr(m, "register_runtime_plugin")
    assert not hasattr(m, "RUNTIME_CAPABILITY")


def test_92_no_makecredential_getassertion_pin_calls_in_coordinator_or_script():
    import ast

    for path in (SRC / "core" / "hpac_certification_coordinator.py",
                 REPO / "scripts" / "hpac_certification_admin.py"):
        tree = ast.parse(path.read_text())
        called = set()
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Attribute):
                    called.add(f.attr)
                elif isinstance(f, ast.Name):
                    called.add(f.id)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not ({"make_credential", "makeCredential", "get_assertion", "getAssertion", "verify_pin"} & called)
        assert "pcae.core.hpac_rhamp_ctap2" not in imported
        assert "pcae.core.human_authenticator_fido2" not in imported
