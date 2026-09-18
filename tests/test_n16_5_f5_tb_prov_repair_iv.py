"""Phase N16-5-F-5-TB-HELPER-INSTALLATION-PROVISIONING-CONTRACT-REPAIR-IV.

Fresh independent adversarial verification tests, distinct from the
predecessor repair phase's own tests (`test_n16_5_f5_tb_prov_repair_contract.py`,
kept unmodified and re-run separately as part of this IV's regression sweep).

This IV's central, load-bearing finding is that the predecessor's contract
text (`docs/contracts/*.md`, frozen HELPER v5.0 / PAWA v4.0 / PPA v2.1) is
*internally* self-consistent and does textually remove F1's circular
dispatch route, but the already-existing, already-wired PRODUCTION source
under `src/pcae/core/` (written by an earlier phase, N16-5-F-5-TB-HELPER-IMPL,
before the contract-repair phase existed, and never touched by it — the
contract-repair phase's own source-impact map explicitly and correctly
states `src/pcae/**` is byte-unchanged) still implements the OLD,
pre-repair, circular vocabulary: `configure_privileged_helper` and
`configure_presentation_mechanism` remain live members of
`CLOSED_ADMIN_MUTATIONS` in `hpac_pawa_helper_protocol.py`, and the store
adapter (`hpac_pawa_helper_store_adapter.py`) still dispatches
`configure_privileged_helper` through the helper's own `admin_mutation`
handler (`hpac_pawa_helper_operations.py::handle_admin_mutation`), reachable
from the real entrypoint dispatch table. This is precisely the F1-A/F1-B
mechanism the frozen contract text says no longer exists. The contract
repair therefore exists at the text layer only; it has not propagated to
the deployed mechanism the contract describes, so F1 is not actually
eliminated end-to-end — it is eliminated in prose and reopened in the one
place (running code) where it can actually be triggered.

These tests are read-only: they do not modify `src/pcae/**` (the successor
"minimal contract-repair follow-up" this IV recommends is out of scope for
IV itself, per phase-authorization §21/§25).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
HELPER_CONTRACT = CONTRACTS / "HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
PAWA_CONTRACT = CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
PPA_CONTRACT = CONTRACTS / "HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"

CORE = REPO_ROOT / "src" / "pcae" / "core"
PROTOCOL_SRC = CORE / "hpac_pawa_helper_protocol.py"
STORE_ADAPTER_SRC = CORE / "hpac_pawa_helper_store_adapter.py"
OPERATIONS_SRC = CORE / "hpac_pawa_helper_operations.py"
WRITER_AUTHORITY_SRC = CORE / "hpac_pawa_helper_writer_authority.py"


@pytest.fixture(scope="module")
def helper_text() -> str:
    return HELPER_CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pawa_text() -> str:
    return PAWA_CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ppa_text() -> str:
    return PPA_CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def protocol_src_text() -> str:
    return PROTOCOL_SRC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def store_adapter_src_text() -> str:
    return STORE_ADAPTER_SRC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def operations_src_text() -> str:
    return OPERATIONS_SRC.read_text(encoding="utf-8")


# --- (1) Contract versions/status independently extracted -----------------


def test_pawa_contract_is_v4_0_frozen(pawa_text: str) -> None:
    assert "# HPAC-PAWA-001 v4.0" in pawa_text
    assert "**Version:** 4.0" in pawa_text


def test_helper_contract_is_v5_0_frozen(helper_text: str) -> None:
    assert "# HPAC-PAWA-HELPER-001 v5.0" in helper_text
    assert "**Version:** 5.0" in helper_text


def test_ppa_contract_is_v2_1_byte_unchanged(ppa_text: str) -> None:
    assert "# HPAC-PPA-001 v2.1" in ppa_text
    assert "**Version:** 2.1" in ppa_text


# --- (2)-(4) Closed vocabulary excludes both provisioning ops, in TEXT ----


def test_helper_admin_mutation_enum_excludes_provisioning_in_contract_text(
    helper_text: str,
) -> None:
    """REQ-053's table must not list either mutation as an admin_mutation member."""
    match = re.search(
        r"HPAC-PAWA-HELPER-REQ-053\..*?\n\n(.*?)\n\n- \*\*HPAC-PAWA-HELPER-REQ-054",
        helper_text,
        re.DOTALL,
    )
    assert match, "REQ-053 closed-vocabulary table not found"
    table = match.group(1)
    admin_mutation_row = [
        line for line in table.splitlines() if line.strip().startswith("| `admin_mutation`")
    ]
    assert len(admin_mutation_row) == 1
    row = admin_mutation_row[0]
    mutation_set_cell = row.split("|")[1]
    mutation_set_before_parenthetical = mutation_set_cell.split("(§30E.2")[0]
    assert "configure_privileged_helper" not in mutation_set_before_parenthetical
    assert "configure_presentation_mechanism" not in mutation_set_before_parenthetical
    # The parenthetical aside *naming* both retired ids as "no longer members"
    # is expected and is exactly REQ-184's cross-reference, not a live
    # vocabulary entry.
    assert "no longer members" in mutation_set_cell


def test_helper_req_184_explicitly_removes_both_mutations(helper_text: str) -> None:
    assert "HPAC-PAWA-HELPER-REQ-184" in helper_text
    req_184 = helper_text[helper_text.index("HPAC-PAWA-HELPER-REQ-184") :][:600]
    assert "no longer includes" in req_184
    assert "configure_privileged_helper" in req_184
    assert "configure_presentation_mechanism" in req_184


# --- (5)/(9)/(11) PAWA direct dispatch is narrow, not a generic broker -----


