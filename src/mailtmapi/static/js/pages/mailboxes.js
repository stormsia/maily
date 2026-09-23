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
          btn.classList.add("is-loading");
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
            btn.classList.remove("is-loading");
            throw err; // keeps the modal open (openModal only closes on success)
          }
        },
        noClose: false,
      },
    ],
  });
}

/* Server-side paged mailbox list: search/filter/pagination happen on the API,
   so the page stays responsive no matter how many mailboxes exist. */
const PER_PAGE = 200;
const SEARCH_DEBOUNCE_MS = 250;

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
  const loadMoreBtn = h("button", { class: "btn btn-ghost btn-sm", onclick: loadMore }, h("span", {}, "Show more"));
  const pageInfo = h("span", { class: "mono pager-info" }, "");
  const pager = h("div", { class: "pager" }, pageInfo, loadMoreBtn);
  root.append(listWrap, pager);
  refreshIcons();

  let items = [];        // mailboxes loaded so far (bounded page by page)
  let page = 1;          // last page fetched
  let more = false;      // may another page exist?
  let loading = false;
  let providers = [];

  function currentQuery() {
    return searchInput.value.trim();
  }

  async function fetchPage(n) {
    const params = { limit: PER_PAGE, offset: (n - 1) * PER_PAGE };
    const q = currentQuery();
    const pf = provFilter.value;
    if (q) params.q = q;
    if (pf) params.provider = pf;
    return api.mailboxes(params);
  }

  async function reload() {
    loading = true;
    draw();
    try {
      const rows = await fetchPage(1);
      items = rows;
      page = 1;
      more = rows.length === PER_PAGE;
      loading = false;
      draw();
    } catch (e) {
      loading = false;
      items = [];
      listWrap.innerHTML = "";
      listWrap.append(errorBox(e.detail || "Could not load mailboxes.", () => render(root)));
      pager.style.display = "none";
      refreshIcons();
    }
  }

  async function loadMore() {
    if (loading || !more) return;
    loading = true;
    draw();
    try {
      const rows = await fetchPage(page + 1);
      items = items.concat(rows);
      page += 1;
      more = rows.length === PER_PAGE;
      loading = false;
      draw();
    } catch (e) {
      loading = false;
      draw();
      toast(e.detail || "Could not load more mailboxes.", "err");
    }
  }

  function updatePager() {
    const hasRows = items.length > 0;
    pager.style.display = hasRows ? "" : "none";
    if (loading && more) pageInfo.textContent = "loading…";
    else pageInfo.textContent = hasRows ? `loaded ${items.length}${more ? "+" : ""}` : "";
    loadMoreBtn.hidden = !more;
    loadMoreBtn.disabled = loading;
  }

  function draw() {
    updatePager();
    listWrap.innerHTML = "";
    if (loading && !items.length) {
      listWrap.append(skeletonRows(7));
      refreshIcons();
      return;
    }
    if (!items.length) {
      const filtering = Boolean(currentQuery() || provFilter.value);
      listWrap.append(emptyState({
        icon: filtering ? "search-x" : "inbox",
        title: filtering ? "No mailboxes match" : "No mailboxes yet",
        copy: filtering
          ? "Try a different search, or clear the provider filter."
          : "Create your first mailbox to start receiving temporary mail.",
        actionLabel: filtering ? undefined : "Create mailbox",
        onAction: () => openCreateMailbox(() => render(root)),
      }));
      return;
    }
    const tbody = h("tbody", {});
    const frag = document.createDocumentFragment();
    for (const m of items) {
      const tr = h("tr", { class: "clickable", tabindex: "0", role: "link", "aria-label": `Open ${m.address}` });
      const go = () => { location.hash = `#/mailboxes/${m.id}`; };
      tr.addEventListener("click", (e) => { if (!e.target.closest("button")) go(); });
      tr.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
      const openBtn = h("button", { class: "icon-btn", "aria-label": `Open ${m.address}`, title: "Open", onclick: (e) => { e.stopPropagation(); go(); } },
        h("i", { "data-lucide": "arrow-right" }));
      const delBtn = h("button", { class: "icon-btn danger", "aria-label": `Delete ${m.address}`, title: "Delete", onclick: (e) => deleteOne(e, m) },
        h("i", { "data-lucide": "trash-2" }));
      const provCell = h("td", { style: "display:flex;gap:6px;align-items:center;flex-wrap:wrap" },
        providerBadge(m.provider));
      if (m.provider === "gmail" && m.parent_status && m.parent_status !== "active") {
        provCell.append(h("a", { class: "pill pill--warn", href: "#/gmail", title: "The Gmail account that owns this mailbox lost access — reconnect it." },
          "reauth"));
      }
      tr.append(
        h("td", {}, addressCell(m.address)),
        provCell,
        h("td", {}, statusPill(m.is_active)),
        h("td", { class: "muted small mono" }, fmtDate(m.created_at)),
        h("td", {}, h("div", { class: "row-actions" }, openBtn, delBtn)));
      frag.appendChild(tr);
    }
    tbody.appendChild(frag);
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
      items = items.filter((x) => x.id !== m.id);
      draw();
    } catch (err) {
      toast(err.detail || "Could not delete mailbox.", "err");
    }
  }

  // Debounced search: resets to page 1 instead of re-filtering a huge list.
  let searchTimer = null;
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(reload, SEARCH_DEBOUNCE_MS);
  });
  provFilter.addEventListener("change", reload);

  listWrap.append(skeletonRows(7));
  try {
    const [first, provs] = await Promise.all([
      fetchPage(1),
      api.providers().catch(() => []),
    ]);
    items = first;
    more = first.length === PER_PAGE;
    providers = provs;
    for (const p of providers) provFilter.append(h("option", { value: p.slug }, p.slug));
  } catch (e) {
    listWrap.innerHTML = "";
    listWrap.append(errorBox(e.detail || "Could not load mailboxes.", () => render(root)));
    pager.style.display = "none";
    refreshIcons();
    return;
  }
  draw();
}
