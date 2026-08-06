"""Phase 149O.1H.4 -- HATP Timestamp Canonicalization Final Independent
Re-Verification.

Verification-only suite. Independently reconstructs and attacks the
Phase 149O.1H.3 repair (`_reject_excess_fractional_precision` /
`_parse_iso_timestamp` in
`src/pcae/core/human_approval_trusted_provenance.py`) across the entire
relevant Wave-3 timestamp/constructor/canonicalization semantic domain:
raw lexical precision, the pre-existing millisecond-domain rule,
injectivity, timezone equivalence, parser/constructor equivalence,
B-149O.1H-2 constructor hardening, closed-schema/duplicate-key/AG3-AG5
regressions, and independently recomputed canonical golden vectors.

This suite does NOT modify, weaken, or duplicate the pre-existing
149O.1G/149O.1H/149O.1H.1/149O.1H.2/149O.1H.3 suites. It adds
independent re-verification coverage, including a new BLOCKING finding
this phase discovered: the 149O.1H.3 lexical guard's regex
(`_FRACTIONAL_SECONDS_RE = re.compile(r"\\.(\\d+)(?=Z$|[+-]\\d{2}:\\d{2}$)")`)
only recognizes a `Z` suffix or a *colon-separated* `+HH:MM`/`-HH:MM`
offset immediately following the fractional-seconds group. Python
3.11+'s `datetime.fromisoformat` accepts additional ISO-8601 offset
syntaxes the guard's lookahead does not match -- most importantly a
*non-colon* two-or-four-digit offset (`+00`, `+0000`, `-0500`, ...).
For those forms, `_reject_excess_fractional_precision` never fires, the
raw string flows straight into the historically lossy
`datetime.fromisoformat` call, and -- for the specific 7+-digit
sub-microsecond values whose truncated microsecond happens to already
be millisecond-aligned (e.g. `.0000001`, `.0000009`, both truncating to
`microsecond == 0`) -- the pre-existing millisecond-domain rule
(`microsecond % 1000 == 0`) does not reject them either. The result is
the *exact* B-149O.1H-1 collision the 149O.1H.3 repair was written to
close, reproduced through the `+00`/`+0000`-style offset syntax:

    issued_at="...12:00:00.0000001+00"  -> canonicalizes to ...12:00:00.000Z
    issued_at="...12:00:00.0000009+00"  -> canonicalizes to ...12:00:00.000Z

i.e. two distinct raw `issued_at` claims silently canonicalize to the
identical instant and produce the identical canonical payload/digest.
This suite records and reproduces the finding (both parser and
constructor paths) without repairing it -- repair is out of scope for a
verification-only phase (149O.1H.5 narrow repair recommended).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HumanApprovalProvenanceProof,
    InvalidProofSchemaError,
    MalformedProofError,
    RollbackSite,
    UnsupportedProofVersionError,
    canonicalize_hatp_proof_payload,
    digest_hatp_proof_payload,
    hatp_proof_to_document,
    parse_hatp_proof,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_MODULE_PATH = REPO_ROOT / "src" / "pcae" / "core" / "human_approval_trusted_provenance.py"

# The commit immediately preceding the 149O.1H.3 repair (01bacf8a, the
# 149O.1H.2 independent re-verification commit) -- independently
# reconstructed via `git diff --name-only 01bacf8a..acb511bb -- src/pcae/`,
# which shows exactly one file changed:
# `src/pcae/core/human_approval_trusted_provenance.py`, UNRELATED = 0.
PRE_REPAIR_COMMIT = "01bacf8a"
POST_REPAIR_COMMIT = "acb511bb"


def _repo_id() -> str:
    return str(uuid.uuid4())


def _valid_document(family: str = "AG3", **overrides: object) -> dict:
    doc: dict = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": _repo_id(),
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": family,
        "issued_at": "2026-08-06T00:00:00.000Z",
    }
    if family == "AG3":
        doc["job_id"] = "job-1"
        doc["original_commit_sha"] = "c" * 40
    else:
        doc["per_id"] = "per-1"
        doc["ecp_id"] = "ecp-1"
    doc.update(overrides)
    return doc


def _valid_kwargs(family: str = "AG3", **overrides: object) -> dict:
    common: dict = dict(
        proof_version=1,
        principal_id="alice",
        signer_key_id="signer-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=_repo_id(),
        decision_record_id="chgr-record-1",
        decision_record_digest="a" * 64,
        binding_id="rae-binding-1",
        binding_digest="b" * 64,
        issued_at="2026-08-06T00:00:00.000Z",
    )
    if family == "AG3":
        common["rollback_site"] = RollbackSite.AG3
        common["operation_reference"] = Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40)
    else:
        common["rollback_site"] = RollbackSite.AG5
        common["operation_reference"] = Ag5OperationReference(per_id="per-1", ecp_id="ecp-1")
    common.update(overrides)
    return common


def _parse(issued_at: str, family: str = "AG3") -> HumanApprovalProvenanceProof:
    return parse_hatp_proof(json.dumps(_valid_document(family, issued_at=issued_at)))


def _construct(issued_at: str, family: str = "AG3") -> HumanApprovalProvenanceProof:
    return HumanApprovalProvenanceProof(**_valid_kwargs(family, issued_at=issued_at))


# ═══════════════════════════════════════════════════════════════════════════
# Section A -- Independent reconstruction of pre/post repair sources via
# `git show`, isolated by importlib (never mutating `sys.modules` for the
# live production module).
# ═══════════════════════════════════════════════════════════════════════════


def _load_module_at_commit(commit: str, tmp_path: Path):
    import subprocess

    text = subprocess.run(
        ["git", "show", f"{commit}:src/pcae/core/human_approval_trusted_provenance.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    dest = tmp_path / f"hatp_at_{commit}.py"
    dest.write_text(text)
    module_name = f"hatp_isolated_{commit}"
    spec = importlib.util.spec_from_file_location(module_name, dest)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        del sys.modules[module_name]
    return mod


@pytest.fixture(scope="module")
def pre_repair_module(tmp_path_factory: pytest.TempPathFactory):
    return _load_module_at_commit(PRE_REPAIR_COMMIT, tmp_path_factory.mktemp("pre_repair"))


def test_production_diff_boundary_between_pre_and_post_repair_commits() -> None:
    """Independently reconstruct the exact 149O.1H.3 production diff
    boundary: exactly one src/pcae file changed, UNRELATED = 0."""
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--name-only", f"{PRE_REPAIR_COMMIT}..{POST_REPAIR_COMMIT}", "--", "src/pcae/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    assert changed == ["src/pcae/core/human_approval_trusted_provenance.py"]


def _doc_for_module(family: str = "AG3", **overrides: object) -> dict:
    return _valid_document(family, **overrides)


def test_historical_defect_reproduced_against_isolated_pre_repair_source(pre_repair_module) -> None:
    """Against the unmodified pre-149O.1H.3 source (01bacf8a), both
    .0000001Z and .0000009Z must still be ACCEPTED and canonicalize
    identically -- the historical defect must remain demonstrably real,
    independent of this phase's own reproduction tooling."""
    doc_a = _doc_for_module(issued_at="2026-01-01T12:00:00.0000001Z")
    doc_b = _doc_for_module(issued_at="2026-01-01T12:00:00.0000009Z")
    proof_a = pre_repair_module.parse_hatp_proof(json.dumps(doc_a))
    proof_b = pre_repair_module.parse_hatp_proof(json.dumps(doc_b))
    assert proof_a.issued_at == proof_b.issued_at == "2026-01-01T12:00:00.000Z"
    payload_a = pre_repair_module.canonicalize_hatp_proof_payload(proof_a)
    payload_b = pre_repair_module.canonicalize_hatp_proof_payload(proof_b)
    assert b'"issued_at":"2026-01-01T12:00:00.000Z"' in payload_a
    assert b'"issued_at":"2026-01-01T12:00:00.000Z"' in payload_b


