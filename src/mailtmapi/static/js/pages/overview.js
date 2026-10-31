/* Overview page: executive system health, KPI cards, interactive 10-day dynamics,
   provider storage breakdown, domain intelligence, and provider infrastructure grid. */
import { api } from "../api.js";
import { h, esc, toast, refreshIcons, errorBox, skeletonCards, slugHue, timeAgo } from "../ui.js";

const POLL_MS = 30000;

let charts = [];
let resizeHandler = null;
let pollTimer = null;
let pollRoot = null;
let refreshGen = 0;

// State for interactive chart toggles
let trendMode = "messages";   // "messages" | "mailboxes"
let donutMode = "messages";   // "messages" | "mailboxes"

function disposeCharts() {
  for (const c of charts) {
    try { c.dispose(); } catch { /* already gone */ }
  }
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
  if (resizeHandler) {
    window.removeEventListener("resize", resizeHandler);
    resizeHandler = null;
  }
}

/* One debounced resize listener for every live chart, removed on cleanup. */
function bindResize() {
  if (resizeHandler) window.removeEventListener("resize", resizeHandler);
  let t = null;
  resizeHandler = () => {
    clearTimeout(t);
    t = setTimeout(() => {
      for (const c of charts) {
        try { c.resize(); } catch { /* disposed */ }
      }
    }, 150);
  };
  window.addEventListener("resize", resizeHandler);
}

function statCard({ key, label, icon, tone, subText, subTone }, values) {
  const val = values[key] ?? "—";
  const sub = typeof subText === "function" ? subText(values) : subText;
  const sTone = typeof subTone === "function" ? subTone(values) : subTone;
  return h("div", { class: "card stat-card" },
    h("div", { class: "stat-top" },
      h("span", { class: `stat-icon ${tone}` }, h("i", { "data-lucide": icon })),
      h("span", { class: "stat-label" }, label)),
    h("div", { class: "stat-value" }, String(val)),
    sub ? h("div", { class: `kpi-sub ${sTone ? `kpi-sub--${sTone}` : ""}` }, sub) : null);
}

/* ------------------------------------------------------------
   Charts: 10-Day Dynamics Timeline (Area + Bar combo)
   ------------------------------------------------------------ */
function mountTrend(el, days, mode = "messages") {
  if (!window.echarts) {
    el.replaceWith(h("div", { class: "chart-fallback" }, "Charts unavailable offline."));
    return;
  }

  const isMsg = mode === "messages";
  const primaryName = isMsg ? "Received" : "Created";
  const secondaryName = isMsg ? "Deleted" : "Deleted";
  const primaryKey = isMsg ? "inCount" : "boxCreated";
  const secondaryKey = isMsg ? "outCount" : "boxDeleted";

  const dates = days.map((d) => d.date.slice(5));
  const primaryData = days.map((d) => d[primaryKey] ?? 0);
  const secondaryData = days.map((d) => d[secondaryKey] ?? 0);
  const hasSecondary = secondaryData.some((v) => v > 0);

  const primaryColor = isMsg ? "#8f81ff" : "#41d99a";
  const primaryGrad = isMsg
    ? [{ offset: 0, color: "rgba(143,129,255,0.42)" }, { offset: 1, color: "rgba(124,108,255,0.02)" }]
    : [{ offset: 0, color: "rgba(65,217,154,0.38)" }, { offset: 1, color: "rgba(65,217,154,0.02)" }];

  const series = [
    {
      name: primaryName,
      type: "line",
      smooth: true,
      showSymbol: false,
      symbolSize: 6,
      lineStyle: { width: 3, color: primaryColor },
      areaStyle: {
        color: {
          type: "linear", x: 0, y: 0, x2: 0, y2: 1,
          colorStops: primaryGrad,
        },
      },
      data: primaryData,
    },
  ];

  if (hasSecondary) {
    series.push({
      name: secondaryName,
      type: "bar",
      barMaxWidth: 16,
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: {
          type: "linear", x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: "#ff7d7d" }, { offset: 1, color: "rgba(255,125,125,0.25)" }],
        },
      },
      data: secondaryData,
    });
  }

  const chart = window.echarts.init(el, null, { renderer: "canvas" });
  charts.push(chart);

  chart.setOption({
    backgroundColor: "transparent",
    grid: { left: 8, right: 12, top: 20, bottom: 24, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#161c29",
      borderColor: "rgba(255,255,255,0.12)",
      textStyle: { color: "#eceef4", fontFamily: "JetBrains Mono", fontSize: 12 },
      formatter: (items) => {
        if (!items || !items.length) return "";
        const title = items[0].axisValue;
        let html = `<div style="font-weight:600;margin-bottom:4px;color:#9aa3b6">${title}</div>`;
        let prim = 0;
        let sec = 0;
        for (const item of items) {
          const val = item.value ?? 0;
          if (item.seriesName === primaryName) prim = val;
          if (item.seriesName === secondaryName) sec = val;
          html += `<div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
            <span>${item.marker} ${item.seriesName}</span>
            <b style="font-family:JetBrains Mono">${val}</b>
          </div>`;
        }
        const diff = prim - sec;
        const diffColor = diff > 0 ? "var(--ok)" : diff < 0 ? "var(--danger)" : "var(--muted)";
        const sign = diff > 0 ? "+" : "";
        html += `<div style="border-top:1px solid rgba(255,255,255,0.08);margin-top:6px;padding-top:4px;display:flex;justify-content:space-between;gap:12px;font-size:11px">
          <span style="color:#666e82">Net flow</span>
          <b style="color:${diffColor};font-family:JetBrains Mono">${sign}${diff}</b>
        </div>`;
        return html;
      },
    },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.1)" } },
      axisTick: { show: false },
      axisLabel: { color: "#666e82", fontFamily: "JetBrains Mono", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      minInterval: 1,
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
      axisLabel: { color: "#666e82", fontFamily: "JetBrains Mono", fontSize: 10 },
    },
    series,
  });
}

