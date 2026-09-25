/* Keys page (root only): list issued keys, create, reveal, rotate, delete, open-as. */
import { api, getApiKey, setApiKey } from "../api.js";
import { h, toast, refreshIcons, openModal, closeModal, confirmDialog, emptyState, errorBox, skeletonRows, copyText, fmtDate } from "../ui.js";

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

const RETENTION_HINT = "Leave a provider blank to follow the root retention settings. A number replaces the root TTL for this key only.";

let slugs = [];

const PREV_KEY = "mailtm_api_key_prev";

function scopeSummary(scope) {
  const providers = scope?.providers?.length ? scope.providers.join(", ") : "all providers";
  const parents = scope?.parent_ids?.length ? `${scope.parent_ids.length} parents` : "no parents";
  const actions = scope?.actions?.length ?? 0;
  return `${providers} · ${parents} · ${actions} action${actions === 1 ? "" : "s"}`;
}

function secretField(secret) {
  const input = h("input", {
    type: "text",
    value: secret,
    readonly: true,
    spellcheck: "false",
    "aria-label": "Key secret",
    style: "font-family:var(--font-mono)",
  });
  const copyBtn = h("button", {
    class: "icon-btn",
    type: "button",
    "aria-label": "Copy secret",
    title: "Copy",
    onclick: () => copyText(secret, "Secret copied"),
  }, h("i", { "data-lucide": "copy" }));
  return h("div", { class: "field" },
    h("label", {}, "Secret"),
    h("div", { class: "pass-wrap" }, input, copyBtn),
    h("p", { class: "field-hint" }, "Shown once in this dialog. Copy it now — the list never stores it."));
}

function pickTile(label, copy, pressed, onToggle) {
  const check = h("i", { "data-lucide": "check", class: "pick-tile-check", "aria-hidden": "true" });
  const btn = h("button", {
    type: "button",
    class: pressed ? "pick-tile is-on" : "pick-tile",
    "aria-pressed": pressed ? "true" : "false",
    onclick: () => onToggle(btn),
  }, check, h("span", { class: "pick-tile-body" },
    h("span", { class: "pick-tile-title" }, label),
    copy ? h("span", { class: "pick-tile-copy" }, copy) : null));
  btn.dataset.value = label;
  return btn;
}

function paintTile(btn, on) {
  btn.classList.toggle("is-on", on);
  btn.setAttribute("aria-pressed", on ? "true" : "false");
}

function providerTiles(selected = []) {
  const chosen = new Set(selected);
  const wrap = h("div", { class: "pick-grid", role: "group", "aria-label": "Providers" });
  for (const slug of selected) {
    if (slugs.includes(slug)) continue;
    wrap.append(pickTile(slug, "Already on this key", chosen.has(slug), (btn) => {
      paintTile(btn, btn.getAttribute("aria-pressed") !== "true");
    }));
  }
  for (const slug of slugs) {
    wrap.append(pickTile(slug, null, chosen.has(slug), (btn) => {
      paintTile(btn, btn.getAttribute("aria-pressed") !== "true");
    }));
  }
  return wrap;
}

function selectedValues(root) {
  return [...root.querySelectorAll('.pick-tile[aria-pressed="true"]')].map((el) => el.dataset.value);
}

function actionTiles(selected = []) {
  const wrap = h("div", { class: "pick-grid", role: "group", "aria-label": "Actions" });
  for (const [action, copy] of ACTIONS) {
    wrap.append(pickTile(action, copy, selected.includes(action), (btn) => {
      paintTile(btn, btn.getAttribute("aria-pressed") !== "true");
    }));
  }
  return wrap;
}

function ttlInput(slug, side, value) {
  return h("input", {
    type: "number", min: "1", step: "1", placeholder: "root",
    value: value ?? "",
    "aria-label": `${slug} ${side} TTL hours`,
  });
}

function retentionCard(slug, box, msg) {
  return h("div", { class: "card ret-card" },
    h("div", { class: "ret-card-top" }, h("span", { class: "prov-name mono" }, slug)),
    h("div", { style: "display:flex;gap:12px" },
      h("div", { class: "field", style: "margin:0;flex:1" }, h("label", {}, "Mailbox TTL (hours)"), box),
      h("div", { class: "field", style: "margin:0;flex:1" }, h("label", {}, "Message TTL (hours)"), msg)));
}

