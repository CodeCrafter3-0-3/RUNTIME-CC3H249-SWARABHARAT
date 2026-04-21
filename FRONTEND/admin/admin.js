/******************************************************************
 * SwaraBharat - Admin Intelligence Panel
 * Department station routing + resilient rendering
 ******************************************************************/

const DEFAULT_API_BASE = "https://backend-swarabharat.onrender.com";
const LOCAL_FALLBACK_BASE = "http://localhost:5000";
const STATUS_VALUES = ["Submitted", "Acknowledged", "In Progress", "Resolved"];
const STATIONS = ["Government", "Hospital", "Fire", "Police"];

const API_PATHS = Object.freeze({
  dashboard: "/dashboard",
  reports: "/reports",
  analyze: "/demo_analyze",
  models: "/demo_models",
  status: "/demo_status",
  priority: "/analytics/priority",
  explain: "/analytics/explain_priority",
  updateStatus: "/update_status",
  buildIndex: "/ai/build_index",
  searchSimilar: "/ai/search_similar",
  indexStatus: "/ai/index_status"
});

const state = {
  emotionChart: null,
  issueChart: null,
  map: null,
  markers: [],
  allReports: [],
  filteredReports: [],
  apiBaseInUse: null
};

const tabs = document.querySelectorAll(".nav-btn");
const sections = {
  dashboard: document.getElementById("dashboard"),
  analytics: document.getElementById("analytics"),
  reports: document.getElementById("reports"),
  stations: document.getElementById("stations"),
  ai: document.getElementById("ai")
};

const DOM = {
  liveStatus: document.getElementById("liveStatus"),
  statusDot: document.getElementById("statusDot"),
  lastUpdate: document.getElementById("lastUpdate"),
  totalVoices: document.getElementById("totalVoices"),
  highUrgency: document.getElementById("highUrgency"),
  topIssue: document.getElementById("topIssue"),
  topStation: document.getElementById("topStation"),
  resolvedToday: document.getElementById("resolvedToday"),
  avgResponseTime: document.getElementById("avgResponseTime"),
  resolutionRate: document.getElementById("resolutionRate"),
  satisfaction: document.getElementById("satisfaction"),
  multiDeptCases: document.getElementById("multiDeptCases"),
  refreshCharts: document.getElementById("refreshCharts"),
  reportsTable: document.getElementById("reportsTable"),
  searchInput: document.getElementById("searchInput"),
  urgencyFilter: document.getElementById("urgencyFilter"),
  departmentFilter: document.getElementById("departmentFilter"),
  exportCsv: document.getElementById("exportCsv"),
  setAdminApiBtn: document.getElementById("setAdminApiBtn"),
  trendingIssue: document.getElementById("trendingIssue"),
  alertLevel: document.getElementById("alertLevel"),
  locationCoverage: document.getElementById("locationCoverage"),
  emergencyCount: document.getElementById("emergencyCount"),
  insightsBox: document.getElementById("insightsBox"),
  routingBox: document.getElementById("routingBox"),
  aiMessage: document.getElementById("aiMessage"),
  analyzeBtn: document.getElementById("analyzeBtn"),
  aiResult: document.getElementById("aiResult"),
  aiModel: document.getElementById("aiModel"),
  aiModelStatus: document.getElementById("aiModelStatus"),
  buildIndex: document.getElementById("buildIndex"),
  searchBtn: document.getElementById("searchBtn"),
  searchText: document.getElementById("searchText"),
  searchResults: document.getElementById("searchResults"),
  indexStatus: document.getElementById("indexStatus"),
  stationGovernmentCount: document.getElementById("stationGovernmentCount"),
  stationHospitalCount: document.getElementById("stationHospitalCount"),
  stationFireCount: document.getElementById("stationFireCount"),
  stationPoliceCount: document.getElementById("stationPoliceCount"),
  stationGovernmentMeta: document.getElementById("stationGovernmentMeta"),
  stationHospitalMeta: document.getElementById("stationHospitalMeta"),
  stationFireMeta: document.getElementById("stationFireMeta"),
  stationPoliceMeta: document.getElementById("stationPoliceMeta"),
  stationGovernmentQueue: document.getElementById("stationGovernmentQueue"),
  stationHospitalQueue: document.getElementById("stationHospitalQueue"),
  stationFireQueue: document.getElementById("stationFireQueue"),
  stationPoliceQueue: document.getElementById("stationPoliceQueue")
};

Chart.defaults.color = "#94a3b8";
Chart.defaults.font.family = "'Inter', sans-serif";

function exists(el) {
  return el !== null;
}

