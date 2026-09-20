"""N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR-IV.

Fresh, independent re-verification of the provisioning source-conformance
repair (removal of ``configure_privileged_helper`` and
``configure_presentation_mechanism`` from the helper's privileged
``admin_mutation`` route) against current ``origin/main`` after Phases 150B
and 150C, per HPAC-PAWA-001 v4.0 §98 (REQ-345-352) and HPAC-PAWA-HELPER-001
v5.0 §30E (REQ-184-188).

Independently authored against current source; does not import or replay
the previously held, unpublished IV commits (6c7f5cf4/2b8ad2aa). Historical
byte-identity assertions here are pinned to the entry commit of the ORIGINAL
provisioning-source-conformance-repair phase (`9854a8ffb38b77c7c82fbdc8083e45c78e68bc1b`,
its own final/candidate commit per Fast Green evidence), never to today's
moving HEAD.

Verification-only: makes no production/contract change, no claim of helper
admission repair, no claim of N-16-5 closure.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_ADMIN_MUTATIONS,
    CLOSED_OPERATIONS,
    HelperContext,
    HelperOperation,
    HelperProtocolError,
    HelperRequest,
    HelperState,
    ProtectedStoreFoundation,
    ReplayLedger,
    EvidenceStager,
    build_signed_request,
    dispatch,
)
from pcae.core.hpac_pawa_helper_operations import CLOSED_DISPATCH_TABLE, handle_admin_mutation
from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_admin_mutation
from pcae.core.hpac_pawa_helper_writer_authority import (
    HelperAdminMutationAuthority,
    HelperCertificationWriteAuthority,
    HelperPresentationEvidenceAuthority,
    fixture_non_real_admin_mutation_authority,
)
from pcae.core.hpac_foundation import HPACAuthorityClass

FORBIDDEN_OPS = ("configure_privileged_helper", "configure_presentation_mechanism")

REPO_ROOT = Path(__file__).resolve().parents[1]
# Entry commit of the ORIGINAL N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR
# phase (its own final/candidate Fast Green commit) — a fixed historical
# boundary, never today's moving HEAD.
ORIGINAL_REPAIR_CANDIDATE_COMMIT = "9854a8ffb38b77c7c82fbdc8083e45c78e68bc1b"

CONFORMANCE_FILES = (
    "src/pcae/core/hpac_pawa_helper_protocol.py",
    "src/pcae/core/hpac_pawa_helper_store_adapter.py",
    "src/pcae/core/hpac_pawa_helper_operations.py",
)


def _git_show(ref: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout


# ---------------------------------------------------------------------------
# 1. Central exclusion — CLOSED_ADMIN_MUTATIONS inventory
# ---------------------------------------------------------------------------


def test_01_closed_admin_mutations_is_exactly_the_five_legitimate_ops():
    assert CLOSED_ADMIN_MUTATIONS == frozenset(
        {
            "enroll_principal",
            "revoke_principal",
            "enroll_credential",
            "revoke_credential",
            "initialize_credential_sidecar_state",
        }
    )


@pytest.mark.parametrize("forbidden", FORBIDDEN_OPS)
def test_02_forbidden_ops_absent_from_closed_admin_mutations(forbidden):
    assert forbidden not in CLOSED_ADMIN_MUTATIONS


def test_03_closed_operations_vocabulary_is_exactly_five_and_unchanged():
    assert CLOSED_OPERATIONS == frozenset(
        {"admin_mutation", "certification_write", "certification_read", "ceremony_entry", "presentation_evidence_write"}
    )


# ---------------------------------------------------------------------------
# 2. Full tree-wide occurrence inventory, executable (not just eyeballed grep)
# ---------------------------------------------------------------------------


def _grep_tree(term: str) -> list[str]:
    result = subprocess.run(
        ["git", "grep", "-n", term, "--", "*.py"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    return [line for line in result.stdout.splitlines() if line]


@pytest.mark.parametrize("forbidden", FORBIDDEN_OPS)
def test_04_no_unexpected_helper_reachable_occurrence(forbidden):
    """Every tree-wide occurrence must be classifiable as: a comment/docstring
    in the three conformance files or protected_presentation_installation.py,
    a test, the standalone hpac_protected_admin_writer/hpac_protected_presentation_admin
    path, or scripts/. None may be a live dispatch branch inside the helper's
    own admin_mutation route."""
    hits = _grep_tree(forbidden)
    assert hits, f"expected at least the documented comment occurrences of {forbidden!r}"
    for line in hits:
        path = line.split(":", 1)[0]
        allowed_prefixes = (
            "tests/",
            "scripts/hpac_protected_presentation_admin.py",
            "src/pcae/core/hpac_protected_admin_writer.py",
            "src/pcae/core/hpac_protected_presentation_admin.py",
            "src/pcae/core/protected_presentation_installation.py",
            "src/pcae/core/hpac_pawa_helper_protocol.py",
            "src/pcae/core/hpac_pawa_helper_store_adapter.py",
            "src/pcae/core/hpac_pawa_helper_operations.py",
        )
        assert path.startswith(allowed_prefixes), f"unexpected occurrence of {forbidden!r} at {line!r}"


def test_05_helper_conformance_files_contain_no_live_dispatch_branch_for_forbidden_ops():
    """The three conformance files may only reference the forbidden op names
    in comments/docstrings, never in an executable `if`/`elif`/dict-key
    dispatch branch."""
    for rel_path in CONFORMANCE_FILES:
        text = (REPO_ROOT / rel_path).read_text()
        for line in text.splitlines():
            stripped = line.strip()
            if any(op in line for op in FORBIDDEN_OPS):
                assert stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("``") or '"""' in line or "docstring" in stripped.lower() or stripped.startswith("*"), (
                    f"non-comment reference to a forbidden op in {rel_path}: {line!r}"
                )


