from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.exceptions import (
    MailNotFoundError,
    MailServerError,
    MailValidationError,
)
from mailtmapi.http import HttpClient
from mailtmapi.providers.base import MailboxInfo, MailboxSpec
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.providers.temp_tf import TempTF
from mailtmapi.providers.temp_tf.service import (
    _clean_body_text,
    _extract_domains_from_html,
    _extract_syntaxes_from_html,
    _parse_message,
    _resolve_provider_and_syntax,
    _validate_temp_tf_address,
)
from mailtmapi.settings import Settings

SAMPLE_HTML = """
<!DOCTYPE html><html lang="en" class="dark"><head><title>temp.tf</title></head>
<body>
<div class="flex flex-wrap items-center gap-3 pt-0.5">
  <span class="font-mono text-xs uppercase tracking-wider text-slate-600 w-full sm:w-auto shrink-0">Providers</span>
  <label class="inline-flex items-center gap-2 font-mono text-sm text-slate-300 shrink-0 touch-manipulation cursor-pointer"><input type="checkbox" checked=""/><span>outlook.com</span></label>
  <label class="inline-flex items-center gap-2 font-mono text-sm text-slate-300 shrink-0 touch-manipulation cursor-pointer"><input type="checkbox" checked=""/><span>hotmail.com</span></label>
  <label class="inline-flex items-center gap-2 font-mono text-sm text-slate-300 shrink-0 touch-manipulation cursor-pointer"><input type="checkbox" checked=""/><span>gmail.com</span></label>
  <label class="inline-flex items-center gap-2 font-mono text-sm text-slate-300 shrink-0 touch-manipulation cursor-pointer"><input type="checkbox" checked=""/><span>high.edu.pl</span></label>
</div>
<div class="flex flex-wrap items-center gap-3 pt-0.5">
  <span class="font-mono text-xs uppercase tracking-wider text-slate-600 w-full sm:w-auto shrink-0">Syntaxes</span>
  <label class="inline-flex items-center gap-2 font-mono text-sm text-slate-300 shrink-0 touch-manipulation cursor-pointer" title="Dot in local part (Gmail only)"><input type="checkbox" checked=""/><span>dot</span></label>
  <label class="inline-flex items-center gap-2 font-mono text-sm text-slate-300 shrink-0 touch-manipulation cursor-pointer" title="Plus alias"><input type="checkbox" checked=""/><span>plus</span></label>
</div>
</body></html>
"""

# The EXACT check response payload provided in the original task prompt
PROMPT_CHECK_DATA = {
    "data": [
        {
            "subject": "Grok confirmation code: 865-662",
            "from": "noreply@x.ai",
            "date": "2026-10-31T00:24:45Z",
            "body": (
                '<html lang="en"><head>\r\n'
                '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
                '<meta content="IE=edge"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<style type="text/css">\r\n'
                '<!--\r\n'
                '#outlook a\r\n\t{padding:0}\r\n'
                '.ReadMsgBody\r\n\t{width:100%}\r\n'
                '.ExternalClass\r\n\t{width:100%}\r\n'
                'body\r\n\t{margin:0;padding:0}\r\n'
                'h1\r\n\t{font-family:-apple-system,system-ui,BlinkMacSystemFont;font-size:24px;font-weight:600;line-height:24px;text-align:left;color:#333333;padding-bottom:18px}\r\n'
                'p\r\n\t{font-family:-apple-system,system-ui,BlinkMacSystemFont;font-size:15px;font-weight:300;line-height:24px;text-align:left;color:#333333}\r\n'
                '-->\r\n'
                '</style></head><body style="background-color:#ffffff">'
                '<div style="background-color:#ffffff">'
                '<h1>Validate your email</h1>'
                '<p>Hi,</p>'
                '<p>Thank you for creating a Grok Account. Please use the code below to validate your email address.</p>'
                '<table><tr><td style="text-align:center; background:#FAFAFA; padding:30px 20px; font-size:26px; font-weight:bold">865-662</td></tr></table>'
                '<p>If you did not create a new account, please ignore this email.</p>'
                '<p>SpaceXSI Team</p>'
                '</div></body></html>'
            ),
            "bodyContentType": "html",
            "id": "895065865791524",
            "attachments": [],
        }
    ],
    "totalReceived": 6051174,
}


def _http(handler) -> HttpClient:
    http = HttpClient.__new__(HttpClient)
    http._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    return http


