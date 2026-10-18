# Integrated interpolation facts

For the benchmark A-side, every group representative r_i is entailed true.

Therefore A entails all of:
- AND_i r_i;
- XOR_i r_i = g mod 2;
- sum_i r_i >= g.

The B-side entails the opposite parity of the representatives.

Hence:
- the conjunction is a valid Craig interpolant;
- the XOR relation is a valid Craig interpolant;
- the PB all-true bound is a valid Craig interpolant;
- no single representative literal is sufficient in general, because B has models with
  that representative true and the required opposite global parity.

The proof extractor independently derives the Boolean conjunction from the resolution DAG;
the portfolio then validates the stronger-language alternatives against the same A/B
semantics.
