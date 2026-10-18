# Bounded Proof-Driven Language Invention

**Status:** Executed exact prototype with an all-size fixed-parameter theorem. No proof of
P=NP or P!=NP.

## Main change

The solver no longer needs a predeclared semantic name such as XOR, AMO, or ITE for every
bounded proof fragment.

For a fragment with boundary variables x and local variables y it computes exactly

    R_F(x) = exists y . F(x,y).

The resulting Boolean relation is canonicalized under boundary-variable permutation and
assigned a fresh relation symbol:

    REL_0000, REL_0001, ...

The canonical truth table is the logical certificate. Compact ANF, affine, weight,
coordinate-quotient, OBDD metrics, and synthesized circuits are optimization layers only.

## Exact fixed-width completeness theorem

If boundary width K and local width L are fixed constants, every fragment relation can be
computed in

    O(2^(K+L) |F|)

work.

The current exact permutation canonicalizer uses

    O(K! 2^K)

additional work.

Therefore for fixed K,L the complete invention procedure is polynomial in the explicit
proof/fragments input.

There are only

    sum_(k<=K) 2^(2^k)

possible Boolean relations of arity at most K. This is an enormous constant, but it means
the dynamically invented vocabulary is **complete for all bounded-arity Boolean
interfaces**. It is not limited to a motif dictionary.

## Different encodings, one invented language

The experiment fed the registry:
- a direct four-variable parity CNF;
- a completely different encoding using two local XOR auxiliary variables.

Twelve renamed/permuted occurrences of each were observed.

Both sets were assigned the same relation identifier:

    REL_0000.

The chosen compact implementation was automatically recognized from the relation's ANF as

    AFFINE

with 13 modeled definition bits.

The registry never used an "auxiliary parity" fixture label in its semantic check.

## Generic semantic quotienting

The bounded truth table also permits exact coordinate quotienting.

A width-5 proof fragment consisting of one positive OR plus implication spokes was given to
the generic relation engine—not the earlier OR-macro recognizer.

Its exact projected relation was found to contain:
- 4 irrelevant coordinates;
- 1 fixed coordinate;
- quotient arity 0.

So the fragment was semantically reduced to one forced Boolean fact without an OR-specific
language rule.

For the five-variable equality fragment, the generic quotient checker discovered one
signed-equality class containing all 5 coordinates and an exact
quotient relation of arity 1.

A symmetric weight representation happened to be cheaper under the declared bit model,
but the equality quotient itself was still discovered and independently verified.

## Generic circuit invention

The direct ITE relation was **not** recognized using an ITE-specific synthesizer.

The generic gate grammar {NOT,AND,OR,XOR} found an exact

    5-gate

circuit for the four-variable ITE predicate.

The declared representation-cost selector still preferred the 16-bit truth-table relation
symbol, but the synthesized circuit demonstrates that the language inventor can derive a
new implementation from semantics rather than from a named motif.

## Arbitrary custom relation

A random four-variable relation was deliberately chosen for which:
- the declared truth-table representation was cheapest;
- no circuit of <=5 gates was found in the grammar;
- it had no useful weight/affine/coordinate quotient.

Forty renamed/permuted occurrences were grouped into one invented custom language:

    REL_0005.

Its certified definition is simply the exact 16-bit Boolean relation. Even this unstructured
custom relation became profitable under the recurrence accounting:

    accumulated raw cost = 1120
    setup bits            = 24
    net saving            = 536.

This is the central "language invention" result: the system can create a new exact proof
symbol even when the relation does not belong to the named library.

## One-off control

Twenty-five random one-off relations were also presented.

There were 24 distinct one-off relation IDs after accidental semantic
collisions/canonical equivalences. Of these, 17 were rejected as
unprofitable by the simple definition/call accounting.

Some one-off relations are still cheap enough relative to their direct CNF that immediate
installation can be profitable; recurrence is not artificially required.

## Measured width dependence

The fixed-width theorem should not be confused with a universal polynomial bound.

Executed random-relation timing:

| K | truth-table bits | K! | projection seconds | permutation canonicalization seconds |
|---:|---:|---:|---:|---:|
| 2 | 4 | 2 | 0.000037 | 0.000017 |
| 3 | 8 | 6 | 0.000033 | 0.000031 |
| 4 | 16 | 24 | 0.000058 | 0.000268 |
| 5 | 32 | 120 | 0.000172 | 0.002553 |
| 6 | 64 | 720 | 0.000633 | 0.034413 |
| 7 | 128 | 5040 | 0.002253 | 0.535247 |

The experiment makes the boundary visible: current permutation canonicalization already
shows factorial growth in K.

For a fixed K this is a constant and the theorem is polynomial in the overall proof size.
For growing K it is not acceptable.

If interface roles arrive already ordered, the K! canonicalization term can be dropped,
and exact relation extraction itself remains polynomial when K+L=O(log n). But the current
permutation-invariant registry does not establish such a result.

## Logical authority

Every invented symbol stores its canonical truth table as the authoritative certificate.

Compressed implementations are independently compared against that table on the bounded
interface. The OBDD entry in this prototype is deliberately only a diagnostic size metric;
it is not used as logical authority because the graph itself is not serialized.

This maintains the project's core rule:

    synthesis proposes; exact checking authorizes.

## What this accomplishes

Within bounded proof interfaces we no longer have a fixed semantic vocabulary problem.

The system can:
1. project away local auxiliaries;
2. canonicalize a relation across renamed variables;
3. invent a fresh exact relation symbol;
4. discover generic coordinate quotients;
5. synthesize ANF/affine/weight/circuit implementations;
6. reuse the symbol across recurring proof fragments;
7. reject installation when the economics do not repay it.

## Remaining barrier

The universal problem has moved to **interface growth and fragment discovery**.

Bounded-arity relation invention is complete, but arbitrary SAT may force useful interfaces
whose width grows with the instance.

The next target is therefore to combine this exact bounded inventor with the earlier
decomposition/quotient machinery:

    large proof region
      -> polynomially discover low-information boundary
      -> bounded relation invention inside that boundary.

A P=NP route would need a theorem that such bounded/logarithmic interfaces can always be
found in polynomial work. We do not have that theorem.


## Proof-sub-DAG bridge

The earlier structural proof miner was then wired directly into this bounded semantic
inventor.

The structural layer only proposes repeated resolution sub-DAGs. For each proposal, this
lab discards the motif name and recomputes the exact relation from the sub-DAG's leaf
clauses.

Results:

| repeated sub-DAGs | raw boundary width | recurring signature count | invented relation IDs | ignored coords | fixed coords | net saving |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 4 | 8 | 1 | 3 | 1 | -4 |
| 32 | 4 | 32 | 1 | 3 | 1 | 20 |
| 64 | 5 | 64 | 1 | 4 | 1 | 243 |
| 128 | 5 | 128 | 1 | 4 | 1 | 499 |

All repeated fragments in each run collapsed to one invented relation.

The semantic checker discovered that each apparently width-4/5 proof fragment actually
transmits only one forced Boolean coordinate; all other boundary coordinates are irrelevant
to the relation.

The economics also behaved correctly: the eight-occurrence width-4 case was not yet worth
installing under the declared setup/call accounting, while recurrence eventually made the
same invented relation profitable.

This is the first end-to-end version of:

    repeated proof sub-DAG
      -> structural proposal
      -> exact existential relation extraction
      -> new relation symbol
      -> semantic quotient
      -> profitability decision.

The structural miner still proposes the fragment boundary. The language inventor is
complete only **after** such a bounded boundary has been supplied.
