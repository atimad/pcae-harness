"""Phase 136V: Compatibility State / Quarantine Record Schema
Implementation (Implementation Group 11 -- the final of the 11 frozen
executable-schema implementation groups).

Focused tests for the packaged ``src/pcae/schema_resources/cltr_cutover/records``
Group 11 record schemas -- ``compatibility_state.schema.json`` and
``quarantine_record.schema.json`` -- manifest entries, registry integration,
local conditional validation, family-reference disclosure, unknown-field
strictness, authority-role restriction, and the exact scope guard proving no
Group 12+ record schema, view, typed model, semantic validator, or authority
resolver/state/pointer was introduced.

Per the frozen contract's own Sec.46 grouping table, Group 11 is exactly
{compatibility_state (depends only on Group 1), quarantine_record (depends
on Groups 2-8)} -- the final row of the table; there is no Group 12. This
module derives Group 11 independently from the frozen contract text (Sec.4,
Sec.7, Sec.9, Sec.14, Sec.16, Sec.30, Sec.34, Sec.46) rather than inferring
it from prior phases' prose (see docs/PHASE_136_COMPATIBILITY_STATE_
QUARANTINE_RECORD_SCHEMA_IMPLEMENTATION.md for the full derivation and
discrepancy disclosures NON-BLOCKING-136V-1 through -6 and DEFERRED-136V-1).

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state,
compatibility resolution, quarantine mutation, artifact movement, or
production lifecycle behavior. Legacy lifecycle remains the sole production
authority; CLTR remains derivative.
"""
from __future__ import annotations

import copy
import json
import socket
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
    build_offline_registry,
    load_and_verify_manifest,
    validate_record_shape,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/manifest.schema.json"
BASE_ID = "https://pcae.local/schemas/cltr_cutover/"

SHARED_FILES = (
    "shared/digest.schema.json",
    "shared/enums.schema.json",
    "shared/envelope.schema.json",
    "shared/failures.schema.json",
    "shared/identity.schema.json",
    "shared/limitations.schema.json",
    "shared/references.schema.json",
)

GROUP2_RECORD_FILES = (
    "records/authority_epoch.schema.json",
    "records/authority_state.schema.json",
)
GROUP3_RECORD_FILES = (
    "records/cutover_request.schema.json",
    "records/readiness_package.schema.json",
)
GROUP4_RECORD_FILES = (
    "records/certification.schema.json",
    "records/cutover_candidate.schema.json",
    "records/human_authorization.schema.json",
)
GROUP5_RECORD_FILES = (
    "records/publication_attempt.schema.json",
    "records/publication_evidence.schema.json",
)
GROUP8_RECORD_FILES = (
    "records/concurrency_conflict.schema.json",
    "records/recovery_journal_entry.schema.json",
)
GROUP10_RECORD_FILES = (
    "records/marker_authority_binding.schema.json",
    "records/notification_authority_binding.schema.json",
    "records/receipt_authority_binding.schema.json",
)
GROUP11_RECORD_FILES = (
    "records/compatibility_state.schema.json",
    "records/quarantine_record.schema.json",
)

# Group 11 is the final row of Sec.46's table -- there is no Group 12.
LATER_GROUP_RECORD_FILES = ()

COMPAT_ID = BASE_ID + "records/compatibility_state.schema.json"
QUARANTINE_ID = BASE_ID + "records/quarantine_record.schema.json"
AUTHORITY_STATE_ID = BASE_ID + "records/authority_state.schema.json"
PUBLICATION_ATTEMPT_ID = BASE_ID + "records/publication_attempt.schema.json"


# ---------------------------------------------------------------------------
# Fixtures (inline Python builders, matching this package's established
# convention -- no prior implementation group under schemas/cltr_cutover
# uses separate on-disk JSON fixture files; every one of 136H-136U's focused
# modules builds fixtures as Python dict factories in the module itself).
# ---------------------------------------------------------------------------


def _ref(record_id, digest, family, schema_id=None, schema_version="1.0"):
    r = {"record_id": record_id, "record_digest": digest, "record_family": family}
    if schema_id is not None:
        r["schema_id"] = schema_id
        r["schema_version"] = schema_version
    return r


