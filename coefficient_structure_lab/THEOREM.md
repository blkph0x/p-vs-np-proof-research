# Exact packed coefficients from clause interaction structure

This lab supplies an exact algorithm for the actual SAT-packed product, parameterized by a checked variable-elimination width. It preserves coefficient multiplicities and the single shared assignment across clauses. On bounded-width families it avoids exponentially large exponent supports. It does not establish that arbitrary formulas have small width, infer SAT structure from an arbitrary product, or resolve P versus NP.

The underlying sum-product elimination method is standard: see Rina Dechter, [*Bucket elimination: A unifying framework for reasoning* (1999)](https://ics.uci.edu/~dechter/publications/r76A.pdf), especially the explicit ordering and induced-width definitions and the sum-product algorithms. The application below derives the exact slack factors, coefficient bounds, original-request checks, and separating controls for this project's saved encoding. No novelty claim is made for variable elimination.

## 1. Preserve the original coefficient, including slack multiplicity

Use the verified encoding in `packed_cost_exact_matching`: n original Boolean variables, m nonempty clauses of sizes k_j in {1,2,3}, distinct underlying variables within each clause, b_j=k_j−1 binary slack bits, base six, and

    P(z) = product_(i=1)^q (z^a_i + z^b_i),
    q = n + sum_j b_j,
    W = sum_j b_j 6^j.

Whole clauses may repeat. The two choices of an unused variable both have exponent zero and must both be counted. The implementation rejects within-clause repeated variables and empty clauses, matching the original encoder's stated input contract. It accepts empty formulas, including n=0.

For assignment x to the original variables, let c_j(x) count false literals in clause j. The jth digit equation is

    c_j(x) + sum_(t=1)^(b_j) s_(j,t) = b_j.

All possible left digits are at most 2k_j−1≤5, so there are no base-six carries. The number of satisfying slack choices for this fixed x is exactly

    f_j(x restricted to clause j) = binomial(b_j, b_j−c_j(x)),

with the binomial defined to be zero outside 0≤b_j−c_j≤b_j. Slack bits belonging to different clauses are distinct. Therefore

    [z^W] P(z) = sum_(x in {0,1}^n) product_(j=1)^m f_j(x).

This is an equality of integer counts, not merely positivity. Its positivity is equivalent to satisfiability, since each factor is positive exactly when its clause is satisfied. A ternary clause's factor is 0,1,2,1 for zero, one, two, three true literals. Thus one positive ternary clause has coefficient 10 although it has only seven satisfying logical assignments. Repeating that same clause gives coefficient 16, not 10: each copy has its own slack bits. Adding one unused logical variable doubles either coefficient.

The variables cannot be summed separately inside each clause. For (x) AND (NOT x), the correct shared-variable sum is zero, while the product of the two separate one-clause sums is one. The prototype retains the shared variable in every factor that contains it.

## 2. Elimination theorem and explicit width parameter

The primal interaction graph has one vertex for each original variable, including unused variables, and an edge between variables occurring together in a clause. Supply a full elimination order pi. When eliminating v, join all its still-live neighbors into a clique, then remove v. Define w_pi as the largest number of still-live neighbors at any step. This definition fixes the convention explicitly; it is not the size of a bucket including v, which is one larger. No minimum-width order is assumed available.

Maintain a collection of nonnegative integer factors. Initially these are the f_j. To eliminate v, collect every current factor involving v, multiply their values at each joint assignment, and sum over v=0,1. The resulting factor has the union of their scopes minus v. Factors not involving v remain. If no factor involves v, summing the empty product gives scalar 2; this correctly counts an unused variable. At the end multiply all scalar factors, with an empty final product equal to one.

**Theorem.** For the externally supplied order pi, this procedure returns exactly [z^W]P. Every joint bucket involves at most w_pi+1 variables. All recorded tables have at most 2^w_pi entries, except the initial at-most-three-variable tables. The number of integer additions and multiplications is O((n+m)2^(w_pi+1)); a direct implementation adds polynomial bookkeeping and variable-index projection work. Consequently this is a polynomial-time exact coefficient algorithm when a supplied order has w_pi=O(log(n+m)), with the original input bit costs included. It gives no such bound for arbitrary orders or arbitrary formulas.

**Proof.** Distributivity permits summing v only in the product of factors depending on it and leaving all other factors outside that sum. Induction over the supplied order preserves the exact remaining sum-product expression. The scopes of the collected factors are precisely the eliminated variable and its neighbors in the filled graph, so the claimed table dimensions follow. Each original factor and each generated factor is consumed at most once. Charging its lookups and multiplications to that consuming bucket yields the arithmetic bound; each bucket also requires one addition per output row. Final component products contribute at most n+m extra multiplications. Independent connected components therefore factor exactly, but the algorithm also works on connected low-width instances.

The implementation stores every generated output table as a checkable certificate. Its simple active-factor scans and graph fills are polynomial bookkeeping, not hidden constant-time operations. Projecting one bucket assignment to a factor index uses at most w_pi+1 bit positions. A conservative bit bound is polynomial preprocessing plus O((n+m)(w_pi+1)2^(w_pi+1) poly(q)) operations, with polynomial graph bookkeeping. It is not a bound polynomial in the huge numerical target W.

## 3. Bit lengths of every partial count

At all times, each active factor represents a disjoint group of original clause/slack factors, summed over a disjoint group of already eliminated original variables. The groups of eliminated variables and slack bits represented by different active factors are disjoint. Remaining variables shared between factors are fixed at a bucket assignment, not independently summed twice.

An initial factor counts a subset of the 2^b_j slack assignments. A generated factor counts choices for the union of its consumed groups plus the newly eliminated variable. The same interpretation applies to a partial product of a subset of the bucket factors. Thus every nonnegative integer term is at most 2^q. Partial sums are bounded by their completed sums because every term is nonnegative, so they too are at most 2^q. The final product of independent scalar factors has the same bound. Every integer count, including intermediate products and partial sums, has at most q+1 binary bits. Unused variables contribute their separate factors of two and are included in q=n+sum b_j.

This does not turn exponentially many table entries into a polynomial-size computation. It bounds the cost of each arithmetic operation once the table widths are controlled. Original packed exponents have O(m) bits and the verifier compares them exactly against the original clauses; that preprocessing is polynomial as well.

## 4. Concrete exponential separation from sparse expansion

Take m disjoint positive ternary clauses on 3m variables. The original packed product has five independent (1+z^(6^j)) factors per clause digit j: three truth choices and two slack choices. Hence

    P(z) = product_(j=0)^(m−1) (1+z^(6^j))^5,
    W = 2 sum_(j=0)^(m−1) 6^j,
    [z^W]P = binomial(5,2)^m = 10^m.

Every base-six digit 0,...,5 is attainable independently, so the full support is exactly all integers from zero to 6^m−1. A sparse expansion retaining all reachable costs at most W ends with W+1=(2(6^m−1)/5)+1 distinct states, exponential in m. By contrast, each primal component is a triangle. Eliminating its three variables consecutively has width two, with at most eight assignments in any bucket and O(m) arithmetic operations. The certificate retains the actual count 10^m, not just the knowledge that the support is an interval.

The saved 24-clause original encoding certifies this count with peak bucket size eight. The preceding sparse reference, with a 4,096-state cap, returns UNKNOWN on the same original pairs and target. The closed-form support assertion is proved above; no exponential-sized state list is manufactured to claim that separation.

For a connected control use clauses (x_(2j) OR x_(2j+1) OR x_(2j+2)) for j=0,...,m−1. Adjacent clauses share one endpoint variable. Natural order has width two. Summing each private middle variable gives the endpoint transfer matrix

    T = [[1,3],[3,3]].

The coefficient is C_m = [1,1] T^m [1,1]^T. Therefore C_0=2, C_1=10 and C_m=4C_(m−1)+6C_(m−2). This independently checks the connected 40-clause control and all shorter chains in the tests. Shared variables are explicitly retained until elimination; disconnected-component multiplication is not being misapplied to this example.

## 5. Limits and adversarial original formulas

Ordering matters. For the binary-clause star AND_(i=2)^n (x_1 OR x_i), eliminating the center first has width n−1, while eliminating leaves first has width one. The coefficient is 2^(n−1)+1, because binary-clause slack choices are unique once an assignment satisfies the formula. The saved good and bad orders query exactly the same packed product.

Small width is not a universal property, even after choosing the best order. The formula AND_(i<j)(x_i OR x_j) has a complete primal graph, so every order has width n−1. It is nevertheless an easy positive instance, with coefficient n+1: at most one variable can be false. The width-limited prototype intentionally returns UNKNOWN on a 16-variable instance at the chosen cap. This is a limitation of explicit width-based tables, not intrinsic hardness of that family or of all algorithms.

Additional saved controls are planted mixed-polarity 3CNFs on 24 and 32 variables, with 4n clauses each. Their original satisfying assignments and exact-weight matching extensions are independently checked and saved. The chosen bucket cap is exceeded, so the structure solver returns UNKNOWN, without claiming zero coefficient. An original unsatisfiable control containing all eight polarity clauses on three variables instead receives a complete width-two certificate of coefficient zero. These controls distinguish actual original encodings and honest resource limits from assumptions based only on favorable examples.

For comparison, a general binomial product admits the exact normalization

    P(z) = z^A product_i (1+z^d_i),
    A=sum_i min(a_i,b_i), d_i=|a_i−b_i|.

Factors with d_i=0 contribute two, not one. The interval check 0≤W−A≤sum d_i and divisibility by gcd of the nonzero d_i are necessary. They are not sufficient: the saved gap pairs (1,6),(36,0),(36,0),(0,36), W=36 normalize to A=1, differences 5,36,36,36 and target 35. The gcd is one and the interval contains 35, but its coefficient is zero. Meet-in-the-middle or sparse subset-sum methods remain possible general exponential fallbacks. This lab's substantive improvement instead exploits a separately verified clause-factor structure.

## 6. Original-request binding, certificates, and budgets

`solve_structure` and `verify_structure` take the original n, clauses, exponent pairs, target, and full external elimination order. The verifier first checks every exponent and slack factor against the original base-six encoding, preserving whole-clause repetitions and unused variables. An unrelated binomial product or a different target is rejected; the implementation does not guess an encoding from its exponent list. It currently requires the original factor order; a different factor permutation would need its own checked mapping.

The certificate contains each eliminated variable, exact consumed factor IDs, remaining scope, and integer output table. The verifier uses a different traversal of each full bucket to recompute its multiply-and-sum recurrence. It independently rebuilds graph fill, checks scopes against the induced neighbors, checks all final components, recomputes the claimed width/work/bit statistics, and binds the original request and external order with a length-prefixed binary hash. Claimed small width and heuristic provenance are not trusted. The artifact is an executable certificate, not a formal proof-assistant development.

Caps cover original dimensions, graph-fill work, peak bucket states, total stored table entries, and arithmetic operations. Powers of two are checked against the cap before a huge shift or allocation. Exhaustion returns UNKNOWN with no coefficient or positivity claim. Checker exhaustion likewise returns UNKNOWN, distinct from an invalid certificate. Exact certificates include all steps, even when a zero factor appears; this reference does not claim advanced semantic factor simplification.

The named graph-fill and arithmetic counters do not measure total setup CPU or wall time. In particular the original exponent binding uses an n-by-m scan, base-six integer arithmetic and binary hashing before the table computation. Those operations have the separately charged polynomial input-bit cost above; dimension caps bound their input sizes.

`RESULTS.json` preserves original encodings, exact certificates or honest UNKNOWN outcomes, independent coefficient oracles, known assignments where available, work counts, and before/after hashes of local and prior-encoder sources. The finite tests validate examples and implementation; the all-size algorithmic guarantee rests on the sum-product invariant and verified width condition above.
