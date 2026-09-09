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
    assert w._detect_caller_module("literally.anything") == "literally.anything"


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
    handle = w.production_writer(
        w.PawaOperation.ENROLL_PRINCIPAL,
        principal_id="hp-" + "1" * 32,
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
        _caller_module="pcae.core.hpac_protected_admin_writer",
    )
    assert isinstance(handle, w.ProductionWriterHandle)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id="hp-" + "1" * 32)
    from pcae.core.hpac_foundation import HPACWriterCapability

    assert isinstance(cap, HPACWriterCapability)


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
    principal_id, credential_id = principal_and_credential
    handle = w.certification_writer(
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
    assert isinstance(handle, w.CertificationWriterHandle)
    assert handle.role == "hpac_challenge_coordinator"


def test_14_recognized_read_authority_spoofed_succeeds_but_escalation_denied(root, principal_and_credential):
    # Re-confirms the F-5-B1-IV finding fresh, from this phase's own entry
    # point, and additionally checks the independent escalation gate.
    principal_id, credential_id = principal_and_credential
    ra = w.recognized_certification_read_authority(
        certification_session_id="hcs-" + "2" * 32,
        principal_id=principal_id,
        credential_id=credential_id,
        proof_id=new_proof_id(),
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
        _caller_module="pcae.core.hpac_certification_coordinator",
    )
    assert isinstance(ra, w.CertificationReadAuthority)
    with pytest.raises(HPACAuthorityError):
        ra._authority.writer("hpac_challenge_coordinator")


def test_15_presentation_evidence_writer_spoofed_yields_full_writer_capability(root):
    authority = HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )
    from pcae.core.hpac_foundation import HPACWriterCapability

    cap = w.mint_protected_presentation_evidence_writer(
        authority, mechanism_id="f5b2-mechanism", _caller_module="pcae.core.protected_presentation"
    )
    assert isinstance(cap, HPACWriterCapability)


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
    # This suite's own THIS_MODULE assertions above (not a member of any
    # allowlist) plus test_11/13/15's live success from that same module
    # jointly demonstrate: a source-level "no non-test caller passes
    # _caller_module" scan cannot see, and does not block, a call made
    # from outside the scanned tree (this file itself, an external script,
    # a plugin, or any other in-process caller).
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
    names = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", B2_0, "HEAD", "--",
         "src/pcae", "scripts", "pyproject.toml", "docs/contracts"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert names == [], names


def test_32_runtime_unchanged():
    out = subprocess.run(["pcae", "runtime", "inspect"], cwd=REPO, capture_output=True, text=True).stdout
    assert "Runtime status:            not_implemented" in out
    assert "Execution capability:      unavailable" in out
    assert "Plugin count:              0" in out
    assert "Capability count:          0" in out
