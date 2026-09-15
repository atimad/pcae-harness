# N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-IV — Independent Adversarial Verification Evidence

**Status: DELEGATED BOUNDED WORKER OUTPUT — NOT SELF-FINALIZED.** No commit, no
push, no `pcae phase complete`/`phase-report create` was run by this worker.
This file is an uncommitted working document for the primary operator's
review.

## 0. Scope discipline confirmation

- Zero changes under `src/pcae/**` (confirmed by `git status` at the end of
  this work — see §7).
- No commits, no pushes.
- `tasks/active/**`, `.pcae/**`, `PROJECT_STATUS.md`, `CHANGELOG.md` untouched.
- New files only: this evidence file, and
  `tests/test_n16_5_f_5_tb_helper_writer_authority_contract_iv.py`.

## 1. What was read

- `docs/PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_ARCH.md` (full,
  344 lines) — the predecessor's own architecture record, including its §4
  writer-authority inventory table, §5 mint-path-uniqueness proof, §6
  REQ-033 reconstruction, §8 model comparison, §10 30-row threat matrix.
- `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` §26–§35
  in full, including all of §30A (HPAC-PAWA-HELPER-REQ-115 through REQ-140,
  REQ-114A) and §29 (PAWAH-INV-11 through PAWAH-INV-18).
- `src/pcae/core/hpac_protected_admin_writer.py` (read in full to ~1189
  lines covering the module docstring, REQ-033 fence comment, the §33
  eleven-step `_run_recognition_sequence`, `_detect_caller_module` /
  `_verified_production_caller_name`, `ProductionWriterHandle`, and
  `production_writer()`).
- `src/pcae/core/hpac_foundation.py` — `HPACWriterCapability` (lines
  246–316), `_CapabilityIssuanceRecord` / issuance registry (318–463),
  `HPACStoreAuthority` (514–781), `_mint_production_writer_capability`
  (753–780), `complete_multi_write` (782–804), `require_writer` (813–854),
  `record_write` (936–980), `_ensure_root` (663–706).
