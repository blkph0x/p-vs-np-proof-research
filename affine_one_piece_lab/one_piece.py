"""Complete bounded recognition of one real affine-quadratic explicit sum.

Discovery uses exact restricted squared norms. The checker verifies retained
support witnesses, outside-zero norms and either equality or a complete
one-piece obstruction, without repeating the discovery search.
"""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import importlib.util
import sys

NIGHT=Path(__file__).resolve().parent.parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module


partition=load('_one_piece_partition',NIGHT/'affine_partition_compression_lab'/'partition.py')
block=load('_one_piece_block',NIGHT/'affine_boundary_reference'/'reference.py')
LIMITS=dict(max_variables=256,max_pieces=128,max_rows=16384,max_terms=100000,
            max_scalar_bits=65536,max_work=20000000,max_norm_queries=10000,
            max_pair_contractions=200000,max_point_evaluations=100000,
            max_certificate_products=100000)


class Exhausted(Exception):pass


class Budget:
    def __init__(self,caps):
        if set(caps)-set(LIMITS):raise ValueError('unknown cap')
        self.caps={**LIMITS,**caps}
        if any(type(v) is not int or v<0 for v in self.caps.values()):raise ValueError('caps must be nonnegative exact integers')
        self.stats=dict(work=0,norm_queries=0,pair_contractions=0,point_evaluations=0,
          peak_scalar_bits=0,certificate_products=0,hull_augmentations=0,fast_candidates=0)
    def tick(self,amount=1):
        self.stats['work']+=amount
        if self.stats['work']>self.caps['max_work']:raise Exhausted('work cap')
    def reserve(self,key,cap):
        self.stats[key]+=1
        if self.stats[key]>self.caps[cap]:raise Exhausted(cap)
    def rational(self,c):
        bits=max(abs(c.numerator).bit_length(),c.denominator.bit_length())
        self.stats['peak_scalar_bits']=max(bits,self.stats['peak_scalar_bits'])
        if bits>self.caps['max_scalar_bits']:raise Exhausted('rational bit cap')
        self.tick();return c
    def support_meter(self):
        keys=('max_variables','max_pieces','max_rows','max_terms','max_scalar_bits')
        return partition.Meter({k:self.caps[k] for k in keys}|{'max_work':max(0,self.caps['max_work']-self.stats['work'])})
    def charge_support(self,meter):
        self.stats['peak_scalar_bits']=max(self.stats['peak_scalar_bits'],meter.stats['peak_scalar_bits'])
        self.tick(meter.stats['work'])
    def block_caps(self):
        return {k:self.caps[k] for k in ('max_variables','max_rows','max_terms','max_scalar_bits')}|{
              'max_work':max(0,self.caps['max_work']-self.stats['work']),
              'max_steps':self.caps['max_variables']}


def pair(c):return [c.numerator,c.denominator]


def read_ratio(value):
    if type(value) is not list or len(value)!=2 or any(type(v) is not int for v in value) or value[1]<=0:raise ValueError('invalid rational field')
    c=Fraction(*value)
    if value!=pair(c):raise ValueError('noncanonical rational field')
    return c


def request(n,retained,messages,budget):
    meter=budget.support_meter()
    try:ids,originals,parsed,_=partition.request(n,retained,messages,meter)
    finally:budget.charge_support(meter)
    binding=partition.digest(dict(format='explicit-one-piece-v1',n=n,retained=ids,messages=originals))
    return ids,originals,parsed,binding


def parse(n,ids,message,budget):
    meter=budget.support_meter()
    try:return partition.parse_message(n,ids,message,meter)
    finally:budget.charge_support(meter)


def point_value(messages,word,budget):
    budget.reserve('point_evaluations','max_point_evaluations')
    result=Fraction(0)
    for message in messages:
        if message['zero']:continue
        budget.tick(len(message['equations'])+len(message['phase'])+1)
        if any((word&mask).bit_count()%2!=rhs for mask,rhs in message['equations']):continue
        sign=sum((word&t)==t for t in message['phase'])%2
        c=read_ratio(message['scalar'])*(-1 if sign else 1)
        result=budget.rational(result+c)
    return result


def closed_value(message,budget):
    # The independent block verifier permits equivalent noncanonical phases.
    # Evaluate the actual zero-coordinate function, not just its scalar.
    if message['zero']:return Fraction(0)
    sign=sum(t==0 for t in message['phase'])%2
    return budget.rational(read_ratio(message['scalar'])*(-1 if sign else 1))


