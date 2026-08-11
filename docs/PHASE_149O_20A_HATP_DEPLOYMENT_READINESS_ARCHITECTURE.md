# Phase 149O.20A — HATP Deployment Readiness Architecture

HATP DEPLOYMENT READINESS ARCHITECTURE: COMPLETE
— IMPLEMENTATION VERIFIED
— REAL DEPLOYMENT NOT AUTHORIZED
— REAL ACTIVATION NOT AUTHORIZED

## 1. Charter and Mandate

This phase is architecture/deployment-readiness design only. It reconstructs
the complete remaining path from verified implementation to operational HATP
deployment. It does not provision Class-B, create OS principals, touch any
protected root, create real HMIC certification/binding/revocation state, a
Cutover Record, or an activation marker, and it does not activate
`HATP_MANDATORY`. No `src/pcae/**` file, no `scripts/**` file, and no
`docs/contracts/**` file is modified by this phase.

This phase's direct mandate is 149O.19.5G §14 (Strategic Next-Step
Reassessment), quoted verbatim from
`docs/PHASE_149O_19_5G_HMIC_ASSEMBLED_ATTACK_MATRIX_HARDENING.md`:

> "Deployment prerequisites remain unaddressed: no real Class-B principal is
> provisioned on this host, and runtime/executed-source binding
> (HMIC-REQ-063) remains an explicit residual limitation. Recommended next
> phase: a deployment-readiness architecture phase examining what a real
> Class-B provisioning plan requires (not provisioning it), and/or
> disposition of the HMIC-REQ-063 residual limitation as its own scoped
> design phase — not real Class-B provisioning or real activation, which
> remain out of scope until those architecture phases exist and are
> independently reviewed."

This phase addresses both halves of that mandate together, in a single
architecture: the Class-B deployment topology, and the HMIC-REQ-063
disposition, because they are load-bearing for each other (the disposition
of HMIC-REQ-063 depends on which deployment/installation model Class-B
selects; see §14).

## 2. Baseline (149O.19.5G Assembled Implementation/Hardening Result)

Reconstructed from `docs/PHASE_149O_19_5G_HMIC_ASSEMBLED_ATTACK_MATRIX_HARDENING.md`
and independently reconfirmed this phase (§1 — Initial Inspection, below):

- Latest completed phase: 149O.19.5G — HMIC Assembled Attack Matrix /
  Hardening. Status: completed. Report completeness: complete.
- Assembled HMIC Wave A–F verdict: VERIFIED WITH NON-BLOCKING FINDINGS.
- 68 new assembled tests, all passed. Zero production/contract changes
  during 149O.19.5G.
- HMIC-001 is at v1.1. HMIC contract independently verified. Current HMIC
  frozen implementation subject: 24 files. Contract/production identity
  alignment independently verified exact.
- W-1: INDEPENDENTLY CONFIRMED CLOSED AT CONTRACT + IMPLEMENTATION-IDENTITY
  BOUNDARY — VALIDATOR/ADMIN SOURCE SELF-BINDING COMPLETE — DEPLOYMENT/
  RUNTIME-SOURCE PROVENANCE STILL DEFERRED.
- HATP activation-readiness integration implemented: `CertificationStatus.VALID`
  maps to exactly one HMRC readiness fact; all other statuses/validation
  failures map to `False`.
- HMRC readiness: six contractual HMRC-REQ-054 terms remain intact.
  Implementation additionally retains `repository_deployment_identity_valid`
  for seven total implementation readiness checks.
- Historical findings, unchanged, not upgraded: B-149O.19.3-1 INDEPENDENTLY
  CLOSED; B-149O-1..4 INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM
  IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION
  DEFERRED. This phase does not upgrade any of these to deployment closure.

Current operational state (unchanged, reconfirmed this phase, §3):

- HATP production: NOT READY.
- Runtime: Observed / observe / unavailable.
- Real Class-B provisioning: ABSENT.
- Real protected HATP trust root: not provisioned on this host.
- Real HMIC certification artifact / active binding / revocation state:
  ABSENT.
- Real Cutover Record / activation marker: ABSENT.
- Real HATP_MANDATORY activation: NOT PERFORMED.
- Permission Broker: unchanged. POL-005: unchanged. COMP-002: not
  implemented.
- Runtime/executed-source binding: explicit residual limitation under
  HMIC-REQ-063.

## 3. Initial Inspection (This Phase)

```
git status --short                       -> (clean)
git status --branch --short              -> ## main...origin/main
git rev-list --count origin/main..HEAD   -> 0
pcae health                              -> healthy
pcae check                               -> passed
pcae status coherence                    -> coherent
pcae doctor task-memory                  -> warnings (pre-existing, see §32)
pcae push check                          -> clean, nothing_to_push
pcae runtime inspect                     -> Observed / observe / unavailable
pcae notify status                       -> telegram configured/enabled/ready
pcae phase-report show --latest          -> 149O.19.5G, complete, recommends
                                             this deployment-readiness
                                             architecture phase
pcae phase-report reconcile --phase-id 149O.19.5G
                                          -> reconciled, mutation: none
                                             (inspection only)
```

Repo clean, `origin/main..HEAD = 0`, 149O.19.5G completed, HATP production
NOT READY, runtime Observed/observe/unavailable, no real protected/
certification/cutover state — all confirmed.

## 4. Primary Sources Read

Eight bound contracts (docs/contracts/): HATP-001 (`HUMAN_APPROVAL_TRUSTED_
PROVENANCE_CONTRACT.md`), HMRC-001 (`HATP_MANDATORY_ROLLBACK_CONSUMPTION_
CONTRACT.md`), HMIC-001 v1.1 (`HATP_MANDATORY_INDEPENDENT_VERIFICATION_
CERTIFICATION_CONTRACT.md`), HSCE-001 (`HATP_SIGNING_CEREMONY_EVIDENCE_
STORE_CONTRACT.md`), RAE-001 (`ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`),
RWMPC-001 (`REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`),
PBPA-001 (`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`), PBPC-001
(`PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`).

Architecture documents: 149O.1A, 149O.1B/1B.1/1B.2/1B.3, 149O.8, 149O.14,
149O.15, 149O.17, 149O.18A–F, 149O.19, 149O.19.1–149O.19.5G.

Production source directly inspected: `src/pcae/core/hatp_bootstrap.py`
(`HATPTrustStore`, `_default_production_trust_root`, `DeploymentBinding`,
`deployment_binding_matches`, `resolve_canonical_deployment_root`),
`src/pcae/core/repository_identity.py` (`ensure_repository_identity`,
`is_valid_repository_instance_id`), `src/pcae/core/hatp_mandatory_
certification.py` (`_FROZEN_SRC_PCAE_RELATIVE_FILES`,
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, `CertificationStatus`,
`certification_status_satisfies_readiness`), `src/pcae/core/hatp_mandatory_
cutover.py` (`CutoverMode`, `_assess_hatp_mandatory_activation_readiness_at_
root`), `src/pcae/core/permission_broker_foundation.py`
(`ExecutionDisabledRule`, decision vocabulary).

## 5. Deployment Trust Model — Principals and State

Reconstructed from HATP-001 §7–§18, HMRC-001 §19/§41, HMIC-001 §8/§16–§20.

| Entity | Owner | Reader(s) | Writer(s) | Authority role | Mutability |
|---|---|---|---|---|---|
| Human/bootstrap-admin OS principal (`PCAE_BOOTSTRAP_ADMIN_PRINCIPAL`) | itself (OS account) | itself | itself | Sole authority for Protected Root writes, certification, activation, revocation, Cutover Record transitions | Provisioned once at deployment; not created by this phase |
| Ordinary PCAE agent OS principal (`PCAE_AGENT_PRINCIPAL`) | itself (OS account) | itself; read-only on Protected Root | itself; agent-writable repo tree and `.pcae/` only | Runs the autonomous agent; consumes readiness facts, never produces protected authority state | Distinct OS account, mandatory (§6) |
| Runtime process | agent OS principal | n/a | n/a | Executes agent/PCAE code under the agent principal's OS identity | Currently `Observed / observe / unavailable` — no live execution capability exists on this host |
| Repository working tree | agent OS principal (or shared, depending on deployment model, §13) | agent, admin | agent (source), admin (via deployment, §13) | Holds the source whose bytes are digested into `implementation_scope_digest` | Ordinary git-managed tree |
| Protected trust root (`HATPTrustStore.production().root`) | admin OS principal | admin (rw), agent (r-only) | admin only | Houses `registry.json`, `certifications.json`, `certification-bindings.json`, Cutover Record, hardware-credential registry | Admin-provisioned out-of-band; never created by PCAE code (confirmed, §7) |
| HMIC certification state (`certifications.json`, bindings) | admin OS principal (under Protected Root) | admin, agent (read, for validation) | admin only, via `scripts/hatp_certification_admin.py` | Append-only certification records + explicit active-binding pointer | Admin-ceremony only; no agent write path (HMIC-REQ-017/018/020) |
| HATP signer trust state (hardware-credential registry) | admin OS principal | admin, agent (read, for validation) | admin only | Authorized-signer metadata for hardware providers | Admin-provisioned; structurally identical second protected root |
| Cutover state (Cutover Record) | admin OS principal (same Protected Root family, HMRC-REQ-043) | admin, agent (read) | admin only (Protected Activation Authority, HMRC-REQ-041) | `LEGACY_COMPATIBLE → PREPARED → HATP_MANDATORY`, forward-only | Admin-ceremony only |

## 6. Class-B Principal Separation (Freeze)

Reused unmodified from 149O.1B.1 (`docs/PHASE_149O_1B_1_HUMAN_APPROVAL_
BOOTSTRAP_AUTHORITY_ARCHITECTURE.md`), not re-derived from scratch: this
phase inherits, does not re-litigate, that architecture's decision.

Minimum topology, exactly two OS principals for v1:

- **A. Agent principal** — runs the autonomous PCAE agent/runtime.
- **B. Protected human/bootstrap-admin principal** — combines the
  human-approver role and the bootstrap-administrator role into one OS
  account, distinct from A.

Certification administration runs as the same protected human/bootstrap-
admin principal (B). A three-principal split (separate human-approver and
bootstrap-admin accounts) was considered by 149O.1B.1 and explicitly
deferred (HATP-REQ-028) — revisit only if a future phase adopts the
out-of-scope "Threat B" (compromised admin acting maliciously, as opposed
to a compromised agent) into scope. This phase does not reopen that
deferral or invent a third principal.

Explicit negative case, reaffirmed (149O.1B.1 §6): if the human and the
agent run as the *same* Unix/macOS user — this repository's actual, current
development configuration — Class B does **not** hold. Distinct OS-user
separation between the agent principal and the admin principal is
load-bearing and mandatory, not merely preferred.

## 7. Agent Principal — Exact Permissions

Reconstructed from HATP-001 §12–§13/§26, HMIC-001 §16–§20, and
`hatp_bootstrap.py`'s own docstring (lines 205–221).

The agent principal MAY:

- Read the Protected Root's readiness-relevant state (for validation only:
  `HATPTrustStore.production().root`, `certifications.json`,
  `certification-bindings.json`, Cutover Record) — read access, not write.
- Write its own repository-local, untrusted artifacts: `.pcae/hatp-evidence/`
  (HSCE-001, agent-writable, explicitly "not an authority root"),
  `.pcae/repository-identity.json` (Layer 1 CRI, non-authoritative by
  itself, HATP-REQ-051/063).
- Invoke `pcae hatp sign rollback` (produces a proof; does not itself grant
  authority — HSCE-REQ-025).

The agent principal MUST NOT write:

