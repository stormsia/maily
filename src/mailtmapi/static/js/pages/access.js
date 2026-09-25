/* Access page: read-only view of GET /v1/admin/keys/me. No secret. */
import { api } from "../api.js";
import { h, refreshIcons, errorBox, skeletonRows, fmtDate } from "../ui.js";

function chips(items, emptyLabel) {
  if (!items?.length) return h("span", { class: "muted" }, emptyLabel);
  return h("div", { class: "sendas" }, ...items.map((item) => h("span", { class: "chip" }, String(item))));
}

function row(label, value) {
  return h("div", { class: "field", style: "margin-bottom:var(--s-4)" },
    h("label", {}, label),
    value);
}

export async function render(root) {
  root.innerHTML = "";
  root.append(skeletonRows(3));

  let me;
  try {
    me = await api.keyMe();
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
        "This session is the root key. It is not an issued key, so it has no scope row. ",
        "Issue and inspect keys from the Keys page.")));
    refreshIcons();
    return;
  }

  const scope = me?.scope || {};
  const retention = Array.isArray(me?.key_retention) ? me.key_retention : [];
  const card = h("div", { class: "card" },
    h("div", { class: "section-head", style: "margin-top:0" },
      h("h2", {}, me?.name || "This key"),
      h("span", { class: "pill pill--off" }, "read-only")),
    row("Expiry", h("span", { class: "mono" }, me?.expires_at ? fmtDate(me.expires_at) : "never")),
    row("Providers", h("div", {},
      chips(scope.providers, "all providers"),
      h("p", { class: "field-hint" }, "Empty means all providers."))),
    row("Parent ids", h("div", {},
      chips(scope.parent_ids, "none"),
      h("p", { class: "field-hint" }, "Empty means none. This key cannot use a root Gmail parent that is not listed."))),
    row("Actions", chips(scope.actions, "none")));

  if (retention.length) {
    const grid = h("div", { class: "ret-grid" });
    for (const item of retention) {
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
    card.append(row("Retention", grid));
  } else {
    card.append(row("Retention", h("span", { class: "muted" }, "No per-key retention rows.")));
  }

  root.append(card);
  root.append(h("div", { class: "note" },
    h("i", { "data-lucide": "info" }),
    h("span", {}, "This page only shows what this key can do. It cannot change the scope, and it never shows the secret.")));
  refreshIcons();
}
