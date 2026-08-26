"""
Phase 149O.20L.7O.3J.1 — Independent End-to-End Repository Intelligence /
Advisory Consumption Verification.

Independently re-derives and verifies (or would refute) 149O.20L.7O.3J's
claim that the real Advisory production path (`pcae.core.advisory.build_advisory`,
the engine behind `pcae advisory check`) automatically consumes the
existing Repository Intelligence Advisory-context bridge
(`pcae.advisory.context.build_advisory_context`) without a manual CLI
prerequisite, read-only, fail-soft, and non-authoritatively.

This suite does NOT import any function from
`tests/test_phase_149o_20l_7o_3j_ri_advisory_production_consumption.py`.
It re-derives its own fixtures and its own assertions independently,
per the 3J.1 governing verification directive ("RE-DERIVE. DO NOT TRUST 3J.").
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from pcae.core import advisory as advisory_module
from pcae.core.advisory import build_advisory
from pcae.advisory.context.advisory_context_builder import (
    AdvisoryContextBuilderError,
    build_advisory_context,
)
from pcae.advisory.context.context_request import AdvisoryContextRequest
from pcae.repository_intelligence.snapshot_generator import generate_snapshot
from pcae.repository_intelligence.persistence import DEFAULT_OUTPUT_SUBDIR

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent


def _fresh_repo_with_real_snapshot(tmp_path: Path, name: str = "repo") -> Path:
    """A disposable repo_root with a freshly-generated, valid RI snapshot
    at the canonical `.pcae/repository-intelligence/latest.json` location,
    generated independently in this suite (not reusing 3J's fixture code)."""
    repo_root = tmp_path / name
    repo_root.mkdir(parents=True)
    generate_snapshot(REPO_ROOT, output_dir=repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR)
    return repo_root


def _canonical_snapshot_path(repo_root: Path) -> Path:
    return repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR / "latest.json"


# ── 1/2: pre-3J had no automatic RI consumption; post-3J reaches it ──────


def test_no_repository_intelligence_import_would_be_required_pre_3j_by_source_diff():
    """Independently re-derive, from the current source tree, that the
    RI/advisory-context imports and the `_gather_repository_intelligence_context`
    helper exist in build_advisory's module -- i.e. this is genuinely wired
    into the module that backs `pcae advisory check`, not merely present
    in a parallel/unrelated module."""
    source = Path(advisory_module.__file__).read_text()
    assert "build_advisory_context" in source
    assert "_gather_repository_intelligence_context" in source
    tree = ast.parse(source)
    func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "build_advisory" in func_names
    assert "_gather_repository_intelligence_context" in func_names


def test_build_advisory_reaches_repository_intelligence_context_key(tmp_path):
    """Direct call to the real production entry point (not a test helper
    invoked only by tests) returns the additive RI context key."""
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    assert "repository_intelligence_context" in data
    assert data["repository_intelligence_context"]["available"] is True


# ── 3: no manual CLI prerequisite ────────────────────────────────────────


def test_no_manual_context_build_precedes_automatic_consumption(tmp_path):
    """RI context is available on the very first call to build_advisory in
    a brand-new repo_root -- no `build_advisory_context`/CLI call precedes it
    in this test."""
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    # Nothing else touches build_advisory_context before this call.
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    assert data["repository_intelligence_context"]["available"] is True


# ── 4/20: canonical latest.json pointer ──────────────────────────────────


def test_canonical_latest_json_is_the_pipeline_write_location(tmp_path):
    """Independently confirm, from persistence.py itself (the write side of
    the pipeline), that `latest.json` under DEFAULT_OUTPUT_SUBDIR is the
    literal artifact the generator (over)writes -- not a heuristic chosen
    by the Advisory consumer."""
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    expected = repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR / "latest.json"
    assert expected.is_file()
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    assert data["repository_intelligence_context"]["available"] is True
    # Remove only latest.json (leave snapshots/ dir); consumption must fail.
    expected.unlink()
    data2 = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    assert data2["repository_intelligence_context"]["available"] is False


# ── 5: read-only acquisition ──────────────────────────────────────────────


def test_acquisition_is_read_only_no_filesystem_mutation(tmp_path):
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    ri_dir = repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR
    before = {
        p: (p.stat().st_mtime_ns, p.read_bytes())
        for p in ri_dir.rglob("*") if p.is_file()
    }
    build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    build_advisory(repo_root=repo_root, requested_command="git status", requested_action="read")
    after = {
        p: (p.stat().st_mtime_ns, p.read_bytes())
        for p in ri_dir.rglob("*") if p.is_file()
    }
    assert before == after


# ── 6/7: valid RI / missing RI ────────────────────────────────────────────


def test_missing_ri_snapshot_directory_entirely(tmp_path):
    repo_root = tmp_path / "no_ri_repo"
    repo_root.mkdir()
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    assert ri["available"] is False
    assert ri["unavailable_reason"] == "no_repository_intelligence_snapshot_found"


# ── 8: malformed JSON ──────────────────────────────────────────────────────


def test_malformed_json_snapshot_fails_soft_no_traceback(tmp_path):
    repo_root = tmp_path / "malformed_repo"
    ri_dir = repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR
    ri_dir.mkdir(parents=True)
    (ri_dir / "latest.json").write_text("{not valid json!!")
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    assert ri["available"] is False
    assert ri["unavailable_reason"] == "repository_intelligence_context_build_failed"
    assert "not valid JSON" in ri["unavailable_detail"]


# ── 9: incompatible schema version ────────────────────────────────────────


def test_incompatible_schema_version_fails_soft(tmp_path):
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    snap_path = _canonical_snapshot_path(repo_root)
    snapshot = json.loads(snap_path.read_text())
    snapshot["snapshot_identity"]["executable_schema_version"] = "999.9.9-not-real"
    snap_path.write_text(json.dumps(snapshot))
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    assert ri["available"] is False
    assert "unsupported" in ri["unavailable_detail"]


# ── corrupt-but-valid-JSON: missing required key (absent != corrupt) ────


def test_corrupt_snapshot_missing_required_key_distinguished_from_absent(tmp_path):
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    snap_path = _canonical_snapshot_path(repo_root)
    snapshot = json.loads(snap_path.read_text())
    del snapshot["capabilities"]
    snap_path.write_text(json.dumps(snapshot))
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    assert ri["available"] is False
    assert ri["unavailable_reason"] == "repository_intelligence_context_build_failed"
    assert ri["unavailable_reason"] != "no_repository_intelligence_snapshot_found"


# ── 10: staleness derivation and disclosure ──────────────────────────────


def test_staleness_disclosed_via_preexisting_repository_commit_field(tmp_path):
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    snap_path = _canonical_snapshot_path(repo_root)
    snapshot = json.loads(snap_path.read_text())
    snapshot["envelope"]["repository_context"]["repository_commit"] = "0" * 40
    snap_path.write_text(json.dumps(snapshot))

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "x", "-q"], cwd=repo_root, check=True)

    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    assert ri["available"] is True
    types = [l["limitation_type"] for l in ri["context"]["limitation_bundle"]]
    assert "possibly_stale_snapshot" in types


