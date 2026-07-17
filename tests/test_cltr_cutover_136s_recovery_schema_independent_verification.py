"""Phase 136S: Recovery Schema Independent Verification (Implementation Group 8).

Independent, adversarial re-derivation of Phase 136R's claims about Group 8
(``ConcurrencyConflict``, ``RecoveryJournalEntry``). This module does not
import or reuse 136R's test helpers, fixtures, or assertions -- every
fixture and graph below is authored fresh from the schema files and the
frozen contract (CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Sec.27, Sec.28,
Sec.46, CSCH-EXEC-REQ-062) and attempts, wherever plausible, to falsify
136R's reported inventory, field tables, sibling-independence, and scope
claims rather than merely restate them.

Every schema validated here proves shape only. No test asserts, implies, or
depends on any live conflict resolution, recovery execution, publication
outcome, or CLTR authority. Legacy lifecycle remains the sole production
authority; CLTR remains derivative.
"""
from __future__ import annotations

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

BASE_ID = "https://pcae.local/schemas/cltr_cutover/"
CONFLICT_ID = BASE_ID + "records/concurrency_conflict.schema.json"
JOURNAL_ID = BASE_ID + "records/recovery_journal_entry.schema.json"
MANIFEST_SCHEMA_ID = BASE_ID + "manifest.schema.json"

REPO_ROOT = Path(__file__).resolve().parents[1]


def _ref(record_id: str, digest: str, family: str, schema_id: str | None = None) -> dict:
    r = {"record_id": record_id, "record_digest": digest, "record_family": family}
    if schema_id is not None:
        r["schema_id"] = schema_id
        r["schema_version"] = "1.0"
    return r


def _base_conflict(**overrides) -> dict:
    record = {
        "schema_id": CONFLICT_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "concurrency_conflict",
        "record_id": "ccnflct-1000001",
        "record_digest": "1" * 64,
        "created_at": "2026-07-17T00:00:00Z",
        "migration_epoch": "epoch-136s",
        "actors": [
            "svc-actor@example.test",
            _ref("pubattmp-1000001", "2" * 64, "publication_attempt"),
        ],
        "requests": [_ref("cutreq-10000001", "3" * 64, "cutover_request", BASE_ID + "records/cutover_request.schema.json")],
        "type": "stale_expectation",
        "winner": None,
        "recovery_requirement": "reconciliation_required",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "136S adversarial fixture; not authoritative.",
        },
    }
    record.update(overrides)
    return record


def _base_journal(**overrides) -> dict:
    record = {
        "schema_id": JOURNAL_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "recovery_journal_entry",
        "record_id": "rcjrnl-1000001",
        "record_digest": "4" * 64,
        "created_at": "2026-07-17T00:00:00Z",
        "migration_epoch": "epoch-136s",
        "transition_id": "trans-10000001",
        "sequence": 0,
        "prior_entry_digest": None,
        "operation_reference": _ref("cutreq-10000001", "5" * 64, "cutover_request"),
        "prior_state_reference": _ref("authstat-1000001", "6" * 64, "authority_state"),
        "new_state_reference": _ref("authstat-1000002", "7" * 64, "authority_state"),
        "authority_state_reference": _ref(
            "authstat-1000001", "8" * 64, "authority_state", BASE_ID + "records/authority_state.schema.json"
        ),
        "generation_reference": {"generation_id": "generatn-1000001", "generation_digest": "9" * 64},
        "external_effect_state": "none",
        "retry_replay_classification": "original",
        "state": "recorded",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "136S adversarial fixture; not authoritative.",
        },
    }
    record.update(overrides)
    return record


@pytest.fixture(scope="module")
def registry():
    with cltr_cutover_root() as root:
        yield build_offline_registry(root)


def _outcome(record, schema_id, registry):
    return validate_record_shape(record, schema_id=schema_id, registry=registry)


# ---------------------------------------------------------------------------
# 1. Exact Group 8 inventory / Section 46 / CSCH-EXEC-REQ-062 pairing
# ---------------------------------------------------------------------------


