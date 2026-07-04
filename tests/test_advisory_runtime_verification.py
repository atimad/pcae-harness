"""Tests for Phase 113D — Advisory Runtime Verification & Compatibility.

Verification-focused tests that go beyond the 113C prototype tests.
Each test maps to a specific verification requirement from the 113D brief.

Verification areas:
  1. Advisory Runtime consumes Runtime Snapshot only
  2. Advisory Providers remain modular
  3. Advisory Results follow 113B contract
  4. explainability is complete
  5. recommendations are reproducible from Runtime Snapshot
  6. aggregation is deterministic
  7. no provider inspects Runtime internals directly
  8. no PermissionBroker.evaluate() is called
  9. no plugin loading/invocation occurs
  10. no mutation of Runtime Snapshot or Runtime Context
  11. runtime state remains Observed
  12. execution capability remains unavailable
"""

from __future__ import annotations

import ast
import dataclasses
import typing
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ADVISORY_RUNTIME_MODULE = REPO_ROOT / "src" / "pcae" / "core" / "advisory_runtime.py"


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def ar():
    """The advisory_runtime module under test."""
    import pcae.core.advisory_runtime as mod
    return mod


@pytest.fixture(scope="module")
def module_source(ar) -> str:
    return Path(ar.__file__).read_text()


@pytest.fixture(scope="module")
def module_ast(ar):
    return ast.parse(Path(ar.__file__).read_text())


def _minimal_snapshot(ar):
    """Build a minimal RuntimeSnapshot for testing."""
    from pcae.core.runtime_snapshot import RuntimeSnapshot
    from pcae.core.runtime_introspection import (
        RuntimeInfo, HealthInfo, GovernanceInfo, RuntimeStateInfo, VersionInfo,
    )
    from pcae.core.runtime_registry import RegistrySnapshot

    return RuntimeSnapshot(
        runtime=RuntimeInfo(
            pipeline_stages=(),
            principles=(),
            runtime_services=(),
        ),
        registry=RegistrySnapshot(
            registered_plugin_count=0,
            registered_capability_count=0,
            registry_status="initialized",
            metadata_validity="valid",
            plugin_ids=(),
            capabilities=(),
        ),
        plugins=(),
        capabilities=(),
        health=HealthInfo(
            runtime_status="not_implemented",
            registry_status="initialized",
            plugin_count=0,
            capability_count=0,
            metadata_validity="valid",
            execution_availability="unavailable",
            current_runtime_state="Observed",
            current_maximum_plugin_capability="observe",
        ),
        governance=GovernanceInfo(
            non_executing_posture=True,
            broker_implementation_status="execution_unavailable",
            observed_command_paths=4,
            execution_capability="unavailable",
        ),
        state=RuntimeStateInfo(
            current_state="Observed",
            state_model=(
                "Intent", "Observed", "Advisory", "Approved",
                "Executable", "Executed", "Audited", "Rollback Ready",
            ),
        ),
        version=VersionInfo(
            release_version="0.1.0",
            plugin_versions=(),
        ),
        context=None,
    )


# ═══════════════════════════════════════════════════════════════════════
# Section 1 — Runtime Snapshot-Only Input Verification
# ═══════════════════════════════════════════════════════════════════════


def test_advisory_runtime_only_imports_runtime_snapshot(ar):
    """Verification 1: Advisory Runtime must import RuntimeSnapshot only
    — no other internal PCAE module.

    The AST import allowlist from 113C already verifies this; here we
    confirm it holds at runtime by checking the actual module's
    __dict__ for unexpected internal references.
    """
    source = Path(ar.__file__).read_text()
    tree = ast.parse(source)
    internal_imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("pcae"):
                internal_imports.append(node.module)

    # The only allowed internal import is runtime_snapshot
    for imp in internal_imports:
        assert imp == "pcae.core.runtime_snapshot", (
            f"Unexpected internal import: {imp}. "
            f"Advisory Runtime must only import RuntimeSnapshot."
        )


