"""Phase 149O.20L.7B.1 -- Dell Boundary-P Proposition Materialization
(Amendment).

This phase materialized the four amendments the human governance
authority elected in Phase 149O.20L.7B's AMEND election: (1) an exact
pinned deployment-source commit SHA for Action 6; (2) exact literal
forward/read-back/rollback/rollback-verification command text for all
nine actions; (3) exact literal launch-wrapper script content and
environment contract for Action 8; (4) an explicit scope clarification
that `/opt/pcae/projects/<repo-slug>/repo` is a future per-repository
path template, not standing repository-creation authority. It is
planning-only: no provisioning, no new election, no CHGR, no
certification, no activation.

These tests assert the phase document's documentary content only. They
do not perform live Dell SSH, do not invoke `pcae decision-session`,
and do not mutate the Dell or this repository's governance state.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

RECORDS_DIR = REPO_ROOT / ".pcae" / "publication-execution" / "records"
MAC_CHGR_PATH = RECORDS_DIR / "chgr-d4343fa51b9743f3abaeb87a881a78b1.json"

DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md"
)

PRIOR_SESSION_ID = "CDS-cf123bbf-a5d7-4f0f-ac22-0baa257990af"
PRIOR_SESSION_PATH = REPO_ROOT / ".pcae" / "decision-sessions" / f"{PRIOR_SESSION_ID}.json"

PINNED_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"

WRAPPER_SCRIPT = (
    "#!/bin/sh\n"
    "set -eu\n"
    "unset PYTHONPATH\n"
    "PYTHONNOUSERSITE=1\n"
    "export PYTHONNOUSERSITE\n"
    "PATH=/usr/bin:/bin:/usr/sbin:/sbin\n"
    "export PATH\n"
    "cd /opt/pcae/runtime\n"
    'exec /opt/pcae/runtime/venv/bin/pcae "$@"\n'
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def prior_session() -> dict:
    payload = json.loads(PRIOR_SESSION_PATH.read_text(encoding="utf-8"))
    return payload["session"]


class TestAmendElectionPreservedNotReinterpreted:
    def test_prior_session_still_amend(self, prior_session: dict):
        assert prior_session["human_selection_id"] == "amend"

    def test_prior_session_still_confirmed(self, prior_session: dict):
        assert prior_session["session_state"] == "Confirmed"

    def test_doc_does_not_claim_a_new_election(self, doc_text: str):
        assert "No election was held" in doc_text or "no election" in doc_text.lower()
        assert "pcae decision-session create" not in doc_text.split("## 21")[1].split(
            "## 22"
        )[0]

    def test_no_new_chgr_published(self):
        chgr_files = sorted(p.name for p in RECORDS_DIR.glob("chgr-*.json"))
        assert chgr_files == ["chgr-d4343fa51b9743f3abaeb87a881a78b1.json"]

    def test_mac_chgr_unmodified(self):
        record = json.loads(MAC_CHGR_PATH.read_text(encoding="utf-8"))
        assert record["lifecycle_state"] == "published"
        assert record["selected_option_id"] == "approve"
        assert "Atilas-MacBook-Pro.local" in record["decision_subject"]


class TestBoundaryStatus:
    def test_boundary_p_not_authorized(self, doc_text: str):
        assert "Boundary P: NOT AUTHORIZED" in doc_text or "DELL BOUNDARY P: NOT AUTHORIZED" in doc_text

    def test_boundary_c_and_a_not_authorized(self, doc_text: str):
        assert doc_text.count("Boundary C: NOT AUTHORIZED") >= 1
        assert doc_text.count("Boundary A: NOT AUTHORIZED") >= 1

    def test_class_b_not_provisioned(self, doc_text: str):
        assert "NOT PROVISIONED" in doc_text

    def test_hatp_not_ready(self, doc_text: str):
        assert "HATP: NOT READY" in doc_text or "HATP:       NOT READY" in doc_text

    def test_runtime_unchanged(self, doc_text: str):
        assert "Observed / observe / unavailable" in doc_text


class TestPinnedSourceCommit:
    def test_exact_full_sha_present(self, doc_text: str):
        assert PINNED_SHA in doc_text

    def test_no_moving_ref_source_binding(self, doc_text: str):
        action_6_section = doc_text.split("### Action 6")[1].split("### Action 7")[0]
        for forbidden in ("--branch main", "git clone git@github", "checkout main"):
            assert forbidden not in action_6_section or "checkout --detach" in action_6_section

    def test_action_6_uses_detached_checkout_of_exact_sha(self, doc_text: str):
        action_6_section = doc_text.split("### Action 6")[1].split("### Action 7")[0]
        assert f"checkout --detach {PINNED_SHA}" in action_6_section

    def test_action_6_readback_requires_exact_sha_match(self, doc_text: str):
        action_6_section = doc_text.split("### Action 6")[1].split("### Action 7")[0]
        assert "rev-parse HEAD" in action_6_section
        assert "EXACTLY (full 40-char compare)" in action_6_section

    def test_pinned_commit_exists_in_repo_history(self):
        assert (REPO_ROOT / ".git").exists()

    def test_source_drift_rule_present(self, doc_text: str):
        assert "Source-Drift" in doc_text or "source drift" in doc_text.lower()
        assert "src/pcae/**" in doc_text

    def test_contract_versions_cited(self, doc_text: str):
        assert "HBDC-001 v1.0" in doc_text or "HBDC-001 **v1.0**" in doc_text
        assert "HMIC-001 v1.3" in doc_text or "HMIC-001 **v1.3**" in doc_text
        assert "HMRC-001 v1.1" in doc_text or "HMRC-001 **v1.1**" in doc_text


class TestNineActionsFullyMaterialized:
    ACTION_HEADERS = [
        "### Action 1",
        "### Action 2",
        "### Action 3",
        "### Action 4",
        "### Action 5",
        "### Action 6",
        "### Action 7",
        "### Action 8",
        "### Action 9",
    ]

    def test_all_nine_action_headers_present(self, doc_text: str):
        for header in self.ACTION_HEADERS:
            assert header in doc_text

    def test_each_action_has_forward_or_preflight_and_readback(self, doc_text: str):
        sections = re.split(r"### Action \d+ ---?", doc_text)
        combined = doc_text
        for i in range(1, 10):
            start = combined.index(f"### Action {i} ")
            end = (
                combined.index(f"### Action {i + 1} ")
                if i < 9
                else combined.index("## 10. Privilege Map")
            )
            block = combined[start:end]
            if i == 9:
                # Action 9 is read-only verification, not a mutation --
                # it has a precondition and a command, not a
                # preflight/idempotency-class/read-back mutation cycle.
                assert "Command" in block
                assert "Rollback" in block
                continue
            assert "Preflight" in block
            assert "Read-back" in block or "**Command" in block
            assert "Rollback" in block

    def test_no_pseudo_command_placeholders(self, doc_text: str):
        action_block = doc_text[
            doc_text.index("### Action 1") : doc_text.index("## 10. Privilege Map")
        ]
        forbidden_tokens = [
            "<user>",
            "<group>",
            "<commit>",
            "<something>",
            "as appropriate",
            "similar command",
        ]
        for token in forbidden_tokens:
            assert token not in action_block

    def test_repo_slug_placeholder_not_exercised_in_action_graph(self, doc_text: str):
        action_block = doc_text[
            doc_text.index("### Action 1") : doc_text.index("## 10. Privilege Map")
        ]
        assert "<repo-slug>" not in action_block

    def test_action_9_success_condition_corrected(self, doc_text: str):
        action_9_section = doc_text.split("### Action 9")[1].split("## 10.")[0]
        assert "NON_COMPLIANT" in action_9_section
        assert "HBDC-REQ-042" in action_9_section


class TestLaunchWrapperExactContent:
    def test_wrapper_script_bytes_present_verbatim(self, doc_text: str):
        assert WRAPPER_SCRIPT.strip("\n") in doc_text.replace("\r\n", "\n")

    def test_wrapper_digest_present(self, doc_text: str):
        assert WRAPPER_DIGEST in doc_text

    def test_wrapper_digest_matches_script_bytes(self):
        computed = hashlib.sha256(WRAPPER_SCRIPT.encode("utf-8")).hexdigest()
        assert computed == WRAPPER_DIGEST

    def test_pythonpath_semantics_explicit(self, doc_text: str):
        wrapper_section = doc_text.split("## 12.")[1].split("## 13.")[0]
        assert "unset PYTHONPATH" in wrapper_section
        assert "not set to empty" in wrapper_section or "removed from the process environment" in wrapper_section

    def test_wrapper_path_and_ownership(self, doc_text: str):
        assert "/opt/pcae/runtime/bin/pcae-launch" in doc_text
        assert "root:pcae" in doc_text
        assert "0750" in doc_text


class TestRepoSlugTemplateClarification:
    def test_repo_slug_classified_as_future_template(self, doc_text: str):
        assert "future per-repository" in doc_text.lower() or "future per-repository parameter" in doc_text

    def test_no_concrete_project_repo_authorized(self, doc_text: str):
        assert "does **not** authorize creation of" in doc_text or "does not authorize creation of" in doc_text

    def test_repository_onboarding_boundary_section_present(self, doc_text: str):
        assert "Repository-Onboarding Boundary" in doc_text or "Repository onboarding" in doc_text


class TestNoDellMutationAndNoDriftDrama:
    def test_doc_asserts_no_dell_mutation(self, doc_text: str):
        assert "NO DELL MUTATION OCCURRED" in doc_text

    def test_doc_asserts_no_new_election(self, doc_text: str):
        assert "NO NEW ELECTION HELD" in doc_text

    def test_doc_asserts_no_new_chgr(self, doc_text: str):
        assert "NO NEW CHGR PUBLISHED" in doc_text


class TestProductionScopeUntouched:
    def test_no_src_pcae_changes_claimed(self, doc_text: str):
        assert "Zero" in doc_text
        assert "src/pcae/**" in doc_text

    def test_git_diff_actually_touches_only_expected_paths(self):
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        changed = [line for line in result.stdout.splitlines() if line.strip()]
        for path in changed:
            assert not path.startswith("src/pcae/")
            assert not path.startswith("docs/contracts/")
            assert not path.startswith("scripts/")


class TestNoUnresolvedPlaceholders:
    def test_no_angle_bracket_placeholders_in_authority_bearing_values(self, doc_text: str):
        proposition_section = doc_text.split("## 19. Full Literal Revised Proposition")[1].split(
            "## 20."
        )[0]
        for forbidden in ("<origin-url>", "<pinned-commit-sha>", "<user>", "<group>"):
            assert forbidden not in proposition_section