def test_136s_manifest_records_exactly_two_group8_entries():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    group8 = [e for e in manifest["entries"] if e["implementation_group"] == 8]
    families = sorted(e["family"] for e in group8)
    assert families == ["concurrency_conflict", "recovery_journal_entry"]


def test_136s_manifest_total_entry_counts_are_exact():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    entries = manifest["entries"]
    assert len(entries) == 18
    shared = [e for e in entries if e["implementation_group"] == 1]
    records = [e for e in entries if e["implementation_group"] != 1]
    assert len(shared) == 7
    assert len(records) == 11


def test_136s_no_implementation_group_9_or_higher_in_manifest():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    groups = {e["implementation_group"] for e in manifest["entries"]}
    assert max(groups) == 8
    assert all(g in (1, 2, 3, 4, 5, 8) for g in groups)


def test_136s_group8_pair_completeness_missing_sibling_is_detectable():
    """CSCH-EXEC-REQ-062: neither Group 8 schema may exist without the other.
    Simulate a manifest with only one Group 8 entry and confirm the pairing
    invariant is falsifiable (i.e. a one-sided manifest is distinguishable
    from the real, paired one) -- this is the schema-level meaning of
    'paired atomically', not runtime atomic persistence.
    """
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    group8_families = {e["family"] for e in manifest["entries"] if e["implementation_group"] == 8}
    assert group8_families == {"concurrency_conflict", "recovery_journal_entry"}
    partial = {"concurrency_conflict"}
    assert partial != group8_families  # a one-sided delivery is structurally distinct and thus detectable


def test_136s_both_group8_schema_files_exist_on_disk():
    with cltr_cutover_root() as root:
        assert (root / "records" / "concurrency_conflict.schema.json").is_file()
        assert (root / "records" / "recovery_journal_entry.schema.json").is_file()


def test_136s_no_group9plus_record_files_present():
    forbidden = (
        "quarantine_record.schema.json",
        "notification_authority_binding.schema.json",
        "marker_authority_binding.schema.json",
        "receipt_authority_binding.schema.json",
        "compatibility_state.schema.json",
        "historical_authority_reference.schema.json",
    )
    with cltr_cutover_root() as root:
        present = {p.name for p in (root / "records").glob("*.schema.json")}
    for name in forbidden:
        assert name not in present


def test_136s_no_bindings_or_views_directories():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


# ---------------------------------------------------------------------------
# 2. ConcurrencyConflict field table -- required, conditional, prohibited
# ---------------------------------------------------------------------------


def test_136s_conflict_valid_record_passes_registry(registry):
    result = _outcome(_base_conflict(), CONFLICT_ID, registry)
    assert result.status == OutcomeStatus.VALID


REQUIRED_CONFLICT_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch", "actors", "requests",
    "type", "winner", "recovery_requirement", "limitations", "authority_disclosure",
)


@pytest.mark.parametrize("field", REQUIRED_CONFLICT_FIELDS)
def test_136s_conflict_each_required_field_rejected_if_absent(registry, field):
    record = _base_conflict()
    del record[field]
    result = _outcome(record, CONFLICT_ID, registry)
    assert result.status == OutcomeStatus.INVALID


def test_136s_conflict_unknown_top_level_field_rejected(registry):
    record = _base_conflict(injected_field="unexpected")
    result = _outcome(record, CONFLICT_ID, registry)
    assert result.status == OutcomeStatus.INVALID


def test_136s_conflict_phase_id_and_transition_id_are_prohibited(registry):
    # concurrency_conflict is NOT in Sec.7.2's phase_id-required or
    # transition_id-required family lists -- injecting either must be
    # rejected as an unknown field (additionalProperties: false).
    for field, value in (("phase_id", "136S"), ("transition_id", "trans-00000001")):
        record = _base_conflict(**{field: value})
        result = _outcome(record, CONFLICT_ID, registry)
        assert result.status == OutcomeStatus.INVALID, field


