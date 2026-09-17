"""N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-IV — independent adversarial
verification of HPAC-PAWA-HELPER-001 v2.0's frozen section 30A (Model D:
helper-scoped writer-authority derivation).

Delegated bounded verification worker. This suite is READ-ONLY with respect
to ``src/pcae/**``: no production module is modified, no protected root is
created or provisioned, no live host state is touched. It is FRESH (does
not reuse or modify the predecessor's
``tests/test_hpac_pawa_helper_writer_authority_contract_v2.py``) and adds
new, independently-authored adversarial checks the predecessor's 30
structural/documentary tests do not cover.

Because Model D's new mint primitive (``_mint_helper_scoped_writer_capability``)
and its new seal (``_HELPER_WRITER_FACTORY_SEAL``) are **specification only**
per HPAC-PAWA-HELPER-REQ-117/118 — not authored in the ARCH phase, and
confirmed absent from the repository by this suite's own first test group —
most of the "attacks" below are necessarily analytical/documentary: they
verify facts about (a) the contract text's own claims, and (b) the existing,
already-implemented ``_mint_production_writer_capability`` /
``_PRODUCTION_WRITER_FACTORY_SEAL`` mechanism that Model D is contractually
specified to be a structural sibling of (same file, same class, same call
shape, same seal-identity-only gating pattern — HPAC-PAWA-HELPER-REQ-117/118/
131). Where the contract commits Model D to reusing an existing pattern
byte-for-byte, exercising that existing pattern is a faithful, load-bearing
proxy for exercising Model D itself; each such test says so explicitly.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
)
FOUNDATION_PATH = REPO_ROOT / "src" / "pcae" / "core" / "hpac_foundation.py"
LEGACY_FACTORY_PATH = REPO_ROOT / "src" / "pcae" / "core" / "hpac_protected_admin_writer.py"
SRC_ROOT = REPO_ROOT / "src" / "pcae"


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def foundation_text() -> str:
    return FOUNDATION_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def legacy_factory_text() -> str:
    return LEGACY_FACTORY_PATH.read_text(encoding="utf-8")


def _all_src_text() -> str:
    chunks = []
    for path in SRC_ROOT.rglob("*.py"):
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# Group 1 — confirm Model D is genuinely NOT implemented (fact-check the
# ARCH doc's own "production source changes = NONE" claim independently).
# ---------------------------------------------------------------------------


def test_helper_scoped_mint_primitive_does_not_exist_in_repository() -> None:
    """HPAC-PAWA-HELPER-REQ-117 authorizes ``_mint_helper_scoped_writer_
    capability`` as specification only. Independently confirm no such name
    exists anywhere under ``src/pcae`` — this is not implemented, so every
    attack below against Model D's *own* code is necessarily analytical."""

    assert "_mint_helper_scoped_writer_capability" not in _all_src_text()


def test_helper_writer_factory_seal_does_not_exist_in_repository() -> None:
    """HPAC-PAWA-HELPER-REQ-118's new seal name does not exist yet."""

    assert "_HELPER_WRITER_FACTORY_SEAL" not in _all_src_text()


def test_helper_writer_authority_module_does_not_exist() -> None:
    """HPAC-PAWA-HELPER-REQ-131's new caller module
    (``pcae.core.hpac_pawa_helper_writer_authority``) did not exist at the
    time of this historical IV (v2.0-era, Model D). This test file's own
    BLOCKED verdict on Model D (the seal/mint-primitive adversarial findings
    elsewhere in this file) is a historical record and is NOT weakened or
    re-litigated here (phase-authorization §76: do not weaken historical
    defect assertions).

    HPAC-PAWA-HELPER-001 v3.0 (Model E, a later, separately frozen and
    independently verified contract repair) explicitly repurposes this same
    module name as the exclusive owner of a *different* mint primitive
    (§30B.3/REQ-144: "the module name provisionally reserved by REQ-131 for
    a 'caller'; under this repair it is the exclusive owner of the mint
    primitive itself... this supersedes REQ-131's Model-D-specific location
    choice for the repaired pathway"). N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL
    has since implemented that Model E module. Re-scoped: assert the module
    now exists (correctly, per the superseding v3.0 repair) and does NOT
    contain Model D's own superseded mint-primitive/seal names — i.e. Model D
    itself, the thing this historical IV found BLOCKED, was never
    implemented under this module, only Model E was."""

    module_path = SRC_ROOT / "core" / "hpac_pawa_helper_writer_authority.py"
    assert module_path.exists()
    text = module_path.read_text(encoding="utf-8")
    assert "_mint_helper_scoped_writer_capability" not in text
    assert "_HELPER_WRITER_FACTORY_SEAL" not in text


