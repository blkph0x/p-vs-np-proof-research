# RM(2,5) SOS moment separation

The exact full level-eight projection-marginal witness has objective `31/5`.
It is feasible for every saved local table and every containment marginal, but
it is not a valid second-order Boolean moment sequence.

Let

    t = sum_{p != 0} x_p.

Every Boolean assignment satisfies the globally valid square inequality

    (5t - 31)^2 >= 0.

The full witness gives exact singleton moment `E[x_p] = 1/5` for every nonpin
point and exact pair moment `E[x_p x_q] = 1/35` for every distinct nonpin pair.
Therefore

    E[t]   = 31/5,
    E[t^2] = 31/5 + 2 * 465/35 = 1147/35,
    E[(5t-31)^2] = 25(1147/35) - 310(31/5) + 961 = -992/7.

After dividing by 25, the pseudo-expectation of `(t-31/5)^2` is `-992/175`.
The Boolean control enumerates all 32 possible integer values of `t`; its
minimum scaled square is one, attained at `t=6`. The negative value is thus an
exact separation between the local-marginal witness and a valid global moment
constraint.

This is a finite hierarchy diagnostic. It does not prove that the
moment-strengthened relaxation is integral, does not provide a separation
algorithm for arbitrary SAT, and does not resolve P versus NP.

Replay from this directory:

    python run_reed_muller_sos_moment.py
    python REED_MULLER_SOS_MOMENT_INDEPENDENT_REVIEW.py
    python -m unittest -v test_reed_muller_sos_moment.py

The independent replay is pure standard library and rejects a mutated moment
certificate.