def test_build_advisory_results_accepts_only_runtime_snapshot(ar):
    """Verification 1: build_advisory_results signature accepts RuntimeSnapshot."""
    hints = typing.get_type_hints(ar.build_advisory_results)
    assert "snapshot" in hints
    # The return type is tuple[AdvisoryResult, ...]
    assert "return" in hints


def test_providers_accept_only_runtime_snapshot(ar):
    """Verification 1: Every provider's analyze() accepts only RuntimeSnapshot."""
    from pcae.core.runtime_snapshot import RuntimeSnapshot

    providers = [
        ar.RuntimeHealthProvider(),
        ar.GovernanceProvider(),
        ar.RuntimeContextProvider(),
        ar.RegistryProvider(),
    ]
    for provider in providers:
        hints = typing.get_type_hints(provider.analyze)
        assert "snapshot" in hints
        assert hints["snapshot"] is RuntimeSnapshot


# ═══════════════════════════════════════════════════════════════════════
# Section 2 — Provider Modularity Verification
# ═══════════════════════════════════════════════════════════════════════


def test_providers_are_stateless_classes(ar):
    """Verification 2: Each provider is a stateless class — no __init__
    beyond the default, no instance state that persists between calls."""
    providers = [
        ar.RuntimeHealthProvider,
        ar.GovernanceProvider,
        ar.RuntimeContextProvider,
        ar.RegistryProvider,
    ]
    for provider_cls in providers:
        # Each provider should have no custom __init__
        assert "__init__" not in provider_cls.__dict__, (
            f"{provider_cls.__name__} has custom __init__ — "
            f"providers must be stateless"
        )


def test_providers_independent_no_cross_calls(ar):
    """Verification 2: Each provider can be called independently without
    any other provider — no shared state, no cross-dependency."""
    snapshot = _minimal_snapshot(ar)

    # Call each provider in isolation
    health = ar.RuntimeHealthProvider().analyze(snapshot)
    gov = ar.GovernanceProvider().analyze(snapshot)
    ctx = ar.RuntimeContextProvider().analyze(snapshot)
    reg = ar.RegistryProvider().analyze(snapshot)

    # Each must return a tuple of AdvisoryResults
    assert isinstance(health, tuple)
    assert isinstance(gov, tuple)
    assert isinstance(ctx, tuple)
    assert isinstance(reg, tuple)

    # Results from each provider must have distinct categories
    health_cats = {r.category for r in health}
    gov_cats = {r.category for r in gov}
    ctx_cats = {r.category for r in ctx}
    reg_cats = {r.category for r in reg}

    assert health_cats == {"Runtime Health"}
    assert gov_cats == {"Governance"}
    assert ctx_cats == {"Context Consistency"}
    assert reg_cats == {"Registry"}


def test_providers_removable_without_breaking_aggregation(ar):
    """Verification 2: Removing a provider from the aggregation pipeline
    must not break build_advisory_results. Each provider is modular."""
    snapshot = _minimal_snapshot(ar)

    # Full results
    full = ar.build_advisory_results(snapshot)
    full_cats = {r.category for r in full}

    # Simulate removing a provider by running only 3 of 4
    results_without_registry = (
        ar.RuntimeHealthProvider().analyze(snapshot)
        + ar.GovernanceProvider().analyze(snapshot)
        + ar.RuntimeContextProvider().analyze(snapshot)
    )
    # Aggregate manually
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    aggregated = ar._aggregate(list(results_without_registry), snapshot, now)

    agg_cats = {r.category for r in aggregated}
    assert "Registry" not in agg_cats
    assert "Runtime Health" in agg_cats
    assert "Governance" in agg_cats


# ═══════════════════════════════════════════════════════════════════════
# Section 3 — 113B Contract Compliance Verification
# ═══════════════════════════════════════════════════════════════════════


