"""Certified narrow recognition of a disjoint signed affine partition.

The producer fits a common quadratic ANF by linear coefficient equations. The
checker instead evaluates the phase difference at weights zero, one and two in
each support's affine coordinates, and checks independent coverage witnesses.
No discovery of subgroups in an arbitrary sum is attempted.
"""
from fractions import Fraction
from hashlib import sha256
from itertools import combinations

LIMITS=dict(max_variables=256,max_pieces=128,max_rows=16384,max_terms=100000,
            max_pairs=8192,max_unknowns=40000,max_work=5000000,max_scalar_bits=65536)


class Exhausted(Exception):pass


class Meter:
    def __init__(self,caps):
        if set(caps)-set(LIMITS):raise ValueError('unknown cap')
        self.caps={**LIMITS,**caps}
        if any(type(x) is not int or x<0 for x in self.caps.values()):raise ValueError('caps must be nonnegative exact integers')
        self.stats=dict(work=0,pairs=0,fit_unknowns=0,fit_equations=0,fit_rank=0,
                        phase_samples=0,peak_scalar_bits=0)
    def tick(self,amount=1):
        self.stats['work']+=amount
        if self.stats['work']>self.caps['max_work']:raise Exhausted('work cap')
    def pair(self):
        self.stats['pairs']+=1
        if self.stats['pairs']>self.caps['max_pairs']:raise Exhausted('pair cap')
    def scalar(self,c):
        bits=max(abs(c.numerator).bit_length(),c.denominator.bit_length())
        self.stats['peak_scalar_bits']=max(bits,self.stats['peak_scalar_bits'])
        if bits>self.caps['max_scalar_bits']:raise Exhausted('scalar bit cap')
        return c


