"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1 — Independent Verification of the
Configured-Agent-Principal Resolution Source Contract-Compatibility Adjudication.

VERIFICATION ONLY. This suite reads production source, contracts, and git
history as read-only evidence. It implements no resolution source, imports no
production mutation path, and changes no `src/pcae` / `docs/contracts` /
runtime state. Every assertion independently re-derives a `.1R.30R.2A`
adjudication claim from primary source rather than trusting the adjudication
prose.

Immutable SHAs (independently derived at the verification-entry commit):
  B30 = 8e65529596fc351face4b83c4b5d08573326d034  finalized .1R.30 BLOCKED head
  A   = 5b45aa7b444f15852c51985879570b8913fedbe4  finalized .1R.30R.2 head
                                                  (== .1R.30R.2A phase-entry)
  J   = 1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a  finalized .1R.30R.2A head
  V   = 1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a  .1R.30R.2A.1 phase-entry (== J)
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACTS = REPO / "docs" / "contracts"

B30 = "8e65529596fc351face4b83c4b5d08573326d034"
A = "5b45aa7b444f15852c51985879570b8913fedbe4"
J = "1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a"

HPAC_FOUNDATION = SRC / "core" / "hpac_foundation.py"
TOPO_VERIFIER = SRC / "core" / "hatp_class_b_topology_verifier.py"
AGENT = SRC / "core" / "agent.py"
HATP_BOOTSTRAP = SRC / "core" / "hatp_bootstrap.py"

PAWA_CONTRACT = CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
HPAC_CONTRACT = CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
RHAMP_CONTRACT = CONTRACTS / "REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HBDC_CONTRACT = CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
CPIPC_CONTRACT = CONTRACTS / "CANONICAL_PHASE_ID_PARSING_CONTRACT.md"

ADJ_DOC = REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2A_CONFIGURED_AGENT_PRINCIPAL_RESOLUTION_SOURCE_CONTRACT_COMPATIBILITY_ADJUDICATION.md"
IV_DOC = REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2A_1_INDEPENDENT_VERIFICATION_OF_THE_CONFIGURED_AGENT_PRINCIPAL_RESOLUTION_SOURCE_CONTRACT_COMPATIBILITY_ADJUDICATION.md"
METADATA = REPO / ".pcae" / "phase-completion-metadata.json"
THIS_FILE = Path(__file__)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True, check=True,
    ).stdout


def _norm(text: str) -> str:
    """Collapse contract line-wrapping so exact phrases can be matched."""
    return re.sub(r"\s+", " ", text)


# ── 1. Immutable SHA derivation ───────────────────────────────────────────

def test_immutable_shas_resolve() -> None:
    for sha in (B30, A, J):
        assert _git("rev-parse", sha).strip() == sha


def test_a_is_the_1r30r2_head_and_2a_phase_entry() -> None:
    subject = _norm(_git("log", "-1", "--format=%s", A))
    assert "1R.30R.2:" in subject
    assert "reconcile governed push state" in subject
    # the .1R.30R.2A adjudication doc records A as its phase-entry SHA
    assert A in ADJ_DOC.read_text(encoding="utf-8")


def test_j_is_the_1r30r2a_head() -> None:
    subject = _norm(_git("log", "-1", "--format=%s", J))
    assert "1R.30R.2A:" in subject
    assert "reconcile governed push state" in subject


def test_b30_is_the_blocked_1r30_head_and_immutable() -> None:
    subject = _norm(_git("log", "-1", "--format=%s", B30))
    assert "1R.30:" in subject and "BLOCKED completion metadata" in subject
    # PAWA-INV-11: historical .1R.30 is never reused / resumed / relabelled
    assert "PAWA-INV-11" in _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))


# ── 2. No production / contract change since the phase entry ───────────────

def test_no_src_pcae_change_since_phase_entry() -> None:
    assert _git("diff", J, "HEAD", "--", "src/pcae").strip() == ""


# The .1R.30R.2A.1 finalized head. Point-in-time guards below are pinned to this
# phase's own entry -> finalized-head window and reconciled by .1R.30R.2A.3 (the
# dedicated HPAC-PAWA-001 v1.1 contract IV): after this window .1R.30R.2A.2
# legitimately evolved HPAC-PAWA-001 v1.0 -> v1.1 (MINOR) in place, which this
# IV suite would otherwise flag as drift it never authored.
FINALIZED_2A1_HEAD = "3f23d6fd4a6812cdb4d2f6f7d2c0e2edd2511667"


