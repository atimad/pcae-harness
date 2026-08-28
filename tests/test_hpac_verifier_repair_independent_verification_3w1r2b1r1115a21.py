"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.2.1 — Independent Verification of
AuthenticatedHumanPrincipal Trusted-Construction and Provenance Repair.

Independently derived from HPAC-001 v2.0 §19 (HPAC-REQ-056/057/058) and the
governing verification prompt's own attack checklist, without copying
assertions from ``.1R.5.2``'s own new suite
(``tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py``); only the minimal
``_Rig`` fixture harness from ``tests/test_hpac_verifier.py`` is reused, for
fixture setup only (obtaining a genuine ``verify_human_authentication``
result), never for assertions. Historical evidence files
(``tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py``,
``tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py``) are read but not
modified; two of the former's tests are expected to keep failing by design
(see this phase's report, §9-equivalent) and are not re-litigated here.

Central verification question (this phase's own framing): possession,
construction, copying, reconstruction, or exact duplication of an
``AuthenticatedHumanPrincipal`` must not itself prove that HPAC verification
occurred. Trust must terminate in verifier-controlled provenance
(``is_verifier_authenticated_principal``), not in object shape.
"""
from __future__ import annotations

import copy
import pickle
import subprocess
import sys

import pytest

from pcae.core.hpac_foundation import HPACAuthorityClass, HPACAuthorityError
from pcae.core.hpac_verifier import (
    AuthenticatedHumanPrincipal,
    HPACVerificationError,
    is_verifier_authenticated_principal,
    verify_human_authentication,
)
import pcae.core.hpac_verifier as hpac_verifier_module

from test_hpac_verifier import _Rig  # fixture harness only, not assertions


# ═══════════════════════════════════════════════════════════════════════
# 1. Legitimate positive case + deterministic NON-REAL (baseline sanity)
# ═══════════════════════════════════════════════════════════════════════


def test_legitimate_result_is_verifier_authenticated_and_non_real(tmp_path):
    rig = _Rig(tmp_path)
    legit = rig.verify()
    assert isinstance(legit, AuthenticatedHumanPrincipal)
    assert is_verifier_authenticated_principal(legit) is True
    assert legit.assurance_class is HPACAuthorityClass.FIXTURE_NON_REAL
    assert legit.is_real_runtime_eligible is False


# ═══════════════════════════════════════════════════════════════════════
# 2. object.__new__ forgery — the exact F1 reproduction, then re-tested
#    against the provenance boundary rather than isinstance
# ═══════════════════════════════════════════════════════════════════════


def test_object_new_forgery_is_isinstance_true_but_not_verifier_authenticated(tmp_path):
    """Reproduces F1 exactly (isinstance is unavoidably True — this is a
    Python-language fact, not a defect a __new__ override could fix) and
    then confirms the actual repaired trust boundary rejects it."""
    rig = _Rig(tmp_path)
    legit = rig.verify()
    forged = object.__new__(AuthenticatedHumanPrincipal)
    for slot in AuthenticatedHumanPrincipal.__slots__:
        setattr(forged, slot, getattr(legit, slot))
    forged.assurance_class = HPACAuthorityClass.PRODUCTION
    assert isinstance(forged, AuthenticatedHumanPrincipal) is True
    assert forged.is_real_runtime_eligible is True  # data-shape only, expected
    assert is_verifier_authenticated_principal(forged) is False


def test_object_new_forgery_with_no_legitimate_reference_material(tmp_path):
    """A forgery built with no access to any legitimate result at all
    (attacker who has only read the module source, not a live result)."""
    forged = object.__new__(AuthenticatedHumanPrincipal)
    forged.principal_id = "attacker-principal"
    forged.credential_id = "attacker-credential"
    forged.mechanism_id = "hpac.deterministic.test-only.v1"
    forged.approval_id = "attacker-approval"
    forged.invocation_id = "attacker-invocation"
    forged.proof_id = "attacker-proof"
    forged.presentation_id = "attacker-presentation"
    forged.assurance_class = HPACAuthorityClass.PRODUCTION
    forged.verified_at = "2026-08-28T00:00:00Z"
    forged._verifier_seal = object()
    assert is_verifier_authenticated_principal(forged) is False


# ═══════════════════════════════════════════════════════════════════════
# 3. Direct construction — without and with the real seal
# ═══════════════════════════════════════════════════════════════════════


def test_direct_construction_without_seal_rejected_at_init():
    with pytest.raises(HPACAuthorityError):
        AuthenticatedHumanPrincipal(
            principal_id="p", credential_id="c", mechanism_id="m",
            approval_id="a", invocation_id="i", proof_id="pr",
            presentation_id="pe", assurance_class=HPACAuthorityClass.PRODUCTION,
            verified_at="2026-08-28T00:00:00Z", _seal=object(),
        )


def test_direct_construction_with_stolen_real_seal_still_not_authenticated(tmp_path):
    """Proves the _seal check is defense-in-depth, not the boundary: even
    an attacker who obtains the actual module-private sentinel via
    ``from pcae.core.hpac_verifier import _VERIFIER_CONSTRUCTOR_SEAL``
    cannot register a result in the identity registry, because only
    verify_human_authentication's own return path ever calls .add()."""
    from pcae.core.hpac_verifier import _VERIFIER_CONSTRUCTOR_SEAL

    rig = _Rig(tmp_path)
    legit = rig.verify()
    stolen = AuthenticatedHumanPrincipal(
        principal_id=legit.principal_id, credential_id=legit.credential_id,
        mechanism_id=legit.mechanism_id, approval_id=legit.approval_id,
        invocation_id=legit.invocation_id, proof_id=legit.proof_id,
        presentation_id=legit.presentation_id,
        assurance_class=HPACAuthorityClass.PRODUCTION,
        verified_at="2026-08-28T00:00:00Z", _seal=_VERIFIER_CONSTRUCTOR_SEAL,
    )
    assert is_verifier_authenticated_principal(stolen) is False
    assert is_verifier_authenticated_principal(legit) is True  # unaffected


# ═══════════════════════════════════════════════════════════════════════
# 4. Copy / deepcopy / pickle of a LEGITIMATE result
# ═══════════════════════════════════════════════════════════════════════


def test_shallow_copy_of_legitimate_result_raises(tmp_path):
    rig = _Rig(tmp_path)
    legit = rig.verify()
    with pytest.raises(TypeError):
        copy.copy(legit)


def test_deepcopy_of_legitimate_result_raises(tmp_path):
    rig = _Rig(tmp_path)
    legit = rig.verify()
    with pytest.raises(TypeError):
        copy.deepcopy(legit)


def test_pickle_of_legitimate_result_raises(tmp_path):
    rig = _Rig(tmp_path)
    legit = rig.verify()
    with pytest.raises(TypeError):
        pickle.dumps(legit)


# ═══════════════════════════════════════════════════════════════════════
# 5. Manual slot-clone / reflection reconstruction of a LEGITIMATE result
# ═══════════════════════════════════════════════════════════════════════


def test_manual_slot_clone_of_legitimate_result_not_authenticated(tmp_path):
    rig = _Rig(tmp_path)
    legit = rig.verify()
    clone = object.__new__(AuthenticatedHumanPrincipal)
    for slot in AuthenticatedHumanPrincipal.__slots__:
        setattr(clone, slot, getattr(legit, slot))
    assert clone is not legit
    assert clone != legit  # identity-only equality
    assert is_verifier_authenticated_principal(clone) is False
    assert is_verifier_authenticated_principal(legit) is True


def test_reflection_based_reconstruction_via_type_dunder_new(tmp_path):
    rig = _Rig(tmp_path)
    legit = rig.verify()
    reflected = type(legit).__new__(type(legit))
    for slot in type(legit).__slots__:
        setattr(reflected, slot, getattr(legit, slot))
    assert is_verifier_authenticated_principal(reflected) is False


# ═══════════════════════════════════════════════════════════════════════
# 6. Subclass attack
# ═══════════════════════════════════════════════════════════════════════


def test_subclassing_refused_at_definition_time():
    with pytest.raises(HPACAuthorityError):
        type("EvilPrincipal", (AuthenticatedHumanPrincipal,), {})


# ═══════════════════════════════════════════════════════════════════════
# 7. Equality / hash collision semantics
# ═══════════════════════════════════════════════════════════════════════


def test_field_identical_forgery_does_not_hash_or_equality_collide(tmp_path):
    rig = _Rig(tmp_path)
    legit = rig.verify()
    clone = object.__new__(AuthenticatedHumanPrincipal)
    for slot in AuthenticatedHumanPrincipal.__slots__:
        setattr(clone, slot, getattr(legit, slot))
    assert hash(clone) != hash(legit)
    assert (clone == legit) is False
    assert (clone in hpac_verifier_module._AUTHENTIC_PRINCIPAL_REGISTRY) is False


def test_two_independent_legitimate_results_are_each_authenticated_but_unequal(tmp_path):
    rig_a = _Rig(tmp_path / "a")
    rig_b = _Rig(tmp_path / "b")
    legit_a = rig_a.verify()
    legit_b = rig_b.verify()
    assert legit_a is not legit_b
    assert (legit_a == legit_b) is False
    assert is_verifier_authenticated_principal(legit_a) is True
    assert is_verifier_authenticated_principal(legit_b) is True


# ═══════════════════════════════════════════════════════════════════════
# 8. Non-AuthenticatedHumanPrincipal inputs — fail closed, no exception
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("bad", [None, "a-string", object(), 12345, [], {}])
def test_non_principal_inputs_rejected_fail_closed_no_exception(bad):
    assert is_verifier_authenticated_principal(bad) is False


# ═══════════════════════════════════════════════════════════════════════
# 9. Registry write-path inventory — only verify_human_authentication adds
# ═══════════════════════════════════════════════════════════════════════


def test_registry_add_is_only_reachable_from_verify_human_authentication_source():
    """AST/text-level inventory: exactly one call site in the module's own
    source adds to _AUTHENTIC_PRINCIPAL_REGISTRY, and it is inside
    verify_human_authentication's body, not a separately importable helper
    an ordinary caller could invoke to register an arbitrary object."""
    import ast
    import inspect

    src = inspect.getsource(hpac_verifier_module)
    tree = ast.parse(src)
    add_call_functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "add"
                    and isinstance(child.func.value, ast.Name)
                    and child.func.value.id == "_AUTHENTIC_PRINCIPAL_REGISTRY"
                ):
                    add_call_functions.append(node.name)
    assert add_call_functions == ["verify_human_authentication"]


def test_registry_has_no_separately_exported_registration_helper():
    """No public, importable function other than verify_human_authentication
    itself can add to the registry -- confirmed by __all__ containing no
    such helper and by direct attribute inspection."""
    assert "register" not in " ".join(hpac_verifier_module.__all__).lower()
    for name in hpac_verifier_module.__all__:
        obj = getattr(hpac_verifier_module, name)
        assert obj is not hpac_verifier_module._AUTHENTIC_PRINCIPAL_REGISTRY


def test_direct_same_process_registry_mutation_is_a_disclosed_threat_boundary_limitation():
    """Same-process code CAN mutate the module-level registry object
    directly (Python affords no protection against a same-process
    importer treating a single-underscore name as anything but a
    convention). This is not a defect this repair claims to close --
    HPAC-REQ-056 forbids a *caller-supplied-strings-or-dicts* construction
    from establishing authority; it does not (and, in pure Python, cannot)
    promise resistance to arbitrary same-process code that imports and
    mutates the verifier module's own internals. This test exists to keep
    that boundary explicit and regression-checked, not to assert it away."""
    forged = object.__new__(AuthenticatedHumanPrincipal)
    for slot in AuthenticatedHumanPrincipal.__slots__:
        setattr(forged, slot, "z")
    assert is_verifier_authenticated_principal(forged) is False
    hpac_verifier_module._AUTHENTIC_PRINCIPAL_REGISTRY.add(forged)
    try:
        assert is_verifier_authenticated_principal(forged) is True
    finally:
        hpac_verifier_module._AUTHENTIC_PRINCIPAL_REGISTRY.discard(forged)


# ═══════════════════════════════════════════════════════════════════════
# 10. Lifetime / GC / restart / reload semantics
# ═══════════════════════════════════════════════════════════════════════


def test_registry_holds_strong_references_result_survives_del(tmp_path):
    """The registry is a plain set (strong refs), documented trade-off:
    dropping the caller's own reference does not remove the result from
    the registry or make it eligible for GC while the process lives."""
    rig = _Rig(tmp_path)
    legit = rig.verify()
    before = len(hpac_verifier_module._AUTHENTIC_PRINCIPAL_REGISTRY)
    del legit
    import gc

    gc.collect()
    after = len(hpac_verifier_module._AUTHENTIC_PRINCIPAL_REGISTRY)
    assert after == before  # nothing was freed; strong references held


def test_object_id_reuse_after_del_does_not_grant_forged_object_authority(tmp_path):
    """Even if CPython later reuses a freed object's memory address for a
    new allocation, id()-reuse must not let a forged object at that
    address gain provenance -- because the registry holds strong
    references, the original result is never actually freed while
    registered, so no id can be reused for it; independently confirm a
    fresh object.__new__ allocation (whatever address it lands at) is
    never a member."""
    rig = _Rig(tmp_path)
    legit = rig.verify()
    legit_id = id(legit)
    del legit
    import gc

    gc.collect()
    junk = [object() for _ in range(500)]
    candidate = object.__new__(AuthenticatedHumanPrincipal)
    for slot in AuthenticatedHumanPrincipal.__slots__:
        setattr(candidate, slot, "w")
    assert is_verifier_authenticated_principal(candidate) is False
    del junk


def test_process_restart_semantics_via_module_reload_forces_reverification():
    """A verification result obtained before a module reload (the closest
    same-process proxy for a restart, since the registry is a fresh
    module-level set on reload) must not remain authenticated afterward --
    matching HPAC-REQ-058's re-verification-required semantics.

    Run in a fully isolated subprocess rather than an in-process
    importlib.reload: reloading pcae.core.hpac_verifier in-process rebinds
    AuthenticatedHumanPrincipal/HPACVerificationError to new class objects
    inside the shared module, which would silently break identity/`isinstance`
    assumptions in every other test in this same pytest session that already
    imported the pre-reload classes (a test-isolation hazard of the reload
    mechanism itself, not something this phase's repair should risk
    triggering as a side effect of verifying it)."""
    script = (
        "import sys; sys.path.insert(0, 'tests'); sys.path.insert(0, 'src')\n"
        "import importlib, pathlib, tempfile\n"
        "from test_hpac_verifier import _Rig\n"
        "import pcae.core.hpac_verifier as hv\n"
        "tmp = pathlib.Path(tempfile.mkdtemp(dir='/private/tmp'))\n"
        "rig = _Rig(tmp)\n"
        "legit = rig.verify()\n"
        "assert hv.is_verifier_authenticated_principal(legit) is True\n"
        "importlib.reload(hv)\n"
        "assert hv.is_verifier_authenticated_principal(legit) is False, "
        "'result from before reload must not remain authenticated after reload'\n"
        "assert len(hv._AUTHENTIC_PRINCIPAL_REGISTRY) == 0\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
        cwd=str(_repo_root()),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


# ═══════════════════════════════════════════════════════════════════════
# 11. Deterministic assurance remains NON-REAL; upgrade attempt rejected
# ═══════════════════════════════════════════════════════════════════════


def test_require_real_assurance_flag_still_rejects_fixture_chain(tmp_path):
    rig = _Rig(tmp_path)
    with pytest.raises(HPACVerificationError):
        rig.verify(require_real_assurance=True)


# ═══════════════════════════════════════════════════════════════════════
# 12. Zero production / PB / runtime-authority / Gate-9 consumers
# ═══════════════════════════════════════════════════════════════════════


def test_zero_production_consumers_of_hpac_verifier_outside_itself():
    """AST-based: an actual import of hpac_verifier (or an attribute access
    naming its public symbols) anywhere else in src/pcae, not a grep-text
    match -- a source comment mentioning "AuthenticatedHumanPrincipal" in
    prose (human_authenticator.py has exactly one, already independently
    confirmed non-functional by .1R.5.1 §12) must not count as a hit."""
    import ast

    root = _repo_root() / "src" / "pcae"
    offenders = []
    for path in root.rglob("*.py"):
        if path.resolve() == (_repo_root() / "src" / "pcae" / "core" / "hpac_verifier.py").resolve():
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[-1] == "hpac_verifier":
                        offenders.append(str(path))
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[-1] == "hpac_verifier":
                    offenders.append(str(path))
    assert offenders == []


def test_no_pb_or_runtime_authority_or_gate9_imports_in_hpac_verifier_source():
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(hpac_verifier_module))
    forbidden = {
        "permission_broker", "runtime_dispatch_permission", "runtime_authority",
        "runtime_invocation_authority_consumption", "runtime_invocation_approval_store",
    }
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[-1])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[-1])
    assert imported.isdisjoint(forbidden)


def _repo_root():
    import pathlib

    return pathlib.Path(__file__).resolve().parents[1]


# ═══════════════════════════════════════════════════════════════════════
# 13. F2/F3 regression guard -- step 3/4 logic untouched by this repair
# ═══════════════════════════════════════════════════════════════════════


def test_f2_f3_challenge_digest_step_still_deferred_to_lifecycle_cross_check(tmp_path):
    """Confirms F2 (HPAC-REQ-054 step 4 not independently recomputed) is
    unchanged by the F1 repair -- the verifier still only cross-checks
    proof.challenge_digest against the lifecycle genesis binding, not an
    independent recomputation from raw challenge state. This is a
    regression guard, not a re-adjudication of F2 itself (still
    NON-BLOCKING, unchanged, per this phase's own scope)."""
    import inspect

    src = inspect.getsource(hpac_verifier_module.verify_human_authentication)
    assert "binding[\"challenge_digest\"] != proof.challenge_digest" in src
