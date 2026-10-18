import json
from pathlib import Path

from fourier_boundary import (analytic_summary, brute_force_spectrum,
                              cyclic_analytic_summary,
                              cyclic_brute_force_spectrum,
                              cyclic_target_span_summary,
                              cyclic_modular_spectrum, cyclic_unique_3cnf,
                              forced_3cnf)


ROOT = Path(__file__).resolve().parent


def main():
    rows = [analytic_summary(n) for n in range(0, 13)]
    brute_rows = []
    for n in range(0, 5):
        variables, _ = forced_3cnf(n)
        spectrum = brute_force_spectrum(n)
        support = sum(value != 0 for value in spectrum)
        expected = 1 << n
        assert support == expected
        brute_rows.append({"n": n, "variables": variables,
                           "brute_force_support": support,
                           "expected_support": expected})
    cyclic_analytic_rows = [cyclic_analytic_summary(n) for n in range(3, 15)]
    cyclic_brute_rows = []
    for n in range(3, 9):
        variables, clauses = cyclic_unique_3cnf(n)
        spectrum = cyclic_brute_force_spectrum(n)
        support = sum(value != 0 for value in spectrum)
        expected = 1 << n
        assert len(clauses) == 4 * n
        assert support == expected
        assert all(len(clause) == 3 and len({abs(x) for x in clause}) == 3
                   for clause in clauses)
        cyclic_brute_rows.append({"n": n, "variables": variables,
                                  "brute_force_support": support,
                                  "expected_support": expected})
    cyclic_modular_rows = []
    for prime in (3, 5, 7):
        for n in range(3, 9):
            spectrum = cyclic_modular_spectrum(n, prime)
            support = sum(value != 0 for value in spectrum)
            expected = 1 << n
            assert support == expected
            cyclic_modular_rows.append({"n": n, "prime": prime,
                                        "modular_support": support,
                                        "expected_support": expected})
    cyclic_target_span_rows = [cyclic_target_span_summary(n) for n in range(3, 9)]
    payload = {
        "all_checks_passed": True,
        "scope": "explicit Fourier/Walsh support barrier; not a lower bound for arbitrary SAT algorithms",
        "analytic_rows": rows,
        "brute_force_rows": brute_rows,
        "family": "private-helper forcing family and cyclic unique-model family",
        "cyclic_analytic_rows": cyclic_analytic_rows,
        "cyclic_brute_force_rows": cyclic_brute_rows,
        "cyclic_modular_rows": cyclic_modular_rows,
        "cyclic_target_span_rows": cyclic_target_span_rows,
    }
    (ROOT / "RESULTS.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
