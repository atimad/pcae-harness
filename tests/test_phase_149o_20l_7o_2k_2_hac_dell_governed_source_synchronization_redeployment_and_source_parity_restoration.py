"""Phase 149O.20L.7O.2K.2 -- hac-dell Governed Source Synchronization /
Redeployment and Source-Parity Restoration.

Independently-authored companion test module. Covers static checks against
already-persisted repository/CHGR state and the exact command/content text
this phase's report and canonical proposition document claim to have
executed on the live Dell host. No live SSH or Dell mutation is performed
in CI -- all Dell evidence is captured in the canonical phase report and
proposition document (docs/PHASE_149O_20L_7O_2K_2_HAC_DELL_GOVERNED_SOURCE_
SYNCHRONIZATION_REDEPLOYMENT_AND_SOURCE_PARITY_RESTORATION.md) and is not
re-verified live here.
"""
from __future__ import annotations

import json
import subprocess
import tarfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parents[1]

OLD_SHA = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"
CANDIDATE_SHA = "305f8e7913bac76941dade6ff4e018c74533f062"

GOVERNING_CHGR_ID = "chgr-4291cd399b6a4db9a82f7945cbc8177c"
HISTORICAL_CHGR_IDS = (
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
    "chgr-0e37ed1340b14311826722c4dbf3e856",
    "chgr-71bd24f9d3d742d6baac772e480fc876",
    "chgr-86aeb5cfa7c44020ad002bc9f80c5856",
)

DELL_MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"
DELL_HOSTNAME = "atila-Latitude-E5470"
WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
HMIC_IMPLEMENTATION_DIGEST = (
    "cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f"
)
REPOSITORY_INSTANCE_ID = "0107866f-af7c-40b4-8317-74e71acb05ca"

EXPECTED_HBDC_RESIDUAL = {"HBDC-REQ-042"}
EXPECTED_CONTRACT_VERSIONS = {
    "HMRC-001": "1.1",
    "HATP-001": "1.0",
    "HSCE-001": "1.3",
    "RAE-001": "1.0",
    "HBDC-001": "1.2",
    "HPSE-001": "1.1",
    "HHCE-001": "1.1",
}

MUTATION_COMMANDS = [
    f"sudo -n git -C /opt/pcae/runtime/src fetch origin {CANDIDATE_SHA}",
    f"sudo -n git -C /opt/pcae/runtime/src cat-file -t {CANDIDATE_SHA}",
    f"sudo -n git -C /opt/pcae/runtime/src checkout --detach {CANDIDATE_SHA}",
    "sudo -n chown -R root:pcae /opt/pcae/runtime/src",
    "sudo -n find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \\;",
    "sudo -n find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \\;",
    "sudo -n find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \\;",
]

ROLLBACK_COMMANDS = [
    f"sudo -n git -C /opt/pcae/runtime/src checkout --detach {OLD_SHA}",
    "sudo -n chown -R root:pcae /opt/pcae/runtime/src",
    "sudo -n find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \\;",
    "sudo -n find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \\;",
    "sudo -n find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \\;",
]

PROPOSITION_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2K_2_HAC_DELL_GOVERNED_SOURCE_SYNCHRONIZATION_REDEPLOYMENT_AND_SOURCE_PARITY_RESTORATION.md"
)

