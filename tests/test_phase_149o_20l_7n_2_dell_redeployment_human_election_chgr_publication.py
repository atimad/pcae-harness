"""Phase 149O.20L.7N.2 -- Dell Current-Source Redeployment Human Election
+ CHGR Publication.

Independent assertions against the actually-published CHGR artifact and
its related records -- not a re-run of the election, and not an oracle
for a future 149O.20L.7N.3 independent verification phase. This module
checks facts that are true regardless of who runs it or when: the
published record's content, its schema conformance, and the absence of
any Dell mutation / RepositoryIdentity / DeploymentBinding / election
side effects beyond the governed decision-session/publication-execution
artifacts this phase itself created.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]

_CANDIDATE_SHA = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"
_OLD_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"

_CHGR_ID = "chgr-71bd24f9d3d742d6baac772e480fc876"
_CHGR_PATH = _REPO_ROOT / ".pcae" / "publication-execution" / "records" / f"{_CHGR_ID}.json"

_HISTORICAL_CHGR_IDS = {
    "chgr-0e37ed1340b14311826722c4dbf3e856",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
}

_EXPECTED_SUBJECT = (
    "Approve hac-dell PCAE source redeployment from "
    f"{_OLD_SHA} to {_CANDIDATE_SHA} only; retain venv/wrapper; "
    "no RepositoryIdentity, DeploymentBinding, certification, or activation"
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def test_candidate_and_old_sha_are_ordinary_forty_hex_commits() -> None:
    assert len(_CANDIDATE_SHA) == 40
    assert len(_OLD_SHA) == 40
    assert _git("cat-file", "-t", _CANDIDATE_SHA) == "commit"
    assert _git("cat-file", "-t", _OLD_SHA) == "commit"


def test_candidate_remains_ancestor_of_origin_main() -> None:
    rc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", _CANDIDATE_SHA, "origin/main"],
        cwd=_REPO_ROOT,
    ).returncode
    assert rc == 0


def test_chgr_artifact_exists_and_is_published() -> None:
    assert _CHGR_PATH.is_file()
    payload = json.loads(_CHGR_PATH.read_text())
    assert payload["record_id"] == _CHGR_ID
    assert payload["record_type"] == "human_governance_record"
    assert payload["lifecycle_state"] == "published"
    assert payload["selected_option_id"] == "approve"


def test_decision_subject_matches_expected_text_and_is_within_schema_limit() -> None:
    payload = json.loads(_CHGR_PATH.read_text())
    subject = payload["decision_subject"]
    assert subject == _EXPECTED_SUBJECT
    assert len(subject) == 229
    assert len(subject) <= 500


def test_both_shas_directly_embedded_in_chgr_fields() -> None:
    payload = json.loads(_CHGR_PATH.read_text())
    for field in ("decision_subject", "rationale", "conditions"):
        text = payload[field]
        assert _OLD_SHA in text, f"{_OLD_SHA} missing from {field}"
        assert _CANDIDATE_SHA in text, f"{_CANDIDATE_SHA} missing from {field}"


def test_conditions_and_rationale_within_schema_max_length() -> None:
    payload = json.loads(_CHGR_PATH.read_text())
    assert len(payload["rationale"]) <= 5000
    assert len(payload["conditions"]) <= 5000


def test_conditions_bind_target_scope_and_exclusions() -> None:
    payload = json.loads(_CHGR_PATH.read_text())
    conditions = payload["conditions"]
    for token in (
        "hac-dell",
        "atila-Latitude-E5470",
        "54ff22ce400b475aa0d55cb68f4a3334",
        "/opt/pcae/runtime/src",
        "No RepositoryIdentity creation authorized",
        "No DeploymentBinding creation, rotation, or revocation authorized",
        "No HMIC certification authorized",
        "No Boundary C, no Boundary A",
    ):
        assert token in conditions, f"{token!r} missing from conditions"


def test_conditions_bind_rollback_target() -> None:
    payload = json.loads(_CHGR_PATH.read_text())
    conditions = payload["conditions"]
    assert f"Rollback is authorized to exact old SHA {_OLD_SHA}" in conditions


def test_no_historical_chgr_names_the_candidate_sha() -> None:
    records_dir = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
    for chgr_id in _HISTORICAL_CHGR_IDS:
        path = records_dir / f"{chgr_id}.json"
        assert path.is_file()
        payload = json.loads(path.read_text())
        assert _CANDIDATE_SHA not in payload.get("decision_subject", "")


def test_exactly_four_historical_chgrs_plus_this_phases_one_exist() -> None:
    records_dir = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
    chgr_ids = {p.stem for p in records_dir.glob("chgr-*.json")}
    assert chgr_ids == _HISTORICAL_CHGR_IDS | {_CHGR_ID}


def test_no_repository_identity_artifact_exists() -> None:
    matches = list(_REPO_ROOT.rglob("*repository-identity*.json"))
    matches = [m for m in matches if ".git" not in m.parts]
    assert matches == []


def test_no_deploymentbinding_json_artifact_exists() -> None:
    matches = list(_REPO_ROOT.rglob("*deploymentbinding*.json"))
    matches = [m for m in matches if ".git" not in m.parts]
    assert matches == []


def test_no_authority_bearing_drift_between_candidate_and_head() -> None:
    diff = _git(
        "diff",
        "--stat",
        f"{_CANDIDATE_SHA}..HEAD",
        "--",
        "src/pcae",
        "scripts",
        "docs/contracts",
        "schemas",
        "pyproject.toml",
    )
    assert diff == ""
