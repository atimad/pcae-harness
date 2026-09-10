"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R
(alias N16-5-F-5-B2) — Privileged Production Factory Consumer-Authenticity
Blast-Radius Reconstruction and Normative Repair Adjudication.

Read-only / architecture-and-normative-adjudication phase (§2 of the
governing prompt): this suite is diagnostic evidence, not a repair. No
src/pcae, scripts/, or contract-text file is modified anywhere in this
phase. Every mutation test below uses a disposable provisioned PRODUCTION
test-fixture protected root under ``tmp_path`` -- no live protected-host
state.

Confirms and extends the F-5-B1-IV MATERIAL FINDING (consumer authenticity
is spoofable via the ungated ``_caller_module`` keyword argument) across the
full inventory of privileged factories that share
``hpac_protected_admin_writer._detect_caller_module``:

  * ``production_writer``                             -- freshly reproduced here
  * ``certification_writer``                           -- freshly reproduced here
  * ``recognized_certification_read_authority``        -- re-confirmed (F-5-B1-IV)
  * ``mint_protected_presentation_evidence_writer``     -- freshly reproduced here

No real ceremony, no genuine YubiKey, no PIN, no protected APPROVE, no
``makeCredential`` / ``getAssertion``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,  # builds the disposable provisioned root only
    HPACAuthorityError,
    HPACStoreAuthority,
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
CONTRACTS = REPO / "docs" / "contracts"

#: B2_0 -- this phase's entry SHA (docs/PHASE_..._N16_5_F_5_B2.md; frozen at
#: phase-open time, before any diagnostic test file existed).
B2_0 = "7b744ebadbfc19860b55e6040adff4122cd12494"

FAKE_AGENT_UID = 4_242_702
FAKE_AGENT_GID = 999_702
AGENT_ACCOUNT = "pcae-agent-svc-n16-5-f5b2"

