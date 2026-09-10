"""Contract-level verification for phase N16-5-F-5-PPA-CONTRACT
(149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1)
— HPAC-PPA-001 Contract Evolution: Out-of-Process Presentation-Evidence Writer
Ownership Alignment (HPAC-PPA-001 v1.0 -> v2.0 FROZEN, MAJOR).

Intentionally static / read-only. This phase evolves normative contract text
only. It implements NO helper executable, launcher, IPC channel, or evidence
write; performs NO protected-host mutation and NO ceremony; changes NO
`src/pcae`, `scripts`, `pyproject.toml`, or `schemas` file.

Resolves the blocking finding of the predecessor contract IV
N16-5-F-5-TB-CONTRACT-IV (evidence-writer-delivery adjudication option B):
HPAC-PAWA-HELPER-001 v1.0 §17 and HPAC-PAWA-001 v2.0 §42B note freeze
`presentation_evidence_write` as invoked by the HPAC-PPA-001 presentation
helper itself, conflicting with HPAC-PPA-001 v1.0 HPAC-PPA-REQ-041 / -052 /
-054 and PPA-INV-2.

N-16-5 is NOT CLOSED by this phase. The dedicated IV N16-5-F-5-PPA-CONTRACT-IV
is derived but NOT begun.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Phase-entry SHA — the finalized predecessor N16-5-F-5-TB-CONTRACT-IV head
#: plus the governed task-transition commit that opened this phase. HPAC-PPA-001
#: is v1.0 at ENTRY; this phase's sole normative delta is HPAC-PPA-001 -> v2.0.
ENTRY = "f0ca3423ece0a54052dd1195f5c889865eb19c3d"

PPA = ROOT / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
PAWA = ROOT / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
HELPER = ROOT / "docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
RHAMP = ROOT / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
HBDC = ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
RIHAC = ROOT / "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
RIASC = ROOT / "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
RDGO = ROOT / "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
SCHEMAS = ROOT / "src/pcae/core/hpac_pawa_schemas.py"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N16_5_F_5_PPA_CONTRACT.md"

CANONICAL_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1"
    ".1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1"
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
# CPIPC identity
# --------------------------------------------------------------------------

def test_01_canonical_phase_id_is_the_cpipc_child_of_the_predecessor() -> None:
    from pcae.core import phase_id as p

    pred = (
        "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1"
        ".1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1"
    )
    assert p.is_valid(CANONICAL_PHASE_ID)
    assert p.normalize(CANONICAL_PHASE_ID) == CANONICAL_PHASE_ID
    a, b = p.parse(pred), p.parse(CANONICAL_PHASE_ID)
    assert p.same_series(a, b) and p.same_branch(a, b)
    assert p.compare(a, b) == "less"
    assert len(b.subphase) == len(a.subphase) + 1
    assert b.subphase[-1] == (1, "")


def test_02_phase_id_is_unique_against_history_and_docs() -> None:
    # The trailing token appears only in this phase's own commit subjects.
    token = "1R.1.1.1.1.1.1 ("
    subjects = [l for l in _git("log", "--all", "--pretty=%s").splitlines() if token in l]
    assert subjects and all("N16-5-F-5-PPA-CONTRACT" in l for l in subjects)
    # no successor id (this id + .1) is reserved anywhere yet
    for base in ("docs", "tasks", ".pcae"):
        out = subprocess.run(
            ["grep", "-rlF", CANONICAL_PHASE_ID + ".1", str(ROOT / base)],
            capture_output=True, text=True,
        )
        assert out.stdout.strip() == ""


# --------------------------------------------------------------------------
# HPAC-PPA-001 v2.0 — identity, versioning, numbering, append-only
# --------------------------------------------------------------------------

def test_03_ppa_header_is_v2_0_frozen() -> None:
    t = text(PPA)
    assert t.splitlines()[0].startswith("# HPAC-PPA-001 v2.0 —")
    assert "**Version:** 2.0" in t
    assert "**Status:** FROZEN" in t
    assert "IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING" in t


def test_04_v2_0_evolution_record_is_appended_not_a_rewrite() -> None:
    t = text(PPA)
    assert "**Evolved to v2.0 by:** Phase" in t
    # the v1.0 initial-freeze record is preserved
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R — N-16-5 Protected-Presentation" in t
    assert "`HPAC-PPA-REQ-001..075`, `PPA-INV-1..8`" in t


def test_05_version_classification_is_major_under_req_069() -> None:
    # collapse markdown blockquote markers and whitespace
    t = re.sub(r"\s+", " ", text(PPA).replace("> ", ""))
    assert "**MAJOR** under" in text(PPA) or "MAJOR under HPAC-PPA-REQ-069" in t
    assert "(v2.0) §14 note — version classification of the v2.0 evolution." in text(PPA)
    assert "is a MAJOR" in t
    assert "not** a HPAC-PPA-REQ-070 MINOR" in t
    # REQ-041's parenthetical governs which primitive, not which component holds it
    assert "which primitive" in t


def test_06_requirement_ids_contiguous_1_to_103() -> None:
    ids = sorted(int(m) for m in re.findall(r"\*\*HPAC-PPA-REQ-(\d{3})\.\*\*", text(PPA)))
    assert ids == list(range(1, 104))
    assert len(ids) == len(set(ids)) == 103


def test_07_v2_0_additions_are_exactly_req_077_to_103() -> None:
    v1 = at_entry(PPA).decode("utf-8")
    v1_ids = {int(m) for m in re.findall(r"\*\*HPAC-PPA-REQ-(\d{3})\.\*\*", v1)}
    cur_ids = {int(m) for m in re.findall(r"\*\*HPAC-PPA-REQ-(\d{3})\.\*\*", text(PPA))}
    assert max(v1_ids) == 76
    assert sorted(cur_ids - v1_ids) == list(range(77, 104))


def test_08_every_v1_0_requirement_body_survives_verbatim() -> None:
    """A MAJOR may append '(v2.0)' notes and new sections; it never rewords,
    shortens, reorders, or interrupts an existing v1.0 requirement body."""

    def bodies(s: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for m in re.finditer(
            r"- \*\*HPAC-PPA-REQ-(\d{3})\.\*\*(.+?)(?=\n- \*\*HPAC-PPA-REQ-|\n  > |\n#|\n## )",
            s,
            re.S,
        ):
            out[m.group(1)] = re.sub(r"\s+", " ", m.group(2)).strip()
        return out

    b1 = bodies(at_entry(PPA).decode("utf-8"))
    bc = bodies(text(PPA))
    assert set(b1).issubset(bc)
    for rid, body in b1.items():
        assert body and body in bc[rid], rid


def test_09_ppa_invariants_1_to_12_defined_once_each() -> None:
    t = text(PPA)
    for n in range(1, 13):
        assert t.count(f"- **PPA-INV-{n}.") == 1, n


# --------------------------------------------------------------------------
# The evolved evidence-ownership model
# --------------------------------------------------------------------------

def test_10_helper_is_the_sole_evidence_producer() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-077." in text(PPA)
    assert "verified protected\n  presentation helper process" in text(PPA) or "verified protected presentation helper process" in t
    assert "sole author" in t
    assert "supersedes HPAC-PPA-REQ-054" in t
    assert "one valid `APPROVE`" in text(PPA)


def test_11_no_generic_writer_transfer() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-078." in text(PPA)
    assert "No generic writer transfer." in text(PPA)
    for phrase in (
        "HPACWriterCapability",
        "capability token",
        "serialised seal",
        "reconstructable authority descriptor",
        "opaque bearer handle",
    ):
        assert phrase in t, phrase
    assert "no returnable writer" in t


def test_12_launcher_no_longer_holds_production_evidence_writer() -> None:
    t = norm(PPA)
    # §8 note supersedes REQ-041's launcher-holder clause
    assert "(v2.0) §8 note." in text(PPA)
    assert "is **superseded** by §21" in t
    assert "no** `HPACWriterCapability`" in t
    # §10 note: launcher module is no longer the evidence-writer issuer
    assert "no longer** the evidence-writer" in t


def test_13_req_052_issuer_disposition_is_option_c_protected_side_internal() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-081." in text(PPA)
    assert "no longer** the evidence-writer issuer" in t
    assert "protected-side-internal operation of the helper process" in t
    assert "option C of the phase authorisation" in t
    assert "No `mint_*` factory returns a writer" in t


def test_14_helper_response_is_not_evidence_authority() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-082." in text(PPA)
    assert "helper response != evidence-writer\n  authority" in text(PPA) or "helper response != evidence-writer authority" in t
    assert "SHALL NOT be able to reconstruct writer authority from the response" in t


def test_15_ppa_inv_2_is_re_derived_as_semantic_separation() -> None:
    t = norm(PPA)
    assert "PPA-INV-2 (v2.0) — re-derived, semantic separation." in text(PPA)
    assert "even when several are performed by the same verified\n  > protected helper process" in text(PPA) or "even when several are performed by the same verified protected helper process" in t
    assert "HPAC-PPA-REQ-083." in text(PPA)
    # the v1.0 four-action wording is preserved
    assert "Installer, launcher, helper response, and evidence writer are\n  distinct trust actions with no authority transfer." in text(PPA)


def test_16_bounded_helper_write_binds_ceremony_session_subject_generation() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-079." in text(PPA)
    for b in (
        "(invocation_id, attempt_id)",
        "request digest",
        "nonce",
        "installation id",
        "generation",
        "human election outcome actually observed",
        "helper deployment generation",
    ):
        assert b in t, b
    assert "exactly one** create-only" in text(PPA) or "exactly one create-only" in t


def test_17_helper_cannot_self_assert_and_only_input_is_rechecked_response() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-080." in text(PPA)
    assert "SHALL NOT self-assert `approved`, `verified`, `human_present`, or\n  `authenticated`" in text(PPA) or "SHALL NOT self-assert" in t
    assert "independently re-checks" in t


# --------------------------------------------------------------------------
# Semantic walls preserved
# --------------------------------------------------------------------------

def test_18_ceremony_entry_and_approval_and_authentication_stay_distinct() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-093." in text(PPA)
    assert "`approved=true` SHALL NOT create approval" in t or "SHALL NOT create approval" in t
    assert "YubiKey touch = user presence" in t
    assert "UP != approval" in t
    assert "HPAC-PPA-REQ-094." in text(PPA)
    assert "Presentation\n  evidence != authentication proof" in text(PPA) or "Presentation evidence != authentication proof" in t
    assert "own\n  RHAMP / HPAC verification chain" in text(PPA) or "own RHAMP / HPAC verification chain" in t


def test_19_gate5_pb_runtime_execution_non_expansion() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-095." in text(PPA)
    assert "Presentation\n  evidence write != Gate 5 ALLOW" in text(PPA) or "Presentation evidence write != Gate 5 ALLOW" in t
    for wall in (
        "Gate 5 ALLOW != PB permission",
        "PB permission\n  != runtime capability",
        "runtime capability != execution",
    ):
        assert wall in text(PPA) or re.sub(r"\s+", " ", wall) in t, wall
    assert "no first governed runtime external effect" in t.lower() or "first governed runtime external effect remains\n  **ABSENT" in text(PPA)


# --------------------------------------------------------------------------
# Provenance, single trust root, freshness, failure model
# --------------------------------------------------------------------------

def test_20_helper_provenance_same_file_object_alignment() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-088." in text(PPA)
    assert "same** verified protected helper object / process" in text(PPA) or "same verified protected helper object / process" in t
    assert "SHA-256 of the complete opened byte\n  stream `== helper_sha256`" in text(PPA) or "== helper_sha256" in t
    assert "STOPS BLOCKED" in t
    assert "PPA-INV-10." in text(PPA)


def test_21_single_trust_root_unchanged_no_second_root() -> None:
    t = norm(PPA)
    assert "trust root is **unchanged**" in t or "trust root is unchanged" in t
    assert "OS filesystem write authority on the\n  out-of-band-provisioned `<HPAC_PROTECTED_ROOT>`" in text(PPA) or "OS filesystem write authority" in t
    assert "No second trust root is introduced" in t
    assert "helper hash / path / registration metadata alone" in t or "helper hash / path /\n  registration metadata alone" in text(PPA)


def test_22_freshness_and_replay_and_currentness_preserved() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-090." in text(PPA)
    for b in (
        "expired ceremony",
        "consumed ceremony",
        "replayed request",
        "stale installation generation",
        "mismatched presentation mechanism",
    ):
        assert b in t, b
    assert "No response loss makes a consumed\n  ceremony reusable" in text(PPA) or "No response loss makes a consumed ceremony reusable" in t


def test_23_failure_uncertainty_state_model_and_no_auto_retry() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-091." in text(PPA)
    for s in (
        "CEREMONY_REQUEST_RECEIVED",
        "CEREMONY_ADMITTED",
        "PRESENTATION_STARTED",
        "HUMAN_ELECTION_CAPTURED",
        "EVIDENCE_WRITE_ATTEMPT_STARTED",
        "EVIDENCE_COMMITTED",
        "RESPONSE_EMITTED",
    ):
        assert s in t, s
    assert "A missing response is **not** proof that no evidence exists" in t or "not** proof that no evidence exists" in text(PPA)
    assert "HPAC-PPA-REQ-092." in text(PPA)
    assert "no automatic retry" in t


# --------------------------------------------------------------------------
# Relationship to sibling contracts / no scope widening
# --------------------------------------------------------------------------

def test_24_relationship_to_helper_protocol_is_transport_not_authority() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-084." in text(PPA)
    assert "There is no circular authority" in t
    assert "helper protocol transports, this\n  contract adjudicates validity" in text(PPA) or "helper protocol transports, this contract adjudicates validity" in t
    assert "does **not** duplicate the helper\n  protocol's privileged-operation vocabulary" in text(PPA) or "does not duplicate the helper protocol" in t
    assert "PPA-INV-12." in text(PPA)


def test_25_mechanism_neutrality_and_mobile_future_preserved() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-096." in text(PPA)
    assert "does not\n  hardcode YubiKey, FIDO2, a local TTY, USB" in text(PPA) or "does not hardcode YubiKey, FIDO2, a local TTY, USB" in t
    assert "mobile-only / passkey / protected-mobile\n  approval profile remains possible" in text(PPA) or "mobile-only / passkey / protected-mobile approval profile remains possible" in t


def test_26_schema_impact_is_no_change_required() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-097." in text(PPA)
    assert "NO SCHEMA CHANGE REQUIRED" in text(PPA)
    assert "adds, changes, and removes **no** schema field" in t or "no** schema field" in text(PPA)
    assert "verification\n  state**, not a caller-controlled evidence field" in text(PPA) or "verification state" in t


def test_27_no_new_failure_code_or_terminal_reason() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-098." in text(PPA)
    assert "No new `pawa_failure_code`; no new RHAMP\n  `terminal_reason_code`" in text(PPA) or "No new `pawa_failure_code`" in t
    assert "RHAMP-001 v1.0 is byte-unchanged" in t


def test_28_compatibility_shim_forbids_insecure_fallback() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-099." in text(PPA)
    assert "SHALL NOT recreate the v1.0 launcher-held `HPACWriterCapability`" in t
    assert "exactly **one**\n  authoritative production model" in text(PPA) or "exactly one\n  authoritative production model" in text(PPA) or "one** authoritative production model" in t
    assert "superseded and non-production** as of v2.0" in text(PPA) or "superseded and non-production" in t


def test_29_security_claim_boundary_is_bounded() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-100." in text(PPA)
    assert "gc.get_objects()" in t
    assert "SHALL NOT overclaim against" in t
    for x in ("hostile root", "compromised OS kernel", "compromised registered presentation\n  helper binary"):
        assert x in text(PPA) or re.sub(r"\s+", " ", x) in t, x


def test_30_cross_contract_conflict_resolved_and_siblings_byte_unchanged() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-101." in text(PPA)
    assert "resolved **at contract\n  level**" in text(PPA) or "resolved at contract level" in t
    # siblings byte-unchanged since ENTRY
    for c in (PAWA, HELPER, RHAMP, HPAC, HBDC, RIHAC, RIASC, RDGO):
        assert at_entry(c) == c.read_bytes(), c
    assert at_entry(SCHEMAS) == SCHEMAS.read_bytes()


def test_31_pawa_v2_0_and_helper_headers_are_the_frozen_versions() -> None:
    assert text(PAWA).splitlines()[0].startswith("# HPAC-PAWA-001 v2.0 —")
    assert text(HELPER).splitlines()[0].startswith("# HPAC-PAWA-HELPER-001 v1.0 —")
    assert text(RHAMP).splitlines()[0].startswith("# RHAMP-001 v1.0 —")


# --------------------------------------------------------------------------
# Scope fence — this phase changes only contract prose + guards + docs
# --------------------------------------------------------------------------

def test_32_no_src_scripts_pyproject_or_schema_change() -> None:
    changed = _git("diff", "--name-only", ENTRY, "--", "src", "scripts", "pyproject.toml", "schemas").split()
    assert changed == [], changed


def test_33_docs_contracts_delta_is_exactly_hpac_ppa_001() -> None:
    changed = set(_git("diff", "--name-only", ENTRY, "--", "docs/contracts").split())
    assert changed == {"docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"}, changed


def test_34_no_adapter_dispatch_or_effect_symbol_introduced() -> None:
    diff = _git("diff", ENTRY, "--", "docs/contracts", "tests")
    assert "adapter.dispatch(" not in diff
    # the contract explicitly denies any first external effect
    assert "first governed runtime external effect remains\n  **ABSENT" in text(PPA) or "first governed runtime external effect" in norm(PPA)


def test_35_runtime_remains_observed_observe_unavailable() -> None:
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    for value in (
        "not_implemented",
        "Observed",
        "unavailable",
        "Plugin count:              0",
        "Capability count:          0",
    ):
        assert value in out, value


def test_36_downstream_guard_reconciliation_is_widen_not_weaken() -> None:
    """Every touched pre-existing guard suite keeps or grows its test-function
    set — no test renamed, removed, or disabled — and adds no wildcard/glob."""
    import ast

    touched = [
        p for p in _git("diff", "--name-only", ENTRY, "--", "tests").split()
        if p.endswith(".py") and "n16_5_f_5_ppa_contract" not in p
    ]
    assert touched, "expected downstream guard reconciliations"
    for rel in touched:
        old_src = _git("show", f"{ENTRY}:{rel}")
        new_src = (ROOT / rel).read_text()
        old_defs = {
            n.name for n in ast.parse(old_src).body
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        }
        new_defs = {
            n.name for n in ast.parse(new_src).body
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        }
        assert old_defs <= new_defs, rel
        for banned in ("fnmatch", ".rglob(", "@pytest.mark.skip", "@pytest.mark.xfail"):
            assert new_src.count(banned) <= old_src.count(banned), (rel, banned)


def test_37_n16_5_not_closed_and_successor_iv_derived_not_begun() -> None:
    t = norm(PPA)
    assert "HPAC-PPA-REQ-103." in text(PPA)
    assert "N16-5-F-5-PPA-CONTRACT-IV" in text(PPA)
    assert "derived, NOT begun" in t or "derived but\n  **NOT begun**" in text(PPA) or "NOT begun" in t
    assert "N-16-5 remains **NOT CLOSED**" in text(PPA) or "N-16-5 NOT CLOSED" in t
    # the IV suite must not exist yet
    iv = ROOT / "tests" / (
        "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r"
        "_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1_1_1_1_1_1_n16_5_f_5_ppa_contract_iv.py"
    )
    assert not iv.exists()


def test_38_delta_table_and_v2_0_freeze_verdict_present() -> None:
    t = text(PPA)
    assert "## 21A. (v2.0) Delta table" in t
    assert "## 22. (v2.0) Freeze verdict" in t
    assert "**FROZEN (v2.0):**" in t
    assert "N-16-6 / N-16-7 remain **OPEN / UNTOUCHED** (N-16-7 strictly last)." in t


def test_39_phase_report_exists_and_states_the_verdict() -> None:
    assert REPORT.exists()
    r = norm(REPORT)
    assert "N16-5-F-5-PPA-CONTRACT" in text(REPORT)
    assert "HPAC-PPA-001 v1.0 -> v2.0" in r or "v1.0 → v2.0" in text(REPORT)
    assert "MAJOR" in text(REPORT)
    assert "N-16-5" in text(REPORT) and "NOT CLOSED" in text(REPORT)
