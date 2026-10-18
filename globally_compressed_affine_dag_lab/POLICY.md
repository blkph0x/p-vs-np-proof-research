# Predeclared optional recognition policy

This policy was selected before running the parent's unchanged 58 original
requests and 22 stress requests. No expected answer or family metadata is read
by the adapter. Those original benchmarks must wait for the implementation and
its independent review to freeze. Small correctness fixtures do not tune this
policy.

An optional whole-sum recognition attempt is made only after the mandatory
greedy compressor succeeds, and only when its output has 2 through 16 nonzero
pieces, the retained boundary has at most 12 coordinates, and the original
coordinate bound `n` is at most 256. Every policy check costs one bookkeeping
work unit, including skipped attempts. The original fixed balanced/component
factor planning remains unchanged.

Each attempt has these caps: 50,000 work units, 64 norm queries, 2,048 pair
contractions, 128 point evaluations, and 2,048 certificate products. The fast
wrapper's probe stage has at most 64 samples, 16 cube tests, and 20,000 probe
work units within that same 50,000 total. Representation caps are 256 original
coordinate positions, 16 input pieces, 4,096 support rows, 8,192 phase terms,
and 4,096 rational coefficient bits.

Across the entire DAG, recognition is limited to 1,024 attempts, 1,000,000 work
units, 4,096 norm queries, 65,536 pair contractions, 8,192 point evaluations,
and 65,536 certificate products. All consumed recognition work also contributes
to the unchanged overall DAG work cap of 3,000,000. Probe and fallback counters
are separately accumulated; they do not disappear when an attempt fails.
Each call receives the smaller of its local allowance and the remaining
aggregate/global allowance. A counter's attempted operation may cross its
limit by the primitive's documented rejection unit; that consumption is still
recorded, and exceeding an aggregate/global limit returns UNKNOWN.

An EXACT one-piece or zero result replaces the derived greedy output. A proved
UNSUPPORTED result retains that valid output. A local UNKNOWN also retains it,
after charging its actual consumed producer work. Mandatory greedy failure is
never bypassed; this integration cannot rescue an overflow that occurs before
greedy output exists. The optional stage does not search proper subgroups.

Verification derives recognizer inputs from freshly verified marginals and
greedy outputs. It never accepts a supplied replacement operand list or charges
producer statistics as if they were checker work. Accepted replacements and
claimed negative certificates are replayed under the external configuration;
insufficient replay resources return UNKNOWN. A producer UNKNOWN is an identity
event with no semantic replacement, checked by retaining the derived list. It
does not certify historical discovery effort or the truth of a claimed resource
exhaustion. Its producer counters are ignored by the checker, while the actual
producer run and source hashes retain the measured work record.

The old greedy input, retained, pending, and proof counters remain separate from
the post-recognition output count. A new accepted message can temporarily
coexist with all greedy input pieces; that input-plus-output piece count is
reported. These are representation counts, not a complete resident-memory
measurement. No general runtime or polynomial SAT bound is claimed.
