# Runtime scaling chart template

The Pages landing page loads `assets/data/scaling-runtime.json` into the
dependency-free component in `assets/js/scaling-chart.js`. The component is
deliberately data-driven: add a dataset with an `id`, `label`, and points
containing `x`, `dimension`, `runtime_seconds`, `status`, and `label`, then the
axis selector, log-scale toggle, tooltips, and accessible table update without
changing the chart code.

The checked data combines `NATIVE_RESULTS.json` with the proof-producing CDCL
campaign in `proof_complexity_scaling_lab/SCALING_RESULTS.json`; both source
hashes are saved in the chart data. `EXACT` and `UNKNOWN` records use separate
symbols. UNKNOWN means that the native branch cap stopped the run; it must not
be read as an exact answer, a lower bound, or evidence of an asymptotic runtime
class. Measurements are wall-clock observations from the saved producer
artifacts and are not a polynomial-time proof. The CDCL series are replayed
resolution traces for one deterministic implementation.

When a new artifact is accepted:

1. Regenerate the JSON with its source SHA-256 and update the interpretation
   text if the statuses or axes change.
2. Keep the original source artifact and independent verifier in the same
   commit.
3. Run the Pages build and the full research audit before publishing the
   updated chart.