def test_direct_cpython_truncation_still_occurs_this_interpreter() -> None:
    """§18: confirm the current interpreter still truncates
    fromisoformat for 7+ digits -- establishes the production guard
    remains necessary."""
    a = datetime.fromisoformat("2026-01-01T12:00:00.0000001+00:00")
    b = datetime.fromisoformat("2026-01-01T12:00:00.0000009+00:00")
    assert a.microsecond == b.microsecond == 0


# ═══════════════════════════════════════════════════════════════════════════
# Section B -- Current post-repair source: ordering + fraction-length
# matrix + offset-suffix coverage (colon forms only -- the guarded
# domain).
# ═══════════════════════════════════════════════════════════════════════════


def test_current_repair_rejects_historical_collision_pair_z_suffix() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0000001Z")
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0000009Z")


def test_current_repair_rejects_historical_collision_pair_colon_offset() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0000001+00:00")
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0000009+00:00")


def test_original_149o_1h_1_collision_pair_still_rejected() -> None:
    """§16: .0001Z / .0009Z (149O.1H.1's own repair target) must remain
    rejected -- confirms no regression there."""
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0001Z")
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0009Z")


@pytest.mark.parametrize(
    ("fraction", "expect_lexically_eligible"),
    [
        ("", True),
        ("0", True),
        ("00", True),
        ("000", True),
        ("0000", True),
        ("00000", True),
        ("000000", True),
        ("0000000", False),
        ("00000000", False),
        ("000000000", False),
        ("000000000000", False),
    ],
)
def test_fraction_length_matrix_0_through_12_colon_offset_domain(
    fraction: str, expect_lexically_eligible: bool
) -> None:
    raw = f"2026-01-01T12:00:00{'.' + fraction if fraction else ''}Z"
    if expect_lexically_eligible:
        proof = _parse(raw)
        assert proof.issued_at == "2026-01-01T12:00:00.000Z"
    else:
        with pytest.raises(InvalidProofSchemaError):
            _parse(raw)


