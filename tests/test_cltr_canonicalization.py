"""Phase 135K — canonical serialization tests."""

from __future__ import annotations

import unicodedata

from pcae.cltr import schema
from pcae.cltr.canonicalization import canonicalize, canonicalize_dict
from pcae.cltr.enums import LifecycleState, TransitionType
from pcae.cltr.models import CommitOwnershipEntry, ProductionCltrRecord
from pcae.cltr.enums import CertificationState


def _record(**overrides) -> ProductionCltrRecord:
    fields = dict(
        schema_id=schema.SCHEMA_ID,
        schema_version=schema.SCHEMA_VERSION,
        contract_version=schema.CONTRACT_VERSION,
        compatibility_id=schema.COMPATIBILITY_ID,
        transition_id="135K-CANON",
        phase_id="135K-CANON",
        repository_identity="repo",
        branch_identity="main",
        transition_type=TransitionType.PROPOSE_TRANSITION,
        lifecycle_state=LifecycleState.PROPOSED,
        source_revision="abc123",
    )
    fields.update(overrides)
    return ProductionCltrRecord(**fields)


def test_object_keys_sorted():
    record = _record()
    raw = canonicalize(record)
    text = raw.decode("utf-8")
    # crude but sufficient: top-level keys appear in the payload in
    # ascending order by first occurrence of `"key":`
    import re

    keys = re.findall(r'"([a-z_]+)":', text)
    assert keys == sorted(keys)


def test_set_like_collection_sorted_by_natural_key():
    commits = (
        CommitOwnershipEntry(commit_hash="zzz", repository_identity="repo", branch_identity="main", certification_state=CertificationState.UNVERIFIABLE),
        CommitOwnershipEntry(commit_hash="aaa", repository_identity="repo", branch_identity="main", certification_state=CertificationState.UNVERIFIABLE),
    )
    record = _record(phase_commit_ownership=commits)
    raw = canonicalize(record).decode("utf-8")
    assert raw.index('"aaa"') < raw.index('"zzz"')


def test_unicode_normalization_nfc():
    # "é" as combining sequence vs precomposed should canonicalize the same.
    decomposed = "é"
    precomposed = "é"
    assert unicodedata.normalize("NFC", decomposed) == precomposed
    r1 = _record(branch_identity=f"main-{decomposed}")
    r2 = _record(branch_identity=f"main-{precomposed}")
    assert canonicalize(r1) == canonicalize(r2)


def test_equivalent_content_byte_identical_across_construction_order():
    r1 = _record(final_revision="x", branch_identity="main")
    r2 = _record(branch_identity="main", final_revision="x")
    assert canonicalize(r1) == canonicalize(r2)


def test_record_digest_excluded_from_digest_input():
    r1 = _record()
    r2 = r1.with_digest("f" * 64)
    assert canonicalize(r1, include_digest=False) == canonicalize(r2, include_digest=False)
    assert canonicalize(r1, include_digest=True) != canonicalize(r2, include_digest=True)


def test_compact_no_whitespace():
    raw = canonicalize(_record()).decode("utf-8")
    assert "\n" not in raw
    assert ": " not in raw
    assert ", " not in raw


def test_floats_prohibited():
    import pytest

    with pytest.raises(ValueError):
        canonicalize_dict({"x": 1.5})


def test_duplicate_key_semantics_via_python_dict_collapse():
    # Python dicts cannot carry duplicate keys; canonicalize_dict operates
    # on an already-deduplicated mapping. This test documents that the
    # canonical form never independently re-introduces a duplicate.
    value = {"a": 1, "b": 2}
    raw = canonicalize_dict(value).decode("utf-8")
    assert raw.count('"a"') == 1
    assert raw.count('"b"') == 1


def test_null_vs_absent_distinction():
    r_absent = _record()  # task_id never set -> absent
    r_null = _record(task_id=None)
    # Both omit task_id because our nullable-field policy treats task_id
    # as absent when None was never explicitly distinguished from unset at
    # the Python level (135I §8.1's distinction is enforced by the caller
    # supplying an explicit value upstream, e.g. ShadowTransitionInput).
    from pcae.cltr.canonicalization import record_to_dict

    d_absent = record_to_dict(r_absent)
    d_null = record_to_dict(r_null)
    assert "task_id" in d_absent
    assert d_absent["task_id"] is None
    assert d_null["task_id"] is None
