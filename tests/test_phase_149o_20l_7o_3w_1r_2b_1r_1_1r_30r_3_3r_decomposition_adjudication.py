"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3R — N-16-5 RHAMP Slice 2 / Slice 3
Decomposition Adjudication.

Verification-only suite. It imports no PCAE runtime code and enables nothing;
it reads contract / production source as text and asserts the source facts the
adjudication (Decision A — RE-MERGE) rests on:

  * RHAMP-001 v1.0 binds canonical credential registration to a real CTAP2
    ``authenticatorMakeCredential`` ceremony (RHAMP-REQ-043 / -048 / -055 /
    -056 / -150) and defines no material-less / staged / placeholder mode;
  * RHAMP-REQ-156 bundles "mechanism + registry + bootstrap" into one phase;
  * no ``PENDING`` / staged ``CredentialRecord`` lifecycle state exists;
  * the production tree and the runtime / first-effect boundary are unchanged
    by this adjudication phase.

No implementation is performed or asserted to exist.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
CORE = REPO_ROOT / "src" / "pcae" / "core"

RHAMP = CONTRACTS / "REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC_PAWA = CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
HPAC = CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
VERIFIER = CORE / "hpac_verifier.py"
REGISTRY = CORE / "human_principal_registry.py"
GATE5 = CORE / "runtime_dispatch_gate5.py"
GATE9 = CORE / "runtime_dispatch_gate9.py"

# Immutable adjudication baseline A == phase-entry SHA V (the finalized
# .1R.30R.3.3 head). git diff A..HEAD must not touch production / contracts.
BASELINE_A = "93266b7d64d514ec5c5456fa04c9ea96a610aa92"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


@pytest.fixture(scope="module")
def rhamp_text() -> str:
    return _read(RHAMP)


# --------------------------------------------------------------------------- #
# 1. RHAMP-001 v1.0 exists, is frozen v1.0, and is byte-identical to baseline A
# --------------------------------------------------------------------------- #


def test_rhamp_001_is_frozen_v1_0(rhamp_text: str) -> None:
    assert "RHAMP-001 v1.0" in rhamp_text
    assert "**Version:** 1.0" in rhamp_text
    assert "**Status:** FROZEN" in rhamp_text


def test_rhamp_001_byte_unchanged_since_baseline_a() -> None:
    changed = _git("diff", "--name-only", BASELINE_A, "HEAD", "--", "docs/contracts").strip()
    assert changed == "", f"a normative contract changed since A: {changed!r}"


# --------------------------------------------------------------------------- #
# 2. makeCredential is non-severable from canonical registration
# --------------------------------------------------------------------------- #


def test_reg_flow_consumes_makecredential_outputs(rhamp_text: str) -> None:
    # RHAMP-REQ-043: enroll_credential public_key comes from the COSE key that
    # PCAE extracts from the verified makeCredential response.
    assert "RHAMP-REQ-043" in rhamp_text
    assert "authenticatorMakeCredential" in rhamp_text
    assert "PCAE verifies the makeCredential response, extracts" in rhamp_text
    assert "public_key = hex(cbor(COSE_Key))" in rhamp_text


def test_first_credential_bootstrap_requires_makecredential_verification(rhamp_text: str) -> None:
    # RHAMP-REQ-048: "verification of the `makeCredential` response" is inside
    # the mandatory "all of" conjunction for the bootstrap ceremony.
    assert "RHAMP-REQ-048" in rhamp_text
    assert "verification of the `makeCredential` response" in rhamp_text
    assert "atomic create of the first `CredentialRecord` + sidecar + counter-state" in rhamp_text


def test_sidecar_is_a_closed_schema_over_authenticator_output(rhamp_text: str) -> None:
    # RHAMP-REQ-056: RHAMP-FIDO2-CREDENTIAL/1.0 fields are "exactly" a closed
    # set including raw_credential_id + cose_public_key — both authenticator
    # output; there is no nullable / placeholder / pending variant.
    assert "RHAMP-FIDO2-CREDENTIAL/1.0" in rhamp_text
    assert "raw_credential_id" in rhamp_text and "cose_public_key" in rhamp_text
    assert "immutable, create-only, atomically written" in rhamp_text
    # no staged / pending credential-lifecycle state is defined anywhere in v1.0
    for forbidden in ("PENDING_MATERIAL", "PENDING_REGISTRATION"):
        assert forbidden not in rhamp_text


def test_counter_state_created_at_enrollment(rhamp_text: str) -> None:
    # RHAMP-REQ-069: the counter-state record is created at enrollment, keyed
    # by credential_id; a missing record for an active credential fails closed.
    assert "RHAMP-COUNTER-STATE/1.0" in rhamp_text
    assert "created at enrollment" in rhamp_text
    assert "SHALL NOT be silently treated as \"counter 0\"" in rhamp_text


