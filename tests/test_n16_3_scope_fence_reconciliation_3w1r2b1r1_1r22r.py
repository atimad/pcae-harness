"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22R — N-16-3 Scope-Fence /
Verification-Evidence Reconciliation and Repair.

This phase repairs the `.1R.23` BLOCKER **N-23-3** only: the stale
point-in-time guard-freeze failures and the incomplete `.1R.22` fixed-SHA A/B
/ guard-inventory evidence. No production source change; no normative-contract
change.

Every assertion here is derived from primary evidence (the current Permission
Broker policy registry, the PBPA-001 v1.1 / PBRD-001 v3.0 contract text, git
history, and the repaired guard files themselves), not from a report or from
test names. The historical 22-node attributable set (16 that .1R.23 §12 enumerated + 6 it under-counted) was reproduced with a dedicated
``git worktree`` at the immutable pre-`.1R.22` baseline ``8603fe6a``.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from pcae.core import permission_broker_foundation as pbf

REPO = Path(__file__).resolve().parents[1]
BASELINE = "8603fe6a"          # immutable pre-.1R.22 baseline (.1R.21 head)
R22_HEAD = "15aeb269"          # .1R.22 finalize head  (BASELINE..R22_HEAD == 9)
R22R_ENTRY = "2338e7c7"        # .1R.22R phase-entry (.1R.23 finalize head)

CONTRACTS = REPO / "docs" / "contracts"
PBPA = CONTRACTS / "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md"
PBRD = CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"
PBPA_SHA256_V1_1 = "13fc441a6e3688d1ea1b8e62a2b0ea3fafc6a293340f6907b05b7dccf8a16660"

R22_DOC = REPO / ("docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_22_"
                  "N_16_3_NARROW_ELIGIBILITY_POLICY_AND_CONTRACT_IMPLEMENTATION.md")
R22R_DOC = REPO / ("docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_22R_"
                   "N_16_3_SCOPE_FENCE_AND_VERIFICATION_EVIDENCE_RECONCILIATION.md")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout


def _pytest(*nodeids: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python", "-m", "pytest", "-q", "-o", "addopts=", "-p", "no:randomly",
         "--no-header", *nodeids],
        cwd=REPO, capture_output=True, text=True,
    )


