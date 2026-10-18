# Independent review verdict

No correctness defect was found in the frozen compressor, its source-bound
checker, or the new compressed DAG adapter. All 15 independently authored tests
pass. This is a mathematical/source audit with bounded executable evidence,
not a claim of a machine-checked formal proof or a general SAT algorithm bound.

Reviewed principal SHA-256 hashes:

- `affine_sum_compression_lab/compression.py`:
  `4105542d6c7317bf0ba8ca63d4c34fc5acab249d9ff38704201bdef3e8617dff`
- `compressed_affine_dag_lab/dag.py`:
  `9ed5f226b5f31fe6a78b229e568a9935582899940a7877b2ee687a5d73f47898`
- `affine_boundary_lab/boundary.py`:
  `19a51e88ca8e88d419c04d9ddd7f5f7ec04afaaabe94da00de4ab49250d2fcb7`
- Independent `affine_boundary_reference/reference.py`:
  `60b62bfd936c7b9a399630754df6fdddaf6ee370135bd9a4e4bf6144f04f7a15`
- `affine_sum_capacity_lab/capacity.py`:
  `43c09044fa7535dd310c12ca00c9901146838bf4169d0db7211699c7f2abd8aa`

The complete source, theorem, test, experiment and saved-result hash map is in
RESULTS.json. Source hashes matched before and after the replay. No production
or prior frozen file was edited by this review.

## Exact evidence

| Audit | Result |
|---|---:|
| New original compact sums | 200; 3,585 direct assignments |
| New original mixed-factor requests | 200; 3,652 direct assignments |
| Intermediate original-factor boundary values | 3,156 |
| New DAG rewrite squared-norm checks | 98; 585 closed block products |
| Compression semantic/source mutations | 92 rejected |
| Adapter source/ownership/product mutations | 9 rejected |
| Named identity/counteridentity controls | 12 at each of widths 3, 128, 512 |
| Saved compressor replay | 102 EXACT; 7 UNKNOWN claims remain null |
| Saved compressor direct assignments | 1,847 |
| Saved compressor wide whole-sum norms | 6 |
| Saved compressor rewrite norms | 46; 270 closed block products |
| Saved adapter replay | 19 EXACT; 3 UNKNOWN claims remain null |
| Saved adapter independent block marginals | 836 |
| Saved adapter rewrite norms | 516; 3,096 closed block products |
| Capacity product/sum checks | n=0 through 64 |

Original inputs, seeds, producer results, certificate-checker outputs, explicit
nonconfluence schedules, and norm proofs for the named/wide controls are saved.
Saved production proof replays are bound by the exact RESULTS.json file hash
and case index. The replay code reconstructs every extra audit; evidence does
not depend on an unstored terminal transcript.

The independent norm verifier checks the completed rational sum of squares,
not nonnegativity of its individual signed pair contributions. Positive norms
are useful negative controls. Every pair is externally derived and covered,
and consumed IDs/source arrivals are checked separately by the production
certificate checker. Malformed certificates, omitted inputs, reused consumed
IDs, false support identities, coefficient changes and tight resource caps are
covered. An equivalent noncanonical closed constant-phase output is read with
its sign, avoiding a scalar-only interpretation.

## Confirmed planning limitation

Greedy pairwise reduction is order-sensitive. The same eight singleton pins
reduce to four mutually nonparallel lines in order [0,1,4,6,3,7,2,5], and to one
constant piece in natural order. Both actual production certificates verify;
independent explicit schedules establish each equality. The four-line endpoint
admits none of the implemented pair rules, but the good schedule already shows
that this is not a representation lower bound for the function.

The adapter correctly charges all generated child products before compression,
binds the complete ordered input stream, and preserves original factor ownership
and free-variable multiplicity. Its cumulative checker limits do not trust
producer statistics. A retained-piece bound still excludes materialized input
lists, marginal caches, proof storage and transient pending objects. Replaying
failed-pair no-ops does not prove maximal compression or authenticate unrecorded
producer effort; it preserves the represented function.

The separate capacity theorem is also sound, with its essential arbitrary-truth-
function scope intact. See CAPACITY_REVIEW.md. Neither that count nor the greedy
example proves a lower bound for polynomial-size original CNFs, every possible
decomposition, another representation language, or P versus NP.

Reproduce from this folder with `python -m unittest discover -v` followed by
`python run_review.py`. The latter writes only this review's RESULTS.json.
