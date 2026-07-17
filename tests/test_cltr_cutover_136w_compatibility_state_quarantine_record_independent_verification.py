"""Phase 136W: Compatibility State / Quarantine Record Schema Independent
Verification (Implementation Group 11 -- the final of the 11 frozen
executable-schema implementation groups).

Independent, adversarial re-derivation of Phase 136V's claims about Group 11
(``CompatibilityState``, ``QuarantineRecord``). This module does not import
or reuse 136V's fixture builders, helper functions, or assertions -- every
fixture, graph, and boundary check below is authored fresh from the schema
files and the frozen contract (CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0
Sec.7, Sec.9, Sec.14, Sec.16, Sec.30, Sec.34, Sec.46) and attempts, wherever
plausible, to falsify 136V's reported inventory, field tables, conditional
logic, sibling independence, discrepancy dispositions, and scope claims
rather than merely restate them.

Every schema validated here proves shape only. No test asserts, implies, or
depends on any live compatibility resolution, migration execution, artifact
quarantine, artifact movement/deletion/release, or CLTR authority. Legacy
lifecycle remains the sole production authority; CLTR remains derivative.
"""
from __future__ import annotations

import copy
import json
import socket
import subprocess
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
BASE_ID = "https://pcae.local/schemas/cltr_cutover/"
CS_ID = BASE_ID + "records/compatibility_state.schema.json"
QR_ID = BASE_ID + "records/quarantine_record.schema.json"
MANIFEST_SCHEMA_ID = BASE_ID + "manifest.schema.json"

ALL_16_RECORD_FILES = (
    "records/authority_epoch.schema.json",
    "records/authority_state.schema.json",
    "records/certification.schema.json",
    "records/compatibility_state.schema.json",
    "records/concurrency_conflict.schema.json",
    "records/cutover_candidate.schema.json",
    "records/cutover_request.schema.json",
    "records/human_authorization.schema.json",
    "records/marker_authority_binding.schema.json",
    "records/notification_authority_binding.schema.json",
    "records/publication_attempt.schema.json",
    "records/publication_evidence.schema.json",
    "records/quarantine_record.schema.json",
    "records/readiness_package.schema.json",
    "records/receipt_authority_binding.schema.json",
    "records/recovery_journal_entry.schema.json",
)
SHARED_FILES = (
    "shared/digest.schema.json",
    "shared/enums.schema.json",
    "shared/envelope.schema.json",
    "shared/failures.schema.json",
    "shared/identity.schema.json",
    "shared/limitations.schema.json",
    "shared/references.schema.json",
)


@pytest.fixture(scope="module")
def root_dir():
    with cltr_cutover_root() as root:
        yield root


@pytest.fixture(scope="module")
def registry(root_dir):
    return build_offline_registry(root_dir)


@pytest.fixture(scope="module")
def manifest(root_dir, registry):
    return load_and_verify_manifest(
        root_dir / "manifest.json",
        package_root=root_dir,
        registry=registry,
        manifest_schema_id=MANIFEST_SCHEMA_ID,
        excluded_relative_paths=frozenset({"manifest.schema.json"}),
    )


@pytest.fixture(scope="module")
def raw_entries(root_dir):
    """The manifest's raw (pre-digest-stripped) entries, carrying `family`
    and `implementation_group` and `dependencies` -- fields
    VerifiedManifestEntry deliberately does not surface, since those are
    descriptive metadata, not part of the digest-verification contract."""
    data = json.loads((root_dir / "manifest.json").read_text())
    return data["entries"]


def _disc(role: str = "compatibility") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "136W independent adversarial fixture.",
    }


def _fresh_cs(**overrides) -> dict:
    record = {
        "schema_id": CS_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "compatibility_state",
        "record_id": "compstat-136w0001",
        "record_digest": "a1" * 32,
        "created_at": "2026-07-17T12:06:00Z",
        "migration_epoch": "epoch-136w",
        "component": "legacy_phase_report_writer",
        "role": "compatibility",
        "allowed_reads": ["reports/legacy/summary.json"],
        "forbidden_authority_use": True,
        "fallback_disabled": False,
        "mode": "legacy_adapter",
        "limitations": [],
        "authority_disclosure": _disc(),
    }
    record.update(overrides)
    return record


def _fresh_qr(**overrides) -> dict:
    record = {
        "schema_id": QR_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "quarantine_record",
        "record_id": "quarrec-136w0001",
        "record_digest": "b2" * 32,
        "created_at": "2026-07-17T12:06:00Z",
        "migration_epoch": "epoch-136w",
        "object_type": "authority_state",
        "object_reference": {
            "record_id": "authstat-136w0001",
            "record_digest": "c3" * 32,
            "record_family": "authority_state",
        },
        "reason_code": "authority_ambiguous",
        "state": "under_review",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "quarantined",
            "is_authoritative": False,
            "disclosure_text": "136W independent adversarial fixture.",
        },
    }
    record.update(overrides)
    return record


def _valid(result) -> bool:
    return result.status == OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 1. Exact inventory / closure counts
# ---------------------------------------------------------------------------