- Trust-anchor state (the Protected Root itself, or anything under it).
- HMIC certifications (`certifications.json`).
- Active HMIC binding (`certification-bindings.json`).
- Revocations.
- Protected deployment identity (`DeploymentBinding` records under the
  Protected Root — distinct from the repo-local `repository_instance_id`,
  §11).
- Protected cutover authority state (the Cutover Record), except through
  no authorized transition path — the architecture grants the agent no
  transition path at all; every Cutover Record write requires the Protected
  Activation Authority (HMRC-REQ-041).

This resolves existing contract semantics exactly; it does not create new
restrictions. No specifically-authorized agent transition path for cutover
state exists anywhere in the frozen contracts, so the "except through..."
clause in this phase's governing prompt (§5) has an empty exception set:
the agent has zero write path to any protected authority state, full stop.

## 8. Protected Admin Principal — Exact Write Authority

The admin principal (B, §6) is the sole party authorized to:

- Create the Protected Root (§9).
- Create HMIC certification records (`scripts/hatp_certification_admin.py`
  ceremony, HMIC-001 §9–§13).
- Supersede/establish the active-certification binding pointer.
- Revoke a certification.
- Bootstrap and maintain trust state: hardware-credential registry entries
  (authorized signers), `DeploymentBinding` records.
- Transition the Cutover Record (`LEGACY_COMPATIBLE → PREPARED →
  HATP_MANDATORY`, HMRC-REQ-041).

No ordinary agent path exists to any of the above, confirmed by direct
source inspection (§7) and by 149O.19.5G's own `admin_agent_unreachability`
test finding: "No `src/pcae/**` file besides the certification module
itself references the admin writer primitives; no CLI/agent code path
imports the admin script; ordinary agents/CLI have zero path to creating or
revoking certification authority."

## 9. Root Creation

Ordinary PCAE agent MUST NOT bootstrap its own authority root. This is
already structurally true today: `hatp_bootstrap.py`'s
`_default_production_trust_root()` resolves a fixed, hardcoded,
platform-specific path (`/Library/Application Support/PCAE/HATP/trust-store`
on macOS, `/etc/pcae/hatp/trust-store` on Linux) and never calls `mkdir` —
confirmed by direct source inspection. No PCAE code path creates the
Protected Root.

Frozen requirement for any future provisioning phase: the Protected Root
MUST be created by the admin principal, out-of-band from any PCAE agent
invocation (e.g. a manual `mkdir` + `chown`/ACL step performed by a human
operator with admin OS credentials, or an admin-run, admin-invoked
provisioning script that itself requires the admin's own OS write
privilege to execute — never a PCAE-agent-triggered code path). This phase
does not write that provisioning script; it only fixes the requirement
that whichever future phase writes it must satisfy this non-negotiable
invariant (DRA-S5, §86).

## 10. Repository Identity (`repository_instance_id`)

Reconstructed from `src/pcae/core/repository_identity.py` and HATP-001
§18/§49–§53 (CRI Model A).

- **What it is:** a UUID4 string, generated and validated as version-4.
- **Where it lives:** repository-local, agent-writable:
  `.pcae/repository-identity.json` (`repository_instance_id`,
  `created_at`, `schema_version`).
