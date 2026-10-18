"""SAT-to-exact-weight matching encoding; deliberately not an ordinary min-cost solver."""
import hashlib


def formula(n, clauses):
    if type(n) is not int or n < 0:
        raise ValueError("invalid variable count")
    clauses = tuple(tuple(c) for c in clauses)
    for clause in clauses:
        if not 1 <= len(clause) <= 3:
            raise ValueError("this encoder accepts nonempty clauses of width at most three")
        if any(type(x) is not int or x == 0 or abs(x) > n for x in clause):
            raise ValueError("invalid literal")
        if len({abs(x) for x in clause}) != len(clause):
            raise ValueError("clauses must have distinct underlying variables")
    return clauses


def satisfied(n, clauses, assignment):
    clauses = formula(n, clauses)
    if type(assignment) is not int or assignment < 0 or assignment.bit_length() > n:
        raise ValueError("invalid assignment")
    return all(any(bool((assignment >> (abs(x)-1)) & 1) == (x > 0) for x in clause)
               for clause in clauses)


def encode(n, clauses):
    clauses = formula(n, clauses)
    powers = [6**j for j in range(len(clauses))]
    choices = [[0, 0] for _ in range(n)]
    for clause, power in zip(clauses, powers):
        for literal in clause:
            choices[abs(literal)-1][int(literal < 0)] += power
    slack_clauses = []
    for j, clause in enumerate(clauses):
        for _ in range(len(clause)-1):
            choices.append([0, powers[j]])
            slack_clauses.append(j)
    target = sum((len(c)-1)*p for c, p in zip(clauses, powers))
    edges = []
    for i, (w0, w1) in enumerate(choices):
        a = 4*i
        # Exactly two perfect matchings: edges 0,2 or edges 1,3.
        edges.extend([[a, a+1, w0], [a+1, a+2, w1],
                      [a+2, a+3, 0], [a, a+3, 0]])
    return {"n": n, "clauses": [list(c) for c in clauses], "base": 6,
            "choice_weights": choices, "slack_clauses": slack_clauses,
            "target": target, "vertices": 4*len(choices), "edges": edges}


def encode_solution(encoding, assignment):
    n, clauses = encoding["n"], encoding["clauses"]
    if not satisfied(n, clauses, assignment):
        raise ValueError("assignment does not satisfy the original formula")
    bits = [(assignment >> i) & 1 for i in range(n)]
    for clause in clauses:
        false_count = sum(bool((assignment >> (abs(x)-1)) & 1) != (x > 0) for x in clause)
        needed = len(clause)-1-false_count
        bits.extend([1]*needed + [0]*(len(clause)-1-needed))
    return bits


def verify_encoding(n, clauses, encoding):
    """Bind supplied graph, costs and target to the external original formula."""
    try:
        clauses = formula(n, clauses)
        if set(encoding) != {"n", "clauses", "base", "choice_weights", "slack_clauses", "target", "vertices", "edges"}:
            return False
        if type(encoding["n"]) is not int or encoding["n"] != n or formula(n, encoding["clauses"]) != clauses:
            return False
        for key in ("base", "target", "vertices"):
            if type(encoding[key]) is not int:
                return False
        if encoding["base"] != 6:
            return False
        expected = []
        for variable in range(1, n+1):
            expected.append([sum(6**j for j, c in enumerate(clauses)
                                 if (variable if bit == 0 else -variable) in c)
                             for bit in (0, 1)])
        slack = [j for j, c in enumerate(clauses) for _ in range(len(c)-1)]
        expected += [[0, 6**j] for j in slack]
        if encoding["slack_clauses"] != slack or any(type(j) is not int for j in encoding["slack_clauses"]):
            return False
        pairs = _checked(encoding["choice_weights"], encoding["target"])
        if [list(p) for p in pairs] != expected:
            return False
        if encoding["target"] != sum((len(c)-1)*6**j for j, c in enumerate(clauses)):
            return False
        if encoding["vertices"] != 4*len(pairs) or len(encoding["edges"]) != 4*len(pairs):
            return False
        for i, pair in enumerate(pairs):
            a = 4*i
            wanted = [(a, a+1, pair[0]), (a+1, a+2, pair[1]), (a+2, a+3, 0), (a, a+3, 0)]
            for row, check in zip(encoding["edges"][4*i:4*i+4], wanted):
                if any(type(x) is not int for x in row) or tuple(row) != check:
                    return False
        return True
    except (ValueError, TypeError, KeyError, IndexError):
        return False


def matching_for_choices(bits):
    if any(type(b) is not int or b not in (0, 1) for b in bits):
        raise ValueError("choices must be bits")
    return [4*i+edge for i, bit in enumerate(bits) for edge in ((0, 2) if bit == 0 else (1, 3))]


