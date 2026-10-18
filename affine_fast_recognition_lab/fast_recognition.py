"""Cheap exact obstructions followed by the frozen complete norm recognizer.

Local search limits are inconclusive.  All consumed search and repeated parsing
work is charged before passing the remaining aggregate budget to the fallback.
"""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import importlib.util
import sys

NIGHT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('_fast_frozen_one_piece', NIGHT/'affine_one_piece_lab'/'one_piece.py')
strong = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = strong
spec.loader.exec_module(strong)
partition = strong.partition
EXTRA_LIMITS = dict(max_probe_samples=64, max_probe_cubes=16, max_probe_work=20000)
LIMITS = {**strong.LIMITS, **EXTRA_LIMITS}
FORMAT = 'fast-one-piece-v1'


class LocalLimit(Exception):
    pass


class Budget(strong.Budget):
    def __init__(self, caps):
        if set(caps)-set(LIMITS):
            raise ValueError('unknown cap')
        if any(type(v) is not int or v < 0 for v in caps.values()):
            raise ValueError('caps must be nonnegative exact integers')
        super().__init__({k:v for k,v in caps.items() if k in strong.LIMITS})
        self.caps.update({k:caps.get(k,v) for k,v in EXTRA_LIMITS.items()})
        self.in_probe = False
        self.stats.update(probe_work=0, probe_samples=0, probe_samples_completed=0,
            probe_cache_hits=0, probe_cube_tests=0, probe_linear_steps=0,
            probe_schedule_steps=0, parse_work=0, fallback_work=0, fallback_calls=0,
            probe_local_limits=0, probe_identity_tests=0)

    def tick(self, amount=1):
        # Attempted operations, including the one crossing a cap, remain charged.
        if self.in_probe:
            self.stats['probe_work'] += amount
        super().tick(amount)
        if self.in_probe and self.stats['probe_work'] > self.caps['max_probe_work']:
            raise LocalLimit('local probe work cap')

    def linear(self, amount=1):
        self.stats['probe_linear_steps'] += amount
        self.tick(amount)

    def schedule(self):
        self.stats['probe_schedule_steps'] += 1
        self.tick()

    def remaining(self):
        result = {k:self.caps[k] for k in strong.LIMITS}
        for cap, key in (('max_work','work'), ('max_norm_queries','norm_queries'),
                ('max_pair_contractions','pair_contractions'),
                ('max_point_evaluations','point_evaluations'),
                ('max_certificate_products','certificate_products')):
            result[cap] = max(0, result[cap]-self.stats[key])
        return result

    def absorb(self, stats):
        self.stats['fallback_work'] += stats['work']
        for key in strong.Budget({}).stats:
            if key == 'work':
                continue
            if key == 'peak_scalar_bits':
                self.stats[key] = max(self.stats[key],stats[key])
            else:
                self.stats[key] += stats[key]
        self.tick(stats['work'])


