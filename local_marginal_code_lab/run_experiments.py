import json
from pathlib import Path

from local_marginal import make_certificate, random_code_union_bound, verify_certificate


def even_parity_generator(n):
    return tuple((1 << i) | (1 << (n - 1)) for i in range(n - 1))


def golay_generator():
    polynomial = sum(1 << i for i in (0, 1, 5, 6, 7, 9, 11))
    return tuple((polynomial << i) | (1 << 23) for i in range(12))


def run_case(name, rows, n, pin, level, enumerate_scopes):
    made = make_certificate(rows, n, pin, level, enumerate_scopes=enumerate_scopes)
    if made["status"] != "FOUND":
        raise RuntimeError(made)
    checked = verify_certificate(made["certificate"])
    if not checked["valid"]:
        raise RuntimeError(checked)
    return {"name": name, "certificate": made["certificate"],
            "verification": checked}


def main():
    rows = [run_case("even_parity_n5_level3", even_parity_generator(5), 5, 0, 3, True),
            run_case("even_parity_n5_level4_boundary", even_parity_generator(5), 5, 0, 4, True),
            run_case("golay_level6", golay_generator(), 24, 0, 6, False)]
    output = {
        "format": "local-pinned-marginal-v1",
        "rows": rows,
        "all_valid": all(row["verification"]["valid"] for row in rows),
        "golay_level_bound_verified": rows[2]["verification"]["theorem_level_valid"],
        "golay_support_replay_deferred": rows[2]["certificate"]["enumerated_support"] is None,
        "scope": "exact local projection-marginal relaxation; no claim about a named hierarchy",
        "random_code_bounds": [random_code_union_bound(n) for n in (32, 64, 128, 256, 512, 1024)],
    }
    Path("RESULTS.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"status": "LOCAL_MARGINAL_BOUND_PASS",
                      "cases": len(rows),
                      "golay_level": rows[2]["certificate"]["level"],
                      "golay_pinned_optimum": rows[2]["verification"]["pinned_integer_optimum"],
                      "golay_dual_distance": rows[2]["verification"]["dual_distance"]}))


if __name__ == "__main__":
    main()
