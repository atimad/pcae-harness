"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R
(alias N16-5-F-5-B1-IV) -- INDEPENDENT VERIFICATION suite for the
predecessor N16-5-F-5-B1-IMPL implementation of HPAC-PAWA-001 v1.4
S33B / S38B / S42D / S42E / S49B / S68B.

This suite is authored fresh for this IV phase. It reconstructs its
findings from primary source and live execution rather than adopting the
predecessor's own report. It intentionally does NOT reuse the predecessor
test file's Rig fixture wholesale (built independently below) so that a
defect hidden by a shared fixture bug would not also hide here.

Verification-only: no src/pcae, scripts/, or contract-text mutation. No
real ceremony, no genuine YubiKey/PIN, no live protected-host writes.

KEY FINDING (see test_20_* below): consumer authenticity for
``recognized_certification_read_authority`` is NOT independently bound to
a trusted caller-identity mechanism. The exported keyword argument
``_caller_module`` is accepted verbatim with no runtime gate -- any
in-process caller (this test module included, acting as an "arbitrary
unauthorized module") can claim the authorized coordinator's identity and
obtain a fully working ``CertificationReadAuthority`` handle. The only
control is a *static* source-scanning guard test elsewhere in the repo
that asserts no non-test module in this checkout happens to pass the
argument -- that is not a runtime authorization boundary. Per
HPAC-PAWA-001 v1.4 S33B / S38B and this IV's governing spec (mandatory
consumer-authenticity criterion), this is a material BLOCKING defect.
This pattern is pre-existing (shared with ``production_writer`` /
``certification_writer`` since before this implementation phase), so
F-5-B1's repair reused it unmodified rather than introducing it -- the
provenance does not change the verdict for F-5-B1's own read-authority
factory.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core import phase_id as pid
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
)
from pcae.core.human_authentication_proof import new_proof_id
from pcae.core.human_principal_registry import HumanPrincipalRegistryStore, new_principal_id

from _caller_identity_helper import call_with_real_module_identity

pytestmark = [
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root model"),
]

REPO = Path(__file__).resolve().parents[1]

#: I_ENTRY -- independently re-derived predecessor implementation phase-entry SHA.
I_ENTRY = "a6455ef1ef130d77c01aa3b2a2d7833f5eb8cb5e"

PREDECESSOR_CANDIDATE = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R"
    ".1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R"
)
IV_CANDIDATE = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R"
    ".1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R"
)

FAKE_AGENT_UID = 4_242_802
FAKE_AGENT_GID = 999_802
AGENT_ACCOUNT = "pcae-agent-svc-n16-5-f-5-b1-iv"

UNAUTHORIZED_MODULE_NAME = __name__  # this IV test module -- a genuinely arbitrary, unauthorized caller


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


class IvRig:
    """Independently constructed provisioned fixture root + one active
    principal/credential, built without reusing the predecessor's Rig."""

    def __init__(self, tmp_path):
        self.root = (tmp_path / "hpac-protected-root-iv").resolve()
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
            enrollment_provenance_ref="iv-prov-ref",
            _protected_root=self.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
        self.credential_id = self._enroll_credential()
        self.proof_id = new_proof_id()
        self.session_id = "hcs-" + "2" * 32

    def _enroll_credential(self) -> str:
        from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
        from pcae.core.hpac_rhamp_enrollment import enroll_first_credential

        result = enroll_first_credential(
            principal_id=self.principal_id,
            subject_digest="e" * 64,
            presentation_digest="f" * 64,
            invocation_id="iv-n16-5-f-5-b1-iv",
            attempt_id="at-n16-5-f-5-b1-iv",
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
        )
        kw.update(over)
        return w.recognized_certification_read_authority(**kw)

    def real_ra(self, **over):
        """N16-5-F-5-B2R-IMPL: obtain a genuine (non-spoofed)
        ``CertificationReadAuthority`` by driving the call through the real,
        actually-imported ``HpacCertificationCoordinator``'s own
        pre-existing code -- the scratch-module
        ``call_with_real_module_identity`` technique this helper previously
        used is no longer sufficient real provenance for the enumerated
        production consumers (see
        tests/test_phase_n16_5_f5b2r_impl_repair.py). ``over`` overrides are
        applied only to the fields this real path still accepts a caller
        override for (none currently -- the real coordinator derives
        ``certification_session_id`` / ``proof_id`` itself from its own
        ``begin_session``); a caller that needs a genuinely different
        session/proof must construct its own coordinator flow."""
        from pcae.core.hpac_certification_coordinator import HpacCertificationCoordinator

        principal_id = over.pop("principal_id", self.principal_id)
        credential_id = over.pop("credential_id", self.credential_id)
        coordinator = HpacCertificationCoordinator(
            _protected_root=over.pop("_protected_root", self.root),
            _configured_agent_identity_source=over.pop("_configured_agent_identity_source", _agent_src()),
            _topology_probe=over.pop("_topology_probe", _locked_probe()),
        )
        session = coordinator.begin_session(principal_id=principal_id, credential_id=credential_id)
        kw = dict(
            certification_session_id=session.certification_session_id,
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=session.proof_id,
        )
        kw.update(over)
        return coordinator._obtain_read_authority(**kw)


