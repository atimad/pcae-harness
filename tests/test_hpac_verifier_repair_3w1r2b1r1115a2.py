"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.2 -- AuthenticatedHumanPrincipal
trusted-construction and provenance blocking repair.

Repairs F1 (BLOCKING, found by
``...1R.5.1``, ``docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_5_1_...md`` §10):
``AuthenticatedHumanPrincipal``'s trusted-construction seal
(``_VERIFIER_CONSTRUCTOR_SEAL``) lived only inside ``__init__``, so
``object.__new__`` -- which never calls ``__init__`` -- produced a fully
functional, ``isinstance``-true, field-populated forged instance without
ever running HPAC-REQ-054's verification sequence.

This suite does not attempt to make ``object.__new__``-allocated instances
stop being ``isinstance``-true (impossible in pure Python -- that is
exactly what ``object.__new__(cls)`` does, and it bypasses any subclass
``__new__`` override too, since it is a direct call to a different,
unrelated method). Instead it tests the actual repair: an identity-keyed,
verifier-owned registry (``is_verifier_authenticated_principal``) that
distinguishes a genuine :func:`verify_human_authentication` return value
from any caller-manufactured lookalike, however it was allocated --
direct construction, ``object.__new__``, a subclass attempt, ``copy``,
``deepcopy``, manual slot injection, reflection, or pickling.

The historical reproduction tests in
``tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py``
are preserved unmodified as evidence that F1 existed; one of them
(``test_object_dunder_new_bypasses_trusted_construction_seal``) asserts
``not isinstance(forged, AuthenticatedHumanPrincipal)``, which is not a
satisfiable postcondition in Python and is expected to keep failing after
this repair -- see this repository's `.1R.5.2` repair document, "Historical
F1 test handling", for why that is the correct outcome rather than a
regression.
"""

from __future__ import annotations

import ast
import copy
import gc
import pathlib
import pickle

import pytest

from pcae.core.hpac_foundation import HPACAuthorityClass, HPACAuthorityError
from pcae.core.hpac_verifier import (
    AuthenticatedHumanPrincipal,
    _VERIFIER_CONSTRUCTOR_SEAL,
    is_verifier_authenticated_principal,
)
import pcae.core.hpac_verifier as hpac_verifier_module

from test_hpac_verifier import NOW, _Rig

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_VERIFIER_SOURCE_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hpac_verifier.py"


def _legitimate_result(tmp_path):
    rig = _Rig(tmp_path)
    return rig.verify()


def _bare_slot_values(source: AuthenticatedHumanPrincipal) -> dict:
    return {
        slot: getattr(source, slot)
        for slot in AuthenticatedHumanPrincipal.__slots__
        if slot != "__weakref__"
    }


# ═══════════════════════════════════════════════════════════════════════
# §20 item: pre-repair object.__new__ bypass reproduced from fixed source
# ═══════════════════════════════════════════════════════════════════════


def test_object_new_still_allocates_an_isinstance_true_bare_instance():
    """Reproduces the exact F1 mechanism from fixed source: object.__new__
    does not call __init__, so the seal check never runs and the class
    remains constructible this way. This is expected to remain true after
    the repair -- see the module docstring's explanation of why blocking
    object.__new__ itself is not the fix. The repair is that this bare
    instance is never trusted (see the tests below)."""

    forged = object.__new__(AuthenticatedHumanPrincipal)
    assert isinstance(forged, AuthenticatedHumanPrincipal)
    # __init__ never ran: __slots__ attributes are simply unset.
    with pytest.raises(AttributeError):
        forged.principal_id


# ═══════════════════════════════════════════════════════════════════════
# §20 items: direct constructor / object.__new__ / subclass / copy /
# deepcopy / state-copy / reflection / pickle cannot establish authority
# ═══════════════════════════════════════════════════════════════════════


def test_direct_constructor_with_wrong_seal_raises():
    with pytest.raises(HPACAuthorityError):
        AuthenticatedHumanPrincipal(
            principal_id="hp-forged",
            credential_id="hpc-forged",
            mechanism_id="hpac.deterministic.test-only.v1",
            approval_id="ria-forged",
            invocation_id="iv-forged",
            proof_id="hap-forged",
            presentation_id="hpe-forged",
            assurance_class=HPACAuthorityClass.FIXTURE_NON_REAL,
            verified_at=NOW,
            _seal=object(),
        )


def test_direct_constructor_even_with_the_real_module_private_seal_is_not_registered():
    """The seal is real, but obtaining it (e.g. via
    `from pcae.core.hpac_verifier import _VERIFIER_CONSTRUCTOR_SEAL`, which
    only works because this is a *test* granted source access, not a
    documented/exported name) only satisfies __init__'s defense-in-depth
    check. It is not the trust boundary -- constructing this way does not
    add the instance to the identity registry, because only
    verify_human_authentication's own call site does that."""

    direct = AuthenticatedHumanPrincipal(
        principal_id="hp-direct",
        credential_id="hpc-direct",
        mechanism_id="hpac.deterministic.test-only.v1",
        approval_id="ria-direct",
        invocation_id="iv-direct",
        proof_id="hap-direct",
        presentation_id="hpe-direct",
        assurance_class=HPACAuthorityClass.PRODUCTION,
        verified_at=NOW,
        _seal=_VERIFIER_CONSTRUCTOR_SEAL,
    )
    assert isinstance(direct, AuthenticatedHumanPrincipal)
    assert is_verifier_authenticated_principal(direct) is False


