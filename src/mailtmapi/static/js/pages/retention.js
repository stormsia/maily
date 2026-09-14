/* Retention page: per-provider TTL cards + global sweep. */
import { api } from "../api.js";
import { h, toast, refreshIcons, confirmDialog, emptyState, errorBox, skeletonRows } from "../ui.js";

function numField(label, value) {
  const input = h("input", {
    type: "number", min: "1", step: "1",
    placeholder: "disabled",
    value: value ?? "",
    "aria-label": label,
  });
  return h("div", { class: "field", style: "margin:0;flex:1" }, h("label", {}, label), input);
}

export async function render(root) {
  root.innerHTML = "";
  root.append(skeletonRows(3));

  let providers = [];
  let rows = [];
  try {
    [providers, rows] = await Promise.all([
      api.providers().catch(() => []),
      api.retention(),
    ]);
  } catch (e) {
    root.innerHTML = "";
    root.append(errorBox(e.detail || "Could not load retention rules.", () => render(root)));
    refreshIcons();
    return;
  }

  const byProvider = Object.fromEntries(rows.map((r) => [r.provider, r]));
  const slugs = [...new Set([...providers.map((p) => p.slug), ...Object.keys(byProvider)])];

  root.innerHTML = "";
  const sweepBtn = h("button", { class: "btn btn-primary", onclick: runSweep },
    h("i", { "data-lucide": "timer" }), h("span", {}, "Run sweep now"));
  root.append(h("div", { class: "toolbar", style: "margin-top:0" },
    h("p", { class: "muted", style: "flex:1;min-width:220px" },
      "Automatic cleanup for old mailboxes and messages. Empty fields mean disabled."),
    sweepBtn));

  if (!slugs.length) {
    root.append(emptyState({
      icon: "timer", title: "No providers yet",
      copy: "Retention rules appear here once a provider has been used at least once.",
    }));
    return;
  }

  const grid = h("div", { class: "ret-grid" });
  for (const slug of slugs) {
    const existing = byProvider[slug];
    const boxTtl = numField("Mailbox TTL (hours)", existing?.mailbox_ttl_hours);
    const msgTtl = numField("Message TTL (hours)", existing?.message_ttl_hours);
    const boxInput = boxTtl.querySelector("input");
    const msgInput = msgTtl.querySelector("input");
    const stateBadge = h("span", { class: `pill ${(existing?.mailbox_ttl_hours != null || existing?.message_ttl_hours != null) ? "pill--on" : "pill--off"}` },
      (existing?.mailbox_ttl_hours != null || existing?.message_ttl_hours != null) ? "enabled" : "disabled");

    const saveBtn = h("button", { class: "btn btn-primary btn-sm", onclick: async () => {
      const parse = (v) => (v === "" ? null : Math.floor(Number(v)));
      const mb = parse(boxInput.value);
      const ms = parse(msgInput.value);
      if (mb === null && ms === null) { toast("Set at least one TTL — or use Disable.", "err"); return; }
      if ((mb !== null && !(mb >= 1)) || (ms !== null && !(ms >= 1))) {
        toast("TTL values must be 1 hour or more.", "err");
        return;
      }
      saveBtn.disabled = true;
      try {
        await api.saveRetention(slug, { mailbox_ttl_hours: mb, message_ttl_hours: ms });
        toast(`Retention saved for ${slug}.`, "ok", "check-circle-2");
        render(root);
      } catch (e) {
        toast(e.detail || "Could not save.", "err");
        saveBtn.disabled = false;
      }
    } }, "Save");
    const disableBtn = h("button", { class: "btn btn-ghost btn-sm", onclick: async () => {
      if (!existing) { toast("Already disabled.", "info"); return; }
      const ok = await confirmDialog({
        title: `Disable retention for ${slug}?`,
        message: "Automatic cleanup stops for this provider. Existing data is kept.",
        confirmLabel: "Disable",
      });
      if (!ok) return;
      try {
        await api.disableRetention(slug);
        toast(`Retention disabled for ${slug}.`, "ok", "check-circle-2");
        render(root);
      } catch (e) { toast(e.detail || "Could not disable.", "err"); }
    } }, "Disable");

    grid.append(h("div", { class: "card ret-card" },
      h("div", { class: "ret-card-top" },
        h("span", { class: "prov-name mono" }, slug),
        stateBadge),
      h("div", { style: "display:flex;gap:12px" }, boxTtl, msgTtl),
      h("div", { style: "display:flex;gap:8px;justify-content:flex-end" }, disableBtn, saveBtn)));
  }
  root.append(grid);

  root.append(h("div", { class: "note" },
    h("i", { "data-lucide": "info" }),
    h("span", {},
      "Mailboxes are deleted {mailbox TTL}h after creation; messages {message TTL}h after receipt. ",
      "Provider-side deletion is best-effort — local records are always removed.")));
  refreshIcons();

  async function runSweep(e) {
    const btn = e.currentTarget;
    btn.disabled = true;
    try {
      const res = await api.runRetention();
      toast(`Deleted ${res.mailboxes_deleted ?? 0} mailboxes, ${res.messages_deleted ?? 0} messages.`, "ok", "timer");
    } catch (err) {
      toast(err.detail || "Sweep failed.", "err");
    } finally {
      btn.disabled = false;
    }
  }
}
