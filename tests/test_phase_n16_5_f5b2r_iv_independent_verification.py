"""N16-5-F-5-B2R-IV — independent verification of the N16-5-F-5-B2R-IMPL
consumer-authenticity repair.

Independently constructed (not a rerun of the implementation phase's own
23-test suite). This suite reconstructs and adversarially probes
``_verified_production_caller_name`` / the process-local pin state in
``src/pcae/core/hpac_protected_admin_writer.py``.

FINDING (BLOCKING): the repair correctly denies the predecessor's disclosed
forged-``__name__``-via-``exec()`` technique and denies ``sys.modules``
poisoning (both confirmed below), but the process-local trust-pin state
(``_PINNED_CODE_OBJECTS`` / ``_PINNED_TRUSTED_MODULES`` /
``_CODE_OBJECT_KEEPALIVE``) is ordinary module-level mutable dict/list
state with NO real encapsulation -- protected only by a leading-underscore
naming convention, which Python does not enforce. Any ordinary in-process
code that can ``import pcae.core.hpac_protected_admin_writer`` can write
directly to these dicts. Doing so, then invoking any of the four privileged
factories from a single ``exec()`` against the real target module's own
``__dict__`` (itself an ordinary, caller-obtainable object via
``sys.modules[name].__dict__``, ID-matched to a caller-supplied code
object), mints a genuine capability -- no forged ``__name__``, no
``sys.modules`` poisoning, and no import-machinery spoof is needed. This
directly violates the primary IV negative-authenticity property (spec
Sec. 4.B) and pass criterion #17 ("ordinary in-process code cannot
trivially mutate/reset/replace the trust state in a way that grants
authority").

No production source is modified by this suite. No real ceremony, no live
protected-host state. All fixtures are disposable tmp_path-provisioned
PRODUCTION test-fixture protected roots.
"""

from __future__ import annotations

import os
import sys

import pytest

from pcae.core import hpac_protected_admin_writer as w

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root model"),
]

FAKE_AGENT_UID = 4_242_953
FAKE_AGENT_GID = 999_953
AGENT_ACCOUNT = "pcae-agent-svc-n16-5-f5b2r-iv"


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


def _call_with_forged_name(module_name: str, fn, *args, **kwargs):
    """Independent reconstruction of the predecessor's disclosed forged-name
    technique -- an ordinary caller with no import-machinery registration."""

    ns = {"__name__": module_name, "_fn": fn, "_args": args, "_kwargs": kwargs}
    exec(compile("_result = _fn(*_args, **_kwargs)", f"<forged:{module_name}>", "exec"), ns)
    return ns["_result"]


def test_forged_name_via_exec_globals_still_denied(root):
    """Regression confirmation: the predecessor's exact forgery-class
    remains denied (independently re-derived, not merely re-run)."""
    assert "pcae.core.hpac_rhamp_enrollment" in w.AUTHORIZED_FACTORY_CONSUMERS
    with pytest.raises(w.PawaError) as ei:
        _call_with_forged_name(
            "pcae.core.hpac_rhamp_enrollment",
            w.production_writer,
            w.PawaOperation.ENROLL_PRINCIPAL,
            principal_id="hp-" + "4" * 32,
            _protected_root=root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )
    assert ei.value.code == "unauthorized_factory_consumer"


