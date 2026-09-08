"""Contract-level verification for phase N16-5-F5B1-READAUTH
(149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R)
— F-5-B1 Production Recognized Read / Ceremony Authority Contract Reconciliation
and Freeze (HPAC-PAWA-001 v1.3 -> v1.4, MINOR, S-3).

Intentionally static / read-only. This phase freezes authority semantics and
implements NO production read / ceremony-entry authority: no
`recognized_certification_read_authority` accessor, no `CertificationReadAuthority`
handle, no §33B recognition code, no protected-store read, no ceremony. The
functional guards implied below are specifications for the F-5-B1 implementation
phase and the dedicated v1.4 contract IV, not tests authored now.

N-16-5 is NOT CLOSED by this phase.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Phase-entry SHA (C0) — the finalized predecessor N16-5-FINAL-CERT head, the
#: last commit at which HPAC-PAWA-001 was still v1.3.
C0 = "18d7da02435cac61159e9a90f86b2a586c4704d0"
#: The v1.3 git blob — byte-identical from N16-5-H3-IMPL through C0.
PAWA_V13_BLOB = "9c816716bae2262831945ac24b1771cf79de4c55"

PAWA = ROOT / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
PPA = ROOT / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
RHAMP = ROOT / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
HBDC = ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
SCHEMAS = ROOT / "src/pcae/core/hpac_pawa_schemas.py"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N16_5_F5B1_READAUTH.md"

FOUNDATION = ROOT / "src/pcae/core/hpac_foundation.py"
ADMIN_WRITER = ROOT / "src/pcae/core/hpac_protected_admin_writer.py"
PRESENTATION = ROOT / "src/pcae/core/protected_presentation.py"

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


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def at_c0(path: Path) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{C0}:{path.relative_to(ROOT).as_posix()}"], cwd=ROOT
    )


# --- 1. phase lineage / CPIPC --------------------------------------------------


def test_01_phase_entry_sha_resolves() -> None:
    assert _git("rev-parse", C0).strip() == C0
    # HPAC-PAWA-001 was v1.3 at C0.
    assert at_c0(PAWA).splitlines()[0].decode().startswith("# HPAC-PAWA-001 v1.3 —")
    assert _git("rev-parse", f"{C0}:docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md").strip() == PAWA_V13_BLOB


def test_02_cpipc_candidate_is_direct_valid_successor() -> None:
    from pcae.core import phase_id as p

    pred = (
        "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R."
        "1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R"
    )
    cand = pred + ".1R"
    a, b = p.parse(pred), p.parse(cand)
    assert p.is_valid(pred) and p.is_valid(cand)
    assert p.same_series(a, b) and p.same_branch(a, b)
    assert p.compare(a, b) == "less"
    assert b.subphase[: len(a.subphase)] == a.subphase
    assert len(b.subphase) == len(a.subphase) + 1
    assert b.subphase[-1] == (1, "R")


def test_03_predecessor_final_cert_blocked_report_present() -> None:
    pred = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N16_5_FINAL_CERT.md"
    t = text(pred)
    assert "F-5-B1" in t and "BLOCKED" in t
    assert "N-16-5" in t and "NOT CLOSED" in t


def test_04_this_phase_report_present_with_required_verdicts() -> None:
    t = text(REPORT)
    for needle in (
        "F-5-B1 ROOT CAUSE", "VERIFIED",
        "F-5-B1 CONTRACT BLOCKER", "RESOLVED",
        "F-5-B1 IMPLEMENTATION", "PENDING",
        "N-16-5", "NOT CLOSED",
        "MINOR (S-3)",
        "NOT INTRODUCED",
        "ABSENT / UNREACHABLE",
    ):
        assert needle in t, needle


# --- 2. version / lineage ---------------------------------------------------


def test_10_contract_version_is_v1_4_frozen() -> None:
    t = text(PAWA)
    assert t.splitlines()[0].startswith("# HPAC-PAWA-001 v1.4 —")
    assert "**Version:** 1.4" in t
    assert "**Status:** FROZEN" in t


def test_11_lineage_records_all_five_versions() -> None:
    assert "HPAC-PAWA-001 v1.0 → v1.1 → v1.2 → v1.3 → v1.4" in text(PAWA)


def test_12_v1_3_history_preserved_immutable() -> None:
    t = text(PAWA)
    assert "### 90.3 v1.3 contract-freeze verdict" in t
    assert "⇒ HPAC-PAWA-001 v1.3 — MINOR." in t
    assert "Historical v1.0 /\nv1.1 / v1.2 / v1.3 freeze records and their IVs remain **immutable**" in t
    # v1.3 was the frozen state at C0.
    assert at_c0(PAWA).splitlines()[0].decode().startswith("# HPAC-PAWA-001 v1.3 —")


# --- 3. new sections / recognition / consumer -----------------------------


def test_20_new_v1_4_sections_present() -> None:
    t = text(PAWA)
    for sec in (
        "## 7C. v1.3 → v1.4 normative delta table",
        "## 33B. Certification read / ceremony-entry authority recognition sequence (v1.4)",
        "## 38B. Authorized read / ceremony-entry authority consumer (v1.4)",
        "## 42D. Certification read / ceremony-entry authority — grants no write (v1.4)",
        "## 42E. v1.4 rejection cases — all map onto the existing 21 codes",
        "## 49B. Certification read / ceremony-entry authority lifetime (v1.4)",
        "## 68B. Certification read / ceremony-entry authority walls (v1.4)",
        "### 80.4 v1.4 versioning rule (finding S-3)",
        "### 90.4 v1.4 contract-freeze verdict",
        "## 95C. Read / ceremony-entry authority contract-shape disposition (append-only, v1.4)",
        "## 96C. Recommended next phases (as of v1.4)",
    ):
        assert sec in t, sec


def test_21_recognition_reuses_33_steps_1_to_9_verbatim() -> None:
    t = text(PAWA)
    assert "the §33 steps 1–9 **verbatim**" in t
    assert "fails closed" in t.lower() or "**fails closed**" in t
    assert "_bind_configured_agent_identity" in t
    assert "_PRODUCTION_WRITER_FACTORY_SEAL" in t


def test_22_consumer_is_the_already_enumerated_38a_coordinator_no_new_category() -> None:
    f = flat(PAWA)
    assert "HPAC-PAWA-001 v1.4 adds **no** new factory-consumer category" in f
    assert "pcae.core.hpac_certification_coordinator" in f
    assert "scripts/hpac_certification_admin.py" in f
    assert "Neither name is a prefix, glob, or category wildcard." in f


@pytest.mark.parametrize(
    "term",
    ["launcher", "helper", "presentation store", "verifier", "Gate", "runtime",
     "agent", "CLI", "plugin", "harness"],
)
def test_23_ordinary_categories_unauthorized(term: str) -> None:
    t = text(PAWA)
    assert term in t
    assert "SHALL NOT be authorized certification-writer consumers" in t or \
        "is an\n  authorized read-authority consumer" in t


# --- 4. grants-no-write / read-vs-write separation -----------------------


def test_30_read_authority_grants_no_writer_capability_or_mint() -> None:
    f = flat(PAWA)
    assert "grants **no** `HPACWriterCapability`" in f
    assert "**no** mint authority" in f
    assert "**no** new `PawaOperation`" in f
    assert "**no** new writer role" in f
    assert "**no** mutation" in f


def test_31_writer_still_raises_on_the_recognized_authority() -> None:
    f = flat(PAWA)
    assert "`HPACStoreAuthority.writer()` on the wrapped recognized\n  authority SHALL continue to `raise`".replace("\n ", "") in f.replace("  ", " ") \
        or "HPACStoreAuthority.writer() still raises" in f.replace("`", "")


def test_32_counter_update_not_authorized_by_this_authority() -> None:
    f = flat(PAWA)
    assert "SHALL NOT apply a\n  counter-state transition".replace("\n ", "") in f.replace("  ", " ")
    assert "`hpac_rhamp_counter_state_verifier` role remains the **sole**" in f


def test_33_presentation_evidence_writer_unchanged_outside_this_authority() -> None:
    f = flat(PAWA)
    assert "`mint_protected_presentation_evidence_writer` path (HPAC-PAWA-REQ-248 /\n  HPAC-PPA-REQ-041) **unchanged**".replace("\n ", "") in f.replace("  ", " ")


def test_34_read_scope_is_a_closed_enumeration() -> None:
    f = flat(PAWA)
    assert "an **explicitly enumerated closed** set" in f
    assert "**No** arbitrary filesystem read" in f
    assert "an open-ended HPAC store\n  enumeration".replace("\n ", "") in f.replace("  ", " ")


# --- 5. taxonomy / no new op / no new code -----------------------------


def test_40_no_new_pawa_failure_code() -> None:
    t = text(PAWA)
    assert "## 42E. v1.4 rejection cases — all map onto the existing 21 codes" in t
    assert "the taxonomy remains 21 closed values" in t


def test_41_no_new_terminal_reason_code_no_rhamp_edit() -> None:
    f = flat(PAWA)
    assert "No new `terminal_reason_code`; RHAMP-001 v1.0 §49's 41-code vocabulary is\n  byte-unchanged; RHAMP-001 is not edited.".replace("\n ", "") in f.replace("  ", " ")


def test_42_no_new_pawa_operation() -> None:
    f = flat(PAWA)
    assert "is **not** a new\n  `PawaOperation`".replace("\n ", "") in f
    assert "The `PawaOperation`\n  vocabulary stays at its 6 closed mutation members.".replace("\n ", "") in f
    # primary source: still exactly 6
    import pcae.core.hpac_protected_admin_writer as w

    assert [m.value for m in w.PawaOperation] == [
        "enroll_principal", "revoke_principal", "enroll_credential",
        "revoke_credential", "initialize_credential_sidecar_state",
        "configure_presentation_mechanism",
    ]
    assert len(w.PAWA_FAILURE_CODES) == 21 == len(set(w.PAWA_FAILURE_CODES))


# --- 6. walls ---------------------------------------------------------


def test_50_second_trust_root_not_introduced() -> None:
    f = flat(PAWA)
    assert "**No second trust root.**" in f
    assert "reuses the **existing** production recognition / trust root" in f
    assert "**no** new global seal, secret, trust token, magic environment\n  variable".replace("\n ", "") in f.replace("  ", " ")


def test_51_human_approval_and_real_assurance_walls() -> None:
    f = flat(PAWA)
    assert "cannot produce a human APPROVE" not in f  # phrased positively:
    assert "SHALL NOT: manufacture a human\n  APPROVE or REJECT".replace("\n ", "") in f.replace("  ", " ")
    assert "`verify_human_authentication(require_real_assurance=True)`" in f
    assert "convert deterministic authentication / presentation evidence into REAL\n  assurance".replace("\n ", "") in f.replace("  ", " ")


def test_52_pb_policy_runtime_effect_walls_and_termination() -> None:
    f = flat(PAWA)
    assert "a Permission Broker permission, a policy exception, a Runtime Enforcement result" in f
    assert "terminates at the trusted reads plus one ceremony entry" in f
    assert "authorizes\n  **no first governed runtime external effect**".replace("\n ", "") in f.replace("  ", " ")


def test_53_h3_design_unchanged() -> None:
    f = flat(PAWA)
    assert "**H-3 and its neighbours are unchanged.**" in f
    assert "§33A / §38A / §42B / §68A" in f
    # h3 sections still present verbatim
    t = text(PAWA)
    for sec in (
        "## 33A. Certification-coordinator recognition sequence (v1.3)",
        "## 38A. Authorized certification consumer (v1.3)",
        "## 42B. Certification-lifecycle writer family (v1.3)",
        "## 68A. Certification authority walls (v1.3)",
    ):
        assert sec in t, sec
    for r in FIVE_ROLES:
        assert r in t


def test_54_pawa_inv_14_present_once() -> None:
    t = text(PAWA)
    assert t.count("- **PAWA-INV-14.**") == 1
    assert re.search(r"`PAWA-INV-1` through `PAWA-INV-14`", t)


# --- 7. MINOR classification --------------------------------------


def test_60_minor_rule_s3_and_major_review() -> None:
    t = text(PAWA)
    assert "**Explicit MINOR rule (S-3):**" in t
    assert "⇒ HPAC-PAWA-001 v1.4 — MINOR." in t
    assert "**v1.4 MAJOR-trigger review — none fires" in t


def test_61_96_further_specialized_not_redefined() -> None:
    f = flat(PAWA)
    assert "§96 is thereby **further\n  specialized**, not redefined".replace("\n ", "") in f.replace("  ", " ")


def test_62_single_contract_solution() -> None:
    f = flat(PAWA)
    assert "**Single-contract solution.**" in f
    assert "a bounded amendment to **HPAC-PAWA-001 alone** is normatively\n  sufficient".replace("\n ", "") in f.replace("  ", " ")


# --- 8. no implementation / no ceremony / neutrality --------


def test_70_no_src_or_scripts_change_since_c0() -> None:
    out = _git("diff", "--name-only", C0, "HEAD", "--", "src/pcae", "scripts", "pyproject.toml").split()
    assert out == [], out


def test_71_only_this_contract_changed_in_docs_contracts_since_c0() -> None:
    out = set(_git("diff", "--name-only", C0, "HEAD", "--", "docs/contracts").split())
    assert out == {"docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"}, out


def test_72_schemas_byte_unchanged_since_c0() -> None:
    assert at_c0(SCHEMAS) == SCHEMAS.read_bytes()
    for c in (PPA, RHAMP, HPAC, HBDC):
        assert at_c0(c) == c.read_bytes()


def test_73_no_instance_ids_frozen_normatively() -> None:
    t = text(PAWA)
    assert "**No instance data in the contract.**" in t
    assert "const `hp-8cee9b36" not in t
    assert "const `hpc-2e7bbfa0" not in t


def test_74_requirement_ids_sequential_1_to_309() -> None:
    ids = sorted(int(m) for m in re.findall(r"\*\*HPAC-PAWA-REQ-(\d+)\.\*\*", text(PAWA)))
    assert ids == list(range(1, 310))
    assert len(ids) == len(set(ids)) == 309


def test_75_v1_4_additions_are_req_276_to_309() -> None:
    v13 = at_c0(PAWA).decode("utf-8")
    v13_ids = {int(m) for m in re.findall(r"\*\*HPAC-PAWA-REQ-(\d+)\.\*\*", v13)}
    cur_ids = {int(m) for m in re.findall(r"\*\*HPAC-PAWA-REQ-(\d+)\.\*\*", text(PAWA))}
    assert max(v13_ids) == 275
    assert sorted(cur_ids - v13_ids) == list(range(276, 310))


def test_76_mechanism_neutrality_preserved() -> None:
    f = flat(PAWA)
    assert "Mechanism-neutral" in text(PAWA) or "mechanism-neutral" in f
    assert "mobile / passkey" in f.lower() or "MOBILE / PASSKEY FUTURE OPEN" in text(PAWA)


def test_77_n16_5_not_closed_n16_6_7_untouched() -> None:
    f = flat(PAWA)
    assert "**N-16-5 remains NOT CLOSED**" in f or "N-16-5: NOT CLOSED" in f
    assert "N-16-6 / N-16-7: OPEN, untouched, N-16-7 last." in f


def test_78_dedicated_v1_4_contract_iv_recommended() -> None:
    f = flat(PAWA).lower()
    assert "dedicated independent verification of hpac-pawa-001\n  v1.4".replace("\n ", "") in f.replace("  ", " ")
    assert "n16-5-f5b1-readauth-iv" in f


# --- 9. F-5-B1 root cause is real (primary source) ---------------------


def test_90_boundary_keys_off_geteuid_without_the_bind() -> None:
    t = text(FOUNDATION)
    # _validate_production_boundary falls back to _current_agent_identity()
    # (= os.geteuid()) when _configured_agent_identity is None.
    assert "_current_agent_identity" in t
    assert "if self._configured_agent_identity is not None:" in t
    # _bind_configured_agent_identity is seal-guarded.
    assert "_bind_configured_agent_identity" in t
    assert "_PRODUCTION_WRITER_FACTORY_SEAL" in t


def test_91_current_agent_identity_is_geteuid() -> None:
    t = text(ROOT / "src/pcae/core/hatp_class_b_topology_verifier.py")
    assert "return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}" in t


def test_92_every_seal_holder_is_a_write_path() -> None:
    t = text(ADMIN_WRITER)
    # the three functions that bind the configured-agent identity
    for sym in ("def production_writer(", "def certification_writer(",
                "def mint_protected_presentation_evidence_writer("):
        assert sym in t
    # no read-only accessor exists yet
    assert "recognized_certification_read_authority" not in t
    assert "CertificationReadAuthority" not in t


def test_93_ceremony_takes_an_hpac_store_authority_no_read_only_getter() -> None:
    t = text(PRESENTATION)
    assert "def run_protected_presentation_ceremony(" in t
    assert "authority: HPACStoreAuthority" in t
    # this phase adds no accessor / getter in production source
    assert "recognized_certification_read_authority" not in t