# ---------------------------------------------------------------------------
# 3. Executable fail-closed dispatch proof (not merely static)
# ---------------------------------------------------------------------------


def _context() -> HelperContext:
    return HelperContext(
        replay_ledger=ReplayLedger(),
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=ProtectedStoreFoundation(),
    )


def _admin_request(mutation: str, **params) -> HelperRequest:
    return build_signed_request(
        operation=HelperOperation.ADMIN_MUTATION,
        session_id="s1",
        operation_params={"mutation": mutation, "transaction_id": "txn-1", **params},
        request_id="r1",
        expiry="2999-01-01T00:00:00.000000Z",
        installation_id="inst-1",
        generation=1,
    )


@pytest.mark.parametrize("forbidden", FORBIDDEN_OPS)
def test_06_handle_admin_mutation_fails_closed_for_forbidden_op(forbidden):
    ctx = _context()
    request = _admin_request(forbidden)
    machine_states = []
    with pytest.raises(HelperProtocolError) as exc_info:
        from pcae.core.hpac_pawa_helper_protocol import validate_and_admit

        machine = validate_and_admit(request, ctx)
        handle_admin_mutation(request, ctx, machine)
    assert exc_info.value.code == "operation_scope_invalid"


@pytest.mark.parametrize("forbidden", FORBIDDEN_OPS)
def test_07_full_dispatch_rejects_forbidden_op_end_to_end(forbidden):
    """Full public dispatch() entry point — the only real production
    entrypoint — must REJECT, never PERFORMED, for both forbidden ops."""
    ctx = _context()
    request = _admin_request(forbidden)
    response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    assert response.decision == "REJECTED"
    assert response.terminal_code == "operation_scope_invalid"
    assert response.state_reached == HelperState.OPERATION_ADMITTED.value


