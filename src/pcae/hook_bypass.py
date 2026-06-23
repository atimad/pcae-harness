"""Hook-bypass policy formalization (Phase 79D).

Classifies hook-bypass events as bounded documented exceptions or blocking
violations. Hook bypass is forbidden by default and only accepted when
explicitly documented with bounded scope.
"""
from __future__ import annotations

from dataclasses import dataclass


BROAD_PATTERNS = frozenset({"*", "**", "src/**", "tests/**", "docs/**", "."})


@dataclass(frozen=True)
class HookBypassPolicy:
    status: str
    outcome: str
    bypass_detected: bool
    bypass_documented: bool
    bypass_reason: str
    expected_commit_message: str
    actual_commit_message: str
    allowed_files: tuple[str, ...]
    actual_files: tuple[str, ...]
    unexpected_files: tuple[str, ...]
    broad_scope_detected: bool
    hook_bypass_normalized: bool
    force_push_performed: bool
    raw_git_push_performed: bool
    backend_invocation_performed: bool
    runner_execute_performed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "actual_commit_message": self.actual_commit_message,
            "actual_files": list(self.actual_files),
            "allowed_files": list(self.allowed_files),
            "backend_invocation_performed": self.backend_invocation_performed,
            "blockers": list(self.blockers),
            "broad_scope_detected": self.broad_scope_detected,
            "bypass_detected": self.bypass_detected,
            "bypass_documented": self.bypass_documented,
            "bypass_reason": self.bypass_reason,
            "expected_commit_message": self.expected_commit_message,
            "force_push_performed": self.force_push_performed,
            "hook_bypass_normalized": self.hook_bypass_normalized,
            "hook_bypass_policy_outcome": self.outcome,
            "hook_bypass_policy_status": self.status,
            "raw_git_push_performed": self.raw_git_push_performed,
            "runner_execute_performed": self.runner_execute_performed,
            "unexpected_files": list(self.unexpected_files),
            "warnings": list(self.warnings),
        }


def evaluate_hook_bypass(
    bypass_detected: bool = False,
    bypass_documented: bool = False,
    bypass_reason: str = "",
    expected_commit_message: str = "",
    actual_commit_message: str = "",
    allowed_files: tuple[str, ...] | list[str] = (),
    actual_files: tuple[str, ...] | list[str] = (),
    hook_bypass_normalized: bool = False,
    force_push_performed: bool = False,
    raw_git_push_performed: bool = False,
    backend_invocation_performed: bool = False,
    runner_execute_performed: bool = False,
) -> HookBypassPolicy:
    bl: list[str] = []
    wl: list[str] = []
    allowed = tuple(allowed_files)
    actual = tuple(actual_files)

    if not bypass_detected:
        return HookBypassPolicy(
            status="no_bypass_detected", outcome="allowed",
            bypass_detected=False, bypass_documented=False,
            bypass_reason="", expected_commit_message="",
            actual_commit_message="", allowed_files=allowed,
            actual_files=actual, unexpected_files=(),
            broad_scope_detected=False, hook_bypass_normalized=False,
            force_push_performed=False, raw_git_push_performed=False,
            backend_invocation_performed=False, runner_execute_performed=False,
            blockers=(), warnings=(),
        )

    if hook_bypass_normalized:
        bl.append("Hook bypass has been normalized; this is not an acceptable workflow.")
        return _blocked("normalized_bypass", bl, wl, bypass_reason,
                        expected_commit_message, actual_commit_message,
                        allowed, actual, hook_bypass_normalized=True,
                        force_push_performed=force_push_performed,
                        raw_git_push_performed=raw_git_push_performed)

    if not bypass_documented:
        bl.append("Hook bypass is undocumented.")
        return _blocked("undocumented_bypass", bl, wl, bypass_reason,
                        expected_commit_message, actual_commit_message,
                        allowed, actual,
                        force_push_performed=force_push_performed,
                        raw_git_push_performed=raw_git_push_performed)

    broad = any(p in BROAD_PATTERNS for p in allowed)
    if broad:
        bl.append("Allowed file pattern is too broad.")
        return _blocked("broad_scope_bypass", bl, wl, bypass_reason,
                        expected_commit_message, actual_commit_message,
                        allowed, actual, broad_scope_detected=True,
                        force_push_performed=force_push_performed,
                        raw_git_push_performed=raw_git_push_performed)

    if expected_commit_message and actual_commit_message != expected_commit_message:
        bl.append(f"Expected commit message '{expected_commit_message}' but got '{actual_commit_message}'.")
        return _blocked("unexpected_commit_message", bl, wl, bypass_reason,
                        expected_commit_message, actual_commit_message,
                        allowed, actual,
                        force_push_performed=force_push_performed,
                        raw_git_push_performed=raw_git_push_performed)

    allowed_set = set(allowed)
    unexpected = tuple(sorted(f for f in actual if f not in allowed_set))
    if unexpected:
        bl.append(f"Unexpected files in bypass: {', '.join(unexpected)}")
        return _blocked("unexpected_files", bl, wl, bypass_reason,
                        expected_commit_message, actual_commit_message,
                        allowed, actual, unexpected=unexpected,
                        force_push_performed=force_push_performed,
                        raw_git_push_performed=raw_git_push_performed)

    if force_push_performed or raw_git_push_performed:
        if force_push_performed:
            bl.append("Force push was performed alongside hook bypass.")
        if raw_git_push_performed:
            bl.append("Raw git push was performed alongside hook bypass.")
        return _blocked("blocking", bl, wl, bypass_reason,
                        expected_commit_message, actual_commit_message,
                        allowed, actual,
                        force_push_performed=force_push_performed,
                        raw_git_push_performed=raw_git_push_performed)

    return HookBypassPolicy(
        status="documented_bounded_exception", outcome="allowed",
        bypass_detected=True, bypass_documented=True,
        bypass_reason=bypass_reason,
        expected_commit_message=expected_commit_message,
        actual_commit_message=actual_commit_message,
        allowed_files=allowed, actual_files=actual,
        unexpected_files=(), broad_scope_detected=False,
        hook_bypass_normalized=False,
        force_push_performed=False, raw_git_push_performed=False,
        backend_invocation_performed=backend_invocation_performed,
        runner_execute_performed=runner_execute_performed,
        blockers=(), warnings=(),
    )


def _blocked(
    status: str, bl: list, wl: list, reason: str,
    expected_msg: str, actual_msg: str,
    allowed: tuple, actual: tuple,
    unexpected: tuple = (),
    broad_scope_detected: bool = False,
    hook_bypass_normalized: bool = False,
    force_push_performed: bool = False,
    raw_git_push_performed: bool = False,
) -> HookBypassPolicy:
    return HookBypassPolicy(
        status=status, outcome="blocked",
        bypass_detected=True, bypass_documented=status != "undocumented_bypass",
        bypass_reason=reason,
        expected_commit_message=expected_msg,
        actual_commit_message=actual_msg,
        allowed_files=allowed, actual_files=actual,
        unexpected_files=unexpected,
        broad_scope_detected=broad_scope_detected,
        hook_bypass_normalized=hook_bypass_normalized,
        force_push_performed=force_push_performed,
        raw_git_push_performed=raw_git_push_performed,
        backend_invocation_performed=False,
        runner_execute_performed=False,
        blockers=tuple(bl), warnings=tuple(wl),
    )
