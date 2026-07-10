"""Phase 134B.3 — canonical, channel-agnostic delivery-configuration resolver.

Investigation (134B.3 Part I) found delivery configuration read directly
from ``os.environ`` at eleven independent call sites across six files, with
no automatic path other than manually sourcing a shell environment file
(``~/.config/pcae/telegram.env``) in the same command chain as governed
finalization. That dependency is what this module removes.

This module does not change what any of those eleven call sites read --
they still read plain ``os.environ`` entries such as ``PCAE_NOTIFY_ENABLED``
and ``PCAE_TELEGRAM_BOT_TOKEN``, unchanged. It adds exactly one thing before
any of them run: a fail-closed, deterministic step that populates
``os.environ`` from a governed local configuration file when the operator
has not already supplied those variables through the shell. Explicit
environment always wins; the file is a convenience fallback, resolved fresh
for every process (including every subprocess), so no shell inheritance
chain is required for correctness.

The configuration file is a flat JSON object of ``PCAE_``-prefixed keys and
string values -- deliberately not a structured multi-adapter schema, so a
future delivery channel's own environment-variable names work through this
same resolver without any change here (Core Question 9 / 134B.2's
channel-agnostic invariant, extended to configuration resolution).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Explicit escape hatch: governed test isolation (tests/conftest.py) sets
# this so that no test process -- and no subprocess a test spawns -- ever
# auto-loads real delivery configuration from disk, regardless of what the
# operator's actual config file contains. This is checked *before* anything
# else; when set, resolution is skipped unconditionally.
CONFIG_DISABLE_ENV = "PCAE_NOTIFY_CONFIG_DISABLE"

# Explicit override for the config file path (used by tests and by
# operators who keep the file somewhere other than the default location).
CONFIG_PATH_ENV = "PCAE_NOTIFY_CONFIG_FILE"

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "pcae" / "notify.json"

# Only keys with this prefix are ever copied into os.environ. This is the
# one piece of channel-agnostic-but-not-unbounded discipline: the resolver
# will happily carry a brand-new adapter's env-var names (e.g.
# PCAE_SLACK_BOT_TOKEN) without code changes, but it will never let a
# config file inject arbitrary, non-PCAE environment variables into the
# process.
_ALLOWED_KEY_PREFIX = "PCAE_"

_SECRET_KEY_MARKERS = ("TOKEN", "SECRET", "KEY", "PASSWORD", "CHAT_ID")


def _truthy(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes")


def resolve_notification_config_path() -> Path:
    override = os.environ.get(CONFIG_PATH_ENV)
    if override:
        return Path(override)
    return DEFAULT_CONFIG_PATH


def is_config_resolution_disabled() -> bool:
    return _truthy(os.environ.get(CONFIG_DISABLE_ENV, ""))


def redact_config_value(key: str, value: str) -> str:
    """Redact a value for display (status output, logs) if its key looks
    like a secret. Never used to decide behavior -- only for safe display.
    """
    if any(marker in key.upper() for marker in _SECRET_KEY_MARKERS):
        if not value:
            return ""
        return "present" if len(value) else "missing"
    return value


def ensure_notification_environment_loaded() -> dict[str, Any]:
    """Populate ``os.environ`` from the governed config file, unless the
    operator's shell already provided the relevant variables or governed
    test isolation has disabled resolution.

    Fail-closed by construction: any missing file, unreadable file, invalid
    JSON, or non-dict/non-string content results in *no* environment
    change and no exception -- callers see exactly the same "not
    configured" state they would without this module existing. This
    function never raises.

    Returns a small, secret-free summary dict describing what happened, for
    ``pcae notify status`` and tests -- never the resolved values
    themselves.
    """
    summary: dict[str, Any] = {
        "disabled": False,
        "source": "none",
        "config_path": None,
        "applied_keys": [],
    }

    if is_config_resolution_disabled():
        summary["disabled"] = True
        return summary

    config_path = resolve_notification_config_path()
    summary["config_path"] = str(config_path)

    try:
        if not config_path.is_file():
            return summary
        raw = config_path.read_text()
        data = json.loads(raw)
    except (OSError, ValueError):
        # Unreadable or invalid config fails closed: no environment
        # change, no crash, no secret ever touches an exception message.
        summary["source"] = "invalid_or_unreadable"
        return summary

    if not isinstance(data, dict):
        summary["source"] = "invalid_or_unreadable"
        return summary

    applied: list[str] = []
    for key, value in data.items():
        if not isinstance(key, str) or not key.startswith(_ALLOWED_KEY_PREFIX):
            continue
        if not isinstance(value, str):
            continue
        # Explicit environment always wins -- a value already present in
        # os.environ (shell-sourced, CLI-exported, or set by an earlier
        # resolver call this same process) is never overwritten.
        if key in os.environ:
            continue
        os.environ[key] = value
        applied.append(key)

    if applied:
        summary["source"] = "governed_config_file"
        summary["applied_keys"] = sorted(applied)

    return summary
