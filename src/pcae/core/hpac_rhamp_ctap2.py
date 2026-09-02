"""RHAMP-001 v1.0 §3 / §9 / §21 / §38 — the native CTAP2 client boundary
for ``hpac.fido2.uv_presence.v2``: ``authenticatorMakeCredential`` (§13,
enrollment) and ``authenticatorGetAssertion`` (§33, authentication), the
authenticator profile restrictions (§9 / §19 / §51), and the deterministic
NON_REAL provider seam CI uses instead of hardware (§63).

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156 ``.1R.30``
bundle).

**Native CTAP2, not WebAuthn** (RHAMP-REQ-008/009/010): this module drives
``fido2.ctap2`` over ``fido2.hid.CtapHidDevice`` directly. There is no
browser, no web page, no DOM, no WebAuthn client, no web origin, no TLS.
It adopts the CTAP2 wire shapes (``authenticatorData``, COSE keys, the
assertion signature form ``sign(authenticatorData ‖ clientDataHash)``)
because the pinned ``fido2`` library implements them — exactly as
``hatp_fido2_provider.py`` already does (RHAMP-REQ-104: reuse the CTAP2
transport / COSE-verify primitives **as a shared library only**, never HATP
trust state; the HATP ``_HATP_RP_ID`` / ``_HATP_ORIGIN`` constants are
**not** reused — RHAMP-001 supplies its own canonical ``client_data_hash``).

**No new dependency** (RHAMP-REQ-106): the already-declared
``fido2>=1.1,<2`` / ``cryptography>=42,<45`` (the ``hatp-hardware`` extra).
``CoseKey.verify`` is the library's; **no custom cryptography**
(RHAMP-REQ-062/107).

**Structural NON_REAL wall** (RHAMP-REQ-155 / §41): the deterministic
provider carries ``SIMULATION_ONLY: Final[bool] = True`` — a class constant
with no constructor override — and a fixed ``PROVIDER_KIND`` that can never
equal the production kind. Production selection
(:func:`resolve_production_ctap2_provider`) accepts **no** environment
variable / caller flag that swaps in a fixture (RHAMP-REQ-048 / §63).
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Final, Optional, Protocol

from fido2 import cbor
from fido2.cose import ES256, CoseKey
from fido2.webauthn import AttestedCredentialData, AuthenticatorData

from pcae.core.hpac_rhamp_client_context import MECHANISM_ID, RP_ID, RP_ID_HASH
from pcae.core.hpac_rhamp_terminal_reasons import RhampTerminalError, TerminalReasonCode

__all__ = [
    "PRODUCTION_PROVIDER_KIND",
    "SUPPORTED_TRANSPORTS",
    "Ctap2UnavailableError",
    "Ctap2CancelledError",
    "MakeCredentialResult",
    "GetAssertionResult",
    "Ctap2Provider",
    "NativeCtap2Provider",
    "DeterministicCtap2Provider",
    "resolve_production_ctap2_provider",
    "verify_assertion_signature_material",
]

PRODUCTION_PROVIDER_KIND = "native-ctap2"
#: RHAMP-REQ-132 — USB-HID and NFC only. BLE / hybrid / platform excluded.
SUPPORTED_TRANSPORTS: Final[tuple[str, ...]] = ("usb", "nfc")

_ES256_ALG = -7  # COSE alg identifier for ES256 (RHAMP-REQ-043: ES256 only).


class Ctap2UnavailableError(RhampTerminalError):
    """No supported CTAP2 authenticator is available, or it cannot perform
    UV (RHAMP-REQ-035 — no downgrade, no fallback mechanism)."""

    def __init__(self, detail: str = "") -> None:
        super().__init__(TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID, detail or "no CTAP2 authenticator")


class Ctap2CancelledError(RhampTerminalError):
    """The human cancelled the authenticator ceremony, or it timed out
    (RHAMP-REQ-146)."""

    def __init__(self, detail: str = "", *, timed_out: bool = False) -> None:
        code = (
            TerminalReasonCode.CEREMONY_TIMED_OUT
            if timed_out
            else TerminalReasonCode.CEREMONY_CANCELLED
        )
        super().__init__(code, detail or code.value)


@dataclass(frozen=True)
class MakeCredentialResult:
    """The verified output of one CTAP2 ``authenticatorMakeCredential`` call
    (RHAMP-REQ-043 / §22). ``cose_public_key`` is ``cbor(COSE_Key)`` —
    exactly the bytes ``CoseKey.parse(cbor.decode(...))`` consumes."""

    raw_credential_id: bytes
    cose_public_key: bytes
    aaguid: Optional[bytes]
    up: bool
    uv: bool
    transport: str  # one of SUPPORTED_TRANSPORTS


@dataclass(frozen=True)
class GetAssertionResult:
    """The raw output of one CTAP2 ``authenticatorGetAssertion`` call. All
    fields are **untrusted** until :func:`verify_assertion_signature_material`
    (and the full §37 verifier sequence) pass."""

    raw_credential_id: bytes
    authenticator_data: bytes
    signature: bytes
    up: bool
    uv: bool
    sign_count: int


class Ctap2Provider(Protocol):
    """RHAMP-REQ-104 — the narrow CTAP2 protocol surface RHAMP-001 uses."""

    PROVIDER_KIND: str

    def available(self) -> bool:
        ...

    def make_credential(
        self, *, client_data_hash: bytes, user_id: bytes, user_name: str
    ) -> MakeCredentialResult:
        ...

    def get_assertion(
        self, *, client_data_hash: bytes, allow_credential_ids: list[bytes]
    ) -> GetAssertionResult:
        ...


# ─────────────────────────────────────────────────────────────────────────
# Assertion signature material verification (RHAMP-REQ-102 steps 2/3/5)
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AssertionSignatureCheck:
    rp_id_hash_ok: bool
    signature_ok: bool
    up: bool
    uv: bool
    sign_count: int


def verify_assertion_signature_material(
    *,
    cose_public_key: bytes,
    authenticator_data: bytes,
    signature: bytes,
    client_data_hash: bytes,
) -> AssertionSignatureCheck:
    """RHAMP-REQ-102 — verify, with the pinned library's primitives and **no
    custom cryptography**:

      * ``authenticatorData.rpIdHash == SHA-256("hpac.pcae.local")`` (§6);
      * the assertion signature over ``authenticatorData ‖ client_data_hash``
        using ``CoseKey.parse(cbor.decode(cose_public_key))`` (§17);
      * the ``FLAG.UP`` and ``FLAG.UV`` bits (§10) and the raw ``signCount``.

    Never raises for a bad signature / flags — returns the granular booleans
    so the verifier maps each to its own ``terminal_reason_code``. Raises
    only for a structurally unparseable input (mapped to
    ``internal_verification_error`` by the caller).
    """

    try:
        auth_data = AuthenticatorData(authenticator_data)
    except Exception as exc:  # noqa: BLE001 — malformed authData
        raise RhampTerminalError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR, f"malformed authenticatorData: {exc}"
        ) from exc
    try:
        key = CoseKey.parse(cbor.decode(cose_public_key))
    except Exception as exc:  # noqa: BLE001 — malformed stored key
        raise RhampTerminalError(
            TerminalReasonCode.INTERNAL_VERIFICATION_ERROR, f"malformed stored cose_public_key: {exc}"
        ) from exc

    rp_id_hash_ok = bytes(auth_data.rp_id_hash) == RP_ID_HASH
    signature_ok = False
    try:
        key.verify(bytes(auth_data) + client_data_hash, signature)
        signature_ok = True
    except Exception:  # noqa: BLE001 — any crypto/format failure is a plain invalid signature
        signature_ok = False
    return AssertionSignatureCheck(
        rp_id_hash_ok=rp_id_hash_ok,
        signature_ok=signature_ok,
        up=bool(auth_data.flags & AuthenticatorData.FLAG.UP),
        uv=bool(auth_data.flags & AuthenticatorData.FLAG.UV),
        sign_count=int(auth_data.counter),
    )


# ─────────────────────────────────────────────────────────────────────────
# Production provider — native CTAP2 over USB-HID / NFC
# ─────────────────────────────────────────────────────────────────────────


class NativeCtap2Provider:
    """RHAMP-REQ-030/031/032 — a roaming / cross-platform FIDO2 authenticator
    over CTAP2, non-discoverable credential, ``allowList``-bound assertion,
    USB-HID or NFC, UP + UV required. No BLE, no hybrid, no platform
    authenticator, no resident-credential fallback.

    Reuses the ``fido2.ctap2`` / ``fido2.hid`` primitives exactly as
    ``hatp_fido2_provider.py`` does (RHAMP-REQ-104). Construction never
    touches hardware — device I/O happens only inside ``make_credential`` /
    ``get_assertion`` (RHAMP-REQ-153: no hardware in this phase's automated
    runs; this class is hardware-capable production code, exercised for real
    in ``.1R.33``).
    """

    PROVIDER_KIND: Final[str] = PRODUCTION_PROVIDER_KIND

    def __init__(self, *, presence_timeout_s: float = 60.0) -> None:
        self._presence_timeout_s = presence_timeout_s

    def _devices(self):
        from fido2.hid import CtapHidDevice

        try:
            return list(CtapHidDevice.list_devices())
        except Exception as exc:  # noqa: BLE001
            raise Ctap2UnavailableError(f"CTAP2 device enumeration failed: {exc}") from exc

    def available(self) -> bool:
        try:
            return bool(self._devices())
        except Ctap2UnavailableError:
            return False

    def _ctap2(self, device):
        from fido2.ctap2.base import Ctap2

        return Ctap2(device)

    def make_credential(
        self, *, client_data_hash: bytes, user_id: bytes, user_name: str
    ) -> MakeCredentialResult:
        from fido2.ctap import CtapError

        devices = self._devices()
        if not devices:
            raise Ctap2UnavailableError("no CTAP2 authenticator attached for makeCredential")
        rp = {"id": RP_ID, "name": "PCAE HPAC"}
        user = {"id": user_id, "name": user_name, "displayName": user_name}
        key_params = [{"type": "public-key", "alg": ES256.ALGORITHM}]
        # RHAMP-REQ-032/033/061: non-discoverable (rk absent), UV required,
        # no attestation preference.
        options = {"rk": False, "uv": True}
        try:
            ctap2 = self._ctap2(devices[0])
            attestation = ctap2.make_credential(
                client_data_hash=client_data_hash,
                rp=rp,
                user=user,
                key_params=key_params,
                options=options,
            )
        except CtapError as exc:
            if exc.code in (
                CtapError.ERR.ACTION_TIMEOUT,
                CtapError.ERR.USER_ACTION_TIMEOUT,
            ):
                raise Ctap2CancelledError(str(exc), timed_out=True) from exc
            if exc.code == CtapError.ERR.KEEPALIVE_CANCEL:
                raise Ctap2CancelledError(str(exc)) from exc
            raise Ctap2UnavailableError(f"device rejected makeCredential: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise Ctap2UnavailableError(f"CTAP2 transport failure during makeCredential: {exc}") from exc

        auth_data = attestation.auth_data
        credential_data = getattr(auth_data, "credential_data", None)
        if credential_data is None:
            raise Ctap2UnavailableError("makeCredential response carried no attested credential data")
        cose_key = credential_data.public_key
        if cose_key.get(3) != _ES256_ALG:  # COSE 'alg'
            raise Ctap2UnavailableError(
                f"makeCredential produced an unsupported COSE algorithm: {cose_key.get(3)!r} (ES256 only)"
            )
        flags = int(auth_data.flags)
        return MakeCredentialResult(
            raw_credential_id=bytes(credential_data.credential_id),
            cose_public_key=cbor.encode(cose_key),
            aaguid=bytes(credential_data.aaguid) if credential_data.aaguid else None,
            up=bool(flags & AuthenticatorData.FLAG.UP),
            uv=bool(flags & AuthenticatorData.FLAG.UV),
            transport="usb",
        )

    def get_assertion(
        self, *, client_data_hash: bytes, allow_credential_ids: list[bytes]
    ) -> GetAssertionResult:
        from fido2.ctap import CtapError

        if not allow_credential_ids:
            raise Ctap2UnavailableError("getAssertion requires a non-empty canonical allowList (no discoverable flow)")
        devices = self._devices()
        if not devices:
            raise Ctap2UnavailableError("no CTAP2 authenticator attached for getAssertion")
        allow_list = [{"type": "public-key", "id": cid} for cid in allow_credential_ids]
        try:
            ctap2 = self._ctap2(devices[0])
            response = ctap2.get_assertion(
                rp_id=RP_ID,
                client_data_hash=client_data_hash,
                allow_list=allow_list,
                options={"uv": True},
            )
        except CtapError as exc:
            if exc.code in (CtapError.ERR.ACTION_TIMEOUT, CtapError.ERR.USER_ACTION_TIMEOUT):
                raise Ctap2CancelledError(str(exc), timed_out=True) from exc
            if exc.code == CtapError.ERR.KEEPALIVE_CANCEL:
                raise Ctap2CancelledError(str(exc)) from exc
            raise Ctap2UnavailableError(f"device rejected getAssertion: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise Ctap2UnavailableError(f"CTAP2 transport failure during getAssertion: {exc}") from exc

        auth_data = AuthenticatorData(bytes(response.auth_data))
        credential = response.credential or {}
        raw_id = bytes(credential.get("id", allow_credential_ids[0]))
        flags = int(auth_data.flags)
        return GetAssertionResult(
            raw_credential_id=raw_id,
            authenticator_data=bytes(response.auth_data),
            signature=bytes(response.signature),
            up=bool(flags & AuthenticatorData.FLAG.UP),
            uv=bool(flags & AuthenticatorData.FLAG.UV),
            sign_count=int(auth_data.counter),
        )


# ─────────────────────────────────────────────────────────────────────────
# Deterministic NON_REAL provider — a synthetic virtual authenticator
# (RHAMP-REQ-154/155 / §63). Real ES256 crypto, synthetic authenticator.
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class _VirtualCredential:
    private_key: object
    cose_public_key: bytes
    sign_count: int


class DeterministicCtap2Provider:
    """RHAMP-REQ-154 — an **explicitly TEST / NON_PRODUCTION** virtual
    authenticator. It performs **real ES256 signing / verification** (so the
    full COSE verification path is exercised) over a **synthetic** in-memory
    key — it is never a real device and its output is structurally NON_REAL
    (RHAMP-REQ-155 / §41).

    Adversarial knobs are explicit constructor parameters — there is no
    hidden default that silently produces a UV-satisfied assertion.
    """

    PROVIDER_KIND: Final[str] = "deterministic-test-fixture"
    #: Structural NON_REAL wall (RHAMP-REQ-155): a class constant, no
    #: constructor override, never equal to PRODUCTION_PROVIDER_KIND.
    SIMULATION_ONLY: Final[bool] = True

    def __init__(
        self,
        *,
        up: bool = True,
        uv: bool = True,
        available: bool = True,
        aaguid: bytes = b"\x00" * 16,
        start_sign_count: int = 0,
        sign_count_step: int = 1,
        cancel: bool = False,
        timed_out: bool = False,
        wrong_rp_id_hash: bool = False,
        transport: str = "usb",
    ) -> None:
        assert self.SIMULATION_ONLY is True and self.PROVIDER_KIND != PRODUCTION_PROVIDER_KIND
        self._up = up
        self._uv = uv
        self._available = available
        self._aaguid = aaguid
        self._sign_count_step = sign_count_step
        self._cancel = cancel
        self._timed_out = timed_out
        self._wrong_rp_id_hash = wrong_rp_id_hash
        self._transport = transport
        self._credentials: dict[bytes, _VirtualCredential] = {}
        self._next_sign_count = start_sign_count

    PROVIDER_KIND_IS_REAL: Final[bool] = False

    def available(self) -> bool:
        return self._available

    def _maybe_cancel(self) -> None:
        if self._timed_out:
            raise Ctap2CancelledError("virtual authenticator timeout", timed_out=True)
        if self._cancel:
            raise Ctap2CancelledError("virtual authenticator cancelled")

    def make_credential(
        self, *, client_data_hash: bytes, user_id: bytes, user_name: str
    ) -> MakeCredentialResult:
        from cryptography.hazmat.primitives.asymmetric import ec

        self._maybe_cancel()
        if not self._available:
            raise Ctap2UnavailableError("virtual authenticator unavailable")
        priv = ec.generate_private_key(ec.SECP256R1())
        cose = ES256.from_cryptography_key(priv.public_key())
        cose_bytes = cbor.encode(cose)
        raw_id = hashlib.sha256(cose_bytes + os.urandom(16)).digest()
        self._credentials[raw_id] = _VirtualCredential(
            private_key=priv, cose_public_key=cose_bytes, sign_count=self._next_sign_count
        )
        return MakeCredentialResult(
            raw_credential_id=raw_id,
            cose_public_key=cose_bytes,
            aaguid=self._aaguid,
            up=self._up,
            uv=self._uv,
            transport=self._transport,
        )

    def register_external_credential(self, raw_credential_id: bytes, private_key, cose_public_key: bytes) -> None:
        """Test seam: load a credential this provider did not itself mint
        (used to model a *different* authenticator / clone)."""

        self._credentials[bytes(raw_credential_id)] = _VirtualCredential(
            private_key=private_key, cose_public_key=cose_public_key, sign_count=self._next_sign_count
        )

    def get_assertion(
        self, *, client_data_hash: bytes, allow_credential_ids: list[bytes]
    ) -> GetAssertionResult:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec

        self._maybe_cancel()
        if not self._available:
            raise Ctap2UnavailableError("virtual authenticator unavailable")
        if not allow_credential_ids:
            raise Ctap2UnavailableError("getAssertion requires a non-empty allowList")
        selected: Optional[bytes] = None
        for cid in allow_credential_ids:
            if bytes(cid) in self._credentials:
                selected = bytes(cid)
                break
        if selected is None:
            raise Ctap2UnavailableError("no allowList credential is held by this virtual authenticator")
        vcred = self._credentials[selected]
        vcred.sign_count += self._sign_count_step
        rp_id_hash = RP_ID_HASH if not self._wrong_rp_id_hash else hashlib.sha256(b"attacker.example").digest()
        flags = 0
        if self._up:
            flags |= AuthenticatorData.FLAG.UP
        if self._uv:
            flags |= AuthenticatorData.FLAG.UV
        auth_data = AuthenticatorData.create(rp_id_hash, flags, vcred.sign_count)
        signature = vcred.private_key.sign(
            bytes(auth_data) + client_data_hash, ec.ECDSA(hashes.SHA256())
        )
        return GetAssertionResult(
            raw_credential_id=selected,
            authenticator_data=bytes(auth_data),
            signature=signature,
            up=self._up,
            uv=self._uv,
            sign_count=vcred.sign_count,
        )


def resolve_production_ctap2_provider() -> NativeCtap2Provider:
    """RHAMP-REQ-048 / §63 — the **only** production selection path. It
    accepts **no** environment variable, caller flag, repository value, or
    config that could swap in the deterministic fixture. The deterministic
    provider is reachable **only** by explicit construction in test code."""

    return NativeCtap2Provider()
