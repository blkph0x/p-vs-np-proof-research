# Checkable Fano minors for the saved random cores

The saved v17 random binary matroids at lengths 18, 20, 22, 24, 26 and 28
each contain an explicitly verified Fano minor. They are therefore neither
graphic nor cographic. This adds a certificate to the existing finite controls;
it does not prove minimum-distance hardness or an all-size family theorem.

## Certificate and independent verification

The input consists of generator-matrix columns as integer vectors over GF(2).
A certificate identifies an independent contraction set C and seven retained
original coordinate indices R. Delete every coordinate outside C union R after
contracting C. For any retained set X, the minor rank is

    r_minor(X) = r(C union X) - r(C).

The verifier checks independently that the retained quotient has rank three,
each retained column has quotient rank one, and every retained pair has rank
two. Thus its seven vectors are nonzero and pairwise distinct in a
three-dimensional binary space. They are exactly the seven nonzero vectors of
GF(2)^3, which represent F7.

The certificate also supplies three retained coordinates as a quotient basis
and seven labels from 1 through 7. For every retained coordinate, the verifier
checks that XORing the basis columns selected by its label leaves a vector in
span(C). These labels make the quotient explicit; their mere presence is not
trusted. The certificate verifier uses separate row-elimination code and rank
identities rather than discovery's incremental quotient reducer.

Malformed fields, wrong input size/rank, noninteger or out-of-range coordinates,
duplicate coordinates, dependent contraction sets, contraction/retention overlap,
loops or parallel elements in the quotient, and incorrect quotient labels are
rejected. The verifier is polynomial in the input matrix dimensions and
certificate size. It makes only a constant number of rank computations beyond
the input-rank check (seven points and 21 pairs).

## Why this rules out both graph interpretations

Graphic matroids are regular: an oriented vertex-edge incidence matrix
represents the same cycle dependencies over every field. Their duals are
cographic and regular as well. Regularity is preserved by deletion and
contraction, while F7 is not regular. Hence a verified F7 minor excludes both
classes. This rules out an exact graphic/cographic matroid representation of
the code, not every possible graph-based algorithm or extended formulation.

For a primary research cross-check, Jim Geelen and Bert Gerards,
*Regular Matroid Decomposition Via Signed Graphs*, Journal of Graph Theory
48 (2005), 74-84, explicitly identify F7 among the nonregular excluded minors
for the union of graphic and cographic matroids on page 75, first section.
[Author-hosted paper](https://www.math.uwaterloo.ca/~jfgeelen/Publications/regular.pdf)
and [publisher DOI](https://doi.org/10.1002/jgt.20037).
The implication above uses only the necessary obstruction direction, not a
complete recognition or decomposition algorithm.

## Bounded discovery and its costs

`find_fano_minor(columns, max_trials=256, seed=8128)` uses a private seeded
random generator, so runs with the same input, seed and budget are deterministic.
Each trial shuffles original coordinates, greedily selects rank(M)-3 independent
columns to contract, and reduces every column modulo their span. If all seven
nonzero quotient vectors occur, it retains their first representatives, records
explicit quotient labels and calls the independent verifier.

The returned search counters are the number of trials, vector reductions and
integer XOR operations. These counters include the initial input-rank pass and
the explicit-label construction, but exclude the independent verifier's work.
The caller can measure end-to-end time separately. With ambient bit dimension b,
one trial uses O(n b) bit-vector elimination steps plus sorting at most b pivots
per reduction; Python integer operations themselves cost up to O(b) bit work.
The fixed trial budget bounds discovery effort but provides no completeness
guarantee. `UNKNOWN` means no certificate was found under this bounded strategy;
it never means graphic, cographic, regular, or F7-minor-free.

On the saved v17 inputs, seed 8128 succeeds after respectively 14, 15, 1, 1, 1
and 2 trials for n=18,20,22,24,26,28. These are discovery counts, not asymptotic
complexity evidence. The smallest example contracts original zero-based indices
[12,11,9,13,6,14] and retains [0,1,2,5,8,16,17].

The n<=26 internal-4-connectivity certificates and the saved balanced-cut width
lower bounds remain separate evidence. In particular, this Fano certificate
does **not** fill the n=28 internal-4-connectivity gap, and does not certify any
large explicit sample beyond the stored finite matrices.

Run `python -m unittest -v test_fano_certificate` from this directory. Tests
cover the literal Fano plane, an explicit nonempty contraction, every saved
random core, K5 as a negative control, deterministic budgets, and corrupted
certificates.