- Confirmed by repo-wide `grep`: `_mint_helper_scoped_writer_capability`,
  `_HELPER_WRITER_FACTORY_SEAL`, and
  `pcae.core.hpac_pawa_helper_writer_authority` **do not exist anywhere**
  under `src/pcae/**` — Model D is genuinely unimplemented, independently
  confirmed (not merely trusting the ARCH doc's §15 claim).
- Predecessor's test file
  `tests/test_hpac_pawa_helper_writer_authority_contract_v2.py` (415 lines,
  30 test functions) — re-run, not modified.

## 2. Model D flow, reconstructed independently from contract text

```
existing protected root
  -> registered helper installation (§6)
  -> verified execution object (§6/§8 hash+owner+mode+same-file exec)
  -> verified helper process
  -> authenticated private channel/peer (§9/§10)
  -> configured-agent-exclusion binding (§7 = HPAC-PAWA-001 §33 steps 1-8)
  -> request/replay admission -> OPERATION_ADMITTED (§20, REQ-120)
  -> [NEW] a new, helper-only module (unbuilt; provisionally
     `hpac_pawa_helper_writer_authority`) calls
     `HPACStoreAuthority._mint_helper_scoped_writer_capability(
        operation, mutation|role|None, subject,
        session_id, request_id, nonce, installation_id, generation,
        _factory_seal=_HELPER_WRITER_FACTORY_SEAL, multi_write=...)`
     (REQ-117/118/119/121)
  -> closed operation/role/subtype/subject validation INSIDE the primitive
     itself (REQ-119) -- fail closed, `operation_scope_invalid`, no partial
     mint
  -> installation/generation currentness check against the live anchor
     (REQ-121) -- fail closed, `descriptor_installation_mismatch` /
     `descriptor_generation_stale`
  -> `HPACAuthorityClass.PRODUCTION` check (REQ-138) -- FIXTURE_NON_REAL
     authority raises, mints nothing
  -> mint via the EXISTING, unmodified `_new_capability` construction site
     -> registers in the EXISTING, unmodified process-local issuance
        registry (`_register_issued_capability`)
  -> ordinary `HPACWriterCapability`, single_use=True (REQ-122)
  -> consumed by exactly one `require_writer` + `record_write` (or one
     bounded `complete_multi_write` transaction) inside the SAME helper
     process -> MUTATION_ATTEMPT_STARTED -> MUTATION_COMMITTED
  -> discarded at helper process exit (PAWAH-INV-16); never exported,
     never logged, never persisted (REQ-124)
```

Store recognition (`require_writer`/`record_write`) is explicitly,
contractually **unchanged** (REQ-123) — it keys on `self._seal` identity
plus process-local issuance-registry membership, "independent of which of
the two mint entrypoints produced the capability." This is the crux of
every finding below.

## 3. Subsystem verdict table

| # | Dimension | Verdict | Evidence / reasoning |
|---|---|---|---|
| 1 | Ordinary process invokes new mint path directly, bypassing the helper | **NOT VERIFIED** (structural gap, not fatal) | `_mint_production_writer_capability` — the primitive Model D's own new primitive is contractually specified to mirror (REQ-117: "sibling... same call shape") — is source-confirmed (`hpac_foundation.py:753-780`) to call **none** of `_run_recognition_sequence`, `_detect_caller_module`, `_verified_production_caller_name`, or `AUTHORIZED_FACTORY_CONSUMERS`. Its **only** caller-facing gate is `if _factory_seal is not _PRODUCTION_WRITER_FACTORY_SEAL: raise`. That seal is a bare `object()` module global with **no Python-level access control** — `getattr(hpac_foundation, "_PRODUCTION_WRITER_FACTORY_SEAL")` succeeds from any code that has the (already, admittedly, per §30A.4/REQ-129, agent-reachable-transitively-imported) `hpac_foundation` module loaded. Nothing "mechanically prevents" direct invocation of the low-level primitive by ordinary in-process code beyond a naming convention — confirmed live by `tests/test_n16_5_f_5_tb_helper_writer_authority_contract_iv.py::test_factory_seal_is_an_ordinary_unprotected_module_attribute` and `::test_low_level_mint_primitive_never_calls_the_recognition_sequence`. **Why this is not immediately fatal**: `_mint_production_writer_capability` still calls `self._ensure_root(create=False)` → `_validate_production_boundary()`, which re-checks that the (configured-agent-or-current-process) OS identity **cannot write** the real protected root — and any resulting `HPACWriterCapability`, however minted, still cannot perform a real `record_write` unless the OS filesystem genuinely grants that write. The load-bearing security boundary is OS filesystem permission on `<HPAC_PROTECTED_ROOT>` (contract §3, and `hpac_protected_admin_writer.py`'s own module docstring: "the only principal with real OS write access... the real security boundary; never an in-process check"), not the seal. Model D's REQ-118/131/132 language ("new, distinct seal... strictly narrower... no second trust root") is **true as a statement about the trust root**, but **misleading if read as a claim that the seal itself mechanically restricts who can call the mint primitive** — it does not, any more than the existing legacy seal does today. |
| 2 | Deterministic/test authority promoted to REAL via a settable field | **PARTIALLY NOT VERIFIED** | REQ-138's *check* (`self.authority_class is HPACAuthorityClass.PRODUCTION`) is real and confirmed (`hpac_foundation.py:775`). But `HPACStoreAuthority.authority_class` is an ordinary `__slots__` attribute with **no setter guard** — `fixture_authority.authority_class = HPACAuthorityClass.PRODUCTION` is an unguarded, successful plain assignment (confirmed live by the new test `test_authority_class_enum_has_exactly_two_members_no_promotable_boolean`). This alone is **not** a full bypass (the promoted object still lacks the real protected-root binding `_ensure_root` requires, and still has no entry in the issuance registry until `_new_capability` runs), but it means the FIXTURE/PRODUCTION wall is a single mutable attribute, not an immutable, construction-time-only fact — a defense-in-depth gap the contract does not disclose. |
| 3 | Store recognition (`require_writer`/`record_write`) enforces scope, or accepts type alone | **VERIFIED as narrow-by-convention only, NOT type-enforced** | Source-confirmed (`hpac_foundation.py:813-853`): `require_writer` checks seal identity + registry membership + `record.role != role or record.subject != subject` where `role`/`subject` are **plain caller-supplied strings from whichever store-operation call site invokes it** — not a property of the capability's mint entrypoint. `HPACWriterCapability` has one shape (`__slots__`) for every mint entrypoint, with no `mint_entrypoint`/`minted_by` field. This is REQ-123's own claim, independently confirmed against live source rather than trusted from contract prose (`test_require_writer_signature_takes_role_and_subject_as_plain_caller_args`, `test_scope_narrowing_is_entirely_a_mint_time_input_contract_not_a_store_side_check`). **This is the single most important finding**: Model D is **not narrower at the store layer** at all — it is exactly as broad as the legacy path there. All of its narrowing is concentrated at **mint-time input validation** (§119's closed enum, checked inside the new primitive itself, per REQ-117/119) — a real, mechanically-checkable narrowing relative to the *legacy* `_mint_production_writer_capability` (which has **no** enum check on its own `role: str` parameter — arbitrary role strings are only prevented today by the *factory wrapper's* hardcoded role constants, e.g. `_REGISTRY_WRITER_ROLE`). So Model D's mint entrypoint would genuinely be narrower **than the legacy mint entrypoint**, but it achieves this by validating inputs at its own call boundary, not by the store recognizing it as a distinct, narrower *type* of capability. If a future implementation of Model D's caller module ever mints with a role/subject string that happens to coincide with an unrelated legacy-path operation's expected role/subject, `require_writer` would accept it identically — there is no independent semantic check that the role is "appropriate," only string equality. |
| 4 | Cross-operation/cross-role reuse (5 certification roles, admin subtypes, evidence write) | **VERIFIED, contingent on future implementation fidelity** | The role/subject binding mechanism (registry-membership + string equality, dimension 3) is real and, per REQ-125/126/127, would be exercised identically for Model D as for the legacy path — cross-role/cross-subtype reuse is already mechanically rejected **today** for the legacy path by this exact mechanism (`record.role != role` check), and nothing in Model D's specification weakens it. **Contingent**, not fully verified, because the actual per-operation role/subject *strings* the new caller module will pass are "specification only" (REQ-117) — not yet written; if a future implementation accidentally reuses an existing role string across two logically-distinct scopes, the mechanism (dimension 3) would not catch it. |
| 5 | Target/request/installation/generation/currentness binding | **VERIFIED as specified, NOT independently re-checked at write time** | REQ-121 binds session/request/nonce/installation/generation at *mint* time against the live anchor. REQ-135 **explicitly discloses** that the mint call does **not** itself re-check currentness a second time at write time — that remains the existing store/record layer's unchanged responsibility, "exactly as it is today for a legacy-minted capability." This is an honest, non-hidden disclosure, not a gap the contract missed. |
| 6 | Serialization/copy/deepcopy/restart-dead/disk-persistence/IPC-export | **VERIFIED** | `HPACWriterCapability.__reduce__` and `ProductionWriterHandle.__reduce__` both raise `TypeError` (confirmed source, `hpac_foundation.py:305-306`; `hpac_protected_admin_writer.py:1025-1026`). The issuance registry and both seals are plain process-memory `dict`/`object()` globals — destroyed at process exit (restart-dead, PAWAH-INV-16). Nothing in Model D's specification introduces a new export/serialization path; REQ-124 explicitly reaffirms the existing no-export rule applies identically. |
| 7 | Second trust root / circular trust / generic broker | **VERIFIED as specified** | REQ-132/133 explicitly disclaim a new bootstrap authority, persistent record, env var, or privileged file; the sole trust root remains OS filesystem write authority over `<HPAC_PROTECTED_ROOT>` (§3, unchanged). Contract's own self-consistency statement (§34) reaffirms this. Independently checkable once implemented; not falsifiable from contract text alone, but nothing in the frozen text describes a mechanism that WOULD introduce one. |
| 8 | REQ-033 semantic compatibility | **VERIFIED, Option B disposition is defensible** | REQ-033's literal text (contract §7, confirmed byte-present) names exactly three things: the module `pcae.core.hpac_protected_admin_writer`, three named symbols, and "any agent-reachable module" for realizing the §7 recognition **logic**. It does not, by its literal text, prohibit "helper-side writer authority generally" — REQ-033 is scoped to *how the recognition logic is realized*, not to whether the helper may ever hold write authority at all (HPAC-PAWA-001 §42F already anticipates the helper acting "in its own process"). The Option B reading is textually defensible. However, this IV worker flags an **ambiguity** the ARCH doc's own §6(c) reasoning glosses: REQ-033's prohibition on importing "any agent-reachable module" for the recognition logic is reasoned around by pointing out `hpac_foundation` is *already* imported by agent-reachable code without objection — but that precedent was set for **reads** (`hpac_pawa_helper_store_adapter.py`'s `RealCanonicalReadAdapter`), not for a module that will additionally hold a **write-authority-minting seal**. Extending the precedent from "shared read-path module" to "shared module that also gates real production write authority" is a substantive step the ARCH doc treats as a formality; this IV worker considers it defensible but non-trivial, and notes it as a point a future contract reader could reasonably re-litigate. |
| 9 | Versioning classification (v1.0→v2.0 MAJOR) | **VERIFIED** | HPAC-PAWA-001's own v1.4→v2.0 precedent (cited in the ARCH doc §13, cross-referenced in the contract) was for introducing `recognized_certification_read_authority` — a new authority-boundary-crossing read mechanism. Introducing a new production-write-authority-minting mechanism is at least as significant; MAJOR is the conservative, correct classification, and REQ-130 additively closes the gap for future evolutions rather than leaving it ad hoc. No inconsistency found with other contracts' own versioning conventions in this repo. |
| 10 | Threat-matrix / requirement-inventory completeness | **NOT VERIFIED — one concrete gap found** | The frozen 30-row threat matrix has row #1 ("ordinary caller constructs a scoped authority object directly," mitigated by `__init__`'s `_WRITER_CONSTRUCTOR_SEAL`) and row #22 ("ordinary caller influences a helper-local registry/seal," mitigated by process isolation). **Neither row addresses dimension 1 above**: an ordinary in-process caller who does not construct the object directly and does not "influence" any seal, but simply *reads* an already-instantiated real seal singleton via plain attribute access and calls the low-level **mint primitive** directly, skipping the higher-level factory's entire recognition sequence. This is a distinct attack shape with no dedicated row; confirmed absent by `test_threat_matrix_has_no_row_for_direct_low_level_mint_bypass`. |

