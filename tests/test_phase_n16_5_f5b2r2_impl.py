"""N16-5-F-5-B2R2-IMPL -- mutable-state trust-boundary repair /
unsatisfiability adjudication for the four privileged HPAC-PAWA factories in
``src/pcae/core/hpac_protected_admin_writer.py``.

This phase's Section 8 adjudication (required by the authorizing prompt):
can the frozen HPAC-PAWA-001 consumer-authenticity property be enforced
against ordinary same-process Python code, given Python's ability to
inspect/rebind/import/mutate objects?

VERDICT: NO. Confirmed by three independent, escalating PoCs below:

1. ``test_regression_direct_pin_mutation_bypass_unchanged`` -- reconfirms
   the predecessor's (N16-5-F-5-B2R-IV) disclosed finding is unchanged: no
   production source was modified by this phase, because a genuine repair
   does not exist within the stated threat model (see #2/#3).

2. ``test_gc_based_bypass_defeats_closure_encapsulation`` -- proves the
   general case: even a "best-effort" pure-Python encapsulation the current
   defect does NOT use (trust state as a local variable inside a factory
   closure, never assigned to any module-level name, never returned,
   `_secret_pin`/`_bind` never exposed anywhere) is still discoverable and
   directly mutable by ordinary code using only ``import gc`` and
   ``gc.get_objects()`` -- no reference chain to the closure is required at
   all. This is not specific to this module's implementation choices; it is
   a general property of the CPython object model available to any
   same-process code via the standard library, so no re-encapsulation of
   the *existing* pin dicts (class instance, frozen dataclass,
   MappingProxyType, name-mangling, closure) can close the gap.

3. ``test_fresh_scan_no_cache_redesign_is_also_unsafe`` -- proves the
   defect is not confined to the three named pin dicts either: a
   standalone, isolated analogue of the Sec. 7-preferred "eliminate the
   mutable cache, re-derive trust fresh from ``vars(module)`` at every
   call" redesign shape remains attackable, because the trusted module's
   own ``__dict__`` -- the object every legitimate caller must be able to
   reach via ``sys.modules[name].__dict__`` for imports to work at all --
   is itself an ordinary, caller-writable dict. An attacker can define a
   new function directly inside the trusted module's own namespace (via
   ``exec()`` against ``module.__dict__``, an ordinary operation on an
   already-imported module object) and call it normally, satisfying any purely-runtime
   provenance/identity check that relies on ``vars(module)`` /
   ``module.__dict__`` without a frozen-at-a-trustworthy-moment snapshot.

No production source is modified by this suite. No real ceremony, no live
protected-host state. All fixtures are local, disposable, and self-contained
-- none is a reusable attack utility exported for use elsewhere.
"""

from __future__ import annotations

import gc
import os
import sys

import pytest

from pcae.core import hpac_protected_admin_writer as w

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root model"),
]

FAKE_AGENT_UID = 4_242_954
FAKE_AGENT_GID = 999_954
AGENT_ACCOUNT = "pcae-agent-svc-n16-5-f5b2r2-impl"


def _agent_src():
    def source(symbolic_account, provisioned_uid):
        return provisioned_uid, frozenset({FAKE_AGENT_GID})

    return source


def _locked_probe():
    def ewa(path, uid, gids):
        return (False, "fixture_locked", ())

    def acs(start, uid, gids):
        return (True, ("fixture_root_reached",))

    return w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


@pytest.fixture
def root(tmp_path):
    r = (tmp_path / "hpac-protected-root").resolve()
    w.provision_protected_root(protected_root=r, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID)
    return r


