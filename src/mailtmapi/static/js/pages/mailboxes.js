/* Mailboxes page: search, provider filter, create modal, list w/ delete. */
import { api } from "../api.js";
import {
  h, esc, toast, refreshIcons, openModal, confirmDialog, emptyState,
  errorBox, skeletonRows, addressCell, providerBadge, statusPill, fmtDate,
} from "../ui.js";

/** Shared "create mailbox" modal — also used by the topbar quick button. */
export async function openCreateMailbox(onCreated) {
  let providers = [];
  try {
    providers = await api.providers();
  } catch (e) {
    toast(e.detail || "Could not load providers.", "err");
    return;
  }
  if (!providers.length) {
    toast("No providers available.", "err");
    return;
  }

  const providerSel = h("select", {}, ...providers.map((p) =>
    h("option", { value: p.slug }, `${p.slug} · ${p.kind}`)));
  const kindHint = h("p", { class: "field-hint" }, "");
  const domainField = h("div", { class: "field" },
    h("label", {}, "Domain"), h("select", {}, h("option", {}, "Loading…")));
  const domainSel = domainField.querySelector("select");
  const addressInput = h("input", { placeholder: "leave blank for random", autocomplete: "off", spellcheck: "false" });
  const addrSuffix = h("span", { class: "addr-suffix" }, "");
  const addrWrap = h("div", { class: "field-addr" }, addressInput, addrSuffix);
  const passwordInput = h("input", { type: "password", placeholder: "leave blank to auto-generate", autocomplete: "new-password" });
  const parentField = h("div", { class: "field" },
    h("label", {}, "Parent Gmail account"), h("select", {}));
  const parentSel = parentField.querySelector("select");

  async function loadTargets() {
    const slug = providerSel.value;
    const prov = providers.find((p) => p.slug === slug);
    kindHint.textContent = prov?.kind === "parent"
      ? "Parent-kind provider: pick which connected account owns the new address."
      : "Domain-kind provider: pick which domain the address is created on.";
    if (prov?.kind === "domain") {
      parentField.style.display = "none";
      domainField.style.display = "";
      domainSel.innerHTML = "";
      domainSel.append(h("option", {}, "Loading…"));
      try {
        const targets = await api.targets(slug);
        domainSel.innerHTML = "";
        if (!targets.length) domainSel.append(h("option", { value: "" }, "No domains available"));
        for (const t of targets) domainSel.append(h("option", { value: t.label || t.id }, esc(t.label || t.id)));
      } catch {
        domainSel.innerHTML = "";
        domainSel.append(h("option", { value: "" }, "Could not load domains"));
      }
    } else {
      domainField.style.display = "none";
      parentField.style.display = "";
      parentSel.innerHTML = "";
      parentSel.append(h("option", {}, "Loading…"));
      try {
        const accounts = await api.gmailAccounts();
        parentSel.innerHTML = "";
        if (!accounts.length) parentSel.append(h("option", { value: "" }, "No Gmail accounts — connect one first"));
        for (const a of accounts) parentSel.append(h("option", { value: String(a.id) }, esc(a.email)));
      } catch {
        parentSel.innerHTML = "";
        parentSel.append(h("option", { value: "" }, "Could not load accounts"));
      }
    }
    updateAddrSuffix();
  }
  domainSel.addEventListener("change", updateAddrSuffix);

  /** Show "@domain" next to the typed local part when a domain is picked. */
  function updateAddrSuffix() {
    const prov = providers.find((p) => p.slug === providerSel.value);
    addrSuffix.textContent = prov?.kind === "domain" && domainSel.value ? `@${domainSel.value}` : "";
  }
  providerSel.addEventListener("change", loadTargets);
  loadTargets();

  const form = h("div", {},
    h("div", { class: "field" }, h("label", {}, "Provider"), providerSel, kindHint),
    domainField,
    parentField,
    h("div", { class: "field-row" },
      h("div", { class: "field" }, h("label", {}, "Address ", h("span", { class: "opt" }, "(optional)")), addrWrap),
      h("div", { class: "field" }, h("label", {}, "Password ", h("span", { class: "opt" }, "(optional)")), passwordInput)));

  openModal({
    title: "New mailbox",
    sub: "Creates the address on the provider, then stores it locally.",
    body: form,
    actions: [
      { label: "Cancel" },
      {
        label: "Create mailbox", kind: "btn-primary",
        onClick: async (e) => {
          const btn = e.currentTarget;
          btn.disabled = true;
          const prov = providers.find((p) => p.slug === providerSel.value);
          const body = { provider: providerSel.value };
          const local = addressInput.value.trim();
          if (local) {
            body.address = local.includes("@") ? local : (prov?.kind === "domain" && domainSel.value ? `${local}@${domainSel.value}` : local);
          }
          if (passwordInput.value) body.password = passwordInput.value;
          if (prov?.kind === "domain" && domainSel.value) body.domain = domainSel.value;
          if (prov?.kind === "parent" && parentSel.value && /^\d+$/.test(parentSel.value)) {
            body.parent_id = Number(parentSel.value);
          }
          try {
            const mb = await api.createMailbox(body);
            toast(`Mailbox ${mb.address} created.`, "ok", "check-circle-2");
            onCreated?.(mb);
          } catch (err) {
            toast(err.detail || "Could not create mailbox.", "err");
            btn.disabled = false;
            throw err; // keeps the modal open (openModal only closes on success)
          }
        },
        noClose: false,
      },
    ],
  });
}

