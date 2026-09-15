# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1

Alias: **N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR**

Title: Writer-Authority Contract Repair — Helper-Process-Isolated Mutation
Facades (Model E hybrid), HPAC-PAWA-HELPER-001 v2.0 -> v3.0

## Result

**COMPLETE — REPAIRED / FROZEN — PENDING INDEPENDENT RE-VERIFICATION.**
Contract-drafting-and-structural-tests only. No implementation. No
finalization performed by this bounded worker.

## 0. Governance identity

- **Predecessor canonical Phase ID:**
  `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
  (alias **N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-IV**), final
  commit **f75b5b76** (per repository `git log` at session start: "Phase
  ...1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1: close post-IV idle
  placeholder and open N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR
  task"), confirmed COMPLETE — NOT VERIFIED / BLOCKED.
- **This phase's canonical Phase ID:** the predecessor ID + literal `.1`
  (above).
- **CPIPC validation** (independently validated using `pcae.core.phase_id`
  by the primary operator before delegating this bounded task; cited here
  verbatim, not re-derived by this worker, per the task instructions):
  candidate = predecessor + `.1`; `is_valid` = True; `same_series` = True;
  `same_branch` = True; `compare` = less; `equals` = False; zero matches in
  `git log --all` for the candidate ID at session start.
- Branch `main`.

## 1. Predecessor evidence reconciliation

The predecessor's own final report
(`docs/PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_IV.md`, 456
lines, read in full) reached **COMPLETE — NOT VERIFIED / BLOCKED** on two
independently source-confirmed defects in v2.0 §30A's Model D:

1. **Mint exclusion defect** (predecessor §7): `_mint_production_writer_capability`
   (`src/pcae/core/hpac_foundation.py:753-780`) is gated only by
   `if _factory_seal is not _PRODUCTION_WRITER_FACTORY_SEAL`, where
   `_PRODUCTION_WRITER_FACTORY_SEAL = object()` (`hpac_foundation.py:124`)
   is a bare, unprotected module-level global in a module already loaded in
   the same process as agent-reachable read-path code
   (`hpac_pawa_helper_store_adapter.py`). Any code with `hpac_foundation`
   imported can `getattr` the seal and call the primitive directly,
   bypassing the entire §33 eleven-step recognition sequence. Model D's own
   new primitive was specified (REQ-117) to structurally mirror this exact
   primitive, so it would have inherited the identical defect.
2. **Store-recognition (sink) defect** (predecessor §6/§8): the
   `_CapabilityIssuanceRecord`/`_ISSUED_CAPABILITY_REGISTRY` machinery
   (`hpac_foundation.py:318-470`, `813-854`) tracks `role`, `subject`,
   `authority_class`, and consumption `state` by object identity, but has
   **no field recording which mint entrypoint produced the capability** —
   a helper-scoped and a legacy-broad capability, once issued with the same
   role/subject, are completely indistinguishable to `require_writer`.

**Two threat-matrix gaps** (predecessor §15, quoted verbatim):

> 1. **No threat-matrix row addresses "ordinary process invokes the
>    low-level mint primitive directly, bypassing the higher-level factory's
>    recognition sequence"** — the closest rows (row #1, "ordinary caller
>    constructs a scoped authority object directly"; row #22, "ordinary
>    caller influences a helper-local registry/seal") do not cover this
>    distinct attack shape: reading (not influencing) an already-instantiated
>    real seal and calling the mint primitive with it. This is exactly the
>    central finding in Section 7 above, and the frozen matrix's absence of a
>    dedicated row for it is itself informative — it suggests the ARCH
>    phase's own threat-matrix authoring did not consider this attack shape.
> 2. **No threat-matrix row addresses "role/subject field mutation on an
>    already-legitimately-issued capability by its own holder"** — the actual
>    mitigation for this exists (registry-bound scope dominates mutable
>    fields, §8 above), but no row names the attack.

Recommended successor per the predecessor: `N16-5-F-5-TB-HELPER-WRITER-
AUTHORITY-CONTRACT-REPAIR` (this phase), addressing exactly these two
defects and two gaps, reconsidering whether A/B/C or a tightened D variant
is appropriate — **not** the implementation successor.

## 2. Contract baseline (hashes captured before any edit this phase)

- `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` (v2.0,
  before this phase's edits): `sha256:912405307089ba4d050bad9200bad2d7d7af28cde87f19c3d23e428523a8e4da`
  (1784 lines).
- `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v2.0, unchanged by this phase):
  `sha256:b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e`.
- `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`
  (HPAC-PPA-001 v2.0, unchanged by this phase):
  `sha256:27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2`.

