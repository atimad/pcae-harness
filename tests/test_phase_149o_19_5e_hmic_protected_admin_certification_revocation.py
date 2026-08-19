"""Phase 149O.19.5E -- HMIC Protected Admin Certification / Revocation
Surface (Wave E), `docs/PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md`
§9.2-9.5, `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_
CERTIFICATION_CONTRACT.md` HMIC-REQ-012-020, 039, 045, 076-082, 086-088,
091-093, 118-119, 126-127, 144.

Phase-boundary verification and behavioral test suite for the standalone
`scripts/hatp_certification_admin.py` admin ceremony script -- the sole
production write path for `CertificationRecord`/`CertificationBinding`
state. Scope discipline (restated from the 149O.19.5A-D suites): this
phase answers "can a Protected Admin Authority create, activate, and
revoke certification state, and can nothing else" -- and only that. No
test here exercises readiness integration, the hard-coded `mandatory_
consumption_implementation_independently_verified = False` ceiling, or
any Wave-F wiring; no test mutates `HATPTrustStore.production().root`.
All write tests use isolated `tmp_path` protected roots and isolated
git-fixture repositories, mirroring the 149O.19.5D suite's `env` fixture
exactly.

`scripts/hatp_certification_admin.py` is a standalone script outside
`src/pcae/**`, so it is loaded here via `importlib` from its file path
(not imported as a normal package module) -- the same posture a real
operator's manual `python scripts/hatp_certification_admin.py ...`
invocation has, never a `src/pcae/**` import of it.
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"
_CLI_PATH = _REPO_ROOT / "src" / "pcae" / "cli.py"
_AGENT_COMMANDS_PATH = _REPO_ROOT / "src" / "pcae" / "commands" / "agent.py"
_CORE_AGENT_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "agent.py"
_CUTOVER_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py"


def _load_admin_module():
    spec = importlib.util.spec_from_file_location("hatp_certification_admin", _ADMIN_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


admin = _load_admin_module()


# ═══════════════════════════════════════════════════════════════════════════
# Isolated git-fixture repository + isolated protected root (mirrors the
# 149O.19.5D suite's `env` fixture exactly).
# ═══════════════════════════════════════════════════════════════════════════


def _git(args: "list[str]", cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Fixture"], cwd=root, check=True)


def _git_commit_all(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)
    return _git(["rev-parse", "HEAD"], cwd=root)


@pytest.fixture
def env(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    protected_root = tmp_path / "protected-root"
    (repo_root / "src" / "pcae" / "core").mkdir(parents=True)
    (repo_root / "docs" / "contracts").mkdir(parents=True)

    (repo_root / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"alpha content v1\n")
    for name, cid, ver in (
        ("FIXTURE_HMRC.md", "HMRC-001", "1.0"),
        ("FIXTURE_HATP.md", "HATP-001", "1.0"),
        ("FIXTURE_HSCE.md", "HSCE-001", "1.1"),
        ("FIXTURE_RAE.md", "RAE-001", "1.0"),
    ):
        (repo_root / "docs" / "contracts" / name).write_bytes(f"**Contract:** {cid}\n**Version:** {ver}\n".encode())

    monkeypatch.setattr(
        hmic,
        "_FROZEN_AUTHORITY_BEARING_FILES",
        (
            "core/fixture_a.py",
            "docs/contracts/FIXTURE_HMRC.md",
            "docs/contracts/FIXTURE_HATP.md",
            "docs/contracts/FIXTURE_HSCE.md",
            "docs/contracts/FIXTURE_RAE.md",
        ),
    )
    monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)
    monkeypatch.setattr(
        hmic,
        "_CONTRACT_IDENTITY_FILES",
        (
            ("HMRC-001", "docs/contracts/FIXTURE_HMRC.md"),
            ("HATP-001", "docs/contracts/FIXTURE_HATP.md"),
            ("HSCE-001", "docs/contracts/FIXTURE_HSCE.md"),
            ("RAE-001", "docs/contracts/FIXTURE_RAE.md"),
        ),
    )
    monkeypatch.setattr(
        hmic,
        "_CONTRACT_VERSIONS_REQUIRED_KEYS",
        frozenset({"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}),
    )

    _init_git_repo(repo_root)
    _git_commit_all(repo_root, "initial")
    ensure_repository_identity(HarnessPath(repo_root))

    vr_path = tmp_path / "verification-record.md"
    vr_path.write_bytes(b"canonical phase report fixture\n")

    return {
        "repo_root": repo_root,
        "protected_root": protected_root,
        "verification_record_path": vr_path,
    }


def _certify(env, *, certified_by="protected-admin", confirm=True):
    return admin.certify(
        repository_root=env["repo_root"],
        certified_by=certified_by,
        verification_record_path=env["verification_record_path"],
        confirm=confirm,
        _protected_root=env["protected_root"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# CREATE -- HMIC-REQ-076 steps 1-6, HMIC-REQ-083-084/098.
# ═══════════════════════════════════════════════════════════════════════════


class TestCreate:
    def test_create_appends_active_record(self, env) -> None:
        result = _certify(env)
        assert result.already_existed is False
        assert result.record.status == "active"
        loaded = hmic._load_certification_record(env["protected_root"], result.certification_id)
        assert loaded.certification_id == result.certification_id

    def test_create_does_not_activate(self, env) -> None:
        """HMIC-REQ-086: creating never makes a record active."""

        _certify(env)
        binding = hmic._load_active_binding(
            env["protected_root"],
            repository_instance_id=hmic.derive_repository_instance_id(HarnessPath(env["repo_root"])),
            canonical_deployment_root=hmic.derive_canonical_deployment_root(HarnessPath(env["repo_root"])),
        )
        assert binding is None

    def test_idempotent_repeat_identical_content(self, env, monkeypatch) -> None:
        monkeypatch.setattr(admin, "_canonical_timestamp_now", lambda: "2026-08-10T12:00:00.000Z")
        first = _certify(env)
        second = _certify(env)
        assert second.already_existed is True
        assert second.certification_id == first.certification_id

    def test_declined_confirmation_writes_nothing(self, env) -> None:
        with pytest.raises(admin.ConfirmationDeclinedError):
            _certify(env, confirm=False)
        result = hmic._read_certifications(env["protected_root"])
        assert result.status == hmic._ReadStatus.ABSENT

    def test_certification_id_is_tool_derived_not_caller_suppliable(self, env) -> None:
        """HMIC-REQ-039/077: `certify` accepts no `certification_id`
        parameter at all."""

        params = set(inspect.signature(admin.certify).parameters)
        for forbidden in (
            "certification_id",
            "repository_instance_id",
            "canonical_deployment_root",
            "implementation_commit",
            "implementation_scope_digest",
            "contract_versions",
            "verified",
            "status",
        ):
            assert forbidden not in params

    def test_verification_record_is_a_locator_not_a_digest(self, env) -> None:
        """governing-prompt item 62: the human supplies a path, the tool
        hashes it -- no `verification_record_digest=` parameter exists."""

        params = set(inspect.signature(admin.certify).parameters)
        assert "verification_record_path" in params
        assert "verification_record_digest" not in params


# ═══════════════════════════════════════════════════════════════════════════
# ACTIVATE -- HMIC-REQ-076 step 7, HMIC-REQ-085-090.
# ═══════════════════════════════════════════════════════════════════════════


class TestActivate:
    def test_activate_binds_existing_certification(self, env) -> None:
        created = _certify(env)
        result = admin.activate(
            repository_root=env["repo_root"],
            certification_id=created.certification_id,
            confirm=True,
            _protected_root=env["protected_root"],
        )
        assert result.certification_id == created.certification_id
        binding = hmic._load_active_binding(
            env["protected_root"],
            repository_instance_id=result.repository_instance_id,
            canonical_deployment_root=result.canonical_deployment_root,
        )
        assert binding is not None
        assert binding.active_certification_id == created.certification_id

    def test_activate_rejects_nonexistent_certification_id(self, env) -> None:
        with pytest.raises(hmic.CertificationRecordNotFoundError):
            admin.activate(
                repository_root=env["repo_root"],
                certification_id="f" * 64,
                confirm=True,
                _protected_root=env["protected_root"],
            )
        binding = hmic._read_certification_bindings(env["protected_root"])
        assert binding.status == hmic._ReadStatus.ABSENT

    def test_no_implicit_latest_selection(self, env) -> None:
        """HMIC-REQ-085/092: `activate` never accepts anything but an
        exact certification_id -- no 'latest'/'newest' argument exists."""

        params = set(inspect.signature(admin.activate).parameters)
        assert "certification_id" in params
        for forbidden in ("latest", "newest", "most_recent"):
            assert forbidden not in params

    def test_declined_activate_confirmation_writes_nothing(self, env) -> None:
        created = _certify(env)
        with pytest.raises(admin.ConfirmationDeclinedError):
            admin.activate(
                repository_root=env["repo_root"],
                certification_id=created.certification_id,
                confirm=False,
                _protected_root=env["protected_root"],
            )
        binding = hmic._read_certification_bindings(env["protected_root"])
        assert binding.status == hmic._ReadStatus.ABSENT

    def test_activate_does_not_require_target_to_be_currently_valid(self, env) -> None:
        """governing-prompt item 20/21: binding mutation != validator
        decision -- a structurally well-formed but not-yet-`VALID`-checked
        record may still be bound; Wave D alone judges validity."""

        created = _certify(env)
        # No call to the Wave-D validator occurs anywhere in `activate`.
        source = inspect.getsource(admin.activate)
        assert "_validate_at_root" not in source
        assert "validate_active_hatp_mandatory" not in source
        result = admin.activate(
            repository_root=env["repo_root"],
            certification_id=created.certification_id,
            confirm=True,
            _protected_root=env["protected_root"],
        )
        assert result.certification_id == created.certification_id


# ═══════════════════════════════════════════════════════════════════════════
# REVOKE -- HMIC-REQ-091-094, monotonic.
# ═══════════════════════════════════════════════════════════════════════════


class TestRevoke:
    def test_revoke_field_mutates_not_deletes(self, env) -> None:
        created = _certify(env)
        result = admin.revoke(
            certification_id=created.certification_id, confirm=True, _protected_root=env["protected_root"]
        )
        assert result.already_revoked is False
        loaded = hmic._load_certification_record(env["protected_root"], created.certification_id)
        assert loaded.status == "revoked"
        assert loaded.revoked_at == result.revoked_at

    def test_revoke_idempotent_same_moment_replay(self, env, monkeypatch) -> None:
        created = _certify(env)
        fixed_ts = "2026-08-10T12:00:00.000Z"
        monkeypatch.setattr(admin, "_canonical_timestamp_now", lambda: fixed_ts)
        first = admin.revoke(
            certification_id=created.certification_id, confirm=True, _protected_root=env["protected_root"]
        )
        second = admin.revoke(
            certification_id=created.certification_id, confirm=True, _protected_root=env["protected_root"]
        )
        assert first.revoked_at == fixed_ts
        assert second.already_revoked is True
        assert second.revoked_at == fixed_ts

    def test_revoke_conflicting_replay_rejected(self, env, monkeypatch) -> None:
        created = _certify(env)
        monkeypatch.setattr(admin, "_canonical_timestamp_now", lambda: "2026-08-10T12:00:00.000Z")
        admin.revoke(certification_id=created.certification_id, confirm=True, _protected_root=env["protected_root"])
        monkeypatch.setattr(admin, "_canonical_timestamp_now", lambda: "2026-08-10T13:00:00.000Z")
        with pytest.raises(hmic.CertificationConflictError):
            admin.revoke(certification_id=created.certification_id, confirm=True, _protected_root=env["protected_root"])

    def test_revoke_nonexistent_certification_id_rejected(self, env) -> None:
        with pytest.raises(hmic.CertificationRecordNotFoundError):
            admin.revoke(certification_id="e" * 64, confirm=True, _protected_root=env["protected_root"])

    def test_no_unrevoke_api_exists(self) -> None:
        """HMIC-REQ item-75: no function in the admin module can set
        status back to 'active' on an already-revoked record."""

        public_and_private_names = {name for name in vars(admin) if not name.startswith("__")}
        for forbidden in ("unrevoke", "un_revoke", "restore", "reactivate", "clear_revocation"):
            assert forbidden not in public_and_private_names

    def test_revoke_declined_confirmation_writes_nothing(self, env) -> None:
        created = _certify(env)
        with pytest.raises(admin.ConfirmationDeclinedError):
            admin.revoke(certification_id=created.certification_id, confirm=False, _protected_root=env["protected_root"])
        loaded = hmic._load_certification_record(env["protected_root"], created.certification_id)
        assert loaded.status == "active"

    def test_revoke_does_not_clear_active_binding(self, env) -> None:
        """governing-prompt item 24: after revoking the currently-active
        certification, the binding still points at it -- Wave D's
        validator, not the writer, turns this into REVOKED readiness."""

        created = _certify(env)
        admin.activate(
            repository_root=env["repo_root"],
            certification_id=created.certification_id,
            confirm=True,
            _protected_root=env["protected_root"],
        )
        admin.revoke(certification_id=created.certification_id, confirm=True, _protected_root=env["protected_root"])
        result = hmic._validate_at_root(protected_root=env["protected_root"], repository_root=env["repo_root"])
        assert result.status is hmic.CertificationStatus.REVOKED

    def test_revoke_reason_field_not_accepted(self) -> None:
        """governing-prompt item 23: HMIC-REQ-032's schema has no
        revocation-reason field, so `revoke` accepts none."""

        params = set(inspect.signature(admin.revoke).parameters)
        assert "reason" not in params


# ═══════════════════════════════════════════════════════════════════════════
# Concurrency -- HMIC-REQ-097-100 (writer-level, exercised through the
# ceremony functions rather than the raw Wave-C primitives directly).
# ═══════════════════════════════════════════════════════════════════════════


class TestConcurrency:
    def test_concurrent_identical_create_is_deterministic_idempotent(self, env, monkeypatch) -> None:
        monkeypatch.setattr(admin, "_canonical_timestamp_now", lambda: "2026-08-10T12:00:00.000Z")
        results = []
        errors = []

        def worker() -> None:
            try:
                results.append(_certify(env))
            except Exception as exc:  # noqa: BLE001 -- captured for assertion
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len({r.certification_id for r in results}) == 1
        assert sum(1 for r in results if not r.already_existed) == 1

    def test_concurrent_activate_supersession_is_single_deterministic_winner(self, env) -> None:
        cert_a = _certify(env, certified_by="admin-a")
        cert_b = admin.certify(
            repository_root=env["repo_root"],
            certified_by="admin-b",
            verification_record_path=env["verification_record_path"],
            confirm=True,
            _protected_root=env["protected_root"],
        )
        # admin-a and admin-b differ only by certified_by, so certification_id differs.
        assert cert_a.certification_id != cert_b.certification_id

        def activate_one(cert_id: str) -> None:
            admin.activate(
                repository_root=env["repo_root"],
                certification_id=cert_id,
                confirm=True,
                _protected_root=env["protected_root"],
            )

        t1 = threading.Thread(target=activate_one, args=(cert_a.certification_id,))
        t2 = threading.Thread(target=activate_one, args=(cert_b.certification_id,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        binding = hmic._load_active_binding(
            env["protected_root"],
            repository_instance_id=hmic.derive_repository_instance_id(HarnessPath(env["repo_root"])),
            canonical_deployment_root=hmic.derive_canonical_deployment_root(HarnessPath(env["repo_root"])),
        )
        assert binding.active_certification_id in (cert_a.certification_id, cert_b.certification_id)


# ═══════════════════════════════════════════════════════════════════════════
# Cross-repository / cross-deployment isolation -- HMIC-REQ-026, attacks
# 83-84 (governing-prompt items 81-84).
# ═══════════════════════════════════════════════════════════════════════════


class TestMultiRepositoryIsolation:
    def test_two_repositories_same_protected_root_do_not_cross_contaminate(self, tmp_path, monkeypatch) -> None:
        protected_root = tmp_path / "shared-protected-root"

        def make_repo(name: str) -> Path:
            repo_root = tmp_path / name
            (repo_root / "src" / "pcae" / "core").mkdir(parents=True)
            (repo_root / "docs" / "contracts").mkdir(parents=True)
            (repo_root / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(f"{name}-content\n".encode())
            for cname, cid, ver in (
                ("FIXTURE_HMRC.md", "HMRC-001", "1.0"),
                ("FIXTURE_HATP.md", "HATP-001", "1.0"),
                ("FIXTURE_HSCE.md", "HSCE-001", "1.1"),
                ("FIXTURE_RAE.md", "RAE-001", "1.0"),
            ):
                (repo_root / "docs" / "contracts" / cname).write_bytes(f"**Contract:** {cid}\n**Version:** {ver}\n".encode())
            _init_git_repo(repo_root)
            _git_commit_all(repo_root, "initial")
            ensure_repository_identity(HarnessPath(repo_root))
            return repo_root

        monkeypatch.setattr(
            hmic,
            "_FROZEN_AUTHORITY_BEARING_FILES",
            (
                "core/fixture_a.py",
                "docs/contracts/FIXTURE_HMRC.md",
                "docs/contracts/FIXTURE_HATP.md",
                "docs/contracts/FIXTURE_HSCE.md",
                "docs/contracts/FIXTURE_RAE.md",
            ),
        )
        monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)
        monkeypatch.setattr(
            hmic,
            "_CONTRACT_IDENTITY_FILES",
            (
                ("HMRC-001", "docs/contracts/FIXTURE_HMRC.md"),
                ("HATP-001", "docs/contracts/FIXTURE_HATP.md"),
                ("HSCE-001", "docs/contracts/FIXTURE_HSCE.md"),
                ("RAE-001", "docs/contracts/FIXTURE_RAE.md"),
            ),
        )
        monkeypatch.setattr(
            hmic,
            "_CONTRACT_VERSIONS_REQUIRED_KEYS",
            frozenset({"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}),
        )

        repo_a = make_repo("repo-a")
        repo_b = make_repo("repo-b")
        vr_path = tmp_path / "vr.md"
        vr_path.write_bytes(b"vr\n")

        cert_a = admin.certify(
            repository_root=repo_a, certified_by="admin", verification_record_path=vr_path,
            confirm=True, _protected_root=protected_root,
        )
        admin.activate(
            repository_root=repo_a, certification_id=cert_a.certification_id,
            confirm=True, _protected_root=protected_root,
        )

        result_b = hmic._validate_at_root(protected_root=protected_root, repository_root=repo_b)
        assert result_b.status is hmic.CertificationStatus.MISSING

        result_a = hmic._validate_at_root(protected_root=protected_root, repository_root=repo_a)
        assert result_a.status is hmic.CertificationStatus.VALID

    def test_revoke_wrong_id_in_shared_root_does_not_touch_other_records(self, env) -> None:
        cert = _certify(env)
        with pytest.raises(hmic.CertificationRecordNotFoundError):
            admin.revoke(certification_id="d" * 64, confirm=True, _protected_root=env["protected_root"])
        loaded = hmic._load_certification_record(env["protected_root"], cert.certification_id)
        assert loaded.status == "active"


# ═══════════════════════════════════════════════════════════════════════════
# Self-certification / agent-reachability attacks -- HMIC-REQ-012, 017,
# 018, 020, 079-082, CIVC-2, CIVC-12; attacks 5, 6, 27.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoAgentReachableWriteSurface:
    def test_ordinary_pcae_cli_has_no_certify_or_revoke_subcommand(self) -> None:
        from pcae import cli as pcae_cli

        parser = pcae_cli.build_parser() if hasattr(pcae_cli, "build_parser") else None
        source = _CLI_PATH.read_text(encoding="utf-8")
        forbidden_tokens = (
            '"certify"',
            "'certify'",
            '"revoke-certification"',
            "'revoke-certification'",
            "mark_independently_verified",
            "set_certified",
        )
        for token in forbidden_tokens:
            assert token not in source
        del parser  # presence-of-parser is not itself the assertion; source scan is.

    def test_cli_module_does_not_import_admin_script_or_writer_functions(self) -> None:
        source = _CLI_PATH.read_text(encoding="utf-8")
        for forbidden in ("hatp_certification_admin", "_append_certification_record", "_write_active_binding", "_write_revocation"):
            assert forbidden not in source

    def test_agent_modules_do_not_import_admin_script_or_writer_functions(self) -> None:
        for path in (_AGENT_COMMANDS_PATH, _CORE_AGENT_PATH):
            source = path.read_text(encoding="utf-8")
            for forbidden in (
                "hatp_certification_admin",
                "_append_certification_record",
                "_write_active_binding",
                "_write_revocation",
            ):
                assert forbidden not in source

    def test_no_production_src_pcae_file_imports_the_admin_script(self) -> None:
        """AST-based (not substring) check: `hatp_mandatory_certification.
        py`'s own module docstring *mentions* the admin script's future
        path in prose (documenting who is allowed to call its internal
        writers) -- that is not an import and must not fail this check;
        only an actual `import`/`from ... import` naming the admin script
        is forbidden."""

        src_pcae = _REPO_ROOT / "src" / "pcae"
        for path in src_pcae.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "hatp_certification_admin" not in alias.name, f"{path} must not import the admin script"
                elif isinstance(node, ast.ImportFrom) and node.module:
                    assert "hatp_certification_admin" not in node.module, f"{path} must not import the admin script"

    def test_admin_writer_functions_have_no_agent_reachable_public_wrapper(self) -> None:
        """HMIC-REQ-082: `hatp_mandatory_certification.py` itself exposes
        no public `create_certification`/`activate_certification`/
        `revoke_certification` name -- the writer primitives remain
        underscore-prefixed and are only ever called from the standalone
        script under test."""

        public_names = {name for name in vars(hmic) if not name.startswith("_")}
        for forbidden in (
            "create_certification",
            "activate_certification",
            "revoke_certification",
            "mark_independently_verified",
            "set_certified",
        ):
            assert forbidden not in public_names


# ═══════════════════════════════════════════════════════════════════════════
# No readiness / PB / RAE / AG3-AG5 / HMRC coupling -- HMIC-REQ-118-127,
# 101-107 of the governing prompt.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCoupling:
    def test_admin_script_does_not_import_forbidden_modules(self) -> None:
        tree = ast.parse(_ADMIN_SCRIPT_PATH.read_text(encoding="utf-8"), filename=str(_ADMIN_SCRIPT_PATH))
        imported_modules: "set[str]" = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        forbidden_substrings = (
            "hatp_mandatory_cutover",
            "permission_broker",
            "rollback_approval_evidence",
            "hatp_ag_authority",
            "hatp_rollback_consumption",
        )
        for module_name in imported_modules:
            for forbidden in forbidden_substrings:
                assert forbidden not in module_name, f"admin script must not import {module_name}"

    def test_ceremony_results_carry_no_readiness_or_approval_field(self) -> None:
        for result_type in (admin.CreateCeremonyResult, admin.ActivateCeremonyResult, admin.RevokeCeremonyResult):
            field_names = set(inspect.signature(result_type).parameters)
            for forbidden in (
                "ready",
                "readiness",
                "activation_allowed",
                "pb_result",
                "approved",
                "rollback_approval",
                "capability",
            ):
                assert forbidden not in field_names

    def test_hatp_mandatory_cutover_module_unchanged_by_this_phase(self) -> None:
        """Structural proxy: the cutover module still names the hard-coded
        readiness ceiling and still does not import the certification
        module (Wave F remains ungated by this phase).

        Phase 149O.19.5F (Wave F, gated by Stop Condition W-1 --
        independently confirmed closed at 149O.19.5E.4) is the first
        phase to wire that import in. Pinned to this file's own
        pre-Wave-F phase-entry commit so the original evidentiary claim
        (unchanged as of this phase) is preserved, not weakened."""

        source = subprocess.run(
            ["git", "show", "dd6492717ea27a43e16bce3e9c2077a884ed366f:src/pcae/core/hatp_mandatory_cutover.py"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert "mandatory_consumption_implementation_independently_verified" in source
        assert "hatp_mandatory_certification" not in source
        assert "hatp_certification_admin" not in source


# ═══════════════════════════════════════════════════════════════════════════
# Malformed / path-safety -- governing-prompt items 86-88.
# ═══════════════════════════════════════════════════════════════════════════


class TestMalformedAndPathSafety:
    def test_certification_id_never_used_as_a_filesystem_path_component(self) -> None:
        """`certification_id` is compared as an in-memory string against
        parsed JSON records -- never joined onto a `Path` -- in both the
        Wave-C readers and this phase's ceremony functions, so a
        malformed/traversal-shaped ID cannot escape the protected root
        (source-inspected: no `Path(...)`/`/`-join expression anywhere in
        `_load_certification_record`, `_write_revocation`, `admin.activate`,
        or `admin.revoke` combines `certification_id` with a path)."""

        for func in (hmic._load_certification_record, hmic._write_revocation, admin.activate, admin.revoke):
            source = inspect.getsource(func)
            assert "certification_id /" not in source
            assert "/ certification_id" not in source
            assert "Path(certification_id" not in source

    def test_path_traversal_shaped_certification_id_rejected_as_not_found(self, env) -> None:
        traversal_id = "../../../../etc/passwd"
        with pytest.raises(hmic.CertificationRecordNotFoundError):
            admin.revoke(certification_id=traversal_id, confirm=True, _protected_root=env["protected_root"])
        with pytest.raises(hmic.CertificationRecordNotFoundError):
            admin.activate(
                repository_root=env["repo_root"],
                certification_id=traversal_id,
                confirm=True,
                _protected_root=env["protected_root"],
            )
        # No file escaped the protected root: only the two frozen-name
        # certification files may exist under it.
        existing = {p.name for p in env["protected_root"].glob("*")} if env["protected_root"].exists() else set()
        assert existing <= {"certifications.json", "certification-bindings.json", ".certification-transition.lock"}