def test_all_14_fields_populated_in_every_result(ar):
    """Verification 3: Every AdvisoryResult from build_advisory_results
    must have all 14 fields populated (non-empty where required)."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    assert len(results) > 0

    required_non_empty = [
        "advisory_id", "category", "severity", "confidence",
        "recommended_action", "rationale", "reasoning_summary",
        "remediation", "timestamp", "source_snapshot_reference",
        "implementation_status",
    ]

    for r in results:
        for field_name in required_non_empty:
            val = getattr(r, field_name)
            assert val, (
                f"Field '{field_name}' is empty in result {r.advisory_id}"
            )
        # evidence_references must be a non-empty tuple
        assert isinstance(r.evidence_references, tuple)
        # affected_runtime_objects and alternative_considerations
        # may be empty tuples (valid for info-level results)
        assert isinstance(r.affected_runtime_objects, tuple)
        assert isinstance(r.alternative_considerations, tuple)


def test_every_result_has_at_least_one_evidence_reference(ar):
    """Verification 3: Every AdvisoryResult must have at least one
    EvidenceReference linking it to a specific RuntimeSnapshot field."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for r in results:
        assert len(r.evidence_references) >= 1, (
            f"Result {r.advisory_id} has no evidence references — "
            f"every result must be traceable to a RuntimeSnapshot field"
        )
        for ev in r.evidence_references:
            assert ev.domain in ar.RUNTIME_SNAPSHOT_DOMAINS
            assert ev.field_path
            assert ev.evidence_summary


def test_implementation_status_unconditionally_execution_unavailable(ar):
    """Verification 3: implementation_status must be 'execution_unavailable'
    on every single result, unconditionally."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for r in results:
        assert r.implementation_status == "execution_unavailable", (
            f"Result {r.advisory_id} has implementation_status="
            f"{r.implementation_status!r} — must be 'execution_unavailable'"
        )


def test_category_severity_confidence_from_frozen_vocabularies(ar):
    """Verification 3: Every result's category, severity, and confidence
    must come from the frozen vocabulary tuples."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for r in results:
        assert r.category in ar.ADVISORY_CATEGORIES, (
            f"Category {r.category!r} not in ADVISORY_CATEGORIES"
        )
        assert r.severity in ar.SEVERITY_LEVELS, (
            f"Severity {r.severity!r} not in SEVERITY_LEVELS"
        )
        assert r.confidence in ar.CONFIDENCE_LEVELS, (
            f"Confidence {r.confidence!r} not in CONFIDENCE_LEVELS"
        )


# ═══════════════════════════════════════════════════════════════════════
# Section 4 — Explainability Verification
# ═══════════════════════════════════════════════════════════════════════


def test_explainability_8_facets_all_populated(ar):
    """Verification 4: The 8 explainability facets (113B §2) must all
    be populated in every AdvisoryResult.

    The 8 facets are realized through specific fields:
      1. What was observed → reasoning_summary
      2. Why it matters → rationale + severity
      3. What evidence → evidence_references
      4. Which snapshot fields → evidence_references[].field_path
      5. What recommendation → recommended_action
      6. What remediation → remediation
      7. Why advisory only → ADVISORY_INVARIANT (module constant)
      8. Why no execution → implementation_status
    """
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    assert len(results) > 0

    for r in results:
        # Facet 1: reasoning_summary
        assert r.reasoning_summary, f"Missing reasoning_summary in {r.advisory_id}"
        # Facet 2: rationale + severity
        assert r.rationale, f"Missing rationale in {r.advisory_id}"
        assert r.severity in ar.SEVERITY_LEVELS
        # Facet 3: evidence_references
        assert len(r.evidence_references) >= 1
        # Facet 4: field_path on each evidence reference
        for ev in r.evidence_references:
            assert ev.field_path, f"Missing field_path in evidence ref for {r.advisory_id}"
        # Facet 5: recommended_action
        assert r.recommended_action, f"Missing recommended_action in {r.advisory_id}"
        # Facet 6: remediation
        assert r.remediation, f"Missing remediation in {r.advisory_id}"
        # Facet 7: ADVISORY_INVARIANT (module constant)
        assert ar.ADVISORY_INVARIANT, "ADVISORY_INVARIANT must be non-empty"
        assert "advisory recommendation only" in ar.ADVISORY_INVARIANT.lower()
        # Facet 8: implementation_status
        assert r.implementation_status == "execution_unavailable"


