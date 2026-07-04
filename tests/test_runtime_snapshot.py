"""Tests for Phase 112E — Runtime Snapshot & Runtime Inspect Context Integration.

Verifies `pcae.core.runtime_snapshot` (112E): the new `RuntimeSnapshot`
composition (Runtime/Registry/Plugin/Capability/Governance/Health
metadata from 111B, unchanged, plus Runtime Context from 112C), the
read-only `build_runtime_context_from_repo()` helper that reflects real
session/task state into a `RuntimeContext`, and the CLI's consumption
of it through `pcae.commands.runtime_inspect._build_snapshot()`.
Confirms backward compatibility with 111C/111D's own JSON schema,
module isolation (no broker evaluation, no plugin loading, no shell/
subprocess/network), and every observation-only guarantee.

No subprocess invocation in this file; pure in-process, pytest-xdist
safe.
"""

from __future__ import annotations

import ast
import dataclasses
import json
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands import runtime_inspect as ri_cli
from pcae.core import runtime_snapshot as rs
from pcae.core.paths import HarnessPath
from pcae.core.runtime_context import RuntimeContext
from pcae.core.runtime_registry import RuntimeRegistry
from pcae.core.runtime_snapshot import (
    RuntimeSnapshot,
    build_runtime_context_from_repo,
    build_runtime_snapshot,
    snapshot_to_dict,
)

REPO_ROOT = Path(rs.__file__).resolve().parent.parent.parent.parent


def _run(capsys, *args: str) -> tuple[int, str]:
    exit_code = main(["runtime", "inspect", *args])
    output = capsys.readouterr().out
    return exit_code, output


def _write_session(tmp_path: Path, *, timestamp: str = "2026-01-01T00:00:00+00:00") -> None:
    pcae_dir = tmp_path / ".pcae"
    pcae_dir.mkdir(exist_ok=True)
    (pcae_dir / "session.json").write_text(
        json.dumps({"active_task": None, "timestamp": timestamp}), encoding="utf-8"
    )


def _write_active_task(tmp_path: Path, *, task_id: str = "20260101-0000-example", title: str = "Example task") -> None:
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / f"{task_id}.md").write_text(
        "# Task Contract\n\n"
        f"## Task ID\n\n{task_id}\n\n"
        f"## Title\n\n{title}\n\n"
        "## Status\n\nactive\n\n"
        "## Mode\n\nimplementation\n\n"
        "## Allowed Files\n\n- src/pcae/**\n",
        encoding="utf-8",
    )


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — Runtime Snapshot concept exists
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_snapshot_is_a_frozen_dataclass():
    assert dataclasses.is_dataclass(RuntimeSnapshot)
    assert RuntimeSnapshot.__dataclass_params__.frozen is True


def test_runtime_snapshot_field_names():
    field_names = {f.name for f in dataclasses.fields(RuntimeSnapshot)}
    assert field_names == {
        "runtime", "registry", "plugins", "capabilities",
        "health", "governance", "state", "version", "context",
    }


def test_module_docstring_names_canonical_read_model_principle():
    text = Path(rs.__file__).read_text()
    assert "canonical read model" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — composition (no duplication, delegates to 111B/112C)
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_snapshot_composes_registry_metadata_via_111b():
    from pcae.core.runtime_introspection import get_registry

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath(REPO_ROOT), registry)
    assert snapshot.registry == get_registry(registry)


def test_runtime_snapshot_composes_runtime_metadata_via_111b():
    from pcae.core.runtime_introspection import get_runtime

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath(REPO_ROOT), registry)
    assert snapshot.runtime == get_runtime()


def test_runtime_snapshot_composes_governance_and_state_via_111b():
    from pcae.core.runtime_introspection import get_governance, get_state

    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath(REPO_ROOT), registry)
    assert snapshot.governance == get_governance()
    assert snapshot.state == get_state()


def test_runtime_snapshot_composes_runtime_context(tmp_path: Path):
    _write_session(tmp_path)
    _write_active_task(tmp_path)
    registry = RuntimeRegistry()
    snapshot = build_runtime_snapshot(HarnessPath(tmp_path), registry)
    assert isinstance(snapshot.context, RuntimeContext)
    assert snapshot.context.session is not None
    assert snapshot.context.session.tasks[0].task_id == "20260101-0000-example"


