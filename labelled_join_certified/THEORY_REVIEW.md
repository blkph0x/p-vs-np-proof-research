# Independent theory review: labelled terminal subsets and incidence perturbations

Reviewed on 2026-10-18. The conclusions below concern a supplied and checked
representation. They do not claim a method for finding such a representation
for every binary matrix, or a polynomial algorithm for general minimum
distance. This is a mathematical review, not a machine-checked formal proof.

## Arbitrary-terminal recurrence

Let G be an undirected multigraph with distinct edge IDs, nonnegative weights,
and labels in GF(2)^p. Loops have zero boundary; parallel edges remain distinct.
Put K=2^p. Let d(v,w,a) be the shortest lifted-walk distance from (v,0) to
(w,a). Let E(z) be the minimum weight of an even-degree edge subset of label
z, computed by the closed-walk label-space closure proved in
`../LABELLED_JOIN_REVIEW.md`. Infeasible values are infinity.

For every even terminal set S, define

    F(empty,z) = E(z),
    F(S,z) = min_{w in S-{v}, a in GF(2)^p}
                 [d(v,w,a) + F(S-{v,w}, z XOR a)],

where v is a fixed deterministic choice from S, such as its least vertex.
Then F(S,z) is exactly the minimum weight of an edge subset with odd-degree
boundary S and label z. Odd-size terminal sets are infeasible.

Proof by induction on |S|: every connected component has an even number of
odd-degree vertices. Thus a feasible edge subset with v in its boundary has
a simple path from v to another boundary vertex w. Removing that path
changes the boundary to S-{v,w}; its label a changes the residual target to
z XOR a. The recurrence term is at most this solution's cost, by the lifted
distance bound and the induction hypothesis. Conversely, XOR a realizing
lifted walk with the inductively constructed residual support. The result
has exactly the requested boundary and label. Its cost is no greater than
the sum, since cancellation of repeated edge IDs cannot increase cost for
nonnegative weights. This gives the reverse inequality and proves equality.
The argument also proves feasibility in both directions, so it covers
infinity cases and disconnected graphs.

The empty-set base must use E(z), not just zero when z=0 and infinity
otherwise: the solution may contain labelled cycles in components with no
terminals. Reconstructed walks can repeat original edges; reconstruction
therefore uses XOR of original IDs rather than set union. The final optimum
support has exactly the scalar optimum weight by the two inequalities, even
though an individual lifted walk's XOR support may cost strictly less than
that walk.

For t=|T|, compute F(S,z) for even subsets S of the supplied terminal set T.
There are at most 2^t K states, with at most tK candidate transitions each.
Thus O(2^t t K^2) scalar arithmetic operations suffice after the lifted and
Eulerian tables, with O(2^t K) scalar entries and corresponding reconstruction
data. A looser O(2^t t^2 K^2) bound is also valid. This improves enumeration
of all terminal pairings but remains exponential in t. Intermediate subset
states can be infeasible even when other states are finite.

## Supplied incidence-column perturbation

Work over GF(2). Suppose a parity-check matrix is supplied in the form

    H = B + U V,

where B is a reduced graph incidence matrix on r rows and m edge columns,
U has r rows and p columns, and V has p rows and m columns. Each column of
B and each column of U must have Hamming weight at most two. Weight-zero
B columns are graph loops; weight-one B columns join their indicated vertex
to a common ground vertex; weight-two columns join their two indicated
vertices. V's edge columns supply the p-bit labels. No column-independence
assumption on U or V is needed, although dependent labels may make some
branches infeasible.

For a reduced syndrome y define its full incidence extension by

    ext(y) = (y, XOR of all coordinates of y).

This map is linear. Each extended B or U column is an even vector of weight
at most two. The equation Hx=s is therefore equivalent, after fixing the
edge-label sum z=Vx, to the graph request

    boundary(x) = ext(s + U z),   label(x) = z.

Enumerating all K labels and solving their labelled-join requests is exact.
The same x is used in both equations: z is a constraint on the selected
edges, not an independent variable that can be selected without enforcing
Vx=z.

For the homogeneous case s=0, each target terminal set has size at most 2p,
because ext(Uz) is an XOR of at most p vectors of weight at most two. Hence
the terminal-subset recurrence takes 2^{O(p)} times a polynomial in the
explicit matrix/graph input. Enumerating all K label branches preserves
this bound. An arbitrary affine target s may itself have many terminals;
no comparable parameter-p bound follows without a bound on ext(s).

## Homogeneous nonzero solutions by pinning

The unrestricted homogeneous minimum admits x=0. To obtain a nonzero
minimum, pin each original edge coordinate e to one, remove that coordinate
from the residual graph and matrices, solve

    H_(E-{e}) x = H_e,

and add the weight of e. Every nonzero support contains some e, while
deletion guarantees the reconstructed support really contains the pinned
edge. Taking the minimum over all m pins is exact; with m=0 the nonzero
problem is infeasible.