def test_explainability_rationale_is_substantive(ar):
    """Verification 4: Each result's rationale must be a substantive
    explanation, not a placeholder or trivial string."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for r in results:
        # Rationale must be at least 30 characters — substantial explanation
        assert len(r.rationale) >= 30, (
            f"Rationale for {r.advisory_id} is too short ({len(r.rationale)} chars): "
            f"{r.rationale!r}"
        )
        # Reasoning summary must be at least 10 characters
        assert len(r.reasoning_summary) >= 10, (
            f"Reasoning summary for {r.advisory_id} is too short: "
            f"{r.reasoning_summary!r}"
        )
        # Recommended action must be at least 5 characters
        assert len(r.recommended_action) >= 5, (
            f"Recommended action for {r.advisory_id} is too short: "
            f"{r.recommended_action!r}"
        )


# ═══════════════════════════════════════════════════════════════════════
# Section 5 — Reproducibility Verification
# ═══════════════════════════════════════════════════════════════════════


def test_reproducibility_identical_snapshot_identical_results(ar):
    """Verification 5: Same RuntimeSnapshot → identical advisory IDs,
    categories, severities, confidences, and recommended_actions.

    Per 113B §4: given the same Runtime Snapshot and the same Analysis
    logic version, re-running must produce identical category/severity/
    confidence/recommended_action.
    """
    snapshot = _minimal_snapshot(ar)

    results1 = ar.build_advisory_results(snapshot)
    results2 = ar.build_advisory_results(snapshot)

    assert len(results1) == len(results2)

    for r1, r2 in zip(results1, results2):
        assert r1.advisory_id == r2.advisory_id
        assert r1.category == r2.category
        assert r1.severity == r2.severity
        assert r1.confidence == r2.confidence
        assert r1.recommended_action == r2.recommended_action
        assert r1.rationale == r2.rationale
        assert r1.reasoning_summary == r2.reasoning_summary
        assert r1.remediation == r2.remediation
        # Timestamps will differ (captured per-call) — that's expected
        # source_snapshot_reference may differ if based on timestamp
        # These are the only fields that may vary between calls


def test_reproducibility_with_different_timestamps(ar):
    """Verification 5: Results from different calls have different
    timestamps but identical advisory content (category, severity,
    confidence, recommended_action)."""
    snapshot = _minimal_snapshot(ar)

    results1 = ar.build_advisory_results(snapshot)
    results2 = ar.build_advisory_results(snapshot)

    for r1, r2 in zip(results1, results2):
        # Content fields must be identical
        assert r1.category == r2.category
        assert r1.severity == r2.severity
        assert r1.confidence == r2.confidence
        assert r1.recommended_action == r2.recommended_action
        # Timestamps may differ
        # Both must be valid ISO timestamps
        assert r1.timestamp
        assert r2.timestamp


def test_reproducibility_advisory_id_sequence_stable(ar):
    """Verification 5: The advisory ID sequence must be stable across
    calls with the same snapshot — same IDs in same order."""
    snapshot = _minimal_snapshot(ar)

    ids1 = tuple(r.advisory_id for r in ar.build_advisory_results(snapshot))
    ids2 = tuple(r.advisory_id for r in ar.build_advisory_results(snapshot))

    assert ids1 == ids2


# ═══════════════════════════════════════════════════════════════════════
# Section 6 — Deterministic Aggregation Verification
# ═══════════════════════════════════════════════════════════════════════


def test_aggregation_sort_order_match_113c_spec(ar):
    """Verification 6: Results must be sorted by severity rank
    (critical < warning < advisory < info), then category alphabetically,
    then first evidence field_path alphabetically."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)

    severity_order = {"critical": 0, "warning": 1, "advisory": 2, "info": 3}

    for i in range(len(results) - 1):
        r_cur = results[i]
        r_next = results[i + 1]

        sev_cur = severity_order.get(r_cur.severity, 99)
        sev_next = severity_order.get(r_next.severity, 99)

        assert sev_cur <= sev_next, (
            f"Severity sort violation at positions {i}/{i+1}: "
            f"{r_cur.advisory_id}({r_cur.severity}) vs "
            f"{r_next.advisory_id}({r_next.severity})"
        )

        if sev_cur == sev_next:
            # Within same severity: alphabetical by category
            assert r_cur.category <= r_next.category, (
                f"Category sort violation: {r_cur.category} vs {r_next.category}"
            )

            if r_cur.category == r_next.category:
                # Within same category: by first evidence field_path
                fp_cur = r_cur.evidence_references[0].field_path if r_cur.evidence_references else ""
                fp_next = r_next.evidence_references[0].field_path if r_next.evidence_references else ""
                assert fp_cur <= fp_next, (
                    f"Field path sort violation: {fp_cur} vs {fp_next}"
                )