#: The caller identity this suite's own module resolves to via real stack
#: inspection -- deliberately NOT a member of any production or test
#: consumer allowlist, so every "spoofed" call below is genuinely an
#: unauthorized-caller reproduction, not a disclosed test seam being
#: exercised legitimately.
THIS_MODULE = __name__
assert THIS_MODULE not in w.AUTHORIZED_FACTORY_CONSUMERS
assert THIS_MODULE not in w._TEST_FACTORY_CONSUMERS
assert THIS_MODULE not in w._CERTIFICATION_TEST_CONSUMERS
assert THIS_MODULE not in w._READ_AUTHORITY_TEST_CONSUMERS


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
        enrollment_provenance_ref="f5b2-prov-ref",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    result = enroll_first_credential(
        principal_id=principal_id,
        subject_digest="a" * 64,
        presentation_digest="b" * 64,
        invocation_id="iv-f5b2",
        attempt_id="at-f5b2",
        provider=DeterministicCtap2Provider(),
        protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    return principal_id, result.credential_id


# ═══════════════════════════════════════════════════════════════════════════
# A. _detect_caller_module / _caller_module inventory (§10 of the prompt)
# ═══════════════════════════════════════════════════════════════════════════


def test_01_detect_caller_module_trusts_explicit_value_verbatim():
    """POST-REPAIR (N16-5-F-5-B2-IMPL): the historical name of this test is
    retained (no test is renamed), but the behaviour it now demonstrates is
    the opposite of its name — ``explicit`` is unconditionally ignored;
    real stack-based provenance governs regardless of what is passed."""
    assert w._detect_caller_module("literally.anything") != "literally.anything"


def test_02_four_factories_share_the_primitive():
    import inspect as _inspect

    for fn in (
        w.production_writer,
        w.certification_writer,
        w.recognized_certification_read_authority,
        w.mint_protected_presentation_evidence_writer,
    ):
        src = _inspect.getsource(fn)
        assert "_detect_caller_module(_caller_module)" in src


def test_03_only_production_caller_of_the_override_defaults_to_none():
    # HpacCertificationCoordinator forwards s.caller_module, which is None
    # unless the coordinator itself is constructed with the disclosed
    # test-only seam -- real production construction never sets it.
    from pcae.core.hpac_certification_coordinator import HpacCertificationCoordinator

    coord = HpacCertificationCoordinator()
    assert coord._seams.caller_module is None
    assert coord.ceremony_mode == "production"


# ═══════════════════════════════════════════════════════════════════════════
# B. Per-factory spoof reproduction (§12-16) -- fresh, disposable state only
# ═══════════════════════════════════════════════════════════════════════════


def test_10_production_writer_unspoofed_denied(root):
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "0" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_11_production_writer_spoofed_yields_full_writer_capability(root):
    """POST-REPAIR (N16-5-F-5-B2-IMPL): this test's historical name is
    retained (no test is renamed/deleted), but the finding it reproduced is
    now closed — ``_caller_module`` no longer overrides real provenance, so
    the exact same spoof attempt is now DENIED. See
    ``test_11b_production_writer_real_caller_still_yields_full_writer_capability``
    below for proof the genuine production path is unaffected."""
    with pytest.raises(w.PawaError) as ei:
        w.production_writer(
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "1" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
            _caller_module="pcae.core.hpac_protected_admin_writer",
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_11b_production_writer_real_caller_still_yields_full_writer_capability(root):
    # The genuine production path is unaffected: a call that REALLY
    # originates from an authorized consumer module (here, the self-consumer
    # bounded principal-admin operations of hpac_protected_admin_writer
    # itself) still mints and consumes a full writer capability end to end
    # -- proving the N16-5-F-5-B2R-IMPL repair closed the forgery (see
    # tests/test_phase_n16_5_f5b2r_impl_repair.py) without breaking real
    # recognition. (N16-5-F-5-B2R-IMPL: the scratch-module
    # `call_with_real_module_identity` technique this test previously used
    # is no longer sufficient real provenance for the four enumerated
    # production consumers -- see that suite for why.)
    result = w.enroll_principal_via_pawa(
        principal_id="hp-" + "1" * 32,
        enrollment_provenance_ref="f5b2-11b-real",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
    )
    assert result is not None


def test_12_certification_writer_unspoofed_denied(root, principal_and_credential):
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        w.certification_writer(
            "hpac_challenge_coordinator",
            certification_session_id="hcs-" + "0" * 32,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=new_proof_id(),
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_13_certification_writer_spoofed_yields_full_writer_handle(root, principal_and_credential):
    """POST-REPAIR: name retained, spoof now DENIED — see test_13b for the
    genuine real-caller path."""
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        w.certification_writer(
            "hpac_challenge_coordinator",
            certification_session_id="hcs-" + "1" * 32,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=new_proof_id(),
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
            _caller_module="pcae.core.hpac_certification_coordinator",
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_13b_certification_writer_real_caller_still_yields_full_writer_handle(root, principal_and_credential):
    # N16-5-F-5-B2R-IMPL: driven through the real HpacCertificationCoordinator
    # (its own genuine pre-existing code) instead of the scratch-module proxy
    # -- see test_11b's comment / tests/test_phase_n16_5_f5b2r_impl_repair.py.
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


def test_14_recognized_read_authority_spoofed_succeeds_but_escalation_denied(root, principal_and_credential):
    """POST-REPAIR: the F-5-B1-IV finding this test reproduced is now
    CLOSED by N16-5-F-5-B2-IMPL — the same spoof attempt is denied outright
    (never reaches the escalation gate). The escalation gate itself is
    re-confirmed independently below via the genuine real-caller path."""
    principal_id, credential_id = principal_and_credential
    with pytest.raises(w.PawaError) as ei:
        w.recognized_certification_read_authority(
            certification_session_id="hcs-" + "2" * 32,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=new_proof_id(),
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
            _caller_module="pcae.core.hpac_certification_coordinator",
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_14b_recognized_read_authority_real_caller_succeeds_escalation_still_denied(root, principal_and_credential):
    # N16-5-F-5-B2R-IMPL: driven through the real HpacCertificationCoordinator
    # instead of the scratch-module proxy -- see test_13b.
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
    with pytest.raises(HPACAuthorityError):
        ra._authority.writer("hpac_challenge_coordinator")


def test_15_presentation_evidence_writer_spoofed_yields_full_writer_capability(root):
    """POST-REPAIR: name retained, spoof now DENIED — see test_15b for the
    genuine real-caller (launcher) path."""
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    with pytest.raises(w.PawaError) as ei:
        w.mint_protected_presentation_evidence_writer(
            authority, mechanism_id="f5b2-mechanism", _caller_module="pcae.core.protected_presentation"
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_15b_presentation_evidence_writer_real_caller_still_yields_full_writer_capability(root):
    # N16-5-F-5-B2R-IMPL: driven through the real production launcher path
    # (pcae.core.protected_presentation.run_protected_presentation_ceremony
    # -> _build_and_persist_evidence -> mint_protected_presentation_evidence_writer)
    # end to end, instead of the scratch-module proxy -- see test_11b's
    # comment / tests/test_phase_n16_5_f5b2r_impl_repair.py.
    import hashlib as _hashlib

    from pcae.core import hpac_protected_presentation_admin as admin
    from pcae.core import protected_presentation as pp
    from pcae.core import protected_presentation_installation as inst
    from pcae.core.approval_presentation import new_canonical_runtime_approval_subject
    from pcae.protected_presentation_helper import render_human_visible_bytes

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
        descriptor_version="f5b2-15b-1.0",
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
        "invocation_id": "inv-f5b2-15b",
        "invocation_display": "inv-f5b2-15b (fp:i001)",
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
        approval_id="ria-" + _hashlib.sha256(b"f5b2-15b").hexdigest()[:32],
        challenge_id="ch-f5b2-15b",
        canonical_subject=subject,
        human_visible_facts=facts,
        principal_id="hp-" + "d" * 32,
        invocation_id="inv-f5b2-15b",
        attempt_id="at-f5b2-15b",
        _test_decision_source="APPROVE",
    )
    assert result.decision == "APPROVE"
    assert (root / "presentations" / "v2" / result.presentation_id / "presentation.json").exists()


def test_16_presentation_evidence_writer_unspoofed_denied(root):
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    with pytest.raises(w.PawaError) as ei:
        w.mint_protected_presentation_evidence_writer(authority, mechanism_id="f5b2-mechanism-2")
    assert ei.value.code == "unauthorized_factory_consumer"


# ═══════════════════════════════════════════════════════════════════════════
# C. Static guard is not a runtime control (§18)
# ═══════════════════════════════════════════════════════════════════════════


def test_20_static_guard_is_source_scan_not_runtime_gate():
    # POST-REPAIR (N16-5-F-5-B2-IMPL): before the repair, this suite's own
    # THIS_MODULE assertions above (not a member of any allowlist) plus
    # test_11/13/15's live success from that same module jointly
    # demonstrated that a source-level "no non-test caller passes
    # _caller_module" scan alone was not a runtime control. Since the
    # repair, test_11/13/15 (same inputs) are now correctly DENIED at
    # runtime too -- the disclosed keyword argument is no longer
    # authoritative for either control. This scan is retained as
    # defence-in-depth (it still independently confirms no *other*
    # production module forwards the now-inert seam), not as the sole
    # control it once effectively was.
    result = subprocess.run(
        ["git", "grep", "-n", "_caller_module=", "--", "src/pcae"],
        cwd=REPO, capture_output=True, text=True,
    )
    # only the one legitimate production forwarding site should appear
    hits = [l for l in result.stdout.splitlines() if "hpac_certification_coordinator.py" in l]
    assert len(hits) == 2, hits


# ═══════════════════════════════════════════════════════════════════════════
# D. Contract text already defines consumer as the calling module (§23-27)
# ═══════════════════════════════════════════════════════════════════════════


def test_30_pawa_contract_defines_consumer_as_the_calling_module():
    pawa = (CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md").read_text()
    assert "the importing / calling **source module**" in pawa
    assert "a build-time / import-time fact" in pawa
    assert "## 32. Recognition predicate 6" in pawa


def test_31_no_contract_or_production_source_modified_since_b2_0():
    """This diagnostic phase (N16-5-F-5-B2) was itself read-only / decision
    -only, so at B2_0 it correctly asserted NO src/pcae change at all. Its
    recommended successor, N16-5-F-5-B2-IMPL, deliberately DOES modify
    ``src/pcae/core/hpac_protected_admin_writer.py`` to repair the finding
    this suite documents -- that is the entire point of the successor
    phase, not a regression of this invariant. What must still hold, and
    is independently re-checked here, is the part of the original
    invariant that is a real, permanent constraint on this repair: no
    contract-text byte changes and no dependency-set change. (Whether
    ``src/pcae`` / ``scripts`` differ from B2_0 is no longer asserted here
    -- see test_02_four_factories_share_the_primitive and the regression
    suite in test_phase_..._n16_5_f5b2_impl_consumer_authenticity.py for
    what DID change and why.)"""
    # Reconciled by phase N16-5-F-5-TB-CONTRACT (HPAC-PAWA-001 v1.4 -> v2.0, MAJOR S-4; new companion HPAC-PAWA-HELPER-001 v1.0): re-anchor the moving `HEAD` to the fixed
    # SHA 05056eeb1d38d92d7eda749a4334f7626c5e6a8f (last v1.4 commit); the B2 diagnostic phase changed no contract
    # text and no dependency, which stays true through that SHA.
    names = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", B2_0, "05056eeb1d38d92d7eda749a4334f7626c5e6a8f", "--",
         "docs/contracts", "pyproject.toml"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert names == [], names


def test_32_runtime_unchanged():
    out = subprocess.run(["pcae", "runtime", "inspect"], cwd=REPO, capture_output=True, text=True).stdout
    assert "Runtime status:            not_implemented" in out
    assert "Execution capability:      unavailable" in out
    assert "Plugin count:              0" in out
    assert "Capability count:          0" in out
