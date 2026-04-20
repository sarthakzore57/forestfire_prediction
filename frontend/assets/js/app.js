import {
  createSavedLocation,
  geocodeLocation,
  getSavedLocations,
  predictRisk,
} from "./api.js";
import {
  ensureNotificationPermission,
  pushNotification,
  riskClass,
  setActiveNav,
  showToast,
} from "./common.js";

setActiveNav("home");

const map = L.map("map").setView([37.7749, -122.4194], 5);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

let marker = null;
let riskCircle = null;
const pinnedLayer = L.layerGroup().addTo(map);
let currentSelection = {
  latitude: 37.7749,
  longitude: -122.4194,
  locationName: "San Francisco, US",
  countryCode: "US",
};

const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const predictBtn = document.getElementById("predictBtn");
const pinBtn = document.getElementById("pinBtn");
const suggestionsEl = document.getElementById("suggestions");
const resultEl = document.getElementById("result");
const warningEl = document.getElementById("warning");

function placeMarker(lat, lon) {
  if (marker) {
    marker.setLatLng([lat, lon]);
  } else {
    marker = L.marker([lat, lon]).addTo(map);
  }
}

function colorForCategory(category) {
  if (category === "High") return "#c0392b";
  if (category === "Medium") return "#c49a00";
  return "#2e7d32";
}

function renderSuggestions(items) {
  suggestionsEl.innerHTML = "";
  if (!items.length) {
    suggestionsEl.innerHTML = "<div class='suggestion'>No location found.</div>";
    return;
  }

  items.forEach((item) => {
    const el = document.createElement("button");
    el.className = "suggestion";
    el.type = "button";
    el.innerHTML = `<strong>${item.name}</strong> ${item.state ? `${item.state},` : ""} ${item.country}<br><small>${item.lat.toFixed(4)}, ${item.lon.toFixed(4)}</small>`;
    el.addEventListener("click", () => {
      currentSelection = {
        latitude: item.lat,
        longitude: item.lon,
        locationName: `${item.name}${item.state ? `, ${item.state}` : ""}, ${item.country}`,
        countryCode: item.country,
      };
      map.setView([item.lat, item.lon], 9);
      placeMarker(item.lat, item.lon);
      suggestionsEl.innerHTML = "";
      searchInput.value = currentSelection.locationName;
      showToast(`Selected ${currentSelection.locationName}`);
    });
    suggestionsEl.appendChild(el);
  });
}

async function runSearch() {
  const query = searchInput.value.trim();
  if (!query) {
    showToast("Type a location first");
    return;
  }
  try {
    const results = await geocodeLocation(query);
    renderSuggestions(results);
  } catch (error) {
    showToast(error.message);
  }
}

function renderResult(data) {
  const riskClassName = riskClass(data.risk_category);
  const color = colorForCategory(data.risk_category);
  warningEl.innerHTML = data.warning ? `<div class='warning'>${data.warning}</div>` : "";

  if (riskCircle) {
    riskCircle.setLatLng([data.latitude, data.longitude]);
    riskCircle.setStyle({ color, fillColor: color });
  } else {
    riskCircle = L.circle([data.latitude, data.longitude], {
      radius: 12000,
      color,
      fillColor: color,
      fillOpacity: 0.18,
      weight: 2,
    }).addTo(map);
  }

  resultEl.innerHTML = `
    <div class="result-card">
      <div>
        <div>${data.location_name}</div>
        <small>${data.latitude.toFixed(4)}, ${data.longitude.toFixed(4)}</small>
      </div>
      <div>
        <span class="risk-pill ${riskClassName}">${data.risk_category} Risk</span>
        <strong style="margin-left:8px;">Score: ${data.risk_score.toFixed(2)}</strong>
      </div>
      <div><small>Model: ${data.model_used}</small></div>
      <div class="metric-grid">
        <div class="metric"><div class="metric-label">Temperature</div><div class="metric-value">${data.weather.temperature_c.toFixed(1)} °C</div></div>
        <div class="metric"><div class="metric-label">Humidity</div><div class="metric-value">${data.weather.humidity_pct.toFixed(0)} %</div></div>
        <div class="metric"><div class="metric-label">Wind</div><div class="metric-value">${data.weather.wind_speed_mps.toFixed(1)} m/s</div></div>
        <div class="metric"><div class="metric-label">Rainfall</div><div class="metric-value">${data.weather.rainfall_mm.toFixed(1)} mm</div></div>
      </div>
      <div><small>Weather: ${data.weather.weather_main} (${data.weather.weather_description})</small></div>
    </div>
  `;

  localStorage.setItem(
    "latestPrediction",
    JSON.stringify({
      ...data,
      viewedAt: new Date().toISOString(),
    }),
  );

  const localHistory = JSON.parse(localStorage.getItem("localSearchHistory") || "[]");
  localHistory.unshift({
    location: data.location_name,
    risk: data.risk_category,
    score: data.risk_score,
    date: new Date().toISOString(),
  });
  localStorage.setItem("localSearchHistory", JSON.stringify(localHistory.slice(0, 40)));

  if (data.risk_category === "High") {
    pushNotification(
      "Forest Fire Alert",
      `${data.location_name} is at HIGH risk. Score ${data.risk_score.toFixed(2)}.`,
    );
  }
}

async function runPrediction() {
  try {
    const payload = {
      location_name: currentSelection.locationName,
      latitude: currentSelection.latitude,
      longitude: currentSelection.longitude,
    };
    const prediction = await predictRisk(payload);
    renderResult(prediction);
    showToast("Prediction updated");
  } catch (error) {
    showToast(error.message);
  }
}

async function loadPinnedMarkers() {
  pinnedLayer.clearLayers();
  try {
    const pins = await getSavedLocations();
    pins.forEach((pin) => {
      L.marker([pin.latitude, pin.longitude])
        .bindPopup(`<strong>${pin.location_name}</strong><br/>Pinned location`)
        .addTo(pinnedLayer);
    });
  } catch (_) {
    // Non-blocking; ignore marker refresh failures.
  }
}

async function pinCurrentLocation() {
  try {
    await createSavedLocation({
      location_name: currentSelection.locationName,
      latitude: currentSelection.latitude,
      longitude: currentSelection.longitude,
      country_code: currentSelection.countryCode || "",
      notes: "Pinned from Home",
    });
    showToast("Location pinned");
    await loadPinnedMarkers();
  } catch (error) {
    showToast(error.message);
  }
}

searchBtn.addEventListener("click", runSearch);
predictBtn.addEventListener("click", runPrediction);
pinBtn.addEventListener("click", pinCurrentLocation);
searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    runSearch();
  }
});

map.on("click", (event) => {
  const { lat, lng } = event.latlng;
  currentSelection = {
    latitude: lat,
    longitude: lng,
    locationName: `Custom point (${lat.toFixed(3)}, ${lng.toFixed(3)})`,
    countryCode: "",
  };
  placeMarker(lat, lng);
  showToast("Map location selected");
});

(async function init() {
  const params = new URLSearchParams(window.location.search);
  const lat = Number(params.get("lat"));
  const lon = Number(params.get("lon"));
  if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
    currentSelection = {
      latitude: lat,
      longitude: lon,
      locationName: `Selected from history (${lat.toFixed(3)}, ${lon.toFixed(3)})`,
      countryCode: "",
    };
    map.setView([lat, lon], 8);
  }

  placeMarker(currentSelection.latitude, currentSelection.longitude);
  await loadPinnedMarkers();
  await ensureNotificationPermission();
  runPrediction();
})();