function escapeHtml(value) {
  const text = String(value ?? "");
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function readCustomApiBase() {
  return (localStorage.getItem("SWARA_ADMIN_API_BASE") || "").trim();
}

function getApiBases() {
  const bases = [];
  const custom = readCustomApiBase();
  if (custom) bases.push(custom);
  bases.push(DEFAULT_API_BASE);
  if (window.location.protocol !== "file:") bases.push(window.location.origin);
  bases.push(LOCAL_FALLBACK_BASE);
  return [...new Set(bases)];
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function requestJson(path, options = {}) {
  const urls = /^https?:\/\//i.test(path)
    ? [path]
    : getApiBases().map((base) => `${base}${path}`);
  const errors = [];

  for (const url of urls) {
    try {
      const response = await fetchWithTimeout(url, options, 15000);
      let data = null;
      try {
        data = await response.json();
      } catch (_) {
        data = null;
      }
      if (!response.ok) {
        const message = (data && (data.message || data.error)) || `HTTP ${response.status}`;
        throw new Error(message);
      }
      state.apiBaseInUse = url.split(path)[0] || state.apiBaseInUse;
      return data || {};
    } catch (error) {
      errors.push({ url, message: error.message || "Unknown error" });
    }
  }

  const first = errors[0];
  throw new Error(first ? first.message : "API request failed");
}

function parseDate(value) {
  if (!value) return null;
  const t = Date.parse(value);
  return Number.isFinite(t) ? t : null;
}

function formatDate(value) {
  const timestamp = parseDate(value);
  if (!timestamp) return "-";
  return new Date(timestamp).toLocaleString("en-IN", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function parseLocation(rawLocation) {
  if (!rawLocation) return null;

  if (typeof rawLocation === "object" && rawLocation !== null) {
    const lat = Number(rawLocation.latitude);
    const lng = Number(rawLocation.longitude);
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      return {
        latitude: lat,
        longitude: lng,
        label: `${lat.toFixed(4)}, ${lng.toFixed(4)}`
      };
    }
    return null;
  }

  if (typeof rawLocation === "string") {
    const trimmed = rawLocation.trim();
    const match = trimmed.match(/(-?\d+(\.\d+)?)\s*[, ]\s*(-?\d+(\.\d+)?)/);
    if (match) {
      const lat = Number(match[1]);
      const lng = Number(match[3]);
      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        return {
          latitude: lat,
          longitude: lng,
          label: `${lat.toFixed(4)}, ${lng.toFixed(4)}`
        };
      }
    }
    return { latitude: null, longitude: null, label: trimmed };
  }

  return null;
}

function normalizeIssue(issue) {
  const text = String(issue || "Other").trim();
  return text || "Other";
}

function normalizeUrgency(urgency) {
  const clean = String(urgency || "Medium").trim();
  if (["High", "Medium", "Low"].includes(clean)) return clean;
  return "Medium";
}

function normalizeStatus(status) {
  const clean = String(status || "Submitted").trim();
  if (STATUS_VALUES.includes(clean)) return clean;
  return "Submitted";
}

function classifyDepartments(report) {
  const issue = normalizeIssue(report.issue);
  const message = String(report.message || report.text || report.summary || "").toLowerCase();
  const urgency = normalizeUrgency(report.urgency);
  const departments = new Set();

  const fireSignals = ["fire", "smoke", "burn", "gas leak", "explosion"];
  const policeSignals = ["crime", "theft", "fight", "violence", "harassment", "unsafe", "attack"];
  const medicalSignals = ["hospital", "medical", "ambulance", "injury", "injured", "bleeding", "fainted"];

  if (issue === "Health") departments.add("Hospital");
  if (issue === "Safety") departments.add("Police");
  if (issue === "Accident") {
    departments.add("Police");
    departments.add("Hospital");
  }
  if (["Water", "Food", "Education", "Employment", "Other"].includes(issue)) {
    departments.add("Government");
  }

  if (fireSignals.some((signal) => message.includes(signal))) departments.add("Fire");
  if (policeSignals.some((signal) => message.includes(signal))) departments.add("Police");
  if (medicalSignals.some((signal) => message.includes(signal))) departments.add("Hospital");

  if (urgency === "High" && departments.has("Government") && departments.size === 1) {
    departments.add("Police");
  }

  if (!departments.size) departments.add("Government");

  let primary = "Government";
  if (departments.has("Fire")) primary = "Fire";
  else if (departments.has("Hospital") && (issue === "Health" || issue === "Accident")) primary = "Hospital";
  else if (departments.has("Police")) primary = "Police";
  else if (departments.has("Government")) primary = "Government";

  let caseType = "General civic case";
  if (primary === "Fire") caseType = "Fire and rescue case";
  else if (primary === "Hospital") caseType = "Medical response case";
  else if (primary === "Police") caseType = "Public safety case";
  else if (["Water", "Food", "Education", "Employment"].includes(issue)) caseType = "Civic support case";

  return {
    departments: [...departments],
    primaryDepartment: primary,
    caseType
  };
}

function enrichReport(report) {
  const location = parseLocation(report.location);
  const issue = normalizeIssue(report.issue);
  const urgency = normalizeUrgency(report.urgency);
  const status = normalizeStatus(report.status);
  const message = String(report.message || report.text || report.summary || "").trim();
  const id = String(report.id || report.report_id || "-");
  const time = report.time || report.created_at || null;
  const updatedAt = report.updated_at || time;
  const emotion = String(report.emotion || "Calm");
  const emergency = report.emergency ? String(report.emergency) : "";
  const classification = classifyDepartments({ ...report, issue, urgency, message });

  return {
    ...report,
    id,
    issue,
    urgency,
    status,
    message,
    emotion,
    time,
    updated_at: updatedAt,
    emergency,
    locationObj: location,
    departments: classification.departments,
    primaryDepartment: classification.primaryDepartment,
    caseType: classification.caseType,
    timeMs: parseDate(time),
    updatedMs: parseDate(updatedAt)
  };
}

function sortReportsDescending(list) {
  return [...list].sort((a, b) => (b.timeMs || 0) - (a.timeMs || 0));
}

function updateTimestamp() {
  if (!exists(DOM.lastUpdate)) return;
  const now = new Date();
  DOM.lastUpdate.innerHTML = `<i class="fas fa-clock"></i> Last update: ${now.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  })}`;
}

function switchTab(tabName) {
  tabs.forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tabName));
  Object.entries(sections).forEach(([key, section]) => {
    if (!section) return;
    section.classList.toggle("hidden", key !== tabName);
  });
  if (tabName === "dashboard" && state.map) {
    setTimeout(() => state.map.invalidateSize(), 80);
  }
}

