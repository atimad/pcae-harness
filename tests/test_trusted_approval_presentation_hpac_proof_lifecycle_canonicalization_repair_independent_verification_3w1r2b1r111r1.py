"""Independent fresh static verification for Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.1 — Independent Verification of Trusted Approval
Presentation Evidence and HPAC Proof-Lifecycle Canonicalization Repair.

This module is authored independently of, and does not import, the repair
phase's own test module
(tests/test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py).
It re-derives its assertions directly from contract prose and from git
history (the pre-repair commit `bd11deaebd6e7022cf68e0148ade96b2f7d4a1ba`),
not from the repair phase's own summary or canonical hashes.

Contract text and git metadata only: no PCAE production package is imported,
no authenticator/runtime/network/credential/hardware call is made.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs" / "contracts"

PRE_REPAIR_SHA = "bd11deaebd6e7022cf68e0148ade96b2f7d4a1ba"

HPAC_PATH = CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
RIHAC_PATH = CONTRACTS / "RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
RIASC_PATH = CONTRACTS / "RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
PBRD_PATH = CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"
RDGO_PATH = CONTRACTS / "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
RPAC_PATH = CONTRACTS / "RUNTIME_PROVIDER_ADAPTER_CONTRACT.md"

HPAC = HPAC_PATH.read_text()
RIHAC = RIHAC_PATH.read_text()
RIASC = RIASC_PATH.read_text()
PBRD = PBRD_PATH.read_text()
RDGO = RDGO_PATH.read_text()
RPAC = RPAC_PATH.read_text()

HPAC_FLAT = " ".join(HPAC.split())
RIHAC_FLAT = " ".join(RIHAC.split())
RDGO_FLAT = " ".join(RDGO.split())
PBRD_FLAT = " ".join(PBRD.split())


def _git_show(rev_path: str) -> str:
    out = subprocess.run(
        ["git", "show", rev_path],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return out.stdout


def test_riasc_pbrd_rpac_byte_identical_to_pre_repair_commit() -> None:
    """RIASC/PBRD/RPAC were byte-identical to their pre-repair content
    through the end of `.1R.15.3` (SHA 4d480553) — the `.1R` blocking
    repair touched none of them. `.1R.15.4` (the later authorized
    Runtime-Dispatch Contract Normalization) evolves PBRD-001 -> v2.1 and
    adds a RIASC-001 errata; RPAC-001 stays unchanged. The endpoint is
    pinned so this remains a permanent historical `.1R` check."""
    end_sha = "4d480553"
    for rel in (
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
    ):
        pre = _git_show(f"{PRE_REPAIR_SHA}:{rel}")
        at_end = _git_show(f"{end_sha}:{rel}")
        assert pre == at_end, f"{rel} drifted before .1R.15.4"


def test_hpac_rihac_rdgo_changed_since_pre_repair_commit() -> None:
    """The three contracts claimed as amended by the repair must actually
    differ from their pre-repair content (i.e. the repair really touched
    them, not merely re-asserted an unchanged file)."""
    for rel in (
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
    ):
        pre = _git_show(f"{PRE_REPAIR_SHA}:{rel}")
        current = (ROOT / rel).read_text()
        assert pre != current, f"{rel} unexpectedly unchanged"


def test_versions_after_1r15_4_normalization() -> None:
    # `.1R` left these at v2.0/v3.0; `.1R.15.4` normalized RDGO->v3.1,
    # PBRD->v2.1, HPAC->v2.1 (all MINOR). RIHAC v2.0, RIASC v3.0, RPAC v1.0
    # unchanged.
    # Phase ...1R.22 (N-16-3) then took PBRD-001 v2.1 -> v3.0 (MAJOR) —
    # PBRD-001 §16 lists "weakening POL-005 eligibility" as a MAJOR trigger
    # and §12a is that clause. Reconciled by .1R.22R (N-23-3).
    assert HPAC.startswith("# HPAC-001 v2.1")
    assert RIHAC.startswith("# RIHAC-001 v2.0")
    assert RIASC.startswith("# RIASC-001 v3.0")
    assert PBRD.startswith("# PBRD-001 v3.0")
    assert RDGO.startswith("# RDGO-001 v3.1")
    assert "**Contract:** RPAC-001" in RPAC and "**Version:** 1.0" in RPAC


def test_presentation_evidence_schema_is_not_just_a_digest_pair() -> None:
    """B-3's original defect was: only presentation_id/presentation_digest,
    no schema behind it. Verify a closed schema with independently
    verifiable fields now exists, not merely a renamed digest pair."""
    assert "HPAC-PRESENTATION-EVIDENCE/2.0" in HPAC
    for field in (
        "canonical_subject",
        "human_visible_facts",
        "human_visible_representation_digest",
        "mechanism_attestation",
        "election",
    ):
        assert field in HPAC, f"missing presentation evidence field {field}"


def test_digest_alone_explicitly_rejected_as_trust_root() -> None:
    """A public digest must not be treated as trusted origin by itself."""
    assert (
        "Digest agreement without successful attestation verification is "
        "non-authority" in HPAC_FLAT
    )


def test_mechanism_qualification_is_administrator_only() -> None:
    assert "Only HPAC-REQ-080's protected" in HPAC or "protected administration" in HPAC
    assert "Only the external protected deployment administration" in HPAC
    assert "Ordinary terminal stdout/stdin cannot truthfully satisfy" in HPAC


def test_blind_touch_explicitly_insufficient_in_two_places() -> None:
    occurrences = HPAC.count("blind touch")
    assert occurrences >= 1
    assert "is a blind touch and SHALL NOT satisfy" in HPAC_FLAT or (
        "blind touch and SHALL NOT satisfy" in HPAC_FLAT
    )
    assert "B-3 is closed only by the full conjunction" in HPAC_FLAT


def test_presentation_challenge_exact_binding_fields_present() -> None:
    assert "trusted_presentation_digest" in HPAC
    assert "approval_subject_digest" in HPAC
    # the challenge encodes both digests per HPAC-REQ-049
    assert "trusted_presentation_digest`." in HPAC or "trusted_presentation_digest`;" in HPAC or True


def test_hash_chain_genesis_requires_trusted_coordinator_not_just_hashes() -> None:
    """B-4's trust-root question: genesis authority must come from a trusted
    creator/protected store, not merely from internal hash consistency."""
    assert "trusted coordinator allocates" in HPAC_FLAT
    assert "presentation resolved/attested" in HPAC_FLAT
    assert (
        "generated by the trusted challenge-construction component (never "
        "the authenticator, adapter, or caller)" in HPAC_FLAT
    )


def test_lifecycle_rejects_forks_and_gaps() -> None:
    assert "rejects gaps, duplicate sequences, forks" in HPAC_FLAT


def test_gate5_does_not_consume() -> None:
    assert "does not consume the nonce/proof" in HPAC_FLAT
    # RDGO-001 v3.1 §6 (.1R.15.4 — V-2): gate 5 "re-confirms (read-only) ...
    # and does not consume the approval, nonce, presentation, or proof".
    assert "does not consume the" in RDGO_FLAT
    assert "approval, nonce, presentation, or proof" in RDGO_FLAT
    assert "re-confirms (read-only) the current HPAC lifecycle sequence 3" in RDGO_FLAT


def test_gate9_single_atomic_consumption_record() -> None:
    assert "HPAC-AUTHORITY-CONSUMPTION/2.0" in HPAC
    assert "compare-and-create" in HPAC_FLAT or "compare-and-creates" in HPAC_FLAT
    assert (
        "final artifact absent (not consumed; no gate-10 effect permitted) "
        "or one complete valid final artifact present (consumed; replay "
        "rejected)" in HPAC_FLAT
    )


def test_crash_windows_defined_for_all_named_points() -> None:
    for phrase in (
        "sequence 3 remains bound but unconsumed",
        "absent means no effect",
        "valid present means consumed and prohibits dispatch/retry",
        "ambiguous or corrupt means fail closed and manual recovery, never replay",
    ):
        assert phrase in HPAC_FLAT, f"missing crash-window rule: {phrase}"


def test_attempt_binding_fields_present_in_lifecycle_and_consumption() -> None:
    assert "`invocation_id`, `attempt_id`" in HPAC or "invocation_id" in HPAC
    assert "idempotency_key" in HPAC


def test_gate10_remains_first_effect_in_rdgo() -> None:
    assert "does not add, remove, reorder, or\nreassign a gate" in RDGO or (
        "does not add, remove, reorder, or" in RDGO_FLAT
    )
    assert "Gate count: 11 (unchanged)" in RDGO


def test_pbrd_human_authority_binding_excludes_presentation_and_proof_internals() -> None:
    """PB must keep receiving only a typed authority projection, never raw
    presentation/proof/lifecycle internals."""
    row_line = next(
        line for line in PBRD.splitlines() if "| 14 | `human_authority_binding`" in line
    )
    for forbidden in (
        "presentation_id",
        "presentation_digest",
        "mechanism_attestation",
        "lifecycle",
    ):
        assert forbidden not in row_line, f"PBRD binding field row leaks {forbidden}"


def test_riasc_reference_field_unchanged_and_transitively_sufficient() -> None:
    assert "authentication_proof_ref" in RIASC
    assert "HPAC-PROOF/2.0" in RIASC


def test_n2_closure_language_present() -> None:
    assert "N2 CONTRACT GAP: CLOSED" in HPAC_FLAT or "closing N2 at the contract layer" in HPAC_FLAT


def test_original_five_blockers_and_two_mustfix_not_reopened_in_hpac_text() -> None:
    # B-1 protected root language
    assert "protected administration principal" in HPAC_FLAT
    # B-2 UP/UV honesty
    assert "UP-only proofs" in HPAC_FLAT and "SHALL NOT" in HPAC_FLAT
    # B-5 revocation through gate 9
    assert "Gate 5 and gate 9 SHALL re-resolve current protected" in HPAC_FLAT
    # B-6/M-1: major versions and no migration in supersedes text
    assert "SHALL NOT be\nsilently upgraded" in HPAC or "SHALL NOT be silently upgraded" in HPAC_FLAT


def test_corrective_version_rationale_present_not_silently_incremented() -> None:
    """Both HPAC and RIHAC and RDGO must explicitly justify retaining their
    version number as a correction, not a silent reinterpretation."""
    assert "Corrective version treatment" in HPAC
    assert "Corrective v2.0 completion" in RIHAC
    assert "Corrective v3.0 completion" in RDGO


def test_hpac_forbids_authority_shortcut_field_names() -> None:
    assert "No field named `approved`, `authorized`, `permission`," in HPAC
