from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from pcae.cltr_prototype import identity as identity_mod
from pcae.cltr_prototype.identity import IdentityError, IdentityErrorKind, resolve_identity

FIXTURES = Path(__file__).parent / "fixtures" / "cltr_prototype"


def test_resolve_identity_basic():
    ident = resolve_identity(
        {"transition_id": "t1", "phase_id": "135F", "repository_identity": "pcae-harness", "branch_identity": "main"}
    )
    assert ident.transition_id == "t1"
    assert ident.phase_id == "135F"
    assert ident.task_id is None


def test_resolve_identity_missing_field_raises():
    with pytest.raises(IdentityError) as exc:
        resolve_identity({"phase_id": "135F", "repository_identity": "r", "branch_identity": "main"})
    assert exc.value.kind == IdentityErrorKind.MISSING_FIELD


@pytest.mark.parametrize(
    "phase_id",
    ["135A", "134E.10.1V.1", "134E.10.1.1", "135D.1"],
)
def test_dotted_phase_id_round_trips(phase_id):
    ident = resolve_identity(
        {"transition_id": "t1", "phase_id": phase_id, "repository_identity": "r", "branch_identity": "main"}
    )
    assert ident.phase_id == phase_id


@pytest.mark.parametrize("bad_phase_id", ["", "abc", "135", "135-A", "135F "])
def test_malformed_phase_id_rejected(bad_phase_id):
    with pytest.raises(IdentityError):
        resolve_identity(
            {"transition_id": "t1", "phase_id": bad_phase_id, "repository_identity": "r", "branch_identity": "main"}
        )


def test_task_id_bound_to_declaring_phase_only():
    ident = resolve_identity(
        {
            "transition_id": "t1",
            "phase_id": "135F",
            "repository_identity": "r",
            "branch_identity": "main",
            "task_id": "task-1",
        }
    )
    assert ident.task_id == "task-1"


def test_empty_string_task_id_rejected():
    with pytest.raises(IdentityError):
        resolve_identity(
            {
                "transition_id": "t1",
                "phase_id": "135F",
                "repository_identity": "r",
                "branch_identity": "main",
                "task_id": "",
            }
        )


def test_check_identity_conflict_detects_disagreement():
    fixture = json.loads((FIXTURES / "identity_mismatch.json").read_text())
    declared = resolve_identity(fixture["declared_identity"])
    conflict = identity_mod.check_identity_conflict(declared, fixture["embedded_identity_from_bound_artifact"])
    assert conflict is not None
    assert conflict.field == "phase_id"


def test_check_identity_conflict_none_when_agreeing():
    declared = resolve_identity(
        {"transition_id": "t1", "phase_id": "135F", "repository_identity": "r", "branch_identity": "main"}
    )
    conflict = identity_mod.check_identity_conflict(declared, {"phase_id": "135F", "transition_id": "t1"})
    assert conflict is None


def _non_docstring_source(module) -> str:
    """Concatenate every function's executable statements' source, stripping
    every module/function docstring — those legitimately *describe*, in
    prose, the identity sources this module must never actually read from."""

    import ast

    full_source = inspect.getsource(module)
    tree = ast.parse(full_source)
    parts = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = node.body
        for i, stmt in enumerate(body):
            is_docstring = i == 0 and isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant) and isinstance(stmt.value.value, str)
            if is_docstring:
                continue
            segment = ast.get_source_segment(full_source, stmt)
            if segment:
                parts.append(segment)
    return "\n".join(parts)


def test_identity_module_has_no_title_parsing_code_path():
    code = _non_docstring_source(identity_mod)
    for forbidden in ("title", "filename", "commit_subject"):
        assert forbidden not in code.lower(), f"identity.py's executable code must not reference {forbidden!r} as an identity source"


def test_identity_module_has_no_git_history_scan():
    code = _non_docstring_source(identity_mod)
    assert "subprocess" not in code
    assert "git" not in code.lower()
    assert "open(" not in code
    assert ".read_text(" not in code
