/* Overview page: status, stat cards, provider donut, 7-day trend, retention strip. */
import { api } from "../api.js";
import { h, esc, toast, refreshIcons, errorBox, skeletonCards, slugHue, timeAgo } from "../ui.js";

let charts = [];
let resizeHandler = null;

function disposeCharts() {
  for (const c of charts) { try { c.dispose(); } catch { /* already gone */ } }
  charts = [];
}
export function cleanup() {
  disposeCharts();
  if (resizeHandler) { window.removeEventListener("resize", resizeHandler); resizeHandler = null; }
}

/* One debounced resize listener for every live chart, removed on cleanup. */
function bindResize() {
  if (resizeHandler) window.removeEventListener("resize", resizeHandler);
  let t = null;
  resizeHandler = () => {
    clearTimeout(t);
    t = setTimeout(() => {
      for (const c of charts) { try { c.resize(); } catch { /* disposed */ } }
    }, 150);
  };
  window.addEventListener("resize", resizeHandler);
}

const STATS = [
  { key: "mbTotal", label: "Mailboxes · total", icon: "inbox", tone: "" },
  { key: "mbActive", label: "Mailboxes · active", icon: "inbox", tone: "stat-icon--green" },
  { key: "mbDeleted", label: "Mailboxes · deleted", icon: "trash-2", tone: "stat-icon--red" },
  { key: "msgTotal", label: "Messages · total", icon: "mails", tone: "stat-icon--cyan" },
  { key: "gmail", label: "Gmail accounts", icon: "at-sign", tone: "stat-icon--amber" },
];

function statCard(s, values) {
  return h("div", { class: "card stat-card" },
    h("div", { class: "stat-top" },
      h("span", { class: `stat-icon ${s.tone}` }, h("i", { "data-lucide": s.icon })),
      h("span", { class: "stat-label" }, s.label)),
    h("div", { class: "stat-value" }, String(values[s.key] ?? "—")));
}

function mountDonut(el, entries) {
  if (!window.echarts) {
    el.replaceWith(h("div", { class: "chart-fallback" }, "Charts unavailable offline — data is listed below."));
    return;
  }
  const total = entries.reduce((a, [, v]) => a + (v.messages_total ?? 0), 0);
  const chart = window.echarts.init(el, null, { renderer: "canvas" });
  charts.push(chart);
  chart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "#1d2434", borderColor: "rgba(255,255,255,.12)", textStyle: { color: "#eceef4", fontFamily: "JetBrains Mono" } },
    legend: { bottom: 0, textStyle: { color: "#9aa3b6", fontSize: 11, fontFamily: "JetBrains Mono" }, icon: "circle", itemWidth: 8, itemHeight: 8 },
    graphic: [
      { type: "text", left: "center", top: "36%", style: { text: String(total), textAlign: "center", fill: "#eceef4", font: "600 26px 'JetBrains Mono', monospace" } },
      { type: "text", left: "center", top: "50%", style: { text: "messages", textAlign: "center", fill: "#666e82", font: "500 11px Inter" } },
    ],
    series: [{
      type: "pie", radius: ["58%", "80%"], center: ["50%", "44%"],
      avoidLabelOverlap: true, label: { show: false },
      itemStyle: { borderColor: "#121722", borderWidth: 3, borderRadius: 6 },
      emphasis: { scale: true, scaleSize: 4 },
      // Same hue the provider's badge uses, so colors match everywhere.
      data: entries.map(([name, v]) => ({
        name, value: v.messages_total ?? 0,
        itemStyle: { color: `hsl(${slugHue(name)} 62% 56%)` },
      })),
    }],
  });
}