class Norms:
    def __init__(self,n,ids,originals,budget):
        self.n=n;self.ids=ids;self.originals=originals;self.budget=budget
    def operands(self,candidate):
        result=[(i,m,1) for i,m in enumerate(self.originals) if not m['zero']]
        if candidate is not None and not candidate['zero']:
            result.append((len(self.originals),candidate,-1))
        return result
    def product_request(self,a,b,restriction,double):
        _,left,sa=a;_,right,sb=b
        c=self.budget.rational(read_ratio(left['scalar'])*read_ratio(right['scalar'])*sa*sb*(2 if double else 1))
        return dict(n=self.n,retained=[],active=self.ids,
              equations=left['equations']+right['equations']+restriction,
              phase=left['phase']+right['phase'],scalar=pair(c))
    def query(self,restriction,candidate=None):
        self.budget.reserve('norm_queries','max_norm_queries')
        operands=self.operands(candidate);products=[];total=Fraction(0)
        if len(operands)*(len(operands)+1)//2>self.budget.caps['max_certificate_products']:raise Exhausted('single norm proof product cap')
        for i,a in enumerate(operands):
            for j in range(i,len(operands)):
                self.budget.reserve('pair_contractions','max_pair_contractions')
                b=operands[j];request=self.product_request(a,b,restriction,i!=j)
                result=block.marginalize_reference(**request,**self.budget.block_caps())
                self.budget.tick(result['stats']['work'])
                if result['status']=='UNKNOWN':raise Exhausted('block contraction cap')
                total=self.budget.rational(total+closed_value(result['message'],self.budget))
                products.append(dict(pair=[a[0],b[0]],result=result))
        if total<0:raise ArithmeticError('negative exact squared norm')
        return dict(format='restricted-square-norm-v1',restriction=deepcopy(restriction),
             operand_indices=[a[0] for a in operands],products=products,value=pair(total))
    def check(self,restriction,proof,candidate=None):
        self.budget.reserve('norm_queries','max_norm_queries')
        fields={'format','restriction','operand_indices','products','value'}
        operands=self.operands(candidate);count=len(operands)*(len(operands)+1)//2
        if type(proof) is not dict or set(proof)!=fields or proof['format']!='restricted-square-norm-v1' or not partition.typed_equal(proof['restriction'],restriction) or not partition.typed_equal(proof['operand_indices'],[a[0] for a in operands]) or type(proof['products']) is not list or len(proof['products'])!=count:raise ValueError('invalid complete norm product coverage')
        total=Fraction(0);position=0
        for i,a in enumerate(operands):
            for j in range(i,len(operands)):
                self.budget.reserve('pair_contractions','max_pair_contractions')
                b=operands[j];entry=proof['products'][position];position+=1
                if type(entry) is not dict or set(entry)!={'pair','result'} or not partition.typed_equal(entry['pair'],[a[0],b[0]]):raise ValueError('wrong original norm pair')
                request=self.product_request(a,b,restriction,i!=j)
                check=block.verify_reference(**request,result=entry['result'],**self.budget.block_caps())
                self.budget.tick(check['stats']['work'])
                if check['status']=='UNKNOWN':raise Exhausted('block verification cap')
                if not check['valid']:raise ValueError('invalid externally bound block contraction')
                total=self.budget.rational(total+closed_value(entry['result']['message'],self.budget))
        if total<0 or read_ratio(proof['value'])!=total:raise ValueError('wrong completed squared norm')
        return total


def support_message(n,ids,equations):
    _,_,free=partition.parameter(equations,ids)
    return dict(n=n,retained=list(ids),zero=False,equations=equations,phase=[],scalar=[1,1],free_ids=free)


def input_hull(n,ids,parsed,budget):
    active=[i for i,p in enumerate(parsed) if p is not None]
    meter=budget.support_meter()
    try:rows=partition.hull(parsed,active,ids,meter)
    finally:budget.charge_support(meter)
    return support_message(n,ids,rows)


def point_hull(n,ids,points,budget):
    meter=budget.support_meter()
    try:
        rows,_=partition.rref([[x^points[0],0] for x in points[1:]],ids,meter)
        _,null,_=partition.parameter(rows,ids)
        equations,_=partition.rref([[v,(v&points[0]).bit_count()%2] for v in null],ids,meter)
    finally:budget.charge_support(meter)
    return support_message(n,ids,equations)


def sample_words(hull):
    anchor,basis,free=partition.parameter(hull['equations'],hull['retained'])
    yield anchor
    for v in basis:yield anchor^v
    for a,b in combinations(basis,2):yield anchor^a^b


def candidate_from_values(hull,values):
    c=values[0];free=hull['free_ids'];d=len(free)
    if not c or any(abs(v)!=abs(c) for v in values):raise ValueError('invalid candidate samples')
    singles=[int(values[1+i]!=c) for i in range(d)]
    phase=[1<<free[i] for i in range(d) if singles[i]]
    index=1+d
    for i,j in combinations(range(d),2):
        if int(values[index]!=c)^singles[i]^singles[j]:phase.append((1<<free[i])|(1<<free[j]))
        index+=1
    result=deepcopy(hull);result['phase']=sorted(phase);result['scalar']=pair(c)
    return result