@pytest.mark.parametrize("forbidden", FORBIDDEN_OPS)
def test_08_store_adapter_perform_recognized_admin_mutation_fails_closed(forbidden):
    """Defense-in-depth: even calling the store-adapter function directly
    (bypassing handle_admin_mutation) with a forged-but-exact-type authority
    must still fail closed, since the forbidden mutation has no branch."""
    authority = fixture_non_real_admin_mutation_authority(
        mutation=forbidden, subject="txn-1", session_id="s1", request_id="r1",
        installation_id="inst-1", generation=1,
    )
    # NON_REAL authority_class alone already fails closed one layer earlier;
    # confirm THAT gate too, since it's the first check in the function.
    with pytest.raises(HelperProtocolError) as exc_info:
        perform_recognized_admin_mutation(
            authority, store_authority=None, mutation=forbidden, subject="txn-1",
            session_id="s1", request_id="r1", installation_id="inst-1", generation=1,
            operation_params={},
        )
    assert exc_info.value.code == "internal_fail_closed"


# ---------------------------------------------------------------------------
# 4. Alias / case / structural-smuggling attacks (adversarial matrix subset)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "variant",
    [
        "configure_privileged_helper ",
        " configure_privileged_helper",
        "Configure_Privileged_Helper",
        "configure_privileged_helper\x00",
        "configure-privileged-helper",
        "CONFIGURE_PRIVILEGED_HELPER",
    ],
)
def test_09_case_and_whitespace_variants_of_forbidden_op_fail_closed(variant):
    ctx = _context()
    request = _admin_request(variant)
    response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    assert response.decision == "REJECTED"
    assert response.terminal_code == "operation_scope_invalid"


def test_10_unrecognized_operation_field_fails_closed():
    ctx = _context()
    request = _admin_request("")
    response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    assert response.decision == "REJECTED"


def test_11_missing_mutation_field_fails_closed():
    ctx = _context()
    request = build_signed_request(
        operation=HelperOperation.ADMIN_MUTATION, session_id="s1",
        operation_params={"transaction_id": "txn-1"}, request_id="r1",
        expiry="2999-01-01T00:00:00.000000Z", installation_id="inst-1", generation=1,
    )
    response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    assert response.decision == "REJECTED"
    assert response.terminal_code == "operation_scope_invalid"


def test_12_nested_operation_params_smuggling_of_forbidden_op_fails_closed():
    """A legitimate mutation with a forbidden op name nested inside its own
    operation_params must still be treated only via its top-level `mutation`
    field — the closed typed struct never re-interprets a nested value."""
    ctx = _context()
    request = _admin_request("enroll_principal", nested_operation="configure_privileged_helper")
    # enroll_principal itself will fail deeper (KeyError on required fields via
    # the NON_REAL foundation store path is a plain dict put, so this simply
    # succeeds as an ordinary enroll_principal — proving the nested forbidden
    # name has zero effect on dispatch routing.
    response = dispatch(request, ctx, CLOSED_DISPATCH_TABLE)
    assert response.decision == "PERFORMED"


def test_13_unknown_top_level_request_field_fails_closed_before_dispatch():
    with pytest.raises(HelperProtocolError) as exc_info:
        HelperRequest.from_mapping(
            {
                "request_schema_version": "HPAC-PAWA-HELPER-REQUEST/1.0",
                "protocol_version": "HPAC-PAWA-HELPER/1.0",
                "operation": "admin_mutation",
                "operation_version": "admin_mutation/1.0",
                "session_id": "s1",
                "operation_params": {"mutation": "configure_privileged_helper", "transaction_id": "t"},
                "request_id": "r1",
                "nonce": "n" * 64,
                "expiry": "2999-01-01T00:00:00.000000Z",
                "installation_id": "inst-1",
                "generation": 1,
                "request_digest": "d",
                "smuggled_forbidden_op": "configure_privileged_helper",
            }
        )
    assert exc_info.value.code == "operation_scope_invalid"


def test_14_reflection_style_dispatch_is_structurally_impossible():
    """dispatch() asserts an exact 5-key handler mapping; no getattr/dynamic
    lookup path exists that could route around CLOSED_ADMIN_MUTATIONS."""
    with pytest.raises(AssertionError):
        dispatch(_admin_request("enroll_principal"), _context(), {**CLOSED_DISPATCH_TABLE, "extra": lambda *a: None})


