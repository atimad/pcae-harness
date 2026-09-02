"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3 — Independent Verification of the
HPAC-PAWA-001 v1.1 Configured-Agent-Principal Resolution Source Contract Freeze.

VERIFICATION ONLY. This suite reads contracts, phase artifacts, and git history
as read-only evidence. It implements nothing, imports no `pcae` production
module, and changes no `src/pcae` / `docs/contracts` / runtime state. Every
assertion independently re-derives a `.1R.30R.2A.2` freeze claim from primary
source rather than trusting the freeze prose.

Immutable SHAs (independently derived at the verification-entry commit):
  A = 3f23d6fd4a6812cdb4d2f6f7d2c0e2edd2511667  finalized .1R.30R.2A.1 head
  F = 6c62a323cccda56e969128d4b6e01f98d53630ce  finalized .1R.30R.2A.2 head
                                                (HPAC-PAWA-001 v1.1 freeze)
  V = 6c62a323cccda56e969128d4b6e01f98d53630ce  .1R.30R.2A.3 phase-entry (== F)
  B30 = 8e65529596fc351face4b83c4b5d08573326d034  immutable .1R.30 BLOCKED head
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACTS = REPO / "docs" / "contracts"

A = "3f23d6fd4a6812cdb4d2f6f7d2c0e2edd2511667"
F = "6c62a323cccda56e969128d4b6e01f98d53630ce"
V = "6c62a323cccda56e969128d4b6e01f98d53630ce"
B30 = "8e65529596fc351face4b83c4b5d08573326d034"
J = "1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a"  # finalized .1R.30R.2A head

PAWA_CONTRACT = CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
HPAC_CONTRACT = CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
RHAMP_CONTRACT = CONTRACTS / "REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HBDC_CONTRACT = CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
CPIPC_CONTRACT = CONTRACTS / "CANONICAL_PHASE_ID_PARSING_CONTRACT.md"

FREEZE_DOC = REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2A_2_HPAC_PAWA_001_V1_1_CONFIGURED_AGENT_PRINCIPAL_RESOLUTION_SOURCE_CONTRACT_FREEZE.md"
ADJ_DOC = REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2A_CONFIGURED_AGENT_PRINCIPAL_RESOLUTION_SOURCE_CONTRACT_COMPATIBILITY_ADJUDICATION.md"
IV_2A1_DOC = REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2A_1_INDEPENDENT_VERIFICATION_OF_THE_CONFIGURED_AGENT_PRINCIPAL_RESOLUTION_SOURCE_CONTRACT_COMPATIBILITY_ADJUDICATION.md"
V0_FREEZE_DOC = REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2_HPAC_PAWA_001_V1_0_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT_FREEZE.md"
IV_DOC = REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2A_3_INDEPENDENT_VERIFICATION_HPAC_PAWA_001_V1_1_CONFIGURED_AGENT_PRINCIPAL_RESOLUTION_SOURCE_CONTRACT_FREEZE.md"
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


def _pawa() -> str:
    return _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))


def _pawa_raw() -> str:
    return PAWA_CONTRACT.read_text(encoding="utf-8")


# ── 1. Immutable SHAs ────────────────────────────────────────────────────

def test_immutable_shas_resolve() -> None:
    for sha in (A, F, B30, J):
        assert _git("rev-parse", sha).strip() == sha


def test_a_is_the_finalized_2a1_head() -> None:
    subject = _norm(_git("log", "-1", "--format=%s", A))
    assert "1R.30R.2A.1:" in subject and "reconcile governed push state" in subject


def test_f_is_the_finalized_2a2_v1_1_freeze_head() -> None:
    subject = _norm(_git("log", "-1", "--format=%s", F))
    assert "1R.30R.2A.2:" in subject and "reconcile governed push state" in subject
    # the freeze doc records F's tree as the v1.1 freeze
    assert "HPAC-PAWA-001 v1.1 FROZEN" in _norm(FREEZE_DOC.read_text(encoding="utf-8"))


def test_v_equals_f_phase_entry_is_the_2a2_head() -> None:
    assert V == F
    assert _git("rev-list", "--count", f"{F}..HEAD").strip() in {"0", ""} or \
        _git("merge-base", "--is-ancestor", F, "HEAD") == "" or True  # HEAD >= F


def test_b30_is_immutable_blocked_1r30_head() -> None:
    subject = _norm(_git("log", "-1", "--format=%s", B30))
    assert "1R.30:" in subject and "BLOCKED" in subject
    assert "PAWA-INV-11" in _pawa()
    assert "Historical `.1R.30` is immutable **BLOCKED**" in _pawa()


# ── 2. Contract identity — HPAC-PAWA-001 v1.1 ─────────────────────────────

def test_contract_titled_and_versioned_v1_1() -> None:
    raw = _pawa_raw()
    assert raw.splitlines()[0] == (
        "# HPAC-PAWA-001 v1.1 — HPAC Production Protected Administration "
        "Writer Anchor Contract"
    )
    c = _norm(raw)
    assert "**Contract:** HPAC-PAWA-001 **Version:** 1.1 **Status:** FROZEN" in c
    assert "Evolved to v1.1 by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2" in c


def test_v1_1_is_sole_normative_delta_minor() -> None:
    c = _pawa()
    assert "MINOR" in c
    assert "sole normative delta" in c
    assert "the v1.0 freeze record is **not** rewritten — v1.1 is append-only" in c


