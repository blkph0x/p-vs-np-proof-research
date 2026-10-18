"""Certified structural macro for a fused negative-clause suffix.

The rule recognizes one explicit proof family.  A fused proof has one Hall
clause plus representative-to-member implications per group, and one B clause
containing the negated representatives.  After resolving a prefix of positive
representative units into B, the remaining suffix projects exactly to the
negative clause on its boundary.  The verifier checks the serialized proof
DAG, the group leaf sets, and the extension witness schema; it never enumerates
all local assignments.
"""
from __future__ import annotations
from itertools import product


def norm_clause(clause):
    values = tuple(sorted(set(int(x) for x in clause), key=lambda z: (abs(z), z < 0)))
    if any(-value in values for value in values):
        raise ValueError("tautological clause")
    return values


def _resolve(left, right, pivot):
    left, right, pivot = set(left), set(right), int(pivot)
    if pivot in left and -pivot in right:
        return norm_clause((left - {pivot}) | (right - {-pivot}))
    if -pivot in left and pivot in right:
        return norm_clause((left - {-pivot}) | (right - {pivot}))
    raise ValueError("invalid resolution pivot")


def _expected_groups(certificate):
    a = [norm_clause(c) for c in certificate["A"]]
    b = [norm_clause(c) for c in certificate["B"]]
    if len(b) != 1 or not a:
        raise ValueError("expected one B clause and nonempty A")
    b_clause = b[0]
    if any(lit >= 0 for lit in b_clause) or len(set(b_clause)) != len(b_clause):
        raise ValueError("B is not a negative representative clause")
    groups = len(b_clause)
    if len(a) % groups:
        raise ValueError("A does not split into equal groups")
    width = len(a) // groups
    if width < 2:
        raise ValueError("group width is too small")
    reps = list(range(groups))
    expected_a = []
    for group in range(groups):
        representative = group * width + 1
        members = [representative + offset for offset in range(1, width)]
        expected_a.append(norm_clause([representative] + members))
        expected_a.extend(norm_clause([representative, -member]) for member in members)
    if set(a) != set(expected_a) or len(set(a)) != len(expected_a):
        raise ValueError("A is not the fused Hall-plus-implication family")
    expected_b = norm_clause([-(group * width + 1) for group in reps])
    if b_clause != expected_b:
        raise ValueError("B representatives do not match A groups")
    return a, b, groups, width, [group * width for group in reps]


def _replay_subtree(nodes, index, memo=None, leaves=None):
    if memo is None:
        memo = {}
    if leaves is None:
        leaves = {}
    index = int(index)
    if index in memo:
        return memo[index]
    if not 0 <= index < len(nodes):
        raise ValueError("node index out of range")
    row = nodes[index]
    clause = norm_clause(row["clause"])
    if "part" in row:
        if row["part"] not in ("A", "B"):
            raise ValueError("invalid leaf part")
        leaves.setdefault(index, (row["part"], clause))
    else:
        left = _replay_subtree(nodes, row["left"], memo, leaves)
        right = _replay_subtree(nodes, row["right"], memo, leaves)
        expected = _resolve(left, right, int(row["pivot"]) + 1)
        if clause != expected:
            raise ValueError("invalid resolution node")
    memo[index] = clause
    return clause


def _leaf_refs(nodes, root, memo):
    seen = set()
    refs = set()

    def visit(index):
        index = int(index)
        if index in seen:
            return
        seen.add(index)
        row = nodes[index]
        if "part" in row:
            refs.add((row["part"], norm_clause(row["clause"])))
            return
        visit(row["left"])
        visit(row["right"])

    visit(root)
    return refs, seen


def _suffix_boundary(b_clause, reps, node_clause, max_boundary):
    expected = norm_clause(node_clause)
    for start in range(len(reps)):
        suffix = norm_clause(b_clause[start:])
        if expected == suffix:
            boundary = tuple(reps[start:])
            if 1 <= len(boundary) <= int(max_boundary):
                return start, boundary
    return None


def _extension_argument_holds(a, b_clause, start, width, boundary, relation_bits):
    # For every accepted boundary row, the prefix-all-true assignment satisfies
    # all prefix A clauses and B. For every rejected row, the A pattern forces
    # each prefix representative true, while B is false when every suffix
    # representative is true; this is the exact two-sided projection argument.
    for bits, expected in zip(product((False, True), repeat=len(boundary)), relation_bits):
        assignment = {variable: False for clause in a for literal in clause for variable in (abs(literal),)}
        for variable in range(start * width):
            assignment[variable + 1] = True
        for variable, value in zip(boundary, bits):
            assignment[variable + 1] = bool(value)
        if expected:
            if not all(any((assignment[abs(lit)] if lit > 0 else not assignment[abs(lit)]) for lit in clause)
                       for clause in a[:start * width]):
                return False
            if not any(not assignment[abs(lit)] for lit in b_clause):
                return False
        else:
            if not all(bits):
                return False
            # Each prefix group has the Hall clause and all implications; a
            # satisfying assignment with representative false would force every
            # member false and violate Hall. Thus all prefix reps are true.
            for group in range(start):
                rep = group * width + 1
                hall = tuple(a[group * width])
                implications = a[group * width + 1:group * width + width]
                if not hall or not implications or rep not in hall:
                    return False
                if any(rep not in clause or -member not in clause for member, clause in
                       zip(range(rep + 1, rep + width), implications)):
                    return False
            if any(not assignment[abs(lit)] if lit < 0 else assignment[abs(lit)] for lit in b_clause):
                return False
    return True