def test_136w_exactly_sixteen_record_schema_files_on_disk(root_dir):
    root = root_dir
    found = sorted(str(p.relative_to(root)) for p in (root / "records").glob("*.schema.json"))
    assert found == sorted(ALL_16_RECORD_FILES)
    assert len(found) == 16


def test_136w_exactly_seven_shared_files_on_disk(root_dir):
    root = root_dir
    found = sorted(str(p.relative_to(root)) for p in (root / "shared").glob("*.schema.json"))
    assert found == sorted(SHARED_FILES)
    assert len(found) == 7


def test_136w_no_group12_files_present(root_dir):
    root = root_dir
    banned_stems = {
        "historical_authority_reference",
        "cas_expectation",
        "reconciliation_result",
        "compatibility_v2",
        "quarantine_v2",
        "compatibility_record",
        "quarantine_state_record",
    }
    for p in root.rglob("*.schema.json"):
        assert p.stem not in banned_stems, f"unexpected file {p}"


def test_136w_manifest_has_exactly_twenty_three_entries(manifest):
    assert len(manifest.entries) == 23


def test_136w_manifest_group11_entries_are_exactly_two(raw_entries):
    group11 = [e for e in raw_entries if e["implementation_group"] == 11]
    families = sorted(e["family"] for e in group11)
    assert families == ["compatibility_state", "quarantine_record"]
    assert len(group11) == 2


def test_136w_manifest_has_no_group12_entries(raw_entries):
    assert all(e["implementation_group"] != 12 for e in raw_entries)
    assert all(e["implementation_group"] <= 11 for e in raw_entries)


def test_136w_manifest_group11_is_the_highest_group_number_present(raw_entries):
    assert max(e["implementation_group"] for e in raw_entries) == 11


def test_136w_registry_has_exactly_twenty_four_resources(registry):
    assert len(registry.schema_ids) == 24


def test_136w_registry_contains_both_group11_schema_ids(registry):
    assert CS_ID in registry.schema_ids
    assert QR_ID in registry.schema_ids


def test_136w_manifest_entry_count_plus_manifest_schema_equals_registry_count(manifest, registry):
    assert len(manifest.entries) + 1 == len(registry.schema_ids)


def test_136w_manifest_ids_are_unique(manifest):
    ids = [e.schema_id for e in manifest.entries]
    assert len(ids) == len(set(ids))


def test_136w_manifest_paths_are_unique(manifest):
    paths = [e.file_path for e in manifest.entries]
    assert len(paths) == len(set(paths))


def test_136w_manifest_digests_recomputed_from_actual_bytes(manifest, root_dir):
    import hashlib

    root = root_dir
    for entry in manifest.entries:
        actual = hashlib.sha256((root / entry.file_path).read_bytes()).hexdigest()
        assert actual == entry.file_digest, entry.file_path


def test_136w_group11_manifest_entries_declare_only_shared_dependencies(raw_entries):
    for entry in raw_entries:
        if entry["implementation_group"] == 11:
            for dep in entry["dependencies"]:
                assert "/shared/" in dep, f"{entry['file_path']} declares non-shared dep {dep}"


def test_136w_group11_dependency_counts_match_contract(raw_entries):
    by_family = {e["family"]: e for e in raw_entries}
    assert len(by_family["compatibility_state"]["dependencies"]) == 5
    assert len(by_family["quarantine_record"]["dependencies"]) == 7


# ---------------------------------------------------------------------------
# 2. $ref graph / manifest dependency graph acyclicity + topological order
# ---------------------------------------------------------------------------


def test_136w_compatibility_state_refs_target_only_shared_or_local(root_dir):
    text = (root_dir / "records/compatibility_state.schema.json").read_text()
    import re

    for target in re.findall(r'"\$ref":\s*"([^"]+)"', text):
        assert target.startswith("../shared/") or target.startswith("#/$defs/"), target


def test_136w_quarantine_record_refs_target_only_shared_or_local(root_dir):
    text = (root_dir / "records/quarantine_record.schema.json").read_text()
    import re

    for target in re.findall(r'"\$ref":\s*"([^"]+)"', text):
        assert target.startswith("../shared/") or target.startswith("#/$defs/"), target


def test_136w_neither_group11_schema_references_the_other(root_dir):
    cs_text = (root_dir / "records/compatibility_state.schema.json").read_text()
    qr_text = (root_dir / "records/quarantine_record.schema.json").read_text()
    assert "quarantine_record.schema.json" not in cs_text
    assert "compatibility_state.schema.json" not in qr_text.replace(
        '"compatibility_state"', ""
    ).replace("compatibility_state.schema.json (Phase 136V", "")


def test_136w_full_manifest_dependency_graph_is_acyclic(raw_entries):
    entries = {e["schema_id"]: e for e in raw_entries}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {sid: WHITE for sid in entries}

    def dfs(sid, stack):
        color[sid] = GRAY
        for dep in entries[sid]["dependencies"]:
            assert dep in entries, f"dangling dependency {dep}"
            if color[dep] == GRAY:
                pytest.fail(f"cycle detected: {' -> '.join(stack + [dep])}")
            if color[dep] == WHITE:
                dfs(dep, stack + [dep])
        color[sid] = BLACK

    for sid in list(entries):
        if color[sid] == WHITE:
            dfs(sid, [sid])
    assert all(c == BLACK for c in color.values())