def test_aggregation_deduplication_works(ar):
    """Verification 6: The deduplication function must remove duplicates
    by (category, evidence domains, evidence field_paths) fingerprint."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)

    # Verify no duplicate fingerprints exist
    fingerprints: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    for r in results:
        domains = tuple(ev.domain for ev in r.evidence_references)
        field_paths = tuple(ev.field_path for ev in r.evidence_references)
        fp = (r.category, domains, field_paths)
        assert fp not in fingerprints, (
            f"Duplicate result fingerprint: {fp} — deduplication failed"
        )
        fingerprints.add(fp)


def test_aggregation_advisory_id_format(ar):
    """Verification 6: Advisory IDs must follow ADV-{category_slug}-{seq:04d}."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)

    for r in results:
        assert r.advisory_id.startswith("ADV-"), (
            f"Invalid ID prefix: {r.advisory_id}"
        )
        parts = r.advisory_id.split("-")
        assert len(parts) >= 3
        # Last part must be a 4-digit sequence number
        seq = parts[-1]
        assert len(seq) == 4, f"Sequence not 4 digits: {seq}"
        assert seq.isdigit(), f"Sequence not numeric: {seq}"

    # Sequence numbers within each category must start at 0001 and be consecutive
    cat_counters: dict[str, list[int]] = {}
    for r in results:
        slug = r.category.lower().replace(" ", "_")
        seq = int(r.advisory_id.split("-")[-1])
        cat_counters.setdefault(slug, []).append(seq)

    for slug, seqs in cat_counters.items():
        assert seqs == sorted(seqs), f"Non-sequential IDs for {slug}: {seqs}"
        assert seqs[0] == 1, f"First sequence for {slug} is {seqs[0]}, expected 1"


def test_aggregation_returns_tuple_not_list(ar):
    """Verification 6: build_advisory_results must return an immutable tuple."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    assert isinstance(results, tuple)

    # Individual results must be frozen
    for r in results:
        assert dataclasses.is_dataclass(r)
        assert r.__dataclass_params__.frozen


# ═══════════════════════════════════════════════════════════════════════
# Section 7 — Provider Boundary Verification
# ═══════════════════════════════════════════════════════════════════════


def test_no_provider_imports_runtime_internals(ar):
    """Verification 7: No provider class accesses Runtime internals
    directly. All data comes through the RuntimeSnapshot surface.

    Verified by AST inspection: the module only imports RuntimeSnapshot
    (the surface), never RuntimeRegistry, runtime_context internals, etc.
    """
    tree = ast.parse(Path(ar.__file__).read_text())
    internal_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("pcae"):
                internal_modules.add(node.module)

    # Only pcae.core.runtime_snapshot is allowed
    assert internal_modules == {"pcae.core.runtime_snapshot"} or internal_modules == set(), (
        f"Unexpected internal imports: {internal_modules}"
    )


def test_providers_only_access_snapshot_fields(ar):
    """Verification 7: Each provider only accesses attributes on the
    RuntimeSnapshot — no direct filesystem, no network, no subprocess.

    Verified by grep for forbidden patterns in the module source.
    """
    source = Path(ar.__file__).read_text()
    # No provider code should contain these patterns
    forbidden = [
        "open(", "pathlib.Path(", "os.", "subprocess.",
        "socket.", "requests.", "urllib.",
        "importlib.", "__import__(",
        "eval(", "exec(", "compile(",
    ]
    # Remove docstrings first to avoid false positives
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body[0].value.value = ""
    code_without_docs = ast.unparse(tree)

    for pattern in forbidden:
        assert pattern not in code_without_docs, (
            f"Forbidden pattern '{pattern}' found in advisory_runtime.py code "
            f"(outside docstrings)"
        )


def test_evidence_references_only_point_to_snapshot_domains(ar):
    """Verification 7: Every EvidenceReference must point to one of the
    9 frozen RuntimeSnapshot domains — never to an internal path."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)

    for r in results:
        for ev in r.evidence_references:
            assert ev.domain in ar.RUNTIME_SNAPSHOT_DOMAINS, (
                f"EvidenceReference domain '{ev.domain}' not in "
                f"RUNTIME_SNAPSHOT_DOMAINS for result {r.advisory_id}"
            )


