/* Gmail page: OAuth connect card + account list (sync / delete). */
import { api } from "../api.js";
import { h, toast, refreshIcons, openModal, confirmDialog, emptyState, errorBox, skeletonRows } from "../ui.js";

function statusBadge(status) {
  const s = (status || "").toLowerCase();
  const cls = s === "active" || s === "ok" || s === "connected" ? "pill pill--on"
    : s.includes("error") || s.includes("expired") || s.includes("invalid") ? "pill pill--warn"
    : "pill pill--off";
  return h("span", { class: cls }, status || "unknown");
}

export async function render(root) {
  root.innerHTML = "";

  const connectBtn = h("button", { class: "btn btn-primary", onclick: connect },
    h("i", { "data-lucide": "plug-zap" }), h("span", {}, "Connect Gmail"));
  const actionsRow = h("div", { style: "display:flex;gap:8px;justify-content:center;flex-wrap:wrap" }, connectBtn);
  const credsLine = h("div", { class: "small muted", style: "margin-bottom:12px;min-height:20px" });
  const card = h("div", { class: "card connect-card" },
    h("h2", {}, "Bring your own Gmail"),
    h("p", {}, "Connect a Google account via OAuth, then create unlimited +alias mailboxes on top of it. The callback returns to the server — this tab stays put."),
    credsLine,
    actionsRow);
  root.append(card);

  const listWrap = h("div", { class: "mt-6" });
  root.append(listWrap);
  refreshIcons();

  listWrap.append(skeletonRows(3));
  let accounts;
  let creds = null; // null = could not load (endpoint missing); otherwise {configured, source, client_id, redirect_uri}
  try {
    [accounts, creds] = await Promise.all([
      api.gmailAccounts(),
      api.gmailCreds().catch(() => null),
    ]);
  } catch (e) {
    listWrap.innerHTML = "";
    listWrap.append(errorBox(e.detail || "Could not load Gmail accounts.", () => render(root)));
    refreshIcons();
    return;
  }
  drawCreds();
  draw();

  /** Status line + setup/edit affordances on the connect card. */
  function drawCreds() {
    credsLine.innerHTML = "";
    actionsRow.querySelectorAll("[data-creds-btn]").forEach((b) => b.remove());
    if (!creds) { refreshIcons(); return; }
    if (creds.source === "none") {
      credsLine.append(
        h("span", { class: "pill pill--warn" }, "OAuth not configured"));
      actionsRow.append(h("button", {
        class: "btn btn-ghost", "data-creds-btn": "1", onclick: () => openSetupDialog(),
      }, "Set up OAuth"));
    } else if (creds.source === "db") {
      credsLine.append("OAuth configured · ",
        h("span", { class: "mono" }, creds.client_id || "—"));
      actionsRow.append(h("button", {
        class: "btn btn-ghost btn-sm", "data-creds-btn": "1", onclick: () => openSetupDialog(),
      }, "Edit"));
    } else {
      credsLine.append("OAuth configured via server environment",
        h("div", { class: "field-hint", style: "margin-top:2px" },
          "Managed by MAILTM_GMAIL_CLIENT_ID / MAILTM_GMAIL_SECRET — not editable here."));
    }
    refreshIcons();
  }

  /** "Gmail OAuth setup" dialog: Client ID / Secret / Redirect URI → PUT creds. */
  function openSetupDialog() {
    const idInput = h("input", {
      value: creds?.source === "db" ? (creds.client_id || "") : "",
      placeholder: "123…apps.googleusercontent.com",
      autocomplete: "off", spellcheck: "false", "aria-label": "Client ID",
      style: "font-family:var(--font-mono)",
    });
    const secretInput = h("input", {
      type: "password", placeholder: "Client secret", autocomplete: "new-password",
      "aria-label": "Client secret",
    });
    const toggle = h("button", {
      class: "icon-btn", type: "button", "aria-label": "Show or hide client secret", title: "Show / hide",
      onclick: () => {
        const show = secretInput.type === "password";
        secretInput.type = show ? "text" : "password";
        toggle.querySelector("i, svg")?.setAttribute("data-lucide", show ? "eye-off" : "eye");
        refreshIcons();
        secretInput.focus();
      },
    }, h("i", { "data-lucide": "eye" }));
    const uriInput = h("input", {
      value: creds?.redirect_uri || "",
      placeholder: "http://127.0.0.1:8477/v1/gmail/oauth/callback",
      autocomplete: "off", spellcheck: "false", "aria-label": "Redirect URI",
      style: "font-family:var(--font-mono)",
    });
    const form = h("div", {},
      h("p", { class: "muted", style: "margin-bottom:16px" },
        "Paste the credentials of your Google Cloud OAuth client. Only your Client ID is shown again later — the secret is stored encrypted on this server."),
      h("div", { class: "field" }, h("label", {}, "Client ID"), idInput),
      h("div", { class: "field" }, h("label", {}, "Client Secret"),
        h("div", { class: "pass-wrap" }, secretInput, toggle)),
      h("div", { class: "field", style: "margin-bottom:0" }, h("label", {}, "Redirect URI"),
        uriInput,
        h("p", { class: "field-hint" },
          "Register this exact URI as an authorized redirect URI in your Google Cloud OAuth client.")));

    let saveBtn = null;
    const valid = () => idInput.value.trim() !== "" && secretInput.value !== "";
    const m = openModal({
      title: "Gmail OAuth setup",
      sub: "Google Cloud OAuth client credentials",
      body: form,
      actions: [
        { label: "Cancel" },
        {
          label: "Save", kind: "btn-primary",
          onClick: async (e) => {
            const btn = e.currentTarget;
            btn.disabled = true;
            const body = {
              client_id: idInput.value.trim(),
              client_secret: secretInput.value,
            };
            if (uriInput.value.trim()) body.redirect_uri = uriInput.value.trim();
            try {
              creds = await api.saveGmailCreds(body);
              toast("OAuth credentials saved.", "ok", "check-circle-2");
              drawCreds();
            } catch (err) {
              m.body.querySelector(".error-box")?.remove();
              m.body.prepend(errorBox(err.detail || "Could not save credentials."));
              refreshIcons();
              btn.disabled = false;
              throw err; // keeps the dialog open
            }
          },
        },
      ],
    });
    saveBtn = m.dialog.querySelector(".modal-foot .btn-primary");
    saveBtn.disabled = !valid();
    idInput.addEventListener("input", () => { saveBtn.disabled = !valid(); });
    secretInput.addEventListener("input", () => { saveBtn.disabled = !valid(); });
  }

  async function connect(e) {
    const btn = e.currentTarget;
    btn.disabled = true;
    try {
      const { auth_url } = await api.gmailOAuthStart();
      window.open(auth_url, "_blank", "noopener");
      toast("Google consent opened in a new tab — approve it, then come back and refresh.", "info", "external-link");
    } catch (err) {
      if (err.status === 400) {
        // CredentialsError-like: OAuth credentials not configured yet.
        openSetupDialog();
      } else {
        toast(err.detail || "Could not start OAuth.", "err");
      }
    } finally {
      btn.disabled = false;
    }
  }

  function draw() {
    listWrap.innerHTML = "";
    listWrap.append(h("div", { class: "section-head" },
      h("h2", {}, "Connected accounts"),
      h("p", {}, `${accounts.length} account${accounts.length === 1 ? "" : "s"}`)));
    if (!accounts.length) {
      listWrap.append(emptyState({
        icon: "at-sign",
        title: "No Gmail accounts connected",
        copy: "Hit “Connect Gmail” above and approve access in the new tab. Accounts you add will show up here.",
      }));
      return;
    }
    const list = h("div", { class: "acct-list" });
    for (const a of accounts) {
      const initial = (a.email || "?").trim().charAt(0).toUpperCase() || "G";
      const syncBtn = h("button", { class: "icon-btn", title: "Sync account", "aria-label": `Sync ${a.email}`, onclick: (e) => syncOne(e, a) },
        h("i", { "data-lucide": "refresh-cw" }));
      const delBtn = h("button", { class: "icon-btn danger", title: "Remove account", "aria-label": `Remove ${a.email}`, onclick: (e) => deleteOne(e, a) },
        h("i", { "data-lucide": "trash-2" }));
      list.append(h("div", { class: "card acct" },
        h("div", { class: "acct-avatar", "aria-hidden": "true" }, initial),
        h("div", { class: "acct-main" },
          h("div", { class: "acct-email" }, a.email),
          a.send_as?.length
            ? h("div", { class: "sendas" }, ...a.send_as.map((s) => h("span", { class: "chip" }, s)))
            : h("div", { class: "small muted mt-4" }, "no send-as aliases")),
        statusBadge(a.status),
        h("div", { class: "acct-actions" }, syncBtn, delBtn)));
    }
    listWrap.append(list);
    refreshIcons();
  }

  async function syncOne(e, a) {
    const btn = e.currentTarget;
    const icon = btn.querySelector("svg, i");
    btn.disabled = true;
    if (icon) icon.classList.add("spin");
    try {
      await api.gmailSync(a.id);
      toast(`Synced ${a.email}.`, "ok", "refresh-cw");
    } catch (err) {
      toast(err.detail || "Sync failed.", "err");
    } finally {
      btn.disabled = false;
      if (icon) icon.classList.remove("spin");
    }
  }

  async function deleteOne(e, a) {
    const ok = await confirmDialog({
      title: "Remove Gmail account?",
      message: `${a.email} will be disconnected. Mailboxes already created on it are kept unless deleted separately.`,
    });
    if (!ok) return;
    try {
      await api.gmailDelete(a.id);
      toast(`Removed ${a.email}.`, "ok", "trash-2");
      accounts = accounts.filter((x) => x.id !== a.id);
      draw();
    } catch (err) {
      toast(err.detail || "Could not remove account.", "err");
    }
  }
}