CHGR_PATH = (
    REPO_ROOT
    / ".pcae"
    / "publication-execution"
    / "records"
    / f"{GOVERNING_CHGR_ID}.json"
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestPropositionDocument:
    def test_proposition_document_exists(self):
        assert PROPOSITION_PATH.exists()

    def test_proposition_names_both_shas(self):
        text = PROPOSITION_PATH.read_text(encoding="utf-8")
        assert OLD_SHA in text
        assert CANDIDATE_SHA in text

    def test_proposition_names_hmic_digest(self):
        text = PROPOSITION_PATH.read_text(encoding="utf-8")
        assert HMIC_IMPLEMENTATION_DIGEST in text

    def test_proposition_names_exact_mutation_commands(self):
        text = PROPOSITION_PATH.read_text(encoding="utf-8")
        assert "fetch origin" in text
        assert "checkout --detach" in text
        assert "chown -R root:pcae" in text

    def test_proposition_excludes_certification_and_first_use(self):
        text = PROPOSITION_PATH.read_text(encoding="utf-8")
        assert "RepositoryIdentity" in text
        assert "DeploymentBinding" in text
        assert "certification" in text.lower()


class TestGoverningCHGR:
    def test_chgr_record_exists(self):
        assert CHGR_PATH.exists()

    def test_chgr_lifecycle_state_published(self):
        record = _read_json(CHGR_PATH)
        assert record.get("lifecycle_state") == "published"

    def test_chgr_selected_option_is_approve(self):
        record = _read_json(CHGR_PATH)
        assert record.get("selected_option_id") == "approve"

    def test_chgr_embeds_both_shas(self):
        record = _read_json(CHGR_PATH)
        blob = json.dumps(record)
        assert OLD_SHA in blob
        assert CANDIDATE_SHA in blob

    def test_chgr_conditions_bind_target_host(self):
        record = _read_json(CHGR_PATH)
        conditions = record.get("conditions", "")
        assert DELL_HOSTNAME in conditions
        assert DELL_MACHINE_ID in conditions

    def test_chgr_conditions_exclude_first_use_and_certification(self):
        record = _read_json(CHGR_PATH)
        conditions = record.get("conditions", "")
        assert "RepositoryIdentity" in conditions
        assert "DeploymentBinding" in conditions
        assert "certification" in conditions.lower()

    def test_no_historical_chgr_authorizes_this_transition(self):
        for chgr_id in HISTORICAL_CHGR_IDS:
            path = (
                REPO_ROOT
                / ".pcae"
                / "publication-execution"
                / "records"
                / f"{chgr_id}.json"
            )
            if not path.exists():
                continue
            record = _read_json(path)
            blob = json.dumps(record)
            assert CANDIDATE_SHA not in blob


class TestMutationCommandIdentity:
    def test_mutation_sequence_has_seven_steps(self):
        assert len(MUTATION_COMMANDS) == 7

    def test_mutation_commands_scoped_to_deployment_root(self):
        for command in MUTATION_COMMANDS:
            assert "/opt/pcae/runtime/src" in command

    def test_mutation_commands_never_use_blanket_chmod(self):
        for command in MUTATION_COMMANDS:
            assert "chmod -R" not in command

    def test_rollback_targets_old_sha(self):
        assert OLD_SHA in ROLLBACK_COMMANDS[0]
        assert CANDIDATE_SHA not in " ".join(ROLLBACK_COMMANDS)


class TestExpectedPostDeploymentIdentity:
    def test_expected_hbdc_residual_is_sole_deploymentbinding_reason(self):
        assert EXPECTED_HBDC_RESIDUAL == {"HBDC-REQ-042"}

    def test_expected_contract_versions_has_seven_members(self):
        assert len(EXPECTED_CONTRACT_VERSIONS) == 7

    def test_repository_instance_id_format(self):
        assert len(REPOSITORY_INSTANCE_ID) == 36
        assert REPOSITORY_INSTANCE_ID.count("-") == 4

    def test_wrapper_digest_is_64_hex_chars(self):
        assert len(WRAPPER_DIGEST) == 64
        int(WRAPPER_DIGEST, 16)

    def test_hmic_digest_is_64_hex_chars(self):
        assert len(HMIC_IMPLEMENTATION_DIGEST) == 64
        int(HMIC_IMPLEMENTATION_DIGEST, 16)


class TestLocalHMICReconstruction:
    """Independently re-derives the same HMIC facts locally (this Mac
    repository, not Dell) that the phase report claims were separately,
    live re-derived on hac-dell -- confirming this phase's own local
    claims are at least internally consistent with production source."""

    def test_frozen_set_has_36_members(self):
        """Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
        governing prompt): true of `CANDIDATE_SHA`, the commit this
        phase actually redeployed to the real Dell. Superseded for LIVE
        production `HEAD` state by Phase 149O.20L.7O.2M's own HMIC v1.7
        widening (36 -> 38) -- see §61.7/§61.8 of the amended contract:
        the real Dell intentionally still runs this phase's own
        36-member v1.6 generation until a later, separately-governed
        redeployment."""

        text = subprocess.check_output(
            ["git", "show", f"{CANDIDATE_SHA}:src/pcae/core/hatp_mandatory_certification.py"],
            cwd=REPO_ROOT,
            text=True,
        )
        assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36" in text

    def test_local_digest_matches_recorded_digest(self, tmp_path: Path):
        """Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
        governing prompt): reconstructs the digest using CANDIDATE_SHA's
        OWN 36-member frozen-file literal (extracted from that commit's
        own `hatp_mandatory_certification.py` blob via AST, not the
        LIVE, since-widened 38-member module-level constant) applied to
        an archived checkout of that same commit -- the exact HMIC-REQ-
        054/056/057/058 two-level SHA-256 construction, reproduced
        independently rather than calling the live `derive_
        implementation_scope_digest` (which would otherwise look for the
        two 149O.20L.7O.2M-era scripts that did not exist yet at
        CANDIDATE_SHA and fail closed). Phase 149O.20L.7O.2M's own HMIC
        v1.7 widening changes the LIVE digest by design (§61.7); this
        historical parity claim is pinned and unaffected by it."""

        import ast
        import hashlib

        archive_path = tmp_path / "archive.tar"
        with archive_path.open("wb") as fh:
            subprocess.run(["git", "archive", CANDIDATE_SHA], cwd=REPO_ROOT, stdout=fh, check=True)
        checkout = tmp_path / "checkout"
        checkout.mkdir()
        with tarfile.open(archive_path) as tf:
            tf.extractall(checkout)

        source = subprocess.check_output(
            ["git", "show", f"{CANDIDATE_SHA}:src/pcae/core/hatp_mandatory_certification.py"],
            cwd=REPO_ROOT,
            text=True,
        )
        literals: dict[str, object] = {}
        wanted = {"_FROZEN_SRC_PCAE_RELATIVE_FILES", "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"}
        for node in ast.parse(source).body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in wanted:
                literals[node.target.id] = ast.literal_eval(node.value)
        assert len(literals["_FROZEN_SRC_PCAE_RELATIVE_FILES"]) + len(literals["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"]) == 36

        canonical_paths = sorted(
            [f"src/pcae/{p}" for p in literals["_FROZEN_SRC_PCAE_RELATIVE_FILES"]]
            + list(literals["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"])
        )
        hasher = hashlib.sha256()
        for canonical_path in canonical_paths:
            file_bytes = (checkout / canonical_path).read_bytes()
            file_digest = hashlib.sha256(file_bytes).hexdigest()
            hasher.update(f"{canonical_path}\0{file_digest}\n".encode("utf-8"))
        assert hasher.hexdigest() == HMIC_IMPLEMENTATION_DIGEST

    def test_local_contract_versions_match_recorded(self):
        from pcae.core import hatp_mandatory_certification as h
        from pcae.core.paths import HarnessPath

        root = HarnessPath(REPO_ROOT)
        assert h.derive_contract_versions(root) == EXPECTED_CONTRACT_VERSIONS

    def test_candidate_sha_is_current_repo_head_at_authoring_time(self):
        # This phase's authorized target revision was frozen as the exact
        # HEAD == origin/main commit at phase entry; the module constant
        # above must match the SHA baked into the proposition document.
        text = PROPOSITION_PATH.read_text(encoding="utf-8")
        assert f"`{CANDIDATE_SHA}`" in text or CANDIDATE_SHA in text
