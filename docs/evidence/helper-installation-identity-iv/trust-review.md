# Independent identity-IV trust review

Scope: read-only primary contract/source review of HELPER4.0, PAWA3.0, PPA2.1 and helper_installation_identity_constraints.json. No predecessor report used. No repository changes or lifecycle/finalization actions.

## Blocking finding: H registration lifecycle has no consistently authorized producer

The new parent/component identity relation itself is directional and well formed. The remaining circularity is in the execution/provenance dependency for creating that relation.

* PAWA REQ-328 (lines 5071-5079) explicitly requires the configure_privileged_helper transaction itself to run through §33C as admin_mutation and says its registration metadata is written by a verified helper process. Merely invoking an external admin script does not satisfy or remove this execution requirement.
* PAWA REQ-311 as specialized by REQ-342 requires that executing privileged helper already have a verified current schema2 registration and exact current PAWA parent binding.
* HELPER REQ-023/024 (lines 324-339) require component metadata's PAWA writer provenance and a PAWA capability for initial registration. REQ-144 makes the Model E mint exclusive to protected dispatch, and REQ-183 keeps the legacy-factory prohibition.
* HELPER REQ-175 (lines 2482-2491) instead says initial component registration uses external recognized deployment-owner provisioning and forbids a helper from registering/rotating/revoking its own active executing lineage. PAWA REQ-343 reiterates external installer lifecycle.
* The exact existing no-capability raw-filesystem exceptions, PAWA REQ-056 and REQ-194, authorize initial root/manifest/descriptor/current-anchor/exclusion provisioning; they do not define an external component registration writer/provenance path. PAWA §97 explicitly updates REQ-336 and REQ-311 but does not reconcile REQ-328 or the capability/provenance production requirements.

Counterexample A: a valid independently recognized PAWA root exists; hpac-pawa-privileged-helper bytes have been installed out of band; no H generation record or anchor exists. REQ-328 requires H execution to produce generation1, but current H admission must fail RegisteredGenerationMatch/descriptor_missing. P cannot produce this mutation because its only family is presentation evidence. An external coordinator cannot change the executor requirement. Raw external writes require an unspecified exception to the frozen producer/capability requirements.

Counterexample B: the sole current H lineage is hpahi-A generation1 and the owner wants generation2 or revocation. REQ-328 routes the metadata mutation to H. A is the only current H under the fixed pawa-helper/current-generation.json anchor, but REQ-175 forbids A from changing its active executing lineage. An alternate H cannot be current under that same anchor without first performing the blocked lifecycle transition.

Reading HELPER-175 as intended supersession of PAWA-328 repairs the high-level direction only by implication; it still leaves the external production writer/provenance mechanism undefined, despite preserving Model E as sole forward-authorized mechanism and forbidding legacy factory imports. A coherent contract must expressly specify the external provisioning exception/producer and its bounded provenance validation semantics, or provide a non-circular separately admitted executor model. This is a contract coherence/implementability defect, not proof an unprivileged caller can presently mint a writer.

## Other attacks that fail at contract level

* Forged self-consistent binding: HELPER172/174/175 require exact live independently recognized PAWA state. Hash consistency alone grants nothing. No parent recognition back-reference to H/P is permitted (PAWA341, PPA105).
* Caller profile/root/executable/account selection: HELPER173/177/178 fixes profile from verified opened executable, treats request tuple as echo only, and resolves the account from protected state and trusted live OS data. Unknown or mismatching shapes fail closed. JSON constraints faithfully express these relations.
* Same-uid and unknown account fallback: HELPER178 mandates helper uid == peer uid == deployment-owner uid, both unequal to configured agent; missing/None/unresolvable identity fails agent_principal_unknown. Account uid pins and live groups are mandatory. Task labels and ambient euid cannot substitute. Equal uid numbers cannot establish human identity.
* H writing P evidence / forged APPROVE: HELPER176/180, PAWA342 and PPA106 restrict P evidence to the original authenticated P ceremony process after actual valid APPROVE; privileged IPC cannot dispatch the fifth operation.
* Stale component/parent/schema1: HELPER176/181 require admission and pre-mutation exact tuple checks; PAWA parent changes invalidate old bindings; historical validation is only for external lifecycle repair, never runtime admission. Equal integer generations across categories do not bind them.
* Pre-admission provenance-read cycle: HELPER179 expressly permits fixed-root trusted primitive reads for PAWA recognition before admission and disallows a circular assertion of already admitted state. HELPER183 explicitly leaves foundation repair deferred. Existing source corroborates this is unimplemented: hpac_foundation.py:599-611 requires the legacy seal to bind configured-agent identity; :639-661 otherwise checks ambient process identity; :982-990 verify_record calls _ensure_root. This is an acknowledged implementation blocker, not an additional contradiction in the new read contract.
* Last-instruction rotation race: immediate pre-mutation checks are required and PAWA069/070 explicitly bound the claim, including no promise of absolute TOCTOU elimination and expected_current compare-and-write. No additional contract blocker established merely by scheduling rotation between arbitrary instructions; implementation IV must test real commit/currentness ordering.

No production safety or implementation-ready verdict is inferred. Runtime boundaries remain unchanged; independent checks by the owning agent are required before session closure.
