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

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R — **N-16-5 CTAP2 PIN/UV protocol
interoperability repair** (finding H-1). CTAP 2.1 removed the bare ``uv``
option from ``authenticatorMakeCredential`` and requires a PIN/UV-protocol
``pinUvAuthParam`` for ``authenticatorGetAssertion`` on a ``clientPin``-based
roaming key. :class:`NativeCtap2Provider` therefore negotiates the
authenticator's supported PIN/UV protocol (``ClientPin`` / ``PinProtocolV2``
preferred), acquires a permission-scoped, rp-bound ``pinUvAuthToken`` via a
**trusted, non-logging, non-persisted local PIN entry** (``getpass`` — never a
CLI argument, environment variable, repository value, or chat prompt; the PIN
is discarded the instant the token is obtained and never stored on any RHAMP
artifact — RHAMP-INV-006 / §18 / §54 intact), derives a **command-scoped**
``pinUvAuthParam`` over the canonical ``client_data_hash``, and threads it
through both ceremonies. There is **no bare-``uv`` fallback**; an authenticator
that cannot perform UV is rejected as incompatible (no UP-only downgrade —
RHAMP-REQ-034/035). The transient PIN handling is the client-side mechanism by
which "UV is satisfied inside the authenticator (PIN…)" (RHAMP-REQ-035) is
actually reachable for a PIN-based key; it introduces no normative-contract
change (the wire mechanics are a pinned-library detail, like COSE verify).
"""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass, field
from typing import Callable, Final, Optional, Protocol

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
    "build_virtual_ctap2_test_seam",
]

PRODUCTION_PROVIDER_KIND = "native-ctap2"
#: RHAMP-REQ-132 — USB-HID and NFC only. BLE / hybrid / platform excluded.
SUPPORTED_TRANSPORTS: Final[tuple[str, ...]] = ("usb", "nfc")

_ES256_ALG = -7  # COSE alg identifier for ES256 (RHAMP-REQ-043: ES256 only).

#: RHAMP-REQ-017 / §6 — the compiled-in relying-party id every PIN/UV token is
#: bound to. Never caller-selectable.
_PIN_UV_TOKEN_RP_ID: Final[str] = RP_ID


def _default_pin_prompt() -> str:
    """RHAMP-REQ-035 / §8 — trusted local PIN acquisition.

    No CLI argument, no environment variable, no repository / config value, no
    chat prompt. Hidden input via :mod:`getpass`; never logged, never persisted,
    never echoed, never placed on an exception or a RHAMP artifact. A
    non-interactive environment fails closed (no default PIN).
    """

    import getpass
    import sys

    if not (sys.stdin is not None and sys.stdin.isatty()):
        raise Ctap2UnavailableError(
            "a security-key PIN is required for user verification but no "
            "interactive terminal is available for trusted PIN entry"
        )
    try:
        return getpass.getpass("Enter your security-key PIN in the local trusted prompt: ")
    except (EOFError, KeyboardInterrupt) as exc:  # user aborted the prompt
        raise Ctap2CancelledError("PIN entry cancelled") from exc


def _map_pin_uv_ctap_error(exc: Exception) -> RhampTerminalError:
    """Map a ``ClientPin`` / PIN-UV ``CtapError`` onto an existing frozen
    terminal reason (RHAMP-REQ-149 / §18 / §49 — no new code). The PIN itself
    never appears in the returned message."""

    from fido2.ctap import CtapError

    if isinstance(exc, RhampTerminalError):
        return exc
    code = getattr(exc, "code", None)
    E = CtapError.ERR
    if code in (E.ACTION_TIMEOUT, E.USER_ACTION_TIMEOUT):
        return Ctap2CancelledError("user verification timed out", timed_out=True)
    if code == E.KEEPALIVE_CANCEL:
        return Ctap2CancelledError("user verification cancelled")
    if code in (E.PIN_INVALID, E.PIN_AUTH_INVALID, E.UV_INVALID):
        return Ctap2UnavailableError("user verification failed (invalid PIN / UV auth)")
    if code in (E.PIN_BLOCKED, E.PIN_AUTH_BLOCKED, E.UV_BLOCKED):
        return Ctap2UnavailableError("user verification unavailable (authenticator PIN/UV blocked)")
    if code == E.PIN_NOT_SET:
        return Ctap2UnavailableError(
            "authenticator has no PIN configured and no built-in UV; RHAMP-001 §10 forbids downgrade"
        )
    return Ctap2UnavailableError("CTAP2 PIN/UV protocol failure during user verification")


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

    def __init__(
        self,
        *,
        presence_timeout_s: float = 60.0,
        _connection_factory: Optional[Callable[[], object]] = None,
        _client_pin_factory: Optional[Callable[[object], object]] = None,
        _pin_prompt: Optional[Callable[[], str]] = None,
    ) -> None:
        """The three underscore-prefixed parameters are **test-only** seams for
        driving this production class against an in-memory protocol-faithful
        virtual authenticator (:func:`build_virtual_ctap2_test_seam`). They are
        never populated by :func:`resolve_production_ctap2_provider` and accept
        **no** environment variable / caller flag / repository value
        (RHAMP-REQ-048 / §63)."""

        self._presence_timeout_s = presence_timeout_s
        self._connection_factory = _connection_factory
        self._client_pin_factory = _client_pin_factory
        self._pin_prompt = _pin_prompt or _default_pin_prompt

    def _devices(self):
        from fido2.hid import CtapHidDevice

        try:
            return list(CtapHidDevice.list_devices())
        except Exception as exc:  # noqa: BLE001
            raise Ctap2UnavailableError(f"CTAP2 device enumeration failed: {exc}") from exc

    def available(self) -> bool:
        if self._connection_factory is not None:
            return True
        try:
            return bool(self._devices())
        except Ctap2UnavailableError:
            return False

    def _ctap2(self, device):
        from fido2.ctap2.base import Ctap2

        return Ctap2(device)

    def _open_ctap2(self):
        if self._connection_factory is not None:
            return self._connection_factory()
        devices = self._devices()
        if not devices:
            raise Ctap2UnavailableError("no CTAP2 authenticator attached")
        return self._ctap2(devices[0])

    def _client_pin(self, ctap2):
        if self._client_pin_factory is not None:
            return self._client_pin_factory(ctap2)
        from fido2.ctap2 import ClientPin

        return ClientPin(ctap2)

    def _obtain_pin_uv(
        self, ctap2, *, permission_name: str, client_data_hash: bytes
    ) -> tuple[bytes, int]:
        """RHAMP-REQ-033..036 / §8..§13 — negotiate the authenticator's
        supported PIN/UV protocol, acquire a permission-scoped, rp-bound
        PIN/UV token (built-in UV where advertised, otherwise a trusted local
        PIN), and derive a **command-scoped** ``pinUvAuthParam`` over
        ``client_data_hash``. No bare-``uv`` fallback; no UP-only downgrade.
        Returns ``(pin_uv_param, pin_uv_protocol_version)``."""

        from fido2.ctap import CtapError
        from fido2.ctap2 import ClientPin as _ClientPin

        info = ctap2.info
        options = dict(getattr(info, "options", {}) or {})
        builtin_uv = options.get("uv") is True
        client_pin_configured = options.get("clientPin") is True
        if not builtin_uv and not client_pin_configured:
            raise Ctap2UnavailableError(
                "authenticator cannot satisfy mandatory user verification (no built-in "
                "UV, no client PIN configured); RHAMP-001 §10 forbids any downgrade"
            )
        try:
            client_pin = self._client_pin(ctap2)
        except ValueError as exc:  # no mutually supported PIN/UV protocol
            raise Ctap2UnavailableError(
                f"no mutually supported CTAP2 PIN/UV protocol: {exc}"
            ) from exc

        protocol = client_pin.protocol
        protocol_version = int(protocol.VERSION)
        permission = {
            "make_credential": _ClientPin.PERMISSION.MAKE_CREDENTIAL,
            "get_assertion": _ClientPin.PERMISSION.GET_ASSERTION,
        }[permission_name]

        token: Optional[bytes] = None
        try:
            if builtin_uv:
                token = client_pin.get_uv_token(permission, _PIN_UV_TOKEN_RP_ID)
            else:
                pin = self._pin_prompt()
                try:
                    if not pin:
                        raise Ctap2UnavailableError(
                            "no security-key PIN was provided for user verification"
                        )
                    token = client_pin.get_pin_token(pin, permission, _PIN_UV_TOKEN_RP_ID)
                finally:
                    pin = None  # noqa: F841 — drop the PIN immediately
                    del pin
            pin_uv_param = protocol.authenticate(token, client_data_hash)
        except CtapError as exc:
            raise _map_pin_uv_ctap_error(exc) from exc
        except RhampTerminalError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise Ctap2UnavailableError(
                "CTAP2 PIN/UV protocol failure during user verification"
            ) from exc
        finally:
            token = None
            del token
        return pin_uv_param, protocol_version

    def make_credential(
        self, *, client_data_hash: bytes, user_id: bytes, user_name: str
    ) -> MakeCredentialResult:
        from fido2.ctap import CtapError

        ctap2 = self._open_ctap2()
        rp = {"id": RP_ID, "name": "PCAE HPAC"}
        user = {"id": user_id, "name": user_name, "displayName": user_name}
        key_params = [{"type": "public-key", "alg": ES256.ALGORITHM}]
        pin_uv_param, pin_uv_protocol = self._obtain_pin_uv(
            ctap2, permission_name="make_credential", client_data_hash=client_data_hash
        )
        # RHAMP-REQ-032/033/061 + finding H-1: non-discoverable (rk=False), no
        # bare "uv" option (removed in CTAP 2.1) — UV is asserted by the
        # command-scoped pinUvAuthParam. No attestation preference.
        options = {"rk": False}
        try:
            attestation = ctap2.make_credential(
                client_data_hash=client_data_hash,
                rp=rp,
                user=user,
                key_params=key_params,
                options=options,
                pin_uv_param=pin_uv_param,
                pin_uv_protocol=pin_uv_protocol,
            )
        except CtapError as exc:
            if exc.code in (
                CtapError.ERR.ACTION_TIMEOUT,
                CtapError.ERR.USER_ACTION_TIMEOUT,
            ):
                raise Ctap2CancelledError(str(exc), timed_out=True) from exc
            if exc.code == CtapError.ERR.KEEPALIVE_CANCEL:
                raise Ctap2CancelledError(str(exc)) from exc
            # No bare-"uv" retry — fail closed with a canonical reason.
            raise Ctap2UnavailableError(f"device rejected makeCredential: {exc}") from exc
        except RhampTerminalError:
            raise
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
        if not flags & AuthenticatorData.FLAG.UV:
            # RHAMP-REQ-034/035 — never accept a UP-only makeCredential.
            raise Ctap2UnavailableError(
                "makeCredential completed without user verification (FLAG.UV clear); "
                "RHAMP-001 §10 forbids a UP-only downgrade"
            )
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
        ctap2 = self._open_ctap2()
        allow_list = [{"type": "public-key", "id": cid} for cid in allow_credential_ids]
        pin_uv_param, pin_uv_protocol = self._obtain_pin_uv(
            ctap2, permission_name="get_assertion", client_data_hash=client_data_hash
        )
        try:
            # finding H-1: no bare "uv" option — UV is asserted by the
            # command-scoped pinUvAuthParam; the §37 verifier still enforces FLAG.UV.
            response = ctap2.get_assertion(
                rp_id=RP_ID,
                client_data_hash=client_data_hash,
                allow_list=allow_list,
                pin_uv_param=pin_uv_param,
                pin_uv_protocol=pin_uv_protocol,
            )
        except CtapError as exc:
            if exc.code in (CtapError.ERR.ACTION_TIMEOUT, CtapError.ERR.USER_ACTION_TIMEOUT):
                raise Ctap2CancelledError(str(exc), timed_out=True) from exc
            if exc.code == CtapError.ERR.KEEPALIVE_CANCEL:
                raise Ctap2CancelledError(str(exc)) from exc
            raise Ctap2UnavailableError(f"device rejected getAssertion: {exc}") from exc
        except RhampTerminalError:
            raise
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


# ─────────────────────────────────────────────────────────────────────────
# Protocol-faithful virtual CTAP2 authenticator (Phase .1R.30R.5R / finding
# H-1). NON_REAL. It models enough of the CTAP 2.1 wire contract to reject the
# exact request shapes a genuine FIDO_2_1 key rejects — a bare ``uv`` option,
# a missing / wrong ``pinUvAuthParam``, a wrong protocol, a permission
# mismatch, a wrong rp_id token binding — so the production PIN/UV code path in
# :class:`NativeCtap2Provider` is exercised without hardware. It is driven only
# through the test-only seams and can never be returned by
# :func:`resolve_production_ctap2_provider`.
# ─────────────────────────────────────────────────────────────────────────


class _DeterministicPinUvProtocol:
    """A deterministic stand-in for ``PinProtocolV2.authenticate`` used by the
    virtual authenticator and its virtual ClientPin. NOT cryptography that
    protects anything — a fixed keyed digest so the fixture can recompute and
    compare ``pinUvAuthParam``."""

    def __init__(self, version: int = 2) -> None:
        self.VERSION = int(version)

    def authenticate(self, key: bytes, message: bytes) -> bytes:
        return hmac.new(key, message, hashlib.sha256).digest()


@dataclass
class _VirtualInfo:
    options: dict
    pin_uv_protocols: list
    versions: tuple = ("U2F_V2", "FIDO_2_0", "FIDO_2_1_PRE", "FIDO_2_1")
    algorithms: tuple = ({"type": "public-key", "alg": _ES256_ALG},)


class _VirtualClientPin:
    """NON_REAL. Models ``ClientPin`` token issuance against a
    :class:`_VirtualCtap2Authenticator`."""

    SIMULATION_ONLY: Final[bool] = True
    PROVIDER_KIND_IS_REAL: Final[bool] = False

    def __init__(self, authenticator: "_VirtualCtap2Authenticator") -> None:
        self._auth = authenticator
        selected = next((v for v in (2, 1) if v in authenticator._pin_uv_protocols), None)
        if selected is None:
            raise ValueError("No compatible PIN/UV protocols supported!")
        self.protocol = _DeterministicPinUvProtocol(selected)

    def get_pin_token(self, pin, permissions=None, permissions_rpid=None):
        from fido2.ctap import CtapError

        a = self._auth
        if a._pin_blocked:
            raise CtapError(CtapError.ERR.PIN_BLOCKED)
        if not a._client_pin_configured:
            raise CtapError(CtapError.ERR.PIN_NOT_SET)
        if pin != a._pin:
            raise CtapError(CtapError.ERR.PIN_INVALID)
        return a._issue_token(permissions, permissions_rpid)

    def get_uv_token(self, permissions=None, permissions_rpid=None, event=None, on_keepalive=None):
        from fido2.ctap import CtapError

        a = self._auth
        if not a._builtin_uv:
            raise CtapError(CtapError.ERR.UV_INVALID)
        return a._issue_token(permissions, permissions_rpid)


class _VirtualCtap2Authenticator:
    """NON_REAL protocol-faithful model of a CTAP 2.1 roaming key."""

    SIMULATION_ONLY: Final[bool] = True
    PROVIDER_KIND_IS_REAL: Final[bool] = False

    def __init__(
        self,
        *,
        pin: str = "13795746",
        client_pin_configured: bool = True,
        builtin_uv: bool = False,
        pin_blocked: bool = False,
        pin_uv_protocols: tuple = (2, 1),
        up: bool = True,
        uv: bool = True,
        aaguid: bytes = b"\x11" * 16,
        start_sign_count: int = 0,
        sign_count_step: int = 1,
        wrong_rp_id_hash: bool = False,
    ) -> None:
        assert self.SIMULATION_ONLY is True
        self._pin = pin
        self._client_pin_configured = client_pin_configured
        self._builtin_uv = builtin_uv
        self._pin_blocked = pin_blocked
        self._pin_uv_protocols = tuple(pin_uv_protocols)
        self._up = up
        self._uv = uv
        self._aaguid = aaguid
        self._start_sign_count = start_sign_count
        self._sign_count_step = sign_count_step
        self._wrong_rp_id_hash = wrong_rp_id_hash
        self._credentials: dict[bytes, _VirtualCredential] = {}
        self._token: Optional[bytes] = None
        self._token_permissions = None
        self._token_rpid = None

    @property
    def info(self) -> _VirtualInfo:
        options: dict = {"pinUvAuthToken": True}
        if self._client_pin_configured:
            options["clientPin"] = True
        elif "clientPin" not in options and not self._builtin_uv:
            options["clientPin"] = False
        if self._builtin_uv:
            options["uv"] = True
        return _VirtualInfo(options=options, pin_uv_protocols=list(self._pin_uv_protocols))

    def _issue_token(self, permissions, permissions_rpid) -> bytes:
        self._token = os.urandom(32)
        self._token_permissions = permissions
        self._token_rpid = permissions_rpid
        return self._token

    def _check_pin_uv(self, pin_uv_param, pin_uv_protocol, client_data_hash, expected_permission, rp_id):
        from fido2.ctap import CtapError
        from fido2.ctap2 import ClientPin as _ClientPin

        if pin_uv_param is None:
            raise CtapError(CtapError.ERR.PUAT_REQUIRED)
        if pin_uv_protocol not in self._pin_uv_protocols:
            raise CtapError(CtapError.ERR.INVALID_PARAMETER)
        if self._token is None:
            raise CtapError(CtapError.ERR.PIN_AUTH_INVALID)
        expected = _DeterministicPinUvProtocol().authenticate(self._token, client_data_hash)
        if pin_uv_param != expected:
            raise CtapError(CtapError.ERR.PIN_AUTH_INVALID)
        if self._token_rpid is not None and self._token_rpid != rp_id:
            raise CtapError(CtapError.ERR.PIN_AUTH_INVALID)
        if (
            self._token_permissions is not None
            and not int(self._token_permissions) & int(expected_permission)
        ):
            raise CtapError(CtapError.ERR.PIN_AUTH_INVALID)

    def make_credential(
        self,
        client_data_hash,
        rp,
        user,
        key_params,
        exclude_list=None,
        extensions=None,
        options=None,
        pin_uv_param=None,
        pin_uv_protocol=None,
        *,
        event=None,
        on_keepalive=None,
    ):
        from cryptography.hazmat.primitives.asymmetric import ec
        from fido2.ctap import CtapError

        if options and "uv" in options:
            # exactly what a genuine FIDO_2_1 authenticator returns (0x2C).
            raise CtapError(CtapError.ERR.INVALID_OPTION)
        from fido2.ctap2 import ClientPin as _ClientPin

        self._check_pin_uv(
            pin_uv_param, pin_uv_protocol, client_data_hash,
            _ClientPin.PERMISSION.MAKE_CREDENTIAL, rp["id"],
        )
        priv = ec.generate_private_key(ec.SECP256R1())
        cose = ES256.from_cryptography_key(priv.public_key())
        cose_bytes = cbor.encode(cose)
        cred_id = hashlib.sha256(cose_bytes + os.urandom(16)).digest()
        self._credentials[cred_id] = _VirtualCredential(
            private_key=priv, cose_public_key=cose_bytes, sign_count=self._start_sign_count
        )
        acd = AttestedCredentialData.create(self._aaguid, cred_id, cose)
        flags = AuthenticatorData.FLAG.AT
        if self._up:
            flags |= AuthenticatorData.FLAG.UP
        if self._uv:
            flags |= AuthenticatorData.FLAG.UV
        auth_data = AuthenticatorData.create(RP_ID_HASH, flags, 0, bytes(acd))
        return _VirtualAttestation(auth_data)

    def get_assertion(
        self,
        rp_id,
        client_data_hash,
        allow_list=None,
        extensions=None,
        options=None,
        pin_uv_param=None,
        pin_uv_protocol=None,
        *,
        event=None,
        on_keepalive=None,
    ):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        from fido2.ctap import CtapError
        from fido2.ctap2 import ClientPin as _ClientPin

        if options and "uv" in options:
            raise CtapError(CtapError.ERR.INVALID_OPTION)
        self._check_pin_uv(
            pin_uv_param, pin_uv_protocol, client_data_hash,
            _ClientPin.PERMISSION.GET_ASSERTION, rp_id,
        )
        ids = [bytes(e["id"]) for e in (allow_list or [])]
        selected = next((c for c in ids if c in self._credentials), None)
        if selected is None:
            raise CtapError(CtapError.ERR.NO_CREDENTIALS)
        vcred = self._credentials[selected]
        vcred.sign_count += self._sign_count_step
        rp_hash = (
            RP_ID_HASH if not self._wrong_rp_id_hash
            else hashlib.sha256(b"attacker.example").digest()
        )
        flags = 0
        if self._up:
            flags |= AuthenticatorData.FLAG.UP
        if self._uv:
            flags |= AuthenticatorData.FLAG.UV
        auth_data = AuthenticatorData.create(rp_hash, flags, vcred.sign_count)
        signature = vcred.private_key.sign(
            bytes(auth_data) + client_data_hash, ec.ECDSA(hashes.SHA256())
        )
        return _VirtualAssertion(bytes(auth_data), signature, {"id": selected, "type": "public-key"})


@dataclass
class _VirtualAttestation:
    auth_data: object


@dataclass
class _VirtualAssertion:
    auth_data: bytes
    signature: bytes
    credential: dict


def build_virtual_ctap2_test_seam(
    *,
    supplied_pin: Optional[str] = None,
    **authenticator_kwargs,
) -> "tuple[NativeCtap2Provider, _VirtualCtap2Authenticator]":
    """TEST-ONLY. NON_REAL. Returns ``(provider, authenticator)`` where
    ``provider`` is a genuine :class:`NativeCtap2Provider` wired — via the
    underscore-prefixed seams only — to an in-memory protocol-faithful
    :class:`_VirtualCtap2Authenticator`. The production CTAP 2.1 PIN/UV code
    path runs unchanged; no hardware, no ``getpass``. Never reachable from
    :func:`resolve_production_ctap2_provider`."""

    auth = _VirtualCtap2Authenticator(**authenticator_kwargs)
    pin_value = supplied_pin if supplied_pin is not None else auth._pin

    def _prompt() -> str:
        return pin_value

    provider = NativeCtap2Provider(
        _connection_factory=lambda: auth,
        _client_pin_factory=lambda _ctap2: _VirtualClientPin(auth),
        _pin_prompt=_prompt,
    )
    return provider, auth


def resolve_production_ctap2_provider() -> NativeCtap2Provider:
    """RHAMP-REQ-048 / §63 — the **only** production selection path. It
    accepts **no** environment variable, caller flag, repository value, or
    config that could swap in the deterministic fixture. The deterministic
    provider is reachable **only** by explicit construction in test code."""

    return NativeCtap2Provider()
