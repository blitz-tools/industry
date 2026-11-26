// Observability owner panels: remembered open/closed per owner (the
// roster.js localStorage pattern, keyed on the owner ref so same-named
// owners never collide). Loaded immediately after the panel markup so
// remembered states apply during parsing, before the browser's first
// paint.

window.initObservabilityOwners = () => {
  const rows = document.querySelectorAll("details.obs-owner");
  rows.forEach((row) => {
    const key = `obs-owner-open:${row.dataset.owner}`;
    let saved = null;
    try {
      saved = localStorage.getItem(key);
    } catch (error) {
      /* private browsing mode */
    }
    if (saved !== null) row.open = saved === "true";
    row.addEventListener("toggle", () => {
      try {
        localStorage.setItem(key, String(row.open));
      } catch (error) {
        /* private browsing mode */
      }
    });
  });
};

window.initObservabilityOwners();

// Line-chart crosshair + tooltip: the vertical hairline tracks the
// pointer and snaps to the nearest sample; the readout lists every
// series at that X (values lead, names follow — the legend's hierarchy
// inverted). The data comes from the JSON twin beside the SVG, whose
// points carry the pixel coordinates the server drew, so no scale
// math runs here. Labels are inserted with textContent only.
window.initObservabilityCharts = () => {
  document.querySelectorAll("figure.chart-figure").forEach((figure) => {
    const source = figure.querySelector("script[type='application/json']");
    const svg = figure.querySelector("svg.line-chart");
    const tooltip = figure.querySelector(".chart-tooltip");
    const crosshair = svg && svg.querySelector(".chart-crosshair");
    if (!source || !svg || !tooltip || !crosshair) return;
    let data;
    try {
      data = JSON.parse(source.textContent);
    } catch (error) {
      return;
    }
    if (!data.series || !data.series.length) return;

    const view = svg.viewBox.baseVal;
    const toViewX = (clientX) => {
      const rect = svg.getBoundingClientRect();
      return rect.width ? ((clientX - rect.left) * view.width) / rect.width : 0;
    };

    const hide = () => {
      crosshair.setAttribute("visibility", "hidden");
      tooltip.hidden = true;
    };

    const render = (x) => {
      let anchor = null;
      data.series.forEach((series) => {
        series.points.forEach((point) => {
          const distance = Math.abs(point.x - x);
          if (anchor === null || distance < anchor.distance) {
            anchor = { distance, point };
          }
        });
      });
      if (anchor === null) return;
      crosshair.setAttribute("x1", anchor.point.x);
      crosshair.setAttribute("x2", anchor.point.x);
      crosshair.setAttribute("visibility", "visible");
      tooltip.replaceChildren();
      data.series.forEach((series) => {
        let close = series.points[0];
        series.points.forEach((point) => {
          if (
            Math.abs(point.x - anchor.point.x) < Math.abs(close.x - anchor.point.x)
          ) {
            close = point;
          }
        });
        const row = document.createElement("p");
        const key = document.createElement("span");
        key.className = "chart-tooltip-key";
        key.style.background = series.hue;
        const value = document.createElement("strong");
        value.textContent = close.value;
        const name = document.createElement("span");
        name.className = "chart-tooltip-name";
        name.textContent = series.name;
        row.append(key, value, name);
        tooltip.append(row);
      });
      tooltip.hidden = false;
      const scale = view.width / svg.getBoundingClientRect().width;
      const left = Math.min(
        Math.max(anchor.point.x / scale + 12, 0),
        Math.max(svg.getBoundingClientRect().width - tooltip.offsetWidth - 8, 0)
      );
      tooltip.style.left = `${left}px`;
    };

    svg.addEventListener("pointermove", (event) => render(toViewX(event.clientX)));
    svg.addEventListener("pointerleave", hide);
    // Keyboard parity: focus shows the readout at the latest sample.
    svg.addEventListener("focus", () => render(view.width));
    svg.addEventListener("blur", hide);
  });
};

window.initObservabilityCharts();
