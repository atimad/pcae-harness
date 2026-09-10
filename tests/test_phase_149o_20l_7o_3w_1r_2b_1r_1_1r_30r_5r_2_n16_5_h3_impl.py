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
    _PRODUCTION_TEST_FIXTURE_SEAL,  # builds the disposable provisioned root only
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
)
from pcae.core.human_authentication_proof import new_proof_id
from pcae.core.human_principal_registry import HumanPrincipalRegistryStore, new_principal_id

from _caller_identity_helper import call_with_real_module_identity

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
#: N16-5-F5B1-READAUTH: a downstream governed phase evolved HPAC-PAWA-001
#: v1.3 -> v1.4 (MINOR, S-3 -- the F-5-B1 recognized read / ceremony-entry
#: authority) and legitimately edits this one contract file. The H-3
#: guards below assert "no retro-edit during the H-3 window": their
#: endpoint is re-anchored from the moving HEAD to this fixed SHA (the
#: N16-5-FINAL-CERT head -- the last commit at which the contract was
#: still v1.3), so they keep asserting exactly what they were written to
#: assert. No test function renamed or removed; no test disabled.
_F5B1_READAUTH_ENTRY = "18d7da02435cac61159e9a90f86b2a586c4704d0"

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
         f"{_F5B1_READAUTH_ENTRY}:docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert blob == PAWA_V13_BLOB


def test_02_no_contract_normative_diff_since_i0():
    names = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", I0, _F5B1_READAUTH_ENTRY, "--", "docs/contracts"],
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


