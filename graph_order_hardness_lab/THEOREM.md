# Order-discovery hardness is separate from SAT hardness

For a graph $G=(V,E)$ and a variable order $\pi$, define the prefix boundary at
cut $k$ by

\[
B_\pi(k)=\{v\in P_k:\exists w\notin P_k,\{v,w\}\in E\}.
\]

The vertex-separation width of the order is
$\max_k |B_\pi(k)|$. The lab computes the exact minimum width on small graphs
by subset dynamic programming and emits every boundary as a certificate.

Map $G$ to the monotone 2-CNF

\[
F_G=\bigwedge_{\{u,v\}\in E}(x_u\lor x_v).
\]

This formula is always satisfiable: the all-ones assignment is a witness. A
variable-order planner that carries every already-seen variable with a future
neighbor has exactly the boundary $B_\pi(k)$ as its active-variable interface.
Thus minimizing that structural interface on this always-satisfiable family is
precisely the vertex-separation problem; it is not a disguised SAT decision
instance.

Kinnersley proved that vertex separation equals pathwidth
([1992 paper](https://www.sciencedirect.com/science/article/pii/002001909290234M)).
Vertex separation/pathwidth recognition is known NP-complete, including
restricted graph classes (see the Monien–Sudborough result summarized in
[this open graph-complexity paper](https://www.combinatorics.org/ojs/index.php/eljc/article/download/v32i3p36/pdf)).
Therefore a universal optimizer that always discovers the minimum active-variable
order would solve an NP-complete layout problem even on formulas with trivial
SAT witnesses.

This is a barrier for that particular order-discovery objective, not a proof that
SAT is hard and not a P-versus-NP resolution. A solver may use a nonoptimal order,
a different representation, or a stronger theorem. The exact oracle here is
exponential and exists to charge the discovery cost honestly.

## A local greedy policy is not enough

Consider $K_{m,2}$ with leaf vertices $0,\ldots,m-1$ and two hubs. The
min-boundary greedy rule with lowest-index tie-breaking chooses the leaves first:
each next leaf initially creates only one active vertex, so it ties the hub
choice. After all leaves, the boundary has size $m$. Processing the two hubs
first gives width at most two. Thus this polynomial local rule has an
approximation ratio at least $m/2$ on this family. The saved $K_{4,2}$ control
has greedy width 4 and exact width 2, with independent replay.