def test_synthetic_material_never_becomes_real_authority(rhamp_text: str) -> None:
    # RHAMP-REQ-155 closes the "administratively-supplied material" escape hatch.
    assert "No synthetic / virtual / deterministic fixture object" in rhamp_text
    assert "REAL authority in a production registry" in rhamp_text


def test_terminal_reason_vocabulary_is_frozen_at_41(rhamp_text: str) -> None:
    # RHAMP-REQ-129 — the closed vocabulary is exactly 41 values; the .1R.28
    # "25"/"27" figures are superseded.
    assert "exactly the **41** values" in rhamp_text
    assert "| 41 | `internal_verification_error`" in rhamp_text
    assert "| 42 |" not in rhamp_text


# --------------------------------------------------------------------------- #
# 3. RHAMP-REQ-156 bundles mechanism + registry + bootstrap into one phase
# --------------------------------------------------------------------------- #


def test_req_156_bundles_mechanism_registry_bootstrap(rhamp_text: str) -> None:
    assert "RHAMP-REQ-156" in rhamp_text
    # the .1R.30 row names the stores, the enrollment/bootstrap tool, the
    # authenticator, and the verifier branch all in one phase.
    assert "the protected-admin enrollment + first-credential bootstrap ceremony tool" in rhamp_text
    assert "`FIDO2HumanAuthenticator`" in rhamp_text
    assert "real CTAP2 assertion verification in `hpac_verifier`" in rhamp_text
    # the freeze verdict parenthetical:
    assert "(mechanism + registry + bootstrap)" in rhamp_text


def test_only_presentation_is_severed_to_the_next_phase(rhamp_text: str) -> None:
    # the .1R.30 row explicitly defers ONLY the protected UI / approval-authority
    # path — not the registry, not the counter-state, not the authenticator.
    assert "No protected approval UI. No real approval-authority production path yet." in rhamp_text


# --------------------------------------------------------------------------- #
# 4. No staged / pending credential-lifecycle state exists in production
# --------------------------------------------------------------------------- #


def test_credential_record_status_is_active_revoked_only() -> None:
    text = _read(REGISTRY)
    assert "CredentialRecord" in text
    # no staged lifecycle token anywhere in the registry module
    for forbidden in ("PENDING_MATERIAL", "PENDING_REGISTRATION", "pending_material"):
        assert forbidden not in text


def test_verifier_has_no_real_signature_branch_yet() -> None:
    text = _read(VERIFIER)
    assert '_ELIGIBLE_MECHANISM_IDS = frozenset({"hpac.deterministic.test-only.v1"})' in text
    assert "hpac.fido2.uv_presence.v2" not in text
    # the module still documents that it does not do real signature math
    assert "does not attempt real signature math" in text


# --------------------------------------------------------------------------- #
# 5. This adjudication phase changed no production / script / contract code
# --------------------------------------------------------------------------- #


def test_no_production_or_script_diff_since_baseline_a() -> None:
    changed = _git("diff", "--name-only", BASELINE_A, "HEAD", "--", "src/pcae", "scripts").strip()
    assert changed == "", f"unexpected production/script diff since A: {changed!r}"


def test_verifier_and_gates_byte_unchanged_since_baseline_a() -> None:
    for rel in (
        "src/pcae/core/hpac_verifier.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/approval_presentation.py",
    ):
        diff = _git("diff", BASELINE_A, "HEAD", "--", rel)
        assert diff == "", f"{rel} changed since A"


def test_no_existing_test_file_changed_since_baseline_a() -> None:
    # tracked-diff against A must not touch any PRE-EXISTING test file; the only
    # permissible tests/ change is this new adjudication file (untracked until
    # this phase's own commit, hence absent from a diff --name-only A..HEAD).
    changed = [
        c for c in _git("diff", "--name-only", BASELINE_A, "HEAD", "--", "tests").splitlines() if c
    ]
    allowed = {"tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_3r_decomposition_adjudication.py"}
    assert set(changed) <= allowed, f"unexpected pre-existing test change: {set(changed) - allowed}"


# --------------------------------------------------------------------------- #
# 6. Runtime / first-effect boundary unchanged; Slice 1 anchor still present
# --------------------------------------------------------------------------- #


def test_no_new_first_external_effect_since_baseline_a() -> None:
    # the adjudication adds no src/pcae byte, so it cannot have added a call
    # site; the standing runtime posture (Observed / observe / unavailable) is
    # unchanged because hpac_verifier / the gates are byte-identical (above).
    diff = _git("diff", "--name-only", BASELINE_A, "HEAD", "--", "src/pcae").strip()
    assert diff == ""


def test_slice1_pawa_anchor_contract_present_and_v1_1() -> None:
    text = _read(HPAC_PAWA)
    assert "HPAC-PAWA-001" in text
    assert "1.1" in text