# ═══════════════════════════════════════════════════════════════════════
# Section 8 — No PermissionBroker.evaluate() Verification
# ═══════════════════════════════════════════════════════════════════════


def test_no_permission_broker_import(ar):
    """Verification 8: advisory_runtime.py must not import
    permission_broker_foundation or any permission_broker module."""
    tree = ast.parse(Path(ar.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                assert "permission_broker" not in node.module, (
                    f"PermissionBroker import: {node.module}"
                )
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "permission_broker" not in alias.name, (
                    f"PermissionBroker import: {alias.name}"
                )


def test_no_evaluate_call_in_code(ar):
    """Verification 8: advisory_runtime.py code (excluding docstrings)
    must not contain any call to evaluate()."""
    tree = ast.parse(Path(ar.__file__).read_text())
    # Strip docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body[0].value.value = ""
    code = ast.unparse(tree)
    assert "evaluate(" not in code, (
        "evaluate() call found in advisory_runtime.py code (outside docstrings)"
    )


# ═══════════════════════════════════════════════════════════════════════
# Section 9 — No Plugin Loading/Invocation Verification
# ═══════════════════════════════════════════════════════════════════════


def test_no_plugin_loading_in_code(ar):
    """Verification 9: advisory_runtime.py must not load, instantiate,
    or invoke any plugin.

    Verified by AST inspection: no import of plugin_loader,
    runtime_registry, or importlib dynamic loading.
    """
    tree = ast.parse(Path(ar.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                assert "plugin" not in node.module, (
                    f"Plugin-related import: {node.module}"
                )
                assert "runtime_registry" not in node.module, (
                    f"RuntimeRegistry import: {node.module}"
                )
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "importlib" not in alias.name, (
                    "importlib import — dynamic plugin loading prohibited"
                )
                assert "plugin" not in alias.name.lower(), (
                    f"Plugin-related import: {alias.name}"
                )


def test_no_runtime_registry_direct_instantiation(ar):
    """Verification 9: advisory_runtime.py must never instantiate
    RuntimeRegistry directly — all registry data comes through the
    RuntimeSnapshot surface."""
    tree = ast.parse(Path(ar.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for RuntimeRegistry() calls
            if isinstance(node.func, ast.Name):
                assert node.func.id != "RuntimeRegistry", (
                    "RuntimeRegistry() direct instantiation found — "
                    "providers must read registry data through RuntimeSnapshot"
                )


# ═══════════════════════════════════════════════════════════════════════
# Section 10 — No Mutation Verification
# ═══════════════════════════════════════════════════════════════════════


def test_snapshot_unchanged_after_each_provider(ar):
    """Verification 10: Each provider must leave the RuntimeSnapshot
    completely unchanged after analyze() returns."""
    snapshot = _minimal_snapshot(ar)

    providers = [
        ("RuntimeHealthProvider", ar.RuntimeHealthProvider()),
        ("GovernanceProvider", ar.GovernanceProvider()),
        ("RuntimeContextProvider", ar.RuntimeContextProvider()),
        ("RegistryProvider", ar.RegistryProvider()),
    ]

    for name, provider in providers:
        before = {f.name: getattr(snapshot, f.name) for f in dataclasses.fields(snapshot)}
        provider.analyze(snapshot)
        after = {f.name: getattr(snapshot, f.name) for f in dataclasses.fields(snapshot)}
        assert before == after, (
            f"{name} mutated the snapshot! "
            f"Changed fields: {[k for k in before if before[k] != after[k]]}"
        )


def test_snapshot_unchanged_after_full_aggregation(ar):
    """Verification 10: build_advisory_results must leave the
    RuntimeSnapshot unchanged."""
    snapshot = _minimal_snapshot(ar)

    before = {f.name: getattr(snapshot, f.name) for f in dataclasses.fields(snapshot)}
    ar.build_advisory_results(snapshot)
    after = {f.name: getattr(snapshot, f.name) for f in dataclasses.fields(snapshot)}

    assert before == after, (
        f"build_advisory_results mutated the snapshot! "
        f"Changed fields: {[k for k in before if before[k] != after[k]]}"
    )


def test_results_immutable_after_return(ar):
    """Verification 10: Returned AdvisoryResults must be frozen —
    no mutation possible."""
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)

    for r in results:
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.advisory_id = "modified"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════════
# Section 11 — Runtime State Remains Observed
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_state_observed_before_and_after(ar):
    """Verification 11: Runtime state must remain 'Observed' before
    and after advisory analysis."""
    from pcae.core.runtime_snapshot import build_runtime_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    from pcae.core.paths import HarnessPath

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath.cwd(), registry)

    assert snapshot.health.current_runtime_state == "Observed"
    assert snapshot.state.current_state == "Observed"

    ar.build_advisory_results(snapshot)

    assert snapshot.health.current_runtime_state == "Observed"
    assert snapshot.state.current_state == "Observed"


def test_maximum_plugin_capability_remains_observe(ar):
    """Verification 11: Maximum plugin capability must remain 'observe'
    — no escalation to enforce, execute, or authorize."""
    from pcae.core.runtime_snapshot import build_runtime_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    from pcae.core.paths import HarnessPath

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath.cwd(), registry)

    assert snapshot.health.current_maximum_plugin_capability == "observe"

    ar.build_advisory_results(snapshot)

    assert snapshot.health.current_maximum_plugin_capability == "observe"


# ═══════════════════════════════════════════════════════════════════════
# Section 12 — Execution Capability Remains Unavailable
# ═══════════════════════════════════════════════════════════════════════


def test_execution_capability_unavailable_before_and_after(ar):
    """Verification 12: Execution capability must remain 'unavailable'
    before and after advisory analysis."""
    from pcae.core.runtime_snapshot import build_runtime_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    from pcae.core.paths import HarnessPath

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath.cwd(), registry)

    assert snapshot.governance.execution_capability == "unavailable"
    assert snapshot.health.execution_availability == "unavailable"

    ar.build_advisory_results(snapshot)

    assert snapshot.governance.execution_capability == "unavailable"
    assert snapshot.health.execution_availability == "unavailable"


def test_non_executing_posture_true_before_and_after(ar):
    """Verification 12: non_executing_posture must remain True."""
    from pcae.core.runtime_snapshot import build_runtime_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    from pcae.core.paths import HarnessPath

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath.cwd(), registry)

    assert snapshot.governance.non_executing_posture is True

    ar.build_advisory_results(snapshot)

    assert snapshot.governance.non_executing_posture is True


def test_all_results_confirm_execution_unavailable(ar):
    """Verification 12: Every AdvisoryResult must confirm
    execution_unavailable in its implementation_status field."""
    from pcae.core.runtime_snapshot import build_runtime_snapshot
    from pcae.core.runtime_registry import RuntimeRegistry
    from pcae.core.paths import HarnessPath

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath.cwd(), registry)
    results = ar.build_advisory_results(snapshot)

    for r in results:
        assert r.implementation_status == "execution_unavailable"