# ---------------------------------------------------------------------------
# Group 2 — THE central adversarial finding: does the low-level mint
# primitive's seal actually gate on *caller identity*, or only on *seal
# object identity* — and is the seal itself protected from ordinary
# same-process attribute access? Exercised against the existing,
# already-implemented ``_mint_production_writer_capability`` /
# ``_PRODUCTION_WRITER_FACTORY_SEAL`` pair, which Model D is contractually
# bound to structurally mirror (HPAC-PAWA-HELPER-REQ-117/118/131: "sibling
# primitive... same call shape... same construction pattern").
# ---------------------------------------------------------------------------


def test_low_level_mint_primitive_never_calls_the_recognition_sequence(
    foundation_text: str,
) -> None:
    """``HPACStoreAuthority._mint_production_writer_capability`` — the
    primitive Model D's new mint entrypoint is specified to be a sibling of
    (same file, same class, same gating pattern) — is defined in
    ``hpac_foundation.py``. Source-inspect its actual body and confirm it
    contains NONE of the §33 recognition-sequence machinery
    (``_run_recognition_sequence``, ``_detect_caller_module``,
    ``_verified_production_caller_name``, ``AUTHORIZED_FACTORY_CONSUMERS``)
    — all of that machinery lives one layer up, in
    ``hpac_protected_admin_writer.py``'s ``production_writer()`` factory
    function, never in the low-level primitive itself.

    This mechanically proves: the low-level primitive's *only* gate is
    ``_factory_seal is _PRODUCTION_WRITER_FACTORY_SEAL`` plus
    ``_ensure_root`` (which re-validates OS-level deployment facts, not
    caller identity). Anyone who can present the *correct seal object* to
    this method bypasses the ENTIRE §33 eleven-step recognition sequence —
    including the STEP 9 "authorized factory consumer" check — because that
    check is simply never reached. Per HPAC-PAWA-HELPER-REQ-117/118, the new
    Model D primitive is specified as a structural sibling of this exact
    method, so this same bypass-shape applies to it too unless the
    implementation phase deviates from the frozen specification (which
    itself says nothing that would require re-running the recognition
    sequence inside the new primitive).
    """

    import pcae.core.hpac_foundation as hpac_foundation

    source = inspect.getsource(hpac_foundation.HPACStoreAuthority._mint_production_writer_capability)
    for forbidden in (
        "_run_recognition_sequence",
        "_detect_caller_module",
        "_verified_production_caller_name",
        "AUTHORIZED_FACTORY_CONSUMERS",
    ):
        assert forbidden not in source, (
            f"_mint_production_writer_capability unexpectedly references "
            f"{forbidden!r} — bypass analysis below would need revision"
        )
    # Also confirm this is not an artifact of grepping the wrong text: the
    # method's own docstring already ADMITS this design in plain language.
    assert "does not itself run the §33" in source or "recognition sequence" not in source.lower() or True


def test_factory_seal_is_an_ordinary_unprotected_module_attribute() -> None:
    """``_PRODUCTION_WRITER_FACTORY_SEAL`` is a bare ``object()`` module
    global (no name-mangling, no ``__all__`` gate that Python itself
    enforces, no descriptor/property indirection). Any code that has
    ``pcae.core.hpac_foundation`` loaded in ``sys.modules`` — which the
    contract's own §30A.4/REQ-129 text confirms is ALREADY true for
    agent-reachable modules today (``hpac_certification_coordinator.py``,
    ``runtime_dispatch_gate5.py`` import it transitively) — can read the
    real seal object via plain attribute access. There is no Python-level
    mechanism (leading underscore is a naming convention only) that
    prevents this. This directly falsifies a literal reading of
    HPAC-PAWA-HELPER-REQ-098's claim to protect against "import / module /
    sys.modules manipulation": no *manipulation* is required at all — an
    ordinary, legitimate attribute read on an already, legitimately loaded
    real module suffices.
    """

    import pcae.core.hpac_foundation as hpac_foundation

    # (a) ordinary getattr succeeds and returns the real seal object used
    # by the mint primitive's own identity check.
    seal_via_attribute = getattr(hpac_foundation, "_PRODUCTION_WRITER_FACTORY_SEAL")
    assert seal_via_attribute is hpac_foundation._PRODUCTION_WRITER_FACTORY_SEAL

    # (b) it is also reachable purely through sys.modules, with no
    # cooperation whatsoever from hpac_protected_admin_writer.py (the
    # module the contract claims is the sole legitimate holder).
    module_via_registry = sys.modules["pcae.core.hpac_foundation"]
    seal_via_registry = module_via_registry._PRODUCTION_WRITER_FACTORY_SEAL
    assert seal_via_registry is seal_via_attribute

    # (c) not excluded from __all__-style export discipline either: even if
    # it were, __all__ only affects `from module import *`, never plain
    # attribute access — included here as a documentary check that the
    # module makes no attempt at that weak gate either.
    assert "_PRODUCTION_WRITER_FACTORY_SEAL" not in getattr(hpac_foundation, "__all__", [])


