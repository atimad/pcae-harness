"""Phase 149O.20L.7O.2A.3 -- RepositoryIdentity Write-Path Remediation
Authority Independent Verification.

Independent assertions against the primary decision-session,
orchestration, and CHGR-family artifacts -- not against
`149O.20L.7O.2A.2`'s own phase report or companion tests, which this
phase's doc explicitly declines to treat as an oracle. Focuses on facts
this phase's doc specifically had to reconstruct rather than accept:
stage-timestamp ordering between the human APPROVE selection and the
later explicit CONFIRM, cross-artifact preview-digest agreement, CHGR
uniqueness among all six published records, and single-attempt
publication. No production module is modified by this phase; no Dell
command is issued by this suite (the doc's own live SSH/HBDC/HMIC
findings are not re-executed here, since CI has no route to `hac-dell`).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RECORDS_DIR = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
_ATTEMPTS_DIR = _REPO_ROOT / ".pcae" / "publication-execution" / "attempts"

_SESSION_ID = "CDS-bc9a70fc-3913-4c8b-b95e-50ca0c26091c"
_SESSION_PATH = _REPO_ROOT / ".pcae" / "decision-sessions" / f"{_SESSION_ID}.json"
_ORCHESTRATION_PATH = (
    _REPO_ROOT / ".pcae" / "decision-sessions" / "orchestration" / f"{_SESSION_ID}.json"
)
_PACKAGE_ID = "prp-b25318907ab842ddadc30bde67722944"
_CONSUMED_PACKAGE_PATH = (
    _REPO_ROOT
    / ".pcae"
    / "decision-sessions"
    / "pending-packages"
    / "consumed"
    / f"{_PACKAGE_ID}.json"
)

_CHGR_ID = "chgr-86aeb5cfa7c44020ad002bc9f80c5856"
_CHGR_PATH = _RECORDS_DIR / f"{_CHGR_ID}.json"
_CONF_ID = "chgrconf-698eefcec95841ef8350e94fa7a59ea8"
_PROV_ID = "chgrprov-5a681f551c3646af81d7ecdb1a3ccff1"
_INTG_ID = "chgrintg-2fa93bd13e7e440f8c98a283cff99872"

_ALL_CHGR_IDS = {
    "chgr-0e37ed1340b14311826722c4dbf3e856",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
    "chgr-71bd24f9d3d742d6baac772e480fc876",
    _CHGR_ID,
}

_EXPECTED_PREVIEW_DIGEST = (
    "616ffc29fc0a6f20110a9decbb0d72a9587426ec91ba1eb9db38eba30530b2bd"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


# ═══════════════════════════════════════════════════════════════════════════
# 1. Stage-timestamp ordering -- APPROVE strictly before CONFIRM, with an
#    independently-verifiable window, not a single collapsed event.
# ═══════════════════════════════════════════════════════════════════════════


class TestApproveConfirmSeparation:
    def test_orchestration_records_all_eight_completed_stages(self) -> None:
        record = _load(_ORCHESTRATION_PATH)
        assert record["completed_stages"] == [
            "SessionInitialization",
            "EvidenceAvailability",
            "ClarificationLifecycle",
            "PreviewConstruction",
            "PreviewValidation",
            "ConfirmationRequest",
            "ConfirmationValidation",
            "TerminalCompletion",
        ]

    def test_evidence_precedes_preview_precedes_confirmation(self) -> None:
        record = _load(_ORCHESTRATION_PATH)
        evidence_time = min(_parse(e["collected_at"]) for e in record["evidence"])
        preview_time = _parse(record["last_preview"]["preview_timestamp"])
        confirm_time = _parse(record["confirmation_responses"][0]["confirmed_at"])
        assert evidence_time < preview_time < confirm_time

    def test_approve_selection_reflected_in_preview_before_confirmation(self) -> None:
        """The preview (rendered from the DecisionSelected state, i.e. after
        the human's APPROVE `select` call) already carries the selection --
        proving `select` happened strictly before the preview, which itself
        strictly precedes `confirm` (previous test)."""

        record = _load(_ORCHESTRATION_PATH)
        assert "Selected option: approve" in record["last_preview"]["rendered_content"]

    def test_confirmation_request_and_response_share_a_single_atomic_capture(self) -> None:
        """Documented architectural fact (see doc §3): the CLI `confirm`
        command captures one `now` for both the request and its response,
        since there is no separate interactive round-trip. Confirmed
        structurally here rather than re-asserted as a defect."""

        record = _load(_ORCHESTRATION_PATH)
        req = record["confirmation_requests"][0]
        resp = record["confirmation_responses"][0]
        assert req["created_at"] == resp["confirmed_at"]
        assert req["request_id"] == resp["request_id"]

    def test_confirmation_gap_after_preview_is_multiple_seconds(self) -> None:
        record = _load(_ORCHESTRATION_PATH)
        preview_time = _parse(record["last_preview"]["preview_timestamp"])
        confirm_time = _parse(record["confirmation_responses"][0]["confirmed_at"])
        gap_seconds = (confirm_time - preview_time).total_seconds()
        assert gap_seconds > 30

    def test_session_final_state_is_confirmed_not_merely_selected(self) -> None:
        session = _load(_SESSION_PATH)["session"]
        assert session["session_state"] == "Confirmed"
        assert session["human_selection_id"] == "approve"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Preview digest cross-artifact agreement (three independently-schema'd
#    records, not a single source repeated).
# ═══════════════════════════════════════════════════════════════════════════


class TestPreviewDigestCrossAgreement:
    def test_orchestration_preview_digest_matches_expected(self) -> None:
        record = _load(_ORCHESTRATION_PATH)
        assert record["last_preview"]["preview_id"].startswith("prev-")
        assert (
            record["confirmation_requests"][0]["preview_digest"]
            == _EXPECTED_PREVIEW_DIGEST
        )

    def test_confirmation_evidence_digest_matches_expected(self) -> None:
        conf = _load(_RECORDS_DIR / f"{_CONF_ID}.json")
        assert conf["confirmed_content_digest"] == _EXPECTED_PREVIEW_DIGEST
        assert conf["preview_rendering_digest"] == _EXPECTED_PREVIEW_DIGEST

    def test_provenance_record_digest_matches_expected(self) -> None:
        prov = _load(_RECORDS_DIR / f"{_PROV_ID}.json")
        assert prov["preview_content_digest"] == _EXPECTED_PREVIEW_DIGEST

    def test_consumed_package_digest_matches_expected(self) -> None:
        package = _load(_CONSUMED_PACKAGE_PATH)["package"]
        assert package["preview_digest"] == _EXPECTED_PREVIEW_DIGEST


# ═══════════════════════════════════════════════════════════════════════════
# 3. Integrity chain: chgrintg payload_digest must equal the CHGR's own
#    record_digest (the check `governance-record verify --related` performs).
# ═══════════════════════════════════════════════════════════════════════════


class TestIntegrityChain:
    def test_integrity_payload_digest_matches_chgr_record_digest(self) -> None:
        chgr = _load(_CHGR_PATH)
        integrity = _load(_RECORDS_DIR / f"{_INTG_ID}.json")
        assert integrity["payload_digest"] == chgr["record_digest"]

    def test_chgr_integrity_ref_is_disclosed_provisional_not_final(self) -> None:
        """The CHGR's own integrity_ref.record_digest intentionally does NOT
        equal chgrintg's own record_digest -- a disclosed forward-reference
        artifact, not a defect. Confirmed structurally so a future accidental
        "fix" that breaks this disclosed property is caught."""

        chgr = _load(_CHGR_PATH)
        integrity = _load(_RECORDS_DIR / f"{_INTG_ID}.json")
        assert chgr["integrity_ref"]["record_digest"] != integrity["record_digest"]
        assert any(
            "provisional digest" in limitation for limitation in chgr["limitations"]
        )

    def test_confirmation_evidence_record_digest_matches_chgr_ref(self) -> None:
        chgr = _load(_CHGR_PATH)
        conf = _load(_RECORDS_DIR / f"{_CONF_ID}.json")
        assert chgr["confirmation_evidence_ref"]["record_digest"] == conf["record_digest"]

    def test_provenance_record_digest_matches_chgr_ref(self) -> None:
        chgr = _load(_CHGR_PATH)
        prov = _load(_RECORDS_DIR / f"{_PROV_ID}.json")
        assert chgr["provenance_ref"]["record_digest"] == prov["record_digest"]


# ═══════════════════════════════════════════════════════════════════════════
# 4. CHGR uniqueness and publication-attempt cardinality.
# ═══════════════════════════════════════════════════════════════════════════


class TestChgrUniquenessAndAttempts:
    def test_exactly_six_published_chgrs_exist(self) -> None:
        chgr_ids = {p.stem for p in _RECORDS_DIR.glob("chgr-*.json")}
        assert chgr_ids == _ALL_CHGR_IDS

    def test_all_six_chgrs_are_published_none_revoked(self) -> None:
        for chgr_id in _ALL_CHGR_IDS:
            payload = _load(_RECORDS_DIR / f"{chgr_id}.json")
            assert payload["lifecycle_state"] == "published"

    def test_only_this_chgr_names_the_target_path(self) -> None:
        target_path = "/opt/pcae/runtime/src/.pcae"
        matches = [
            chgr_id
            for chgr_id in _ALL_CHGR_IDS
            if target_path in _load(_RECORDS_DIR / f"{chgr_id}.json").get("decision_subject", "")
        ]
        assert matches == [_CHGR_ID]

    def test_exactly_one_publication_attempt_for_this_session(self) -> None:
        matches = [
            p
            for p in _ATTEMPTS_DIR.glob("pubexec-*.json")
            if _SESSION_ID in p.read_text() or _PACKAGE_ID in p.read_text()
        ]
        assert len(matches) == 1
        attempt = _load(matches[0])
        assert attempt["result"]["success"] is True
        assert attempt["result"]["failure_reason"] is None
        assert attempt["result"]["error_type"] is None

    def test_no_revocation_registry_or_state_exists(self) -> None:
        pcae_dir = _REPO_ROOT / ".pcae"
        assert list(pcae_dir.rglob("*revoc*")) == []
        assert list(pcae_dir.rglob("*supersed*")) == []
        for chgr_id in _ALL_CHGR_IDS:
            payload = _load(_RECORDS_DIR / f"{chgr_id}.json")
            assert payload["lifecycle_state"] != "revoked"
            assert payload["lifecycle_state"] != "superseded"


# ═══════════════════════════════════════════════════════════════════════════
# 5. Authority currentness: election-time source SHA is a real ancestor of
#    the current HEAD, and only non-authority-bearing paths changed since.
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthorityCurrentnessVsSourceEvolution:
    def test_election_time_source_sha_is_ancestor_of_head(self) -> None:
        import subprocess

        result = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                "b0840e96a7ffb12308e95828aa5927c3e7c770c0",
                "HEAD",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
        )
        assert result.returncode == 0

    def test_no_src_contracts_or_scripts_changes_since_election(self) -> None:
        import subprocess

        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                "b0840e96a7ffb12308e95828aa5927c3e7c770c0",
                "HEAD",
                "--",
                "src/",
                "docs/contracts/",
                "scripts/",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════════
# 6. No mutation artifacts of any kind exist locally as a side effect of
#    this verification-only phase.
# ═══════════════════════════════════════════════════════════════════════════


class TestZeroLocalMutationArtifacts:
    def test_no_repository_identity_artifact_exists_locally(self) -> None:
        matches = [
            m for m in _REPO_ROOT.rglob("*repository-identity*.json") if ".git" not in m.parts
        ]
        assert matches == []

    def test_no_deploymentbinding_artifact_exists_locally(self) -> None:
        matches = [
            m for m in _REPO_ROOT.rglob("*deploymentbinding*.json") if ".git" not in m.parts
        ]
        assert matches == []

    def test_no_new_chgr_published_by_this_phase(self) -> None:
        chgr_ids = {p.stem for p in _RECORDS_DIR.glob("chgr-*.json")}
        assert chgr_ids == _ALL_CHGR_IDS
