// "Jak pisać?" — stroke-order player (KanjiVG data from /static/strokes/<hex>.json).
//
// Any element with data-strokes="猫" opens the player for that text. Every kana or
// kanji in the text gets its own box; strokes are drawn one after another (across
// all boxes), with stroke numbers, play/pause, step and speed controls.
// Keys while the window is open: Space play/pause, → next stroke, ← previous stroke,
// R from the beginning, Esc close.
(function () {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const SPEEDS = { slow: 0.06, normal: 0.12, fast: 0.25 };  // path units per millisecond
  const PAUSE_MS = 250;
  const cache = {};

  let strokes = [];   // [{path, length, number}]
  let current = 0;    // index of the stroke being drawn
  let progress = 0;   // 0..1 of the current stroke
  let playing = false;
  let lastTime = null;
  let waitUntil = 0;
  let frame = null;

  const $ = (id) => document.getElementById(id);

  function hex(char) {
    return char.codePointAt(0).toString(16).padStart(5, "0");
  }

  function load(char) {
    if (!cache[char]) {
      cache[char] = fetch(`/static/strokes/${hex(char)}.json`)
        .then((response) => (response.ok ? response.json() : null))
        .catch(() => null);
    }
    return cache[char];
  }

  function svgElement(name, attributes) {
    const element = document.createElementNS(SVG_NS, name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    return element;
  }

  function buildBox(char, data) {
    const box = document.createElement("figure");
    box.className = "stroke-box text-center m-0";
    if (!data) {
      box.innerHTML = '<div class="stroke-missing jp"></div><figcaption class="small text-body-secondary">brak danych</figcaption>';
      box.querySelector(".stroke-missing").textContent = char;
      return box;
    }
    const svg = svgElement("svg", { viewBox: "0 0 109 109", class: "stroke-svg", role: "img", "aria-label": `Kolejność kresek: ${char}` });
    svg.append(
      svgElement("line", { x1: 54.5, y1: 0, x2: 54.5, y2: 109, class: "stroke-grid" }),
      svgElement("line", { x1: 0, y1: 54.5, x2: 109, y2: 54.5, class: "stroke-grid" }),
    );
    const ghosts = svgElement("g", { class: "stroke-ghost" });
    const ink = svgElement("g", { class: "stroke-ink" });
    const numbers = svgElement("g", { class: "stroke-numbers" });
    svg.append(ghosts, ink, numbers);
    data.s.forEach((d, index) => {
      ghosts.append(svgElement("path", { d }));
      const path = svgElement("path", { d });
      ink.append(path);
      const position = data.n[index] || [0, 0];
      const number = svgElement("text", { x: position[0], y: position[1] });
      number.textContent = index + 1;
      numbers.append(number);
      strokes.push({ path, number, length: 0 });
    });
    const caption = document.createElement("figcaption");
    caption.className = "small text-body-secondary";
    caption.textContent = `${char} · kresek: ${data.s.length}`;
    box.append(svg, caption);
    return box;
  }

  function paint() {
    strokes.forEach((stroke, index) => {
      const shown = index < current ? 1 : index === current ? progress : 0;
      stroke.path.style.strokeDashoffset = stroke.length * (1 - shown);
      stroke.path.classList.toggle("active", index === current && shown > 0 && shown < 1);
      stroke.number.classList.toggle("visible", shown > 0);
    });
    const total = strokes.length;
    $("stroke-counter").textContent = !total ? "" : current >= total ? `Gotowe · kresek: ${total}` : `Kreska ${current + 1} z ${total}`;
    $("stroke-play").innerHTML = playing ? '<i class="bi bi-pause-fill"></i> Pauza' : '<i class="bi bi-play-fill"></i> Odtwórz';
  }

  function tick(time) {
    if (!playing) return;
    if (lastTime === null) lastTime = time;
    const elapsed = time - lastTime;
    lastTime = time;
    if (time >= waitUntil && current < strokes.length) {
      const speed = SPEEDS[$("stroke-speed").value] || SPEEDS.normal;
      progress += (elapsed * speed) / Math.max(strokes[current].length, 1);
      if (progress >= 1) {
        progress = 0;
        current += 1;
        waitUntil = time + PAUSE_MS;
      }
    }
    if (current >= strokes.length) {
      current = strokes.length;
      progress = 0;
      playing = false;
    }
    paint();
    if (playing) frame = requestAnimationFrame(tick);
  }

  function play() {
    if (!strokes.length) return;
    if (current >= strokes.length) { current = 0; progress = 0; }
    playing = true;
    lastTime = null;
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(tick);
    paint();
  }

  function pause() {
    playing = false;
    cancelAnimationFrame(frame);
    paint();
  }

  function step(delta) {
    pause();
    current = Math.min(Math.max(current + delta, 0), strokes.length);
    progress = 0;
    paint();
  }

  function restart() {
    pause();
    current = 0;
    progress = 0;
    play();
  }

  async function open(text) {
    const chars = Array.from(text).filter((c) => !/[\s\x00-\x7F、。・〜～()（）]/.test(c));
    const modalElement = $("stroke-modal");
    $("stroke-title").textContent = text;
    const area = $("stroke-area");
    area.innerHTML = '<div class="text-body-secondary small py-5">Wczytywanie…</div>';
    pause();
    strokes = [];
    current = 0;
    progress = 0;
    bootstrap.Modal.getOrCreateInstance(modalElement).show();

    const data = await Promise.all(chars.map(load));
    area.innerHTML = "";
    chars.forEach((char, index) => area.append(buildBox(char, data[index])));
    if (!chars.length) area.innerHTML = '<div class="text-body-secondary small py-5">Brak znaków japońskich do pokazania.</div>';
    strokes.forEach((stroke) => {
      stroke.length = stroke.path.getTotalLength();
      stroke.path.style.strokeDasharray = stroke.length;
    });
    $("stroke-controls").classList.toggle("d-none", strokes.length === 0);
    paint();
    if (modalElement.classList.contains("show")) play();
    else modalElement.addEventListener("shown.bs.modal", play, { once: true });
  }

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-strokes]");
    if (trigger) {
      event.preventDefault();
      open(trigger.dataset.strokes);
    }
  });

  document.addEventListener("DOMContentLoaded", () => {
    const modalElement = $("stroke-modal");
    if (!modalElement) return;
    modalElement.addEventListener("hidden.bs.modal", pause);
    $("stroke-play").addEventListener("click", () => (playing ? pause() : play()));
    $("stroke-prev").addEventListener("click", () => step(-1));
    $("stroke-next").addEventListener("click", () => step(1));
    $("stroke-restart").addEventListener("click", restart);
    $("stroke-numbers").addEventListener("change", (event) => {
      $("stroke-area").classList.toggle("hide-numbers", !event.target.checked);
    });
    modalElement.addEventListener("keydown", (event) => {
      if (event.ctrlKey || event.altKey || event.metaKey) return;
      if (event.target.tagName === "SELECT" || event.target.tagName === "INPUT") return;
      const actions = {
        " ": () => (playing ? pause() : play()),
        ArrowRight: () => step(1),
        ArrowLeft: () => step(-1),
        r: restart,
        R: restart,
      };
      if (actions[event.key]) {
        event.preventDefault();
        actions[event.key]();
      }
    });
  });

  window.NS = window.NS || {};
  window.NS.showStrokes = open;
})();