def _provider_with_routes(routes: dict[tuple[str, str], httpx.Response], **kwargs) -> TempTF:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        if key in routes:
            return routes[key]
        return httpx.Response(404, json={"detail": f"no mock for {key}"})

    http = _http(handler)
    return TempTF(http=http, **kwargs)


# -------------------------------------------------------------------------
# 1. HTML parsing tests (domains and syntaxes)
# -------------------------------------------------------------------------


def test_extract_domains_from_html():
    domains = _extract_domains_from_html(SAMPLE_HTML)
    assert domains == ["outlook.com", "hotmail.com", "gmail.com", "high.edu.pl"]


def test_extract_syntaxes_from_html():
    syntaxes = _extract_syntaxes_from_html(SAMPLE_HTML)
    assert syntaxes == ["dot", "plus"]


def test_extract_domains_from_empty_html_fallback():
    assert _extract_domains_from_html("") == ["outlook.com", "hotmail.com", "gmail.com", "high.edu.pl"]
    assert _extract_syntaxes_from_html("") == ["dot", "plus"]


@pytest.mark.asyncio
async def test_temp_tf_fetch_targets_from_html():
    routes = {
        ("GET", "/"): httpx.Response(200, text=SAMPLE_HTML, headers={"content-type": "text/html"}),
    }
    provider = _provider_with_routes(routes)
    targets = await provider.list_targets()
    assert len(targets) == 4
    labels = [t.label for t in targets]
    assert "outlook.com" in labels
    assert "hotmail.com" in labels
    assert "gmail.com" in labels
    assert "high.edu.pl" in labels
    assert all(t.kind == "domain" for t in targets)
    assert all(t.provider == "temp.tf" for t in targets)


@pytest.mark.asyncio
async def test_temp_tf_fetch_targets_fallback_on_error():
    routes = {
        ("GET", "/"): httpx.Response(500, text="Internal Server Error"),
    }
    provider = _provider_with_routes(routes)
    targets = await provider.list_targets()
    assert len(targets) == 4
    labels = [t.label for t in targets]
    assert "outlook.com" in labels
    assert "high.edu.pl" in labels


# -------------------------------------------------------------------------
# 2. Address validation & user feedback fix (tdvfscd@outlook.com prevention)
# -------------------------------------------------------------------------


def test_validate_address_outlook_requires_plus():
    # User feedback scenario: tdvfscd@outlook.com has no plus alias
    with pytest.raises(MailValidationError, match="requires a plus alias"):
        _validate_temp_tf_address("tdvfscd@outlook.com")

    # Valid plus alias works
    u, d = _validate_temp_tf_address("tdvfscd+tag123@outlook.com")
    assert u == "tdvfscd+tag123"
    assert d == "outlook.com"


def test_validate_address_hotmail_requires_plus():
    with pytest.raises(MailValidationError, match="requires a plus alias"):
        _validate_temp_tf_address("testuser@hotmail.com")

    u, d = _validate_temp_tf_address("testuser+alias@hotmail.com")
    assert u == "testuser+alias"
    assert d == "hotmail.com"


def test_validate_address_high_edu_pl_no_aliases():
    # high.edu.pl rejects plus alias
    with pytest.raises(MailValidationError, match="does not support dot or plus aliases"):
        _validate_temp_tf_address("user+tag@high.edu.pl")

    # high.edu.pl rejects dot alias
    with pytest.raises(MailValidationError, match="does not support dot or plus aliases"):
        _validate_temp_tf_address("first.last@high.edu.pl")

    # high.edu.pl rejects reserved usernames
    with pytest.raises(MailValidationError, match="is reserved"):
        _validate_temp_tf_address("admin@high.edu.pl")

    # high.edu.pl rejects username > 10 chars
    with pytest.raises(MailValidationError, match="must be 1-10 alphanumeric characters"):
        _validate_temp_tf_address("toolongusername123@high.edu.pl")

    # Valid 10-char alphanumeric high.edu.pl address
    u, d = _validate_temp_tf_address("stcm51lw4y@high.edu.pl")
    assert u == "stcm51lw4y"
    assert d == "high.edu.pl"


def test_validate_address_gmail_requires_dot_or_plus():
    with pytest.raises(MailValidationError, match="require a dot or plus alias"):
        _validate_temp_tf_address("plainuser@gmail.com")

    # Dot alias works
    u, d = _validate_temp_tf_address("first.last@gmail.com")
    assert u == "first.last"
    assert d == "gmail.com"

    # Plus alias works
    u, d = _validate_temp_tf_address("first+tag@gmail.com")
    assert u == "first+tag"
    assert d == "gmail.com"