The helper contract's post-edit content is the working-tree state; no new
hash is recorded here since this bounded worker performs no commit (the
primary operator will capture the post-edit hash at finalization).

## 3. Defect reconstruction (independent, source-cited by this worker)

Confirmed directly against `src/pcae/core/hpac_foundation.py` (read in full,
1207 lines):

- `_PRODUCTION_WRITER_FACTORY_SEAL = object()` at line 124, a bare
  module-level global with no construction-time gate of its own.
- `_mint_production_writer_capability` at lines 753-780: its only
  caller-facing gate is `if _factory_seal is not
  _PRODUCTION_WRITER_FACTORY_SEAL: raise HPACAuthorityError(...)` — an
  object-identity check against a readable module attribute, nothing more.
  It never calls `_run_recognition_sequence` / `_detect_caller_module` /
  `_verified_production_caller_name` (that machinery lives one layer up, in
  `hpac_protected_admin_writer.py`).
- `_CapabilityIssuanceRecord` (lines 326-382) and
  `_ISSUED_CAPABILITY_REGISTRY` (line 389), plus `_register_issued_capability`
  (392-404), `_lookup_issued_capability` (407-412), and `require_writer`
  (813-854): every field recorded (`role`, `subject`, `authority_class`,
  `state`) is scope/consumption data, keyed by `id(capability)` with a
  strong reference to prevent id-reuse forgery — genuine, non-trivial
  anti-forgery — but **no field anywhere in this record records which mint
  entrypoint produced the capability object**. `require_writer`
  (`hpac_foundation.py:813-854`) checks `_authority_seal` identity, registry
  membership, `role`/`subject` equality against the registry entry, and
  `authority_class` equality — none of these can distinguish "minted by the
  legacy factory" from "minted by any sibling primitive with the same call
  shape."

**Exploit path (defect 1):** any module in the same OS process that has
already executed `import pcae.core.hpac_foundation` (true, per the
predecessor's confirmation, of the agent-reachable read-path module
`hpac_pawa_helper_store_adapter.py`, and therefore of any process that also
imports that module or `hpac_foundation` directly for any other reason) can
do `getattr(hpac_foundation, "_PRODUCTION_WRITER_FACTORY_SEAL")` and call
`store_authority._mint_production_writer_capability(role, subject,
_factory_seal=that_seal)` directly — no recognition sequence, no peer
authentication, no helper subprocess, nothing but an attribute read.

**Exploit path (defect 2):** even with defect 1 hypothetically closed for a
future primitive, if that primitive still produces a plain
`HPACWriterCapability` (as Model D specified, REQ-117's "same call shape"
sibling), a capability minted via a narrow, correctly-gated helper-only path
and one minted via the broad legacy path are, once issued with the same
`role`/`subject` strings, indistinguishable objects to every downstream
store check — the "narrowness" advertised by Model D existed only as
input-validation discipline at the mint call site, never as a store-side
property.

## 4. Model comparison (reproduced from the contract; see contract §30B.2 for full table and rationale)

| Model | Disposition |
|---|---|
| A — helper-local scoped capability mint | subsumed by D/E |
| pure repaired D (caller-identity check moved into the primitive, still in `hpac_foundation`) | rejected — still an in-process convention-strength check, not a real process boundary |
| pure B (helper-only mutation facades alone) | rejected alone — solves *where* but not *what type*; store still can't distinguish |
| pure C (store-local scoped permits alone) | rejected alone — solves *what type* but not *where*, unless also confined to the helper process |
| **E (selected) — hybrid of B + C** | helper-process-isolated mutation facades, each minting a distinct, non-shared-base-recognized authority family, entirely inside the already-isolated one-shot helper subprocess |

Full justification, per-family scoping guarantees, mint-eligibility
mechanism, and store-recognition mechanism are in the contract's new §30B
(sections 30B.2 through 30B.5). Summary: Model E closes defect 1 by physical
relocation (the mint primitive and its seal are defined and constructed only
inside a module that is **never** imported by any agent-reachable code path
— a real OS-process boundary, not a checkable-but-forgeable token) and
defect 2 by typing (three distinct authority classes recognized by exact-type
/ sealed-family checks, never bare `isinstance` against a shared base class).

## 5. REQ-033 disposition