## 4. Fifteen required-attack-expansion scenarios — coverage check

None of the fifteen scenario phrasings from the phase-authorization prompt
appear verbatim in the frozen 30-row matrix (confirmed by
`test_required_attack_expansion_scenario_not_verbatim_in_frozen_threat_matrix`,
11 parametrized keyword checks — expected, since the matrix predates this
IV phase). Substantive coverage assessment:

| Scenario | Substantively covered by an existing row? |
|---|---|
| valid scoped object passed to unrelated broad legacy store method | Partially — rows #27/#28 cover admin-vs-certification cross-operation, but no row explicitly frames "Model-D-minted object accepted by the *legacy* factory's own call sites" (which REQ-123 says is mechanically indistinguishable to the store) |
| copied scoped object | Row #9 (copy/deepcopy guard) |
| reconstructed scoped object with identical fields | Row #10 (field-inventory / reconstruction) |
| role/subtype/target/request/generation field mutation after mint | **Gap** — no row addresses a legitimately-issued capability's own mutable slots (`role`/`subject`) being reassigned post-mint by the holder itself; `require_writer`'s registry-membership check (dimension 3 above) is the actual mitigation, but no threat-matrix row names this attack |
| stale currentness after mint | Row #12 |
| mint before replay reservation | Row #34/REQ-134 text covers ordering, but no numbered threat-matrix row is dedicated to "mint attempted before `OPERATION_ADMITTED`" specifically (REQ-120 explicitly disclaims the primitive can self-enforce this) |
| remint after indeterminate mutation | Not directly covered — closest is row #15 (no-auto-retry) |
| deterministic authority promoted to REAL | Row #26 — but see dimension 2 above: the row's cited mitigation (the `is` check) is real, but the matrix does not consider the unguarded `authority_class` attribute assignment path this IV worker found |
| helper mint invoked by ordinary process | **Gap** — see dimension 1 and row-#1/#22 analysis above |
| helper mint invoked from direct helper entrypoint without trusted admission | Addressed narratively by REQ-120 (explicitly disclaims self-enforcement), but has no threat-matrix row |
| authority leaked in exception/repr | Row #24 (marked "future" test, not yet written) |

