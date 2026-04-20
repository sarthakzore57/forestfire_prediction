import {
  createSavedLocation,
  deleteSavedLocation,
  getConfig,
  getSavedLocations,
  predictRisk,
} from "./api.js";
import {
  ensureNotificationPermission,
  formatDate,
  pushNotification,
  riskClass,
  setActiveNav,
  showToast,
} from "./common.js";

setActiveNav("saved");

const gridEl = document.getElementById("savedGrid");
const addForm = document.getElementById("manualPinForm");
const refreshAllBtn = document.getElementById("refreshAllBtn");

let refreshTimer = null;
let config = {
  pin_refresh_minutes: 5,
};

function riskChanged(oldScore, newScore, oldCategory, newCategory) {
  if (!oldCategory) return true;
  if (newCategory === "High" && oldCategory !== "High") return true;
  if (Math.abs((oldScore || 0) - (newScore || 0)) >= 0.2) return true;
  return false;
}

async function refreshPin(pin) {
  const payload = {
    location_name: pin.location_name,
    latitude: pin.latitude,
    longitude: pin.longitude,
    pinned_location_id: pin.id,
  };
  const prediction = await predictRisk(payload);

  if (
    riskChanged(
      pin.last_risk_score,
      prediction.risk_score,
      pin.last_risk_category,
      prediction.risk_category,
    )
  ) {
    const message = `${pin.location_name}: ${prediction.risk_category} (${prediction.risk_score.toFixed(2)})`;
    showToast(message);
    if (prediction.risk_category === "High") {
      pushNotification("High Fire Risk Alert", message);
    }
  }

  return prediction;
}

async function refreshAll() {
  try {
    const pins = await getSavedLocations();
    for (const pin of pins) {
      // Sequential refresh avoids API bursts and keeps progress predictable.
      await refreshPin(pin);
    }
    await loadSaved();
  } catch (error) {
    showToast(error.message);
  }
}

function renderSaved(pins) {
  gridEl.innerHTML = "";
  if (!pins.length) {
    gridEl.innerHTML = "<div class='saved-card'>No saved locations yet.</div>";
    return;
  }

  pins.forEach((pin) => {
    const card = document.createElement("div");
    card.className = "saved-card";
    card.innerHTML = `
      <div>
        <strong>${pin.location_name}</strong>
        <div><small>${pin.latitude.toFixed(4)}, ${pin.longitude.toFixed(4)}</small></div>
      </div>
      <div>
        <span class="risk-pill ${riskClass(pin.last_risk_category || "Low")}">
          ${pin.last_risk_category || "Not checked"}
        </span>
        ${pin.last_risk_score != null ? `<strong style="margin-left:8px;">${pin.last_risk_score.toFixed(2)}</strong>` : ""}
      </div>
      <div><small>Last checked: ${formatDate(pin.last_checked_at)}</small></div>
      <div class="saved-actions">
        <button class="btn btn-secondary" data-refresh="${pin.id}">Refresh</button>
        <button class="btn" style="background:#fbe4e1;color:#922b21;" data-delete="${pin.id}">Delete</button>
      </div>
    `;
    gridEl.appendChild(card);
  });

  gridEl.querySelectorAll("[data-refresh]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      try {
        const locationId = Number(btn.getAttribute("data-refresh"));
        const pins = await getSavedLocations();
        const pin = pins.find((p) => p.id === locationId);
        if (!pin) throw new Error("Pinned location not found");
        await refreshPin(pin);
        await loadSaved();
      } catch (error) {
        showToast(error.message);
      } finally {
        btn.disabled = false;
      }
    });
  });

  gridEl.querySelectorAll("[data-delete]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const locationId = Number(btn.getAttribute("data-delete"));
      try {
        await deleteSavedLocation(locationId);
        showToast("Location removed");
        await loadSaved();
      } catch (error) {
        showToast(error.message);
      }
    });
  });
}

async function loadSaved() {
  const pins = await getSavedLocations();
  renderSaved(pins);
}

addForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(addForm);
  try {
    await createSavedLocation({
      location_name: form.get("location_name"),
      latitude: Number(form.get("latitude")),
      longitude: Number(form.get("longitude")),
      notes: form.get("notes") || "",
      country_code: (form.get("country_code") || "").toString().toUpperCase(),
    });
    addForm.reset();
    showToast("Pinned location added");
    await loadSaved();
  } catch (error) {
    showToast(error.message);
  }
});

refreshAllBtn.addEventListener("click", refreshAll);

(async function init() {
  try {
    await ensureNotificationPermission();
    config = await getConfig();
    await loadSaved();

    const intervalMs = Math.max(1, Number(config.pin_refresh_minutes || 5)) * 60 * 1000;
    refreshTimer = setInterval(refreshAll, intervalMs);
  } catch (error) {
    showToast(error.message);
  }
})();

window.addEventListener("beforeunload", () => {
  if (refreshTimer) clearInterval(refreshTimer);
});
