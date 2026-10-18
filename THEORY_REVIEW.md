# Native graph optimization after conditioning: theory review

Reviewed 2026-10-18. These are elementary proofs, established algorithmic facts,
and explicitly limited proposals. Nothing here resolves P versus NP.

## 1. The essential distinction

For a graph G with binary vertex-edge incidence matrix B, write

    Z(G) = ker(B)                 cycle-space code
    K(G) = rowspace(B)            cut-space code.

The names describe the code itself, avoiding ambiguity about whether its
generator matroid or parity-check matroid is graphic. Homogeneous minimum
nonzero weight is easy for both: shortest cycle for Z(G), and minimum nonempty
edge cut for K(G). Their affine and conditioned versions behave differently.

For disconnected G, global mincut over arbitrary nontrivial vertex subsets can
be zero. That zero cut is not a nonzero codeword. Minimum nonzero cut-code weight
instead minimizes the positive cut value within nontrivial connected components.
This repairs the unrestricted-graph wording in the earlier high-width theorem;
its complete-graph examples were unaffected.

## 2. Cycle-space affine cosets and coordinate conditioning remain tractable

Consider the affine equations Bx=t over GF(2), with nonnegative edge costs.
The support of x has odd degree exactly at T={v:t_v=1}; it is a T-join.
It exists exactly when every connected component contains an even number of
vertices of T. Necessity follows by summing degrees in a component. Sufficiency
follows by pairing terminals within each component and taking the symmetric
difference of paths joining the pairs.

For each component, construct the complete metric graph on its terminals, with
edge costs equal to shortest-path distances in G. Find a minimum-weight perfect
matching, and XOR the original edge IDs along shortest paths for its pairs.
The result has boundary T. Repeated original edges cancel modulo two.