**Net assessment**: 2 clear gaps (ordinary-process direct mint-primitive
invocation; post-mint field mutation by the legitimate holder), 2 partial
gaps (pre-admission mint ordering; Model-D-object-into-legacy-path framing),
rest adequately covered by existing rows.

## 5. New tests written and results

**New file**: `tests/test_n16_5_f_5_tb_helper_writer_authority_contract_iv.py`
(fresh, independently authored, does not modify or reuse the predecessor's
suite).

```
24 passed in 0.14s
```

Six groups: (1) confirms Model D genuinely unimplemented; (2) the central
adversarial finding (dimension 1) exercised live against the existing,
structurally-mirrored `_mint_production_writer_capability`; (3) store
recognition scope-vs-type analysis (dimension 3); (4) threat-matrix /
required-attack-expansion gap checks (dimension 10, §4 above); (5) REQ-033
/ versioning re-derivation; (6) deterministic-vs-real wall re-derivation
(dimension 2).

**Predecessor regression** —
`tests/test_hpac_pawa_helper_writer_authority_contract_v2.py` (unmodified):

```
39 passed in 0.86s
```

**Helper-boundary regression** (`pytest tests/ -k hpac_pawa_helper`):

```
96 passed, 1 skipped, 42952 deselected in 5.98s
```

