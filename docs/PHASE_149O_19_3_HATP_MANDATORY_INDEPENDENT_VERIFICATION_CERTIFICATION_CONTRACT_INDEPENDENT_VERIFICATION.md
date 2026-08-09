# Phase 149O.19.3 — HATP Mandatory Independent-Verification Certification Contract Independent Verification

**Phase type:** Independent contract verification only. No `src/pcae/**`
file, no HMIC-001, HMRC-001, HATP-001, HSCE-001, RAE-001, RWMPC-001,
PBPA-001, or PBPC-001 contract file was modified to produce this
document. No certification artifact, active-certification pointer, or
revocation record was created. The hard-coded
`mandatory_consumption_implementation_independently_verified = False`
readiness ceiling (`hatp_mandatory_cutover.py:842-853`) is unchanged.

**Subject:** HMIC-001 v1.0
(`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`),
frozen by Phase 149O.19.2, status at entry: **FROZEN — READY FOR
INDEPENDENT CONTRACT VERIFICATION (not VERIFIED)**.

---

## 1. Baseline (Confirmed by Direct Inspection)

At phase entry: repository clean, `origin/main..HEAD = 0`. `pcae
health` healthy. `pcae check` passed. `pcae status coherence`
coherent. `pcae doctor task-memory` reports only pre-existing,
unrelated warnings (seven historical `tasks/done/` entries missing from
`tasks/DONE.md`, predating this phase and outside its allowed-file
scope — not remediated here). `pcae push check` clean
(`nothing_to_push`). `pcae runtime inspect` returns `Observed / observe
/ unavailable`. `pcae notify status` reports Telegram configured,
enabled, and ready. `pcae phase-report show --latest` and `pcae
phase-report reconcile --phase-id 149O.19.2` both confirm, with zero
mutation, that Phase 149O.19.2 is `status: completed`, `report
completeness: complete`, at commit `679f9ba6`, pushed, HMIC-001 v1.0
FROZEN, 144/12/32 counts as declared, no certification state, hardcoded
`False` ceiling unchanged, HATP production **NOT READY**, runtime
**Observed / observe / unavailable**.

## 2. Primary Sources Read

Read in full, directly: the 1,557-line HMIC-001 v1.0 contract
(`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`,
§0-§48) and the 925-line 149O.19.1 architecture document
(`docs/PHASE_149O_19_1_..._ARCHITECTURE.md`, §1-§33). Cross-checked
version headers of all seven upstream/adjacent contracts (HMRC-001,
HATP-001, HSCE-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001). Read and
grepped the fourteen `src/pcae/**` production files HMIC-REQ-050 names,
plus their direct `pcae.*` import graphs (via Python `ast`, not regex),
plus `hatp_providers.py`, `hatp_fido2_provider.py`, and
`hatp_piv_provider.py` (not in the frozen set — see §7 below).
Inspected `pyproject.toml`/editable-install topology and the current
interpreter's module resolution.

**149O.19.2's own prose/test expectations were not trusted.** Every
count and structural claim below was independently mechanically
recomputed from the contract text itself (regex/AST extraction, not
transcription).

---

## 3. Requirement Inventory (Independent, Mechanical)

Extracted every `**HMIC-REQ-###` bold definition via regex over the
contract's raw text.

- **Expected:** HMIC-REQ-001..144, sequential, gapless, unique.
- **Observed:** 144 bold definitions. `sorted(ids) == list(range(1,
  145))`. Zero duplicates. Zero gaps.
- **Result: CONFIRMS the contract's own declared count.**

## 4. Invariant Inventory (Independent, Mechanical)

Extracted every `**CIVC-#.**` bold definition.

- **Expected:** CIVC-1..12.
- **Observed:** exactly `{1..12}`, no gaps, no duplicates.
- **Result: CONFIRMS.**

## 5. Attack Matrix Inventory (Independent, Mechanical)

Extracted the §41 table's row-number column between the `## 41.` and
`## 42.` headers.

- **Expected:** 32 rows, sequential.
- **Observed:** `[1..32]`, sequential, no gaps, no duplicates. Every
  row cites at least one `HMIC-REQ-###` or `§NN` normative anchor
  (independently checked by regex against every data row — none was
  found citing no anchor at all).
