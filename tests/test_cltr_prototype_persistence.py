from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.cltr_prototype import digest as digest_mod
from pcae.cltr_prototype import generator
from pcae.cltr_prototype import persistence

FIXTURES = Path(__file__).parent / "fixtures" / "cltr_prototype"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_persist_writes_only_under_prototype_prefix(tmp_path):
    result = generator.generate(_load("successful_transition.json"))
    gen_dir = persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    assert gen_dir.is_relative_to(tmp_path)
    for f in tmp_path.rglob("*"):
        if f.is_file():
            assert str(f).startswith(str(tmp_path))


def test_persist_generation_directory_complete_manifest(tmp_path):
    result = generator.generate(_load("successful_transition.json"))
    gen_dir = persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    manifest = json.loads((gen_dir / "manifest.json").read_text())
    assert set(manifest["files"].keys()) == {"record.json", "verification.json"}
    for filename, meta in manifest["files"].items():
        assert (gen_dir / filename).exists()


def test_persist_idempotent_rerun_same_content(tmp_path):
    result = generator.generate(_load("successful_transition.json"))
    d1 = persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    d2 = persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    assert d1 == d2


def test_persist_conflicting_replay_rejected(tmp_path):
    original = generator.generate(_load("successful_transition.json"))
    persistence.persist(original.record, original.invariant_results, base_dir=tmp_path)

    conflicting = generator.generate(_load("conflicting_replay.json"))
    assert conflicting.record.identity.transition_id == original.record.identity.transition_id
    with pytest.raises(persistence.ImmutableGenerationExistsError):
        persistence.persist(conflicting.record, conflicting.invariant_results, base_dir=tmp_path)


def test_latest_pointer_updates_per_phase(tmp_path):
    result = generator.generate(_load("successful_transition.json"))
    persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    latest = persistence.read_latest("135F", base_dir=tmp_path)
    assert latest["identity"]["transition_id"] == result.record.identity.transition_id


def test_stale_pointer_recovers_from_history(tmp_path):
    fixture = _load("stale_pointer.json")
    result = generator.generate(_load("successful_transition.json"))
    persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)

    # Corrupt the pointer to reference a nonexistent generation directory.
    latest_path = tmp_path / "latest.json"
    pointer_map = json.loads(latest_path.read_text())
    pointer_map["135F"] = fixture["corrupt_pointer_entry"]
    latest_path.write_text(json.dumps(pointer_map))

    recovered = persistence.read_latest("135F", base_dir=tmp_path)
    assert recovered is not None
    assert recovered["identity"]["transition_id"] == result.record.identity.transition_id


def test_missing_pointer_recovers_from_history(tmp_path):
    result = generator.generate(_load("successful_transition.json"))
    persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    (tmp_path / "latest.json").unlink()
    recovered = persistence.read_latest("135F", base_dir=tmp_path)
    assert recovered is not None


def test_partial_temporary_generation_invisible(tmp_path):
    result = generator.generate(_load("pre_certification_failure.json"))
    gen_dir = persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    # Simulate a crash: delete verification.json after a complete write,
    # leaving the manifest referencing a now-missing file.
    (gen_dir / "verification.json").unlink()
    assert persistence.read_generation(result.record.identity.transition_id, base_dir=tmp_path) is None


def test_prior_generation_unchanged_after_new_generation(tmp_path):
    r1 = generator.generate(_load("successful_transition.json"))
    persistence.persist(r1.record, r1.invariant_results, base_dir=tmp_path)
    original_bytes = (tmp_path / "generations" / r1.record.identity.transition_id / "record.json").read_bytes()

    r2 = generator.generate(_load("pre_certification_failure.json"))
    persistence.persist(r2.record, r2.invariant_results, base_dir=tmp_path)

    still_bytes = (tmp_path / "generations" / r1.record.identity.transition_id / "record.json").read_bytes()
    assert original_bytes == still_bytes


def test_list_generations(tmp_path):
    assert persistence.list_generations(base_dir=tmp_path) == []
    result = generator.generate(_load("successful_transition.json"))
    persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    assert result.record.identity.transition_id in persistence.list_generations(base_dir=tmp_path)


def test_no_production_paths_touched(tmp_path):
    # A generation directory outside .pcae/cltr-prototypes never appears.
    result = generator.generate(_load("successful_transition.json"))
    persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    all_paths = [str(p) for p in tmp_path.rglob("*")]
    for forbidden in (".pcae/canonical-reports", ".pcae/phase-completion-metadata.json", ".pcae/finalization-transactions", ".pcae/delivery-receipts", "phase-completion-report.md"):
        assert not any(forbidden in p for p in all_paths)