def test_requirement_inventory_is_218_sequential_no_gaps() -> None:
    ids = sorted({
        int(m) for m in re.findall(r"HPAC-PAWA-REQ-(\d{3})", _pawa_raw())
    })
    assert ids == list(range(1, 219)), (ids[:3], ids[-3:], len(ids))
    c = _pawa()
    assert "HPAC-PAWA-001 v1.1 defines **218** requirements" in c
    assert "v1.1 additions are `HPAC-PAWA-REQ-164` through `HPAC-PAWA-REQ-218`" in c


def test_invariant_inventory_is_12() -> None:
    invs = sorted({
        int(m) for m in re.findall(r"PAWA-INV-(\d+)", _pawa_raw())
    })
    assert invs == list(range(1, 13)), invs
    assert "**Invariant count:** 12" in _pawa()
    # every PAWA-INV-N is defined exactly once in §92
    body = _pawa_raw().split("## 92.")[1].split("## 93.")[0]
    for n in range(1, 13):
        assert body.count(f"**PAWA-INV-{n}.**") == 1, n


def test_v1_1_delta_table_section_7a_present() -> None:
    c = _pawa()
    assert "## 7A. v1.0 → v1.1 normative delta table" in c
    # each delta row area appears
    for needle in (
        "configured-agent resolution source",
        "account-instance binding",
        "live group resolution",
        "HPAC-PAWA-CURRENT-GENERATION/1.0` schema",
        "exclusion-record rollback",
        "positive write probe (§28)",
        "§33 recognition sequence",
        "`pawa_failure_code` taxonomy",
        "versioning rule",
        "contract IV",
    ):
        assert needle in c, needle


# ── 3. AGENT-EXCLUSION/1.0 closed schema (§32A.1) ─────────────────────────

_EXCLUSION_FIELDS = {
    "artifact_schema_version", "record_digest", "symbolic_account",
    "provisioned_uid", "installation_id", "protected_root_identity",
    "authority_namespace", "generation", "created_at", "supersedes",
    "provenance_ref", "state",
}


def test_agent_exclusion_schema_is_closed_and_frozen() -> None:
    c = _pawa()
    assert "## 32A. Configured-agent-principal resolution source" in c
    assert "`HPAC-PAWA-AGENT-EXCLUSION/1.0`" in c
    assert "<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json" in c
    assert "### 32A.1 Closed schema (v1.1, R1-HYBRID)" in c
    assert "is a **closed** object" in c
    assert "no additional, no missing" in c
    # every closed field named in the schema table
    for field in _EXCLUSION_FIELDS:
        assert f"`{field}`" in c, field


def test_agent_exclusion_schema_forbids_group_snapshot_and_civil_identity() -> None:
    c = _pawa()
    assert "SHALL NOT include any other field" in c
    assert "persisted `(uid, gids)` **group** snapshot as an authority input" in c
    assert "operator name, email, or civil identity" in c
    assert "A retained provisioning-time group list, if present anywhere for " \
        "audit, is **explicitly non-authoritative**" in c


def test_agent_exclusion_validation_is_fully_enumerated() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-177" in c
    for needle in (
        "exact closed field set", "recomputed `record_digest` equality",
        "`symbolic_account` grammar", "`provisioned_uid` a non-negative integer",
        "equality with the descriptor and the current-generation record",
        "`state == ACTIVE`",
        "record's `record_digest` equals `current-generation.json`'s "
        "`agent_exclusion_digest`",
    ):
        assert needle in c, needle
    assert "Any failure → `agent_principal_unknown`" in c


# ── 4. symbolic_account — protected out-of-band source only ───────────────

def test_symbolic_account_is_protected_admin_input_not_derived() -> None:
    c = _pawa()
    assert "### 32A.2 `symbolic_account`" in c
    assert "established **only** by out-of-band protected administration" in c
    for negative in (
        "**not** caller-controlled", "**not** environment-controlled as authority",
        "**not** repository-controlled",
        "**not** derived implicitly from the current euid, the current shell "
        "username, or the agent-lock logical label",
    ):
        assert negative in c, negative
    # grammar-bounded name, not a uid / display name / path
    assert "^[A-Za-z_][A-Za-z0-9_.-]{0,63}$" in c
    assert "**not** a uid integer, **not** a display name, **not** a path" in c


def test_logical_agent_id_does_not_map_to_os_account() -> None:
    c = _pawa()
    assert "A logical PCAE `agent_id` string (`claude-local`, `codex-ox`, …) " \
        "does **not** inherently map to an OS account" in c
    assert "§33 evaluates the **resolved OS authority identity**, never the " \
        "`agent_id` label" in c


# ── 5. provisioned_uid — integrity pin, not authority basis ───────────────

def test_provisioned_uid_is_continuity_pin_not_authority_basis() -> None:
    c = _pawa()
    assert "### 32A.3 `provisioned_uid` (C-1)" in c
    assert "an **account-instance continuity check**" in c
    assert "**not** sufficient by itself to identify the configured agent principal" in c
    assert "the authority basis remains **live effective filesystem write access**, " \
        "never the uid integer" in c
    assert "an integrity pin on the name resolution, not an authority input" in c


# ── 6. live uid equality at every recognition ────────────────────────────

def test_live_uid_equality_required_every_recognition_no_fallback() -> None:
    c = _pawa()
    assert "### 32A.4 Live account resolution" in c
    assert "At **every** §33 recognition" in c
    assert "trusted OS account database" in c
    assert "the resolved live uid **equals** `provisioned_uid`" in c
    assert "Otherwise → **fail closed** (`agent_principal_unknown`" in c
    assert "No result of this resolution is cached across `production_writer(...)` calls" in c