- **Result: CONFIRMS.**

---

## 6. Semantic Walls, Threat Model, Authority (Independent Read)

**Semantic walls (§5, HMIC-REQ-009-010):** the twelve-line
non-collapse block (`phase completed ≠ certification`, …,
`certification valid ≠ HATP production READY`) is present, and its
binary-readiness restatement (HMIC-REQ-107: exactly `VALID` → `True`,
every other status → `False`, no `VALID_WITH_WARNING`) is unambiguous.
No clause anywhere in the document grants partial credit. **No
ambiguity found.**

**Threat model (§6):** Threat-A (agent/attacker: can edit repo, run
tests, commit, push, call any public function, invoke read-only
inspection) vs. the Class-B Protected Admin Authority (real OS write
access to the Protected Root) is stated identically to HMRC-001's own
threat model, with root/platform compromise (Threat-B) explicitly and
consistently out of scope. **No overclaim found**: HMIC-REQ-015
explicitly names its own residual limitation (§19) rather than
implying whole-program formal identity.

**Write/read authority (§7):** the sole authority is
`PCAE_BOOTSTRAP_ADMIN_PRINCIPAL`, reused from HMRC-REQ-041's "Protected
Activation Authority" — not a new principal. HMIC-REQ-017/020 close off
every application-level fake-admin vector (username string, env var,
CLI boolean, Git author identity, repo ownership) explicitly and by
name. HMIC-REQ-019 grants read-only access to the agent principal with
an explicit "SHALL NOT imply write authority" clause. **Independently
confirmed against current source**: a repository-wide grep for
`certifications.json`, `certification-bindings.json`,
`mark_independently_verified`, `set_certified`, `create_certification`,
`activate_certification`, `revoke_certification` across all of
`src/pcae/**` returns **zero hits** — no such writer or state exists
today, consistent with the contract's "not yet implemented" status
(new test:
`test_no_certification_writer_or_state_exists_anywhere_in_src`,
`test_no_certification_state_files_exist_under_repository_or_pcae_dir`).

**Protected root (§8):** exactly `HATPTrustStore.production().root`,
reused, no second root introduced, no override accepted (HMIC-REQ-021,
023). Cross-checked against
`hatp_bootstrap.py::_default_production_trust_root` — the function
this contract names is the one that actually exists and is called by
the frozen `hatp_bootstrap.py`/`hatp_mandatory_cutover.py` files today.

---

## 7. Implementation Identity — The Central Finding

This is the highest-risk area named by both the contract's own §47
"Next Phase" instruction and this verification's governing prompt, and
where this phase's independent attack effort concentrated.

### 7.1 Formula (independently reconstructed)

`implementation_scope_digest` = SHA-256 hex digest of the
concatenation, in lexicographic path order, of per-file records
`<canonical_path> + "\0" + <sha256_hex_of_file_bytes> + "\n"`
(HMIC-REQ-054-058), computed over exactly eighteen enumerated paths
(HMIC-REQ-050) — fourteen `src/pcae/**` files plus the four bound
contract files themselves. `implementation_commit` (git HEAD SHA) is a
required, independently-compared identity term alongside it
(HMIC-REQ-046-049): either mismatching alone fails validation. This
formula leaves **no implementation choice** — algorithm, delimiter,
order, and canonicalization are all frozen exactly (HMIC-REQ-054-058).

### 7.2 Digest-domain collision/ambiguity attack (independently reimplemented, tested)

A naive "sort and concatenate raw file bytes" scheme is famously
ambiguous: `("ab","c")` and `("a","bc")` hash identically under plain
concatenation. This verification independently reimplemented
HMIC-REQ-057's exact per-record scheme
(`tests/test_phase_149o_19_3_hmic_contract_independent_verification.py::test_digest_domain_resists_naive_path_content_concatenation_ambiguity`)
and confirmed the null-byte-delimited, newline-terminated record
construction does **not** reproduce this collision: the null byte
between path and digest, and the newline terminating each record, make
every record self-delimiting. **Verdict: digest domain is unambiguous.**

### 7.3 Path canonicalization attack (independently tested)