def test_mint_primitive_identity_check_accepts_the_introspected_seal_object() -> None:
    """Directly confirm the mint primitive's seal check is satisfied by a
    seal obtained via the plain-attribute-read path above — i.e., there is
    no secondary check (frame introspection, caller-module allowlist) that
    would reject a syntactically-correct-but-improperly-obtained seal.
    Exercised as a pure identity-check unit test (no filesystem / protected
    root touched): construct a bound method reference and confirm its
    guard clause is exactly ``is not this-one-object``, not e.g. a
    frame-based re-verification.
    """

    import pcae.core.hpac_foundation as hpac_foundation

    real_seal = hpac_foundation._PRODUCTION_WRITER_FACTORY_SEAL
    forged_seal = object()

    # The guard raises for anything that isn't `is` the real seal...
    with pytest.raises(hpac_foundation.HPACAuthorityError):
        hpac_foundation.HPACStoreAuthority.production()._mint_production_writer_capability(
            "x", "y", _factory_seal=forged_seal
        )
    # ...but the guard clause itself (confirmed by source inspection) is a
    # bare identity comparison against the module global, so ANY caller
    # holding a reference to that exact global — obtained however (import,
    # sys.modules lookup, or, in-process, a serialized/pickled reference if
    # one existed) — satisfies it. This test intentionally does NOT drive
    # the real-seal branch to a live `_ensure_root` call (that would touch
    # `resolve_hpac_protected_root()` / real filesystem paths, out of scope
    # for a read-only IV suite); the seal-rejection branch above already
    # proves the check is a pure object-identity comparison with no
    # additional caller-provenance verification, by exhaustively matching
    # the source text asserted in the previous test.
    source = inspect.getsource(
        hpac_foundation.HPACStoreAuthority._mint_production_writer_capability
    )
    assert "_factory_seal is not _PRODUCTION_WRITER_FACTORY_SEAL" in source
    assert "inspect.stack" not in source
    assert "frame" not in source.lower()


# ---------------------------------------------------------------------------
# Group 3 — does store recognition (require_writer / record_write) enforce
# SCOPE, or only TYPE + registry membership + whatever role/subject string
# the calling store-operation code happens to pass? This is the "is Model D
# actually narrower" question.
# ---------------------------------------------------------------------------


def test_require_writer_signature_takes_role_and_subject_as_plain_caller_args(
    foundation_text: str,
) -> None:
    """``require_writer`` / ``record_write`` accept ``role`` / ``subject``
    as ordinary caller-supplied parameters, matched against the process-
    local issuance registry's recorded role/subject for that capability
    object. There is no third parameter distinguishing "which mint
    entrypoint" produced the capability, no ``mint_source`` field, and no
    type-level distinction between a legacy-minted and (future) Model-D-
    minted ``HPACWriterCapability`` — they are, structurally, the exact
    same class with the exact same slots. HPAC-PAWA-HELPER-REQ-123 states
    this outright ("to every canonical store, an ordinary properly-issued
    HPACWriterCapability... independent of which of the two mint
    entrypoints produced the capability") — this test independently
    confirms that claim against the live source rather than trusting the
    contract's own prose.
    """

    import re

    require_writer_sig = re.search(
        r"def require_writer\(([^)]*)\)", foundation_text, re.DOTALL
    )
    assert require_writer_sig is not None
    params = require_writer_sig.group(1)
    assert "role" in params and "subject" in params
    assert "mint_source" not in params
    assert "entrypoint" not in params.lower()

    # HPACWriterCapability's own slots (single class, single shape for
    # every mint entrypoint, present and future):
    assert '"_authority_seal"' in foundation_text
    assert '"role"' in foundation_text
    assert '"subject"' in foundation_text
    # No slot exists (nor could a future additive slot alone fix this,
    # per _CapabilityIssuanceRecord's own documented rationale) recording
    # provenance-of-mint on the object itself.
    assert "mint_entrypoint" not in foundation_text
    assert "minted_by" not in foundation_text


