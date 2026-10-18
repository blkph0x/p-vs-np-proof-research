"""Independent verifier for the fused negative-suffix macro."""
from __future__ import annotations
from itertools import product


def norm_clause(clause):
    values = tuple(sorted(set(int(x) for x in clause), key=lambda z: (abs(z), z < 0)))
    if any(-value in values for value in values):
        raise ValueError("tautological clause")
    return values


def resolve(left, right, pivot):
    left, right, pivot = set(left), set(right), int(pivot)
    if pivot in left and -pivot in right:
        return norm_clause((left - {pivot}) | (right - {-pivot}))
    if -pivot in left and pivot in right:
        return norm_clause((left - {-pivot}) | (right - {pivot}))
    raise ValueError("invalid pivot")


def expected_groups(certificate):
    a = [norm_clause(c) for c in certificate["A"]]
    b = [norm_clause(c) for c in certificate["B"]]
    if len(b) != 1 or not a:
        raise ValueError("expected one B clause")
    b_clause = b[0]
    if any(lit >= 0 for lit in b_clause):
        raise ValueError("B must be negative")
    groups = len(b_clause)
    if len(a) % groups:
        raise ValueError("A group split")
    width = len(a) // groups
    if width < 2:
        raise ValueError("width")
    expected_a = []
    for group in range(groups):
        rep = group * width + 1
        members = [rep + offset for offset in range(1, width)]
        expected_a.append(norm_clause([rep] + members))
        expected_a.extend(norm_clause([rep, -member]) for member in members)
    if set(a) != set(expected_a) or len(set(a)) != len(expected_a):
        raise ValueError("A family")
    expected_b = norm_clause([-(group * width + 1) for group in range(groups)])
    if b_clause != expected_b:
        raise ValueError("B family")
    return a, b_clause, groups, width, [group * width for group in range(groups)]


def replay(nodes, index, memo, leaves):
    index = int(index)
    if index in memo:
        return memo[index]
    if not 0 <= index < len(nodes):
        raise ValueError("node index")
    row = nodes[index]
    clause = norm_clause(row["clause"])
    if "part" in row:
        if row["part"] not in ("A", "B"):
            raise ValueError("leaf part")
        leaves[index] = (row["part"], clause)
    else:
        left = replay(nodes, row["left"], memo, leaves)
        right = replay(nodes, row["right"], memo, leaves)
        if clause != resolve(left, right, int(row["pivot"]) + 1):
            raise ValueError("resolution")
    memo[index] = clause
    return clause


def leaf_clauses(nodes, root):
    seen, refs = set(), set()
    def visit(index):
        index = int(index)
        if index in seen:
            return
        seen.add(index)
        row = nodes[index]
        if "part" in row:
            refs.add((row["part"], norm_clause(row["clause"])))
        else:
            visit(row["left"])
            visit(row["right"])
    visit(root)
    return refs


def extension_argument_holds(a, b_clause, start, width, boundary, relation_bits):
    for bits, expected in zip(product((False, True), repeat=len(boundary)), relation_bits):
        assignment={variable:False for clause in a for literal in clause for variable in (abs(literal),)}
        for variable in range(start*width):
            assignment[variable+1]=True
        for variable,value in zip(boundary,bits):
            assignment[variable+1]=bool(value)
        if expected:
            if not all(any((assignment[abs(lit)] if lit>0 else not assignment[abs(lit)]) for lit in clause)
                       for clause in a[:start*width]):
                return False
            if not any(not assignment[abs(lit)] for lit in b_clause):
                return False
        else:
            if not all(bits):
                return False
            for group in range(start):
                rep=group*width+1
                hall=a[group*width]
                implications=a[group*width+1:group*width+width]
                if rep not in hall or len(implications)!=width-1:
                    return False
                if any(rep not in clause or -(rep+offset) not in clause
                       for offset,clause in enumerate(implications,1)):
                    return False
            if any((not assignment[abs(lit)] if lit<0 else assignment[abs(lit)]) for lit in b_clause):
                return False
    return True


def relation(boundary):
    bits = tuple(int(not all(values)) for values in product((False, True), repeat=len(boundary)))
    if len(boundary) == 1:
        candidate = {"kind":"UNIT","var":int(boundary[0]),"value":False}
    elif len(boundary) == 2:
        candidate = {"kind":"PB","weights":{str(boundary[0]):1,str(boundary[1]):1},"sense":"<=","bound":1}
    else:
        raise ValueError("boundary width")
    return bits, candidate