function retentionRows(container, providers, existing = new Map()) {
  const rows = [];
  for (const slug of providers) {
    const row = existing.get(slug);
    const box = ttlInput(slug, "mailbox", row?.mailbox_ttl_hours);
    const msg = ttlInput(slug, "message", row?.message_ttl_hours);
    rows.push({ slug, box, msg });
    container.append(retentionCard(slug, box, msg));
  }
  return rows;
}

function collectRetention(rows) {
  const out = [];
  for (const row of rows) {
    const parse = (v) => (v.trim() === "" ? null : Math.floor(Number(v)));
    const mailbox = parse(row.box.value);
    const message = parse(row.msg.value);
    if (mailbox === null && message === null) continue;
    if ((mailbox !== null && !(mailbox >= 1)) || (message !== null && !(message >= 1))) {
      throw new Error(`TTL for ${row.slug} must be 1 hour or more.`);
    }
    out.push({ provider: row.slug, mailbox_ttl_hours: mailbox, message_ttl_hours: message });
  }
  return out;
}

function parseIds(raw) {
  const text = raw.trim();
  if (!text) return [];
  const parts = text.split(/[\s,]+/).filter(Boolean);
  const ids = parts.map((part) => Number(part));
  if (ids.some((id) => !Number.isInteger(id))) {
    throw new Error("Parent ids must be integers.");
  }
  return ids;
}

function statusPill(status) {
  if (!status) return null;
  const s = String(status).toLowerCase();
  const cls = s === "active" || s === "ok" || s === "connected" ? "pill pill--on"
    : s.includes("error") || s.includes("expired") || s.includes("invalid") ? "pill pill--warn"
    : "pill pill--off";
  return h("span", { class: cls }, status);
}

function parentOptions(accounts, selectedIds) {
  const rows = [];
  const seen = new Set();
  for (const account of accounts) {
    const id = Number(account?.id);
    if (!Number.isInteger(id) || seen.has(id)) continue;
    seen.add(id);
    rows.push({
      id,
      email: account.email || `id ${id}`,
      status: account.status || "",
      missing: false,
    });
  }
  for (const raw of selectedIds) {
    const id = Number(raw);
    if (!Number.isInteger(id) || seen.has(id)) continue;
    seen.add(id);
    rows.push({ id, email: `${id} · (missing)`, status: "", missing: true });
  }
  rows.sort((a, b) => a.email.localeCompare(b.email) || a.id - b.id);
  return rows;
}

