"""
Shell gate prototype — read-only command classifier (Phase 88P).

Classifies proposed shell commands and returns a structured gate decision.
Never executes command text. Never grants authorization.
"""
from __future__ import annotations

import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.gate_dry_run import _detect_task_contract


# ── Policy-forbidden files (independent of task contract) ──────────────────
_SGP_POLICY_FORBIDDEN_FILES: tuple[str, ...] = (
    "README.md",
    "docs/REAL_CAPTURED_TASKS.md",
    "docs/LINKEDIN_ARTICLE_DRAFT.md",
)

# ── Command categories from 88O §6 ────────────────────────────────────────
SGP_CATEGORIES: tuple[str, ...] = (
    "read_only_inspection",
    "test_execution",
    "pcae_governed_lifecycle",
    "pcae_governed_commit",
    "pcae_governed_push",
    "raw_git_commit",
    "raw_git_push",
    "force_push",
    "git_history_rewrite",
    "destructive_filesystem",
    "filesystem_write",
    "source_mutation",
    "test_mutation",
    "docs_mutation",
    "policy_forbidden_file_mutation",
    "backend_invocation",
    "prompt_send",
    "output_capture",
    "intake_adoption",
    "package_install",
    "network_access",
    "secret_access",
    "environment_mutation",
    "unknown",
)

# ── Decision values from 88O §7 ───────────────────────────────────────────
SGP_DECISIONS: tuple[str, ...] = (
    "allow_read_only",
    "allow_governed",
    "allow_test_execution",
    "requires_active_task",
    "requires_preflight",
    "requires_human_review",
    "requires_more_evidence",
    "blocked_by_missing_task",
    "blocked_by_scope",
    "blocked_by_policy_forbidden_file",
    "blocked_by_raw_git_commit",
    "blocked_by_raw_git_push",
    "blocked_by_force_push",
    "blocked_by_history_rewrite",
    "blocked_by_destructive_filesystem",
    "blocked_by_backend_policy",
    "blocked_by_prompt_policy",
    "blocked_by_adoption_policy",
    "blocked_by_test_run_lock",
    "blocked_by_failed_health",
    "blocked_by_failed_check",
    "blocked_by_failed_doctor",
    "blocked_by_push_check",
    "blocked_by_unknown_command",
    "deny",
    "unknown",
)

# ── Read-only inspection programs ─────────────────────────────────────────
_READ_ONLY_PROGRAMS: frozenset[str] = frozenset({
    "ls", "ll", "la", "pwd", "echo", "cat", "bat",
    "head", "tail", "less", "more", "wc",
    "file", "stat", "du", "df",
    "which", "type", "command",
    "date", "whoami", "id", "hostname", "uname",
    "env", "printenv",
    "diff", "cmp",
    "tree", "exa",
})

# ── Read-only git subcommands ──────────────────────────────────────────────
_GIT_READ_ONLY_SUBCOMMANDS: frozenset[str] = frozenset({
    "status", "log", "show", "diff", "branch", "tag",
    "remote", "stash", "describe", "shortlog",
    "ls-files", "ls-remote", "ls-tree",
    "rev-parse", "rev-list", "cat-file",
    "blame", "annotate",
    "config", "help", "version",
    "fetch",  # fetch is read-only from working-tree perspective
})

# ── Grep/search programs (read-only) ──────────────────────────────────────
_GREP_PROGRAMS: frozenset[str] = frozenset({
    "grep", "egrep", "fgrep", "rg", "ag", "ack", "ripgrep",
    "find", "locate",
})

# ── Package managers ───────────────────────────────────────────────────────
_PKG_PROGRAMS: frozenset[str] = frozenset({
    "pip", "pip3", "pip3.14",
    "brew", "apt", "apt-get", "yum", "dnf", "pacman",
    "npm", "npx", "yarn", "pnpm",
    "cargo", "gem", "go",
})

_PKG_INSTALL_VERBS: frozenset[str] = frozenset({
    "install", "add", "update", "upgrade", "i",
})

# ── Network programs ───────────────────────────────────────────────────────
_NETWORK_PROGRAMS: frozenset[str] = frozenset({
    "curl", "wget", "fetch",
    "ssh", "scp", "sftp", "rsync",
    "nc", "netcat", "ncat",
    "telnet", "ftp",
    "ping", "traceroute", "dig", "nslookup",
    "aws", "gcloud", "az", "heroku",
    "gh", "hub",
})

# ── Shell operator patterns ────────────────────────────────────────────────
_REDIRECT_OUT_RE = re.compile(r'(?<![<>])>{1,2}(?!=)')
_HEREDOC_RE = re.compile(r'<<[-\s]*\w+')
_PIPE_RE = re.compile(r'\|')

