"""Phase 149O.20L.7C -- Dell Class-B Boundary-P Authorization Independent
Verification.

This phase does NOT provision the Dell, does NOT create or modify a
DeploymentBinding, does NOT certify, does NOT activate, and does NOT
reinterpret the human election. It independently reconstructs and
adversarially attacks the Dell-specific CHGR
(`chgr-96a0ce12756e4cc892492a87af1db832`) published by Phase
149O.20L.7B.2, tracing the full create/evidence/select/preview/confirm/
readiness/publish chain, proving the two cancelled decision sessions
(one citing a wrong commit, one citing a fabricated/hand-padded SHA)
never contaminate the successful chain, and re-deriving source-SHA and
wrapper-digest authenticity directly from the immutable 149O.20L.7B.1
proposition commit rather than trusting any prior phase's report.

These assertions are independently authored against this repository's
persisted `.pcae/` governance state and immutable git history. They
were written after reading (for pattern reference only, not as an
authority oracle) tests/test_phase_149o_20l_7b_dell_class_b_boundary_p_authorization_record_capture.py
and tests/test_phase_149o_20l_7b_2_dell_class_b_boundary_p_authorization_record_re_capture.py.
No Dell mutation is performed by this module -- it reads only
already-persisted local artifacts and immutable git history.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

PCAE_DIR = REPO_ROOT / ".pcae"
RECORDS_DIR = PCAE_DIR / "publication-execution" / "records"
SESSIONS_DIR = PCAE_DIR / "decision-sessions"
ORCH_DIR = SESSIONS_DIR / "orchestration"

DELL_CHGR_ID = "chgr-96a0ce12756e4cc892492a87af1db832"
DELL_CHGR_PATH = RECORDS_DIR / f"{DELL_CHGR_ID}.json"

MAC_CHGR_ID = "chgr-d4343fa51b9743f3abaeb87a881a78b1"
MAC_CHGR_PATH = RECORDS_DIR / f"{MAC_CHGR_ID}.json"

SUCCESS_SESSION_ID = "CDS-adb67041-3a30-4b4e-a188-e6284e7743be"
AMEND_SESSION_ID = "CDS-cf123bbf-a5d7-4f0f-ac22-0baa257990af"
WRONG_COMMIT_SESSION_ID = "CDS-506d69fd-1d22-4d27-8004-5dff2b5a8079"
FABRICATED_SHA_SESSION_ID = "CDS-e020f5a5-abc6-4562-b992-0d17a19896f1"

PACKAGE_ID = "prp-66418889a03e42379213a2f50340d362"
READINESS_PACKAGE_PATH = (
    SESSIONS_DIR / "pending-packages" / "consumed" / f"{PACKAGE_ID}.json"
)
PUBLISHED_HANDOFF_PATH = (
    PCAE_DIR / "publication-execution" / "published" / f"{PACKAGE_ID}.json"
)

PINNED_SOURCE_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
PREVIEW_DIGEST = "e49caf228bdbddda27277f1b37ad06cd71bd68a60bd5aa6a8faacd50d899033d"
IMMUTABLE_7B1_COMMIT = "f9e33232c83163aad5e50bc94db7cab51b844ac5"

WRONG_COMMIT_EVIDENCE_ID = "0ed700911c89fd04f28f087c0a11de8dd7f35a46"
FABRICATED_SHA_EVIDENCE_ID = "f9e33232f13c7a58f6e2fa1b2c7d3a5e5f9d0c11"

WRAPPER_SCRIPT_BYTES = (
    b"#!/bin/sh\n"
    b"set -eu\n"
    b"unset PYTHONPATH\n"
    b"PYTHONNOUSERSITE=1\n"
    b"export PYTHONNOUSERSITE\n"
    b"PATH=/usr/bin:/bin:/usr/sbin:/sbin\n"
    b"export PATH\n"
    b"cd /opt/pcae/runtime\n"
    b'exec /opt/pcae/runtime/venv/bin/pcae "$@"\n'
)


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def dell_chgr() -> dict:
    return _load_json(DELL_CHGR_PATH)


@pytest.fixture(scope="module")
def mac_chgr() -> dict:
    return _load_json(MAC_CHGR_PATH)


@pytest.fixture(scope="module")
def success_session() -> dict:
    return _load_json(SESSIONS_DIR / f"{SUCCESS_SESSION_ID}.json")["session"]


@pytest.fixture(scope="module")
def amend_session() -> dict:
    return _load_json(SESSIONS_DIR / f"{AMEND_SESSION_ID}.json")["session"]


@pytest.fixture(scope="module")
def wrong_commit_session_orch() -> dict:
    return _load_json(ORCH_DIR / f"{WRONG_COMMIT_SESSION_ID}.json")


@pytest.fixture(scope="module")
def fabricated_sha_session_orch() -> dict:
    return _load_json(ORCH_DIR / f"{FABRICATED_SHA_SESSION_ID}.json")


@pytest.fixture(scope="module")
def success_session_orch() -> dict:
    return _load_json(ORCH_DIR / f"{SUCCESS_SESSION_ID}.json")


@pytest.fixture(scope="module")
def readiness_package() -> dict:
    return _load_json(READINESS_PACKAGE_PATH)


@pytest.fixture(scope="module")
def published_handoff() -> dict:
    return _load_json(PUBLISHED_HANDOFF_PATH)


class TestSuccessfulChgrIdentity:
    def test_dell_chgr_file_exists(self):
        assert DELL_CHGR_PATH.is_file()

    def test_dell_chgr_record_id_matches(self, dell_chgr):
        assert dell_chgr["record_id"] == DELL_CHGR_ID

    def test_dell_chgr_lifecycle_published(self, dell_chgr):
        assert dell_chgr["lifecycle_state"] == "published"

    def test_dell_chgr_selected_option_approve(self, dell_chgr):
        assert dell_chgr["selected_option_id"] == "approve"

    def test_dell_chgr_names_dell_by_machine_id(self, dell_chgr):
        assert DELL_MACHINE_ID in dell_chgr["decision_subject"]

    def test_dell_chgr_cites_7b1_document_by_path(self, dell_chgr):
        assert (
            "PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md"
            in dell_chgr["decision_subject"]
        )


class TestSuccessfulSessionIdentity:
    def test_session_id_is_expected_and_distinct_from_amend(self):
        assert SUCCESS_SESSION_ID != AMEND_SESSION_ID

    def test_session_id_distinct_from_both_cancelled_sessions(self):
        assert SUCCESS_SESSION_ID not in (
            WRONG_COMMIT_SESSION_ID,
            FABRICATED_SHA_SESSION_ID,
        )

    def test_success_session_confirmed(self, success_session):
        assert success_session["session_state"] == "Confirmed"

    def test_success_session_readiness_status_consumed(self):
        status_result = subprocess.run(
            ["python3", "-m", "pcae", "decision-session", "status", SUCCESS_SESSION_ID],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert status_result.returncode == 0
        assert "readiness_package_status: consumed" in status_result.stdout


class TestApproveElectionAuthenticity:
    def test_selection_is_literally_approve(self, success_session):
        assert success_session["human_selection_id"] == "approve"

    def test_options_presented_include_decline_and_amend_not_forced(self, success_session):
        # A genuine election requires decline/amend to have been real,
        # available alternatives -- not a rubber-stamped single option.
        assert set(success_session["options_presented"]) == {
            "approve",
            "decline",
            "amend",
        }

    def test_rationale_is_first_person_and_explicit(self, success_session):
        rationale = success_session["human_rationale_text"]
        assert rationale is not None
        assert rationale.strip().startswith("I, as the human governance authority")
        assert "elect to APPROVE" in rationale

    def test_rationale_not_reused_verbatim_from_amend_session(
        self, success_session, amend_session
    ):
        assert success_session["human_rationale_text"] != amend_session["human_rationale_text"]

    def test_amend_session_selection_untouched_by_success_session(self, amend_session):
        assert amend_session["human_selection_id"] == "amend"
        assert amend_session["session_state"] == "Confirmed"


class TestConfirmationBinding:
    def test_confirmation_response_accepted(self, success_session_orch):
        responses = success_session_orch["confirmation_responses"]
        assert len(responses) == 1
        assert responses[0]["confirmation_result"] == "Accepted"

    def test_confirmation_bound_to_preview_digest(self, success_session_orch):
        req = success_session_orch["confirmation_requests"][0]
        resp = success_session_orch["confirmation_responses"][0]
        assert req["preview_digest"] == PREVIEW_DIGEST
        assert resp["preview_digest"] == PREVIEW_DIGEST

    def test_confirmation_request_and_response_share_request_id(self, success_session_orch):
        req = success_session_orch["confirmation_requests"][0]
        resp = success_session_orch["confirmation_responses"][0]
        assert req["request_id"] == resp["request_id"]

    def test_neither_cancelled_session_has_any_confirmation(
        self, wrong_commit_session_orch, fabricated_sha_session_orch
    ):
        assert wrong_commit_session_orch["confirmation_requests"] == []
        assert wrong_commit_session_orch["confirmation_responses"] == []
        assert fabricated_sha_session_orch["confirmation_requests"] == []
        assert fabricated_sha_session_orch["confirmation_responses"] == []


class TestPreviewDigest:
    def test_last_preview_digest_field_matches(self, success_session_orch):
        # last_preview itself does not carry a "preview_digest" key (it
        # carries preview_id/rendered_content); the digest binding is
        # asserted via the confirmation_requests entry (tested above).
        # Here we independently recompute that the rendered content's
        # cited evidence set is exactly the three genuine evidence refs.
        evidence_refs = success_session_orch["last_preview"]["evidence_refs"]
        assert set(evidence_refs) == {
            PINNED_SOURCE_SHA,
            WRAPPER_DIGEST,
            IMMUTABLE_7B1_COMMIT,
        }

    def test_rendered_content_binds_approve_selection(self, success_session_orch):
        rendered = success_session_orch["last_preview"]["rendered_content"]
        assert "Selected option: approve" in rendered

    def test_rendered_content_does_not_contain_bad_evidence(self, success_session_orch):
        rendered = success_session_orch["last_preview"]["rendered_content"]
        assert WRONG_COMMIT_EVIDENCE_ID not in rendered
        assert FABRICATED_SHA_EVIDENCE_ID not in rendered


class TestReadinessPackageIdentity:
    def test_readiness_package_belongs_to_success_session_only(self, readiness_package):
        assert readiness_package["package"]["session_id"] == SUCCESS_SESSION_ID
        assert readiness_package["package"]["package_id"] == PACKAGE_ID

    def test_readiness_package_disposition_consumed(self, readiness_package):
        assert readiness_package["disposition"] == "consumed"

    def test_readiness_package_evidence_refs_exclude_bad_shas(self, readiness_package):
        refs = readiness_package["package"]["evidence_refs"]
        assert WRONG_COMMIT_EVIDENCE_ID not in refs
        assert FABRICATED_SHA_EVIDENCE_ID not in refs

    def test_no_second_readiness_package_directory_entry(self):
        consumed_dir = SESSIONS_DIR / "pending-packages" / "consumed"
        matches = list(consumed_dir.glob(f"{PACKAGE_ID}*.json"))
        assert len(matches) == 1


class TestPublicationContinuity:
    def test_published_handoff_references_correct_session_and_package(self, published_handoff):
        assert published_handoff["session_id"] == SUCCESS_SESSION_ID
        assert published_handoff["package_id"] == PACKAGE_ID
        assert published_handoff["record_id"] == DELL_CHGR_ID

    def test_readiness_package_record_id_matches_published_chgr(self, readiness_package):
        assert readiness_package["record_id"] == DELL_CHGR_ID


class TestSourceShaAuthenticity:
    def test_pinned_sha_is_40_hex_chars(self):
        assert len(PINNED_SOURCE_SHA) == 40
        int(PINNED_SOURCE_SHA, 16)  # raises if not hex

    def test_pinned_sha_resolves_to_a_real_commit_object(self):
        assert _run_git("cat-file", "-t", PINNED_SOURCE_SHA) == "commit"

    def test_pinned_sha_is_ancestor_of_current_head(self):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", PINNED_SOURCE_SHA, "HEAD"],
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0

    def test_pinned_sha_tree_contains_class_b_verifier_source(self):
        listing = _run_git("ls-tree", "-r", "--name-only", PINNED_SOURCE_SHA)
        assert "src/pcae/core/hatp_class_b_conformance.py" in listing
        assert "src/pcae/core/hatp_class_b_topology_verifier.py" in listing

    def test_pinned_sha_tree_contains_hbdc_req_042(self):
        content = _run_git(
            "show", f"{PINNED_SOURCE_SHA}:src/pcae/core/hatp_class_b_conformance.py"
        )
        assert "HBDC-REQ-042" in content


class TestSourceDrift:
    def test_no_src_pcae_paths_changed_since_pinned_sha(self):
        changed = _run_git("diff", "--name-only", f"{PINNED_SOURCE_SHA}..HEAD").splitlines()
        assert not any(p.startswith("src/pcae/") for p in changed)

    def test_no_scripts_paths_changed_since_pinned_sha(self):
        changed = _run_git("diff", "--name-only", f"{PINNED_SOURCE_SHA}..HEAD").splitlines()
        assert not any(p.startswith("scripts/") for p in changed)

    def test_no_docs_contracts_paths_changed_since_pinned_sha(self):
        changed = _run_git("diff", "--name-only", f"{PINNED_SOURCE_SHA}..HEAD").splitlines()
        assert not any(p.startswith("docs/contracts/") for p in changed)


class TestImmutableProposition:
    def test_immutable_7b1_commit_exists_and_is_a_commit(self):
        assert _run_git("cat-file", "-t", IMMUTABLE_7B1_COMMIT) == "commit"

    def test_immutable_7b1_commit_introduces_expected_document(self):
        changed = _run_git(
            "show", "--name-only", "--format=", IMMUTABLE_7B1_COMMIT
        ).splitlines()
        assert (
            "docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md"
            in changed
        )

    def test_pinned_historical_bytes_contain_nine_action_headers(self):
        content = _run_git(
            "show",
            f"{IMMUTABLE_7B1_COMMIT}:docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md",
        )
        for n in range(1, 10):
            assert f"### Action {n} " in content or f"### Action {n} —" in content.replace(
                "—", "—"
            ) or f"Action {n} " in content

    def test_pinned_historical_bytes_contain_action_9_residual_finding(self):
        content = _run_git(
            "show",
            f"{IMMUTABLE_7B1_COMMIT}:docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md",
        )
        assert "HBDC-REQ-042" in content
        assert "NON_COMPLIANT" in content


class TestWrapperDigest:
    def test_reported_wrapper_digest_is_64_hex_chars(self):
        # The orchestrating phase spec's own prose claimed this string
        # was 71 hex characters; independently measured, it is 64 --
        # the correct length for a SHA-256 hex digest. That prose/value
        # mismatch is documented as a finding in the phase report, not
        # silently corrected here.
        assert len(WRAPPER_DIGEST) == 64
        int(WRAPPER_DIGEST, 16)

    def test_recomputed_sha256_of_exact_wrapper_bytes_matches_reported_digest(self):
        computed = hashlib.sha256(WRAPPER_SCRIPT_BYTES).hexdigest()
        assert computed == WRAPPER_DIGEST

    def test_wrapper_bytes_are_exactly_188_bytes(self):
        assert len(WRAPPER_SCRIPT_BYTES) == 188

    def test_wrapper_bytes_contain_expected_semantics(self):
        text = WRAPPER_SCRIPT_BYTES.decode("ascii")
        assert "set -eu" in text
        assert "unset PYTHONPATH" in text
        assert "PYTHONNOUSERSITE=1" in text
        assert "PATH=/usr/bin:/bin:/usr/sbin:/sbin" in text
        assert 'exec /opt/pcae/runtime/venv/bin/pcae "$@"' in text
        assert "source" not in text
        assert ".bashrc" not in text
        assert ".profile" not in text


class TestActionNineAndDeploymentBindingSemantics:
    def test_verifier_source_treats_missing_deployment_binding_as_failure(self):
        content = _run_git(
            "show", f"{PINNED_SOURCE_SHA}:src/pcae/core/hatp_class_b_conformance.py"
        )
        assert "no_active_deployment_binding_matches_repository_and_root" in content

    def test_dell_chgr_rationale_discloses_action_9_residual_verbatim(self, dell_chgr):
        rationale = dell_chgr["rationale"]
        assert "HBDC-REQ-042" in rationale
        assert "DeploymentBinding" in rationale
        assert "intentionally absent" in rationale


class TestDeploymentBindingAndBoundaryExclusions:
    def test_conditions_exclude_deploymentbinding_creation(self, dell_chgr):
        assert "does not authorize DeploymentBinding creation" in dell_chgr["conditions"]

    def test_conditions_exclude_boundary_c_certification(self, dell_chgr):
        assert "Boundary C certification" in dell_chgr["conditions"]

    def test_conditions_exclude_boundary_a_activation(self, dell_chgr):
        assert "Boundary A activation" in dell_chgr["conditions"]

    def test_conditions_exclude_hatp_mandatory_activation(self, dell_chgr):
        assert "HATP_MANDATORY activation" in dell_chgr["conditions"]

    def test_conditions_exclude_cutover_record(self, dell_chgr):
        assert "Cutover Record creation" in dell_chgr["conditions"]

    def test_conditions_exclude_permission_broker_changes(self, dell_chgr):
        assert "Permission Broker changes" in dell_chgr["conditions"]

    def test_conditions_exclude_arbitrary_repository_onboarding(self, dell_chgr):
        assert "arbitrary repository onboarding" in dell_chgr["conditions"]

    def test_conditions_exclude_centralized_multi_repo_governance(self, dell_chgr):
        assert "centralized multi-repository governance" in dell_chgr["conditions"]

    def test_conditions_exclude_mac_provisioning(self, dell_chgr):
        assert "Mac provisioning" in dell_chgr["conditions"]


class TestCancelledSessionIsolation:
    def test_wrong_commit_session_state_cancelled(self):
        record = _load_json(SESSIONS_DIR / f"{WRONG_COMMIT_SESSION_ID}.json")["session"]
        assert record["session_state"] == "Cancelled"
        assert record["human_selection_id"] is None

    def test_fabricated_sha_session_state_cancelled(self):
        record = _load_json(SESSIONS_DIR / f"{FABRICATED_SHA_SESSION_ID}.json")["session"]
        assert record["session_state"] == "Cancelled"
        assert record["human_selection_id"] is None

    def test_wrong_commit_session_never_reached_preview_or_confirmation(
        self, wrong_commit_session_orch
    ):
        assert wrong_commit_session_orch["last_preview"] is None
        assert wrong_commit_session_orch["confirmation_responses"] == []
        assert "PreviewConstruction" not in wrong_commit_session_orch["completed_stages"]

    def test_fabricated_sha_session_never_reached_preview_or_confirmation(
        self, fabricated_sha_session_orch
    ):
        assert fabricated_sha_session_orch["last_preview"] is None
        assert fabricated_sha_session_orch["confirmation_responses"] == []
        assert "PreviewConstruction" not in fabricated_sha_session_orch["completed_stages"]

    def test_neither_cancelled_session_has_a_readiness_package(self):
        status_a = subprocess.run(
            ["python3", "-m", "pcae", "decision-session", "status", WRONG_COMMIT_SESSION_ID],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        status_b = subprocess.run(
            ["python3", "-m", "pcae", "decision-session", "status", FABRICATED_SHA_SESSION_ID],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert "readiness_package_status: none" in status_a.stdout
        assert "readiness_package_status: none" in status_b.stdout

    def test_no_chgr_file_exists_for_either_cancelled_session_id(self):
        for record_path in RECORDS_DIR.glob("chgr-*.json"):
            record = _load_json(record_path)
            assert record.get("record_id") not in (WRONG_COMMIT_SESSION_ID, FABRICATED_SHA_SESSION_ID)


class TestFabricatedShaNonContamination:
    def test_wrong_commit_evidence_id_is_a_real_but_wrong_commit(self):
        # It resolves as a real object (it is 149O.20L.7B.1's own
        # trailing "sync idle-task allowed-file list" commit) -- but it
        # is NOT the commit that introduced the 7B.1 proposition
        # document, so citing it as that evidence was an operator error,
        # not a fabrication.
        assert _run_git("cat-file", "-t", WRONG_COMMIT_EVIDENCE_ID) == "commit"
        assert WRONG_COMMIT_EVIDENCE_ID != IMMUTABLE_7B1_COMMIT

    def test_fabricated_sha_does_not_resolve_to_any_git_object(self):
        result = subprocess.run(
            ["git", "cat-file", "-t", FABRICATED_SHA_EVIDENCE_ID],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_fabricated_sha_shares_prefix_with_real_commit_but_is_not_it(self):
        assert FABRICATED_SHA_EVIDENCE_ID[:8] == IMMUTABLE_7B1_COMMIT[:8]
        assert FABRICATED_SHA_EVIDENCE_ID != IMMUTABLE_7B1_COMMIT

    def test_neither_bad_evidence_id_appears_in_success_session_evidence(
        self, success_session_orch
    ):
        evidence_ids = {e["evidence_id"] for e in success_session_orch["evidence"]}
        assert WRONG_COMMIT_EVIDENCE_ID not in evidence_ids
        assert FABRICATED_SHA_EVIDENCE_ID not in evidence_ids
        assert evidence_ids == {PINNED_SOURCE_SHA, WRAPPER_DIGEST, IMMUTABLE_7B1_COMMIT}

    def test_neither_bad_evidence_id_appears_in_dell_chgr_bytes(self, dell_chgr):
        raw = json.dumps(dell_chgr)
        assert WRONG_COMMIT_EVIDENCE_ID not in raw
        assert FABRICATED_SHA_EVIDENCE_ID not in raw

    def test_neither_bad_evidence_id_appears_in_readiness_package(self, readiness_package):
        raw = json.dumps(readiness_package)
        assert WRONG_COMMIT_EVIDENCE_ID not in raw
        assert FABRICATED_SHA_EVIDENCE_ID not in raw


class TestMacChgrSeparation:
    def test_mac_chgr_file_exists(self):
        assert MAC_CHGR_PATH.is_file()

    def test_mac_chgr_distinct_id_from_dell_chgr(self):
        assert MAC_CHGR_ID != DELL_CHGR_ID

    def test_mac_chgr_still_published_approve(self, mac_chgr):
        assert mac_chgr["lifecycle_state"] == "published"
        assert mac_chgr["selected_option_id"] == "approve"

    def test_mac_chgr_names_mac_not_dell(self, mac_chgr):
        assert "Atilas-MacBook-Pro.local" in mac_chgr["decision_subject"]
        assert DELL_MACHINE_ID not in mac_chgr["decision_subject"]

    def test_mac_chgr_carries_no_revocation_or_supersession_markers(self, mac_chgr):
        raw = json.dumps(mac_chgr).lower()
        assert "revok" not in raw
        assert "supersed" not in raw


class TestAmendSessionSeparation:
    def test_amend_session_still_records_amend(self, amend_session):
        assert amend_session["human_selection_id"] == "amend"

    def test_amend_session_not_part_of_success_evidence_or_confirmation(
        self, success_session_orch
    ):
        raw = json.dumps(success_session_orch)
        assert AMEND_SESSION_ID not in raw

    def test_amend_session_names_dell_but_is_a_distinct_subject_ref(
        self, amend_session, success_session
    ):
        assert DELL_MACHINE_ID in amend_session["subject_ref"]
        assert amend_session["subject_ref"] != success_session["subject_ref"]


class TestChgrVerifyResult:
    def _related_paths(self, chgr: dict) -> list:
        return [
            str(RECORDS_DIR / f"{chgr['confirmation_evidence_ref']['record_id']}.json"),
            str(RECORDS_DIR / f"{chgr['provenance_ref']['record_id']}.json"),
            str(RECORDS_DIR / f"{chgr['integrity_ref']['record_id']}.json"),
        ]

    def test_dell_chgr_verify_returns_verified_with_seven_of_seven_substantive_passes(
        self, dell_chgr
    ):
        cmd = [
            "python3",
            "-m",
            "pcae",
            "governance-record",
            "verify",
            str(DELL_CHGR_PATH),
        ]
        for related in self._related_paths(dell_chgr):
            cmd.extend(["--related", related])
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        assert result.returncode == 0
        assert "outcome: verified" in result.stdout
        substantive_checks = [
            "schema_shape",
            "digest_self_consistency",
            "lifecycle_structural_legality",
            "confirmation_binding",
            "assurance_truthfulness",
            "provenance_consistency",
            "integrity_consistency",
        ]
        for check in substantive_checks:
            assert f"check: {check}" in result.stdout
        for check in substantive_checks:
            idx = result.stdout.index(f"check: {check}")
            line = result.stdout[idx : idx + 200].splitlines()[0]
            assert "passed" in line

    def test_template_resolution_skipped_not_silently_dropped(self, dell_chgr):
        cmd = [
            "python3",
            "-m",
            "pcae",
            "governance-record",
            "verify",
            str(DELL_CHGR_PATH),
        ]
        for related in self._related_paths(dell_chgr):
            cmd.extend(["--related", related])
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        assert "check: template_resolution" in result.stdout
        assert "skipped" in result.stdout

    def test_mac_chgr_exhibits_identical_template_resolution_skip(self, mac_chgr):
        cmd = [
            "python3",
            "-m",
            "pcae",
            "governance-record",
            "verify",
            str(MAC_CHGR_PATH),
        ]
        for related in self._related_paths(mac_chgr):
            cmd.extend(["--related", related])
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        assert "check: template_resolution" in result.stdout
        assert "skipped" in result.stdout


class TestRevocationAndSupersession:
    def test_no_revocation_registry_exists_anywhere_in_pcae_state(self):
        matches = list(PCAE_DIR.glob("**/*revoc*")) + list(PCAE_DIR.glob("**/*supersed*"))
        assert matches == []

    def test_dell_chgr_bytes_contain_no_revocation_or_supersession_marker(self, dell_chgr):
        raw = json.dumps(dell_chgr).lower()
        assert "revok" not in raw
        assert "supersed" not in raw


class TestNoHostMutationEvidence:
    def test_no_provisioning_verbs_appear_in_any_persisted_session_or_chgr_artifact(self):
        forbidden = ("useradd pcae", "groupadd pcae", "mkdir -p /opt/pcae", "apt-get install")
        for path in list(SESSIONS_DIR.glob("*.json")) + list(RECORDS_DIR.glob("*.json")):
            raw = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                assert phrase not in raw, f"{path} unexpectedly contains {phrase!r}"

    def test_no_pcae_or_src_pcae_paths_dirtied_by_running_this_module(self):
        status_lines = _run_git("status", "--short").splitlines()
        # This module performs read-only git/subprocess calls only.
        # New phase-deliverable files (this test module, the phase
        # report) are expected to show as untracked -- but no existing
        # governance state (.pcae/**) or production source (src/pcae/**)
        # may be modified by running it.
        for line in status_lines:
            path = line[3:]
            assert not path.startswith(".pcae/"), f"unexpected .pcae mutation: {line}"
            assert not path.startswith("src/pcae/"), f"unexpected src/pcae mutation: {line}"
