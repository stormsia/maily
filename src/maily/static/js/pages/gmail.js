/* Gmail page: OAuth connect card + account list (sync / delete). */
import { api } from "../api.js";
import { h, toast, refreshIcons, openModal, confirmDialog, emptyState, errorBox, skeletonRows, copyText } from "../ui.js";

function statusBadge(status) {
  const s = (status || "").toLowerCase();
  const cls = s === "active" || s === "ok" || s === "connected" ? "pill pill--on"
    : s.includes("error") || s.includes("expired") || s.includes("invalid") ? "pill pill--warn"
    : "pill pill--off";
  return h("span", { class: cls }, status || "unknown");
}

/* Guided setup wizard — Google Cloud OAuth client walkthrough. */
const WIZ_URLS = {
  console: "https://console.cloud.google.com",
  library: "https://console.developers.google.com/apis/library",
  branding: "https://console.developers.google.com/auth/branding",
  audience: "https://console.developers.google.com/auth/audience",
  clients: "https://console.developers.google.com/auth/clients",
};
const WIZ_STEPS = [
  { label: "Project", title: "Create a project and enable the Gmail API",
    lead: "Done once per server — the project is the container for your OAuth client and API access." },
  { label: "Consent", title: "Set up the Google Auth platform",
    lead: "Google blocks brand-new OAuth clients until the consent screen is configured." },
  { label: "Client", title: "Create a Web application OAuth client",
    lead: "The Client ID and Client Secret are shown exactly once — keep them for step 4." },
  { label: "Credentials", title: "Paste the client credentials", lead: "" },
  { label: "Connect", title: "Save and connect your Google account",
    lead: "Credentials are stored on this server, then the Google consent screen opens in a new tab." },
];

function showCredentials(me) {
  if (me == null || me.is_root === true) return true;
  return false;
}

function canAddParents(me) {
  if (me == null || me.is_root === true) return true;
  const actions = me.scope?.actions;
  return Array.isArray(actions) && actions.includes("parents:add");
}

