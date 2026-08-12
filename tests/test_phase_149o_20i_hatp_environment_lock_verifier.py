"""Phase 149O.20I, Wave C — tests for `hatp_environment_lock_verifier.py`.

Covers HBDC-REQ-023, HBDC-REQ-025..039 against the live interpreter and
isolated fixtures/subprocess environments (never a real Class-B host)."""
from __future__ import annotations

import inspect
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hatp_environment_lock_verifier as e
from pcae.core.hatp_class_b_topology_verifier import ClassBConformanceStatus
from pcae.core.hatp_environment_lock_verifier import verify_environment_lock_conformance

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]


def _agent_uid_gids():
    return os.geteuid(), frozenset(os.getgroups())


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════


def test_public_api_accepts_zero_parameters():
    sig = inspect.signature(verify_environment_lock_conformance)
    assert len(sig.parameters) == 0


def test_real_host_result_is_not_compliant():
    """§53 expectation: current dev host is not a locked-down Model-A
    environment (agent owns the interpreter/venv it runs under)."""

    result = verify_environment_lock_conformance()
    assert result.status != ClassBConformanceStatus.COMPLIANT


def test_all_hbdc_req_rows_present():
    result = verify_environment_lock_conformance()
    ids = {c.check_id for c in result.checks}
    expected = {
        "HBDC-REQ-025",
        "HBDC-REQ-026",
        "HBDC-REQ-027",
        "HBDC-REQ-028",
        "HBDC-REQ-029",
        "HBDC-REQ-030",
        "HBDC-REQ-031",
        "HBDC-REQ-032",
        "HBDC-REQ-033",
        "HBDC-REQ-034",
        "HBDC-REQ-035",
        "HBDC-REQ-036",
        "HBDC-REQ-037",
        "HBDC-REQ-038",
        "HBDC-REQ-039",
    }
    assert expected <= ids


# ═══════════════════════════════════════════════════════════════════════════
# Interpreter / venv
# ═══════════════════════════════════════════════════════════════════════════


def test_interpreter_check_on_agent_owned_interpreter_non_compliant():
    result = e._check_interpreter_unwritable(*_agent_uid_gids())
    assert result.satisfied is False


def test_interpreter_check_fixture_agent_unwritable(tmp_path, monkeypatch):
    from pcae.core import hatp_class_b_topology_verifier as topo

    monkeypatch.setattr(topo, "_acl_grants_agent_write", lambda path, uid, gids: False)
    fake_interpreter = tmp_path / "python3"
    fake_interpreter.write_text("#!/bin/sh\n")
    fake_interpreter.chmod(0o500)
    tmp_path.chmod(0o500)
    monkeypatch.setattr(e.sys, "executable", str(fake_interpreter))
    try:
        agent_uid, agent_gids = _agent_uid_gids()
        fake_agent_uid = agent_uid + 1
        result = e._check_interpreter_unwritable(fake_agent_uid, frozenset())
        assert result.satisfied is True
    finally:
        tmp_path.chmod(0o700)
        fake_interpreter.chmod(0o700)


def test_venv_not_detected_when_prefix_equals_base_prefix(monkeypatch):
    monkeypatch.setattr(e.sys, "base_prefix", e.sys.prefix)
    result = e._check_venv_lock(*_agent_uid_gids())
    assert result.satisfied is False
    assert result.status == "no_venv_detected_not_provisioned"


def test_venv_root_none_when_not_in_venv(monkeypatch):
    monkeypatch.setattr(e.sys, "base_prefix", e.sys.prefix)
    assert e._venv_root() is None


# ═══════════════════════════════════════════════════════════════════════════
# PYTHONPATH
# ═══════════════════════════════════════════════════════════════════════════


def test_pythonpath_unset_compliant(monkeypatch):
    monkeypatch.delenv("PYTHONPATH", raising=False)
    result = e._check_pythonpath(*_agent_uid_gids())
    assert result.satisfied is True
    assert result.status == "pythonpath_unset"


