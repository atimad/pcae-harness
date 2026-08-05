# Phase 149O.1B: Human Approval Trusted Provenance Contract Freeze

**Phase type:** normative-contract freeze attempt, Root 2B (bootstrap/
authorization trust) resolution.

**Status:** completed. **Verdict: HATP-001 NOT FROZEN — BOOTSTRAP /
AUTHORIZATION TRUST GAP CONFIRMED, NOW WITH CONCRETE PRIMARY-SOURCE
EVIDENCE, NOT MERELY ARCHITECTURAL SUSPICION.**

## 1. Starting Position (independently reconfirmed)

- Repository clean; `origin/main..HEAD` = 0 at phase start.
- Latest completed phase: 149O.1A — **HUMAN APPROVAL TRUST BOUNDARY
  ARCHITECTURE DEFINED — CONTRACT FREEZE REQUIRES FOLLOW-UP.** Root 1
  (proof-production) resolved: **HATP MODEL A**, hardware-backed
  external signing key. Root 2 decomposed into 2A (device genuineness,
  conceptually resolved) and 2B (approver-authorization mapping,
  unresolved). B-149O-1..4 remain OPEN.
- `pcae health`/`check`/`status coherence`/`doctor task-memory`/`push
  check`/`runtime inspect`/`notify status`: all healthy/coherent/clean;
  runtime Observed / observe / unavailable; Telegram configured and
  ready.
- `pcae phase-report reconcile --phase-id 149O.1A`: `receipt: absent`,
  `status: delivery_recorded_bookkeeping_incomplete` — inspection only,
  no mutation performed; noted, not a blocker for this phase's own
  contract work.
- `git diff --name-only <149O.1A start>..HEAD -- src/pcae/` is empty
  (confirmed via `git status --short` clean and no commits since
  `eee67fd4` touching `src/pcae/**`): no production code changed since
  149O.1A, so this phase does not re-run the B-149O exploit suite, for
  the same reason 149O.1A itself gave for skipping it relative to 149O.1.

## 2. Scope Discipline (governing-prompt requirement)

Per the governing prompt, this phase does **not** reopen the Model A/B/
C/D/E signer-model comparison (149O.1A §7) — no primary-source
contradiction in Model A emerged. This phase's entire job is Root 2B:

> What independently protected fact tells PCAE that a particular
> hardware-backed signing key corresponds to a particular principal who
> is authorized to approve rollback for a particular repository?

## 3. Method: Investigate, Don't Assume

149O.1A left Root 2B open specifically because it could not verify
whether any of its three candidate bootstrap-boundary mechanisms was
**actually enforced** in this repository's real deployment (149O.1A
§19: mechanism 3, external human-gated review, was explicitly flagged
as "not verified as configured for this repository during that phase,"
since it required inspecting remote hosting-platform configuration,
outside that phase's read-only scope of the local checkout).