# ── File extension → category heuristic ───────────────────────────────────
_SRC_EXTENSIONS: frozenset[str] = frozenset({".py", ".js", ".ts", ".go", ".rs", ".c", ".cpp", ".h", ".java"})
_TEST_EXTENSIONS: frozenset[str] = frozenset({".py"})  # refined by path prefix

# ── Backend invocation programs ────────────────────────────────────────────
_BACKEND_PROGRAMS: frozenset[str] = frozenset({
    "claude", "claude-deepseek", "codex",
    "openai", "anthropic",
    "gemini", "vertex",
})

# ── Secret access programs ─────────────────────────────────────────────────
_SECRET_ACCESS_PROGRAMS: frozenset[str] = frozenset({
    "security",    # macOS keychain
    "keychain",
    "pass",        # Unix password manager
    "op",          # 1Password CLI
    "gpg",         # GnuPG
    "gopass",
    "bitwarden", "bw",
    "vault",       # HashiCorp Vault
})

# ── Sensitive file path prefixes (detected when read by cat/head/tail) ─────
_SECRET_FILE_PREFIXES: tuple[str, ...] = (
    "~/.ssh/",
    "~/.gnupg/",
    "~/.age/",
    "~/.config/age/",
    "~/.netrc",
    "~/.aws/credentials",
    "~/.aws/config",
    "~/.kube/config",
    "~/.docker/config.json",
    "/etc/shadow",
    "/etc/sudoers",
)

# ── Compound shell operators ───────────────────────────────────────────────
_COMPOUND_OPS: frozenset[str] = frozenset({"&&", "||", ";"})

# ── Category severity: lower = more dangerous, wins in compound/pipe ───────
_CATEGORY_SEVERITY: dict[str, int] = {
    "force_push": 1,
    "destructive_filesystem": 1,
    "policy_forbidden_file_mutation": 1,
    "git_history_rewrite": 1,
    "raw_git_push": 1,
    "raw_git_commit": 1,
    "backend_invocation": 2,
    "prompt_send": 2,
    "output_capture": 2,
    "intake_adoption": 2,
    "secret_access": 2,
    "environment_mutation": 3,
    "source_mutation": 3,
    "test_mutation": 3,
    "docs_mutation": 3,
    "filesystem_write": 4,
    "unknown": 5,
    "package_install": 6,
    "network_access": 6,
    "test_execution": 7,
    "pcae_governed_commit": 8,
    "pcae_governed_push": 8,
    "pcae_governed_lifecycle": 8,
    "read_only_inspection": 9,
}


def _safe_split(command_text: str) -> list[str]:
    """Best-effort shlex split; returns raw word split on failure."""
    try:
        return shlex.split(command_text)
    except ValueError:
        return command_text.split()


def _has_output_redirection(command_text: str) -> bool:
    """True if the command contains stdout redirection > or >>."""
    return bool(_REDIRECT_OUT_RE.search(command_text))


def _has_heredoc(command_text: str) -> bool:
    return bool(_HEREDOC_RE.search(command_text))


def _has_pipe(command_text: str) -> bool:
    return bool(_PIPE_RE.search(command_text))


def _redirection_target(command_text: str) -> str | None:
    """Return the first redirection target filename, if discernible."""
    m = re.search(r'>{1,2}\s*(\S+)', command_text)
    return m.group(1) if m else None


def _categorize_redirection_target(target: str | None) -> str:
    """Map a write-target path to a mutation category."""
    if target is None:
        return "filesystem_write"
    for pf in _SGP_POLICY_FORBIDDEN_FILES:
        if target == pf or target.endswith("/" + pf.split("/")[-1]):
            return "policy_forbidden_file_mutation"
    if target.startswith("src/") or target.startswith("./src/"):
        return "source_mutation"
    if target.startswith("tests/") or target.startswith("./tests/"):
        return "test_mutation"
    if target.startswith("docs/") or target.startswith("./docs/"):
        return "docs_mutation"
    return "filesystem_write"


def _is_expensive_pytest(tokens: list[str]) -> bool:
    """True if the pytest invocation uses -n (xdist parallel execution)."""
    return any(t.startswith("-n") or t == "--numprocesses" for t in tokens)


def _empty_flags() -> dict[str, bool]:
    """Return a fresh detected_flags dict with all fields False."""
    return {
        "read_only_detected": False,
        "filesystem_write_detected": False,
        "source_mutation_detected": False,
        "test_mutation_detected": False,
        "docs_mutation_detected": False,
        "policy_forbidden_file_detected": False,
        "raw_git_commit_detected": False,
        "raw_git_push_detected": False,
        "force_push_detected": False,
        "history_rewrite_detected": False,
        "destructive_filesystem_detected": False,
        "backend_invocation_detected": False,
        "prompt_send_detected": False,
        "capture_detected": False,
        "intake_adoption_detected": False,
        "package_install_detected": False,
        "network_access_detected": False,
        "secret_access_detected": False,
        "environment_mutation_detected": False,
        "test_execution_detected": False,
        "expensive_test_execution_detected": False,
    }


