# Proof-producing SAT on a supplied variable order

Fix a CNF $F$ and a variable order. At cut $k$, let $B_k$ be the processed
variables that occur in a clause with at least one unprocessed variable. A
frontier state is an assignment to $B_k$ that can be extended to satisfy every
clause whose last variable has already been processed.

When the next variable is assigned, only clauses whose last variable is that
new variable become decidable. Every earlier variable in such a clause belongs
to the previous boundary, so the clause can be checked from the old frontier
state and the new bit. The new state is the restriction to $B_{k+1}$; duplicate
states are merged existentially.

An empty clause is handled as an immediate contradiction before the first
transition, with an explicit empty state set at every later cut.

Induction on cuts proves that the stored state set is exactly the set of
extendable frontier assignments. At the final empty boundary, the sole state is
present exactly when the CNF is satisfiable. The saved certificate records every
boundary, state set and transition, and the independent reviewer recomputes all
three objects directly.

If the maximum boundary size is $w$, there are at most $2^w$ states per cut and
at most twice that many one-bit transitions. With straightforward clause
checking, the supplied-order algorithm is polynomial in the input size for
fixed $w$, and exponential only in the parameter $w$.

The graph-order hardness lab shows why this does not resolve general SAT: finding
the best boundary order is itself a difficult layout problem, and a local greedy
order can be arbitrarily worse. This lab therefore proves the conditional
algorithm and its certificates without hiding order-discovery cost.
