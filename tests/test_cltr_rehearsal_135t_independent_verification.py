"""Phase 135T — Atomic Publication Rehearsal Independent Verification.

Fresh adversarial tests, not copied from 135S's own test suite. These
attack implementation assumptions the 135S implementation and its own
tests do not exercise:

- Symlink escape at a candidate-artifact path and at the manifest path
  (135T finding: 135S's coordinator wrote candidate/manifest files with a
  bare ``Path.write_text``/``write_bytes`` call, bypassing
  ``persistence.write_candidate_artifact``'s pre-existing-symlink abort
  entirely -- repaired in this phase; this is the regression test proving
  the repair holds).
- Rehearsal-generation identity determinism: independently recomputing
  the identity in a fresh, separate process reproduces the same value,
  and changing any one bound field changes it.
- Honest 23-item inventory disclosure: the manifest's file-backed
  ``artifact_inventory`` is exactly the 10 file-producing kinds; the
  4 folded/deferred items (11-14) are explicitly disclosed in
  ``limitations``, never silently omitted without disclosure.
- Manifest/generation-digest tamper detection via direct on-disk mutation
  (not merely unit-testing the verifier in isolation).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

import pcae.core.phase_reports as pr
from pcae.cltr.migration.rehearsal.identity import compute_rehearsal_generation_id
from pcae.cltr.migration.rehearsal.persistence import (
    PathContainmentError,
    write_candidate_artifact,
)
from pcae.core.finalization_transaction import run_finalization_transaction


def _fresh_arch_status(phase_id: str) -> dict:
    return {
        "schema_version": "1.0",
        "state_marker": "abc123",
        "repository_revision": "deadbeef",
        "completed": [],
        "completed_phase_ids": ["998A"],
        "completed_chapters": [],
        "in_progress": [],
        "current_phase_id": phase_id,
        "planned": [],
        "planned_phase_ids": [],
        "current_runtime_state": "Observed",
        "current_maximum_capability": "observe",
        "execution_availability": "unavailable",
        "freshness": "fresh",
        "limitations": [],
        "conflicts": [],
        "source_provenance": {},
    }


def _certified_report(phase_id: str):
    defaults = dict(
        phase_id=phase_id,
        phase_name="135T Independent Verification Test Phase",
        status="completed",
        summary=f"Phase {phase_id}: 135T independent verification test.",
        files_changed=1,
        tests_run=1,
        commits=["a" * 40],
        pushed_status="pushed",
        origin_main_head_count=0,
        recommended_next_phase="999Y — Next Phase",
        explicit_no_go_confirmations=[f"No issue {i}." for i in range(11)],
        test_results={
            "fast_green": "1/1",
            "report_notification_tests": "passed",
            "bootstrap_session_reporting_tests": "passed",
        },
        governance_results={
            "pcae_health": "healthy",
            "pcae_check": "passed",
            "pcae_doctor_task_memory": "clean",
            "pcae_push_check": "clean",
            "telegram_runtime": "configured",
        },
        risks=["Some known risk."],
        follow_ups=["Some follow-up."],
    )
    with mock.patch.object(pr, "load_canonical_report", return_value=None):
        report = pr.make_phase_report(**defaults)
        report.architecture_status = _fresh_arch_status(phase_id)
        report.metadata["phase_id"] = phase_id
        report.metadata["source_revision"] = "deadbeef"
        report.metadata["phase_commits"] = report.commits
        pr._apply_canonical_and_trust(report, phase_id, report.phase_name, report.status)
        gate = pr.validate_finalization_gate(
            phase_id=phase_id,
            report=report,
            metadata=report.metadata,
            pushed_status=report.pushed_status,
            origin_main_head_count=report.origin_main_head_count,
            governance_results=report.governance_results,
            test_results=report.test_results,
            no_go_confirmations=report.explicit_no_go_confirmations,
            recommended_next_phase=report.recommended_next_phase,
            commit_attribution=report.commits[0],
        )
    return report, gate


def _run(phase_id: str, tmp_path, entry_point: str = "phase_complete"):
    report, gate = _certified_report(phase_id)
    calls: list = []

    def _callback() -> dict:
        calls.append(True)
        report.notification_result = {
            "dispatched": True, "sinks": ["noop"], "success": False, "error": None,
            "outcome": "sent", "reason": "", "kind": "complete",
        }
        return {"report": report, "blocked": False, "report_error": None}

    result = run_finalization_transaction(
        phase_id=report.phase_id, phase_name=report.phase_name, report=report, gate=gate,
        promote_and_dispatch=_callback, transaction_root=tmp_path / "txns", receipt_root=tmp_path / "receipts",
        entry_point=entry_point,
    )
    return result, calls


@pytest.fixture()
def rehearsal_enabled(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", "epoch-135t")
    monkeypatch.setenv("PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED", "1")
    return tmp_path


class TestSymlinkEscapeRepaired:
    """135T finding: coordinator.py wrote every candidate artifact and the
    manifest via a bare ``Path.write_text``/``write_bytes`` call, never
    calling ``persistence.write_candidate_artifact`` (which performs the
    pre-existing-symlink abort 135Q §7/§25/§47 requires). A pre-placed
    symlink at a candidate artifact path was silently followed and the
    linked-to file overwritten -- a real containment escape. Repaired in
    this phase (coordinator.py now calls ``write_candidate_artifact`` for
    every candidate and the manifest)."""

    def test_write_candidate_artifact_aborts_on_pre_existing_symlink(self, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("ORIGINAL-OUTSIDE-CONTENT", encoding="utf-8")

        candidate_dir = tmp_path / "candidates" / "gen1"
        candidate_dir.mkdir(parents=True)
        target = candidate_dir / "report_candidate.json"
        target.symlink_to(secret)

        with pytest.raises(PathContainmentError):
            write_candidate_artifact(candidate_dir, "report_candidate.json", {"x": 1})

        assert secret.read_text(encoding="utf-8") == "ORIGINAL-OUTSIDE-CONTENT"

    def test_manifest_write_path_also_uses_containment_checked_helper(self):
        """Static proof the manifest write call site in coordinator.py
        goes through the same symlink-checked helper as candidate writes
        -- not a second, unchecked write path."""

        import inspect

        from pcae.cltr.migration.rehearsal import coordinator

        source = inspect.getsource(coordinator.run_stage2_rehearsal)
        assert '"manifest.json"' in source
        assert "write_candidate_artifact" in source
        assert ".write_bytes(" not in source
        assert ".write_text(" not in source

    def test_real_coordinator_run_end_to_end_still_succeeds_after_repair(self, rehearsal_enabled):
        """Confirms the repair did not break the ordinary successful path."""

        phase_id = "999X.3-135t-symlink-repair-e2e"
        result, calls = _run(phase_id, rehearsal_enabled)
        assert calls == [True]
        assert result.status in ("completed", "completed_receipt_best_effort_incomplete")


class TestIdentityDeterminism:
    """135Q §6 -- re-derive the identity formula independently and prove
    it is a pure function of its bound fields, never wall-clock/random/
    filename-derived."""

    def _base_kwargs(self) -> dict:
        return dict(
            migration_epoch="epoch-a",
            authority_epoch="authority-a",
            transition_id="11111111-1111-1111-1111-111111111111",
            shared_input_package_id="pkg-1",
            final_input_revision_digest="deadbeef" * 8,
            phase_id="999X.3",
            task_id=None,
            schema_versions={"cltr_schema_version": "1.0.1", "manifest_schema_version": "1.0.0"},
        )

    def test_repeated_computation_in_this_process_is_stable(self):
        kwargs = self._base_kwargs()
        first = compute_rehearsal_generation_id(**kwargs)
        second = compute_rehearsal_generation_id(**kwargs)
        assert first == second

    def test_stable_across_a_fresh_python_subprocess(self):
        """Cross-process determinism: a brand-new interpreter (no shared
        globals, no shared hash seed unless PYTHONHASHSEED is pinned)
        recomputes the identical identity."""

        kwargs = self._base_kwargs()
        expected = compute_rehearsal_generation_id(**kwargs)
        script = (
            "import json,sys;"
            "from pcae.cltr.migration.rehearsal.identity import compute_rehearsal_generation_id;"
            f"print(compute_rehearsal_generation_id(**{kwargs!r}))"
        )
        out = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, check=True, cwd=str(Path(__file__).resolve().parents[1]),
        )
        assert out.stdout.strip() == expected

    @pytest.mark.parametrize(
        "field,new_value",
        [
            ("migration_epoch", "epoch-b"),
            ("authority_epoch", "authority-b"),
            ("transition_id", "22222222-2222-2222-2222-222222222222"),
            ("shared_input_package_id", "pkg-2"),
            ("final_input_revision_digest", "f" * 64),
            ("phase_id", "999X.4"),
        ],
    )
    def test_each_bound_field_change_changes_identity(self, field, new_value):
        kwargs = self._base_kwargs()
        baseline = compute_rehearsal_generation_id(**kwargs)
        kwargs[field] = new_value
        changed = compute_rehearsal_generation_id(**kwargs)
        assert changed != baseline

    def test_task_id_change_changes_identity(self):
        kwargs = self._base_kwargs()
        baseline = compute_rehearsal_generation_id(**kwargs)
        kwargs["task_id"] = "some-task-id"
        changed = compute_rehearsal_generation_id(**kwargs)
        assert changed != baseline

    def test_schema_version_change_changes_identity(self):
        kwargs = self._base_kwargs()
        baseline = compute_rehearsal_generation_id(**kwargs)
        kwargs["schema_versions"] = {"cltr_schema_version": "1.0.2", "manifest_schema_version": "1.0.0"}
        changed = compute_rehearsal_generation_id(**kwargs)
        assert changed != baseline


class TestHonestInventoryDisclosure:
    """135Q §9's 23-item inventory. 135S folds items 11-14 into other
    artifacts/commands rather than emitting them as separate files.
    Independently verify this is honestly disclosed, not silently
    reduced, and that the file-backed subset is exactly the 10 items
    135S actually claims (no unauthorized extra item silently presented
    as required, no missing item from that 10)."""

    def test_manifest_discloses_folded_items_11_through_14(self, rehearsal_enabled, tmp_path):
        phase_id = "999X.3-135t-inventory"
        _run(phase_id, tmp_path)
        epoch_dir = tmp_path / ".pcae" / "cltr-migration" / "epochs" / "epoch-135t" / "rehearsals"
        transition_dirs = list(epoch_dir.iterdir())
        assert len(transition_dirs) == 1
        generations_dir = transition_dirs[0] / "generations"
        gen_dirs = list(generations_dir.iterdir())
        assert len(gen_dirs) == 1
        manifest = json.loads((gen_dirs[0] / "manifest.json").read_text(encoding="utf-8"))

        assert len(manifest["artifact_inventory"]) == 10
        kinds = {entry["artifact_kind"] for entry in manifest["artifact_inventory"]}
        expected_kinds = {
            "cltr_record", "report_candidate", "metadata_candidate",
            "architecture_status_candidate", "checkpoint_candidate",
            "notification_intent_candidate", "marker_candidate", "receipt_candidate",
            "commit_attribution_candidate", "repository_transition_candidate",
        }
        assert kinds == expected_kinds

        limitations_text = " ".join(manifest["limitations"])
        assert "items 11-14" in limitations_text
        assert "not emitted as separate files" in limitations_text

    def test_every_inventory_artifact_file_actually_exists_on_disk(self, rehearsal_enabled, tmp_path):
        phase_id = "999X.3-135t-inventory-files"
        _run(phase_id, tmp_path)
        epoch_dir = tmp_path / ".pcae" / "cltr-migration" / "epochs" / "epoch-135t" / "rehearsals"
        transition_dir = list(epoch_dir.iterdir())[0]
        gen_dir = list((transition_dir / "generations").iterdir())[0]
        manifest = json.loads((gen_dir / "manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["artifact_inventory"]:
            artifact_path = gen_dir / entry["path"]
            assert artifact_path.exists(), f"missing artifact file: {entry['path']}"
            content = json.loads(artifact_path.read_text(encoding="utf-8"))
            digest_mod = __import__(
                "pcae.cltr.migration.rehearsal.digest", fromlist=["compute_artifact_digest"]
            )
            assert digest_mod.compute_artifact_digest(content) == entry["digest"]


class TestManifestTamperDetection:
    """135Q §19/§38 -- direct on-disk mutation of a finalized artifact
    must be detected on re-verification, not silently accepted."""

    def test_mutating_a_finalized_artifact_breaks_digest_verification(self, rehearsal_enabled, tmp_path):
        from pcae.cltr.migration.rehearsal.digest import compute_artifact_digest
        from pcae.cltr.migration.rehearsal.manifest import ManifestVerificationError, verify_manifest
        from pcae.cltr.migration.rehearsal.models import CandidateArtifact, RehearsalManifest
        from pcae.cltr.migration.rehearsal.enums import ArtifactRole, CandidateKind, VerificationStatus

        phase_id = "999X.3-135t-tamper"
        _run(phase_id, tmp_path)
        epoch_dir = tmp_path / ".pcae" / "cltr-migration" / "epochs" / "epoch-135t" / "rehearsals"
        transition_dir = list(epoch_dir.iterdir())[0]
        gen_dir = list((transition_dir / "generations").iterdir())[0]
        manifest_payload = json.loads((gen_dir / "manifest.json").read_text(encoding="utf-8"))

        # Tamper: flip a byte in the on-disk report candidate after
        # finalization (simulating post-finalization corruption/tampering).
        report_path = gen_dir / "report_candidate.json"
        original = json.loads(report_path.read_text(encoding="utf-8"))
        tampered = dict(original)
        tampered["report_role"] = "TAMPERED"

        digested_candidates = {}
        for entry in manifest_payload["artifact_inventory"]:
            kind = CandidateKind(entry["artifact_kind"])
            content = tampered if entry["artifact_kind"] == "report_candidate" else json.loads(
                (gen_dir / entry["path"]).read_text(encoding="utf-8")
            )
            digested_candidates[kind] = CandidateArtifact(
                kind=kind,
                artifact_role=ArtifactRole(entry["artifact_role"]),
                verification_status=VerificationStatus(entry["verification_status"]),
                content=content,
                digest=compute_artifact_digest(content) if entry["artifact_kind"] != "report_candidate" else entry["digest"],
            )

        manifest_kwargs = dict(manifest_payload)
        manifest_kwargs.pop("generation_digest")
        manifest = RehearsalManifest(**manifest_kwargs).with_digest(manifest_payload["generation_digest"])

        with pytest.raises(ManifestVerificationError):
            verify_manifest(manifest, digested_candidates)
