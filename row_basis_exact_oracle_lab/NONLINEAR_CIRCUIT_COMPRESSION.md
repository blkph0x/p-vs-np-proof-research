# Polynomial-size nonlinear circuit boundary control

The binary-digit construction can be evaluated by an explicit Boolean circuit,
so it is not merely an oracle row map.  For source forms `r_i`, compute each
parity bit with a binary XOR chain.  Add the resulting bits sequentially to an
`L`-bit accumulator using ripple-carry gates:

`sum = old xor carry`, `carry' = old and carry`,

where `L=max(1,n.bit_length())` and `n` is the number of source forms.  The
final accumulator is the exact binary expansion of

`h(u)=sum_i [r_i dot u = 1]`.

If the forms have Hamming weights `d_i`, the construction uses exactly
`sum_i max(0,d_i-1)` parity XOR gates, `nL` accumulator XOR gates and `nL`
accumulator AND gates.  Its size is therefore polynomial in the explicit
source representation.  The saved explicit families use 14, 16 and 18 output
bits, although the circuit still reads every source form.

This is a boundary result, not a P=NP algorithm. Integrating the circuit into
a target solver would require preserving its constraints, objective and
nonzero semantics, and charging the resulting search or contraction cost.
The affine Walsh lower bounds do not apply to this nonlinear circuit class.
