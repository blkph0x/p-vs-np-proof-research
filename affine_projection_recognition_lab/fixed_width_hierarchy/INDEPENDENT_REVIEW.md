# Separate-agent mathematical audit

The `research_review` agent read [THEOREM.md](THEOREM.md) independently and
reported no correction. This is an internal, separate-agent mathematical
audit, not an external referee report, proof-assistant verification, or
confirmation of novelty.

The audited theorem's SHA-256 after strict UTF-8/LF normalization is:

```text
a5f57d67320b3a07e7e612ccf1faa43de934d0f1bf1efc5e14261e291c0bf630
```

The audit checked:

- the `2k-1` maximum alternating-chain length, including the singleton-to-next-
  affine-stage dimension jump;
- longest-contained-chain parity and NP witnesses for included points only;
- total hardness for arbitrary source tuples, using disjoint prefix-SAT blocks;
- selector exclusivity and exact equality of the projection with the chain stage;
- polynomial size for each fixed width, and the warning against varying-width
  promotion;
- the nonempty-affine convention and width-zero/width-one boundary cases;
- the matching nested-difference convention in Chang's primary manuscript,
  Definition 1, PDF page 4 / printed page 3;
- all relative links in the theorem.

This audit concerns the written mathematical proof. The independently
implemented finite checker and the normal/optimized test transcripts are
separate evidence recorded in [RESULTS.json](RESULTS.json).
