"""Phase 147P — Authority Evaluation Persistence Boundary Hardening.

Adversarial and regression suite for the bundled repair of AESIC-N-01
(canonical-pointer cross-key confusion) and 147O.2-F-1 (``package_id``
single-level path containment), both carried forward as contained-but-open
findings through Phase 147O.3's chapter certification.

Independently authored against ``pcae.aesic.storage.AuthorityEvaluationRecordStore``
directly (isolating the storage layer's own guarantee, per this phase's
mandate) plus a handful of production-wiring/diagnostics regression checks.
Does not duplicate ``tests/test_phase_147n_authority_evaluation_integration_independent_verification.py``
or ``tests/test_phase_147o2_authority_evaluation_production_wiring_independent_verification.py``,
which this phase updated in place to assert the post-repair behavior for
the two findings they originally demonstrated as open.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from pcae.aesic.diagnostics import summarize_package
from pcae.aesic.errors import (
    AuthorityEvaluationRecordCorruptError,
    AuthorityEvaluationStorageIdentifierError,
    CanonicalPointerCorruptError,
)
from pcae.aesic.records import (
    AuthorityEvaluationRecord,
    CanonicalPointer,
    _compute_pointer_digest,
    aer_to_payload,
    pointer_to_payload,
)
from pcae.aesic.storage import AuthorityEvaluationRecordStore, _write_atomic_json
from pcae.authority_evaluation.models import AuthorityEvaluationOutcome, EvaluationResult
from pcae.commands.aesic_status import run_aesic_status

_TS = "2026-01-01T00:00:00Z"


def _outcome(
    *,
    template_ref="tpl-1",
    template_version="v1",
    claimed_identity="alice",
    result=EvaluationResult.ELIGIBLE,
    citation_text="Only Finance may approve.",
    declaration_ref="tpl-1::v1",
) -> AuthorityEvaluationOutcome:
    if result is not EvaluationResult.ELIGIBLE:
        citation_text = None
    return AuthorityEvaluationOutcome(
        template_ref=template_ref,
        template_version=template_version,
        claimed_identity=claimed_identity,
        evaluation_result=result,
        declaration_ref=declaration_ref,
        citation_text=citation_text,
        evaluated_at=_TS,
        evaluator_version="aem-evaluator/1.0",
    )


def _write_aer(store: AuthorityEvaluationRecordStore, *, package_id: str, evaluation_id: str, record_id: str) -> AuthorityEvaluationRecord:
    record = AuthorityEvaluationRecord(
        record_id=record_id,
        package_id=package_id,
        evaluation_id=evaluation_id,
        outcome=_outcome(),
        evaluated_at=_TS,
    )
    store.write_record(record)
    return record


def _valid_pointer_for(record: AuthorityEvaluationRecord) -> CanonicalPointer:
    return CanonicalPointer(
        package_id=record.package_id,
        evaluation_id=record.evaluation_id,
        record_id=record.record_id,
        record_digest=aer_to_payload(record)["record_digest"],
    )


def _forge_pointer_at(store: AuthorityEvaluationRecordStore, *, filename_key: str, content: CanonicalPointer) -> Path:
    """Write ``content`` (a self-consistent, validly-digested pointer) at
    the physical location for ``filename_key`` -- i.e. simulate a pointer
    file whose location and embedded content disagree, bypassing
    ``write_pointer`` (which always keeps them equal) exactly as a
    filesystem-tampering or copy/relocation attacker would."""

    payload = pointer_to_payload(content)
    path = store._root / "pointers" / f"{filename_key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_atomic_json(path, payload)
    return path


# ===========================================================================
# 1. Identifier path-safety invariant (147O.2-F-1)
# ===========================================================================


class TestIdentifierPathSafety:
    @pytest.mark.parametrize(
        "bad_id",
        [
            "..",
            ".",
            "../foo",
            "foo/..",
            "foo/bar",
            "/foo",
            "",
            "foo\x00bar",
        ],
    )
    def test_record_path_rejects_invalid_package_id(self, tmp_path, bad_id):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._record_path(bad_id, "ev-1")

    @pytest.mark.parametrize("bad_id", ["..", ".", "foo/bar", "/foo", ""])
    def test_pointer_path_rejects_invalid_package_id(self, tmp_path, bad_id):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._pointer_path(bad_id)

    @pytest.mark.parametrize("bad_id", ["..", ".", "foo/bar", "/foo", ""])
    def test_list_evaluation_ids_rejects_invalid_package_id(self, tmp_path, bad_id):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store.list_evaluation_ids(bad_id)

    @pytest.mark.parametrize("bad_id", ["..", ".", "foo/bar"])
    def test_evaluation_id_component_also_validated(self, tmp_path, bad_id):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._record_path("pkg-1", bad_id)

    def test_valid_package_id_unaffected(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        path = store._record_path("prp-abc123", "ev-1")
        assert path == tmp_path / "records" / "prp-abc123" / "ev-1.json"

    def test_valid_package_id_with_previously_substituted_chars_still_works(self, tmp_path):
        # Characters _safe_name would have substituted (spaces) remain
        # accepted -- only path-traversal-relevant values are now rejected.
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        path = store._record_path("pkg with spaces", "ev-1")
        assert store._root.resolve() in path.resolve().parents

    def test_read_record_rejects_invalid_package_id_before_touching_disk(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store.read_record("..", "ev-1")
        assert not tmp_path.exists() or not any(tmp_path.iterdir())

    def test_read_canonical_rejects_invalid_package_id_before_touching_disk(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store.read_canonical("..")


# ===========================================================================
# 2. Root containment, including symlink escapes (147O.2-F-1, §10)
# ===========================================================================


class TestRootContainment:
    def test_symlinked_records_directory_escaping_root_is_rejected(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path / "aer-root")
        (store._root / "records").mkdir(parents=True)
        outside = tmp_path / "outside"
        outside.mkdir()
        (store._root / "records" / "pkg-evil").symlink_to(outside, target_is_directory=True)

        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._records_directory("pkg-evil")
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._record_path("pkg-evil", "ev-1")

    def test_symlinked_pointers_directory_escaping_root_is_rejected(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path / "aer-root")
        store._root.mkdir(parents=True)
        outside = tmp_path / "outside-pointers"
        outside.mkdir()
        (store._root / "pointers").symlink_to(outside, target_is_directory=True)

        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._pointer_path("pkg-evil")

    def test_ordinary_valid_ids_remain_contained(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_path = store._record_path("pkg-1", "ev-1")
        pointer_path = store._pointer_path("pkg-1")
        assert store._root.resolve() in record_path.resolve().parents
        assert store._root.resolve() in pointer_path.resolve().parents


# ===========================================================================
# 3. Cross-key substitution attacks (AESIC-N-01)
# ===========================================================================


class TestCrossKeySubstitution:
    def test_pointer_physically_at_A_embeds_key_B_rejected(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _write_aer(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        _forge_pointer_at(store, filename_key="pkg-A", content=_valid_pointer_for(record_b))

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-A")

    def test_pointer_under_A_references_valid_AER_under_B(self, tmp_path):
        # Same mechanics as the above, phrased as a distinct scenario: B's
        # AER is fully valid (correct digest, exists on disk) -- the only
        # thing wrong is the pointer's embedded key disagreeing with where
        # the pointer itself is stored.
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _write_aer(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        assert store.read_record("pkg-B", "ev-b") is not None  # B's AER is genuinely valid
        _forge_pointer_at(store, filename_key="pkg-A", content=_valid_pointer_for(record_b))

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-A")

    def test_record_id_collision_across_keys_does_not_defeat_key_binding(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        # Two AERs, in different package namespaces, that happen to share a
        # record_id (a defense-in-depth adversarial construction -- never
        # produced by AES's own record_id generation, but not something
        # the storage layer should trust to disambiguate a key).
        record_a = _write_aer(store, package_id="pkg-A", evaluation_id="ev-a", record_id="shared-rec")
        record_b = _write_aer(store, package_id="pkg-B", evaluation_id="ev-b", record_id="shared-rec")
        assert record_a.record_id == record_b.record_id

        _forge_pointer_at(store, filename_key="pkg-A", content=_valid_pointer_for(record_b))
        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-A")

        # The legitimate same-key pointer for pkg-A is unaffected.
        store.write_pointer(_valid_pointer_for(record_a))
        assert store.read_canonical("pkg-A").record_id == "shared-rec"
        assert store.read_canonical("pkg-A").package_id == "pkg-A"

    def test_attacker_recomputed_valid_pointer_digest_over_forged_content_still_rejected(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _write_aer(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        content = {
            "package_id": "pkg-B",
            "evaluation_id": "ev-b",
            "record_id": "rec-b",
            "record_digest": aer_to_payload(record_b)["record_digest"],
            "schema_version": "aesic-authority-evaluation-pointer/1.0",
        }
        forged_payload = dict(content)
        # A fully self-consistent, correctly-recomputed pointer_digest --
        # digest verification alone cannot catch this; only the key-binding
        # check can.
        forged_payload["pointer_digest"] = _compute_pointer_digest(content)
        path = store._pointer_path("pkg-A")
        _write_atomic_json(path, forged_payload)

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-A")

    def test_aer_physically_copied_across_package_directories_rejected_by_record_key_check(self, tmp_path):
        """Simulates a filesystem-level AER copy (e.g. a careless backup/
        restore across package namespaces) landing content whose own
        embedded ``package_id`` disagrees with the directory it now lives
        under -- the AER's own compound-key binding must still be enforced
        even when the pointer's key matches the query."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _write_aer(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        payload_b = aer_to_payload(record_b)

        # Copy B's (validly-digested) AER content verbatim into A's own
        # records directory, under A's evaluation_id.
        dest = store._root / "records" / "pkg-A" / "ev-a.json"
        _write_atomic_json(dest, payload_b)

        # A same-key pointer for pkg-A, naming the copied evaluation.
        forged_pointer = CanonicalPointer(
            package_id="pkg-A",
            evaluation_id="ev-a",
            record_id="rec-b",
            record_digest=payload_b["record_digest"],
        )
        store.write_pointer(forged_pointer)

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-A")

    def test_pointer_wholesale_copied_from_B_into_A(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _write_aer(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        store.write_pointer(_valid_pointer_for(record_b))
        legit_path = store._pointer_path("pkg-B")

        # Copy the entire, legitimate pkg-B pointer file byte-for-byte into
        # pkg-A's own pointer slot.
        forged_path = store._pointer_path("pkg-A")
        forged_path.write_bytes(legit_path.read_bytes())

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-A")
        # pkg-B's own legitimate read is unaffected.
        assert store.read_canonical("pkg-B").record_id == "rec-b"

    def test_historical_superseded_AER_shares_metadata_cross_key_rejected(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        # Two generations under pkg-A (supersession).
        gen1 = _write_aer(store, package_id="pkg-A", evaluation_id="ev-a1", record_id="rec-a1")
        store.write_pointer(_valid_pointer_for(gen1))
        gen2 = _write_aer(store, package_id="pkg-A", evaluation_id="ev-a2", record_id="rec-a2")
        store.write_pointer(_valid_pointer_for(gen2))
        # A superseded, no-longer-canonical generation (gen1) still exists
        # on disk under pkg-A. Forge a pointer for pkg-B naming gen1.
        _forge_pointer_at(store, filename_key="pkg-B", content=_valid_pointer_for(gen1))

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-B")
        # Canonical pkg-A read is unaffected by the pkg-B forgery attempt.
        assert store.read_canonical("pkg-A").record_id == "rec-a2"

    def test_cross_session_key_substitution_rejected(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        session1_record = _write_aer(store, package_id="pkg-session-1", evaluation_id="ev-1", record_id="rec-1")
        _forge_pointer_at(store, filename_key="pkg-session-2", content=_valid_pointer_for(session1_record))

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-session-2")

    def test_cross_template_key_substitution_rejected(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_tpl_a = AuthorityEvaluationRecord(
            record_id="rec-tpl-a", package_id="pkg-tpl-a", evaluation_id="ev-1",
            outcome=_outcome(template_ref="tpl-a", declaration_ref="tpl-a::v1"), evaluated_at=_TS,
        )
        store.write_record(record_tpl_a)
        _forge_pointer_at(store, filename_key="pkg-tpl-b", content=_valid_pointer_for(record_tpl_a))

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-tpl-b")


# ===========================================================================
# 4. Recovery, restart, and diagnostics compatibility
# ===========================================================================


class TestRecoveryAndDiagnosticsCompatibility:
    def test_corrupt_cross_key_pointer_fails_closed_and_does_not_redirect_recovery(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_a = _write_aer(store, package_id="pkg-A", evaluation_id="ev-a", record_id="rec-a")
        _forge_pointer_at(store, filename_key="pkg-B", content=_valid_pointer_for(record_a))

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-B")

        # Recovery: write pkg-B's own, genuinely-correct AER and pointer.
        # The requested/current compound key ("pkg-B") remains authoritative
        # -- recovery is not redirected to pkg-A's content.
        record_b = _write_aer(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        store.write_pointer(_valid_pointer_for(record_b))
        assert store.read_canonical("pkg-B").record_id == "rec-b"
        # pkg-A's own canonical state, meanwhile, is untouched.
        store.write_pointer(_valid_pointer_for(record_a))
        assert store.read_canonical("pkg-A").record_id == "rec-a"

    def test_restart_new_store_instance_same_root_sees_consistent_state(self, tmp_path):
        store1 = AuthorityEvaluationRecordStore(root=tmp_path)
        record = _write_aer(store1, package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1")
        store1.write_pointer(_valid_pointer_for(record))

        store2 = AuthorityEvaluationRecordStore(root=tmp_path)  # simulates process restart
        assert store2.read_canonical("pkg-1").record_id == "rec-1"

    def test_diagnostic_lookup_with_invalid_key_is_safe_read_only_no_crash(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        store = AuthorityEvaluationRecordStore()
        for bad_id in ("..", ".", "foo/bar", "/etc/passwd"):
            summary = summarize_package(store, bad_id)
            assert summary.canonical_record_id is None
            assert summary.canonical_pointer_ok is False
            assert summary.total_attempts == 0

    def test_cli_status_with_invalid_package_id_does_not_crash(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        class _Args:
            json = True
            package_id = ".."

        buf = io.StringIO()
        from contextlib import redirect_stdout

        with redirect_stdout(buf):
            exit_code = run_aesic_status(_Args())
        assert exit_code == 0
        payload = json.loads(buf.getvalue())
        assert payload["current_effective_stage_2"]["canonical_pointer_ok"] is False


# ===========================================================================
# 5. Regression: unchanged behavior for valid, same-key operations
# ===========================================================================


class TestRegressionValidOperationsUnchanged:
    def test_normal_commit_and_read(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record = _write_aer(store, package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1")
        assert store.read_record("pkg-1", "ev-1").record_id == "rec-1"
        assert store.read_record("pkg-1", "ev-1").package_id == "pkg-1"

    def test_same_key_canonical_pointer_read(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record = _write_aer(store, package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1")
        store.write_pointer(_valid_pointer_for(record))
        canonical = store.read_canonical("pkg-1")
        assert canonical is not None
        assert canonical.record_id == "rec-1"
        assert canonical.package_id == "pkg-1"

    def test_no_pointer_yet_returns_none_not_an_error(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        _write_aer(store, package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1")
        assert store.read_canonical("pkg-1") is None

    def test_supersession_pointer_advances_and_stays_key_bound(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        gen1 = _write_aer(store, package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1")
        store.write_pointer(_valid_pointer_for(gen1))
        gen2 = _write_aer(store, package_id="pkg-1", evaluation_id="ev-2", record_id="rec-2")
        store.write_pointer(_valid_pointer_for(gen2))
        canonical = store.read_canonical("pkg-1")
        assert canonical.record_id == "rec-2"
        assert canonical.package_id == "pkg-1"

    def test_multiple_packages_never_collide(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_a = _write_aer(store, package_id="pkg-A", evaluation_id="ev-1", record_id="rec-a")
        record_b = _write_aer(store, package_id="pkg-B", evaluation_id="ev-1", record_id="rec-b")
        store.write_pointer(_valid_pointer_for(record_a))
        store.write_pointer(_valid_pointer_for(record_b))
        assert store.read_canonical("pkg-A").record_id == "rec-a"
        assert store.read_canonical("pkg-B").record_id == "rec-b"

    def test_ordinary_digest_tamper_still_caught_independently_of_key_binding(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record = _write_aer(store, package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1")
        store.write_pointer(_valid_pointer_for(record))
        path = store._pointer_path("pkg-1")
        payload = json.loads(path.read_text())
        payload["pointer_digest"] = "0" * 64
        path.write_text(json.dumps(payload))
        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-1")

    def test_ordinary_aer_digest_tamper_still_caught(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record = _write_aer(store, package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1")
        path = store._record_path("pkg-1", "ev-1")
        payload = json.loads(path.read_text())
        payload["outcome"]["evaluation_result"] = "ineligible"
        path.write_text(json.dumps(payload))
        with pytest.raises(AuthorityEvaluationRecordCorruptError):
            store.read_record("pkg-1", "ev-1")

    def test_list_evaluation_ids_unconfigured_package_returns_empty_tuple(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        assert store.list_evaluation_ids("never-written") == ()

    def test_diagnostics_summary_for_valid_package_unaffected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        store = AuthorityEvaluationRecordStore()
        record = _write_aer(store, package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1")
        store.write_pointer(_valid_pointer_for(record))
        summary = summarize_package(store, "pkg-1")
        assert summary.canonical_record_id == "rec-1"
        assert summary.canonical_pointer_ok is True
        assert summary.total_attempts == 1