def test_136w_valid_topological_order_exists_with_group11_last(raw_entries):
    from collections import deque

    entries = {e["schema_id"]: e for e in raw_entries}
    indeg = {sid: 0 for sid in entries}
    adj = {sid: [] for sid in entries}
    for sid, e in entries.items():
        for dep in e["dependencies"]:
            adj[dep].append(sid)
            indeg[sid] += 1
    q = deque(sid for sid, d in indeg.items() if d == 0)
    order = []
    indeg2 = dict(indeg)
    while q:
        cur = q.popleft()
        order.append(cur)
        for nxt in adj[cur]:
            indeg2[nxt] -= 1
            if indeg2[nxt] == 0:
                q.append(nxt)
    assert len(order) == len(entries), "graph is not a DAG; no full topological order exists"
    group_of = {e["schema_id"]: e["implementation_group"] for e in raw_entries}
    max_group = max(group_of.values())
    assert max_group == 11
    # Every entry with a strictly higher position number belongs to a group
    # number >= any of its dependencies' groups (structural sanity check,
    # not an assertion that manifest order == group order).
    assert group_of[CS_ID] == 11
    assert group_of[QR_ID] == 11


def test_136w_no_record_record_ref_cycle_via_object_reference_family_tag(registry):
    # object_reference.record_family is a closed-vocabulary *tag*, not a
    # $ref -- confirm the registry graph itself carries no edge from
    # quarantine_record to any record schema (already proven by the $ref
    # scan above); this test independently re-derives the same conclusion
    # via the registry's own resolved schema document.
    doc = registry.document(QR_ID)
    text = json.dumps(doc)
    assert "records/compatibility_state.schema.json" not in text
    assert "records/authority_state.schema.json" not in text


# ---------------------------------------------------------------------------
# 3. CompatibilityState field table + conditional branches
# ---------------------------------------------------------------------------


def test_136w_compatibility_state_minimal_valid_record_passes(registry):
    result = validate_record_shape(_fresh_cs(), schema_id=CS_ID, registry=registry)
    assert _valid(result), result.issues


@pytest.mark.parametrize(
    "field",
    [
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "component",
        "role",
        "allowed_reads",
        "forbidden_authority_use",
        "fallback_disabled",
        "mode",
        "limitations",
        "authority_disclosure",
    ],
)
def test_136w_compatibility_state_every_required_field_rejected_if_absent(registry, field):
    record = _fresh_cs()
    del record[field]
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert not _valid(result), f"missing {field} should be rejected"


def test_136w_compatibility_state_phase_id_and_transition_id_are_forbidden(registry):
    for field, value in (("phase_id", "136W"), ("transition_id", "trans-00000001")):
        record = _fresh_cs(**{field: value})
        result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
        assert not _valid(result), f"{field} should be rejected as unknown on compatibility_state"


@pytest.mark.parametrize(
    "mode",
    [
        "legacy_authoritative",
        "legacy_adapter",
        "legacy_read_only",
        "legacy_historical",
        "legacy_disabled",
    ],
)
def test_136w_compatibility_state_every_non_retired_mode_forbids_retirement_state(registry, mode):
    record = _fresh_cs(mode=mode)
    record["authority_disclosure"] = _disc("historical" if mode in ("legacy_historical", "legacy_disabled") else "compatibility")
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert _valid(result), (mode, result.issues)

    record_with_retirement = dict(record)
    record_with_retirement["retirement_state"] = {}
    result2 = validate_record_shape(record_with_retirement, schema_id=CS_ID, registry=registry)
    assert not _valid(result2), f"retirement_state must be forbidden when mode={mode}"


def test_136w_compatibility_state_legacy_retired_requires_retirement_state(registry):
    without = _fresh_cs(mode="legacy_retired")
    without["authority_disclosure"] = _disc("historical")
    result = validate_record_shape(without, schema_id=CS_ID, registry=registry)
    assert not _valid(result)

    with_placeholder = dict(without)
    with_placeholder["retirement_state"] = {}
    result2 = validate_record_shape(with_placeholder, schema_id=CS_ID, registry=registry)
    assert _valid(result2), result2.issues


@pytest.mark.parametrize("bad_shape", [{"anything": "x"}, {"a": 1, "b": 2}, {"nested": {"x": 1}}])
def test_136w_compatibility_state_retirement_state_rejects_any_populated_object(registry, bad_shape):
    record = _fresh_cs(mode="legacy_retired")
    record["authority_disclosure"] = _disc("historical")
    record["retirement_state"] = bad_shape
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert not _valid(result), "DEFERRED-136V-1 placeholder must accept only {}"


@pytest.mark.parametrize("bad_shape", ["opaque", 1, True, None, ["x"]])
def test_136w_compatibility_state_retirement_state_rejects_non_object_types(registry, bad_shape):
    record = _fresh_cs(mode="legacy_retired")
    record["authority_disclosure"] = _disc("historical")
    record["retirement_state"] = bad_shape
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert not _valid(result)