def test_validate_address_unsupported_domain():
    with pytest.raises(MailValidationError, match="is not supported"):
        _validate_temp_tf_address("someone@yahoo.com")


@pytest.mark.asyncio
async def test_create_mailbox_custom_address_rejection():
    provider = _provider_with_routes({})
    # Attempting to register tdvfscd@outlook.com must fail with 400
    with pytest.raises(MailValidationError, match="requires a plus alias"):
        await provider.create_mailbox(MailboxSpec(address="tdvfscd@outlook.com"))


@pytest.mark.asyncio
async def test_create_mailbox_custom_address_valid():
    provider = _provider_with_routes({})
    spec = MailboxSpec(address="myuser+alias42@outlook.com")
    box = await provider.create_mailbox(spec)
    assert box.provider == "temp.tf"
    assert box.address == "myuser+alias42@outlook.com"
    assert box.provider_account_id == "myuser+alias42@outlook.com"


# -------------------------------------------------------------------------
# 3. Domain resolution and alias syntax parameters
# -------------------------------------------------------------------------


def test_resolve_provider_and_syntax():
    # outlook: dot=0, plus=1
    prov, dot, plus = _resolve_provider_and_syntax("outlook.com")
    assert (prov, dot, plus) == ("outlook", "0", "1")

    # hotmail: dot=0, plus=1
    prov, dot, plus = _resolve_provider_and_syntax("hotmail.com")
    assert (prov, dot, plus) == ("hotmail", "0", "1")

    # high.edu.pl: dot=0, plus=0
    prov, dot, plus = _resolve_provider_and_syntax("high.edu.pl")
    assert (prov, dot, plus) == ("high.edu.pl", "0", "0")

    # gmail default (dot=1, plus=1)
    prov, dot, plus = _resolve_provider_and_syntax("gmail.com", gmail_dot=True, gmail_plus=True)
    assert (prov, dot, plus) == ("gmail", "1", "1")

    # gmail dot-only via syntax modifier
    prov, dot, plus = _resolve_provider_and_syntax("gmail.com:dot")
    assert (prov, dot, plus) == ("gmail", "1", "0")

    # gmail plus-only via syntax modifier
    prov, dot, plus = _resolve_provider_and_syntax("gmail.com:plus")
    assert (prov, dot, plus) == ("gmail", "0", "1")

    # no domain specified -> all providers with dot=1, plus=1
    prov, dot, plus = _resolve_provider_and_syntax(None, gmail_dot=True, gmail_plus=True)
    assert "outlook" in prov
    assert "gmail" in prov
    assert (dot, plus) == ("1", "1")

    # unsupported domain raises 400 MailValidationError
    with pytest.raises(MailValidationError, match="unsupported domain"):
        _resolve_provider_and_syntax("unsupported.org")


@pytest.mark.asyncio
async def test_create_mailbox_domain_outlook():
    captured_params = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/account":
            captured_params.update(dict(request.url.params))
            return httpx.Response(200, json={"email": "testuser+alias123@outlook.com"})
        return httpx.Response(404)

    http = _http(handler)
    provider = TempTF(http=http)
    box = await provider.create_mailbox(MailboxSpec(domain="outlook.com"))
    assert captured_params["providers"] == "outlook"
    assert captured_params["dot"] == "0"
    assert captured_params["plus"] == "1"
    assert box.address == "testuser+alias123@outlook.com"


@pytest.mark.asyncio
async def test_create_mailbox_domain_high_edu_pl():
    captured_params = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/account":
            captured_params.update(dict(request.url.params))
            return httpx.Response(200, json={"email": "stcm51lw4y@high.edu.pl"})
        return httpx.Response(404)

    http = _http(handler)
    provider = TempTF(http=http)
    box = await provider.create_mailbox(MailboxSpec(domain="high.edu.pl"))
    assert captured_params["providers"] == "high.edu.pl"
    assert captured_params["dot"] == "0"
    assert captured_params["plus"] == "0"
    assert box.address == "stcm51lw4y@high.edu.pl"


