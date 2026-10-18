# Certified graph-lift experiments

All 49 requests completed EXACT, passed independent certificate replay against their original matrices and objectives, and agreed with an independent optimum. The examples use supplied graph-plus-label representations. They do not establish universal coverage, a new complexity theorem, or P=NP.

## Primary and larger supplied representations

The first two cases are the 13-column one-row lift and the 15-column projective matrix PG(3,2), represented with two label rows. Every original word was enumerated for these cases (8,192 and 32,768 words). The separate proof that PG(3,2) has no one-row lift is in COVERAGE_AUDIT.md; these experiments do not implement or claim an automatic representation recognizer.

Complete-graph cases use one or two seeded random label bits on each distinct graph edge, unit weights, target zero and a nonzero-word requirement. K4 cases enumerate all 64 original words. For the larger cases, distinct nonzero check columns rule out weights one and two, and an explicit zero-label triangle proves an upper bound of three. These two facts give an independent exact optimum without enumerating all codewords. The JSON preserves each triangle.

| Case | Coordinates | Graph rows | Label rows | Optimum | Join cases | Solve wall (s) | Replay (s) |
|:---|---:|---:|---:|---:|---:|---:|---:|
| thirteen_point_one_row_lift | 13 | 3 | 1 | 3 | 13 | 0.021115 | 0.005029 |
| PG_3_2_two_row_lift | 15 | 2 | 2 | 3 | 15 | 0.030112 | 0.007448 |
| complete_graph_K4_labels1 | 6 | 3 | 1 | 3 | 6 | 0.006115 | 0.001540 |
| complete_graph_K4_labels2 | 6 | 3 | 2 | 3 | 6 | 0.009097 | 0.002195 |
| complete_graph_K6_labels1 | 15 | 5 | 1 | 3 | 15 | 0.035809 | 0.008981 |
| complete_graph_K6_labels2 | 15 | 5 | 2 | 3 | 15 | 0.059340 | 0.015217 |
| complete_graph_K8_labels1 | 28 | 7 | 1 | 3 | 28 | 0.130566 | 0.033621 |
| complete_graph_K8_labels2 | 28 | 7 | 2 | 3 | 28 | 0.225115 | 0.056969 |
| complete_graph_K10_labels2 | 45 | 9 | 2 | 3 | 45 | 0.641468 | 0.166162 |

The largest case has 45 coordinates (K10) and two label rows. Its 45 edge-pinned residual cases all have zero or two terminals. No 2^45 full-word enumeration was performed. The solver's certificate proves every pin optimum; the triangle argument independently proves the aggregate minimum of three.

## Exhaustive original-coordinate controls

Thirty seeded small cases have 4–12 coordinates, 1–4 graph rows and 0–3 label rows. The original rows are scrambled by a generated invertible matrix, and the inverse is supplied to the solver. Targets include zero, targets known to be feasible, and arbitrary row syndromes. The nonzero condition is varied. Half use unit weights and half use independently generated integer weights from zero through five. Every one of the 2^n original words is checked by an independent exhaustive oracle.

Ten further cases start from supplied sparse-U products H=B+UV. They include zero and dependent U columns, components containing ground, and components requiring sums of multiple original rows. The normalizer and its independent verifier run first. The code solver then receives the original H, original target and the certified row transform. Each answer is compared with exhaustive enumeration on the original coordinates.

| Group | Cases | Infeasible requests | Zero-cost optima | Original words enumerated |
|:---|---:|---:|---:|---:|
| named_row_form | 2 | 0 | 0 | 40960 |
| seeded_small_row_form | 30 | 3 | 9 | 24640 |
| sparse_U_normalized | 10 | 1 | 2 | 8192 |
| seeded_complete_graph_labels | 7 | 0 | 0 | 128 |

An EXACT result with a null optimum means that the specified request is infeasible; it is not an unknown answer. Zero-weight nonempty answers are legitimate when zero-cost coordinates are present. The original nonzero requirement is verified independently of objective value.

## Evidence, limits and reproduction

Run `python run_lift_experiments.py` in this directory. `RESULTS.json` stores the original request, its compact-JSON SHA256 hash, original columns, supplied row transformation, full solver certificate, independent replay result, reference optimum and timings for every case. The ten normalization cases also store B,U,V and the full normalization evidence. Certificates are serialized and parsed back before another complete replay; all 49 code certificates and ten normalization certificates passed.

The four production modules and this runner are hashed before and after the experiment. Publication fails if a source changed during the run. Hashes of Python files use exact bytes; request hashes use sorted-key, compact UTF-8 JSON. The result JSON is compact to avoid duplicating formatting space around nested certificate arrays.

Caps per residual solve: 4,096 product states; 1,000,000 total table states; 1,000,000 search relaxations; 65,536 terminal-DP states; 1,000,000 DP transitions; and 10,000,000 verification arcs. The nonempty adapter permits at most 64 pinned cases. Normalization and its verifier each have a separate 1,000,000-work-unit cap. Every experiment completed within these caps. Work budgets are not wall-time limits.

Seed: 2026101807. Python: 3.10.10. Start: 2026-10-17T14:07:58.368211+00:00. Experiment time before final output serialization: 2.152869 seconds. Each timing is a single local measurement with possible concurrent work. Solve-wall measurements include the producer's internal checks; replay is an additional independent verification. These are not comparative benchmarks and imply no measured speedup over enumeration.

## Scope

Homogeneous nonzero optimization on a supplied p-row graphic lift has the deterministic 2^{O(p)} polynomial-size graph algorithm proved in COVERAGE_AUDIT.md. Arbitrary affine targets may have many graph terminals; the implemented general-terminal subset DP is exponential in that count. The small affine tests validate behavior, not unrestricted polynomial running time. The normalizer converts a supplied sparse perturbation; it does not find such a representation for an arbitrary matrix. The coverage obstructions and missing general reduction remain unchanged.