def _cw_as(rig, module_name, role, **over):
    """N16-5-F-5-B2-IMPL: ``rig.cw``'s own default ``_caller_module``
    override is no longer authoritative, so a genuine wrong-identity
    negative test must make the ``certification_writer`` call really
    originate from ``module_name`` (real caller-provenance detection)."""
    kw = dict(
        certification_session_id=rig.session_id,
        principal_id=rig.principal_id,
        credential_id=rig.credential_id,
        proof_id=rig.proof_id,
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    kw.update(over)
    return call_with_real_module_identity(module_name, w.certification_writer, role, **kw)


def test_13_wrong_category_caller_denied(rig):
    with pytest.raises(w.PawaError) as ei:
        _cw_as(rig, "pcae.core.agent", "hpac_challenge_coordinator")
    assert ei.value.code == "unauthorized_factory_consumer"


def test_14_production_writer_admin_module_cannot_request_certification_role(rig):
    with pytest.raises(w.PawaError) as ei:
        _cw_as(rig, "pcae.core.hpac_protected_admin_writer", "hpac_challenge_coordinator")
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
    # An arbitrary caller module that is not the exact §38A consumer is
    # rejected; consumer identity is real caller provenance, never a
    # caller-asserted argument.
    with pytest.raises(w.PawaError) as ei:
        _cw_as(rig, "pcae.core.hpac_certification_coordinator.evil", "hpac_challenge_coordinator")
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


def test_93_pawa_and_frozen_contracts_byte_unchanged_since_i0():
    names = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", I0, _F5B1_READAUTH_ENTRY, "--", "docs/contracts", "schemas"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert names == [], names
    # And since the F-5-B1 read/ceremony-entry evolution: it touches exactly
    # this one contract file and nothing under schemas/ (v1.4 adds no schema).
    # Reconciled by phase N16-5-F-5-TB-CONTRACT (HPAC-PAWA-001 v1.4 -> v2.0, MAJOR S-4; new companion HPAC-PAWA-HELPER-001 v1.0): re-anchor the moving `HEAD` to the fixed
    # SHA 05056eeb1d38d92d7eda749a4334f7626c5e6a8f (last v1.4 commit); through that SHA exactly the one PAWA
    # anchor file changed under docs/contracts and nothing under schemas/.
    since = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", _F5B1_READAUTH_ENTRY, "05056eeb1d38d92d7eda749a4334f7626c5e6a8f", "--", "docs/contracts", "schemas"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert set(since) <= {"docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"}, since


# ═══════════════════════════════════════════════════════════════════════════
# I. Deterministic end-to-end reachability through the coordinator
#    (§99 items 38-66; §106 criteria 9-15). This is the H-3 repair proof:
#    the full canonical challenge → assertion → proof/verified →
#    Gate-5 binding → counter chain composes through the NEW production
#    `certification_writer` / coordinator boundary — NOT the disclosed
#    `_mint_production_writer_capability` test seal.
# ═══════════════════════════════════════════════════════════════════════════


def test_100_full_chain_reaches_real_assurance_and_gate5_via_coordinator(tmp_path):
    import hashlib
    import json

    from pcae.core import hpac_protected_presentation_admin as ppadmin
    from pcae.core import protected_presentation as pp
    from pcae.core import protected_presentation_installation as inst
    import pcae.protected_presentation_helper as H
    from pcae.core.hpac_foundation import canonical_digest, canonical_json_bytes
    from pcae.core.approval_presentation import (
        PresentationMechanismDescriptorStore,
        TrustedApprovalPresentationStore,
        new_canonical_runtime_approval_subject,
    )
    from pcae.core.hpac_lifecycle import HPACLifecycleStore, STATE_PROOF_VERIFIED_AND_BOUND
    from pcae.core.hpac_rhamp_client_context import MECHANISM_ID
    from pcae.core.hpac_rhamp_credential_sidecar import HpacRhampCredentialSidecarStore
    from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
    from pcae.core.hpac_rhamp_enrollment import enroll_first_credential, resolve_active_credentials
    from pcae.core.human_authenticator_fido2 import FIDO2HumanAuthenticator, encode_assertion_envelope
    from pcae.core.human_authentication_proof import (
        HumanAuthenticationProof,
        HumanAuthenticationProofStore,
        PROOF_SCHEMA_VERSION,
    )
    from pcae.core.hpac_verifier import (
        AuthenticatedHumanPrincipal,
        is_verifier_authenticated_principal,
    )

    HELPER_SHIM = (
        b"#!/usr/bin/env python3\nimport sys\nfrom pcae.protected_presentation_helper import main\n"
        b"sys.exit(main())\n"
    )
    RENDERER = "pcae-protected-local-presentation-renderer/1.0"

    def _inproc_launch(helper_fd, request, *, timeout_seconds):
        os.close(helper_fd)
        req = H._validate_request(json.loads(canonical_json_bytes(request).decode()))
        displayed = H.render_human_visible_bytes(req["human_visible_facts"], renderer_profile=req["renderer_profile"])
        dd = hashlib.sha256(displayed).hexdigest()
        decision = H._observe_election(req, displayed)
        if decision == "CANCEL":
            return None
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        return json.loads(canonical_json_bytes(H._build_response(req, decision, dd, now=now)).decode())

    root = (tmp_path / "root").resolve()
    w.provision_protected_root(protected_root=root, agent_account="a-svc-h3impl-e2e", agent_uid=4_242_777)
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    registry = HumanPrincipalRegistryStore(authority)
    sidecar_store = HpacRhampCredentialSidecarStore(authority)
    principal_id = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=principal_id, enrollment_provenance_ref="h3impl-e2e",
        _protected_root=root, _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    sha = hashlib.sha256(HELPER_SHIM).hexdigest()
    hp = inst.helper_content_addressed_path(root, sha)
    hp.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    hp.write_bytes(HELPER_SHIM)
    os.chmod(hp, 0o500)
    ppadmin.configure_presentation_mechanism(
        action="install", helper_sha256=sha, helper_implementation_version="pplp/1.0.0",
        verifier_configuration_digest=hashlib.sha256(b"vc-h3impl").hexdigest(),
        renderer_profile=RENDERER, descriptor_version="pplp-1.0", protected_root=root,
        _configured_agent_identity_source=_agent_src(), _topology_probe=_locked_probe(),
    )
    provider = DeterministicCtap2Provider()
    res = enroll_first_credential(
        principal_id=principal_id, subject_digest="a" * 64, presentation_digest="b" * 64,
        invocation_id="iv-h3impl", attempt_id="at-h3impl", provider=provider, protected_root=root,
        _configured_agent_identity_source=_agent_src(), _topology_probe=_locked_probe(),
    )

    invocation_id, attempt_id = "inv-h3impl", "at-h3impl"
    facts = {
        "repository_identity": "repo-h3", "repository_display": "repo-h3 (fp:h3)",
        "task_id": "task-h3", "task_display": "task-h3 x",
        "runtime_target_id": "rt-none", "runtime_target_display": "rt-none x",
        "operation_effect_scope_display": "cap=none; no-effect", "prompt_hash": "c" * 64,
        "prompt_instruction_display": "h3 (fp:c001)", "invocation_id": invocation_id,
        "invocation_display": f"{invocation_id} (fp:i001)", "expires_at": "2099-01-01T00:00:00Z",
        "one_shot_notice": True,
    }
    subject = new_canonical_runtime_approval_subject(
        subject={"repository_identity": "repo-h3", "task_id": "task-h3",
                 "runtime_target_id": "rt-none", "prompt_hash": "c" * 64, "invocation_id": invocation_id},
        approval_scope={"capability": "none", "one_dispatch": False, "network": False},
        approval_preview_digest=hashlib.sha256(
            H.render_human_visible_bytes(facts, renderer_profile=RENDERER)
        ).hexdigest(),
        expires_at="2099-01-01T00:00:00Z",
    )
    approval_id = "ria-" + hashlib.sha256(f"{invocation_id}{attempt_id}".encode()).hexdigest()[:32]

    orig = pp._launch_and_exchange
    pp._launch_and_exchange = _inproc_launch
    try:
        cer = pp.run_protected_presentation_ceremony(
            authority=authority, approval_id=approval_id, challenge_id="ch-" + invocation_id,
            canonical_subject=subject, human_visible_facts=facts, principal_id=principal_id,
            invocation_id=invocation_id, attempt_id=attempt_id, _test_decision_source="APPROVE",
        )
    finally:
        pp._launch_and_exchange = orig

    ds = PresentationMechanismDescriptorStore(authority)
    ps = TrustedApprovalPresentationStore(authority)
    resolved_pres = ps.resolve_canonical(
        presentation_id=cer.presentation_id, presentation_digest=cer.presentation_digest, descriptor_store=ds
    )
    assert resolved_pres.authority_class is HPACAuthorityClass.PRODUCTION

    material = resolve_active_credentials(registry, principal_id)
    allow = tuple(m.raw_credential_id for m in material if m.credential_id == res.credential_id)
    auth_fido = FIDO2HumanAuthenticator(
        principal_id=principal_id, credential_id=res.credential_id, provider=provider,
        allow_credential_ids=allow, invocation_id=invocation_id, attempt_id=attempt_id,
    )
    ch = auth_fido.prepare_challenge(subject.digest(), cer.presentation_digest, issued_at="2026-09-07T12:00:00Z")
    env = auth_fido.run_assertion_ceremony(ch)

    # ── drive the chain through the NEW production coordinator ──────────
    co = cc.HpacCertificationCoordinator(
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
        _caller_module=COORDINATOR_MODULE,
    )
    sess = co.begin_session(principal_id=principal_id, credential_id=res.credential_id)

    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION, "proof_id": sess.proof_id,
        "mechanism_id": MECHANISM_ID, "principal_id": principal_id, "credential_id": res.credential_id,
        "challenge_digest": ch.challenge_digest, "approval_subject_digest": ch.approval_subject_digest,
        "trusted_presentation_ref": {"presentation_id": cer.presentation_id,
                                     "presentation_digest": cer.presentation_digest},
        "assertion": encode_assertion_envelope(env), "up": env.up, "uv": env.uv,
        "authenticated_at": ch.issued_at, "verifier_version": "h3impl/1.0",
    }
    body["proof_digest"] = canonical_digest({k: v for k, v in body.items() if k != "proof_digest"})
    proof = HumanAuthenticationProof(**body)

    assert resolved_pres is not None  # sanity: the test authority also resolves it
    sess.open_challenge(
        approval_id=approval_id, invocation_id=invocation_id, attempt_id=attempt_id,
        mechanism_id=MECHANISM_ID, occurred_at="2026-09-07T12:00:10Z",
        presentation_id=cer.presentation_id, presentation_digest=cer.presentation_digest, challenge=ch,
    )
    sess.record_assertion(
        assertion_digest=canonical_digest({"assertion": proof.assertion}),
        occurred_at="2026-09-07T12:00:20Z",
    )
    sess.record_verified_proof(
        proof=proof, registry_state_digest=canonical_digest({"r": "s"}),
        verifier_version="h3impl/1.0", occurred_at="2026-09-07T12:00:30Z",
    )
    principal = sess.reach_gate5_assurance(
        challenge=ch, approval_id=approval_id, now="2026-09-07T12:01:00Z",
        occurred_at="2026-09-07T12:00:45Z", verifier_version="h3impl/1.0",
    )

    # §106 criterion 13/14: the require_real_assurance PRODUCTION path and
    # the actual Gate-5 binding are mechanically reachable through the new
    # certification boundary, with NO test seal.
    assert isinstance(principal, AuthenticatedHumanPrincipal)
    assert principal.assurance_class is HPACAuthorityClass.PRODUCTION
    assert principal.is_real_runtime_eligible is True
    assert is_verifier_authenticated_principal(principal)

    lc = HPACLifecycleStore(authority)
    bound = lc.resolve_gate5_binding_event(sess.proof_id)
    assert bound is not None and bound.record.state == STATE_PROOF_VERIFIED_AND_BOUND

    # §106 criterion 16: the certification chain composed with NO test-only
    # production seal — this end-to-end path never calls the low-level mint
    # primitive directly and never imports the factory seal.
    import ast

    tree = ast.parse(Path(__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr != ("_mint_production_writer" + "_capability")
        if isinstance(node, ast.ImportFrom) and node.module == "pcae.core.hpac_foundation":
            names = {a.name for a in node.names}
            assert ("_PRODUCTION_WRITER" + "_FACTORY_SEAL") not in names


def test_101_deterministic_fixture_authority_does_not_reach_real_assurance(tmp_path):
    # A purely FIXTURE_NON_REAL authority can never satisfy the §33A
    # recognition sequence — certification_writer needs a PRODUCTION-class
    # HPACStoreAuthority (via the provisioned root), so a fixture path
    # cannot elevate.
    fixture_authority = HPACStoreAuthority.fixture(tmp_path / "fx")
    assert fixture_authority.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL
    with pytest.raises(w.PawaError):
        w.certification_writer(
            "hpac_challenge_coordinator",
            certification_session_id="hcs-" + "0" * 32,
            principal_id="hp-" + "0" * 32, credential_id="hpc-" + "0" * 32,
            proof_id="hap-" + "0" * 32,
            _protected_root=tmp_path / "fx",
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
            _caller_module=COORDINATOR_MODULE,
        )


def test_102_coordinator_production_status_does_not_relax_require_real_assurance():
    v = (SRC / "core" / "hpac_verifier.py").read_text()
    # the joint real-auth + real-presentation check is unchanged and lives
    # in the verifier, not the coordinator.
    assert "HPAC-PPA-REQ-057" in v
    assert "require_real_assurance" in v
    coord = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    assert "require_real_assurance" in coord  # only ever passed through, never redefined
    assert "assurance_class" not in coord.replace("assurance result", "")


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


# ═══════════════════════════════════════════════════════════════════════════
# J. Part 3 — non-elevation matrix, PB/policy dominance, forgery, currentness,
#    restart-dead, ordinary-actor non-authority, external-effect termination
#    (§57-§74 / §94; §99 items to ≥100; §106 criteria 17-24)
# ═══════════════════════════════════════════════════════════════════════════


def test_110_deterministic_mechanism_id_never_reaches_real_eligible_set():
    from pcae.core.hpac_verifier import _REAL_ELIGIBLE_MECHANISM_IDS
    from pcae.core.human_authenticator_deterministic import DETERMINISTIC_MECHANISM_ID

    assert DETERMINISTIC_MECHANISM_ID not in _REAL_ELIGIBLE_MECHANISM_IDS
    assert _REAL_ELIGIBLE_MECHANISM_IDS == frozenset({"hpac.fido2.uv_presence.v2"})


def test_111_require_real_assurance_joint_check_is_in_the_verifier_not_the_coordinator():
    import ast

    coord = ast.parse((SRC / "core" / "hpac_certification_coordinator.py").read_text())
    # the coordinator only passes require_real_assurance through to the verifier;
    # it never compares assurance_class or a mechanism id itself.
    names = {n.attr for n in ast.walk(coord) if isinstance(n, ast.Attribute)}
    assert "assurance_class" not in names
    for kw in ("_REAL_ELIGIBLE_MECHANISM_IDS", "_REAL_PRESENTATION_MECHANISM_ID", "HPACAuthorityClass"):
        assert kw not in (SRC / "core" / "hpac_certification_coordinator.py").read_text().replace(
            "assurance result", ""
        ).replace("the bounded assurance", "")


def test_112_coordinator_does_not_construct_or_seal_a_principal_or_gate_result():
    import ast

    tree = ast.parse((SRC / "core" / "hpac_certification_coordinator.py").read_text())
    called = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    for forbidden in ("AuthenticatedHumanPrincipal", "Gate5Result", "ValidatedAuthorityProjection"):
        assert forbidden not in called
    text = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    for seal in ("_VERIFIER_CONSTRUCTOR_SEAL", "_GATE5_RESULT_CONSTRUCTOR_SEAL", "_WRITER_CONSTRUCTOR_SEAL"):
        assert seal not in text


def test_113_pb_and_policy_walls_named_in_contract_and_unrelaxed():
    pawa = (CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md").read_text()
    assert "override PB or policy" in pawa or "override a no-go" in pawa
    assert "PAWA-INV-13" in pawa
    # the certification family explicitly excludes a PB permission / policy
    # exception / RE result / runtime capability / DispatchEnvelope
    for excluded in ("PB\n  permission", "Runtime Enforcement result", "DispatchEnvelope",
                     "runtime capability"):
        assert excluded in pawa


def test_114_certification_family_cannot_write_authority_consumption_or_gate9():
    pawa = (CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md").read_text()
    assert "HPAC-AUTHORITY-CONSUMPTION/2.1" in pawa
    assert "Gate-9 artifact" in pawa
    # the coordinator imports no Gate-9 / consumption module
    import ast

    imported = {
        n.module for n in ast.walk(ast.parse((SRC / "core" / "hpac_certification_coordinator.py").read_text()))
        if isinstance(n, ast.ImportFrom) and n.module
    }
    assert "pcae.core.runtime_invocation_authority_consumption" not in imported
    assert not any("gate9" in m or "gate_9" in m for m in imported)


def test_115_presentation_evidence_writer_is_outside_the_five_role_family():
    assert "protected_presentation_mechanism" not in w.CERTIFICATION_ROLE_ALLOWLIST
    src = (SRC / "core" / "hpac_protected_admin_writer.py").read_text()
    # mint_protected_presentation_evidence_writer is a DISTINCT factory,
    # reused unchanged (HPAC-PAWA-REQ-248).
    assert "def mint_protected_presentation_evidence_writer" in src
    assert "PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS" in src


def test_116_challenge_forgery_rejected_by_open_challenge(rig):
    # a structurally-plausible but non-issued challenge fails
    # open_challenge_canonical's digest / binding checks.
    co = _coord(rig)
    sess = co.begin_session(principal_id=rig.principal_id, credential_id=rig.credential_id)

    class _FakeChallenge:
        domain_separator = "x"
        challenge_version = "v1"
        proof_schema_version = "HPAC-PROOF/2.0"
        principal_id = rig.principal_id
        credential_id = rig.credential_id
        approval_subject_digest = "a" * 64
        trusted_presentation_digest = "b" * 64
        nonce = "c" * 64
        issued_at = "2026-09-07T12:00:00Z"
        expires_at = "2026-09-07T13:00:00Z"
        challenge_digest = "d" * 64

    with pytest.raises(cc.CertificationCoordinatorError):
        sess.open_challenge(
            approval_id="ria-x", invocation_id="iv-x", attempt_id="at-x",
            mechanism_id="hpac.fido2.uv_presence.v2",
            presentation_id="hpe-" + "0" * 32, presentation_digest="b" * 64,
            challenge=_FakeChallenge(),
        )


def test_117_forged_certification_capability_via_object_new_rejected(rig):
    h = rig.cw("hpac_gate5_binder")
    forged = object.__new__(w.CertificationWriterHandle)
    with pytest.raises((HPACAuthorityError, AttributeError, w.PawaError, TypeError)):
        # a shell handle has no bound capability / authority
        forged.consume("hpac_gate5_binder", certification_session_id=rig.session_id, subject=rig.proof_id)


def test_118_counter_decision_cannot_be_caller_supplied(rig):
    # the counter role's authority is bounded to `apply_after_verification`
    # on an accepted canonical decision — the coordinator never lets a caller
    # pass ACCEPT/REVIEW/DENY. reach_gate5_assurance takes no `decision` arg.
    import inspect

    sig = inspect.signature(cc.CertificationSession.reach_gate5_assurance)
    assert "decision" not in sig.parameters
    assert "counter_decision" not in sig.parameters
    pawa = (CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md").read_text()
    assert "trusting a caller-provided" in pawa and "counter accepted" in pawa


def test_119_counter_role_cannot_reset_or_reassign(rig):
    from pcae.core.hpac_rhamp_counter_state import COUNTER_STATE_VERIFIER_ROLE

    h = rig.cw(COUNTER_STATE_VERIFIER_ROLE)
    assert h.subject == rig.credential_id
    # the minted capability is single-use, bound to exactly one credential
    cap = h.consume(COUNTER_STATE_VERIFIER_ROLE, certification_session_id=rig.session_id, subject=rig.credential_id)
    assert cap.role == COUNTER_STATE_VERIFIER_ROLE
    with pytest.raises(w.PawaError):
        h.consume(COUNTER_STATE_VERIFIER_ROLE, certification_session_id=rig.session_id, subject=rig.credential_id)


def test_120_restart_dead_capability_from_a_prior_authority_instance(rig):
    h1 = rig.cw("hpac_challenge_coordinator")
    cap1 = h1._capability
    # a fresh recognition (== a fresh "process" in the seal model) mints a
    # new authority instance; the old capability fails the new one's identity
    h2 = rig.cw("hpac_challenge_coordinator")
    with pytest.raises(HPACAuthorityError):
        h2.authority.require_writer(cap1, "hpac_challenge_coordinator", subject=rig.proof_id)


def test_121_wrong_credential_for_counter_role_rejected(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.cw("hpac_rhamp_counter_state_verifier", credential_id="hpc-" + "0" * 32)
    assert ei.value.code == "operation_scope_invalid"


@pytest.mark.parametrize("actor_module", [
    "pcae.core.agent", "pcae.cli", "pcae.core.runtime_authority",
    "pcae.core.runtime_dispatch_gate5", "pcae.core.protected_presentation",
    "pcae.protected_presentation_helper", "pcae.core.hpac_protected_presentation_admin",
    "pcae.core.hpac_verifier", "pcae.core.daemon", "some.plugin.module",
])
def test_122_ordinary_actors_cannot_acquire_certification_authority(rig, actor_module):
    with pytest.raises(w.PawaError) as ei:
        _cw_as(rig, actor_module, "hpac_challenge_coordinator")
    assert ei.value.code == "unauthorized_factory_consumer"


def test_123_test_fixture_module_is_not_a_production_consumer():
    # the disclosed test-only seam is exactly this suite; a fixture module
    # name is not in the production §38A inventory.
    assert THIS_MODULE not in w.CERTIFICATION_FACTORY_CONSUMERS
    assert THIS_MODULE in w._CERTIFICATION_TEST_CONSUMERS


def test_124_external_effect_termination_contract_and_status():
    pawa = (CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md").read_text()
    assert "bounded Gate-5 certification result" in pawa
    assert "terminates at the bounded Gate-5 assurance result" in pawa
    assert "authorizes no first" in pawa and "external effect" in pawa
    out = subprocess.run(["pcae", "runtime", "inspect"], cwd=REPO, capture_output=True, text=True).stdout
    assert "Runtime status:            not_implemented" in out
    assert "Execution capability:      unavailable" in out
    assert "Plugin count:              0" in out
    assert "Capability count:          0" in out


def test_125_no_pawa_operation_added_and_enum_membership_frozen():
    from pcae.core.hpac_protected_admin_writer import PawaOperation

    assert {m.value for m in PawaOperation} == {
        "enroll_principal", "revoke_principal", "enroll_credential",
        "revoke_credential", "initialize_credential_sidecar_state",
        "configure_presentation_mechanism",
    }


def test_126_every_certification_rejection_maps_to_an_existing_code(rig):
    seen = set()
    cases = [
        ("hpac_lifecycle_terminator", {}),
        ("wildcard*", {}),
        ("hpac_challenge_coordinator", {"certification_session_id": ""}),
        ("hpac_challenge_coordinator", {"proof_id": "bad"}),
        ("hpac_challenge_coordinator", {"principal_id": "hp-" + "0" * 32}),
        ("hpac_challenge_coordinator", {"_caller_module": "pcae.core.agent"}),
    ]
    for role, over in cases:
        try:
            rig.cw(role, **over)
        except w.PawaError as e:
            seen.add(e.code)
    assert seen <= set(w.PAWA_FAILURE_CODES)
    assert seen <= {"operation_scope_invalid", "unauthorized_factory_consumer",
                    "protected_root_untrusted", "agent_principal_unknown"}


def test_127_certification_capabilities_are_process_local_non_bearer(rig):
    h = rig.cw("hpac_challenge_coordinator")
    cap = h._capability
    # non-bearer: a structural lookalike with copied fields is not authority
    import copy

    with pytest.raises(TypeError):
        copy.deepcopy(cap)
    # process-local: the seal is an object() private to the authority instance
    assert cap._authority_seal is h.authority._seal


def test_128_admin_script_status_does_not_mutate_and_exits_cleanly_or_2():
    # Reconciled by phase N16-5-F-5-PPA-CONTRACT: compare the tracked-file diff
    # before and after running the script rather than asserting the working
    # tree is free of contract-path changes -- an unrelated in-flight governed
    # contract evolution (HPAC-PPA-001 v1.0 -> v2.0) may legitimately have
    # docs/contracts edits staged in the working tree; the property under test
    # is that the bounded `status` read introduces NO new tracked-file change.
    def _diff() -> set[str]:
        return set(subprocess.run(
            ["git", "-C", str(REPO), "diff", "--name-only"], capture_output=True, text=True
        ).stdout.split())

    before = _diff()
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "hpac_certification_admin.py"), "status"],
        capture_output=True, text=True,
    )
    assert r.returncode in (0, 2)  # 0 if a real root exists, 2 (reported) otherwise
    # the bounded `status` entry performs only a read; it touches no protected
    # store and no tracked source file.
    assert _diff() == before


def test_129_no_new_terminal_reason_and_rhamp_contract_unedited_since_i0():
    names = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", I0, "HEAD", "--",
         "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert names == []


def test_130_h3_verdict_is_iv_pending_never_self_verified():
    doc = (REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N16_5_H3_IMPL.md").read_text()
    # the phase never claims H-3 VERIFIED / N-16-5 CLOSED
    assert "H-3 VERIFIED" not in doc.replace("INDEPENDENTLY VERIFIED RESOLVED", "")
    assert "N-16-5 CLOSED" not in doc.replace("N-16-5 NOT CLOSED", "").replace(
        "do not close N-16-5", ""
    ).replace("N-16-5 remains NOT CLOSED", "")


def test_131_gate5_binder_subject_is_proof_id_and_counter_subject_is_credential_id(rig):
    assert rig.cw("hpac_gate5_binder").subject == rig.proof_id
    assert rig.cw("human_authentication_proof_verifier").subject == rig.proof_id
    assert rig.cw("hpac_assertion_recorder").subject == rig.proof_id
    assert rig.cw("hpac_rhamp_counter_state_verifier").subject == rig.credential_id


def test_132_second_ceremony_capability_not_usable_in_first(rig):
    co = _coord(rig)
    s1 = co.begin_session(principal_id=rig.principal_id, credential_id=rig.credential_id)
    s2 = co.begin_session(principal_id=rig.principal_id, credential_id=rig.credential_id)
    assert s1.certification_session_id != s2.certification_session_id
    assert s1.proof_id != s2.proof_id
    h1 = s1._mint("hpac_challenge_coordinator")
    with pytest.raises(w.PawaError) as ei:
        h1.consume("hpac_challenge_coordinator",
                   certification_session_id=s2.certification_session_id, subject=s1.proof_id)
    assert ei.value.code == "target_scope_invalid"


def test_133_coordinator_short_lived_one_ceremony_per_invocation_documented():
    text = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    assert "ceremony per invocation" in text
    assert "HPAC-PAWA-REQ-259" in text