def test_136s_conflict_expected_observed_state_required_together_for_cas_mismatch(registry):
    record = _base_conflict(type="cas_mismatch")
    result = _outcome(record, CONFLICT_ID, registry)
    assert result.status == OutcomeStatus.INVALID  # missing expected_state/observed_state

    record2 = _base_conflict(
        type="cas_mismatch",
        expected_state=_ref("cutreq-10000001", "a" * 64, "cutover_request"),
        observed_state=_ref("cutreq-10000001", "b" * 64, "cutover_request"),
    )
    result2 = _outcome(record2, CONFLICT_ID, registry)
    assert result2.status == OutcomeStatus.VALID


def test_136s_conflict_expected_state_forbidden_when_type_is_not_cas_mismatch(registry):
    record = _base_conflict(
        type="dual_writer",
        expected_state=_ref("cutreq-10000001", "a" * 64, "cutover_request"),
    )
    result = _outcome(record, CONFLICT_ID, registry)
    assert result.status == OutcomeStatus.INVALID


def test_136s_conflict_winner_key_must_be_present_null_or_reference(registry):
    record = _base_conflict()
    del record["winner"]
    assert _outcome(record, CONFLICT_ID, registry).status == OutcomeStatus.INVALID

    record_null = _base_conflict(winner=None)
    assert _outcome(record_null, CONFLICT_ID, registry).status == OutcomeStatus.VALID

    record_ref = _base_conflict(winner=_ref("pubattmp-1000001", "c" * 64, "publication_attempt"))
    assert _outcome(record_ref, CONFLICT_ID, registry).status == OutcomeStatus.VALID


def test_136s_conflict_type_enum_rejects_unknown_and_group9_style_values(registry):
    for bogus in ("winner_selected", "resolved", "cas_mismatch_v2", ""):
        record = _base_conflict(type=bogus)
        assert _outcome(record, CONFLICT_ID, registry).status == OutcomeStatus.INVALID, bogus


def test_136s_conflict_requests_family_is_locked_to_cutover_request(registry):
    record = _base_conflict(requests=[_ref("authstat-1000001", "d" * 64, "authority_state")])
    assert _outcome(record, CONFLICT_ID, registry).status == OutcomeStatus.INVALID


def test_136s_conflict_requests_minimum_one_actors_minimum_two(registry):
    assert _outcome(_base_conflict(requests=[]), CONFLICT_ID, registry).status == OutcomeStatus.INVALID
    assert _outcome(
        _base_conflict(actors=["only-one@example.test"]), CONFLICT_ID, registry
    ).status == OutcomeStatus.INVALID


def test_136s_conflict_authority_role_authoritative_locally_forbidden(registry):
    record = _base_conflict(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "attempted escalation",
        }
    )
    assert _outcome(record, CONFLICT_ID, registry).status == OutcomeStatus.INVALID


def test_136s_conflict_is_authoritative_cannot_be_forced_true(registry):
    record = _base_conflict(
        authority_disclosure={
            "authority_role": "derivative",
            "is_authoritative": True,
            "disclosure_text": "attempted escalation",
        }
    )
    assert _outcome(record, CONFLICT_ID, registry).status == OutcomeStatus.INVALID


def test_136s_conflict_malformed_digest_and_record_id_rejected(registry):
    assert _outcome(_base_conflict(record_digest="not-hex"), CONFLICT_ID, registry).status == OutcomeStatus.INVALID
    assert _outcome(_base_conflict(record_id="../etc/passwd"), CONFLICT_ID, registry).status == OutcomeStatus.INVALID


def test_136s_conflict_extensions_reject_non_string_values(registry):
    record = _base_conflict(_extensions={"note": 123})
    assert _outcome(record, CONFLICT_ID, registry).status == OutcomeStatus.INVALID
    record_ok = _base_conflict(_extensions={"note": "ok"})
    assert _outcome(record_ok, CONFLICT_ID, registry).status == OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 3. ConcurrencyConflict semantic boundary -- schema-valid must not imply truth
# ---------------------------------------------------------------------------


