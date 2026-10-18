# Independent circuit-boundary review

The separate evaluator checks every XOR, AND and constant clause for all 32 source assignments and reproduces every output Hamming weight. The saved frontier widths are independently recomputed from clause scopes; the producer rejects every deliberately wrong pinned output. This verifies the circuit-to-CNF bridge on the bounded control only.
