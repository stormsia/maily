import React from 'react';
import { CodeBlock } from '../../components/common/CodeBlock';
import { Callout } from '../../components/common/Callout';
import { Link } from '../../context/RouterContext';
import { ArrowRight, Code2, Layers, CheckCircle2, Terminal } from 'lucide-react';
import { GithubIcon } from '../../components/common/Icons';

export const DocsAddingProviders: React.FC = () => {
  return (
    <div className="space-y-10">
      {/* Header */}
      <section>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-xs font-mono mb-4">
          <span>Extension Guide · Custom Providers</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-display" id="provider-architecture">
            Custom Provider Implementation Guide
          </h2>
          <a
            href="https://github.com/stormsia/maily/blob/main/docs/ADDING_PROVIDERS.md"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 shadow-sm transition-all self-start sm:self-auto"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>Guide in GitHub Repo ↗</span>
          </a>
        </div>
        <p className="text-base leading-relaxed text-slate-300">
          Maily employs a modular provider adapter pattern. Implementing a new disposable mail service requires subclassing the <code className="text-cyan-400 font-mono">BaseProvider</code> abstract base class and registering it with the central <code className="text-cyan-400 font-mono">ProviderRegistry</code>.
        </p>
      </section>

      {/* Step 1: BaseProvider Interface */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="base-provider-interface">
          Step 1: Subclassing <code className="font-mono text-cyan-400">BaseProvider</code>
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Create a new file in <code className="text-cyan-400 font-mono">src/maily/providers/custom_service.py</code> and implement the core lifecycle methods:
        </p>
        <CodeBlock
          language="python"
          filename="src/maily/providers/custom_service.py"
          code={`from typing import List, Optional, AsyncIterator
import httpx
from maily.providers.base import BaseProvider
from maily.models import Mailbox, Message, Attachment
from maily.exceptions import UpstreamProviderError, RateLimitError

class CustomService(BaseProvider):
    name = "custom_service"
    capabilities = {
        "custom_username": True,
        "custom_domain": True,
        "password_auth": False,
        "sse_stream": False,
        "attachments": True,
    }

    def __init__(self, base_url: str = "https://api.custom-tempmail.dev"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=15.0)

    async def get_domains(self) -> List[str]:
        """Query upstream API to discover active public domains."""
        try:
            resp = await self.client.get(f"{self.base_url}/domains")
            resp.raise_for_status()
            return resp.json().get("domains", ["custommail.dev"])
        except httpx.HTTPStatusError as exc:
            raise UpstreamProviderError(f"Failed to fetch domains: {exc}")

    async def create_mailbox(self, username: str, domain: str) -> Mailbox:
        """Provision a new ephemeral mailbox."""
        payload = {"username": username, "domain": domain}
        resp = await self.client.post(f"{self.base_url}/inboxes", json=payload)
        if resp.status_code == 429:
            raise RateLimitError("Upstream rate limit reached")
        resp.raise_for_status()
        data = resp.json()

        return Mailbox(
            address=f"{username}@{domain}",
            provider=self.name,
            token=data.get("auth_token", ""),
        )

    async def get_messages(self, mailbox: Mailbox) -> List[Message]:
        """Fetch incoming message list for the mailbox."""
        headers = {"Authorization": f"Bearer {mailbox.token}"}
        resp = await self.client.get(f"{self.base_url}/inboxes/{mailbox.address}/messages", headers=headers)
        resp.raise_for_status()

        messages = []
        for item in resp.json():
            messages.append(Message(
                id=str(item["id"]),
                mailbox_id=mailbox.id,
                from_address=item["sender"],
                subject=item.get("subject", ""),
                intro=item.get("snippet", ""),
                created_at=item["date"],
            ))
        return messages

    async def get_message(self, mailbox: Mailbox, message_id: str) -> Message:
        """Fetch full email content (text, html, and attachments)."""
        headers = {"Authorization": f"Bearer {mailbox.token}"}
        resp = await self.client.get(f"{self.base_url}/messages/{message_id}", headers=headers)
        resp.raise_for_status()
        data = resp.json()

        return Message(
            id=message_id,
            mailbox_id=mailbox.id,
            from_address=data["from"],
            subject=data.get("subject", ""),
            text=data.get("text_body", ""),
            html=data.get("html_body", ""),
            created_at=data["created_at"],
            attachments=[
                Attachment(
                    id=att["id"],
                    filename=att["filename"],
                    content_type=att["mime_type"],
                    size=att["size"],
                    download_url=f"/v1/mailboxes/{mailbox.id}/messages/{message_id}/attachments/{att['id']}",
                )
                for att in data.get("attachments", [])
            ],
        )

    async def delete_mailbox(self, mailbox: Mailbox) -> bool:
        """Clean up mailbox remotely."""
        try:
            headers = {"Authorization": f"Bearer {mailbox.token}"}
            await self.client.delete(f"{self.base_url}/inboxes/{mailbox.address}", headers=headers)
            return True
        except Exception:
            return False`}
        />
      </section>

      {/* Step 2: Registering Provider */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="provider-registration">
          Step 2: Registering in the Provider Registry
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Register your provider inside <code className="text-cyan-400 font-mono">src/maily/providers/__init__.py</code>:
        </p>
        <CodeBlock
          language="python"
          filename="src/maily/providers/__init__.py"
          code={`from maily.providers.registry import registry
from maily.providers.custom_service import CustomService

# Register custom driver
registry.register(CustomService)`}
        />
      </section>

      {/* Step 3: Automated Testing */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="testing-provider">
          Step 3: Writing Unit Tests with Mock HTTP
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Validate your driver using <code className="text-cyan-400 font-mono">respx</code> or <code className="text-cyan-400 font-mono">pytest-httpx</code> without touching live external APIs:
        </p>
        <CodeBlock
          language="python"
          filename="tests/test_custom_provider.py"
          code={`import pytest
import respx
from httpx import Response
from maily.providers.custom_service import CustomService

@pytest.mark.asyncio
@respx.mock
async def test_custom_service_lifecycle():
    # 1. Mock domains response
    respx.get("https://api.custom-tempmail.dev/domains").mock(
        return_value=Response(200, json={"domains": ["test-mail.org"]})
    )

    provider = CustomService()
    domains = await provider.get_domains()
    assert "test-mail.org" in domains

    # 2. Mock inbox creation
    respx.post("https://api.custom-tempmail.dev/inboxes").mock(
        return_value=Response(201, json={"auth_token": "mock-tok-123"})
    )

    mailbox = await provider.create_mailbox(username="ci-test", domain="test-mail.org")
    assert mailbox.address == "ci-test@test-mail.org"`}
        />
      </section>

      {/* Navigation */}
      <div className="pt-6 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/providers" className="text-slate-400 hover:text-white">
          ← Provider Matrix
        </Link>
        <Link
          to="/docs/recipes"
          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold"
        >
          <span>Production Recipes & Testing</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