Contract §30B.15 (`HPAC-PAWA-HELPER-REQ-171`): a further additive
clarification of REQ-033 (REQ-033's and REQ-129's own text unchanged,
byte-for-byte). REQ-033 already forbade the helper from importing the
in-process PAWA factory module or "any agent-reachable module" for the §7
recognition **logic**. This repair extends that same discipline, for the
first time explicitly, to **the writer-authority-derivation mint primitive
itself, not only its caller** — Model D's defect arose precisely because its
mint primitive was specified to live in the agent-reachable-for-reads
`hpac_foundation` module. This is **not** a second factory / second trust
root in the sense the contract already forbids: there remains exactly one
production-authority trust root (OS filesystem write authority over
`<HPAC_PROTECTED_ROOT>`) and one canonical `HPACWriterCapability`-family
construction discipline (`require_writer`/`record_write`, unchanged); what
moves is *where the helper-scoped facade code executes and is defined* — a
module-boundary fact — not the introduction of an independently-trusted
second party. The disposition also requires this boundary be independently
verifiable by static import-graph analysis (closing threat-matrix row 40),
not asserted only by convention.

## 6. PAWA / PPA impact adjudication

- **HPAC-PAWA-001 v2.0: unchanged, byte-identical.** The authority decision
  ("is this a trusted production consumer?") stays owned by HPAC-PAWA-001
  §32/§33/§33B (HPAC-PAWA-HELPER-REQ-006, unaffected); this repair supplies
  only a corrected derivation *mechanism*, fully contained within
  HPAC-PAWA-HELPER-001's own delegated scope. No HPAC-PAWA-001 evolution
  needed.
- **HPAC-PPA-001 v2.0: unchanged, byte-identical.** Contract §17's existing
  open cross-contract question (whether `presentation_evidence_write`'s
  authority-derivation location is within HPAC-PPA-REQ-041/070's existing
  bounds, or needs a fresh HPAC-PPA-001 evolution) is explicitly carried
  forward unresolved by this repair — this repair changes only *where the
  mint primitive is defined and what type it produces*, not *which process
  performs the presentation-evidence write* (already the out-of-process
  presentation helper, unchanged). No HPAC-PPA-001 evolution needed by this
  repair specifically; the pre-existing question remains for
  N16-5-F-5-TB-CONTRACT-IV or its successor.

## 7. Versioning decision: v2.0 -> **v3.0** (MAJOR), not v2.1

Considered against the external-surface MINOR criteria alone (§108: bounded
addition, no wire schema change, no new operation id, no new failure code,
consumed only by already-enumerated consumers), this repair would be
MINOR-shaped — the wire schemas (§11-§17), the three operation ids, the five
certification roles, the three admin-mutation subtypes, and the
`pawa_failure_code` mapping are all byte-unchanged. **However**,
`HPAC-PAWA-HELPER-REQ-130` — a requirement v2.0 itself froze specifically to
close this future classification question — states without qualification
that *"introducing any new internal writer-authority derivation / mint
mechanism, even if narrowly scoped, closed-vocabulary-bound, and never
exported, is a MAJOR change requiring explicit human authorization and
independent verification."* This repair does exactly that (replacing Model
D's specification with Model E's). This is a literal, already-frozen,
unconditional trigger the predecessor contract itself pre-declared — honoring
it is the more conservative and more faithful reading, not a re-derived
judgment call. **Decision: v2.0 -> v3.0, MAJOR.** Full rationale in contract
§30B.9.

## 8. Requirement / invariant inventories

