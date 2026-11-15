// Generated directly from Python backend (maily.providers.registry and docs/PROVIDERS.md)

export interface RepoProviderInfo {
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
}

export const REPO_PROVIDERS: RepoProviderInfo[] = [
  {
    "id": "mail_tm",
    "name": "mail.tm",
    "domains": "mailtm.net, etc.",
    "targetKind": "domain",
    "customUsername": true,
    "customDomain": true,
    "passwordOrPin": true,
    "rawMimeSource": true,
    "attachments": true,
    "deleteMailbox": true,
    "deleteMessage": true,
    "markRead": true,
    "status": "operational",
    "description": "The default and most feature-complete provider with real-time SSE stream events and instant token creation.",
    "pythonSnippet": "mailbox = await client.create_mailbox(provider=\"mail.tm\")"
  },
  {
    "id": "tempmail_plus",
    "name": "tempmail.plus",
    "domains": "tempmail.plus, etc.",
    "targetKind": "domain",
    "customUsername": true,
    "customDomain": true,
    "passwordOrPin": true,
    "rawMimeSource": true,
    "attachments": true,
    "deleteMailbox": true,
    "deleteMessage": true,
    "markRead": true,
    "status": "operational",
    "description": "Fast disposable email network with PIN-code protected inboxes and direct raw MIME access.",
    "pythonSnippet": "mailbox = await client.create_mailbox(provider=\"tempmail.plus\")"
  },
  {
    "id": "temp_mail_io",
    "name": "temp-mail.io",
    "domains": "temp-mail.io, etc.",
    "targetKind": "domain",
    "customUsername": true,
    "customDomain": true,
    "passwordOrPin": false,
    "rawMimeSource": true,
    "attachments": true,
    "deleteMailbox": true,
    "deleteMessage": true,
    "markRead": false,
    "status": "operational",
    "description": "Zero-auth disposable gateway with support for custom username and domain rotation.",
    "pythonSnippet": "mailbox = await client.create_mailbox(provider=\"temp-mail.io\")"
  },
  {
    "id": "temp_tf",
    "name": "temp.tf",
    "domains": "temp.tf, gmail aliases",
    "targetKind": "domain",
    "customUsername": true,
    "customDomain": true,
    "passwordOrPin": false,
    "rawMimeSource": true,
    "attachments": true,
    "deleteMailbox": true,
    "deleteMessage": true,
    "markRead": false,
    "status": "operational",
    "description": "Gateway with Google dot/plus alias routing and instant inbound delivery.",
    "pythonSnippet": "mailbox = await client.create_mailbox(provider=\"temp.tf\")"
  },
  {
    "id": "anonymmail_net",
    "name": "anonymmail.net",
    "domains": "anonymmail.net, etc.",
    "targetKind": "domain",
    "customUsername": true,
    "customDomain": true,
    "passwordOrPin": false,
    "rawMimeSource": true,
    "attachments": true,
    "deleteMailbox": true,
    "deleteMessage": true,
    "markRead": false,
    "status": "operational",
    "description": "Zero-auth disposable provider with fast mailbox provisioning and message listing.",
    "pythonSnippet": "mailbox = await client.create_mailbox(provider=\"anonymmail.net\")"
  },
  {
    "id": "dispoemail_org",
    "name": "dispoemail.org",
    "domains": "dispoemail.org, etc.",
    "targetKind": "domain",
    "customUsername": true,
    "customDomain": true,
    "passwordOrPin": false,
    "rawMimeSource": true,
    "attachments": true,
    "deleteMailbox": true,
    "deleteMessage": true,
    "markRead": false,
    "status": "operational",
    "description": "Zero-auth temporary inbox provider supporting attachments and raw email source.",
    "pythonSnippet": "mailbox = await client.create_mailbox(provider=\"dispoemail.org\")"
  },
  {
    "id": "noopmail_org",
    "name": "noopmail.org",
    "domains": "noopmail.org, etc.",
    "targetKind": "domain",
    "customUsername": true,
    "customDomain": true,
    "passwordOrPin": false,
    "rawMimeSource": true,
    "attachments": false,
    "deleteMailbox": false,
    "deleteMessage": true,
    "markRead": false,
    "status": "operational",
    "description": "High-speed zero-auth testing provider with sub-millisecond local in-memory/WAL routing.",
    "pythonSnippet": "mailbox = await client.create_mailbox(provider=\"noopmail.org\")"
  },
  {
    "id": "gmail",
    "name": "gmail",
    "domains": "gmail.com (+alias)",
    "targetKind": "parent",
    "customUsername": true,
    "customDomain": false,
    "passwordOrPin": false,
    "rawMimeSource": true,
    "attachments": true,
    "deleteMailbox": false,
    "deleteMessage": true,
    "markRead": true,
    "status": "operational",
    "description": "Private OAuth2 parent router allowing infinite disposable sub-addresses via RFC 5233 plus-addressing (user+tag@gmail.com).",
    "pythonSnippet": "mailbox = await client.create_mailbox(provider=\"gmail\", username=\"user+tag\")"
  }
];
