// Light/dark theme toggle. The initial theme is applied inline in <head>
// (base.html) to avoid a flash of the wrong theme; this file wires the button
// and exposes NS.toggleTheme() for the keyboard shortcut (shortcuts.js).
(function () {
  const STORAGE_KEY = "ns-theme";

  function store(theme) {
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) { /* storage unavailable */ }
  }

  function apply(theme) {
    document.documentElement.setAttribute("data-bs-theme", theme);
    const icon = document.getElementById("theme-icon");
    if (icon) {
      icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
    }
  }

  function toggle() {
    const next = document.documentElement.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
    apply(next);
    store(next);
  }

  window.NS = window.NS || {};
  window.NS.toggleTheme = toggle;

  document.addEventListener("DOMContentLoaded", function () {
    apply(document.documentElement.getAttribute("data-bs-theme") || "light");
    const button = document.getElementById("theme-toggle");
    if (button) button.addEventListener("click", toggle);
  });
})();
