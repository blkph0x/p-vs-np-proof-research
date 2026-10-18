# Circuit boundary audit

`circuit_cnf.py` builds the XOR/AND Hamming-weight circuit from the nonlinear
compression control and emits a Tseitin CNF with a topological variable order.
`run_experiments.py` pins every source assignment in a seven-form, five-bit
control, asks the proof-producing frontier SAT solver for the exact output
weight and a deliberately wrong output, and saves the boundary width and
certificate statistics. `INDEPENDENT_REVIEW.py` checks gate truth tables,
output values and boundary scopes without trusting the producer's evaluator.

The result tests the real integration bottleneck: compact nonlinear output
does not automatically give compact SAT search. The circuit is polynomial-size
in the explicit source forms, but the frontier solver remains exponential in
its active boundary. No general SAT or P-versus-NP claim is made.

Run:

```text
python run_experiments.py
python INDEPENDENT_REVIEW.py
python -m unittest discover -v
```
