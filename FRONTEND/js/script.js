/**
 * SwaraBharat Frontend Foundation
 * Stable citizen reporting flow with real-time context and routing preview
 */

const CONFIG = Object.freeze({
  API_SUBMIT: "https://backend-swarabharat.onrender.com/submit",
  API_SUBMIT_FALLBACK: "http://localhost:5000/submit",
  WEATHER_API: "https://api.open-meteo.com/v1/forecast",
  REQUEST_TIMEOUT: 60000,
  WEATHER_TIMEOUT: 8000,
  MIN_TEXT_LENGTH: 3,
  STATUS_AUTO_CLEAR: 6000,
  MAX_ERROR_LOGS: 50,
  VERSION: "1.2.0"
});

const ISSUE_KEYWORDS = Object.freeze({
  Accident: ["accident", "crash", "collision", "injury", "hit", "road crash"],
  Health: ["hospital", "ambulance", "medical", "doctor", "sick", "injured", "blood", "death"],
  Safety: ["crime", "theft", "fight", "unsafe", "violence", "attack", "harassment"],
  Water: ["water", "drinking water", "tap", "contaminated", "sewage", "drainage"],
  Food: ["food", "hunger", "ration", "starving", "meal"],
  Education: ["school", "teacher", "classroom", "student", "education"],
  Employment: ["job", "unemployment", "salary", "work", "livelihood"]
});

const WEATHER_CODES = Object.freeze({
  0: "Clear",
  1: "Mostly clear",
  2: "Partly cloudy",
  3: "Cloudy",
  45: "Fog",
  48: "Fog",
  51: "Light drizzle",
  53: "Drizzle",
  55: "Dense drizzle",
  61: "Light rain",
  63: "Rain",
  65: "Heavy rain",
  71: "Light snow",
  73: "Snow",
  75: "Heavy snow",
  80: "Rain showers",
  81: "Rain showers",
  82: "Violent rain showers",
  95: "Thunderstorm"
});

const State = {
  isListening: false,
  isSubmitting: false,
  recognition: null,
  sessionId: crypto.randomUUID(),
  location: null,
  locationWatchId: null,
  weather: null,
  photoData: null,
  lastClassification: {
    issue: "Other",
    urgency: "Medium",
    departments: ["Government"],
    caseType: "General civic case",
    reason: "Waiting for report details"
  }
};

const DOM = {
  input: document.getElementById("input"),
  manualIssue: document.getElementById("manualIssue"),
  status: document.getElementById("status"),
  speakBtn: document.getElementById("speakBtn"),
  submitBtn: document.getElementById("submitBtn"),
  emergency: document.getElementById("emergency"),
  locationText: document.getElementById("locationText"),
  locationMeta: document.getElementById("locationMeta"),
  photoUpload: document.getElementById("photoUpload"),
  photoPreview: document.getElementById("photoPreview"),
  syncInfo: document.getElementById("syncInfo"),
  configApiBtn: document.getElementById("configApiBtn"),
  clockValue: document.getElementById("clockValue"),
  networkValue: document.getElementById("networkValue"),
  weatherValue: document.getElementById("weatherValue"),
  classificationPreview: document.getElementById("classificationPreview")
};

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

function normalizeText(value) {
  return String(value || "").trim();
}

const Status = {
  show(text, type = "") {
    if (!exists(DOM.status)) return;
    DOM.status.textContent = text;
    DOM.status.className = type;
    DOM.status.style.display = "block";
  },

  clear(delay = 0) {
    if (!exists(DOM.status)) return;
    if (delay > 0) {
      setTimeout(() => this.clear(), delay);
      return;
    }
    DOM.status.textContent = "";
    DOM.status.className = "";
    DOM.status.style.display = "none";
  }
};

const Telemetry = {
  emit(event, meta = {}) {
    const payload = {
      event,
      meta,
      time: new Date().toISOString(),
      sessionId: State.sessionId,
      version: CONFIG.VERSION
    };
    console.debug("[Telemetry]", payload);
  }
};

