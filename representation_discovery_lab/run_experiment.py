"""Generate the bounded hidden-affine representation experiment."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

from engine import project, records, reorder_gadget_blocks, rename_variables, xor_chain
from gaussian_baseline import recover_xor_relation
from nonlinear_control import classify

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    """Hash UTF-8 source text after CRLF/lone-CR to LF normalization only."""
    source = path.read_bytes().decode('utf-8')
    canonical = source.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def main() -> None:
    source_names = ['engine.py', 'run_experiment.py', 'gaussian_baseline.py',
                    'nonlinear_control.py', 'independent_review.py', 'test_engine.py',
                    'test_baseline.py', 'test_nonlinear_control.py', 'test_independent_review.py', 'REPORT.md']
    before = {name: sha256(HERE / name) for name in source_names}
    def original_input(chain):
        return {key: [list(c) for c in chain[key]] if key == 'clauses' else list(chain[key])
                for key in ('clauses', 'shared', 'local')}
    rows = []
    for row in records():
        chain = xor_chain(row.shared_count, row.permutation)
        baseline = recover_xor_relation(tuple(chain["clauses"]), tuple(chain["shared"]))
        rows.append({
            "original_input": original_input(chain),
            "shared_count": row.shared_count,
            "permutation": list(row.permutation),
            "clause_count": row.clause_count,
            "local_count": row.local_count,
            "encoded_representation_bits": row.encoded_representation_bits,
            "enumeration_discovery_work": row.enumeration_discovery_work,
            "exhaustive_replay_work": row.exhaustive_replay_work,
            "projected_bits": list(row.projected_bits),
            "linear_algebra_baseline": {
                "status": baseline.status,
                "support": list(baseline.support),
                "rhs": baseline.rhs,
                "work": baseline.work,
                "gadget_count": baseline.gadget_count,
            },
        })
    control_chain = xor_chain(5)
    renamed = rename_variables(control_chain,
                               {index: 8 - index for index in range(9)})
    controls = {
        "reordered_gadgets": reorder_gadget_blocks(control_chain),
        "duplicated_gadget": reorder_gadget_blocks(control_chain, duplicate_block=0),
        "renamed_all_variables": renamed,
        "positive_unit": {**control_chain, "clauses": control_chain['clauses'][:-1]
                          + ((-control_chain['clauses'][-1][0],),)},
        "added_binary_clause": {**control_chain, "clauses": control_chain['clauses'] + ((1, 2),)},
        "added_empty_clause": {**control_chain, "clauses": control_chain['clauses'] + ((),)},
        "duplicate_unit_and_tautology": {**control_chain, "clauses": control_chain['clauses']
                                         + (control_chain['clauses'][-1], (1, -1, 2))},
    }
    control_rows = {}
    for name, chain in controls.items():
        baseline = recover_xor_relation(tuple(chain["clauses"]), tuple(chain["shared"]))
        control_rows[name] = {
            "original_input": original_input(chain),
            "projected_bits": list(project(chain['clauses'], chain['shared'], chain['local'])),
            "clause_count": len(chain["clauses"]),
            "shared": list(chain["shared"]),
            "status": baseline.status,
            "support": list(baseline.support),
            "rhs": baseline.rhs,
            "work": baseline.work,
            "gadget_count": baseline.gadget_count,
        }
    nonlinear = classify()
    nonbaseline = recover_xor_relation(nonlinear['clauses'], (0, 1, 2))
    nonlinear['linear_algebra_baseline'] = {
        "status": nonbaseline.status, "support": list(nonbaseline.support), "rhs": nonbaseline.rhs,
        "work": nonbaseline.work, "gadget_count": nonbaseline.gadget_count}
    payload = {
        "schema": "representation_discovery_hidden_xor_v1",
        "status": "EXACT_BOUNDED_EXPERIMENT",
        "model": {
            "representation": "one even-parity XOR equation on the shared variables",
            "encoding": "existential XOR chain in 3-CNF with one helper per prefix",
            "discovery": "exact short-circuit projection plus symbolic full-schedule candidate and replay charges",
            "verification": "independent exhaustive projection replay",
            "representation_size_note": "encoded_representation_bits is the size of this label encoding, not a minimum over representations",
            "discovery_cost_note": "The work formulas charge a declared full, non-short-circuit schedule; candidate search is calculated symbolically, not executed. They do not measure actual Python work or lower-bound other algorithms.",
            "baseline_work_note": "Counts raw/shared/literal/unique-literal visits, normalized clause/support visits, all eight local truth-check visits, all elimination passes/equation/variable visits (including failures), substitutions, expression setup and output scans. Sorting, hashing, allocation and integer bit costs are excluded.",
            "shared_range": [3, 7],
            "operation_formulas": {
                "local_count": "m - 1",
                "clause_count": "4m - 3",
                "encoded_representation_bits": "9 + m*ceil(log2(m))",
                "exhaustive_replay_work": "(4m - 3)*2^(2m - 1)",
                "candidate_search_work": "(2^(m + 1) - 1)*2^m",
                "enumeration_discovery_work": "(4m - 3)*2^(2m - 1) + (2^(m + 1) - 1)*2^m",
            },
        },
        "source_sha256": before,
        "source_hash_scheme": "sha256-utf8-lf-v1",
        "source_unchanged_during_run": True,
        "records": rows,
        "controls": control_rows,
        "nonlinear_control": nonlinear,
        "interpretation": (
            "The projected representation remains one XOR equation while the bounded "
            "projection-based enumeration work grows with the hidden helper variables. "
            "A separate GF(2) baseline recovers the same relation without projection, "
            "so the enumeration cost is algorithm-specific evidence rather than an "
            "intrinsic discovery lower bound."
        ),
    }
    if before != {name: sha256(HERE / name) for name in source_names}:
        raise RuntimeError('source changed during experiment')
    (HERE / "RESULTS.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(rows), "status": payload["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