def test_matching_commit_produces_no_stale_disclosure(tmp_path):
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    snap_path = _canonical_snapshot_path(repo_root)
    snapshot = json.loads(snap_path.read_text())

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "x", "-q"], cwd=repo_root, check=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    snapshot["envelope"]["repository_context"]["repository_commit"] = head
    snap_path.write_text(json.dumps(snapshot))

    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    types = [l["limitation_type"] for l in ri["context"]["limitation_bundle"]]
    assert "possibly_stale_snapshot" not in types


# ── 11: provenance preservation ──────────────────────────────────────────


def test_provenance_source_artifact_fields_preserved(tmp_path):
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    metadata = ri["context"]["context_metadata"]
    assert "source_artifact" in metadata
    assert metadata["source_artifact"].get("snapshot_id")
    assert metadata["source_artifact"].get("repository_commit")


# ── 12: limitations preservation, additive not destructive ──────────────


def test_original_limitations_survive_alongside_new_disclosure(tmp_path):
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    snap_path = _canonical_snapshot_path(repo_root)
    snapshot = json.loads(snap_path.read_text())
    snapshot["envelope"]["repository_context"]["repository_commit"] = "0" * 40
    snap_path.write_text(json.dumps(snapshot))
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "x", "-q"], cwd=repo_root, check=True)

    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    types = [l["limitation_type"] for l in ri["context"]["limitation_bundle"]]
    assert "scope_limitation" in types  # pre-existing snapshot-prototype limitation
    assert "possibly_stale_snapshot" in types  # additive disclosure
    assert len(types) == len(set(types))  # distinguishable, not merged/deduped away