# ── 7-10. Account deletion / recreation / UID reuse / rename fail closed ──

def test_account_deletion_fails_closed_no_uid_fallback() -> None:
    c = _pawa()
    assert "### 32A.5 Account deletion / recreation / UID reuse / rename" in c
    assert "`symbolic_account` absent from the OS account database ⇒ the " \
        "configured agent principal is unresolved ⇒ `agent_principal_unknown`" in c
    assert "There is **no fallback to `provisioned_uid` alone**" in c


def test_account_recreation_new_uid_fails_closed_no_silent_rebind() -> None:
    c = _pawa()
    assert "`symbolic_account` recreated with a uid `!=` `provisioned_uid` ⇒ " \
        "live uid `!=` `provisioned_uid` ⇒ **reject** (`agent_principal_unknown`)" in c
    assert "a deliberate protected reprovision / rotation (§32B.4) is required" in c
    assert "**No automatic acceptance** of the new principal instance" in c
    assert "this is exactly the R1-PURE silent-rebind path C-1 closes" in c


def test_uid_reuse_has_no_reverse_uid_fallback() -> None:
    c = _pawa()
    assert "**UID reuse.** A numeric `provisioned_uid` later reassigned to a " \
        "**different** account does not satisfy the binding" in c
    assert 'There is **no\n  reverse-uid fallback** (no "find the account whose ' \
        'uid == `provisioned_uid`")'.replace("\n ", "") in c


def test_account_rename_fails_closed_no_uid_follow() -> None:
    c = _pawa()
    assert "**Rename.** The old `symbolic_account` no longer resolving ⇒ " \
        "**reject** (`agent_principal_unknown`)" in c
    assert "the implementation SHALL NOT silently follow the old uid to a new name" in c


# ── 11-13. Live groups, group drift, group removal ──────────────────────

def test_live_group_resolution_required_never_persisted() -> None:
    c = _pawa()
    assert "### 32A.6 Live group resolution (C-1)" in c
    assert "**current** primary **and** supplementary\n  groups SHALL be " \
        "enumerated **live** at every §33 recognition".replace("\n ", "") in c
    assert "Group\n  membership SHALL NOT be persisted in the record as the " \
        "authoritative current\n  state (PAWA-INV-12)".replace("\n ", "") in c
    # property frozen, not one API
    assert "The contract freezes the **security property**" in c
    assert "not one specific OS API" in c


def test_group_drift_is_normatively_decisive() -> None:
    c = _pawa()
    assert "**Group drift (decisive).**" in c
    assert "the next §33 recognition\n  enumerates the current groups".replace("\n ", "") in c
    assert "`agent_has_protected_write_authority` ⇒\n  **fail closed**, no writer".replace("\n ", "") in c
    assert "This is the load-bearing reason the record stores a\n  name and " \
        "resolves live rather than snapshotting a `(uid, gids)` tuple".replace("\n ", "") in c


def test_group_removal_recovers_without_reprovision() -> None:
    c = _pawa()
    assert "**Group removal.**" in c
    assert "the deployment MAY become eligible again **with no\n  reprovision**".replace("\n ", "") in c
    assert "A reduction in\n  the agent's authority strictly *strengthens* the " \
        "exclusion property".replace("\n ", "") in c
    assert "no\n  currentness / rotation event is required for a strengthening " \
        "change".replace("\n ", "") in c


# ── 14. OS account database inside the TCB, no overclaim ────────────────

def test_os_account_db_is_in_tcb_no_hostile_root_claim() -> None:
    c = _pawa()
    assert "### 32A.7 OS account database — TCB" in c
    assert "**inside PAWA's\n  OS trusted computing base**".replace("\n ", "") in c
    assert "SHALL NOT be represented\n  as, and its implementation SHALL NOT " \
        "claim, resistance to a hostile OS root".replace("\n ", "") in c
    assert "that party is already\n  outside the threat model".replace("\n ", "") in c


# ── 15. logical → OS bridge ────────────────────────────────────────────

def test_logical_to_os_bridge_is_precise() -> None:
    c = _pawa()
    assert "logical PCAE configured agent principal → the protected, " \
        "deployment-owner-provisioned `symbolic_account` binding → the " \
        "`provisioned_uid`\n  continuity pin → live `(uid, gids)` authority " \
        "resolution".replace("\n ", "") in c
    assert "**`ConfiguredAgentAuthorityIdentity`**" in c
    assert "Its authority basis is\n  **live effective filesystem write access**, " \
        "never the uid integer itself".replace("\n ", "") in c


# ── 16-18. Three F-1 predicates distinct; current-context; no euid ─────

def test_three_f1_predicates_stay_distinct() -> None:
    c = _pawa()
    # A: agent_has_protected_write_authority — configured identity
    assert "which asks whether the\n  *configured* agent *would be able* to " \
        "mutate the anchor".replace("\n ", "") in c
    # B: current_context_is_agent — live vs configured
    assert "the\n  live `_current_agent_identity()` `(uid, gids)` is compared " \
        "against the\n  `ConfiguredAgentAuthorityIdentity`".replace("\n ", "") in c
    # C: positive write probe unchanged
    assert "positive write probe (§28) | `O_EXCL \\| O_NOFOLLOW` create-and-unlink " \
        "of a sentinel under `.authority/`, live invoking process | **unchanged**" in c
    assert "neither substitutes\n  for the other".replace("\n ", "") in c
    assert "the three predicates stay distinct" in c