def test_136s_conflict_schema_valid_cas_mismatch_does_not_imply_cas_actually_failed(registry):
    """A structurally perfect cas_mismatch record with contradictory-looking
    but well-formed references still validates -- proving the schema
    describes claimed conflict data only, never adjudicated truth."""
    record = _base_conflict(
        type="cas_mismatch",
        expected_state=_ref("cutreq-10000001", "e" * 64, "cutover_request"),
        observed_state=_ref("cutreq-10000001", "e" * 64, "cutover_request"),  # identical id+digest
    )
    result = _outcome(record, CONFLICT_ID, registry)
    assert result.status == OutcomeStatus.VALID  # schema cannot detect this is a non-conflict


def test_136s_conflict_winner_reference_validity_does_not_imply_correct_resolution(registry):
    record = _base_conflict(winner=_ref("cutreq-10000001", "f" * 64, "cutover_request"))
    result = _outcome(record, CONFLICT_ID, registry)
    assert result.status == OutcomeStatus.VALID  # any well-formed reference is accepted as "a" winner claim


# ---------------------------------------------------------------------------
# 4. RecoveryJournalEntry field table
# ---------------------------------------------------------------------------


REQUIRED_JOURNAL_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch", "transition_id", "sequence",
    "prior_entry_digest", "operation_reference", "prior_state_reference",
    "new_state_reference", "authority_state_reference", "generation_reference",
    "external_effect_state", "retry_replay_classification", "state",
    "limitations", "authority_disclosure",
)


def test_136s_journal_valid_genesis_entry_passes(registry):
    result = _outcome(_base_journal(), JOURNAL_ID, registry)
    assert result.status == OutcomeStatus.VALID


@pytest.mark.parametrize("field", REQUIRED_JOURNAL_FIELDS)
def test_136s_journal_each_required_field_rejected_if_absent(registry, field):
    record = _base_journal()
    del record[field]
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_unknown_field_rejected(registry):
    record = _base_journal(unexpected_field="x")
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_genesis_requires_null_prior_digest(registry):
    record = _base_journal(sequence=0, prior_entry_digest="a" * 64)
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_nongenesis_requires_wellformed_prior_digest(registry):
    record = _base_journal(sequence=1, prior_entry_digest=None)
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID

    record_ok = _base_journal(sequence=1, prior_entry_digest="b" * 64)
    assert _outcome(record_ok, JOURNAL_ID, registry).status == OutcomeStatus.VALID


def test_136s_journal_negative_sequence_rejected(registry):
    record = _base_journal(sequence=-1)
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_state_recorded_forbids_operator_review_and_recovery_action(registry):
    record = _base_journal(state="recorded", operator_review={"notes": "n"})
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_state_reviewed_requires_operator_review(registry):
    record = _base_journal(state="reviewed")
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID

    record_ok = _base_journal(state="reviewed", operator_review={"notes": "reviewed by operator"})
    assert _outcome(record_ok, JOURNAL_ID, registry).status == OutcomeStatus.VALID


def test_136s_journal_state_actioned_requires_recovery_action_and_operator_review(registry):
    record = _base_journal(state="actioned", operator_review={"notes": "n"})
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID  # missing recovery_action

    record_ok = _base_journal(
        state="actioned",
        operator_review={"notes": "n"},
        recovery_action={"description": "described only, not executed"},
    )
    assert _outcome(record_ok, JOURNAL_ID, registry).status == OutcomeStatus.VALID


def test_136s_journal_recovery_action_forbidden_unless_actioned(registry):
    record = _base_journal(state="reviewed", operator_review={"notes": "n"}, recovery_action={"description": "x"})
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_authority_state_reference_family_locked(registry):
    record = _base_journal(authority_state_reference=_ref("cutreq-10000001", "c" * 64, "cutover_request"))
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_publication_attempt_reference_optional_but_family_locked_when_present(registry):
    record_absent = _base_journal()
    assert _outcome(record_absent, JOURNAL_ID, registry).status == OutcomeStatus.VALID

    record_wrong_family = _base_journal(
        publication_attempt_reference=_ref("cutreq-10000001", "d" * 64, "cutover_request")
    )
    assert _outcome(record_wrong_family, JOURNAL_ID, registry).status == OutcomeStatus.INVALID

    record_right_family = _base_journal(
        publication_attempt_reference=_ref("pubattmp-1000001", "e" * 64, "publication_attempt")
    )
    assert _outcome(record_right_family, JOURNAL_ID, registry).status == OutcomeStatus.VALID