export async function render(root, me = null) {
  const credentials = showCredentials(me);
  const canConnect = canAddParents(me);
  root.innerHTML = "";

  const actionsRow = h("div", { style: "display:flex;gap:8px;justify-content:center;flex-wrap:wrap" });
  const credsLine = credentials
    ? h("div", { class: "small muted", style: "margin-bottom:12px;min-height:20px" })
    : null;
  const card = h("div", { class: "card connect-card" },
    h("h2", {}, "Bring your own Gmail"),
    h("p", {}, "Connect a Google account via OAuth, then create unlimited +alias mailboxes on top of it. The callback returns to the server — this tab stays put."),
    credsLine,
    canConnect ? actionsRow : null);
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
      credentials ? api.gmailCreds().catch(() => null) : Promise.resolve(null),
    ]);
  } catch (e) {
    listWrap.innerHTML = "";
    listWrap.append(errorBox(e.detail || "Could not load Gmail accounts.", () => render(root)));
    refreshIcons();
    return;
  }
  if (credentials) drawCreds();
  else if (canConnect) {
    actionsRow.append(connectBtn());
    refreshIcons();
  }
  draw();

  function normalizeRedirectUri(raw) {
    let uri = (raw || "").trim();
    if (!uri || uri.includes("0.0.0.0") || !uri.startsWith("http")) {
      return "http://127.0.0.1:8477/v1/gmail/oauth/callback";
    }
    return uri.replace("://0.0.0.0", "://127.0.0.1");
  }

  /** Connect button (primary once configured, ghost otherwise). */
  function connectBtn(kind = "btn-primary") {
    return h("button", { class: `btn ${kind}`, onclick: connect },
      h("i", { "data-lucide": "plug-zap" }), h("span", {}, "Connect Gmail"));
  }

  function manualCallbackBtn() {
    return h("button", {
      class: "btn btn-ghost",
      title: "Manually complete OAuth if Google redirected to an unreachable address (e.g. behind proxy)",
      onclick: openManualCallbackModal,
    }, h("i", { "data-lucide": "link-2" }), h("span", {}, "Manual callback"));
  }

  /** Status line + setup/edit affordances on the connect card. */
  function drawCreds() {
    if (!credentials || !credsLine || !actionsRow) return;
    credsLine.innerHTML = "";
    actionsRow.innerHTML = "";
    if (!creds) { actionsRow.append(connectBtn(), manualCallbackBtn()); refreshIcons(); return; }
    if (creds.source === "none") {
      credsLine.append(
        h("span", { class: "pill pill--warn" }, "OAuth not configured"));
      actionsRow.append(
        h("button", {
          class: "btn btn-primary", title: "Step-by-step walkthrough of the Google Cloud Console",
          onclick: () => openWizard(1),
        }, h("i", { "data-lucide": "sparkles" }), h("span", {}, "Guided setup")),
        h("button", {
          class: "btn btn-ghost", title: "Already created an OAuth client? Jump straight to the credentials step.",
          onclick: () => openWizard(4),
        }, h("span", {}, "Set up OAuth")),
        manualCallbackBtn(),
        connectBtn("btn-ghost"));
    } else if (creds.source === "db") {
      credsLine.append("OAuth configured · ",
        h("span", { class: "mono" }, creds.client_id || "—"));
      actionsRow.append(
        connectBtn(),
        manualCallbackBtn(),
        h("button", {
          class: "btn btn-ghost btn-sm", onclick: () => openWizard(4),
        }, h("span", {}, "Edit")));
    } else {
      credsLine.append("OAuth configured via server environment",
        h("div", { class: "field-hint", style: "margin-top:2px" },
          "Managed by MAILY_GMAIL_CLIENT_ID / MAILY_GMAIL_CLIENT_SECRET (or MAILY_GMAIL_CREDENTIALS_PATH) — not editable here."));
      actionsRow.append(connectBtn(), manualCallbackBtn());
    }
    refreshIcons();
  }

  /** "Gmail OAuth setup" wizard: guided walkthrough of the Google Cloud
   *  Console (5 steps), credential entry and save+connect. */
  function openWizard(startStep = 1) {
    const state = {
      clientId: creds?.source === "db" ? creds.client_id || "" : "",
      secret: "",
      redirectUri: normalizeRedirectUri(creds?.redirect_uri),
    };
    let step = Math.min(WIZ_STEPS.length, Math.max(1, startStep));
    let dir = 1;

    const wrap = h("div", { class: "wizard" });
    const progress = h("div", { class: "wizard-track", role: "list" });
    const stepEl = h("div", { class: "wizard-step" });
    wrap.append(progress, stepEl);

    const m = openModal({
      title: "Gmail OAuth setup",
      sub: "Guided setup · Google Cloud OAuth client",
      body: wrap,
      wide: true,
    });

    const valid = () => state.clientId.trim() !== "" && state.secret !== "";
    const extLink = (label, url) => h("a", { class: "wz-link-a", href: url, target: "_blank", rel: "noopener" },
      label, h("i", { "data-lucide": "arrow-up-right" }));
    const linkRow = (label, url, hint) => h("div", { class: "wz-link" },
      h("span", { class: "wz-link-ic" }, h("i", { "data-lucide": "external-link" })),
      h("div", {}, extLink(label, url), h("p", { class: "wz-link-hint" }, hint)));

    function renderProgress() {
      progress.innerHTML = "";
      WIZ_STEPS.forEach((s, i) => {
        const n = i + 1;
        if (i > 0) progress.append(h("span", { class: `wz-line${n <= step ? " done" : ""}` }));
        const node = n < step
          ? h("button", { class: "wizard-node done", type: "button", role: "listitem",
              "aria-label": `Go to step ${n}: ${s.label}`, title: `Back to ${s.label}`,
              onclick: () => goTo(n) },
              h("span", { class: "wz-dot" }, h("i", { "data-lucide": "check" })),
              h("span", { class: "wz-label" }, s.label))
          : h("span", { class: `wizard-node ${n === step ? "current" : "todo"}`, role: "listitem",
              "aria-current": n === step ? "step" : undefined },
              h("span", { class: "wz-dot" }, String(n)),
              h("span", { class: "wz-label" }, s.label));
        progress.append(node);
      });
    }

    function renderStep() {
      stepEl.innerHTML = "";
      stepEl.style.setProperty("--wz-dir", dir);
      stepEl.append(stepHead());

      if (step === 1) {
        stepEl.append(
          linkRow("Create a project", WIZ_URLS.console,
            "Open the Google Cloud Console and create a project — or pick an existing one."),
          linkRow("Enable the Gmail API", WIZ_URLS.library,
            "In the API library: search “Gmail API” → Enable."),
          h("div", { class: "wz-tip" }, h("i", { "data-lucide": "info" }),
            h("span", {}, "Check the project shown in the console header before every step here — enabling the API in one project and creating the OAuth client in another is the classic mistake.")));
        stepEl.append(foot(null, nextBtn()));
      } else if (step === 2) {
        stepEl.append(
          linkRow("Configure the consent screen", WIZ_URLS.branding,
            "“Get Started” → set an App name and a User support email."),
          linkRow("Audience & test users", WIZ_URLS.audience,
            "User type: External. Add yourself to Test users — the quota is 100 and a test user keeps its slot forever."),
          h("div", { class: "wz-tip" }, h("i", { "data-lucide": "info" }),
            h("span", {}, "Scopes: the app only needs gmail.modify (read + labels + trash). Nothing extra to set under Audience → Data Access.")),
          h("div", { class: "wz-warn" }, h("i", { "data-lucide": "alert-triangle" }),
            h("span", {}, h("b", {}, "Testing mode expires every 7 days: "),
              "test-user authorization and the refresh token both lapse, so the account must be reconnected weekly. Publishing the app (requires a homepage, privacy policy and Google verification) removes the limit.")));
        stepEl.append(foot(backBtn(), nextBtn()));
      } else if (step === 3) {
        stepEl.append(
          linkRow("Create the OAuth client", WIZ_URLS.clients,
            "“Create client” → Application type: Web application → name it (e.g. “maily”)."),
          h("div", { class: "field", style: "margin-bottom:0" },
            h("label", {}, "Authorized redirect URI"),
            h("div", { class: "wz-uri" },
              h("code", {}, state.redirectUri),
              h("button", { class: "copy-mini", type: "button", "aria-label": "Copy redirect URI", title: "Copy",
                onclick: () => copyText(state.redirectUri, "Redirect URI copied") },
                h("i", { "data-lucide": "copy" }))),
            h("p", { class: "field-hint", style: "margin-top:6px" },
              "Add this exact URI under Authorized redirect URIs → “Add URI”.")),
          h("div", { class: "wz-warn" }, h("i", { "data-lucide": "alert-triangle" }),
            h("span", {}, "The match must be exact — scheme, case, trailing slash. Any difference fails with redirect_uri_mismatch during authorization. https is mandatory, except for localhost / 127.0.0.1.")),
          h("p", { class: "wz-field-note" },
            "Click “Create”. The “OAuth client created” popup shows the Client ID and Client Secret — the secret is displayed only once, so copy both before closing it."));
        stepEl.append(foot(backBtn(), nextBtn()));
      } else if (step === 4) {
        const idInput = h("input", {
          value: state.clientId,
          placeholder: "123…apps.googleusercontent.com",
          autocomplete: "off", spellcheck: "false", "aria-label": "Client ID",
          style: "font-family:var(--font-mono)",
        });
        const secretInput = h("input", {
          type: "password", value: state.secret, placeholder: "Client secret",
          autocomplete: "new-password", "aria-label": "Client secret",
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
        // Redirect URI is fixed — must match the one shown in step 3 and
        // registered in Google; editing it causes redirect_uri_mismatch.
        const uriInput = h("input", {
          value: state.redirectUri,
          readonly: true,
          placeholder: "http://127.0.0.1:8477/v1/gmail/oauth/callback",
          autocomplete: "off", spellcheck: "false", "aria-label": "Redirect URI",
          title: "Set by this server — matches step 3",
          style: "font-family:var(--font-mono)",
        });
        const nxt = nextBtn();
        const sync = () => {
          state.clientId = idInput.value;
          state.secret = secretInput.value;
          nxt.disabled = !valid();
        };
        idInput.addEventListener("input", sync);
        secretInput.addEventListener("input", sync);
        stepEl.append(
          h("div", { class: "field" }, h("label", {}, "Client ID"), idInput),
          h("div", { class: "field" }, h("label", {}, "Client Secret"),
            h("div", { class: "pass-wrap" }, secretInput, toggle)),
          h("div", { class: "field", style: "margin-bottom:0" },
            h("label", {}, "Redirect URI"), uriInput,
            h("p", { class: "field-hint" },
              "Locked to the URI from step 3 — add it under Authorized redirect URIs in Google exactly as shown. The secret is stored on the server encrypted.")));
        nxt.disabled = !valid();
        stepEl.append(foot(backBtn(), nxt));
        idInput.focus();
      } else {
        const manualInput = h("input", {
          placeholder: "http://127.0.0.1:8477/v1/gmail/oauth/callback?state=...&code=...",
          autocomplete: "off", spellcheck: "false",
          style: "font-family:var(--font-mono);font-size:var(--fs-12);flex:1",
          "aria-label": "Google redirect URL",
        });
        const manualBtn = h("button", {
          class: "btn btn-ghost btn-sm", type: "button",
          style: "white-space:nowrap",
          onclick: async () => {
            const val = manualInput.value.trim();
            if (!val) {
              showError("Paste the redirect URL or code from the browser address bar.");
              return;
            }
            manualBtn.disabled = true;
            manualBtn.classList.add("is-loading");
            try {
              if (valid() && creds?.source !== "db") {
                const body = { client_id: state.clientId.trim(), client_secret: state.secret };
                if (state.redirectUri.trim()) body.redirect_uri = state.redirectUri.trim();
                creds = await api.saveGmailCreds(body);
              }
              await api.gmailOAuthCallback({ url_or_code: val });
              toast("Gmail account connected successfully!", "ok", "check-circle-2");
              m.close();
              await reloadAccounts();
            } catch (err) {
              showError(err.detail || err.message || "Failed to exchange authorization code.");
            } finally {
              manualBtn.disabled = false;
              manualBtn.classList.remove("is-loading");
              refreshIcons();
            }
          },
        }, h("i", { "data-lucide": "check" }), h("span", {}, "Complete manually"));

        const manualBox = h("div", { class: "manual-callback-box" },
          h("div", { class: "manual-callback-title" },
            h("i", { "data-lucide": "network" }),
            h("span", { style: "font-weight:600" }, "Behind a proxy or remote server?")),
          h("p", { class: "small muted" },
            "If Google redirected to an unreachable address (like 127.0.0.1:8477), copy the entire URL from that browser tab's address bar and paste it below:"),
          h("div", { style: "display:flex;gap:8px;align-items:center;margin-top:8px" },
            manualInput, manualBtn));

        stepEl.append(
          h("p", {}, "Save & Connect writes the credentials (encrypted) to this server, then opens Google's consent screen in a new tab."),
          creds?.source === "db" ? h("p", { class: "wz-field-note" }, "Existing credentials will be replaced.") : null,
          h("div", { class: "wz-tip" }, h("i", { "data-lucide": "external-link" }),
            h("span", {}, "After approving, come back here and refresh the page — the account appears in the Connected accounts list.")),
          manualBox);
        const saveEl = h("button", {
          class: "btn btn-primary", type: "button", disabled: !valid(), onclick: saveAndConnect,
        }, h("i", { "data-lucide": "plug-zap" }), h("span", {}, "Save & Connect"));
        stepEl.append(foot(
          backBtn(),
          h("div", { style: "display:flex;gap:8px" },
            h("button", { class: "btn btn-ghost", type: "button", onclick: () => m.close() }, "Cancel"),
            saveEl)));
        saveEl.focus();
      }
      refreshIcons();
      if (step <= 3) stepEl.querySelector(".btn-primary")?.focus();
    }

    function stepHead() {
      const s = WIZ_STEPS[step - 1];
      return h("div", { class: "wizard-step-head" },
        h("span", { class: "wz-step-no" }, `Step ${step} of ${WIZ_STEPS.length}`),
        h("h4", {}, s.title),
        s.lead ? h("p", {}, s.lead) : null);
    }

    const backBtn = () => h("button", { class: "btn btn-ghost", type: "button", onclick: () => goTo(step - 1) },
      h("i", { "data-lucide": "arrow-left" }), h("span", {}, "Back"));
    const nextBtn = () => h("button", { class: "btn btn-primary", type: "button", onclick: () => goTo(step + 1) },
      h("span", {}, "Next"), h("i", { "data-lucide": "arrow-right" }));

    const foot = (back, right) => h("div", { class: "wizard-foot" },
      back || h("span", {}),
      h("span", { class: "spacer" }),
      right);

    function showError(msg) {
      stepEl.querySelector(".wz-error")?.remove();
      stepEl.prepend(h("div", { class: "error-box wz-error" },
        h("i", { "data-lucide": "alert-triangle" }), h("span", {}, msg)));
    }

    function goTo(n) {
      if (n < 1 || n > WIZ_STEPS.length) return;
      if (n === WIZ_STEPS.length && !valid()) return; // can't skip to Connect without creds
      dir = n < step ? -1 : 1;
      step = n;
      renderProgress();
      renderStep();
    }

    async function saveAndConnect(e) {
      const btn = e.currentTarget;
      btn.disabled = true;
      btn.classList.add("is-loading");
      stepEl.querySelector(".wz-error")?.remove();
      try {
        const body = { client_id: state.clientId.trim(), client_secret: state.secret };
        if (state.redirectUri.trim()) body.redirect_uri = state.redirectUri.trim();
        creds = await api.saveGmailCreds(body);
        toast("OAuth credentials saved.", "ok", "check-circle-2");
      } catch (err) {
        showError(err.detail || "Could not save credentials.");
        btn.disabled = false;
        btn.classList.remove("is-loading");
        refreshIcons();
        return; // wizard stays open
      }
      try {
        const { auth_url } = await api.gmailOAuthStart();
        window.open(auth_url, "_blank", "noopener");
        toast("Google consent opened in a new tab — approve it, then come back and refresh.", "info", "external-link");
      } catch (err) {
        showError(err.detail || "Could not start OAuth — check the Client ID and Secret.");
        btn.disabled = false;
        btn.classList.remove("is-loading");
        refreshIcons();
        return; // wizard stays open
      }
      drawCreds();
      m.close();
    }

    // Enter in any wizard input advances (step 4 → 5, 5 → save).
    m.dialog.addEventListener("keydown", (e) => {
      if (e.key !== "Enter") return;
      const t = e.target;
      if (!(t instanceof HTMLInputElement) || !stepEl.contains(t)) return;
      e.preventDefault();
      if (step === 4) goTo(5);
      else if (step === 5) stepEl.querySelector(".btn-primary")?.click();
    });

    renderProgress();
    renderStep();
  }

  async function connect(e) {
    const btn = e.currentTarget;
    btn.disabled = true;
    btn.classList.add("is-loading");
    try {
      const { auth_url } = await api.gmailOAuthStart();
      window.open(auth_url, "_blank", "noopener");
      toast("Google consent opened in a new tab — approve it, then come back and refresh.", "info", "external-link");
    } catch (err) {
      if (err.status === 400 && credentials) {
        // CredentialsError-like: OAuth credentials not configured yet.
        openWizard(creds?.source === "db" ? 4 : 1);
      } else {
        toast(err.detail || "Could not start OAuth.", "err");
      }
    } finally {
      btn.disabled = false;
      btn.classList.remove("is-loading");
    }
  }

  async function reloadAccounts() {
    try {
      accounts = await api.gmailAccounts();
      draw();
    } catch {
      /* ignore */
    }
  }

  function openManualCallbackModal() {
    const input = h("input", {
      placeholder: "http://127.0.0.1:8477/v1/gmail/oauth/callback?state=...&code=...",
      autocomplete: "off", spellcheck: "false",
      style: "font-family:var(--font-mono);font-size:var(--fs-13);width:100%",
      "aria-label": "Google redirect URL or authorization code",
    });
    const wrap = h("div", {},
      h("p", { style: "margin-bottom:var(--s-3);color:var(--muted);font-size:var(--fs-13);line-height:1.5" },
        "When running behind a reverse proxy, Docker, or on a remote server, Google's redirect to ",
        h("code", {}, "http://127.0.0.1:8477/..."),
        " may show “Site can’t be reached”. Copy the full URL from that browser tab's address bar and paste it below:"),
      h("div", { class: "field" },
        h("label", {}, "Redirect URL or Authorization Code"),
        input,
        h("p", { class: "field-hint" }, "Paste the full redirect URL (with ?code=...&state=...) or just the authorization code.")),
      h("div", { class: "wz-tip", style: "margin-top:var(--s-3)" },
        h("i", { "data-lucide": "info" }),
        h("span", {}, "Google authorization codes are single-use and expire within minutes. Paste immediately after granting consent.")));

    openModal({
      title: "Manual OAuth callback",
      sub: "Complete Gmail connection from browser redirect URL",
      body: wrap,
      wide: true,
      actions: [
        { label: "Cancel" },
        {
          label: "Connect account",
          kind: "btn-primary",
          onClick: async () => {
            const val = input.value.trim();
            if (!val) {
              toast("Please paste the redirect URL or code first.", "warn");
              return false;
            }
            try {
              await api.gmailOAuthCallback({ url_or_code: val });
              toast("Gmail account connected successfully!", "ok", "check-circle-2");
              closeModal();
              await reloadAccounts();
              return true;
            } catch (err) {
              toast(err.detail || err.message || "Failed to exchange authorization code.", "err");
              return false;
            }
          },
        },
      ],
    });
    refreshIcons();
    input.focus();
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
        copy: canConnect
          ? "Hit “Connect Gmail” above and approve access in the new tab. Accounts you add will show up here."
          : "Accounts this key may use show up here. This key cannot connect a new one.",
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
      const needsReauth = !["active", "connected", "ok"].includes((a.status || "").toLowerCase());
      const reauthBtn = needsReauth && canConnect
        ? h("button", { class: "icon-btn warn", title: `Reconnect ${a.email} — access expired`, "aria-label": `Reconnect ${a.email}`, onclick: () => reconnectAccount(a) },
            h("i", { "data-lucide": "plug-zap" }))
        : null;
      list.append(h("div", { class: "card acct" },
        h("div", { class: "acct-avatar", "aria-hidden": "true" }, initial),
        h("div", { class: "acct-main" },
          h("div", { class: "acct-email" }, a.email),
          a.send_as?.length
            ? h("div", { class: "sendas" }, ...a.send_as.map((s) => h("span", { class: "chip" }, s)))
            : h("div", { class: "small muted mt-4" }, "no send-as aliases")),
        statusBadge(a.status),
        h("div", { class: "acct-actions" }, reauthBtn, syncBtn, delBtn)));
    }
    listWrap.append(list);
    refreshIcons();
  }

  async function reconnectAccount(a) {
    try {
      const { auth_url } = await api.gmailOAuthStart();
      window.open(auth_url, "_blank", "noopener");
      toast("Google consent opened in a new tab — approve it, then refresh.", "info", "external-link");
    } catch (err) {
      if (err.status === 400 && credentials) {
        openWizard(creds?.source === "db" ? 4 : 1);
      } else {
        toast(err.detail || "Could not start OAuth.", "err");
      }
    }
  }

  async function syncOne(e, a) {
    const btn = e.currentTarget;
    btn.disabled = true;
    btn.classList.add("is-loading");
    try {
      await api.gmailSync(a.id);
      toast(`Synced ${a.email}.`, "ok", "refresh-cw");
    } catch (err) {
      if (err.providerAuth) {
        toast(
          `Auth for ${a.email} expired or was revoked — reconnect the account. ${err.detail || ""}`,
          "err",
        );
      } else {
        toast(err.detail || "Sync failed.", "err");
      }
    } finally {
      btn.disabled = false;
      btn.classList.remove("is-loading");
      btn.querySelectorAll(".spin, svg, i").forEach((el) => el.classList.remove("spin"));
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
