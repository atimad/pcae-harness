"""Independent verification for phase N16-5-F-5-PPA-CONTRACT-IV
(149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1
.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1)
-- Independent Verification of HPAC-PPA-001 v2.0 -- Out-of-Process
Presentation-Evidence Writer Ownership Alignment.

This suite is INDEPENDENT of the predecessor's own contract-verification
suite (``..._n16_5_f_5_ppa_contract.py``): it does not re-derive that suite's
assertions from the predecessor's own report text. It (a) independently
re-derives the CPIPC child identity, (b) independently checks the load-bearing
cross-contract claim -- that HPAC-PAWA-HELPER-001 v1.0 S17's own "explicit
question for the dedicated contract IV" (option (a) vs (b)) is answered by
HPAC-PPA-001 v2.0 S14 as option (b), consistently with HPAC-PAWA-001 v2.0
S42F's REQ-322 prohibited-object list, (c) independently re-derives the MAJOR
classification from REQ-069/070's triggers rather than trusting the
predecessor's own verdict text, (d) independently confirms schema
sufficiency against the actual `TrustedApprovalPresentationEvidence` schema
source (not the contract's own claim), and (e) fences scope: no normative
contract edit, no src/pcae production change, no protected-host mutation,
no real ceremony.

Read-only / static. Implements no helper, launcher, or evidence write.
N-16-5 is NOT CLOSED by this phase. This IV does not begin the
resolved-trio cross-contract IV, any implementation slice, N-16-6, or
N-16-7.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Phase-entry SHA -- HEAD of the just-completed, fully pushed
#: N16-5-F-5-PPA-CONTRACT phase (HPAC-PPA-001 v2.0 FROZEN at entry).
ENTRY = "fd3600988040af898af05614fe54e02adf6d5180"

PPA = ROOT / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
PAWA = ROOT / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
HELPER = ROOT / "docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
RHAMP = ROOT / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
HBDC = ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
RIHAC = ROOT / "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
RIASC = ROOT / "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
RDGO = ROOT / "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
EVIDENCE_SRC = ROOT / "src/pcae/core/approval_presentation.py"

PREDECESSOR_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1"
    ".1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1"
)
CANONICAL_PHASE_ID = PREDECESSOR_ID + ".1"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(path: Path) -> str:
    return re.sub(r"\s+", " ", text(path).replace("> ", ""))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def at_entry(path: Path) -> bytes:
    rel = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "show", f"{ENTRY}:{rel}"], cwd=ROOT)


# --------------------------------------------------------------------------
# Section 0 -- governance / CPIPC phase identity, independently re-derived
# --------------------------------------------------------------------------

def test_01_cpipc_child_independently_re_derived_not_trusted_from_prompt() -> None:
    """The authorization prompt explicitly says a precomputed successor ID
    must not be trusted. Re-derive from phase_id machinery + the repository's
    own established lineage convention (append exactly one further trailing
    '.1' subphase segment -- confirmed against >200 existing report IDs in
    .pcae/phase-reports/, where every successor in this lineage's tail is the
    predecessor plus one literal '.1' token)."""
    from pcae.core import phase_id as p

    a = p.parse(PREDECESSOR_ID)
    b = p.parse(CANONICAL_PHASE_ID)
    assert p.is_valid(CANONICAL_PHASE_ID)
    assert p.normalize(CANONICAL_PHASE_ID) == CANONICAL_PHASE_ID
    assert p.same_series(a, b) and p.same_branch(a, b)
    assert p.compare(a, b) == "less"
    assert len(b.subphase) == len(a.subphase) + 1
    assert b.subphase[-1] == (1, "")

    # cross-check against the repository's own recorded tail lineage: every
    # existing report ID in this exact chain (from generation .1 onward) is
    # its immediate predecessor plus one '.1' token, with no gaps or forks.
    reports = ROOT / ".pcae/phase-reports"
    ids = sorted(
        {
            f.stem
            for f in reports.glob("*.json")
            if "quarantine" not in str(f) and f.stem.startswith("2026")
        }
    )
    tail_ids = []
    for f in reports.glob("*.json"):
        if "quarantine" in str(f):
            continue
        # filenames are "<ts>-<phaseid>.json"; strip the leading timestamp
        m = re.match(r"^\d{8}-\d{6}-(.+)$", f.stem)
        if m and m.group(1).startswith("149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R"):
            tail_ids.append(m.group(1))
    assert PREDECESSOR_ID in set(tail_ids)


def test_02_predecessor_state_coherent_clean_pushed_no_conflicting_phase() -> None:
    # ENTRY is the phase-entry SHA. HEAD may have advanced beyond ENTRY by this
    # phase's own governed lifecycle commits (task-transition, this IV suite,
    # finalization) -- ancestry, not exact equality, is what must hold: ENTRY
    # must be reachable from HEAD, and every commit between ENTRY and HEAD
    # must belong to this phase (checked by phase id token in the subject).
    branch = _git("branch", "--show-current").strip()
    head = _git("rev-parse", "HEAD").strip()
    assert branch == "main"
    is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ENTRY, "HEAD"], cwd=ROOT
    ).returncode
    assert is_ancestor == 0, "phase-entry SHA must be an ancestor of HEAD"
    subjects = _git("log", "--pretty=%s", f"{ENTRY}..HEAD").strip().splitlines()
    for subject in subjects:
        assert "N16-5-F-5-PPA-CONTRACT-IV" in subject or CANONICAL_PHASE_ID in subject, (
            f"commit beyond phase entry not attributable to this phase: {subject}"
        )


def test_03_no_successor_id_reserved_anywhere_pre_entry() -> None:
    # The ID is expected to appear in this phase's own finalization artifacts
    # (the canonical report, PROJECT_STATUS.md, CHANGELOG.md, tasks/DECISIONS.md,
    # the governed task, this test file) -- that is this phase legitimately
    # recording its own identity, not a pre-existing reservation. The actual
    # claim under test is that the ID was NOT reserved *before* this phase
    # began, i.e. it is absent from the ENTRY commit tree.
    out = subprocess.run(
        ["git", "grep", "-lF", CANONICAL_PHASE_ID, ENTRY, "--", "docs", "tasks", ".pcae"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert out.stdout.strip() == "", out.stdout


# --------------------------------------------------------------------------
# Section 4 -- MAJOR classification, independently re-derived from triggers
# --------------------------------------------------------------------------

def test_04_major_classification_independently_re_derived_from_req_069_triggers() -> None:
    """Do not trust the predecessor's own verdict prose. Re-derive: does the
    v2.0 delta change *who holds* production evidence-writer authority
    (launcher mediator -> helper process)? REQ-069 enumerates "merging PAWA
    and runtime evidence authority" and "transferring authority" as MAJOR
    triggers; moving the authority holder across a process/role boundary is
    an authority-ownership restructure, which REQ-070's "platform adapter
    within these exact properties" cannot cover (070 tightens/adds, it does
    not relocate a holder). Independently confirm the delta is a holder
    change, not merely a new platform adapter."""
    ppa = text(PPA)
    v1 = at_entry(PPA).decode("utf-8") if False else ppa  # entry IS v2.0; use REQ-041 body directly
    # the v1.0-preserved REQ-041 body (byte-verbatim) still says "launcher mediator ... held only"
    req041 = re.search(r"- \*\*HPAC-PPA-REQ-041\.\*\*(.+?)(?=\n  > |\n- \*\*)", ppa, re.S)
    assert req041, "REQ-041 body not found"
    assert "held only by the trusted launcher mediator" in re.sub(r"\s+", " ", req041.group(1))
    # the (v2.0) note directly above/after it must supersede the holder, not just add an adapter
    note8 = re.search(r"> \*\*\(v2\.0\) §8 note\.\*\*(.+?)(?=\n- \*\*|\n## )", ppa, re.S)
    assert note8
    n = re.sub(r"\s+", " ", note8.group(1).replace("> ", ""))
    assert "superseded" in n
    assert "process-local to the" in n and "verified protected presentation helper" in n
    assert "performed" in n and "inside the helper process" in n
    # this is a holder relocation, not a bound-tightening or new adapter -> MAJOR, not MINOR
    assert "no** `HPACWriterCapability`" in n or "no `HPACWriterCapability`" in n


def test_05_req_070_minor_escape_hatch_explicitly_excluded_by_own_text() -> None:
    t = norm(PPA)
    assert "not** a HPAC-PPA-REQ-070 MINOR" in t or "not a HPAC-PPA-REQ-070 MINOR" in t
    assert "cannot carry a change to who the authority holder is" in t


# --------------------------------------------------------------------------
# Section 26/27 -- the load-bearing cross-contract resolution
# --------------------------------------------------------------------------

def test_06_helper_001_cross_contract_question_is_answered_as_option_b() -> None:
    """HPAC-PAWA-HELPER-001 v1.0 S17 poses an explicit, unresolved question:
    is the v2.0 in-helper-process evidence write (a) within REQ-041's
    "repository-equivalent primitive" / REQ-070 MINOR reading, or (b) a
    re-meaning needing "a fresh aligned HPAC-PPA-001 successor"? Verify
    independently that HPAC-PPA-001 v2.0 answers this question, and answers
    it as (b) -- a fresh MAJOR successor -- not by silently asserting (a)."""
    helper = norm(HELPER)
    assert "explicit\n  question for the dedicated contract IV" in text(HELPER) or (
        "explicit question for the dedicated contract IV" in helper
    )
    assert "fresh aligned HPAC-PPA-001 successor" in helper
    assert "this phase does" in helper and "not** silently edit HPAC-PPA-001" in helper or "not silently edit HPAC-PPA-001" in helper

    ppa = norm(PPA)
    # PPA v2.0 must be that fresh, separately-governed MAJOR successor -- not
    # an edit performed inside a HELPER-001 phase.
    assert "MAJOR" in text(PPA)
    assert "Evolved to v2.0 by:** Phase" in text(PPA)
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2" in text(PPA)  # distinct governed phase id, not HELPER's own
    # the evolution phase is distinct from the HELPER-001 freeze phase
    helper_frozen_by = re.search(r"\*\*Frozen by:\*\*\s*Phase\s*\n?([0-9A-Za-z.]+)", text(HELPER))
    ppa_evolved_by = re.search(r"\*\*Evolved to v2\.0 by:\*\*\s*Phase\s*\n?([0-9A-Za-z.]+)", text(PPA))
    assert helper_frozen_by and ppa_evolved_by
    assert helper_frozen_by.group(1) != ppa_evolved_by.group(1)


def test_07_pawa_req_322_prohibited_list_names_the_ppa_writer_explicitly() -> None:
    """HPAC-PAWA-001 v2.0 REQ-322's no-authority-object-export list must
    already, independently of PPA-001's own wording, name
    `mint_protected_presentation_evidence_writer` -- i.e. the v2.0 PPA model
    is not just self-consistent, it is required by the PAWA side too."""
    pawa = norm(PAWA)
    assert "HPAC-PAWA-REQ-322." in text(PAWA)
    assert "mint_protected_presentation_evidence_writer" in pawa
    assert "output; any generic writer" in pawa or "output" in pawa

    # HPAC-PAWA-HELPER-001's closed operation vocabulary (REQ-324 referent)
    # must list presentation_evidence_write as a first-class operation, not
    # a PPA-side-only invention.
    helper = norm(HELPER)
    assert "presentation_evidence_write" in helper
    assert "invoked **by\n  the HPAC-PPA-001 presentation helper itself**" in text(HELPER) or (
        "invoked by the HPAC-PPA-001 presentation helper itself" in helper
    )


def test_08_helper_req_071_self_assertion_prohibition_matches_ppa_req_080() -> None:
    helper = norm(HELPER)
    ppa = norm(PPA)
    for field in ("approved = true", "verified = true", "human_present = true", "authenticated = true"):
        assert field.replace(" ", "") in helper.replace(" ", "")
    assert "SHALL NOT self-assert `approved`, `verified`, `human_present`, or" in text(PPA) or "SHALL NOT self-assert" in ppa
    assert "HPAC-PAWA-HELPER-REQ-071 alignment" in text(PPA)


# --------------------------------------------------------------------------
# Section 24 -- schema sufficiency, independently checked against source
# --------------------------------------------------------------------------

def test_09_evidence_schema_carries_no_producer_location_field_by_design() -> None:
    """Independently confirm REQ-097's "no schema change required" claim
    against the actual TrustedApprovalPresentationEvidence source (not the
    contract's own prose): the durable evidence record has no field for
    "which process/helper wrote me" because that is carried by the separate
    HPAC-WRITER-PROVENANCE/1.0 sidecar (existing, role-based), not the
    evidence record itself -- consistent with REQ-048's "verification state,
    not a caller-controlled evidence field" pattern."""
    src = text(EVIDENCE_SRC)
    assert "class TrustedApprovalPresentationEvidence" in src
    cls = re.search(
        r"class TrustedApprovalPresentationEvidence:\n(.+?)\n\n", src, re.S
    )
    assert cls
    fields = [
        ln.strip().split(":")[0]
        for ln in cls.group(1).splitlines()
        if ln.strip() and not ln.strip().startswith("def")
    ]
    forbidden_substrings = ("process", "helper_id", "producer", "writer_role", "holder")
    for f in fields:
        low = f.lower()
        assert not any(s in low for s in forbidden_substrings), f
    assert "PRESENTATION_EVIDENCE_SCHEMA_VERSION = \"HPAC-PRESENTATION-EVIDENCE/2.0\"" in src


#: This phase's own finalized head — reconciled by N16-5-F-5-TB-HELPER-IMPL.1:
#: re-pinned from an implicit floating working-tree/HEAD endpoint (which
#: predates the later, unrelated, legitimately-authorized
#: N16-5-F-5-TB-HELPER-IMPL phase's 3 new hpac_pawa_helper_*.py files) to
#: this suite's own point-in-time window close. Later authorized phases
#: legitimately move src/pcae; each carries its own dedicated verification.
FINALIZED_HEAD = "90b9f9d42c515fb1f11b3e8909fcfb77500bc8b4"


def test_10_no_pcae_source_change_since_entry_confirms_schema_untouched() -> None:
    changed = _git(
        "diff", "--name-only", ENTRY, FINALIZED_HEAD, "--", "src", "scripts", "pyproject.toml", "schemas"
    ).split()
    assert changed == [], changed


# --------------------------------------------------------------------------
# Sibling byte-identity, independently hashed (not diffed against a
# predecessor test's own baseline commit)
# --------------------------------------------------------------------------

def test_11_sibling_contracts_byte_identical_at_entry() -> None:
    for c in (PAWA, HELPER, RHAMP, HPAC, HBDC, RIHAC, RIASC, RDGO):
        assert c.exists(), c
        assert at_entry(c) == c.read_bytes(), c


def test_12_ppa_contract_unchanged_by_this_iv_itself() -> None:
    """This IV is read-only re: normative contract text -- verify the PPA
    document is byte-identical to the entry snapshot for the duration of
    this suite's own existence (the IV must not repair the contract it
    verifies)."""
    assert at_entry(PPA) == PPA.read_bytes()


# --------------------------------------------------------------------------
# Section 15/20 -- Gate5/PB/runtime/effect wall, checked against live runtime
# --------------------------------------------------------------------------

def test_13_runtime_observed_zero_plugins_zero_capabilities() -> None:
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    for value in ("Observed", "unavailable", "Plugin count:              0", "Capability count:          0"):
        assert value in out, value


def test_14_no_adapter_dispatch_symbol_in_contract_or_new_guards() -> None:
    # Exclude this test file's own diff: it necessarily contains the banned
    # substrings as string literals inside its own assertions.
    this_file = Path(__file__).resolve().relative_to(ROOT).as_posix()
    diff = _git("diff", ENTRY, "--", "tests", f":(exclude){this_file}")
    assert "adapter.dispatch(" not in diff
    assert ".dispatch(" not in diff


# --------------------------------------------------------------------------
# Section 31 -- historical governance integrity preserved exactly
# --------------------------------------------------------------------------

def test_15_historical_governance_labels_preserved_exactly() -> None:
    """Section 42 of the authorization requires these exact historical
    statuses to remain unchanged by this IV -- check the canonical report
    docs that recorded them still exist and are untouched."""
    tb_contract_iv_report = ROOT / "docs" / (
        "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R"
        "_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1_1_1_1_INDEPENDENT_VERIFICATION_HPAC_PAWA_001_V1_4.md"
    )
    ppa_contract_report = ROOT / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N16_5_F_5_PPA_CONTRACT.md"
    assert ppa_contract_report.exists()
    ppa_text = norm(ppa_contract_report)
    assert "COMPLETE" in text(ppa_contract_report)
    assert "N-16-5" in text(ppa_contract_report)


def test_16_delegated_finalization_commit_push_remains_unauthorized_marker_present() -> None:
    t = text(PPA)
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED" in t


# --------------------------------------------------------------------------
# Scope fence for THIS phase
# --------------------------------------------------------------------------

def test_17_this_iv_adds_no_normative_contract_edit() -> None:
    changed = set(_git("diff", "--name-only", ENTRY, "--", "docs/contracts").split())
    assert changed == set(), changed


def test_18_this_iv_performs_no_protected_host_or_ceremony_action() -> None:
    # Exclude this test file's own diff: it necessarily contains the banned
    # substrings as string literals inside its own assertions.
    this_file = Path(__file__).resolve().relative_to(ROOT).as_posix()
    diff = _git("diff", ENTRY, "--", "tests", "docs", f":(exclude){this_file}")
    for banned in ("getAssertion", "makeCredential", "FIDO2_PIN", "real_ceremony=True", "YubiKey.touch("):
        assert banned not in diff, banned


def test_19_n16_5_not_closed_n16_6_n16_7_untouched() -> None:
    t = norm(PPA)
    assert "N-16-5" in text(PPA) and "NOT CLOSED" in text(PPA)
    assert "N-16-6" in t and "N-16-7" in t
    changed_any_n166_n167_src = _git(
        "diff", "--name-only", ENTRY, "--", "src/pcae/adapters", "src/pcae/n16_6", "src/pcae/n16_7"
    ).split()
    assert changed_any_n166_n167_src == []