def test_object_new_forgery_is_not_verifier_authenticated():
    forged = object.__new__(AuthenticatedHumanPrincipal)
    forged.principal_id = "forged-principal"
    forged.credential_id = "forged-credential"
    forged.mechanism_id = "forged-mechanism"
    forged.approval_id = "forged-approval"
    forged.invocation_id = "forged-invocation"
    forged.proof_id = "forged-proof"
    forged.presentation_id = "forged-presentation"
    forged.assurance_class = HPACAuthorityClass.PRODUCTION
    forged.verified_at = NOW
    forged._verifier_seal = object()

    assert isinstance(forged, AuthenticatedHumanPrincipal)
    assert forged.is_real_runtime_eligible is True  # data-shape only, see docstring
    assert is_verifier_authenticated_principal(forged) is False


def test_subclass_construction_is_refused_at_class_definition_time():
    with pytest.raises(HPACAuthorityError, match="must not be subclassed"):

        class Evil(AuthenticatedHumanPrincipal):
            def __init__(self, **kwargs):  # pragma: no cover - never reached
                for key, value in kwargs.items():
                    object.__setattr__(self, key, value)


def test_shallow_copy_of_legitimate_result_raises(tmp_path):
    result = _legitimate_result(tmp_path)
    with pytest.raises(TypeError):
        copy.copy(result)


def test_deepcopy_of_legitimate_result_raises(tmp_path):
    result = _legitimate_result(tmp_path)
    with pytest.raises(TypeError):
        copy.deepcopy(result)


def test_pickle_of_legitimate_result_raises(tmp_path):
    result = _legitimate_result(tmp_path)
    with pytest.raises(TypeError):
        pickle.dumps(result)


def test_manual_slot_state_copy_of_legitimate_result_is_not_authenticated(tmp_path):
    """§20/§9/§10: reproduce the exact field values of a real verification
    result (including its own real assurance_class) via object.__new__ plus
    setattr for every slot -- the literal "clone the object's internal
    state" attack. The clone must not be trusted even though every visible
    field, repr-relevant attribute, and even the copied
    `_verifier_seal` sentinel is byte-for-byte identical to the genuine
    result."""

    result = _legitimate_result(tmp_path)
    clone = object.__new__(AuthenticatedHumanPrincipal)
    for slot, value in _bare_slot_values(result).items():
        setattr(clone, slot, value)

    assert clone is not result
    assert clone.principal_id == result.principal_id
    assert clone.assurance_class == result.assurance_class
    assert clone._verifier_seal is result._verifier_seal
    assert is_verifier_authenticated_principal(result) is True
    assert is_verifier_authenticated_principal(clone) is False


def test_slot_injection_via_reflection_is_not_authenticated(tmp_path):
    """Reflection-based reconstruction: discover the slot names and the
    real seal value entirely through introspection of a legitimate result
    (as an attacker with only a reference to one value, not source access,
    might attempt), rather than by reading the class's own __slots__
    tuple directly."""

    result = _legitimate_result(tmp_path)
    cls = type(result)
    reflected = cls.__new__(cls)
    for slot in cls.__slots__:
        if slot == "__weakref__":
            continue
        if hasattr(result, slot):
            setattr(reflected, slot, getattr(result, slot))

    assert is_verifier_authenticated_principal(reflected) is False


def test_forged_result_with_identical_public_fields_is_rejected(tmp_path):
    """§20 'forged result with identical public fields rejected', phrased
    as the actual trust decision (§21): even though every publicly-visible
    field matches a legitimate result, the forged object is not the
    registry-tracked object and is therefore never trusted."""

    result = _legitimate_result(tmp_path)
    forged = object.__new__(AuthenticatedHumanPrincipal)
    for slot in (
        "principal_id",
        "credential_id",
        "mechanism_id",
        "approval_id",
        "invocation_id",
        "proof_id",
        "presentation_id",
        "assurance_class",
        "verified_at",
    ):
        setattr(forged, slot, getattr(result, slot))
    forged._verifier_seal = _VERIFIER_CONSTRUCTOR_SEAL

    assert forged == forged  # identity-only __eq__, reflexive
    assert forged != result  # never equal to the genuine object either
    assert is_verifier_authenticated_principal(forged) is False


# ═══════════════════════════════════════════════════════════════════════
# §21: the key test is the downstream trust decision, not construction
# ═══════════════════════════════════════════════════════════════════════


def test_legitimate_verifier_result_is_accepted_through_the_provenance_boundary(tmp_path):
    result = _legitimate_result(tmp_path)
    assert is_verifier_authenticated_principal(result) is True


