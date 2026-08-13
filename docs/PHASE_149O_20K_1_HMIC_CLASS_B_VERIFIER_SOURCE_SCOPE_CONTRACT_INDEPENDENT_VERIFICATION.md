# Phase 149O.20K.1 — HMIC Class-B Verifier Source-Scope Contract Independent Verification

**Purpose.** Independently verify Phase 149O.20K's HMIC-001 v1.2 → v1.3
amendment (contract §53), without trusting 149O.20K's narrative,
dependency graph, AST walk, Category A/B/C/D/E classification, 28-file
conclusion, version-bump rationale, cycle/self-binding analysis, or
historical-test-failure attribution. Verification-only: no production
source modification, no further HMIC contract modification, no
production alignment, no readiness integration, no Class-B provisioning,
no HATP certification/activation.

## 1. Exact commit reconstruction

Independently confirmed via `git log --format='%H %P'`:

- `3e1137ef19c354f221a1b1b1a6d358259e6bfc9a` — "Phase 149O.20K: HMIC
  Class-B Verifier Source-Scope Contract Evolution (v1.2 -> v1.3)" — the
  contract/engineering commit. Its sole parent is
  `e917779b891074bf957823fe6f20277296563745` ("Phase 149O.20J.8: task
  lifecycle transitions (close to idle)"), independently confirmed as the
  true pre-K commit — the state of the repository immediately before
  149O.20K's own contract edit.
- `39c6d8e83a93f6a45abb9636652a4ec712f6b21f` — lifecycle/metadata sync.
- `68cb0b07e663f063dd01898b743a73c3c51f5420` — record post-commit hash.
- `0d91760017f4366bcf485baa16d5ce5891621d36` — sync canonical report
  title/metadata.
- `8e35cfa21ce95e148d49d3365fe6a59de26739dd` — task lifecycle transitions
  (close to idle).

`git diff e917779b 3e1137ef -- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
was read directly and used as the sole source for the semantic diff in
§3 below.

## 2. HMIC v1.2 independently reconstructed

`git show e917779b:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
confirms: `**Version:** 1.2`; HMIC-REQ-050's fenced enumeration has
exactly 25 entries, none of the three Class-B verifier modules present;
HMIC-REQ-052 has exactly two limbs — (a) reachable from
`assess_hatp_mandatory_activation_readiness`'s call graph, (b) reachable
from `validate_active_hatp_mandatory_independent_verification_certification`'s
call graph or the Protected Admin ceremony functions — with no limb (c)
and no mention of `verify_class_b_deployment_conformance` anywhere in the
requirement body. Direct search of `assess_hatp_mandatory_activation_
readiness`'s own body in `hatp_mandatory_cutover.py` (production source,
not the pre-K contract snapshot, since production is unchanged) confirms
it contains no reference to `class_b`, `verify_class_b_deployment_
conformance`, or `hatp_environment_lock_verifier` — limb (a) genuinely
does not reach the verifier island. This independently establishes the
v1.2 gap: it is a real scope gap, not a K-invented pretext.

## 3. HMIC v1.3 exact semantic diff

Read directly from the current contract and cross-checked against the
`git diff` above. Confirmed changes: version header 1.2→1.3 and status
line; a new "Amended by: Phase 149O.20K" provenance line; HMIC-REQ-050's
enumeration widened 25→28 (three `src/pcae/`-relative entries appended:
`core/hatp_class_b_topology_verifier.py`,
`core/hatp_environment_lock_verifier.py`,
`core/hatp_class_b_conformance.py`); HMIC-REQ-052 gains new limb (c)
anchored at `verify_class_b_deployment_conformance`'s call graph; the
attack matrix header changes "37 Scenarios" → "38 Scenarios" with a new
row 38; a wholly new §53 (subsections 53.1–53.14) is appended. No
unrelated normative change was found: every edited line traces to one of
these five changes; no other requirement's text, no other section, no
other contract file was touched (`git status --porcelain` on all four
other bound contracts and `git diff` scoped to the HMIC contract file
alone both confirm this).

