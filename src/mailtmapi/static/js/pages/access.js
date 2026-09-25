/* Access page: read-only view of GET /v1/admin/keys/me. No secret. */
import { api } from "../api.js";
import { h, refreshIcons, errorBox, skeletonRows, fmtDate } from "../ui.js";

const ACTIONS = [
  ["mailboxes:read", "List and open mailboxes this key owns"],
  ["mailboxes:write", "Create and delete its own mailboxes"],
  ["messages:read", "Read messages in its mailboxes"],
  ["messages:write", "Mark read and delete its messages"],
  ["stats:read", "See stats for its own mail"],
  ["retention:read", "View retention rules"],
  ["retention:write", "Change retention and run a sweep of its mail"],
  ["parents:read", "See Gmail parents it may use"],
  ["parents:add", "Connect and remove its own Gmail parents"],
];

function statusTile(label, copy, allowed) {
  const state = allowed ? "Allowed" : "Not granted";
  const icon = allowed ? "check" : "minus";
  return h("div", {
    class: allowed ? "pick-tile is-on" : "pick-tile is-off",
    role: "group",
    "aria-pressed": allowed ? "true" : "false",
    "aria-disabled": "true",
  },
    h("i", { "data-lucide": icon, class: "pick-tile-check", "aria-hidden": "true" }),
    h("span", { class: "pick-tile-body" },
      h("span", { class: "pick-tile-title" }, label),
      h("span", { class: "pick-tile-copy" }, copy),
      h("span", { class: "pick-tile-copy" }, state)));
}

function section(title, hint, body) {
  return h("div", { class: "field", style: "margin-bottom:var(--s-4)" },
    h("label", {}, title),
    hint ? h("p", { class: "field-hint" }, hint) : null,
    body);
}

function actionGrid(granted) {
  const allowed = new Set(Array.isArray(granted) ? granted : []);
  const wrap = h("div", { class: "pick-grid", role: "group", "aria-label": "Actions" });
  for (const [action, copy] of ACTIONS) {
    wrap.append(statusTile(action, copy, allowed.has(action)));
  }
  return wrap;
}

function providerGrid(providers) {
  const wrap = h("div", { class: "pick-grid", role: "group", "aria-label": "Providers" });
  if (!providers?.length) {
    wrap.append(statusTile("All providers", "Empty means every provider", true));
    return wrap;
  }
  for (const slug of providers) {
    wrap.append(statusTile(String(slug), "Allowed", true));
  }
  return wrap;
}

function parentList(ids, accounts) {
  const byId = new Map();
  for (const account of accounts) {
    const id = Number(account?.id);
    if (Number.isInteger(id)) byId.set(id, account);
  }
  const summary = h("span", { class: "parent-picker-label" },
    ids.length ? `${ids.length} root parent${ids.length === 1 ? "" : "s"}` : "No root Gmail parents");
  const list = h("div", { class: "parent-picker-list", role: "list", "aria-label": "Gmail parents" });
  if (!ids.length) {
    list.append(h("p", { class: "parent-picker-empty" }, "No root Gmail parents."));
  } else {
    for (const raw of ids) {
      const id = Number(raw);
      const account = byId.get(id);
      const email = account?.email || `${raw} · (not visible)`;
      list.append(h("div", { class: "parent-picker-row", role: "listitem" },
        h("span", { class: "parent-picker-main" },
          h("span", { class: "parent-picker-email" }, email),
          h("span", { class: "parent-picker-id" }, String(raw)))));
    }
  }
  const panel = h("div", { class: "parent-picker-panel" }, list);
  const toggle = h("button", {
    type: "button",
    class: "parent-picker-toggle",
    "aria-expanded": "false",
    "aria-label": "Gmail parents",
    onclick: () => {
      const open = !root.classList.contains("is-open");
      root.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    },
  }, summary, h("i", { "data-lucide": "chevron-down", class: "parent-picker-chevron", "aria-hidden": "true" }));
  const root = h("div", { class: "parent-picker" }, toggle, panel);
  return root;
}

function retentionBlock(rows) {
  if (!rows.length) {
    return h("span", { class: "muted" }, "Follows root retention");
  }
  const grid = h("div", { class: "ret-grid" });
  for (const item of rows) {
    grid.append(h("div", { class: "card ret-card" },
      h("div", { class: "ret-card-top" },
        h("span", { class: "prov-name mono" }, item.provider || "—")),
      h("div", { class: "prov-metrics" },
        h("div", { class: "prov-metric" },
          h("b", {}, item.mailbox_ttl_hours == null ? "—" : String(item.mailbox_ttl_hours)),
          h("span", {}, "mailbox hours")),
        h("div", { class: "prov-metric" },
          h("b", {}, item.message_ttl_hours == null ? "—" : String(item.message_ttl_hours)),
          h("span", {}, "message hours")))));
  }
  return grid;
}

export async function render(root) {
  root.innerHTML = "";
  root.append(skeletonRows(3));

  let me;
  let accounts = [];
  try {
    [me, accounts] = await Promise.all([
      api.keyMe(),
      api.gmailAccounts().catch(() => []),
    ]);
  } catch (e) {
    root.innerHTML = "";
    root.append(errorBox(e.detail || "Could not load this key.", () => render(root)));
    refreshIcons();
    return;
  }

  root.innerHTML = "";
  if (me?.is_root) {
    root.append(h("div", { class: "card" },
      h("div", { class: "section-head", style: "margin-top:0" },
        h("h2", {}, "Root key"),
        h("span", { class: "pill pill--on" }, "root")),
      h("p", { class: "muted" },
        "This session is the root key and can do everything."),
      h("a", { class: "btn btn-ghost", href: "#/keys" },
        h("i", { "data-lucide": "key-round" }),
        h("span", {}, "Keys"))));
    refreshIcons();
    return;
  }

  const scope = me?.scope || {};
  const retention = Array.isArray(me?.key_retention) ? me.key_retention : [];
  root.append(h("div", { class: "card" },
    h("div", { class: "section-head", style: "margin-top:0" },
      h("h2", {}, me?.name || "This key"),
      h("span", { class: "pill pill--off" }, "read-only")),
    section("Expiry", null, h("span", { class: "mono" }, me?.expires_at ? fmtDate(me.expires_at) : "never")),
    section("Actions", null, actionGrid(scope.actions)),
    section("Providers", "Empty means all providers.", providerGrid(scope.providers)),
    section("Gmail parents", "Empty means no root Gmail parents.", parentList(scope.parent_ids || [], accounts)),
    section("Retention", "A blank provider follows the root TTL.", retentionBlock(retention))));

  root.append(h("div", { class: "note" },
    h("i", { "data-lucide": "info" }),
    h("span", {}, "This page only shows what this key can do. It cannot change the scope, and it never shows the secret.")));
  refreshIcons();
}
