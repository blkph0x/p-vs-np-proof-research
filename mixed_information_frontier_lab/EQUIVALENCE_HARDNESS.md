# Exact residual-equivalence discovery is coNP-hard

Fix a variable order and a cut. For a prefix assignment $p$, let

\[
R_p(s)=F(p\Vert s)
\]

be the residual Boolean function on suffix assignments. A complete
future-equivalence quotient must decide when two such residual functions are
identical, including the all-zero (dead) residual.

Take an arbitrary CNF $G(y_1,\ldots,y_m)$ and introduce one selector variable
$z$. Define

\[
F(z,y)=G(y)\land\lnot z.
\]

At the cut immediately after $z$,

\[
R_{z=0}(y)=G(y),\qquad R_{z=1}(y)=0.
\]

Consequently,

\[
R_{z=0}=R_{z=1}quad\Longleftrightarrowquad G\text{ is unsatisfiable}.
\]

The transformation is linear in the size of $G$, and UNSAT is coNP-complete.
Thus exact residual-equivalence testing for arbitrary CNF frontiers is
coNP-hard. Independently, deciding whether the first residual is nonempty is
SAT-hard, since $R_{z=0}$ is nonempty exactly when $G$ is satisfiable.

This does not prove P $\ne$ NP and does not rule out a different polynomial SAT
algorithm. It does rule out treating an explicit arbitrary-CNF
future-equivalence query, or a quotient procedure that must answer arbitrary
prefix-pair class queries, as a free preprocessing step. A symbolic quotient
could avoid exposing such pair answers, but then it needs its own correctness
and complexity theorem. Any universal frontier route must either restrict the
constraint catalogue, provide a special structural certificate, or pay for a
computation whose difficulty already contains SAT/UNSAT. The small
exhaustive tests in `test_equivalence_reduction.py` validate the reduction on
SAT and UNSAT controls; the claim itself follows from the all-size reduction
above.