/* ------------------------------------------------------------
   Charts: Distribution Donut (Hollow ring w/ center total)
   ------------------------------------------------------------ */
function mountDonut(el, entries, label = "stored now") {
  if (!window.echarts) {
    el.replaceWith(h("div", { class: "chart-fallback" }, "Charts unavailable offline."));
    return;
  }
  const total = entries.reduce((a, e) => a + (e.value ?? 0), 0);
  const chart = window.echarts.init(el, null, { renderer: "canvas" });
  charts.push(chart);

  chart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "#161c29",
      borderColor: "rgba(255,255,255,0.12)",
      textStyle: { color: "#eceef4", fontFamily: "JetBrains Mono", fontSize: 12 },
      formatter: (p) => `${p.name}<br/><b>${p.value}</b> (${p.percent}%)`,
    },
    legend: {
      bottom: 0,
      data: entries.map((e) => e.name),
      textStyle: { color: "#9aa3b6", fontSize: 11, fontFamily: "JetBrains Mono" },
      icon: "circle",
      itemWidth: 8,
      itemHeight: 8,
    },
    graphic: [
      {
        type: "text",
        left: "center",
        top: "35%",
        style: {
          text: String(total),
          textAlign: "center",
          fill: "#eceef4",
          font: "600 28px 'JetBrains Mono', monospace",
        },
      },
      {
        type: "text",
        left: "center",
        top: "50%",
        style: {
          text: label,
          textAlign: "center",
          fill: "#666e82",
          font: "500 11px Inter, sans-serif",
        },
      },
    ],
    series: [{
      name: label,
      type: "pie",
      radius: ["58%", "80%"],
      center: ["50%", "44%"],
      avoidLabelOverlap: true,
      label: { show: false },
      itemStyle: { borderColor: "#121722", borderWidth: 3, borderRadius: 6 },
      emphasis: { scale: true, scaleSize: 4 },
      data: entries.map((e) => ({
        name: e.name,
        value: e.value,
        itemStyle: { color: `hsl(${slugHue(e.name)} 62% 56%)` },
      })),
    }],
  });
}

/* ------------------------------------------------------------
   UI: System Status Hero Banner
   ------------------------------------------------------------ */