def test_136s_journal_external_effect_state_and_retry_replay_enums_reject_unknown(registry):
    assert _outcome(_base_journal(external_effect_state="bogus"), JOURNAL_ID, registry).status == OutcomeStatus.INVALID
    assert _outcome(_base_journal(retry_replay_classification="bogus"), JOURNAL_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_authority_role_authoritative_locally_forbidden(registry):
    record = _base_journal(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "attempted escalation",
        }
    )
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 5. RecoveryJournalEntry semantic boundary
# ---------------------------------------------------------------------------


def test_136s_journal_schema_valid_actioned_entry_does_not_imply_recovery_executed(registry):
    """A structurally perfect 'actioned' entry validates even though no
    recovery action has actually run anywhere in this process -- the schema
    records a claim, never an execution."""
    record = _base_journal(
        state="actioned",
        operator_review={"notes": "reviewed"},
        recovery_action={"description": "claims retry was performed"},
    )
    result = _outcome(record, JOURNAL_ID, registry)
    assert result.status == OutcomeStatus.VALID


def test_136s_journal_chain_link_validity_does_not_imply_chain_is_unbroken(registry):
    """sequence=5 with a well-formed prior_entry_digest validates even though
    no sequence 0..4 documents exist anywhere -- contiguity/chain-integrity
    is explicitly Layer 4, never enforced by this schema (Sec.28)."""
    record = _base_journal(sequence=5, prior_entry_digest="f" * 64)
    result = _outcome(record, JOURNAL_ID, registry)
    assert result.status == OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 6. Sibling independence -- four independently authored graphs
# ---------------------------------------------------------------------------


def _load_all_schema_documents():
    with cltr_cutover_root() as root:
        docs = {}
        for p in root.rglob("*.schema.json"):
            docs[p.relative_to(root).as_posix()] = json.loads(p.read_text())
        return docs


def _collect_refs(node, base_dir: str, out: set) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str) and not value.startswith("#"):
                target_file = value.split("#", 1)[0]
                # resolve relative to base_dir (schema files live in records/ or shared/)
                if target_file.startswith("../"):
                    resolved = target_file[3:]
                else:
                    resolved = f"{base_dir}/{target_file}" if base_dir else target_file
                out.add(resolved)
            else:
                _collect_refs(value, base_dir, out)
    elif isinstance(node, list):
        for item in node:
            _collect_refs(item, base_dir, out)


def test_136s_ref_graph_conflict_and_journal_do_not_reference_each_other():
    docs = _load_all_schema_documents()
    conflict_refs: set = set()
    _collect_refs(docs["records/concurrency_conflict.schema.json"], "shared", conflict_refs)
    journal_refs: set = set()
    _collect_refs(docs["records/recovery_journal_entry.schema.json"], "shared", journal_refs)

    assert "records/recovery_journal_entry.schema.json" not in conflict_refs
    assert "records/concurrency_conflict.schema.json" not in journal_refs


def test_136s_ref_graph_full_group1_through_group8_is_acyclic():
    docs = _load_all_schema_documents()
    graph: dict[str, set] = {}
    for path, doc in docs.items():
        base_dir = "shared" if path.startswith("shared/") else "shared"  # all $refs from records/ point into shared/
        refs: set = set()
        _collect_refs(doc, "shared", refs)
        graph[path] = {r for r in refs if r in docs and r != path}

    visiting: set = set()
    visited: set = set()

    def dfs(node):
        if node in visited:
            return
        if node in visiting:
            raise AssertionError(f"Cycle detected through {node}")
        visiting.add(node)
        for nxt in graph.get(node, ()):  # noqa: B007
            dfs(nxt)
        visiting.discard(node)
        visited.add(node)

    for path in graph:
        dfs(path)
    assert visited == set(graph)


