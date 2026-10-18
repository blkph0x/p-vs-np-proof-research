# Coverage audit: sparse graph perturbations and the remaining P-versus-NP gap

**Status:** mathematical audit of a supplied representation, 2026-10-18. No novelty claim. The structural statements below have direct proofs. Small quotient counts were also exhaustively checked with integer arithmetic. This file does not claim that the proposed solver implementation has passed its separate tests, or that P versus NP has been resolved.

The useful conclusion is stronger than branching over sparse perturbations: if

    H = B + U V  over GF(2),

where every column of both B and U has at most two ones, then H can be transformed, without changing its coordinates or their Hamming costs, into

    S H = [ L ]
          [ A ],

where S is invertible, A is a graph incidence matrix, and L has at most p=rank(U) rows. Homogeneous minimum nonzero weight therefore needs only zero- or two-terminal labelled joins after pinning an original edge. It does not need an outer enumeration of perturbation states or a general-terminal matching routine.

This is a restricted class. There are explicit rank-one graphic perturbations outside it, and it is incomparable at parameter one with the existing disjoint-exception-rank class. Pure linear auxiliary-variable extensions do not remove this restriction. More general objective-preserving encodings remain an unresolved possibility and require a precise constructive theorem.

## 1. Conventions and the exact structural theorem

There are n original coordinates and r original rows. B is r by n, U is r by q, and V is q by n. A column of weight two is an edge joining its two row vertices; a unit column joins its row vertex to a common ground vertex; a zero column is a loop. Thus B and U together describe a multigraph on r+1 vertices. Loops, parallel edges, disconnected components, isolated vertices and redundant rows are allowed. The p in the theorem is rank(U), not the number q of supplied columns and not necessarily rank(UV).

**Theorem.** Given this decomposition, one can construct in polynomial time an invertible r by r matrix S and a row ordering for which SH consists of a reduced graph incidence block A and at most p arbitrary label rows L. Conversely, a matrix with a graphic incidence block and p arbitrary rows has a sparse-U decomposition of rank at most p.

### Constructive forward proof

1. Regard the U columns as graph edges. Choose a spanning forest F of their non-loop edges. The forest has p edges because binary incidence-column rank is forest rank. Its columns U_F are a basis of the column space of U; any dependent U columns need not remain as separate label dimensions.

2. Root each forest component, choosing the ground vertex as the root of its component. For each forest edge f, let D_f be the subtree separated from its root by deleting f. Let P_f be the sum of the original vertex rows indexed by D_f. These p row vectors form a matrix P satisfying P U_F=I_p: among forest edges, only f crosses its subtree cut.

3. For each forest component C not containing ground, form the sum of all its vertex rows. Put these r-p row vectors in Q. They have disjoint nonempty supports, so are independent. Every U edge has both ends in one forest component, hence Q U=0. The matrix A=Q B is exactly the reduced incidence matrix of the graph obtained by contracting F. An original edge internal to a component becomes a graph loop; retain that coordinate.

4. The matrix S=[P;Q] is invertible. If a linear combination of its rows is zero, multiplying by U_F makes all coefficients of the P rows zero. Independence of the Q rows then makes the remaining coefficients zero.

5. Put C=P U. Since U_F is a basis and P U_F=I_p, U=U_F C. Thus W=C V is the compressed label matrix and

       S H = S B + S U V
           = [P B + W; Q B]
           = [L; A].

This explicitly rewrites dependent perturbation columns before solving. It preserves every original coordinate, all original linear dependencies, and the objective |x|. No original edge is contracted as a variable in this conversion: contracting the auxiliary forest describes the new graph block only. Original coordinates that become loops or parallel edges must remain distinct, with their individual labels and costs.

### Converse and terminology

Given H=[L;A], set B=[0;A], U=[I_p;0] and V=L. The zero top rows of B are isolated graph vertices, and every column of U is a unit graph column. Then H=B+UV. Dependent or unused label rows can be removed, so this is a bound of at most p.

