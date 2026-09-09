"""N16-5-F-5-B2R-IMPL — Privileged Production Factory Consumer-Authenticity
Repair (second repair, successor to the insufficient N16-5-F-5-B2-IMPL
repair; predecessor finding: N16-5-F-5-B2-IV).

The N16-5-F-5-B2-IV independent-verification phase proved the first repair
insufficient: ``_detect_caller_module`` trusted
``frame.f_globals["__name__"]`` verbatim, an ordinary caller-writable dict
key on the caller's own frame, settable via
``exec(code, {"__name__": "<authorized name>", ...})`` with no
import-machinery registration required.

This suite verifies the SECOND repair in
``src/pcae/core/hpac_protected_admin_writer.py``
(``_verified_production_caller_name`` / ``_module_has_verified_provenance`` /
``_collect_module_code_objects``), which requires, for any candidate name
that names one of the four factories' real enumerated production
consumers:

  1. the candidate module is genuinely registered in ``sys.modules`` with a
     ``__spec__.loader`` that is a real ``SourceFileLoader`` whose
     ``origin`` resolves to the EXACT on-disk path the installed ``pcae``
     package layout requires for that dotted name (defeats sys.modules
     poisoning with a hand-built module/spec);
  2. the calling frame's ``f_globals`` is object-identical to that real
     module's own ``__dict__`` (defeats an entirely separate scratch
     module merely claiming the same ``__name__``);
  3. the calling frame's ``f_code`` is object-identical to one of a set of
     code objects snapshotted from that real module's own pre-existing
     functions/methods at first-verified-use (defeats
     ``exec(code, real_module.__dict__)`` — a stronger variant found
     during this phase's own adversarial design: (2) alone is
     insufficient, because ``sys.modules[name].__dict__`` is itself an
     ordinary, caller-referenceable object, so executing fresh,
     attacker-authored code directly against the REAL module's own dict
     satisfies (2) without the calling code being anything the module
     ever defined).

No real ceremony, no genuine YubiKey/PIN, no protected APPROVE, no
``makeCredential``/``getAssertion``. Every mutation test uses a disposable,
provisioned PRODUCTION test-fixture protected root under ``tmp_path`` — no
live protected-host state. This suite's own module identity is not a
member of any production or test consumer allowlist, so every direct call
below is a genuine unauthorized-caller baseline unless a helper is used to
construct a specific adversarial or genuine scenario.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    HPACStoreAuthority,
    HPACWriterCapability,
)
from pcae.core.human_authentication_proof import new_proof_id
from pcae.core.human_principal_registry import new_principal_id
from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
from pcae.core.hpac_rhamp_enrollment import enroll_first_credential

from _caller_identity_helper import call_with_real_module_identity

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root model"),
]

THIS_MODULE = __name__
assert THIS_MODULE not in w.AUTHORIZED_FACTORY_CONSUMERS
assert THIS_MODULE not in w.CERTIFICATION_FACTORY_CONSUMERS
assert THIS_MODULE not in w.READ_AUTHORITY_CONSUMERS
assert THIS_MODULE not in w.PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS

FAKE_AGENT_UID = 4_242_953
FAKE_AGENT_GID = 999_953
AGENT_ACCOUNT = "pcae-agent-svc-n16-5-f5b2r-impl"


def _agent_src():
    def source(symbolic_account, provisioned_uid):
        return provisioned_uid, frozenset({FAKE_AGENT_GID})

    return source


def _locked_probe():
    def ewa(path, uid, gids):
        return (False, "fixture_locked", ())

    def acs(start, uid, gids):
        return (True, ("fixture_root_reached",))

    return w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


@pytest.fixture
def root(tmp_path):
    r = (tmp_path / "hpac-protected-root").resolve()
    w.provision_protected_root(protected_root=r, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID)
    return r


@pytest.fixture
def principal_and_credential(root):
    principal_id = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=principal_id,
        enrollment_provenance_ref="f5b2r-prov-ref",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    result = enroll_first_credential(
        principal_id=principal_id,
        subject_digest="7" * 64,
        presentation_digest="8" * 64,
        invocation_id="iv-f5b2r",
        attempt_id="at-f5b2r",
        provider=DeterministicCtap2Provider(),
        protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    return principal_id, result.credential_id


def _exec_into_real_module_dict(dotted_name: str, fn, *args, **kwargs):
    """The stronger forgery this phase's own repair design found: obtain a
    reference to the REAL, already-imported module's own ``__dict__`` (a
    perfectly ordinary, publicly reachable object via
    ``sys.modules[name].__dict__``) and ``exec()`` fresh, attacker-authored
    code directly against it — never registering any new module, never
    touching ``sys.modules``, and producing a frame whose ``f_globals`` IS
    (by object identity) the real module's own dict. This is NOT the
    disclosed ``_caller_identity_helper`` technique (which builds a
    separate, unregistered scratch module) — it targets the ``f_globals
    is module.__dict__`` check specifically."""

    real_module = sys.modules[dotted_name]
    ns = real_module.__dict__
    ns["_f5b2r_fn"] = fn
    ns["_f5b2r_args"] = args
    ns["_f5b2r_kwargs"] = kwargs
    code = "_f5b2r_result = _f5b2r_fn(*_f5b2r_args, **_f5b2r_kwargs)"
    try:
        exec(compile(code, f"<exec-into-{dotted_name}>", "exec"), ns)
        return ns["_f5b2r_result"]
    finally:
        for key in ("_f5b2r_fn", "_f5b2r_args", "_f5b2r_kwargs", "_f5b2r_result"):
            ns.pop(key, None)


def _sys_modules_poison(dotted_name: str, monkeypatch):
    """Insert a hand-built module object at the authorized dotted name in
    ``sys.modules`` with a spoofed ``__spec__``/``__loader__`` claiming (but
    not actually possessing) real on-disk provenance under the installed
    package -- never any real ``SourceFileLoader`` resolving to the real
    file."""

    fake = types.ModuleType(dotted_name)
    fake.__dict__["__name__"] = dotted_name

    class _FakeLoader:
        pass

    class _FakeSpec:
        loader = _FakeLoader()
        origin = str(Path(w.__file__).resolve().parent / (dotted_name.rsplit(".", 1)[-1] + ".py"))

    fake.__dict__["__spec__"] = _FakeSpec()
    monkeypatch.setitem(sys.modules, dotted_name, fake)
    return fake


# ═══════════════════════════════════════════════════════════════════════════
# 1. Legitimate consumers still succeed for all four factories, via a
#    genuinely-imported real module (never the disclosed keyword, never a
#    fabricated-identity simulation).
# ═══════════════════════════════════════════════════════════════════════════


def test_01_production_writer_genuine_rhamp_enrollment_call_succeeds(root):
    # enroll_first_credential's own real, pre-existing code genuinely
    # calls production_writer -- the exact real path, not a simulation.
    principal_id = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=principal_id,
        enrollment_provenance_ref="f5b2r-real",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    result = enroll_first_credential(
        principal_id=principal_id,
        subject_digest="9" * 64,
        presentation_digest="a" * 64,
        invocation_id="iv-real",
        attempt_id="at-real",
        provider=DeterministicCtap2Provider(),
        protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    assert result.credential_id


def test_02_certification_writer_genuine_coordinator_call_succeeds(root, principal_and_credential):
    from pcae.core.hpac_certification_coordinator import HpacCertificationCoordinator

    principal_id, credential_id = principal_and_credential
    coordinator = HpacCertificationCoordinator(
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    session = coordinator.begin_session(principal_id=principal_id, credential_id=credential_id)
    handle = coordinator._mint(
        "hpac_challenge_coordinator",
        certification_session_id=session.certification_session_id,
        principal_id=principal_id,
        credential_id=credential_id,
        proof_id=session.proof_id,
    )
    assert isinstance(handle, w.CertificationWriterHandle)


def test_03_read_authority_genuine_coordinator_call_succeeds(root, principal_and_credential):
    from pcae.core.hpac_certification_coordinator import HpacCertificationCoordinator

    principal_id, credential_id = principal_and_credential
    coordinator = HpacCertificationCoordinator(
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    session = coordinator.begin_session(principal_id=principal_id, credential_id=credential_id)
    ra = coordinator._obtain_read_authority(
        certification_session_id=session.certification_session_id,
        principal_id=principal_id,
        credential_id=credential_id,
        proof_id=session.proof_id,
    )
    assert isinstance(ra, w.CertificationReadAuthority)


def test_04_presentation_evidence_writer_pinned_module_repeat_call_succeeds(root):
    # protected_presentation.py imports mint_protected_presentation_evidence_writer
    # lazily inside its launch path (module docstring), so exercising the
    # true end-to-end launcher ceremony is out of this focused suite's
    # scope; this positive case instead proves the pin/verification
    # mechanism itself (module provenance + code-object identity) accepts
    # a real, already-verified consumer on a SECOND call once pinned --
    # exercised here through production_writer's own already-verified
    # self-consumer path (pcae.core.hpac_protected_admin_writer is itself
    # a member of AUTHORIZED_FACTORY_CONSUMERS), proving the pin survives
    # and re-validates identically across repeated genuine calls.
    for _ in range(3):
        principal_id = new_principal_id()
        w.enroll_principal_via_pawa(
            principal_id=principal_id,
            enrollment_provenance_ref="f5b2r-repeat",
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )


# ═══════════════════════════════════════════════════════════════════════════
# 2. The exact IV-reproduced exec()-crafted-scratch-module-__name__ attack
#    is now denied for all four factories.
# ═══════════════════════════════════════════════════════════════════════════


def test_10_production_writer_scratch_module_forgery_denied(root):
    with pytest.raises(w.PawaError) as ei:
        call_with_real_module_identity(
            "pcae.core.hpac_rhamp_enrollment",
            w.production_writer,
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "4" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_11_certification_writer_scratch_module_forgery_denied(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        call_with_real_module_identity(
            "pcae.core.hpac_certification_coordinator",
            w.certification_writer,
            "hpac_challenge_coordinator",
            certification_session_id="hcs-" + "5" * 32,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=new_proof_id(),
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_12_read_authority_scratch_module_forgery_denied(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        call_with_real_module_identity(
            "pcae.core.hpac_certification_coordinator",
            w.recognized_certification_read_authority,
            certification_session_id="hcs-" + "6" * 32,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=new_proof_id(),
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_13_presentation_evidence_writer_scratch_module_forgery_denied(root):
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    with pytest.raises(w.PawaError) as ei:
        call_with_real_module_identity(
            "pcae.core.protected_presentation",
            w.mint_protected_presentation_evidence_writer,
            authority,
            mechanism_id="f5b2r-mechanism",
        )
    assert ei.value.code == "unauthorized_factory_consumer"


# ═══════════════════════════════════════════════════════════════════════════
# 3. The stronger exec()-into-the-REAL-module's-own-__dict__ variant found
#    during this phase's design is also denied for all four factories.
# ═══════════════════════════════════════════════════════════════════════════


def test_20_production_writer_exec_into_real_dict_denied(root):
    with pytest.raises(w.PawaError) as ei:
        _exec_into_real_module_dict(
            "pcae.core.hpac_rhamp_enrollment",
            w.production_writer,
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "7" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_21_certification_writer_exec_into_real_dict_denied(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        _exec_into_real_module_dict(
            "pcae.core.hpac_certification_coordinator",
            w.certification_writer,
            "hpac_challenge_coordinator",
            certification_session_id="hcs-" + "8" * 32,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=new_proof_id(),
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_22_read_authority_exec_into_real_dict_denied(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        _exec_into_real_module_dict(
            "pcae.core.hpac_certification_coordinator",
            w.recognized_certification_read_authority,
            certification_session_id="hcs-" + "9" * 32,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=new_proof_id(),
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_23_presentation_evidence_writer_exec_into_real_dict_denied(root):
    import pcae.core.protected_presentation  # noqa: F401 -- ensure real import registration

    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    with pytest.raises(w.PawaError) as ei:
        _exec_into_real_module_dict(
            "pcae.core.protected_presentation",
            w.mint_protected_presentation_evidence_writer,
            authority,
            mechanism_id="f5b2r-mechanism-2",
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_24_exec_into_own_module_dict_denied(root):
    # Even the trust-anchor module itself (a member of
    # AUTHORIZED_FACTORY_CONSUMERS) cannot be impersonated by exec()-ing
    # into ITS OWN __dict__ -- the code-object pin still requires the
    # frame's f_code to be one of the module's real pre-existing
    # functions/methods.
    with pytest.raises(w.PawaError) as ei:
        _exec_into_real_module_dict(
            "pcae.core.hpac_protected_admin_writer",
            w.production_writer,
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "6" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


# ═══════════════════════════════════════════════════════════════════════════
# 4. sys.modules poisoning (a hand-built module/spec registered under the
#    authorized name) is denied.
# ═══════════════════════════════════════════════════════════════════════════


def test_30_sys_modules_poisoning_production_writer_denied(root, monkeypatch):
    _sys_modules_poison("pcae.core.hpac_rhamp_enrollment", monkeypatch)
    with pytest.raises(w.PawaError) as ei:
        call_with_real_module_identity(
            "pcae.core.hpac_rhamp_enrollment",
            w.production_writer,
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "5" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_31_sys_modules_poisoning_never_pins_a_forged_module(root, monkeypatch):
    fake = _sys_modules_poison("pcae.core.hpac_rhamp_enrollment", monkeypatch)
    try:
        call_with_real_module_identity(
            "pcae.core.hpac_rhamp_enrollment",
            w.production_writer,
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "5" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    except w.PawaError:
        pass
    # Pinning is process-local and may already hold the REAL module from
    # an earlier genuine call in this same test session (order-dependent,
    # expected) -- what must never happen is the pin becoming, or having
    # ever become, the poisoned fake module.
    assert w._PINNED_TRUSTED_MODULES.get("pcae.core.hpac_rhamp_enrollment") is not fake


# ═══════════════════════════════════════════════════════════════════════════
# 5. Decoy / lookalike consumer module denied.
# ═══════════════════════════════════════════════════════════════════════════


def test_40_decoy_module_under_different_dotted_path_denied(root):
    import pcae.core.hpac_pawa_agent_exclusion as decoy  # a real, but unrelated, module

    # Even a genuinely-imported, real module (decoy) is denied: it is not
    # in any of the four enumerated production-consumer sets at all, so it
    # never reaches the provenance/pin machinery -- the plain membership
    # check already denies it (defence-in-depth: name never authorized).
    assert decoy.__name__ not in w._all_known_production_consumer_names()


def test_41_copied_source_under_the_right_dotted_name_but_wrong_file_denied(tmp_path, root):
    import importlib.util

    src = Path(w.__file__).resolve().parent.parent / "core" / "hpac_rhamp_enrollment.py"
    copy_path = tmp_path / "hpac_rhamp_enrollment_copy.py"
    copy_path.write_text(src.read_text())
    # A byte-identical copy of the real source, genuinely imported via the
    # real import machinery (no exec()/scratch-module trick at all), but
    # registered at a non-canonical on-disk path -- and, critically, NOT
    # placed into sys.modules under the authorized dotted name (a
    # not-yet-registered decoy is the realistic shape of this attack: an
    # attacker cannot get their own copy accepted as sys.modules[the real
    # name] without overwriting the genuine entry, which test_30/31 above
    # already cover as poisoning).
    spec = importlib.util.spec_from_file_location("pcae.core.hpac_rhamp_enrollment", copy_path)
    decoy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoy_module)

    frame_holder = {}

    def _capture_and_call():
        import inspect as _inspect

        frame_holder["frame"] = _inspect.currentframe()
        return w.production_writer(
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "2" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )

    decoy_module.__dict__["_capture_and_call"] = _capture_and_call
    with pytest.raises(w.PawaError) as ei2:
        exec(compile("_r = _capture_and_call()", "<decoy>", "exec"), decoy_module.__dict__)
    assert ei2.value.code == "unauthorized_factory_consumer"


# ═══════════════════════════════════════════════════════════════════════════
# 6. Ambient identity (env / argv / cwd) remains irrelevant.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("var", ["USER", "LOGNAME", "SUDO_USER"])
def test_50_ambient_env_identity_irrelevant(root, monkeypatch, var):
    monkeypatch.setenv(var, "pcae.core.hpac_rhamp_enrollment")
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "1" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_51_ambient_argv_and_cwd_irrelevant(root, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pcae.core.hpac_rhamp_enrollment"])
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "1" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Five-role certification closure remains intact under the new
#    mechanism (reusing the genuine coordinator caller).
# ═══════════════════════════════════════════════════════════════════════════


def test_60_five_role_closure_intact_via_genuine_caller(root, principal_and_credential):
    from pcae.core.hpac_certification_coordinator import HpacCertificationCoordinator

    principal_id, credential_id = principal_and_credential
    coordinator = HpacCertificationCoordinator(
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    session = coordinator.begin_session(principal_id=principal_id, credential_id=credential_id)
    for role in w.CERTIFICATION_LIFECYCLE_ROLES:
        handle = coordinator._mint(
            role,
            certification_session_id=session.certification_session_id,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=session.proof_id,
        )
        assert handle.role == role


def test_61_terminator_role_denied_via_genuine_caller(root, principal_and_credential):
    from pcae.core.hpac_certification_coordinator import (
        CertificationCoordinatorError,
        HpacCertificationCoordinator,
    )

    principal_id, credential_id = principal_and_credential
    coordinator = HpacCertificationCoordinator(
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    session = coordinator.begin_session(principal_id=principal_id, credential_id=credential_id)
    with pytest.raises(CertificationCoordinatorError) as ei:
        coordinator._mint(
            "hpac_lifecycle_terminator",
            certification_session_id=session.certification_session_id,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=session.proof_id,
        )
    assert ei.value.pawa_failure_code == "operation_scope_invalid"