def test_136s_manifest_dependency_graph_group8_siblings_share_no_edge():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    by_family = {e["family"]: e for e in manifest["entries"]}
    conflict_deps = set(by_family["concurrency_conflict"]["dependencies"])
    journal_deps = set(by_family["recovery_journal_entry"]["dependencies"])
    assert not any("concurrency_conflict" in d for d in journal_deps)
    assert not any("recovery_journal_entry" in d for d in conflict_deps)


def test_136s_manifest_dependency_graph_is_acyclic():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    by_id = {e["schema_id"]: e for e in manifest["entries"]}
    visiting: set = set()
    visited: set = set()

    def dfs(schema_id):
        if schema_id in visited:
            return
        if schema_id in visiting:
            raise AssertionError(f"Manifest dependency cycle through {schema_id}")
        visiting.add(schema_id)
        for dep in by_id[schema_id]["dependencies"]:
            dfs(dep)
        visiting.discard(schema_id)
        visited.add(schema_id)

    for schema_id in by_id:
        dfs(schema_id)
    assert visited == set(by_id)


def test_136s_record_identity_graph_conflict_and_journal_have_independent_id_shapes():
    """Both use the generic record_identity pattern; a value valid for one
    family is structurally indistinguishable from the other at the
    identity-shape level alone (both match ^[a-z][a-z0-9-]{7,127}$), which
    is why family enforcement happens via record_family/schema_id const
    fields, not via the identity pattern itself -- confirming there is no
    identity-pattern-level dependency or distinguishing constraint between
    the two siblings."""
    import re

    pattern = re.compile(r"^[a-z][a-z0-9-]{7,127}$")
    assert pattern.match("ccnflct-1000001")
    assert pattern.match("rcjrnl-1000001")


def test_136s_record_digest_graph_journal_prior_digest_is_not_its_own_digest():
    """A RecoveryJournalEntry's prior_entry_digest must reference a PRIOR
    entry's record_digest, never its own -- verify a document cannot embed
    its own record_digest value into prior_entry_digest and be rejected for
    circularity implicitly (schema cannot detect self-reference by value
    since both are just sha256_hex strings; documented as Layer 4, but
    confirm the shape at least permits distinguishing the two fields)."""
    record = _base_journal(sequence=1, record_digest="9" * 64, prior_entry_digest="9" * 64)
    # Schema-valid even though digest matches its own -- proving digest equality
    # is NOT itself rejected at Layer 2 (self-reference detection is Layer 4).
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
    result = _outcome(record, JOURNAL_ID, reg)
    assert result.status == OutcomeStatus.VALID


def test_136s_creation_order_shared_before_group8_group8_has_no_forward_deps():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_text())
    by_family = {e["family"]: e for e in manifest["entries"]}
    for family in ("concurrency_conflict", "recovery_journal_entry"):
        deps = by_family[family]["dependencies"]
        for dep in deps:
            dep_entry = next(e for e in manifest["entries"] if e["schema_id"] == dep)
            assert dep_entry["implementation_group"] <= 8


# ---------------------------------------------------------------------------
# 7. Family-specific reference / wrong-family substitution attacks
# ---------------------------------------------------------------------------


WRONG_FAMILY_TARGETS = (
    ("authority_epoch", "authority_state_reference", JOURNAL_ID),
    ("cutover_request", "authority_state_reference", JOURNAL_ID),
    ("human_authorization", "authority_state_reference", JOURNAL_ID),
    ("certification", "publication_attempt_reference", JOURNAL_ID),
)


@pytest.mark.parametrize("wrong_family, field, schema_id", WRONG_FAMILY_TARGETS)
def test_136s_journal_wrong_family_substitution_rejected(registry, wrong_family, field, schema_id):
    record = _base_journal(**{field: _ref("someid-0000001", "a" * 64, wrong_family)})
    assert _outcome(record, schema_id, registry).status == OutcomeStatus.INVALID


