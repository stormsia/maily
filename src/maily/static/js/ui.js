/* maily admin — shared UI: DOM helpers, toasts, modals, formatting. */

export function refreshIcons() {
  if (window.lucide?.createIcons) window.lucide.createIcons();
}

/** Escape a string for safe HTML interpolation. */
export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

/** Tiny element builder: h("div", { class: "x", onclick }, children...). */
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "html") el.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
    else if (k === "dataset") Object.assign(el.dataset, v);
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, String(v));
  }
  for (const child of children.flat()) {
    if (child == null) continue;
    el.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return el;
}

/* ---------- time ---------- */
export function timeAgo(iso) {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "—";
  const s = Math.max(1, Math.floor((Date.now() - t) / 1000));
  if (s < 60)  return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60)  return `${m}m ago`;
  const hh = Math.floor(m / 60);
  if (hh < 24) return `${hh}h ago`;
  const d = Math.floor(hh / 24);
  if (d < 30)  return `${d}d ago`;
  return new Date(t).toLocaleDateString();
}

export function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : d.toLocaleString();
}

/* ---------- clipboard ---------- */
export async function copyText(text, label = "Copied to clipboard") {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    /* Fallback for non-HTTPS environments */
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.cssText = "position:fixed;opacity:0;pointer-events:none";
    document.body.append(ta);
    ta.select();
    try { document.execCommand("copy"); } catch { /* best effort */ }
    ta.remove();
  }
  toast(label, "ok", "copy");
}

/* ---------- toasts ---------- */
const ICONS = { ok: "check-circle-2", err: "alert-circle", info: "info" };
/** Duration scales with message length — short messages vanish faster. */
function toastDuration(message) {
  return Math.max(3000, Math.min(8000, 2000 + message.length * 50));
}

export function toast(message, type = "info", icon) {
  const root = document.getElementById("toast-root");
  const el = h("div", { class: `toast toast--${type}`, role: "status" },
    h("i", { "data-lucide": icon || ICONS[type] || "info" }),
    h("span", {}, message));
  root.append(el);
  refreshIcons();
  const dur = toastDuration(message);
  setTimeout(() => {
    el.classList.add("out");
    setTimeout(() => el.remove(), 260);
  }, dur);
}

/* ---------- modals ---------- */
const modalRoot = () => document.getElementById("modal-root");
let lastFocus = null;

/** All focusable elements inside `el`, in DOM order. */
function focusable(el) {
  return [...el.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )].filter((n) => !n.hidden && n.offsetParent !== null);
}

function trapFocus(dialog) {
  function onKeydown(e) {
    if (e.key !== "Tab") return;
    const nodes = focusable(dialog);
    if (!nodes.length) { e.preventDefault(); return; }
    const first = nodes[0];
    const last  = nodes[nodes.length - 1];
    if (e.shiftKey) {
      if (document.activeElement === first) { e.preventDefault(); last.focus(); }
    } else {
      if (document.activeElement === last)  { e.preventDefault(); first.focus(); }
    }
  }
  dialog.addEventListener("keydown", onKeydown);
  return () => dialog.removeEventListener("keydown", onKeydown);
}

let removeTrap = null;

export function openModal({ title, sub = "", body, actions = [], wide = false }) {
  if (!modalRoot().contains(document.activeElement)) {
    lastFocus = document.activeElement;
  }
  closeModal(true);
  const overlay = h("div", { class: "modal-overlay" });
  const dialog  = h("div", {
    class: `modal${wide ? " modal--wide" : ""}`,
    role: "dialog",
    "aria-modal": "true",
    "aria-label": title,
  });
  const head = h("div", { class: "modal-head" },
    h("div", {},
      h("h3", {}, title),
      sub ? h("p", {}, sub) : null),
    h("button", {
      class: "icon-btn",
      "aria-label": "Close dialog",
      onclick: () => closeModal(),
    }, h("i", { "data-lucide": "x" })));

  const bodyEl = h("div", { class: "modal-body" });
  if (typeof body === "string") bodyEl.innerHTML = body;
  else if (body?.nodeType) bodyEl.append(body);

  const foot = h("div", { class: "modal-foot" });
  for (const a of actions) {
    if (a.spacer) { foot.append(h("span", { class: "spacer" })); continue; }
    foot.append(h("button", {
      class: `btn ${a.kind || "btn-ghost"}`,
      onclick: async (e) => {
        try {
          if (a.onClick) await a.onClick(e);
        } catch {
          return; // handler signalled "keep open" (e.g. validation failed)
        }
        if (!a.keepOpen && !a.noClose) closeModal();
      },
    }, a.label));
  }

  dialog.append(head, bodyEl);
  if (actions.length) dialog.append(foot);
  overlay.append(dialog);
  overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) closeModal(); });
  modalRoot().append(overlay);
  refreshIcons();

  // Focus first interactive element
  const firstFocus = dialog.querySelector("input, select, textarea, button.btn-primary, button.btn");
  (firstFocus || dialog.querySelector(".icon-btn"))?.focus();

  // Install focus trap
  removeTrap?.();
  removeTrap = trapFocus(dialog);

  return { overlay, dialog, body: bodyEl, close: () => closeModal() };
}

