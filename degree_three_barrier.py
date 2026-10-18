"""Exact-cover reduction and rational negative controls for affine optimization.

These are reductions/certificates, not a polynomial algorithm for the hard
problems.  In particular, the reduction has a NONZERO TARGET SYNDROME and does
not establish hardness of homogeneous minimum distance by itself.
"""

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class ExactCoverCoset:
    universe_size: int
    triples: tuple
    columns: tuple
    target: int
    max_weight: int


def encode_exact_cover(universe_size, triples):
    """Encode 3-set exact cover as Hx=all-ones, weight(x)<=|U|/3.

    Universe elements are integers in range(universe_size). Every column has
    exactly three ones. Duplicate columns are permitted and retain their input
    positions. For an empty universe, the empty selection is a valid cover;
    this is intentionally not a minimum-NONZERO-codeword encoding.

    Proof: if c_i counts selected triples containing element i, Hx=1 makes
    every c_i odd and at least one. Since sum(c_i)=3*weight(x)<=|U|, every c_i
    equals one and the selected triples form an exact cover. Conversely an
    exact cover satisfies the syndrome and cardinality bound.
    """
    if isinstance(universe_size, bool) or not isinstance(universe_size, int):
        raise ValueError("universe_size must be a nonnegative integer divisible by 3")
    if universe_size < 0 or universe_size % 3:
        raise ValueError("universe_size must be a nonnegative integer divisible by 3")
    canonical = []
    columns = []
    for triple in triples:
        items = tuple(triple)
        if len(items) != 3:
            raise ValueError("every set must contain exactly three elements")
        if any(isinstance(v, bool) or not isinstance(v, int) for v in items):
            raise ValueError("universe elements must be integers")
        if len(set(items)) != 3 or any(v < 0 or v >= universe_size for v in items):
            raise ValueError("triple elements must be distinct and within the universe")
        items = tuple(sorted(items))
        canonical.append(items)
        columns.append(sum(1 << v for v in items))
    return ExactCoverCoset(universe_size, tuple(canonical), tuple(columns),
                          (1 << universe_size) - 1, universe_size // 3)


def naive_homogenization_counterexample():
    """Return a concrete failure of the usual append-the-target trick.

    The X3C instance has a six-element universe and two duplicate triples on
    only the first three elements, so it has no exact cover.  The two equal
    columns nevertheless sum to zero over GF(2).  If one appends the target
    column and merely raises the threshold from ``k`` to ``k+1``, that kernel
    word (with appended bit zero) is accepted as a homogeneous witness.
    """
    instance = encode_exact_cover(6, ((0, 1, 2), (0, 1, 2)))
    kernel_selection = 0b11
    appended_target_weight = instance.target.bit_count()
    return {
        "instance": instance,
        "kernel_selection": kernel_selection,
        "kernel_syndrome": syndrome(instance, kernel_selection),
        "kernel_weight": kernel_selection.bit_count(),
        "has_exact_cover": any(is_exact_cover(instance, s)
                                for s in range(1 << len(instance.columns))),
        "naive_homogeneous_threshold": instance.max_weight + 1,
        "appended_target_weight": appended_target_weight,
    }


def _validate_selection(instance, selection):
    if isinstance(selection, bool) or not isinstance(selection, int):
        raise ValueError("selection must be a nonnegative integer bit mask")
    if selection < 0 or selection >> len(instance.columns):
        raise ValueError("selection contains an out-of-range column")


def syndrome(instance, selection):
    _validate_selection(instance, selection)
    value = 0
    for i, column in enumerate(instance.columns):
        if selection >> i & 1:
            value ^= column
    return value


def satisfies_coset_bound(instance, selection):
    """Independently check the binary linear system and cardinality bound."""
    _validate_selection(instance, selection)
    return (selection.bit_count() <= instance.max_weight
            and syndrome(instance, selection) == instance.target)


def is_exact_cover(instance, selection):
    """Check integer coverage counts directly, without parity arithmetic."""
    _validate_selection(instance, selection)
    counts = [0] * instance.universe_size
    for i, triple in enumerate(instance.triples):
        if selection >> i & 1:
            for vertex in triple:
                counts[vertex] += 1
    return all(count == 1 for count in counts)


def decode_cover(instance, selection):
    """Return a checked cover witness, or None for an infeasible selection."""
    if not satisfies_coset_bound(instance, selection):
        return None
    selected = tuple(triple for i, triple in enumerate(instance.triples)
                     if selection >> i & 1)
    if not is_exact_cover(instance, selection):
        raise AssertionError("reduction invariant violated")
    return selected


def extended_hamming_lp_counterexample():
    """Return an exact rational false positive for local parity-polytope LP.

    H has four rows: an all-ones row and the three binary coordinate-index
    rows, for coordinates 0,...,7. This is the [8,4,4] extended Hamming code.

    The local relaxation accepts x_7=1, x_3=x_5=x_6=1/2, all other x_i=0.
    Its weight is 5/2 <= 3. The nonzero pin is explicit, so this is not merely
    a convex combination with the zero codeword. Each row's local convex
    mixture below is supported entirely on even-parity Boolean assignments.

    Every integer codeword has even weight, and distinct coordinate indices
    rule out weight two. The support {0,1,2,3} is a weight-four codeword.
    Therefore the true minimum nonzero weight is four, making the LP decision
    at threshold three a false positive even with x_7 pinned to one.

    This only concerns the four supplied checks. XORing the three index rows
    gives the redundant support {1,2,4,7}; our point has restriction 0001 there
    and violates its parity polytope. It is not an all-redundant-check example.
    """
    half = Fraction(1, 2)
    quarter = Fraction(1, 4)
    rows = (255, 170, 204, 240)
    point = (Fraction(0), Fraction(0), Fraction(0), half,
             Fraction(0), half, half, Fraction(1))
    mixtures = (
        ((quarter, (1 << 7) | (1 << 3)),
         (quarter, (1 << 7) | (1 << 5)),
         (quarter, (1 << 7) | (1 << 6)),
         (quarter, (1 << 7) | (1 << 3) | (1 << 5) | (1 << 6))),
        ((half, (1 << 7) | (1 << 3)), (half, (1 << 7) | (1 << 5))),
        ((half, (1 << 7) | (1 << 3)), (half, (1 << 7) | (1 << 6))),
        ((half, (1 << 7) | (1 << 5)), (half, (1 << 7) | (1 << 6))),
    )
    return {
        "n": 8,
        "parity_check_rows": rows,
        "target": 0,
        "point": point,
        "local_even_mixtures": mixtures,
        "pinned_one_coordinate": 7,
        "lp_feasible_weight": sum(point),
        "decision_upper_bound": 3,
        "integer_distance": 4,
        "weight_four_witness": 15,
        "redundant_check_cut": rows[1] ^ rows[2] ^ rows[3],
    }
