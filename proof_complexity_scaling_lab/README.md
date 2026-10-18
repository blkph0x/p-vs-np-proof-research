# Proof-complexity scaling campaign

This lab runs the proof-producing CDCL baseline on two explicit adversarial
families and saves the complete resolution traces. The reviewer reconstructs
both formula families independently, replays every resolution step, checks the
terminal empty clause, and verifies the exact trace counts on the
all-assignment family.

Run:

    python run_scaling.py
    python review_scaling.py
    python -m unittest -v test_scaling.py

The campaign is a solver and proof-system scaling study. It does not establish
that every SAT algorithm is exponential and it does not resolve P versus NP.
