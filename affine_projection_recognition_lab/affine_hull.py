"""Affine hull discovery using the existing proof-producing CDCL backend.

Only decision and query counts are capped during solving. Input-size limits
bound the admitted variable/clause counts; they are not wall-clock, literal-
scan, proof-size or memory caps. solver_totals contains reported native counters.
EXACT_HULL describes the affine hull, not affinity of the projected relation.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


BACKEND_PATH=(Path(__file__).resolve().parent.parent/'proof_producing_cdcl_lab'/'cdcl.py').resolve()
BACKEND_NAME='_affine_projection_hull_native_cdcl_v1'
STAT_KEYS=('decisions','boolean_props','conflicts','learned_clauses',
           'learned_literals','resolution_steps','backjumps')


def _backend():
    existing=sys.modules.get(BACKEND_NAME)
    if existing is not None:
        if Path(existing.__file__).resolve()!=BACKEND_PATH:
            raise RuntimeError('native CDCL module name is already bound to another file')
        return existing
    spec=importlib.util.spec_from_file_location(BACKEND_NAME,BACKEND_PATH)
    if spec is None or spec.loader is None:
        raise ImportError('cannot load the native CDCL source')
    module=importlib.util.module_from_spec(spec)
    sys.modules[BACKEND_NAME]=module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(BACKEND_NAME,None)
        raise
    return module


def _integer(value,name):
    if type(value) is not int or value<0:
        raise ValueError(name+' must be a nonnegative exact integer')
    return value


def _clauses(nvars,clauses):
    if not isinstance(clauses,(tuple,list)):
        raise ValueError('clauses must be a finite list or tuple')
    copied=[]
    for clause in clauses:
        if not isinstance(clause,(tuple,list)):
            raise ValueError('each clause must be a list or tuple')
        row=[]
        for literal in clause:
            if type(literal) is not int or literal==0 or abs(literal)>nvars:
                raise ValueError('literals must be exact nonzero integers in the declared range')
            row.append(literal)
        copied.append(row)
    return copied


def canonical_equations(m,points):
    """Return (equations,dimension) of the span of supplied visible masks.

    Pivots use increasing original bit positions. The equation for each free
    column uses that column plus the relevant pivot columns. Empty input has
    the explicit inconsistent equation 0=1 and dimension None.
    """
    _integer(m,'visible width')
    if not isinstance(points,(tuple,list)):
        raise ValueError('points must be a finite list or tuple')
    if any(type(point) is not int or point<0 or point.bit_length()>m for point in points):
        raise ValueError('points must be exact masks on visible coordinates')
    if not points:return [[0,1]],None
    anchor=points[0]
    rows=[point^anchor for point in points[1:] if point!=anchor]
    rank=0;pivots=[]
    for column in range(m):
        pivot=next((i for i in range(rank,len(rows)) if rows[i]>>column&1),None)
        if pivot is None:continue
        rows[rank],rows[pivot]=rows[pivot],rows[rank]
        for index in range(len(rows)):
            if index!=rank and rows[index]>>column&1:
                rows[index]^=rows[rank]
        pivots.append(column);rank+=1
    equations=[];pivot_set=set(pivots)
    for free in range(m):
        if free in pivot_set:continue
        normal=1<<free
        for row,pivot in zip(rows[:rank],pivots):
            if row>>free&1:normal^=1<<pivot
        equations.append([normal,(normal&anchor).bit_count()%2])
    return equations,rank


def compile_outside(nvars,clauses,equations):
    """Return (query_nvars, original_CNF AND outside(equations)).

    XOR chains use fresh auxiliary IDs, increasing row support bits and the
    four forbidden odd words 1,2,4,7. A final disjunction requires a violated
    row. The empty equation system gives an appended empty clause.
    """
    _integer(nvars,'variable count')
    result=_clauses(nvars,clauses)
    if not isinstance(equations,(tuple,list)):
        raise ValueError('equations must be a list or tuple')
    checked=[]
    for equation in equations:
        if not isinstance(equation,(tuple,list)) or len(equation)!=2:
            raise ValueError('each equation must be a mask/RHS pair')
        mask,rhs=equation
        if type(mask) is not int or mask<0 or mask.bit_length()>nvars or type(rhs) is not int or rhs not in (0,1):
            raise ValueError('invalid equation mask/RHS')
        checked.append((mask,rhs))
    if (0,1) in checked:
        return nvars,result
    next_variable=nvars;violations=[]
    for mask,rhs in checked:
        if not mask:continue
        support=[bit for bit in range(mask.bit_length()) if mask>>bit&1]
        accumulator=support[0]
        for variable in support[1:]:
            output=next_variable;next_variable+=1
            ports=(accumulator,variable,output)
            for word in (1,2,4,7):
                result.append([-(port+1) if word>>index&1 else port+1
                               for index,port in enumerate(ports)])
            accumulator=output
        violations.append(accumulator+1 if rhs==0 else -(accumulator+1))
    result.append(violations)
    return next_variable,result


def _model(nvars,clauses,raw):
    if not isinstance(raw,dict):
        raise RuntimeError('native SAT model is not a mapping')
    # Accept a JSON round trip, without coercing bool keys, values or aliases.
    if set(raw)==set(range(nvars)) and all(type(key) is int for key in raw):
        values=[raw[index] for index in range(nvars)]
    elif set(raw)=={str(index) for index in range(nvars)} and all(type(key) is str for key in raw):
        values=[raw[str(index)] for index in range(nvars)]
    else:
        raise RuntimeError('native SAT model has missing, extra or ambiguous IDs')
    if any(type(value) is not bool for value in values):
        raise RuntimeError('native SAT model values must be Boolean')
    if not all(any(values[abs(lit)-1]==(lit>0) for lit in clause) for clause in clauses):
        raise RuntimeError('native SAT model does not satisfy the complete query')
    return values


def recover(m,q,clauses,*,max_decisions=1000,max_calls=None,
            max_input_vars=64,max_input_clauses=4096):
    """Discover the exact affine hull of an existential CNF projection.

    Visible coordinates are 0..m-1, hidden coordinates m..m+q-1. Malformed
    inputs raise ValueError; resource exhaustion returns UNKNOWN with neither
    equations nor dimension. SAT witnesses are checked against every query
    clause. UNSAT claims retain their native proof for independent checking;
    this producer does not certify its own terminal proof.
    """
    for value,name in [(m,'visible width'),(q,'hidden width'),(max_decisions,'decision cap'),
                       (max_input_vars,'input variable cap'),(max_input_clauses,'input clause cap')]:
        _integer(value,name)
    if max_calls is None:max_calls=m+1
    _integer(max_calls,'call cap')
    nvars=m+q
    original=_clauses(nvars,clauses)
    source=dict(visible_width=m,hidden_width=q,clauses=original)
    queries=[];totals={key:0 for key in STAT_KEYS}
    def finish(status,equations=None,dimension=None,reason=None):
        return dict(source=source,status=status,equations=equations,dimension=dimension,
                    queries=queries,solver_totals=totals,reason=reason)
    if nvars>max_input_vars:return finish('UNKNOWN',reason='INPUT_VARIABLE_CAP')
    if len(original)>max_input_clauses:return finish('UNKNOWN',reason='INPUT_CLAUSE_CAP')
    backend=_backend();points=[];equations=None
    while True:
        if len(queries)>=max_calls:return finish('UNKNOWN',reason='CALL_CAP')
        if not points:
            query_nvars=nvars;query_clauses=[row[:] for row in original]
        else:
            query_nvars,query_clauses=compile_outside(nvars,original,equations)
        remaining=max_decisions-totals['decisions']
        result=backend.CDCL(query_nvars,query_clauses,max_decisions=remaining).solve()
        queries.append(dict(nvars=query_nvars,clauses=query_clauses,result=result))
        stats=result.get('stats')
        if not isinstance(stats,dict) or set(stats)!=set(STAT_KEYS) or any(type(stats[key]) is not int or stats[key]<0 for key in STAT_KEYS):
            raise RuntimeError('native solver reported malformed counters')
        if stats['decisions']>remaining:
            raise RuntimeError('native solver exceeded its decision cap')
        # Each decision increases the current level by one; every nonroot
        # conflict backjumps by >=1; a root conflict terminates this call.
        if stats['conflicts']>stats['decisions']+1:
            raise RuntimeError('native conflict/decision-level invariant failed')
        for key in STAT_KEYS:totals[key]+=stats[key]
        status=result.get('status')
        if status=='UNKNOWN':return finish('UNKNOWN',reason=result.get('reason','BACKEND_UNKNOWN'))
        if status=='UNSAT':
            if not points:return finish('EMPTY',equations=[[0,1]])
            equations,dimension=canonical_equations(m,points)
            return finish('EXACT_HULL',equations=equations,dimension=dimension)
        if status!='SAT':raise RuntimeError('native solver returned an invalid status')
        model=_model(query_nvars,query_clauses,result.get('model'))
        point=sum(int(model[index])<<index for index in range(m))
        if points and all((mask&point).bit_count()%2==rhs for mask,rhs in equations):
            raise RuntimeError('outside query returned a point inside the current hull')
        points.append(point)
        equations,dimension=canonical_equations(m,points)
        if dimension==m:
            return finish('EXACT_HULL',equations=equations,dimension=dimension)
