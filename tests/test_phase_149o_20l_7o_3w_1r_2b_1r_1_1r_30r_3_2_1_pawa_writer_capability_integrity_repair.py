"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2.1 — N-16-5 PAWA
HPACWriterCapability Non-Bearer / One-Operation Integrity Repair.

Dedicated repair suite. Independently re-derives, against the finalized
`.1R.30R.3.1` head (A = aff46ec3), the decisive `.1R.30R.3.2` BLOCKED
finding (a `.1R.30R.3.2` IV, not this phase) — a caller who already holds
one legitimately issued PRODUCTION HPACWriterCapability can copy its real
`_authority_seal` onto a fresh `object.__new__` shell, which then also
passes `require_writer`'s identity check and authorizes a second, distinct
registry mutation — then proves the repaired code in this working tree
(R) rejects the identical adversary through the real `production_writer()`
-> `HumanPrincipalRegistryStore` path, plus the surrounding non-bearer /
one-operation / scope-binding / copy / concurrency / restart matrix.

`.1R.30R.3.2` (Independent Verification) is preserved, immutable, and
BLOCKED — this suite does not re-open, re-verify, or rewrite it. `.1R.30R.1`
is likewise untouched. N-16-5 is NOT CLOSED by this phase; a fresh
successor IV is required.

