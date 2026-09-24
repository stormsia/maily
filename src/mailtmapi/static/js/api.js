/* mailtmapi admin — fetch wrapper + per-endpoint functions.
   All URLs are relative (/v1/...) so the app works same-origin.
   Auth: X-API-Key from localStorage ("mailtm_api_key"); on 401 the
   registered handler prompts for a key and we retry once. */

const KEY_NAME = "mailtm_api_key";

export function getApiKey() {
  try {
    return localStorage.getItem(KEY_NAME) || "";
  } catch {
    return "";
  }
}

export function setApiKey(key) {
  try {
    if (key) localStorage.setItem(KEY_NAME, key);
    else localStorage.removeItem(KEY_NAME);
  } catch {
    /* private mode: key just won't persist */
  }
}

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `Request failed (${status})`);
    this.status = status;
    this.detail = detail || `Request failed (${status})`;
    this.code = null;
  }
}

/** Injected by app.js: () => Promise<boolean> (true = key saved, retry). */
let onAuthRequired = async () => false;
export function setAuthRequiredHandler(fn) {
  onAuthRequired = fn;
}

/* Structured extras from an error body (e.g. failed/refreshed lists, code). */
function copyExtra(err, data) {
  if (!data) return;
  for (const k of ["failed", "refreshed"]) {
    if (Array.isArray(data[k])) err[k] = data[k];
  }
  if (typeof data.code === "string") err.code = data.code;
}

/* FastAPI: detail is a string, or a 422 array of {loc, msg, type}. */
function formatDetail(data) {
  if (!data) return "";
  const detail = data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (!item || typeof item !== "object") return item == null ? "" : String(item);
        const loc = Array.isArray(item.loc) ? item.loc.join(".") : "";
        const msg = typeof item.msg === "string" ? item.msg : "";
        return [loc, msg].filter(Boolean).join(" ");
      })
      .filter(Boolean);
    return parts.join("; ");
  }
  return "";
}

async function parseError(res) {
  let data;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  const detail = formatDetail(data) || `${res.status} ${res.statusText}`.trim();
  return { detail, data: data && typeof data === "object" ? data : null };
}

async function request(path, { method = "GET", body, retried = false } = {}) {
  const headers = { Accept: "application/json" };
  const key = getApiKey();
  if (key) headers["X-API-Key"] = key;
  let payload;
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(path, { method, headers, body: payload });
  } catch {
    throw new ApiError(
      0,
      `Cannot reach the server — is it running on ${location.host}?`,
    );
  }
  if (res.status === 401) {
    const { detail, data } = await parseError(res);
    // Machine-readable reason: body `code` first (structured errors), header
    // as a fallback for older servers. A 401 from a provider (e.g. expired
    // Gmail token, code "provider_auth") is NOT an API-key problem — show its
    // real message instead of triggering the key prompt.
    const reason = (data && data.code) || res.headers.get("x-mailtm-error");
    if (reason === "api_key" && !retried) {
      const saved = await onAuthRequired();
      if (saved) return request(path, { method, body, retried: true });
    }
    const err = new ApiError(401, detail);
    if (reason === "provider_auth") err.providerAuth = true;
    copyExtra(err, data);
    throw err;
  }
  if (res.status === 204) return null;
  if (!res.ok) {
    const { detail, data } = await parseError(res);
    const err = new ApiError(res.status, detail);
    copyExtra(err, data);
    throw err;
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

export const api = {
  health: () => request("/health"),
  config: () => request("/v1/config"),
  providers: () => request("/v1/providers"),
  targets: (provider) =>
    request(`/v1/targets?provider=${encodeURIComponent(provider)}`),
  createMailbox: (body) => request("/v1/mailboxes", { method: "POST", body }),
  mailboxes: (params = {}) => {
    const q = new URLSearchParams();
    if (params.provider) q.set("provider", params.provider);
    if (params.active !== undefined && params.active !== "")
      q.set("active", String(params.active));
    if (params.q) q.set("q", params.q);
    if (params.limit != null) q.set("limit", String(params.limit));
    if (params.offset != null) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request(`/v1/mailboxes${qs ? `?${qs}` : ""}`);
  },
  mailbox: (id) => request(`/v1/mailboxes/${encodeURIComponent(id)}`),
  mailboxByAddress: (email) =>
    request(`/v1/mailboxes/by-address/${encodeURIComponent(email)}`),
  deleteMailbox: (id) =>
    request(`/v1/mailboxes/${encodeURIComponent(id)}`, { method: "DELETE" }),
  messages: (id, page = 1) =>
    request(`/v1/mailboxes/${encodeURIComponent(id)}/messages?page=${page}`),
  message: (id, message_api_id) =>
    request(
      `/v1/mailboxes/${encodeURIComponent(id)}/messages/${encodeURIComponent(message_api_id)}`,
    ),
  markRead: (id, message_api_id) =>
    request(
      `/v1/mailboxes/${encodeURIComponent(id)}/messages/${encodeURIComponent(message_api_id)}/read`,
      { method: "POST" },
    ),
  deleteMessage: (id, message_api_id) =>
    request(
      `/v1/mailboxes/${encodeURIComponent(id)}/messages/${encodeURIComponent(message_api_id)}`,
      { method: "DELETE" },
    ),
  messageSource: (id, message_api_id) =>
    request(
      `/v1/mailboxes/${encodeURIComponent(id)}/messages/${encodeURIComponent(message_api_id)}/source`,
    ),
  stats: () => request("/v1/admin/stats"),
  retention: () => request("/v1/admin/retention"),
  saveRetention: (provider, body) =>
    request(`/v1/admin/retention/${encodeURIComponent(provider)}`, {
      method: "PUT",
      body,
    }),
  disableRetention: (provider) =>
    request(`/v1/admin/retention/${encodeURIComponent(provider)}`, {
      method: "DELETE",
    }),
  runRetention: () => request("/v1/admin/retention/run", { method: "POST" }),
  domainCache: () => request("/v1/admin/domain-cache"),
  saveDomainCache: (body) =>
    request("/v1/admin/domain-cache", { method: "PUT", body }),
  runDomainCache: () =>
    request("/v1/admin/domain-cache/run", { method: "POST" }),
  gmailOAuthStart: () => request("/v1/gmail/oauth/start", { method: "POST" }),
  gmailCreds: () => request("/v1/admin/gmail/creds"),
  saveGmailCreds: (body) =>
    request("/v1/admin/gmail/creds", { method: "PUT", body }),
  clearGmailCreds: () => request("/v1/admin/gmail/creds", { method: "DELETE" }),
  gmailAccounts: () => request("/v1/gmail/accounts"),
  gmailDelete: (id) =>
    request(`/v1/gmail/accounts/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),
  gmailSync: (id) =>
    request(`/v1/gmail/accounts/${encodeURIComponent(id)}/sync`, {
      method: "POST",
    }),
};