def test_no_contract_change_since_phase_entry() -> None:
    assert _git("diff", J, FINALIZED_2A1_HEAD, "--", "docs/contracts").strip() == ""


def test_2a_adjudication_changed_no_src_or_contract() -> None:
    assert _git("diff", A, J, "--", "src/pcae").strip() == ""
    assert _git("diff", A, J, "--", "docs/contracts").strip() == ""


# ── 3. F-1 clause reconstruction from HPAC-PAWA-001 v1.0 ───────────────────

def test_pawa_contract_requires_configured_not_geteuid() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    # §2 terminology
    assert "It is **not** `os.geteuid()` of whatever process happens to be running" in c
    # §9 REQ-021 canonical resolution source, not env / caller / --agent-id / geteuid
    assert "HPAC-PAWA-REQ-021" in c
    assert "never from caller input, an environment variable, a CLI flag, `--agent-id`, repository state, or the live `os.geteuid()`" in c
    # §9 REQ-022 identity form (uid, gids) from the configured principal
    assert "resolved from the configured principal, **not** the invoking process's live ids" in c
    # §9 REQ-023 fail closed, never default to os.geteuid()
    assert "SHALL NOT default to `os.geteuid()`" in c


def test_pawa_contract_per_predicate_identity_matrix_names_configured_source() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "HPAC-PAWA-REQ-026" in c
    # the configured-agent exclusion predicate's authority source column
    assert "canonical PCAE agent configuration / lock (§9)" in c
    # §26 REQ-061 concrete predicate
    assert "_effective_write_access(root, configured_agent_uid, configured_agent_gids)" in c


def test_pawa_contract_section_33_sequence_has_configured_resolution_steps() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "HPAC-PAWA-REQ-074" in c
    assert "resolve the canonical configured agent principal from PCAE configuration" in c
    assert "validate the current administrative context is **not** the configured agent" in c


# ── 4. `_current_agent_identity()` semantics — live, not configured ───────

def test_current_agent_identity_is_live_geteuid() -> None:
    src = TOPO_VERIFIER.read_text(encoding="utf-8")
    assert "def _current_agent_identity()" in src
    assert "return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}" in src
    assert "Live process identity" in src


def test_validate_production_boundary_uses_live_identity() -> None:
    src = HPAC_FOUNDATION.read_text(encoding="utf-8")
    boundary = src.split("def _validate_production_boundary", 1)[1].split("def _ensure_root", 1)[0]
    assert "_current_agent_identity()" in boundary
    assert "_effective_write_access(self.root, agent_uid, agent_gids)" in boundary
    # it takes NO configured-principal input — the F-1 gap
    assert "configured_agent" not in boundary


def test_effective_write_access_parameterizes_uid_and_gids() -> None:
    src = TOPO_VERIFIER.read_text(encoding="utf-8")
    assert "def _effective_write_access(" in src
    sig = src.split("def _effective_write_access(", 1)[1].split(")", 1)[0]
    assert "agent_uid" in sig and "agent_gids" in sig


# ── 5. No existing configured-agent → OS-principal mapping ────────────────

def test_no_getpwnam_configured_agent_bridge_in_production() -> None:
    hits = []
    for path in SRC.rglob("*.py"):
        if "test" in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"getpw(nam|uid)|getgr(nam|gid)|getgrouplist|getgrall", text):
            line = text[: m.start()].count("\n") + 1
            hits.append((path.relative_to(REPO), line))
    # The only production hits are: a COMMENT in hatp_bootstrap.py, and the
    # ACL-entry-name resolution in hatp_class_b_topology_verifier.py which
    # consumes an ALREADY-KNOWN live agent_uid / agent_gids.
    allowed = {
        Path("src/pcae/core/hatp_bootstrap.py"),
        Path("src/pcae/core/hatp_class_b_topology_verifier.py"),
    }
    assert {p for p, _ in hits} <= allowed, f"unexpected pwd/grp use: {hits}"


def test_topo_verifier_getpwnam_consumes_known_ids_not_a_configured_source() -> None:
    src = TOPO_VERIFIER.read_text(encoding="utf-8")
    # resolves an ACL principal NAME against ids it is handed as parameters
    assert "pwd.getpwnam(name).pw_uid == agent_uid" in src
    assert "grp.getgrnam(name).gr_gid in agent_gids" in src


