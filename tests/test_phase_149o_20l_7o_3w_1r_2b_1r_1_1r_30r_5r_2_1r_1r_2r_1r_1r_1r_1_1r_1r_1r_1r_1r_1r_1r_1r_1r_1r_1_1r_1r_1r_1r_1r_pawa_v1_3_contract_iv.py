"""Independent Verification of HPAC-PAWA-001 v1.3 — Certification-Coordinator
Authority Contract.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R
(alias N16-5-H3-PAWA13-IV; HPAC-PAWA-REQ-274).

This is a *verification-only* phase. It authors NO production certification
path, edits NO normative contract text, performs NO ceremony, and does NOT
close N-16-5. The assertions below independently reconstruct the v1.2 -> v1.3
authority model from:

  * the immutable git history of the contract document,
  * the v1.2 baseline blob and the v1.3 freeze blob,
  * primary-source production modules (`hpac_lifecycle.py`,
    `human_authentication_proof.py`, `hpac_rhamp_counter_state.py`,
    `hpac_protected_admin_writer.py`, `hpac_rhamp_terminal_reasons.py`),
  * the current schema module,

and check them against the frozen v1.3 text — rather than trusting the
predecessor freeze verdict or its passing tests.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------- #
# Immutable lineage anchors (independently derived from git topology).
# --------------------------------------------------------------------------- #

#: IV phase-entry SHA (V0) — finalized predecessor N16-5-H3-PAWA13 head.
V0 = "4977a2e5db362e9e86f898cf438578f00e8051f5"
#: Predecessor (contract-freeze) phase-entry SHA — guard-attribution baseline.
H0 = "b2530066b062b14b3c6f6df7c71c3092b22f215b"
#: The commit whose parent holds the v1.2 contract text and whose tree holds
#: the v1.3 freeze (independently confirmed: it is the freeze commit).
V13_FREEZE = "76523d8ce07435619127fbf19491a8d200ceb4bc"
#: v1.2 contract-text baseline blob commit (V13_FREEZE^, the "open phase task"
#: commit; contract byte-identical to H0).
V12_BASELINE = "ab5b471d06619e452433e624a971f5e1c84b400d"

PAWA_REL = "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
PAWA = ROOT / PAWA_REL
PPA = ROOT / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
RHAMP = ROOT / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
HBDC = ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
HATP_PROV = ROOT / "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
SCHEMAS = ROOT / "src/pcae/core/hpac_pawa_schemas.py"

#: The five certification-lifecycle roles, independently taken from the
#: positive-chain writer roles in the production lifecycle / proof / counter
#: modules (NOT copied from the contract).
POSITIVE_CHAIN_ROLES = (
    "hpac_challenge_coordinator",
    "hpac_assertion_recorder",
    "human_authentication_proof_verifier",
    "hpac_gate5_binder",
    "hpac_rhamp_counter_state_verifier",
)
TERMINATOR_ROLE = "hpac_lifecycle_terminator"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def _blob(commit: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{rel}"], cwd=ROOT)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(path: Path) -> str:
    return re.sub(r"\s+", " ", text(path))


@pytest.fixture(scope="module")
def pawa() -> str:
    return text(PAWA)


@pytest.fixture(scope="module")
def pawa_flat() -> str:
    return flat(PAWA)


@pytest.fixture(scope="module")
def v12() -> str:
    return _blob(V12_BASELINE, PAWA_REL).decode("utf-8")


# --------------------------------------------------------------------------- #
# 1. Lineage / phase-entry.
# --------------------------------------------------------------------------- #


def test_01_v0_phase_entry_sha_resolves() -> None:
    assert _git("rev-parse", "HEAD").strip() == V0
    assert _git("rev-list", "--count", "origin/main..HEAD").strip() == "0"


def test_02_cpipc_candidate_is_direct_valid_successor() -> None:
    from pcae.core import phase_id as p

    pred = (
        "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R."
        "1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R"
    )
    cand = pred + ".1R"
    a, b = p.parse(pred), p.parse(cand)
    assert p.is_valid(pred) and p.is_valid(cand)
    assert p.same_series(a, b) and p.same_branch(a, b)
    assert p.compare(a, b) == "less"  # strict ordering, predecessor first
    # direct successor: candidate == predecessor + exactly one trailing segment
    assert b.subphase[: len(a.subphase)] == a.subphase
    assert len(b.subphase) == len(a.subphase) + 1
    assert b.subphase[-1] == (1, "R")


def test_03_v13_freeze_commit_is_the_contract_freeze() -> None:
    subject = _git("log", "-1", "--format=%s", V13_FREEZE)
    assert "HPAC-PAWA-001 v1.2 -> v1.3 FROZEN" in subject
    assert _git("rev-parse", f"{V13_FREEZE}^").strip() == V12_BASELINE


# --------------------------------------------------------------------------- #
# 2. v1.2 -> v1.3 immutable normative delta.
# --------------------------------------------------------------------------- #


def test_04_contract_is_v1_3_frozen(pawa: str) -> None:
    assert pawa.startswith("# HPAC-PAWA-001 v1.3 ")
    assert re.search(r"^\*\*Version:\*\* 1\.3$", pawa, re.M)
    assert re.search(r"^\*\*Status:\*\* FROZEN$", pawa, re.M)


def test_05_v12_baseline_was_v1_2(v12: str) -> None:
    assert v12.startswith("# HPAC-PAWA-001 v1.2 ")
    assert re.search(r"^\*\*Version:\*\* 1\.2$", v12, re.M)


def test_06_contract_text_unchanged_since_freeze() -> None:
    # v1.3 normative text is byte-identical at the freeze commit and at V0 —
    # this IV must not (and did not) edit it.
    assert _blob(V13_FREEZE, PAWA_REL) == _blob(V0, PAWA_REL) == PAWA.read_bytes()


def test_07_only_this_contract_changed_v12_to_v13() -> None:
    changed = _git("diff", "--name-only", V12_BASELINE, V13_FREEZE, "--", "docs/contracts").split()
    assert changed == [PAWA_REL]


def test_08_normative_delta_sections_present(pawa: str) -> None:
    # The v1.3 delta is confined to these new / edited sections.
    for header in (
        "## 7B. v1.2 → v1.3 normative delta table",
        "## 33A. Certification-coordinator recognition sequence (v1.3)",
        "## 38A. Authorized certification consumer (v1.3)",
        "## 39A. Certification consumer inventory guard (v1.3)",
        "## 42B. Certification-lifecycle writer family (v1.3)",
        "## 42C. v1.3 rejection cases",
        "## 43A. Certification session and subject scope (v1.3)",
        "## 44A. Certification currentness / replay (v1.3)",
        "## 49A. Certification-lifecycle one-ceremony lifetime (v1.3)",
        "## 68A. Certification authority walls (v1.3)",
        "### 80.3 v1.3 versioning rule (finding S-2)",
        "### 90.3 v1.3 contract-freeze verdict",
    ):
        assert header in pawa, header


def test_09_delta_introduces_no_unrelated_authority(v12: str, pawa: str) -> None:
    # Every line the diff *adds* must be certification-scoped, a lineage/history
    # note, an inventory/count line, or the specialization of §96. Assert there
    # is no added mention of runtime enablement, dispatch, N-16-6/N-16-7
    # progression, or a new companion contract creation.
    added = [
        ln[1:]
        for ln in _git("diff", V12_BASELINE, V13_FREEZE, "--", PAWA_REL).splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
    ]
    body = re.sub(r"\s+", " ", "\n".join(added).lower())
    # No positive grant of runtime / execution / dispatch authority is added.
    for smuggled in (
        "enables execution",
        "authorizes the first external effect",
        "grants a runtime capability",
        "issues a dispatchenvelope",
        "unblocks n-16-6",
        "unblocks n-16-7",
        "adds a new companion contract",
    ):
        assert smuggled not in body
    # The delta's runtime/effect language is present only in denial framing.
    assert "authorizes no first external effect" in body
    assert "gate-5 assurance result" in body
    # Every added sentence-fragment that pairs the coordinator with a runtime
    # effect keeps it on the deny side.
    assert "certification authority ≠ execution authority" in body


# --------------------------------------------------------------------------- #
# 3. Version classification — MINOR / S-2.
# --------------------------------------------------------------------------- #


def test_10_minor_s2_rule_and_major_review_present(pawa_flat: str) -> None:
    assert "HPAC-PAWA-REQ-269" in pawa_flat and "Explicit MINOR rule (S-2)" in pawa_flat
    assert "HPAC-PAWA-REQ-270" in pawa_flat and "v1.3 MAJOR-trigger review — none fires" in pawa_flat
    assert "⇒ HPAC-PAWA-001 v1.3 — MINOR." in pawa_flat


def test_11_no_major_trigger_fires(pawa_flat: str) -> None:
    # Independently walk each §152 MAJOR trigger and confirm v1.3 rebuts it.
    for rebuttal in (
        "does **not** make `sudo` / `euid` / an environment variable sufficient",
        "does **not** collapse or remove the configured-agent exclusion",
        "does **not** permit a same-principal agent / deployment-owner topology",
        "does **not** introduce a remote / network / cloud authority service",
        "does **not** make any certification capability bearer, durable, serialisable, or reusable",
        "does **not** broaden the capability into runtime approval / PB permission / RE result",
        "does **not** change the bootstrap trust root away from OS filesystem write authority",
        "does **not** remove the `generation` / rollback-prevention protection",
        "does **not** add a signing key / pinned key / keychain requirement",
        "does **not** widen the authorized-consumer inventory by wildcard / prefix / glob",
    ):
        assert re.sub(r"\s+", " ", rebuttal) in pawa_flat, rebuttal


def test_12_minor_shape_matches_the_v1_2_precedent(v12: str) -> None:
    # v1.2 §80.2 classified `configure_presentation_mechanism` — "one explicitly
    # enumerated protected-admin metadata mutation family" — as MINOR
    # (HPAC-PAWA-REQ-230). v1.3 uses the identical shape and cites it.
    assert "Therefore v1.2 is a **MINOR**." in v12
    assert "the direct precedent of **v1.2 §80.2**" in flat(PAWA)


def test_13_section_153_permits_this_evolution() -> None:
    m = re.search(r"HPAC-PAWA-REQ-153\.\*\*(.+?)HPAC-PAWA-REQ-154", flat(PAWA))
    assert m
    permit = m.group(1)
    assert "add an authorized-consumer **category** by explicit enumeration (never wildcard)" in permit
    assert "add one explicitly enumerated protected-admin **metadata mutation family**" in permit
    assert "no MAJOR trigger in §152 fires" in permit


def test_14_req_154_not_violated(v12: str, pawa: str) -> None:
    # §96 for the *existing* §42 administrative-mutation family is unchanged in
    # scope: v1.3 rescopes REQ-096's subject to "§42 administrative-mutation"
    # and adds a separate carve-out for the new family — it does not widen an
    # already-minted §42 capability.
    assert "A `PRODUCTION` writer capability SHALL NOT authorize" in re.sub(r"\s+", " ", v12)
    assert "A **§42 administrative-mutation** `PRODUCTION` writer capability SHALL NOT authorize" in re.sub(
        r"\s+", " ", pawa
    )
    assert "This rule is **specialized, not redefined**" in re.sub(r"\s+", " ", pawa)


# --------------------------------------------------------------------------- #
# 4. Requirement / invariant inventory.
# --------------------------------------------------------------------------- #


def _req_ids(s: str) -> list[int]:
    return [int(v) for v in re.findall(r"^ *- \*\*HPAC-PAWA-REQ-(\d{3})\.\*\*", s, re.M)]


def test_15_requirement_ids_sequential_1_to_275(pawa: str) -> None:
    ids = _req_ids(pawa)
    # closed, no gaps, no duplicates, no reuse (definitions are grouped by
    # section, not strictly file-ordered — the invariant is on the set).
    assert sorted(ids) == list(range(1, 276))
    assert len(ids) == len(set(ids)) == 275


def test_16_v13_additions_are_req_234_to_275(v12: str, pawa: str) -> None:
    assert max(_req_ids(v12)) == 233
    new_ids = sorted(set(_req_ids(pawa)) - set(_req_ids(v12)))
    assert new_ids == list(range(234, 276))


def test_17_invariants_sequential_1_to_13(pawa: str) -> None:
    invs = sorted({int(v) for v in re.findall(r"PAWA-INV-(\d+)", pawa)})
    assert invs == list(range(1, 14))
    assert pawa.count("- **PAWA-INV-13.**") == 1  # defined exactly once


def test_18_historical_req_087_088_223_224_semantics_preserved(v12: str, pawa: str) -> None:
    for rid in ("087", "088", "223", "224"):
        v12_body = re.search(rf"- \*\*HPAC-PAWA-REQ-{rid}\.\*\*(.+?)(?=\n- \*\*HPAC-PAWA-REQ-|\n## )", v12, re.S)
        cur_body = re.search(rf"- \*\*HPAC-PAWA-REQ-{rid}\.\*\*(.+?)(?=\n- \*\*HPAC-PAWA-REQ-|\n## )", pawa, re.S)
        assert v12_body and cur_body
        # The v1.2 sentence(s) survive verbatim inside the (possibly extended)
        # v1.3 requirement — the certification exception is added by NEW
        # requirement ids, never by re-meaning a frozen one.
        v12_core = re.sub(r"\s+", " ", v12_body.group(1)).strip().split(" HPAC-PAWA-001 v1.3")[0]
        assert v12_core[:120] in re.sub(r"\s+", " ", cur_body.group(1))


# --------------------------------------------------------------------------- #
# 5. Closed category + closed five-role allowlist (primary-source grounded).
# --------------------------------------------------------------------------- #


def test_19_positive_chain_roles_are_exactly_these_five() -> None:
    # Independently reconstruct the positive authentication chain from prod src.
    lc = text(ROOT / "src/pcae/core/hpac_lifecycle.py")
    assert '_GENESIS_WRITER_ROLE = "hpac_challenge_coordinator"' in lc
    assert '_ASSERTION_WRITER_ROLE = "hpac_assertion_recorder"' in lc
    assert '_VERIFIED_WRITER_ROLE = "human_authentication_proof_verifier"' in lc
    assert '_BOUND_WRITER_ROLE = "hpac_gate5_binder"' in lc
    assert '_TERMINAL_WRITER_ROLE = "hpac_lifecycle_terminator"' in lc
    proof = text(ROOT / "src/pcae/core/human_authentication_proof.py")
    assert '_WRITER_ROLE = "human_authentication_proof_verifier"' in proof
    ctr = text(ROOT / "src/pcae/core/hpac_rhamp_counter_state.py")
    assert 'COUNTER_STATE_VERIFIER_ROLE = "hpac_rhamp_counter_state_verifier"' in ctr
    assert "apply_after_verification requires an accepted counter decision" in ctr


def test_20_contract_allowlist_equals_primary_source_positive_chain(pawa: str) -> None:
    m = re.search(r"closed five-role allowlist\*\* is \*\*exactly\*\*:\s*```(.+?)```", pawa, re.S)
    assert m
    listed = tuple(re.findall(r"[a-z0-9_]+", m.group(1)))
    assert set(listed) == set(POSITIVE_CHAIN_ROLES)
    assert TERMINATOR_ROLE not in listed


def test_21_terminator_explicitly_denied(pawa_flat: str) -> None:
    assert "`hpac_lifecycle_terminator`" in pawa_flat
    assert (
        "which writes only the negative terminal states `EXPIRED` / `REVOKED` / `REJECTED`) is **explicitly NOT** a member"
        in pawa_flat
    )
    # terminator maps to a denial code, never a positive path
    assert "including `hpac_lifecycle_terminator`" in pawa_flat


def test_22_no_wildcard_prefix_glob_role_or_consumer(pawa_flat: str) -> None:
    assert "No wildcard, no prefix match, no `fnmatch`, no arbitrary role argument" in pawa_flat
    assert "no future role implicitly authorized" in pawa_flat
    assert "Neither name is a prefix, glob, or\n  category wildcard".replace("\n ", "") in pawa_flat.replace("  ", " ")
    assert "No glob / `fnmatch` / prefix\n  broadening of the certification consumer inventory is ever permitted".replace(
        "\n ", ""
    ) in pawa_flat.replace("  ", " ")


def test_23_authorized_consumer_set_stays_closed(pawa_flat: str) -> None:
    assert "The authorized-consumer set stays\n  **closed** — extended only by this explicit enumeration.".replace(
        "\n ", ""
    ) in pawa_flat.replace("  ", " ")
    assert "adds **exactly one** authorized" in pawa_flat
    assert "pcae.core.hpac_certification_coordinator" in pawa_flat
    assert "scripts/hpac_certification_admin.py" in pawa_flat


def test_24_new_category_distinct_from_ordinary_actors(pawa_flat: str) -> None:
    assert (
        "**No** launcher, helper, presentation store, verifier\n  (`hpac_verifier` as an importer of the factory), "
        "Gate, gate coordinator,\n  runtime, agent, CLI, or plugin is added to this inventory.".replace("\n ", "")
        in pawa_flat.replace("  ", " ")
    )


def test_25_test_fixture_not_authorized(pawa_flat: str) -> None:
    assert "any test fixture or\n  phase-specific orchestration harness".replace("\n ", "") in pawa_flat.replace("  ", " ")
    assert "Test-only seals remain NON-PRODUCTION" in pawa_flat
    assert "does **not**\n  legitimize `HPACStoreAuthority._production_test_fixture`".replace("\n ", "") in pawa_flat.replace(
        "  ", " "
    )


# --------------------------------------------------------------------------- #
# 6. §33A recognition sequence — reuse of §33, fail-closed.
# --------------------------------------------------------------------------- #


def test_26_33a_reuses_33_steps_1_to_9_verbatim(pawa_flat: str) -> None:
    assert "SHALL run, as **required conjuncts**,\n  the §33 steps 1–9 **verbatim**".replace(
        "\n ", ""
    ) in pawa_flat.replace("  ", " ")
    for conjunct in (
        "canonical-root resolution and trust (§25)",
        "`HPAC-PAWA-AGENT-EXCLUSION/1.0` load",
        "live uid ==\n  provisioned_uid",
        "the configured-agent exclusion\n  negative boundary (§26)",
        "descriptor trust",
        "`current-generation.json` incl. `agent_exclusion_digest`",
        "the not-configured-agent current-context check (§31)",
        "the `O_EXCL | O_NOFOLLOW`\n  positive write probe under `.authority/` (§28)",
        "the authorized-factory-consumer\n  check (§32)",
    ):
        assert re.sub(r"\s+", " ", conjunct) in pawa_flat, conjunct


def test_27_33a_removing_any_conjunct_reopens_a_threat(pawa_flat: str) -> None:
    assert "Removing any one re-opens a named §20 threat; no single conjunct is\n  sufficient (PAWA-INV-3).".replace(
        "\n ", ""
    ) in pawa_flat.replace("  ", " ")


def test_28_33a_adds_consumer_role_session_mint_audit_steps(pawa_flat: str) -> None:
    assert "verify the calling module is the **exact** §38A certification consumer" in pawa_flat
    assert "member of the **closed five-role allowlist**" in pawa_flat
    assert "validate the **certification-session context binding**" in pawa_flat
    assert "mint **one** process-local, single-use, restart-dead `PRODUCTION`" in pawa_flat
    assert "record the issuance audit evidence" in pawa_flat


def test_29_33a_fresh_run_every_call_atomic(pawa_flat: str) -> None:
    assert "SHALL run fresh on **every**\n  `certification_writer(...)` call".replace("\n ", "") in pawa_flat.replace(
        "  ", " "
    )
    assert "one atomic recognition\n  unit".replace("\n ", "") in pawa_flat.replace("  ", " ")
    assert "PAWA-INV-3,\n  PAWA-INV-12, PAWA-INV-13".replace("\n ", "") in pawa_flat.replace("  ", " ")


def test_30_33a_fails_closed(pawa_flat: str) -> None:
    assert "The sequence **fails closed**" in pawa_flat
    assert "**no** certification\n  capability is minted".replace("\n ", "") in pawa_flat.replace("  ", " ")
    assert "The absence of a denial\n  is never authority.".replace("\n ", "") in pawa_flat.replace("  ", " ")


def test_31_recognition_authority_basis_is_not_ambient(pawa_flat: str) -> None:
    assert "the §33A authority basis is the\n  §33 conjunction".replace("\n ", "") in pawa_flat.replace("  ", " ")
    assert "live effective filesystem write authority + the descriptor +\n  the write probe".replace(
        "\n ", ""
    ) in pawa_flat.replace("  ", " ")


# --------------------------------------------------------------------------- #
# 7. Mint authority — dedicated, closed, non-generic.
# --------------------------------------------------------------------------- #


def test_32_dedicated_certification_writer_factory(pawa_flat: str) -> None:
    assert "minted **only** by a distinct\n  `certification_writer(...)` factory".replace("\n ", "") in pawa_flat.replace(
        "  ", " "
    )
    assert "same\n  non-agent-importable admin-only production module".replace("\n ", "") in pawa_flat.replace("  ", " ")


def test_33_ordinary_writer_cannot_self_select_certification_role(pawa_flat: str) -> None:
    assert (
        "`HPACStoreAuthority.writer(role)` SHALL\n  continue to `raise HPACAuthorityError` for every non-`FIXTURE_NON_REAL` class".replace(
            "\n ", ""
        )
        in pawa_flat.replace("  ", " ")
    )
    assert "no new public generic mint function, no\n  string-addressable role escalation".replace(
        "\n ", ""
    ) in pawa_flat.replace("  ", " ")


def test_34_no_generic_production_writer_authority_introduced(pawa_flat: str) -> None:
    assert "GENERIC PRODUCTION WRITER AUTHORITY = NOT INTRODUCED" in re.sub(r"\s+", " ", pawa_flat)
    assert "no caller-controlled role argument is\n  introduced".replace("\n ", "") in pawa_flat.replace("  ", " ")


def test_35_no_remint_no_delegation_no_escalation(pawa_flat: str) -> None:
    assert "FACTORY ≠ CONSUMER, CONSUMER ≠ MINTER" in pawa_flat
    assert (
        "does\n  **not** permit the coordinator (or anything it calls) to remint, delegate,\n  convert to generic authority, serialise, store, or reissue".replace(
            "\n ", ""
        )
        in pawa_flat.replace("  ", " ")
    )


# --------------------------------------------------------------------------- #
# 8. Per-role bounded authority (matches primary source).
# --------------------------------------------------------------------------- #


def test_36_per_role_table_bindings(pawa: str) -> None:
    row = {
        "hpac_challenge_coordinator": ("open_challenge_canonical", "STATE_CHALLENGE_CREATED", "subject=proof_id"),
        "hpac_assertion_recorder": ("record_assertion_canonical", "STATE_ASSERTION_RECEIVED", "subject=proof_id"),
        "human_authentication_proof_verifier": ("create_canonical", "STATE_PROOF_VERIFIED", "subject=proof_id"),
        "hpac_gate5_binder": ("bind_gate5_canonical", "STATE_PROOF_VERIFIED_AND_BOUND", "subject=proof_id"),
        "hpac_rhamp_counter_state_verifier": (
            "apply_after_verification",
            "one bounded transition",
            "subject=credential_id",
        ),
    }
    flat_p = re.sub(r"\s+", " ", pawa)
    for role, (action, state, subject) in row.items():
        assert action in flat_p, (role, action)
        assert state in flat_p, (role, state)
        assert subject in flat_p, (role, subject)


def test_37_assertion_recorder_does_not_imply_authentication_success(pawa: str) -> None:
    assert "forging assertion validity" in pawa
    assert "skipping signature / challenge / credential-currentness / UP / UV / counter validation" in re.sub(
        r"\s+", " ", pawa
    )


def test_38_proof_verifier_cannot_directly_mint_a_production_principal(pawa: str) -> None:
    assert "directly minting a PRODUCTION `AuthenticatedHumanPrincipal` outside" in re.sub(r"\s+", " ", pawa)
    assert "verify_human_authentication(require_real_assurance=True)" in pawa


def test_39_gate5_binder_cannot_manufacture_gate_or_principal(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "manufacturing a principal; manufacturing a Gate result" in f
    assert "overriding PB / policy" in f
    assert "trusted verifier-issued" in f


def test_40_counter_verifier_is_bounded(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "on an **accepted** counter decision only" in f
    assert "resetting counters; arbitrarily setting values; modifying credential identity or revocation" in f


def test_41_presentation_evidence_outside_family(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "`HPAC-PRESENTATION-EVIDENCE/2.0` is **outside** this family." in f
    assert "reuses the existing `mint_protected_presentation_evidence_writer` path **unchanged**" in f
    assert "HPAC-PPA-001 v1.0 are unaffected" in f


# --------------------------------------------------------------------------- #
# 9. Capability lifetime semantics.
# --------------------------------------------------------------------------- #


def test_42_non_bearer_process_local_restart_dead_single_use(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "§45 (process-local), §46\n  (non-bearer), §47 (non-serializable), §48 (restart invalidation) apply to the\n  certification family **verbatim**".replace(
        "\n ", " "
    ).replace("  ", " ") in f.replace("  ", " ")
    assert "single-use per role **per one authentication ceremony**" in f
    assert "no reusable / bearer / cross-ceremony certification authority is\n  contemplated".replace("\n ", "") in f.replace(
        "  ", " "
    )


def test_43_one_ceremony_short_lived_process(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "one certification ceremony per\n  invocation, the process exits after".replace("\n ", "") in f.replace("  ", " ")
    assert "**no** certification capability that survives the\n  ceremony it was minted for".replace("\n ", "") in f.replace(
        "  ", " "
    )


def test_44_type_change_if_needed_is_additive_only(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "the\n  change is\n  **additive** (a spent flag / one-shot wrapper), never a weakening".replace("\n ", " ").replace(
        "  ", " "
    ) in f.replace("  ", " ")


def test_45_currentness_replay_semantics_preserved(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "v1.3 introduces\n  **no** new TTL".replace("\n ", "") in f.replace("  ", " ")
    assert "The certification coordinator SHALL NOT bypass any of them" in f


# --------------------------------------------------------------------------- #
# 10. §68A walls + PAWA-INV-13.
# --------------------------------------------------------------------------- #


def test_46_certification_authority_ne_execution_authority(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "**Certification authority ≠ execution authority.**" in f
    assert "SHALL\n  NOT: satisfy Gate 6 / 7 / 8 / 9 / 10; create a `DispatchEnvelope`".replace("\n ", "") in f.replace(
        "  ", " "
    )
    assert "terminates no later than the\n  bounded Gate-5 certification result".replace("\n ", "") in f.replace("  ", " ")


def test_47_coordinator_cannot_manufacture_human_approve_or_uv(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "SHALL NOT\n  manufacture: a human APPROVE or REJECT; FIDO2 user presence; FIDO2 user\n  verification".replace(
        "\n ", ""
    ) in f.replace("  ", " ")
    assert "`coordinator ≠ human principal`" in f
    assert "Deployment owner ≠ human approver" in f


def test_48_real_ne_deterministic(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "**Real ≠ deterministic.**" in f
    assert "SHALL NOT convert deterministic authentication\n  evidence into REAL assurance".replace("\n ", "") in f.replace(
        "  ", " "
    )
    assert "it does not relax the check" in f


def test_49_pb_and_policy_wall(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "issue a runtime approval, a Permission Broker permission, a policy\n  exception, a Runtime Enforcement result".replace(
        "\n ", ""
    ) in f.replace("  ", " ")


def test_50_gate5_not_manufactured_not_bypassed(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "**Gate 5 is not manufactured and not bypassed.**" in f
    assert "Gate 5 success is **not** transformed into a bearer authorization\n  token".replace("\n ", "") in f.replace(
        "  ", " "
    )


def test_51_n16_6_n16_7_exclusion(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "**N-16-6 / N-16-7 exclusion.**" in f
    assert "v1.3 contains **no**\n  runtime-enablement clause".replace("\n ", "") in f.replace("  ", " ")
    assert "N-16-7 strictly last" in f


def test_52_pawa_inv_13_captures_non_escalation(pawa: str) -> None:
    m = re.search(r"- \*\*PAWA-INV-13\.\*\*(.+?)(?=\n\n## )", pawa, re.S)
    assert m
    inv = re.sub(r"\s+", " ", m.group(1))
    assert "one** explicitly enumerated non-agent-importable consumer" in inv
    assert "closed **five-role**" in inv
    assert "**single-use**, **process-local**,\n  **non-bearer**, **restart-dead**".replace("\n ", "") in inv.replace(
        "  ", " "
    )
    assert "terminates** at the bounded Gate-5\n  assurance result".replace("\n ", "") in inv.replace("  ", " ")
    assert "No new `pawa_failure_code`; no RHAMP-001 edit; no protected-root schema change." in inv


# --------------------------------------------------------------------------- #
# 11. Vocabulary / schema sufficiency — primary-source grounded.
# --------------------------------------------------------------------------- #


def test_53_no_new_pawa_operation() -> None:
    from pcae.core.hpac_protected_admin_writer import PawaOperation

    assert {m.value for m in PawaOperation} == {
        "enroll_principal",
        "revoke_principal",
        "enroll_credential",
        "revoke_credential",
        "initialize_credential_sidecar_state",
        "configure_presentation_mechanism",
    }
    assert not any("cert" in m.value for m in PawaOperation)
    assert "It is **not** a new `PawaOperation`" in re.sub(r"\s+", " ", text(PAWA))


def test_54_pawa_failure_codes_still_21_and_unchanged() -> None:
    from pcae.core.hpac_protected_admin_writer import PAWA_FAILURE_CODES

    assert len(PAWA_FAILURE_CODES) == len(set(PAWA_FAILURE_CODES)) == 21
    # src is byte-identical since H0 -> the taxonomy is unchanged by v1.3.
    assert _blob(H0, "src/pcae/core/hpac_protected_admin_writer.py") == _blob(
        V0, "src/pcae/core/hpac_protected_admin_writer.py"
    )


def test_55_every_v13_rejection_maps_to_an_existing_code(pawa: str) -> None:
    from pcae.core.hpac_protected_admin_writer import PAWA_FAILURE_CODES

    codes = set(PAWA_FAILURE_CODES)
    m = re.search(r"## 42C\..+?\n(.+?)\n## 43A", pawa, re.S)
    assert m
    mapped = set(re.findall(r"`([a-z_]+)`\s*\|\s*\d+\s*\|", m.group(1)))
    assert mapped, "no mapped codes parsed"
    assert mapped <= codes, mapped - codes
    assert {"unauthorized_factory_consumer", "operation_scope_invalid", "target_scope_invalid",
            "capability_stale", "reconstruction_attempt", "internal_fail_closed"} <= mapped


def test_56_no_new_rhamp_terminal_reason_code_no_rhamp_edit() -> None:
    from pcae.core import hpac_rhamp_terminal_reasons as tr

    assert len(tr.TERMINAL_REASON_CODES) == 41
    assert _blob(H0, RHAMP.relative_to(ROOT).as_posix()) == _blob(V0, RHAMP.relative_to(ROOT).as_posix())
    assert "41-code vocabulary is byte-unchanged; RHAMP-001 is not edited." in re.sub(r"\s+", " ", text(PAWA))


def test_57_no_new_schema_field_or_artifact(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "schemas are byte-unchanged by v1.3" in f
    assert "adds\n  **no** field to any protected-root schema, **no** new\n  protected-root artifact, and **no** new provisioning step".replace(
        "\n ", ""
    ) in f.replace("  ", " ")
    assert _blob(H0, SCHEMAS.relative_to(ROOT).as_posix()) == _blob(V0, SCHEMAS.relative_to(ROOT).as_posix())


def test_58_no_companion_contract_required(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "v1.3 adds no new companion contract" in f
    assert "v1.3 is additive and authority-preserving; no parent cascade" in f


# --------------------------------------------------------------------------- #
# 12. Cross-contract byte identity + semantic consistency.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "rel",
    [
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",  # HPAC-001 v2.1
        "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md",  # RHAMP-001
        "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",  # HBDC-001 v1.2
        "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md",  # HPAC-PPA-001 v1.0
        "src/pcae/core/hpac_pawa_schemas.py",  # descriptor + current-generation schemas
    ],
)
def test_59_related_frozen_artifacts_byte_unchanged(rel: str) -> None:
    assert _blob(V12_BASELINE, rel) == _blob(V13_FREEZE, rel) == _blob(V0, rel)


def test_60_cross_contract_semantic_consistency(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "§96's verifier-only\n  lifecycle-record rule is **specialized** by the §42B narrow enumerated exception,\n  not left in contradiction".replace(
        "\n ", ""
    ) in f.replace("  ", " ")
    assert "the closed-consumer-set language of §38 / §87 is\n  **extended by explicit enumeration** (§38A), not opened".replace(
        "\n ", ""
    ) in f.replace("  ", " ")
    # RHAMP §57 map unchanged claim
    assert "The PAWA→RHAMP map (§57) is **unchanged**" in f


# --------------------------------------------------------------------------- #
# 13. Mechanism / principal neutrality; no instance data.
# --------------------------------------------------------------------------- #


def test_61_mechanism_neutrality_preserved(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "**Mechanism neutrality.**" in f
    assert "SHALL NOT hardcode\n  YubiKey, USB, a specific AAGUID, one hardware brand".replace("\n ", "") in f.replace(
        "  ", " "
    )
    assert "Future mobile / passkey authentication profiles" in f
    assert "The canonical PrincipalRecord\n  stays mechanism-neutral; `human principal ≠ credential`".replace(
        "\n ", ""
    ) in f.replace("  ", " ")


def test_62_no_instance_ids_frozen_normatively(pawa: str) -> None:
    # The only occurrences of a concrete principal/credential id are inside the
    # clauses that forbid freezing them (with an ellipsis), never as normative
    # authority data.
    flat_p = re.sub(r"\s+", " ", pawa)
    for m in re.finditer(r"(hp-8cee9b36|hpc-2e7bbfa0)", flat_p):
        window = flat_p[max(0, m.start() - 400) : m.start()]
        assert ("SHALL NOT normatively" in window) or ("none frozen" in window) or (
            "SHALL NOT\n normatively" in window
        ) or ("v1.3 SHALL NOT" in window), window[-120:]
    assert "**No instance data in the contract.**" in flat_p


# --------------------------------------------------------------------------- #
# 14. Guard reconciliation independence (this phase + predecessor).
# --------------------------------------------------------------------------- #


def test_63_predecessor_touched_no_production_source() -> None:
    out = _git("diff", "--name-only", H0, V0, "--", "src/pcae", "scripts", "pyproject.toml").strip()
    assert out == "", out


def test_64_predecessor_guard_edits_did_not_remove_or_rename_a_test() -> None:
    changed = [
        p
        for p in _git("diff", "--name-only", H0, V0, "--", "tests").splitlines()
        if p.endswith(".py")
    ]
    assert changed
    for path in changed:
        try:
            old = _git("show", f"{H0}:{path}")
        except subprocess.CalledProcessError:
            continue  # newly added file
        old_defs = set(re.findall(r"^\s*(?:async +)?def (test_\w+)", old, re.M))
        new_defs = set(re.findall(r"^\s*(?:async +)?def (test_\w+)", text(ROOT / path), re.M))
        assert old_defs <= new_defs, f"{path}: dropped/renamed {old_defs - new_defs}"


def test_65_predecessor_guard_edits_did_not_add_skip_or_xfail() -> None:
    for path in _git("diff", "--name-only", H0, V0, "--", "tests").splitlines():
        if not path.endswith(".py"):
            continue
        try:
            old = _git("show", f"{H0}:{path}")
        except subprocess.CalledProcessError:
            continue
        new = text(ROOT / path)
        for tok in ("pytest.mark." + "skip", "x" + "fail"):
            assert new.count(tok) <= old.count(tok), f"{path}: {tok} count increased"


# N16-5-H3-IMPL (149O...30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R):
# this contract-IV phase completed at its own final commit; its `.1R`
# successor N16-5-H3-IMPL is the sanctioned §33A/§38A/§42B implementation
# phase. Re-anchor this guard's endpoint from the moving `HEAD` to the fixed
# IV-completion SHA so it keeps asserting exactly what it was written to
# assert — that THIS IV made no source / contract edit — without falsely
# implicating the downstream implementation phase.
_IV_COMPLETION = "74e52d59738007c4b9f6dbeb28f83990ba82e9a8"


def test_66_this_iv_edits_no_normative_contract_or_source() -> None:
    changed = set(_git("diff", "--name-only", V0, _IV_COMPLETION).split())
    for p in changed:
        assert not p.startswith("src/pcae/")
        assert not p.startswith("scripts/")
        assert p != PAWA_REL
        assert not (p.startswith("docs/contracts/"))


# --------------------------------------------------------------------------- #
# 15. Boundaries — no implementation, no ceremony, runtime unchanged.
# --------------------------------------------------------------------------- #


def test_67_no_certification_production_module_exists() -> None:
    # N16-5-H3-IMPL re-anchor: assert the certification production surface did
    # not exist AS OF THIS IV's COMPLETION (the IV was verification-only). Its
    # `.1R` successor N16-5-H3-IMPL is the phase that builds it; checking the
    # live tree would falsely fail once the sanctioned implementation lands.
    def _absent_at(rev: str, path: str) -> bool:
        import subprocess as _sp

        return _sp.run(["git", "cat-file", "-e", f"{rev}:{path}"], cwd=ROOT,
                       capture_output=True).returncode != 0

    assert _absent_at(_IV_COMPLETION, "src/pcae/core/hpac_certification_coordinator.py")
    assert _absent_at(_IV_COMPLETION, "scripts/hpac_certification_admin.py")
    admin_writer = _git("show", f"{_IV_COMPLETION}:src/pcae/core/hpac_protected_admin_writer.py")
    assert "def certification_writer" not in admin_writer


def test_68_runtime_unchanged() -> None:
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    assert "Runtime status:            not_implemented" in out
    assert "Runtime state:             Observed" in out
    assert "Execution capability:      unavailable" in out
    assert "Plugin count:              0" in out
    assert "Capability count:          0" in out


def test_69_n16_5_not_closed_marker(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "**N-16-5 remains NOT CLOSED**" in f or "N-16-5: NOT CLOSED" in f
    assert "H-3 CONTRACT BLOCKER: RESOLVED" in f
    assert "H-3 PRODUCTION IMPLEMENTATION: PENDING" in f


def test_70_dedicated_v13_iv_is_the_recommended_default(pawa: str) -> None:
    f = re.sub(r"\s+", " ", pawa)
    assert "HPAC-PAWA-REQ-274" in f
    assert "A **dedicated independent verification of HPAC-PAWA-001 v1.3** SHALL run **before**\n  the H-3 implementation phase relies on this text".replace(
        "\n ", ""
    ) in f.replace("  ", " ")
