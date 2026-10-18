"""A source-bound barrier for exact existential projection discovery.

Given arbitrary CNF G(y), form F(z,y)=G(y) AND NOT z and project the
remaining variables y away.  The one-bit relation is [1,0] exactly when G is
satisfiable and [0,0] exactly when G is unsatisfiable.  Thus an exact universal
projection classifier, even one restricted to deciding emptiness, would solve
SAT (and its complement) in polynomial time.
"""
from __future__ import annotations
from itertools import product
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def normalize_clause(clause):
    values=tuple(sorted(set(int(x) for x in clause),key=lambda z:(abs(z),z<0)))
    if any(-value in values for value in values):
        return None
    return values


def normalize_formula(clauses):
    out=[]; seen=set()
    for clause in clauses:
        normalized=normalize_clause(clause)
        if normalized is None:
            return None
        if normalized not in seen:
            seen.add(normalized); out.append(normalized)
    return tuple(sorted(out))


def cnf_sat(clauses,assignment):
    return all(any((assignment[abs(lit)-1] if lit>0 else not assignment[abs(lit)-1]) for lit in clause)
               for clause in clauses)


def all_non_tautological_clauses(nvars):
    pool=[]
    for choices in product((-1,0,1),repeat=nvars):
        if all(choice==0 for choice in choices):
            continue
        pool.append(tuple((index+1)*choice for index,choice in enumerate(choices) if choice))
    return tuple(pool)


def shift_formula(g_clauses):
    return tuple(tuple(lit+1 if lit>0 else lit-1 for lit in clause) for clause in g_clauses)


def lifted_formula(g_clauses):
    return shift_formula(g_clauses)+((-1,),)


def projected_relation(g_clauses,nvars):
    normalized=normalize_formula(g_clauses)
    if normalized is None:
        raise ValueError("tautological clause is outside the fixture language")
    formula=lifted_formula(normalized)
    bits=[]
    for z in (False,True):
        found=False
        for y in product((False,True),repeat=nvars):
            assignment=(z,)+y
            if cnf_sat(formula,assignment):
                found=True; break
        bits.append(int(found))
    return tuple(bits)


def classify_relation(bits):
    bits=tuple(int(value) for value in bits)
    if bits==(1,0):
        return "UNIT_Z_FALSE"
    if bits==(0,0):
        return "EMPTY"
    return "OTHER"


def exact_record(g_clauses,nvars):
    normalized=normalize_formula(g_clauses)
    if normalized is None:
        raise ValueError("tautological clause")
    models=[bits for bits in product((False,True),repeat=nvars) if cnf_sat(normalized,bits)]
    relation=projected_relation(normalized,nvars)
    return {"nvars":int(nvars),"g_clauses":[list(c) for c in normalized],"g_satisfiable":bool(models),"g_model_count":len(models),"boundary_width":1,"projection_bits":list(relation),"relation_class":classify_relation(relation),"lifted_clauses":[list(c) for c in lifted_formula(normalized)]}


def exhaustive_small_records(nvars=2):
    pool=all_non_tautological_clauses(nvars); records=[]
    for selector in range(1<<len(pool)):
        clauses=tuple(pool[index] for index in range(len(pool)) if selector>>index&1)
        records.append(exact_record(clauses,nvars))
    return records


def verify_record(record):
    try:
        nvars=int(record["nvars"]); clauses=tuple(tuple(c) for c in record["g_clauses"])
        normalized=normalize_formula(clauses)
        if normalized is None or [list(c) for c in normalized]!=record["g_clauses"]:
            return False
        models=[bits for bits in product((False,True),repeat=nvars) if cnf_sat(normalized,bits)]
        relation=projected_relation(normalized,nvars)
        return (int(record["boundary_width"])==1 and bool(record["g_satisfiable"])==bool(models)
                and int(record["g_model_count"])==len(models)
                and list(relation)==list(record["projection_bits"])
                and record["relation_class"]==classify_relation(relation)
                and record["lifted_clauses"]==[list(c) for c in lifted_formula(normalized)])
    except (KeyError,TypeError,ValueError,IndexError):
        return False


def build_artifact():
    records=exhaustive_small_records(2)
    controls=[exact_record((),2),exact_record(((1,),(-1,)),1),exact_record(((1,2),(-1,2),(1,-2)),2)]
    assert all(verify_record(record) for record in records+controls)
    forged=dict(records[0]); forged["projection_bits"]=[0,0]
    return {"all_checks_passed":True,"theorem_construction":"F(z,y)=G(y) AND NOT z","boundary_width":1,"small_nvars":2,"small_formula_count":len(records),"satisfiable_count":sum(record["g_satisfiable"] for record in records),"unsatisfiable_count":sum(not record["g_satisfiable"] for record in records),"relation_class_counts":{"EMPTY":sum(record["relation_class"]=="EMPTY" for record in records),"UNIT_Z_FALSE":sum(record["relation_class"]=="UNIT_Z_FALSE" for record in records),"OTHER":sum(record["relation_class"]=="OTHER" for record in records)},"controls":controls,"records":records,"adversarial":{"forged_record_rejected":not verify_record(forged)}}


def write_artifact():
    artifact=build_artifact(); (ROOT/"PROJECTION_DISCOVERY_BARRIER.json").write_text(json.dumps(artifact,indent=2)+"\n",encoding="utf-8"); return artifact

if __name__=="__main__":
    print(json.dumps(write_artifact(),indent=2))