def test_no_duplicate_field_names_across_composed_objects():
    """RuntimeSnapshot's own field set must be exactly the composed
    object references -- no independently-recomputed duplicate of a
    field 111B/112C already owns (e.g. no separate 'plugin_count' field
    duplicating what health.plugin_count already reports)."""
    field_names = {f.name for f in dataclasses.fields(RuntimeSnapshot)}
    forbidden_duplicates = {"plugin_count", "capability_count", "runtime_status", "session_id", "task_id"}
    assert not (field_names & forbidden_duplicates)


# ═══════════════════════════════════════════════════════════════════════
# build_runtime_context_from_repo() -- hermetic behavior
# ═══════════════════════════════════════════════════════════════════════


def test_context_none_when_no_session_file(tmp_path: Path):
    assert build_runtime_context_from_repo(HarnessPath(tmp_path)) is None


def test_context_present_with_empty_tasks_when_session_exists_no_active_task(tmp_path: Path):
    _write_session(tmp_path)
    context = build_runtime_context_from_repo(HarnessPath(tmp_path))
    assert context is not None
    assert context.session.tasks == ()


def test_context_includes_active_task_when_present(tmp_path: Path):
    _write_session(tmp_path)
    _write_active_task(tmp_path, task_id="20260202-0000-other", title="Other task")
    context = build_runtime_context_from_repo(HarnessPath(tmp_path))
    assert len(context.session.tasks) == 1
    assert context.session.tasks[0].task_id == "20260202-0000-other"
    assert context.session.tasks[0].title == "Other task"


def test_context_observation_always_populated_when_session_exists(tmp_path: Path):
    """112B §8: 'Observation always available' -- the four INT-NNN
    integrations are reported regardless of whether a task is active."""
    _write_session(tmp_path)
    context = build_runtime_context_from_repo(HarnessPath(tmp_path))
    assert context.session.observation is not None
    assert len(context.session.observation.consulted_integrations) == 4


def test_context_lifecycle_stage_is_observed_not_created(tmp_path: Path):
    """A context built from real, already-existing repo state has
    genuinely been observed -- 'Created' (the default for a freshly
    constructed, unpopulated object) would understate that."""
    _write_session(tmp_path)
    context = build_runtime_context_from_repo(HarnessPath(tmp_path))
    assert context.lifecycle_stage == "Observed"
    assert context.session.lifecycle_stage == "Observed"


def test_phase_intent_approval_decision_evidence_never_populated(tmp_path: Path):
    """None of these has a real, governed backing source anywhere in
    this codebase (COMP-003/COMP-007 unimplemented) -- confirmed the
    snapshot never invents placeholder data for them."""
    _write_session(tmp_path)
    _write_active_task(tmp_path)
    snapshot = build_runtime_snapshot(HarnessPath(tmp_path), RuntimeRegistry())
    d = snapshot_to_dict(snapshot)
    assert d["context"]["active_phase"] is None
    assert d["context"]["intent"] is None
    assert d["context"]["approval"] is None
    assert d["context"]["broker_decision"] is None
    assert d["context"]["evidence"] is None


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — CLI consumes Runtime Snapshot (no bespoke assembly)
# ═══════════════════════════════════════════════════════════════════════


def test_cli_build_snapshot_delegates_to_runtime_snapshot():
    registry = RuntimeRegistry()
    result = ri_cli._build_snapshot(registry)
    root = HarnessPath.cwd()
    expected = snapshot_to_dict(build_runtime_snapshot(root, registry))
    # context is time/session-dependent (real repo state) -- compare
    # everything except context directly, then compare context shape.
    assert {k: v for k, v in result.items() if k != "context"} == {
        k: v for k, v in expected.items() if k != "context"
    }
    assert set(result["context"] or {}) == set(expected["context"] or {})


def test_build_snapshot_function_has_no_loop_no_bespoke_assembly():
    """The CLI's own _build_snapshot must contain no loop -- all
    composition now lives in pcae.core.runtime_snapshot."""
    tree = ast.parse(Path(ri_cli.__file__).read_text())
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_build_snapshot")
    loops = [n for n in ast.walk(fn) if isinstance(n, (ast.For, ast.While))]
    assert loops == []