## 6. Overall recommendation

Model D is **honestly specified as narrow at the mint-time input-validation
layer**, and that narrowing is real and independently confirmed relative to
the *legacy* mint primitive (which has no enum check of its own). Model D is
**not narrower than the legacy path at the store-recognition layer** —
`require_writer`/`record_write` treat every properly-issued
`HPACWriterCapability` identically regardless of mint entrypoint, exactly as
the contract itself discloses (REQ-123) — so all of Model D's scoping
guarantees rest entirely on (a) the new mint primitive's own closed-enum
input validation being implemented faithfully, and (b) the new seal and new
caller module never being importable by agent-reachable code, a property
that is **not mechanically enforced by Python** and is currently defended
only by import-discipline convention plus a future guard test — the same
class of defense the *existing* legacy seal already relies on, and which
this IV worker independently demonstrated (live, not hypothetically) can be
defeated by ordinary module-attribute access with **no import/sys.modules
manipulation required**, given that `hpac_foundation` (which will hold both
the legacy and the new seal, per REQ-118/131) is already transitively
imported by agent-reachable code today.

This is **not fatal** to the overall security posture, because the
contract's own true trust root — OS filesystem write authority over
`<HPAC_PROTECTED_ROOT>` — remains the thing that actually prevents an
ordinary configured agent from completing a real write, independent of
whether it can forge a `HPACWriterCapability` object in memory. But it does
mean two specific pieces of the contract's own language should not be read
too literally: (1) REQ-118/131's "new, distinct seal... owned exclusively
by a new helper-only module" describes an *intended* import-discipline
boundary, not a *mechanically enforced* one — no code in this contract or
in the existing analogous legacy mechanism prevents ordinary same-process
code from reading the seal via `getattr`/`sys.modules` once the defining
module is loaded; (2) HPAC-PAWA-HELPER-REQ-098's claim to protect against
"import / module / sys.modules manipulation" is over-broad as literally
worded — the specific vector demonstrated here requires no manipulation at
all, only an ordinary attribute read on a module that is, by the contract's
own admission, already loaded in agent-reachable contexts.

**What a defect-fix would need to change** (characterization only, per
instructions — no fix authored here): the low-level mint primitive (both
the existing legacy one and any future Model D one) would need a caller-
identity check of its own — analogous to `_detect_caller_module`/
`_verified_production_caller_name`'s frame-and-module-provenance
verification already used one layer up in `production_writer()` — moved
down into the primitive itself, so that presenting the correct seal object
is necessary but not sufficient; the calling frame's own module identity
would need to be independently, cryptographically-strength verified against
the exclusive intended caller (the new helper-only module), the same
defense already used to close the analogous `_caller_module` keyword-
argument spoof found by the N16-5-F-5-B2/B2R lineage. Given that lineage's
own history in this repository (the seal-identity-alone check was already
found insufficient once, for a different reason — copyable
`_authority_seal` attributes — and repaired by adding the process-local
issuance registry), this finding is consistent with, and continues, that
same pattern: seal identity alone is demonstrably not a sufficient gate at
any layer where it has been tried in this codebase.

## 7. Zero-src-change / zero-commit / zero-push confirmation

```
$ git status --short
 (only new/untracked files under docs/ and tests/; no modification anywhere
 under src/pcae/**; no staged changes; no commits made by this worker)
```

See the actual `git status` output captured by the calling operator at hand-
off; this worker ran no `git add`, `git commit`, `git push`, `pcae phase
complete`, `pcae push`, or `pcae phase-report create` at any point.