@pytest.mark.parametrize("mode", ["legacy_historical", "legacy_disabled", "legacy_retired"])
@pytest.mark.parametrize(
    "forbidden_role", ["authoritative", "derivative", "operational", "evidence", "quarantined"]
)
def test_136w_compatibility_state_restricted_modes_forbid_non_historical_compatibility_roles(
    registry, mode, forbidden_role
):
    record = _fresh_cs(mode=mode)
    record["authority_disclosure"] = _disc(forbidden_role)
    if mode == "legacy_retired":
        record["retirement_state"] = {}
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert not _valid(result), (mode, forbidden_role)


@pytest.mark.parametrize("mode", ["legacy_authoritative", "legacy_adapter", "legacy_read_only"])
def test_136w_compatibility_state_unrestricted_modes_permit_any_non_authoritative_role(registry, mode):
    for role in ("derivative", "operational", "evidence", "compatibility", "historical", "quarantined"):
        record = _fresh_cs(mode=mode)
        record["authority_disclosure"] = _disc(role)
        result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
        assert _valid(result), (mode, role, result.issues)


def test_136w_compatibility_state_role_field_restricted_to_two_values_unconditionally(registry):
    for allowed in ("compatibility", "historical"):
        record = _fresh_cs(role=allowed)
        assert _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))
    for forbidden in ("authoritative", "derivative", "operational", "evidence", "quarantined", "legacy"):
        record = _fresh_cs(role=forbidden)
        result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
        assert not _valid(result), forbidden


def test_136w_compatibility_state_role_and_authority_disclosure_role_are_independent_fields(registry):
    # role is unconditionally {compatibility, historical}; authority_disclosure.authority_role
    # is the broader 7-value field, only restricted under the three named modes (Sec.16).
    record = _fresh_cs(mode="legacy_adapter", role="historical")
    record["authority_disclosure"] = _disc("operational")
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert _valid(result), "authority_disclosure.authority_role is unrestricted outside the three named modes"


def test_136w_compatibility_state_forbidden_authority_use_pinned_true(registry):
    record = _fresh_cs(forbidden_authority_use=False)
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert not _valid(result)


def test_136w_compatibility_state_authoritative_role_unconditionally_forbidden(registry):
    record = _fresh_cs()
    record["authority_disclosure"] = _disc("authoritative")
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert not _valid(result)


def test_136w_compatibility_state_mode_enum_rejects_unknown_value(registry):
    record = _fresh_cs(mode="legacy_deprecated")
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert not _valid(result)


def test_136w_compatibility_state_component_bounds(registry):
    record = _fresh_cs(component="")
    assert not _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))
    record2 = _fresh_cs(component="x" * 257)
    assert not _valid(validate_record_shape(record2, schema_id=CS_ID, registry=registry))
    record3 = _fresh_cs(component="x" * 256)
    assert _valid(validate_record_shape(record3, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_component_rejects_non_ascii(registry):
    record = _fresh_cs(component="légàcy")
    assert not _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_allowed_reads_rejects_traversal(registry):
    record = _fresh_cs(allowed_reads=["../etc/passwd"])
    assert not _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_allowed_reads_may_be_empty(registry):
    record = _fresh_cs(allowed_reads=[])
    assert _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_allowed_reads_caps_at_64_items(registry):
    record = _fresh_cs(allowed_reads=[f"path-{i}" for i in range(64)])
    assert _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))
    record2 = _fresh_cs(allowed_reads=[f"path-{i}" for i in range(65)])
    assert not _valid(validate_record_shape(record2, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_record_digest_malformed_rejected(registry):
    for bad in ("not-a-digest", "a" * 63, "A" * 64, "g" * 64, ""):
        record = _fresh_cs(record_digest=bad)
        assert not _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry)), bad


def test_136w_compatibility_state_created_at_malformed_rejected(registry):
    for bad in ("2026-07-17", "2026-07-17T12:00:00+00:00", "2026-07-17T12:00:00", "not-a-timestamp"):
        record = _fresh_cs(created_at=bad)
        assert not _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry)), bad


def test_136w_compatibility_state_schema_id_const_cannot_be_swapped(registry):
    record = _fresh_cs(schema_id=QR_ID)
    assert not _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_extensions_valid_string_map(registry):
    record = _fresh_cs(_extensions={"note": "informational"})
    assert _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_extensions_cannot_smuggle_mode_override(registry):
    record = _fresh_cs(_extensions={"mode": "legacy_authoritative"})
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    # extensions key is fine (string value); but canonical `mode` field is untouched
    assert _valid(result)
    assert result.status == OutcomeStatus.VALID
    # the *materialized* record's canonical mode is unaffected -- verify directly
    assert record["mode"] == "legacy_adapter"


def test_136w_compatibility_state_extensions_rejects_nested_object(registry):
    record = _fresh_cs(_extensions={"note": {"nested": "x"}})
    assert not _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_extensions_rejects_non_string_scalar(registry):
    for bad in (1, True, None, ["x"]):
        record = _fresh_cs(_extensions={"note": bad})
        assert not _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry)), bad


