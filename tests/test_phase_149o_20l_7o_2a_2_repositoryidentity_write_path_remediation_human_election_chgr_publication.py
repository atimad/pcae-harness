"""Phase 149O.20L.7O.2A.2 -- RepositoryIdentity Write-Path Remediation
Human Election + CHGR Publication.

Independent assertions against the actually-published CHGR artifact and
its related records -- not a re-run of the election, and not an oracle
for a future 149O.20L.7O.2A.3 independent verification phase. Checks
facts that are true regardless of who runs this test or when: the
published record's content, its schema conformance, and the absence of
any Dell mutation / RepositoryIdentity / DeploymentBinding artifact
beyond the governed decision-session/publication-execution artifacts
this phase itself created.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]

_TARGET_HOST = "hac-dell"
_HOSTNAME = "atila-Latitude-E5470"
_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
_SOURCE_SHA = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"
_HMIC_DIGEST = "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"
_TARGET_PATH = "/opt/pcae/runtime/src/.pcae"

_CHGR_ID = "chgr-86aeb5cfa7c44020ad002bc9f80c5856"
_CHGR_PATH = _REPO_ROOT / ".pcae" / "publication-execution" / "records" / f"{_CHGR_ID}.json"

_HISTORICAL_CHGR_IDS = {
    "chgr-0e37ed1340b14311826722c4dbf3e856",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
    "chgr-71bd24f9d3d742d6baac772e480fc876",
}

_EXPECTED_SUBJECT = (
    "Authorize changing only /opt/pcae/runtime/src/.pcae on hac-dell from "
    "root:pcae 0750 to root:pcae 1770 (chmod 1770), retaining owner root and "
    "group pcae, adding no extended ACL, solely to permit pcae-principal "
    "runtime-local file creation while preserving sticky-bit protection of "
    "existing root-owned entries. Excludes RepositoryIdentity and "
    "DeploymentBinding creation."
)


def _load_chgr() -> dict:
    return json.loads(_CHGR_PATH.read_text())


def test_chgr_artifact_exists_and_is_published() -> None:
    assert _CHGR_PATH.is_file()
    payload = _load_chgr()
    assert payload["record_id"] == _CHGR_ID
    assert payload["record_type"] == "human_governance_record"
    assert payload["lifecycle_state"] == "published"
    assert payload["selected_option_id"] == "approve"


def test_decision_subject_matches_expected_text_and_is_within_schema_limit() -> None:
    payload = _load_chgr()
    subject = payload["decision_subject"]
    assert subject == _EXPECTED_SUBJECT
    assert len(subject) == 367
    assert len(subject) <= 500


def test_rationale_and_conditions_within_schema_max_length() -> None:
    payload = _load_chgr()
    assert len(payload["rationale"]) <= 5000
    assert len(payload["conditions"]) <= 5000


def test_target_host_binding_directly_embedded() -> None:
    payload = _load_chgr()
    assert _TARGET_HOST in payload["decision_subject"]
    conditions = payload["conditions"]
    assert _TARGET_HOST in conditions
    assert _HOSTNAME in conditions
    assert _MACHINE_ID in conditions


def test_source_sha_and_hmic_digest_directly_embedded_in_conditions() -> None:
    payload = _load_chgr()
    conditions = payload["conditions"]
    assert _SOURCE_SHA in conditions
    assert _HMIC_DIGEST in conditions


def test_before_and_after_mode_directly_embedded() -> None:
    payload = _load_chgr()
    for field in ("decision_subject", "conditions"):
        text = payload[field]
        assert "0750" in text
        assert "1770" in text
        assert _TARGET_PATH in text


def test_correction_disclosure_present_and_no_full_coverage_claim() -> None:
    payload = _load_chgr()
    for field in ("rationale", "conditions"):
        text = payload[field]
        assert "38 of the 39" in text
        assert "architecture-history.json" in text
    # The rationale legitimately discusses (and disclaims) the overclaim in
    # prose ("does not claim P-A' covers the complete write-required
    # inventory"); the disqualifying condition is an affirmative,
    # undisclaimed claim, which "38 of the 39" above already rules out.
    assert "covers the complete write-required inventory" not in payload["decision_subject"]
    assert "covers the full" not in payload["decision_subject"]


def test_sticky_bit_evidence_qualification_present() -> None:
    payload = _load_chgr()
    for field in ("rationale", "conditions"):
        text = payload[field]
        assert "REFERENCE-VERIFIED FROM PRIMARY LINUX/POSIX SOURCES" in text
        assert "not empirically tested" in text


def test_conditions_bind_all_exclusions() -> None:
    payload = _load_chgr()
    conditions = payload["conditions"]
    for token in (
        "Excluded: RepositoryIdentity creation.",
        "DeploymentBinding creation, rotation, or revocation",
        "Protected Root",
        "source mutation",
        "venv modification",
        "wrapper/launcher modification",
        "Permission Broker modification",
        "certification (HMIC)",
        "Boundary C, Boundary A, HATP_MANDATORY activation",
        "hac-windows",
        "recursive chmod",
    ):
        assert token in conditions, f"{token!r} missing from conditions"


def test_conditions_bind_exact_rollback() -> None:
    payload = _load_chgr()
    conditions = payload["conditions"]
    assert "chmod 0750 /opt/pcae/runtime/src/.pcae" in conditions


def test_conditions_bind_exact_chmod_command_no_recursive_no_chown_no_setfacl() -> None:
    payload = _load_chgr()
    conditions = payload["conditions"]
    assert "chmod 1770 /opt/pcae/runtime/src/.pcae" in conditions
    assert "no -R recursive flag, no chown, no setfacl" in conditions


def test_no_historical_chgr_names_this_transitions_target_path() -> None:
    records_dir = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
    for chgr_id in _HISTORICAL_CHGR_IDS:
        path = records_dir / f"{chgr_id}.json"
        assert path.is_file()
        payload = json.loads(path.read_text())
        assert _TARGET_PATH not in payload.get("decision_subject", "")


def test_exactly_five_historical_chgrs_plus_this_phases_one_exist() -> None:
    records_dir = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
    chgr_ids = {p.stem for p in records_dir.glob("chgr-*.json")}
    assert chgr_ids == _HISTORICAL_CHGR_IDS | {_CHGR_ID}


def test_confirmation_provenance_and_integrity_related_records_exist() -> None:
    payload = _load_chgr()
    records_dir = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
    for ref_key in ("confirmation_evidence_ref", "provenance_ref", "integrity_ref"):
        related_id = payload[ref_key]["record_id"]
        assert (records_dir / f"{related_id}.json").is_file()


def test_no_repository_identity_artifact_exists_locally() -> None:
    matches = [
        m
        for m in _REPO_ROOT.rglob("*repository-identity*.json")
        if ".git" not in m.parts
    ]
    assert matches == []


def test_no_deploymentbinding_json_artifact_exists_locally() -> None:
    matches = [
        m
        for m in _REPO_ROOT.rglob("*deploymentbinding*.json")
        if ".git" not in m.parts
    ]
    assert matches == []