def test_regression_direct_pin_mutation_bypass_unchanged(root):
    """Reconfirms the N16-5-F-5-B2R-IV disclosed finding still reproduces
    unchanged: this phase's Section 8 adjudication (see module docstring
    and tests #2/#3 below) concluded BLOCKED -- unsatisfiable within the
    current same-process Python boundary -- so no production source was
    modified. This is not a rerun of the predecessor's own test file; it is
    a fresh, independent re-derivation used only to confirm the premise of
    the BLOCKED conclusion (the defect this phase was asked to repair is
    still present, unrepaired, because it cannot honestly be repaired
    in-process)."""
    candidate = "pcae.core.hpac_rhamp_enrollment"
    assert candidate in w.AUTHORIZED_FACTORY_CONSUMERS
    import pcae.core.hpac_rhamp_enrollment as real_mod

    before_codes = dict(w._PINNED_CODE_OBJECTS)
    before_modules = dict(w._PINNED_TRUSTED_MODULES)

    attacker_code = compile(
        "from pcae.core import hpac_protected_admin_writer as _w\n"
        "_result['handle'] = _w.production_writer(\n"
        "    _w.PawaOperation.ENROLL_PRINCIPAL,\n"
        "    principal_id='hp-' + '7'*32,\n"
        "    _protected_root=_root,\n"
        "    _configured_agent_identity_source=_agent_src,\n"
        "    _topology_probe=_probe,\n"
        ")\n",
        "<attacker-exec-e2e-regression>", "exec",
    )
    try:
        w._PINNED_CODE_OBJECTS[candidate] = frozenset([id(attacker_code)])
        w._PINNED_TRUSTED_MODULES[candidate] = real_mod
        w._CODE_OBJECT_KEEPALIVE[candidate] = [attacker_code]

        result: dict = {}
        real_mod.__dict__.update(
            _result=result, _root=root, _agent_src=_agent_src(), _probe=_locked_probe()
        )
        try:
            exec(attacker_code, real_mod.__dict__)
        finally:
            for attr in ("_result", "_root", "_agent_src", "_probe"):
                real_mod.__dict__.pop(attr, None)

        handle = result.get("handle")
        assert handle is not None and isinstance(handle, w.ProductionWriterHandle), (
            "the disclosed bypass no longer reproduces -- if a repair was made "
            "elsewhere in this phase, this test must be re-adjudicated before "
            "any BLOCKED conclusion is finalized"
        )
    finally:
        w._PINNED_CODE_OBJECTS.clear()
        w._PINNED_CODE_OBJECTS.update(before_codes)
        w._PINNED_TRUSTED_MODULES.clear()
        w._PINNED_TRUSTED_MODULES.update(before_modules)


def test_gc_based_bypass_defeats_closure_encapsulation():
    """Architectural PoC (not against production code): even trust state
    that is NEVER assigned to any module-level name, NEVER returned from
    its enclosing factory, and NEVER referenced by any function this
    demonstration module exposes, is still discoverable and mutable by
    ordinary code using only the ``gc`` standard-library module -- with
    ZERO reference chain to the closure. This generalizes past the specific
    pin dicts in ``hpac_protected_admin_writer`` and shows that no
    conventional pure-Python encapsulation technique (class attribute,
    name-mangled attribute, frozen dataclass, MappingProxyType wrapping a
    mutable dict held elsewhere, WeakValueDictionary, or closure) can hide
    authority-bearing mutable state from same-process code, because
    ``gc.get_objects()`` enumerates every GC-tracked object currently alive
    in the process regardless of what references it."""

    marker = "n16_5_f5b2r2_impl_gc_poc_marker_9f13ae"

    def make_guard():
        _secret_pin = {marker: "trusted_only"}  # never returned, never module-level

        def check(name):
            return _secret_pin.get(marker) == "trusted" and name == "victim"

        return check

    check = make_guard()
    assert check("victim") is False  # not yet trusted

    # The only "attacker" action: import gc and enumerate live objects.
    # No reference to `check`, `make_guard`, or this test function is used.
    target = None
    for obj in gc.get_objects():
        if isinstance(obj, dict) and obj.get(marker) == "trusted_only":
            target = obj
            break

    assert target is not None, (
        "expected gc.get_objects() to locate the closure-hidden dict with "
        "zero reference chain -- if this now fails, CPython's GC object "
        "enumeration semantics have changed and this adjudication must be "
        "redone before relying on it"
    )
    target[marker] = "trusted"

    assert check("victim") is True, (
        "expected the blind gc.get_objects() mutation to flip trust state "
        "with no import-chain, no closure reference, and no ctypes -- "
        "confirming no pure-Python same-interpreter encapsulation of "
        "authority-bearing mutable state is safe against ordinary code"
    )