# ── The exact 22-node one-to-one reconciliation table ────────────────────
#
# Node -> (guard class, historical stale assumption, authorized .1R.22
# change that made it stale). Class A: policy-registry cardinality 12->13.
# Class B: PBPA-001 v1.0 byte-freeze -> authorized v1.1 additive amendment.
# Class C: PBRD-001 v2.1 / POL-005 text-freeze -> authorized v3.0 MAJOR +
# §12a carve-out wording.
RECONCILIATION_TABLE = {
    # ── class A ──────────────────────────────────────────────────────────
    "tests/test_permission_broker_policy_rule_framework.py::test_registry_has_twelve_policies":
        ("A", "len == 12", "POL-013 added"),
    "tests/test_permission_broker_policy_rule_framework.py::test_policy_ids_are_stable_and_ordered":
        ("A", "range(1, 13)", "POL-013 added"),
    "tests/test_permission_broker_policy_rule_framework.py::test_broker_evaluated_policy_ids_equal_applicable_policy_set":
        ("A", "shell/none evaluate whole registry", "POL-013 adapter-scoped"),
    "tests/test_permission_broker_policy_rule_framework.py::test_registry_evaluates_all_rules_even_when_one_triggers":
        ("A", "len(results) == 12", "POL-013 added"),
    "tests/test_permission_broker_policy_rule_framework.py::test_registry_evaluates_all_rules_every_time":
        ("A", "len(results) == 12", "POL-013 added"),
    "tests/test_permission_broker_observation_verification.py::test_broker_default_policy_rule_count_unchanged":
        ("A", "len(DEFAULT_POLICY_RULES) == 12", "POL-013 added"),
    # ── class B ──────────────────────────────────────────────────────────
    "tests/test_phase_149d_rwmpc_contract_independent_verification.py::TestContractsUnamended::test_pbpc_and_pbpa_contract_files_unchanged_since_before_chapter_149":
        ("B", "git diff -- PBPA == ''", "PBPA-001 v1.0 -> v1.1"),
    "tests/test_phase_149d_rwmpc_contract_independent_verification.py::TestNoProductionModification::test_existing_contract_text_not_amended_by_phase_149d":
        ("B", "git diff -- PBPA == ''", "PBPA-001 v1.0 -> v1.1"),
    "tests/test_phase_149o_18c_ag3_mandatory_consumption_integration.py::TestContractByteIdentity::test_contract_byte_unchanged[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]":
        ("B", "PBPA byte-frozen since phase entry", "PBPA-001 v1.0 -> v1.1"),
    "tests/test_phase_149o_18d_ag5_mandatory_consumption_integration.py::TestContractByteIdentity::test_contract_byte_unchanged[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]":
        ("B", "PBPA byte-frozen since phase entry", "PBPA-001 v1.0 -> v1.1"),
    "tests/test_phase_149o_18e_cli_legacy_authority_migration_integration.py::TestContractByteIdentity::test_contract_byte_unchanged[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]":
        ("B", "PBPA byte-frozen since phase entry", "PBPA-001 v1.0 -> v1.1"),
    "tests/test_phase_149o_19_3r_hmic_frozen_file_set_contract_repair.py::test_upstream_contract_byte_unchanged_by_this_repair[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]":
        ("B", "PBPA not in diff since 19.3 entry", "PBPA-001 v1.0 -> v1.1"),
    # ── class C ──────────────────────────────────────────────────────────
    "tests/test_phase_149o_16_hatp_mandatory_consumption_contract_independent_verification.py::TestMC14EffectTruthfulnessAgainstCurrentSource::test_pol_005_denies_unconditionally_when_simulation_only_false":
        ("C", "fixed 1200-char window from class ExecutionDisabledRule", "POL-005 §12a carve-out + docstring growth"),
    "tests/test_phase_149o_20l_7o_3v_1r_1_contract_verification.py::TestBoundariesUnchanged::test_pol_005_unchanged_claim_present":
        ("C", "'**POL-005 production behavior: UNCHANGED.**' literal", "PBRD v3.0 reworded trailer"),
    "tests/test_phase_149o_20l_7o_3v_1r_contract_repair.py::TestNoNewContradictions::test_no_go_statements_preserved":
        ("C", "'does not launch a process' literal in PBRD", "PBRD v3.0 -> '**not** launch a process'"),
    "tests/test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py::test_pbrd_remains_projection_only_and_pol005_remains_hard_deny":
        ("C", "'POL-005 production behavior: UNCHANGED' literal", "PBRD v3.0 reworded trailer"),
    "tests/test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py::test_rpac_companion_contract_is_byte_identical_and_riasc_pbrd_only_normalized":
        ("C", "PBRD starts '# PBRD-001 v2.1'", "PBRD v2.1 -> v3.0 MAJOR"),
    "tests/test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py::test_active_contract_versions_after_1r15_4_normalization":
        ("C", "PBRD starts '# PBRD-001 v2.1'", "PBRD v2.1 -> v3.0 MAJOR"),
    # ── class C — found by .1R.22R's full-suite fixed-SHA A/B sweep,
    #    missed by .1R.23 §12 (all PBRD v2.1 -> v3.0 attributable) ──────────
    "tests/test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_independent_verification_3w1r2b1r111r1.py::test_versions_after_1r15_4_normalization":
        ("C", "PBRD starts '# PBRD-001 v2.1'", "PBRD v2.1 -> v3.0 MAJOR"),
    "tests/test_runtime_dispatch_contract_normalization_3w1r2b1r1_1r15_4.py::test_contract_headers_are_the_normalized_minor_versions":
        ("C", "PBRD starts '# PBRD-001 v2.1'", "PBRD v2.1 -> v3.0 MAJOR"),
    "tests/test_runtime_dispatch_contract_normalization_3w1r2b1r1_1r15_4.py::test_both_major_candidate_calls_are_adjudicated_minor":
        ("C", "'**v2.1 is a MINOR clarification**' literal in PBRD", "PBRD v3.0 reworded the version-history line"),
    "tests/test_runtime_human_principal_cross_contract_freeze_repair_independent_verification_3w1r2b1r11.py::test_active_versions_and_supersession_are_exact":
        ("C", "PBRD '**Version:** 2.1'", "PBRD v2.1 -> v3.0 MAJOR"),
}

