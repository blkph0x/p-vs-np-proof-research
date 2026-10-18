# Cancellation, overlap and the missing rank conclusion

P versus NP remains unresolved. This note separates the project's elementary
proofs from a relevant published theorem. No solver implementation relies on
the external theorem, and no novelty claim is made.

The local [positive-cover theorem](affine_positive_cover_limits_lab/THEOREM.md)
proves the following for the normalized indicator psi of m disjoint positive
three-variable clauses:

    max_phi |<psi,phi>|^2 = (7/8)^m,

where phi is any normalized real affine quadratic atom. Its proof actually
bounds arbitrary unit-modulus phases on affine supports, so it also bounds
the usual complex stabilizer atoms; the positive full-cube atom attains
equality. The same local proof gives

    (sum_j |alpha_j|)^2 >= (8/7)^m

for every normalized-atom expansion of psi. This is an exponential coefficient
weight bound. It is not an exponential piece-count bound.

Stabilizer rank and stabilizer extent distinguish these two measures in the
established literature: rank minimizes the number of atoms; extent minimizes
the squared coefficient l1 norm over normalized stabilizer decompositions.
Their relationship is not an identification. See Bravyi et al.,
[Simulation of quantum circuits by low-rank stabilizer decompositions](https://arxiv.org/abs/1808.00128).

Kalra and Sinha's published [Stabilizer Ranks, Barnes Wall Lattices and Magic
Monotones](https://quantum-journal.org/papers/q-2026-07-29-2179/) gives a
quantitative rank-to-fidelity inequality. In [Theorem 2 / Section 3,
Theorem 33](https://arxiv.org/html/2503.04101v3#S3), a normalized rank-k state u
and a normalized state v satisfy

    |<v,u>| / sqrt(F_S(v)) <= sqrt(e) (2k)^((2k+1)/2).

Here F_S is maximum squared stabilizer overlap. The paper's proof uses a
Barnes--Wall lattice minimum-length fact, Minkowski's theorem and a Gram
determinant estimate. Those external lattice premises are not independently
reproved or formally verified in this project. The displayed application
below is an inference using that published theorem, not a new local theorem
or a result inferred from experiments.

Taking u=v=psi and inserting the independently proved overlap value gives

    (8/7)^m <= e (2k)^(2k+1).

Taking logarithms yields m log(8/7) <= 1+(2k+1)log(2k), hence only the
asymptotic lower bound k=Omega(m/log m) from this argument. This also applies
to the more restricted real rational affine representation: every such
normalized atom is an allowed complex stabilizer atom, so allowing the larger
dictionary cannot make its minimum rank larger. This is a polynomial lower
bound and supplies no superpolynomial barrier or P-versus-NP conclusion.

The project's [conditioning counterexample](affine_gram_conditioning_lab/THEOREM.md)
shows why a tempting stronger shortcut fails. An independent set of n+1
normalized affine indicators has smallest Gram eigenvalue between
2^(-(n+1)) and 2^(-n). In the original indicator coordinates it represents one
pin using only coefficients +1 and -1. Thus universal polynomial conditioning
of independent affine dictionaries is false, and poor normalized conditioning
alone does not imply exponential coefficient encoding length. The target has
rank one; this does not establish bad conditioning for its minimum dictionary.

There is a further algorithmic distinction. The disjoint-clause family has an
immediate satisfying assignment and exact model count 7^m. Componentwise
elimination computes it efficiently without constructing a whole-function
decomposition. Even a superpolynomial rank lower bound for that entire truth
function would not by itself establish hardness of its SAT decision or count.
The general research task still needs an all-input algorithm with a proved
polynomial total cost, or an unrestricted computational lower bound.
