/* maily admin — entry: routing, health, settings, shared wiring. */
import { api, getApiKey, setApiKey, setAuthRequiredHandler } from "./api.js";
import { h, toast, refreshIcons, openModal, closeModal } from "./ui.js";
import { render as renderOverview, cleanup as cleanupOverview } from "./pages/overview.js";
import { render as renderMailboxes, openCreateMailbox } from "./pages/mailboxes.js";
import { render as renderDetail, cleanup as cleanupDetail } from "./pages/detail.js";
import { render as renderRetention } from "./pages/retention.js";
import { render as renderDomainCache } from "./pages/domain-cache.js";
import { render as renderGmail } from "./pages/gmail.js";
import { render as renderKeys } from "./pages/keys.js";
import { render as renderAccess } from "./pages/access.js";

const root = document.getElementById("app");
const titleEl = document.getElementById("page-title");
const eyebrowEl = document.getElementById("page-eyebrow");

const TITLES = {
  overview:      ["Overview",     "Admin console", "Service health, traffic and providers at a glance."],
  mailboxes:     ["Mailboxes",    "Admin console", "Create, search and manage temporary addresses."],
  detail:        ["Mailbox",      "Mailboxes",     "Messages for one address."],
  retention:     ["Retention",    "Admin console", "Automatic cleanup rules per provider."],
  "domain-cache":["Domain cache", "Admin console", "Cached provider domains and refresh schedule."],
  gmail:         ["Gmail",        "Admin console", "Connect Google accounts for +alias mailboxes."],
  keys:          ["Keys",         "Admin console", "Issue scoped keys, reveal secrets, and open the dashboard as one."],
  access:        ["Access",       "Admin console", "What this key can do. Read-only."],
};

const PREV_KEY = "mailtm_api_key_prev";
/** Latest GET /v1/admin/keys/me, or null when the call has not succeeded. */
let currentMe = null;
let currentCleanup = null;

/* ============================================================
   Mobile sidebar drawer
   ============================================================ */
const sidebar   = document.getElementById("sidebar");
const backdrop  = document.getElementById("sidebar-backdrop");
const hamburger = document.getElementById("hamburger-btn");

function openSidebar() {
  sidebar.classList.add("is-open");
  backdrop.classList.add("is-open");
  hamburger?.setAttribute("aria-expanded", "true");
  // trap focus loosely — close on backdrop click / Escape
  document.addEventListener("keydown", onSidebarKeydown);
}

function closeSidebar() {
  sidebar.classList.remove("is-open");
  backdrop.classList.remove("is-open");
  hamburger?.setAttribute("aria-expanded", "false");
  document.removeEventListener("keydown", onSidebarKeydown);
}

function onSidebarKeydown(e) {
  if (e.key === "Escape") { closeSidebar(); hamburger?.focus(); }
}

hamburger?.addEventListener("click", () => {
  sidebar.classList.contains("is-open") ? closeSidebar() : openSidebar();
});
backdrop?.addEventListener("click", closeSidebar);

// Close drawer on nav link click (mobile)
sidebar?.querySelectorAll(".nav-link").forEach((a) => {
  a.addEventListener("click", () => {
    if (window.innerWidth <= 640) closeSidebar();
  });
});

// Skip link keyboard accessibility (focus main without corrupting SPA hash)
document.querySelector(".skip-link")?.addEventListener("click", (e) => {
  e.preventDefault();
  const target = document.getElementById("app");
  if (target) {
    target.setAttribute("tabindex", "-1");
    target.focus();
  }
});

/* ============================================================
   Health + auth-mode banner
   ============================================================ */
