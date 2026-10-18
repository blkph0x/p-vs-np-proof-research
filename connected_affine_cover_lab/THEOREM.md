# Connected path CNF and a nonnegative affine-support lower bound

Let

\[
F_n=\bigwedge_{i=0}^{n-2}(x_i\lor x_{i+1}),
\qquad S_n=\{x\in\mathbb F_2^n:F_n(x)=1\}.
\]

The clause graph is a connected path with $n$ variables and $n-1$ clauses.
The satisfying assignments are binary strings with no adjacent zeros, so the
two-state recurrence gives

\[
|S_n|=\operatorname{Fib}_{n+2},
\qquad \operatorname{Fib}_2=1,\ \operatorname{Fib}_3=2.
\]

## Affine-support dimension bound

Consider an affine subspace $H=a+V\subseteq S_n$, with direction space
$V\leq\mathbb F_2^n$. Let $\ell_i:V\to\mathbb F_2$ be the $i$th coordinate
linear functional of a direction vector. Projecting $H$ onto coordinates
$(i,i+1)$ gives an affine subspace of $\mathbb F_2^2$ that avoids $(0,0)$,
because that pair is constrained by $x_i\lor x_{i+1}$. An affine subspace of
$\mathbb F_2^2$ has size $1$, $2$, or $4$; avoiding $(0,0)$ rules out size $4$.
Therefore

\[
\operatorname{rank}\{\ell_i,\ell_{i+1}\}\leq 1
\quad\text{for every }i.
\]

Along every consecutive run of nonzero coordinate functionals, adjacent
functionals are equal: over $\mathbb F_2$, two nonzero linearly dependent
functionals are identical. Distinct runs are separated by zero functionals.
There can be at most $\lceil n/2\rceil$ such runs, so the span of all
$\ell_i$ has dimension at most $\lceil n/2\rceil$. The coordinate map from
$V$ into $\mathbb F_2^n$ is injective, hence

\[
\dim H=\dim V\leq\left\lceil\frac n2\right\rceil,
\qquad |H|\leq 2^{\lceil n/2\rceil}.
\]

The bound is attained: fix coordinates $1,3,5,\ldots$ to one and vary
$0,2,4,\ldots$. Every resulting assignment satisfies the path clauses, and
the support has dimension $\lceil n/2\rceil$.

## Consequence for nonnegative decompositions

Suppose the exact path indicator has a finite decomposition

\[
1_{S_n}(x)=\sum_{j=1}^t c_j\,1_{H_j}(x),
\qquad c_j\geq 0,
\]

where each $H_j$ is an affine support and zero-coefficient terms are removed.
At an assignment outside $S_n$, the left side is zero and every summand is
nonnegative. Thus every $H_j\subseteq S_n$. Every satisfying assignment must
belong to at least one $H_j$, so the union bound and the dimension result give

\[
t\geq
\left\lceil\frac{\operatorname{Fib}_{n+2}}
{2^{\lceil n/2\rceil}}\right\rceil.
\]

This grows exponentially because $\varphi/\sqrt2>1$. At $n=256$, the
certified lower bound is $1{,}090{,}151{,}200{,}392{,}118$ pieces, despite the
formula having only 256 variables and 255 connected clauses.

The sign restriction is essential. Signed affine sums may cancel on rejected
assignments, so this theorem does not lower-bound the signed affine DAG or
arbitrary algorithms. The path CNF is itself easy to count by a recurrence and
has immediate witnesses; the result is a barrier for one proposed positive
representation language, not a P-versus-NP separation.

The executable controls exhaustively enumerate affine cosets through $n=6$,
verify the maximum contained dimension, and independently replay the recurrence
and lower bound through $n=256$.

## Scope check: a richer weighted route escapes the cover bound

The cover theorem charges only nonnegative affine supports. It does not charge
the compact signed boundary messages used by the weighted affine DAG. An
independent replay reconstructs the same path factors for $n=8,16,32,64,128$,
obtains the Fibonacci count exactly in every case, and verifies every saved
certificate. The largest retained message has four terms. Those results are
recorded in `WEIGHTED_RESULTS.json` and `WEIGHTED_REVIEW.md`; they are an
explicit escape route from this restricted representation barrier, not evidence
for a general polynomial SAT algorithm.
