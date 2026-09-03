"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5 — Mandatory Real-CTAP2-Hardware
Verification and N-16-5 Closure.

RESULT: **BLOCKED.** N-16-5: **NOT CLOSED.**

A genuine CTAP2 roaming USB security key was exercised through the production
native provider path. Both mandatory ceremonies were rejected by the
authenticator with ``CTAP2_ERR_INVALID_OPTION (0x2C)`` because
``NativeCtap2Provider`` requests user verification with a bare ``uv`` option,
which CTAP 2.1 authenticators reject (finding H-1). Repairing that handshake is
a production change outside this certification phase's scope (governing prompt
§55).

This suite is **hardware-free and deterministic**: it pins the phase-entry
SHA, proves the contracts and production source are byte-unchanged, proves the
production provider (not the deterministic fixture) is what resolves, pins the
exact source locus of finding H-1, and proves N-16-5 remains not closed with
the runtime / first-effect / N-16-6 / N-16-7 boundaries unchanged. The
real-hardware observations themselves are recorded in the canonical phase
document, not as CI-executed assertions (RHAMP-REQ-154: the automated suite
never requires real hardware).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Phase-entry SHA A = finalized .1R.30R.4R.2 head.
A = "0b973e2e1a433dd8983a17fc320f2bee55c430b8"

PHASE_DOC = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5_N_16_5_MANDATORY_REAL_CTAP2_HARDWARE_VERIFICATION_AND_N_16_5_CLOSURE.md"
)
CTAP2_MODULE = REPO_ROOT / "src" / "pcae" / "core" / "hpac_rhamp_ctap2.py"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


# ── 1. Phase entry ────────────────────────────────────────────────────────

def test_phase_entry_sha_is_the_finalized_30r4r2_head():
    assert _git("cat-file", "-t", A).strip() == "commit"
    subject = _git("show", "-s", "--format=%s", A).strip()
    assert ".1R.30R.4R.2" in subject


# ── 2. Contracts byte-unchanged since A ───────────────────────────────────

def test_all_contracts_byte_unchanged_since_A():
    assert _git("diff", "--name-only", A, "HEAD", "--", "docs/contracts").strip() == ""


@pytest.mark.parametrize(
    "contract",
    [
        "REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md",
        "HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md",
        "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
    ],
)
def test_named_normative_contract_unchanged(contract):
    assert (
        _git("diff", "--stat", A, "HEAD", "--", f"docs/contracts/{contract}").strip()
        == ""
    )


# ── 3. Production source unchanged — this is a verification phase ──────────

def test_no_production_or_script_or_pyproject_change_since_A():
    # Through the .1R.30R.5 finalized head this verification phase changed no
    # production source / script / pyproject byte (reconciled by .1R.30R.5R).
    assert (
        _git(
            "diff", "--name-only", A, "9f004ea9", "--", "src/pcae", "scripts", "pyproject.toml"
        ).strip()
        == ""
    )
    # The dedicated .1R.30R.5R repair phase changes exactly one src/pcae file
    # and no script / pyproject byte.
    changed = set(
        _git("diff", "--name-only", A, "HEAD", "--", "src/pcae", "scripts", "pyproject.toml").split()
    )
    assert changed <= {"src/pcae/core/hpac_rhamp_ctap2.py"}, changed


# ── 4. Production provider resolves (not the deterministic fixture) ───────

def test_resolve_production_ctap2_provider_is_the_native_provider():
    from pcae.core.hpac_rhamp_ctap2 import (
        NativeCtap2Provider,
        resolve_production_ctap2_provider,
    )

    provider = resolve_production_ctap2_provider()
    assert isinstance(provider, NativeCtap2Provider)
    assert provider.PROVIDER_KIND == "native-ctap2"


def test_deterministic_provider_is_permanently_simulation_only():
    from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider

    assert DeterministicCtap2Provider.SIMULATION_ONLY is True
    # no constructor override of the class constant
    inst = DeterministicCtap2Provider()
    assert inst.SIMULATION_ONLY is True


def test_deterministic_fixture_result_never_satisfies_certification():
    # The fixture honours the bare `uv` option that real CTAP 2.1 hardware
    # rejects — so an all-green automated suite is not hardware evidence
    # (RHAMP-INV-018). This is a NON_REAL result and must be distinguishable.
    import os

    from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider

    r = DeterministicCtap2Provider().make_credential(
        client_data_hash=os.urandom(32), user_id=b"x", user_name="x"
    )
    assert r.up is True and r.uv is True  # lenient fixture
    assert DeterministicCtap2Provider.SIMULATION_ONLY is True