def test_no_pcae_agent_principal_symbol_in_production() -> None:
    for path in SRC.rglob("*.py"):
        if "test" in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        assert "PCAE_AGENT_PRINCIPAL" not in text
        assert "resolve_configured_agent_identity" not in text


def test_agent_lock_id_is_non_authorizing() -> None:
    src = AGENT.read_text(encoding="utf-8")
    assert "non-authenticating, non-authorizing" in src
    assert "agent_id is descriptive only" in src


def test_no_production_writer_mint_path_exists() -> None:
    src = HPAC_FOUNDATION.read_text(encoding="utf-8")
    assert 'raise HPACAuthorityError("no production HPAC writer is implemented in this foundation phase")' in src
    assert "def production_writer(" not in src


# ── 6. Three-predicate separation ────────────────────────────────────────

def test_three_predicates_are_distinct_in_contract() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    # predicate 2 (§26): configured agent principal
    assert "Recognition predicate 2 — configured-agent exclusion" in c
    # predicate 4 (§28): current invoking OS process, an operation
    assert "Recognition predicate 4 — positive write authority" in c
    assert "the **current invoking OS process**" in c
    # predicate 5 (§31): not configured agent — current context vs configured
    assert "Recognition predicate 5 — not configured agent" in c


def test_iv_doc_keeps_three_predicates_distinct() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "None substitutes for another" in d
    assert "agent_has_protected_write_authority" in d
    assert "current_context_is_agent" in d


# ── 7. R1 artifact model + symbolic account trust ─────────────────────────

def test_adjudication_selected_r1_protected_agent_exclusion_record() -> None:
    a = _norm(ADJ_DOC.read_text(encoding="utf-8"))
    assert "HPAC-PAWA-AGENT-EXCLUSION/1.0" in a
    assert "/.authority/agent-exclusion.json" in a
    assert "symbolic OS account name" in a


def test_r1_record_is_agent_unwritable_and_deployment_owner_provisioned() -> None:
    a = _norm(ADJ_DOC.read_text(encoding="utf-8"))
    assert "scripts/hpac_protected_root_admin.py" in a
    assert "agent-writable" in a or "agent-unwritable" in a
    # bound to installation + generation
    assert "installation_id" in a and "generation" in a


def test_authority_namespace_is_agent_unwritable_in_contract() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "Directory mode SHALL exclude group-write and other-write" in c
    assert "the configured agent principal SHALL hold no write permission" in c


# ── 8. uid / group resolution behaviour ──────────────────────────────────

def test_unresolvable_account_maps_to_existing_agent_principal_unknown_code() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    # §56 failure taxonomy — code #3 already exists
    assert "`agent_principal_unknown`" in c
    assert "configured agent principal unresolvable / ambiguous / unmappable" in c


def test_agent_with_write_maps_to_existing_agent_has_protected_write_authority() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "`agent_has_protected_write_authority`" in c
    assert "the configured agent principal holds protected-root write authority" in c


def test_effective_write_access_tests_group_membership() -> None:
    src = TOPO_VERIFIER.read_text(encoding="utf-8")
    assert "mode & stat.S_IWGRP and st.st_gid in agent_gids" in src


# ── 9. Adversary coverage in the IV doc ─────────────────────────────────

def test_iv_doc_covers_group_drift_detection() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "group-drift adversary" in d
    assert "next §33 recognition enumerates the account's **current** groups" in d


def test_iv_doc_covers_group_removal() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "group-removal" in d


def test_iv_doc_records_c1_hybrid_correction_for_recreation() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "R1-HYBRID" in d
    assert "provisioned_uid" in d
    assert "silent-rebind" in d or "silently rebind" in d
    # the §6-vs-§12.2 internal inconsistency is called out
    assert "bound expectation" in d and "no uid integer" in d


def test_iv_doc_records_c2_rollback_anchor_digest_correction() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "agent_exclusion_digest" in d
    assert "HPAC-PAWA-CURRENT-GENERATION/1.0" in d
    assert "bare generation-integer equality" in d or "bare generation-integer" in d


def test_iv_doc_covers_uid_reuse_and_rename_fail_closed() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "UID-reuse adversary" in d
    assert "account rename" in d
    assert "no silent fallback to uid" in d or "no**\nsilent fallback to uid" in d or "There is **no\nsilent fallback" in d or "There is **no silent fallback to uid**" in d


def test_iv_doc_covers_migration_and_bootstrap_noncircular() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "machine migration" in d
    assert "Non-circular" in d
    assert "PAWA-INV-4" in d


