// Study session: reveal the answer, measure response time, keyboard shortcuts.
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const revealBtn = document.getElementById("reveal-btn");
    const answer = document.getElementById("answer");
    const ratings = document.getElementById("ratings");
    const timeInput = document.getElementById("id_response_ms");
    const form = document.getElementById("review-form");
    if (!revealBtn || !answer || !ratings || !form) return;

    const shownAt = performance.now();
    let revealed = false;

    function reveal() {
      if (revealed) return;
      revealed = true;
      if (timeInput) timeInput.value = Math.round(performance.now() - shownAt);
      answer.classList.remove("d-none");
      ratings.classList.remove("d-none");
      revealBtn.classList.add("d-none");
    }

    function rate(value) {
      const button = form.querySelector('button[name="rating"][value="' + value + '"]');
      if (button) button.click();
    }

    revealBtn.addEventListener("click", reveal);
    document.addEventListener("keydown", function (event) {
      if (event.target.tagName === "INPUT" || event.target.tagName === "TEXTAREA") return;
      if (event.code === "Space" || event.key === "Enter") {
        if (!revealed) { event.preventDefault(); reveal(); }
      } else if (revealed && ["1", "2", "3", "4"].includes(event.key)) {
        rate(Number(event.key) - 1);
      }
    });
  });
})();
