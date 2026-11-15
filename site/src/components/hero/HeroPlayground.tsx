import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  Mail,
  Send,
  Code2,
  Terminal,
  ShieldCheck,
  Key,
  Radio,
  Clock,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  Trash2,
  FileCode,
  Eye
} from 'lucide-react';
import { useRouter } from '../../context/RouterContext';
import { APP_VERSION } from '../../data/version';

interface SimulatedMessage {
  id: string;
  from: string;
  subject: string;
  preview: string;
  bodyText: string;
  bodyHtml: string;
  receivedAt: string;
  otpCode?: string;
  headers: Record<string, string>;
}

const PRESET_MESSAGES: Omit<SimulatedMessage, 'id' | 'receivedAt'>[] = [
  {
    from: 'support@github.com',
    subject: '[GitHub] Please verify your device (OTP: 742918)',
    preview: 'A login attempt was made with your credentials. Your one-time verification code is 742918.',
    otpCode: '742918',
    bodyText: `Hey developer,\n\nA login attempt requires additional verification.\nYour verification code is: 742918\n\nThis code expires in 10 minutes. If this was not you, please secure your account immediately.\n\nGitHub Security Team`,
    bodyHtml: `<div style="font-family: sans-serif; line-height: 1.6; color: #1e293b;">
      <h3 style="color: #0f172a; margin-top: 0;">Device Verification</h3>
      <p>A login attempt requires additional verification for your account.</p>
      <div style="background: #f1f5f9; border: 1px dashed #cbd5e1; padding: 16px; border-radius: 8px; text-align: center; margin: 20px 0;">
        <span style="font-size: 28px; font-weight: 800; letter-spacing: 4px; color: #0284c7; font-family: monospace;">742918</span>
      </div>
      <p style="font-size: 13px; color: #64748b;">This code expires in 10 minutes.</p>
    </div>`,
    headers: {
      'message-id': '<gh-auth-742918@github.com>',
      'spf': 'pass (github.com: domain of support@github.com designates 192.30.252.204 as permitted sender)',
      'dkim': 'pass header.i=@github.com',
      'dmarc': 'pass (p=REJECT sp=REJECT dis=NONE)'
    }
  },
  {
    from: 'notifications@stripe.com',
    subject: 'Invoice #INV-2026-890 paid ($49.00 USD)',
    preview: 'Your invoice for Maily Pro Gateway has been successfully charged to Visa •••• 4242.',
    bodyText: `Receipt for invoice #INV-2026-890\nAmount: $49.00 USD\nStatus: Paid\nCustomer: QA Engineering Team\nItem: Maily High-Throughput Dedicated Gateway Cluster\n\nThank you for your business!\nStripe Billing`,
    bodyHtml: `<div style="font-family: sans-serif; line-height: 1.6; color: #1e293b;">
      <h3 style="color: #0f172a; margin-top: 0;">Payment Confirmation</h3>
      <p>Your payment for invoice <strong>#INV-2026-890</strong> has succeeded.</p>
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin: 16px 0;">
        <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 8px;">
          <span>Maily Cluster Gateway</span>
          <span style="font-weight: 700;">$49.00</span>
        </div>
        <div style="font-size: 12px; color: #10b981; font-weight: 600;">Paid via Visa ending in 4242</div>
      </div>
    </div>`,
    headers: {
      'message-id': '<inv-2026-890@stripe.com>',
      'spf': 'pass',
      'dkim': 'pass',
      'x-stripe-event': 'invoice.payment_succeeded'
    }
  },
  {
    from: 'auth@supabase.co',
    subject: 'Your Magic Link for Project Staging',
    preview: 'Click the link to authenticate into the staging project workspace (Token: 993412).',
    otpCode: '993412',
    bodyText: `Welcome back!\n\nFollow this link to login:\nhttps://auth.example.com/verify?token=993412&type=magiclink\n\nOr enter code: 993412`,
    bodyHtml: `<div style="font-family: sans-serif; line-height: 1.6; color: #1e293b;">
      <h3 style="color: #0f172a; margin-top: 0;">Supabase Magic Link</h3>
      <p>Click below to sign in directly without a password:</p>
      <p><a href="#" style="display: inline-block; background: #0284c7; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px;">Sign In to Workspace</a></p>
      <p style="font-size: 12px; color: #64748b; margin-top: 16px;">Backup verification code: <strong style="font-family: monospace; color: #0284c7;">993412</strong></p>
    </div>`,
    headers: {
      'message-id': '<supa-magic-993412@supabase.co>',
      'spf': 'pass',
      'dkim': 'pass'
    }
  }
];