## 4. Independent proof a contract amendment was required

Starting from HMIC-REQ-052 v1.2's two limbs (§2 above) and the confirmed
absence of any call-graph path from either bound root
(`assess_hatp_mandatory_activation_readiness`,
`validate_active_hatp_mandatory_independent_verification_certification`,
the admin ceremony functions) into
`verify_class_b_deployment_conformance` or its two sub-verifiers (fresh
`src/`-wide symbol-level text search, zero matches outside the island
itself — §9 below): a byte edit to any of the three Class-B verifier
files today changes zero HMIC-bound digest, because none of the three
files is in `_FROZEN_AUTHORITY_BEARING_FILES`. This is not hypothetical:
`hatp_class_b_topology_verifier.py`/`hatp_environment_lock_verifier.py`
are the exact files 149O.20J.3 through 149O.20J.8 repeatedly patched for
real ACL-classification defects (`writesecurity`/`chown`
reclassification, ACL-only higher-ancestor detection, full ancestor-chain
verification) — each of those five prior repairs changed
`verify_class_b_deployment_conformance`'s real-host verdict while every
HMIC-bound file's digest stayed byte-identical, since none of the five
touched files was HMIC-bound. This is a live-fire demonstration, not a
constructed scenario, of the exact attack limb (c)/attack-matrix row 38
describes. A normative scope amendment was therefore independently
necessary, not merely asserted.

## 5. Current production HMIC identity — independently re-read

`src/pcae/core/hatp_mandatory_certification.py` (unchanged, confirmed
`git status --porcelain` empty for this file before and after this
phase): `_FROZEN_SRC_PCAE_RELATIVE_FILES` = 19 literal entries;
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` = 6 literal entries (five bound
contract documents + `scripts/hatp_certification_admin.py`);
`_FROZEN_AUTHORITY_BEARING_FILES` = their concatenation, with a live
`assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 25` in the module
itself. `_CONTRACT_IDENTITY_FILES` = exactly 5 `(contract_id, path)`
pairs (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001`). None
of the three Class-B verifier module names appear anywhere in this file.
Production is therefore still 25/5, unaligned to v1.3's 28/5 target —
independently and explicitly demonstrated, not assumed.

## 6–9. Fresh static/semantic dependency graph and classification

A throwaway `ast.parse`/`ast.walk` script (not reused from 149O.20K) was
run directly against current on-disk bytes of all three verifier
modules. Results (imports only, PCAE-owned):

- `hatp_class_b_topology_verifier.py`: `from pcae.core import
  hatp_bootstrap` only; rest stdlib (`ast`, `inspect`, `os`, `re`,
  `stat`, `subprocess`, `sys`, `dataclasses`, `enum`, `pathlib`,
  `typing`, `grp`, `pwd`).
- `hatp_environment_lock_verifier.py`: `from
  pcae.core.hatp_class_b_topology_verifier import (...)` only (sibling
  module symbols); rest stdlib.
- `hatp_class_b_conformance.py`: `pcae.core.hatp_bootstrap`,
  `pcae.core.repository_identity`,
  `pcae.core.hatp_class_b_topology_verifier`,
  `pcae.core.hatp_environment_lock_verifier`, `pcae.core.paths`
  (`HarnessPath`); rest stdlib.

No fourth PCAE-owned module reached; no dynamic
(`importlib.import_module`/`__import__`) PCAE-owned import found in any
of the three files (confirmed by AST `Call`-node inspection, not text
search alone).