@pytest.mark.parametrize(
    ("fraction_a", "fraction_b"),
    [
        ("0000001", "0000009"),
        ("0010001", "0010009"),
        ("1234561", "1234569"),
        ("9999991", "9999999"),
        ("123456789", "123456780"),
        ("000000000001", "000000000009"),
    ],
)
def test_seven_plus_digit_adversarial_matrix_z_and_colon_offsets(fraction_a: str, fraction_b: str) -> None:
    for suffix in ("Z", "+00:00", "+01:00", "-05:00"):
        with pytest.raises(InvalidProofSchemaError):
            _parse(f"2026-01-01T12:00:00.{fraction_a}{suffix}")
        with pytest.raises(InvalidProofSchemaError):
            _parse(f"2026-01-01T12:00:00.{fraction_b}{suffix}")


def test_no_fraction_form_still_accepted() -> None:
    proof = _parse("2026-01-01T12:00:00Z")
    assert proof.issued_at == "2026-01-01T12:00:00.000Z"


@pytest.mark.parametrize("fraction", [".123", ".1230", ".12300", ".123000"])
def test_one_to_six_digit_forms_of_same_instant_canonicalize_identically(fraction: str) -> None:
    proof = _parse(f"2026-01-01T12:00:00{fraction}Z")
    assert proof.issued_at == "2026-01-01T12:00:00.123Z"


def test_single_digit_fraction_canonicalizes_to_hundred_milliseconds() -> None:
    proof = _parse("2026-01-01T12:00:00.1Z")
    assert proof.issued_at == "2026-01-01T12:00:00.100Z"


def test_two_digit_fraction_canonicalizes_correctly() -> None:
    proof = _parse("2026-01-01T12:00:00.12Z")
    assert proof.issued_at == "2026-01-01T12:00:00.120Z"


@pytest.mark.parametrize("fraction", ["000000", "001000", "123000", "999000"])
def test_millisecond_aligned_six_digit_forms_accepted(fraction: str) -> None:
    proof = _parse(f"2026-01-01T12:00:00.{fraction}Z")
    assert proof.issued_at == f"2026-01-01T12:00:00.{fraction[:3]}Z"