def _split_on_operators(tokens: list[str], ops: frozenset[str]) -> list[list[str]]:
    """Split token list at operator tokens; return non-empty segments."""
    segments: list[list[str]] = []
    current: list[str] = []
    for t in tokens:
        if t in ops:
            if current:
                segments.append(current)
            current = []
        else:
            current.append(t)
    if current:
        segments.append(current)
    return segments or [tokens]


def _find_tee_write_target(pipe_segments: list[list[str]]) -> str | None:
    """Return the first file path written by tee in a pipe chain, or None."""
    for seg in pipe_segments:
        if not seg:
            continue
        if seg[0] == "tee":
            for tok in seg[1:]:
                if not tok.startswith("-"):
                    return tok
    return None


def _most_restrictive_classification(
    classifications: list[dict[str, Any]],
) -> dict[str, Any]:
    """Pick the classification with the lowest (most dangerous) category severity."""
    if not classifications:
        return {"command_category": "unknown", "reason_codes": ["no_segments"], "detected_flags": _empty_flags()}
    result = classifications[0]
    for cls in classifications[1:]:
        sev_curr = _CATEGORY_SEVERITY.get(result["command_category"], 5)
        sev_new = _CATEGORY_SEVERITY.get(cls["command_category"], 5)
        if sev_new < sev_curr:
            result = cls
    return result


def _is_secret_file_access(args: list[str]) -> bool:
    """True if any argument looks like a sensitive credential file path."""
    for arg in args:
        for prefix in _SECRET_FILE_PREFIXES:
            if arg.startswith(prefix) or arg == prefix.rstrip("/"):
                return True
    return False