def test_verbose_output_includes_runtime_context_section(capsys):
    _, output = _run(capsys, "--verbose")
    assert "Runtime Context (112E):" in output
    assert "Session:" in output
    assert "Active task:" in output


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — backward compatibility
# ═══════════════════════════════════════════════════════════════════════


def test_backward_compatible_top_level_keys_still_present(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    original_keys = {"runtime", "registry", "plugins", "capabilities", "health", "governance", "state", "version"}
    assert original_keys <= set(data.keys())


def test_backward_compatible_section_shapes_unchanged(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert set(data["health"].keys()) == {
        "runtime_status", "registry_status", "plugin_count", "capability_count",
        "metadata_validity", "execution_availability", "current_runtime_state",
        "current_maximum_plugin_capability",
    }


def test_pcae_runtime_inspect_still_exits_zero(capsys):
    exit_code, _ = _run(capsys)
    assert exit_code == 0


def test_pcae_runtime_inspect_json_still_exits_zero(capsys):
    exit_code, _ = _run(capsys, "--json")
    assert exit_code == 0


def test_pcae_runtime_inspect_verbose_still_exits_zero(capsys):
    exit_code, _ = _run(capsys, "--verbose")
    assert exit_code == 0


def test_json_output_is_new_additive_key_only(capsys):
    """The only new top-level key is 'context' -- no existing key was
    removed or renamed."""
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert set(data.keys()) == {
        "runtime", "registry", "plugins", "capabilities",
        "health", "governance", "state", "version", "context",
    }


# ═══════════════════════════════════════════════════════════════════════
# Objective 5/7 — runtime state, execution unavailable, observation-only
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_state_remains_observed(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["health"]["current_runtime_state"] == "Observed"
    assert data["state"]["current_state"] == "Observed"


def test_execution_capability_remains_unavailable(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["health"]["execution_availability"] == "unavailable"
    assert data["governance"]["execution_capability"] == "unavailable"


def test_maximum_plugin_capability_remains_observe(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["health"]["current_maximum_plugin_capability"] == "observe"


@pytest.fixture(scope="module")
def module_imports() -> list[str]:
    tree = ast.parse(Path(rs.__file__).read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def test_module_imports_are_allowlisted(module_imports):
    allowed = {
        "__future__",
        "dataclasses",
        "pcae.core.command_path_observation",
        "pcae.core.paths",
        "pcae.core.runtime_context",
        "pcae.core.runtime_introspection",
        "pcae.core.runtime_registry",
        "pcae.core.session",
        "pcae.core.tasks",
    }
    for name in module_imports:
        assert name in allowed, f"unexpected import: {name}"


def test_no_broker_evaluation_dependency(module_imports):
    for name in module_imports:
        assert "broker" not in name.lower()


def test_no_plugin_loading_or_invocation_dependency(module_imports):
    for name in module_imports:
        assert "plugin" not in name.lower()


def test_no_shell_subprocess_network_or_telegram_dependency(module_imports):
    forbidden = ("shell_gate", "subprocess", "backend_invocations", "notifications", "telegram", "socket", "requests", "urllib")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_no_permission_broker_evaluate_call():
    tree = ast.parse(Path(rs.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            assert name not in ("PermissionBroker", "evaluate")


def test_no_execution_related_calls_in_module():
    tree = ast.parse(Path(rs.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            assert name not in ("eval", "exec", "compile", "system", "popen", "run", "call", "check_output")


def test_no_writes_no_mutation_reading_session_state(tmp_path: Path):
    """build_runtime_context_from_repo() reads; it must never write."""
    _write_session(tmp_path)
    _write_active_task(tmp_path)
    before = {p: p.read_text() for p in tmp_path.rglob("*") if p.is_file()}
    build_runtime_context_from_repo(HarnessPath(tmp_path))
    after = {p: p.read_text() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after


def test_no_secrets_exposed(capsys):
    for extra_args in ((), ("--json",), ("--verbose",)):
        _, output = _run(capsys, *extra_args)
        lowered = output.lower()
        for forbidden in ("token", "secret", "credential", "password", "api_key", "apikey"):
            assert forbidden not in lowered


def test_no_manifest_exposed(capsys):
    for extra_args in ((), ("--json",), ("--verbose",)):
        _, output = _run(capsys, *extra_args)
        assert "manifest" not in output.lower()