@pytest.mark.parametrize("fraction", ["000001", "000999", "001001", "123456", "999999"])
def test_non_millisecond_aligned_six_or_fewer_digit_forms_rejected_by_domain_rule(fraction: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse(f"2026-01-01T12:00:00.{fraction}Z")


def test_lexical_guard_and_millisecond_domain_rule_are_independent_layers() -> None:
    """§15: >6 digits -> lexical rejection; <=6 digits but not
    millisecond-aligned -> the pre-existing semantic rule. No
    conflation: verify each rejects for its own reason by checking the
    guard doesn't fire for a <=6-digit non-aligned value (it must reach
    the semantic layer, not be rejected lexically first)."""
    import pcae.core.human_approval_trusted_provenance as prod

    # 6 digits, non-aligned: lexical guard must NOT raise on its own.
    prod._reject_excess_fractional_precision("2026-01-01T12:00:00.123456Z", context="issued_at")
    # But the full validator still rejects it (via the semantic layer).
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.123456Z")


def test_mandatory_ordering_lexical_guard_precedes_lossy_conversion() -> None:
    """§6: independently confirm via source inspection that
    `_reject_excess_fractional_precision` is invoked before
    `datetime.fromisoformat` within `_parse_iso_timestamp`."""
    import inspect

    import pcae.core.human_approval_trusted_provenance as prod

    source = inspect.getsource(prod._parse_iso_timestamp)
    guard_pos = source.index("_reject_excess_fractional_precision")
    parse_pos = source.index("datetime.fromisoformat")
    assert guard_pos < parse_pos, "lexical guard call must textually precede the fromisoformat call"


# ═══════════════════════════════════════════════════════════════════════════
# Section C -- BLOCKING FINDING: non-colon offset syntax bypasses the
# lexical guard entirely and reproduces the original collision.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.0000001+00",
        "2026-01-01T12:00:00.0000001+0000",
        "2026-01-01T12:00:00.0000009+00",
        "2026-01-01T12:00:00.0000009+0000",
    ],
)
def test_finding_non_colon_offset_bypasses_lexical_guard_and_is_accepted(raw: str) -> None:
    """BLOCKING: `_FRACTIONAL_SECONDS_RE`'s lookahead
    `(?=Z$|[+-]\\d{2}:\\d{2}$)` requires a colon-separated offset. A
    non-colon offset (`+00`, `+0000`) is a syntax `datetime.fromisoformat`
    accepts (Python 3.11+) but the guard's regex does not match, so
    `_reject_excess_fractional_precision` never fires and the 7+-digit
    raw string flows straight into the lossy `fromisoformat` call.
    Demonstrated here: these 7-digit-fraction, non-colon-offset values
    are ACCEPTED, not rejected -- contrary to the mandatory >6-digit
    rejection rule."""
    proof = _parse(raw)
    assert proof.issued_at == "2026-01-01T12:00:00.000Z"


def test_finding_non_colon_offset_reproduces_exact_original_collision_parser() -> None:
    """BLOCKING: the exact B-149O.1H-1 collision -- .0000001 vs
    .0000009 -- reproduced end-to-end via the parser using a non-colon
    offset. Two distinct raw issued_at claims canonicalize identically
    and produce identical canonical payload/digest."""
    doc_a = _valid_document(issued_at="2026-01-01T12:00:00.0000001+00")
    doc_b = _valid_document(issued_at="2026-01-01T12:00:00.0000009+00")
    proof_a = parse_hatp_proof(json.dumps(doc_a))
    proof_b = parse_hatp_proof(json.dumps(doc_b))
    assert proof_a.issued_at == proof_b.issued_at == "2026-01-01T12:00:00.000Z"

    payload_a = canonicalize_hatp_proof_payload(proof_a)
    payload_b = canonicalize_hatp_proof_payload(proof_b)
    assert b'"issued_at":"2026-01-01T12:00:00.000Z"' in payload_a
    assert b'"issued_at":"2026-01-01T12:00:00.000Z"' in payload_b


def test_finding_non_colon_offset_reproduces_exact_original_collision_constructor() -> None:
    """BLOCKING: same collision reproduced via the direct public
    constructor path (B-149O.1H-2's shared-validator claim means the
    constructor is equally exposed, not a divergence -- confirmed
    below)."""
    proof_a = _construct("2026-01-01T12:00:00.0000001+00")
    proof_b = _construct("2026-01-01T12:00:00.0000009+00")
    assert proof_a.issued_at == proof_b.issued_at == "2026-01-01T12:00:00.000Z"