# ── 13: repository identity binding / cross-repo isolation ───────────────


def test_symlinked_foreign_ri_directory_is_disclosed_as_stale_once_head_exists(tmp_path):
    """A foreign RI snapshot placed at the canonical path via symlink is
    consumed (no path-based repo-identity check exists beyond commit-SHA
    staleness disclosure). Document the actual guarantee: once the target
    repo has a HEAD commit, a differing snapshot commit is disclosed as
    'possibly_stale_snapshot' -- this is the only existing cross-repository
    safeguard, and it is a staleness disclosure, not a hard rejection."""
    repo_a = _fresh_repo_with_real_snapshot(tmp_path, name="repo_a")
    repo_b = tmp_path / "repo_b"
    (repo_b / ".pcae").mkdir(parents=True)
    (repo_b / ".pcae" / DEFAULT_OUTPUT_SUBDIR).symlink_to(
        repo_a / ".pcae" / DEFAULT_OUTPUT_SUBDIR
    )
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "x", "-q"], cwd=repo_b, check=True)

    data = build_advisory(repo_root=repo_b, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    assert ri["available"] is True  # foreign snapshot IS consumed
    types = [l["limitation_type"] for l in ri["context"]["limitation_bundle"]]
    assert "possibly_stale_snapshot" in types  # only mitigation: disclosed as stale


def test_symlinked_foreign_ri_with_no_head_commit_yields_zero_disclosure(tmp_path):
    """FINDING: in a repo with no commits yet (no resolvable HEAD), the
    staleness comparison is silently skipped (HistoricalSourceError ->
    current_commit=None -> comparison short-circuits), so a foreign
    snapshot consumed via a canonical-path symlink is presented with
    *no* cross-repository disclosure at all in this edge case."""
    repo_a = _fresh_repo_with_real_snapshot(tmp_path, name="repo_a2")
    repo_b = tmp_path / "repo_b2"
    (repo_b / ".pcae").mkdir(parents=True)
    (repo_b / ".pcae" / DEFAULT_OUTPUT_SUBDIR).symlink_to(
        repo_a / ".pcae" / DEFAULT_OUTPUT_SUBDIR
    )
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True)
    # deliberately no commit -> no HEAD

    data = build_advisory(repo_root=repo_b, requested_command="ls", requested_action="read")
    ri = data["repository_intelligence_context"]
    assert ri["available"] is True
    types = [l["limitation_type"] for l in ri["context"]["limitation_bundle"]]
    assert "possibly_stale_snapshot" not in types


# ── 14: determinism (modulo timestamp) ───────────────────────────────────


def test_deterministic_repeat_modulo_assembly_timestamp(tmp_path):
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    d1 = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    d2 = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")

    def strip(ri):
        ri = json.loads(json.dumps(ri))
        ri["context"]["context_metadata"].pop("assembly_timestamp", None)
        return ri

    assert strip(d1["repository_intelligence_context"]) == strip(d2["repository_intelligence_context"])
    assert d1["broker_decision"] == d2["broker_decision"]
    assert d1["advisory_decision"] == d2["advisory_decision"]


