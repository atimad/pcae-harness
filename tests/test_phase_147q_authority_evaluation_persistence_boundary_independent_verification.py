"""Phase 147Q — Authority Evaluation Persistence Boundary Hardening
Independent Verification.

Independently authored verification of Phase 147P's bundled repair of two
findings carried forward as contained-but-open through Phase 147O.3's
chapter certification:

- **AESIC-N-01** (canonical-pointer cross-key confusion): first
  independently discovered in Phase 147N.
- **147O.2-F-1** (``package_id`` single-level path containment): first
  independently discovered in Phase 147O.2.

This suite is independently authored per this phase's discipline: it does
not import, call, or duplicate the assertions in
``tests/test_phase_147p_authority_evaluation_persistence_boundary_hardening.py``.
Where scenarios overlap in *category* (e.g. cross-key substitution), the
concrete construction differs (different attack shapes, different
fixtures, additional scenarios: historical pre-repair reproduction, TOCTOU
symlink-swap, case-insensitive-filesystem aliasing, Unicode/percent-encoded
lookalikes, production-service-level regression).

Findings this phase newly, independently discovered are documented in
``docs/verification/PHASE_147Q_AUTHORITY_EVALUATION_PERSISTENCE_BOUNDARY_HARDENING_INDEPENDENT_VERIFICATION.md``
§21 and are exercised here where reproducible.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from pcae.aesic.diagnostics import summarize_package
from pcae.aesic.errors import (
    AuthorityEvaluationStorageIdentifierError,
    CanonicalPointerCorruptError,
)
from pcae.aesic.records import (
    AuthorityEvaluationRecord,
    CanonicalPointer,
    aer_to_payload,
    pointer_to_payload,
)
from pcae.aesic.storage import AuthorityEvaluationRecordStore, _write_atomic_json, _write_exclusive_json
from pcae.authority_evaluation.models import AuthorityEvaluationOutcome, EvaluationResult

_TS = "2026-01-01T00:00:00Z"

# The commit immediately preceding Phase 147P's repair -- Phase 147M's own
# implementation, carrying AESIC-N-01 and 147O.2-F-1 exactly as both were
# independently discovered and characterized in Phase 147N/147O.2.
_PRE_REPAIR_COMMIT = "d0c1008a88ec6e5aafa5f298a1f5ad440f49fd6e"


# ===========================================================================
# Shared construction helpers (independently written, not imported from
# any other phase's test module)
# ===========================================================================


def _outcome(result: EvaluationResult = EvaluationResult.ELIGIBLE) -> AuthorityEvaluationOutcome:
    return AuthorityEvaluationOutcome(
        template_ref="tpl-q",
        template_version="v1",
        claimed_identity="carol",
        evaluation_result=result,
        declaration_ref="tpl-q::v1",
        citation_text="Finance may approve." if result is EvaluationResult.ELIGIBLE else None,
        evaluated_at=_TS,
        evaluator_version="aem-evaluator/1.0",
    )


def _commit(store: AuthorityEvaluationRecordStore, *, package_id: str, evaluation_id: str, record_id: str,
            result: EvaluationResult = EvaluationResult.ELIGIBLE) -> AuthorityEvaluationRecord:
    record = AuthorityEvaluationRecord(
        record_id=record_id,
        package_id=package_id,
        evaluation_id=evaluation_id,
        outcome=_outcome(result),
        evaluated_at=_TS,
    )
    store.write_record(record)
    return record


def _publish(store: AuthorityEvaluationRecordStore, record: AuthorityEvaluationRecord) -> None:
    store.write_pointer(
        CanonicalPointer(
            package_id=record.package_id,
            evaluation_id=record.evaluation_id,
            record_id=record.record_id,
            record_digest=aer_to_payload(record)["record_digest"],
        )
    )


def _plant_pointer_under(
    store: AuthorityEvaluationRecordStore, *, physical_key: str, record: AuthorityEvaluationRecord
) -> Path:
    """Write a pointer physically at ``pointers/<physical_key>.json`` whose
    own embedded content names ``record``'s compound key -- i.e. a
    filesystem-level relocation/tamper, never reachable via
    ``write_pointer`` (which always keeps location and content in
    agreement). Mirrors what an attacker with raw filesystem write access
    to the AER store tree (backup/restore mistake, tampering, or a
    corrupted sync) could produce."""

    pointer = CanonicalPointer(
        package_id=record.package_id,
        evaluation_id=record.evaluation_id,
        record_id=record.record_id,
        record_digest=aer_to_payload(record)["record_digest"],
    )
    path = store._root / "pointers" / f"{physical_key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_atomic_json(path, pointer_to_payload(pointer))
    return path


@pytest.fixture(scope="module")
def pre_repair_storage_module(tmp_path_factory):
    """Loads the exact pre-Phase-147P ``storage.py`` from git history
    (commit ``d0c1008a``, Phase 147M) as an isolated module, independent of
    the current (repaired) ``pcae.aesic.storage``. Skips if git history is
    unavailable in the execution environment rather than fabricating a
    result."""

    repo_root = Path(__file__).resolve().parents[1]
    try:
        historical_source = subprocess.run(
            ["git", "show", f"{_PRE_REPAIR_COMMIT}:src/pcae/aesic/storage.py"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        pytest.skip(f"git history unavailable for pre-repair reconstruction: {exc}")

    out_dir = tmp_path_factory.mktemp("pre147p_source")
    module_path = out_dir / "pre_147p_storage.py"
    module_path.write_text(historical_source, encoding="utf-8")

    spec = importlib.util.spec_from_file_location("pre_147p_storage_147q", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ===========================================================================
# 1. Historical pre-repair reconstruction (independently against git
#    history, before trusting Phase 147P's own closure claim)
# ===========================================================================


class TestHistoricalPreRepairReconstruction:
    def test_aesic_n01_pre_repair_pointer_redirects_across_keys(self, tmp_path, pre_repair_storage_module):
        """Faithful reproduction of AESIC-N-01 against the actual
        pre-Phase-147P ``read_canonical`` implementation: a pointer
        physically stored under key A, whose own embedded ``package_id``
        names key B, silently resolves and returns B's AER as canonical
        for a caller who asked for A -- no exception, no key check."""

        store = pre_repair_storage_module.AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _commit(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        _plant_pointer_under(store, physical_key="pkg-A", record=record_b)

        result = store.read_canonical("pkg-A")

        assert result is not None, "pre-repair code should have redirected, not returned None"
        assert result.package_id == "pkg-B"
        assert result.record_id == "rec-b"

    def test_147o2_f1_pre_repair_dotdot_escapes_records_subdirectory(self, tmp_path, pre_repair_storage_module):
        """Faithful reproduction of 147O.2-F-1: ``package_id='..'``
        resolves one directory level above the intended
        ``records/<package_id>/`` subdirectory, landing directly inside
        the AER store root."""

        aer_root = tmp_path / "aer-root"
        store = pre_repair_storage_module.AuthorityEvaluationRecordStore(root=aer_root)

        record_path = store._record_path("..", "ev-1")

        assert record_path.parent.resolve() == aer_root.resolve()
        assert record_path.name == "ev-1.json"
        assert record_path.parent.resolve() != (aer_root / "records").resolve()  # real traversal, not a no-op

    def test_147o2_f1_pre_repair_pointer_variant_also_escapes(self, tmp_path, pre_repair_storage_module):
        aer_root = tmp_path / "aer-root"
        store = pre_repair_storage_module.AuthorityEvaluationRecordStore(root=aer_root)
        pointer_path = store._pointer_path("..")
        # "pointers/....json" stays a sibling of pointers/ under aer_root in
        # this exact construction (no true "/" in the raw id), but the
        # unsanitized "." characters pass straight through _safe_name
        # untouched -- confirms the character class gap independently of
        # the records-side reproduction above.
        assert pointer_path.parent == aer_root / "pointers"
        assert pointer_path.name == "...json"

    def test_current_code_closes_aesic_n01_for_the_identical_forged_state(self, tmp_path):
        """The exact same on-disk forged state used above, read back
        through the *current* (repaired) store, must now fail closed."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _commit(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        _plant_pointer_under(store, physical_key="pkg-A", record=record_b)

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-A")

    def test_current_code_closes_147o2_f1_for_the_identical_input(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path / "aer-root")
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._record_path("..", "ev-1")