- **Who creates it:** `ensure_repository_identity(root)` — any principal
  able to write to the repository, including the ordinary agent. This is
  deliberate: creation is not privileged, because the identifier alone
  grants no authority (HATP-REQ-051/063 — "possession, knowledge, copying,
  or modification of the identifier defined here SHALL NOT by itself grant
  any approval authority").
- **Protected or repository-local:** repository-local, explicitly Layer 1
  of CRI Model A — not a trust root, not a secret, not itself an authority
  fact.
- **How it is bound to protected deployment state:** the *authority-bearing*
  fact is Layer 2 — the admin-owned `DeploymentBinding` record under the
  Protected Root, which pairs a `repository_id` with a
  `canonical_deployment_root` and an authorized `principal_id`.
  `deployment_binding_matches()` only returns `True` when both fields match
  a non-revoked binding. Identifier ≠ authority is explicit and preserved
  by this phase: an agent creating or copying
  `.pcae/repository-identity.json` grants itself nothing; only an admin
  writing a matching `DeploymentBinding` under the Protected Root does.

## 11. Deployment Identity

Canonical deployment root binding uses `resolve_canonical_deployment_root()`
(`hatp_bootstrap.py`): absolute path, `os.path.normpath`, then
`.resolve(strict=True)`, rendered as `.as_posix()`. This guarantees the same
physical directory canonicalizes identically on repeated calls; it does not
attempt symlink-escape containment (there is no separate trusted
containment root for the subject directory itself — see §12).

Operational provisioning rule, frozen this phase: a `DeploymentBinding`
pairs exactly one `repository_id` with exactly one `canonical_deployment_
root`. Copying a repository (clone, tarball copy, backup restore) to a new
physical path — and therefore a new canonical deployment root — produces a
binding mismatch: `deployment_binding_matches()` returns `False`, and any
certification bound to the old `(repository_instance_id,
canonical_deployment_root)` pair maps to `WRONG_DEPLOYMENT`. "Copy repo →
reuse certification from another deployment" is therefore already
structurally prevented by the existing binding model; no new mechanism is
required. This phase freezes that as the deployment-identity architecture
result — see §67 (attack #7 "wrong repo/deployment cert reuse").

## 12. Worktree Semantics

Per 149O.1B.2 (`PHASE_149O_1B_2_CANONICAL_REPOSITORY_IDENTITY_ARCHITECTURE.md`)
and the canonicalization logic in §11: `resolve_canonical_deployment_root`
resolves to a single physical path via `Path.resolve(strict=True)`, which
follows symlinks to their real target. Consequences, frozen this phase:

- **A git worktree** (`git worktree add`) is a distinct physical directory
  with its own resolved canonical path → a distinct `canonical_deployment_
  root` → a distinct deployment requiring its own `DeploymentBinding` and
  its own certification. It is **not** the same repository instance for
  HATP purposes, even though it shares git history/objects with the
  original checkout.
- **A clone** is likewise a distinct physical directory → new deployment,
  new certification requirement.
- **A copy** (cp -r, tarball extraction) is likewise a distinct physical
  directory → new deployment, new certification requirement.
- **A symlinked root**: because `resolve_canonical_deployment_root` calls
  `.resolve(strict=True)`, a symlink and its target resolve to the *same*
  canonical path — so a symlink pointing at an already-bound deployment
  root is treated as the *same* deployment instance, not a new one. This is
  intentional (symlinks are a path-naming convenience, not a distinct
  physical directory) but means the Protected Root's own directory must
  itself not be reachable via an agent-writable symlink redirect (this is
  a Class-B directory-protection requirement, not a deployment-identity
  concern — see §67 attack #8 "protected root symlink").
- **An alternate checkout** (e.g. a second `git clone` of the same remote)
  is a distinct physical directory → new deployment, new certification
  requirement, identical treatment to "clone" above.

No new mechanism is introduced; this section applies the existing
canonicalization logic explicitly to each named case, per 149O.1B.2's own
architecture.

## 13. Installation Model (Decision Record)

**Selected: Model A — editable install from the canonical repository
working tree.** This is a Decision Record, not ambiguous.

Rationale:

- This is the only topology PCAE runs from today, and the only topology
  HMIC-001 v1.0/v1.1 certifies (HMIC-REQ-064, "Editable-Install /
  Source-Checkout Topology Only" — installed-wheel or other non-editable
  distribution modes are explicitly unsupported by v1.0; no future
  implementation may silently treat a wheel-installed deployment as
  certifiable without an explicit future contract revision naming that
  mode).
- `implementation_scope_digest` binds on-disk source-byte content of the
  24 frozen files, read directly from the repository tree — this
  computation is only meaningful when the executing Python environment's
  editable install (`pip install -e .` / `.venv` pointing at the source
  tree) resolves imports to that same tree.
- Models B (installed wheel/site-packages), C (dedicated immutable
  deployment tree), and D (another explicitly selected model) are **not
  selected** for the first real deployment. Any future adoption of Model
  B/C/D requires its own explicit future contract revision (per
  HMIC-REQ-064) and is out of this phase's scope to design.

Production executed-source location is therefore: the same repository
working tree whose canonical deployment root is bound in the
`DeploymentBinding`, running under an editable install (`pip install -e .`
or equivalent `PYTHONPATH`-free editable resolution) from that tree. This
is not left undefined.

## 14. HMIC-REQ-063 Disposition (Central Deliverable)

Exact contract text (HMIC-001 §19, quoted in full):

> "HMIC-REQ-063 (Import-Shadowing / Executed-Code Binding — Out of Scope,
> v1.0). `implementation_scope_digest` binds the on-disk byte content of
> the frozen file set. It does NOT verify that the Python interpreter
> actually executing PCAE resolves its imports of those modules to those
> exact on-disk files (module shadowing, `sitecustomize`, `PYTHONPATH`
> injection, or an editable-install redirect could in principle cause a
> different file's code to execute despite an identical on-disk frozen-file
> digest). v1.0 of this contract does NOT implement an executed-code/
> runtime-module-resolution check. This is a named, explicit limitation —
> not a silent gap."

**Selected disposition: OPTION C — BLOCKING ONLY FOR SOME DEPLOYMENT
MODELS.**

Rationale, derived (not assumed):

Given §13's Decision Record (Model A, editable install from the canonical
repository working tree, the only certifiable topology under HMIC-REQ-064),
the executed-source threat surface HMIC-REQ-063 names is narrower than it
would be under a wheel/site-packages model:

- Under Model A, there is exactly one source tree on disk that the editable
  install resolves to, and that tree is exactly the tree
  `implementation_scope_digest` reads. The residual gap is: could something
  *else* on `sys.path` shadow a frozen module ahead of the editable-install
  entry (a `PYTHONPATH` entry, a `sitecustomize.py`, a `.pth` file, an
  import hook) so that the *executing* bytes differ from the *certified*
  bytes while the digest still matches the untouched on-disk tree? This
  attack requires control over the *agent's Python environment*
  (site-packages, `PYTHONPATH`, or files outside the repository tree that
  Python's import machinery would consult), not merely control over
  repository files.
- Under the frozen threat model (§16), a malicious agent that already has
  the OS-level capability to write `sitecustomize.py` into the interpreter's
  site-packages, or to set `PYTHONPATH` in the process environment that
  launches the agent runtime, already exceeds the "malicious agent
  controlling repository files" threat class Class B is designed to
  contain — it has moved into "malicious control over the Python execution
  environment," a distinct, broader threat class (§16). Class B's OS
  boundary (§6) constrains what the agent principal's OS account can write;
  it does not, by itself, constrain what code an already-running process
  under that same account can inject into its own future imports unless a
  separate control (e.g. a locked-down, admin-owned, read-only venv;
  `-P`/`-I` interpreter isolation flags; a frozen `PYTHONPATH`) is also
  provisioned.
- Therefore: **for an initial deployment where the agent OS principal's own
  environment (site-packages, `PYTHONPATH`, interpreter invocation) is
  itself provisioned and locked down by the admin principal** (not
  self-managed by the agent) — e.g. an admin-created, agent-read-only
  virtualenv with no writable site-packages, no `PYTHONPATH` override
  permitted in the agent's launch environment, no world-writable `.pth`
  files — HMIC-REQ-063's residual gap is **accepted for that deployment
  model** (equivalent to OPTION A for that specific case), because the
  channel it would need lies outside what the agent OS principal can reach.
- **For any deployment where the agent OS principal can write to its own
  interpreter's import search path** (a self-managed venv the agent can
  `pip install` into, a `PYTHONPATH` the agent's own launch command
  controls, a writable site-packages) — HMIC-REQ-063 is **BLOCKING**: no
  trustworthy claim that "the certified bytes are the executing bytes" can
  be made, and deployment MUST NOT proceed to `HATP_MANDATORY` activation
  under that configuration without first implementing an executed-source
  binding check (§18).

This is OPTION C, not OPTION A, because it is conditional on a deployment
prerequisite (admin-locked agent Python environment) that does not yet
exist on this host and is not yet a frozen Class-B requirement elsewhere in
the corpus — this phase adds it as a new, explicit Class-B deployment
prerequisite (§79, Decision Record) precisely because HMIC-REQ-063's
disposition depends on it.

This is not OPTION B (unconditionally blocking) because requiring a full
executed-source binding *implementation* (§18) before any deployment can
occur would contradict HMIC-REQ-064's own acceptance of the editable-install
topology as certifiable, and would add an implementation burden this
architecture-only phase has no authority to mandate as a hard prerequisite
when a narrower environmental control (locked-down venv) achieves the same
practical protection for the threat class actually in scope (Threat A, §16).

**Consequence for "HATP production READY" (§65):** HATP MAY become
production READY under Model A with HMIC-REQ-063 accepted as a residual
limitation, but only when the deployment additionally satisfies the
admin-locked-agent-environment prerequisite (§79 DRA-REQ list item). If
that prerequisite is not met, the correct claim is qualified: "READY WITH
DECLARED EXECUTED-SOURCE PROVENANCE LIMITATION" is not available — the
deployment simply is not ready, because the accepted-residual-limitation
branch of this disposition does not apply.

## 15. HMIC-REQ-063 Risk Analysis

Attack: protected certification binds repository source A. Runtime executes
authority code B from site-packages, `PYTHONPATH`, another checkout, an
import hook, or a shadow package.

**Can certification still validate? Yes — this is the confirmed operational
consequence.** `implementation_scope_digest` is computed by reading bytes
directly from the filesystem paths of the 24 frozen files under the
certified repository root; it does not inspect `sys.modules`, `__file__`
attributes of already-imported modules, or the interpreter's actual import
resolution. A validation run recomputes the digest from repository A's
on-disk bytes and finds it matches the stored certification — VALID —
regardless of which bytes the *currently executing* interpreter actually
loaded for code path B. The validator answers "does the certified
repository's on-disk source match what was certified," not "did the running
process execute that source." This is the exact, confirmed gap
HMIC-REQ-063 names; this phase adds no new gap, it only makes the
operational consequence explicit and states the deployment-model-scoped
mitigation (§14).

## 16. Threat Model

Four distinct threat classes, separated per this phase's governing prompt
§16:

1. **Malicious agent controlling repository files** — the agent OS
   principal, or code running under it, modifies files inside the
   repository working tree (including the 24 frozen files). **In scope**
   for Class B / HMIC. This is the threat `implementation_scope_digest`
   and the Class-B agent/admin OS separation (§6–§7) are designed to
   contain, and do contain: any such modification changes the digest and
   invalidates certification (confirmed, 149O.19.5G
   `identity_self_binding_attacks` finding).
2. **Malicious control over the Python execution environment** (writable
   site-packages, `PYTHONPATH` injection, import hooks, `sitecustomize`) —
   **conditionally in scope**, per §14: in scope (must be prevented by
   provisioning, not by HMIC) when the agent OS principal can reach it;
   accepted as out of the digest-verification boundary (though still
   required to be environmentally prevented) when the agent's environment
   is admin-locked.
3. **Bootstrap/admin compromise** — **out of scope** for Class B's threat
   model (Threat B in 149O.1B.1's own terms), consistent with 149O.1B.1's
   explicit deferral of a three-principal split; this phase does not
   change that scoping.
4. **OS/root compromise** — **out of scope**. Class B's OS-enforced
   security-principal/ACL boundary is a boundary *between* the agent and
   admin OS accounts under a shared, trusted OS/kernel; it grants no
   resistance to an attacker who already holds root/Administrator on the
   host, since root can read/write both accounts' files and bypass any
   ACL. This phase does not claim otherwise (§17).

## 17. Root / OS Admin

This architecture does not claim resistance to a fully compromised OS
root. Class B's ACL/security-principal boundary is meaningful only between
the agent principal and the admin principal, both operating under the same
trusted OS kernel and root authority. A root-level compromise can read the
Protected Root, forge or corrupt Protected Root content, or impersonate
either OS principal, defeating the entire trust model. The physical/hardware
signer boundary (HATP Root 1 — non-exportable key, human presence per
operation) survives a *software*-only OS compromise for operations it is
actively invoked on (an attacker cannot forge a fresh hardware signature
without the physical device and human presence), but it does not protect
already-stored trust-store/certification/binding state from a root-level
attacker who can simply overwrite files those checks read, nor does it
prevent a root-level attacker from disabling the checks entirely. This is
stated precisely, not left implicit, per this phase's governing prompt §17.

## 18. Executed-Source Binding — Candidate Designs (Comparison, No Implementation)

Evaluated for a future phase, should Model B/C/D adoption or an
agent-writable-environment deployment ever require closing HMIC-REQ-063
fully:

| Candidate | Trust property | Weakness |
|---|---|---|
| `importlib` origin verification (check `module.__file__` / `__spec__.origin` for each frozen module at runtime, compare to certified repository root) | Verifies actual resolved import origin at check time | Self-referential — the verification code itself must run trusted bytes to be believed (§19); only covers modules already imported at check time |
| Canonical module-origin binding (pin `sys.path`/`sys.meta_path` at process start, refuse to start if resolution differs from certified root) | Fail-closed at startup, before any authority-bearing code runs | Requires a trusted startup measurement point that itself must be certified; adds complexity to process bootstrap |
| Installation manifest digest (hash the installed package/venv layout, not just repo source) | Extends `implementation_scope_digest`'s model to the installed artifact, not just source | Only meaningful under Model B/C (installed/immutable tree); not applicable to Model A's editable-install topology without redefinition |
| Executable/package hash manifest | Verifies the on-disk installed bytes match a signed manifest | Same self-referential concern; needs its own trust anchor for the manifest signature |
| Signed deployment manifest | Admin-signed record of expected `sys.executable`, venv identity, module origins | Strongest candidate for Model B/C; requires a new protected artifact and ceremony, out of scope for this architecture-only phase to design in full |
| Protected deployment source manifest | Similar to above, scoped to source-tree identity rather than installed-package identity | Overlaps significantly with `DeploymentBinding` + `implementation_scope_digest`; marginal value under Model A |
| Immutable venv/wheel identity | Treats the venv itself as a certified artifact | Requires Model B/C adoption; not applicable under this phase's Model A decision (§13) |
| Startup measurement | Record process `sys.executable`, `sys.path`, and loaded-module origins once at process start, compare against certified expectation before granting any readiness fact | Closest fit for Model A; still self-referential (§19) unless the measurement code itself is part of the frozen, digested set (it already would be, since it would live in `src/pcae/`) |
| Process executable/module verification | Broadest version of the above, covering `sys.executable` identity itself (protects against a swapped interpreter binary) | Adds an additional protected fact (expected interpreter path/hash) requiring its own admin-provisioning step |

No candidate is selected or implemented by this phase. The startup-
measurement family is the most promising direction for a future Model-A-
scoped follow-on architecture, because it can be implemented as ordinary
`src/pcae/` code already subject to `implementation_scope_digest` protection
(§19), rather than requiring a new deployment-manifest primitive.

## 19. Self-Binding Consequence

Any future runtime/executed-source provenance verifier must itself have a
protected trust disposition — it must not become a second, unaudited
authority root. Precedent: HMIC-001 §50 already reasons through this
non-circularity for `implementation_scope_digest` itself (which includes
`hatp_mandatory_certification.py` and `scripts/hatp_certification_admin.py`
in the set of files it digests) — the validator recomputes fresh from live
bytes on every call; it never trusts its own stored output. A future
executed-source verifier must follow the identical discipline: (a) live in
`src/pcae/` so its own bytes are already covered by
`implementation_scope_digest`, (b) never cache or memoize a prior "verified"
result (repeating the `freshness_no_cache_read_only_authority_input`
property 149O.19.5G already tests for the certification validator), and
(c) never accept a caller-suppliable override of its own measurement. This
phase does not repeat W-1's original mistake (a validator that could
initially be pointed at attacker-controlled input) by pre-authorizing any
design that has not been shown to satisfy these three properties.

## 20. Deployment Manifest

**Determination: not needed for the initial deployment under this
architecture's selected disposition (§14 OPTION C, Model A).**

`DeploymentBinding` (repository_instance_id + canonical_deployment_root +
principal_id, admin-owned) together with `implementation_scope_digest`
(24-file source-byte identity) and `contract_versions` (HMIC-REQ-048/049)
already cover: repository identity, canonical deployment root, source
identity, and contract identity. The items a deployment manifest would add
beyond these — Python executable identity, venv/site-packages identity,
module-origin identity — are exactly the executed-source-binding concerns
deferred by HMIC-REQ-063 (§14, §18) and not required for Model A's accepted-
residual-limitation branch. If a future phase adopts Model B/C (§13) or
extends the environment threat class into scope (§16 item 2 becoming fully
in-scope rather than conditionally in-scope), a deployment manifest becomes
necessary at that time, with contents as listed in this phase's governing
prompt §20 (`repository_instance_id`, canonical deployment root, Python
executable, venv/site-packages identity, source/module origins, HMIC
implementation identity, contract identities), owned and ceremony-governed
by the admin principal identically to certification (§29). Not built now.

## 21. Python Executable

Production architecture does **not** bind `sys.executable` under this
phase's selected disposition (§14, §20). Current development runtime is
CPython 3.9.6 in the repository's own `.venv` — this is explicitly *not*
assumed to be the production deployment model. A future deployment MUST
name its own Python executable/venv as part of its admin-provisioning step
(§79), but no cryptographic or digest binding of that executable identity
is required under Model A's accepted-residual-limitation branch (§14).
Should `sys.executable` binding become necessary (Model B/C adoption, or
environment threat class moving fully in-scope), it is covered by the
"process executable/module verification" candidate in §18, not built now.

## 22. PYTHONPATH

**Policy, frozen this phase:** the agent OS principal's launch environment
MUST NOT be able to set or influence `PYTHONPATH` (or any equivalent
import-search-path override) for the process that executes certified,
frozen-file authority code. This is the exact prerequisite §14's
disposition conditions the accepted-residual-limitation branch on. Concrete
mechanism (illustrative, not frozen as final, consistent with 149O.1B.1's
own treatment of directory permissions in §13): the admin principal
provisions and owns the agent's launch environment (systemd service
`Environment=` block owned by admin, or an admin-owned wrapper script/venv
activation the agent cannot modify) such that `PYTHONPATH` is fixed at
process-start time by admin-controlled configuration, not by anything the
agent's own OS account can write. A deployment that instead lets the agent
account manage its own launch environment (self-managed venv, agent-
writable systemd unit, agent-writable shell profile sourced at launch) does
NOT satisfy this prerequisite and falls into §14's BLOCKING branch.

## 23. Import Hooks

`sys.meta_path` entries, `sitecustomize.py`, `usercustomize.py`, and `.pth`
files are dispositioned identically to §22: they are import-search-path-
adjacent mechanisms reachable only through the same channel (writable
site-packages / writable interpreter configuration directories). Under an
admin-locked agent environment (§14 accepted-residual-limitation branch),
these are already excluded because the agent OS principal has no write
access to the site-packages/interpreter configuration directories that
host them. This phase does not add a separate mechanism to detect or block
import hooks beyond the environmental lock already required by §22 — adding
a runtime self-check for their presence would be over-engineering beyond
the threat model actually in scope for Model A (Threat A, §16), and is
explicitly not built here, consistent with this phase's governing prompt
§23 ("do not over-engineer beyond threat model, but explicitly disposition").