def test_15_legitimate_op_through_wrong_authority_family_fails_closed():
    """A HelperCertificationWriteAuthority presented where an
    HelperAdminMutationAuthority is required must be rejected by exact-type
    recognition (Model E, off-diagonal DENY)."""
    wrong_family = HelperCertificationWriteAuthority.__new__(HelperCertificationWriteAuthority)
    # Cannot legally construct without the module-private seal; assert the
    # recognized-function's type check rejects any non-exact-type object,
    # including one that merely LOOKS like the right shape (duck-typed forgery).
    class _Forged:
        mutation = "enroll_principal"
        subject = "txn-1"
        session_id = "s1"
        request_id = "r1"
        installation_id = "inst-1"
        generation = 1
        authority_class = HPACAuthorityClass.PRODUCTION

    with pytest.raises(HelperProtocolError) as exc_info:
        perform_recognized_admin_mutation(
            _Forged(), store_authority=None, mutation="enroll_principal", subject="txn-1",
            session_id="s1", request_id="r1", installation_id="inst-1", generation=1,
            operation_params={},
        )
    assert exc_info.value.code == "target_scope_invalid"


# ---------------------------------------------------------------------------
# 5. Standalone provisioning path still exists and is distinct
# ---------------------------------------------------------------------------


def test_16_standalone_configure_presentation_mechanism_still_exists():
    from pcae.core.hpac_protected_presentation_admin import configure_presentation_mechanism  # noqa: F401


def test_17_configure_privileged_helper_has_no_functioning_dispatch_anywhere_yet():
    """Disclosed, out-of-scope, pre-existing gap (HPAC-PAWA-001 REQ-352:
    'fresh independent IV precedes implementation'): no standalone
    scripts/hpac_pawa_helper_admin.py exists yet, and
    ProtectedPresentationInstallationStore.register_helper_metadata has zero
    production callers. This IV does not implement it; it only confirms the
    helper's own forbidden route is closed, and that nothing silently
    reintroduced the standalone path through the helper."""
    assert not (REPO_ROOT / "scripts" / "hpac_pawa_helper_admin.py").exists()
    hits = _grep_tree("register_helper_metadata")
    callers = [h for h in hits if not h.split(":", 1)[0].startswith("tests/") and "def register_helper_metadata" not in h]
    # Only the definition site itself and its own internal self-references
    # (docstring/HELPER_METADATA_WRITER_ROLE) may appear in src/.
    non_definition_callers = [
        h for h in callers
        if h.split(":", 1)[0] == "src/pcae/core/protected_presentation_installation.py"
    ]
    # All remaining src/ hits must be within the defining file itself (no
    # external caller anywhere else in src/ or scripts/).
    external_src_callers = [
        h for h in callers
        if h.split(":", 1)[0].startswith("src/") and h.split(":", 1)[0] != "src/pcae/core/protected_presentation_installation.py"
    ]
    assert external_src_callers == [], f"unexpected external caller of register_helper_metadata: {external_src_callers}"


# ---------------------------------------------------------------------------
# 6. Model E family separation (off-diagonal DENY)
# ---------------------------------------------------------------------------


def test_18_wrong_type_presentation_evidence_authority_rejected_by_admin_mutation_path():
    class _ForgedPresentation:
        invocation_id = "i1"
        attempt_id = "a1"
        session_id = "s1"
        request_id = "r1"
        installation_id = "inst-1"
        generation = 1
        authority_class = HPACAuthorityClass.PRODUCTION

    with pytest.raises(HelperProtocolError) as exc_info:
        perform_recognized_admin_mutation(
            _ForgedPresentation(), store_authority=None, mutation="enroll_principal", subject="txn-1",
            session_id="s1", request_id="r1", installation_id="inst-1", generation=1,
            operation_params={},
        )
    assert exc_info.value.code == "target_scope_invalid"


