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


def test_20_production_writer_real_rhamp_enrollment_caller_succeeds(root):
    handle = call_with_real_module_identity(
        "pcae.core.hpac_rhamp_enrollment",
        w.production_writer,
        w.PawaOperation.ENROLL_PRINCIPAL,
        **_pw_kwargs(root),
    )
    assert isinstance(handle, w.ProductionWriterHandle)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id="hp-" + "3" * 32)
    assert isinstance(cap, HPACWriterCapability)


def test_21_certification_writer_real_coordinator_caller_succeeds(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    handle = call_with_real_module_identity(
        "pcae.core.hpac_certification_coordinator",
        w.certification_writer,
        "hpac_challenge_coordinator",
        **_cw_kwargs(root, principal_id, credential_id),
    )
    assert isinstance(handle, w.CertificationWriterHandle)
    assert handle.role == "hpac_challenge_coordinator"


def test_22_recognized_read_authority_real_coordinator_caller_succeeds(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    ra = call_with_real_module_identity(
        "pcae.core.hpac_certification_coordinator",
        w.recognized_certification_read_authority,
        **_cw_kwargs(root, principal_id, credential_id),
    )
    assert isinstance(ra, w.CertificationReadAuthority)


def test_23_presentation_evidence_writer_real_launcher_caller_succeeds(root):
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    cap = call_with_real_module_identity(
        "pcae.core.protected_presentation",
        w.mint_protected_presentation_evidence_writer,
        authority,
        mechanism_id="impl-mechanism-3",
    )
    assert isinstance(cap, HPACWriterCapability)


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