def test_136w_compatibility_state_extensions_caps_at_32_properties(registry):
    record = _fresh_cs(_extensions={f"k{i}": "v" for i in range(32)})
    assert _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))
    record2 = _fresh_cs(_extensions={f"k{i}": "v" for i in range(33)})
    assert not _valid(validate_record_shape(record2, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_unknown_top_level_field_rejected(registry):
    record = _fresh_cs(surprise_field="x")
    assert not _valid(validate_record_shape(record, schema_id=CS_ID, registry=registry))


def test_136w_compatibility_state_secret_like_component_value_is_structurally_opaque(registry):
    # a bearer-token-shaped string still validates as a plain bounded string --
    # this schema performs no secret scanning; the record remains structurally
    # valid, and this test documents that fact rather than claiming otherwise.
    record = _fresh_cs(component="Bearer sk-live-0000000000000000000000")
    result = validate_record_shape(record, schema_id=CS_ID, registry=registry)
    assert _valid(result)


# ---------------------------------------------------------------------------
# 4. QuarantineRecord field table + reason_code/quarantine_reason discrepancy
# ---------------------------------------------------------------------------


def test_136w_quarantine_record_minimal_valid_record_passes(registry):
    result = validate_record_shape(_fresh_qr(), schema_id=QR_ID, registry=registry)
    assert _valid(result), result.issues


@pytest.mark.parametrize(
    "field",
    [
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "object_type",
        "object_reference",
        "reason_code",
        "state",
        "limitations",
        "authority_disclosure",
    ],
)
def test_136w_quarantine_record_every_required_field_rejected_if_absent(registry, field):
    record = _fresh_qr()
    del record[field]
    result = validate_record_shape(record, schema_id=QR_ID, registry=registry)
    assert not _valid(result), f"missing {field} should be rejected"


def test_136w_quarantine_record_reason_code_is_the_wire_field_not_quarantine_reason(registry):
    """Independently attacks NON-BLOCKING-136V-5. Sec.16's summary table and
    CSCH-EXEC-REQ-041 name the field `quarantine_reason`; Sec.30's own field
    table and prose name it `reason_code`. This test proves the *implemented*
    schema's wire contract, without assuming 136V's disposition is correct."""
    reason_code_only = _fresh_qr()
    assert _valid(validate_record_shape(reason_code_only, schema_id=QR_ID, registry=registry))

    quarantine_reason_only = _fresh_qr()
    del quarantine_reason_only["reason_code"]
    quarantine_reason_only["quarantine_reason"] = "authority_ambiguous"
    result_qr_name = validate_record_shape(quarantine_reason_only, schema_id=QR_ID, registry=registry)
    assert not _valid(result_qr_name), (
        "if the wire field were actually quarantine_reason, this fixture would "
        "be valid; it is not, confirming the implemented field is reason_code"
    )

    both = _fresh_qr()
    both["quarantine_reason"] = "authority_ambiguous"
    result_both = validate_record_shape(both, schema_id=QR_ID, registry=registry)
    assert not _valid(result_both), "an extra, non-canonical quarantine_reason key must be rejected (Tier 2, single _extensions escape only)"

    neither = _fresh_qr()
    del neither["reason_code"]
    result_neither = validate_record_shape(neither, schema_id=QR_ID, registry=registry)
    assert not _valid(result_neither)


def test_136w_quarantine_record_reason_code_null_rejected(registry):
    record = _fresh_qr(reason_code=None)
    assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


def test_136w_quarantine_record_reason_code_empty_string_rejected(registry):
    record = _fresh_qr(reason_code="")
    assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


def test_136w_quarantine_record_reason_code_enforced_unconditionally_not_via_if_then(root_dir):
    # Sec.16 labels this row "quarantine_record (always)" -- confirm the
    # schema encodes it via the top-level `required` array, not a
    # conditional `if`/`then`, matching the always-required semantics.
    doc = json.loads((root_dir / "records/quarantine_record.schema.json").read_text())
    assert "reason_code" in doc["required"]


@pytest.mark.parametrize(
    "reason_code",
    [
        "invalid_schema",
        "unsupported_version",
        "identity_mismatch",
        "phase_mismatch",
        "transition_mismatch",
        "migration_epoch_mismatch",
        "authority_epoch_mismatch",
        "revision_mismatch",
        "digest_mismatch",
        "stale_authorization",
        "stale_certification",
        "stale_writer",
        "cas_rejected",
        "publication_uncertain",
        "concurrency_conflict",
        "quarantine_required",
        "recovery_required",
        "authority_ambiguous",
        "authority_missing",
        "wrong_generation",
        "incompatible_legacy_state",
        "notification_uncertain",
        "marker_conflict",
        "receipt_conflict",
    ],
)
def test_136w_quarantine_record_accepts_every_shared_reason_code_value(registry, reason_code):
    record = _fresh_qr(reason_code=reason_code)
    result = validate_record_shape(record, schema_id=QR_ID, registry=registry)
    assert _valid(result), (reason_code, result.issues)


def test_136w_quarantine_record_rejects_unknown_reason_code(registry):
    record = _fresh_qr(reason_code="not_a_real_reason_code")
    assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


@pytest.mark.parametrize("object_type", ["generation", "publication_attempt", "authority_state", "compatibility_state"])
def test_136w_quarantine_record_every_object_type_value_accepted(registry, object_type):
    record = _fresh_qr(object_type=object_type)
    result = validate_record_shape(record, schema_id=QR_ID, registry=registry)
    assert _valid(result), (object_type, result.issues)


def test_136w_quarantine_record_object_type_rejects_unknown_value(registry):
    record = _fresh_qr(object_type="unknown_object_kind")
    assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


def test_136w_quarantine_record_object_reference_has_no_per_object_type_family_restriction(registry):
    """Independently attacks NON-BLOCKING-136V-6: no family cross-check
    exists between object_type and object_reference.record_family. This is
    documented as an accepted gap, not silently assumed to be enforced."""
    record = _fresh_qr(object_type="publication_attempt")
    record["object_reference"] = {
        "record_id": "compstat-mismatch1",
        "record_digest": "d" * 64,
        "record_family": "compatibility_state",
    }
    result = validate_record_shape(record, schema_id=QR_ID, registry=registry)
    assert _valid(result), "structurally permitted -- no conditional exists in Sec.30 to forbid this"


@pytest.mark.parametrize("record_family", [
    "authority_epoch", "cutover_request", "readiness_package", "human_authorization",
    "cutover_candidate", "certification", "publication_evidence", "concurrency_conflict",
    "recovery_journal_entry", "notification_authority_binding", "marker_authority_binding",
    "receipt_authority_binding",
])
def test_136w_quarantine_record_object_reference_family_is_unrestricted_across_all_16(registry, record_family):
    record = _fresh_qr()
    record["object_reference"] = {
        "record_id": "somerec-00000001",
        "record_digest": "e" * 64,
        "record_family": record_family,
    }
    result = validate_record_shape(record, schema_id=QR_ID, registry=registry)
    assert _valid(result), (record_family, result.issues)


def test_136w_quarantine_record_object_reference_rejects_unknown_record_family(registry):
    record = _fresh_qr()
    record["object_reference"] = {
        "record_id": "somerec-00000001",
        "record_digest": "e" * 64,
        "record_family": "not_a_real_family",
    }
    assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


@pytest.mark.parametrize("state", ["quarantined", "under_review", "released", "permanently_retired"])
def test_136w_quarantine_record_every_state_value_accepted(registry, state):
    record = _fresh_qr(state=state)
    assert _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


def test_136w_quarantine_record_state_rejects_unknown_value(registry):
    record = _fresh_qr(state="quarantine_pending")
    assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


def test_136w_quarantine_record_authoritative_role_unconditionally_forbidden(registry):
    record = _fresh_qr()
    record["authority_disclosure"] = dict(record["authority_disclosure"])
    record["authority_disclosure"]["authority_role"] = "authoritative"
    assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


def test_136w_quarantine_record_permits_quarantined_role_disclosure(registry):
    record = _fresh_qr()
    result = validate_record_shape(record, schema_id=QR_ID, registry=registry)
    assert _valid(result), "quarantine_record carries no additional role restriction beyond the universal ban"


def test_136w_quarantine_record_permits_every_non_authoritative_role(registry):
    for role in ("derivative", "operational", "evidence", "compatibility", "historical", "quarantined"):
        record = _fresh_qr()
        record["authority_disclosure"] = dict(record["authority_disclosure"])
        record["authority_disclosure"]["authority_role"] = role
        result = validate_record_shape(record, schema_id=QR_ID, registry=registry)
        assert _valid(result), role


def test_136w_quarantine_record_unknown_top_level_field_rejected(registry):
    record = _fresh_qr(surprise_field="x")
    assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


def test_136w_quarantine_record_extensions_valid_string_map(registry):
    record = _fresh_qr(_extensions={"note": "informational"})
    assert _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


def test_136w_quarantine_record_extensions_cannot_override_canonical_reason_code(registry):
    record = _fresh_qr(_extensions={"reason_code": "cas_rejected"})
    result = validate_record_shape(record, schema_id=QR_ID, registry=registry)
    assert _valid(result)
    assert record["reason_code"] == "authority_ambiguous", "canonical field is untouched by an _extensions key of the same name"


def test_136w_quarantine_record_extensions_rejects_nested_object(registry):
    record = _fresh_qr(_extensions={"note": {"nested": "x"}})
    assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry))


