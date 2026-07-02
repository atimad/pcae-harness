# Phase 106L — v0.1 RC GitHub Release Publication

## Purpose

Publish a GitHub Release for the already-created `v0.1.0-rc1` tag and
attach the verified Python release artifacts (sdist + wheel), so the
release candidate is discoverable and downloadable directly from GitHub
— without publishing to PyPI or GitHub Packages.

## Scope

Pre-publication gate verification, a clean rebuild of release artifacts
(sdist + wheel) from the current `main` state, a wheel smoke-install in a
throwaway virtual environment, creation of a GitHub Release attached to
the existing `v0.1.0-rc1` tag (marked prerelease) with the sdist/wheel as
release assets, documentation of this publication
(this document), and updates to existing release docs/records. New tests
(`tests/test_v0_1_rc_github_release_publication.py`). No product/runtime
behavior is implemented or changed in this phase.

## Non-Goals

No runtime enforcement; no autonomous execution; no real backend
invocation; no adapter execution; no subprocess/shell execution beyond
existing lifecycle/test/docs/build/release-publication command behavior;
no shell execution beyond that same boundary; no network calls outside
the existing Telegram outbound path, ordinary git remote verification,
and the explicit GitHub Release publication operation performed in this
phase; no shell interception; no Telegram inbound/polling; no remote
shell; no `/run`; no automatic apply/apply execution/patch parsing; no
commit/push authorization changes beyond the existing governed lifecycle;
no real AI backend calls; no executable artifact-only invocation path; no
execution enablement flag or toggle; no cryptographic signing beyond the
SHA256 checksums computed for the release artifacts below; no remote
attestation; no database-backed audit storage; no shell mediation; no
rollback execution, file mutation rollback, or automatic restore; no git
reset/checkout/revert execution. **No new git tag was created.** No final
`v0.1.0` tag was created. No PyPI publication. No GitHub Packages
publication. No v0.2 work started.

## Pre-Publication Gate Results

All gates verified before publishing the GitHub Release:

| Gate | Result |
|---|---|
| Working tree clean at start | clean |
| `origin/main..HEAD` = 0 at start | 0 |
| `v0.1.0-rc1` tag exists locally | yes |
| `v0.1.0-rc1` tag exists on origin | yes |
| Final `v0.1.0` tag exists | no |
| GitHub Release for `v0.1.0-rc1` exists before this phase | no (`gh release view v0.1.0-rc1` → "release not found") |
| `gh auth status` usable | yes (logged in as `atimad`, `repo` scope present) |
| `pcae health` | healthy (idle) |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean (nothing to push) |
| Latest phase report trust | complete (phase_id `106K`, `pcae phase-report trust --json` → `"complete": true`) |
| `fast_green` baseline | 4390/4390 fully green (confirmed unchanged from 106K) |

**All gates passed. GitHub Release publication is authorized.**

## Tag Verification

```
git tag --list                          -> v0.1.0-rc1 (only tag)
git ls-remote --tags origin              -> v0.1.0-rc1 present on origin
```

No new tag was created or pushed by this phase. `v0.1.0-rc1` is unchanged
from the tag recorded in `docs/RELEASE_HANDOFF_V0_1_RC1.md`.

## GitHub Release State Before Publication

`gh release view v0.1.0-rc1` returned "release not found" and `gh release
list` returned no releases — confirming no GitHub Release existed for
this tag (or any tag) before this phase. This is expected: prior phases
(106F–106K) created/pushed the tag and validated local build artifacts,
but did not create a GitHub Release or publish packages.

## Build Artifact Result

Rebuilt from a clean state (`rm -rf dist build *.egg-info`, then `python
-m build`, hatchling backend) at current `main` HEAD:

- **sdist:** `pcae_harness-0.1.0.tar.gz`
- **wheel:** `pcae_harness-0.1.0-py3-none-any.whl`
- **Build result:** succeeded — exactly one sdist and one wheel produced.

## Artifact SHA256 Checksums

| Artifact | SHA256 |
|---|---|
| `pcae_harness-0.1.0-py3-none-any.whl` | `6c0b896a945beb9b81d28a869dc3a7f3bbc51c8b26f4dc2d1d2a79543f6ccf7d` |
| `pcae_harness-0.1.0.tar.gz` | `f9b52572298b999d1e78a8b4725642bbbb441eb569f8a21c3c723c1c67ff994e` |