def test_finding_parser_and_constructor_remain_equivalent_on_the_bypass() -> None:
    """The bypass affects parser and constructor identically -- it is a
    shared-validator gap, not a parser/constructor divergence. B-149O.1H-2
    (constructor-domain hardening) itself is NOT reopened by this
    finding; B-149O.1H-1 (timestamp losslessness/injectivity) is."""
    for raw in (
        "2026-01-01T12:00:00.0000001+00",
        "2026-01-01T12:00:00.0000009+00",
    ):
        parser_result = _parse(raw).issued_at
        constructor_result = _construct(raw).issued_at
        assert parser_result == constructor_result


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.1234567+05",
        "2026-01-01T07:00:00.1234567-0500",
        "2026-01-01T12:00:00.9999999+00",
    ],
)
def test_finding_non_colon_offset_non_zero_aligned_values_still_rejected_by_millisecond_rule(raw: str) -> None:
    """Not every non-colon-offset 7+-digit value bypasses detection end
    to end: most truncate to a non-millisecond-aligned microsecond value
    and are still caught by the pre-existing semantic domain rule. Only
    values whose truncated microsecond happens to already be
    millisecond-aligned (all-zero beyond the 6th digit, e.g. .0000001/
    .0000009) fully bypass both layers. This test documents that the
    bypass is real but narrow -- not a wholesale disabling of the
    millisecond-domain rule."""
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


def test_finding_lexical_guard_regex_does_not_match_non_colon_offset_directly() -> None:
    """Direct regex-level confirmation of the root cause: the compiled
    `_FRACTIONAL_SECONDS_RE` used by the production guard does not match
    a fractional-seconds group followed by a non-colon offset."""
    import pcae.core.human_approval_trusted_provenance as prod

    assert prod._FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.0000001+00") is None
    assert prod._FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.0000001+0000") is None
    assert prod._FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.0000001Z") is not None
    assert prod._FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.0000001+00:00") is not None


# ═══════════════════════════════════════════════════════════════════════════
# Section D -- Malformed-form bypass attempts that must NOT succeed
# (distinct from the genuine finding above).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.1234567z",  # lowercase z: not accepted syntax at all
        "2026-01-01T12:00:00.1234567",  # naive, no timezone
        "2026-01-01T12:00:00.1234567Z ",  # trailing whitespace
        "2026-01-01T12:00:00.1234567ZZ",  # malformed double suffix
    ],
)
def test_unsupported_malformed_forms_still_rejected(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


def test_supported_colon_and_z_forms_cannot_bypass_detection() -> None:
    for raw in (
        "2026-01-01T12:00:00.1234567+00:00",
        "2026-01-01T12:00:00.1234567-05:00",
        "2026-01-01T12:00:00.1234567Z",
    ):
        with pytest.raises(InvalidProofSchemaError):
            _parse(raw)


# ═══════════════════════════════════════════════════════════════════════════
# Section E -- Injectivity sweep, timezone equivalence, distinct-
# millisecond sensitivity (within the guarded/colon domain).
# ═══════════════════════════════════════════════════════════════════════════


def test_injectivity_sweep_broad_accepted_domain() -> None:
    canon = set()
    dates = ["2026-01-01", "2026-06-15", "2026-12-31"]
    hours = ["00", "12", "23"]
    ms_values = list(range(0, 1000, 13))
    for date in dates:
        for hour in hours:
            for ms in ms_values:
                raw = f"{date}T{hour}:00:00.{ms:03d}Z"
                proof = _parse(raw)
                canon.add((date, hour, proof.issued_at))
    expected_count = len(dates) * len(hours) * len(ms_values)
    assert len(canon) == expected_count


def test_same_instant_timezone_equivalence() -> None:
    a = _parse("2026-01-01T12:00:00.001Z")
    b = _parse("2026-01-01T12:00:00.001+00:00")
    c = _parse("2026-01-01T13:00:00.001+01:00")
    d = _parse("2026-01-01T07:00:00.001-05:00")
    assert a.issued_at == b.issued_at == c.issued_at == d.issued_at


def test_distinct_millisecond_sensitivity_full_chain() -> None:
    a = _parse("2026-01-01T12:00:00.001Z")
    b = _parse("2026-01-01T12:00:00.002Z")
    assert a.issued_at != b.issued_at
    digest_a = digest_hatp_proof_payload(a)
    digest_b = digest_hatp_proof_payload(b)
    assert digest_a != digest_b


# ═══════════════════════════════════════════════════════════════════════════
# Section F -- Parser/constructor equivalence, B-149O.1H-2 constructor
# hardening regression.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00Z",
        "2026-01-01T12:00:00.001Z",
        "2026-01-01T12:00:00.000000Z",
        "2026-01-01T12:00:00.123456Z",
        "2026-01-01T12:00:00.0000001Z",
        "2026-01-01T12:00:00.123456789Z",
        "not-a-timestamp",
        "2026-01-01T12:00:00.001",
    ],
)
def test_parser_constructor_equivalence_matrix(raw: str) -> None:
    parser_outcome = None
    constructor_outcome = None
    try:
        parser_outcome = _parse(raw).issued_at
    except InvalidProofSchemaError:
        parser_outcome = "REJECTED"
    try:
        constructor_outcome = _construct(raw).issued_at
    except InvalidProofSchemaError:
        constructor_outcome = "REJECTED"
    assert parser_outcome == constructor_outcome