function heroBanner({ health, config, isSweeping, onRefresh, onSweep }) {
  const cache = (health && health.domain_cache) || {};
  const entries = Object.entries(cache);
  const failing = entries.filter(([, m]) => m && m.error).map(([slug]) => slug);
  const isHealthy = failing.length === 0;

  const versionText = config?.client_version ? `v${config.client_version}` : "v0.1.0";
  const authProtected = Boolean(config?.api_key_required);

  return h("div", { class: "overview-hero" },
    h("div", { class: "hero-status-group" },
      h("span", { class: `pulse-dot ${isHealthy ? "" : "is-warn"}`, "aria-hidden": "true" }),
      h("div", {},
        h("div", { style: "display:flex;align-items:center;gap:8px" },
          h("b", { style: "font-size:var(--fs-14);font-family:var(--font-ui)" },
            isHealthy ? "System operational" : `${failing.length} provider(s) degraded`),
          h("span", { class: "badge mono", style: "font-size:10px" }, versionText),
          h("span", {
            class: `badge ${authProtected ? "badge--ok" : "badge--warn"} mono`,
            style: "font-size:10px",
            title: authProtected ? "Protected by MAILTM_API_KEY" : "No API key configured (open local access)",
          }, authProtected ? "auth on" : "no auth key")),
        h("div", { style: "font-size:var(--fs-12);color:var(--muted);margin-top:2px" },
          isHealthy
            ? `${entries.length} domain providers active · automated retention active`
            : `Degraded domain cache: ${failing.join(", ")}`))),
    h("div", { class: "hero-actions" },
      h("button", {
        class: "btn btn-ghost btn-sm",
        onclick: onRefresh,
        title: "Refresh dashboard stats immediately",
      }, h("i", { "data-lucide": "refresh-cw" }), h("span", {}, "Refresh")),
      h("button", {
        class: `btn btn-ghost btn-sm ${isSweeping ? "is-loading" : ""}`,
        disabled: isSweeping,
        onclick: onSweep,
        title: "Trigger retention policy cleanup sweep",
      }, h("i", { "data-lucide": "timer" }), h("span", {}, "Run retention sweep"))));
}

/* ------------------------------------------------------------
   UI: Provider Infrastructure Card
   ------------------------------------------------------------ */
function providerCard(slug, live, hist = {}, healthEntry = null, ttl = null) {
  const hue = slugHue(slug);
  const stored = live.messages_total ?? 0;
  const active = live.mailboxes_active ?? 0;
  const boxDel = hist.mailbox_deleted ?? 0;
  const msgDel = hist.message_deleted ?? 0;
  const boxCreated = hist.mailbox_created ?? 0;
  const msgRecv = hist.message_received ?? 0;

  const hasCacheErr = Boolean(healthEntry && healthEntry.error);
  const cachedDomains = healthEntry?.domains ?? 0;

  const ttlInfo = ttl && (ttl.mailbox_ttl_hours != null || ttl.message_ttl_hours != null)
    ? `box ${ttl.mailbox_ttl_hours ?? "—"}h · msg ${ttl.message_ttl_hours ?? "—"}h`
    : "no ttl";

  const tip = `10d: +${boxCreated} / -${boxDel} boxes, +${msgRecv} / -${msgDel} msgs`;

  return h("div", { class: "card prov-card", style: `--prov-hue:${hue}`, title: tip },
    h("div", { class: "prov-card-top" },
      h("span", { class: "prov-name" },
        h("span", { class: "prov-dot", "aria-hidden": "true" }),
        slug),
      h("span", {
        class: `pill ${hasCacheErr ? "pill--danger" : active > 0 ? "pill--on" : "pill--off"}`,
      }, hasCacheErr ? "cache error" : active > 0 ? `${active} live` : "idle")),
    h("div", { class: "prov-metrics" },
      h("div", { class: "prov-metric" },
        h("b", {}, String(active)),
        h("span", {}, "Live boxes")),
      h("div", { class: `prov-metric ${boxDel > 0 ? "prov-metric--del" : ""}` },
        h("b", {}, String(boxDel)),
        h("span", {}, "Deleted (10d)")),
      h("div", { class: "prov-metric" },
        h("b", {}, String(stored)),
        h("span", {}, "Msgs stored")),
      h("div", { class: `prov-metric ${msgDel > 0 ? "prov-metric--del" : ""}` },
        h("b", {}, String(msgDel)),
        h("span", {}, "Msg del (10d)"))),
    h("div", { class: "prov-card-foot" },
      h("span", {}, `${cachedDomains} domains · ${timeAgo(healthEntry?.last_refresh)}`),
      h("span", { class: "mono", style: "font-size:10px" }, ttlInfo)));
}

/* ------------------------------------------------------------
   UI: Domain Activity Progress Bars
   ------------------------------------------------------------ */
