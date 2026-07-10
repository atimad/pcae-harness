"""Regression coverage for Phase 134B.1 external notification isolation."""

from __future__ import annotations

import json
import os
import subprocess
import sys

from conftest import (
    _EXTERNAL_NOTIFICATION_ENV,
    _LIVE_NOTIFICATION_TEST_OPT_IN,
    isolate_external_notification_env,
)


def test_ordinary_test_environment_has_no_live_notification_configuration():
    """Reproduces the incident prerequisite and proves the fixture removes it."""
    for key in _EXTERNAL_NOTIFICATION_ENV:
        assert key not in os.environ


def test_subprocess_inherits_isolated_environment_not_operator_credentials():
    """CLI/subprocess tests receive the already-isolated parent environment."""
    code = (
        "import json, os; "
        f"print(json.dumps({{k: os.environ.get(k) for k in {list(_EXTERNAL_NOTIFICATION_ENV)!r}}}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    values = json.loads(result.stdout)
    assert all(value is None for value in values.values())


def test_isolation_removes_preexisting_live_configuration():
    """Pre-repair failure mode: a sourced shell supplied every live value."""
    env = {key: f"live-{key}" for key in _EXTERNAL_NOTIFICATION_ENV}
    assert isolate_external_notification_env(env) is True
    assert all(key not in env for key in _EXTERNAL_NOTIFICATION_ENV)


def test_explicit_governed_live_integration_opt_in_is_preserved():
    """A separately governed live test can opt in deliberately."""
    env = {key: f"live-{key}" for key in _EXTERNAL_NOTIFICATION_ENV}
    env[_LIVE_NOTIFICATION_TEST_OPT_IN] = "1"
    before = dict(env)
    assert isolate_external_notification_env(env) is False
    assert env == before
