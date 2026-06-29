# Phase 92D.2 — Telegram Payload Compatibility Repair

```
phase_name    = phase_92d_2_telegram_payload_compatibility_repair
phase_version = 1.0
phase_status  = completed
implementation_status = corrective_repair
recommended_next_phase = 93C — Shell Gate Audit Evidence Model
```

## 1. Purpose

Fix PCAE Telegram outbound delivery so `pcae notify send-report --latest` works with the same Telegram bot token/chat ID that already succeeds via direct curl.

## 2. Root Cause

**`parse_mode: "Markdown"` in `_send_message()` was the root cause.**

The `_send_message()` method in `TelegramSink` (Phase 92C) was sending:

```python
payload = {
    "chat_id": self._chat_id,
    "text": text,
    "parse_mode": "Markdown",  # ← ROOT CAUSE
}
```

The phase report summary text starts with `[INFO]`, `[COMPLETED]`, `[FAILED]`, etc. — square bracket patterns that Telegram's Markdown parser interprets as link markup. When the text contains unclosed or invalid Markdown entities, Telegram returns `HTTP 400: Bad Request` with description `"can't parse entities"`.

The known-good `curl` command worked because it sends plain text (no `parse_mode`):
```bash
curl -d "chat_id=..." --data-urlencode "text=..."
```

### Secondary Issue: Error Reporting

When Telegram returned HTTP 400, `_api_call()` caught the `URLError` and returned `{"ok": False, "error": str(exc)}`. This produced: `"HTTP Error 400: Bad Request"` — losing the Telegram `description` field that would have revealed the Markdown parsing issue.

## 3. Known-Good curl Comparison

| Aspect | curl (known-good) | PCAE (before) | PCAE (after) |
|--------|------------------|---------------|--------------|
| HTTP method | POST | POST | POST |
| Content-Type | `application/x-www-form-urlencoded` | `application/json` | `application/x-www-form-urlencoded` |
| Body format | `chat_id=...&text=...` | `{"chat_id":"...","text":"...","parse_mode":"Markdown"}` | `chat_id=...&text=...` |
| parse_mode | (none) | `Markdown` | (none) |
| Error detail | (N/A) | `HTTP Error 400: Bad Request` | `Telegram: can't parse entities` |

## 4. Request Encoding Repair

### 4.1 sendMessage: URL-encoded form data

Changed `_send_message()` to use `application/x-www-form-urlencoded` with `urllib.parse.urlencode()`:

```python
def _send_message(self, text: str) -> dict:
    from urllib.parse import urlencode
    payload_bytes = urlencode({
        "chat_id": self._chat_id,
        "text": text,
    }).encode()
    return self._api_call_form("sendMessage", payload_bytes)
```

### 4.2 No parse_mode

`parse_mode` is not sent. Plain text avoids all Markdown/HTML entity parsing errors. The Telegram API defaults to plain text when `parse_mode` is absent.

### 4.3 New `_api_call_form()` method

Added a dedicated form-data API caller that sends `Content-Type: application/x-www-form-urlencoded` and includes full HTTP error body capture.

## 5. Error-Body Reporting

### 5.1 Before

```python
except URLError as exc:
    return {"ok": False, "error": str(exc)}
# Result: "HTTP Error 400: Bad Request"
```

### 5.2 After

```python
except HTTPError as exc:
    error_body = ""
    try:
        error_body = exc.read().decode()
        error_data = json.loads(error_body)
        telegram_desc = error_data.get("description", "")
        if telegram_desc:
            return {"ok": False, "error": f"Telegram: {telegram_desc}"}
    except Exception:
        pass
    return {"ok": False, "error": f"HTTP {exc.code}: {exc.reason}"}
# Result: "Telegram: Bad Request: can't parse entities"
```

The Telegram `description` field is now captured and surfaced in `NotificationResult.error`. This applies to all three API methods: `_api_call` (JSON), `_api_call_form` (URL-encoded), and `_api_call_multipart` (multipart).

## 6. Secret Redaction

- Bot token and chat ID are read from environment variables only — never hardcoded
- `_build_summary()` and `_send_message()` text never include token or chat ID
- Error messages from Telegram do not include token (Telegram API returns `Unauthorized` without the token)
- Chat ID is not included in the human-readable error output (only in the URL, which is not printed)
- Test `test_token_not_leaked_in_error` verifies token absence
- Test `test_chat_id_not_leaked_in_error` verifies chat ID absence

## 7. Manual Verification

After the repair and with env vars configured:

```
$ pcae notify send-report --latest
Telegram send-report: Narrow Shell Gate Prototype — completed
  [OK] Telegram: summary sent, document sent
```

JSON output:
```json
{
  "results": [{
    "sink_name": "telegram",
    "success": true,
    "message": "Telegram: summary sent, document sent",
    "metadata": {
      "send_message_ok": true,
      "send_document_ok": true
    },
    "error": null
  }]
}
```

## 8. No-Go Conditions

- No Telegram polling, webhooks, or inbound command reception
- No `/run`, `/commit`, `/push`, or remote shell from Telegram
- No shell interception or wrappers
- No backend invocation
- No enforcement
- No real network calls in tests (all HTTP mocked)
- No token or chat ID leakage in output

## 9. Test Coverage

| Test | Category |
|------|----------|
| `test_send_message_uses_url_encoded_form` | Payload format |
| `test_no_parse_mode_in_send_message` | parse_mode removal |
| `test_markdown_brackets_dont_break` | Markdown safety |
| `test_send_message_success_proceeds_to_document` | sendDocument flow |
| `test_http_400_error_body_captured` | Error body capture |
| `test_http_error_without_body_handled` | Error fallback |
| `test_token_not_leaked_in_error` | Secret redaction |
| `test_chat_id_not_leaked_in_error` | Secret redaction |
| `test_truncation_still_works` | Summary truncation |
| `test_truncation_ellipsis` | Truncation detail |

10 new tests added to existing 20 = 30 total Telegram tests.

---

*Phase 92D.2 is a corrective repair for the 92C/92D Telegram outbound notification path. No Telegram polling, inbound commands, remote shell, /run, command execution, shell interception, wrappers, backend invocation, or enforcement was implemented. Recommended next phase: 93C — Shell Gate Audit Evidence Model.*