export const HeroPlayground: React.FC = () => {
  const { assetUrl } = useRouter();
  const [provider, setProvider] = useState<string>('mail.tm');
  const [inboxAddress, setInboxAddress] = useState<string>('qa-runner-724@mailtm.net');
  const [mailboxId, setMailboxId] = useState<string>('mbx_01h8a9v2');
  const [messages, setMessages] = useState<SimulatedMessage[]>([]);
  const [selectedMsgId, setSelectedMsgId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'preview' | 'json' | 'curl' | 'python'>('preview');
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [snippetCopied, setSnippetCopied] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [eventLogs, setEventLogs] = useState<string[]>([
    'SSE stream initialized on port 8477',
    'Provider mail.tm connected (driver: aiohttp, TLS: v1.3)'
  ]);

  // Generate new ephemeral inbox
  const handleGenerateInbox = (prov = provider) => {
    setIsGenerating(true);
    setTimeout(() => {
      const randNum = Math.floor(1000 + Math.random() * 9000);
      const domainMap: Record<string, string> = {
        'mail.tm': 'mailtm.net',
        'mail.gw': 'mailgw.com',
        '1secmail': '1secmail.com',
        'guerrillamail': 'sharklasers.com',
        'tempmail.plus': 'mailto.plus',
        'anonymmail.net': 'anonymmail.net',
        'dispoemail.org': 'dispoemail.org'
      };
      const domain = domainMap[prov] || 'mailtm.net';
      const newAddr = `qa-runner-${randNum}@${domain}`;
      const newId = `mbx_${Math.random().toString(36).substring(2, 9)}`;

      setInboxAddress(newAddr);
      setMailboxId(newId);
      setMessages([]);
      setSelectedMsgId(null);
      setIsGenerating(false);

      const time = new Date().toLocaleTimeString();
      setEventLogs((prev) => [
        `[${time}] Created mailbox ${newId} (${newAddr}) via ${prov}`,
        `[${time}] SSE subscribed to channel /api/v1/mailboxes/${newId}/events`,
        ...prev.slice(0, 3)
      ]);
    }, 280);
  };

  // Simulate incoming email
  const handleSimulateReceive = (presetIndex = 0) => {
    setIsSimulating(true);
    setTimeout(() => {
      const template = PRESET_MESSAGES[presetIndex % PRESET_MESSAGES.length];
      const newMsgId = `msg_${Math.random().toString(36).substring(2, 10)}`;
      const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      const newMsg: SimulatedMessage = {
        ...template,
        id: newMsgId,
        receivedAt: time
      };

      setMessages((prev) => [newMsg, ...prev]);
      setSelectedMsgId(newMsgId);
      setIsSimulating(false);

      setEventLogs((prev) => [
        `[${time}] SSE event: message.created -> ${newMsgId} (From: ${newMsg.from})`,
        ...prev.slice(0, 4)
      ]);
    }, 350);
  };

  // Copy email to clipboard
  const handleCopy = () => {
    try {
      navigator.clipboard.writeText(inboxAddress);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch {}
  };

  const selectedMessage = messages.find((m) => m.id === selectedMsgId) || messages[0] || null;

  const handleCopySnippetText = (text: string) => {
    try {
      navigator.clipboard.writeText(text);
      setSnippetCopied(true);
      setTimeout(() => setSnippetCopied(false), 2000);
    } catch {}
  };

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-950/80 shadow-2xl backdrop-blur-sm overflow-hidden text-left">
      {/* Top Interactive Toolbar */}
      <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/50 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-mono font-semibold text-slate-800 dark:text-slate-200">
              Gateway Engine
            </span>
          </div>
          <span className="text-slate-300 dark:text-slate-700">|</span>
          <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-700 dark:text-cyan-400">
            <Radio className="w-3.5 h-3.5" />
            <span>SSE Live Stream</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
            Storage: <span className="text-slate-700 dark:text-slate-300 font-semibold">SQLite WAL (AES-GCM)</span>
          </span>
          <span className="text-slate-300 dark:text-slate-700">·</span>
          <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400">0.8ms p50</span>
        </div>
      </div>

      {/* Main Playground Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-slate-200 dark:divide-slate-800">

        {/* Left Column: Inbox Controls & Inbox List (5 cols) */}
        <div className="lg:col-span-5 p-5 space-y-5 bg-slate-50/40 dark:bg-slate-900/20">
          {/* Provider Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-mono flex items-center justify-between">
              <span>Upstream Provider</span>
              <span className="text-[10px] text-cyan-600 dark:text-cyan-400 lowercase font-normal">8+ drivers ready</span>
            </label>
            <div className="flex gap-2">
              <select
                value={provider}
                onChange={(e) => {
                  setProvider(e.target.value);
                  handleGenerateInbox(e.target.value);
                }}
                className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-200 font-medium focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              >
                <option value="mail.tm">Mail.tm (Default · SSE Enabled)</option>
                <option value="mail.gw">Mail.gw (Alternative Hydra API)</option>
                <option value="1secmail">1secmail (High Speed · No Auth)</option>
                <option value="guerrillamail">GuerrillaMail (High Volume)</option>
                <option value="tempmail.plus">TempMail.plus (PIN Support)</option>
                <option value="anonymmail.net">AnonymMail.net (Ephemeral)</option>
                <option value="dispoemail.org">DispoEmail.org (Direct REST)</option>
              </select>

              <button
                onClick={() => handleGenerateInbox()}
                disabled={isGenerating}
                className="px-3 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50"
                title="Generate fresh mailbox"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">New</span>
              </button>
            </div>
          </div>

          {/* Generated Email Box */}
          <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500 dark:text-slate-400 font-mono">Disposable Mailbox:</span>
              <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-500/20">
                Active
              </span>
            </div>

            <div className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-xs text-cyan-700 dark:text-cyan-300">
              <span className="font-semibold truncate select-all">{inboxAddress}</span>
              <button
                onClick={handleCopy}
                className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
                title="Copy to clipboard"
                aria-label="Copy mailbox address"
              >
                {isCopied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 pt-1">
              <span>Mailbox ID: <code className="font-mono text-slate-700 dark:text-slate-300">{mailboxId}</code></span>
              {isCopied && <span className="text-emerald-600 dark:text-emerald-400 font-medium">Copied!</span>}
            </div>
          </div>

          {/* Simulation Action Buttons */}
          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-mono block">
              Simulate Upstream Inbound
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => handleSimulateReceive(0)}
                disabled={isSimulating}
                className="p-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition-all shadow-sm flex flex-col items-center justify-center gap-1 disabled:opacity-50"
              >
                <Key className="w-3.5 h-3.5" />
                <span className="text-[11px]">GitHub OTP</span>
              </button>
              <button
                onClick={() => handleSimulateReceive(1)}
                disabled={isSimulating}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium transition-all shadow-sm flex flex-col items-center justify-center gap-1 disabled:opacity-50"
              >
                <FileCode className="w-3.5 h-3.5" />
                <span className="text-[11px]">Stripe Event</span>
              </button>
              <button
                onClick={() => handleSimulateReceive(2)}
                disabled={isSimulating}
                className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-all shadow-sm flex flex-col items-center justify-center gap-1 disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span className="text-[11px]">Magic Link</span>
              </button>
            </div>
          </div>

          {/* Message List */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 font-mono">
              <span>Inbox ({messages.length})</span>
              {messages.length > 0 && (
                <button
                  onClick={() => {
                    setMessages([]);
                    setSelectedMsgId(null);
                  }}
                  className="text-rose-500 hover:text-rose-600 flex items-center gap-1 text-[11px]"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Clear</span>
                </button>
              )}
            </div>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {messages.length === 0 ? (
                <div className="p-6 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-xl text-slate-500 dark:text-slate-400 text-xs space-y-2">
                  <Mail className="w-6 h-6 mx-auto text-slate-400 opacity-60" />
                  <p>Inbox is waiting for incoming mail.</p>
                  <p className="text-[11px] text-slate-400">Click a simulation button above or send to this email via your app.</p>
                </div>
              ) : (
                messages.map((msg) => {
                  const isSelected = msg.id === (selectedMsgId || messages[0].id);
                  return (
                    <button
                      key={msg.id}
                      onClick={() => setSelectedMsgId(msg.id)}
                      className={`w-full text-left p-3 rounded-xl border transition-all ${
                        isSelected
                          ? 'bg-cyan-50/80 dark:bg-cyan-950/30 border-cyan-400/80 dark:border-cyan-500/50 shadow-sm'
                          : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-slate-900 dark:text-slate-200 truncate">
                          {msg.from}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400 shrink-0">
                          {msg.receivedAt}
                        </span>
                      </div>
                      <div className="text-xs text-slate-700 dark:text-slate-300 font-medium truncate">
                        {msg.subject}
                      </div>
                      {msg.otpCode && (
                        <div className="mt-2 inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-500/15 border border-emerald-300 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-[10px] font-mono font-bold">
                          <span>OTP: {msg.otpCode}</span>
                        </div>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Realtime Event Stream Ticker */}
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
            <div className="text-slate-300 font-semibold flex items-center justify-between pb-1 border-b border-slate-800">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <Terminal className="w-3 h-3" />
                <span>Real-Time SSE Event Log</span>
              </span>
              <span className="text-[10px] text-slate-500">200 OK</span>
            </div>
            {eventLogs.map((log, idx) => (
              <div key={idx} className="truncate text-slate-400">
                {log}
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Message Inspector & Developer Tools (7 cols) */}
        <div className="lg:col-span-7 p-5 flex flex-col justify-between bg-white dark:bg-slate-950">
          <div>
            {/* View Mode Tabs */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800 gap-3">
              <div className="flex items-center gap-1 sm:gap-2 flex-wrap">
                <button
                  onClick={() => setActiveTab('preview')}
                  className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
                    activeTab === 'preview'
                      ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-semibold'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Rendered</span>
                </button>
                <button
                  onClick={() => setActiveTab('curl')}
                  className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
                    activeTab === 'curl'
                      ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-semibold'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  <Terminal className="w-3.5 h-3.5" />
                  <span>cURL</span>
                </button>
                <button
                  onClick={() => setActiveTab('python')}
                  className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
                    activeTab === 'python'
                      ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-semibold'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  <Code2 className="w-3.5 h-3.5" />
                  <span>Python SDK</span>
                </button>
                <button
                  onClick={() => setActiveTab('json')}
                  className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
                    activeTab === 'json'
                      ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-semibold'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  <FileCode className="w-3.5 h-3.5" />
                  <span>JSON</span>
                </button>
              </div>

              {selectedMessage && (
                <div className="hidden sm:flex items-center gap-2 text-[11px] font-mono text-emerald-600 dark:text-emerald-400">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>DKIM / SPF Validated</span>
                </div>
              )}
            </div>

            {/* Tab Contents */}
            <div className="py-4">
              {selectedMessage ? (
                <>
                  {activeTab === 'preview' && (
                    <div className="space-y-4">
                      {/* Message Metadata Header */}
                      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-1.5 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500 dark:text-slate-400">From:</span>
                          <span className="font-semibold text-slate-900 dark:text-slate-200 font-mono">
                            {selectedMessage.from}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500 dark:text-slate-400">Subject:</span>
                          <span className="font-semibold text-slate-900 dark:text-slate-100">
                            {selectedMessage.subject}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500 dark:text-slate-400">Received:</span>
                          <span className="font-mono text-slate-600 dark:text-slate-400">
                            {selectedMessage.receivedAt}
                          </span>
                        </div>
                      </div>

                      {/* OTP Auto-Extraction Highlight Banner */}
                      {selectedMessage.otpCode && (
                        <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-500/40 flex items-center justify-between">
                          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 dark:text-emerald-300">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                            <span>Auto-Extracted OTP:</span>
                            <span className="font-mono text-base font-extrabold tracking-wider bg-white dark:bg-emerald-900/60 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-700">
                              {selectedMessage.otpCode}
                            </span>
                          </div>
                          <button
                            onClick={() => {
                              try {
                                navigator.clipboard.writeText(selectedMessage.otpCode || '');
                              } catch {}
                            }}
                            className="text-[11px] font-mono text-emerald-700 dark:text-emerald-400 hover:underline flex items-center gap-1"
                          >
                            <Copy className="w-3 h-3" />
                            <span>Copy Token</span>
                          </button>
                        </div>
                      )}

                      {/* HTML Render Container */}
                      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white text-slate-900 min-h-[160px] text-xs">
                        <div dangerouslySetInnerHTML={{ __html: selectedMessage.bodyHtml }} />
                      </div>
                    </div>
                  )}

                  {activeTab === 'json' && (() => {
                    const jsonPayload = JSON.stringify(
                      {
                        id: selectedMessage.id,
                        mailbox_id: mailboxId,
                        from_address: selectedMessage.from,
                        to_address: inboxAddress,
                        subject: selectedMessage.subject,
                        text_body: selectedMessage.bodyText,
                        extracted_otp: selectedMessage.otpCode || null,
                        headers: selectedMessage.headers,
                        attachments: [],
                        security: {
                          spf: 'pass',
                          dkim: 'pass',
                          encryption: 'AES-256-GCM'
                        },
                        created_at: new Date().toISOString()
                      },
                      null,
                      2
                    );
                    return (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs font-mono text-slate-500">
                          <span>Normalized REST API Schema</span>
                          <button
                            onClick={() => handleCopySnippetText(jsonPayload)}
                            className="flex items-center gap-1 text-[11px] text-cyan-600 dark:text-cyan-400 hover:underline"
                          >
                            {snippetCopied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                            <span>{snippetCopied ? 'Copied!' : 'Copy JSON'}</span>
                          </button>
                        </div>
                        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-200 max-h-[340px] overflow-auto">
                          <pre>
                            <code>{jsonPayload}</code>
                          </pre>
                        </div>
                      </div>
                    );
                  })()}

                  {activeTab === 'curl' && (() => {
                    const curlPayload = `# 1. Fetch message details
curl -X GET "http://127.0.0.1:8477/api/v1/messages/${selectedMessage.id}" \\
  -H "Accept: application/json"

# 2. Extract parsed OTP directly
curl -X GET "http://127.0.0.1:8477/api/v1/messages/${selectedMessage.id}/otp"`;

                    return (
                      <div className="space-y-3 font-mono text-xs">
                        <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs">
                          <span>Execute directly against self-hosted Maily:</span>
                          <button
                            onClick={() => handleCopySnippetText(curlPayload)}
                            className="flex items-center gap-1 text-[11px] text-cyan-600 dark:text-cyan-400 hover:underline"
                          >
                            {snippetCopied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                            <span>{snippetCopied ? 'Copied!' : 'Copy cURL'}</span>
                          </button>
                        </div>
                        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-950 p-4 text-cyan-300 overflow-x-auto">
                          <pre>
                            <code>{curlPayload}</code>
                          </pre>
                        </div>
                      </div>
                    );
                  })()}

                  {activeTab === 'python' && (() => {
                    const pyPayload = `import asyncio
from maily import MailyClient

async def main():
    async with MailyClient(base_url="http://127.0.0.1:8477") as client:
        # 1. Inspect existing inbox or wait for mail
        mbx = await client.get_mailbox("${mailboxId}")
        print(f"Target Inbox: {mbx.address}")

        # 2. Extract verification code directly
        msg = await client.get_message("${selectedMessage.id}")
        print(f"Received Subject: {msg.subject}")
        print(f"Extracted OTP: {msg.extracted_otp}")

asyncio.run(main())`;

                    return (
                      <div className="space-y-3 font-mono text-xs">
                        <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs">
                          <span>Official Python Async SDK (maily-client):</span>
                          <button
                            onClick={() => handleCopySnippetText(pyPayload)}
                            className="flex items-center gap-1 text-[11px] text-cyan-600 dark:text-cyan-400 hover:underline"
                          >
                            {snippetCopied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                            <span>{snippetCopied ? 'Copied!' : 'Copy Python'}</span>
                          </button>
                        </div>
                        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-950 p-4 text-emerald-300 overflow-x-auto">
                          <pre>
                            <code>{pyPayload}</code>
                          </pre>
                        </div>
                      </div>
                    );
                  })()}
                </>
              ) : (
                <div className="py-16 text-center space-y-3 text-slate-500 dark:text-slate-400">
                  <Mail className="w-8 h-8 mx-auto text-slate-400 opacity-50" />
                  <p className="text-sm">No message selected.</p>
                  <p className="text-xs">
                    Generate an inbox and click "GitHub OTP" or "Stripe Event" to inspect live payloads.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Footer Bar */}
          <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 font-mono">
            <span>SDK Compatible: <span className="text-cyan-600 dark:text-cyan-400">maily-client &gt;= {APP_VERSION}</span></span>
            <a
              href={assetUrl('/scalar.html')}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-cyan-600 dark:hover:text-cyan-400 flex items-center gap-1"
            >
              <span>Explore OpenAPI specs</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

      </div>
    </div>
  );
};
