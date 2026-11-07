// Keyboard shortcuts for the whole site.
//
// - Global single-key shortcuts: T (theme), ? (help), G then P/N/T/S/O (navigation).
// - Page shortcuts: any element with data-shortcut="x" is clicked (links, buttons)
//   or focused (inputs) when the key is pressed; its tooltip shows the key.
// - Ctrl+Enter in a form field submits the form.
// Single-key shortcuts are ignored while typing in a field, when a modifier key
// (Ctrl/Alt/Meta) is held, and can be switched off in the help window (WCAG 2.1.4).
// Study-session keys (space, 1-4) live in study.js.
(function () {
  const STORAGE_KEY = "ns-shortcuts";
  const NAVIGATION = { p: "/", n: "/nauka/", t: "/talie/", s: "/statystyki/", o: "/o-aplikacji/" };
  let pendingG = null;

  function enabled() {
    try { return localStorage.getItem(STORAGE_KEY) !== "off"; } catch (e) { return true; }
  }

  function setEnabled(value) {
    try { localStorage.setItem(STORAGE_KEY, value ? "on" : "off"); } catch (e) { /* storage unavailable */ }
  }

  function isTyping(target) {
    return target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
  }

  function anyModalOpen() {
    return document.querySelector(".modal.show") !== null;
  }

  function showHelp() {
    const element = document.getElementById("shortcuts-modal");
    if (element && window.bootstrap) bootstrap.Modal.getOrCreateInstance(element).show();
  }

  function trigger(element) {
    if (element.classList.contains("disabled") || element.disabled) return;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(element.tagName)) {
      element.focus();
      if (element.select) element.select();
    } else {
      element.click();
    }
  }

  function pageShortcut(key) {
    return Array.from(document.querySelectorAll("[data-shortcut]")).find(function (el) {
      return el.dataset.shortcut === key && el.offsetParent !== null;
    });
  }

  document.addEventListener("keydown", function (event) {
    // Ctrl+Enter (Cmd+Enter on macOS) submits the form of the focused field.
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && event.target.form) {
      event.preventDefault();
      const form = event.target.form;
      form.requestSubmit(form.querySelector("[data-ctrl-enter]") || undefined);
      return;
    }
    if (event.ctrlKey || event.altKey || event.metaKey || isTyping(event.target)) return;
    if (event.repeat) return;

    const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
    if (key === "?") {  // always active, so the shortcuts can be switched back on
      event.preventDefault();
      showHelp();
      return;
    }
    if (!enabled() || anyModalOpen()) return;

    if (pendingG) {
      clearTimeout(pendingG);
      pendingG = null;
      if (NAVIGATION[key]) {
        event.preventDefault();
        window.location.href = NAVIGATION[key];
      }
      return;
    }
    if (key === "g" && document.body.dataset.authenticated === "true") {
      pendingG = setTimeout(function () { pendingG = null; }, 1500);
      return;
    }
    if (key === "t") {
      event.preventDefault();
      window.NS.toggleTheme();
      return;
    }
    const element = pageShortcut(key);
    if (element) {
      event.preventDefault();
      trigger(element);
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    // Tooltips: elements with data-shortcut get the key appended to their title.
    document.querySelectorAll("[data-shortcut]").forEach(function (el) {
      const label = el.getAttribute("title") || el.dataset.shortcutLabel || el.textContent.trim();
      el.setAttribute("title", label + " · skrót: " + el.dataset.shortcut.toUpperCase());
      el.setAttribute("data-bs-toggle", "tooltip");
      el.setAttribute("aria-keyshortcuts", el.dataset.shortcut.toUpperCase());
    });
    if (window.bootstrap) {
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        bootstrap.Tooltip.getOrCreateInstance(el, {
          trigger: "hover", placement: el.closest(".navbar") ? "bottom" : "top",
        });
      });
    }

    // Help window: list this page's shortcuts and wire the on/off switch.
    const list = document.getElementById("page-shortcuts");
    if (list) {
      const items = Array.from(document.querySelectorAll("[data-shortcut]")).filter(function (el) {
        return el.dataset.shortcutLabel;
      });
      items.forEach(function (el) {
        const row = document.createElement("tr");
        const keyCell = document.createElement("td");
        const kbd = document.createElement("kbd");
        kbd.textContent = el.dataset.shortcut.toUpperCase();
        keyCell.appendChild(kbd);
        const labelCell = document.createElement("td");
        labelCell.textContent = el.dataset.shortcutLabel;
        row.append(keyCell, labelCell);
        list.appendChild(row);
      });
      document.getElementById("page-shortcuts-section").classList.toggle("d-none", items.length === 0);
    }
    const toggle = document.getElementById("shortcuts-enabled");
    if (toggle) {
      toggle.checked = enabled();
      toggle.addEventListener("change", function () { setEnabled(toggle.checked); });
    }
    const helpButton = document.getElementById("shortcuts-help");
    if (helpButton) helpButton.addEventListener("click", showHelp);
  });
})();