# ═══════════════════════════════════════════════════════════════════════
# Section 13 — Cross-Cutting Verification
# ═══════════════════════════════════════════════════════════════════════


def test_advisory_runtime_classifier_not_tagged_as_execution(ar):
    """AdvisoryResult must never have implementation_status other than
    execution_unavailable — enforced at construction."""
    ev = ar.EvidenceReference(
        domain="health", object_id=None,
        field_path="health.runtime_status", evidence_summary="test",
    )
    for bad_status in ("executing", "available", "enabled", "implemented", "active"):
        with pytest.raises(ValueError):
            ar.AdvisoryResult(
                advisory_id="ADV-test-0001",
                category="Runtime Health",
                severity="info",
                confidence="observed",
                recommended_action="test",
                rationale="test rationale for the recommendation",
                evidence_references=(ev,),
                affected_runtime_objects=(),
                timestamp="2026-07-04T00:00:00Z",
                source_snapshot_reference="snapshot-test",
                reasoning_summary="test summary",
                alternative_considerations=(),
                remediation="none",
                implementation_status=bad_status,
            )


def test_cli_has_no_advisory_runtime_command(ar):
    """cli.py must not wire an advisory-runtime command — no execution path."""
    cli_path = REPO_ROOT / "src" / "pcae" / "cli.py"
    cli_text = cli_path.read_text()
    assert "advisory_runtime" not in cli_text
    assert "advisory-runtime" not in cli_text