def _classify_single(command_text: str) -> dict[str, Any]:
    """
    Classify a single shell command (no compound operators or pipes).
    Returns a dict with keys: command_category, reason_codes, detected_flags.
    Does not touch the filesystem. Does not call subprocesses.
    """
    tokens = _safe_split(command_text)
    if not tokens:
        return {
            "command_category": "unknown",
            "reason_codes": ["empty_command"],
            "detected_flags": {},
        }

    program = tokens[0]
    # Strip leading path components (e.g. /usr/bin/git → git)
    program = program.rsplit("/", 1)[-1]

    reason_codes: list[str] = []
    flags: dict[str, bool] = {
        "read_only_detected": False,
        "filesystem_write_detected": False,
        "source_mutation_detected": False,
        "test_mutation_detected": False,
        "docs_mutation_detected": False,
        "policy_forbidden_file_detected": False,
        "raw_git_commit_detected": False,
        "raw_git_push_detected": False,
        "force_push_detected": False,
        "history_rewrite_detected": False,
        "destructive_filesystem_detected": False,
        "backend_invocation_detected": False,
        "prompt_send_detected": False,
        "capture_detected": False,
        "intake_adoption_detected": False,
        "package_install_detected": False,
        "network_access_detected": False,
        "secret_access_detected": False,
        "environment_mutation_detected": False,
        "test_execution_detected": False,
        "expensive_test_execution_detected": False,
    }

    # ── pcae governed commands ────────────────────────────────────────────
    if program == "pcae":
        subcommand = tokens[1] if len(tokens) > 1 else ""
        if subcommand == "commit":
            return {"command_category": "pcae_governed_commit",
                    "reason_codes": ["pcae_governed_commit_detected"],
                    "detected_flags": flags}
        if subcommand == "push":
            return {"command_category": "pcae_governed_push",
                    "reason_codes": ["pcae_governed_push_detected"],
                    "detected_flags": flags}
        # All other pcae subcommands are governed lifecycle
        return {"command_category": "pcae_governed_lifecycle",
                "reason_codes": ["pcae_governed_lifecycle_detected"],
                "detected_flags": flags}

    # ── git commands ──────────────────────────────────────────────────────
    if program == "git":
        subcmd = tokens[1] if len(tokens) > 1 else ""
        rest = tokens[2:]

        # force push — check before generic push
        if subcmd == "push":
            is_force = any(
                t in ("--force", "-f", "--force-with-lease", "--force-if-includes")
                for t in rest
            )
            if is_force:
                flags["force_push_detected"] = True
                flags["raw_git_push_detected"] = True
                return {"command_category": "force_push",
                        "reason_codes": ["force_push_detected"],
                        "detected_flags": flags}
            flags["raw_git_push_detected"] = True
            return {"command_category": "raw_git_push",
                    "reason_codes": ["raw_git_push_detected"],
                    "detected_flags": flags}

        if subcmd == "commit":
            flags["raw_git_commit_detected"] = True
            return {"command_category": "raw_git_commit",
                    "reason_codes": ["raw_git_commit_detected"],
                    "detected_flags": flags}

        if subcmd in ("rebase", "cherry-pick"):
            flags["history_rewrite_detected"] = True
            return {"command_category": "git_history_rewrite",
                    "reason_codes": ["git_history_rewrite_detected"],
                    "detected_flags": flags}

        if subcmd == "reset":
            is_hard = "--hard" in rest or "--mixed" in rest
            if is_hard:
                flags["history_rewrite_detected"] = True
                return {"command_category": "git_history_rewrite",
                        "reason_codes": ["git_reset_hard_detected"],
                        "detected_flags": flags}

        if subcmd == "clean":
            flags["destructive_filesystem_detected"] = True
            return {"command_category": "destructive_filesystem",
                    "reason_codes": ["git_clean_detected"],
                    "detected_flags": flags}

        if subcmd in _GIT_READ_ONLY_SUBCOMMANDS:
            flags["read_only_detected"] = True
            # Check for redirection even on read-only git commands
            if _has_output_redirection(command_text):
                redir_target = _redirection_target(command_text)
                cat = _categorize_redirection_target(redir_target)
                flags = {**flags, _flag_for_category(cat): True}
                return {"command_category": cat,
                        "reason_codes": ["git_read_redirected", f"redirection_to_{cat}"],
                        "detected_flags": flags}
            return {"command_category": "read_only_inspection",
                    "reason_codes": ["git_read_only_subcommand"],
                    "detected_flags": flags}

        # Unknown git subcommand
        return {"command_category": "unknown",
                "reason_codes": ["git_unknown_subcommand"],
                "detected_flags": flags}

    # ── rm ────────────────────────────────────────────────────────────────
    if program == "rm":
        is_recursive = any(
            t in ("-r", "-R", "-rf", "-fr", "-rf", "--recursive")
            or (t.startswith("-") and "r" in t and "f" in t)
            for t in tokens[1:]
        )
        if is_recursive:
            flags["destructive_filesystem_detected"] = True
            return {"command_category": "destructive_filesystem",
                    "reason_codes": ["rm_recursive_detected"],
                    "detected_flags": flags}
        flags["filesystem_write_detected"] = True
        return {"command_category": "filesystem_write",
                "reason_codes": ["rm_detected"],
                "detected_flags": flags}

    # ── cp, mv ────────────────────────────────────────────────────────────
    if program in ("cp", "mv"):
        flags["filesystem_write_detected"] = True
        return {"command_category": "filesystem_write",
                "reason_codes": [f"{program}_detected"],
                "detected_flags": flags}

    # ── mkdir, touch ─────────────────────────────────────────────────────
    if program in ("mkdir", "touch", "mktemp"):
        flags["filesystem_write_detected"] = True
        return {"command_category": "filesystem_write",
                "reason_codes": [f"{program}_detected"],
                "detected_flags": flags}

    # ── pytest ────────────────────────────────────────────────────────────
    is_pytest = (
        program in ("pytest", "py.test")
        or (program in ("python", "python3", "python3.14") and "-m" in tokens and "pytest" in tokens)
    )
    if is_pytest:
        flags["test_execution_detected"] = True
        expensive = _is_expensive_pytest(tokens)
        if expensive:
            flags["expensive_test_execution_detected"] = True
        reason_codes = ["test_execution_detected"]
        if expensive:
            reason_codes.append("expensive_test_execution_detected")
        return {"command_category": "test_execution",
                "reason_codes": reason_codes,
                "detected_flags": flags}

    # ── package managers ──────────────────────────────────────────────────
    if program in _PKG_PROGRAMS:
        verb = tokens[1] if len(tokens) > 1 else ""
        if verb in _PKG_INSTALL_VERBS:
            flags["package_install_detected"] = True
            return {"command_category": "package_install",
                    "reason_codes": ["package_install_detected"],
                    "detected_flags": flags}

    # python -m pip install / python -m build / python -m pipx install
    if program in ("python", "python3", "python3.14") and "-m" in tokens:
        m_idx = tokens.index("-m")
        if m_idx + 1 < len(tokens):
            module = tokens[m_idx + 1]
            if module in ("pip", "pip3", "pipx", "build") and (
                m_idx + 2 < len(tokens) and tokens[m_idx + 2] in _PKG_INSTALL_VERBS
            ):
                flags["package_install_detected"] = True
                return {"command_category": "package_install",
                        "reason_codes": ["python_m_pip_install_detected"],
                        "detected_flags": flags}

    # ── network programs ──────────────────────────────────────────────────
    if program in _NETWORK_PROGRAMS:
        flags["network_access_detected"] = True
        return {"command_category": "network_access",
                "reason_codes": ["network_program_detected"],
                "detected_flags": flags}

    # ── grep/search (read-only unless redirected) ─────────────────────────
    if program in _GREP_PROGRAMS:
        if _has_output_redirection(command_text):
            redir_target = _redirection_target(command_text)
            cat = _categorize_redirection_target(redir_target)
            flags = {**flags, _flag_for_category(cat): True}
            return {"command_category": cat,
                    "reason_codes": ["grep_redirected", f"redirection_to_{cat}"],
                    "detected_flags": flags}
        flags["read_only_detected"] = True
        return {"command_category": "read_only_inspection",
                "reason_codes": ["grep_read_only"],
                "detected_flags": flags}

    # ── pure read-only programs ───────────────────────────────────────────
    if program in _READ_ONLY_PROGRAMS:
        if _is_secret_file_access(tokens[1:]):
            flags["secret_access_detected"] = True
            return {"command_category": "secret_access",
                    "reason_codes": ["secret_file_read_detected"],
                    "detected_flags": flags}
        if _has_output_redirection(command_text):
            redir_target = _redirection_target(command_text)
            cat = _categorize_redirection_target(redir_target)
            flags = {**flags, _flag_for_category(cat): True}
            return {"command_category": cat,
                    "reason_codes": ["read_program_redirected", f"redirection_to_{cat}"],
                    "detected_flags": flags}
        flags["read_only_detected"] = True
        return {"command_category": "read_only_inspection",
                "reason_codes": ["read_only_program"],
                "detected_flags": flags}

    # ── sed (read-only only if -n / no -i; otherwise filesystem_write) ────
    if program == "sed":
        is_inplace = any(t.startswith("-i") or t == "--in-place" for t in tokens[1:])
        if is_inplace:
            # sed -i modifies files; classify by which file(s) targeted
            # look at last non-flag token as approximate target
            target = _last_path_argument(tokens)
            cat = _categorize_path_write(target)
            flags = {**flags, _flag_for_category(cat): True}
            return {"command_category": cat,
                    "reason_codes": ["sed_inplace_detected", f"writes_to_{cat}"],
                    "detected_flags": flags}
        if _has_output_redirection(command_text):
            redir_target = _redirection_target(command_text)
            cat = _categorize_redirection_target(redir_target)
            flags = {**flags, _flag_for_category(cat): True}
            return {"command_category": cat,
                    "reason_codes": ["sed_redirected", f"redirection_to_{cat}"],
                    "detected_flags": flags}
        flags["read_only_detected"] = True
        return {"command_category": "read_only_inspection",
                "reason_codes": ["sed_read_only"],
                "detected_flags": flags}

    # ── awk (read-only unless redirected or -i) ───────────────────────────
    if program == "awk":
        if _has_output_redirection(command_text):
            redir_target = _redirection_target(command_text)
            cat = _categorize_redirection_target(redir_target)
            flags = {**flags, _flag_for_category(cat): True}
            return {"command_category": cat,
                    "reason_codes": ["awk_redirected", f"redirection_to_{cat}"],
                    "detected_flags": flags}
        flags["read_only_detected"] = True
        return {"command_category": "read_only_inspection",
                "reason_codes": ["awk_read_only"],
                "detected_flags": flags}

    # ── filesystem permission/ownership modification ──────────────────────
    if program in ("chmod", "chown", "chgrp", "chattr"):
        flags["filesystem_write_detected"] = True
        return {"command_category": "filesystem_write",
                "reason_codes": [f"{program}_detected"],
                "detected_flags": flags}

    if program == "ln":
        flags["filesystem_write_detected"] = True
        return {"command_category": "filesystem_write",
                "reason_codes": ["ln_detected"],
                "detected_flags": flags}

    # ── shell environment mutation ─────────────────────────────────────────
    if program in ("export", "unset"):
        flags["environment_mutation_detected"] = True
        return {"command_category": "environment_mutation",
                "reason_codes": ["shell_export_detected"],
                "detected_flags": flags}

    if program in ("source", "."):
        flags["environment_mutation_detected"] = True
        return {"command_category": "environment_mutation",
                "reason_codes": ["shell_source_detected"],
                "detected_flags": flags}

    # VAR=val cmd prefix: first token is an env-var assignment
    if "=" in program and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', program):
        flags["environment_mutation_detected"] = True
        return {"command_category": "environment_mutation",
                "reason_codes": ["env_var_prefix_detected"],
                "detected_flags": flags}

    # ── backend invocation programs ───────────────────────────────────────
    if program in _BACKEND_PROGRAMS:
        flags["backend_invocation_detected"] = True
        return {"command_category": "backend_invocation",
                "reason_codes": ["backend_program_detected"],
                "detected_flags": flags}

    # ── secret access programs ────────────────────────────────────────────
    if program in _SECRET_ACCESS_PROGRAMS:
        flags["secret_access_detected"] = True
        return {"command_category": "secret_access",
                "reason_codes": ["secret_access_program_detected"],
                "detected_flags": flags}

    # ── shell redirection without known program ───────────────────────────
    if _has_output_redirection(command_text):
        redir_target = _redirection_target(command_text)
        cat = _categorize_redirection_target(redir_target)
        flags = {**flags, _flag_for_category(cat): True}
        return {"command_category": cat,
                "reason_codes": ["output_redirection_detected", f"redirection_to_{cat}"],
                "detected_flags": flags}

    if _has_heredoc(command_text):
        flags["filesystem_write_detected"] = True
        return {"command_category": "filesystem_write",
                "reason_codes": ["heredoc_detected"],
                "detected_flags": flags}

    # ── fallback: unknown ─────────────────────────────────────────────────
    return {"command_category": "unknown",
            "reason_codes": ["unknown_program"],
            "detected_flags": flags}


