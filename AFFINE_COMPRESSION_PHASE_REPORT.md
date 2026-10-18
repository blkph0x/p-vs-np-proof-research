# Certified affine-sum compression and its measured limits

**P versus NP remains unresolved.** This phase implements exact rules for
compressing sums of affine-supported quadratic signs. The same 58 original
counting requests still produce 54 checked exact answers and four UNKNOWNs.
An additional 22-request stress set gives 11 checked answers versus the earlier
method's two, with all failures preserved. These results identify useful local
algebra and a concrete ordering problem; they do not establish a general
polynomial solver or a lower bound against all algorithms.

## What changed

A piece has the form c*1[A*x=b]*(-1)^q(x), with rational c and quadratic q
over GF(2). The frozen earlier marginalizer sums internal coordinates of one
piece in polynomial time in its explicit dimensions and coefficient lengths.
The new compressor adds three identities beyond identical-piece addition:

1. On equal supports, compatible opposite phases impose one affine equation.
2. Equal-magnitude compatible pieces on parallel cosets join into one piece
   on their affine union, with a checked quadratic selector phase.
3. Subtracting a compatible codimension-one affine subset leaves the opposite
   half of the larger affine support.

Every rewrite consumes two live pieces, creates a fresh piece, and binds the
ordered original input stream. A separately structured checker verifies the
support and phase identities and replays normalization evidence. It rejects
missing inputs, changed coefficients, reused consumed pieces and forged outputs.

The separate compressed DAG adapter preserves every original clause occurrence,
all original variables and every child cross-product before compression. It
charges cumulative discovery and compression work across structural nodes.
Recorded limits return UNKNOWN without a partial count. Neither implementation
claims that the number of pieces, failed attempts or certificates stays small
on arbitrary inputs.

## Complete-original comparisons

The retained 58 requests use the same complete formulas, orders and recorded
limits as the preceding boundary phase. Some formulas occur more than once
because earlier controls had different provenance. They are 58 requests, not
58 claimed distinct formulas. All expected original counts have a separate
counting reference and an independent enumeration or structural calculation.

| Retained batch | Earlier weighted method | New compressed method |
|---|---:|---:|
| Earlier 58 original requests | 54 EXACT / 4 UNKNOWN | 54 EXACT / 4 UNKNOWN |
| Additional 22 original stress requests | 2 EXACT / 20 UNKNOWN | 11 EXACT / 11 UNKNOWN |

There are no lost exact answers in either recorded batch. The four original
failures remain the complete positive binary formula on 16 variables, planted
24-variable and 32-variable formulas, and the connected historical mixed
72-variable formula. Their stopping points can differ: the last now reaches
the retained-piece cap rather than the previous node cap. The exact planted
counts remain 64 and 680; knowing them does not turn the capped solver's
UNKNOWN into an answer.

For the 54 earlier requests solved by both methods, recorded work is lower
on 10 and higher on 44; none tie. Products are lower on 28, equal on 25 and
higher on one. Node counts are lower on 30, equal on 23 and higher on one.
The recorded `peak_terms` counter is lower on 23, equal on 30 and higher on
one, but the old transient dictionary peak and new settled retained-piece peak
have different meanings; this is not a like-for-like memory comparison. The
work counters record specified operations, not CPU instructions or elapsed-time
speedups. Compression's failed pair searches often outweigh its savings.

The stress inputs contain 16 parity CNFs and six pigeonhole CNFs. The parity
inputs encode all degree-three vertex equations of connected simple cubic
graphs with 8, 20, 40 and 80 vertices. Each has an even-charge and odd-charge
version, each stored in grouped and shuffled clause orders. Every equation
is expanded into its four original clauses; the solver receives ordinary CNF.
Independent source proofs reconstruct every clause and derive the incidence
rank V-1. The model count is 2^(E-V+1) for even total charge and zero for odd.
No graph expansion property or generic hardness claim is assumed.

All eight grouped parity inputs become exact under compression, including
120-variable, 320-clause inputs. All eight shuffled versions still reach
limits. The grouped and shuffled members have exactly the same clause
multisets. The ninth new answer is the four-pigeon/four-hole formula, with
24 models. Both methods already solve the three-pigeon/three-hole and
four-pigeon/three-hole controls. The three larger pigeonhole controls still
reach limits under the new method.

The pigeonhole encoding requires each pigeon to use at least one hole and
each hole to contain at most one pigeon. It does not silently add a row
at-most-one constraint. For equal counts of pigeons and holes, the two total
bounds force a bijection, giving h!; one extra pigeon makes the formula
unsatisfiable. A separate owner-of-each-hole enumeration confirms all six
expected counts. These family-specific calculations verify experiments;
they are not substituted into either general solver.

Exact counting must also be distinguished from the SAT decision objective.
A separate bounded probe produces direct original-assignment witnesses for
all three positive counting failures: the complete binary input and both
planted inputs. It supplies an original-clause unit contradiction for the
connected mixed input. Their witness searches visit 16, eight and 14 states,
respectively; the contradiction needs no branches. Every exported witness or
contradiction is directly checked against the original clauses. Thus these
four counting failures are already decided by short evidence. The probe's
search remains potentially exponential, counts literal visits rather than
all CPU work, and returns UNKNOWN on limits or when it lacks an exported
proof. See [decision evidence](COUNTING_VS_DECISION_AUDIT.json).

