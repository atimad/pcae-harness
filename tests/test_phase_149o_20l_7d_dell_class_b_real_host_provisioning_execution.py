"""Phase 149O.20L.7D -- Dell Class-B Real Host Provisioning Execution.

This phase attempted real provisioning of the Dell under CHGR
`chgr-96a0ce12756e4cc892492a87af1db832`. Actions 1-5 of the frozen
149O.20L.7B.1 nine-action plan were executed live over SSH and
independently verified against the Dell, then rolled back (Action 6 was
blocked by a missing, out-of-scope GitHub deploy key). Net Dell mutation
is zero; no DeploymentBinding, certification, or activation was
attempted.

This module does not re-run live SSH mutation or rollback -- that is
inherently a live-host, non-deterministic operation unsuitable for CI --
and instead independently re-derives the static, already-persisted
repository facts this phase's report
(`docs/PHASE_149O_20L_7D_DELL_CLASS_B_REAL_HOST_PROVISIONING_EXECUTION.md`)
depends on: the CHGR record's content and integrity, the pinned source
commit's existence and freshness, the exact wrapper script bytes/digest,
and the contract versions bound at the pin. No Dell mutation is
performed by this module -- it reads only already-persisted local
artifacts and immutable git history.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

CHGR_ID = "chgr-96a0ce12756e4cc892492a87af1db832"
CHGR_PATH = (
    REPO_ROOT / ".pcae" / "publication-execution" / "records" / f"{CHGR_ID}.json"
)

PINNED_SOURCE_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
IMMUTABLE_7B1_COMMIT = "f9e33232c83163aad5e50bc94db7cab51b844ac5"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"

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

PHASE_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7D_DELL_CLASS_B_REAL_HOST_PROVISIONING_EXECUTION.md"
)


def _git_show(ref: str) -> str:
    return subprocess.run(
        ["git", "show", ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _git_cat_file_type(ref: str) -> str:
    return subprocess.run(
        ["git", "cat-file", "-t", ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


class TestWrapperBytesAndDigest:
    def test_wrapper_is_exactly_188_bytes(self) -> None:
        assert len(WRAPPER_SCRIPT_BYTES) == 188

    def test_wrapper_digest_matches_chgr_and_7b1(self) -> None:
        assert hashlib.sha256(WRAPPER_SCRIPT_BYTES).hexdigest() == WRAPPER_DIGEST

    def test_wrapper_bytes_match_frozen_7b1_commit(self) -> None:
        doc = _git_show(
            f"{IMMUTABLE_7B1_COMMIT}:"
            "docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md"
        )
        assert WRAPPER_DIGEST in doc
        for line in (
            "#!/bin/sh",
            "set -eu",
            "unset PYTHONPATH",
            "PYTHONNOUSERSITE=1",
            "export PYTHONNOUSERSITE",
            "PATH=/usr/bin:/bin:/usr/sbin:/sbin",
            "export PATH",
            "cd /opt/pcae/runtime",
            'exec /opt/pcae/runtime/venv/bin/pcae "$@"',
        ):
            assert line in doc


class TestChgrRecordIntegrity:
    def test_chgr_record_exists(self) -> None:
        assert CHGR_PATH.is_file()

    def test_chgr_record_published_and_approved(self) -> None:
        record = json.loads(CHGR_PATH.read_text())
        assert record["record_id"] == CHGR_ID
        assert record["lifecycle_state"] == "published"
        assert record["selected_option_id"] == "approve"
        assert record["decision_maker_identity_evidence"]["identifier"] == (
            "Atila Madai"
        )

    def test_chgr_record_cites_correct_target_and_pin(self) -> None:
        record = json.loads(CHGR_PATH.read_text())
        assert DELL_MACHINE_ID in record["decision_subject"]
        assert PINNED_SOURCE_SHA in record["rationale"]

    def test_chgr_conditions_exclude_boundary_c_a_and_deployment_binding(
        self,
    ) -> None:
        record = json.loads(CHGR_PATH.read_text())
        conditions = record["conditions"].lower()
        for excluded in (
            "deploymentbinding",
            "boundary c",
            "boundary a",
            "hatp_mandatory",
            "cutover record",
            "permission broker",
            "unrelated dell mutation",
            "arbitrary repository onboarding",
            "mac provisioning",
            "centralized multi-repository governance",
        ):
            assert excluded in conditions

    def test_chgr_record_unmodified_by_this_phase(self) -> None:
        result = subprocess.run(
            ["git", "status", "--porcelain", str(CHGR_PATH)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ""


class TestSourcePinFreshness:
    def test_pinned_commit_exists(self) -> None:
        assert _git_cat_file_type(PINNED_SOURCE_SHA) == "commit"

    def test_immutable_7b1_commit_exists(self) -> None:
        assert _git_cat_file_type(IMMUTABLE_7B1_COMMIT) == "commit"

    def test_no_authority_relevant_drift_since_pin(self) -> None:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--stat",
                f"{PINNED_SOURCE_SHA}..HEAD",
                "--",
                "src/pcae",
                "docs/contracts",
                "scripts",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ""

    def test_pin_contains_expected_contract_versions(self) -> None:
        hbdc = _git_show(
            f"{PINNED_SOURCE_SHA}:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
        )
        assert "**Contract:** HBDC-001" in hbdc
        hbdc_normalized = " ".join(hbdc.split())
        assert "Contract:** HBDC-001" in hbdc_normalized
        assert "Version:** 1.0" in hbdc_normalized

        hmic = _git_show(
            f"{PINNED_SOURCE_SHA}:"
            "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
        )
        assert "**Version:** 1.3" in hmic
        assert "HMRC-001 v1.1" in hmic

    def test_pin_contains_class_b_verifier_sources(self) -> None:
        result = subprocess.run(
            [
                "git",
                "ls-tree",
                "-r",
                "--name-only",
                PINNED_SOURCE_SHA,
                "--",
                "src/pcae",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        names = result.stdout.splitlines()
        assert "src/pcae/core/hatp_class_b_conformance.py" in names
        assert "src/pcae/core/hatp_class_b_topology_verifier.py" in names


class TestPhaseReportRecordsBlockedNetZeroOutcome:
    def test_phase_doc_exists(self) -> None:
        assert PHASE_DOC_PATH.is_file()

    def test_phase_doc_states_blocked_net_zero_mutation(self) -> None:
        text = PHASE_DOC_PATH.read_text()
        normalized = " ".join(text.split())
        assert "blocked" in text.lower()
        assert "Net Dell mutation: none." in normalized
        assert "Net persistent Dell state change: none." in normalized

    def test_phase_doc_records_action6_blocker_reason(self) -> None:
        text = PHASE_DOC_PATH.read_text()
        assert "deploy" in text.lower() and "key" in text.lower()
        assert "github.com" in text

    def test_phase_doc_does_not_claim_deployment_binding_or_certification(
        self,
    ) -> None:
        text = PHASE_DOC_PATH.read_text()
        assert "No `DeploymentBinding`, certification pointer" in text
        assert "Boundary C:** NOT AUTHORIZED" in text
        assert "Boundary A:** NOT AUTHORIZED" in text

    def test_phase_doc_records_wrapper_digest(self) -> None:
        text = PHASE_DOC_PATH.read_text()
        assert WRAPPER_DIGEST in text

    def test_phase_doc_recommends_retry_not_independent_verification(self) -> None:
        text = PHASE_DOC_PATH.read_text()
        assert "149O.20L.7D.1" in text
        assert "149O.20L.7E" in text


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