# ── 5. Finding H-1 — exact source locus ──────────────────────────────────

def test_h1_locus_native_provider_requests_uv_as_a_bare_option():
    """Finding H-1's source locus: ``NativeCtap2Provider`` used to pass a bare
    ``uv`` option to both ceremonies, which CTAP 2.1 authenticators reject with
    0x2C. Reconciled by .1R.30R.5R (the dedicated repair phase): the bare-``uv``
    shape is now GONE and the CTAP 2.1 PIN/UV auth-protocol handshake is in
    place. This guard is widened, not weakened — it still anchors the same
    locus, now asserting the repaired state.
    """
    src = CTAP2_MODULE.read_text(encoding="utf-8")
    # the pre-repair invalid shapes are gone
    assert 'options = {"rk": False, "uv": True}' not in src  # make_credential
    assert 'options={"uv": True}' not in src  # get_assertion
    # the PIN/UV auth-protocol handshake is present
    assert "ClientPin" in src
    assert "pin_uv_param" in src and "pin_uv_protocol" in src
    assert "_obtain_pin_uv" in src


# ── 6. N-16-5 remains NOT CLOSED ─────────────────────────────────────────

def test_phase_doc_records_blocked_and_n1655_not_closed():
    text = PHASE_DOC.read_text(encoding="utf-8")
    assert "**Status:** **BLOCKED.** N-16-5: **NOT CLOSED.**" in text
    assert "CTAP2_ERR_INVALID_OPTION" in text
    assert "RHAMP-REQ-152" in text and "RHAMP-INV-018" in text
    # F-1 and the sibling stale guards are carried forward, not repaired here
    assert "F-1" in text and "test_no_contract_change_since_r20_head" in text
    assert "test_no_contract_change_since_b30" in text


def test_project_status_current_phase_is_30r5_blocked():
    text = (REPO_ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    head = text.split("## Prior Phase", 1)[0]
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5" in head
    assert "BLOCKED" in head
    assert "N-16-5" in head and "NOT CLOSED" in head


# ── 7. Boundaries unchanged ──────────────────────────────────────────────

def test_runtime_still_observed_and_unavailable():
    out = subprocess.run(
        ["python", "-m", "pcae", "runtime", "inspect"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    ).stdout
    assert "not_implemented" in out
    assert "Observed" in out
    assert "unavailable" in out
    import re

    assert re.search(r"Plugin count:\s+0\b", out)
    assert re.search(r"Capability count:\s+0\b", out)


#: finalized .1R.30R.5 BLOCKED head — the upper bound of *this phase's* own
#: window (reconciled by .1R.30R.5R).
_30R5_FINALIZED_HEAD = "9f004ea9"


def test_no_effect_adapter_or_dispatch_introduced_since_A():
    # Through the .1R.30R.5 finalized head, src/pcae was byte-unchanged since A.
    assert _git("diff", A, _30R5_FINALIZED_HEAD, "--", "src/pcae").strip() == ""
    # The dedicated .1R.30R.5R repair phase legitimately changes exactly one
    # src/pcae file (the CTAP2 PIN/UV handshake); no effect-adapter / dispatch
    # primitive is introduced anywhere.
    changed = {
        l.split(" b/")[-1] for l in _git("diff", A, "HEAD", "--", "src/pcae").splitlines()
        if l.startswith("diff --git ")
    }
    assert changed <= {"src/pcae/core/hpac_rhamp_ctap2.py"}, changed
    added = [
        l for l in _git("diff", A, "HEAD", "--", "src/pcae").splitlines()
        if l.startswith("+") and not l.startswith("+++")
    ]
    assert not any("adapter.dispatch(" in l or "DispatchEnvelope" in l for l in added)
    assert not any("subprocess" in l or "os.fork" in l or "posix_spawn" in l for l in added)


def test_this_phase_touched_only_doc_test_and_status_files():
    # "this phase" = .1R.30R.5; its window ends at its finalized head.
    changed = {
        line.split("\t")[-1]
        for line in _git("diff", "--name-only", A, _30R5_FINALIZED_HEAD).splitlines()
        if line.strip()
    }
    allowed_prefixes = ("docs/", "tests/", "tasks/", ".pcae/")
    allowed_exact = {"PROJECT_STATUS.md", "CHANGELOG.md"}
    for path in changed:
        assert path in allowed_exact or path.startswith(allowed_prefixes), path
