# Proof-to-Portfolio Interpolant Integration

**Status:** Executed integration prototype. No proof of P=NP or P!=NP.

## End-to-end path now implemented

The experiment now runs the full chain:

    mixed-theory resolution proof
      -> McMillan raw Craig interpolant
      -> source-driven candidate generation
      -> receiver-side exact validation
      -> language/cost selection
      -> online rent/buy policy for recurrence.

The candidate generator is not told which receiver language will win.

## Benchmark

Each of g groups has w Boolean switches.

A-side matching/Hall plus equality reasoning forces every group representative true.
B-side requires the opposite parity of the representative vector.

The resolution proof first removes all A-local group members. McMillan extraction returns

    r_1 AND ... AND r_g.

At g=256,w=8:

    Boolean variables                 = 2048
    A-local variables eliminated      = 1792
    resolution proof nodes            = 4097
    raw interpolant literals          = 256
    receiver-certified languages      = CNF-conjunction;XOR;PB
    selected language                 = XOR
    selected serialized bits          = 2057
    raw conjunction serialized bits   = 4864.

The source independently generates CNF, literal, XOR, and PB consequences. Under the
opposite-parity receiver:
- individual literals are rejected;
- raw conjunction is accepted;
- XOR is accepted;
- PB all-true is accepted;
- XOR wins the declared message-cost comparison.

At 256 representatives the modeled message costs are:

    raw conjunction = 4864 bits
    XOR              = 2057 bits
    PB               = 2065 bits.

This is not an exponential bit-size collapse. The significance is that the transmitted
object is now typed in the receiver's native algebra rather than frozen in the proof's
initial Boolean syntax.

## Audit boundary

For small instances with at most 18 Boolean variables, both the raw proof-derived
interpolant and the lifted candidates are checked exhaustively against the actual A/B
semantics.

For large instances, the same candidate validity is justified symbolically by the benchmark
invariant:

    A => every representative is true
      => XOR parity = g mod 2
      => PB sum >= g,

while B asserts the opposite parity.

## Online reuse

For the largest interface the XOR setup cost is already smaller than one occurrence's
raw-vs-XOR transmission premium, so the two-mode controller buys XOR immediately.

The more interesting online behavior occurs when quotient/macro setup is expensive relative
to one use; the standalone portfolio lab retains the <2 rent/buy controller for that case.

## What has been achieved

This closes the gap between:

    "we know a better interpolant language exists"

and

    "an actual proof interface is extracted, candidate consequences are generated from the
     sender, the receiver filters them, and a language is selected."

The remaining gap is automatic candidate discovery for structures not already exposed by
the proof metadata/theory certificates.