## 24. Site-Packages

Not applicable to the selected Model A (editable install from the
canonical repository working tree, §13) for the *certified* PCAE package
itself — an editable install resolves `import pcae` to the repository
tree, not to a copied package in site-packages. Third-party dependencies
(§26) do live in site-packages and are explicitly outside
`implementation_scope_digest`'s scope. Should a future phase adopt Model B
(installed wheel), the "how does certified repository source correspond to
executing package bytes" question becomes live and must be answered by
that future phase's own contract revision (HMIC-REQ-064 requires this
explicitly) — not answered here, since Model B is not selected.

## 25. Editable Install

Canonical module origins can be bound safely under Model A specifically
because: (a) there is exactly one on-disk copy of the certified source
(the repository working tree itself — no separate "build" or "install"
step copies bytes elsewhere), so `implementation_scope_digest`'s file-read
and the interpreter's own import resolution target the identical files
when no shadowing channel exists; and (b) HMIC-REQ-064 already scopes v1.0/
v1.1 certification exclusively to this topology, so no additional
architecture invention is required to justify it — this phase inherits and
applies that existing contractual scoping rather than re-deriving it.

## 26. Third-Party Dependencies

HMIC presently binds PCAE source only (`implementation_scope_digest`'s 24
frozen files), not any third-party package. Deployment-position
classification, this phase:

- **Trusted platform dependency:** Python stdlib, Git (the `git` binary
  invoked by subprocess for revert/promotion operations). Assumed correct
  and unmodified by the threat model; verifying stdlib/Git integrity is
  outside Class B's scope (an OS-platform-integrity concern, not a PCAE
  deployment concern).
- **Version-pinned deployment dependency:** `cryptography`, `fido2`
  (pinned `>=1.1,<2` per `pyproject.toml`) — required for hardware-signer
  operation; version-pinned but explicitly excluded from
  `implementation_scope_digest`'s scope by HMIC-REQ-065. A future
  deployment-readiness follow-on MAY choose to add dependency-manifest
  pinning verification (e.g. `pip freeze` hash comparison) as part of a
  deployment manifest (§20) if Model B/C is ever adopted; not required
  now.
- **Future attestation scope:** any executed-source-binding candidate that
  extends beyond PCAE's own source (§18's "installation manifest digest" /
  "executable/package hash manifest" candidates) would need to decide
  whether third-party dependency bytes are in scope; not decided by this
  phase, since no candidate from §18 is selected.
- **Outside current threat model:** all other installed packages not on
  the HATP signing/verification code path (test-only dependencies such as
  `pytest`, developer tooling).

## 27. FIDO2/PIV Provider Deployment

Reconstructed from HATP-001 §10–§11 and production source
(`hatp_fido2_provider.py`, `hatp_piv_provider.py`, `hatp_hardware_
credentials.py`). Operational prerequisites for a real deployment (not
performed by this phase):

- **Device:** a physical authenticator satisfying the generic
  `HATP_HARDWARE_PROVIDER_V1` profile (non-exportable key, fresh
  user-presence assertion per operation). FIDO2 and PIV are not declared
  interchangeable by contract; whichever protocol is chosen must be shown
  to actually satisfy the profile. Today, only the FIDO2 provider
  (`Fido2HardwareProvider.verify()`) is implemented as conformant; the PIV
  provider is currently `NOT_CONFORMANT`/fail-closed by design (not
  hardware-backed today).
- **Credential registration:** an admin-run enrollment step writing an
  authorized-signer record into the hardware-credential registry — a
  second, structurally identical protected root
  (`/Library/Application Support/PCAE/HATP/hardware-credentials` macOS,
  `/etc/pcae/hatp/hardware-credentials` Linux).
- **Authorized-signer metadata:** signer identity, enrollment timestamp,
  and any revocation-relevant fields required by the hardware-credential
  registry schema.
- **Revocation:** an admin-only path to mark a previously authorized signer
  revoked (mirrors certification revocation, §8).
- **Trust-store installation:** the Protected Root itself must exist and be
  admin-owned before any signer can be enrolled into it (§9 ordering).

No hardware setup is performed by this phase.

## 28. Signer Trust Bootstrap

The admin principal installs authorized-signer records; the agent cannot
self-authorize a signer. This follows directly from §7/§8 (agent has no
write path to any Protected Root content, including the hardware-credential
registry) — no new mechanism is introduced, this is the same write-authority
model applied to signer records specifically.

## 29. HMIC Certification Bootstrap — First-Real-Certification Sequence

Derived exact order (not the illustrative example in this phase's governing
prompt, reconciled against the actual prerequisite graph in §5–§13, §27):

