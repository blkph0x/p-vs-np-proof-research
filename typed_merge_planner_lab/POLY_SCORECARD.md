# Polynomial scorecard

| Component | Status |
|---|---|
| Bounded relation Schaefer signature inference | polynomial in explicit truth table |
| Pair common-polymorphism classification | polynomial |
| Native closed-pair lookup | constant/table lookup |
| TT bridge admissibility | exact 2^k cost check |
| Extension-quotient admissibility | polynomial given certified q-state quotient |
| Supplied Horn/affine backdoor solver | `2^k * poly(explicit relation tables)`; backdoor is an input |
| Affine/cardinality dimension route | FPT in supplied code dimension `k`: `2^k * poly(n,k)` |
| Affine/cardinality distance route | XP in supplied distance `d`: `sum C(n,s) * poly(n,k)` |
| Greedy merge planner | polynomial |
| Exact subset merge planner | exponential audit only |
| Horn+Affine wide combination | known hard barrier |
| Affine+Cardinality wide combination | known NP-hard barrier |
| Universal legal merge-tree existence | unresolved |
| General SAT | unresolved |