const ErrorReporter = {
  store(error) {
    try {
      const logs = JSON.parse(localStorage.getItem("__swara_errors__") || "[]");
      logs.push({
        id: crypto.randomUUID(),
        time: new Date().toISOString(),
        sessionId: State.sessionId,
        message: error.message || "Unknown error",
        stack: error.stack || null,
        type: error.type || "runtime"
      });
      localStorage.setItem("__swara_errors__", JSON.stringify(logs.slice(-CONFIG.MAX_ERROR_LOGS)));
      console.error("[Swara Error]", error);
    } catch (_) {
      // ignore storage failures
    }
  },

  getAll() {
    try {
      return JSON.parse(localStorage.getItem("__swara_errors__") || "[]");
    } catch (_) {
      return [];
    }
  },

  clear() {
    localStorage.removeItem("__swara_errors__");
  }
};

window.addEventListener("error", (e) => {
  ErrorReporter.store({
    message: e.message,
    stack: e.error && e.error.stack,
    type: "js_error"
  });
});

window.addEventListener("unhandledrejection", (e) => {
  ErrorReporter.store({
    message: (e.reason && e.reason.message) || "Unhandled rejection",
    stack: e.reason && e.reason.stack,
    type: "promise_rejection"
  });
});

function detectIssue(text, manualIssue) {
  if (manualIssue) return manualIssue;
  const lower = text.toLowerCase();

  for (const [issue, keywords] of Object.entries(ISSUE_KEYWORDS)) {
    if (keywords.some((keyword) => lower.includes(keyword))) {
      return issue;
    }
  }

  return "Other";
}

function detectUrgency(text, issue) {
  const lower = text.toLowerCase();
  const highSignals = [
    "urgent",
    "emergency",
    "immediately",
    "help now",
    "critical",
    "fire",
    "trapped",
    "dying",
    "severe"
  ];
  const mediumSignals = ["soon", "unsafe", "shortage", "not working", "broken", "problem"];

  if (highSignals.some((signal) => lower.includes(signal))) return "High";
  if (["Accident", "Health"].includes(issue) && lower.length > 8) return "High";
  if (mediumSignals.some((signal) => lower.includes(signal))) return "Medium";
  return "Low";
}

function routeDepartments(issue, text, urgency) {
  const lower = text.toLowerCase();
  const departments = new Set();

  const fireSignals = ["fire", "smoke", "burn", "gas leak", "explosion"];
  const policeSignals = ["crime", "theft", "assault", "fight", "violence", "harassment", "unsafe"];
  const medicalSignals = ["injury", "injured", "hospital", "ambulance", "medical", "bleeding", "fainted"];

  if (issue === "Health") departments.add("Hospital");
  if (issue === "Safety") departments.add("Police");
  if (issue === "Accident") {
    departments.add("Police");
    departments.add("Hospital");
  }
  if (["Water", "Food", "Education", "Employment", "Other"].includes(issue)) {
    departments.add("Government");
  }

  if (fireSignals.some((signal) => lower.includes(signal))) {
    departments.add("Fire");
  }
  if (policeSignals.some((signal) => lower.includes(signal))) {
    departments.add("Police");
  }
  if (medicalSignals.some((signal) => lower.includes(signal))) {
    departments.add("Hospital");
  }

  if (urgency === "High" && departments.has("Government") && departments.size === 1) {
    departments.add("Police");
  }

  if (!departments.size) departments.add("Government");

  return [...departments];
}

function detectCaseType(issue, departments) {
  if (departments.includes("Fire")) return "Fire and rescue case";
  if (issue === "Health") return "Medical response case";
  if (issue === "Accident") return "Accident response case";
  if (issue === "Safety") return "Public safety case";
  if (["Water", "Food", "Education", "Employment"].includes(issue)) return "Civic support case";
  return "General civic case";
}

function classifyCase(text, manualIssue = "") {
  const cleanText = normalizeText(text);
  const issue = detectIssue(cleanText, manualIssue);
  const urgency = cleanText.length < CONFIG.MIN_TEXT_LENGTH ? "Medium" : detectUrgency(cleanText, issue);
  const departments = routeDepartments(issue, cleanText, urgency);
  const caseType = detectCaseType(issue, departments);

  let reason = "Auto-routed by issue category";
  if (manualIssue) reason = "Manual issue type selected by citizen";
  else if (departments.includes("Fire")) reason = "Fire or smoke keywords detected";
  else if (issue === "Accident") reason = "Accident signals detected in report";

  return { issue, urgency, departments, caseType, reason };
}