In a residual label branch z=V_(E-{e})x, its graph boundary is

    ext(H_e + Uz) = ext(B_e + U(V_e + z)).

Its terminal count is at most 2+2p, even when the raw H_e column is dense.
The additional two terminals come from the original graph column B_e;
loops contribute none. Thus all pin/label branches can be solved in
deterministic 2^{O(p)} times polynomial input size, using nonnegative edge
weights. For unit weights this gives minimum nonzero Hamming weight for
this supplied class. Zero-weight edges do not undermine pinning: a nonempty
optimum may legitimately have weight zero.

This argument does not cover arbitrary rank-p perturbations. The bound uses
the incidence support of every U column in the same row basis in which B
is a graph incidence matrix. If a row change P is used, its invertibility
and the identity PH=B+UV must be checked, and an affine target must be
transformed as Ps. The decomposition equality and both incidence conditions
are efficiently checkable. Existence or efficient discovery of such a
decomposition is a separate question.

## Certification and resource limits

Correct scalar recurrences alone do not certify a producer's output. The
distance tables need source-rooted realizing paths, Bellman lower-bound
potentials, and reachability closure. In particular, locally consistent
zero-cost predecessor cycles must be rejected unless the alleged paths
actually reach their specified source. The Eulerian label closure requires
the same checks on its label graph, including all closed-walk minima over
base vertices.

A future certificate for the arbitrary-terminal recurrence must cover every
required subset/label state and every candidate in its minimum, and provide
reconstructible choices. A global pinned optimum must cover every pin and
label branch, or justify omitted branches by certified lower bounds. If a
budget prevents this coverage, feasible reconstructed supports provide upper
bounds only; the answer must remain UNKNOWN rather than assert an exact
optimum or infeasibility.

The certified-table implementation currently targets exact nonnegative
integers. The mathematical route extends to nonnegative rational weights by
clearing denominators, whose total bit length grows only polynomially in the
encoded input. That extension is not an assertion that an integer-only API
accepts rational objects.

## Independent certificate implementation checks

`test_labelled_tables.py` contains an exhaustive support oracle independent of
the shortest-path producer. Fourteen tests passed on 2026-10-18 in 0.806
seconds. The primary graph coverage consists of all 761 one-bit labelled
simple graphs through four vertices, all 325 two-vertex multigraphs with at
most two edges chosen from all endpoint/loop, two-bit label, and zero/one
weight types, and 120 seeded weighted multigraphs with up to eight edges.
For each graph the tests compare all labels and zero/two-terminal requests
against original edge-subset enumeration. Seeded cases also check every
lifted witness's boundary, label, and cost bound.

Targeted tests cover disconnected label corrections, a lifted walk of cost
204 whose XOR support costs four, exact 10^120-scale weights, empty graphs,
p=0, saved JSON reload, and snapshot isolation after external certificate
mutation. Adversarial certificates include false unreachability, zero-cost
predecessor cycles in both graph levels, a realizing but suboptimal lifted
path, forged closed-walk minima and sources, malformed schemas and indices,
boolean numeric fields, and mismatched graph inputs. Exact producer and
verifier budget boundaries are tested: insufficient coverage yields UNKNOWN,
not a partial exact certificate. No correctness issue was found in this
review or finite test set; neither constitutes a formal verification of the
implementation.

## Independent terminal-subset and nonempty-wrapper review

The implemented `labelled_tjoin.py` recurrence, complete DP coverage, support
reconstruction, original edge-ID remapping after a pin, and external terminal
and label binding were reviewed separately from the producer's own tests.
Zero optimum weights are handled as finite values rather than as absence of
a candidate. Odd terminal cardinality is correctly an immediate infeasibility
proof. A nonempty request with nonzero boundary or label can use the ordinary
solver directly; only the empty-boundary, zero-label request needs pinning.

This audit found and reported a resource-status bug: the producer's reachable
arc scans cannot bound the verifier's scans from all base sources, including
unreachable lifted states. An isolated zero-cost loop on four vertices with
a search-relaxation cap of one exposed it. The root implementation was fixed
to separate verification-arc limits, preserve UNKNOWN from exhausted table
verification through both wrappers, and use declared limits for its final
self-check. The exact regression was rerun successfully. This was a budget
and error-status issue, not acceptance of a false optimum.

An additional independent in-memory test enumerated original edge subsets
for 100 seeded weighted multigraphs with one to five vertices, up to seven
edges, and zero to two label bits. Three ordinary budget configurations and
three nonempty pin limits per graph gave 600 comparisons, including 241
UNKNOWN outcomes. All exact values agreed with the oracle. Every reported
partial nonempty upper bound had a nonempty original support with the right
label, boundary, and weight. Wrong externally supplied targets and forged
empty witnesses were rejected. Ordinary UNKNOWN results contained neither
an optimum nor a witness; nonempty UNKNOWN results retained only bounds from
completed, verified pin cases.

## Independent normal-form and coverage review

