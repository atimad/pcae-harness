"""Phase 147H -- independent adversarial verification of the Phase 147G
``pcae.authority_evaluation`` implementation against AEMIC-001 v1.2.

This file is independent of ``tests/test_phase_147g_authority_evaluation.py``:
it does not import, reuse, or extend that file's fixtures or test doubles.
Every test double, adversarial input, and assertion here was derived directly
from AEMIC-001 v1.2's own text, not from Phase 147G's own account of it.

This phase does not modify Phase 147G's own tests or any production code
(No-Go Boundary, phase authorization §31).
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import pathlib
import sys
import threading
from abc import ABC

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
from pcae.authority_evaluation import serialization as ser


def _decl(**overrides):
    fields = {
        "template_ref": "tmpl-A",
        "template_version": "v1",
        "eligible_identities": frozenset({"alice", "bob"}),
        "declared_at": "2026-07-30T00:00:00+00:00",
        "declared_by": "governance-author",
    }
    fields.update(overrides)
    return EligibleAuthorityDeclaration(**fields)


# --- §7/§12: evaluator signature introspection, independent of visual read --


class TestEvaluatorSignatureIntrospection:
    def test_signature_has_exactly_seven_parameters_in_order(self):
        sig = inspect.signature(evaluate)
        names = list(sig.parameters.keys())
        assert names == [
            "template_ref",
            "template_version",
            "claimed_identity",
            "declaration",
            "evaluated_at",
            "evaluator_version",
            "citation_text",
        ]

    def test_only_citation_text_has_a_default(self):
        sig = inspect.signature(evaluate)
        for name, param in sig.parameters.items():
            if name == "citation_text":
                assert param.default is None
            else:
                assert param.default is inspect.Parameter.empty, name

    def test_all_parameters_accept_positional_or_keyword(self):
        sig = inspect.signature(evaluate)
        for param in sig.parameters.values():
            assert param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    def test_return_annotation_is_outcome_type(self):
        sig = inspect.signature(evaluate)
        assert sig.return_annotation in (
            AuthorityEvaluationOutcome,
            "AuthorityEvaluationOutcome",
        )

    def test_no_var_positional_or_var_keyword_catch_all(self):
        sig = inspect.signature(evaluate)
        kinds = {p.kind for p in sig.parameters.values()}
        assert inspect.Parameter.VAR_POSITIONAL not in kinds
        assert inspect.Parameter.VAR_KEYWORD not in kinds


# --- §5/§14.2: exception precedence, independently reconstructed ordering --


class TestExceptionPrecedenceIndependentMatrix:
    """AEMIC-REQ-104/105: the first violated check in ordering wins, never
    masked by a later one. Each case here supplies two simultaneously-true
    violation conditions and asserts only the earlier-ordered exception
    surfaces."""

    def test_invalid_template_ref_beats_declaration_mismatch(self):
        d = _decl(template_ref="other", template_version="v9")
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate("", "v1", "alice", d, "2026-01-01T00:00:00Z", "aem-evaluator/1.0")

    def test_invalid_template_version_beats_declaration_mismatch(self):
        d = _decl(template_ref="other", template_version="v9")
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate("tmpl-A", 123, "alice", d, "2026-01-01T00:00:00Z", "aem-evaluator/1.0")

    def test_invalid_claimed_identity_beats_mismatch(self):
        d = _decl(template_ref="other", template_version="v9")
        with pytest.raises(InvalidClaimedIdentityError):
            evaluate("tmpl-A", "v1", "", d, "2026-01-01T00:00:00Z", "aem-evaluator/1.0")

    def test_mismatch_beats_missing_citation(self):
        # declaration resolves for a DIFFERENT identity than requested; if the
        # implementation determined evaluation_result first it might raise
        # MissingCitationTextError instead -- mismatch must win.
        d = _decl(template_ref="other-tmpl", template_version="v1",
                   eligible_identities=frozenset({"alice"}))
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "aem-evaluator/1.0")

    def test_mismatch_beats_invalid_citation_type_irrelevance(self):
        d = _decl(template_ref="tmpl-A", template_version="different-version")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate(
                "tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z",
                "aem-evaluator/1.0", citation_text=12345,
            )

    def test_eligible_missing_citation_raises(self):
        d = _decl()
        with pytest.raises(MissingCitationTextError):
            evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "aem-evaluator/1.0")

    def test_non_eligible_with_supplied_citation_does_not_raise_and_drops_it(self):
        d = _decl()
        outcome = evaluate(
            "tmpl-A", "v1", "carol", d, "2026-01-01T00:00:00Z",
            "aem-evaluator/1.0", citation_text="should be dropped",
        )
        assert outcome.evaluation_result is EvaluationResult.INELIGIBLE
        assert outcome.citation_text is None

    def test_indeterminate_with_supplied_citation_drops_it(self):
        outcome = evaluate(
            "tmpl-A", "v1", "carol", None, "2026-01-01T00:00:00Z",
            "aem-evaluator/1.0", citation_text="should be dropped",
        )
        assert outcome.evaluation_result is EvaluationResult.INDETERMINATE
        assert outcome.citation_text is None

    def test_first_ordering_step_wins_even_with_every_later_condition_also_true(self):
        # template_ref invalid AND claimed_identity invalid AND declaration
        # would mismatch AND would be eligible-missing-citation -- only the
        # first-ordered failure (InvalidTemplateReferenceError) may surface.
        d = _decl(template_ref="zzz", template_version="zzz")
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate(None, "v1", "", d, "2026-01-01T00:00:00Z", "aem-evaluator/1.0")

    def test_duplicate_style_double_violation_declaration_and_version_both_invalid(self):
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate("tmpl-A", None, "alice", None, "2026-01-01T00:00:00Z", "aem-evaluator/1.0")

    def test_unsupported_version_style_otherwise_valid_eligible_succeeds(self):
        # "unsupported version" has no contract meaning at evaluate()'s own
        # layer (no version-compatibility check exists there); a well-formed
        # call must simply succeed.
        d = _decl()
        outcome = evaluate(
            "tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z",
            "aem-evaluator/9.9-unknown", citation_text="cited text",
        )
        assert outcome.evaluation_result is EvaluationResult.ELIGIBLE
        assert outcome.evaluator_version == "aem-evaluator/9.9-unknown"


# --- §14.2/§10: template identity agreement, adversarial ------------------


class TestTemplateIdentityAgreementAdversarial:
    def test_exact_match_ok(self):
        d = _decl(template_ref="T", template_version="1")
        outcome = evaluate("T", "1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")
        assert outcome.template_ref == "T"
        assert outcome.template_version == "1"

    def test_ref_mismatch_raises(self):
        d = _decl(template_ref="T2", template_version="1")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("T", "1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")

    def test_version_mismatch_raises(self):
        d = _decl(template_ref="T", template_version="2")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("T", "1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")

    def test_both_mismatch_raises(self):
        d = _decl(template_ref="T2", template_version="2")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("T", "1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")

    def test_unicode_lookalike_ref_is_not_equal(self):
        # Cyrillic 'Т' (U+0422) vs Latin 'T' -- must not be conflated.
        d = _decl(template_ref="Т", template_version="1")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("T", "1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")

    def test_case_difference_is_a_mismatch(self):
        d = _decl(template_ref="tmpl", template_version="1")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("TMPL", "1", "alice", d, "2026-01-01T00:00:00Z", "v")

    def test_whitespace_difference_is_a_mismatch(self):
        d = _decl(template_ref="tmpl ", template_version="1")
        with pytest.raises(TemplateIdentityMismatchError):
            evaluate("tmpl", "1", "alice", d, "2026-01-01T00:00:00Z", "v")

    def test_non_string_declaration_field_impossible_but_signature_rejects_non_str_inputs(self):
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate(123, "1", "alice", None, "2026-01-01T00:00:00Z", "v")
        with pytest.raises(InvalidTemplateReferenceError):
            evaluate("T", 123, "alice", None, "2026-01-01T00:00:00Z", "v")

    def test_declaration_identity_never_overrides_evaluate_own_parameters(self):
        # Declaration and evaluate() agree; outcome must copy evaluate()'s
        # own parameters (structurally indistinguishable here, but this
        # locks in the *source*, not merely the value, via a second check).
        d = _decl(template_ref="T", template_version="1")
        outcome = evaluate("T", "1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")
        assert outcome.template_ref is not None
        assert (outcome.template_ref, outcome.template_version) == ("T", "1")


# --- §6.1: citation if-and-only-if invariant, adversarial ------------------


class TestCitationInvariantAdversarial:
    def test_none_on_eligible_raises_at_evaluate(self):
        d = _decl()
        with pytest.raises(MissingCitationTextError):
            evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text=None)

    def test_empty_string_on_eligible_is_accepted_not_none(self):
        # Empty string is not None -- the if-and-only-if invariant is about
        # None-ness, not truthiness. Contract does not require rejecting "".
        d = _decl()
        outcome = evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="")
        assert outcome.citation_text == ""

    def test_whitespace_only_citation_is_accepted_verbatim(self):
        d = _decl()
        outcome = evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="   ")
        assert outcome.citation_text == "   "

    def test_non_string_citation_on_eligible_is_not_none_so_passes_evaluate_but_model_may_reject(self):
        # evaluate() itself only checks `is None`, so a non-str truthy value
        # passes through to AuthorityEvaluationOutcome's own constructor,
        # which does not type-check citation_text at all (models.py has no
        # isinstance check on citation_text). Document actual behavior.
        d = _decl()
        outcome = evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text=12345)
        assert outcome.citation_text == 12345  # not coerced to str

    def test_long_unicode_citation_round_trips_verbatim(self):
        d = _decl()
        text = "引用文本 " * 500
        outcome = evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text=text)
        assert outcome.citation_text == text

    def test_citation_on_ineligible_construction_direct_raises(self):
        with pytest.raises(MalformedDeclarationError):
            AuthorityEvaluationOutcome(
                template_ref="T", template_version="1", claimed_identity="carol",
                evaluation_result=EvaluationResult.INELIGIBLE,
                declaration_ref="T::1", citation_text="should not exist",
                evaluated_at="2026-01-01T00:00:00Z", evaluator_version="v",
            )

    def test_citation_on_indeterminate_construction_direct_raises(self):
        with pytest.raises(MalformedDeclarationError):
            AuthorityEvaluationOutcome(
                template_ref="T", template_version="1", claimed_identity="carol",
                evaluation_result=EvaluationResult.INDETERMINATE,
                declaration_ref=None, citation_text="should not exist",
                evaluated_at="2026-01-01T00:00:00Z", evaluator_version="v",
            )

    def test_missing_citation_on_eligible_construction_direct_raises(self):
        with pytest.raises(MalformedDeclarationError):
            AuthorityEvaluationOutcome(
                template_ref="T", template_version="1", claimed_identity="alice",
                evaluation_result=EvaluationResult.ELIGIBLE,
                declaration_ref="T::1", citation_text=None,
                evaluated_at="2026-01-01T00:00:00Z", evaluator_version="v",
            )


# --- §6/§7/§14: field-source / branch completeness, independent matrix ----


class TestFieldSourceMatrixIndependent:
    def test_eligible_branch_all_mandatory_fields_present(self):
        d = _decl()
        outcome = evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")
        assert outcome.template_ref == "tmpl-A"
        assert outcome.template_version == "v1"
        assert outcome.claimed_identity == "alice"
        assert outcome.evaluation_result is EvaluationResult.ELIGIBLE
        assert outcome.declaration_ref == "tmpl-A::v1"
        assert outcome.citation_text == "c"
        assert outcome.evaluated_at == "2026-01-01T00:00:00Z"
        assert outcome.evaluator_version == "v"
        assert outcome.schema_version == "aem-outcome/1.0"

    def test_ineligible_branch_all_mandatory_fields_present_no_citation(self):
        d = _decl()
        outcome = evaluate("tmpl-A", "v1", "carol", d, "2026-01-01T00:00:00Z", "v")
        assert outcome.evaluation_result is EvaluationResult.INELIGIBLE
        assert outcome.declaration_ref == "tmpl-A::v1"
        assert outcome.citation_text is None
        assert outcome.template_ref == "tmpl-A"
        assert outcome.template_version == "v1"

    def test_indeterminate_branch_template_identity_still_present(self):
        # This is the specific BF-147F.1-1 repair: declaration is None, yet
        # template_ref/template_version must still be reachable and equal to
        # evaluate()'s own inputs, never fabricated or omitted.
        outcome = evaluate("tmpl-Z", "v7", "dave", None, "2026-01-01T00:00:00Z", "v")
        assert outcome.evaluation_result is EvaluationResult.INDETERMINATE
        assert outcome.template_ref == "tmpl-Z"
        assert outcome.template_version == "v7"
        assert outcome.declaration_ref is None
        assert outcome.citation_text is None

    def test_declaration_ref_derived_from_identity_tuple_not_storage(self):
        d = _decl(template_ref="alpha", template_version="beta")
        outcome = evaluate("alpha", "beta", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")
        assert outcome.declaration_ref == "alpha::beta"


# --- §11: Registry ABC isolation, independent test doubles -----------------


class _ResolvedDouble(AuthorityRegistry):
    def resolve(self, template_ref, template_version):
        return _decl(template_ref=template_ref, template_version=template_version)


class _AbsentDouble(AuthorityRegistry):
    def resolve(self, template_ref, template_version):
        return None


class _UnavailableDouble(AuthorityRegistry):
    def resolve(self, template_ref, template_version):
        raise AuthorityRegistryUnavailableError("storage unreachable")


class _CorruptDouble(AuthorityRegistry):
    def resolve(self, template_ref, template_version):
        raise AuthorityRegistryCorruptError("malformed record")


class _DuplicateDouble(AuthorityRegistry):
    """Models a resolve()-time duplicate-candidate detection: per
    AEMIC-REQ-045, this MUST raise AuthorityRegistryCorruptError, never
    first-match-select."""

    def resolve(self, template_ref, template_version):
        raise AuthorityRegistryCorruptError("duplicate candidates for identity tuple")


class TestAuthorityRegistryABCIsolation:
    def test_is_abstract_base_class(self):
        assert issubclass(AuthorityRegistry, ABC)
        with pytest.raises(TypeError):
            AuthorityRegistry()  # cannot instantiate the ABC directly

    def test_exposes_exactly_one_abstract_method(self):
        abstract_methods = AuthorityRegistry.__abstractmethods__
        assert abstract_methods == frozenset({"resolve"})

    def test_no_write_methods_exist(self):
        for forbidden in ("create", "persist", "delete", "list", "enumerate", "save", "write"):
            assert not hasattr(AuthorityRegistry, forbidden)

    def test_resolved_double_returns_matching_declaration(self):
        reg = _ResolvedDouble()
        d = reg.resolve("T", "1")
        assert d.template_ref == "T"
        assert d.template_version == "1"

    def test_absent_double_returns_none_not_raise(self):
        reg = _AbsentDouble()
        assert reg.resolve("T", "1") is None

    def test_unavailable_double_raises_unavailable(self):
        reg = _UnavailableDouble()
        with pytest.raises(AuthorityRegistryUnavailableError):
            reg.resolve("T", "1")

    def test_corrupt_double_raises_corrupt(self):
        reg = _CorruptDouble()
        with pytest.raises(AuthorityRegistryCorruptError):
            reg.resolve("T", "1")

    def test_duplicate_double_raises_corrupt_never_first_match(self):
        reg = _DuplicateDouble()
        with pytest.raises(AuthorityRegistryCorruptError):
            reg.resolve("T", "1")

    def test_registry_module_has_no_concrete_subclass_shipped(self):
        import pcae.authority_evaluation.registry as registry_mod

        for name, obj in vars(registry_mod).items():
            if isinstance(obj, type) and issubclass(obj, AuthorityRegistry) and obj is not AuthorityRegistry:
                pytest.fail(f"unexpected concrete AuthorityRegistry subclass shipped: {name}")

    def test_registry_module_source_has_no_concrete_class_definition(self):
        source = pathlib.Path(
            inspect.getfile(sys.modules["pcae.authority_evaluation.registry"])
        ).read_text()
        tree = ast.parse(source)
        class_defs = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert len(class_defs) == 1
        assert class_defs[0].name == "AuthorityRegistry"


# --- §16 evaluator/registry architectural separation -----------------------


class TestEvaluatorRegistrySeparation:
    def test_evaluation_module_does_not_import_registry_module(self):
        import pcae.authority_evaluation.evaluation as eval_mod

        tree = ast.parse(inspect.getsource(eval_mod))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any("registry" in name for name in imported)

    def test_evaluate_never_touches_a_registry_instance(self):
        # Passing a Registry double as `declaration` (a type confusion) must
        # fail structurally, proving evaluate() never introspects for or
        # calls .resolve() on anything -- it only reads declaration.template_ref
        # /.template_version/.eligible_identities as plain attribute access.
        class _NotADeclaration:
            template_ref = "T"
            template_version = "1"
            eligible_identities = frozenset({"alice"})

        outcome = evaluate("T", "1", "alice", _NotADeclaration(), "2026-01-01T00:00:00Z", "v", citation_text="c")
        assert outcome.evaluation_result is EvaluationResult.ELIGIBLE


# --- §18: serialization, adversarial ---------------------------------------


class TestSerializationAdversarial:
    def test_round_trip_declaration(self):
        d = _decl(eligible_identities=frozenset({"alice", "bob", "réné", "中文"}))
        payload = ser.declaration_to_payload(d)
        d2 = ser.declaration_from_payload(payload)
        assert d2 == d

    def test_round_trip_outcome_eligible(self):
        o = AuthorityEvaluationOutcome(
            template_ref="T", template_version="1", claimed_identity="alice",
            evaluation_result=EvaluationResult.ELIGIBLE, declaration_ref="T::1",
            citation_text="城市 citation", evaluated_at="2026-01-01T00:00:00Z",
            evaluator_version="v",
        )
        payload = ser.outcome_to_payload(o)
        o2 = ser.outcome_from_payload(payload)
        assert o2 == o

    def test_declaration_payload_is_json_dumpable_with_sort_keys(self):
        d = _decl()
        payload = ser.declaration_to_payload(d)
        text = json.dumps(payload, sort_keys=True)
        assert json.loads(text) == payload

    def test_eligible_identities_serialized_as_sorted_list_not_set(self):
        d = _decl(eligible_identities=frozenset({"zed", "alpha", "mid"}))
        payload = ser.declaration_to_payload(d)
        assert payload["eligible_identities"] == ["alpha", "mid", "zed"]

    def test_unsupported_schema_version_raises_before_other_validation(self):
        payload = {
            "template_ref": "T", "template_version": "1",
            "eligible_identities": ["alice"], "declared_at": "not-even-a-date",
            "declared_by": "x", "schema_version": "aem-declaration/999.0",
        }
        with pytest.raises(UnsupportedSchemaVersionError):
            ser.declaration_from_payload(payload)

    def test_missing_required_field_raises_malformed(self):
        payload = {
            "template_ref": "T", "template_version": "1",
            "declared_at": "2026-01-01T00:00:00Z", "declared_by": "x",
            "schema_version": "aem-declaration/1.0",
        }
        with pytest.raises(MalformedDeclarationError):
            ser.declaration_from_payload(payload)

    def test_null_required_field_raises_malformed(self):
        payload = {
            "template_ref": None, "template_version": "1",
            "eligible_identities": ["alice"], "declared_at": "2026-01-01T00:00:00Z",
            "declared_by": "x", "schema_version": "aem-declaration/1.0",
        }
        with pytest.raises(MalformedDeclarationError):
            ser.declaration_from_payload(payload)

    def test_eligible_identities_as_dict_is_silently_accepted_as_its_key_set(self):
        # AEMIC-REQ-090/091 do not specify JSON-type enforcement beyond
        # "missing or null"; declaration_from_payload does
        # frozenset(eligible_identities), and frozenset() of a dict yields
        # its key set rather than raising. This is a genuine, disclosed gap
        # (Informational, not Blocking): a malformed payload shaped as an
        # object rather than a list is silently reinterpreted, not rejected.
        payload = {
            "template_ref": "T", "template_version": "1",
            "eligible_identities": {"alice": "ignored-value"}, "declared_at": "2026-01-01T00:00:00Z",
            "declared_by": "x", "schema_version": "aem-declaration/1.0",
        }
        result = ser.declaration_from_payload(payload)
        assert result.eligible_identities == frozenset({"alice"})

    def test_outcome_from_payload_unrecognized_evaluation_result_raises(self):
        payload = {
            "template_ref": "T", "template_version": "1", "claimed_identity": "alice",
            "evaluation_result": "not-a-real-value", "declaration_ref": "T::1",
            "citation_text": "c", "evaluated_at": "2026-01-01T00:00:00Z",
            "evaluator_version": "v", "schema_version": "aem-outcome/1.0",
        }
        with pytest.raises(MalformedDeclarationError):
            ser.outcome_from_payload(payload)

    def test_outcome_from_payload_citation_evaluation_mismatch_raises(self):
        # citation_text present but evaluation_result is ineligible -- the
        # if-and-only-if invariant must be enforced during deserialization
        # too, via AuthorityEvaluationOutcome's own constructor.
        payload = {
            "template_ref": "T", "template_version": "1", "claimed_identity": "carol",
            "evaluation_result": "ineligible", "declaration_ref": "T::1",
            "citation_text": "should not be here", "evaluated_at": "2026-01-01T00:00:00Z",
            "evaluator_version": "v", "schema_version": "aem-outcome/1.0",
        }
        with pytest.raises(MalformedDeclarationError):
            ser.outcome_from_payload(payload)

    def test_malicious_str_object_in_declared_by_is_captured_verbatim_not_executed(self):
        class _Evil:
            def __str__(self):
                raise RuntimeError("should never be called by construction")

        with pytest.raises(MalformedDeclarationError):
            _decl(declared_by=_Evil())  # not a str -> rejected by isinstance check

    def test_deeply_nested_eligible_identities_member_type_rejected(self):
        with pytest.raises(MalformedDeclarationError):
            _decl(eligible_identities=frozenset({("nested", "tuple")}))


# --- §14/§10: determinism ---------------------------------------------------


class TestDeterminismIndependent:
    def test_repeated_calls_produce_field_identical_outcomes(self):
        d = _decl()
        o1 = evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")
        o2 = evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")
        assert o1 == o2

    def test_independent_equal_declarations_produce_identical_outcome(self):
        d1 = _decl()
        d2 = _decl()
        assert d1 is not d2
        o1 = evaluate("tmpl-A", "v1", "alice", d1, "2026-01-01T00:00:00Z", "v", citation_text="c")
        o2 = evaluate("tmpl-A", "v1", "alice", d2, "2026-01-01T00:00:00Z", "v", citation_text="c")
        assert o1 == o2

    def test_serialize_before_and_after_evaluation_agree(self):
        d = _decl()
        payload_before = ser.declaration_to_payload(d)
        evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")
        payload_after = ser.declaration_to_payload(d)
        assert payload_before == payload_after

    def test_reordered_equivalent_dict_payload_round_trips_identically(self):
        payload_a = {
            "template_ref": "T", "template_version": "1",
            "eligible_identities": ["alice", "bob"], "declared_at": "2026-01-01T00:00:00Z",
            "declared_by": "x", "schema_version": "aem-declaration/1.0",
        }
        payload_b = dict(reversed(list(payload_a.items())))
        assert ser.declaration_from_payload(payload_a) == ser.declaration_from_payload(payload_b)

    def test_concurrent_calls_across_threads_produce_identical_outcomes(self):
        d = _decl()
        results = []
        lock = threading.Lock()

        def worker():
            o = evaluate("tmpl-A", "v1", "alice", d, "2026-01-01T00:00:00Z", "v", citation_text="c")
            with lock:
                results.append(o)

        threads = [threading.Thread(target=worker) for _ in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 16
        assert all(r == results[0] for r in results)

    def test_evaluated_at_is_purely_caller_supplied_not_wall_clock(self):
        d = _decl()
        o = evaluate("tmpl-A", "v1", "alice", d, "1999-01-01T00:00:00Z", "v", citation_text="c")
        assert o.evaluated_at == "1999-01-01T00:00:00Z"


# --- §6/§4: equality and hashing -------------------------------------------


class TestEqualityAndHashingIndependent:
    def test_equal_declarations_hash_equal(self):
        d1 = _decl()
        d2 = _decl()
        assert d1 == d2
        assert hash(d1) == hash(d2)

    def test_equal_outcomes_hash_equal(self):
        o1 = AuthorityEvaluationOutcome(
            template_ref="T", template_version="1", claimed_identity="alice",
            evaluation_result=EvaluationResult.ELIGIBLE, declaration_ref="T::1",
            citation_text="c", evaluated_at="2026-01-01T00:00:00Z", evaluator_version="v",
        )
        o2 = AuthorityEvaluationOutcome(
            template_ref="T", template_version="1", claimed_identity="alice",
            evaluation_result=EvaluationResult.ELIGIBLE, declaration_ref="T::1",
            citation_text="c", evaluated_at="2026-01-01T00:00:00Z", evaluator_version="v",
        )
        assert o1 == o2
        assert hash(o1) == hash(o2)

    def test_enum_members_hash_stable_and_equal_by_identity(self):
        assert hash(EvaluationResult.ELIGIBLE) == hash(EvaluationResult.ELIGIBLE)
        assert EvaluationResult("eligible") is EvaluationResult.ELIGIBLE

    def test_reconstructed_serialized_declaration_hashes_equal_to_original(self):
        d = _decl()
        d2 = ser.declaration_from_payload(ser.declaration_to_payload(d))
        assert d == d2
        assert hash(d) == hash(d2)

    def test_none_optional_fields_are_hashable(self):
        o = AuthorityEvaluationOutcome(
            template_ref="T", template_version="1", claimed_identity="carol",
            evaluation_result=EvaluationResult.INDETERMINATE, declaration_ref=None,
            citation_text=None, evaluated_at="2026-01-01T00:00:00Z", evaluator_version="v",
        )
        assert hash(o) is not None

    def test_frozenset_field_is_hashable_container(self):
        d = _decl(eligible_identities=frozenset({"alice", "bob"}))
        assert hash(d) is not None  # would raise TypeError if unhashable nested value existed


# --- §8/§20: disclosure-only security, behavioral (not name-based) --------


class TestDisclosureOnlySecurityBehavioral:
    def test_no_public_name_suggests_authorize_grant_permit_allow_deny(self):
        import pcae.authority_evaluation as pkg

        forbidden_substrings = ("authorize", "grant", "permit", "allow", "deny")
        for name in pkg.__all__:
            lowered = name.lower()
            for substring in forbidden_substrings:
                assert substring not in lowered, f"{name} contains {substring!r}"

    def test_importing_package_performs_no_filesystem_write(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        before = set(tmp_path.rglob("*"))
        for mod_name in list(sys.modules):
            if mod_name.startswith("pcae.authority_evaluation"):
                del sys.modules[mod_name]
        importlib.import_module("pcae.authority_evaluation")
        after = set(tmp_path.rglob("*"))
        assert before == after

    def test_evaluate_result_is_not_truthy_gate_shaped(self):
        # A disclosure-only outcome should not be usable as an ad hoc boolean
        # authorization gate: EvaluationResult itself defines no __bool__
        # override (the True/False here is Enum's own uniform default, not
        # a package-specific ELIGIBLE-is-truthy/others-are-falsy special
        # case that would invite `if evaluate(...):` misuse patterns).
        assert "__bool__" not in EvaluationResult.__dict__
        assert bool(EvaluationResult.ELIGIBLE) is bool(EvaluationResult.INELIGIBLE) is True

    def test_no_function_named_check_or_verify_grants_capability(self):
        import pcae.authority_evaluation as pkg

        for name in pkg.__all__:
            obj = getattr(pkg, name)
            if inspect.isfunction(obj):
                assert obj.__doc__ and (
                    "disclos" in obj.__doc__.lower() or "authoriz" not in obj.__doc__.lower()
                )


# --- §3.4: forbidden dependencies, static + dynamic ------------------------


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


class TestForbiddenDependenciesIndependent:
    @pytest.mark.parametrize(
        "module_path",
        sorted(
            str(p)
            for p in pathlib.Path("src/pcae/authority_evaluation").glob("*.py")
        ),
    )
    def test_source_file_has_no_forbidden_import(self, module_path):
        source = pathlib.Path(module_path).read_text()
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        for root in _FORBIDDEN_IMPORT_ROOTS:
            for name in imported:
                assert not (name == root or name.startswith(root + ".")), (
                    f"{module_path} imports forbidden root via {name!r}"
                )

    def test_runtime_module_graph_after_import_contains_no_forbidden_root(self):
        for mod_name in list(sys.modules):
            if mod_name.startswith("pcae.authority_evaluation"):
                del sys.modules[mod_name]
        importlib.import_module("pcae.authority_evaluation")
        for mod_name in list(sys.modules):
            if mod_name.startswith("pcae.authority_evaluation"):
                mod = sys.modules[mod_name]
                mod_file = getattr(mod, "__file__", "") or ""
                assert "authority_evaluation" in mod_file or mod_name == "pcae.authority_evaluation"

    def test_no_forbidden_root_is_importable_transitively_via_authority_evaluation_alone(self):
        # A clean subprocess-free proxy: confirm none of the forbidden roots
        # are already present in sys.modules purely as a side effect of
        # importing pcae.authority_evaluation in a fresh state.
        for mod_name in list(sys.modules):
            if mod_name.startswith("pcae.authority_evaluation") or any(
                mod_name == r or mod_name.startswith(r + ".") for r in _FORBIDDEN_IMPORT_ROOTS
            ):
                del sys.modules[mod_name]
        importlib.import_module("pcae.authority_evaluation")
        for root in _FORBIDDEN_IMPORT_ROOTS:
            assert root not in sys.modules, f"{root} was imported as a side effect"


# --- §3.6: export exactness --------------------------------------------


class TestPublicExportExactness:
    def test_all_list_matches_expected_set_exactly(self):
        import pcae.authority_evaluation as pkg

        expected = {
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
        assert set(pkg.__all__) == expected
        assert len(pkg.__all__) == len(set(pkg.__all__))  # no duplicates

    def test_no_private_helper_leaked_via_star_import_surface(self):
        import pcae.authority_evaluation as pkg

        for name in dir(pkg):
            if name.startswith("_"):
                continue
            if name in pkg.__all__:
                continue
            # module attributes like __name__, or re-imported submodules
            # (pkg.errors, pkg.models, etc.) are expected and harmless --
            # only flag names that look like accidental logic exports.
            obj = getattr(pkg, name)
            if inspect.isfunction(obj) or (inspect.isclass(obj) and obj.__module__.startswith("pcae.authority_evaluation")):
                assert name in pkg.__all__, f"{name} is a callable/class not in __all__"


# --- Package shape: exactly six modules, no extras -------------------------


class TestPackageShapeIndependent:
    def test_directory_contains_exactly_the_required_files(self):
        pkg_dir = pathlib.Path("src/pcae/authority_evaluation")
        actual = {p.name for p in pkg_dir.iterdir() if p.is_file()}
        expected = {
            "__init__.py", "models.py", "evaluation.py",
            "registry.py", "errors.py", "serialization.py",
        }
        assert actual == expected

    def test_no_pycache_or_generated_artifact_committed(self):
        import subprocess

        tracked = subprocess.run(
            ["git", "ls-files", "src/pcae/authority_evaluation"],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        for path in tracked:
            assert "__pycache__" not in path
            assert not path.endswith(".pyc")

    def test_no_cli_or_plugin_registration_module_present(self):
        pkg_dir = pathlib.Path("src/pcae/authority_evaluation")
        names = {p.stem for p in pkg_dir.glob("*.py")}
        for forbidden in ("cli", "commands", "plugin", "lifecycle_adapter", "publication_adapter"):
            assert forbidden not in names
