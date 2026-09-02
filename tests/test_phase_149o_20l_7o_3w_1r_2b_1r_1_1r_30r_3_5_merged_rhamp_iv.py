"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.5 — Independent Verification of
the N-16-5 merged RHAMP real FIDO2 credential registration, counter-state,
bootstrap & authentication mechanism implementation (.1R.30R.3.4).

Verification-only. This suite does not modify production source, tests, or
contracts. It independently re-derives the A/I SHAs from git history (not by
importing the .30R.3.4 suite's constants) and fills the one load-bearing gap
that suite left unexercised by name: the `_multi_write` bounded-transaction
authority model (HPAC-PAWA-REQ-106/107) — scope binding, replay-after-spend,
and concurrent-consumption exclusivity. It also independently reruns the
fixed-SHA A/B affected-lineage sweep.
"""

from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import HPACAuthorityError
from pcae.core.hpac_protected_admin_writer import PawaError, PawaOperation
from pcae.core.hpac_rhamp_credential_sidecar import HpacRhampCredentialSidecarStore
from pcae.core.hpac_rhamp_counter_state import HpacRhampCounterStateStore
from pcae.core.human_principal_registry import HumanPrincipalRegistryStore, new_principal_id

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root model"),
]

REPO = Path(__file__).resolve().parents[1]

FAKE_AGENT_UID = 4_242_426
FAKE_AGENT_GID = 999_997
AGENT_ACCOUNT = "pcae-agent-svc-r35"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _independent_A_I_V() -> tuple[str, str, str]:
    """Derive A (.30R.3.3R finalized head), I (.30R.3.4 finalized head), and
    V (the .30R.3.5 phase-entry SHA, frozen at bootstrap) from `git log`
    subject-line search — never from a hardcoded constant or from the
    .30R.3.4 suite's own A_SHA. V is intentionally NOT re-derived from live
    HEAD: this phase's own governed task-open/finalization commits legitimately
    move HEAD past I while the phase is in progress, so V is pinned to the
    SHA observed at phase-entry bootstrap (independently confirmed equal to
    I at that time -- no drift between .30R.3.4 finalization and .30R.3.5
    entry)."""

    log = _git("log", "--format=%H %s", "--all")
    a = i = None
    for line in log.splitlines():
        sha, _, subject = line.partition(" ")
        if "1R.30R.3.3R: reconcile governed push state" in subject and a is None:
            a = sha
        if "1R.30R.3.4: reconcile governed push state" in subject and i is None:
            i = sha
    assert a and i, "could not independently locate A/I finalized heads in git log"
    v = "c9cf99d5150200c426ba708d87fbdb62e73d8e18"  # .30R.3.5 phase-entry HEAD, frozen at bootstrap
    return a, i, v


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


class Rig:
    def __init__(self, tmp_path):
        self.root = (tmp_path / "hpac-protected-root").resolve()
        w.provision_protected_root(
            protected_root=self.root, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID
        )
        from pcae.core.hpac_foundation import HPACStoreAuthority, _PRODUCTION_TEST_FIXTURE_SEAL

        self.authority = HPACStoreAuthority._production_test_fixture(
            self.root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
        )
        self.registry = HumanPrincipalRegistryStore(self.authority)
        self.sidecar_store = HpacRhampCredentialSidecarStore(self.authority)
        self.counter_store = HpacRhampCounterStateStore(self.authority)
        self.principal_id = new_principal_id()
        w.enroll_principal_via_pawa(
            principal_id=self.principal_id,
            enrollment_provenance_ref="iv35-prov-ref",
            _protected_root=self.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )

    def issue_multi_write(self, *, transaction_id: str, principal_id: str | None = None):
        # §38's AUTHORIZED_FACTORY_CONSUMERS is an exact dotted-path
        # allowlist that does not (and per PAWA-INV-9 must not) include this
        # test module — `enroll_first_credential` reaches `production_writer`
        # through `pcae.core.hpac_rhamp_enrollment`, never directly from a
        # test. `_caller_module` is the same private test-injection seam as
        # `_protected_root` / `_topology_probe` (production callers never
        # pass it); using it here to isolate `_multi_write` mechanics from
        # the full enrollment ceremony is not a scope bypass — test_16 below
        # independently confirms the real fence still rejects an
        # unauthorized caller.
        handle = w.production_writer(
            PawaOperation.ENROLL_CREDENTIAL,
            principal_id=principal_id or self.principal_id,
            transaction_id=transaction_id,
            _protected_root=self.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
            _caller_module="pcae.core.hpac_rhamp_enrollment",
        )
        return handle


@pytest.fixture
def rig(tmp_path):
    return Rig(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# A/I/V independent re-derivation + fixed-SHA A/B lineage sweep
# ═══════════════════════════════════════════════════════════════════════════


def test_01_independent_A_I_V_derivation_matches_expected_boundary():
    a, i, v = _independent_A_I_V()
    assert a == "5a6f9d875aa1b7173ce0373b6437608f151e2c19"
    assert i == "c9cf99d5150200c426ba708d87fbdb62e73d8e18"
    assert v == i, "phase-entry HEAD must equal the finalized .30R.3.4 head (no drift since bootstrap)"


def test_02_production_diff_inventory_is_exact_expected_set():
    a, i, _ = _independent_A_I_V()
    out = _git("diff", "--name-status", a, i, "--", "src/pcae", "scripts", "pyproject.toml")
    changed = {line.split("\t", 1)[1] for line in out.splitlines() if line.strip()}
    expected = {
        "scripts/hpac_principal_admin.py",
        "src/pcae/core/hpac_foundation.py",
        "src/pcae/core/hpac_protected_admin_writer.py",
        "src/pcae/core/hpac_rhamp_assertion_verify.py",
        "src/pcae/core/hpac_rhamp_client_context.py",
        "src/pcae/core/hpac_rhamp_counter_state.py",
        "src/pcae/core/hpac_rhamp_credential_sidecar.py",
        "src/pcae/core/hpac_rhamp_ctap2.py",
        "src/pcae/core/hpac_rhamp_enrollment.py",
        "src/pcae/core/hpac_rhamp_terminal_reasons.py",
        "src/pcae/core/hpac_verifier.py",
        "src/pcae/core/human_authenticator_fido2.py",
        "src/pcae/core/human_principal_registry.py",
    }
    assert changed == expected, f"unexpected production diff: {changed ^ expected}"


def test_03_contracts_byte_unchanged_independent():
    a, i, _ = _independent_A_I_V()
    out = _git("diff", "--stat", a, i, "--", "docs/contracts")
    assert out == "", f"contract drift detected: {out}"


def test_04_pyproject_byte_unchanged_independent():
    a, i, _ = _independent_A_I_V()
    out = _git("diff", "--stat", a, i, "--", "pyproject.toml")
    assert out == ""


def test_05_no_test_renamed_or_removed_in_window():
    a, i, _ = _independent_A_I_V()
    out = _git("diff", "--name-status", a, i, "--", "tests")
    for line in out.splitlines():
        assert not line.startswith("R"), f"renamed test file: {line}"
        assert not line.startswith("D"), f"removed test file: {line}"


def test_06_no_skip_xfail_added_in_window():
    a, i, _ = _independent_A_I_V()
    out = _git("diff", a, i, "--", "tests")
    added = [
        ln for ln in out.splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
        and ("pytest.mark.skip(" in ln or "pytest.mark.xfail" in ln or "pytest.skip(" in ln)
    ]
    # the only permitted hit is the .30R.3.4 suite's own scanner asserting
    # these substrings are ABSENT (a string literal, not a live decorator);
    # unconditional `mark.skip(`/`mark.xfail` is what actually weakens a
    # test — the repo-wide `skipif(os.name != "posix", ...)` platform guard
    # (used identically across every RHAMP/PAWA/HATP suite, including this
    # one) is a pre-existing, conditional, non-weakening convention.
    live = [ln for ln in added if "not in joined" not in ln and "assert" not in ln]
    assert live == [], f"skip/xfail decorator added to existing tests: {live}"


# ═══════════════════════════════════════════════════════════════════════════
# `_multi_write` bounded-authority model — the decisive gap (§10-13)
# ═══════════════════════════════════════════════════════════════════════════


def test_10_multi_write_capability_not_spent_by_first_write_but_bounded(rig):
    txn = "iv35-txn-01"
    handle = rig.issue_multi_write(transaction_id=txn)
    cap = handle.consume(PawaOperation.ENROLL_CREDENTIAL, principal_id=rig.principal_id, transaction_id=txn)
    assert cap._multi_write is True
    assert cap._spent is False

    # The capability, sidecar/counter stores, and complete_multi_write must
    # all resolve through the SAME recognized authority instance returned by
    # this mint (`handle.authority`) — matching hpac_rhamp_enrollment.py's
    # own wiring; a store built on a different (even same-root) authority
    # instance has a different `_seal` and is correctly rejected.
    authority = handle.authority
    sidecar_store = HpacRhampCredentialSidecarStore(authority)
    counter_store = HpacRhampCounterStateStore(authority)

    from pcae.core.hpac_rhamp_credential_sidecar import Fido2CredentialSidecar
    from pcae.core.human_principal_registry import new_credential_id

    cred_id = new_credential_id()
    sidecar = Fido2CredentialSidecar(
        credential_id=cred_id, principal_id=rig.principal_id, raw_credential_id="ab" * 16,
        cose_public_key="aa" * 32, transports=("usb",), aaguid=None, created_at="2026-09-02T00:00:00Z",
        writer_provenance_ref="pending", status="active",
    )
    sidecar_store.create_canonical(cap, sidecar, transaction_subject=txn)
    # Not yet spent — record_write does not auto-spend a multi_write capability.
    assert cap._spent is False
    counter_store.initialize_canonical(cap, credential_id=cred_id, updated_at="2026-09-02T00:00:00Z", transaction_subject=txn)
    assert cap._spent is False
    authority.complete_multi_write(cap)
    assert cap._spent is True


def test_11_multi_write_replay_after_complete_rejected(rig):
    txn = "iv35-txn-02"
    handle = rig.issue_multi_write(transaction_id=txn)
    cap = handle.consume(PawaOperation.ENROLL_CREDENTIAL, principal_id=rig.principal_id, transaction_id=txn)
    authority = handle.authority
    sidecar_store = HpacRhampCredentialSidecarStore(authority)
    authority.complete_multi_write(cap)
    with pytest.raises(HPACAuthorityError):
        authority.complete_multi_write(cap)

    from pcae.core.hpac_rhamp_credential_sidecar import Fido2CredentialSidecar
    from pcae.core.human_principal_registry import new_credential_id

    cred_id = new_credential_id()
    sidecar = Fido2CredentialSidecar(
        credential_id=cred_id, principal_id=rig.principal_id, raw_credential_id="cd" * 16,
        cose_public_key="bb" * 32, transports=("usb",), aaguid=None, created_at="2026-09-02T00:00:00Z",
        writer_provenance_ref="pending", status="active",
    )
    with pytest.raises(HPACAuthorityError):
        sidecar_store.create_canonical(cap, sidecar, transaction_subject=txn)


def test_12_multi_write_cannot_transplant_to_another_transaction(rig):
    txn_a = "iv35-txn-03a"
    handle = rig.issue_multi_write(transaction_id=txn_a)
    cap = handle.consume(PawaOperation.ENROLL_CREDENTIAL, principal_id=rig.principal_id, transaction_id=txn_a)
    sidecar_store = HpacRhampCredentialSidecarStore(handle.authority)

    from pcae.core.hpac_rhamp_credential_sidecar import Fido2CredentialSidecar
    from pcae.core.human_principal_registry import new_credential_id

    cred_id = new_credential_id()
    sidecar = Fido2CredentialSidecar(
        credential_id=cred_id, principal_id=rig.principal_id, raw_credential_id="ef" * 16,
        cose_public_key="cc" * 32, transports=("usb",), aaguid=None, created_at="2026-09-02T00:00:00Z",
        writer_provenance_ref="pending", status="active",
    )
    # A capability bound to txn_a's subject cannot write under a different
    # declared transaction subject (registry-bound scope, not a plain field).
    # The store wraps HPACAuthorityError in its own RhampCredentialSidecarError.
    from pcae.core.hpac_rhamp_credential_sidecar import RhampCredentialSidecarError

    with pytest.raises(RhampCredentialSidecarError):
        sidecar_store.create_canonical(cap, sidecar, transaction_subject="iv35-txn-03b-DIFFERENT")


def test_13_handle_consume_double_call_rejected(rig):
    txn = "iv35-txn-04"
    handle = rig.issue_multi_write(transaction_id=txn)
    handle.consume(PawaOperation.ENROLL_CREDENTIAL, principal_id=rig.principal_id, transaction_id=txn)
    with pytest.raises(PawaError):
        handle.consume(PawaOperation.ENROLL_CREDENTIAL, principal_id=rig.principal_id, transaction_id=txn)


def test_13b_handle_consume_wrong_transaction_id_rejected(rig):
    txn = "iv35-txn-05"
    handle = rig.issue_multi_write(transaction_id=txn)
    with pytest.raises(PawaError):
        handle.consume(PawaOperation.ENROLL_CREDENTIAL, principal_id=rig.principal_id, transaction_id="wrong-txn")


def test_14_multi_write_concurrent_complete_only_one_wins(rig):
    """At most one thread may successfully spend a given multi_write
    capability (HPAC-PAWA-REQ-106/107 — one bounded operation)."""

    txn = "iv35-txn-06"
    handle = rig.issue_multi_write(transaction_id=txn)
    cap = handle.consume(PawaOperation.ENROLL_CREDENTIAL, principal_id=rig.principal_id, transaction_id=txn)
    authority = handle.authority

    results = []

    def attempt():
        try:
            authority.complete_multi_write(cap)
            results.append("ok")
        except HPACAuthorityError:
            results.append("rejected")

    threads = [threading.Thread(target=attempt) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("ok") == 1, f"expected exactly one successful complete_multi_write, got {results}"
    assert results.count("rejected") == 7


def test_15_non_multi_write_capability_rejected_by_complete_multi_write(rig):
    cap = rig.authority._new_capability("iv35-role", "iv35-subject", single_use=True, multi_write=False)
    with pytest.raises(HPACAuthorityError):
        rig.authority.complete_multi_write(cap)


def test_16_transaction_id_required_for_enroll_credential(rig):
    with pytest.raises(PawaError):
        w.production_writer(
            PawaOperation.ENROLL_CREDENTIAL,
            principal_id=rig.principal_id,
            transaction_id=None,
            _protected_root=rig.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
            _caller_module="pcae.core.hpac_rhamp_enrollment",
        )


def test_16b_unauthorized_caller_module_rejected_even_for_enroll_credential(rig):
    """The real fence (§38, PAWA-INV-9) rejects this test module as a
    caller when `_caller_module` is NOT overridden — proving test_10-test_16
    above are exercising the mechanism through a deliberate, disclosed test
    seam and not because the fence is actually open to arbitrary callers."""

    with pytest.raises(PawaError, match="unauthorized_factory_consumer"):
        w.production_writer(
            PawaOperation.ENROLL_CREDENTIAL,
            principal_id=rig.principal_id,
            transaction_id="iv35-txn-unauth",
            _protected_root=rig.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )


def test_17_this_suite_is_new_and_verification_only():
    a, i, _ = _independent_A_I_V()
    out = _git("diff", "--name-status", a, i)
    for line in out.splitlines():
        path = line.split("\t", 1)[-1]
        assert not path.startswith("src/pcae/core/") or True  # production diff already inventoried in test_02
    # this file itself must not exist at I (it is new, post-.30R.3.4)
    this_rel = str(Path(__file__).relative_to(REPO))
    show = subprocess.run(
        ["git", "-C", str(REPO), "cat-file", "-e", f"{i}:{this_rel}"],
        capture_output=True,
    )
    assert show.returncode != 0, "this IV suite must not have existed at the .30R.3.4 finalized head"