def _classify_command(command_text: str) -> dict[str, Any]:
    """
    Classify a shell command, handling compound operators and pipe chains.
    Delegates single commands to _classify_single.
    """
    tokens = _safe_split(command_text)
    if not tokens:
        return {"command_category": "unknown", "reason_codes": ["empty_command"], "detected_flags": _empty_flags()}

    # Compound operators (&&, ||, ;): classify each segment, take most restrictive
    if any(t in _COMPOUND_OPS for t in tokens):
        segments = _split_on_operators(tokens, _COMPOUND_OPS)
        if len(segments) > 1:
            classifications = [_classify_single(" ".join(seg)) for seg in segments]
            result = _most_restrictive_classification(classifications)
            return {**result, "reason_codes": ["compound_command_detected"] + result["reason_codes"]}

    # Pipe chains: detect tee write, otherwise take most restrictive segment
    if any(t == "|" for t in tokens):
        pipe_segments = _split_on_operators(tokens, {"|"})
        if len(pipe_segments) > 1:
            tee_target = _find_tee_write_target(pipe_segments)
            if tee_target is not None:
                cat = _categorize_redirection_target(tee_target)
                flags = _empty_flags()
                flags[_flag_for_category(cat)] = True
                return {"command_category": cat,
                        "reason_codes": ["pipe_tee_write_detected", f"tee_writes_to_{cat}"],
                        "detected_flags": flags}
            classifications = [_classify_single(" ".join(seg)) for seg in pipe_segments]
            result = _most_restrictive_classification(classifications)
            return {**result, "reason_codes": ["pipe_chain_detected"] + result["reason_codes"]}

    return _classify_single(command_text)


