# Phase 150F — N16-5-F-5-TB-HELPER-ADMISSION-RECOGNITION-SHARED-INFRASTRUCTURE-ARCHITECTURE

**Status: COMPLETE — HELPER ADMISSION RECOGNITION SHARED-INFRASTRUCTURE ARCHITECTURE VERIFIED (architecture/contract-freeze only; no production implementation).**

CPIPC: `150F`, an independently derived, unused, valid (`pcae.core.phase_id.is_valid` True) short top-level sibling of `150A`-`150E`, confirmed absent from `git log --all` and from `tasks/`/`docs/`/`PROJECT_STATUS.md`/`CHANGELOG.md` before use.

Runtime posture: Observed / observe / unavailable (unchanged). N-16-5: **NOT CLOSED** (architecture work does not close it). N-16-6 / N-16-7: **untouched**.

## 0. Preflight

Before opening this phase: `git fetch origin` — clean; `git status` — clean; local `HEAD == origin/main == 81985989c3d49f8aa52cf999168c07d4ba8035d8`; `origin/main..HEAD == 0`; none of the four forbidden held/disowned commits (`6c7f5cf4`, `2b8ad2aa`, `72cdba16`, `d0b2a75a`) in ancestry; no active governed phase (`pcae session read` showed only the Phase 150E idle-placeholder task); `PROJECT_STATUS.md`'s `## Current Phase` section (Phase 150E) independently read and confirmed as authoritative; Phase 150E confirmed complete and pushed; recommended next work confirmed to be exactly this architecture question; N-16-5 confirmed OPEN, N-16-6/N-16-7 confirmed untouched.

## 1. Current-state reconstruction

### 1.1 `hpac_protected_admin_writer._run_recognition_sequence` (lines 719-927)

