# Dense redundant syntax is not semantic hardness

For $p$ independent equality pairs, use the two clauses enforcing
$x_{2i}=x_{2i+1}$. Add, for every pair of variables $(u,v)$, the clause
$(x_u\lor\lnot x_u\lor x_v)$. Each added clause is a tautology, so deleting
them preserves the Boolean function and its SAT answer. Syntactically, however,
every processed variable has a clause containing an unprocessed variable, so
the raw frontier width is $2p-1$ for every order.

With the natural order, after the first $2k$ variables the $k$ equality pairs
have two choices each. The tautologies keep all of those variables on the
frontier, so the raw state set contains at least $2^k$ distinct assignments.
The supplied-order DP therefore retains exponentially many syntactic states
even though the normalized formula has width one and is solved by the same
certificate engine with a linear state count.

This is an adversarial representation control. It justifies charging
tautology/semantic preprocessing and does not imply that SAT is hard: the
redundancy is deliberately easy to recognize.