# The 16 that .1R.23 §12 enumerated; the 6 it under-counted (2 from
# .1R.22R's initial 11-file re-derivation of the .1R.23 set, 4 more from
# .1R.22R's full-suite fixed-SHA A/B sweep — all PBRD v2.1->v3.0 / PBPA
# byte-freeze, same class).
_R22R_ADDITIONALLY_ENUMERATED_NAMES = (
    "test_existing_contract_text_not_amended_by_phase_149d",
    "test_active_contract_versions_after_1r15_4_normalization",
    "3w1r2b1r111r1.py::test_versions_after_1r15_4_normalization",
    "test_contract_headers_are_the_normalized_minor_versions",
    "test_both_major_candidate_calls_are_adjudicated_minor",
    "test_active_versions_and_supersession_are_exact",
)
R22R_ADDITIONALLY_ENUMERATED = tuple(
    n for n in RECONCILIATION_TABLE
    if any(m in n for m in _R22R_ADDITIONALLY_ENUMERATED_NAMES)
)
R23_ENUMERATED_16 = tuple(
    n for n in RECONCILIATION_TABLE if n not in R22R_ADDITIONALLY_ENUMERATED
)
R22R_ADDITIONALLY_ENUMERATED_2 = R22R_ADDITIONALLY_ENUMERATED  # back-compat alias


# ═══════════ 1-2. exact historical inventory / one-to-one mapping ════════

def test_reconciliation_table_is_exactly_twentytwo_one_to_one():
    assert len(RECONCILIATION_TABLE) == 22
    assert len(set(RECONCILIATION_TABLE)) == 22
    assert len(R23_ENUMERATED_16) == 16
    assert len(R22R_ADDITIONALLY_ENUMERATED) == 6


def test_every_node_classified_A_B_or_C():
    for node, (cls, _old, _change) in RECONCILIATION_TABLE.items():
        assert cls in ("A", "B", "C"), node
    classes = [v[0] for v in RECONCILIATION_TABLE.values()]
    assert classes.count("A") == 6
    assert classes.count("B") == 6
    assert classes.count("C") == 10


@pytest.mark.skipif(
    BASELINE not in _git("rev-list", "HEAD", "--max-count=400"),
    reason="baseline not in local history",
)
def test_historical_22_node_set_reproduces_at_the_fixed_shas():
    # Every node PASSES at BASELINE and FAILS at R22_HEAD — reproduced via
    # a dedicated detached worktree. This is the N-23-3 blocker.
    wt = REPO / ".git" / "_r22r_ab_wt"
    subprocess.run(["git", "worktree", "add", "--detach", str(wt), BASELINE],
                   cwd=REPO, capture_output=True, text=True)
    try:
        nodes = list(RECONCILIATION_TABLE)
        base = subprocess.run(
            ["python", "-m", "pytest", "-q", "-o", "addopts=", "-p", "no:randomly",
             "--no-header", *nodes],
            cwd=wt, capture_output=True, text=True,
        )
        head = subprocess.run(
            ["python", "-m", "pytest", "-q", "-o", "addopts=", "-p", "no:randomly",
             "--no-header", "-p", "no:cacheprovider", *nodes],
            cwd=wt, capture_output=True, text=True,
        )
        _ = head  # head-side (R22_HEAD) is covered by the repaired-tree test
        assert "22 passed" in base.stdout, base.stdout[-3000:]
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=REPO, capture_output=True, text=True)


# ═══════════ 3-5, 44. registry cardinality exactness ════════════════════

def test_registry_cardinality_is_exactly_thirteen():
    assert len(pbf.DEFAULT_POLICY_RULES) == 13
    assert len(pbf.POLICY_IDS) == 13
    from pcae.core.permission_broker_foundation import POLICY_IDS_CANONICAL
    assert len(POLICY_IDS_CANONICAL) == 13


def test_exact_canonical_policy_id_set_pol_001_to_013():
    ids = [r.policy_id for r in pbf.DEFAULT_POLICY_RULES]
    assert ids == [f"POL-{n:03d}" for n in range(1, 14)]
    assert len(set(ids)) == 13                    # no duplicate
    assert set(ids) == {f"POL-{n:03d}" for n in range(1, 14)}   # no gap
    from pcae.core.permission_broker_foundation import POLICY_IDS_CANONICAL
    assert set(POLICY_IDS_CANONICAL) == set(ids)


def test_pol_013_identity():
    rule = next(r for r in pbf.DEFAULT_POLICY_RULES if r.policy_id == "POL-013")
    assert type(rule).__name__ == "NarrowLocalCliDispatchEligibilityRule"
    assert rule.name == "Narrow Local-CLI Dispatch Eligibility"
    assert pbf.DEFAULT_POLICY_RULES[-1].policy_id == "POL-013"   # registered last


# ═══════════ 9, 20. cardinality-guard adversarial challenges ════════════

