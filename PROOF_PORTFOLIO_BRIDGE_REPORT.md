# Proof-DAG to invented-interpolant bridge

**Status:** completed bounded integration. No proof of P=NP or P!=NP.

This experiment connects the independent bounded relation projector to the actual
resolution proof used by `proof_portfolio_integration_lab`.

For the saved `g=8`, `w=4` refutation:

1. The proof engine constructs 65 resolution nodes and an empty root clause.
2. The bridge scans the proof graph for the eight positive unit nodes rather than
   using group labels.
3. It extracts each unit node's seven-node leaf sub-DAG.
4. It projects the four-variable leaf fragment onto its one representative
   boundary variable.
5. The exact relation inventor independently recognizes the resulting relation as
   `representative = true`.
6. Those eight certified source facts are combined into the existing XOR
   interpolant over the representatives. The receiver requires the opposite
   parity, so the source and receiver certificates disagree exactly.

Every fragment also retains its raw clauses, projected truth table, candidate
catalog, proof-node index, and visited-node count. The separate checker
recomputes each existential projection and evaluates every serialized candidate;
it does not import the synthesizer or the proof engine. It also replays all 65
resolution nodes from the serialized A/B proof certificate and independently
reconstructs the empty root clause.

The same bridge was also run at the larger `g=256`, `w=8` scale. It processed
4,097 proof nodes and 256 unit sub-DAGs, retained 256 raw interpolant literals,
and passed the symbolic receiver check in 0.575 seconds on the saved run. The
large result is stored as a compact summary; the small case retains the full
per-fragment certificates.

As a label-free control, a scanner treated every nonempty proof clause of
boundary arity at most two as a possible sub-DAG boundary. Among 42 considered
nodes it found 16 exact compact relations (eight units and eight PB relations),
24 exact but noncompact table relations, and two honest `UNKNOWN` cases. The
scan uses the derived clause as the boundary and independently projects the
complete leaf fragment; it does not assume the known group partition.

The integration passes four focused tests plus the independent replay. A node cap
below seven fails closed. The `n=5,k=3` clique-versus-2-coloring control has ten
shared edge variables and returns `UNKNOWN` under the six-variable cap, so the
bridge does not turn a classical hard interpolation interface into a spurious
local candidate.

This closes one plumbing gap: a proof-derived relation can be invented and
certified from actual proof-DAG structure before receiver-side language selection.
It does not establish that arbitrary refutations decompose into bounded
interfaces. That interface-growth question remains the universal obstacle.

Artifacts:

- `proof_portfolio_bridge.py` — integration and artifact producer;
- `verify_proof_portfolio_bridge.py` — independent replay;
- `test_proof_portfolio_bridge.py` — bounded integration and hard-control tests;
- `PROOF_PORTFOLIO_BRIDGE.json` — serialized proof and relation certificates.