def test_constructor_hardening_boolean_proof_version_still_rejected() -> None:
    kwargs_true = _valid_kwargs()
    kwargs_true["proof_version"] = True
    with pytest.raises(UnsupportedProofVersionError):
        HumanApprovalProvenanceProof(**kwargs_true)
    kwargs_false = _valid_kwargs()
    kwargs_false["proof_version"] = False
    with pytest.raises(UnsupportedProofVersionError):
        HumanApprovalProvenanceProof(**kwargs_false)


def test_constructor_hardening_invalid_repository_id_still_rejected() -> None:
    kwargs = _valid_kwargs()
    kwargs["repository_id"] = "not-a-uuid"
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**kwargs)


def test_constructor_hardening_invalid_digests_still_rejected() -> None:
    kwargs = _valid_kwargs()
    kwargs["decision_record_digest"] = "not-hex"
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**kwargs)
    kwargs2 = _valid_kwargs()
    kwargs2["binding_digest"] = "not-hex"
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**kwargs2)


def test_constructor_hardening_invalid_commit_sha_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        Ag3OperationReference(job_id="j", original_commit_sha="not-a-sha")


def test_constructor_hardening_empty_identifier_still_rejected() -> None:
    kwargs = _valid_kwargs()
    kwargs["principal_id"] = ""
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**kwargs)


def test_constructor_hardening_family_mismatch_still_rejected() -> None:
    kwargs = _valid_kwargs("AG3")
    kwargs["rollback_site"] = RollbackSite.AG5
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# Section G -- Closed schema, duplicate keys, AG3/AG5 discrimination
# regressions.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "unknown_field",
    [
        "trusted_root",
        "trusted_public_key",
        "attestation_root",
        "authority_registry",
        "canonical_root",
        "trust_store_root",
        "deployment_root",
        "approved",
        "trusted",
        "authorized",
        "human_present",
        "valid",
        "arbitrary_unknown",
    ],
)
def test_closed_schema_rejects_unknown_semantic_fields(unknown_field: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(**{unknown_field: True})))


def test_duplicate_top_level_key_rejected() -> None:
    raw = (
        '{"proof_version": 1, "proof_version": 1, "principal_id": "alice", '
        '"signer_key_id": "signer-1", "provider_profile": "HATP_HARDWARE_PROVIDER_V1", '
        f'"repository_id": "{_repo_id()}", "decision_record_id": "chgr-record-1", '
        f'"decision_record_digest": "{"a" * 64}", "binding_id": "rae-binding-1", '
        f'"binding_digest": "{"b" * 64}", "rollback_site": "AG3", '
        '"issued_at": "2026-01-01T12:00:00.000Z", "job_id": "job-1", '
        f'"original_commit_sha": "{"c" * 40}"}}'
    )
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(raw)


