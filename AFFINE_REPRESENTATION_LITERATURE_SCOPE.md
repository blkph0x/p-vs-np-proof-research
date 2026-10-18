# Literature check: related rank notions and input size

Checked 18 October 2026 local time. This note supplies context and scope checks;
the project's elementary recognition proof and certificate checkers do not
depend on a new external lower-bound theorem. No novelty claim is made.

## Affine quadratic pieces are an established representation

Peleg, Shpilka and Volk describe stabilizer functions using affine support,
quadratic signs and an additional complex linear phase. Our real rational
pieces use a restricted form of that established language. Their discussion
also distinguishes full-support quadratic phases from affine-supported pieces:
AND is one affine pin in the latter language. Consequently a lower bound for
expressing AND using only full-support phases cannot be transferred to this
project's larger dictionary. See Section 1.4 and the preliminaries of
[Lower Bounds on Stabilizer Rank](https://arxiv.org/pdf/2106.03214).

The direct local check is immediate: AND(x_1,...,x_n) equals the indicator of
x_1=...=x_n=1, with coefficient one and zero quadratic phase. Likewise its
sign (-1)^AND is one minus twice that pin, hence at most two of our pieces.
Neither function can witness a superpolynomial lower bound for this dictionary.

## Exponential rank can hide exponential numeric input

Lovitz and Steffan's Corollary 3.6 gives a product-state family built from
factors proportional to (1,2^(2^(i-1))), with exponential stabilizer rank in
the number of factors. Proposition 3.7 gives a different construction using
large algebraic degree. These are relevant examples, but their input model
must be preserved. See the published article
[New techniques for bounding stabilizer rank](https://quantum-journal.org/papers/q-2022-04-20-692/)
and [Sections 3.4 of its paper](https://arxiv.org/pdf/2110.07781).

For the integer product family, our own bit accounting is simple: writing
2^(2^(i-1)) as an ordinary binary integer takes 2^(i-1)+1 bits. Across n factors
the explicit coefficient length is 2^n-1+n. Exponential growth measured only
in n is therefore not automatically superpolynomial in this project's
explicit rational input length. A compressed exponent or algebraic-number
representation would require different arithmetic and cost assumptions.

## Recent claims also require dictionary and access-model checks

The 5 October 2026 preprint by Sinha and Lovitz states a nearly quadratic
lower bound for representations of AND by full-support quadratic phases.
Its Section 1.3 defines that restricted dictionary explicitly. Its learning
results use access to quantum-state copies, which differs from our supplied
classical list of exact rational pieces. These statements are contextual
claims of the preprint, not independently audited results of this project.
See [Improved bounds on stabilizer extent and Clifford rank](https://arxiv.org/html/2610.06819v1).

The project should neither relabel a familiar representation as a new discovery
nor import a lower bound across incompatible dictionaries, precision models
or oracle access assumptions. The concrete unresolved task remains controlling
the size and discovery cost of representations generated from original SAT
inputs. The new one-piece recognizer addresses only an already explicit sum.