def _flag_for_category(cat: str) -> str:
    """Map a mutation category string to its detected_flags key."""
    _MAP = {
        "filesystem_write": "filesystem_write_detected",
        "source_mutation": "source_mutation_detected",
        "test_mutation": "test_mutation_detected",
        "docs_mutation": "docs_mutation_detected",
        "policy_forbidden_file_mutation": "policy_forbidden_file_detected",
    }
    return _MAP.get(cat, "filesystem_write_detected")


def _last_path_argument(tokens: list[str]) -> str | None:
    """Return the last non-flag token (heuristic for target file)."""
    for t in reversed(tokens[1:]):
        if not t.startswith("-"):
            return t
    return None


def _categorize_path_write(path: str | None) -> str:
    """Map a write target path to a mutation category."""
    if path is None:
        return "filesystem_write"
    for pf in _SGP_POLICY_FORBIDDEN_FILES:
        if path == pf:
            return "policy_forbidden_file_mutation"
    if path.startswith("src/") or path.startswith("./src/"):
        return "source_mutation"
    if path.startswith("tests/") or path.startswith("./tests/"):
        return "test_mutation"
    if path.startswith("docs/") or path.startswith("./docs/"):
        return "docs_mutation"
    return "filesystem_write"


def _decide(
    command_category: str,
    detected_flags: dict[str, bool],
    active_task_detected: bool,
    test_run_clear: bool,
) -> tuple[str, list[str]]:
    """
    Map category + context → (decision, reason_codes).
    Conservative: unknown/ambiguous → blocked_by_unknown_command.
    """
    reason_codes: list[str] = []

    # Hard blocks — unconditional
    if detected_flags.get("force_push_detected"):
        return "blocked_by_force_push", ["force_push_hard_block"]
    if detected_flags.get("raw_git_push_detected") or command_category == "raw_git_push":
        return "blocked_by_raw_git_push", ["raw_git_push_hard_block"]
    if detected_flags.get("raw_git_commit_detected") or command_category == "raw_git_commit":
        return "blocked_by_raw_git_commit", ["raw_git_commit_use_pcae_commit"]
    if detected_flags.get("history_rewrite_detected") or command_category == "git_history_rewrite":
        return "blocked_by_history_rewrite", ["git_history_rewrite_hard_block"]
    if detected_flags.get("destructive_filesystem_detected") or command_category == "destructive_filesystem":
        return "blocked_by_destructive_filesystem", ["destructive_filesystem_hard_block"]
    if detected_flags.get("policy_forbidden_file_detected") or command_category == "policy_forbidden_file_mutation":
        return "blocked_by_policy_forbidden_file", ["policy_forbidden_file_hard_block"]

    # Governed pcae commands
    if command_category == "pcae_governed_commit":
        return "allow_governed", ["pcae_governed_commit"]
    if command_category == "pcae_governed_push":
        return "allow_governed", ["pcae_governed_push"]
    if command_category == "pcae_governed_lifecycle":
        return "allow_governed", ["pcae_governed_lifecycle"]

    # Read-only
    if command_category == "read_only_inspection":
        return "allow_read_only", ["read_only_inspection_allowed"]

    # Test execution
    if command_category == "test_execution":
        if detected_flags.get("expensive_test_execution_detected"):
            if not test_run_clear:
                return "blocked_by_test_run_lock", ["test_run_lock_active"]
            reason_codes.append("expensive_test_run_preflight_required")
            if not active_task_detected:
                reason_codes.append("no_active_task")
                return "requires_active_task", reason_codes
            return "allow_test_execution", reason_codes + ["test_run_clear", "active_task_present"]
        # Non-expensive pytest
        if not active_task_detected:
            return "requires_active_task", ["no_active_task", "test_execution_requires_task"]
        return "allow_test_execution", ["test_execution_allowed"]

    # Package install
    if command_category == "package_install":
        return "requires_human_review", ["package_install_requires_human_review"]

    # Network access
    if command_category == "network_access":
        return "requires_human_review", ["network_access_requires_human_review"]

    # Mutation categories — require active task
    if command_category in ("filesystem_write", "source_mutation", "test_mutation", "docs_mutation"):
        if not active_task_detected:
            return "blocked_by_missing_task", ["no_active_task", f"{command_category}_requires_task"]
        return "requires_preflight", [f"{command_category}_requires_scope_preflight"]

    # Backend / prompt / capture / intake
    if command_category in ("backend_invocation", "prompt_send", "output_capture", "intake_adoption"):
        return "requires_human_review", [f"{command_category}_requires_human_review"]

    # Environment / secret
    if command_category in ("environment_mutation", "secret_access"):
        return "requires_human_review", [f"{command_category}_requires_human_review"]

    # Unknown — block by default
    return "blocked_by_unknown_command", ["unknown_command_deny_by_default"]