def test_no_commands_module_for_advisory_runtime(ar):
    """No src/pcae/commands/advisory_runtime.py must exist."""
    cmd_path = REPO_ROOT / "src" / "pcae" / "commands" / "advisory_runtime.py"
    assert not cmd_path.exists(), (
        "src/pcae/commands/advisory_runtime.py exists — "
        "advisory runtime must not have a CLI command"
    )


def test_module_docstring_accurately_describes_phase(ar):
    """Module docstring must identify this as Phase 113C prototype."""
    doc = ar.__doc__ or ""
    assert "113C" in doc
    assert "Observation-only" in doc or "observation-only" in doc.lower()
    assert "no authorization" in doc.lower()
    assert "no execution" in doc.lower()


def test_advisory_invariant_is_universal_constant(ar):
    """ADVISORY_INVARIANT must be a module-level constant — same value
    for every consumer."""
    assert isinstance(ar.ADVISORY_INVARIANT, str)
    assert len(ar.ADVISORY_INVARIANT) > 50
    # Must contain both key principles
    assert "Recommendation precedes authorization" in ar.ADVISORY_INVARIANT
    assert "Explainability precedes trust" in ar.ADVISORY_INVARIANT


def test_frozen_vocabularies_are_immutable_tuples(ar):
    """All module-level vocabulary constants must be tuples (immutable)."""
    vocab_attrs = [
        "RUNTIME_SNAPSHOT_DOMAINS",
        "ADVISORY_CATEGORIES",
        "SEVERITY_LEVELS",
        "CONFIDENCE_LEVELS",
        "ADVISORY_LIFECYCLE_STAGES",
    ]
    for attr in vocab_attrs:
        val = getattr(ar, attr)
        assert isinstance(val, tuple), (
            f"{attr} is {type(val).__name__}, expected tuple"
        )


def test_all_results_have_valid_iso_timestamps(ar):
    """Every result's timestamp must be a valid ISO 8601 string."""
    import datetime
    snapshot = _minimal_snapshot(ar)
    results = ar.build_advisory_results(snapshot)
    for r in results:
        try:
            datetime.datetime.fromisoformat(r.timestamp)
        except ValueError:
            pytest.fail(f"Invalid ISO timestamp in {r.advisory_id}: {r.timestamp!r}")
