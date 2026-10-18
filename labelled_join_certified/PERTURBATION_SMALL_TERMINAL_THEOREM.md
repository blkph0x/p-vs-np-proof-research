# Deterministic small-terminal perturbation solver

Let B be an r-by-m binary matrix with at most two ones in every column. Let U
be an r-by-p binary matrix, and let the label of coordinate e be the p-bit
column V_e. For a target s, the system

    (B + U V)x = s

is equivalent to the disjoint union, over all p-bit values z, of

    Bx = s + U z,       XOR of V_e for selected e = z.

The implementation converts each column of B into an edge of a graph with one
ground vertex. The first equation selects a terminal set T_z; an odd number of
visible terminals is completed by the ground vertex. The second equation is
the edge-label target. `labelled_tjoin.solve_tjoin` computes the minimum
nonnegative edge weight for that boundary and label, using all terminal
pairings and its disconnected Eulerian label closure. For z=0, an empty
solution is excluded only on the branch with s+Uz=0 when the caller asks for a
nonzero word; the edge-pinning proof in `solve_nonempty` then handles loops,
zero-cost edges and disconnected cycles exactly.

Every z is enumerated. If all branch certificates are exact, taking the
minimum over their exact minima is therefore exact. A branch cap or nested
solver cap returns UNKNOWN with no aggregate optimum. The verifier checks all
branch metadata, independently replays each labelled-T-join certificate,
recomputes the aggregate minimum, and checks the returned word against the
original matrix B+UV and the original objective.

The `prepare_perturbation` and `solve_original` APIs add an explicit binding
layer. They reconstruct every row of B+UV from the supplied column masks,
reject a decomposition that differs from the original H, and retain H and the
decomposition in the outer certificate. `verify_original` repeats that check
before replaying the nested branch proof. A valid branch proof therefore cannot
be reused for a different original matrix by merely changing metadata.

The work is deterministic and fixed-parameter in p and in the largest terminal
set: it performs 2^p labelled T-join calls, each with the existing
terminal-subset dynamic program. This is a useful exact extension of the
supplied graph class, but it is not a polynomial algorithm for arbitrary
matrices. In particular, the label dimension can grow with the input. The
controls in `test_small_terminal_perturbation.py` preserve the known failure
modes: an inconsistent one-edge branch, a cheapest path with the wrong label,
a disconnected cycle needed for label correction, and exhaustive random
comparison with direct original-assignment enumeration.
