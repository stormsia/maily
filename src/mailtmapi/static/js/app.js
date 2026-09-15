/* mailtmapi admin — entry: routing, health, settings, shared wiring. */
import { api, getApiKey, setApiKey, setAuthRequiredHandler } from "./api.js";
import { h, toast, refreshIcons, openModal, closeModal } from "./ui.js";
import { render as renderOverview, cleanup as cleanupOverview } from "./pages/overview.js";
import { render as renderMailboxes, openCreateMailbox } from "./pages/mailboxes.js";
import { render as renderDetail } from "./pages/detail.js";
import { render as renderRetention } from "./pages/retention.js";
import { render as renderDomainCache } from "./pages/domain-cache.js";
import { render as renderGmail } from "./pages/gmail.js";

const root = document.getElementById("app");
const titleEl = document.getElementById("page-title");
const eyebrowEl = document.getElementById("page-eyebrow");

const TITLES = {
  overview: ["Overview", "Admin console", "Service health, traffic and providers at a glance."],
  mailboxes: ["Mailboxes", "Admin console", "Create, search and manage temporary addresses."],
  detail: ["Mailbox", "Mailboxes", "Messages for one address."],
  retention: ["Retention", "Admin console", "Automatic cleanup rules per provider."],
  "domain-cache": ["Domain cache", "Admin console", "Cached provider domains and refresh schedule."],
  gmail: ["Gmail", "Admin console", "Connect Google accounts for +alias mailboxes."],
};

let currentCleanup = null;

/* ---------- health ---------- */
async function ping() {
  const pill = document.getElementById("health-pill");
  const text = document.getElementById("health-text");
  const pillSm = document.getElementById("health-pill-sm");
  const dotSm = document.getElementById("health-dot-sm");
  const textSm = document.getElementById("health-text-sm");
  try {
    await api.health();
    pill?.classList.remove("off");
    pill?.classList.add("on");
    if (text) text.textContent = "online";
    pillSm?.classList.remove("off");
    pillSm?.classList.add("on");
    if (dotSm) { dotSm.style.background = "var(--ok)"; dotSm.style.boxShadow = "0 0 10px rgba(65,217,154,.9)"; }
    if (textSm) textSm.textContent = `online · ${location.host}`;
  } catch {
    pill?.classList.remove("on");
    pill?.classList.add("off");
    if (text) text.textContent = "offline";
    pillSm?.classList.remove("on");
    pillSm?.classList.add("off");
    if (dotSm) { dotSm.style.background = "var(--danger)"; dotSm.style.boxShadow = "0 0 10px rgba(255,125,125,.8)"; }
    if (textSm) textSm.textContent = `offline · ${location.host}`;
  }
}

/* ---------- settings / API key modal ---------- */
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
  const wrap = h("div", {},
    h("div", { class: "field" },
      h("label", {}, "API key"),
      h("div", { class: "pass-wrap" }, input, toggle),
      h("p", { class: "field-hint" }, "Required only if the server runs with MAILTM_API_KEY set. Stored locally in your browser.")));
  openModal({
    title: "Settings",
    sub: "Connection & authentication",
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
    const input = h("input", { type: "password", placeholder: "Paste API key", "aria-label": "API key", style: "font-family:var(--font-mono)" });
    openModal({
      title: "API key required",
      sub: "The server answered 401. Paste the key configured as MAILTM_API_KEY.",
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

/* ---------- router ---------- */
function parseHash() {
  const raw = location.hash.replace(/^#/, "") || "/";
  const parts = raw.split("/").filter(Boolean);
  if (!parts.length) return { name: "overview" };
  if (parts[0] === "mailboxes" && parts[1]) return { name: "detail", id: decodeURIComponent(parts[1]) };
  if (parts[0] === "mailboxes") return { name: "mailboxes" };
  if (parts[0] === "retention") return { name: "retention" };
  if (parts[0] === "domain-cache") return { name: "domain-cache" };
  if (parts[0] === "gmail") return { name: "gmail" };
  return { name: "overview" };
}

function setNav(name) {
  const key = name === "detail" ? "mailboxes" : name;
  document.querySelectorAll(".nav-link").forEach((a) =>
    a.classList.toggle("active", a.dataset.route === key));
}

async function route() {
  const r = parseHash();
  try { currentCleanup?.(); } catch { /* page torn down already */ }
  currentCleanup = r.name === "overview" ? cleanupOverview : null;
  setNav(r.name);
  const [title, eyebrow, sub] = TITLES[r.name] || TITLES.overview;
  titleEl.textContent = title;
  eyebrowEl.textContent = eyebrow;
  root.style.animation = "none";
  void root.offsetWidth; // restart page-in animation
  root.style.animation = "";
  try {
    if (r.name === "overview") await renderOverview(root);
    else if (r.name === "mailboxes") await renderMailboxes(root);
    else if (r.name === "detail") await renderDetail(root, r.id);
    else if (r.name === "retention") await renderRetention(root);
    else if (r.name === "domain-cache") await renderDomainCache(root);
    else if (r.name === "gmail") await renderGmail(root);
  } catch (e) {
    root.innerHTML = "";
    root.append(h("div", { class: "error-box" },
      h("i", { "data-lucide": "alert-triangle" }),
      h("span", {}, e?.detail || e?.message || "Something went wrong rendering this page.")));
  }
  refreshIcons();
  document.querySelectorAll(".page-sub").forEach((el) => el.remove());
  if (sub) titleEl.after(h("p", { class: "page-sub" }, sub));
}

window.addEventListener("hashchange", route);

/* ---------- wiring ---------- */
document.getElementById("settings-btn")?.addEventListener("click", openSettings);
document.getElementById("key-btn")?.addEventListener("click", openSettings);
document.getElementById("quick-create-btn")?.addEventListener("click", () =>
  openCreateMailbox((mb) => { location.hash = `#/mailboxes/${mb.id}`; }));

ping();
setInterval(ping, 30000);
route();
refreshIcons();