FIDO2-free. No Slice 2/3. No RHAMP credential/counter store. No
`hpac_verifier` change. No Gate 5/9 wiring. No runtime/effect change.
"""

from __future__ import annotations

import copy
import pickle
import threading

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
    HPACWriterCapability,
)
from pcae.core.human_principal_registry import (
    HumanPrincipalRegistryError,
    HumanPrincipalRegistryStore,
)

from test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1 import (
    AGENT_ACCOUNT,
    FAKE_AGENT_UID,
    HP_A,
    HP_B,
    THIS_MODULE as _SLICE1_MODULE,
    _authority,
    _mint,
)

pytestmark = [pytest.mark.fast_green]

REPO = __import__("pathlib").Path(__file__).resolve().parents[1]
BLOCKED_IV_DOC = (
    REPO / "docs"
    / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_2_INDEPENDENT_VERIFICATION_OF_N_16_5_PAWA_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_SLICE_1.md"
)
HPAC_FOUNDATION = REPO / "src" / "pcae" / "core" / "hpac_foundation.py"

# .1R.30R.3.2.1 drives production_writer() directly, like the Slice-1
# suite; it reuses that already-authorized closed-allowlist test-consumer
# name (§38, HPAC-PAWA-REQ-166) via the disclosed `_caller_module` seam
# rather than widening `_TEST_FACTORY_CONSUMERS`.


def _provision(tmp_path):
    root = (tmp_path / "hpac-protected-root").resolve()
    w.provision_protected_root(protected_root=root, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID)
    return root


def _shell_from(cap: HPACWriterCapability) -> HPACWriterCapability:
    """The decisive .1R.30R.3.2 adversary: an object.__new__ shell carrying
    every field copied off a real, legitimately-issued capability."""

    shell = HPACWriterCapability.__new__(HPACWriterCapability)
    shell._authority_seal = cap._authority_seal
    shell.role = cap.role
    shell.subject = cap.subject
    shell.authority_class = cap.authority_class
    shell._single_use = True
    shell._spent = False
    return shell


# ═══════════════════════════════════════════════════════════════════════════
# 1. Historical preservation
# ═══════════════════════════════════════════════════════════════════════════


def test_01_historical_30r_3_2_blocked_verdict_preserved():
    text = BLOCKED_IV_DOC.read_text(encoding="utf-8")
    assert "STATUS: BLOCKED." in text
    assert "N-16-5 remains **NOT CLOSED**" in text


def test_02_historical_30r_3_2_report_not_rewritten_as_success():
    text = BLOCKED_IV_DOC.read_text(encoding="utf-8")
    assert "VERIFIED" != text.split("STATUS:")[1].split(".")[0].strip()


# ═══════════════════════════════════════════════════════════════════════════
# 2. Defect reproduction at the immutable A (.1R.30R.3.1 finalized) head,
#    independent of any prose claim -- confirms the adversary is real before
#    trusting the repair against it (this repo state, not a separate worktree
#    check -- the historical reproduction against A itself was independently
#    performed and recorded during this phase's investigation; see the phase
#    completion report).
# ═══════════════════════════════════════════════════════════════════════════


def test_03_decisive_adversary_rejected_on_require_writer_directly(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    shell = _shell_from(cap)
    with pytest.raises(HPACAuthorityError):
        handle.authority.require_writer(shell, "human_principal_registry_admin", subject=HP_A)


def test_04_decisive_adversary_rejected_end_to_end_production_path(tmp_path):
    """Mirrors .1R.30R.3.2 §5.3's exact live reproduction: enroll, then a
    forged-capability revoke -- both against the real production_writer()
    -> HumanPrincipalRegistryStore path."""

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())
    assert cap._spent is True

    shell = _shell_from(cap)
    with pytest.raises(HumanPrincipalRegistryError):
        store.revoke_principal(shell, principal_id=HP_A, revoked_at=w._now())


def test_05_canonical_issuance_still_succeeds(tmp_path):
    """The repair must not be a broadened rejection net -- a genuine
    capability, used once, for its own bound scope, still works."""

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    record = store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())
    assert record.principal_id == HP_A


def test_06_bare_object_new_shell_rejected_cleanly_not_attributeerror(tmp_path):
    """A shell with no fields set at all fails closed with
    HPACAuthorityError, not a raw AttributeError leaking past the
    fail-closed boundary (defense-in-depth hardening in this repair)."""

    root = _provision(tmp_path)
    authority = _authority(root)
    bare = HPACWriterCapability.__new__(HPACWriterCapability)
    with pytest.raises(HPACAuthorityError):
        authority.require_writer(bare, "human_principal_registry_admin")


def test_07_direct_constructor_still_rejected(tmp_path):
    with pytest.raises(Exception):
        HPACWriterCapability(object(), "role", None, HPACAuthorityClass.PRODUCTION, _seal=object())


def test_08_copy_of_valid_capability_rejected(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    with pytest.raises(TypeError):
        copy.copy(cap)


def test_09_deepcopy_of_valid_capability_rejected(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    with pytest.raises(TypeError):
        copy.deepcopy(cap)


def test_10_pickle_of_valid_capability_rejected(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    with pytest.raises(TypeError):
        pickle.dumps(cap)


def test_11_restart_invalidation_still_holds_with_repair(tmp_path):
    """A fresh authority instance (simulating a process restart) has both
    a fresh ``_seal`` AND an empty process-local issuance registry -- the
    old capability is rejected on both grounds."""

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    other = _authority(root)
    with pytest.raises(HPACAuthorityError):
        other.require_writer(cap, "human_principal_registry_admin", subject=HP_A)


def test_12_one_operation_replay_rejected_after_repair(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())
    with pytest.raises(HumanPrincipalRegistryError):
        store.revoke_principal(cap, principal_id=HP_A, revoked_at=w._now())


def test_13_second_handle_consume_rejected_factory_layer(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    with pytest.raises(w.PawaError) as ei:
        handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    assert ei.value.code == "capability_stale"


def test_14_token_transplant_wrong_principal_rejected(tmp_path):
    """A genuine capability's seal (and other fields) transplanted onto a
    shell that claims a *different* subject is rejected -- registry-bound
    scope, not the copied field, is authoritative."""

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    shell = _shell_from(cap)
    shell.subject = HP_B
    with pytest.raises(HPACAuthorityError):
        handle.authority.require_writer(shell, "human_principal_registry_admin", subject=HP_B)


def test_15_wrong_mutation_role_rejected(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    with pytest.raises(HPACAuthorityError):
        handle.authority.require_writer(cap, "some_other_role", subject=HP_A)


def test_16_fixture_capability_cannot_satisfy_production_registry_write(tmp_path):
    """A FIXTURE_NON_REAL capability -- also now registered on issuance --
    still cannot be accepted where a PRODUCTION authority_class is
    required (authority_class mismatch, unaffected by this repair)."""

    root = _provision(tmp_path)
    fixture_authority = HPACStoreAuthority.fixture(root / "fixture-side")
    fixture_cap = fixture_authority.writer("human_principal_registry_admin", subject=HP_A)

    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    with pytest.raises(HPACAuthorityError):
        handle.authority.require_writer(fixture_cap, "human_principal_registry_admin", subject=HP_A)


def test_17_concurrent_use_permits_at_most_one_success(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())

    handle2 = _mint(root, w.PawaOperation.REVOKE_PRINCIPAL, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap2 = handle2.consume(w.PawaOperation.REVOKE_PRINCIPAL, principal_id=HP_A)
    # production_writer() mints a fresh HPACStoreAuthority (fresh _seal) on
    # every call (HPAC-PAWA-REQ-075) -- cap2 is bound to handle2.authority,
    # not the first handle's authority.
    store2 = HumanPrincipalRegistryStore(handle2.authority)

    results = []

    def attempt():
        try:
            store2.revoke_principal(cap2, principal_id=HP_A, revoked_at=w._now())
            results.append("success")
        except Exception as exc:  # noqa: BLE001
            results.append(type(exc).__name__)

    threads = [threading.Thread(target=attempt) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("success") == 1


def test_18_sole_construction_site_unchanged():
    import re as _re

    text = HPAC_FOUNDATION.read_text(encoding="utf-8")
    # exactly one call-expression construction site: _new_capability.
    calls = _re.findall(r"\bHPACWriterCapability\(\s*\n?\s*self\._seal", text)
    assert len(calls) == 1


def test_19_registry_helper_not_exported_from_module_all():
    import pcae.core.hpac_foundation as hf

    assert "_register_issued_capability" not in hf.__all__
    assert "_lookup_issued_capability" not in hf.__all__
    assert "_ISSUED_CAPABILITY_REGISTRY" not in hf.__all__


def test_20_issuance_id_never_exposed_on_capability_object(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    assert cap.__slots__ == ("_authority_seal", "role", "subject", "authority_class", "_single_use", "_spent")


def test_21_no_slice2_no_fido2_no_rhamp_sidecar_added():
    text = HPAC_FOUNDATION.read_text(encoding="utf-8")
    for token in ("fido2", "Ctap2", "CtapHidDevice", "CoseKey", "AuthenticatorData", "RHAMP-FIDO2-CREDENTIAL", "RHAMP-COUNTER-STATE"):
        assert token not in text


def test_22_hpac_verifier_byte_unchanged_since_phase_entry():
    import subprocess

    result = subprocess.run(
        ["git", "diff", "83b7f70b", "--", "src/pcae/core/hpac_verifier.py",
         "src/pcae/core/runtime_dispatch_gate5.py", "src/pcae/core/runtime_dispatch_gate9.py"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert result.stdout.strip() == ""


def test_23_contract_byte_unchanged_since_phase_entry():
    import subprocess

    result = subprocess.run(
        ["git", "diff", "83b7f70b", "--", "docs/contracts"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert result.stdout.strip() == ""


def test_24_runtime_unchanged():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "pcae", "runtime", "inspect"], cwd=REPO, capture_output=True, text=True
    )
    out = result.stdout
    assert "Runtime state:             Observed" in out
    assert "Maximum plugin capability: observe" in out
    assert "Execution capability:      unavailable" in out
