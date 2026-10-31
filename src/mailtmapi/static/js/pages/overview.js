/* Overview page: status, stat cards, provider donut, 7-day trend, retention strip. */
import { api } from "../api.js";
import { h, esc, toast, refreshIcons, errorBox, skeletonCards, slugHue, timeAgo } from "../ui.js";

const POLL_MS = 30000;

let charts = [];
let resizeHandler = null;
let pollTimer = null;
let pollRoot = null;
let refreshGen = 0;

function disposeCharts() {
  for (const c of charts) { try { c.dispose(); } catch { /* already gone */ } }
  charts = [];
}
function stopPoll() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  pollRoot = null;
}
export function cleanup() {
  refreshGen += 1;
  stopPoll();
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
  { key: "mbTotal", label: "Mailboxes · live", icon: "inbox", tone: "" },
  { key: "mbActive", label: "Mailboxes · active", icon: "inbox", tone: "stat-icon--green" },
  { key: "mbDeleted", label: "Mailboxes · del (10d)", icon: "trash-2", tone: "stat-icon--red" },
  { key: "msgTotal", label: "Messages · stored", icon: "mails", tone: "stat-icon--cyan" },
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
  const storedTotal = entries.reduce((a, e) => a + (e.stored ?? 0), 0);
  const chart = window.echarts.init(el, null, { renderer: "canvas" });
  charts.push(chart);
  // One ring, one color per provider: messages still stored. Deletions live
  // on the cards underneath so the chart doesn't need a second ring to read.
  chart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "#1d2434",
      borderColor: "rgba(255,255,255,.12)",
      textStyle: { color: "#eceef4", fontFamily: "JetBrains Mono", fontSize: 12 },
      formatter: (p) => `${p.name}<br/>${p.value} stored now · ${p.percent}%`,
    },
    legend: {
      bottom: 0,
      data: entries.map((e) => e.name),
      textStyle: { color: "#9aa3b6", fontSize: 11, fontFamily: "JetBrains Mono" },
      icon: "circle", itemWidth: 8, itemHeight: 8,
    },
    graphic: [
      { type: "text", left: "center", top: "34%", style: { text: String(storedTotal), textAlign: "center", fill: "#eceef4", font: "600 28px 'JetBrains Mono', monospace" } },
      { type: "text", left: "center", top: "50%", style: { text: "stored now", textAlign: "center", fill: "#666e82", font: "500 11px Inter" } },
    ],
    series: [{
      name: "stored",
      type: "pie", radius: ["56%", "78%"], center: ["50%", "44%"],
      avoidLabelOverlap: true, label: { show: false },
      itemStyle: { borderColor: "#121722", borderWidth: 3, borderRadius: 6 },
      emphasis: { scale: true, scaleSize: 4 },
      data: entries.map((e) => ({
        name: e.name, value: e.stored,
        itemStyle: { color: `hsl(${slugHue(e.name)} 62% 56%)` },
      })),
    }],
  });
}