export function closeModal(silent = false) {
  const root = modalRoot();
  if (!root.firstChild && silent) return;
  root.innerHTML = "";
  removeTrap?.();
  removeTrap = null;
  if (!silent && lastFocus?.focus) lastFocus.focus();
  lastFocus = null;
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && modalRoot().firstChild) closeModal();
});

/** Confirm dialog. Resolves true when confirmed, false on cancel/dismiss. */
export function confirmDialog({ title, message, confirmLabel = "Delete", danger = true }) {
  return new Promise((resolve) => {
    let settled = false;
    const done = (v) => { if (!settled) { settled = true; closeModal(); resolve(v); } };
    const m = openModal({
      title,
      body: h("p", { class: "muted" }, message),
      actions: [
        { label: "Cancel",       noClose: true, onClick: () => done(false) },
        { label: confirmLabel, kind: danger ? "btn-danger" : "btn-primary", noClose: true, onClick: () => done(true) },
      ],
    });
    m.overlay.addEventListener("mousedown", (e) => {
      if (e.target === m.overlay) done(false);
    }, { once: true });
  });
}

/* ---------- states ---------- */
export function emptyState({ icon = "inbox", title, copy, actionLabel, onAction, inline = false } = {}) {
  const el = h("div", { class: `empty${inline ? " empty--inline" : ""}` },
    h("div", { class: "empty-icon" }, h("i", { "data-lucide": icon })),
    h("h3", {}, title),
    h("p", {}, copy));
  if (actionLabel) el.append(h("button", { class: "btn btn-primary", onclick: onAction }, actionLabel));
  queueMicrotask(refreshIcons);
  return el;
}

export function errorBox(message, onRetry) {
  const el = h("div", { class: "error-box" },
    h("i", { "data-lucide": "alert-triangle" }),
    h("div", {},
      h("div", {}, message),
      onRetry ? h("button", { class: "btn btn-ghost btn-sm mt-4", onclick: onRetry }, "Try again") : null));
  queueMicrotask(refreshIcons);
  return el;
}

export function skeletonCards(n = 5, height = "132px") {
  const wrap = h("div", { class: "grid grid--stats" });
  for (let i = 0; i < n; i++) wrap.append(h("div", { class: "skeleton", style: `height:${height}` }));
  return wrap;
}

export function skeletonRows(n = 6) {
  const wrap = h("div", { class: "grid", style: "gap:8px" });
  for (let i = 0; i < n; i++) wrap.append(h("div", { class: "skeleton", style: "height:64px" }));
  return wrap;
}

/* ---------- inline address w/ copy ---------- */
export function addressCell(address) {
  const btn = h("button", {
    class: "copy-mini", "aria-label": `Copy ${address}`, title: "Copy address",
    onclick: (e) => { e.stopPropagation(); copyText(address, "Address copied"); },
  }, h("i", { "data-lucide": "copy" }));
  queueMicrotask(refreshIcons);
  return h("span", { class: "addr" }, address, btn);
}

/* Deterministic slug → hue (palette harmonized with design tokens). */
const BADGE_HUES = [262, 172, 152, 40, 5, 214, 330, 24];

export function slugHue(slug) {
  const hash = [...(slug || "")].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 0);
  return BADGE_HUES[hash % BADGE_HUES.length];
}

export function providerBadge(slug) {
  return h("span", { class: "badge badge--auto", style: `--badge-hue:${slugHue(slug)}` }, slug);
}

export function statusPill(active) {
  return h("span", { class: `pill ${active ? "pill--on" : "pill--off"}` }, active ? "active" : "inactive");
}
