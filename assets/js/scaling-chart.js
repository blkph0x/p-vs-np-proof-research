(() => {
  "use strict";

  const root = document.querySelector("[data-runtime-chart]");
  if (!root) return;

  const svg = root.querySelector("[data-chart-svg]");
  const status = root.querySelector("[data-chart-status]");
  const details = root.querySelector("[data-chart-details]");
  const legend = root.querySelector("[data-chart-legend]");
  const tableBody = root.querySelector("[data-chart-table-body]");
  const axisSelect = root.querySelector("[data-chart-axis]");
  const unknownToggle = root.querySelector("[data-chart-unknown]");
  const logToggle = root.querySelector("[data-chart-log]");
  const resetButton = root.querySelector("[data-chart-reset]");
  const width = 760;
  const height = 390;
  const margin = {top: 26, right: 24, bottom: 62, left: 76};

  function element(name, attrs = {}) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    return node;
  }

  function text(parent, value, attrs = {}) {
    const node = element("text", attrs);
    node.textContent = value;
    parent.appendChild(node);
    return node;
  }

  function formatSeconds(value) {
    if (value < 0.001) return `${(value * 1000000).toFixed(1)} μs`;
    if (value < 1) return `${(value * 1000).toFixed(1)} ms`;
    return `${value.toFixed(3)} s`;
  }

  function formatTick(value, logarithmic) {
    if (!logarithmic) return value < 1 ? `${(value * 1000).toFixed(0)} ms` : `${value.toFixed(2)} s`;
    if (value >= 1) return `${value.toFixed(value >= 10 ? 0 : 1)} s`;
    return `${(value * 1000).toFixed(0)} ms`;
  }

  function tickValues(min, max, logarithmic) {
    if (logarithmic) {
      const lo = Math.log10(min);
      const hi = Math.log10(max);
      return Array.from({length: 5}, (_, i) => 10 ** (lo + (hi - lo) * i / 4));
    }
    const step = (max - min) / 4;
    return Array.from({length: 5}, (_, i) => min + step * i);
  }

  function render(data) {
    const axis = axisSelect.value;
    const showUnknown = unknownToggle.checked;
    const logarithmic = logToggle.checked;
    const allPoints = data.datasets.flatMap(dataset => dataset.points.map(point => ({...point, dataset})));
    const points = allPoints.filter(point => showUnknown || point.status === "EXACT");
    const plot = {x: margin.left, y: margin.top, width: width - margin.left - margin.right, height: height - margin.top - margin.bottom};
    const xValues = points.map(point => point[axis]).filter(Number.isFinite);
    const yValues = points.map(point => point.runtime_seconds).filter(value => value > 0);
    if (!xValues.length || !yValues.length) {
      status.textContent = "No points match the selected filters.";
      return;
    }
    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const rawYMin = Math.min(...yValues);
    const rawYMax = Math.max(...yValues);
    const yMin = logarithmic ? Math.max(rawYMin / 2, Number.MIN_VALUE) : 0;
    const yMax = logarithmic ? rawYMax * 2 : rawYMax * 1.08 || 1;
    const xScale = value => plot.x + (xMax === xMin ? .5 : (value - xMin) / (xMax - xMin)) * plot.width;
    const yScale = value => {
      if (logarithmic) return plot.y + plot.height - (Math.log10(value) - Math.log10(yMin)) / (Math.log10(yMax) - Math.log10(yMin)) * plot.height;
      return plot.y + plot.height - (value - yMin) / (yMax - yMin) * plot.height;
    };

    svg.replaceChildren();
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("aria-label", `${data.y_axis} by ${data.x_axes[axis]}`);
    const grid = element("g", {class: "chart-grid"});
    const ticks = tickValues(yMin, yMax, logarithmic);
    ticks.forEach(value => {
      const y = yScale(value);
      grid.appendChild(element("line", {x1: plot.x, x2: plot.x + plot.width, y1: y, y2: y}));
      text(grid, formatTick(value, logarithmic), {x: plot.x - 10, y: y + 4, "text-anchor": "end", class: "chart-tick"});
    });
    svg.appendChild(grid);
    svg.appendChild(element("line", {x1: plot.x, x2: plot.x, y1: plot.y, y2: plot.y + plot.height, class: "chart-axis"}));
    svg.appendChild(element("line", {x1: plot.x, x2: plot.x + plot.width, y1: plot.y + plot.height, y2: plot.y + plot.height, class: "chart-axis"}));
    text(svg, data.x_axes[axis], {x: plot.x + plot.width / 2, y: height - 14, "text-anchor": "middle", class: "chart-label"});
    text(svg, `${data.y_axis}${logarithmic ? " · logarithmic" : ""}`, {x: 17, y: plot.y + plot.height / 2, transform: `rotate(-90 17 ${plot.y + plot.height / 2})`, "text-anchor": "middle", class: "chart-label"});

    legend.replaceChildren();
    data.datasets.forEach((dataset, datasetIndex) => {
      const item = document.createElement("span");
      item.className = `chart-legend-item chart-legend-${datasetIndex}`;
      const swatch = document.createElement("span");
      swatch.className = "chart-legend-swatch";
      swatch.setAttribute("aria-hidden", "true");
      item.append(swatch, document.createTextNode(dataset.label));
      legend.appendChild(item);
    });

    data.datasets.forEach((dataset, datasetIndex) => {
      const visible = dataset.points
        .filter(point => (showUnknown || point.status === "EXACT") && Number.isFinite(point[axis]))
        .sort((a, b) => a[axis] - b[axis]);
      const exact = visible.filter(point => point.status === "EXACT");
      if (exact.length > 1) {
        svg.appendChild(element("polyline", {
          points: exact.map(point => `${xScale(point[axis])},${yScale(point.runtime_seconds)}`).join(" "),
          class: `chart-line chart-line-${datasetIndex}`,
        }));
      }
      visible.forEach(point => {
        const circle = element("circle", {
          cx: xScale(point[axis]), cy: yScale(point.runtime_seconds), r: point.status === "EXACT" ? 5 : 6,
          class: `chart-point chart-point-${datasetIndex} ${point.status === "EXACT" ? "exact" : "unknown"}`,
          tabindex: 0, role: "img",
          "aria-label": `${point.label}: ${formatSeconds(point.runtime_seconds)}, ${point.status}`,
        });
        const show = () => {
          details.textContent = `${point.label} · ${data.x_axes[axis]} ${point[axis]} · ${formatSeconds(point.runtime_seconds)} · ${point.status}`;
        };
        circle.addEventListener("mouseenter", show);
        circle.addEventListener("focus", show);
        circle.addEventListener("click", show);
        svg.appendChild(circle);
      });
    });

    tableBody.replaceChildren();
    points.filter(point => Number.isFinite(point[axis])).sort((a, b) => a[axis] - b[axis]).forEach(point => {
      const row = document.createElement("tr");
      [point.dataset.label, point[axis], point.runtime_seconds.toFixed(6), point.status].forEach(value => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
      });
      tableBody.appendChild(row);
    });
    status.textContent = `${points.length} recorded points · ${showUnknown ? "EXACT and UNKNOWN" : "EXACT only"}${logarithmic ? " · log scale" : ""}`;
  }

  fetch(root.dataset.runtimeSource)
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(data => {
      axisSelect.replaceChildren(...Object.entries(data.x_axes).map(([value, label]) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        return option;
      }));
      [axisSelect, unknownToggle, logToggle].forEach(control => control.addEventListener("change", () => render(data)));
      resetButton.addEventListener("click", () => {
        axisSelect.value = data.default_x_axis || Object.keys(data.x_axes)[0];
        unknownToggle.checked = false;
        logToggle.checked = false;
        render(data);
      });
      render(data);
    })
    .catch(error => {
      status.textContent = `Chart data could not be loaded: ${error.message}`;
      details.textContent = "The repository still contains the raw measurements in assets/data/scaling-runtime.json.";
    });
})();