function mountTrend(el, days) {
  if (!window.echarts) {
    el.replaceWith(h("div", { class: "chart-fallback" }, "Charts unavailable offline."));
    return;
  }
  // Stacked bars: violet = received, red = deleted that day (ledger keeps both,
  // so a retention wipe doesn't hollow out the chart — it just shows red).
  const hasDeletes = days.some((d) => (d.deleted ?? 0) > 0);
  const series = [{
    name: "received",
    type: "bar", stack: hasDeletes ? "m" : null,
    data: days.map((d) => d.count), barWidth: "46%",
    itemStyle: {
      borderRadius: [7, 7, 3, 3],
      color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "#8f81ff" }, { offset: 1, color: "rgba(124,108,255,.25)" }] },
    },
    emphasis: { itemStyle: { color: "#a79dff" } },
  }];
  if (hasDeletes) {
    series.push({
      name: "deleted",
      type: "bar", stack: "m",
      data: days.map((d) => d.deleted ?? 0), barWidth: "46%",
      itemStyle: {
        borderRadius: [7, 7, 3, 3],
        color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "#ff7d7d" }, { offset: 1, color: "rgba(255,125,125,.3)" }] },
      },
      emphasis: { itemStyle: { color: "#ffb3b3" } },
    });
  }
  const chart = window.echarts.init(el, null, { renderer: "canvas" });
  charts.push(chart);
  chart.setOption({
    backgroundColor: "transparent",
    grid: { left: 8, right: 12, top: 12, bottom: hasDeletes ? 28 : 4, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1d2434",
      borderColor: "rgba(255,255,255,.12)",
      textStyle: { color: "#eceef4", fontFamily: "JetBrains Mono", fontSize: 12 },
    },
    legend: hasDeletes ? {
      bottom: 0, data: series.map((s) => s.name),
      textStyle: { color: "#9aa3b6", fontSize: 11, fontFamily: "JetBrains Mono" },
      icon: "circle", itemWidth: 8, itemHeight: 8,
    } : undefined,
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
    series,
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

function fmtWhen(d) {
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function legendKey(color, label, hint) {
  return h("span", { class: "legend-key", title: hint },
    h("span", { class: "legend-swatch", style: `background:${color}` }),
    h("span", {}, label));
}

function metric(value, label, tone) {
  return h("div", { class: `prov-metric${tone ? ` prov-metric--${tone}` : ""}` },
    h("b", {}, String(value)),
    h("span", {}, label));
}

function providerCard(slug, live, hist = {}) {
  const hue = slugHue(slug);
  const stored = live.messages_total ?? 0;
  const active = live.mailboxes_active ?? 0;
  const boxDel = hist.mailbox_deleted ?? 0;
  const msgDel = hist.message_deleted ?? 0;
  const boxCreated = hist.mailbox_created ?? 0;
  const msgRecv = hist.message_received ?? 0;
  const tip = `10d: +${boxCreated} / -${boxDel} boxes, +${msgRecv} / -${msgDel} msgs`;
  return h("div", { class: "card prov-card", style: `--prov-hue:${hue}`, title: tip },
    h("div", { class: "prov-card-top" },
      h("span", { class: "prov-name" },
        h("span", { class: "prov-dot", "aria-hidden": "true" }),
        slug),
      h("span", { class: `pill ${active > 0 ? "pill--on" : "pill--off"}` },
        active > 0 ? `${active} live` : "idle")),
    h("div", { class: "prov-metrics" },
      metric(active, "Live boxes"),
      metric(boxDel, "Boxes del · 10d", boxDel > 0 ? "del" : ""),
      metric(stored, "Msgs stored"),
      metric(msgDel, "Msgs del · 10d", msgDel > 0 ? "del" : "")));
}

export async function render(root, { silent = false } = {}) {
  const gen = ++refreshGen;
  disposeCharts();
  bindResize();
  if (!silent) {
    root.innerHTML = "";
    root.append(skeletonCards(5), h("div", { class: "grid grid--2 mt-4" },
      h("div", { class: "skeleton", style: "height:360px" }),
      h("div", { class: "skeleton", style: "height:360px" })));
  }

  let stats, retention, health;
  try {
    [stats, retention, health] = await Promise.all([
      api.stats(),
      api.retention().catch(() => []),
      api.health().catch(() => null),
    ]);
  } catch (e) {
    if (gen !== refreshGen) return;
    if (silent && root.childElementCount) return;
    root.innerHTML = "";
    root.append(errorBox(e.detail || "Could not load stats.", () => render(root)));
    refreshIcons();
    return;
  }
  if (gen !== refreshGen) return;

  const hist = stats.history || {};
  const histTotals = hist.totals || {};
  const histByProv = hist.by_provider || {};
  const values = {
    mbTotal: stats.mailboxes?.total ?? 0,
    mbActive: stats.mailboxes?.active ?? 0,
    mbDeleted: (histTotals.mailbox_deleted ?? 0) || (stats.mailboxes?.deleted ?? 0),
    msgTotal: stats.messages?.total ?? 0,
    gmail: stats.gmail_accounts?.total ?? 0,
  };
  const byProvider = stats.by_provider || {};
  const ttlByProvider = Object.fromEntries((retention || []).map((r) => [r.provider, r]));
  // Ledger is the single source once it has activity: received+deleted survive
  // retention, live rows do not. Otherwise fall back to the live 7-day query.
  const hasLedgerActivity = (histTotals.message_received ?? 0) + (histTotals.message_deleted ?? 0) > 0;
  const isDay = (d) => /^\d{4}-\d{2}-\d{2}$/.test(d?.date || "");
  const days = (hasLedgerActivity
    ? (hist.days || []).slice(-7).map((d) => ({ date: d.date, count: d.message_received, deleted: d.message_deleted }))
    : (stats.messages_last_7_days || [])
  ).filter(isDay);

  root.innerHTML = "";

  // stat cards
  const grid = h("div", { class: "grid grid--stats" });
  for (const s of STATS) grid.append(statCard(s, values));
  root.append(grid);

  const hCard = healthCard(health);
  if (hCard) root.append(hCard);

  // charts row
  const donutSlugs = [...new Set([...Object.keys(byProvider), ...Object.keys(histByProv)])];
  const donutEntries = donutSlugs
    .map((slug) => ({
      name: slug,
      stored: byProvider[slug]?.messages_total ?? 0,
    }))
    .filter((e) => e.stored > 0);
  const donutBox = h("div", { class: "chart-box", role: "img", "aria-label": "Messages stored now, split by provider" });
  const trendBox = h("div", { class: "chart-box", role: "img", "aria-label": "Messages received and deleted, last 7 days" });
  const updated = fmtWhen(new Date());
  root.append(h("div", { class: "grid grid--2 mt-4" },
    h("div", { class: "card chart-card" },
      h("div", { class: "chart-head" },
        h("div", {},
          h("div", { class: "chart-title" }, "Messages by provider"),
          h("div", { class: "chart-sub" }, "How many messages are stored right now")),
        h("span", { class: "chart-updated mono", title: "Overview refreshes every 30 seconds" }, `Updated ${updated}`)),
      donutEntries.length ? donutBox : h("div", { class: "chart-fallback" }, "No provider data yet — the chart will appear here."),
      donutSlugs.length
        ? h("div", { class: "prov-grid" }, ...donutSlugs.map((slug) =>
            providerCard(slug, byProvider[slug] || {}, histByProv[slug] || {})))
        : null),
    h("div", { class: "card chart-card" },
      h("div", { class: "chart-head" },
        h("div", {},
          h("div", { class: "chart-title" }, "Mail · last 7 days"),
          h("div", { class: "chart-sub" }, days.length
            ? "Each bar is one day. Violet arrived, red was deleted."
            : "No activity recorded yet")),
        h("span", { class: "chart-updated mono" }, `Updated ${updated}`)),
      days.length
        ? h("div", { class: "chart-legend" },
            legendKey("#8f81ff", "Received", "Messages that arrived that day"),
            hasLedgerActivity ? legendKey("var(--danger)", "Deleted", "Messages removed that day, including retention sweeps") : null)
        : null,
      days.length ? trendBox : h("div", { class: "chart-fallback" }, "No messages in the last 7 days — the chart will appear here."))));

  if (donutEntries.length) mountDonut(donutBox, donutEntries);
  if (days.length) mountTrend(trendBox, days);

  // last-10-days activity (retention-proof ledger — includes deleted boxes/messages)
  const histStrip = h("div", { class: "card strip mt-4" },
    h("span", { class: "strip-text" }, "Activity · last 10 days"),
    h("span", { class: "ttl-badge" }, h("b", {}, String(histTotals.mailbox_created ?? 0)), h("span", {}, "boxes created")),
    h("span", { class: "ttl-badge is-off" }, h("b", {}, String(histTotals.mailbox_deleted ?? 0)), h("span", {}, "boxes deleted")),
    h("span", { class: "ttl-badge" }, h("b", {}, String(histTotals.message_received ?? 0)), h("span", {}, "messages received")),
    h("span", { class: "ttl-badge is-off" }, h("b", {}, String(histTotals.message_deleted ?? 0)), h("span", {}, "messages deleted")));
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
  if (pollRoot !== root) {
    stopPoll();
    pollRoot = root;
    pollTimer = setInterval(() => {
      if (document.hidden || pollRoot !== root) return;
      render(root, { silent: true });
    }, POLL_MS);
  }

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
