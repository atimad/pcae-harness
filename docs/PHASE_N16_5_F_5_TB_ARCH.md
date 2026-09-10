# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1 (alias N16-5-F-5-TB-ARCH) — N-16-5 Privileged Production Authority Trust-Boundary Architecture: Stronger-than-Same-Interpreter Consumer Authenticity

**Status: COMPLETE — architecture defined. Contract-evolution verdict: B —
REQUIRES HPAC-PAWA-001 CONTRACT EVOLUTION (see §31 / §21).**
**F-5-B2: BLOCKED pending stronger-boundary contract + implementation.
F-5: CERTIFICATION BLOCKED. N-16-5: NOT CLOSED. N-16-6 / N-16-7: OPEN /
UNTOUCHED (N-16-7 strictly last).**

This is an **architecture-only** governed phase. It designs and adjudicates a
trust boundary; it implements nothing, mutates no protected host state,
performs no ceremony, and amends no frozen contract. Runtime posture is
unchanged throughout: `not_implemented` / `Observed` / `observe` /
`unavailable` / 0 plugins / 0 capabilities; the first governed runtime
external effect remains ABSENT / UNREACHABLE.

---

## 0. Governance / phase identity

### 0.1 Repository state at phase entry

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `089817c8dfa0293136941c3c07946eac38612e90` |
| `origin/main` | `089817c8dfa0293136941c3c07946eac38612e90` (identical; fetched at entry) |
| `origin/main..HEAD` | empty (0 commits) |
| Working tree | clean at entry |
| Conflicting active governed phase | none — the only active task was the idle placeholder `20260909-2322-idle-awaiting-explicit-authorization-for-the-n16-5-f-5-b2r2-impl-successor-architecture-phase…`; phase queue empty; no handoff newer than the latest completed phase report other than the informational 2026-09-04 "Switching agents" handoff |

### 0.2 Predecessor

| Field | Value |
|---|---|
| Alias | **N16-5-F-5-B2R2-IMPL** |
| Canonical Phase ID | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1` |
| Predecessor HEAD (finalizing commit) | `089817c8` (`Phase … (N16-5-F-5-B2R2-IMPL): retitle closed phase task with canonical "Phase <id> (alias)" prefix`); the substantive adjudication commit is `c83f001d` |
| Predecessor completion — canonical artifacts | `PROJECT_STATUS.md` "## Current Phase" = this predecessor, **STATUS: COMPLETE — BLOCKED**; `.pcae/phase-completion-metadata.json` `status = "completed"`, `phase_id` matches; `.pcae/phase-completion-report.md` staging header matches; governed task `tasks/done/20260909-2302-n16-5-f-5-b2r2-impl-…md` `## Status: done`; canonical report `docs/PHASE_N16_5_F5B2R2_IMPL.md` |

### 0.3 CPIPC-valid successor derivation

Independently derived via `pcae.core.phase_id` (CPIPC-001 v1.0, the sole
authority per CPIPC-REQ-018), **not** taken from any precomputed value in the
authorizing prompt:

```
candidate = <predecessor phase id> + exactly one ".1" subphase segment
          = 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1
```

| CPIPC check | Result |
|---|---|
| `is_valid(candidate)` | `True` |
| `format(parse(candidate)) == candidate` | `True` — exact canonical textual representation, no normalization drift |
| `compare(predecessor, candidate)` | `less` — candidate is a **strict** successor |
| `same_series(predecessor, candidate)` | `True` — series `149` |
| `same_branch(predecessor, candidate)` | `True` — branch `O` |
| Successor-segment count | predecessor 47 subphase segments → candidate 48; exactly one appended segment `(1, "")` — the canonical first-child |
| Uniqueness / collision | `git log --all` for the exact dotted string: **no match**; `grep -rF` over `docs/`, `tasks/`, `.pcae/`: **no match** |
| Conflicting active governed phase | none (§0.1) |

Recorded in PCAE authoritative artifacts by this phase: the active task title
(`tasks/active/20260910-0222-…md` `## Title`), `PROJECT_STATUS.md`
"## Current Phase", `.pcae/phase-completion-metadata.json` `phase_id` /
`phase_title`, and the staging `.pcae/phase-completion-report.md`. Alias
**N16-5-F-5-TB-ARCH** is display-only; it is written hyphenated in every
governed identity source so the CPIPC token scanner
(`pcae.core.phase_id.scan_tokens`, greedy `[0-9]+[A-Za-z]+`) extracts no stray
phase token from it (`feedback_cpipc_alias_token_trap`).

---

## 1. Authoritative predecessor finding (carried forward, not re-adjudicated)

The predecessor **N16-5-F-5-B2R2-IMPL** concluded, and this phase adopts as its
starting axiom:

> The frozen HPAC-PAWA-001 consumer-authenticity property is **UNSATISFIABLE
> within the current same-process Python interpreter boundary**, for all four
> privileged factories, under every design shape considered (cache-based,
> cache-free, or conventional encapsulation of either). This is a
> same-interpreter, standard-library capability limitation
> (`gc.get_objects()` / `gc.get_referrers()` require no reference chain), not a
> coding defect fixable by better hiding of state.

Concretely (predecessor PoCs `tests/test_phase_n16_5_f5b2r2_impl.py`, 3/3):

1. Direct mutation of the module-level `_PINNED_CODE_OBJECTS` /
   `_PINNED_TRUSTED_MODULES` / `_CODE_OBJECT_KEEPALIVE` dicts (ordinary,
   underscore-by-convention only) still mints a genuine `ProductionWriterHandle`.
2. A trust dict held **only** as a local closure variable — never bound to any
   module-level name, never returned — is still located and mutated by
   `import gc; gc.get_objects()` with **zero reference chain** to the closure.
3. The prompt's own preferred cache-free alternative (re-derive trust from
   `vars(module)` every call) is **also** unsafe: ordinary code can `exec()` a
   new function into an already-imported trusted module's `__dict__`, and a
   fresh-every-call scan then legitimately recognizes it.

**Architectural conclusion carried forward:** Python-language privacy and any
interpreter-visible mutable state MUST NOT be the final authority boundary for
the four privileged factory families. Iterative "hide the dict / hide the
closure / hide the object" patching is abandoned as a dead end.

**Historical governance integrity preserved exactly** (no retroactive
reinterpretation): `N16-5-F-5-B2` — NOT VERIFIED / BLOCKED; `N16-5-F-5-B2R-IV`
— NOT VERIFIED / BLOCKED; `N16-5-F-5-B2R2-IMPL` — COMPLETE — BLOCKED; the
delegated `.3` finalization / commit / push — UNAUTHORIZED.

---

## 2. Problem statement

`src/pcae/core/hpac_protected_admin_writer.py` is the single non-agent-importable
production module (HPAC-PAWA-REQ-084) that mints privileged authority for four
factory families:

| # | Factory symbol | Authority output today | HPAC-PAWA clauses |
|---|---|---|---|
| 1 | `production_writer(...)` | full `PRODUCTION` `HPACWriterCapability` (bounded §42 administrative mutations) | §33, §36, §41–§44 |
| 2 | `certification_writer(...)` | single-use certification-lifecycle `PRODUCTION` `HPACWriterCapability` over the closed five-role allowlist | §33A, §38A, §42B, §68A, PAWA-INV-13 |
| 3 | `recognized_certification_read_authority(...)` | `CertificationReadAuthority` handle wrapping a recognized read-only `HPACStoreAuthority` + one ceremony entry | §33B, §38B, §42D, §68B, PAWA-INV-14 |
| 4 | `mint_protected_presentation_evidence_writer(...)` | evidence-writer capability for `HPAC-PRESENTATION-EVIDENCE/2.0` | §42B / HPAC-PAWA-REQ-248, HPAC-PPA-REQ-041 |

All four run the **§33 recognition sequence** (11 steps) or a superset (§33A /
§33B reuse §33 steps 1–9 verbatim). Steps 1–8 are **OS-level**: canonical
protected-root resolution and symlink rejection; live `HPAC-PAWA-AGENT-EXCLUSION/1.0`
resolution against the OS account database; `_effective_write_access` /
`_ancestor_chain_safe` against the configured-agent identity; `{device,inode}`
root-identity binding; descriptor ownership/mode/digest/`state==ACTIVE`;
current-generation match; the not-configured-agent live-euid check; and the
`O_EXCL | O_NOFOLLOW` positive write probe under `.authority/`.

**Step 9 — "verify the calling module is an authorized factory consumer" (§32,
§38) — is the sole in-process, Python-identity conjunct.** It is implemented by
`_detect_caller_module` → `_verified_production_caller_name`, backed by the
`_PINNED_*` module-level dicts. This is the mechanism the predecessor proved
cannot be made sound in a shared interpreter.

Two independent failure modes make step 9 (and therefore the whole sequence)
unsound in-process:

- **F-A — recognition bypass.** Ordinary in-process code that can
  `import pcae.core.hpac_protected_admin_writer` can mutate the `_PINNED_*`
  state, `exec()` code into the module's own `__dict__`, or reach any needed
  object via `gc`, and thereby pass step 9 (or skip the sequence entirely and
  fabricate the handle).
