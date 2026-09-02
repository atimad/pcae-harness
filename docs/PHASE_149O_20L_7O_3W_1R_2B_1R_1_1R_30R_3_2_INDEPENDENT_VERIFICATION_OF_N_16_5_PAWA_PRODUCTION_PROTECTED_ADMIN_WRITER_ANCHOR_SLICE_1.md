# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2 — BLOCKED

**Independent Verification of the N-16-5 PAWA Production Protected-Admin
Writer Anchor Implementation (Slice 1)**

**STATUS: BLOCKED.** Independent re-derivation from primary source found a
reproducible bypass of the PRODUCTION `HPACWriterCapability` one-operation /
non-bearer invariant (HPAC-PAWA-REQ-102/106/107). This is exactly one of the
phase's own enumerated "Stop and return BLOCKED" conditions: *"a PRODUCTION
`HPACWriterCapability` can be forged, copied, deep-copied, serialized,
reconstructed, reused after restart, or reused after one successful
mutation"* / *"one-operation spend can be bypassed."* Per the phase's own
governance rules, no repair, no contract edit, and no test/guard weakening
was performed inside this IV. N-16-5 remains **NOT CLOSED**.

## 1. SHAs

- **A** (finalized `.1R.30R.2A.3` head) = `1793a75a73c54c6f6687bc830664caeac5aeaa66`
- **I** (finalized `.1R.30R.3.1` head) = `aff46ec3` (full: see `git log`
  commit `aff46ec3...`, "reconcile governed push state in Slice-1 completion
  metadata (pushed; origin/main..HEAD = 0)")
- **V** (`.1R.30R.3.2` phase-entry SHA) = `aff46ec3` (== I; `git status
  --branch --short` showed `main...origin/main` with clean tree and
  `origin/main..HEAD = 0` at entry)
- Historical `.1R.30` BLOCKED anchor `B30 = 8e655295` (unchanged, not
  reused/resumed).

Derived independently by grepping `git log --oneline` for each phase's own
"reconcile governed push state ... (pushed; origin/main..HEAD = 0)" commit —
the canonical finalized head per phase — not inherited from prose.

## 2. Primary sources read

- `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v1.1) — read in full, in particular §46 (Non-bearer,
  HPAC-PAWA-REQ-102), §47 (Non-serializable, HPAC-PAWA-REQ-103), §49
  (One-operation, HPAC-PAWA-REQ-106/107/108), and the §56 failure-code table
  (row 20, `reconstruction_attempt`).
- `.1R.30R.3.1` implementation report/doc
  (`docs/PHASE_..._30R_3_1_...SLICE_1.md`) and its
  `.pcae/phase-completion-metadata.json` (pre-.3.2 state).
- `.1R.30R.2A.3`, `.1R.30R.2A.2`, `.1R.30R.2A.1`, `.1R.30R.2A`, `.1R.30R`,
  and the historical `.1R.30` BLOCKED artifact — read via `git show` /
  `git log` for the adjudication and contract-freeze chain.
- Production source in full: `src/pcae/core/hpac_pawa_agent_exclusion.py`,
  `src/pcae/core/hpac_pawa_schemas.py`,
  `src/pcae/core/hpac_protected_admin_writer.py`,
  `src/pcae/core/hpac_foundation.py`,
  `src/pcae/core/human_principal_registry.py`,
  `scripts/hpac_protected_root_admin.py`.
- The fresh `.1R.30R.3.1` 95-test suite
  (`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1.py`),
  read in full, including `test_54_direct_constructor_rejected`,
  `test_55_object_new_reconstruction_rejected`,
  `test_56_copy_does_not_create_a_second_usable_capability`,
  `test_59_restart_invalidation_fresh_seal`,
  `test_60_one_operation_replay_rejected_at_both_layers`.

## 3. Production diff inventory (A → I) — independently re-derived

```
git diff --name-status 1793a75a aff46ec3 -- src/pcae scripts
A  scripts/hpac_protected_root_admin.py
M  src/pcae/core/hpac_foundation.py
A  src/pcae/core/hpac_pawa_agent_exclusion.py
A  src/pcae/core/hpac_pawa_schemas.py
A  src/pcae/core/hpac_protected_admin_writer.py
M  src/pcae/core/human_principal_registry.py
```

Exactly the 6 files claimed by `.1R.30R.3.1`. No unrelated production file
changed. **VERIFIED.**

## 4. Contract byte identity — independently re-derived

`git diff --name-only 1793a75a aff46ec3 -- docs/contracts` is empty.
`git diff 1793a75a aff46ec3 -- src/pcae/core/hpac_verifier.py
runtime_dispatch_gate5.py runtime_dispatch_gate9.py` is empty.
`_ELIGIBLE_MECHANISM_IDS` in `hpac_verifier.py` remains
`frozenset({"hpac.deterministic.test-only.v1"})`. **VERIFIED — no normative
drift, no Gate/verifier/mechanism-allowlist change.**

## 5. ★ Decisive finding — HPACWriterCapability seal-identity forgery bypasses one-operation spend

### 5.1 Mechanism

`src/pcae/core/hpac_foundation.py:594-608`:

```python
def require_writer(
    self, writer: HPACWriterCapability, role: str, *, subject: Optional[str] = None
) -> None:
    if not isinstance(writer, HPACWriterCapability) or writer._authority_seal is not self._seal:
        raise HPACAuthorityError("writer capability is absent, forged, or bound to another HPAC root")
    if writer.role != role or writer.subject != subject:
        raise HPACAuthorityError("writer capability role/subject does not match this operation")
    if writer.authority_class is not self.authority_class:
        raise HPACAuthorityError("writer capability assurance-class mismatch")
    if writer._spent:
        raise HPACAuthorityError("writer capability is spent (one-operation lifetime exhausted)")
    self._ensure_root(create=True)
```

The **only** integrity check binding a capability to its issuing authority is
object identity of `_authority_seal` (`writer._authority_seal is self._seal`).
`HPACWriterCapability` (`hpac_foundation.py:244-290`) is a plain `__slots__`
class; `__init__`'s constructor seal (`_WRITER_CONSTRUCTOR_SEAL`) gates
`__init__`, but **`object.__new__(HPACWriterCapability)` bypasses `__init__`
entirely**, and every slot (`_authority_seal`, `role`, `subject`,
`authority_class`, `_single_use`, `_spent`) is then a normal, directly
settable/readable instance attribute — there is no `__setattr__` override,
no name-mangled privacy, no cryptographic binding.

`_authority_seal` is not a secret an attacker must *guess* or *reconstruct*:
it is the literal `object()` singleton the issuing `HPACStoreAuthority`
holds, and any code that already possesses a legitimately-issued (even
already-*spent*) `HPACWriterCapability` can read that exact object off it
(`cap._authority_seal`) and copy the *same object reference* onto a
`__new__`-constructed shell. The identity check then trivially passes,
because it genuinely is the same object — not a reconstruction.

### 5.2 Contract text vs. actual guarantee

`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`:

- **HPAC-PAWA-REQ-102** (§46, Non-bearer): "A capability is valid only if it
  was produced by the canonical `PRODUCTION` writer factory in this process
  and is recognised by `require_writer`'s **identity** check
  (`writer._authority_seal is self._seal`), not a value comparison."
- **HPAC-PAWA-REQ-103** (§47): "reconstruction via `object.__new__` + known
  field values (**fails the seal-identity check** and the live root
  re-probe)."
- §56 failure-code row 20: `reconstruction_attempt` — "a forged /
  deserialised / `object.__new__` capability **fails the seal-identity
  check**."

The contract's own claim in REQ-103/§56 — that `object.__new__` +
known-field-value reconstruction fails the seal-identity check — is **only
true if the attacker does not already hold a reference to a real,
previously-issued capability object**. It is false for the case actually
demonstrated here: the production code *faithfully implements exactly the
mechanism REQ-102 mandates* (raw object-identity comparison, no cryptographic
per-mint binding), and that mandated mechanism does not, in fact, prevent a
holder of one legitimate (spent) capability from forging a second one that
passes it. The implementation is not deviating from the contract; the
contract's own prescribed mechanism does not deliver the guarantee the
contract's own prose (REQ-103, §56 row 20) claims it does.

### 5.3 Independent live reproduction (real production path, not mocked)

Run against the actual `production_writer()` → `HumanPrincipalRegistryStore`
path, using the exact fixtures from the `.1R.30R.3.1` suite
(`_agent_src`, `_locked_probe`, `provision_protected_root`, the
`_TEST_FACTORY_CONSUMERS`-listed test-module caller name):

```
legit cap spent: True subject: alice role: human_principal_registry_admin
SECOND MUTATION (revoke_principal) via forged capability: SUCCEEDED  <-- BUG CONFIRMED
```

Steps:
1. Mint a real `PRODUCTION` `HPACWriterCapability` via `production_writer(ENROLL_PRINCIPAL, principal_id="alice", ...)`.
2. Legitimately spend it once: `HumanPrincipalRegistryStore.enroll_principal(cap, ...)` → `cap._spent == True`.
3. `forged = HPACWriterCapability.__new__(HPACWriterCapability)`; copy `forged._authority_seal = cap._authority_seal`, `forged.role = cap.role`, `forged.subject = cap.subject`, `forged.authority_class = cap.authority_class`, `forged._single_use = True`, `forged._spent = False`.
4. `handle.authority.require_writer(forged, "human_principal_registry_admin", subject="alice")` → **ACCEPTED** (no exception).
5. `store.revoke_principal(forged, principal_id="alice", revoked_at=...)` → **SUCCEEDED** — a second, distinct registry mutation performed from a single §33 recognition/mint event, using only in-process attribute access to an object the code already legitimately held.

### 5.4 Why the existing 95-test suite did not catch this

`test_55_object_new_reconstruction_rejected` constructs
`HPACWriterCapability.__new__(HPACWriterCapability)` and asserts
`require_writer` raises — but it **never sets `_authority_seal`**, so the
assertion passes only because accessing the unset slot raises `AttributeError`
(caught by the test's broad `pytest.raises(Exception)`), not because forgery
is actually rejected. `test_56` (copy/deepcopy) and `test_59` (restart) both
correctly reject **their own specific adversaries** (`__reduce__` raising
`TypeError`; a fresh authority instance's fresh `_seal`), but neither tests
the specific, contract-described adversary of §5.1/§5.3: a `__new__` shell
that copies a **real, already-held** seal reference. That adversary — the
one HPAC-PAWA-REQ-102/103 and this phase's §41/§46/§108 explicitly describe
— is absent from the fresh suite and was not exercised by `.1R.30R.3.1`'s
own verification.

### 5.5 Severity note

Exploiting this requires the ability to run arbitrary Python in the *same
interpreter process* that already legitimately obtained the capability — it
does not grant privilege to any caller who could not already invoke
`production_writer()` themselves (a caller who cannot mint any capability at
all still cannot forge one). But it defeats the specific one-operation /
non-bearer / non-reconstructable invariant the contract and this IV phase
declare mandatory (HPAC-PAWA-REQ-102, -106, -107), and it is trivially
reproducible with no privileged access, no OS-level compromise, and no
timing race — only ordinary attribute access on an object the calling code
already holds a reference to. Given `.1R.30R.3.1`'s own admin script
(`scripts/hpac_protected_root_admin.py`) invokes `production_writer()` and
then performs the mutation in the same process, this is a real,
in-scope process-boundary the contract's threat model is meant to defend.

## 6. Verdict

**BLOCKED.**

- **Class: product** — a code-level insufficiency in
  `hpac_foundation.py`'s `HPACWriterCapability` / `require_writer` seal
  check — **with a contract note**: the insufficiency traces to
  HPAC-PAWA-REQ-102's own mandated mechanism (raw object-identity, "not a
  value comparison"), whose accompanying claim in REQ-103/§56-row-20 ("fails
  the seal-identity check") does not hold under the demonstrated adversary.
  A pure code patch that leaves the seal an unauthenticated, readable
  instance attribute cannot close this gap merely by adding more identity
  checks on the same object; closing it requires either (a) a
  process-local *minted-capability-membership* check (an issuance registry
  the seal alone does not provide) or (b) an unpredictable, per-mint,
  non-copyable binding — either of which is a change to the mechanism
  REQ-102 currently prescribes, and therefore likely needs a small
  HPAC-PAWA-001 contract amendment (PATCH or MINOR — not a Slice-1
  re-scope) alongside the code fix, not a silent code-only patch.
- Not repaired inside this IV, per the phase's own governance rules (no
  repair, no contract edit, no test/guard weakening inside `.1R.30R.3.2`).
- **Recommended successor repair phase:**
  `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1.1` — "N-16-5 PAWA
  `HPACWriterCapability` Seal-Forgery / One-Operation-Bypass Repair" — assess
  and (if needed) narrowly amend HPAC-PAWA-REQ-102/103's mechanism
  description, then harden `require_writer`/`HPACWriterCapability` (e.g. an
  unpredictable per-mint token checked against a process-local issuance-
  registry membership set, not merely `is`-identity of a plain readable
  attribute), add the specific "copied-real-seal-onto-a-`__new__`-shell"
  adversary test that `test_55` currently misses, then re-run the full
  `.1R.30R.3.2` verification matrix (this IV's remaining, not-yet-exhausted
  sections) against the repaired code before Slice 2 begins.

## 7. Other decisive items independently confirmed (re-derived, not merely trusted)

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Production diff A→I is exactly 6 files | VERIFIED | §3 above |
| 2 | Contract/Gate/verifier byte-identity | VERIFIED | §4 above |
| 3 | `_ELIGIBLE_MECHANISM_IDS` unwidened | VERIFIED | `hpac_verifier.py:128` unchanged |
| 4 | FIDO2/CTAP absent from new surface | VERIFIED | no `fido2`/`ctap` import in any of the 6 diffed files |
| 5 | Fresh 95-test Slice-1 suite green, unedited | VERIFIED | re-run: `95 passed` (no test file modified by this IV) |
| 6 | Sole `HPACWriterCapability(` construction site | VERIFIED | one hit repo-wide: `hpac_foundation.py:548` |
| 7 | `writer()` fixture-only hard stop preserved | VERIFIED | `hpac_foundation.py:557-563` unchanged |
| 8 | Non-agent-importable consumer fence | VERIFIED | no import of the PAWA modules outside the PAWA family / `cli.py` / `commands/**` / `core/agent.py` |
| 9 | Runtime / first-effect unchanged | VERIFIED | `pcae runtime inspect`: Observed / observe / unavailable, 0 plugins, 0 capabilities |
| 10 | 14 historical guard reconciliations non-weakening | VERIFIED (sampled) | `git show --stat` on `5ce6f3b5`/`baec05e8`: additive-only diffstats, no `def test_` removed |
| 11 | "13 deselected baseline failures" — itemized node-id list | **NOT VERIFIABLE from repo state** | No itemized node-id list exists anywhere in the repo (`.pcae/phase-completion-metadata.json`, the phase doc, or any script) — only an aggregate prose count. Flagged as a documentation/provenance gap in `.1R.30R.3.1`'s own completion artifacts (non-blocking on its own), not evidence of a Slice-1 regression. |

## 8. What this IV did not exhaustively complete

Given the BLOCKED-triggering finding in §5, this report stops short of
mechanically completing all ~96 items of the phase prompt's fresh
`.1R.30R.3.2` suite outline and the full fixed-SHA broad guard sweep, per the
phase's own instruction to stop at a genuine BLOCKED condition rather than
pad further work once one is found and independently confirmed. §7 lists
what was independently re-derived beyond the decisive finding. A successor
repair phase should re-run the remaining matrix items against the repaired
code.

## 9. Scope fence preserved

No production repair, no contract edit, no test/guard weakening, no Slice 2
(RHAMP-FIDO2-CREDENTIAL/1.0, RHAMP-COUNTER-STATE/1.0, enrollment,
`FIDO2HumanAuthenticator`), no `hpac_verifier` REAL-mechanism change, no
`_ELIGIBLE_MECHANISM_IDS` widening, no protected presentation, no
`require_real_assurance` wiring through Gate 5/9, no N-16-6/N-16-7, no
Slice C, no first external effect, no execution enablement. Runtime remains
Observed / observe / unavailable. N-23-1 / N-23-2 carried unchanged.

## 10. N-16-5 status

**NOT CLOSED.** Slice 1 is IMPLEMENTED but its own IV (`.1R.30R.3.2`) is
**BLOCKED** on the finding in §5 — Slice 1 cannot be declared "IV COMPLETE"
until the successor repair phase (§6) closes this finding and a fresh IV
confirms it.

## 11. Governance incident (preserved)

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved. Only
the primary human-authorized operator holds `.1R.30R.3.2` lifecycle
authority. The investigative/read-only portion of this IV (source review,
test re-runs, the independent adversarial reproduction in §5.3, sampled
guard-reconciliation review) was performed by a delegated research pass;
**all governed commit/push/phase-completion actions for `.1R.30R.3.2` were
performed directly by the primary human-authorized operator**, not by a
delegated worker.

## 12. Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1.1` — N-16-5 PAWA `HPACWriterCapability`
Seal-Forgery / One-Operation-Bypass Repair (see §6). Requires its own
separate explicit human authorization; ID recommended, not reserved. Do not
begin it here. Do not begin Slice 2. Do not implement RHAMP credential
sidecars, RHAMP counter-state, credential enrollment, or
`FIDO2HumanAuthenticator`. Do not modify `hpac_verifier` for REAL
authentication. Do not widen `_ELIGIBLE_MECHANISM_IDS`. Do not implement
protected presentation. Do not wire `require_real_assurance` through Gate
5/9. Do not begin N-16-6 or N-16-7. Do not begin Slice C. Do not implement or
call the first external effect. Do not enable execution.
