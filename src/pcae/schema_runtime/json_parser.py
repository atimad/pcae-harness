"""Strict, duplicate-key-rejecting JSON parser (Layer-1).

Phase 136F prerequisite infrastructure. A hand-rolled recursive-descent
parser is used, rather than ``json.loads`` with ``object_pairs_hook``,
because the latter cannot report a JSON-Pointer instance path for a
rejected duplicate key (hooks fire bottom-up with no ancestor context).
Value grammar (strings, numbers, literals) follows RFC 8259; ``NaN``,
``Infinity``, and ``-Infinity`` -- accepted by ``json.loads`` as a
non-standard extension -- are rejected explicitly with a distinct error
code rather than silently parsed.

This module:

* accepts bytes or text through explicit APIs;
* requires UTF-8 for bytes;
* rejects duplicate object keys at every nesting level;
* rejects invalid JSON;
* rejects non-finite numbers;
* optionally requires a top-level object;
* imposes a configurable input-size limit;
* imposes a configurable object/array nesting-depth limit (Phase 136G
  repair: closes an uncaught-``RecursionError`` gap found by independent
  adversarial testing -- see ``DEFAULT_MAX_NESTING_DEPTH`` in
  ``limits.py``);
* does not access the network, follow paths, or mutate input;
* returns a structured :class:`JsonParseResult`, never raising on
  ordinary invalid input.
"""
from __future__ import annotations

from .limits import DEFAULT_MAX_INPUT_BYTES, DEFAULT_MAX_NESTING_DEPTH
from .models import JsonParseResult, OutcomeStatus, ValidationIssue

_WHITESPACE = " \t\n\r"
_ESCAPES = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


class _StrictJsonError(Exception):
    def __init__(self, code: str, message: str, path: tuple[str, ...]) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path


def _is_ascii_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def _json_pointer(path: tuple[str, ...]) -> str:
    if not path:
        return ""
    escaped = [segment.replace("~", "~0").replace("/", "~1") for segment in path]
    return "/" + "/".join(escaped)