function mountTrend(el, days) {
  if (!window.echarts) {
    el.replaceWith(h("div", { class: "chart-fallback" }, "Charts unavailable offline."));
    return;
  }
  const chart = window.echarts.init(el, null, { renderer: "canvas" });
  charts.push(chart);
  chart.setOption({
    backgroundColor: "transparent",
    grid: { left: 8, right: 12, top: 26, bottom: 0, containLabel: true },
    tooltip: { trigger: "axis", backgroundColor: "#1d2434", borderColor: "rgba(255,255,255,.12)", textStyle: { color: "#eceef4", fontFamily: "JetBrains Mono" } },
    xAxis: {
      type: "category", data: days.map((d) => d.date.slice(5)),
      axisLine: { lineStyle: { color: "rgba(255,255,255,.1)" } },
      axisTick: { show: false }, axisLabel: { color: "#666e82", fontFamily: "JetBrains Mono", fontSize: 10 },
    },
    yAxis: {
      type: "value", minInterval: 1,
      splitLine: { lineStyle: { color: "rgba(255,255,255,.06)" } },
      axisLabel: { color: "#666e82", fontFamily: "JetBrains Mono", fontSize: 10 },
    },
    series: [{
      type: "bar", data: days.map((d) => d.count),
      barWidth: "46%",
      itemStyle: {
        borderRadius: [7, 7, 3, 3],
        color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "#8f81ff" }, { offset: 1, color: "rgba(124,108,255,.25)" }] },
      },
      emphasis: { itemStyle: { color: "#a79dff" } },
    }],
  });
}

function healthCard(health) {
  const cache = (health && health.domain_cache) || {};
  const entries = Object.entries(cache);
  if (!entries.length) return null;
  const rows = entries.map(([slug, m]) => {
    const bad = Boolean(m && m.error);
    return h("div", { class: "health-row" },
      h("div", { class: "health-row-main" },
        h("span", { class: "prov-name mono" }, slug),
        h("span", { class: `pill ${bad ? "pill--danger" : "pill--on"}` },
          bad ? "error" : "ok")),
      h("div", { class: "health-meta" },
        h("span", {}, `${m?.domains ?? 0} domains`),
        h("span", {}, "·"),
        h("span", {}, `refresh ${timeAgo(m?.last_refresh)}`)),
      bad ? h("div", { class: "health-err", title: m.error }, m.error) : null);
  });
  return h("div", { class: "card chart-card mt-4" },
    h("div", { class: "chart-title" }, "Provider health"),
    h("div", { class: "chart-sub" }, "Domain cache refresh state per provider"),
    h("div", { class: "health-list mt-4" }, ...rows),
    h("a", { class: "mini-link", href: "#/domain-cache" },
      "Manage domain cache", h("i", { "data-lucide": "arrow-up-right" })));
}

function ttlText(v) {
  return v == null ? "disabled" : `${v}h`;
}

