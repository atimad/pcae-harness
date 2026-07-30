"""Production tests for ``pcae.authority_evaluation`` (Phase 147G, AEMIC-001 v1.2).

Covers: model construction/validation/immutability/equality/hashing;
``EvaluationResult``'s closed enum; ``evaluate``'s purity, totality,
determinism, and exact error-precedence ordering (AEMIC-REQ-104-105);
the ``AuthorityRegistry`` ABC via an in-memory test double
(AEMIC-REQ-009); serialization round-trip including Unicode; the
forbidden-import/package-boundary guard; and disclosure-only naming.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import pytest

from pcae.authority_evaluation import (
    AuthorityEvaluationError,
    AuthorityEvaluationOutcome,
    AuthorityRegistry,
    AuthorityRegistryCorruptError,
    AuthorityRegistryUnavailableError,
    EligibleAuthorityDeclaration,
    EvaluationResult,
    InvalidClaimedIdentityError,
    InvalidTemplateReferenceError,
    MalformedDeclarationError,
    MissingCitationTextError,
    TemplateIdentityMismatchError,
    UnsupportedSchemaVersionError,
    evaluate,
)
from pcae.authority_evaluation import serialization
from pcae.authority_evaluation.models import (
    DECLARATION_SCHEMA_VERSION,
    EVALUATOR_VERSION,
    OUTCOME_SCHEMA_VERSION,
)

_TS_A = "2026-01-01T00:00:00+00:00"
_TS_B = "2026-01-02T00:00:00+00:00"


def _declaration(
    template_ref: str = "tpl-1",
    template_version: str = "v1",
    eligible_identities: frozenset = frozenset({"alice", "bob"}),
    declared_at: str = _TS_A,
    declared_by: str = "authoring-workflow",
) -> EligibleAuthorityDeclaration:
    return EligibleAuthorityDeclaration(
        template_ref=template_ref,
        template_version=template_version,
        eligible_identities=eligible_identities,
        declared_at=declared_at,
        declared_by=declared_by,
    )


# --- EligibleAuthorityDeclaration -------------------------------------------


class TestEligibleAuthorityDeclaration:
    def test_valid_construction_succeeds(self):
        decl = _declaration()
        assert decl.template_ref == "tpl-1"
        assert decl.eligible_identities == frozenset({"alice", "bob"})
        assert decl.schema_version == DECLARATION_SCHEMA_VERSION

    def test_immutable(self):
        decl = _declaration()
        with pytest.raises(Exception):
            decl.template_ref = "other"  # type: ignore[misc]

    def test_equality_and_hashing(self):
        a = _declaration()
        b = _declaration()
        assert a == b
        assert hash(a) == hash(b)
        assert len({a, b}) == 1

    def test_inequality_on_different_identities(self):
        a = _declaration()
        b = _declaration(eligible_identities=frozenset({"carol"}))
        assert a != b

    @pytest.mark.parametrize(
        "field_name,value",
        [
            ("template_ref", ""),
            ("template_version", ""),
            ("declared_at", ""),
            ("declared_by", ""),
        ],
    )
    def test_empty_required_string_field_raises(self, field_name, value):
        kwargs = {
            "template_ref": "tpl-1",
            "template_version": "v1",
            "eligible_identities": frozenset({"alice"}),
            "declared_at": _TS_A,
            "declared_by": "someone",
        }
        kwargs[field_name] = value
        with pytest.raises(MalformedDeclarationError):
            EligibleAuthorityDeclaration(**kwargs)

    def test_empty_eligible_identities_raises(self):
        with pytest.raises(MalformedDeclarationError):
            _declaration(eligible_identities=frozenset())

    def test_non_str_member_raises(self):
        with pytest.raises(MalformedDeclarationError):
            _declaration(eligible_identities=frozenset({"alice", 42}))  # type: ignore[arg-type]

    def test_malformed_declared_at_raises(self):
        with pytest.raises(MalformedDeclarationError):
            _declaration(declared_at="not-a-timestamp")

    def test_wrong_schema_version_raises(self):
        with pytest.raises(MalformedDeclarationError):
            EligibleAuthorityDeclaration(
                template_ref="tpl-1",
                template_version="v1",
                eligible_identities=frozenset({"alice"}),
                declared_at=_TS_A,
                declared_by="someone",
                schema_version="wrong/1.0",
            )

    def test_no_extra_field_accepted(self):
        with pytest.raises(TypeError):
            EligibleAuthorityDeclaration(
                template_ref="tpl-1",
                template_version="v1",
                eligible_identities=frozenset({"alice"}),
                declared_at=_TS_A,
                declared_by="someone",
                role="admin",  # type: ignore[call-arg]
            )


# --- AuthorityEvaluationOutcome ----------------------------------------------


def _outcome(
    evaluation_result: EvaluationResult = EvaluationResult.ELIGIBLE,
    citation_text: Optional[str] = "cited text",
    declaration_ref: Optional[str] = "tpl-1::v1",
) -> AuthorityEvaluationOutcome:
    return AuthorityEvaluationOutcome(
        template_ref="tpl-1",
        template_version="v1",
        claimed_identity="alice",
        evaluation_result=evaluation_result,
        declaration_ref=declaration_ref,
        citation_text=citation_text,
        evaluated_at=_TS_B,
        evaluator_version=EVALUATOR_VERSION,
    )


class TestAuthorityEvaluationOutcome:
    @pytest.mark.parametrize(
        "result,citation,decl_ref",
        [
            (EvaluationResult.ELIGIBLE, "cited text", "tpl-1::v1"),
            (EvaluationResult.INELIGIBLE, None, "tpl-1::v1"),
            (EvaluationResult.INDETERMINATE, None, None),
        ],
    )
    def test_valid_construction_for_each_result(self, result, citation, decl_ref):
        outcome = _outcome(evaluation_result=result, citation_text=citation, declaration_ref=decl_ref)
        assert outcome.evaluation_result is result
        assert outcome.schema_version == OUTCOME_SCHEMA_VERSION

    def test_immutable(self):
        outcome = _outcome()
        with pytest.raises(Exception):
            outcome.claimed_identity = "someone-else"  # type: ignore[misc]

    def test_equality_and_hashing(self):
        a = _outcome()
        b = _outcome()
        assert a == b
        assert hash(a) == hash(b)

    def test_citation_present_on_non_eligible_raises(self):
        with pytest.raises(MalformedDeclarationError):
            _outcome(evaluation_result=EvaluationResult.INELIGIBLE, citation_text="should not be here")

    def test_citation_absent_on_eligible_raises(self):
        with pytest.raises(MalformedDeclarationError):
            _outcome(evaluation_result=EvaluationResult.ELIGIBLE, citation_text=None)

    def test_wrong_schema_version_raises(self):
        with pytest.raises(MalformedDeclarationError):
            AuthorityEvaluationOutcome(
                template_ref="tpl-1",
                template_version="v1",
                claimed_identity="alice",
                evaluation_result=EvaluationResult.INDETERMINATE,
                declaration_ref=None,
                citation_text=None,
                evaluated_at=_TS_B,
                evaluator_version=EVALUATOR_VERSION,
                schema_version="wrong/1.0",
            )


# --- EvaluationResult --------------------------------------------------------


class TestEvaluationResult:
    def test_three_members(self):
        assert {m.value for m in EvaluationResult} == {"eligible", "ineligible", "indeterminate"}

    def test_not_a_str_subclass(self):
        assert not isinstance(EvaluationResult.ELIGIBLE, str)

    def test_unknown_value_does_not_coerce(self):
        with pytest.raises(ValueError):
            EvaluationResult("unknown")

    def test_comparable(self):
        assert EvaluationResult.ELIGIBLE == EvaluationResult.ELIGIBLE
        assert EvaluationResult.ELIGIBLE != EvaluationResult.INELIGIBLE


# --- evaluate(): happy paths for all three branches --------------------------


class TestEvaluateHappyPaths:
    def test_eligible(self):
        decl = _declaration()
        outcome = evaluate(
            "tpl-1", "v1", "alice", decl, _TS_B, EVALUATOR_VERSION, citation_text="the citation"
        )
        assert outcome.evaluation_result is EvaluationResult.ELIGIBLE
        assert outcome.citation_text == "the citation"
        assert outcome.declaration_ref == "tpl-1::v1"
        assert outcome.template_ref == "tpl-1"
        assert outcome.template_version == "v1"

    def test_ineligible(self):
        decl = _declaration()
        outcome = evaluate("tpl-1", "v1", "mallory", decl, _TS_B, EVALUATOR_VERSION)
        assert outcome.evaluation_result is EvaluationResult.INELIGIBLE
        assert outcome.citation_text is None
        assert outcome.declaration_ref == "tpl-1::v1"

    def test_indeterminate_no_declaration(self):
        outcome = evaluate("tpl-1", "v1", "alice", None, _TS_B, EVALUATOR_VERSION)
        assert outcome.evaluation_result is EvaluationResult.INDETERMINATE
        assert outcome.citation_text is None
        assert outcome.declaration_ref is None
        # BF-147F.1-1 repair: template identity fully reachable/mandatory
        # even when no Declaration resolved.
        assert outcome.template_ref == "tpl-1"
        assert outcome.template_version == "v1"


# --- evaluate(): malformed inputs --------------------------------------------


class TestEvaluateMalformedInputs:
    @pytest.mark.parametrize("bad_template_ref", ["", None, 42])
    def test_invalid_template_ref_raises(self, bad_template_ref):
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate(bad_template_ref, "v1", "alice", None, _TS_B, EVALUATOR_VERSION)

    @pytest.mark.parametrize("bad_template_version", ["", None, 42])
    def test_invalid_template_version_raises(self, bad_template_version):
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate("tpl-1", bad_template_version, "alice", None, _TS_B, EVALUATOR_VERSION)

    @pytest.mark.parametrize("bad_identity", ["", None, 42])
    def test_invalid_claimed_identity_raises(self, bad_identity):
        with pytest.raises(InvalidClaimedIdentityError):
            evaluate("tpl-1", "v1", bad_identity, None, _TS_B, EVALUATOR_VERSION)

    def test_eligible_without_citation_raises(self):
        decl = _declaration()
        with pytest.raises(MissingCitationTextError):
            evaluate("tpl-1", "v1", "alice", decl, _TS_B, EVALUATOR_VERSION)

    def test_ineligible_with_stray_citation_is_disregarded_not_raised(self):
        decl = _declaration()
        outcome = evaluate(
            "tpl-1", "v1", "mallory", decl, _TS_B, EVALUATOR_VERSION, citation_text="stray"
        )
        assert outcome.evaluation_result is EvaluationResult.INELIGIBLE
        assert outcome.citation_text is None

    def test_indeterminate_with_stray_citation_is_disregarded_not_raised(self):
        outcome = evaluate(
            "tpl-1", "v1", "alice", None, _TS_B, EVALUATOR_VERSION, citation_text="stray"
        )
        assert outcome.evaluation_result is EvaluationResult.INDETERMINATE
        assert outcome.citation_text is None


# --- evaluate(): template identity mismatch (BF-147F.1-1 repair) ------------


class TestEvaluateTemplateIdentityMismatch:
    def test_template_ref_mismatch_raises(self):
        decl = _declaration(template_ref="tpl-1")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("tpl-OTHER", "v1", "alice", decl, _TS_B, EVALUATOR_VERSION, citation_text="c")

    def test_template_version_mismatch_raises(self):
        decl = _declaration(template_version="v1")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("tpl-1", "v-OTHER", "alice", decl, _TS_B, EVALUATOR_VERSION, citation_text="c")

    def test_matching_identity_does_not_raise(self):
        decl = _declaration(template_ref="tpl-1", template_version="v1")
        outcome = evaluate("tpl-1", "v1", "alice", decl, _TS_B, EVALUATOR_VERSION, citation_text="c")
        assert outcome.evaluation_result is EvaluationResult.ELIGIBLE


# --- evaluate(): exact error precedence (AEMIC-REQ-104-105) -----------------


class TestEvaluateErrorPrecedence:
    def test_malformed_template_ref_beats_mismatched_declaration(self):
        decl = _declaration(template_ref="tpl-1", template_version="v1")
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate("", "v-OTHER", "alice", decl, _TS_B, EVALUATOR_VERSION)

    def test_malformed_claimed_identity_beats_mismatched_declaration(self):
        decl = _declaration(template_ref="tpl-1", template_version="v1")
        with pytest.raises(InvalidClaimedIdentityError):
            evaluate("tpl-1", "v1", "", decl, _TS_B, EVALUATOR_VERSION)

    def test_mismatch_beats_missing_citation(self):
        decl = _declaration(template_ref="tpl-1", template_version="v1")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("tpl-OTHER", "v1", "alice", decl, _TS_B, EVALUATOR_VERSION)

    def test_malformed_template_ref_beats_missing_citation(self):
        decl = _declaration(template_ref="tpl-1", template_version="v1")
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate(None, "v1", "alice", decl, _TS_B, EVALUATOR_VERSION)


# --- Determinism --------------------------------------------------------


class TestEvaluateDeterminism:
    def test_identical_inputs_produce_field_identical_outcome(self):
        decl = _declaration()
        first = evaluate("tpl-1", "v1", "alice", decl, _TS_B, EVALUATOR_VERSION, citation_text="c")
        second = evaluate("tpl-1", "v1", "alice", decl, _TS_B, EVALUATOR_VERSION, citation_text="c")
        assert first == second

    def test_identical_malformed_inputs_raise_identical_exception_type(self):
        for _ in range(2):
            with pytest.raises(InvalidClaimedIdentityError):
                evaluate("tpl-1", "v1", "", None, _TS_B, EVALUATOR_VERSION)

    def test_no_side_effects_on_declaration(self):
        decl = _declaration()
        before = (decl.template_ref, decl.template_version, decl.eligible_identities)
        evaluate("tpl-1", "v1", "alice", decl, _TS_B, EVALUATOR_VERSION, citation_text="c")
        after = (decl.template_ref, decl.template_version, decl.eligible_identities)
        assert before == after


# --- AuthorityRegistry ABC + in-memory test double --------------------------


class _InMemoryRegistry(AuthorityRegistry):
    """Minimal in-memory test double (AEMIC-REQ-009) -- never a concrete
    production Registry; lives in tests/, not in src/pcae/authority_evaluation."""

    def __init__(self, records: Optional[Dict[Tuple[str, str], EligibleAuthorityDeclaration]] = None):
        self._records = dict(records or {})

    def resolve(
        self, template_ref: str, template_version: str
    ) -> Optional[EligibleAuthorityDeclaration]:
        return self._records.get((template_ref, template_version))


class _UnavailableRegistry(AuthorityRegistry):
    def resolve(self, template_ref, template_version):
        raise AuthorityRegistryUnavailableError("storage layer unreachable")


class _CorruptRegistry(AuthorityRegistry):
    def resolve(self, template_ref, template_version):
        raise AuthorityRegistryCorruptError("duplicate record detected")


class TestAuthorityRegistry:
    def test_abc_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            AuthorityRegistry()  # type: ignore[abstract]

    def test_resolve_returns_declaration_when_present(self):
        decl = _declaration()
        registry = _InMemoryRegistry({("tpl-1", "v1"): decl})
        assert registry.resolve("tpl-1", "v1") == decl

    def test_resolve_returns_none_never_raises_when_absent(self):
        registry = _InMemoryRegistry()
        assert registry.resolve("tpl-1", "v1") is None

    def test_resolve_is_pure_and_repeatable(self):
        decl = _declaration()
        registry = _InMemoryRegistry({("tpl-1", "v1"): decl})
        assert registry.resolve("tpl-1", "v1") == registry.resolve("tpl-1", "v1")

    def test_two_distinct_versions_resolve_independently(self):
        decl_v1 = _declaration(template_version="v1")
        decl_v2 = _declaration(template_version="v2")
        registry = _InMemoryRegistry({("tpl-1", "v1"): decl_v1, ("tpl-1", "v2"): decl_v2})
        assert registry.resolve("tpl-1", "v1") == decl_v1
        assert registry.resolve("tpl-1", "v2") == decl_v2

    def test_unavailable_registry_raises_distinct_from_corrupt_and_none(self):
        with pytest.raises(AuthorityRegistryUnavailableError):
            _UnavailableRegistry().resolve("tpl-1", "v1")

    def test_corrupt_registry_raises_distinct_from_unavailable_and_none(self):
        with pytest.raises(AuthorityRegistryCorruptError):
            _CorruptRegistry().resolve("tpl-1", "v1")

    def test_evaluate_has_no_registry_dependency(self):
        # evaluate() never calls resolve(); passing a declaration directly
        # is the only channel (AEMIC-REQ-073).
        decl = _declaration()
        outcome = evaluate("tpl-1", "v1", "alice", decl, _TS_B, EVALUATOR_VERSION, citation_text="c")
        assert outcome.evaluation_result is EvaluationResult.ELIGIBLE


# --- Serialization ------------------------------------------------------


class TestSerialization:
    def test_declaration_round_trip(self):
        decl = _declaration()
        payload = serialization.declaration_to_payload(decl)
        assert json.dumps(payload, sort_keys=True)  # must be JSON-serializable
        assert serialization.declaration_from_payload(payload) == decl

    def test_outcome_round_trip_for_each_branch(self):
        for outcome in (
            _outcome(EvaluationResult.ELIGIBLE, "c", "tpl-1::v1"),
            _outcome(EvaluationResult.INELIGIBLE, None, "tpl-1::v1"),
            _outcome(EvaluationResult.INDETERMINATE, None, None),
        ):
            payload = serialization.outcome_to_payload(outcome)
            assert json.dumps(payload, sort_keys=True)
            assert serialization.outcome_from_payload(payload) == outcome

    def test_indeterminate_outcome_round_trip_preserves_template_identity(self):
        outcome = evaluate("tpl-1", "v1", "alice", None, _TS_B, EVALUATOR_VERSION)
        payload = serialization.outcome_to_payload(outcome)
        restored = serialization.outcome_from_payload(payload)
        assert restored.template_ref == "tpl-1"
        assert restored.template_version == "v1"
        assert restored == outcome

    def test_unicode_round_trips_byte_for_byte(self):
        decl = _declaration(
            eligible_identities=frozenset({"üser-éè", "中文用户"}),
            declared_by="ééé",
        )
        payload = serialization.declaration_to_payload(decl)
        raw = json.dumps(payload, sort_keys=True)
        restored = serialization.declaration_from_payload(json.loads(raw))
        assert restored == decl

        outcome = _outcome(citation_text="引用: élégible")
        payload2 = serialization.outcome_to_payload(outcome)
        raw2 = json.dumps(payload2, sort_keys=True)
        restored2 = serialization.outcome_from_payload(json.loads(raw2))
        assert restored2 == outcome

    def test_declaration_unrecognized_schema_version_raises(self):
        payload = serialization.declaration_to_payload(_declaration())
        payload["schema_version"] = "unknown/9.9"
        with pytest.raises(UnsupportedSchemaVersionError):
            serialization.declaration_from_payload(payload)

    def test_outcome_unrecognized_schema_version_raises(self):
        payload = serialization.outcome_to_payload(_outcome())
        payload["schema_version"] = "unknown/9.9"
        with pytest.raises(UnsupportedSchemaVersionError):
            serialization.outcome_from_payload(payload)

    def test_declaration_missing_field_raises(self):
        payload = serialization.declaration_to_payload(_declaration())
        del payload["declared_by"]
        with pytest.raises(MalformedDeclarationError):
            serialization.declaration_from_payload(payload)

    def test_declaration_null_field_raises(self):
        payload = serialization.declaration_to_payload(_declaration())
        payload["eligible_identities"] = None
        with pytest.raises(MalformedDeclarationError):
            serialization.declaration_from_payload(payload)

    def test_outcome_missing_field_raises(self):
        payload = serialization.outcome_to_payload(_outcome())
        del payload["claimed_identity"]
        with pytest.raises(MalformedDeclarationError):
            serialization.outcome_from_payload(payload)

    def test_outcome_null_evaluation_result_raises(self):
        payload = serialization.outcome_to_payload(_outcome())
        payload["evaluation_result"] = None
        with pytest.raises(MalformedDeclarationError):
            serialization.outcome_from_payload(payload)

    def test_outcome_unrecognized_evaluation_result_raises(self):
        payload = serialization.outcome_to_payload(_outcome())
        payload["evaluation_result"] = "not-a-real-result"
        with pytest.raises(MalformedDeclarationError):
            serialization.outcome_from_payload(payload)

    def test_outcome_cross_field_invariant_enforced_on_deserialize(self):
        # citation_text present alongside a non-eligible evaluation_result
        # in a hand-crafted payload is rejected by the constructor's own
        # invariant (F-147F.1-4's own disclosed area, still enforced here).
        payload = serialization.outcome_to_payload(
            _outcome(EvaluationResult.INELIGIBLE, None, "tpl-1::v1")
        )
        payload["citation_text"] = "fabricated"
        with pytest.raises(MalformedDeclarationError):
            serialization.outcome_from_payload(payload)


# --- Disclosure-only naming/semantics audit (§8) -----------------------------


_FORBIDDEN_NAME_FRAGMENTS = ("authorize", "grant", "permit", "allow", "deny")


def _package_files():
    root = Path(__file__).resolve().parents[1] / "src" / "pcae" / "authority_evaluation"
    return sorted(root.glob("*.py"))


class TestDisclosureOnlySemantics:
    def test_no_public_name_implies_authorization(self):
        import pcae.authority_evaluation as pkg

        for name in pkg.__all__:
            lowered = name.lower()
            for fragment in _FORBIDDEN_NAME_FRAGMENTS:
                assert fragment not in lowered, (
                    f"Public name {name!r} contains {fragment!r}, which could be "
                    "mistaken for an authorization primitive (AEMIC-REQ-027)."
                )

    def test_evaluation_result_alone_distinguishes_ineligible_from_indeterminate(self):
        decl = _declaration()
        ineligible = evaluate("tpl-1", "v1", "mallory", decl, _TS_B, EVALUATOR_VERSION)
        indeterminate = evaluate("tpl-1", "v1", "mallory", None, _TS_B, EVALUATOR_VERSION)
        assert ineligible.evaluation_result is EvaluationResult.INELIGIBLE
        assert indeterminate.evaluation_result is EvaluationResult.INDETERMINATE
        assert ineligible.evaluation_result != indeterminate.evaluation_result

    def test_matching_identity_does_not_by_itself_prove_authority(self):
        # AEMIC-REQ-107: a matching template identity check passing does
        # not, by itself, prove authority -- claimed_identity must still
        # separately be a set member.
        decl = _declaration(eligible_identities=frozenset({"alice"}))
        outcome = evaluate("tpl-1", "v1", "mallory", decl, _TS_B, EVALUATOR_VERSION)
        assert outcome.evaluation_result is EvaluationResult.INELIGIBLE


# --- Forbidden imports / package boundary (AEMIC-REQ-010-014) ---------------


_FORBIDDEN_IMPORT_ROOTS = (
    "pcae.interactive_workflow",
    "pcae.governance",
    "pcae.cltr",
    "pcae.cltr_prototype",
    "pcae.commands",
    "pcae.cli",
    "pcae.core",
    "pcae.lifecycle",
    "pcae.repository_intelligence",
)


def _imported_modules(path: Path) -> set:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


@pytest.mark.parametrize("path", _package_files(), ids=lambda p: p.name)
def test_authority_evaluation_package_has_no_forbidden_imports(path):
    modules = _imported_modules(path)
    for module in modules:
        for forbidden_root in _FORBIDDEN_IMPORT_ROOTS:
            assert not (module == forbidden_root or module.startswith(forbidden_root + ".")), (
                f"{path.name} imports {module!r}, coupling pcae.authority_evaluation to "
                f"{forbidden_root!r} in violation of AEMIC-REQ-010."
            )


def test_registry_module_has_no_concrete_registry():
    import pcae.authority_evaluation.registry as registry_module
    import inspect

    classes = [
        obj
        for _, obj in inspect.getmembers(registry_module, inspect.isclass)
        if obj.__module__ == registry_module.__name__
    ]
    assert classes == [registry_module.AuthorityRegistry]


def test_package_has_exactly_the_required_modules():
    names = {p.name for p in _package_files()}
    assert names == {
        "__init__.py",
        "models.py",
        "evaluation.py",
        "registry.py",
        "errors.py",
        "serialization.py",
    }


def test_public_reexport_surface_is_exact():
    import pcae.authority_evaluation as pkg

    assert set(pkg.__all__) == {
        "EligibleAuthorityDeclaration",
        "AuthorityEvaluationOutcome",
        "EvaluationResult",
        "evaluate",
        "AuthorityRegistry",
        "AuthorityEvaluationError",
        "InvalidClaimedIdentityError",
        "InvalidTemplateReferenceError",
        "MalformedDeclarationError",
        "UnsupportedSchemaVersionError",
        "MissingCitationTextError",
        "TemplateIdentityMismatchError",
        "AuthorityRegistryUnavailableError",
        "AuthorityRegistryCorruptError",
    }


def test_evaluation_module_has_no_registry_import():
    path = Path(__file__).resolve().parents[1] / "src" / "pcae" / "authority_evaluation" / "evaluation.py"
    modules = _imported_modules(path)
    assert "pcae.authority_evaluation.registry" not in modules


def test_no_bare_exception_types_collapse_named_errors():
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "pcae"
        / "authority_evaluation"
        / "errors.py"
    )
    tree = ast.parse(path.read_text(), filename=str(path))
    class_defs = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    names = {node.name for node in class_defs}
    expected = {
        "AuthorityEvaluationError",
        "InvalidClaimedIdentityError",
        "InvalidTemplateReferenceError",
        "MalformedDeclarationError",
        "UnsupportedSchemaVersionError",
        "MissingCitationTextError",
        "TemplateIdentityMismatchError",
        "AuthorityRegistryUnavailableError",
        "AuthorityRegistryCorruptError",
    }
    assert names == expected


# --- Exception hierarchy -----------------------------------------------


class TestExceptionHierarchy:
    @pytest.mark.parametrize(
        "exc_type",
        [
            InvalidClaimedIdentityError,
            InvalidTemplateReferenceError,
            MalformedDeclarationError,
            UnsupportedSchemaVersionError,
            MissingCitationTextError,
            TemplateIdentityMismatchError,
            AuthorityRegistryUnavailableError,
            AuthorityRegistryCorruptError,
        ],
    )
    def test_direct_subclass_of_base(self, exc_type):
        assert issubclass(exc_type, AuthorityEvaluationError)
        assert exc_type.__bases__ == (AuthorityEvaluationError,)

    def test_registry_exceptions_never_raised_by_evaluate(self):
        # evaluate() never touches a Registry (AEMIC-REQ-073/077); its
        # exception boundary is exactly the six §13.1 exceptions plus the
        # base-class fallback -- never AuthorityRegistryUnavailableError
        # or AuthorityRegistryCorruptError.
        decl = _declaration()
        try:
            evaluate("", "", "", decl, _TS_B, EVALUATOR_VERSION)
        except (AuthorityRegistryUnavailableError, AuthorityRegistryCorruptError):
            pytest.fail("evaluate() must never raise a Registry-layer exception")
        except AuthorityEvaluationError:
            pass
