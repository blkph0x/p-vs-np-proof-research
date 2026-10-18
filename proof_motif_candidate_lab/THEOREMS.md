# Soundness statements

## OR-collapse macro

Given

    C = r OR x_2 OR ... OR x_w

and binary clauses

    r OR not x_i

for every i>=2, successively resolve C with those binary clauses on x_i.
After w-1 resolution steps the result is the unit `(r)`.

The implementation constructs and replays this proof.

## Equality motif

The pair of clauses

    not x OR y
    x OR not y

is exactly x <-> y. A class is admitted only after both directions to its representative
are present.

## AMO motif

If every pair x_i,x_j in a set has the clause

    not x_i OR not x_j,

then no satisfying assignment can set two members true. Therefore the set entails

    sum_i x_i <= 1.

The miner accepts only complete conflict cliques.

## Direct parity block

A full-width clause excludes exactly one Boolean assignment on its support.

For arity k, a direct parity CNF contains exactly 2^(k-1) such clauses, and their excluded
assignments are precisely one parity class.

The fixed-arity miner accepts a block only after checking this condition exactly.

## Direct ITE block

For four variables z,c,a,b, the direct full-width CNF for

    z = ite(c,a,b)

contains exactly one clause excluding each of the eight falsifying assignments.

The miner tries the constant 24 role permutations and accepts only exact truth-table
equality.

## Receiver affine candidate

Let the source proof derive fixed Boolean values for every variable in a trusted affine
receiver row

    XOR_{v in S} v = b.

If the source-fixed parity is p != b, then

    XOR_{v in S} v = p

is a sound interpolant between those source facts and the receiver row.

The receiver row is used only after exact membership in the trusted affine theory database
is verified.

## Receiver PB candidate

For a trusted positive-weight receiver inequality

    sum_v w_v x_v <= B,

the source's fixed-true variables imply the lower bound

    sum_{v fixed true} w_v x_v >= L

with L equal to their weight sum.

If L>B, this lower bound is a valid source consequence and contradicts the trusted receiver
inequality.