function domainIntelligenceCard(domainMap) {
  const entries = Object.entries(domainMap || {})
    .filter(([dom]) => dom && dom.length > 0)
    .map(([dom, counts]) => ({
      domain: dom,
      received: counts.message_received ?? 0,
      created: counts.mailbox_created ?? 0,
    }))
    .sort((a, b) => (b.received + b.created) - (a.received + a.created))
    .slice(0, 6);

  if (!entries.length) return null;

  const maxActivity = Math.max(...entries.map((e) => e.received + e.created), 1);

  const items = entries.map((e) => {
    const total = e.received + e.created;
    const pct = Math.round((total / maxActivity) * 100);
    return h("div", { class: "domain-item" },
      h("div", { class: "domain-item-head" },
        h("span", { class: "domain-item-name" }, e.domain),
        h("span", { class: "domain-item-stat" }, `${e.received} msgs · ${e.created} boxes`)),
      h("div", { class: "domain-bar-track" },
        h("div", { class: "domain-bar-fill", style: `width:${pct}%` })));
  });

  return h("div", { class: "card chart-card mt-4" },
    h("div", { class: "chart-head" },
      h("div", {},
        h("div", { class: "chart-title" }, "Domain activity distribution"),
        h("div", { class: "chart-sub" }, "Top domains by traffic across the 10-day ledger"))),
    h("div", { class: "domain-list" }, ...items));
}

function ttlText(v) {
  return v == null ? "disabled" : `${v}h`;
}

