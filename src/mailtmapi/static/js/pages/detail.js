/* Mailbox detail: header + paginated message list + reading pane. */
import { api } from "../api.js";
import {
  h,
  toast,
  refreshIcons,
  openModal,
  confirmDialog,
  emptyState,
  errorBox,
  skeletonRows,
  copyText,
  timeAgo,
  fmtDate,
  statusPill,
  providerBadge,
} from "../ui.js";

const PAGE_SIZE_HINT = 20;

function msgItem(msg, selected, onOpen) {
  const el = h(
    "button",
    {
      class: `msg-item${msg.seen ? " seen-item" : ""}${selected ? " selected" : ""}`,
      onclick: onOpen,
      "aria-label": `${msg.seen ? "" : "Unread: "}${msg.subject || "(no subject)"}`,
    },
    h("span", { class: `msg-dot${msg.seen ? " seen" : ""}` }),
    h(
      "span",
      { class: "msg-main" },
      h("div", { class: "msg-subject" }, msg.subject || "(no subject)"),
      h(
        "div",
        { class: "msg-from" },
        msg.from_name
          ? `${msg.from_name} · ${msg.from_address}`
          : msg.from_address || "unknown sender",
      ),
    ),
    h(
      "span",
      { class: "msg-side" },
      h("span", { class: "msg-time" }, timeAgo(msg.received_at)),
      msg.has_attachments
        ? h(
            "span",
            { class: "msg-attach", title: "Has attachments" },
            h("i", { "data-lucide": "paperclip" }),
          )
        : null,
    ),
  );
  return el;
}

/* Provider-auth failure (e.g. expired Gmail token): make the cause visible
 * and point to the reconnect flow instead of a generic error. */
function providerAuthBox(e, onRetry) {
  const gmail = e?.provider === "gmail";
  return h(
    "div",
    { class: "error-box" },
    h("i", { "data-lucide": "alert-triangle" }),
    h(
      "div",
      { style: "width:100%" },
      h(
        "div",
        { style: "font-weight:700" },
        gmail ? "Gmail account access expired" : "Provider account auth failed",
      ),
      h("div", {}, e?.detail || "The connected account is no longer authorized."),
      gmail
        ? h(
            "p",
            { class: "field-hint", style: "margin-top:6px;color:inherit" },
            "Google rejected the account token (expired or revoked). Reconnect the account below, then refresh.",
          )
        : null,
      h(
        "div",
        { style: "display:flex;gap:8px;margin-top:12px;flex-wrap:wrap" },
        onRetry
          ? h(
              "button",
              { class: "btn btn-ghost btn-sm", onclick: onRetry },
              "Try again",
            )
          : null,
        gmail
          ? h(
              "a",
              { class: "btn btn-primary btn-sm", href: "#/gmail" },
              "Reconnect Gmail account",
            )
          : null,
      ),
    ),
  );
}

