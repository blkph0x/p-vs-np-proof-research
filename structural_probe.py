"""Polynomial direct-sum decomposition of represented binary column matroids.

The fundamental-circuit graph of any basis gives the matroid components. A
separate, low-pivot rank computation validates rank additivity of the output.
Rank additivity certifies the direct sum, but alone does not certify that its
blocks are finest: that follows from the recorded fundamental circuits.

Run this file to print bounded probes of the six stored code fixtures. No result
artifacts are overwritten. Only tiny independent tests enumerate circuits.
"""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from itertools import combinations
from pathlib import Path
from time import perf_counter
import argparse
import json


def _columns(columns):
    result = tuple(columns)
    if any(type(value) is not int or value < 0 for value in result):
        raise ValueError('columns must be nonnegative integers')
    return result


def _indices(indices, n, name):
    result = tuple(indices)
    if any(type(j) is not int or not 0 <= j < n for j in result):
        raise ValueError(f'{name} contains an invalid coordinate')
    if len(set(result)) != len(result):
        raise ValueError(f'{name} contains duplicate coordinates')
    return result


def _independent_rank(columns):
    """Low-pivot elimination, independent of the decomposition implementation."""
    pivots = {}
    xors = 0
    for value in columns:
        while value:
            low_bit = value & -value
            if low_bit not in pivots:
                pivots[low_bit] = value
                break
            value ^= pivots[low_bit]
            xors += 1
    return len(pivots), xors


def validate_partition(columns, components):
    """Independently certify coverage and r(E)=sum_C r(C).

    A valid result proves a direct-sum partition; coarser partitions also pass.
    All coordinates, including loops, must occur exactly once.
    """
    columns = _columns(columns)
    parts = tuple(tuple(part) for part in components)
    errors = []
    flat = [j for part in parts for j in part]
    if any(not part for part in parts):
        errors.append('empty component')
    if any(type(j) is not int or not 0 <= j < len(columns) for j in flat):
        errors.append('invalid coordinate')
    elif sorted(flat) != list(range(len(columns))):
        errors.append('components must partition all coordinates exactly once')
    if errors:
        return {'valid': False, 'errors': errors, 'rank_evaluations': 0,
                'xor_reductions': 0}
    total_rank, xors = _independent_rank(columns)
    ranks = []
    for part in parts:
        rank, work = _independent_rank(columns[j] for j in part)
        ranks.append(rank)
        xors += work
    if sum(ranks) != total_rank:
        errors.append('component ranks do not add to the total rank')
    return {'valid': not errors, 'errors': errors, 'total_rank': total_rank,
            'component_ranks': ranks, 'rank_sum': sum(ranks),
            'rank_evaluations': len(parts) + 1, 'xor_reductions': xors}


def decompose_columns(columns, basis_indices=None):
    """Return finest direct-sum blocks and fundamental circuits in local indices.

    An optional basis may use any independent spanning columns, in any order.
    Zero columns are singleton loops; independent elements in no circuit are
    singleton coloops. All integer XOR counts are reported, not hidden as time.
    """
    columns = _columns(columns)
    n = len(columns)
    work = {'basis_discovery_columns': 0, 'basis_discovery_xors': 0,
            'basis_setup_xors': 0, 'circuit_reduction_xors': 0,
            'fundamental_circuits': 0, 'union_attempts': 0, 'successful_unions': 0}
    if basis_indices is None:
        selected, echelon = [], {}
        for j, value in enumerate(columns):
            work['basis_discovery_columns'] += 1
            while value:
                pivot = value.bit_length() - 1
                if pivot not in echelon:
                    echelon[pivot] = value
                    selected.append(j)
                    break
                value ^= echelon[pivot]
                work['basis_discovery_xors'] += 1
        basis_indices = tuple(selected)
    else:
        basis_indices = _indices(basis_indices, n, 'basis_indices')

    # Each reduced basis vector carries its expression in the ORIGINAL basis.
    echelon = {}
    for position, j in enumerate(basis_indices):
        value, expression = columns[j], 1 << position
        while value:
            pivot = value.bit_length() - 1
            if pivot not in echelon:
                echelon[pivot] = value, expression
                break
            previous, support = echelon[pivot]
            value ^= previous
            expression ^= support
            work['basis_setup_xors'] += 1
        if not value:
            raise ValueError('basis_indices are not independent')

    parent = list(range(n))
    size = [1] * n

    def find(j):
        while parent[j] != j:
            parent[j] = parent[parent[j]]
            j = parent[j]
        return j

    def union(a, b):
        work['union_attempts'] += 1
        a, b = find(a), find(b)
        if a == b:
            return
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]
        work['successful_unions'] += 1

    basis_set = set(basis_indices)
    circuits = []
    for j, column in enumerate(columns):
        if j in basis_set:
            continue
        value, expression = column, 0
        while value:
            pivot = value.bit_length() - 1
            if pivot not in echelon:
                raise ValueError('basis_indices do not span all columns')
            previous, support = echelon[pivot]
            value ^= previous
            expression ^= support
            work['circuit_reduction_xors'] += 1
        support = [basis_indices[i] for i in range(len(basis_indices)) if expression >> i & 1]
        circuit = sorted([j, *support])
        circuits.append({'nonbasis_coordinate': j, 'coordinates': circuit})
        work['fundamental_circuits'] += 1
        for other in support:
            union(j, other)

    blocks = {}
    for j in range(n):
        blocks.setdefault(find(j), []).append(j)
    components = sorted(blocks.values(), key=lambda block: block[0])
    certificate = validate_partition(columns, components)
    if not certificate['valid']:
        raise ArithmeticError('fundamental-circuit partition failed rank-additivity verification')
    work['verification_rank_evaluations'] = certificate['rank_evaluations']
    work['verification_xors'] = certificate['xor_reductions']
    work['total_xor_reductions'] = sum(work[key] for key in (
        'basis_discovery_xors', 'basis_setup_xors', 'circuit_reduction_xors', 'verification_xors'))
    return {'n': n, 'rank': len(basis_indices), 'basis_indices': list(basis_indices),
            'components': components, 'fundamental_circuits': circuits,
            'loops': [j for j, column in enumerate(columns) if column == 0],
            'coloops': [block[0] for block in components if len(block) == 1 and columns[block[0]]],
            'partition_certificate': certificate, 'work': work}