function parentPicker(accounts, selectedIds = []) {
  const chosen = new Set(selectedIds.map((id) => Number(id)).filter(Number.isInteger));
  const options = parentOptions(accounts, [...chosen]);
  let query = "";
  let open = false;

  const summary = h("span", { class: "parent-picker-label" }, "None");
  const toggle = h("button", {
    type: "button",
    class: "parent-picker-toggle",
    "aria-expanded": "false",
    "aria-label": "Gmail parents",
    onclick: () => setOpen(!open),
  }, summary, h("i", { "data-lucide": "chevron-down", class: "parent-picker-chevron", "aria-hidden": "true" }));

  const search = h("input", {
    type: "search",
    placeholder: "Filter by email or id",
    autocomplete: "off",
    spellcheck: "false",
    "aria-label": "Filter Gmail parents",
    oninput: () => {
      query = search.value;
      paint();
    },
  });
  const selectAll = h("button", {
    type: "button",
    onclick: () => {
      for (const row of visible()) chosen.add(row.id);
      paint();
    },
  }, "Select all");
  const clear = h("button", {
    type: "button",
    onclick: () => {
      for (const row of visible()) chosen.delete(row.id);
      paint();
    },
  }, "Clear");
  const list = h("div", { class: "parent-picker-list", role: "group", "aria-label": "Gmail parents" });
  const panel = h("div", { class: "parent-picker-panel" },
    h("div", { class: "parent-picker-tools" },
      h("div", { class: "parent-picker-search" },
        h("i", { "data-lucide": "search", "aria-hidden": "true" }),
        search),
      h("div", { class: "parent-picker-actions" }, selectAll, clear)),
    list);
  const root = h("div", { class: "parent-picker" }, toggle, panel);

  function matches(row) {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    return row.email.toLowerCase().includes(q) || String(row.id).includes(q);
  }

  function visible() {
    return options.filter(matches);
  }

  function setOpen(next) {
    open = next;
    root.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) search.focus();
  }

  function paint() {
    const n = chosen.size;
    summary.textContent = n ? `${n} selected` : "None";
    list.innerHTML = "";
    const rows = visible();
    if (!rows.length) {
      list.append(h("p", { class: "parent-picker-empty" }, options.length ? "No matches." : "No Gmail parents."));
      return;
    }
    for (const row of rows) {
      const on = chosen.has(row.id);
      const box = h("input", { type: "checkbox", checked: on ? "checked" : null, tabindex: "-1" });
      if (on) box.checked = true;
      const btn = h("button", {
        type: "button",
        class: on ? "parent-picker-row is-on" : "parent-picker-row",
        "aria-pressed": on ? "true" : "false",
        onclick: () => {
          if (chosen.has(row.id)) chosen.delete(row.id);
          else chosen.add(row.id);
          paint();
        },
      }, box, h("span", { class: "parent-picker-main" },
        h("span", { class: "parent-picker-email" }, row.email),
        h("span", { class: "parent-picker-id" }, String(row.id))),
      row.missing ? null : statusPill(row.status));
      list.append(btn);
    }
  }

  paint();
  return {
    root,
    selectedIds() {
      return [...chosen].sort((a, b) => a - b);
    },
  };
}

function toExpires(value) {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) throw new Error("Expiry is not a valid date.");
  return d.toISOString();
}

