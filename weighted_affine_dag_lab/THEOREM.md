# Exact weighted sums of compact affine boundary messages

This is an exact counting and signed-contraction method with explicit resource limits. It extends the existing Boolean semantic-boundary recurrence to rational weighted sums of compact affine quadratic messages. It does not establish a polynomial bound on the number of components, outperform general exact counting methods on all inputs, or resolve P versus NP. The algebraic identities and factor-tree dynamic programming are established techniques; no novelty claim is made.

## Original input and meaning

`solve_formula(n, clauses)` returns the number of assignments to **all n original variables**, with variables numbered 1 through n in literals. Its generic form `solve_factors(n, factors)` sums a product of original factors over the same Boolean universe. An OR factor has its supplied literal list; a native factor has a declared original-variable scope, affine equations over F2, a degree-at-most-two Boolean polynomial q, and an exact rational scalar lambda. Its value is lambda times the indicator of its equations times (-1)^q. Constant monomial mask 0 is one; repeated monomials cancel modulo 2. Masks always use the original variable positions. Negative and zero contractions are permitted by the generic API.

Each original factor occurrence receives a separate ID, including repeated factors, tautologies, and empty clauses. An explicit order must list every original factor ID exactly once. The request binding records n, all original factors including repeated literals, and that order. A tautological OR is replaced by the constant one, repeated identical literals are removed locally, and an empty OR is zero. These transformations preserve the original function; they do not change the original n. Variables unused after this local normalization are counted by an explicit final factor 2^f. Native declared scopes are retained even when an expression happens not to depend on some scoped variable; that variable is summed exactly once according to its ownership.

For a non-tautological, nonempty clause C, let V_C pin every literal to its false value. Then OR(C) = 1 - V_C. Thus an ordinary clause starts as two signed affine pieces. A native affine quadratic factor starts as one piece. This computes ordinary SAT counts, not the number of extensions through a slack encoding.

## Boundary invariant and product rule

For a set S of original factor IDs, let X_S be the union of their normalized scopes. Its boundary B_S consists of the variables in X_S also appearing in a factor outside S. The node function is

    M_S(b) = sum over X_S minus B_S of product_{i in S} F_i.

A message is a finite sum of canonical compact affine quadratic pieces on the ordered, original-coordinate boundary B_S. The primitive from `../affine_boundary_lab/boundary.py` implements exact marginalization of each piece and independently verifies a complete elimination trace.

If S is the disjoint union of child ownership sets L and R, every variable shared between their scopes belongs to both child boundaries: it occurs outside each child. Consequently the variables internal to a child appear in no factor of the other child. Distributing the product of the two child sums is therefore valid, and the parent is obtained by summing the product over

    (B_L union B_R) minus B_S.

The active universe passed to the marginalizer is exactly B_L union B_R, rather than all n coordinates. This prevents inserting free factors for variables already summed in a child or unrelated to this product. At a leaf it is exactly the original factor's normalized scope. Multiplication stacks affine equations, XORs phase polynomials, and multiplies rational scalars. Every pair of child pieces is generated and charged **before** any coefficient merging. Empty child sums correctly produce a zero parent. The empty original input has one identity root and the final value 2^n.

The complete root has no boundary. Sum its scalar pieces, then multiply by 2^f for original variables outside all normalized scopes. The invariant proves that this is the original contraction; for pure CNF it is a nonnegative integer.

## Compact canonicalization, sharing, and scope

The affine primitive puts support equations in canonical RREF with the retained order as pivot order, substitutes pivots into the phase, and absorbs the constant phase into the scalar. Its scalar-independent key includes original n and the complete ordered retained-variable list. Equal keys can therefore have their rational coefficients added exactly. A zero total coefficient is removed. This merges only identical canonical affine functions up to scalar; it makes no claim to find every linear dependence among different affine pieces.

The producer first separates original factor-incidence components, preserving the requested factor order within a component, and builds balanced binary product trees. This adapts the existing component decomposition and repaired semantic boundary ownership recurrence. It is not the old unit-residual solver and does not introduce a second backdoor recognizer. The substantive added capability is compact **weighted** boundary functions, including phases and negative coefficients, and exact merging after projection.

The source ownership structure is a tree, a special DAG. Arithmetic marginal requests with identical full inputs are shared through separate certificate records, so repeated exact computations need be produced and checked only once. The full request is compared in addition to its cache digest. Sharing is never used to omit an original factor occurrence. There is no claim of unrestricted search-DAG compression or automatic variable renaming.

## Certificate soundness

`verify_formula` and `verify_factors` bind to the externally supplied original request. They derive local clause decompositions and scopes afresh. They require every structural node to occur in a topological sequence, each leaf to own one original factor, and each product's children to have disjoint ownership whose union is exactly the parent. They recompute every node's boundary from original occurrences and its active projected-variable universe from the children. The root must own every original factor. Identity is allowed only for empty original input. Every nonroot node and every marginal record must be used.