def charge_hash(value, budget):
    """Charge typed traversal and payload bytes before the extra source digest."""
    budget.tick()
    if type(value) is int:
        budget.tick(max(1,(abs(value).bit_length()+7)//8))
    elif type(value) is str:
        budget.tick(len(value.encode()))
    elif type(value) is list:
        for item in value:
            charge_hash(item,budget)
    elif type(value) is dict:
        for key, item in value.items():
            charge_hash(key,budget); charge_hash(item,budget)


def request(n, retained, messages, budget):
    start = budget.stats['work']
    try:
        ids, originals, parsed, _ = strong.request(n,retained,messages,budget)
        payload = dict(format=FORMAT,n=n,retained=ids,messages=originals)
        # The imported parser computes two binding digests as well as this one.
        # A conservative three traversals make this setup cost visible.
        for _ in range(3):
            charge_hash(payload,budget)
        binding = partition.digest(payload)
        return ids, originals, parsed, binding
    finally:
        budget.stats['parse_work'] += budget.stats['work']-start


def value_at(messages, word, budget):
    """Direct complete original-sum evaluation, independent of norm discovery."""
    budget.reserve('point_evaluations','max_point_evaluations')
    total = Fraction(0)
    for message in messages:
        budget.tick()  # Even a zero original occurrence is visited.
        if message['zero']:
            continue
        inside = True
        for mask, rhs in message['equations']:
            budget.tick()
            if (word & mask).bit_count() % 2 != rhs:
                inside = False
        # The complete term is evaluated; no saved sample or scalar is trusted.
        parity = 0
        for monomial in message['phase']:
            budget.tick()
            parity ^= int((word & monomial) == monomial)
        if inside:
            coefficient = Fraction(*message['scalar'])
            total = budget.rational(total + (-coefficient if parity else coefficient))
    return total


def sample(word, value):
    return dict(word=word,value=strong.pair(value))


class Discovery:
    def __init__(self,n,ids,messages,budget):
        self.n=n; self.ids=ids; self.messages=messages; self.budget=budget
        self.cache={}; self.nonzero=[]; self.basis={}; self.zeros=[]
        self.first=None; self.witness=None

    def reduce(self, vector, selector=0):
        while vector:
            self.budget.linear()
            pivot=vector.bit_length()-1
            if pivot not in self.basis:
                break
            other, used=self.basis[pivot]
            vector ^= other; selector ^= used
        return vector,selector

    def test_zero(self, word):
        residual,selector=self.reduce((1<<self.n)|word)
        if not residual:
            points=[self.nonzero[i] for i in range(len(self.nonzero)) if selector>>i&1]
            self.budget.linear(len(self.nonzero))
            self.witness=dict(kind='affine_hole',nonzero_points=deepcopy(points),
                selector=(1<<len(points))-1,zero=sample(word,Fraction(0)))

    def get(self,word):
        self.budget.schedule()
        if word in self.cache:
            self.budget.stats['probe_cache_hits']+=1
            return self.cache[word]
        if self.budget.stats['probe_samples'] >= self.budget.caps['max_probe_samples']:
            raise LocalLimit('local probe sample cap')
        self.budget.stats['probe_samples']+=1
        value=value_at(self.messages,word,self.budget)
        self.budget.stats['probe_samples_completed']+=1
        self.cache[word]=value
        current=sample(word,value)
        if value:
            self.budget.stats['probe_identity_tests']+=1
            self.budget.tick()
            if self.first is not None and abs(value)!=abs(strong.read_ratio(self.first['value'])):
                self.witness=dict(kind='magnitude',points=[deepcopy(self.first),current])
                return value
            if self.first is None:
                self.first=current
            index=len(self.nonzero)
            residual,selector=self.reduce((1<<self.n)|word,1<<index)
            if residual:
                self.basis[residual.bit_length()-1]=(residual,selector)
                self.nonzero.append(current)
                self.budget.linear()
                for zero in self.zeros:
                    self.test_zero(zero)
                    if self.witness is not None:
                        break
        else:
            self.zeros.append(word)
            self.test_zero(word)
        return value

    def run(self,parsed):
        # Fixed data-independent coordinate schedule, then supplied supports.
        self.get(0)
        if self.witness: return self.witness
        for variable in self.ids:
            self.get(1<<variable)
            if self.witness: return self.witness
        for triple in combinations(self.ids,3):
            if self.budget.stats['probe_cube_tests']>=self.budget.caps['max_probe_cubes']:
                break
            self.budget.stats['probe_cube_tests']+=1
            self.budget.schedule()
            directions=[1<<v for v in triple]
            values=[]; points=[]
            for mask in range(8):
                word=0
                for i,direction in enumerate(directions):
                    self.budget.schedule()
                    if mask>>i&1: word ^= direction
                value=self.get(word); values.append(value); points.append(sample(word,value))
                if self.witness: return self.witness
            self.budget.stats['probe_identity_tests']+=1
            self.budget.tick(8)
            if values[0] and all(abs(v)==abs(values[0]) for v in values):
                if sum(v<0 for v in values)%2:
                    return dict(kind='cubic_sign',anchor=0,directions=directions,points=points)
        for support in parsed:
            self.budget.schedule()
            if support is None: continue
            self.get(support['anchor'])
            if self.witness: return self.witness
            for direction in support['basis']:
                self.get(support['anchor']^direction)
                if self.witness: return self.witness
        return None


def run_probe(n,ids,originals,parsed,budget):
    budget.in_probe=True
    try:
        witness=Discovery(n,ids,originals,budget).run(parsed)
        return witness,'witness' if witness else 'deterministic schedule completed'
    except LocalLimit as error:
        budget.stats['probe_local_limits']+=1
        return None,str(error)
    finally:
        budget.in_probe=False


def negative_result(binding,witness,budget):
    return dict(status='UNSUPPORTED',message=None,certificate=dict(
        format=FORMAT,input_sha256=binding,kind='negative',witness=witness),stats=budget.stats)


def unknown(budget,error):
    return dict(status='UNKNOWN',message=None,certificate=None,stats=budget.stats,reason=str(error))


def probe(n,retained,messages,**caps):
    """Return a verified-type obstruction or INCONCLUSIVE/UNKNOWN, never positive."""
    budget=Budget(caps)
    try:
        ids,originals,parsed,binding=request(n,retained,messages,budget)
        witness,reason=run_probe(n,ids,originals,parsed,budget)
        if witness is not None:
            return negative_result(binding,witness,budget)
        return dict(status='INCONCLUSIVE',message=None,certificate=None,reason=reason,stats=budget.stats)
    except (strong.Exhausted,partition.Exhausted) as error:
        return unknown(budget,error)


def recognize(n,retained,messages,**caps):
    budget=Budget(caps)
    try:
        ids,originals,parsed,binding=request(n,retained,messages,budget)
        witness,_=run_probe(n,ids,originals,parsed,budget)
        if witness is not None:
            return negative_result(binding,witness,budget)
        budget.stats['fallback_calls']+=1
        result=strong.recognize(n,ids,originals,**budget.remaining())
        budget.absorb(result['stats'])
        if result['status']=='UNKNOWN':
            return unknown(budget,'complete fallback: '+result.get('reason','cap'))
        certificate=dict(format=FORMAT,input_sha256=binding,kind='fallback',result=result)
        return dict(status=result['status'],message=deepcopy(result['message']),certificate=certificate,stats=budget.stats)
    except (strong.Exhausted,partition.Exhausted) as error:
        return unknown(budget,error)


def coordinate(word,allowed):
    if type(word) is not int or word<0 or word&~allowed:
        raise ValueError('invalid exact coordinate word')
    return word


def check_sample(item,allowed,originals,budget):
    if type(item) is not dict or set(item)!={'word','value'}:
        raise ValueError('invalid sample record')
    word=coordinate(item['word'],allowed)
    recorded=strong.read_ratio(item['value'])
    budget.rational(recorded)
    value=value_at(originals,word,budget)
    if value!=recorded: raise ValueError('false complete original-sum value')
    return word,value


def check_witness(witness,n,ids,originals,budget):
    if type(witness) is not dict: raise ValueError('invalid negative witness')
    allowed=sum(1<<v for v in ids)
    kind=witness.get('kind')
    if kind=='magnitude':
        if set(witness)!={'kind','points'} or type(witness['points']) is not list or len(witness['points'])!=2:
            raise ValueError('invalid magnitude witness')
        first,second=[check_sample(p,allowed,originals,budget) for p in witness['points']]
        if not first[1] or not second[1] or abs(first[1])==abs(second[1]):
            raise ValueError('no unequal nonzero magnitudes')
    elif kind=='affine_hole':
        if set(witness)!={'kind','nonzero_points','selector','zero'}:
            raise ValueError('invalid affine-hole witness')
        points=witness['nonzero_points']; selector=witness['selector']
        if type(points) is not list or not 1<=len(points)<=len(ids)+1 or type(selector) is not int or selector<0 or selector>>len(points) or selector.bit_count()%2!=1:
            raise ValueError('invalid odd selector')
        zero,zero_value=check_sample(witness['zero'],allowed,originals,budget)
        total=0;seen=set()
        for i,p in enumerate(points):
            word,value=check_sample(p,allowed,originals,budget)
            if not value or word in seen: raise ValueError('invalid nonzero support points')
            seen.add(word);budget.tick()
            if selector>>i&1: total^=word
        if zero_value or total!=zero: raise ValueError('false odd affine combination hole')
    elif kind=='cubic_sign':
        if set(witness)!={'kind','anchor','directions','points'} or type(witness['directions']) is not list or len(witness['directions'])!=3 or type(witness['points']) is not list or len(witness['points'])!=8:
            raise ValueError('invalid cubic-sign witness')
        anchor=coordinate(witness['anchor'],allowed)
        directions=[coordinate(v,allowed) for v in witness['directions']]
        values=[]
        for mask,item in enumerate(witness['points']):
            expected=anchor
            for i,direction in enumerate(directions):
                budget.tick()
                if mask>>i&1: expected^=direction
            word,value=check_sample(item,allowed,originals,budget)
            if word!=expected: raise ValueError('wrong cube coordinate')
            values.append(value)
        if not values[0] or any(abs(v)!=abs(values[0]) for v in values) or sum(v<0 for v in values)%2!=1:
            raise ValueError('no negative equal-magnitude cube sign product')
    else:
        raise ValueError('unknown obstruction kind')


def verify_one_piece(n,retained,messages,result,**caps):
    budget=Budget(caps)
    try:
        ids,originals,_,binding=request(n,retained,messages,budget)
        if type(result) is not dict or result.get('status') not in ('EXACT','UNSUPPORTED'):
            raise ValueError('no complete recognition claim')
        certificate=result.get('certificate')
        if type(certificate) is not dict or certificate.get('format')!=FORMAT or certificate.get('input_sha256')!=binding:
            raise ValueError('wrong original input binding')
        base={'format','input_sha256','kind'}
        if certificate.get('kind')=='negative':
            if set(certificate)!=base|{'witness'} or result['status']!='UNSUPPORTED' or result.get('message') is not None:
                raise ValueError('wrong negative claim')
            check_witness(certificate['witness'],n,ids,originals,budget)
            return dict(valid=True,status='VERIFIED',recognition='UNSUPPORTED',message=None,stats=budget.stats)
        if certificate.get('kind')!='fallback' or set(certificate)!=base|{'result'}:
            raise ValueError('wrong fallback format')
        nested=certificate['result']
        if type(nested) is not dict or nested.get('status')!=result['status'] or not partition.typed_equal(nested.get('message'),result.get('message')):
            raise ValueError('wrong fallback result binding')
        budget.stats['fallback_calls']+=1
        checked=strong.verify_one_piece(n,ids,originals,nested,**budget.remaining())
        budget.absorb(checked['stats'])
        if checked['status']=='UNKNOWN': raise strong.Exhausted('fallback proof replay cap')
        if not checked['valid']: raise ValueError('invalid externally bound fallback proof')
        return dict(valid=True,status='VERIFIED',recognition=checked['recognition'],message=deepcopy(checked['message']),stats=budget.stats)
    except (strong.Exhausted,partition.Exhausted) as error:
        return dict(valid=False,status='UNKNOWN',recognition=None,message=None,reason=str(error),stats=budget.stats)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,OverflowError,ZeroDivisionError) as error:
        return dict(valid=False,status='INVALID',recognition=None,message=None,reason=str(error),stats=budget.stats)


verify=verify_one_piece
verify_probe=verify_one_piece
