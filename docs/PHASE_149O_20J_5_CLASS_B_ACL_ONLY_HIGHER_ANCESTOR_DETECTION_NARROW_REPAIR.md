# Phase 149O.20J.5 — Class-B macOS ACL-Only Higher-Ancestor Detection Narrow Repair

## 1. Scope and Non-Goals

Repairs exactly one Blocking defect: **B-149O.20J.4-1** — macOS ACL-only
higher-ancestor detection gap in `_acl_grants_agent_write_macos`
(`src/pcae/core/hatp_class_b_topology_verifier.py`), independently
discovered and left unrepaired by 149O.20J.4.

Not performed in this phase (per governing prompt): HMIC source-scope
evolution, readiness integration, Class-B host provisioning,
certification, or activation. Runtime remains **Observed / observe /
unavailable** throughout.

## 2. Governing Status Entering This Phase

- **B-149O.20J.2-1** (early-stop bypass): INDEPENDENTLY CONFIRMED CLOSED
  AT NON-AUTHORITATIVE VERIFIER IMPLEMENTATION BOUNDARY — not reopened;
  no new direct evidence surfaced against it in this phase.
- **B-149O.20J.4-1**: OPEN — BLOCKING for HMIC-binding progression — the
  repair target of this phase.
- **J-1** (`.pth` tab-form): INDEPENDENTLY CLOSED — re-confirmed
  byte-unchanged and behaviorally intact (§9).
- **J-2** (effective-GID omission): INDEPENDENTLY CLOSED — re-confirmed
  (§9).
- **J-3** (Trusted-Git ACL blindness): adjudicated below (§8).

## 3. Initial Inspection

`cd ~/repos/pcae-harness`; `git status --short` clean; `git status
--branch --short` `main...origin/main` (no divergence);
`git rev-list --count origin/main..HEAD` = 0 before this phase's
commits; `pcae health` healthy; `pcae check` passed; `pcae status
coherence` coherent; `pcae doctor task-memory` warnings (pre-existing,
unrelated: historical `tasks/done/` entries missing from
`tasks/DONE.md`, predating this phase, outside this phase's allowed-file
scope); `pcae push check` clean, nothing to push; `pcae runtime inspect`
Observed / observe / unavailable; `pcae notify status` Telegram
configured/enabled/ready; `pcae phase-report show --latest` returned the
149O.20J.4 canonical report (recommending exactly this phase);
`pcae phase-report reconcile --phase-id 149O.20J.4` returned `status:
reconciled`, `mutation: none (inspection only)` — read-only, no J.4
redispatch.

`git show --stat afa17ea7` confirmed the exact J.4 commit and its
disclosure of B-149O.20J.4-1. `git diff HEAD:...
hatp_class_b_topology_verifier.py` against the working-tree copy at
phase entry was byte-identical, confirming HEAD (`0b2fd134`) carried the
still-defective pre-repair source.

## 4. Primary Source Reconstruction