def test_pythonpath_agent_writable_entry_non_compliant(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    result = e._check_pythonpath(*_agent_uid_gids())
    assert result.satisfied is False
    assert result.status == "pythonpath_contains_agent_writable_entry"


def test_pythonpath_agent_unwritable_entry_compliant(tmp_path, monkeypatch):
    from pcae.core import hatp_class_b_topology_verifier as topo

    monkeypatch.setattr(topo, "_acl_grants_agent_write", lambda path, uid, gids: False)
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o500)
    try:
        monkeypatch.setenv("PYTHONPATH", str(locked))
        agent_uid = locked.stat().st_uid + 1
        result = e._check_pythonpath(agent_uid, frozenset())
        assert result.satisfied is True
    finally:
        locked.chmod(0o700)


# ═══════════════════════════════════════════════════════════════════════════
# user-site
# ═══════════════════════════════════════════════════════════════════════════


def test_user_site_disabled_compliant(monkeypatch):
    monkeypatch.setattr(e.site, "ENABLE_USER_SITE", False)
    result = e._check_user_site(*_agent_uid_gids())
    assert result.satisfied is True
    assert result.status == "user_site_disabled"


def test_user_site_enabled_agent_writable_non_compliant(tmp_path, monkeypatch):
    monkeypatch.setattr(e.site, "ENABLE_USER_SITE", True)
    monkeypatch.setattr(e.site, "getusersitepackages", lambda: str(tmp_path))
    result = e._check_user_site(*_agent_uid_gids())
    assert result.satisfied is False


# ═══════════════════════════════════════════════════════════════════════════
# sitecustomize / usercustomize
# ═══════════════════════════════════════════════════════════════════════════


def test_no_customization_module_present_compliant(tmp_path, monkeypatch):
    monkeypatch.setattr(e.sys, "path", [str(tmp_path)])
    result = e._check_customization_modules(*_agent_uid_gids())
    assert result.satisfied is True
    assert result.status == "no_customization_module_present"


def test_agent_writable_sitecustomize_non_compliant(tmp_path, monkeypatch):
    (tmp_path / "sitecustomize.py").write_text("import os\n")
    monkeypatch.setattr(e.sys, "path", [str(tmp_path)])
    result = e._check_customization_modules(*_agent_uid_gids())
    assert result.satisfied is False
    assert result.status == "customization_module_agent_writable"


def test_agent_writable_usercustomize_non_compliant(tmp_path, monkeypatch):
    (tmp_path / "usercustomize.py").write_text("import os\n")
    monkeypatch.setattr(e.sys, "path", [str(tmp_path)])
    result = e._check_customization_modules(*_agent_uid_gids())
    assert result.satisfied is False


# ═══════════════════════════════════════════════════════════════════════════
# .pth files
# ═══════════════════════════════════════════════════════════════════════════


def test_no_pth_file_present_compliant(tmp_path, monkeypatch):
    monkeypatch.setattr(e.sys, "path", [str(tmp_path)])
    result = e._check_pth_files(*_agent_uid_gids())
    assert result.satisfied is True
    assert result.status == "no_pth_file_present"


def test_agent_writable_pth_file_non_compliant(tmp_path, monkeypatch):
    (tmp_path / "shadow.pth").write_text("/tmp/somewhere\n")
    monkeypatch.setattr(e.sys, "path", [str(tmp_path)])
    result = e._check_pth_files(*_agent_uid_gids())
    assert result.satisfied is False
    assert result.status == "unsafe_pth_file_present"


def test_pth_file_with_import_line_non_compliant(tmp_path, monkeypatch):
    (tmp_path / "hostile.pth").write_text("import os; os.system('true')\n")
    monkeypatch.setattr(e.sys, "path", [str(tmp_path)])
    result = e._check_pth_files(*_agent_uid_gids())
    assert result.satisfied is False


# ═══════════════════════════════════════════════════════════════════════════
# meta_path hooks
# ═══════════════════════════════════════════════════════════════════════════


def test_only_expected_meta_path_hooks_present(monkeypatch):
    """Isolated from pytest's own `AssertionRewritingHook` (itself an
    injected meta_path finder in the test-running process, correctly
    flagged as unexpected by this same check when present — proven by
    the sibling test below)."""

    import importlib.machinery

    baseline = [
        importlib.machinery.BuiltinImporter,
        importlib.machinery.FrozenImporter,
        importlib.machinery.PathFinder,
    ]
    monkeypatch.setattr(e.sys, "meta_path", baseline)
    result = e._check_meta_path_hooks()
    assert result.satisfied is True


