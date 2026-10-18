# Independent capacity theorem review

The exact dictionary count and representation argument in
`../affine_sum_capacity_lab/THEOREM.md` are sound. The review found no requested
source correction; all four producer tests passed.

For a d-dimensional affine support there are G(n,d) times 2^(n-d) choices of
support and 2^[d(d+1)/2] quadratic sign directions modulo a constant sign.
Boolean multilinear uniqueness makes those phase directions distinct. The
Gaussian recurrence gives the stated product D_n=2^n product_i(1+2^i).
The code's `D.bit_length()` is indeed ceil(log2(D+1)) for positive integer D.

Any rank-r real span admits an injective projection onto r selected coordinates,
so it contains at most 2^r Boolean vectors. Union bounding spans of at most K
dictionary directions is valid even with arbitrary real coefficients. Padding
ordered tuples with zero gives the looser [2(D_n+1)]^K bound used for the explicit
existence inequality. K=0 and n=0 are also consistent: the zero-piece span
contains only the zero function, whereas the constant-one function needs one.

The scope caveat is essential and is stated correctly. This counting argument
does not exhibit succinct hard functions or polynomial-size CNFs, establish
hardness of evaluating an already supplied short sum, force every decomposition
to expose the counted function, or imply a P-versus-NP separation. Its exponential
piece lower bound in n is not superpolynomial in a full 2^n-bit truth table.

Reviewed production, theorem, test, experiment, and saved-results SHA-256 hashes
are recorded in the adjacent `RESULTS.json` capacity section. The review code
rechecks the product and dimension-sum agreement through n=64 and the exact
finite coverage artifacts. No frozen capacity file is changed.
