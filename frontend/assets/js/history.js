import { getHistory } from "./api.js";
import { formatDate, riskClass, setActiveNav, showToast } from "./common.js";

setActiveNav("history");

const tableBody = document.getElementById("historyTableBody");
const localHistoryList = document.getElementById("localHistoryList");

function renderServerHistory(items) {
  tableBody.innerHTML = "";
  if (!items.length) {
    tableBody.innerHTML = "<tr><td colspan='7'>No history yet. Make predictions from Home page.</td></tr>";
    return;
  }

  items.forEach((item) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.location_name}</td>
      <td>${item.latitude.toFixed(3)}, ${item.longitude.toFixed(3)}</td>
      <td>${item.risk_score.toFixed(2)}</td>
      <td><span class="risk-pill ${riskClass(item.risk_category)}">${item.risk_category}</span></td>
      <td>${item.model_used}</td>
      <td>${formatDate(item.created_at)}</td>
      <td><a href="/?lat=${item.latitude}&lon=${item.longitude}">Open</a></td>
    `;
    tableBody.appendChild(row);
  });
}

function renderLocalHistory() {
  const localHistory = JSON.parse(localStorage.getItem("localSearchHistory") || "[]");
  localHistoryList.innerHTML = "";
  if (!localHistory.length) {
    localHistoryList.innerHTML = "<li>No local history.</li>";
    return;
  }

  localHistory.slice(0, 15).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = `${formatDate(item.date)} | ${item.location} | ${item.risk} (${item.score.toFixed(2)})`;
    localHistoryList.appendChild(li);
  });
}

async function load() {
  try {
    const history = await getHistory(200);
    renderServerHistory(history);
    renderLocalHistory();
  } catch (error) {
    showToast(error.message);
  }
}

load();