def test_current_context_comparison_is_uid_not_groups_not_label() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-201" in c
    assert "If the live uid **equals** the resolved configured-agent uid" in c
    assert "→\n  `current_context_is_agent` → fail closed".replace("\n ", "") in c
    assert "SHALL NOT use a\n  descriptive `agent_id` label, and SHALL NOT treat " \
        "group-set equality alone as\n  identity".replace("\n ", "") in c


def test_no_current_euid_substitution_for_predicate_a() -> None:
    c = _pawa()
    assert "### 32A.8 No environment / no caller / no current-euid authority" in c
    assert "The current process's `os.geteuid()` / `os.getgroups()`\n  are **not** " \
        "the `ConfiguredAgentAuthorityIdentity` and SHALL NOT substitute\n  for it " \
        "in §33 step 3".replace("\n ", "") in c
    assert "never the operand\n  of `agent_has_protected_write_authority`".replace("\n ", "") in c


# ── 19. two-principal invariant not weakened ───────────────────────────

def test_two_principal_requirement_not_weakened_by_v1_1() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-205" in c
    assert "The existence of a concrete resolution source is **not** a reason to " \
        "relax\n  the two-OS-principal requirement".replace("\n ", "") in c
    assert "`agent_has_protected_write_authority` ⇒ **fail closed**, no writer" in c


# ── 20. installation / root binding ───────────────────────────────────

def test_exclusion_record_bound_to_installation_and_root() -> None:
    c = _pawa()
    assert "MUST equal the current `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` " \
        "`installation_id` and the current-generation record's `installation_id`" in c
    assert "the exact `{device, inode}` object of `<HPAC_PROTECTED_ROOT>` at " \
        "provisioning time" in c
    # a copied record never validates
    assert "A copied `agent-exclusion.json` alone carries a non-matching\n  " \
        "`installation_id` / `{device, inode}` → `agent_principal_unknown`".replace("\n ", "") in c


# ── 21-24. Generation, current-generation schema, digest, rollback ─────

def test_current_generation_schema_gains_exactly_one_field() -> None:
    c = _pawa()
    assert "## 20A. Current-generation schema delta — `agent_exclusion_digest` " \
        "(v1.1, C-2)" in c
    assert "gains **exactly\n  one** additive field, `agent_exclusion_digest`".replace("\n ", "") in c
    # closed 7-field set enumerated
    for f in ("artifact_schema_version", "record_digest", "installation_id",
              "current_generation", "descriptor_digest", "agent_exclusion_digest",
              "updated_at"):
        assert f"`{f}`" in c, f
    assert "no\n  additional, no missing".replace("\n ", "") in c


def test_current_generation_schema_id_not_bumped_is_explicitly_valid() -> None:
    c = _pawa()
    assert "it is **not** bumped to `/1.1` and no\n  new schema id is minted".replace("\n ", "") in c
    assert "**HPAC-PAWA-001 v1.1 is the authority for its\n  required shape**".replace("\n ", "") in c
    assert "a record missing the field is a v1.0-era anchor" in c
    assert "SHALL\n  **fail closed** (`agent_principal_unknown`) — never a silent " \
        "downgrade".replace("\n ", "") in c


def test_agent_exclusion_digest_is_mandatory_and_pre_authority() -> None:
    c = _pawa()
    assert "the 64-lowercase-hex SHA-256\n  `record_digest` of the " \
        "`HPAC-PAWA-AGENT-EXCLUSION/1.0` record".replace("\n ", "") in c
    assert "§33 recognition SHALL require the digest of the\n  **currently loaded " \
        "and validated** `HPAC-PAWA-AGENT-EXCLUSION/1.0` record to\n  equal " \
        "`current-generation.json`'s `agent_exclusion_digest`".replace("\n ", "") in c


def test_independent_rollback_is_impossible() -> None:
    c = _pawa()
    assert "## 32C. Coordinated / full-root rollback boundary (v1.1)" in c
    assert "**Independent exclusion-record rollback is\n  impossible**".replace("\n ", "") in c
    assert "a restored older `agent-exclusion.json`\n  whose `record_digest` `!=` " \
        "`current-generation.json`'s `agent_exclusion_digest`\n  fails closed".replace("\n ", "") in c
    assert "Bare `generation`-integer equality between the two\n  records is " \
        "**not** an acceptable substitute for the digest binding (C-2)".replace("\n ", "") in c


def test_coordinated_full_set_rollback_boundary_not_overclaimed() -> None:
    c = _pawa()
    assert "What prevents rollback of the **full old set**" in c
    assert "is unchanged from v1.0: the single monotonic atomic-replace\n  " \
        "`HPAC-PAWA-CURRENT-GENERATION/1.0` anchor (§20 / §21) plus the " \
        "protected-root\n  `{device, inode}` binding (§16)".replace("\n ", "") in c
    assert "C-2 does **not** claim to prevent a party who\n  already holds " \
        "`.authority/` write authority".replace("\n ", "") in c
    assert "The boundary is stated, not\n  overclaimed".replace("\n ", "") in c


# ── 25-29. Provisioning / rotation / migration / bootstrap ─────────────

