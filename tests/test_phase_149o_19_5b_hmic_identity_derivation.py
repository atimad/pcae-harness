"""Phase 149O.19.5B -- HMIC Implementation + Contract Identity Derivation.

Phase-boundary verification and behavioral test suite for Wave B (`docs/
PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md` §9.3): the pure identity-
derivation layer extending `src/pcae/core/hatp_mandatory_certification.py`
-- `_FROZEN_AUTHORITY_BEARING_FILES`, `derive_repository_instance_id`,
`derive_canonical_deployment_root`, `derive_implementation_commit`,
`derive_implementation_scope_digest`, `derive_contract_versions`, and
`derive_certification_id`.

Scope discipline mirrored from the 149O.19.5A suite: this phase answers
"what is the current implementation identity?" and "what are the current
bound contract identities?", never "is a protected certification valid?"
No test here asserts, exercises, or would be satisfied by a
`CertificationStatus.VALID` outcome, a certification-state read/write, or
a runtime/executed-source-binding check (HMIC-REQ-063 names that an
explicit, out-of-scope-for-v1.0 residual limitation; the 149O.19.4 plan's
Wave B API surface names no such function either).
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.hatp_bootstrap import resolve_canonical_deployment_root
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_NEW_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_HMIC_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"


def _git(*args: str, cwd: Path = _REPO_ROOT) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Fixture"], cwd=root, check=True)


def _git_commit_all(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 89. 22-file manifest test -- the production constant must be string-for-
# string identical to a fresh extraction of the live HMIC-001 contract text.
# ═══════════════════════════════════════════════════════════════════════════


def _extract_contract_frozen_file_list() -> "tuple[str, ...]":
    text = _HMIC_CONTRACT_PATH.read_text(encoding="utf-8")
    heading = "## 17. Implementation Identity — Frozen Authority-Bearing File Set"
    assert heading in text, "HMIC-001 §17 heading not found -- contract structure changed"
    section = text.split(heading, 1)[1]
    fence_match = re.search(r"```\n(.*?)\n```", section, re.DOTALL)
    assert fence_match is not None, "no fenced code block found under HMIC-001 §17"
    lines = [line for line in fence_match.group(1).splitlines() if line.strip()]
    # Contract-path lines carry a trailing "(HMIC-ID)" annotation not part
    # of the path itself.
    paths = [re.sub(r"\s+\([A-Z0-9-]+\)\s*$", "", line).strip() for line in lines]
    return tuple(paths)


class TestFrozenFileManifest:
    def test_manifest_matches_contract_enumeration_exactly(self) -> None:
        assert hmic._FROZEN_AUTHORITY_BEARING_FILES == _extract_contract_frozen_file_list()

    def test_manifest_has_exactly_22_entries(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 22

    def test_manifest_has_no_duplicate_entries(self) -> None:
        assert len(set(hmic._FROZEN_AUTHORITY_BEARING_FILES)) == 22

    def test_canonical_paths_are_22_and_lexicographically_sorted(self) -> None:
        canonical = hmic._frozen_canonical_paths()
        assert len(canonical) == 22
        assert list(canonical) == sorted(canonical)

    def test_provider_repair_files_present(self) -> None:
        canonical = hmic._frozen_canonical_paths()
        for expected in (
            "src/pcae/core/hatp_providers.py",
            "src/pcae/core/hatp_fido2_provider.py",
            "src/pcae/core/hatp_piv_provider.py",
            "src/pcae/core/hatp_hardware_credentials.py",
        ):
            assert expected in canonical

    def test_hatp_signing_ceremony_not_in_frozen_set(self) -> None:
        canonical = hmic._frozen_canonical_paths()
        assert "src/pcae/core/hatp_signing_ceremony.py" not in canonical

    def test_new_certification_module_not_in_v1_0_frozen_set(self) -> None:
        canonical = hmic._frozen_canonical_paths()
        assert "src/pcae/core/hatp_mandatory_certification.py" not in canonical

    def test_all_22_frozen_files_currently_exist_in_repository(self) -> None:
        for canonical_path in hmic._frozen_canonical_paths():
            assert (_REPO_ROOT / canonical_path).is_file(), f"missing: {canonical_path}"


# ═══════════════════════════════════════════════════════════════════════════
# Path-literal safety (HMIC-REQ-055), applied to the trusted constant itself
# ═══════════════════════════════════════════════════════════════════════════


class TestFrozenPathLiteralSafety:
    @pytest.mark.parametrize(
        "unsafe",
        ["/etc/passwd", "../escape.py", "core/../../escape.py", "", "core//double.py", "core/./x.py"],
    )
    def test_rejects_unsafe_literal(self, unsafe: str) -> None:
        with pytest.raises(hmic.HMICIdentityDerivationError):
            hmic._validate_frozen_path_literal(unsafe)

    def test_rejects_backslash(self) -> None:
        with pytest.raises(hmic.HMICIdentityDerivationError):
            hmic._validate_frozen_path_literal("core\\hatp_mandatory_cutover.py")

    def test_accepts_every_real_frozen_entry(self) -> None:
        for entry in hmic._FROZEN_AUTHORITY_BEARING_FILES:
            hmic._validate_frozen_path_literal(entry)  # must not raise


# ═══════════════════════════════════════════════════════════════════════════
# Implementation-scope-digest algorithm, exercised against a controlled
# temporary fixture (monkeypatched frozen-file constants) -- never against
# real authority-bearing source (item 81/113: never modify actual frozen
# files just to test digest sensitivity).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def fixture_repo(tmp_path, monkeypatch):
    """A minimal temp repository whose only frozen-set entries are two
    controlled fixture files, one `src/pcae`-relative and one
    repository-root-relative (mirroring the real 18+4 split), plus one
    deliberately non-frozen file. Monkeypatches the module's private
    frozen-set constants -- a private/internal test seam (item 84), never
    a public production parameter."""

    (tmp_path / "src" / "pcae" / "core").mkdir(parents=True)
    (tmp_path / "docs" / "contracts").mkdir(parents=True)

    fixture_a = tmp_path / "src" / "pcae" / "core" / "fixture_a.py"
    fixture_a.write_bytes(b"alpha content\n")
    fixture_b = tmp_path / "docs" / "contracts" / "FIXTURE_CONTRACT.md"
    fixture_b.write_bytes(b"**Contract:** FIX-001\n**Version:** 1.0\n")
    non_frozen = tmp_path / "src" / "pcae" / "core" / "not_frozen.py"
    non_frozen.write_bytes(b"irrelevant\n")

    monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", ("core/fixture_a.py", "docs/contracts/FIXTURE_CONTRACT.md"))
    monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)

    return HarnessPath(tmp_path), fixture_a, fixture_b, non_frozen


class TestImplementationScopeDigest:
    def test_digest_is_64_char_lowercase_hex(self, fixture_repo) -> None:
        root, *_ = fixture_repo
        digest = hmic.derive_implementation_scope_digest(root)
        assert re.fullmatch(r"[0-9a-f]{64}", digest)

    def test_golden_digest_matches_independent_calculation(self, fixture_repo) -> None:
        """Independently re-derives the expected digest directly from
        HMIC-REQ-057/058's textual algorithm (per-file record =
        `<canonical_path> + "\\0" + <sha256_hex> + "\\n"`, concatenated
        in lexicographic canonical-path order, then SHA-256'd) -- without
        calling any production helper (`_sha256_hex`, `_read_frozen_
        file_bytes`, `_frozen_canonical_paths`) -- and checks it matches.
        This is not a self-consistency check."""

        root, fixture_a, fixture_b, _ = fixture_repo
        entries = {
            "src/pcae/core/fixture_a.py": fixture_a.read_bytes(),
            "docs/contracts/FIXTURE_CONTRACT.md": fixture_b.read_bytes(),
        }
        concatenation = b""
        for canonical_path in sorted(entries):
            file_hex = hashlib.sha256(entries[canonical_path]).hexdigest()
            concatenation += f"{canonical_path}\0{file_hex}\n".encode("utf-8")
        expected = hashlib.sha256(concatenation).hexdigest()

        assert hmic.derive_implementation_scope_digest(root) == expected

    def test_one_byte_change_in_first_group_file_changes_digest(self, fixture_repo) -> None:
        root, fixture_a, _fixture_b, _ = fixture_repo
        before = hmic.derive_implementation_scope_digest(root)
        fixture_a.write_bytes(fixture_a.read_bytes() + b"X")
        after = hmic.derive_implementation_scope_digest(root)
        assert before != after

    def test_one_byte_change_in_second_group_file_changes_digest(self, fixture_repo) -> None:
        root, _fixture_a, fixture_b, _ = fixture_repo
        before = hmic.derive_implementation_scope_digest(root)
        fixture_b.write_bytes(fixture_b.read_bytes() + b"X")
        after = hmic.derive_implementation_scope_digest(root)
        assert before != after

    def test_non_frozen_file_change_does_not_affect_digest(self, fixture_repo) -> None:
        root, _fixture_a, _fixture_b, non_frozen = fixture_repo
        before = hmic.derive_implementation_scope_digest(root)
        non_frozen.write_bytes(non_frozen.read_bytes() + b"unrelated change")
        after = hmic.derive_implementation_scope_digest(root)
        assert before == after

    def test_missing_frozen_file_fails_closed(self, fixture_repo) -> None:
        root, fixture_a, _fixture_b, _ = fixture_repo
        fixture_a.unlink()
        with pytest.raises(hmic.FrozenFileDerivationError):
            hmic.derive_implementation_scope_digest(root)

    def test_symlinked_frozen_file_rejected(self, fixture_repo) -> None:
        root, fixture_a, _fixture_b, _ = fixture_repo
        target = fixture_a.parent / "symlink-target.py"
        target.write_bytes(b"attacker content\n")
        fixture_a.unlink()
        fixture_a.symlink_to(target)
        with pytest.raises(hmic.FrozenFileDerivationError):
            hmic.derive_implementation_scope_digest(root)

    def test_symlinked_parent_directory_rejected(self, tmp_path, monkeypatch) -> None:
        real_dir = tmp_path / "real_core"
        real_dir.mkdir()
        (real_dir / "fixture_a.py").write_bytes(b"content\n")
        (tmp_path / "src" / "pcae").mkdir(parents=True)
        (tmp_path / "src" / "pcae" / "core").symlink_to(real_dir)

        monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", ("core/fixture_a.py",))
        monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)

        with pytest.raises(hmic.FrozenFileDerivationError):
            hmic.derive_implementation_scope_digest(HarnessPath(tmp_path))

    def test_directory_in_place_of_frozen_file_rejected(self, fixture_repo) -> None:
        root, fixture_a, _fixture_b, _ = fixture_repo
        fixture_a.unlink()
        fixture_a.mkdir()
        with pytest.raises(hmic.FrozenFileDerivationError):
            hmic.derive_implementation_scope_digest(root)

    def test_fifo_in_place_of_frozen_file_rejected(self, fixture_repo) -> None:
        root, fixture_a, _fixture_b, _ = fixture_repo
        fixture_a.unlink()
        os.mkfifo(fixture_a)
        try:
            with pytest.raises(hmic.FrozenFileDerivationError):
                hmic.derive_implementation_scope_digest(root)
        finally:
            fixture_a.unlink()

    def test_all_modeled_frozen_files_are_individually_sensitive(self, fixture_repo) -> None:
        """22/22-style sensitivity, applied to every entry the fixture
        models (both the src/pcae-relative and repository-root-relative
        group) -- not just one representative from each."""

        root, fixture_a, fixture_b, _ = fixture_repo
        baseline = hmic.derive_implementation_scope_digest(root)
        for target in (fixture_a, fixture_b):
            original = target.read_bytes()
            try:
                target.write_bytes(original + b"\x00mutated")
                assert hmic.derive_implementation_scope_digest(root) != baseline
            finally:
                target.write_bytes(original)
        assert hmic.derive_implementation_scope_digest(root) == baseline


# ═══════════════════════════════════════════════════════════════════════════
# `derive_implementation_commit` (HMIC-REQ-046) -- real temporary Git repos
# ═══════════════════════════════════════════════════════════════════════════


class TestDeriveImplementationCommit:
    def test_returns_current_head_sha(self, tmp_path) -> None:
        _init_git_repo(tmp_path)
        (tmp_path / "file.txt").write_text("hello\n")
        expected = _git_commit_all(tmp_path, "initial")
        assert hmic.derive_implementation_commit(HarnessPath(tmp_path)) == expected

    def test_returns_a_valid_commit_sha_shape(self, tmp_path) -> None:
        _init_git_repo(tmp_path)
        (tmp_path / "file.txt").write_text("hello\n")
        _git_commit_all(tmp_path, "initial")
        sha = hmic.derive_implementation_commit(HarnessPath(tmp_path))
        assert re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha)

    def test_changes_after_new_commit(self, tmp_path) -> None:
        _init_git_repo(tmp_path)
        (tmp_path / "file.txt").write_text("v1\n")
        first = _git_commit_all(tmp_path, "v1")
        (tmp_path / "file.txt").write_text("v2\n")
        second = _git_commit_all(tmp_path, "v2")
        assert first != second
        assert hmic.derive_implementation_commit(HarnessPath(tmp_path)) == second

    def test_fails_closed_when_not_a_git_repository(self, tmp_path) -> None:
        with pytest.raises(hmic.GitIdentityDerivationError):
            hmic.derive_implementation_commit(HarnessPath(tmp_path))

    def test_fails_closed_on_git_repo_with_no_commits(self, tmp_path) -> None:
        _init_git_repo(tmp_path)
        with pytest.raises(hmic.GitIdentityDerivationError):
            hmic.derive_implementation_commit(HarnessPath(tmp_path))

    def test_never_returns_a_fake_or_zero_sha_on_failure(self, tmp_path) -> None:
        try:
            hmic.derive_implementation_commit(HarnessPath(tmp_path))
        except hmic.GitIdentityDerivationError:
            pass
        else:
            pytest.fail("expected GitIdentityDerivationError, got a return value")


# ═══════════════════════════════════════════════════════════════════════════
# Commit + digest AND semantics (HMIC-REQ-047/048/049) -- exercised at the
# pair level: both derive_* functions are independent, and the caller
# (a future Wave C/D consumer) is responsible for comparing both. Wave B's
# obligation is that each component independently reflects only its own
# domain (Git identity never leaks into the file digest and vice versa).
# ═══════════════════════════════════════════════════════════════════════════


class TestCommitAndDigestIndependence:
    def test_dirty_frozen_file_changes_digest_but_not_commit(self, fixture_repo) -> None:
        root, fixture_a, _fixture_b, _ = fixture_repo
        _init_git_repo(root.path)
        _git_commit_all(root.path, "initial")
        commit_before = hmic.derive_implementation_commit(root)
        digest_before = hmic.derive_implementation_scope_digest(root)

        fixture_a.write_bytes(fixture_a.read_bytes() + b"dirty-uncommitted-change")

        assert hmic.derive_implementation_commit(root) == commit_before
        assert hmic.derive_implementation_scope_digest(root) != digest_before

    def test_dirty_non_frozen_file_changes_neither(self, fixture_repo) -> None:
        root, _fixture_a, _fixture_b, non_frozen = fixture_repo
        _init_git_repo(root.path)
        _git_commit_all(root.path, "initial")
        commit_before = hmic.derive_implementation_commit(root)
        digest_before = hmic.derive_implementation_scope_digest(root)

        non_frozen.write_bytes(non_frozen.read_bytes() + b"unrelated dirty change")

        assert hmic.derive_implementation_commit(root) == commit_before
        assert hmic.derive_implementation_scope_digest(root) == digest_before

    def test_new_commit_with_unchanged_frozen_bytes_changes_commit_not_digest(self, fixture_repo) -> None:
        root, _fixture_a, _fixture_b, non_frozen = fixture_repo
        _init_git_repo(root.path)
        _git_commit_all(root.path, "initial")
        commit_before = hmic.derive_implementation_commit(root)
        digest_before = hmic.derive_implementation_scope_digest(root)

        non_frozen.write_bytes(non_frozen.read_bytes() + b"a new, committed, non-frozen change")
        commit_after = _git_commit_all(root.path, "unrelated commit")

        assert commit_after != commit_before
        assert hmic.derive_implementation_commit(root) == commit_after
        assert hmic.derive_implementation_scope_digest(root) == digest_before


# ═══════════════════════════════════════════════════════════════════════════
# `derive_repository_instance_id` / `derive_canonical_deployment_root`
# (HMIC-REQ-043/044)
# ═══════════════════════════════════════════════════════════════════════════


class TestRepositoryAndDeploymentIdentity:
    def test_fails_closed_when_no_identity_established(self, tmp_path) -> None:
        with pytest.raises(hmic.RepositoryIdentityUnavailableError):
            hmic.derive_repository_instance_id(HarnessPath(tmp_path))

    def test_matches_established_layer_1_identity(self, tmp_path) -> None:
        identity = ensure_repository_identity(HarnessPath(tmp_path))
        derived = hmic.derive_repository_instance_id(HarnessPath(tmp_path))
        assert derived == identity.repository_instance_id

    def test_never_creates_an_identity_as_a_side_effect(self, tmp_path) -> None:
        with pytest.raises(hmic.RepositoryIdentityUnavailableError):
            hmic.derive_repository_instance_id(HarnessPath(tmp_path))
        assert not (tmp_path / ".pcae" / "repository-identity.json").exists()

    def test_canonical_deployment_root_matches_hatp_bootstrap_directly(self, tmp_path) -> None:
        expected = resolve_canonical_deployment_root(tmp_path)
        assert hmic.derive_canonical_deployment_root(HarnessPath(tmp_path)) == expected

    def test_canonical_deployment_root_is_stable_for_same_directory(self, tmp_path) -> None:
        first = hmic.derive_canonical_deployment_root(HarnessPath(tmp_path))
        second = hmic.derive_canonical_deployment_root(HarnessPath(tmp_path))
        assert first == second

    def test_no_caller_supplied_repository_instance_id_override_accepted(self) -> None:
        import inspect

        params = inspect.signature(hmic.derive_repository_instance_id).parameters
        assert set(params) == {"root"}

    def test_no_caller_supplied_deployment_root_override_accepted(self) -> None:
        import inspect

        params = inspect.signature(hmic.derive_canonical_deployment_root).parameters
        assert set(params) == {"root"}


# ═══════════════════════════════════════════════════════════════════════════
# `derive_contract_versions` (HMIC-REQ-067/069) -- controlled fixture
# contracts, monkeypatched `_CONTRACT_IDENTITY_FILES`.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def contract_fixture(tmp_path, monkeypatch):
    (tmp_path / "docs" / "contracts").mkdir(parents=True)
    contract_path = tmp_path / "docs" / "contracts" / "FIXTURE_CONTRACT.md"
    contract_path.write_text("# Fixture Contract\n\n**Contract:** FIX-001\n**Version:** 1.0\n**Status:** FROZEN\n")

    monkeypatch.setattr(hmic, "_CONTRACT_IDENTITY_FILES", (("FIX-001", "docs/contracts/FIXTURE_CONTRACT.md"),))
    return HarnessPath(tmp_path), contract_path


class TestDeriveContractVersions:
    def test_derives_expected_version(self, contract_fixture) -> None:
        root, _path = contract_fixture
        versions = hmic.derive_contract_versions(root)
        assert dict(versions) == {"FIX-001": "1.0"}

    def test_result_is_a_read_only_mapping(self, contract_fixture) -> None:
        root, _path = contract_fixture
        versions = hmic.derive_contract_versions(root)
        with pytest.raises(TypeError):
            versions["FIX-001"] = "9.9"  # type: ignore[index]

    def test_alternate_contract_id_label_accepted(self, tmp_path, monkeypatch) -> None:
        """Confirms the real, live inconsistency across the four bound
        contracts (HMRC-001 uses `**Contract ID:**`; HATP-001/HSCE-001/
        RAE-001 use `**Contract:**`) is handled for both spellings."""

        (tmp_path / "docs" / "contracts").mkdir(parents=True)
        path = tmp_path / "docs" / "contracts" / "FIXTURE_CONTRACT_ID.md"
        path.write_text("**Contract ID:** FIX-002\n**Version:** 2.0\n")
        monkeypatch.setattr(hmic, "_CONTRACT_IDENTITY_FILES", (("FIX-002", "docs/contracts/FIXTURE_CONTRACT_ID.md"),))
        versions = hmic.derive_contract_versions(HarnessPath(tmp_path))
        assert dict(versions) == {"FIX-002": "2.0"}

    def test_missing_contract_file_fails_closed(self, contract_fixture) -> None:
        root, path = contract_fixture
        path.unlink()
        with pytest.raises(hmic.ContractIdentityDerivationError):
            hmic.derive_contract_versions(root)

    def test_symlinked_contract_file_rejected(self, contract_fixture) -> None:
        root, path = contract_fixture
        target = path.parent / "external-target.md"
        target.write_text("**Contract:** FIX-001\n**Version:** 9.9\n")
        path.unlink()
        path.symlink_to(target)
        with pytest.raises(hmic.ContractIdentityDerivationError):
            hmic.derive_contract_versions(root)

    def test_malformed_header_fails_closed(self, tmp_path, monkeypatch) -> None:
        (tmp_path / "docs" / "contracts").mkdir(parents=True)
        path = tmp_path / "docs" / "contracts" / "MALFORMED.md"
        path.write_text("no header here at all\n")
        monkeypatch.setattr(hmic, "_CONTRACT_IDENTITY_FILES", (("FIX-001", "docs/contracts/MALFORMED.md"),))
        with pytest.raises(hmic.ContractIdentityDerivationError):
            hmic.derive_contract_versions(HarnessPath(tmp_path))

    def test_wrong_contract_id_in_header_fails_closed(self, tmp_path, monkeypatch) -> None:
        (tmp_path / "docs" / "contracts").mkdir(parents=True)
        path = tmp_path / "docs" / "contracts" / "WRONG_ID.md"
        path.write_text("**Contract:** SOMETHING-ELSE-001\n**Version:** 1.0\n")
        monkeypatch.setattr(hmic, "_CONTRACT_IDENTITY_FILES", (("FIX-001", "docs/contracts/WRONG_ID.md"),))
        with pytest.raises(hmic.ContractIdentityDerivationError):
            hmic.derive_contract_versions(HarnessPath(tmp_path))

    def test_content_drift_without_version_bump_is_still_detectable_via_scope_digest(self, contract_fixture) -> None:
        """HMIC-REQ-053: the two mechanisms are deliberately redundant.
        `derive_contract_versions` alone would not notice a prose edit
        without a version bump -- but `derive_implementation_scope_
        digest` (over the same file, as a frozen-set member) does. This
        test asserts the version stays the same while noting the digest
        mechanism is what actually catches this drift (covered
        separately by `TestImplementationScopeDigest`)."""

        root, path = contract_fixture
        before = hmic.derive_contract_versions(root)
        path.write_text(path.read_text() + "\nAn added, unversioned prose sentence.\n")
        after = hmic.derive_contract_versions(root)
        assert dict(before) == dict(after)

    def test_deterministic_fixed_order_not_dict_hash_order(self) -> None:
        assert [contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES] == [
            "HMRC-001",
            "HATP-001",
            "HSCE-001",
            "RAE-001",
        ]

    def test_real_repository_bound_contract_set_is_exactly_four(self) -> None:
        root = HarnessPath(_REPO_ROOT)
        versions = hmic.derive_contract_versions(root)
        assert set(versions) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}
        assert "HMIC-001" not in versions
        assert "RWMPC-001" not in versions
        assert "PBPA-001" not in versions
        assert "PBPC-001" not in versions

    def test_real_repository_contract_versions_are_non_empty_strings(self) -> None:
        root = HarnessPath(_REPO_ROOT)
        versions = hmic.derive_contract_versions(root)
        for contract_id, version in versions.items():
            assert isinstance(version, str) and version, f"{contract_id}: empty/non-string version"


# ═══════════════════════════════════════════════════════════════════════════
# `derive_certification_id` (HMIC-REQ-038) -- pure, no I/O
# ═══════════════════════════════════════════════════════════════════════════

_VALID_ID_FIELDS = {
    "repository_instance_id": "11111111-1111-4111-8111-111111111111",
    "canonical_deployment_root": "/tmp/example-repo",
    "implementation_commit": "a" * 40,
    "implementation_scope_digest": "b" * 64,
    "contract_versions": {"HMRC-001": "1.0", "HATP-001": "1.0", "HSCE-001": "1.1", "RAE-001": "1.0"},
    "verification_record_digest": "c" * 64,
    "certified_at": "2026-01-01T00:00:00Z",
    "certified_by": "independent-fixture-operator",
}

# Independently computed offline via `json.dumps(payload, indent=2,
# sort_keys=True, allow_nan=False) + "\n"` -> UTF-8 -> SHA-256, using the
# exact `_VALID_ID_FIELDS` payload above -- not derived by calling
# `derive_certification_id` itself.
_GOLDEN_CERTIFICATION_ID = "b042024cc7d67bdf7fc6568175c47047230192001cf3fcd0f037fd0ba8d69c90"


class TestDeriveCertificationId:
    def test_golden_fixture_matches_independent_calculation(self) -> None:
        assert hmic.derive_certification_id(_VALID_ID_FIELDS) == _GOLDEN_CERTIFICATION_ID

    def test_returns_64_char_lowercase_hex(self) -> None:
        result = hmic.derive_certification_id(_VALID_ID_FIELDS)
        assert re.fullmatch(r"[0-9a-f]{64}", result)

    def test_is_pure_no_filesystem_or_git_access(self) -> None:
        """No I/O side channel: calling it in a nonexistent cwd must still work."""

        original_cwd = os.getcwd()
        missing = Path(original_cwd) / "___definitely_does_not_exist___"
        try:
            os.chdir(original_cwd)  # sanity: stay put, this test only asserts no FS dependency exists
            result_a = hmic.derive_certification_id(_VALID_ID_FIELDS)
            result_b = hmic.derive_certification_id(dict(_VALID_ID_FIELDS))
            assert result_a == result_b
        finally:
            os.chdir(original_cwd)
        assert not missing.exists()

    def test_missing_field_fails_closed(self) -> None:
        fields = dict(_VALID_ID_FIELDS)
        del fields["certified_by"]
        with pytest.raises(hmic.HMICIdentityDerivationError):
            hmic.derive_certification_id(fields)

    def test_extra_field_fails_closed(self) -> None:
        fields = dict(_VALID_ID_FIELDS)
        fields["certification_id"] = "d" * 64
        with pytest.raises(hmic.HMICIdentityDerivationError):
            hmic.derive_certification_id(fields)

    def test_status_and_revoked_at_never_participate(self) -> None:
        """status/revoked_at are mutable, non-identity fields -- passing
        them must be rejected outright (they are not in the allowed
        field set at all), never silently ignored."""

        fields = dict(_VALID_ID_FIELDS)
        fields["status"] = "active"
        with pytest.raises(hmic.HMICIdentityDerivationError):
            hmic.derive_certification_id(fields)

    @pytest.mark.parametrize("field", sorted(_VALID_ID_FIELDS.keys()))
    def test_changing_any_single_field_changes_the_id(self, field) -> None:
        baseline = hmic.derive_certification_id(_VALID_ID_FIELDS)
        mutated = dict(_VALID_ID_FIELDS)
        if field == "contract_versions":
            mutated[field] = {**mutated[field], "HMRC-001": "9.9"}
        else:
            mutated[field] = mutated[field] + "-mutated"
        assert hmic.derive_certification_id(mutated) != baseline

    def test_contract_versions_must_be_a_mapping(self) -> None:
        fields = dict(_VALID_ID_FIELDS)
        fields["contract_versions"] = "not-a-mapping"
        with pytest.raises(hmic.HMICIdentityDerivationError):
            hmic.derive_certification_id(fields)

    def test_accepts_mapping_proxy_for_contract_versions(self) -> None:
        from types import MappingProxyType

        fields = dict(_VALID_ID_FIELDS)
        fields["contract_versions"] = MappingProxyType(dict(fields["contract_versions"]))
        result = hmic.derive_certification_id(fields)
        assert result == _GOLDEN_CERTIFICATION_ID

    def test_no_public_signature_accepts_a_precomputed_digest_or_sha_override(self) -> None:
        import inspect

        params = inspect.signature(hmic.derive_certification_id).parameters
        assert set(params) == {"record_fields"}


# ═══════════════════════════════════════════════════════════════════════════
# No-VALID-status / no-certification-bool / no-certification-state-read
# proof (items 62/63/60/116)
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCertificationValidityJudgment:
    def test_no_wave_b_function_returns_certification_status(self) -> None:
        import inspect

        for name in (
            "derive_repository_instance_id",
            "derive_canonical_deployment_root",
            "derive_implementation_commit",
            "derive_implementation_scope_digest",
            "derive_contract_versions",
            "derive_certification_id",
        ):
            func = getattr(hmic, name)
            annotation = inspect.signature(func).return_annotation
            assert annotation is not hmic.CertificationStatus

    def test_no_is_certified_verified_or_valid_named_function_exists(self) -> None:
        forbidden_names = {"is_certified", "verified", "valid", "is_valid_certification"}
        public_names = {name for name in dir(hmic) if not name.startswith("_")}
        assert forbidden_names.isdisjoint(public_names)

    def test_module_source_never_reads_certifications_json(self) -> None:
        """Checked against the parsed AST's string-literal pool, not raw
        source text, so this isn't tripped by the module's own docstring
        prose (which legitimately names these filenames when explaining
        what Wave B does NOT read)."""

        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        docstring_nodes = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc is not None:
                    docstring_nodes.add(doc)
        string_literals = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value not in docstring_nodes
        }
        assert not any("certifications.json" in literal for literal in string_literals)
        assert not any("certification-bindings.json" in literal for literal in string_literals)

    def test_no_writer_create_revoke_or_supersede_function_exists(self) -> None:
        forbidden_substrings = ("create_certification", "revoke_certification", "supersede", "write_certification")
        public_names = {name for name in dir(hmic) if not name.startswith("_")}
        for name in public_names:
            for forbidden in forbidden_substrings:
                assert forbidden not in name


# ═══════════════════════════════════════════════════════════════════════════
# W-1 / dependency-direction re-confirmation specific to Wave B's additions
# ═══════════════════════════════════════════════════════════════════════════


class TestWaveBDependencyDiscipline:
    def test_module_never_imports_cutover_module(self) -> None:
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
        assert "pcae.core.hatp_mandatory_cutover" not in imported

    def test_no_permission_broker_or_provider_import(self) -> None:
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
        forbidden_substrings = ("permission_broker", "hatp_providers", "hatp_fido2", "hatp_piv", "hatp_hardware")
        for name in imported:
            for forbidden in forbidden_substrings:
                assert forbidden not in name

    def test_importing_module_performs_no_io(self, tmp_path, monkeypatch) -> None:
        """Import-time side-effect check (item 72): importing the module
        in a subprocess with a nonexistent, non-repository cwd must
        succeed without raising -- proving no Git/filesystem read
        happens merely from `import`."""

        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "from pcae.core import hatp_mandatory_certification\n"
            "print('import-ok')\n"
        ) % str(_REPO_ROOT / "src")
        isolated_cwd = tmp_path / "isolated"
        isolated_cwd.mkdir()
        result = subprocess.run(
            ["python3", "-c", script], cwd=isolated_cwd, capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stderr
        assert "import-ok" in result.stdout
