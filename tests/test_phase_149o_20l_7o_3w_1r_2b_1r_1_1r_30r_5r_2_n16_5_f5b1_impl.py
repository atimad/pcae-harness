"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R
(alias N16-5-F-5-B1-IMPL) — the F-5-B1 read / ceremony-entry authority
IMPLEMENTATION suite.

Exercises HPAC-PAWA-001 v1.4 §33B / §38B / §42D / §42E / §49B / §68B as
implemented by:

  * ``hpac_protected_admin_writer.recognized_certification_read_authority``
    (the dedicated §33B factory) + ``CertificationReadAuthority`` (§49B
    one-ceremony-entry handle);
  * ``hpac_certification_coordinator.CertificationSession
    .run_presentation_ceremony`` (the sole §38B consumer path).

No real ceremony, no genuine YubiKey, no PIN, no protected APPROVE, no
``makeCredential`` / ``getAssertion``. All tests use a disposable
provisioned PRODUCTION test-fixture protected root under ``tmp_path``.
The one ceremony-entry test point monkeypatches the module-level
``run_protected_presentation_ceremony`` reference with a deterministic
sentinel -- no production test-injection parameter is added for this.
"""

from __future__ import annotations

import os
import subprocess
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
THIS_MODULE = "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_f5b1_impl"
COORDINATOR_MODULE = "pcae.core.hpac_certification_coordinator"

#: I0 -- this implementation phase's entry SHA (predecessor N16-5-F5B1-READAUTH-IV head).
I0 = "a6455ef1ef130d77c01aa3b2a2d7833f5eb8cb5e"

FAKE_AGENT_UID = 4_242_801
FAKE_AGENT_GID = 999_801
AGENT_ACCOUNT = "pcae-agent-svc-n16-5-f5b1-impl"


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures / helpers (mirrors the H-3 implementation suite's Rig pattern)
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


def _root_repro_probe():
    """F-5-B1 reproduction: ambient uid 0 (root) genuinely CAN write the
    fixture root per this probe; the configured agent (FAKE_AGENT_UID)
    cannot. This is the exact shape of the real sudo/root deployment."""

    def ewa(path, uid, gids):
        if uid == 0:
            return (True, "root_can_write_fixture", ())
        return (False, "agent_excluded", ())

    def acs(start, uid, gids):
        return (True, ("fixture_root_reached",))

    return w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


class Rig:
    """A provisioned PRODUCTION test-fixture protected root + one active
    principal + one active bound credential, ready to drive
    ``recognized_certification_read_authority`` / the coordinator."""

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
        self.session_id = "hcs-" + "1" * 32

    def _enroll_credential(self) -> str:
        from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
        from pcae.core.hpac_rhamp_enrollment import enroll_first_credential

        result = enroll_first_credential(
            principal_id=self.principal_id,
            subject_digest="c" * 64,
            presentation_digest="d" * 64,
            invocation_id="iv-n16-5-f5b1-impl",
            attempt_id="at-n16-5-f5b1-impl",
            provider=DeterministicCtap2Provider(),
            protected_root=self.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
        return result.credential_id

    def ra(self, **over):
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
        return w.recognized_certification_read_authority(**kw)


@pytest.fixture
def rig(tmp_path):
    return Rig(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# A. Contract identity / no forbidden changes
# ═══════════════════════════════════════════════════════════════════════════


def test_01_pawa_contract_version_is_v1_4():
    text = (REPO / "docs" / "contracts" / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md").read_text()
    assert text.splitlines()[0].strip().startswith("# HPAC-PAWA-001 v1.4")


def test_02_no_contract_diff_since_i0():
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


def test_05_rhamp_terminal_reason_vocab_unchanged():
    from pcae.core.hpac_rhamp_terminal_reasons import TerminalReasonCode

    assert len(list(TerminalReasonCode)) == 41


def test_06_dependency_set_unchanged_since_i0():
    names = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", I0, "HEAD", "--", "pyproject.toml"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert names == [], names


def test_07_certification_role_allowlist_still_exactly_five():
    assert len(w.CERTIFICATION_ROLE_ALLOWLIST) == 5


# ═══════════════════════════════════════════════════════════════════════════
# B. Factory / §33B recognition
# ═══════════════════════════════════════════════════════════════════════════


def test_10_symbol_exists_and_is_distinct_from_writer_factories():
    assert callable(w.recognized_certification_read_authority)
    assert w.recognized_certification_read_authority is not w.certification_writer
    assert w.recognized_certification_read_authority is not w.production_writer


def test_11_no_new_factory_consumer_category():
    assert w.READ_AUTHORITY_CONSUMERS == w.CERTIFICATION_FACTORY_CONSUMERS
    assert w.READ_AUTHORITY_CONSUMERS == frozenset({"pcae.core.hpac_certification_coordinator"})


def test_12_authorized_consumer_accepted(rig):
    handle = rig.ra()
    assert isinstance(handle, w.CertificationReadAuthority)
    assert handle.certification_session_id == rig.session_id
    assert handle.principal_id == rig.principal_id
    assert handle.credential_id == rig.credential_id


@pytest.mark.parametrize("caller", [
    "pcae.core.agent",
    "pcae.cli",
    "pcae.commands.gate5",
    "pcae.core.protected_presentation",
    "pcae.protected_presentation_helper",
    "pcae.core.hpac_protected_presentation_admin",
    "pcae.core.hpac_verifier",
    "scripts.hpac_certification_admin",
    "pcae.core.hpac_protected_admin_writer",
])
def test_13_wrong_consumer_matrix_denied(rig, caller):
    # N16-5-F-5-B2-IMPL: the disclosed ``_caller_module`` keyword is no
    # longer authoritative, so the negative matrix is now reproduced by
    # making the call genuinely originate from each candidate module name
    # (real caller-provenance detection), not by asserting a string.
    kw = dict(
        certification_session_id=rig.session_id,
        principal_id=rig.principal_id,
        credential_id=rig.credential_id,
        proof_id=rig.proof_id,
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    with pytest.raises(w.PawaError) as ei:
        call_with_real_module_identity(caller, w.recognized_certification_read_authority, **kw)
    assert ei.value.code == "unauthorized_factory_consumer"


def test_14_wildcard_prefix_nearmiss_denied(rig):
    kw = dict(
        certification_session_id=rig.session_id,
        principal_id=rig.principal_id,
        credential_id=rig.credential_id,
        proof_id=rig.proof_id,
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    with pytest.raises(w.PawaError) as ei:
        call_with_real_module_identity(
            "pcae.core.hpac_certification_coordinator.evil",
            w.recognized_certification_read_authority,
            **kw,
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_15_ss33_agent_writable_root_denied(rig):
    def ewa(path, uid, gids):
        return (True, "agent_can_write", ())

    def acs(start, uid, gids):
        return (True, ("ok",))

    with pytest.raises(w.PawaError) as ei:
        rig.ra(_topology_probe=w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs))
    assert ei.value.code == "agent_has_protected_write_authority"


def test_16_unresolvable_agent_denied(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.ra(_configured_agent_identity_source=_agent_src({"someone-else": 5}))
    assert ei.value.code == "agent_principal_unknown"


def test_17_runs_fresh_every_call_no_caching(rig):
    a = rig.ra()
    b = rig.ra()
    assert a is not b


def test_18_no_fallback_to_production_writer_or_direct_authority(rig):
    # Failing the §33B sequence never falls back to a mutation capability
    # or a raw HPACStoreAuthority.production() -- it just raises.
    kw = dict(
        certification_session_id=rig.session_id,
        principal_id=rig.principal_id,
        credential_id=rig.credential_id,
        proof_id=rig.proof_id,
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    with pytest.raises(w.PawaError):
        call_with_real_module_identity("pcae.core.agent", w.recognized_certification_read_authority, **kw)


# ═══════════════════════════════════════════════════════════════════════════
# C. Session-binding negatives (§42E / HPAC-PAWA-REQ-291)
# ═══════════════════════════════════════════════════════════════════════════


def test_20_missing_session_id_rejected(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.ra(certification_session_id="")
    assert ei.value.code == "operation_scope_invalid"


def test_21_none_bypass_rejected(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.ra(principal_id=None)
    assert ei.value.code == "operation_scope_invalid"


def test_22_malformed_proof_id_rejected(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.ra(proof_id="not-a-real-proof-id")
    assert ei.value.code == "operation_scope_invalid"


def test_23_unresolvable_principal_rejected(rig):
    with pytest.raises(w.PawaError) as ei:
        rig.ra(principal_id="hp-" + "0" * 32)
    assert ei.value.code == "operation_scope_invalid"


def test_24_credential_not_bound_to_principal_rejected(rig, tmp_path):
    other = Rig(tmp_path / "other")
    with pytest.raises(w.PawaError) as ei:
        rig.ra(credential_id=other.credential_id)
    assert ei.value.code == "operation_scope_invalid"


def test_25_revoked_principal_rejected(rig):
    from pcae.core.hpac_protected_admin_writer import revoke_principal_via_pawa

    revoke_principal_via_pawa(
        principal_id=rig.principal_id,
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    with pytest.raises(w.PawaError) as ei:
        rig.ra()
    assert ei.value.code == "operation_scope_invalid"


# ═══════════════════════════════════════════════════════════════════════════
# D. Handle construction / forgery / non-bearer (§46/§47/§68B)
# ═══════════════════════════════════════════════════════════════════════════


def test_30_direct_construction_denied(rig):
    with pytest.raises(HPACAuthorityError):
        w.CertificationReadAuthority(
            _factory_seal=object(),
            authority=rig.authority,
            certification_session_id=rig.session_id,
            principal_id=rig.principal_id,
            credential_id=rig.credential_id,
            proof_id=rig.proof_id,
            anchor_id="a",
            installation_id="i",
            descriptor_generation=1,
        )


def test_31_object_new_forgery_unusable(rig):
    shell = object.__new__(w.CertificationReadAuthority)
    # No __init__ ran: none of the bound-state slots are set, so every
    # public method fails closed (AttributeError on the unset slot) rather
    # than operating on attacker-controlled defaults.
    with pytest.raises(AttributeError):
        shell.read_principal_and_credential()


def test_32_non_serializable(rig):
    handle = rig.ra()
    import pickle

    with pytest.raises(TypeError):
        pickle.dumps(handle)
    import copy

    with pytest.raises(TypeError):
        copy.deepcopy(handle)


def test_33_no_raw_authority_escape_public_surface(rig):
    handle = rig.ra()
    public = [name for name in dir(handle) if not name.startswith("_")]
    for name in public:
        assert name not in (
            "authority", "store_authority", "raw", "unwrap", "get_authority", "as_store_authority",
        )
    # No public attribute returns an HPACStoreAuthority.
    for name in public:
        value = getattr(handle, name)
        assert not isinstance(value, HPACStoreAuthority)


def test_34_no_writer_mint_or_certification_methods_exposed(rig):
    handle = rig.ra()
    for name in ("writer", "production_writer", "certification_writer", "mint", "delegate", "clone", "transfer"):
        assert not hasattr(handle, name)


def test_35_wrapped_authority_writer_still_denied(rig):
    # Defence in depth: even if a caller obtained the wrapped authority via
    # reflection, HPACStoreAuthority.writer() still raises for PRODUCTION.
    handle = rig.ra()
    inner = object.__getattribute__(handle, "_authority")
    with pytest.raises(HPACAuthorityError):
        inner.writer("human_authentication_proof_verifier", subject="x")


def test_36_slots_only_no_dict_injection(rig):
    handle = rig.ra()
    assert not hasattr(handle, "__dict__")


# ═══════════════════════════════════════════════════════════════════════════
# E. §42D closed read scope -- positives
# ═══════════════════════════════════════════════════════════════════════════


def test_40_read_principal_and_credential(rig):
    handle = rig.ra()
    principal, credential = handle.read_principal_and_credential()
    assert principal.principal_id == rig.principal_id
    assert credential.credential_id == rig.credential_id
    assert credential.principal_id == rig.principal_id


def test_41_read_credential_sidecar_and_counter(rig):
    handle = rig.ra()
    sidecar, counter = handle.read_credential_sidecar_and_counter()
    assert sidecar.credential_id == rig.credential_id
    assert counter.credential_id == rig.credential_id


def test_42_read_presentation_state_no_prior_presentation(rig):
    handle = rig.ra()
    descriptor, installation, presentation = handle.read_presentation_state(mechanism_id="pcae-protected-local-presentation")
    assert presentation is None


def test_43_reads_do_not_return_resolved_record_wrapper_with_seal(rig):
    handle = rig.ra()
    principal, credential = handle.read_principal_and_credential()
    assert not hasattr(principal, "authority_seal")
    assert not hasattr(credential, "authority_seal")


def test_44_multiple_reads_within_session_allowed(rig):
    handle = rig.ra()
    handle.read_principal_and_credential()
    handle.read_principal_and_credential()
    handle.read_credential_sidecar_and_counter()


# ═══════════════════════════════════════════════════════════════════════════
# F. §42D closed read scope -- negatives / no mutation
# ═══════════════════════════════════════════════════════════════════════════


def test_50_no_counter_transition_method(rig):
    handle = rig.ra()
    assert not hasattr(handle, "apply_after_verification")
    assert not hasattr(handle, "update_counter")
    assert not hasattr(handle, "reset_counter")


def test_51_no_generic_read_method(rig):
    handle = rig.ra()
    for name in ("read", "read_any_record", "resolve_arbitrary", "open_store", "filesystem_read"):
        assert not hasattr(handle, name)


def test_52_presentation_read_rejects_empty_mechanism(rig):
    handle = rig.ra()
    with pytest.raises(w.PawaError) as ei:
        handle.read_presentation_state(mechanism_id="")
    assert ei.value.code == "operation_scope_invalid"


def test_53_presentation_read_rejects_half_specified_prior_presentation(rig):
    handle = rig.ra()
    with pytest.raises(w.PawaError) as ei:
        handle.read_presentation_state(mechanism_id="m", presentation_id="p-1", presentation_digest=None)
    assert ei.value.code == "operation_scope_invalid"


def test_54_sidecar_read_denied_for_unrelated_credential(rig):
    handle = rig.ra()
    from pcae.core.hpac_rhamp_credential_sidecar import HpacRhampCredentialSidecarStore

    result = HpacRhampCredentialSidecarStore(handle._authority).resolve_canonical("hpc-" + "0" * 32)
    assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# G. F-5-B1 mechanical repair -- ambient root vs configured-agent binding
# ═══════════════════════════════════════════════════════════════════════════


def test_60_unbound_direct_read_denied_under_ambient_root(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.hatp_class_b_topology_verifier._current_agent_identity",
        lambda: (0, frozenset()),
    )
    unbound = HPACStoreAuthority._production_test_fixture(
        rig.root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_root_repro_probe()
    )
    with pytest.raises(HPACAuthorityError):
        HumanPrincipalRegistryStore(unbound).resolve_canonical_principal(rig.principal_id)


def test_61_recognized_read_authority_succeeds_under_same_ambient_root(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.hatp_class_b_topology_verifier._current_agent_identity",
        lambda: (0, frozenset()),
    )
    handle = rig.ra(_topology_probe=_root_repro_probe())
    principal, credential = handle.read_principal_and_credential()
    assert principal.principal_id == rig.principal_id


def test_62_ambient_direct_read_remains_denied_after_recognized_session(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.hatp_class_b_topology_verifier._current_agent_identity",
        lambda: (0, frozenset()),
    )
    rig.ra(_topology_probe=_root_repro_probe())
    still_unbound = HPACStoreAuthority._production_test_fixture(
        rig.root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_root_repro_probe()
    )
    with pytest.raises(HPACAuthorityError):
        HumanPrincipalRegistryStore(still_unbound).resolve_canonical_principal(rig.principal_id)


def test_63_bind_does_not_leak_into_a_fresh_unrelated_authority(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.hatp_class_b_topology_verifier._current_agent_identity",
        lambda: (0, frozenset()),
    )
    rig.ra(_topology_probe=_root_repro_probe())
    fresh = HPACStoreAuthority._production_test_fixture(
        rig.root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_root_repro_probe()
    )
    assert fresh._configured_agent_identity is None


def test_64_bind_removed_after_exception_does_not_apply_here_new_instance_per_call(rig, monkeypatch):
    # Each recognized_certification_read_authority call builds a fresh
    # HPACStoreAuthority instance (§33 step 1); a failure in one call
    # cannot leave a stale bind on a later instance because there is no
    # shared mutable authority object across calls.
    monkeypatch.setattr(
        "pcae.core.hatp_class_b_topology_verifier._current_agent_identity",
        lambda: (0, frozenset()),
    )
    with pytest.raises(w.PawaError):
        rig.ra(_topology_probe=_root_repro_probe(), principal_id="hp-" + "9" * 32)
    handle = rig.ra(_topology_probe=_root_repro_probe())
    handle.read_principal_and_credential()


# ═══════════════════════════════════════════════════════════════════════════
# H. Ceremony entry (§42D/§49B) -- single use, replay, walls
# ═══════════════════════════════════════════════════════════════════════════


def _ceremony_kwargs():
    return dict(
        approval_id="appr-1",
        challenge_id="chal-1",
        canonical_subject=object(),
        human_visible_facts={"k": "v"},
        invocation_id="iv-1",
        attempt_id="at-1",
    )


def test_70_ceremony_entry_calls_production_boundary_exactly_once(rig, monkeypatch):
    calls = []

    def fake_ceremony(**kwargs):
        calls.append(kwargs)
        return "SENTINEL_RESULT"

    monkeypatch.setattr(
        "pcae.core.protected_presentation.run_protected_presentation_ceremony", fake_ceremony
    )
    handle = rig.ra()
    result = handle.enter_ceremony(**_ceremony_kwargs())
    assert result == "SENTINEL_RESULT"
    assert len(calls) == 1
    assert calls[0]["authority"] is handle._authority
    assert calls[0]["principal_id"] == rig.principal_id


def test_71_second_ceremony_entry_denied(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.protected_presentation.run_protected_presentation_ceremony",
        lambda **kw: "ok",
    )
    handle = rig.ra()
    handle.enter_ceremony(**_ceremony_kwargs())
    with pytest.raises(w.PawaError) as ei:
        handle.enter_ceremony(**_ceremony_kwargs())
    assert ei.value.code == "capability_stale"


def test_72_reads_denied_after_ceremony_entered(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.protected_presentation.run_protected_presentation_ceremony",
        lambda **kw: "ok",
    )
    handle = rig.ra()
    handle.enter_ceremony(**_ceremony_kwargs())
    with pytest.raises(w.PawaError) as ei:
        handle.read_principal_and_credential()
    assert ei.value.code == "capability_stale"


def test_73_ceremony_spent_even_if_underlying_ceremony_raises(rig, monkeypatch):
    def boom(**kw):
        raise RuntimeError("simulated ceremony failure")

    monkeypatch.setattr("pcae.core.protected_presentation.run_protected_presentation_ceremony", boom)
    handle = rig.ra()
    with pytest.raises(RuntimeError):
        handle.enter_ceremony(**_ceremony_kwargs())
    with pytest.raises(w.PawaError) as ei:
        handle.enter_ceremony(**_ceremony_kwargs())
    assert ei.value.code == "capability_stale"


def test_74_second_accessor_call_reruns_full_recognition(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.protected_presentation.run_protected_presentation_ceremony",
        lambda **kw: "ok",
    )
    first = rig.ra()
    first.enter_ceremony(**_ceremony_kwargs())
    second = rig.ra()
    assert second is not first
    result = second.enter_ceremony(**_ceremony_kwargs())
    assert result == "ok"


def test_75_ceremony_entry_takes_no_test_decision_source_parameter(rig):
    handle = rig.ra()
    with pytest.raises(TypeError):
        handle.enter_ceremony(_test_decision_source="APPROVE", **_ceremony_kwargs())


def test_76_ceremony_cannot_manufacture_evidence_directly(rig):
    handle = rig.ra()
    for name in ("mint_evidence", "write_evidence", "seal_evidence", "persist_evidence"):
        assert not hasattr(handle, name)


# ═══════════════════════════════════════════════════════════════════════════
# I. Coordinator integration (§38B sole consumer path)
# ═══════════════════════════════════════════════════════════════════════════


def _coord(rig):
    return cc.HpacCertificationCoordinator(
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )


def test_80_coordinator_is_sole_read_authority_consumer_constant():
    assert w.READ_AUTHORITY_CONSUMERS == frozenset({"pcae.core.hpac_certification_coordinator"})


def test_81_coordinator_run_presentation_ceremony_success(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.protected_presentation.run_protected_presentation_ceremony",
        lambda **kw: "COORD_SENTINEL",
    )
    coordinator = _coord(rig)
    session = coordinator.begin_session(
        principal_id=rig.principal_id, credential_id=rig.credential_id, proof_id=rig.proof_id
    )
    result = session.run_presentation_ceremony(**_ceremony_kwargs())
    assert result == "COORD_SENTINEL"


def test_82_coordinator_run_presentation_ceremony_second_call_denied(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.protected_presentation.run_protected_presentation_ceremony",
        lambda **kw: "ok",
    )
    coordinator = _coord(rig)
    session = coordinator.begin_session(
        principal_id=rig.principal_id, credential_id=rig.credential_id, proof_id=rig.proof_id
    )
    session.run_presentation_ceremony(**_ceremony_kwargs())
    with pytest.raises(cc.CertificationCoordinatorError):
        session.run_presentation_ceremony(**_ceremony_kwargs())


def test_83_coordinator_wrong_consumer_module_denied(tmp_path, rig, monkeypatch):
    """POST-REPAIR (N16-5-F-5-B2-IMPL): the coordinator's own
    ``_caller_module`` constructor seam forwards straight into the (now
    non-authoritative) factory keyword -- it can no longer make the REAL
    coordinator either impersonate a different consumer or be denied as
    one. The coordinator's genuine module identity (itself the sole §38B
    consumer) always governs. This test's name is retained; it now proves
    exactly that: setting the seam to an arbitrary unauthorized-looking
    name has NO effect on the outcome -- the call still succeeds, exactly
    as it does with no seam at all (test_81)."""
    monkeypatch.setattr(
        "pcae.core.protected_presentation.run_protected_presentation_ceremony",
        lambda **kw: "COORD_SENTINEL",
    )
    coordinator = cc.HpacCertificationCoordinator(
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
        _caller_module="pcae.core.agent",
    )
    session = coordinator.begin_session(
        principal_id=rig.principal_id, credential_id=rig.credential_id, proof_id=rig.proof_id
    )
    result = session.run_presentation_ceremony(**_ceremony_kwargs())
    assert result == "COORD_SENTINEL"


def test_84_coordinator_never_exposes_read_authority_object(rig, monkeypatch):
    monkeypatch.setattr(
        "pcae.core.protected_presentation.run_protected_presentation_ceremony",
        lambda **kw: "ok",
    )
    coordinator = _coord(rig)
    session = coordinator.begin_session(
        principal_id=rig.principal_id, credential_id=rig.credential_id, proof_id=rig.proof_id
    )
    result = session.run_presentation_ceremony(**_ceremony_kwargs())
    assert not isinstance(result, w.CertificationReadAuthority)
    assert not hasattr(session, "read_authority")
    assert not hasattr(session, "_read_authority")


# ═══════════════════════════════════════════════════════════════════════════
# J. Consumer-inventory / import guards (§39/§39A/§282 pattern)
# ═══════════════════════════════════════════════════════════════════════════


def test_90_read_authority_symbol_not_imported_by_agent_reachable_code():
    forbidden_roots = [REPO / "src" / "pcae" / "cli.py", REPO / "src" / "pcae" / "core" / "agent.py"]
    commands_dir = REPO / "src" / "pcae" / "commands"
    files = list(forbidden_roots)
    if commands_dir.is_dir():
        files += list(commands_dir.rglob("*.py"))
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text()
        assert "recognized_certification_read_authority" not in text, path
        assert "CertificationReadAuthority" not in text, path


def test_91_read_authority_test_consumer_allowlist_is_test_only():
    assert w._READ_AUTHORITY_TEST_CONSUMERS == frozenset({THIS_MODULE})


def test_92_test_fixture_module_is_not_a_production_consumer():
    assert THIS_MODULE not in w.READ_AUTHORITY_CONSUMERS
    assert THIS_MODULE in w._READ_AUTHORITY_TEST_CONSUMERS


def test_93_coordinator_module_not_imported_by_cli_or_agent():
    for path in (REPO / "src" / "pcae" / "cli.py", REPO / "src" / "pcae" / "core" / "agent.py"):
        if path.is_file():
            assert "hpac_certification_coordinator" not in path.read_text()


# ═══════════════════════════════════════════════════════════════════════════
# K. H-3 non-regression (§68B / §77 of the phase prompt)
# ═══════════════════════════════════════════════════════════════════════════


def test_95_certification_writer_still_mints_for_h3_roles(rig):
    # This suite's own real module name is a disclosed
    # ``_READ_AUTHORITY_TEST_CONSUMERS`` member, not a
    # ``_CERTIFICATION_TEST_CONSUMERS`` one -- so a direct
    # ``certification_writer`` call needs a genuine real-caller-identity
    # simulation (the disclosed ``_caller_module`` keyword is no longer
    # authoritative for either allowlist).
    handle = call_with_real_module_identity(
        COORDINATOR_MODULE,
        w.certification_writer,
        "hpac_challenge_coordinator",
        certification_session_id=rig.session_id,
        principal_id=rig.principal_id,
        credential_id=rig.credential_id,
        proof_id=rig.proof_id,
        _protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    assert isinstance(handle, w.CertificationWriterHandle)
    assert handle.role == "hpac_challenge_coordinator"


def test_96_five_role_family_unchanged():
    assert w.CERTIFICATION_ROLE_ALLOWLIST == frozenset({
        "hpac_challenge_coordinator",
        "hpac_assertion_recorder",
        "human_authentication_proof_verifier",
        "hpac_gate5_binder",
        "hpac_rhamp_counter_state_verifier",
    })


def test_97_read_authority_grants_no_certification_writer_role(rig):
    handle = rig.ra()
    for role in w.CERTIFICATION_ROLE_ALLOWLIST:
        assert not hasattr(handle, role)


# ═══════════════════════════════════════════════════════════════════════════
# L. Runtime / no-effect (§79/§80/§38 of the phase prompt)
# ═══════════════════════════════════════════════════════════════════════════


def test_99_no_dispatch_or_runtime_symbol_referenced_in_new_code():
    text = (REPO / "src" / "pcae" / "core" / "hpac_protected_admin_writer.py").read_text()
    section = text.split("recognized_certification_read_authority", 1)[-1]
    for forbidden in ("DispatchEnvelope", "adapter.dispatch", "runtime_capability"):
        assert forbidden not in section
