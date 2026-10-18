"""Independent, explicitly exponential bit-parallel truth enumeration controls."""


def bitset_truth_count(n, clauses, max_variables=32):
    if type(n) is not int or not 0 <= n <= max_variables:
        raise ValueError('bitset oracle dimension cap')
    if any(type(lit) is not int or lit == 0 or abs(lit) > n for c in clauses for lit in c):
        raise ValueError('original literal')
    left = n//2
    right = n-left
    width = 1 << right
    full = (1 << width)-1
    masks = []
    for j in range(right):
        half_period = 1 << j
        period = 2*half_period
        block = ((1 << half_period)-1) << half_period
        masks.append(block*(full//((1 << period)-1)))
    prepared = []
    for clause in clauses:
        left_literals, right_mask = [], 0
        for lit in clause:
            v = abs(lit)-1
            if v < left:
                left_literals.append((v, lit > 0))
            else:
                mask = masks[v-left]
                right_mask |= mask if lit > 0 else full ^ mask
        prepared.append((left_literals, right_mask))
    count = ands = clause_visits = 0
    for assignment in range(1 << left):
        live = full
        for lits, mask in prepared:
            clause_visits += 1
            if any(bool((assignment >> v) & 1) == sign for v, sign in lits):
                continue
            live &= mask
            ands += 1
            if not live:
                break
        count += live.bit_count()
    return {'count': count, 'outer_assignments': 1 << left,
            'right_assignment_bits': width, 'logical_assignments_covered': 1 << n,
            'clause_visits': clause_visits, 'big_integer_ands': ands,
            'and_bit_work_upper_bound': ands*width,
            'method': 'complete split truth table with exponential-size row bitsets'}


def sliding_count(n, clauses):
    if n != len(clauses)+2 or any(sorted(abs(lit) for lit in c) != [i+1, i+2, i+3]
                                for i, c in enumerate(clauses)):
        raise ValueError('requires the original consecutive triple chain')
    counts = [1]*4
    transitions = 0
    for i, clause in enumerate(clauses):
        out = [0]*4
        for state in range(4):
            for bit in (0, 1):
                bits = [(state >> j) & 1 for j in (0, 1)]+[bit]
                transitions += 1
                if any(bool(bits[abs(lit)-1-i]) == (lit > 0) for lit in clause):
                    out[(state >> 1) | (bit << 1)] += counts[state]
        counts = out
    return {'count': sum(counts), 'transitions': transitions,
            'method': 'independent four-state original signed-clause transfer'}