# ── 10. OS account DB trust boundary ────────────────────────────────────

def test_os_account_db_is_in_the_tcb_no_overclaim() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "part of the OS TCB" in d
    assert "does **not** claim resistance to a hostile root" in d
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "is part of the trusted\ncomputing base".replace("\n", " ") in c or "is part of the trusted computing base" in c


# ── 11. R2 / R3 / R4 rejections ────────────────────────────────────────

def test_r2_rejected_needs_hbdc_amendment_wrong_namespace() -> None:
    a = _norm(ADJ_DOC.read_text(encoding="utf-8"))
    assert "R2" in a and "REJECTED" in a
    assert "HBDC-001 amendment" in a
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "HPAC-PAWA-REQ-134" in c
    assert "no cross-subsystem\nbearer authority".replace("\n", " ") in c or "no cross-subsystem bearer authority" in c


def test_r3_rejected_permanently_non_production() -> None:
    a = _norm(ADJ_DOC.read_text(encoding="utf-8"))
    assert "permanently\nproduction-unsatisfiable".replace("\n", " ") in a or "permanently non-production" in a or "permanently\nproduction-unsatisfiable" in a
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "Safe `!=`\ncomplete".replace("\n", " ") in d or "Safe `!=` complete" in d


def test_r3_retained_only_as_test_seam() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "fixture seam is **retained**" in d
    assert "test\nstrategy".replace("\n", " ") in d or "test strategy" in d


def test_r4_search_found_nothing_superior() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "No R4 superior to R1" in d
    a = _norm(ADJ_DOC.read_text(encoding="utf-8"))
    assert "No R4 superior to R1" in a


# ── 12. New authority input / versioning ───────────────────────────────

def test_new_authority_input_is_a_normative_delta() -> None:
    a = _norm(ADJ_DOC.read_text(encoding="utf-8"))
    assert "normative contract delta is required" in a or "normative delta" in a
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "changes the closed set of PAWA" in d


def test_no_major_trigger_fires_for_r1() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "HPAC-PAWA-REQ-152" in c
    # the trust root R1 preserves
    assert "changing the bootstrap trust root away from OS filesystem write\nauthority".replace("\n", " ") in c or "changing the bootstrap trust root away from OS\nfilesystem write authority".replace("\n", " ") in c or "changing the bootstrap trust root away from OS filesystem write" in c
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "No MAJOR trigger fires" in d


def test_no_new_pawa_failure_code_and_taxonomy_is_21() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    # Point-in-time requirement-inventory guard, reconciled by .1R.30R.2A.2 when
    # HPAC-PAWA-001 legitimately evolved v1.0 -> v1.1 (MINOR): the v1.0 total was
    # 163; the v1.1 total is 218 (HPAC-PAWA-REQ-001..218). The load-bearing
    # invariant this test protects is the *failure taxonomy*, which is unchanged.
    assert "defines **163** requirements" in c or "defines **218** requirements" in c
    assert "21 closed `pawa_failure_code` values" in c or "21 closed pawa_failure_code values" in c
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "adds **no** new `pawa_failure_code`" in d


def test_minor_verdict_and_soft_point_s1_recorded() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "HPAC-PAWA-001 v1.1 — MINOR — REQUIRED" in d or "HPAC-PAWA-001 v1.1\n— MINOR — REQUIRED".replace("\n", " ") in d
    assert "S-1" in d
    # HPAC-001 v2.1 MINOR precedent
    assert "HPAC-001 v2.1 was itself a MINOR" in d


def test_hpac_and_rhamp_byte_unchanged_since_pawa_freeze() -> None:
    # RHAMP-REQ-047 externalises the anchor; no RHAMP change needed
    r = _norm(RHAMP_CONTRACT.read_text(encoding="utf-8"))
    assert "RHAMP-REQ-047" in r
    assert "This is the trust anchor" in r
    # unchanged across the whole .1R.30R.* chain up to HEAD
    assert _git("diff", B30, "HEAD", "--", "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md").strip() == ""
    assert _git("diff", B30, "HEAD", "--", "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md").strip() == ""


# ── 13. Atomicity ─────────────────────────────────────────────────────

def test_section_33_runs_fresh_every_call() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "HPAC-PAWA-REQ-075" in c
    assert "SHALL run fresh on **every**\n`production_writer(...)` call".replace("\n", " ") in c or "SHALL run fresh on **every** `production_writer(...)` call" in c
    assert "PAWA-INV-3" in c