function urgencyClass(urgency) {
  if (urgency === "High") return "high";
  if (urgency === "Low") return "low";
  return "medium";
}

function renderClassificationPreview() {
  if (!exists(DOM.classificationPreview)) return;

  const text = exists(DOM.input) ? DOM.input.value : "";
  const manualIssue = exists(DOM.manualIssue) ? DOM.manualIssue.value : "";
  const classification = classifyCase(text, manualIssue);
  State.lastClassification = classification;

  const departmentsHtml = classification.departments
    .map((dept) => `<span class="badge dept">${escapeHtml(dept)}</span>`)
    .join("");

  DOM.classificationPreview.innerHTML = [
    `<div class="classification-item"><span>Case type</span><span>${escapeHtml(classification.caseType)}</span></div>`,
    `<div class="classification-item"><span>Issue class</span><span>${escapeHtml(classification.issue)}</span></div>`,
    `<div class="classification-item"><span>Urgency</span><span class="badge ${urgencyClass(classification.urgency)}">${escapeHtml(classification.urgency)}</span></div>`,
    `<div class="classification-item"><span>Routed stations</span><span class="badge-row">${departmentsHtml}</span></div>`,
    `<div class="classification-item"><span>Routing logic</span><span>${escapeHtml(classification.reason)}</span></div>`
  ].join("");
}

const Realtime = {
  initClock() {
    if (!exists(DOM.clockValue)) return;

    const refresh = () => {
      const now = new Date();
      const time = now.toLocaleString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        day: "2-digit",
        month: "short"
      });
      DOM.clockValue.innerHTML = `<i class="fas fa-clock"></i> ${escapeHtml(time)}`;
    };

    refresh();
    setInterval(refresh, 1000);
  },

  refreshNetwork() {
    if (!exists(DOM.networkValue)) return;

    const isOnline = navigator.onLine;
    const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    const quality = conn && conn.effectiveType ? ` (${conn.effectiveType})` : "";
    const text = isOnline ? `Online${quality}` : "Offline";
    const icon = isOnline ? "fa-signal" : "fa-plug-circle-xmark";

    DOM.networkValue.innerHTML = `<i class="fas ${icon}"></i> ${escapeHtml(text)}`;
  },

  initNetwork() {
    this.refreshNetwork();
    window.addEventListener("online", () => this.refreshNetwork());
    window.addEventListener("offline", () => this.refreshNetwork());
    const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (conn && typeof conn.addEventListener === "function") {
      conn.addEventListener("change", () => this.refreshNetwork());
    }
  }
};

async function fetchWithTimeout(url, options = {}, timeoutMs = CONFIG.REQUEST_TIMEOUT) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

const Weather = {
  async update(lat, lng) {
    if (!exists(DOM.weatherValue)) return;

    try {
      const query = `${CONFIG.WEATHER_API}?latitude=${encodeURIComponent(lat)}&longitude=${encodeURIComponent(lng)}&current=temperature_2m,weather_code,wind_speed_10m`;
      const res = await fetchWithTimeout(query, { method: "GET" }, CONFIG.WEATHER_TIMEOUT);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      const current = data && data.current ? data.current : null;
      if (!current) {
        throw new Error("Missing weather data");
      }

      const code = Number(current.weather_code);
      const condition = WEATHER_CODES[code] || "Unknown";
      const temp = Number(current.temperature_2m);
      const wind = Number(current.wind_speed_10m);

      const text = `${condition}, ${Number.isFinite(temp) ? `${temp}C` : "-"}, wind ${Number.isFinite(wind) ? `${wind} km/h` : "-"}`;
      DOM.weatherValue.innerHTML = `<i class="fas fa-cloud"></i> ${escapeHtml(text)}`;
      State.weather = {
        condition,
        temperature_c: Number.isFinite(temp) ? temp : null,
        wind_kmh: Number.isFinite(wind) ? wind : null,
        code,
        at: new Date().toISOString()
      };
    } catch (_) {
      DOM.weatherValue.innerHTML = "<i class=\"fas fa-cloud\"></i> Weather unavailable";
    }
  }
};