Independently re-read (not assumed from J.4's own prose):

- **HBDC-REQ-016**: no ACL entry (POSIX, extended, default, inherited)
  SHALL grant the agent write access, even where mode bits deny it.
- **HBDC-REQ-017**: every ancestor directory up to the point of no write
  access at all SHALL be non-agent-writable; parent-path replacement is
  explicitly named as a distinct channel from Protected Root's own
  bytes.
- **HBDC-REQ-020**: directory-entry deletion/rename authority is
  compliance-equivalent to direct write, satisfied jointly by
  HBDC-REQ-017.
- **CBD-3**: "no override path exists, and symlink/ACL/group/parent-path
  channels are closed."
- **CBD-7**: fail-closed on incomplete evidence — `INDETERMINATE` is
  never treated as ready.
- 149O.20J's own Finding 3 (`B-CBV-J-3`): `_resolve_trusted_executable`
  "checks only mode+group bits, never ACL, deliberately... an ACL-only
  agent write grant to the git executable, **its ancestors**, or a
  PATH-preceding directory would not be detected" — the original defect
  text explicitly named ancestor coverage, not file-level coverage only
  (load-bearing for §8's adjudication).
- 149O.20J.1's J-3 repair (`_resolve_trusted_executable_with_effective_
  access`): composes the unchanged PATH-precedence primitive with
  `_effective_write_access` + `_ancestor_chain_safe`, explicitly claiming
  ("Git-executable and ancestor ACL coverage") that both the executable
  itself and its full ancestor chain gained ACL awareness through this
  composition.
- 149O.20J.2's independent verification of J-3: confirmed the delegation
  wiring using **simulated/forced** ACL results (`with the ACL sub-check
  forced to report "no ACL"`, `simulated an ACL-only write grant`) —
  never a real `chmod +a` grant — and closed J-3 "for the specific
  disclosed defect (ACL blindness)."
- 149O.20J.3's repair of B-149O.20J.2-1: widened `_ancestor_chain_safe`
  to walk to the true filesystem root; left `_acl_grants_agent_write_
  macos` itself untouched.
- 149O.20J.4's independent verification: reproduced the historical
  early-stop defect from fixed source, confirmed J.3's repair, and
  discovered B-149O.20J.4-1 via a `strict=True`-xfail-marked real-ACL
  test — disclosed, not repaired.
- Current `hatp_class_b_topology_verifier.py` (this phase's starting
  point, commit `0b2fd134`): confirmed via direct read that
  `_acl_grants_agent_write_macos` gated ACL-presence on a `+` marker in
  `ls -lde`'s mode column, then searched for the literal substring
  `"write"` across entry lines.

## 5. Historical Defect Reproduction (Real macOS ACLs, Fixed Source)

Reproduced against `git show 0b2fd134:...` (the exact pre-repair blob),
not retyped, on this real macOS 26.6.1 (Darwin 25.6.0, arm64) host.

**Direct primitive, clean PATH** (`/bin:/usr/bin`, avoiding this dev
host's Homebrew-PATH indeterminate-resolution confound):

```
mkdir grandparent; chmod 555 grandparent
chmod +a "$(whoami) allow add_file,delete_child" grandparent
# ground truth: touch grandparent/x succeeds, confirming real write authority
pre-repair _acl_grants_agent_write_macos(grandparent) => False
```

The pre-repair primitive returns a confident **False** (not even
`None`/indeterminate) for a directory ground-truth-verified writable —
the worst-case failure mode: silent misclassification as safe.

**Full ancestor-chain walk**, fixture isolated at `grandparent` (host
region above it stubbed safe via monkeypatched `_effective_write_access`
+ `_is_symlink_unsafe`, exactly the disclosed technique used by
149O.20J.3/.4's own suites; built under `/private/tmp` specifically to
avoid `/tmp`'s own symlink-to-`/private/tmp` confound):

```
subject = grandparent/parent/subject_dir  (parent, subject POSIX-safe, mode 555)
grandparent: mode 555, ACL add_file,delete_child (real chmod +a)
pre-repair _ancestor_chain_safe(subject) => (True, (..., "ancestor_walk_reached_filesystem_root"))
```

**B-149O.20J.4-1 confirmed exactly as reported**: the walk returns
`safe=True`, reaching the filesystem root, despite a real,
ground-truth-verified ACL-writable grandparent.

## 6. macOS ACL Canonicalization — Empirically Derived (Real Host)

Not assumed from `man chmod`'s prose alone; every claim below is a
directly observed `ls -le`/`ls -lde` result on this host after a real
`chmod +a` grant, cross-checked against `man chmod`'s RIGHTS section.

### 6.1 The `+`-marker gate is independently broken on a real host

`ls`'s single trailing mode-column indicator is `@` (extended
attributes) or `+` (ACL) — never both. Modern macOS attaches a
`com.apple.provenance` extended attribute to effectively every
filesystem object (confirmed via `xattr -l`, and confirmed
non-removable — `xattr -c` returns `Permission denied` — it is a
system-managed attribute). A directory with **both** a real ACL and this
now-ubiquitous xattr renders `@`, not `+`. The pre-repair `+`-gate
therefore discarded real ACL evidence *before* the substring search ever
ran — an independent, compounding failure mode beyond the "write"
substring bug alone. The repair parses the numbered ACL entry lines
directly and never gates on the leading marker character.

### 6.2 Canonical entry-line grammar

```
 N: <principal> allow|deny <right1,right2,...>
```

`<principal>` observed as `user:<name>` or `group:<name>` (the bare-name
form shown as an older example in `man chmod` was deliberately not
assumed — it does not match this host's real output). Multiple ACEs for
the *same* principal+action are merged by `ls` into one comma-joined
line; different principals get separate numbered lines.

### 6.3 Right-token aliasing (file vs. directory context)

Empirically confirmed by granting the *same* right on a file and on a
directory and comparing `ls` output:

| Right granted via `chmod +a` | Rendered on a file | Rendered on a directory |
|---|---|---|
| `write` / `add_file` | `write` | `add_file` |
| `append` / `add_subdirectory` | `append` | `add_subdirectory` |
| `delete` | `delete` | `delete` |
| `writeattr` | `writeattr` | `writeattr` |
| `writeextattr` | `writeextattr` | `writeextattr` |

`write`(file)/`add_file`(directory) are the identical underlying NFSv4
ACE bit, rendered contextually by `ls` — likewise `append`/
`add_subdirectory`. `delete_child` has no file-context equivalent (files
have no children). This means a single unified rights vocabulary works
for both files and directories without branching on `path.is_dir()`: by
the time `ls` has rendered the entry, it has already performed the
type-appropriate translation.

### 6.4 Confirmed irrelevant (non-write) rights

`read`, `execute`, `readattr`, `readextattr`, `readsecurity`, `list`,
`search`, `chown`, `writesecurity` (ownership/ACL-security metadata, not
content/entry-structure authority — excluded per "avoid broadening
beyond HBDC without justification") — empirically confirmed to not
confer any effective write authority when granted alone.

## 7. Repair

`src/pcae/core/hatp_class_b_topology_verifier.py` — the only production
file touched, as expected.

- Added `_MACOS_ACL_ENTRY_RE`, `_MACOS_ACL_WRITE_CAPABLE_RIGHTS` (`write`,
  `append`, `writeattr`, `writeextattr`, `add_file`, `add_subdirectory`,
  `delete_child`, `delete`), `_MACOS_ACL_KNOWN_SAFE_RIGHTS`, and
  `_MACOS_ACL_KNOWN_RIGHTS` (their union — the full macOS ACL right
  vocabulary per `man chmod`, empirically cross-checked).
- Added `_macos_acl_principal_matches_agent`: resolves `user:<name>` via
  `pwd.getpwnam`, `group:<name>` via `grp.getgrnam` (imported locally
  inside the macOS-only function, preserving cross-platform top-level
  import safety); an unresolvable or unrecognized-shape principal
  returns `None` (indeterminate), never a silent non-match.
- Rewrote `_acl_grants_agent_write_macos(path, agent_uid, agent_gids)`
  (signature widened to accept agent identity, matching the Linux
  sibling): parses each numbered entry line directly (no marker gate);
  a line that doesn't match the entry grammar is malformed → `None`; any
  right token outside `_MACOS_ACL_KNOWN_RIGHTS` → unrecognized →  `None`
  (never silently treated as non-write); `deny` entries are parsed for
  malformed/unrecognized-token detection but never contribute a grant;
  an `allow` entry with a write-capable right resolves principal match —
  `True` short-circuits, unresolvable principal accumulates
  `saw_indeterminate` (only overrides the final `False` if no `True` was
  found).
- Updated `_acl_grants_agent_write`'s `darwin` branch to pass
  `agent_uid`/`agent_gids` through.

No other function's signature or behavior changed. `_ancestor_chain_safe`,
`_effective_write_access`, `_resolve_trusted_executable`,
`_resolve_trusted_executable_with_effective_access`, and the Linux ACL
path are byte-unchanged.

**Deny-precedence disclosure**: this repair does not implement full
NFSv4 first-entry-wins evaluation order. Any `allow` entry granting a
write-capable right to a matching principal is treated as writable
regardless of a later `deny` entry that might, under strict NFSv4
semantics, override it. This is a disclosed, deliberately conservative
(fail-closed, never fail-open) simplification — it can only cause an
over-cautious `True`/indeterminate classification, never mask a real
grant.

## 8. J-3 Scope Adjudication

**Original J-3 scope** (`B-CBV-J-3`, 149O.20J's own table): *"...
`_resolve_trusted_executable` ... checks only mode+group bits, never
ACL, deliberately ... an ACL-only agent write grant to the git
executable, **its ancestors**, or a PATH-preceding directory would not
be detected."* — the defect as originally named explicitly included
ancestor-level ACL blindness, not file-level blindness alone.

**149O.20J.1's repair and its own closure claim**: composed
`_resolve_trusted_executable_with_effective_access` from the unchanged
PATH walk plus `_effective_write_access`/`_ancestor_chain_safe`, and
explicitly stated: *"both the 'Git executable ACL' and 'Git ancestor
ACL' requirements from the governing prompt are covered by this single
composition."* This is an explicit, textual claim of ancestor-ACL
coverage, not merely file-level coverage.

**149O.20J.2's independent verification of that claim**: exercised it
only with **simulated/forced** ACL results — "with the ACL sub-check
forced to report 'no ACL'", "simulated an ACL-only write grant" — never
a real `chmod +a` grant. Its own results table lists "Git immediate-
parent ACL-only write grant: REJECTED" as part of the J-3 verdict, based
on that same simulated evidence.

**149O.20J.4's and this phase's real-host evidence**: a real macOS
`chmod +a add_file,delete_child` grant on a directory ancestor is *not*
detected by the underlying `_acl_grants_agent_write_macos` primitive
that J-3's delegation relies on for its ancestor-ACL coverage claim.

**Derivation.** J-3's *closure text*, as written, asserted ancestor-ACL
coverage as part of what was closed — not merely "ACL is now consulted
at all for the executable's own bytes." That specific sub-claim was
validated only against simulated/forced results, never real macOS ACL
evidence, and the real evidence now shows it did not hold for real
canonical directory-replacement rights. This is **not** a case of two
architecturally independent defects coexisting by coincidence
(Outcome A) — J-3's own repair and closure language directly asserted
the exact ancestor-ACL property that B-149O.20J.4-1 shows to be false on
a real host. The historical closure was broader than the evidence
justified.

**Verdict: Outcome B.** J-3's closure language is narrowed, without
rewriting the historical artifacts:

- **J-3 (delegation wiring)** — *"`_resolve_trusted_executable`'s
  ACL-blind delegation is repaired; ACL evidence (mode/group/ACL-branch)
  is now consulted for the resolved executable's own bytes and its full
  ancestor chain, via the shared `_effective_write_access`/
  `_ancestor_chain_safe` primitives"* — **remains INDEPENDENTLY CLOSED**.
  §9.3 below reconfirms this wiring end-to-end with a real file-level ACL
  grant on the executable itself.
- **J-3's specific "Git ancestor ACL... covered" sub-claim**, as stated
  in 149O.20J.1 §5 and verified only by simulation in 149O.20J.2, is
  **NARROWED**: it was true only in the sense that the ancestor walk now
  *calls into* ACL-aware code — it was not, and could not have been,
  evidence that the ACL-aware code correctly recognized real macOS
  canonical directory rights. That specific evidentiary gap is
  B-149O.20J.4-1, now repaired by this phase (§7) and independently
  re-verified with real ACLs through the exact Trusted-Git delegation
  path (§9.4).
- No historical test file's assertions are deleted or retyped to match
  this narrowing; 149O.20J.1/.2's own documents remain the historical
  record, and this phase's own doc records the adjudication rather than
  editing theirs.

## 9. Regression Results

### 9.1 New 149O.20J.5 suite

`tests/test_phase_149o_20j_5_class_b_acl_only_higher_ancestor_detection_
macos_narrow_repair.py`: **39/39 passed** (macOS-only via module-level
`skipif`), run twice for determinism, identical result both times.
Covers: historical pre-repair reproduction from fixed `0b2fd134` source;
directory rights `add_file`/`add_subdirectory`/`delete_child`/`delete`
each individually ground-truth-verified via a right-specific probe
(create-file, create-subdirectory, delete-preexisting-child,
rename-self respectively — not a one-size-fits-all "touch" probe, since
each right authorizes a narrower action than the others); combined
canonicalized multi-right grants; POSIX-safe control; file-level
`write`/`append`/`writeextattr`; irrelevant rights; unrelated-user
principal; effective-group (`everyone`, gid 12) principal; deny-not-
allow; malformed output; unexpected right token; ACL-tool unavailable;
subprocess error; unresolvable write-capable principal; full
ancestor-chain composition at one and two levels above a safe parent;
fully-safe-chain control; Trusted-Git composition; Protected-Root
composition; Git/Protected-Root equivalence on the same attack;
early-stop-repair regression (both directions); J-1/J-2/J-3 regressions;
symlinked-ancestor regression; indeterminate-above-safe-ancestor
fail-closed; read-only wall; zero-consumers; HMIC frozen-set unchanged;
production-scope-limited; real-host NON_COMPLIANT.

### 9.2 149O.20J.4 suite (xfail disposition)

The two `strict=True` xfail-marked tests whose own reason text
explicitly authorized removal "once a follow-up phase repairs the ACL
right-name matching and this test genuinely passes"
(`test_acl_only_higher_ancestor_write_macos`,
`test_acl_grants_agent_write_macos_direct_ground_truth`) now pass
genuinely; their xfail markers were removed and their `pytest.fail`-on-
detected-True assertions were converted to direct `assert result is
False` / `assert detected is True` positive checks — a disclosed,
explicitly-pre-authorized contract evolution, not a silent rewrite. No
other assertion in that file was changed.

### 9.3 J-1/J-2/J-3 core regressions

- **J-1**: `hatp_environment_lock_verifier.py` byte-unchanged since
  before this phase (`git diff --stat 0b2fd134 HEAD` empty).
- **J-2**: `os.getegid()` still independently folded into
  `_current_agent_identity()`'s group set.
- **J-3 (delegation wiring)**: `_resolve_trusted_executable_with_
  effective_access` still calls `_effective_write_access(resolved...)`;
  a fresh real file-level ACL `write` grant directly on a would-be
  trusted executable is still detected and rejected end-to-end through
  the unmodified delegation path (§9.1's new suite).

### 9.4 Complete-chain composition

- Ancestor walk: ACL-only grandparent rejects; ACL-only great-
  grandparent (two levels above a POSIX-safe parent) rejects; fully-safe
  chain still reaches the filesystem root.
- Trusted Git: a real ACL-only grandparent-of-the-resolved-executable
  grant is rejected through the unmodified call graph (no truncation).
- Protected Root: the identical attack against `_check_ancestor_chain`
  rejects.
- Git and Protected Root produce identical (not merely similar)
  rejection on the same real-ACL fixture — no divergence between the two
  call sites.
- Early-stop repair (149O.20J.3): mode-bit-writable grandparent behind a
  safe parent still rejects; fully-safe chain still reaches root —
  unaffected by this phase.
- Symlinked higher ancestor: still unconditionally rejected.
- Indeterminate ACL result above a locally-safe ancestor: still forces
  the overall result to `None`, never `True`.

### 9.5 Broad sweep (`pytest -k 'class_b or hbdc or 149o_20j' -n auto`)

Clean baseline (this phase's changes stashed, matching 149O.20J.4's own
citation exactly): **11 failed / 617 passed / 5 skipped / 2 xfailed / 1
pre-existing collection error** (`fido2` module absent).

With this phase's changes, before commit (dirty working tree): **17
failed / 652 passed / 5 skipped / 1 error**. Every one of the 6
additional failures beyond baseline is a "working tree must be clean" /
"no `src/pcae` files dirty" historical self-check
(`149o_20c`/`149o_20d`/`149o_20d_1`/`149o_20e`/`149o_20h`/`149o_20j`
variants) — mechanically expected while this phase's real, intentional
changes are uncommitted, and re-verified clean again immediately after
this phase's commit (§11). The remaining 5 baseline failures (the two
`149o_20j_2` first-safe-boundary/deep-ancestor documentation tests, the
`149o_20j`-suite's two frozen historical-snapshot assertions, and
`149o_20g`'s unrelated diff-scope self-check) are byte-identical to
baseline — zero new failures attributable to this phase's production or
test changes.

### 9.6 Fast Green

`pytest -m "not slow" -n auto`, `--ignore=tests/test_phase_149o_7_hatp_
class_b_activation_independent_verification.py` (pre-existing collection
error, `fido2` module absent — matches every prior phase's citation):
xdist worker collection mismatch is **pre-existing** — independently
reconfirmed on the stashed clean baseline (identical `Different tests
were collected between gwN and gw0` failure at `-n2`, before any of this
phase's changes). Authoritative single-process citation:
`pytest -m "not slow" -q --ignore=.../test_phase_149o_7_...py`.

## 10. HMIC / Zero-Consumer / Read-Only / Real-Host Confirmations

- `_FROZEN_AUTHORITY_BEARING_FILES` still exactly 25 entries; none of
  the three Class-B modules present (confirmed by the new suite,
  imported directly from `hatp_mandatory_certification`).
- `git grep` for each of the three Class-B module names under `src/`
  returns only the modules themselves — zero production consumers.
- Source inspection: no `chmod`/`chown`/`mkdir`/`makedirs`/`rmtree`/
  `remove`/`unlink`/file-write call anywhere in the module.
- `verify_class_b_deployment_conformance()` still returns non-`COMPLIANT`
  on this deliberately unprovisioned host, confirmed both before and
  after this phase's changes.
- Production diff scope: `git diff --name-only 0b2fd134 -- src/` =
  exactly `src/pcae/core/hatp_class_b_topology_verifier.py`.

## 11. Status

- **B-149O.20J.4-1**: **REPAIRED — INDEPENDENT VERIFICATION PENDING —
  NOT CLOSED.**
- **J-3**: core delegation-wiring defect remains **INDEPENDENTLY
  CLOSED**; the historical closure's ancestor-ACL-coverage sub-claim is
  **NARROWED** per §8 (Outcome B), now made evidentially whole by this
  phase's repair pending 149O.20J.6's independent re-verification.
- **CBV-S1**: OPEN — HMIC SOURCE-SCOPE BINDING STILL PENDING. Nothing in
  this phase HMIC-binds anything.
- **CBV-S10**: OPEN — READINESS CONTRACT/INTEGRATION GAP REMAINS. No
  readiness work performed.
- **Class-B**: CONTRACT VERIFIED — ACL REPAIR IMPLEMENTED
  NON-AUTHORITATIVELY — INDEPENDENT VERIFICATION PENDING — NOT
  PROVISIONED.
- **HATP**: NOT READY.
- **Runtime**: Observed / observe / unavailable (unchanged).
- **Real host**: deliberately unprovisioned; `verify_class_b_deployment_
  conformance()` returns `NON_COMPLIANT`.

## 12. No-Go Confirmations

No HMIC source-scope evolution occurred. No readiness integration
occurred. No Class-B host was provisioned. No certification or
activation code path was touched. No Permission Broker, POL-005, or
COMP-002 change was made. No governance bypass, `--no-verify` flag, or
force push was used. No production file outside
`hatp_class_b_topology_verifier.py` was modified. No `_FROZEN_AUTHORITY_
BEARING_FILES` or contract-version change was made. No ACL, mode,
ownership, or ancestor state was mutated by production code — only
isolated temporary test fixtures were created and cleaned up. No
real-host provisioning occurred. No J-1/J-2/J-3 core regression was
introduced. No historical test assertion was silently rewritten — the
two xfail removals in the J.4 suite were explicitly pre-authorized by
their own original reason text, and are disclosed as such here and in
the test file itself. B-149O.20J.4-1 was not independently closed in
this same phase — only repaired, pending 149O.20J.6.

## 13. Recommended Next Phase

**149O.20J.6 — Class-B macOS ACL-Only Higher-Ancestor Detection Repair
Independent Verification.** Must independently re-derive HBDC-REQ-016/
017/020 and the macOS ACL canonicalization grammar from primary
evidence (not from this phase's own derivation alone), independently
reproduce this phase's real-ACL test results, and only then may
B-149O.20J.4-1 be considered for closure. 149O.20K (HMIC Class-B
Verifier Source-Scope Contract Evolution) must not begin until 149O.20J.6
passes, and must still perform its own fresh HMIC-REQ-052 transitive
authority-dependency closure analysis.
