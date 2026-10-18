"""Save exact certificates and bounded corroboration, with source hashes."""

from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

import basis


ROOT = Path(__file__).resolve().parent
SOURCES = ("basis.py", "test_basis.py", "run_experiments.py", "THEOREM.md")


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def json_value(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    return value


def groebner_corroboration(systems):
    # Discovery/corroboration only: the actual certificate verifier does not
    # import SymPy, and the proof uses the direct classification in THEOREM.md.
    import sympy
    variables = sympy.symbols("a b c d u")
    results = []
    for system in systems:
        equations = []
        for terms in system["equations"]:
            equations.append(sum(term["coefficient"] * sympy.prod(
                variable ** exponent for variable, exponent in zip(variables, term["powers"]))
                for term in terms))
        start = time.perf_counter()
        basis_ = sympy.groebner(equations, variables[-1], *variables[:-1], order="grevlex")
        unit = len(basis_.polys) == 1 and basis_.polys[0].as_expr() == 1
        if not unit:
            raise AssertionError("disagrees with exact obstruction proof")
        results.append({"gate": system["gate"], "eq_support_parity": system["eq_support_parity"],
                        "clause_support_parity": system["clause_support_parity"],
                        "basis": [str(p.as_expr()) for p in basis_.polys],
                        "unit_ideal": unit, "elapsed_seconds": time.perf_counter() - start})
    return {"sympy_version": sympy.__version__, "variable_order": ["u", "a", "b", "c", "d"],
            "monomial_order": "grevlex", "proof_role": "corroboration only", "branches": results}


def main():
    before = hashes()
    started = time.perf_counter()
    certificate = basis.obstruction_certificate()
    assert basis.verify_obstruction(certificate)
    edge_certificate = basis.edge_specific_or3_certificate()
    assert basis.verify_edge_specific_or3_certificate(edge_certificate)
    edge_slack_certificate = basis.edge_specific_slack_certificate()
    assert basis.verify_edge_specific_slack_certificate(edge_slack_certificate)
    edge_global_certificate = basis.edge_specific_global_certificate("OR3")
    edge_global_slack_certificate = basis.edge_specific_global_certificate("SLACK3")
    product_certificate = basis.product_type_obstruction_certificate()
    assert basis.verify_product_type_obstruction(product_certificate)
    assert basis.verify_edge_specific_global_certificate(edge_global_certificate)
    assert basis.verify_edge_specific_global_certificate(edge_global_slack_certificate)
    controls = basis.positive_controls()
    discovery = groebner_corroboration(certificate["equation_systems"])
    clause_classification = {
        name: basis.common_eq3_parity_branches(signature)
        for name, signature in (("EQ3", basis.EQ3), ("NAE3", basis.NAE3),
                                ("OR3", basis.OR3), ("SLACK3", basis.SLACK3))
    }
    after = hashes()
    if before != after:
        raise RuntimeError("sources changed during experiment")
    result = {
        "format": "simultaneous-basis-experiment-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "request": "Investigate one common invertible complex 2x2 basis for row EQ3 and column OR3, and separately row EQ3 and column slack [0,1,2,1], under opposite tensor actions; prove or certify all four parity branches for each pair. Include genuine positive controls and avoid a general complexity claim.",
        "scope": "Same invertible 2x2 matrix on every port; complex numbers; necessary planar matchgate parity. Does not resolve P versus NP.",
        "status": "Both gate pairs are impossible in the stated model, by direct classification and integer Bezout identities.",
        "source_hashes_before": before, "source_hashes_after": after,
        "certificate": certificate, "certificate_replayed": True,
        "edge_specific_certificate": edge_certificate,
        "edge_specific_certificate_replayed": True,
        "edge_specific_slack_certificate": edge_slack_certificate,
        "edge_specific_slack_certificate_replayed": True,
        "edge_specific_global_certificate": edge_global_certificate,
        "edge_specific_global_slack_certificate": edge_global_slack_certificate,
        "edge_specific_global_certificates_replayed": True,
        "product_type_certificate": product_certificate,
        "product_type_certificate_replayed": True,
        "groebner_corroboration": discovery,
        "symmetric_clause_classification": clause_classification,
        "positive_controls": controls,
        "counts": {"excluded_gate_pairs": 2, "parity_branches": 8, "bezout_identities": 4,
                   "planar_graph_realizations": len(controls), "graph_boundary_entries_replayed": 8 * len(controls),
                   "symmetric_clause_signatures_classified": 4,
                   "symmetric_clause_families": 4,
                   "edge_specific_parity_branches": 4,
                   "edge_specific_surviving_support_triples": 2,
                   "edge_specific_clause_pairs_excluded": 2,
                   "edge_specific_flip_cases_checked_per_clause": 16,
                   "product_type_common_basis_obstructions": 1},
        "elapsed_seconds": time.perf_counter() - started,
    }
    encoded = json_value(result)
    (ROOT / "RESULTS.json").write_text(json.dumps(encoded, indent=2) + "\n", encoding="utf-8")
    # Reload the exact saved artifact and replay both certificate and graph tables.
    saved = json.loads((ROOT / "RESULTS.json").read_text(encoding="utf-8"))
    assert basis.verify_obstruction(saved["certificate"])
    assert basis.verify_product_type_obstruction(saved["product_type_certificate"])
    for control in saved["positive_controls"]:
        graph = control["graph"]
        replay = basis.matching_signature(graph)
        matrix = [[Fraction(v) for v in row] for row in control["basis"]]
        transformed = basis.transform(control["signature"], matrix if control["orientation"] == "row"
                                      else basis.inverse2(matrix), control["orientation"])
        assert replay == transformed == [Fraction(v) for v in control["transformed"]]
    lines = ["# Simultaneous basis results", "",
             "Two exact parity obstructions over the complex numbers exclude a common invertible 2 by 2 basis for EQ3 with OR3, and for EQ3 with the slack factor [0,1,2,1], in the stated row/column convention. A separate product-type certificate excludes the other main symmetric Holant target: requiring transformed EQ3 to have product-type support forces a diagonal or anti-diagonal basis, under which both OR3 and SLACK3 still have three nonzero weight classes. The edge-specific certificate extends the obstruction to every degree-three equality/OR3 or equality/slack incidence network. This is a limitation of this basis route; P versus NP remains unresolved.", "",
             "The saved certificate contains all eight five-equation parity systems, four integer Bezout identities, the rational symmetric-clause classification, the edge-specific EQ3/OR3 and EQ3/slack ±4 certificates, and the product-type case split. All eight per-edge flip patterns are replayed for both clauses. A standard-library verifier replays the identities and binds them to the original tensors. The accompanying direct proof classifies every admissible EQ3 basis and every rational symmetric ternary clause compatible with its parity; the program is not a formal proof assistant.", "",
             "SymPy " + discovery["sympy_version"] + " independently returned the unit ideal for all eight systems. Those computations are corroboration, not the certificate of nonexistence.", "",
             "Five explicit planar weighted graphs replay all 40 boundary entries. They verify shared Hadamard-basis EQ3/EQ3 and EQ3/NAE3 controls and individual OR3/slack3 transformations. Individual success does not supply a shared basis with EQ3.", "",
             "All before/after source hashes agree; full inputs, exact fractions, polynomial terms, graph edges and timings are in RESULTS.json. The runner reloaded the saved JSON and replayed its proof identities and graph/tensor controls.", "",
             "Run `python -m unittest -v test_basis.py` and `python run_experiments.py` from this directory. Tests include 200 seeded rational matrices checked by independent direct tensor summation, mutation rejection, all branch equations and the explicit graph signatures. No finite sample is used to infer nonexistence.", "",
             "## Source hashes", ""]
    lines.extend("- `" + name + "`: `" + digest + "`" for name, digest in before.items())
    (ROOT / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"counts": result["counts"], "source_hashes_agree": before == after,
                      "elapsed_seconds": result["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