def sample_candidate(hull,originals,budget):
    samples=[];values=[]
    for word in sample_words(hull):
        value=point_value(originals,word,budget);values.append(value)
        samples.append(dict(word=word,value=pair(value)))
        if not values[0]:return 'anchor_zero',samples,None
        if abs(value)!=abs(values[0]):return 'magnitude',samples,None
    candidate=candidate_from_values(hull,values)
    parse(hull['n'],hull['retained'],candidate,budget)
    return None,samples,candidate


def proof_products(cert):
    total=len(cert['root_norm']['products'])
    if cert.get('difference_norm') is not None:total+=len(cert['difference_norm']['products'])
    total+=sum(len(p['products']) for p in cert.get('outside_norms',[]))
    return total


def finish(status,message,certificate,budget,reason=None):
    budget.stats['certificate_products']=proof_products(certificate)
    if budget.stats['certificate_products']>budget.caps['max_certificate_products']:raise Exhausted('certificate product cap')
    result=dict(status=status,message=message,certificate=certificate,stats=budget.stats)
    if reason is not None:result['reason']=reason
    return result


def recognize(n,retained,messages,**caps):
    budget=Budget(caps)
    try:
        ids,originals,parsed,binding=request(n,retained,messages,budget)
        norms=Norms(n,ids,originals,budget)
        root=norms.query([])
        common=dict(format='explicit-one-piece-v1',input_sha256=binding,root_norm=root)
        if not read_ratio(root['value']):
            return finish('EXACT',partition.zero(n,ids),common|dict(kind='zero'),budget)
        enclosing=input_hull(n,ids,parsed,budget)
        # A failed enclosing-hull candidate is NEVER a rejection: cancellation
        # may have made the true support hull strictly smaller.
        budget.stats['fast_candidates']+=1
        _,_,candidate=sample_candidate(enclosing,originals,budget)
        if candidate is not None:
            difference=norms.query([],candidate)
            if not read_ratio(difference['value']):
                cert=common|dict(kind='equality',candidate=candidate,difference_norm=difference)
                return finish('EXACT',candidate,cert,budget)
        enclosing_anchor,enclosing_basis,enclosing_free=partition.parameter(enclosing['equations'],ids)
        def find_point(restriction):
            current=list(restriction);word=enclosing_anchor
            for variable,direction in zip(enclosing_free,enclosing_basis):
                half=current+[[1<<variable,0]]
                value=read_ratio(norms.query(half)['value'])
                bit=int(value==0)
                current.append([1<<variable,bit])
                if bit:word^=direction
            if any((word&mask).bit_count()%2!=rhs for mask,rhs in restriction) or not point_value(originals,word,budget):raise ArithmeticError('positive norm search lost support')
            return word
        points=[find_point([])]
        while True:
            hull=point_hull(n,ids,points,budget);outside=[]
            for mask,rhs in hull['equations']:
                restriction=[[mask,rhs^1]];proof=norms.query(restriction)
                if read_ratio(proof['value']):
                    points.append(find_point(restriction));budget.stats['hull_augmentations']+=1
                    if len(points)>len(ids)+1:raise ArithmeticError('hull rank did not strictly increase')
                    break
                outside.append(proof)
            else:break
        obstruction,samples,candidate=sample_candidate(hull,originals,budget)
        cert=common|dict(kind=obstruction,points=points,hull=hull,outside_norms=outside,
                         samples=samples,candidate=candidate,difference_norm=None)
        if obstruction is not None:
            return finish('UNSUPPORTED',None,cert,budget,obstruction)
        difference=norms.query([],candidate);cert['difference_norm']=difference
        if not read_ratio(difference['value']):
            # Equality alone is sufficient for a positive certificate; retained
            # discovery work remains charged even though its trace is discarded.
            positive=common|dict(kind='equality',candidate=candidate,difference_norm=difference)
            return finish('EXACT',candidate,positive,budget)
        cert['kind']='phase'
        return finish('UNSUPPORTED',None,cert,budget,'positive final difference norm')
    except (Exhausted,partition.Exhausted) as error:
        return dict(status='UNKNOWN',message=None,certificate=None,reason=str(error),stats=budget.stats)


