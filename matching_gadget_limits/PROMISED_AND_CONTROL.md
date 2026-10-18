# Positive control: AND works on the promised paired domain

This additional exact example confirms that global validity and composition are the missing ingredients; individual promised-domain Boolean truth tables are possible. It does not provide a reduction from general Boolean circuits to matching.

Use six terminal vertices, no internal vertices, and logical pairs x=(0,1), y=(2,3), z=(4,5). As in THEOREM.md, logical zero deletes neither terminal of a pair and logical one deletes both. Give these five edges cost zero:

    (0,4), (1,5), (2,4), (3,5), (0,3).

The full feasible deleted-terminal masks are

    {0,3,6,9,12,20,23,29,34,43,46,54,63}.

Intersecting with the valid paired domain gives precisely {0,3,12,63}, representing the relation z=x AND y.

| x | y | z | Deleted mask | Perfect matching exists |
|---:|---:|---:|---:|:---:|
| 0 | 0 | 0 | 0 | Yes |
| 1 | 0 | 0 | 3 | Yes |
| 0 | 1 | 0 | 12 | Yes |
| 1 | 1 | 0 | 15 | No |
| 0 | 0 | 1 | 48 | No |
| 1 | 0 | 1 | 51 | No |
| 0 | 1 | 1 | 60 | No |
| 1 | 1 | 1 | 63 | Yes |

For mask zero, a matching is {(0,3),(1,5),(2,4)}. For mask 3, use {(2,4),(3,5)}; for mask 12, use {(0,4),(1,5)}; for mask 63, use the empty matching. The remaining valid states leave either the output pair without an edge, the input pairs with only one edge, or a single input pair without an edge, proving infeasibility directly.

The full physical relation is an even delta-matroid, while its restriction to valid pair encodings is not. Consequently the exact-support impossibility theorem and this positive promised-domain example agree. Invalid physical states must not be ignored during composition.

`PROMISED_AND_CONTROL.json` records every feasible boundary's exact matching witness, the complete expected domain intersection, and the source/input hashes. It was revalidated against the current bounded reference after adding the threshold-exchange checks; RESULTS.json also contains this control in the main reproducible experiment. Reproduce its core check with:

```python
from matching_boundary import boundary_signature, valid_domain, encoded_and
edges = [(0,4,0), (1,5,0), (2,4,0), (3,5,0), (0,3,0)]
signature = boundary_signature(6, edges, range(6))
assert set(signature) & set(valid_domain(3)) == set(encoded_and(2))
```