function fmtWhen(d) {
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/* ------------------------------------------------------------
   Main Render Function
   ------------------------------------------------------------ */
export async function render(root, { silent = false } = {}) {
  const gen = ++refreshGen;
  disposeCharts();
  bindResize();

  if (!silent) {
    root.innerHTML = "";
    root.append(
      skeletonCards(5),
      h("div", { class: "grid grid--2 mt-4" },
        h("div", { class: "skeleton", style: "height:360px" }),
        h("div", { class: "skeleton", style: "height:360px" })));
  }

  let stats, retention, health, config;
  try {
    [stats, retention, health, config] = await Promise.all([
      api.stats(),
      api.retention().catch(() => []),
      api.health().catch(() => null),
      api.config().catch(() => null),
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
  const byProvider = stats.by_provider || {};
  const domainCache = health?.domain_cache || {};
  const ttlByProvider = Object.fromEntries((retention || []).map((r) => [r.provider, r]));

  const mbTotal = stats.mailboxes?.total ?? 0;
  const mbActive = stats.mailboxes?.active ?? 0;
  const mbDel = (histTotals.mailbox_deleted ?? 0) || (stats.mailboxes?.deleted ?? 0);
  const msgTotal = stats.messages?.total ?? 0;
  const msgRecv10d = histTotals.message_received ?? 0;
  const msgDel10d = histTotals.message_deleted ?? 0;
  const activeProvCount = Object.keys(byProvider).length;

  const values = {
    mbTotal,
    mbActive,
    mbDeleted: mbDel,
    msgTotal,
    gmail: stats.gmail_accounts?.total ?? 0,
    gmailActive: stats.gmail_accounts?.active ?? 0,
  };

  const statConfig = [
    {
      key: "mbTotal",
      label: "Mailboxes · live",
      icon: "inbox",
      tone: "",
      subText: () => `${mbActive} active (${mbTotal ? Math.round((mbActive / mbTotal) * 100) : 0}%)`,
      subTone: "ok",
    },
    {
      key: "mbActive",
      label: "Mailboxes · active",
      icon: "check-circle-2",
      tone: "stat-icon--green",
      subText: () => `${mbDel} deleted (10d)`,
      subTone: "",
    },
    {
      key: "msgTotal",
      label: "Messages · stored",
      icon: "mails",
      tone: "stat-icon--cyan",
      subText: () => `+${msgRecv10d} in · -${msgDel10d} out`,
      subTone: msgRecv10d >= msgDel10d ? "ok" : "warn",
    },
    {
      key: "mbDeleted",
      label: "Activity flow (10d)",
      icon: "activity",
      tone: "stat-icon--amber",
      subText: () => `+${histTotals.mailbox_created ?? 0} boxes · +${msgRecv10d} msgs`,
      subTone: "",
    },
    {
      key: "gmail",
      label: "Gmail accounts",
      icon: "at-sign",
      tone: "stat-icon--green",
      subText: () => `${values.gmailActive} connected & synced`,
      subTone: values.gmailActive > 0 ? "ok" : "",
    },
  ];

  // 10-day history timeline series
  const rawDays = hist.days && hist.days.length
    ? hist.days
    : (stats.messages_last_7_days || []).map((d) => ({
        date: d.date,
        message_received: d.count,
        message_deleted: 0,
        mailbox_created: 0,
        mailbox_deleted: 0,
      }));

  const days = rawDays.map((d) => ({
    date: d.date,
    inCount: d.message_received ?? 0,
    outCount: d.message_deleted ?? 0,
    boxCreated: d.mailbox_created ?? 0,
    boxDeleted: d.mailbox_deleted ?? 0,
  }));

  root.innerHTML = "";

  // 1. Hero Status & Action Banner
  let isSweeping = false;
  async function triggerSweep() {
    isSweeping = true;
    render(root, { silent: true });
    try {
      const res = await api.runRetention();
      toast(`Sweep complete — deleted ${res.mailboxes_deleted ?? 0} mailboxes, ${res.messages_deleted ?? 0} messages.`, "ok", "timer");
      render(root);
    } catch (err) {
      toast(err.detail || "Sweep failed.", "err");
      isSweeping = false;
      render(root, { silent: true });
    }
  }

  root.append(heroBanner({
    health,
    config,
    isSweeping,
    onRefresh: () => render(root),
    onSweep: triggerSweep,
  }));

  // 2. Metric KPI Cards
  const grid = h("div", { class: "grid grid--stats" });
  for (const s of statConfig) grid.append(statCard(s, values));
  root.append(grid);

  // 3. Interactive Charts (Dynamics Timeline & Provider Donut)
  const donutSlugs = [...new Set([...Object.keys(byProvider), ...Object.keys(histByProv)])];

  function getDonutEntries(mode) {
    if (mode === "mailboxes") {
      return donutSlugs
        .map((slug) => ({
          name: slug,
          value: byProvider[slug]?.mailboxes_active ?? 0,
        }))
        .filter((e) => e.value > 0);
    }
    return donutSlugs
      .map((slug) => ({
        name: slug,
        value: byProvider[slug]?.messages_total ?? 0,
      }))
      .filter((e) => e.value > 0);
  }

  const updated = fmtWhen(new Date());

  // Left Chart: 10-day dynamics timeline
  const trendBox = h("div", { class: "chart-box", role: "img", "aria-label": "10-day activity trend chart" });
  const trendCard = h("div", { class: "card chart-card" },
    h("div", { class: "chart-head" },
      h("div", {},
        h("div", { class: "chart-title" }, "Activity dynamics · 10 days"),
        h("div", { class: "chart-sub" }, "Daily throughput recorded by the ledger")),
      h("div", { class: "chart-actions" },
        h("div", { class: "chart-tabs", role: "tablist", "aria-label": "Trend chart metric" },
          h("button", {
            class: `chart-tab-btn ${trendMode === "messages" ? "is-active" : ""}`,
            onclick: () => {
              trendMode = "messages";
              trendCard.querySelector(".chart-tab-btn:nth-child(1)").classList.add("is-active");
              trendCard.querySelector(".chart-tab-btn:nth-child(2)").classList.remove("is-active");
              mountTrend(trendBox, days, "messages");
            },
          }, "Messages"),
          h("button", {
            class: `chart-tab-btn ${trendMode === "mailboxes" ? "is-active" : ""}`,
            onclick: () => {
              trendMode = "mailboxes";
              trendCard.querySelector(".chart-tab-btn:nth-child(2)").classList.add("is-active");
              trendCard.querySelector(".chart-tab-btn:nth-child(1)").classList.remove("is-active");
              mountTrend(trendBox, days, "mailboxes");
            },
          }, "Mailboxes")),
        h("span", { class: "chart-updated mono" }, `Sync ${updated}`))),
    days.length ? trendBox : h("div", { class: "chart-fallback" }, "No activity recorded in the last 10 days."));

  // Right Chart: Provider distribution donut
  const donutBox = h("div", { class: "chart-box", role: "img", "aria-label": "Provider distribution chart" });
  const donutCard = h("div", { class: "card chart-card" },
    h("div", { class: "chart-head" },
      h("div", {},
        h("div", { class: "chart-title" }, "Provider distribution"),
        h("div", { class: "chart-sub" }, "Share of traffic across integrated providers")),
      h("div", { class: "chart-actions" },
        h("div", { class: "chart-tabs", role: "tablist", "aria-label": "Donut distribution metric" },
          h("button", {
            class: `chart-tab-btn ${donutMode === "messages" ? "is-active" : ""}`,
            onclick: () => {
              donutMode = "messages";
              donutCard.querySelector(".chart-tab-btn:nth-child(1)").classList.add("is-active");
              donutCard.querySelector(".chart-tab-btn:nth-child(2)").classList.remove("is-active");
              mountDonut(donutBox, getDonutEntries("messages"), "messages stored");
            },
          }, "Messages"),
          h("button", {
            class: `chart-tab-btn ${donutMode === "mailboxes" ? "is-active" : ""}`,
            onclick: () => {
              donutMode = "mailboxes";
              donutCard.querySelector(".chart-tab-btn:nth-child(2)").classList.add("is-active");
              donutCard.querySelector(".chart-tab-btn:nth-child(1)").classList.remove("is-active");
              mountDonut(donutBox, getDonutEntries("mailboxes"), "live mailboxes");
            },
          }, "Mailboxes")),
        h("span", { class: "chart-updated mono" }, `Sync ${updated}`))),
    donutSlugs.length ? donutBox : h("div", { class: "chart-fallback" }, "No provider data available."));

  root.append(h("div", { class: "grid grid--2 mt-4" }, trendCard, donutCard));

  if (days.length) mountTrend(trendBox, days, trendMode);
  if (donutSlugs.length) mountDonut(donutBox, getDonutEntries(donutMode), donutMode === "messages" ? "messages stored" : "live mailboxes");

  // 4. Domain Intelligence (Top Domains)
  const domainCard = domainIntelligenceCard(hist.by_domain);
  if (domainCard) root.append(domainCard);

  // 5. Provider Infrastructure Grid
  if (donutSlugs.length) {
    const provCards = donutSlugs.map((slug) =>
      providerCard(
        slug,
        byProvider[slug] || {},
        histByProv[slug] || {},
        domainCache[slug] || null,
        ttlByProvider[slug] || null,
      ));
    root.append(h("div", { class: "card chart-card mt-4" },
      h("div", { class: "chart-head" },
        h("div", {},
          h("div", { class: "chart-title" }, "Provider infrastructure & health"),
          h("div", { class: "chart-sub" }, "Real-time metrics, domain cache state, and TTL retention rules")),
        h("a", { class: "mini-link", href: "#/domain-cache" },
          "Manage domain cache", h("i", { "data-lucide": "arrow-up-right" }))),
      h("div", { class: "prov-grid" }, ...provCards)));
  }

  // 6. 10-Day Ledger Totals Strip
  const histStrip = h("div", { class: "card strip mt-4" },
    h("span", { class: "strip-text" }, "10-day activity ledger (retention-proof)"),
    h("span", { class: "ttl-badge" }, h("b", {}, String(histTotals.mailbox_created ?? 0)), h("span", {}, "boxes created")),
    h("span", { class: "ttl-badge is-off" }, h("b", {}, String(histTotals.mailbox_deleted ?? 0)), h("span", {}, "boxes cleaned")),
    h("span", { class: "ttl-badge" }, h("b", {}, String(histTotals.message_received ?? 0)), h("span", {}, "messages received")),
    h("span", { class: "ttl-badge is-off" }, h("b", {}, String(histTotals.message_deleted ?? 0)), h("span", {}, "messages purged")));
  root.append(histStrip);

  // 7. Retention Policy Strip
  const allSlugs = [...new Set([...donutSlugs, ...Object.keys(ttlByProvider)])];
  const strip = h("div", { class: "card strip mt-4" });
  if (!allSlugs.length) {
    strip.append(h("span", { class: "strip-text" }, "No providers configured yet — retention rules apply once mailboxes are created."));
  } else {
    strip.append(h("span", { class: "strip-text" }, "Retention policies"));
    for (const slug of allSlugs) {
      const r = ttlByProvider[slug];
      strip.append(h("span", { class: `ttl-badge ${!r || (r.mailbox_ttl_hours == null && r.message_ttl_hours == null) ? "is-off" : ""}` },
        h("span", {}, esc(slug)),
        h("b", {}, `box ${ttlText(r?.mailbox_ttl_hours)} · msg ${ttlText(r?.message_ttl_hours)}`)));
    }
    const spacer = h("span", { class: "strip-text" }, "");
    const sweepBtn = h("button", { class: "btn btn-ghost btn-sm", onclick: triggerSweep },
      h("i", { "data-lucide": "timer" }), h("span", {}, "Run retention sweep"));
    strip.append(spacer, sweepBtn);
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
}