- **F-B — authority exfiltration.** Even a *perfectly* recognized legitimate
  caller receives a Python object (`HPACWriterCapability` /
  `ProductionWriterHandle` / `CertificationReadAuthority` /
  `HPACStoreAuthority`) that lives on the heap of an interpreter shared with
  attacker-controlled code. `gc.get_objects()` enumerates it; `_seal` /
  `_authority_seal` identity checks are defeated by handing the attacker the
  same object. `__reduce__` raising stops serialization but not in-process
  capture.

The contract's **trust root is already correct**: HPAC-PAWA-REQ-010 / REQ-300
fix it as *"OS filesystem write authority on the out-of-band-provisioned
`<HPAC_PROTECTED_ROOT>` … the identical trust root HBDC-001 v1.2 froze …
'Real security boundary: OS filesystem write permission on the Protected Root,
never an in-process check.'"* HPAC-PAWA-REQ-020 already places *"the agent
process"* in the attacker-controlled set and requires the attacker MUST NOT be
able to mint a `PRODUCTION` capability. The defect is that the **implementation
delivers authority as an in-process object and enforces consumer identity with
an in-process check**, which the frozen trust root never sanctioned and the
predecessor proved cannot hold.

---

## 3. Current same-process boundary failure (reconstructed)

Reconstructed from primary source at HEAD `089817c8`:

- `src/pcae/core/hpac_protected_admin_writer.py:521-523` — `_PINNED_TRUSTED_MODULES`,
  `_PINNED_CODE_OBJECTS`, `_CODE_OBJECT_KEEPALIVE`: bare module-level
  `dict`s, underscore-prefixed only. No access control. `import`-reachable.
- `:622-663` `_verified_production_caller_name` — requires
  `frame.f_globals is pinned_module.__dict__` **and**
  `id(frame.f_code) in pinned_codes`. Both operands are ordinary objects:
  `sys.modules[name].__dict__` is directly referenceable, and `pinned_codes`
  is a module-level dict an attacker can overwrite before first-verified-use
  (or after, holding `_PIN_LOCK` is no barrier — it is also module-level).
- `:665-717` `_detect_caller_module` — walks `inspect.stack()`, reads
  `frame.f_globals["__name__"]` (predecessor B2R-IV: ordinary caller-writable
  dict key), then calls `_verified_production_caller_name`.
- `:971` `ProductionWriterHandle`, `:1934` `CertificationWriterHandle`,
  `:2338` `CertificationReadAuthority` — plain Python objects; a
  `_factory_seal is _PRODUCTION_WRITER_FACTORY_SEAL` identity check
  (`:2381`) gates construction, but `_PRODUCTION_WRITER_FACTORY_SEAL` is
  itself a module-level import (`:49`) reachable by any code that imports
  the module.

The predecessor's three PoCs (§1) demonstrate that **no pure-Python
technique** — name-mangling, `MappingProxyType`, `WeakValueDictionary`,
class-private attributes, closure capture, cache elimination — removes the
`gc`-reachability of authority-bearing state or objects from same-interpreter
code. The interpreter's own reflective capabilities (`gc.get_objects`,
`gc.get_referrers`, `sys._getframe`, `module.__dict__` mutation, `exec` against
an arbitrary globals mapping) are the ceiling.

---

## 4. Threat model

**Trusted computing base (inherited from HPAC-PAWA-001 §8, HBDC-001 §18):**
the OS filesystem protection model for `<HPAC_PROTECTED_ROOT>`; the OS account
/ process-identity subsystem; the OS kernel; a non-hostile OS root/admin
**within** the protected-root boundary. A fully compromised OS root/admin
boundary is **out of scope** (§26 below) unless a parent contract says
otherwise.

**Adversary capabilities (HPAC-PAWA-REQ-020, extended for this phase):** the
attacker MAY control repository content; the PCAE agent process and any code it
loads (including malicious plugins); import state, `sys.modules`, module
`__dict__`s, module-level mutable state, closures, the GC object graph;
environment variables, `argv`, `cwd`, `PATH`; writable user configuration
(`~/.config/pcae/**`); task / session / Git metadata; `--agent-id`. On a
single-account host the attacker additionally runs as the same UID as any
would-be privileged process.

**The attacker MUST NOT be able to:** mint any `PRODUCTION`
`HPACWriterCapability` or certification capability; obtain a recognized
`HPACStoreAuthority` (read or write); write the `HumanPrincipalRegistry`,
RHAMP counter state, or any protected artifact under `<HPAC_PROTECTED_ROOT>`;
enter `run_protected_presentation_ceremony()` with a recognized authority;
manufacture presentation evidence, a human APPROVE/REJECT, a Gate-5 result, a
PB/RE/policy decision, a runtime capability, a `DispatchEnvelope`, or any
external effect.

| ID | Threat | Same-process status today | Selected architecture (§7) disposition |
|---|---|---|---|
| **T1** | Ordinary same-interpreter Python code in the main PCAE process | **NOT MITIGATED** (F-A, F-B) | **Mitigated** — no privileged object or state exists in the main interpreter; the privileged operation and its recognition run in a separate OS process the attacker's principal cannot be, and cannot inject code into |
| **T2** | Malicious plugin code loaded into the main PCAE process | **NOT MITIGATED** | **Mitigated** — same as T1; plugins never share an address space with the recognition/mint |
| **T3** | Accidental / hostile `import` or module-object manipulation, `sys.modules` poisoning | Partially (provenance check) but defeated by F-A | **Excluded from the authority path** — the helper is `exec`'d, not imported; the main process never imports the writer module (§39 guard, strengthened) |
| **T4** | Caller-controlled environment / `argv` / `cwd` / inherited fds | Partially | **Mitigated** — closed minimal env allowlist for the helper (HPAC-PPA-REQ-032 pattern); no authority selector, response, or path in env/argv; unknown env fails closed |
| **T5** | Copied / lookalike package or module resembling an authorized consumer | Partially (`_expected_source_path`) but F-A dominates | **Mitigated** — helper executable identity is pinned by out-of-band install + `helper_sha256`, validated same-file-object before exec (HPAC-PPA-REQ-029/030); a lookalike is a different file |
| **T6** | Writable application source files | **NOT MITIGATED** (attacker edits repo, runs in-process) | **Mitigated** — helper bytes are out-of-band, admin-owned, agent-unwritable; repo edits do not change the helper |
| **T7** | Compromised unprivileged PCAE user account (single-account host) | **NOT MITIGATED** | **Fail-closed, not mitigated** — on a single-account host the two-principal topology is absent → REAL issuance **ineligible**, no authority minted (§61 / PAWA-INV-7, preserved). Genuine protection requires the two-principal deployment |
| **T8** | Spoofing the privileged helper / service (attacker starts a fake one) | n/a today | **Mitigated** — the *launcher* verifies the helper (byte hash, owner/mode, no-symlink, same-file exec); a fake helper is not the verified object. Conversely a fake *launcher* cannot obtain authority: the helper independently re-runs §33 OS recognition and checks its peer credential |
| **T9** | IPC replay | n/a today | **Mitigated** — CSPRNG ≥256-bit nonce per request, private one-shot parent/child channel, exact request/response binding (HPAC-PPA-REQ-034/037) |
| **T10** | Stale request / session | n/a today | **Mitigated** — request carries expiry + certification-session binding; helper validates freshness and session membership; restart-dead |
| **T11** | Process crash / response uncertainty after a mutation | in-process: mutation + return are one call | **Bounded** — explicit state-transition model (§21); response loss is never proof the mutation did not happen; no auto-retry |
| **T12** | Test fixture impersonating production authority | disclosed one-underscore seams, guarded | **Preserved** — a test helper speaking the protocol is still not the verified production executable; the fixture seam guard is carried into the helper design |
| **T13** | Installer / launcher / evidence-writer / approver confusion | conflated risk | **Mitigated by explicit role separation** (§16): deployment owner ≠ installer ≠ launcher ≠ evidence writer ≠ certification authority ≠ human approver |
| **T14** | Privilege escalation via generic operation parameters | n/a (no protocol today) | **Mitigated** — narrow typed operation vocabulary; no arbitrary path / expression / role / command (§11, §28) |
| **T15** | Compromised protected helper executable or its config | trusted (TCB) | **Out of scope** — equivalent to root compromise within the protected boundary (§26); bound claim only |

---

## 5. Existing PCAE protected-boundary inventory (§6D reuse analysis)

