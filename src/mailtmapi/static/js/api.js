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
  }
}

/** Injected by app.js: () => Promise<boolean> (true = key saved, retry). */
let onAuthRequired = async () => false;
export function setAuthRequiredHandler(fn) {
  onAuthRequired = fn;
}

async function parseError(res) {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string" && data.detail) return data.detail;
  } catch {
    /* non-JSON error body */
  }
  return `${res.status} ${res.statusText}`.trim();
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
  if (res.status === 401 && !retried) {
    const saved = await onAuthRequired();
    if (saved) return request(path, { method, body, retried: true });
    throw new ApiError(401, "Unauthorized — an API key is required.");
  }
  if (res.status === 204) return null;
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

export const api = {
  health: () => request("/health"),
  providers: () => request("/v1/providers"),
  targets: (provider) =>
    request(`/v1/targets?provider=${encodeURIComponent(provider)}`),
  createMailbox: (body) => request("/v1/mailboxes", { method: "POST", body }),
  mailboxes: (params = {}) => {
    const q = new URLSearchParams();
    if (params.provider) q.set("provider", params.provider);
    if (params.active !== undefined && params.active !== "")
      q.set("active", String(params.active));
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