@pytest.mark.asyncio
async def test_create_mailbox_domain_gmail_modifiers():
    captured_params_list = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/account":
            captured_params_list.append(dict(request.url.params))
            return httpx.Response(200, json={"email": "test.user+alias@gmail.com"})
        return httpx.Response(404)

    http = _http(handler)
    provider = TempTF(http=http)

    # 1. Plain gmail.com
    await provider.create_mailbox(MailboxSpec(domain="gmail.com"))
    assert captured_params_list[-1]["dot"] == "1"
    assert captured_params_list[-1]["plus"] == "1"

    # 2. gmail.com:dot
    await provider.create_mailbox(MailboxSpec(domain="gmail.com:dot"))
    assert captured_params_list[-1]["dot"] == "1"
    assert captured_params_list[-1]["plus"] == "0"

    # 3. gmail.com:plus
    await provider.create_mailbox(MailboxSpec(domain="gmail.com:plus"))
    assert captured_params_list[-1]["dot"] == "0"
    assert captured_params_list[-1]["plus"] == "1"


# -------------------------------------------------------------------------
# 4. Message cleaning and parsing (Real Prompt Payload with <style>)
# -------------------------------------------------------------------------


def test_clean_body_text_strips_styles_and_comments():
    raw_html = (
        '<html><head><style type="text/css">body { color: #333; font-size: 14px; }</style></head>'
        '<body><!-- comment --><h1>Title</h1><p>Hello world.</p></body></html>'
    )
    cleaned = _clean_body_text(raw_html)
    assert "color: #333" not in cleaned
    assert "font-size" not in cleaned
    assert "comment" not in cleaned
    assert "Title" in cleaned
    assert "Hello world." in cleaned


def test_parse_message_prompt_payload():
    msg = _parse_message(PROMPT_CHECK_DATA["data"][0], "testuser+alias@outlook.com", "https://temp.tf")
    assert msg.id == "895065865791524"
    assert msg.subject == "Grok confirmation code: 865-662"
    assert msg.from_.address == "noreply@x.ai"
    assert msg.to[0].address == "testuser+alias@outlook.com"
    # Intro must be clean text, not CSS styles
    assert msg.intro == "Validate your email"
    assert "#outlook" not in msg.intro
    assert "color:#333333" not in msg.intro
    # Text must contain the verification code
    assert "865-662" in msg.text
    assert "#outlook a" not in msg.text
    # Raw HTML is preserved in html list
    assert len(msg.html) == 1
    assert "SpaceXSI" in msg.html[0]


# -------------------------------------------------------------------------
# 5. Security & Isolation: Mailbox-scoped message cache
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mailbox_message_isolation():
    """Ensure Mailbox B cannot access or delete messages belonging to Mailbox A."""
    box_a = MailboxInfo(
        provider="temp.tf",
        address="user_a+tag1@outlook.com",
        token="",
        provider_account_id="user_a+tag1@outlook.com",
    )
    box_b = MailboxInfo(
        provider="temp.tf",
        address="user_b+tag2@outlook.com",
        token="",
        provider_account_id="user_b+tag2@outlook.com",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/check":
            import json
            req_data = json.loads(request.content)
            if req_data.get("email") == box_a.address:
                return httpx.Response(200, json=PROMPT_CHECK_DATA)
            return httpx.Response(200, json={"data": [], "totalReceived": 0})
        return httpx.Response(404)

    http = _http(handler)
    provider = TempTF(http=http)

    # Box A lists messages (message 895065865791524 is loaded into cache)
    msgs_a = await provider.list_messages(box_a)
    assert len(msgs_a) == 1
    assert msgs_a[0].id == "895065865791524"

    # Box A can access its own message
    detail_a = await provider.get_message(box_a, "895065865791524")
    assert detail_a.id == "895065865791524"

    # Box B queries Box A's message -> MUST raise MailNotFoundError!
    with pytest.raises(MailNotFoundError, match="not found for user_b\\+tag2@outlook.com"):
        await provider.get_message(box_b, "895065865791524")

    # Box B cannot delete Box A's message
    await provider.delete_message(box_b, "895065865791524")
    assert "895065865791524" in provider._messages[box_a.address]

    # Deleting Box A removes its cache
    await provider.delete_mailbox(box_a)
    assert box_a.address not in provider._messages


# -------------------------------------------------------------------------
# 6. Error handling in list_messages
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_messages_404_returns_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "Not found"})

    http = _http(handler)
    provider = TempTF(http=http)
    box = MailboxInfo(provider="temp.tf", address="u+1@outlook.com", token="")
    messages = await provider.list_messages(box)
    assert messages == []


@pytest.mark.asyncio
async def test_list_messages_403_returns_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "Forbidden"})

    http = _http(handler)
    provider = TempTF(http=http)
    box = MailboxInfo(provider="temp.tf", address="u+1@outlook.com", token="")
    messages = await provider.list_messages(box)
    assert messages == []