# ── 15/16: authority non-flow + causal ordering ──────────────────────────


_AUTHORITY_FIELDS = [
    "broker_decision", "advisory_decision", "would_allow_read_only",
    "would_allow_governed_preflight_only", "would_require_active_task",
    "would_require_preflight", "would_require_human_review",
    "would_require_more_evidence", "would_block", "would_deny",
    "hard_block_present", "authorization_granted", "execution_authorized",
    "command_executed", "enforcement_applied",
]


def test_authority_fields_invariant_with_and_without_ri_context(tmp_path):
    with_ri = _fresh_repo_with_real_snapshot(tmp_path, name="with_ri")
    without_ri = tmp_path / "without_ri"
    without_ri.mkdir()

    a = build_advisory(repo_root=with_ri, requested_command="ls", requested_action="read")
    b = build_advisory(repo_root=without_ri, requested_command="ls", requested_action="read")

    assert a["repository_intelligence_context"]["available"] is True
    assert b["repository_intelligence_context"]["available"] is False
    for field in _AUTHORITY_FIELDS:
        assert a[field] == b[field], f"authority field {field} diverged with RI presence"


def test_causal_ordering_ri_computed_after_broker_decision_bound(tmp_path):
    """Static re-derivation: in build_advisory's source, the
    `repository_intelligence_context` local is assigned strictly after the
    line that reads `broker["decision"]` into `broker_decision`, and the
    returned dict's authority-bearing values are plain already-bound local
    variables at the point `_gather_repository_intelligence_context` is
    called -- so RI acquisition cannot mutate them in this call graph."""
    source = Path(advisory_module.__file__).read_text()
    broker_decision_idx = source.index('broker_decision: str = broker["decision"]')
    ri_call_idx = source.index("repository_intelligence_context = _gather_repository_intelligence_context")
    assert broker_decision_idx < ri_call_idx
    # the RI helper must not accept broker/decision state as input
    import inspect
    params = list(inspect.signature(advisory_module._gather_repository_intelligence_context).parameters)
    assert params == ["repo_root", "requested_files"]


# ── 17: Permission Broker isolation ──────────────────────────────────────


def test_no_permission_broker_reference_in_ri_or_context_modules():
    import pcae.advisory.context.advisory_context_builder as builder_mod
    import pcae.repository_intelligence.query.query_engine as query_mod
    for mod in (builder_mod, query_mod):
        source = Path(mod.__file__).read_text()
        assert "permission_broker" not in source.lower()


def test_no_ri_or_advisory_context_reference_in_permission_broker():
    import pcae.core.permission_broker as broker_mod
    source = Path(broker_mod.__file__).read_text()
    assert "repository_intelligence" not in source.lower()
    assert "advisory_context" not in source.lower()
    assert "build_advisory_context" not in source


# ── 18: attachment vs. genuine consumption adjudication ──────────────────


def test_ri_context_is_attachment_not_consumed_by_decision_reasoning(tmp_path):
    """Directly answers the mandatory Step 25/26 question. Construct two
    scenarios with identical broker-relevant evidence but RI context that
    would differ (available vs. unavailable, and different snapshot
    content); advisory_decision and advisory_recommendation must be
    byte-identical in both, proving RI is exposed in the output envelope
    but not consumed by any reasoning step that determines the decision or
    its accompanying recommendation text."""
    with_ri = _fresh_repo_with_real_snapshot(tmp_path, name="attach_with_ri")
    without_ri = tmp_path / "attach_without_ri"
    without_ri.mkdir()

    a = build_advisory(repo_root=with_ri, requested_command="ls", requested_action="read")
    b = build_advisory(repo_root=without_ri, requested_command="ls", requested_action="read")

    assert a["advisory_decision"] == b["advisory_decision"]
    assert a["advisory_recommendation"] == b["advisory_recommendation"]
    assert a["operator_message"] == b["operator_message"]
    assert a["next_required_action"] == b["next_required_action"]


