# Adaptive bounded proof-fragment synthesis

**Status:** completed independent bounded cross-check. It does not prove P=NP or P!=NP.

The checkpoint already contains a broader bounded language-invention lab. This
file is an independent, smaller reimplementation used to cross-check that
route and to make the cap behavior and hard controls executable in isolation.
It discovers a candidate relation from a residual proof fragment without a
benchmark-family label. The input is an explicit CNF fragment and a declared
shared interface.
Variables outside that interface are existentially projected. The synthesizer
enumerates the bounded interface and local assignments, then tests a fixed
language vocabulary:

- a unit relation;
- one affine/XOR equation;
- an unweighted PB threshold;
- a four-variable ITE gate;
- an explicit truth table as a fallback for small interfaces.

Every proposed object carries the complete projection work and a representation
size estimate. `verify_adaptive_fragment_synthesis.py` is a separate checker; it
does not import the synthesizer and independently recomputes the projection and
candidate semantics.

The saved run has eleven unit tests and seven serialized examples. It rediscovers
the exact XOR relation, ITE relation, AMO/PB threshold, and the unit relation
behind a five-variable OR-collapse fragment. A fourth local variable forced by a
unit is existentially projected away while preserving the XOR result. Removing
one XOR clause rejects the XOR candidate and leaves only the explicit table.
The nonlinear three-variable relation `x0 OR (x1 AND x2)` also receives only the
table fallback, so the implementation does not silently relabel every small
relation as a recognized compact language.

The two hard controls are explicit. A projection budget of one assignment returns
`UNKNOWN`, and the `n=5,k=3` clique-versus-2-coloring control has ten shared edge
variables, exceeding the six-variable synthesis cap, so it also returns
`UNKNOWN`. This is the correct behavior for the bounded algorithm; it is not a
hardness proof for all candidate languages.

For a fragment with `s` shared and `l` local variables, projection costs
`2^(s+l)` assignment checks times the number of clauses. Candidate testing adds
the explicit fixed-vocabulary work: `2^s` truth-table evaluations for each
unit, threshold, role, XOR-support, and fallback proposal. The saved
`discovery_work` includes both terms and the implementation fails closed when
either support or assignment caps are exceeded. Thus this experiment supplies a
checkable, finite adaptive discovery step, while leaving the central unresolved
problem visible: a general proof may need a relation of unbounded interface size
or a language whose recognition is itself hard.

Artifacts:

- `adaptive_fragment_synthesis.py` — bounded synthesizer and certificate data;
- `test_adaptive_fragment_synthesis.py` — positive, mutation, projection,
  budget, and clique-coloring controls;
- `verify_adaptive_fragment_synthesis.py` — independent replay;
- `ADAPTIVE_FRAGMENT_SYNTHESIS.json` — serialized results.
The same bounded extractor can take the leaves of an actual motif-miner
resolution sub-DAG. It visits all nine nodes of the five-variable OR-collapse
proof and refuses the same request when the node cap is eight, so proof ancestry
is not silently truncated before synthesis.