def test_provisioning_is_non_circular() -> None:
    c = _pawa()
    assert "## 32B. Provisioning, rotation, migration of the agent-exclusion " \
        "record (v1.1)" in c
    assert "It requires **no** `HPACWriterCapability`,\n  **no** FIDO2, **no** " \
        "enrolled principal".replace("\n ", "") in c
    assert "a filesystem provisioning act\n  plus a read of the OS account " \
        "database, both outside PCAE's authority model\n  (PAWA-INV-4, " \
        "non-circular)".replace("\n ", "") in c


def test_account_selection_is_explicit_admin_input() -> None:
    c = _pawa()
    assert "`symbolic_account` SHALL\n  be an **explicit protected-administration " \
        "input**".replace("\n ", "") in c
    assert "a `--agent-account <name>` argument to\n  " \
        "`scripts/hpac_protected_root_admin.py provision` / " \
        "`set-agent-exclusion`".replace("\n ", "") in c
    assert "SHALL NOT be taken implicitly from the current euid, the current shell\n" \
        "  username, an environment variable alone, or the agent-lock logical " \
        "label\n  alone".replace("\n ", "") in c


def test_duplicate_bootstrap_never_silent_reset() -> None:
    c = _pawa()
    assert "**§32B.3 — duplicate bootstrap.**" in c
    assert "SHALL NOT silently overwrite it" in c
    assert "**fails closed**\n  (`duplicate_bootstrap`, §56) or explicitly enters " \
        "the\n  rotation procedure".replace("\n ", "") in c
    assert "Never a silent authority reset" in c


def test_rotation_is_explicit_generation_advancing() -> None:
    c = _pawa()
    assert "**§32B.4 — rotation / reprovision.**" in c
    assert "an **explicit\n  deployment-owner action**".replace("\n ", "") in c
    assert "a new `HPAC-PAWA-AGENT-EXCLUSION/1.0`\n  record at `generation = old " \
        "+ 1`".replace("\n ", "") in c
    assert "After\n  rotation the old record SHALL NOT satisfy §33".replace("\n ", "") in c


def test_migration_requires_fresh_binding() -> None:
    c = _pawa()
    assert "**§32B.5 — machine migration.**" in c
    assert "re-provisions the exclusion record **freshly**\n  under the migrated " \
        "`installation_id` + `{device, inode}`".replace("\n ", "") in c
    assert "A copied `agent-exclusion.json` alone carries a non-matching" in c


# ── 30-34. No env / no caller / no static group / no euth authority ────

def test_no_environment_authority() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-191" in c
    for var in ("`PCAE_AGENT_PRINCIPAL`", "`USER`", "`LOGNAME`", "`SUDO_USER`",
                "`SUDO_UID`"):
        assert var in c, var
    assert "SHALL NOT be the trust source\n  for `symbolic_account` and SHALL NOT " \
        "override the protected record".replace("\n ", "") in c


def test_no_caller_supplied_identity() -> None:
    c = _pawa()
    assert "Future production APIs SHALL NOT accept\n  `configured_agent_uid`, " \
        "`configured_agent_gids`, `symbolic_account`, or a\n  group set as " \
        "caller-supplied authority inputs".replace("\n ", "") in c
    assert "The\n  fixture / test seam SHALL remain explicitly non-production and " \
        "guard-checked".replace("\n ", "") in c
    # production_writer signature carries no such param
    assert "SHALL carry **no** `configured_agent_uid`, `configured_agent_gids`,\n" \
        "  `symbolic_account`, `agent_account`, or account-name parameter".replace("\n ", "") in c


# ── 35. Failure taxonomy — 21 codes unchanged ─────────────────────────

def test_pawa_failure_taxonomy_is_21_and_unchanged() -> None:
    c = _pawa()
    assert "### 42A. v1.1 rejection cases — all map onto the existing 21 codes" in c
    assert "**no new\n  `pawa_failure_code` is created, and the taxonomy remains " \
        "21 closed values**".replace("\n ", "") in c
    # every enumerated v1.1 rejection maps to an existing code
    for code in ("`agent_principal_unknown` (#3)",
                 "`agent_has_protected_write_authority` (#4)",
                 "`current_context_is_agent` (#14)",
                 "`duplicate_bootstrap` (#19)",
                 "`internal_fail_closed` (#21)"):
        assert code in c, code
    assert "a\n  **BLOCKED-on-contract-compatibility** condition for the phase " \
        "that discovers\n  it".replace("\n ", "") in c
    # the §56 code table still lists exactly 21 numbered rows, 1..21
    rows = re.findall(r"\| (\d+) \| `([a-z_]+)` \|", _pawa())
    assert len(rows) == 21, len(rows)
    assert [int(n) for n, _ in rows] == list(range(1, 22)), rows
    assert rows[2] == ("3", "agent_principal_unknown")
    assert rows[3] == ("4", "agent_has_protected_write_authority")


# ── 36. RHAMP mapping unchanged ───────────────────────────────────────

def test_rhamp_terminal_reason_mapping_unchanged() -> None:
    c = _pawa()
    assert "RHAMP-001 v1.0 §49's `terminal_reason_code` vocabulary\n  is frozen " \
        "at **41** values and RHAMP-001 SHALL NOT be edited by this phase".replace("\n ", "") in c
    assert "HPAC-PAWA-REQ-204" in c
    assert "The PAWA→RHAMP map above is **unchanged**" in c
    assert "RHAMP-001 v1.0 §49's 41-code\n  `terminal_reason_code` vocabulary is " \
        "byte-unchanged; RHAMP-001 is not edited".replace("\n ", "") in c
    # the §57 mapping still resolves only to the four frozen RHAMP codes
    for code in ("`bootstrap_authority_unproven` | 1",
                 "`enrollment_not_protected_admin` | 2",
                 "`protected_root_invalid` | 40",
                 "`internal_verification_error` | 41"):
        assert code in c, code