These checksums were computed locally before upload and independently
confirmed against the `digest` field reported by `gh release view
v0.1.0-rc1 --json assets` after upload — both match exactly.

## Smoke-Install Result

The built wheel was installed into a fresh, throwaway virtual environment
(outside the repository); `pip install` succeeded and `python -m pcae
--help` resolved without error. **Passed.**

## Release Title

`PCAE v0.1.0-rc1`

## Release Body Summary

The release body states: what this release is (a non-executing PCAE
lifecycle governance harness, first release candidate); a summary of
governed-lifecycle capabilities included; the non-execution boundary (no
autonomous execution, no shell mediation, no real AI backend invocation,
no Telegram inbound, no runtime enforcement — v0.2 is the future autonomy
target); the fast_green 4390/4390 validation summary; and installation
guidance pointing at the attached artifacts and repository documentation.
No overclaiming language was used.

## GitHub Release Publication Result

```
gh release create v0.1.0-rc1 dist/pcae_harness-0.1.0.tar.gz dist/pcae_harness-0.1.0-py3-none-any.whl \
  --title "PCAE v0.1.0-rc1" \
  --notes-file <release-notes-scratch-file> \
  --prerelease
```

- **Result:** created (no prior release existed for this tag, so `gh
  release create` was used rather than `gh release edit`).
- **Tag:** `v0.1.0-rc1` (existing tag; no new tag created).
- **Prerelease:** `true`.
- **Draft:** `false`.
- **URL:** `https://github.com/atimad/pcae-harness/releases/tag/v0.1.0-rc1`

## Attached Artifacts

Confirmed via `gh release view v0.1.0-rc1 --json tagName,name,isPrerelease,assets,url`:

| Asset | Size | SHA256 (from GitHub) |
|---|---|---|
| `pcae_harness-0.1.0-py3-none-any.whl` | 1,160,938 bytes | `sha256:6c0b896a945beb9b81d28a869dc3a7f3bbc51c8b26f4dc2d1d2a79543f6ccf7d` |
| `pcae_harness-0.1.0.tar.gz` | 1,105,768 bytes | `sha256:f9b52572298b999d1e78a8b4725642bbbb441eb569f8a21c3c723c1c67ff994e` |

Both assets uploaded with `state: uploaded`; digests match the
locally-computed checksums exactly. No unrelated artifacts were uploaded.

## Confirmation: No PyPI Publication

No `twine`, `pip install --upload`, or any PyPI-index command was run.
`dist/` artifacts were only attached to the GitHub Release; they were not
uploaded to any package index.

## Confirmation: No GitHub Packages Publication

No `gh api` call to a GitHub Packages endpoint, no `npm publish`/package
registry command, and no GitHub Packages configuration change was made.
Only the GitHub Releases feature (tag-attached release object + assets)
was used.

## Release URL

`https://github.com/atimad/pcae-harness/releases/tag/v0.1.0-rc1`

## Release Impact

The `v0.1.0-rc1` release candidate is now directly discoverable and
downloadable from the repository's GitHub Releases page, with verified
sdist/wheel artifacts attached and checksummed. This does not change any
product/runtime behavior, does not create a new tag, and does not affect
`origin/main..HEAD` (`0`, unchanged — a GitHub Release does not touch
branch history).

## Remaining Risks

Unchanged from 106F/106K, plus:

1. Release artifacts are attached to this GitHub Release only; they are
   still not published to any package index (PyPI/TestPyPI) — installing
   via `pip install pcae-harness` remains unavailable. This is
   intentional and out of scope for this phase.
2. The release is marked prerelease; promoting it to a full/final
   release (or creating a `v0.1.0` final tag) is a distinct,
   not-yet-requested action.
3. All risks carried from 106F/106K (README/ROADMAP staleness, dual
   report-trust schemas, static package version not derived from git
   tags) remain unchanged and non-blocking.

## Recommended Next Step

107A — v0.2 Full Autonomy Roadmap / Execution Capability Gap Analysis.
