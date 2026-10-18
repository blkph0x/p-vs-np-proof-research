"""Exact bounded coefficient controls for products of binary monomial choices."""
from math import gcd


def checked(choices, target):
    choices = tuple(tuple(pair) for pair in choices)
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    if any(len(pair) != 2 or any(type(x) is not int or x < 0 for x in pair) for pair in choices):
        raise ValueError("each choice must contain two nonnegative integer exponents")
    return choices


def normalize(choices, target):
    choices = checked(choices, target)
    lower = sum(min(pair) for pair in choices)
    diffs = [abs(a-b) for a,b in choices]
    zero_count = diffs.count(0)
    positive = [d for d in diffs if d]
    common = 0
    for d in positive:
        common = gcd(common,d)
    offset = target-lower
    if offset < 0 or offset > sum(positive) or (common and offset % common):
        return {"outside_support_lattice": True, "coefficient": 0, "q": len(choices)}
    if not positive:
        return {"outside_support_lattice": False, "monomial": True,
                "coefficient": 1 << zero_count, "q": len(choices)}
    diffs = [d//common for d in positive]
    degree, t = sum(diffs), offset//common
    return {"outside_support_lattice": False, "monomial": False,
            "q": len(choices), "zero_count": zero_count, "gcd": common,
            "differences": diffs, "degree": degree, "target": t,
            "symmetric_target": min(t,degree-t)}


def _immediate(normal):
    if "coefficient" in normal:
        return {"status": "EXACT", "coefficient": normal["coefficient"],
                "method": "support_lattice_or_monomial"}
    return None


def sparse_coefficient(choices, target, *, max_states=4096, max_transitions=1000000):
    if any(type(x) is not int or x < 0 for x in (max_states,max_transitions)):
        raise ValueError("invalid cap")
    normal = normalize(choices,target)
    immediate = _immediate(normal)
    if immediate is not None:
        return immediate
    h, states, transitions, peak = normal["symmetric_target"], {0:1}, 0, 1
    if max_states < 1:
        return {"status":"UNKNOWN", "reason":"initial state cap"}
    for d in normal["differences"]:
        if transitions+2*len(states) > max_transitions:
            return {"status":"UNKNOWN", "reason":"transition cap", "transitions":transitions}
        next_states = {}
        for cost,count in states.items():
            for new_cost in (cost,cost+d):
                transitions += 1
                if new_cost <= h:
                    next_states[new_cost] = next_states.get(new_cost,0)+count
                if len(next_states) > max_states:
                    return {"status":"UNKNOWN", "reason":"state cap", "transitions":transitions}
        states = next_states
        peak = max(peak,len(states))
    return {"status":"EXACT", "coefficient":states.get(h,0) << normal["zero_count"],
            "method":"bounded_sparse_count", "transitions":transitions, "peak_states":peak}


def packed_integer_coefficient(choices, target, *, max_pack_bits=1000000,
                               max_bit_work_proxy=20000000):
    if any(type(x) is not int or x < 0 for x in (max_pack_bits,max_bit_work_proxy)):
        raise ValueError("invalid cap")
    normal = normalize(choices,target)
    immediate = _immediate(normal)
    if immediate is not None:
        return immediate
    h, r = normal["symmetric_target"], len(normal["differences"])
    spacing = r+1
    bits, work = spacing*(h+1), r*spacing*(h+1)
    if bits > max_pack_bits or work > max_bit_work_proxy:
        return {"status":"UNKNOWN", "reason":"packed integer bit cap", "required_pack_bits":bits,
                "bit_work_proxy":work, "reduced_target":h}
    mask = (1 << bits)-1
    packed = 1
    for d in normal["differences"]:
        if d <= h:
            packed = (packed+(packed << (spacing*d))) & mask
    coefficient = (packed >> (spacing*h)) << normal["zero_count"]
    return {"status":"EXACT", "coefficient":coefficient, "method":"carry_free_integer_digits",
            "required_pack_bits":bits, "bit_work_proxy":work,
            "individual_temporary_integer_bit_bound":2*bits,
            "digit_bits":spacing, "reduced_target":h, "zero_difference_count":normal["zero_count"],
            "packed_hex":hex(packed)}


def binary_ladder_coefficient(choices, target):
    normal = normalize(choices,target)
    immediate = _immediate(normal)
    if immediate is not None:
        return immediate
    diffs = sorted(normal["differences"])
    if any(d != 1 << i for i,d in enumerate(diffs)):
        return {"status":"UNKNOWN", "reason":"not a complete binary ladder"}
    return {"status":"EXACT", "coefficient":1 << normal["zero_count"],
            "method":"complete_binary_ladder_identity", "positive_differences":len(diffs)}


def _trial_prime(p, cap):
    if p < 2:
        return False
    if p % 2 == 0:
        return p == 2
    divisor, work = 3, 0
    while divisor*divisor <= p:
        if work >= cap:
            return None
        work += 1
        if p % divisor == 0:
            return False
        divisor += 2
    return True


def prime_field_filter(choices, target, p, order, omega, *, max_evaluations=4096,
                       max_prime_trials=100000):
    choices = checked(choices,target)
    if any(type(x) is not int for x in (p,order,omega,max_evaluations,max_prime_trials)):
        raise ValueError("integer field parameters and caps required")
    if p < 2 or order < 1 or not 0 < omega < p or min(max_evaluations,max_prime_trials) < 0:
        raise ValueError("invalid field parameters or cap")
    if order > max_evaluations:
        return {"status":"UNKNOWN", "reason":"evaluation cap"}
    prime = _trial_prime(p,max_prime_trials)
    if prime is None:
        return {"status":"UNKNOWN", "reason":"primality-check cap"}
    if not prime or (p-1) % order or pow(omega,order,p) != 1:
        raise ValueError("prime field and root-of-unity conditions fail")
    # With order bounded by max_evaluations, trial factorization is explicitly bounded too.
    remaining, factors, divisor = order, [], 2
    while divisor*divisor <= remaining:
        if remaining % divisor == 0:
            factors.append(divisor)
            while remaining % divisor == 0:
                remaining //= divisor
        divisor += 1
    if remaining > 1:
        factors.append(remaining)
    if any(pow(omega,order//factor,p) == 1 for factor in factors):
        raise ValueError("root does not have the claimed exact order")
    reduced = [(a % order,b % order) for a,b in choices]
    reduced_target = target % order
    values, total, point = [], 0, 1
    for j in range(order):
        value = 1
        for a,b in reduced:
            value = value*(pow(point,a,p)+pow(point,b,p)) % p
        weighted = value*pow(omega,(-reduced_target*j) % order,p) % p
        values.append({"index":j,"point":point,"value":value,"weighted_value":weighted})
        total = (total+weighted) % p
        point = point*omega % p
    residue = total*pow(order,-1,p) % p
    degree, bound = sum(max(pair) for pair in choices), 1 << len(choices)
    alias_free = order > degree and target <= degree
    answer = {"status":"EXACT", "quantity":"residue_folded_coefficient_sum_mod_p",
              "p":p, "order":order, "omega":omega, "filter_residue":residue,
              "degree":degree, "coefficient_upper_bound":bound, "alias_free":alias_free,
              "evaluations":values, "coefficient_decision":"UNKNOWN"}
    if p > bound:
        answer["exact_folded_count"] = residue
    if target > degree:
        answer.update(exact_coefficient=0, coefficient_decision="ZERO",
                      decision_reason="target exceeds polynomial degree, independently of the folded sum")
    elif p > bound and residue == 0:
        answer.update(exact_coefficient=0, coefficient_decision="ZERO",
                      decision_reason="the exact nonnegative folded count is zero")
    elif alias_free and p > bound:
        answer.update(exact_coefficient=residue,
                      coefficient_decision="POSITIVE" if residue else "ZERO")
    elif alias_free and residue:
        answer["coefficient_decision"] = "POSITIVE"
    return answer


def reconstruct_bounded_count(congruences, bound):
    """CRT uniqueness only: supplied residues must independently concern one verified count."""
    if type(bound) is not int or bound < 0:
        raise ValueError("nonnegative integer coefficient bound required")
    residue, modulus = 0, 1
    for m,value in congruences:
        if any(type(x) is not int for x in (m,value)) or m < 2 or not 0 <= value < m:
            raise ValueError("invalid congruence")
        if gcd(modulus,m) != 1:
            raise ValueError("moduli must be pairwise coprime")
        adjustment = ((value-residue)*pow(modulus,-1,m)) % m
        residue += modulus*adjustment
        modulus *= m
    if residue > bound:
        return {"status":"INVALID", "reason":"no count within asserted bound"}
    if modulus > bound:
        return {"status":"EXACT", "coefficient":residue, "combined_modulus":modulus}
    return {"status":"UNKNOWN", "reason":"coefficient range not uniquely determined",
            "residue":residue, "combined_modulus":modulus}
