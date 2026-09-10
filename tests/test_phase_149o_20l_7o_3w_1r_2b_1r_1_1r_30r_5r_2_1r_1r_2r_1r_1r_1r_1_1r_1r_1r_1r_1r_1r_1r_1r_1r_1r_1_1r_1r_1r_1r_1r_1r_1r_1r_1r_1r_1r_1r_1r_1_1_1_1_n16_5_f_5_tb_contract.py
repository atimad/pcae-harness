"""Contract-level verification for phase N16-5-F-5-TB-CONTRACT
(149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1)
— N-16-5 Privileged Production Authority Trust-Boundary Contract Evolution
(HPAC-PAWA-001 v1.4 -> v2.0 FROZEN, MAJOR S-4; new companion
HPAC-PAWA-HELPER-001 v1.0 FROZEN).

Intentionally static / read-only. This phase freezes authority semantics and
implements NO helper executable, launcher, IPC channel, `configure_privileged_helper`
transaction, or caller migration, and does NOT remove the in-process
`_PINNED_*` / `_verified_production_caller_name` mechanism (a later governed
implementation slice). The functional guards implied below are specifications
for the helper + protocol implementation phase and the dedicated
N16-5-F-5-TB-CONTRACT-IV, not tests authored now.

N-16-5 is NOT CLOSED by this phase.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Phase-entry SHA — the finalized predecessor N16-5-F-5-TB-ARCH head, the last
#: commit at which HPAC-PAWA-001 was v1.4 and the new companion did not exist.
ENTRY = "05056eeb1d38d92d7eda749a4334f7626c5e6a8f"

PAWA = ROOT / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
HELPER = ROOT / "docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
PPA = ROOT / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
RHAMP = ROOT / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
HBDC = ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
SCHEMAS = ROOT / "src/pcae/core/hpac_pawa_schemas.py"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N16_5_F_5_TB_CONTRACT.md"
DECISIONS = ROOT / "tasks/DECISIONS.md"

FIVE_ROLES = (
    "hpac_challenge_coordinator",
    "hpac_assertion_recorder",
    "human_authentication_proof_verifier",
    "hpac_gate5_binder",
    "hpac_rhamp_counter_state_verifier",
)

OPERATION_VOCAB = (
    "admin_mutation",
    "certification_write",
    "certification_read",
    "ceremony_entry",
    "presentation_evidence_write",
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(path: Path) -> str:
    return re.sub(r"\s+", " ", text(path))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def at_entry(path: Path) -> bytes:
    rel = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "show", f"{ENTRY}:{rel}"], cwd=ROOT)


# --------------------------------------------------------------------------
# HPAC-PAWA-001 v2.0 — identity, versioning, numbering
# --------------------------------------------------------------------------

def test_01_pawa_header_is_v2_0_frozen() -> None:
    t = text(PAWA)
    assert t.splitlines()[0].startswith("# HPAC-PAWA-001 v2.0 —")
    assert "**Version:** 2.0" in t
    assert "**Status:** FROZEN" in t


def test_02_pawa_lineage_prefix_preserved_verbatim() -> None:
    # every prior MINOR lineage string is kept; v2.0 is appended, never a rewrite
    assert "HPAC-PAWA-001 v1.0 → v1.1 → v1.2 → v1.3" in text(PAWA)
    assert "→ v2.0" in text(PAWA)


def test_03_pawa_requirement_ids_contiguous_1_to_340() -> None:
    ids = sorted(int(m) for m in re.findall(r"\*\*HPAC-PAWA-REQ-(\d{3})\.\*\*", text(PAWA)))
    assert ids == list(range(1, 341))
    assert len(ids) == len(set(ids)) == 340


def test_04_pawa_v2_0_additions_are_req_310_to_340() -> None:
    v14 = at_entry(PAWA).decode("utf-8")
    v14_ids = {int(m) for m in re.findall(r"\*\*HPAC-PAWA-REQ-(\d{3})\.\*\*", v14)}
    cur_ids = {int(m) for m in re.findall(r"\*\*HPAC-PAWA-REQ-(\d{3})\.\*\*", text(PAWA))}
    assert max(v14_ids) == 309
    assert sorted(cur_ids - v14_ids) == list(range(310, 341))


def test_05_pawa_invariants_1_to_17_defined_once_each() -> None:
    t = text(PAWA)
    for n in range(1, 18):
        assert t.count(f"- **PAWA-INV-{n}.**") == 1, n
    assert "`PAWA-INV-1` through `PAWA-INV-17`" in t


def test_06_every_v14_requirement_body_survives_verbatim() -> None:
    """A MAJOR may append '(v2.0)' notes and new sections; it never rewords,
    shortens, reorders, or interrupts an existing v1.0-v1.4 requirement body."""
    def bodies(s: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for m in re.finditer(
            r"- \*\*HPAC-PAWA-REQ-(\d{3})\.\*\*(.+?)(?=\n- \*\*HPAC-PAWA-REQ-|\n#)", s, re.S
        ):
            out[m.group(1)] = re.sub(r"\s+", " ", m.group(2)).strip()
        return out

    b14 = bodies(at_entry(PAWA).decode("utf-8"))
    bc = bodies(text(PAWA))
    assert set(b14).issubset(bc)
    for rid, body in b14.items():
        assert body in bc[rid], rid


def test_07_historical_freeze_verdicts_intact() -> None:
    t = text(PAWA)
    for s in (
        "⇒ HPAC-PAWA-001 v1.1 — MINOR.",
        "⇒ HPAC-PAWA-001 v1.3 — MINOR.",
        "⇒ HPAC-PAWA-001 v1.4 — MINOR.",
        "### 90.3 v1.3 contract-freeze verdict",
        "### 80.4 v1.4 versioning rule (finding S-3)",
        "### 90.4 v1.4 contract-freeze verdict",
    ):
        assert s in t, s


# --------------------------------------------------------------------------
# HPAC-PAWA-001 v2.0 — the out-of-process delivery model
# --------------------------------------------------------------------------

def test_10_predicate_6_and_step_9_marked_superseded_by_33c() -> None:
    t = text(PAWA)
    assert "SUPERSEDED by §33C" in t
    assert "## 33C. Out-of-process privileged-helper recognition" in t


def test_11_trusted_consumer_conjunction_is_frozen_and_closed() -> None:
    t = text(PAWA)
    assert "TrustedProtectedAuthorityConsumer(request) =" in t
    for conjunct in (
        "RegisteredGenerationMatch",
        "ProtectedHelperFilesystemPropertiesValid",
        "HelperIntegrityBindingValid",
        "VerifiedExecutionObjectValid",
        "ProtectedProcessPrincipalValid",
        "PrivateChannelValid",
        "PeerCredentialValid",
        "PAWAOSRecognitionValid",
        "ConfiguredAgentIdentityBindingValid",
        "RequestSchemaValid",
        "ClosedOperationMembershipValid",
        "OperationSpecificAuthorityPredicatesValid",
        "FreshnessAndReplayPredicatesValid",
    ):
        assert conjunct in t, conjunct
    assert "No single conjunct" in t or "no single conjunct" in t.lower()


def test_12_no_authority_object_export_invariant_present() -> None:
    t = text(PAWA)
    assert "- **PAWA-INV-15.**" in t
    assert "no returnable authority object" in t.lower() or "returns typed evidence only" in t.lower() \
        or "typed evidence only" in t
    assert "HPACWriterCapability" in t and "HPACStoreAuthority" in t
    # the in-process mechanism is named as NO LONGER the recognition predicate
    assert "_verified_production_caller_name" in t
    assert "_PINNED_" in t


def test_13_single_trust_root_no_second_root() -> None:
    t = text(PAWA)
    assert "- **PAWA-INV-17.**" in t
    assert "No second trust root" in t
    assert "HPAC-PAWA-REQ-010" in t
    assert "integrity-pinned artifact of the existing kind" in t


def test_14_new_mutation_is_configure_privileged_helper_only() -> None:
    t = text(PAWA)
    assert "## 42G. `configure_privileged_helper`" in t
    assert "privileged_helper_installer" in t
    assert "PawaOperation" in t and ("count becomes **7**" in t or "count to **7**" in t)
    # no other new PawaOperation / certification role
    assert "no new `pawa_failure_code`" in t.lower() or "21 closed values" in t


def test_15_closed_operation_vocabulary_named() -> None:
    t = text(PAWA)
    for op in OPERATION_VOCAB:
        assert op in t, op
    assert "## 42F. Out-of-process typed-operation delivery" in t


def test_16_five_role_closure_preserved_verbatim() -> None:
    t = text(PAWA)
    for role in FIVE_ROLES:
        assert role in t, role
    assert "hpac_lifecycle_terminator" in t
    assert "PAWA-INV-13" in t
    # PAWA-INV-13/14 annotated 'delivery superseded - substance unchanged'
    assert "delivery superseded" in t


def test_17_major_adjudication_recorded() -> None:
    t = text(PAWA)
    assert "## 80.5. v2.0 versioning rule (finding S-4)" in t
    assert "**MAJOR**" in t
    assert "HPAC-PAWA-REQ-331" in t
    assert "outside every HPAC-PAWA-REQ-153 MINOR permit" in t or \
        "outside every" in t and "MINOR permit" in t
    assert "no §152 verbatim trigger" in t.lower() or "no §152 trigger fires verbatim" in t.lower()


def test_18_companion_contract_decision_recorded() -> None:
    t = text(PAWA)
    assert "HPAC-PAWA-REQ-334" in t
    assert "distinct new companion contract" in norm(PAWA)
    assert "HPAC-PAWA-HELPER-001 v1.0" in t
    assert "not** an extension of HPAC-PPA-001" in norm(PAWA) or "not an extension of HPAC-PPA-001" in norm(PAWA)


def test_19_dedicated_iv_required_not_foldable() -> None:
    t = text(PAWA)
    assert "N16-5-F-5-TB-CONTRACT-IV" in t
    assert "HPAC-PAWA-REQ-330" in t
    assert "REQUIRED" in t and "folding" in t.lower()


def test_20_walls_and_runtime_posture_preserved() -> None:
    t = text(PAWA)
    assert "## 68C. v2.0 walls — all preserved verbatim" in t
    assert "Observed" in t and "observe" in t and "unavailable" in t
    assert "first governed runtime external effect stays ABSENT / UNREACHABLE" in t or \
        "first external effect remains **ABSENT**" in t


# --------------------------------------------------------------------------
# HPAC-PAWA-HELPER-001 v1.0 — the new companion
# --------------------------------------------------------------------------

def test_30_helper_header_is_v1_0_frozen() -> None:
    t = text(HELPER)
    assert t.splitlines()[0].startswith("# HPAC-PAWA-HELPER-001 v1.0 —")
    assert "**Version:** 1.0" in t
    assert "**Status:** FROZEN" in t
    assert "**Companion of:** HPAC-PAWA-001 **v2.0**" in t


def test_31_helper_requirement_ids_contiguous_1_to_114() -> None:
    ids = sorted(int(m) for m in re.findall(r"\*\*HPAC-PAWA-HELPER-REQ-(\d{3})\.\*\*", text(HELPER)))
    assert ids == list(range(1, 115))
    assert len(ids) == len(set(ids)) == 114
    # no suffixed / non-sequential ids
    assert re.search(r"HPAC-PAWA-HELPER-REQ-\d{3}[A-Za-z]", text(HELPER)) is None


def test_32_helper_invariants_1_to_10_defined_once_each() -> None:
    t = text(HELPER)
    for n in range(1, 11):
        assert t.count(f"- **PAWAH-INV-{n}.**") == 1, n
    assert "`PAWAH-INV-1` through `PAWAH-INV-10`" in t


def test_33_helper_single_trust_root_no_second_root() -> None:
    t = text(HELPER)
    assert "## 3. Trust root — single, unchanged" in t
    assert "- **PAWAH-INV-7.**" in t
    assert "No second trust root" in t
    assert "HPAC-PAWA-REQ-010" in t or "HPAC-PAWA-REQ-300" in t


def test_34_helper_no_authority_object_export() -> None:
    t = text(HELPER)
    assert "## 24. No privileged authority-object export (frozen invariant)" in t
    assert "- **PAWAH-INV-1.**" in t
    for name in ("HPACWriterCapability", "HPACStoreAuthority", "ProductionWriterHandle",
                 "CertificationReadAuthority"):
        assert name in t, name
    assert "typed evidence" in t


def test_35_helper_closed_operation_vocabulary() -> None:
    t = text(HELPER)
    assert "## 13. Closed operation vocabulary" in t
    for op in OPERATION_VOCAB:
        assert op in t, op
    assert "Unknown operation → DENY" in t
    assert "no** generic" in t.lower() or "no generic" in t.lower()


def test_36_helper_five_role_closure_verbatim() -> None:
    t = text(HELPER)
    for role in FIVE_ROLES:
        assert role in t, role
    assert "hpac_lifecycle_terminator" in t
    assert "closed five-role allowlist" in t


def test_37_helper_typed_read_no_generic_broker() -> None:
    t = text(HELPER)
    assert "## 15. Typed enumerated read vocabulary" in t
    assert "SHALL NOT reconstruct unrestricted store authority" in norm(HELPER)
    assert "arbitrary filesystem read" in norm(HELPER)


def test_38_helper_peer_auth_not_human_identity() -> None:
    t = text(HELPER)
    assert "## 10. Peer authentication" in t
    assert "- **PAWAH-INV-8.**" in t
    assert "OS peer credential ≠ human identity" in t


def test_39_helper_same_file_object_anti_toctou() -> None:
    t = text(HELPER)
    assert "same opened file object" in t
    assert "no pathname re-open gap" in norm(HELPER) or "re-open" in norm(HELPER)
    assert "STOPS BLOCKED" in t


def test_40_helper_state_transition_and_audit_ordering() -> None:
    t = text(HELPER)
    assert "REQUEST_RECEIVED" in t and "MUTATION_ATTEMPT_STARTED" in t and "MUTATION_COMMITTED" in t
    assert "INDETERMINATE / RECONCILIATION REQUIRED" in t or "RECONCILIATION REQUIRED" in t
    assert "evidence durably staged before the mutation" in t or \
        "evidence staged before mutation" in t or "evidence-staged-before-mutation" in t
    assert "## 23. No-auto-retry rule" in t


def test_41_helper_replay_semantics() -> None:
    t = text(HELPER)
    for state in ("fresh", "consumed", "duplicate", "expired", "unknown", "conflicting replay"):
        assert state in t, state
    assert "lost response does not make the original request unused" in norm(HELPER).lower()


def test_42_helper_mechanism_neutrality_and_mobile_future() -> None:
    t = text(HELPER)
    assert "## 27. Mechanism neutrality and the mobile future" in t
    assert "SHALL NOT hardcode YubiKey" in t or "hardcode YubiKey" in t
    assert "mobile-only" in t


def test_43_helper_cross_platform_profiles() -> None:
    t = text(HELPER)
    assert "SO_PEERCRED" in t and "getpeereid" in t
    assert "not** assumed byte-for-byte equivalent" in t or "not assumed byte-for-byte equivalent" in t


def test_44_helper_deterministic_vs_real_wall() -> None:
    t = text(HELPER)
    assert "deterministic test mechanism ≠ real human authentication" in t or \
        "`deterministic test mechanism ≠ real human authentication`" in t
    assert "a test helper speaking the protocol ≠ production authority" in t or \
        "test double is a **different file**" in t


def test_45_helper_versioning_rules() -> None:
    t = text(HELPER)
    assert "## 30. Versioning and evolution rules" in t
    assert "v1.0 is the initial freeze" in t
    assert "persistent helper / daemon / service" in t  # a named MAJOR trigger


def test_46_helper_bounds_security_claims() -> None:
    t = text(HELPER)
    assert "does NOT claim protection against" in norm(HELPER)
    assert "compromised OS kernel" in t
    assert "single-account host" in t


def test_47_helper_ppa_cross_contract_deferred_to_iv() -> None:
    t = text(HELPER)
    assert "Cross-contract note (HPAC-PPA-001)" in t
    assert "fresh governed HPAC-PPA-001 evolution phase" in t or \
        "fresh aligned HPAC-PPA-001 successor" in t
    assert "does **not** silently edit HPAC-PPA-001" in t or "not silently edit HPAC-PPA-001" in t


# --------------------------------------------------------------------------
# Scope / boundary — no production change, sibling contracts byte-unchanged
# --------------------------------------------------------------------------

def test_60_no_src_scripts_pyproject_change_since_entry() -> None:
    names = _git("diff", "--name-only", ENTRY, "HEAD", "--",
                 "src/pcae", "scripts", "pyproject.toml").split()
    assert names == [], names


def test_61_only_the_two_contract_files_changed_in_docs_contracts() -> None:
    changed = set(_git("diff", "--name-only", ENTRY, "HEAD", "--", "docs/contracts").split())
    assert changed == {
        "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
        "docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md",
    }, changed


def test_62_sibling_contracts_and_schemas_byte_unchanged() -> None:
    # RHAMP / HPAC / HBDC and the PAWA schema module stay byte-frozen.
    for c in (RHAMP, HPAC, HBDC):
        assert at_entry(c) == c.read_bytes(), c
    assert at_entry(SCHEMAS) == SCHEMAS.read_bytes()
    # Point-in-time guard reconciled by phase N16-5-F-5-PPA-CONTRACT
    # (HPAC-PPA-001 v1.0 -> v2.0, MAJOR -- out-of-process presentation-evidence
    # writer ownership). HPAC-PPA-001 is the sole later docs/contracts delta;
    # the byte-freeze on it becomes a not-weakened check: every v1.0 requirement
    # id present at ENTRY is still present, the numbering only grew, and the
    # header moved v1.0 -> v2.0 (append-only evolution).
    entry_ppa = at_entry(PPA).decode()
    now_ppa = PPA.read_text()
    entry_reqs = set(re.findall(r"\*\*HPAC-PPA-REQ-\d{3}\.\*\*", entry_ppa))
    now_reqs = set(re.findall(r"\*\*HPAC-PPA-REQ-\d{3}\.\*\*", now_ppa))
    assert entry_reqs and entry_reqs <= now_reqs
    assert len(now_reqs) >= len(entry_reqs)
    assert now_ppa.splitlines()[0].startswith("# HPAC-PPA-001 v2.0")
    assert "PPA-INV-2" in now_ppa


def test_63_hpac_ppa_001_still_v1_0() -> None:
    # Point-in-time guard reconciled by phase N16-5-F-5-PPA-CONTRACT: the
    # dedicated governed successor evolved HPAC-PPA-001 v1.0 -> v2.0 (MAJOR,
    # out-of-process presentation-evidence writer ownership). v1.0 was the state
    # frozen by N16-5-F-5-TB-CONTRACT; v2.0 is the current in-place evolution of
    # the same document.
    assert text(PPA).splitlines()[0].startswith(
        ("# HPAC-PPA-001 v1.0", "# HPAC-PPA-001 v2.0")
    )


def test_64_helper_contract_did_not_exist_at_entry() -> None:
    rel = HELPER.relative_to(ROOT).as_posix()
    r = subprocess.run(["git", "show", f"{ENTRY}:{rel}"], cwd=ROOT, capture_output=True)
    assert r.returncode != 0  # new file this phase


def test_65_decisions_records_both_adjudications() -> None:
    d = text(DECISIONS)
    assert "alias N16-5-F-5-TB-CONTRACT" in d
    assert "v1.4 → **v2.0 (MAJOR)**" in d or "v1.4 -> **v2.0" in d or "v1.4 → v2.0" in d
    assert "HPAC-PAWA-HELPER-001 v1.0" in d
    assert "Guard reconciliation" in d


def test_66_no_protected_root_or_helper_installation_artifact() -> None:
    changed = _git("diff", "--name-only", ENTRY, "HEAD").splitlines()
    assert not any(p.startswith((".pcae/protected-root", "protected-root/", "pawa-helper/")) for p in changed)
    assert not any("helper-installation" in p.lower() for p in changed)


def test_67_runtime_posture_unchanged() -> None:
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    for token in ("not_implemented", "Observed", "observe", "unavailable"):
        assert token in out, token


def test_68_n16_6_and_n16_7_untouched_in_this_delta() -> None:
    diff = _git("diff", ENTRY, "HEAD", "--", "docs/contracts")
    # v2.0 contains no runtime-enablement clause and no N-16-6/N-16-7 work
    assert "N-16-6 and N-16-7 remain **OPEN and untouched**" in text(HELPER) or \
        "N-16-6 / N-16-7 OPEN / UNTOUCHED" in text(PAWA)
