// Study session: reveal (or check a typed answer), measure response time, keyboard shortcuts.
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const revealBtn = document.getElementById("reveal-btn");
    const answer = document.getElementById("answer");
    const ratings = document.getElementById("ratings");
    const timeInput = document.getElementById("id_response_ms");
    const form = document.getElementById("review-form");
    if (!revealBtn || !answer || !ratings || !form) return;

    const typed = document.getElementById("typed-answer");
    const feedback = document.getElementById("typed-feedback");
    const answersData = document.getElementById("typing-answers");
    const shownAt = performance.now();
    let revealed = false;

    function ratingButton(value) {
      return form.querySelector('button[name="rating"][value="' + value + '"]');
    }

    function reveal() {
      if (revealed) return;
      revealed = true;
      if (timeInput) timeInput.value = Math.round(performance.now() - shownAt);
      answer.classList.remove("d-none");
      ratings.classList.remove("d-none");
      revealBtn.classList.add("d-none");
    }

    function rate(value) {
      const button = ratingButton(value);
      if (button) button.click();
    }

    // --- Typed-answer mode ----------------------------------------------------
    // Both sides go through WanaKana's toHiragana, so "shi"/"si", ん/"n" and
    // katakana/hiragana count as the same answer.
    function normalize(text) {
      const cleaned = text.trim().toLowerCase().replace(/\s+/g, "");
      return window.wanakana ? wanakana.toHiragana(cleaned) : cleaned;
    }

    function suggest(value) {
      const button = ratingButton(value);
      const outline = value === 0 ? "btn-outline-danger" : "btn-outline-success";
      button.classList.replace(outline, value === 0 ? "btn-danger" : "btn-success");
      button.focus();
      document.getElementById("suggestion-hint").classList.remove("d-none");
    }

    function check() {
      if (revealed) return;
      const value = typed.value.trim();
      const accepted = JSON.parse(answersData.textContent).map(normalize);
      const correct = value !== "" && accepted.includes(normalize(value));
      reveal();
      typed.readOnly = true;
      typed.classList.add(correct ? "is-valid" : "is-invalid");
      feedback.classList.remove("d-none");
      feedback.className = "mt-2 fw-semibold " + (correct ? "text-success" : "text-danger");
      feedback.textContent = correct
        ? "✓ Dobrze!"
        : value === "" ? "✗ Nie wpisano odpowiedzi." : "✗ Niepoprawnie. Prawidłowa odpowiedź jest niżej.";
      suggest(correct ? 2 : 0);
    }

    if (typed) {
      if (typed.dataset.kana === "1" && window.wanakana) {
        wanakana.bind(typed, { IMEMode: true });
      }
      typed.focus();
      typed.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.isComposing) {
          event.preventDefault();
          check();
        }
      });
      revealBtn.addEventListener("click", check);
    } else {
      revealBtn.addEventListener("click", reveal);
    }

    document.addEventListener("keydown", function (event) {
      if (event.target.tagName === "INPUT" || event.target.tagName === "TEXTAREA") return;
      if (event.ctrlKey || event.altKey || event.metaKey) return;  // e.g. Ctrl+1 switches browser tabs
      if (document.querySelector(".modal.show")) return;
      if (!revealed && (event.code === "Space" || event.key === "Enter")) {
        event.preventDefault();
        if (typed) typed.focus(); else reveal();
      } else if (revealed && ["1", "2", "3", "4"].includes(event.key)) {
        rate(Number(event.key) - 1);
      }
    });
  });
})();
