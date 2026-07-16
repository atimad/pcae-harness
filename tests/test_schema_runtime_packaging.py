"""Phase 136F: packaging tests resolving PREREQUISITE-136E-1.

Verifies that the packaged generic schema resource
(``src/pcae/schema_resources/smoke/generic_smoke_record.schema.json``)
is present and loadable from an editable install, a built wheel, and a
built source distribution.

Phase 136H updates the wheel/sdist assertions: the Stage 3 shared-core
package (``cltr_cutover/shared/*``, Implementation Group 1 only) is now
packaged and present, so the prior "no cltr_cutover in the archive"
assertion is replaced with the still-true, narrower guarantee that no
``records/`` directory and no authority-bearing record schema filename
is present in either archive.
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


_FORBIDDEN_RECORD_SCHEMA_FILENAMES = (
    # authority_epoch.schema.json and authority_state.schema.json are no
    # longer forbidden: Phase 136J legitimately packages them as
    # Implementation Group 2. cutover_request.schema.json and
    # readiness_package.schema.json are no longer forbidden: Phase 136L
    # legitimately packages them as Implementation Group 3.
    # human_authorization.schema.json, cutover_candidate.schema.json, and
    # certification.schema.json are no longer forbidden: Phase 136N
    # legitimately packages them as Implementation Group 4.
    # publication_attempt.schema.json and publication_evidence.schema.json
    # are no longer forbidden: Phase 136P legitimately packages them as
    # Implementation Group 5. Every later-group (6+) record schema remains
    # forbidden until its own phase.
    "concurrency_conflict.schema.json",
    "recovery_journal_entry.schema.json",
    "quarantine_record.schema.json",
    "notification_authority_binding.schema.json",
    "marker_authority_binding.schema.json",
    "receipt_authority_binding.schema.json",
    "compatibility_state.schema.json",
)


@pytest.mark.slow
def test_136f_wheel_contains_smoke_schema_and_no_stage3_record_schema(tmp_path: Path):
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
    shared_envelope_path = "pcae/schema_resources/cltr_cutover/shared/envelope.schema.json"
    assert shared_envelope_path in names, f"{shared_envelope_path} missing from wheel (136H shared core)"
    # Phase 136J packages 2 Group 2 record schemas; Phase 136L adds 2
    # Group 3 record schemas; Phase 136N adds 3 Group 4 record schemas;
    # Phase 136P adds 2 Group 5 record schemas (9 total); no other
    # records/ resource is permitted.
    record_names = [name for name in names if "cltr_cutover/records/" in name]
    assert set(record_names) == {
        "pcae/schema_resources/cltr_cutover/records/authority_epoch.schema.json",
        "pcae/schema_resources/cltr_cutover/records/authority_state.schema.json",
        "pcae/schema_resources/cltr_cutover/records/cutover_request.schema.json",
        "pcae/schema_resources/cltr_cutover/records/readiness_package.schema.json",
        "pcae/schema_resources/cltr_cutover/records/human_authorization.schema.json",
        "pcae/schema_resources/cltr_cutover/records/cutover_candidate.schema.json",
        "pcae/schema_resources/cltr_cutover/records/certification.schema.json",
        "pcae/schema_resources/cltr_cutover/records/publication_attempt.schema.json",
        "pcae/schema_resources/cltr_cutover/records/publication_evidence.schema.json",
    }
    for forbidden in _FORBIDDEN_RECORD_SCHEMA_FILENAMES:
        assert not any(name.endswith(forbidden) for name in names)
    assert not any(name.startswith(".pcae/") for name in names)
    assert not any(name.endswith("session.json") for name in names)


@pytest.mark.slow
def test_136f_sdist_contains_smoke_schema_and_no_stage3_record_schema(tmp_path: Path):
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
    assert any(name.endswith("cltr_cutover/shared/envelope.schema.json") for name in names)
    # Phase 136J packages 2 Group 2 record schemas; Phase 136L adds 2
    # Group 3 record schemas; Phase 136N adds 3 Group 4 record schemas;
    # Phase 136P adds 2 Group 5 record schemas (9 total); no other
    # records/ resource is permitted.
    record_names = {name for name in names if "cltr_cutover/records/" in name}
    assert {Path(name).name for name in record_names} == {
        "authority_epoch.schema.json",
        "authority_state.schema.json",
        "cutover_request.schema.json",
        "readiness_package.schema.json",
        "human_authorization.schema.json",
        "cutover_candidate.schema.json",
        "certification.schema.json",
        "publication_attempt.schema.json",
        "publication_evidence.schema.json",
    }
    for forbidden in _FORBIDDEN_RECORD_SCHEMA_FILENAMES:
        assert not any(name.endswith(forbidden) for name in names)
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