class _Parser:
    """Minimal recursive-descent JSON parser with duplicate-key tracking."""

    __slots__ = ("text", "length", "pos", "max_depth")

    def __init__(self, text: str, max_depth: int = DEFAULT_MAX_NESTING_DEPTH) -> None:
        self.text = text
        self.length = len(text)
        self.pos = 0
        self.max_depth = max_depth

    def parse(self) -> object:
        self._skip_ws()
        value = self._parse_value(())
        self._skip_ws()
        if self.pos != self.length:
            raise _StrictJsonError("invalid_json", "Unexpected trailing data after JSON value", ())
        return value

    def _skip_ws(self) -> None:
        text, length = self.text, self.length
        pos = self.pos
        while pos < length and text[pos] in _WHITESPACE:
            pos += 1
        self.pos = pos

    def _parse_value(self, path: tuple[str, ...]) -> object:
        if self.pos >= self.length:
            raise _StrictJsonError("invalid_json", "Unexpected end of input", path)
        ch = self.text[self.pos]
        if ch == "{":
            return self._parse_object(path)
        if ch == "[":
            return self._parse_array(path)
        if ch == '"':
            return self._parse_string(path)
        if self.text.startswith("-Infinity", self.pos):
            raise _StrictJsonError(
                "non_finite_number", "Non-finite number literal '-Infinity' is not permitted", path
            )
        if ch == "-" or _is_ascii_digit(ch):
            return self._parse_number(path)
        if self.text.startswith("true", self.pos):
            self.pos += 4
            return True
        if self.text.startswith("false", self.pos):
            self.pos += 5
            return False
        if self.text.startswith("null", self.pos):
            self.pos += 4
            return None
        if self.text.startswith("NaN", self.pos):
            raise _StrictJsonError("non_finite_number", "Non-finite number literal 'NaN' is not permitted", path)
        if self.text.startswith("Infinity", self.pos):
            raise _StrictJsonError(
                "non_finite_number", "Non-finite number literal 'Infinity' is not permitted", path
            )
        raise _StrictJsonError("invalid_json", f"Unexpected character {ch!r}", path)

    def _check_depth(self, path: tuple[str, ...]) -> None:
        if len(path) > self.max_depth:
            raise _StrictJsonError(
                "invalid_json",
                f"Maximum object/array nesting depth of {self.max_depth} exceeded",
                path,
            )

    def _parse_object(self, path: tuple[str, ...]) -> dict:
        self._check_depth(path)
        self.pos += 1  # consume '{'
        obj: dict = {}
        self._skip_ws()
        if self.pos < self.length and self.text[self.pos] == "}":
            self.pos += 1
            return obj
        while True:
            self._skip_ws()
            if self.pos >= self.length or self.text[self.pos] != '"':
                raise _StrictJsonError("invalid_json", "Expected string object key", path)
            key = self._parse_string(path)
            self._skip_ws()
            if self.pos >= self.length or self.text[self.pos] != ":":
                raise _StrictJsonError("invalid_json", "Expected ':' after object key", path + (key,))
            self.pos += 1
            self._skip_ws()
            child_path = path + (key,)
            value = self._parse_value(child_path)
            if key in obj:
                raise _StrictJsonError("duplicate_key", f"Duplicate object key {key!r}", child_path)
            obj[key] = value
            self._skip_ws()
            if self.pos >= self.length:
                raise _StrictJsonError("invalid_json", "Unexpected end of input in object", path)
            ch = self.text[self.pos]
            if ch == ",":
                self.pos += 1
                continue
            if ch == "}":
                self.pos += 1
                return obj
            raise _StrictJsonError("invalid_json", "Expected ',' or '}' in object", path)

    def _parse_array(self, path: tuple[str, ...]) -> list:
        self._check_depth(path)
        self.pos += 1  # consume '['
        arr: list = []
        self._skip_ws()
        if self.pos < self.length and self.text[self.pos] == "]":
            self.pos += 1
            return arr
        index = 0
        while True:
            self._skip_ws()
            child_path = path + (str(index),)
            value = self._parse_value(child_path)
            arr.append(value)
            index += 1
            self._skip_ws()
            if self.pos >= self.length:
                raise _StrictJsonError("invalid_json", "Unexpected end of input in array", path)
            ch = self.text[self.pos]
            if ch == ",":
                self.pos += 1
                continue
            if ch == "]":
                self.pos += 1
                return arr
            raise _StrictJsonError("invalid_json", "Expected ',' or ']' in array", path)

    def _parse_string(self, path: tuple[str, ...]) -> str:
        # Caller has already confirmed text[pos] == '"'.
        self.pos += 1
        chars: list[str] = []
        text, length = self.text, self.length
        while True:
            if self.pos >= length:
                raise _StrictJsonError("invalid_json", "Unterminated string", path)
            ch = text[self.pos]
            if ch == '"':
                self.pos += 1
                return "".join(chars)
            if ch == "\\":
                self.pos += 1
                if self.pos >= length:
                    raise _StrictJsonError("invalid_json", "Unterminated escape sequence", path)
                esc = text[self.pos]
                if esc == "u":
                    code_point = self._parse_unicode_escape(path)
                    if 0xD800 <= code_point <= 0xDBFF and text[self.pos : self.pos + 2] == "\\u":
                        saved_pos = self.pos
                        self.pos += 2
                        low = self._parse_unicode_escape(path)
                        if 0xDC00 <= low <= 0xDFFF:
                            code_point = 0x10000 + (code_point - 0xD800) * 0x400 + (low - 0xDC00)
                        else:
                            self.pos = saved_pos
                    chars.append(chr(code_point))
                    continue
                mapped = _ESCAPES.get(esc)
                if mapped is None:
                    raise _StrictJsonError("invalid_json", f"Invalid escape character {esc!r}", path)
                chars.append(mapped)
                self.pos += 1
                continue
            if ord(ch) < 0x20:
                raise _StrictJsonError("invalid_json", "Unescaped control character in string", path)
            chars.append(ch)
            self.pos += 1

    def _parse_unicode_escape(self, path: tuple[str, ...]) -> int:
        # Caller has already consumed the 'u'; self.pos points at 'u'.
        hex_digits = self.text[self.pos + 1 : self.pos + 5]
        if len(hex_digits) != 4:
            raise _StrictJsonError("invalid_json", "Invalid \\u escape", path)
        try:
            code_point = int(hex_digits, 16)
        except ValueError:
            raise _StrictJsonError("invalid_json", "Invalid \\u escape", path) from None
        self.pos += 5
        return code_point

    def _parse_number(self, path: tuple[str, ...]) -> object:
        text, length = self.text, self.length
        start = self.pos
        pos = self.pos
        if pos < length and text[pos] == "-":
            pos += 1
        if pos >= length or not _is_ascii_digit(text[pos]):
            raise _StrictJsonError("invalid_json", "Invalid number literal", path)
        if text[pos] == "0":
            pos += 1
        else:
            while pos < length and _is_ascii_digit(text[pos]):
                pos += 1
        is_float = False
        if pos < length and text[pos] == ".":
            is_float = True
            pos += 1
            if pos >= length or not _is_ascii_digit(text[pos]):
                raise _StrictJsonError("invalid_json", "Invalid number literal", path)
            while pos < length and _is_ascii_digit(text[pos]):
                pos += 1
        if pos < length and text[pos] in "eE":
            is_float = True
            pos += 1
            if pos < length and text[pos] in "+-":
                pos += 1
            if pos >= length or not _is_ascii_digit(text[pos]):
                raise _StrictJsonError("invalid_json", "Invalid number literal", path)
            while pos < length and _is_ascii_digit(text[pos]):
                pos += 1
        raw = text[start:pos]
        self.pos = pos
        return float(raw) if is_float else int(raw)