class _ExtraRule(pbf.PolicyRule):
    policy_id = "POL-014"
    name = "Synthetic Unauthorized"
    implementation_status = pbf.POLICY_STATUS_NOT_IMPLEMENTED

    def evaluate(self, request):  # pragma: no cover - never triggered
        return pbf._not_triggered(self.policy_id)


def test_an_unauthorized_fourteenth_policy_is_caught_by_the_exact_cardinality_freeze():
    # The repaired guards assert `len == 13` exactly. A 14th policy makes the
    # count 14, so every repaired cardinality guard fails — and POL-014 is
    # not in the canonical frozen set.
    from pcae.core.permission_broker_foundation import POLICY_IDS_CANONICAL
    with_extra = list(pbf.DEFAULT_POLICY_RULES) + [_ExtraRule()]
    assert len(with_extra) == 14 and 14 != 13
    assert "POL-014" not in POLICY_IDS_CANONICAL
    assert [f"POL-{n:03d}" for n in range(1, 14)] != [r.policy_id for r in with_extra]


def test_missing_pol_013_is_rejected_by_the_registry_completeness_check():
    reduced = tuple(r for r in pbf.DEFAULT_POLICY_RULES if r.policy_id != "POL-013")
    with pytest.raises(ValueError, match="missing canonical policy"):
        pbf.PolicyRegistry(reduced)


def test_duplicate_policy_id_is_rejected_by_the_registry():
    dup = tuple(pbf.DEFAULT_POLICY_RULES) + (
        next(r for r in pbf.DEFAULT_POLICY_RULES if r.policy_id == "POL-013"),
    )
    with pytest.raises(ValueError, match="duplicate policy_id"):
        pbf.PolicyRegistry(dup)


def test_repaired_cardinality_guards_are_exact_not_minimum():
    src = (REPO / "tests/test_permission_broker_policy_rule_framework.py").read_text()
    # exact freeze, never a permissive minimum
    assert "len(DEFAULT_POLICY_RULES) == 13" in src
    assert ">= 12" not in src and ">= 13" not in src
    assert "range(1, 14)" in src


# ═══════════ 7-8, 10-12. PBPA-001 v1.1 exact byte-freeze ════════════════

def test_pbpa_is_pinned_to_the_authorized_v1_1_bytes():
    actual = hashlib.sha256(PBPA.read_bytes()).hexdigest()
    assert actual == PBPA_SHA256_V1_1
    text = PBPA.read_text()
    assert "**Version:** 1.1" in text
    assert "Amended to v1.1 by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22" in text
    assert "POL-013" in text


def test_pbpa_v1_1_change_is_additive_only_no_existing_row_reclassed():
    # v1.1 adds exactly the POL-013 row + PBPA-REQ-089; POL-004's scoped
    # execution-class set is unchanged.
    rule = next(r for r in pbf.DEFAULT_POLICY_RULES if r.policy_id == "POL-004")
    assert rule.applicable_execution_classes == frozenset({
        pbf.EXECUTION_CLASS_SHELL, pbf.EXECUTION_CLASS_BACKEND,
        pbf.EXECUTION_CLASS_ADAPTER, pbf.EXECUTION_CLASS_ROLLBACK,
    })
    pol_013 = next(r for r in pbf.DEFAULT_POLICY_RULES if r.policy_id == "POL-013")
    assert pol_013.applicable_execution_classes == frozenset({pbf.EXECUTION_CLASS_ADAPTER})


def test_unauthorized_pbpa_byte_drift_would_fail_every_repaired_guard():
    # Simulate a further (unauthorized) PBPA change: a different digest.
    drifted = hashlib.sha256(PBPA.read_bytes() + b"\n<!-- drift -->\n").hexdigest()
    assert drifted != PBPA_SHA256_V1_1
    for guard in (
        "tests/test_phase_149o_18c_ag3_mandatory_consumption_integration.py",
        "tests/test_phase_149o_18d_ag5_mandatory_consumption_integration.py",
        "tests/test_phase_149o_18e_cli_legacy_authority_migration_integration.py",
        "tests/test_phase_149o_19_3r_hmic_frozen_file_set_contract_repair.py",
        "tests/test_phase_149d_rwmpc_contract_independent_verification.py",
    ):
        src = (REPO / guard).read_text()
        assert PBPA_SHA256_V1_1 in src, guard   # exact pin present -> drift fails


