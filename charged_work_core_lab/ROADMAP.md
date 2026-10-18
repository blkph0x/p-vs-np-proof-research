# Next bounded experiment

1. For each verified non-graphic sample, consider fixing at most two coordinates.
   Search for direct-sum or low-order separators in the resulting shortened code.
   Report candidate-discovery work and the distinction between shortening and puncturing.
2. Carry the affine target syndrome across every separator and reconstruct a full
   original-code witness. The b=0 branch must still exclude the zero full word.
   Reuse the current conditioned trellis and generator enumeration as exact oracles.
3. Compare total work across all feasible cosets, not just the largest table.
   Count separator discovery, local solves, interface merges and reconstruction.
   Accept a useful improvement only if it beats a defined baseline after these costs.
4. Add a native residual solver only with a checkable representation certificate.
   Solving an affine coset is a separate obligation from solving a homogeneous code;
   a native minimum-distance routine alone does not automatically solve every coset.
5. Keep complete-graph graphic controls, verified Fano-minor samples, zero codes,
   puncturing traps, and interrupted-budget cases in the regression suite.

The charged-work replay now verifies that all completed choices pay at least the
original `2^w` state scale when branch enumeration is included. If all small
conditioning choices merely exchange states for branches, record that negative
outcome and move to symbolic/native residual structure. Larger random
examples alone would not resolve the architectural obstacle. The n=28 all-cut
internal-4 audit and explicit large-width family construction remain separate work.
