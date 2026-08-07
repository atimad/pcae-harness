"""HATP FIDO2 Hardware Provider -- Phase 149O.2, Wave 5 (primary
provider strategy per 149O.1D plan §23).

Wave-5 spike result (HATP-REQ-020: "generic FIDO2 and generic PIV are
not declared interchangeable... a future implementation SHALL
demonstrate, for its chosen protocol and profile, that it actually
satisfies HATP_HARDWARE_PROVIDER_V1's exact signing/assertion
requirement before being accepted as compliant"):

    WebAuthn/CTAP2 `getAssertion` signs `authenticatorData ||
    SHA-256(clientDataJSON)` (confirmed directly from the installed
    `fido2` library's own `AssertionResponse.verify()`:
    `public_key.verify(self.auth_data + client_param, self.signature)`,
    where `client_param` is the SHA-256 hash of `clientDataJSON`).
    `clientDataJSON` itself embeds a caller-supplied `challenge` field
    (`fido2.webauthn.CollectedClientData.create(type, challenge, ...)`
    accepts an arbitrary caller-supplied byte string as `challenge`,
    independently confirmed by reading the installed library's source).

    This module binds HATP's canonical payload digest
    (`sha256(canonical_payload)`) as that challenge. Any change to the
    canonical payload changes the digest, which changes `challenge`,
    which changes `clientDataJSON`, which changes `client_param`
    (its SHA-256 hash), which invalidates the signature over
    `authenticatorData || client_param` for every other payload. The
    binding is therefore genuine and byte-exact, even though the digest
    is not the literal bytes fed to the signature algorithm (the
    WebAuthn wire format never signs a caller byte string directly --
    it always signs authenticatorData + a hash of a JSON structure that
    *contains* the caller's challenge). This satisfies HATP-REQ-020's
    demonstration requirement for FIDO2; the FIDO2-spike-failure /
    PIV-fallback branch of 149O.1D plan §23 was therefore NOT taken.

Root-1 (non-exportable key, fresh physical presence) mapping, confirmed
directly against the installed library, not assumed (items 49-51):

    - Non-exportable private key: CTAP2 authenticators never expose the
      private key over any documented command; this module never
      requests, receives, or constructs a private key on the
      verification side, and the signing side (`request_signature`)
      never accepts one as a parameter either -- signing happens
      entirely inside the physical device via `Ctap2.get_assertion`.
    - Fresh human presence: `AuthenticatorData.FLAG.UP` ("User Present"),
      read from `AuthenticatorData.is_user_present`, set by the
      authenticator itself as part of assertion generation -- this
      module treats `human_presence_proven` as `is_user_present`,
      exactly (item 51: UP, not UV -- HATP-001's text says
      "human-presence", not "user verification"/biometric; UV is a
      distinct, stronger, optional signal this module does not require
      because HATP-001 does not require it). CTAP2 authenticators
      re-evaluate UP on every `getAssertion` call -- there is no
      "unlock once, sign many" caching at this layer (HATP-REQ-017); no
      code in this module caches or reuses a prior presence result.

This module hard-imports the third-party `fido2` and `cryptography`
packages (declared as the optional `pcae-harness[hatp-hardware]`
extra). It is imported lazily, only from
`hatp_providers.discover_hardware_providers()` /
`create_production_hardware_provider()` -- ordinary PCAE core imports
never touch this module and never require either dependency to be
installed (item 64/65: no import-time hardware failure, no import-time
device probe; `_discover_devices()` below is the only place this
module calls into `fido2.hid`, and only when explicitly invoked).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import List, Optional

from fido2 import cbor
from fido2.cose import CoseKey
from fido2.ctap import CtapError
from fido2.ctap2.base import Ctap2
from fido2.hid import CtapHidDevice
from fido2.webauthn import AuthenticatorData, CollectedClientData

from pcae.core.hatp_hardware_credentials import HATPHardwareCredentialStore, HATPHardwareCredentialStoreError
from pcae.core.hatp_providers import (
    HATP_HARDWARE_PROVIDER_V1,
    HardwareProviderAvailability,
    HardwareProviderCapabilities,
    HardwareProviderConformance,
    HATPProviderCancelledError,
    HATPProviderDeviceError,
    HATPProviderUnavailableError,
    HATPProviderVerificationOutcome,
    ProviderAssertion,
)

PROTOCOL_NAME = "FIDO2"

#: Fixed, non-caller-selectable RP-ID/origin pair this module uses for
#: every HATP FIDO2 operation (item 22: caller cannot self-select a
#: trust-relevant string; there is no parameter anywhere in this module
#: that changes these). HATP is not a web origin; these are stable,
#: internal constants scoping every assertion this module produces/
#: verifies to "HATP operations" specifically, exactly as an RP ID scopes
#: ordinary WebAuthn credentials to a web origin.
_HATP_RP_ID = "hatp.pcae.local"
_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"
_RP_ID_HASH = hashlib.sha256(_HATP_RP_ID.encode("utf-8")).digest()

_EVIDENCE_SCHEMA_VERSION = 1
_EVIDENCE_FIELDS = frozenset(
    {"version", "credential_id_hex", "authenticator_data_hex", "client_data_json_hex", "signature_hex"}
)


def _payload_digest(canonical_payload: bytes) -> bytes:
    """The challenge bound into every HATP FIDO2 assertion: SHA-256 of
    the exact canonical payload bytes, computed independently here (item
    10: no second canonicalizer -- this hashes the bytes it is given, it
    never reconstructs proof JSON, and never accepts a caller-supplied
    pre-digested value on the signing side)."""

    return hashlib.sha256(canonical_payload).digest()


def _reject_duplicate_keys(pairs: list) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key in FIDO2 evidence: {key!r}")
        result[key] = value
    return result


def _serialize_evidence(
    *, credential_id: bytes, authenticator_data: bytes, client_data_json: bytes, signature: bytes
) -> bytes:
    """Strict, closed, versioned schema (items 30-32). No unknown field
    accepted on parse; duplicate JSON keys rejected; unknown `version`
    values fail closed."""

    document = {
        "version": _EVIDENCE_SCHEMA_VERSION,
        "credential_id_hex": credential_id.hex(),
        "authenticator_data_hex": authenticator_data.hex(),
        "client_data_json_hex": client_data_json.hex(),
        "signature_hex": signature.hex(),
    }
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")


class HATPFido2EvidenceMalformedError(HATPProviderDeviceError):
    """Reserved for genuine deserialization plumbing failures this
    module cannot recover from as a plain "invalid assertion" -- in
    practice `verify()` below catches this and every other parse issue
    and returns `signature_valid=False` instead of raising (see the
    `HATPProofVerifierProvider.verify` docstring's fail-closed-without-
    raising contract); this class exists for internal clarity only and
    is never allowed to propagate out of `verify()`."""


def _deserialize_evidence(evidence: bytes) -> dict:
    try:
        raw_text = evidence.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HATPFido2EvidenceMalformedError(f"evidence is not valid UTF-8: {exc}") from exc
    try:
        document = json.loads(raw_text, object_pairs_hook=_reject_duplicate_keys)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HATPFido2EvidenceMalformedError(f"evidence is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise HATPFido2EvidenceMalformedError("evidence must be a JSON object")
    extra_fields = set(document) - _EVIDENCE_FIELDS
    if extra_fields:
        raise HATPFido2EvidenceMalformedError(f"evidence contains unknown fields: {sorted(extra_fields)}")
    missing_fields = _EVIDENCE_FIELDS - set(document)
    if missing_fields:
        raise HATPFido2EvidenceMalformedError(f"evidence is missing fields: {sorted(missing_fields)}")
    if document["version"] != _EVIDENCE_SCHEMA_VERSION:
        raise HATPFido2EvidenceMalformedError(f"unsupported evidence schema version: {document['version']!r}")
    return document


def discover_fido2() -> HardwareProviderAvailability:
    """Discovery facts only (item 34): library presence + a raw USB HID
    enumeration count. Never establishes trust; never itself a readiness
    claim. Any enumeration failure is reported as `device_detected=False`
    with a note, never raised (item 63)."""

    device_count = 0
    notes: List[str] = []
    try:
        device_count = sum(1 for _ in CtapHidDevice.list_devices())
    except Exception as exc:  # noqa: BLE001 -- discovery must never raise/crash the caller
        notes.append(f"device_enumeration_failed:{exc.__class__.__name__}")

    return HardwareProviderAvailability(
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        protocol_name=PROTOCOL_NAME,
        library_installed=True,
        device_detected=device_count > 0,
        notes=tuple(notes) or (f"devices_detected:{device_count}",),
    )


@dataclass(frozen=True)
class _ParsedFido2Evidence:
    credential_id: bytes
    authenticator_data: AuthenticatorData
    client_data: CollectedClientData
    signature: bytes


def _parse_fido2_evidence(evidence: bytes) -> _ParsedFido2Evidence:
    document = _deserialize_evidence(evidence)
    credential_id = bytes.fromhex(document["credential_id_hex"])
    authenticator_data = AuthenticatorData(bytes.fromhex(document["authenticator_data_hex"]))
    client_data = CollectedClientData(bytes.fromhex(document["client_data_json_hex"]))
    signature = bytes.fromhex(document["signature_hex"])
    return _ParsedFido2Evidence(
        credential_id=credential_id,
        authenticator_data=authenticator_data,
        client_data=client_data,
        signature=signature,
    )


class Fido2HardwareProvider:
    """Real FIDO2 provider: implements both the production signing
    interface (`HATPHardwareSigner`, structurally) and the Wave-4
    verification interface (`HATPProofVerifierProvider`, structurally --
    no explicit inheritance required, since both are `Protocol` classes).

    Construction never touches hardware or the credential registry
    (item 66: device probing happens explicitly, inside
    `request_signature`/`verify`, never at `__init__`)."""

    def __init__(self, *, credential_store: Optional[HATPHardwareCredentialStore] = None) -> None:
        self._credential_store = credential_store

    def _resolve_credential_store(self) -> HATPHardwareCredentialStore:
        if self._credential_store is not None:
            return self._credential_store
        return HATPHardwareCredentialStore.production()

    def capabilities(self) -> HardwareProviderCapabilities:
        return HardwareProviderCapabilities(
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name=PROTOCOL_NAME,
            non_exportable_key=True,
            fresh_touch_per_operation=True,
            credential_identity=True,
            signature_verification=True,
            device_attestation=False,
            hatp_conformant=HardwareProviderConformance.CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS,
            notes=(
                "non_exportable_key: CTAP2 authenticators never expose the private key over any"
                " documented command; this module has no code path that could extract one.",
                "fresh_touch_per_operation: AuthenticatorData.FLAG.UP, re-evaluated by the"
                " authenticator on every getAssertion call; this module never caches or reuses a"
                " prior presence result.",
                "device_attestation: NOT implemented this phase -- vendor attestation-object"
                " validation (Root 2A) is deferred; `attestation_valid=None` is returned by"
                " verify(), meaning 'this provider profile does not evaluate attestation', which"
                " Wave 4 treats as non-blocking (attestation_valid is Optional by contract). This"
                " is why the conformance verdict is CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS, not"
                " CONFORMANT.",
                "REAL HARDWARE NOT EXERCISED in this development environment -- see phase"
                " documentation for exact test scope (deterministic evidence-format and"
                " signature-cryptography tests only, using a test-only in-memory key, never a"
                " live CTAP2 device).",
            ),
        )

    def credential_identity(self) -> str:
        raise HATPProviderUnavailableError(
            "credential_identity() requires a live CTAP2 device with a discoverable/resident"
            " credential; no device is available in this environment. Credential identity for a"
            " non-resident credential is established at enrollment time (Wave 2/7 administrative"
            " surface, out of Wave-5 scope) and is not re-derivable from the device alone."
        )

    # ------------------------------------------------------------------
    # Signing side (HATPHardwareSigner)
    # ------------------------------------------------------------------

    def request_signature(
        self,
        payload: bytes,
        *,
        signer_key_id: str,
        provider_profile: str,
        presence_timeout_s: float = 30.0,
    ) -> ProviderAssertion:
        try:
            devices = list(CtapHidDevice.list_devices())
        except Exception as exc:  # noqa: BLE001 -- enumeration failure is a device error, not a crash
            raise HATPProviderDeviceError(f"FIDO2 device enumeration failed: {exc}") from exc
        if not devices:
            raise HATPProviderUnavailableError("no FIDO2 CTAP2 HID device detected")

        try:
            credential_id = bytes.fromhex(signer_key_id)
        except ValueError as exc:
            raise HATPProviderUnavailableError(
                f"signer_key_id is not a valid hex-encoded FIDO2 credential id: {exc}"
            ) from exc

        challenge = _payload_digest(payload)
        client_data = CollectedClientData.create(
            type=CollectedClientData.TYPE.GET, challenge=challenge, origin=_HATP_ORIGIN
        )

        device = devices[0]
        try:
            ctap2 = Ctap2(device)
            response = ctap2.get_assertion(
                rp_id=_HATP_RP_ID,
                client_data_hash=client_data.hash,
                allow_list=[{"type": "public-key", "id": credential_id}],
            )
        except CtapError as exc:
            if exc.code in (CtapError.ERR.ACTION_TIMEOUT, CtapError.ERR.KEEPALIVE_CANCEL, CtapError.ERR.USER_ACTION_TIMEOUT):
                raise HATPProviderCancelledError(f"FIDO2 presence request cancelled or timed out: {exc}") from exc
            raise HATPProviderDeviceError(f"FIDO2 device rejected the assertion request: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 -- any other transport failure fails closed as a device error
            raise HATPProviderDeviceError(f"FIDO2 transport failure: {exc}") from exc

        evidence = _serialize_evidence(
            credential_id=credential_id,
            authenticator_data=bytes(response.auth_data),
            client_data_json=bytes(client_data),
            signature=response.signature,
        )
        return ProviderAssertion(
            credential_id=credential_id.hex(),
            provider_profile=provider_profile,
            algorithm="ES256",
            evidence=evidence,
        )

    # ------------------------------------------------------------------
    # Verification side (HATPProofVerifierProvider)
    # ------------------------------------------------------------------

    def verify(
        self,
        *,
        canonical_payload: bytes,
        signer_key_id: str,
        provider_profile: str,
        assertion: bytes,
    ) -> HATPProviderVerificationOutcome:
        try:
            record_store = self._resolve_credential_store()
            record = record_store.lookup_credential(signer_key_id)
        except HATPHardwareCredentialStoreError:
            # Genuine registry failure (malformed/symlinked/unreadable) is
            # a provider-level failure -- propagate so Wave 4's
            # broad `except Exception` maps it to INVALID_SIGNATURE,
            # fail-closed, never a silent pass.
            raise

        if record is None or record.status != "active" or record.protocol_name != PROTOCOL_NAME:
            # Unknown/revoked/wrong-protocol credential: fail closed as
            # an invalid assertion, not a crash (item 36/40).
            return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)
        if record.provider_profile != provider_profile:
            # Item 38: provider profile mismatch fails closed here too,
            # independent of the Wave-2 trust-store's own profile check.
            return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)

        try:
            parsed = _parse_fido2_evidence(assertion)
        except HATPFido2EvidenceMalformedError:
            return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)

        if parsed.credential_id.hex() != signer_key_id.lower():
            # Item 37: wrong credential used to sign.
            return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)

        if parsed.client_data.type != CollectedClientData.TYPE.GET:
            return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)
        if parsed.client_data.origin != _HATP_ORIGIN:
            return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)
        expected_challenge = _payload_digest(canonical_payload)
        if parsed.client_data.challenge != expected_challenge:
            # Item 41: replay against a different canonical payload.
            return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)
        if parsed.authenticator_data.rp_id_hash != _RP_ID_HASH:
            return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)

        try:
            cose_key = CoseKey.parse(cbor.decode(record.public_key))
            cose_key.verify(bytes(parsed.authenticator_data) + parsed.client_data.hash, parsed.signature)
        except Exception:  # noqa: BLE001 -- any crypto/format failure is a plain invalid signature
            return HATPProviderVerificationOutcome(signature_valid=False, human_presence_proven=False)

        human_presence_proven = bool(parsed.authenticator_data.is_user_present())
        return HATPProviderVerificationOutcome(
            signature_valid=True,
            human_presence_proven=human_presence_proven,
            # Device attestation (Root 2A) is not evaluated by this
            # phase -- `None` means "this provider profile does not
            # perform/require device attestation," a documented,
            # non-blocking limitation (see `capabilities()` above), not
            # an omission.
            attestation_valid=None,
        )