def verify_matching(encoding, matching, *, exact=True):
    """Check coverage, edge costs and original formula; no matching search."""
    try:
        n, edges = encoding["vertices"], encoding["edges"]
        covered, ids, cost = set(), set(), 0
        for i in matching:
            if type(i) is not int or not 0 <= i < len(edges) or i in ids:
                raise ValueError("invalid matching edge")
            u, v, w = edges[i]
            if u in covered or v in covered:
                raise ValueError("repeated vertex")
            covered.update((u, v)); ids.add(i); cost += w
        if covered != set(range(n)):
            raise ValueError("incomplete vertex coverage")
        if exact and cost != encoding["target"]:
            raise ValueError("wrong exact weight")
        bits = []
        for i in range(len(encoding["choice_weights"])):
            local = {j-4*i for j in ids if 4*i <= j < 4*i+4}
            if local not in ({0, 2}, {1, 3}):
                raise ValueError("wrong four-cycle matching")
            bits.append(int(local == {1, 3}))
        assignment = sum(bit << i for i, bit in enumerate(bits[:encoding["n"]]))
        if exact and not satisfied(encoding["n"], encoding["clauses"], assignment):
            raise ValueError("exact matching does not satisfy original clauses")
        return {"valid": True, "cost": cost, "assignment": assignment, "choice_bits": bits}
    except (ValueError, TypeError, KeyError, IndexError):
        return {"valid": False}


def _checked(choices, target):
    choices = tuple(tuple(pair) for pair in choices)
    if type(target) is not int or target < 0:
        raise ValueError("nonnegative integer target required")
    if any(len(p) != 2 or any(type(x) is not int or x < 0 for x in p) for p in choices):
        raise ValueError("two nonnegative integer costs per choice required")
    return choices


def _hash(choices, target):
    digest = hashlib.sha256(b"bounded_exact_cost_choices_v1\0")
    for x in (len(choices), target, *(w for pair in choices for w in pair)):
        data = x.to_bytes(max(1, (x.bit_length()+7)//8), "little")
        digest.update(len(data).to_bytes(8, "little")); digest.update(data)
    return digest.hexdigest()


def solve_choices(choices, target, *, max_states=4096, max_transitions=1000000):
    choices = _checked(choices, target)
    if any(type(x) is not int or x < 0 for x in (max_states, max_transitions)):
        raise ValueError("invalid budget")
    layers, transitions = [[0]], 0
    for pair in choices:
        previous = layers[-1]
        if len(previous) > max_states or transitions + 2*len(previous) > max_transitions:
            return {"status": "UNKNOWN", "reason": "budget", "completed_choices": len(layers)-1,
                    "peak_states": max(map(len, layers)), "transitions": transitions}
        current = set()
        for cost in previous:
            for weight in pair:
                transitions += 1
                if cost+weight <= target:
                    current.add(cost+weight)
                if len(current) > max_states:
                    return {"status": "UNKNOWN", "reason": "state budget", "completed_choices": len(layers)-1,
                            "peak_states": len(current), "transitions": transitions}
        layers.append(sorted(current))
    if max(map(len, layers)) > max_states:
        return {"status": "UNKNOWN", "reason": "initial state budget", "completed_choices": 0,
                "peak_states": 1, "transitions": 0}
    feasible, bits = target in layers[-1], None
    if feasible:
        bits, cost = [], target
        for i in range(len(choices)-1, -1, -1):
            bit = next(b for b in (0, 1) if cost-choices[i][b] in layers[i])
            bits.append(bit); cost -= choices[i][bit]
        bits.reverse()
    return {"status": "EXACT", "format": "bounded_exact_cost_choices_v1",
            "input_hash": _hash(choices, target), "feasible": feasible,
            "choice_bits": bits, "layers": layers, "transitions": transitions,
            "peak_states": max(map(len, layers))}


def verify_choices(choices, target, result, *, max_transitions=2000000):
    try:
        choices = _checked(choices, target)
        if type(max_transitions) is not int or max_transitions < 0:
            raise ValueError("invalid budget")
        if result.get("status") != "EXACT":
            return {"valid": False, "status": "UNKNOWN"}
        if result.get("format") != "bounded_exact_cost_choices_v1" or result.get("input_hash") != _hash(choices, target):
            raise ValueError("wrong original input")
        layers = result["layers"]
        if len(layers) != len(choices)+1 or layers[0] != [0]:
            raise ValueError("incomplete layers")
        transitions = 0
        for i, layer in enumerate(layers):
            if not isinstance(layer, list) or any(type(x) is not int or not 0 <= x <= target for x in layer):
                raise ValueError("invalid cost state")
            if layer != sorted(set(layer)):
                raise ValueError("duplicate or unsorted states")
            if i:
                transitions += 2*len(layers[i-1])
                if transitions > max_transitions:
                    return {"valid": False, "status": "UNKNOWN"}
                expected = {old+weight for weight in choices[i-1] for old in layers[i-1] if old+weight <= target}
                if set(layer) != expected:
                    raise ValueError("wrong reachable-cost recurrence")
        feasible = target in layers[-1]
        if type(result["feasible"]) is not bool or result["feasible"] != feasible:
            raise ValueError("wrong feasibility")
        bits = result["choice_bits"]
        if feasible:
            if not isinstance(bits, list) or len(bits) != len(choices) or any(type(b) is not int or b not in (0, 1) for b in bits):
                raise ValueError("invalid choices")
            if sum(pair[b] for pair, b in zip(choices, bits)) != target:
                raise ValueError("wrong exact sum")
        elif bits is not None:
            raise ValueError("spurious witness")
        if type(result["transitions"]) is not int or result["transitions"] != transitions:
            raise ValueError("wrong work count")
        if type(result["peak_states"]) is not int or result["peak_states"] != max(map(len, layers)):
            raise ValueError("wrong peak")
        return {"valid": True, "status": "EXACT"}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return {"valid": False, "status": "INVALID"}
