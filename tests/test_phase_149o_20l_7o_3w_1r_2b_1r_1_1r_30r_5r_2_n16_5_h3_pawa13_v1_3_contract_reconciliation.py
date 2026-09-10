"""Contract-level verification for phase N16-5-H3-PAWA13
(149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R)
— HPAC-PAWA-001 v1.2 -> v1.3 Certification-Coordinator Authority Contract
Reconciliation / Freeze.

Intentionally static / read-only. This phase freezes authority semantics and
implements NO production certification path: no `certification_writer`, no
`hpac_certification_coordinator`, no `scripts/hpac_certification_admin.py`, no
challenge / assertion / proof / Gate-5-binding / counter-state write, no
ceremony. The functional guards below are specifications for the H-3
implementation phase and the dedicated v1.3 contract IV, not tests authored now.

N-16-5 is NOT CLOSED by this phase.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Phase-entry SHA (H0) — the finalized predecessor
#: `…1.1R.1R.1R` N-16-5 H-3 production authority-path repair BLOCKED head.
H0 = "b2530066b062b14b3c6f6df7c71c3092b22f215b"

#: This v1.3 freeze phase's own finalized head (origin/main at completion).
_V13_FREEZE_END = "4977a2e5db362e9e86f898cf438578f00e8051f5"
#: N16-5-F5B1-READAUTH: a later governed phase evolved HPAC-PAWA-001 v1.3 ->
#: v1.4 (MINOR, S-3 -- the F-5-B1 recognized read / ceremony-entry authority).
#: The version / requirement-count / invariant-range assertions below were
#: point-in-time to v1.3; they are re-anchored to `_V13_FREEZE_END` (this
#: phase's own frozen head) or widened to "v1.3 baseline preserved, contiguous,
#: never renumbered". No test function renamed or removed; no test disabled.
_F5B1_READAUTH_ENTRY = "18d7da02435cac61159e9a90f86b2a586c4704d0"


def at_sha(sha: str, path: Path) -> bytes:
    rel = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)

PAWA = ROOT / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
PPA = ROOT / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
RHAMP = ROOT / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
HBDC = ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
PRED_REPORT = ROOT / (
    "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1R_1R_1R_"
    "N_16_5_H3_PRODUCTION_AUTHORITY_PATH_REPAIR_BLOCKED.md"
)

FIVE_ROLES = (
    "hpac_challenge_coordinator",
    "hpac_assertion_recorder",
    "human_authentication_proof_verifier",
    "hpac_gate5_binder",
    "hpac_rhamp_counter_state_verifier",
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(path: Path) -> str:
    return re.sub(r"\s+", " ", text(path))


def at_h0(path: Path) -> bytes:
    rel = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "show", f"{H0}:{rel}"], cwd=ROOT)


# --- 1. phase lineage / CPIPC -------------------------------------------------

def test_01_phase_entry_sha_resolves() -> None:
    got = subprocess.check_output(["git", "show", "-s", "--format=%H", H0], cwd=ROOT).decode().strip()
    assert got == H0


def test_02_cpipc_candidate_is_direct_valid_successor() -> None:
    from pcae.core import phase_id as p

    pred = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R"
    cand = pred + ".1R"
    a, b = p.parse(pred), p.parse(cand)
    assert p.is_valid(cand)
    assert p.same_series(a, b) and p.same_branch(a, b)
    assert p.compare(a, b) == "less"


def test_03_predecessor_h3_blocked_report_present() -> None:
    t = text(PRED_REPORT)
    assert "H-3" in t and "NOT REPAIRED" in t and "N-16-5: NOT CLOSED" in t


# --- 2. version / lineage ---------------------------------------------------

def test_04_contract_version_is_v1_3() -> None:
    # v1.3 was the frozen state at this phase's own finalized head.
    t = at_sha(_V13_FREEZE_END, PAWA).decode("utf-8")
    assert t.splitlines()[0].startswith("# HPAC-PAWA-001 v1.3 —")
    assert "**Version:** 1.3" in t
    assert "**Status:** FROZEN" in t
    # the current head is v1.3 or a later governed MINOR of the same contract,
    # still FROZEN, lineage never rewritten.
    cur = text(PAWA)
    # Reconciled by phase N16-5-F-5-TB-CONTRACT (HPAC-PAWA-001 v1.4 -> v2.0, MAJOR S-4; new companion HPAC-PAWA-HELPER-001 v1.0): a later governed MAJOR bumps the
    # header to v2.x; the v1.3 lineage prefix is never rewritten (asserted below).
    assert cur.splitlines()[0].startswith(("# HPAC-PAWA-001 v1.", "# HPAC-PAWA-001 v2."))
    assert "**Status:** FROZEN" in cur
    assert "HPAC-PAWA-001 v1.0 → v1.1 → v1.2 → v1.3" in cur


def test_05_lineage_records_all_four_versions() -> None:
    assert "HPAC-PAWA-001 v1.0 → v1.1 → v1.2 → v1.3" in text(PAWA)


def test_06_v1_2_history_is_preserved_immutable() -> None:
    t = text(PAWA)
    assert "**v1.1**" in t and "**v1.2**" in t and "**v1.3**" in t
    assert "Historical v1.1 and its\nIV remain immutable." in t


def test_07_h0_contract_was_v1_2() -> None:
    assert at_h0(PAWA).splitlines()[0].decode().startswith("# HPAC-PAWA-001 v1.2 —")


# --- 3. closed-set / new category ------------------------------------------

def test_08_authorized_consumer_set_stays_closed() -> None:
    t = text(PAWA)
    assert "authorized-consumer set stays\n  **closed**" in t or "stays\n  **closed** — extended only by this explicit enumeration." in t


def test_09_new_certification_category_frozen() -> None:
    t = text(PAWA)
    assert "## 38A. Authorized certification consumer (v1.3)" in t
    assert "N-16-5 real-human-authentication certification coordinator" in t
    assert "pcae.core.hpac_certification_coordinator" in t
    assert "scripts/hpac_certification_admin.py" in t


def test_10_recognition_sequence_frozen_and_reuses_33() -> None:
    t = text(PAWA)
    assert "## 33A. Certification-coordinator recognition sequence (v1.3)" in t
    assert "§33 steps 1–9 **verbatim**" in t
    assert "fails closed" in t


def test_11_five_role_allowlist_exact() -> None:
    t = text(PAWA)
    for r in FIVE_ROLES:
        assert r in t
    assert "closed five-role allowlist" in t


def test_12_no_wildcard_prefix_glob_in_role_or_consumer() -> None:
    f = flat(PAWA)
    assert "No wildcard, no prefix match, no `fnmatch`, no arbitrary role argument" in f
    assert "Neither name is a prefix, glob, or category wildcard." in f


def test_13_unknown_and_terminator_role_denied() -> None:
    t = text(PAWA)
    assert "hpac_lifecycle_terminator" in t
    assert "explicitly NOT" in t or "explicitly **NOT**" in t
    assert "`operation_scope_invalid`" in t


# --- 4. ordinary categories remain unauthorized ---------------------------

@pytest.mark.parametrize(
    "term",
    [
        "launcher", "helper", "presentation store", "verifier", "Gate",
        "runtime", "agent", "CLI", "plugin", "test fixture",
    ],
)
def test_14_ordinary_categories_unauthorized(term: str) -> None:
    t = text(PAWA)
    # each appears in the §38A / §240 unauthorized enumeration
    assert term in t
    assert "SHALL NOT be authorized certification-writer consumers" in t


def test_15_088_and_224_preserved() -> None:
    f = flat(PAWA)
    assert "HPAC-PAWA-REQ-088" in f and "HPAC-PAWA-REQ-224" in f
    assert "Restating §38 / §88 / §224 for the certification factory" in f


# --- 5. capability semantics ---------------------------------------------

def test_16_non_bearer_single_use_process_local_restart_dead() -> None:
    t = text(PAWA)
    assert "## 49A. Certification-lifecycle one-ceremony lifetime (v1.3)" in t
    assert "process-local" in t and "non-bearer" in t and "restart-dead" in t
    assert "single-use per role" in t


def test_17_no_remint_no_delegation_no_escalation() -> None:
    t = text(PAWA)
    assert "does\n  **not** permit the coordinator (or anything it calls) to remint, delegate" in t \
        or "no delegation / remint" in t


def test_18_no_generic_writer_authority_introduced() -> None:
    f = flat(PAWA)
    assert "no new public generic mint function" in f
    assert "GENERIC PRODUCTION WRITER AUTHORITY = NOT INTRODUCED" in f


def test_19_factory_not_consumer_preserved() -> None:
    t = text(PAWA)
    assert "FACTORY ≠ CONSUMER" in t


# --- 6. per-role boundaries --------------------------------------------

def test_20_challenge_role_bounded() -> None:
    t = text(PAWA)
    assert "open the trusted authentication-challenge lifecycle" in t
    assert "sealing arbitrary trusted bytes" in t


def test_21_assertion_recorder_bounded() -> None:
    t = text(PAWA)
    assert "record one validated assertion lifecycle object" in t
    assert "skipping signature / challenge / credential-currentness / UP / UV / counter validation" in t


def test_22_proof_verifier_bounded() -> None:
    t = text(PAWA)
    assert "directly minting a PRODUCTION `AuthenticatedHumanPrincipal` outside `verify_human_authentication(require_real_assurance=True)`" in t


def test_23_gate5_binder_bounded() -> None:
    t = text(PAWA)
    assert "manufacturing a principal; manufacturing a Gate result" in t


def test_24_counter_verifier_bounded() -> None:
    t = text(PAWA)
    assert "resetting counters; arbitrarily setting values" in t
    assert 'trusting a caller-provided "counter accepted"' in t


def test_25_presentation_evidence_outside_family() -> None:
    t = text(PAWA)
    assert "`HPAC-PRESENTATION-EVIDENCE/2.0` is **outside** this\n  family" in t
    assert "mint_protected_presentation_evidence_writer" in t


# --- 7. walls ---------------------------------------------------------

def test_26_human_approval_cannot_be_manufactured() -> None:
    t = text(PAWA)
    assert "SHALL NOT\n  manufacture: a human APPROVE or REJECT" in t


def test_27_deterministic_not_real() -> None:
    t = text(PAWA)
    assert "**Real ≠ deterministic.**" in t
    assert "require_real_assurance=True" in t


def test_28_pb_policy_wall() -> None:
    t = text(PAWA)
    assert "a Permission Broker permission, a policy\n  exception, a Runtime Enforcement result" in t


def test_29_runtime_effect_wall_and_gate5_termination() -> None:
    t = text(PAWA)
    assert "terminates no later than the\n  bounded Gate-5 certification result" in t
    assert "authorizes no first governed runtime effect" in t or "authorizes no first external effect" in t


def test_30_pawa_inv_13_present_once() -> None:
    t = text(PAWA)
    assert t.count("**PAWA-INV-13.**") == 1
    # v1.3 introduced PAWA-INV-13; a later MINOR may append further invariants
    # (never renumber). The range clause still opens at PAWA-INV-1 and covers
    # at least through 13.
    assert re.search(r"`PAWA-INV-1` through `PAWA-INV-1[3-9]`", t)


# --- 8. taxonomy / cross-contract ------------------------------------

def test_31_no_new_pawa_failure_code() -> None:
    t = text(PAWA)
    assert "## 42C. v1.3 rejection cases — all map onto the existing 21 codes" in t
    assert "the taxonomy remains 21 closed values" in t


def test_32_no_new_terminal_reason_code_no_rhamp_edit() -> None:
    f = flat(PAWA)
    assert "No new `terminal_reason_code`; RHAMP-001 v1.0 §49's 41-code vocabulary is byte-unchanged; RHAMP-001 is not edited." in f


def test_33_no_new_pawa_operation() -> None:
    t = text(PAWA)
    assert "It is **not** a new `PawaOperation`" in t


def test_34_schemas_byte_unchanged_clause() -> None:
    t = text(PAWA)
    assert "`HPAC-PAWA-CURRENT-GENERATION/1.0` and\n  `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schemas are byte-unchanged by v1.3" in t


def test_35_related_frozen_contracts_byte_unchanged_at_h0() -> None:
    for path in (RHAMP, HPAC, HBDC):
        assert at_h0(path) == path.read_bytes()
    # Point-in-time guard reconciled by phase N16-5-F-5-PPA-CONTRACT
    # (HPAC-PPA-001 v1.0 -> v2.0, MAJOR -- out-of-process presentation-evidence
    # writer ownership). Not-weakened check on HPAC-PPA-001: every v1.0
    # requirement id present at H0 is still present, numbering only grew, and
    # the header moved v1.0 -> v2.0 (append-only evolution).
    old = at_h0(PPA).decode()
    new = PPA.read_text()
    old_reqs = set(re.findall(r"\*\*HPAC-PPA-REQ-\d{3}\.\*\*", old))
    new_reqs = set(re.findall(r"\*\*HPAC-PPA-REQ-\d{3}\.\*\*", new))
    assert old_reqs and old_reqs <= new_reqs and len(new_reqs) >= len(old_reqs)
    assert new.splitlines()[0].startswith("# HPAC-PPA-001 v2.0")


# --- 9. MINOR classification --------------------------------------

def test_36_minor_rule_s2_and_major_review() -> None:
    t = text(PAWA)
    assert "### 80.3 v1.3 versioning rule (finding S-2)" in t
    assert "⇒ HPAC-PAWA-001 v1.3 — MINOR." in t
    assert "MAJOR-trigger review — none fires" in t


def test_37_96_specialized_not_redefined() -> None:
    t = text(PAWA)
    assert "This rule is **specialized, not redefined**, by the §42B" in t


# --- 10. no implementation / no ceremony / instance neutrality --------

# N16-5-H3-IMPL: the HPAC-PAWA-001 v1.3 FREEZE phase (this suite's phase)
# completed at `_FREEZE_END` and made no source / scripts change — a
# contract-only MINOR. Its `.1R` grandchild N16-5-H3-IMPL is the sanctioned
# §33A/§38A/§42B implementation phase. Re-anchor this guard's endpoint from
# the moving `HEAD` to the fixed freeze-completion SHA so it keeps asserting
# exactly what it was written to assert — that THE FREEZE touched no source.
_FREEZE_END = "4977a2e5db362e9e86f898cf438578f00e8051f5"


def test_38_no_src_or_scripts_change_since_h0() -> None:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", H0, _FREEZE_END, "--", "src/pcae", "scripts", "pyproject.toml"],
        cwd=ROOT,
    ).decode().strip()
    assert out == "", out


def test_39_only_this_contract_changed_in_docs_contracts() -> None:
    # committed + working-tree, so this holds mid-phase and at finalization
    out = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", H0, "--", "docs/contracts"], cwd=ROOT
        ).decode().split()
    )
    # Reconciled by phase N16-5-F-5-TB-CONTRACT (HPAC-PAWA-001 v1.4 -> v2.0, MAJOR S-4; new companion HPAC-PAWA-HELPER-001 v1.0): the later MAJOR adds one new companion contract file.
    # Reconciled again by phase N16-5-F-5-PPA-CONTRACT (HPAC-PPA-001 v1.0 -> v2.0, MAJOR): the later governed successor evolves the HPAC-PPA-001 document in place (out-of-process presentation-evidence writer ownership).
    assert out <= {
        "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
        "docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md",
        "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md",
    }, out


def test_40_no_instance_ids_frozen_normatively() -> None:
    t = text(PAWA)
    assert "SHALL NOT\n  normatively freeze any current deployment-specific value" in t
    # the specific ids appear only as prohibited examples, never as a const
    assert "const `hp-8cee9b36" not in t


def test_41_requirement_ids_sequential_1_to_275() -> None:
    # v1.3 defined exactly 275; a later governed MINOR appends further
    # requirements (never renumbering, never reusing). The invariant is:
    # contiguous from 1, no gaps, no duplicates, and 1..275 all present.
    ids = sorted(int(m) for m in re.findall(r"\*\*HPAC-PAWA-REQ-(\d+)\.\*\*", text(PAWA)))
    assert ids == list(range(1, len(ids) + 1))
    assert len(ids) == len(set(ids))
    assert set(range(1, 276)).issubset(ids)
    v13_ids = sorted(int(m) for m in re.findall(r"\*\*HPAC-PAWA-REQ-(\d+)\.\*\*", at_sha(_V13_FREEZE_END, PAWA).decode("utf-8")))
    assert v13_ids == list(range(1, 276))


def test_42_n16_5_not_closed_and_n16_6_7_untouched() -> None:
    t = text(PAWA)
    assert "N-16-5 remains NOT CLOSED" in t or "N-16-5: NOT CLOSED" in t
    assert "N-16-6 / N-16-7: OPEN, untouched, N-16-7 last." in t


def test_43_dedicated_v1_3_contract_iv_recommended() -> None:
    f = flat(PAWA).lower()
    assert "dedicated independent verification of hpac-pawa-001 v1.3" in f
    assert "n16-5-h3-pawa13-iv" in f


def test_44_mechanism_neutrality_preserved() -> None:
    t = text(PAWA)
    assert "SHALL NOT hardcode\n  YubiKey, USB, a specific AAGUID" in t
    assert "Future mobile / passkey authentication profiles" in t


def test_45_runtime_unchanged_clause() -> None:
    t = text(PAWA)
    assert "Runtime remains\n`not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins /\n0 capabilities." in t
