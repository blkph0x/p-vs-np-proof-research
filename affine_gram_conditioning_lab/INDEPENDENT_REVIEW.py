"""Independent original-support and exact Gram replay; no producer imports."""
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import time

HERE=Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(test,message):
    if not test:raise AssertionError(message)


def member(word,equations):
    return all((word&mask).bit_count()%2==rhs for mask,rhs in equations)


def main():
    started=time.perf_counter()
    saved=json.loads((HERE/'RESULTS.json').read_text())
    require(saved['source_hashes_before']==saved['source_hashes_after'],'author source mismatch')
    source={name:digest(HERE/name) for name in saved['source_hashes_before']}
    require(source==saved['source_hashes_before'],'stale producer sources')
    for name in ['RESULTS.json','INDEPENDENT_REVIEW.py','INDEPENDENT_REVIEW.md']:
        source[name]=digest(HERE/name)
    cases=[];words=grams=evaluation_points=0
    require([r['original']['n'] for r in saved['cases']]==list(range(1,25))+[32,64,128,256],
            'saved width coverage changed')
    for row in saved['cases']:
        original=row['original'];n=original['n'];shells=original['shell_equations']
        require(original['full_equations']==[],'full cube changed')
        require(original['coefficients']==[1]+[-1]*n,'coefficients changed')
        require(original['target_equations']==[[1<<j,0] for j in range(n)],'target changed')
        require(shells==[[[1<<k,0] for k in range(j)]+[[1<<j,1]] for j in range(n)],'original shells changed')
        sizes=[2**(n-j-1) for j in range(n)]
        require(sum(sizes)==2**n-1,'shell sizes do not partition nonzero words')
        require(row['normalized_coefficient_energy']==2**(n+1)-1,'energy formula changed')
        require(row['normalized_gram_determinant']==[1,2**n],'Gram determinant changed')
        require(row['smallest_eigenvalue_bounds']==[[1,2**(n+1)],[1,2**n]],'eigenvalue bounds changed')
        # Actual evaluation minor: first row [1,0,...], other rows [1,e_j].
        # Its determinant is one, so these n+1 indicators are independent.
        for point in [0]+[1<<j for j in range(n)]:
            actual=[int(member(point,eq)) for eq in shells]
            require(actual==[int(point==1<<j) for j in range(n)],'independence minor differs')
            evaluation_points+=1
        direct=None
        if n<=12:
            sets=[set(range(2**n))]+[{x for x in range(2**n) if member(x,eq)} for eq in shells]
            gram=[[len(a&b) for b in sets] for a in sets]
            for x in range(2**n):
                require(1-sum(x in a for a in sets[1:])==int(x==0),'original partition identity fails')
            require([gram[0][j] for j in range(n+1)]==[2**n]+sizes,'actual full-shell correlations differ')
            for j in range(1,n+1):
                require([gram[j][k] for k in range(1,n+1)]==[sizes[j-1] if k==j else 0 for k in range(1,n+1)],
                        'actual shells are not orthogonal with stated sizes')
            # Determinant-preserving row subtraction is structurally separate
            # from the producer's generic rational Gaussian elimination.
            reduced=[gram[0][k]-sum(gram[j][k] for j in range(1,n+1)) for k in range(n+1)]
            require(reduced==[1]+[0]*n,'determinant row operation failed')
            determinant=1
            for size in sizes:determinant*=size
            normalized=Fraction(determinant,2**n*determinant)
            require(normalized==Fraction(*row['determinant_by_elimination']),'independent determinant disagrees')
            coefficients=original['coefficients']
            require(sum(coefficients[i]*gram[i][j]*coefficients[j] for i in range(n+1) for j in range(n+1))==1,
                    'actual quadratic energy is not one')
            direct=dict(original_truth_words=2**n,actual_integer_gram=gram,
                        determinant_from_row_subtraction=determinant,normalized_determinant=[normalized.numerator,normalized.denominator])
            words+=2**n;grams+=1
        elif n<=24:
            require(row['determinant_by_elimination']==[1,2**n],'saved elimination determinant disagrees with identity')
        else:
            require(row['determinant_by_elimination'] is None,'wide row claims unperformed elimination')
        require(row['truth_words']==(2**n if n<=12 else 0),'truth-word scope changed')
        cases.append(dict(n=n,original_support_equations_checked=True,independence_evaluation_points=n+1,
                          squared_full_shell_overlap_sum=[2**n-1,2**n],direct_support_gram=direct))
    require(words==8190 and grams==12 and len(cases)==28,'independent coverage differs')
    require(saved['summary']==dict(cases=28,truth_words=8190,exact_determinants=24),'author summary differs')
    require(all(digest(HERE/name)==value for name,value in source.items()),'source changed during review')
    output=dict(verdict='CLEAN',source_sha256=source,source_unchanged_during_run=True,
                summary=dict(original_cases=28,original_truth_words=words,truth_vector_Gram_matrices=grams,
                             independence_evaluation_points=evaluation_points,saved_determinants_matching_theorem=24),
                cases=cases,seconds=time.perf_counter()-started,
                scope='Producer not imported. Complete actual-support vectors and exact integer Gram matrices through n12; original equations and evaluation-minor independence for all28 widths through256. All-size spectral inequalities are proved in the accompanying review, not numerically approximated.')
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(verdict=output['verdict'],**output['summary'],source_unchanged=True)))


if __name__=='__main__':main()
