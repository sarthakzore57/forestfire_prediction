const API_BASE = window.location.origin;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      message = data.detail || data.message || message;
    } catch (_) {
      // Ignore parse errors and use fallback message.
    }
    throw new Error(message);
  }

  return response.json();
}

export function geocodeLocation(query) {
  return request(`/api/geocode?query=${encodeURIComponent(query)}`);
}

export function fetchWeather(latitude, longitude) {
  return request(`/api/weather?latitude=${latitude}&longitude=${longitude}`);
}

export function predictRisk(payload) {
  return request("/api/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getHistory(limit = 100) {
  return request(`/api/history?limit=${limit}`);
}

export function getSavedLocations() {
  return request("/api/saved-locations");
}

export function createSavedLocation(payload) {
  return request("/api/saved-locations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteSavedLocation(locationId) {
  return request(`/api/saved-locations/${locationId}`, {
    method: "DELETE",
  });
}

export function getConfig() {
  return request("/api/config");
}