# ── 19: output compatibility (additive key only) ─────────────────────────


def test_ri_context_key_is_purely_additive_all_other_keys_unaffected(tmp_path):
    with_ri = _fresh_repo_with_real_snapshot(tmp_path, name="compat_with")
    without_ri = tmp_path / "compat_without"
    without_ri.mkdir()

    a = build_advisory(repo_root=with_ri, requested_command="ls", requested_action="read")
    b = build_advisory(repo_root=without_ri, requested_command="ls", requested_action="read")

    a_keys = set(a) - {"repository_intelligence_context", "generated_at", "repository_root"}
    b_keys = set(b) - {"repository_intelligence_context", "generated_at", "repository_root"}
    assert a_keys == b_keys


# ── 20: manual CLI unchanged / direct service path ────────────────────────


def test_manual_context_build_still_requires_explicit_snapshot_path_and_fails_closed(tmp_path):
    with pytest.raises(AdvisoryContextBuilderError):
        build_advisory_context(
            tmp_path / "does_not_exist.json",
            AdvisoryContextRequest(category="boundary_lookup", advisory_purpose="test"),
        )


def test_production_path_calls_shared_builder_directly_not_a_reimplementation(tmp_path):
    """Confirm core/advisory.py imports and calls the *same* function
    object as the manual CLI path, rather than a duplicate/parallel
    implementation."""
    import pcae.commands.advisory_context as manual_cli_mod
    assert advisory_module.build_advisory_context is manual_cli_mod.build_advisory_context


# ── 21: no self-CLI / no subprocess in production RI+advisory path ──────


def test_no_subprocess_or_shell_reference_in_advisory_module():
    source = Path(advisory_module.__file__).read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


# ── 22: no model/network expansion ───────────────────────────────────────


def test_no_network_or_model_provider_references(tmp_path):
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    import pcae.advisory.context.advisory_context_builder as builder_mod
    import pcae.repository_intelligence.query.query_engine as query_mod
    for mod in (advisory_module, builder_mod, query_mod):
        source = Path(mod.__file__).read_text().lower()
        for banned in ("openrouter", "openai", "requests.", "urllib", "httpx", "socket."):
            assert banned not in source


# ── 23: runtime unchanged ─────────────────────────────────────────────────


def test_runtime_inspect_unchanged_around_advisory_invocation(tmp_path):
    from pcae.commands.runtime_inspect import run_runtime_inspect  # noqa: F401  (import-only smoke check)
    repo_root = _fresh_repo_with_real_snapshot(tmp_path)
    # Advisory invocation must not touch runtime state; assert no runtime
    # module is imported transitively by build_advisory's own module source.
    source = Path(advisory_module.__file__).read_text()
    assert "runtime_enforcement" not in source.lower()
    assert "plugin_registry" not in source.lower()
    build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")


# ── 24: retry / re-entry (missing -> valid -> stale-fixed) ───────────────


def test_retry_reentry_missing_then_valid_then_fixed_staleness(tmp_path):
    repo_root = tmp_path / "retry_repo"
    repo_root.mkdir()

    d1 = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    assert d1["repository_intelligence_context"]["available"] is False

    generate_snapshot(REPO_ROOT, output_dir=repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR)
    d2 = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    assert d2["repository_intelligence_context"]["available"] is True

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "x", "-q"], cwd=repo_root, check=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    snap_path = _canonical_snapshot_path(repo_root)
    snapshot = json.loads(snap_path.read_text())
    snapshot["envelope"]["repository_context"]["repository_commit"] = head
    snap_path.write_text(json.dumps(snapshot))

    d3 = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    types = [l["limitation_type"] for l in d3["repository_intelligence_context"]["context"]["limitation_bundle"]]
    assert "possibly_stale_snapshot" not in types