def test_injected_meta_path_hook_flagged(monkeypatch):
    class _HostileFinder:
        pass

    monkeypatch.setattr(e.sys, "meta_path", list(e.sys.meta_path) + [_HostileFinder()])
    result = e._check_meta_path_hooks()
    assert result.satisfied is False
    assert result.status == "unexpected_meta_path_hook_present"


# ═══════════════════════════════════════════════════════════════════════════
# CWD shadow / sys.path order
# ═══════════════════════════════════════════════════════════════════════════


def test_cwd_shadow_check_passes_on_real_environment():
    result = e._check_cwd_shadow_and_path_order()
    assert result.satisfied is True


def test_cwd_shadow_hostile_cwd_precedes_package_dir(tmp_path, monkeypatch):
    import pcae

    real_package_dir = str(Path(pcae.__file__).resolve().parent.parent)
    monkeypatch.setattr(e.sys, "path", [str(tmp_path), real_package_dir])
    monkeypatch.setattr(e.Path, "cwd", staticmethod(lambda: tmp_path))
    result = e._check_cwd_shadow_and_path_order()
    assert result.satisfied is False
    assert result.status == "agent_writable_cwd_precedes_canonical_package_location"


# ═══════════════════════════════════════════════════════════════════════════
# Module origin containment
# ═══════════════════════════════════════════════════════════════════════════


def test_module_origin_containment_passes_on_real_environment():
    result = e._check_module_origin_containment()
    assert result.satisfied is True


def test_module_origin_containment_flags_shadow_package(monkeypatch):
    monkeypatch.setattr(e, "_own_repo_root", lambda: Path("/definitely/not/the/real/root"))
    result = e._check_module_origin_containment()
    assert result.satisfied is False
    assert result.status == "authority_module_origin_outside_canonical_root"


# ═══════════════════════════════════════════════════════════════════════════
# Editable install / launcher / Git trust
# ═══════════════════════════════════════════════════════════════════════════


def test_editable_install_metadata_check_runs_without_exception():
    result = e._check_editable_install_metadata(*_agent_uid_gids())
    assert result.check_id == "HBDC-REQ-035"
    assert isinstance(result.satisfied, bool)


def test_launcher_check_runs_without_exception():
    result = e._check_launcher(*_agent_uid_gids())
    assert result.check_id == "HBDC-REQ-036"
    assert isinstance(result.satisfied, bool)


def test_trusted_git_fake_git_earlier_on_path_rejected(tmp_path, monkeypatch):
    fake_dir = tmp_path / "hostile-bin"
    fake_dir.mkdir()
    fake_git = fake_dir / "git"
    fake_git.write_text("#!/bin/sh\necho fake\n")
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    result = e._check_trusted_git()
    assert result.satisfied is False


def test_trusted_git_check_runs_without_exception():
    result = e._check_trusted_git()
    assert result.check_id == "HBDC-REQ-038"
    assert isinstance(result.satisfied, bool)


# ═══════════════════════════════════════════════════════════════════════════
# Fail-closed on exception
# ═══════════════════════════════════════════════════════════════════════════


def test_unexpected_exception_never_yields_compliant():
    from pcae.core.hatp_class_b_topology_verifier import _safe_check

    def _boom():
        raise ValueError("simulated environment inspection failure")

    result = _safe_check("HBDC-REQ-999", _boom)
    assert result.satisfied is False
    assert result.status == "unexpected_inspection_exception"


def test_current_module_not_in_hmic_frozen_scope():
    from pcae.core.hatp_mandatory_certification import _FROZEN_SRC_PCAE_RELATIVE_FILES

    assert "core/hatp_environment_lock_verifier.py" not in _FROZEN_SRC_PCAE_RELATIVE_FILES


# ═══════════════════════════════════════════════════════════════════════════
# Subprocess fixture: hostile PYTHONPATH end-to-end
# ═══════════════════════════════════════════════════════════════════════════


def test_subprocess_hostile_pythonpath_detected(tmp_path):
    hostile_dir = tmp_path / "hostile"
    hostile_dir.mkdir()
    script = (
        "import sys; sys.path.insert(0, 'src'); "
        "from pcae.core.hatp_environment_lock_verifier import _check_pythonpath, _current_agent_identity; "
        "r = _check_pythonpath(*_current_agent_identity()); "
        "print(r.satisfied, r.status)"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(hostile_dir)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(Path(__file__).resolve().parents[1]),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "False" in result.stdout, result.stdout + result.stderr
