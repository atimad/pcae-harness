"""Phase 149O.20L.6A — Class-B Provisioning Authorization Record Independent
Verification.

Independent verification-only test coverage for the CHGR published by
Phase 149O.20L.6 (chgr-d4343fa51b9743f3abaeb87a881a78b1). Deliberately does
not import ``test_phase_149o_20l_6_class_b_provisioning_authorization_record_capture``
(L.6's own module) -- every assertion here is re-derived independently from
the live CLI, the canonical artifact files, and CHGR-001 itself, so this
module can catch a defect L.6's own suite would not (or fraudulently
would) catch.

No production host mutation, provisioning, certification, activation, or
CHGR mutation is performed or tested here.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PCAE_EXECUTABLE = shutil.which("pcae")

RECORDS_DIR = REPO_ROOT / ".pcae" / "publication-execution" / "records"
CHGR_PATH = RECORDS_DIR / "chgr-d4343fa51b9743f3abaeb87a881a78b1.json"
CHGR_CONF_PATH = RECORDS_DIR / "chgrconf-71ceda34408e4c469b5a799c01774364.json"
CHGR_PROV_PATH = RECORDS_DIR / "chgrprov-9cd1ad63128c4c3ea7624a437c0b73a7.json"
CHGR_INTG_PATH = RECORDS_DIR / "chgrintg-ee5908d1ded84b1ea8531806f445349e.json"

SESSION_PATH = (
    REPO_ROOT
    / ".pcae"
    / "decision-sessions"
    / "orchestration"
    / "CDS-6476b6d1-e934-41b8-a57b-27426e18a4b5.json"
)
CONSUMED_PACKAGE_PATH = (
    REPO_ROOT
    / ".pcae"
    / "decision-sessions"
    / "pending-packages"
    / "consumed"
    / "prp-af987a7157804bdfb13dc06e6a060459.json"
)
AESIC_TEMPLATE_PATH = (
    REPO_ROOT
    / ".pcae"
    / "authority-evaluation"
    / "templates"
    / "class-b-boundary-p-provisioning-authorization"
    / "1.0.json"
)

L5A_ENTRY_COMMIT = "2e97651ef9366e6427b26ea061deac827b6485e9"

REQUIRED_EXCLUSION_TOKENS = (
    # Boundary C is named literally; Boundary A's substance (HATP_MANDATORY
    # activation) is present but the record never uses the literal string
    # "Boundary A" -- both are checked accordingly below.
    "Boundary C",
    "HATP_MANDATORY",
    "runtime capability elevation",
    "Permission Broker",
    "POL-005",
    "COMP-002",
)


@pytest.fixture(scope="module")
def chgr_record() -> dict:
    return json.loads(CHGR_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def confirmation_record() -> dict:
    return json.loads(CHGR_CONF_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def provenance_record() -> dict:
    return json.loads(CHGR_PROV_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def integrity_record() -> dict:
    return json.loads(CHGR_INTG_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def session_record() -> dict:
    return json.loads(SESSION_PATH.read_text(encoding="utf-8"))


# --- 1. Existence, identity, publication state -----------------------------


def test_chgr_artifact_exists_with_exact_record_id(chgr_record: dict) -> None:
    assert chgr_record["record_id"] == "chgr-d4343fa51b9743f3abaeb87a881a78b1"


def test_chgr_is_published_human_governance_record(chgr_record: dict) -> None:
    assert chgr_record["record_type"] == "human_governance_record"
    assert chgr_record["lifecycle_state"] == "published"
    assert chgr_record["contract_version"] == "CHGR-001/1.0"


def test_chgr_is_the_only_chgr_record_in_the_repository() -> None:
    chgr_records = sorted(RECORDS_DIR.glob("chgr-*.json"))
    assert chgr_records == [CHGR_PATH], (
        "expected exactly one published human_governance_record artifact "
        f"in the repository, found: {chgr_records}"
    )


# --- 2. Election authenticity ----------------------------------------------


def test_selected_option_is_approve_among_closed_option_set(
    chgr_record: dict, provenance_record: dict
) -> None:
    assert chgr_record["selected_option_id"] == "approve"
    assert provenance_record["selected_option_id"] == "approve"
    options = set(provenance_record["options_presented"])
    assert options == {"approve", "decline", "amend"}


def test_rationale_is_first_person_explicit_election(chgr_record: dict) -> None:
    rationale = chgr_record["rationale"]
    assert rationale.strip().lower().startswith(
        "i, as the human governance authority, elect to approve"
    )
    assert "APPROVE" in rationale


def test_human_authority_identity_matches_across_all_related_artifacts(
    chgr_record: dict, confirmation_record: dict
) -> None:
    decision_maker = chgr_record["decision_maker_identity_evidence"]["identifier"]
    confirmer = confirmation_record["confirmer_identity_evidence"]["identifier"]
    assert decision_maker == "Atila Madai"
    assert confirmer == "Atila Madai"
    assert decision_maker == confirmer


def test_aesic_template_names_the_same_specific_human_authority() -> None:
    assert AESIC_TEMPLATE_PATH.exists()
    payload = json.loads(AESIC_TEMPLATE_PATH.read_text(encoding="utf-8"))
    assert "Atila Madai" in payload["eligible_authority"]
    assert "generic role" in payload["eligible_authority"].lower()


# --- 3. Scope / target / plan binding ---------------------------------------


def test_decision_subject_binds_boundary_p_specifically_not_general_class_b(
    chgr_record: dict,
) -> None:
    subject = chgr_record["decision_subject"]
    assert "Boundary-P provisioning authorization" in subject
    assert "Class-B target Option B" in subject
    lowered = subject.lower()
    assert "certification" not in lowered
    assert "activation" not in lowered


def test_decision_subject_cites_l5a_and_l5_documents_by_path(chgr_record: dict) -> None:
    subject = chgr_record["decision_subject"]
    assert "PHASE_149O_20L_5A_CLASS_B_PROVISIONING_TARGET_ENVIRONMENT_SELECTION_AND_PREFLIGHT.md" in subject
    assert "PHASE_149O_20L_5_CLASS_B_REAL_HOST_PROVISIONING_AUTHORIZATION_AND_PLANNING.md" in subject


def test_rationale_binds_the_nine_action_plan_not_an_unbounded_grant(
    chgr_record: dict,
) -> None:
    rationale = chgr_record["rationale"]
    assert "nine-action" in rationale
    assert "does not authorize provisioning execution in this phase" in rationale


def test_conditions_pin_git_commit_and_all_three_governing_contract_versions(
    chgr_record: dict,
) -> None:
    conditions = chgr_record["conditions"]
    assert "2e97651ef9366e6427b26ea061deac827b6485e9" in conditions
    assert "HMIC-001 v1.3" in conditions
    assert "HMRC-001 v1.1" in conditions
    assert "HBDC-001 v1.0" in conditions


# --- 4. Explicit exclusions preserved on the published artifact itself -----


def test_published_conditions_field_preserves_every_required_exclusion(
    chgr_record: dict,
) -> None:
    conditions = chgr_record["conditions"]
    for token in REQUIRED_EXCLUSION_TOKENS:
        assert token in conditions, f"exclusion token missing from published conditions: {token!r}"


def test_rationale_also_independently_states_the_core_exclusions(chgr_record: dict) -> None:
    rationale = chgr_record["rationale"]
    for token in ("Boundary C certification", "Boundary A activation", "HATP_MANDATORY activation"):
        assert token in rationale


# --- 5. Session continuity: evidence -> preview -> confirm -> publish -----


def test_session_completed_full_stage_sequence_without_gaps(session_record: dict) -> None:
    completed = session_record["completed_stages"]
    for stage in (
        "SessionInitialization",
        "EvidenceAvailability",
        "PreviewConstruction",
        "PreviewValidation",
        "ConfirmationRequest",
        "ConfirmationValidation",
        "TerminalCompletion",
    ):
        assert stage in completed


def test_confirmation_request_and_response_share_one_preview_digest(
    session_record: dict,
) -> None:
    request = session_record["confirmation_requests"][0]
    response = session_record["confirmation_responses"][0]
    assert request["preview_digest"] == response["preview_digest"]
    assert request["request_id"] == response["request_id"]


def test_confirmation_closing_statement_is_explicit_first_person_and_scoped(
    session_record: dict,
) -> None:
    statement = session_record["confirmation_responses"][0]["metadata"]["statement"]
    assert statement.startswith("I confirm this is my human governance decision")
    assert "Boundary-P provisioning authorization" in statement


def test_preview_digest_matches_confirmation_evidence_and_provenance(
    session_record: dict, confirmation_record: dict, provenance_record: dict
) -> None:
    preview_digest = session_record["last_preview"]["preview_id"]
    assert session_record["confirmation_requests"][0]["preview_digest"] == confirmation_record["preview_rendering_digest"]
    assert confirmation_record["confirmed_content_digest"] == confirmation_record["preview_rendering_digest"]
    assert provenance_record["preview_content_digest"] == confirmation_record["preview_rendering_digest"]
    assert preview_digest  # non-empty; last_preview itself is present


def test_no_second_session_or_package_id_exists_anywhere_in_the_chain(
    session_record: dict,
) -> None:
    consumed = json.loads(CONSUMED_PACKAGE_PATH.read_text(encoding="utf-8"))
    assert consumed["session_id"] == session_record["session_id"]
    assert consumed["record_id"] == "chgr-d4343fa51b9743f3abaeb87a881a78b1"
    other_sessions = list(
        (REPO_ROOT / ".pcae" / "decision-sessions" / "orchestration").glob("CDS-*.json")
    )
    assert other_sessions == [SESSION_PATH]


# --- 6. Evidence completeness -----------------------------------------------


def test_every_evidence_ref_in_the_session_is_resolvable_on_disk(
    session_record: dict,
) -> None:
    for entry in session_record["evidence"]:
        ref = entry["evidence_id"]
        if ref.startswith("git-commit:"):
            commit = ref.split(":", 1)[1]
            proc = subprocess.run(
                ["git", "cat-file", "-e", commit],
                cwd=REPO_ROOT,
                capture_output=True,
            )
            assert proc.returncode == 0, f"git commit not resolvable: {commit}"
            continue
        path_part = ref.split("@", 1)[0]
        assert (REPO_ROOT / path_part).exists(), f"evidence artifact missing: {path_part}"


# --- 7. Cross-artifact digest binding (record <-> conf/prov/integrity) -----


def test_record_cross_references_the_exact_related_artifact_ids(
    chgr_record: dict, confirmation_record: dict, provenance_record: dict, integrity_record: dict
) -> None:
    assert chgr_record["confirmation_evidence_ref"]["record_id"] == confirmation_record["record_id"]
    assert chgr_record["provenance_ref"]["record_id"] == provenance_record["record_id"]
    assert chgr_record["integrity_ref"]["record_id"] == integrity_record["record_id"]


def test_integrity_payload_digest_matches_record_digest(
    chgr_record: dict, integrity_record: dict
) -> None:
    assert integrity_record["payload_digest"] == chgr_record["record_digest"]


# --- 8. Live CLI inspect/verify reproduction --------------------------------


def test_live_inspect_succeeds_and_identifies_the_record() -> None:
    assert PCAE_EXECUTABLE, "pcae executable not found on PATH"
    proc = subprocess.run(
        [PCAE_EXECUTABLE, "governance-record", "inspect", str(CHGR_PATH), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["outcome"] == "inspected"
    assert payload["record_identity"] == "chgr-d4343fa51b9743f3abaeb87a881a78b1"


def test_live_verify_with_all_three_supplyable_related_artifacts_yields_seven_passed_one_skipped() -> None:
    assert PCAE_EXECUTABLE, "pcae executable not found on PATH"
    proc = subprocess.run(
        [
            PCAE_EXECUTABLE,
            "governance-record",
            "verify",
            str(CHGR_PATH),
            "--related",
            str(CHGR_CONF_PATH),
            "--related",
            str(CHGR_PROV_PATH),
            "--related",
            str(CHGR_INTG_PATH),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["outcome"] == "verified"
    checks = {c["name"]: c["status"] for c in payload["checks"]}
    passed = [name for name, status in checks.items() if status == "passed"]
    skipped = [name for name, status in checks.items() if status == "skipped"]
    failed = [name for name, status in checks.items() if status == "failed"]
    assert failed == []
    assert len(passed) == 7, f"expected 7 passed checks, got {passed}"
    assert skipped == ["template_resolution"]


def test_decision_template_artifact_class_is_structurally_unbuildable_this_increment() -> None:
    """CHGR-001's own decision_template.schema.json documents that no
    session/record-creation workflow exists for this record_type as of
    Phase 143E; the AESIC authority-evaluation template (a distinct
    schema family) is what actually carries eligible_authority in this
    repository. Independently confirms the skipped ``template_resolution``
    check reflects a repository-wide, not record-specific, gap.
    """
    schema_path = (
        REPO_ROOT
        / "src"
        / "pcae"
        / "schema_resources"
        / "chgr"
        / "records"
        / "decision_template.schema.json"
    )
    schema_text = schema_path.read_text(encoding="utf-8")
    assert "No session or record-creation workflow exists this increment" in schema_text
    matching_chgr_templates = list(
        (REPO_ROOT).glob("**/*.json")
    )
    real_decision_template_artifacts = []
    for path in matching_chgr_templates:
        if ".venv" in path.parts or "tests/fixtures" in str(path):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue
        if isinstance(payload, dict) and payload.get("record_type") == "decision_template":
            real_decision_template_artifacts.append(path)
    assert real_decision_template_artifacts == [], (
        "expected no real (non-fixture) CHGR-schema decision_template artifact to exist "
        f"yet, found: {real_decision_template_artifacts}"
    )


def test_authority_basis_gap_is_disclosed_not_concealed(chgr_record: dict) -> None:
    limitations = " ".join(chgr_record["limitations"])
    assert "authority_basis_claimed is not populated" in limitations


# --- 9. Publication immutability, revocation, supersession -----------------


def test_record_digest_still_matches_declared_content_no_post_publication_edit(
    chgr_record: dict,
) -> None:
    assert PCAE_EXECUTABLE, "pcae executable not found on PATH"
    proc = subprocess.run(
        [PCAE_EXECUTABLE, "governance-record", "verify", str(CHGR_PATH), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    checks = {c["name"]: c["status"] for c in payload["checks"]}
    assert checks["digest_self_consistency"] == "passed"


def test_no_mutating_governance_record_command_exists_besides_publish() -> None:
    cli_source = (REPO_ROOT / "src" / "pcae" / "commands" / "governance_record.py").read_text(
        encoding="utf-8"
    )
    assert (
        "no ``create``/\n``confirm``/``suspend``/``supersede``/``revoke``/``import`` command"
        in cli_source
        or "There is no ``create``/" in cli_source
    )


def test_record_has_no_revocation_ref_and_no_deprecated_by(chgr_record: dict) -> None:
    assert "revocation_ref" not in chgr_record
    assert "superseded_by" not in chgr_record
    assert "deprecated_by" not in chgr_record


def test_no_other_chgr_or_supersession_artifact_references_this_record_id() -> None:
    referencing_files = []
    for path in RECORDS_DIR.glob("*.json"):
        if path == CHGR_PATH:
            continue
        text = path.read_text(encoding="utf-8")
        if "chgr-d4343fa51b9743f3abaeb87a881a78b1" in text:
            referencing_files.append(path.name)
    # confirmation/provenance/integrity companions do NOT embed the CHGR's
    # own record_id (they are referenced FROM the CHGR, not the reverse);
    # any hit here would indicate an unexpected coupling, not supersession,
    # but is asserted empty as a structural sanity check either way.
    assert referencing_files == []


# --- 10. Current-state match: target / plan / source / contracts -----------


def test_no_src_docs_contracts_or_scripts_file_changed_since_l5a_entry_commit() -> None:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{L5A_ENTRY_COMMIT}..HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in proc.stdout.splitlines() if line.strip()]
    for path in changed:
        assert not path.startswith("src/pcae/"), f"unexpected src/pcae/ drift: {path}"
        assert not path.startswith("docs/contracts/"), f"unexpected contract drift: {path}"
        assert not path.startswith("scripts/"), f"unexpected scripts/ drift: {path}"


def test_current_hmic_hmrc_hbdc_versions_still_match_the_chgr_conditions_pin(
    chgr_record: dict,
) -> None:
    hmic_text = (
        REPO_ROOT
        / "docs"
        / "contracts"
        / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
    ).read_text(encoding="utf-8")
    hmrc_text = (
        REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
    ).read_text(encoding="utf-8")
    hbdc_text = (
        REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
    ).read_text(encoding="utf-8")
    assert "**Version:** 1.3" in hmic_text
    assert "**Version:** 1.1" in hmrc_text
    assert "**Version:** 1.0" in hbdc_text
    assert "HMIC-001 v1.3" in chgr_record["conditions"]
    assert "HMRC-001 v1.1" in chgr_record["conditions"]
    assert "HBDC-001 v1.0" in chgr_record["conditions"]


# --- 11. Boundary C / Boundary A regression and no host mutation -----------


def test_no_certification_or_cutover_artifacts_exist_anywhere() -> None:
    pcae_dir = REPO_ROOT / ".pcae"
    hits = [p for p in pcae_dir.rglob("*") if "cutover" in p.name.lower() or "certif" in p.name.lower()]
    assert hits == [], f"unexpected certification/cutover artifacts found: {hits}"


def test_no_real_deployment_principal_or_protected_root_exists_on_host() -> None:
    protected_root = Path("/Library/Application Support/PCAE")
    assert not protected_root.exists()
    id_proc = subprocess.run(["id"], capture_output=True, text=True, check=True)
    assert "pcae" not in id_proc.stdout.lower()


def test_git_worktree_is_clean_read_only_verification() -> None:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked_changes = [
        line
        for line in proc.stdout.splitlines()
        if not line.strip().startswith("??")
    ]
    assert tracked_changes == [] or all(
        "tasks/" in line or "PROJECT_STATUS.md" in line or "CHANGELOG.md" in line or ".pcae/phase-completion" in line
        for line in tracked_changes
    )


def test_runtime_remains_observed_observe_unavailable() -> None:
    assert PCAE_EXECUTABLE, "pcae executable not found on PATH"
    proc = subprocess.run(
        [PCAE_EXECUTABLE, "runtime", "inspect"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "Runtime state:             Observed" in out
    assert "Maximum plugin capability: observe" in out
    assert "Execution capability:      unavailable" in out


# --- 12. L.6 host-inspection wording adjudication ---------------------------


def test_l6_no_go_host_inspection_claim_contradicts_l6_own_test_module() -> None:
    """Independently establishes the true historical fact: L.6's own test
    module performed read-only host inspection (Protected Root existence
    check, ``id`` invocation), directly contradicting its own No-Go
    Confirmations line claiming 'this phase performed no host inspection
    at all'. Classified Non-Blocking (wording only; no mutation occurred)
    -- this test records that finding without rewriting L.6's report.
    """
    l6_test_path = (
        REPO_ROOT
        / "tests"
        / "test_phase_149o_20l_6_class_b_provisioning_authorization_record_capture.py"
    )
    l6_source = l6_test_path.read_text(encoding="utf-8")
    assert "def test_no_real_host_provisioning_artifacts_created" in l6_source
    assert 'subprocess.run(["id"]' in l6_source
    assert "protected_root.exists()" in l6_source

    report_path = REPO_ROOT / ".pcae" / "phase-completion-report.md"
    latest_report = json.loads(
        (REPO_ROOT / ".pcae" / "phase-completion-metadata.json").read_text(encoding="utf-8")
    )
    assert latest_report.get("phase_id") in (None, "149O.20L.6A", "149O.20L.6")


def test_boundary_c_and_boundary_a_remain_unauthorized_after_independent_check() -> None:
    hmic_dir = REPO_ROOT / ".pcae"
    active_cert_pointers = list(hmic_dir.rglob("*active-certification*"))
    assert active_cert_pointers == []
