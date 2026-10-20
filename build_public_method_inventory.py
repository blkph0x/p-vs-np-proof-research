"""Map every repository Python module to a public-method comparison area.

This is an inventory, not a line-by-line correctness or novelty audit. The
callable names are parsed, not executed. --check detects unclassified additions
and stale inventory metadata without regenerating accepted evidence.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "PUBLIC_METHOD_INVENTORY.json"

GROUP_DIRS = {
    "sat-search": "proof_producing_cdcl_lab horn_cdclt_lab proof_portfolio_integration_lab proof_motif_candidate_lab",
    "proof-complexity": "resolution_width_lab proof_complexity_frontier_lab proof_complexity_scaling_lab tseitin_expander_lab",
    "frontier-planning": "typed_merge_planner_lab charged_work_core_lab high_width_core_stress_lab circuit_boundary_lab circuit_order_hardness_lab graph_order_hardness_lab linear_frontier_order_lab mixed_information_frontier_lab primal_order_sat_lab semantic_frontier_expander_lab variable_boundary_sat_lab bounded_language_invention_lab",
    "affine-algebra": "affine_boundary_lab affine_boundary_reference affine_character_factor_lab affine_compression_review affine_compression_stress_lab affine_fast_recognition_lab affine_gram_conditioning_lab affine_grouping_plan_lab affine_one_piece_lab affine_partition_compression_lab affine_positive_cover_limits_lab affine_sum_capacity_lab affine_sum_compression_lab connected_affine_cover_lab row_basis_exact_oracle_lab weighted_boundary_lab",
    "hidden-affine": "representation_discovery_lab affine_projection_recognition_lab",
    "knowledge-compilation": "compressed_affine_dag_lab globally_compressed_affine_dag_lab weighted_affine_dag_lab",
    "matching-decoding": "degree_two_min_distance_lab labelled_join_certified labelled_join_next matching_composition_controls matching_gadget_limits multiobjective_matching_limits non_graphic_core_lab objective_pullback_limits packed_cost_exact_matching gadget_limits projection_limits saturated_clause_limits",
    "counting-coefficients": "coefficient_isolation_lab coefficient_residue_lab coefficient_structure_lab interval_coefficient_lab original_count_reference_lab threshold_composition_lab",
    "fourier-transforms": "fourier_spectrum_boundary_lab",
    "holographic-tensors": "crossing_sign_lab holographic_tractability_lab simultaneous_basis_lab tensor_basis_lab",
    "code-relaxations": "local_marginal_code_lab",
}
DIR_GROUP = {directory: group for group, names in GROUP_DIRS.items() for directory in names.split()}
ROOT_NAMES = {
    "sat-search": "proof_portfolio_bridge indirect_ite indirect_xor sequential_counter xor_closure",
    "frontier-planning": "adaptive_fragment_synthesis structural_probe complete_graph_frontier semantic_frontier_expander",
    "affine-algebra": "affine_recognition_limits affine_one_piece_recognition_review affine_recognition_limits_review affine_sum_compression_review rank_native_solver row_basis_discovery row_basis_escape",
    "knowledge-compilation": "certified_residual_quotient macro_assisted_subdag projection_discovery_barrier repeated_subdag_templates residual_equivalence_barrier symbolic_suffix_template symbolic_unit_template",
    "matching-decoding": "native_coset_solver matching_certificate degree_three_barrier degree_three_reduction_review projection_barrier degree_two_min_distance",
    "counting-coefficients": "coefficient_complexity_barrier coefficient_complexity_review counting_vs_decision_audit counting_vs_decision_review randomized_isolation randomized_isolation_review",
    "fourier-transforms": "fourier_spectrum_boundary fwht_cost_audit",
    "code-relaxations": "all_dual_lp_barrier regular_ldpc_33_local_audit regular_ldpc_local_audit regular_ldpc_size_bounds regular_ldpc_audit quadratic_code_family",
    "engineering-evidence": "build_public_source_index build_repository_manifest build_public_method_inventory refresh_working_manifest save_vohra_metadata",
}
ROOT_GROUP = {name: group for group, names in ROOT_NAMES.items() for name in names.split()}


def group_for(relative: str) -> str:
    parts = relative.split("/")
    if len(parts) > 1:
        if parts[0] not in DIR_GROUP:
            raise ValueError(f"Unclassified source directory: {parts[0]}")
        # The same lab contains two distinct comparison tasks.
        if parts[0] == "local_marginal_code_lab" and "sos" in parts[-1].lower():
            return "polynomial-cuts"
        return DIR_GROUP[parts[0]]
    stem = Path(relative).stem.lower()
    if stem.startswith("run_") or stem.startswith("verify_") and stem.endswith("_artifacts"):
        return "engineering-evidence"
    for prefix in ("test_", "verify_"):
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
    stem = stem.removesuffix("_integration")
    if stem not in ROOT_GROUP:
        raise ValueError(f"Unclassified root module: {relative}")
    return ROOT_GROUP[stem]


def build() -> dict:
    paths = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                           cwd=ROOT, check=True, capture_output=True).stdout.decode("utf-8").split("\0")
    records = []
    for relative in sorted({p for p in paths if p.endswith(".py")}):
        source = (ROOT / relative).read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=relative)
        callables = []
        def walk(node, prefix=""):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = prefix + child.name
                    callables.append({"name": name, "line": child.lineno,
                                      "kind": "class" if isinstance(child, ast.ClassDef) else "function"})
                    walk(child, name + ".")
                else:
                    walk(child, prefix)
        walk(tree)
        records.append({"path": relative, "comparison_area": group_for(relative),
                        "normalized_source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                        "callables": callables,
                        "assert_statement_count": sum(isinstance(n, ast.Assert) for n in ast.walk(tree))})
    return {"schema": 1, "review": "PUBLIC_METHOD_REVIEW.md", "review_date": "2026-10-20",
            "scope": "All repository Python files mapped by capability; selected code paths inspected. Callable listing is not an individual semantic audit.",
            "hash_convention": "UTF-8 without BOM; universal newlines normalized to LF",
            "python_files": len(records),
            "research_directories": sorted({p["path"].split("/")[0] for p in records if "/" in p["path"]}),
            "callable_definitions": sum(len(p["callables"]) for p in records),
            "non_python_components": [".github/workflows/research-checks.yml", ".github/workflows/pages.yml",
                                      "requirements.txt", "index.md", "_includes/runtime-chart.html",
                                      "assets/js/scaling-chart.js", "assets/data/scaling-runtime.json",
                                      "high_width_core_stress_lab/rank_audit.cpp",
                                      "non_graphic_core_lab/matroid_audit.cpp",
                                      "row_basis_exact_oracle_lab/rank5_exact.cpp"],
            "files": records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build()
    if args.check:
        if json.loads(OUT.read_text(encoding="utf-8")) != payload:
            raise ValueError("Public-method inventory is stale; review changed modules, then regenerate")
    else:
        OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Mapped {payload['python_files']} Python files in {len(payload['research_directories'])} research directories; {payload['callable_definitions']} parsed callable definitions")


if __name__ == "__main__":
    main()
