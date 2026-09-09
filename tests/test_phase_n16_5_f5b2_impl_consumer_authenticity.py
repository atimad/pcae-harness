"""N16-5-F-5-B2-IMPL — Privileged Production Factory Consumer-Authenticity
Repair: dedicated regression suite.

Verifies the repair of the N16-5-F-5-B2 finding (confirmed and extended
from the F-5-B1-IV finding) in
``src/pcae/core/hpac_protected_admin_writer.py``: the disclosed
``_caller_module`` keyword-argument seam on the four privileged factories

  * ``production_writer``
  * ``certification_writer``
  * ``recognized_certification_read_authority``
  * ``mint_protected_presentation_evidence_writer``

was returned verbatim by the shared ``_detect_caller_module`` helper and
therefore satisfied the §38 / §38A / §38B / HPAC-PPA-REQ-041 enumerated
production-consumer allowlists for ANY in-process caller. The repair makes
``_detect_caller_module`` unconditionally use real call-stack provenance
(``inspect.stack()`` over ``frame.f_globals["__name__"]``) and never
return, or otherwise consult, the caller-supplied string.

This suite's own module is deliberately NOT enumerated in any production
or test consumer allowlist (see the assertions immediately below the
imports), so every "spoof" attempt here is a genuine unauthorized-caller
reproduction, never a disclosed test seam being exercised legitimately.
Real, distinct caller-module identities are simulated only via
``call_with_real_module_identity`` (real caller-provenance detection),
never via the disclosed keyword.

No real ceremony, no genuine YubiKey / PIN, no protected APPROVE, no
``makeCredential`` / ``getAssertion``. Every mutation test uses a
disposable, provisioned PRODUCTION test-fixture protected root under
``tmp_path`` -- no live protected-host state.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
    HPACWriterCapability,
)
from pcae.core.human_authentication_proof import new_proof_id
from pcae.core.human_principal_registry import HumanPrincipalRegistryStore, new_principal_id
from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
from pcae.core.hpac_rhamp_enrollment import enroll_first_credential

from _caller_identity_helper import call_with_real_module_identity

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root model"),
]

REPO = Path(__file__).resolve().parents[1]

FAKE_AGENT_UID = 4_242_952
FAKE_AGENT_GID = 999_952
AGENT_ACCOUNT = "pcae-agent-svc-n16-5-f5b2-impl"

#: This suite's own real caller identity (via genuine stack inspection) --
#: deliberately not a member of any production or test consumer allowlist,
#: so every direct (non-fabricated-identity) call below is a genuine
#: unauthorized-caller baseline.
THIS_MODULE = __name__
assert THIS_MODULE not in w.AUTHORIZED_FACTORY_CONSUMERS
assert THIS_MODULE not in w._TEST_FACTORY_CONSUMERS
assert THIS_MODULE not in w._CERTIFICATION_TEST_CONSUMERS
assert THIS_MODULE not in w._READ_AUTHORITY_TEST_CONSUMERS
assert THIS_MODULE not in w.PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS
assert THIS_MODULE not in w._PROTECTED_PRESENTATION_EVIDENCE_TEST_CONSUMERS


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
        enrollment_provenance_ref="impl-prov-ref",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    result = enroll_first_credential(
        principal_id=principal_id,
        subject_digest="1" * 64,
        presentation_digest="2" * 64,
        invocation_id="iv-impl",
        attempt_id="at-impl",
        provider=DeterministicCtap2Provider(),
        protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    return principal_id, result.credential_id


def _pw_kwargs(root, **over):
    kw = dict(
        principal_id="hp-" + "3" * 32,
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    kw.update(over)
    return kw


def _cw_kwargs(root, principal_id, credential_id, **over):
    kw = dict(
        certification_session_id="hcs-" + "3" * 32,
        principal_id=principal_id,
        credential_id=credential_id,
        proof_id=new_proof_id(),
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    kw.update(over)
    return kw


# ═══════════════════════════════════════════════════════════════════════════
# 1. For each of the 4 factories: naming the exact authorized consumer via
#    the disclosed keyword is denied
# ═══════════════════════════════════════════════════════════════════════════


def test_01_production_writer_named_authorized_consumer_denied(root):
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(
            w.PawaOperation.ENROLL_PRINCIPAL,
            **_pw_kwargs(root, _caller_module="pcae.core.hpac_rhamp_enrollment"),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_02_certification_writer_named_authorized_consumer_denied(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        w.certification_writer(
            "hpac_challenge_coordinator",
            **_cw_kwargs(
                root, principal_id, credential_id,
                _caller_module="pcae.core.hpac_certification_coordinator",
            ),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_03_recognized_read_authority_named_authorized_consumer_denied(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        w.recognized_certification_read_authority(
            **_cw_kwargs(
                root, principal_id, credential_id,
                _caller_module="pcae.core.hpac_certification_coordinator",
            ),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_04_presentation_evidence_writer_named_authorized_consumer_denied(root):
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    with pytest.raises(w.PawaError) as ei:
        w.mint_protected_presentation_evidence_writer(
            authority, mechanism_id="impl-mechanism", _caller_module="pcae.core.protected_presentation"
        )
    assert ei.value.code == "unauthorized_factory_consumer"


# ═══════════════════════════════════════════════════════════════════════════
# 2. For each of the 4 factories: near-miss / prefix / suffix / empty /
#    wildcard consumer strings are denied
# ═══════════════════════════════════════════════════════════════════════════

_NEAR_MISS_PRODUCTION_WRITER = (
    "pcae.core.hpac_rhamp_enrollment.evil",
    "pcae.core.hpac_rhamp_enrollment ",
    " pcae.core.hpac_rhamp_enrollment",
    "pcae.core.hpac_rhamp_enrollmen",
    "PCAE.CORE.HPAC_RHAMP_ENROLLMENT",
    "",
    "*",
    "pcae.core.*",
    "pcae.core.hpac_rhamp_enrollment*",
)


@pytest.mark.parametrize("bad", _NEAR_MISS_PRODUCTION_WRITER)
def test_10_production_writer_near_miss_denied(root, bad):
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(w.PawaOperation.ENROLL_PRINCIPAL, **_pw_kwargs(root, _caller_module=bad))
    assert ei.value.code == "unauthorized_factory_consumer"


_NEAR_MISS_CERTIFICATION = (
    "pcae.core.hpac_certification_coordinator.evil",
    "pcae.core.hpac_certification_coordinator ",
    "pcae.core.hpac_certification_coordinato",
    "PCAE.CORE.HPAC_CERTIFICATION_COORDINATOR",
    "",
    "*",
    "pcae.core.*",
)


@pytest.mark.parametrize("bad", _NEAR_MISS_CERTIFICATION)
def test_11_certification_writer_near_miss_denied(root, principal_and_credential, bad):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        w.certification_writer(
            "hpac_challenge_coordinator",
            **_cw_kwargs(root, principal_id, credential_id, _caller_module=bad),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


@pytest.mark.parametrize("bad", _NEAR_MISS_CERTIFICATION)
def test_12_recognized_read_authority_near_miss_denied(root, principal_and_credential, bad):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        w.recognized_certification_read_authority(
            **_cw_kwargs(root, principal_id, credential_id, _caller_module=bad),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


_NEAR_MISS_LAUNCHER = (
    "pcae.core.protected_presentation.evil",
    "pcae.core.protected_presentation ",
    "pcae.core.protected_presentatio",
    "PCAE.CORE.PROTECTED_PRESENTATION",
    "",
    "*",
)


@pytest.mark.parametrize("bad", _NEAR_MISS_LAUNCHER)
def test_13_presentation_evidence_writer_near_miss_denied(root, bad):
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    with pytest.raises(w.PawaError) as ei:
        w.mint_protected_presentation_evidence_writer(authority, mechanism_id="impl-mechanism-2", _caller_module=bad)
    assert ei.value.code == "unauthorized_factory_consumer"


# ═══════════════════════════════════════════════════════════════════════════
# 3. For each of the 4 factories: the actual legitimate production caller,
#    reached via its REAL call path/module (not by asserting a name), still
#    succeeds
# ═══════════════════════════════════════════════════════════════════════════


# N16-5-F-5-B2R-IMPL: `call_with_real_module_identity`'s scratch-module
# technique no longer suffices to prove "a real caller succeeds" for the
# four enumerated production consumers -- the repair correctly denies it
# (that denial is now covered by tests/test_phase_n16_5_f5b2r_impl_repair.py
# and by test_01-04/test_10-13 near-miss coverage above). The four tests
# below instead drive the call genuinely through the real, actually-imported
# production consumer module's own pre-existing code, proving the repair
# does not break legitimate recognition.


def test_20_production_writer_real_rhamp_enrollment_caller_succeeds(root):
    # enroll_first_credential is hpac_rhamp_enrollment's own real,
    # pre-existing code and genuinely calls production_writer internally --
    # the exact real path, not a simulation.
    principal_id = new_principal_id()
    w.enroll_principal_via_pawa(
        principal_id=principal_id,
        enrollment_provenance_ref="impl-real-20",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    result = enroll_first_credential(
        principal_id=principal_id,
        subject_digest="3" * 64,
        presentation_digest="4" * 64,
        invocation_id="iv-impl-20",
        attempt_id="at-impl-20",
        provider=DeterministicCtap2Provider(),
        protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    assert result.credential_id


def test_21_certification_writer_real_coordinator_caller_succeeds(root, principal_and_credential):
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
    assert handle.role == "hpac_challenge_coordinator"


def test_22_recognized_read_authority_real_coordinator_caller_succeeds(root, principal_and_credential):
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


def test_23_presentation_evidence_writer_real_launcher_caller_succeeds(root):
    # Genuinely drive the real production launcher path
    # (pcae.core.protected_presentation.run_protected_presentation_ceremony
    # -> _build_and_persist_evidence -> mint_protected_presentation_evidence_writer)
    # end to end, rather than simulating the launcher's module identity.
    from pcae.core import hpac_protected_presentation_admin as admin
    from pcae.core import protected_presentation as pp
    from pcae.core import protected_presentation_installation as inst
    from pcae.core.approval_presentation import new_canonical_runtime_approval_subject
    from pcae.protected_presentation_helper import render_human_visible_bytes
    import hashlib as _hashlib

    renderer = "pcae-protected-local-presentation-renderer/1.0"
    helper_shim = (
        b"#!/usr/bin/env python3\n"
        b"import sys\n"
        b"from pcae.protected_presentation_helper import main\n"
        b"sys.exit(main())\n"
    )
    sha = _hashlib.sha256(helper_shim).hexdigest()
    helper_path = inst.helper_content_addressed_path(root, sha)
    helper_path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    helper_path.write_bytes(helper_shim)
    os.chmod(helper_path, 0o500)
    admin.configure_presentation_mechanism(
        action="install",
        protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
        helper_sha256=sha,
        helper_implementation_version="pplp/1.0.0",
        verifier_configuration_digest=_hashlib.sha256(b"verifier-config-v1").hexdigest(),
        renderer_profile=renderer,
        descriptor_version="impl23-1.0",
    )
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    facts = {
        "repository_identity": "repo-abc",
        "repository_display": "repo-abc (fp:abc123)",
        "task_id": "task-1",
        "task_display": "task-1 — the active task",
        "runtime_target_id": "rt-1",
        "runtime_target_display": "rt-1 — mock runtime",
        "operation_effect_scope_display": "cap=read; local; effect=fs; one-dispatch; no-network",
        "prompt_hash": "p" * 64,
        "prompt_instruction_display": "do the bounded thing (fp:p001)",
        "invocation_id": "inv-impl-23",
        "invocation_display": "inv-impl-23 (fp:i001)",
        "expires_at": "2099-01-01T00:00:00Z",
        "one_shot_notice": True,
    }
    displayed_digest = _hashlib.sha256(render_human_visible_bytes(facts, renderer_profile=renderer)).hexdigest()
    subject = new_canonical_runtime_approval_subject(
        subject={
            "repository_identity": facts["repository_identity"],
            "task_id": facts["task_id"],
            "runtime_target_id": facts["runtime_target_id"],
            "prompt_hash": facts["prompt_hash"],
            "invocation_id": facts["invocation_id"],
        },
        approval_scope={"capability": "read", "one_dispatch": True, "network": False},
        approval_preview_digest=displayed_digest,
        expires_at=facts["expires_at"],
    )
    result = pp.run_protected_presentation_ceremony(
        authority=authority,
        approval_id="ria-" + _hashlib.sha256(b"impl-23").hexdigest()[:32],
        challenge_id="ch-impl-23",
        canonical_subject=subject,
        human_visible_facts=facts,
        principal_id="hp-" + "c" * 32,
        invocation_id="inv-impl-23",
        attempt_id="at-impl-23",
        _test_decision_source="APPROVE",
    )
    assert result.decision == "APPROVE"
    assert (root / "presentations" / "v2" / result.presentation_id / "presentation.json").exists()


def test_24_actual_certification_coordinator_module_is_the_real_production_path(root, principal_and_credential):
    """End-to-end confirmation via the REAL production wrapper (not a
    fabricated-identity simulation): ``HpacCertificationCoordinator``,
    constructed with no ``_caller_module`` seam (the genuine production
    configuration), reaches ``certification_writer`` and
    ``recognized_certification_read_authority`` successfully purely because
    its own module really is the enumerated §38A/§38B consumer."""
    from pcae.core.hpac_certification_coordinator import HpacCertificationCoordinator

    principal_id, credential_id = principal_and_credential
    coordinator = HpacCertificationCoordinator(
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    assert coordinator.ceremony_mode == "test-only"  # env seams set, but NOT _caller_module
    session = coordinator.begin_session(principal_id=principal_id, credential_id=credential_id)
    handle = coordinator._mint(
        "hpac_challenge_coordinator",
        certification_session_id=session.certification_session_id,
        principal_id=principal_id,
        credential_id=credential_id,
        proof_id=session.proof_id,
    )
    assert isinstance(handle, w.CertificationWriterHandle)
    ra = coordinator._obtain_read_authority(
        certification_session_id=session.certification_session_id,
        principal_id=principal_id,
        credential_id=credential_id,
        proof_id=session.proof_id,
    )
    assert isinstance(ra, w.CertificationReadAuthority)


# ═══════════════════════════════════════════════════════════════════════════
# 4. A caller-supplied descriptive identity alone never authenticates
#    (generic cross-factory test)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "factory_name,call",
    [
        (
            "production_writer",
            lambda root, pc: w.production_writer(
                w.PawaOperation.ENROLL_PRINCIPAL,
                **_pw_kwargs(root, _caller_module="pcae.core.hpac_protected_admin_writer"),
            ),
        ),
        (
            "certification_writer",
            lambda root, pc: w.certification_writer(
                "hpac_challenge_coordinator",
                **_cw_kwargs(root, pc[0], pc[1], _caller_module="pcae.core.hpac_certification_coordinator"),
            ),
        ),
        (
            "recognized_certification_read_authority",
            lambda root, pc: w.recognized_certification_read_authority(
                **_cw_kwargs(root, pc[0], pc[1], _caller_module="pcae.core.hpac_certification_coordinator"),
            ),
        ),
    ],
)
def test_30_caller_supplied_identity_alone_never_authenticates(root, principal_and_credential, factory_name, call):
    # Every branch here supplies an EXACT authorized-consumer name via the
    # disclosed keyword, from a genuinely unauthorized real caller (this
    # test module). All must be denied -- the assertion alone is the point;
    # `factory_name` documents which factory is under test in a failure.
    with pytest.raises(w.PawaError) as ei:
        call(root, principal_and_credential)
    assert ei.value.code == "unauthorized_factory_consumer", factory_name


def test_31_detect_caller_module_never_returns_or_is_influenced_by_explicit():
    for candidate in (
        "literally.anything",
        "pcae.core.hpac_rhamp_enrollment",
        "pcae.core.hpac_certification_coordinator",
        "pcae.core.protected_presentation",
        "pcae.core.hpac_protected_admin_writer",
        "",
        None,
    ):
        assert w._detect_caller_module(candidate) == w._detect_caller_module(None)


# ═══════════════════════════════════════════════════════════════════════════
# 5. No test module can mint PRODUCTION authority merely by naming itself
#    as an authorized consumer
# ═══════════════════════════════════════════════════════════════════════════


def test_40_this_unenumerated_test_module_cannot_self_authorize(root):
    # THIS_MODULE is asserted (top of file) to be a member of no allowlist.
    # A bare call with no override at all (real provenance = THIS_MODULE)
    # must be denied for every one of the 4 factories.
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(w.PawaOperation.ENROLL_PRINCIPAL, **_pw_kwargs(root))
    assert ei.value.code == "unauthorized_factory_consumer"


def test_41_this_unenumerated_test_module_cannot_self_authorize_certification(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        w.certification_writer(
            "hpac_challenge_coordinator", **_cw_kwargs(root, principal_id, credential_id)
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_42_this_unenumerated_test_module_cannot_self_authorize_read_authority(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        w.recognized_certification_read_authority(**_cw_kwargs(root, principal_id, credential_id))
    assert ei.value.code == "unauthorized_factory_consumer"


def test_43_this_unenumerated_test_module_cannot_self_authorize_presentation_writer(root):
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    with pytest.raises(w.PawaError) as ei:
        w.mint_protected_presentation_evidence_writer(authority, mechanism_id="impl-mechanism-4")
    assert ei.value.code == "unauthorized_factory_consumer"


def test_44_asserting_the_test_consumer_allowlist_name_also_does_not_help(root):
    # Even naming a genuine, disclosed *test*-consumer identity (a member of
    # a DIFFERENT factory's `_TEST_FACTORY_CONSUMERS`-style set) via the
    # keyword does not grant this module authority: the keyword is inert,
    # full stop, regardless of which set the asserted string happens to be
    # a member of.
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(
            w.PawaOperation.ENROLL_PRINCIPAL,
            **_pw_kwargs(
                root,
                _caller_module="test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1",
            ),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


# ═══════════════════════════════════════════════════════════════════════════
# 6. No existing test in this file / suite relies on the removed shortcut
# ═══════════════════════════════════════════════════════════════════════════


def test_50_no_early_return_of_explicit_in_source():
    import inspect as _inspect

    src = _inspect.getsource(w._detect_caller_module)
    assert "return explicit" not in src
    assert "del explicit" in src or "explicit" not in src.split("stack = inspect.stack()")[1]


def test_51_source_scan_still_shows_exactly_one_legitimate_forwarding_site():
    import subprocess

    result = subprocess.run(
        ["git", "grep", "-n", "_caller_module=", "--", "src/pcae"],
        cwd=REPO, capture_output=True, text=True,
    )
    hits = [line for line in result.stdout.splitlines() if "hpac_certification_coordinator.py" in line]
    assert len(hits) == 2, hits
    # and no OTHER production module forwards it at all
    other_hits = [
        line for line in result.stdout.splitlines() if "hpac_certification_coordinator.py" not in line
    ]
    assert other_hits == [], other_hits