async function ping() {
  const pill   = document.getElementById("health-pill");
  const text   = document.getElementById("health-text");
  const pillSm = document.getElementById("health-pill-sm");
  const dotSm  = document.getElementById("health-dot-sm");
  const textSm = document.getElementById("health-text-sm");

  let degraded = null;
  try {
    const body = await api.health();
    // Extended health: domain_cache -> {last_refresh, domains, error}.
    const cache = (body && body.domain_cache) || {};
    const failing = Object.entries(cache).filter(([, m]) => m && m.error).map(([slug]) => slug);
    degraded = failing.length ? failing : null;

    if (!degraded) {
      setHealthState(pill, text, "on", "online");
      setHealthState(pillSm, null, "on");
      if (dotSm) applyDot(dotSm, "var(--ok)", "rgba(65,217,154,.9)");
      if (textSm) { textSm.textContent = `online · ${location.host}`; textSm.removeAttribute("title"); }
    }
  } catch {
    degraded = null;
    setHealthState(pill, text, "off", "offline");
    setHealthState(pillSm, null, "off");
    if (dotSm) applyDot(dotSm, "var(--danger)", "rgba(255,125,125,.8)");
    if (textSm) { textSm.textContent = `offline · ${location.host}`; textSm.title = ""; }
  }

  if (degraded) {
    const hint = `Domain cache refresh failing: ${degraded.join(", ")}`;
    setHealthState(pill, text, "warn", "degraded", hint);
    setHealthState(pillSm, null, "warn");
    if (dotSm) applyDot(dotSm, "var(--warn)", "rgba(255,190,90,.9)");
    if (textSm) { textSm.textContent = `degraded · ${location.host}`; textSm.title = hint; }
  }

  try {
    const cfg = await api.config();
    if (cfg?.client_version || cfg?.version) {
      updateVersionTags(cfg.client_version || cfg.version);
    }
    const warn = document.getElementById("key-warning");
    if (warn) warn.hidden = !!cfg.api_key_required;
  } catch { /* server too old / unreachable: keep banner state unset */ }

  try {
    currentMe = await api.keyMe();
  } catch {
    currentMe = null;
  }
  applyPrincipalNav();
  syncPrevKeyButton();
  redirectIfHidden();
}

function setHealthState(pill, textEl, state, label, titleText) {
  if (!pill) return;
  pill.classList.remove("on", "off", "warn");
  pill.classList.add(state);
  if (textEl && label) { textEl.textContent = label; textEl.title = titleText || ""; }
}

function applyDot(dot, bg, shadow) {
  dot.style.background  = bg;
  dot.style.boxShadow   = `0 0 10px ${shadow}`;
}

function hasAction(name) {
  const actions = currentMe?.scope?.actions;
  return Array.isArray(actions) && actions.includes(name);
}

/** Root sees Keys, Domain cache, and Gmail credentials. Issued keys do not. */
function applyPrincipalNav() {
  const isRoot = currentMe?.is_root === true;
  const known  = currentMe != null;
  const show   = (route, visible) => {
    const link = document.querySelector(`.nav-link[data-route="${route}"]`);
    if (link) link.hidden = !visible;
  };
  show("keys",         !known || isRoot);
  show("domain-cache", !known || isRoot);
  show("access",       true);
  const retention = !known || isRoot || hasAction("retention:read") || hasAction("retention:write");
  show("retention", retention);
  const gmail = !known || isRoot || hasAction("parents:read") || hasAction("parents:add");
  show("gmail", gmail);
}

/** Leave a page the current principal is not allowed to see. */
function redirectIfHidden() {
  if (currentMe == null) return;
  const name = parseHash().name;
  const link = document.querySelector(`.nav-link[data-route="${name}"]`);
  if (link?.hidden) location.hash = name === "keys" ? "#/access" : "#/";
}

function readPrevKey() {
  try { return localStorage.getItem(PREV_KEY) || ""; } catch { return ""; }
}

function syncPrevKeyButton() {
  const btn = document.getElementById("prev-key-btn");
  if (btn) btn.hidden = !readPrevKey();
}

function restorePrevKey() {
  const prev = readPrevKey();
  if (!prev) return;
  setApiKey(prev);
  try { localStorage.removeItem(PREV_KEY); } catch { /* private mode */ }
  location.reload();
}

/* ============================================================
   Version & Update Checking
   ============================================================ */
let currentVersion = "0.5.0"; // x-release-please-version
let latestUpdateInfo = null;

function updateVersionTags(ver) {
  currentVersion = (ver || currentVersion).replace(/^v/, "");
  const tagEl = document.getElementById("version-tag");
  if (tagEl) tagEl.textContent = `v${currentVersion}`;
  const footVer = document.getElementById("foot-version");
  if (footVer) footVer.textContent = `v${currentVersion}`;
}