def typed_equal(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return set(a)==set(b) and all(typed_equal(a[k],b[k]) for k in a)
    if type(a) in (list,tuple):return len(a)==len(b) and all(typed_equal(x,y) for x,y in zip(a,b))
    return a==b


def digest(value):
    h=sha256(b'affine-partition-recognition-v1')
    def emit(x):
        if type(x) is int:
            data=abs(x).to_bytes(max(1,(abs(x).bit_length()+7)//8),'little')
            h.update(b'i'+bytes([x<0])+len(data).to_bytes(8,'little')+data)
        elif type(x) is bool:h.update(b't' if x else b'f')
        elif type(x) is str:
            data=x.encode();h.update(b's'+len(data).to_bytes(8,'little')+data)
        elif type(x) is list:
            h.update(b'l');emit(len(x))
            for y in x:emit(y)
        elif type(x) is dict:
            h.update(b'd');emit(len(x))
            for key in sorted(x):emit(key);emit(x[key])
        else:raise ValueError('unsupported hash field')
    emit(value);return h.hexdigest()


def rref(rows,ids,meter):
    """Column-ordered elimination, with a contradiction witness in input rows."""
    if len(rows)>meter.caps['max_rows']:raise Exhausted('support row cap')
    work=[[mask,rhs,1<<i] for i,(mask,rhs) in enumerate(rows)]
    rank=0
    for variable in ids:
        pivot=next((j for j in range(rank,len(work)) if work[j][0]>>variable&1),None)
        meter.tick(len(work)-rank)
        if pivot is None:continue
        work[rank],work[pivot]=work[pivot],work[rank]
        for j in range(len(work)):
            if j!=rank and work[j][0]>>variable&1:
                work[j]=[x^y for x,y in zip(work[j],work[rank])];meter.tick()
        rank+=1
    for mask,rhs,witness in work[rank:]:
        if not mask and rhs:return None,witness
    return [[mask,rhs] for mask,rhs,_ in work[:rank]],None


def parameter(rows,ids):
    pivots=[next(v for v in ids if mask>>v&1) for mask,_ in rows]
    free=[v for v in ids if v not in pivots]
    anchor=sum(rhs<<v for v,(_,rhs) in zip(pivots,rows))
    basis=[(1<<f)|sum(((mask>>f)&1)<<p for p,(mask,_) in zip(pivots,rows)) for f in free]
    return anchor,basis,free


def zero(n,ids):
    return dict(n=n,retained=list(ids),zero=True,equations=[],phase=[],scalar=[0,1],free_ids=[])


def parse_message(n,ids,message,meter):
    fields={'n','retained','zero','equations','phase','scalar','free_ids'}
    if type(message) is not dict or set(message)!=fields or type(message['n']) is not int or message['n']!=n or not typed_equal(message['retained'],ids) or type(message['zero']) is not bool:
        raise ValueError('wrong canonical message header')
    if any(type(message[k]) is not list for k in ('equations','phase','scalar','free_ids')):raise ValueError('explicit canonical message fields required')
    if len(message['scalar'])!=2 or any(type(x) is not int for x in message['scalar']) or message['scalar'][1]<=0:raise ValueError('invalid rational')
    c=meter.scalar(Fraction(*message['scalar']))
    if message['scalar']!=[c.numerator,c.denominator]:raise ValueError('noncanonical rational')
    if message['zero']:
        if not typed_equal(message,zero(n,ids)):raise ValueError('noncanonical zero')
        return None
    if not c:raise ValueError('nonzero message has zero coefficient')
    if len(message['equations'])>meter.caps['max_rows'] or len(message['phase'])>meter.caps['max_terms']:raise Exhausted('input row/term cap')
    allowed=sum(1<<v for v in ids)
    for row in message['equations']:
        if type(row) is not list or len(row)!=2 or any(type(x) is not int for x in row) or row[0]<0 or row[0]&~allowed or row[1] not in (0,1):raise ValueError('invalid support row')
    rows,bad=rref(message['equations'],ids,meter)
    if rows is None or not typed_equal(rows,message['equations']):raise ValueError('support is not nonempty canonical RREF')
    anchor,basis,free=parameter(rows,ids)
    if not typed_equal(message['free_ids'],free):raise ValueError('wrong free coordinates')
    free_mask=sum(1<<v for v in free)
    phase=message['phase']
    if any(type(t) is not int or t<=0 or t&~free_mask or t.bit_count()>2 for t in phase) or phase!=sorted(set(phase)):raise ValueError('noncanonical quadratic phase')
    meter.tick(len(phase)+len(rows)+len(ids))
    return dict(anchor=anchor,basis=basis,free=free,scalar=c)


def request(n,retained,messages,meter):
    if type(n) is not int or n<0:raise ValueError('invalid dimension')
    if n>meter.caps['max_variables']:raise Exhausted('coordinate cap')
    if type(retained) not in (list,tuple) or any(type(v) is not int or not 0<=v<n for v in retained) or len(set(retained))!=len(retained):raise ValueError('invalid retained coordinates')
    ids=list(retained)
    if type(messages) not in (list,tuple):raise ValueError('explicit input list required')
    if len(messages)>meter.caps['max_pieces']:raise Exhausted('piece cap')
    originals=list(messages)
    parsed=[parse_message(n,ids,m,meter) for m in originals]
    return ids,originals,parsed,digest(dict(n=n,retained=ids,messages=originals))


def generators(parsed,active):
    anchor=parsed[active[0]]['anchor']
    return anchor,[v for i in active for v in [parsed[i]['anchor']^anchor]+parsed[i]['basis']]


def hull(parsed,active,ids,meter):
    anchor,directions=generators(parsed,active)
    direction_rows,_=rref([[v,0] for v in directions],ids,meter)
    _,annihilator,_=parameter(direction_rows,ids)
    equations,_=rref([[v,(v&anchor).bit_count()%2] for v in annihilator],ids,meter)
    return equations


def toggle(poly,term):
    if term in poly:poly.remove(term)
    else:poly.add(term)


def restrict_term(term,expressions,meter):
    """Producer's polynomial substitution into one support's free variables."""
    polynomial={0}
    while term:
        bit=term&-term;term^=bit
        replacement=expressions[bit]
        following=set()
        for a in polynomial:
            for b in replacement:toggle(following,a|b);meter.tick()
        if len(following)>meter.caps['max_terms']:raise Exhausted('restricted phase term cap')
        polynomial=following
    return polynomial


def fit_phase(equations,ids,originals,parsed,active,meter):
    _,_,free=parameter(equations,ids)
    dimension=len(free)
    unknowns=1+dimension+dimension*(dimension-1)//2
    if unknowns>meter.caps['max_unknowns']:raise Exhausted('quadratic unknown cap')
    terms=[0]+[1<<v for v in free]+[(1<<a)|(1<<b) for a,b in combinations(free,2)]
    meter.stats['fit_unknowns']=len(terms)
    # Stream coefficient equations into a highest-pivot row basis instead of
    # retaining the complete k-times-quadratic constraint matrix.
    basis={}
    for i in active:
        p=parsed[i];expressions={}
        for v in free:
            expression={1<<f for f,direction in zip(p['free'],p['basis']) if direction>>v&1}
            if p['anchor']>>v&1:expression.add(0)
            expressions[1<<v]=expression;meter.tick(len(p['basis'])+1)
        coefficient_rows={}
        for column,term in enumerate(terms):
            for monomial in restrict_term(term,expressions,meter):
                coefficient_rows[monomial]=coefficient_rows.get(monomial,0)^(1<<column)
        target=set(originals[i]['phase'])
        if parsed[i]['scalar']<0:target.add(0)
        for monomial in sorted(set(coefficient_rows)|target):
            mask=coefficient_rows.get(monomial,0);rhs=int(monomial in target)
            meter.stats['fit_equations']+=1
            meter.tick()
            while mask:
                pivot=mask.bit_length()-1;meter.tick()
                if pivot in basis:
                    other,value=basis[pivot];mask^=other;rhs^=value
                else:
                    basis[pivot]=(mask,rhs)
                    meter.stats['fit_rank']=len(basis)
                    break
            if not mask and rhs:return None
    meter.stats['fit_rank']=len(basis)
    if len(basis)!=len(terms):raise ArithmeticError('full partition must determine its quadratic uniquely')
    solution=0
    for pivot in sorted(basis):
        mask,rhs=basis[pivot]
        value=rhs^((mask&solution).bit_count()%2)
        if value:solution|=1<<pivot
        meter.tick()
    return terms,solution


def recognize(n,retained,messages,**caps):
    meter=Meter(caps)
    try:
        ids,originals,parsed,binding=request(n,retained,messages,meter)
        active=[i for i,p in enumerate(parsed) if p is not None]
        if not active:
            cert=dict(kind='zero-partition-v1',input_sha256=binding,active_indices=[])
            return dict(status='EXACT',message=zero(n,ids),certificate=cert,stats=meter.stats)
        magnitude=abs(parsed[active[0]]['scalar'])
        if any(abs(parsed[i]['scalar'])!=magnitude for i in active):
            return dict(status='UNSUPPORTED',message=None,certificate=None,reason='unequal magnitudes',stats=meter.stats)
        intersections=[]
        for i,j in combinations(active,2):
            meter.pair()
            rows=originals[i]['equations']+originals[j]['equations']
            _,witness=rref(rows,ids,meter)
            if witness is None:
                return dict(status='UNSUPPORTED',message=None,certificate=None,reason='overlapping supports',stats=meter.stats)
            intersections.append(dict(pair=[i,j],contradiction=witness))
        equations=hull(parsed,active,ids,meter)
        _,_,free=parameter(equations,ids)
        cardinality=sum(1<<len(parsed[i]['free']) for i in active)
        if cardinality!=(1<<len(free)):
            return dict(status='UNSUPPORTED',message=None,certificate=None,reason='gap in affine hull',stats=meter.stats)
        fitted=fit_phase(equations,ids,originals,parsed,active,meter)
        if fitted is None:
            return dict(status='UNSUPPORTED',message=None,certificate=None,reason='incompatible quadratic phase',stats=meter.stats)
        terms,solution=fitted
        scalar=-magnitude if solution&1 else magnitude
        phase=sorted(terms[i] for i in range(1,len(terms)) if solution>>i&1)
        if len(phase)>meter.caps['max_terms']:raise Exhausted('output phase term cap')
        output=dict(n=n,retained=ids,zero=False,equations=equations,phase=phase,
                    scalar=[scalar.numerator,scalar.denominator],free_ids=free)
        cert=dict(kind='affine-partition-v1',input_sha256=binding,active_indices=active,
                  intersections=intersections,support_dimensions=[len(parsed[i]['free']) for i in active],
                  hull_dimension=len(free),coverage_cardinality=cardinality)
        return dict(status='EXACT',message=output,certificate=cert,stats=meter.stats)
    except Exhausted as error:
        return dict(status='UNKNOWN',message=None,certificate=None,reason=str(error),stats=meter.stats)


def xor_rank(vectors,meter):
    """Verifier rank via a dictionary of highest leading bits."""
    basis={}
    for value in vectors:
        while value:
            p=value.bit_length()-1;meter.tick()
            if p in basis:value^=basis[p]
            else:basis[p]=value;break
    return len(basis)


def phase_value(phase,word,meter):
    meter.tick(len(phase))
    return sum((word&term)==term for term in phase)%2


def verify_partition(n,retained,messages,result,**caps):
    meter=Meter(caps)
    try:
        ids,originals,parsed,binding=request(n,retained,messages,meter)
        if type(result) is not dict or result.get('status')!='EXACT' or type(result.get('certificate')) is not dict:raise ValueError('expected exact result')
        cert=result['certificate'];active=[i for i,p in enumerate(parsed) if p is not None]
        if cert.get('input_sha256')!=binding or not typed_equal(cert.get('active_indices'),active):raise ValueError('wrong complete external input binding')
        if not active:
            if set(cert)!={'kind','input_sha256','active_indices'} or cert['kind']!='zero-partition-v1' or not typed_equal(result.get('message'),zero(n,ids)):raise ValueError('wrong zero result')
            return dict(valid=True,status='VERIFIED',message=zero(n,ids),stats=meter.stats)
        fields={'kind','input_sha256','active_indices','intersections','support_dimensions','hull_dimension','coverage_cardinality'}
        if set(cert)!=fields or cert['kind']!='affine-partition-v1':raise ValueError('wrong certificate format')
        output=result.get('message');out=parse_message(n,ids,output,meter)
        if out is None:raise ValueError('nonempty partition cannot produce zero')
        magnitude=abs(parsed[active[0]]['scalar'])
        if abs(out['scalar'])!=magnitude or any(abs(parsed[i]['scalar'])!=magnitude for i in active):raise ValueError('unequal magnitudes')
        pairs=list(combinations(active,2))
        if type(cert['intersections']) is not list or len(cert['intersections'])!=len(pairs):raise ValueError('incomplete pair coverage')
        for (i,j),entry in zip(pairs,cert['intersections']):
            meter.pair()
            if type(entry) is not dict or set(entry)!={'pair','contradiction'} or not typed_equal(entry['pair'],[i,j]):raise ValueError('wrong intersection pair')
            rows=originals[i]['equations']+originals[j]['equations'];witness=entry['contradiction']
            if type(witness) is not int or witness<=0 or witness.bit_length()>len(rows):raise ValueError('invalid contradiction selector')
            mask=rhs=0
            for k,(row,value) in enumerate(rows):
                if witness>>k&1:mask^=row;rhs^=value
                meter.tick()
            if mask or rhs!=1:raise ValueError('supports not certified disjoint')
        dimensions=[len(parsed[i]['free']) for i in active]
        dimension=len(out['free']);cardinality=sum(1<<d for d in dimensions)
        if not typed_equal(cert['support_dimensions'],dimensions) or type(cert['hull_dimension']) is not int or cert['hull_dimension']!=dimension or type(cert['coverage_cardinality']) is not int or cert['coverage_cardinality']!=cardinality or cardinality!=(1<<dimension):raise ValueError('wrong cardinality coverage')
        anchor,directions=generators(parsed,active)
        if xor_rank(directions,meter)!=dimension:raise ValueError('proposed support is not the affine hull')
        for i in active:
            p=parsed[i]
            for mask,rhs in output['equations']:
                if (mask&p['anchor']).bit_count()%2!=rhs or any((mask&v).bit_count()%2 for v in p['basis']):raise ValueError('input support escapes hull')
                meter.tick(len(p['basis'])+1)
            # A quadratic in support coordinates is determined by these
            # 1+d+binom(d,2) values; no coefficient fitting is rerun.
            samples=[p['anchor']]+[p['anchor']^v for v in p['basis']]
            samples += [p['anchor']^a^b for a,b in combinations(p['basis'],2)]
            target_sign=int(p['scalar']!=out['scalar'])
            for word in samples:
                meter.stats['phase_samples']+=1
                if phase_value(output['phase'],word,meter)^phase_value(originals[i]['phase'],word,meter)!=target_sign:raise ValueError('phase mismatch on input support')
        return dict(valid=True,status='VERIFIED',message=output,stats=meter.stats)
    except Exhausted as error:
        return dict(valid=False,status='UNKNOWN',message=None,reason=str(error),stats=meter.stats)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,OverflowError) as error:
        return dict(valid=False,status='INVALID',message=None,reason=str(error),stats=meter.stats)


compress_partition=recognize