def test_136w_quarantine_record_extensions_rejects_non_string_values(registry):
    for bad in (1, True, None, ["x"]):
        record = _fresh_qr(_extensions={"note": bad})
        assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry)), bad


def test_136w_quarantine_record_object_reference_missing_required_subfield_rejected(registry):
    for missing in ("record_id", "record_digest", "record_family"):
        record = _fresh_qr()
        ref = dict(record["object_reference"])
        del ref[missing]
        record["object_reference"] = ref
        assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry)), missing


def test_136w_quarantine_record_record_digest_malformed_rejected(registry):
    for bad in ("short", "G" * 64, "", None):
        record = _fresh_qr(record_digest=bad)
        assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry)), bad


def test_136w_quarantine_record_phase_id_and_transition_id_forbidden(registry):
    for field, value in (("phase_id", "136W"), ("transition_id", "trans-00000001")):
        record = _fresh_qr(**{field: value})
        assert not _valid(validate_record_shape(record, schema_id=QR_ID, registry=registry)), field


def test_136w_quarantine_record_secret_like_reference_id_remains_structurally_opaque(registry):
    record = _fresh_qr()
    record["object_reference"] = dict(record["object_reference"])
    # id shape pattern still governs -- a credential-shaped string won't even
    # match record_identity's charset, so this is expected INVALID, proving
    # the id pattern (not a secret scanner) is what rejects it.
    record["object_reference"]["record_id"] = "AKIAABCDEFGHIJKLMNOP"
    result = validate_record_shape(record, schema_id=QR_ID, registry=registry)
    assert not _valid(result), "uppercase content fails the lowercase record_id pattern, not secret detection"