function compareSemver(v1, v2) {
  const p1 = (v1 || "").replace(/^v/, "").split(".").map((n) => parseInt(n, 10) || 0);
  const p2 = (v2 || "").replace(/^v/, "").split(".").map((n) => parseInt(n, 10) || 0);
  const len = Math.max(p1.length, p2.length, 3);
  for (let i = 0; i < len; i++) {
    const n1 = p1[i] || 0;
    const n2 = p2[i] || 0;
    if (n1 > n2) return 1;
    if (n1 < n2) return -1;
  }
  return 0;
}

async function checkUpdates(manual = false) {
  const dot = document.getElementById("version-dot");
  const refreshBtn = document.getElementById("version-refresh-btn");
  const footBtn = document.getElementById("foot-check-updates-btn");

  refreshBtn?.classList.add("is-loading");
  footBtn?.classList.add("is-loading");

  try {
    const info = await api.checkUpdates();
    if (!info || !info.latest) {
      if (manual) toast("Could not fetch latest release info.", "warn");
      return;
    }
    latestUpdateInfo = info;
    const isNewer = compareSemver(info.latest, currentVersion) > 0;
    if (dot) {
      dot.className = `version-dot ${isNewer ? "update" : "ok"}`;
      dot.title = isNewer ? `Update available: v${info.latest}` : `Up to date: v${currentVersion}`;
    }

    if (isNewer) {
      if (manual) openUpdateModal(info);
      else toast(`New version available: v${info.latest}! Click to view.`, "info", "sparkles", 8000, () => openUpdateModal(info));
    } else if (manual) {
      toast(`You're up to date! maily v${currentVersion} is the latest version.`, "ok", "check-circle-2");
    }
  } catch (err) {
    if (manual) toast("Could not check updates: " + (err.message || "network error"), "err");
  } finally {
    refreshBtn?.classList.remove("is-loading");
    footBtn?.classList.remove("is-loading");
    document.querySelectorAll(".version-refresh-btn .spin, #foot-check-updates-btn .spin, #version-badge .spin").forEach((el) => {
      el.classList.remove("spin");
    });
  }
}

function openUpdateModal(info) {
  const wrap = h("div", { class: "update-modal-body" },
    h("div", { class: "update-version-card" },
      h("div", { class: "update-badge-row" },
        h("span", { class: "pill pill--ok" }, `Latest: v${info.latest}`),
        h("span", { class: "pill pill--muted" }, `Installed: v${currentVersion}`)),
      info.name && info.name !== `v${info.latest}` ? h("h4", { style: "margin-top:var(--s-2);font-weight:700" }, info.name) : null,
      info.notes ? h("p", { class: "small muted", style: "margin-top:var(--s-2);white-space:pre-wrap;max-height:120px;overflow:auto" }, info.notes.slice(0, 300) + (info.notes.length > 300 ? "…" : "")) : null),
    h("div", { class: "update-instructions mt-4" },
      h("label", { style: "font-weight:600;font-size:var(--fs-13);display:block;margin-bottom:var(--s-2)" }, "How to upgrade:"),
      h("div", { class: "field", style: "margin-bottom:var(--s-2)" },
        h("span", { class: "small muted" }, "Docker compose:"),
        h("div", { class: "pass-wrap" },
          h("input", { readonly: true, value: "docker compose pull && docker compose up -d", style: "font-family:var(--font-mono);font-size:var(--fs-12)" }))),
      h("div", { class: "field", style: "margin-bottom:var(--s-2)" },
        h("span", { class: "small muted" }, "Standalone Python Client:"),
        h("div", { class: "pass-wrap" },
          h("input", { readonly: true, value: "maily-client update", style: "font-family:var(--font-mono);font-size:var(--fs-12)" }))),
      h("div", { class: "field", style: "margin-bottom:0" },
        h("span", { class: "small muted" }, "Git clone:"),
        h("div", { class: "pass-wrap" },
          h("input", { readonly: true, value: "git pull && uv sync", style: "font-family:var(--font-mono);font-size:var(--fs-12)" })))));

  openModal({
    title: "Software Update Available",
    sub: `maily v${info.latest} is now available`,
    body: wrap,
    wide: true,
    actions: [
      { label: "Close" },
      {
        label: "View on GitHub",
        kind: "btn-primary",
        onClick: () => {
          window.open(info.release_url || "https://github.com/stormsia/maily/releases", "_blank", "noopener");
        },
      },
    ],
  });
  refreshIcons();
}

/* ============================================================
   Settings / API key modal
   ============================================================ */
