# Next R&D

1. Mine arbitrary repeated resolution sub-DAGs, not only OR-collapse chains.
2. For a repeated fragment, synthesize bounded candidate truth tables/ANF/circuits and
   require proof-carrying equivalence certificates.
3. Extend the new bounded indirect XOR/compact-ITE recognizers beyond one-overlap closure to auxiliary definitions and longer proof-carrying compositions.
4. Add PB/cardinality recognition beyond AMO (sequential counters, totalizers, sorting networks).
   The bounded prefix-threshold counter is now certified under a supplied role map;
   standard encodings and unrestricted role discovery remain open.
5. Feed motif recurrence into the existing online rent/buy controller.
6. Test on random/competition proof logs, measuring proposal volume and checker rejection rate.
7. Add interpolation/proof-complexity lower-bound families as mandatory controls.

8. On clique-coloring controls, try circuit/interpolant synthesis over the shared edge
   variables and compare discovered circuit size to known monotone interpolation barriers.
9. Add non-convex theory-combination controls where no individual equality can be propagated.
