const STATUS_COLORS = {
  replied: "#34d399",
  sent: "#38bdf8",
  pending: "#fbbf24",
  skipped: "#94a3b8",
  failed: "#f87171",
};
const STATUS_LABELS = {
  replied: "Replied",
  sent: "Sent",
  pending: "Pending",
  skipped: "Route-only",
  failed: "Failed",
};

Chart.defaults.color = "#8a95ad";
Chart.defaults.borderColor = "#262f45";
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

let ALL_COMPANIES = [];
const CHARTS = {};

async function loadAndRender() {
  let stats;
  try {
    const res = await fetch(`data/stats.json?ts=${Date.now()}`);
    stats = await res.json();
  } catch (err) {
    document.querySelector("main").innerHTML =
      '<p class="empty">Could not load data/stats.json. Run the pipeline to generate it.</p>';
    return;
  }

  renderHeader(stats);
  renderKpis(stats.kpis);
  renderFunnel(stats.funnel);
  renderLikelihood(stats.by_likelihood);
  renderTimeline(stats.timeline);
  renderAsk(stats.by_best_ask);
  renderCategory(stats.by_category);

  ALL_COMPANIES = stats.companies || [];
  renderTable();
}

function main() {
  loadAndRender();
  document.getElementById("search").addEventListener("input", renderTable);
  document.getElementById("status-filter").addEventListener("change", renderTable);
  document.getElementById("refresh-btn").addEventListener("click", onRefresh);

  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("modal-overlay").addEventListener("click", (e) => {
    if (e.target.id === "modal-overlay") closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  document.querySelector("#company-table tbody").addEventListener("click", (e) => {
    const row = e.target.closest("tr[data-id]");
    if (row) openModal(row.dataset.id);
  });
}

async function onRefresh() {
  const btn = document.getElementById("refresh-btn");
  btn.classList.add("loading");
  await loadAndRender();
  setTimeout(() => btn.classList.remove("loading"), 400);
}

function destroyChart(key) {
  if (CHARTS[key]) {
    CHARTS[key].destroy();
    delete CHARTS[key];
  }
}

function renderHeader(stats) {
  const e = stats.event || {};
  document.getElementById("event-name").textContent = e.name || "Sponsorship Outreach";
  const meta = [e.date, e.venue, e.city].filter(Boolean).join("  •  ");
  document.getElementById("event-meta").textContent = meta;
  if (stats.generated_at) {
    document.getElementById("generated-at").textContent =
      new Date(stats.generated_at).toLocaleString();
  }
}

function kpiCard(value, label, accent) {
  return `<div class="kpi"><div class="value ${accent ? "accent" : ""}">${value}</div>
          <div class="label">${label}</div></div>`;
}

function renderKpis(k) {
  const el = document.getElementById("kpis");
  el.innerHTML = [
    kpiCard(k.total, "Total prospects"),
    kpiCard(k.sent, "Emails sent", true),
    kpiCard(k.replied, "Replies"),
    kpiCard(`${k.reply_rate}%`, "Reply rate"),
    kpiCard(k.pending, "Pending"),
    kpiCard(k.route_only, "Route-only (no email)"),
  ].join("");
}

function renderFunnel(f) {
  if (!f) return;
  const steps = [
    { label: "Prospects", value: f.prospects },
    { label: "Emailable", value: f.emailable },
    { label: "Sent", value: f.sent },
    { label: "Replied", value: f.replied },
  ];
  const max = Math.max(f.prospects, 1);
  const colors = ["#6366f1", "#38bdf8", "#22d3ee", "#34d399"];
  document.getElementById("funnel").innerHTML = steps
    .map((s, i) => {
      const pct = Math.max((s.value / max) * 100, 3);
      return `<div class="funnel-row">
        <div class="funnel-label">${s.label}</div>
        <div class="funnel-bar-track">
          <div class="funnel-bar" style="width:${pct}%;background:${colors[i]}">${s.value}</div>
        </div>
      </div>`;
    })
    .join("");
}

function renderLikelihood(rows) {
  destroyChart("likelihood");
  if (!rows || !rows.length) return;
  CHARTS.likelihood = new Chart(document.getElementById("likelihoodChart"), {
    type: "doughnut",
    data: {
      labels: rows.map((r) => r.label),
      datasets: [{
        data: rows.map((r) => r.total),
        backgroundColor: ["#34d399", "#fbbf24", "#f87171", "#6366f1", "#38bdf8"],
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "right" } },
    },
  });
}

function renderTimeline(timeline) {
  destroyChart("timeline");
  const empty = document.getElementById("timeline-empty");
  if (!timeline || !timeline.length) {
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");
  CHARTS.timeline = new Chart(document.getElementById("timelineChart"), {
    type: "line",
    data: {
      labels: timeline.map((t) => t.date),
      datasets: [
        {
          label: "Sent",
          data: timeline.map((t) => t.sent),
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56,189,248,.15)",
          fill: true,
          tension: 0.3,
        },
        {
          label: "Replies",
          data: timeline.map((t) => t.replies),
          borderColor: "#34d399",
          backgroundColor: "rgba(52,211,153,.15)",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
}

function renderAsk(rows) {
  destroyChart("ask");
  if (!rows || !rows.length) return;
  CHARTS.ask = new Chart(document.getElementById("askChart"), {
    type: "bar",
    data: {
      labels: rows.map((r) => r.label),
      datasets: [{
        label: "Prospects",
        data: rows.map((r) => r.count),
        backgroundColor: "#6366f1",
        borderRadius: 4,
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
}

function renderCategory(rows) {
  destroyChart("category");
  if (!rows || !rows.length) return;
  const statuses = ["replied", "sent", "pending", "skipped", "failed"];
  CHARTS.category = new Chart(document.getElementById("categoryChart"), {
    type: "bar",
    data: {
      labels: rows.map((r) => r.label),
      datasets: statuses.map((s) => ({
        label: STATUS_LABELS[s],
        data: rows.map((r) => r[s] || 0),
        backgroundColor: STATUS_COLORS[s],
        borderRadius: 3,
      })),
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: {
        x: { stacked: true, beginAtZero: true, ticks: { precision: 0 } },
        y: { stacked: true },
      },
    },
  });
}

function renderTable() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const statusFilter = document.getElementById("status-filter").value;
  const tbody = document.querySelector("#company-table tbody");

  const filtered = ALL_COMPANIES.filter((c) => {
    if (statusFilter && c.status !== statusFilter) return false;
    if (q && !c.company.toLowerCase().includes(q)) return false;
    return true;
  });

  tbody.innerHTML = filtered
    .map((c) => {
      const route = c.status === "skipped"
        ? escapeHtml([c.contact_route, c.phone].filter((v) => v && v !== "Not listed").join(" · ") || "See source")
        : escapeHtml(c.email || "—");
      return `<tr data-id="${escapeHtml(c.id)}">
        <td>${escapeHtml(c.company)}</td>
        <td>${escapeHtml(c.category)}</td>
        <td>${escapeHtml(c.likelihood)}</td>
        <td><span class="badge ${c.status}">${STATUS_LABELS[c.status] || c.status}</span></td>
        <td>${route}</td>
      </tr>`;
    })
    .join("");

  document.getElementById("table-count").textContent =
    `Showing ${filtered.length} of ${ALL_COMPANIES.length} prospects · click a row for details`;
}

function row(label, value) {
  if (!value && value !== 0) return "";
  return `<dt>${escapeHtml(label)}</dt><dd>${value}</dd>`;
}

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d) ? iso : d.toLocaleString();
}

function openModal(id) {
  const c = ALL_COMPANIES.find((x) => x.id === id);
  if (!c) return;

  const emailTarget = c.email
    ? `<a href="mailto:${escapeHtml(c.email)}">${escapeHtml(c.email)}</a>`
    : '<span class="muted">No public email (route-only)</span>';

  let outreach = "";
  if (c.status === "sent" || c.status === "replied" || c.status === "failed") {
    outreach = `
      <div class="detail-section-title">Email</div>
      <dl class="detail-grid">
        ${row("Subject", escapeHtml(c.subject) || "—")}
        ${row("Sent at", fmtDate(c.sent_at) || "—")}
        ${row("Message-ID", c.message_id ? `<code>${escapeHtml(c.message_id)}</code>` : "—")}
        ${c.send_reason ? row("Note", escapeHtml(c.send_reason)) : ""}
      </dl>`;
  } else if (c.status === "skipped") {
    outreach = `
      <div class="detail-section-title">How to reach them</div>
      <dl class="detail-grid">
        ${row("Best route", escapeHtml(c.contact_route) || "—")}
        ${row("Phone", escapeHtml(c.phone) || "—")}
        ${row("Source", c.source_url ? `<a href="${escapeHtml(c.source_url)}" target="_blank" rel="noopener">${escapeHtml(c.source_url)}</a>` : "—")}
        ${c.routing_notes ? row("Notes", escapeHtml(c.routing_notes)) : ""}
      </dl>`;
  } else {
    outreach = `
      <div class="detail-section-title">Email</div>
      <p class="muted" style="font-size:13px;margin:0;">Not sent yet. This company is queued and will be emailed at ${escapeHtml(c.email)}.</p>`;
  }

  let reply = "";
  if (c.status === "replied") {
    reply = `
      <div class="detail-section-title">Reply</div>
      <dl class="detail-grid">
        ${row("Replies", c.reply_count || 1)}
        ${row("From", escapeHtml(c.reply_from) || "—")}
        ${row("Subject", escapeHtml(c.reply_subject) || "—")}
        ${row("First reply", fmtDate(c.reply_at) || "—")}
      </dl>`;
  }

  document.getElementById("modal-content").innerHTML = `
    <h3>${escapeHtml(c.company)}</h3>
    <div class="sub">
      <span class="badge ${c.status}">${STATUS_LABELS[c.status] || c.status}</span>
      ${c.parent_company ? " · " + escapeHtml(c.parent_company) : ""}
    </div>

    <div class="detail-section-title">Company</div>
    <dl class="detail-grid">
      ${row("Category", escapeHtml(c.category))}
      ${row("Likelihood", escapeHtml(c.likelihood))}
      ${row("Brands", escapeHtml(c.brands))}
      ${row("Best ask", escapeHtml(c.best_ask))}
      ${row("Contact", emailTarget)}
    </dl>

    ${outreach}
    ${reply}
  `;
  document.getElementById("modal-overlay").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("modal-overlay").classList.add("hidden");
}

function escapeHtml(str) {
  return String(str || "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

main();
