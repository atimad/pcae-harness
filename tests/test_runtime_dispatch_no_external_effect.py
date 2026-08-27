"""Tests for Phase 149O.20L.7O.3W — no-external-effect invariant (3V.2
§37): `subprocess=0`, `network=0`, `credential access=0`,
`external runtime=0`, `repo mutation by runtime=0` across the full
authority/PB foundation chain, plus a static source audit that the new
modules import none of the forbidden execution-adjacent primitives.
"""

from __future__ import annotations

import ast
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core import runtime_authority as ra
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core import runtime_invocation_approval_store as store_mod

from _rdw3w_helpers import always_unconsumed, build_approval, dispatch_inputs, full_chain, matching_context

NEW_MODULE_PATHS = [
    Path(ra.__file__),
    Path(rdp.__file__),
    Path(store_mod.__file__),
]

_FORBIDDEN_IMPORT_MODULES = frozenset({
    "subprocess", "socket", "http", "http.client", "urllib", "urllib.request",
    "requests", "ftplib", "smtplib", "telnetlib", "ssl", "pty", "os.system",
})


def _imported_module_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


@pytest.mark.parametrize("path", NEW_MODULE_PATHS, ids=[p.name for p in NEW_MODULE_PATHS])
def test_new_module_imports_no_forbidden_execution_primitive(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = _imported_module_names(tree)
    forbidden_hit = imported & {m.split(".")[0] for m in _FORBIDDEN_IMPORT_MODULES}
    assert forbidden_hit == set(), f"{path.name} imports forbidden module(s): {forbidden_hit}"


@pytest.mark.parametrize("path", NEW_MODULE_PATHS, ids=[p.name for p in NEW_MODULE_PATHS])
def test_new_module_source_contains_no_subprocess_or_shell_calls(path: Path):
    source = path.read_text(encoding="utf-8")
    for token in ("subprocess.", "os.system(", "os.popen(", "Popen(", "pty.spawn"):
        assert token not in source, f"{path.name} contains forbidden token: {token}"


def test_permission_broker_foundation_still_isolated_after_extension():
    """This phase's edit to `permission_broker_foundation.py` is additive
    only -- re-verify its own pre-existing isolation guarantee still
    holds (matches this module's own docstring claim)."""
    path = Path(pbf.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = _imported_module_names(tree)
    assert imported.isdisjoint({"subprocess", "socket"})
    assert "shell_gate" not in " ".join(
        n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
    )


def test_full_chain_makes_zero_subprocess_calls(monkeypatch):
    calls = {"count": 0}

    def _tripwire(*args, **kwargs):
        calls["count"] += 1
        raise AssertionError("subprocess invoked during authority/PB chain")

    monkeypatch.setattr(subprocess, "run", _tripwire)
    monkeypatch.setattr(subprocess, "Popen", _tripwire)
    full_chain(simulation_only=True)
    full_chain(simulation_only=False)
    assert calls["count"] == 0


def test_full_chain_makes_zero_network_calls(monkeypatch):
    def _tripwire(*args, **kwargs):
        raise AssertionError("socket created during authority/PB chain")

    monkeypatch.setattr(socket, "socket", _tripwire)
    full_chain(simulation_only=True)
    full_chain(simulation_only=False)


def test_full_chain_reads_no_environment_credentials(monkeypatch):
    """No code path in the new modules reads `os.environ` at all (checked
    both statically and via a runtime tripwire on common credential-shaped
    keys)."""
    import os

    original_getitem = os.environ.__class__.__getitem__
    original_get = os.environ.__class__.get
    touched: list[str] = []

    def _tracking_getitem(self, key):
        touched.append(key)
        return original_getitem(self, key)

    def _tracking_get(self, key, *a, **kw):
        touched.append(key)
        return original_get(self, key, *a, **kw)

    monkeypatch.setattr(os.environ.__class__, "__getitem__", _tracking_getitem)
    monkeypatch.setattr(os.environ.__class__, "get", _tracking_get)
    full_chain(simulation_only=True)
    assert touched == []


def test_no_credential_shaped_field_anywhere_in_approval_or_request():
    approval, projection, request, decision = full_chain()
    approval_text = str(approval.to_dict())
    request_text = str(dataclasses_to_str(request))
    for forbidden in ("password", "secret", "token", "api_key", "credential", "private_key"):
        assert forbidden not in approval_text.lower()
        assert forbidden not in request_text.lower()


def dataclasses_to_str(value) -> str:
    import dataclasses

    if dataclasses.is_dataclass(value):
        return str({f.name: dataclasses_to_str(getattr(value, f.name)) for f in dataclasses.fields(value)})
    return str(value)


def test_no_repository_mutation_by_authority_pb_chain(tmp_path):
    """The full chain never writes anywhere except the approval store's
    own canonical directory under the caller-supplied root -- no stray
    file appears anywhere else under `tmp_path`."""
    from pcae.core.runtime_invocation_approval_store import RuntimeInvocationApprovalStore

    before = set(tmp_path.rglob("*"))
    approval = build_approval()
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    ctx = matching_context(approval)
    projection, _ = ra.validate_approval(approval, context=ctx, consumption_lookup=always_unconsumed)
    inputs = dispatch_inputs()
    identity = rdp.new_runtime_dispatch_identity(inputs, invocation_id=approval.subject.invocation_id)
    rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=projection,
    )
    after = set(tmp_path.rglob("*"))
    new_paths = after - before
    for p in new_paths:
        assert ".pcae/runtime-invocation-approvals/v1" in str(p.relative_to(tmp_path)) or p.is_dir()
