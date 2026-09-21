/* Domain cache page: refresh schedule + per-provider cache state. */
import { api } from "../api.js";
import { h, toast, refreshIcons, emptyState, errorBox, skeletonRows } from "../ui.js";

function fmtUpdated(iso) {
  if (!iso) return "never";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "never" : d.toLocaleString();
}

function providerCard(slug, c, caching) {
  const statusPill = h("span", { class: `pill ${caching ? "pill--on" : "pill--off"}` },
    caching ? "caching" : "off");
  const errorText = c?.error
    ? h("div", { class: "cache-error", title: c.error, role: "status" },
        h("span", { class: "cache-error-label" }, "refresh failed:"),
        " ",
        h("span", { class: "cache-error-msg" }, c.error))
    : null;
  return h("div", { class: "card ret-card" },
    h("div", { class: "ret-card-top" },
      h("span", { class: "prov-name mono" }, slug),
      h("span", { class: "ret-card-pills" }, statusPill)),
    h("div", { class: "prov-nums" },
      h("div", {}, h("b", {}, String(c?.domains_count ?? 0)), h("span", {}, "domains cached"))),
    errorText,
    h("div", { class: "cache-meta" },
      h("span", {}, "Last refresh: "),
      h("span", { class: "mono" }, fmtUpdated(c?.updated_at))));
}

export async function render(root) {
  root.innerHTML = "";
  root.append(skeletonRows(3));

  let providers = [];
  let settings;
  try {
    [providers, settings] = await Promise.all([
      api.providers().catch(() => []),
      api.domainCache(),
    ]);
  } catch (e) {
    root.innerHTML = "";
    root.append(errorBox(e.detail || "Could not load the domain cache.", () => render(root)));
    refreshIcons();
    return;
  }

  const byCache = Object.fromEntries((settings.providers || []).map((p) => [p.provider, p]));
  const slugs = [...new Set([...providers.map((p) => p.slug), ...Object.keys(byCache)])];
  const caching = !!settings.enabled;
  const minutes = Math.max(1, Math.round((settings.interval_seconds || 1800) / 60));

  root.innerHTML = "";

  /* toolbar */
  const refreshBtn = h("button", { class: "btn btn-primary", onclick: runRefresh },
    h("i", { "data-lucide": "refresh-cw" }), h("span", {}, "Refresh now"));
  root.append(h("div", { class: "toolbar toolbar--top" },
    h("p", { class: "muted", style: "flex:1;min-width:220px" },
      caching
        ? `Provider domain lists are cached locally for mailbox creation. Automatic refresh runs every ${minutes} minute${minutes === 1 ? "" : "s"}.`
        : "Provider domain lists are cached locally for mailbox creation. Automatic refresh is off."),
    refreshBtn));

  /* settings card */
  const statusPill = h("span", { class: `pill ${caching ? "pill--on" : "pill--off"}` },
    caching ? "enabled" : "paused");
  const enabledInput = h("input", { type: "checkbox", checked: caching, "aria-label": "Automatic refresh" });
  enabledInput.addEventListener("change", () => {
    statusPill.className = `pill ${enabledInput.checked ? "pill--on" : "pill--off"}`;
    statusPill.textContent = enabledInput.checked ? "enabled" : "paused";
  });
  const toggleWrap = h("label", { class: "switch" }, enabledInput,
    h("span", { class: "switch-track" }, h("span", { class: "switch-knob" })));
  const minutesInput = h("input", {
    type: "number", min: "1", step: "1", value: minutes,
    "aria-label": "Refresh interval in minutes",
  });
  const saveBtn = h("button", { class: "btn btn-primary", onclick: saveSettings },
    h("i", { "data-lucide": "save" }), h("span", {}, "Save"));

  root.append(h("div", { class: "card ret-card mt-4" },
    h("div", { class: "ret-card-top" },
      h("div", {},
        h("h2", { class: "chart-title" }, "Refresh schedule"),
        h("p", { class: "muted small", style: "margin-top:2px" }, "When and whether domain lists are fetched from each provider.")),
      statusPill),
    h("div", { class: "cache-settings" },
      h("label", { class: "cache-toggle" }, toggleWrap, h("span", {}, "Automatic refresh")),
      h("div", { class: "field", style: "margin:0;flex:0 1 190px;min-width:150px" },
        h("label", {}, "Interval (minutes)"),
        minutesInput),
      saveBtn)));

  /* providers grid */
  if (!slugs.length) {
    root.append(emptyState({
      icon: "database", title: "No providers yet",
      copy: "Cached domains show up here once a provider has been used at least once.",
    }));
    refreshIcons();
    return;
  }

  const grid = h("div", { class: "ret-grid" });
  for (const slug of slugs) grid.append(providerCard(slug, byCache[slug], caching));
  root.append(grid);

  root.append(h("div", { class: "note" },
    h("i", { "data-lucide": "info" }),
    h("span", {}, "New mailboxes are created from the cached domain lists. Refreshing helps when a provider adds new domains. Caching is offline-safe.")));
  refreshIcons();

  async function runRefresh(e) {
    const btn = e.currentTarget;
    btn.disabled = true;
    btn.classList.add("is-loading");
    try {
      const res = await api.runDomainCache();
      const refreshed = res.refreshed || [];
      toast(`Refreshed ${refreshed.length} provider${refreshed.length === 1 ? "" : "s"}.`, "ok", "refresh-cw");
    } catch (err) {
      const names = err.failed?.length ? err.failed.join(", ") : "";
      toast(
        names
          ? `Refresh failed for: ${names}`
          : err.detail || "Refresh failed.",
        "err",
        "refresh-cw",
      );
    } finally {
      btn.disabled = false;
      btn.classList.remove("is-loading");
      render(root);
    }
  }

  async function saveSettings() {
    const mins = Number.parseInt(minutesInput.value, 10);
    if (!Number.isInteger(mins) || mins < 1) {
      toast("Interval must be at least 1 minute.", "err");
      return;
    }
    saveBtn.disabled = true;
    saveBtn.classList.add("is-loading");
    try {
      await api.saveDomainCache({ enabled: enabledInput.checked, interval_seconds: mins * 60 });
      toast("Domain cache settings saved.", "ok", "check-circle-2");
      render(root);
    } catch (e) {
      toast(e.detail || "Could not save settings.", "err");
      saveBtn.disabled = false;
      saveBtn.classList.remove("is-loading");
    }
  }
}