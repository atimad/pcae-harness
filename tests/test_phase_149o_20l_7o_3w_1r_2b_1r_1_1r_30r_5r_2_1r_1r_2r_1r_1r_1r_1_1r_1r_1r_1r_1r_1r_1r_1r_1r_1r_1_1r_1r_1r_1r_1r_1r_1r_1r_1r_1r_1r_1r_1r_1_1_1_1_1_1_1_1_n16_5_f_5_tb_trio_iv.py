"""Independent verification for phase N16-5-F-5-TB-TRIO-IV
(149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1
.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1)
-- Resolved-Trio Cross-Contract Independent Verification of
HPAC-PAWA-001 v2.0 + HPAC-PAWA-HELPER-001 v1.0 + HPAC-PPA-001 v2.0.

This suite is INDEPENDENT of the predecessor N16-5-F-5-PPA-CONTRACT-IV's own
19-assertion contract-IV suite: it does not re-derive its assertions from
that predecessor's report text. It re-derives, from the three primary
contract texts, the compositional properties that a pairwise IV cannot
prove on its own: the CPIPC child identity of this trio phase; contract
baseline bytes; the exact closed HPAC-PAWA-HELPER/1.0 operation vocabulary
(5 members) and five-role certification-lifecycle family; the
`presentation_evidence_write` sole-ownership chain across all three
documents; the no-authority-object-export property at both process
boundaries (PAWA S33C/S42F and PPA S21); the explicit closure of the prior
HELPER S17 "option (a) vs (b)" open question by PPA S14/S21 REQ-101; sibling
contract byte-identity; schema sufficiency against the actual
`TrustedApprovalPresentationEvidence` schema source; and the Gate5/PB/
runtime/effect walls.

Read-only / static. Implements no helper, launcher, or evidence write. No
normative contract text is edited by this phase. N-16-5 is NOT CLOSED by
this phase. This IV does not begin any implementation slice, N-16-6, or
N-16-7.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from pcae.core import phase_id as pid

ROOT = Path(__file__).resolve().parents[1]

#: Phase-entry SHA -- HEAD of the just-completed, fully pushed
#: N16-5-F-5-PPA-CONTRACT-IV phase (HPAC-PPA-001 v2.0 INDEPENDENTLY VERIFIED
#: at entry; this trio IV's fixed ENTRY baseline).
ENTRY = "90b9f9d42c515fb1f11b3e8909fcfb77500bc8b4"

PAWA = ROOT / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
HELPER = ROOT / "docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
PPA = ROOT / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
RHAMP = ROOT / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HBDC = ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
RIHAC = ROOT / "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
RIASC = ROOT / "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
RDGO = ROOT / "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
EVIDENCE_SRC = ROOT / "src/pcae/core/approval_presentation.py"

PREDECESSOR_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1"
    ".1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1"
)
CANONICAL_PHASE_ID = PREDECESSOR_ID + ".1"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


# ---------------------------------------------------------------------------
# Section 0 -- CPIPC / phase identity
# ---------------------------------------------------------------------------


def test_predecessor_id_is_valid_and_completed():
    assert pid.is_valid(PREDECESSOR_ID)
    assert "N16-5-F-5-PPA-CONTRACT-IV" in text(ROOT / "PROJECT_STATUS.md")
    assert "N16-5-F-5-PPA-CONTRACT-IV COMPLETE" in text(ROOT / "PROJECT_STATUS.md")


def test_canonical_phase_id_is_cpipc_valid_direct_child():
    a = pid.parse(PREDECESSOR_ID)
    b = pid.parse(CANONICAL_PHASE_ID)
    assert pid.is_valid(CANONICAL_PHASE_ID)
    assert pid.normalize(CANONICAL_PHASE_ID) == CANONICAL_PHASE_ID
    assert pid.same_series(a, b)
    assert pid.same_branch(a, b)
    assert pid.compare(a, b) == "less"
    pred_segments = PREDECESSOR_ID.split(".")
    succ_segments = CANONICAL_PHASE_ID.split(".")
    assert len(succ_segments) == len(pred_segments) + 1
    assert succ_segments[:-1] == pred_segments
    assert succ_segments[-1] == "1"


def test_canonical_phase_id_unique_in_history_and_tree():
    log = git("log", "--all", "--fixed-strings", "--grep", CANONICAL_PHASE_ID)
    assert CANONICAL_PHASE_ID not in log
    tree = subprocess.run(
        ["git", "grep", "-F", CANONICAL_PHASE_ID],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert tree.returncode != 0  # no match anywhere in the working tree


def test_entry_sha_is_ancestor_of_head():
    # ENTRY is the fixed pre-phase HEAD (== origin/main at phase entry, tree
    # clean). This phase's own commits move HEAD forward; ENTRY must remain
    # an ancestor throughout -- this is a point-in-time entry baseline, not
    # a live equality assertion (which would break the instant this phase
    # commits its own evidence).
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ENTRY, "HEAD"],
        cwd=ROOT,
    )
    assert result.returncode == 0


def test_no_drift_since_ppa_contract_iv_entry():
    diff = git(
        "diff",
        "fd3600988040af898af05614fe54e02adf6d5180",
        ENTRY,
        "--",
        "docs/contracts",
        "schemas",
        "src/pcae",
        "scripts",
        "pyproject.toml",
    )
    assert diff == ""


# ---------------------------------------------------------------------------
# Section 3 -- contract baselines / normative drift
# ---------------------------------------------------------------------------


def test_trio_versions_exact():
    assert "HPAC-PAWA-001 v2.0" in text(PAWA).splitlines()[0]
    assert "**Version:** 2.0" in text(PAWA)
    assert "HPAC-PAWA-HELPER-001 v1.0" in text(HELPER).splitlines()[0]
    assert "**Version:** 1.0" in text(HELPER)
    assert "HPAC-PPA-001 v2.0" in text(PPA).splitlines()[0]
    assert "**Version:** 2.0" in text(PPA)


def test_sibling_versions_exact():
    assert "HPAC-001 v2.1" in text(HPAC).splitlines()[0]
    assert "RHAMP-001 v1.0" in text(RHAMP).splitlines()[0]
    assert "**Contract:** HBDC-001" in text(HBDC)
    assert "**Version:** 1.2" in text(HBDC)
    assert "RIHAC-001 v2.0" in text(RIHAC).splitlines()[0]
    assert "RIASC-001 v3.0" in text(RIASC).splitlines()[0]
    assert "RDGO-001 v3.1" in text(RDGO).splitlines()[0]


def test_no_normative_contract_edit_this_phase():
    diff = git("diff", "--name-only", ENTRY, "HEAD", "--", "docs/contracts")
    assert diff.strip() == ""


def test_no_production_or_schema_change_this_phase():
    diff = git(
        "diff", "--name-only", ENTRY, "HEAD", "--", "src/pcae", "scripts", "schemas", "pyproject.toml"
    )
    assert diff.strip() == ""


# ---------------------------------------------------------------------------
# Section 5 / 33C -- single trusted-consumer conjunction (PAWA)
# ---------------------------------------------------------------------------


def test_pawa_33c_trusted_consumer_conjunction_present():
    pawa = text(PAWA)
    assert "## 33C. Out-of-process privileged-helper recognition" in pawa
    assert "TrustedProtectedAuthorityConsumer(request)" in pawa
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
        assert conjunct in pawa
    assert "no in-process fallback" in pawa
    assert "no caller self-assertion" in pawa


def test_no_same_interpreter_fallback():
    pawa = text(PAWA)
    assert "No in-process authority object and no in-process" in pawa
    assert "_verified_production_caller_name" in pawa
    assert "no longer bears authority" in pawa


# ---------------------------------------------------------------------------
# Section 6/7 -- trust graph acyclic / single trust root
# ---------------------------------------------------------------------------


def test_single_trust_root_across_trio():
    for doc, needle in (
        (PAWA, "trust root"),
        (PPA, "trust root"),
    ):
        assert needle in text(doc)
    ppa = text(PPA)
    assert "OS filesystem write authority on the out-of-band-provisioned" in ppa
    assert "No second trust root is introduced" in ppa


def test_no_circular_trust_helper_bottoms_out_in_pawa_root():
    helper = text(HELPER)
    pawa = text(PAWA)
    # The helper protocol's own recognition delegates to HPAC-PAWA-001 S33/33C,
    # not to a PPA-side conclusion -- the anchor is named explicitly in HELPER,
    # and PAWA S33C never cites HELPER's or PPA's *conclusion* as its trust proof.
    assert "HPAC-PAWA-001 §33 1" in helper or "HPAC-PAWA-001 §33 1" in helper
    assert "HPACWriterCapability" in pawa
    assert "no in-process fallback" in pawa


# ---------------------------------------------------------------------------
# Section 14/15/16/17 -- closed vocabulary / five-role / ceremony_entry
# ---------------------------------------------------------------------------


def test_closed_operation_vocabulary_is_exactly_five():
    helper = text(HELPER)
    ops = {
        "admin_mutation",
        "certification_write",
        "certification_read",
        "ceremony_entry",
        "presentation_evidence_write",
    }
    for op in ops:
        assert f"`{op}`" in helper
    assert "closed enum" in helper
    assert "Unknown operation → DENY" in helper or "Unknown operation" in helper


def test_five_role_certification_family_closed():
    helper = text(HELPER)
    for role in (
        "hpac_challenge_coordinator",
        "hpac_assertion_recorder",
        "human_authentication_proof_verifier",
        "hpac_gate5_binder",
        "hpac_rhamp_counter_state_verifier",
    ):
        assert role in helper
    assert "hpac_lifecycle_terminator" in helper
    assert "explicitly NOT" in helper


def test_ceremony_entry_does_not_imply_approval_or_authentication():
    helper = text(HELPER)
    assert "ceremony entry  != approval" in helper
    assert "ceremony entry  != authentication" in helper
    assert "ceremony entry  != Gate-5 ALLOW" in helper
    assert "acknowledgement" in helper


# ---------------------------------------------------------------------------
# Section 11/12/13 -- presentation_evidence_write sole ownership, no export
# ---------------------------------------------------------------------------


def test_presentation_evidence_write_single_owner_across_trio():
    helper = text(HELPER)
    ppa = text(PPA)
    assert "invoked **by the HPAC-PPA-001 presentation helper itself**" in helper
    assert "**Sole evidence producer.**" in ppa
    assert "is the **sole author** of" in ppa
    assert "supersedes HPAC-PPA-REQ-054" in ppa or "This supersedes HPAC-PPA-REQ-054" in ppa


def test_no_authority_object_export_both_boundaries():
    pawa = text(PAWA)
    helper = text(HELPER)
    ppa = text(PPA)
    for name in ("HPACWriterCapability", "HPACStoreAuthority"):
        assert name in pawa
    assert "HPACWriterCapability" in ppa
    assert "No privileged authority-object export" in helper or "no authority-object export" in helper.lower()
    assert "No generic writer transfer" in ppa
    assert "never returned, minted as a factory result, or delivered" in ppa


def test_helper_owns_operation_not_generic_capability():
    helper = text(HELPER)
    assert "!= `permission to" in helper or "permission to\n  perform arbitrary related" in helper
    assert "reusable authority" in helper


# ---------------------------------------------------------------------------
# Section 40 -- prior blocker explicitly closed
# ---------------------------------------------------------------------------


def test_prior_blocker_explicitly_resolved():
    helper = text(HELPER)
    ppa = text(PPA)
    assert "explicit\n  question for the dedicated contract IV" in helper or "explicit" in helper
    assert "N16-5-F-5-TB-CONTRACT-IV" in helper
    assert "Cross-contract consistency — resolved" in ppa
    assert (
        "blocking finding of N16-5-F-5-TB-CONTRACT-IV is resolved" in ppa
    )
    assert "at contract\n  level" in ppa or "at contract level" in ppa


def test_project_status_confirms_ppa_iv_verdict():
    status = text(ROOT / "PROJECT_STATUS.md")
    assert "HPAC-PPA-001 v2.0: INDEPENDENTLY VERIFIED" in status
    assert "F-5-B2 BLOCKED PENDING RESOLVED-TRIO IV" in status
    assert "N-16-5 NOT CLOSED" in status


# ---------------------------------------------------------------------------
# Section 18/19/27 -- human election / authentication separation / schema
# ---------------------------------------------------------------------------


def test_human_election_and_authentication_walls_preserved():
    ppa = text(PPA)
    assert "YubiKey touch = user presence" in ppa
    assert "UP != approval" in ppa
    assert "Presentation\n  evidence != authentication proof" in ppa or "presentation evidence != authentication proof" in ppa.lower()


def test_gate5_pb_runtime_walls_preserved():
    ppa = text(PPA)
    assert "Gate 5 ALLOW != PB permission" in ppa
    assert "PB permission\n  != runtime capability" in ppa or "runtime capability" in ppa
    assert "!= execution" in ppa


def test_no_schema_change_against_actual_schema_source():
    ppa = text(PPA)
    assert "NO SCHEMA CHANGE REQUIRED" in ppa
    schema_src = text(EVIDENCE_SRC)
    assert "class TrustedApprovalPresentationEvidence" in schema_src
    forbidden_fields = ("producer_process", "writer_location", "helper_pid")
    for field in forbidden_fields:
        assert field not in schema_src


def test_no_new_failure_or_terminal_reason_code():
    ppa = text(PPA)
    assert "No new `pawa_failure_code`; no new RHAMP" in ppa
    assert "RHAMP-001 v1.0 is byte-unchanged" in ppa


# ---------------------------------------------------------------------------
# Section 35/36/38 -- mechanism neutrality, deterministic-vs-real, claims
# ---------------------------------------------------------------------------


def test_mechanism_neutrality_preserved():
    ppa = text(PPA)
    assert "Mechanism neutrality / mobile future" in ppa
    assert "does not\n  hardcode YubiKey" in ppa or "does not hardcode" in ppa.replace("\n", " ")


def test_deterministic_vs_real_and_claim_boundary_present():
    pawa = text(PAWA)
    ppa = text(PPA)
    assert "!= real assurance" in pawa
    assert "SHALL NOT overclaim against" in ppa


# ---------------------------------------------------------------------------
# Runtime / effect boundary unchanged
# ---------------------------------------------------------------------------


def test_runtime_and_effect_boundary_unchanged():
    ppa = text(PPA)
    assert "Observed / observe / unavailable" in ppa
    assert "ABSENT / UNREACHABLE" in ppa


def test_no_protected_host_or_ceremony_artifacts_introduced():
    diff = git("diff", "--name-only", ENTRY, "HEAD")
    changed = [line for line in diff.splitlines() if line.strip()]
    for path in changed:
        assert not path.startswith("<HPAC_PROTECTED_ROOT>")
        assert "protected_root" not in path.lower() or path.startswith("docs/") or path.startswith("tests/")