**Optimality proof.** Any T-join decomposes into terminal-pair trails and cycles.
Removing cycles cannot increase nonnegative cost, and replacing trails by
shortest paths gives a terminal perfect matching of cost at most the T-join.
Conversely a terminal perfect matching yields, by path XOR, a T-join of cost at
most the matching. The two optimum values are therefore equal. The exact
matching algorithm is polynomial. See Edmonds and Johnson's primary research
paper on matching and postman optimization:
[Matching, Euler tours and the Chinese postman (1973)](https://doi.org/10.1007/BF01580113).

Fixing edge coordinates D to b in a cycle code leaves

    B_R x_R = B_D b,       total weight = |b| + |x_R|.

Thus each feasible branch is still a T-join on the residual graph. If b is
nonzero, x_R=0 is permitted when its target is zero, because the full word is
already nonzero. If b=0 and the required full word is nonzero, the residual
problem is the shortest **nonempty cycle**, not the zero-cost empty T-join.

The same distinction applies to arbitrary affine cosets: when t is nonzero,
all feasible x are nonzero; when t=0, the nonzero condition must be handled.

Implementation details required for correctness:

- A zero incidence column is a loop. It has zero boundary and, in the unweighted
  nonzero problem, supplies a length-one cycle.
- Distinct equal nonzero columns are parallel edges, not duplicate data to
  discard. Two form a length-two cycle.
- Keep original coordinate IDs when reconstructing paths and taking XORs.
- For shortest cycles in a multigraph, remove one **edge ID** at a time and
  find a shortest path between its endpoints; other parallel edges remain.
- An infeasible component is not an infinite numerical edge to pass to a
  matching solver. Detect its odd terminal count explicitly.

## 3. Arbitrary cut-space cosets already contain MaxCut

Given a binary edge vector y, every vector in y+K(G) has the form

    x_e = y_e XOR (s_u XOR s_v),       e=uv.

When y is the all-ones vector, its weight is exactly

    |x| = |E(G)| - |delta(s)|.

Consequently minimizing weight in this affine cut-code coset computes MaxCut.
The decision threshold maps K to |E(G)|-K. A feasible cut is a polynomial-size
witness. Unit-weight MaxCut is NP-complete by the primary result of Garey,
Johnson and Stockmeyer,
[Some simplified NP-complete graph problems (1976)](https://doi.org/10.1016/0304-3975(76)90059-1).

This is an NP-hardness reduction, not a proof that no polynomial algorithm
exists. It makes the missing general theorem as hard as P=NP. Requiring x to
be nonzero does not rescue generality: append a disjoint triangle to G. Its
all-ones coset contributes minimum weight one and cannot contain zero, so the
new optimum is |E(G)|-MaxCut(G)+1 and every feasible full vector is nonzero.

## 4. Even conditioning a homogeneous cut code can introduce MaxCut

Here is a separate reduction, requiring no arbitrary affine shift of the input
code. Start from a simple unweighted MaxCut instance F=(V,E), with vertices
indexed 0 through p-1. Build a bipartite graph G with vertices u_i,v_i:

1. Add D={u_i v_i : i in V} and require each of these cut coordinates to be 1.
2. For each original edge {i,j}, choose the orientation i<j and add u_i v_j.

The forced edges form a matching. For any feasible cut, write s_i for the label
on u_i. The label on v_i must be 1 XOR s_i. Therefore its new edge u_i v_j is
cut exactly when s_i=s_j, and

    conditioned minimum cut-code weight = p + |E| - MaxCut(F).

Conversely every original vertex assignment determines such a feasible cut.
The construction has 2p vertices and p+|E| edges and uses only unit costs. The
full codeword is automatically nonzero because every matching edge is fixed
to one. Thus the conditioned cut-code minimum-weight decision problem is
NP-complete even for a bipartite underlying graph and matching fixed edges.

Read-only independent enumeration checked this equality on all graphs with at
most four vertices and 40 seeded five-vertex samples: 115 graphs total. This
finite audit supports the implementation-level formula; the preceding direct
bijection is the proof for all instances.

There is no contradiction with ordinary mincut being polynomial: mincut can
choose a solution that does not satisfy the additional opposite-label pairs.
Conditioning preserves affine membership but can destroy the useful native
optimization interpretation.

Useful positive subcases remain. Fixing only zero cut coordinates contracts
their edges and leaves a cut problem; the nonzero caveat above still applies.
Fixing a single edge to one is an s-t mincut. More generally, solving the fixed
edge parity constraints gives one flip variable per fixed-edge component.
The remaining objective is a signed pairwise binary objective, and only when
its resulting structure has an appropriate tractability certificate should it
be dispatched to an ordinary cut solver.

## 5. Certified exceptional-column reduction to T-joins

Let C=ker(H), and suppose an invertible binary row transformation P is supplied.
Let A=PH. Let D be q exceptional columns, with every column in R=E-D having
Hamming weight at most two. A certificate must verify P is invertible and
PH=A; merely asserting a discovered row change does not suffice.

Construct a graph with one vertex per row of A plus a ground vertex g:

- Weight-two column: edge between its two row vertices.
- Weight-one column: edge between its row vertex and g.
- Weight-zero column: a loop at g, retaining its coordinate ID.

For an assignment a to the exceptional coordinates, the required nonground
boundary is t=A_D a. Add g to the terminal set iff |t| is odd. The graph
incidence equations, including ground, are now equivalent to

    A_R x_R = A_D a.

The ground equation is the sum of the nonground equations. Check feasibility
component by component, solve a minimum T-join, and charge |a|. When a=0 use
the minimum nonempty residual cycle instead. Minimize over all 2^q assignments
and reconstruct the full original-coordinate word. Because P is invertible,
checking the original Hx=0 confirms membership in the intended code.

The implemented API also accepts an arbitrary original-basis syndrome s for
Hx=s. It transforms that syndrome by the same P and uses branch target
Ps XOR A_D a. The shortest-nonempty-cycle special case is needed only when
the caller requires a nonzero word, the fixed exceptional support is empty,
and this residual target is zero. All other branches use ordinary minimum
T-joins. The certificate verifier receives the requested syndrome and nonzero
condition separately and compares them with the recorded metadata; a valid
certificate for another request must not be silently accepted.

This proves an exact algorithm with cost 2^q times a polynomial graph/matching
cost, plus certificate verification and discovery. When q=O(log N), where N
is the binary input length, and the representation is found in polynomial
time, the whole procedure is polynomial. A bounded heuristic search may find
certificates but does not establish a polynomial discovery theorem. Budget
exhaustion must return UNKNOWN, optionally with a feasible upper bound.

**Implemented matching certificate.** Feasibility of a perfect matching and
its path XOR alone does not certify optimality. The current implementation
additionally exports NetworkX's final vertex and blossom dual variables through
a temporary observer, then checks them independently in `matching_certificate.py`.
Unsupported producer internals fail closed; the producer restores the previous
observer after the call. The certificate checker does not trust the extraction.

For maximum matching edge weights w, its integer certificate contains
nonnegative doubled vertex duals y_v and nonnegative odd-set duals z_B. It checks

    y_u + y_v + 2 sum_{B containing u,v} z_B >= 2 w_uv

on every edge, and checks the equality

    sum_v y_v + sum_B (|B|-1) z_B = 2 weight(returned matching).

These conditions prove optimality by weak duality: any matching uses each
vertex at most once and at most (|B|-1)/2 edges inside each odd set B. No
unverified optimality claim from the producer is needed. The independent
checker also validates all matching incidences and dual-set memberships.

For a componentwise complete terminal metric with distance d, the native solver
sets w_uv=L-d_uv, where L exceeds every finite distance. All weights are
positive. Since every terminal component has even size, a maximum-weight
matching must be perfect: any two unmatched vertices of one component could
be joined to improve it. Among perfect matchings the constant term is
|T|L/2, so the checked maximum-weight certificate proves minimum total distance.
The native verifier independently reconstructs graph distances, checks the
certificate on that metric, and checks the output edge support and boundary.
An independent girth algorithm handles the nonzero zero-target branch.

## 6. An all-size nonregular high-width family still has a native route

For t>=5, let H_t be the reduced binary incidence matrix of K_t, augmented by
the column g=e_1+e_2+e_3 on three distinct nonground rows. Write N_t for its
column matroid and C_t=ker(H_t). This gives a one-exception instance of section 5.

### Fano minor

Contract the edges joining every other nonground vertex to ground. Retain the
six edges of K4 on the three selected vertices plus ground, and retain g.
The quotient columns are the three unit vectors, their three pairwise sums,
and their triple sum: exactly F7. Thus N_t is neither graphic nor cographic,
as is its dual. The latter has an F7* minor. The generator matroid of C_t is
N_t*, so the code has neither a graphic nor a cographic generator matroid.
The primary forbidden-minor cross-check is Geelen and Gerards, page 75:
[Regular Matroid Decomposition Via Signed Graphs (2005)](https://www.math.uwaterloo.ca/~jfgeelen/Publications/regular.pdf).

### Internal 4-connectivity

Let M=M(K_t), already proved internally 4-connected in the v17 lab. Its new
column g is nonzero, distinct from all old columns and in their span. Its
addition preserves rank. For a partition (A,B) with g in A,

    lambda_N(A) = lambda_M(A-g) + r_N(A)-r_M(A-g).

For a prospective 2-separation with both new sides of size at least two, if
|A-g|>=2, old 3-connectivity makes lambda_N>=2. If A-g is a singleton f,
{f,g} is independent and the old complement still spans, giving lambda_N=2.
Singleton separators cannot occur: old elements were neither loops nor
coloops, and g is neither. Hence N_t is 3-connected.

Suppose a new 3-separation has |A|,|B|>=4. Then |A-g|>=3 and |B|>=4,
and the displayed formula forces an old 3-separation. In M(K_t), the only
three-element side is a triangle; thus A-g must be precisely a triangle.
For lambda_N to stay two, g would have to lie in that triangle's rank-two
span. Over GF(2), the three nonzero vectors of this span are already exactly
the triangle's three columns, contradicting g being distinct. Therefore no
3-separation has both sides of size at least four. In a 3-connected binary
matroid, any three-element side of a 3-separation is a triangle or triad:
lambda(S)=r(S)+r*(S)-|S|=2 forces the two ranks to be 2 and 3. This proves
internal 4-connectivity of N_t, and duality gives it for C_t's matroid too.

### Width and minimum weight

Deleting g recovers M(K_t), whose pathwidth is t-2. Pathwidth is minor
monotone, so N_t has width at least t-2. For this deletion one can see
monotonicity directly: r(N_t)=r(M), and at any cut the side containing g
can only have larger rank before deletion. Conversely insert g at the end of
the star order for K_t. Each old cut connectivity increases by at most one,
so width is at most t-1. Thus width is Theta(t)=Theta(sqrt(n)), where
n=C(t,2)+1, and trellis state size is superpolynomial in n.

Yet every affine coset of C_t is solvable by two T-join branches (with the
nonzero special case handled separately). For its homogeneous code the
minimum distance is simply three: the graph triangles supply weight-three
words and the columns are nonzero and distinct, ruling out weights one and
two. The dual code has minimum distance t-1: its original graph cut weight
is at least t-1, and a star at a nonground vertex outside the three selected
rows achieves t-1 with zero contribution from g. Such a vertex exists for
t>=5. These exact distance formulas are not computational hardness claims.

A finite independent all-cut audit found no connectivity violations for
t=5 (11 columns, 1,023 unordered cuts) or t=6 (16 columns, 32,767 cuts).
The proof above, not extrapolation from these audits, establishes the family.

This family defeats the conjunction of internal 4-connectivity, high trellis
width, growing dimension, and nongraphic/noncographic generator matroids as a
sufficient hardness criterion. Nonregularity alone does not defeat a richer
native algorithm.

## 7. Why small exceptional sets cannot be universal under row changes

This limitation has a counting proof. Set n=2r and use full-rank r-row
parity-check matrices. Distinct rowspaces correspond to distinct codes.
There are at least 2^{r(n-r)}=2^{r^2} such rowspaces: the systematic matrices
[I_r | X], with arbitrary binary r by r X, already yield that many distinct
rowspaces.

There are L=1+r+C(r,2) possible columns of weight at most two. The number of
r by n matrices with at most q exceptional columns is bounded by

    sum_{j=0}^q C(n,j) 2^(rj) L^(n-j)
      <= (q+1) n^q 2^(rq) L^n.

For q=O(log n) this is 2^{O(n log n)}, far smaller than 2^{Theta(n^2)}.
Every rowspace admitting such a representation must have at least one matrix
in this counted collection. Row operations preserve rowspace, so there is
no additional factor for arbitrary row transformations. Consequently a
universal logarithmic-exception theorem for this representation is false.

This excludes one proposed universal representation scheme, not polynomial
algorithms generally. It does not count arbitrary extensions, auxiliary
variables, nonlinear transformations, or entirely different native theories.

## 8. A broader route and its exact missing theorem

The useful broader direction is **proof-producing optimization with a separation
oracle**, not just bounded explicit state tables. Matching demonstrates why:
an optimization problem can admit exact polynomial algorithms even when a
direct path-state representation is enormous. Odd-cut inequalities and blossom
separation are the established prototype; Padberg and Rao give a primary
polynomial separation result:
[Odd Minimum Cut-Sets and b-Matchings (1982)](https://doi.org/10.1287/moor.7.1.67).

For general binary codes, LP decoding is an existing starting point, not a
new universal algorithm. Fractional pseudocodewords prevent unconditional
exactness of its relaxation. See Feldman, Wainwright and Karger,
[Using Linear Programming to Decode Binary Linear Codes (2005)](https://www.ee.iitm.ac.in/~andrew/ee512/projects/LinearProgrammingDecoding.pdf).

A concrete research task is to build exact primal/dual certificate extraction
for native cases, then study which additional valid inequalities close the
gap on the stored nonregular cores. Keep an explicit fractional obstruction
whenever they do not. The precise theorem needed for a universal result is:

> There is a uniform polynomial-time separation algorithm, with polynomial
> bit complexity, for an exact integral formulation of
> conv{x in {0,1}^n : Hx=0 and x!=0}, for every binary matrix H.

An oracle for the named convex hull would imply polynomial minimum distance
by the optimization/separation equivalence. We have no proof of that theorem;
stating the convex hull is not a construction, and adding all valid inequalities
does not give an efficient separator. A successful universal result would have
to overcome the demonstrated MaxCut obstruction and existing minimum-distance
NP-hardness. Conversely, failure of a particular relaxation or exponential
facet count would not establish P!=NP.

For the exceptional-column route, the solving theorem is proved above;
polynomial discovery for a specified promised class remains a separate target.
The all-input logarithmic-exception version is ruled out by section 7, so it
must not be left on the roadmap as a plausible universal theorem.
