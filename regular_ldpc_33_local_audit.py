"""Finite audit of the (3,3)-regularization phase in arXiv:2606.23161.

The script checks the construction's degree invariants, canonical support maps,
and weight thresholds on tiny 3-left-regular Tanner graphs.  It intentionally
does not claim an independent all-size proof.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def valid(neighbors, checks, mask):
    parity = [0] * checks
    for i, inc in enumerate(neighbors):
        if (mask >> i) & 1:
            for r in inc:
                parity[r] ^= 1
    return not any(parity)


def supports(neighbors, checks):
    return [mask for mask in range(1 << len(neighbors)) if valid(neighbors, checks, mask)]


def add_bit(mask, i):
    return mask | (1 << i)


def split_checks(neighbors, checks):
    """Algorithm 2, plus the prefix metadata for its canonical lift."""
    n = len(neighbors)
    old_check_vars = [[] for _ in range(checks)]
    for v, inc in enumerate(neighbors):
        for r in inc:
            old_check_vars[r].append(v)
    new_inc = [[] for _ in range(n)]
    aux_specs = []
    next_check = 0
    next_var = n

    def edge(v, r):
        new_inc[v].append(r)

    for old_r, vars_at_r in enumerate(old_check_vars):
        k = len(vars_at_r)
        if k <= 3:
            for v in vars_at_r:
                edge(v, next_check)
            next_check += 1
            continue
        chain = list(range(next_check, next_check + k - 2))
        next_check += k - 2
        aux = list(range(next_var, next_var + k - 3))
        next_var += k - 3
        new_inc.extend([[] for _ in aux])
        for j, a in enumerate(aux):
            aux_specs.append((a, tuple(vars_at_r[:j + 2])))
        edge(vars_at_r[0], chain[0])
        edge(vars_at_r[1], chain[0])
        edge(aux[0], chain[0])
        for j in range(1, k - 3):
            edge(aux[j - 1], chain[j])
            edge(vars_at_r[j + 1], chain[j])
            edge(aux[j], chain[j])
        edge(aux[-1], chain[-1])
        edge(vars_at_r[-2], chain[-1])
        edge(vars_at_r[-1], chain[-1])
    return new_inc, next_check, aux_specs


def split_lift(mask, original_n, aux_specs):
    out = mask & ((1 << original_n) - 1)
    for a, prefix in aux_specs:
        parity = 0
        for v in prefix:
            parity ^= (mask >> v) & 1
        if parity:
            out = add_bit(out, a)
    return out


def duplicate_and_split(neighbors, checks, aux_count, original_count):
    """Duplicate G1, couple copies, and split every degree-four original copy."""
    n = len(neighbors)
    dup_checks = 2 * checks
    duplicated = [tuple(inc) for inc in neighbors]
    duplicated.extend(tuple(r + checks for r in inc) for inc in neighbors)
    for u in range(n):
        coupling = dup_checks + u
        duplicated[u] = tuple(duplicated[u]) + (coupling,)
        duplicated[n + u] = tuple(duplicated[n + u]) + (coupling,)
    dup_check_count = dup_checks + n

    new_inc = []
    old_to_new = []
    representatives = []
    next_check = dup_check_count
    for old_id, inc in enumerate(duplicated):
        if len(inc) == 3:
            old_to_new.append((len(new_inc),))
            new_inc.append(tuple(inc))
        elif len(inc) == 4:
            e = next_check
            next_check += 1
            p1, p2 = len(new_inc), len(new_inc) + 1
            old_to_new.append((p1, p2))
            new_inc.extend(((inc[0], inc[1], e), (inc[2], inc[3], e)))
        else:
            raise AssertionError((old_id, inc))
    for v in range(original_count):
        representatives.append(old_to_new[v][0])
    return new_inc, next_check, old_to_new, representatives


def duplicate_split_lift(mask, old_n, old_to_new):
    out = 0
    for old_id in range(old_n):
        if (mask >> old_id) & 1:
            for new_id in old_to_new[old_id]:
                out = add_bit(out, new_id)
            # copy 1 is the second block in the duplicated graph.
            copy_id = old_id + old_n
            for new_id in old_to_new[copy_id]:
                out = add_bit(out, new_id)
    return out


def replicate(neighbors, checks, target, m):
    assert m >= 2 and m % 2 == 0
    out = [tuple(x) for x in neighbors]
    r1, r2, r3 = out[target]
    out[target] = (r3, checks, checks + 1)
    next_check = checks + 2
    x1 = len(out)
    x2 = x1 + 1
    out.extend(((r1, checks), (r2, checks + 1)))
    for i in range(4, m + 1, 2):
        xm3, xm2, xm1, xi = (x1 + i - 4, x1 + i - 3,
                              x1 + i - 2, x1 + i - 1)
        yl, yr, yp = next_check, next_check + 1, next_check + 2
        out[xm3] = tuple(out[xm3]) + (yl,)
        out[xm2] = tuple(out[xm2]) + (yr,)
        out.extend(((yl, yp), (yr, yp)))
        next_check += 3
    terminal = next_check
    out[x1 + m - 2] = tuple(out[x1 + m - 2]) + (terminal,)
    out[x1 + m - 1] = tuple(out[x1 + m - 1]) + (terminal,)
    next_check += 1
    assert all(len(set(x)) == 3 for x in out)
    return out, next_check


def duplicate_graph(neighbors, checks, copies):
    out = []
    for c in range(copies):
        out.extend(tuple(r + c * checks for r in inc) for inc in neighbors)
    return out, copies * checks


def suffix_complete(neighbors, checks):
    """Phase II completion with explicit check-incidence updates."""
    check_vars = [[] for _ in range(checks)]
    for v, inc in enumerate(neighbors):
        for r in inc:
            check_vars[r].append(v)
    q = [r for r, vs in enumerate(check_vars) if len(vs) == 2]
    if not q:
        return [tuple(x) for x in neighbors], checks, []
    n = len(neighbors)
    c = 3
    while c * len(q) < 3 * n + 3:
        c += 3
    base, check_count = duplicate_graph(neighbors, checks, c)
    check_vars = [[] for _ in range(check_count)]
    for v, inc in enumerate(base):
        for r in inc:
            check_vars[r].append(v)
    current = [r + k * checks for k in range(c) for r in q]
    suffix = []
    while len(current) > 3:
        nj = len(current)
        stage_ids = []
        new_checks = list(range(check_count, check_count + nj - 3))
        check_count += nj - 3
        check_vars.extend([[] for _ in new_checks])
        # Construct variables and add their incidences to old/new checks.
        for idx in range(nj - 2):
            if idx == 0:
                inc = [current[0], current[1], new_checks[0]]
            elif idx == nj - 3:
                inc = [new_checks[-1], current[-2], current[-1]]
            else:
                inc = [new_checks[idx - 1], current[idx + 1], new_checks[idx]]
            v = len(base)
            base.append(tuple(inc))
            stage_ids.append(v)
            for r in inc:
                check_vars[r].append(v)
        suffix.extend(stage_ids)
        current = new_checks
    # terminal variable touches all three remaining checks.
    v = len(base)
    base.append(tuple(current))
    suffix.append(v)
    for r in current:
        check_vars[r].append(v)
    assert all(len(vs) == 3 for vs in check_vars)
    assert all(len(set(inc)) == 3 for inc in base)
    return base, check_count, suffix


def map_replicated(mask, targets, old_count, m):
    out = mask
    offset = old_count
    for target in targets:
        if (mask >> target) & 1:
            out |= ((1 << m) - 1) << offset
        offset += m
    return out


def make_graph(kind):
    if kind == "cubic_three":
        # Every check has degree three; this also has nonzero codewords.
        return [(0, 1, 2), (0, 1, 2), (0, 1, 2)], 3
    if kind == "one_four_check":
        # Every variable has degree three; one check has degree four.
        return [(0, 1, 2), (0, 1, 3), (0, 2, 3), (0, 2, 3)], 4
    raise AssertionError(kind)


def run_case(kind):
    base, checks = make_graph(kind)
    n = len(base)
    old_supports = supports(base, checks)
    g1, r1, aux_specs = split_checks(base, checks)
    split_supports = supports(g1, r1)
    lifted = {split_lift(mask, n, aux_specs) for mask in old_supports}
    assert set(split_supports) == lifted
    g2, r2, old_to_new, reps = duplicate_and_split(g1, r1, len(aux_specs), n)
    g1_supports = set(split_supports)
    g2_supports = set(supports(g2, r2))
    mapped_g2 = {duplicate_split_lift(mask, len(g1), old_to_new) for mask in g1_supports}
    assert g2_supports == mapped_g2
    m = 2 * max(1, len(aux_specs))
    g3 = [tuple(x) for x in g2]
    r3 = r2
    current_reps = reps
    mapped_g3 = {mask: mask for mask in g2_supports}
    for rep in current_reps:
        old_count = len(g3)
        g3, r3 = replicate(g3, r3, rep, m)
        # Every lift from G2 remains valid after the local replication.
        for mask in g2_supports:
            mapped = mapped_g3[mask]
            if (mapped >> rep) & 1:
                mapped |= ((1 << m) - 1) << old_count
            mapped_g3[mask] = mapped
            assert valid(g3, r3, mapped)
    N = len(g3)
    # Phase-II construction and degree check.  We do not enumerate its large
    # final code; the paper's suffix lower-bound argument is the all-size step.
    g4, r4, suffix = suffix_complete(g3, r3)
    assert all(len(set(x)) == 3 for x in g4)
    check_degrees = [0] * r4
    for inc in g4:
        for r in inc:
            check_degrees[r] += 1
    assert all(d == 3 for d in check_degrees)
    # Forward maps from every original support into one copy of G3, then the
    # suffix graph, remain valid and obey the first-phase weight formula.
    maps = 0
    for mask in old_supports:
        s1 = split_lift(mask, n, aux_specs)
        s2 = duplicate_split_lift(s1, len(g1), old_to_new)
        # Rebuild the sequential replication map, with the same representative
        # order and offsets as the construction.
        mapped = s2
        offset = len(g2)
        for rep in reps:
            if (mapped >> rep) & 1:
                mapped |= ((1 << m) - 1) << offset
            offset += m
        assert valid(g3, r3, mapped)
        # One copy of G3 is embedded by the completion construction; variables
        # in that copy retain their IDs, so the map remains valid in G4.
        assert valid(g4, r4, mapped)
        orig_weight = mask.bit_count()
        aux_weight = sum((s1 >> a) & 1 for a, _ in aux_specs)
        lam = m + 4
        assert mapped.bit_count() == lam * orig_weight + 2 * aux_weight
        maps += 1
    return {
        "kind": kind,
        "input_supports": len(old_supports),
        "split_supports": len(split_supports),
        "g2_supports": len(g2_supports),
        "g3_variables": len(g3),
        "g4_variables": len(g4),
        "suffix_variables": len(suffix),
        "forward_maps": maps,
        "auxiliary_variables": len(aux_specs),
    }


def run_generated_cases(seed=20261018, count=12):
    """Audit the generic completion on fresh small 3-left-regular inputs.

    The output graphs are intentionally too large for brute-force support
    enumeration.  The checks are therefore the all-size structural obligations
    that can be tested directly: degree three on both sides, validity of every
    canonical lift, the exact first-phase weight identity, and the suffix
    lower-bound inequality used to exclude new small supports.
    """
    rng = random.Random(seed)
    rows = []
    attempts = 0
    while len(rows) < count:
        attempts += 1
        checks = rng.randint(3, 5)
        variables = rng.randint(3, 5)
        neighbors = [tuple(sorted(rng.sample(range(checks), 3)))
                     for _ in range(variables)]
        check_degrees = [0] * checks
        for inc in neighbors:
            for row in inc:
                check_degrees[row] += 1
        # The theorem removes degree-one checks before this phase.
        if min(check_degrees) < 2:
            continue

        old_supports = set(supports(neighbors, checks))
        g1, r1, aux_specs = split_checks(neighbors, checks)
        g2, r2, old_to_new, reps = duplicate_and_split(
            g1, r1, len(aux_specs), variables)
        m = 2 * max(1, len(aux_specs))
        g3 = [tuple(x) for x in g2]
        r3 = r2
        for rep in reps:
            g3, r3 = replicate(g3, r3, rep, m)

        g4, r4, suffix = suffix_complete(g3, r3)
        assert all(len(set(inc)) == 3 for inc in g4)
        final_check_degrees = [0] * r4
        for inc in g4:
            for row in inc:
                final_check_degrees[row] += 1
        assert all(degree == 3 for degree in final_check_degrees)

        for mask in old_supports:
            split_mask = split_lift(mask, variables, aux_specs)
            duplicate_mask = duplicate_split_lift(
                split_mask, len(g1), old_to_new)
            lifted = duplicate_mask
            offset = len(g2)
            for rep in reps:
                if (lifted >> rep) & 1:
                    lifted |= ((1 << m) - 1) << offset
                offset += m
            assert valid(g4, r4, lifted)
            aux_weight = sum((split_mask >> a) & 1 for a, _ in aux_specs)
            assert lifted.bit_count() == (m + 4) * mask.bit_count() + 2 * aux_weight

        degree_counts = [0] * r3
        for inc in g3:
            for row in inc:
                degree_counts[row] += 1
        q = sum(degree == 2 for degree in degree_counts)
        h = 0
        if q:
            c = 3
            while c * q < 3 * len(g3) + 3:
                c += 3
            h = c * q
            assert h // 3 > len(g3)
        rows.append({
            "variables": variables,
            "checks": checks,
            "input_supports": len(old_supports),
            "auxiliary_variables": len(aux_specs),
            "g3_variables": len(g3),
            "g3_degree_two_checks": q,
            "suffix_variables": len(suffix),
            "g4_variables": len(g4),
            "g4_checks": r4,
            "suffix_bound_h": h,
        })
    assert attempts < count * 100
    return {"seed": seed, "requested": count, "completed": len(rows),
            "attempts": attempts, "rows": rows}


def main():
    rows = [run_case("cubic_three"), run_case("one_four_check")]
    payload = {
        "source": "Jia et al., arXiv:2606.23161v3, Theorem 18",
        "scope": "finite reconstruction of the (3,3)-regularization phase; not an all-size proof",
        "rows": rows,
        "random_completion": run_generated_cases(),
        "all_checks_passed": True,
    }
    payload["source_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (Path(__file__), ROOT / "REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md")
    }
    (ROOT / "REGULAR_LDPC_33_LOCAL_AUDIT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
