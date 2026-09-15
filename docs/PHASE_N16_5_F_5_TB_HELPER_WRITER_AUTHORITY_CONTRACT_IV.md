# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1

Alias: **N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-IV**

Title: Fresh Independent Verification of Helper-Scoped Writer Authority
Contract Architecture

## Result

**COMPLETE — NOT VERIFIED / BLOCKED.**

## 0. Governance identity

- Predecessor canonical Phase ID:
  `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
  (alias N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-ARCH), confirmed
  COMPLETE / CONTRACT FROZEN — PENDING INDEPENDENT VERIFICATION, agreeing
  identically across PROJECT_STATUS.md, `.pcae/phase-completion-metadata.json`,
  and the active task, at session start.
- This phase's canonical Phase ID: the predecessor ID + literal `.1`
  (above). Independently derived and validated via `pcae.core.phase_id`
  (`parse`/`same_series`/`same_branch`/`compare`/`equals`): `is_valid` True
  on both predecessor and candidate; `same_series` True; `same_branch` True;
  `compare` = less; `equals` = False; zero collisions against
  `git log --all` at entry.
- Branch `main`; HEAD at entry `d951253daa931d49876073cd3d1da88db6ee6b85`;
  `origin/main` identical; `origin/main..HEAD` = 0; working tree clean; no
  conflicting active governed phase.

## 1. Predecessor evidence reconciliation (Section 5/90)

- `79b2582b7d807a0e86d4b534d339fa4163de8c5a` = the predecessor phase's
  **contract-freeze commit** ("freeze HPAC-PAWA-HELPER-001 v2.0
  helper-scoped writer authority contract (architecture only)").
- `0aa8b2bbd85c508083c142187de1117ca5d1e01c`,
  `10265d5f...`, `54eec7ea...`, `d951253d...` = **subsequent
  governance-finalization commits under the identical predecessor phase
  ID** (task close/title repair, final canonical-report-evidence capture,
  idle-placeholder scope sync). All five commits carry the same phase-ID
  commit-subject prefix; confirmed directly via `git log --oneline -10`.
- Disposition: **EVIDENCE-MINOR-MISMATCH, not material.** The predecessor's
  embedded `fast_green.candidate_commit` (`0aa8b2bb...`) is the commit at
  the moment fast-green-attribution was actually run during finalization,
  not the earlier freeze commit (`79b2582b`) — both are legitimate points
  within the same phase's own commit sequence, not a foreign or
  unrelated commit.
- **One real, non-benign gap found**: the predecessor's final
  `validation_results.pcae_push_check` field still reads literally
  `"to be re-verified after push"` in the canonical metadata as of this
  phase's start — it was never resolved to a definitive post-push value,
  contrary to Section 89's requirement ("Do not leave 'to be re-verified
  after push' in final canonical report"). This is a governance-hygiene
  defect in the predecessor's own finalization discipline. It is
  **non-blocking to this IV's semantic verdict** (it does not affect
  whether Model D's architecture is sound) but is recorded here per
  Section 90's explicit reconciliation requirement and should be treated
  as a lesson for future finalizations, not repaired retroactively.

## 2. Frozen-by identity recheck (Section 6)

Re-checked: the contract's own "Frozen by" field and the predecessor Phase
ID agree exactly (both the full 185-character candidate string used by the
predecessor, matching `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`).
No stale malformed identity found elsewhere in the contract's normative
text. **VERIFIED.**

## 3. Versioning (Section 7)

v1.0 → v2.0 (MAJOR) is the correct classification: the change introduces a
new production-write-authority-minting mechanism, at least as significant
as the precedent MAJOR bump HPAC-PAWA-001 took for introducing
`recognized_certification_read_authority`. **VERIFIED.**

## 4. REQ-033 (Section 8)

`HPAC-PAWA-HELPER-REQ-033`'s literal text (contract §7, line 387-393)
prohibits the helper from importing the named in-process PAWA factory
module/symbols, or "any agent-reachable module," specifically for realizing
the §6/§7 recognition **logic**. It does not, by its literal text,
categorically prohibit the helper from ever holding write authority. The
Option B disposition (`HPAC-PAWA-HELPER-REQ-129`, additive clarification,
byte-unchanged intent) is textually defensible. One non-fatal ambiguity
noted: the precedent cited for `hpac_foundation` already being
agent-reachable was established for a **read**-path module use
(`RealCanonicalReadAdapter`), and extending it to a module that will also
gate real production **write** authority is a substantive step the
predecessor's ARCH doc treats as a formality rather than argues fully — a
fair point for a future contract reader to re-litigate, but not itself
sufficient to block this IV. **VERIFIED, with a disclosed ambiguity.**

## 5. Model D independent reconstruction (Section 9)

Reconstructed directly from `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`
§26-§35 and independently cross-checked against `src/pcae/core/hpac_foundation.py`
and `src/pcae/core/hpac_protected_admin_writer.py` source (read-only):

```
protected root -> registered helper installation -> verified execution
object -> verified helper process -> authenticated private channel/peer
-> configured-agent-exclusion binding -> request/replay admission
(OPERATION_ADMITTED) -> [unimplemented] new helper-only module calls
HPACStoreAuthority._mint_helper_scoped_writer_capability(operation,
role/subtype, subject, session_id, request_id, nonce, installation_id,
generation, _factory_seal=_HELPER_WRITER_FACTORY_SEAL) -> closed
operation/role/subtype/subject enum validation INSIDE the primitive itself
-> installation/generation/currentness check -> PRODUCTION authority-class
check -> mint via the existing, unmodified _new_capability construction
site -> registers in the existing, unmodified process-local issuance
registry -> single-use HPACWriterCapability -> consumed by exactly one
require_writer + record_write inside the same helper process ->
MUTATION_ATTEMPT_STARTED -> MUTATION_COMMITTED -> discarded at process exit.
```

Confirmed independently, by repo-wide grep, that
`_mint_helper_scoped_writer_capability`, `_HELPER_WRITER_FACTORY_SEAL`, and
any dedicated `hpac_pawa_helper_writer_authority` module **do not exist
anywhere under `src/pcae/**`** — Model D is genuinely unimplemented (no
production repair, no implementation successor begun).

## 6. Legacy vs. helper capability type relationship (Section 10)

`HPACWriterCapability` (`hpac_foundation.py:246-316`) has a single shape
(`__slots__`) with no `mint_entrypoint`/`minted_by` distinguishing field.
Model D's specified mint would produce **the same runtime class with a
different provenance, indistinguishable to the store** — classification
**D** from Section 10's own list ("same broad object with descriptive
scope fields"), not a subclass or a separate authority type. This is the
root of the central finding below.

## 7. THE CENTRAL FINDING — ordinary-process mint exclusion (Sections
11-13, independently source-confirmed by the primary operator, not merely
accepted from the delegated worker)

`_mint_production_writer_capability` (`hpac_foundation.py:753-780`), the
existing low-level primitive that Model D's own new primitive is
contractually specified to structurally mirror (REQ-117, "sibling, same
call shape"), was read directly:

```python
def _mint_production_writer_capability(
    self, role, subject, *, _factory_seal: object, multi_write: bool = False,
) -> HPACWriterCapability:
    if _factory_seal is not _PRODUCTION_WRITER_FACTORY_SEAL:
        raise HPACAuthorityError(...)
    if self.authority_class is not HPACAuthorityClass.PRODUCTION:
        raise HPACAuthorityError(...)
    self._ensure_root(create=False)
    return self._new_capability(role, subject, single_use=True, multi_write=multi_write)
```

This primitive calls **none** of `_run_recognition_sequence`,
`_detect_caller_module`, `_verified_production_caller_name`, or
`AUTHORIZED_FACTORY_CONSUMERS` — that machinery exists **one layer up**, in
`hpac_protected_admin_writer.py`'s `production_writer()` factory wrapper,
not in the primitive itself. The primitive's only caller-facing gate is
object-identity equality against `_PRODUCTION_WRITER_FACTORY_SEAL`, which
is confirmed at `hpac_foundation.py:124` to be a **bare, unprotected
module-level global**: `_PRODUCTION_WRITER_FACTORY_SEAL = object()`.

Independently confirmed live (not hypothetically) via
`tests/test_n16_5_f_5_tb_helper_writer_authority_contract_iv.py`
(`test_factory_seal_is_an_ordinary_unprotected_module_attribute`,
`test_low_level_mint_primitive_never_calls_the_recognition_sequence` — both
re-run directly by the primary operator, 24/24 passed) and by direct
primary-operator source reading of the same two files: any ordinary Python
code that already has `hpac_foundation` imported (which the contract's own
`HPAC-PAWA-HELPER-REQ-129`/§30A.4 discloses is already true of
agent-reachable code, since `hpac_foundation` is shared with the
agent-reachable read-path module `hpac_pawa_helper_store_adapter.py`) can
read `_PRODUCTION_WRITER_FACTORY_SEAL` via ordinary `getattr` and pass it
to `_mint_production_writer_capability` directly, skipping the entire §33
eleven-step recognition sequence.

Since Model D's own new primitive is specified (REQ-117) to mirror this
exact structure, and the contract's justification for the new seal being
"new, distinct... owned exclusively by a new helper-only module"
(REQ-118/131) rests entirely on an import-discipline **convention** —
nothing mechanically prevents ordinary same-process code from reading a
bare module attribute once the defining module is loaded — this fails the
phase-authorization prompt's own explicit standard (Section 13: *"failure
must rely on non-forgeable/process-local trust state, not a convention. If
ordinary process could satisfy the mint contract: NOT VERIFIED"*), and
matches Section 72's unconditional blocking condition ("ordinary Python can
invoke mint").

**Why this is not a total defeat of the security posture, but is still a
contract-verification blocker**: the true trust root remains OS filesystem
write authority over `<HPAC_PROTECTED_ROOT>` (`_ensure_root`, re-checked
inside the primitive itself on every mint) — an ordinary agent process
minting a forged-but-Python-valid capability object still cannot cause a
real protected write unless its OS identity already has write access,
which by design it should not. So this is not a full authority bypass of
the *ultimate* boundary. But it directly falsifies the contract's own
literal claims (REQ-118/131's "owned exclusively," REQ-098's "protects
against import/module/sys.modules manipulation" — the demonstrated vector
requires **no manipulation at all**, only an ordinary attribute read on an
already-loaded module) as *mechanical* guarantees, and the phase-
authorization prompt's own verification posture (Section 2: *"Do not
trust... names such as 'scoped' or 'narrow'... private constructors...
documentation assertions"*) requires treating an unenforced convention as
a verification failure regardless of whether a downstream boundary happens
to also catch the resulting object. This is consistent with, and continues,
this codebase's own documented history (`hpac_foundation.py:825-834`
comment): a bare seal-identity check was already found insufficient once
before (copyable `_authority_seal` attributes) and repaired by adding the
process-local issuance registry check in `require_writer`. That repair
protects `require_writer`/`record_write`; it does not protect the mint
primitive itself, which is exactly the layer this finding concerns.

## 8. Store recognition / broad-capability escape (Sections 15-16)

Independently confirmed via source read (`require_writer`,
`hpac_foundation.py:813-854`): store recognition is mechanically enforced
against the **process-local issuance registry**, not against mutable
object fields — `record.role != role or record.subject != subject` is
checked against the registry entry set at mint time, which cannot be
altered by the capability holder after the fact. This means: (a) a
Model-D-minted capability passed to an unrelated store call expecting a
different role/subject **is** mechanically rejected (broad-capability
escape via role/subject mismatch: **VERIFIED, prevented**); but (b) store
recognition has **no concept of "which mint entrypoint produced this
capability"** at all — a capability minted via the (unimplemented) helper
path and one minted via the legacy factory path are, once issued with the
same role/subject, **completely indistinguishable** to `require_writer`.
This is contractually disclosed by the contract itself (`REQ-123`), not
hidden. **Net**: cross-operation/cross-role reuse is prevented (contingent
on future implementation using distinct role/subject strings per
operation, which is normal and expected); but Model D's advertised
"narrowness" is **not** a store-side property at all — it exists **only**
at mint-time input validation, one layer that (per finding §7 above) is
itself not exclusively reachable by the intended caller.

## 9. Five-role certification matrix / admin subtype matrix (Sections
17-23)

Mechanically contingent on the same role/subject-string equality mechanism
in §8 above — since that mechanism is real and independently confirmed,
cross-role and cross-subtype reuse would be rejected today for the legacy
path and would be rejected identically for a faithfully-implemented Model D
path, **provided** the future implementation assigns distinct role/subject
strings per operation/role/subtype (specification-only; not yet
implemented, so not independently testable beyond this contingency).
**VERIFIED, contingent on future implementation fidelity** — same
qualification the delegated worker's evidence file records.

## 10. Target/request/installation/generation/currentness binding
(Sections 24-27)

`HPAC-PAWA-HELPER-REQ-121` binds session/request/nonce/installation/
generation at mint time against the live anchor. `HPAC-PAWA-HELPER-REQ-135`
explicitly and honestly discloses that currentness is **not** re-checked a
second time at write time — that remains the unchanged responsibility of
the existing store/record layer, identically to the legacy path today. This
is a disclosed design choice, not a hidden gap. **VERIFIED as specified.**

## 11. Replay ordering / no-auto-retry / consumption (Sections 28-33)

Unchanged from the existing, independently-verified helper process
boundary and replay-ledger mechanisms (outside this phase's scope to
re-verify from scratch, per Section 83's regression-only requirement).
Helper-boundary regression suite re-run directly: **96 passed, 1 skipped,
0 failed** (`pytest tests/ -k hpac_pawa_helper`). **No regression found.**

## 12. Presentation evidence create-only / human election binding
(Sections 34-35)

Unchanged; Model D's specification does not touch `HPAC-PPA-001`'s
create-only semantics or human-election binding, and `HPAC-PPA-001` v2.0
remains byte-unchanged (confirmed via independent `sha256sum`, matching the
predecessor's own recorded value — no drift since predecessor freeze).
**VERIFIED, unaffected.**

## 13. Serialization/copy/reconstruction/restart/IPC/logging (Sections
36-42)

`HPACWriterCapability.__reduce__` and `ProductionWriterHandle.__reduce__`
both raise `TypeError` — confirmed directly at `hpac_foundation.py:305-306`
and `hpac_protected_admin_writer.py:1025-1026`. Issuance registry and both
seals are plain process-memory globals, destroyed at process exit
(restart-dead). Model D's specification introduces no new export path;
`HPAC-PAWA-HELPER-REQ-124` reaffirms the existing no-export rule applies
identically. **VERIFIED.**

## 14. Legacy factory isolation / second trust root / circular trust /
generic broker (Sections 43-47)

`HPAC-PAWA-HELPER-REQ-132`/`133` explicitly disclaim any new bootstrap
authority, persistent record, env var, or privileged file; the sole trust
root remains OS filesystem write authority, unchanged. **VERIFIED as
specified** — not independently falsifiable beyond contract text since
unimplemented, but nothing in the frozen text describes a mechanism that
would introduce a second root. Operation/role vocabularies remain exactly
the five frozen operations and five frozen certification roles
(independently grep-confirmed against the contract text — no sixth
operation, no wildcard role). **VERIFIED.**

## 15. Requirement/invariant/threat-matrix inventory (Sections 58-61)

Independently re-counted (not trusting predecessor's count): `REQ-114`,
`REQ-114A`, `REQ-115` through `REQ-140` present and contiguous in
`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`
(confirmed via direct `grep`). Threat matrix: exactly **30** numbered rows
present in the ARCH doc's §10 (confirmed via direct `grep -c` on the row
pattern — matches the "30-item" claim exactly, no more, no fewer).

**Two clear gaps found** relative to the fifteen required attack-expansion
scenarios (Section 61 of the phase-authorization prompt), independently
re-derived and cross-checked against the frozen matrix:
1. **No threat-matrix row addresses "ordinary process invokes the
   low-level mint primitive directly, bypassing the higher-level factory's
   recognition sequence"** — the closest rows (row #1, "ordinary caller
   constructs a scoped authority object directly"; row #22, "ordinary
   caller influences a helper-local registry/seal") do not cover this
   distinct attack shape: reading (not influencing) an already-instantiated
   real seal and calling the mint primitive with it. This is exactly the
   central finding in Section 7 above, and the frozen matrix's absence of a
   dedicated row for it is itself informative — it suggests the ARCH
   phase's own threat-matrix authoring did not consider this attack shape.
2. **No threat-matrix row addresses "role/subject field mutation on an
   already-legitimately-issued capability by its own holder"** — the actual
   mitigation for this exists (registry-bound scope dominates mutable
   fields, §8 above), but no row names the attack.

Two partial gaps: pre-admission mint ordering (REQ-134 covers it in prose,
no dedicated numbered row) and "Model-D-object accepted by an unrelated
*legacy* call site" framing (rows #27/28 cover admin-vs-certification
cross-operation generally, but not this specific framing). Remaining
scenarios adequately covered by existing rows.

## 16. Fresh IV tests / regression tallies (Sections 81-84)

- Fresh IV tests (`tests/test_n16_5_f_5_tb_helper_writer_authority_contract_iv.py`,
  newly authored, independent of predecessor's suite): **24 passed**
  (re-run directly by the primary operator).
- Predecessor's 39-test suite
  (`tests/test_hpac_pawa_helper_writer_authority_contract_v2.py`,
  unmodified — treated as regression only, not independent proof): **39
  passed** (re-run directly by the primary operator).
- Helper-boundary regression (`pytest tests/ -k hpac_pawa_helper`): **96
  passed, 1 skipped, 0 failed** (re-run directly by the primary operator).
- Governed fast-green-attribution: run directly by the primary operator
  (see below), against final pushed HEAD.

## 17. Subsystem verdict table (Section 70)

| Dimension | Verdict |
|---|---|
| Model D scope (narrower than legacy) | **NOT VERIFIED** — narrower only at mint-time input validation, not at store recognition |
| Second mint eligibility (non-forgeable) | **NOT VERIFIED** — gated only by a bare, unprotected module-level object |
| Ordinary-process exclusion | **NOT VERIFIED** — demonstrated, live, that the mirrored primitive is callable by ordinary same-process code holding the seal reference |
| Store enforcement | VERIFIED (role/subject registry-bound), but does not distinguish mint entrypoint |
| Cross-operation isolation | VERIFIED, contingent on future distinct role/subject strings |
| Certification-role isolation | VERIFIED, contingent on future implementation fidelity |
| Admin-subtype isolation | VERIFIED, contingent on future implementation fidelity |
| Target/request binding | VERIFIED as specified |
| Install/generation/currentness binding | VERIFIED as specified (currentness re-check at write time explicitly and honestly disclaimed, not hidden) |
| Replay/no-retry ordering | VERIFIED (unchanged, regression-confirmed) |
| Non-serialization | VERIFIED |
| Non-reconstruction | VERIFIED |
| Restart-dead semantics | VERIFIED |
| No IPC export | VERIFIED |
| Presentation create-only | VERIFIED (unaffected) |
| REQ-033 consistency | VERIFIED, with one disclosed non-fatal ambiguity |
| No second trust root | VERIFIED as specified |
| No generic broker | VERIFIED (closed vocabularies confirmed) |
| PAWA cross-consistency | VERIFIED (byte-unchanged, confirmed via sha256) |
| PPA cross-consistency | VERIFIED (byte-unchanged, confirmed via sha256) |
| Versioning | VERIFIED |
| Predecessor evidence consistency | MINOR MISMATCH (bookkeeping, non-material) plus one unresolved `pcae_push_check` hygiene gap |
| Threat-matrix/requirement-inventory completeness | **NOT VERIFIED** — two clear gaps found (§15 above) |

## 18. Overall verdict (Sections 70-72)

**COMPLETE — NOT VERIFIED / BLOCKED.**

Load-bearing reasons (per Section 72's own explicit criteria): "ordinary
Python can invoke mint" is demonstrated true for the existing primitive
Model D's own new primitive is specified to structurally mirror; "scope
fields are descriptive but not enforced" is true **at the store layer**
(narrowing exists only at mint-time input validation, one layer that is
itself not exclusively reachable by the intended caller). Both conditions
are independently source-confirmed by the primary operator, not merely
accepted from the delegated worker's report — see Section 7 above for the
direct source excerpts and live test confirmation.

This is **not** a claim that Model D is catastrophically insecure in
practice (the ultimate OS-filesystem trust root remains intact and
independently re-checked on every mint), but the phase-authorization
prompt's own verification posture (Section 2) requires treating an
unenforced naming/import convention as a verification failure, and Section
72 lists this exact condition as unconditionally blocking. Per Section 73,
this IV recommends a narrow contract-repair phase, not the implementation
successor.

## 19. Recommended contract-repair characterization (Section 73; no fix
authored)

The low-level mint primitive (both the existing legacy one and any future
Model D one) needs a caller-identity check of its own — the same class of
frame-and-module-provenance verification already used one layer up in
`production_writer()` (`_detect_caller_module`/
`_verified_production_caller_name`) — moved down into the primitive itself,
so that presenting the correct seal object is necessary but not
sufficient. This is consistent with, and continues, this codebase's own
prior pattern of finding and repairing exactly this class of gap (the
process-local issuance registry was added to `require_writer` after a
similar seal-identity-alone insufficiency was found for a different
attack). This characterization is offered for a future contract-repair
phase's scoping; **no repair was authored in this phase.**

## 20. What did NOT happen (Sections 3, 75-79, 94)

- Zero production source (`src/pcae/**`) changes: confirmed via
  `git status --porcelain -- src/pcae/` before and after this phase (empty
  both times).
- No mint path, authority class, or store method was implemented or
  modified.
- No blocked operation (`admin_mutation`, `certification_write`,
  `presentation_evidence_write`) was unlocked.
- No caller migration. No packaging change. No live host mutation. No
  helper deployment/registration/generation rotation. No real FIDO2
  ceremony, no real protected presentation, no real certification.
- No implementation successor (`N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL`
  or equivalent) begun.
- N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 remain untouched.
- Runtime remained Observed / observe / unavailable throughout; 0
  plugins, 0 capabilities; first governed runtime external effect
  ABSENT/UNREACHABLE.
- Transition-validator ancestry-checking gap remains a separately
  deferred follow-up, not mixed into this IV (Section 80).

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved
exactly. The bounded delegated worker performed contract/source-fact
extraction and adversarial-test authoring only, under exactly these
constraints; it made no commits, no pushes, and touched no file under
`src/pcae/**`, `.pcae/**`, `tasks/active/**`, or `PROJECT_STATUS.md`
(independently confirmed via `git status --porcelain` by the primary
operator after hand-off, before any further action was taken). The primary
operator independently re-read the delegated worker's evidence file in
full, independently re-derived the central finding directly against
production source (`hpac_foundation.py:124,753-780,813-854`) rather than
accepting the worker's summary, independently re-ran all test suites
(24 + 39 + 96 passed / 1 skipped, 0 failed across all three), and performed
all governance/finalization steps below directly.

## 21. Recommended successor

`N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR` (or
repository-conformant CPIPC-derived equivalent) — a **narrow
contract-repair** phase addressing the ordinary-process mint-exclusion gap
(Section 19 above) and the two threat-matrix gaps (Section 15 above),
reconsidering whether Model A/B/C or a tightened Model D variant (with a
caller-identity check moved into the low-level primitive itself) is
appropriate. **NOT begun.** Do not proceed to
`N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL` until this repair phase
independently verifies clean.