Classification, independently derived (not copied from K's A–E labels):

- **Authority-sensitive (bind).** All three root modules. Each computes
  or aggregates part of the `COMPLIANT`/`NON_COMPLIANT`/`INDETERMINATE`
  verdict: topology verifier resolves agent identity, mode/group/ACL
  write-access (Linux and macOS ACL text parsing), Trusted-Git and
  Protected-Root ancestor-chain safety; environment-lock verifier
  extends that to interpreter-writability, venv-lock, `PYTHONPATH`/
  `.pth`/module-origin/editable-install checks; the aggregator
  (`hatp_class_b_conformance.py`) calls both sub-verifiers plus its own
  `_check_model_a_deployment`/`_check_deployment_identity` through
  shared `_aggregate_status`/`_build_result` primitives — independently
  confirmed present by direct grep of the aggregator's call sites (§8).
  Aggregation logic itself is authority-sensitive: an edit to how
  `INDETERMINATE` is decided, or omission of either additional check,
  changes the final verdict without touching either sub-verifier's
  bytes.
- **Non-authority-sensitive (exclude).** `pcae.core.paths` — read in
  full (15 lines): a frozen `@dataclass` with only `cwd()` (wraps
  `Path.cwd()`) and `join()` (path concatenation). No ACL, identity,
  I/O, or verdict-affecting logic. In `hatp_class_b_conformance.py` it
  is used only as `root.path` and `HarnessPath.cwd()` — a value carrier,
  never a decision input. Independently confirmed excludable.
- **Already bound, no new decision needed.** `hatp_bootstrap.py` and
  `repository_identity.py` are both already present in
  `_FROZEN_SRC_PCAE_RELATIVE_FILES` (confirmed by direct string search
  of the module's literal tuple) — genuinely authority-sensitive, but
  contribute nothing new to widen.
- **Standard library (Category C, disclosed residual trust).** `ast`,
  `inspect`, `os`, `re`, `stat`, `subprocess`, `sys`, `dataclasses`,
  `enum`, `pathlib`, `typing`, `grp`, `pwd`, `importlib.metadata`,
  `importlib.util`, `site`, `shutil`. HMIC-REQ-065 (read directly,
  unchanged) already names the interpreter/stdlib boundary as
  out-of-scope. This phase does not overclaim HMIC covers Python/runtime
  bytes.
- **External/system tools (Category D).** `git` (resolved via
  `_resolve_trusted_executable`/`_resolve_trusted_executable_with_
  effective_access`), the macOS `ls`-based ACL text format parsed via
  `subprocess.run`, the `pcae` launcher resolved via `shutil.which`, the
  Python interpreter binary, the kernel ACL subsystem. None can be
  brought into HMIC scope by naming a PCAE source file — these remain
  HBDC-001's own environment-lock/deployment-model assumptions and
  HMIC-REQ-063's already-disclosed executed-code/runtime-module-
  resolution limitation (read directly from the contract, unchanged
  since v1.0).
- **Contract/document inputs (Category E).** Independently confirmed
  empty: an AST walk for `open`/`read_text` calls in all three verifier
  modules found none whose argument references any `docs/contracts`
  path. The `read_text` calls found are: a `.pth` file
  (`hatp_environment_lock_verifier.py`), package `direct_url.json`
  metadata (`hatp_class_b_conformance.py`), and the topology verifier's
  own `Path(__file__).read_text(...)` (self-scan for admin-inference
  checks) — none read normative contract bytes at runtime.

## 10. `pcae.core.paths` re-adjudication (not accepted automatically)

`src/pcae/core/paths.py` was read in full — 15 lines, one frozen
dataclass, two trivial methods (`cwd`, `join`), zero conditional logic,
zero I/O beyond `Path.cwd()`. If this module's implementation changed
while all 28 proposed HMIC-bound files stayed byte-identical, no
authority-sensitive semantic could change through it: it carries no ACL,
identity, mode, or verdict logic of its own, only a filesystem-path
value. Independently confirmed non-authoritative; excluded per HMIC-
REQ-052's own existing exclusion precedent (already named there for
limbs (a)/(b)), reapplied under limb (c), not invented new.

## 11. Bootstrap/repository-identity binding re-check

`hatp_bootstrap` and `repository_identity` references in all three
verifier modules resolve to `pcae.core.hatp_bootstrap` and
`pcae.core.repository_identity` — both independently confirmed present,
by exact string match, in `_FROZEN_SRC_PCAE_RELATIVE_FILES` (`"core/
hatp_bootstrap.py"`, `"core/repository_identity.py"`). Already bound;
K did not omit them.

## 12–13. Indirect dependencies and parallel/bypass logic search

Searched all three verifier modules for callbacks, registries, module-
level computed globals, environment-variable parsers beyond what's
already covered, subprocess command builders, serialization/
canonicalization helpers, resource files, package metadata reads: found
only what §6–9 already covers (`importlib.metadata.distribution`,
`shutil.which`, `subprocess.run` for `git`/`ls`). No hidden decision
input found. Searched all of `src/` for a second implementation of
topology/environment-lock/aggregate Class-B logic: none found — see §9's
zero-consumer confirmation, which also rules out a parallel
implementation (a full-repo symbol search for the aggregator's own
exported names found no second definition).

## 14. Independently derived target file set

**Existing 25 (unchanged, verified byte-for-byte against pre-K text):**
the 19 `src/pcae/`-relative entries plus the 6 repository-root-relative
entries listed in `hatp_mandatory_certification.py` (§5).

**Newly required (3, independently derived by the walk in §6–9):**
`src/pcae/core/hatp_class_b_topology_verifier.py`,
`src/pcae/core/hatp_environment_lock_verifier.py`,
`src/pcae/core/hatp_class_b_conformance.py`.

**Inspected but excluded (1):** `src/pcae/core/paths.py` (§10).

**Target count: 25 + 3 = 28.** This independently reproduces K's
28-file conclusion — not assumed in advance; the walk in §6–9 was run
before this count was written down, and no PCAE-owned file beyond these
three was found reachable at all, so there was no larger candidate pool
to prune from.

## 15. Minimality proof

For each of the three newly-included files: removing it from the
closure permits an authority-relevant semantic change (§4's live-fire
precedent — five prior J-series phases patched exactly these files to
fix real verdict-affecting defects) while every currently-HMIC-bound
file's digest stays identical — closure violated if omitted. For the one
excluded dependency (`pcae.core.paths`): changing its 15 lines cannot
alter any topology/environment-lock/aggregate result, because it
performs no comparison, no ACL/identity resolution, and is used only as
a `Path` value carrier — its relevant "semantics" (arbitrary path
values) are not authority semantics at all, not merely represented
elsewhere.

## 16. Completeness proof

Mutation thought experiment applied to every authority-producing symbol
identified in §6–9: topology result (all logic local to
`hatp_class_b_topology_verifier.py`, itself bound), environment-lock
result (local + sibling import, both bound), aggregator result and
failure interpretation (`hatp_class_b_conformance.py`, itself bound, its
own two additional checks included). No unbound PCAE-owned byte was
found capable of changing any of the four inputs to the final verdict —
the walk found exactly zero PCAE-owned files beyond the three roots and
the already-bound/already-excluded set (§6–9). Closure is complete for
the current source tree.

## 17–18. Stdlib and external-tool boundary

Disclosed explicitly in §9 (Categories C/D). Residual trust in the
Python interpreter, stdlib, `git`, `ls`, the kernel ACL subsystem, and
the `pcae` launcher binary is unchanged by this phase and remains
disclosed, not silently assumed away. HMIC-REQ-063 (read directly, §4)
continues to disclose the executed-code/runtime-module-resolution
limitation unweakened.

## 19. Contract/document dependency result

Category E is legitimately empty — independently confirmed in §9 via
AST-level `open`/`read_text` call inspection, not text search alone.
`HBDC-001`'s normative text informed the verifiers' human-authored
implementation but is not a runtime dependency of them, and is already
bound via `implementation_scope_digest` (25th entry) and
`contract_versions` (HMIC-REQ-067) — this phase's analysis does not
duplicate that binding, nor does it find a new one needed.

## 20. HBDC binding preservation

`git diff e917779b 3e1137ef -- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
is empty — byte-identical. `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` remains
present in `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` and
`_CONTRACT_IDENTITY_FILES`, both re-read directly in §5. Finding
B-149O.20D-1 remains closed; the K amendment does not weaken HBDC
binding.

## 21. B-149O.19.3-1 regression

`hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`,
`hatp_hardware_credentials.py` independently re-confirmed present, by
exact string match, in `_FROZEN_SRC_PCAE_RELATIVE_FILES` — unremoved,
unmodified (`git status --porcelain` on `hatp_mandatory_certification.py`
is empty for the whole 149O.20K.1 phase).

## 22. W-1/self-binding analysis — no new cycle

`hatp_environment_lock_verifier.py`'s `_AUTHORITY_MODULE_RELATIVE_PATHS`
is a 19-entry literal tuple of path strings — independently confirmed,
by AST walk, to contain zero `Import`/`ImportFrom` nodes naming
`hatp_mandatory_certification` or `hatp_certification_admin` anywhere in
any of the three verifier modules. The one runtime use of that tuple
(`_check_module_origin_containment`) calls
`importlib.util.find_spec(module_name)` only — resolves a module's
*file location* without executing/importing it — not a Python `import`
statement, confirmed by reading the function body directly. Neither
`hatp_mandatory_certification.py` nor `scripts/hatp_certification_
admin.py` imports any of the three verifier modules (grep confirms
zero occurrences of any of the three module names in either file). W-1
(a distinct file pair — the HMIC validator/admin binding themselves,
unrelated import direction to this phase's three files) is not
reopened; this is a new, independently-checked non-finding, not a
reuse of W-1's old closure.

## 23. Runtime/import cycle analysis

No cycle Class-B-verifier → HMIC-certification → Class-B-verifier or
equivalent exists: the import graph (§6–9) is a strict DAG rooted at the
three verifier modules, terminating in `hatp_bootstrap`/
`repository_identity`/stdlib, with no edge back toward
`hatp_mandatory_certification.py` or `hatp_certification_admin.py`. No
semantic cycle found either (§22).

## 24. v1.2 → v1.3 versioning verification

Read directly: v1.0→v1.1 (§50, widened HMIC-REQ-050/052 by adding limb
(b) and two files) and v1.1→v1.2 (§51, widened `contract_versions` to
five members) were both minor-version scope-widening amendments;
149O.20D.1 (same v1.2, §52) was a same-version *repair* (closing a
disclosed gap in an existing binding, not adding a new limb). K's v1.3
amendment adds a new limb (c) and three files — the same shape as
v1.0→v1.1, not the shape of a same-version repair (it is a scope
addition, not a defect fix in an existing binding, and no existing
field/schema/algorithm is redefined or removed). Independently confirmed
correct per repository convention: minor bump (v1.2→v1.3), not v2.0, not
a same-version repair.

## 25. Attack-matrix evolution verification

New row 38 accurately represents the incomplete-binding threat this
amendment closes (§4's live-fire precedent is the concrete instance).
Attack-matrix header count (37→38) matches the actual row count
(independently counted: 38 `| N |`-prefixed rows). Row 37 (HBDC-001
same-version content drift) is present, unweakened, unedited by this
diff.

## 26–27. New section and contract internal consistency

§53 (subsections 53.1–53.14) specifies exact target files, closure
rationale, non-authoritative/progression status ("not yet operative,
not yet consequential"), external-dependency limitations, HBDC
relationship, and production-alignment requirement — all present.
Searched the full contract text for stale current-target phrasing:
`"these twenty-five files"` (current-target form) does not appear;
`"these twenty-eight files"` does. All other "twenty-five"/"twenty-four"
occurrences are confirmed, by direct inspection of surrounding text, to
be historical references inside §49–52 or §53's own "Context" paragraph
describing the pre-amendment baseline — not current-target claims. No
contradictory normative text found.

## 28. Production/non-production distinction

§53.12/§53.14 explicitly state production remains 25/5, unaligned,
intentionally and disclosed-ly. §5 independently reconfirms this by
direct source read. No collapse of the distinction found.

## 29. Zero-consumer verification (symbol-level, fresh)

Full `src/` text search (module names AND
`verify_class_b_deployment_conformance`/
`verify_class_b_topology_conformance`/`verify_environment_lock_
conformance`), excluding the three files themselves: zero matches.
`hatp_mandatory_cutover.py` and `human_approval_trusted_provenance.py`
independently confirmed to reference only the unrelated string
`"class_b_protected_storage_available"` / `"class_b_bootstrap_
environment_safe"` (CBV-S10's own pre-existing readiness terms) — never
any of the three module names or exported functions.

## 30–31. Stop-condition adjudication

**CBV-S1: OPEN — HMIC v1.3 SOURCE-SCOPE CONTRACT INDEPENDENTLY VERIFIED
— PRODUCTION SOURCE-SET ALIGNMENT + INDEPENDENT PRODUCTION VERIFICATION
PENDING.** Not closed by this phase. The Class-B verifier island is
*not* HMIC-bound in production; positive Class-B conformance is not
authoritative; no certification, activation, or readiness wiring
resulted from this phase.

**CBV-S10: OPEN — READINESS CONTRACT/INTEGRATION GAP.** Untouched by
this phase.

## 32–35. Historical test-failure independent classification

A fixed pre-K baseline was established via `git worktree add --detach
<tmp-path> e917779b` (not `git stash`), with `PYTHONPATH=<worktree>/src`
used to force the worktree's own source over the editable-install
`.pth` pointer at the main repo (verified via `python3 -c "import pcae;
print(pcae.__file__)"` before running tests).

**Fast Green baseline** (`pytest -m fast_green -n auto -q`, worktree):
71 failed, 6771 passed, 5 skipped, 1 error (105.8–140.3s) — reproduced
twice, both runs identical. This independently matches 149O.20K's own
cited baseline exactly.

**Fast Green, current HEAD** (same command, main repo, editable install
confirmed pointing at main repo source): 105 failed, 6768 passed, 5
skipped, 10 errors.

**Exact node-ID diff** (`comm` against sorted, deduplicated `FAILED `/
`ERROR ` lines): baseline has 72 unique nodes; HEAD has 115 unique
nodes; **zero baseline nodes are absent from HEAD** (no previously-
failing node was fixed or became newly passing); **43 new nodes**. All
43 new nodes fall into 8 pre-existing historical test files (149O.19.5B,
149O.19.5E.3, 149O.19.5E.4, 149O.20D, 149O.20D.1, 149O.20E, 149O.20F,
149O.20G — none touched by this phase's own allowed-file scope), and
every one asserts a fixed prior-normative-value: `"25 files"` /
`"28 == 25"` count assertions, `"v1.2 not bumped"` version assertions,
`"37 attack rows"` count assertions, or fixed-commit
`byte_unchanged_since_phase_entry` / `no_contract_file_changed_since_
phase_entry` git-diff self-checks. This is legitimate contract-evolution
supersession, not a genuine regression — independently classified, not
merely counted.

**Broad sweep baseline** (`pytest -k 'hmic or hbdc or class_b or
149o_20' -n auto -q`, worktree): 47 failed, 1522 passed, 5 skipped, 1
error — independently matches 149O.20K's own cited baseline exactly.

**Broad sweep, current HEAD:** 81 failed, 1519 passed, 5 skipped, 10
errors. Node-ID diff: baseline 48 unique nodes, HEAD 91 unique nodes,
zero baseline nodes fixed, 43 new nodes — the identical 43-node set
found in the Fast Green diff (broad sweep is a keyword-narrowed subset).

**Observation on 149O.20K's own fast_green citation.** K's canonical
report describes its post-commit citation as "exactly 115 new failing/
error nodes." Independently re-derived here: the correct interpretation
is that 115 is the **total** post-K-commit failing+error node count
(K's own cited 114 failed + 1 error = 115), not the count of nodes that
are *newly* failing relative to the 72-node pre-K baseline — the
independently-derived new-node count is 43 (115 total = 72 pre-existing
baseline nodes, unchanged, + 43 newly-failing nodes). K's underlying
115-node `--deselect` argv list was still correctly sized (it needed to
cover the full post-commit failing set, baseline-carried-forward plus
new, to reach a 0-failed clean-deselected run), so this is a
**citation-precision observation, not a Blocking finding** — the
operational deselect mechanism was correct; the report prose describing
those 115 nodes as "new" was imprecise. No genuine regression was found
by either K or this independent re-derivation.

This phase's own node counts differ slightly in exact F/E split and
totals from K's own post-commit numbers (K: 114F/1E fast_green,
86F/10E broad sweep; this phase: 105F/10E fast_green, 81F/10E broad
sweep) — both K and this phase disclose pytest-xdist `-n auto`
ordering-dependent flakes as the source of small run-to-run variance;
this is consistent with, not contradictory to, K's own disclosure of
two such flakes. The structural conclusion (zero regressions, all new
failures traced to historical self-checks superseded by legitimate
contract evolution) is independently reproduced.

## 36. No production modification

Confirmed throughout: `git status --porcelain` returns empty for
`hatp_mandatory_certification.py`, all three Class-B verifier modules,
`HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`, and
`HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` for the entire duration of this
phase. No readiness, certification/activation, Permission Broker, or
Runtime Enforcement code was touched.

## 37. Real-host state

`verify_class_b_deployment_conformance()` called directly against the
real host (read-only, `src/` import, no CLI provisioning invoked):
returns `ClassBConformanceStatus.NON_COMPLIANT`, as expected (Protected
Root absent/not provisioned, interpreter/venv not admin-provisioned,
several HBDC-REQ checks unsatisfied on this dev host — the identical
class of finding prior Class-B verification phases already documented).
`git status --porcelain` confirmed empty before and immediately after
the call — no source/repository state change resulted from invoking the
verifier.

## 38. Verification conclusion

All required conditions independently satisfied:

- HMIC v1.2 gap independently established (§2, §4)
- v1.3 amendment exact and internally coherent (§3, §26–27)
- HMIC-REQ-052 new limb justified (§4)
- 28-file target independently derived, not forced to match (§14)
- target proven complete (§16) and minimal (§15)
- no missing PCAE-owned authority-sensitive dependency (§6–9, §12–13)
- version bump correct (§24)
- no cycle/self-binding defect (§22–23)
- HBDC binding preserved (§20)
- provider-source binding preserved (§21)
- production/non-production distinction clear (§28)
- historical test failures correctly classified (§32–35, one citation-
  precision observation noted, non-Blocking)
- zero production consumers remain (§29)

**"HMIC-001 v1.3 Class-B verifier source-scope contract independently
verified."** CBV-S1 is **not** closed by this conclusion (§30).

## 39. Expected clean statuses (confirmed)

- HMIC contract: HMIC-001 v1.3 — CLASS-B VERIFIER SOURCE-SCOPE CONTRACT
  INDEPENDENTLY VERIFIED
- Production HMIC: still 25 source/content files + 5 contract identity
  members, not aligned to v1.3
- CBV-S1: OPEN — CONTRACT INDEPENDENTLY VERIFIED — PRODUCTION ALIGNMENT
  + INDEPENDENT PRODUCTION VERIFICATION PENDING
- CBV-S10: OPEN
- Class-B: CONTRACT VERIFIED — VERIFIER REPAIR LINE INDEPENDENTLY
  VERIFIED — HMIC SOURCE-SCOPE CONTRACT INDEPENDENTLY VERIFIED —
  PRODUCTION HMIC ALIGNMENT PENDING — NOT PROVISIONED
- HATP: NOT READY
- Runtime: Observed / observe / unavailable

## 40. Recommended next phase

**149O.20K.2 — HMIC Class-B Verifier Production Source-Set Alignment**
(not begun by this phase). That future phase should: update live
production HMIC source set (`_FROZEN_AUTHORITY_BEARING_FILES`) to the
independently-verified 28-file target; update live HMIC contract-version
identity if the implementation requires it; prove every newly-bound
file is digest-sensitive; preserve the existing 25 members; preserve
HBDC binding; preserve zero Class-B consumers; keep CBV-S10 open. An
independent production-alignment verification phase must follow before
CBV-S1 can close.