def test_non_principal_values_are_rejected_by_the_provenance_boundary():
    assert is_verifier_authenticated_principal(None) is False
    assert is_verifier_authenticated_principal("not-a-principal") is False
    assert is_verifier_authenticated_principal(object()) is False


def test_two_independent_legitimate_results_are_both_authenticated_but_not_equal(tmp_path):
    rig = _Rig(tmp_path)
    first = rig.verify()
    second = rig.verify()
    assert is_verifier_authenticated_principal(first) is True
    assert is_verifier_authenticated_principal(second) is True
    assert first != second


# ═══════════════════════════════════════════════════════════════════════
# Registry lifetime (§24: process-internal, not durably persisted)
# ═══════════════════════════════════════════════════════════════════════


def test_registry_is_process_local_and_holds_a_strong_reference(tmp_path):
    """The registry is a plain (strong-reference) set, not a weak one --
    see the module's `_AUTHENTIC_PRINCIPAL_REGISTRY` comment for why
    `__weakref__` cannot be added to `__slots__` without breaking
    `...1R.5.1`'s preserved historical evidence test. This is a documented
    trade-off, not an oversight: a verified result therefore remains
    registered (and reachable via the registry) even after the caller
    drops its own reference, for the remaining lifetime of the process --
    it is still never persisted to disk, never survives a process
    restart, and is still non-serializable (HPAC-REQ-058)."""

    rig = _Rig(tmp_path)
    result = rig.verify()
    assert result in hpac_verifier_module._AUTHENTIC_PRINCIPAL_REGISTRY
    result_id = id(result)
    del result
    gc.collect()
    # The registry itself keeps the object alive; membership is unaffected
    # by the caller dropping its own reference.
    assert any(
        id(entry) == result_id for entry in hpac_verifier_module._AUTHENTIC_PRINCIPAL_REGISTRY
    )


def test_registry_is_not_part_of_the_public_api():
    assert "_AUTHENTIC_PRINCIPAL_REGISTRY" not in hpac_verifier_module.__all__
    assert "is_verifier_authenticated_principal" in hpac_verifier_module.__all__


# ═══════════════════════════════════════════════════════════════════════
# Deterministic NON-REAL assurance unaffected by the repair (regression)
# ═══════════════════════════════════════════════════════════════════════


def test_legitimate_deterministic_result_remains_non_real_after_repair(tmp_path):
    result = _legitimate_result(tmp_path)
    assert result.assurance_class is HPACAuthorityClass.FIXTURE_NON_REAL
    assert result.is_real_runtime_eligible is False
    assert is_verifier_authenticated_principal(result) is True


# ═══════════════════════════════════════════════════════════════════════
# §20: zero production consumers / zero PB / runtime / Gate-9 consumers
# (re-confirmed from this repair's own test file, independent of
# test_hpac_verifier.py's equivalent checks)
# ═══════════════════════════════════════════════════════════════════════


def _imported_module_names(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_repair_did_not_introduce_pb_or_runtime_authority_or_gate9_imports():
    imports = _imported_module_names(_VERIFIER_SOURCE_PATH)
    forbidden_suffixes = (
        "runtime_dispatch_permission",
        "permission_broker",
        "runtime_authority",
        "runtime_invocation_authority_consumption",
        "runtime_invocation_approval_store",
    )
    for module_name in imports:
        for suffix in forbidden_suffixes:
            assert not module_name.endswith(suffix), f"hpac_verifier.py must not import {module_name}"


def test_runtime_authority_is_the_only_production_consumer_after_integration():
    # Phase .1R.30R.3.4 reconciliation: check real `import` statements, not a
    # bare substring — the merged RHAMP `.1R.30` bundle adds modules that
    # name `hpac_verifier` only in prose (the real dependency runs the other
    # way: hpac_verifier lazily imports `verify_real_fido2_assertion`). The
    # authorized consumer set is unchanged. No `def test_` renamed/removed.
    import ast as _ast

    src_root = _REPO_ROOT / "src" / "pcae"
    consumers = []
    for path in src_root.rglob("*.py"):
        if "__pycache__" in path.parts or path.name == "hpac_verifier.py":
            continue
        try:
            tree = _ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        modules = {n.module for n in _ast.walk(tree) if isinstance(n, _ast.ImportFrom) and n.module}
        modules |= {a.name for n in _ast.walk(tree) if isinstance(n, _ast.Import) for a in n.names}
        if any(m.endswith("hpac_verifier") for m in modules):
            consumers.append(str(path.relative_to(_REPO_ROOT)))
    # .1R.10 added the authorized Gate-5 approval-validation coordinator.
    assert sorted(consumers) == [
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
    ]


def test_reverification_is_the_only_added_public_consumption_surface():
    assert set(hpac_verifier_module.__all__) == {
        "HPACVerificationError",
        "AuthenticatedHumanPrincipal",
        "verify_human_authentication",
        "is_verifier_authenticated_principal",
        "reverify_authenticated_principal",
    }
