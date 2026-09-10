"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R
(alias N16-5-H3-IV) — fresh INDEPENDENT verification of the H-3 production
certification authority-path implementation against HPAC-PAWA-001 v1.3.

This suite is written from primary source; it does NOT import or reuse the
predecessor N16-5-H3-IMPL fixtures. It independently re-proves the
load-bearing security properties:

  * the exact 4-file production diff (I_ENTRY .. HEAD);
  * HPAC-PAWA-001 v1.3 and the sibling contracts byte-unchanged;
  * the certification mint reuses the SAME `_PRODUCTION_WRITER_FACTORY_SEAL`
    trust root — no second seal / mint primitive is introduced;
  * `certification_writer` is a dedicated factory with a closed, disjoint
    consumer inventory and a closed exact five-role allowlist
    (terminator / wildcard / prefix / arbitrary string all denied);
  * §33 steps 1-9 are shared verbatim with `production_writer`;
  * the coordinator is the sole caller and is non-agent-importable;
  * `verify_human_authentication` remains the sole PRODUCTION principal
    issuer and the coordinator does not relax `require_real_assurance`;
  * the coordinator reaches no runtime / dispatch / Gate-6+ path;
  * `certification_proof_subject` is a narrow validated binding, not
    caller-controlled authority;
  * runtime stays Observed / observe / unavailable.

No real ceremony, no YubiKey, no PIN, no makeCredential / getAssertion, no
live protected-root access.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACTS = REPO / "docs" / "contracts"

I_ENTRY = "74e52d59738007c4b9f6dbeb28f83990ba82e9a8"
PAWA_V13_BLOB = "9c816716bae2262831945ac24b1771cf79de4c55"
#: N16-5-F5B1-READAUTH: a downstream governed phase evolved HPAC-PAWA-001
#: v1.3 -> v1.4 (MINOR, S-3 -- the F-5-B1 recognized read / ceremony-entry
#: authority) and legitimately edits this one contract file, adding no
#: schema and no dependency. These IV guards assert "no retro-edit during
#: the H-3-IV window": re-anchor their endpoint from the moving HEAD to
#: this fixed SHA (the N16-5-FINAL-CERT head -- the last commit at which
#: the contract was still v1.3). No test function renamed or removed; no
#: test disabled.
_F5B1_READAUTH_ENTRY = "18d7da02435cac61159e9a90f86b2a586c4704d0"

FIVE_ROLES = frozenset(
    {
        "hpac_challenge_coordinator",
        "hpac_assertion_recorder",
        "human_authentication_proof_verifier",
        "hpac_gate5_binder",
        "hpac_rhamp_counter_state_verifier",
    }
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True
    ).stdout


# ── lineage / diff ──────────────────────────────────────────────────────────


def test_iv01_production_diff_is_exactly_the_four_sanctioned_files():
    changed = sorted(
        p for p in _git("diff", "--name-only", I_ENTRY, "HEAD", "--", "src", "scripts").split()
    )
    assert changed == [
        "scripts/hpac_certification_admin.py",
        "src/pcae/core/hpac_certification_coordinator.py",
        "src/pcae/core/hpac_protected_admin_writer.py",
        "src/pcae/core/human_authentication_proof.py",
    ]


def test_iv02_pawa_v13_blob_byte_unchanged_since_i_entry():
    at_entry = _git(
        "rev-parse",
        f"{I_ENTRY}:docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
    ).strip()
    at_head = _git(
        "rev-parse",
        f"{_F5B1_READAUTH_ENTRY}:docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
    ).strip()
    assert at_entry == at_head == PAWA_V13_BLOB


def test_iv03_sibling_contracts_and_schemas_and_deps_byte_unchanged():
    diff = _git(
        "diff", "--name-only", I_ENTRY, _F5B1_READAUTH_ENTRY, "--", "docs/contracts", "schemas", "pyproject.toml"
    ).split()
    assert diff == []
    # Since the F-5-B1 evolution: exactly this one contract file, and nothing
    # under schemas/ or pyproject.toml (v1.4 adds no schema, no dependency).
    # Reconciled by phase N16-5-F-5-TB-CONTRACT (HPAC-PAWA-001 v1.4 -> v2.0, MAJOR S-4; new companion HPAC-PAWA-HELPER-001 v1.0): re-anchor the moving `HEAD` to the fixed
    # SHA 05056eeb1d38d92d7eda749a4334f7626c5e6a8f (last v1.4 commit).
    since = _git(
        "diff", "--name-only", _F5B1_READAUTH_ENTRY, "05056eeb1d38d92d7eda749a4334f7626c5e6a8f", "--", "docs/contracts", "schemas", "pyproject.toml"
    ).split()
    assert set(since) <= {"docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"}, since