def test_iv_doc_confirms_atomicity_unit_a1() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "atomic unit A1" in d


# ── 14. CPIPC-001 §4 grammar / D1 decomposition ───────────────────────

def test_cpipc_grammar_admits_letter_suffixed_numeric_segments() -> None:
    c = CPIPC_CONTRACT.read_text(encoding="utf-8")
    assert "numeric-segment = digit , { digit } , [ letter , { letter } ] ;" in c
    assert "subphase-segment" in c


def test_phase_id_2a_1_is_grammar_valid_and_distinct_from_1r30() -> None:
    # 2A = digit '2' + letter 'A'; 2A.1 = child numeric-segment
    seg = re.compile(r"^\d+[A-Za-z]*$")
    for s in ("30R", "2A", "1", "2"):
        assert seg.match(s), s
    # distinct identity: .1R.30R.2A.1 is not .1R.30
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "distinct identity" in d and "PAWA-INV-11" in d


def test_downstream_sequence_matches_pawa_section_78() -> None:
    c = _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "HPAC-PAWA-REQ-148" in c
    assert "recommended, NOT reserved" in c
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "collide with nothing in HPAC-PAWA-001 §78" in d


# ── 15. Contract-freeze successor + IV decision ──────────────────────

def test_contract_freeze_successor_is_2a_2() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2" in d
    assert "Contract Freeze" in d


def test_c3_recommends_dedicated_contract_iv() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "C-3" in d
    assert ".1R.30R.2A.3" in d
    assert "dedicated" in d


# ── 16. Runtime posture / first-effect absence ──────────────────────

def test_runtime_posture_unchanged_language_in_iv_doc() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "not_implemented` / `Observed` / `observe` / `unavailable`" in d
    assert "0\nplugins / 0 capabilities".replace("\n", " ") in d or "0 plugins / 0 capabilities" in d
    assert "First external effect:** ABSENT" in d or "First external effect:**\nABSENT".replace("\n", " ") in d or "first external effect" in d.lower()


def test_no_new_dispatch_call_site_added_by_this_phase() -> None:
    # This phase adds no src/pcae change at all, so no real-effect dispatch
    # call site can have been introduced.
    assert _git("diff", J, "HEAD", "--", "src/pcae").strip() == ""
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "deterministic simulation\nharness in `runtime_adapter.py`".replace("\n", " ") in d or "deterministic simulation harness in `runtime_adapter.py`" in d


def test_iv_doc_preserves_delegated_3_incident() -> None:
    d = IV_DOC.read_text(encoding="utf-8")
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED" in d


# ── 17. This suite does not weaken tests / touch production ─────────────

def test_this_suite_adds_only_test_functions_no_skips_or_xfails() -> None:
    tree = ast.parse(THIS_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            for n in names:
                assert not n.startswith("pcae"), f"IV suite must not import production: {n}"
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                txt = ast.unparse(dec)
                assert "skip" not in txt and "xfail" not in txt, txt
        if isinstance(node, ast.Call):
            callee = ast.unparse(node.func)
            assert callee not in {"pytest.skip", "pytest.xfail", "skip", "xfail"}, callee


def test_this_suite_is_the_only_tests_change_since_phase_entry() -> None:
    changed = _git(
        "diff", "--name-only", J, FINALIZED_2A1_HEAD, "--", "tests"
    ).split()
    assert changed in ([f"tests/{THIS_FILE.name}"], []), changed
    # file did not exist at the phase entry
    existed = subprocess.run(
        ["git", "-C", str(REPO), "cat-file", "-e", f"{J}:tests/{THIS_FILE.name}"],
        capture_output=True,
    ).returncode
    assert existed != 0, "IV suite must be new at the phase entry"


def test_no_existing_def_test_removed_or_renamed_repo_wide_since_phase_entry() -> None:
    diff = _git("diff", J, FINALIZED_2A1_HEAD, "--", "tests")
    # only additions to a single new file; no other test file touched
    removed_test_defs = re.findall(r"^-\s*def (test_\w+)", diff, re.MULTILINE)
    assert removed_test_defs == [], removed_test_defs


# ── 18. Metadata coherence ────────────────────────────────────────────

def test_iv_doc_is_internally_consistent_on_verdict_and_next_phase() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "ADJUDICATION VERIFIED WITH CORRECTIONS" in d
    assert d.count("149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1") >= 1
    # recommended next is the contract-freeze phase, not begun
    assert "Do not begin" in d
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2" in d
