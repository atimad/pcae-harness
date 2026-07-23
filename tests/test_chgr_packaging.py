"""Phase 143E: CHGR schema resource packaging tests.

Mirrors tests/test_schema_runtime_packaging.py's test_136f_* pattern:
verifies the packaged CHGR schema resources are present and loadable from
an editable install and from a built wheel, and that no
``.pcae/governance-records/`` runtime artifact is packaged (there is no
storage this increment; nothing would exist to package).
"""
from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_143e_editable_install_resource_lookup():
    from pcae.schema_resources import chgr_root

    with chgr_root() as root:
        manifest = root / "manifest.json"
        assert manifest.is_file()
        assert '"chgr"' in manifest.read_text(encoding="utf-8")
        for name in (
            "records/decision_template.schema.json",
            "records/human_governance_record.schema.json",
            "records/human_confirmation_evidence.schema.json",
            "records/governance_record_provenance.schema.json",
            "records/governance_record_integrity.schema.json",
            "records/governance_record_lifecycle_event.schema.json",
        ):
            assert (root / name).is_file(), name


@pytest.mark.slow
def test_143e_wheel_contains_all_six_chgr_record_schemas(tmp_path: Path):
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

    manifest_path = "pcae/schema_resources/chgr/manifest.json"
    assert manifest_path in names, f"{manifest_path} missing from wheel"

    record_names = {name for name in names if "chgr/records/" in name}
    assert record_names == {
        "pcae/schema_resources/chgr/records/decision_template.schema.json",
        "pcae/schema_resources/chgr/records/human_governance_record.schema.json",
        "pcae/schema_resources/chgr/records/human_confirmation_evidence.schema.json",
        "pcae/schema_resources/chgr/records/governance_record_provenance.schema.json",
        "pcae/schema_resources/chgr/records/governance_record_integrity.schema.json",
        "pcae/schema_resources/chgr/records/governance_record_lifecycle_event.schema.json",
    }
    shared_names = {name for name in names if "chgr/shared/" in name}
    assert shared_names == {
        "pcae/schema_resources/chgr/shared/digest.schema.json",
        "pcae/schema_resources/chgr/shared/enums.schema.json",
        "pcae/schema_resources/chgr/shared/envelope.schema.json",
        "pcae/schema_resources/chgr/shared/identity.schema.json",
        "pcae/schema_resources/chgr/shared/limitations.schema.json",
        "pcae/schema_resources/chgr/shared/references.schema.json",
    }
    assert not any(name.startswith(".pcae/governance-records") for name in names)


@pytest.mark.slow
def test_143e_installed_wheel_offline_registry_resolves_in_isolated_venv(tmp_path: Path):
    import venv

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
    venv.create(venv_dir, with_pip=True)
    venv_python = venv_dir / "bin" / "python"
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--quiet", str(wheels[0])],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [
            str(venv_python),
            "-c",
            (
                "from pcae.schema_resources import chgr_root\n"
                "from pcae.schema_runtime import build_offline_registry\n"
                "with chgr_root() as root:\n"
                "    registry = build_offline_registry(root)\n"
                "    record_ids = [s for s in registry.schema_ids if '/records/' in s]\n"
                "    assert len(record_ids) == 6, record_ids\n"
                "print('OK')\n"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "OK" in result.stdout
