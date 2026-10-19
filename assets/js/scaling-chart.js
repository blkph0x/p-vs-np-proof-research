(() => {
  "use strict";

  const roots = document.querySelectorAll("[data-runtime-chart]");
  if (!roots.length) return;

  const SVG_NS = "http://www.w3.org/2000/svg";
  const width = 760;
  const height = 390;
  const margin = {top: 26, right: 24, bottom: 62, left: 76};
  let chartInstance = 0;

  function element(name, attrs = {}) {
    const node = document.createElementNS(SVG_NS, name);
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

  function formatXTick(value) {
    if (Number.isInteger(value)) return String(value);
    return value.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
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

  function initialize(root) {
    const svg = root.querySelector("[data-chart-svg]");
    const status = root.querySelector("[data-chart-status]");
    const summary = root.querySelector("[data-chart-summary]");
    const details = root.querySelector("[data-chart-details]");
    const legend = root.querySelector("[data-chart-legend]");
    const tableBody = root.querySelector("[data-chart-table-body]");
    const seriesControls = root.querySelector("[data-chart-series-controls]");
    const axisSelect = root.querySelector("[data-chart-axis]");
    const unknownToggle = root.querySelector("[data-chart-unknown]");
    const xLogToggle = root.querySelector("[data-chart-x-log]");
    const logToggle = root.querySelector("[data-chart-log]");
    const resetButton = root.querySelector("[data-chart-reset]");

    function render(data) {
      const axis = axisSelect.value;
      const showUnknown = unknownToggle.checked;
      const xLogarithmic = xLogToggle.checked;
      const logarithmic = logToggle.checked;
      const selectedIds = new Set([...seriesControls.querySelectorAll("input:checked")].map(input => input.value));
      const visibleDatasets = data.datasets.filter(dataset => selectedIds.has(dataset.id));
      const allPoints = visibleDatasets.flatMap(dataset => dataset.points.map(point => ({...point, dataset})));
      const points = allPoints.filter(point => showUnknown || point.status === "EXACT");
      const plot = {x: margin.left, y: margin.top, width: width - margin.left - margin.right, height: height - margin.top - margin.bottom};
      const xValues = points.map(point => point[axis]).filter(value => Number.isFinite(value) && (!xLogarithmic || value > 0));
      const yValues = points.map(point => point.runtime_seconds).filter(value => value > 0);
      if (!xValues.length || !yValues.length) {
        svg.replaceChildren();
        legend.replaceChildren();
        tableBody.replaceChildren();
        details.textContent = "No point is available for the selected filters.";
        summary.textContent = "Select at least one series with recorded points to view the observed range.";
        status.textContent = "No points match the selected filters.";
        return;
      }
      const xMin = Math.min(...xValues);
      const xMax = Math.max(...xValues);
      const rawYMin = Math.min(...yValues);
      const rawYMax = Math.max(...yValues);
      const yMin = logarithmic ? Math.max(rawYMin / 2, Number.MIN_VALUE) : 0;
      const yMax = logarithmic ? rawYMax * 2 : rawYMax * 1.08 || 1;
      const xScale = value => {
        if (xMax === xMin) return plot.x + plot.width / 2;
        if (xLogarithmic) {
          return plot.x + (Math.log10(value) - Math.log10(xMin)) / (Math.log10(xMax) - Math.log10(xMin)) * plot.width;
        }
        return plot.x + (value - xMin) / (xMax - xMin) * plot.width;
      };
      const yScale = value => {
        if (logarithmic) return plot.y + plot.height - (Math.log10(value) - Math.log10(yMin)) / (Math.log10(yMax) - Math.log10(yMin)) * plot.height;
        return plot.y + plot.height - (value - yMin) / (yMax - yMin) * plot.height;
      };

      svg.replaceChildren();
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.setAttribute("aria-label", `${data.y_axis} by ${data.x_axes[axis]}${xLogarithmic ? " on a logarithmic axis" : ""}`);
      const titleId = `runtime-chart-title-${chartInstance++}`;
      const title = element("title", {id: titleId});
      title.textContent = `${data.y_axis} by ${data.x_axes[axis]}${xLogarithmic ? " on a logarithmic axis" : ""}`;
      svg.setAttribute("aria-labelledby", titleId);
      svg.appendChild(title);
      const grid = element("g", {class: "chart-grid"});
      tickValues(yMin, yMax, logarithmic).forEach(value => {
        const y = yScale(value);
        grid.appendChild(element("line", {x1: plot.x, x2: plot.x + plot.width, y1: y, y2: y}));
        text(grid, formatTick(value, logarithmic), {x: plot.x - 10, y: y + 4, "text-anchor": "end", class: "chart-tick"});
      });
      tickValues(xMin, xMax, xLogarithmic).forEach(value => {
        const x = xScale(value);
        grid.appendChild(element("line", {x1: x, x2: x, y1: plot.y, y2: plot.y + plot.height, class: "chart-grid-vertical"}));
        text(grid, formatXTick(value), {x, y: plot.y + plot.height + 19, "text-anchor": "middle", class: "chart-tick chart-x-tick"});
      });
      svg.appendChild(grid);
      svg.appendChild(element("line", {x1: plot.x, x2: plot.x, y1: plot.y, y2: plot.y + plot.height, class: "chart-axis"}));
      svg.appendChild(element("line", {x1: plot.x, x2: plot.x + plot.width, y1: plot.y + plot.height, y2: plot.y + plot.height, class: "chart-axis"}));
      text(svg, `${data.x_axes[axis]}${xLogarithmic ? " · logarithmic" : ""}`, {x: plot.x + plot.width / 2, y: height - 14, "text-anchor": "middle", class: "chart-label"});
      text(svg, `${data.y_axis}${logarithmic ? " · logarithmic" : ""}`, {x: 17, y: plot.y + plot.height / 2, transform: `rotate(-90 17 ${plot.y + plot.height / 2})`, "text-anchor": "middle", class: "chart-label"});

      legend.replaceChildren();
      visibleDatasets.forEach((dataset, datasetIndex) => {
        const item = document.createElement("span");
        item.className = `chart-legend-item chart-legend-${datasetIndex}`;
        const swatch = document.createElement("span");
        swatch.className = "chart-legend-swatch";
        swatch.setAttribute("aria-hidden", "true");
        item.append(swatch, document.createTextNode(dataset.label));
        legend.appendChild(item);
      });

      visibleDatasets.forEach((dataset, datasetIndex) => {
        const visible = dataset.points
          .filter(point => (showUnknown || point.status === "EXACT") && Number.isFinite(point[axis]) && (!xLogarithmic || point[axis] > 0))
          .sort((a, b) => a[axis] - b[axis]);
        const exact = visible.filter(point => point.status === "EXACT");
        if (exact.length > 1) {
          svg.appendChild(element("polyline", {
            points: exact.map(point => `${xScale(point[axis])},${yScale(point.runtime_seconds)}`).join(" "),
            class: `chart-line chart-line-${datasetIndex}`,
          }));
        }
        visible.forEach(point => {
          const isExact = point.status === "EXACT";
          const x = xScale(point[axis]);
          const y = yScale(point.runtime_seconds);
          const pointNode = isExact
            ? element("circle", {cx: x, cy: y, r: 5})
            : element("path", {d: `M ${x} ${y - 6} L ${x + 6} ${y} L ${x} ${y + 6} L ${x - 6} ${y} Z`});
          pointNode.setAttribute("class", `chart-point chart-point-${datasetIndex} ${isExact ? "exact" : "unknown"}`);
          pointNode.setAttribute("tabindex", "0");
          pointNode.setAttribute("role", "img");
          pointNode.setAttribute("aria-label", `${point.label}: ${formatSeconds(point.runtime_seconds)}, ${point.status}`);
          const show = () => {
            details.textContent = `${point.label} · ${data.x_axes[axis]} ${point[axis]} · ${formatSeconds(point.runtime_seconds)} · ${point.status}`;
          };
          pointNode.addEventListener("mouseenter", show);
          pointNode.addEventListener("focus", show);
          pointNode.addEventListener("click", show);
          svg.appendChild(pointNode);
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
      summary.textContent = `Observed ${points.length} point${points.length === 1 ? "" : "s"} across ${data.x_axes[axis].toLowerCase()} ${xMin}–${xMax}; runtimes span ${formatSeconds(rawYMin)}–${formatSeconds(rawYMax)}. This is a measured range, not an asymptotic fit.`;
      status.textContent = `${points.length} recorded points · ${showUnknown ? "EXACT and UNKNOWN" : "EXACT only"}${xLogarithmic ? " · logarithmic variables" : ""}${logarithmic ? " · logarithmic runtime" : ""}`;
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
        seriesControls.replaceChildren(...data.datasets.map(dataset => {
          const label = document.createElement("label");
          const input = document.createElement("input");
          input.type = "checkbox";
          input.value = dataset.id;
          input.checked = true;
          input.addEventListener("change", () => render(data));
          label.append(input, document.createTextNode(dataset.label));
          return label;
        }));
        [axisSelect, unknownToggle, xLogToggle, logToggle].forEach(control => control.addEventListener("change", () => render(data)));
        resetButton.addEventListener("click", () => {
          axisSelect.value = data.default_x_axis || Object.keys(data.x_axes)[0];
          unknownToggle.checked = false;
          xLogToggle.checked = false;
          logToggle.checked = false;
          seriesControls.querySelectorAll("input").forEach(input => { input.checked = true; });
          render(data);
        });
        render(data);
      })
      .catch(error => {
        status.textContent = `Chart data could not be loaded: ${error.message}`;
        summary.textContent = "The observed runtime range is unavailable until the data file loads.";
        details.textContent = "The repository still contains the raw measurements in assets/data/scaling-runtime.json.";
      });
  }

  roots.forEach(initialize);
})();