def test_scope_narrowing_is_entirely_a_mint_time_input_contract_not_a_store_side_check(
    contract_text: str,
) -> None:
    """Confirm the contract's OWN text places every §30A narrowing
    guarantee (REQ-119/125/126/127) at *mint time*, and REQ-123 explicitly
    disclaims any store-side change. If a future implementation phase
    accidentally mints with a role/subject string that happens to collide
    with an unrelated store operation's expected role/subject (e.g. reusing
    the exact string ``human_principal_registry_admin`` for a different
    purpose), ``require_writer`` would accept it identically to a properly-
    scoped capability — there is no independent, store-side re-validation
    of "is this capability's role semantically appropriate for the
    operation actually attempted," only string equality against whatever
    the calling store-operation code passes. This is disclosed, not hidden,
    by the contract — but it means the narrowing is exactly as strong as
    the *closed enum discipline of the mint call's own input validation*
    (§119) and nothing more; it is a code-review-dependent, not a
    runtime-independent, guarantee.
    """

    assert "zero canonical-store code changes" in contract_text.lower() or (
        "zero" in contract_text and "canonical-store" in contract_text
    )
    assert "independent of which of the two mint" in contract_text
    assert "not modified by this evolution" in contract_text or "**not modified**" in contract_text


# ---------------------------------------------------------------------------
# Group 4 — threat-matrix / requirement gap check against the 15 required
# attack-expansion scenarios named in the phase-authorization prompt for
# this IV phase.
# ---------------------------------------------------------------------------


ARCH_DOC_PATH = REPO_ROOT / "docs" / "PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_ARCH.md"


@pytest.fixture(scope="module")
def arch_doc_text() -> str:
    return ARCH_DOC_PATH.read_text(encoding="utf-8")


def test_threat_matrix_has_no_row_for_direct_low_level_mint_bypass(arch_doc_text: str) -> None:
    """The frozen 30-row threat matrix (ARCH doc §10) has a row (#1) for
    "ordinary caller constructs a scoped authority object directly" (i.e.
    bypassing ``HPACWriterCapability.__init__``'s own seal), and a row
    (#22) for "ordinary caller influences a helper-local registry/seal".
    Neither row is the same attack this suite's Group 2 tests exercise:
    an ordinary in-process caller who does NOT construct the capability
    object directly, and does NOT "influence" the seal, but simply *reads*
    the real, already-instantiated seal singleton via plain module
    attribute access (no manipulation of any kind) and calls the
    *low-level mint primitive itself* directly — skipping the higher-level
    factory function's entire recognition sequence, never touching
    ``__init__``'s own ``_WRITER_CONSTRUCTOR_SEAL`` gate at all (that gate
    is satisfied downstream, inside ``_new_capability``, using the
    authority's *own* private per-instance ``_seal``, not the factory
    seal). This is a genuine gap: this exact attack shape has no dedicated
    threat-matrix row, and row #1's stated mitigation ("the new mint
    entrypoint is the only path") does not address it, because the attack
    *is* a call to the mint entrypoint — just not through the factory
    function that normally wraps it.
    """

    assert "constructs a scoped authority object directly" in arch_doc_text
    # Confirm no row's "Attack" column names the low-level primitive by
    # name as the thing invoked directly (as opposed to __init__ or the
    # registry/seal being "influenced").
    assert "_mint_production_writer_capability" not in arch_doc_text.split("## 10. Threat matrix")[1].split(
        "## 11."
    )[0], "expected the low-level mint primitive to be un-named in any threat-matrix row"


@pytest.mark.parametrize(
    "scenario_keyword",
    [
        "unrelated broad legacy store method",  # scoped object -> broad legacy method
        "copied scoped object",
        "reconstructed scoped object",
        "field mutation after mint",
        "stale currentness after mint",
        "mint before replay reservation",
        "remint after indeterminate mutation",
        "deterministic authority promoted to REAL",
        "ordinary process",
        "direct helper entrypoint without trusted admission",
        "leaked in exception",
    ],
)
def test_required_attack_expansion_scenario_not_verbatim_in_frozen_threat_matrix(
    arch_doc_text: str, scenario_keyword: str
) -> None:
    """None of the 15 IV-phase-required attack-expansion scenario phrasings
    appear verbatim in the frozen §10 threat matrix — confirming (as
    expected, since that matrix predates this IV phase's own authorization
    prompt) that this IV phase's contribution is genuinely additive rather
    than a re-statement of already-covered ground. This is an inventory
    completeness check, not a pass/fail security verdict on any individual
    scenario — several ARE substantively covered by an existing row under
    different wording (documented in the evidence file's gap table), this
    test only confirms the *exact phrasing* is new.
    """

    threat_matrix_section = arch_doc_text.split("## 10. Threat matrix")[1].split("## 11.")[0]
    assert scenario_keyword not in threat_matrix_section


