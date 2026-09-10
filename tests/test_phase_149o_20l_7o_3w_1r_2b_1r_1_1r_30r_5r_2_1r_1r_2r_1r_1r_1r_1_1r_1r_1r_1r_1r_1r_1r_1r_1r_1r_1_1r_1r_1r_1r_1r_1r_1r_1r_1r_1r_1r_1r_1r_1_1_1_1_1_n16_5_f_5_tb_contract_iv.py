"""Independent contract verification for phase N16-5-F-5-TB-CONTRACT-IV
(149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1)
— dedicated independent verification of HPAC-PAWA-001 v2.0 AND
HPAC-PAWA-HELPER-001 v1.0 together (HPAC-PAWA-REQ-330; a MAJOR always carries
its own IV, §80.5 — folding is NOT permitted).

Intentionally static / read-only. This IV implements NO helper executable,
launcher, IPC channel, `configure_privileged_helper` transaction, or caller
migration; performs NO protected-host mutation and NO ceremony. Each assertion
independently reconstructs a contract meaning from primary text rather than
re-checking predecessor wording verbatim.

VERDICT OF THIS IV: **NOT VERIFIED / BLOCKED.**
The mandatory HPAC-PPA-001 evidence-writer-delivery adjudication (§25 of the
authorizing prompt; HPAC-PAWA-HELPER-001 §17 cross-contract note) resolves to
**option B — HPAC-PPA-001 CONTRACT EVOLUTION REQUIRED**: HPAC-PAWA-HELPER-001's
`presentation_evidence_write` operation is invoked "by the HPAC-PPA-001
presentation helper itself", which materially conflicts with HPAC-PPA-001 v1.0
HPAC-PPA-REQ-041 ("held only by the trusted launcher mediator … never sent to
the helper"), HPAC-PPA-REQ-054 ("evidence producer is only the launcher
mediator"), HPAC-PPA-REQ-052 (a distinct evidence-writer-issuer module), and
PPA-INV-2 (helper response and evidence writer are distinct trust actions with
no authority transfer). Per §45 of the authorizing prompt, option B ⇒ this IV
is COMPLETE — NOT VERIFIED / BLOCKED, and a fresh governed HPAC-PPA-001
contract-evolution phase is the required successor (derived, NOT begun).

Every OTHER load-bearing IV criterion was independently established (see the
canonical Phase Report). N-16-5 is NOT CLOSED by this phase.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Phase-entry SHA — the finalized predecessor N16-5-F-5-TB-CONTRACT head, the
#: commit at which HPAC-PAWA-001 became v2.0 and HPAC-PAWA-HELPER-001 v1.0 was
#: first frozen. This IV changes no contract byte; ENTRY == the IV baseline.
ENTRY = "3cdc3c089e5f8952b0d46b7c95b6c6bf580754e8"

PAWA = ROOT / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
HELPER = ROOT / "docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
PPA = ROOT / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
RHAMP = ROOT / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
HBDC = ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
RIHAC = ROOT / "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
RIASC = ROOT / "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
RDGO = ROOT / "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N16_5_F_5_TB_CONTRACT_IV.md"
PRED_SUITE = ROOT / (
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1_1_1_n16_5_f_5_tb_contract.py"
)

CANONICAL_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1"
    ".1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1"
)
PREDECESSOR_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1"
    ".1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1"
)

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

# The exact 13 conjuncts of §33C TrustedProtectedAuthorityConsumer(request).
CONJUNCTS_33C = (
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
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(path: Path) -> str:
    return re.sub(r"\s+", " ", text(path))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


# ==========================================================================
# 0. CPIPC identity and predecessor coherence
# ==========================================================================

def test_00_cpipc_child_is_exact_canonical_direct_successor() -> None:
    from pcae.core import phase_id as p

    assert p.is_valid(CANONICAL_PHASE_ID)
    assert p.validate(CANONICAL_PHASE_ID) is None
    assert p.format(p.parse(CANONICAL_PHASE_ID)) == CANONICAL_PHASE_ID
    a, b = p.parse(PREDECESSOR_PHASE_ID), p.parse(CANONICAL_PHASE_ID)
    assert p.compare(a, b) == "less"
    assert p.same_series(a, b) and p.same_branch(a, b)
    # exactly one appended `.1` subphase segment
    assert CANONICAL_PHASE_ID == PREDECESSOR_PHASE_ID + ".1"
    assert len(CANONICAL_PHASE_ID.split(".")) == len(PREDECESSOR_PHASE_ID.split(".")) + 1


def test_00b_child_id_is_a_distinct_new_cpipc_identity() -> None:
    """A strict CPIPC child of the predecessor that, at the phase-entry SHA
    (before this phase's own commits), appeared nowhere in git or the tree --
    it reuses no completed or blocked phase identity."""
    from pcae.core import phase_id as p

    assert CANONICAL_PHASE_ID != PREDECESSOR_PHASE_ID
    assert p.compare(p.parse(PREDECESSOR_PHASE_ID), p.parse(CANONICAL_PHASE_ID)) == "less"
    assert CANONICAL_PHASE_ID not in _git("log", ENTRY, "--format=%H %s")
    hits = subprocess.run(
        ["git", "grep", "-lF", CANONICAL_PHASE_ID, ENTRY, "--", "docs", "tasks", ".pcae"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert hits.stdout.strip() == ""
    # after finalization it is carried by this phase's own canonical report
    assert CANONICAL_PHASE_ID in text(REPORT)


def test_00c_predecessor_is_completed_contract_freeze() -> None:
    """Confirmed from immutable primary sources -- the predecessor's own
    canonical report doc and the frozen HPAC-PAWA-001 v2.0 header -- not the
    live (now-superseded) metadata / PROJECT_STATUS."""
    pred_report = ROOT / (
        "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N16_5_F_5_TB_CONTRACT.md"
    )
    assert pred_report.exists()
    rt = text(pred_report)
    assert "COMPLETE — CONTRACT FROZEN" in rt
    assert PREDECESSOR_PHASE_ID in rt
    assert text(PAWA).splitlines()[0].startswith("# HPAC-PAWA-001 v2.0 —")
    assert text(HELPER).splitlines()[0].startswith("# HPAC-PAWA-HELPER-001 v1.0 —")


# ==========================================================================
# 1. Byte baselines — both contracts, and the sibling set
# ==========================================================================

def test_01_pawa_v2_0_and_helper_v1_0_frozen_headers() -> None:
    assert text(PAWA).splitlines()[0].startswith("# HPAC-PAWA-001 v2.0 —")
    assert "**Version:** 2.0" in text(PAWA)
    h = text(HELPER)
    assert h.splitlines()[0].startswith("# HPAC-PAWA-HELPER-001 v1.0 —")
    assert "**Version:** 1.0" in h
    assert "**Status:** FROZEN" in h


def test_02_iv_changes_no_contract_byte() -> None:
    """This IV is contract-verification only: no docs/contracts edit at all."""
    changed = _git("diff", "--name-only", ENTRY, "HEAD", "--", "docs/contracts").split()
    assert changed == []


def test_03_no_production_or_schema_change_this_phase() -> None:
    for area in ("src/pcae", "scripts", "pyproject.toml", "schemas"):
        assert _git("diff", "--name-only", ENTRY, "HEAD", "--", area).split() == [], area


def test_04_sibling_contracts_byte_unchanged_since_pawa_v2_0_freeze() -> None:
    """v2.0 claims HPAC-001 v2.1 / RHAMP-001 v1.0 / HPAC-PPA-001 v1.0 /
    HBDC-001 v1.2 / RIHAC-001 v2.0 / RIASC-001 v3.0 / RDGO-001 v3.1 and the
    protected-root schemas are byte-unchanged. Verify against the v2.0 freeze."""
    v2_freeze = _git(
        "log", "-1", "--format=%H", "--", PAWA.relative_to(ROOT).as_posix()
    ).strip()
    for sib in (HPAC, RHAMP, PPA, HBDC, RIHAC, RIASC, RDGO):
        rel = sib.relative_to(ROOT).as_posix()
        assert _git("diff", "--name-only", v2_freeze, "HEAD", "--", rel).strip() == "", rel


def test_05_sibling_version_headers_match_v2_0_claims() -> None:
    assert text(HPAC).splitlines()[0].startswith("# HPAC-001 v2.1 —")
    assert text(RHAMP).splitlines()[0].startswith("# RHAMP-001 v1.0 —")
    # Point-in-time guard reconciled by phase N16-5-F-5-PPA-CONTRACT
    # (HPAC-PPA-001 v1.0 -> v2.0, MAJOR): v2.0 is the current in-place evolution
    # (out-of-process presentation-evidence writer ownership); v1.0 is the floor.
    assert text(PPA).splitlines()[0].startswith(
        ("# HPAC-PPA-001 v1.0 —", "# HPAC-PPA-001 v2.0 —")
    )
    assert text(RIHAC).splitlines()[0].startswith("# RIHAC-001 v2.0 —")
    assert text(RIASC).splitlines()[0].startswith("# RIASC-001 v3.0 —")
    assert text(RDGO).splitlines()[0].startswith("# RDGO-001 v3.1 —")


# ==========================================================================
# 2. MAJOR (S-4) classification — independently reconstructed
# ==========================================================================

def test_10_minor_permit_list_is_closed_and_v2_0_is_outside_it() -> None:
    """§153's MINOR permits are a closed enumeration. Independently: v2.0
    replaces a normative recognition predicate (§32 predicate 6 / §33 step 9)
    and restructures the authority-delivery model — neither is in the list."""
    t = text(PAWA)
    # the closed permit list still reads exactly as at v1.4 (a MAJOR does not
    # widen the MINOR permits)
    assert "**HPAC-PAWA-REQ-153.** A **MINOR** may:" in t
    permit_block = t.split("**HPAC-PAWA-REQ-153.**", 1)[1].split("**HPAC-PAWA-REQ-154.**", 1)[0]
    for forbidden in ("replace", "out-of-process", "helper process", "which OS actor"):
        assert forbidden not in permit_block.lower() or forbidden == "replace"
    # v2.0 explicitly records the classification and the rejected counter-argument
    assert "Explicit MAJOR rule (S-4)" in t
    assert "outside every HPAC-PAWA-REQ-153 MINOR permit" in t
    assert "provided no meaning above changes" in t
    assert "is **rejected**" in t  # the "tighten a bound" counter-argument


def test_11_no_section_152_verbatim_trigger_fires() -> None:
    j = re.sub(r"\s+", " ", text(PAWA))
    # the local one-shot channel is not a remote/network/cloud transport
    assert "a **local** private parent/child pipe / `AF_UNIX` socket" in j
    # helper_sha256 is a content-integrity digest, not a cryptographic authority key
    assert "not a cryptographic authority key" in j
    # the review is recorded but the classification rests on the closed §153 list
    assert "No §152 trigger fires verbatim; the MAJOR classification stands on HPAC-PAWA-REQ-331 / §153." in j
    assert "the classification rests on §153's closed permit list, not on a\n  §152 verbatim trigger" in text(PAWA) or (
        "the classification rests on §153's closed permit list" in j
    )


def test_12_dedicated_iv_is_required_not_foldable() -> None:
    t = text(PAWA)
    assert "Dedicated contract IV — REQUIRED (not merely" in t
    assert "folding it into a later implementation IV is\n  **not** permitted" in t or (
        "folding it into a later implementation IV is **not** permitted"
        in re.sub(r"\s+", " ", t)
    )
    assert "HPAC-PAWA-REQ-330" in t


# ==========================================================================
# 3. §33C — exact TrustedProtectedAuthorityConsumer conjunction, fail-closed
# ==========================================================================

def test_20_all_thirteen_conjuncts_present_in_req_311() -> None:
    block = text(PAWA).split("**HPAC-PAWA-REQ-311.**", 1)[1].split("**HPAC-PAWA-REQ-312.**", 1)[0]
    for c in CONJUNCTS_33C:
        assert c in block, c
    # the conjunction is AND-composed with an explicit iff / fail-closed frame
    assert "iff ALL" in block or "**iff ALL**" in block
    assert "failure of **ANY** conjunct" in block or "any conjunct fails" in block.lower()
    assert "no** single conjunct is sufficient" in block or "no single conjunct" in block.lower()
    assert "no** in-process fallback" in block or "no in-process fallback" in block.lower()
    assert "no caller self-assertion" in block.lower()


def test_21_no_single_fact_is_the_recognition_predicate() -> None:
    """REQ-312: none of channel-fd / euid==0 / env var / path / hash-alone /
    launcher-identity-alone / peer-credential-alone is the positive predicate."""
    block = text(PAWA).split("**HPAC-PAWA-REQ-312.**", 1)[1].split("**HPAC-PAWA-REQ-313.**", 1)[0]
    for fact in (
        "possession of the channel fd",
        "`euid == 0`",
        "an environment variable",
        "the helper executable path",
        "the helper hash\n  alone" if False else "helper hash",
        "launcher's identity alone",
        "the peer credential alone",
    ):
        assert fact.replace("\n  ", " ") in block.replace("\n  ", " "), fact


def test_22_section_33C_fails_closed_onto_existing_codes() -> None:
    t = text(PAWA)
    assert "HPAC-PAWA-REQ-314" in t
    b = t.split("**HPAC-PAWA-REQ-314.**", 1)[1].split("**HPAC-PAWA-REQ-315.**", 1)[0]
    assert "fails closed" in b
    assert "§42H mapping" in b or "42H" in b
    assert "The absence of a denial is never authority." in b


def test_23_section_33C_runs_fresh_every_exec_no_cache() -> None:
    b = text(PAWA).split("**HPAC-PAWA-REQ-313.**", 1)[1].split("**HPAC-PAWA-REQ-314.**", 1)[0]
    assert "fresh" in b and "every" in b
    assert "No result is cached across processes." in b
    assert "gone at exit" in b


# ==========================================================================
# 4. Same-interpreter production predicate — eliminated
# ==========================================================================

def test_30_section_32_predicate_6_and_33_step_9_superseded() -> None:
    """The predecessor kept every v1.x REQ body byte-verbatim (commit b34cc348
    reverted a transient mid-list edit); the supersession is expressed as
    APPENDED notes + the §7D delta table + §33C REQ-311, never a mid-body edit."""
    j = re.sub(r"\s+", " ", text(PAWA))
    # §32 appended note
    assert 'predicate 6 — the "calling module is an authorized factory consumer" check — is SUPERSEDED by §33C.' in j
    # §33 step 9 body is preserved verbatim as at v1.4 ...
    assert "verify the calling module is an authorized factory consumer (§32, §38)" in j
    # ... and its replacement is stated by the appended REQ-075 / §33A / §33B notes
    assert "Step 9 is replaced per §33C step 9′" in j
    assert "Step 9 is\n  replaced per §33C step 9′" in text(PAWA) or "Step 9 is replaced per §33C step 9′" in j
    # §7D delta table row
    assert "consumer-authenticity predicate (§32 predicate 6 / §33 step 9)" in j
    assert "no in-process fallback" in j


def test_31_no_in_process_production_authority_object_normatively_permitted() -> None:
    b = text(PAWA).split("**HPAC-PAWA-REQ-315.**", 1)[1].split("**HPAC-PAWA-REQ-316.**", 1)[0]
    j = re.sub(r"\s+", " ", b)
    assert "the ordinary PCAE interpreter contains **no** `HPACWriterCapability`" in j
    assert "_verified_production_caller_name" in b
    assert "_detect_caller_module" in b
    assert "_PINNED_*" in b
    assert "the recognition\n  predicate is **not**" in b or "the recognition predicate is **not**" in j


def test_32_no_compatibility_shim_may_preserve_the_in_process_path() -> None:
    joined = re.sub(r"\s+", " ", text(PAWA))
    assert joined.count("compatibility shim MUST NOT preserve the insecure in-process") >= 3
    assert "removal is a later governed" in joined


def test_33_forbidden_in_process_identity_signals_enumerated() -> None:
    """REQ-316: trust rests on none of module name / __module__ / __file__ /
    inspect.stack() / sys.modules / mutable globals / closure hiding / etc."""
    b = text(PAWA).split("**HPAC-PAWA-REQ-316.**", 1)[1].split("## 38C.", 1)[0]
    for sig in (
        "module / function name",
        "`inspect.stack()` textual identity",
        "`sys.modules` keys",
        "mutable module\n  globals",
        "closure hiding",
        "in-process bearer-object\n  possession",
        "a filesystem path alone",
        "digest consistency alone",
    ):
        assert sig.replace("\n  ", " ") in b.replace("\n  ", " "), sig


# ==========================================================================
# 5. No authority-object export (PAWA-INV-15/16 · PAWAH-INV-1)
# ==========================================================================

def test_40_pawa_inv_15_covers_named_and_semantic_equivalents() -> None:
    t = text(PAWA)
    b = t.split("- **PAWA-INV-15.**", 1)[1].split("- **PAWA-INV-16.**", 1)[0]
    for name in (
        "HPACWriterCapability",
        "HPACStoreAuthority",
        "CertificationReadAuthority",
        "ProductionWriterHandle",
        "presentation-evidence writer",
        "seal",
        "opaque handle",
        "capability\n  token",
        "reconstructable field set",
    ):
        assert name.replace("\n  ", " ") in b.replace("\n  ", " "), name


def test_41_helper_side_no_export_by_name_and_by_equivalence() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-091.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-092.**", 1
    )[0]
    assert "by name **and by semantic equivalence**" in b
    assert "any transferable object whose possession enables an equivalent privileged operation" in b
    assert "reconstructable field set" in b


def test_42_caller_receives_only_typed_evidence() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-092.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-093.**", 1
    )[0]
    assert "decision" in b and "evidence_ref" in b and "evidence_digest" in b
    assert "result_payload" in b
    assert "Nothing else." in b
    assert "no** \"capability token\" workaround" in b or "no \"capability token\" workaround" in b


def test_43_privileged_side_owns_the_operation() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-093.**", 1)[1].split("## 25.", 1)[0]
    assert "helper performs the exact mutation / read / ceremony\n  entry itself" in b or (
        "helper performs the exact mutation / read / ceremony entry itself"
        in re.sub(r"\s+", " ", b)
    )
    assert "never receive authority\n  to perform the mutation later" in b or (
        "never receive authority to perform the mutation later" in re.sub(r"\s+", " ", b)
    )


# ==========================================================================
# 6. Closed operation vocabulary
# ==========================================================================

def test_50_operation_vocab_is_exactly_five_closed_members() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-053.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-054.**", 1
    )[0]
    for op in OPERATION_VOCAB:
        assert f"`{op}`" in b, op
    # no sixth family
    assert "operation family is a **MAJOR**" in re.sub(r"\s+", " ", text(HELPER)) or (
        "otherwise it is a\n  **MAJOR**" in text(HELPER)
    )


def test_51_unknown_prefix_wildcard_version_are_denied() -> None:
    joined = re.sub(r"\s+", " ", text(HELPER))
    assert "Unknown operation → DENY. Unrecognized operation version → DENY. Prefix / wildcard / extension matching → DENY." in joined
    joined_p = re.sub(r"\s+", " ", text(PAWA))
    assert "Unknown operation → DENY; unrecognized\n  operation version → DENY; prefix / wildcard / extension matching → DENY." in text(PAWA) or (
        "Unknown operation → DENY; unrecognized operation version → DENY; prefix / wildcard / extension matching → DENY." in joined_p
    )


def test_52_operation_params_is_a_closed_typed_struct_never_a_blob() -> None:
    joined = re.sub(r"\s+", " ", text(HELPER))
    assert "never** a free path string, expression, shell command, module name, JSON-patch blob, or executable path" in joined or (
        "never a free path string, expression, shell command, module name, JSON-patch blob, or executable path" in joined
    )


def test_53_supported_operations_gating() -> None:
    assert "HPAC-PAWA-HELPER-REQ-054" in text(HELPER)
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-054.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-055.**", 1
    )[0]
    assert "supported_operations" in b and "fails closed" in b


# ==========================================================================
# 7. configure_privileged_helper — metadata only, no second trust root
# ==========================================================================

def test_60_configure_privileged_helper_is_metadata_only() -> None:
    b = text(PAWA).split("**HPAC-PAWA-REQ-326.**", 1)[1].split("**HPAC-PAWA-REQ-327.**", 1)[0]
    assert "metadata-only" in b
    assert "SHALL\n  **NOT** create, copy, replace, `chmod`, `chown`, or execute helper bytes" in b or (
        "SHALL **NOT** create, copy, replace, `chmod`, `chown`, or execute helper bytes"
        in re.sub(r"\s+", " ", b)
    )
    assert "`PawaOperation` count\n  becomes **7**" in b or "PawaOperation count becomes **7**" in re.sub(r"\s+", " ", b)


def test_61_helper_registration_is_not_a_trust_root() -> None:
    t = text(PAWA)
    b = t.split("- **PAWA-INV-17.**", 1)[1].split("## 93.", 1)[0]
    assert "No second trust root." in b
    assert "integrity-pinned artifact of the existing kind" in b
    assert "registration is **not** a bootstrap authority" in b
    for distinct in ("`helper hash`", "`executable path`", "`launcher identity`", "`peer\n  credential`", "`operation authorization`"):
        assert distinct.replace("\n  ", " ") in b.replace("\n  ", " "), distinct


def test_62_configure_privileged_helper_driven_through_the_helper_boundary() -> None:
    b = text(PAWA).split("**HPAC-PAWA-REQ-328.**", 1)[1].split("## 42H.", 1)[0]
    assert "driven through the §33C helper boundary" in b
    assert "not in the main interpreter" in b


def test_63_non_circular_bootstrap() -> None:
    b = text(PAWA).split("**HPAC-PAWA-REQ-327.**", 1)[1].split("**HPAC-PAWA-REQ-328.**", 1)[0]
    assert "no pre-existing\n  privileged-helper operation and no ceremony" in b or (
        "no pre-existing privileged-helper operation and no ceremony" in re.sub(r"\s+", " ", b)
    )
    assert "after** the\n  helper bytes have been installed out of band" in b or (
        "after the helper bytes have been installed out of band" in re.sub(r"\s+", " ", b)
    )


# ==========================================================================
# 8. Helper contract — provenance, peer-auth, same-file-object, cross-platform
# ==========================================================================

def test_70_helper_req_ids_contiguous_1_to_114() -> None:
    ids = sorted(int(m) for m in re.findall(r"\*\*HPAC-PAWA-HELPER-REQ-(\d{3})\.\*\*", text(HELPER)))
    assert ids == list(range(1, 115))
    for n in range(1, 11):
        assert text(HELPER).count(f"- **PAWAH-INV-{n}.**") == 1, n


def test_71_same_file_object_is_a_frozen_property_not_a_syscall() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-029.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-030.**", 1
    )[0]
    assert "same\n  file object" in b or "same file object" in re.sub(r"\s+", " ", b)
    assert "pathname re-open\n  after validation is forbidden" in b or (
        "pathname re-open after validation is forbidden" in re.sub(r"\s+", " ", b)
    )
    assert "STOPS BLOCKED" in b
    assert "freezes this **property**" in b


def test_72_cross_platform_macos_and_linux_feasible_or_blocked() -> None:
    j = re.sub(r"\s+", " ", text(HELPER))
    assert "SO_PEERCRED" in j and "LOCAL_PEERCRED" in j and "getpeereid" in j
    assert "fexecve" in j and ("execveat" in j or "AT_EMPTY_PATH" in j)
    assert "not** assumed byte-for-byte equivalent" in j or "not assumed byte-for-byte equivalent" in j
    assert "STOPS BLOCKED" in j  # a platform that cannot realize a property is blocked, not downgraded


def test_73_peer_auth_precedes_admission_and_any_protected_read() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-043.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-044.**", 1
    )[0]
    assert "before** operation admission" in b or "before operation admission" in re.sub(r"\s+", " ", b)
    assert "before** any protected-store\n  read" in b or "before any protected-store read" in re.sub(r"\s+", " ", b)


def test_74_peer_credential_is_kernel_authenticated_never_caller_asserted() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-042.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-043.**", 1
    )[0]
    assert "kernel-authenticated" in b
    assert "not** from any peer-supplied protocol field" in b or (
        "not from any peer-supplied protocol field" in re.sub(r"\s+", " ", b)
    )
    assert "not** the configured agent principal" in b or "not the configured agent principal" in re.sub(r"\s+", " ", b)


def test_75_configured_agent_identity_never_ambient_root() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-032.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-033.**", 1
    )[0]
    for s in ("never** against\n  `os.geteuid()`", "SUDO_", "mints **nothing**"):
        assert s.replace("\n  ", " ") in b.replace("\n  ", " "), s


def test_76_request_carries_no_authority_and_no_field_asserts_trust() -> None:
    j = re.sub(r"\s+", " ", text(HELPER))
    assert "The request carries **no authority**" in j
    b = j.split("HPAC-PAWA-HELPER-REQ-047.", 1)[1].split("HPAC-PAWA-HELPER-REQ-048.", 1)[0]
    for forbidden in ("caller-provided `approved=True`", "a shell command", "an executable path", "a role string beyond the\n  enumerated five".replace("\n  ", " ")):
        assert forbidden in b, forbidden


# ==========================================================================
# 9. Freshness / replay / state-transition / crash / audit ordering
# ==========================================================================

def test_80_replay_dispositions_are_all_distinct() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-076.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-077.**", 1
    )[0]
    for state in ("fresh", "consumed", "duplicate", "expired", "unknown", "conflicting replay"):
        assert f"**{state}**" in b, state
    assert "cannot** be accepted again, even if its response was lost" in b or (
        "cannot be accepted again, even if its response was lost" in re.sub(r"\s+", " ", b)
    )


def test_81_lost_response_never_frees_a_spent_request() -> None:
    j = re.sub(r"\s+", " ", text(HELPER))
    assert "A lost response does not make the original\n  request unused.".replace("\n  ", " ") in j
    assert "response loss is **never** proof the mutation did not happen" in j


def test_82_state_model_has_the_no_auto_retry_boundary() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-079.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-080.**", 1
    )[0]
    for st in (
        "REQUEST_RECEIVED",
        "REQUEST_AUTHENTICATED",
        "OPERATION_ADMITTED",
        "MUTATION_ATTEMPT_STARTED",
        "MUTATION_COMMITTED",
        "EVIDENCE_WRITTEN",
        "RESPONSE_EMITTED",
    ):
        assert st in b, st
    assert "no-auto-retry boundary is now crossed" in b


def test_83_indeterminate_reconciliation_required_state_exists() -> None:
    j = re.sub(r"\s+", " ", text(HELPER))
    assert "INDETERMINATE / RECONCILIATION REQUIRED" in j
    assert "not** a silent success and **not** a retry" in j or "not a silent success and not a retry" in j
    assert "Unknown outcome remains unknown until\n  reconciled.".replace("\n  ", " ") in j


def test_84_audit_evidence_staged_before_mutation() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-086.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-087.**", 1
    )[0]
    assert "evidence durably staged before the mutation" in b
    assert "abort before any mutation" in b
    assert "does **not** claim \"audit-write failure means the mutation did not occur\"" in re.sub(
        r"\s+", " ", text(HELPER)
    )


# ==========================================================================
# 10. Five-role closure · typed-read non-reconstructibility · ceremony entry
# ==========================================================================

def test_90_five_role_closure_is_exact_and_terminator_excluded() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-059.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-060.**", 1
    )[0]
    for r in FIVE_ROLES:
        assert r in b, r
    assert "`hpac_lifecycle_terminator` is **explicitly NOT**\n  a member".replace("\n  ", " ") in b.replace("\n  ", " ")
    assert "No wildcard, no prefix, no `fnmatch`" in b
    # PAWA-INV-13 annotated 'delivery superseded — substance unchanged'
    assert "delivery superseded by §33C — substance\n  unchanged".replace("\n  ", " ") in re.sub(
        r" +", " ", text(PAWA)
    ).replace("\n  ", " ")


def test_91_typed_reads_cannot_reconstruct_store_authority() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-065.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-066.**", 1
    )[0]
    assert "Repeated typed reads SHALL NOT reconstruct\n  unrestricted store authority.".replace("\n  ", " ") in b.replace("\n  ", " ")
    assert "cannot iterate it into a generic read broker" in b
    assert "record **contents**, not a store handle" in b


def test_92_typed_read_forbids_arbitrary_and_secret_reads() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-064.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-065.**", 1
    )[0]
    for forbidden in ("arbitrary\n  filesystem read", "wildcard field selection", "FIDO2 PIN", "a private\n  key", "any** write, create, replace"):
        assert forbidden.replace("\n  ", " ") in b.replace("\n  ", " "), forbidden


def test_93_ceremony_entry_is_only_a_bounded_handoff() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-068.**", 1)[1].split(
        "**HPAC-PAWA-HELPER-REQ-069.**", 1
    )[0]
    for wall in (
        "ceremony entry  != approval",
        "ceremony entry  != authentication",
        "ceremony entry  != Gate-5 ALLOW",
        "ceremony entry  != PB permission",
        "ceremony entry  != execution",
        "ceremony entry  != real assurance",
    ):
        assert wall in b, wall
    assert "never** produces its outcome" in b or "never produces its outcome" in re.sub(r"\s+", " ", b)


# ==========================================================================
# 11. Failure codes · RHAMP non-expansion · generic-broker prohibition
# ==========================================================================

def test_a0_no_new_pawa_failure_code_deterministic_mapping() -> None:
    b = text(PAWA).split("## 42H.", 1)[1].split("## 49C.", 1)[0]
    assert "no new\n  `pawa_failure_code` is created; the taxonomy remains 21 closed values".replace("\n  ", " ") in b.replace("\n  ", " ")
    # every listed v2.0 rejection row names an existing code number
    rows = [ln for ln in b.splitlines() if ln.startswith("  | ") and "`" in ln]
    assert len(rows) >= 8
    assert "No new\n  `terminal_reason_code`; RHAMP-001 v1.0 §49's 41-code vocabulary is\n  byte-unchanged".replace("\n  ", " ") in b.replace("\n  ", " ")


def test_a1_rhamp_not_edited_and_no_helper_op_bypasses_verifier() -> None:
    j = re.sub(r"\s+", " ", text(HELPER))
    assert "RHAMP-001 v1.0 §49 is byte-unchanged" in j
    assert "introduces **no** new TTL and the helper SHALL NOT bypass any existing one" in j
    assert "trust a caller-provided \"counter accepted\"" in j


def test_a2_generic_privileged_broker_prohibited() -> None:
    b = text(HELPER).split("**HPAC-PAWA-HELPER-REQ-094.**", 1)[1].split("## 26.", 1)[0]
    for forbidden in (
        "arbitrary filesystem path mutation",
        "arbitrary command execution",
        "arbitrary Python execution / eval / exec of caller bytes",
        "arbitrary store-method dispatch",
        "unrestricted registry editing",
        "generic secret retrieval",
        "unrestricted process launch",
        "\"run this operation by name\" or \"apply this JSON patch\" entry point",
    ):
        assert forbidden in b, forbidden


# ==========================================================================
# 12. Walls · deterministic-vs-real · mechanism neutrality · runtime posture
# ==========================================================================

def test_b0_section_68C_walls_preserved_verbatim() -> None:
    b = text(PAWA).split("## 68C.", 1)[1].split("## 69.", 1)[0]
    for wall in (
        "OS peer credential                         != human identity != informed intent",
        "successful §33C recognition                != real assurance",
        "typed evidence / a typed read result       != HPACWriterCapability / HPACStoreAuthority",
        "ceremony_entry                             != approval != authentication != Gate-5 ALLOW != PB permission != execution",
        "deterministic input                        never becomes REAL assurance through the helper",
    ):
        assert wall in b, wall
    assert "first governed runtime external effect stays ABSENT / UNREACHABLE" in b


def test_b1_deterministic_vs_real_wall_permanent() -> None:
    j = re.sub(r"\s+", " ", text(HELPER))
    assert "a test helper speaking the protocol ≠ production authority" in j
    assert "remains permanently unable** to produce `PRODUCTION` authority" in j or (
        "remains permanently unable to produce `PRODUCTION` authority" in j
    )
    assert "does not relax the check" in j


def test_b2_mechanism_neutral_mobile_future_open() -> None:
    b = text(HELPER).split("## 27.", 1)[1].split("## 28.", 1)[0]
    assert "SHALL NOT hardcode YubiKey, FIDO2, USB, a specific AAGUID" in b
    assert "mobile-only / passkey**\n  authentication-and-approval path stays open".replace("\n  ", " ") in b.replace("\n  ", " ")
    assert "SHALL NOT be a prerequisite for ordinary\n  non-effecting PCAE development".replace("\n  ", " ") in b.replace("\n  ", " ")


def test_b3_runtime_posture_unchanged_zero_plugins_zero_capabilities() -> None:
    for c in (PAWA, HELPER):
        j = re.sub(r"\s+", " ", text(c))
        assert "0 plugins / 0 capabilities" in j
        assert "ABSENT" in j
    assert "N-16-6 and N-16-7 remain **OPEN and untouched**; N-16-7 strictly last." in re.sub(
        r"\s+", " ", text(HELPER)
    )


def test_b4_bounded_security_claims_no_overclaim() -> None:
    b = text(HELPER).split("### 26.2 Bounded security claims", 1)[1].split("## 27.", 1)[0]
    assert "does NOT claim protection\n  against:".replace("\n  ", " ") in b.replace("\n  ", " ")
    for excluded in ("hostile root / admin", "compromised OS kernel", "byte-identical whole trusted-machine snapshot", "single-account\n  host"):
        assert excluded.replace("\n  ", " ") in b.replace("\n  ", " "), excluded


# ==========================================================================
# 13. THE MANDATORY HPAC-PPA-001 EVIDENCE-WRITER ADJUDICATION → OPTION B
# ==========================================================================

def test_c0_ppa_v1_0_holds_the_evidence_writer_only_in_the_launcher_mediator() -> None:
    """Primary text of HPAC-PPA-001 v1.0 — the constraints the v2.0
    `presentation_evidence_write` operation runs into."""
    t = text(PPA)
    assert "held only by the trusted launcher mediator" in t
    assert "It is never sent to the helper or requesting caller." in t          # REQ-041
    assert "Evidence producer is only the launcher mediator" in t               # REQ-054
    assert (
        "Installer, launcher, helper response, and evidence writer are\n  distinct trust actions with no authority transfer."
        in t
    )  # PPA-INV-2


def test_c1_helper_v1_0_puts_presentation_evidence_write_inside_the_helper() -> None:
    j = re.sub(r"\s+", " ", text(HELPER))
    assert "invoked **by\n  the HPAC-PPA-001 presentation helper itself**".replace("\n  ", " ") in j
    # the contract itself flags the unresolved question and defers it
    assert "an explicit question for the dedicated\ncontract IV".replace("\n", " ") in j
    assert "a re-meaning of \"never sent to the helper\"" in j
    assert "frozen here as a **specification** consistent\n  with option (a)".replace("\n  ", " ") in j


def test_c2_iv_adjudication_is_option_B_evolution_required() -> None:
    """Independent IV determination (see the canonical Phase Report §HPAC-PPA):

    `presentation_evidence_write` invoked by the presentation helper itself
      * is 'sent to the helper'  -> contradicts HPAC-PPA-REQ-041 verbatim
      * makes the helper the evidence producer -> contradicts HPAC-PPA-REQ-054
      * merges the 'helper response' and 'evidence writer' trust actions
        -> re-means PPA-INV-2
      * is not 'a platform adapter within these exact properties'
        (HPAC-PPA-REQ-070); it changes which actor holds the writer, a
        MAJOR-class change under HPAC-PPA-REQ-069.

    Therefore option (a) 'COMPATIBLE AS WRITTEN' is NOT sustainable, and the
    adjudication is **B — HPAC-PPA-001 CONTRACT EVOLUTION REQUIRED**.
    """
    r = text(REPORT)
    assert "HPAC-PPA-001 EVIDENCE-WRITER ADJUDICATION: B" in r
    assert "HPAC-PPA-001 CONTRACT EVOLUTION REQUIRED" in r
    assert "NOT VERIFIED / BLOCKED" in r


def test_c3_phase_verdict_is_blocked_and_successor_not_begun() -> None:
    r = text(REPORT)
    assert "N16-5-F-5-TB-CONTRACT-IV: COMPLETE — NOT VERIFIED / BLOCKED" in r
    assert "fresh governed HPAC-PPA-001 contract-evolution phase" in r
    assert "NOT begun" in r or "NOT BEGUN" in r
    for immutable in (
        "**N-16-5** | **NOT CLOSED**",
        "**F-5** | **CERTIFICATION BLOCKED**",
        "**N-16-6 / N-16-7** | **OPEN / UNTOUCHED**",
    ):
        assert immutable in r, immutable


# ==========================================================================
# 14. Historical governance integrity · predecessor suite still green
# ==========================================================================

def test_d0_historical_outcomes_preserved_verbatim() -> None:
    hj = re.sub(r"\s+", " ", text(HELPER))
    assert "N16-5-F-5-B2 NOT VERIFIED / BLOCKED; N16-5-F-5-B2R-IV NOT VERIFIED / BLOCKED; N16-5-F-5-B2R2-IMPL COMPLETE — BLOCKED" in hj
    for c in (PAWA, HELPER):
        j = re.sub(r"\s+", " ", text(c))
        assert "N16-5-F-5-B2R2-IMPL" in j
        assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED" in j
    # the immutable v1.0-v1.4 freeze lineage is intact in PAWA
    pj = re.sub(r"\s+", " ", text(PAWA))
    assert "Historical v1.0–v1.4 freeze records and their IVs remain **immutable**" in pj
    assert "N16-5-F-5-TB-ARCH" in pj


def test_d1_predecessor_contract_suite_still_passes() -> None:
    proc = subprocess.run(
        ["python", "-m", "pytest", "-q", PRED_SUITE.as_posix()],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout[-3000:]
    assert "45 passed" in proc.stdout


def test_d2_no_new_terminal_reason_code_in_rhamp() -> None:
    assert "RHAMP-001 v1.0" in text(RHAMP).splitlines()[0]
    # unchanged 41-code vocabulary asserted by both companions
    pj = re.sub(r"\s+", " ", text(PAWA))
    assert "RHAMP-001 v1.0 §49's 41-code vocabulary is\n  byte-unchanged" in text(PAWA) or (
        "RHAMP-001 v1.0 §49's 41-code vocabulary is byte-unchanged" in pj
    )
    assert "No new\n  `terminal_reason_code`" in text(PAWA) or "No new `terminal_reason_code`" in pj
    assert "RHAMP-001 v1.0 §49 is byte-unchanged" in re.sub(r"\s+", " ", text(HELPER))
