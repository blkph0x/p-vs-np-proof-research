# Connected affine coupling: order can beat character rank

The character solver correctly treats a connected cumulative-parity family as
rank (m), so it has (2^m) character terms. The audited weighted affine DAG
provides a different exact route: preserve affine constraints as compact
messages and choose an order that follows the chain.

For each block (i), the original factors are

\[
 (a_i\lor b_i),\qquad p_0=0,
 \qquad p_i\oplus p_{i-1}=0\ (i>0),
 \qquad p_i=a_i\oplus b_i.
\]

All equations are independent, and the interaction graph is connected. The
equations force every pair to have even parity; the OR factor then forces
((a_i,b_i)=(1,1)), so the exact count is one for every (m). This direct
family argument is used only as an external control.

The saved weighted-DAG run uses the same factor occurrences and an interleaved
order `[OR_0, parity_0, OR_1, parity_1, ...]`. It returns an exact, independently
verified value for (m=1,2,4,8,16,32,64,128). The 128-block certificate has
peak retained terms three, 1,044 pre-merge products and 51,685 producer work
units. A deliberately poor order lists all OR factors before all parity factors;
the same (m=12) request reaches its explicit one-million-work cap with no
value. The run records this as `UNKNOWN`, never as UNSAT.

This is evidence about representation and order. It does not prove that an
order can be discovered efficiently for arbitrary SAT, and it does not turn
the easy control family into a P=NP result. It does show that affine rank alone
is too crude: connected rank (m) can coexist with a compact exact
elimination route when the interaction order exposes a narrow chain.

The independent review regenerates all nine controls, replays all eight exact
certificates through the weighted-DAG verifier, checks dependency hashes, and
confirms the poor-order cap has no value.