tabs.forEach((btn) => {
  btn.addEventListener("click", () => {
    switchTab(btn.dataset.tab);
    if (btn.dataset.tab === "analytics") {
      renderAnalytics();
    }
    if (btn.dataset.tab === "stations") {
      renderStations();
    }
  });
});

function initMap() {
  if (state.map || !document.getElementById("mapContainer") || typeof L === "undefined") return;
  state.map = L.map("mapContainer").setView([20.5937, 78.9629], 4);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: "&copy; CARTO",
    subdomains: "abcd",
    maxZoom: 20
  }).addTo(state.map);
}

function urgencyColor(urgency) {
  if (urgency === "High") return "#ef4444";
  if (urgency === "Low") return "#22c55e";
  return "#f59e0b";
}

function updateMap() {
  if (!document.getElementById("mapContainer")) return;
  initMap();
  if (!state.map) return;

  state.markers.forEach((marker) => state.map.removeLayer(marker));
  state.markers = [];

  const reportsWithCoords = state.allReports.filter(
    (report) => report.locationObj && Number.isFinite(report.locationObj.latitude) && Number.isFinite(report.locationObj.longitude)
  );

  reportsWithCoords.forEach((report) => {
    const lat = report.locationObj.latitude;
    const lng = report.locationObj.longitude;
    const color = urgencyColor(report.urgency);

    const marker = L.circleMarker([lat, lng], {
      radius: report.urgency === "High" ? 9 : 7,
      fillColor: color,
      color: "#ffffff",
      weight: 1,
      opacity: 0.85,
      fillOpacity: 0.85
    }).addTo(state.map);

    const stationTags = report.departments.map((dept) => `<span style="display:inline-block;margin-right:4px;margin-top:4px;padding:2px 6px;border-radius:999px;border:1px solid rgba(37,99,235,0.35);background:#eff6ff;color:#1d4ed8;font-size:10px;">${escapeHtml(dept)}</span>`).join("");
    marker.bindPopup(`
      <div style="font-family: Inter, sans-serif; color:#0f172a; min-width:220px;">
        <strong style="color:#1e3a8a;">${escapeHtml(report.issue)}</strong><br>
        <span style="font-size:12px;">Urgency: <strong style="color:${color};">${escapeHtml(report.urgency)}</strong></span><br>
        <span style="font-size:12px;">Status: ${escapeHtml(report.status)}</span><br>
        <span style="font-size:12px;">Case: ${escapeHtml(report.caseType)}</span>
        <div style="margin-top:6px;">${stationTags}</div>
      </div>
    `);

    state.markers.push(marker);
  });
}

function aggregateByKey(key) {
  const out = {};
  state.allReports.forEach((report) => {
    const value = String(report[key] || "Unknown");
    out[value] = (out[value] || 0) + 1;
  });
  return out;
}

function renderEmotionChart() {
  const canvas = document.getElementById("emotionChart");
  if (!canvas) return;
  const data = aggregateByKey("emotion");
  const labels = Object.keys(data);
  const values = Object.values(data);

  if (state.emotionChart) {
    state.emotionChart.data.labels = labels;
    state.emotionChart.data.datasets[0].data = values;
    state.emotionChart.update();
    return;
  }

  state.emotionChart = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Emotion Count",
        data: values,
        backgroundColor: "rgba(99, 102, 241, 0.82)",
        borderColor: "#6366f1",
        borderWidth: 1,
        borderRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true, grid: { color: "rgba(255,255,255,0.06)" } },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderIssueChart() {
  const canvas = document.getElementById("issueChart");
  if (!canvas) return;

  const data = aggregateByKey("issue");
  const labels = Object.keys(data);
  const values = Object.values(data);

  if (state.issueChart) {
    state.issueChart.data.labels = labels;
    state.issueChart.data.datasets[0].data = values;
    state.issueChart.update();
    return;
  }

  state.issueChart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#0ea5e9", "#a855f7", "#14b8a6", "#ec4899"],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: { position: "right" }
      },
      onClick: (_, elements) => {
        if (!elements.length) return;
        const issue = state.issueChart.data.labels[elements[0].index];
        if (exists(DOM.searchInput)) DOM.searchInput.value = issue;
        switchTab("reports");
        renderReports();
      }
    }
  });
}

function stationCounts() {
  const counts = { Government: 0, Hospital: 0, Fire: 0, Police: 0 };
  state.allReports.forEach((report) => {
    report.departments.forEach((department) => {
      counts[department] = (counts[department] || 0) + 1;
    });
  });
  return counts;
}

