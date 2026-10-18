"""Exact minimum vertex-boundary order oracle for small primal graphs."""
from __future__ import annotations


def primal_adjacency(nvars, clauses):
    adjacency = [0] * nvars
    for clause in clauses:
        variables = sorted({abs(literal) - 1 for literal in clause})
        for left_index, left in enumerate(variables):
            for right in variables[left_index + 1:]:
                adjacency[left] |= 1 << right
                adjacency[right] |= 1 << left
    return adjacency


def vertex_boundary(mask, adjacency):
    boundary = 0
    remaining = mask
    while remaining:
        bit = remaining & -remaining
        variable = bit.bit_length() - 1
        remaining ^= bit
        if adjacency[variable] & ~mask:
            boundary |= bit
    return boundary.bit_count()


def optimal_order(nvars, clauses):
    """Return an exact minimum-width order by subset recurrence.

    If S is the prefix set, its boundary value is fixed.  The optimal order
    ending at S can therefore be obtained by removing each possible last
    variable and minimizing max(previous width, boundary(S)).
    """
    adjacency = primal_adjacency(nvars, clauses)
    universe = 1 << nvars
    boundaries = [0] * universe
    widths = [nvars + 1] * universe
    last_bits = [0] * universe
    widths[0] = 0
    for mask in range(1, universe):
        boundary = vertex_boundary(mask, adjacency)
        boundaries[mask] = boundary
        remaining = mask
        best = nvars + 1
        best_bit = 0
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            candidate = max(widths[mask ^ bit], boundary)
            if candidate < best:
                best = candidate
                best_bit = bit
        widths[mask] = best
        last_bits[mask] = best_bit

    mask = universe - 1
    reverse_order = []
    while mask:
        bit = last_bits[mask]
        reverse_order.append(bit.bit_length() - 1)
        mask ^= bit
    order = reverse_order[::-1]
    prefix = 0
    prefix_widths = []
    for variable in order:
        prefix |= 1 << variable
        prefix_widths.append(boundaries[prefix])
    return {
        "width": widths[universe - 1],
        "order": order,
        "prefix_widths": prefix_widths,
    }