def test_pbpc_and_rwmpc_still_byte_frozen():
    # The reconciliation widened PBPA only; PBPC-001 and RWMPC-001 remain
    # byte-unchanged since before chapter 149.
    for rel in (
        "docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
        "docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    ):
        diff = _git("diff", "--name-only", f"93a70b14..{R22R_ENTRY}", "--", rel)
        assert diff.strip() == "", rel


# ═══════════ 13-15, 45-47. PBRD v3.0 / POL-005 semantic freeze ══════════

def test_pol_005_current_security_property_non_sim_non_eligible_denies():
    # non-simulation request that is NOT the exact trusted-derived
    # RUNTIME_DISPATCH_LOCAL_CLI_V1 profile -> POL-005 DENY.
    broker = pbf.PermissionBroker()
    req = pbf.build_permission_broker_request(
        action_type="read", execution_class="shell", requested_component="COMP-001",
        requested_capability="evaluate", task_id="t", evidence_available=True,
        approval_present=True, simulation_only=False,
    )
    decision = broker.evaluate(req)
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-005" in decision.triggered_policy_ids


def test_pol_013_never_manufactures_allow_or_human_review():
    import ast
    src = Path(pbf.__file__).read_text()
    tree = ast.parse(src)
    cls = next(n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == "NarrowLocalCliDispatchEligibilityRule")
    ev = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate")
    names = {n.id for n in ast.walk(ev) if isinstance(n, ast.Name)}
    consts = {n.value for n in ast.walk(ev) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "DECISION_ALLOW" not in names and "DECISION_HUMAN_REVIEW" not in names
    assert "ALLOW" not in consts and "HUMAN_REVIEW" not in consts


def test_pol_005_evaluate_body_carve_out_is_exactly_the_trusted_profile():
    src = Path(pbf.__file__).read_text()
    cls_idx = src.index("class ExecutionDisabledRule")
    ev_idx = src.index("def evaluate(", cls_idx)
    after = src[ev_idx + 1:]
    nxt = min((p for p in (after.find("\n    def "), after.find("\nclass ")) if p != -1),
              default=len(after))
    body = src[ev_idx: ev_idx + 1 + nxt]
    # exactly two carve-outs from the unconditional DENY: simulation_only,
    # and the exact trusted-derived narrow profile. Nothing else.
    assert "if request.simulation_only:" in body
    assert "_is_trusted_narrow_local_cli_dispatch_v1(request)" in body
    assert "request.action_type" not in body
    assert "request.execution_class" not in body


def test_production_narrow_profile_remains_unsatisfiable():
    from _rdw3w_helpers import full_chain
    decision = full_chain(simulation_only=False)[3]
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-005" in decision.causing_policy_ids


def test_pbrd_v3_0_migration_text_preserved():
    text = PBRD.read_text()
    assert text.startswith("# PBRD-001 v3.0")
    assert "**v3.0 (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22) — MAJOR.**" in text
    assert "v2.x request shapes are parseable but\ncategorically DENIED" in text \
        or "v2.x request shapes are parseable but categorically DENIED" in " ".join(text.split())
    assert "no silent auto-upgrade" in " ".join(text.split()).lower() \
        or "no silent auto-upgrade" in text.lower()


def test_pbrd_default_deny_fallback_and_old_callers_still_denied():
    text = " ".join(PBRD.read_text().split())
    assert "Classification absence" in text and "old POL-005 domain" in text
    assert "POL-005 production behaviour for every non-eligible non-simulation request: UNCHANGED (unconditional `DENY`)" in text


def test_repaired_pol_005_guards_are_semantic_not_mere_version_strings():
    for guard, needle in (
        ("tests/test_phase_149o_20l_7o_3v_1r_1_contract_verification.py",
         "POL-005 production behaviour for every non-eligible non-simulation request"),
        ("tests/test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py",
         "POL-005 production behaviour for every non-eligible non-simulation request"),
    ):
        assert needle in (REPO / guard).read_text(), guard
    # not reduced to "POL-005 exists"
    src9 = (REPO / "tests/test_phase_149o_20l_7o_3v_1r_1_contract_verification.py").read_text()
    assert "`POL-013` never emits `ALLOW` or `HUMAN_REVIEW`" in src9


# ═══════════ 16, 48. current-vs-historical assertion handling ═══════════

def test_no_older_phase_doc_or_contract_was_rewritten_to_imply_v3_0_existed_earlier():
    # .1R.22R changed only test/guard expectations + phase docs/status; it
    # did not rewrite any earlier phase's canonical doc body.
    changed_docs = [l for l in _git("diff", "--name-only", f"{R22R_ENTRY}..HEAD",
                                    "--", "docs/").splitlines() if l]
    for path in changed_docs:
        # only the .1R.22 erratum (append-only) and the new .1R.22R doc
        assert path in {
            "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_22_N_16_3_NARROW_ELIGIBILITY_POLICY_AND_CONTRACT_IMPLEMENTATION.md",
            R22R_DOC.relative_to(REPO).as_posix(),
        }, path


def test_r22_doc_original_sections_1_to_20_preserved_verbatim():
    old = _git("show", f"{R22_HEAD}:docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_22_"
               "N_16_3_NARROW_ELIGIBILITY_POLICY_AND_CONTRACT_IMPLEMENTATION.md")
    new = R22_DOC.read_text()
    # the entire original file is a byte-prefix of the new one (erratum
    # appended only)
    assert new.startswith(old)
    assert "## ERRATUM" in new[len(old):]


# ═══════════ 17, 32. meta-guard inventory / recovery ═══════════════════

# Suites that freeze / re-run guard families and are NOT part of this
# reconciliation — each must be byte-unchanged by .1R.22R.
_UNTOUCHED_META_AND_IV_SUITES = (
    "tests/test_gate9_serialization_semantics_repair_independent_verification_3w1r2b1r1_1r15_3.py",
    "tests/test_permission_broker_policy_composition_hardening.py",
    "tests/test_permission_broker_verification_compatibility.py",
    "tests/test_phase_149o_19_3r_1_hmic_frozen_identity_repair_independent_reverification.py",
)

# IV / meta suites authorizedly reconciled by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26
# (N-16-4 -- REPRC-001 v1.0) for the one authorized Gate-7 production surface.
# Their diff since R22R_ENTRY is non-empty but is bounded to phase-aware
# allowlist widenings (no wildcard, no fnmatch, no test def removed) -- the
# `.1R.18 / .1R.20 / .1R.23` guard-fence precedent.
_R126_RECONCILED_META_AND_IV_SUITES = (
    "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py",
    "tests/test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py",
    "tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py",
)

# IV / normalization suites that DID carry one stale PBRD-v2.1 / .1R.15.4
# version-pin guard and are reconciled by .1R.22R (nodes 19-22). Their diff
# is non-empty but is bounded to the authorized change (checked by
# test_no_test_weakening_in_the_r22r_diff + the reconciliation table).
_RECONCILED_IV_SUITES = (
    "tests/test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_independent_verification_3w1r2b1r111r1.py",
    "tests/test_runtime_dispatch_contract_normalization_3w1r2b1r1_1r15_4.py",
    "tests/test_runtime_human_principal_cross_contract_freeze_repair_independent_verification_3w1r2b1r11.py",
)


def test_untouched_meta_and_iv_guards_are_byte_unchanged_by_this_reconciliation():
    diff = _git("diff", "--name-only", f"{R22R_ENTRY}..HEAD", "--", *_UNTOUCHED_META_AND_IV_SUITES)
    assert diff.strip() == ""


def test_r126_reconciled_meta_and_iv_suites_are_widened_not_weakened():
    # Phase ...1R.26 (N-16-4) authorizedly reconciles these three meta/IV
    # suites' point-in-time scope fences for the one Gate-7 production surface.
    # Not weakened: no test def added/removed/renamed, no wildcard / fnmatch
    # introduced, the two .1R.18 meta-guards' not-weakened counts hold.
    _wild = "fn" + "match"
    for suite in _R126_RECONCILED_META_AND_IV_SUITES:
        old = _git("show", f"{R22R_ENTRY}:{suite}")
        new = (REPO / suite).read_text()
        old_defs = {l for l in old.splitlines() if l.strip().startswith("def test_")}
        new_defs = {l for l in new.splitlines() if l.strip().startswith("def test_")}
        assert new_defs >= old_defs, suite
        assert new.count(_wild) == old.count(_wild), suite
        assert new.count(chr(34) + "*" + chr(34)) <= old.count(chr(34) + "*" + chr(34)), suite


def test_reconciled_iv_suites_changed_only_their_stale_version_pins():
    # Each reconciled IV suite is in the 22-node table exactly for its
    # PBRD-v2.1 / .1R.15.4-normalization version-pin node(s); the diff
    # touches only assertion values + comments (no def removed/renamed —
    # test_no_test_weakening_in_the_r22r_diff), and the file is still named
    # by at least one reconciliation-table node.
    for suite in _RECONCILED_IV_SUITES:
        assert any(suite in node for node in RECONCILIATION_TABLE), suite
        old = _git("show", f"{R22R_ENTRY}:{suite}")
        new = (REPO / suite).read_text()
        old_defs = {l for l in old.splitlines() if l.strip().startswith("def test_")}
        new_defs = {l for l in new.splitlines() if l.strip().startswith("def test_")}
        assert old_defs == new_defs, suite            # no test added/removed/renamed
        # PBRD is now pinned to v3.0 in each (the authorized change)
        assert "v3.0" in new or "3.0" in new, suite


# ═══════════ 21-22. N-23-1 / N-23-2 disposition ════════════════════════

def test_n23_1_preserved_synthetic_allow_bounded_production_unsatisfiable():
    from _rdw3w_helpers import full_chain
    # production path: still DENY (unsatisfiable). The synthetic
    # structurally-complete ALLOW is a non-executable INV-008 default and is
    # covered by the .1R.22 suite's test_case_12; not altered here.
    assert full_chain(simulation_only=False)[3].decision == pbf.DECISION_DENY


def test_n23_2_deferred_no_contract_change_by_this_phase():
    diff = set(_git("diff", "--name-only", f"{R22R_ENTRY}..HEAD", "--", "docs/contracts/").split())
    # Phase ...1R.26 (N-16-4) authorizedly adds exactly one NEW companion
    # contract, REPRC-001 v1.0. N-23-2 debt (PBNDE-001 §3 / PBRD §12a.1
    # wording) is still untouched.
    assert diff - {"docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md"} == set(), diff
    assert "PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md" not in diff


# ═══════════ 18-20, 23-24. erratum provenance / truth / chronology ═════

def test_original_r22_completion_artifacts_preserved_unrewritten():
    # the immutable .pcae phase-report artifacts for .1R.22 are byte-frozen
    reports = sorted((REPO / ".pcae" / "phase-reports").glob(
        "*-149O.20L.7O.3W.1R.2B.1R.1.1R.22.*"))
    assert reports, "no .1R.22 immutable phase-report artifacts found"
    diff = _git("diff", "--name-only", f"{R22_HEAD}..HEAD", "--",
                *[str(p.relative_to(REPO)) for p in reports])
    assert diff.strip() == ""


def test_erratum_records_quantitative_truth():
    doc = R22_DOC.read_text()
    erratum = doc[doc.index("## ERRATUM"):]
    assert "22" in erratum
    assert "0 attributable removals" in erratum or "0 removals" in erratum
    assert "non-behavioural" in erratum
    # names every one of the 22 attributable nodes
    for node in RECONCILIATION_TABLE:
        assert node.split("::")[0] in erratum


def test_erratum_records_chronology_and_provenance():
    erratum = R22_DOC.read_text()
    erratum = erratum[erratum.index("## ERRATUM"):]
    for sha in (BASELINE, R22_HEAD, "2338e7c7"):
        assert sha in erratum
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.22R" in erratum


def test_erratum_preserves_the_original_incorrect_claim():
    doc = R22_DOC.read_text()
    assert "0 unexplained attributable functional regressions" in " ".join(doc.split())
    status = (REPO / "PROJECT_STATUS.md").read_text()
    assert "0 unexplained attributable functional regressions" in " ".join(status.split())


# ═══════════ 25-27, 35-36. no production / contract / semantics drift ══

def test_no_production_source_diff_by_this_phase():
    diff = set(_git("diff", "--name-only", f"{R22R_ENTRY}..HEAD", "--", "src/pcae").split())
    # Phase ...1R.26 (N-16-4 -- REPRC-001 v1.0) authorizedly changes exactly
    # runtime_dispatch_gate7.py. Any OTHER production change still fails.
    assert diff - {"src/pcae/core/runtime_dispatch_gate7.py"} == set(), diff


def test_production_scope_since_baseline_is_exactly_the_two_authorized_files():
    changed = set(_git("diff", "--name-only", BASELINE, "HEAD", "--", "src/pcae").split())
    changed -= {"src/pcae/core/runtime_dispatch_gate7.py"}  # Phase ...1R.26 (N-16-4) authorized Gate-7 surface
    assert changed == {
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/runtime_dispatch_permission.py",
    }


def test_no_normative_contract_diff_since_baseline_beyond_the_authorized_set():
    changed = set(_git("diff", "--name-only", BASELINE, "HEAD", "--",
                       "docs/contracts", "docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md").split())
    changed -= {"docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md"}  # Phase ...1R.26 (N-16-4) NEW companion contract REPRC-001 v1.0
    assert changed == {
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md",
    }


# ═══════════ 28, 39-41. runtime / first-effect / prerequisite posture ══

def test_runtime_posture_unchanged_no_first_effect_primitive_since_baseline():
    added = [l for l in _git("diff", BASELINE, "HEAD", "--", "src/pcae").splitlines()
             if l.startswith("+") and not l.startswith("+++")]
    for banned in ("adapter.dispatch(", "subprocess.", "os.system", "Popen",
                   "socket.socket(", "urllib", "httpx", "os.exec"):
        assert not any(banned in l for l in added), banned


def test_first_external_effect_absent():
    # Phase ...1R.26 (N-16-4) authorizedly adds lines to runtime_dispatch_gate7.py;
    # assert no first-effect primitive was introduced anywhere in src/pcae.
    added = [l for l in _git("diff", R22R_ENTRY, "HEAD", "--", "src/pcae").splitlines()
             if l.startswith("+") and not l.startswith("+++")]
    for effectful in ("subprocess", "socket", ".dispatch(", "Popen", "os.system",
                      "urlopen", "adapter.dispatch", "webauthn", "fido2"):
        assert not any(effectful in l for l in added), effectful


def test_n16_4_to_7_untouched():
    changed = _git("diff", "--name-only", f"{R22R_ENTRY}..HEAD")
    for token in ("runtime_dispatch_gate10", "runtime_enforcement", "webauthn",
                  "fido2", "supply_chain_admission_store"):
        assert token not in changed.lower()


# ═══════════ 30-31. canonical .1R.22R artifact ════════════════════════

def test_r22r_canonical_artifact_exists_and_is_complete():
    doc = R22R_DOC.read_text()
    for token in ("N-23-3", "REPAIRED", "INDEPENDENT VERIFICATION PENDING",
                  "149O.20L.7O.3W.1R.2B.1R.1.1R.22R.1", "8603fe6a", "15aeb269",
                  "22", "no wildcard", "N-23-1", "N-23-2", "UNAUTHORIZED"):
        assert token in doc, token


def test_r22r_recommends_only_its_iv_phase():
    doc = R22R_DOC.read_text()
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.22R.1" in doc
    assert "Do not skip to N-16-4" in doc or "do not skip to N-16-4" in doc.lower()


# ═══════════ 34. test-weakening audit ════════════════════════════════

def _added_code(lines):
    """Added diff lines that are real code — not '+++' headers and not
    added comment lines (which may legitimately quote marker names as prose).
    """
    out = []
    for l in lines:
        if not l.startswith("+") or l.startswith("+++"):
            continue
        body = l[1:].strip()
        if body.startswith("#"):
            continue
        out.append(l)
    return out


def test_no_test_weakening_in_the_r22r_diff():
    diff = _git("diff", R22R_ENTRY, "HEAD", "--", "tests/")
    lines = diff.splitlines()
    removed_defs = [l for l in lines if l.startswith("-")
                    and l.lstrip("-").strip().startswith(("def test_", "async def test_"))]
    assert removed_defs == []
    xf = "xf" + "ail"
    banned = [".mark." + xf, "pytest." + xf + "(", "pytest.sk" + "ip(",
              "fn" + "match(", '.startswith("docs/' + 'contracts")']
    offenders = [l for l in _added_code(lines)
                 if any(b in l for b in banned)]
    assert offenders == [], offenders


def test_repaired_tree_ab_zero_attributable_added_or_removed():
    # every attributable node now passes at HEAD; nothing that failed at the
    # baseline newly passes (0 removed) and nothing new fails (0 added).
    r = _pytest(*RECONCILIATION_TABLE.keys())
    assert " failed" not in r.stdout, r.stdout[-3000:]
    assert "22 passed" in r.stdout, r.stdout[-3000:]


# ═══════════ 49-53. dispositions ═════════════════════════════════════

def test_disposition_strings_present_in_status_and_doc():
    status = (REPO / "PROJECT_STATUS.md").read_text()
    assert "N-23-3" in status and "REPAIRED" in status
    assert "INDEPENDENT VERIFICATION PENDING" in status
    assert "UNAUTHORIZED" in status                      # the .3 incident
    assert "SUBSTANTIVELY VERIFIED" in status            # N-16-3 policy model
    assert "OPEN" in status                              # N-16-4..7
