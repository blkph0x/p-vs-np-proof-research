# Hidden-affine representation discovery experiment

This bounded experiment asks whether a short projected representation can coexist with high work for one explicitly declared discovery procedure. It is an experiment about algorithms and accounting, not a lower bound for SAT, representation discovery in general, or P versus NP.

The family encodes one even-parity equation on `m` shared variables as a chain of 3-CNF XOR gadgets. The chain has `m-1` existential helper variables. Its projection therefore has a one-equation XOR description. The original procedure enumerates all shared/helper assignments and then tests every nonempty XOR support and both right-hand sides.

## Two discovery procedures

`enumeration_discovery_work` is the exact charged work of that fixed projection-and-candidate procedure. `exhaustive_replay_work` is the exact charged work of its exhaustive replay. They are procedure costs, not minima over algorithms and not lower bounds.

The separate `gaussian_baseline.py` recognises the constant-size XOR gadgets, then propagates affine expressions over GF(2) by substitution (the chain-specialised form of Gaussian elimination). It recovers the same parity support without constructing the projected truth table. Its `work` field is an explicit implementation charge for this baseline, included to make the comparison auditable rather than to claim a universal complexity measure.

The encoded representation size is named `encoded_representation_bits`: it is the bit count for this repository's support-label encoding. It is not a proof of minimum representation length.

| shared variables | helpers | clauses | encoded bits | enumeration work | exhaustive replay | GF(2) baseline |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 2 | 9 | 15 | 408 | 288 | recorded in `RESULTS.json` |
| 4 | 3 | 13 | 17 | 2,160 | 1,664 | recorded in `RESULTS.json` |
| 5 | 4 | 17 | 24 | 10,720 | 8,704 | recorded in `RESULTS.json` |
| 6 | 5 | 21 | 27 | 51,136 | 43,008 | recorded in `RESULTS.json` |
| 7 | 6 | 25 | 30 | 237,440 | 204,800 | recorded in `RESULTS.json` |

For `m` shared variables:

```text
local variables            = m - 1
CNF clauses                = 4m - 3
encoded bits               = 9 + m ceil(log2 m)
exhaustive replay work     = (4m - 3) 2^(2m - 1)
candidate-search work      = (2^(m + 1) - 1) 2^m
enumeration discovery work = (4m - 3) 2^(2m - 1) + (2^(m + 1) - 1) 2^m
```

The projection count follows from `2^(m+(m-1))` assignments. The candidate vocabulary has `2(2^m-1)+1` entries. Thus the declared enumeration procedure has Θ(m4^m) charged work while its particular encoded support has Θ(m log m) bits. The GF(2) baseline gives a polynomial structural control for the same family, so the exponential separation is algorithm-specific evidence.

## Controls and nonlinear boundary

`RESULTS.json` includes three syntactic controls at `m=5`: reversed gadget order, a duplicated redundant gadget, and a bijective renaming of all variables. The baseline recovers the same affine relation in each case. These controls test robustness to superficial hiding; they do not make discovery hard.

The companion nonlinear control tests a Boolean relation that is not affine. The baseline must return `NOT_AFFINE`/`UNKNOWN` rather than silently treating a nonlinear projection as an XOR equation. This keeps affine recovery and nonlinear representation questions separate.

`independent_review.py` rebuilds the chain and projection without importing the producer, checks every saved formula, and checks the baseline outputs and controls. The tests also exercise reordered, duplicated, renamed, and malformed inputs.

The supported conclusion is narrow: a compact projected representation can coexist with high work for one explicit exhaustive synthesizer. A meaningful discovery barrier would require a reduction or theorem covering a broad, well-defined class of algorithms, including methods that bypass this representation.