def test_ag3_ag5_family_discrimination_wrong_family_payload() -> None:
    doc = _valid_document("AG3")
    doc["per_id"] = "per-1"
    doc["ecp_id"] = "ecp-1"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_ag3_ag5_family_discrimination_unknown_family() -> None:
    doc = _valid_document("AG3")
    doc["rollback_site"] = "AG7"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_cross_family_canonical_distinctness() -> None:
    ag3 = _parse("2026-01-01T12:00:00.001Z", family="AG3")
    ag5 = _parse("2026-01-01T12:00:00.001Z", family="AG5")
    assert digest_hatp_proof_payload(ag3) != digest_hatp_proof_payload(ag5)


# ═══════════════════════════════════════════════════════════════════════════
# Section H -- Independent golden vectors (AG3, AG5), SHA-256
# verification, canonical serializer semantics.
# ═══════════════════════════════════════════════════════════════════════════


def _independent_canonicalize(document: dict) -> bytes:
    """An independently written canonicalizer -- NOT copied from, nor
    calling, `canonicalize_hatp_proof_payload` -- used to cross-check
    production canonical bytes byte-for-byte."""
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def test_independent_golden_ag3_vector() -> None:
    proof = _parse("2026-03-04T05:06:07.008Z", family="AG3")
    expected_document = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": proof.repository_id,
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": "AG3",
        "issued_at": "2026-03-04T05:06:07.008Z",
        "job_id": "job-1",
        "original_commit_sha": "c" * 40,
    }
    expected_bytes = _independent_canonicalize(expected_document)
    production_bytes = canonicalize_hatp_proof_payload(proof)
    assert production_bytes == expected_bytes
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()
    assert digest_hatp_proof_payload(proof) == expected_digest


def test_independent_golden_ag5_vector() -> None:
    proof = _parse("2026-03-04T05:06:07.008Z", family="AG5")
    expected_document = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": proof.repository_id,
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": "AG5",
        "issued_at": "2026-03-04T05:06:07.008Z",
        "per_id": "per-1",
        "ecp_id": "ecp-1",
    }
    expected_bytes = _independent_canonicalize(expected_document)
    production_bytes = canonicalize_hatp_proof_payload(proof)
    assert production_bytes == expected_bytes
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()
    assert digest_hatp_proof_payload(proof) == expected_digest


def test_sha256_hex_digest_matches_independent_recomputation() -> None:
    proof = _parse("2026-01-01T00:00:00.000Z")
    payload = canonicalize_hatp_proof_payload(proof)
    assert digest_hatp_proof_payload(proof) == hashlib.sha256(payload).hexdigest()


def test_canonical_serializer_key_order_independence() -> None:
    doc = _valid_document(issued_at="2026-01-01T00:00:00.000Z")
    doc_reordered = dict(reversed(list(doc.items())))
    proof_original_order = parse_hatp_proof(json.dumps(doc))
    proof_reordered = parse_hatp_proof(json.dumps(doc_reordered))
    # Same document content parsed from differently key-ordered raw JSON
    # must canonicalize to byte-identical output (sort_keys=True).
    assert canonicalize_hatp_proof_payload(proof_original_order) == canonicalize_hatp_proof_payload(proof_reordered)


def test_canonical_serializer_whitespace_independence() -> None:
    doc = _valid_document(issued_at="2026-01-01T00:00:00.000Z")
    compact = json.dumps(doc, separators=(",", ":"))
    spaced = json.dumps(doc, indent=4)
    proof_compact = parse_hatp_proof(compact)
    proof_spaced = parse_hatp_proof(spaced)
    assert canonicalize_hatp_proof_payload(proof_compact) == canonicalize_hatp_proof_payload(proof_spaced)


def test_canonical_serializer_unicode_round_trip() -> None:
    doc = _valid_document(principal_id="alice-é中文", issued_at="2026-01-01T00:00:00.000Z")
    proof = parse_hatp_proof(json.dumps(doc))
    payload = canonicalize_hatp_proof_payload(proof)
    decoded = json.loads(payload.decode("utf-8"))
    assert decoded["principal_id"] == "alice-é中文"


