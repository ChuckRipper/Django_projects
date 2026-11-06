// Daily reviews chart (Chart.js). Colours are read from CSS variables so the chart
// follows the light/dark theme and is re-drawn when the theme changes.
(function () {
  const canvas = document.getElementById("daily-chart");
  const dataEl = document.getElementById("daily-data");
  if (!canvas || !dataEl || typeof Chart === "undefined") return;
  const data = JSON.parse(dataEl.textContent);
  let chart = null;

  function css(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function render() {
    if (chart) chart.destroy();
    const surface = css("--ns-surface");
    const ink = css("--ns-muted");
    const grid = css("--ns-grid");
    const bar = { maxBarThickness: 24, borderColor: surface, borderWidth: 1, borderSkipped: false };
    chart = new Chart(canvas, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          { ...bar, label: "Poprawne", data: data.correct, backgroundColor: css("--ns-chart-1"),
            // rounded top only when no "again" segment sits on top of this bar
            borderRadius: (ctx) => (data.again[ctx.dataIndex] ? 0 : { topLeft: 4, topRight: 4 }),
          },
          {
            ...bar, label: "Znów", data: data.again, backgroundColor: css("--ns-chart-2"),
            borderRadius: { topLeft: 4, topRight: 4 },
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          x: { stacked: true, grid: { display: false }, ticks: { color: ink, maxRotation: 0, autoSkipPadding: 12 } },
          y: {
            stacked: true, beginAtZero: true, border: { display: false },
            grid: { color: grid, lineWidth: 1 }, ticks: { color: ink, precision: 0 },
          },
        },
        plugins: {
          legend: { position: "top", align: "end", labels: { color: ink, boxWidth: 12, boxHeight: 12, useBorderRadius: true, borderRadius: 2 } },
          tooltip: {
            callbacks: {
              footer: (items) => "Razem: " + items.reduce((sum, item) => sum + item.parsed.y, 0),
            },
          },
        },
      },
    });
  }

  render();
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["data-bs-theme"] });
})();