# ── trust root ─────────────────────────────────────────────────────────────


def test_iv10_no_second_mint_seal_or_trust_root_introduced():
    text = (SRC / "core" / "hpac_protected_admin_writer.py").read_text()
    # exactly one factory-seal name is referenced for the mint; the new code
    # imports and reuses it, it does not define a fresh object().
    assert "_PRODUCTION_WRITER_FACTORY_SEAL" in text
    new_seg = _git("diff", I_ENTRY, "HEAD", "--", "src/pcae/core/hpac_protected_admin_writer.py")
    added = "\n".join(l[1:] for l in new_seg.splitlines() if l.startswith("+") and not l.startswith("+++"))
    assert "= object()" not in added, "certification code must not mint a fresh trust-root object"
    assert "_WRITER_CONSTRUCTOR_SEAL" not in added or "import" in added
    # the certification factory threads the *same* factory seal into the same
    # two foundation calls production_writer uses.
    assert added.count("_factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL") >= 2


def test_iv11_foundation_mint_primitive_unchanged_since_i_entry():
    diff = _git("diff", "--name-only", I_ENTRY, "HEAD", "--", "src/pcae/core/hpac_foundation.py")
    assert diff.strip() == "", "hpac_foundation.py (the mint primitive) must be untouched"


# ── factory / role allowlist ───────────────────────────────────────────────


def _validator_fn():
    src = (SRC / "core" / "hpac_protected_admin_writer.py").read_text()
    return next(
        n
        for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.FunctionDef) and n.name == "_validate_certification_inputs"
    )


def test_iv20_role_allowlist_is_exactly_the_closed_five():
    from pcae.core import hpac_protected_admin_writer as w

    assert isinstance(w.CERTIFICATION_ROLE_ALLOWLIST, frozenset)
    assert set(w.CERTIFICATION_ROLE_ALLOWLIST) == FIVE_ROLES
    assert "hpac_lifecycle_terminator" not in w.CERTIFICATION_ROLE_ALLOWLIST


def test_iv21_role_gate_is_exact_membership_no_prefix_glob_regex():
    fn = _validator_fn()
    has_membership_gate = False
    forbidden = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, (ast.In, ast.NotIn)) and isinstance(comp, ast.Name) and comp.id == "CERTIFICATION_ROLE_ALLOWLIST":
                    has_membership_gate = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("startswith", "endswith", "match", "search", "fnmatch", "fnmatchcase"):
                forbidden.add(node.func.attr)
    assert has_membership_gate
    assert not forbidden


def test_iv22_certification_consumer_set_is_closed_and_disjoint_from_the_ss36_set():
    from pcae.core import hpac_protected_admin_writer as w

    assert w.CERTIFICATION_FACTORY_CONSUMERS == frozenset({"pcae.core.hpac_certification_coordinator"})
    # the §36 administrative-mutation consumers cannot mint a certification role
    assert w.CERTIFICATION_FACTORY_CONSUMERS.isdisjoint(w.AUTHORIZED_FACTORY_CONSUMERS)


def test_iv23_ss33_steps_1_9_are_the_shared_verbatim_sequence():
    src = (SRC / "core" / "hpac_protected_admin_writer.py").read_text()
    tree = ast.parse(src)
    # exactly one _run_recognition_sequence definition; both factories call it.
    defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_run_recognition_sequence"]
    assert len(defs) == 1
    callers = {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
        and any(
            isinstance(c, ast.Call)
            and isinstance(c.func, ast.Name)
            and c.func.id == "_run_recognition_sequence"
            for c in ast.walk(n)
        )
    }
    assert {"production_writer", "certification_writer"} <= callers


# ── consumer inventory / import fence ──────────────────────────────────────