| Boundary | What it establishes | Process model | Reusable for the four factories? |
|---|---|---|---|
| **HPAC-PAWA-001 §4 trust root** (`<HPAC_PROTECTED_ROOT>` filesystem authority) | deployment-owner recognition = OS filesystem write authority on an out-of-band-provisioned root, agent-unwritable | filesystem ACLs | **YES — reused unchanged as the trust root.** Already correct; the gap is delivery, not the root |
| **HBDC-001 v1.2** / `scripts/hatp_deployment_binding_admin.py` | structurally identical HATP Class-B protected-root writer boundary — *"never an in-process check"* | standalone admin script | **YES — precedent.** Same "standalone script, OS boundary" shape the four factories must adopt end-to-end |
| **HPAC-PPA-001 v1.0** protected-presentation helper | out-of-band immutable helper bytes + PAWA metadata registration; pre-launch integrity (no-symlink open, type/link/owner/mode/ACL, byte hash, exact `helper_sha256`, same-file-object validate-and-exec, no re-open gap); fixed one-shot local invocation, no shell/PATH/argv/cwd/env-selected helper; CSPRNG ≥256-bit nonce; private parent/child channel unavailable to the agent; canonical request/response binding; launcher never accepts caller-provided `approved=True`; fail-closed on crash/exit/malformed/timeout/nonce/binding mismatch; *"the helper process itself may not import or call the PAWA installer factory"*; *"Launch permission is not PAWA installation authority and not runtime dispatch authority"* | **out-of-process verified one-shot helper** | **YES — this is the reuse anchor.** The presentation ceremony already crosses the exact boundary the four factories need. HPAC-PAWA-REQ-308 explicitly notes *"HPAC-PPA-001 never fixed where the launcher's authority originates"* — that unfixed question is precisely this phase's subject |
| **`scripts/hpac_certification_admin.py`** → `pcae.core.hpac_certification_coordinator` (§38A, the sole authorized consumer of factories 2 & 3) | already a standalone, non-agent-reachable script run by the deployment owner under `sudo`/root | standalone script (but currently `import`s the writer module into its own interpreter) | **Partial** — the entrypoint shape is right; the defect is that it loads the mint logic in-process and hands the coordinator a Python authority object |
| `_PRODUCTION_WRITER_FACTORY_SEAL` / `_bind_configured_agent_identity` | in-process mint-trust-root + configured-agent binding for `_validate_production_boundary` | in-process | **NO for the trust decision** — this is exactly the in-process primitive that fails. Its *logic* (bind the configured-agent identity so the negative boundary keys off the agent principal, not root-under-sudo) is reused **inside the helper process** |

**Conclusion:** PCAE already contains a verified, IV'd out-of-process protected
boundary (HPAC-PPA-001) and a standalone admin-script precedent (HBDC-001).
The stronger boundary is a **generalization of the HPAC-PPA-001 one-shot
verified-helper pattern to the four privileged factory operations**, anchored
on the **unchanged** HPAC-PAWA-001 §4 filesystem trust root. **No second trust
root is introduced** (§27).

---

## 6. Candidate architectures — comparative analysis

### 6A. Dedicated protected helper process (persistent)

A long-lived helper process, started by the deployment owner (or an admin
service manager), owns privileged authority state and exposes the four
factories' operations over a local endpoint.

- Installation/provisioning: out-of-band, admin-owned bytes + PAWA metadata
  registration (HPAC-PPA-REQ-004 pattern). Process identity pinned by
  executable hash + owner/mode. Startup: admin action or the launcher on
  first request.
- Request authentication: private channel + OS peer-credential check
  (`SO_PEERCRED` on Linux, `LOCAL_PEERCRED` / `getpeereid` on macOS) — the
  peer must be the deployment-owner principal (or, on the two-principal
  topology, at least not the agent principal), **and** the helper
  independently re-runs the §33 OS recognition every request.
- Operation allowlist: the closed set of §42 mutation classes + the §42B
  five-role lifecycle writes + the §42D reads + one ceremony entry.
- Replay: per-request CSPRNG nonce; session binding; monotonic request ids.
- Lifecycle / crash recovery: systemd / launchd supervised; a crash loses
  only in-flight requests; restart re-derives all state from the protected
  root.
- **Cons:** a persistent privileged process is a standing attack surface
  (T15); it holds authority-bearing state across requests; upgrade/rotation
  needs a restart protocol; it is the largest new trust surface of the five.

### 6B. Protected local service / daemon (root/admin-owned, versioned protocol)

Like 6A but explicitly a root/admin-owned system service with a
socket at an admin-owned path, a service manager, and a versioned wire
protocol.

- Adds: filesystem-permissioned socket (`0700` dir, admin-owned); service
  manager as launch authority; protocol compatibility negotiation.
- **Cons:** strongest availability story but the **broadest** persistent
  privileged surface and the heaviest deployment/packaging burden;
  effectively a new privileged subsystem. Overkill for an operation that
  happens a handful of times per certification.

### 6C. Short-lived one-shot privileged process

A privileged process is `exec`'d **only** for one specific governed action and
terminates after completing or rejecting exactly one bounded operation.

- Launch authority: the standalone `scripts/hpac_certification_admin.py`
  (factories 2–4) / the standalone principal-admin script (factory 1),
  already the only authorized consumers, already run by the deployment owner.
- Executable provenance: out-of-band immutable bytes, `helper_sha256`
  pinned in PAWA metadata, validated same-file-object before `exec`
  (HPAC-PPA-REQ-029/030).
- Input channel: private parent/child pipe, not inherited by agent code;
  canonical request bytes only; closed minimal env.
- Operation binding: one typed operation per launch; the request binds the
  certification session, subject (principal/credential/proof), nonce, expiry.
- One-shot semantics: the process performs the §33 recognition **in its own
  interpreter**, performs the one mutation/read/ceremony-entry, emits typed
  evidence, exits. No authority object is ever returned to the caller.
- Replay resistance: nonce + session + expiry + single-use.
- **Pros:** **smallest persistent attack surface** (no standing privileged
  process); no cross-request authority state; upgrade = replace the bytes;
  crash semantics are simple (a crash before the commit point = no effect).
  Directly mirrors the IV'd HPAC-PPA-001 ceremony helper.
- **Cons:** per-operation process spawn cost (irrelevant at this call
  frequency); each launch re-runs full recognition (a feature, not a cost).

### 6D. Reuse of the existing HPAC-PPA-001 protected-helper architecture

Not a distinct mechanism — the recognition that 6C **is** the HPAC-PPA-001
pattern applied to the four factories. The presentation helper already crosses
this boundary for the APPROVE ceremony; the four factories adopt the same
launcher-verifies-helper + helper-verifies-peer + one-shot-typed-protocol
model, and factory 3's "one ceremony entry" becomes a direct hand-off to the
existing presentation helper rather than passing a Python `HPACStoreAuthority`.

### 6E. Other stronger local boundary

Considered and rejected as the primary mechanism:

