# PCAE v0.1.0-rc1 — Published Release Notes

This is the exact release body published to the GitHub Release for
`v0.1.0-rc1` in Phase 106L
(https://github.com/atimad/pcae-harness/releases/tag/v0.1.0-rc1),
promoted from `docs/RELEASE_NOTES_V0_1_DRAFT.md`. The release is marked
**prerelease**. No `v0.1.0` final tag exists. No PyPI publication. No
GitHub Packages publication.

---

# PCAE v0.1.0-rc1
PCAE v0.1.0-rc1 is the first release candidate for the non-executing PCAE lifecycle governance harness.
## What this release is
PCAE v0.1 provides governed lifecycle support for AI-assisted software engineering:
- task and phase contracts
- report-trust validation and hard-fail gates
- golden workflow documentation
- commit/push governance
- bootstrap/session reporting
- outbound Telegram report notification
- release readiness checks
- packaging/install smoke validation
- post-RC audit, repair, and verification documentation
## Important boundary
v0.1 is non-executing by design.
It does not:
- autonomously execute code
- mediate shell commands
- invoke real AI backends
- provide Telegram inbound control
- replace human approval
- enable runtime enforcement
v0.2 is the future autonomy target.
## Validation summary
- fast_green: 4390/4390 fully green
- sdist/wheel build: passed
- wheel smoke install: passed
- post-RC audit: completed
- trust-gate asymmetry repair: completed and live-CLI verified
- documentation alignment: completed
- effectiveness evaluation framework: added
## Installation
Download the attached wheel or sdist from this release.
See repository documentation for installation and golden workflow details.
## Notes
This release candidate is intended for evaluation of PCAE's non-executing governance lifecycle, not for autonomous coding execution.