Six adversarial path variants (`./`-relative, `../`-traversal,
absolute-prefixed, backslash-separated, case-varied, double-separator)
were checked against the eighteen literal enumerated strings for exact
match. None match — HMIC-REQ-055's "no path normalization beyond exact
string match" is real, not aspirational, because the enumeration itself
contains no ambiguous entries. **Verdict: no traversal/normalization
ambiguity.**

### 7.4 Frozen file-set existence and non-symlink check

All eighteen paths exist on disk today; none is a symlink; no parent
directory component up to the repository root is a symlink either.
**Verdict: existence confirmed** — but per this contract's own
instruction, existence is necessary, not sufficient; completeness is
the real question (§7.5).

### 7.5 Transitive-dependency completeness attack — BLOCKING FINDING

HMIC-REQ-052 claims the eighteen-file enumeration is "the union of" two
named sources and that "no named file was excluded." This verification
independently computed the one-hop `pcae.*` import closure (via Python
`ast`, not the contract's own prose) of every frozen file and found
this claim **false** for one specific, security-relevant dependency:

```
core/hatp_ag_authority.py            (frozen)  -> imports pcae.core.hatp_providers  (NOT frozen)
core/hatp_rollback_consumption.py    (frozen)  -> imports pcae.core.hatp_providers  (NOT frozen)
core/human_approval_trusted_provenance.py (frozen) -> imports pcae.core.hatp_providers (NOT frozen)
```

`hatp_providers.py` itself defines
`create_production_hardware_provider()`, which dynamically imports and
returns `Fido2HardwareProvider` (from `hatp_fido2_provider.py`, 19,465
bytes) or, with explicit fallback, `PivHardwareProvider` (from
`hatp_piv_provider.py`). **Neither `hatp_providers.py`, nor
`hatp_fido2_provider.py`, nor `hatp_piv_provider.py` is named anywhere
in HMIC-REQ-050's eighteen-file enumeration, nor in HMIC-REQ-052's own
cited "minimum transitive-dependency evaluation set."**

`Fido2HardwareProvider.verify()` (`hatp_fido2_provider.py:341-397`) is
where the actual FIDO2 cryptographic signature/attestation
verification happens, producing the raw
`HATPProviderVerificationOutcome(signature_valid=…,
human_presence_proven=…)` facts that `verify_hatp_proof` (in the
*frozen* `human_approval_trusted_provenance.py`) combines with
protected trust-store lookups to reach a HATP verification status —
the status that ultimately gates real AG3/AG5 rollback execution
through the mandatory-consumption chain this certification exists to
attest was correctly implemented.

**Concretely:** an edit to `hatp_fido2_provider.py::Fido2HardwareProvider.verify()`
that unconditionally returns `signature_valid=True,
human_presence_proven=True` — a complete bypass of the real hardware
check — changes **zero bytes** of any file named in HMIC-REQ-050.
`implementation_scope_digest` would be identical before and after this
edit. A certification computed before such an edit would continue to
validate `VALID` after it, silently certifying an implementation that
no longer performs real hardware verification.

This is independently reproduced, not theoretical, by
`tests/test_phase_149o_19_3_hmic_contract_independent_verification.py::test_hatp_providers_hardware_verification_modules_are_not_in_frozen_set`,
which asserts the exact import edges above and the presence of a
`signature_valid=True` return in the unbound file, and by
`test_frozen_set_first_party_import_closure_names_every_pcae_dependency_or_is_documented`,
which mechanically walks the strict HATP/HMRC/PB-core subset's import
graph and fails on any *undocumented* unbound dependency (currently
passing only because `hatp_providers` is explicitly, narrowly
allowlisted in the test with this finding as its documented rationale
— not because the gap is closed).

**This is Blocking** under this verification's own governing
criterion: "the 18-file set under-binds an authority-sensitive
production dependency." HMIC-REQ-052's completeness claim is
incorrect as written; HMIC-REQ-063's named residual limitation
(import-shadowing/executed-code binding) is a *different*, honestly
disclosed limitation and does not cover this gap — this gap is about
on-disk byte coverage within the certified repository itself, requiring
no shadowing or interpreter trickery at all.

### 7.6 Other transitive dependencies of the frozen set — reviewed, non-blocking

The strict-subset import-closure walk (excluding the three broad
CLI-dispatch/agent-lifecycle files `cli.py`, `commands/agent.py`,
`core/agent.py`, whose own `pcae.*` import lists are dominated by
dozens of unrelated command modules and generic task/git/policy
utilities with no HATP/HMRC logic of their own) surfaces two further,
already-documented, non-blocking dependencies:

- **`pcae.core.paths`** — a generic repository-root/`HarnessPath`
  path-join helper with no HATP/consumption-authority logic. A utility
  dependency whose change cannot alter authority semantics.
- **`pcae.core.gate_dry_run`, `pcae.core.scope_preflight`,
  `pcae.core.shell_gate`** — imported by `permission_broker.py`
  (frozen). These implement Permission Broker *policy-decision-support*
  logic, downstream of `permission_broker.py`'s own bound bytes.
  HMIC-REQ-068 already explicitly excludes PBPA-001/PBPC-001 (PB
  *policy*) from `contract_versions` on the stated reasoning that "PB
  policy is a separate, downstream concern from the consumption
  chain's own implementation correctness." These three modules
  implement that same, already-excluded PB policy-decision concern —
  leaving them unbound from `implementation_scope_digest` is
  **consistent with, not an exception to**, the contract's own stated
  line, not a second undisclosed gap.

A third, lower-confidence observation: `rollback_approval_evidence.py`
(frozen) imports `pcae.governance.publication.{chgr_envelope,
coordinator, storage}` and `pcae.interactive_workflow.{models.session,
publication_handoff.models, session.identity}`, used by a
publication-pipeline helper function within that file
(`PublicationCoordinator`/`PublicationRecordStore`-based). This
verification did not fully trace whether this code path is reachable
from `assess_hatp_mandatory_activation_readiness`'s own call graph or
is a separate, unrelated RAE-adjacent publication concern; it is
flagged here as a residual open question for the recommended
contract-repair phase to resolve definitively, not asserted as a second
Blocking finding, since (unlike §7.5) no concrete exploitable scenario
was mechanically demonstrated.

---

## 8. Editable-Install / Runtime-Source Binding (HMIC-REQ-063-064)

Confirmed by direct inspection of the running interpreter environment:
the global `pcae` CLI entrypoint (`/opt/homebrew/bin/pcae`, backed by
Homebrew CPython 3.14.5) is installed via a genuine PEP 660 editable
install (`/opt/homebrew/lib/python3.14/site-packages/pcae_harness-0.1.0.dist-info/direct_url.json`
→ `{"dir_info": {"editable": true}, "url":
"file:///Users/atilamadai/repos/pcae-harness"}`), and
`pcae.core.hatp_mandatory_cutover.__file__` resolves to this exact
checkout's on-disk file — confirmed independently by
`test_current_interpreter_resolves_frozen_modules_to_this_repository_checkout`.
HMIC-REQ-064's "editable-install / source-checkout topology" assumption
is realistic and currently satisfied, not aspirational.

The repository's own pinned test venv (`.venv`, CPython 3.9.6) is a
**separate** interpreter/installation from the global CLI's Homebrew
CPython 3.14.5 install; both resolve the same on-disk source correctly
in this checkout today, but this is an environment-topology fact
HMIC-REQ-065 already names as out of this contract's scope
("interpreter version… separate, future deployment/environment-
readiness concern") — **non-blocking**, consistent with the contract's
own explicit scope carve-out.

**PYTHONPATH-shadow attack (§41 attack #29):** independently confirmed
structurally reproducible today — `sys.path` places the editable
install's `src/` entry *after* `site-packages`, so a higher-precedence
`pcae` package (planted via `PYTHONPATH` or a competing
`site-packages` entry) would be imported instead, with
`implementation_scope_digest` computed over the correct on-disk bytes
remaining unaware of the substitution. This is **exactly** HMIC-REQ-063's
own named, explicitly disclosed residual limitation ("v1.0 of this
contract does NOT implement an executed-code/runtime-module-resolution
check… not a silent gap"). Because the contract discloses this
honestly and does not claim to have solved it, this is **non-blocking**
under this verification's own criteria — disclosed limitations are
explicitly distinguished from silent gaps (per §7.5's contrast).

---

## 9. Contract Binding and Drift (§20)

The minimal `contract_versions` set — HMRC-001, HATP-001, HSCE-001,
RAE-001 — matches all four current contract version headers exactly
(v1.0, v1.0, v1.1, v1.0; independently re-read from each contract file
directly, not from HMIC-001's own summary table). HMIC-REQ-053 draws an
explicit, correct distinction this verification confirms is real, not
redundant: the four contract files' *bytes* participate directly in
`implementation_scope_digest` (as four of the eighteen frozen paths),
while `contract_versions` separately compares version-header *strings*
at validation time (§31 step 10). These are genuinely two independent
detection mechanisms — a prose edit without a version bump is caught
only by the digest binding; a version bump alone (even with reverted
bytes) is caught only by the version-string comparison. **No gap
found**: unlike §7.5's transitive-dependency omission, the four
contract files ARE in the frozen set, so this binding is complete as
designed.

RWMPC-001/PBPA-001/PBPC-001's exclusion from `contract_versions`
(HMIC-REQ-068) is reasoned consistently with HMRC-001's own scope
statement and, per §7.6 above, consistently extends to the PB
policy-support modules this verification separately checked.

---

## 10. Storage Topology, Schemas, Active Pointer, Revocation, Supersession, Concurrency (Read-Through Verification)

These sections (§8-§30, HMIC-REQ-021-102) were read in full and checked
for authority-sensitive ambiguity, TBDs, or implicit-selection language.
No ambiguity was found:

- **Storage topology (§9):** exactly two frozen-named files under the
  Protected Root, both entry-keyed by `(repository_instance_id,
  canonical_deployment_root)` — genuinely repository/deployment-scoped,
  a real improvement over the Cutover Record's own acknowledged flat
  single-slot topology (HMIC-REQ-027 states this explicitly; nothing in
  HMIC-001 worsens the Cutover Record's own limitation, and nothing
  introduces a second flat-slot crossover).
- **Schemas (§11-13):** both `CertificationRecord` and
  `CertificationBinding` are closed-field, closed-vocabulary
  (`"active"|"revoked"` only), with `status`/`revoked_at` validated
  together (HMIC-REQ-034) and a strict-positive-integer `version` field
  that explicitly rejects a JSON boolean (HMIC-REQ-033) — mirroring
  `hatp_bootstrap.py`'s and `hatp_mandatory_cutover.py`'s existing
  strict-parser discipline by direct citation, not by fresh invention.
- **Active pointer (§26):** `active_certification_id` is an explicit,
  exact-match pointer into `certifications.json`; HMIC-REQ-085
  explicitly forbids "implicit latest" (sort-by-`certified_at`,
  first-found, or any other implicit discovery) — the same discipline
  HSCE-001/HMRC-001 already enforce elsewhere, extended, not invented,
  here.
- **Revocation (§28-29):** field mutation, not deletion
  (HMIC-REQ-091); explicit-ID-only (HMIC-REQ-092, no "revoke latest");
  and — critically — HMIC-REQ-095 explicitly states revocation
  post-`HATP_MANDATORY`-activation "SHALL NOT, and structurally
  cannot," cause a mode downgrade, because the Cutover Record's own
  transition graph (HMRC-REQ-038/039) has no reverse edge at all. This
  is a real structural guarantee, not merely a policy statement — no
  future implementation of HMIC-001 could introduce a downgrade path
  without *also* amending HMRC-001's transition graph, which HMIC-001
  is explicitly forbidden from doing (HMIC-REQ-002, HMIC-REQ-136).
- **Concurrency (§30):** a single, dedicated
  `.certification-transition.lock` (distinct from the Cutover Record's
  own `.cutover-transition.lock`) serializes every certification write;
  HMIC-REQ-101 explicitly forbids acquiring this lock during read-only
  validation (avoiding a lock-ordering hazard with the activation
  lock) and explicitly forbids any certification *write* from nesting
  inside `activate_hatp_mandatory`. No circular-acquisition scenario is
  left ambiguous — lock ordering is fully specified, not merely
  implied.

**No Blocking finding in this section.**

---

## 11. Self-Certification, Bootstrap Circularity, Cross-Contract Independence

- **Self-certification (§7, §24, CIVC-12):** confirmed both textually
  (HMIC-REQ-016-020, 079-082 close every application-level fake-admin
  vector by name) and against current source (§6 above: zero hits for
  any certification-writer-shaped symbol anywhere in `src/pcae/**`
  today). **CLOSED.**
- **Bootstrap circularity (HMIC-REQ-126):** certification authority is
  explicitly stated to exist "independently of, and prior to, any
  `HATP_MANDATORY` activation" — no future implementation may require
  an already-activated deployment as a precondition for certifying it.
  **No circularity found.**
- **Cross-contract independence (§35, §38):** HMIC-REQ-118-127 and
  HMIC-REQ-134-138 each explicitly deny a specific cross-authority
  conflation (no PB evaluation, no HATP approval, no execution
  capability, no redefinition of HMRC/HATP/RAE/PB ownership). Read
  against each named upstream contract's own current scope statement,
  no contradiction was found.

---

## 12. Attack Matrix — Independent Reproduction (Representative Sample)

All 32 rows were read against their cited requirement/section anchors
and found internally consistent (expected result matches the citation's
actual normative text) for every row, including the highest-priority
ones this verification independently re-derived rather than trusting:

- **#10 (old-implementation replay)** → HMIC-REQ-049/§31 step 9:
  confirmed the step-ordering table (§31) evaluates this before
  `CONTRACT_MISMATCH`, so an implementation mismatch is reported as
  `IMPLEMENTATION_MISMATCH`, never masked by a later step.
- **#22 (implicit-latest attempt)** → HMIC-REQ-085: confirmed
  structurally impossible as designed, not merely policy-forbidden,
  because the validator's only lookup path (§31 steps 4-5) reads the
  explicit pointer field, never `certifications.json` directly for
  selection.
- **#29 (import-shadowing)** → HMIC-REQ-063: confirmed as a named,
  disclosed limitation, not solved — see §8 above for independent
  structural reproduction.
- **#32 (certify-activates-itself)** → HMIC-REQ-118-121: confirmed no
  code exists yet at all (nothing to couple), and the *contract text*
  itself never describes `CERTIFY` as triggering `ACTIVATE` or vice
  versa in any of its ceremony descriptions (§23, §34-35).

No row was found to have an ambiguous or missing expected outcome.
**Attack-matrix coverage assessed as complete** for the threat classes
it names; §7.5's finding is a distinct completeness gap in the
*implementation-identity binding itself* (upstream of the attack
matrix, which assumes a correctly-scoped digest to begin with) — the
attack matrix's own row #10/#11/#12/#13 correctly describe the
*intended* behavior of a scope digest that, per §7.5, is not yet
complete.

---

## 13. Test Suites Run

**New independent test module**
(`tests/test_phase_149o_19_3_hmic_contract_independent_verification.py`,
34 tests): derives expectations directly from the HMIC-001 contract
text and from independent reimplementation of its digest algorithm —
not from the 149O.19.2 freeze-test module's own fixtures. **34 passed,
0 failed.**

**149O.19.2 freeze suite, run as regression only** (not as this
phase's own verdict): **35 passed, 0 failed.**

**Fast Green** (`.venv/bin/python3 -m pytest -m fast_green`,
CPython 3.9.6): raw undeselected run: **5529 passed, 28 failed, 1
skipped, 25639 deselected**. All 28 raw failures are the same
git-diff-baseline-anchored test class 149O.19.2 already documented as
pre-existing (e.g. `test_phase_149o_18d_...::test_no_cli_files_touched`,
`test_phase_149o_17_...::test_no_src_pcae_files_changed_name_only`) —
tests that assert "no file changed since phase X's own entry commit"
for phases whose entry commit is now dozens of commits behind `HEAD`;
they fail identically regardless of this phase's own (zero) `src/pcae`
changes, confirmed by this phase's own
`test_no_src_pcae_file_modified_since_149o_19_2_entry_commit`. A
second, independent run deselecting those 28 surfaced **4 additional,
order-dependent failures**, all in `tests/test_backend_cli.py`
(`TestBackendReviewApprove::test_approve_succeeds_with_correct_ids`,
`test_approve_json_no_execution`,
`TestBackendReviewReject::test_reject_json_no_secrets`,
`Test95MFixtureCLI::test_fixture_save_and_verify`) — confirmed flaky,
not caused by this phase: all four pass when run in isolation, and all
307 tests in `test_backend_cli.py` pass when that file is run alone
(unrelated to HATP/HMIC/PB entirely; a cross-module test-isolation
artifact). Final deselected clean run (all 32 known-flaky/pre-existing
node IDs deselected): **5525 passed, 0 failed, 1 skipped, 25671
deselected** — the value recorded in this phase's structured
`fast_green` metadata field.

**Broad sweep** (`-k "149o or hmic or hatp or rae or permission_broker"`):
**4,186 passed, 154 failed, 4 skipped, 26,853 deselected.** All 154
failures are in historical phase-specific verification modules
(`test_phase_149o_1h_6_...`, `test_phase_149o_3_...`,
`test_phase_149o_4_...`, `test_phase_149o_5_...`,
`test_phase_149o_7_...`, `test_phase_149o_9_...`,
`test_phase_149o_rollback_approval_evidence_...`) — the same class of
git-diff-baseline-anchored and timestamp-grammar-fixture assertions
whose entry-commit references have aged past `HEAD`; none reference
HMIC-001, `hatp_providers.py`, or any file this phase touched. Since
this phase's own `git diff --stat` against `src/pcae` is empty (§17),
no test in this sweep could have newly failed as a result of this
phase's own changes — every failure here necessarily predates it.

**Report trust / consistency:** `pcae phase-report trust` → `Report is
COMPLETE. All trust fields present.` `pcae phase-report consistency` →
`Result: consistent` (source revision `a9a3d060`, report digest
`f195ed54…`).

---

## 14. Findings Summary

### Blocking

1. **HMIC-REQ-052's transitive-dependency-coverage claim is false for
   `hatp_providers.py` (and, transitively, `hatp_fido2_provider.py`/
   `hatp_piv_provider.py`)**, which implement the actual hardware
   signature/human-presence verification consumed directly by three
   frozen files. This is invisible to `implementation_scope_digest`
   and is not covered by HMIC-REQ-063's separate, honestly-disclosed
   import-shadowing limitation. See §7.5.

### Non-Blocking

1. `pcae.core.paths` and the Permission-Broker policy-support trio
   (`gate_dry_run`, `scope_preflight`, `shell_gate`) are unbound but
   are, respectively, a pure utility and an already-contract-excluded
   PB-policy concern (§7.6).
2. `rollback_approval_evidence.py`'s publication/interactive-workflow
   imports are an open question flagged for the repair phase, not a
   demonstrated exploit (§7.6).
3. The PYTHONPATH-shadow / executed-code-binding limitation is real but
   is the contract's own named, disclosed v1.0 limitation, not a silent
   gap (§8).
4. Pre-existing `pcae doctor task-memory` warnings (seven historical
   `tasks/done/`/`tasks/DONE.md` entries), unrelated to this phase and
   predating it.

---

## 15. Explicit Verdicts

**A. Verification Verdict:**

```
NOT VERIFIED — BLOCKING HMIC-001 CONTRACT FINDING
```

One Blocking finding (§7.5/§14) survives independent attack: the
eighteen-file frozen authority-bearing set under-binds an
authority-sensitive production dependency (`hatp_providers.py` +
its own hardware-provider modules). Every other section attacked —
requirement/invariant/attack inventory, semantic walls, threat model,
authority/write/read boundaries, storage topology, schemas, active
pointer, revocation/supersession, concurrency, contract binding,
self-certification, bootstrap circularity, cross-contract
independence, digest-domain construction, and path canonicalization —
was independently confirmed sound with no ambiguity found.

**B. Implementation-Identity Verdict:**

```
C. IMPLEMENTATION IDENTITY UNDER-BINDS AUTHORITY-RELEVANT EXECUTABLE
   STATE — BLOCKING
```

The `(implementation_commit, implementation_scope_digest)` pair is a
sound, unambiguous, collision-resistant construction *over the file set
it is given* — the algorithm itself (§7.1-7.3) is not the defect. The
defect is the file set's incompleteness (§7.5).

**C. Frozen File-Set (Transitive) Verdict:**

```
INSUFFICIENT
```

Omitted: `src/pcae/core/hatp_providers.py`,
`src/pcae/core/hatp_fido2_provider.py`,
`src/pcae/core/hatp_piv_provider.py`. Authority effect: an edit to any
of these three files that alters real hardware/cryptographic
verification behavior (e.g., a `Fido2HardwareProvider.verify()` that
always reports `signature_valid=True`) is completely invisible to
`implementation_scope_digest` and therefore to certification validity.

**D. Editable-Source/Runtime-Binding Verdict:**

```
B. SAFE BUT HAS NON-BLOCKING DEPLOYMENT LIMITATIONS
```

Today's editable-install topology correctly resolves frozen modules to
this checkout (§8, independently confirmed by direct interpreter
inspection). The PYTHONPATH-shadow / executed-code-binding gap is real
but is the contract's own honestly-disclosed v1.0 limitation
(HMIC-REQ-063), not a silent one — consistent with this verification's
own Blocking/non-Blocking distinction.

**E. Contract-Binding Verdict:**

```
CLOSED — version AND content-digest binding both present, deliberately
redundant, and independently confirmed sufficient (§9)
```

**F. Self-Certification Verdict:**

```
CLOSED
```

**G. Concurrency Verdict:**

```
DETERMINISTIC / FAIL-SAFE, at the contract-text level — creation,
supersession, revocation, and activation interaction are all fully
ordered by a single dedicated lock with explicit non-nesting rules;
no implementation exists yet to test empirically (§10)
```

---

## 16. Recommended Next Phase

Per §140/§14's Blocking finding, this verification does **not**
recommend proceeding directly to `149O.19.4` (Implementation Plan) as
149O.19.2's own §47 anticipated. It recommends a **narrow
contract-repair phase** — `149O.19.3R` (or repository-conventional
equivalent) — scoped exclusively to:

1. Amend HMIC-REQ-050's eighteen-file enumeration to add
   `core/hatp_providers.py`, `core/hatp_fido2_provider.py`, and
   `core/hatp_piv_provider.py` (or otherwise resolve the gap the
   contract's own authors judge correct — e.g., an explicit,
   contract-frozen statement that hardware-provider modules are
   deliberately out of `implementation_scope_digest`'s scope and are
   instead owned by a separate, named hardware-readiness contract, if
   that is the intended design — but HMIC-001 v1.0 as written makes no
   such carve-out and instead affirmatively claims completeness it does
   not have).
2. Resolve the `rollback_approval_evidence.py` publication-import
   open question named in §7.6.
3. Re-verify the amended file count, re-run this phase's digest-domain
   and path-canonicalization tests against the corrected enumeration,
   and re-issue a verification verdict before `149O.19.4` (Implementation
   Plan) may begin.

No implementation phase should begin before this repair completes and
is itself independently re-verified, per this contract's own §47
gating language ("No implementation SHALL begin before 149O.19.3
completes"), which this verification reads as requiring completion
*with a passing verdict*, not merely running to completion with a
Blocking finding.

---

## 17. Explicit Confirmations (Restated for the Phase Report)

No production source (`src/pcae/**`) was modified. HMIC-001 v1.0,
HMRC-001 v1.0, HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0, RWMPC-001
v1.0, PBPA-001 v1.0, and PBPC-001 v1.2 all remain byte-unchanged. The
current hard-coded `False` readiness ceiling remained unchanged. No
certification artifact, Active-Certification Pointer, or revocation
record was created — confirmed both by repository search and by
independent test
(`test_no_certification_state_files_exist_under_repository_or_pcae_dir`).
No Cutover Record or activation marker was created or modified. No real
`HATP_MANDATORY` activation occurred. No Class-B provisioning occurred.
No Permission Broker behavior changed. `POL-005` remained unchanged. No
`COMP-002` capability was implemented. No self-certification
implementation was introduced. B-149O-1..4 remain **INDEPENDENTLY
CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT BOUNDARY —
DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED**, unchanged by this phase.
HATP production remains **NOT READY**. Runtime remains **Observed /
observe / unavailable**.
