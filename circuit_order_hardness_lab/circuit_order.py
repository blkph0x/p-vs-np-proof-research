"""Small Tseitin circuits whose source primal graph is prescribed.

The construction is deliberately modest.  For every graph edge {u, v} it
creates an OR gate z_e = x_u OR x_v and pins z_e to one.  The resulting CNF
is always satisfiable (all source bits one), while its primal graph contains
the original graph on the source variables.  The exact order routines are
used only on small controls; the lower-bound statement itself is general.
"""

from __future__ import annotations

from itertools import combinations


def validate_graph(n, edges):
    if type(n) is not int or n < 0:
        raise ValueError("nonnegative vertex count required")
    if type(edges) not in (list, tuple):
        raise ValueError("edge list required")
    checked = set()
    for edge in edges:
        if type(edge) not in (list, tuple) or len(edge) != 2:
            raise ValueError("edge pair required")
        u, v = edge
        if (type(u) is not int or type(v) is not int or u == v
                or not 0 <= u < n or not 0 <= v < n):
            raise ValueError("invalid edge")
        if u > v:
            u, v = v, u
        if (u, v) in checked:
            raise ValueError("duplicate edge")
        checked.add((u, v))
    return tuple(sorted(checked))


def build_edge_or_circuit(n, edges):
    """Build exact OR-gate Tseitin clauses, one pinned output per edge."""
    edges = validate_graph(n, edges)
    clauses = []
    gates = []
    outputs = []
    for index, (u, v) in enumerate(edges):
        left, right = u + 1, v + 1
        output = n + index + 1
        # output = left OR right
        clauses.extend(([-left, output], [-right, output],
                        [left, right, -output], [output]))
        gates.append(("or", output, left, right))
        outputs.append(output)
    return {
        "vertices": n + len(edges),
        "source_variables": n,
        "edges": [list(edge) for edge in edges],
        "clauses": [list(clause) for clause in clauses],
        "gates": [list(gate) for gate in gates],
        "outputs": outputs,
    }


def evaluate(circuit, assignment):
    n = circuit["source_variables"]
    if type(assignment) is not int or assignment < 0 or assignment >= (1 << n):
        raise ValueError("assignment does not fit source dimension")
    values = {1 + bit: (assignment >> bit) & 1 for bit in range(n)}
    for kind, output, left, right in circuit["gates"]:
        if kind != "or":
            raise ValueError("unknown gate")
        values[output] = values[left] | values[right]
    return values


def clauses_satisfied(clauses, values):
    return all(any((literal > 0) == bool(values[abs(literal)])
                   for literal in clause) for clause in clauses)


def primal_edges(clauses, variables):
    """Return the undirected primal graph as sorted variable pairs."""
    pairs = set()
    for clause in clauses:
        scope = sorted(set(abs(literal) for literal in clause))
        for left, right in combinations(scope, 2):
            if left < 1 or right > variables:
                raise ValueError("literal outside variable range")
            pairs.add((left, right))
    return tuple(sorted(pairs))


def boundary(variables, edges, subset):
    if type(subset) is not int or subset < 0 or subset >= (1 << variables):
        raise ValueError("invalid subset")
    adjacency = [0] * variables
    for left, right in edges:
        left -= 1
        right -= 1
        adjacency[left] |= 1 << right
        adjacency[right] |= 1 << left
    suffix = ((1 << variables) - 1) ^ subset
    return tuple(index + 1 for index in range(variables)
                 if subset >> index & 1 and adjacency[index] & suffix)


def width_for_order(variables, edges, order):
    order = tuple(order)
    if sorted(order) != list(range(1, variables + 1)):
        raise ValueError("order must be a permutation")
    subset = 0
    widths = []
    records = []
    for cut, variable in enumerate(order, 1):
        subset |= 1 << (variable - 1)
        active = boundary(variables, edges, subset)
        widths.append(0 if cut == variables else len(active))
        records.append({"cut": cut, "subset": subset,
                        "boundary": list(active), "width": widths[-1]})
    return max(widths, default=0), records


def optimal_width(variables, edges):
    """Exact bottleneck subset DP; intended for small validation controls."""
    edges = tuple(edges)
    full = (1 << variables) - 1
    best = {0: (0, ())}
    for subset in range(full + 1):
        if subset not in best:
            continue
        prior_width, prior_order = best[subset]
        for variable in range(1, variables + 1):
            bit = 1 << (variable - 1)
            if subset & bit:
                continue
            nxt = subset | bit
            cut_width = 0 if nxt == full else len(boundary(variables, edges, nxt))
            candidate = (max(prior_width, cut_width), prior_order + (variable,))
            if nxt not in best or candidate < best[nxt]:
                best[nxt] = candidate
    width, order = best[full]
    replay, records = width_for_order(variables, edges, order)
    if replay != width:
        raise AssertionError("subset-DP replay mismatch")
    return {"status": "EXACT", "width": width, "order": list(order),
            "records": records, "state_count": len(best)}


def source_lower_bound(circuit):
    """Compute the source graph and its exact width on a small control."""
    source_edges = tuple((u + 1, v + 1) for u, v in
                         validate_graph(circuit["source_variables"], circuit["edges"]))
    result = optimal_width(circuit["source_variables"], source_edges)
    full_edges = primal_edges(circuit["clauses"], circuit["vertices"])
    full = optimal_width(circuit["vertices"], full_edges)
    extended = extend_source_order(circuit, result["order"])
    extended_width, _ = width_for_order(circuit["vertices"], full_edges, extended)
    return {"source": result, "full": full,
            "source_edges": [list(edge) for edge in source_edges],
            "full_edges": [list(edge) for edge in full_edges],
            "lower_bound_holds": full["width"] >= result["width"],
            "extended_order": extended,
            "extended_width": extended_width,
            "additive_upper_bound_holds": extended_width <= result["width"] + 1}


def extend_source_order(circuit, source_order):
    """Insert each edge gate immediately after its later source endpoint."""
    n = circuit["source_variables"]
    source_order = tuple(source_order)
    if sorted(source_order) != list(range(1, n + 1)):
        raise ValueError("source order must be a permutation")
    rank = {variable: index for index, variable in enumerate(source_order)}
    after = {variable: [] for variable in source_order}
    for index, (u, v) in enumerate(circuit["edges"]):
        left, right = u + 1, v + 1
        later = right if rank[right] > rank[left] else left
        after[later].append(n + index + 1)
    order = []
    for source in source_order:
        order.append(source)
        order.extend(sorted(after[source]))
    return order
