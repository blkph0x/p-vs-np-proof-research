"""Fail-closed structural XOR-chain recovery without projected truth tables.

The work field counts named loop visits and substitutions, including failed
scans. It excludes sorting, hashing, allocation and integer bit costs; it is
an auditable logical-operation proxy, not measured CPU or a lower bound.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineResult:
    status: str
    support: tuple[int, ...] = ()
    rhs: int = 0
    work: int = 0
    gadget_count: int = 0


def _validated_input(clauses, shared):
    if not isinstance(clauses, (tuple, list)) or not isinstance(shared, (tuple, list)):
        raise ValueError('clauses and shared must be finite lists or tuples')
    seen=set();work=0
    for variable in shared:
        work+=1
        if type(variable) is not int or variable<0 or variable in seen:
            raise ValueError('shared IDs must be distinct nonnegative exact integers')
        seen.add(variable)
    normalised=set()
    for clause in clauses:
        work+=1
        if not isinstance(clause,(tuple,list)):
            raise ValueError('each clause must be a list or tuple')
        literals=set()
        for literal in clause:
            work+=1
            if type(literal) is not int or literal==0:
                raise ValueError('literals must be nonzero exact integers')
            literals.add(literal)
        tautological=False
        for literal in literals:
            work+=1
            if -literal in literals:tautological=True
        if not tautological:
            normalised.add(tuple(sorted(literals,key=lambda x:(abs(x),x))))
    return normalised,work


def _xor_truth_check(clauses, support):
    """Full eight-word check, with no short-circuit literal scans."""
    valid=True;work=0
    for mask in range(8):
        work+=1+len(support)
        assignment={variable:bool(mask & (1<<i)) for i,variable in enumerate(support)}
        satisfied=True
        for clause in clauses:
            work+=1;clause_satisfied=False
            for literal in clause:
                work+=1
                value=assignment[abs(literal)-1]
                clause_satisfied |= value if literal>0 else not value
            satisfied &= clause_satisfied
        expected=(mask.bit_count()%2==0)
        valid &= satisfied==expected
    return valid,work


def recover_xor_relation(clauses: tuple[tuple[int, ...], ...],
                         shared: tuple[int, ...]) -> BaselineResult:
    """Return one exact projected equation, or UNKNOWN for unsupported CNF.

    Invalid literal/shared-ID encodings raise ValueError. Every nontrivial
    original clause must belong to a complete verified even-XOR triple or to
    the single distinct unit. Repetition and tautologies are harmless. Each
    gadget must introduce a previously unknown helper from two known affine
    expressions; otherwise this deliberately narrow recognizer returns UNKNOWN.
    support indexes positions in the supplied ordered shared list. The legacy
    EXACT_AFFINE status means an exact XOR equation, not a nonempty affine
    coset: empty support with rhs=0 is universal; with rhs=1 it is empty.
    """
    normalised,work=_validated_input(clauses,shared)
    groups={};units=[];unsupported=False
    for clause in sorted(normalised):
        work+=1+len(clause)
        if len(clause)==1:
            literal=clause[0]
            units.append((abs(literal)-1,int(literal>0)))
        elif len(clause)==3:
            support=tuple(sorted(abs(literal)-1 for literal in clause))
            groups.setdefault(support,set()).add(clause)
        else:
            unsupported=True
    equations=[]
    for support,group in sorted(groups.items()):
        work+=1
        if len(group)!=4:
            unsupported=True
            continue
        valid,checked_work=_xor_truth_check(sorted(group),support)
        work+=checked_work
        if valid:equations.append(support)
        else:unsupported=True
    def unknown():
        return BaselineResult('UNKNOWN',work=work,gadget_count=len(equations))
    if unsupported or len(units)!=1:return unknown()
    target,target_value=units[0]
    expressions={}
    for index,variable in enumerate(shared):
        work+=1
        expressions[variable]=(1<<index,0)
    remaining=list(equations)
    while remaining:
        work+=1;next_remaining=[];progress=False
        for equation in remaining:
            work+=1;known=[];unknown_variables=[]
            for variable in equation:
                work+=1
                (known if variable in expressions else unknown_variables).append(variable)
            if len(known)==2 and len(unknown_variables)==1:
                left,lo=expressions[known[0]];right,ro=expressions[known[1]]
                expressions[unknown_variables[0]]=(left^right,lo^ro)
                work+=1;progress=True
            else:next_remaining.append(equation)
        remaining=next_remaining
        if not progress:return unknown()
    if target not in expressions:return unknown()
    mask,offset=expressions[target]
    support=[]
    for index in range(len(shared)):
        work+=1
        if mask & (1<<index):support.append(index)
    return BaselineResult('EXACT_AFFINE',tuple(support),target_value^offset,work,len(equations))


def expected_even_parity(shared: tuple[int, ...]) -> BaselineResult:
    _validated_input((),shared)
    return BaselineResult('EXACT_AFFINE',support=tuple(range(len(shared))),rhs=0)
