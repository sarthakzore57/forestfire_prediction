export function riskClass(category) {
  if (!category) return "";
  const c = category.toLowerCase();
  if (c.includes("high")) return "risk-high";
  if (c.includes("medium")) return "risk-medium";
  return "risk-low";
}

export function formatDate(value) {
  if (!value) return "-";
  const dt = new Date(value);
  return dt.toLocaleString();
}

export function showToast(message) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 2200);
}

export function setActiveNav(pageKey) {
  const links = document.querySelectorAll("[data-nav]");
  links.forEach((a) => {
    a.classList.toggle("active", a.getAttribute("data-nav") === pageKey);
  });
}

export async function ensureNotificationPermission() {
  if (!("Notification" in window)) return false;
  if (Notification.permission === "granted") return true;
  if (Notification.permission === "denied") return false;
  const result = await Notification.requestPermission();
  return result === "granted";
}

export function pushNotification(title, body) {
  if (!("Notification" in window)) return;
  if (Notification.permission !== "granted") return;
  // eslint-disable-next-line no-new
  new Notification(title, { body });
}