def verify_one_piece(n,retained,messages,result,**caps):
    budget=Budget(caps)
    try:
        ids,originals,parsed,binding=request(n,retained,messages,budget)
        if type(result) is not dict or result.get('status') not in ('EXACT','UNSUPPORTED') or type(result.get('certificate')) is not dict:raise ValueError('expected completed recognition proof')
        cert=result['certificate'];base={'format','input_sha256','root_norm','kind'}
        if cert.get('format')!='explicit-one-piece-v1' or cert.get('input_sha256')!=binding:raise ValueError('wrong complete original input binding')
        kind=cert.get('kind');norms=Norms(n,ids,originals,budget)
        if proof_products(cert)>budget.caps['max_certificate_products']:raise Exhausted('certificate product cap')
        budget.stats['certificate_products']=proof_products(cert)
        total=norms.check([],cert['root_norm'])
        if kind=='zero':
            expected=partition.zero(n,ids)
            if set(cert)!=base or total or result['status']!='EXACT' or not partition.typed_equal(result.get('message'),expected):raise ValueError('false zero recognition')
            return dict(valid=True,status='VERIFIED',recognition='EXACT',message=expected,stats=budget.stats)
        if not total:raise ValueError('nonzero case requires positive original norm')
        if kind=='equality':
            if set(cert)!=base|{'candidate','difference_norm'} or result['status']!='EXACT':raise ValueError('wrong equality proof format')
            candidate=cert['candidate'];parse(n,ids,candidate,budget)
            if candidate['zero'] or not partition.typed_equal(result.get('message'),candidate) or norms.check([],cert['difference_norm'],candidate):raise ValueError('false one-piece equality')
            return dict(valid=True,status='VERIFIED',recognition='EXACT',message=deepcopy(candidate),stats=budget.stats)
        fields=base|{'points','hull','outside_norms','samples','candidate','difference_norm'}
        if set(cert)!=fields or kind not in ('anchor_zero','magnitude','phase') or result['status']!='UNSUPPORTED' or result.get('message') is not None:raise ValueError('wrong obstruction proof format')
        hull=cert['hull'];h=parse(n,ids,hull,budget)
        if h is None or hull['phase'] or hull['scalar']!=[1,1]:raise ValueError('invalid hull descriptor')
        points=cert['points'];allowed=sum(1<<v for v in ids)
        if type(points) is not list or not points or len(points)>len(ids)+1 or any(type(x) is not int or x<0 or x&~allowed for x in points):raise ValueError('invalid support witnesses')
        for word in points:
            if any((word&mask).bit_count()%2!=rhs for mask,rhs in hull['equations']) or not point_value(originals,word,budget):raise ValueError('false nonzero support point')
        meter=budget.support_meter()
        try:rank=partition.xor_rank([x^points[0] for x in points[1:]],meter)
        finally:budget.charge_support(meter)
        if rank!=len(points)-1 or rank!=len(h['free']):raise ValueError('support points do not span the proposed hull')
        outside=cert['outside_norms']
        if type(outside) is not list or len(outside)!=len(hull['equations']):raise ValueError('missing outside-hull norm')
        for (mask,rhs),proof in zip(hull['equations'],outside):
            if norms.check([[mask,rhs^1]],proof):raise ValueError('nonzero support escapes proposed hull')
        samples=cert['samples'];words=sample_words(hull)
        dimension=len(hull['free_ids']);sample_count=1+dimension+dimension*(dimension-1)//2
        if type(samples) is not list or not samples or len(samples)>sample_count:raise ValueError('invalid phase sample coverage')
        values=[]
        for sample,word in zip(samples,words):
            if type(sample) is not dict or set(sample)!={'word','value'} or type(sample['word']) is not int or sample['word']!=word:raise ValueError('wrong phase sample point')
            value=point_value(originals,word,budget)
            if read_ratio(sample['value'])!=value:raise ValueError('wrong original sample value')
            values.append(value)
        if kind=='anchor_zero':
            if len(values)!=1 or values[0] or cert['candidate'] is not None or cert['difference_norm'] is not None:raise ValueError('false zero-anchor obstruction')
        elif kind=='magnitude':
            if len(values)<2 or not values[0] or any(abs(v)!=abs(values[0]) for v in values[:-1]) or abs(values[-1])==abs(values[0]) or cert['candidate'] is not None or cert['difference_norm'] is not None:raise ValueError('false magnitude obstruction')
        else:
            if len(values)!=sample_count or not values[0] or any(abs(v)!=abs(values[0]) for v in values):raise ValueError('incomplete compatible quadratic samples')
            candidate=candidate_from_values(hull,values)
            parse(n,ids,candidate,budget)
            if not partition.typed_equal(cert['candidate'],candidate) or norms.check([],cert['difference_norm'],candidate)<=0:raise ValueError('false final phase obstruction')
        return dict(valid=True,status='VERIFIED',recognition='UNSUPPORTED',message=None,reason=kind,stats=budget.stats)
    except (Exhausted,partition.Exhausted) as error:
        return dict(valid=False,status='UNKNOWN',recognition=None,message=None,reason=str(error),stats=budget.stats)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,OverflowError,ZeroDivisionError) as error:
        return dict(valid=False,status='INVALID',recognition=None,message=None,reason=str(error),stats=budget.stats)


verify=verify_one_piece