def _deletion_helpers():
    path = Path(__file__).resolve().parent / 'charged_work_core_lab' / 'deletion_solver.py'
    spec = spec_from_file_location('_structural_probe_deletion_helpers', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def conditioned_components(generator, n, deleted=()):
    """Decompose H_R after conditioning D; retain original coordinate labels.

    This analyzes the homogeneous kernel of H_R shared by feasible affine cosets.
    It does not by itself solve the coset syndrome compatibility problem.
    """
    helper = _deletion_helpers()
    rows = helper.validate_generator(generator, n)
    deleted = _indices(deleted, n, 'deleted')
    checks = helper.parity_check(rows, n)
    columns = helper.columns_from_rows(checks, n)
    return _conditioned_from_columns(columns, deleted)


def _conditioned_from_columns(columns, deleted):
    removed = set(deleted)
    remaining = [j for j in range(len(columns)) if j not in removed]
    result = decompose_columns([columns[j] for j in remaining])
    result['deleted'] = list(deleted)
    result['remaining_coordinates'] = remaining
    result['original_components'] = [[remaining[j] for j in block] for block in result['components']]
    result['original_basis_indices'] = [remaining[j] for j in result['basis_indices']]
    result['original_loops'] = [remaining[j] for j in result['loops']]
    result['original_coloops'] = [remaining[j] for j in result['coloops']]
    return result


def probe_stored_codes(max_delete=2):
    """Check every D of size <=2 on the stored fixtures without cut enumeration."""
    if type(max_delete) is not int or not 0 <= max_delete <= 2:
        raise ValueError('this bounded probe requires max_delete in {0,1,2}')
    source = Path(__file__).resolve().parent / 'high_width_core_stress_lab' / 'random_code_audits.json'
    records = json.loads(source.read_text(encoding='utf-8'))
    helper = _deletion_helpers()
    started = perf_counter()
    summaries = []
    total_cases = 0
    all_work = {'total_xor_reductions': 0, 'verification_rank_evaluations': 0,
                'union_attempts': 0, 'successful_unions': 0}
    for record in records:
        n, k = record['n'], record['k']
        generator = tuple(sum(1 << j for j, col in enumerate(record['columns']) if col >> i & 1)
                          for i in range(k))
        checks = helper.parity_check(generator, n)
        columns = helper.columns_from_rows(checks, n)
        levels = []
        for d in range(max_delete + 1):
            level = {'deleted_count': d, 'cases': 0, 'split_cases': 0,
                     'multiple_nontrivial_component_cases': 0, 'loop_cases': 0,
                     'coloop_cases': 0, 'max_components': 0,
                     'smallest_largest_component': n - d, 'split_witnesses': []}
            for deleted in combinations(range(n), d):
                result = _conditioned_from_columns(columns, deleted)
                components = result['original_components']
                nontrivial = [block for block in components if len(block) > 1]
                level['cases'] += 1
                total_cases += 1
                level['max_components'] = max(level['max_components'], len(components))
                level['smallest_largest_component'] = min(level['smallest_largest_component'],
                                                          max(map(len, components), default=0))
                level['loop_cases'] += bool(result['loops'])
                level['coloop_cases'] += bool(result['coloops'])
                for key in all_work:
                    all_work[key] += result['work'][key]
                if len(components) > 1:
                    level['split_cases'] += 1
                    level['multiple_nontrivial_component_cases'] += len(nontrivial) > 1
                    level['split_witnesses'].append({
                        'deleted': list(deleted), 'components': components,
                        'component_ranks': result['partition_certificate']['component_ranks'],
                        'total_rank': result['rank'], 'loops': result['original_loops'],
                        'coloops': result['original_coloops']})
            levels.append(level)
        summaries.append({'n': n, 'k': k, 'seed': record['seed'], 'levels': levels})
    return {'source': str(source), 'max_delete': max_delete, 'cases': total_cases,
            'codes': summaries, 'work': all_work, 'seconds': perf_counter() - started,
            'scope': 'Direct sums only; no claim about 2/3-sums, optimal width or hardness.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-delete', type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(probe_stored_codes(args.max_delete), indent=2))