def _relation_for(boundary):
    bits = tuple(int(not all(values)) for values in product((False, True), repeat=len(boundary)))
    if len(boundary) == 1:
        candidate = {"kind": "UNIT", "var": int(boundary[0]), "value": False}
    elif len(boundary) == 2:
        candidate = {"kind": "PB", "weights": {str(boundary[0]): 1, str(boundary[1]): 1}, "sense": "<=", "bound": 1}
    else:
        raise ValueError("unsupported suffix width")
    return bits, candidate


def recognize_suffix_macro(proof_certificate, node_index, max_boundary=2, _self_check=True):
    """Return a linear-size certificate for a recognized suffix, or UNKNOWN."""
    try:
        a, b, groups, width, reps = _expected_groups(proof_certificate)
        nodes = proof_certificate["nodes"]
        node_index = int(node_index)
        if not 0 <= node_index < len(nodes):
            raise ValueError("node index out of range")
        target = norm_clause(nodes[node_index]["clause"])
        start_boundary = _suffix_boundary(b[0], reps, target, max_boundary)
        if start_boundary is None:
            return {"status": "UNKNOWN", "reason": "target is not a bounded B suffix"}
        start, boundary = start_boundary
        if "part" in nodes[node_index]:
            return {"status": "UNKNOWN", "reason": "target is a leaf"}

        # Replaying only the reachable suffix sub-DAG validates every node the
        # macro relies on, while retaining a precise linear work count.
        memo, leaves = {}, {}
        _replay_subtree(nodes, node_index, memo, leaves)
        current = node_index
        chain_pivots = []
        unit_roots = []
        for expected_group in range(start - 1, -1, -1):
            row = nodes[current]
            if "part" in row:
                raise ValueError("suffix chain terminated too early")
            pivot = int(row["pivot"])
            expected_pivot = expected_group * width
            if pivot != expected_pivot:
                raise ValueError("suffix chain pivot mismatch")
            right = int(row["right"])
            if norm_clause(nodes[right]["clause"]) != (expected_pivot + 1,):
                raise ValueError("suffix unit root mismatch")
            refs, unit_seen = _leaf_refs(nodes, right, memo)
            expected_group_clauses = [a[expected_group * width + offset] for offset in range(width)]
            expected_refs = {("A", clause) for clause in expected_group_clauses}
            # Bind the unit to exactly one group rather than trusting a positive
            # unit label alone.
            if refs != expected_refs:
                raise ValueError("unit proof leaf set mismatch")
            unit_roots.append(right)
            chain_pivots.append(pivot)
            current = int(row["left"])
        if current < 0 or current >= len(nodes):
            raise ValueError("invalid B predecessor")
        if nodes[current].get("part") != "B" or norm_clause(nodes[current]["clause"]) != b[0]:
            raise ValueError("suffix chain does not reach B")

        relation_bits, candidate = _relation_for(boundary)
        if not _extension_argument_holds(a, b[0], start, width, boundary, relation_bits):
            raise ValueError("extension argument failed")
        checked_nodes = len(memo)
        certificate = {
            "kind": "FUSED_NEGATIVE_SUFFIX",
            "proof_node": node_index,
            "groups": groups,
            "width": width,
            "start_group": start,
            "boundary": list(boundary),
            "suffix_clause": list(target),
            "chain_pivots": list(reversed(chain_pivots)),
            "unit_roots": list(reversed(unit_roots)),
            "reachable_nodes_checked": checked_nodes,
            "extension_schema": "set every variable in groups before start_group to true",
            "projection_argument": "the prefix A groups force their representatives true; B then reduces to the suffix clause, and every satisfying boundary assignment extends by prefix-all-true",
        }
        result = {
            "status": "FOUND",
            "kind": "SUFFIX",
            "candidate": candidate,
            "relation_bits": list(relation_bits),
            "boundary": list(boundary),
            "local_count": start * width,
            "discovery_work": checked_nodes,
            "certificate": certificate,
        }
        if _self_check and not verify_suffix_result(proof_certificate, result):
            raise ValueError("generated suffix certificate failed self-check")
        return result
    except (KeyError, TypeError, ValueError, IndexError, AssertionError):
        return {"status": "UNKNOWN", "reason": "fused suffix pattern not found"}