export async function render(root, id) {
  root.innerHTML = "";
  root.append(skeletonRows(3));

  let mailbox;
  try {
    mailbox = await api.mailbox(id);
  } catch (e) {
    root.innerHTML = "";
    root.append(
      h("a", { class: "back-link", href: "#/mailboxes" }, "← All mailboxes"),
      errorBox(
        e.status === 404
          ? "Mailbox not found."
          : e.detail || "Could not load mailbox.",
      ),
    );
    refreshIcons();
    return;
  }

  let page = 1;
  let messages = [];
  let loadingMsgs = true;
  let selected = null; // full message object

  root.innerHTML = "";
  const back = h(
    "a",
    { class: "back-link", href: "#/mailboxes" },
    "← All mailboxes",
  );
  const head = h(
    "div",
    { class: "detail-head" },
    h(
      "div",
      { style: "flex:1;min-width:240px" },
      h(
        "div",
        { style: "display:flex;gap:8px;align-items:center;flex-wrap:wrap" },
        providerBadge(mailbox.provider),
        statusPill(mailbox.is_active),
      ),
      h("div", { class: "detail-addr mt-4" }, mailbox.address),
    ),
    h(
      "div",
      { style: "display:flex;gap:8px" },
      h(
        "button",
        {
          class: "btn btn-ghost btn-sm",
          onclick: () => copyText(mailbox.address, "Address copied"),
        },
        h("i", { "data-lucide": "copy" }),
        h("span", {}, "Copy"),
      ),
      h(
        "button",
        { class: "btn btn-ghost btn-sm", onclick: refreshList },
        h("i", { "data-lucide": "refresh-cw" }),
        h("span", {}, "Refresh"),
      ),
    ),
  );

  const split = h("div", { class: "detail-split" });
  const listCol = h(
    "div",
    {},
    h(
      "div",
      { class: "section-head", style: "margin-top:0" },
      h("h2", {}, "Messages"),
      h("p", { class: "mono pager-info", id: "pager-info" }, ""),
    ),
    h("div", { class: "msg-list", id: "msg-list" }),
    h(
      "div",
      { class: "pager" },
      h("button", { class: "btn btn-ghost btn-sm", id: "prev-btn" }, "← Newer"),
      h("button", { class: "btn btn-ghost btn-sm", id: "next-btn" }, "Older →"),
    ),
  );
  const readCol = h("div", { class: "card card-pad reading", id: "reading" });
  split.append(listCol, readCol);
  root.append(back, head, split);
  refreshIcons();

  const listEl = listCol.querySelector("#msg-list");
  const pagerInfo = listCol.querySelector("#pager-info");
  const prevBtn = listCol.querySelector("#prev-btn");
  const nextBtn = listCol.querySelector("#next-btn");
  prevBtn.onclick = () => {
    if (page > 1) {
      page--;
      refreshList();
    }
  };
  nextBtn.onclick = () => {
    page++;
    refreshList();
  };

  drawReading(null);

  async function refreshList() {
    loadingMsgs = true;
    drawList();
    try {
      messages = await api.messages(mailbox.id, page);
    } catch (e) {
      loadingMsgs = false;
      listEl.innerHTML = "";
      if (e.providerAuth) {
        listEl.append(providerAuthBox({ ...e, provider: mailbox.provider }, refreshList));
      } else {
        listEl.append(
          errorBox(
            e.detail ||
              "Could not load messages (provider fetch can be slow — try again).",
            refreshList,
          ),
        );
      }
      refreshIcons();
      return;
    }
    loadingMsgs = false;
    // keep selection if still present
    if (selected) {
      const still = messages.find((m) => m.id === selected.id);
      if (!still && messages.length) {
        /* keep old reading pane */
      }
    }
    drawList();
  }

  function drawList() {
    listEl.innerHTML = "";
    prevBtn.disabled = page <= 1 || loadingMsgs;
    if (loadingMsgs) {
      listEl.append(skeletonRows(5));
      pagerInfo.textContent = "fetching from provider…";
      refreshIcons();
      return;
    }
    pagerInfo.textContent = `page ${page}`;
    nextBtn.disabled = messages.length < PAGE_SIZE_HINT;
    if (!messages.length) {
      listEl.append(
        emptyState({
          icon: "mail-open",
          title: "No messages yet",
          copy: "Waiting for incoming mail… new arrivals appear when you hit Refresh. Provider fetches can take a few seconds.",
        }),
      );
      return;
    }
    for (const m of messages) {
      listEl.append(msgItem(m, selected?.id === m.id, () => openMessage(m)));
    }
    refreshIcons();
  }

  async function openMessage(m) {
    selected = m;
    drawList();
    drawReading({ loading: true });
    try {
      const full = await api.message(mailbox.id, m.message_api_id);
      selected = full;
      drawList();
      drawReading({ msg: full });
    } catch (e) {
      drawReading({
        error: e.detail || "Could not open message.",
        providerAuth: e.providerAuth,
      });
    }
  }

  function drawReading(state) {
    readCol.innerHTML = "";
    if (!state) {
      readCol.append(
        emptyState({
          icon: "mouse-pointer-click",
          title: "Select a message",
          copy: "Pick anything on the left to read it here.",
          inline: true,
        }),
      );
      return;
    }
    if (state.loading) {
      readCol.append(skeletonRows(4));
      refreshIcons();
      return;
    }
    if (state.error) {
      if (state.providerAuth) {
        readCol.append(providerAuthBox({ detail: state.error, provider: mailbox.provider }));
      } else {
        readCol.append(errorBox(state.error));
      }
      refreshIcons();
      return;
    }
    const msg = state.msg;
    let mode = "pretty";
    const bodyWrap = h("div", {});
    const seg = msg.html?.length
      ? h(
          "div",
          { class: "seg", role: "tablist", "aria-label": "Body view" },
          h(
            "button",
            { class: "on", onclick: (e) => setMode("pretty", e) },
            "Formatted",
          ),
          h("button", { onclick: (e) => setMode("raw", e) }, "Raw HTML"),
        )
      : null;

    function setMode(next, e) {
      mode = next;
      seg
        ?.querySelectorAll("button")
        .forEach((b) => b.classList.toggle("on", b === e.currentTarget));
      drawBody();
    }
    function drawBody() {
      bodyWrap.innerHTML = "";
      if (mode === "raw" && msg.html?.length) {
        bodyWrap.append(h("pre", { class: "code" }, msg.html.join("\n")));
      } else if (msg.html?.length) {
        const frame = h("iframe", {
          title: "Message HTML",
          sandbox: "",
          style:
            "width:100%;min-height:320px;border:1px solid var(--border);border-radius:12px;background:#fff",
        });
        bodyWrap.append(frame);
        frame.srcdoc = msg.html.join("\n");
      } else {
        bodyWrap.append(
          h(
            "div",
            { class: "msg-body-text" },
            msg.text?.trim() ? msg.text : "(empty body)",
          ),
        );
      }
    }
    drawBody();

    const markBtn = h(
      "button",
      {
        class: "icon-btn",
        title: "Mark as read",
        "aria-label": "Mark as read",
        onclick: async () => {
          try {
            const updated = await api.markRead(mailbox.id, msg.message_api_id);
            selected = updated;
            messages = messages.map((x) =>
              x.message_api_id === updated.message_api_id
                ? { ...x, seen: true }
                : x,
            );
            drawList();
            toast("Marked as read.", "ok", "check");
          } catch (e) {
            toast(e.detail || "Could not mark as read.", "err");
          }
        },
      },
      h("i", { "data-lucide": "check" }),
    );
    const delBtn = h(
      "button",
      {
        class: "icon-btn danger",
        title: "Delete message",
        "aria-label": "Delete message",
        onclick: async () => {
          const ok = await confirmDialog({
            title: "Delete message?",
            message: "This removes the message permanently.",
          });
          if (!ok) return;
          try {
            await api.deleteMessage(mailbox.id, msg.message_api_id);
            toast("Message deleted.", "ok", "trash-2");
            messages = messages.filter((x) => x.id !== msg.id);
            selected = null;
            drawList();
            drawReading(null);
          } catch (e) {
            toast(e.detail || "Could not delete message.", "err");
          }
        },
      },
      h("i", { "data-lucide": "trash-2" }),
    );
    const srcBtn = h(
      "button",
      {
        class: "icon-btn",
        title: "View source",
        "aria-label": "View source",
        onclick: async () => {
          openModal({
            title: "Message source",
            sub: "Raw source as stored by the server.",
            body: h("pre", { class: "code" }, "Loading…"),
          });
          try {
            const src = await api.messageSource(mailbox.id, msg.message_api_id);
            openModal({
              title: "Message source",
              sub: `id ${src.id || msg.message_api_id || msg.id}`,
              wide: true,
              body: h("pre", { class: "code" }, src.data || "(empty)"),
              actions: [
                {
                  label: "Copy",
                  keepOpen: true,
                  onClick: () => copyText(src.data || ""),
                },
                { label: "Close", kind: "btn-primary" },
              ],
            });
          } catch (e) {
            openModal({
              title: "Message source",
              body: errorBox(e.detail || "Could not load source."),
            });
            refreshIcons();
          }
        },
      },
      h("i", { "data-lucide": "code-2" }),
    );

    readCol.append(
      h(
        "div",
        { class: "reading-head" },
        h("div", { class: "reading-subject" }, msg.subject || "(no subject)"),
        h("div", { class: "reading-actions" }, markBtn, srcBtn, delBtn),
      ),
      h(
        "dl",
        { class: "msg-meta" },
        h(
          "div",
          { class: "msg-meta-row" },
          h("dt", {}, "From"),
          h(
            "dd",
            { class: "mono" },
            msg.from_name
              ? `${msg.from_name} <${msg.from_address}>`
              : msg.from_address || "—",
          ),
        ),
        h(
          "div",
          { class: "msg-meta-row" },
          h("dt", {}, "Date"),
          h(
            "dd",
            {},
            `${fmtDate(msg.received_at)} · ${timeAgo(msg.received_at)}`,
          ),
        ),
        h(
          "div",
          { class: "msg-meta-row" },
          h("dt", {}, "Size"),
          h(
            "dd",
            { class: "mono" },
            msg.size != null ? `${msg.size} bytes` : "—",
          ),
        ),
      ),
      seg ? h("div", { style: "margin-bottom:12px" }, seg) : null,
      bodyWrap,
    );
    refreshIcons();
  }

  refreshList();
}
