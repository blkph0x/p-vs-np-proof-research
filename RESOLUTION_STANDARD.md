# Research objective and acceptance standard

The objective is to resolve whether P=NP. The investigation must allow either
answer and must not treat the preferred direction as an assumption. As of this
working checkpoint, **neither answer has been proved**. The official problem
description remains the reference for the question:
[Clay Mathematics Institute](https://www.claymath.org/millennium/p-vs-np/).

## What would establish P=NP here

A sufficient result is a uniform deterministic algorithm for every SAT instance,
or another proved NP-complete problem, together with complete arguments that:

1. Every allowed input is handled, including NO instances and adversarial inputs.
2. The result is correct, including all transformations and reconstructions.
3. Total bit complexity is bounded by one fixed polynomial in encoded input size.
4. That bound includes discovery, decomposition, representation construction,
   arithmetic precision, intermediate objects, certificates, and verification.

An exact solver with an exponential fallback is useful but does not meet this
standard. A budgeted solver returning UNKNOWN is also not a decision algorithm
for all inputs. Bounds whose exponent depends on the input are not a fixed
polynomial bound. A polynomial algorithm for a promised family needs a separate
proof that the promise covers all instances before it can resolve P=NP.

## What would establish P!=NP here

A sufficient negative result must exclude every deterministic polynomial-time
algorithm for an NP problem. Large trellises, hard cases for this portfolio,
failed heuristics, fractional LP solutions, and limitations of particular
representations do not exclude all other algorithms. None is labeled a
P-versus-NP lower bound in this project.

## Evidence labels

- **Elementary theorem:** an all-size mathematical argument with explicit scope,
  reviewed independently where possible. These are written mathematical proofs;
  they are not claimed to be formal proof-assistant developments.
- **Finite exhaustive audit:** every member of a specifically bounded set was
  checked. The set and checker are stated; no asymptotic extrapolation follows.
- **Certificate-verified result:** a supplied instance and certificate pass a
  documented checker. Distinguish feasibility witnesses from optimality proofs.
- **Measured result:** observed time, state count, or operation count for a saved
  instance. It does not establish asymptotic complexity.
- **Unresolved proposal:** a precise missing assertion, kept separate from results.
- **Refuted proposal:** a counterexample or scoped impossibility proof is retained
  as a regression control so that the same assumption is not reused silently.

For the new native solver, maximum-weight matching optimality is certified by
integer primal/dual equality and all edge inequalities. The independent checker
does not accept a matching merely because the producer calls it optimal. Graph
metric and cycle computations remain explicit polynomial algorithms with
independent finite brute-force tests. Row transformations are checked against
the original matrix, and affine requests bind both matrix and target syndrome.

Source hashes, exact rational arithmetic where needed, deterministic seeds,
saved certificates, and separate discovery/solving costs support reproduction.
Neither a successful test suite nor agreement between two programs replaces an
all-size proof of a proposed polynomial algorithm.

## Current mathematical focus

The positive graph-plus-exception solver shows how to replace explicit states
with a stronger native optimization method. Counting already rules out a
universal logarithmic-exception representation using row changes alone.
The next generalization must address the NP-complete degree-three incidence
instances directly, rather than calling their columns exceptional and omitting
the resulting exponential cost.

The LP investigation tests a different possible generalization: whether richer
globally valid inequalities can replace the missing native solver. An exact
polyhedral description without an efficient separation algorithm is not enough;
an efficiently separable relaxation without integrality is not enough either.