1. Admin principal provisions the OS-level Class-B boundary: creates the
   distinct admin OS account (if not already the operator's own account)
   and the distinct agent OS account, establishes the Protected Root
   directory with admin read/write, agent read-only permissions (§6, §9).
2. Admin principal provisions the agent's launch environment as
   admin-locked (no agent-writable `PYTHONPATH`/site-packages/import-hook
   channel) — the §14/§22 prerequisite for HMIC-REQ-063's accepted-residual
   branch to apply.
3. Admin principal provisions/registers the hardware signer (§27–§28):
   device enrollment, authorized-signer record written into the
   hardware-credential registry under the Protected Root.
4. Repository/deployment identity is established: `repository_instance_id`
   exists (agent or admin may create the repo-local Layer 1 file, §10);
   admin principal writes the matching `DeploymentBinding` (Layer 2, §10)
   pairing that `repository_instance_id` with the resolved canonical
   deployment root and the authorized principal.
5. Final certified source is deployed: the repository working tree at the
   canonical deployment root is at the exact commit/byte-state intended for
   certification (Model A, §13 — no separate "deploy" copy step; the
   working tree *is* the deployed artifact).
6. Independent implementation verification is performed (an
   already-established governed-phase pattern — e.g. the 149O.19.x chain)
   confirming the 24-file frozen set and contract set match what is
   intended to be certified. This is a governance/process step, not a new
   mechanism.
7. Protected admin invokes the HMIC certification ceremony
   (`scripts/hatp_certification_admin.py`, admin OS credentials required)
   — computes `implementation_commit`, `implementation_scope_digest`,
   `contract_versions` fresh from live bytes, and writes a new
   `CertificationRecord` to `certifications.json`.
8. Certification artifact is published (the `CertificationRecord` now
   exists in `certifications.json`, but is not yet the active-bound
   certification — Certify and Activate remain separate, non-causal
   ceremonies per HMIC-001 §35).
9. Admin principal establishes the explicit active-binding pointer in
   `certification-bindings.json`, making this specific certification the
   one the validator consults (no implicit-latest selection, HMIC-REQ-085).
10. Ordinary readiness assessment (`_assess_hatp_mandatory_activation_
    readiness_at_root`) now sees HMIC status `VALID` for the
    `mandatory_consumption_implementation_independently_verified` term.

This reorders the illustrative sequence in the governing prompt only
where the prerequisite graph requires it (Class-B boundary and agent-
environment lock, steps 1–2, must precede repository/deployment identity
and certification, since the admin principal and its exclusive write
capability must already exist before any admin-only ceremony can run; the
agent-environment lock specifically must precede certification because
HMIC-REQ-063's accepted-residual disposition, on which this whole
architecture's "HATP production READY" claim depends, is conditioned on
it, §14).

## 30. Certification After Source Change

Any change to a frozen 24-file source path invalidates the existing
certification: `implementation_scope_digest` is recomputed fresh from live
bytes on every validation (no caching, §19), and a changed file changes at
least one `<path>\0<sha256>\n` record, changing the aggregate digest, which
no longer matches the stored `CertificationRecord.implementation_scope_
digest` — the validator reports `IMPLEMENTATION_MISMATCH` (confirmed,
149O.19.5G `identity_self_binding_attacks` / `historical_replay_rejected`
findings). Operational update procedure, frozen this phase: no automatic
recertification exists or is permitted; the admin principal must re-run the
full certification ceremony (§29 steps 6–9) after any frozen-file change,
following the same independent-verification-before-certify discipline as
the initial ceremony. This applies equally to a single-line change, a
refactor, or a full file rewrite — the digest is content-based, not
diff-based.

## 31. Contract Change

Identical disposition to §30: `contract_versions` binds each of the eight
bound contracts' own version headers; any bound-contract version bump
invalidates the existing certification (`CONTRACT_MISMATCH`), requiring the
same re-certification ceremony. No automatic recertification.

## 32. Admin-Script Change

Identical disposition: `scripts/hatp_certification_admin.py` is itself one
of the 24 frozen files (§4, confirmed enumeration) — a change to the
admin-ceremony script's own bytes changes `implementation_scope_digest`
exactly like any other frozen file, invalidating existing certifications
and requiring re-certification through the (now-changed) admin script
itself. No special-case exemption exists for the admin script changing
itself; HMIC-001 §50 already reasons this is non-circular because the
validator always recomputes fresh.

## 33. Cutover-Source Change

Identical disposition: `hatp_mandatory_cutover.py` is also one of the 24
frozen files. A change to cutover-logic source invalidates existing
certifications for the same reason as §30–§32. This is the same mechanism
applied three times to three different frozen-file categories (application
logic, admin ceremony, cutover logic) — not three different mechanisms.

## 34. Deployment Update State Machine

These are deployment-readiness *labels* this architecture document uses for
exposition, distinct from HMRC-001's own `CutoverMode` enum
(`LEGACY_COMPATIBLE`/`PREPARED`/`HATP_MANDATORY`), which remains the sole
production state-machine authority and is not overloaded or extended by
this phase:

- **DEPLOYED_UNCERTIFIED** — Class-B boundary provisioned (§29 steps 1–2),
  repository/deployment identity established (§29 step 4), source deployed
  (§29 step 5), but no `CertificationRecord` exists yet. Corresponds to
  HMIC status `MISSING`.
- **CERTIFIED_INACTIVE** — a `CertificationRecord` exists (§29 step 8) but
  is not yet the active-bound certification (§29 step 9 not yet performed).
  Corresponds to HMIC status `MISSING` still (no active binding to
  validate against) despite a certification record existing on disk —
  this is intentional per HMIC-001's no-implicit-latest rule.
- **CERTIFIED_ACTIVE** — the active-binding pointer is set (§29 step 9);
  HMIC status is `VALID` (assuming no other defect). This alone satisfies
  one of HMRC-REQ-054's six terms; it does not by itself mean `PREPARED`
  or `HATP_MANDATORY` (§35).
- **READY** — all seven implementation readiness checks (§ per 149O.19.5F/
  149O.19.5G — the six HMRC-REQ-054 terms plus `repository_deployment_
  identity_valid`) evaluate `True`. Distinct from `PREPARED` (§37).
- **HATP_MANDATORY** — the actual production `CutoverMode` value, entered
  only via the admin-only, lock-held transition (HMRC-REQ-041, and the
  fresh-recheck discipline in §49–§51 below).

These labels describe deployment-readiness progress; they are not stored
anywhere and do not gate any production code path — `CutoverMode` remains
the only enforced state machine.

## 35. Certification ≠ Activation

Retained, unmodified. Certify (§29 steps 6–8) and Activate (§29 step 9,
the binding-pointer write) are separate, non-causal ceremonies per
HMIC-001 §35; a `CertificationRecord` existing in `certifications.json`
grants nothing until explicitly bound.

## 36. Active Certification ≠ Full Readiness

Retained, unmodified. `CERTIFIED_ACTIVE` (§34) satisfies exactly one of
seven implementation readiness checks (`mandatory_consumption_
implementation_independently_verified`); the other six
(`class_b_protected_storage_available`, `repository_deployment_identity_
valid`, `hatp_substrate_operational`, `hsce_signing_implementation_
available`, `production_dependency_provenance_valid`, `protected_
activation_authority_mechanism_available`) are independent facts that must
also be true.

## 37. Readiness ≠ Activation

Retained, unmodified. All seven readiness checks evaluating `True` (§34
`READY`) is a precondition the admin principal consults before invoking the
`PREPARED` transition; it does not itself perform the transition.
`CutoverMode` only changes via the admin's explicit, deliberate action.

## 38. Activation ≠ Execution Availability

Retained, unmodified, and reinforced by HMRC-REQ-030/037 (§39–§40 below):
even `HATP_MANDATORY` does not require or guarantee that MC-14/ETPR's
truthful `simulation_only=False` request path resolves `ALLOW` — it
currently deterministically resolves `DENY` via POL-005, because `COMP-002`
remains `not_implemented`. A rollback-execution rollback path may remain
denied even after real activation.

## 39. PB / COMP-002 Blocker

Reconstructed exactly (HMRC-REQ-029/037, PBPC-REQ-036/037): a truthful
AG3/AG5 rollback-execution request that honestly sets `simulation_only=
False` deterministically resolves `DENY` via POL-005's `ExecutionDisabledRule`
(`policy_id="POL-005"`), because `COMP-002` (the Permission Broker
Foundation's own general-purpose execution boundary) remains
`not_implemented`. HMRC-001 explicitly classifies this as expected,
accepted behavior (HMRC-REQ-037), not a defect — `HATP_MANDATORY` does not
guarantee rollback availability, and reaching it does not additionally
require MC-14/execution-enforcement capability to exist (HMRC-REQ-030/055).
This phase classifies this as a separate concern from HATP deployment
readiness, per §40.

## 40. Deployment-Ready vs. Operational-Rollback-Ready

Three distinct terms, frozen this phase, none conflated:

- **HATP DEPLOYMENT READY** — the Class-B boundary is provisioned, the
  agent environment is admin-locked (§14, §22), signer trust is
  provisioned, and a `VALID`, actively-bound HMIC certification exists —
  i.e., all seven readiness checks are `True` (§34 `READY`). This is a
  statement about HATP's own implementation/certification/binding
  correctness.
- **HATP ACTIVATED** — the admin principal has performed the `PREPARED →
  HATP_MANDATORY` transition (§29 is a prerequisite; the transition itself
  is a distinct, later, admin-invoked ceremony not designed by this phase
  in full, see §46–§48).
- **ROLLBACK EXECUTION CAPABLE** — a truthful `simulation_only=False`
  AG3/AG5 request resolves `ALLOW`. This additionally requires `COMP-002`
  to be implemented (§39) and is entirely independent of HATP's own
  readiness/activation state — HATP being deployment-ready and activated
  does not make the system rollback-execution-capable, and `COMP-002`
  being implemented would not, by itself, satisfy HATP's own readiness
  checks either. The two axes are orthogonal.

## 41. Operational Readiness Matrix

For each named combination, the maximum legitimate claim (`I`=implementation
verified, `C`=Class-B provisioned, `R`=runtime-source bound [i.e.
HMIC-REQ-063's accepted-branch prerequisite met], `S`=signer trust
provisioned, `Ci`=HMIC cert installed, `Ca`=HMIC cert active, `Rd`=readiness
true, `Cu`=cutover mandatory, `PB`=PB real-effect permission available,
`Rt`=runtime capability available):

| I | C | R | S | Ci | Ca | Rd | Cu | PB | Rt | Maximum legitimate claim |
|---|---|---|---|---|---|---|---|---|---|---|
| ✔ | ✘ | – | – | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | SYSTEM IMPLEMENTATION VERIFIED — DEPLOYMENT NOT READY (current real state, §42) |
| ✔ | ✔ | ✘ | – | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | CLASS-B PROVISIONED — DEPLOYMENT NOT READY (environment lock/executed-source prerequisite unmet, §14) |
| ✔ | ✔ | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | CLASS-B + ENVIRONMENT READY — SIGNER TRUST NOT PROVISIONED |
| ✔ | ✔ | ✔ | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | PREREQUISITES PROVISIONED — NOT CERTIFIED |
| ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | CERTIFIED_INACTIVE — NOT ACTIVE-BOUND |
| ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ | ✘ | ✘ | CERTIFIED_ACTIVE — OTHER READINESS TERMS UNSATISFIED |
| ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | – | – | HATP DEPLOYMENT READY — NOT ACTIVATED |
| ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | – | HATP ACTIVATED (HATP_MANDATORY) — ROLLBACK EXECUTION NOT CAPABLE (COMP-002 gap, §39) |
| ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | HATP ACTIVATED — PB REAL-EFFECT AVAILABLE — RUNTIME CAPABILITY STILL UNAVAILABLE |
| ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | FULLY OPERATIONAL — ROLLBACK EXECUTION CAPABLE (maximum achievable state under this architecture) |

Any row not listed (e.g. `Rd=✔` without `Ci`/`Ca=✔`) is structurally
unreachable given the readiness computation's own dependency on HMIC status
(§36) — the matrix reflects only reachable combinations under the frozen
contracts.

## 42. Current Real State (This Host)

Applying the matrix (§41) to this host, confirmed by direct read-only
inspection (§3) and by 149O.19.5F's independently reproduced seven-check
readiness result (§ baseline, §2):

```
I  (implementation verified):                    TRUE
C  (Class-B provisioned):                         FALSE (Protected Root absent)
R  (agent environment admin-locked):               N/A (no deployment exists to lock)
S  (signer trust provisioned):                     FALSE
Ci (HMIC cert installed):                          FALSE
Ca (HMIC cert active):                             FALSE
Rd (readiness true):                               FALSE
Cu (cutover mandatory):                            FALSE (LEGACY_COMPATIBLE, default)
PB (real-effect permission available):             FALSE (POL-005 DENY, COMP-002 not_implemented)
Rt (runtime capability available):                 FALSE (Observed / observe / unavailable)
```

**Maximum legitimate claim: SYSTEM IMPLEMENTATION VERIFIED — DEPLOYMENT NOT
READY.** This matches HATP-REQ-108's frozen status block exactly in spirit
(`HATP IMPLEMENTATION: NOT IMPLEMENTED` in that block predates the 149O.2–
149O.19.5G implementation chain; the implementation *has since been built
and independently verified* — this phase's own claim is the current,
accurate successor statement, not a contradiction of the older frozen
block, which described an earlier point in the roadmap). Not upgraded
beyond this by this phase.

## 43. Provisioning Plan Boundary

This architecture phase does not provision anything. §29 (certification
bootstrap sequence), §9 (root creation requirement), §27 (signer
provisioning), and §22 (agent environment lock) each name *what* a future
provisioning phase must do and in what order; none of them are executed
here. No `mkdir`, `chown`, `chmod`, `useradd`, credential registration, or
certification-ceremony invocation occurs in this phase (confirmed, §87–§95).

## 44. Possible Future Phases

Derived from this architecture's own selected disposition (§14 OPTION C),
not the illustrative example in the governing prompt, reconciled against
the actual prerequisite ordering this phase determined (§29):

- **149O.20B — Class-B Deployment Contract Freeze.** Freezes, as a bound
  contract, the exact OS-principal separation, Protected Root directory
  ownership/permissions, and (new, this phase's addition) the agent-
  environment-lock requirement (§22) as concrete, testable normative
  requirements — the contract-level counterpart to this architecture
  document, analogous to how 149O.1B.1 (architecture) preceded 149O.1B/
  1B.3 (contract freeze) for HATP-001 itself.
- **149O.20C — Independent Deployment Contract Verification.** Independent
  review of 149O.20B's contract text against this architecture, mirroring
  the HATP-001/HMIC-001 contract-then-independent-verification pattern
  already used repeatedly in this chapter.
- **149O.20D — Class-B Provisioning Implementation Plan.** A concrete,
  reviewed plan (commands, scripts, or manual runbook) for creating the
  Protected Root, the two OS principals, and the agent-environment lock —
  still not executing it.
- **149O.20E — Isolated Provisioning Implementation / Verification (test
  environment only, not this production host)** — proves the plan works
  in a disposable/sandboxed environment before any real-host provisioning
  is authorized.
- **149O.20F — Independent Provisioning Verification.**
- **149O.20G — Real Deployment Readiness Assessment** — a real-host
  readiness check (still not activation) once provisioning has actually
  occurred on a real target host, gated by its own separate authorization
  (§45).

Because this phase's selected HMIC-REQ-063 disposition (OPTION C) does not
require a full executed-source-binding *implementation* before initial
deployment (only an environmental lock, §22), no separate blocking
HMIC-REQ-063 implementation/contract/verification chain is inserted ahead
of 149O.20B–G, unlike the governing prompt's conditional instruction for a
BLOCKING disposition. This sequence is not a commitment; a later phase may
revise it if 149O.20B's contract-freeze work surfaces new prerequisites.

## 45. Real Deployment Authorization Gate

Architecture completion does not equal permission to provision a real
host. Frozen rule, this phase: any real `useradd`/`dscl`/equivalent OS
principal creation, any real protected-directory creation, any real
`chown`/`chmod`/ACL configuration, any real hardware-credential
registration, any real HMIC certification creation, or any real activation
requires a later, separately authorized governed phase (149O.20D onward,
§44) with its own independent review. This document, by itself, authorizes
none of it.

## 46. Real Activation Authorization Gate

Even after real provisioning occurs (a future phase, §44), real
`HATP_MANDATORY` activation requires a distinct governed phase, separate
from the provisioning phase. A provisioning phase MUST NOT activate
implicitly as a side effect of provisioning — activation is always its own
explicit, deliberate, admin-invoked ceremony (§37, §47–§48).

## 47. First Certification Authorization Gate

**Determination: yes, the first real HMIC certification requires its own
distinct phase, separate from provisioning.** Rationale: certification
creates protected authority state (a `CertificationRecord`) that did not
exist before, is not idempotent to re-derive without full re-verification
(§30), and — per this architecture's own bootstrap sequence (§29 steps 6–8)
— depends on an independent-implementation-verification step that is
itself a governance artifact deserving its own review, not a side effect
folded into a provisioning phase's file-system setup work.

## 48. First Active-Binding Gate

**Determination: certify and activate-the-binding are the same operational
ceremony's two sub-steps (§29 steps 8–9), performed together by the admin
principal in one certification session, but they remain logically and
mechanically distinct writes** (`certifications.json` append, then
`certification-bindings.json` pointer write) per HMIC-001 §35's own
"separate, non-causal ceremonies" framing. This phase does not require them
to occur in physically separate governed phases (unlike §47's certify-vs-
provision separation) because HMIC-001 itself already treats them as two
steps of one admin ceremony rather than two independently authorizable
events — but any future provisioning/certification plan (149O.20D) must
still implement them as two distinct writes, never a single atomic
"certify-and-activate" operation, to preserve the ability to certify
without activating (e.g. for pre-certification review of a
`CertificationRecord` before binding it).

## 49. Cutover PREPARED State — Entry Timing

`PREPARED` should be entered only after: Class-B provisioning is complete
(§45 gate passed), HMIC certification is active-bound (§47–§48 gate
passed), and readiness (§34 `READY`, all seven checks `True`) is
independently confirmed. This is already the exact ordering HMRC-REQ-054
encodes as a conjunction — `PREPARED` cannot be entered before all seven
readiness checks are true, because `PREPARED`'s own precondition set is
that conjunction. This phase does not modify HMRC-001's transition
contract; it confirms this architecture's provisioning/certification
sequence (§29, §44) is consistent with, and does not attempt to bypass,
that existing precondition.

## 50. PREPARED Failure Recovery

If provisioning or certification is incomplete when `PREPARED` is
attempted, HMRC-001's own transition contract already fails closed: the
conjunction (HMRC-REQ-054) simply evaluates `False`, and no transition
occurs — there is no partial-`PREPARED` state and no ambiguous
intermediate. No new recovery mechanism is required or introduced by this
phase; "safe recovery" here means "the transition never happened," which
is the existing, already-frozen HMRC-001 behavior.

## 51. HATP_MANDATORY One-Way Property

Retained, unmodified. After real activation, certificate revocation or
readiness degradation must not silently downgrade cutover state — HMRC-001's
write-once monotonic marker (HMRC-REQ-049) already enforces this: if the
Cutover Record ever goes missing/corrupt after having once activated, the
system fails closed to `HATP_MANDATORY`-equivalent, never silently
downgrading. This phase does not weaken or reinterpret that property.

## 52. Post-Activation Cert Revocation

Operator response, frozen this phase (derived from §51's one-way property
plus §36's "active certification ≠ full readiness"): if the active HMIC
certification is revoked after `HATP_MANDATORY` activation, `CutoverMode`
remains `HATP_MANDATORY` (§51 — no automatic downgrade), but the
`mandatory_consumption_implementation_independently_verified` readiness
term now evaluates `False` (HMIC status `REVOKED`), so overall readiness
becomes `False` even though the mode string still reads `HATP_MANDATORY`.
Practical consequence: any consumer that gates real effects on both
`CutoverMode == HATP_MANDATORY` AND fresh readiness (the lock-held recheck
discipline, §53 below / 149O.19.5G's `toctou_lock_held_recheck` finding)
correctly fails closed even though the mode itself did not change. Required
operator response: repair (re-provision whatever caused revocation) and
re-certify (§29 steps 6–9 again) — never a downgrade to `LEGACY_COMPATIBLE`
or `PREPARED`, which no code path performs automatically and which this
architecture does not authorize as a manual admin action either (no
reverse-transition edge exists in HMRC-001's transition graph, HMRC-REQ-
038/039).

## 53. Lost Hardware Credential

Recovery governance, frozen this phase: loss of the admin's hardware
signing device requires a separately authorized replacement-signer
ceremony — the admin principal (still holding OS-level Protected Root
write access, which is independent of the hardware device) enrolls a new
device via the same signer-bootstrap path (§28), and the old device's
credential entry is marked revoked in the hardware-credential registry
(§27). No insecure bypass signer is introduced; if the admin principal
itself cannot authenticate to perform this ceremony (e.g. also lost OS
credentials), this collapses into §54 (admin principal loss).

## 54. Admin Principal Loss

Recovery assumptions, frozen this phase: no agent self-escalation path
exists or is introduced (§7 — the agent has zero write path to any
protected state, and this architecture adds none). Recovery from complete
loss of the admin OS principal's own credentials is an OS-account-recovery
problem outside HATP's own trust model — identical in kind to losing root/
Administrator credentials on any system, and governed by whatever OS-level
account-recovery process the host's platform/organization already uses,
not by any PCAE-specific mechanism. This architecture does not invent a
PCAE-level "admin recovery key" or equivalent, since doing so would itself
create a new, un-analyzed authority-bearing artifact.

## 55. Protected State Backup

**Determination: yes, protected state MAY be backed up, admin-owned and
admin-restored only.** `certifications.json`, `certification-bindings.json`,
the Cutover Record, and the hardware-credential registry are all ordinary
files under the Protected Root — nothing prevents an admin-initiated
filesystem-level backup (the same backup discipline any admin-owned system
file would receive). Frozen requirements for a future implementation phase
to satisfy, not built here:

- **What parts:** all Protected Root content (certifications, bindings,
  Cutover Record, hardware-credential registry) — a partial backup that
  omits the Cutover Record while restoring certifications risks exactly
  the "missing/corrupt Cutover Record after prior activation" case §51's
  fail-closed marker already defends against, so backups should be
  captured as a consistent set.
- **Encryption:** backup content includes no cryptographic secrets (the
  hardware key itself is non-exportable, per HATP Root 1 — it is never
  present in any file to back up); encryption-at-rest for the backup
  medium is a general operational-security recommendation, not a new
  HATP-specific requirement.
- **Owner:** admin principal exclusively — identical write-authority
  requirement to the live Protected Root itself (§8).
- **Restore authority:** admin principal exclusively.
- **Deployment binding implications:** restoring a backup to the *same*
  canonical deployment root (same physical path, §11–§12) is a same-
  deployment restore (no new certification required). Restoring to a
  *different* canonical deployment root is host migration (§56) — the
  restored `DeploymentBinding` records no longer match the new resolved
  path, and `WRONG_DEPLOYMENT` results until re-bound.

## 56. Host Migration

Moving a deployment to a new machine changes the canonical deployment root
(a new physical path resolves under `resolve_canonical_deployment_root`,
§11), which the existing `DeploymentBinding` and certification records do
not match. Frozen semantics, this phase: host migration is treated
identically to establishing a new deployment (§11's "copy repo → reuse
certification" prevention applies equally to "migrate repo → reuse
certification") — it requires a new `DeploymentBinding` (admin-written,
§10) and, because `implementation_scope_digest`/`contract_versions` may
also need re-verification of the migrated bytes' integrity even if
unchanged, a fresh certification ceremony (§29 steps 4–9) is required
before the migrated deployment can reach `READY`. No automatic
"re-certification carries over" path exists or is introduced.

## 57. Repository Clone / Restore

Identical analysis to §56: a clone or restore to a new physical path is a
new canonical deployment root, requiring new `DeploymentBinding` and
certification. A restore to the *original* physical path (disaster
recovery of the exact same deployment, §58) is the one case where the
existing binding/certification MAY still validate, since the canonical
deployment root is unchanged.

## 58. Disaster Recovery

Two cases, differentiated this phase:

- **Restoring the same deployment** (recovering the original host/path
  after e.g. a crash, using a backup restored to the identical canonical
  deployment root, §55) — existing `DeploymentBinding` and certification
  records remain valid if the restored source bytes are bit-identical to
  what was certified (§30's digest-based invalidation only triggers on an
  actual byte difference).
- **Creating a new deployment** (recovering by standing up a replacement
  host at a new physical path, or restoring to a different path) — treated
  as host migration (§56): new `DeploymentBinding`, new certification
  required.

## 59. Observability

Safe diagnostics for a future deployment, without exposing secrets:
Class-B provisioning status (Protected Root exists / permissions correct —
boolean/structural facts only, not directory contents), HMIC validation
status (the `CertificationStatus` enum value itself — already
disclosure-safe, since it names a status category, not certificate
contents), active certification ID (the `certification_id` field — an
identifier, not a secret, consistent with `repository_instance_id`'s own
"identifier ≠ authority" framing, §10), deployment identity
(`canonical_deployment_root` path — already logged/displayed elsewhere,
e.g. `pcae runtime inspect`-style commands), readiness failures (which of
the seven named checks is `False` — already the exact shape 149O.19.5F/
149O.19.5G's own read-only diagnostic output uses), cutover state (the
`CutoverMode` string). None of these expose hardware key material,
signature bytes, or admin OS credentials — none of which are ever stored
in a form a diagnostic command reads.

## 60. No Authority From Diagnostics

Diagnostics are disclosure only. Retained, unmodified: no code path may
derive a readiness/validity/activation *decision* from a diagnostic report
file's own content (a report is a rendering of a live computation's
output, never re-consulted as an input) — this mirrors HMIC-001's own
no-implicit-latest and no-caching disciplines (§19, §36) applied to
reporting surfaces specifically.

## 61. PROJECT_STATUS

`PROJECT_STATUS.md` remains the canonical project planning/status document.
It is NOT runtime authority — no code path reads it to make a readiness,
certification, or activation decision. This phase's own `PROJECT_STATUS.md`
update (§104) is a planning-document edit only.

## 62. Deployment Status Documentation

Canonical wording rule, frozen this phase: after any future deployment
step, `PROJECT_STATUS.md` and phase reports MUST use the exact label from
the operational readiness matrix (§41) that matches the real, independently
confirmed state at that point — never a claim one row higher than what has
actually been confirmed (e.g. never write "HATP DEPLOYMENT READY" after
only Class-B provisioning without also confirming certification is active-
bound and all seven readiness checks are true). This avoids the "accidental
ready claim" risk named in this phase's governing prompt §62.

## 63. HATP Production READY Definition

**Frozen, exact criteria:** HATP production MAY be stated as READY (using
the §41 matrix's "HATP DEPLOYMENT READY" row label) if and only if all of
the following are independently, freshly confirmed (not cached, not
inferred from a report file, §60):

1. Class-B is provisioned (distinct agent/admin OS principals; Protected
   Root exists, admin-owned, agent-read-only, §6/§9).
2. The agent's Python execution environment is admin-locked per §22 (no
   agent-writable `PYTHONPATH`/site-packages/import-hook channel) —
   satisfying HMIC-REQ-063's accepted-residual-limitation prerequisite
   (§14).
3. Hardware signer trust is provisioned (§27–§28).
4. HMIC certification is `VALID` and actively bound (§29 steps 8–9).
5. All seven implementation readiness checks (§34 `READY`) evaluate `True`,
   freshly computed at the moment of the claim.

If (2) is not satisfied, HATP MUST NOT be claimed READY even if (1)/(3)/
(4)/(5) all hold — per §14, the accepted-residual-limitation disposition
for HMIC-REQ-063 does not apply without the environment lock, and no
alternative disposition has been selected for an unlocked environment.

## 64. Rollback Operational READY Definition

**Frozen, exact criteria, separately from §63:** rollback is operational-
ready if and only if HATP production READY (§63) holds, **and**
`CutoverMode == HATP_MANDATORY` (real activation performed, §46), **and**
`COMP-002` is implemented such that a truthful `simulation_only=False`
AG3/AG5 request resolves `ALLOW` under POL-005 (§39). Per §40, this is an
orthogonal, additional axis — HATP production READY and even
`HATP_MANDATORY` activation do not by themselves satisfy this definition.

## 65. HMIC-REQ-063 Impact on "READY"

Per §14/§63: under this architecture's selected OPTION C disposition, HATP
MAY be stated production READY with the qualification "READY WITH DECLARED
EXECUTED-SOURCE PROVENANCE LIMITATION" only when the admin-locked-agent-
environment prerequisite (§22) is independently confirmed satisfied as part
of the READY determination (§63 item 2) — the qualification is not a
blanket allowance, it is conditional on that specific environmental control
being in place and confirmed, not merely asserted. If the environment lock
is not confirmed, HATP cannot be stated production READY at all until
either the lock is provisioned and confirmed, or a future phase implements
a full executed-source binding (§18) removing the need for the lock
prerequisite.

## 66. Security Ceiling

Maximum trust claim, frozen this phase: this architecture does not claim
tamper resistance against a compromised OS root (§17). Its maximum claim,
once fully deployed and activated per §63–§64, is: an agent OS principal
operating within its own OS-account privileges — without root/Administrator
escalation, without write access to the admin OS principal's files, and
(per §22) without write access to its own Python import search path —
cannot forge, redirect, or self-certify HATP authority state, cannot
fabricate a valid hardware-signed approval proof without the physical
device and a human's fresh presence, and cannot cause a real AG3/AG5 effect
to execute without both a valid HATP-consumption path (§64) and (until
`COMP-002` exists) any real effect at all. This ceiling does not extend to:
root/Administrator-level compromise (§17), admin-principal compromise (§16
item 3, out of scope), or an agent that has already escalated into
site-packages/`PYTHONPATH` write access on a deployment that failed to
satisfy §22's lock (§14's BLOCKING branch for that configuration).

## 67. Class-B Verification (Future Phase Scope)

A future independent phase must verify, on a real provisioned host (not
performed here): the agent OS principal cannot write to the Protected
Root (negative test); the admin OS principal can write to it (positive
test); symlink/path protections work as analyzed in §12 (a symlink into
the Protected Root from an agent-writable location does not itself grant
write access, since permissions are enforced on the real target, not the
symlink); ownership/mode values match whatever 149O.20B eventually freezes
normatively (§8 of this phase's governing prompt notes modes need not be
frozen numerically here — deferred to that future contract).

## 68. Real-Host Testing (Future Phase Scope)

Future provisioning verification needs actual OS-principal tests on a real
(not this production) host: negative write attempts from the agent
account, positive admin writes to an isolated/disposable provisioned path
— never using `sudo` shortcuts from the agent's own test-runner context
(consistent with 149O.1B.1's own admonition against conflating a test
runner's ambient privilege with the agent principal's actual, narrower
privilege). Not performed by this phase.

## 69. Hardware Verification (Future Phase Scope)

Future operational verification must prove: the registered key is genuinely
non-exportable (device-attested, not merely claimed), user-presence is
required per signing operation (not bypassable via a cached assertion),
the signer is the specific authorized one enrolled in §27–§28 (not an
arbitrary FIDO2 device), and revocation of a signer is honored by the
verification path. No hardware operation is performed by this phase.

## 70. First-End-to-End Ceremony (Design Only)

Design (not executed): admin certification (§29 steps 6–9) → active
binding (§29 step 9, already included above) → readiness confirmation
(§34 `READY`, all seven checks fresh) → `PREPARED` transition (§49) →
`HATP_MANDATORY` transition (§46, a separate governed phase's explicit
action). Each arrow is a distinct, admin-initiated step; none happens
implicitly as a side effect of the previous one.

## 71. Activation Dry Run

**Determination: yes**, a read-only readiness rehearsal is required before
real activation. This is not a new invention — it already exists as a
pattern: 149O.19.5F/149O.19.5G's own "fresh lock-held readiness recheck
independently exercised and preserved" is exactly this rehearsal,
performed read-only against the real host's actual (currently absent)
protected state. Frozen requirement for any future activation phase: the
lock-held recheck (§72's TOCTOU discipline) must be exercised and its
result independently confirmed immediately before the actual
`PREPARED → HATP_MANDATORY` write, not merely at some earlier point in the
same session.

## 72. Real Activation Change Window

If organizational governance requires a human maintenance window or change
approval for the real activation step, that is a distinct, additional
organizational-process requirement layered on top of — not a substitute
for — HMIC's own independent-verification certification. This architecture
does not conflate the two: HMIC certification answers "was the
implementation independently verified," a change window answers "did the
organization approve doing this now." Both may be required; neither
satisfies the other. This phase does not itself mandate a specific change-
window process (outside PCAE's own scope), only states that if one exists
organizationally, it composes with, rather than replaces, this
architecture's gates.

## 73. Authority Semantic Walls

All preserved, unmodified by this phase: confirmed ≠ authorized ≠
permitted ≠ capable ≠ executed; approval ≠ confirmation; certified ≠
active; active ≠ ready; ready ≠ activated; activated ≠ rollback execution
permitted; generated ≠ approved ≠ dispatched ≠ executed. This document's
own §34–§41 vocabulary (`DEPLOYED_UNCERTIFIED`/`CERTIFIED_INACTIVE`/
`CERTIFIED_ACTIVE`/`READY`/`HATP_MANDATORY`, and the four-term
`DEPLOYMENT READY`/`ACTIVATED`/`ROLLBACK EXECUTION CAPABLE` distinction)
is constructed specifically to keep each of these walls intact rather than
collapsing any pair.

## 74. No Prompt-Generation Scope Expansion

Prompt generation remains design/deferred, unrelated to this phase. This
architecture grants no agent invocation or execution authority; nothing in
§1–§73 touches prompt generation, prompt dispatch, or agent-invocation
capability.

## 75. Telegram

Outbound-only notification state is unrelated to deployment authority and
unaffected by this phase.

## 76. Runtime

No runtime capability change. Confirmed before and during this phase (§3):
Observed / observe / unavailable.

## 77. HMIC Stale v1.0 Text Debt

Retained as a non-blocking finding, not opportunistically repaired here:
HMIC-REQ-139/§42 and part of §46 of HMIC-001 still use stale v1.0 wording
(per prior-phase disclosure). This architecture phase does not touch
`docs/contracts/**` (§88) and therefore does not repair this debt; it is
noted here only for continuity, unchanged in status.

## 78. HMIC-REQ-063 Decision Record

- **Selected option:** OPTION C — BLOCKING ONLY FOR SOME DEPLOYMENT MODELS
  (§14).
- **Rejected alternatives:** OPTION A (unconditionally accepted residual)
  — rejected because it would permit a "READY" claim even on a deployment
  where the agent OS principal can freely shadow certified imports, which
  this architecture judges too weak given Class B's own threat model
  already assumes a potentially-malicious agent. OPTION B (unconditionally
  blocking, requiring a full executed-source-binding implementation before
  any deployment) — rejected because it would contradict HMIC-REQ-064's
  own acceptance of the editable-install topology as certifiable today,
  and would impose an implementation burden not justified once the
  narrower environmental control (§22 agent-environment lock) closes the
  practically reachable channel under Model A.
- **Threat model:** §16 (four classes); the environment-shadowing channel
  (class 2) is the one HMIC-REQ-063 names, and is closed by provisioning
  (§22), not by digest verification, under Model A.
- **Operational consequence:** §15 (certification still validates even
  under a successful shadowing attack; this is the confirmed, named gap).
- **Required next phases:** none are inserted as blocking prerequisites
  ahead of §44's sequence, because the accepted-residual branch's
  prerequisite (§22) is an environmental-provisioning requirement folded
  into 149O.20D (Class-B Provisioning Implementation Plan), not a new
  contract/implementation chain of its own. If a future phase instead
  wants full HMIC-REQ-063 closure (§18 candidates), that becomes its own
  scoped architecture/contract/implementation/verification chain,
  inserted before any Model B/C adoption (§13) or before any deployment
  that cannot satisfy §22's lock.

## 79. Class-B Architecture Decision Record

- **Principal topology:** two OS principals — agent, admin (§6), inherited
  unmodified from 149O.1B.1.
- **Protected root:** `HATPTrustStore.production().root`, fixed
  platform path, admin-owned, never created by PCAE code (§9).
- **Ownership:** admin OS principal owns the Protected Root and all
  content beneath it (certifications, bindings, Cutover Record, hardware-
  credential registry).
- **Writer/reader model:** admin read/write; agent read-only on Protected
  Root content; agent read/write on its own repository-local artifacts
  only (§7).
- **Provisioning responsibility:** admin principal, out-of-band from any
  PCAE agent invocation (§9, §45).
- **New requirement this phase adds to the Class-B topology:** the agent's
  Python execution environment (site-packages, `PYTHONPATH`, import hooks)
  MUST also be admin-provisioned and agent-unwritable (§22–§23) — this is
  a deployment-readiness-architecture addition to Class-B's scope,
  motivated directly by the HMIC-REQ-063 disposition (§14), not present in
  149O.1B.1's original architecture. It does not contradict 149O.1B.1;
  it extends the same OS-boundary principle (admin-owned, agent-read-only
  or agent-no-access) from the trust-store directory to the agent's own
  import search path.

## 80. Deployment Model Decision Record

Editable source install from the canonical repository working tree (Model
A) — selected, §13. Installed wheel (Model B), dedicated immutable
deployment tree (Model C), and any other model (Model D) are explicitly
not selected for the initial deployment; adopting any of them requires a
future, explicit contract revision per HMIC-REQ-064.

## 81. Certification Deployment Decision Record

- **When/by whom created:** admin principal, after Class-B provisioning,
  agent-environment lock, and signer-trust provisioning are all complete,
  and after independent implementation verification of the exact bytes to
  be certified (§29 steps 1–7).
- **When it becomes active:** immediately following certification creation
  within the same admin ceremony, via the explicit binding-pointer write
  (§29 step 9, §48).
- **When it must be refreshed:** on any change to a frozen file (§30), any
  bound-contract version change (§31), or any change to the admin/cutover
  scripts themselves (§32–§33) — always via full re-certification, never
  automatically.

## 82. Activation Decision Record

- **Preconditions:** all seven readiness checks `True` (§34 `READY`,
  §49).
- **Human/admin authority:** Protected Activation Authority (admin OS
  principal), exclusively (§8, HMRC-REQ-041).
- **Readiness check:** the seven-term conjunction (§34, HMRC-REQ-054 +
  module-owned term).
- **Lock-held recheck:** required immediately before the actual write
  (§71), following the existing TOCTOU-safe pattern 149O.19.5F/149O.19.5G
  already implement and independently verified.
- **Real activation separation:** a distinct governed phase from
  provisioning (§46) and from first certification (§47).

## 83. PB/Capability Decision Record

Frozen, unmodified: HATP activation does not repair POL-005/COMP-002
(§39–§40). Any future implementation of `COMP-002` (making rollback
execution truthfully capable) is a separate future chapter/phase, entirely
outside this architecture's scope and outside HMIC-001/HMRC-001's own
scope (HMIC-REQ-125 — HMIC never amends, triggers, or interacts with
POL-005 or COMP-002).

## 84. Requirement Inventory

New deployment-readiness architecture namespace, this phase (does not
alter any HMIC/HMRC/HATP/HSCE/RAE/RWMPC/PBPA/PBPC requirement numbering):

- **DRA-REQ-001** — The agent principal and the admin principal SHALL be
  distinct OS accounts (§6).
- **DRA-REQ-002** — The Protected Root SHALL be created only by the admin
  principal, out-of-band from any PCAE agent invocation (§9).
- **DRA-REQ-003** — The agent OS principal's Python import search path
  (site-packages, `PYTHONPATH`, import hooks, `.pth` files) SHALL be
  admin-provisioned and agent-unwritable for any deployment claiming
  HMIC-REQ-063's accepted-residual-limitation disposition (§14, §22–§23).
- **DRA-REQ-004** — A deployment whose agent OS principal CAN write to its
  own Python import search path SHALL NOT be claimed HATP production READY
  under this architecture's OPTION C disposition (§14, §65).
- **DRA-REQ-005** — Any change to a frozen file, bound contract, or the
  admin/cutover scripts SHALL invalidate the existing certification and
  SHALL require full re-certification; no automatic recertification SHALL
  exist (§30–§33).
- **DRA-REQ-006** — A copy, clone, migration, or restore of the deployment
  to a new canonical deployment root SHALL require a new
  `DeploymentBinding` and a new certification; existing certification
  records SHALL NOT be reused across canonical deployment roots (§11,
  §56–§58).
- **DRA-REQ-007** — Post-activation certification revocation SHALL NOT
  cause an automatic `CutoverMode` downgrade; recovery SHALL be repair-and-
  recertify, never silent downgrade (§52).
- **DRA-REQ-008** — First real HMIC certification SHALL require its own
  governed phase, distinct from any provisioning phase (§47).
- **DRA-REQ-009** — Real `HATP_MANDATORY` activation SHALL require its own
  governed phase, distinct from provisioning and from first certification
  (§46).
- **DRA-REQ-010** — A read-only, lock-held readiness rehearsal SHALL be
  performed immediately before any real activation write (§71).
- **DRA-REQ-011** — Deployment-readiness status claims in
  `PROJECT_STATUS.md`/phase reports SHALL use only the exact matrix row
  (§41) matching independently, freshly confirmed state — never a claim
  one row higher than confirmed (§62).

## 85. Attack Matrix (Deployment-Specific)

| # | Attack | Disposition |
|---|---|---|
| 1 | Agent writes protected root | Prevented — no OS write permission (§7, §9) |
| 2 | Agent redirects root (env var/CLI override) | Prevented — no override parameter exists on `HATPTrustStore.production()` (confirmed by source inspection, §7 of research) |
| 3 | Agent edits source after certification | Detected — `IMPLEMENTATION_MISMATCH` on next validation (§30) |
| 4 | Runtime imports different source (shadowing) | Named residual limitation under HMIC-REQ-063; closed operationally by agent-environment lock (§14, §22), not by the digest itself |
| 5 | Admin script modified | Detected — admin script is a frozen file; `IMPLEMENTATION_MISMATCH` (§32) |
| 6 | Wrong repo/deployment cert reuse | Prevented — `WRONG_REPOSITORY`/`WRONG_DEPLOYMENT` via `DeploymentBinding` match (§11) |
| 7 | Old certification after source update | Prevented — digest recomputed fresh every time; stale cert mismatches (§30, historical_replay_rejected) |
| 8 | Protected root symlink | Neutral/prevented if the symlink resolves to the same admin-owned physical directory (§12); a symlink redirecting to an agent-writable location would itself require agent write access to the Protected Root's parent directory to create, which DRA-REQ-001/002 already prevent |
| 9 | Host migration (cert reuse across hosts) | Prevented — new canonical deployment root requires new binding + certification (§56) |
| 10 | Backup restore (cert reuse across paths) | Prevented if restored to a different path (§55, §58); valid if restored to the identical original path with bit-identical bytes |
| 11 | Lost signer (no valid device) | Governed recovery path — replacement-signer ceremony (§53), no bypass signer |
| 12 | Revoked signer still accepted | Prevented — hardware-credential registry revocation is admin-only and consulted at verification time (§27–§28); not implemented by this phase, but the write-authority model prevents an agent from un-revoking |
| 13 | Cert revoked after HATP_MANDATORY | Handled — readiness degrades honestly, `CutoverMode` does not silently downgrade (§51–§52) |
| 14 | PB remains DENY despite HATP_MANDATORY | Expected, documented, not a defect (§39, HMRC-REQ-037) |
| 15 | Runtime unavailable | Expected, unchanged — Observed/observe/unavailable (§76) |

## 86. Stop Conditions

None of the following triggered during this phase; each is evaluated
against this architecture's own findings:

- **DRA-S1** — cannot establish agent/admin OS-principal separation: NOT
  TRIGGERED. §6 confirms the separation is already architecturally defined
  (149O.1B.1) and this phase adds no contradiction.
- **DRA-S2** — protected root can be redirected by agent: NOT TRIGGERED.
  §7/§85 attack #2 confirms no override path exists in production source.
- **DRA-S3** — executed-source provenance required but no trustworthy
  design selected: NOT TRIGGERED. §14 selects OPTION C with a concrete,
  trustworthy environmental-lock mitigation (§22) for the deployment model
  actually selected (§13); a full executed-source-binding design is
  identified (§18) but is not required to be selected under OPTION C.
- **DRA-S4** — production deployment model cannot connect certified source
  to executing code: NOT TRIGGERED. §13/§25 confirm Model A's editable
  install connects them directly (absent the shadowing channel §14
  addresses via provisioning).
- **DRA-S5** — real provisioning would require agent-controlled authority
  input: NOT TRIGGERED. §9/§29 confirm every provisioning/certification
  step requires admin OS credentials; the agent supplies no authority-
  bearing input to any of them.
- **DRA-S6** — certification ceremony cannot operate without self-
  certification: NOT TRIGGERED. §19/§29 confirm the ceremony always
  recomputes fresh from live bytes; HMIC-001 §50's non-circularity
  reasoning already covers this and this phase does not weaken it.
- **DRA-S7** — activation can occur without fresh protected readiness:
  NOT TRIGGERED. §71/§82 require a lock-held fresh recheck immediately
  before any real activation write.
- **DRA-S8** — Class-B recovery introduces downgrade/bypass: NOT
  TRIGGERED. §52–§54 confirm all recovery paths are repair-and-recertify
  or OS-level account recovery, never a HATP-specific downgrade/bypass
  mechanism.
- **DRA-S9** — PB/COMP-002 is incorrectly conflated with HATP deployment
  readiness: NOT TRIGGERED. §40/§64/§83 keep them explicitly orthogonal
  throughout.

No stop condition blocks this architecture. Verdict: COMPLETE (§101).

## 87. No Production Change

Zero `src/pcae/**` changes, zero `scripts/**` changes — confirmed (§97,
§104).

## 88. No Contract Change

Zero changes to all eight bound contracts — confirmed (§97, §104). If this
architecture discovers a contract defect, it is documented and recommended
for later repair, not repaired now: none was discovered (this phase found
existing contracts sufficient to reason from; no defect is reported).

## 89. No Real Protected State

No protected root, certification, binding, revocation, Cutover Record, or
activation marker was created — confirmed (§97, §104).

## 90. No Real OS Change

No `useradd`, `dscl`, `chmod`, `chown`, sudoers, ACL, group creation, or
service install was performed — confirmed (§97, §104).

## 91. No Hardware Change

No credential registration or device mutation was performed.

## 92. No PB Change

None.

## 93. No POL-005 Change

None.

## 94. No COMP-002

None implemented.

## 95. No Runtime Change

None. `pcae runtime inspect`: Observed / observe / unavailable, unchanged
(§3, §76).

## 96. Architecture-Completeness Test

`tests/test_phase_149o_20a_hatp_deployment_readiness_architecture.py`
mechanically verifies: this document exists; every section required by
this phase's governing prompt is present (by heading text); the
HMIC-REQ-063 Decision Record (§78), the Class-B Architecture Decision
Record (§79), and the Deployment Model Decision Record (§80) are present
and non-empty; all nine stop conditions (§86) are enumerated and each
explicitly marked "NOT TRIGGERED"; the eleven future-phase candidates
(§44) are named; the eight production-boundary confirmations (§87–§95) are
present; and — as read-only evidence gathering, not a production-behavior
test — that no `src/pcae/**` or `docs/contracts/**` file differs from this
phase's pre-phase `HEAD` (mirroring 149O.14's own convention).

## 97. Existing Regression

```
pytest -k "hmic or hatp_mandatory or 149o_19" -n auto -q
```

Raw result (HEAD, this phase): 7 failed, 1222 passed, 105 warnings. A/B
confirmed via a detached `git worktree` at the pre-phase commit
(`a6c3b1e3`, HEAD prior to this phase's own two commits): the *identical*
7 node IDs fail at the pre-phase commit as well (7 failed, 1219 passed) --
byte-for-byte the same failing test names on both sides, confirming all
seven are pre-existing and unrelated to this phase's doc/test-only
change. The pass-count delta (1222 vs. 1219) is explained by this phase's
own 3 new fast_green-marked tests that also match the `-k` filter's
substring (none of the 7 failures are in the new test file). Failures are
date-drift (`test_accept_strict_timestamp` uses a fixed 2026-08-08
timestamp, now stale) and stale baseline-fact assertions from superseded
architecture phases (e.g. `test_no_hatp_mandatory_cutover_module_exists_yet`
asserts a module that has since been built) -- not attributable to this
phase.

## 98. Fast Green

```
pytest -m fast_green -q          (serial, deterministic)
```

Raw run (HEAD, this phase): 20 failed, 6336 passed, 1 skipped, 25639
deselected. A/B confirmed via the same detached pre-phase-commit worktree,
serial run: 21 failed, 6318 passed, 1 skipped -- the *same* 20 node IDs
fail at the pre-phase commit as at HEAD (one additional baseline-only
node, `test_shell_gate.py::TestAuditPersistence::test_verify_detects_
tampered_record`, is itself flaky across runs -- it failed on the baseline
run and passed on the HEAD run, not the reverse -- confirming it is not a
regression introduced by this phase either). The 18-test pass-count delta
(6336 vs. 6318) is exactly this phase's own 17 new architecture-
completeness tests plus the one flaked-to-pass shell_gate node.

Clean deselected run (all 20 confirmed pre-existing node IDs, plus the
one additional flaky `test_shell_gate.py` node, explicitly deselected):
**0 failed, 6335 passed, 1 skipped, 25639 deselected.**

## 99. Report Trust

Canonical report-trust run via `pcae phase-report reconcile --phase-id
149O.20A` as part of phase completion (§104).

## 100. Governance Close Checks

`pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor
task-memory`, `pcae push check`, `pcae runtime inspect`, `pcae notify
status` — run as part of phase completion (§104); results in the canonical
phase report.

## 101. Architecture Verdict

**HATP DEPLOYMENT READINESS ARCHITECTURE: COMPLETE — IMPLEMENTATION
VERIFIED — REAL DEPLOYMENT NOT AUTHORIZED — REAL ACTIVATION NOT
AUTHORIZED.**

- **HMIC-REQ-063:** OPTION C — BLOCKING ONLY FOR SOME DEPLOYMENT MODELS
  (accepted-residual-limitation for Model A under an admin-locked agent
  environment; blocking for any deployment where the agent OS principal
  can write to its own Python import search path).
- **CLASS-B:** two-OS-principal topology (agent, admin), fixed
  platform-level Protected Root, admin-owned/agent-read-only, inherited
  from 149O.1B.1, extended this phase to additionally require an
  admin-locked agent Python execution environment (DRA-REQ-003).
- **CURRENT HATP:** NOT READY (§42, matrix row: SYSTEM IMPLEMENTATION
  VERIFIED — DEPLOYMENT NOT READY).

## 102. Strategic Next Phase

Per §44/§78: no blocking architecture gap was found (§86, all nine stop
conditions NOT TRIGGERED), so the next prerequisite is the Class-B
deployment contract freeze, not real provisioning and not real activation:

**Recommended next phase: 149O.20B — HATP Class-B Deployment Contract
Freeze** — freezing, as a bound contract, the OS-principal separation,
Protected Root ownership/permissions, and the agent-environment-lock
requirement (DRA-REQ-001 through DRA-REQ-003) this architecture names, as
concrete, testable normative requirements. Real Class-B provisioning and
real activation remain out of scope until 149O.20B (and its own
independent verification, 149O.20C) exist and are independently reviewed
(§45–§46).

## 103. No-Go Confirmations

No `src/pcae/**` file was modified this phase. No `scripts/**` file was
modified this phase. No contract file was modified — HATP-001, HMRC-001,
HMIC-001 v1.1, HSCE-001, RAE-001, RWMPC-001, PBPA-001, and PBPC-001 all
confirmed byte-unchanged at exit. No real protected root, certification,
active binding, revocation, Cutover Record, or activation marker was
created anywhere on this real host. No real HATP_MANDATORY activation
occurred. No real Class-B provisioning occurred (no OS principal created,
no directory ownership/ACL changed). No Permission Broker behavior
changed. No POL-005 change was made. No COMP-002 capability was
implemented. No hardware credential/device state was changed. No
governance bypass, `--no-verify` flag, or force push was used this phase.
149O.19.5G completed the assembled implementation/hardening path; no
Blocking assembled HMIC finding remains from that phase. W-1 remains
independently closed only at the contract + implementation-identity
boundary — not reopened, not upgraded. Runtime/executed-source provenance
was explicitly dispositioned this phase (§14, OPTION C) — not silently
left unresolved, and not silently resolved beyond what OPTION C actually
grants. B-149O-1..4 remain independently closed only at the system
implementation/enforcement boundary with deployment/operational activation
deferred — not upgraded to deployment closure by this phase. HATP
production remains NOT READY. Runtime remains Observed / observe /
unavailable.

## 104. Recommended Next Phase (Restated)

149O.20B — HATP Class-B Deployment Contract Freeze (§102).