@pytest.fixture
def rig(tmp_path):
    return IvRig(tmp_path)


# =============================================================================
# LINEAGE / CPIPC (spec section 6, items 1-6)
# =============================================================================


def test_01_cpipc_successor_is_exactly_predecessor_plus_one_1r_token():
    predecessor = pid.parse(PREDECESSOR_CANDIDATE)
    candidate = pid.parse(IV_CANDIDATE)
    assert pid.same_series(predecessor, candidate)
    assert pid.same_branch(predecessor, candidate)
    assert pid.compare(candidate, predecessor) == "greater"
    assert candidate.subphase[: len(predecessor.subphase)] == predecessor.subphase
    assert candidate.subphase[len(predecessor.subphase) :] == ((1, "R"),)


def test_02_production_diff_since_i_entry_is_exactly_two_files_pure_addition():
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--stat", f"{I_ENTRY}..HEAD", "--", "src/pcae", "scripts", "pyproject.toml"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "hpac_protected_admin_writer.py" in diff
    assert "hpac_certification_coordinator.py" in diff
    assert "hpac_certification_admin.py" not in diff
    assert "pyproject.toml" not in diff


def test_03_contract_and_schema_byte_unchanged_since_i_entry():
    import subprocess

    out = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            f"{I_ENTRY}..HEAD",
            "--",
            "docs/contracts",
            "src/pcae/core/hpac_pawa_schemas.py",
            "pyproject.toml",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert out.strip() == ""


# =============================================================================
# CONSUMER AUTHENTICITY -- THE MATERIAL FINDING (spec sections 11, 62, 92.13)
# =============================================================================


def test_20_baseline_this_module_is_genuinely_unauthorized(rig):
    """Sanity: without spoofing anything, this IV test module (an ordinary
    non-coordinator caller) is correctly denied via real stack-based caller
    detection -- establishing that the positive result in test_21 below is
    due to the spoof, not to this module being on the allowlist."""
    assert UNAUTHORIZED_MODULE_NAME not in w.READ_AUTHORITY_CONSUMERS
    with pytest.raises(w.PawaError) as ei:
        rig.ra()  # no _caller_module override -- real stack inspection applies
    assert ei.value.code == "unauthorized_factory_consumer"


def test_21_arbitrary_caller_spoofs_coordinator_identity_and_succeeds(rig):
    """POST-REPAIR (N16-5-F-5-B2-IMPL): THE FINDING this test's historical
    name documents is now CLOSED. The exact same attempt -- the public
    ``_caller_module`` keyword argument claiming the authorized
    coordinator's module name, from this genuinely unauthorized module --
    is now denied outright; the argument is no longer authoritative for
    consumer recognition. (Name retained; no test is renamed or deleted.)
    See ``test_21b_...`` for proof a GENUINE call from that module name
    still succeeds, i.e. the repair closed the spoof without breaking real
    recognition.
    """
    with pytest.raises(w.PawaError) as ei:
        rig.ra(_caller_module="pcae.core.hpac_certification_coordinator")
    assert ei.value.code == "unauthorized_factory_consumer"