The constructive and minor-closure arguments in `COVERAGE_AUDIT.md` were
independently checked. For sparse-incidence U, choose a forest basis U_F.
Subtree-cut rows P satisfy P U_F=I, and component-sum rows Q satisfy QU=0.
The rows of S=[P;Q] are independent: multiplication by U_F first eliminates
the P coefficients, then the disjoint nonempty component supports eliminate
the Q coefficients. Thus S is invertible, and

    SH = [PB+(PU)V; QB] = [L; A],

where A is a graph incidence matrix after contracting the auxiliary forest.
All original coordinates remain present; some may become loops or parallel
edges. The number of arbitrary label rows is rank(U), not the number of
possibly dependent supplied U columns. Conversely, [L;A] has the sparse-U
representation B=[0;A], U=[I;0], V=L.

This normal form simplifies the homogeneous route beyond the earlier direct
terminal bound. A homogeneous word satisfies Ax=0 and Lx=0: it is precisely
a zero-label even-degree graph subset. Pinning e leaves graph boundary A_e
and label L_e, with zero or two terminals. The general terminal-subset DP is
therefore unnecessary for this normalized homogeneous problem, although it
remains useful for affine requests whose graph syndrome has many terminals.

The class with at most p arbitrary rows above a graphic block is closed under
matroid minors. Deletion is immediate. To contract a column whose graphic
part is nonzero, pivot a graph endpoint row, perform graph-edge contraction,
and clear the same column from arbitrary rows; their number remains p. If
the graphic part is zero but the arbitrary part is nonzero, pivot an arbitrary
row, reducing its count by one and leaving the graph block unchanged. A
fully zero column can be deleted. These operations also handle redundant
rows and graph loops.

For a linear extension K(x,y)=0, existential elimination of y replaces each
original column by its class modulo the span of the auxiliary columns. This
is contraction of those columns, so the projected code remains in the same
at-most-p-row graphic-lift class. Arbitrarily many linear auxiliary variables
with exact coordinate projection cannot enlarge this fixed-p coverage.
Combining closure with the same-coordinate count in `COVERAGE_AUDIT.md`
rules out universal logarithmic-p coverage for that encoding format. This
does not address nonlinear encodings or arbitrary output maps whose objective
must be proved separately. Nonzero original support must also be enforced on
original coordinates; a nonzero auxiliary support can project to zero.

The finite separation counts in that audit also check out. All 15 nonzero
four-bit columns have seven distinct nonzero images of rank three in every
one-dimensional quotient, exceeding the graphic bound six. Yet complementing
columns of weight at least three by 1111 gives a general rank-one perturbation
of an incidence matrix. For the 15 K6 incidence columns plus 11111, quotient
directions of reduced weights one/two, three/four, and five give respectively
11, 12, and 15 distinct nonzero rank-four images, all exceeding the graphic
bound ten. The unchanged rank-five case has 16 distinct nonzero columns,
exceeding the graphic bound 15. These are fixed-parameter representation
separations, not complexity lower bounds for unrestricted algorithms.

## Independent normalizer-to-code integration audit

The complete sources of `sparse_lift_normal_form.py` and `code_lift_solver.py`
were reviewed without modifying them. The implemented normalizer orders
component-indicator graph rows first and completes them with unit rows,
rather than using subtree-cut label rows. This is valid: in each non-ground
component the indicator plus all but one unit row form a basis, while all
non-ground vertex unit rows of the ground component are included. Thus its
row transform is invertible, the top rows annihilate U, and the remaining
row count is rank(U). Its independent verifier also checks the actual rank,
products, transformed syndrome, and incidence-column condition.

The normalizer is bound to its supplied factors B,U,V. The final code
certificate separately recomputes the row transform on the externally
supplied original H and checks its invertibility and graph-column condition.
Consequently correctness of that code certificate does not depend on
trusting the forest producer. The adapter transforms the affine target in
the same row basis, extends the graph syndrome by the parity ground vertex,
keeps every original coordinate ID and weight, and checks reconstructed
words against the original parity checks and objective. When custom weights
are supplied, its reported distance is that weighted objective, not Hamming
weight unless all weights are one.

An independent integrated test generated 150 sparse-U factorizations with
zero to five original rows, zero to eight coordinates, and zero to five
possibly dependent U columns. For each factorization it checked the normal
form and then compared weighted affine/nonzero code requests with exhaustive
enumeration of original supports. There were 450 code requests, including
75 UNKNOWN outcomes from pin limits. All exact optima matched; every returned
upper-bound word satisfied the original equations and had exactly the
reported weight. The cases included empty row/coordinate sets, dependent U,
zero weights, and both nonzero requirements. Mutating certified objective
weights was rejected against the externally supplied weights. The earlier
empty-pin verifier-cap validation issue was also checked after its fix.

No additional correctness or certification gap was found in this source
review and integration audit. The finite checks do not establish universal
coverage or replace the mathematical reduction proofs above.
