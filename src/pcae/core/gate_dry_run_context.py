"""Gate dry-run shared evidence context.

Provides lazy-memoized access to expensive governance evidence builders
within a single :func:`build_gate_dry_run` invocation.  Each property is
computed at most once per context instance.  The context is throw-away —
it never persists data, never caches across CLI invocations, and never
mutates global state.

Safety
------

* Immutable within one ``build_gate_dry_run`` call — repo state cannot
  change mid-call (single-threaded, synchronous).
* No cross-invocation caching.  Create a fresh ``GateDryRunContext`` per
  ``build_gate_dry_run`` call.
* No disk writes.  No ``.pcae`` cache files.
* Decision-neutral: replacing a direct builder call with a context
  property access must return the same data.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GateDryRunContext:
    """Lazy-memoized evidence cache for one gate dry-run evaluation.

    Create one instance per ``build_gate_dry_run`` call and pass it to
    ``_evaluate_gate`` and its sub-evaluators.  Properties are computed on
    first access and then cached for the lifetime of the instance.
    """

    repo_root: Path

    # -- private lazy caches --------------------------------------------------
    _artifact_index: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _memory_snapshot: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _governance_timeline: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _decision_log: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _risk_register: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _project_state: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _task_contract: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _git_porcelain: str | None = field(default=None, init=False, repr=False)
    _git_branch: str | None = field(default=None, init=False, repr=False)
    _git_ahead_count: int | None = field(default=None, init=False, repr=False)

    # -- lazy properties: governance evidence builders ------------------------

    @property
    def artifact_index(self) -> dict[str, Any]:
        if self._artifact_index is None:
            from pcae.core.artifact_index import build_artifact_index
            self._artifact_index = build_artifact_index(self.repo_root)
        return self._artifact_index

    @property
    def memory_snapshot(self) -> dict[str, Any]:
        if self._memory_snapshot is None:
            from pcae.core.memory_snapshot import build_memory_snapshot
            self._memory_snapshot = build_memory_snapshot(self.repo_root)
        return self._memory_snapshot

    @property
    def governance_timeline(self) -> dict[str, Any]:
        if self._governance_timeline is None:
            from pcae.core.governance_timeline import build_governance_timeline
            self._governance_timeline = build_governance_timeline(self.repo_root)
        return self._governance_timeline

    @property
    def decision_log(self) -> dict[str, Any]:
        if self._decision_log is None:
            from pcae.core.decision_log import build_decision_log
            self._decision_log = build_decision_log(self.repo_root)
        return self._decision_log

    @property
    def risk_register(self) -> dict[str, Any]:
        if self._risk_register is None:
            from pcae.core.risk_register import build_risk_register
            self._risk_register = build_risk_register(self.repo_root)
        return self._risk_register

    @property
    def project_state(self) -> dict[str, Any]:
        if self._project_state is None:
            from pcae.core.project_state import build_project_state
            self._project_state = build_project_state(self.repo_root)
        return self._project_state

    # -- lazy properties: task contract ---------------------------------------

    @property
    def task_contract(self) -> dict[str, Any] | None:
        """Active task contract, parsed once per dry-run invocation."""
        if self._task_contract is None:
            from pcae.core.gate_dry_run import _detect_task_contract
            self._task_contract = _detect_task_contract(self.repo_root)
        return self._task_contract

    # -- lazy properties: git metadata (used by commit/push evaluators) --------

    @property
    def git_porcelain(self) -> str | None:
        """Cached ``git status --porcelain`` output."""
        if self._git_porcelain is None:
            self._git_porcelain = _git_porcelain_raw(self.repo_root)
        return self._git_porcelain

    @property
    def git_branch(self) -> str | None:
        """Cached ``git branch --show-current`` output."""
        if self._git_branch is None:
            self._git_branch = _git_branch_raw(self.repo_root)
        return self._git_branch

    @property
    def git_ahead_count(self) -> int | None:
        """Cached ``git rev-list --count origin/main..HEAD`` output."""
        if self._git_ahead_count is None:
            self._git_ahead_count = _git_ahead_count_raw(self.repo_root)
        return self._git_ahead_count


# -- module-level helpers (not methods — avoid import-time coupling) ---------


def _git_porcelain_raw(repo_root: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _git_branch_raw(repo_root: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _git_ahead_count_raw(repo_root: Path) -> int | None:
    try:
        r = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if r.returncode == 0:
            return int(r.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None