function openSettings() {
  const input = h("input", {
    type: "password", value: getApiKey(), placeholder: "sk-… / your server key",
    autocomplete: "off", spellcheck: "false", "aria-label": "API key",
    style: "font-family:var(--font-mono)",
  });
  const toggle = h("button", {
    class: "icon-btn", "aria-label": "Show or hide API key", title: "Show / hide",
    onclick: () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      toggle.querySelector("i, svg")?.setAttribute("data-lucide", show ? "eye-off" : "eye");
      refreshIcons();
      input.focus();
    },
  }, h("i", { "data-lucide": "eye" }));

  const updateStatusText = h("span", { class: "small muted" },
    latestUpdateInfo
      ? (compareSemver(latestUpdateInfo.latest, currentVersion) > 0 ? `Update available: v${latestUpdateInfo.latest}` : "Up to date")
      : "Not checked yet");

  const checkBtn = h("button", {
    class: "btn btn-ghost btn-sm", type: "button",
    onclick: async () => {
      checkBtn.disabled = true;
      checkBtn.classList.add("is-loading");
      await checkUpdates(true);
      checkBtn.disabled = false;
      checkBtn.classList.remove("is-loading");
      if (latestUpdateInfo) {
        updateStatusText.textContent = compareSemver(latestUpdateInfo.latest, currentVersion) > 0
          ? `Update available: v${latestUpdateInfo.latest}`
          : "Up to date";
      }
      refreshIcons();
    },
  }, h("i", { "data-lucide": "refresh-cw" }), h("span", {}, "Check now"));

  const versionSection = h("div", { class: "settings-section mt-6", style: "border-top:1px solid var(--border);padding-top:var(--s-4)" },
    h("div", { style: "display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--s-2)" },
      h("label", { style: "font-weight:600;font-size:var(--fs-13)" }, "Version & Updates"),
      checkBtn),
    h("div", { style: "display:flex;align-items:center;gap:var(--s-3);margin-bottom:var(--s-3)" },
      h("span", { class: "mono small" }, `Installed: v${currentVersion}`),
      h("span", { class: "foot-sep" }, "·"),
      updateStatusText),
    h("div", { style: "display:flex;gap:var(--s-4);font-size:var(--fs-12)" },
      h("a", { href: "https://github.com/stormsia/maily", target: "_blank", rel: "noopener", style: "display:inline-flex;align-items:center;gap:4px;color:var(--accent)" },
        h("i", { "data-lucide": "github" }), "GitHub Repository"),
      h("a", { href: "https://github.com/stormsia/maily/releases", target: "_blank", rel: "noopener", style: "display:inline-flex;align-items:center;gap:4px;color:var(--muted)" },
        h("i", { "data-lucide": "history" }), "Releases & Changelog")));

  const wrap = h("div", {},
    h("div", { class: "field" },
      h("label", {}, "API key"),
      h("div", { class: "pass-wrap" }, input, toggle),
      h("p", { class: "field-hint" }, "Required only if the server runs with MAILY_API_KEY set. Stored locally in your browser.")),
    versionSection);

  openModal({
    title: "Settings",
    sub: "Connection, authentication & version",
    body: wrap,
    actions: [
      {
        label: "Clear", keepOpen: true,
        onClick: () => { input.value = ""; setApiKey(""); toast("API key cleared.", "info", "key-round"); route(); },
      },
      { spacer: true },
      { label: "Cancel" },
      {
        label: "Save key", kind: "btn-primary",
        onClick: () => {
          setApiKey(input.value.trim());
          toast(input.value.trim() ? "API key saved locally." : "Saved — running without a key.", "ok", "key-round");
          route();
          ping();
        },
      },
    ],
  });
}

/* 401 handler: prompt for the key once, retry if the user saves one. */
let keyModalOpen = false;
setAuthRequiredHandler(async () => {
  if (keyModalOpen) return false;
  keyModalOpen = true;
  const saved = await new Promise((resolve) => {
    const input = h("input", {
      type: "password", placeholder: "Paste API key",
      "aria-label": "API key", style: "font-family:var(--font-mono)",
    });
    openModal({
      title: "API key required",
      sub: "The server answered 401. Paste the key configured as MAILY_API_KEY.",
      body: h("div", { class: "field" }, h("label", {}, "API key"), input),
      actions: [
        { label: "Continue without key", onClick: () => resolve(false) },
        {
          label: "Save & retry", kind: "btn-primary",
          onClick: () => {
            const v = input.value.trim();
            if (!v) { resolve(false); return; }
            setApiKey(v);
            toast("API key saved — retrying.", "ok", "key-round");
            resolve(true);
          },
        },
      ],
    });
    // Overlay-dismiss or Escape counts as "no key".
    const obs = new MutationObserver(() => {
      if (!document.getElementById("modal-root").firstChild) {
        obs.disconnect();
        resolve(false);
      }
    });
    obs.observe(document.getElementById("modal-root"), { childList: true });
    setTimeout(() => { obs.disconnect(); }, 120000);
  });
  keyModalOpen = false;
  closeModal();
  return saved;
});