- **C-extension opaque handle** (predecessor's alternative suggestion). A
  capability represented as an opaque non-Python-heap object. *Rejected as
  sufficient on its own:* it still executes the recognition in the shared
  interpreter (F-A survives — attacker code calls the C entrypoint after
  tampering with the inputs it reads), and a C object in-process can still be
  handed to the attacker (F-B survives for read-through use). It may be a
  **defense-in-depth adjunct** inside the helper but is not the trust
  boundary.
- **OS user-namespace / seccomp sandbox around the agent.** Reduces T1/T2 but
  does not create a *positive* privileged path; and PCAE must run ordinary
  agent code with broad ability. Out of proportion.
- **Network / cloud authority service.** Explicitly excluded — no necessity;
  introduces a remote trust root and transport (a §80.4 MAJOR trigger).

### Comparison matrix

Scored 1 (poor) – 5 (excellent) against the §7 criteria that discriminate:

| Criterion | 6A persistent helper | 6B daemon | 6C one-shot | 6E C-ext |
|---|---|---|---|---|
| 2. Prevents same-interpreter self-assertion | 5 | 5 | **5** | 2 |
| 3. Smallest new trust surface | 3 | 2 | **5** | 4 |
| 4. Reuses existing verified infrastructure | 3 | 2 | **5** (HPAC-PPA-001) | 2 |
| 5. No second trust root | 4 | 3 | **5** | 5 |
| 6. Bounded operation vocabulary | 4 | 4 | **5** | 3 |
| 7. No generic writer export | 4 | 4 | **5** | 2 |
| 8. Non-bearer authority | 3 (cross-request state) | 3 | **5** | 3 |
| 9. Process/session freshness | 4 | 4 | **5** | 2 |
| 10. Fail-closed | 4 | 4 | **5** | 3 |
| 11. Deterministic testability w/o REAL elevation | 4 | 3 | **5** | 3 |
| 12. Packaging/deployment story | 3 | 2 | **4** | 3 |
| 13. Upgrade/rotation | 3 | 3 | **5** (replace bytes) | 3 |
| 14. Crash/restart safety | 3 | 4 | **4** | 3 |
| 15. Auditable evidence | 4 | 4 | **5** | 3 |
| 16. Least privilege | 3 | 2 | **5** | 3 |
| 18. Mobile-only future compatibility | 4 | 4 | **4** | 4 |
| 19. No runtime external-effect enablement | 5 | 5 | 5 | 5 |
| 20. No N16-6/N16-7 coupling | 5 | 5 | 5 | 5 |

---

## 7. Selected architecture

**Selected: 6C — Short-lived one-shot privileged process, realized as a
generalization of the HPAC-PPA-001 verified-helper pattern (6D), anchored on
the unchanged HPAC-PAWA-001 §4 filesystem trust root.** 6E (C-extension /
in-helper hardening) is retained only as optional defense-in-depth **inside**
the helper.

### 7.1 Shape

```
main PCAE interpreter (agent, plugins, gates, CLI)
    — has NO privileged object, NO writer module import, NO channel to the helper

deployment-owner standalone launcher  (scripts/hpac_certification_admin.py ;
                                       principal-admin script for factory 1)
    — minimal; imports NO agent-reachable code
    1. builds the canonical typed request (operation, certification session,
       subject digests, CSPRNG nonce >=256b, expiry)
    2. resolves + integrity-verifies the fixed privileged-helper executable
       (no-symlink open, type/link/owner/mode/ACL, byte hash == helper_sha256,
       same file object used to exec — no re-open gap)
    3. creates a private parent/child channel NOT inherited by any agent code
    4. exec's the helper as a one-shot child, closed minimal env, no shell/PATH
    5. sends canonical request bytes; never sends approved=True / a result

privileged one-shot helper process  (out-of-band admin-owned bytes)
    — its own interpreter; loads ONLY its own minimal privileged code
    A. verifies its peer credential over the channel (SO_PEERCRED /
       getpeereid): peer is the deployment-owner principal (two-principal
       topology) — else fail closed
    B. runs the HPAC-PAWA-001 §33 recognition sequence steps 1..8 in-process
       (OS-level: root resolution, agent-exclusion, write-probe, descriptor,
       generation, not-configured-agent) — binding the configured-agent
       identity (the _bind_configured_agent_identity logic) so the negative
       boundary keys off the agent principal, not root-under-sudo
    C. replaces step 9 ("calling module is an authorized consumer") with:
       "this process was exec'd (not imported), its peer is the verified
       deployment-owner launcher, and the request is a well-formed member of
       the closed operation vocabulary bound to a valid certification session"
    D. validates the typed request: operation in the closed set; role in the
       closed five-role allowlist (factory 2); session/subject binding
       (principal active+not-revoked+mechanism-neutral, credential bound,
       proof matches session)
    E. performs EXACTLY ONE bounded action:
         factory 1: one §42 administrative mutation
         factory 2: one five-role certification-lifecycle write
         factory 3: the enumerated §42D reads and/or ONE ceremony entry
                    (hand off to the HPAC-PPA-001 presentation helper directly)
         factory 4: one HPAC-PRESENTATION-EVIDENCE/2.0 write
    F. writes issuance/lifecycle audit evidence under the protected root
    G. emits a canonical typed RESULT (evidence digest, decision, terminal
       code) over the channel — NEVER an HPACWriterCapability /
       HPACStoreAuthority / handle
    H. exits; the process (and any authority it held) is gone
```

### 7.2 Why this satisfies the core requirement (§5 of the prompt)

Ordinary PCAE code in the main interpreter:

- has **no authority-bearing state to mutate** — none exists in that process;
- **cannot forge a trusted consumer identity** — identity is now "I am the
  process that was `exec`'d by the verified launcher and my peer credential is
  the deployment owner", which same-UID agent code on a two-principal
  deployment cannot present, and which does not exist as any in-process
  token;
- **cannot instantiate equivalent authority** — the mint runs in a separate
  interpreter that loads no attacker code;
- **cannot impersonate the protected consumer** — the helper checks its peer,
  not a Python module name;
- **cannot bypass the boundary** — there is no in-process path; the only
  channel is the private pipe the launcher (not agent code) holds.

The design depends for final authority on **none** of: Python underscore
privacy; module / function name; `__module__` / `__package__` / `__file__`;
`inspect.stack()` textual identity; `sys.modules` keys; mutable module
globals; closure hiding; class-private state; in-process bearer-object
possession; filesystem path alone; digest consistency alone. It depends on
**OS process isolation + OS filesystem permissions + OS peer credentials +
out-of-band executable provenance** — the HPAC-PAWA-001 §4 trust root, made
the *sole* authority-delivery boundary.

Preserved: `FILE LOCATION != TRUSTED ORIGIN`; `HASH CONSISTENCY != PROVENANCE`;
`STRUCTURALLY VALID OBJECT != TRUSTED CANONICAL STATE`.

---

## 8. Key design principle — do not export generic writer authority

**Adjudication (prompt §8): the four-factory "writer/factory returns a
capability" abstraction is NO LONGER the correct production boundary.** The
privileged side (the helper) MUST own the mutation/read/ceremony-entry and
expose only operation-specific typed protocol commands. The main interpreter
(and even the launcher) receives only typed evidence/results.

Conceptually preferred and selected:

```
request bounded operation  ->  helper verifies peer + request + §33 OS recognition
                           ->  helper performs the exact permitted action
                           ->  helper returns evidence/result
```

Rejected:

```
caller asks for a privileged writer  ->  writer object returned  ->  caller invokes methods
```

This is a normative change to §36 / §37 / §33 step 9 / §42B / §42D / the §33B
handle model, and is the primary driver of the §31 "Verdict B" classification.

---

## 9. Consumer authenticity vs IPC peer authentication

The design does **not** conflate: local IPC access with trusted consumer
authenticity; a socket connection with authorization; process existence with
authorization; OS user identity with human identity; an OS peer credential
with informed human approval.

**A trusted production consumer is defined as the conjunction of:**

1. the process was **`exec`'d from the out-of-band-provisioned, admin-owned,
   integrity-verified privileged-helper executable** (byte hash + owner/mode +
   no-symlink + same-file-object exec) — not `import`ed, not a lookalike;
2. its **peer over the private channel presents the deployment-owner OS
   principal credential** (two-principal topology; single-account host →
   ineligible, fail closed);
3. the full **HPAC-PAWA-001 §33 steps 1–8 OS recognition** passes inside the
   helper (filesystem write authority against the configured-agent exclusion,
   descriptor trust, current generation, write probe, not-configured-agent);
4. the request is a **well-formed member of the closed typed operation
   vocabulary bound to a valid, current certification session** (§43A / §44A
   currentness).

No single one of these is sufficient. Weak signals explicitly **not** promoted
to authority on their own: a socket connection; `euid == 0` / `sudo` /
`SUDO_*`; an environment variable; a path; a module name; possession of the
channel fd alone (the helper still runs 1–4).

---

## 10. OS / process boundary model

| Entity | Identity / ownership |
|---|---|
| Untrusted / main PCAE process | runs as the **configured agent principal** (§9 / `HPAC-PAWA-AGENT-EXCLUSION/1.0`); no protected-root write; never imports the writer module or the helper |
| Standalone launcher | runs as the **deployment owner** (distinct OS account; two-principal topology, §61); minimal, imports no agent-reachable code |
| Privileged one-shot helper | `exec`'d child of the launcher; **deployment-owner** UID; loads only its own code; no agent/plugin/repository import |
| Deployment owner / admin | provisions `<HPAC_PROTECTED_ROOT>` and installs the helper bytes out-of-band (filesystem act, outside PCAE's authority model — PAWA-INV-4) |
| `<HPAC_PROTECTED_ROOT>` filesystem owner | deployment owner; agent-unwritable; `{device,inode}`-bound |
| Helper executable + config | deployment-owner-owned, mode `0755` / `0644`, agent-unwritable; `helper_sha256` in PAWA metadata |
| Private channel endpoint | created by the launcher; fd not shared with agent code; `0700` parent dir if a socket path is used |
| Service manager (if 6A/6B ever adopted) | systemd (Linux) / launchd (macOS); **not used by the selected 6C design** beyond optional launcher invocation |
| Process UID/GID | helper and launcher = deployment owner; **ambient root EUID is never the PCAE agent identity** and never the authority basis (PAWA-INV-1, §34) |
| Inherited env / fds / PATH / cwd | closed minimal allowlist for the helper; unknown env fails closed; no authority selector / response / helper path / role in env or argv |
| Symlink / traversal | every protected path opened `O_NOFOLLOW`; component-symlink rejection (`_reject_component_symlinks` pattern); helper validated and executed as the same file object |

The prior configured-agent-identity lessons (F-1: the negative boundary must
key off the *configured agent* principal resolved from
`HPAC-PAWA-AGENT-EXCLUSION/1.0`, never `os.geteuid()`; the two-OS-principal
requirement; live account resolution with `live uid == provisioned_uid`) are
**preserved and executed inside the helper**.

---

## 11. Protocol design

A new **narrow, versioned, local, one-shot** protocol —
`HPAC-PAWA-HELPER/1.0` (name indicative; the contract phase fixes it). This
warrants a **companion contract** analogous to HPAC-PPA-001 (§21 / §31).

**Request (canonical serialization, closed schema, unknown-field = fail
closed):**

| Field | Notes |
|---|---|
| `protocol_version` | exact match required |
| `operation` | **enum**, closed — see §13 per-factory; no arbitrary string |
| `role` | factory 2 only; member of the closed five-role allowlist (§12); `operation_scope_invalid` otherwise |
| `certification_session_id` | nonempty; bound |
| `principal_id` / `credential_id` / `proof_id` | subject binding; resolved & validated by the helper (§9.4); `target_scope_invalid` on mismatch |
| `operation_params` | a **closed typed struct per operation** — no free path, no JSON blob, no expression |
| `request_id` | monotonic within the session |
| `nonce` | CSPRNG ≥ 256 bits |
| `expiry` | trusted-clock deadline; helper validates freshness |
| `installation_id` / `generation` | echoed; helper cross-checks against the live protected root |
| `request_digest` | self-excluding |

**Response (closed schema):**

| Field | Notes |
|---|---|
| `protocol_version` / `request_id` / `nonce` | echoed, must match |
| `decision` | `PERFORMED` / `REJECTED` (+ `§56` terminal code) |
| `evidence_ref` / `evidence_digest` | digest of the audit record the helper wrote under the protected root |
| `result_payload` | factory 3 reads only — the enumerated §42D record contents, or a ceremony-entry acknowledgement; **never** an authority object |
| `trusted_timestamp` | |
| `response_digest` | self-excluding |

**Forbidden in the protocol** (prompt §11, §28): arbitrary Python
expression; module name / import path; shell command; executable path; role
string beyond the enumerated values; generic file path; unrestricted JSON
mutation payload; caller-provided `approved=True` / response bytes / helper
process / channel / attestation.

---

## 12. Five-role certification family

Preserved **exactly** (HPAC-PAWA-001 §42B, PAWA-INV-13, unchanged):

```
1. hpac_challenge_coordinator
2. hpac_assertion_recorder
3. human_authentication_proof_verifier
4. hpac_gate5_binder
5. hpac_rhamp_counter_state_verifier
```

`hpac_lifecycle_terminator` remains **outside** the family. Everything else is
denied (`operation_scope_invalid`).

**Mapping to the stronger boundary:** the five roles become **five members of
the closed `operation` enum** of the `certification_writer`-equivalent helper
invocation — one coordinator executable with exact internal role dispatch,
**not** five separate executables (smaller trust surface; exact closure
preserved; a single integrity-verified binary). Each invocation still mints
**one** single-use action bound to `(role, subject, certification_session_id)`;
`hpac_rhamp_counter_state_verifier` remains the **sole** counter-state
mutation authority.

---

## 13. Four factory responsibilities → stronger-boundary mapping

| Factory | Current responsibility | Current consumer | Current authority output | Proposed protected operation | Caller-visible result | State-mutation location | Audit evidence | Compatibility impact |
|---|---|---|---|---|---|---|---|---|
| `production_writer` | bounded §42 administrative mutations (principal/credential enroll/revoke; bootstrap; recovery) | principal-admin / bootstrap / recovery standalone scripts (§38) | `PRODUCTION` `HPACWriterCapability` | one typed `admin_mutation` op per launch (`enroll_principal`, `revoke_principal`, `revoke_credential`, `bootstrap`, `recover`, `rotate`) | `PERFORMED` + evidence digest | **in the helper process**, under `<HPAC_PROTECTED_ROOT>` | `HPAC-PAWA-ISSUANCE-EVIDENCE/1.0` written by the helper | callers switch from "get writer, call method" to "request op, receive evidence"; **contract change** (§8) |
| `certification_writer` | one five-role lifecycle write per ceremony | `pcae.core.hpac_certification_coordinator` via `scripts/hpac_certification_admin.py` (§38A) | single-use certification `HPACWriterCapability` | one typed `certification_write` op, `role` ∈ closed five (§12) | `PERFORMED` + evidence digest | in the helper | §55 + §42B extended issuance evidence | coordinator switches to protocol calls; **contract change** to §33A/§42B delivery |
| `recognized_certification_read_authority` | enumerated §42D reads + one ceremony entry | same §38A coordinator (§38B) | `CertificationReadAuthority` handle wrapping a read-only `HPACStoreAuthority` | one typed `certification_read` op (returns the enumerated record contents) **or** one `ceremony_entry` op (helper hands off to the HPAC-PPA-001 presentation helper directly) | the enumerated record contents / a ceremony-entry ack — **no handle** | reads in the helper; ceremony in the existing presentation helper | §42D / HPAC-PAWA-REQ-290 audit, `operation = "certification_read_authority"` | **largest contract change** — the §33B handle model is replaced by typed reads/hand-off; PAWA-INV-14's "handle" language is restructured |
| `mint_protected_presentation_evidence_writer` | authors `HPAC-PRESENTATION-EVIDENCE/2.0` | HPAC-PPA-001 launcher path (HPAC-PAWA-REQ-248) | evidence-writer capability | one typed `presentation_evidence_write` op invoked **by the presentation helper itself** post-ceremony | `PERFORMED` + evidence digest | in the presentation helper (already out-of-process) | HPAC-PPA / §54 evidence | **smallest change** — this factory is already consumed across the HPAC-PPA-001 boundary; it mainly needs to stop being reachable as an in-process Python capability |

**The mapping does not merely relocate the unsafe Python factory into another
importable module.** The privileged code path leaves the main interpreter
entirely.

---

## 14. Human authentication / approval separation

The stronger authority boundary **does not collapse** any of:

```
authenticated principal   != user presence
user presence             != user verification
authenticated principal   != informed approval intent
confirmation              != approval
approval                  != PB permission
PB permission             != runtime capability
runtime capability        != execution
```

The privileged helper / launcher is **not** a human approver. Possession of
access to the helper, or a successful peer-credential check, is **not**
approval. A YubiKey touch remains **user presence (UP)**, not informed
approval. Protected APPROVE / REJECT remains a **separate informed human
election** conducted only by the HPAC-PPA-001 presentation ceremony. The
helper's `ceremony_entry` operation only *starts* that ceremony; it never
produces its outcome.

---

## 15. Mobile-friendly / mechanism-neutral requirement

The architecture does **not** make YubiKey, FIDO2, or a local TTY mandatory
for ordinary PCAE development, nor the architectural identity of the
privileged helper. The helper's existence and trust are bound to **OS process
+ filesystem + peer-credential** facts, **not** to possession of any physical
authenticator. The helper **consumes** verified human-authentication results
(per the HPAC / RHAMP contracts) but hardcodes **no** authenticator. A future
**mobile-only / passkey** authentication-and-approval path stays open: it
would deliver a verified authentication result and a protected APPROVE to the
same helper operations unchanged.

---

## 16. Reuse of the existing PAWA / PPA trust root — role separation

The stronger boundary **reuses the existing HPAC-PAWA-001 §4 filesystem trust
root and the HPAC-PPA-001 out-of-band-install + integrity-verify pattern**. It
introduces **no second privileged bootstrap authority**.

Conceptual separations kept distinct:

```
deployment owner  !=  installer  !=  launcher  !=  evidence writer
                  !=  human approver  !=  runtime  !=  certification authority
```

- **Reused anchor:** `<HPAC_PROTECTED_ROOT>` filesystem authority + the
  `{device,inode}` / descriptor / generation machinery; the HPAC-PPA-001
  helper-integrity + private-channel + nonce pattern.
- **New authority it gains:** the helper executable is added to PAWA metadata
  as an integrity-pinned out-of-band artifact (a `helper_sha256` +
  owner/mode + generation binding) — the **same kind** of registration
  HPAC-PPA-001 already defines for the presentation helper. It gains **no**
  new trust root, **no** new provisioning act beyond installing bytes.
- **Bounding:** the helper can perform **only** the closed operation
  vocabulary; it cannot self-modify its registration; a new helper /
  operation requires a governed contract evolution + explicit enumeration
  (PAWA-INV-9).
- **Installation / registration governance:** out-of-band admin action,
  audited, generation-bound (rollback of an old helper alone fails
  current-anchor comparison — HPAC-PPA-REQ-028 pattern).

If the contract phase concludes the helper-metadata registration expands
frozen HPAC-PAWA / HPAC-PPA schema semantics beyond "add an integrity-pinned
artifact of the existing kind", it **recommends a companion contract** rather
than stretching a MINOR (§21 / §31).

---

## 17. Credential / secret design

The selected 6C design **requires no durable bearer secret** in any process.
Request authenticity rests on: the **private one-shot parent/child channel**
(agent code never holds the fd) + **OS peer credentials** + the **per-request
CSPRNG nonce** + **exact request/response binding** + the helper's own §33 OS
recognition — the HPAC-PPA-REQ-037 conjunction, *"No new signing key is
required or implied."*

If a future variant needs a MAC/secret (e.g. a persistent 6A/6B helper), the
contract phase MUST define a **real protected secret boundary**: generation
and storage under `<HPAC_PROTECTED_ROOT>` admin-owned, agent-unreadable;
rotation; compromise scope; and — critically — **the main interpreter never
receives the secret** (a secret in the agent process is no boundary against
code in that process, the same lesson as F-B). Preference stays with
OS/peer-credential trust over exported bearer secrets. No secret is designed
or implemented in this phase.

---

## 18. Non-bearer / one-shot authority

Preserved and **strengthened**: privileged authority never becomes a generic
transferable bearer token because it never becomes a *returnable object* at
all. Each helper invocation is: one operation-specific request; explicit
certification-session + subject context; bounded freshness (nonce + expiry);
single-use; immediate protected-side consumption; **no serialization of writer
authority** (there is nothing to serialize). Process restart cannot revive
stale consumed authority — the helper process is gone after one operation, and
a fresh launch re-runs the entire §33 sequence. §45–§49 / §49A / §49B
semantics are preserved (process-local, non-bearer, non-serialisable,
restart-dead, one-operation) and become properties of the **process boundary**
rather than of a fragile in-heap object.

---

## 19. Challenge / proof / counter path (H-3 five responsibilities)

Each of the five §42B roles maps to a bounded helper `certification_write`
operation:

| Role | Bounded helper op | Preserved semantics |
|---|---|---|
| `hpac_challenge_coordinator` | issue one challenge bound to the session | `recording != validity` |
| `hpac_assertion_recorder` | record one assertion | `assertion recorded != assertion valid` |
| `human_authentication_proof_verifier` | verify one proof | `proof existence != proof validity` |
| `hpac_gate5_binder` | bind one Gate-5 assurance result | `human approval != Gate5 result`; `Gate5 ALLOW != runtime capability` |
| `hpac_rhamp_counter_state_verifier` | one authorized post-assertion counter transition | pre-ceremony counter **read** (factory 3) `!=` post-assertion counter **transition** (this role, sole authority); `counter evidence != authority` |

The helper — running in its own interpreter, its inputs re-derived from the
protected root — means the main interpreter **cannot self-assert a successful
verification result**: it can only submit a typed request and receive a
typed, helper-authored evidence record.

---

## 20. Presentation evidence boundary

The distinct protected-presentation evidence boundary is preserved. The
architecture does **not** merge presentation rendering, human authentication,
certification-writer authority, and Gate-5 binding. `factory 3`'s
`ceremony_entry` op is a **hand-off** to the existing HPAC-PPA-001 presentation
helper (already out-of-process), passing the canonical ceremony request — not
a Python `HPACStoreAuthority`. `mint_protected_presentation_evidence_writer`
(factory 4) stays the **sole** author of `HPAC-PRESENTATION-EVIDENCE/2.0`,
invoked by the presentation helper itself. HPAC-PPA-001 v1.0 is **byte-unchanged**
by this architecture; whether the launcher-authority-origin question needs a
HPAC-PPA-001 note is deferred to the contract phase.

---

## 21. Failure / uncertainty semantics

**Fail-closed** for: helper executable missing / hash mismatch / wrong owner
or mode / symlink in path; peer-credential mismatch or unavailable; channel
creation / connection failure; malformed / unknown-field request; unknown
operation or role; stale (expired) request; duplicate `request_id` / nonce;
`installation_id` / `generation` mismatch; descriptor / §33 conjunct failure;
audit-write failure (the mutation is **not** committed if its evidence cannot
be written); session / subject binding mismatch.

**Explicit state-transition model for a mutating operation:**

```
REQUEST RECEIVED
  -> REQUEST AUTHENTICATED    (peer + nonce + binding + freshness)
  -> OPERATION ADMITTED       (§33 1..8 + operation/role/session valid)
  -> MUTATION ATTEMPT STARTED
  -> MUTATION COMMITTED       (atomic record write under the protected root)
  -> EVIDENCE WRITTEN
  -> RESPONSE EMITTED
```

Response loss after `MUTATION COMMITTED` is **never** proof the mutation did
not happen — the launcher/caller MUST reconcile against the protected-root
evidence record (whose digest the response would have carried), **not** retry
blindly. **No auto-retry** (existing PCAE principle preserved). A crash before
`MUTATION COMMITTED` leaves no effect; a crash between commit and evidence
write is detectable (committed record without matching evidence) and is a
`BLOCKED` reconcile condition, not a silent success.

---

## 22. Testability / deterministic verification

The architecture supports deterministic testing **without** turning fixtures
into production authority:

- **protocol tests** — request/response schema, canonical serialization,
  unknown-field rejection;
- **peer-auth tests** — a non-deployment-owner peer is refused;
- **negative authorization tests** — main-interpreter code cannot reach the
  helper; a forged launcher without the protected root fails §33;
- **operation validation tests** — non-enumerated op / role / path rejected;
- **crash/replay tests** — the §21 transition model, nonce/expiry reuse;
- **clean-install tests** — helper bytes + PAWA metadata registration on a
  fresh host;
- **real-hardware certification tests** — only in a fresh `N16-5-FINAL-CERT`.

Preserved: `deterministic test mechanism != real human authentication`. A test
helper that speaks `HPAC-PAWA-HELPER/1.0` is **never** production authority —
it is not the integrity-verified out-of-band executable, and the launcher's
same-file-object hash check rejects it. The disclosed one-leading-underscore
fixture seam discipline (HPAC-PAWA-REQ-265 / 287) is carried into the helper
design with a guard that no non-test invoker passes it.

---

## 23. Packaging / deployment architecture

- The privileged helper is a **separate deployment artifact**, not bundled as
  an importable module in the wheel's agent-reachable path. It MAY ship as a
  data file in the wheel that the admin **installs out-of-band** to an
  admin-owned path (bytes are inert until installed + registered), mirroring
  HPAC-PPA-001's helper.
- Installation ownership: deployment owner; protected target path
  admin-owned, agent-unwritable; executable mode `0755`, config `0644`.
- Version pinning: `helper_sha256` + `protocol_version` in PAWA metadata,
  generation-bound.
- Upgrade: install new bytes out-of-band, update the registered hash under a
  generation bump; old bytes fail current-anchor comparison.
- Rollback / uninstall / clean install: the HPAC-PPA-REQ-028 pattern
  (restoring an old helper alone fails; a whole-root snapshot restore is
  bounded by the deployment-owner TCB).
- Compatibility: macOS development host (launchd-adjacent, `getpeereid`) and
  the eventual Dell Ubuntu deployment target (systemd-adjacent,
  `SO_PEERCRED`). **No host is provisioned or mutated by this phase.**

---

## 24. Cross-platform boundary

| Guarantee | Portability |
|---|---|
| Filesystem-permission trust root, `O_NOFOLLOW`, `{device,inode}` binding | **portable** (macOS + Linux) — already relied on by HPAC-PAWA-001 §63 |
| One-shot `exec` of an integrity-verified executable, private parent/child pipe | **portable** |
| Peer-credential check | **platform-specific backend, one logical contract** — `SO_PEERCRED` (Linux) vs `LOCAL_PEERCRED` / `getpeereid` (macOS); both yield `(uid, gid)` of the peer |
| Service-manager supervision (only if 6A/6B) | platform-specific (systemd vs launchd) — **not in the selected design** |

One common logical protocol + trust contract, with platform-specific
peer-auth and launch backends, is preferred over two authority models
(HPAC-PAWA-001 §63 discipline). macOS launchd/socket and Linux
systemd/Unix-socket semantics are **not** assumed identical.

---

## 25. Threat-model dispositions

See the table in §4. Summary: T1–T6, T8–T14 **mitigated** by the selected
architecture (vs **not mitigated** today for T1, T2, T6); T7 is **fail-closed
by the two-principal requirement** (genuine protection needs the two-account
deployment); T15 and a hostile root TCB are **explicitly out of scope**
(§26).

---

## 26. Out-of-scope threats (bounded claims)

The architecture does **not** claim protection against an adversary who
already controls: the privileged helper binary or its admin-owned config; the
root-owned `<HPAC_PROTECTED_ROOT>`; the OS kernel; or the deployment-owner /
root account. This matches HPAC-PAWA-001 §8(c) / §60 / PAWA-INV-6 and
HBDC-001 §18, inherited unchanged. Within those bounds, the claim is: **no
same-interpreter agent/plugin/repository code, and no same-UID agent process
on a two-principal deployment, can mint privileged authority or reach a
protected mutation.**

---

## 27. No second trust root

The selected design adds **no** new production trust root. It reuses the
HPAC-PAWA-001 §4 filesystem authority and the HPAC-PPA-001 out-of-band-install
pattern. The helper executable registration is an *integrity-pinned artifact
of the existing kind*, not a new bootstrap authority. If the contract phase
finds a genuinely new root is unavoidable, it MUST justify it and recommend a
**separate governed contract / bootstrap phase** — not fold it in.

---

## 28. Generic-operation no-go

The helper protocol MUST NOT become an arbitrary shell / Python executor, a
generic filesystem writer, a generic registry editor, an arbitrary role mint,
a generic secret broker, or an unrestricted sudo bridge. Every operation is
narrow, typed, validated, and contract-bound (§11, §13). `operation_params`
is a **closed typed struct per operation** — never a path string, expression,
or JSON mutation payload.

---

## 29. Runtime / effect wall

Unchanged and unaffected:

```
Runtime state:            Observed
Maximum capability:       observe
Execution availability:   unavailable
Plugins:                  0
Capabilities:             0
First governed runtime external effect:  ABSENT / UNREACHABLE
```

This architecture authorizes **no** execution enablement, real adapter,
`adapter.dispatch()`, Gate-10 effect reachability, N16-6, or N16-7.
Preserved: `DispatchEnvelope != runtime capability != permission to dispatch`;
`execution unavailable -> no external effect`. The privileged helper is an
**administrative** boundary (principal/credential/certification-lifecycle
records under the protected root); it is not a runtime, not an adapter, and
cannot produce a first external effect.

---

## 30. N-16-5 boundary

This phase does **not** close N-16-5. A defined stronger-boundary architecture
means only that: **the architecture is defined and adjudicated.** It is not
implemented, verified, deployed, or certified. Final certification remains
several governed steps away (§34). No real certification is scheduled or
performed here.

---

## 31. Contract-evolution decision

**Verdict: B — REQUIRES HPAC-PAWA-001 CONTRACT EVOLUTION.**

**Why not A (implementable under current v1.4):** v1.4's §32 recognition
predicate 6 / §33 step 9 ("verify the **calling module** is an authorized
factory consumer"), §36–§37 (factory **exported from a module**, **returns a
capability**), §33A / §33B (accessor **returns a handle** to the coordinator),
and the §42B / §42D / §49B "handle" semantics and PAWA-INV-13 / PAWA-INV-14
"process-local … non-serialisable … handle" language are all **written around
an in-process factory that returns a Python authority object to a same-process
caller**. The predecessor proved that shape cannot carry authority. Delivering
authority out-of-process and replacing "calling module identity" with
"verified peer process + OS recognition" is **not** expressible as
HPAC-PAWA-REQ-153's permitted MINOR moves ("re-state verified behaviour",
"tighten a bound", "add an enumerated consumer category") — it **restructures
the frozen recognition-sequence delivery model** and the factory/handle
semantics.

**Smallest necessary evolution** (for the contract phase to specify precisely):

1. **§32 / §33 step 9** — replace "the calling module is an authorized factory
   consumer" with "the privileged operation is performed by a distinct
   protected-owner process, `exec`'d from the integrity-verified out-of-band
   helper executable, whose peer credential over a private one-shot channel is
   the deployment-owner principal, and which itself runs §33 steps 1–8".
2. **§36 / §37 / §38 / §42B / §42D** — the privileged side performs the
   operation and returns typed evidence; no `HPACWriterCapability` /
   `HPACStoreAuthority` / handle crosses back to the main interpreter or the
   launcher.
3. **§33B / §49B / PAWA-INV-14** — restate factory 3 as typed enumerated
   reads + a ceremony-entry hand-off rather than a returned
   `CertificationReadAuthority` handle.
4. **A companion contract** (`HPAC-PAWA-HELPER-00x`, analogous to
   HPAC-PPA-001) for the helper protocol, integrity/launch model, peer-auth,
   and failure semantics — **or** a determination that HPAC-PPA-001 can be
   extended. HPAC-PAWA-REQ-308 explicitly anticipates this: *"Had a second
   frozen contract genuinely required a normative change, this phase would
   have BLOCKED and derived a separate contract phase."*

**Magnitude:** most likely **MAJOR** (restructures a frozen 11-step
recognition sequence and the factory/handle model; probably adds a companion
contract), with a plausible **MINOR** framing available only if the evolution
can be expressed purely as "make the already-frozen OS-filesystem trust root
the *sole* authority-delivery boundary and remove the in-process authority
object" without renumbering §33. **This architecture phase does not author the
contract change.** Per the default, it **recommends a fresh, separately
authorized contract phase** (§34).

---

## 32. Required architecture artifact — coverage map

| # | Required element | Section |
|---|---|---|
| 1 | baseline reconciliation | §3.x below / §0.2 / Appendix A |
| 2 | problem statement | §2 |
| 3 | current boundary failure | §3 |
| 4 | threat model | §4 |
| 5 | candidate architectures | §6 |
| 6 | comparison matrix | §6 |
| 7 | selected architecture | §7 |
| 8 | trust anchors | §7.2 / §16 / §27 |
| 9 | process/OS model | §10 |
| 10 | protocol model | §11 |
| 11 | factory-to-operation mapping | §13 |
| 12 | five-role mapping | §12 / §19 |
| 13 | presentation/authentication separation | §14 / §20 |
| 14 | state/freshness/replay model | §11 / §18 / §21 |
| 15 | failure/uncertainty semantics | §21 |
| 16 | deployment/packaging model | §23 |
| 17 | test strategy | §22 |
| 18 | migration plan | §33-migration below |
| 19 | compatibility impact | §13 / §33 |
| 20 | contract impact | §31 |
| 21 | implementation slices | §34 |
| 22 | IV strategy | §34 |
| 23 | final certification prerequisites | §35 |
| 24 | explicit no-go boundaries | §29 / §47 |

### Appendix A — HPAC-PAWA-001 v1.3 → v1.4 baseline reconciliation

Reconstructed from primary repository artifacts (the contract file header,
§7C, §80.3, §80.4, §90.3, §90.4, §94, §95B, §95C, PAWA-INV-13, PAWA-INV-14)
and the predecessor completion metadata — **not** taken on the predecessor's
assertion:

| Question | Finding |
|---|---|
| Governing phase (v1.3) | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R` (alias **N16-5-H3-PAWA13**), commit `b2530066` region; folded contract-IV precedent noted |
| Governing phase (v1.4) | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R` (alias **N16-5-F5B1-READAUTH**), pushed `3ef9ad5d`; **N16-5-F-5-B1-IV** (independent verification of HPAC-PAWA-001 v1.4) subsequently completed |
| v1.3 → v1.4 contract diff | adds §7C delta table, §33B, §38B, §39B (consumer guard spec), §42D, §42E, §49B, §68B, §80.4, §90.4, §95C, §95.3, §96C, PAWA-INV-14; §7C / §92 updated. **One file changed**, evolved in place |
| Rationale | resolves blocking finding **F-5-B1** (from N16-5-FINAL-CERT): the N-16-5 pre-ceremony provenance-verified canonical reads + `run_protected_presentation_ceremony()` entry need an `HPACStoreAuthority` passing `_validate_production_boundary` under the deployment owner's real OS context — reachable only via `_PRODUCTION_WRITER_FACTORY_SEAL`, and every seal-holding factory is a mutation/lifecycle-write path; there was **no least-privilege production read / ceremony-entry path** |
| Version classification | **MINOR (S-3)** — one recognized **read-only** accessor; no writer family, role, `PawaOperation`, mutation, counter transition, new `pawa_failure_code`; strictly narrower than the S-2 certification-writer family; §80.4 MAJOR-trigger review — **none fires** |
| Verification status | dedicated **HPAC-PAWA-001 v1.4 contract IV** recommended (HPAC-PAWA-REQ-305); the F-5-B1 IV lineage (**N16-5-F5B1-READAUTH-IV**, **N16-5-F-5-B1-IV**) is reflected in `git log`; v1.4 is **FROZEN** |
| Is v1.4 fully frozen and independently verified? | **FROZEN**; independently verified at the contract level (F-5-B1 IV lineage). It has **not** been validated against the *same-process unsatisfiability* the later N16-5-F-5-B2 line discovered — that discovery is *why this architecture phase exists* |
| Consumer-authenticity requirement — changed how by v1.4? | **unchanged in intent**; v1.4 *reuses* §33 steps 1–9 (incl. the §32 step-9 consumer check) verbatim as required conjuncts for §33B. v1.4 did **not** introduce a new trust-boundary expectation for consumer authenticity — it inherited the existing (now-known-unsound) same-process one |
| Does v1.4 already define/constrain out-of-process authority / protected helper boundaries / authenticated local IPC / production-factory consumer provenance / writer capability confinement? | **Out-of-process authority: NO** (v1.4 authority is an in-process handle to the coordinator). **Protected helper boundary: only via HPAC-PPA-001 reuse for the ceremony hand-off** (§7C: `mint_protected_presentation_evidence_writer` path reused unchanged). **Authenticated local IPC: NO.** **Consumer provenance: via §32 module-identity** (the unsound mechanism). **Writer-capability confinement: YES for the read authority** (`writer()` still raises; handle non-serialisable / restart-dead) — but confinement is *in-process*, the exact property the predecessor invalidated |
| Exact current normative baseline | **HPAC-PAWA-001 v1.4, FROZEN, MINOR (S-3).** Trust root: OS filesystem write authority on the out-of-band-provisioned protected root (HPAC-PAWA-REQ-010 / REQ-300), *"never an in-process check"*. §33: 11 steps, frozen order; steps 1–8 OS-level; step 9 = in-process authorized-factory-consumer check. §33A / §33B reuse steps 1–9. Four factory families, all minting in-process Python authority objects. PAWA-INV-1..14. Companion contracts (HPAC-001 v2.1, RHAMP-001 v1.0, HPAC-PPA-001 v1.0, HBDC-001 v1.2, RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001 v3.1) all byte-unchanged at v1.4 |

**v1.4 lineage is consistent and not ambiguous** — the header, §7C, §80.4,
§90.4, §94, and the completion metadata agree; the governing phase is a
legitimately governed prior phase that is an ancestor of the predecessor's own
commit. This phase therefore proceeds (no §3-mandated STOP).

---

## 33. Migration plan

| Step | Action |
|---|---|
| M1 | **Contract phase** freezes the evolved HPAC-PAWA-001 (+ any companion helper-protocol contract). No source. |
| M2 | **Contract IV.** |
| M3 | Implement the privileged helper executable + `HPAC-PAWA-HELPER/1.0` protocol + launcher integrity-verify + peer-auth, behind the non-agent-importable fence / as a separate deployment artifact. The helper runs §33 1–8 in-process. |
| M4 | Migrate `scripts/hpac_certification_admin.py` / `pcae.core.hpac_certification_coordinator` and the principal-admin scripts from "import writer module, call factory, use returned capability" to "build request, launch helper, consume typed evidence". |
| M5 | **Remove the in-process privileged factory path** — `production_writer` / `certification_writer` / `recognized_certification_read_authority` / `mint_protected_presentation_evidence_writer` no longer return authority objects; the `_PINNED_*` / `_verified_production_caller_name` / `_detect_caller_module` mechanism and the in-process `_PRODUCTION_WRITER_FACTORY_SEAL` mint path are deleted (their logic moves into the helper). **A compatibility shim MUST NOT preserve the insecure in-process authority path.** |
| M6 | Packaging / deployment integration — helper bytes in the wheel as an inert data artifact; out-of-band install docs; PAWA metadata registration. |
| M7 | Clean-install verification on macOS and (later) the Dell Ubuntu target. |
| M8 | Migrate negative tests: the predecessor's bypass PoCs become regression locks asserting **there is no in-process authority object to attack**; new negative tests target the helper boundary. |
| M9 | Rollback strategy: the contract and each implementation slice are independently revertible; the helper is generation-bound so a bad helper is rejected by current-anchor comparison, not silently used. |

Rollout order: contract → IV → helper+protocol → caller integration →
in-process-path removal → packaging → clean-install IV → security IV →
deployment → fresh final certification. Old mutable trust-pin path removal
(M5) happens **only after** the helper path is verified working (M3–M4), but a
compatibility shim never keeps the old path reachable.

---

## 34. Implementation slicing + IV strategy (recommended future governed phases — NOT begun)

Each requires its own explicit human authorization; IDs recommended, **NOT
reserved**; none begun by this phase.

| # | Phase | Scope | IV |
|---|---|---|---|
| 1 | **Contract evolution phase** (alias e.g. `N16-5-F-5-TB-CONTRACT`) | freeze the evolved HPAC-PAWA-001 §32/§33/§36–§38/§42B/§42D/§49B + companion helper-protocol contract; classify MINOR/MAJOR definitively; contract-only, no source | folded or dedicated per operator discretion |
| 2 | **Dedicated contract IV** (`…-CONTRACT-IV`) | independently verify the evolution, magnitude, walls, no second trust root, companion-contract sufficiency | dedicated |
| 3 | **Helper + protocol implementation** (`…-HELPER-IMPL`) | the privileged one-shot helper executable; `HPAC-PAWA-HELPER/1.0`; launcher integrity-verify + private channel + peer-auth; §33 1–8 in the helper; audit evidence; **no** caller migration yet | — |
| 4 | **Caller integration** (`…-CALLER-IMPL`) | migrate the standalone scripts + coordinator to the protocol; keep the old path only until this lands | — |
| 5 | **In-process path removal** (`…-DEPRECATE-IMPL`) | delete `_PINNED_*` / `_verified_production_caller_name` / in-process factory returns / in-process seal mint; regression-lock the absence | — |
| 6 | **Packaging / clean-install** (`…-PACKAGING-IMPL`) | wheel data artifact; out-of-band install; PAWA metadata registration; macOS + Ubuntu clean-install tests | — |
| 7 | **Independent security IV** (`…-SECURITY-IV`) | independently verify: no in-process authority object exists; a forged launcher fails §33; a fake helper fails the hash check; peer-auth; replay resistance; the §21 transition model; T1–T15 dispositions; runtime unchanged; no external effect; H-3 five-role closure preserved | dedicated, not merged |
| 8 | **Production deployment** (`…-DEPLOY`) | deploy helper bytes + registration on the real host; verify principal/credential/counter/generation coherence and the real protected-presentation path | — |
| 9 | **Fresh `N16-5-FINAL-CERT`** | **fresh CPIPC-valid id** (never reuse a completed/blocked certification id — PAWA-INV-11); the real ceremony end-to-end + N-16-5 closure adjudication | its own phase |

---

## 35. Final-certification preconditions

A future `N16-5-FINAL-CERT` is **prohibited** until **all** hold:

- the stronger-boundary contract evolution (+ companion contract if any) is
  **frozen and independently verified**;
- the helper + protocol + launcher + caller migration + in-process-path
  removal implementation is **complete**;
- the **independent security IV** (§34 #7) **passes**;
- packaging / clean-install is **verified** on the target host;
- production principal / credential / RHAMP counter / generation-1 state is
  **coherent**;
- the real protected-presentation path is **coherent** end-to-end;
- genuine hardware / mechanism prerequisites are **ready** on the real host;
- a **fresh** certification session / challenge is created (never reuse a
  prior completed or blocked certification identity — PAWA-INV-11).

---

## 36. Human-authentication flexibility

Preserved: FIDO2 / YubiKey is a supported strong mechanism, **not** the only
future one. The selected helper architecture accepts mechanism-neutral
verified human-authentication results per the HPAC contracts and does **not**
bind the helper's existence to possession of a YubiKey (§15). A future
mobile-only approval / authentication direction stays open.

---

## 37. Historical governance integrity

Preserved exactly, no retroactive authorization or reinterpretation:

```
N16-5-F-5-B2       : NOT VERIFIED / BLOCKED
N16-5-F-5-B2R-IV   : NOT VERIFIED / BLOCKED
N16-5-F-5-B2R2-IMPL: COMPLETE — BLOCKED
DELEGATED .3 FINALIZATION / COMMIT / PUSH : UNAUTHORIZED
```

---

## 38. Delegated-worker rule

No delegated workers were used in this phase; all inventory, source
inspection, contract comparison, protocol-option analysis, and threat modeling
were performed by the primary operator directly. Had any been delegated, the
constraints (no finalize / mutate canonical status / commit / push / mutate
protected host / install / authenticate / certify; primary operator
independently adjudicates) would apply, and
`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` remains an immutable
historical outcome.

---

## 39. REPORTING-UX-1

The architecture-status current-phase display parser limitation
(**REPORTING-UX-1**) remains **open and non-blocking**. Canonical phase
identity and metadata for this phase were verified independently via
`pcae.core.phase_id` and direct artifact inspection (§0). This phase does
**not** expand into parser repair. REPORTING-UX-1 is **recorded as still
present**.

---

## 40. Doctor / health / notification

| Check | Result at finalization |
|---|---|
| `pcae check` | passed |
| `pcae health` | healthy |
| `pcae push check` | (recorded in the phase-completion metadata / report) |
| `pcae status` coherence | passed |
| `pcae doctor task-memory` | (recorded in the completion metadata) |
| governed completion notification | Telegram runtime loaded; dispatched by `pcae phase complete` (no fabricated credentials) |

---

## 41–43. Success / blocked end state

This phase reaches the **§42 success end state** (architecture defined):

```
N16-5-F-5-TB-ARCH : COMPLETE
Trust-boundary status : STRONGER-THAN-SAME-INTERPRETER ARCHITECTURE DEFINED
Contract-evolution verdict : B — REQUIRES HPAC-PAWA-001 CONTRACT EVOLUTION
F-5-B2 : BLOCKED PENDING STRONGER-BOUNDARY CONTRACT + IMPLEMENTATION
F-5 : CERTIFICATION BLOCKED
N-16-5 : NOT CLOSED
N-16-6 : OPEN / UNTOUCHED
N-16-7 : OPEN / UNTOUCHED — STRICTLY LAST
Runtime : Observed / observe / unavailable
Plugins / capabilities : 0 / 0
First governed runtime external effect : ABSENT / UNREACHABLE
Real certification ceremony : NOT PERFORMED
Recommended next : a fresh, separately authorized governed CONTRACT phase
                   (§34 #1) — NOT BEGUN
```

It is **not** a §43 BLOCKED outcome: a truthful stronger-boundary architecture
*was* defined; the only reason it cannot be implemented immediately is that it
requires a contract evolution, which is the normal governed path, not an
architectural dead end.

---

## 47. Absolute stop boundary

This phase ends at architecture definition / adjudication. It does **not**,
and no successor may without its own fresh human authorization: implement the
helper/service; create privileged IPC endpoints; install protected binaries;
mutate PAWA/PPA production state; perform protected host writes; start contract
evolution; start implementation; start final certification; request a FIDO2
PIN or YubiKey touch; launch protected approval; create a production
challenge; issue real proof; mutate live counter state; issue a PRODUCTION
principal; perform Gate-5 final certification; close N-16-5; begin N-16-6;
begin N-16-7.

---

## Canonical evidence

- Phase ID CPIPC derivation: `pcae.core.phase_id` (§0.3).
- Predecessor state: `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json`,
  `docs/PHASE_N16_5_F5B2R2_IMPL.md`, `tasks/done/20260909-2302-…md`.
- Contract baseline: `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v1.4) §4, §5, §7C, §8, §32, §33, §33A, §33B, §36–§39, §42B,
  §42D, §60, §68, §74, §80.4, §92 (PAWA-INV-1..14), §95C, §96C;
  `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`
  (HPAC-PPA-001 v1.0) §5, §6, §7.
- Failed mechanism: `src/pcae/core/hpac_protected_admin_writer.py:49, 486-717,
  971, 1143, 1820, 1934, 2338, 2546` (read-only inspection; **byte-unchanged
  by this phase**).
- Runtime posture: `pcae runtime inspect` — `not_implemented` / `Observed` /
  `observe` / `unavailable` / 0 / 0.
- `git diff <phase-entry 089817c8> HEAD -- src/pcae scripts pyproject.toml
  docs/contracts` — **empty** (no production / script / dependency / contract
  change); the only changes this phase makes are `docs/PHASE_N16_5_F_5_TB_ARCH.md`
  (this file), `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`,
  `.pcae/phase-completion-*`.