def _failure(code: str, message: str, path: tuple[str, ...]) -> JsonParseResult:
    issue = ValidationIssue(code=code, message=message, instance_path=_json_pointer(path))
    return JsonParseResult(status=OutcomeStatus.INVALID, value=None, errors=(issue,))


def parse_strict_json(
    data: bytes | str,
    *,
    max_bytes: int = DEFAULT_MAX_INPUT_BYTES,
    require_top_level_object: bool = False,
    max_depth: int = DEFAULT_MAX_NESTING_DEPTH,
) -> JsonParseResult:
    """Strictly parse ``data`` as JSON.

    Duplicate object keys, non-finite number literals, and malformed
    JSON are reported through the returned :class:`JsonParseResult`
    rather than raised. ``TypeError`` is raised only for programmer
    misuse (an argument that is neither ``bytes`` nor ``str``).
    """
    if isinstance(data, bytes):
        if len(data) > max_bytes:
            return _failure("input_too_large", f"Input exceeds maximum of {max_bytes} bytes", ())
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            return _failure("invalid_utf8", f"Input is not valid UTF-8: {exc}", ())
    elif isinstance(data, str):
        if len(data.encode("utf-8")) > max_bytes:
            return _failure("input_too_large", f"Input exceeds maximum of {max_bytes} bytes", ())
        text = data
    else:
        raise TypeError(f"parse_strict_json expects bytes or str, got {type(data).__name__}")

    try:
        value = _Parser(text, max_depth=max_depth).parse()
    except _StrictJsonError as exc:
        return _failure(exc.code, exc.message, exc.path)

    if require_top_level_object and not isinstance(value, dict):
        return _failure("top_level_not_object", "Top-level JSON value must be an object", ())

    return JsonParseResult(status=OutcomeStatus.VALID, value=value, errors=())
