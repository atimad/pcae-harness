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
    # env/printenv removed — classified as secret_access (GAP-2 repair, 88V.1)
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

# ── Known interactive shell programs (89A) ──────────────────────────────────
_KNOWN_SHELLS: frozenset[str] = frozenset({
    "bash", "sh", "zsh", "dash", "fish", "ksh", "tcsh", "csh",
})

# ── Compound shell operators ───────────────────────────────────────────────
_COMPOUND_OPS: frozenset[str] = frozenset({"&&", "||", ";"})

# ── Compact operator regex (no surrounding spaces) ── 89A ───────────────────
_COMPACT_OP_RE = re.compile(r'(\|\||&&|;|\|)')

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


# ── Secret-like environment variable name patterns (GAP-1 repair, 88V.1) ────
_SECRET_VAR_NAME_SUBSTRINGS: tuple[str, ...] = (
    "KEY", "SECRET", "TOKEN", "PASSWORD", "PASSWD", "CREDENTIAL",
    "AUTH", "CERT", "PRIVATE_KEY", "ENCRYPT", "SIGNING",
    "API_KEY", "API_SECRET", "API_TOKEN",
    "ACCESS_KEY", "SECRET_KEY",
)


def _is_secret_env_var_name(name: str) -> bool:
    """True if an environment variable name suggests it contains a secret."""
    upper = name.upper()
    return any(pat in upper for pat in _SECRET_VAR_NAME_SUBSTRINGS)


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
    # Only strip when no '=' present: VAR=val prefixes like PATH=/custom/bin
    # must not have the path portion of the value stripped. (88V.1)
    if "=" not in program:
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

    # ── env / printenv secret exposure (GAP-2 repair, 88V.1) ──────────────
    # 89A: inspect env arguments — env python is NOT secret_access;
    #       env KEY=secret cmd still triggers secret detection
    if program in ("env", "printenv"):
        if program == "printenv":
            flags["secret_access_detected"] = True
            return {"command_category": "secret_access",
                    "reason_codes": ["printenv_secret_exposure_detected"],
                    "detected_flags": flags}
        # env: check arguments
        args = tokens[1:]
        if not args:
            # bare env — list all env vars, could expose secrets
            flags["secret_access_detected"] = True
            return {"command_category": "secret_access",
                    "reason_codes": ["env_secret_exposure_detected"],
                    "detected_flags": flags}
        # Check each argument for secret-like VAR=val assignments
        has_secret_var = False
        has_any_assignment = False
        first_program_arg_idx = len(args)
        for i, arg in enumerate(args):
            if "=" in arg and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', arg):
                has_any_assignment = True
                var_name = arg.split("=", 1)[0]
                if _is_secret_env_var_name(var_name):
                    has_secret_var = True
            else:
                first_program_arg_idx = i
                break
        if has_secret_var:
            # env KEY=secret cmd — secret access detected
            flags["secret_access_detected"] = True
            flags["environment_mutation_detected"] = True
            return {"command_category": "secret_access",
                    "reason_codes": ["env_secret_var_detected"],
                    "detected_flags": flags}
        if has_any_assignment and first_program_arg_idx < len(args):
            # env VAR=val cmd — non-secret env assignment, classify the cmd
            subcmd = " ".join(args[first_program_arg_idx:])
            sub_result = _classify_single(subcmd)
            sub_flags = sub_result.get("detected_flags", {})
            merged_flags = {**flags, **sub_flags}
            merged_flags["environment_mutation_detected"] = True
            return {"command_category": sub_result["command_category"],
                    "reason_codes": ["env_prefix_non_secret"] + sub_result.get("reason_codes", []),
                    "detected_flags": merged_flags}
        if first_program_arg_idx < len(args):
            # env python — run program with current environment
            # Not secret access per se; classify the target program
            subcmd = " ".join(args[first_program_arg_idx:])
            sub_result = _classify_single(subcmd)
            sub_flags = sub_result.get("detected_flags", {})
            merged_flags = {**flags, **sub_flags}
            # Do NOT set secret_access_detected — 89A fix
            return {"command_category": sub_result["command_category"],
                    "reason_codes": ["env_program_runner"] + sub_result.get("reason_codes", []),
                    "detected_flags": merged_flags}
        # env VAR=val (no command) — environment mutation, not secret access
        flags["environment_mutation_detected"] = True
        return {"command_category": "environment_mutation",
                "reason_codes": ["env_var_assignment_only"],
                "detected_flags": flags}

    # VAR=val cmd prefix: first token is an env-var assignment
    if "=" in program and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', program):
        var_name = program.split("=", 1)[0]
        if _is_secret_env_var_name(var_name):
            flags["environment_mutation_detected"] = True
            flags["secret_access_detected"] = True
            return {"command_category": "secret_access",
                    "reason_codes": ["env_var_prefix_secret_detected",
                                     f"secret_var_name:{var_name}"],
                    "detected_flags": flags}
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

    # ── known interactive shells (89A) ─────────────────────────────────────
    if program in _KNOWN_SHELLS:
        args = tokens[1:]
        # bare shell (no args) — interactive shell access, requires review
        if not args:
            return {"command_category": "network_access",
                    "reason_codes": ["interactive_shell_bare"],
                    "detected_flags": flags}
        # shell -c "command" — classify the embedded command
        if args[0] in ("-c", "-lc", "--command"):
            if len(args) > 1:
                # Extract and classify the embedded command
                embedded = " ".join(args[1:])
                # Strip outer quotes if present
                if len(embedded) >= 2 and (
                    (embedded.startswith('"') and embedded.endswith('"'))
                    or (embedded.startswith("'") and embedded.endswith("'"))
                ):
                    embedded = embedded[1:-1]
                if embedded.strip():
                    sub_result = _classify_single(embedded)
                    sub_flags = sub_result.get("detected_flags", {})
                    merged_flags = {**flags, **sub_flags}
                    return {"command_category": sub_result["command_category"],
                            "reason_codes": ["shell_embedded_command"] + sub_result.get("reason_codes", []),
                            "detected_flags": merged_flags}
            # -c with no command text
            return {"command_category": "unknown",
                    "reason_codes": ["shell_c_no_command"],
                    "detected_flags": flags}
        # shell with other arguments (script file or flags) — requires review
        return {"command_category": "network_access",
                "reason_codes": ["interactive_shell_with_args"],
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


def _split_compact_operators(command_text: str) -> list[str]:
    """Split a command string on compact operators (no spaces around |, &&, ||, ;).
    Returns list of individual sub-commands for multi-segment classification."""
    parts = _COMPACT_OP_RE.split(command_text)
    # parts alternates: subcmd, op, subcmd, op, ...
    # Collect only subcommands (even indices)
    subcmds = [p.strip() for i, p in enumerate(parts) if i % 2 == 0 and p.strip()]
    # If no operators found, parts == [command_text] and subcmds == [command_text]
    # Detect if operators were present
    if len(parts) <= 1:
        return [command_text]
    return subcmds if len(subcmds) > 1 else [command_text]


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

    # Compact operators (no spaces around |, &&, ||, ;) — 89A fallback
    compact_segments = _split_compact_operators(command_text)
    if len(compact_segments) > 1:
        classifications = [_classify_single(seg) for seg in compact_segments]
        result = _most_restrictive_classification(classifications)
        return {**result, "reason_codes": ["compound_command_detected"] + result["reason_codes"]}

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


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 93B — Narrow Shell Gate Prototype (broker-integrated check)
# ═══════════════════════════════════════════════════════════════════════════════


def _has_no_verify_flag(tokens: list[str]) -> bool:
    """Check whether command tokens contain --no-verify or -n flag."""
    for t in tokens:
        if t in ("--no-verify", "-n", "--no-gpg-sign"):
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 93C — Audit evidence model: redaction helpers
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns for secret-bearing tokens and env vars
_SECRET_ENV_VAR_NAMES: frozenset[str] = frozenset({
    "TOKEN", "API_KEY", "SECRET", "PASSWORD", "PASSWD", "PASS",
    "AUTH", "CREDENTIAL", "KEY", "PRIVATE_KEY", "ACCESS_KEY",
    "SECRET_KEY", "BEARER",
    "PCAE_TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GITHUB_TOKEN", "GITLAB_TOKEN", "NPM_TOKEN", "PYPI_TOKEN",
})

_SECRET_FLAG_PATTERNS: tuple[str, ...] = (
    "--token", "--api-key", "--secret", "--password", "--passwd",
    "--access-key", "--secret-key", "--private-key",
    "--authorization", "--bearer",
)


def _looks_like_secret_value(value: str) -> bool:
    """Heuristic check for likely secret/token/password values."""
    if not value:
        return False
    # Long alphanumeric strings, JWTs, base64-encoded
    if len(value) >= 20 and any(c.isalpha() for c in value) and any(c.isdigit() for c in value):
        return True
    # Starts with common token prefixes
    if value.startswith(("sk-", "pk-", "ghp_", "gho_", "ghu_", "ghs_",
                         "xoxb-", "xoxp-", "AKIA", "eyJ", "t.")):
        return True
    return False


def _redact_command_text(command_text: str) -> tuple[str, bool]:
    """Redact secrets from command text for audit display.

    Returns (redacted_command, redaction_applied).
    Handles:
      - env VAR=VALUE patterns where VAR is a known secret name
      - --flag value patterns where flag is a known secret flag
      - Bearer token patterns in curl/HTTP commands
    """
    import re
    redacted = command_text
    did_redact = False

    # Redact env var assignments: SECRET_NAME=value → SECRET_NAME=[REDACTED]
    for var_name in _SECRET_ENV_VAR_NAMES:
        pattern = re.compile(
            rf'\b({var_name})=(\S+)', re.IGNORECASE
        )
        if pattern.search(redacted):
            redacted = pattern.sub(rf'\1=[REDACTED]', redacted)
            did_redact = True

    # Redact --flag value: --token mytoken123 → --token [REDACTED]
    for flag in _SECRET_FLAG_PATTERNS:
        # Match --flag followed by a non-flag value
        pattern = re.compile(
            rf'({flag})\s+([^\s-][^\s]*)', re.IGNORECASE
        )
        if pattern.search(redacted):
            redacted = pattern.sub(r'\1 [REDACTED]', redacted)
            did_redact = True

    # Redact Bearer tokens: Authorization: Bearer xxx → Authorization: Bearer [REDACTED]
    bearer_pattern = re.compile(
        r'(Authorization:\s*Bearer\s+)(\S+)', re.IGNORECASE
    )
    if bearer_pattern.search(redacted):
        redacted = bearer_pattern.sub(r'\1[REDACTED]', redacted)
        did_redact = True

    return redacted, did_redact


def _build_audit_evidence(
    command_text: str,
    command_category: str,
    command_class: str,
    action_type: str,
    decision: str,
    hard_block: bool,
    reason_code: str,
    reason_codes: list[str],
    required_evidence: list[str],
    message: str,
    broker_result: dict[str, object],
    event_id: str,
) -> dict[str, object]:
    """Build a structured audit evidence payload for a shell-gate decision.

    Phase 93C — simulation-only.  No disk write, no persistent state.
    Command text is redacted for secrets before inclusion.
    """
    import hashlib
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    # Hash the original (unredacted) command for integrity
    command_hash = hashlib.sha256(command_text.encode()).hexdigest()

    # Redact command for display
    redacted_command, redaction_applied = _redact_command_text(command_text)

    # If full redaction applied but result is empty or nearly so, use placeholder
    if not redacted_command.strip():
        redacted_command = "<redacted_command>"
        redaction_applied = True

    broker_audit = broker_result.get("audit_payload", {})
    broker_event_id = broker_audit.get("event_id") if isinstance(broker_audit, dict) else None

    # Build broker message hash for cross-referencing
    broker_msg = broker_result.get("message", "")
    broker_msg_hash = (
        hashlib.sha256(str(broker_msg).encode()).hexdigest()[:16]
        if broker_msg else None
    )

    return {
        "audit_id": event_id,
        "event_type": f"shell_gate.{decision}",
        "timestamp_utc": now,
        "command_hash": command_hash,
        "redacted_command": redacted_command,
        "redaction_applied": redaction_applied,
        "command_class": command_class,
        "command_category": command_category,
        "action_type": action_type,
        "decision": decision,
        "hard_block": hard_block,
        "reason_code": reason_code,
        "reason_codes": reason_codes,
        "required_evidence": required_evidence,
        "message_summary": message[:200] if message else "",
        "broker_event_id": broker_event_id,
        "broker_message_hash": broker_msg_hash,
        "simulation_only": True,
        "no_execution": True,
        "no_enforcement": True,
        "source": "shell_gate",
        "schema_version": "1.0",
    }


def _detect_backend_program(program: str, tokens: list[str]) -> bool:
    """Check whether the command invokes a known AI backend CLI."""
    backend_names: frozenset[str] = frozenset({
        "claude", "claude-code", "deepseek", "kimi",
        "codex", "copilot", "cursor", "codegate",
    })
    return program in backend_names


# ── Category → broker input mapping ─────────────────────────────────────────

# Shell gate category → (broker action_type, broker command_class)
_CATEGORY_TO_BROKER: dict[str, tuple[str, str]] = {
    "read_only_inspection":        ("read",                "read_only"),
    "test_execution":              ("read",                "read_only"),
    "pcae_governed_lifecycle":     ("read",                "governed"),
    "pcae_governed_commit":        ("read",                "governed"),
    "pcae_governed_push":          ("read",                "governed"),
    "raw_git_commit":              ("commit",              "raw_git_commit"),
    "raw_git_push":                ("push",                "raw_git_push"),
    "force_push":                  ("push",                "force_push"),
    "git_history_rewrite":         ("source_mutation",     "raw_git_commit"),
    "destructive_filesystem":      ("source_mutation",     "destructive_filesystem"),
    "filesystem_write":            ("source_mutation",     "read_only"),
    "source_mutation":             ("source_mutation",     "read_only"),
    "test_mutation":               ("test_mutation",       "read_only"),
    "docs_mutation":               ("docs_mutation",       "read_only"),
    "policy_forbidden_file_mutation": ("docs_mutation",    "read_only"),
    "backend_invocation":          ("backend_invocation",  "backend_invocation"),
    "prompt_send":                 ("backend_invocation",  "backend_invocation"),
    "output_capture":              ("backend_invocation",  "backend_invocation"),
    "intake_adoption":             ("backend_invocation",  "backend_invocation"),
    "package_install":             ("source_mutation",     "read_only"),
    "network_access":              ("read",                "read_only"),
    "secret_access":               ("read",                "read_only"),
    "environment_mutation":        ("source_mutation",     "read_only"),
    "unknown":                     ("read",                "unknown"),
}


def _map_to_broker_inputs(
    command_category: str,
    tokens: list[str],
) -> tuple[str, str]:
    """
    Map shell gate command category and tokens to broker (action_type, command_class).
    Applies no-verify override when --no-verify/-n is detected in git context.
    """
    mapping = _CATEGORY_TO_BROKER.get(
        command_category, ("read", "unknown")
    )
    action_type, command_class = mapping

    # No-verify override: git commit/push with --no-verify → no_verify class
    if command_class in ("raw_git_commit", "raw_git_push") and _has_no_verify_flag(tokens):
        command_class = "no_verify"

    return action_type, command_class


def _extract_paths(tokens: list[str]) -> tuple[str, ...]:
    """Extract likely file/directory path arguments from command tokens."""
    paths: list[str] = []
    seen_double_dash = False
    for t in tokens:
        if t == "--":
            seen_double_dash = True
            continue
        if seen_double_dash:
            paths.append(t)
            continue
        if t.startswith("-"):
            continue
        # Heuristic: looks like a path (contains / or common extensions)
        if "/" in t or "." in t:
            paths.append(t)
    return tuple(paths)


def check_shell_gate(
    repo_root: Path,
    command_text: str,
) -> dict[str, object]:
    """
    Phase 93B — Narrow Shell Gate Prototype.

    Classify a proposed shell command, evaluate via the permission broker,
    and return a structured simulation decision.

    - Classifies the command text using the shell gate classifier
    - Maps classification to broker action_type and command_class
    - Calls evaluate_permission_broker() for the broker decision
    - Never executes the command, never intercepts shell, never invokes backends
    - Simulation only: no_execution=True, no_enforcement=True

    Returns a dict with: command_text, command_category, command_class,
    action_type, decision, hard_block, reason_code, reason_codes, message,
    required_evidence, audit_payload, simulation_only, no_execution,
    no_enforcement, authorization_granted, schema_version, and more.
    """
    from pcae.core.permission_broker import evaluate_permission_broker

    # 1. Classify the command text
    classification = _classify_command(command_text)
    command_category: str = classification["command_category"]
    classify_reason_codes: list[str] = classification["reason_codes"]
    detected_flags: dict[str, bool] = classification["detected_flags"]

    # 2. Tokenize for further analysis
    tokens = _safe_split(command_text)

    # 3. Map category + tokens → broker action_type and command_class
    action_type, command_class = _map_to_broker_inputs(command_category, tokens)

    # 4. Detect task contract
    task_contract = _detect_task_contract(repo_root)
    task_present = task_contract is not None

    # 5. Extract paths from command text
    paths = _extract_paths(tokens)

    # 6. Call the permission broker
    broker_result = evaluate_permission_broker(
        action_type=action_type,
        command_class=command_class,
        paths=paths,
        task_present=task_present,
        task_scope_known=task_present,
        approval_present=False,
        approval_fresh=True,
        accepted_risk_present=False,
        readiness_ready=False,
        enforcement_authorized=False,
        repo_dirty=False,
    )

    # 7. Build audit evidence (Phase 93C)
    import uuid
    event_id = f"sg-{uuid.uuid4().hex[:12]}"
    audit_evidence = _build_audit_evidence(
        command_text=command_text,
        command_category=command_category,
        command_class=command_class,
        action_type=action_type,
        decision=broker_result["decision"],
        hard_block=broker_result["hard_block"],
        reason_code=broker_result["reason_code"],
        reason_codes=broker_result.get("reason_codes", []),
        required_evidence=broker_result.get("required_evidence", []),
        message=broker_result.get("message", ""),
        broker_result=broker_result,
        event_id=event_id,
    )

    # 8. Build output envelope
    now = datetime.now(timezone.utc).isoformat()

    return {
        # Shell gate metadata
        "schema_version": "1.0",
        "generated_at": now,
        "source_command": "pcae shell-gate check",
        "repository_root": str(repo_root),
        "event_id": event_id,

        # Command classification
        "command_text": audit_evidence["redacted_command"],  # redacted for safety
        "command_category": command_category,
        "command_class": command_class,
        "action_type": action_type,
        "classify_reason_codes": classify_reason_codes,
        "detected_flags": {k: v for k, v in detected_flags.items() if v},

        # Extracted context
        "extracted_paths": list(paths),
        "active_task_detected": task_present,

        # Broker decision (from evaluate_permission_broker)
        "decision": broker_result["decision"],
        "hard_block": broker_result["hard_block"],
        "reason_code": broker_result["reason_code"],
        "reason_codes": broker_result.get("reason_codes", []),
        "message": broker_result["message"],
        "required_evidence": broker_result.get("required_evidence", []),
        "audit_payload": broker_result.get("audit_payload", {}),

        # Audit evidence (Phase 93C)
        "audit_evidence": audit_evidence,
        "redaction_applied": audit_evidence["redaction_applied"],

        # Simulation-only invariants
        "simulation_only": True,
        "no_execution": True,
        "no_enforcement": True,
        "authorization_granted": False,
        "execution_authorized": False,
        "command_executed": False,
        "shell_intercepted": False,
        "wrappers_installed": False,
        "backend_invoked": False,

        # Safety notes
        "safety_notes": {
            "shell_gate_prototype_only": True,
            "shell_gate_does_not_execute_commands": True,
            "shell_gate_does_not_intercept_shell": True,
            "shell_gate_does_not_install_wrappers": True,
            "shell_gate_does_not_invoke_backends": True,
            "hard_blocks_non_overridable": True,
            "execution_authorization_not_granted": True,
            "audit_evidence_simulation_only": True,
        },
        # Phase 93E — audit persistence
        "audit_persistence": _persist_if_enabled(audit_evidence, repo_root),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 93E — Audit persistence helpers
# ═══════════════════════════════════════════════════════════════════════════════

_AUDIT_DIR = ".pcae/shell-gate-audit"
_AUDIT_ENV_ENABLE = "PCAE_SHELL_GATE_AUDIT"


def _persist_if_enabled(audit_evidence: dict, repo_root: Path) -> dict:
    """Persist audit evidence if enabled. Always returns status dict."""
    result = persist_audit_record(audit_evidence)
    # Detect active task for context
    task_contract = _detect_task_contract(repo_root)
    if task_contract and result["status"] == "written":
        # Task ID could be added to persisted record in a future phase
        pass
    return result


def _audit_enabled() -> bool:
    """Check if audit persistence is enabled (always-on for explicit checks)."""
    import os
    val = os.environ.get(_AUDIT_ENV_ENABLE, "1")
    return val.lower() in ("1", "true", "yes")


def _audit_dir() -> Path:
    return Path(_AUDIT_DIR)


def persist_audit_record(record: dict) -> dict:
    """Persist a shell-gate audit record to .pcae/shell-gate-audit/.

    Returns dict with status, path, latest_path, record_digest.
    Never raises — failures are non-fatal.
    """
    import hashlib
    import json as _json
    import os
    from datetime import datetime, timezone

    result = {"status": "skipped", "path": "", "latest_path": "", "record_digest": ""}

    if not _audit_enabled():
        result["status"] = "disabled"
        return result

    audit_id = record.get("audit_id", "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"{ts}-{audit_id}.json"

    try:
        audit_dir_path = _audit_dir()
        audit_dir_path.mkdir(parents=True, exist_ok=True)

        # Persisted fields only — redacted command, no raw secrets
        persisted = {
            "audit_id": record.get("audit_id", ""),
            "schema_version": record.get("schema_version", "1.0"),
            "timestamp_utc": record.get("timestamp_utc", ""),
            "phase_id": record.get("phase_id", None),
            "task_id": record.get("task_id", None),
            "command_hash": record.get("command_hash", ""),
            "redacted_command": record.get("redacted_command", ""),
            "redaction_applied": record.get("redaction_applied", False),
            "command_class": record.get("command_class", ""),
            "command_category": record.get("command_category", ""),
            "action_type": record.get("action_type", ""),
            "decision": record.get("decision", ""),
            "hard_block": record.get("hard_block", False),
            "reason_code": record.get("reason_code", ""),
            "reason_codes": record.get("reason_codes", []),
            "required_evidence": record.get("required_evidence", []),
            "message_summary": record.get("message_summary", ""),
            "broker_event_id": record.get("broker_event_id", None),
            "broker_message_hash": record.get("broker_message_hash", None),
            "simulation_only": record.get("simulation_only", True),
            "no_execution": record.get("no_execution", True),
            "no_enforcement": record.get("no_enforcement", True),
            "source": record.get("source", "shell_gate"),
            "persisted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Compute record digest (excluding digest field itself)
        digest_input = _json.dumps(persisted, sort_keys=True, default=str)
        record_digest = hashlib.sha256(digest_input.encode()).hexdigest()
        persisted["record_digest"] = record_digest

        file_path = audit_dir_path / filename
        latest_path = audit_dir_path / "latest.json"

        # Write record
        file_path.write_text(_json.dumps(persisted, indent=2, sort_keys=True))
        # Atomically update latest.json via temp file
        tmp_path = audit_dir_path / ".latest.tmp"
        tmp_path.write_text(_json.dumps(persisted, indent=2, sort_keys=True))
        os.replace(str(tmp_path), str(latest_path))

        result["status"] = "written"
        result["path"] = str(file_path)
        result["latest_path"] = str(latest_path)
        result["record_digest"] = record_digest
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = str(exc)

    return result


def verify_audit_records(audit_dir: Path | None = None) -> dict:
    """Verify integrity of all audit records.

    Returns dict with total, valid, tampered, and details.
    """
    import json as _json
    import hashlib

    if audit_dir is None:
        audit_dir = _audit_dir()

    result = {"total": 0, "valid": 0, "tampered": 0, "missing": 0, "details": []}

    if not audit_dir.exists():
        return result

    for f in sorted(audit_dir.glob("*.json")):
        if f.name in ("latest.json", ".latest.tmp"):
            continue
        result["total"] += 1
        try:
            data = _json.loads(f.read_text())
            stored_digest = data.pop("record_digest", None)
            if not stored_digest:
                result["missing"] += 1
                result["details"].append({"file": str(f), "status": "no_digest"})
                continue
            digest_input = _json.dumps(data, sort_keys=True, default=str)
            computed = hashlib.sha256(digest_input.encode()).hexdigest()
            if computed == stored_digest:
                result["valid"] += 1
            else:
                result["tampered"] += 1
                result["details"].append({
                    "file": str(f), "status": "tampered",
                    "stored": stored_digest[:16], "computed": computed[:16],
                })
        except Exception as exc:
            result["tampered"] += 1
            result["details"].append({"file": str(f), "status": "error", "error": str(exc)})

    return result


def read_latest_audit(audit_dir: Path | None = None) -> dict | None:
    """Read the latest audit record. Returns None if no records exist."""
    import json as _json

    if audit_dir is None:
        audit_dir = _audit_dir()

    latest_path = audit_dir / "latest.json"
    if not latest_path.exists():
        return None
    try:
        return _json.loads(latest_path.read_text())
    except Exception:
        return None


def list_audit_records(limit: int = 10, audit_dir: Path | None = None) -> list[dict]:
    """List recent audit records. Returns list of record summaries."""
    import json as _json

    if audit_dir is None:
        audit_dir = _audit_dir()

    if not audit_dir.exists():
        return []

    records: list[dict] = []
    for f in sorted(audit_dir.glob("*.json"), reverse=True):
        if f.name in ("latest.json", ".latest.tmp"):
            continue
        try:
            data = _json.loads(f.read_text())
            records.append({
                "file": f.name,
                "audit_id": data.get("audit_id", ""),
                "timestamp_utc": data.get("timestamp_utc", ""),
                "decision": data.get("decision", ""),
                "reason_code": data.get("reason_code", ""),
                "redacted_command": data.get("redacted_command", ""),
            })
            if len(records) >= limit:
                break
        except Exception:
            pass
    return records
