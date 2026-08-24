# Phase 149O.20L.7O.2V.1 Complete — v0.3.0 Final Release Preparation and Publication

**Verdict: completed — v0.3.0 PUBLISHED.**
`v0.3.0` final release blockers: **0**. No `src/pcae/**` file touched
this phase (`git diff 028cd254..HEAD -- src/pcae scripts` is empty).

Finalized stable version framing (CHANGELOG.md, README.md, new
`docs/RELEASE_NOTES_V0_3_0.md`); `pyproject.toml`/`src/pcae/__init__.py`
already carried stable `0.3.0` metadata. Built clean wheel + sdist from
a detached-HEAD `git worktree`: SHA-256 `4fb566da3b55fda8f6cee48f06b5e59bd96c180d1b9cebabb9a3252a599376d0`
(wheel), `1e56b64cb2c89a4539430c0f7d5e7d2c642d14a1255b7427bbbc97ad98ce0846`
(sdist). Clean-venv wheel install verified (`0.3.0`); ran the full
ALLOW→review→promote chain, DENY rejection, Claude reference adapter,
a hand-built generic-producer JSON candidate, and the entire
`docs/QUICKSTART_V0_3.md` walkthrough end-to-end against that clean
install — all PASS, zero mocks.

Structured Fast Green attribution (`pcae phase fast-green-attribution`,
isolated baseline-vs-candidate worktree method): **PASS**, 0
attributable failures — 338 raw failed + 9 raw errors, all 347
classified `excluded_preexisting_failures` against baseline
`3a77647e0b71e7014215bc0d05604d1c72a864db`.

Feature delta from `v0.3.0-rc1`: **NONE.**

Human explicitly approved publication of the `v0.3.0` Git tag and
GitHub Release at commit `738a81553128665a9c206f3ce33c931dc9089a6c`
(`FINAL_STABLE_CANDIDATE_SHA`). **Publication is now complete:**

- Tag `v0.3.0` created (annotated) at `738a81553128665a9c206f3ce33c931dc9089a6c`
  and pushed to origin; local tag SHA == remote tag SHA ==
  `738a81553128665a9c206f3ce33c931dc9089a6c` (verified).
- GitHub Release `v0.3.0` published at
  https://github.com/atimad/pcae-harness/releases/tag/v0.3.0 —
  `isDraft: false`, `isPrerelease: false`, release list shows
  **Latest**. Body is the reviewed `docs/RELEASE_NOTES_V0_3_0.md`.
  Attached the exact reviewed wheel + sdist (not rebuilt); downloaded
  digests match the reviewed checksums.
- Post-publication install smoke: downloaded the public release wheel
  via `gh release download`, installed into a fresh venv — version
  `0.3.0`, `pcae intake --help` present and functional. **PASS.**

Push: pushed (`origin/main == HEAD`, `origin/main..HEAD` count 0).
Full text: `docs/PHASE_149O_20L_7O_2V_1_V0_3_0_FINAL_RELEASE_PREPARATION.md`.

Recommended next phase: 149O.20L.7O.2V.2 — v0.3.0 Release Article Draft
and Editorial Review Preparation (local-only, non-publishing).
