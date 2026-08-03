"""Tests for Phase 149F — Repository-Wide Mutation Permission Coverage
Wave 1: authoritative, AST-based mutation inventory guard.

Enumerates every `subprocess.run(["git", ...])` (commit/push/revert/
reset) and every direct `write_text`/`write_bytes`/`unlink` call in the
four in-scope files (`push.py`, `agent.py`, `task.py`, `phase.py`),
classifies each by its enclosing function against the frozen RWMPC-001
13-site inventory, and fails on any site that is new/unclassified
(`UNKNOWN`) or that no longer matches its expected classification.

Classification vocabulary:
  EXISTING_CERTIFIED   -- PU1, PU2 (Chapter 148, unchanged)
  WAVE1_GOVERNED        -- AG1, AG2, AG4, PH1 (broker-gated in this phase)
  CANONICALLY_ROUTED     -- AG2 dispatcher itself (shared by PH2/PH3);
                            PH2/PH3 route here and construct no dispatch
                            of their own (zero matches expected)
  ROLLBACK_BLOCKED       -- AG3, AG5 (not Wave 1; unchanged)
  TASK_FINISH_DEFERRED   -- TK1, TK2, TK3 (not Wave 1; unchanged)
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUSH_PY = REPO_ROOT / "src" / "pcae" / "commands" / "push.py"
AGENT_PY = REPO_ROOT / "src" / "pcae" / "core" / "agent.py"
TASK_PY = REPO_ROOT / "src" / "pcae" / "commands" / "task.py"
PHASE_PY = REPO_ROOT / "src" / "pcae" / "commands" / "phase.py"

_GIT_MUTATION_SUBCOMMANDS = {"commit", "push", "revert", "reset"}
_WRITE_METHODS = {"write_text", "write_bytes", "unlink"}

# Enclosing-function-name -> classification. A dispatch/write call found
# inside a function not listed here is UNKNOWN (test failure). Functions
# listed with an empty expected classification set are *forbidden* from
# containing any matching call (routing must have removed it).
_CLASSIFICATION: dict[tuple[Path, str], str] = {
    (PUSH_PY, "run_push"): "EXISTING_CERTIFIED",
    (PUSH_PY, "_run_push_staged_file_aware"): "EXISTING_CERTIFIED",
    (AGENT_PY, "_run_git_commit"): "WAVE1_GOVERNED",
    (AGENT_PY, "_run_git_push"): "WAVE1_GOVERNED",
    (AGENT_PY, "_run_git_revert"): "ROLLBACK_BLOCKED",
    (AGENT_PY, "build_promotion_execution"): "WAVE1_GOVERNED",
    (AGENT_PY, "build_rollback_execution"): "ROLLBACK_BLOCKED",
    (TASK_PY, "run_task_finish"): "TASK_FINISH_DEFERRED",
    (TASK_PY, "run_task_finish_recover"): "TASK_FINISH_DEFERRED",
    (PHASE_PY, "_build_backend_created_output_adoption_commit_execution"): "WAVE1_GOVERNED",
}

# Functions that must contain ZERO matching dispatch calls (their
# dispatch was intentionally removed by Wave-1 routing).
_MUST_BE_EMPTY: set[tuple[Path, str]] = {
    (PHASE_PY, "_build_backend_created_output_adoption_push_execution"),
    (PHASE_PY, "_build_final_verification_tooling_push_decision"),
}

_EXPECTED_MIN_COUNTS: dict[tuple[Path, str], int] = {
    (PUSH_PY, "run_push"): 1,
    (PUSH_PY, "_run_push_staged_file_aware"): 1,
    (AGENT_PY, "_run_git_commit"): 1,
    (AGENT_PY, "_run_git_push"): 1,
    (AGENT_PY, "_run_git_revert"): 1,
    (AGENT_PY, "build_promotion_execution"): 1,
    (AGENT_PY, "build_rollback_execution"): 1,
    (TASK_PY, "run_task_finish"): 2,  # TK1 + TK2
    (TASK_PY, "run_task_finish_recover"): 1,  # TK3
    (PHASE_PY, "_build_backend_created_output_adoption_commit_execution"): 1,
}


def _is_git_mutation_list(node: ast.AST) -> bool:
    # `["git", "commit", ...] + stageable_paths` (TK1, task.py:308) is a
    # BinOp(Add) whose left operand is the literal list -- unwrap it so
    # the concatenation doesn't hide the dispatch from static detection.
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        node = node.left
    if not isinstance(node, ast.List) or not node.elts:
        return False
    first = node.elts[0]
    if not (isinstance(first, ast.Constant) and first.value == "git"):
        return False
    if len(node.elts) < 2:
        return False
    second = node.elts[1]
    return isinstance(second, ast.Constant) and second.value in _GIT_MUTATION_SUBCOMMANDS


def _is_subprocess_dispatch_call(call: ast.Call) -> bool:
    func = call.func
    name = None
    if isinstance(func, ast.Attribute):
        name = func.attr
    if name != "run":
        return False
    if not call.args:
        return False
    return _is_git_mutation_list(call.args[0])


def _is_direct_write_call(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute) and func.attr in _WRITE_METHODS:
        return True
    return False


# Direct write_text/write_bytes/unlink is an extremely common pattern for
# ordinary `.pcae/**` lifecycle-state bookkeeping (explicitly out of
# RWMPC-001 scope, Section 2/RWMPC-REQ-006) throughout agent.py -- a
# blanket file-wide scan for these method names alone would be almost
# entirely false positives unrelated to root-mutation dispatch. RWMPC-001
# already independently identifies exactly which two functions perform
# the *root-mutating* direct writes (AG4, AG5); this guard checks write/
# unlink calls only within those two known functions' bodies, while the
# `git`-subprocess-dispatch scan (narrow and reliable on its own: an
# explicit `["git", "commit"/"push"/"revert"/"reset", ...]` literal) runs
# repo-wide to catch a genuinely new 14th site.
_WRITE_SCAN_FUNCTIONS: set[tuple[Path, str]] = {
    (AGENT_PY, "build_promotion_execution"),
    (AGENT_PY, "build_rollback_execution"),
}


def _enclosing_function_matches(
    tree: ast.AST, path: Path, *, scan_writes: bool = False
) -> list[tuple[str, int]]:
    """Return (function_name, lineno) for every matching call, attributed
    to its innermost enclosing top-level function. `scan_writes=True`
    additionally reports write_text/write_bytes/unlink calls, but only
    when the enclosing function is one of `_WRITE_SCAN_FUNCTIONS` for
    this path (see rationale above)."""
    matches: list[tuple[str, int]] = []

    class _Visitor(ast.NodeVisitor):
        def __init__(self):
            self.func_stack: list[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef):
            self.func_stack.append(node.name)
            self.generic_visit(node)
            self.func_stack.pop()

        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)

        def visit_Call(self, node: ast.Call):
            if self.func_stack:
                enclosing = self.func_stack[-1]
                is_write_scope = scan_writes and (path, enclosing) in _WRITE_SCAN_FUNCTIONS
                if _is_subprocess_dispatch_call(node) or (
                    is_write_scope and _is_direct_write_call(node)
                ):
                    matches.append((enclosing, node.lineno))
            self.generic_visit(node)

    _Visitor().visit(tree)
    return matches


def _all_matches_by_file(path: Path, *, scan_writes: bool = False) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return _enclosing_function_matches(tree, path, scan_writes=scan_writes)


def test_every_matching_dispatch_site_is_classified():
    for path in (PUSH_PY, AGENT_PY, TASK_PY, PHASE_PY):
        for func_name, lineno in _all_matches_by_file(path, scan_writes=(path == AGENT_PY)):
            key = (path, func_name)
            if key in _MUST_BE_EMPTY:
                raise AssertionError(
                    f"UNKNOWN/forbidden dispatch found in routed function "
                    f"{path.name}:{func_name} at line {lineno} -- this function "
                    f"must not construct its own dispatch (Wave-1 routing)."
                )
            assert key in _CLASSIFICATION, (
                f"UNKNOWN mutation dispatch site: {path.name}:{func_name} "
                f"(line {lineno}) is not in the frozen 13-site classification -- "
                f"reconcile the inventory before adding coverage."
            )


def test_every_expected_site_still_present_with_min_count():
    counts: dict[tuple[Path, str], int] = {}
    for path in (PUSH_PY, AGENT_PY, TASK_PY, PHASE_PY):
        for func_name, _lineno in _all_matches_by_file(path, scan_writes=(path == AGENT_PY)):
            key = (path, func_name)
            counts[key] = counts.get(key, 0) + 1

    for key, expected_min in _EXPECTED_MIN_COUNTS.items():
        actual = counts.get(key, 0)
        assert actual >= expected_min, (
            f"expected at least {expected_min} dispatch call(s) in "
            f"{key[0].name}:{key[1]}, found {actual}"
        )


def test_routed_functions_contain_zero_independent_dispatch():
    for path in (PHASE_PY,):
        matches_by_func: dict[str, int] = {}
        for func_name, _lineno in _all_matches_by_file(path):
            matches_by_func[func_name] = matches_by_func.get(func_name, 0) + 1
        for key in _MUST_BE_EMPTY:
            if key[0] != path:
                continue
            assert matches_by_func.get(key[1], 0) == 0, (
                f"{path.name}:{key[1]} retains an independent dispatch call; "
                f"expected zero (routed through _dispatch_governed_push)"
            )


def test_no_fourteenth_site_elsewhere_in_src():
    """A repo-wide search (not just the four named files) must not turn
    up a new, unclassified git-mutation dispatch site."""
    src_dir = REPO_ROOT / "src" / "pcae"
    scoped = {PUSH_PY, AGENT_PY, TASK_PY, PHASE_PY}
    for path in sorted(src_dir.rglob("*.py")):
        if path in scoped:
            continue
        text = path.read_text(encoding="utf-8")
        if '"git"' not in text:
            continue
        tree = ast.parse(text, filename=str(path))
        matches = _enclosing_function_matches(tree, path)
        assert not matches, f"unexpected new git-mutation dispatch site outside scope: {path} {matches}"


def test_classification_covers_exactly_thirteen_conceptual_sites():
    """PU1,PU2 (2) + AG1,AG2,AG4,PH1 (4, WAVE1_GOVERNED) + AG3,AG5 (2,
    ROLLBACK_BLOCKED) + TK1,TK2,TK3 (3, TASK_FINISH_DEFERRED via 2
    functions) + PH2,PH3 (2, CANONICALLY_ROUTED, zero independent
    dispatch, routed into AG2's WAVE1_GOVERNED `_run_git_push`) = 13."""
    wave1_governed = sum(1 for v in _CLASSIFICATION.values() if v == "WAVE1_GOVERNED")
    existing_certified = sum(1 for v in _CLASSIFICATION.values() if v == "EXISTING_CERTIFIED")
    rollback_blocked = sum(1 for v in _CLASSIFICATION.values() if v == "ROLLBACK_BLOCKED")
    task_finish_deferred_functions = sum(
        1 for v in _CLASSIFICATION.values() if v == "TASK_FINISH_DEFERRED"
    )
    assert existing_certified == 2  # PU1, PU2
    assert wave1_governed == 4  # AG1 (_run_git_commit), AG2 (_run_git_push), AG4, PH1
    assert rollback_blocked == 2  # AG3, AG5
    assert task_finish_deferred_functions == 2  # run_task_finish (TK1+TK2), recover (TK3)
    assert len(_MUST_BE_EMPTY) == 2  # PH2, PH3 routed