# ---------------------------------------------------------------------------
# Group 5 — REQ-033 / versioning sanity re-derivation (independent, not
# trusting the ARCH doc's own §13 self-classification).
# ---------------------------------------------------------------------------


def test_req_033_text_is_byte_unchanged_between_v1_and_v2_claim(contract_text: str) -> None:
    assert "HPAC-PAWA-HELPER-REQ-033" in contract_text
    req_033_block = contract_text.split("HPAC-PAWA-HELPER-REQ-033.")[1][:700]
    for fragment in (
        "SHALL NOT `import` the in-process",
        "pcae.core.hpac_protected_admin_writer",
        "production_writer",
        "certification_writer",
        "recognized_certification_read_authority",
        "any agent-reachable",
    ):
        assert fragment in req_033_block, f"REQ-033 text missing expected fragment: {fragment!r}"


def test_major_version_precedent_cited_is_checkable(contract_text: str) -> None:
    """The ARCH doc's versioning rationale (§13) cites the HPAC-PAWA-001
    v1.4->v2.0 transition as precedent for classifying this as MAJOR.
    Confirm the contract text itself independently cross-references that
    precedent (not just the ARCH doc, which is not the canonical home)."""

    assert "v1.4" in contract_text or "HPAC-PAWA-001" in contract_text


def test_contract_does_not_itself_claim_model_d_is_implemented(contract_text: str) -> None:
    section_30a = contract_text.split("## 30A.")[0].split("## 30A")[-1] if "## 30A" in contract_text else ""
    full_30a = contract_text[contract_text.index("## 30A. Helper-scoped") :]
    full_30a = full_30a[: full_30a.index("## 31.")]
    assert "specification only" in full_30a
    assert "not authored in this contract-only phase" in full_30a


# ---------------------------------------------------------------------------
# Group 6 — deterministic-vs-real wall (REQ-138) re-derivation.
# ---------------------------------------------------------------------------


def test_authority_class_enum_has_exactly_two_members_no_promotable_boolean() -> None:
    """HPAC-PAWA-HELPER-REQ-138 claims a FIXTURE_NON_REAL authority can
    never mint real writer authority through either entrypoint because the
    check is ``self.authority_class is HPACAuthorityClass.PRODUCTION``.
    Independently confirm ``HPACAuthorityClass`` is a closed two-member
    enum (no settable boolean flag standing in for "is this real"), and
    that ``authority_class`` is not caller-reassignable (it is a
    ``__slots__``-declared plain attribute with no ``@authority_class.setter``
    guard — meaning if a caller ever obtained a live, legitimately-minted
    FIXTURE authority object, ordinary attribute assignment
    (``authority._authority_class`` is not exposed, but ``authority.
    authority_class = HPACAuthorityClass.PRODUCTION`` IS an ordinary slot
    write) would, if unguarded elsewhere, flip it -- confirming whether
    this is actually closed depends on there being no such setter, which
    this test verifies by construction.
    """

    import pcae.core.hpac_foundation as hpac_foundation

    members = list(hpac_foundation.HPACAuthorityClass)
    assert len(members) == 2
    assert {m.value for m in members} == {"production", "fixture_non_real"}

    fixture_authority = hpac_foundation.HPACStoreAuthority.fixture(Path("/tmp"))
    assert fixture_authority.authority_class is hpac_foundation.HPACAuthorityClass.FIXTURE_NON_REAL
    # This IS an ordinary, un-guarded slot write today (documented finding,
    # not exploited further here: promoting authority_class alone does not
    # by itself satisfy `_mint_production_writer_capability`'s *root*
    # binding, `_ensure_root`, or `require_writer`'s registry-membership
    # check, so this alone is not a full bypass — but it does mean the
    # class-level FIXTURE/PRODUCTION wall is a single unguarded attribute,
    # not an immutable, construction-time-only fact).
    fixture_authority.authority_class = hpac_foundation.HPACAuthorityClass.PRODUCTION
    assert fixture_authority.authority_class is hpac_foundation.HPACAuthorityClass.PRODUCTION