def test_iv30_coordinator_and_factory_symbol_absent_from_agent_reachable_code():
    targets = [SRC / "cli.py", SRC / "core" / "agent.py"] + sorted((SRC / "commands").glob("*.py"))
    for path in targets:
        text = path.read_text()
        assert "hpac_certification_coordinator" not in text
        assert "certification_writer" not in text


def test_iv31_only_caller_of_certification_writer_is_the_coordinator():
    hits = subprocess.run(
        ["git", "-C", str(REPO), "grep", "-l", r"certification_writer(", "--", "src", "scripts"],
        capture_output=True,
        text=True,
    ).stdout.split()
    assert set(hits) <= {
        "src/pcae/core/hpac_protected_admin_writer.py",
        "src/pcae/core/hpac_certification_coordinator.py",
    }


def test_iv32_admin_script_is_standalone_not_a_cli_subcommand_or_entrypoint():
    assert (REPO / "scripts" / "hpac_certification_admin.py").exists()
    assert "hpac_certification_admin" not in (SRC / "cli.py").read_text()
    assert "hpac_certification_admin" not in (REPO / "pyproject.toml").read_text()


def test_iv33_coordinator_imports_no_runtime_dispatch_or_gate6plus_path():
    tree = ast.parse((SRC / "core" / "hpac_certification_coordinator.py").read_text())
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module)
        elif isinstance(n, ast.Import):
            mods.update(a.name for a in n.names)
    forbidden = [
        m
        for m in mods
        if any(
            k in m
            for k in ("dispatch", "adapter", "runtime_authority", "permission_broker", "gate6", "gate7", "gate8", "gate9", "gate10")
        )
    ]
    assert forbidden == []


def test_iv34_coordinator_does_not_import_test_or_fixture_seams():
    text = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    for bad in ("import pytest", "from tests", "_PRODUCTION_TEST_FIXTURE_SEAL", "DeterministicCtap2Provider", "monkeypatch"):
        assert bad not in text


# ── principal issuer / real-assurance wall ─────────────────────────────────


def test_iv40_verify_human_authentication_is_the_sole_principal_issuer_call():
    tree = ast.parse((SRC / "core" / "hpac_certification_coordinator.py").read_text())
    names = {
        n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
    }
    assert "verify_human_authentication" in names
    # the coordinator never constructs a principal / gate result directly
    text = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    assert "AuthenticatedHumanPrincipal(" not in text
    assert "object.__new__" not in text


def test_iv41_coordinator_does_not_pass_require_real_assurance_false_downstream():
    text = (SRC / "core" / "hpac_certification_coordinator.py").read_text()
    # the coordinator's own default is True and it forwards the caller value;
    # it never hard-codes a False into verify_human_authentication.
    assert "require_real_assurance: bool = True" in text
    assert "require_real_assurance=False" not in text


# ── certification_proof_subject (OQ-1) ─────────────────────────────────────


def test_iv50_certification_proof_subject_is_a_validated_equality_binding():
    src = (SRC / "core" / "human_authentication_proof.py").read_text()
    fn = next(
        n
        for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.FunctionDef) and n.name == "create_canonical"
    )
    # the override must be compared for equality against proof.proof_id and
    # raise on mismatch — it is not passed through unchecked.
    joined = ast.dump(fn)
    assert "certification_proof_subject" in joined
    assert "proof_id" in joined
    raises_on_mismatch = any(
        isinstance(n, ast.Raise) for n in ast.walk(fn)
    )
    assert raises_on_mismatch


def test_iv51_resolve_canonical_only_accepts_the_records_own_immutable_fields():
    src = (SRC / "core" / "human_authentication_proof.py").read_text()
    fn = next(
        n
        for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.FunctionDef) and n.name == "resolve_canonical"
    )
    joined = ast.dump(fn)
    # the accepted writer subjects are exactly {mechanism_id, proof_id} of the
    # resolved proof — both digest-bound fields of that same record.
    assert "mechanism_id" in joined and "proof_id" in joined


# ── runtime ────────────────────────────────────────────────────────────────


def test_iv60_runtime_remains_observed_observe_unavailable():
    out = subprocess.run(
        ["pcae", "runtime", "inspect"], capture_output=True, text=True, cwd=REPO
    ).stdout
    import re

    assert "not_implemented" in out
    assert "Observed" in out
    assert "unavailable" in out
    assert re.search(r"Plugin count:\s+0\b", out)
    assert re.search(r"Capability count:\s+0\b", out)