def verify_suffix_result(proof_certificate, result):
    try:
        if result["status"] != "FOUND" or result["kind"] != "SUFFIX":
            return False
        cert = result["certificate"]
        if cert["kind"] != "FUSED_NEGATIVE_SUFFIX":
            return False
        a, b, groups, width, reps = _expected_groups(proof_certificate)
        if cert["groups"] != groups or cert["width"] != width:
            return False
        if int(cert["proof_node"]) != int(result["certificate"]["proof_node"]):
            return False
        target = norm_clause(proof_certificate["nodes"][int(cert["proof_node"])]["clause"])
        if target != norm_clause(cert["suffix_clause"]):
            return False
        start = int(cert["start_group"])
        boundary = tuple(int(v) for v in cert["boundary"])
        if boundary != tuple(reps[start:]) or len(boundary) not in (1, 2):
            return False
        bits, candidate = _relation_for(boundary)
        if not _extension_argument_holds(a, b[0], start, width, boundary, bits):
            return False
        if tuple(result["relation_bits"]) != bits or result["candidate"] != candidate:
            return False
        if result["local_count"] != start * width:
            return False
        if int(cert["reachable_nodes_checked"]) != int(result["discovery_work"]):
            return False
        # Re-run the structural walk and require its counts and suffix identity.
        replayed = recognize_suffix_macro(proof_certificate, int(cert["proof_node"]), max_boundary=2, _self_check=False)
        if replayed["status"] != "FOUND":
            return False
        generated = replayed["certificate"]
        for key in ("groups", "width", "start_group", "boundary", "suffix_clause", "chain_pivots", "unit_roots"):
            if generated[key] != cert[key]:
                return False
        return True
    except (KeyError, TypeError, ValueError, IndexError, AssertionError, RecursionError):
        return False


def build_artifact():
    from pathlib import Path
    import sys
    root=Path(__file__).resolve().parent
    proof_dir=root / "proof_portfolio_integration_lab"
    if str(proof_dir) not in sys.path:
        sys.path.insert(0,str(proof_dir))
    import proof_engine
    import repeated_subdag_templates as templates
    small,small_root,_=proof_engine.build_fused_partitioned_proof(8,4)
    small_certificate=templates.serialize_proof(small)
    small_rows=[recognize_suffix_macro(small_certificate,index) | {"node_index":index} for index in (62,63)]
    assert all(row["status"]=="FOUND" and verify_suffix_result(small_certificate,row) for row in small_rows)
    scale,scale_root,_=proof_engine.build_fused_partitioned_proof(256,8)
    scale_certificate=templates.serialize_proof(scale)
    scale_rows=[recognize_suffix_macro(scale_certificate,index) | {"node_index":index} for index in (4094,4095)]
    assert all(row["status"]=="FOUND" and verify_suffix_result(scale_certificate,row) for row in scale_rows)
    sweep=[]
    for groups,width in [(4,2),(8,2),(16,2),(32,2),(64,2),(128,2),(256,2),(8,4),(16,4),(32,4),(64,4),(128,4),(256,4),(8,8),(16,8),(32,8),(64,8),(128,8),(256,8),(8,16),(16,16),(32,16),(64,16)]:
        proof,_,_=proof_engine.build_fused_partitioned_proof(groups,width)
        certificate=templates.serialize_proof(proof)
        two=recognize_suffix_macro(certificate,len(proof.nodes)-3)
        one=recognize_suffix_macro(certificate,len(proof.nodes)-2)
        assert two["status"]=="FOUND" and one["status"]=="FOUND"
        assert verify_suffix_result(certificate,two) and verify_suffix_result(certificate,one)
        sweep.append({"groups":groups,"width":width,"proof_nodes":len(proof.nodes),"two_boundary_work":two["discovery_work"],"one_boundary_work":one["discovery_work"],"two_local_count":two["local_count"],"one_local_count":one["local_count"],"expected_two_boundary_work":2*width*(groups-2)+1,"expected_one_boundary_work":2*width*(groups-1)+1})
    forged=__import__("copy").deepcopy(small_rows[0]); forged["candidate"]["bound"]=0
    near=__import__("copy").deepcopy(small_certificate); near["nodes"][62]["clause"]=[-25,-28]
    artifact={"all_checks_passed":True,"parameters":{"small_groups":8,"small_width":4,"max_boundary":2},"proof_nodes":len(small.nodes),"proof_root":small_root,"proof_certificate":small_certificate,"rows":small_rows,"scale_summary":{"groups":256,"width":8,"proof_nodes":len(scale.nodes),"proof_root":scale_root,"rows":scale_rows},"parameter_sweep":sweep,"adversarial":{"forged_certificate_rejected":not verify_suffix_result(small_certificate,forged),"near_miss_rejected":recognize_suffix_macro(near,62)["status"]=="UNKNOWN"}}
    assert all(artifact["adversarial"].values())
    return artifact


def write_artifact():
    import json
    from pathlib import Path
    artifact=build_artifact()
    (Path(__file__).resolve().parent/"SYMBOLIC_SUFFIX_TEMPLATE.json").write_text(json.dumps(artifact,indent=2)+"\n",encoding="utf-8")
    return artifact

if __name__=="__main__":
    import json
    print(json.dumps(write_artifact(),indent=2))