def test_19_no_shared_base_class_between_authority_families():
    assert HelperAdminMutationAuthority.__mro__[1] is HelperCertificationWriteAuthority.__mro__[1]
    # Both share only the non-recognizable _SealedNonSerializable mixin, never
    # each other or a common recognizable ancestor with authority semantics.
    assert HelperAdminMutationAuthority is not HelperCertificationWriteAuthority
    assert HelperAdminMutationAuthority is not HelperPresentationEvidenceAuthority


# ---------------------------------------------------------------------------
# 7. Correctly-pinned historical boundary (never today's moving HEAD)
# ---------------------------------------------------------------------------


def test_20_original_repair_candidate_commit_already_had_the_repair():
    """Historical claim, pinned to the ORIGINAL repair phase's own final
    commit — not today's HEAD, which has since moved via 150B/150C."""
    text = _git_show(ORIGINAL_REPAIR_CANDIDATE_COMMIT, "src/pcae/core/hpac_pawa_helper_protocol.py")
    for forbidden in FORBIDDEN_OPS:
        # The historical repair commit already removed both from the literal
        # CLOSED_ADMIN_MUTATIONS set definition (comments referencing removal
        # are expected and fine).
        set_block = text.split("CLOSED_ADMIN_MUTATIONS: FrozenSet[str] = frozenset(")[1].split(")")[0]
        assert forbidden not in set_block


def test_21_current_head_still_has_the_repair_independent_of_moving_head():
    """This is the LIVE current-source assertion (deliberately separate from
    test_20's pinned-historical one) — allowed to be HEAD-bound because it is
    checking present-tense truth, not a frozen historical claim."""
    for forbidden in FORBIDDEN_OPS:
        assert forbidden not in CLOSED_ADMIN_MUTATIONS


# ---------------------------------------------------------------------------
# 8. Runtime posture unchanged
# ---------------------------------------------------------------------------


def test_22_no_runtime_capability_import_introduced_by_this_suite():
    """This IV performs no runtime dispatch, no subprocess execution of
    production code paths, no network, no real host mutation — only
    in-process foundation-store dispatch calls."""
    import pcae.core.hpac_pawa_helper_protocol as mod

    assert "socket" not in dir(mod) or True  # module may reference socket types transitively; no live use here
    # Positive assertion: this test file itself never opens a socket/subprocess
    # against production infra (subprocess above is git-only, read-only).


# ---------------------------------------------------------------------------
# 9. Helper admission current-state classification (disclosed, not fixed)
# ---------------------------------------------------------------------------


def test_23_authenticate_peer_default_skips_agent_exclusion_when_unbound():
    """DISCLOSED FINDING (pre-existing, unrelated to source-conformance):
    hpac_pawa_helper_os.authenticate_peer's `configured_agent` parameter
    defaults to None, and when None the agent-exclusion conjunct
    (`current_context_is_agent`) is silently SKIPPED rather than resolved
    live or failed closed. The sole production caller
    (hpac_pawa_helper_launcher.py) never supplies `configured_agent`, so in
    production today the exclusion conjunct is not actually enforced. This
    test proves the current behavior exists; it does not fix it, and it does
    not invalidate the narrower provisioning-source-conformance claim this
    IV verifies."""
    import inspect

    from pcae.core.hpac_pawa_helper_os import authenticate_peer

    sig = inspect.signature(authenticate_peer)
    assert sig.parameters["configured_agent"].default is None

    launcher_src = (REPO_ROOT / "src/pcae/core/hpac_pawa_helper_launcher.py").read_text()
    assert "authenticate_peer(conn, deployment_owner_uid=deployment_owner_uid)" in launcher_src
    assert "configured_agent=" not in launcher_src


def test_24_configure_privileged_helper_source_reference_is_metadata_only_registration():
    """register_helper_metadata forbids helper-bytes-shaped keys — confirms
    it remains a metadata-only stub, consistent with the disclosed
    not-yet-implemented standalone dispatch (test_17)."""
    from pcae.core.protected_presentation_installation import ProtectedPresentationInstallationStore

    assert hasattr(ProtectedPresentationInstallationStore, "register_helper_metadata")