For each product, the verifier enumerates every ordered pair of independently verified child pieces; the recorded list must have exactly the same length and match every derived marginal input. For each first reference to a marginal record it invokes the independent affine trace verifier, and uses the verifier's freshly derived canonical message. It then repeats exact coefficient merging and checks the saved node output. Convenience keys and producer work statistics are not trusted. It derives final free variables and the rational root value independently; the CNF wrapper additionally requires the exact integer count. Typed comparisons reject booleans or floats masquerading as proof integers.

Induction on the topological order proves correctness of every accepted node. Full root coverage and the final free-variable factor then prove the accepted original count. This explicitly avoids the historical omitted-root-clause bug that was repaired in `semantic_branch_dp_lab`; that repair is documented separately in `../SEMANTIC_CERTIFICATE_REPAIR.md`.

## Cost and limits

Let K_v be the number of retained pieces at node v. A binary product generates K_left*K_right pairs, each requiring polynomial-time affine quadratic multiplication and marginalization in the explicit variable/equation/phase dimensions and rational bit lengths. With C equal to the sum of these products plus initial leaf pieces, and W the total work of distinct marginal computations, the producer and verifier use O(C) pair/merge operations plus W and polynomial input, bookkeeping, hashing, and exact-arithmetic costs. Repeated ownership-set scans and certificate storage are also charged by their ordinary explicit sizes; the implementation's `work` statistic is an operation counter, **not** a literal bit-operation or wall-clock bound. In particular it does not count every byte processed by hashes or every arbitrary-precision arithmetic step.

The explicit caps cover retained terms, all pre-merge products, combined structural and marginal nodes, operation work, original dimensions, and integer numerator/denominator bit lengths. Separate `boundary_caps` govern every affine trace. The retained-term cap is applied to intermediate merge dictionaries; a later cancellation does not retroactively avoid a prior cap. The product cap counts all pairs even if the output is zero or many requests are identical. Exceeding a cap returns UNKNOWN with no count or completed certificate. Verification cap exhaustion likewise returns UNKNOWN, never VERIFIED. There is no polynomial worst-case bound on K_v or total C.

Small cases are directly enumerated in the tests, including every intermediate boundary function. The own-lab saved controls include genuinely wide boundaries and negative/rational values. The parent additionally benchmarks the same adapter against previously saved original formulas and an independently certified counting reference; neither selecting controls nor excluding UNKNOWN cases is evidence of a general algorithmic improvement.

The saved `../WEIGHTED_AFFINE_CROSSCHECK.json` contains 58 original CNFs under the default caps and original clause order: 54 exact counts agree with independently certified references and replay successfully; four are UNKNOWN. The complete positive binary interaction on 16 variables, planted 32-variable/128-clause formula, and legacy connected mixed 12 fixture exceed the combined node cap at 4,097. The planted 24-variable/96-clause formula reaches 257 retained pieces, exceeding the 256-piece cap. The 72-variable disjoint, 81-variable chain, and 66-variable sliding fixtures complete exactly. All 58 original counts were also obtained by a separate bounded branch/component reference; no general speed or coverage advantage over that reference is claimed. These measured failures remain part of the saved record.

## Analytic saved controls and a falsifiable limitation

For F_m = AND_i (x OR y OR z_i), the original count is 3*2^m+1. The private z_i are eliminated at their leaves, producing the two-piece function 2 - [x=0,y=0]. Every later product and merge stays within this two-piece span. This is a positive instance of early elimination and merging, not a bound for arbitrary clauses.

For boundary y of width b and one internal t, summing (-1)^(t*parity(y)) gives 2[parity(y)=0]. Multiplying by OR(y) then summing gives 2^b-2 for b>=1. The saved b=128 control retains a compact parity equation rather than a table of 2^128 entries.

Two identical quadratic phases supported on the same even-parity subspace cancel in their product. With scalars -3/5 and 7/11 on width b>0, the exact contraction is (-21/55)*2^(b-1). The two leaves each retain all b boundary bits; their compact size does not depend on enumerating those assignments.

For m disjoint positive binary ORs together with a native global even-parity factor on their 2m variables, the exact count is (3^m+(-1)^m)/2: each pair has one accepted even assignment and two accepted odd assignments. The saved m=12 input deliberately uses max_terms=16. The fixed balanced factor plan exceeds that cap and reports UNKNOWN, although the analytic count is elementary. This demonstrates a concrete limitation of the chosen plan and key-equality merge, not a lower bound against other decompositions or exact algorithms. A substantive next test is whether an independently certified alternative plan or richer component-span representation reduces this failure without silently omitting pre-merge work.
