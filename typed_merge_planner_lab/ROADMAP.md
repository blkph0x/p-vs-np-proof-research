# Next R&D

1. **Completed:** infer exact Schaefer signatures for every bounded invented relation
   automatically and feed them into the typed planner.
2. **Partially completed:** add a supplied strong Horn/affine backdoor edge with an
   explicit `2^k * poly(input)` solver and direct replay. The remaining work is
   parameter discovery and additional hard-pair parameters; no automatic small
   backdoor theorem is assumed.
3. Add parameterized hard-pair edges: affine+cardinality by code dimension/distance,
   Horn+affine by recursive backdoor depth, etc.
4. Add native theory-combination conditions such as convex/equality-interpolating
   Nelson-Oppen edges.
5. Let extension variables/reencodings change both the structural scopes and the language
   labels before replanning.
6. Integrate region-order investment/basin hopping with typed merge feasibility.
7. The one-bridge Horn/affine search rejects every factorization of positive
   exact-one, while the exhaustive two-bridge search finds explicit
   factorizations in all four orientations. The resulting fixed mixed
   Horn+affine language is NP-hard by a direct positive-1-in-3 reduction.
   The next target is a global planner that charges auxiliary interaction and
   bridge discovery rather than treating this local factorization as a free
   simplification. The primal-width audit now shows the fixed gadget preserves
   the original clause-graph pathwidth up to an additive two, so the next
   global target is an explicit order/discovery algorithm rather than more
   local factor search.
   A proof-producing mixed-relation frontier DP is now implemented for a
   supplied order; its remaining gap is exactly the global order/discovery
   bound, not local relation evaluation.
   The exact subset order oracle now reconstructs and certifies minimum-width
   orders on the same controls, while retaining its `O(n 2^n)` discovery cost.
8. Keep greedy-failure and minimum-distance fixtures as permanent controls.