@pytest.mark.asyncio
async def test_list_messages_500_raises_server_error():
    """Server errors must NOT be silently swallowed as empty lists."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="Bad Gateway")

    http = _http(handler)
    provider = TempTF(http=http)
    box = MailboxInfo(provider="temp.tf", address="u+1@outlook.com", token="")
    with pytest.raises(MailServerError):
        await provider.list_messages(box)


# -------------------------------------------------------------------------
# 7. Attachment parsing and download URL encoding
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_attachment_parsing_and_encoding():
    att_data = {
        "data": [
            {
                "id": "msg_att_1",
                "subject": "Invoice Attached",
                "from": "accounting@company.com",
                "date": "2026-10-31T01:00:00Z",
                "body": "Please find invoice attached.",
                "bodyContentType": "text",
                "attachments": [
                    {
                        "id": "att_999",
                        "name": "invoice.pdf",
                        "contentType": "application/pdf",
                        "size": 12345,
                    }
                ],
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=att_data)

    http = _http(handler)
    provider = TempTF(http=http)
    box = MailboxInfo(provider="temp.tf", address="user+plus1@outlook.com", token="")

    msgs = await provider.list_messages(box)
    assert len(msgs) == 1
    assert msgs[0].has_attachments is True

    detail = await provider.get_message(box, "msg_att_1")
    assert len(detail.attachments) == 1
    att = detail.attachments[0]
    assert att.id == "att_999"
    assert att.filename == "invoice.pdf"
    assert att.content_type == "application/pdf"
    assert att.size == 12345
    # Verification: + in email is properly urlencoded as %2B in download_url
    assert "user%2Bplus1%40outlook.com" in att.download_url
    assert "messageId=msg_att_1" in att.download_url
    assert "attachmentId=att_999" in att.download_url


# -------------------------------------------------------------------------
# 8. Full FastAPI app e2e integration flow
# -------------------------------------------------------------------------


def test_temp_tf_app_e2e(tmp_path):
    db_file = tmp_path / "test_temp_tf.db"
    settings = Settings(
        api_key="",
        database_url=f"sqlite+aiosqlite:///{db_file.as_posix()}",
        secret_key="0" * 32,
        domain_cache_enabled=False,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/account":
            return httpx.Response(200, json={"email": "appuser+alias456@outlook.com"})
        if request.url.path == "/api/check":
            return httpx.Response(200, json=PROMPT_CHECK_DATA)
        if request.url.path == "/":
            return httpx.Response(200, text=SAMPLE_HTML, headers={"content-type": "text/html"})
        return httpx.Response(404)

    http = _http(handler)
    provider = TempTF(http=http)
    registry = ProviderRegistry([provider])
    app = create_app(settings=settings)

    with TestClient(app) as client:
        app.state.registry = registry
        app.state.http = http

        # 1. Validation test: trying to create invalid address tdvfscd@outlook.com returns 400!
        resp_invalid = client.post(
            "/v1/mailboxes",
            json={"provider": "temp.tf", "address": "tdvfscd@outlook.com"},
        )
        assert resp_invalid.status_code == 400
        assert "requires a plus alias" in resp_invalid.text

        # 2. Valid creation by domain
        resp = client.post("/v1/mailboxes", json={"provider": "temp.tf", "domain": "outlook.com"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["provider"] == "temp.tf"
        assert data["address"] == "appuser+alias456@outlook.com"
        mailbox_id = data["id"]

        # 3. List messages
        resp = client.get(f"/v1/mailboxes/{mailbox_id}/messages")
        assert resp.status_code == 200, resp.text
        messages = resp.json()
        assert len(messages) == 1
        assert messages[0]["message_api_id"] == "895065865791524"
        assert messages[0]["subject"] == "Grok confirmation code: 865-662"

        # 4. Get message detail
        resp = client.get(f"/v1/mailboxes/{mailbox_id}/messages/895065865791524")
        assert resp.status_code == 200, resp.text
        msg_detail = resp.json()
        assert "865-662" in msg_detail["text"]
        assert "#outlook" not in msg_detail["text"]
        assert len(msg_detail["html"]) == 1

        # 5. Get message source
        resp = client.get(f"/v1/mailboxes/{mailbox_id}/messages/895065865791524/source")
        assert resp.status_code == 200, resp.text
        src = resp.json()
        assert "<html" in src["data"]