def test_fresh_scan_no_cache_redesign_is_also_unsafe():
    """Architectural PoC (isolated, not against production code): proves
    that the Sec. 7-preferred 'eliminate the mutable pin cache, re-derive
    trust fresh from ``vars(module)`` at every call' redesign shape is
    ALSO unsafe, not merely today's caching implementation. This is why
    the repair is not a matter of finding a better place to re-derive from
    -- the module namespace being re-derived FROM is itself the untrusted,
    ordinary, caller-writable surface.

    Builds a minimal standalone analogue of the real recognizer with the
    cache removed (scan-``vars(module)``-fresh-every-call, no
    ``_PINNED_*`` state at all -- exactly the 'no cache' design Sec. 7
    asks to prefer), then shows an ordinary caller defeats it by adding a
    new function to the trusted module's own namespace and calling it
    against that namespace: the freshly-collected code-object set now
    legitimately includes the attacker's own injected function, because a
    scan-at-call-time recognizer cannot distinguish 'always been here'
    from 'the attacker just added it a moment ago'."""

    import types as _types

    trusted = _types.ModuleType("poc_trusted_consumer_module")

    def legit_entrypoint():
        return "legit"

    trusted.legit_entrypoint = legit_entrypoint

    def fresh_scan_recognize(frame) -> bool:
        """No cache, no pin dict -- re-derives the trusted code-object set
        fresh from ``vars(trusted)`` on every single call, exactly as
        Sec. 7 prefers ('no caller-writable cache determines
        authorization... cache miss may trigger re-derivation')."""
        if frame.f_globals is not trusted.__dict__:
            return False
        code_ids = {
            id(fn.__code__)
            for fn in vars(trusted).values()
            if isinstance(fn, _types.FunctionType)
        }
        return id(frame.f_code) in code_ids

    # Baseline: an outside caller (this test function's own frame, whose
    # f_globals is this test module's dict, not `trusted`'s) is correctly
    # denied -- the "improvement" a no-cache redesign claims to offer.
    assert fresh_scan_recognize(sys._getframe(0)) is False

    # ATTACKER: the only action taken is defining a brand-new function
    # directly inside the trusted module's own namespace via exec() (an
    # ordinary, no-privilege operation on an already-imported module
    # object), then calling it normally. A `def` executed against
    # `trusted.__dict__` genuinely binds `__globals__` to that dict --
    # exactly like any real top-level function in that module -- and the
    # resulting function is automatically part of `vars(trusted)`, so a
    # mere attribute-assignment shortcut is not even needed.
    trusted.__dict__["_recognize"] = fresh_scan_recognize
    trusted.__dict__["_sys"] = sys
    trusted.__dict__["recognized"] = {}
    exec(
        compile(
            "def attacker_payload():\n"
            "    recognized['ok'] = _recognize(_sys._getframe(0))\n"
            "attacker_payload()\n",
            "<attacker-defines-and-calls-inside-trusted-namespace>", "exec",
        ),
        trusted.__dict__,
    )
    recognized = trusted.__dict__["recognized"]
    for attr in ("_recognize", "_sys"):
        trusted.__dict__.pop(attr, None)

    assert recognized["ok"] is True, (
        "expected the fresh-scan (no-cache) redesign to ALSO wrongly "
        "recognize attacker-supplied code as trusted, because once the "
        "attacker attaches their own function to `vars(trusted)` as "
        "`trusted.attacker_payload` and calls it normally, that call's own "
        "frame.f_code IS `attacker_payload.__code__` -- genuinely "
        "id()-present in the freshly-collected set, by construction, no "
        "matter when the scan runs -- proving 'no cache, re-derive fresh "
        "at call time' is not a safe alternative to today's pin-based "
        "cache; the module namespace being scanned is itself the "
        "untrusted, ordinary, caller-writable surface"
    )
