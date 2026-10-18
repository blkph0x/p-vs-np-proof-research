# Exact interval support and the limit of separate residue tests

This is an exact coefficient-positivity method for products
P(z)=product_i(z^a_i+z^b_i), with nonnegative binary integer exponents.
It is not a polynomial algorithm for arbitrary inputs and does not resolve
P versus NP. No novelty is claimed. All results below have direct proofs;
the sibling packing theorem supplies the previously checked SAT reduction.

## Positive algorithm: keep entire runs of reachable weights

Let R_0={0}. For target W, define

    R_i=((R_(i-1)+a_i) union (R_(i-1)+b_i)) intersect [0,W].

Nonnegative future weights make the truncation sound. Every coefficient of
the product counts choice words and is nonnegative. Thus [z^W]P>0 exactly
when W belongs to R_q; multiplicities are unnecessary for this decision.

Represent R_i by its maximal closed integer intervals. Shifting each previous
interval twice, clipping to W, sorting and merging overlapping or adjacent
intervals gives the exact recurrence. A bit witness is recovered backwards:
for each step choose a_i or b_i whose subtraction belongs to R_(i-1).
An independent verifier uses a sweep of interval-start and interval-end
coverage events, checks all layers against the external original request,
and then checks the witness's original weight. It does not call the producer.

If layer i has K_i intervals, the implementation uses
O(sum_i K_(i-1) log(K_(i-1)+1)) comparisons and integer additions, plus the
input scan and witness recovery. Each stored endpoint has O(log(W+2)) bits;
intermediate additions also charge the input exponent bit lengths. A more
precise polynomial bound includes the maximum exponent bit length and q.
The certificate contains O(sum_i K_i) endpoint pairs. None of these statements
bound K_i polynomially for general inputs. Caps apply to intervals, total
retained intervals and generated spans; exhaustion returns UNKNOWN without
a decision. The verifier has its own limits and returns UNKNOWN on exhaustion.
The interval cap is checked on the candidate next layer before retaining it;
constructing that candidate uses at most twice the previous layer's interval
count. UNKNOWN work statistics include that candidate's peak but count only
completed layers in the retained total.

## A compact all-size failure of separate modular sieving

For integer q>=1 let L=2^q and take the q+1 choice pairs

    (0,1),(0,2),...,(0,2^(q-1)),(0,2L),   target W=L.

The first q factors have every weight in [0,L-1], exactly once, by binary
representation. The last factor shifts a second copy by 2L. Therefore

    support(P) = [0,L-1] union [2L,3L-1],
    P(z) = (1+z^(2L)) (1+z+...+z^(L-1)).

The target L is absent, strictly between the minimum and maximum; the gcd
of the positive weights is one. A range or gcd test cannot decide this case.

For EVERY integer modulus 1<=M<=L, however, choose s=L mod M. Then
0<=s<M<=L, so s belongs to the first block and s is congruent to L modulo M.
The binary digits of s, with final choice zero, are an explicit original
choice witness. Consequently every separate residue-attainability test with
modulus at most L accepts, including adaptive selections and arbitrarily
many such tests. A method that rejects only when one such test rejects must
use a modulus larger than L on this family. A dense algorithm enumerating
all residues for that rejecting modulus has superpolynomial work in the
O(q^2)-bit explicit input encoding. This is a limitation of that particular
separate-test rule and dense implementation, not of all algebraic methods.

Many moduli can have a large lcm while these independent tests still accept:
they may choose different words. A simultaneous test requires one common
word and cannot substitute the conjunction of existential statements.

The interval method solves this entire family with ONE retained interval
per layer, since it truncates above L. It represents 2^q reachable values
without listing them. There is also a short geometric-series identity
(1-z)P=(1-z^L)(1+z^(2L)). These facts show that the family is easy and that
failure of the modular tests does not establish computational hardness.

## Exact fragmentation control

For q>=1, use (0,4^i), i=0,...,q-1 and target sum_i 4^i. All 2^q sums are
distinct base-four strings with digits zero or one. The lowest digit gives
consecutive pairs; distinct choices of the higher digits separate those
pairs by gaps of at least two missing integers. Thus the canonical support
has exactly 2^(q-1) intervals. This interval representation is exponential
on a family whose membership is easily tested by inspecting base-four digits.
It is not a lower bound for other representations or for SAT algorithms.

## Controls on the actual SAT encoding

The saved experiment also uses the existing base-six SAT encoder. For small
formulas it checks original Boolean assignments independently. Exact interval
results must agree with those assignments; feasible results also decode to
an original satisfying matching. For larger easy SAT controls, an independently
constructed original witness verifies satisfiability even when interval growth
hits a cap. These prevent a successful specially structured family from being
mistaken for universal coverage.

Run `python -m unittest -v test_intervals` and `python run_experiments.py`
in this directory. RESULTS.json binds saved requests and proof layers to
current source hashes. Written arguments are not proof-assistant formalized.