Independently re-read from current source (not from Phase 150E's prose). The function runs eleven physically-ordered checks inside one hard fail-closed `try/except Exception` wrapper (924-927: any non-`PawaError` becomes `PawaError("internal_fail_closed", ...)`; no step can fail open). Physical order in source: STEP 1, STEP 4, STEP 5, STEP 6, STEP 2, STEP 3, STEP 7, STEP 8, STEP 9 (STEP 10/11 — mint + audit — live outside this function, in the caller).

| Step | Purpose | Reads | Side effect | Depends on admin-writer-only state | Depends on agent/process-only primitive | Read-only | Mints/consumes authority | Safe for helper to invoke |
|---|---|---|---|---|---|---|---|---|
| 1 (740-756) | Resolve canonical `<HPAC_PROTECTED_ROOT>`, reject symlinks, check mode | filesystem stat/symlink/dir checks | none | no | no | yes | no | yes |
| 4 (762-784) | `HPAC-STORE-AUTHORITY/1.0` manifest + `{device,inode}` binding | manifest JSON, `root_owner_uid` (from step 1) | none | no | no | yes | no | yes |
| 5 (786-806) | Authority descriptor: schema/owner/mode/root-identity/`state==ACTIVE` | descriptor JSON | none | no | no | yes | no | yes |
| 6 (808-841) | `current-generation.json`: schema/installation/generation/digest + provenance | current-generation JSON | none | no | no | yes | no | yes |
| 2 (843-874) | Resolve `ConfiguredAgentAuthorityIdentity` via `HPAC-PAWA-AGENT-EXCLUSION/1.0` (`resolve_configured_agent_identity`, `hpac_pawa_agent_exclusion.py`) | exclusion-record JSON, live `pwd`/`os.getgrouplist` (via the exclusion module, not admin-writer) | none | no | no (reads the *configured* agent's OS record, not the calling process) | yes | no | yes |
| 3 (876-896) | Configured-agent exclusion negative boundary (`_effective_write_access`/`_ancestor_chain_safe` against the configured agent, F-1) + exclusion-file self-protection | live filesystem permission topology; `configured_agent.uid/gids` (step 2) | none | no | no | yes | no | yes |
| 7 (898-904) | Current administrative context is **not** the configured agent (`_current_agent_identity()` vs `configured_agent.uid`) | live calling-process OS identity | none | no | yes (`_current_agent_identity()` is exactly "who is running this code now") | yes | no | yes — this is the check the helper *also* needs, run against the helper's own process identity |
| 8 (906-908, impl. 936-963) | `O_EXCL\|O_NOFOLLOW` positive write probe under `.authority/` | filesystem (creates+deletes one sentinel file) | **yes** — one self-contained, deterministic create/write/fsync/unlink | no | no | **no** (the only side-effecting step) | no (proves capability to write; does not itself write anything durable or mint a capability) | yes — contract (REQ-031 item "the `O_EXCL\|O_NOFOLLOW` positive write probe under `.authority/` (§28)") already requires this conjunct inside the helper too |
| 9 (910-912) | Calling module is an authorized factory consumer (`AUTHORIZED_FACTORY_CONSUMERS`/`_TEST_FACTORY_CONSUMERS`) | `caller_module` string (from `_detect_caller_module`'s anti-spoofing frame walk) | none | **yes** — the allowlist itself is an admin-writer-module-only concept | no | yes | no | **no** — HPAC-PAWA-001 v2.0's own note (quoted in §2 below) states this step is *replaced* for the helper by a distinct step 9′ |

Independently confirmed by direct source inspection (test: `test_steps_1_through_8_contain_no_mutation_or_write_authority_primitive`, `test_steps_1_through_8_do_not_touch_hpac_store_authority`): **steps 1-8, as a contiguous region, reference no capability-mint primitive, no write-authority class, no seal object, and no `HPACStoreAuthority` method at all** — not `_validate_production_boundary`, not `_ensure_root`, not `_bind_configured_agent_identity`, not `_mint_production_writer_capability`, not `_new_capability`. The function's return value, `_RecognizedAnchor` (914-923), carries only descriptive identity fields (`authority`, `root`, `live_root_identity[_digest]`, `anchor_id`, `installation_id`, `generation`, `configured_agent`) — no writer capability, no token, no seal (test: `test_recognized_anchor_return_is_descriptive_not_capability_bearing`).

Independently confirmed (test: `test_only_step_9_references_the_factory_consumer_allowlist`): the factory-consumer allowlist (`authorized_consumers`/`test_consumers`) is referenced **only** inside step 9's own three lines (910-912) — nowhere in steps 1-8.

### 1.2 Helper-side state (unchanged since Phase 150E; independently re-confirmed against current source, not assumed from prior prose)

- `hpac_pawa_helper_os.authenticate_peer` (287-305): `configured_agent: Optional[ConfiguredAgentAuthorityIdentity] = None`; its docstring's "defaults to a live resolution via `resolve_configured_agent_identity`" claim is **still false** — no call to that function exists inside it.
- `hpac_pawa_helper_launcher.py:141`, the sole production caller, still supplies only `deployment_owner_uid`; the module still contains no reference to `resolve_configured_agent_identity` or `configured_agent=` (test: `test_helper_launcher_still_has_no_configured_agent_resolution`).
- `hpac_pawa_helper_entrypoint.py` / `hpac_pawa_helper_store_adapter.py` still contain no call to `resolve_configured_agent_identity` anywhere — REQ-031's full in-helper §33-steps-1-8 recognition is still entirely unimplemented (test: `test_helper_entrypoint_still_has_no_in_helper_recognition`).
- REQ-033's fence still holds: none of `hpac_pawa_helper_os.py`, `hpac_pawa_helper_launcher.py`, `hpac_pawa_helper_entrypoint.py`, `hpac_pawa_helper_operations.py`, `hpac_pawa_helper_store_adapter.py` import `hpac_protected_admin_writer` (test: `test_helper_modules_still_forbidden_from_importing_admin_writer`).

This confirms **N-16-5 remains open for the identical reason Phase 150E left it open** — this phase changes none of that production behavior; it defines the boundary a future implementation phase would use to close it.

### 1.3 `hpac_pawa_agent_exclusion.py` — the one dependency a shared module would need

Module docstring (1-41) already declares itself inside "the non-agent-importable consumer-inventory fence" and permits helper-side import as a co-shipped, non-agent-reachable primitive under REQ-033's own carve-out (`hpac_pawa_helper_os.py` already imports it today). Independently confirmed (test: `test_hpac_pawa_agent_exclusion_has_no_mutation_primitive_or_writer_authority_import`): it imports only `hpac_foundation.HPACMalformedError` (an error class, not `HPACStoreAuthority` itself) and `hpac_pawa_schemas`; it defines no function whose name suggests mutation (no `mutate*`/`write_*`/`*capability*`); it does not import `hpac_pawa_helper_writer_authority`.

### 1.4 The separate foundation blocker (`HPACStoreAuthority._ensure_root`/`_validate_production_boundary`, `hpac_foundation.py`)

Independently reconstructed and confirmed unchanged, per N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL's prior finding: `_bind_configured_agent_identity` (599-611) is gated by `_PRODUCTION_WRITER_FACTORY_SEAL`, callable only from the legacy factory; `_validate_production_boundary` (639-661) falls back to `_current_agent_identity()` (the *calling process's* live identity) whenever `_configured_agent_identity` was never bound — which is the case for any `HPACStoreAuthority` instance used outside the legacy factory's own recognition sequence, including the Model E helper write path. **This phase's proposed shared module does not touch any of this machinery** (§1.1's steps-1-8 region references none of it) — see §13 for the explicit foundation-separation statement.

## 2. Exact contract requirement mapping

HPAC-PAWA-HELPER-001 v5.0 §7 (REQ-031/032/033) requires the helper to run, in its own interpreter, "HPAC-PAWA-001 §33 steps 1-8" before admitting any operation. The real §33 (`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`, HPAC-PAWA-001 v4.0, line 1429, `## 33. Positive validation sequence`) is an **11-step** frozen order, and its own v2.0 note (lines 1487-1496) states explicitly:

> "Steps 1–8 are unchanged and are executed by helper-local code that imports no agent-reachable module... Step 9 is replaced per §33C step 9′. Step 10 becomes 'perform the one bounded operation' and step 11 keeps the audit-evidence record..."

This is independent contract-text confirmation — not an inference of this phase — that steps 1-8 are exactly the portion meant to be shared/re-implemented identically by both consumers, while steps 9-11 are consumer-specific by the contract's own design.

| Contract step | Current implementation symbol | Current module | Current caller | Helper reachable today? | Authority-bearing? | Candidate for neutral extraction? |
|---|---|---|---|---|---|---|
| 1 root resolution | inline (740-756) | `hpac_protected_admin_writer.py` | legacy factory only | no | no | **yes** |
| 2 configured-agent resolution | `resolve_configured_agent_identity` | `hpac_pawa_agent_exclusion.py` | legacy factory only (via step 2's call) | no (helper never calls it — dead import) | no | **yes** |
| 3 exclusion boundary | inline (876-896) | `hpac_protected_admin_writer.py` | legacy factory only | no | no | **yes** |
| 4 manifest binding | inline (762-784) | `hpac_protected_admin_writer.py` | legacy factory only | no | no | **yes** |
| 5 descriptor trust | inline (786-806) | `hpac_protected_admin_writer.py` | legacy factory only | no | no | **yes** |
| 6 current-generation | inline (808-841) | `hpac_protected_admin_writer.py` | legacy factory only | no | no | **yes** |
| 7 not-current-context | inline (898-904) | `hpac_protected_admin_writer.py` | legacy factory only | no | no | **yes** |
| 8 positive write probe | `_positive_write_probe` (936-963) | `hpac_protected_admin_writer.py` | legacy factory only | no | no (proves, does not mint) | **yes** |
| 9′ (helper-specific consumer check) | **not implemented** | — | — | n/a | n/a | no (admin-writer's step 9 is a different check; helper's 9′ is contract-deferred, out of this architecture's scope) |
| 10 (helper: "perform the one bounded operation") | Model E facades (`hpac_pawa_helper_writer_authority.py`) | already implemented, separately | helper | yes | yes | no — already implemented by the separately-blocked Model E work |
| 11 audit | separately implemented per module | — | — | — | — | no |

No contract step has semantics that differ between the admin-writer implementation and what the helper needs — REQ-031/032 explicitly require the *same* steps 1-8, evaluated against the *same* `ConfiguredAgentAuthorityIdentity` concept, with no admin-writer-specific variant of steps 1-8 identified anywhere in the current contract text or source.

## 3. Trust-boundary analysis

Explicitly assessed against the required list:

- **Agent-controlled module/global state, mutable process-local registries, bearer handles**: none of steps 1-8 read or write any such state; they read only the filesystem (protected-root manifest/descriptor/current-generation/exclusion documents) and, in step 7, the live calling-process OS identity (a kernel fact, not a Python object).
- **`HPACWriterCapability`, Model E authority objects, protected-admin-writer authority**: absent from steps 1-8 by direct inspection (§1.1); confirmed by `test_steps_1_through_8_contain_no_mutation_or_write_authority_primitive`.
- **Configured-agent declarations, repository-controlled configuration, environment variables**: the exclusion record is untrusted filesystem data validated against ground-truth `{device,inode}`/digest bindings (steps 2/4/5/6) before being trusted — this validation chain is exactly what would move into the shared module, unchanged.
- **`sys.modules`/import-state identity, caller-frame/module-name identity, arbitrary Python object identity**: step 9 (caller-module / frame-walk identity) is explicitly excluded from the shared module (§1.1, §2) — it stays admin-writer-specific. The shared module introduces no caller-identity check of its own; it is a pure function of `(protected_root, filesystem state, OS account database, live process identity)`.
- **Writable filesystem state, symlinks/path substitution**: steps 1/4/5/6 already reject symlink components and validate ownership/mode; this is exactly the logic being reused, not weakened.
- **Peer PID/UID/GID facts, helper installation identity, launch/install identity, replay/currentness state**: none of these are read by steps 1-8 today; they belong to the launcher's separate peer-authentication layer (REQ-042) and to the currentness re-checks Model E's write path already performs independently (`_require_currentness`).
- The helper does **not** gain trust by importing an agent-owned/admin-authority module: the proposed shared module is not `hpac_protected_admin_writer`, imports nothing from it, and (per §1.3) its one real dependency (`hpac_pawa_agent_exclusion`) is already an explicitly non-agent-reachable, helper-importable module under REQ-033's existing carve-out.

## 4. Candidate architecture evaluation

**Model A — duplicate recognition logic inside helper modules.** Rejected. Would create a second, independently-maintained implementation of the ~170-line steps-1-8 validation chain (symlink rejection, manifest/descriptor/current-generation schema+digest+ownership validation, exclusion resolution, exclusion boundary, non-agent-context check, write probe) — the exact "two divergent recognition implementations" anti-pattern this codebase already explicitly rejects elsewhere (`hpac_pawa_helper_store_adapter.resolve_launcher_deployment_metadata`'s own docstring: "the exact same read-only resolver ... one canonical source ... never two divergent ones"). High divergence risk over time; violates PAWA-INV-3's "no single conjunct sufficient" spirit by risking silent semantic drift between the two copies; explicitly forbidden by this phase's own authorization.

**Model B — extract the neutral, read-mostly recognition portion (steps 1-8) into a shared module consumed by both the legacy factory and the future helper.** Selected (§5). Zero authority export (§3); zero circular-dependency risk (§1.3, §1.4 — the one real dependency, `hpac_pawa_agent_exclusion`, has no reverse dependency on either consumer or on the write-authority module, confirmed by `test_hpac_pawa_agent_exclusion_has_no_mutation_primitive_or_writer_authority_import` and `test_admin_writer_module_does_not_import_helper_writer_authority`); zero divergence risk by construction (one implementation, two callers); does not touch the foundation blocker (§1.4, §13); fully compatible with Model E (§12, unrelated code paths); testable in isolation against synthetic protected roots; migration is a mechanical refactor of the legacy factory's own steps 1-8 into calls against the new module plus (in a later, separately-authorized phase) new call sites inside the helper.

**Model C — move all recognition to the helper; admin-writer consumes a helper-produced result.** Rejected. Inverts trust direction: the legacy factory runs synchronously in-process today and has no IPC dependency on a helper process; making it consume a result "produced by the helper" would require either (a) spinning up a helper process from every legacy-factory call site (a runtime/behavior change far outside this phase's scope and likely outside any narrow future phase's scope too), or (b) some other new trust-transfer mechanism from helper to admin-writer that does not exist in the contract today. Blurs "helper admission != authority-family selection" and would require a genuine contract-evolution phase, not an architecture freeze. Not evaluated further; no repository evidence supports it as achievable within the walls this phase must preserve.

**Model D — other.** Not selected. No repository evidence (contract text, existing precedent, or structural constraint) surfaced during this reconstruction that motivates a fourth model; Models A/B/C above exhaust the design space actually implied by the current contract and source.

## 5. Selected architecture and rationale

**Model B.** The neutral module realizes exactly HPAC-PAWA-001 §33 steps 1-8 (root resolution, manifest binding, descriptor trust, current-generation validation, configured-agent resolution, exclusion boundary, non-agent-context check, positive write probe) as a single, shared, read-mostly implementation. It is selected because: it is the only model that satisfies REQ-031 (helper can run the *same* steps 1-8, in its own interpreter, without importing the forbidden module) without creating a second implementation (Model A) or inverting trust direction (Model C); it requires no new authority concept; it does not collapse or touch Model E; it separates cleanly from the still-open foundation blocker; and it is exactly the model the contract's own v2.0 note (§2) already anticipates by describing steps 1-8 as unchanged/shared and steps 9-11 as consumer-specific.

## 6. Proposed module/interface boundary

Proposed module name (repository-consistent, not forced to any name suggested in the activating prompt): **`src/pcae/core/hpac_pawa_recognition_core.py`**, alongside the existing `hpac_pawa_*` family (`hpac_pawa_agent_exclusion.py`, `hpac_pawa_helper_protocol.py`, `hpac_pawa_schemas.py`). It would carry the same "non-agent-importable consumer-inventory fence" docstring discipline as `hpac_pawa_agent_exclusion.py` (§1.3) — ordinary agent/runtime/CLI/plugin code SHALL NOT import it; only the legacy factory and the helper's in-process recognition code may.

Proposed primary entry point (signature only — **not implemented in this phase**):

```python
def recognize_protected_anchor(
    *,
    protected_root: Optional[Path] = None,
    configured_agent_identity_source: Optional[AgentIdentitySource] = None,
    topology_probe: Optional["TopologyProbe"] = None,
) -> RecognizedAnchorFacts:
    """Runs HPAC-PAWA-001 §33 steps 1, 4, 5, 6, 2, 3, 7, 8 exactly as
    currently implemented in `_run_recognition_sequence`, minus step 9
    (the admin-writer-specific factory-consumer allowlist, which stays in
    the legacy factory) and steps 10/11 (mint + audit, consumer-specific).
    Read-only except for step 8's self-contained create/write/fsync/unlink
    write probe. Raises the same closed `PawaError`-shaped failure codes
    used today (`protected_root_missing`, `protected_root_untrusted`,
    `agent_principal_unknown`, `agent_has_protected_write_authority`,
    `descriptor_*`, `current_context_is_agent`, `write_probe_failed`).
    Fail-closed: no code path returns a partially-recognized result."""
```

`RecognizedAnchorFacts` is the proposed neutral rename of today's `_RecognizedAnchor` fields (§1.1): `root`, `live_root_identity[_digest]`, `anchor_id`, `installation_id`, `generation`, `configured_agent: ConfiguredAgentAuthorityIdentity` — ordinary descriptive data (§7), not a capability.

Consumers:
- **Legacy factory** (`hpac_protected_admin_writer.py`): `_run_recognition_sequence` is refactored (in a future, separately-authorized implementation phase) to call `recognize_protected_anchor(...)` for steps 1-8, then perform its own step 9 (factory-consumer allowlist) + build `_RecognizedAnchor` (or adopt `RecognizedAnchorFacts` directly) + steps 10/11 (mint + audit) exactly as today.
- **Helper** (future implementation, not this phase): the exec'd helper process calls `recognize_protected_anchor(...)` once, in its own interpreter, immediately after exec and before accepting any peer connection (§9), obtaining a real `ConfiguredAgentAuthorityIdentity` to thread into `authenticate_peer(..., configured_agent=facts.configured_agent)` — closing the exact gap Phase 150E left open — then performs its own step 9′ (not yet specified; out of this phase's scope) before operation dispatch.

## 7. Input/output schema and trust classification

**Inputs** (all optional test-only seams; every production call passes none of them, using the canonical live resolution path):

| Input | Trusted? | Why |
|---|---|---|
| `protected_root` | test-seam only | production always resolves the one canonical root; a caller override is never trusted in production (matches today's `_run_recognition_sequence` signature) |
| `configured_agent_identity_source` | test-seam only | production always uses live `pwd`/`os.getgrouplist` resolution |
| `topology_probe` | test-seam only | production always uses `_real_topology()` |

**Output** (`RecognizedAnchorFacts`): ordinary descriptive data (§F). Every field is either a filesystem-derived identity fact (`root`, `live_root_identity[_digest]`, `anchor_id`, `installation_id`, `generation`) or the resolved `ConfiguredAgentAuthorityIdentity` (itself already an existing, frozen, non-authoritative dataclass per `hpac_pawa_agent_exclusion.py`). None of these fields is a capability, token, or seal; none can be redeemed for a mutation; possessing a `RecognizedAnchorFacts` instance grants nothing beyond "here is what was true about the protected anchor and the configured agent at the moment this function returned."

## 8. Result-object semantics (item F)

`RecognizedAnchorFacts` is **ordinary descriptive data**, not process-local trusted evidence. It requires no same-interpreter trust seal: nothing forged or monkeypatched at the *result* layer can grant authority, because the object itself never authorizes anything — every consumer (legacy factory step 9-11, future helper step 9′-11) still independently re-validates currentness and, for the legacy factory, still independently mints its capability through the existing seal-gated `HPACStoreAuthority` machinery untouched by this proposal. This avoids the previously-rejected same-interpreter Python trust model (class identity, private constructor naming, module globals, hidden seals, mutable registries) entirely, because the *object* was never the security boundary in the current design either — the security boundary is the OS-level facts (`os.stat`, kernel peer credentials, `O_EXCL|O_NOFOLLOW`) that produced the object's fields, which remain independently re-checked at each consumption point downstream (Model E's own `_require_currentness` re-validates at recognition time, not just at mint time — a pattern this proposal preserves, not weakens).

## 9. Currentness / TOCTOU rules

`recognize_protected_anchor` must be called fresh, uncached, at each admission point — exactly as `_run_recognition_sequence` already is today (it is re-run on every `production_writer()`/`certification_writer()` call, never memoized). For the future helper implementation: recognition must run once per exec'd one-shot helper process, after exec and **before** the channel is opened to accept a peer connection, and its resulting `configured_agent` must be threaded into `authenticate_peer` for **that same process's single connection** — never cached across helper process invocations (each one-shot helper process already exits after one operation, per the existing one-shot design, so no cross-invocation caching risk is introduced). Operation dispatch (Model E's `perform_recognized_*` functions) must continue to independently re-validate currentness via `_require_currentness` exactly as today; this proposal does not relax that. A configured-agent identity recognized before helper launch (i.e., resolved by an earlier admin action) must never be treated as authoritative after launch — this is guaranteed by construction, since the proposed function is stateless and any prior caller's result is never passed across a process boundary; each process performs its own live resolution.

## 10. Helper admission sequencing (future implementation; not this phase)

1. Helper is `exec`'d (existing `execute_verified`/`os.execve` anti-TOCTOU path, unchanged).
2. Helper calls `recognize_protected_anchor()` in its own interpreter (REQ-031) — obtains `RecognizedAnchorFacts`, including a live `ConfiguredAgentAuthorityIdentity`.
3. Helper opens its one-shot channel and accepts the peer connection (unchanged).
4. Helper calls `authenticate_peer(conn, deployment_owner_uid=..., configured_agent=facts.configured_agent)` — now supplying the real identity instead of `None` (closing the Phase 150E gap), evaluating both REQ-042 conjuncts.
5. Only after both (2) and (4) succeed does operation dispatch (`handle_one_request`/`CLOSED_DISPATCH_TABLE`) run, itself still gated by Model E's own currentness re-check.

This sequencing is proposed, not implemented, in this phase.

## 11. Threat/adversarial matrix

| Threat | Fail-closed outcome under the proposed architecture |
|---|---|
| Forged module names | Unaffected — step 9 (caller-module check) stays in the legacy factory only; the shared module has no caller-identity concept to forge |
| Monkeypatched module globals | The shared module holds no mutable trust-bearing global (no seal, no registry); nothing to monkeypatch into an authority |
| Arbitrary externally-constructed recognition objects | `RecognizedAnchorFacts` is inert descriptive data — constructing one by hand grants nothing, since no downstream consumer treats possession of the object as authority; each consumer still independently re-validates currentness and, for the legacy factory, still independently mints through the untouched seal-gated `HPACStoreAuthority` path |
| Symlink/path substitution | Unchanged from today's steps 1/4/5 symlink-rejection logic, reused verbatim |
| Stale recognition after configured-agent state changes | Prevented by §9's no-caching rule; each call re-resolves live |
| `configured_agent=None` | The proposed function never returns a `None` `configured_agent` on success — it raises `agent_principal_unknown` instead (same as today's step 2); a future helper caller that supplies the function's real return value can no longer accidentally pass `None` the way the launcher does today |
| Mismatched configured-agent identity | Detected by step 7 (`current_context_is_agent`) and by `authenticate_peer`'s existing REQ-042 conjunct 2, unchanged |
| Peer UID/PID valid but configured-agent recognition invalid | `recognize_protected_anchor` raising before `authenticate_peer` is ever reached (per §10's ordering) means operation dispatch never occurs |
| Valid configured-agent declaration but untrusted provenance | Steps 2/5/6's existing provenance/digest/`{device,inode}` checks reject this, unchanged |
| Helper launcher bypass of recognition | Not itself prevented by this architecture alone — it is a wiring/implementation-phase concern (§10 step 2 must actually be called); this architecture defines the boundary, a future implementation phase and its tests must prove the call site is unconditional |
| Operation dispatch reached without successful recognition | Same as above — an implementation-phase concern; this architecture's contribution is making a genuine, non-forgeable recognition result available so that guarantee becomes implementable at all |

## 12. Model E compatibility proof

Model E's three authority classes (`HelperAdminMutationAuthority`, `HelperCertificationWriteAuthority`, `HelperPresentationEvidenceAuthority`, `hpac_pawa_helper_writer_authority.py`) remain untouched by this proposal: the shared recognition module has no relationship to them (§1.1 confirms zero references either direction), they remain distinct sealed `__slots__` classes gated by `_HELPER_AUTHORITY_SEAL`, never subclasses of `HPACWriterCapability`, never exported outside the helper process — independently reconfirmed against current source in this phase (`test_model_e_authority_classes_remain_distinct_sealed_and_exact_type_checked`). This architecture does not collapse them, does not add a fourth family, and does not change their construction/recognition/dispatch logic in `hpac_pawa_helper_operations.py`/`hpac_pawa_helper_store_adapter.py`.

## 13. Foundation-separation statement

**FOUNDATION BLOCKER UNCHANGED.** The proposed shared recognition module (steps 1-8) does not reference `HPACStoreAuthority`, `_ensure_root`, `_validate_production_boundary`, or `_bind_configured_agent_identity` anywhere (§1.1, confirmed by direct source inspection of the exact region that would be extracted) and would not need to: recognition (proving who the configured agent is, and that the anchor is trustworthy) is architecturally and today already independent of capability minting (proving a caller may write, and issuing the token) — the legacy factory currently performs them as two separable phases (steps 1-9 = recognition, then a separate mint step outside this function). This phase's proposal preserves and formalizes that separation; it neither repairs nor worsens the separate, still-open N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL blocker (the privileged helper's real write path still cannot pass `_validate_production_boundary` without the legacy factory's `_bind_configured_agent_identity` seal, exactly as that phase found). No interaction between the two was discovered.

## 14. Contract handling

**Conforms without normative contract change.** HPAC-PAWA-HELPER-001 v5.0's REQ-031/032/033 already require exactly the behavior Model B enables (in-helper steps 1-8, no import of the forbidden module); HPAC-PAWA-001 v4.0's §33/v2.0 note already anticipates steps 1-8 being shared, unchanged infrastructure while steps 9-11 diverge per consumer. No contradiction was found between the two contracts' text and Model B's shape. No contract version evolution is proposed or required by this architecture.

## 15. Test/evidence requirements (this phase's own executable proof)

Governed Fast Green (`pcae phase fast-green-attribution --phase-id 150F`): baseline `81985989c3d49f8aa52cf999168c07d4ba8035d8` (this phase's own entry commit == origin/main at preflight). Initial isolated run reported one attributable failure, `tests/test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record` — a test unrelated to any file this phase touches (it exercises `shell_gate.py`'s audit-directory tamper detection against ambient filesystem state, not this phase's docs/tests/task files). Reproduced locally four times in isolation, all four passed (7-28s each, timing-sensitive); a governed isolated single-node rerun (`--rerun-node`) also passed. **Final: `attributable_failures: []`.** No test skipped, xfail'd, or deleted to obtain this result — the node was independently re-executed under the tool's own excluded-environment-failure mechanism and returned green on its own, not excluded by exception.

New suite: `tests/test_n16_5_f_5_tb_helper_admission_recognition_shared_infrastructure_architecture.py` (14 tests, all passing), covering items 1, 2, 3, 8, 9, 10, 11 of the activating prompt's TEST/EVIDENCE REQUIREMENTS list directly against current source (items 4-7, which concern the *proposed, not-yet-existing* module's absence of mutation/authority/circularity, are answered here by inspecting the exact current-source region that would become that module — an honest substitute for testing code that this phase deliberately does not write):

1. Helper does not perform complete configured-agent recognition today — `test_helper_launcher_still_has_no_configured_agent_resolution`, `test_helper_entrypoint_still_has_no_in_helper_recognition`.
2. Protected-admin-writer recognition path exists and its dependencies are identified — `test_recognition_sequence_has_the_eleven_documented_steps`.
3. Helper cannot safely import the full admin-writer module as the trust solution — `test_helper_modules_still_forbidden_from_importing_admin_writer` (REQ-033 fence still holds).
4/5. Candidate shared-extraction region has no mutation primitive / no writer-authority import — `test_steps_1_through_8_contain_no_mutation_or_write_authority_primitive`.
6. No helper→agent/admin-authority trust inversion in the candidate dependency graph — `test_admin_writer_module_does_not_import_helper_writer_authority`, `test_hpac_pawa_agent_exclusion_has_no_mutation_primitive_or_writer_authority_import`.
7. No circular dependency between the two consumers via the shared dependency — same two tests above (neither direction imports the other's authority module).
8. Model E authority module unchanged — `test_model_e_authority_classes_remain_distinct_sealed_and_exact_type_checked`.
9. Contract versions unchanged — `test_contract_versions_unchanged_by_this_phase`.
10. Runtime/PB/POL state unchanged — no code touches any runtime/PB/POL module in this phase (verified by `test_this_phase_changed_zero_production_or_contract_files`, which covers all of `src/pcae/**`).
11. N-16-6/N-16-7 untouched — `test_n16_6_and_n16_7_artifacts_absent_from_this_phase` plus manual confirmation no file under this phase's diff mentions either.

Adversarial architecture checks are addressed narratively in §11 (threat matrix), since the module under discussion does not yet exist to test adversarially in code; each row states the specific fail-closed outcome the architecture guarantees or, where it is an implementation-phase concern, says so explicitly.

## 16. Independent-verification requirements (for a future IV phase)

A future independent verification of this architecture (before or alongside the implementation phase it authorizes) should re-derive: (a) that steps 1-8 as implemented today truly contain no authority-bearing primitive (re-run/extend this phase's AST-based tests against the then-current source); (b) that the eventual concrete `hpac_pawa_recognition_core.py` module, once implemented, is byte-for-byte behaviorally equivalent to today's steps 1-8 for the legacy factory's own call site (no semantic drift introduced by extraction); (c) that the future helper wiring genuinely calls the shared function unconditionally before any operation dispatch (an implementation-phase claim this architecture phase cannot itself prove, since no such wiring exists yet).

## 17. Implementation-phase file allowlist proposal (for a future, separately-authorized phase)

Proposed allowlist for the narrow follow-on implementation phase (derive the exact final list at that phase's own preflight from then-current source):
- `src/pcae/core/hpac_pawa_recognition_core.py` (new)
- `src/pcae/core/hpac_protected_admin_writer.py` (refactor `_run_recognition_sequence` to call the new module for steps 1-8; keep steps 9-11 as today)
- `tests/test_hpac_pawa_recognition_core.py` (new, unit tests for the extracted module in isolation)
- A narrow regression suite confirming the legacy factory's own behavior is unchanged after the refactor (byte-for-byte failure-code parity for every existing failure scenario)

Explicitly **not** in that future phase's scope (per this architecture and the activating prompt's own non-goals): any helper-side wiring of `authenticate_peer`/the launcher/step 9′ (a separate, still-undefined normative step); any foundation (`hpac_foundation.py`) repair; any Model E redesign; any contract version change; any runtime/PB/POL change; N-16-6/N-16-7.

## 18. Explicit no-go confirmations

- No FIDO2/RHAMP/protected-presentation behavior changed.
- No PB, POL-005, or runtime state/capability changed.
- No first external-effect path created.
- N-16-6 not touched.
- N-16-7 not touched.
- Nothing published/released/versioned/tagged.
- No deployment-packaging change.
- No unrelated contract modified.
- `HPACStoreAuthority` foundation semantics not repaired (confirmed §13).
- No same-process Python trust seal reintroduced (confirmed §8).
- No held/disowned commit (`6c7f5cf4`, `2b8ad2aa`, `72cdba16`, `d0b2a75a`) inspected, cherry-picked, merged, or referenced as canonical history.
- Zero `src/pcae/**` and zero `docs/contracts/**` bytes changed by this phase (confirmed by `test_this_phase_changed_zero_production_or_contract_files`, pinned to this phase's own entry commit `81985989c3d49f8aa52cf999168c07d4ba8035d8`).
- No test skipped, xfail'd, or deleted to obtain green.
- `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — this phase's central architecture claims, evidence document, and test suite were authored directly by the primary operator; one bounded, read-only research fork was used to reconstruct current source/contract facts (no `src/pcae/**` write access, no commit/push/finalization authority, no lifecycle CLI use), and the primary operator independently re-verified its central factual claims (line numbers, contract text, import graphs, foundation-boundary code) against live source before relying on them, and performed all lifecycle mutation, finalization, commit, and push directly.

## 19. N-16-5 disposition

**NOT CLOSED.** This phase is architecture/contract-freeze only. It does not implement REQ-031's in-helper recognition, does not wire `authenticate_peer`'s `configured_agent` parameter, and does not repair the separate foundation blocker. It removes the structural reason Phase 150E's narrow repair attempt was blocked (the absence of any safe way to share steps 1-8) by defining a concrete, contract-conformant boundary — but defining the boundary is not implementing it.

## 20. Recommended next governed phase

A narrow, separately-authorized implementation phase realizing exactly §17's allowlist: extract steps 1-8 into `hpac_pawa_recognition_core.py`, refactor the legacy factory to call it (behavior-preserving), and — if explicitly authorized in that phase's own scope — wire the helper side (launcher calling the new module before channel accept, threading its result into `authenticate_peer`, defining the still-unspecified step 9′). N-16-5 remains **NOT CLOSED** until that implementation exists and is independently verified. N-16-6/N-16-7 remain untouched and out of scope for that next phase too.
