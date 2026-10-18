# Repeated proof-DAG template discovery

**Status:** completed bounded, label-free scan. No proof of P=NP or P!=NP.

The earlier bridge inspected the known positive unit nodes. This experiment
removes those group labels and scans every nonempty proof node whose proposed
boundary has at most two variables. For each candidate it extracts the complete
leaf sub-DAG under an explicit 32-node cap, projects local variables exactly,
and runs the bounded unit/XOR/PB/ITE/table synthesizer.

The 65-node proof yields 42 considered nodes:

- 16 `FOUND` compact relations: eight unit templates and eight two-variable PB
  templates;
- 24 `NO_COMPACT` table-only relations;
- 2 explicit `UNKNOWN` results when the leaf sub-DAG exceeds the cap.

Canonicalization renames variables by their sorted boundary positions. It finds
three repeated templates with occurrence counts 8, 8 and 24. Reuse is measured
without hiding semantic work: every occurrence still pays its full exact
projection cost, while only the fixed candidate-vocabulary search is amortized
after the first occurrence. The artifact records naive work, reused work, and
the resulting savings for each template.

The same scan was serialized and replayed on the 4,097-node, 256-group proof.
It considers 2,306 small-boundary nodes: 256 compact PB relations, 1,792
table-only relations, and 258 `UNKNOWN` cases. Two of those exceed the
sub-DAG cap; the other 256 exceed the local-projection cap. The two repeated
scale templates occur 256 and 1,792 times. Their full records remain in the
artifact so the independent checker can verify the scale result rather than
trusting a summary.

A one-step cap sweep changes the result in a controlled way. Raising the local
cap from 6 to 7 recovers all 256 one-variable unit templates: the scan then
has 512 compact relations, 1,792 table-only relations, and only the two
sub-DAG-cap `UNKNOWN` cases. The artifact stores and independently replays both
cap settings, making the interface-growth effect explicit rather than folding
it into a success claim.

The separate checker replays all 65 resolution nodes, independently extracts
each leaf sub-DAG, recomputes every projection and candidate truth table, and
rebuilds the template groups from serialized records. It also rejects a forged
candidate mutation. Thus repeated syntax is evidence for a reusable template,
not an uncharged equivalence oracle.

This demonstrates a possible proof-portfolio optimization on a structured
family. It does not show that arbitrary proofs have bounded interfaces, that
template discovery is polynomial, or that reused relations solve general SAT.

Artifacts:

- `repeated_subdag_templates.py` — bounded label-free scanner and work ledger;
- `verify_repeated_subdag_templates.py` — independent proof/projection replay;
- `test_repeated_subdag_templates.py` — counts, reuse accounting, and adversarial test;
- `REPEATED_SUBDAG_TEMPLATES.json` — serialized proof, records, and templates.