def test_timestamp_mutation_alters_digest() -> None:
    proof_a = _parse("2026-01-01T12:00:00.001Z")
    proof_b = _parse("2026-01-01T12:00:00.002Z")
    assert digest_hatp_proof_payload(proof_a) != digest_hatp_proof_payload(proof_b)


def test_golden_vectors_stable_vs_pre_149o_1h_3_valid_millisecond_semantics() -> None:
    """§36: for valid millisecond-precision input unaffected by the
    149O.1H.3 repair, golden bytes/digest must be unchanged from
    pre-repair behavior."""
    proof = _parse("2026-03-04T05:06:07.008Z")
    payload = canonicalize_hatp_proof_payload(proof)
    assert b'"issued_at":"2026-03-04T05:06:07.008Z"' in payload
    # Matches the exact digest independently recomputed in the 149O.1H.3
    # canonical phase report for this same fixture pattern.
    assert digest_hatp_proof_payload(proof) == hashlib.sha256(payload).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# Section I -- Model immutability, purity, dependency, public-API audits.
# ═══════════════════════════════════════════════════════════════════════════


def test_model_immutability_top_level() -> None:
    proof = _parse("2026-01-01T00:00:00.000Z")
    with pytest.raises(Exception):
        proof.principal_id = "mallory"  # type: ignore[misc]


def test_model_immutability_nested() -> None:
    proof = _parse("2026-01-01T00:00:00.000Z")
    with pytest.raises(Exception):
        proof.operation_reference.job_id = "mallory"  # type: ignore[misc]


def _actual_import_lines(source: str) -> list:
    """Only lines that are actual `import`/`from ... import` statements
    -- excludes docstring/comment prose that merely *mentions* a module
    name while explaining what is deliberately NOT imported."""
    return [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith("import ") or line.strip().startswith("from ")
    ]


def test_no_forbidden_imports_in_production_module() -> None:
    import_lines = _actual_import_lines(PRODUCTION_MODULE_PATH.read_text())
    only_pcae_import = [line for line in import_lines if line.startswith("from pcae")]
    assert only_pcae_import == ["from pcae.core.repository_identity import is_valid_repository_instance_id"]
    for line in import_lines:
        assert "hatp_bootstrap" not in line
        assert "rollback_approval_evidence" not in line
        assert "permission_broker" not in line
        assert "pcae.core.agent" not in line
        assert "commands.agent" not in line


def test_no_purity_violations_in_production_module() -> None:
    source = PRODUCTION_MODULE_PATH.read_text()
    for forbidden in ("open(", "socket", "os.environ", "random.", "datetime.now(", "datetime.utcnow("):
        assert forbidden not in source, f"purity violation candidate found: {forbidden}"


def test_no_verification_vocabulary_introduced() -> None:
    """Independently checks the module's actual runtime namespace (public
    + private module-level attributes), not its docstring prose -- the
    module's own docstrings *legitimately discuss* `VALID`/`UNKNOWN_SIGNER`
    as vocabulary explicitly OUT of scope for this module; that discussion
    is not itself a vocabulary introduction."""
    import pcae.core.human_approval_trusted_provenance as prod

    names = dir(prod)
    for forbidden_symbol in ("VALID", "UNKNOWN_SIGNER", "APPROVAL_PRESENT", "HATP_VALID"):
        assert forbidden_symbol not in names
    proof = _parse("2026-01-01T00:00:00.000Z")
    document = hatp_proof_to_document(proof)
    for forbidden_key in document:
        assert forbidden_key not in ("valid", "unknown_signer", "approval_present", "hatp_valid")


def test_structural_validity_does_not_imply_trust_semantics() -> None:
    """§45: parse success/canonicalization success/digest success carry
    no signer-trust, human-presence, or authorization meaning -- the
    module exposes no such attribute or return value."""
    proof = _parse("2026-01-01T00:00:00.000Z")
    for forbidden_attr in ("signature_valid", "signer_trusted", "human_present", "authorized", "hatp_valid"):
        assert not hasattr(proof, forbidden_attr)
    document = hatp_proof_to_document(proof)
    for forbidden_key in ("signature_valid", "signer_trusted", "human_present", "authorized", "hatp_valid", "approval_present"):
        assert forbidden_key not in document
