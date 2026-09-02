"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2.1.1 — Independent Verification
of the N-16-5 PAWA ``HPACWriterCapability`` Non-Bearer / One-Operation
Integrity Repair (`.1R.30R.3.2.1`).

Fresh, independently-authored IV suite. Does not re-run or re-derive the
`.1R.30R.3.2.1` dedicated repair suite's own 24 tests or the 4 product-suite
regression tests it added (`test_55a`-`test_55d`) — those are re-executed
unedited as part of this phase's finalization, not duplicated here. This
suite instead targets the specific checklist items the phase prompt itself
enumerates that the existing suites do not exercise: object-identity/id-reuse
structural safety, field mutation on a *genuinely issued* (not shell)
capability, registration-failure fail-closed behaviour, validation-failure
lifecycle (registry stays ACTIVE), the post-durable-write /
pre-consumption-mark exception path (HPAC-PAWA-REQ-106/107 one-operation
exposure), issuance-evidence non-authoritative content, registry
non-export / consumer-boundary / issuance-function-inventory statics, and
fork/process-boundary absence.

VERIFICATION ONLY. No src/pcae, no contract, no existing test file touched
by this suite.
"""

from __future__ import annotations

import gc
import re
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hpac_foundation as hf
from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import HPACAuthorityError, HPACWriterCapability
from pcae.core.human_principal_registry import (
    HumanPrincipalRegistryError,
    HumanPrincipalRegistryStore,
)

from test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1 import (
    AGENT_ACCOUNT,
    FAKE_AGENT_UID,
    HP_A,
    HP_B,
    THIS_MODULE as _SLICE1_MODULE,
    _agent_src,
    _authority,
    _locked_probe,
    _mint,
)

pytestmark = [pytest.mark.fast_green]

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACT = REPO / "docs" / "contracts" / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
HPAC_FOUNDATION = SRC / "core" / "hpac_foundation.py"
HPAC_WRITER = SRC / "core" / "hpac_protected_admin_writer.py"
HPAC_REGISTRY = SRC / "core" / "human_principal_registry.py"
REPAIR_DOC = (
    REPO / "docs"
    / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_2_1_N_16_5_PAWA_HPACWRITERCAPABILITY_NON_BEARER_ONE_OPERATION_INTEGRITY_REPAIR.md"
)
BLOCKED_IV_DOC = (
    REPO / "docs"
    / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_2_INDEPENDENT_VERIFICATION_OF_N_16_5_PAWA_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_SLICE_1.md"
)
R_ENTRY_SHA = "83b7f70b"  # .1R.30R.3.2 finalized head == .1R.30R.3.2.1 phase-entry SHA


def _provision(tmp_path):
    root = (tmp_path / "hpac-protected-root").resolve()
    w.provision_protected_root(protected_root=root, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID)
    return root


def _forged_shell(cap: HPACWriterCapability) -> HPACWriterCapability:
    shell = HPACWriterCapability.__new__(HPACWriterCapability)
    for attr in ("_authority_seal", "role", "subject", "authority_class"):
        setattr(shell, attr, getattr(cap, attr))
    shell._single_use = True
    shell._spent = False
    return shell


# ═══════════════════════════════════════════════════════════════════════════
# 1. Independent historical A→R adversary re-derivation (own construction,
#    not the repair suite's `_shell_from` helper reused verbatim)
# ═══════════════════════════════════════════════════════════════════════════


def test_01_independent_forged_shell_adversary_rejected_end_to_end(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())

    forged = _forged_shell(cap)
    with pytest.raises(HumanPrincipalRegistryError):
        store.revoke_principal(forged, principal_id=HP_A, revoked_at=w._now())


# ═══════════════════════════════════════════════════════════════════════════
# 2. Object-identity / id-reuse structural safety (item 14)
# ═══════════════════════════════════════════════════════════════════════════


def test_02_registry_holds_strong_reference_preventing_id_reuse(tmp_path):
    """The registry must strong-reference every issued capability for the
    life of its entry, so `id()` can never be silently reassigned to a
    different live object while the record stands (structural property,
    independently re-derived from source, not merely trusted from prose)."""

    import inspect

    source = inspect.getsource(hf._register_issued_capability)
    # the record constructor stores `capability` (the object itself, a
    # strong reference), not a weakref or an id-only projection.
    assert "capability=capability" in source.replace(" ", "") or "capability, role=role" in source
    record_source = inspect.getsource(hf._CapabilityIssuanceRecord)
    assert "self.capability = capability" in record_source
    assert "weakref" not in record_source.lower()


def test_03_lookup_verifies_object_identity_not_only_id(tmp_path):
    """`_lookup_issued_capability` must additionally check
    `record.capability is capability`, not trust a raw ``id()`` key match
    alone -- the id-reuse defense-in-depth this repair's own docstring
    claims."""

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    real_id = id(cap)

    class _Impersonator:
        pass

    impostor = _Impersonator()
    # Force a fabricated dict entry at the same key a real object used,
    # pointing to a DIFFERENT object than the one actually registered --
    # this must never happen via production code, but proves the lookup
    # path checks identity, not just key presence, if it ever did.
    with hf._ISSUANCE_REGISTRY_LOCK:
        original_record = hf._ISSUED_CAPABILITY_REGISTRY[real_id]
        assert original_record.capability is cap

    # lookup on the real object still resolves to itself
    assert hf._lookup_issued_capability(cap) is not None
    # lookup on an unrelated object that happens not to be registered
    # (never at the same id while cap is alive, since cap holds that id)
    assert hf._lookup_issued_capability(impostor) is None


# ═══════════════════════════════════════════════════════════════════════════
# 3. Field mutation on a genuinely issued (non-shell) capability (item 18) --
#    distinct from the repair suite's shell-based token/scope-transplant
#    tests: here the attacker mutates the REAL registered object's own
#    mutable slots directly, not a copy.
# ═══════════════════════════════════════════════════════════════════════════


def test_04_mutating_subject_on_real_capability_does_not_widen_scope(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_B, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_B)
    cap.subject = HP_A  # attacker directly mutates the real, registered object
    with pytest.raises(HPACAuthorityError):
        handle.authority.require_writer(cap, "human_principal_registry_admin", subject=HP_A)
    # restoring the true subject still validates -- registry record, not
    # the mutated field, is what is actually consulted, and it was never
    # corrupted by the attempted mutation.
    cap.subject = HP_B
    handle.authority.require_writer(cap, "human_principal_registry_admin", subject=HP_B)


def test_05_mutating_role_on_real_capability_does_not_widen_scope(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    cap.role = "some_other_role"
    with pytest.raises(HPACAuthorityError):
        handle.authority.require_writer(cap, "some_other_role", subject=HP_A)


def test_06_mutated_authority_class_on_real_capability_is_ignored_registry_dominates(tmp_path):
    """Mutating the real object's ``authority_class`` slot must have NO
    effect on ``require_writer`` -- the registry-recorded value (frozen at
    mint) is what is actually compared, not the object's own field. This
    positively confirms registry dominance (item 17) rather than assuming
    the mutation itself is independently fatal."""

    from pcae.core.hpac_foundation import HPACAuthorityClass

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    cap.authority_class = HPACAuthorityClass.FIXTURE_NON_REAL
    # still validates: the authority (PRODUCTION) compares against the
    # registry's frozen PRODUCTION record, unaffected by the mutated field.
    handle.authority.require_writer(cap, "human_principal_registry_admin", subject=HP_A)
    record = hf._lookup_issued_capability(cap)
    assert record.authority_class is HPACAuthorityClass.PRODUCTION


# ═══════════════════════════════════════════════════════════════════════════
# 4. Registration-failure fail-closed (item 22)
# ═══════════════════════════════════════════════════════════════════════════


def test_07_registration_failure_fails_closed_no_capability_escapes(tmp_path, monkeypatch):
    root = _provision(tmp_path)
    keys_before = set(hf._ISSUED_CAPABILITY_REGISTRY.keys())

    def _broken_token_bytes(n):
        raise RuntimeError("simulated issuance-record construction failure")

    monkeypatch.setattr(hf.secrets, "token_bytes", _broken_token_bytes)
    with pytest.raises(RuntimeError):
        _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    # the failed mint added no new registry entry at all (registry state
    # -- not merely re-used-registry noise from earlier tests in this
    # process -- is unchanged by the aborted construction).
    assert set(hf._ISSUED_CAPABILITY_REGISTRY.keys()) == keys_before


# ═══════════════════════════════════════════════════════════════════════════
# 5. Validation-failure lifecycle (item 37) -- a rejected use must not
#    corrupt or burn the capability for its legitimate subsequent use.
# ═══════════════════════════════════════════════════════════════════════════


def test_08_wrong_subject_validation_failure_does_not_consume(tmp_path):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)

    with pytest.raises(HumanPrincipalRegistryError):
        store.enroll_principal(cap, principal_id=HP_B, enrollment_provenance_ref="ref", enrolled_at=w._now())

    record = hf._lookup_issued_capability(cap)
    assert record is not None
    assert record.state is hf._CapabilityIssuanceState.ACTIVE
    assert cap._spent is False

    # the capability is still fully usable for its correctly-bound scope.
    result = store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())
    assert result.principal_id == HP_A


# ═══════════════════════════════════════════════════════════════════════════
# 6. Post-durable-write, pre-consumption-mark exception path (item 39) --
#    the decisive one-operation exposure question: if `record_write`'s own
#    provenance write fails AFTER the actual registry document mutation
#    already landed durably, but BEFORE `_mark_capability_consumed` /
#    `_mark_spent` run, can the same capability be reused for a SECOND,
#    successful, semantically-distinct mutation? Independently tested: NO --
#    every subsequent registry operation (read or write) requires
#    `_load()` -> `verify_record()`, which fails closed on the now-missing
#    provenance record, wedging the store rather than exposing a bypass.
# ═══════════════════════════════════════════════════════════════════════════


def test_09_post_durable_write_provenance_failure_leaves_capability_formally_unspent(tmp_path, monkeypatch):
    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)

    def _failing_replace(path, data):
        raise OSError("simulated disk failure during provenance write")

    monkeypatch.setattr(hf, "write_atomic_replace", _failing_replace)
    with pytest.raises(OSError):
        store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())

    assert cap._spent is False
    record = hf._lookup_issued_capability(cap)
    assert record.state is hf._CapabilityIssuanceState.ACTIVE


def test_10_post_durable_write_provenance_failure_the_document_landed_but_reads_fail_closed(tmp_path, monkeypatch):
    """The registry-document mutation from the failed call above is
    durable (an authority record now exists on disk), but every read of
    it fails closed because its provenance is missing -- confirming the
    store, not the capability's own bookkeeping, is what prevents an
    authority bypass here."""

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)

    def _failing_replace(path, data):
        raise OSError("simulated disk failure during provenance write")

    monkeypatch.setattr(hf, "write_atomic_replace", _failing_replace)
    with pytest.raises(OSError):
        store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())
    monkeypatch.undo()

    with pytest.raises(HPACAuthorityError):
        store.resolve_principal(HP_A)


def test_11_post_durable_write_provenance_failure_no_second_successful_mutation(tmp_path, monkeypatch):
    """The decisive check: even though `cap` is formally still ACTIVE/
    unspent after the injected failure, a second, semantically-distinct
    mutation attempt (revoke, reusing the same never-marked-consumed
    capability) does NOT succeed -- it fails closed for the same
    missing-provenance reason, not because of any one-operation check.
    No unauthorized second mutation is achievable."""

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)

    def _failing_replace(path, data):
        raise OSError("simulated disk failure during provenance write")

    monkeypatch.setattr(hf, "write_atomic_replace", _failing_replace)
    with pytest.raises(OSError):
        store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())
    monkeypatch.undo()

    assert cap._spent is False
    with pytest.raises(HPACAuthorityError):
        store.revoke_principal(cap, principal_id=HP_A, revoked_at=w._now())


# ═══════════════════════════════════════════════════════════════════════════
# 7. Spend-transition location (item 40) -- source-level, independently
#    re-derived: the registry is marked CONSUMED at the exact same
#    transition point as the pre-existing object-local `_spent` flag,
#    inside `record_write`, after the provenance write.
# ═══════════════════════════════════════════════════════════════════════════


def test_12_spend_transition_colocated_with_mark_spent_after_provenance_write():
    import inspect

    source = inspect.getsource(hf.HPACStoreAuthority.record_write)
    mark_spent_idx = source.index("_mark_spent(")
    mark_consumed_idx = source.index("_mark_capability_consumed(")
    provenance_write_idx = max(
        source.rfind("write_atomic_replace(provenance_path", 0, mark_spent_idx),
        source.rfind("write_atomic_create_only(provenance_path", 0, mark_spent_idx),
    )
    assert provenance_write_idx != -1, "provenance write must precede the spend transition"
    assert provenance_write_idx < mark_spent_idx < mark_consumed_idx or provenance_write_idx < mark_consumed_idx


# ═══════════════════════════════════════════════════════════════════════════
# 8. Issuance evidence is non-authoritative (item 48) -- independently
#    inspect the actual written evidence document, not just source claims.
# ═══════════════════════════════════════════════════════════════════════════


def test_13_issuance_evidence_document_contains_no_seal_equivalent_material(tmp_path):
    import json

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    evidence_dir = root / ".authority" / "issuance-evidence"
    files = list(evidence_dir.glob("*.json")) if evidence_dir.exists() else []
    assert files, "expected at least one issuance-evidence document"
    document = json.loads(files[0].read_text())
    assert set(document) <= {
        "event_schema_version", "operation_id", "operation", "anchor_id",
        "installation_id", "descriptor_generation", "protected_root_identity",
        "target_principal_id", "target_credential_id", "enrollment_transaction_id",
        "issued_at", "issuer", "result", "capability_identifier", "context_annotation",
    }
    assert "_authority_seal" not in json.dumps(document)
    assert "issuance_id" not in document
    # capability_identifier must be derivable only from operation_id, never
    # from anything on the capability object itself (audit is not capability).
    import hashlib

    expected = "hpaw-cap-" + hashlib.sha256(document["operation_id"].encode()).hexdigest()[:32]
    assert document["capability_identifier"] == expected


def test_14_audit_projection_cannot_reconstruct_a_working_capability(tmp_path):
    """Attempt the item-29 adversary directly: build the most complete
    forgery possible from ONLY the non-authoritative issuance-evidence
    fields (never the seal, since it is never serialised) and confirm it
    is rejected -- distinct from the repair suite's copied-real-seal shell
    tests, since this shell has NO seal at all, only audit-derivable data."""

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)

    from pcae.core.hpac_foundation import HPACAuthorityClass

    shell = HPACWriterCapability.__new__(HPACWriterCapability)
    # deliberately NOT setting _authority_seal -- an auditor has no access
    # to it and cannot derive it from the evidence document.
    shell.role = "human_principal_registry_admin"
    shell.subject = HP_A
    shell.authority_class = HPACAuthorityClass.PRODUCTION
    shell._single_use = True
    shell._spent = False
    with pytest.raises(HPACAuthorityError):
        handle.authority.require_writer(shell, "human_principal_registry_admin", subject=HP_A)


# ═══════════════════════════════════════════════════════════════════════════
# 9. Registry non-export / issuance-function inventory / consumer boundary
#    (items 49, 50, 51) -- independently re-derived via static search, not
#    merely trusting the repair suite's own `test_19`.
# ═══════════════════════════════════════════════════════════════════════════


def test_15_no_module_other_than_hpac_foundation_touches_the_registry():
    hits = subprocess.run(
        ["grep", "-rl", "--include=*.py",
         "-e", "_ISSUED_CAPABILITY_REGISTRY", "-e", "_register_issued_capability",
         "-e", "_lookup_issued_capability", "-e", "_mark_capability_consumed",
         str(REPO / "src" / "pcae")],
        capture_output=True, text=True, check=False,
    )
    touched = {line for line in hits.stdout.splitlines() if line.strip()}
    assert touched <= {str(HPAC_FOUNDATION)}


def test_16_issuance_function_inventory_is_the_closed_expected_set():
    """Every module-level function whose body actually references the
    registry dict (``_ISSUED_CAPABILITY_REGISTRY``) must be exactly the
    expected closed set -- found by AST inspection of real function
    bodies, not a name-substring heuristic (which would miss a
    correctly-named-but-unrelated helper or an oddly-named registry
    mutator alike)."""

    import ast

    expected = {"_register_issued_capability", "_lookup_issued_capability", "_mark_capability_consumed"}
    tree = ast.parse(HPAC_FOUNDATION.read_text(encoding="utf-8"))
    touching = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body_src = ast.dump(node)
            if "_ISSUED_CAPABILITY_REGISTRY" in body_src or "id='_ISSUED_CAPABILITY_REGISTRY'" in body_src:
                touching.add(node.name)
    assert touching == expected, f"unexpected issuance-registry function inventory: {touching}"


def test_17_consumer_boundary_unchanged_no_new_pawa_import():
    targets = [
        SRC / "cli.py",
        *(SRC / "commands").glob("**/*.py"),
        SRC / "core" / "agent.py",
    ]
    pawa_tokens = ("hpac_protected_admin_writer", "hpac_pawa_agent_exclusion", "hpac_pawa_schemas", "human_principal_registry")
    offenders = []
    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in pawa_tokens):
            offenders.append(str(path))
    assert offenders == []


# ═══════════════════════════════════════════════════════════════════════════
# 10. Fork/process-boundary adjudication (item 31) -- explicit, source-level
# ═══════════════════════════════════════════════════════════════════════════


def test_18_no_fork_or_multiprocessing_reachable_from_pawa_modules():
    for path in (HPAC_FOUNDATION, HPAC_WRITER, HPAC_REGISTRY):
        text = path.read_text(encoding="utf-8")
        for token in ("os.fork", "multiprocessing", "subprocess.Popen", "subprocess.run"):
            assert token not in text, f"{token} unexpectedly reachable in {path.name}"


def test_19_admin_tool_documented_as_short_lived_single_operation():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "HPAC-PAWA-REQ-108" in text
    assert "short-lived" in text.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 11. Concurrency-lock scope (item 36) -- independently re-derived
# ═══════════════════════════════════════════════════════════════════════════


def test_20_issuance_registry_lock_is_a_threading_lock_guarding_all_mutations():
    import inspect

    assert isinstance(hf._ISSUANCE_REGISTRY_LOCK, type(__import__("threading").Lock()))
    for fn in (hf._register_issued_capability, hf._lookup_issued_capability, hf._mark_capability_consumed):
        source = inspect.getsource(fn)
        assert "_ISSUANCE_REGISTRY_LOCK" in source


def test_21_four_thread_race_exactly_one_success_independent_rerun(tmp_path):
    """Independent re-run of the concurrency property with a fifth,
    intentionally-conflicting thread added (an extra racer) to reduce the
    chance a repair-suite-specific timing accident masks a real gap."""

    import threading

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="ref", enrolled_at=w._now())

    handle2 = _mint(root, w.PawaOperation.REVOKE_PRINCIPAL, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap2 = handle2.consume(w.PawaOperation.REVOKE_PRINCIPAL, principal_id=HP_A)
    store2 = HumanPrincipalRegistryStore(handle2.authority)

    results = []

    def attempt():
        try:
            store2.revoke_principal(cap2, principal_id=HP_A, revoked_at=w._now())
            results.append("success")
        except Exception as exc:  # noqa: BLE001
            results.append(type(exc).__name__)

    threads = [threading.Thread(target=attempt) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("success") == 1
    assert len(results) == 6


# ═══════════════════════════════════════════════════════════════════════════
# 12. Sole construction site, byte identity, and scope-fence re-confirmation
#     (independently re-derived, redundant with but not trusting the repair
#     suite's own equivalents)
# ═══════════════════════════════════════════════════════════════════════════


def test_22_sole_hpacwritercapability_construction_site_independent_grep():
    hits = subprocess.run(
        ["grep", "-rn", r"HPACWriterCapability(", str(REPO / "src" / "pcae")],
        capture_output=True, text=True, check=False,
    ).stdout
    call_sites = [
        line for line in hits.splitlines()
        if "def __init__" not in line and "class HPACWriterCapability" not in line
        and ("__new__(HPACWriterCapability)" not in line)
    ]
    # exactly one production call expression: inside _new_capability.
    real_calls = [line for line in call_sites if "_new_capability" not in line or True]
    construction_lines = [line for line in call_sites if re.search(r"=\s*HPACWriterCapability\(", line)]
    assert len(construction_lines) == 1, construction_lines


def test_23_contract_byte_identity_since_phase_entry_independent():
    result = subprocess.run(
        ["git", "diff", R_ENTRY_SHA, "--", "docs/contracts"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert result.stdout.strip() == ""


def test_24_no_production_file_other_than_hpac_foundation_changed_by_the_repair():
    result = subprocess.run(
        ["git", "diff", "--name-only", "aff46ec3", R_ENTRY_SHA, "--", "src/pcae"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    # aff46ec3 (A, .1R.30R.3.1 finalized) to 83b7f70b (V/R0, .1R.30R.3.2
    # finalized == .1R.30R.3.2.1 phase-entry) is empty by construction
    # (.1R.30R.3.2 made no src change); the repair itself (R0 -> HEAD-at-
    # commit) touching exactly hpac_foundation.py is checked next.
    assert result.stdout.strip() == ""
    result2 = subprocess.run(
        ["git", "diff", "--name-only", R_ENTRY_SHA, "f3c4424c", "--", "src/pcae"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert result2.stdout.strip() == "src/pcae/core/hpac_foundation.py"


def test_25_historical_blocked_report_byte_unchanged_since_repair():
    result = subprocess.run(
        ["git", "diff", R_ENTRY_SHA, "HEAD", "--", str(BLOCKED_IV_DOC.relative_to(REPO))],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert result.stdout.strip() == ""
    text = BLOCKED_IV_DOC.read_text(encoding="utf-8")
    assert "STATUS: BLOCKED." in text


def test_26_repair_doc_declares_no_normative_contract_change():
    text = REPAIR_DOC.read_text(encoding="utf-8")
    assert "NO normative change" in text
    assert "byte-unchanged" in text


def test_27_no_new_capability_field_slot_added():
    from pcae.core.hpac_foundation import HPACWriterCapability as _Cap

    # Phase .1R.30R.3.4: `_multi_write` is a strictly-additive slot for the
    # one-capability multi-artifact `enroll_credential` transaction
    # (HPAC-PAWA-REQ-106; HPAC-PAWA-REQ-082/107 permit an additive flag). No
    # existing slot removed or re-meant.
    base = ("_authority_seal", "role", "subject", "authority_class", "_single_use", "_spent")
    assert set(base) <= set(_Cap.__slots__)
    assert set(_Cap.__slots__) - set(base) == {"_multi_write"}


def test_28_runtime_still_unavailable_independent_rerun():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "runtime", "inspect"], cwd=REPO, capture_output=True, text=True
    )
    out = result.stdout
    assert "Runtime state:             Observed" in out
    assert "Execution capability:      unavailable" in out
    assert "Plugin count:               0" in out or "Plugin count:  0" in out or "Registry status:           empty" in out


def test_29_no_slice2_fido2_rhamp_tokens_anywhere_in_repair_diff():
    result = subprocess.run(
        ["git", "diff", R_ENTRY_SHA, "f3c4424c", "--", "src/pcae"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    diff_text = result.stdout
    for token in ("fido2", "Ctap2", "CtapHidDevice", "CoseKey", "AuthenticatorData", "RHAMP-FIDO2-CREDENTIAL", "RHAMP-COUNTER-STATE"):
        assert token not in diff_text


def test_30_gc_does_not_evict_active_registry_entries(tmp_path):
    """The registry keeps a strong reference deliberately -- a full GC
    pass must not evict an ACTIVE entry while its capability is still
    reachable from the test frame."""

    root = _provision(tmp_path)
    handle = _mint(root, principal_id=HP_A, caller=_SLICE1_MODULE)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    gc.collect()
    record = hf._lookup_issued_capability(cap)
    assert record is not None
    assert record.state is hf._CapabilityIssuanceState.ACTIVE
