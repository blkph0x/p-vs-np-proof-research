# Typed Merge Planner Lab

Run:
    python -m unittest -v test_lab
    python -m unittest -v test_invented_relation_bridge.py
    python -m unittest -v test_backdoor_solver.py
    python run_backdoor_audit.py
    python BACKDOOR_REVIEW.py

Key artifacts:
- engine.py
- bridge_factorization.py and BRIDGE_FACTOR_THEOREM.md
- two_bridge_factorization.py and TWO_BRIDGE_FACTOR_THEOREM.md
- RESULTS.json
- BRIDGE_FACTOR_RESULTS.json and BRIDGE_FACTOR_REVIEW.json
- TWO_BRIDGE_FACTOR_RESULTS.json and TWO_BRIDGE_FACTOR_REVIEW.json
- mixed_horn_affine_reduction.py and MIXED_REDUCTION_REVIEW.json
- mixed_bridge_width.py and MIXED_BRIDGE_WIDTH_THEOREM.md
- MIXED_BRIDGE_WIDTH_RESULTS.json and MIXED_BRIDGE_WIDTH_REVIEW.json
- mixed_relation_dp.py and MIXED_RELATION_DP_THEOREM.md
- MIXED_RELATION_DP_RESULTS.json, MIXED_RELATION_DP_CERTIFICATES.json and MIXED_RELATION_DP_REVIEW.json
- mixed_order_discovery.py and MIXED_ORDER_DISCOVERY_THEOREM.md
- MIXED_ORDER_DISCOVERY_RESULTS.json, MIXED_ORDER_DISCOVERY_CERTIFICATES.json and MIXED_ORDER_DISCOVERY_REVIEW.json
- HELPER_PLAN.json
- GREEDY_FAILURE.json
- relation_pair_matrix.csv
- native_pair_matrix.csv
- bridge_assessments.csv
- REPORT.md
- THEOREMS.md
- `INVENTED_RELATION_BRIDGE.md`, `invented_relation_bridge.py`, and
  `INVENTED_RELATION_SIGNATURES.json`: independent Schaefer classification of
  the bounded language inventor catalog.
- `BACKDOOR_THEOREM.md`, `backdoor_solver.py`, and `BACKDOOR_RESULTS.json`:
  supplied strong Horn/affine backdoor solver with an independent replay in
  `BACKDOOR_REVIEW.py`.
- `PARAMETERIZED_EDGE_THEOREM.md`, `parameterized_edges.py`, and
  `PARAMETERIZED_EDGE_RESULTS.json`: dimension-FPT and distance-XP routes for
  the affine/cardinality hard edge, independently replayed by
  `PARAMETERIZED_EDGE_REVIEW.py`.