def _valid_compat(**overrides) -> dict:
    record = {
        "schema_id": COMPAT_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "compatibility_state",
        "record_id": "compatstate-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "component": "legacy_lifecycle_reader",
        "role": "compatibility",
        "allowed_reads": ["legacy/state.json"],
        "forbidden_authority_use": True,
        "fallback_disabled": False,
        "mode": "legacy_adapter",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "evidence",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_quarantine(**overrides) -> dict:
    record = {
        "schema_id": QUARANTINE_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "quarantine_record",
        "record_id": "quarantine-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "object_type": "authority_state",
        "object_reference": _ref("authstate-0000001", "b" * 64, "authority_state", AUTHORITY_STATE_ID),
        "reason_code": "authority_ambiguous",
        "state": "quarantined",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "evidence",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


@pytest.fixture(scope="module")
def registry():
    with cltr_cutover_root() as root:
        yield build_offline_registry(root)


def _validate(record, schema_id, registry):
    return validate_record_shape(record, schema_id=schema_id, registry=registry)


def _copy_tree(source: Path, dest: Path) -> None:
    import shutil

    for item in source.rglob("*"):
        if item.is_file():
            target = dest / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


# ---------------------------------------------------------------------------
# 1. Package integrity / exact scope guard
# ---------------------------------------------------------------------------


def test_136v_exact_group11_inventory_is_compatibility_state_quarantine_record():
    assert GROUP11_RECORD_FILES == (
        "records/compatibility_state.schema.json",
        "records/quarantine_record.schema.json",
    )


def test_136v_exact_group1_through_group11_file_inventory():
    with cltr_cutover_root() as root:
        schema_files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.schema.json"))
    assert schema_files == sorted(
        ("manifest.schema.json",)
        + SHARED_FILES
        + GROUP2_RECORD_FILES
        + GROUP3_RECORD_FILES
        + GROUP4_RECORD_FILES
        + GROUP5_RECORD_FILES
        + GROUP8_RECORD_FILES
        + GROUP10_RECORD_FILES
        + GROUP11_RECORD_FILES
    )


def test_136v_no_bindings_or_views_directory_exists():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136v_no_group12_filename_tracked_anywhere():
    # Group 11 is the final row of Sec.46's table -- there is no Group 12.
    # reconciliation_result/historical_authority_reference remain
    # permanently forbidden: Group 9 (Sec.46) assigns neither a schema
    # file, ever.
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_stems = (
        "reconciliation_result.schema",
        "historical_authority_reference.schema",
    )
    hits = [
        path
        for path in tracked
        if any(stem in path for stem in forbidden_stems) and "docs/" not in path and path.endswith(".json")
    ]
    assert hits == []


def test_136v_no_typed_python_record_model_introduced():
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_names = (
        "compatibility_state.py",
        "quarantine_record.py",
        "authority_model.py",
        "typed_authority.py",
    )
    hits = [path for path in tracked if Path(path).name in forbidden_names]
    assert hits == []


def test_136v_no_cltr_authority_namespace_directory_exists():
    assert not (REPO_ROOT / ".pcae" / "cltr-authority").exists()


@pytest.mark.parametrize("relative_path", GROUP11_RECORD_FILES)
def test_136v_every_resource_declares_draft_2020_12(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("relative_path", GROUP11_RECORD_FILES)
def test_136v_every_resource_id_matches_frozen_namespace(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["$id"] == BASE_ID + relative_path


def test_136v_registry_loads_exactly_twenty_four_resources_with_unique_ids(registry):
    assert len(registry.schema_ids) == 24
    assert len(set(registry.schema_ids)) == 24
    assert COMPAT_ID in registry.schema_ids
    assert QUARANTINE_ID in registry.schema_ids


@pytest.mark.parametrize("relative_path", GROUP11_RECORD_FILES)
def test_136v_group11_schema_is_tier2_extensions_only(relative_path):
    with cltr_cutover_root() as root:
        document = json.loads((root / relative_path).read_bytes())
    assert document["additionalProperties"] is False
    assert "_extensions" in document["properties"]
    assert document["properties"]["_extensions"]["additionalProperties"] == {"type": "string"}


# ---------------------------------------------------------------------------
# 2. Manifest
# ---------------------------------------------------------------------------


def test_136v_manifest_verifies_cleanly():
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        manifest = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    assert len(manifest.entries) == 23
    assert {e.file_path for e in manifest.entries} == (
        set(SHARED_FILES)
        | set(GROUP2_RECORD_FILES)
        | set(GROUP3_RECORD_FILES)
        | set(GROUP4_RECORD_FILES)
        | set(GROUP5_RECORD_FILES)
        | set(GROUP8_RECORD_FILES)
        | set(GROUP10_RECORD_FILES)
        | set(GROUP11_RECORD_FILES)
    )


def test_136v_manifest_new_entries_are_group_eleven():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    for path, family, schema_id in (
        ("records/compatibility_state.schema.json", "compatibility_state", COMPAT_ID),
        ("records/quarantine_record.schema.json", "quarantine_record", QUARANTINE_ID),
    ):
        entry = by_path[path]
        assert entry["implementation_group"] == 11
        assert entry["family"] == family
        assert entry["status"] == "frozen"
        assert entry["schema_id"] == schema_id


def test_136v_manifest_group1_through_group10_entries_unchanged():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    shared_entries = [e for e in manifest["entries"] if e["family"] == "shared"]
    assert len(shared_entries) == 7
    assert all(e["implementation_group"] == 1 for e in shared_entries)
    group10_entries = [
        e for e in manifest["entries"]
        if e["family"] in ("notification_authority_binding", "marker_authority_binding", "receipt_authority_binding")
    ]
    assert len(group10_entries) == 3
    assert all(e["implementation_group"] == 10 for e in group10_entries)


def test_136v_manifest_entries_in_deterministic_sorted_order():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    paths = [e["file_path"] for e in manifest["entries"]]
    assert paths == sorted(paths)


def test_136v_manifest_entry_count_matches_group1_through_11_exactly():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    assert len(manifest["entries"]) == 23


def test_136v_manifest_no_group9_entry_and_no_group12_entry():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    groups = {e["implementation_group"] for e in manifest["entries"]}
    assert 9 not in groups
    assert 12 not in groups
    assert max(groups) == 11


def test_136v_compatibility_state_declares_group1_dependencies_only():
    # Sec.46: compatibility_state.schema.json "depends only on group 1".
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    entry = next(e for e in manifest["entries"] if e["family"] == "compatibility_state")
    group1_ids = {
        e["schema_id"] for e in manifest["entries"] if e["implementation_group"] == 1
    }
    assert set(entry["dependencies"]) <= group1_ids


def test_136v_quarantine_record_declares_no_direct_ref_to_group2through8_files():
    # Sec.46: quarantine_record.schema.json "depends on 2-8" is a
    # conceptual/manifest-ordering prerequisite, not a direct $ref
    # dependency -- quarantine_record's object_reference field is generic
    # (shared/references.schema.json#/$defs/record_reference), never a
    # $ref into any Group 2-8 records/*.schema.json file itself (matching
    # every other family's precedent: manifest "dependencies" always list
    # shared/*.schema.json files only, never other records/*.schema.json
    # files).
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    entry = next(e for e in manifest["entries"] if e["family"] == "quarantine_record")
    assert all("/shared/" in dep for dep in entry["dependencies"])


def test_136v_manifest_detects_content_tamper_on_new_record(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    tampered = tmp_path / "records" / "compatibility_state.schema.json"
    document = json.loads(tampered.read_bytes())
    document["title"] = "tampered"
    tampered.write_text(json.dumps(document), encoding="utf-8")

    reg = build_offline_registry(tmp_path)
    with pytest.raises(ManifestIntegrityError, match="does not match"):
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136v_manifest_detects_missing_group11_sibling_file(tmp_path):
    # Group atomicity: partial Group 11 manifest delivery fails closed.
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    (tmp_path / "records" / "quarantine_record.schema.json").unlink()

    with pytest.raises(Exception):
        reg = build_offline_registry(tmp_path)
        load_and_verify_manifest(
            tmp_path / "manifest.json",
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


# ---------------------------------------------------------------------------
# 3. Fixture validity
# ---------------------------------------------------------------------------


def test_136v_compat_valid_minimal(registry):
    assert _validate(_valid_compat(), COMPAT_ID, registry).status is OutcomeStatus.VALID


def test_136v_quarantine_valid_minimal(registry):
    assert _validate(_valid_quarantine(), QUARANTINE_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "mode",
    ["legacy_authoritative", "legacy_adapter", "legacy_read_only"],
)
def test_136v_compat_valid_every_non_restricted_mode(mode, registry):
    record = _valid_compat(mode=mode)
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize("mode", ["legacy_historical", "legacy_disabled"])
def test_136v_compat_valid_restricted_mode_with_historical_role(mode, registry):
    record = _valid_compat(
        mode=mode,
        authority_disclosure={
            "authority_role": "historical",
            "is_authoritative": False,
            "disclosure_text": "x",
        },
    )
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.VALID


def test_136v_compat_legacy_retired_with_retirement_state_and_compatible_role_valid(registry):
    record = _valid_compat(
        mode="legacy_retired",
        retirement_state={},
        authority_disclosure={
            "authority_role": "compatibility",
            "is_authoritative": False,
            "disclosure_text": "x",
        },
    )
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize("state", ["quarantined", "under_review", "released", "permanently_retired"])
def test_136v_quarantine_valid_every_state(state, registry):
    record = _valid_quarantine(state=state)
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "object_type",
    ["generation", "publication_attempt", "authority_state", "compatibility_state"],
)
def test_136v_quarantine_valid_every_object_type(object_type, registry):
    record = _valid_quarantine(object_type=object_type)
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 4. Local conditional validation
# ---------------------------------------------------------------------------


def test_136v_compat_legacy_retired_without_retirement_state_rejected(registry):
    record = _valid_compat(mode="legacy_retired")
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.INVALID


def test_136v_compat_non_retired_with_stray_retirement_state_rejected(registry):
    record = _valid_compat(mode="legacy_adapter", retirement_state={})
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize("mode", ["legacy_historical", "legacy_disabled", "legacy_retired"])
@pytest.mark.parametrize("forbidden_role", ["authoritative", "derivative", "operational", "evidence", "quarantined"])
def test_136v_compat_restricted_mode_forbids_non_historical_compatibility_role(mode, forbidden_role, registry):
    overrides = {
        "mode": mode,
        "authority_disclosure": {
            "authority_role": forbidden_role,
            "is_authoritative": False,
            "disclosure_text": "x",
        },
    }
    if mode == "legacy_retired":
        overrides["retirement_state"] = {}
    record = _valid_compat(**overrides)
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.INVALID


def test_136v_compat_authoritative_role_forbidden_unconditionally(registry):
    record = _valid_compat(
        authority_disclosure={"authority_role": "authoritative", "is_authoritative": False, "disclosure_text": "x"}
    )
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.INVALID


def test_136v_compat_role_field_restricted_to_two_values(registry):
    record = _valid_compat(role="authoritative")
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.INVALID


def test_136v_quarantine_authoritative_role_forbidden_unconditionally(registry):
    record = _valid_quarantine(
        authority_disclosure={"authority_role": "authoritative", "is_authoritative": False, "disclosure_text": "x"}
    )
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.INVALID


def test_136v_quarantine_missing_reason_code_rejected(registry):
    record = _valid_quarantine()
    del record["reason_code"]
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.INVALID


def test_136v_quarantine_reason_code_field_name_is_reason_code_not_quarantine_reason(registry):
    # NON-BLOCKING-136V-5: the field is named reason_code (Sec.30's own
    # field table and prose), not quarantine_reason (Sec.16/CSCH-EXEC-
    # REQ-041's label). Confirm the schema does not silently accept a
    # 'quarantine_reason' key as a substitute, and confirm 'reason_code'
    # is the only recognized name (unknown field, Tier 2 strictness).
    record = _valid_quarantine()
    del record["reason_code"]
    record["quarantine_reason"] = "authority_ambiguous"
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. Enum strictness
# ---------------------------------------------------------------------------


def test_136v_compat_unknown_mode_rejected(registry):
    record = _valid_compat(mode="bogus_mode")
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.INVALID


def test_136v_quarantine_unknown_object_type_rejected(registry):
    record = _valid_quarantine(object_type="bogus")
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.INVALID


def test_136v_quarantine_unknown_state_rejected(registry):
    record = _valid_quarantine(state="bogus")
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.INVALID


def test_136v_quarantine_unknown_reason_code_rejected(registry):
    record = _valid_quarantine(reason_code="bogus_reason")
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 6. Strictness / unknown fields / _extensions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_unknown_top_level_field_rejected(valid_fn, schema_id, registry):
    record = valid_fn(bogus_field="x")
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_extensions_key_valid_tier2(valid_fn, schema_id, registry):
    record = valid_fn(_extensions={"note": "annotation"})
    assert _validate(record, schema_id, registry).status is OutcomeStatus.VALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_extensions_non_string_value_rejected(valid_fn, schema_id, registry):
    record = valid_fn(_extensions={"note": 123})
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_extensions_null_rejected(valid_fn, schema_id, registry):
    record = valid_fn(_extensions=None)
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_extensions_scalar_rejected(valid_fn, schema_id, registry):
    record = valid_fn(_extensions="not-an-object")
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_extensions_cannot_smuggle_alternate_authority_role(valid_fn, schema_id, registry):
    # _extensions carrying an authoritative-looking claim must not
    # override canonical meaning (Sec.14: sole extension boundary,
    # canonical meaning never overridden).
    record = valid_fn(_extensions={"authority_role": "authoritative"})
    result = _validate(record, schema_id, registry)
    assert result.status is OutcomeStatus.VALID
    # The canonical authority_disclosure.authority_role is unaffected.
    assert record["authority_disclosure"]["authority_role"] != "authoritative"


def test_136v_compat_extensions_cannot_smuggle_alternate_compatibility_classification(registry):
    record = _valid_compat(_extensions={"mode": "legacy_retired"})
    result = _validate(record, COMPAT_ID, registry)
    assert result.status is OutcomeStatus.VALID
    assert record["mode"] != "legacy_retired"


def test_136v_quarantine_extensions_cannot_smuggle_alternate_quarantine_outcome(registry):
    record = _valid_quarantine(_extensions={"state": "released"})
    result = _validate(record, QUARANTINE_ID, registry)
    assert result.status is OutcomeStatus.VALID
    assert record["state"] != "released"


@pytest.mark.parametrize(
    "valid_fn,schema_id,required_field",
    [
        (_valid_compat, COMPAT_ID, "component"),
        (_valid_compat, COMPAT_ID, "role"),
        (_valid_compat, COMPAT_ID, "allowed_reads"),
        (_valid_compat, COMPAT_ID, "forbidden_authority_use"),
        (_valid_compat, COMPAT_ID, "fallback_disabled"),
        (_valid_compat, COMPAT_ID, "mode"),
        (_valid_compat, COMPAT_ID, "migration_epoch"),
        (_valid_compat, COMPAT_ID, "limitations"),
        (_valid_compat, COMPAT_ID, "authority_disclosure"),
        (_valid_quarantine, QUARANTINE_ID, "object_type"),
        (_valid_quarantine, QUARANTINE_ID, "object_reference"),
        (_valid_quarantine, QUARANTINE_ID, "reason_code"),
        (_valid_quarantine, QUARANTINE_ID, "state"),
        (_valid_quarantine, QUARANTINE_ID, "migration_epoch"),
        (_valid_quarantine, QUARANTINE_ID, "limitations"),
        (_valid_quarantine, QUARANTINE_ID, "authority_disclosure"),
    ],
)
def test_136v_missing_required_field_rejected(valid_fn, schema_id, required_field, registry):
    record = valid_fn()
    del record[required_field]
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_malformed_digest_rejected(valid_fn, schema_id, registry):
    record = valid_fn(record_digest="not-a-digest")
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_malformed_timestamp_rejected(valid_fn, schema_id, registry):
    record = valid_fn(created_at="not-a-timestamp")
    assert _validate(record, schema_id, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_empty_limitations_array_valid(valid_fn, schema_id, registry):
    record = valid_fn(limitations=[])
    assert _validate(record, schema_id, registry).status is OutcomeStatus.VALID


def test_136v_compat_forbidden_authority_use_false_rejected(registry):
    record = _valid_compat(forbidden_authority_use=False)
    assert _validate(record, COMPAT_ID, registry).status is OutcomeStatus.INVALID


def test_136v_no_field_named_password_token_or_secret():
    for path in GROUP11_RECORD_FILES:
        with cltr_cutover_root() as root:
            text = (root / path).read_text(encoding="utf-8")
        document = json.loads(text)
        props = set(document.get("properties", {}).keys())
        for defn in document.get("$defs", {}).values():
            if isinstance(defn, dict):
                props |= set(defn.get("properties", {}).keys())
        forbidden = {"password", "token", "secret", "private_key", "credential"}
        assert props.isdisjoint(forbidden), (path, props & forbidden)


# ---------------------------------------------------------------------------
# 7. Family-specific reference / wrong-family substitution
# ---------------------------------------------------------------------------


def test_136v_quarantine_object_reference_accepts_any_declared_record_family(registry):
    # NON-BLOCKING-136V-6: object_reference is a generic record_reference
    # (no per-object_type family restriction is contract-defined, and
    # 'generation' has no record_family enum member to restrict to in the
    # first place). Confirm every declared record_family value is accepted
    # structurally regardless of object_type.
    record = _valid_quarantine(
        object_type="publication_attempt",
        object_reference=_ref("pubattmp-0000001", "c" * 64, "publication_attempt", PUBLICATION_ATTEMPT_ID),
    )
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.VALID


def test_136v_quarantine_object_reference_malformed_family_rejected(registry):
    record = _valid_quarantine(object_reference=_ref("authstate-0000001", "b" * 64, "not_a_real_family"))
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.INVALID


def test_136v_quarantine_object_reference_malformed_id_rejected(registry):
    record = _valid_quarantine(
        object_reference=_ref("../../etc/passwd", "b" * 64, "authority_state")
    )
    assert _validate(record, QUARANTINE_ID, registry).status is OutcomeStatus.INVALID


def test_136v_compat_references_only_group1_shared_defs():
    # Sibling independence + Sec.46 prerequisite check: compatibility_state
    # does not $ref any records/*.schema.json file (Group 1 shared-only
    # dependency) -- every $ref in the document must target ../shared/ or
    # a local #/$defs/ fragment, never ../records/.
    with cltr_cutover_root() as root:
        document = json.loads(
            (root / "records" / "compatibility_state.schema.json").read_text(encoding="utf-8")
        )

    def _collect_refs(node):
        if isinstance(node, dict):
            if "$ref" in node:
                yield node["$ref"]
            for value in node.values():
                yield from _collect_refs(value)
        elif isinstance(node, list):
            for item in node:
                yield from _collect_refs(item)

    refs = list(_collect_refs(document))
    assert refs, "expected at least one $ref (shared envelope/identity/digest/enums)"
    assert all(ref.startswith("../shared/") or ref.startswith("#/") for ref in refs), refs


def test_136v_quarantine_does_not_reference_compatibility_state_or_vice_versa():
    # Sibling independence: neither Group 11 family $refs the other.
    with cltr_cutover_root() as root:
        compat_text = (root / "records" / "compatibility_state.schema.json").read_text(encoding="utf-8")
        quarantine_text = (root / "records" / "quarantine_record.schema.json").read_text(encoding="utf-8")
    assert "quarantine_record.schema.json" not in compat_text
    assert "compatibility_state.schema.json" not in quarantine_text


# ---------------------------------------------------------------------------
# 8. Dependency graphs / group atomicity
# ---------------------------------------------------------------------------


def test_136v_full_manifest_dependency_graph_is_acyclic():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_id = {e["schema_id"]: e for e in manifest["entries"]}

    def _visit(schema_id, stack):
        if schema_id in stack:
            raise AssertionError(f"cycle detected: {stack + [schema_id]}")
        entry = by_id.get(schema_id)
        if entry is None:
            return
        for dep in entry["dependencies"]:
            _visit(dep, stack + [schema_id])

    for schema_id in by_id:
        _visit(schema_id, [])


def test_136v_full_ref_graph_resolves_without_unresolvable_reference(registry):
    for schema_id in (COMPAT_ID, QUARANTINE_ID):
        assert schema_id in registry.schema_ids


@pytest.mark.parametrize(
    "valid_fn,schema_id",
    [(_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)],
)
def test_136v_group11_creation_order_independent_of_sibling(valid_fn, schema_id, registry):
    # Neither Group 11 schema requires the other to already exist to
    # validate -- both are independently, concurrently valid.
    assert _validate(_valid_compat(), COMPAT_ID, registry).status is OutcomeStatus.VALID
    assert _validate(_valid_quarantine(), QUARANTINE_ID, registry).status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 9. No-execution / no-authority / no-network boundaries
# ---------------------------------------------------------------------------


def test_136v_no_subprocess_shell_socket_or_dynamic_execution_in_new_files():
    forbidden_tokens = ("subprocess.", "os.system(", "eval(", "exec(", "socket.")
    for path in GROUP11_RECORD_FILES:
        with cltr_cutover_root() as root:
            text = (root / path).read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text


def test_136v_no_network_during_registry_and_validation(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted during offline schema validation")

    monkeypatch.setattr(socket, "socket", _raise)
    monkeypatch.setattr(socket, "create_connection", _raise)
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        assert _validate(_valid_compat(), COMPAT_ID, reg).status is OutcomeStatus.VALID
        assert _validate(_valid_quarantine(), QUARANTINE_ID, reg).status is OutcomeStatus.VALID


def test_136v_validation_never_mutates_input_record(registry):
    for valid_fn, schema_id in ((_valid_compat, COMPAT_ID), (_valid_quarantine, QUARANTINE_ID)):
        record = valid_fn()
        before = copy.deepcopy(record)
        _validate(record, schema_id, registry)
        assert record == before


def test_136v_no_persistence_directory_created_during_validation(tmp_path, registry):
    before = set(tmp_path.iterdir())
    _validate(_valid_compat(), COMPAT_ID, registry)
    _validate(_valid_quarantine(), QUARANTINE_ID, registry)
    after = set(tmp_path.iterdir())
    assert before == after


def test_136v_no_compatibility_execution_symbol_referenced():
    forbidden = ("migration_executor", "adapter_selector", "version_upgrader", "version_downgrader",
                 "compatibility_resolver", "compatibility_decision_engine")
    for path in GROUP11_RECORD_FILES:
        with cltr_cutover_root() as root:
            text = (root / path).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text


def test_136v_no_quarantine_mutation_symbol_referenced():
    forbidden = ("quarantine_directory", "file_move", "file_rename", "atomic_rename",
                 "symlink_change", "release_operation", "restoration", "repair_artifact")
    for path in GROUP11_RECORD_FILES:
        with cltr_cutover_root() as root:
            text = (root / path).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text


def test_136v_no_authority_resolver_symbol_referenced_in_new_schema_text():
    forbidden = ("authority_resolver", "current_authority_lookup", "authority_pointer_write",
                 "authority_activation", "legacy_demotion", "legacy_retirement")
    for path in GROUP11_RECORD_FILES:
        with cltr_cutover_root() as root:
            text = (root / path).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text


def test_136v_no_authority_epoch_mutation_or_pointer_created():
    assert not (REPO_ROOT / ".pcae" / "cltr-authority").exists()


# ---------------------------------------------------------------------------
# 10. Packaging / installed-wheel
# ---------------------------------------------------------------------------


def test_136v_group11_schemas_load_from_editable_install(registry):
    assert COMPAT_ID in registry.schema_ids
    assert QUARANTINE_ID in registry.schema_ids


@pytest.mark.slow
def test_136v_wheel_contains_group11_schemas_no_group12_schema(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()

    for path in GROUP11_RECORD_FILES:
        assert f"pcae/schema_resources/cltr_cutover/{path}" in names
    for forbidden in LATER_GROUP_RECORD_FILES:
        stem = Path(forbidden).name
        assert not any(name.endswith(stem) for name in names)


@pytest.mark.slow
def test_136v_installed_wheel_validates_group11_fixtures_outside_repository(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv136v"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    venv_python = venv_dir / "bin" / "python"
    assert venv_python.exists()

    install = subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheels[0]), "jsonschema>=4.18,<5"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr

    outside_cwd = tmp_path / "elsewhere"
    outside_cwd.mkdir()
    probe_script = (
        "from pcae.schema_resources import cltr_cutover_root\n"
        "from pcae.schema_runtime import build_offline_registry, validate_record_shape, OutcomeStatus\n"
        "with cltr_cutover_root() as root:\n"
        "    reg = build_offline_registry(root)\n"
        "assert len(reg.schema_ids) == 24, reg.schema_ids\n"
        "valid = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/compatibility_state.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0', 'record_type': 'compatibility_state',\n"
        "    'record_id': 'compatstate-9000001', 'record_digest': 'a'*64, 'created_at': '2026-07-17T00:00:00Z',\n"
        "    'migration_epoch': 'epoch-w', 'component': 'legacy_reader', 'role': 'compatibility',\n"
        "    'allowed_reads': [], 'forbidden_authority_use': True, 'fallback_disabled': False,\n"
        "    'mode': 'legacy_adapter', 'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'evidence', 'is_authoritative': False, 'disclosure_text': 'x'},\n"
        "}\n"
        "result = validate_record_shape(valid, schema_id=valid['schema_id'], registry=reg)\n"
        "assert result.status is OutcomeStatus.VALID, result.issues\n"
        "print('OK')\n"
    )
    probe = subprocess.run(
        [str(venv_python), "-c", probe_script],
        cwd=outside_cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr
    assert "OK" in probe.stdout
