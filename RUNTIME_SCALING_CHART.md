# Runtime scaling chart template

The Pages landing page includes `_includes/runtime-chart.html`, which loads
`assets/data/scaling-runtime.json` into the dependency-free component in
`assets/js/scaling-chart.js`. The include accepts an optional `data_url` value,
so another page can reuse the same interactive element without copying its
markup. The component is deliberately data-driven: add a dataset with an `id`,
`label`, and points containing `x`, `dimension`, `runtime_seconds`, `status`,
and `label`, then the axis selector, series visibility controls, log-scale
toggle, observed-range summary, tooltips, and accessible table update without
changing the chart code. The script initializes every include on a page, so a
page can compare independent data files with more than one chart. Every key in
`x_axes` must be a finite numeric field on every point; `default_x_axis` names
the initial selection.

The plot shows five labelled x-axis ticks with vertical guides, and every point
is keyboard-focusable. A circle denotes an `EXACT` completed run; a diamond
denotes an `UNKNOWN` run stopped at its cap. The status key is part of the
include so a reused chart keeps the same interpretation.

The checked data combines `NATIVE_RESULTS.json` with the proof-producing CDCL
campaign in `proof_complexity_scaling_lab/SCALING_RESULTS.json`; both source
hashes are saved in the chart data. `EXACT` and `UNKNOWN` records use separate
symbols. UNKNOWN means that the native branch cap stopped the run; it must not
be read as an exact answer, a lower bound, or evidence of an asymptotic runtime
class. Measurements are wall-clock observations from the saved producer
artifacts and are not a polynomial-time proof. The CDCL series are replayed
resolution traces for one deterministic implementation. Source hashes use the
normalized UTF-8 text with LF line endings so the check is stable across
Windows and Linux checkouts.

When a new artifact is accepted:

1. Regenerate the JSON with its source SHA-256 and update the interpretation
   text if the statuses or axes change.
2. Keep the original source artifact and independent verifier in the same
   commit.
3. Run the Pages build and the full research audit before publishing the
   updated chart.