/* ============================================================
   Router
   ============================================================ */
function parseHash() {
  const raw = location.hash.replace(/^#/, "") || "/";
  const parts = raw.split("/").filter(Boolean);
  if (!parts.length) return { name: "overview" };
  if (parts[0] === "mailboxes" && parts[1]) return { name: "detail", id: decodeURIComponent(parts[1]) };
  if (parts[0] === "mailboxes")   return { name: "mailboxes" };
  if (parts[0] === "retention")   return { name: "retention" };
  if (parts[0] === "domain-cache") return { name: "domain-cache" };
  if (parts[0] === "gmail")       return { name: "gmail" };
  if (parts[0] === "keys")        return { name: "keys" };
  if (parts[0] === "access")      return { name: "access" };
  return { name: "overview" };
}

function setNav(name) {
  const key = name === "detail" ? "mailboxes" : name;
  document.querySelectorAll(".nav-link").forEach((a) =>
    a.classList.toggle("active", a.dataset.route === key));
}

async function route() {
  closeSidebar();
  const r = parseHash();
  try { currentCleanup?.(); } catch { /* page torn down already */ }
  currentCleanup = r.name === "overview" ? cleanupOverview
    : r.name === "detail" ? cleanupDetail
    : null;
  setNav(r.name);
  const [title, eyebrow, sub] = TITLES[r.name] || TITLES.overview;
  titleEl.textContent   = title;
  eyebrowEl.textContent = eyebrow;

  // Restart page-in animation
  root.style.animation = "none";
  void root.offsetWidth;
  root.style.animation = "";

  try {
    if      (r.name === "overview")      await renderOverview(root);
    else if (r.name === "mailboxes")     await renderMailboxes(root);
    else if (r.name === "detail")        await renderDetail(root, r.id);
    else if (r.name === "retention")     await renderRetention(root, currentMe);
    else if (r.name === "domain-cache")  await renderDomainCache(root);
    else if (r.name === "gmail")         await renderGmail(root, currentMe);
    else if (r.name === "keys")          await renderKeys(root);
    else if (r.name === "access")        await renderAccess(root);
  } catch (e) {
    root.innerHTML = "";
    root.append(h("div", { class: "error-box" },
      h("i", { "data-lucide": "alert-triangle" }),
      h("span", {}, e?.detail || e?.message || "Something went wrong rendering this page.")));
  }

  refreshIcons();

  // Inject page subtitle
  document.querySelectorAll(".page-sub").forEach((el) => el.remove());
  if (sub) titleEl.after(h("p", { class: "page-sub" }, sub));

  // Scroll to top on route change (helps mobile UX)
  window.scrollTo({ top: 0, behavior: "instant" });
}

window.addEventListener("hashchange", route);

/* ============================================================
   Wiring
   ============================================================ */
document.getElementById("settings-btn")?.addEventListener("click", openSettings);
document.getElementById("key-btn")?.addEventListener("click", openSettings);
document.getElementById("prev-key-btn")?.addEventListener("click", restorePrevKey);
document.getElementById("version-badge")?.addEventListener("click", () => checkUpdates(true));
document.getElementById("version-refresh-btn")?.addEventListener("click", (e) => {
  e.stopPropagation();
  checkUpdates(true);
});
document.getElementById("foot-check-updates-btn")?.addEventListener("click", () => checkUpdates(true));
syncPrevKeyButton();
document.getElementById("quick-create-btn")?.addEventListener("click", () =>
  openCreateMailbox((mb) => { location.hash = `#/mailboxes/${mb.id}`; }));

ping();
setInterval(ping, 30000);
setTimeout(() => checkUpdates(false), 1500);
route();
refreshIcons();
