# Non-graphic core adversary report

This increment addresses the next hard-frontier question in the project:
whether high trellis width can be dismissed as a consequence of graphic
structure. The answer from these controls is no. The matrices below contain a
certified Fano restriction, so they are non-graphic, and every cut was audited
for internal 4-connectivity.

| n | rank | exhaustive cuts | minimum balanced lambda | trellis states lower bound | minimum codeword weight |
|---:|---:|---:|---:|---:|---:|
| 18 | 9 | 131,071 | 3 | 8 | 3 |
| 20 | 10 | 524,287 | 4 | 16 | 3 |
| 22 | 11 | 2,097,151 | 4 | 16 | 3 |
| 24 | 12 | 8,388,607 | 5 | 32 | 3 |
| 26 | 13 | 33,554,431 | 5 | 32 | 4 |

The C++ audit checks all unordered cuts, rejects every 1-separation, and
rejects every nontrivial order-three separation. It permits only the standard
triangle/triad three-element exceptions. The independent Python replay scans
all cuts for the first two controls, recomputes the Fano certificate for all
five, checks the message-enumerated distances, and confirms every saved source
hash.

The result is an adversarial representation control, not a hardness theorem.
The balanced-cut lower bound forces large state tables for the trellis route,
but it does not rule out a different polynomial native algorithm for these
codes and says nothing by itself about SAT or P versus NP.

Reproduce with `python -m unittest -v test_non_graphic_core.py`,
`python run_experiments.py`, and `python INDEPENDENT_REVIEW.py`.
