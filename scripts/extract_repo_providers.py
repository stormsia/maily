import json
from pathlib import Path

from maily.providers.registry import ProviderRegistry, create_public_providers

reg = ProviderRegistry(create_public_providers())
summary = reg.summary()

# Map slug to rich metadata based on docs/PROVIDERS.md and python implementations
providers_data = []

# 1. Add public providers from registry
descriptions = {
    "mail.tm": "The default and most feature-complete provider with real-time SSE stream events and instant token creation.",
    "tempmail.plus": "Fast disposable email network with PIN-code protected inboxes and direct raw MIME access.",
    "temp-mail.io": "Zero-auth disposable gateway with support for custom username and domain rotation.",
    "temp.tf": "Gateway with Google dot/plus alias routing and instant inbound delivery.",
    "anonymmail.net": "Zero-auth disposable provider with fast mailbox provisioning and message listing.",
    "dispoemail.org": "Zero-auth temporary inbox provider supporting attachments and raw email source.",
    "noopmail.org": "High-speed zero-auth testing provider with sub-millisecond local in-memory/WAL routing.",
}

domain_examples = {
    "mail.tm": "mailtm.net, etc.",
    "tempmail.plus": "tempmail.plus, etc.",
    "temp-mail.io": "temp-mail.io, etc.",
    "temp.tf": "temp.tf, gmail aliases",
    "anonymmail.net": "anonymmail.net, etc.",
    "dispoemail.org": "dispoemail.org, etc.",
    "noopmail.org": "noopmail.org, etc.",
    "gmail": "gmail.com (+alias)",
}

for item in summary:
    slug = item["slug"]
    caps = item["capabilities"]
    providers_data.append(
        {
            "id": slug.replace(".", "_").replace("-", "_"),
            "name": slug,
            "domains": domain_examples.get(slug, slug),
            "targetKind": item["kind"],
            "customUsername": caps["can_choose_username"],
            "customDomain": caps["can_choose_domain"],
            "passwordOrPin": caps["can_set_password"],
            "rawMimeSource": caps["supports_source"],
            "attachments": caps["supports_attachments"],
            "deleteMailbox": caps["supports_delete_mailbox"],
            "deleteMessage": caps["supports_delete_message"],
            "markRead": caps["supports_mark_read"],
            "status": "operational",
            "description": descriptions.get(
                slug, "Official supported provider adapter in Maily registry."
            ),
            "pythonSnippet": f'mailbox = await client.create_mailbox(provider="{slug}")',
        }
    )

# 2. Add Gmail parent router as defined in docs/PROVIDERS.md and src/maily/providers/gmail
providers_data.append(
    {
        "id": "gmail",
        "name": "gmail",
        "domains": "gmail.com (+alias)",
        "targetKind": "parent",
        "customUsername": True,  # supports +alias
        "customDomain": False,
        "passwordOrPin": False,  # OAuth2 token
        "rawMimeSource": True,
        "attachments": True,
        "deleteMailbox": False,
        "deleteMessage": True,
        "markRead": True,
        "status": "operational",
        "description": "Private OAuth2 parent router allowing infinite disposable sub-addresses via RFC 5233 plus-addressing (user+tag@gmail.com).",
        "pythonSnippet": 'mailbox = await client.create_mailbox(provider="gmail", username="user+tag")',
    }
)

out_file = Path("site/src/data/repoProviders.ts")
ts_content = f"""// Generated directly from Python backend (maily.providers.registry and docs/PROVIDERS.md)

export interface RepoProviderInfo {{
  id: string;
  name: string;
  domains: string;
  targetKind: 'domain' | 'parent';
  customUsername: boolean;
  customDomain: boolean;
  passwordOrPin: boolean;
  rawMimeSource: boolean;
  attachments: boolean;
  deleteMailbox: boolean;
  deleteMessage: boolean;
  markRead: boolean;
  status: 'operational' | 'degraded';
  description: string;
  pythonSnippet: string;
}}

export const REPO_PROVIDERS: RepoProviderInfo[] = {json.dumps(providers_data, indent=2)};
"""

out_file.write_text(ts_content, encoding="utf-8")
print(f"Generated {out_file} with {len(providers_data)} authentic providers!")
