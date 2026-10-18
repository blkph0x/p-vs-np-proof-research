# Bounded XOR-chain closure audit

The one-step hidden-XOR audit can be extended along an auxiliary chain, but
unbounded closure must expose its resource policy. This audit keeps only exact
three-variable parity blocks and repeatedly joins a frontier relation with a
known relation when their supports share exactly one variable. The shared
variable cancels. Every derived row carries the symmetric difference of the
source block IDs as its proof certificate.

The positive fixture has five chained blocks:

```text
(x0 XOR x1 XOR t0) = 0
(t0 XOR x2 XOR t1) = 1
(t1 XOR x3 XOR t2) = 0
(t2 XOR x4 XOR t3) = 1
(t3 XOR x5 XOR t4) = 0
```

With four closure rounds, the checker derives
`x0 XOR x1 XOR x2 XOR x3 XOR x4 XOR x5 XOR t4 = 0`, backed by all five
source blocks. The independent reviewer reconstructs the local parity blocks,
repeats the bounded join, and checks the exact relation/proof list. A mutation
in the third block removes the target relation. A branching eight-block fixture
exceeds an explicit relation cap and returns `UNKNOWN_CAP`; it is never treated
as a complete negative result.

The bounded algorithm is polynomial for fixed caps in the explicit block list,
but the cap is part of the result. Increasing the support or relation budget
can grow the frontier rapidly, and arbitrary XOR-span discovery or general
auxiliary-circuit discovery remains outside this audit. The result therefore
strengthens the proof-producing motif language without claiming a general SAT
algorithm or a P-versus-NP resolution.

Run:

```text
python run_xor_closure.py
python review_xor_closure.py
```

