"""Exact original-input checks of the first-one-shell conditioning example."""
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent


def original(n):
    if type(n) is not int or n < 1:
        raise ValueError('positive exact integer width required')
    shells = [[[1 << k, 0] for k in range(j)] + [[1 << j, 1]]
              for j in range(n)]
    return dict(n=n, full_equations=[], shell_equations=shells,
                coefficients=[1]+[-1]*n,
                target_equations=[[1 << j, 0] for j in range(n)])


def satisfies(word, rows):
    return all((word & mask).bit_count() % 2 == rhs for mask, rhs in rows)


def determinant(matrix):
    """Generic rational elimination, independent of the star determinant formula."""
    matrix = [list(map(Fraction, row)) for row in matrix]
    answer = Fraction(1)
    for j in range(len(matrix)):
        pivot = next((i for i in range(j, len(matrix)) if matrix[i][j]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != j:
            matrix[pivot], matrix[j] = matrix[j], matrix[pivot]
            answer = -answer
        value = matrix[j][j]
        answer *= value
        for i in range(j+1, len(matrix)):
            factor = matrix[i][j]/value
            for k in range(j+1, len(matrix)):
                matrix[i][k] -= factor*matrix[j][k]
            matrix[i][j] = 0
    return answer


def run_case(n):
    request = original(n)
    sizes = [1 << (n-j-1) for j in range(n)]
    # Check that the actual equations are independent coordinate pins and
    # hence justify the support sizes even when no truth table is enumerated.
    for j, rows in enumerate(request['shell_equations']):
        assert len(rows) == j+1
        assert [mask for mask, _ in rows] == [1 << k for k in range(j+1)]
        assert [rhs for _, rhs in rows] == [0]*j+[1]
        assert sizes[j] == 1 << (n-len(rows))
    assert sum(sizes) == (1 << n)-1
    words = 0
    if n <= 12:
        for word in range(1 << n):
            memberships = [satisfies(word, rows) for rows in request['shell_equations']]
            assert sum(memberships) == int(word != 0)
            actual = request['coefficients'][0] + sum(
                c*inside for c, inside in zip(request['coefficients'][1:], memberships))
            assert actual == int(satisfies(word, request['target_equations']))
            words += 1
    rational_det = None
    if n <= 24:
        # Unnormalized inner products are exact integers. Dividing its
        # determinant by the product of diagonal norms gives det(G).
        matrix = [[0]*(n+1) for _ in range(n+1)]
        matrix[0][0] = 1 << n
        for j, size in enumerate(sizes, 1):
            matrix[0][j] = matrix[j][0] = matrix[j][j] = size
        got = determinant(matrix)
        denominator = 1 << n
        for size in sizes:
            denominator *= size
        normalized = got/denominator
        assert normalized == Fraction(1, 1 << n)
        c = request['coefficients']
        assert sum(c[i]*matrix[i][j]*c[j] for i in range(n+1) for j in range(n+1)) == 1
        rational_det = [normalized.numerator, normalized.denominator]
    squared_overlap_sum = sum((Fraction(size, 1 << n) for size in sizes), Fraction())
    assert squared_overlap_sum == 1-Fraction(1, 1 << n)
    normalized_coefficient_energy = (1 << n)+sum(sizes)
    assert normalized_coefficient_energy == (1 << (n+1))-1
    return dict(original=request, pieces=n+1, original_coefficient_max_bits=1,
                truth_words=words, determinant_by_elimination=rational_det,
                normalized_gram_determinant=[1, 1 << n],
                smallest_eigenvalue_bounds=[[1, 1 << (n+1)], [1, 1 << n]],
                normalized_coefficient_energy=normalized_coefficient_energy,
                support_partition_checked=True)


def hashes():
    return {p.name: sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__), HERE/'THEOREM.md']}


def main():
    before = hashes()
    cases = [run_case(n) for n in [*range(1, 25), 32, 64, 128, 256]]
    after = hashes()
    assert before == after
    result = dict(status='VERIFIED_BOUNDED_CONTROLS', source_hashes_before=before,
                  source_hashes_after=after, cases=cases,
                  summary=dict(cases=len(cases), truth_words=sum(r['truth_words'] for r in cases),
                               exact_determinants=sum(r['determinant_by_elimination'] is not None for r in cases)),
                  scope='Finite checks supplement the written all-size partition and spectral proof. No minimum-rank or SAT complexity claim.')
    (HERE/'RESULTS.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result['summary']))


if __name__ == '__main__':
    main()
