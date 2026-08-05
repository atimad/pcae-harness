# Phase 149O.1B.2 Complete — Canonical Repository Identity Architecture

**Phase ID:** 149O.1B.2
**Mode:** Repository-identity architecture only (blocking prerequisite
for HATP-001 freeze, flagged by 149O.1B.1)
**Predecessor:** 149O.1B.1 (Human Approval Bootstrap Authority
Architecture — completed, HUMAN APPROVAL BOOTSTRAP AUTHORITY
ARCHITECTURE DEFINED — REPOSITORY IDENTITY PREREQUISITE REMAINS)
**Date:** 2026-08-05
**Status:** completed
**Pushed:** pushed

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_1B_2_CANONICAL_REPOSITORY_IDENTITY_ARCHITECTURE.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149O.1B.2's job was the one prerequisite 149O.1B.1 flagged as
BLOCKING and left unresolved: what constitutes one PCAE repository
instance for the purpose of scoping HATP repository-specific
rollback-approval authority. It did not reopen Root 1, Root 2A, or
Root 2B, all already selected by prior phases.

**Independent recheck:** rather than trusting 149O.1B.1's "no suitable
identity exists" conclusion, this phase re-ran the primary-source
search from scratch across `.pcae/**` and `src/pcae/**`. Confirmed:
every `repository_identity`-named field in this codebase today is
either the current phase's own `phase_id` label (changes every phase)
or a human-editable `pyproject.toml` `[project] name` string with a
hardcoded fallback — neither mechanically derived, protected, nor
instance-scoped.

**Selected model — CRI Model A (two-layer):** Layer 1 is a
repository-local, random, persisted repository-instance UUID that
confers no HATP authority by itself. Layer 2 is a protected,
admin-owned, agent-unwritable HATP deployment binding (reusing
149O.1B.1's Class-B trust-store boundary) keyed on a resolved
canonical local deployment root — the only place authority actually
exists. This closes the mandatory copy/clone attack: copying or
cloning the identity UUID alone does not transfer HATP authority,
because Layer 2's binding will not match a copied or cloned tree's
canonical root.

**Scenario/attack matrix resolved, no ambiguous cell:** path move,
rename, restore (same root vs. different root), full-directory copy,
`git clone`, fork, `git worktree` (decided: distinct identity per
worktree), repository-ID theft, repository-ID mutation/deletion — all
explicitly worked through and shown to fail closed under Model A.

**Independently verified (not assumed):** `.pcae/**` is only partially
gitignored in this repository (`agent-lock.json` is ignored via
`.pcae/.gitignore`; `phase-completion-metadata.json` and
`repository-intelligence/latest.json` are tracked) — so any future
repository-identity file must be added to `.pcae/.gitignore`, not
committed, or the clone-inherits-authority hole reopens automatically.

**Contract ownership:** decided no separate Canonical Repository
Identity contract is required before HATP-001 freeze — this
architecture's normative content is fully HATP-scoped.

**Architecture verdict: CANONICAL REPOSITORY IDENTITY ARCHITECTURE
DEFINED — READY TO RESUME HATP CONTRACT FREEZE.**

No production code changed this phase (`git status --short` confirms
zero `src/pcae/**` and zero `docs/contracts/**` diff, zero `.pcae`
initialization behavior change). No OS account, ACL, or sudoers
configuration was created or changed — HATP bootstrap environment
remains **NOT READY** (same OS user for human and agent; deployment
work, unchanged, out of this architecture-only phase's scope). B-149O-
1..4 remain OPEN, unchanged. AG3/AG5 remain unwired. RAE-001/RWMPC-001/
PBPC-001/PBPA-001/CHGR-001 all remain byte-unchanged. Fast Green: 4391
passed, exact match to entering baseline, no flake. Runtime remains
Observed / observe / unavailable throughout.

**Recommended next phase:** 149O.1B.3 — Human Approval Trusted
Provenance Contract Freeze, resuming the HATP-001 freeze now that Root
1, Root 2A, Root 2B, and repository identity are all resolved.

See `docs/PHASE_149O_1B_2_CANONICAL_REPOSITORY_IDENTITY_ARCHITECTURE.md`
for the full analysis.
