# Independent review of the original-CNF counting reference

Reviewed on 2026-10-18. **Clean verdict for the bounded exponential reference
and its saved original-input counts.** This document and the requested
independent audit code/result were added; implementation, tests, theorem and
saved production results remain unchanged. Run `python independent_review.py`
to reproduce the 735 mutation checks and all 744 original planted models.
[INDEPENDENT_REVIEW.json](INDEPENDENT_REVIEW.json) stores exact source hashes,
counts, complete planted model lists and the larger original requests.
The reference makes no polynomial-time SAT claim and counts logical original
assignments, not the earlier binomial-slack multiplicities.

## Correctness and original coverage

Each residual count refers to assignments of exactly the variables still
appearing in that residual formula. At a restriction of variable v, the
variables in the parent that are neither v nor present in the restricted
child can take either value independently: they occurred only in clauses
already satisfied by that restriction. The factor

`2 ** (len(parent_variables) - 1 - len(child_variables))`

is therefore necessary and correct. The factor is applied separately to
both branches, or once for a forced unit. The two branch domains are disjoint
even when they refer to the same memoized residual node. Memoizing by the
residual formula is sound because the discarded-variable multiplicity is
charged by each parent, not included ambiguously in the child's count.

Variable-disjoint components multiply. The checker does not trust the
producer's component finder: it requires nonempty child scopes, pairwise
disjoint variables, exact coverage of all canonical parent clauses, and
equality of the scope union with the parent's variables. Components need
not be maximal for this multiplication identity to hold.

Duplicate clauses, duplicate literals and tautologies may be normalized
because this is Boolean model counting. Variables lost by that normalization
are accounted for by the final factor `2 ** (n - len(root_variables))`.
An empty formula has count 1 on its empty residual scope; an indexed empty
clause forces count 0. Thus n unused original variables correctly contribute
2^n, including variables occurring only in dropped tautologies.

The certificate is bound to the separately supplied original n and every
literal occurrence through a binary request hash. Independently of that
hash, its final root must equal the checker's normalization of the entire
external formula. All child references are strictly earlier topological
indices, so cycles and forward references fail. All nodes must be reachable
from the root. Every unit and both branches must have exactly the restriction
reconstructed by the checker. Recurrence counts and free-variable factors
are recomputed, not accepted from certificate fields. These conditions close
the historical omitted-original-clause issue for this new reference.

The producer reuses the old normalization, restriction and component helpers.
The checker uses its own normalization and restriction implementations and
checks component partitions directly, rather than calling those helpers or
rerunning the producer. Some input validation, binary hashing and bookkeeping
are shared, as documented. This is executable checking with ordinary proof,
not proof-assistant formalization. Producer recursion is bounded by its depth
cap; the checker scans the supplied topological DAG iteratively.

The exponential state and proof-size scope is explicit. State formulas can
be large, component discovery is charged, and big-integer bitset operations
in the independent oracle are correctly distinguished from constant-cost
Boolean operations. UNKNOWN carries neither count nor partial proof.

## Independent checks on the frozen sources

The local suite passes all **9 tests** (0.410 seconds in this review), using
`python -m unittest discover -s . -p 'test*.py' -v` in this directory.
All **58 saved original proofs** were independently replayed, and each count
agreed with its saved direct or closed-form control. All **10 recorded source
references** matched their current hashes.

An additional read-only audit with seed 2026101902 generated **400 original
formulas**, including repeated literals, tautologies, empty clauses and unused
variables. Direct enumeration covered **23,456 original assignments**.
Every original count agreed. Each of the **735 residual node counts** was
also checked by direct enumeration of that node's actual variable scope;
original and residual checks together covered **34,248 assignments**.
All **735 single-node count increments** were rejected. For each positive
formula, appending an empty external clause was rejected even after replacing
the stored hash with the new request hash. For an already contradictory
formula, a proof may validly describe the same normalized Boolean function
after another redundant empty occurrence is added; rejecting all such
semantically equivalent rebinding is not required for count correctness.

## Separate verification of the three larger counts

The two planted originals were counted again by a separate assignment search
that scans their original positive/negative literal masks. It maintains an
explicit assigned-variable mask, repeatedly applies directly observed units,
and branches on the first unresolved original variable. It uses no component
decomposition, no memoization, no legacy restriction helpers, and no saved
certificate. When all clauses are satisfied it explicitly expands the still
unassigned variables into full original models. Every generated model was
checked against every original clause and inserted into a set to reject
duplicates.

| Original request | Independent count | Search calls |
|---|---:|---:|
| `structure_planted_mixed_3CNF_n24_m96` | 64 | 195 |
| `structure_planted_mixed_3CNF_n32_m128` | 680 | 361 |

All **744 complete original models** passed the clause checks. Exhausting both
branches after sound unit restrictions proves these are complete counts;
the model list alone would establish only a lower bound. The audit imposed
a one-million-call limit and completed far below it.

For `legacy_sliding_64_radius2_seed17`, an independently written backward
suffix recurrence retained the values of the two original variables shared
with the next clause. It evaluated each original signed clause before
extending to the third bit. Summing the four initial boundary assignments
gave **10,620,580,317,322,270**, with **260 memoized suffix states**. This agrees
with the saved count and is distinct in implementation from the producer's
branch/component DAG and the saved forward transfer oracle. The small
frontier is justified by this particular original consecutive-triple family;
it gives no bound for arbitrary CNF.