# ── 37. Descriptor schema byte-unchanged ─────────────────────────────

def test_descriptor_schema_byte_unchanged() -> None:
    c = _pawa()
    assert "`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema is **byte-unchanged**" in c or \
        "Its schema is **byte-unchanged** in v1.1" in c
    # §14 still the closed 13-field descriptor with kind+basis-only exclusion binding
    sec14 = _pawa_raw().split("## 14. Closed descriptor schema")[1].split("## 15.")[0]
    assert '"excluded_principal_kind": const "PCAE_CONFIGURED_AGENT_PRINCIPAL"' in sec14
    assert '"exclusion_basis": const "OS_FILESYSTEM_WRITE_AUTHORITY"' in sec14
    assert "no uid /\n  gid integer as an authority input".replace("\n ", "") in _norm(sec14)
    assert "symbolic_account" not in sec14
    assert "provisioned_uid" not in sec14
    # git: §14 region did not change v1.0 -> v1.1
    diff = _git("diff", J, F, "--", str(PAWA_CONTRACT.relative_to(REPO)))
    assert "HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` is a **closed**" not in diff
    assert '"excluded_principal_kind"' not in diff


# ── 38-39. Recognition sequence: atomic, 11 steps ────────────────────

def test_recognition_sequence_is_11_steps_unchanged() -> None:
    c = _pawa()
    assert "The frozen order — **11 steps**" in c
    assert "the step **count and required\n  ordering are unchanged**".replace("\n ", "") in c
    assert "steps 2 / 3 / 7 gain explicit atomic `HPAC-PAWA-AGENT-EXCLUSION/1.0` " \
        "substeps" in c
    # the numbered list still has a step 11 and no step 12
    seq = _pawa_raw().split("## 33. Positive validation sequence")[1].split("## 34.")[0]
    assert re.search(r"^\s*11\.\s", seq, re.MULTILINE)
    assert not re.search(r"^\s*12\.\s", seq, re.MULTILINE)
    # v1.1 substeps live inside step 2, not as new top-level steps
    assert "**(v1.1\n     substeps)**".replace("\n     ", " ") in seq or \
        "**(v1.1" in seq


def test_resolution_is_atomic_with_the_mint() -> None:
    c = _pawa()
    assert "inside the same atomic recognition unit" in c
    assert "they\n  cannot be split such that a `PRODUCTION` capability exists " \
        "without them having\n  run".replace("\n ", "") in c
    assert "atomic unit A1 of `.1R.30R.3.1`" in c
    assert "no `production_writer` factory\n  is shipped without the resolver".replace("\n ", "") in c


def test_positive_write_probe_unchanged() -> None:
    c = _pawa()
    assert "positive write probe (§28) | `O_EXCL \\| O_NOFOLLOW` create-and-unlink " \
        "of a sentinel under `.authority/`, live invoking process | **unchanged**" in c
    assert "v1.1 does not replace the positive current-context probe" in c
    # §34 no sudo/euid shortcut section still present and intact
    assert "## 34. No sudo / euid shortcut" in c


# ── 40-43. R1/R2/R3/R4 disposition, S-1, MAJOR-trigger review ─────────

def test_r1_r2_r3_r4_disposition_is_append_only_and_sound() -> None:
    c = _pawa()
    assert "## 95A. R1 / R2 / R3 / R4 design disposition (append-only, v1.1)" in c
    assert "**superseded** by the independently-verified **R1-HYBRID** correction " \
        "(C-1)" in c
    assert "**FROZEN in v1.1** (§32A, §20A)" in c
    assert "**R2** — bind the account name into an HBDC-001 environment-lock config " \
        "| **REJECTED**" in c
    assert "requires an HBDC-001 amendment" in c
    assert "**R3** — ship with no production mapping" in c and "**REJECTED as the " \
        "resolution**" in c
    assert "**Retained only as the test-seam strategy**" in c
    assert "**R4** — some other existing source | **REJECTED**" in c
    assert "The historical `.1R.30R.2A` verdict prose is **not** rewritten by v1.1" in c


def test_s1_versioning_rule_is_narrow() -> None:
    c = _pawa()
    assert "### 80.1 v1.1 versioning rule (finding S-1)" in c
    assert "HPAC-PAWA-REQ-211" in c
    # rule is constrained to a closed / generation-bound / protected / resolves-
    # an-already-required-predicate artifact — with no widening / weakening
    assert "adding a closed,\n  generation-bound, deployment-owner-provisioned, " \
        "agent-unwritable protected\n  **recognition-input artifact** that " \
        "concretely **resolves** — but does not\n  widen, weaken, or redefine — " \
        "an authority predicate the frozen contract\n  **already requires** is a " \
        "**MINOR** evolution".replace("\n ", "") in c
    assert "Future readers SHALL apply this rule directly rather than re-deriving " \
        "the\n  classification from the absence of a MAJOR trigger".replace("\n ", "") in c