## Independent checks and counterexamples

All **54 tests** pass across the compressor (12), adapter (20), independent
review (15), capacity calculation (4), and original stress controls (3).
Sources remained unchanged during the aggregate run. Saved compressor controls
contain 102 EXACT and seven UNKNOWN requests; saved adapter controls contain
19 EXACT and three UNKNOWN requests.

The artifact audit passes all 106 recorded source references, representing
54 unique source files. It replays 300 exact certificates across the saved
compressor, new adapter, old/new original comparisons, original count
reference and old/new stress results. These are artifact replays, with some
inputs represented in more than one retained batch. All UNKNOWN outputs remain
claim-free; the original inputs and cap settings are compared explicitly.

The independent review checks 200 additional compact sums and 200 additional
mixed-factor inputs by direct original-assignment evaluation. It also checks
3,156 intermediate boundary values, rejects 92 compressor mutations and nine
adapter mutations, and replays all saved exact proofs. The saved adapter's
836 marginals are independently recomputed by the block reference, and its
516 rewrites pass independent squared-norm equality checks using 3,096 closed
block products. These checks supplement ordinary mathematical and code review;
they are not proof-assistant formalization or a novelty claim.

The norm method checks h=sum(inputs)-sum(outputs) by computing sum_x h(x)^2
exactly. Each pair product is another compact affine quadratic sum, so the
method avoids a full boundary truth table and costs quadratically many pair
contractions in the number of explicit pieces. A zero total proves pointwise
equality over real-valued functions. Individual signed pair contributions
need not be nonnegative; the completed square sum is what matters.

Greedy compression is provably order-sensitive on a small saved control.
The eight singleton pins on three bits reduce to one constant piece in natural
order. The order [0,1,4,6,3,7,2,5] leaves four disjoint affine lines, with
different directions, to which none of the pair rules applies. Both output
sums are the same constant function and both certificates verify. This
counterexample defeats completeness of the greedy rules; it is not a
representation lower bound for that function.

The independent stress review reconstructs all 22 inputs, rejects all 2,611
single-clause omissions, verifies all eight grouped/shuffled pairs, and
directly evaluates 23,382 assignment words across 18 smaller original formulas.

## A representation limit, with its scope intact

The number of nonzero real affine quadratic directions on n Boolean variables,
up to overall sign, is exactly

    D_n = 2^n * product_{i=0}^{n-1}(1+2^i).

An r-dimensional real linear subspace contains at most 2^r Boolean vectors:
projection onto r independent coordinate evaluations is injective. Counting
spans of at most K dictionary directions therefore shows that some arbitrary
Boolean truth functions need Omega(2^n/n^2) pieces, even with arbitrary real
coefficients. The all-size argument is separate from the numeric checks
through n=64 and exhaustive dictionary counts through n=4.

This does **not** exhibit a succinct hard family. An arbitrary truth table
already has 2^n input bits, and its corresponding CNF can be exponentially
large. The result is not a polynomial-size CNF lower bound, a bound on every
decomposition plan, or a proof of P!=NP. It prevents an unjustified claim that
this particular language compresses every Boolean function into polynomially
many pieces.

## Resource interpretation

The retained-piece cap applies between input arrivals. An arriving piece can
temporarily increase the live set by one; normalized outputs can also exist
as pending objects before consumed sources are released. Actual live and
live-plus-pending peaks are recorded separately. The cap does not describe
total memory: input lists, marginal caches and proof storage also occupy space.

Failed-pair certificate events are checked as valid no-ops on live IDs. Their
replay preserves the function but does not re-prove that no rewrite exists or
authenticate every unrecorded producer operation. Producer discovery counters
and fresh verifier costs are therefore kept distinct.

## Reproduction and next work

From this directory, run `python run_affine_compression_phase_checks.py` and
`python verify_affine_compression_artifacts.py`. The original comparisons are
reproduced by `python run_affine_compression_crosscheck.py` and
`python affine_compression_stress_lab/run_experiments.py`. Full original inputs,
certificates, limits, unsuccessful runs and source hashes are retained.

- [Test summary](AFFINE_COMPRESSION_TEST_SUMMARY.json).
- [Artifact replay](AFFINE_COMPRESSION_ARTIFACT_AUDIT.json).
- [Same 58 requests](AFFINE_COMPRESSION_CROSSCHECK.json).
- [Additional original stress results](affine_compression_stress_lab/RESULTS.json).
- [Independent review](affine_compression_review/REVIEW.md).
- [Capacity theorem](affine_sum_capacity_lab/THEOREM.md).

The next experiments address the observed failures directly: source-checked
clause grouping for shuffled parity blocks, and global recognition of equal-
magnitude disjoint affine partitions whose phases fit one quadratic function.
The second can address the four-line greedy trap without searching all pair
schedules. Both require separate original-input certificates and full discovery
cost accounting. Their benefit on the retained benchmarks is to be measured;
neither supplies a general polynomial representation or discovery theorem.