def test_21b_real_coordinator_identity_still_succeeds(rig):
    handle = rig.real_ra()
    assert isinstance(handle, w.CertificationReadAuthority)
    principal, credential = handle.read_principal_and_credential()
    assert principal.principal_id == rig.principal_id
    assert credential.credential_id == rig.credential_id


def test_22_predecessors_own_positive_tests_rely_on_the_same_spoof_seam():
    """Independently confirms (by reading the predecessor's own committed
    test file) that its "authorized consumer accepted" positive tests
    exercise the factory exclusively via this same caller-supplied
    ``_caller_module`` override, from the test module -- i.e. the
    predecessor's evidence for consumer authenticity is itself produced
    using the mechanism this IV finds is spoofable, not by exercising a
    real trusted-caller-identity binding."""
    predecessor_test = (
        REPO
        / "tests"
        / "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_f5b1_impl.py"
    )
    text = predecessor_test.read_text()
    assert '_caller_module=COORDINATOR_MODULE' in text


def test_23_detect_caller_module_returns_explicit_value_unconditionally():
    """POST-REPAIR: name retained; the root cause this test documented is
    fixed -- the shared ``_detect_caller_module`` helper no longer returns
    (or otherwise consults) any explicitly supplied value at all; it always
    consults the real call stack."""
    assert w._detect_caller_module("literally.anything.i.want") != "literally.anything.i.want"


# =============================================================================
# ESCALATION / FORGERY / RAW-ESCAPE (spec sections 24-28, 43-51) -- re-verified
# =============================================================================


def test_30_wrapped_authority_writer_denied(rig):
    # N16-5-F-5-B2-IMPL: obtained via the genuine real-caller path (the
    # disclosed ``_caller_module`` override is no longer authoritative).
    handle = rig.real_ra()
    with pytest.raises(HPACAuthorityError):
        handle._authority.writer("certification_writer")


def test_31_reads_return_plain_records_not_resolved_record_with_seal(rig):
    handle = rig.real_ra()
    principal, credential = handle.read_principal_and_credential()
    for obj in (principal, credential):
        assert not hasattr(obj, "authority_seal")
        assert not isinstance(obj, HPACStoreAuthority)


def test_32_handle_is_not_serializable(rig):
    handle = rig.real_ra()
    with pytest.raises(TypeError):
        handle.__reduce__()


def test_33_direct_construction_without_factory_seal_denied():
    with pytest.raises(TypeError):
        w.CertificationReadAuthority(
            _factory_seal=object(),
            certification_session_id="x",
            principal_id="y",
            credential_id="z",
            proof_id="p",
        )


# =============================================================================
# GUARD RECONCILIATION (spec sections 37, 73-75, 100) -- independently re-checked
# =============================================================================


def test_40_approval_presentation_consumer_tuple_is_the_sole_widening():
    import subprocess

    diff = subprocess.run(
        ["git", "diff", f"{I_ENTRY}..HEAD", "--", "tests"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    added_tuple_lines = [
        line
        for line in diff.splitlines()
        if line.startswith("+") and "approval_presentation" in line
    ]
    assert len(added_tuple_lines) >= 1
    assert not any("*" in line or "glob" in line for line in added_tuple_lines)
    removed_test_defs = [
        line for line in diff.splitlines() if line.startswith("-def test_")
    ]
    assert removed_test_defs == []


# =============================================================================
# PREDECESSOR TEST SUITE STILL GREEN (spec section F) -- re-verified, not trusted
# =============================================================================


def test_50_predecessor_implementation_suite_still_fully_passes():
    import subprocess

    result = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            str(
                REPO
                / "tests"
                / "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_f5b1_impl.py"
            ),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-3000:]
    assert "72 passed" in result.stdout