export async function render(root) {
  root.innerHTML = "";
  root.append(skeletonRows(4));

  let keys = [];
  let providers = [];
  let accounts = [];
  try {
    [keys, providers, accounts] = await Promise.all([
      api.keys(),
      api.providers().catch(() => []),
      api.gmailAccounts().catch(() => []),
    ]);
  } catch (e) {
    root.innerHTML = "";
    root.append(errorBox(e.detail || "Could not load keys.", () => render(root)));
    refreshIcons();
    return;
  }

  slugs = [...new Set(providers.map((p) => p.slug).filter(Boolean))];
  root.innerHTML = "";
  const createBtn = h("button", { class: "btn btn-primary", onclick: openCreate },
    h("i", { "data-lucide": "plus" }), h("span", {}, "New key"));
  root.append(h("div", { class: "toolbar toolbar--top" },
    h("p", { class: "muted", style: "flex:1;min-width:220px" },
      "Issued keys. Empty providers means all. Empty parent ids means none. Secrets stay off this list."),
    createBtn));

  const listWrap = h("div", {});
  root.append(listWrap);
  draw();

  function draw() {
    listWrap.innerHTML = "";
    if (!keys.length) {
      listWrap.append(emptyState({
        icon: "key-round",
        title: "No issued keys",
        copy: "Create a key with a name, an optional expiry, and the actions it may use.",
        actionLabel: "New key",
        onAction: openCreate,
      }));
      refreshIcons();
      return;
    }
    const tbody = h("tbody", {});
    for (const key of keys) {
      const revealBtn = h("button", {
        class: "icon-btn", title: "Reveal secret", "aria-label": `Reveal ${key.name}`,
        onclick: () => reveal(key),
      }, h("i", { "data-lucide": "eye" }));
      const rotateBtn = h("button", {
        class: "icon-btn", title: "Rotate secret", "aria-label": `Rotate ${key.name}`,
        onclick: () => rotate(key),
      }, h("i", { "data-lucide": "refresh-cw" }));
      const openBtn = h("button", {
        class: "icon-btn", title: "Open dashboard as this key", "aria-label": `Open dashboard as ${key.name}`,
        onclick: () => openAs(key),
      }, h("i", { "data-lucide": "log-in" }));
      const editBtn = h("button", {
        class: "icon-btn", title: "Edit scope", "aria-label": `Edit ${key.name}`,
        onclick: () => openEdit(key),
      }, h("i", { "data-lucide": "pencil" }));
      const delBtn = h("button", {
        class: "icon-btn danger", title: "Delete key", "aria-label": `Delete ${key.name}`,
        onclick: () => remove(key),
      }, h("i", { "data-lucide": "trash-2" }));
      tbody.append(h("tr", {},
        h("td", {}, key.name),
        h("td", { class: "mono" }, key.prefix || "—"),
        h("td", { class: "muted small mono" }, key.expires_at ? fmtDate(key.expires_at) : "never"),
        h("td", { class: "muted small" }, scopeSummary(key.scope)),
        h("td", {}, h("div", { class: "row-actions" }, revealBtn, rotateBtn, openBtn, editBtn, delBtn))));
    }
    listWrap.append(h("div", { class: "table-wrap" },
      h("table", { class: "table" },
        h("thead", {}, h("tr", {},
          h("th", {}, "Name"),
          h("th", {}, "Prefix"),
          h("th", {}, "Expiry"),
          h("th", {}, "Scope"),
          h("th", { style: "text-align:right" }, "Actions"))),
        tbody)));
    refreshIcons();
  }

  function formBody(existing) {
    const nameInput = h("input", {
      value: existing?.name || "",
      placeholder: "ci-readonly",
      autocomplete: "off",
      "aria-label": "Key name",
    });
    const expiryInput = h("input", {
      type: "datetime-local",
      "aria-label": "Expiry",
      value: existing?.expires_at ? toLocalInput(existing.expires_at) : "",
    });
    const providersPick = providerTiles(existing?.scope?.providers || []);
    const parentsPick = parentPicker(accounts, existing?.scope?.parent_ids || []);
    const actionsPick = actionTiles(existing?.scope?.actions || []);
    const retWrap = h("div", { class: "grid", style: "gap:8px" });
    const retRows = existing ? [] : retentionRows(retWrap, slugs);
    const body = h("div", {},
      h("div", { class: "field" }, h("label", {}, "Name"), nameInput),
      h("div", { class: "field" },
        h("label", {}, "Expiry ", h("span", { class: "opt" }, "(optional)")),
        expiryInput,
        h("p", { class: "field-hint" }, "Leave blank for a key that does not expire.")),
      h("div", { class: "field" },
        h("label", {}, "Providers"),
        providersPick,
        h("p", { class: "field-hint" }, "None selected means every provider.")),
      h("div", { class: "field" },
        h("label", {}, "Gmail parents"),
        parentsPick.root,
        h("p", { class: "field-hint" }, "None selected means this key gets no root Gmail parents.")),
      h("div", { class: "field" }, h("label", {}, "Actions"), actionsPick),
      existing ? null : h("div", { class: "field" },
        h("label", {}, "Retention ", h("span", { class: "opt" }, "(optional)")),
        h("p", { class: "field-hint" }, RETENTION_HINT),
        retWrap,
        slugs.length ? null : h("p", { class: "field-hint" }, "No providers loaded — retention can be set later.")));
    return { body, nameInput, expiryInput, providersPick, parentsPick, actionsPick, retRows };
  }

  function readForm(form) {
    const name = form.nameInput.value.trim();
    if (!name) throw new Error("Name is required.");
    const providersList = selectedValues(form.providersPick);
    const actions = selectedValues(form.actionsPick);
    if (!actions.length) throw new Error("Pick at least one action.");
    return {
      name,
      expires_at: toExpires(form.expiryInput.value),
      scope: {
        providers: providersList,
        parent_ids: form.parentsPick.selectedIds(),
        actions,
      },
    };
  }

  function openCreate() {
    const form = formBody(null);
    openModal({
      title: "New key",
      sub: "The secret is shown once after create.",
      wide: true,
      body: form.body,
      actions: [
        { label: "Cancel" },
        {
          label: "Create key",
          kind: "btn-primary",
          keepOpen: true,
          onClick: async (e) => {
            let payload;
            try {
              payload = readForm(form);
              payload.retention = collectRetention(form.retRows);
            } catch (err) {
              toast(err.message, "err");
              return;
            }
            const btn = e.currentTarget;
            btn.disabled = true;
            btn.classList.add("is-loading");
            try {
              const created = await api.keyCreate(payload);
              toast(`Created ${created.name}.`, "ok", "key-round");
              closeModal();
              showSecret("Key created", created.secret, () => render(root));
            } catch (err) {
              toast(err.detail || "Could not create key.", "err");
              btn.disabled = false;
              btn.classList.remove("is-loading");
            }
          },
        },
      ],
    });
  }

  function openEdit(key) {
    const form = formBody(key);
    const retWrap = h("div", { class: "grid", style: "gap:8px" });
    const existingRetention = new Map((key.key_retention || []).map((row) => [row.provider, row]));
    const editSlugs = [...new Set([...slugs, ...existingRetention.keys()])];
    const retRows = retentionRows(retWrap, editSlugs, existingRetention);
    form.body.append(h("div", { class: "field" },
      h("label", {}, "Retention"),
      h("p", { class: "field-hint" }, RETENTION_HINT),
      retWrap));
    openModal({
      title: `Edit ${key.name}`,
      sub: "Name, expiry, and scope. The secret does not change.",
      wide: true,
      body: form.body,
      actions: [
        { label: "Cancel" },
        {
          label: "Save",
          kind: "btn-primary",
          keepOpen: true,
          onClick: async (e) => {
            let payload;
            let retention;
            try {
              payload = readForm(form);
              retention = collectRetention(retRows);
            } catch (err) {
              toast(err.message, "err");
              return;
            }
            const btn = e.currentTarget;
            btn.disabled = true;
            btn.classList.add("is-loading");
            try {
              await api.keyUpdate(key.id, payload);
              await api.keyRetentionSet(key.id, retention);
              toast(`Updated ${key.name}.`, "ok", "check-circle-2");
              closeModal();
              render(root);
            } catch (err) {
              toast(err.detail || "Could not update key.", "err");
              btn.disabled = false;
              btn.classList.remove("is-loading");
            }
          },
        },
      ],
    });
  }

  function showSecret(title, secret, after) {
    if (!secret) {
      toast("The server did not return a secret.", "err");
      return;
    }
    openModal({
      title,
      sub: "Copy the secret. It is not written to the key list.",
      body: secretField(secret),
      actions: [{ label: "Done", kind: "btn-primary", onClick: () => { if (after) after(); } }],
    });
  }

  async function reveal(key) {
    try {
      const body = await api.keySecret(key.id);
      showSecret(`Secret for ${key.name}`, body?.secret);
    } catch (err) {
      toast(err.detail || "Could not reveal secret.", "err");
    }
  }

  async function rotate(key) {
    const ok = await confirmDialog({
      title: `Rotate ${key.name}?`,
      message: "The current secret stops working. Name, scope, and owned rows stay.",
      confirmLabel: "Rotate",
    });
    if (!ok) return;
    try {
      const created = await api.keyRotate(key.id);
      showSecret("Rotated secret", created?.secret, () => render(root));
    } catch (err) {
      toast(err.detail || "Could not rotate key.", "err");
    }
  }

  async function openAs(key) {
    try {
      const body = await api.keySecret(key.id);
      const secret = body?.secret;
      if (!secret) { toast("The server did not return a secret.", "err"); return; }
      const current = getApiKey();
      try {
        if (current) localStorage.setItem(PREV_KEY, current);
        else localStorage.removeItem(PREV_KEY);
      } catch { /* private mode */ }
      setApiKey(secret);
      location.reload();
    } catch (err) {
      toast(err.detail || "Could not open as this key.", "err");
    }
  }

  async function remove(key) {
    const ok = await confirmDialog({
      title: `Delete ${key.name}?`,
      message: "Refused while the key still owns a live mailbox or Gmail account.",
    });
    if (!ok) return;
    try {
      await api.keyDelete(key.id);
      toast(`Deleted ${key.name}.`, "ok", "trash-2");
      keys = keys.filter((row) => row.id !== key.id);
      draw();
    } catch (err) {
      toast(err.detail || "Could not delete key.", "err");
    }
  }
}

function toLocalInput(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
