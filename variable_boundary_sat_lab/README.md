# Variable-boundary SAT lab

This lab solves arbitrary CNF on a supplied variable order by exact frontier
dynamic programming. It records every state and transition and independently
replays SAT and UNSAT certificates.

```text
python -m unittest -v test_boundary_dp.py
python run_experiments.py
python INDEPENDENT_REVIEW.py
python EXHAUSTIVE_SMALL_CHECK.py
```

The algorithm is fixed-parameter in supplied boundary width. Discovering a
small order for arbitrary CNF remains outside its claim.

The saved exhaustive check covers all 2,952 three-variable CNFs with at most
three clauses and all six orders, replaying 17,712 exact certificates against
brute-force SAT.

`REDUNDANCY_THEOREM.md` records a separate adversary: tautological clauses make
the raw primal frontier dense and retain exponentially many syntactic states,
while deleting those tautologies restores the width-one equality system. The
producer and independent replay preserve this as a preprocessing control, not
as a claim of semantic SAT hardness.