- New requirements: `HPAC-PAWA-HELPER-REQ-141` through
  `HPAC-PAWA-HELPER-REQ-171` (31 new, sequential, no gaps/duplicates —
  independently re-confirmed via `grep` at drafting time, contract §33).
  v3.0 total: 172 requirement items (v2.0's 141 unchanged + 31 new).
- New invariants: `PAWAH-INV-19` through `PAWAH-INV-24` (6 new, contract
  §30C). v3.0 total: 24 invariants.

## 9. Matrices (full text in contract §30B.11-§30B.14)

- **Threat matrix: 40 rows total** — 30 rows inherited unchanged from the
  v2.0 architecture record (`docs/PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_ARCH.md`
  §10), plus 2 rows (31-32) closing the two predecessor-IV gaps quoted in
  §1 above, plus 8 rows (33-40) naming attack shapes the Model E hybrid
  architecture itself newly requires defending (process-boundary-as-primary
  vs. seal-as-defense-in-depth-only; per-family non-isinstance recognition;
  no-shared-base escape in either direction; module-relocation-regression;
  no-fallback-to-superseded-Model-D-or-legacy; single-replay-mechanism
  reuse; second-broad-trust-root rejection for the three-family cluster;
  and REQ-033's module-boundary independent-verifiability requirement).
  This meets phase-authorization §44's ≥36 floor with a reasoned, not
  padded, count — every new row traces to either a named predecessor gap or
  a named new architectural property.
- **Store-recognition matrix**: 4 authority-family rows (three new families
  plus legacy `HPACWriterCapability`) x 4 mutation-surface columns
  (`admin_mutation`, `certification_write`, `presentation_evidence_write`,
  any other/unlisted); every non-listed cell is DENY.
- **Certification five-role matrix**: 5x5, diagonal PERMIT, off-diagonal
  DENY; `hpac_lifecycle_terminator` is not a row/column (denied at the
  closed-enum boundary before reaching the matrix).
- **Admin-mutation subtype matrix**: 7x7 (the seven closed §57 mutation
  subtypes), diagonal PERMIT, off-diagonal DENY.

## 10. Requirement -> future-test traceability (summary; full mapping in contract §30B, each REQ cross-references its threat-matrix row and/or existing §31 testability class)

| New requirement(s) | Future test class |
|---|---|
| REQ-144, REQ-145 | process-import-graph structural test (no agent-reachable module imports the new facade module) |
| REQ-146 | seal-not-sufficient-alone contract-text assertion test |
| REQ-148, REQ-149, REQ-151 | isinstance-escape / reverse-confusion structural tests |
| REQ-150 | recognition-time binding tests (session/request/nonce/installation/generation) |
| REQ-152 through REQ-159 | per-facade closed-enum / cross-operation / cross-role / cross-subtype rejection tests |
| REQ-160 | single-replay-mechanism structural test |
| REQ-163 | failure-code mapping test (no new code) |
| REQ-164 | deterministic-vs-real test |
| REQ-166 | no-fallback-to-superseded-model test |
| REQ-167, REQ-168 | versioning-rationale documentary test |
| REQ-169, REQ-170 | PAWA/PPA byte-unchanged sha256 regression test |
| REQ-171 | import-graph independent-verifiability test |

## 11. Explicit statements (phase-authorization §82 content items)

- Production source (`src/pcae/**`) changed: **NONE**. Confirmed —
  `git diff --stat -- src/pcae` output is **empty** (see report to caller;
  also `git status --porcelain -- src/pcae` empty before and after this
  phase's edits).
- Writer implementation: **NOT BEGUN**. None of the three facades, their
  three authority-family types, or their defining module exist anywhere
  under `src/pcae/**`.
- Caller migration: **NONE**.
- Live host writes: **0**.
- Runtime: **unchanged** — Observed / observe / unavailable; 0 plugins; 0
  capabilities; first governed runtime external effect ABSENT / UNREACHABLE.
- Recommended successor: **N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR-IV**
  (fresh independent verification of this repair) — **not begun**. Do not
  proceed to an implementation successor until that IV independently
  verifies clean.
- N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 remain untouched.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved
exactly. This bounded worker performed contract drafting and structural-test
authoring only, under exactly these constraints: read-only against
`src/pcae/**`; no commit; no push; no `pcae phase complete` /
`pcae push` / `pcae commit` / `pcae task close`; `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
and `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` not
modified; no `tasks/**` file modified. Writes confined to
`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` (in-place
v2.0 -> v3.0 append-only evolution), this phase-evidence document, and one
new test file under `tests/`.

## 12. Open questions / out-of-scope observations (not blocking, disclosed per instructions)

While reading `src/pcae/core/hpac_foundation.py` in full for this repair,
this worker noted that `HPACStoreAuthority._new_capability`
(`hpac_foundation.py:711-743`) — the single construction site both mint
entrypoints call into — has **no seal check of its own**; it relies entirely
on being called only from within `writer()` (fixture-gated) or
`_mint_production_writer_capability` (seal-gated). Nothing in Python
mechanically prevents external code holding a `PRODUCTION`-class
`HPACStoreAuthority` instance (obtainable via the public
`HPACStoreAuthority.production()` classmethod, which requires no seal) from
calling `authority._new_capability(role, subject, single_use=True)`
directly, bypassing **both** existing mint gates entirely. This is a
pre-existing property that equally affects the legacy path today, is
**not** one of the two defects this phase was scoped to repair (the
predecessor IV did not flag it, and the phase-authorization directed a
narrow repair of exactly the mint-exclusion and store-recognition defects),
and this repair's Model E facades do not make it worse (they call down into
the same primitive the legacy path already relies on). It is recorded here,
per the task's instruction to document a genuine ambiguity/gap rather than
silently guess or silently expand scope, as a candidate finding for a future
dedicated hardening phase or for N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-
CONTRACT-REPAIR-IV to independently assess whether it is in-scope for that
IV or a separate follow-on.