def verify_suffix_result(proof_certificate, result):
    try:
        if result["status"] != "FOUND" or result["kind"] != "SUFFIX":
            return False
        a, b_clause, groups, width, reps = expected_groups(proof_certificate)
        cert = result["certificate"]
        if cert["kind"] != "FUSED_NEGATIVE_SUFFIX":
            return False
        start = int(cert["start_group"])
        boundary = tuple(int(v) for v in cert["boundary"])
        if boundary != tuple(reps[start:]) or len(boundary) not in (1,2):
            return False
        node_index = int(cert["proof_node"])
        nodes = proof_certificate["nodes"]
        if norm_clause(nodes[node_index]["clause"]) != norm_clause(cert["suffix_clause"]):
            return False
        if norm_clause(cert["suffix_clause"]) != norm_clause(b_clause[start:]):
            return False
        memo, leaves = {}, {}
        replay(nodes,node_index,memo,leaves)
        current=node_index; pivots=[]; roots=[]
        for group in range(start-1,-1,-1):
            row=nodes[current]
            if "part" in row or int(row["pivot"]) != group*width:
                return False
            right=int(row["right"])
            if norm_clause(nodes[right]["clause"]) != (group*width+1,):
                return False
            expected={("A",a[group*width+offset]) for offset in range(width)}
            if leaf_clauses(nodes,right) != expected:
                return False
            pivots.append(int(row["pivot"])); roots.append(right); current=int(row["left"])
        if nodes[current].get("part") != "B" or norm_clause(nodes[current]["clause"]) != b_clause:
            return False
        if list(reversed(pivots)) != list(cert["chain_pivots"]):
            return False
        if list(reversed(roots)) != list(cert["unit_roots"]):
            return False
        bits,candidate=relation(boundary)
        if not extension_argument_holds(a,b_clause,start,width,boundary,bits):
            return False
        if list(result["relation_bits"]) != list(bits) or result["candidate"] != candidate:
            return False
        if int(result["local_count"]) != start*width:
            return False
        if int(result["discovery_work"]) != len(memo) or int(cert["reachable_nodes_checked"]) != len(memo):
            return False
        if cert["extension_schema"] != "set every variable in groups before start_group to true":
            return False
        if "prefix A groups force" not in cert["projection_argument"]:
            return False
        return True
    except (KeyError,TypeError,ValueError,IndexError,AssertionError,RecursionError):
        return False


def mutate_and_reject(proof_certificate, result):
    import copy
    forged=copy.deepcopy(result)
    forged["candidate"]["bound"]=0
    return not verify_suffix_result(proof_certificate,forged)


if __name__ == "__main__":
    import copy
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parent
    artifact=json.loads((root/"SYMBOLIC_SUFFIX_TEMPLATE.json").read_text(encoding="utf-8"))
    assert artifact["all_checks_passed"]
    for row in artifact["rows"]:
        assert verify_suffix_result(artifact["proof_certificate"],row)
    forged=copy.deepcopy(artifact["rows"][0]); forged["candidate"]["bound"]=0
    near=copy.deepcopy(artifact["proof_certificate"]); near["nodes"][62]["clause"]= [-25,-28]
    assert not verify_suffix_result(artifact["proof_certificate"],forged)
    assert artifact["adversarial"]=={"forged_certificate_rejected":True,"near_miss_rejected":True}
    for row in artifact["parameter_sweep"]:
        groups=int(row["groups"]); width=int(row["width"])
        assert row["proof_nodes"]==2*groups*width+1
        assert row["two_boundary_work"]==row["expected_two_boundary_work"]==2*width*(groups-2)+1
        assert row["one_boundary_work"]==row["expected_one_boundary_work"]==2*width*(groups-1)+1
        assert row["two_local_count"]==width*(groups-2) and row["one_local_count"]==width*(groups-1)
    print(json.dumps({"independent_checks_passed":True,"small_rows":len(artifact["rows"]),"scale_nodes":artifact["scale_summary"]["proof_nodes"],"scale_rows":len(artifact["scale_summary"]["rows"]),"sweep_rows":len(artifact["parameter_sweep"])}))
