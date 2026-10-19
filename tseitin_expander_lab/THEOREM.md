# Odd-charge Tseitin CNF certificate

Let `G=(V,E)` be a connected graph, give each edge `e` a Boolean variable
`x_e`, and assign a charge `c_v` in `{0,1}` to every vertex. The local
constraint at `v` is

`XOR_{e incident to v} x_e = c_v`.

`tseitin.py` encodes that constraint exactly as CNF by adding one clause for
each incident-edge assignment with the wrong parity. The encoder therefore
has no relaxation step: a Boolean assignment satisfies the local clauses if
and only if it satisfies the parity equation.

Every edge occurs at exactly two vertices. XORing all vertex equations cancels
each edge variable, leaving `0 = sum_v c_v (mod 2)`. Consequently an odd total
charge is an exact, all-input unsatisfiability certificate. The independent
reviewer reconstructs the incidence map and every forbidden local assignment,
checks the odd-charge identity, and replays the saved first-UIP resolution
trace without importing the encoder.

The finite campaign uses four named connected cubic graphs and a deterministic
Möbius-ladder family with even sizes 6 through 20; every case places charge one
at vertex zero. Its purpose is to test the proof-producing SAT baseline against
a canonical parity family and a reproducible size sweep. The
[Ben-Sasson--Wigderson width-size tradeoff](https://people.inf.ethz.ch/emo/SatSem05/Papers/BensassonWidgerson01.pdf)
and the expansion literature provide the all-size resolution lower-bound
context for Tseitin contradictions; this repository does not reprove that
theorem. The observed Möbius-ladder conflict counts are measurements of this
fixed CDCL policy, not an all-size formula, a uniform-expander claim, or a
lower bound on every SAT algorithm.
The saved timings and CDCL proof lengths are measurements of one solver, not
lower bounds on every SAT algorithm and not a resolution of P versus NP.

Run the campaign from this directory:

```text
python run_experiments.py
python INDEPENDENT_REVIEW.py
python -m unittest -v test_tseitin.py
```