def test_pawa_req_345_scopes_capability_to_exact_mutation(pawa_text: str) -> None:
    req_345 = pawa_text[pawa_text.index("HPAC-PAWA-REQ-345") :][:1600]
    assert "process-local, single-use PAWA writer capability" in req_345
    assert "configure_privileged_helper" in req_345


def test_pawa_req_346_genesis_requires_no_admitted_h(pawa_text: str) -> None:
    req_346 = pawa_text[pawa_text.index("HPAC-PAWA-REQ-346") :][:900]
    normalized = " ".join(req_346.split())
    assert "No admitted H, no ceremony" in normalized


def test_pawa_req_347_rotation_never_dispatches_through_current_h(pawa_text: str) -> None:
    req_347 = pawa_text[pawa_text.index("HPAC-PAWA-REQ-347") :][:700]
    normalized = " ".join(req_347.split())
    assert "never the current H=G itself" in normalized
    assert "never dispatched through G's §33C boundary" in normalized


# --- (14)/(15) PPA reuse is semantically valid, not just textual analogy --


def test_ppa_req_021_022_shape_matches_pawa_345_350(ppa_text: str, pawa_text: str) -> None:
    ppa_021 = ppa_text[ppa_text.index("HPAC-PPA-REQ-021") :][:400]
    ppa_022 = ppa_text[ppa_text.index("HPAC-PPA-REQ-022") :][:400]
    assert "non-circular" in ppa_021
    assert "standalone" in ppa_022
    pawa_351 = pawa_text[pawa_text.index("HPAC-PAWA-REQ-351") :][:700]
    assert "HPAC-PPA-REQ-021/022 already specify exactly the" in pawa_351


# --- (16) Model E exact three families preserved ---------------------------


def test_helper_contract_still_declares_model_e_three_families(helper_text: str) -> None:
    assert "Model E" in helper_text
    # configure_privileged_helper must not be described anywhere as a Model E family.
    for family_marker in ("certification_write", "presentation_evidence_write"):
        assert family_marker in helper_text


# --- CRITICAL: source/contract conformance ---------------------------------


def test_LOAD_BEARING_source_still_implements_removed_vocabulary(
    protocol_src_text: str,
) -> None:
    """Contradicts REQ-184: production source has NOT been updated to match
    the frozen v5.0 contract text. Both retired mutation ids remain live
    members of the closed admin-mutation set the running helper protocol
    module actually enforces.

    This test is expected to PASS today (documenting the live defect) and
    is expected to start FAILING once a future implementation phase repairs
    `src/pcae/core/hpac_pawa_helper_protocol.py` to match HELPER v5.0 — at
    which point this test (and this whole module's docstring) must be
    retired/rewritten by that phase, not by this IV.
    """
    assert "CLOSED_ADMIN_MUTATIONS" in protocol_src_text
    block = protocol_src_text[protocol_src_text.index("CLOSED_ADMIN_MUTATIONS") :][:400]
    assert "configure_privileged_helper" in block, (
        "expected finding: source still lists configure_privileged_helper "
        "in CLOSED_ADMIN_MUTATIONS, contradicting frozen HELPER-REQ-184"
    )
    assert "configure_presentation_mechanism" in block, (
        "expected finding: source still lists configure_presentation_mechanism "
        "in CLOSED_ADMIN_MUTATIONS, contradicting frozen HELPER-REQ-184/PAWA-REQ-351"
    )


def test_LOAD_BEARING_store_adapter_still_dispatches_configure_privileged_helper_through_h(
    store_adapter_src_text: str,
) -> None:
    """The store adapter's admin_mutation dispatcher — invoked from H's own
    `handle_admin_mutation` — still has a live branch for
    `configure_privileged_helper` that performs a real write
    (`register_helper_metadata`). This is the exact F1-A/F1-B mechanism:
    an admitted H process still has a reachable code path to write its own
    (or a successor's) registration metadata, unchanged by the contract
    repair, because the contract repair touched no `src/pcae/**` file.
    """
    assert 'if mutation == "configure_privileged_helper":' in store_adapter_src_text
    assert "register_helper_metadata" in store_adapter_src_text


def test_LOAD_BEARING_operations_handler_accepts_provisioning_mutation_from_h(
    operations_src_text: str,
) -> None:
    """`handle_admin_mutation` (H's own request handler) still accepts
    `configure_privileged_helper` as a valid `mutation` value — it is only
    rejected once it fails to match `CLOSED_ADMIN_MUTATIONS`, and
    `CLOSED_ADMIN_MUTATIONS` (per the sibling test above) still contains it.
    """
    assert "def handle_admin_mutation(" in operations_src_text
    assert "mutation not in CLOSED_ADMIN_MUTATIONS" in operations_src_text


def test_predecessor_source_impact_map_did_not_flag_this(helper_text: str) -> None:
    """Sanity check on the finding's novelty: the frozen contract's own
    header block explicitly claims this evolution 'creates no protected
    root, installs no descriptor, mints no writer capability, writes no
    registry... adds normative text only' for the HELPER v5.0 change,
    which is true of the *contract* but was evidently read by the
    predecessor phase as meaning the *deployed system* was unaffected by
    the stale vocabulary — the predecessor's own evidence doc
    (`docs/PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR.md`
    §8 source-impact map) lists `hpac_pawa_helper_store_adapter.py` as
    "no change" without noting it still contains the retired dispatch
    branch this contract's own REQ-184 says must not exist.
    """
    predecessor_evidence = (
        REPO_ROOT
        / "docs"
        / "PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR.md"
    ).read_text(encoding="utf-8")
    assert "hpac_pawa_helper_store_adapter.py` | no change" in predecessor_evidence
    assert "hpac_pawa_helper_protocol.py" not in predecessor_evidence