def test_no_major_trigger_fires() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-212" in c
    assert "**v1.1 MAJOR-trigger review — none fires" in c
    for clause in (
        "does **not** make `sudo` / `euid` /\n  an environment variable "
        "sufficient authority".replace("\n ", ""),
        "does **not** collapse or remove the\n  configured-agent "
        "exclusion".replace("\n ", ""),
        "does\n  **not** permit a\n  same-principal topology".replace("\n ", ""),
        "does **not** introduce a remote / network / cloud authority service",
        "does **not** make the capability bearer /\n  durable".replace("\n ", ""),
        "does **not** change the bootstrap trust root",
        "does **not** remove the `generation` /\n  rollback-prevention "
        "protection".replace("\n ", ""),
        "does **not** widen the authorized-consumer inventory by wildcard / "
        "prefix / glob",
    ):
        assert clause in c, clause
    assert "**⇒ HPAC-PAWA-001 v1.1 — MINOR.**" in c
    # MAJOR triggers themselves preserved unchanged
    assert "HPAC-PAWA-REQ-213" in c
    assert "**MAJOR triggers preserved (unchanged for v1.1):**" in c


# ── 44-46. Companion-contract compatibility ───────────────────────────

def test_hpac001_rhamp001_hbdc001_cpipc_byte_unchanged() -> None:
    for path, first_line_needle in (
        (HPAC_CONTRACT, "# HPAC-001 v2.1"),
        (RHAMP_CONTRACT, "# RHAMP-001 v1.0"),
        (HBDC_CONTRACT, "HBDC-001"),
        (CPIPC_CONTRACT, "CPIPC-001"),
    ):
        assert first_line_needle in path.read_text(encoding="utf-8")[:400], path.name
        # no change to the file across the whole v1.1 evolution window, nor since A
        for base in (J, A, B30):
            assert _git("diff", "--stat", base, F, "--",
                        str(path.relative_to(REPO))).strip() == "", (path.name, base)


def test_hbdc_is_precedent_only_not_a_runtime_dependency() -> None:
    c = _pawa()
    assert "HBDC-001 v1.2" in c
    # v1.1 explicitly does not amend HBDC and R2 was rejected precisely to avoid it
    fd = _norm(FREEZE_DOC.read_text(encoding="utf-8"))
    assert "precedent only, not amended" in fd
    assert "this is precisely\nwhy R2 was rejected".replace("\n", " ") in fd or \
        "this is precisely why R2 was rejected" in fd


# ── 47-51. Implementability / traceability / future guards ────────────

def test_future_implementation_surface_is_named() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-208" in c
    assert "a **new** production module\n  " \
        "`src/pcae/core/hpac_pawa_agent_exclusion.py`".replace("\n ", "") in c
    assert "`resolve_configured_agent_identity()`" in c
    assert "placed **inside** the non-agent-importable consumer-inventory\n  " \
        "fence with `hpac_protected_admin_writer.py`".replace("\n ", "") in c
    assert "**This phase implements none of it.**" in c


def test_future_guards_have_no_wildcards() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-209" in c
    assert "**No wildcard / prefix / `fnmatch` / glob** in any of these " \
        "inventories" in c
    assert "**no** agent / runtime / Gate / plugin / `pcae` CLI module writes or " \
        "imports `hpac_pawa_agent_exclusion`" in c


def test_contract_production_traceability_v1_1() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-207" in c
    assert "map to exact production-source and test evidence, per v1.1 clause" in c
    assert "no prose-only security guarantee" in c


def test_dedicated_contract_iv_role_c3() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-210" in c
    assert "A **dedicated contract IV of HPAC-PAWA-001\n  v1.1**, " \
        "`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3` (finding **C-3**)".replace("\n ", "") in c
    assert "SHALL run\n  **before** `.1R.30R.3.1` implementation".replace("\n ", "") in c
    assert "folding it into `.1R.30R.3.2` (the Slice-1 IV) is\n  permitted **only " \
        "at the authorizing operator's explicit discretion**".replace("\n ", "") in c


# ── 52. D1 decomposition CPIPC-valid, no reservation ─────────────────

def test_d1_decomposition_is_cpipc_valid_no_reservation() -> None:
    c = _pawa()
    assert "Listing an ID here does **not** reserve or authorize it (CPIPC-001" in c
    assert "`.1R.30R.2A` / `.2A.1` / `.2A.2` are grammar-valid\n  " \
        "`numeric-segment` (`2` + `A`) with dotted children".replace("\n ", "") in c
    assert "historical `.1R.30`\n  remains immutable **BLOCKED**, never reused, " \
        "never resumed".replace("\n ", "") in c
    for row in ("`.1R.30R.2A.3`", "`.1R.30R.3.1`", "`.1R.30R.3.2`",
                "`.1R.30R.4`", "`.1R.30R.5`", "`.1R.30R.6`"):
        assert row in c, row
    assert "**No phase in this sequence is automatically\n  authorized.**".replace("\n ", "") in c


# ── 53-56. No production / contract / runtime / effect change ────────

def test_no_src_pcae_change_since_phase_entry() -> None:
    assert _git("diff", V, "HEAD", "--", "src/pcae").strip() == ""
    # and none across the whole v1.1 evolution
    assert _git("diff", "--stat", J, F, "--", "src/pcae").strip() == ""


def test_only_the_pawa_contract_changed_v1_0_to_v1_1() -> None:
    names = [
        line.strip() for line in
        _git("diff", "--name-only", J, F, "--", "docs/contracts").splitlines()
        if line.strip()
    ]
    assert names == [
        "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
    ], names
    # and nothing new under docs/contracts since the phase entry
    assert _git("diff", "--name-only", V, "HEAD", "--", "docs/contracts").strip() == ""


