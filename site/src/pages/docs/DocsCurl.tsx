import React from 'react';
import { CodeBlock } from '../../components/common/CodeBlock';
import { Callout } from '../../components/common/Callout';
import { Link, useRouter } from '../../context/RouterContext';
import { ArrowRight, Terminal, ExternalLink, ShieldCheck, Zap, AlertTriangle } from 'lucide-react';
import { GithubIcon } from '../../components/common/Icons';

export const DocsCurl: React.FC = () => {
  const { assetUrl } = useRouter();
  return (
    <div className="space-y-10">
      {/* Header */}
      <section>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-xs font-mono mb-4">
          <span>cURL & REST API Reference</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-display" id="curl-overview">
            Universal REST API Cheat Sheet
          </h2>
          <a
            href="https://github.com/stormsia/maily#quickstart--getting-started"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 shadow-sm transition-all self-start sm:self-auto"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>REST API in GitHub README ↗</span>
          </a>
        </div>
        <p className="text-base leading-relaxed text-slate-300">
          The Maily REST API operates over HTTP/1.1 and HTTP/2 on port <code className="text-cyan-400 font-mono">8477</code> by default. All endpoints consume and return standard JSON schemas.
        </p>
      </section>

      {/* Server Prerequisite */}
      <Callout type="warning" title="Maily Gateway Server Required">
        <p className="text-xs leading-relaxed text-amber-200/90">
          All cURL and HTTP requests interact with your self-hosted <strong>Maily Gateway Server</strong> on port <code className="text-cyan-300 font-mono">8477</code>. <strong>The API is unavailable without a running server instance.</strong> Launch your server container first (<code className="text-slate-200 font-mono">docker run -d -p 8477:8477 -e MAILY_API_KEY=your_secret_api_key -v maily_data:/data ghcr.io/stormsia/maily:latest</code>).
        </p>
      </Callout>

      {/* Authentication */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="authentication">
          Authentication
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Authenticate your requests by supplying the <code className="text-cyan-400 font-mono">X-API-Key</code> HTTP header matching your configured <code className="text-cyan-400 font-mono">MAILY_API_KEY</code> environment variable:
        </p>
        <CodeBlock
          language="bash"
          code={`curl -X GET "http://127.0.0.1:8477/v1/targets" \\
  -H "X-API-Key: your_secret_api_key" \\
  -H "Accept: application/json"`}
        />
        <p className="text-xs text-slate-500 mt-2">
          Note: If <code className="font-mono">MAILY_API_KEY</code> is unset on the server, all non-admin routes are publicly accessible without authentication.
        </p>
      </section>

      {/* Targets & Discovery */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="targets-discovery">
          1. Provider & Target Discovery
        </h3>
        <p className="text-xs text-slate-400 mb-2">List active providers and rotating domains:</p>
        <CodeBlock
          language="bash"
          code={`curl -X GET "http://127.0.0.1:8477/v1/targets" \\
  -H "X-API-Key: your_secret_api_key"`}
        />
        <p className="text-xs text-slate-400 mt-3 mb-1">Sample Response:</p>
        <CodeBlock
          language="json"
          code={`[
  {
    "name": "mail.tm",
    "kind": "domain",
    "domains": ["mailtm.net", "mailtm.me", "mohmal.im"],
    "capabilities": {
      "custom_username": true,
      "custom_domain": true,
      "password_auth": true,
      "sse_stream": true,
      "attachments": true
    }
  },
  {
    "name": "tempmailplus",
    "kind": "domain",
    "domains": ["mailto.plus", "fexpost.com"],
    "capabilities": {
      "custom_username": true,
      "custom_domain": true,
      "pin_code": true,
      "sse_stream": false,
      "attachments": true
    }
  }
]`}
        />
      </section>

      {/* Mailbox Operations */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="mailbox-operations">
          2. Ephemeral Mailbox Lifecycle
        </h3>

        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold text-slate-300 mb-1">Create Disposable Mailbox:</p>
            <CodeBlock
              language="bash"
              code={`curl -X POST "http://127.0.0.1:8477/v1/mailboxes" \\
  -H "X-API-Key: your_secret_api_key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "provider": "mail.tm",
    "username": "qa-worker-91",
    "domain": "mailtm.net"
  }'`}
            />
            <p className="text-xs text-slate-400 mt-2 mb-1">Sample Response (201 Created):</p>
            <CodeBlock
              language="json"
              code={`{
  "id": 42,
  "address": "qa-worker-91@mailtm.net",
  "provider": "mail.tm",
  "created_at": "2026-11-15T01:30:00Z",
  "expires_at": "2026-11-15T02:30:00Z"
}`}
            />
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-300 mb-1">List Active Mailboxes:</p>
            <CodeBlock
              language="bash"
              code={`curl -X GET "http://127.0.0.1:8477/v1/mailboxes" \\
  -H "X-API-Key: your_secret_api_key"`}
            />
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-300 mb-1">Delete Mailbox:</p>
            <CodeBlock
              language="bash"
              code={`curl -X DELETE "http://127.0.0.1:8477/v1/mailboxes/42" \\
  -H "X-API-Key: your_secret_api_key"`}
            />
          </div>
        </div>
      </section>

      {/* Messages & Attachments */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="message-operations">
          3. Inspect Messages & Attachments
        </h3>

        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold text-slate-300 mb-1">List Messages for Mailbox:</p>
            <CodeBlock
              language="bash"
              code={`curl -X GET "http://127.0.0.1:8477/v1/mailboxes/42/messages" \\
  -H "X-API-Key: your_secret_api_key"`}
            />
            <p className="text-xs text-slate-400 mt-2 mb-1">Sample Response:</p>
            <CodeBlock
              language="json"
              code={`[
  {
    "id": "msg_984712",
    "mailbox_id": 42,
    "from_address": "no-reply@saas-app.test",
    "subject": "Your verification code is 849201",
    "intro": "Use code 849201 to verify your new account...",
    "created_at": "2026-11-15T01:31:12Z",
    "has_attachments": false
  }
]`}
            />
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-300 mb-1">Fetch Complete Message Payload (HTML & Plaintext):</p>
            <CodeBlock
              language="bash"
              code={`curl -X GET "http://127.0.0.1:8477/v1/mailboxes/42/messages/msg_984712" \\
  -H "X-API-Key: your_secret_api_key"`}
            />
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-300 mb-1">Download Binary Attachment:</p>
            <CodeBlock
              language="bash"
              code={`curl -X GET "http://127.0.0.1:8477/v1/mailboxes/42/messages/msg_984712/attachments/att_1" \\
  -H "X-API-Key: your_secret_api_key" \\
  --output invoice.pdf`}
            />
          </div>
        </div>
      </section>

      {/* SSE Realtime Streaming */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="sse-streaming">
          4. Real-Time Server-Sent Events (SSE) Stream
        </h3>
        <p className="text-sm text-slate-400 mb-2">
          Connect directly via <code className="text-cyan-400 font-mono">curl -N</code> to stream incoming messages without polling:
        </p>
        <CodeBlock
          language="bash"
          code={`curl -N -X GET "http://127.0.0.1:8477/v1/mailboxes/42/events" \\
  -H "X-API-Key: your_secret_api_key" \\
  -H "Accept: text/event-stream"`}
        />
        <p className="text-xs text-slate-400 mt-2 mb-1">Stream Output:</p>
        <CodeBlock
          language="text"
          code={`event: message
data: {"id": "msg_984712", "subject": "Your OTP is 849201", "from": "auth@service.com"}

event: ping
data: {"timestamp": 1731634280}`}
        />
      </section>

      {/* Administration & Scoped Keys */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="admin-operations">
          5. Scoped Keys & Database Maintenance
        </h3>
        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold text-slate-300 mb-1">Mint Fine-Grained Scoped API Key:</p>
            <CodeBlock
              language="bash"
              code={`curl -X POST "http://127.0.0.1:8477/v1/keys" \\
  -H "X-API-Key: your_secret_api_key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "playwright-ci-runner",
    "scope": {
      "providers": ["mail.tm", "tempmailplus"],
      "actions": ["read", "write"]
    }
  }'`}
            />
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-300 mb-1">Trigger Retention Garbage Sweep:</p>
            <CodeBlock
              language="bash"
              code={`curl -X POST "http://127.0.0.1:8477/v1/admin/retention/run?force_maintenance=true" \\
  -H "X-API-Key: your_secret_api_key"`}
            />
          </div>
        </div>
      </section>

      {/* Scalar Banner */}
      <Callout type="tip" title="Interactive OpenAPI 3.1 Explorer">
        Ready to test these requests interactively in your browser? Open the{' '}
        <a href={assetUrl('/scalar.html')} target="_blank" rel="noopener noreferrer" className="underline font-semibold text-cyan-400">
          Scalar Interactive API Explorer
        </a>{' '}
        to generate code snippets in 15+ programming languages.
      </Callout>

      {/* Navigation */}
      <div className="pt-6 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/python" className="text-slate-400 hover:text-white">
          ← Python SDK Guide
        </Link>
        <Link
          to="/docs/docker"
          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold"
        >
          <span>Docker & Deployment Guide</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