export async function render(root) {
  disposeCharts();
  bindResize();
  root.innerHTML = "";
  root.append(skeletonCards(5), h("div", { class: "grid grid--2 mt-4" },
    h("div", { class: "skeleton", style: "height:360px" }),
    h("div", { class: "skeleton", style: "height:360px" })));

  let stats, retention, health;
  try {
    [stats, retention, health] = await Promise.all([
      api.stats(),
      api.retention().catch(() => []),
      api.health().catch(() => null),
    ]);
  } catch (e) {
    root.innerHTML = "";
    root.append(errorBox(e.detail || "Could not load stats.", () => render(root)));
    refreshIcons();
    return;
  }

  const values = {
    mbTotal: stats.mailboxes?.total ?? 0,
    mbActive: stats.mailboxes?.active ?? 0,
    mbDeleted: stats.mailboxes?.deleted ?? 0,
    msgTotal: stats.messages?.total ?? 0,
    gmail: stats.gmail_accounts?.total ?? 0,
  };
  const byProvider = stats.by_provider || {};
  const days = stats.messages_last_7_days || [];
  const ttlByProvider = Object.fromEntries((retention || []).map((r) => [r.provider, r]));

  root.innerHTML = "";

  // stat cards
  const grid = h("div", { class: "grid grid--stats" });
  for (const s of STATS) grid.append(statCard(s, values));
  root.append(grid);

  const hCard = healthCard(health);
  if (hCard) root.append(hCard);

  // charts row
  const entries = Object.entries(byProvider);
  const donutBox = h("div", { class: "chart-box", role: "img", "aria-label": "Messages per provider" });
  const trendBox = h("div", { class: "chart-box", role: "img", "aria-label": "Messages received, last 7 days" });
  root.append(h("div", { class: "grid grid--2 mt-4" },
    h("div", { class: "card chart-card" },
      h("div", { class: "chart-title" }, "Provider split"),
      h("div", { class: "chart-sub" }, "Share of stored messages by provider"),
      entries.length ? donutBox : h("div", { class: "chart-fallback" }, "No provider data yet — the chart will appear here."),
      h("div", { class: "prov-grid" }, ...entries.map(([slug, v]) =>
        h("div", { class: "card prov-card" },
          h("div", { class: "prov-card-top" },
            h("span", { class: "prov-name" }, slug),
            h("span", { class: `pill ${(v.mailboxes_active ?? 0) > 0 ? "pill--on" : "pill--off"}` }, `${v.mailboxes_active ?? 0} live`)),
          h("div", { class: "prov-nums" },
            h("div", {}, h("b", {}, String(v.messages_total ?? 0)), h("span", {}, "msgs")),
            h("div", {}, h("b", {}, String(v.mailboxes_total ?? 0)), h("span", {}, "boxes"))))))),
    h("div", { class: "card chart-card" },
      h("div", { class: "chart-title" }, "Incoming mail · 7 days"),
      h("div", { class: "chart-sub" }, days.length ? "Messages stored per day" : "No activity recorded yet"),
      days.length ? trendBox : h("div", { class: "chart-fallback" }, "No messages in the last 7 days — the chart will appear here."))));

  if (entries.length) mountDonut(donutBox, entries);
  if (days.length) mountTrend(trendBox, days);

  // last-10-days activity (retention-proof ledger — includes deleted boxes/messages)
  const hist = stats.history && stats.history.totals ? stats.history.totals : {};
  const histStrip = h("div", { class: "card strip mt-4" },
    h("span", { class: "strip-text" }, "Activity · last 10 days"),
    h("span", { class: "ttl-badge" }, h("b", {}, String(hist.mailbox_created ?? 0)), h("span", {}, "boxes created")),
    h("span", { class: "ttl-badge is-off" }, h("b", {}, String(hist.mailbox_deleted ?? 0)), h("span", {}, "boxes deleted")),
    h("span", { class: "ttl-badge" }, h("b", {}, String(hist.message_received ?? 0)), h("span", {}, "messages received")),
    h("span", { class: "ttl-badge is-off" }, h("b", {}, String(hist.message_deleted ?? 0)), h("span", {}, "messages deleted")));
  root.append(histStrip);

  // retention strip
  const slugs = [...new Set([...Object.keys(byProvider), ...Object.keys(ttlByProvider)])];
  const strip = h("div", { class: "card strip mt-4" });
  if (!slugs.length) {
    strip.append(h("span", { class: "strip-text" }, "No providers seen yet — retention rules can be set once a provider is used."));
  } else {
    for (const slug of slugs) {
      const r = ttlByProvider[slug];
      strip.append(h("span", { class: `ttl-badge ${!r || (r.mailbox_ttl_hours == null && r.message_ttl_hours == null) ? "is-off" : ""}` },
        h("span", {}, esc(slug)),
        h("b", {}, `box ${ttlText(r?.mailbox_ttl_hours)} · msg ${ttlText(r?.message_ttl_hours)}`)));
    }
    const spacer = h("span", { class: "strip-text" }, "");
    const btn = h("button", { class: "btn btn-ghost btn-sm", onclick: runSweep },
      h("i", { "data-lucide": "timer" }), h("span", {}, "Run retention sweep"));
    strip.append(spacer, btn);
  }
  if (!slugs.length) {
    const btn = h("button", { class: "btn btn-ghost btn-sm", onclick: runSweep },
      h("i", { "data-lucide": "timer" }), h("span", {}, "Run retention sweep"));
    strip.append(btn);
  }
  root.append(strip);
  refreshIcons();

  async function runSweep(e) {
    const btn = e.currentTarget;
    btn.disabled = true;
    btn.classList.add("is-loading");
    try {
      const res = await api.runRetention();
      toast(`Sweep done — deleted ${res.mailboxes_deleted ?? 0} mailboxes, ${res.messages_deleted ?? 0} messages.`, "ok", "timer");
      render(root);
    } catch (err) {
      toast(err.detail || "Sweep failed.", "err");
      btn.disabled = false;
      btn.classList.remove("is-loading");
    }
  }
}
