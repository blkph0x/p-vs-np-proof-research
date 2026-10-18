"""A first-principles probabilistic existence proof of linear-width binary codes.

Does not prove any explicit seed has that bound without exhaustive certification;
no claim of internal 4-connectivity follows from the probability calculation alone.
"""
import math


def existence_bound(k:int)->dict:
    """For a random k x 2k GF(2) generator, bound ALL balanced cuts.

    Rank <= k-t of one kxk submatrix implies a t-subspace of kernel.
    Number of t-subspaces <= 4*2^{t(k-t)}, each is killed with prob 2^{-kt},
    so chance <=4*2^{-t^2} per submatrix.
    Union over <= 2*binom(2k,k) submatrices; full row rank fails with prob <2^{-k}.
    """
    if k<2: raise ValueError
    t=math.isqrt(2*k+6)
    if t*t<2*k+6:t+=1
    # upper bound probability of any poor balanced kxk side: <=2^(2k+3-t*t)
    failure_upper=2.0**(2*k+3-t*t)
    full_rank_failure=2.0**(-k)
    lam_lower=k-2*t+2
    return {
        'n':2*k,'dimension':k,'rank_deficiency_threshold_t':t,
        'certified_existence_lambda_lower_bound':max(0,lam_lower),
        'at_least_trellis_states':1<<max(0,lam_lower),
        'bad_balanced_cut_probability_upper':failure_upper,
        'full_rank_failure_probability_upper':full_rank_failure,
        'positive_probability_of_full_rank_good_code':failure_upper+full_rank_failure<1,
        'asymptotic_bound':'k - 2*ceil(sqrt(2k+6)) + 2 = k-O(sqrt(k))',
    }