function updateHeadlineCards() {
  if (exists(DOM.totalVoices)) DOM.totalVoices.textContent = String(state.allReports.length);
  if (exists(DOM.highUrgency)) {
    DOM.highUrgency.textContent = String(state.allReports.filter((r) => r.urgency === "High").length);
  }

  const issueCounts = aggregateByKey("issue");
  const topIssue = Object.keys(issueCounts).length
    ? Object.keys(issueCounts).reduce((a, b) => (issueCounts[a] > issueCounts[b] ? a : b))
    : "-";
  if (exists(DOM.topIssue)) DOM.topIssue.textContent = topIssue;

  const counts = stationCounts();
  const topStation = Object.keys(counts).reduce((a, b) => (counts[a] > counts[b] ? a : b), "Government");
  if (exists(DOM.topStation)) DOM.topStation.textContent = topStation;
}

function updateMetrics() {
  const reports = state.allReports;
  if (!reports.length) return;

  const today = new Date().toDateString();
  const resolvedToday = reports.filter((report) => report.status === "Resolved" && report.timeMs && new Date(report.timeMs).toDateString() === today).length;
  const totalResolved = reports.filter((report) => report.status === "Resolved").length;
  const resolutionRate = Math.round((totalResolved / reports.length) * 100);
  const multiDeptCases = reports.filter((report) => report.departments.length > 1).length;

  let responseTotalMinutes = 0;
  let responseCount = 0;
  reports.forEach((report) => {
    if (report.updatedMs && report.timeMs && report.updatedMs > report.timeMs && report.status !== "Submitted") {
      const mins = (report.updatedMs - report.timeMs) / (1000 * 60);
      if (mins > 0 && mins < 120000) {
        responseTotalMinutes += mins;
        responseCount += 1;
      }
    }
  });

  let avgResponse = "-";
  if (responseCount > 0) {
    const avg = responseTotalMinutes / responseCount;
    avgResponse = avg < 60 ? `${Math.round(avg)} min` : `${(avg / 60).toFixed(1)} hrs`;
  }

  let satisfaction = "-";
  if (reports.length > 0) {
    const score = Math.min(5, 2.9 + resolutionRate * 0.018 + Math.min(multiDeptCases / 8, 0.7));
    satisfaction = `${score.toFixed(1)}/5`;
  }

  if (exists(DOM.resolvedToday)) DOM.resolvedToday.textContent = String(resolvedToday);
  if (exists(DOM.avgResponseTime)) DOM.avgResponseTime.textContent = avgResponse;
  if (exists(DOM.resolutionRate)) DOM.resolutionRate.textContent = `${resolutionRate}%`;
  if (exists(DOM.satisfaction)) DOM.satisfaction.textContent = satisfaction;
  if (exists(DOM.multiDeptCases)) DOM.multiDeptCases.textContent = String(multiDeptCases);
}

function getFilteredReports() {
  let result = [...state.allReports];

  if (exists(DOM.searchInput) && DOM.searchInput.value.trim()) {
    const query = DOM.searchInput.value.trim().toLowerCase();
    result = result.filter((report) => {
      const haystack = [
        report.id,
        report.issue,
        report.urgency,
        report.status,
        report.message,
        report.caseType,
        report.departments.join(" ")
      ].join(" ").toLowerCase();
      return haystack.includes(query);
    });
  }

  if (exists(DOM.urgencyFilter) && DOM.urgencyFilter.value !== "ALL") {
    result = result.filter((report) => report.urgency === DOM.urgencyFilter.value);
  }

  if (exists(DOM.departmentFilter) && DOM.departmentFilter.value !== "ALL") {
    const selected = DOM.departmentFilter.value;
    result = result.filter((report) => report.departments.includes(selected));
  }

  state.filteredReports = result;
  return result;
}

function urgencyPill(urgency) {
  const cls = urgency === "High" ? "high" : urgency === "Low" ? "low" : "medium";
  return `<span class="pill ${cls}">${escapeHtml(urgency)}</span>`;
}

function statusPill(status) {
  return `<span class="pill status">${escapeHtml(status)}</span>`;
}

function departmentPills(report) {
  return report.departments.map((dept) => `<span class="pill dept">${escapeHtml(dept)}</span>`).join("");
}

function renderReports() {
  if (!exists(DOM.reportsTable)) return;
  const rows = getFilteredReports();

  let html = `
    <table>
      <thead>
        <tr>
          <th style="width:90px;">ID</th>
          <th style="width:160px;">Time</th>
          <th style="width:280px;">Message</th>
          <th>Issue</th>
          <th>Urgency</th>
          <th>Status</th>
          <th style="width:160px;">Stations</th>
          <th style="width:150px;">Location</th>
          <th style="width:200px;">Actions</th>
        </tr>
      </thead>
      <tbody>
  `;

  rows.forEach((report) => {
    const encodedId = encodeURIComponent(report.id);
    const locationText = report.locationObj ? escapeHtml(report.locationObj.label) : "-";
    const canMap = report.locationObj && Number.isFinite(report.locationObj.latitude) && Number.isFinite(report.locationObj.longitude);
    const message = report.message || report.summary || "-";

    html += `
      <tr>
        <td><span style="font-size:11px; opacity:0.78;">${escapeHtml(report.id)}</span></td>
        <td style="font-size:12px;">${escapeHtml(formatDate(report.time))}</td>
        <td><div class="td-msg" title="${escapeHtml(message)}">${escapeHtml(message)}</div></td>
        <td>${escapeHtml(report.issue)}</td>
        <td>${urgencyPill(report.urgency)}</td>
        <td>${statusPill(report.status)}</td>
        <td>${departmentPills(report)}</td>
        <td>
          <div style="display:flex; flex-direction:column; gap:6px;">
            <span style="font-size:12px;">${locationText}</span>
            ${canMap ? `<button class="small-btn map-btn" data-id="${encodedId}" type="button"><i class="fas fa-map-marker-alt"></i> Focus</button>` : ""}
          </div>
        </td>
        <td>
          <div style="display:grid; gap:6px;">
            <select class="status-select" data-id="${encodedId}" style="font-size:11px; padding:6px;">
              ${STATUS_VALUES.map((value) => `<option value="${value}" ${report.status === value ? "selected" : ""}>${value}</option>`).join("")}
            </select>
            <button class="primary explain-btn" data-id="${encodedId}" type="button" style="font-size:11px; padding:7px 10px;">Explain</button>
          </div>
        </td>
      </tr>
    `;
  });

  html += "</tbody></table>";

  if (!rows.length) {
    html = '<div class="station-empty">No reports match the selected filters.</div>';
  }

  DOM.reportsTable.innerHTML = html;
}

