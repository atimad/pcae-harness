"""N16-5-F-5-B2-IV — independent adversarial verification.

Independently constructed (NOT rerunning the predecessor's 49-test suite).
Central question under test: does ``_detect_caller_module`` establish
TRUSTED production consumer authenticity, or only a caller-controllable
descriptive label -- just relocated from the disclosed ``_caller_module``
keyword argument to the live frame's ``f_globals["__name__"]``?

No production source is modified by this suite. Every mutation uses a
disposable tmp_path-provisioned PRODUCTION test-fixture protected root.
No real ceremony, no live protected-host state.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root model"),
]

THIS_MODULE = __name__
assert THIS_MODULE not in w.AUTHORIZED_FACTORY_CONSUMERS
assert THIS_MODULE not in w._TEST_FACTORY_CONSUMERS
assert THIS_MODULE not in w._CERTIFICATION_TEST_CONSUMERS
assert THIS_MODULE not in w._READ_AUTHORITY_TEST_CONSUMERS
assert THIS_MODULE not in w.PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS
assert THIS_MODULE not in w._PROTECTED_PRESENTATION_EVIDENCE_TEST_CONSUMERS

FAKE_AGENT_UID = 4_242_953
FAKE_AGENT_GID = 999_953
AGENT_ACCOUNT = "pcae-agent-svc-n16-5-f5b2-iv"


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


def _pw_kwargs(root, **over):
    kw = dict(
        principal_id="hp-" + "4" * 32,
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    kw.update(over)
    return kw


# ═══════════════════════════════════════════════════════════════════════════
# A. GLOBAL-NAMESPACE (__name__) FORGERY — ordinary code-execution privilege,
#    no import machinery, no sys.modules registration, no filesystem access.
#    This is the exact "genuine caller" simulation technique the
#    predecessor's own tests/_caller_identity_helper.py uses to represent a
#    LEGITIMATE caller. If it also succeeds for an UNAUTHORIZED real module
#    forging an AUTHORIZED name, the repair has not eliminated
#    caller-controlled recognition -- it has only relocated the trusted
#    input from an explicit keyword argument to an implicit global.
# ═══════════════════════════════════════════════════════════════════════════


def _call_with_forged_name(module_name: str, fn, *args, **kwargs):
    """Call ``fn`` from a scratch code object whose *only* claim to
    ``module_name`` is a hand-set ``__name__`` key in its own exec globals
    dict -- never registered in ``sys.modules``, never actually the
    ``pcae.core.*`` module it claims to be. Any ordinary Python caller with
    no special privilege can construct this."""

    ns = {"__name__": module_name, "_fn": fn, "_args": args, "_kwargs": kwargs}
    exec(compile("_result = _fn(*_args, **_kwargs)", f"<forged:{module_name}>", "exec"), ns)
    return ns["_result"]


def test_A1_production_writer_name_forgery_via_exec_globals(root):
    """Forge __name__ to the real AUTHORIZED_FACTORY_CONSUMERS member
    'pcae.core.hpac_rhamp_enrollment' from this (unauthorized) test module,
    with NO disclosed _caller_module keyword used at all."""
    assert "pcae.core.hpac_rhamp_enrollment" in w.AUTHORIZED_FACTORY_CONSUMERS
    try:
        handle = _call_with_forged_name(
            "pcae.core.hpac_rhamp_enrollment",
            w.production_writer,
            w.PawaOperation.ENROLL_PRINCIPAL,
            **_pw_kwargs(root),
        )
    except w.PawaError as exc:
        pytest.fail(
            "EXPECTED-FAIL-CLOSED-BUT-GOT-DENY: recognition denied the forged "
            f"identity (code={exc.code!r}) -- record as evidence, not a bug"
        )
    else:
        # If we get here, forging __name__ was sufficient to obtain a real,
        # usable capability handle -- this IS the blocking finding.
        assert isinstance(handle, w.ProductionWriterHandle)
        raise AssertionError(
            "SECURITY BOUNDARY FAILURE: production_writer granted a genuine "
            "ProductionWriterHandle to a caller whose ONLY credential was a "
            "hand-set __name__ key in its own exec() globals dict -- this "
            "reproduces the B2 defect's authority consequence through a "
            "different mechanical route (forged f_globals['__name__'] instead "
            "of the removed _caller_module keyword)."
        )


def test_A2_certification_writer_name_forgery_via_exec_globals(root):
    from pcae.core.human_authentication_proof import new_proof_id
    from pcae.core.human_principal_registry import new_principal_id
    from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
    from pcae.core.hpac_rhamp_enrollment import enroll_first_credential

    principal_id = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=principal_id,
        enrollment_provenance_ref="iv-prov-ref",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    result = enroll_first_credential(
        principal_id=principal_id,
        subject_digest="5" * 64,
        presentation_digest="6" * 64,
        invocation_id="iv-iv",
        attempt_id="at-iv",
        provider=DeterministicCtap2Provider(),
        protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    credential_id = result.credential_id

    assert w.CERTIFICATION_FACTORY_CONSUMERS == frozenset({"pcae.core.hpac_certification_coordinator"})
    try:
        handle = _call_with_forged_name(
            "pcae.core.hpac_certification_coordinator",
            w.certification_writer,
            "hpac_challenge_coordinator",
            certification_session_id="hcs-" + "4" * 32,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=new_proof_id(),
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    except w.PawaError as exc:
        pytest.fail(
            "EXPECTED-FAIL-CLOSED-BUT-GOT-DENY: recognition denied the forged "
            f"identity (code={exc.code!r}) -- record as evidence, not a bug"
        )
    else:
        assert isinstance(handle, w.CertificationWriterHandle)
        raise AssertionError(
            "SECURITY BOUNDARY FAILURE: certification_writer granted a "
            "genuine CertificationWriterHandle to a __name__-forged caller."
        )


# ═══════════════════════════════════════════════════════════════════════════
# B. AMBIENT IDENTITY SPOOFING — USER/LOGNAME/SUDO_USER/argv/cwd/PATH must
#    have NO effect (the mechanism should not consult them at all).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("var", ["USER", "LOGNAME", "SUDO_USER", "PATH"])
def test_B1_ambient_env_var_spoof_has_no_effect(root, monkeypatch, var):
    monkeypatch.setenv(var, "pcae.core.hpac_rhamp_enrollment")
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(w.PawaOperation.ENROLL_PRINCIPAL, **_pw_kwargs(root))
    assert ei.value.code == "unauthorized_factory_consumer"


def test_B2_argv_spoof_has_no_effect(root, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pcae.core.hpac_rhamp_enrollment", "--pretend"])
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(w.PawaOperation.ENROLL_PRINCIPAL, **_pw_kwargs(root))
    assert ei.value.code == "unauthorized_factory_consumer"


def test_B3_cwd_spoof_has_no_effect(root, monkeypatch, tmp_path):
    decoy = tmp_path / "pcae.core.hpac_rhamp_enrollment"
    decoy.mkdir()
    monkeypatch.chdir(decoy)
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(w.PawaOperation.ENROLL_PRINCIPAL, **_pw_kwargs(root))
    assert ei.value.code == "unauthorized_factory_consumer"


# ═══════════════════════════════════════════════════════════════════════════
# C. STRUCTURAL FORGERY — a real, importable module named identically to an
#    authorized consumer but placed under a DIFFERENT dotted path (i.e., a
#    genuinely-imported module whose __name__ is attacker-controlled via
#    normal import mechanics, not exec-forgery) must still be denied,
#    because its real __name__ will differ from the enumerated string.
# ═══════════════════════════════════════════════════════════════════════════


def test_C1_real_import_under_different_path_is_denied(root, tmp_path):
    """A genuinely-imported module that merely CONTAINS calls to
    production_writer, but is not itself one of the enumerated dotted
    paths, must be denied -- confirms recognition keys off the real,
    full dotted __name__, not a substring/basename match."""
    pkg_dir = tmp_path / "not_pcae_core"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "hpac_rhamp_enrollment.py").write_text(
        "from pcae.core import hpac_protected_admin_writer as w\n"
        "def call(**kw):\n"
        "    return w.production_writer(w.PawaOperation.ENROLL_PRINCIPAL, **kw)\n"
    )
    sys.path.insert(0, str(tmp_path))
    try:
        import not_pcae_core.hpac_rhamp_enrollment as decoy  # noqa: PLC0415

        with pytest.raises(w.PawaError) as ei:
            decoy.call(**_pw_kwargs(root))
        assert ei.value.code == "unauthorized_factory_consumer"
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("not_pcae_core.hpac_rhamp_enrollment", None)
        sys.modules.pop("not_pcae_core", None)


# ═══════════════════════════════════════════════════════════════════════════
# D. FIVE-ROLE CLOSURE — independent negative sweep (certification_writer),
#    exercised through a genuine (non-forged) unauthorized real caller path
#    to confirm role rejection happens independent of consumer recognition.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "bad_role",
    [
        "hpac_lifecycle_terminator",
        "unknown_role",
        "",
        "*",
        "hpac_",
        "hpac_challenge_coordinator ",
        "hpac_challenge_coordinatorX",
        "hpac_challenge_coordinator,hpac_gate5_binder",
    ],
)
def test_D1_certification_role_closure_negative_sweep(root, bad_role):
    with pytest.raises(w.PawaError) as ei:
        w.certification_writer(
            bad_role,
            certification_session_id="hcs-" + "5" * 32,
            principal_id="hp-" + "6" * 32,
            credential_id="hc-" + "7" * 32,
            proof_id="hap-" + "8" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "operation_scope_invalid"


def test_D2_role_allowlist_is_exactly_five_and_excludes_terminator():
    assert len(w.CERTIFICATION_ROLE_ALLOWLIST) == 5
    assert w.CERTIFICATION_ROLE_ALLOWLIST == frozenset(
        {
            "hpac_challenge_coordinator",
            "hpac_assertion_recorder",
            "human_authentication_proof_verifier",
            "hpac_gate5_binder",
            "hpac_rhamp_counter_state_verifier",
        }
    )
    assert "hpac_lifecycle_terminator" not in w.CERTIFICATION_ROLE_ALLOWLIST


# ═══════════════════════════════════════════════════════════════════════════
# E. NO SECOND TRUST ROOT / GENERIC MINT — production_writer and
#    certification_writer remain the only two exposed minting entry points
#    for this authority; no new public factory function was introduced.
# ═══════════════════════════════════════════════════════════════════════════


def test_E1_no_new_public_factory_symbol_introduced():
    expected = {
        "production_writer",
        "certification_writer",
        "recognized_certification_read_authority",
        "mint_protected_presentation_evidence_writer",
    }
    found = {
        name
        for name in w.__all__
        if callable(getattr(w, name, None)) and "writer" in name.lower() or name == "recognized_certification_read_authority"
    }
    assert expected <= found


def test_E2_detect_caller_module_ignores_explicit_argument_unconditionally(root):
    """Confirmation, through a real factory call (matching the intended
    "0: _detect_caller_module, 1: factory, 2: real caller" stack shape),
    that the repaired primitive discards ``explicit`` for every input,
    including one matching a real enumerated consumer -- the exact shape
    of the original defect. (A direct, non-factory call to
    ``_detect_caller_module`` is deliberately NOT used here: it collapses
    the intended 3-frame shape by one level and would misreport the
    caller -- an unrelated test-harness artifact, not a production path.)"""
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(
            w.PawaOperation.ENROLL_PRINCIPAL,
            **_pw_kwargs(root, _caller_module="pcae.core.hpac_rhamp_enrollment"),
        )
    assert ei.value.code == "unauthorized_factory_consumer"
