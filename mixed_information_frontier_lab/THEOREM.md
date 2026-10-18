# Mixed future-equivalence frontiers

This lab measures the exact interface needed by a constraint bundle at a
variable cut. For a prefix assignment $p$, define its residual signature to be
the set of suffix assignments $s$ for which the full assignment $p\Vert s$
satisfies every constraint. Two live prefixes are future-equivalent exactly
when their residual signatures are equal. The executable analyzer stores these
signatures as bit sets; the independent review recomputes them as explicit
suffix tuples.

## Three exact controls

### Duplicate parity

Suppose six constraints all impose the same parity equation on all twelve
variables. A prefix has only one relevant bit: the parity of its first six
coordinates. The six nominal two-state machines therefore have a product upper
bound of $2^6=64$, but the conjunction has only two distinct residual
signatures. This is a semantic quotient, not a timing observation.

### Independent crossing parity

For $i=0,\ldots,m-1$, impose

\[
x_i\oplus x_{m+i}=0.
\]

At the cut between the first and second blocks, each prefix vector determines a
different required suffix vector. Therefore every one of the $2^m$ prefixes is
live and has a distinct residual signature. The product state bound is tight:
no quotient can merge these prefixes without changing the set of valid futures.

### Exact cardinality plus parity on one scope

If the same $n$ variables obey $\sum_i x_i=K$, then their parity is already
fixed to $K\bmod 2$. Adding a parity constraint on that same scope is either
redundant or inconsistent. At a cut after $c$ variables, a live prefix is
classified by its prefix count $a$; its suffix must have count $K-a$. Hence at
most $c+1$ future classes occur, even though the naive local summaries count a
parity bit and a count separately. For the twelve-variable, $K=6$, midpoint
control, all seven counts $a=0,\ldots,6$ occur and give seven distinct classes.

Duplicate cardinality constraints provide the same quotient with a nominal
$7^5=16{,}807$-state product and only seven future classes.

The collapse depends on scope. If the parity constraint sees only three prefix
variables and three suffix variables while cardinality still sees all twelve,
the midpoint summary is the pair (prefix count, partial parity). The six
feasible count/parity combinations at the endpoints and the two combinations
for each interior count give ten classes, and the direct replay confirms that
all ten have distinct futures. Thus a mixed bundle can retain its full
reachable local product even when one component is a global counting constraint.

## What this establishes

The exact frontier is a quotient after composition. Local state counts can
overestimate it by an exponential factor when constraints are duplicate or
semantically dependent, while independent crossing relations can force the
full product. Any proposed universal SAT route based on frontier compression
must therefore provide a polynomially discoverable equivalence certificate and
must survive the independent crossing-parity family. The analyzer and review
are intentionally exponential oracles; they do not claim that arbitrary
future-equivalence classes can be discovered in polynomial time.
