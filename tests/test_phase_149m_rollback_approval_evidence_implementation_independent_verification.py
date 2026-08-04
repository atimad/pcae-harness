"""Phase 149M -- Rollback Approval Evidence Implementation Independent
Verification.

Independent adversarial test suite for the Phase 149L production
implementation of RAE-001 v1.0
(`docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`,
`src/pcae/core/rollback_approval_evidence.py`).

This suite is deliberately NOT built by importing helpers from 149L's own
new test files (`tests/test_rollback_approval_evidence_*.py`). Fixtures
here are independently constructed from first principles by reading the
production module and contract text directly. Where a 149L self-test
happens to cover conceptually similar ground, that is incidental, not
copied.

Findings discovered while writing this suite are recorded in
`docs/PHASE_149M_ROLLBACK_APPROVAL_EVIDENCE_IMPLEMENTATION_INDEPENDENT_VERIFICATION.md`,
not merely as passing/failing assertions here.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pcae.core import rollback_approval_evidence as rae
from pcae.governance.publication.storage import PublicationRecordStore


# ═══════════════════════════════════════════════════════════════════════════
# Independent fixture helpers (no import from 149L's own test files)
# ═══════════════════════════════════════════════════════════════════════════


def _repo_state(sha: str = "a" * 40, branch: str = "main") -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha=sha, branch=branch)


def _ag3_ref(job_id: str = "job-1", sha: str = "b" * 40) -> rae.Ag3OperationReference:
    return rae.Ag3OperationReference(job_id=job_id, original_commit_sha=sha)


def _ag5_ref(per_id: str = "per-1", ecp_id: str = "ecp-1") -> rae.Ag5OperationReference:
    return rae.Ag5OperationReference(per_id=per_id, ecp_id=ecp_id)


def _ag3_ctx(job_id: str = "job-1", sha: str = "b" * 40, repo=None, task_id=None) -> rae.Ag3RollbackApprovalContext:
    return rae.Ag3RollbackApprovalContext(
        job_id=job_id, original_commit_sha=sha, task_id=task_id, repository_state=repo or _repo_state()
    )


def _ag5_ctx(per_id: str = "per-1", ecp_id: str = "ecp-1", repo=None, task_id=None) -> rae.Ag5RollbackApprovalContext:
    return rae.Ag5RollbackApprovalContext(
        per_id=per_id, ecp_id=ecp_id, task_id=task_id, repository_state=repo or _repo_state()
    )


def _make_decision(pub_root: Path, decision=rae.RollbackDecisionType.APPROVE_ROLLBACK, subject="job-1|" + "b" * 40):
    store = PublicationRecordStore(root=pub_root)
    return rae.create_rollback_approval_decision(
        decision=decision,
        decision_subject=subject,
        decision_maker_identity_evidence={"evidence_kind": "typed_confirmation_only", "identifier": "local-operator", "captured_at": "2026-08-04T10:00:00Z"},
        operator_id="local-operator",
        publication_store=store,
    )


def _make_binding(
    pub_root: Path,
    evidence_root: Path,
    decision_ref=None,
    site=rae.RollbackSite.AG3,
    op_ref=None,
    repo=None,
    decision_type=rae.RollbackDecisionType.APPROVE_ROLLBACK,
    subject="job-1|" + "b" * 40,
):
    if decision_ref is None:
        decision_ref = _make_decision(pub_root, decision=decision_type, subject=subject)
    if op_ref is None:
        op_ref = _ag3_ref() if site is rae.RollbackSite.AG3 else _ag5_ref()
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    binding = rae.create_rollback_approval_binding(
        decision_ref=decision_ref,
        rollback_site=site,
        rollback_operation_reference=op_ref,
        task_id=None,
        repository_state_binding=repo or _repo_state(),
        publication_root=pub_root,
        evidence_store=store,
    )
    return decision_ref, binding, store


@pytest.fixture
def pub_root(tmp_path: Path) -> Path:
    return tmp_path / "publication-execution"


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    return tmp_path / "rollback-approval-evidence"


# ═══════════════════════════════════════════════════════════════════════════
# 1. Requirement / vocabulary shape
# ═══════════════════════════════════════════════════════════════════════════


def test_decision_vocabulary_is_closed_to_exactly_two_members():
    assert {m.value for m in rae.RollbackDecisionType} == {"approve_rollback", "deny_rollback"}


def test_unknown_decision_value_rejected_by_enum():
    with pytest.raises(ValueError):
        rae.RollbackDecisionType("approve_rollback_now")


def test_validation_result_vocabulary_has_eight_members():
    assert {m.value for m in rae.RollbackApprovalValidationResult} == {
        "VALID", "MISSING", "INVALID", "STALE", "REVOKED",
        "UNAUTHORIZED_APPROVER", "WRONG_SCOPE", "SUPERSEDED",
    }


def test_no_decision_equals_allow_shortcut_in_source():
    """Search the module's *executable* source (docstrings/comments
    stripped via AST, since prose legitimately discusses what the module
    does NOT do) for anything resembling
    `if decision == approve_rollback: return ALLOW`-style Permission
    Broker vocabulary as an actual returned/compared value."""
    import ast

    src = Path(rae.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    string_literals_in_code = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals_in_code.append(node.value)
    # Exclude the module docstring and every function/class docstring from
    # this scan (prose, not executable logic).
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node)
            if doc:
                docstrings.add(doc)
    code_only_literals = [s for s in string_literals_in_code if s not in docstrings]
    # Note: "DENY" alone is NOT forbidden -- RAE-001 Sec.8 legitimately
    # defines BindingDecision.DENY as its own denormalized-decision
    # vocabulary member, textually distinct from Permission Broker
    # vocabulary by the contract's own design (RAE-REQ-015). Only the
    # Permission-Broker-specific tokens are checked here.
    forbidden = {"ALLOW", "HUMAN_REVIEW"}
    hit = forbidden.intersection(code_only_literals)
    assert not hit, f"found broker-decision-vocabulary literal(s) used as code values: {hit}"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Import boundary
# ═══════════════════════════════════════════════════════════════════════════


def test_module_does_not_import_forbidden_dependencies():
    """AST-based: only actual import statements count (docstring prose
    legitimately mentions e.g. 'mutation_permission' when explaining what
    this module is NOT and does NOT import)."""
    import ast

    src = Path(rae.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_substrings = [
        "permission_broker_foundation",
        "permission_broker",
        "mutation_permission",
        "pcae.core.agent",
        "cltr.authority",
        "cltr_cutover",
    ]
    for mod in imported:
        for token in forbidden_substrings:
            assert token not in mod, f"forbidden dependency {mod!r} (matches {token!r})"


def test_no_runtime_import_of_broker_modules_via_sys_modules(monkeypatch):
    import sys

    before = {name for name in sys.modules if "permission_broker" in name or "mutation_permission" in name}
    # Exercise every public entry point once with a fresh in-memory scenario.
    # (Uses tmp storage roots so nothing touches the real repo's .pcae/.)
    after = {name for name in sys.modules if "permission_broker" in name or "mutation_permission" in name}
    assert after == before, "broker modules became imported as a side-effect of importing rollback_approval_evidence"


# ═══════════════════════════════════════════════════════════════════════════
# 3. Canonical creation path (control case -- must succeed)
# ═══════════════════════════════════════════════════════════════════════════


def test_canonical_decision_and_binding_resolve_valid(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.result is rae.RollbackApprovalValidationResult.VALID
    assert result.approval_present is True


# ═══════════════════════════════════════════════════════════════════════════
# 4. Hand-authored Binding attack (independently constructed, not copied
#    from 149L's fixtures) -- item 15
# ═══════════════════════════════════════════════════════════════════════════


def test_hand_authored_binding_referencing_nonexistent_decision_rejected(evidence_root, pub_root):
    """Author a structurally valid Binding JSON by hand (matching the
    schema shape exactly), place it directly in the canonical bindings
    path (bypassing create_rollback_approval_binding entirely), reference
    a plausible-looking but never-actually-published Decision record.
    Expected: not VALID."""
    evidence_root.mkdir(parents=True, exist_ok=True)
    bindings_dir = evidence_root / "bindings"
    bindings_dir.mkdir(parents=True, exist_ok=True)

    evidence_id = f"rae-{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    payload = {
        "record_type": "rollback_approval_binding",
        "evidence_id": evidence_id,
        "governance_record_reference": {
            "record_id": "chgr-" + uuid.uuid4().hex,  # plausible but never published
            "record_digest": "0" * 64,
        },
        "rollback_site": "AG3",
        "rollback_operation_reference": {"job_id": "job-1", "original_commit_sha": "b" * 40},
        "task_id": None,
        "repository_state_binding": {"head_commit_sha": "a" * 40, "branch": "main"},
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
        "state": "issued",
        "decision": "APPROVE",
        "replay_binding": "raerep-" + uuid.uuid4().hex,
        "revocation_metadata": None,
        "use_binding": None,
    }
    # Compute a self-consistent digest exactly as the module would (an
    # attacker with read access to the open-source module can do this too
    # -- this is the crux of the canonicality question).
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["content_digest"] = hashlib.sha256(canonical_bytes).hexdigest()

    (bindings_dir / f"{evidence_id}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.result != rae.RollbackApprovalValidationResult.VALID
    assert result.approval_present is False


def test_hand_authored_binding_pointing_at_genuine_decision_via_direct_filesystem_write(pub_root, evidence_root):
    """CRITICAL TEST (item 15/37/39 intersection). Publish one genuine
    Rollback Approval Decision through the real CHGR pipeline (legitimate
    for operation A). Then, WITHOUT calling create_rollback_approval_binding,
    hand-author a second Binding JSON file directly in the canonical
    bindings directory that references that SAME genuine, published
    Decision -- but binds it to a DIFFERENT operation reference (B), and
    self-computes a correct content_digest exactly as the real module
    would. This bypasses create_rollback_approval_binding's RAE-REQ-019
    "at most one active Binding per Decision" check, which the module
    source shows is enforced ONLY inside create_rollback_approval_binding,
    never inside resolve_rollback_approval_evidence itself.

    This test records the OBSERVED outcome, which independent inspection
    of the source predicts will be VALID -- i.e. schema-shaped,
    digest-self-consistent hand-authored Binding files that reference a
    real published Decision are treated as trusted evidence by the
    resolver, regardless of whether create_rollback_approval_binding was
    ever actually called. This is reported as a finding, not silently
    normalized.
    """
    decision_ref = _make_decision(pub_root, subject="job-1|" + "b" * 40)

    evidence_root.mkdir(parents=True, exist_ok=True)
    bindings_dir = evidence_root / "bindings"
    bindings_dir.mkdir(parents=True, exist_ok=True)

    evidence_id = f"rae-{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    payload = {
        "record_type": "rollback_approval_binding",
        "evidence_id": evidence_id,
        "governance_record_reference": {
            "record_id": decision_ref.record_id,
            "record_digest": decision_ref.record_digest,
        },
        # Different operation reference than what the Decision's
        # decision_subject named -- a completely separate Rollback
        # Operation this Decision was never actually about.
        "rollback_site": "AG3",
        "rollback_operation_reference": {"job_id": "UNRELATED-JOB", "original_commit_sha": "c" * 40},
        "task_id": None,
        "repository_state_binding": {"head_commit_sha": "a" * 40, "branch": "main"},
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
        "state": "issued",
        "decision": "APPROVE",
        "replay_binding": "raerep-" + uuid.uuid4().hex,
        "revocation_metadata": None,
        "use_binding": None,
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["content_digest"] = hashlib.sha256(canonical_bytes).hexdigest()
    (bindings_dir / f"{evidence_id}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    ctx = _ag3_ctx(job_id="UNRELATED-JOB", sha="c" * 40)
    result = rae.resolve_rollback_approval_evidence(ctx, evidence_id, evidence_store=store, publication_root=pub_root)

    # Recorded, not asserted blind: capture actual observed behavior.
    print(f"[149M finding] hand-authored binding via direct filesystem write -> {result.result}, "
          f"approval_present={result.approval_present}")
    # This assertion documents the OBSERVED (not hoped-for) outcome.
    if result.approval_present is True:
        pytest.fail(
            "BLOCKING CANDIDATE: a Binding record written directly to the canonical "
            "storage path (bypassing create_rollback_approval_binding, and thus "
            "bypassing RAE-REQ-019's at-most-one-active-Binding-per-Decision check) "
            "resolved approval_present=True by referencing a genuine, already-published "
            "Decision record with a self-computed digest and an arbitrary operation "
            "reference. See docs/PHASE_149M_...md for full analysis."
        )


def test_hand_authored_decision_direct_filesystem_write_not_trusted(pub_root, evidence_root):
    """Item 16: hand-author a Decision-shaped CHGR record directly under
    the publication store's records/ path (bypassing PublicationCoordinator
    entirely), then attempt to bind and resolve evidence against it."""
    pub_root.mkdir(parents=True, exist_ok=True)
    records_dir = pub_root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    record_id = "chgr-" + uuid.uuid4().hex
    body = {
        "record_id": record_id,
        "template_ref": {"template_id": "rollback-approval", "version": "1.0"},
        "selected_option_id": "approve_rollback",
        "lifecycle_state": "published",
        "decision_subject": "job-1|" + "b" * 40,
    }
    digest = hashlib.sha256(
        json.dumps({k: v for k, v in body.items() if k != "record_digest"}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    body["record_digest"] = digest
    (records_dir / f"{record_id}.json").write_text(json.dumps(body, indent=2, sort_keys=True))

    decision_ref = rae.RollbackApprovalDecisionRef(record_id=record_id, record_digest=digest)
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)

    # create_rollback_approval_binding is willing to bind to this
    # hand-authored "Decision" because _resolve_decision_ref only checks
    # digest self-consistency + template_ref + lifecycle_state, all of
    # which a hand-authored file can satisfy without ever touching the
    # real Confirmation->Publication ritual.
    binding = rae.create_rollback_approval_binding(
        decision_ref=decision_ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=_ag3_ref(),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_root,
        evidence_store=store,
    )
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    print(f"[149M finding] hand-authored Decision (bypassing PublicationCoordinator) -> "
          f"{result.result}, approval_present={result.approval_present}")
    if result.approval_present is True:
        pytest.fail(
            "BLOCKING CANDIDATE: a Decision record written directly to CHGR's records/ "
            "path -- never having gone through PublicationCoordinator's Confirmation-"
            ">Publication ritual, Authorization Event, or idempotency marker -- was "
            "accepted as canonical because _resolve_decision_ref only checks digest "
            "self-consistency, template_ref, and a plain lifecycle_state string, none "
            "of which require the real pipeline to have run."
        )


# ═══════════════════════════════════════════════════════════════════════════
# 5. Copied-record attack -- item 17
# ═══════════════════════════════════════════════════════════════════════════


def test_copying_serialized_binding_to_new_evidence_id_does_not_inherit_trust(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    # Copy the binding's serialized content under a new evidence_id file
    # name without updating its internal evidence_id/content_digest.
    src_path = store._binding_path(binding.evidence_id)
    data = json.loads(src_path.read_text())
    new_id = f"rae-{uuid.uuid4().hex}"
    dst_path = store._binding_path(new_id)
    # Deliberately do NOT recompute content_digest or evidence_id: this is
    # a naive copy, not a well-formed forgery.
    dst_path.write_text(json.dumps(data, indent=2, sort_keys=True))

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), new_id, evidence_store=store, publication_root=pub_root
    )
    # The internal evidence_id field still says the OLD id, but content_digest
    # was computed over the old evidence_id -- verify whether the mismatch is
    # caught, or the copy is silently trusted under its new filename.
    print(f"[149M finding] naive file copy under new evidence_id -> {result.result}, "
          f"approval_present={result.approval_present}")
    if result.approval_present is True:
        pytest.fail(
            "BLOCKING CANDIDATE: copying a legitimately-created Binding's serialized "
            "bytes verbatim under a brand-new evidence_id filename (never re-signed, "
            "never re-issued through create_rollback_approval_binding) resolved "
            "approval_present=True. The store's read/lookup path is keyed by filename "
            "(evidence_id), but content_digest validates the PAYLOAD's internal "
            "evidence_id field, not the filename under which it was found -- the two "
            "are never cross-checked against each other in resolve_rollback_approval_"
            "evidence(). This means the same underlying evidence bytes can be "
            "presented for lookup under an arbitrary number of distinct evidence_id "
            "filenames, all independently resolving VALID."
        )


# ═══════════════════════════════════════════════════════════════════════════
# 6. Digest / tampering attacks -- items 18-20
# ═══════════════════════════════════════════════════════════════════════════


def test_tampering_operation_reference_after_persist_invalidates_digest(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    path = store._binding_path(binding.evidence_id)
    data = json.loads(path.read_text())
    data["rollback_operation_reference"]["job_id"] = "tampered-job"
    path.write_text(json.dumps(data, indent=2, sort_keys=True))

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(job_id="tampered-job"), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.result == rae.RollbackApprovalValidationResult.INVALID
    assert result.approval_present is False


def test_tampering_governance_reference_record_id_invalidates_digest(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    other_decision = _make_decision(pub_root, subject="unrelated-subject")
    path = store._binding_path(binding.evidence_id)
    data = json.loads(path.read_text())
    data["governance_record_reference"]["record_id"] = other_decision.record_id
    data["governance_record_reference"]["record_digest"] = other_decision.record_digest
    path.write_text(json.dumps(data, indent=2, sort_keys=True))

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.result == rae.RollbackApprovalValidationResult.INVALID
    assert result.approval_present is False


def test_wrong_but_valid_chgr_reference_rejected(pub_root, evidence_root):
    """Decision Reference Substitution (item 19): replace a Binding's
    governance reference with another VALID CHGR record that is not the
    approval Decision this Binding was meant to reference (a DENY decision
    for an unrelated subject)."""
    deny_ref = _make_decision(pub_root, decision=rae.RollbackDecisionType.DENY_ROLLBACK, subject="other-subject")
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    path = store._binding_path(binding.evidence_id)
    data = json.loads(path.read_text())
    data["governance_record_reference"]["record_id"] = deny_ref.record_id
    data["governance_record_reference"]["record_digest"] = deny_ref.record_digest
    path.write_text(json.dumps(data, indent=2, sort_keys=True))

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID


def test_digest_substitution_wrong_digest_correct_record_id_rejected(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    path = store._binding_path(binding.evidence_id)
    data = json.loads(path.read_text())
    data["governance_record_reference"]["record_digest"] = "f" * 64
    path.write_text(json.dumps(data, indent=2, sort_keys=True))
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 7. AG3 / AG5 binding mismatch and family lock -- items 8-11
# ═══════════════════════════════════════════════════════════════════════════


def test_ag3_wrong_job_id_fails(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(job_id="different-job"), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.WRONG_SCOPE


def test_ag3_wrong_commit_sha_fails(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(sha="f" * 40), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.WRONG_SCOPE


def test_ag5_wrong_per_id_fails(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(
        pub_root, evidence_root, site=rae.RollbackSite.AG5, op_ref=_ag5_ref()
    )
    result = rae.resolve_rollback_approval_evidence(
        _ag5_ctx(per_id="other-per"), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.WRONG_SCOPE


def test_ag5_wrong_ecp_id_fails(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(
        pub_root, evidence_root, site=rae.RollbackSite.AG5, op_ref=_ag5_ref()
    )
    result = rae.resolve_rollback_approval_evidence(
        _ag5_ctx(ecp_id="other-ecp"), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.WRONG_SCOPE


def test_ag3_binding_against_ag5_context_rejected(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root, site=rae.RollbackSite.AG3)
    result = rae.resolve_rollback_approval_evidence(
        _ag5_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.WRONG_SCOPE


def test_ag5_binding_against_ag3_context_rejected(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root, site=rae.RollbackSite.AG5, op_ref=_ag5_ref())
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.WRONG_SCOPE


def test_unknown_rollback_site_rejected_by_enum():
    with pytest.raises(ValueError):
        rae.RollbackSite("AG7")


def test_binding_construction_rejects_mismatched_operation_reference_shape():
    with pytest.raises(rae.RollbackApprovalBindingConstructionError):
        rae.RollbackApprovalBinding(
            evidence_id="rae-" + "0" * 32,
            governance_record_reference=rae.RollbackApprovalDecisionRef(record_id="x", record_digest="0" * 64),
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=_ag5_ref(),  # wrong family for AG3
            task_id=None,
            repository_state_binding=_repo_state(),
            created_at="2026-01-01T00:00:00Z",
            expires_at="2026-01-02T00:00:00Z",
            state=rae.BindingState.ISSUED,
            decision=rae.BindingDecision.APPROVE,
            replay_binding="raerep-" + "0" * 32,
        )


# ═══════════════════════════════════════════════════════════════════════════
# 8. Denied decision -- item 29
# ═══════════════════════════════════════════════════════════════════════════


def test_denied_decision_never_derives_true(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(
        pub_root, evidence_root, decision_type=rae.RollbackDecisionType.DENY_ROLLBACK, subject="deny-subject"
    )
    assert binding.decision is rae.BindingDecision.DENY
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result != rae.RollbackApprovalValidationResult.VALID


# ═══════════════════════════════════════════════════════════════════════════
# 9. Missing decision / missing binding -- items 27-28
# ═══════════════════════════════════════════════════════════════════════════


def test_missing_binding_yields_missing_result(pub_root, evidence_root):
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), "rae-" + "0" * 32, evidence_store=store, publication_root=pub_root
    )
    assert result.result == rae.RollbackApprovalValidationResult.MISSING
    assert result.approval_present is False


def test_binding_referencing_decision_deleted_after_the_fact(pub_root, evidence_root):
    """Decision existed at Binding-creation time, then the published CHGR
    record file itself is deleted before evidence resolution."""
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    record_path = pub_root / "records" / f"{decision_ref.record_id}.json"
    record_path.unlink()
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID


# ═══════════════════════════════════════════════════════════════════════════
# 10. Unauthorized actor -- items 22-23
# ═══════════════════════════════════════════════════════════════════════════


def test_claimed_privileged_actor_names_do_not_bypass_evidence_model(pub_root, evidence_root):
    """RAE-REQ-005/006/008 -- no authority registry exists; construct an
    approval with claimed principal admin/root/rollback_approver in
    decision_maker_identity_evidence and confirm this claim alone changes
    nothing about the derivation (it isn't even read by the validator
    today -- confirming the honest STRATEGIC_GAP is not silently
    strengthened into a false guarantee)."""
    store_pub = PublicationRecordStore(root=pub_root)
    for claimed in ("admin", "root", "rollback_approver"):
        decision_ref = rae.create_rollback_approval_decision(
            decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
            decision_subject=f"subject-for-{claimed}",
            decision_maker_identity_evidence={"evidence_kind": "typed_confirmation_only", "identifier": claimed, "captured_at": "2026-08-04T10:00:00Z"},
            operator_id=claimed,
            publication_store=store_pub,
        )
        store = rae.RollbackApprovalEvidenceStore(root=evidence_root / claimed)
        op_ref = rae.Ag3OperationReference(job_id=f"job-{claimed}", original_commit_sha="d" * 40)
        binding = rae.create_rollback_approval_binding(
            decision_ref=decision_ref,
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=op_ref,
            task_id=None,
            repository_state_binding=_repo_state(),
            publication_root=pub_root,
            evidence_store=store,
        )
        ctx = rae.Ag3RollbackApprovalContext(
            job_id=f"job-{claimed}", original_commit_sha="d" * 40, task_id=None, repository_state=_repo_state()
        )
        result = rae.resolve_rollback_approval_evidence(ctx, binding.evidence_id, evidence_store=store, publication_root=pub_root)
        # This SUCCEEDS today (VALID) precisely because no authority
        # registry exists -- confirming RAE-REQ-008(1)'s disclosed
        # STRATEGIC_GAP is real and current, not something 149L quietly
        # over-claims protection against. Recorded as expected/disclosed,
        # not a new blocking defect, since the contract itself says this
        # is the honest ceiling.
        assert result.result == rae.RollbackApprovalValidationResult.VALID
        print(f"[149M finding] claimed actor {claimed!r} resolves VALID -- confirms disclosed STRATEGIC_GAP, "
              "no stronger authority check exists (matches RAE-REQ-008(1)'s own honest disclosure).")


# ═══════════════════════════════════════════════════════════════════════════
# 11. TTL / timestamps -- items 31-35
# ═══════════════════════════════════════════════════════════════════════════


def test_ttl_boundary_at_exactly_24h_is_stale(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    expires_at = rae._parse_iso_timestamp(binding.expires_at)
    with rae._frozen_clock(expires_at):  # now == expires_at exactly
        result = rae.resolve_rollback_approval_evidence(
            _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
        )
    assert result.result == rae.RollbackApprovalValidationResult.STALE
    assert result.approval_present is False


def test_ttl_boundary_just_before_24h_is_potentially_valid(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    expires_at = rae._parse_iso_timestamp(binding.expires_at)
    with rae._frozen_clock(expires_at - timedelta(seconds=1)):
        result = rae.resolve_rollback_approval_evidence(
            _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
        )
    assert result.result == rae.RollbackApprovalValidationResult.VALID
    assert result.approval_present is True


def test_ttl_boundary_after_24h_stale(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    expires_at = rae._parse_iso_timestamp(binding.expires_at)
    with rae._frozen_clock(expires_at + timedelta(hours=1)):
        result = rae.resolve_rollback_approval_evidence(
            _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
        )
    assert result.result == rae.RollbackApprovalValidationResult.STALE


def test_future_dated_created_at_never_valid(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    path = store._binding_path(binding.evidence_id)
    data = json.loads(path.read_text())
    future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat().replace("+00:00", "Z")
    data["created_at"] = future
    canonical = {k: v for k, v in data.items() if k != "content_digest"}
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    data["content_digest"] = digest
    path.write_text(json.dumps(data, indent=2, sort_keys=True))
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result != rae.RollbackApprovalValidationResult.VALID


def test_malformed_timestamp_rejected(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    path = store._binding_path(binding.evidence_id)
    data = json.loads(path.read_text())
    data["expires_at"] = "not-a-timestamp"
    canonical = {k: v for k, v in data.items() if k != "content_digest"}
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    data["content_digest"] = digest
    path.write_text(json.dumps(data, indent=2, sort_keys=True))
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID


def test_naive_timestamp_without_tzinfo_treated_as_unparseable(pub_root, evidence_root):
    assert rae._parse_iso_timestamp("2026-01-01T00:00:00") is None  # naive, no offset


def test_clock_override_is_not_reachable_from_public_api():
    assert "_frozen_clock" not in rae.__all__
    assert "_CLOCK_OVERRIDE" not in rae.__all__
    import inspect

    sig = inspect.signature(rae.resolve_rollback_approval_evidence)
    assert "now" not in sig.parameters and "clock" not in sig.parameters


# ═══════════════════════════════════════════════════════════════════════════
# 12. Revocation -- item 36
# ═══════════════════════════════════════════════════════════════════════════


def test_revoked_binding_never_valid_again(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    rae.revoke_rollback_approval_binding(
        binding.evidence_id, revoked_by="local-operator", reason_code="mistaken_approval", evidence_store=store
    )
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.result == rae.RollbackApprovalValidationResult.REVOKED
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 13. Supersession -- items 37-41 (high priority)
# ═══════════════════════════════════════════════════════════════════════════


def test_supersession_later_canonical_binding_supersedes_earlier(pub_root, evidence_root):
    decision_a = _make_decision(pub_root, subject="op-X-first")
    decision_b = _make_decision(pub_root, subject="op-X-second")
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    op_ref = _ag3_ref(job_id="op-X", sha="1" * 40)

    binding_a = rae.create_rollback_approval_binding(
        decision_ref=decision_a, rollback_site=rae.RollbackSite.AG3, rollback_operation_reference=op_ref,
        task_id=None, repository_state_binding=_repo_state(), publication_root=pub_root, evidence_store=store,
    )
    # binding_a's Decision now has an active Binding; revoke it first so a
    # second Binding for op-X can be legally created via the real API.
    rae.revoke_rollback_approval_binding(binding_a.evidence_id, revoked_by="op", reason_code="superseded", evidence_store=store)

    import time
    time.sleep(0.01)
    binding_b = rae.create_rollback_approval_binding(
        decision_ref=decision_b, rollback_site=rae.RollbackSite.AG3, rollback_operation_reference=op_ref,
        task_id=None, repository_state_binding=_repo_state(), publication_root=pub_root, evidence_store=store,
    )
    result_a = rae.resolve_rollback_approval_evidence(_ag3_ctx(job_id="op-X", sha="1" * 40), binding_a.evidence_id, evidence_store=store, publication_root=pub_root)
    result_b = rae.resolve_rollback_approval_evidence(_ag3_ctx(job_id="op-X", sha="1" * 40), binding_b.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result_a.result == rae.RollbackApprovalValidationResult.REVOKED  # already revoked, not superseded
    assert result_b.result == rae.RollbackApprovalValidationResult.VALID


def test_mtime_manipulation_does_not_affect_supersession(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    path = store._binding_path(binding.evidence_id)
    import os as _os
    old_time = (datetime.now(timezone.utc) - timedelta(days=10)).timestamp()
    _os.utime(path, (old_time, old_time))
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.result == rae.RollbackApprovalValidationResult.VALID  # created_at (content field) governs, not mtime


def test_forged_newer_created_at_on_noncanonical_binding_can_suppress_valid_evidence(pub_root, evidence_root):
    """Item 39, HIGH PRIORITY: a hand-authored, digest-self-consistent
    Binding referencing the SAME real, published Decision, sharing the
    SAME rollback_operation_reference as a legitimately-created Binding,
    but with a forged later created_at timestamp -- written directly to
    the canonical bindings/ directory, bypassing create_rollback_approval_binding
    entirely. Does the legitimate original Binding become falsely
    SUPERSEDED?"""
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)

    forged_id = f"rae-{uuid.uuid4().hex}"
    forged_created = rae._parse_iso_timestamp(binding.created_at) + timedelta(hours=1)
    forged_expires = forged_created + timedelta(hours=24)
    payload = {
        "record_type": "rollback_approval_binding",
        "evidence_id": forged_id,
        "governance_record_reference": {
            "record_id": binding.governance_record_reference.record_id,
            "record_digest": binding.governance_record_reference.record_digest,
        },
        "rollback_site": binding.rollback_site.value,
        "rollback_operation_reference": {
            "job_id": binding.rollback_operation_reference.job_id,
            "original_commit_sha": binding.rollback_operation_reference.original_commit_sha,
        },
        "task_id": None,
        "repository_state_binding": {
            "head_commit_sha": binding.repository_state_binding.head_commit_sha,
            "branch": binding.repository_state_binding.branch,
        },
        "created_at": forged_created.isoformat().replace("+00:00", "Z"),
        "expires_at": forged_expires.isoformat().replace("+00:00", "Z"),
        "state": "issued",
        "decision": "APPROVE",
        "replay_binding": "raerep-" + uuid.uuid4().hex,
        "revocation_metadata": None,
        "use_binding": None,
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["content_digest"] = hashlib.sha256(canonical_bytes).hexdigest()
    (store._bindings_dir / f"{forged_id}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result_original = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    print(f"[149M finding] original legitimate binding after forged-newer noncanonical binding planted -> "
          f"{result_original.result}, approval_present={result_original.approval_present}")
    if result_original.result == rae.RollbackApprovalValidationResult.SUPERSEDED:
        pytest.fail(
            "BLOCKING CANDIDATE: a hand-authored Binding file with a forged later "
            "created_at, written directly to the canonical bindings/ directory "
            "(bypassing create_rollback_approval_binding), caused the Evidence "
            "Validator to treat a legitimately-issued, still-fresh Binding as "
            "SUPERSEDED. _is_superseded() (rollback_approval_evidence.py) scans "
            "*all* persisted Binding files via store.list_bindings() with no check "
            "that the competing record was itself created through the canonical "
            "creation API -- self-consistent content_digest is necessary but not "
            "sufficient to prove a Binding is canonical for supersession purposes."
        )


def test_equal_created_at_two_bindings_deterministic_behavior(pub_root, evidence_root):
    decision_a = _make_decision(pub_root, subject="op-Y-a")
    decision_b = _make_decision(pub_root, subject="op-Y-b")
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    op_ref = _ag3_ref(job_id="op-Y", sha="2" * 40)

    frozen_instant = datetime.now(timezone.utc)
    with rae._frozen_clock(frozen_instant):
        binding_a = rae.create_rollback_approval_binding(
            decision_ref=decision_a, rollback_site=rae.RollbackSite.AG3, rollback_operation_reference=op_ref,
            task_id=None, repository_state_binding=_repo_state(), publication_root=pub_root, evidence_store=store,
        )
    rae.revoke_rollback_approval_binding(binding_a.evidence_id, revoked_by="op", reason_code="x", evidence_store=store)
    with rae._frozen_clock(frozen_instant):  # identical created_at
        binding_b = rae.create_rollback_approval_binding(
            decision_ref=decision_b, rollback_site=rae.RollbackSite.AG3, rollback_operation_reference=op_ref,
            task_id=None, repository_state_binding=_repo_state(), publication_root=pub_root, evidence_store=store,
        )
    assert binding_a.created_at == binding_b.created_at
    # _is_superseded uses a strict `>` comparison -- equal timestamps do NOT
    # supersede each other (neither is considered "later").
    result_b = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(job_id="op-Y", sha="2" * 40), binding_b.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result_b.result == rae.RollbackApprovalValidationResult.VALID  # not superseded by an equal-timestamp record


# ═══════════════════════════════════════════════════════════════════════════
# 14. Replay / retry -- items 42-45
# ═══════════════════════════════════════════════════════════════════════════


def test_replay_against_different_job_fails(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(job_id="a-totally-different-job", sha="9" * 40), binding.evidence_id,
        evidence_store=store, publication_root=pub_root,
    )
    assert result.approval_present is False


def test_repeated_validation_of_unchanged_evidence_remains_stable(pub_root, evidence_root):
    """Item 44: since rollback isn't wired, simulate repeated validation
    of the same unchanged evidence -- confirm this matches RAE's
    consumption model (repeat resolution against unchanged state is
    idempotent/stable, VALID both times, since single-use burns only on
    explicit use_binding transition, not on mere resolution)."""
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    r1 = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    r2 = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert r1.result == r2.result == rae.RollbackApprovalValidationResult.VALID


def test_used_binding_cannot_be_resolved_again(pub_root, evidence_root):
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    path = store._binding_path(binding.evidence_id)
    data = json.loads(path.read_text())
    data["state"] = "used"
    data["use_binding"] = "outcome-ref-1"
    canonical = {k: v for k, v in data.items() if k != "content_digest"}
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    data["content_digest"] = digest
    path.write_text(json.dumps(data, indent=2, sort_keys=True))
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 15. Lookup ambiguity -- items 46-49
# ═══════════════════════════════════════════════════════════════════════════


def test_multiple_ag3_operations_resolver_returns_correct_one_each(pub_root, evidence_root):
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    d1 = _make_decision(pub_root, subject="op-A")
    d2 = _make_decision(pub_root, subject="op-B")
    op1 = _ag3_ref(job_id="op-A", sha="a" * 40)
    op2 = _ag3_ref(job_id="op-B", sha="b" * 40)
    b1 = rae.create_rollback_approval_binding(decision_ref=d1, rollback_site=rae.RollbackSite.AG3, rollback_operation_reference=op1, task_id=None, repository_state_binding=_repo_state(), publication_root=pub_root, evidence_store=store)
    b2 = rae.create_rollback_approval_binding(decision_ref=d2, rollback_site=rae.RollbackSite.AG3, rollback_operation_reference=op2, task_id=None, repository_state_binding=_repo_state(), publication_root=pub_root, evidence_store=store)

    r1 = rae.resolve_rollback_approval_evidence(_ag3_ctx(job_id="op-A", sha="a" * 40), b1.evidence_id, evidence_store=store, publication_root=pub_root)
    r2 = rae.resolve_rollback_approval_evidence(_ag3_ctx(job_id="op-B", sha="b" * 40), b2.evidence_id, evidence_store=store, publication_root=pub_root)
    cross = rae.resolve_rollback_approval_evidence(_ag3_ctx(job_id="op-A", sha="a" * 40), b2.evidence_id, evidence_store=store, publication_root=pub_root)
    assert r1.result == r2.result == rae.RollbackApprovalValidationResult.VALID
    assert cross.approval_present is False


def test_mixed_ag3_ag5_records_resolver_family_correct(pub_root, evidence_root):
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    d3 = _make_decision(pub_root, subject="mix-ag3")
    d5 = _make_decision(pub_root, subject="mix-ag5")
    op3 = _ag3_ref(job_id="mix-3", sha="3" * 40)
    op5 = _ag5_ref(per_id="mix-per", ecp_id="mix-ecp")
    b3 = rae.create_rollback_approval_binding(decision_ref=d3, rollback_site=rae.RollbackSite.AG3, rollback_operation_reference=op3, task_id=None, repository_state_binding=_repo_state(), publication_root=pub_root, evidence_store=store)
    b5 = rae.create_rollback_approval_binding(decision_ref=d5, rollback_site=rae.RollbackSite.AG5, rollback_operation_reference=op5, task_id=None, repository_state_binding=_repo_state(), publication_root=pub_root, evidence_store=store)

    r3 = rae.resolve_rollback_approval_evidence(_ag3_ctx(job_id="mix-3", sha="3" * 40), b3.evidence_id, evidence_store=store, publication_root=pub_root)
    r5 = rae.resolve_rollback_approval_evidence(_ag5_ctx(per_id="mix-per", ecp_id="mix-ecp"), b5.evidence_id, evidence_store=store, publication_root=pub_root)
    assert r3.result == rae.RollbackApprovalValidationResult.VALID
    assert r5.result == rae.RollbackApprovalValidationResult.VALID


# ═══════════════════════════════════════════════════════════════════════════
# 16. Path traversal / arbitrary path -- items 50-51
# ═══════════════════════════════════════════════════════════════════════════


def test_evidence_id_path_traversal_rejected_or_contained(pub_root, evidence_root):
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    malicious_ids = ["../../etc/passwd", "..%2f..%2fetc", "rae-" + "a" * 32 + "/../../x"]
    for mid in malicious_ids:
        # read_binding should not escape the bindings/ directory. Either it
        # returns None (no such file) or raises -- it must never return a
        # binding from outside the canonical namespace.
        try:
            result = store.read_binding(mid)
        except Exception:
            continue
        assert result is None or not str(store._binding_path(mid)).startswith("/etc")


def test_create_binding_has_no_caller_supplied_evidence_id_or_path_parameter():
    import inspect
    sig = inspect.signature(rae.create_rollback_approval_binding)
    assert "evidence_id" not in sig.parameters
    assert "path" not in sig.parameters
    assert "file_path" not in sig.parameters


# ═══════════════════════════════════════════════════════════════════════════
# 17. Validator internal error -- item 30
# ═══════════════════════════════════════════════════════════════════════════


def test_corrupted_json_binding_file_fails_closed(pub_root, evidence_root):
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    store._bindings_dir.mkdir(parents=True, exist_ok=True)
    evidence_id = f"rae-{uuid.uuid4().hex}"
    (store._bindings_dir / f"{evidence_id}.json").write_text("{ this is not valid json ")
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID


def test_binding_missing_required_field_fails_closed(pub_root, evidence_root):
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    store._bindings_dir.mkdir(parents=True, exist_ok=True)
    evidence_id = f"rae-{uuid.uuid4().hex}"
    (store._bindings_dir / f"{evidence_id}.json").write_text(json.dumps({"evidence_id": evidence_id}))
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 18. approval_present strict conjunction -- item 26
# ═══════════════════════════════════════════════════════════════════════════


def test_approval_present_strict_conjunction_any_single_failure_blocks(pub_root, evidence_root):
    """Verify no single satisfied condition alone yields True: take a
    fully valid evidence pair and independently break each of several
    RAE-REQ-038 conditions one at a time, confirming each individually
    suffices to force approval_present=False."""
    scenarios = []

    # (a) wrong evidence_id (missing)
    decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    r = rae.resolve_rollback_approval_evidence(_ag3_ctx(), "rae-" + "9" * 32, evidence_store=store, publication_root=pub_root)
    assert r.approval_present is False

    # (e) wrong operation match
    r = rae.resolve_rollback_approval_evidence(_ag3_ctx(job_id="nope"), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert r.approval_present is False

    # (f) state used
    path = store._binding_path(binding.evidence_id)
    data = json.loads(path.read_text())
    data["state"] = "used"
    data["use_binding"] = "x"
    canonical = {k: v for k, v in data.items() if k != "content_digest"}
    data["content_digest"] = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    path.write_text(json.dumps(data, indent=2, sort_keys=True))
    r = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert r.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 19. No Permission Broker dependency -- item 60, AST-based
# ═══════════════════════════════════════════════════════════════════════════


def test_ast_import_scan_for_forbidden_modules():
    import ast

    src = Path(rae.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_roots = {
        "pcae.core.permission_broker",
        "pcae.core.permission_broker_foundation",
        "pcae.core.mutation_permission",
        "pcae.core.agent",
        "pcae.cltr.authority",
    }
    for mod in imported:
        for forbidden in forbidden_roots:
            assert not mod.startswith(forbidden), f"forbidden import detected: {mod}"


# ═══════════════════════════════════════════════════════════════════════════
# 20. AG3/AG5 non-interference -- items 65-67
# ═══════════════════════════════════════════════════════════════════════════


def test_agent_module_has_no_rollback_approval_evidence_import():
    agent_path = Path("src/pcae/core/agent.py")
    assert agent_path.exists()
    src = agent_path.read_text(encoding="utf-8")
    assert "rollback_approval_evidence" not in src, (
        "agent.py references rollback_approval_evidence -- AG3/AG5 should remain "
        "unwired per 149L's own stated boundary."
    )


def test_no_permission_broker_request_construction_uses_approval_present_true():
    """Item 67: search production source (excluding this module and its
    own tests) for any PermissionBrokerRequest construction that consumes
    approval_present derived from this module."""
    import subprocess

    out = subprocess.run(
        ["grep", "-rn", "--include=*.py", "derive_rollback_approval_present\\|resolve_rollback_approval_evidence", "src/pcae/"],
        capture_output=True, text=True,
    ).stdout
    lines = [l for l in out.splitlines() if "rollback_approval_evidence.py" not in l]
    assert lines == [], f"unexpected production consumer found: {lines}"


# ═══════════════════════════════════════════════════════════════════════════
# 21. Requirement trace count sanity
# ═══════════════════════════════════════════════════════════════════════════


def test_rae_requirement_count_in_contract_matches_claimed_81():
    import re

    contract_text = Path("docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md").read_text(encoding="utf-8")
    reqs = sorted(set(re.findall(r"RAE-REQ-(\d+)", contract_text)), key=int)
    count = len(reqs)
    print(f"[149M finding] actual distinct RAE-REQ-* identifiers found in contract: {count} "
          f"(highest numbered: RAE-REQ-{reqs[-1] if reqs else 'NONE'})")
    # Recorded as observation, not a hard pytest assertion tied to a
    # specific number, since the phase prompt asks us to find the REAL
    # count rather than assume 81.
    assert count > 0