export async function render(root) {
  root.innerHTML = "";
  const searchInput = h("input", { class: "input", placeholder: "Search by address…", "aria-label": "Search mailboxes", type: "search" });
  const provFilter = h("select", { class: "select", "aria-label": "Filter by provider", style: "max-width:190px;padding-left:13px" },
    h("option", { value: "" }, "All providers"));
  const createBtn = h("button", { class: "btn btn-primary", onclick: () => openCreateMailbox(() => render(root)) },
    h("i", { "data-lucide": "plus" }), h("span", {}, "Create mailbox"));
  root.append(h("div", { class: "toolbar" },
    h("div", { class: "search" }, h("i", { "data-lucide": "search" }), searchInput),
    provFilter, createBtn));

  const listWrap = h("div", {});
  root.append(listWrap);
  refreshIcons();

  let all = [];
  let providers = [];
  listWrap.append(skeletonRows(7));
  try {
    [all, providers] = await Promise.all([
      api.mailboxes(),
      api.providers().catch(() => []),
    ]);
  } catch (e) {
    listWrap.innerHTML = "";
    listWrap.append(errorBox(e.detail || "Could not load mailboxes.", () => render(root)));
    refreshIcons();
    return;
  }
  for (const p of providers) provFilter.append(h("option", { value: p.slug }, p.slug));

  function draw() {
    const q = searchInput.value.trim().toLowerCase();
    const pf = provFilter.value;
    const rows = all.filter((m) =>
      (!pf || m.provider === pf) &&
      (!q || (m.address || "").toLowerCase().includes(q)));
    listWrap.innerHTML = "";
    if (!rows.length) {
      listWrap.append(emptyState({
        icon: q || pf ? "search-x" : "inbox",
        title: q || pf ? "No mailboxes match" : "No mailboxes yet",
        copy: q || pf
          ? "Try a different search, or clear the provider filter."
          : "Create your first mailbox to start receiving temporary mail.",
        actionLabel: q || pf ? undefined : "Create mailbox",
        onAction: () => openCreateMailbox(() => render(root)),
      }));
      return;
    }
    const tbody = h("tbody", {});
    for (const m of rows) {
      const tr = h("tr", { class: "clickable", tabindex: "0", role: "link", "aria-label": `Open ${m.address}` });
      const go = () => { location.hash = `#/mailboxes/${m.id}`; };
      tr.addEventListener("click", (e) => { if (!e.target.closest("button")) go(); });
      tr.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
      const openBtn = h("button", { class: "icon-btn", "aria-label": `Open ${m.address}`, title: "Open", onclick: (e) => { e.stopPropagation(); go(); } },
        h("i", { "data-lucide": "arrow-right" }));
      const delBtn = h("button", { class: "icon-btn danger", "aria-label": `Delete ${m.address}`, title: "Delete", onclick: (e) => deleteOne(e, m) },
        h("i", { "data-lucide": "trash-2" }));
      tr.append(
        h("td", {}, addressCell(m.address)),
        h("td", {}, providerBadge(m.provider)),
        h("td", {}, statusPill(m.is_active)),
        h("td", { class: "muted small mono" }, fmtDate(m.created_at)),
        h("td", {}, h("div", { class: "row-actions" }, openBtn, delBtn)));
      tbody.append(tr);
    }
    listWrap.append(h("div", { class: "table-wrap" },
      h("table", { class: "table" },
        h("thead", {}, h("tr", {},
          h("th", {}, "Address"), h("th", {}, "Provider"), h("th", {}, "Status"),
          h("th", {}, "Created"), h("th", { style: "text-align:right" }, "Actions"))),
        tbody)));
    refreshIcons();
  }

  async function deleteOne(e, m) {
    e.stopPropagation();
    const ok = await confirmDialog({
      title: "Delete mailbox?",
      message: `This removes ${m.address} on the provider too. This cannot be undone.`,
    });
    if (!ok) return;
    try {
      await api.deleteMailbox(m.id);
      toast(`Deleted ${m.address}.`, "ok", "trash-2");
      all = all.filter((x) => x.id !== m.id);
      draw();
    } catch (err) {
      toast(err.detail || "Could not delete mailbox.", "err");
    }
  }

  searchInput.addEventListener("input", draw);
  provFilter.addEventListener("change", draw);
  draw();
}
