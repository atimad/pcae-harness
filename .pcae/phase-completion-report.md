# PCAE Phase Completion Report

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R`
- Status: **COMPLETE — PPA REGISTRATION TRANSACTION: COMPLETE**
- F-5: **DEPLOYED / IV PENDING**
- N-16-5: **NOT CLOSED**

Executed exactly one canonical PPA `install` configuration transaction
(`scripts/hpac_protected_presentation_admin.py install`) against the
existing, previously-verified generation-1 protected root, via `sudo` in
the operator's own terminal (password never seen, echoed, or logged by
this session).

Two non-blocking environmental obstacles were hit, root-caused without a
blind retry, and cleared — neither required any `src/pcae` change:

1. First attempt failed closed with `acl_inspection_unavailable` because
   the operator's interactive-shell `PATH` has uid-501(configured-agent)
   -writable directories preceding `/usr/bin`/`/bin` — the ACL-tool-trust
   guard working exactly as designed. Confirmed read-only by reproducing
   the same resolver call with the real vs. a sanitized PATH.
2. Second attempt, retried with a sanitized PATH, failed with
   `ModuleNotFoundError` because that PATH resolved `python3` to Apple's
   system interpreter, which lacks this repo's editable-install
   `sys.path` entry. Confirmed read-only.
3. Third attempt (sanitized PATH for the internal `ls`/`getfacl` trust
   check, combined with an explicit full path to the Homebrew
   interpreter for module resolution) **succeeded**.

**PPA REGISTRATION TRANSACTION: COMPLETE.**
`install ok: mechanism=pcae-protected-local-presentation
installation_id=hppi-648bee5e950b4f5e971a6c65c8cc53cf generation=1
descriptor_digest=c4e9a04d8d4af865372d78db280b8a2ba40f7ad29414b365acf87b775b13fc6e`

**UNAUTHORIZED MUTATING HOST COMMANDS: 0.**

**WRITE SET CONFINED.** Exactly the three authorized files under
`presentation-mechanisms/v2/pcae-protected-local-presentation/`:
`descriptor.json`, `installations/1/installation.json`,
`current-generation.json`. No unexpected durable artifact.

**DIGEST SELF-CONSISTENCY: VERIFIED.** `installation_digest` and
`anchor_digest` both independently recompute (self-excluding canonical
digest) to the stored values; `descriptor_digest` agrees across all
three records; `installation_digest` agrees between `installation.json`
and `current-generation.json` (currentness binding correct).

**GENERATION-1 HELPER AFTER REGISTRATION: UNCHANGED VERIFIED.** Re-hashed
after registration: still `933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182`,
byte-identical to the immutable generation-1 source.

**PROTECTED-ROOT / PAWA GENERATION: PRESERVED.** Root and full ancestor
chain re-`stat`'d directly: `uid=0`, modes `0700`/`0755` throughout; the
configured agent (uid 501) has zero write access anywhere in the chain.
PAWA anchor unchanged (generation 1, `installation_id=hpawi-bfc91d...0eb`,
agent-exclusion ACTIVE).

**PAWA DEPLOYMENT CAPABILITY: CONSUMED**, inside the single bounded
`configure_presentation_mechanism` multi-write. One ad hoc post-registration
diagnostic exception was hit and fully root-caused to the diagnostic
script's own use of an unbound `HPACStoreAuthority.production()` (falls
back to the live process identity — root under sudo — when the PAWA
writer factory has not bound the configured-agent identity); the raw
`stat`-based readback above independently confirms no real topology
defect.

**BOUNDED REGRESSION: 468 passed, 5 pre-existing failed** (all confirmed
unattributable — `git diff --name-only` for `src/pcae`/`scripts`/
`pyproject.toml` since phase entry is empty).

No production/existing-test/contract/dependency modification. No
protected-root provisioning rerun, helper reinstall, or generation
reset. No protected human election, YubiKey/FIDO2 interaction,
presentation evidence, PRODUCTION principal, or Gate 5 certification.
Runtime remains `not_implemented` / `Observed` / `observe` /
`unavailable`, 0 plugins/capabilities.

**F-5 PROTECTED-PRESENTATION REGISTRATION: COMPLETE — DEPLOYMENT-STATE IV
PENDING.** **F-5: DEPLOYED / IV PENDING.** **N-16-5 remains NOT CLOSED**
(registration is not deployment-state IV and is not the final
human/YubiKey certification); N-16-6/N-16-7 untouched.

**Next recommended (not begun):** Independent Verification of Production
Protected-Presentation Generation-1 Deployment State — fresh,
independent re-verification of root/anchor/generation, helper
bytes/provenance, PPA descriptors, currentness, revocation, capability
provenance/consumption, authority separation, and runtime unavailability.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved.