if (exists(DOM.photoUpload)) {
  DOM.photoUpload.addEventListener("change", (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) {
      State.photoData = null;
      if (exists(DOM.photoPreview)) DOM.photoPreview.innerHTML = "";
      return;
    }

    if (!file.type.startsWith("image/")) {
      Status.show("Please upload a valid image file.", "warning");
      event.target.value = "";
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => {
      State.photoData = ev.target && ev.target.result ? ev.target.result : null;
      if (exists(DOM.photoPreview) && State.photoData) {
        DOM.photoPreview.innerHTML = `<img src="${State.photoData}" alt="Uploaded evidence">`;
      }
    };
    reader.readAsDataURL(file);
  });
}

let userMap = null;
let userMarker = null;

const Location = {
  setError(message) {
    if (exists(DOM.locationText)) DOM.locationText.textContent = message;
    if (exists(DOM.locationMeta)) DOM.locationMeta.textContent = "";
  },

  renderCoordinates(latitude, longitude, accuracy) {
    if (exists(DOM.locationText)) {
      DOM.locationText.textContent = `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
    }

    if (exists(DOM.locationMeta)) {
      const accuracyText = Number.isFinite(accuracy) ? `Accuracy ${Math.round(accuracy)}m` : "Accuracy unknown";
      DOM.locationMeta.textContent = `${accuracyText} | Updated ${new Date().toLocaleTimeString("en-IN")}`;
    }
  },

  renderMap(latitude, longitude) {
    const mapEl = document.getElementById("userMapContainer");
    if (!mapEl || typeof L === "undefined") return;

    mapEl.style.display = "block";

    if (!userMap) {
      userMap = L.map("userMapContainer").setView([latitude, longitude], 15);
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: "&copy; CARTO",
        subdomains: "abcd",
        maxZoom: 20
      }).addTo(userMap);
    } else {
      userMap.setView([latitude, longitude], 15);
    }

    if (userMarker) {
      userMap.removeLayer(userMarker);
    }

    userMarker = L.circleMarker([latitude, longitude], {
      radius: 8,
      fillColor: "#06b6d4",
      color: "#ffffff",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.82
    }).addTo(userMap);

    userMarker.bindPopup("Your location");

    setTimeout(() => {
      try {
        userMap.invalidateSize();
      } catch (_) {
        // ignore map refresh issues
      }
    }, 120);
  },

  updatePosition(position) {
    const { latitude, longitude, accuracy } = position.coords;
    State.location = {
      latitude,
      longitude,
      accuracy: Number.isFinite(accuracy) ? accuracy : null,
      captured_at: new Date().toISOString()
    };

    this.renderCoordinates(latitude, longitude, accuracy);
    this.renderMap(latitude, longitude);
    Weather.update(latitude, longitude);
    Telemetry.emit("location_success", { latitude, longitude, accuracy });
  },

  init() {
    if (!navigator.geolocation) {
      this.setError("Location not supported on this browser");
      Telemetry.emit("location_unsupported");
      return;
    }

    const options = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 30000
    };

    navigator.geolocation.getCurrentPosition(
      (pos) => this.updatePosition(pos),
      (err) => {
        this.setError("Location access denied");
        ErrorReporter.store({ message: "Geolocation error", type: err.code });
        Telemetry.emit("location_error", { code: err.code });
      },
      options
    );

    try {
      State.locationWatchId = navigator.geolocation.watchPosition(
        (pos) => this.updatePosition(pos),
        () => {
          // watch errors are non-fatal
        },
        {
          enableHighAccuracy: false,
          timeout: 15000,
          maximumAge: 45000
        }
      );
    } catch (_) {
      // ignore watch position failures
    }
  }
};

const Voice = {
  init() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      if (exists(DOM.speakBtn)) {
        DOM.speakBtn.disabled = true;
        DOM.speakBtn.innerHTML = '<i class="fas fa-microphone-slash"></i> Not supported';
      }
      Telemetry.emit("voice_unsupported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = navigator.language || "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      State.isListening = true;
      Telemetry.emit("voice_start");
      if (exists(DOM.speakBtn)) DOM.speakBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
      Status.show("Listening. Speak your issue now.", "success");
    };

    recognition.onresult = (event) => {
      const text = event.results && event.results[0] && event.results[0][0]
        ? event.results[0][0].transcript
        : "";
      if (exists(DOM.input)) DOM.input.value = text;
      Telemetry.emit("voice_success", { length: text.length });
      Status.show("Voice captured.", "success");
      renderClassificationPreview();
      Status.clear(1800);
    };

    recognition.onerror = (event) => {
      ErrorReporter.store({ message: "Voice input error", type: event.error });
      Telemetry.emit("voice_error", { code: event.error });
      Status.show("Voice capture failed. You can type your issue.", "error");
      this.stop();
    };

    recognition.onend = () => this.stop();
    State.recognition = recognition;
  },

  start() {
    if (!State.recognition) return;

    if (State.isListening) {
      this.stop();
      return;
    }

    try {
      State.recognition.start();
    } catch (error) {
      ErrorReporter.store(error);
      Status.show("Could not start voice capture.", "error");
    }
  },

  stop() {
    State.isListening = false;
    if (exists(DOM.speakBtn)) {
      DOM.speakBtn.innerHTML = '<i class="fas fa-microphone"></i> Speak';
    }
    try {
      if (State.recognition) State.recognition.stop();
    } catch (_) {
      // ignore stop errors
    }
  }
};

const Queue = {
  dbName: "swarabharat-db",
  storeName: "pending-reports",

  openDb() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);
      request.onerror = () => reject(request.error || new Error("IndexedDB open failed"));
      request.onsuccess = () => resolve(request.result);
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName, { keyPath: "id", autoIncrement: true });
        }
      };
    });
  },

  async add(payload) {
    const db = await this.openDb();
    try {
      await new Promise((resolve, reject) => {
        const tx = db.transaction(this.storeName, "readwrite");
        const store = tx.objectStore(this.storeName);
        store.add({ payload, createdAt: new Date().toISOString() });
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error || new Error("Queue add failed"));
      });
    } finally {
      db.close();
    }
  },

  async getAll() {
    const db = await this.openDb();
    try {
      return await new Promise((resolve, reject) => {
        const tx = db.transaction(this.storeName, "readonly");
        const store = tx.objectStore(this.storeName);
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => reject(req.error || new Error("Queue read failed"));
      });
    } finally {
      db.close();
    }
  },

  async remove(id) {
    const db = await this.openDb();
    try {
      await new Promise((resolve, reject) => {
        const tx = db.transaction(this.storeName, "readwrite");
        const store = tx.objectStore(this.storeName);
        store.delete(id);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error || new Error("Queue delete failed"));
      });
    } finally {
      db.close();
    }
  },

  async count() {
    const db = await this.openDb();
    try {
      return await new Promise((resolve, reject) => {
        const tx = db.transaction(this.storeName, "readonly");
        const store = tx.objectStore(this.storeName);
        const req = store.count();
        req.onsuccess = () => resolve(req.result || 0);
        req.onerror = () => reject(req.error || new Error("Queue count failed"));
      });
    } finally {
      db.close();
    }
  }
};

async function updateSyncInfo() {
  if (!exists(DOM.syncInfo)) return;

  try {
    const queued = await Queue.count();
    if (queued > 0) {
      DOM.syncInfo.textContent = `Queued reports: ${queued}`;
      DOM.syncInfo.className = "sync-badge warning";
    } else {
      DOM.syncInfo.textContent = "All reports synced";
      DOM.syncInfo.className = "sync-badge";
    }
  } catch (_) {
    DOM.syncInfo.textContent = "Queue status unavailable";
    DOM.syncInfo.className = "sync-badge error";
  }
}

async function triggerBackgroundSync() {
  try {
    if (!("serviceWorker" in navigator)) return;
    const reg = await navigator.serviceWorker.ready;
    if (reg && "sync" in reg) {
      await reg.sync.register("sync-reports");
    }
  } catch (_) {
    // ignore background sync registration errors
  }
}

async function flushPendingReports() {
  if (!navigator.onLine) return;

  try {
    const queuedReports = await Queue.getAll();
    if (!queuedReports.length) {
      await updateSyncInfo();
      return;
    }

    for (const item of queuedReports) {
      try {
        await submitWithFallback(item.payload || item);
        await Queue.remove(item.id);
      } catch (_) {
        // keep item for retry
      }
    }

    await updateSyncInfo();
  } catch (_) {
    // queue failures are non-fatal
  }
}

function openRuntimeConfig() {
  const current = localStorage.getItem("SWARA_API_SUBMIT") || "";
  const input = window.prompt(
    "Set custom submit endpoint URL. Leave empty to clear custom endpoint.",
    current
  );

  if (input === null) return;

  const next = input.trim();
  if (!next) {
    localStorage.removeItem("SWARA_API_SUBMIT");
    Status.show("Custom API endpoint cleared.", "success");
    Status.clear(2200);
    return;
  }

  try {
    const url = new URL(next);
    if (!["http:", "https:"].includes(url.protocol)) {
      throw new Error("Only http and https endpoints are allowed");
    }
    localStorage.setItem("SWARA_API_SUBMIT", next);
    Status.show("Custom API endpoint saved.", "success");
    Status.clear(2200);
  } catch (error) {
    Status.show(`Invalid endpoint: ${error.message}`, "warning");
  }
}

function getSubmitEndpoints() {
  const endpoints = [];
  const custom = localStorage.getItem("SWARA_API_SUBMIT");

  if (custom && custom.trim()) endpoints.push(custom.trim());
  endpoints.push(CONFIG.API_SUBMIT);

  if (window.location.protocol !== "file:") {
    endpoints.push(`${window.location.origin}/submit`);
  }

  endpoints.push(CONFIG.API_SUBMIT_FALLBACK);
  return [...new Set(endpoints)];
}

async function submitWithFallback(payload) {
  const endpoints = getSubmitEndpoints();
  const errors = [];

  for (const endpoint of endpoints) {
    try {
      const response = await fetchWithTimeout(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      let result = null;
      try {
        result = await response.json();
      } catch (_) {
        result = null;
      }

      if (!response.ok) {
        const msg = (result && (result.message || result.error)) || `HTTP ${response.status}`;
        throw new Error(msg);
      }

      return { endpoint, result: result || {} };
    } catch (error) {
      errors.push({ endpoint, message: error.message || "Unknown error" });
    }
  }

  const first = errors[0];
  const failure = new Error(first ? first.message : "Submission failed");
  failure.details = errors;
  throw failure;
}

function buildPayload() {
  const text = normalizeText(exists(DOM.input) ? DOM.input.value : "");
  const emergency = normalizeText(exists(DOM.emergency) ? DOM.emergency.value : "");
  const manualIssue = normalizeText(exists(DOM.manualIssue) ? DOM.manualIssue.value : "");
  const classification = classifyCase(text, manualIssue);

  const payload = {
    issue: text,
    emergency,
    location: State.location
      ? {
          latitude: Number(State.location.latitude),
          longitude: Number(State.location.longitude),
          accuracy: State.location.accuracy,
          captured_at: State.location.captured_at
        }
      : null,
    photo: State.photoData || null,
    user_issue_type: manualIssue || classification.issue,
    route_departments: classification.departments,
    route_urgency: classification.urgency,
    route_case_type: classification.caseType,
    submitted_at_client: new Date().toISOString(),
    weather_snapshot: State.weather,
    network_status: navigator.onLine ? "online" : "offline"
  };

  return { payload, classification, text, emergency };
}

async function submitIssue() {
  if (State.isSubmitting) return;
  if (!exists(DOM.input)) {
    Status.show("Input control not found.", "error");
    return;
  }

  const { payload, classification, text, emergency } = buildPayload();

  if (text.length < CONFIG.MIN_TEXT_LENGTH) {
    Status.show("Please describe the issue with a little more detail.", "warning");
    return;
  }

  if (emergency !== "") {
    const digits = emergency.replace(/[\s+\-]/g, "");
    if (!/^\d{10,15}$/.test(digits)) {
      Status.show("Please enter a valid 10-15 digit emergency number.", "warning");
      return;
    }
    payload.emergency = digits;
  }

  State.isSubmitting = true;
  if (exists(DOM.submitBtn)) {
    DOM.submitBtn.disabled = true;
    DOM.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting';
  }

  Telemetry.emit("submit_start", { issue: classification.issue, urgency: classification.urgency });

  try {
    const { endpoint, result } = await submitWithFallback(payload);
    const reportId = (result && result.report_id) || "N/A";

    Telemetry.emit("submit_success", { endpoint, reportId });
    Status.show(
      `Submitted successfully. Report ID: ${reportId}. Routed to: ${classification.departments.join(", ")}.`,
      "success"
    );

    DOM.input.value = "";
    if (exists(DOM.manualIssue)) DOM.manualIssue.value = "";
    if (exists(DOM.emergency)) DOM.emergency.value = "";
    if (exists(DOM.photoUpload)) DOM.photoUpload.value = "";
    if (exists(DOM.photoPreview)) DOM.photoPreview.innerHTML = "";
    State.photoData = null;

    renderClassificationPreview();
    await updateSyncInfo();
    Status.clear(CONFIG.STATUS_AUTO_CLEAR);
  } catch (error) {
    ErrorReporter.store(error);
    Telemetry.emit("submit_failed", { reason: error.message });

    const details = Array.isArray(error.details) ? error.details : [];
    const pattern = /(failed to fetch|network|aborted|timeout|load failed|cors|offline)/i;
    const isNetworkFailure =
      !navigator.onLine ||
      pattern.test(error.message || "") ||
      (details.length > 0 && details.every((item) => pattern.test(item.message || "")));

    if (isNetworkFailure) {
      try {
        await Queue.add(payload);
        await triggerBackgroundSync();
        await updateSyncInfo();
        Status.show("Network unavailable. Report saved offline and will auto-sync.", "warning");
      } catch (queueError) {
        ErrorReporter.store(queueError);
        Status.show(`Submission failed: ${error.message}`, "error");
      }
    } else {
      Status.show(`Submission failed: ${error.message}`, "error");
    }
  } finally {
    State.isSubmitting = false;
    if (exists(DOM.submitBtn)) {
      DOM.submitBtn.disabled = false;
      DOM.submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit';
    }
  }
}

function bindRealtimeClassification() {
  if (exists(DOM.input)) {
    DOM.input.addEventListener("input", renderClassificationPreview);
  }
  if (exists(DOM.manualIssue)) {
    DOM.manualIssue.addEventListener("change", renderClassificationPreview);
  }
  renderClassificationPreview();
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  try {
    await navigator.serviceWorker.register("./sw.js");
    await updateSyncInfo();
    await flushPendingReports();
    console.log("Service worker enabled");
  } catch (error) {
    console.error("Service worker registration failed", error);
  }
}

function initConnectivityFeedback() {
  window.addEventListener("offline", async () => {
    Realtime.refreshNetwork();
    Status.show("Offline mode active. Reports will be queued locally.", "warning");
    await updateSyncInfo();
  });

  window.addEventListener("online", async () => {
    Realtime.refreshNetwork();
    await flushPendingReports();
    Status.show("Back online. Syncing queued reports.", "success");
    Status.clear(2200);
  });
}

function initNotifications() {
  if (!("Notification" in window)) return;
  if (Notification.permission === "default") {
    Notification.requestPermission().catch(() => {
      // ignore permission errors
    });
  }
}

function init() {
  Telemetry.emit("app_loaded");

  Realtime.initClock();
  Realtime.initNetwork();

  Voice.init();
  Location.init();

  if (exists(DOM.speakBtn)) {
    DOM.speakBtn.addEventListener("click", () => Voice.start());
  }

  if (exists(DOM.submitBtn)) {
    DOM.submitBtn.addEventListener("click", submitIssue);
  }

  if (exists(DOM.configApiBtn)) {
    DOM.configApiBtn.addEventListener("click", openRuntimeConfig);
  }

  bindRealtimeClassification();
  registerServiceWorker();
  initConnectivityFeedback();
  initNotifications();
  updateSyncInfo();
}

init();

window.__swaraErrors = () => ErrorReporter.getAll();
window.startVoiceInput = () => Voice.start();
window.submitIssue = submitIssue;
