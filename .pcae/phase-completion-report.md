# Phase 150G Complete — Helper Admission Recognition Core Implementation

Canonical Phase ID: `150G`

Alias: **N16-5-F-5-TB-HELPER-ADMISSION-RECOGNITION-CORE-IMPLEMENTATION**

Status: **COMPLETE — SHARED RECOGNITION CORE IMPLEMENTED** (narrow implementation only; helper admission still NOT wired).

CPIPC: a fresh short top-level phase number (`pcae.core.phase_id` `is_valid` True, no collision against `git log --all`), sibling to `150A`-`150F`.

Predecessor: N16-5-F-5-TB-HELPER-ADMISSION-RECOGNITION-SHARED-INFRASTRUCTURE-ARCHITECTURE (150F) — **COMPLETE — ARCHITECTURE VERIFIED**, which selected Model B and recommended this exact narrow implementation as its successor.

## What this phase did

Preflight: `git fetch origin` clean; local `HEAD == origin/main == ce9b8beb` (150F's own final pushed commit); `origin/main..HEAD == 0`; no active governed phase; no unexpected active task (two stale idle placeholders from 150E/150F closed); `PROJECT_STATUS.md` confirmed 150F complete/pushed with Model B selected and this narrow implementation as the recommended next phase.

Realized the Model B architecture: extracted `hpac_protected_admin_writer._run_recognition_sequence`'s §33 steps 1 (root-content checks only — canonical-root resolution itself stays with the legacy factory, the only entitled constructor of an `HPACStoreAuthority`), 4, 5, 6, 2, 3, 7, 8, in that exact original order, into a new module, `src/pcae/core/hpac_pawa_recognition_core.py`, exposing `recognize_protected_anchor(*, root: Path, configured_agent_identity_source, topology_probe=None) -> RecognizedAnchorFacts`. Step 9 (authorized-factory-consumer check) and step 10/11 (configured-agent binding + capability minting) remain unchanged in the legacy factory — never part of the extraction.

`RecognizedAnchorFacts` deliberately carries no `authority` field (unlike the legacy `_RecognizedAnchor`), resolving the one real design tension in Model B: the legacy factory still resolves its own `HPACStoreAuthority` (via its existing `_resolve_authority()`), passes only the plain `root: Path` into the shared core, and keeps its own `authority` reference for step 10/11 binding/minting. The shared core never imports, constructs, or references `HPACStoreAuthority`, `_ensure_root`, or `_validate_production_boundary` (confirmed by AST-based identifier-usage scan, immune to docstring-prose false positives).

Removed (not left as dead code) five steps-1-8-only helper functions (`_require_owner_and_mode`, `_require_not_configured_agent_writable`, `_verify_provenance`, `_exclusion_provenance_ref`, `_positive_write_probe`) and the `TopologyProbe` class / `_real_topology` function from the legacy module, after confirming by full-file grep that they had no other call site; `TopologyProbe` is re-imported for backward-compatible attribute access across ~20 existing test call sites.

A fresh 37-test suite (`tests/test_n16_5_f_5_tb_helper_admission_recognition_core_implementation.py`) proves: behavior parity (old vs. new fail-closed outcomes identical across 9 scenarios, plus the full `production_writer` mint path); the shared core's read-only / non-authoritative / fail-closed / non-cached nature; absence of any duplicate steps-1-8 implementation remaining in the legacy module (AST-based); Model E non-regression; and non-wiring of all six helper admission modules (parametrized — none imports or calls the new core). Isolated keyword sweep (`git stash -u` baseline vs. candidate) showed an identical failure set before fixes (78 failed / 1842 passed both sides, 37 new tests added). Full governed Fast Green attribution surfaced exactly one attributable failure — a pre-existing stale moving-`origin/main`/`HEAD`-bound assertion in an unrelated predecessor phase's own suite (`tests/test_n16_5_f_5_tb_pcae_lifecycle_filename_length_hardening_r.py::test_29_production_diff_confined_to_expected_files`), which pinned `hpac_protected_admin_writer.py` (this phase's own explicitly-authorized production file) against a moving comparison rather than a fixed historical commit range. Repaired in-scope by re-pinning to Phase 150C's own entry/final commit range (`2be6fe01`..`caa155b6`), the same repair pattern already applied twice more in this phase's own commits (one 150F-suite assertion, one provenance-repair-suite byte-identity assertion). Re-running Fast Green attribution after the fix produced `attributable_failures: []`.

Foundation blocker (`hpac_foundation.py`) and Model E authority classes (`hpac_pawa_helper_writer_authority.py`) remain byte-unchanged (pre-existing byte-identity tests still pass). Zero `docs/contracts/**` changes. Helper admission is still NOT implemented by this phase; N-16-5 remains NOT CLOSED; N-16-6/N-16-7 untouched.

Full evidence: `docs/PHASE_150G_N16_5_F_5_TB_HELPER_ADMISSION_RECOGNITION_CORE_IMPLEMENTATION.md`.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — this phase's implementation, tests, and evidence were authored directly by the primary operator; no delegated fork was used. All lifecycle mutation, finalization, commit, and push were performed directly by the primary operator.