This phase's governing prompt explicitly assigns exactly this
investigation to 149O.1B (item 22: "Choose one. Do not leave them
co-equal"; item 21: "MUST choose exactly one concrete bootstrap
model"). Inspecting this repository's actual GitHub configuration is
therefore in scope this phase, as a read-only fact-finding step — no
repository configuration was modified.

## 4. Root 2B Investigation — Primary-Source Evidence (this phase)

All three of 149O.1A §19's candidate mechanisms were checked directly
against this repository's real, current deployment:

### 4.1 Mechanism 1 — Distinct OS user/principal

```
$ whoami
atilamadai
$ git config user.email
madaister@gmail.com
```

The autonomous agent process and the human operator's own shell both
run as OS user `atilamadai`. No distinct OS principal, no filesystem
ACL boundary. **Not established** — reconfirms 149O.1A §4/§9 exactly;
no discrepancy found.

### 4.2 Mechanism 2 — External service/KMS enrollment

Repo-wide grep for `hmac|signing_key|private_key|sign(|signature|
hardware|yubikey|secret_key|getpass|keychain|fido|pkcs11|piv` across
`src/pcae` re-run this phase (112 matches, same order of magnitude as
149O.1A's finding); spot-checked matches remain docstring disclaimers
and third-party-secret redaction logic, never a credential PCAE itself
uses to authenticate anything. `pyproject.toml` unchanged — still no
cryptography dependency. **Not established** — no external service or
KMS exists anywhere in this repository's dependency graph or code.

### 4.3 Mechanism 3 — External human-authenticated review gate

This is the one 149O.1A left genuinely open pending inspection. This
phase ran that inspection directly against the actual hosting repository:

```
$ git remote -v
origin  git@github.com:atimad/pcae-harness.git

$ gh api repos/atimad/pcae-harness/branches/main/protection
required_pull_request_reviews.required_approving_review_count: 1
enforce_admins.enabled: false
allow_force_pushes.enabled: false

$ gh api repos/atimad/pcae-harness/collaborators --jq '.[].login'
atimad

$ gh api repos/atimad/pcae-harness --jq '.owner.login, .private'
atimad
false

$ ssh-add -l
SHA256:XS2IgBYGA7/oQQC2sA4sxfA65/lJ+9Y9Kkuap6CuSFY madaister@gmail.com (ED25519)
```

Findings, all independently verified this phase, not inferred:

1. **Branch protection exists** on `main` and nominally requires one
   approving PR review before merge. This is a real fact this phase
   confirms that 149O.1A could not.
2. **`enforce_admins` is `false`.** The repository owner/admin account
   (`atimad`) is exempt from the review requirement and can push
   directly to `main` — which is exactly the pattern this repository's
   own commit history shows (every Phase 149-series commit up to and
   including 149O.1A's landed as a direct push to `main`, never a PR
   merge commit).
3. **`atimad` is the sole collaborator.** There is no second human
   account on this repository. A "non-author human reviewer" requirement
   is structurally unsatisfiable with one human and one repository —
   there is no second person to be the reviewer.
4. **The SSH key used for `git push` (`madaister@gmail.com`,
   `MacBook Pro M5 pro`) is the same key present on this machine that
   the autonomous agent process also has access to** (same OS user,
   same `ssh-agent`, same `~/.ssh` material, same `gh auth` token — no
   separate credential store gates agent-initiated pushes from
   human-initiated pushes).

**Conclusion: mechanism 3 is not merely "unconfigured" (149O.1A's
honest uncertainty) — it is now confirmed, with primary-source
evidence, to be *structurally insufficient* for this deployment even
though the GitHub feature itself is nominally enabled.** Its two
load-bearing assumptions — a non-admin-bypassable rule, and a distinct
human reviewer with distinct credentials — both fail concretely: the
rule is admin-bypassable, and the account that would have to hold
"reviewer" authority is the identical account, using the identical
local credential material, that this agent process runs under. Under
Threat A, an autonomous process with local shell access on this
machine has exactly the same path to `git push origin main` that the
human operator has; GitHub's branch-protection UI does not observe a
difference between them.

## 5. Root 2B Verdict

**None of the three candidate bootstrap-boundary mechanisms is
currently, mechanically established in this repository's real
deployment.** This is stronger and more concrete than 149O.1A's
finding (which flagged mechanism 3 as merely unverified); this phase
verified it and found it insufficient as configured, not just unread.

## 6. Bootstrap Model Selection (governing-prompt items 21-23, mandatory)

Per item 21, this phase selects exactly one concrete bootstrap model
**class** as the target architecture for HATP-001's Root 2B, rather
than leaving the three candidates co-equal:

**Selected: Class B — Separate privileged local administrator / OS
security context**, over Class A (hardware-mediated administrative
enrollment alone) and Class C (externally administered trusted
approver registry), for the following reasons, each grounded in this
phase's own findings:

- **Class C (external registry / hosted review gate) is rejected as
  the primary mechanism for this deployment.** §4.3 demonstrates it is
  circular here: the "external" system's own authorization decision
  (who may push to `main` unreviewed) reduces to the same local
  credential material the agent already has. A hosted KMS/registry
  service (as opposed to a review gate) remains theoretically viable
  but requires provisioning infrastructure this repository has none of
  today (149O.1A §4, reconfirmed §4.2) — a materially larger
  operational commitment for no demonstrated compensating strength
  over Class B in a single-machine, single-maintainer deployment.
- **Class A (hardware-mediated administrative enrollment) alone does
  not solve Root 2B.** A hardware device can prove *a* human touched
  *a* key at enrollment time (this is Root 1's job, already solved by
  Model A), but the enrollment *record* — "this key belongs to this
  principal, who may approve rollbacks for this repository" — still
  has to be written somewhere with a protected boundary. Hardware
  presence at enrollment time does not, by itself, answer where that
  record lives or who can overwrite it afterward; it still needs
  Class B or Class C underneath it. Class A is therefore adopted as
  *part of the enrollment ceremony* (§8), not as a standalone answer to
  Root 2B.
- **Class B is selected** because it is the only candidate that (a)
  requires no new external infrastructure or second human account that
  does not already exist for this repository, (b) is a well-understood,
  auditable mechanism (a distinct OS principal owning the registry file,
  ACL-restricted from the agent's own OS principal), and (c) directly
  answers the mechanical question item 93 requires ("why can the agent
  not enroll itself") with a concrete, checkable fact (file ownership
  and permission bits under a different UID) rather than a policy the
  agent's own credentials can already satisfy.

This selection is a **choice of target architecture**, not a claim that
the boundary exists today. §7 states plainly that it does not.

## 7. Why HATP-001 Still Cannot Freeze This Phase

Section 93 of the governing prompt requires the frozen contract to
state, concretely:

```
BOOTSTRAP AUTHORITY: <selected mechanism>
WHY THE AUTONOMOUS AGENT CANNOT ENROLL ITSELF: <mechanical reason>
WHY THE AUTONOMOUS AGENT CANNOT REPLACE THE TRUSTED VERIFIER KEY: <mechanical reason>
INITIAL ENROLLMENT PROCEDURE: <conceptual flow>
```

with the explicit instruction: "If any field cannot be filled
concretely: DO NOT FREEZE."

This phase selected Class B (§6) as the target mechanism, but §4.1
confirms that **no distinct OS principal exists in this repository's
actual deployment today** — the agent process and the human operator
run as the same OS user. The "mechanical reason" field cannot honestly
be filled in for *this repository as it is actually deployed right
now*: there is no file-ownership or ACL fact currently true that would
stop this agent process, running as `atilamadai`, from reading or
writing a Class-B-protected registry file, because no such
differently-owned file exists.

Filling that field with a description of a boundary that does not yet
exist would be exactly the failure mode item 110 lists as blocking
("bootstrap admin unspecified... no mechanical self-enrollment
prevention... any one means: CONTRACT NOT FROZEN") and the failure mode
149O.1A itself declined to commit (§9: "under Threat A, any registry
stored under ordinary agent-writable state is therefore exactly as
forgeable as every artifact 149O already broke").

**Per the governing prompt's own Recommended Next Phase Logic:** "If
device genuineness is resolved but approver authorization remains
agent-writable → Do NOT freeze. Recommend a dedicated bootstrap-
authority architecture phase." Device genuineness (Root 2A) remains
resolved (149O.1A §8(a), unchanged). Approver authorization (Root 2B)
remains, concretely and now more precisely than before, agent-writable
in this deployment. **This phase does not freeze `HATP-001` and does
not create `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`**,
per item 119's own conditional ("If freeze succeeds, create...").

## 8. Bootstrap Trust Statement (honest completion of the mandatory template)

```
BOOTSTRAP AUTHORITY:
Selected target class: a distinct OS security context (a dedicated
local system principal, distinct from whatever OS user executes the
autonomous agent process) owning the trusted approver registry file
with restrictive filesystem ACLs (read-only to the agent's OS
principal, read/write only to the dedicated principal).

WHY THE AUTONOMOUS AGENT CANNOT ENROLL ITSELF:
NOT YET TRUE IN THIS DEPLOYMENT. The target mechanical reason ("the
registry file is owned by a different OS principal than the one the
agent process runs as, and the agent's OS principal has no write
permission on it") is not currently a fact about this repository's
actual deployment: this phase confirmed (§4.1) that the agent and the
human operator both run as OS user `atilamadai`. This field cannot be
filled honestly today.

WHY THE AUTONOMOUS AGENT CANNOT REPLACE THE TRUSTED VERIFIER KEY:
Same gap, same reason: no distinct OS principal currently exists to
own the verifier configuration.

INITIAL ENROLLMENT PROCEDURE:
Not frozen. Establishing the target boundary (creating the dedicated OS
principal, setting ownership/ACLs, defining exactly how the human
operator authenticates as that principal to perform the first
enrollment) is production/deployment work this phase is explicitly
forbidden from implementing (governing prompt: "It must NOT: implement
HATP provider code... wire AG3... enable Runtime Enforcement"). It is
scoped to the recommended next phase (§13).
```

Per the template's own instruction, since these fields cannot be filled
concretely for the current deployment, **HATP-001 is not frozen.**

## 9. Verifier-Key-Replacement and Self-Enrollment Attacks (re-run against this phase's findings)

- **Self-enrollment attack:** agent writes a registry entry mapping an
  attacker-controlled key to `approval_authority=True`. Under the
  currently-true deployment facts (§4.1: same OS user; §4.2: no
  external service; §4.3: branch protection admin-bypassable by the
  same credentials the agent has), **nothing mechanically stops this
  today.** Confirmed **NOT BLOCKED**, consistent with 149O.1A's
  "Should be No — unverified" cells (§22 there), now resolved to a
  concrete "No, not currently blocked" rather than "unverified."
- **Verifier-key-replacement attack:** same analysis, same result —
  **NOT BLOCKED** in the current deployment, for the same reason.

This is exactly the attack the entire HATP architecture exists to
defeat (149O.1A §10, governing-prompt §23-24). Freezing a contract that
claims this attack is blocked, while primary-source evidence this phase
gathered shows it is not blocked in the repository's real, current
state, would create a contract whose text asserts a security property
that does not hold — the precise failure mode the governing prompt's
"DO NOT FREEZE" instructions exist to prevent.

## 10. Repository Scope (item 18, informational — unaffected by Root 2B outcome)

149O.1A's position (repository-specific approval authority, inherited
transitively through the Binding digest rather than a new unstable
identity field, §18 there) is reconfirmed unchanged. This phase found
no new information bearing on repository identity; it remains
**NON-BLOCKING and unaffected** by the Root 2B outcome above, since it
concerns proof-payload shape (Root 1/verification), not the bootstrap
boundary this phase investigated.

## 11. Threat-Capability Matrix (updated with this phase's concrete findings)

| Capability | Autonomous agent | Human approver | Hardware signer | Bootstrap admin/verifier |
|---|---|---|---|---|
| Construct approval payload | Yes | Yes | N/A | N/A |
| Write RAE artifacts | Yes | Yes (same CLI, same credentials) | N/A | N/A |
| Invoke signer request | Yes (may submit payload) | Yes | N/A | N/A |
| Satisfy physical presence | **No — mechanically impossible (Root 1, unchanged from 149O.1A)** | Yes | N/A | N/A |
| Extract private key | **No — hardware non-exportable (Root 1, unchanged)** | No | Sole holder | N/A |
| Enroll approver | **Confirmed possible today — no OS/service/review boundary blocks it (§4, this phase)** | Depends on future Class-B establishment | N/A | Would be No, once Class B exists |
| Alter trusted key registry | **Confirmed possible today, same reason** | Depends on future Class-B establishment | N/A | Would be No, once Class B exists |
| Grant rollback authority | **Confirmed possible today, same reason** | Depends on future Class-B establishment | N/A | Would be No, once Class B exists |
| Verify proof | Yes (read-only, public material) | Yes | N/A | Yes |

The bottom three rows are the load-bearing difference from 149O.1A's
matrix: what that phase marked "Should be No — unverified" this phase
resolves to "Confirmed possible today" for the agent column. This is
the concrete reason freeze does not occur.

## 12. B-149O Findings — Mapping (unchanged, still OPEN)

| Finding | Cause | HATP status |
|---|---|---|
| B-149O-1 (fake CHGR + fake publication receipt) | No trusted human signature at all | Would require a valid HATP proof — none exists; still OPEN |
| B-149O-2 (real Decision + fake Binding + fake registration) | Binding digest not covered by any trusted signature | Would require HATP payload binding (§13 of 149O.1A) — not implemented; still OPEN |
| B-149O-3 (fully hand-authored evidence chain) | No trusted human signature | Same as B-149O-1; still OPEN |
| B-149O-4 (fresh forged evidence key + forged registration) | Attacker-controlled key not excluded by any protected registry | **This phase's finding sharpens this exactly**: even a frozen HATP-001 with Model A alone would not close this finding today, because the registry that would exclude an attacker key has no protected home yet (§4-§9). Still OPEN. |

No implementation or repair occurred this phase (governing prompt
prohibition, §2). All four remain OPEN, unchanged from 149O.1/149O.1A.

## 13. Compatibility Reconfirmation

- **RAE-001:** `RAE-001 COMPATIBLE AS-IS`. RAE-REQ-005 ("this repository
  has no OS-level, cryptographic, or credential-based mechanism to
  authenticate...") and RAE-REQ-009 (no technical privilege separation)
  were re-read directly this phase (`docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`
  §6) and are, if anything, independently corroborated by this phase's
  own `whoami`/`gh api` findings — RAE-001 already anticipated exactly
  this gap. No RAE-001 field, requirement, or lifecycle rule changes.
- **CHGR-001 v1.3:** `COMPATIBLE AS-IS` — header confirmed FROZEN this
  phase; no amendment proposed.
- **RWMPC-001 v1.0, PBPA-001 v1.0, PBPC-001 v1.2:** headers confirmed
  FROZEN this phase; no change; HATP still supplies no Permission Broker
  input.
- **IWC-001 v1.2:** confirmation remains distinct from approval, header
  confirmed FROZEN; unchanged.
- **AESIC-001 v1.3 / AEM:** disclosure-only, header confirmed FROZEN;
  unchanged.
- **TAMC-001 v1.0:** header confirmed FROZEN; no CHGR/TAM authority-
  family composition introduced by this phase's (non-)freeze.

## 14. Fast Green

```
python -m pytest -m fast_green -n auto -q
4391 passed
```

Exact match to entering baseline (149O.1A's own exit baseline). No
`src/pcae/**`, no `docs/contracts/**` file was modified this phase —
confirmed via `git status --short`.

## 15. Governance Validation (this phase)

```
pcae health            -> healthy
pcae check              -> passed
pcae status coherence   -> coherent
pcae doctor task-memory -> clean
pcae push check          -> clean, nothing_to_push (pre-finalization)
pcae runtime inspect     -> Observed / observe / unavailable (unchanged)
pcae notify status       -> telegram configured/enabled
```

## 16. Findings

- **BLOCKING (carried forward, unchanged)**: B-149O-1, B-149O-2,
  B-149O-3, B-149O-4 remain OPEN.
- **BLOCKING (sharpened, this phase)**: Root 2B's approver-authorization
  mapping has **no protected home in this repository's actual, current
  deployment**, now confirmed with concrete primary-source evidence
  (§4) rather than 149O.1A's honest uncertainty. All three candidate
  bootstrap mechanisms were checked directly and found either absent
  (Class A alone/Class C-KMS) or structurally insufficient as currently
  configured (Class C review gate: admin-bypassable, sole collaborator,
  shared local credentials).
- **NON-BLOCKING**: repository-scope binding (149O.1A §18) remains
  adequate as previously specified; unaffected by this phase's findings.
- **OBSERVATION**: this repository's GitHub branch protection is a
  real, useful control against unreviewed changes made through GitHub's
  own PR UI by an external contributor, but does not, on its own,
  establish the boundary HATP-001 Root 2B needs against a same-machine
  autonomous process using the maintainer's own local credentials.
- **DEFERRED**: exact Class-B implementation mechanics (dedicated OS
  principal creation, ACL specification, human authentication procedure
  to act as that principal) — scoped to the recommended next phase.

## 17. Contract Freeze Verdict

**HATP-001 NOT FROZEN — BOOTSTRAP / AUTHORIZATION TRUST GAP REMAINS,
NOW CONCRETELY CONFIRMED RATHER THAN MERELY SUSPECTED.**

`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` was
**not created** this phase.

## 18. RAE Readiness

**NOT READY FOR ROLLBACK INTEGRATION** (unchanged). No trusted root is
implemented or verified; AG3/AG5 remain correctly unwired.

## 19. Implementation Status

```
HATP architecture:          DEFINED (149O.1A, unchanged)
HATP Root 1:                RESOLVED (Model A, unchanged)
HATP Root 2A:                RESOLVED (device genuineness, unchanged)
HATP Root 2B:                MODEL CLASS SELECTED (Class B), NOT ESTABLISHED
HATP contract:               NOT FROZEN
HATP implementation:         NOT IMPLEMENTED
RAE HATP integration:        NOT IMPLEMENTED
AG3/AG5 integration:         NOT IMPLEMENTED
```

## 20. Production Boundary

```
git status --short           -> clean (no working-tree changes from this
                                 phase's investigation; all commands were
                                 read-only inspection: gh api, git remote,
                                 whoami, ssh-add -l, grep)
git diff --name-only <start>..HEAD -- src/pcae/   -> (empty)
git diff --name-only <start>..HEAD -- docs/contracts/  -> (empty)
```

No hardware signer code, PIV/FIDO2 adapter, approver registry
implementation, HATP verifier, or RAE integration was created. No
GitHub repository configuration was modified (branch protection was
read via `gh api`, never written).

## 21. Runtime Boundary

`pcae runtime inspect` before and during this phase: Observed / observe
/ unavailable — unchanged.

## 22. Chapter 149 Status

Outstanding, unchanged in scope, updated in precision:

- HATP Root 2B bootstrap-authority establishment (this phase's finding
  sharpens exactly what is missing: a distinct OS security context, not
  yet created)
- HATP contract freeze (blocked on the above)
- HATP contract independent verification
- HATP implementation planning
- HATP implementation
- HATP independent verification
- RAE HATP integration
- RAE re-verification
- AG3/AG5 integration planning
- AG3/AG5 integration
- integration verification
- TK1/TK2/TK3 re-affirmation

## 23. Recommended Next Phase

**149O.1B.1 — Human Approval Bootstrap Authority Architecture.**

Scope: design and specify (architecture only, no implementation) the
concrete mechanics of the selected Class-B boundary for this
repository's actual deployment — dedicated OS principal creation,
registry file ownership/ACL specification, and the human-authentication
procedure by which the repository maintainer acts as that distinct
principal to perform the first ("root") enrollment, closing the exact
gap §8's Bootstrap Trust Statement leaves unfilled. Only once that
architecture is defined and, per the governing prompt's own ordering,
actually established and independently verified as enforced should a
subsequent phase re-attempt `HATP-001 v1.0` freeze using 149O.1A's
§12-§18/§22-§24 content plus this phase's §6-§9 as its normative basis.

Do not implement HATP provider code, PIV/FIDO2 adapters, or any
approver registry before that architecture phase and its own
independent verification.

## 24. Confirmations (governing-prompt required final-report list)

- RAE-001 v1.0 unchanged. RWMPC-001 v1.0 unchanged. PBPC-001 v1.2
  unchanged. PBPA-001 v1.0 unchanged. CHGR-001 unchanged.
- IWC confirmation remains distinct from approval. AESIC/AEM remain
  disclosure-only. No illegal CHGR/TAM authority-family composition was
  introduced.
- No `HATP-001` contract was frozen this phase.
  `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` was not
  created.
- B-149O-1 through B-149O-4 remain OPEN until HATP implementation and
  independent verification close them; no repair was attempted this
  phase.
- No production HATP implementation was created. No RAE production
  integration was implemented. No AG3 Permission Broker integration was
  implemented. No AG5 Permission Broker integration was implemented. No
  rollback execution behavior changed.
- No POL-001..012 meaning was changed. No POL-013+ was added. TK1/TK2/
  TK3 remain deferred.
- No Runtime Enforcement behavior changed. No Prompt Generation, Prompt
  Dispatch, or agent invocation capability was implemented. Runtime
  remains Observed, maximum capability remains observe, execution
  availability remains unavailable (confirmed via `pcae runtime inspect`
  before and during this phase).
- No GitHub repository configuration (branch protection, collaborators)
  was modified this phase — inspected read-only via `gh api` only.