function renderStationQueueTable(reports) {
  if (!reports.length) {
    return '<div class="station-empty">No active cases in this station queue.</div>';
  }

  const rows = reports.slice(0, 40).map((report) => {
    const encodedId = encodeURIComponent(report.id);
    return `
      <tr>
        <td style="font-size:11px;">${escapeHtml(report.id)}</td>
        <td>${escapeHtml(report.issue)}</td>
        <td>${urgencyPill(report.urgency)}</td>
        <td>${statusPill(report.status)}</td>
        <td>
          <button class="small-btn station-view-btn" data-id="${encodedId}" type="button" style="font-size:11px; padding:5px 8px;">View</button>
        </td>
      </tr>
    `;
  }).join("");

  return `
    <table>
      <thead>
        <tr>
          <th style="width:90px;">ID</th>
          <th>Issue</th>
          <th>Urgency</th>
          <th>Status</th>
          <th style="width:80px;">Open</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderStations() {
  const byStation = {
    Government: [],
    Hospital: [],
    Fire: [],
    Police: []
  };

  state.allReports.forEach((report) => {
    report.departments.forEach((department) => {
      if (byStation[department]) byStation[department].push(report);
    });
  });

  STATIONS.forEach((station) => {
    byStation[station] = sortReportsDescending(byStation[station]);
  });

  if (exists(DOM.stationGovernmentCount)) DOM.stationGovernmentCount.textContent = String(byStation.Government.length);
  if (exists(DOM.stationHospitalCount)) DOM.stationHospitalCount.textContent = String(byStation.Hospital.length);
  if (exists(DOM.stationFireCount)) DOM.stationFireCount.textContent = String(byStation.Fire.length);
  if (exists(DOM.stationPoliceCount)) DOM.stationPoliceCount.textContent = String(byStation.Police.length);

  if (exists(DOM.stationGovernmentMeta)) DOM.stationGovernmentMeta.textContent = `${byStation.Government.filter((r) => r.status !== "Resolved").length} active`;
  if (exists(DOM.stationHospitalMeta)) DOM.stationHospitalMeta.textContent = `${byStation.Hospital.filter((r) => r.status !== "Resolved").length} active`;
  if (exists(DOM.stationFireMeta)) DOM.stationFireMeta.textContent = `${byStation.Fire.filter((r) => r.status !== "Resolved").length} active`;
  if (exists(DOM.stationPoliceMeta)) DOM.stationPoliceMeta.textContent = `${byStation.Police.filter((r) => r.status !== "Resolved").length} active`;

  if (exists(DOM.stationGovernmentQueue)) DOM.stationGovernmentQueue.innerHTML = renderStationQueueTable(byStation.Government);
  if (exists(DOM.stationHospitalQueue)) DOM.stationHospitalQueue.innerHTML = renderStationQueueTable(byStation.Hospital);
  if (exists(DOM.stationFireQueue)) DOM.stationFireQueue.innerHTML = renderStationQueueTable(byStation.Fire);
  if (exists(DOM.stationPoliceQueue)) DOM.stationPoliceQueue.innerHTML = renderStationQueueTable(byStation.Police);
}

function renderAnalytics() {
  const now = Date.now();
  const dayAgo = now - 24 * 60 * 60 * 1000;
  const last24h = state.allReports.filter((report) => report.timeMs && report.timeMs >= dayAgo);
  const issueCounts = {};
  last24h.forEach((report) => {
    issueCounts[report.issue] = (issueCounts[report.issue] || 0) + 1;
  });

  const trending = Object.keys(issueCounts).length
    ? Object.keys(issueCounts).reduce((a, b) => (issueCounts[a] > issueCounts[b] ? a : b))
    : "-";
  const high24 = last24h.filter((report) => report.urgency === "High").length;
  const critical = last24h.length > 0 && high24 / last24h.length > 0.3;
  const withLocation = state.allReports.filter((report) => report.locationObj && Number.isFinite(report.locationObj.latitude)).length;
  const coverage = state.allReports.length ? Math.round((withLocation / state.allReports.length) * 100) : 0;
  const emergency = state.allReports.filter((report) => report.emergency).length;

  if (exists(DOM.trendingIssue)) DOM.trendingIssue.textContent = trending;
  if (exists(DOM.alertLevel)) {
    DOM.alertLevel.textContent = critical ? "CRITICAL" : "NORMAL";
    DOM.alertLevel.style.color = critical ? "#ef4444" : "#22c55e";
  }
  if (exists(DOM.locationCoverage)) DOM.locationCoverage.textContent = `${coverage}%`;
  if (exists(DOM.emergencyCount)) DOM.emergencyCount.textContent = String(emergency);

  const counts = stationCounts();
  const sortedStations = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const busiest = sortedStations[0] || ["Government", 0];
  const second = sortedStations[1] || ["Hospital", 0];

  if (exists(DOM.insightsBox)) {
    DOM.insightsBox.innerHTML = `
      <p><strong>Total Reports:</strong> ${state.allReports.length}</p>
      <p><strong>24h Incoming:</strong> ${last24h.length}</p>
      <p><strong>High Urgency (24h):</strong> ${high24}</p>
      <p style="margin-top:10px; color:#93c5fd;"><i class="fas fa-magic"></i> Recommendation: prioritize ${escapeHtml(busiest[0])} station, then ${escapeHtml(second[0])} station.</p>
    `;
  }

  if (exists(DOM.routingBox)) {
    DOM.routingBox.innerHTML = `
      <p><strong>Primary dispatch:</strong> ${escapeHtml(busiest[0])} (${busiest[1]} cases)</p>
      <p><strong>Secondary support:</strong> ${escapeHtml(second[0])} (${second[1]} cases)</p>
      <p><strong>Multi-department load:</strong> ${state.allReports.filter((r) => r.departments.length > 1).length} cases</p>
    `;
  }
}

function updateDashboardFromApi(data) {
  if (!data || typeof data !== "object") return;
  if (exists(DOM.totalVoices) && Number.isFinite(Number(data.totalVoices))) {
    DOM.totalVoices.textContent = String(data.totalVoices);
  }
  if (exists(DOM.highUrgency) && Number.isFinite(Number(data.highUrgency))) {
    DOM.highUrgency.textContent = String(data.highUrgency);
  }
  if (exists(DOM.topIssue) && data.topIssue) {
    DOM.topIssue.textContent = String(data.topIssue);
  }
}

async function loadDashboard() {
  try {
    const dashboard = await requestJson(API_PATHS.dashboard);
    updateDashboardFromApi(dashboard);
  } catch (_) {
    // fallback handled by local aggregation
  }
  updateHeadlineCards();
}

async function loadReports() {
  try {
    const response = await requestJson(API_PATHS.reports);
    const reports = Array.isArray(response.reports) ? response.reports : [];
    state.allReports = sortReportsDescending(reports.map(enrichReport));
    state.filteredReports = [...state.allReports];

    renderReports();
    renderStations();
    updateMap();
    updateHeadlineCards();
    updateMetrics();
    renderAnalytics();
    renderEmotionChart();
    renderIssueChart();
  } catch (error) {
    console.error("Failed to load reports", error);
    if (exists(DOM.reportsTable) && !state.allReports.length) {
      DOM.reportsTable.innerHTML = `<div class="station-empty">Could not load reports: ${escapeHtml(error.message)}</div>`;
    }
  }
}

async function checkStatus() {
  try {
    const data = await requestJson(API_PATHS.status);
    const live = Boolean(data.ai_live);
    const provider = data.ai_provider || "unknown";
    if (exists(DOM.liveStatus)) DOM.liveStatus.textContent = live ? `AI Live (${provider})` : "AI Offline";
    if (exists(DOM.statusDot)) {
      DOM.statusDot.style.background = live ? "#22c55e" : "#ef4444";
      DOM.statusDot.style.boxShadow = live ? "0 0 10px #22c55e" : "0 0 10px #ef4444";
    }
    if (exists(DOM.liveStatus)) DOM.liveStatus.className = live ? "status-online" : "status-offline";
  } catch (_) {
    if (exists(DOM.liveStatus)) {
      DOM.liveStatus.textContent = "Offline (Connection Error)";
      DOM.liveStatus.className = "status-offline";
    }
    if (exists(DOM.statusDot)) {
      DOM.statusDot.style.background = "#ef4444";
      DOM.statusDot.style.boxShadow = "0 0 10px #ef4444";
    }
  }
}

function collectCsvRows() {
  const rows = getFilteredReports();
  const header = "ID,Time,Message,Issue,Emotion,Urgency,Status,Stations,CaseType,Location,Emergency,Summary";
  const lines = rows.map((report) => {
    const location = report.locationObj ? report.locationObj.label : "-";
    const safe = (value) => String(value || "-").replace(/"/g, '""');
    return [
      safe(report.id),
      safe(report.time),
      safe(report.message || report.summary),
      safe(report.issue),
      safe(report.emotion),
      safe(report.urgency),
      safe(report.status),
      safe(report.departments.join("|")),
      safe(report.caseType),
      safe(location),
      safe(report.emergency || "-"),
      safe(report.summary || "-")
    ].map((cell) => `"${cell}"`).join(",");
  });
  return [header, ...lines].join("\n");
}

function exportCsv() {
  const csv = collectCsvRows();
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `swarabharat_reports_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
}

