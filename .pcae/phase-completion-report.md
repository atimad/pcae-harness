# Phase 149O.20L.7O.2N.3 Completion Report

**Verdict:** REPAIRED FIDO2 ADMIN SOURCE DEPLOYED TO HAC-DELL — HMIC
v1.7/38 SOURCE PARITY RESTORED — DECLARED HATP-HARDWARE PYTHON
ENVIRONMENT REALIZED — OLD CERTIFICATION NOW NON-VALID FOR REPAIRED
SOURCE — FRESH CERTIFICATION REQUIRED — NO REAL FIDO2 HARDWARE EFFECT.
See docs/PHASE_149O_20L_7O_2N_3_HAC_DELL_REPAIRED_FIDO2_ADMIN_
REDEPLOYMENT_AND_HATP_HARDWARE_RUNTIME_DEPENDENCY_REALIZATION.md for
the full phase report.

Real-effect governed deployment/environment transition. Obtained a
fresh CHGR (`chgr-e0dfb3e752e6430089ca1ee02636ec7e`, via `pcae
decision-session` create/evidence/select/preview/human-CONFIRM/
readiness/publish, template `class-b-boundary-p-provisioning-
authorization`) bundling two authorized real-effect actions under one
tightly-scoped election: (a) the exact frozen source-checkout
transition mechanism already proven by 149O.20L.7M/7N.4/7N.5/2K.2/2M.2,
redeploying `/opt/pcae/runtime/src` on hac-dell from `4efcb255` to
`cdb77b75` (fetch by exact SHA, `cat-file -t` commit check, `checkout
--detach`, `chown -R root:pcae`, exec-bit-derived mode normalization —
zero of 4498 tracked-path mode mismatches on read-back; live HMIC
re-derivation on Dell matches the Mac target exactly: v1.7/38, digest
`abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4`, 7
contracts); and (b) realizing the already-declared `hatp-hardware`
project extra (`fido2>=1.1,<2`, `cryptography>=42,<45`) into the
canonical `/opt/pcae/runtime/venv` — the first prior redeployment in
this lineage to require a venv change, since none of 7N/2K/2M ever
touched `pyproject.toml`. Dependency resolution was frozen before
mutation (`pip install --dry-run`): exactly `cryptography-44.0.3`,
`fido2-1.2.0`, plus transitive `cffi`/`pycparser` — no OS-level (apt/
udev/kernel/group) dependency triggered, confirmed from `fido2`'s own
wheel metadata before installing.

One incidental defect was introduced and self-caught mid-phase: the
default `pip install ".[hatp-hardware]"` build replaced the venv's
existing editable/path-bound `pcae-harness` install with a built-wheel
copy — a violation of this lineage's standing "path-bound not
byte-bound" invariant, caught immediately via `pip show` and repaired
in the same phase via `pip install --no-deps -e /opt/pcae/runtime/src`,
confirmed restored both by `pip show` and by the Class-B
`HBDC-REQ-022`/`HBDC-REQ-035` checks passing post-repair.

Post-deployment: `import fido2`/`import cryptography` succeed at the
declared versions; the FIDO2 provider module
(`pcae.core.hatp_fido2_provider`) imports cleanly with zero device
enumeration or hardware touch of any kind; the existing active
CertificationRecord/binding are byte-unchanged and, as expected, now
validate `IMPLEMENTATION_MISMATCH` (not `VALID`) against the repaired
source — HMIC readiness derives to `FALSE`. Class-B canonical
diagnostic: `NON_COMPLIANT`, sole failing check `HBDC-REQ-042` (no
active `DeploymentBinding`) — the exact expected pre-first-use residual.
No CertificationRecord created/activated/revoked, no RepositoryIdentity/
DeploymentBinding/Principal/Signer/HardwareCredentialRecord created, no
Protected Root mutation, no HATP activation, no real hardware touch of
any kind, no OS-level mutation.

Fast Green: two independent full local `pytest -m fast_green` runs
(before and after this phase's own new test file was added) show an
identical 337 failed / 9 errors — a direct, controlled proof of zero
attributable regression, since the only variable between the two runs
was the presence of this phase's own purely-additive files. Consistent
with the same large pre-existing environment-level baseline
149O.20L.7O.2N.2 already documented (334 failed there). This phase's
own 28 new independent tests are fully green.

Recommends **149O.20L.7O.2N.4 (or equivalent)** — a fresh, create-only
HMIC CertificationRecord for the newly-deployed repaired v1.7/38
identity, leaving activation to a further separate phase. Do not
create/activate any certification, attach/use real FIDO2 hardware, or
begin real enrollment as part of that phase — those remain separate,
later steps.
