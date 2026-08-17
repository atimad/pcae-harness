"""Phase 149O.20L.7N.3 -- Dell Current-Source Redeployment Authority
Independent Verification.

Independent re-derivation of the 149O.20L.7N.2 redeployment authority from
first principles: which decision session actually governs, that the human
selection was APPROVE with a separate confirmation, that the first
publication attempt failed schema validation and left no CHGR, that the
successful CHGR directly embeds both SHAs / target / scope / exclusions /
rollback, that the human-facing preview does not authorize less than (and
the CHGR does not authorize more than) what was confirmed, that no
historical CHGR applies to the candidate, and that no Dell mutation or
first-use artifact exists.

This module does not import the 149O.20L.7N.2 companion test module as an
oracle -- every assertion here re-reads the underlying persisted artifacts
and re-derives its own expectations.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]

_OLD_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"
_CANDIDATE_SHA = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"

_GOVERNING_SESSION_ID = "CDS-64779ace-4532-43ed-af46-8727c1378552"
_SUPERSEDED_FAILED_SESSION_ID = "CDS-58cb0c15-2f9f-4e26-b576-61d4427935bd"

_FAILED_PACKAGE_ID = "prp-993bf4bc8d1b47b3b84308e868c8f710"
_SUCCESSFUL_PACKAGE_ID = "prp-aa38def3944d4b22b87ee5799f7848ce"

_CHGR_ID = "chgr-71bd24f9d3d742d6baac772e480fc876"
_CHGR_PATH = _REPO_ROOT / ".pcae" / "publication-execution" / "records" / f"{_CHGR_ID}.json"

_HISTORICAL_CHGR_IDS = {
    "chgr-0e37ed1340b14311826722c4dbf3e856",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
}

_DECISION_SESSIONS_DIR = _REPO_ROOT / ".pcae" / "decision-sessions"
_PENDING_PACKAGES_DIR = _DECISION_SESSIONS_DIR / "pending-packages"
_RECORDS_DIR = _REPO_ROOT / ".pcae" / "publication-execution" / "records"

_REQUIRED_EXCLUSION_TOKENS = (
    "pip install",
    "venv recreation",
    "No RepositoryIdentity creation authorized",
    "No DeploymentBinding creation, rotation, or revocation authorized",
    "No HMIC certification authorized",
    "No Boundary C, no Boundary A",
    "no HATP_MANDATORY activation",
    "no Cutover Record",
    "No Permission Broker",
    "No repository onboarding",
    "hac-windows",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _chgr() -> dict:
    return _load(_CHGR_PATH)


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


# --- Decision-session enumeration and governing-session derivation --------


def test_exactly_two_decision_sessions_reference_the_candidate_sha() -> None:
    all_sessions = sorted(_DECISION_SESSIONS_DIR.glob("CDS-*.json"))
    referencing = [
        p for p in all_sessions if _CANDIDATE_SHA in p.read_text()
    ]
    ids = {p.stem for p in referencing}
    assert ids == {_GOVERNING_SESSION_ID, _SUPERSEDED_FAILED_SESSION_ID}


def test_governing_session_is_confirmed_approve_and_bound_to_governing_chgr() -> None:
    session = _load(_DECISION_SESSIONS_DIR / f"{_GOVERNING_SESSION_ID}.json")["session"]
    assert session["session_state"] == "Confirmed"
    assert session["human_selection_id"] == "approve"
    assert session["options_presented"] == ["approve", "decline", "amend"]

    chgr = _chgr()
    confirmation = _load(_RECORDS_DIR / "chgrconf-c32d28bcfeff41b0a504f052cdeb4848.json")
    # The governing session's own confirmation timestamp is within the same
    # sub-second request pipeline as the CHGR's decision-maker-identity-
    # evidence and the confirmation record -- an independent cross-artifact
    # timestamp tie, not a name-based assumption. A tolerance (not exact
    # equality) accounts for distinct capture points within one request.
    session_ts = _parse_ts(session["updated_at"])
    chgr_ts = _parse_ts(chgr["decision_maker_identity_evidence"]["captured_at"])
    confirmation_ts = _parse_ts(confirmation["confirmation_timestamp"])
    assert abs((session_ts - chgr_ts).total_seconds()) < 1.0
    assert abs((confirmation_ts - chgr_ts).total_seconds()) < 1.0


def test_other_candidate_session_is_the_failed_first_attempt_not_governing() -> None:
    session = _load(_DECISION_SESSIONS_DIR / f"{_SUPERSEDED_FAILED_SESSION_ID}.json")["session"]
    # Same subject/selection as the governing session, but its confirmation
    # timestamp does NOT match the CHGR's decision-maker-identity-evidence,
    # so it cannot be the record that actually produced the published CHGR.
    chgr = _chgr()
    assert _parse_ts(session["updated_at"]) != _parse_ts(
        chgr["decision_maker_identity_evidence"]["captured_at"]
    )
    assert session["human_conditions_text"] != chgr["conditions"]
    assert len(session["human_conditions_text"]) > 5000  # would have failed schema validation


# --- Failed first publication attempt is reconstructed and non-authoritative


def test_failed_package_conditions_exceeded_schema_max_length() -> None:
    pkg = _load(_PENDING_PACKAGES_DIR / f"{_FAILED_PACKAGE_ID}.json")
    conditions_text = pkg["package"]["conditions_text"]
    assert len(conditions_text) > 5000
    assert pkg["session_id"] == _SUPERSEDED_FAILED_SESSION_ID


def test_failed_package_left_no_chgr_and_stayed_pending() -> None:
    pkg = _load(_PENDING_PACKAGES_DIR / f"{_FAILED_PACKAGE_ID}.json")
    assert pkg["disposition"] == "pending"
    assert pkg["record_id"] is None
    assert pkg["publication_attempt_id"] is None


def test_all_attempts_against_failed_package_failed_with_schema_diagnostic() -> None:
    attempts_dir = _REPO_ROOT / ".pcae" / "publication-execution" / "attempts"
    matching = [
        p
        for p in attempts_dir.glob("pubexec-*.json")
        if _load(p)["authorization"]["package_id"] == _FAILED_PACKAGE_ID
    ]
    assert len(matching) >= 1
    for path in matching:
        result = _load(path)["result"]
        assert result["record_id"] is None
        diagnostics = " ".join(result["diagnostics"])
        assert "schema_invalid_record" in diagnostics
        assert "/conditions" in diagnostics


def test_failed_package_id_does_not_appear_as_any_chgr_record_id() -> None:
    all_chgr_ids = {p.stem for p in _RECORDS_DIR.glob("chgr-*.json")}
    assert _FAILED_PACKAGE_ID not in all_chgr_ids


# --- Successful package/CHGR identity and preview/confirmation binding -----


def test_successful_package_is_consumed_and_bound_to_governing_chgr() -> None:
    consumed_dir = _PENDING_PACKAGES_DIR / "consumed"
    pkg = _load(consumed_dir / f"{_SUCCESSFUL_PACKAGE_ID}.json")
    assert pkg["disposition"] == "consumed"
    assert pkg["record_id"] == _CHGR_ID
    assert pkg["session_id"] == _GOVERNING_SESSION_ID


def test_confirmed_content_digest_matches_previewed_content_digest() -> None:
    consumed_dir = _PENDING_PACKAGES_DIR / "consumed"
    pkg = _load(consumed_dir / f"{_SUCCESSFUL_PACKAGE_ID}.json")["package"]
    confirmation = _load(_RECORDS_DIR / "chgrconf-c32d28bcfeff41b0a504f052cdeb4848.json")
    assert confirmation["confirmed_content_digest"] == pkg["preview_digest"]
    assert confirmation["preview_rendering_digest"] == pkg["preview_digest"]


def test_chgr_does_not_authorize_beyond_what_was_previewed() -> None:
    consumed_dir = _PENDING_PACKAGES_DIR / "consumed"
    preview = _load(consumed_dir / f"{_SUCCESSFUL_PACKAGE_ID}.json")["package"]["preview_rendered_content"]
    chgr = _chgr()
    for field in ("decision_subject", "conditions", "rationale"):
        assert chgr[field] in preview, f"CHGR field {field!r} not verbatim in human-previewed content"


# --- Governing CHGR: existence, publication, structure, lifecycle ---------


def test_chgr_exists_exactly_once_and_is_published() -> None:
    matches = list(_RECORDS_DIR.glob(f"{_CHGR_ID}.json"))
    assert len(matches) == 1
    chgr = _chgr()
    assert chgr["record_type"] == "human_governance_record"
    assert chgr["lifecycle_state"] == "published"
    assert chgr["selected_option_id"] == "approve"
    assert "executed" not in chgr["lifecycle_state"]
    assert "revoked" not in chgr["lifecycle_state"]
    assert "superseded" not in chgr["lifecycle_state"]


def test_governance_record_verify_related_passes_all_applicable_checks() -> None:
    proc = subprocess.run(
        [
            "pcae",
            "governance-record",
            "verify",
            str(_CHGR_PATH),
            "--related",
            str(_RECORDS_DIR / "chgrconf-c32d28bcfeff41b0a504f052cdeb4848.json"),
            "--related",
            str(_RECORDS_DIR / "chgrprov-a56906437b454b0883a0fbc7ffa627a8.json"),
            "--related",
            str(_RECORDS_DIR / "chgrintg-32392620777b4cce970fb965bec1d8fc.json"),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "outcome: verified" in proc.stdout
    for check in (
        "schema_shape",
        "digest_self_consistency",
        "lifecycle_structural_legality",
        "confirmation_binding",
        "assurance_truthfulness",
        "provenance_consistency",
        "integrity_consistency",
    ):
        assert f"check: {check}" in proc.stdout
        line = next(l for l in proc.stdout.splitlines() if check in l)
        assert "passed" in line


def test_integrity_payload_digest_matches_chgr_record_digest() -> None:
    chgr = _chgr()
    integrity = _load(_RECORDS_DIR / "chgrintg-32392620777b4cce970fb965bec1d8fc.json")
    assert integrity["payload_digest"] == chgr["record_digest"]


# --- SHA bindings and candidate currentness --------------------------------


def test_both_shas_are_full_forty_hex_ordinary_commits() -> None:
    assert len(_OLD_SHA) == 40
    assert len(_CANDIDATE_SHA) == 40
    assert _git("cat-file", "-t", _OLD_SHA) == "commit"
    assert _git("cat-file", "-t", _CANDIDATE_SHA) == "commit"


def test_both_shas_directly_embedded_in_every_authority_bearing_chgr_field() -> None:
    chgr = _chgr()
    for field in ("decision_subject", "rationale", "conditions"):
        assert _OLD_SHA in chgr[field]
        assert _CANDIDATE_SHA in chgr[field]


def test_candidate_is_ancestor_of_origin_main_and_current_head() -> None:
    for ref in ("origin/main", "HEAD"):
        rc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", _CANDIDATE_SHA, ref], cwd=_REPO_ROOT
        ).returncode
        assert rc == 0, f"{_CANDIDATE_SHA} is not an ancestor of {ref}"


def test_no_authority_bearing_drift_between_candidate_and_head() -> None:
    diff = _git(
        "diff",
        "--name-only",
        f"{_CANDIDATE_SHA}..HEAD",
        "--",
        "src/pcae",
        "scripts",
        "docs/contracts",
        "schemas",
        "pyproject.toml",
    )
    assert diff == ""


def test_exact_five_file_authority_relevant_delta_old_to_candidate() -> None:
    diff = _git(
        "diff",
        "--name-only",
        f"{_OLD_SHA}..{_CANDIDATE_SHA}",
        "--",
        "src/pcae",
        "scripts",
        "docs/contracts",
        "schemas",
        "pyproject.toml",
    )
    files = set(diff.splitlines())
    assert files == {
        "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
        "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        "scripts/hatp_deployment_binding_admin.py",
        "src/pcae/core/hatp_deployment_binding_admin.py",
        "src/pcae/core/hatp_mandatory_certification.py",
    }


def test_hmic_digest_independently_recomputed_at_candidate_in_disposable_worktree(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "hmic-scratch"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), _CANDIDATE_SHA],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        proc = subprocess.run(
            [
                "python3",
                "-c",
                "import sys; sys.path.insert(0, 'src');"
                "from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest;"
                "from pcae.core.paths import HarnessPath;"
                "from pathlib import Path;"
                "print(derive_implementation_scope_digest(HarnessPath(Path('.').resolve())))",
            ],
            cwd=worktree,
            check=True,
            capture_output=True,
            text=True,
        )
        digest = proc.stdout.strip()
        assert digest == "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"
        assert _chgr()["rationale"].count(digest) >= 1
    finally:
        subprocess.run(
            ["git", "worktree", "remove", str(worktree), "--force"],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )


# --- Target/scope/exclusions/rollback bindings -----------------------------


def test_conditions_bind_target_host_identity() -> None:
    conditions = _chgr()["conditions"]
    for token in ("hac-dell", "atila-Latitude-E5470", "54ff22ce400b475aa0d55cb68f4a3334"):
        assert token in conditions


def test_conditions_bind_source_only_scope_to_exact_path() -> None:
    conditions = _chgr()["conditions"]
    assert "/opt/pcae/runtime/src" in conditions
    assert "source checkout transition" in conditions


def test_conditions_bind_rollback_to_exact_old_sha_source_only() -> None:
    conditions = _chgr()["conditions"]
    assert f"Rollback is authorized to exact old SHA {_OLD_SHA}" in conditions
    assert "source-only, network-independent" in conditions


def test_conditions_embed_wrapper_digest_and_retention() -> None:
    conditions = _chgr()["conditions"]
    assert "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32" in conditions
    assert "retained unchanged" in conditions


def test_conditions_contain_full_required_exclusion_set() -> None:
    conditions = _chgr()["conditions"]
    for token in _REQUIRED_EXCLUSION_TOKENS:
        assert token in conditions, f"exclusion token {token!r} missing from conditions"


# --- Condensation safety: failed 5250-char vs successful 4452-char --------


def test_condensed_conditions_preserved_all_authority_critical_tokens() -> None:
    failed_conditions = _load(_PENDING_PACKAGES_DIR / f"{_FAILED_PACKAGE_ID}.json")["package"][
        "conditions_text"
    ]
    successful_conditions = _chgr()["conditions"]
    assert len(failed_conditions) > 5000
    assert len(successful_conditions) <= 5000

    critical_tokens = _REQUIRED_EXCLUSION_TOKENS + (
        "hac-dell",
        "atila-Latitude-E5470",
        "54ff22ce400b475aa0d55cb68f4a3334",
        _OLD_SHA,
        _CANDIDATE_SHA,
        "/opt/pcae/runtime/src",
        f"Rollback is authorized to exact old SHA {_OLD_SHA}",
        "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32",
    )
    for token in critical_tokens:
        assert token in failed_conditions, f"{token!r} unexpectedly absent from pre-condensation text"
        assert token in successful_conditions, f"{token!r} was dropped during condensation"


# --- Decision-subject / conditions length -----------------------------------


def test_decision_subject_length_within_schema_maximum() -> None:
    chgr = _chgr()
    assert len(chgr["decision_subject"]) == 229
    assert len(chgr["decision_subject"]) <= 500


def test_conditions_length_within_schema_maximum() -> None:
    chgr = _chgr()
    assert len(chgr["conditions"]) == 4452
    assert len(chgr["conditions"]) <= 5000


# --- Historical CHGR enumeration and inapplicability -----------------------


def test_exactly_five_chgrs_exist_total() -> None:
    chgr_ids = {p.stem for p in _RECORDS_DIR.glob("chgr-*.json")}
    assert chgr_ids == _HISTORICAL_CHGR_IDS | {_CHGR_ID}


def test_no_historical_chgr_names_candidate_sha_in_its_own_content() -> None:
    for chgr_id in _HISTORICAL_CHGR_IDS:
        payload = _load(_RECORDS_DIR / f"{chgr_id}.json")
        full_text = payload["decision_subject"] + payload["rationale"] + payload["conditions"]
        assert _CANDIDATE_SHA not in full_text, f"{chgr_id} unexpectedly names the candidate SHA"


def test_exactly_one_chgr_names_the_candidate_sha() -> None:
    referencing = [
        p.stem
        for p in _RECORDS_DIR.glob("chgr-*.json")
        if _CANDIDATE_SHA in _load(p).get("decision_subject", "") + _load(p).get("rationale", "")
    ]
    assert referencing == [_CHGR_ID]


# --- Zero Dell mutation / absent first-use artifacts -----------------------


def test_phase_7n2_commit_touched_only_governance_bookkeeping_doc_and_test() -> None:
    changed_paths = _git("show", "--name-only", "--format=", "274617f5").strip().splitlines()
    assert changed_paths
    for path in changed_paths:
        assert path.startswith(
            (".pcae/", "docs/PHASE_149O_20L_7N_2", "tests/test_phase_149o_20l_7n_2")
        ), f"unexpected non-governance path touched by 7N.2: {path}"


def test_phase_7n2_committed_code_contains_no_network_capable_calls() -> None:
    diff = _git(
        "show",
        "274617f5",
        "--",
        "tests/test_phase_149o_20l_7n_2_dell_redeployment_human_election_chgr_publication.py",
    )
    lowered = diff.lower()
    for token in ("ssh", "socket", "paramiko", "subprocess.popen", "urllib", "requests."):
        assert token not in lowered


def test_no_repository_identity_artifact_exists() -> None:
    matches = [m for m in _REPO_ROOT.rglob("*repository-identity*.json") if ".git" not in m.parts]
    assert matches == []


def test_no_deploymentbinding_artifact_exists() -> None:
    matches = [
        m
        for m in _REPO_ROOT.rglob("*deploymentbinding*.json")
        if ".git" not in m.parts and ".venv" not in m.parts
    ]
    assert matches == []


def test_no_certification_record_or_binding_artifact_exists() -> None:
    # Scoped to persisted governance-state artifacts (.pcae/**), not
    # pre-existing schema definitions or unrelated fixture files that
    # merely have "certification" in their name.
    matches = [
        m
        for m in (_REPO_ROOT / ".pcae").rglob("*certification*.json")
    ]
    assert matches == []
    hmic_dir = _REPO_ROOT / ".pcae" / "hmic"
    assert not hmic_dir.is_dir()