The appropriate description is “a graphic matrix with at most p arbitrary rows appended,” or “at most p binary lifts of a graphic matroid.” When one independent row is appended, this is the usual even-cycle matroid representation. It should not be identified indiscriminately with every use of the term signed-graphic. The standard one-row representation is described directly on [Bertrand Guenin's research page](https://www.math.uwaterloo.ca/~bguenin/matroid.html).

### Constructibility, verification and dimensions

The decomposition must be supplied, or found by a separate algorithm. This theorem converts it; it does not discover a suitable B,U,V from an arbitrary H.

A forest and component labels are found by ordinary graph operations. Subtree masks give P and component masks give Q. The product W=CV uses p by q and q by n matrices. A conservative bound using straightforward binary matrix multiplication, including a direct replay of S, U=U_F C and SH=[L;A], is

    O(r^2(n+q) + p q n + r^2)

bit operations, and polynomial storage. Faster sparse operations are possible but unnecessary for the claim. The explicit certificate can contain the chosen forest, P,Q,C and the matrices L,A; checking that S is invertible and that the displayed identities hold is polynomial in r,n,q. This is a uniform polynomial construction in the actual input dimensions, rather than a statement whose exponent secretly depends on p.

If a supplied decomposition uses many dependent U columns, replace them by the selected p forest columns and V by W before calling the labelled routine. The arithmetic identity, including the original H, must be checked rather than inferred from successful tests on the graph.

## 2. Direct deterministic homogeneous algorithm

In the row form, Hx=0 is exactly

    A x=0 and L x=0.

The graph edge set selected by x is Eulerian and its total GF(2)^p edge label is zero. To require x nonzero, try each original coordinate e as a pin x_e=1, delete e from the residual graph, and solve

    A_(E-e) y = A_e,
    L_(E-e) y = L_e.

The graph boundary has two terminals when e is a non-loop and zero terminals when e is a loop. The candidate weight is 1+|y|. Every nonempty feasible x contains some pinned e and produces a residual candidate of its own weight. Conversely every residual candidate gives a feasible original nonempty x. Taking the minimum over the n pins is therefore exact. Deleting the pinned coordinate is essential: allowing the residual solution to use e again would cancel the pin under symmetric difference.

The required deterministic primitive is already a known graph-algorithm construction. [Geelen and Kapadia, Section 6, especially Lemmas 6.1–6.3 and Theorem 6.4](https://arxiv.org/pdf/1504.07647), give the zero/two-terminal parity-join route. Their displayed polynomial running time treats the label dimension as fixed. The following explicit uniform accounting makes the parameter dependence visible.

Let v be the number of graph vertices and m the number of edges in a residual instance. Use the product graph with v 2^p vertices and at most m 2^p lifted edges. Compute minimum labelled closed-walk costs and, for a two-terminal instance, labelled terminal-walk costs. Close the closed-walk costs under sums in GF(2)^p using shortest paths on the 2^p group states. An array-based shortest-path implementation on this complete nonnegative-weight state graph uses O(4^p) arithmetic operations. Running the unweighted product-graph searches from every base vertex uses O(v(v+m)2^p) operations. A final convolution over labels costs O(2^p). Hence one valid, conservative bound for all pins is

    O(n [v(v+m)2^p + 4^p])

arithmetic operations, plus polynomial preprocessing and factors for the bit length of distances and labels. Here v<=r-p+1 after the forest conversion and m<=n. This is deterministic 2^{O(p)} poly(r,n,q), and becomes polynomial for supplied p=O(log N), where N is the original input length.

Why closed walks and their closure are needed: a feasible labelled join may include disconnected Eulerian components. A shortest terminal walk alone can miss the optimum. For nonnegative costs, projecting a walk to the edges used an odd number of times preserves its boundary and label and cannot raise its cost. Conversely, a feasible join decomposes into a terminal path, if needed, and graph circuits; their labels and costs give a feasible state-closure decomposition. These two inequalities prove equality of the state optimum and the edge-set optimum. Empty Eulerian sets are allowed inside the residual primitive; nonemptiness is enforced by the original pin.

The audit's claim is the mathematical algorithm and its reduction. A concrete proof-producing implementation still needs independent checks of product-graph distances, closure values, reconstructed edge parities, complete pin coverage and the original equations. Exhaustive checks on small instances supplement those proofs; they do not replace them.

### Affine targets are different

For arbitrary Hx=s, the row transform gives Ax=s_A and Lx=s_L. The support of s_A can contain many graph terminals. The homogeneous argument does not make that arbitrary boundary small. General labelled-terminal DP remains a possible exact fallback, with exponential dependence on the terminal count as well as p. Appending s as an extra homogeneous column and pinning it does not remove this issue: that column need not be a graph edge in the established row form.

## 3. A rank-one general perturbation outside the sparse class

Take the rank-four matrix H whose columns are all 15 nonzero vectors of GF(2)^4. Put u=1111. For each column h define

    B_h = h,       V_h=0, if wt(h)<=2;
    B_h = h+u,     V_h=1, if wt(h)>=3.

Then H=B+uV and every B_h has weight at most two. Thus H is a rank-one perturbation of a graphic matrix. Loops and parallel graph edges appear and are legitimate.

Nevertheless H has no sparse-U decomposition with rank(U)<=1, in any row basis or with any alternative graph on these coordinates.

**Proof.** A simple graphic matroid of rank k has at most k(k+1)/2 non-loop elements: each component of rank k_i has at most k_i(k_i+1)/2 distinct edges, and summing cannot exceed the single-component bound. If H were a one-row graphic lift, deleting that row would leave a graphic quotient of rank three or four. Rank four would imply H itself is graphic, impossible because 15>10. Every quotient of GF(2)^4 by a one-dimensional subspace contains all seven nonzero vectors of GF(2)^3 among the images of the 15 columns. After deleting duplicate images and the zero image, there are seven distinct nonzero elements of rank three, exceeding the graphic bound six. Thus no rank-three quotient is graphic either.

This proves separation of the existential classes, not merely failure of the particular supplied u to be sparse. All 15 nonzero quotient directions were also enumerated: each gave exactly seven distinct nonzero quotient classes. No graph recognition oracle or numerical tolerance is involved in this test.

A smaller warning for a *fixed* decomposition is K4 reduced incidence plus u=111: its augmented columns [B|u] are all seven nonzero vectors in rank three. No common row change can make all seven graph columns, since a simple graphic rank-three matrix has at most six. This fixed-decomposition warning alone would not rule out a different sparse decomposition of H; the 15-column example above does.

Graph vertex splitting is not an innocuous answer to this obstruction. A split must come with a proof that its added constraints, variables, target and objective reproduce the original problem. Arbitrary row changes preserve the matroid but may destroy the graph block. Adding arbitrary constraints can repair that block while increasing the number of label rows, which spends the parameter the algorithm needs to keep small.

## 4. Comparison with disjoint exceptional-coordinate rank

The existing native class is H=[B|D], with graph coordinates and exceptional coordinates disjoint and rank(D)<=p. Its syndrome DP can exploit many exceptional columns lying in a small subspace. The sparse perturbation class instead allows a few additional parity rows to affect many of the same coordinates as the graph. At the same rank budget these are incomparable.

### A one-row lift that is not a rank-one disjoint-exception instance

In GF(2)^4, take the 13 distinct nonzero columns

    1,2,3,4,5,6,8,9,10,11,12,13,14.

The lower three bits of each column have weight at most two; the fourth bit is one arbitrary label row. Hence this is a one-row graphic lift, and has a sparse-U rank-one decomposition.

Any rank-four disjoint-exception representation with rank(D)<=1 has at most ten distinct nonzero graphic column values and at most one distinct nonzero exceptional value, hence at most eleven in total. Invertible row changes preserve the number of distinct nonzero columns. Therefore this 13-column instance has no disjoint-exception rank-one representation in any row basis. Allowing redundant rows does not evade the bound: selecting four independent rows preserves graph-column weight at most two, exceptional rank at most one, and column distinctions.

### A rank-one disjoint-exception instance that is not a one-row lift

Take the 15 reduced incidence columns of K6 in GF(2)^5, namely every vector of weight one or two, and append u=11111. Explicitly the 16 columns are

    1,2,3,4,5,6,8,9,10,12,16,17,18,20,24,31.

This is a disjoint-exception rank-one instance. It cannot be a one-row graphic lift. To see this, restore the ground coordinate so every vector is an even subset of the six graph vertices. The appended u is the subset of all six vertices. Every nonzero quotient direction is an even subset of size two, four or six.

- For a direction of size two, quotienting the K6 graph part contracts an edge, leaving ten distinct nonzero rank-four graph values. The image of u is a new value, so there are eleven.
- For a direction of size four, the 15 graph edge values have exactly three collisions: the three ways of partitioning that four-set into two disjoint edges. There are twelve distinct nonzero graph values; the extra column introduces no reduction of this count.
- For the direction of size six, the 15 graph edge values have no collisions and are all nonzero.

Thus every one-dimensional quotient has at least eleven distinct nonzero rank-four values, exceeding the graphic bound ten. A graphic rank-five representation of the original is also impossible, because it has sixteen distinct nonzero columns, exceeding fifteen. This excludes every possible one-row graphic lift representation. Exhaustive integer checks of the 31 quotient directions gave counts 11 for all 15 directions of size two, 12 for all 15 directions of size four, and 15 for the remaining direction.

These examples prove fixed-budget incomparability. They do not claim a sharp comparison under arbitrary changes of the parameter, and no universal bounded conversion from one parameter to the other is asserted.

## 5. Unbounded p gives the general hard problem back

Every binary matrix H has the trivial representation B=0, U=I_r, V=H. B is a graph of loops and U consists of graph unit columns. Thus the sparse-U condition puts no restriction on H when p is unbounded. The uniform 2^{O(p)} algorithm consequently remains exponential in the worst case.

General homogeneous minimum nonzero codeword weight is NP-hard and its decision version is NP-complete; see [Vardy's original 1997 paper](https://doi.org/10.1145/258533.258559). General affine minimum-weight decoding is also hard; the exact-cover reduction proved in this checkpoint's `degree_three_barrier.py` already shows the inhomogeneous case using columns of weight three. These are distinct claims: that inhomogeneous gadget alone does not prove homogeneous minimum-distance hardness.

If loops were forbidden as a syntactic convention, take any fixed allowed incidence B of the right size and use U=I_r, V=H+B. The same unbounded-parameter conclusion follows. The difficulty is controlling p and constructing the representation, not spelling the matrix as a perturbation.

## 6. Counting coverage, and what auxiliary variables can and cannot change

### Same original coordinates

On n labelled coordinates, a graphic block of rank at most r can be represented on at most r+1 vertices after removing isolated vertices and identifying a root from each component. Each coordinate has at most 1+binom(r+1,2) possible graph column values, including zero. The p label rows have at most 2^{pn} choices. Allowing all smaller graphic ranks contributes at most an additional factor r+1. Hence the number of row spaces representable by this class is at most

    (r+1) [1+binom(r+1,2)]^n 2^{pn}.

This counts row spaces represented by the displayed matrices; no extra arbitrary-GL factor is needed. Multiple descriptions of one row space only enlarge this upper bound. With r=floor(n/2) and p=O(log n), it is 2^{O(n log n)}. By contrast there are at least 2^{r(n-r)} distinct r-dimensional subspaces of GF(2)^n: the row spaces of [I_r|M], for arbitrary r by (n-r) binary M, are all distinct. Therefore universal O(log n)-label coverage on the original coordinates is unconditionally false, regardless of discovery time.

### Why naive size counting is insufficient after enlargement

If a representation may have M polynomially many auxiliary coordinates in the original input length N, its description count can be 2^{O(M log M)}. That quantity can exceed 2^{Theta(n^2)}. Comparing only these two description counts does **not** refute a universal polynomial-size representation. In particular, a proof that simply substitutes “polynomial size” into the same-coordinate counting argument would be invalid.

### A stronger obstruction for pure linear existential extensions

For this specific class there is an independent structural fact: matrices that are graphic plus at most p arbitrary rows are closed under coordinate deletion and matroid contraction, without increasing p.

Deletion simply removes a column. For contraction of a column e, distinguish three cases. If its graph column A_e is nonzero, pivot on a graph endpoint row, clear that column from the label rows, and perform the corresponding graph-edge contraction. The graph block stays graphic and the number of arbitrary rows stays at most p. If A_e=0 but L_e is nonzero, pivot on a label row; this consumes one arbitrary row and leaves the graph block unchanged. If the whole column is zero, contraction is equivalent to deletion. Iterating proves closure for any auxiliary set, of any size.

Now suppose an extended labelled-graph matrix K on original coordinates x and auxiliary coordinates y represents exactly

    C = {x : there exists y with K(x,y)=0}.

Eliminating y replaces each original column by its class modulo the span of the auxiliary columns. This is exactly contraction of the auxiliary elements in the represented binary matroid. By the preceding closure argument, C is still the kernel of a graphic-plus-at-most-p-row matrix on the original coordinates. Consequently even arbitrarily many zero-cost **linear** auxiliary coordinates, followed by exact existential coordinate projection, cannot enlarge this class's p-label coverage. The same-coordinate counting obstruction then applies to the projected code itself. If M is polynomial in N and p=O(log M), then p=O(log N)=O(log n) for the rank-half matrices above, so this does rule out universal coverage by that particular extension format.

This is a restriction on the encoding, not a proof of P unequal to NP. It does not cover nonlinear constraints, arbitrary objective-only reductions, or a different target class.

### Arbitrary output maps and objective preservation

A general linear output map x=Tz is not the same as coordinate projection. It can make coverage look trivial: an unconstrained vector z, represented by graph loops with no labels, can map through a generator matrix onto any linear code. But the objective becomes |Tz|, which is generally not the sum of fixed nonnegative edge costs in z. For example, T(z1,z2)=(z1,z2,z1+z2) has weight two on all three nonzero inputs. Additive costs on z would require c1=c2=2 from inputs 10 and 01, but would then assign cost four to 11. Thus the graphical description alone has not preserved the optimization problem.

Zero-cost auxiliary edges also create a separate nonemptiness hazard. A nonempty extended vector may project to x=0. To optimize a nonzero original word, pins must range over original coordinates, or the reduction must otherwise prove that such spurious witnesses are excluded. This condition cannot be inferred from homogeneous feasibility.

## 7. The explicit missing theorem for a general P=NP route

An actual route from this solver to P=NP would need, for an NP-complete input of bit length N, a uniformly polynomial-time construction of a polynomial-size instance in the solved class with p<=c log N, together with a polynomially computable threshold and a correct solution map. It must prove both directions of the decision equivalence, exact handling of the cost, and exact handling of the nonzero or pinned condition. If the target graph boundary is not zero or two terminals, a polynomial bound for the relevant general-terminal step is also needed.

The same-coordinate universal theorem is already false by counting. The pure linear existential-extension version is also false by minor closure. A more general objective-preserving reduction is not ruled out by either argument, but no such construction has been established here. As a reduction to an NP-hard code problem followed by a proven polynomial solver, this would constitute the substantive breakthrough itself; it is not a routine preprocessing lemma that may be assumed.

The p=O(log N) bound must refer to the original input size and be accompanied by M=poly(N). Using exponentially large M to make p look logarithmic merely transfers the exponential work into representation size. Polynomial-size certificates or existence of a representation alone also do not give a polynomial-time constructor.

## 8. Falsifiable next checks

1. **Verify the structural adapter rather than assume it.** On supplied sparse-U instances with dependent columns, loops, disconnected components and isolated vertices, produce S,P,Q,C,L,A; check their exact identities and invertibility. For small n, enumerate all original words to verify the zero-kernel equivalence and the edge-pinned optimum. The parameter reported must be rank(U), with any later label-rank reduction separately checked.

2. **Keep the separation examples as rejection tests.** A universal claim at p=1 must confront the 15-column rank-one general perturbation and the 16-column native rank-one example above. The one-dimensional quotient counts give finite, independently reproducible obstruction certificates. Conversely, a claim that sparse lifts add no coverage beyond native rank one must confront the 13-column example.

3. **Audit every proposed auxiliary encoding.** State whether the output is a coordinate projection, an arbitrary linear map, or a more general decoding map. For coordinate projection, the contraction theorem applies. For other maps, verify the objective and nonzero semantics on every small assignment before extrapolating. An input encoding that only preserves satisfiability of a homogeneous system has lost the minimum-weight question, since zero always satisfies that system.

4. **Require a general representation theorem before interpreting class expansion as P=NP progress.** A broad next candidate would need to encode hard instances using a cost-preserving format outside pure linear coordinate projection. The necessary invariant is the exact optimum or decision threshold on all inputs, not success on graph-like or randomly sampled instances. No claim that such a candidate exists is made here.

The strongest confirmed outcome of this audit is a simpler deterministic algorithm for the supplied sparse-U class, a complete constructive proof of its row-form interpretation, and explicit limits on how far that interpretation can be extended. The ultimate P-versus-NP objective remains open.
