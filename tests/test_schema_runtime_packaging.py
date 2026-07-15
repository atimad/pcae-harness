"""Phase 136F: packaging tests resolving PREREQUISITE-136E-1.

Verifies that the packaged generic schema resource
(``src/pcae/schema_resources/smoke/generic_smoke_record.schema.json``)
is present and loadable from an editable install, a built wheel, and a
built source distribution -- and that no Stage 3 schema directory is
present in any of them.
"""
from __future__ import annotations

import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_136f_editable_install_resource_lookup():
    from pcae.schema_resources import smoke_schema_root

    with smoke_schema_root() as root:
        target = root / "generic_smoke_record.schema.json"
        assert target.is_file()
        assert '"$id"' in target.read_text(encoding="utf-8")


@pytest.mark.slow
def test_136f_wheel_contains_smoke_schema_and_no_stage3_directory(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()

    smoke_path = "pcae/schema_resources/smoke/generic_smoke_record.schema.json"
    assert smoke_path in names, f"{smoke_path} missing from wheel; names sample: {names[:20]}"
    assert not any("cltr_cutover" in name for name in names)
    assert not any(name.startswith(".pcae/") for name in names)
    assert not any(name.endswith("session.json") for name in names)


@pytest.mark.slow
def test_136f_sdist_contains_smoke_schema_and_no_stage3_directory(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(sdists) == 1, f"expected exactly one sdist, found {sdists}"

    with tarfile.open(sdists[0]) as archive:
        names = archive.getnames()

    assert any(name.endswith("schema_resources/smoke/generic_smoke_record.schema.json") for name in names)
    assert not any("cltr_cutover" in name for name in names)
    assert not any("/.pcae/" in name or name.split("/", 1)[-1].startswith(".pcae/") for name in names)


@pytest.mark.slow
def test_136f_installed_wheel_resource_lookup_in_isolated_venv(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    venv_python = venv_dir / "bin" / "python"
    assert venv_python.exists()

    install = subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--no-deps", str(wheels[0])],
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr

    probe = subprocess.run(
        [
            str(venv_python),
            "-c",
            "from pcae.schema_resources import smoke_schema_root\n"
            "with smoke_schema_root() as root:\n"
            "    target = root / 'generic_smoke_record.schema.json'\n"
            "    assert target.is_file(), target\n"
            "    print('OK')\n",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr
    assert "OK" in probe.stdout
