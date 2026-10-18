# Random affine isolation control

The new isolation theorem gives a precise randomized bridge from SAT to unique
SAT with XOR constraints. For a solution set of size `s`, a uniformly random
binary affine hash of rank `ceil(log2(s))+1` isolates one solution with
probability at least `3/16`. The proof uses exact first and second moments and
holds for every finite solution set.

This is not a P=NP algorithm. It only says that a polynomial unique-SAT/XOR
solver would yield an RP algorithm for SAT after trying the possible ranks and
repeating independent hashes. The missing unique-solver step remains explicit.

The local suite exhausts all nonempty assignment sets on three variables and
checks the exact isolation probabilities; the independent replay uses direct
parity arithmetic, verifies the pairwise-uniform hash family and replays 700
seeded survivor queries. Source hashes remain unchanged throughout.