def test_sys_modules_poisoning_still_denied(root):
    """Independent reconstruction: a hand-built module inserted into
    ``sys.modules`` under an authorized name (no genuine SourceFileLoader
    provenance) is denied."""
    import types

    candidate = "pcae.core.hpac_rhamp_enrollment"
    decoy = types.ModuleType(candidate)
    decoy.__name__ = candidate
    saved = sys.modules.get(candidate)
    sys.modules[candidate] = decoy
    decoy_code = compile(
        "_result['handle'] = _w.production_writer(\n"
        "    _w.PawaOperation.ENROLL_PRINCIPAL,\n"
        "    principal_id='hp-' + '5'*32,\n"
        "    _protected_root=_root,\n"
        "    _configured_agent_identity_source=_agent_src,\n"
        "    _topology_probe=_probe,\n"
        ")\n",
        "<decoy-module-call>", "exec",
    )
    decoy.__dict__["_w"] = w
    decoy.__dict__["_result"] = {}
    decoy.__dict__["_root"] = root
    decoy.__dict__["_agent_src"] = _agent_src()
    decoy.__dict__["_probe"] = _locked_probe()
    try:
        try:
            exec(decoy_code, decoy.__dict__)
        except w.PawaError as exc:
            assert exc.code == "unauthorized_factory_consumer"
        else:
            pytest.fail("sys.modules poisoning was not denied")
    finally:
        if saved is not None:
            sys.modules[candidate] = saved
        else:
            sys.modules.pop(candidate, None)


def test_BLOCKING_ordinary_code_can_overwrite_pin_state_to_impersonate_authorized_consumer(root):
    """BLOCKING FINDING -- see module docstring. An ordinary in-process
    caller (this test module, which is on no consumer allowlist) writes
    directly to ``w._PINNED_CODE_OBJECTS`` / ``w._PINNED_TRUSTED_MODULES``
    -- there is no encapsulation preventing this, only naming convention --
    then invokes ``production_writer`` for real via a single ``exec()``
    against the authorized target module's own ``__dict__``. This mints a
    genuine ``ProductionWriterHandle`` with no forged ``__name__``, no
    ``sys.modules`` poisoning, and no import-provenance spoof: the entire
    repaired recognition sequence is bypassed by direct process-local
    mutable-state tampering."""
    candidate = "pcae.core.hpac_rhamp_enrollment"
    assert candidate in w.AUTHORIZED_FACTORY_CONSUMERS
    import pcae.core.hpac_rhamp_enrollment as real_mod

    before_codes = dict(w._PINNED_CODE_OBJECTS)
    before_modules = dict(w._PINNED_TRUSTED_MODULES)

    attacker_code = compile(
        "import sys as _s\n"
        "from pcae.core import hpac_protected_admin_writer as _w\n"
        "_result['handle'] = _w.production_writer(\n"
        "    _w.PawaOperation.ENROLL_PRINCIPAL,\n"
        "    principal_id='hp-' + '6'*32,\n"
        "    _protected_root=_root,\n"
        "    _configured_agent_identity_source=_agent_src,\n"
        "    _topology_probe=_probe,\n"
        ")\n",
        "<attacker-exec-e2e>", "exec",
    )

    try:
        # The ONLY ordinary-code action taken: direct dict mutation on a
        # module this test merely imported. No forged __name__, no
        # sys.modules poisoning, no import-provenance spoof.
        w._PINNED_CODE_OBJECTS[candidate] = frozenset([id(attacker_code)])
        w._PINNED_TRUSTED_MODULES[candidate] = real_mod
        w._CODE_OBJECT_KEEPALIVE[candidate] = [attacker_code]

        result: dict = {}
        real_mod.__dict__["_result"] = result
        real_mod.__dict__["_root"] = root
        real_mod.__dict__["_agent_src"] = _agent_src()
        real_mod.__dict__["_probe"] = _locked_probe()
        try:
            exec(attacker_code, real_mod.__dict__)
        finally:
            for attr in ("_result", "_root", "_agent_src", "_probe"):
                real_mod.__dict__.pop(attr, None)

        handle = result.get("handle")
        assert handle is not None and isinstance(handle, w.ProductionWriterHandle), (
            "expected the disclosed bypass to succeed (documenting the current "
            "vulnerable behavior); if this assertion now fails, the pin state "
            "has gained real encapsulation and this test should be inverted "
            "into a regression lock by the successor repair phase"
        )
    finally:
        w._PINNED_CODE_OBJECTS.clear()
        w._PINNED_CODE_OBJECTS.update(before_codes)
        w._PINNED_TRUSTED_MODULES.clear()
        w._PINNED_TRUSTED_MODULES.update(before_modules)