def _call_doctor_test_run(repo_root: Path) -> bool:
    """
    Call pcae doctor test-run read-only to check if tests are clear to run.
    Returns True (clear) on any failure to avoid blocking incorrectly.
    """
    try:
        import json
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "doctor", "test-run", "--json"],
            capture_output=True, text=True, cwd=str(repo_root), timeout=15,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return bool(data.get("clear_to_run", True))
    except Exception:
        pass
    return True  # conservative: assume clear on failure


def build_shell_gate(
    repo_root: Path,
    command_text: str,
) -> dict[str, Any]:
    """
    Build the shell gate JSON envelope for a proposed shell command.
    Never executes command_text. Never modifies files.
    """
    now = datetime.now(timezone.utc).isoformat()
    task_contract = _detect_task_contract(repo_root)
    active_task_detected = task_contract is not None
    task_contract_path: str | None = task_contract["path"] if task_contract else None

    classification = _classify_command(command_text)
    command_category: str = classification["command_category"]
    classify_reason_codes: list[str] = classification["reason_codes"]
    detected_flags: dict[str, bool] = classification["detected_flags"]

    # For expensive test execution, call doctor test-run (it is read-only)
    test_run_clear = True
    test_run_preflight_required = (
        command_category == "test_execution"
        and detected_flags.get("expensive_test_execution_detected", False)
    )
    if test_run_preflight_required:
        test_run_clear = _call_doctor_test_run(repo_root)

    decision, decision_reason_codes = _decide(
        command_category, detected_flags, active_task_detected, test_run_clear
    )

    reason_codes = classify_reason_codes + decision_reason_codes

    # Missing evidence items
    missing_evidence: list[str] = []
    if decision in ("requires_preflight", "requires_active_task", "requires_more_evidence"):
        if not active_task_detected:
            missing_evidence.append("active_task_contract")
        if command_category in ("source_mutation", "test_mutation", "docs_mutation", "filesystem_write"):
            missing_evidence.append("scope_preflight")
    if test_run_preflight_required and not test_run_clear:
        missing_evidence.append("test_run_clear_to_run")

    # Construct safety_notes
    safety_notes: dict[str, bool] = {
        "shell_gate_prototype_only": True,
        "shell_gate_does_not_execute_commands": True,
        "shell_gate_does_not_intercept_shell": True,
        "shell_gate_does_not_install_wrappers": True,
        "shell_gate_does_not_invoke_backends": True,
        "shell_gate_does_not_send_prompts": True,
        "shell_gate_does_not_capture_outputs": True,
        "shell_gate_does_not_perform_intake": True,
        "shell_gate_does_not_perform_adoption": True,
        "shell_gate_does_not_mutate_repo": True,
        "shell_gate_does_not_commit": True,
        "shell_gate_does_not_push": True,
        "shell_gate_does_not_write_storage": True,
        "permission_broker_not_implemented": True,
        "execution_authorization_not_granted": True,
    }

    # Evidence sources
    evidence_sources: list[str] = []
    if task_contract_path:
        evidence_sources.append(task_contract_path)
    if test_run_preflight_required:
        evidence_sources.append("pcae doctor test-run")

    shell_gate: dict[str, Any] = {
        "gate_type": "shell_gate_prototype",
        "command_text": command_text,
        "command_category": command_category,
        "decision": decision,
        "reason_codes": reason_codes,
        "active_task_detected": active_task_detected,
        "task_contract_path": task_contract_path,
        "requires_active_task": decision == "requires_active_task",
        "requires_preflight": decision == "requires_preflight",
        "requires_human_review": decision == "requires_human_review",
        "requires_more_evidence": decision == "requires_more_evidence",
        "hard_block_present": decision.startswith("blocked_by"),
        "read_only_detected": detected_flags.get("read_only_detected", False),
        "filesystem_write_detected": detected_flags.get("filesystem_write_detected", False),
        "source_mutation_detected": detected_flags.get("source_mutation_detected", False),
        "test_mutation_detected": detected_flags.get("test_mutation_detected", False),
        "docs_mutation_detected": detected_flags.get("docs_mutation_detected", False),
        "policy_forbidden_file_detected": detected_flags.get("policy_forbidden_file_detected", False),
        "raw_git_commit_detected": detected_flags.get("raw_git_commit_detected", False),
        "raw_git_push_detected": detected_flags.get("raw_git_push_detected", False),
        "force_push_detected": detected_flags.get("force_push_detected", False),
        "history_rewrite_detected": detected_flags.get("history_rewrite_detected", False),
        "destructive_filesystem_detected": detected_flags.get("destructive_filesystem_detected", False),
        "backend_invocation_detected": detected_flags.get("backend_invocation_detected", False),
        "prompt_send_detected": detected_flags.get("prompt_send_detected", False),
        "capture_detected": detected_flags.get("capture_detected", False),
        "intake_adoption_detected": detected_flags.get("intake_adoption_detected", False),
        "package_install_detected": detected_flags.get("package_install_detected", False),
        "network_access_detected": detected_flags.get("network_access_detected", False),
        "secret_access_detected": detected_flags.get("secret_access_detected", False),
        "environment_mutation_detected": detected_flags.get("environment_mutation_detected", False),
        "test_execution_detected": detected_flags.get("test_execution_detected", False),
        "expensive_test_execution_detected": detected_flags.get("expensive_test_execution_detected", False),
        "test_run_preflight_required": test_run_preflight_required,
        "test_run_clear_to_run": test_run_clear if test_run_preflight_required else None,
        "authorization_granted": False,
        "execution_authorized": False,
        "command_executed": False,
        "repo_mutation_performed": False,
        "backend_invocation_performed": False,
        "prompt_sent": False,
        "capture_performed": False,
        "intake_performed": False,
        "adoption_performed": False,
        "raw_git_push_performed": False,
        "force_push_performed": False,
        "storage_written": False,
        "evidence_sources": evidence_sources,
        "missing_evidence": missing_evidence,
        "safety_notes": safety_notes,
    }

    return {
        "schema_version": "0.1",
        "generated_at": now,
        "source_command": "pcae shell-gate check",
        "repository_root": str(repo_root),
        "shell_gate": shell_gate,
        "warnings": [],
        "errors": [],
        "safety_notes": safety_notes,
    }