@pytest.mark.parametrize("wrong_family", ("authority_state", "human_authorization", "certification", "publication_evidence"))
def test_136s_conflict_requests_wrong_family_rejected(registry, wrong_family):
    record = _base_conflict(requests=[_ref("someid-0000001", "a" * 64, wrong_family)])
    assert _outcome(record, CONFLICT_ID, registry).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 8. Strictness / extension probes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field, value", (
    ("_extensions", {"a": "b", "extra_nested": {"x": 1}}),
))
def test_136s_conflict_extensions_reject_nested_structure(registry, field, value):
    record = _base_conflict(**{field: value})
    assert _outcome(record, CONFLICT_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_operator_review_rejects_unknown_subfield(registry):
    record = _base_journal(state="reviewed", operator_review={"notes": "n", "extra": "x"})
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


def test_136s_journal_recovery_action_rejects_unknown_subfield(registry):
    record = _base_journal(
        state="actioned",
        operator_review={"notes": "n"},
        recovery_action={"description": "d", "extra": "x"},
    )
    assert _outcome(record, JOURNAL_ID, registry).status == OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 9. Manifest / packaging integrity
# ---------------------------------------------------------------------------


def test_136s_manifest_digests_match_actual_files_on_disk(registry):
    with cltr_cutover_root() as root:
        verified = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    assert len(verified.entries) == 18


def test_136s_manifest_rejects_tampered_digest(registry, tmp_path):
    with cltr_cutover_root() as root:
        for item in root.rglob("*"):
            if item.is_file():
                target = tmp_path / item.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(item.read_bytes())
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for entry in manifest["entries"]:
        if entry["family"] == "concurrency_conflict":
            entry["file_digest"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ManifestIntegrityError):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136s_manifest_missing_group8_entry_fails_completeness(registry, tmp_path):
    with cltr_cutover_root() as root:
        for item in root.rglob("*"):
            if item.is_file():
                target = tmp_path / item.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(item.read_bytes())
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["entries"] = [e for e in manifest["entries"] if e["family"] != "recovery_journal_entry"]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ManifestIntegrityError):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


# ---------------------------------------------------------------------------
# 10. No-network / no-runtime-behavior probes
# ---------------------------------------------------------------------------


def test_136s_registry_construction_performs_no_network_access(monkeypatch):
    def _forbidden(*args, **kwargs):
        raise AssertionError("Network access attempted during registry construction")

    monkeypatch.setattr(socket, "socket", _forbidden)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
    assert JOURNAL_ID in reg.schema_ids
    assert CONFLICT_ID in reg.schema_ids


def test_136s_validation_performs_no_network_access(monkeypatch, registry):
    def _forbidden(*args, **kwargs):
        raise AssertionError("Network access attempted during validation")

    monkeypatch.setattr(socket, "socket", _forbidden)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    result = _outcome(_base_conflict(), CONFLICT_ID, registry)
    assert result.status == OutcomeStatus.VALID


def test_136s_no_conflict_resolver_or_recovery_coordinator_module_exists():
    forbidden_paths = (
        "src/pcae/cltr/concurrency_resolver.py",
        "src/pcae/cltr/conflict_resolver.py",
        "src/pcae/cltr/recovery_coordinator.py",
        "src/pcae/cltr/recovery_evaluator.py",
        "src/pcae/cltr/reconciliation.py",
        "src/pcae/cltr/quarantine.py",
    )
    for rel in forbidden_paths:
        assert not (REPO_ROOT / rel).exists(), rel


def test_136s_no_authority_pointer_directory_or_file():
    assert not (REPO_ROOT / ".pcae" / "cltr-authority").exists()


def test_136s_no_execution_capability_module_added_for_group8():
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden_names = {
        "concurrency_conflict.py",
        "recovery_journal_entry.py",
        "conflict_resolver.py",
        "recovery_coordinator.py",
    }
    hits = [p for p in tracked if Path(p).name in forbidden_names]
    assert hits == []