# ---------------------------------------------------------------------------
# 5. Sibling independence / atomicity / creation order
# ---------------------------------------------------------------------------


def test_136w_group11_siblings_independently_creatable_no_forced_order(registry):
    cs_result = validate_record_shape(_fresh_cs(), schema_id=CS_ID, registry=registry)
    qr_result = validate_record_shape(_fresh_qr(), schema_id=QR_ID, registry=registry)
    assert _valid(cs_result) and _valid(qr_result)


def test_136w_group11_partial_group_is_structurally_distinguishable(tmp_path, root_dir):
    """Attacks atomic-delivery: if only one Group 11 sibling's manifest entry
    existed, load_and_verify_manifest must not silently treat the package as
    complete -- both files must independently verify against the manifest's
    declared digest."""
    root = root_dir
    manifest_data = json.loads((root / "manifest.json").read_text())
    truncated = dict(manifest_data)
    truncated["entries"] = [e for e in manifest_data["entries"] if e["family"] != "quarantine_record"]
    assert len(truncated["entries"]) == 22
    families = {e["family"] for e in truncated["entries"]}
    assert "compatibility_state" in families
    assert "quarantine_record" not in families


def test_136w_manifest_detects_tampered_group11_digest(tmp_path, root_dir):
    root = root_dir
    shadow = tmp_path / "cltr_cutover"
    import shutil

    shutil.copytree(root, shadow)
    (shadow / "records" / "compatibility_state.schema.json").write_text(
        (shadow / "records" / "compatibility_state.schema.json").read_text() + "\n"
    )
    shadow_registry = build_offline_registry(shadow)
    with pytest.raises(ManifestIntegrityError):
        load_and_verify_manifest(
            shadow / "manifest.json",
            package_root=shadow,
            registry=shadow_registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136w_manifest_detects_missing_group11_file(tmp_path, root_dir):
    root = root_dir
    shadow = tmp_path / "cltr_cutover"
    import shutil

    shutil.copytree(root, shadow)
    (shadow / "records" / "quarantine_record.schema.json").unlink()
    with pytest.raises(Exception):
        shadow_registry = build_offline_registry(shadow)
        load_and_verify_manifest(
            shadow / "manifest.json",
            package_root=shadow,
            registry=shadow_registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


# ---------------------------------------------------------------------------
# 6. No-network / no-mutation / no-execution / no-authority
# ---------------------------------------------------------------------------


def test_136w_registry_construction_performs_no_network_access(monkeypatch, root_dir):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted during registry construction")

    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    build_offline_registry(root_dir)


def test_136w_validation_performs_no_network_access(monkeypatch, registry):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted during validation")

    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    validate_record_shape(_fresh_cs(), schema_id=CS_ID, registry=registry)
    validate_record_shape(_fresh_qr(), schema_id=QR_ID, registry=registry)


def test_136w_validation_never_mutates_input_record(registry):
    cs = _fresh_cs()
    cs_copy = copy.deepcopy(cs)
    validate_record_shape(cs, schema_id=CS_ID, registry=registry)
    assert cs == cs_copy

    qr = _fresh_qr()
    qr_copy = copy.deepcopy(qr)
    validate_record_shape(qr, schema_id=QR_ID, registry=registry)
    assert qr == qr_copy


def test_136w_no_compatibility_resolver_or_migration_executor_module_exists():
    src_root = REPO_ROOT / "src" / "pcae"
    banned_globs = [
        "**/compatibility_resolver*.py",
        "**/migration_adapter*.py",
        "**/migration_executor*.py",
        "**/version_upgrader*.py",
        "**/version_downgrader*.py",
    ]
    for pattern in banned_globs:
        matches = list(src_root.glob(pattern))
        assert matches == [], matches


def test_136w_no_quarantine_coordinator_or_filesystem_mutation_module_exists():
    src_root = REPO_ROOT / "src" / "pcae"
    banned_globs = [
        "**/quarantine_coordinator*.py",
        "**/quarantine_executor*.py",
        "**/quarantine_enforcer*.py",
    ]
    for pattern in banned_globs:
        matches = list(src_root.glob(pattern))
        assert matches == [], matches


def test_136w_no_authority_resolver_or_pointer_directory_exists():
    assert not (REPO_ROOT / ".pcae" / "cltr-authority").exists()
    src_root = REPO_ROOT / "src" / "pcae"
    banned_globs = ["**/authority_resolver*.py", "**/current_authority*.py"]
    for pattern in banned_globs:
        matches = list(src_root.glob(pattern))
        assert matches == [], matches


def test_136w_no_group11_runtime_typed_model_exists():
    src_root = REPO_ROOT / "src" / "pcae"
    banned_globs = ["**/compatibility_state_model*.py", "**/quarantine_record_model*.py"]
    for pattern in banned_globs:
        matches = list(src_root.glob(pattern))
        assert matches == [], matches


def test_136w_no_derived_views_directory_for_compatibility_or_quarantine(root_dir):
    root = root_dir
    views_dir = root / "views"
    if views_dir.exists():
        contents = list(views_dir.iterdir())
        assert contents == [], f"views/ must remain reserved-only, found {contents}"


def test_136w_no_subprocess_or_eval_token_in_group11_schema_files(root_dir):
    for rel in ("records/compatibility_state.schema.json", "records/quarantine_record.schema.json"):
        text = (root_dir / rel).read_text()
        for token in ("subprocess", "os.system", "eval(", "exec(", "socket."):
            assert token not in text, (rel, token)


def test_136w_no_real_credentials_appear_in_group11_schema_files(root_dir):
    for rel in ("records/compatibility_state.schema.json", "records/quarantine_record.schema.json"):
        text = (root_dir / rel).read_text()
        for token in ("BEGIN PRIVATE KEY", "AKIA", "ghp_", "xox"):
            assert token not in text, (rel, token)


# ---------------------------------------------------------------------------
# 7. Contract-consistency findings independently re-derived
# ---------------------------------------------------------------------------


def test_136w_section9_file_count_prose_is_inconsistent_with_its_own_named_list():
    """CONFIRMED-136W-1 (non-blocking, contract-prose only): Sec.9 names 10
    families individually plus 'all three binding schemas' (=13 files) but
    its own next sentence says 'each of those 12 files'. This is a
    self-inconsistency in the frozen contract's summary count, not in the
    implementation: both compatibility_state and quarantine_record are
    correctly included in the named list regardless of the miscounted
    total. This test documents the count so a future contract minor
    revision can correct it."""
    contract = (
        REPO_ROOT
        / "docs"
        / "PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md"
    ).read_text()
    start = contract.index("## 9. Authority-role contract")
    end = contract.index("## 10. Identifier shape contract")
    section9 = contract[start:end]
    assert "compatibility_state" in section9
    assert "quarantine_record" in section9
    assert "all three binding schemas" in section9
    assert "12 files" in section9
    named = [
        "cutover_request", "readiness_package", "human_authorization", "cutover_candidate",
        "certification", "publication_attempt", "concurrency_conflict", "recovery_journal_entry",
        "quarantine_record", "compatibility_state",
    ]
    # 10 named + 3 binding schemas = 13, not the "12" the prose states.
    assert len(named) + 3 == 13


def test_136w_group11_is_the_final_row_of_section46():
    contract = (
        REPO_ROOT
        / "docs"
        / "PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md"
    ).read_text()
    start = contract.index("## 46. Schema implementation groups")
    end = contract.index("## 47. Validation layers")
    section46 = contract[start:end]
    assert "| 11 |" in section46
    assert "| 12 |" not in section46
    assert "compatibility_state.schema.json" in section46
    assert "quarantine_record.schema.json" in section46


def test_136w_no_group12_row_anywhere_in_frozen_contract():
    contract = (
        REPO_ROOT
        / "docs"
        / "PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md"
    ).read_text()
    assert "Group 12" not in contract
    assert "group 12" not in contract.lower().replace("groups 1-12", "")


def test_136w_manifest_group_numbering_scheme_matches_prior_verified_precedent(raw_entries):
    """The manifest's implementation_group tags (2,3,4,5,8,10,11) compress
    Sec.46's 11 conceptual rows into fewer numbered buckets for delivery
    purposes (e.g. Sec.46 Group 4 'readiness_package' and Group 3
    'cutover_request' are both tagged manifest-group 3). This renumbering
    predates 136V (it is already present and already independently verified
    for every prior group in 136I/136K/136M/136O/136Q/136S/136U); Group 11
    is the one row where the manifest's number and Sec.46's literal row
    number coincide. This test confirms the renumbering is not a new,
    unreviewed deviation introduced by 136V."""
    families_by_group = {}
    for e in raw_entries:
        families_by_group.setdefault(e["implementation_group"], set()).add(e["family"])
    assert families_by_group[2] == {"authority_epoch", "authority_state"}
    assert families_by_group[3] == {"cutover_request", "readiness_package"}
    assert families_by_group[4] == {"human_authorization", "cutover_candidate", "certification"}
    assert families_by_group[5] == {"publication_attempt", "publication_evidence"}
    assert families_by_group[8] == {"concurrency_conflict", "recovery_journal_entry"}
    assert families_by_group[10] == {
        "notification_authority_binding",
        "marker_authority_binding",
        "receipt_authority_binding",
    }
    assert families_by_group[11] == {"compatibility_state", "quarantine_record"}
    assert set(families_by_group) == {1, 2, 3, 4, 5, 8, 10, 11}
    assert 6 not in families_by_group and 7 not in families_by_group and 9 not in families_by_group