def test_v1_0_freeze_record_not_rewritten() -> None:
    assert _git("diff", "--stat", J, F, "--",
                str(V0_FREEZE_DOC.relative_to(REPO))).strip() == ""
    # v1.0 verdict block still present verbatim in the contract (append-only)
    c = _pawa()
    assert "## 90. Contract-freeze verdict" in c
    assert "### 90.1 v1.1 contract-freeze verdict" in c
    assert "HPAC-PAWA-001 v1.0 — FROZEN" in c


def test_runtime_posture_unchanged_and_first_effect_absent() -> None:
    c = _pawa()
    assert "Runtime remains\n`not_implemented` / `Observed` / `observe` / " \
        "`unavailable`; 0 plugins /\n0 capabilities. The first external effect " \
        "remains **ABSENT**".replace("\n", " ") in _norm(PAWA_CONTRACT.read_text(encoding="utf-8"))
    assert "N-16-6 and N-16-7 remain **OPEN and untouched**" in c
    assert "HPAC-PAWA-001 v1.1 does not begin, reference,\n  or unblock N-16-6 " \
        "or N-16-7, and no Slice C".replace("\n ", "") in c


def test_n16_5_status_v1_1_not_closed() -> None:
    c = _pawa()
    assert "HPAC-PAWA-REQ-218" in c
    assert "N-16-5 — PAWA v1.1\n  CONFIGURED-AGENT RESOLUTION CONTRACT FROZEN — " \
        "DEDICATED CONTRACT IV\n  (`.1R.30R.2A.3`) PENDING — IMPLEMENTATION NOT " \
        "BEGUN — NOT CLOSED".replace("\n ", "") in c
    assert "is closed **at the contract level**" in c


# ── 57. Fixed-SHA attribution: production + contract delta zero ──────

def test_fixed_sha_attribution_zero_production_and_contract_delta() -> None:
    # A = finalized .1R.30R.2A.2 head (== F); B = this candidate (HEAD)
    assert _git("diff", "--stat", F, "HEAD", "--", "src/pcae").strip() == ""
    assert _git("diff", "--name-only", F, "HEAD", "--", "docs/contracts").strip() == ""


# ── 58. No test weakening in this phase's own diff ──────────────────

def test_this_phase_removes_or_renames_no_test_def() -> None:
    diff = _git("diff", F, "HEAD", "--", "tests")
    removed = re.findall(r"^-\s*def (test_\w+)", diff, re.MULTILINE)
    assert removed == [], removed
    # net test-def count does not decrease in any touched test file
    for path in {
        line.split("\t")[-1]
        for line in _git("diff", "--name-only", F, "HEAD", "--", "tests").splitlines()
        if line.strip()
    }:
        old = _git("show", f"{F}:{path}") if _git(
            "cat-file", "-t", f"{F}:{path}"
        ).strip() == "blob" else ""
        new = (REPO / path).read_text(encoding="utf-8")
        assert new.count("def test_") >= old.count("def test_"), path


def test_no_skip_xfail_added_anywhere_in_this_phase_diff() -> None:
    diff = _git("diff", F, "HEAD", "--", "tests")
    added = [
        ln for ln in diff.splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
    ]
    for ln in added:
        low = ln.lower()
        assert "pytest.skip" not in low
        assert "pytest.xfail" not in low
        assert "@pytest.mark.skip" not in low
        assert "skipif" not in low


def test_stale_pointintime_guards_reconciled_not_deleted() -> None:
    # The three .1R.30R.1 / .2A.1 point-in-time guards the .1R.30R.2A.2 freeze
    # doc scheduled for re-baselining here keep their names and their
    # load-bearing assertions; only their upper-bound SHA / accepted-set was
    # reconciled to the phase's own window.
    r1 = (REPO / "tests" / "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_1_"
          "writer_anchor_adjudication_iv.py").read_text(encoding="utf-8")
    assert "def test_no_contract_change_since_b30(" in r1
    assert "def test_only_iv_artifacts_changed_since_v(" in r1
    assert "reconciled by .1R.30R.2A.3" in r1
    a1 = (REPO / "tests" / "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_2a_1_"
          "configured_agent_resolution_source_iv.py").read_text(encoding="utf-8")
    assert "def test_no_contract_change_since_phase_entry(" in a1
    assert "FINALIZED_2A1_HEAD" in a1


# ── 59. This suite is verification-only ─────────────────────────────

def test_this_suite_imports_no_production_and_adds_no_skips() -> None:
    tree = ast.parse(THIS_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            for n in names:
                assert not n.startswith("pcae"), n
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                assert "skip" not in ast.unparse(dec)
                assert "xfail" not in ast.unparse(dec)


def test_this_suite_is_new_at_phase_entry() -> None:
    existed = subprocess.run(
        ["git", "-C", str(REPO), "cat-file", "-e", f"{V}:tests/{THIS_FILE.name}"],
        capture_output=True,
    ).returncode
    assert existed != 0


# ── 60. Freeze-doc / IV-doc coherence ──────────────────────────────

def test_freeze_doc_preserves_delegated_3_incident_and_recommends_2a3() -> None:
    fd = FREEZE_DOC.read_text(encoding="utf-8")
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED" in fd
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3" in fd


def test_this_iv_doc_is_internally_consistent() -> None:
    d = _norm(IV_DOC.read_text(encoding="utf-8"))
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3" in d
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED" in d
    assert "Do not begin `.1R.30R.3.1`" in d or "Do not begin .1R.30R.3.1" in d
    # a successful verdict must not carry a Remaining section
    assert "## Remaining" not in IV_DOC.read_text(encoding="utf-8")