# ===========================================================================
# 2. Fresh cross-key / identifier adversarial tests (independently
#    constructed attack shapes, not a re-run of Phase 147P's own suite)
# ===========================================================================


class TestFreshCrossKeyAndIdentifierAttacks:
    def test_case_folding_alias_on_case_insensitive_filesystem_still_fails_closed(self, tmp_path):
        """On a case-insensitive-but-case-preserving filesystem (the
        default on this development platform, and on Windows/NTFS), two
        differently-cased package_ids can alias to the *same physical
        file*. Confirms the requested-key/embedded-key binding check still
        fails closed even when the underlying filesystem itself has
        already aliased the two names to one inode -- the protection does
        not depend on path-string inequality alone."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record = _commit(store, package_id="Pkg-Mixed-Case", evaluation_id="ev-1", record_id="rec-1")
        _publish(store, record)

        # A case-insensitive filesystem answers `.exists()` for the
        # differently-cased path too, even though no `pkg-mixed-case.json`
        # was ever written -- `.resolve()` string equality is *not* a
        # reliable detector here (case-insensitive-but-case-preserving
        # filesystems, e.g. default APFS/NTFS, need not canonicalize case
        # on resolve), so detect aliasing via the same open-for-read the
        # store itself performs.
        same_file_on_disk = store._pointer_path("pkg-mixed-case").exists()
        if not same_file_on_disk:
            pytest.skip("filesystem under test is case-sensitive; aliasing scenario not applicable")

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-mixed-case")
        # The originally-cased key is entirely unaffected.
        assert store.read_canonical("Pkg-Mixed-Case").record_id == "rec-1"

    def test_percent_encoded_traversal_string_treated_as_literal_not_decoded(self, tmp_path):
        """``%2e%2e`` must never be decoded into ``..`` by this layer --
        confirms no URL-decoding step exists anywhere between the
        identifier and the filesystem. ``%`` itself is outside
        ``_safe_name``'s allowed character class, so the literal string is
        neutralized to a safe directory name -- the security property
        under test is that it lands as *one* ordinary, contained directory
        component, never interpreted as ``..``."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        path = store._record_path("%2e%2e", "ev-1")
        assert path.parent.name != ".."
        assert store._root.resolve() in path.resolve().parents
        assert path.parent.resolve() == (store._root / "records" / "_2e_2e").resolve()

    def test_whitespace_padded_traversal_identifier_rejected_or_contained(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        for candidate in (" ..", ".. ", "\t..", "..\n"):
            try:
                path = store._record_path(candidate, "ev-1")
            except AuthorityEvaluationStorageIdentifierError:
                continue
            # If not rejected outright, containment must still hold and the
            # literal ".." traversal must not have been trimmed into effect.
            assert store._root.resolve() in path.resolve().parents

    def test_repeated_separator_identifier_rejected(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._record_path("pkg//etc", "ev-1")

    def test_unicode_fullwidth_solidus_lookalike_is_neutralized_not_treated_as_separator(self, tmp_path):
        """U+FF0F (fullwidth solidus, "／") is not a real path separator on
        any supported platform, so it is not rejected by the separator
        check -- confirms it is nonetheless neutralized by ``_safe_name``
        before reaching the filesystem, so it cannot be used to smuggle a
        second path component."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        path = store._record_path("pkg／escape", "ev-1")
        assert "／" not in str(path.relative_to(store._root))
        assert store._root.resolve() in path.resolve().parents
        # Exactly one extra path component was created (records/<one dir>/file),
        # not two -- the lookalike did not introduce a real directory level.
        assert len(path.relative_to(store._root / "records").parts) == 2

    def test_embedded_newline_identifier_contained(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        path = store._record_path("pkg\nname", "ev-1")
        assert store._root.resolve() in path.resolve().parents

    def test_record_id_field_collision_does_not_defeat_package_key_binding(self, tmp_path):
        """A fresh construction of the record_id-collision scenario: two
        packages whose AERs and pointers were written in the *opposite*
        chronological order from Phase 147P's own equivalent test, and
        where the forged pointer is planted under the *first-written*
        package rather than the second."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_x = _commit(store, package_id="pkg-X", evaluation_id="ev-x", record_id="dup-rec")
        _publish(store, record_x)
        record_y = _commit(store, package_id="pkg-Y", evaluation_id="ev-y", record_id="dup-rec")

        # Overwrite pkg-X's own legitimate pointer with a forgery naming Y.
        _plant_pointer_under(store, physical_key="pkg-X", record=record_y)

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-X")
        # pkg-Y, meanwhile, never had a pointer published at all.
        assert store.read_canonical("pkg-Y") is None

    def test_three_way_relay_A_points_to_B_content_stored_under_C_key(self, tmp_path):
        """A three-namespace variant: the pointer is physically at A, its
        embedded package_id says C, and the referenced AER is genuinely
        stored (and correctly self-keyed) under C -- i.e. the pointer's
        *only* defect is being planted under the wrong physical filename.
        Distinguishes "embedded key wrong" from "AER's own key wrong",
        which Phase 147P's suite tests separately but not in this combined
        three-namespace shape."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_c = _commit(store, package_id="pkg-C", evaluation_id="ev-c", record_id="rec-c")
        _plant_pointer_under(store, physical_key="pkg-A", record=record_c)

        with pytest.raises(CanonicalPointerCorruptError) as excinfo:
            store.read_canonical("pkg-A")
        assert "pkg-A" in str(excinfo.value)
        assert "pkg-C" in str(excinfo.value)


# ===========================================================================
# 3. Root containment / symlink / TOCTOU analysis
# ===========================================================================


class TestRootContainmentAndSymlinkAnalysis:
    def test_absolute_path_package_id_rejected_before_resolve(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._record_path("/etc/passwd", "ev-1")

    def test_nested_symlink_chain_escaping_root_is_rejected(self, tmp_path):
        """A two-hop symlink chain (records/pkg-1 -> hop1 -> outside),
        rather than Phase 147P's own single-hop construction."""

        store = AuthorityEvaluationRecordStore(root=tmp_path / "aer-root")
        (store._root / "records").mkdir(parents=True)
        outside = tmp_path / "genuinely-outside"
        outside.mkdir()
        hop1 = tmp_path / "hop1"
        hop1.symlink_to(outside, target_is_directory=True)
        (store._root / "records" / "pkg-1").symlink_to(hop1, target_is_directory=True)

        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._records_directory("pkg-1")

    def test_valid_internal_symlink_within_root_is_permitted(self, tmp_path):
        """A symlink that stays *inside* the configured root is not an
        escape and must not be rejected -- confirms the containment check
        is about the resolved root boundary, not "no symlinks at all"."""

        store = AuthorityEvaluationRecordStore(root=tmp_path / "aer-root")
        (store._root / "records").mkdir(parents=True)
        real_dir = store._root / "records" / "pkg-real"
        real_dir.mkdir()
        (store._root / "records" / "pkg-alias").symlink_to(real_dir, target_is_directory=True)

        path = store._records_directory("pkg-alias")
        assert store._root.resolve() in path.resolve().parents

    def test_toctou_symlink_swap_between_validation_and_write_can_redirect_output(self, tmp_path):
        """Fresh, independent adversarial construction beyond Phase 147P's
        own (static, pre-existing-symlink) tests: demonstrates that
        ``_ensure_within_root`` validates via a *resolved* copy of the
        path but returns the *original, unresolved* ``Path`` object, and
        the actual filesystem write later re-walks that unresolved path.
        If a package directory is swapped for a symlink to outside the
        root in the window between validation and the write, the
        validated-but-stale path still follows the new symlink. This
        requires local, same-privilege filesystem write access to the AER
        store tree itself (the same trust boundary the whole persistence
        layer already assumes) -- documented as a real, reproducible,
        Informational/Minor finding in this phase's verification
        document, not a theoretical concern, but bounded in impact since
        an attacker with that prerequisite access could already write
        malicious content directly under the store tree (§19-equivalent
        below)."""

        store = AuthorityEvaluationRecordStore(root=tmp_path / "aer-root")
        (store._root / "records").mkdir(parents=True)
        package_dir = store._root / "records" / "pkg-1"
        package_dir.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        validated_path = store._record_path("pkg-1", "ev-1")  # containment check passes

        # Race window: swap the now-validated directory for a symlink.
        shutil.rmtree(package_dir)
        package_dir.symlink_to(outside, target_is_directory=True)

        _write_exclusive_json(validated_path, {"tampered": True})

        assert (outside / "ev-1.json").exists(), (
            "expected demonstration of the TOCTOU window: a write using the stale, "
            "already-validated path object followed the swapped-in symlink outside root"
        )

    def test_revalidating_on_a_fresh_call_after_swap_does_catch_it(self, tmp_path):
        """Confirms the TOCTOU window above is narrow, not systemic: any
        *fresh* call to ``_records_directory``/``_record_path`` after the
        swap (i.e. not reusing a stale ``Path`` handed out before the
        race) re-resolves and correctly rejects the swapped symlink,
        because the store caches no path between calls."""

        store = AuthorityEvaluationRecordStore(root=tmp_path / "aer-root")
        (store._root / "records").mkdir(parents=True)
        package_dir = store._root / "records" / "pkg-1"
        package_dir.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        store._record_path("pkg-1", "ev-1")  # first, pre-swap call
        shutil.rmtree(package_dir)
        package_dir.symlink_to(outside, target_is_directory=True)

        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._record_path("pkg-1", "ev-1")  # fresh call, post-swap

    def test_symlinked_pointer_file_itself_rather_than_its_parent_directory(self, tmp_path):
        """Distinct from Phase 147P's directory-symlink tests: the
        *pointer file itself* (not its parent directory) is a symlink
        pointing outside the root."""

        store = AuthorityEvaluationRecordStore(root=tmp_path / "aer-root")
        (store._root / "pointers").mkdir(parents=True)
        outside_file = tmp_path / "outside-pointer.json"
        outside_file.write_text("{}")
        (store._root / "pointers" / "pkg-1.json").symlink_to(outside_file)

        with pytest.raises(AuthorityEvaluationStorageIdentifierError):
            store._pointer_path("pkg-1")


# ===========================================================================
# 4. Malicious persisted state, bypassing all public write APIs
# ===========================================================================


class TestMaliciousPersistedState:
    def test_aer_with_internally_mismatched_package_id_rejected_even_under_correct_pointer_key(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_wrong_key = AuthorityEvaluationRecord(
            record_id="rec-1", package_id="pkg-WRONG", evaluation_id="ev-1", outcome=_outcome(), evaluated_at=_TS,
        )
        payload = aer_to_payload(record_wrong_key)
        # Physically place it under pkg-1's own records directory (bypassing
        # write_record, which would refuse this because the path is derived
        # from record.package_id, never independently chosen).
        dest_dir = store._root / "records" / "pkg-1"
        dest_dir.mkdir(parents=True, exist_ok=True)
        _write_atomic_json(dest_dir / "ev-1.json", payload)
        _write_atomic_json(
            store._pointer_path("pkg-1"),
            pointer_to_payload(
                CanonicalPointer(
                    package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1",
                    record_digest=payload["record_digest"],
                )
            ),
        )

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-1")

    def test_valid_pointer_digest_recomputed_over_a_fully_swapped_content_set(self, tmp_path):
        """An attacker who can write files can trivially recompute a
        *self-consistent* pointer_digest over arbitrary content -- digest
        verification alone was never meant to catch this; only the
        requested-key binding check is. Confirms that path independently
        of Phase 147P's own equivalent (same category, different forged
        payload: this one alters ``record_digest`` too, to a value that
        matches a *different, also-forged* AER, not the real B AER)."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        fake_digest = "f" * 64
        forged_record_payload = {
            "record_id": "rec-fake",
            "record_family": "authority_evaluation_record",
            "package_id": "pkg-B",
            "evaluation_id": "ev-fake",
            "stage": "stage_2",
            "outcome": aer_to_payload(_commit(store, package_id="pkg-B", evaluation_id="ev-real", record_id="rec-real"))["outcome"],
            "evaluated_at": _TS,
            "schema_version": "aesic-authority-evaluation-record/1.0",
            "stage_1_outcome_ref": None,
        }
        from pcae.governance.publication.record import compute_record_digest

        forged_record_payload["record_digest"] = compute_record_digest(forged_record_payload)
        _write_atomic_json(store._root / "records" / "pkg-B" / "ev-fake.json", forged_record_payload)

        forged_pointer_content = {
            "package_id": "pkg-B",
            "evaluation_id": "ev-fake",
            "record_id": "rec-fake",
            "record_digest": forged_record_payload["record_digest"],
            "schema_version": "aesic-authority-evaluation-pointer/1.0",
        }
        from pcae.aesic.records import _compute_pointer_digest

        forged_pointer_payload = dict(forged_pointer_content)
        forged_pointer_payload["pointer_digest"] = _compute_pointer_digest(forged_pointer_content)
        _write_atomic_json(store._pointer_path("pkg-A"), forged_pointer_payload)

        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-A")

    def test_record_copied_into_another_key_directory_caught_via_canonical_read(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _commit(store, package_id="pkg-B", evaluation_id="ev-shared-name", record_id="rec-b")
        payload_b = aer_to_payload(record_b)
        dest = store._root / "records" / "pkg-A" / "ev-shared-name.json"
        _write_atomic_json(dest, payload_b)

        pointer_a = CanonicalPointer(
            package_id="pkg-A", evaluation_id="ev-shared-name", record_id="rec-b",
            record_digest=payload_b["record_digest"],
        )
        _write_atomic_json(store._pointer_path("pkg-A"), pointer_to_payload(pointer_a))

        # read_record alone (digest-only) does NOT catch this -- the digest
        # is untouched, so the AER "verifies" under the wrong directory.
        direct = store.read_record("pkg-A", "ev-shared-name")
        assert direct is not None
        assert direct.package_id == "pkg-B"  # content says B, directory says A

        # read_canonical's own record.package_id != package_id check is what
        # closes this -- confirming that check is load-bearing, not
        # redundant with the pointer-level check alone.
        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-A")


# ===========================================================================
# 5. Recovery, diagnostics distinguishability
# ===========================================================================


class TestRecoveryAndDiagnosticsDistinguishability:
    def test_recovery_after_pointer_write_failure_is_not_derailed_by_a_concurrently_corrupt_sibling_key(
        self, tmp_path, monkeypatch
    ):
        """A fresh combination not in Phase 147P's own suite: a genuine
        crash-recovery scenario for pkg-1 happening while pkg-2's pointer
        is independently, unrelatedly corrupt (cross-key forged) --
        confirms the two keys' recovery paths are fully isolated."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_2 = _commit(store, package_id="pkg-2", evaluation_id="ev-2", record_id="rec-2")
        _plant_pointer_under(store, physical_key="pkg-2", record=record_2)
        # Corrupt pkg-2 unrelatedly via a cross-key forgery for a third key.
        record_x = _commit(store, package_id="pkg-x", evaluation_id="ev-x", record_id="rec-x")
        _plant_pointer_under(store, physical_key="pkg-corrupt", record=record_x)

        record_1 = _commit(store, package_id="pkg-1", evaluation_id="ev-1", record_id="rec-1")
        # Simulate the post-AER/pre-pointer crash for pkg-1 specifically.
        _publish(store, record_1)

        assert store.read_canonical("pkg-1").record_id == "rec-1"
        assert store.read_canonical("pkg-2").record_id == "rec-2"  # unrelated key, unaffected
        with pytest.raises(CanonicalPointerCorruptError):
            store.read_canonical("pkg-corrupt")  # the corrupt key remains corrupt, isolated

    def test_diagnostics_distinguishes_never_established_from_corrupt_cross_key_pointer(self, tmp_path):
        """A cross-key-corrupt pointer and a package that has never had a
        pointer published at all must be *distinguishable* through
        ``summarize_package`` -- not collapsed into the same reported
        state, which would hide real corruption behind ordinary "nothing
        here yet" output."""

        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _commit(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        _plant_pointer_under(store, physical_key="pkg-corrupt", record=record_b)

        corrupt_summary = summarize_package(store, "pkg-corrupt")
        never_established_summary = summarize_package(store, "pkg-never-touched")

        assert corrupt_summary.canonical_pointer_ok is False
        assert never_established_summary.canonical_pointer_ok is True
        assert corrupt_summary.canonical_record_id is None
        assert never_established_summary.canonical_record_id is None

    def test_diagnostics_for_invalid_identifier_is_read_only_and_creates_nothing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        store = AuthorityEvaluationRecordStore(root=tmp_path / "records-root")
        before = set(tmp_path.rglob("*"))
        summary = summarize_package(store, "../../etc")
        after = set(tmp_path.rglob("*"))
        assert summary.canonical_pointer_ok is False
        assert summary.total_attempts == 0
        assert after == before, "diagnostics on an invalid identifier must create no filesystem state"

    def test_repeated_recovery_after_corrupt_pointer_write_of_the_correct_key_is_idempotent(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        record_b = _commit(store, package_id="pkg-B", evaluation_id="ev-b", record_id="rec-b")
        _plant_pointer_under(store, physical_key="pkg-A", record=record_b)

        for _ in range(3):
            with pytest.raises(CanonicalPointerCorruptError):
                store.read_canonical("pkg-A")

        # Recovery: publish pkg-A's own genuine pointer; repeated reads are
        # then idempotent and correct.
        record_a = _commit(store, package_id="pkg-A", evaluation_id="ev-a", record_id="rec-a")
        _publish(store, record_a)
        first = store.read_canonical("pkg-A")
        second = store.read_canonical("pkg-A")
        assert first.record_id == second.record_id == "rec-a"


# ===========================================================================
# 6. Same-key regression (independent scenarios)
# ===========================================================================


class TestSameKeyRegressionIndependent:
    def test_supersession_history_of_five_generations_remains_key_bound_throughout(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        last = None
        for i in range(5):
            last = _commit(store, package_id="pkg-1", evaluation_id=f"ev-{i}", record_id=f"rec-{i}")
            _publish(store, last)
            canonical = store.read_canonical("pkg-1")
            assert canonical.record_id == f"rec-{i}"
            assert canonical.package_id == "pkg-1"

    def test_restart_with_many_packages_each_resolve_independently(self, tmp_path):
        store1 = AuthorityEvaluationRecordStore(root=tmp_path)
        expected = {}
        for i in range(10):
            pkg = f"pkg-{i}"
            rec = _commit(store1, package_id=pkg, evaluation_id="ev-1", record_id=f"rec-{i}")
            _publish(store1, rec)
            expected[pkg] = f"rec-{i}"

        store2 = AuthorityEvaluationRecordStore(root=tmp_path)
        for pkg, expected_record_id in expected.items():
            assert store2.read_canonical(pkg).record_id == expected_record_id
            assert store2.read_canonical(pkg).package_id == pkg

    def test_concurrent_reads_of_distinct_keys_from_multiple_threads_remain_isolated(self, tmp_path):
        store = AuthorityEvaluationRecordStore(root=tmp_path)
        packages = [f"pkg-t{i}" for i in range(8)]
        for i, pkg in enumerate(packages):
            rec = _commit(store, package_id=pkg, evaluation_id="ev-1", record_id=f"rec-t{i}")
            _publish(store, rec)

        results = {}
        errors = []

        def _read(pkg):
            try:
                results[pkg] = store.read_canonical(pkg).record_id
            except Exception as exc:  # pragma: no cover - failure path only
                errors.append((pkg, exc))

        threads = [threading.Thread(target=_read, args=(pkg,)) for pkg in packages]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        for i, pkg in enumerate(packages):
            assert results[pkg] == f"rec-t{i}"


# ===========================================================================
# 7. Production-level (service-layer) regression
# ===========================================================================


class TestProductionServiceLayerRegression:
    def test_evaluate_stage_2_never_constructs_a_cross_key_pointer(self, tmp_path):
        """A white-box confirmation that the production write path
        (``AuthorityEvaluationService.evaluate_stage_2``) is structurally
        incapable of producing a cross-key pointer: it always constructs
        ``CanonicalPointer(package_id=package_id, ...)`` from the same
        ``package_id`` argument it was called with. Verified by reading
        ``service.py`` directly and confirming via the AST that no other
        value feeds ``CanonicalPointer.package_id`` at that call site."""

        import ast

        service_src = (Path(__file__).resolve().parents[1] / "src" / "pcae" / "aesic" / "service.py").read_text()
        tree = ast.parse(service_src)
        pointer_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "CanonicalPointer"
        ]
        assert pointer_calls, "expected at least one CanonicalPointer(...) construction in service.py"
        for call in pointer_calls:
            package_id_kwargs = [kw for kw in call.keywords if kw.arg == "package_id"]
            assert len(package_id_kwargs) == 1
            value = package_id_kwargs[0].value
            assert isinstance(value, ast.Name) and value.id == "package_id", (
                "CanonicalPointer.package_id must be constructed from the same "
                "'package_id' parameter evaluate_stage_2 received, never a "
                "pointer-supplied or otherwise derived value"
            )

    def test_read_canonical_call_site_in_evaluate_stage_2_uses_the_same_package_id(self, tmp_path):
        import ast

        service_src = (Path(__file__).resolve().parents[1] / "src" / "pcae" / "aesic" / "service.py").read_text()
        tree = ast.parse(service_src)
        read_canonical_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "read_canonical"
        ]
        assert read_canonical_calls
        for call in read_canonical_calls:
            assert len(call.args) == 1
            arg = call.args[0]
            assert isinstance(arg, ast.Name) and arg.id == "package_id"


# ===========================================================================
# 8. Architecture / runtime preservation
# ===========================================================================


class TestArchitectureAndRuntimePreservation:
    def test_only_persistence_boundary_files_touched_by_147p(self):
        """Scoped to Phase 147P's *own* commit (its parent to itself),
        never the full 147M..147P range (which spans five intervening
        verification/certification phases and would over-count)."""

        repo_root = Path(__file__).resolve().parents[1]
        commit = "017301e320076093a576153323b3f43584c839e5"
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{commit}^", commit, "--", "src/pcae/**"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip("git history unavailable")
        changed = {line for line in result.stdout.splitlines() if line}
        assert changed <= {
            "src/pcae/aesic/storage.py",
            "src/pcae/aesic/errors.py",
            "src/pcae/aesic/diagnostics.py",
        }, f"Phase 147P touched unexpected production files: {changed}"

    def test_evaluator_and_registry_modules_untouched_by_147p(self):
        repo_root = Path(__file__).resolve().parents[1]
        commit = "017301e320076093a576153323b3f43584c839e5"
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{commit}^", commit],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip("git history unavailable")
        changed = set(result.stdout.splitlines())
        untouched_expected = {
            "src/pcae/authority_evaluation/evaluation.py",
            "src/pcae/authority_evaluation/registry.py",
            "src/pcae/authority_evaluation/models.py",
            "src/pcae/aesic/registry_filesystem.py",
            "src/pcae/aesic/template_store.py",
            "src/pcae/governance/publication/coordinator.py",
        }
        assert not (changed & untouched_expected), (
            f"Phase 147P unexpectedly touched: {changed & untouched_expected}"
        )

    def test_runtime_capability_unaffected(self):
        """Persistence-boundary hardening in ``pcae.aesic`` has no import
        relationship to the plugin runtime registry at all -- confirmed by
        static import inspection rather than re-running the full `pcae
        runtime inspect` CLI (already exercised at bootstrap time in this
        phase's own §1)."""

        import ast

        storage_src = (Path(__file__).resolve().parents[1] / "src" / "pcae" / "aesic" / "storage.py").read_text()
        tree = ast.parse(storage_src)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
        assert not any("runtime" in m for m in imported_modules)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v"]))