function findReportById(reportId) {
  return state.allReports.find((report) => report.id === reportId) || null;
}

function focusMap(report) {
  if (!report || !report.locationObj) return;
  if (!Number.isFinite(report.locationObj.latitude) || !Number.isFinite(report.locationObj.longitude)) return;

  switchTab("dashboard");
  if (!state.map) initMap();
  if (!state.map) return;

  setTimeout(() => {
    state.map.invalidateSize();
    state.map.setView([report.locationObj.latitude, report.locationObj.longitude], 13);
  }, 80);
}

async function updateStatus(reportId, newStatus) {
  if (!reportId || !newStatus) return;
  try {
    await requestJson(`${API_PATHS.updateStatus}/${encodeURIComponent(reportId)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    await loadReports();
    await loadDashboard();
  } catch (error) {
    window.alert(`Could not update status: ${error.message}`);
  }
}

async function showExplanation(reportId) {
  const report = findReportById(reportId);
  if (!report) return;

  try {
    const data = await requestJson(`${API_PATHS.explain}?report_id=${encodeURIComponent(reportId)}`);
    if (data && data.status === "success" && data.explanation) {
      const explanation = data.explanation;
      const details = Array.isArray(explanation.details)
        ? explanation.details.map((item) => `${item.factor}: ${item.value} (+${item.points})`).join("\n")
        : "No factor details";
      window.alert(
        `Priority explanation for ${reportId}\n\n` +
        `Base score: ${explanation.base_score}\n` +
        `Final score: ${explanation.final_score}\n\n` +
        `Factors:\n${details}`
      );
      return;
    }
  } catch (_) {
    // local fallback below
  }

  window.alert(
    `Local classification for ${reportId}\n\n` +
    `Case type: ${report.caseType}\n` +
    `Primary station: ${report.primaryDepartment}\n` +
    `Routed stations: ${report.departments.join(", ")}\n` +
    `Urgency: ${report.urgency}`
  );
}

async function loadAiModels() {
  if (!exists(DOM.aiModel)) return;

  try {
    const data = await requestJson(API_PATHS.models);
    const models = Array.isArray(data.models) ? data.models : [];
    if (!models.length) {
      DOM.aiModel.innerHTML = '<option value="heuristic">Heuristic Fast Classifier</option>';
      if (exists(DOM.aiModelStatus)) DOM.aiModelStatus.textContent = "Model catalog unavailable. Using heuristic fallback.";
      return;
    }

    DOM.aiModel.innerHTML = models.map((model) => {
      const id = model.id || "heuristic";
      const label = model.label || id;
      const enabled = Boolean(model.enabled);
      return `<option value="${escapeHtml(id)}" ${enabled ? "" : "disabled"}>${escapeHtml(label)}${enabled ? "" : " (offline)"}</option>`;
    }).join("");

    const preferred = data.default_model || (models.find((model) => model.default && model.enabled) || {}).id;
    const fallback = (models.find((model) => model.enabled) || models[0] || {}).id;
    DOM.aiModel.value = preferred || fallback || "heuristic";

    const liveCount = models.filter((model) => model.enabled && model.provider !== "heuristic").length;
    if (exists(DOM.aiModelStatus)) {
      DOM.aiModelStatus.textContent = `Model catalog loaded: ${models.length} choices (${liveCount} live cloud models).`;
    }
  } catch (error) {
    DOM.aiModel.innerHTML = '<option value="heuristic">Heuristic Fast Classifier</option>';
    if (exists(DOM.aiModelStatus)) DOM.aiModelStatus.textContent = `Model catalog fetch failed: ${error.message}`;
  }
}

async function analyzeAiMessage() {
  if (!exists(DOM.aiMessage) || !exists(DOM.aiResult)) return;
  const message = DOM.aiMessage.value.trim();
  if (!message) return;

  const model = exists(DOM.aiModel) ? DOM.aiModel.value : "";
  DOM.aiResult.textContent = "Analyzing...";

  try {
    const data = await requestJson(API_PATHS.analyze, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, model })
    });
    const usedModel = data.analysis && data.analysis.model ? data.analysis.model : model || "heuristic";
    DOM.aiResult.innerHTML = `
      <div style="font-family:Inter,sans-serif; color:#93c5fd; margin-bottom:10px; font-size:12px;">
        Model used: <strong>${escapeHtml(usedModel)}</strong>
      </div>
      <pre style="margin:0; white-space:pre-wrap;">${escapeHtml(JSON.stringify(data.analysis || {}, null, 2))}</pre>
    `;
  } catch (error) {
    DOM.aiResult.innerHTML = `<div style="color:#fecaca; font-family:Inter,sans-serif;">AI analysis failed: ${escapeHtml(error.message)}</div>`;
  }
}

async function buildIndex() {
  if (!exists(DOM.indexStatus)) return;
  DOM.indexStatus.textContent = "Index status: building...";
  try {
    const data = await requestJson(API_PATHS.buildIndex, { method: "POST" });
    DOM.indexStatus.textContent = `Index status: ${data.status || "unknown"}`;
    await refreshIndexStatus();
  } catch (error) {
    DOM.indexStatus.textContent = `Index status: build failed (${error.message})`;
  }
}

async function searchSimilar() {
  if (!exists(DOM.searchText) || !exists(DOM.searchResults)) return;
  const text = DOM.searchText.value.trim();
  if (!text) return;

  DOM.searchResults.textContent = "Searching...";
  try {
    const data = await requestJson(API_PATHS.searchSimilar, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, top_n: 5 })
    });
    const results = Array.isArray(data.results) ? data.results : [];
    if (!results.length) {
      DOM.searchResults.textContent = "No similar reports found.";
      return;
    }
    DOM.searchResults.innerHTML = results.map((result) => `
      <div style="padding:10px; border-bottom:1px solid rgba(255,255,255,0.05);">
        <strong style="color:#06b6d4;">${escapeHtml(result.id || "-")}</strong>
        <span style="font-size:12px;color:#94a3b8;"> (score: ${Number(result.score || 0).toFixed(3)})</span>
        <div style="font-size:13px; color:#e2e8f0; margin-top:4px;">${escapeHtml(result.snippet || "")}</div>
      </div>
    `).join("");
  } catch (error) {
    DOM.searchResults.textContent = `Search failed: ${error.message}`;
  }
}

async function refreshIndexStatus() {
  if (!exists(DOM.indexStatus)) return;
  try {
    const data = await requestJson(API_PATHS.indexStatus);
    const built = data.index_status && data.index_status.last_built ? data.index_status.last_built : null;
    if (built) {
      DOM.indexStatus.textContent = `Index status: last built ${formatDate(built)}`;
    } else {
      DOM.indexStatus.textContent = "Index status: not built";
    }
  } catch (error) {
    DOM.indexStatus.textContent = `Index status: unavailable (${error.message})`;
  }
}

function bindReportInteractions() {
  if (exists(DOM.reportsTable)) {
    DOM.reportsTable.addEventListener("change", async (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (!target.classList.contains("status-select")) return;
      const reportId = decodeURIComponent(target.getAttribute("data-id") || "");
      const newStatus = target.value;
      await updateStatus(reportId, newStatus);
    });

    DOM.reportsTable.addEventListener("click", async (event) => {
      const node = event.target instanceof HTMLElement ? event.target : null;
      if (!node) return;

      const explainBtn = node.closest(".explain-btn");
      if (explainBtn) {
        const reportId = decodeURIComponent(explainBtn.getAttribute("data-id") || "");
        await showExplanation(reportId);
        return;
      }

      const mapBtn = node.closest(".map-btn");
      if (mapBtn) {
        const reportId = decodeURIComponent(mapBtn.getAttribute("data-id") || "");
        const report = findReportById(reportId);
        focusMap(report);
      }
    });
  }

  const stationContainers = [
    DOM.stationGovernmentQueue,
    DOM.stationHospitalQueue,
    DOM.stationFireQueue,
    DOM.stationPoliceQueue
  ].filter(Boolean);

  stationContainers.forEach((container) => {
    container.addEventListener("click", (event) => {
      const node = event.target instanceof HTMLElement ? event.target : null;
      if (!node) return;
      const viewBtn = node.closest(".station-view-btn");
      if (!viewBtn) return;
      const reportId = decodeURIComponent(viewBtn.getAttribute("data-id") || "");
      const report = findReportById(reportId);
      if (!report) return;
      switchTab("reports");
      if (exists(DOM.searchInput)) DOM.searchInput.value = reportId;
      renderReports();
    });
  });
}

function bindFiltersAndActions() {
  if (exists(DOM.searchInput)) DOM.searchInput.addEventListener("input", renderReports);
  if (exists(DOM.urgencyFilter)) DOM.urgencyFilter.addEventListener("change", renderReports);
  if (exists(DOM.departmentFilter)) DOM.departmentFilter.addEventListener("change", renderReports);
  if (exists(DOM.exportCsv)) DOM.exportCsv.addEventListener("click", exportCsv);

  if (exists(DOM.refreshCharts)) {
    DOM.refreshCharts.addEventListener("click", () => {
      renderEmotionChart();
      renderIssueChart();
      updateMetrics();
    });
  }

  if (exists(DOM.analyzeBtn)) DOM.analyzeBtn.addEventListener("click", analyzeAiMessage);
  if (exists(DOM.buildIndex)) DOM.buildIndex.addEventListener("click", buildIndex);
  if (exists(DOM.searchBtn)) DOM.searchBtn.addEventListener("click", searchSimilar);

  if (exists(DOM.setAdminApiBtn)) {
    DOM.setAdminApiBtn.addEventListener("click", async () => {
      const current = readCustomApiBase();
      const input = window.prompt(
        "Set custom admin API base URL (example: https://your-backend.com). Leave empty to clear.",
        current
      );
      if (input === null) return;

      const next = input.trim();
      if (!next) {
        localStorage.removeItem("SWARA_ADMIN_API_BASE");
        await fullRefresh();
        window.alert("Custom admin API base cleared.");
        return;
      }

      try {
        const url = new URL(next);
        if (!["http:", "https:"].includes(url.protocol)) {
          throw new Error("Only http and https URLs are allowed.");
        }
        localStorage.setItem("SWARA_ADMIN_API_BASE", url.origin);
        await fullRefresh();
        window.alert(`Custom admin API base saved: ${url.origin}`);
      } catch (error) {
        window.alert(`Invalid URL: ${error.message}`);
      }
    });
  }
}

async function fullRefresh() {
  updateTimestamp();
  await Promise.allSettled([loadReports(), loadDashboard(), checkStatus(), refreshIndexStatus()]);
}

async function init() {
  bindReportInteractions();
  bindFiltersAndActions();
  initMap();
  switchTab("dashboard");

  await loadAiModels();
  await fullRefresh();

  setInterval(async () => {
    updateTimestamp();
    try {
      await loadReports();
      await loadDashboard();
    } catch (_) {
      // soft-fail background refresh
    }
  }, 15000);

  setInterval(checkStatus, 30000);
}

init().catch((error) => {
  console.error("Admin init failed", error);
  if (exists(DOM.liveStatus)) DOM.liveStatus.textContent = `Init error: ${error.message}`;
});
